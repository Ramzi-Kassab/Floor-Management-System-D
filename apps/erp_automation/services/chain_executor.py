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
- Batch execution: run same chain for multiple jobs, skipping WF-0 login after first
"""
import logging
import re
from typing import Dict, Any, Optional, List, Callable

from django.db import close_old_connections
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
        if credentials:
            row_data['ERP_USERNAME'] = credentials.get('username', '')
            row_data['ERP_PASSWORD'] = credentials.get('password', '')
        accumulated_context = {}
        if erp_url:
            accumulated_context["ERP_URL"] = erp_url
        chain_execution.status = "running"
        chain_execution.started_at = timezone.now()
        chain_execution.total_links = total_links
        chain_execution.row_data = row_data
        chain_execution.save()

        self.should_stop = False

        result = self._execute_links(
            links=links,
            job_data=job_data,
            row_data=row_data,
            credentials=credentials,
            chain=chain,
            chain_execution=chain_execution,
            erp_url=erp_url,
            accumulated_context=accumulated_context,
            save_to_job_data=True,
        )

        # Save captured values back to job_data (belt-and-suspenders; _execute_links does it too)
        if result.get("success") and job_data and result.get("context"):
            self._save_captured_values(job_data, result["context"])

        return result

    def execute_batch(
        self,
        chain,                              # WorkflowChain model
        job_data_list: List,                # List of ERPJobData models
        credentials: Dict[str, str],
        erp_url: str = "",
        on_job_complete: Optional[Callable] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a chain for multiple jobs sequentially, sharing one browser.

        First job: runs ALL links (including WF-0 login).
        Subsequent jobs: skips the first link (WF-0 login) — browser already authenticated.

        Saves captured ERP values (Item Number, Journal Number) to each job_data
        immediately after that job completes.

        Args:
            chain: WorkflowChain instance
            job_data_list: List of ERPJobData records to process
            credentials: {"username": str, "password": str} for ERP login
            erp_url: Default ERP URL
            on_job_complete: Optional callback(job_index, job_data, result) called after each job

        Returns:
            List of result dicts, one per job.
        """
        from ..models import ChainExecution, ExecutionStatus

        all_links = list(chain.get_active_links())
        if not all_links:
            return [{"success": False, "message": "No active links in chain", "completed_links": 0}]

        results = []
        self.should_stop = False

        print(f"[BATCH] Starting batch loop: {len(job_data_list)} jobs, {len(all_links)} links per job")

        for idx, job_data in enumerate(job_data_list):
            print(f"\n[BATCH] --- Loop iteration {idx + 1}/{len(job_data_list)} (job pk={job_data.pk}) ---")

            if self.should_stop:
                print(f"[BATCH] Stopped by user at job {idx + 1}")
                for remaining_idx in range(idx, len(job_data_list)):
                    results.append({
                        "success": False,
                        "message": "Batch stopped by user",
                        "completed_links": 0,
                    })
                break

            is_first_job = (idx == 0)
            links = all_links if is_first_job else all_links[1:]

            print(f"[BATCH] Job {idx + 1}: {job_data.get_display_name()}, "
                  f"{'all links' if is_first_job else 'skip WF-0'}, "
                  f"{len(links)} links to run")

            # Refresh DB connections (critical for long-running background threads)
            close_old_connections()

            try:
                # Reload job_data from DB to avoid stale state
                from ..models import ERPJobData
                job_data = ERPJobData.objects.get(pk=job_data.pk)
                print(f"[BATCH] Job {idx + 1}: reloaded from DB, status={job_data.status}")

                # Build row_data for this specific job
                row_data = job_data.get_row_data() if job_data else {}
                if credentials:
                    row_data['ERP_USERNAME'] = credentials.get('username', '')
                    row_data['ERP_PASSWORD'] = credentials.get('password', '')

                accumulated_context = {}
                if erp_url:
                    accumulated_context["ERP_URL"] = erp_url

                # Create ChainExecution record for this job
                chain_execution = ChainExecution.objects.create(
                    chain=chain,
                    job_data=job_data,
                    status=ExecutionStatus.RUNNING,
                    started_at=timezone.now(),
                    total_links=len(links),
                    row_data=row_data,
                )
                print(f"[BATCH] Job {idx + 1}: CE#{chain_execution.pk} created")

                # Mark job as SENT
                job_data.status = 'SENT'
                job_data.save(update_fields=['status', 'updated_at'])
                print(f"[BATCH] Job {idx + 1}: status set to SENT")

                # Run links for this job (reusing the shared browser)
                print(f"[BATCH] Job {idx + 1}: calling _execute_links()...")
                result = self._execute_links(
                    links=links,
                    job_data=job_data,
                    row_data=row_data,
                    credentials=credentials,
                    chain=chain,
                    chain_execution=chain_execution,
                    erp_url=erp_url,
                    accumulated_context=accumulated_context,
                    save_to_job_data=False,
                )

                print(f"[BATCH] Job {idx + 1}: _execute_links() returned: "
                      f"success={result.get('success')}, "
                      f"completed_links={result.get('completed_links')}, "
                      f"msg={result.get('message', '')[:60]}")

                # Refresh connection before saving results
                close_old_connections()

                # Save captured values and update status
                if result.get("success"):
                    job_data.status = 'COMPLETED'
                    ctx = result.get("context", {})
                    self._save_captured_values(job_data, ctx)
                    job_data.save(update_fields=['status', 'updated_at'])
                    print(f"[BATCH] Job {idx + 1}: COMPLETED successfully")
                else:
                    job_data.status = 'ERROR'
                    job_data.save(update_fields=['status', 'updated_at'])
                    print(f"[BATCH] Job {idx + 1}: FAILED — {result.get('message', 'Unknown error')[:80]}")

            except Exception as e:
                import traceback
                print(f"[BATCH] Job {idx + 1}: EXCEPTION: {e}")
                print(traceback.format_exc())
                logger.exception(
                    f"[BatchExec] Exception in job {idx + 1}/{len(job_data_list)} "
                    f"(pk={job_data.pk}): {e}"
                )
                result = {
                    "success": False,
                    "message": f"Batch job exception: {e}",
                    "completed_links": 0,
                }
                try:
                    close_old_connections()
                    job_data.status = 'ERROR'
                    job_data.save(update_fields=['status', 'updated_at'])
                except Exception as save_err:
                    print(f"[BATCH] Job {idx + 1}: Failed to save ERROR status: {save_err}")

            results.append(result)

            if on_job_complete:
                on_job_complete(idx, job_data, result)

            # If job failed and browser died, abort entire batch
            if not result["success"] and result.get("browser_dead"):
                print(f"[BATCH] Browser died — aborting batch")
                break

            # If job failed and stop_on_failure, abort batch
            if not result["success"] and chain.stop_on_failure:
                print(f"[BATCH] Job failed + stop_on_failure=True — stopping batch")
                break

            print(f"[BATCH] Job {idx + 1}: done, continuing to next job...")

        print(f"\n[BATCH] Batch loop finished: "
              f"{sum(1 for r in results if r.get('success'))}/{len(results)} succeeded")
        return results

    def _execute_links(
        self,
        links: list,
        job_data,
        row_data: Dict[str, Any],
        credentials: Dict[str, str],
        chain,
        chain_execution,
        erp_url: str,
        accumulated_context: Dict[str, Any],
        save_to_job_data: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a list of chain links sequentially.

        This is the core link-iteration logic, extracted so both execute_chain()
        and execute_batch() can reuse it.

        Returns:
            {"success": bool, "message": str, "completed_links": int, "context": dict}
        """
        from ..models import WorkflowExecution, ExecutionStatus

        total_links = len(links)
        completed_links = 0

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

                # --- Skip link if required template variables are empty ---
                # e.g. WF-9 uses {{ROUTE}} — skip if ROUTE is empty (scrap jobs)
                skip_link = False
                for step in link.workflow.steps.filter(is_active=True):
                    templates = [step.value_template or '', step.value_static or '']
                    for tmpl in templates:
                        if '{{ROUTE}}' in tmpl and not merged_row_data.get('ROUTE', ''):
                            logger.info(
                                f"[ChainExec] Skipping link #{link.order} "
                                f"'{link.get_display_name()}': step '{step.name}' "
                                f"requires ROUTE but it is empty (scrap job)"
                            )
                            skip_link = True
                            break
                    if skip_link:
                        break
                if skip_link:
                    continue

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

            # Save captured values back to job_data (skip when called from batch mode)
            if save_to_job_data and job_data and accumulated_context:
                self._save_captured_values(job_data, accumulated_context)

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

    def _save_captured_values(self, job_data, context: Dict[str, Any]):
        """Save captured ERP values (ITEM_NO, JOURNAL_NUMBER) to job_data immediately."""
        update_fields = ['updated_at']
        if context.get("ITEM_NO"):
            job_data.item_number = context["ITEM_NO"]
            update_fields.append('item_number')
        if context.get("JOURNAL_NUMBER"):
            job_data.movement_journal_number = context["JOURNAL_NUMBER"]
            update_fields.append('movement_journal_number')
        if len(update_fields) > 1:
            job_data.save(update_fields=update_fields)
            logger.info(f"[ChainExec] Saved captured values to job_data: {update_fields}")

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
