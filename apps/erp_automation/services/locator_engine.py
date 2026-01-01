"""
Smart Locator Engine

Handles element location with multiple fallback strategies.
Learns which strategies work best over time.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from playwright.sync_api import Page, Locator as PlaywrightLocator, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class LocatorEngine:
    """
    Smart locator engine with fallback strategies and self-learning.

    Features:
    - Multiple locator strategies per element
    - Automatic fallback when primary fails
    - Success rate tracking to optimize strategy order
    - Scroll-into-view handling
    - Dynamic element detection
    """

    def __init__(self, page: Page):
        self.page = page
        self._locator_cache = {}

    def find_element(
        self,
        locator_obj,  # Django Locator model instance
        timeout: int = None,
        scroll_into_view: bool = None,
    ) -> Optional[PlaywrightLocator]:
        """
        Find an element using multiple strategies until one works.

        Args:
            locator_obj: Django Locator model instance
            timeout: Override default timeout (ms)
            scroll_into_view: Override scroll behavior

        Returns:
            Playwright Locator object or None
        """
        timeout = timeout or locator_obj.default_timeout
        scroll_into_view = scroll_into_view if scroll_into_view is not None else locator_obj.requires_scroll

        strategies = locator_obj.get_strategies_ordered()

        for strategy in strategies:
            try:
                element = self._try_strategy(strategy, timeout)

                if element and self._is_element_valid(element, timeout):
                    # Scroll into view if needed
                    if scroll_into_view:
                        self._scroll_into_view(element)

                    # Update success stats
                    self._record_success(strategy)

                    logger.info(
                        f"Found element '{locator_obj.name}' using {strategy.strategy_type}: "
                        f"{strategy.value[:50]}..."
                    )
                    return element

            except PlaywrightTimeout:
                self._record_failure(strategy)
                logger.debug(
                    f"Strategy {strategy.strategy_type} timed out for '{locator_obj.name}'"
                )
                continue
            except Exception as e:
                self._record_failure(strategy)
                logger.debug(
                    f"Strategy {strategy.strategy_type} failed for '{locator_obj.name}': {e}"
                )
                continue

        logger.error(f"All strategies failed for locator '{locator_obj.name}'")
        return None

    def find_element_by_strategies(
        self,
        strategies: List[Dict[str, Any]],
        timeout: int = 30000,
        scroll_into_view: bool = False,
    ) -> Optional[PlaywrightLocator]:
        """
        Find element using a list of strategy dicts (without Django model).

        Args:
            strategies: List of {"strategy_type": str, "value": str, "priority": int}
            timeout: Timeout in ms
            scroll_into_view: Whether to scroll

        Returns:
            Playwright Locator or None
        """
        # Sort by priority
        sorted_strategies = sorted(strategies, key=lambda x: x.get("priority", 10))

        for strat in sorted_strategies:
            try:
                element = self._create_locator(
                    strat["strategy_type"],
                    strat["value"],
                    strat.get("offset_direction")
                )

                if element and self._is_element_valid(element, timeout):
                    if scroll_into_view:
                        self._scroll_into_view(element)
                    return element

            except Exception as e:
                logger.debug(f"Strategy {strat['strategy_type']} failed: {e}")
                continue

        return None

    def _try_strategy(self, strategy, timeout: int) -> Optional[PlaywrightLocator]:
        """Try a single locator strategy."""
        element = self._create_locator(
            strategy.strategy_type,
            strategy.value,
            strategy.offset_direction
        )
        return element

    def _create_locator(
        self,
        strategy_type: str,
        value: str,
        offset_direction: str = None
    ) -> PlaywrightLocator:
        """Create a Playwright locator based on strategy type."""

        if strategy_type == "id":
            return self.page.locator(f"#{value}")

        elif strategy_type == "css":
            return self.page.locator(value)

        elif strategy_type == "xpath":
            return self.page.locator(f"xpath={value}")

        elif strategy_type == "name":
            return self.page.locator(f"[name='{value}']")

        elif strategy_type == "data-testid":
            return self.page.locator(f"[data-testid='{value}']")

        elif strategy_type == "aria-label":
            return self.page.get_by_label(value)

        elif strategy_type == "text":
            return self.page.get_by_text(value, exact=False)

        elif strategy_type == "role":
            # value format: "button:Submit" or just "button"
            if ":" in value:
                role, name = value.split(":", 1)
                return self.page.get_by_role(role, name=name)
            return self.page.get_by_role(value)

        elif strategy_type == "text-nearby":
            # Find input near a label text
            return self._find_near_text(value, offset_direction)

        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

    def _find_near_text(
        self,
        label_text: str,
        direction: str = "below"
    ) -> Optional[PlaywrightLocator]:
        """
        Find an input element near a label text.
        Useful when elements don't have good identifiers but have nearby labels.
        """
        # First find the label
        label = self.page.get_by_text(label_text, exact=False)

        if direction == "below":
            # Look for input/select following the label
            return label.locator("xpath=following::input[1] | following::select[1]")
        elif direction == "above":
            return label.locator("xpath=preceding::input[1] | preceding::select[1]")
        elif direction == "right":
            # Same line, to the right
            return label.locator("xpath=../following-sibling::*/input | ../input")
        elif direction == "left":
            return label.locator("xpath=../preceding-sibling::*/input | preceding::input[1]")

        # Default: look for any nearby input
        return label.locator("xpath=ancestor::*[position()<=3]//input")

    def _is_element_valid(self, element: PlaywrightLocator, timeout: int) -> bool:
        """Check if element is valid and interactable."""
        try:
            # Wait for element to be visible
            element.wait_for(state="visible", timeout=timeout)

            # Check if there's exactly one match (or use first())
            count = element.count()
            if count == 0:
                return False
            if count > 1:
                logger.debug(f"Multiple elements found ({count}), using first")

            return True
        except:
            return False

    def _scroll_into_view(self, element: PlaywrightLocator):
        """Scroll element into view with smooth behavior."""
        try:
            element.scroll_into_view_if_needed()
            # Small wait for scroll animation
            self.page.wait_for_timeout(200)
        except Exception as e:
            logger.debug(f"Scroll into view failed: {e}")

    def _record_success(self, strategy):
        """Record successful use of a strategy."""
        try:
            strategy.success_count += 1
            strategy.last_used = datetime.now()
            strategy.save(update_fields=["success_count", "last_used"])
        except:
            pass  # Don't fail if DB update fails

    def _record_failure(self, strategy):
        """Record failed use of a strategy."""
        try:
            strategy.failure_count += 1
            strategy.save(update_fields=["failure_count"])
        except:
            pass

    # ==========================================================================
    # SMART LOCATOR GENERATION
    # ==========================================================================

    def generate_smart_locators(self, element: PlaywrightLocator) -> List[Dict[str, Any]]:
        """
        Generate multiple locator strategies for an element.
        Used during recording to capture robust locators.
        """
        strategies = []

        try:
            # Get element handle for evaluation
            handle = element.element_handle()
            if not handle:
                return strategies

            # Evaluate element properties in browser
            props = self.page.evaluate("""
                (element) => {
                    const rect = element.getBoundingClientRect();

                    // Get unique CSS selector
                    const getCssSelector = (el) => {
                        if (el.id) return '#' + el.id;
                        if (el.className) {
                            const classes = el.className.split(' ').filter(c => c).join('.');
                            if (classes) return el.tagName.toLowerCase() + '.' + classes;
                        }
                        return el.tagName.toLowerCase();
                    };

                    // Get XPath
                    const getXPath = (el) => {
                        if (el.id) return `//*[@id="${el.id}"]`;
                        if (el.name) return `//*[@name="${el.name}"]`;

                        const parts = [];
                        while (el && el.nodeType === Node.ELEMENT_NODE) {
                            let index = 0;
                            let sibling = el.previousSibling;
                            while (sibling) {
                                if (sibling.nodeType === Node.ELEMENT_NODE &&
                                    sibling.nodeName === el.nodeName) index++;
                                sibling = sibling.previousSibling;
                            }
                            const tagName = el.nodeName.toLowerCase();
                            const part = index ? `${tagName}[${index + 1}]` : tagName;
                            parts.unshift(part);
                            el = el.parentNode;
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
                        text: element.innerText?.substring(0, 100) || '',
                        dataTestId: element.getAttribute('data-testid') || '',
                        type: element.getAttribute('type') || '',
                        role: element.getAttribute('role') || '',
                        css: getCssSelector(element),
                        xpath: getXPath(element),
                        rect: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        }
                    };
                }
            """, handle)

            # Build strategies in priority order
            priority = 1

            # data-testid (best for testing)
            if props.get("dataTestId"):
                strategies.append({
                    "strategy_type": "data-testid",
                    "value": props["dataTestId"],
                    "priority": priority
                })
                priority += 1

            # aria-label (good accessibility)
            if props.get("ariaLabel"):
                strategies.append({
                    "strategy_type": "aria-label",
                    "value": props["ariaLabel"],
                    "priority": priority
                })
                priority += 1

            # name attribute (stable for forms)
            if props.get("name"):
                strategies.append({
                    "strategy_type": "name",
                    "value": props["name"],
                    "priority": priority
                })
                priority += 1

            # ID (if not dynamic)
            if props.get("id") and not self._is_dynamic_id(props["id"]):
                strategies.append({
                    "strategy_type": "id",
                    "value": props["id"],
                    "priority": priority
                })
                priority += 1

            # CSS selector
            if props.get("css"):
                strategies.append({
                    "strategy_type": "css",
                    "value": props["css"],
                    "priority": priority + 1
                })

            # XPath (fallback)
            if props.get("xpath"):
                strategies.append({
                    "strategy_type": "xpath",
                    "value": props["xpath"],
                    "priority": priority + 2
                })

            # Text content (for buttons/links)
            if props.get("text") and props.get("tagName") in ["button", "a", "span"]:
                strategies.append({
                    "strategy_type": "text",
                    "value": props["text"][:50],
                    "priority": priority + 3
                })

        except Exception as e:
            logger.error(f"Error generating smart locators: {e}")

        return strategies

    def _is_dynamic_id(self, element_id: str) -> bool:
        """Check if an ID appears to be dynamically generated."""
        import re
        dynamic_patterns = [
            r'[0-9a-f]{8}-[0-9a-f]{4}',  # UUID
            r'_\d{10,}',  # Timestamp
            r'[A-Za-z]+_\d+_',  # Framework generated
            r'react-',
            r'ng-',
            r'ember',
            r'__\d+',
        ]
        for pattern in dynamic_patterns:
            if re.search(pattern, element_id, re.IGNORECASE):
                return True
        return False

    # ==========================================================================
    # ELEMENT INTERACTION HELPERS
    # ==========================================================================

    def click(
        self,
        locator_obj,
        timeout: int = None,
        retry_count: int = 3,
        delay_between_retries: float = 1.0,
    ) -> bool:
        """Click an element with retry logic."""
        for attempt in range(retry_count):
            try:
                element = self.find_element(locator_obj, timeout)
                if element:
                    element.click(timeout=timeout or locator_obj.default_timeout)
                    return True
            except Exception as e:
                logger.warning(f"Click attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    self.page.wait_for_timeout(int(delay_between_retries * 1000))
        return False

    def fill(
        self,
        locator_obj,
        value: str,
        clear_first: bool = False,
        timeout: int = None,
        retry_count: int = 3,
    ) -> bool:
        """Fill a text field with retry logic."""
        for attempt in range(retry_count):
            try:
                element = self.find_element(locator_obj, timeout)
                if element:
                    if clear_first:
                        element.clear()
                    element.fill(value, timeout=timeout or locator_obj.default_timeout)
                    return True
            except Exception as e:
                logger.warning(f"Fill attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    self.page.wait_for_timeout(1000)
        return False

    def select_option(
        self,
        locator_obj,
        value: str = None,
        label: str = None,
        timeout: int = None,
    ) -> bool:
        """Select an option from a dropdown."""
        try:
            element = self.find_element(locator_obj, timeout)
            if element:
                if value:
                    element.select_option(value=value)
                elif label:
                    element.select_option(label=label)
                return True
        except Exception as e:
            logger.error(f"Select option failed: {e}")
        return False

    def wait_for_element(
        self,
        locator_obj,
        state: str = "visible",
        timeout: int = None,
    ) -> bool:
        """Wait for element to reach a specific state."""
        try:
            element = self.find_element(locator_obj, timeout)
            if element:
                element.wait_for(state=state, timeout=timeout or locator_obj.default_timeout)
                return True
        except:
            pass
        return False

    def get_text(self, locator_obj, timeout: int = None) -> Optional[str]:
        """Get text content of an element."""
        try:
            element = self.find_element(locator_obj, timeout)
            if element:
                return element.inner_text()
        except:
            pass
        return None

    def is_visible(self, locator_obj, timeout: int = 5000) -> bool:
        """Check if element is visible."""
        try:
            element = self.find_element(locator_obj, timeout)
            return element is not None and element.is_visible()
        except:
            return False

    def take_screenshot(self, locator_obj, path: str) -> bool:
        """Take screenshot of a specific element."""
        try:
            element = self.find_element(locator_obj)
            if element:
                element.screenshot(path=path)
                return True
        except:
            pass
        return False
