"""
Views V2 — Enhanced views for step verification and start-from-link features.

These views render v2 templates and use DebugExecutorV2. They coexist with
the original views.py — the original chain/workflow detail pages are untouched.

URL patterns:
  /erp-automation/v2/workflows/<pk>/          → WorkflowDetailV2View
  /erp-automation/v2/chains/<pk>/             → ChainDetailV2View
  /erp-automation/v2/api/start-debug/<pk>/    → api_start_debug_chain_v2
  /erp-automation/v2/api/workflows/<pk>/steps/ → api_workflow_steps_v2
  /erp-automation/v2/api/workflows/<pk>/steps/create/ → api_step_create_v2
  /erp-automation/v2/api/workflows/<pk>/steps/<pk>/update/ → api_step_update_v2
"""

import json
import time
import logging
import threading

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import DetailView

from .models import (
    Workflow, WorkflowStep, WorkflowChain, WorkflowChainLink,
    WorkflowStatus, ChainExecution, ExecutionStatus, ERPJobData,
    ERPEnvironment, Locator,
)

logger = logging.getLogger(__name__)

# Module-level executor reference (shared with views.py debug state)
# We reuse the same _debug_executor from the main views module
from . import views as _main_views


# ══════════════════════════════════════════════════════════════════════════
# V2 Detail Views — render v2 templates with verification columns
# ══════════════════════════════════════════════════════════════════════════

class WorkflowDetailV2View(LoginRequiredMixin, DetailView):
    model = Workflow
    template_name = "erp_automation/workflow_detail_v2.html"
    context_object_name = "workflow"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["steps"] = self.object.steps.filter(is_active=True).order_by("order")
        context["executions"] = self.object.executions.order_by("-started_at")[:20]
        return context


class ChainDetailV2View(LoginRequiredMixin, DetailView):
    """Chain detail V2 — same as original + start-from-link + verify columns."""
    model = WorkflowChain
    template_name = "erp_automation/chain_detail_v2.html"
    context_object_name = "chain"

    def _serialize_step(self, s):
        """Serialize a WorkflowStep for JSON — includes verification fields."""
        loc_data = None
        if s.locator:
            loc_data = {
                "id": s.locator.pk,
                "name": s.locator.name,
                "strategies": [
                    {"type": st.strategy_type, "value": st.value, "priority": st.priority,
                     "success": st.success_count, "fail": st.failure_count}
                    for st in s.locator.strategies.all().order_by("priority")
                ],
            }

        # V2: verify locator
        verify_loc_data = None
        if s.verify_locator:
            verify_loc_data = {
                "id": s.verify_locator.pk,
                "name": s.verify_locator.name,
            }

        return {
            "id": s.pk,
            "order": s.order,
            "name": s.name,
            "action_type": s.action_type,
            "locator": loc_data,
            "value_static": s.value_static,
            "value_field": s.value_field,
            "value_template": s.value_template,
            "condition_value": s.condition_value,
            "wait_after": s.wait_after,
            "timeout": s.timeout,
            "continue_on_error": s.continue_on_error,
            "check_for_errors": s.check_for_errors,
            "press_key_after": s.press_key_after,
            "clear_before_fill": s.clear_before_fill,
            "interaction_mode": s.interaction_mode or "auto",
            "repeat_group": s.repeat_group or "",
            "repeat_data_source": s.repeat_data_source or "",
            "skip_group": s.skip_group or "",
            # V2: verification fields
            "verify_type": s.verify_type or "",
            "verify_locator": verify_loc_data,
            "verify_value": s.verify_value or "",
            "verify_timeout": s.verify_timeout or 3000,
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        chain = self.object
        links = chain.links.filter(is_active=True).select_related("workflow").order_by("order")
        ctx["links"] = links
        ctx["recent_executions"] = chain.executions.order_by("-started_at")[:20]
        ctx["available_workflows"] = Workflow.objects.filter(
            status=WorkflowStatus.ACTIVE
        ).order_by("name")

        # Build segments JSON with steps (including verify fields)
        segments = []
        for link in links:
            steps = list(
                link.workflow.steps
                .filter(is_active=True)
                .order_by("order")
                .select_related("locator", "verify_locator")
                .prefetch_related("locator__strategies")
            )
            segments.append({
                "link_id": link.pk,
                "link_order": link.order,
                "workflow_id": link.workflow_id,
                "workflow_name": link.workflow.name,
                "link_name": link.name,
                "condition_field": link.condition_field,
                "condition_value": link.condition_value,
                "wait_before_ms": link.wait_before_ms,
                "navigate_url": link.navigate_url or "",
                "is_active": link.is_active,
                "steps": [self._serialize_step(s) for s in steps],
            })
        ctx["segments_json"] = json.dumps(segments)
        ctx["chain_json"] = json.dumps({
            "id": chain.pk,
            "name": chain.name,
            "status": chain.status,
            "description": chain.description,
            "condition_field": chain.condition_field,
            "stop_on_failure": chain.stop_on_failure,
            "keep_browser_open": chain.keep_browser_open,
        })

        # V2: Build start-from-link options
        # For each link, collect what context variables it produces (save_result_as)
        start_from_options = []
        produced_vars_so_far = []
        for link in links:
            link_vars = []
            for s in link.workflow.steps.filter(is_active=True, save_result_as__gt=''):
                link_vars.append(s.save_result_as)
            start_from_options.append({
                "order": link.order,
                "name": link.get_display_name(),
                "workflow_name": link.workflow.name,
                "produces": link_vars,
                "requires": list(produced_vars_so_far),  # vars from prior links
            })
            produced_vars_so_far.extend(link_vars)
        ctx["start_from_options_json"] = json.dumps(start_from_options)

        # Debug mode params (same as original)
        debug_exec_id = self.request.GET.get("debug")
        if debug_exec_id:
            try:
                debug_exec = ChainExecution.objects.select_related("job_data").get(pk=int(debug_exec_id))
                ctx["debug_execution_id"] = debug_exec.pk
                if debug_exec.job_data:
                    ctx["debug_job_data_pk"] = debug_exec.job_data.pk
            except (ChainExecution.DoesNotExist, ValueError):
                pass

        start_debug_job_pk = self.request.GET.get("start_debug")
        if start_debug_job_pk:
            try:
                job_pk = int(start_debug_job_pk)
                ctx["start_debug_job_pk"] = job_pk
                if "debug_job_data_pk" not in ctx:
                    ctx["debug_job_data_pk"] = job_pk
            except (ValueError, TypeError):
                pass

        batch_jobs_param = self.request.GET.get("batch_jobs", "")
        if batch_jobs_param:
            try:
                batch_pks = [int(x) for x in batch_jobs_param.split(",") if x.strip().isdigit()]
                if batch_pks:
                    ctx["batch_job_pks_json"] = json.dumps(batch_pks)
            except (ValueError, TypeError):
                pass

        # Start-from link order from URL param
        start_from_param = self.request.GET.get("start_from_link")
        if start_from_param:
            try:
                ctx["start_from_link_order"] = int(start_from_param)
            except (ValueError, TypeError):
                pass

        ctx["has_credentials"] = "erp_credentials" in self.request.session
        environments = ERPEnvironment.objects.all().order_by("-is_default", "name")
        ctx["environments_json"] = json.dumps([
            {"id": e.pk, "name": e.name, "url": e.url, "is_default": e.is_default}
            for e in environments
        ])

        return ctx


# ══════════════════════════════════════════════════════════════════════════
# V2 API Endpoints
# ══════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def api_start_debug_chain_v2(request, pk):
    """Start chain execution with V2 executor (verification + start-from-link).

    POST JSON: {
        "chain_id": int,
        "job_ids": [int, ...],       // optional batch
        "start_from_link_order": int, // optional — skip links before this
        "initial_context": {          // optional — pre-fill context vars
            "ITEM_NO": "RPR-0042",
            "JOURNAL_NUMBER": "MVT-0891"
        }
    }
    """
    from .services.executor_v2 import DebugExecutorV2

    try:
        job_data = ERPJobData.objects.get(pk=pk)
    except ERPJobData.DoesNotExist:
        return JsonResponse({"success": False, "message": "Job data not found"}, status=404)

    if job_data.status not in ('READY', 'ERROR', 'SENT'):
        return JsonResponse({"success": False, "message": f"Job status must be READY, ERROR or SENT (got {job_data.status})"}, status=400)

    # Deduplication guard
    now = time.time()
    last = getattr(_main_views, '_last_chain_debug_time', 0)
    if now - last < 5:
        return JsonResponse({"success": False, "message": "Debug already starting, please wait..."}, status=429)
    _main_views._last_chain_debug_time = now

    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    chain_id = body.get("chain_id")
    if not chain_id:
        return JsonResponse({"success": False, "message": "chain_id required"}, status=400)

    try:
        chain = WorkflowChain.objects.get(pk=chain_id)
    except WorkflowChain.DoesNotExist:
        return JsonResponse({"success": False, "message": "Chain not found"}, status=404)

    if chain.status != 'active':
        return JsonResponse({"success": False, "message": "Chain is not active"}, status=400)

    # V2: Extract start-from params
    start_from_link_order = body.get("start_from_link_order")
    initial_context = body.get("initial_context") or {}

    # Batch job IDs
    extra_job_ids = body.get("job_ids", [])
    job_data_list = [job_data]
    if extra_job_ids:
        for jid in extra_job_ids:
            if jid == job_data.pk:
                continue
            try:
                extra_job = ERPJobData.objects.get(pk=jid)
                if extra_job.status in ('READY', 'ERROR', 'SENT'):
                    job_data_list.append(extra_job)
            except ERPJobData.DoesNotExist:
                pass

    batch_mode = len(job_data_list) > 1

    # Get credentials
    credentials = request.session.get("erp_credentials")
    if not credentials:
        return JsonResponse({"success": False, "message": "ERP credentials not set"}, status=400)

    # Create chain execution
    chain_execution = ChainExecution.objects.create(
        chain=chain,
        job_data=job_data,
        status=ExecutionStatus.PENDING,
        total_links=chain.links.filter(is_active=True).count(),
        row_data=job_data.get_row_data(),
        executed_by=request.user,
    )

    # Determine ERP URL
    first_link = chain.links.filter(is_active=True).order_by("order").first()
    erp_url = ""
    if first_link and first_link.workflow.target_url:
        erp_url = first_link.workflow.target_url

    # Create V2 executor
    executor = DebugExecutorV2()
    _main_views._debug_executor = executor

    def _v2_thread():
        try:
            executor.start_debug_chain(
                chain=chain,
                job_data=job_data,
                chain_execution=chain_execution,
                credentials=credentials,
                erp_url=erp_url,
                job_data_list=job_data_list if batch_mode else None,
                start_from_link_order=start_from_link_order,
                initial_context=initial_context if initial_context else None,
            )
        except Exception as e:
            logger.exception(f"[V2 Thread] Fatal error: {e}")
        finally:
            executor.is_running = False

    thread = threading.Thread(target=_v2_thread, daemon=True)
    thread.start()

    # Wait for browser to be ready
    if not executor.ready_event.wait(timeout=90):
        return JsonResponse({"success": False, "message": "Browser failed to start within 90s"}, status=500)

    return JsonResponse({
        "success": True,
        "chain_execution_id": chain_execution.pk,
        "batch_mode": batch_mode,
        "batch_total": len(job_data_list),
        "start_from_link_order": start_from_link_order,
        "redirect": f"/erp-automation/v2/chains/{chain.pk}/?debug={chain_execution.pk}",
        "message": f"V2 debug started for chain '{chain.name}'",
    })


@login_required
@require_GET
def api_workflow_steps_v2(request, wf_pk):
    """Get all steps for a workflow as JSON — includes verification fields."""
    try:
        wf = Workflow.objects.get(pk=wf_pk)
    except Workflow.DoesNotExist:
        return JsonResponse({"error": "Workflow not found"}, status=404)

    steps = (
        wf.steps.filter(is_active=True)
        .order_by("order")
        .select_related("locator", "verify_locator")
        .prefetch_related("locator__strategies")
    )

    result = []
    for s in steps:
        loc_data = None
        if s.locator:
            loc_data = {
                "id": s.locator.pk,
                "name": s.locator.name,
                "strategies": [
                    {"type": st.strategy_type, "value": st.value, "priority": st.priority,
                     "success": st.success_count, "fail": st.failure_count}
                    for st in s.locator.strategies.all().order_by("priority")
                ],
            }

        verify_loc_data = None
        if s.verify_locator:
            verify_loc_data = {
                "id": s.verify_locator.pk,
                "name": s.verify_locator.name,
            }

        result.append({
            "id": s.pk,
            "order": s.order,
            "name": s.name,
            "action_type": s.action_type,
            "locator": loc_data,
            "value_static": s.value_static,
            "value_field": s.value_field,
            "value_template": s.value_template,
            "condition_value": s.condition_value,
            "wait_after": s.wait_after,
            "timeout": s.timeout,
            "continue_on_error": s.continue_on_error,
            "check_for_errors": s.check_for_errors,
            "press_key_after": s.press_key_after,
            "clear_before_fill": s.clear_before_fill,
            "interaction_mode": s.interaction_mode or "auto",
            "repeat_group": s.repeat_group or "",
            "repeat_data_source": s.repeat_data_source or "",
            "skip_group": s.skip_group or "",
            # V2
            "verify_type": s.verify_type or "",
            "verify_locator": verify_loc_data,
            "verify_value": s.verify_value or "",
            "verify_timeout": s.verify_timeout or 3000,
        })

    return JsonResponse({"steps": result})


@login_required
@require_POST
def api_step_create_v2(request, wf_pk):
    """Create a new workflow step — includes verification fields."""
    try:
        wf = Workflow.objects.get(pk=wf_pk)
    except Workflow.DoesNotExist:
        return JsonResponse({"error": "Workflow not found"}, status=404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Determine order
    order = data.get("order")
    if order is None:
        last = wf.steps.filter(is_active=True).order_by("-order").first()
        order = (last.order + 1) if last else 1
    else:
        order = int(order)

    # Shift existing steps if needed
    existing = wf.steps.filter(order__gte=order, is_active=True).order_by("-order")
    for s in existing:
        s.order = s.order + 1
        s.save(update_fields=["order"])

    # Resolve locator
    locator = None
    loc_id = data.get("locator_id")
    loc_name = data.get("locator_name")
    if loc_id:
        try:
            locator = Locator.objects.get(pk=int(loc_id))
        except Locator.DoesNotExist:
            pass
    elif loc_name:
        locator, _ = Locator.objects.get_or_create(name=loc_name)

    # Resolve verify locator
    verify_locator = None
    vloc_id = data.get("verify_locator_id")
    if vloc_id:
        try:
            verify_locator = Locator.objects.get(pk=int(vloc_id))
        except Locator.DoesNotExist:
            pass

    step = WorkflowStep.objects.create(
        workflow=wf,
        order=order,
        name=data.get("name") or f"Step {order}",
        action_type=data.get("action_type") or "click",
        locator=locator,
        value_static=data.get("value_static") or "",
        value_field=data.get("value_field") or "",
        value_template=data.get("value_template") or "",
        condition_value=data.get("condition_value") or "",
        wait_after=int(data.get("wait_after") or 500),
        timeout=int(data.get("timeout") or 30000),
        continue_on_error=bool(data.get("continue_on_error")),
        check_for_errors=bool(data.get("check_for_errors")),
        press_key_after=data.get("press_key_after") or "",
        clear_before_fill=bool(data.get("clear_before_fill")),
        interaction_mode=data.get("interaction_mode") or "auto",
        repeat_group=data.get("repeat_group") or "",
        repeat_data_source=data.get("repeat_data_source") or "",
        skip_group=data.get("skip_group") or "",
        # V2
        verify_type=data.get("verify_type") or "",
        verify_locator=verify_locator,
        verify_value=data.get("verify_value") or "",
        verify_timeout=int(data.get("verify_timeout") or 3000),
    )

    # Renumber all steps
    all_steps = list(wf.steps.filter(is_active=True).order_by("order"))
    for i, s in enumerate(all_steps, start=1):
        if s.order != i:
            s.order = i
            s.save(update_fields=["order"])

    return JsonResponse({
        "success": True,
        "step_id": step.pk,
        "message": f"Step {step.order} created",
    })


@login_required
@require_POST
def api_step_update_v2(request, wf_pk, step_pk):
    """Update a workflow step — includes verification fields."""
    try:
        step = WorkflowStep.objects.get(pk=step_pk, workflow_id=wf_pk)
    except WorkflowStep.DoesNotExist:
        return JsonResponse({"error": "Step not found"}, status=404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Snapshot old data
    old_data = {
        "order": step.order, "name": step.name,
        "action_type": step.action_type,
        "verify_type": step.verify_type,
    }

    # String fields
    for field in [
        "name", "action_type", "value_static", "value_field", "value_template",
        "condition_value", "press_key_after", "interaction_mode",
        "repeat_group", "repeat_data_source", "skip_group",
        # V2
        "verify_type", "verify_value",
    ]:
        if field in data:
            setattr(step, field, data[field] or "")

    # Int fields
    for field in ["order", "wait_after", "timeout", "verify_timeout"]:
        if field in data:
            try:
                setattr(step, field, int(data[field]))
            except (ValueError, TypeError):
                pass

    # Bool fields
    for field in ["continue_on_error", "check_for_errors", "clear_before_fill", "is_active"]:
        if field in data:
            setattr(step, field, bool(data[field]))

    # Locator
    if "locator_id" in data:
        if data["locator_id"]:
            try:
                step.locator = Locator.objects.get(pk=int(data["locator_id"]))
            except Locator.DoesNotExist:
                pass
        else:
            step.locator = None

    # V2: Verify locator
    if "verify_locator_id" in data:
        if data["verify_locator_id"]:
            try:
                step.verify_locator = Locator.objects.get(pk=int(data["verify_locator_id"]))
            except Locator.DoesNotExist:
                pass
        else:
            step.verify_locator = None

    step.save()

    return JsonResponse({
        "success": True,
        "old_data": old_data,
        "message": f"Step {step.order} updated",
    })
