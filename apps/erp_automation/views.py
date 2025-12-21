"""
ERP Automation Views

Views for workflow management, recording, and execution.
"""
import os
import json
import uuid
import pandas as pd
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings

from .models import (
    Workflow, WorkflowStep, Locator, LocatorStrategy,
    RecordingSession, RecordedAction,
    WorkflowExecution, ItemCounter, FieldMapping, WorkflowStatus
)

# Global recorder instance (per-process, for development)
# In production, use Celery or similar for background tasks
_recorder_instance = None
_executor_instance = None


# =============================================================================
# DASHBOARD
# =============================================================================

class DashboardView(LoginRequiredMixin, View):
    """Main dashboard showing overview of automation system."""

    def get(self, request):
        context = {
            "workflow_count": Workflow.objects.filter(status="active").count(),
            "locator_count": Locator.objects.count(),
            "recent_executions": WorkflowExecution.objects.order_by("-started_at")[:10],
            "item_counters": ItemCounter.objects.all(),
            "has_credentials": "erp_credentials" in request.session,
        }
        return render(request, "erp_automation/dashboard.html", context)


# =============================================================================
# CREDENTIALS
# =============================================================================

class CredentialsView(LoginRequiredMixin, View):
    """Handle ERP credentials for the session."""

    def get(self, request):
        has_credentials = "erp_credentials" in request.session
        return render(request, "erp_automation/credentials.html", {
            "has_credentials": has_credentials
        })

    def post(self, request):
        action = request.POST.get("action")

        if action == "save":
            username = request.POST.get("username", "").strip()
            password = request.POST.get("password", "").strip()

            if username and password:
                # Store in session (encrypted in production)
                request.session["erp_credentials"] = {
                    "username": username,
                    "password": password,
                }
                messages.success(request, "Credentials saved for this session.")
            else:
                messages.error(request, "Please provide both username and password.")

        elif action == "clear":
            request.session.pop("erp_credentials", None)
            messages.info(request, "Credentials cleared.")

        return redirect("erp_automation:dashboard")


def get_credentials(request):
    """Helper to get credentials from session."""
    return request.session.get("erp_credentials")


# =============================================================================
# WORKFLOWS
# =============================================================================

class WorkflowListView(LoginRequiredMixin, ListView):
    model = Workflow
    template_name = "erp_automation/workflow_list.html"
    context_object_name = "workflows"

    def get_queryset(self):
        return Workflow.objects.all().order_by("name")


class WorkflowDetailView(LoginRequiredMixin, DetailView):
    model = Workflow
    template_name = "erp_automation/workflow_detail.html"
    context_object_name = "workflow"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["steps"] = self.object.steps.filter(is_active=True).order_by("order")
        context["executions"] = self.object.executions.order_by("-started_at")[:20]
        return context


class WorkflowExecuteView(LoginRequiredMixin, View):
    """View for executing a workflow with Excel data."""

    def get(self, request, pk):
        workflow = get_object_or_404(Workflow, pk=pk)
        selected_data = request.session.get("selected_excel_data", [])
        has_credentials = "erp_credentials" in request.session

        return render(request, "erp_automation/workflow_execute.html", {
            "workflow": workflow,
            "selected_data": selected_data,
            "has_credentials": has_credentials,
        })

    def post(self, request, pk):
        workflow = get_object_or_404(Workflow, pk=pk)
        credentials = get_credentials(request)

        if not credentials:
            messages.error(request, "Please set your ERP credentials first.")
            return redirect("erp_automation:credentials")

        # Get selected rows from session
        selected_data = request.session.get("selected_excel_data", [])
        if not selected_data:
            messages.warning(request, "No Excel rows selected. Please select data first.")
            return redirect("erp_automation:excel_handler")

        # Start execution (simplified - in production use Celery)
        from .services.executor import WorkflowExecutor

        global _executor_instance
        if _executor_instance is None:
            _executor_instance = WorkflowExecutor()

        # Start browser
        if not _executor_instance.page:
            _executor_instance.start_browser(
                url=workflow.target_url,
                credentials=credentials,
                headless=False
            )

        # Execute for each row
        results = []
        for row in selected_data:
            execution = WorkflowExecution.objects.create(
                workflow=workflow,
                row_data=row,
                executed_by=request.user
            )
            result = _executor_instance.execute_workflow(workflow, row, execution)
            results.append(result)

        success_count = sum(1 for r in results if r["success"])
        messages.success(
            request,
            f"Execution complete: {success_count}/{len(results)} successful"
        )

        return redirect("erp_automation:workflow_detail", pk=pk)


# =============================================================================
# LOCATORS
# =============================================================================

class LocatorListView(LoginRequiredMixin, ListView):
    model = Locator
    template_name = "erp_automation/locator_list.html"
    context_object_name = "locators"

    def get_queryset(self):
        return Locator.objects.all().order_by("name")


class LocatorDetailView(LoginRequiredMixin, DetailView):
    model = Locator
    template_name = "erp_automation/locator_detail.html"
    context_object_name = "locator"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["strategies"] = self.object.strategies.all().order_by("priority")
        return context


# =============================================================================
# RECORDING
# =============================================================================

class RecordingView(LoginRequiredMixin, View):
    """View for recording browser actions."""

    def get(self, request):
        sessions = RecordingSession.objects.order_by("-started_at")[:10]
        has_credentials = "erp_credentials" in request.session

        return render(request, "erp_automation/recording.html", {
            "sessions": sessions,
            "is_recording": _recorder_instance is not None and _recorder_instance.is_recording,
            "has_credentials": has_credentials,
        })


@login_required
@require_POST
def start_recording(request):
    """Start a new recording session."""
    global _recorder_instance

    from .services.recorder import RecorderService

    url = request.POST.get("url", "").strip()
    session_name = request.POST.get("name", f"Recording {datetime.now()}")
    credentials = get_credentials(request)

    if not url:
        return JsonResponse({"success": False, "message": "URL is required"})

    if not credentials:
        return JsonResponse({"success": False, "message": "Please set credentials first"})

    # Create session record
    session = RecordingSession.objects.create(
        name=session_name,
        target_url=url,
        created_by=request.user
    )

    # Start recorder
    _recorder_instance = RecorderService()
    success = _recorder_instance.start_recording(
        url=url,
        session_id=str(session.id),
        credentials=credentials,
        headless=False
    )

    if success:
        request.session["active_recording_id"] = session.id
        return JsonResponse({
            "success": True,
            "session_id": session.id,
            "message": "Recording started"
        })
    else:
        session.delete()
        return JsonResponse({"success": False, "message": "Failed to start browser"})


@login_required
@require_POST
def stop_recording(request):
    """Stop current recording and save actions."""
    global _recorder_instance

    if _recorder_instance is None:
        return JsonResponse({"success": False, "message": "No active recording"})

    session_id = request.session.get("active_recording_id")
    actions = _recorder_instance.stop_recording()

    # Save actions to database
    if session_id:
        try:
            session = RecordingSession.objects.get(id=session_id)
            session.is_active = False
            session.ended_at = datetime.now()
            session.save()

            for action_data in actions:
                RecordedAction.objects.create(
                    session=session,
                    order=action_data["order"],
                    action_type=action_data["action_type"],
                    element_tag=action_data.get("element_tag", ""),
                    element_id=action_data.get("element_id", ""),
                    element_name=action_data.get("element_name", ""),
                    element_class=action_data.get("element_class", ""),
                    element_xpath=action_data.get("element_xpath", ""),
                    element_css=action_data.get("element_css", ""),
                    element_text=action_data.get("element_text", ""),
                    element_aria_label=action_data.get("element_aria_label", ""),
                    element_placeholder=action_data.get("element_placeholder", ""),
                    element_rect=action_data.get("element_rect", {}),
                    page_url=action_data.get("page_url", ""),
                    page_title=action_data.get("page_title", ""),
                    input_value=action_data.get("input_value", ""),
                    key_pressed=action_data.get("key_pressed", ""),
                )

        except RecordingSession.DoesNotExist:
            pass

    request.session.pop("active_recording_id", None)
    _recorder_instance = None

    return JsonResponse({
        "success": True,
        "action_count": len(actions),
        "message": f"Recording stopped: {len(actions)} actions captured"
    })


@login_required
@require_GET
def poll_recording(request):
    """Poll for new recorded actions (for live updates)."""
    global _recorder_instance

    if _recorder_instance is None or not _recorder_instance.is_recording:
        return JsonResponse({"recording": False, "actions": []})

    new_actions = _recorder_instance.poll_actions()

    return JsonResponse({
        "recording": True,
        "actions": new_actions
    })


# =============================================================================
# EXCEL HANDLER
# =============================================================================

class ExcelHandlerView(LoginRequiredMixin, View):
    """View for handling Excel data."""

    def get(self, request):
        excel_data = request.session.get("excel_data", [])
        excel_columns = request.session.get("excel_columns", [])

        return render(request, "erp_automation/excel_handler.html", {
            "excel_data": excel_data,
            "excel_columns": excel_columns,
            "field_mappings": FieldMapping.objects.select_related('locator').all(),
            "workflows": Workflow.objects.filter(status=WorkflowStatus.ACTIVE),
        })


@login_required
@require_POST
def excel_upload(request):
    """Handle Excel file upload."""
    if "file" not in request.FILES:
        return JsonResponse({"success": False, "message": "No file uploaded"})

    excel_file = request.FILES["file"]

    # Save temporarily
    temp_path = f"/tmp/erp_automation/{uuid.uuid4()}_{excel_file.name}"
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)

    with open(temp_path, "wb") as f:
        for chunk in excel_file.chunks():
            f.write(chunk)

    # Get sheet names
    try:
        xl = pd.ExcelFile(temp_path)
        sheets = xl.sheet_names

        request.session["excel_file_path"] = temp_path

        return JsonResponse({
            "success": True,
            "sheets": sheets,
            "filename": excel_file.name
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


@login_required
@require_POST
def excel_read_sheet(request):
    """Read a specific sheet from uploaded Excel."""
    file_path = request.session.get("excel_file_path")
    sheet_name = request.POST.get("sheet_name")
    rows_to_display = request.POST.get("rows", "all")

    if not file_path or not os.path.exists(file_path):
        return JsonResponse({"success": False, "message": "No Excel file loaded"})

    try:
        nrows = None if rows_to_display == "all" else int(rows_to_display)
        df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=nrows)

        # Convert to records with row numbers
        records = []
        for idx, row in df.iterrows():
            record = row.to_dict()
            record["__excel_row__"] = idx + 2  # Excel 1-based + header
            record["__sheet__"] = sheet_name
            records.append(record)

        return JsonResponse({
            "success": True,
            "columns": list(df.columns),
            "rows": records,
            "total_rows": len(df)
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})


# =============================================================================
# EXECUTION
# =============================================================================

class ExecutionListView(LoginRequiredMixin, ListView):
    model = WorkflowExecution
    template_name = "erp_automation/execution_list.html"
    context_object_name = "executions"
    paginate_by = 50

    def get_queryset(self):
        return WorkflowExecution.objects.order_by("-started_at")


class ExecutionDetailView(LoginRequiredMixin, DetailView):
    model = WorkflowExecution
    template_name = "erp_automation/execution_detail.html"
    context_object_name = "execution"


@login_required
@require_POST
@csrf_exempt
def execute_workflow_api(request):
    """API endpoint for workflow execution."""
    data = json.loads(request.body)

    workflow_id = data.get("workflow_id")
    row_data = data.get("row_data", {})

    try:
        workflow = Workflow.objects.get(id=workflow_id)
    except Workflow.DoesNotExist:
        return JsonResponse({"success": False, "message": "Workflow not found"})

    credentials = get_credentials(request)
    if not credentials:
        return JsonResponse({"success": False, "message": "No credentials"})

    from .services.executor import WorkflowExecutor

    global _executor_instance
    if _executor_instance is None:
        _executor_instance = WorkflowExecutor()
        _executor_instance.start_browser(
            url=workflow.target_url,
            credentials=credentials
        )

    execution = WorkflowExecution.objects.create(
        workflow=workflow,
        row_data=row_data,
        executed_by=request.user
    )

    result = _executor_instance.execute_workflow(workflow, row_data, execution)

    return JsonResponse(result)


# =============================================================================
# API ENDPOINTS
# =============================================================================

@login_required
@require_GET
def api_workflows(request):
    """API: Get all workflows."""
    workflows = Workflow.objects.filter(status="active").values(
        "id", "name", "description", "target_url", "valid_sheets"
    )
    return JsonResponse({"workflows": list(workflows)})


@login_required
@require_GET
def api_locators(request):
    """API: Get all locators."""
    locators = Locator.objects.all().values(
        "id", "name", "description", "application"
    )
    return JsonResponse({"locators": list(locators)})


@login_required
@require_GET
def api_next_item_number(request, account_type):
    """API: Get next item number for an account type."""
    counter, created = ItemCounter.objects.get_or_create(
        account_type=account_type.upper(),
        defaults={"prefix": f"RPR-{account_type.upper()}-"}
    )

    if request.GET.get("increment") == "true":
        number = counter.get_next_number()
    else:
        number = counter.get_next_preview()

    return JsonResponse({
        "account_type": account_type,
        "next_number": number,
        "current_counter": counter.current_number
    })
