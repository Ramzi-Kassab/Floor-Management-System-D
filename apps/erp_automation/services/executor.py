"""
Workflow Execution Engine

Executes workflows against the ERP system.
Handles data binding, conditional logic, and error recovery.
"""
import os
import re
import time
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from django.utils import timezone

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from .locator_engine import LocatorEngine

logger = logging.getLogger(__name__)


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
            self.context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            self.page = self.context.new_page()
            self.locator_engine = LocatorEngine(self.page)

            if url:
                self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)

            # Handle login if credentials provided
            if credentials:
                self._handle_login(credentials)

            self.screenshots_dir = "/tmp/erp_automation/screenshots"
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

        logger.info("Browser stopped")

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

            logger.info(f"Executing workflow '{workflow.name}' with {steps.count()} steps")

            for step in steps:
                if self.should_stop:
                    logger.info("Workflow stopped by user")
                    break

                # Callback: step starting
                if self.on_step_start:
                    self.on_step_start(step, steps_completed, steps.count())

                # Execute step
                result = self._execute_step(step, row_data)

                if result["success"]:
                    steps_completed += 1
                    if self.on_step_complete:
                        self.on_step_complete(step, result)
                else:
                    logger.error(f"Step {step.order} failed: {result['message']}")

                    if self.on_step_error:
                        self.on_step_error(step, result)

                    if not step.continue_on_error:
                        # Try error handler if defined
                        if step.error_handler_step:
                            self._execute_step(step.error_handler_step, row_data)

                        if execution_record:
                            execution_record.status = "failed"
                            execution_record.error_message = result["message"]
                            execution_record.completed_at = timezone.now()
                            execution_record.save()

                        return {
                            "success": False,
                            "message": f"Step {step.order} failed: {result['message']}",
                            "steps_completed": steps_completed
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

        if step.action_type == "press_key":
            key = value or step.press_key_after
            self.page.keyboard.press(key)
            return {"success": True, "message": f"Pressed {key}"}

        if step.action_type == "screenshot":
            path = os.path.join(self.screenshots_dir, f"step_{step.order}.png")
            self.page.screenshot(path=path)
            return {"success": True, "message": f"Screenshot saved: {path}"}

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
        """Perform the actual action on an element."""

        if action_type == "click":
            element.click(timeout=step.timeout)
            return {"success": True, "message": "Clicked"}

        elif action_type == "fill":
            if step.clear_before_fill:
                element.clear()
            element.fill(value, timeout=step.timeout)
            return {"success": True, "message": f"Filled: {value[:50]}...", "value": value}

        elif action_type == "select":
            element.select_option(value=value)
            return {"success": True, "message": f"Selected: {value}"}

        elif action_type == "check":
            if value.lower() in ["true", "1", "yes", "checked"]:
                element.check()
            else:
                element.uncheck()
            return {"success": True, "message": f"Checked: {value}"}

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
        Handle ERP login.
        Override this method for specific ERP systems.
        """
        # Generic implementation - can be customized
        username = credentials.get("username", "")
        password = credentials.get("password", "")

        if not username or not password:
            logger.warning("No credentials provided for login")
            return

        # Wait for login form
        self.page.wait_for_timeout(2000)

        # Try common login field patterns
        try:
            # Username field
            username_field = self.page.locator(
                "input[name*='user' i], input[name*='login' i], input[type='email'], input#username"
            ).first
            if username_field.is_visible():
                username_field.fill(username)

            # Password field
            password_field = self.page.locator(
                "input[type='password']"
            ).first
            if password_field.is_visible():
                password_field.fill(password)

            # Submit
            submit_btn = self.page.locator(
                "button[type='submit'], input[type='submit'], button:has-text('Sign in'), button:has-text('Login')"
            ).first
            if submit_btn.is_visible():
                submit_btn.click()

            # Wait for navigation
            self.page.wait_for_load_state("domcontentloaded", timeout=30000)

            logger.info("Login completed")

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
