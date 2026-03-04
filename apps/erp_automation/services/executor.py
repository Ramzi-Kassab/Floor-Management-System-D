"""
Workflow Execution Engine

Executes workflows against the ERP system.
Handles data binding, conditional logic, and error recovery.
Includes DebugExecutor for interactive locator debugging.
"""
import os
import re
import time
import base64
import queue
import logging
import threading
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from django.utils import timezone

# Playwright's sync_playwright() creates an internal event loop which causes
# Django to raise SynchronousOnlyOperation for subsequent ORM calls in the
# same process.  Setting this flag tells Django it's safe (dev-only).
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from .locator_engine import LocatorEngine

logger = logging.getLogger(__name__)


# =============================================================================
# D365 INTERACTION ENGINE
# =============================================================================

class D365InteractionEngine:
    """
    Smart interaction engine for D365 ERP elements.

    Each D365 element type (combobox, lookup button, checkbox, etc.) has a
    different interaction pattern. Instead of hardcoding ad-hoc detection
    in _perform_action(), this engine:

    1. Classifies the element type (from step.interaction_mode or runtime detection)
    2. Runs a chain of interaction strategies specific to that element type
    3. Falls back through the chain until one succeeds

    This replaces the fragile hardcoded patterns in the old _perform_action().
    """

    def __init__(self, page):
        self.page = page

    def detect_interaction_mode(self, element) -> str:
        """Classify a D365 element at runtime by inspecting its attributes.

        Used when step.interaction_mode == 'auto'.
        Returns an InteractionMode string value.
        """
        try:
            info = element.evaluate("""el => {
                const dynAncestor = el.closest('[data-dyn-controlname]');
                return {
                    role: el.getAttribute('role') || '',
                    type: el.getAttribute('type') || '',
                    className: (typeof el.className === 'string') ? el.className : '',
                    tagName: el.tagName || '',
                    ariaExpanded: el.getAttribute('aria-expanded'),
                    dynControl: dynAncestor ? (dynAncestor.getAttribute('data-dyn-controlname') || '') : '',
                    ariaLabel: el.getAttribute('aria-label') || '',
                };
            }""")
        except Exception:
            return "standard_input"

        class_name = info.get('className', '')
        role = info.get('role', '')
        el_type = info.get('type', '')
        tag = info.get('tagName', '').lower()
        dyn_control = info.get('dynControl', '')

        # Lookup buttons — need double-click to open flyout
        if 'lookupButton' in class_name:
            return "lookup_button"

        # Combobox — needs Alt+ArrowDown to reliably open
        if role == 'combobox':
            return "combobox"

        # Checkbox / toggle switch
        if role == 'checkbox' or el_type == 'checkbox':
            return "checkbox_toggle"
        if 'checkbox' in class_name.lower() or 'ToggleSwitch' in class_name:
            return "checkbox_toggle"

        # Dropdown option items (the item being SELECTED, not the trigger)
        if role in ('option', 'menuitem', 'treeitem', 'listitem'):
            return "custom_dropdown"

        # Tab headers
        if role == 'tab':
            return "tab_header"

        # Dialog buttons (OK, Cancel, Yes, No) — often CommandButton class
        if 'CommandButton' in class_name:
            return "dialog_button"
        if dyn_control and ('button' in dyn_control.lower() or 'ok' in dyn_control.lower()):
            return "dialog_button"

        # Navigation buttons (toolbar items)
        if tag == 'button' and ('SystemDefined' in class_name or 'toolbar' in class_name.lower()):
            return "nav_button"

        # Segmented entry (D365 multi-part input controls)
        if 'segmented' in class_name.lower() or 'segment' in dyn_control.lower():
            return "segmented_entry"

        return "standard_input"

    def execute_interaction(self, action_type: str, element, value: str, step) -> Dict[str, Any]:
        """Execute an interaction using the appropriate strategy chain.

        Args:
            action_type: The action to perform (click, fill, select, check, etc.)
            element: The Playwright element handle
            value: The value to use (for fill, select, etc.)
            step: The WorkflowStep model instance

        Returns:
            {"success": bool, "message": str, ...}
        """
        # Determine interaction mode
        mode = getattr(step, 'interaction_mode', 'auto') or 'auto'
        if mode == 'auto':
            mode = self.detect_interaction_mode(element)
            logger.info(f"Step {step.order}: Auto-detected interaction mode: {mode}")

        # Delegate to the appropriate action handler
        if action_type == "click":
            return self._execute_click(element, step, mode)
        elif action_type == "fill":
            return self._execute_fill(element, value, step, mode)
        elif action_type == "select":
            return self._execute_select(element, value, step, mode)
        elif action_type == "check":
            return self._execute_check(element, value, step, mode)
        elif action_type == "right_click":
            element.click(button="right", timeout=step.timeout)
            return {"success": True, "message": "Right-clicked (context menu)"}
        elif action_type == "hover":
            element.hover()
            return {"success": True, "message": "Hovered"}
        elif action_type == "scroll":
            element.scroll_into_view_if_needed()
            return {"success": True, "message": "Scrolled into view"}
        elif action_type == "wait":
            element.wait_for(state="visible", timeout=step.timeout)
            return {"success": True, "message": "Element visible"}
        elif action_type == "assert_text":
            text = element.inner_text()
            if value in text:
                return {"success": True, "message": f"Text found: {value}"}
            return {"success": False, "message": f"Text '{value}' not found in '{text}'"}
        elif action_type == "assert_visible":
            if element.is_visible():
                return {"success": True, "message": "Element is visible"}
            return {"success": False, "message": "Element not visible"}
        else:
            return {"success": False, "message": f"Unknown action: {action_type}"}

    # ── Click Chains ─────────────────────────────────────────────────

    def _execute_click(self, element, step, mode: str) -> Dict[str, Any]:
        """Execute click with mode-specific strategy chain."""
        timeout = step.timeout

        if mode == "lookup_button":
            # Lookup button needs TWO clicks: first focuses, second opens flyout
            return self._click_chain(element, timeout, [
                ("click", {}),
                ("wait", {"ms": 500}),
                ("click_again", {"force": True}),
            ], label="lookup_button")

        elif mode == "combobox":
            # Combobox needs click THEN Alt+ArrowDown to open dropdown list
            return self._click_chain(element, timeout, [
                ("click", {}),
                ("wait", {"ms": 300}),
                ("press_key", {"key": "Alt+ArrowDown"}),
            ], label="combobox")

        elif mode == "checkbox_toggle":
            # Checkbox: try click, then force-click, then Space key
            return self._click_chain(element, timeout, [
                ("click", {}),
            ], fallbacks=[
                ("force_click", {}),
                ("press_key", {"key": "Space"}),
            ], label="checkbox_toggle")

        elif mode == "dialog_button":
            # Dialog OK/Cancel: try click, then force-click, then Enter
            return self._click_chain(element, timeout, [
                ("click", {}),
            ], fallbacks=[
                ("force_click", {}),
                ("press_key", {"key": "Enter"}),
            ], label="dialog_button")

        elif mode == "nav_button":
            # Navigation/toolbar buttons: try click, force-click, JS dispatch
            return self._click_chain(element, timeout, [
                ("click", {}),
            ], fallbacks=[
                ("force_click", {}),
                ("js_click", {}),
            ], label="nav_button")

        elif mode == "tab_header":
            # Tab headers: scroll into view first, then click
            return self._click_chain(element, timeout, [
                ("scroll_and_click", {}),
            ], fallbacks=[
                ("force_click", {}),
            ], label="tab_header")

        elif mode == "custom_dropdown":
            # Dropdown option: just click it (it's the option, not the trigger)
            return self._click_chain(element, timeout, [
                ("click", {}),
            ], fallbacks=[
                ("force_click", {}),
            ], label="custom_dropdown")

        else:
            # Standard input / segmented_entry — default click with force fallback
            return self._click_chain(element, timeout, [
                ("click", {}),
            ], fallbacks=[
                ("force_click", {}),
            ], label="standard_input")

    def _click_chain(self, element, timeout, primary_steps, fallbacks=None, label="") -> Dict[str, Any]:
        """Execute a chain of click steps. Primary steps all run; fallbacks only on failure."""
        try:
            # Scroll into view first
            try:
                element.scroll_into_view_if_needed(timeout=3000)
            except Exception:
                pass

            # Execute primary steps
            for action, params in primary_steps:
                self._do_click_action(element, action, timeout, params)

            return {"success": True, "message": f"Clicked ({label})"}

        except Exception as primary_err:
            if not fallbacks:
                # No fallbacks — re-raise as failure
                return {"success": False, "message": f"Click failed ({label}): {primary_err}"}

            # Try fallback strategies
            logger.warning(f"Primary click failed ({label}): {primary_err}, trying fallbacks")
            for action, params in fallbacks:
                try:
                    self._do_click_action(element, action, timeout, params)
                    return {"success": True, "message": f"Clicked via fallback {action} ({label})"}
                except Exception as fb_err:
                    logger.debug(f"Fallback {action} failed: {fb_err}")
                    continue

            return {"success": False, "message": f"All click strategies failed ({label})"}

    def _do_click_action(self, element, action, timeout, params):
        """Execute a single click sub-action."""
        if action == "click":
            element.click(timeout=timeout)
        elif action == "click_again":
            element.click(timeout=timeout, force=params.get("force", False))
        elif action == "force_click":
            element.click(timeout=timeout, force=True)
        elif action == "scroll_and_click":
            element.scroll_into_view_if_needed(timeout=3000)
            element.click(timeout=timeout)
        elif action == "js_click":
            element.evaluate("el => el.click()")
        elif action == "press_key":
            element.press(params.get("key", "Enter"))
        elif action == "wait":
            self.page.wait_for_timeout(params.get("ms", 300))

    # ── Fill Chains ──────────────────────────────────────────────────

    def _execute_fill(self, element, value: str, step, mode: str) -> Dict[str, Any]:
        """Execute fill with mode-specific strategy chain."""
        timeout = step.timeout
        clear = getattr(step, 'clear_before_fill', False)

        if mode == "combobox":
            # Combobox fill: clear → type → Tab (triggers selection)
            return self._fill_chain(element, value, timeout, clear, [
                ("clear_and_type", {"delay": 20}),
            ], fallbacks=[
                ("click_type", {"delay": 20}),
            ], label="combobox")

        elif mode == "segmented_entry":
            # Segmented: click to focus segment, then type
            return self._fill_chain(element, value, timeout, clear, [
                ("click_type", {"delay": 20}),
            ], label="segmented_entry")

        else:
            # Standard: fill() with click+type fallback
            return self._fill_chain(element, value, timeout, clear, [
                ("fill", {}),
            ], fallbacks=[
                ("click_type", {"delay": 20}),
            ], label=mode or "standard")

    def _fill_chain(self, element, value, timeout, clear, primary_steps, fallbacks=None, label="") -> Dict[str, Any]:
        """Execute a chain of fill steps."""
        if clear:
            try:
                element.clear()
            except Exception:
                pass

        for action, params in primary_steps:
            try:
                self._do_fill_action(element, value, action, timeout, params)
                return {"success": True, "message": f"Filled ({label}): {value[:50]}...", "value": value}
            except Exception as e:
                logger.warning(f"Fill {action} failed ({label}): {e}")
                if not fallbacks:
                    return {"success": False, "message": f"Fill failed ({label}): {e}"}

        # Try fallbacks
        if fallbacks:
            for action, params in fallbacks:
                try:
                    self._do_fill_action(element, value, action, timeout, params)
                    return {"success": True, "message": f"Filled via fallback {action} ({label}): {value[:50]}...", "value": value}
                except Exception as fb_err:
                    logger.debug(f"Fill fallback {action} failed: {fb_err}")

        return {"success": False, "message": f"All fill strategies failed ({label})"}

    def _do_fill_action(self, element, value, action, timeout, params):
        """Execute a single fill sub-action."""
        if action == "fill":
            element.fill(value, timeout=timeout)
        elif action == "click_type":
            element.click(timeout=5000)
            self.page.keyboard.press("Control+a")
            self.page.wait_for_timeout(100)
            self.page.keyboard.type(value, delay=params.get("delay", 20))
        elif action == "clear_and_type":
            element.click(timeout=5000)
            self.page.keyboard.press("Control+a")
            self.page.keyboard.press("Delete")
            self.page.wait_for_timeout(100)
            self.page.keyboard.type(value, delay=params.get("delay", 20))

    # ── Select Chain ─────────────────────────────────────────────────

    def _execute_select(self, element, value: str, step, mode: str) -> Dict[str, Any]:
        """Execute select — D365 never uses native <select>."""
        try:
            tag = element.evaluate("el => el.tagName.toLowerCase()")
        except Exception:
            tag = ""

        if tag == "select":
            # Rare native select
            element.select_option(value=value)
            return {"success": True, "message": f"Selected (native): {value}"}

        # D365 custom dropdown — just click the option element
        try:
            element.click(timeout=step.timeout)
            return {"success": True, "message": f"Selected (click): {value}"}
        except Exception:
            try:
                element.click(timeout=step.timeout, force=True)
                return {"success": True, "message": f"Selected (force-click): {value}"}
            except Exception as e:
                return {"success": False, "message": f"Select failed: {e}"}

    # ── Check Chain ──────────────────────────────────────────────────

    def _execute_check(self, element, value: str, step, mode: str) -> Dict[str, Any]:
        """Execute check/uncheck with D365-aware fallbacks."""
        should_check = value.lower() in ("true", "1", "yes", "checked")

        try:
            if should_check:
                element.check()
            else:
                element.uncheck()
            return {"success": True, "message": f"Checked: {value}"}
        except Exception:
            # D365 checkboxes are often custom divs — try click toggle
            try:
                element.click(timeout=step.timeout)
                return {"success": True, "message": f"Toggled via click: {value}"}
            except Exception:
                try:
                    element.click(timeout=step.timeout, force=True)
                    return {"success": True, "message": f"Toggled via force-click: {value}"}
                except Exception as e:
                    return {"success": False, "message": f"Check failed: {e}"}


class WorkflowExecutor:
    """
    Executes workflows with smart error handling and retry logic.

    Features:
    - Data binding from Excel/dict sources
    - Conditional step execution
    - Auto-retry with strategy fallback
    - Screenshot on failure
    - Progress callbacks for UI updates
    """

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.locator_engine: Optional[LocatorEngine] = None
        self.interaction_engine: Optional[D365InteractionEngine] = None

        # Execution state
        self.is_running = False
        self.should_stop = False
        self.context_vars = {}  # Variables during execution
        self.screenshots_dir = None

        # Callbacks
        self.on_step_start: Optional[Callable] = None
        self.on_step_complete: Optional[Callable] = None
        self.on_step_error: Optional[Callable] = None
        self.on_workflow_complete: Optional[Callable] = None

    def start_browser(
        self,
        url: str = None,
        headless: bool = False,
        credentials: Dict[str, str] = None,
        timeout: int = 60000,
    ) -> bool:
        """
        Start browser and optionally navigate to URL.

        Args:
            url: Starting URL
            headless: Run headless
            credentials: {"username": str, "password": str} for login prompt
            timeout: Navigation timeout

        Returns:
            True if successful
        """
        try:
            self.playwright = sync_playwright().start()

            # Try to find an available browser executable
            executable_path = self._find_browser_executable()

            launch_args = {
                "headless": headless,
                "args": ["--start-maximized", "--no-sandbox", "--disable-dev-shm-usage"]
            }

            if executable_path:
                launch_args["executable_path"] = executable_path
                logger.info(f"Using browser at: {executable_path}")

            self.browser = self.playwright.chromium.launch(**launch_args)
            # Use no_viewport=True so --start-maximized actually works
            # and the browser fills the entire screen (D365 needs full width)
            self.context = self.browser.new_context(no_viewport=True)
            self.page = self.context.new_page()
            self.locator_engine = LocatorEngine(self.page)
            self.interaction_engine = D365InteractionEngine(self.page)

            if url:
                # Ensure URL has a protocol — Playwright requires a full URL
                nav_url = url.strip()
                if nav_url and not nav_url.startswith(('http://', 'https://')):
                    nav_url = 'https://' + nav_url
                self.page.goto(nav_url, wait_until="domcontentloaded", timeout=timeout)

            # Handle login if credentials provided
            if credentials:
                self._handle_login(credentials)

            # Use cross-platform temp directory for screenshots
            import tempfile
            self.screenshots_dir = os.path.join(tempfile.gettempdir(), "erp_automation", "screenshots")
            os.makedirs(self.screenshots_dir, exist_ok=True)

            logger.info("Browser started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            self.stop_browser()
            return False

    def _find_browser_executable(self) -> Optional[str]:
        """
        Find an available Chromium browser executable.
        Checks Playwright cache for any available version.
        """
        import glob
        import sys

        # Possible cache locations (platform-specific)
        # Priority: root cache first (for containers/Codespaces), then user cache
        cache_paths = [
            "/root/.cache/ms-playwright",  # Linux root (check first for containers)
            os.path.expanduser("~/.cache/ms-playwright"),  # Linux user
            os.path.expanduser("~/Library/Caches/ms-playwright"),  # macOS
        ]

        # Windows paths (highest priority on Windows)
        if sys.platform == "win32":
            local_app_data = os.environ.get("LOCALAPPDATA", "")
            if local_app_data:
                cache_paths.insert(0, os.path.join(local_app_data, "ms-playwright"))
            # Also check user profile
            user_profile = os.environ.get("USERPROFILE", "")
            if user_profile:
                cache_paths.insert(0, os.path.join(user_profile, "AppData", "Local", "ms-playwright"))

        for cache_path in cache_paths:
            if not os.path.exists(cache_path):
                continue

            # Look for chromium directories (any version)
            chromium_dirs = sorted(
                glob.glob(os.path.join(cache_path, "chromium-*")),
                reverse=True  # Prefer newer versions
            )

            for chromium_dir in chromium_dirs:
                # Windows path (check first on Windows)
                chrome_win = os.path.join(chromium_dir, "chrome-win", "chrome.exe")
                if os.path.exists(chrome_win):
                    return chrome_win

                # Linux path
                chrome_linux = os.path.join(chromium_dir, "chrome-linux", "chrome")
                if os.path.exists(chrome_linux):
                    return chrome_linux

                # macOS path
                chrome_mac = os.path.join(
                    chromium_dir, "chrome-mac", "Chromium.app",
                    "Contents", "MacOS", "Chromium"
                )
                if os.path.exists(chrome_mac):
                    return chrome_mac

        # Return None to use default Playwright-managed browser
        return None

    def is_browser_alive(self) -> bool:
        """Check if browser is still usable (not crashed/closed)."""
        if not self.page or not self.browser:
            return False
        try:
            # Try a harmless operation to check if the page is still connected
            self.page.evaluate("() => true")
            return True
        except Exception:
            logger.warning("Browser health check failed — page/browser is dead")
            return False

    def stop_browser(self):
        """Close browser and cleanup."""
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
        self.locator_engine = None
        self.interaction_engine = None

        logger.info("Browser stopped")

    def _take_error_screenshot(self, step_order: int) -> Optional[str]:
        """Take a screenshot on failure and return the file path."""
        if not self.page or not self.screenshots_dir:
            return None
        try:
            path = os.path.join(self.screenshots_dir, f"error_step_{step_order}.png")
            self.page.screenshot(path=path)
            logger.info(f"Error screenshot saved: {path}")
            return path
        except Exception:
            return None

    def _create_step_record(self, execution_record, step, status, result, started, retries=0):
        """Create a StepExecution record for debugging/tracking."""
        if not execution_record:
            return None
        try:
            from ..models import StepExecution
            se = StepExecution.objects.create(
                execution=execution_record,
                step=step,
                status=status,
                started_at=started,
                completed_at=timezone.now(),
                retry_count=retries,
                error_message=result.get("message", "")[:500] if not result.get("success") else "",
            )
            return se
        except Exception as e:
            logger.warning(f"Could not create StepExecution record: {e}")
            return None

    def execute_workflow(
        self,
        workflow,  # Django Workflow model
        row_data: Dict[str, Any] = None,
        execution_record=None,  # Django WorkflowExecution model
    ) -> Dict[str, Any]:
        """
        Execute a workflow with optional data binding.

        Args:
            workflow: Workflow model instance
            row_data: Excel row data for template substitution
            execution_record: Optional execution tracking model

        Returns:
            {"success": bool, "message": str, "steps_completed": int}
        """
        if not self.page:
            return {"success": False, "message": "Browser not started", "steps_completed": 0}

        self.is_running = True
        self.should_stop = False
        self.context_vars = {}
        steps_completed = 0

        try:
            # Update execution record
            if execution_record:
                execution_record.status = "running"
                execution_record.started_at = timezone.now()
                execution_record.save()

            # Get condition value for branching
            condition_value = None
            if workflow.condition_field and row_data:
                condition_value = self._normalize_condition(
                    row_data.get(workflow.condition_field, "")
                )
                logger.info(f"Condition: {workflow.condition_field}={condition_value}")

            # Get steps for this condition
            raw_steps = list(workflow.get_steps_for_condition(condition_value))

            # ── Expand repeat groups ──────────────────────────────────
            expanded_steps = []  # list of (WorkflowStep, loop_context_or_None)
            ri = 0
            while ri < len(raw_steps):
                s = raw_steps[ri]
                if s.repeat_group:
                    group_name = s.repeat_group
                    group_steps = []
                    data_source_key = None
                    while ri < len(raw_steps) and raw_steps[ri].repeat_group == group_name:
                        if raw_steps[ri].repeat_data_source:
                            data_source_key = raw_steps[ri].repeat_data_source
                        group_steps.append(raw_steps[ri])
                        ri += 1
                    data_source_key = data_source_key or group_name.upper()
                    loop_data = row_data.get(data_source_key, []) if row_data else []
                    if isinstance(loop_data, list):
                        for loop_idx, loop_item in enumerate(loop_data):
                            loop_ctx = {'LOOP_INDEX': str(loop_idx), 'LOOP_ITERATION': str(loop_idx + 1)}
                            if isinstance(loop_item, dict):
                                for k, v in loop_item.items():
                                    loop_ctx[f'LOOP_{k}'] = str(v) if v else ''
                            for gs in group_steps:
                                expanded_steps.append((gs, loop_ctx))
                else:
                    expanded_steps.append((s, None))
                    ri += 1

            total_steps = len(expanded_steps)
            logger.info(f"Executing workflow '{workflow.name}' with {total_steps} steps (expanded)")

            for step, loop_ctx in expanded_steps:
                if self.should_stop:
                    logger.info("Workflow stopped by user")
                    break

                # Merge loop context
                if loop_ctx:
                    step_row_data = dict(row_data) if row_data else {}
                    step_row_data.update(loop_ctx)
                else:
                    step_row_data = row_data

                # Check if browser is still alive before each step
                if not self.is_browser_alive():
                    error_msg = "Browser closed unexpectedly. Aborting workflow."
                    logger.error(error_msg)
                    if execution_record:
                        execution_record.status = "failed"
                        execution_record.error_message = error_msg
                        execution_record.completed_at = timezone.now()
                        execution_record.save()
                    return {
                        "success": False,
                        "message": error_msg,
                        "steps_completed": steps_completed,
                        "context": dict(self.context_vars),
                        "browser_dead": True,
                    }

                step_started = timezone.now()

                # Callback: step starting
                if self.on_step_start:
                    self.on_step_start(step, steps_completed, total_steps)

                # Execute step
                loop_info = f" [Loop {loop_ctx['LOOP_ITERATION']}: {loop_ctx.get('LOOP_ITEM','')}]" if loop_ctx else ""
                logger.info(f"[{steps_completed+1}/{total_steps}] Step {step.order}: {step.name}{loop_info} ({step.action_type})")
                result = self._execute_step(step, step_row_data)

                if result["success"]:
                    steps_completed += 1
                    self._create_step_record(execution_record, step, "success", result, step_started)
                    if self.on_step_complete:
                        self.on_step_complete(step, result)
                else:
                    logger.error(f"Step {step.order} '{step.name}' failed: {result['message']}")

                    # Take error screenshot
                    screenshot_path = self._take_error_screenshot(step.order)

                    # Record the failed step
                    self._create_step_record(
                        execution_record, step, "failed", result, step_started,
                        retries=step.max_retries
                    )

                    if self.on_step_error:
                        self.on_step_error(step, result)

                    if not step.continue_on_error:
                        # Try error handler if defined
                        if step.error_handler_step:
                            self._execute_step(step.error_handler_step, row_data)

                        error_msg = f"Step {step.order} '{step.name}' failed: {result['message']}"
                        if screenshot_path:
                            error_msg += f"\nScreenshot: {screenshot_path}"

                        if execution_record:
                            execution_record.status = "failed"
                            execution_record.error_message = error_msg
                            execution_record.completed_at = timezone.now()
                            execution_record.save()

                        return {
                            "success": False,
                            "message": error_msg,
                            "steps_completed": steps_completed,
                            "failed_step": step.order,
                            "failed_step_name": step.name,
                            "screenshot": screenshot_path,
                        }

            # Success
            if execution_record:
                execution_record.status = "success"
                execution_record.completed_at = timezone.now()
                execution_record.context = self.context_vars
                execution_record.save()

            if self.on_workflow_complete:
                self.on_workflow_complete(True, steps_completed)

            return {
                "success": True,
                "message": f"Workflow completed: {steps_completed} steps",
                "steps_completed": steps_completed,
                "context": self.context_vars
            }

        except Exception as e:
            logger.exception(f"Workflow execution error: {e}")

            # Take error screenshot
            self._take_error_screenshot(0)

            if execution_record:
                execution_record.status = "failed"
                execution_record.error_message = str(e)
                execution_record.completed_at = timezone.now()
                execution_record.save()

            return {
                "success": False,
                "message": str(e),
                "steps_completed": steps_completed
            }
        finally:
            self.is_running = False

    def _execute_step(
        self,
        step,  # WorkflowStep model
        row_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""
        logger.info(f"Executing step {step.order}: {step.name} ({step.action_type})")

        # Get the value to use (from static, field, or template)
        value = step.get_value(row_data, self.context_vars)

        # ── PAGE AWARENESS: Pre-step state ─────────────────────────
        _page_reader = None
        _pre_grid_rows = None
        if self.page:
            try:
                from .page_awareness import D365PageReader
                _page_reader = D365PageReader(self.page)
                pre_state = _page_reader.snapshot_short()
                logger.info(f"[PageState] BEFORE '{step.name}': {pre_state}")

                # For "New" actions on grids, capture row count for comparison
                if step.action_type == 'click' and step.name and 'new' in step.name.lower():
                    _pre_grid_rows = _page_reader.count_grid_rows()
            except Exception as pa_err:
                logger.debug(f"[PageState] Pre-step read failed: {pa_err}")

        # Special actions that don't need a locator
        if step.action_type == "wait_time":
            wait_ms = int(value) if value else step.wait_after
            self.page.wait_for_timeout(wait_ms)
            return {"success": True, "message": f"Waited {wait_ms}ms"}

        if step.action_type == "navigate":
            # Navigation event from recorder — wait for page to finish loading
            # This is a synthetic event, no element to find
            wait_ms = step.wait_after if step.wait_after > 0 else 5000
            try:
                self.page.wait_for_load_state("domcontentloaded", timeout=wait_ms)
            except PlaywrightTimeout:
                pass  # D365 SPA may not trigger full load state change
            self.page.wait_for_timeout(min(wait_ms, 3000))
            # ── PAGE AWARENESS: Post-navigate state ──────────
            if _page_reader:
                try:
                    post_state = _page_reader.snapshot_short()
                    logger.info(f"[PageState] AFTER  '{step.name}': {post_state}")
                    ctx = _page_reader.get_page_context()
                    if ctx.get("form_name"):
                        logger.info(f"[PageState] 📍 Now on form: {ctx['form_name']} — {ctx.get('title', '')}")
                except Exception:
                    pass
            return {"success": True, "message": f"Navigation wait {wait_ms}ms"}

        if step.action_type == "press_key":
            key = value or step.press_key_after
            if not key:
                return {"success": False, "message": "No key specified for press_key"}

            # Special tokens for D365 FixedDataTable grid scrolling
            # Supports fraction suffix: SCROLL_GRID_RIGHT:0.3 (scrolls 30% of track)
            key_upper = key.upper().strip()
            if key_upper.startswith("SCROLL_GRID_LEFT") or key_upper.startswith("SCROLL_GRID_RIGHT"):
                direction = "left" if "LEFT" in key_upper else "right"
                # Parse optional fraction from "SCROLL_GRID_RIGHT:0.3"
                distance_fraction = 1.0
                if ":" in key_upper:
                    try:
                        distance_fraction = float(key_upper.split(":")[1])
                    except (ValueError, IndexError):
                        pass
                result = self._scroll_grid_horizontal(direction, distance_fraction=distance_fraction)
                if step.wait_after > 0:
                    self.page.wait_for_timeout(step.wait_after)
                return result

            # Browser zoom via Ctrl+Minus/Plus keyboard shortcut
            if key_upper.startswith("ZOOM_"):
                try:
                    if key_upper == "ZOOM_OUT":
                        self.page.keyboard.press("Control+Minus")
                        msg = "Zoomed out 1 step"
                    elif key_upper in ("ZOOM_IN", "ZOOM_100"):
                        self.page.keyboard.press("Control+0")
                        msg = "Zoom reset to 100%"
                    else:
                        import math
                        target_pct = int(key_upper.split("_")[1])
                        n = max(1, round(math.log(target_pct / 100) / math.log(0.8333)))
                        self.page.keyboard.press("Control+0")
                        self.page.wait_for_timeout(200)
                        for _ in range(n):
                            self.page.keyboard.press("Control+Minus")
                            self.page.wait_for_timeout(200)
                        msg = f"Zoomed to ~{round(100 * 0.8333**n)}% ({n} steps)"
                    logger.info(f"[zoom] {msg}")
                    if step.wait_after > 0:
                        self.page.wait_for_timeout(step.wait_after)
                    return {"success": True, "message": msg}
                except Exception as e:
                    logger.warning(f"[zoom] Keyboard zoom failed: {e}")
                    return {"success": False, "message": f"Keyboard zoom failed: {e}"}

            self.page.keyboard.press(key)
            logger.info(f"[press_key] Pressed '{key}'")
            if step.wait_after > 0:
                self.page.wait_for_timeout(step.wait_after)
            return {"success": True, "message": f"Pressed {key}"}

        if step.action_type == "type_text":
            # Type text into the focused element. If a locator is provided,
            # first verify/click it to ensure focus is on the correct field.
            if not value:
                return {"success": False, "message": "No value for type_text"}
            try:
                # --- Focus verification: if locator exists, confirm field before typing ---
                if step.locator:
                    logger.info(f"[type_text] Locator provided — verifying focus on '{step.locator.name}'")
                    el = self.locator_engine.find_element(step.locator)
                    if el:
                        # Check if this element already has focus
                        is_focused = False
                        try:
                            is_focused = el.evaluate("el => el === document.activeElement")
                        except Exception:
                            pass
                        if is_focused:
                            logger.info(f"[type_text] Focus verified — already on '{step.locator.name}'")
                        else:
                            logger.info(f"[type_text] Focus MISMATCH — clicking '{step.locator.name}' to correct")
                            try:
                                el.click(timeout=3000)
                                self.page.wait_for_timeout(300)
                            except Exception as click_err:
                                logger.warning(f"[type_text] Click to fix focus failed: {click_err}")
                    else:
                        logger.warning(f"[type_text] Locator '{step.locator.name}' not found — typing into current focus")

                if step.clear_before_fill:
                    self.page.keyboard.press("Control+a")
                    self.page.keyboard.press("Delete")
                    self.page.wait_for_timeout(200)
                self.page.keyboard.insert_text(value)
                target_info = f"'{step.locator.name}'" if step.locator else "focused element"
                logger.info(f"[type_text] Inserted '{value}' into {target_info}")
                if step.press_key_after:
                    self.page.wait_for_timeout(100)
                    self.page.keyboard.press(step.press_key_after)
                    logger.info(f"[type_text] Pressed '{step.press_key_after}' after typing")
                if step.wait_after > 0:
                    logger.info(f"[type_text] Waiting {step.wait_after}ms after action")
                    self.page.wait_for_timeout(step.wait_after)

                return {"success": True, "message": f"Typed '{value}' into {target_info}"}
            except Exception as e:
                return {"success": False, "message": f"type_text failed: {e}"}

        if step.action_type == "click_dynamic_locator":
            # Click an element found by substituting the resolved value into
            # the locator's strategy templates.  Strategies can use any
            # {{PLACEHOLDER}} (e.g. {{VALUE}}, {{ROUTE}}, {{ITEM}}) — all
            # are replaced with the step's resolved value at runtime.
            # Includes D365 grid scroll support for virtualized rows.
            if not value:
                return {"success": False, "message": "No value for click_dynamic_locator"}
            try:
                escaped = value.replace('"', '\\"')

                # Build selectors from locator strategies — replace ANY
                # {{…}} placeholder with the resolved value so users can
                # name placeholders however they like ({{VALUE}}, {{ROUTE}}, etc.)
                selectors = []
                if step.locator:
                    for strat in step.locator.strategies.filter(is_active=True).order_by('priority'):
                        sel_value = re.sub(r'\{\{[^}]+\}\}', escaped, strat.value)
                        selectors.append((strat.strategy_type, sel_value))
                        logger.info(f"[click_dynamic_locator] Strategy: {strat.strategy_type}='{sel_value}' (raw: '{strat.value}')")
                logger.info(f"[click_dynamic_locator] Resolved value='{value}', {len(selectors)} selectors built")
                if not selectors:
                    selectors = [
                        ('css', f'input[value="{escaped}"].dyn-hyperlink'),
                        ('css', f'input[value="{escaped}"]'),
                    ]

                # ── FINDING: CSS/XPath selectors (primary) + JS .value search (fallback) ──
                # Playwright's loc.is_visible(timeout=...) auto-waits for elements to
                # appear after scrolling — critical for D365 virtualized grids where
                # rows take a few hundred ms to render after PageDown.
                # JS frame.evaluate() runs once with no retry, so it's the fallback.

                def _find_and_dblclick_selectors(page_or_frame, label="page"):
                    """Find element by CSS/XPath selectors, then dblclick combo. Returns True if found."""
                    for stype, sel in selectors:
                        try:
                            if stype == 'css':
                                loc = page_or_frame.locator(sel).first
                            elif stype == 'xpath':
                                loc = page_or_frame.locator(f"xpath={sel}").first
                            else:
                                loc = page_or_frame.locator(sel).first
                            if loc.is_visible(timeout=2000):
                                logger.info(f"[click_dynamic_locator] Found {stype}='{sel}' on {label}")
                                self._click_grid_hyperlink(loc, value)
                                return True
                        except Exception:
                            pass
                    return False

                # JS search fallback for D365 inputs whose .value is set via JS
                FIND_BY_VALUE_JS = """(targetVal) => {
                    const inputs = document.querySelectorAll('input');
                    for (const inp of inputs) {
                        if (inp.value === targetVal) {
                            const rect = inp.getBoundingClientRect();
                            if (rect.width === 0 || rect.height === 0) continue;
                            return {found: true, id: inp.id || '', cx: rect.x + rect.width/2, cy: rect.y + rect.height/2};
                        }
                    }
                    return {found: false};
                }"""

                def _js_find_and_dblclick():
                    """JS .value search across all frames, then dblclick at coords. Returns True if found."""
                    all_frames = [self.page] + list(self.page.frames[1:])
                    for fi, frame in enumerate(all_frames):
                        frame_label = "main" if fi == 0 else f"iframe[{fi}]"
                        try:
                            el_info = frame.evaluate(FIND_BY_VALUE_JS, value)
                        except Exception:
                            continue
                        if not el_info or not el_info.get("found"):
                            continue
                        logger.info(f"[click_dynamic_locator] JS .value match in {frame_label}, id={el_info.get('id')}")
                        # Click via #id locator (dblclick combo) or coordinates
                        if el_info.get("id"):
                            try:
                                loc = frame.locator(f"[id='{el_info['id']}']").first
                                if loc.is_visible(timeout=2000):
                                    self._click_grid_hyperlink(loc, value)
                                    return True
                            except Exception:
                                pass
                        # Coordinate fallback: dblclick at JS-found position
                        cx, cy = el_info["cx"], el_info["cy"]
                        try:
                            if fi == 0:
                                self.page.mouse.dblclick(cx, cy)
                            else:
                                frame.locator("body").dblclick(
                                    position={"x": int(cx), "y": int(cy)}, timeout=5000)
                            self.page.wait_for_timeout(500)
                            logger.info(f"[click_dynamic_locator] Dblclick at ({cx:.0f},{cy:.0f}) in {frame_label}")
                            return True
                        except Exception as e:
                            logger.debug(f"[click_dynamic_locator] Coord dblclick failed: {e}")
                    return False

                def _try_all():
                    """Try CSS/XPath on main page + all iframes, then JS .value fallback."""
                    # Method 1: CSS/XPath selectors with Playwright auto-wait
                    if _find_and_dblclick_selectors(self.page, "main"):
                        return True
                    for frame in self.page.frames[1:]:
                        if _find_and_dblclick_selectors(frame, "iframe"):
                            return True
                    # Method 2: JS .value search (fallback)
                    if _js_find_and_dblclick():
                        return True
                    return False

                # Phase 1: Try visible elements
                found = _try_all()

                # Phase 2: Mouse wheel scroll — no keyboard focus needed
                MAX_SCROLLS = 50
                if not found:
                    logger.info(f"[click_dynamic_locator] '{value}' not visible, scrolling grid via mouse.wheel...")

                    # Position mouse over the grid body for wheel events
                    grid_cx, grid_cy = None, None
                    try:
                        grid_el = self.page.locator(".fixedDataTableLayout_body").first
                        if grid_el.is_visible(timeout=3000):
                            box = grid_el.bounding_box()
                            if box:
                                grid_cx = box['x'] + box['width'] / 2
                                grid_cy = box['y'] + box['height'] / 2
                    except Exception:
                        pass
                    if not grid_cx:
                        # Fallback: use first visible hyperlink position
                        try:
                            hl = self.page.locator("input.dyn-hyperlink").first
                            if hl.is_visible(timeout=2000):
                                box = hl.bounding_box()
                                if box:
                                    grid_cx = box['x'] + box['width'] / 2
                                    grid_cy = box['y'] + box['height'] / 2
                        except Exception:
                            pass
                    if not grid_cx:
                        grid_cx, grid_cy = 600, 400  # Last resort center
                    logger.info(f"[click_dynamic_locator] Mouse wheel at ({grid_cx:.0f}, {grid_cy:.0f})")

                    self.page.mouse.move(grid_cx, grid_cy)
                    last_bottom = None
                    same_bottom_count = 0

                    for scroll_num in range(MAX_SCROLLS):
                        # Scroll down ~one page via mouse wheel (800px ≈ 10-12 grid rows)
                        self.page.mouse.wheel(0, 800)
                        self.page.wait_for_timeout(600)

                        # Check for target
                        if _try_all():
                            found = True
                            logger.info(f"[click_dynamic_locator] ✓ Found '{value}' after {scroll_num + 1} wheel scrolls")
                            break

                        # Detect overshoot or bottom via visible grid values
                        try:
                            visible_values = self._read_grid_hyperlink_values()
                            if visible_values:
                                if scroll_num % 3 == 0:
                                    logger.info(f"[click_dynamic_locator] Scroll {scroll_num + 1}: range {visible_values[0]}..{visible_values[-1]}")
                                # Overshot: all visible values > target
                                if all(v > value for v in visible_values):
                                    logger.info(f"[click_dynamic_locator] Overshot! Scrolling back up...")
                                    for up_i in range(MAX_SCROLLS):
                                        self.page.mouse.wheel(0, -400)
                                        self.page.wait_for_timeout(600)
                                        if _try_all():
                                            found = True
                                            logger.info(f"[click_dynamic_locator] ✓ Found '{value}' after {up_i + 1} wheel-ups")
                                            break
                                    break
                                # Bottom: require 3 consecutive same readings
                                if visible_values[-1] == last_bottom:
                                    same_bottom_count += 1
                                    if same_bottom_count >= 3:
                                        logger.info(f"[click_dynamic_locator] Grid bottom confirmed at {visible_values[-1]}")
                                        break
                                else:
                                    same_bottom_count = 0
                                last_bottom = visible_values[-1]
                        except Exception:
                            pass

                if not found:
                    return {"success": False, "message": f"click_dynamic_locator: no visible element with value '{value}'"}

                if step.wait_after > 0:
                    self.page.wait_for_timeout(step.wait_after)
                # ── PAGE AWARENESS: Post-click state ─────────
                if _page_reader:
                    try:
                        post_state = _page_reader.snapshot_short()
                        logger.info(f"[PageState] AFTER  '{step.name}': {post_state}")
                    except Exception:
                        pass
                return {"success": True, "message": f"Clicked element with value '{value}'"}
            except Exception as e:
                return {"success": False, "message": f"click_dynamic_locator failed: {e}"}

        if step.action_type == "screenshot":
            path = os.path.join(self.screenshots_dir, f"step_{step.order}.png")
            self.page.screenshot(path=path)
            return {"success": True, "message": f"Screenshot saved: {path}"}

        if step.action_type == "goto_url":
            url = value
            if url and not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            if not url:
                return {"success": False, "message": "No URL provided for goto_url"}
            try:
                self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                self.page.wait_for_timeout(step.wait_after if step.wait_after > 0 else 3000)
                # Apply keyboard zoom once after first real navigation
                self._apply_keyboard_zoom()
                return {"success": True, "message": f"Navigated to {url}"}
            except Exception as e:
                return {"success": False, "message": f"goto_url failed: {e}"}

        if step.action_type == "select_grid_row":
            # Search a D365 grid for a row where a column matches the value,
            # then click it using Playwright (NOT JS .click() which doesn't
            # trigger D365 custom event handlers on dyn-hyperlink elements).
            # Includes scroll support for D365 FixedDataTable virtualized grids.
            search_value = (value or "").strip()
            column_header = (step.value_field or "Name").strip()
            if not search_value:
                return {"success": False, "message": "No search value for select_grid_row"}

            logger.info(f"select_grid_row: searching '{column_header}' column for '{search_value}'")

            # JS function to search visible rows and return element info
            SEARCH_JS = """(args) => {
                const { searchValue, columnHeader } = args;

                function getCellText(cell) {
                    const input = cell.querySelector('input, textarea');
                    if (input && input.value) return input.value.trim();
                    if (cell.title) return cell.title.trim();
                    return (cell.textContent || '').trim();
                }

                function searchInDocument(doc) {
                    const headers = doc.querySelectorAll('th, [role="columnheader"]');
                    let colIdx = -1;
                    for (let i = 0; i < headers.length; i++) {
                        const txt = (headers[i].textContent || '').trim();
                        if (txt === columnHeader || txt.includes(columnHeader)) {
                            colIdx = i; break;
                        }
                    }
                    const rows = doc.querySelectorAll('tr[role="row"], [role="row"]');
                    for (const row of rows) {
                        const cells = row.querySelectorAll('td, [role="gridcell"]');
                        if (cells.length === 0) continue;
                        let matchedCell = null;
                        if (colIdx >= 0 && colIdx < cells.length) {
                            const t = getCellText(cells[colIdx]);
                            if (t === searchValue || t.startsWith(searchValue)) matchedCell = cells[colIdx];
                        }
                        if (!matchedCell) {
                            for (const cell of cells) {
                                if (getCellText(cell) === searchValue) { matchedCell = cell; break; }
                            }
                        }
                        if (matchedCell) {
                            let target = row.querySelector('input[type="radio"], [role="radio"]');
                            if (!target) target = matchedCell.querySelector('input') || matchedCell;
                            const rect = target.getBoundingClientRect();
                            const inputEl = matchedCell.querySelector('input');
                            return {
                                success: true,
                                x: Math.round(rect.x + rect.width / 2),
                                y: Math.round(rect.y + rect.height / 2),
                                inputId: inputEl ? inputEl.id : null,
                                inputValue: inputEl ? inputEl.value : null,
                                method: target.type === 'radio' ? 'radio' : 'cell'
                            };
                        }
                    }
                    return null;
                }
                let result = searchInDocument(document);
                if (result) return result;
                const frames = document.querySelectorAll('iframe');
                for (const frame of frames) {
                    try {
                        result = searchInDocument(frame.contentDocument || frame.contentWindow.document);
                        if (result) return result;
                    } catch (e) {}
                }
                return { success: false };
            }"""

            # Phase 1: Search currently visible rows
            js_result = self.page.evaluate(SEARCH_JS, {"searchValue": search_value, "columnHeader": column_header})

            # Phase 2: If not found, scroll the grid and search again (D365 virtualization)
            if not js_result or not js_result.get("success"):
                logger.info(f"select_grid_row: not in visible rows, scrolling grid...")
                MAX_SCROLL_ATTEMPTS = 30
                for scroll_attempt in range(MAX_SCROLL_ATTEMPTS):
                    # Try Ctrl+End first to jump to bottom, then scroll up
                    # But simpler: use Page Down on the grid
                    if scroll_attempt == 0:
                        # First click any grid cell to focus the grid
                        try:
                            grid_cell = self.page.locator(f"input[aria-label='{column_header}']").first
                            if grid_cell.is_visible(timeout=3000):
                                grid_cell.click()
                                self.page.wait_for_timeout(300)
                        except Exception:
                            pass
                    self.page.keyboard.press("PageDown")
                    self.page.wait_for_timeout(500)
                    js_result = self.page.evaluate(SEARCH_JS, {"searchValue": search_value, "columnHeader": column_header})
                    if js_result and js_result.get("success"):
                        logger.info(f"select_grid_row: found after {scroll_attempt + 1} PageDown scrolls")
                        break
                else:
                    logger.warning(f"select_grid_row: not found after {MAX_SCROLL_ATTEMPTS} scrolls")
                    return {"success": False, "message": f"Row not found for '{search_value}' after {MAX_SCROLL_ATTEMPTS} scrolls"}

            if js_result and js_result.get("success"):
                method = js_result.get("method", "unknown")
                x, y = js_result.get("x", 0), js_result.get("y", 0)
                input_id = js_result.get("inputId")
                logger.info(f"select_grid_row: found '{search_value}' via {method} at ({x},{y}) inputId={input_id}")

                # Phase 2: Use Playwright to perform the actual click
                # D365 dyn-hyperlink inputs need real mouse events, not JS .click()
                clicked = False

                # Try 1: Click by input ID if available (most precise)
                if input_id and not clicked:
                    try:
                        target = js_result.get("isIframe") and js_result.get("frameIdx", -1) >= 0
                        if target:
                            frame = self.page.frames[js_result["frameIdx"] + 1]  # +1 for main frame
                            locator = frame.locator(f"#{input_id}")
                        else:
                            locator = self.page.locator(f"#{input_id}")
                        locator.click(timeout=5000)
                        clicked = True
                        logger.info(f"select_grid_row: Playwright clicked #{input_id}")
                    except Exception as e:
                        logger.debug(f"select_grid_row: ID click failed: {e}")

                # Try 2: Click by input[value] selector
                if not clicked and js_result.get("inputValue"):
                    try:
                        sel = f"input[value='{search_value}']"
                        locator = self.page.locator(sel).first
                        locator.click(timeout=5000)
                        clicked = True
                        logger.info(f"select_grid_row: Playwright clicked input[value='{search_value}']")
                    except Exception as e:
                        logger.debug(f"select_grid_row: value selector click failed: {e}")

                # Try 3: Click by coordinates from JS bounding rect
                if not clicked and x > 0 and y > 0:
                    try:
                        self.page.mouse.click(x, y)
                        clicked = True
                        logger.info(f"select_grid_row: Playwright mouse.click({x},{y})")
                    except Exception as e:
                        logger.debug(f"select_grid_row: coordinate click failed: {e}")

                if clicked:
                    if step.wait_after > 0:
                        self.page.wait_for_timeout(step.wait_after)
                    # ── PAGE AWARENESS: Post-select_grid_row state ────
                    if _page_reader:
                        try:
                            post_state = _page_reader.snapshot_short()
                            logger.info(f"[PageState] AFTER  '{step.name}': {post_state}")
                        except Exception:
                            pass
                    return {"success": True, "message": f"Selected row '{search_value}' via Playwright {method}"}
                else:
                    return {"success": False, "message": f"Found '{search_value}' but Playwright click failed"}
            else:
                err = js_result.get("error", "Unknown") if js_result else "JS returned null"
                logger.warning(f"select_grid_row failed: {err}")

                # Fallback: try Playwright locator for input[value] directly
                try:
                    locator = self.page.locator(f"input[value='{search_value}']").first
                    if locator.is_visible(timeout=5000):
                        locator.click()
                        logger.info(f"select_grid_row: fallback clicked input[value='{search_value}']")
                        if step.wait_after > 0:
                            self.page.wait_for_timeout(step.wait_after)
                        return {"success": True, "message": f"Selected row via input[value] fallback for '{search_value}'"}
                except Exception:
                    pass

                # Fallback: try Playwright text locator
                try:
                    row_locator = self.page.locator(f"text='{search_value}'").first
                    if row_locator.is_visible(timeout=3000):
                        row_locator.click()
                        if step.wait_after > 0:
                            self.page.wait_for_timeout(step.wait_after)
                        return {"success": True, "message": f"Selected row via text locator for '{search_value}'"}
                except Exception:
                    pass

                return {"success": False, "message": f"Row not found for '{search_value}' in '{column_header}' column"}

        if step.action_type == "read_value":
            if not step.locator:
                return {"success": False, "message": "No locator defined for read_value step"}
            element = self.locator_engine.find_element(step.locator, timeout=step.timeout)
            if element:
                try:
                    val = element.input_value()
                except Exception:
                    try:
                        val = element.inner_text()
                    except Exception:
                        val = element.text_content() or ""
                val = val.strip() if val else ""
                if step.save_result_as and val:
                    self.context_vars[step.save_result_as] = val
                    logger.info(f"read_value: saved '{val}' as context var '{step.save_result_as}'")
                return {"success": True, "message": f"Read value: {val}", "value": val}
            return {"success": False, "message": "Element not found for read_value"}

        # Actions that need a locator
        if not step.locator:
            return {"success": False, "message": "No locator defined for step"}

        # Try to find element with retry
        for attempt in range(step.max_retries):
            try:
                element = self.locator_engine.find_element(
                    step.locator,
                    timeout=step.timeout
                )

                if not element:
                    if attempt < step.max_retries - 1:
                        logger.debug(f"Element not found, retry {attempt + 1}")
                        time.sleep(1)
                        continue
                    return {"success": False, "message": "Element not found"}

                # Execute the action
                result = self._perform_action(
                    step.action_type,
                    element,
                    value,
                    step
                )

                if result["success"]:
                    # Wait after action
                    if step.wait_after > 0:
                        self.page.wait_for_timeout(step.wait_after)

                    # Press key after action if specified
                    if step.press_key_after:
                        self.page.keyboard.press(step.press_key_after)
                        self.page.wait_for_timeout(200)

                    # Post-step D365 error check (opt-in per step)
                    # Skip for dialog_button steps — D365 always shows processing
                    # messages after OK clicks, which are NOT errors.
                    step_mode = getattr(step, 'interaction_mode', 'auto')
                    if getattr(step, 'check_for_errors', False) and step_mode != 'dialog_button':
                        # Wait for D365 to settle after the action
                        self.page.wait_for_timeout(1500)
                        error_text = self.detect_error_message()
                        if error_text:
                            logger.warning(
                                f"D365 error detected after step {step.order} "
                                f"({step.name}): {error_text}"
                            )
                            # Take screenshot of the error state (don't auto-dismiss)
                            try:
                                path = os.path.join(
                                    self.screenshots_dir,
                                    f"d365_error_step_{step.order}.png"
                                )
                                self.page.screenshot(path=path)
                            except Exception:
                                pass
                            return {
                                "success": False,
                                "message": f"D365 error: {error_text}",
                                "error_type": "d365_dialog",
                            }

                    # Save result to context if requested
                    if step.save_result_as:
                        self.context_vars[step.save_result_as] = value or result.get("value")

                    # ── PAGE AWARENESS: Post-step verification ───────
                    if _page_reader:
                        try:
                            post_state = _page_reader.snapshot_short()
                            logger.info(f"[PageState] AFTER  '{step.name}': {post_state}")

                            # Verify fill/type actions: read back the value
                            if step.action_type == 'fill' and value and element:
                                actual = _page_reader.get_field_value_by_element(element)
                                if actual is not None:
                                    if value.strip() in actual.strip() or actual.strip() in value.strip():
                                        logger.info(f"[PageState] ✓ Value verified: '{actual}'")
                                        result["value_verified"] = True
                                    else:
                                        logger.warning(f"[PageState] ✗ VALUE MISMATCH: set '{value}' but field has '{actual}'")
                                        result["value_verified"] = False
                                        result["actual_value"] = actual

                            # Verify grid "New" click: row count should increase
                            if _pre_grid_rows is not None:
                                post_rows = _page_reader.count_grid_rows()
                                delta = post_rows - _pre_grid_rows
                                if delta > 0:
                                    logger.info(f"[PageState] ✓ Grid rows: {_pre_grid_rows} → {post_rows} (+{delta})")
                                    result["grid_row_added"] = True
                                else:
                                    logger.warning(f"[PageState] ✗ Grid rows UNCHANGED: {_pre_grid_rows} → {post_rows}")
                                    result["grid_row_added"] = False

                            # ── SELECT-ALL VERIFY & RETRY ─────────────────
                            # Detect "select all" steps and verify that rows
                            # are actually selected.  D365 FixedDataTable has
                            # duplicate header elements — the click may land
                            # on a shadow copy that does nothing.
                            _is_select_all = (
                                step.action_type == 'click'
                                and step.name
                                and 'select all' in step.name.lower()
                            )
                            if _is_select_all:
                                grid_scope = ""
                                if step.locator and step.locator.page_context:
                                    grid_scope = step.locator.page_context  # e.g. "BOM Table" → "BOMTable"
                                    grid_scope = grid_scope.replace(" ", "")
                                sel_state = _page_reader.count_selected_grid_rows(grid_scope)
                                logger.info(
                                    f"[PageState] Select-all check: "
                                    f"{sel_state['selected']}/{sel_state['total']} rows, "
                                    f"checkbox={sel_state['checkboxState']}"
                                )
                                if sel_state['total'] > 0 and not sel_state['all_selected']:
                                    logger.warning("[PageState] ✗ Select-all did NOT select all rows — retrying")
                                    result["select_all_verified"] = False
                                    # Retry 1: click the same element again
                                    # (first click may have toggled off)
                                    for retry_i in range(2):
                                        try:
                                            element_retry = self.locator_engine.find_element(
                                                step.locator, timeout=step.timeout
                                            )
                                            if element_retry:
                                                element_retry.click(timeout=3000)
                                                self.page.wait_for_timeout(800)
                                                sel2 = _page_reader.count_selected_grid_rows(grid_scope)
                                                logger.info(
                                                    f"[PageState] Retry {retry_i+1}: "
                                                    f"{sel2['selected']}/{sel2['total']}, "
                                                    f"cb={sel2['checkboxState']}"
                                                )
                                                if sel2['all_selected']:
                                                    result["select_all_verified"] = True
                                                    logger.info("[PageState] ✓ Select-all verified after retry click")
                                                    break
                                        except Exception as re_err:
                                            logger.debug(f"[PageState] Retry click failed: {re_err}")

                                    # Retry 2: Ctrl+A as keyboard fallback
                                    if not result.get("select_all_verified"):
                                        try:
                                            # Click inside the grid body first
                                            grid_cell = self.page.locator(
                                                ".fixedDataTableLayout_body input, "
                                                ".fixedDataTableLayout_body [role='gridcell']"
                                            ).first
                                            if grid_cell.is_visible(timeout=2000):
                                                grid_cell.click(timeout=3000)
                                                self.page.wait_for_timeout(300)
                                            self.page.keyboard.press("Control+a")
                                            self.page.wait_for_timeout(800)
                                            sel3 = _page_reader.count_selected_grid_rows(grid_scope)
                                            logger.info(
                                                f"[PageState] After Ctrl+A: "
                                                f"{sel3['selected']}/{sel3['total']}, "
                                                f"cb={sel3['checkboxState']}"
                                            )
                                            if sel3['all_selected']:
                                                result["select_all_verified"] = True
                                                logger.info("[PageState] ✓ Select-all verified after Ctrl+A")
                                        except Exception as ka_err:
                                            logger.debug(f"[PageState] Ctrl+A fallback failed: {ka_err}")

                                    if not result.get("select_all_verified"):
                                        logger.warning(
                                            "[PageState] ✗ Select-all STILL failed after retries"
                                        )
                                else:
                                    result["select_all_verified"] = True
                                    if sel_state['total'] > 0:
                                        logger.info("[PageState] ✓ Select-all verified: all rows selected")

                        except Exception as pa_err:
                            logger.debug(f"[PageState] Post-step read failed: {pa_err}")

                    return result

            except PlaywrightTimeout:
                if attempt < step.max_retries - 1:
                    logger.debug(f"Timeout, retry {attempt + 1}")
                    time.sleep(1)
                    continue
                return {"success": False, "message": "Element interaction timed out"}

            except Exception as e:
                if attempt < step.max_retries - 1:
                    logger.debug(f"Error: {e}, retry {attempt + 1}")
                    time.sleep(1)
                    continue

                # Take screenshot on final failure
                try:
                    path = os.path.join(self.screenshots_dir, f"error_step_{step.order}.png")
                    self.page.screenshot(path=path)
                except:
                    pass

                return {"success": False, "message": str(e)}

        return {"success": False, "message": "Max retries exceeded"}

    def _read_grid_hyperlink_values(self) -> list:
        """Read visible hyperlink input values from D365 grid.

        Returns sorted list of values from visible dyn-hyperlink inputs.
        Used to detect overshoot during grid scrolling.
        """
        js = """
        (() => {
            const values = [];
            const inputs = document.querySelectorAll('input.dyn-hyperlink');
            inputs.forEach(inp => {
                if (inp.value && inp.offsetParent !== null) {
                    values.push(inp.value);
                }
            });
            return [...new Set(values)].sort();
        })()
        """
        for target in [self.page] + list(self.page.frames[1:]):
            try:
                result = target.evaluate(js)
                if result:
                    return result
            except Exception:
                continue
        return []

    def _click_grid_hyperlink(self, element, value: str):
        """Click a D365 grid hyperlink input with multiple fallback methods.

        Uses raw mouse.dblclick() at bounding box coordinates — D365
        hyperlinks respond to real mouse events, not Playwright element events.
        After each method, wait 2s for D365 to navigate, then check if element
        is gone. Only proceed to next method if element still present.
        """
        # Scroll element into viewport first — D365 pre-renders buffer rows
        # just outside the viewport; CSS selector finds them but they're off-screen
        try:
            element.scroll_into_view_if_needed(timeout=3000)
            self.page.wait_for_timeout(300)
        except Exception:
            pass

        # Get bounding box coordinates for raw mouse events
        try:
            box = element.bounding_box()
        except Exception:
            box = None
        if not box:
            logger.warning(f"[grid_hyperlink] Cannot get bounding box for '{value}', trying element.dblclick()")
            try:
                element.dblclick(timeout=5000)
                self.page.wait_for_timeout(2000)
            except Exception as e:
                logger.debug(f"[grid_hyperlink] element.dblclick failed: {e}")
            return

        cx = box['x'] + box['width'] / 2
        cy = box['y'] + box['height'] / 2
        logger.info(f"[grid_hyperlink] Coords for '{value}': ({cx:.0f}, {cy:.0f})")

        # Method A: raw mouse dblclick at coordinates
        try:
            self.page.mouse.dblclick(cx, cy)
            self.page.wait_for_timeout(2000)
            logger.info(f"[grid_hyperlink] A: mouse.dblclick({cx:.0f},{cy:.0f}) done")
        except Exception as e:
            logger.debug(f"[grid_hyperlink] A: mouse.dblclick failed: {e}")
        try:
            if not element.is_visible():
                logger.info(f"[grid_hyperlink] Navigation detected after A, stopping")
                return
        except:
            logger.info(f"[grid_hyperlink] Element detached after A, stopping")
            return

        # Method B: two separate mouse clicks at coordinates (rapid)
        logger.info(f"[grid_hyperlink] Element still visible after A, trying B...")
        try:
            self.page.mouse.click(cx, cy)
            self.page.wait_for_timeout(150)
            self.page.mouse.click(cx, cy)
            self.page.wait_for_timeout(2000)
            logger.info(f"[grid_hyperlink] B: click+click({cx:.0f},{cy:.0f}) done")
        except Exception as e:
            logger.debug(f"[grid_hyperlink] B: click+click failed: {e}")
        try:
            if not element.is_visible():
                logger.info(f"[grid_hyperlink] Navigation detected after B, stopping")
                return
        except:
            logger.info(f"[grid_hyperlink] Element detached after B, stopping")
            return

        # Method C: JS click on element
        logger.info(f"[grid_hyperlink] Element still visible after B, trying C...")
        try:
            element.evaluate("el => el.click()")
            self.page.wait_for_timeout(500)
            element.evaluate("el => el.click()")
            self.page.wait_for_timeout(2000)
            logger.info(f"[grid_hyperlink] C: JS click+click done for '{value}'")
        except Exception as e:
            logger.debug(f"[grid_hyperlink] C: JS click failed: {e}")

    def _scroll_grid_horizontal(self, direction: str = "left", grid_scope: str = "", distance_fraction: float = 1.0) -> Dict[str, Any]:
        """Scroll a D365 FixedDataTable grid horizontally by dragging the scrollbar face.

        Args:
            direction: "left" or "right"
            grid_scope: optional grid ID (unused currently)
            distance_fraction: 0.0-1.0, fraction of track width to scroll.
                1.0 = scroll to the edge (full). 0.3 = scroll 30% of track width.
        """
        face_selector = '.ScrollbarLayout_faceHorizontal'
        track_selector = '.ScrollbarLayout_main.ScrollbarLayout_mainHorizontal'

        face = self.page.locator(face_selector).first
        track = self.page.locator(track_selector).first

        try:
            face.wait_for(state="visible", timeout=5000)
        except Exception:
            logger.warning("[scroll_grid] Scrollbar face not visible within 5s")
            return {"success": False, "message": "Scrollbar face not visible"}

        track_box = track.bounding_box()
        face_box_current = face.bounding_box()
        if not track_box or not face_box_current:
            return {"success": False, "message": "Track or face bounding box is None"}

        if distance_fraction >= 1.0:
            # Full scroll: go to edge
            if direction == "left":
                target_x = 5
            else:
                target_x = int(track_box['width']) - 5
        else:
            # Fractional scroll: move face by fraction of track width
            face_center_relative = (face_box_current['x'] + face_box_current['width'] / 2) - track_box['x']
            delta = track_box['width'] * distance_fraction
            if direction == "left":
                target_x = max(5, int(face_center_relative - delta))
            else:
                target_x = min(int(track_box['width']) - 5, int(face_center_relative + delta))
            logger.info(f"[scroll_grid] fractional={distance_fraction}, face_rel={face_center_relative:.0f}, delta={delta:.0f}, target_x={target_x}")
        target_y = int(track_box['height']) // 2

        face_box_before = face.bounding_box()
        logger.info(
            f"[scroll_grid] face at x={face_box_before['x']:.0f}, "
            f"track x={track_box['x']:.0f} w={track_box['width']:.0f}, "
            f"target_position=({target_x}, {target_y})"
        )

        # APPROACH 1: drag_to()
        try:
            face.drag_to(track, target_position={"x": target_x, "y": target_y})
            self.page.wait_for_timeout(500)
            face_box_after = face.bounding_box()
            if face_box_after and face_box_before:
                moved = abs(face_box_after['x'] - face_box_before['x'])
                logger.info(f"[scroll_grid] drag_to: face moved {moved:.0f}px")
                if moved > 5:
                    return {"success": True, "message": f"Scrolled {direction} via drag_to ({moved:.0f}px)"}
            else:
                return {"success": True, "message": f"Scrolled {direction} via drag_to (unverified)"}
        except Exception as e:
            logger.warning(f"[scroll_grid] drag_to failed: {e}")

        # APPROACH 2: manual mouse drag
        logger.info("[scroll_grid] Trying approach 2: manual mouse drag")
        try:
            face.scroll_into_view_if_needed(timeout=3000)
            self.page.wait_for_timeout(200)
            face_box = face.bounding_box()
            track_box = track.bounding_box()
            if not face_box or not track_box:
                return {"success": False, "message": "bounding_box None"}
            start_x = face_box['x'] + face_box['width'] / 2
            start_y = face_box['y'] + face_box['height'] / 2
            end_x = (track_box['x'] + 5) if direction == "left" \
                else (track_box['x'] + track_box['width'] - 5)
            self.page.mouse.move(start_x, start_y)
            self.page.wait_for_timeout(200)
            self.page.mouse.down()
            self.page.wait_for_timeout(100)
            self.page.mouse.move(end_x, start_y, steps=30)
            self.page.wait_for_timeout(100)
            self.page.mouse.up()
            self.page.wait_for_timeout(500)
            face_box_after = face.bounding_box()
            if face_box_after:
                moved = abs(face_box_after['x'] - face_box['x'])
                logger.info(f"[scroll_grid] mouse drag: face moved {moved:.0f}px")
                if moved > 5:
                    return {"success": True, "message": f"Scrolled {direction} via mouse drag ({moved:.0f}px)"}
            else:
                return {"success": True, "message": f"Scrolled {direction} via mouse drag (unverified)"}
        except Exception as e:
            logger.warning(f"[scroll_grid] Approach 2 (mouse drag) failed: {e}")

        return {"success": False, "message": "All scroll approaches failed"}

    def _apply_keyboard_zoom(self):
        """Apply browser zoom via Ctrl+Minus keyboard shortcut after first navigation."""
        if getattr(self, '_zoom_applied', False):
            return
        zoom_steps = getattr(self, '_zoom_steps', 0)
        if zoom_steps <= 0:
            return
        try:
            for i in range(zoom_steps):
                self.page.keyboard.press("Control+Minus")
                self.page.wait_for_timeout(300)
            self._zoom_applied = True
            pct = round(100 * (0.8333 ** zoom_steps))
            logger.info(f"Browser zoom: {zoom_steps}x Ctrl+Minus applied (~{pct}%)")
        except Exception as e:
            logger.warning(f"Keyboard zoom failed: {e}")

    def _perform_action(
        self,
        action_type: str,
        element,
        value: str,
        step,
    ) -> Dict[str, Any]:
        """Perform the actual action on an element.

        Delegates to the D365InteractionEngine which uses mode-specific
        interaction chains with automatic fallbacks.
        """
        if self.interaction_engine:
            return self.interaction_engine.execute_interaction(
                action_type, element, value, step
            )

        # Fallback if interaction engine not initialized (shouldn't happen)
        logger.warning("InteractionEngine not initialized, using basic click/fill")
        if action_type == "click":
            element.click(timeout=step.timeout)
            return {"success": True, "message": "Clicked (basic)"}
        elif action_type == "fill":
            element.fill(value, timeout=step.timeout)
            return {"success": True, "message": f"Filled (basic): {value[:50]}"}
        else:
            return {"success": False, "message": f"No interaction engine for {action_type}"}

    def _normalize_condition(self, value: str) -> str:
        """Normalize condition value for matching."""
        if not value:
            return ""
        # Standardize formatting
        value = str(value).upper().strip()
        value = re.sub(r'[\s_.-]+', '-', value)
        return value

    def _handle_login(self, credentials: Dict[str, str]):
        """
        Handle ERP login (ADFS / D365).

        ADFS login page (newadfs.alrushaid.net) uses:
        - input#userNameInput (name="UserName") for username
        - input#passwordInput (name="Password") for password
        - span#submitButton or #submitButton for sign-in button
        """
        username = credentials.get("username", "")
        password = credentials.get("password", "")

        if not username or not password:
            logger.warning("No credentials provided for login")
            return

        # Wait for login form to appear
        self.page.wait_for_timeout(3000)

        try:
            # Check if we're on a login page
            url = self.page.url.lower()
            if 'adfs' not in url and 'login' not in url and 'auth' not in url:
                logger.info(f"Not on login page (url={url[:60]}), skipping login")
                return

            # Username field — ADFS uses #userNameInput, also try generic patterns
            username_field = self.page.locator(
                "input#userNameInput, input[name='UserName'], "
                "input[name*='user' i], input[name*='login' i], input[type='email'], input#username"
            ).first
            if username_field.is_visible(timeout=5000):
                username_field.fill(username)
                logger.info(f"Filled username: {username[:20]}...")
            else:
                logger.warning("Username field not visible")
                return

            # Password field
            password_field = self.page.locator(
                "input#passwordInput, input[name='Password'], input[type='password']"
            ).first
            if password_field.is_visible(timeout=3000):
                password_field.fill(password)
                logger.info("Filled password")
            else:
                logger.warning("Password field not visible")
                return

            # Submit button — ADFS uses #submitButton (can be span or input)
            submit_btn = self.page.locator(
                "#submitButton, "
                "button[type='submit'], input[type='submit'], "
                "span#submitButton, "
                "button:has-text('Sign in'), button:has-text('Login'), "
                "a:has-text('Sign in')"
            ).first
            if submit_btn.is_visible(timeout=3000):
                submit_btn.click()
                logger.info("Clicked submit/sign-in button")
            else:
                # Fallback: press Enter on the password field
                logger.info("Submit button not found, pressing Enter")
                self.page.keyboard.press("Enter")

            # Wait for navigation away from login page
            self.page.wait_for_load_state("domcontentloaded", timeout=60000)
            self.page.wait_for_timeout(3000)

            logger.info(f"Login completed, now at: {self.page.url[:60]}")

        except Exception as e:
            logger.error(f"Login failed: {e}")

    def stop(self):
        """Signal workflow to stop."""
        self.should_stop = True

    # ==========================================================================
    # BATCH EXECUTION
    # ==========================================================================

    def execute_batch(
        self,
        workflow,
        rows: List[Dict[str, Any]],
        on_row_complete: Callable = None,
    ) -> Dict[str, Any]:
        """
        Execute workflow for multiple rows.

        Args:
            workflow: Workflow model
            rows: List of row data dicts
            on_row_complete: Callback after each row

        Returns:
            Batch results summary
        """
        results = {
            "total": len(rows),
            "success": 0,
            "failed": 0,
            "details": []
        }

        for i, row in enumerate(rows):
            if self.should_stop:
                break

            logger.info(f"Processing row {i + 1}/{len(rows)}")

            result = self.execute_workflow(workflow, row)
            results["details"].append({
                "row_index": i,
                "row_data": row,
                "result": result
            })

            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1

            if on_row_complete:
                on_row_complete(i, row, result)

        return results

    # ==========================================================================
    # ERROR DETECTION
    # ==========================================================================

    # Non-error D365 messages that should be ignored by error detection.
    # These are informational/processing messages, not actual errors.
    _D365_IGNORE_PATTERNS = [
        "please wait",
        "processing your request",
        "we're processing",
        "we are processing",
        "saved successfully",
        "has been created",
        "has been saved",
        "operation completed",
        "record was created",
        "record has been",
        "loading",
        "validating",
        "submitting",
        "initializing",
        "refreshing",
        "updating",
    ]

    def detect_error_message(self, patterns: List[str] = None) -> Optional[str]:
        """
        Detect ACTUAL error messages on the page, ignoring informational/processing messages.

        Strategy (in order):
        1. Check D365-specific error selectors (error/critical message bars) — high confidence
        2. Check generic error selectors (.error-message, .alert-danger) — medium confidence
        3. Check broad message bars (span.messageBar-message) — filter out non-errors
        4. Check [role='alert'] — filter out non-errors

        Returns:
            Error message text if found, None otherwise
        """
        # Phase 1: D365-specific error message bars (high confidence)
        # D365 error bars have parent .messageBar with .messageBar-error or .messageBar-critical class
        # NOTE: Only exact D365 error bar classes — NOT broad [class*='error'] which catches too much
        d365_error_selectors = [
            ".messageBar-error span.messageBar-message",
            ".messageBar-critical span.messageBar-message",
            ".messageBar--error span.messageBar-message",
            ".messageBar--critical span.messageBar-message",
        ]
        for sel in d365_error_selectors:
            try:
                elements = self.page.locator(sel)
                count = elements.count()
                for i in range(count):
                    text = elements.nth(i).inner_text()
                    if text and len(text) > 5:
                        logger.info(f"D365 error bar found: {text[:100]}")
                        return text
            except:
                continue

        # Phase 2: Generic error selectors (medium confidence)
        generic_error_selectors = [
            ".error-message",
            ".alert-danger",
            ".notification-error",
        ]
        for sel in generic_error_selectors:
            try:
                elements = self.page.locator(sel)
                count = elements.count()
                for i in range(count):
                    text = elements.nth(i).inner_text()
                    if text and len(text) > 5:
                        text_lower = text.lower()
                        if any(ignore in text_lower for ignore in self._D365_IGNORE_PATTERNS):
                            logger.debug(f"Ignoring non-error message: {text[:80]}")
                            continue
                        return text
            except:
                continue

        # Phase 3: Broad message bars — only return if NOT a known non-error
        broad_selectors = [
            "span.messageBar-message",
            "[role='alert']",
        ]
        for sel in broad_selectors:
            try:
                elements = self.page.locator(sel)
                count = elements.count()
                for i in range(count):
                    el = elements.nth(i)
                    text = el.inner_text()
                    if text and len(text) > 5:
                        text_lower = text.lower()
                        # Skip known informational/processing messages
                        if any(ignore in text_lower for ignore in self._D365_IGNORE_PATTERNS):
                            logger.debug(f"Ignoring non-error D365 message: {text[:80]}")
                            continue
                        # Try to check parent for error class (D365 pattern)
                        try:
                            parent_class = el.evaluate(
                                "el => { "
                                "  let p = el.closest('.messageBar') || el.parentElement; "
                                "  return p ? p.className : ''; "
                                "}"
                            )
                            parent_lower = (parent_class or "").lower()
                            # If parent is explicitly info/warning, skip it
                            if "info" in parent_lower or "warning" in parent_lower or "success" in parent_lower:
                                logger.debug(f"Skipping info/warning message bar: {text[:80]}")
                                continue
                        except:
                            pass  # Can't check parent — proceed with text-based filtering
                        # If we got here, it's potentially an error
                        logger.info(f"Potential D365 error detected: {text[:100]}")
                        return text
            except:
                continue

        return None

    def detect_duplicate_item_error(self) -> bool:
        """
        Check if there's a duplicate item error (specific to Dynamics 365).
        """
        error_patterns = [
            "already been assigned",
            "already exists",
            "duplicate",
        ]

        error_text = self.detect_error_message()
        if error_text:
            for pattern in error_patterns:
                if pattern.lower() in error_text.lower():
                    return True

        return False

    def close_error_dialog(self):
        """Try to close any error dialogs on the page."""
        try:
            close_btn = self.page.locator(
                "button[aria-label='Close'], .messageBar-closeIcon, button:has-text('OK'), button:has-text('Close')"
            ).first
            if close_btn.is_visible():
                close_btn.click()
                self.page.wait_for_timeout(500)
                return True
        except:
            pass
        return False


# =============================================================================
# DEBUG EXECUTOR — Interactive debugging with pause-on-error + auto-heal
# =============================================================================

class DebugExecutor(WorkflowExecutor):
    """
    Debug version of WorkflowExecutor that runs in a background thread
    and pauses on locator failures, allowing the user to:
    1. See which step/locator is failing (with screenshot)
    2. Test new XPath expressions against the live page
    3. Save the working locator to DB and resume

    Before pausing for the user, it attempts auto-healing by generating
    alternative locator patterns from the recorded element info.

    Uses the same thread + queue architecture as RecorderService.
    """

    def __init__(self):
        super().__init__()
        # Thread communication
        self._cmd_queue = queue.Queue()
        self._result_queue = queue.Queue()
        self._lock = threading.Lock()
        self.ready_event = threading.Event()

        # Debug state — polled by frontend
        self._debug_state = {
            "status": "idle",
            "execution_id": None,
            "workflow_name": "",
            "total_steps": 0,
            "current_step_index": 0,
            "current_step": None,
            "completed_steps": [],
            "error": None,
            "screenshot_base64": None,
            "auto_heal_attempts": [],
            "row_data": {},
            # Chain-level state (only populated in chain debug mode)
            "chain_mode": False,
            "chain_name": "",
            "total_links": 0,
            "current_link_index": 0,
            "current_link": None,        # {order, name, workflow_name, workflow_id}
            "completed_links": [],        # [{order, name, workflow_name, workflow_id, status, steps_completed, steps_total}]
            "skipped_links": [],          # [{order, name, reason, workflow_id}]
            # Breakpoints — set of WorkflowStep PKs where execution should pause
            "breakpoint_step_ids": set(),
            # Step-by-step mode — pause after every successful step
            "step_by_step_mode": False,
            # Recording state (inline recording into debug browser)
            "recording_active": False,
            "recording_action_count": 0,
        }

        # Recording helpers (used by _inject_recorder / _collect_recording_actions)
        self._recorder_helper = None          # RecorderService instance for _store_action()
        self._recorder_js = None              # Cached JS script
        self._recording_nav_handler = None    # For cleanup on stop
        self._recording_attach_handler = None
        self._recording_result_queue = queue.Queue()  # Separate from debug results

    # ── Thread-safe state access ──────────────────────────────────────

    def get_debug_state(self) -> dict:
        """Get a snapshot of the current debug state (thread-safe, JSON-safe)."""
        with self._lock:
            state = dict(self._debug_state)
        # Convert set to list for JSON serialization
        if "breakpoint_step_ids" in state and isinstance(state["breakpoint_step_ids"], set):
            state["breakpoint_step_ids"] = list(state["breakpoint_step_ids"])
        return state

    def _update_state(self, **kwargs):
        """Update debug state fields (thread-safe)."""
        with self._lock:
            self._debug_state.update(kwargs)

    # ── Command interface (called from Django views) ──────────────────

    def send_command(self, cmd: str, data: dict = None):
        """Send a command to the debug thread."""
        self._cmd_queue.put((cmd, data or {}))

    def get_command_result(self, timeout: float = 10.0):
        """Wait for a result from the debug thread."""
        try:
            return self._result_queue.get(timeout=timeout)
        except queue.Empty:
            return {"error": "Timeout waiting for result"}

    def get_recording_result(self, timeout: float = 10.0):
        """Wait for a recording result from the debug thread (separate queue)."""
        try:
            return self._recording_result_queue.get(timeout=timeout)
        except queue.Empty:
            return {"error": "Timeout waiting for recording result"}

    def resume(self):
        self.send_command("resume")

    def skip(self):
        self.send_command("skip")

    def dismiss_and_continue(self):
        """Dismiss D365 dialog and continue (marks step as completed)."""
        self.send_command("dismiss_and_continue")

    def stop(self):
        self.should_stop = True
        self.send_command("stop")

    # ── Recording injection (all run in Playwright thread) ─────────────

    def _inject_recorder(self):
        """Inject recording JS into page and all frames. Runs in Playwright thread."""
        from .recorder import RecorderService
        self._recorder_js = RecorderService.get_recorder_js()

        # Inject into main page
        try:
            self.page.evaluate(self._recorder_js)
        except Exception as e:
            logger.warning(f"[DebugExec] Failed to inject recorder into main page: {e}")

        # Inject into all child frames
        for frame in self.page.frames:
            try:
                frame.evaluate(self._recorder_js)
            except Exception:
                pass

        # Set up re-injection handlers for SPA navigation
        def on_frame_navigated(frame):
            try:
                frame.evaluate(self._recorder_js)
            except Exception:
                pass

        def on_frame_attached(frame):
            try:
                frame.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass
            try:
                frame.evaluate(self._recorder_js)
            except Exception:
                pass

        self._recording_nav_handler = on_frame_navigated
        self._recording_attach_handler = on_frame_attached
        self.page.on("framenavigated", on_frame_navigated)
        self.page.on("frameattached", on_frame_attached)
        logger.info("[DebugExec] Recorder JS injected into page + %d frames", len(self.page.frames))

    def _collect_recording_actions(self) -> list:
        """Collect pending actions from all frames. Runs in Playwright thread."""
        all_actions = []
        try:
            actions = self.page.evaluate("window.__recorder?.getActions() || []")
            all_actions.extend(actions)
        except Exception:
            pass

        for frame in self.page.frames:
            if frame == self.page.main_frame:
                continue
            try:
                has_rec = frame.evaluate("!!window.__recorder")
                if has_rec:
                    actions = frame.evaluate("window.__recorder.getActions()")
                    all_actions.extend(actions)
                else:
                    # Re-inject into frames that lost the script
                    if self._recorder_js:
                        frame.evaluate(self._recorder_js)
            except Exception:
                pass

        all_actions.sort(key=lambda a: a.get("timestamp", 0))
        return all_actions

    def _remove_recorder(self):
        """Remove recorder from page. Runs in Playwright thread."""
        try:
            self.page.evaluate("if(window.__recorder) { window.__recorder.isRecording = false; }")
        except Exception:
            pass
        for frame in self.page.frames:
            try:
                frame.evaluate("if(window.__recorder) { window.__recorder.isRecording = false; }")
            except Exception:
                pass
        # Remove frame event handlers
        try:
            if self._recording_nav_handler:
                self.page.remove_listener("framenavigated", self._recording_nav_handler)
            if self._recording_attach_handler:
                self.page.remove_listener("frameattached", self._recording_attach_handler)
        except Exception:
            pass
        self._recording_nav_handler = None
        self._recording_attach_handler = None
        logger.info("[DebugExec] Recorder removed from page")

    def _handle_recording_command(self, cmd: str, data: dict):
        """Handle a recording command. Returns result dict. Runs in Playwright thread."""
        if cmd == "start_recording":
            try:
                self._inject_recorder()
                from .recorder import RecorderService
                self._recorder_helper = RecorderService()
                self._recorder_helper.recorded_actions = []
                self._recorder_helper.action_counter = 0
                self._update_state(recording_active=True, recording_action_count=0)
                return {"success": True, "message": "Recording started in debug browser"}
            except Exception as e:
                return {"success": False, "message": str(e)}

        elif cmd == "poll_recording":
            try:
                raw_actions = self._collect_recording_actions()
                processed = []
                if self._recorder_helper:
                    for raw in raw_actions:
                        p = self._recorder_helper._store_action(raw)
                        if p:
                            processed.append(p)
                with self._lock:
                    count = self._debug_state.get("recording_action_count", 0) + len(processed)
                    self._debug_state["recording_action_count"] = count
                return {"success": True, "actions": processed, "total": count}
            except Exception as e:
                return {"success": True, "actions": [], "error": str(e)}

        elif cmd == "stop_recording":
            try:
                raw_actions = self._collect_recording_actions()
                if self._recorder_helper:
                    for raw in raw_actions:
                        self._recorder_helper._store_action(raw)
                    all_actions = list(self._recorder_helper.recorded_actions)
                else:
                    all_actions = []
                self._remove_recorder()
                self._update_state(recording_active=False, recording_action_count=0)
                self._recorder_helper = None
                return {"success": True, "actions": all_actions, "total": len(all_actions)}
            except Exception as e:
                self._recorder_helper = None
                return {"success": False, "message": str(e), "actions": []}

        return {"success": False, "message": f"Unknown recording command: {cmd}"}

    # ── Main debug execution (runs in background thread) ──────────────

    def start_debug(self, workflow, row_data, execution_record, credentials, erp_url):
        """Entry point for the debug thread. Starts browser and runs workflow."""
        try:
            self._update_state(status="running", execution_id=execution_record.pk,
                               workflow_name=workflow.name, row_data=row_data or {})

            # Start browser
            logger.info("[DebugExec] Starting browser...")
            if not self.start_browser(url=erp_url, headless=False, credentials=credentials):
                self._update_state(status="failed", error={
                    "message": "Failed to start browser"
                })
                return

            self.ready_event.set()
            logger.info("[DebugExec] Browser ready, starting workflow")

            # Run the debug step loop
            self._debug_step_loop(workflow, row_data, execution_record)

        except Exception as e:
            logger.exception(f"[DebugExec] Fatal error: {e}")
            self._update_state(status="failed", error={"message": str(e)})
        finally:
            self.is_running = False

    # ── Chain Debug Mode ──────────────────────────────────────────────

    def start_debug_chain(self, chain, job_data, chain_execution, credentials, erp_url,
                          job_data_list=None):
        """Entry point for debug chain execution. Runs in background thread.

        Supports batch mode: when job_data_list is provided, executes the chain
        for each job sequentially, sharing one browser. WF-0 (login) runs only
        for the first job; subsequent jobs skip the first link.

        Iterates over chain links, handling conditions/preconditions/navigation,
        then delegates each workflow to _debug_step_loop() for step-by-step
        debugging with auto-heal and pause-on-error.
        """
        import re as regex
        from django.db import close_old_connections
        from ..models import WorkflowExecution, ChainExecution, ExecutionStatus, ERPJobData

        # Build the job list (single job or batch)
        if job_data_list and len(job_data_list) > 1:
            all_jobs = list(job_data_list)
            batch_mode = True
        else:
            all_jobs = [job_data]
            batch_mode = False

        batch_total = len(all_jobs)
        logger.info(f"[DebugChain] Batch mode={batch_mode}, {batch_total} job(s)")

        try:
            all_links = list(chain.get_active_links())
            total_links = len(all_links)

            if total_links == 0:
                self._update_state(status="failed", error={"message": "No active links in chain"})
                chain_execution.status = "failed"
                chain_execution.error_message = "No active links in chain"
                chain_execution.completed_at = timezone.now()
                chain_execution.save()
                return

            # Start browser — DON'T auto-login or auto-navigate.
            logger.info("[DebugChain] Starting browser (no auto-login, WF-0 handles it)...")
            if not self.start_browser(url=None, headless=False, credentials=None):
                self._update_state(status="failed", error={"message": "Failed to start browser"})
                chain_execution.status = "failed"
                chain_execution.error_message = "Failed to start browser"
                chain_execution.completed_at = timezone.now()
                chain_execution.save()
                return

            self.ready_event.set()
            logger.info(f"[DebugChain] Browser ready, {total_links} links, {batch_total} job(s)")

            # ── Outer job loop (batch mode) ──────────────────────────────
            batch_abort = False
            for job_idx, cur_job_stub in enumerate(all_jobs):
                if self.should_stop or batch_abort:
                    break

                is_first_job = (job_idx == 0)

                # Reload job from DB (fresh connection for long-running threads)
                close_old_connections()
                cur_job = ERPJobData.objects.select_related('route').get(pk=cur_job_stub.pk)

                # First job: ALL links. Subsequent: skip WF-0 (first link = login)
                links = all_links if is_first_job else all_links[1:]
                links_count = len(links)

                # Build row_data for this job
                row_data = cur_job.get_row_data() if cur_job else {}
                if credentials:
                    row_data['ERP_USERNAME'] = credentials.get('username', '')
                    row_data['ERP_PASSWORD'] = credentials.get('password', '')
                accumulated_context = {}
                if erp_url:
                    accumulated_context["ERP_URL"] = erp_url

                # For first job reuse provided chain_execution; for subsequent create new
                if is_first_job:
                    ce = chain_execution
                else:
                    close_old_connections()
                    ce = ChainExecution.objects.create(
                        chain=chain,
                        job_data=cur_job,
                        status=ExecutionStatus.RUNNING,
                        started_at=timezone.now(),
                        total_links=links_count,
                        row_data=row_data,
                    )

                # Initialize chain execution record
                ce.status = "running"
                ce.started_at = timezone.now()
                ce.total_links = links_count
                ce.row_data = row_data
                ce.save()

                # Mark job as SENT
                cur_job.status = 'SENT'
                cur_job.save(update_fields=['status', 'updated_at'])

                # Build batch state for debug polling
                batch_state = {}
                if batch_mode:
                    batch_state = dict(
                        batch_mode=True,
                        batch_total=batch_total,
                        batch_current=job_idx + 1,
                        batch_job_pk=cur_job.pk,
                        batch_job_name=cur_job.get_display_name(),
                        batch_jobs=[{
                            'pk': j.pk,
                            'name': j.get_display_name() if hasattr(j, 'get_display_name') else str(j.pk),
                            'status': 'pending',
                        } for j in all_jobs],
                    )
                    for bi in range(job_idx):
                        batch_state['batch_jobs'][bi]['status'] = 'completed'
                    batch_state['batch_jobs'][job_idx]['status'] = 'running'

                self._update_state(
                    status="running",
                    chain_mode=True,
                    chain_name=chain.name,
                    total_links=links_count,
                    current_link_index=0,
                    current_link=None,
                    completed_links=[],
                    skipped_links=[],
                    row_data=row_data,
                    execution_id=ce.pk,
                    **batch_state,
                )

                logger.info(
                    f"[DebugChain] ═══ Job {job_idx+1}/{batch_total}: "
                    f"{cur_job.get_display_name()} "
                    f"({'all links' if is_first_job else 'skip WF-0'}) ═══"
                )

                completed_link_count = 0
                job_failed = False

                # ── Inner link loop for this job ─────────────────────────
                link_idx = 0
                while link_idx < len(links):
                    link = links[link_idx]
                    if self.should_stop:
                        logger.info(f"[DebugChain] Stopped by user at link #{link.order}")
                        break

                    link_display = link.get_display_name()

                    # --- Check data condition ---
                    if link.condition_field and link.condition_value:
                        actual_value = row_data.get(link.condition_field, "")
                        actual_norm = regex.sub(r'[\s_.-]+', '-', str(actual_value).upper().strip())
                        expected_norm = regex.sub(r'[\s_.-]+', '-', str(link.condition_value).upper().strip())
                        if actual_norm != expected_norm:
                            reason = f"{link.condition_field}='{actual_value}' != '{link.condition_value}'"
                            logger.info(f"[DebugChain] Skipping link #{link.order} '{link_display}': {reason}")
                            with self._lock:
                                self._debug_state["skipped_links"].append({
                                    "order": link.order, "name": link_display, "reason": reason,
                                    "workflow_id": link.workflow_id,
                                })
                            link_idx += 1
                            continue

                    # --- Update chain progress ---
                    link_info = {
                        "order": link.order,
                        "name": link_display,
                        "workflow_name": link.workflow.name,
                        "workflow_id": link.workflow_id,
                    }
                    self._update_state(
                        current_link_index=link_idx,
                        current_link=link_info,
                        _running_link_order=link.order,
                    )
                    ce.current_link_order = link.order
                    ce.save(update_fields=["current_link_order"])

                    # --- Merge context into row_data ---
                    merged_row_data = dict(row_data)
                    if accumulated_context:
                        for ctx_key, ctx_val in accumulated_context.items():
                            if ctx_key not in merged_row_data:
                                merged_row_data[ctx_key] = ctx_val
                    if link.context_mapping and accumulated_context:
                        for target_key, source_key in link.context_mapping.items():
                            if source_key in accumulated_context:
                                merged_row_data[target_key] = accumulated_context[source_key]
                                logger.info(f"[DebugChain] Context mapped: {source_key} → {target_key}")

                    # --- Skip link if required template variables are empty ---
                    skip_link = False
                    for step in link.workflow.steps.filter(is_active=True):
                        templates = [step.value_template or '', step.value_static or '']
                        for tmpl in templates:
                            if '{{ROUTE}}' in tmpl and not merged_row_data.get('ROUTE', ''):
                                reason = "step requires ROUTE but it is empty (scrap job)"
                                logger.info(f"[DebugChain] Skipping link #{link.order} '{link_display}': {reason}")
                                with self._lock:
                                    self._debug_state["skipped_links"].append({
                                        "order": link.order, "name": link_display,
                                        "reason": reason, "workflow_id": link.workflow_id,
                                    })
                                skip_link = True
                                break
                        if skip_link:
                            break
                    if skip_link:
                        link_idx += 1
                        continue

                    # --- Navigate if link has a specific URL ---
                    if link.navigate_url and self.page:
                        try:
                            url = link.navigate_url.strip()
                            if url and not url.startswith(('http://', 'https://')):
                                url = 'https://' + url
                            self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                            self.page.wait_for_timeout(link.wait_before_ms)
                        except Exception as e:
                            logger.warning(f"[DebugChain] Navigation to {link.navigate_url} failed: {e}")
                    elif link.wait_before_ms > 0 and self.page:
                        self.page.wait_for_timeout(link.wait_before_ms)

                    # --- Browser health check ---
                    if not self.is_browser_alive():
                        error_msg = f"Browser closed unexpectedly before link #{link.order} '{link_display}'"
                        logger.error(f"[DebugChain] {error_msg}")
                        self._update_state(status="failed", error={"message": error_msg})
                        ce.status = "failed"
                        ce.error_message = error_msg
                        ce.completed_at = timezone.now()
                        ce.save()
                        batch_abort = True
                        break

                    # --- Page precondition check ---
                    if link.precondition_type and link.precondition_selector:
                        precondition_met = self._check_chain_precondition(link)
                        should_skip = (
                            (precondition_met and link.skip_if_found) or
                            (not precondition_met and not link.skip_if_found)
                        )
                        if should_skip:
                            reason_word = "found" if precondition_met else "not found"
                            reason = (
                                f"Precondition: '{link.precondition_selector[:60]}' {reason_word} → "
                                f"{'skip_if_found' if link.skip_if_found else 'skip_if_not_found'}"
                            )
                            logger.info(f"[DebugChain] Skipping link #{link.order} '{link_display}': {reason}")
                            accumulated_context[f"_precondition_{link.order}"] = "skipped"
                            accumulated_context[f"_precondition_{link.order}_found"] = precondition_met
                            ce.context = accumulated_context
                            ce.save(update_fields=["context"])
                            with self._lock:
                                self._debug_state["skipped_links"].append({
                                    "order": link.order, "name": link_display, "reason": reason,
                                    "workflow_id": link.workflow_id,
                                })
                            link_idx += 1
                            continue

                    # --- Create WorkflowExecution record for this link ---
                    wf_execution = WorkflowExecution.objects.create(
                        workflow=link.workflow,
                        job_data=cur_job,
                        chain_execution=ce,
                        status=ExecutionStatus.PENDING,
                        row_data=merged_row_data,
                    )

                    # --- Reset step-level state for this link's workflow ---
                    self._update_state(
                        status="running",
                        workflow_name=link.workflow.name,
                        total_steps=0,
                        current_step_index=0,
                        current_step=None,
                        completed_steps=[],
                        error=None,
                        screenshot_base64=None,
                        auto_heal_attempts=[],
                        row_data=merged_row_data,
                        execution_id=wf_execution.pk,
                    )

                    logger.info(f"[DebugChain] Running link #{link.order}: '{link_display}' ({link.workflow.name})")

                    # --- Execute the workflow's steps via debug loop ---
                    loop_result = self._debug_step_loop(link.workflow, merged_row_data, wf_execution)

                    # Handle jump-to-link command
                    if loop_result == "JUMP_LINK":
                        target_link_order = self._debug_state.get("_rerun_from_link_order")
                        if target_link_order is not None:
                            target_idx = next((i for i, l in enumerate(links) if l.order == target_link_order), link_idx)
                            logger.info(f"[DebugChain] Jumping to link index {target_idx} (order {target_link_order})")
                            link_idx = target_idx
                            self._update_state(status="running", error=None, screenshot_base64=None)
                            continue

                    # Check result
                    wf_execution.refresh_from_db()
                    if wf_execution.status == "success":
                        completed_link_count += 1
                        ce.completed_links = completed_link_count
                        ce.save(update_fields=["completed_links"])

                        wf_context = wf_execution.context or {}
                        if wf_context:
                            accumulated_context.update(wf_context)
                            ce.context = accumulated_context
                            ce.save(update_fields=["context"])

                        with self._lock:
                            step_info = {
                                "total": self._debug_state.get("total_steps", 0),
                                "completed": len(self._debug_state.get("completed_steps", [])),
                            }

                        with self._lock:
                            self._debug_state["completed_links"].append({
                                "order": link.order,
                                "name": link_display,
                                "workflow_name": link.workflow.name,
                                "workflow_id": link.workflow_id,
                                "status": "success",
                                "steps_completed": step_info["completed"],
                                "steps_total": step_info["total"],
                            })

                        logger.info(f"[DebugChain] Link #{link.order} completed ({completed_link_count}/{links_count})")

                    elif wf_execution.status == "cancelled":
                        logger.info(f"[DebugChain] Link #{link.order} stopped by user")
                        break

                    else:
                        # Failed
                        error_msg = (
                            f"Link #{link.order} '{link_display}' failed: "
                            f"{wf_execution.error_message or 'Unknown error'}"
                        )
                        logger.error(f"[DebugChain] {error_msg}")

                        with self._lock:
                            self._debug_state["completed_links"].append({
                                "order": link.order,
                                "name": link_display,
                                "workflow_name": link.workflow.name,
                                "workflow_id": link.workflow_id,
                                "status": "failed",
                                "steps_completed": 0,
                                "steps_total": 0,
                            })

                        if chain.stop_on_failure:
                            ce.status = "failed"
                            ce.error_message = error_msg
                            ce.completed_at = timezone.now()
                            ce.save()
                            job_failed = True
                            batch_abort = True
                            self._update_state(status="failed", error={"message": error_msg})
                            break
                        else:
                            logger.warning("[DebugChain] Continuing after failure (stop_on_failure=False)")

                    link_idx += 1
                # ── End inner link loop ──────────────────────────────────

                # ── Per-job finalization ──────────────────────────────────
                if not job_failed and not self.should_stop:
                    ce.status = "success"
                    ce.completed_at = timezone.now()
                    ce.context = accumulated_context
                    ce.save()

                    # Save captured values to job_data immediately
                    close_old_connections()
                    cur_job.refresh_from_db()
                    update_fields = ['status', 'updated_at']
                    cur_job.status = 'COMPLETED'
                    if accumulated_context.get("ITEM_NO"):
                        cur_job.item_number = accumulated_context["ITEM_NO"]
                        update_fields.append('item_number')
                    if accumulated_context.get("JOURNAL_NUMBER"):
                        cur_job.movement_journal_number = accumulated_context["JOURNAL_NUMBER"]
                        update_fields.append('movement_journal_number')
                    cur_job.save(update_fields=update_fields)
                    logger.info(f"[DebugChain] Job {job_idx+1}/{batch_total} COMPLETED: {cur_job.get_display_name()} saved={update_fields}")

                elif self.should_stop:
                    ce.status = "cancelled"
                    ce.completed_at = timezone.now()
                    ce.save()
                    cur_job.status = 'ERROR'
                    cur_job.save(update_fields=['status', 'updated_at'])
                    logger.info(f"[DebugChain] Job {job_idx+1}/{batch_total} CANCELLED by user")

                elif job_failed:
                    cur_job.status = 'ERROR'
                    cur_job.save(update_fields=['status', 'updated_at'])
                    logger.info(f"[DebugChain] Job {job_idx+1}/{batch_total} FAILED")

                # Update batch_jobs status in debug state
                if batch_mode:
                    with self._lock:
                        bj = self._debug_state.get("batch_jobs", [])
                        if job_idx < len(bj):
                            bj[job_idx]['status'] = 'completed' if not job_failed else 'failed'

            # ── All jobs done ────────────────────────────────────────────
            if self.should_stop:
                self._update_state(status="stopped")
            elif batch_abort:
                self._update_state(status="failed")
            else:
                self._update_state(status="completed")
                logger.info(f"[DebugChain] Batch complete: {batch_total} job(s) processed")

        except Exception as e:
            logger.exception(f"[DebugChain] Fatal error: {e}")
            self._update_state(status="failed", error={"message": str(e)})
            try:
                chain_execution.status = "failed"
                chain_execution.error_message = str(e)[:500]
                chain_execution.completed_at = timezone.now()
                chain_execution.save()
            except Exception:
                pass
        finally:
            self.is_running = False

    def _check_chain_precondition(self, link) -> bool:
        """Check page precondition for a chain link during debug mode.

        Same logic as ChainExecutor._check_precondition() but uses self.page directly.
        """
        if not self.page:
            return False

        page = self.page
        selector = link.precondition_selector.strip()
        timeout = link.precondition_timeout_ms
        check_type = link.precondition_type

        try:
            if check_type == "element_exists":
                try:
                    locator = page.locator(selector)
                    if locator.count() > 0:
                        return True
                    try:
                        locator.first.wait_for(state="visible", timeout=timeout)
                        return True
                    except Exception:
                        pass
                    for frame in page.frames:
                        if frame == page.main_frame:
                            continue
                        try:
                            if frame.locator(selector).count() > 0:
                                return True
                        except Exception:
                            continue
                except Exception:
                    pass
                return False

            elif check_type == "text_contains":
                search_text = link.precondition_value or selector
                try:
                    body_text = page.inner_text("body", timeout=timeout)
                    if search_text.lower() in body_text.lower():
                        return True
                    for frame in page.frames:
                        if frame == page.main_frame:
                            continue
                        try:
                            frame_text = frame.inner_text("body", timeout=2000)
                            if search_text.lower() in frame_text.lower():
                                return True
                        except Exception:
                            continue
                except Exception:
                    pass
                return False

            elif check_type == "element_count_gt":
                threshold = int(link.precondition_value or "0")
                try:
                    locator = page.locator(selector)
                    page.wait_for_timeout(min(timeout, 3000))
                    count = locator.count()
                    for frame in page.frames:
                        if frame == page.main_frame:
                            continue
                        try:
                            count += frame.locator(selector).count()
                        except Exception:
                            continue
                    return count > threshold
                except Exception:
                    return False

            return False
        except Exception:
            return False

    def _debug_step_loop(self, workflow, row_data, execution_record):
        """Main step loop with auto-heal and pause-on-error.

        When called from chain debug mode, is_running and should_stop are
        already set by start_debug_chain(), so we only reset them in
        single-workflow mode.
        """
        in_chain_mode = self._debug_state.get("chain_mode", False)
        if not in_chain_mode:
            self.is_running = True
            self.should_stop = False
        self.context_vars = {}
        steps_completed = 0

        if execution_record:
            execution_record.status = "running"
            execution_record.started_at = timezone.now()
            execution_record.save()

        # Get condition value for branching
        condition_value = None
        if workflow.condition_field and row_data:
            condition_value = self._normalize_condition(
                row_data.get(workflow.condition_field, "")
            )

        raw_steps = list(workflow.get_steps_for_condition(condition_value))

        # ── Expand repeat groups ──────────────────────────────────
        # Steps with the same repeat_group are executed once per item
        # in the data source array. We expand them into (step, loop_ctx)
        # tuples where loop_ctx is None for normal steps or a dict with
        # LOOP_ITEM, LOOP_QTY, LOOP_INDEX for repeat iterations.
        steps = []  # list of (WorkflowStep, loop_context_dict_or_None)
        i = 0
        while i < len(raw_steps):
            s = raw_steps[i]
            if s.repeat_group:
                # Collect all consecutive steps with same repeat_group
                group_name = s.repeat_group
                group_steps = []
                data_source_key = None
                while i < len(raw_steps) and raw_steps[i].repeat_group == group_name:
                    if raw_steps[i].repeat_data_source:
                        data_source_key = raw_steps[i].repeat_data_source
                    group_steps.append(raw_steps[i])
                    i += 1
                # Get the data array from row_data
                data_source_key = data_source_key or group_name.upper()
                loop_data = row_data.get(data_source_key, []) if row_data else []
                if not isinstance(loop_data, list):
                    loop_data = []
                if not loop_data:
                    logger.warning(f"[DebugExec] Repeat group '{group_name}': no data in '{data_source_key}', skipping {len(group_steps)} steps")
                else:
                    logger.info(f"[DebugExec] Repeat group '{group_name}': {len(loop_data)} iterations × {len(group_steps)} steps")
                    for loop_idx, loop_item in enumerate(loop_data):
                        loop_ctx = {
                            'LOOP_INDEX': str(loop_idx),
                            'LOOP_ITERATION': str(loop_idx + 1),
                        }
                        # Merge all keys from the loop item dict
                        if isinstance(loop_item, dict):
                            for k, v in loop_item.items():
                                loop_ctx[f'LOOP_{k}'] = str(v) if v else ''
                        else:
                            loop_ctx['LOOP_VALUE'] = str(loop_item)
                        for gs in group_steps:
                            steps.append((gs, loop_ctx))
            else:
                steps.append((s, None))
                i += 1

        total_steps = len(steps)
        self._update_state(total_steps=total_steps)

        idx = 0
        while idx < len(steps):
            step, loop_ctx = steps[idx]

            # Merge loop context into row_data for template resolution
            if loop_ctx:
                step_row_data = dict(row_data) if row_data else {}
                step_row_data.update(loop_ctx)
            else:
                step_row_data = row_data

            if self.should_stop:
                logger.info("[DebugExec] Stopped by user")
                break

            # Check if browser is still alive
            if not self.is_browser_alive():
                error_msg = "Browser closed unexpectedly. Aborting debug execution."
                logger.error(f"[DebugExec] {error_msg}")
                if not in_chain_mode:
                    self._update_state(status="failed", error={"message": error_msg})
                if execution_record:
                    execution_record.status = "failed"
                    execution_record.error_message = error_msg
                    execution_record.completed_at = timezone.now()
                    execution_record.save()
                return

            # Drain any pending commands (also processes set_breakpoints)
            self._drain_commands()

            # ── Check breakpoints ────────────────────────────────
            with self._lock:
                bp_ids = self._debug_state.get("breakpoint_step_ids", set())
            if step.pk in bp_ids:
                logger.info(f"[DebugExec] Breakpoint hit at step {step.order}: {step.name}")
                screenshot_b64 = self._take_screenshot_base64()
                self._update_state(
                    status="paused",
                    current_step_index=idx,
                    current_step={
                        "id": step.pk, "order": step.order, "name": step.name,
                        "action_type": step.action_type,
                        "locator_name": step.locator.name if step.locator else None,
                        "locator_id": step.locator.pk if step.locator else None,
                        "value": step.get_value(step_row_data, self.context_vars) if step.action_type in ("fill", "select") else "",
                    },
                    error={"message": f"Breakpoint hit at step {step.order}: {step.name}", "is_breakpoint": True},
                    screenshot_base64=screenshot_b64,
                )
                bp_action = self._pause_and_process_commands()
                if bp_action == "stop":
                    break
                elif bp_action == "rerun_from_step":
                    target_step_id = self._debug_state.get("_rerun_from_step_id")
                    idx = next((i for i, s in enumerate(steps) if s[0].pk == target_step_id), idx)
                    logger.info(f"[DebugExec] Rerunning from step index {idx}")
                    self._update_state(status="running", error=None, screenshot_base64=None)
                    continue
                elif bp_action == "rerun_from_link":
                    return "JUMP_LINK"
                elif bp_action == "skip":
                    self._create_step_record(execution_record, step, "skipped", {"success": False, "message": "Skipped at breakpoint"}, timezone.now())
                    with self._lock:
                        self._debug_state["completed_steps"].append({
                            "id": step.pk, "order": step.order, "name": step.name, "status": "skipped",
                            "duration_ms": 0,
                        })
                    idx += 1
                    continue
                # "resume" — continue to execute the step normally
                self._update_state(status="running", error=None, screenshot_base64=None)

            step_started = timezone.now()
            step_info = {
                "id": step.pk,
                "order": step.order,
                "name": step.name,
                "action_type": step.action_type,
                "locator_name": step.locator.name if step.locator else None,
                "locator_id": step.locator.pk if step.locator else None,
                "value": step.get_value(step_row_data, self.context_vars) if step.action_type in ("fill", "select") else "",
                "loop_ctx": loop_ctx,
            }
            self._update_state(
                status="running",
                current_step_index=idx,
                current_step=step_info,
                error=None,
                screenshot_base64=None,
                auto_heal_attempts=[],
            )

            loop_info = f" [Loop {loop_ctx.get('LOOP_ITERATION','?')}: {loop_ctx.get('LOOP_ITEM','')}]" if loop_ctx else ""
            logger.info(f"[DebugExec] [{idx+1}/{total_steps}] Step {step.order}: {step.name}{loop_info}")
            result = self._execute_step(step, step_row_data)

            # ── PAGE AWARENESS: Capture page state for debug UI ──────
            if self.page:
                try:
                    from .page_awareness import D365PageReader
                    _reader = D365PageReader(self.page)
                    page_state = _reader.snapshot()
                    page_state["step_result"] = {
                        "value_verified": result.get("value_verified"),
                        "actual_value": result.get("actual_value"),
                        "value_after": result.get("value_after"),
                        "grid_row_added": result.get("grid_row_added"),
                    }
                    self._update_state(page_state=page_state)
                except Exception as pa_err:
                    logger.debug(f"[PageState] Debug state capture failed: {pa_err}")

            if result["success"]:
                steps_completed += 1
                self._create_step_record(execution_record, step, "success", result, step_started)
                completed_entry = {
                    "id": step.pk, "order": step.order, "name": step.name,
                    "status": "success",
                    "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                }
                with self._lock:
                    self._debug_state["completed_steps"].append(completed_entry)

                # ── Step-by-step mode: pause after every successful step ──
                with self._lock:
                    sbs_mode = self._debug_state.get("step_by_step_mode", False)
                if sbs_mode:
                    screenshot_b64 = self._take_screenshot_base64()
                    next_step = steps[idx + 1] if idx + 1 < len(steps) else None
                    next_info = f"Next: #{next_step.order} {next_step.name}" if next_step else "Last step in segment"
                    self._update_state(
                        status="paused",
                        current_step_index=idx,
                        current_step={
                            "id": step.pk, "order": step.order, "name": step.name,
                            "action_type": step.action_type,
                            "locator_name": step.locator.name if step.locator else None,
                            "locator_id": step.locator.pk if step.locator else None,
                        },
                        error={
                            "message": f"Step {step.order} ({step.name}) completed. {next_info}",
                            "step_name": step.name,
                            "is_step_pause": True,
                        },
                        screenshot_base64=screenshot_b64,
                    )
                    sbs_action = self._pause_and_process_commands()
                    if sbs_action == "stop":
                        self.should_stop = True
                        break
                    elif sbs_action == "rerun_from_step":
                        target_step_id = self._debug_state.get("_rerun_from_step_id")
                        idx = next((i for i, s in enumerate(steps) if s[0].pk == target_step_id), idx)
                        self._update_state(status="running", error=None, screenshot_base64=None)
                        continue
                    elif sbs_action == "rerun_from_link":
                        return "JUMP_LINK"
                    elif sbs_action == "skip":
                        pass  # Skip just advances to next — same as resume
                    # "resume" — continue normally
                    self._update_state(status="running", error=None, screenshot_base64=None)

                idx += 1
                continue

            # ── STEP FAILED ──────────────────────────────────────
            logger.warning(f"[DebugExec] Step {step.order} failed: {result['message']}")

            # Collect strategies that were tried
            strategies_tried = []
            if step.locator:
                for strat in step.locator.strategies.filter(is_active=True).order_by('priority'):
                    strategies_tried.append({
                        "type": strat.strategy_type,
                        "value": strat.value,
                        "result": "not found",
                    })

            error_info = {
                "step_order": step.order,
                "step_name": step.name,
                "message": result.get("message", "Unknown error"),
                "error_type": result.get("error_type", ""),
                "locator_id": step.locator.pk if step.locator else None,
                "locator_name": step.locator.name if step.locator else None,
                "strategies_tried": strategies_tried,
                "failing_strategy_type": strategies_tried[0]["type"] if strategies_tried else "xpath",
                "failing_value": strategies_tried[0]["value"] if strategies_tried else "",
            }

            # ── D365 dialog errors: skip auto-heal since the step action itself succeeded ──
            is_d365_dialog = result.get("error_type") == "d365_dialog"

            # ── PHASE 1: Auto-heal (only for locator/interaction failures, NOT d365 dialogs) ──
            if step.locator and not is_d365_dialog:
                self._update_state(status="auto_healing", error=error_info)
                healed_result = self._try_auto_heal(step, step_row_data)
                if healed_result and healed_result.get("success"):
                    logger.info(f"[DebugExec] Auto-healed step {step.order}!")
                    steps_completed += 1
                    self._create_step_record(execution_record, step, "success", healed_result, step_started)
                    completed_entry = {
                        "id": step.pk, "order": step.order, "name": step.name,
                        "status": "auto_healed",
                        "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                    }
                    with self._lock:
                        self._debug_state["completed_steps"].append(completed_entry)
                    idx += 1
                    continue

            # ── PHASE 2: Pause for user ──────────────────────────
            screenshot_b64 = self._take_screenshot_base64()
            self._update_state(status="paused", error=error_info,
                               screenshot_base64=screenshot_b64)

            # Block and process commands until resume/skip/stop/rerun_from_step
            action = self._pause_and_process_commands()

            if action == "stop":
                break
            elif action == "rerun_from_step":
                target_step_id = self._debug_state.get("_rerun_from_step_id")
                idx = next((i for i, s in enumerate(steps) if s[0].pk == target_step_id), idx)
                logger.info(f"[DebugExec] Rerunning from step index {idx}")
                self._update_state(status="running", error=None, screenshot_base64=None)
                continue
            elif action == "rerun_from_link":
                return "JUMP_LINK"
            elif action == "skip":
                self._create_step_record(execution_record, step, "skipped", result, step_started)
                with self._lock:
                    self._debug_state["completed_steps"].append({
                        "id": step.pk, "order": step.order, "name": step.name, "status": "skipped",
                        "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                    })
                idx += 1
                continue
            elif action == "dismiss_continue":
                # D365 dialog dismissed — mark step as completed (action itself succeeded)
                steps_completed += 1
                self._create_step_record(execution_record, step, "success", result, step_started)
                with self._lock:
                    self._debug_state["completed_steps"].append({
                        "id": step.pk, "order": step.order, "name": step.name, "status": "success",
                        "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                    })
                self._update_state(status="running", error=None, screenshot_base64=None)
                idx += 1
                continue
            elif action == "resume":
                # Re-fetch locator strategies from DB (user may have updated them)
                if step.locator:
                    step.locator.refresh_from_db()
                self._update_state(status="running", error=None, screenshot_base64=None)
                retry_result = self._execute_step(step, step_row_data)
                if retry_result["success"]:
                    steps_completed += 1
                    self._create_step_record(execution_record, step, "success", retry_result, step_started)
                    with self._lock:
                        self._debug_state["completed_steps"].append({
                            "id": step.pk, "order": step.order, "name": step.name, "status": "success",
                            "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                        })
                else:
                    # Still failing after resume — pause again
                    screenshot_b64 = self._take_screenshot_base64()
                    error_info["message"] = retry_result.get("message", "Still failing after locator update")
                    self._update_state(status="paused", error=error_info,
                                       screenshot_base64=screenshot_b64)
                    action2 = self._pause_and_process_commands()
                    if action2 == "stop":
                        break
                    elif action2 == "rerun_from_step":
                        target_step_id = self._debug_state.get("_rerun_from_step_id")
                        idx = next((i for i, s in enumerate(steps) if s[0].pk == target_step_id), idx)
                        logger.info(f"[DebugExec] Rerunning from step index {idx}")
                        self._update_state(status="running", error=None, screenshot_base64=None)
                        continue
                    elif action2 == "rerun_from_link":
                        return "JUMP_LINK"
                    elif action2 == "skip":
                        with self._lock:
                            self._debug_state["completed_steps"].append({
                                "id": step.pk, "order": step.order, "name": step.name, "status": "skipped",
                                "duration_ms": 0,
                            })
                        idx += 1
                        continue
                    elif action2 == "resume":
                        if step.locator:
                            step.locator.refresh_from_db()
                        self._update_state(status="running")
                        result3 = self._execute_step(step, step_row_data)
                        if result3["success"]:
                            steps_completed += 1
                            self._create_step_record(execution_record, step, "success", result3, step_started)
                            with self._lock:
                                self._debug_state["completed_steps"].append({
                                    "id": step.pk, "order": step.order, "name": step.name, "status": "success",
                                    "duration_ms": 0,
                                })
                        else:
                            # Third failure — record and move on
                            self._create_step_record(execution_record, step, "failed", result3, step_started, retries=3)
                            if not step.continue_on_error:
                                if not in_chain_mode:
                                    self._update_state(status="failed", error={
                                        "message": f"Step {step.order} failed after multiple retries"
                                    })
                                if execution_record:
                                    execution_record.status = "failed"
                                    execution_record.error_message = result3.get("message", "")[:500]
                                    execution_record.completed_at = timezone.now()
                                    execution_record.save()
                                return

            # Advance to next step (normal flow-through after resume success / failure handling)
            idx += 1

        # ── Workflow complete ─────────────────────────────────────
        if self.should_stop:
            # In chain mode, don't set top-level status — chain loop handles it
            if not in_chain_mode:
                self._update_state(status="stopped")
            if execution_record:
                execution_record.status = "cancelled"
                execution_record.completed_at = timezone.now()
                execution_record.save()
        else:
            # In chain mode, don't set top-level status — chain loop handles it
            if not in_chain_mode:
                self._update_state(status="completed")
            if execution_record:
                execution_record.status = "success"
                execution_record.completed_at = timezone.now()
                execution_record.context = self.context_vars
                execution_record.save()

    # ── Pause command loop ────────────────────────────────────────────

    def _pause_and_process_commands(self) -> str:
        """Block the thread and process commands until resume/skip/stop.

        While paused, the thread stays responsive to test_locator and
        screenshot commands from the frontend.
        Returns the action that unblocked: 'resume', 'skip', or 'stop'.
        """
        while True:
            try:
                cmd, data = self._cmd_queue.get(timeout=0.5)
            except queue.Empty:
                if self.should_stop:
                    return "stop"
                continue

            if cmd == "resume":
                return "resume"
            elif cmd == "skip":
                return "skip"
            elif cmd == "dismiss_and_continue":
                # D365 dialog dismissal: close any dialog then mark step as completed
                try:
                    self.close_error_dialog()
                    self.page.wait_for_timeout(500)
                except Exception:
                    pass
                return "dismiss_continue"
            elif cmd == "stop":
                self.should_stop = True
                return "stop"
            elif cmd == "test_locator":
                result = self._test_locator_on_page(
                    data.get("strategy_type", "xpath"),
                    data.get("value", ""),
                )
                self._result_queue.put(result)
            elif cmd == "screenshot":
                b64 = self._take_screenshot_base64()
                self._result_queue.put({"screenshot_base64": b64})
            elif cmd == "set_breakpoints":
                with self._lock:
                    self._debug_state["breakpoint_step_ids"] = set(data.get("step_ids", []))
            elif cmd == "rerun_from_step":
                # Store the rerun target so the main loop knows to jump
                with self._lock:
                    self._debug_state["_rerun_from_step_id"] = data.get("step_id")
                return "rerun_from_step"
            elif cmd == "rerun_from_link":
                # Store the target link order so the chain loop knows to jump
                with self._lock:
                    self._debug_state["_rerun_from_link_order"] = data.get("link_order")
                return "rerun_from_link"
            elif cmd == "run_single_step":
                # Run a single step in isolation, then re-pause
                step_id = data.get("step_id")
                self._run_single_step_inline(step_id)
                # Don't return — stay paused
            elif cmd == "set_step_by_step":
                with self._lock:
                    self._debug_state["step_by_step_mode"] = data.get("enabled", False)
                # Don't return — stay paused (or continue running)
            elif cmd in ("start_recording", "poll_recording", "stop_recording"):
                result = self._handle_recording_command(cmd, data)
                self._recording_result_queue.put(result)
                # Don't return — stay paused

    def _drain_commands(self):
        """Process any pending commands from the queue (non-blocking)."""
        while not self._cmd_queue.empty():
            try:
                cmd, data = self._cmd_queue.get_nowait()
                # Handle set_breakpoints while running (non-blocking)
                if cmd == "set_breakpoints":
                    with self._lock:
                        self._debug_state["breakpoint_step_ids"] = set(data.get("step_ids", []))
                elif cmd == "set_step_by_step":
                    with self._lock:
                        self._debug_state["step_by_step_mode"] = data.get("enabled", False)
                elif cmd == "stop":
                    self.should_stop = True
                elif cmd in ("start_recording", "poll_recording", "stop_recording"):
                    result = self._handle_recording_command(cmd, data)
                    self._recording_result_queue.put(result)
            except queue.Empty:
                break

    def _run_single_step_inline(self, step_id):
        """Execute a single step against the live browser page (inline, stays paused).

        Runs the step and reports back via state update (success/failure info),
        then returns without unpausing the main loop.
        """
        from ..models import WorkflowStep

        try:
            step = WorkflowStep.objects.select_related("locator").get(pk=step_id)
            row_data = self._debug_state.get("row_data", {})

            # Refresh locator strategies from DB
            if step.locator:
                step.locator.refresh_from_db()

            self._update_state(
                status="running",
                error=None,
                screenshot_base64=None,
            )

            result = self._execute_step(step, row_data)
            screenshot_b64 = self._take_screenshot_base64()

            if result["success"]:
                self._update_state(
                    status="paused",
                    error={
                        "message": f"Step {step.order} ({step.name}) executed successfully!",
                        "step_name": step.name,
                        "is_test_result": True,
                        "test_success": True,
                    },
                    screenshot_base64=screenshot_b64,
                )
                logger.info(f"[DebugExec] Single-step run: step {step.order} succeeded")
            else:
                self._update_state(
                    status="paused",
                    error={
                        "message": f"Step {step.order} failed: {result.get('message', 'unknown error')}",
                        "step_name": step.name,
                        "is_test_result": True,
                        "test_success": False,
                        "locator_name": step.locator.name if step.locator else None,
                        "locator_id": step.locator.pk if step.locator else None,
                    },
                    screenshot_base64=screenshot_b64,
                )
                logger.warning(f"[DebugExec] Single-step run: step {step.order} failed: {result.get('message')}")

        except Exception as e:
            logger.exception(f"[DebugExec] Error running single step {step_id}: {e}")
            self._update_state(
                status="paused",
                error={"message": f"Error running step: {e}", "is_test_result": True, "test_success": False},
            )

    # ── Auto-heal ─────────────────────────────────────────────────────

    def _try_auto_heal(self, step, row_data) -> Optional[dict]:
        """Try alternative locator patterns before asking the user.

        Generates XPath candidates from the step's locator strategies
        and from the recorded action element info, tests each against
        the live page, and saves the first working one.
        """
        from ..models import LocatorStrategy, RecordedAction

        candidates = []
        locator = step.locator
        heal_attempts = []

        # Source 1: Find the recorded action that created this locator
        # Look for RecordedAction whose element_id/element_name matches
        recorded_actions = RecordedAction.objects.filter(
            session__status="completed"
        ).order_by("-session__id")

        # Try to find matching recorded action by locator name
        matched_action = None
        for ra in recorded_actions[:200]:
            strats_json = ra.locator_strategies or []
            for s in strats_json:
                val = s.get("value", "")
                # Check if any existing strategy value appears in recorded strategies
                for existing_s in locator.strategies.filter(is_active=True):
                    if existing_s.value and existing_s.value in val:
                        matched_action = ra
                        break
                if matched_action:
                    break
            if matched_action:
                break

        if matched_action:
            el_id = matched_action.element_id or ""
            el_name = matched_action.element_name or ""
            el_aria = matched_action.element_aria_label or ""
            el_tag = matched_action.element_tag or ""

            # Generate candidates from element info
            if el_aria and el_aria not in ("Name", "ea", "Back", "Close"):
                candidates.append(f'//*[@aria-label="{el_aria}"]')
            if el_name:
                candidates.append(f'//*[@name="{el_name}"]')
                candidates.append(f'//input[@name="{el_name}"]')
            if el_id:
                # Try exact ID
                candidates.append(f'//*[@id="{el_id}"]')
                # Try various contains combinations
                parts = el_id.split("_")
                for i in range(1, len(parts)):
                    suffix = "_".join(parts[i:])
                    if len(suffix) > 5 and suffix not in ("input", "header", "label"):
                        candidates.append(f'//*[contains(@id, "{suffix}")]')

        # Source 2: Generate from existing strategy values (variations)
        for strat in locator.strategies.filter(is_active=True):
            if "contains(@id" in strat.value:
                # Try with broader/narrower contains
                import re as regex
                ids = regex.findall(r'contains\(@id,\s*"([^"]+)"\)', strat.value)
                for id_part in ids:
                    if len(id_part) > 3:
                        candidates.append(f'//*[contains(@id, "{id_part}")]')

        # Deduplicate and exclude already-tried strategies
        existing_values = set(s.value for s in locator.strategies.filter(is_active=True))
        seen = set()
        unique_candidates = []
        for c in candidates:
            if c not in seen and c not in existing_values:
                seen.add(c)
                unique_candidates.append(c)

        # Test each candidate
        for xpath in unique_candidates:
            test_result = self._test_locator_on_page("xpath", xpath)
            attempt = {"xpath": xpath, "result": "not found"}

            if test_result.get("found"):
                count = test_result.get("count", 0)
                visible = test_result.get("visible", False)
                attempt["result"] = f"found ({count}, {'visible' if visible else 'hidden'})"
                heal_attempts.append(attempt)

                # Only accept if exactly 1 visible element found
                if count == 1 and visible:
                    # Save as new priority-0 strategy (highest)
                    LocatorStrategy.objects.create(
                        locator=locator,
                        strategy_type="xpath",
                        value=xpath,
                        priority=0,
                        is_active=True,
                    )
                    logger.info(f"[DebugExec] Auto-healed: {xpath}")

                    # Update state with heal attempts
                    self._update_state(auto_heal_attempts=heal_attempts)

                    # Retry the step with the new strategy
                    locator.refresh_from_db()
                    retry_result = self._execute_step(step, row_data)
                    if retry_result.get("success"):
                        return retry_result
            else:
                heal_attempts.append(attempt)

            self._update_state(auto_heal_attempts=heal_attempts)

        return None

    # ── Test locator on live page ─────────────────────────────────────

    def _test_locator_on_page(self, strategy_type: str, value: str) -> dict:
        """Test a locator expression against the current browser page.

        Checks main page and all iframes. Returns match info.
        """
        if not self.page:
            return {"found": False, "error": "No browser page"}

        try:
            # Build the Playwright locator from strategy type + value
            targets_to_try = [self.page] + [
                f for f in self.page.frames if f != self.page.main_frame
            ]

            for target in targets_to_try:
                try:
                    if strategy_type == "xpath":
                        element = target.locator(f"xpath={value}")
                    elif strategy_type == "css":
                        element = target.locator(value)
                    elif strategy_type == "text":
                        element = target.locator(f"text={value}")
                    elif strategy_type == "id":
                        element = target.locator(f"#{value}")
                    elif strategy_type == "aria-label":
                        element = target.locator(f'[aria-label="{value}"]')
                    elif strategy_type == "name":
                        element = target.locator(f'[name="{value}"]')
                    else:
                        element = target.locator(f"xpath={value}")

                    count = element.count()
                    if count > 0:
                        is_visible = False
                        tag_name = ""
                        text_content = ""
                        try:
                            is_visible = element.first.is_visible()
                            tag_name = element.first.evaluate("el => el.tagName")
                            text_content = element.first.evaluate(
                                "el => (el.innerText || el.value || '').substring(0, 100)"
                            )
                        except Exception:
                            pass

                        in_iframe = target != self.page
                        return {
                            "found": True,
                            "count": count,
                            "visible": is_visible,
                            "tag": tag_name,
                            "text": text_content,
                            "in_iframe": in_iframe,
                        }
                except Exception:
                    continue

            return {"found": False, "count": 0}

        except Exception as e:
            return {"found": False, "error": str(e)}

    # ── Screenshot ────────────────────────────────────────────────────

    def _take_screenshot_base64(self) -> Optional[str]:
        """Capture the current page as a base64-encoded PNG."""
        if not self.page:
            return None
        try:
            screenshot_bytes = self.page.screenshot()
            return base64.b64encode(screenshot_bytes).decode("ascii")
        except Exception:
            return None
