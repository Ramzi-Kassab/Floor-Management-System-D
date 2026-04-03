"""
Executor V2 — Enhanced DebugExecutor with:
  1. Post-step verification (using StepVerifier + Playwright expect() assertions)
  2. Start-from-link (skip earlier chain links, inject initial context)

This file subclasses DebugExecutor and overrides:
  - start_debug_chain()  → adds start_from_link_order + initial_context
  - _debug_step_loop()   → adds verification after each successful step

All other methods (browser management, _execute_step, _pause_and_process_commands,
auto-heal, etc.) are inherited from DebugExecutor unchanged.
"""

import logging
import queue

from django.utils import timezone

from .executor import DebugExecutor
from .step_verifier import StepVerifier

logger = logging.getLogger(__name__)


class DebugExecutorV2(DebugExecutor):
    """Enhanced debug executor with step verification and start-from-link."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._step_verifier = None  # Created after browser starts

    def _get_verifier(self):
        """Lazy-init the StepVerifier (needs page + locator_engine)."""
        if self._step_verifier is None and self.page:
            self._step_verifier = StepVerifier(self.page, self.locator_engine)
        return self._step_verifier

    # ══════════════════════════════════════════════════════════════════════
    # start_debug_chain — with start_from_link_order + initial_context
    # ══════════════════════════════════════════════════════════════════════

    def start_debug_chain(self, chain, job_data, chain_execution, credentials, erp_url,
                          job_data_list=None,
                          start_from_link_order=None,
                          initial_context=None):
        """
        Entry point for debug chain execution with start-from-link support.

        New parameters:
          start_from_link_order (int|None): Skip all links before this order.
              The browser still opens, but WF-0 (login) and earlier workflows
              are skipped. User must provide initial_context with any values
              those skipped links would have produced (e.g., ITEM_NO).
          initial_context (dict|None): Pre-populated context variables to inject
              into accumulated_context before starting. Used when starting from
              a mid-chain point to supply values from prior runs.
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
        logger.info(
            f"[DebugChainV2] Batch mode={batch_mode}, {batch_total} job(s), "
            f"start_from_link_order={start_from_link_order}"
        )

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

            # Start browser — DON'T auto-login or auto-navigate
            logger.info("[DebugChainV2] Starting browser (no auto-login)...")
            if not self.start_browser(url=None, headless=False, credentials=None):
                self._update_state(status="failed", error={"message": "Failed to start browser"})
                chain_execution.status = "failed"
                chain_execution.error_message = "Failed to start browser"
                chain_execution.completed_at = timezone.now()
                chain_execution.save()
                return

            self.ready_event.set()
            logger.info(f"[DebugChainV2] Browser ready, {total_links} links, {batch_total} job(s)")

            # ── Determine which links to run ──────────────────────────
            if start_from_link_order is not None:
                # Filter links: only those with order >= start_from_link_order
                original_count = len(all_links)
                all_links = [l for l in all_links if l.order >= start_from_link_order]
                skipped_count = original_count - len(all_links)
                logger.info(
                    f"[DebugChainV2] Start-from link order {start_from_link_order}: "
                    f"skipping {skipped_count} links, running {len(all_links)}"
                )

            # ── Outer job loop (batch mode) ───────────────────────────
            batch_abort = False
            for job_idx, cur_job_stub in enumerate(all_jobs):
                if self.should_stop or batch_abort:
                    break

                is_first_job = (job_idx == 0)

                # Reload job from DB
                close_old_connections()
                cur_job = ERPJobData.objects.select_related('route').get(pk=cur_job_stub.pk)

                # First job: all remaining links. Subsequent: skip WF-0 (first link)
                if start_from_link_order is not None:
                    # Already filtered above — use all_links for first, skip first for others
                    links = all_links if is_first_job else all_links
                    # If start_from is after WF-0, subsequent jobs also start there
                else:
                    links = all_links if is_first_job else all_links[1:]
                links_count = len(links)

                # Build row_data for this job
                row_data = cur_job.get_row_data() if cur_job else {}
                if credentials:
                    row_data['ERP_USERNAME'] = credentials.get('username', '')
                    row_data['ERP_PASSWORD'] = credentials.get('password', '')

                # Initialize accumulated_context with user-provided initial context
                accumulated_context = {}
                if erp_url:
                    accumulated_context["ERP_URL"] = erp_url
                if initial_context and is_first_job:
                    accumulated_context.update(initial_context)
                    logger.info(
                        f"[DebugChainV2] Injected initial context: "
                        f"{list(initial_context.keys())}"
                    )

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

                # Track current job PK for duplicate item number retry
                self._current_job_data_pk = cur_job.pk

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
                    f"[DebugChainV2] ═══ Job {job_idx+1}/{batch_total}: "
                    f"{cur_job.get_display_name()} "
                    f"({'all links' if is_first_job else 'skip WF-0'}) ═══"
                )

                completed_link_count = 0
                job_failed = False

                # ── Inner link loop ───────────────────────────────────
                link_idx = 0
                while link_idx < len(links):
                    link = links[link_idx]
                    if self.should_stop:
                        logger.info(f"[DebugChainV2] Stopped by user at link #{link.order}")
                        break

                    link_display = link.get_display_name()

                    # --- Check data condition ---
                    if link.condition_field and link.condition_value:
                        actual_value = row_data.get(link.condition_field, "")
                        actual_norm = regex.sub(r'[\s_.-]+', '-', str(actual_value).upper().strip())
                        expected_norm = regex.sub(r'[\s_.-]+', '-', str(link.condition_value).upper().strip())
                        if actual_norm != expected_norm:
                            reason = f"{link.condition_field}='{actual_value}' != '{link.condition_value}'"
                            logger.info(f"[DebugChainV2] Skipping link #{link.order} '{link_display}': {reason}")
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
                                logger.info(f"[DebugChainV2] Context mapped: {source_key} → {target_key}")

                    # --- Skip link if required template variables are empty ---
                    skip_link = False
                    for step in link.workflow.steps.filter(is_active=True):
                        templates = [step.value_template or '', step.value_static or '']
                        for tmpl in templates:
                            if '{{ROUTE}}' in tmpl and not merged_row_data.get('ROUTE', ''):
                                reason = "step requires ROUTE but it is empty (scrap job)"
                                logger.info(f"[DebugChainV2] Skipping link #{link.order} '{link_display}': {reason}")
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
                            logger.warning(f"[DebugChainV2] Navigation to {link.navigate_url} failed: {e}")
                    elif link.wait_before_ms > 0 and self.page:
                        self.page.wait_for_timeout(link.wait_before_ms)

                    # --- Browser health check ---
                    if not self.is_browser_alive():
                        error_msg = f"Browser closed unexpectedly before link #{link.order} '{link_display}'"
                        logger.error(f"[DebugChainV2] {error_msg}")
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
                            logger.info(f"[DebugChainV2] Skipping link #{link.order} '{link_display}': {reason}")
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

                    # --- Create WorkflowExecution record ---
                    wf_execution = WorkflowExecution.objects.create(
                        workflow=link.workflow,
                        job_data=cur_job,
                        chain_execution=ce,
                        status=ExecutionStatus.PENDING,
                        row_data=merged_row_data,
                    )

                    # --- Reset step-level state ---
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

                    logger.info(f"[DebugChainV2] Running link #{link.order}: '{link_display}' ({link.workflow.name})")

                    # --- Execute the workflow's steps via debug loop ---
                    loop_result = self._debug_step_loop(link.workflow, merged_row_data, wf_execution)

                    # Handle jump-to-link command
                    if loop_result == "JUMP_LINK":
                        target_link_order = self._debug_state.get("_rerun_from_link_order")
                        if target_link_order is not None:
                            target_idx = next((i for i, l in enumerate(links) if l.order == target_link_order), link_idx)
                            logger.info(f"[DebugChainV2] Jumping to link index {target_idx} (order {target_link_order})")
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
                            self._debug_state["completed_links"].append({
                                "order": link.order,
                                "name": link_display,
                                "workflow_name": link.workflow.name,
                                "workflow_id": link.workflow_id,
                                "status": "success",
                            })

                        logger.info(f"[DebugChainV2] Link #{link.order} completed ({completed_link_count}/{links_count})")

                    elif wf_execution.status == "cancelled":
                        logger.info(f"[DebugChainV2] Link #{link.order} stopped by user")
                        break

                    else:
                        # Failed
                        error_msg = (
                            f"Link #{link.order} '{link_display}' failed: "
                            f"{wf_execution.error_message or 'Unknown error'}"
                        )
                        logger.error(f"[DebugChainV2] {error_msg}")

                        with self._lock:
                            self._debug_state["completed_links"].append({
                                "order": link.order,
                                "name": link_display,
                                "workflow_name": link.workflow.name,
                                "workflow_id": link.workflow_id,
                                "status": "failed",
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
                            logger.warning("[DebugChainV2] Continuing after failure (stop_on_failure=False)")

                    link_idx += 1
                # ── End inner link loop ──────────────────────────────

                # ── Per-job finalization ──────────────────────────────
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
                    logger.info(f"[DebugChainV2] Job {job_idx+1}/{batch_total} COMPLETED: {cur_job.get_display_name()}")

                elif self.should_stop:
                    ce.status = "cancelled"
                    ce.completed_at = timezone.now()
                    ce.save()
                    cur_job.status = 'ERROR'
                    cur_job.save(update_fields=['status', 'updated_at'])

                elif job_failed:
                    cur_job.status = 'ERROR'
                    cur_job.save(update_fields=['status', 'updated_at'])

                # Update batch_jobs status
                if batch_mode:
                    with self._lock:
                        bj = self._debug_state.get("batch_jobs", [])
                        if job_idx < len(bj):
                            bj[job_idx]['status'] = 'completed' if not job_failed else 'failed'

            # ── All jobs done ─────────────────────────────────────────
            if self.should_stop:
                self._update_state(status="stopped")
            elif batch_abort:
                self._update_state(status="failed")
            else:
                self._update_state(status="completed")
                logger.info(f"[DebugChainV2] Batch complete: {batch_total} job(s) processed")

        except Exception as e:
            logger.exception(f"[DebugChainV2] Fatal error: {e}")
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

    # ══════════════════════════════════════════════════════════════════════
    # _debug_step_loop — with post-step verification
    # ══════════════════════════════════════════════════════════════════════

    def _debug_step_loop(self, workflow, row_data, execution_record):
        """Main step loop with verification after each successful step.

        Identical to parent except: after a step succeeds and before recording
        completion, runs StepVerifier.verify() if the step has verify_type set.
        Verification failure is treated like a step failure (pause for user).
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
        steps = []
        i = 0
        while i < len(raw_steps):
            s = raw_steps[i]
            if s.repeat_group:
                group_name = s.repeat_group
                group_steps = []
                data_source_key = None
                while i < len(raw_steps) and raw_steps[i].repeat_group == group_name:
                    if raw_steps[i].repeat_data_source:
                        data_source_key = raw_steps[i].repeat_data_source
                    group_steps.append(raw_steps[i])
                    i += 1
                data_source_key = data_source_key or group_name.upper()
                loop_data = row_data.get(data_source_key, []) if row_data else []
                if not isinstance(loop_data, list):
                    loop_data = []
                if not loop_data:
                    logger.warning(f"[DebugExecV2] Repeat group '{group_name}': no data, skipping")
                else:
                    logger.info(f"[DebugExecV2] Repeat group '{group_name}': {len(loop_data)} × {len(group_steps)} steps")
                    for loop_idx, loop_item in enumerate(loop_data):
                        loop_ctx = {
                            'LOOP_INDEX': str(loop_idx),
                            'LOOP_ITERATION': str(loop_idx + 1),
                        }
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

        skipped_groups = set()

        idx = 0
        while idx < len(steps):
            step, loop_ctx = steps[idx]

            # ── Skip group check ──
            if step.skip_group and step.skip_group in skipped_groups:
                logger.info(f"[DebugExecV2] [skip_group] Skipping step {step.order} '{step.name}'")
                with self._lock:
                    self._debug_state["completed_steps"].append({
                        "id": step.pk, "order": step.order, "name": step.name,
                        "status": "skipped", "duration_ms": 0,
                    })
                self._create_step_record(execution_record, step, "skipped",
                    {"success": False, "message": f"Skip group '{step.skip_group}'"},
                    timezone.now())
                idx += 1
                continue

            # Merge loop context
            if loop_ctx:
                step_row_data = dict(row_data) if row_data else {}
                step_row_data.update(loop_ctx)
            else:
                step_row_data = row_data

            if self.should_stop:
                logger.info("[DebugExecV2] Stopped by user")
                break

            if not self.is_browser_alive():
                error_msg = "Browser closed unexpectedly."
                logger.error(f"[DebugExecV2] {error_msg}")
                if not in_chain_mode:
                    self._update_state(status="failed", error={"message": error_msg})
                if execution_record:
                    execution_record.status = "failed"
                    execution_record.error_message = error_msg
                    execution_record.completed_at = timezone.now()
                    execution_record.save()
                return

            self._drain_commands()

            # ── Breakpoints ──
            with self._lock:
                bp_ids = self._debug_state.get("breakpoint_step_ids", set())
            if step.pk in bp_ids:
                logger.info(f"[DebugExecV2] Breakpoint at step {step.order}: {step.name}")
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
                    error={"message": f"Breakpoint at step {step.order}: {step.name}", "is_breakpoint": True},
                    screenshot_base64=screenshot_b64,
                )
                bp_action = self._pause_and_process_commands()
                if bp_action == "stop":
                    break
                elif bp_action == "rerun_from_step":
                    target_step_id = self._debug_state.get("_rerun_from_step_id")
                    idx = next((i for i, s in enumerate(steps) if s[0].pk == target_step_id), idx)
                    self._update_state(status="running", error=None, screenshot_base64=None)
                    continue
                elif bp_action == "rerun_from_link":
                    return "JUMP_LINK"
                elif bp_action == "skip":
                    self._create_step_record(execution_record, step, "skipped",
                        {"success": False, "message": "Skipped at breakpoint"}, timezone.now())
                    with self._lock:
                        self._debug_state["completed_steps"].append({
                            "id": step.pk, "order": step.order, "name": step.name,
                            "status": "skipped", "duration_ms": 0,
                        })
                    idx += 1
                    continue
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
            logger.info(f"[DebugExecV2] [{idx+1}/{total_steps}] Step {step.order}: {step.name}{loop_info}")
            result = self._execute_step(step, step_row_data)

            # ── Page awareness snapshot ──
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
                    logger.debug(f"[PageState] Debug capture failed: {pa_err}")

            if result["success"]:
                # Post-fill verification for repeat groups
                if step.action_type == "fill" and step.repeat_group and step.locator and loop_ctx:
                    fill_value = step.get_value(step_row_data, self.context_vars)
                    if fill_value:
                        self._verify_and_retry_fill(step, fill_value)

                # ┌─────────────────────────────────────────────────────┐
                # │  V2 ADDITION: Post-step verification               │
                # └─────────────────────────────────────────────────────┘
                verify_result = self._run_verification(step, step_row_data)

                if verify_result and not verify_result.get("success") and not verify_result.get("skipped"):
                    # Verification failed — treat like a step failure
                    logger.warning(
                        f"[DebugExecV2] Verification FAILED for step {step.order}: "
                        f"{verify_result['message']}"
                    )

                    # If COE, log and continue
                    if step.continue_on_error:
                        self._create_step_record(execution_record, step, "success", result, step_started)
                        completed_entry = {
                            "id": step.pk, "order": step.order, "name": step.name,
                            "status": "verify_failed",
                            "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                            "verify_result": verify_result,
                        }
                        with self._lock:
                            self._debug_state["completed_steps"].append(completed_entry)
                        idx += 1
                        continue

                    # Pause for user — verification failure
                    screenshot_b64 = self._take_screenshot_base64()
                    verify_error = {
                        "step_order": step.order,
                        "step_name": step.name,
                        "message": f"Verification failed: {verify_result['message']}",
                        "error_type": "verification_failed",
                        "verify_type": verify_result.get("verify_type", ""),
                        "verify_duration_ms": verify_result.get("duration_ms", 0),
                    }
                    self._update_state(
                        status="paused",
                        error=verify_error,
                        screenshot_base64=screenshot_b64,
                    )
                    v_action = self._pause_and_process_commands()
                    if v_action == "stop":
                        break
                    elif v_action == "skip":
                        # Accept the step despite verification failure
                        self._create_step_record(execution_record, step, "success", result, step_started)
                        with self._lock:
                            self._debug_state["completed_steps"].append({
                                "id": step.pk, "order": step.order, "name": step.name,
                                "status": "verify_failed",
                                "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                                "verify_result": verify_result,
                            })
                        self._update_state(status="running", error=None, screenshot_base64=None)
                        idx += 1
                        continue
                    elif v_action == "rerun_from_step":
                        target_step_id = self._debug_state.get("_rerun_from_step_id")
                        idx = next((i for i, s in enumerate(steps) if s[0].pk == target_step_id), idx)
                        self._update_state(status="running", error=None, screenshot_base64=None)
                        continue
                    elif v_action == "rerun_from_link":
                        return "JUMP_LINK"
                    elif v_action in ("resume", "dismiss_continue"):
                        # Accept and continue
                        pass
                    self._update_state(status="running", error=None, screenshot_base64=None)

                # ── Record step success ──
                steps_completed += 1
                self._create_step_record(execution_record, step, "success", result, step_started)
                completed_entry = {
                    "id": step.pk, "order": step.order, "name": step.name,
                    "status": "success",
                    "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                }
                # Include verification info in completed_steps
                if verify_result and not verify_result.get("skipped"):
                    completed_entry["verify_result"] = {
                        "type": verify_result.get("verify_type", ""),
                        "success": verify_result.get("success", True),
                        "message": verify_result.get("message", ""),
                        "duration_ms": verify_result.get("duration_ms", 0),
                    }
                with self._lock:
                    self._debug_state["completed_steps"].append(completed_entry)

                # ── Step-by-step mode ──
                with self._lock:
                    sbs_mode = self._debug_state.get("step_by_step_mode", False)
                if sbs_mode:
                    screenshot_b64 = self._take_screenshot_base64()
                    next_step = steps[idx + 1][0] if idx + 1 < len(steps) else None
                    next_info = f"Next: #{next_step.order} {next_step.name}" if next_step else "Last step"
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
                        pass
                    self._update_state(status="running", error=None, screenshot_base64=None)

                idx += 1
                continue

            # ── STEP FAILED ──────────────────────────────────────
            logger.warning(f"[DebugExecV2] Step {step.order} failed: {result['message']}")

            # COE → skip (optionally mark skip_group)
            if step.continue_on_error:
                if step.skip_group:
                    skipped_groups.add(step.skip_group)
                self._create_step_record(execution_record, step, "skipped", result, step_started)
                with self._lock:
                    self._debug_state["completed_steps"].append({
                        "id": step.pk, "order": step.order, "name": step.name,
                        "status": "skipped",
                        "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                    })
                idx += 1
                continue

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

            is_d365_dialog = result.get("error_type") == "d365_dialog"

            # Auto-heal (not for d365 dialogs)
            if step.locator and not is_d365_dialog:
                self._update_state(status="auto_healing", error=error_info)
                healed_result = self._try_auto_heal(step, step_row_data)
                if healed_result and healed_result.get("success"):
                    logger.info(f"[DebugExecV2] Auto-healed step {step.order}!")
                    steps_completed += 1
                    self._create_step_record(execution_record, step, "success", healed_result, step_started)
                    with self._lock:
                        self._debug_state["completed_steps"].append({
                            "id": step.pk, "order": step.order, "name": step.name,
                            "status": "auto_healed",
                            "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                        })
                    idx += 1
                    continue

            # Pause for user
            screenshot_b64 = self._take_screenshot_base64()
            self._update_state(status="paused", error=error_info, screenshot_base64=screenshot_b64)

            action = self._pause_and_process_commands()

            if action == "stop":
                break
            elif action == "rerun_from_step":
                target_step_id = self._debug_state.get("_rerun_from_step_id")
                idx = next((i for i, s in enumerate(steps) if s[0].pk == target_step_id), idx)
                self._update_state(status="running", error=None, screenshot_base64=None)
                continue
            elif action == "rerun_from_link":
                return "JUMP_LINK"
            elif action == "skip":
                self._create_step_record(execution_record, step, "skipped", result, step_started)
                with self._lock:
                    self._debug_state["completed_steps"].append({
                        "id": step.pk, "order": step.order, "name": step.name,
                        "status": "skipped",
                        "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                    })
                idx += 1
                continue
            elif action == "dismiss_continue":
                steps_completed += 1
                self._create_step_record(execution_record, step, "success", result, step_started)
                with self._lock:
                    self._debug_state["completed_steps"].append({
                        "id": step.pk, "order": step.order, "name": step.name,
                        "status": "success",
                        "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                    })
                self._update_state(status="running", error=None, screenshot_base64=None)
                idx += 1
                continue
            elif action == "resume":
                if step.locator:
                    step.locator.refresh_from_db()
                self._update_state(status="running", error=None, screenshot_base64=None)
                retry_result = self._execute_step(step, step_row_data)
                if retry_result["success"]:
                    steps_completed += 1
                    self._create_step_record(execution_record, step, "success", retry_result, step_started)
                    with self._lock:
                        self._debug_state["completed_steps"].append({
                            "id": step.pk, "order": step.order, "name": step.name,
                            "status": "success",
                            "duration_ms": int((timezone.now() - step_started).total_seconds() * 1000),
                        })
                else:
                    screenshot_b64 = self._take_screenshot_base64()
                    error_info["message"] = retry_result.get("message", "Still failing")
                    self._update_state(status="paused", error=error_info, screenshot_base64=screenshot_b64)
                    action2 = self._pause_and_process_commands()
                    if action2 == "stop":
                        break
                    elif action2 == "rerun_from_step":
                        target_step_id = self._debug_state.get("_rerun_from_step_id")
                        idx = next((i for i, s in enumerate(steps) if s[0].pk == target_step_id), idx)
                        self._update_state(status="running", error=None, screenshot_base64=None)
                        continue
                    elif action2 == "rerun_from_link":
                        return "JUMP_LINK"
                    elif action2 == "skip":
                        with self._lock:
                            self._debug_state["completed_steps"].append({
                                "id": step.pk, "order": step.order, "name": step.name,
                                "status": "skipped", "duration_ms": 0,
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
                                    "id": step.pk, "order": step.order, "name": step.name,
                                    "status": "success", "duration_ms": 0,
                                })
                        else:
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

            idx += 1

        # ── Workflow complete ─────────────────────────────────────
        if self.should_stop:
            if not in_chain_mode:
                self._update_state(status="stopped")
            if execution_record:
                execution_record.status = "cancelled"
                execution_record.completed_at = timezone.now()
                execution_record.save()
        else:
            if not in_chain_mode:
                self._update_state(status="completed")
            if execution_record:
                execution_record.status = "success"
                execution_record.completed_at = timezone.now()
                execution_record.context = self.context_vars
                execution_record.save()

    # ══════════════════════════════════════════════════════════════════════
    # Verification helper
    # ══════════════════════════════════════════════════════════════════════

    def _run_verification(self, step, row_data):
        """Run post-step verification with auto-retry.

        On failure:
          1. Wait 1.5s → re-verify (D365 may still be rendering)
          2. Wait 2.5s → re-verify
          3. Re-execute the step → wait 1s → re-verify
          4. Return failure (caller handles pause/skip)
        """
        if not step.verify_type:
            return None

        verifier = self._get_verifier()
        if not verifier:
            return {"success": False, "skipped": False, "message": "No verifier available (no page)"}

        # Attempt 1: immediate verify
        result = verifier.verify(step, row_data=row_data, context=self.context_vars)
        if result.get("success") or result.get("skipped"):
            return result

        logger.info(f"[VerifyRetry] Attempt 1 failed: {result.get('message')} — retrying...")

        # Attempt 2: wait 1.5s → re-verify
        if self.page:
            self.page.wait_for_timeout(1500)
        result = verifier.verify(step, row_data=row_data, context=self.context_vars)
        if result.get("success"):
            logger.info("[VerifyRetry] Attempt 2 passed after 1.5s wait")
            return result

        logger.info(f"[VerifyRetry] Attempt 2 failed: {result.get('message')} — retrying...")

        # Attempt 3: wait 2.5s → re-verify
        if self.page:
            self.page.wait_for_timeout(2500)
        result = verifier.verify(step, row_data=row_data, context=self.context_vars)
        if result.get("success"):
            logger.info("[VerifyRetry] Attempt 3 passed after 2.5s wait")
            return result

        logger.info(f"[VerifyRetry] Attempt 3 failed: {result.get('message')} — re-executing step...")

        # Attempt 4: re-execute the step, then re-verify
        retry_result = self._execute_step(step, row_data)
        if retry_result.get("success"):
            if self.page:
                self.page.wait_for_timeout(1000)
            result = verifier.verify(step, row_data=row_data, context=self.context_vars)
            if result.get("success"):
                logger.info("[VerifyRetry] Attempt 4 passed after re-execution")
                return result
            logger.warning(f"[VerifyRetry] Re-executed OK but verify still failed: {result.get('message')}")
        else:
            logger.warning(f"[VerifyRetry] Re-execution also failed: {retry_result.get('message')}")
            result["message"] = f"Re-execution failed: {retry_result.get('message')}"

        # All retries exhausted — return failure
        result["retry_exhausted"] = True
        return result
