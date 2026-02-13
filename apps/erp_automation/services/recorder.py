"""
Recording Service

Captures user actions in the browser for workflow creation.
Uses Playwright's tracing and custom JavaScript injection.

CRITICAL ARCHITECTURE NOTE:
Playwright's sync API can only be called from the thread that created it.
Django handles each HTTP request in a different thread, so we MUST run
Playwright in a dedicated background thread and communicate via queues.

Flow:
  start_recording() → spawns a background thread running _recorder_thread()
  poll_actions()    → sends 'poll' command to thread, gets actions back
  stop_recording()  → sends 'stop' command to thread, waits for completion
"""
import os
import json
import logging
import threading
import queue
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)


class RecorderService:
    """
    Records user actions in the browser.

    Features:
    - Runs Playwright in a dedicated thread (solves cross-thread errors)
    - Captures clicks, inputs, selections, key presses
    - Injects into ALL frames/iframes (critical for D365)
    - Generates smart locators for each element
    - Filters noise (body clicks, loading overlays)
    - Deduplicates rapid-fire events
    """

    def __init__(self):
        self.is_recording = False
        self.recorded_actions = []
        self.action_counter = 0
        self.session_id = None
        self.screenshots_dir = None

        # Thread communication
        self._thread: Optional[threading.Thread] = None
        self._cmd_queue: queue.Queue = queue.Queue()
        self._result_queue: queue.Queue = queue.Queue()
        self._thread_ready = threading.Event()
        self._thread_error: Optional[str] = None

    def start_recording(
        self,
        url: str,
        session_id: str,
        screenshots_dir: str = None,
        headless: bool = False,
        credentials: Dict[str, str] = None,
    ) -> bool:
        """Start a recording session in a background thread."""
        import tempfile
        self.session_id = session_id
        self.screenshots_dir = screenshots_dir or os.path.join(
            tempfile.gettempdir(), "erp_automation", "recordings", str(session_id)
        )
        os.makedirs(self.screenshots_dir, exist_ok=True)

        # Ensure URL has protocol
        nav_url = url.strip()
        if nav_url and not nav_url.startswith(('http://', 'https://')):
            nav_url = 'https://' + nav_url

        # Reset state
        self.recorded_actions = []
        self.action_counter = 0
        self._thread_error = None
        self._thread_ready.clear()

        # Clear queues
        while not self._cmd_queue.empty():
            try: self._cmd_queue.get_nowait()
            except: pass
        while not self._result_queue.empty():
            try: self._result_queue.get_nowait()
            except: pass

        # Start the Playwright thread
        self._thread = threading.Thread(
            target=self._recorder_thread,
            args=(nav_url, headless),
            daemon=True,
            name=f"recorder-{session_id}"
        )
        self._thread.start()

        # Wait for the thread to be ready (browser opened, page loaded)
        self._thread_ready.wait(timeout=90)

        if self._thread_error:
            logger.error(f"Recorder thread failed: {self._thread_error}")
            return False

        self.is_recording = True
        logger.info(f"Recording started: session={session_id}, url={nav_url}")
        return True

    def stop_recording(self) -> list:
        """Stop recording and return captured actions."""
        self.is_recording = False

        if self._thread and self._thread.is_alive():
            # Send stop command
            self._cmd_queue.put(('stop', None))
            # Wait for thread to finish
            self._thread.join(timeout=15)

        # Get any final actions from the result queue
        while not self._result_queue.empty():
            try:
                msg_type, data = self._result_queue.get_nowait()
                if msg_type == 'actions':
                    for action in data:
                        self._store_action(action)
            except:
                pass

        self._thread = None
        logger.info(f"Recording stopped: {len(self.recorded_actions)} actions captured")
        return self.recorded_actions

    def poll_actions(self) -> list:
        """
        Poll for new recorded actions.
        Sends a 'poll' command to the background thread and waits for results.
        """
        if not self.is_recording or not self._thread or not self._thread.is_alive():
            return []

        # Send poll command
        self._cmd_queue.put(('poll', None))

        # Wait for result (with timeout)
        try:
            msg_type, data = self._result_queue.get(timeout=5)
            if msg_type == 'actions':
                new_actions = []
                for raw_action in data:
                    processed = self._store_action(raw_action)
                    if processed:
                        new_actions.append(processed)
                return new_actions
            elif msg_type == 'error':
                logger.warning(f"[poll] Thread error: {data}")
                return []
        except queue.Empty:
            logger.debug("[poll] Timeout waiting for poll results")
            return []

        return []

    # =========================================================================
    # BACKGROUND THREAD - All Playwright calls happen here
    # =========================================================================

    def _recorder_thread(self, url: str, headless: bool):
        """
        Background thread that owns the Playwright browser.
        All Playwright API calls MUST happen in this thread.
        Communicates with the main thread via queues.
        """
        from playwright.sync_api import sync_playwright
        from .locator_engine import LocatorEngine

        playwright = None
        browser = None
        context = None
        page = None

        try:
            # Start Playwright (in THIS thread)
            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(
                headless=headless,
                args=["--start-maximized", "--no-sandbox", "--disable-dev-shm-usage"]
            )
            context = browser.new_context(
                no_viewport=True,
                record_video_dir=self.screenshots_dir if not headless else None,
            )
            page = context.new_page()

            # Inject recording scripts via context-level init script (all frames)
            recorder_js = self._get_recorder_script()
            context.add_init_script(recorder_js)

            # Also inject into current page
            try:
                page.evaluate(recorder_js)
            except:
                pass

            # Navigate to URL
            logger.info(f"[thread] Navigating to: {url[:80]}")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Set up frame injection for existing and future frames
            self._setup_frame_injection_in_thread(page, recorder_js)

            # Signal that we're ready
            self._thread_ready.set()
            logger.info(f"[thread] Ready. Frames: {len(page.frames)}")

            # Main command loop
            while True:
                try:
                    cmd, data = self._cmd_queue.get(timeout=2)
                except queue.Empty:
                    # No command — do a background poll to keep actions flowing
                    # This also serves as a heartbeat to detect closed browser
                    try:
                        # Check if browser is still alive
                        page.evaluate("1")
                    except Exception as e:
                        err_str = str(e).lower()
                        if 'closed' in err_str or 'crashed' in err_str or 'target page' in err_str:
                            logger.info("[thread] Browser closed, stopping recorder")
                            break
                    continue

                if cmd == 'stop':
                    logger.info("[thread] Stop command received")
                    # Collect final actions from all frames
                    final_actions = self._collect_all_actions(page, recorder_js)
                    self._result_queue.put(('actions', final_actions))
                    break

                elif cmd == 'poll':
                    # Collect actions from all frames
                    try:
                        actions = self._collect_all_actions(page, recorder_js)

                        # Log frame info periodically
                        if not hasattr(self, '_poll_count'):
                            self._poll_count = 0
                        self._poll_count += 1
                        if self._poll_count % 10 == 1:
                            frames = page.frames
                            logger.info(f"[thread] Poll #{self._poll_count}: {len(frames)} frames, got {len(actions)} new actions")
                            for i, f in enumerate(frames):
                                try:
                                    has_rec = f.evaluate("!!window.__recorder")
                                    logger.info(f"[thread]   frame[{i}]: recorder={has_rec} url={f.url[:80]}")
                                except Exception as e:
                                    logger.info(f"[thread]   frame[{i}]: ERROR={e} url={f.url[:60]}")

                        self._result_queue.put(('actions', actions))
                    except Exception as e:
                        logger.warning(f"[thread] Poll error: {e}")
                        self._result_queue.put(('actions', []))

        except Exception as e:
            logger.error(f"[thread] Fatal error: {e}")
            self._thread_error = str(e)
            self._thread_ready.set()  # Unblock the main thread
        finally:
            # Cleanup
            try:
                if page: page.close()
            except: pass
            try:
                if context: context.close()
            except: pass
            try:
                if browser: browser.close()
            except: pass
            try:
                if playwright: playwright.stop()
            except: pass
            logger.info("[thread] Recorder thread exited")

    def _setup_frame_injection_in_thread(self, page, recorder_js: str):
        """Set up injection into all frames (runs in Playwright thread)."""

        def _inject_into_frame(frame):
            try:
                frame.evaluate(recorder_js)
                logger.info(f"[thread] Injected recorder into frame: {frame.url[:80]}")
            except Exception as e:
                logger.debug(f"[thread] Could not inject into frame {frame.url[:60]}: {e}")

        def _on_frame_navigated(frame):
            try:
                frame.evaluate(recorder_js)
                logger.info(f"[thread] Re-injected after navigation: {frame.url[:80]}")
            except:
                pass

        def _on_frame_attached(frame):
            logger.info(f"[thread] New frame attached: {frame.url[:80]}")
            try:
                frame.wait_for_load_state("domcontentloaded", timeout=5000)
            except:
                pass
            _inject_into_frame(frame)

        # Inject into all existing frames
        for frame in page.frames:
            _inject_into_frame(frame)

        # Listen for new frames
        page.on("frameattached", _on_frame_attached)
        page.on("framenavigated", _on_frame_navigated)

    def _collect_all_actions(self, page, recorder_js: str) -> list:
        """Collect pending actions from all frames (runs in Playwright thread)."""
        all_actions = []

        # Main frame
        try:
            actions = page.evaluate("window.__recorder?.getActions() || []")
            all_actions.extend(actions)
        except Exception as e:
            logger.debug(f"[thread] Main frame collect failed: {e}")

        # All child frames
        try:
            for frame in page.frames:
                if frame == page.main_frame:
                    continue
                try:
                    has_recorder = frame.evaluate("!!window.__recorder")
                    if has_recorder:
                        actions = frame.evaluate("window.__recorder.getActions()")
                        if actions:
                            logger.info(f"[thread] Got {len(actions)} actions from iframe: {frame.url[:60]}")
                        all_actions.extend(actions)
                    else:
                        # Late-inject
                        logger.info(f"[thread] Late-injecting recorder into: {frame.url[:60]}")
                        frame.evaluate(recorder_js)
                except Exception as e:
                    logger.debug(f"[thread] Frame error: {e}")
        except:
            pass

        # Sort by timestamp
        all_actions.sort(key=lambda a: a.get('timestamp', 0))
        return all_actions

    # =========================================================================
    # ACTION PROCESSING (runs in main thread)
    # =========================================================================

    def _store_action(self, raw_action: Dict) -> Optional[Dict]:
        """Process a raw action and add to recorded_actions list."""
        # Navigate events don't have a real element but still matter
        if raw_action.get("type") == "navigate":
            self.action_counter += 1
            processed = {
                "order": self.action_counter,
                "action_type": "navigate",
                "timestamp": raw_action.get("timestamp"),
                "page_url": raw_action.get("url", ""),
                "from_url": raw_action.get("fromUrl", ""),
                "page_title": raw_action.get("title", ""),
                "element_tag": "page",
                "element_id": "",
                "element_name": "",
                "element_class": "",
                "element_xpath": "",
                "element_css": "",
                "element_text": raw_action.get("title", ""),
                "element_aria_label": "",
                "element_placeholder": "",
                "element_role": "",
                "element_type": "",
                "element_rect": {},
                "input_value": "",
                "key_pressed": "",
                "locator_strategies": [],
                "is_in_iframe": False,
                "frame_url": raw_action.get("url", ""),
            }
            self.recorded_actions.append(processed)
            return processed

        if not raw_action.get("element"):
            return None

        self.action_counter += 1
        element_info = raw_action["element"]

        # Generate smart locator strategies
        strategies = self._generate_strategies_with_contains(element_info)

        # Build processed action
        processed = {
            "order": self.action_counter,
            "action_type": self._map_action_type(raw_action["type"]),
            "timestamp": raw_action.get("timestamp"),
            "page_url": raw_action.get("url", ""),
            "page_title": raw_action.get("title", ""),

            # Element info
            "element_tag": element_info.get("tagName", ""),
            "element_id": element_info.get("id", ""),
            "element_name": element_info.get("name", ""),
            "element_class": element_info.get("className", ""),
            "element_xpath": element_info.get("xpath", ""),
            "element_css": element_info.get("css", ""),
            "element_text": element_info.get("text", ""),
            "element_aria_label": element_info.get("ariaLabel", ""),
            "element_placeholder": element_info.get("placeholder", ""),
            "element_role": element_info.get("role", ""),
            "element_type": element_info.get("type", ""),
            "element_rect": element_info.get("rect", {}),
            "element_title": element_info.get("title", ""),
            "element_stable_id": element_info.get("stableId", ""),
            "element_data_testid": element_info.get("dataTestId", ""),

            # D365 control context
            "element_dyn_control_name": (
                element_info.get("dynControlContext", {}) or {}
            ).get("controlName", ""),

            # Input data
            "input_value": raw_action.get("value", ""),
            "key_pressed": raw_action.get("key", ""),

            # Generated locators
            "locator_strategies": strategies,

            # Frame info
            "is_in_iframe": element_info.get("isInIframe", False),
            "frame_url": element_info.get("frameUrl", ""),
        }

        self.recorded_actions.append(processed)
        return processed

    # =========================================================================
    # RECORDER JAVASCRIPT
    # =========================================================================

    def _get_recorder_script(self):
        """Return the JavaScript recording script.

        Key features:
        - Per-element input debounce (not global) so multi-field typing works
        - Noise filtering: ignores clicks on body, loading overlays, empty spans
        - Deduplication: prevents recording same click+change on one element
        - D365 contains-XPath for dynamic IDs (strips page-specific prefixes)
        - Captures Tab/Enter/Escape key presses
        - Captures D365 custom dropdown selections
        - URL change detection: records synthetic 'navigate' events
        - Stable ID extraction: extracts the last meaningful part of D365 IDs
        """
        return """
        if (window.__recorder && window.__recorder.isRecording) {
            // Already injected
        } else {
        (function() {
        var recorder = {
            actions: [],
            isRecording: true,
            lastActionKey: '',
            lastActionTime: 0,
            inputTimers: {},
            lastUrl: window.location.href,
            lastTitle: document.title,
            urlCheckInterval: null,

            getElementInfo: function(element) {
                if (!element) return null;

                var rect = element.getBoundingClientRect();

                var getCssPath = function(el) {
                    if (el.id) return '#' + CSS.escape(el.id);
                    var path = [];
                    while (el && el.nodeType === Node.ELEMENT_NODE) {
                        var selector = el.nodeName.toLowerCase();
                        if (el.className && typeof el.className === 'string') {
                            var classes = el.className.trim().split(/\\s+/).filter(function(c) { return c.length > 0; });
                            if (classes.length > 0 && classes.length < 5) {
                                selector += '.' + classes.map(function(c) { return CSS.escape(c); }).join('.');
                            }
                        }
                        path.unshift(selector);
                        el = el.parentElement;
                    }
                    return path.join(' > ');
                };

                var getXPath = function(el) {
                    if (el.id) return '//*[@id="' + el.id + '"]';
                    if (el.getAttribute && el.getAttribute('name')) return '//*[@name="' + el.getAttribute('name') + '"]';
                    var parts = [];
                    while (el && el.nodeType === Node.ELEMENT_NODE) {
                        var index = 1;
                        var sibling = el.previousElementSibling;
                        while (sibling) {
                            if (sibling.nodeName === el.nodeName) index++;
                            sibling = sibling.previousElementSibling;
                        }
                        parts.unshift(el.nodeName.toLowerCase() + '[' + index + ']');
                        el = el.parentElement;
                    }
                    return '/' + parts.join('/');
                };

                // D365 IDs have dynamic prefixes like "gridname_2_ActualId"
                // Extract the stable suffix part for contains-based matching
                var getStableId = function(el) {
                    if (!el.id) return '';
                    var fullId = el.id;
                    var parts = fullId.split('_');
                    if (parts.length >= 2) {
                        // Try last 2 parts first (e.g., "2_SystemDefinedNewButton" -> "SystemDefinedNewButton")
                        // But if the second-to-last part is a number, use just the last part
                        var lastPart = parts[parts.length - 1];
                        var secondLast = parts[parts.length - 2];
                        if (/^\\d+$/.test(secondLast)) {
                            // e.g., "grid_2_NewButton" -> "NewButton"
                            return lastPart;
                        }
                        // e.g., "prefix_StorageDimensionGroup_Name" -> "StorageDimensionGroup_Name"
                        return parts.slice(-2).join('_');
                    }
                    return fullId;
                };

                var getContainsXPath = function(el) {
                    var stableId = getStableId(el);
                    if (!stableId || stableId.length <= 3) return '';
                    return '//*[contains(@id, "' + stableId + '")]';
                };

                // Walk up to find the nearest meaningful label
                var getLabel = function(el) {
                    // Check aria-label
                    if (el.getAttribute && el.getAttribute('aria-label')) return el.getAttribute('aria-label');
                    // Check title attribute (D365 toolbar buttons use title)
                    if (el.getAttribute && el.getAttribute('title')) return el.getAttribute('title');
                    // Check associated <label>
                    if (el.id) {
                        var label = document.querySelector('label[for="' + el.id + '"]');
                        if (label) return label.innerText.trim().substring(0, 60);
                    }
                    // Check parent label
                    var parent = el.closest ? el.closest('label') : null;
                    if (parent) return parent.innerText.trim().substring(0, 60);
                    // Check preceding sibling label text (D365 pattern)
                    var prev = el.previousElementSibling;
                    if (prev && prev.tagName === 'LABEL') return prev.innerText.trim().substring(0, 60);
                    return '';
                };

                // D365 pattern: walk up to find nearest ancestor with data-dyn-controlname
                // This is critical for lookup buttons, dropdown triggers, etc. that
                // have no ID/name of their own but sit inside a named control container
                var getDynControlContext = function(el) {
                    var maxUp = 10;
                    var cur = el.parentElement;
                    while (cur && maxUp > 0) {
                        var cn = cur.getAttribute ? cur.getAttribute('data-dyn-controlname') : '';
                        if (cn) {
                            return {
                                controlName: cn,
                                // How the element relates to the control (by class)
                                elementClass: (typeof element.className === 'string') ? element.className.trim().split(/\\s+/)[0] : '',
                                // Distance from element to control ancestor
                                depth: 10 - maxUp + 1
                            };
                        }
                        cur = cur.parentElement;
                        maxUp--;
                    }
                    return null;
                };

                return {
                    tagName: element.tagName.toLowerCase(),
                    id: element.id || '',
                    stableId: getStableId(element),
                    name: element.getAttribute ? (element.getAttribute('name') || '') : '',
                    className: (typeof element.className === 'string') ? element.className : '',
                    ariaLabel: getLabel(element),
                    placeholder: element.getAttribute ? (element.getAttribute('placeholder') || '') : '',
                    text: (element.innerText || element.textContent || '').substring(0, 200).trim(),
                    title: element.getAttribute ? (element.getAttribute('title') || '') : '',
                    value: element.value || '',
                    type: element.getAttribute ? (element.getAttribute('type') || '') : '',
                    role: element.getAttribute ? (element.getAttribute('role') || '') : '',
                    dataTestId: element.getAttribute ? (element.getAttribute('data-testid') || '') : '',
                    dynControlContext: getDynControlContext(element),
                    css: getCssPath(element),
                    xpath: getXPath(element),
                    containsXpath: getContainsXPath(element),
                    rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
                    isInIframe: (window !== window.top),
                    frameUrl: window.location.href
                };
            },

            isNoise: function(element) {
                if (!element) return true;
                var tag = element.tagName ? element.tagName.toLowerCase() : '';
                // Skip body clicks, html clicks
                if (tag === 'body' || tag === 'html') return true;
                // Skip clicks on loading overlays / spinners
                var text = (element.innerText || element.textContent || '').trim().toLowerCase();
                if (text.indexOf('please wait') === 0 || text.indexOf('loading') === 0) return true;
                // Check aria-label — elements with aria-label are always meaningful
                var ariaLabel = element.getAttribute ? (element.getAttribute('aria-label') || '') : '';
                if (ariaLabel) return false;
                // Check if inside a D365 dropdown/flyout/listbox container
                var cls = (typeof element.className === 'string') ? element.className : '';
                if (cls && (cls.indexOf('lookup') >= 0 || cls.indexOf('Lookup') >= 0 ||
                    cls.indexOf('dropdown') >= 0 || cls.indexOf('Dropdown') >= 0 ||
                    cls.indexOf('flyout') >= 0 || cls.indexOf('Flyout') >= 0 ||
                    cls.indexOf('option') >= 0 || cls.indexOf('menuItem') >= 0)) return false;
                // Check if element is inside a dropdown/flyout parent (D365 custom dropdowns)
                if (element.closest && (
                    element.closest('[role="listbox"]') ||
                    element.closest('[role="menu"]') ||
                    element.closest('[role="dialog"]') ||
                    element.closest('.flyout') ||
                    element.closest('.lookupPopup') ||
                    element.closest('.dropdown-dialog'))) return false;
                if (text === '' && tag === 'div' && !element.id && !element.getAttribute('role') &&
                    !element.getAttribute('title')) return true;
                // Skip empty spans with no useful attributes
                if (tag === 'span' && !element.id && !element.getAttribute('name') &&
                    !element.getAttribute('role') && !element.getAttribute('title') &&
                    text.length === 0) return true;
                return false;
            },

            isDuplicate: function(type, element) {
                var key = type + '|' + (element.id || '') + '|' + (element.getAttribute ? (element.getAttribute('name') || '') : '') + '|' + element.tagName;
                var now = Date.now();
                if (key === this.lastActionKey && (now - this.lastActionTime) < 800) {
                    return true;
                }
                this.lastActionKey = key;
                this.lastActionTime = now;
                return false;
            },

            recordAction: function(type, element, extra) {
                if (!this.isRecording) return;
                if (this.isNoise(element)) return;
                if (this.isDuplicate(type, element)) return;

                extra = extra || {};
                var action = {
                    type: type,
                    timestamp: Date.now(),
                    url: window.location.href,
                    title: document.title,
                    element: this.getElementInfo(element)
                };
                for (var k in extra) { action[k] = extra[k]; }

                this.actions.push(action);
                var ident = action.element ? (action.element.name || action.element.ariaLabel || action.element.stableId || action.element.id || action.element.text.substring(0, 30)) : '?';
                console.log('[Recorder] ' + type + ': ' + ident + (extra.value ? ' = "' + extra.value.substring(0, 20) + '"' : ''));
            },

            // Record a URL change as a synthetic navigation event
            recordNavigation: function(fromUrl, toUrl) {
                this.actions.push({
                    type: 'navigate',
                    timestamp: Date.now(),
                    url: toUrl,
                    fromUrl: fromUrl,
                    title: document.title,
                    element: {
                        tagName: 'page',
                        id: '',
                        stableId: '',
                        name: '',
                        className: '',
                        ariaLabel: document.title,
                        text: document.title,
                        title: document.title,
                        isInIframe: (window !== window.top),
                        frameUrl: window.location.href
                    }
                });
                console.log('[Recorder] navigate: ' + fromUrl.substring(0, 40) + ' -> ' + toUrl.substring(0, 40));
            },

            getActions: function() {
                var a = this.actions.slice();
                this.actions = [];
                return a;
            },

            // Walk up from e.target to nearest meaningful clickable element.
            // D365 sidebar icons use SVG/path/span inside buttons —
            // e.target is the inner element but we want the button/a/li.
            getMeaningfulElement: function(el) {
                var maxUp = 5;
                var orig = el;
                while (el && maxUp > 0) {
                    var tag = el.tagName ? el.tagName.toLowerCase() : '';
                    // If we find a button, anchor, li, or element with id/name/role — use it
                    if (tag === 'button' || tag === 'a' || tag === 'li' ||
                        tag === 'input' || tag === 'select' || tag === 'textarea') return el;
                    if (el.id || (el.getAttribute && el.getAttribute('name')) ||
                        (el.getAttribute && el.getAttribute('role'))) return el;
                    // If it has a title or aria-label attribute
                    if (el.getAttribute && el.getAttribute('title')) return el;
                    if (el.getAttribute && el.getAttribute('aria-label')) return el;
                    // If it has meaningful class (D365 patterns)
                    var cls = (typeof el.className === 'string') ? el.className : '';
                    if (cls && (cls.indexOf('button') >= 0 || cls.indexOf('Button') >= 0 ||
                        cls.indexOf('link') >= 0 || cls.indexOf('Link') >= 0 ||
                        cls.indexOf('control') >= 0 || cls.indexOf('tab') >= 0 ||
                        cls.indexOf('Tab') >= 0 || cls.indexOf('pane') >= 0 ||
                        cls.indexOf('lookup') >= 0 || cls.indexOf('Lookup') >= 0 ||
                        cls.indexOf('dropdown') >= 0 || cls.indexOf('Dropdown') >= 0 ||
                        cls.indexOf('flyout') >= 0 || cls.indexOf('Flyout') >= 0 ||
                        cls.indexOf('menuItem') >= 0 || cls.indexOf('option') >= 0)) return el;
                    el = el.parentElement;
                    maxUp--;
                }
                return orig; // fallback to original target
            }
        };
        window.__recorder = recorder;

        // ---- EVENT LISTENERS ----

        // Clicks (capture phase to get before D365 handlers)
        document.addEventListener('click', function(e) {
            // Walk up from e.target to find the meaningful clickable element
            var el = recorder.getMeaningfulElement(e.target);
            // For D365 dropdowns: if clicking a list item, record as 'select'
            var role = el.getAttribute ? (el.getAttribute('role') || '') : '';
            if (role === 'option' || role === 'menuitem' || role === 'treeitem' ||
                (el.tagName && el.tagName.toLowerCase() === 'li' && el.closest && el.closest('[role="listbox"]'))) {
                recorder.recordAction('select', el, {
                    value: (el.innerText || el.textContent || '').trim().substring(0, 100)
                });
            } else {
                recorder.recordAction('click', el);
            }
        }, true);

        // Input typing — debounced PER ELEMENT
        document.addEventListener('input', function(e) {
            var el = e.target;
            var elKey = el.id || el.name || el.tagName + '_' + (el.type || '');
            if (recorder.inputTimers[elKey]) clearTimeout(recorder.inputTimers[elKey]);
            recorder.inputTimers[elKey] = setTimeout(function() {
                recorder.recordAction('input', el, { value: el.value || '' });
                delete recorder.inputTimers[elKey];
            }, 800);
        }, true);

        // Change events (for selects, checkboxes, radio buttons)
        document.addEventListener('change', function(e) {
            var el = e.target;
            var tag = el.tagName ? el.tagName.toLowerCase() : '';
            var type = el.type ? el.type.toLowerCase() : '';
            if (tag === 'select') {
                var selectedText = el.options && el.selectedIndex >= 0 ? el.options[el.selectedIndex].text : el.value;
                recorder.recordAction('select', el, { value: selectedText || el.value });
            } else if (type === 'checkbox' || type === 'radio') {
                recorder.recordAction('click', el, { value: el.checked ? 'checked' : 'unchecked' });
            } else {
                recorder.recordAction('change', el, { value: el.value || '' });
            }
        }, true);

        // Key presses (Tab, Enter, Escape)
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === 'Tab' || e.key === 'Escape') {
                recorder.recordAction('keypress', e.target, { key: e.key });
            }
        }, true);

        // Focus out — flush pending input timers (catches pasted values)
        document.addEventListener('focusout', function(e) {
            var el = e.target;
            if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') && el.value) {
                var elKey = el.id || el.name || el.tagName + '_' + (el.type || '');
                if (recorder.inputTimers[elKey]) {
                    clearTimeout(recorder.inputTimers[elKey]);
                    recorder.recordAction('input', el, { value: el.value || '' });
                    delete recorder.inputTimers[elKey];
                }
            }
        }, true);

        // Before page unload — flush ALL pending input timers
        window.addEventListener('beforeunload', function() {
            for (var key in recorder.inputTimers) {
                clearTimeout(recorder.inputTimers[key]);
            }
        });

        // URL change detection — D365 is a SPA that changes URL without full page loads
        // This creates synthetic 'navigate' events so the workflow knows to wait
        recorder.urlCheckInterval = setInterval(function() {
            var currentUrl = window.location.href;
            if (currentUrl !== recorder.lastUrl) {
                recorder.recordNavigation(recorder.lastUrl, currentUrl);
                recorder.lastUrl = currentUrl;
                recorder.lastTitle = document.title;
            }
        }, 1000);

        // Also listen to popstate and hashchange
        window.addEventListener('popstate', function() {
            var currentUrl = window.location.href;
            if (currentUrl !== recorder.lastUrl) {
                recorder.recordNavigation(recorder.lastUrl, currentUrl);
                recorder.lastUrl = currentUrl;
            }
        });

        window.addEventListener('hashchange', function() {
            var currentUrl = window.location.href;
            if (currentUrl !== recorder.lastUrl) {
                recorder.recordNavigation(recorder.lastUrl, currentUrl);
                recorder.lastUrl = currentUrl;
            }
        });

        console.log('[Recorder] Injected into ' + window.location.href.substring(0, 60));
        })();
        } // end if-not-already-injected
        """

    # =========================================================================
    # LOCATOR STRATEGY GENERATION
    # =========================================================================

    def _generate_strategies_with_contains(self, element_info: Dict) -> list:
        """Generate locator strategies with D365 contains-based XPath support.

        This is the main entry point — calls _generate_strategies which now
        produces proven-pattern strategies (double-contains, exact @id, etc.).
        """
        return self._generate_strategies(element_info)

    def _generate_strategies(self, element_info: Dict) -> list:
        """Generate locator strategies following proven D365 locator patterns.

        Proven pattern priority (matches manually-created working locators):
        0. D365 control context — for elements inside data-dyn-controlname containers
           e.g. //*[@data-dyn-controlname="General_BOMVersion_BOMId"]//div[contains(@class, "lookupButton")]
           This is the PRIMARY strategy for lookup buttons, dropdown triggers, etc.
        1. Double contains() XPath — PRIMARY for D365 dynamic-prefix IDs
           e.g. //*[contains(@id, "EcoResProductCreate_") and contains(@id, "ItemGroupId_input")]
        2. Exact @id — for static elements (no dynamic prefix)
           e.g. //*[@id="navPaneFavoritesID"]
        3. @name via xpath — for form fields with name attribute
           e.g. //*[@name="fieldName"]
        4. Single contains(@id) fallback — filtered for safety (no broad matches)
        5. Text content — for buttons/links/tabs (short, specific only)
        6. aria-label via xpath — non-generic only
        """
        import re
        strategies = []
        priority = 1

        element_id = element_info.get("id", "")
        element_name = element_info.get("name", "")
        element_aria = element_info.get("ariaLabel", "")
        element_text = (element_info.get("text", "") or "").strip()
        tag = element_info.get("tagName", "")
        stable_id = element_info.get("stableId", "")
        element_class = element_info.get("className", "")
        element_title = element_info.get("title", "")
        dyn_ctx = element_info.get("dynControlContext")

        # Strategy 0: D365 control context — ancestor data-dyn-controlname pattern
        # Critical for lookup buttons, dropdown triggers, toggle switches, etc.
        # that have no ID/name but sit inside a named control container
        if dyn_ctx and dyn_ctx.get("controlName"):
            control_name = dyn_ctx["controlName"]
            primary_class = dyn_ctx.get("elementClass", "")

            # Build: //*[@data-dyn-controlname="X"]//{tag}[contains(@class, "primaryClass")]
            # Use element's actual tag for precision (div for lookupButton, input for fields)
            target_tag = tag or 'div'
            # For elements without ID/name (lookup buttons, toggles), this is the PRIMARY locator
            if primary_class and not element_id and not element_name:
                strategies.append({
                    "strategy_type": "xpath",
                    "value": f'//*[@data-dyn-controlname="{control_name}"]//{target_tag}[contains(@class, "{primary_class}")]',
                    "priority": priority
                })
                priority += 1

                # Also add partial controlname match as fallback
                cn_parts = control_name.split("_")
                if len(cn_parts) >= 2:
                    short_name = "_".join(cn_parts[-2:]) if len(cn_parts) > 2 else control_name
                    if short_name != control_name:
                        strategies.append({
                            "strategy_type": "xpath",
                            "value": f'//*[contains(@data-dyn-controlname, "{short_name}")]//{target_tag}[contains(@class, "{primary_class}")]',
                            "priority": priority
                        })
                        priority += 1

            # If element has title attribute, add controlname + title combo
            if element_title and element_title not in ('', 'Open'):
                strategies.append({
                    "strategy_type": "xpath",
                    "value": f'//*[@data-dyn-controlname="{control_name}"]//*[@title="{element_title}"]',
                    "priority": priority
                })
                priority += 1

        has_dynamic_id = bool(element_id and re.search(r'_\d+_', element_id))

        # Strategy 1: Double-contains XPath (PRIMARY for D365 fields)
        if has_dynamic_id and element_id:
            page_prefix, field_suffix = self._split_d365_id(element_id)
            if page_prefix and field_suffix and len(field_suffix) > 3:
                xpath = f'//*[contains(@id, "{page_prefix}") and contains(@id, "{field_suffix}")]'
                strategies.append({
                    "strategy_type": "xpath",
                    "value": xpath,
                    "priority": priority
                })
                priority += 1

        # Strategy 2: Exact @id for static elements (no dynamic numbers)
        if element_id and not has_dynamic_id:
            strategies.append({
                "strategy_type": "xpath",
                "value": f'//*[@id="{element_id}"]',
                "priority": priority
            })
            priority += 1

        # Strategy 3: @name attribute via xpath (for form inputs)
        # Skip overly generic names
        if element_name and element_name not in ('Name',):
            strategies.append({
                "strategy_type": "xpath",
                "value": f'//*[@name="{element_name}"]',
                "priority": priority
            })
            priority += 1

        # Strategy 4: Single contains(@id) fallback (filtered for safety)
        # Only if different from double-contains and not dangerously broad
        BROAD_IDS = {'input', 'header', 'label', 'button', 'Name_input',
                     'select', 'text', 'value', 'field', 'container', 'wrapper'}
        if stable_id and stable_id != element_id and len(stable_id) > 5:
            contains_xpath = f'//*[contains(@id, "{stable_id}")]'
            existing_vals = {s["value"] for s in strategies}
            if stable_id not in BROAD_IDS and contains_xpath not in existing_vals:
                strategies.append({
                    "strategy_type": "xpath",
                    "value": contains_xpath,
                    "priority": priority
                })
                priority += 1

        # Strategy 5: Text content (short, specific only — for clickable elements)
        if element_text and tag in ("button", "a", "li", "span"):
            clean_text = element_text.split('\n')[0].strip()
            if clean_text and 1 < len(clean_text) < 40:
                strategies.append({
                    "strategy_type": "text",
                    "value": clean_text,
                    "priority": priority
                })
                priority += 1

        # Strategy 6: aria-label via xpath (non-generic only)
        GENERIC_LABELS = {'Name', 'ea', 'Back', 'Close', 'Search', 'Yes', 'No'}
        if element_aria and element_aria not in GENERIC_LABELS:
            strategies.append({
                "strategy_type": "xpath",
                "value": f'//*[@aria-label="{element_aria}"]',
                "priority": priority
            })
            priority += 1

        return strategies

    def _split_d365_id(self, element_id: str):
        """Split D365 dynamic ID into stable text parts for double-contains XPath.

        Strips the first dynamic numeric segment and keeps everything after it
        (including small numbers like 0, 0_0 which are stable row/col indices).

        Examples:
          "EcoResProductCreate_3_ItemGroupId_input"
              → prefix="EcoResProductCreate_", suffix="ItemGroupId_input"
          "EcoResConfiguration_Name_9392_0_0_input"
              → prefix="EcoResConfiguration_Name_", suffix="0_0_input"
          "Sel_7008_0_0_input"
              → prefix="Sel_", suffix="0_0_input"
          "EcoResProductMasterDimension_13_TabPageSizes_header"
              → prefix="EcoResProductMasterDimension_", suffix="TabPageSizes_header"
        """
        import re
        if not element_id:
            return "", ""

        parts = element_id.split('_')

        # Find first numeric segment — this is the dynamic session ID
        dynamic_idx = None
        for i, part in enumerate(parts):
            if re.match(r'^\d+$', part):
                dynamic_idx = i
                break

        if dynamic_idx is None:
            return "", element_id

        prefix_parts = parts[:dynamic_idx]
        prefix = '_'.join(prefix_parts) + '_' if prefix_parts else ""

        suffix_parts = parts[dynamic_idx + 1:]
        suffix = '_'.join(suffix_parts) if suffix_parts else ""

        return prefix, suffix

    def _map_action_type(self, browser_type: str) -> str:
        """Map browser event type to our action type."""
        mapping = {
            "click": "click",
            "input": "fill",
            "change": "fill",
            "select": "select",
            "submit": "click",
            "keypress": "press_key",
            "navigate": "navigate",
        }
        return mapping.get(browser_type, "click")

    def _is_dynamic_id(self, element_id: str) -> bool:
        """Check if ID is dynamically generated (has D365 prefix or UUID-style).

        D365 dynamic prefix pattern: PageName_123_FieldName
        Static IDs: navPaneFavoritesID, userNameInput
        """
        import re
        # D365 dynamic prefix: word_digits_rest
        if re.match(r'^[a-zA-Z]+_\d+_', element_id):
            return True
        patterns = [
            r'[0-9a-f]{8}-[0-9a-f]{4}',  # UUID
            r'_\d{10,}',                    # Very long numeric suffix
            r'react-',                      # React auto-generated
            r'ng-',                         # Angular auto-generated
        ]
        for pattern in patterns:
            if re.search(pattern, element_id, re.IGNORECASE):
                return True
        return False

    # =========================================================================
    # EXPORT METHODS
    # =========================================================================

    def export_to_workflow(self, workflow_name: str) -> Dict:
        """Export recorded actions to workflow format."""
        steps = []

        for action in self.recorded_actions:
            value_field = ""
            value_static = action.get("input_value", "")

            if value_static and self._looks_like_data_field(value_static):
                value_field = self._guess_field_name(action)
                value_static = ""

            step = {
                "order": action["order"],
                "name": self._generate_step_name(action),
                "action_type": action["action_type"],
                "locator_strategies": action["locator_strategies"],
                "value_static": value_static,
                "value_field": value_field,
                "press_key_after": action.get("key_pressed", ""),
                "wait_after": 500,
                "timeout": 30000,
                "max_retries": 3,
            }
            steps.append(step)

        return {
            "name": workflow_name,
            "steps": steps,
            "recorded_at": datetime.now().isoformat(),
            "action_count": len(steps),
        }

    def _generate_step_name(self, action: Dict) -> str:
        """Generate a human-readable step name."""
        action_type = action["action_type"]
        element_name = (
            action.get("element_name") or
            action.get("element_aria_label") or
            action.get("element_placeholder") or
            action.get("element_text", "")[:30] or
            action.get("element_id", "")[:20] or
            "element"
        )

        if action_type == "click":
            return f"Click {element_name}"
        elif action_type == "fill":
            return f"Fill {element_name}"
        elif action_type == "select":
            return f"Select {element_name}"
        elif action_type == "press_key":
            return f"Press {action.get('key_pressed', 'key')}"
        else:
            return f"{action_type.title()} {element_name}"

    def _looks_like_data_field(self, value: str) -> bool:
        """Check if value looks like it came from Excel data."""
        import re
        patterns = [
            r'^[A-Z]{2,4}-\d+',
            r'^\d{6,}$',
            r'^[A-Z0-9]{5,}-[A-Z0-9]+',
        ]
        for pattern in patterns:
            if re.match(pattern, value):
                return True
        return False

    def _guess_field_name(self, action: Dict) -> str:
        """Guess the Excel field name based on element info."""
        name = action.get("element_name", "").upper()
        label = action.get("element_aria_label", "").upper()
        placeholder = action.get("element_placeholder", "").upper()

        mappings = {
            "SERIAL": "SERIAL NO",
            "PRODUCT": "PRODUCT NO",
            "ITEM": "ITEM NO",
            "DESCRIPTION": "DESCRIPTION",
            "ACCOUNT": "FROM",
        }

        combined = f"{name} {label} {placeholder}"
        for key, field in mappings.items():
            if key in combined:
                return field

        return ""

    def export_to_json(self, filepath: str):
        """Export recorded actions to JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.recorded_actions, f, indent=2, default=str)
