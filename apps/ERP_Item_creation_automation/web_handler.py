from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError
import time
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from urllib.parse import urlparse

def validate_url(url: str) -> str:
    """Validate and format URL properly"""
    if not url:
        raise ValueError("URL cannot be empty")

    # Add https:// if no protocol specified
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL format")
        return url
    except Exception as e:
        raise ValueError(f"Invalid URL: {str(e)}")

def start_browser(url: Optional[str] = None, timeout: int = 60000) -> Dict[str, Any]:
    """
    Start a browser instance and navigate to the given URL if provided

    Args:
        url: Optional URL to navigate to
        timeout: Navigation timeout in milliseconds (default 60 seconds)
    """
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Always navigate to about:blank first to ensure browser is ready
        page.goto("about:blank")

        if url:
            try:
                url = validate_url(url)
                logger.info(f"Navigating to validated URL: {url}")
                # Use page.goto with force option to ensure URL is loaded
                response = page.goto(
                    url,
                    timeout=timeout,
                    wait_until="domcontentloaded",
                )

                if not response:
                    logger.warning(f"No response received when loading URL: {url}")
                elif not response.ok:
                    logger.warning(f"Received status {response.status} when loading URL: {url}")

                # Verify the URL is loaded in the address bar
                actual_url = page.url
                if actual_url == "about:blank":
                    logger.error(f"Failed to navigate to {url}, still at about:blank")
                    raise Exception(f"Failed to navigate to {url}")

            except TimeoutError as e:
                logger.error(f"Timeout while loading URL: {url}")
                raise Exception(f"Timeout while loading URL: {url}")
            except Exception as e:
                logger.error(f"Error navigating to URL {url}: {str(e)}")
                raise

        return {
            'playwright': playwright,
            'browser': browser,
            'context': context,
            'page': page
        }
    except Exception as e:
        logger.error(f"Error starting browser: {str(e)}")
        # Cleanup in case of partial initialization
        try:
            if 'page' in locals(): page.close()
            if 'context' in locals(): context.close()
            if 'browser' in locals(): browser.close()
            if 'playwright' in locals(): playwright.stop()
        except:
            pass
        raise

def close_browser(browser_instance: Dict[str, Any]) -> bool:
    """
    Close the browser instance safely

    Returns:
        bool: True if closed successfully, False otherwise
    """
    try:
        browser_instance['page'].close()
        browser_instance['context'].close()
        browser_instance['browser'].close()
        browser_instance['playwright'].stop()
        return True
    except Exception as e:
        logger.error(f"Error closing browser: {str(e)}")
        return False

def get_locator(page: Page, locator_name: str, locators: Dict[str, Any], timeout: int = 30000):
    """
    Get a Playwright locator based on the locator name with timeout
    """
    if locator_name not in locators:
        raise ValueError(f"Locator '{locator_name}' not found")

    locator_info = locators[locator_name]
    locator_type = locator_info['type']
    locator_value = locator_info['value']

    try:
        if locator_type == 'xpath':
            return page.locator(f"xpath={locator_value}")
        elif locator_type == 'css':
            return page.locator(f"css={locator_value}")
        elif locator_type == 'id':
            return page.locator(f"id={locator_value}")
        elif locator_type == 'text':
            return page.get_by_text(locator_value)
        else:
            raise ValueError(f"Unsupported locator type: {locator_type}")
    except Exception as e:
        logger.error(f"Error creating locator for '{locator_name}': {str(e)}")
        raise

def click_element(page: Page, locator_name: str, locators: Dict[str, Any],
                 max_retries: int = 3, delay: int = 1, timeout: int = 30000) -> bool:
    """
    Click on an element with retry logic and timeout
    """
    element = get_locator(page, locator_name, locators)

    for attempt in range(max_retries):
        try:
            # Wait for element to be visible and enabled
            element.wait_for(state="visible", timeout=timeout)
            if not element.is_enabled():
                raise Exception("Element is not enabled")

            element.click(timeout=timeout)
            return True
        except Exception as e:
            logger.warning(f"Click attempt {attempt+1} failed for '{locator_name}': {str(e)}")
            if attempt < max_retries - 1:  # Don't sleep on last attempt
                time.sleep(delay)

    return False

def send_keys(page: Page, locator_name: str, locators: Dict[str, Any], text: str,
             clear: bool = False, max_retries: int = 3, delay: int = 1, timeout: int = 30000) -> bool:
    """
    Send keys to an element with retry logic and timeout
    """
    element = get_locator(page, locator_name, locators)

    for attempt in range(max_retries):
        try:
            # Wait for element to be visible and enabled
            element.wait_for(state="visible", timeout=timeout)
            if not element.is_enabled():
                raise Exception("Element is not enabled")

            if clear:
                element.clear(timeout=timeout)
            element.fill(text, timeout=timeout)
            return True
        except Exception as e:
            logger.warning(f"Send keys attempt {attempt+1} failed for '{locator_name}': {str(e)}")
            if attempt < max_retries - 1:  # Don't sleep on last attempt
                time.sleep(delay)

    return False

def press_key(page: Page, key: str) -> bool:
    """Press a keyboard key safely"""
    try:
        page.keyboard.press(key)
        return True
    except Exception as e:
        logger.error(f"Error pressing key {key}: {str(e)}")
        return False

def execute_action(browser_instance: Dict[str, Any], action_dict: Dict[str, Any],
                  locators: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an action based on the action dictionary with enhanced error handling
    """
    page = browser_instance['page']
    action_name = action_dict.get('name', 'Unknown Action')

    try:
        locator_name = action_dict.get('locator')
        if not locator_name:
            return {'success': False, 'message': f'No locator specified for action: {action_name}'}

        # Get action parameters with defaults
        max_retries = int(action_dict.get('max_retries', 3))
        delay = int(action_dict.get('delay', 1))
        sleep_time = int(action_dict.get('sleep1', 0))
        clear_option = bool(action_dict.get('clear_option', False))
        option_value = action_dict.get('option', '')
        timeout = int(action_dict.get('timeout', 30000))

        # Check for dependent actions
        dependent_click = bool(action_dict.get('dependent_click_check', False))
        dependent_send = bool(action_dict.get('dependent_send_check', False))
        dependent_loc1 = action_dict.get('dependent_loc1', '')
        dependent_val = action_dict.get('dependent_val', '')

        # Execute the main action
        success = False
        logger.info(f"Executing action: {action_name}")

        try:
            # Click action
            if not option_value and not dependent_send:
                success = click_element(page, locator_name, locators, max_retries, delay, timeout)
                if not success:
                    return {'success': False, 'message': f"Click failed for action: {action_name}"}

            # Send keys action
            elif option_value:
                success = send_keys(page, locator_name, locators, option_value, clear_option, max_retries, delay, timeout)
                if not success:
                    return {'success': False, 'message': f"Send keys failed for action: {action_name}"}

            # Sleep after action
            if sleep_time > 0:
                time.sleep(sleep_time)

            # Handle key presses
            for key_num in ['key1', 'key2', 'key3']:
                key = action_dict.get(key_num, '')
                if key and not press_key(page, key):
                    logger.warning(f"Key press failed for {key_num}: {key}")

            # Handle dependent actions
            if dependent_click and dependent_loc1:
                if not click_element(page, dependent_loc1, locators, max_retries, delay, timeout):
                    return {'success': False, 'message': f"Dependent click failed for action: {action_name}"}

            if dependent_send and dependent_loc1 and dependent_val:
                if not send_keys(page, dependent_loc1, locators, dependent_val, clear_option, max_retries, delay, timeout):
                    return {'success': False, 'message': f"Dependent send keys failed for action: {action_name}"}

            return {'success': True, 'message': f"Action '{action_name}' executed successfully"}

        except Exception as e:
            logger.error(f"Error in action execution step: {str(e)}")
            return {'success': False, 'message': f"Action '{action_name}' failed: {str(e)}"}

    except Exception as e:
        logger.error(f"Error executing action '{action_name}': {str(e)}")
        return {'success': False, 'message': str(e)}