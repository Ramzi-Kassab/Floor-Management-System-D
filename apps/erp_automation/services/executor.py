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
            steps = workflow.get_steps_for_condition(condition_value)

            total_steps = steps.count()
            logger.info(f"Executing workflow '{workflow.name}' with {total_steps} steps")

            for step in steps:
                if self.should_stop:
                    logger.info("Workflow stopped by user")
                    break

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
                logger.info(f"[{steps_completed+1}/{total_steps}] Step {step.order}: {step.name} ({step.action_type})")
                result = self._execute_step(step, row_data)

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
            return {"success": True, "message": f"Navigation wait {wait_ms}ms"}

        if step.action_type == "press_key":
            key = value or step.press_key_after
            self.page.keyboard.press(key)
            return {"success": True, "message": f"Pressed {key}"}

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
                return {"success": True, "message": f"Navigated to {url}"}
            except Exception as e:
                return {"success": False, "message": f"goto_url failed: {e}"}

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
                    if getattr(step, 'check_for_errors', False):
                        error_text = self.detect_error_message()
                        if error_text:
                            logger.warning(
                                f"D365 error detected after step {step.order} "
                                f"({step.name}): {error_text}"
                            )
                            self.close_error_dialog()
                            # Take screenshot of the error state
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

    def detect_error_message(self, patterns: List[str] = None) -> Optional[str]:
        """
        Detect error messages on the page.

        Args:
            patterns: List of CSS selectors or text patterns to check

        Returns:
            Error message text if found, None otherwise
        """
        default_patterns = [
            "span.messageBar-message",
            ".error-message",
            ".alert-danger",
            "[role='alert']",
            ".notification-error",
        ]

        patterns = patterns or default_patterns

        for pattern in patterns:
            try:
                elements = self.page.locator(pattern)
                count = elements.count()

                for i in range(count):
                    text = elements.nth(i).inner_text()
                    if text and len(text) > 5:
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
        }

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

    def resume(self):
        self.send_command("resume")

    def skip(self):
        self.send_command("skip")

    def stop(self):
        self.should_stop = True
        self.send_command("stop")

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

    def start_debug_chain(self, chain, job_data, chain_execution, credentials, erp_url):
        """Entry point for debug chain execution. Runs in background thread.

        Iterates over chain links, handling conditions/preconditions/navigation,
        then delegates each workflow to _debug_step_loop() for step-by-step
        debugging with auto-heal and pause-on-error.
        """
        import re as regex
        from ..models import WorkflowExecution, ExecutionStatus

        try:
            links = list(chain.get_active_links())
            total_links = len(links)

            if total_links == 0:
                self._update_state(status="failed", error={"message": "No active links in chain"})
                chain_execution.status = "failed"
                chain_execution.error_message = "No active links in chain"
                chain_execution.completed_at = timezone.now()
                chain_execution.save()
                return

            # Build row_data
            row_data = job_data.get_row_data() if job_data else {}
            # Inject ERP credentials into row_data so WF-0 login steps can
            # use {{ERP_USERNAME}} and {{ERP_PASSWORD}} templates
            if credentials:
                row_data['ERP_USERNAME'] = credentials.get('username', '')
                row_data['ERP_PASSWORD'] = credentials.get('password', '')
            accumulated_context = {}
            # Inject ERP URL into context so goto_url steps can use {{ERP_URL}} template
            if erp_url:
                accumulated_context["ERP_URL"] = erp_url

            # Initialize chain execution record
            chain_execution.status = "running"
            chain_execution.started_at = timezone.now()
            chain_execution.total_links = total_links
            chain_execution.row_data = row_data
            chain_execution.save()

            # Initialize chain-level debug state
            self._update_state(
                status="running",
                chain_mode=True,
                chain_name=chain.name,
                total_links=total_links,
                current_link_index=0,
                current_link=None,
                completed_links=[],
                skipped_links=[],
                row_data=row_data,
                execution_id=chain_execution.pk,
            )

            # Start browser — DON'T auto-login or auto-navigate.
            # The chain's first link (WF-0) handles login explicitly via its
            # own steps. This matches ChainExecutor.execute_chain() behaviour
            # which skips auto-login for the first link (completed_links == 0).
            # Passing url=None and credentials=None means we just open a blank
            # browser; WF-0's goto_url step navigates to ERP and its fill steps
            # handle the login form using {{ERP_USERNAME}} / {{ERP_PASSWORD}}.
            logger.info("[DebugChain] Starting browser (no auto-login, WF-0 handles it)...")
            if not self.start_browser(url=None, headless=False, credentials=None):
                self._update_state(status="failed", error={"message": "Failed to start browser"})
                chain_execution.status = "failed"
                chain_execution.error_message = "Failed to start browser"
                chain_execution.completed_at = timezone.now()
                chain_execution.save()
                return

            self.ready_event.set()
            logger.info(f"[DebugChain] Browser ready, executing {total_links} links")

            completed_link_count = 0

            for link_idx, link in enumerate(links):
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
                )
                chain_execution.current_link_order = link.order
                chain_execution.save(update_fields=["current_link_order"])

                # --- Merge context into row_data ---
                merged_row_data = dict(row_data)
                # Always merge accumulated_context (e.g. ERP_URL, item_number)
                # so template vars like {{ERP_URL}} resolve in all links
                if accumulated_context:
                    for ctx_key, ctx_val in accumulated_context.items():
                        if ctx_key not in merged_row_data:
                            merged_row_data[ctx_key] = ctx_val
                # Apply explicit context_mapping (can override/rename keys)
                if link.context_mapping and accumulated_context:
                    for target_key, source_key in link.context_mapping.items():
                        if source_key in accumulated_context:
                            merged_row_data[target_key] = accumulated_context[source_key]
                            logger.info(f"[DebugChain] Context mapped: {source_key} → {target_key}")

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
                    chain_execution.status = "failed"
                    chain_execution.error_message = error_msg
                    chain_execution.completed_at = timezone.now()
                    chain_execution.save()
                    return

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
                        # Store in context
                        accumulated_context[f"_precondition_{link.order}"] = "skipped"
                        accumulated_context[f"_precondition_{link.order}_found"] = precondition_met
                        chain_execution.context = accumulated_context
                        chain_execution.save(update_fields=["context"])
                        with self._lock:
                            self._debug_state["skipped_links"].append({
                                "order": link.order, "name": link_display, "reason": reason,
                                "workflow_id": link.workflow_id,
                            })
                        continue

                # --- Create WorkflowExecution record for this link ---
                wf_execution = WorkflowExecution.objects.create(
                    workflow=link.workflow,
                    job_data=job_data,
                    chain_execution=chain_execution,
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
                self._debug_step_loop(link.workflow, merged_row_data, wf_execution)

                # Check result
                wf_execution.refresh_from_db()
                if wf_execution.status == "success":
                    completed_link_count += 1
                    chain_execution.completed_links = completed_link_count
                    chain_execution.save(update_fields=["completed_links"])

                    # Get workflow context from execution
                    wf_context = wf_execution.context or {}
                    if wf_context:
                        accumulated_context.update(wf_context)
                        chain_execution.context = accumulated_context
                        chain_execution.save(update_fields=["context"])

                    # Get step counts from debug state
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

                    logger.info(f"[DebugChain] Link #{link.order} completed ({completed_link_count}/{total_links})")

                elif wf_execution.status == "cancelled":
                    # User stopped during this link
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
                        chain_execution.status = "failed"
                        chain_execution.error_message = error_msg
                        chain_execution.completed_at = timezone.now()
                        chain_execution.save()
                        self._update_state(status="failed", error={"message": error_msg})
                        return
                    else:
                        logger.warning("[DebugChain] Continuing after failure (stop_on_failure=False)")

            # --- Chain complete ---
            if self.should_stop:
                chain_execution.status = "cancelled"
                chain_execution.completed_at = timezone.now()
                chain_execution.save()
                self._update_state(status="stopped")
            else:
                chain_execution.status = "success"
                chain_execution.completed_at = timezone.now()
                chain_execution.context = accumulated_context
                chain_execution.save()
                self._update_state(status="completed")
                logger.info(f"[DebugChain] Chain completed: {completed_link_count}/{total_links} links")

        except Exception as e:
            logger.exception(f"[DebugChain] Fatal error: {e}")
            self._update_state(status="failed", error={"message": str(e)})
            chain_execution.status = "failed"
            chain_execution.error_message = str(e)[:500]
            chain_execution.completed_at = timezone.now()
            chain_execution.save()
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

        steps = list(workflow.get_steps_for_condition(condition_value))
        total_steps = len(steps)
        self._update_state(total_steps=total_steps)

        idx = 0
        while idx < len(steps):
            step = steps[idx]

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
                        "order": step.order, "name": step.name,
                        "action_type": step.action_type,
                        "locator_name": step.locator.name if step.locator else None,
                        "locator_id": step.locator.pk if step.locator else None,
                        "value": step.get_value(row_data, self.context_vars) if step.action_type in ("fill", "select") else "",
                    },
                    error={"message": f"Breakpoint hit at step {step.order}: {step.name}", "is_breakpoint": True},
                    screenshot_base64=screenshot_b64,
                )
                bp_action = self._pause_and_process_commands()
                if bp_action == "stop":
                    break
                elif bp_action == "rerun_from_step":
                    target_step_id = self._debug_state.get("_rerun_from_step_id")
                    idx = next((i for i, s in enumerate(steps) if s.pk == target_step_id), idx)
                    logger.info(f"[DebugExec] Rerunning from step index {idx}")
                    self._update_state(status="running", error=None, screenshot_base64=None)
                    continue
                elif bp_action == "skip":
                    self._create_step_record(execution_record, step, "skipped", {"success": False, "message": "Skipped at breakpoint"}, timezone.now())
                    with self._lock:
                        self._debug_state["completed_steps"].append({
                            "order": step.order, "name": step.name, "status": "skipped",
                            "duration_ms": 0,
                        })
                    idx += 1
                    continue
                # "resume" — continue to execute the step normally
                self._update_state(status="running", error=None, screenshot_base64=None)

            step_started = timezone.now()
            step_info = {
                "order": step.order,
                "name": step.name,
                "action_type": step.action_type,
                "locator_name": step.locator.name if step.locator else None,
                "locator_id": step.locator.pk if step.locator else None,
                "value": step.get_value(row_data, self.context_vars) if step.action_type in ("fill", "select") else "",
            }
            self._update_state(
                status="running",
                current_step_index=idx,
                current_step=step_info,
                error=None,
                screenshot_base64=None,
                auto_heal_attempts=[],
            )

            logger.info(f"[DebugExec] [{idx+1}/{total_steps}] Step {step.order}: {step.name}")
            result = self._execute_step(step, row_data)

            if result["success"]:
                steps_completed += 1
                self._create_step_record(execution_record, step, "success", result, step_started)
                completed_entry = {
                    "order": step.order, "name": step.name,
                    "status": "success",
                    "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                }
                with self._lock:
                    self._debug_state["completed_steps"].append(completed_entry)
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
                "locator_id": step.locator.pk if step.locator else None,
                "locator_name": step.locator.name if step.locator else None,
                "strategies_tried": strategies_tried,
                "failing_strategy_type": strategies_tried[0]["type"] if strategies_tried else "xpath",
                "failing_value": strategies_tried[0]["value"] if strategies_tried else "",
            }

            # ── PHASE 1: Auto-heal ───────────────────────────────
            if step.locator:
                self._update_state(status="auto_healing", error=error_info)
                healed_result = self._try_auto_heal(step, row_data)
                if healed_result and healed_result.get("success"):
                    logger.info(f"[DebugExec] Auto-healed step {step.order}!")
                    steps_completed += 1
                    self._create_step_record(execution_record, step, "success", healed_result, step_started)
                    completed_entry = {
                        "order": step.order, "name": step.name,
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
                idx = next((i for i, s in enumerate(steps) if s.pk == target_step_id), idx)
                logger.info(f"[DebugExec] Rerunning from step index {idx}")
                self._update_state(status="running", error=None, screenshot_base64=None)
                continue
            elif action == "skip":
                self._create_step_record(execution_record, step, "skipped", result, step_started)
                with self._lock:
                    self._debug_state["completed_steps"].append({
                        "order": step.order, "name": step.name, "status": "skipped",
                        "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                    })
                idx += 1
                continue
            elif action == "resume":
                # Re-fetch locator strategies from DB (user may have updated them)
                if step.locator:
                    step.locator.refresh_from_db()
                self._update_state(status="running", error=None, screenshot_base64=None)
                retry_result = self._execute_step(step, row_data)
                if retry_result["success"]:
                    steps_completed += 1
                    self._create_step_record(execution_record, step, "success", retry_result, step_started)
                    with self._lock:
                        self._debug_state["completed_steps"].append({
                            "order": step.order, "name": step.name, "status": "success",
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
                        idx = next((i for i, s in enumerate(steps) if s.pk == target_step_id), idx)
                        logger.info(f"[DebugExec] Rerunning from step index {idx}")
                        self._update_state(status="running", error=None, screenshot_base64=None)
                        continue
                    elif action2 == "skip":
                        with self._lock:
                            self._debug_state["completed_steps"].append({
                                "order": step.order, "name": step.name, "status": "skipped",
                                "duration_ms": 0,
                            })
                        idx += 1
                        continue
                    elif action2 == "resume":
                        if step.locator:
                            step.locator.refresh_from_db()
                        self._update_state(status="running")
                        result3 = self._execute_step(step, row_data)
                        if result3["success"]:
                            steps_completed += 1
                            self._create_step_record(execution_record, step, "success", result3, step_started)
                            with self._lock:
                                self._debug_state["completed_steps"].append({
                                    "order": step.order, "name": step.name, "status": "success",
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
            elif cmd == "run_single_step":
                # Run a single step in isolation, then re-pause
                step_id = data.get("step_id")
                self._run_single_step_inline(step_id)
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
                elif cmd == "stop":
                    self.should_stop = True
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
