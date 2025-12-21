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
        # Get the 'next' URL from query params or referrer
        next_url = request.GET.get("next") or request.META.get("HTTP_REFERER", "")
        return render(request, "erp_automation/credentials.html", {
            "has_credentials": has_credentials,
            "next_url": next_url,
        })

    def post(self, request):
        action = request.POST.get("action")
        next_url = request.POST.get("next", "")

        if action == "save":
            username = request.POST.get("username", "").strip()
            password = request.POST.get("password", "").strip()
            erp_url = request.POST.get("erp_url", "").strip()

            if username and password:
                # Store in session (encrypted in production)
                request.session["erp_credentials"] = {
                    "username": username,
                    "password": password,
                    "erp_url": erp_url,
                }
                request.session.modified = True
                messages.success(request, "Credentials saved for this session.")
            else:
                messages.error(request, "Please provide both username and password.")

        elif action == "clear":
            request.session.pop("erp_credentials", None)
            messages.info(request, "Credentials cleared.")

        # Redirect to next URL if provided, otherwise dashboard
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect("erp_automation:dashboard")


def get_credentials(request):
    """Helper to get credentials from session."""
    return request.session.get("erp_credentials")


@login_required
@require_POST
def clear_credentials(request):
    """Clear ERP credentials from session."""
    request.session.pop("erp_credentials", None)
    messages.info(request, "Credentials cleared.")
    return redirect("erp_automation:dashboard")


def check_browser(request):
    """Check if Playwright browser is installed and working (public endpoint)."""
    import glob

    status = {
        "playwright_installed": False,
        "playwright_version": None,
        "browser_available": False,
        "error": None,
        "install_command": "playwright install",
    }

    def find_browser_executable():
        """Find any available Chromium browser in Playwright cache."""
        cache_paths = [
            os.path.expanduser("~/.cache/ms-playwright"),
            "/root/.cache/ms-playwright",
            os.path.expanduser("~/Library/Caches/ms-playwright"),
        ]
        for cache_path in cache_paths:
            if not os.path.exists(cache_path):
                continue
            chromium_dirs = sorted(
                glob.glob(os.path.join(cache_path, "chromium-*")),
                reverse=True
            )
            for chromium_dir in chromium_dirs:
                chrome_linux = os.path.join(chromium_dir, "chrome-linux", "chrome")
                if os.path.exists(chrome_linux):
                    return chrome_linux
                chrome_mac = os.path.join(
                    chromium_dir, "chrome-mac", "Chromium.app",
                    "Contents", "MacOS", "Chromium"
                )
                if os.path.exists(chrome_mac):
                    return chrome_mac
                chrome_win = os.path.join(chromium_dir, "chrome-win", "chrome.exe")
                if os.path.exists(chrome_win):
                    return chrome_win
        return None

    try:
        import playwright
        from playwright.sync_api import sync_playwright
        status["playwright_installed"] = True
        status["playwright_version"] = getattr(playwright, "__version__", "unknown")

        # Try to launch browser - use fallback to cached version if needed
        p = sync_playwright().start()
        try:
            executable_path = find_browser_executable()
            launch_args = {"headless": True}
            if executable_path:
                launch_args["executable_path"] = executable_path

            browser = p.chromium.launch(**launch_args)
            status["browser_available"] = True
            status["browser_version"] = browser.version
            if executable_path:
                status["browser_path"] = executable_path
            browser.close()
        except Exception as e:
            error_msg = str(e)
            status["error"] = error_msg
            # Provide helpful guidance based on error type
            if "Executable doesn't exist" in error_msg:
                status["install_command"] = "playwright install chromium"
            elif "version" in error_msg.lower():
                status["install_command"] = "pip install --upgrade playwright && playwright install"
        finally:
            p.stop()

    except ImportError as e:
        status["error"] = f"Playwright not installed: {e}"
        status["install_command"] = "pip install playwright && playwright install"

    return JsonResponse(status)


def test_browser(request):
    """Test browser by creating a simple page - returns JSON result."""
    import glob

    result = {
        "success": False,
        "message": "",
        "browser_version": None,
    }

    def find_browser_executable():
        cache_paths = [
            os.path.expanduser("~/.cache/ms-playwright"),
            "/root/.cache/ms-playwright",
        ]
        for cache_path in cache_paths:
            if not os.path.exists(cache_path):
                continue
            chromium_dirs = sorted(
                glob.glob(os.path.join(cache_path, "chromium-*")),
                reverse=True
            )
            for chromium_dir in chromium_dirs:
                chrome_linux = os.path.join(chromium_dir, "chrome-linux", "chrome")
                if os.path.exists(chrome_linux):
                    return chrome_linux
        return None

    try:
        from playwright.sync_api import sync_playwright

        exe_path = find_browser_executable()
        if not exe_path:
            result["message"] = "No browser executable found"
            return JsonResponse(result)

        p = sync_playwright().start()
        try:
            browser = p.chromium.launch(
                headless=True,
                executable_path=exe_path,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            result["browser_version"] = browser.version

            context = browser.new_context()
            page = context.new_page()

            # Create a simple test page (no network needed)
            page.set_content("""
                <html>
                <head><title>Playwright Test Page</title></head>
                <body>
                    <h1>Browser is working!</h1>
                    <p>If you can see this, Playwright automation is functional.</p>
                </body>
                </html>
            """)

            # Get page info
            title = page.title()
            h1_text = page.locator("h1").text_content()

            result["success"] = True
            result["message"] = f"Browser working! Version: {browser.version}, Title: {title}, H1: {h1_text}"

            browser.close()

        finally:
            p.stop()

    except Exception as e:
        result["message"] = f"Error: {str(e)}"

    return JsonResponse(result)


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

        # Check headless option
        headless = request.POST.get("headless") == "on"

        # Start execution (simplified - in production use Celery)
        try:
            from .services.executor import WorkflowExecutor
        except ImportError as e:
            messages.error(request, f"Executor service not available: {e}")
            return redirect("erp_automation:workflow_detail", pk=pk)

        global _executor_instance

        try:
            if _executor_instance is None:
                _executor_instance = WorkflowExecutor()

            # Start browser if not already running
            if not _executor_instance.page:
                browser_started = _executor_instance.start_browser(
                    url=workflow.target_url,
                    credentials=credentials,
                    headless=headless
                )
                if not browser_started:
                    messages.error(
                        request,
                        "Failed to start browser. Please ensure Playwright browsers are installed. "
                        "Run 'playwright install' in your terminal."
                    )
                    return redirect("erp_automation:workflow_detail", pk=pk)

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
            failed_count = len(results) - success_count

            if success_count == len(results):
                messages.success(request, f"Execution complete: all {success_count} rows successful!")
            elif success_count > 0:
                messages.warning(
                    request,
                    f"Execution complete: {success_count} successful, {failed_count} failed."
                )
            else:
                # All failed - show error details from first failure
                first_error = next((r.get("message", "Unknown error") for r in results if not r["success"]), "Unknown error")
                messages.error(
                    request,
                    f"Execution failed for all {len(results)} rows. Error: {first_error}"
                )

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Workflow execution error: {e}")
            messages.error(request, f"Execution error: {str(e)}")

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

    def post(self, request):
        """Handle Excel file upload."""
        if "excel_file" not in request.FILES:
            messages.error(request, "No file uploaded")
            return redirect("erp_automation:excel_handler")

        excel_file = request.FILES["excel_file"]
        sheet_name = request.POST.get("sheet_name", "").strip() or 0  # Default to first sheet (index 0)
        has_header = request.POST.get("has_header") == "on"

        # Save temporarily
        temp_path = f"/tmp/erp_automation/{uuid.uuid4()}_{excel_file.name}"
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)

        with open(temp_path, "wb") as f:
            for chunk in excel_file.chunks():
                f.write(chunk)

        try:
            # Read Excel file
            if excel_file.name.endswith('.csv'):
                df = pd.read_csv(temp_path, header=0 if has_header else None)
            else:
                df = pd.read_excel(temp_path, sheet_name=sheet_name, header=0 if has_header else None)

            # Convert to list of dicts
            df = df.fillna("")
            excel_data = df.to_dict("records")
            excel_columns = [str(col) for col in df.columns]

            # Store in session
            request.session["excel_data"] = excel_data
            request.session["excel_columns"] = excel_columns
            request.session["excel_file_path"] = temp_path

            messages.success(request, f"Loaded {len(excel_data)} rows from {excel_file.name}")

        except Exception as e:
            messages.error(request, f"Error reading file: {str(e)}")

        return redirect("erp_automation:excel_handler")


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


# =============================================================================
# FIELD MAPPINGS
# =============================================================================

class FieldMappingListView(LoginRequiredMixin, View):
    """List and manage field mappings."""

    def get(self, request):
        workflow_filter = request.GET.get("workflow")
        mappings = FieldMapping.objects.select_related("workflow", "locator").order_by("workflow__name", "excel_column")

        if workflow_filter:
            mappings = mappings.filter(workflow_id=workflow_filter)

        return render(request, "erp_automation/field_mapping_list.html", {
            "mappings": mappings,
            "workflows": Workflow.objects.all().order_by("name"),
            "selected_workflow": int(workflow_filter) if workflow_filter else None,
        })


class FieldMappingFormView(LoginRequiredMixin, View):
    """Add or edit a field mapping."""

    def get(self, request, pk=None):
        if pk:
            mapping = get_object_or_404(FieldMapping, pk=pk)
        else:
            mapping = FieldMapping()

        return render(request, "erp_automation/field_mapping_form.html", {
            "form": {"instance": mapping},
            "workflows": Workflow.objects.all().order_by("name"),
            "locators": Locator.objects.all().order_by("name"),
            "excel_columns": request.session.get("excel_columns", []),
        })

    def post(self, request, pk=None):
        if pk:
            mapping = get_object_or_404(FieldMapping, pk=pk)
        else:
            mapping = FieldMapping()

        # Update fields
        workflow_id = request.POST.get("workflow")
        if workflow_id:
            mapping.workflow_id = int(workflow_id)

        mapping.excel_column = request.POST.get("excel_column", "").strip()
        mapping.erp_field = request.POST.get("erp_field", "").strip()

        locator_id = request.POST.get("locator")
        mapping.locator_id = int(locator_id) if locator_id else None

        mapping.transform_function = request.POST.get("transform_function", "")
        mapping.default_value = request.POST.get("default_value", "")
        mapping.is_required = request.POST.get("is_required") == "on"
        mapping.is_active = request.POST.get("is_active") == "on"

        try:
            mapping.save()
            messages.success(request, f"Field mapping {'updated' if pk else 'created'} successfully.")
            return redirect("erp_automation:field_mapping_list")
        except Exception as e:
            messages.error(request, f"Error saving mapping: {str(e)}")
            return render(request, "erp_automation/field_mapping_form.html", {
                "form": {"instance": mapping},
                "workflows": Workflow.objects.all().order_by("name"),
                "locators": Locator.objects.all().order_by("name"),
                "excel_columns": request.session.get("excel_columns", []),
            })


class FieldMappingDeleteView(LoginRequiredMixin, View):
    """Delete a field mapping."""

    def get(self, request, pk):
        mapping = get_object_or_404(FieldMapping, pk=pk)
        mapping.delete()
        messages.success(request, "Field mapping deleted.")
        return redirect("erp_automation:field_mapping_list")


# =============================================================================
# SELECT ROWS FOR EXECUTION
# =============================================================================

@login_required
@require_POST
def select_rows_for_execution(request):
    """Store selected rows in session for workflow execution."""
    try:
        data = json.loads(request.body)
        selected_indices = data.get("selected_indices", [])

        excel_data = request.session.get("excel_data", [])

        # Get selected rows
        selected_rows = []
        for idx in selected_indices:
            if 0 <= idx < len(excel_data):
                row = excel_data[idx].copy()
                row["__row_index__"] = idx + 1
                selected_rows.append(row)

        request.session["selected_excel_data"] = selected_rows
        request.session.modified = True  # Ensure session is saved

        return JsonResponse({
            "success": True,
            "selected_count": len(selected_rows),
            "message": f"{len(selected_rows)} rows selected for execution"
        })
    except json.JSONDecodeError as e:
        return JsonResponse({"success": False, "message": f"Invalid JSON: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Error: {str(e)}"}, status=500)
