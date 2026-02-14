"""
Chain Executor Service

Executes a WorkflowChain — a sequence of independent workflows run in order
for the same job card. Reuses the browser across links for speed.

Key features:
- Browser stays open between sub-workflows (configurable)
- Context passing: outputs from link N available as inputs to link N+1
- Conditional link skipping
- Stop-on-failure or continue mode
- Full execution tracking via ChainExecution + WorkflowExecution records
"""
import logging
import re
from typing import Dict, Any, Optional

from django.utils import timezone

from .executor import WorkflowExecutor

logger = logging.getLogger(__name__)


class ChainExecutor:
    """
    Orchestrates the execution of a WorkflowChain.

    Uses a single WorkflowExecutor instance (and its Playwright browser)
    across all links when keep_browser_open=True.
    """

    def __init__(self):
        self.executor: Optional[WorkflowExecutor] = None
        self.should_stop = False

    def execute_chain(
        self,
        chain,                    # WorkflowChain model
        job_data,                 # ERPJobData model
        credentials: Dict[str, str],
        chain_execution,          # ChainExecution model (pre-created)
        erp_url: str = "",
    ) -> Dict[str, Any]:
        """
        Execute all active links in the chain sequentially.

        Args:
            chain: WorkflowChain instance
            job_data: ERPJobData with row_data for template substitution
            credentials: {"username": str, "password": str} for ERP login
            chain_execution: ChainExecution tracking record
            erp_url: Default ERP URL (used if link has no navigate_url)

        Returns:
            {"success": bool, "message": str, "completed_links": int}
        """
        from ..models import WorkflowExecution, ExecutionStatus

        links = list(chain.get_active_links())
        total_links = len(links)

        if total_links == 0:
            chain_execution.status = "failed"
            chain_execution.error_message = "No active links in chain"
            chain_execution.completed_at = timezone.now()
            chain_execution.save()
            return {"success": False, "message": "No active links in chain", "completed_links": 0}

        # Initialize tracking
        row_data = job_data.get_row_data() if job_data else {}
        # Inject ERP credentials into row_data so login workflow steps
        # can use {{ERP_USERNAME}} and {{ERP_PASSWORD}} templates
        if credentials:
            row_data['ERP_USERNAME'] = credentials.get('username', '')
            row_data['ERP_PASSWORD'] = credentials.get('password', '')
        accumulated_context = {}
        # Inject ERP URL into context so goto_url steps can use {{ERP_URL}} template
        if erp_url:
            accumulated_context["ERP_URL"] = erp_url
        chain_execution.status = "running"
        chain_execution.started_at = timezone.now()
        chain_execution.total_links = total_links
        chain_execution.row_data = row_data
        chain_execution.save()

        completed_links = 0
        self.should_stop = False

        try:
            for link in links:
                if self.should_stop:
                    logger.info(f"[ChainExec] Stopped by user at link #{link.order}")
                    break

                # --- Check data condition (skip if not matched) ---
                if link.condition_field and link.condition_value:
                    actual_value = row_data.get(link.condition_field, "")
                    if not self._condition_matches(actual_value, link.condition_value):
                        logger.info(
                            f"[ChainExec] Skipping link #{link.order} "
                            f"'{link.get_display_name()}': "
                            f"{link.condition_field}='{actual_value}' != '{link.condition_value}'"
                        )
                        continue

                # --- Check context condition (skip based on accumulated context) ---
                if link.condition_field and link.condition_value and link.condition_field in accumulated_context:
                    ctx_value = accumulated_context[link.condition_field]
                    if not self._condition_matches(str(ctx_value), link.condition_value):
                        logger.info(
                            f"[ChainExec] Skipping link #{link.order} "
                            f"'{link.get_display_name()}': "
                            f"context[{link.condition_field}]='{ctx_value}' != '{link.condition_value}'"
                        )
                        continue

                # --- Update chain execution progress ---
                chain_execution.current_link_order = link.order
                chain_execution.save(update_fields=["current_link_order"])

                # --- Merge accumulated context into row_data ---
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
                            logger.info(
                                f"[ChainExec] Context mapped: "
                                f"{source_key} → {target_key} = {accumulated_context[source_key]}"
                            )

                # --- Ensure browser is alive ---
                # On the first link, don't auto-navigate or auto-login —
                # let the workflow steps handle it (WF-0 does login explicitly).
                # For subsequent links, only restart browser if it died.
                if not self.executor or not self.executor.is_browser_alive():
                    nav_url = link.navigate_url or link.workflow.target_url or erp_url
                    # Skip auto-login when browser is first opened; WF-0 handles it
                    skip_login = (completed_links == 0)
                    creds = None if skip_login else credentials
                    browser_url = None if skip_login else nav_url
                else:
                    browser_url = None  # Already running, no re-nav needed
                    creds = None
                if not self._ensure_browser(browser_url, creds, chain.keep_browser_open):
                    error_msg = f"Failed to start/restart browser for link #{link.order}"
                    logger.error(f"[ChainExec] {error_msg}")
                    chain_execution.status = "failed"
                    chain_execution.error_message = error_msg
                    chain_execution.completed_at = timezone.now()
                    chain_execution.save()
                    return {"success": False, "message": error_msg, "completed_links": completed_links}

                # --- Navigate if link has a specific URL ---
                if link.navigate_url and self.executor.page:
                    try:
                        url = link.navigate_url.strip()
                        if url and not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        self.executor.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                        self.executor.page.wait_for_timeout(link.wait_before_ms)
                    except Exception as e:
                        logger.warning(f"[ChainExec] Navigation to {link.navigate_url} failed: {e}")
                elif link.wait_before_ms > 0 and self.executor.page:
                    self.executor.page.wait_for_timeout(link.wait_before_ms)

                # --- Verify browser is still alive before precondition/execution ---
                if not self.executor or not self.executor.is_browser_alive():
                    error_msg = (
                        f"Browser closed unexpectedly before link #{link.order} "
                        f"'{link.get_display_name()}'"
                    )
                    logger.error(f"[ChainExec] {error_msg}")
                    chain_execution.status = "failed"
                    chain_execution.error_message = error_msg
                    chain_execution.completed_at = timezone.now()
                    chain_execution.save()
                    return {
                        "success": False,
                        "message": error_msg,
                        "completed_links": completed_links,
                        "browser_dead": True,
                    }

                # --- Page precondition check ---
                if link.precondition_type and link.precondition_selector:
                    precondition_met = self._check_precondition(link)
                    should_skip = (
                        (precondition_met and link.skip_if_found) or
                        (not precondition_met and not link.skip_if_found)
                    )
                    if should_skip:
                        reason = (
                            f"found" if precondition_met else "not found"
                        )
                        skip_msg = (
                            f"Precondition: '{link.precondition_selector[:60]}' {reason} → "
                            f"{'skip_if_found=True' if link.skip_if_found else 'skip_if_not_found'}"
                        )
                        logger.info(
                            f"[ChainExec] Skipping link #{link.order} "
                            f"'{link.get_display_name()}': {skip_msg}"
                        )
                        # Store in context so downstream links can use this
                        check_key = f"_precondition_{link.order}"
                        accumulated_context[check_key] = "skipped"
                        accumulated_context[f"_precondition_{link.order}_found"] = precondition_met
                        chain_execution.context = accumulated_context
                        chain_execution.save(update_fields=["context"])
                        continue
                    else:
                        logger.info(
                            f"[ChainExec] Precondition passed for link #{link.order}: "
                            f"proceeding with '{link.get_display_name()}'"
                        )

                # --- Create WorkflowExecution record ---
                wf_execution = WorkflowExecution.objects.create(
                    workflow=link.workflow,
                    job_data=job_data,
                    chain_execution=chain_execution,
                    status=ExecutionStatus.PENDING,
                    row_data=merged_row_data,
                )

                # --- Execute the workflow ---
                logger.info(
                    f"[ChainExec] Running link #{link.order}: "
                    f"'{link.get_display_name()}' ({link.workflow.name})"
                )
                result = self.executor.execute_workflow(
                    workflow=link.workflow,
                    row_data=merged_row_data,
                    execution_record=wf_execution,
                )

                if result["success"]:
                    completed_links += 1
                    chain_execution.completed_links = completed_links
                    chain_execution.save(update_fields=["completed_links"])

                    # Merge workflow context into accumulated context
                    wf_context = result.get("context", {})
                    if wf_context:
                        accumulated_context.update(wf_context)
                        chain_execution.context = accumulated_context
                        chain_execution.save(update_fields=["context"])

                    logger.info(
                        f"[ChainExec] Link #{link.order} completed "
                        f"({completed_links}/{total_links})"
                    )
                else:
                    error_msg = (
                        f"Link #{link.order} '{link.get_display_name()}' failed: "
                        f"{result.get('message', 'Unknown error')}"
                    )
                    logger.error(f"[ChainExec] {error_msg}")

                    # If browser died, always abort immediately
                    if result.get("browser_dead"):
                        error_msg = (
                            f"Browser closed unexpectedly during link #{link.order} "
                            f"'{link.get_display_name()}'. Chain aborted."
                        )
                        logger.error(f"[ChainExec] {error_msg}")
                        chain_execution.status = "failed"
                        chain_execution.error_message = error_msg
                        chain_execution.completed_at = timezone.now()
                        chain_execution.save()
                        return {
                            "success": False,
                            "message": error_msg,
                            "completed_links": completed_links,
                            "failed_link": link.order,
                            "browser_dead": True,
                        }

                    if chain.stop_on_failure:
                        chain_execution.status = "failed"
                        chain_execution.error_message = error_msg
                        chain_execution.completed_at = timezone.now()
                        chain_execution.save()
                        return {
                            "success": False,
                            "message": error_msg,
                            "completed_links": completed_links,
                            "failed_link": link.order,
                        }
                    else:
                        # Continue to next link despite failure
                        logger.warning(
                            f"[ChainExec] Continuing after failure (stop_on_failure=False)"
                        )

            # --- Chain complete ---
            if self.should_stop:
                chain_execution.status = "cancelled"
                chain_execution.completed_at = timezone.now()
                chain_execution.save()
                return {
                    "success": False,
                    "message": "Chain stopped by user",
                    "completed_links": completed_links,
                }

            chain_execution.status = "success"
            chain_execution.completed_at = timezone.now()
            chain_execution.context = accumulated_context
            chain_execution.save()

            msg = f"Chain completed: {completed_links}/{total_links} links"
            logger.info(f"[ChainExec] {msg}")
            return {
                "success": True,
                "message": msg,
                "completed_links": completed_links,
                "context": accumulated_context,
            }

        except Exception as e:
            logger.exception(f"[ChainExec] Fatal error: {e}")
            chain_execution.status = "failed"
            chain_execution.error_message = str(e)
            chain_execution.completed_at = timezone.now()
            chain_execution.save()
            return {
                "success": False,
                "message": str(e),
                "completed_links": completed_links,
            }

    def _ensure_browser(
        self,
        url: str,
        credentials: Dict[str, str],
        keep_open: bool,
    ) -> bool:
        """Ensure the browser is alive. Start or restart if needed."""
        if self.executor and keep_open and self.executor.is_browser_alive():
            return True

        # Need to start (or restart) browser
        if self.executor:
            try:
                self.executor.stop_browser()
            except Exception:
                pass

        self.executor = WorkflowExecutor()
        return self.executor.start_browser(
            url=url,
            headless=False,
            credentials=credentials,
            timeout=60000,
        )

    def _check_precondition(self, link) -> bool:
        """
        Check a page precondition before running a chain link.

        Returns True if the precondition IS met (element found / text found / count exceeded).
        The caller then uses link.skip_if_found to decide whether to skip.
        """
        if not self.executor or not self.executor.page:
            logger.warning("[ChainExec] No page available for precondition check")
            return False

        page = self.executor.page
        selector = link.precondition_selector.strip()
        timeout = link.precondition_timeout_ms
        check_type = link.precondition_type

        try:
            if check_type == "element_exists":
                # Check if element matching CSS/XPath selector exists
                # Support both CSS selectors and XPath
                try:
                    locator = page.locator(selector)
                    count = locator.count()
                    if count > 0:
                        logger.info(
                            f"[ChainExec] Precondition: '{selector[:60]}' found "
                            f"({count} elements)"
                        )
                        return True

                    # Wait briefly for element to appear (D365 may be loading)
                    try:
                        locator.first.wait_for(state="visible", timeout=timeout)
                        return True
                    except Exception:
                        pass

                    # Also check all iframes (D365 renders in iframes)
                    for frame in page.frames:
                        if frame == page.main_frame:
                            continue
                        try:
                            f_locator = frame.locator(selector)
                            if f_locator.count() > 0:
                                logger.info(
                                    f"[ChainExec] Precondition: '{selector[:60]}' "
                                    f"found in iframe"
                                )
                                return True
                        except Exception:
                            continue

                except Exception as e:
                    logger.debug(f"[ChainExec] Precondition selector error: {e}")

                logger.info(f"[ChainExec] Precondition: '{selector[:60]}' NOT found")
                return False

            elif check_type == "text_contains":
                # Check if page contains specific text
                search_text = link.precondition_value or selector
                try:
                    # Check main page
                    body_text = page.inner_text("body", timeout=timeout)
                    if search_text.lower() in body_text.lower():
                        logger.info(
                            f"[ChainExec] Precondition: text '{search_text[:40]}' found"
                        )
                        return True

                    # Check iframes
                    for frame in page.frames:
                        if frame == page.main_frame:
                            continue
                        try:
                            frame_text = frame.inner_text("body", timeout=2000)
                            if search_text.lower() in frame_text.lower():
                                logger.info(
                                    f"[ChainExec] Precondition: text '{search_text[:40]}' "
                                    f"found in iframe"
                                )
                                return True
                        except Exception:
                            continue

                except Exception as e:
                    logger.debug(f"[ChainExec] Text check error: {e}")

                logger.info(
                    f"[ChainExec] Precondition: text '{search_text[:40]}' NOT found"
                )
                return False

            elif check_type == "element_count_gt":
                # Check if element count exceeds a threshold
                threshold = int(link.precondition_value or "0")
                try:
                    locator = page.locator(selector)
                    # Wait briefly for elements to render
                    page.wait_for_timeout(min(timeout, 3000))
                    count = locator.count()

                    # Also check iframes
                    for frame in page.frames:
                        if frame == page.main_frame:
                            continue
                        try:
                            count += frame.locator(selector).count()
                        except Exception:
                            continue

                    met = count > threshold
                    logger.info(
                        f"[ChainExec] Precondition: '{selector[:40]}' count={count} "
                        f"{'>' if met else '<='} {threshold}"
                    )
                    return met

                except Exception as e:
                    logger.debug(f"[ChainExec] Count check error: {e}")
                    return False

            else:
                logger.warning(f"[ChainExec] Unknown precondition type: {check_type}")
                return False

        except Exception as e:
            logger.error(f"[ChainExec] Precondition check error: {e}")
            return False

    def _condition_matches(self, actual: str, expected: str) -> bool:
        """Case-insensitive condition matching with normalization."""
        if not actual or not expected:
            return False
        actual_norm = re.sub(r'[\s_.-]+', '-', str(actual).upper().strip())
        expected_norm = re.sub(r'[\s_.-]+', '-', str(expected).upper().strip())
        return actual_norm == expected_norm

    def stop(self):
        """Signal chain to stop."""
        self.should_stop = True
        if self.executor:
            self.executor.stop()

    def cleanup(self):
        """Stop browser and clean up resources."""
        if self.executor:
            try:
                self.executor.stop_browser()
            except Exception:
                pass
            self.executor = None
