"""
Recording Service

Captures user actions in the browser for workflow creation.
Uses Playwright's tracing and custom JavaScript injection.
"""
import os
import json
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from .locator_engine import LocatorEngine

logger = logging.getLogger(__name__)


class RecorderService:
    """
    Records user actions in the browser.

    Features:
    - Captures clicks, inputs, selections
    - Generates smart locators for each element
    - Takes screenshots at each action
    - Tracks page navigation
    - Exports to workflow format
    """

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.locator_engine: Optional[LocatorEngine] = None

        self.is_recording = False
        self.recorded_actions = []
        self.action_counter = 0
        self.session_id = None
        self.screenshots_dir = None

        # Callbacks
        self.on_action_recorded: Optional[Callable] = None

    def start_recording(
        self,
        url: str,
        session_id: str,
        screenshots_dir: str = None,
        headless: bool = False,
        credentials: Dict[str, str] = None,
    ) -> bool:
        """
        Start a recording session.

        Args:
            url: Starting URL
            session_id: Unique session identifier
            screenshots_dir: Directory to save screenshots
            headless: Run browser in headless mode
            credentials: Optional {"username": str, "password": str} for auto-login

        Returns:
            True if started successfully
        """
        try:
            self.session_id = session_id
            self.screenshots_dir = screenshots_dir or f"/tmp/recordings/{session_id}"
            os.makedirs(self.screenshots_dir, exist_ok=True)

            # Start Playwright
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=headless,
                args=["--start-maximized"]
            )
            self.context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=self.screenshots_dir if not headless else None,
            )
            self.page = self.context.new_page()
            self.locator_engine = LocatorEngine(self.page)

            # Inject recording scripts
            self._inject_recording_scripts()

            # Navigate to URL
            self.page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Auto-login if credentials provided
            if credentials:
                self._handle_login(credentials)

            self.is_recording = True
            self.recorded_actions = []
            self.action_counter = 0

            logger.info(f"Recording started: session={session_id}, url={url}")
            return True

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.stop_recording()
            return False

    def stop_recording(self) -> list:
        """
        Stop recording and return captured actions.

        Returns:
            List of recorded actions
        """
        self.is_recording = False

        try:
            # Get any pending actions from browser
            if self.page:
                pending = self.page.evaluate("window.__recorder?.getActions() || []")
                for action in pending:
                    self._process_action(action)
        except:
            pass

        # Close browser
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

        logger.info(f"Recording stopped: {len(self.recorded_actions)} actions captured")
        return self.recorded_actions

    def _inject_recording_scripts(self):
        """Inject JavaScript to capture user actions."""
        recorder_script = """
        window.__recorder = {
            actions: [],
            isRecording: true,

            getElementInfo: function(element) {
                if (!element) return null;

                const rect = element.getBoundingClientRect();

                // Generate unique CSS selector
                const getCssPath = (el) => {
                    if (el.id) return '#' + CSS.escape(el.id);

                    const path = [];
                    while (el && el.nodeType === Node.ELEMENT_NODE) {
                        let selector = el.nodeName.toLowerCase();
                        if (el.className) {
                            selector += '.' + el.className.trim().split(/\\s+/).map(c => CSS.escape(c)).join('.');
                        }
                        path.unshift(selector);
                        el = el.parentElement;
                    }
                    return path.join(' > ');
                };

                // Generate XPath
                const getXPath = (el) => {
                    if (el.id) return `//*[@id="${el.id}"]`;
                    if (el.name) return `//*[@name="${el.name}"]`;

                    const parts = [];
                    while (el && el.nodeType === Node.ELEMENT_NODE) {
                        let index = 1;
                        let sibling = el.previousElementSibling;
                        while (sibling) {
                            if (sibling.nodeName === el.nodeName) index++;
                            sibling = sibling.previousElementSibling;
                        }
                        parts.unshift(el.nodeName.toLowerCase() + '[' + index + ']');
                        el = el.parentElement;
                    }
                    return '/' + parts.join('/');
                };

                return {
                    tagName: element.tagName.toLowerCase(),
                    id: element.id || '',
                    name: element.getAttribute('name') || '',
                    className: element.className || '',
                    ariaLabel: element.getAttribute('aria-label') || '',
                    placeholder: element.getAttribute('placeholder') || '',
                    text: (element.innerText || '').substring(0, 200),
                    value: element.value || '',
                    type: element.getAttribute('type') || '',
                    role: element.getAttribute('role') || '',
                    dataTestId: element.getAttribute('data-testid') || '',
                    css: getCssPath(element),
                    xpath: getXPath(element),
                    rect: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    }
                };
            },

            recordAction: function(type, element, extra = {}) {
                if (!this.isRecording) return;

                const action = {
                    type: type,
                    timestamp: Date.now(),
                    url: window.location.href,
                    title: document.title,
                    element: this.getElementInfo(element),
                    ...extra
                };

                this.actions.push(action);
                console.log('[Recorder]', type, action.element?.name || action.element?.id || action.element?.text?.substring(0, 30));

                // Send to Python (will be picked up by page.evaluate)
                window.__lastRecordedAction = action;
            },

            getActions: function() {
                const actions = [...this.actions];
                this.actions = [];
                return actions;
            }
        };

        // Capture clicks
        document.addEventListener('click', function(e) {
            window.__recorder.recordAction('click', e.target);
        }, true);

        // Capture input changes
        document.addEventListener('change', function(e) {
            window.__recorder.recordAction('change', e.target, {
                value: e.target.value
            });
        }, true);

        // Capture input typing (debounced)
        let inputTimeout;
        document.addEventListener('input', function(e) {
            clearTimeout(inputTimeout);
            inputTimeout = setTimeout(() => {
                window.__recorder.recordAction('input', e.target, {
                    value: e.target.value
                });
            }, 500);
        }, true);

        // Capture form submissions
        document.addEventListener('submit', function(e) {
            window.__recorder.recordAction('submit', e.target);
        }, true);

        // Capture key presses on inputs
        document.addEventListener('keydown', function(e) {
            if (['Enter', 'Tab', 'Escape'].includes(e.key)) {
                window.__recorder.recordAction('keypress', e.target, {
                    key: e.key
                });
            }
        }, true);

        console.log('[Recorder] Injection complete');
        """

        self.page.add_init_script(recorder_script)

        # Also inject into current page
        try:
            self.page.evaluate(recorder_script)
        except:
            pass

    def poll_actions(self) -> list:
        """
        Poll for new recorded actions from the browser.
        Call this periodically during recording.

        Returns:
            List of new actions
        """
        if not self.is_recording or not self.page:
            return []

        try:
            actions = self.page.evaluate("window.__recorder?.getActions() || []")
            new_actions = []

            for action in actions:
                processed = self._process_action(action)
                if processed:
                    new_actions.append(processed)

            return new_actions
        except Exception as e:
            logger.debug(f"Error polling actions: {e}")
            return []

    def _process_action(self, raw_action: Dict) -> Optional[Dict]:
        """
        Process a raw action from the browser.
        Generates smart locators and saves screenshot.
        """
        if not raw_action.get("element"):
            return None

        self.action_counter += 1
        element_info = raw_action["element"]

        # Generate smart locator strategies
        strategies = self._generate_strategies(element_info)

        # Take screenshot
        screenshot_path = None
        try:
            screenshot_path = os.path.join(
                self.screenshots_dir,
                f"action_{self.action_counter:04d}.png"
            )
            self.page.screenshot(path=screenshot_path)
        except:
            pass

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
            "element_rect": element_info.get("rect", {}),

            # Input data
            "input_value": raw_action.get("value", ""),
            "key_pressed": raw_action.get("key", ""),

            # Generated locators
            "locator_strategies": strategies,

            # Screenshot
            "screenshot_path": screenshot_path,
        }

        self.recorded_actions.append(processed)

        # Callback
        if self.on_action_recorded:
            self.on_action_recorded(processed)

        return processed

    def _generate_strategies(self, element_info: Dict) -> list:
        """Generate locator strategies from element info."""
        strategies = []
        priority = 1

        # data-testid
        if element_info.get("dataTestId"):
            strategies.append({
                "strategy_type": "data-testid",
                "value": element_info["dataTestId"],
                "priority": priority
            })
            priority += 1

        # aria-label
        if element_info.get("ariaLabel"):
            strategies.append({
                "strategy_type": "aria-label",
                "value": element_info["ariaLabel"],
                "priority": priority
            })
            priority += 1

        # name
        if element_info.get("name"):
            strategies.append({
                "strategy_type": "name",
                "value": element_info["name"],
                "priority": priority
            })
            priority += 1

        # id (if not dynamic)
        if element_info.get("id") and not self._is_dynamic_id(element_info["id"]):
            strategies.append({
                "strategy_type": "id",
                "value": element_info["id"],
                "priority": priority
            })
            priority += 1

        # xpath
        if element_info.get("xpath"):
            strategies.append({
                "strategy_type": "xpath",
                "value": element_info["xpath"],
                "priority": priority + 2
            })

        # css
        if element_info.get("css"):
            strategies.append({
                "strategy_type": "css",
                "value": element_info["css"],
                "priority": priority + 3
            })

        # text (for buttons/links)
        if element_info.get("text") and element_info.get("tagName") in ["button", "a"]:
            strategies.append({
                "strategy_type": "text",
                "value": element_info["text"][:50],
                "priority": priority + 4
            })

        return strategies

    def _map_action_type(self, browser_type: str) -> str:
        """Map browser event type to our action type."""
        mapping = {
            "click": "click",
            "input": "fill",
            "change": "fill",
            "submit": "click",
            "keypress": "press_key",
        }
        return mapping.get(browser_type, "click")

    def _is_dynamic_id(self, element_id: str) -> bool:
        """Check if ID is dynamically generated."""
        import re
        patterns = [
            r'[0-9a-f]{8}-[0-9a-f]{4}',
            r'_\d{10,}',
            r'[A-Za-z]+_\d+_',
            r'react-',
            r'ng-',
        ]
        for pattern in patterns:
            if re.search(pattern, element_id, re.IGNORECASE):
                return True
        return False

    def _handle_login(self, credentials: Dict[str, str]):
        """Handle ERP login if login page is detected."""
        # This can be customized based on the ERP system
        pass

    # ==========================================================================
    # EXPORT METHODS
    # ==========================================================================

    def export_to_workflow(self, workflow_name: str) -> Dict:
        """
        Export recorded actions to workflow format.

        Returns:
            Workflow dictionary ready to be saved
        """
        steps = []

        for action in self.recorded_actions:
            # Determine value source
            value_field = ""
            value_static = action.get("input_value", "")

            # Check if value looks like it came from Excel (contains data patterns)
            if value_static and self._looks_like_data_field(value_static):
                value_field = self._guess_field_name(action)
                value_static = ""

            step = {
                "order": action["order"],
                "name": self._generate_step_name(action),
                "action_type": action["action_type"],
                "locator_strategies": action["locator_strategies"],

                # Value configuration
                "value_static": value_static,
                "value_field": value_field,

                # Options
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
        elif action_type == "press_key":
            return f"Press {action.get('key_pressed', 'key')}"
        else:
            return f"{action_type.title()} {element_name}"

    def _looks_like_data_field(self, value: str) -> bool:
        """Check if value looks like it came from Excel data."""
        # Serial numbers, codes, etc.
        import re
        patterns = [
            r'^[A-Z]{2,4}-\d+',  # Codes like RC-123
            r'^\d{6,}$',  # Long numbers
            r'^[A-Z0-9]{5,}-[A-Z0-9]+',  # Serial patterns
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

        # Common mappings
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
