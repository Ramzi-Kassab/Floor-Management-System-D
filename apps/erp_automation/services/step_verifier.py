"""
Step Verification Engine — Post-action verification using Playwright assertions.

Each workflow step can have a verification configuration that runs AFTER the step
action succeeds. Verification uses Playwright's expect() API for retry-based
assertions, which are more reliable than immediate checks.

Verify Types:
  - value_match:      expect(locator).to_have_value(expected)
  - element_visible:  expect(locator).to_be_visible()
  - element_hidden:   expect(locator).to_be_hidden()
  - text_contains:    expect(locator).to_contain_text(expected)
  - element_count:    expect(locator).to_have_count(>= N)
  - url_contains:     expect(page).to_have_url(regex)
  - element_enabled:  expect(locator).to_be_enabled()
  - no_error:         assert no D365 error bars visible
  - attr_match:       expect(locator).to_have_attribute(attr, value)
"""

import re
import logging
import time

logger = logging.getLogger(__name__)


class StepVerifier:
    """Post-action verification engine for workflow steps."""

    # D365 error bar selectors
    _ERROR_SELECTORS = [
        ".messageBar-error",
        ".messageBar-critical",
    ]

    # Patterns to ignore in D365 messages (not real errors)
    _IGNORE_PATTERNS = [
        "please wait", "processing your request", "saved successfully",
        "has been created", "loading", "validating", "please wait while",
        "in progress",
    ]

    def __init__(self, page, locator_engine=None):
        """
        Args:
            page: Playwright Page object
            locator_engine: LocatorEngine instance for resolving verify_locator
        """
        self.page = page
        self.locator_engine = locator_engine

    def verify(self, step, row_data=None, context=None):
        """
        Run post-step verification.

        Args:
            step: WorkflowStep instance (must have verify_type, verify_locator, etc.)
            row_data: dict of job data for template resolution
            context: dict of accumulated context (from prior steps)

        Returns:
            dict with keys:
                success (bool): verification passed
                skipped (bool): no verification configured
                message (str): human-readable result
                verify_type (str): what was checked
                duration_ms (int): how long verification took
        """
        if not step.verify_type:
            return {
                "success": True, "skipped": True,
                "message": "No verification configured",
                "verify_type": "", "duration_ms": 0,
            }

        start_time = time.time()
        verify_value = self._resolve_value(step.verify_value, row_data, context)
        timeout = step.verify_timeout or 3000

        logger.info(
            f"[Verify] Step '{step.name}' — type={step.verify_type}, "
            f"value='{verify_value}', timeout={timeout}ms"
        )

        try:
            result = self._dispatch(step, verify_value, timeout)
        except Exception as e:
            result = {"success": False, "message": f"Verification error: {str(e)}"}

        duration_ms = int((time.time() - start_time) * 1000)
        result["verify_type"] = step.verify_type
        result["duration_ms"] = duration_ms
        result.setdefault("skipped", False)

        if result["success"]:
            logger.info(f"[Verify] PASS — {result['message']} ({duration_ms}ms)")
        else:
            logger.warning(f"[Verify] FAIL — {result['message']} ({duration_ms}ms)")

        return result

    def _dispatch(self, step, verify_value, timeout):
        """Route to the correct verification method."""
        vtype = step.verify_type

        if vtype == 'value_match':
            return self._verify_value_match(step, verify_value, timeout)
        elif vtype == 'element_visible':
            return self._verify_element_visible(step, timeout)
        elif vtype == 'element_hidden':
            return self._verify_element_hidden(step, timeout)
        elif vtype == 'text_contains':
            return self._verify_text_contains(step, verify_value, timeout)
        elif vtype == 'element_count':
            return self._verify_element_count(step, verify_value, timeout)
        elif vtype == 'url_contains':
            return self._verify_url_contains(verify_value, timeout)
        elif vtype == 'element_enabled':
            return self._verify_element_enabled(step, timeout)
        elif vtype == 'no_error':
            return self._verify_no_error(timeout)
        elif vtype == 'attr_match':
            return self._verify_attribute_match(step, verify_value, timeout)
        else:
            return {"success": False, "message": f"Unknown verify type: {vtype}"}

    # ── Verification methods ─────────────────────────────────────────────

    def _verify_value_match(self, step, expected, timeout):
        """Verify a field contains the expected value (case-insensitive substring)."""
        element = self._find_verify_element(step)
        if not element:
            return {"success": False, "message": "Verify locator not found"}

        try:
            from playwright.sync_api import expect
            # Use regex for case-insensitive partial match
            # D365 may resolve codes to display names
            pattern = re.compile(re.escape(expected), re.IGNORECASE)
            expect(element).to_have_value(pattern, timeout=timeout)
            actual = element.input_value()
            return {
                "success": True,
                "message": f"Field value matches: '{actual}' contains '{expected}'"
            }
        except AssertionError:
            try:
                actual = element.input_value()
            except Exception:
                actual = "<unreadable>"
            return {
                "success": False,
                "message": f"Value mismatch: expected '{expected}', got '{actual}'"
            }
        except Exception as e:
            return {"success": False, "message": f"Value check error: {str(e)}"}

    def _verify_element_visible(self, step, timeout):
        """Verify an element is visible on the page."""
        element = self._find_verify_element(step)
        if not element:
            return {"success": False, "message": "Verify locator not found"}

        try:
            from playwright.sync_api import expect
            expect(element).to_be_visible(timeout=timeout)
            return {"success": True, "message": "Element is visible"}
        except AssertionError:
            return {"success": False, "message": "Element not visible within timeout"}
        except Exception as e:
            return {"success": False, "message": f"Visibility check error: {str(e)}"}

    def _verify_element_hidden(self, step, timeout):
        """Verify an element is hidden or not present."""
        element = self._find_verify_element(step)
        if not element:
            # If locator engine can't find it at all, it IS hidden
            return {"success": True, "message": "Element not found (hidden)"}

        try:
            from playwright.sync_api import expect
            expect(element).to_be_hidden(timeout=timeout)
            return {"success": True, "message": "Element is hidden"}
        except AssertionError:
            return {"success": False, "message": "Element still visible after timeout"}
        except Exception as e:
            return {"success": False, "message": f"Hidden check error: {str(e)}"}

    def _verify_text_contains(self, step, expected, timeout):
        """Verify an element contains specific text."""
        element = self._find_verify_element(step)
        if not element:
            return {"success": False, "message": "Verify locator not found"}

        try:
            from playwright.sync_api import expect
            expect(element).to_contain_text(expected, timeout=timeout)
            return {"success": True, "message": f"Element contains text '{expected}'"}
        except AssertionError:
            try:
                actual = element.inner_text()
            except Exception:
                actual = "<unreadable>"
            return {
                "success": False,
                "message": f"Text not found: expected '{expected}', got '{actual}'"
            }
        except Exception as e:
            return {"success": False, "message": f"Text check error: {str(e)}"}

    def _verify_element_count(self, step, expected_str, timeout):
        """Verify at least N elements match the verify locator."""
        try:
            min_count = int(expected_str) if expected_str else 1
        except ValueError:
            min_count = 1

        element = self._find_verify_element(step)
        if not element:
            return {"success": False, "message": "Verify locator not found"}

        try:
            # element from locator_engine is an ElementHandle, but we need a Locator
            # for count assertion. Fall back to manual count.
            # Wait for the expected count with polling
            deadline = time.time() + (timeout / 1000.0)
            actual_count = 0
            while time.time() < deadline:
                # Use JS to count matching elements via the verify locator strategies
                actual_count = self._count_verify_elements(step)
                if actual_count >= min_count:
                    return {
                        "success": True,
                        "message": f"Element count {actual_count} >= {min_count}"
                    }
                self.page.wait_for_timeout(300)

            return {
                "success": False,
                "message": f"Element count {actual_count} < {min_count}"
            }
        except Exception as e:
            return {"success": False, "message": f"Count check error: {str(e)}"}

    def _verify_url_contains(self, expected, timeout):
        """Verify the current URL contains a string."""
        if not expected:
            return {"success": False, "message": "No URL pattern specified"}

        try:
            from playwright.sync_api import expect
            pattern = re.compile(re.escape(expected), re.IGNORECASE)
            expect(self.page).to_have_url(pattern, timeout=timeout)
            return {
                "success": True,
                "message": f"URL contains '{expected}'"
            }
        except AssertionError:
            actual_url = self.page.url
            return {
                "success": False,
                "message": f"URL doesn't contain '{expected}'. Current: {actual_url}"
            }
        except Exception as e:
            return {"success": False, "message": f"URL check error: {str(e)}"}

    def _verify_element_enabled(self, step, timeout):
        """Verify an element is enabled (clickable, not disabled)."""
        element = self._find_verify_element(step)
        if not element:
            return {"success": False, "message": "Verify locator not found"}

        try:
            from playwright.sync_api import expect
            expect(element).to_be_enabled(timeout=timeout)
            return {"success": True, "message": "Element is enabled"}
        except AssertionError:
            return {"success": False, "message": "Element is disabled"}
        except Exception as e:
            return {"success": False, "message": f"Enabled check error: {str(e)}"}

    def _verify_no_error(self, timeout):
        """Verify no D365 error bars are visible."""
        # Wait a bit for transient messages to appear
        self.page.wait_for_timeout(min(timeout, 1500))

        for selector in self._ERROR_SELECTORS:
            try:
                locator = self.page.locator(selector)
                if locator.count() > 0 and locator.first.is_visible():
                    text = locator.first.inner_text()
                    # Check if it's a real error or an ignorable message
                    text_lower = text.lower()
                    if any(p in text_lower for p in self._IGNORE_PATTERNS):
                        continue
                    return {
                        "success": False,
                        "message": f"D365 error detected: {text[:200]}"
                    }
            except Exception:
                pass

        return {"success": True, "message": "No D365 errors detected"}

    def _verify_attribute_match(self, step, verify_value, timeout):
        """
        Verify an element has a specific attribute value.
        verify_value format: 'attr_name=expected_value'
        e.g., 'aria-selected=true', 'class=dyn-marked'
        """
        if '=' not in verify_value:
            return {
                "success": False,
                "message": "attr_match format must be 'attr_name=expected_value'"
            }

        attr_name, expected_val = verify_value.split('=', 1)
        attr_name = attr_name.strip()
        expected_val = expected_val.strip()

        element = self._find_verify_element(step)
        if not element:
            return {"success": False, "message": "Verify locator not found"}

        try:
            from playwright.sync_api import expect
            expect(element).to_have_attribute(attr_name, expected_val, timeout=timeout)
            return {
                "success": True,
                "message": f"Attribute '{attr_name}' = '{expected_val}'"
            }
        except AssertionError:
            try:
                actual = element.get_attribute(attr_name)
            except Exception:
                actual = "<not found>"
            return {
                "success": False,
                "message": f"Attribute '{attr_name}': expected '{expected_val}', got '{actual}'"
            }
        except Exception as e:
            return {"success": False, "message": f"Attribute check error: {str(e)}"}

    # ── Helpers ──────────────────────────────────────────────────────────

    def _find_verify_element(self, step):
        """Find the verification target element using verify_locator or action locator."""
        locator = step.verify_locator or step.locator
        if not locator:
            return None

        if not self.locator_engine:
            return None

        try:
            timeout = min(step.verify_timeout or 3000, 5000)
            return self.locator_engine.find_element(locator, timeout=timeout)
        except Exception as e:
            logger.debug(f"[Verify] Locator resolution failed: {e}")
            return None

    def _count_verify_elements(self, step):
        """Count elements matching the verify locator strategies."""
        locator = step.verify_locator or step.locator
        if not locator:
            return 0

        strategies = locator.strategies.filter(is_active=True).order_by('priority')
        for strat in strategies:
            try:
                count = self._count_by_strategy(strat)
                if count > 0:
                    return count
            except Exception:
                continue
        return 0

    def _count_by_strategy(self, strategy):
        """Count elements matching a single strategy."""
        stype = strategy.strategy_type
        value = strategy.value

        if stype == 'css':
            return self.page.locator(value).count()
        elif stype == 'xpath':
            return self.page.locator(f"xpath={value}").count()
        elif stype == 'id':
            return self.page.locator(f"#{value}").count()
        elif stype == 'name':
            return self.page.locator(f"[name='{value}']").count()
        elif stype == 'aria-label':
            return self.page.locator(f"[aria-label='{value}']").count()
        elif stype == 'text':
            return self.page.locator(f"text={value}").count()
        elif stype == 'role':
            return self.page.locator(f"[role='{value}']").count()
        return 0

    def _resolve_value(self, template, row_data=None, context=None):
        """Resolve {{PLACEHOLDER}} tokens in verify_value."""
        if not template:
            return ""

        def replacer(match):
            key = match.group(1).strip()
            if row_data and key in row_data:
                return str(row_data[key])
            if context and key in context:
                return str(context[key])
            return ""

        return re.sub(r'{{(.*?)}}', replacer, template)
