"""
ERP Automation Views

Views for workflow management, recording, and execution.
"""
import os
import json
import uuid
import threading
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
from django.db import models
from django.utils import timezone
import logging

from .models import (
    Workflow, WorkflowStep, Locator, LocatorStrategy,
    RecordingSession, RecordedAction,
    WorkflowExecution, ItemCounter, FieldMapping, WorkflowStatus,
    ERPRoute, ERPJobData,
    WorkflowChain, WorkflowChainLink, ChainExecution, ExecutionStatus,
)

# Global instances (per-process, for development)
# In production, use Celery or similar for background tasks
_recorder_instance = None
_executor_instance = None
_debug_executor = None

# Live execution progress tracking (per-execution)
# Maps execution_id -> progress dict
_live_execution_state = {}
_live_execution_lock = threading.Lock()


# =============================================================================
# DASHBOARD
# =============================================================================

class DashboardView(LoginRequiredMixin, View):
    """Main dashboard showing overview of automation system."""

    def get(self, request):
        context = {
            "workflow_count": Workflow.objects.filter(status="active").count(),
            "chain_count": WorkflowChain.objects.filter(status="active").count(),
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
        creds = request.session.get("erp_credentials", {})
        has_credentials = bool(creds)
        # Get the 'next' URL from query params or referrer
        next_url = request.GET.get("next") or request.META.get("HTTP_REFERER", "")
        return render(request, "erp_automation/credentials.html", {
            "has_credentials": has_credentials,
            "current_username": creds.get("username", ""),
            "current_url": creds.get("erp_url", ""),
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

        # Redirect to next URL if provided, otherwise stay on credentials page
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect("erp_automation:credentials")


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


def _find_browser_executable():
    """Find any available Chromium browser in Playwright cache (all platforms)."""
    import glob
    import sys

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
        user_profile = os.environ.get("USERPROFILE", "")
        if user_profile:
            cache_paths.insert(0, os.path.join(user_profile, "AppData", "Local", "ms-playwright"))

    for cache_path in cache_paths:
        if not os.path.exists(cache_path):
            continue
        chromium_dirs = sorted(
            glob.glob(os.path.join(cache_path, "chromium-*")),
            reverse=True
        )
        for chromium_dir in chromium_dirs:
            # Windows
            chrome_win = os.path.join(chromium_dir, "chrome-win", "chrome.exe")
            if os.path.exists(chrome_win):
                return chrome_win
            # Linux
            chrome_linux = os.path.join(chromium_dir, "chrome-linux", "chrome")
            if os.path.exists(chrome_linux):
                return chrome_linux
            # macOS
            chrome_mac = os.path.join(
                chromium_dir, "chrome-mac", "Chromium.app",
                "Contents", "MacOS", "Chromium"
            )
            if os.path.exists(chrome_mac):
                return chrome_mac
    return None


def check_browser(request):
    """Check if Playwright browser is installed and working (public endpoint)."""
    status = {
        "playwright_installed": False,
        "playwright_version": None,
        "browser_available": False,
        "error": None,
        "install_command": "playwright install",
    }

    try:
        import playwright
        from playwright.sync_api import sync_playwright
        status["playwright_installed"] = True
        status["playwright_version"] = getattr(playwright, "__version__", "unknown")

        # Try to launch browser - use fallback to cached version if needed
        p = sync_playwright().start()
        try:
            executable_path = _find_browser_executable()
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
    result = {
        "success": False,
        "message": "",
        "browser_version": None,
    }

    try:
        from playwright.sync_api import sync_playwright

        exe_path = _find_browser_executable()
        launch_args = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-dev-shm-usage"]
        }
        if exe_path:
            launch_args["executable_path"] = exe_path

        p = sync_playwright().start()
        try:
            browser = p.chromium.launch(**launch_args)
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
        job_data_records = ERPJobData.objects.filter(status__in=['READY', 'DRAFT']).order_by('-created_at')

        return render(request, "erp_automation/recording.html", {
            "recent_sessions": sessions,
            "is_recording": _recorder_instance is not None and _recorder_instance.is_recording,
            "has_credentials": has_credentials,
            "job_data_records": job_data_records,
        })


@login_required
@require_POST
def start_recording(request):
    """Start a new recording session."""
    global _recorder_instance

    from .services.recorder import RecorderService

    url = request.POST.get("target_url", "").strip()
    session_name = request.POST.get("session_name", f"Recording {datetime.now()}")
    job_data_id = request.POST.get("job_data_id", "").strip()
    credentials = get_credentials(request)

    if not url:
        return JsonResponse({"success": False, "message": "URL is required"})

    if not credentials:
        return JsonResponse({"success": False, "message": "Please set credentials first"})

    # Ensure URL has protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Link to job data if provided
    job_data = None
    if job_data_id:
        try:
            job_data = ERPJobData.objects.get(pk=int(job_data_id))
        except (ERPJobData.DoesNotExist, ValueError):
            pass

    # Create session record
    session = RecordingSession.objects.create(
        name=session_name,
        target_url=url,
        status='recording',
        created_by=request.user,
        job_data=job_data,
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
        response_data = {
            "success": True,
            "session_id": session.id,
            "message": "Recording started"
        }
        # Include clipboard data if job data is linked
        if job_data:
            response_data["clipboard_data"] = job_data.get_row_data()
        return JsonResponse(response_data)
    else:
        session.delete()
        return JsonResponse({"success": False, "message": "Failed to start browser"})


@csrf_exempt
@require_POST
def stop_recording(request):
    """Stop current recording and save any remaining actions.
    NOTE: No @login_required or CSRF — must always return JSON even if session expired."""
    global _recorder_instance

    if _recorder_instance is None:
        return JsonResponse({"success": False, "message": "No active recording"})

    session_id = request.session.get("active_recording_id")

    # Stop recorder — may fail if browser already closed
    actions = []
    try:
        actions = _recorder_instance.stop_recording()
    except Exception as e:
        logger.warning(f"[stop] Recorder stop failed (browser may be closed): {e}")

    # Save any remaining actions that weren't saved during polling
    saved_count = 0
    total_actions = len(actions)
    if session_id:
        try:
            session = RecordingSession.objects.get(id=session_id)
            session.is_active = False
            session.status = 'completed'
            session.ended_at = timezone.now()
            session.save()

            # Get existing action orders to avoid duplicates (poll already saves actions)
            existing_orders = set(
                session.actions.values_list('order', flat=True)
            )

            for action_data in actions:
                order = action_data["order"]
                if order not in existing_orders:
                    RecordedAction.objects.create(
                        session=session,
                        order=order,
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
                        element_role=action_data.get("element_role", ""),
                        element_type=action_data.get("element_type", ""),
                        element_dyn_control_name=action_data.get("element_dyn_control_name", ""),
                        element_data_testid=action_data.get("element_data_testid", ""),
                        element_rect=action_data.get("element_rect", {}),
                        page_url=action_data.get("page_url", ""),
                        page_title=action_data.get("page_title", ""),
                        input_value=action_data.get("input_value", ""),
                        key_pressed=action_data.get("key_pressed", ""),
                        locator_strategies=action_data.get("locator_strategies", []),
                    )
                    saved_count += 1

            total_actions = session.actions.count()
            logger.info(f"[stop] Session #{session_id}: saved {saved_count} remaining, {total_actions} total actions")

        except RecordingSession.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"[stop] Error saving session #{session_id}: {e}")

    request.session.pop("active_recording_id", None)
    _recorder_instance = None

    return JsonResponse({
        "success": True,
        "action_count": total_actions,
        "session_id": session_id,
        "message": f"Recording stopped: {total_actions} actions captured"
    })


@require_GET
def poll_recording(request):
    """Poll for new recorded actions (for live updates).
    NOTE: No @login_required — returns JSON even if session expired.

    Also saves new actions to DB immediately so they aren't lost.
    """
    global _recorder_instance

    if _recorder_instance is None or not _recorder_instance.is_recording:
        return JsonResponse({"recording": False, "actions": []})

    try:
        new_actions = _recorder_instance.poll_actions()
    except Exception as e:
        logger.warning(f"[poll] poll_actions raised: {e}")
        return JsonResponse({"recording": True, "actions": []})

    # Save new actions to DB immediately (so they aren't lost if stop fails)
    session_id = request.session.get("active_recording_id")
    if session_id and new_actions:
        try:
            session = RecordingSession.objects.get(id=session_id)
            for action_data in new_actions:
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
                    element_role=action_data.get("element_role", ""),
                    element_type=action_data.get("element_type", ""),
                    element_dyn_control_name=action_data.get("element_dyn_control_name", ""),
                    element_data_testid=action_data.get("element_data_testid", ""),
                    element_rect=action_data.get("element_rect", {}),
                    page_url=action_data.get("page_url", ""),
                    page_title=action_data.get("page_title", ""),
                    input_value=action_data.get("input_value", ""),
                    key_pressed=action_data.get("key_pressed", ""),
                    locator_strategies=action_data.get("locator_strategies", []),
                )
        except RecordingSession.DoesNotExist:
            pass
        except Exception as e:
            logger.warning(f"[poll] Failed to save actions: {e}")

    return JsonResponse({
        "recording": True,
        "actions": new_actions
    })


# =============================================================================
# RECORDING DETAIL & CONVERT TO WORKFLOW
# =============================================================================

class RecordingDetailView(LoginRequiredMixin, DetailView):
    """View a recording session and its captured actions."""
    model = RecordingSession
    template_name = "erp_automation/recording_detail.html"
    context_object_name = "session"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        actions = self.object.actions.order_by("order")
        ctx["actions"] = actions
        ctx["workflows"] = Workflow.objects.filter(status=WorkflowStatus.ACTIVE).order_by("name")

        # Build JSON for conversion UI
        actions_list = []
        for a in actions:
            strategies = a.locator_strategies or a.generate_locator_strategies()
            actions_list.append({
                "order": a.order,
                "action_type": a.action_type,
                "element_tag": a.element_tag,
                "element_id": a.element_id,
                "element_name": a.element_name,
                "element_class": a.element_class[:80] if a.element_class else "",
                "element_xpath": a.element_xpath,
                "element_css": a.element_css[:120] if a.element_css else "",
                "element_text": a.element_text[:60] if a.element_text else "",
                "element_aria_label": a.element_aria_label,
                "element_placeholder": a.element_placeholder,
                "input_value": a.input_value,
                "key_pressed": a.key_pressed,
                "page_url": a.page_url,
                "page_title": a.page_title,
                "locator_strategies": strategies,
            })
        ctx["actions_json"] = json.dumps(actions_list)

        # Job data clipboard values (if linked)
        if self.object.job_data:
            ctx["clipboard_data"] = self.object.job_data.get_row_data()
            ctx["linked_job_data"] = self.object.job_data

        # All available job data records so user can pick/change
        ctx["job_data_records"] = ERPJobData.objects.exclude(
            status='COMPLETED'
        ).order_by('-created_at')
        return ctx


@login_required
@require_POST
def quick_convert_recording(request, pk):
    """Quick-convert a recording session to workflow using smart auto-conversion.

    Uses the same logic as `create_workflow_from_recording` management command:
    - Deduplicates click+fill pairs, consecutive fills
    - Skips login steps
    - Maps known field values to template variables ({{SERIAL NO}}, etc.)
    - Converts D365 'select' → 'click' (no native <select> elements)
    - Generates locators with contains-xpath fallbacks for D365 dynamic IDs
    - Sequential step numbering

    POST body (optional JSON):
      {"workflow_name": "...", "overwrite": false}
    """
    session = get_object_or_404(RecordingSession, pk=pk)
    if session.status != 'completed':
        return JsonResponse({"success": False, "message": "Session must be completed first"}, status=400)

    if session.actions.count() < 5:
        return JsonResponse({"success": False, "message": "Session has too few actions to convert"}, status=400)

    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    workflow_name = body.get("workflow_name", "").strip()
    if not workflow_name:
        workflow_name = f"Create Released Product (Recorded v2)"

    overwrite = body.get("overwrite", True)

    # Check if workflow exists and overwrite is not allowed
    existing_wf = Workflow.objects.filter(name=workflow_name).first()
    if existing_wf and not overwrite:
        return JsonResponse({
            "success": False,
            "message": f"Workflow '{workflow_name}' already exists. Set overwrite=true to replace it.",
        }, status=400)

    # Use the management command logic directly
    from django.core.management import call_command
    from io import StringIO

    stdout = StringIO()
    stderr = StringIO()

    try:
        call_command(
            'create_workflow_from_recording',
            session=session.pk,
            name=workflow_name,
            stdout=stdout,
            stderr=stderr,
        )
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Conversion error: {str(e)}",
        }, status=500)

    error_output = stderr.getvalue().strip()
    if error_output:
        return JsonResponse({
            "success": False,
            "message": f"Conversion error: {error_output}",
        }, status=500)

    # Reload session to get the linked workflow
    session.refresh_from_db()
    if session.generated_workflow:
        wf = session.generated_workflow
        return JsonResponse({
            "success": True,
            "workflow_id": wf.pk,
            "workflow_name": wf.name,
            "steps_created": wf.steps.count(),
            "message": f"Workflow '{wf.name}' created with {wf.steps.count()} steps",
            "output": stdout.getvalue(),
        })
    else:
        return JsonResponse({
            "success": False,
            "message": "Conversion completed but no workflow was linked. Check logs.",
            "output": stdout.getvalue(),
        }, status=500)


@login_required
@require_POST
def convert_recording_to_workflow(request, pk):
    """Convert a recording session into a Workflow with Locator models (manual mode)."""
    import re as _re

    session = get_object_or_404(RecordingSession, pk=pk)
    if session.status != 'completed':
        return JsonResponse({"success": False, "message": "Session must be completed first"}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    workflow_name = data.get("workflow_name", "").strip()
    if not workflow_name:
        return JsonResponse({"success": False, "message": "Workflow name is required"}, status=400)

    if Workflow.objects.filter(name=workflow_name).exists():
        return JsonResponse({"success": False, "message": f"Workflow '{workflow_name}' already exists"}, status=400)

    # Index recorded actions by order
    actions_by_order = {a.order: a for a in session.actions.all()}

    # Create workflow
    workflow = Workflow.objects.create(
        name=workflow_name,
        description=data.get("workflow_description", f"Created from recording: {session.name}"),
        target_url=data.get("target_url", session.target_url),
        application="dynamics365",
        condition_field=data.get("condition_field", ""),
        status=WorkflowStatus.DRAFT,
        created_by=request.user,
    )

    step_order = 10
    steps_created = 0

    for step_data in data.get("steps", []):
        if not step_data.get("is_active", True):
            continue

        action_order = step_data.get("action_order")
        recorded_action = actions_by_order.get(action_order)
        if not recorded_action:
            continue

        # Create or find Locator
        locator = None
        action_type = step_data.get("action_type", recorded_action.action_type)
        if action_type not in ("wait_time", "screenshot"):
            locator = _get_or_create_locator(
                recorded_action=recorded_action,
                step_name=step_data.get("step_name", f"Step {step_order}"),
                application="dynamics365",
                user=request.user,
            )

        WorkflowStep.objects.create(
            workflow=workflow,
            order=step_order,
            name=step_data.get("step_name", f"Step {step_order}"),
            action_type=action_type,
            locator=locator,
            value_static=step_data.get("value_static", ""),
            value_field=step_data.get("value_field", ""),
            value_template=step_data.get("value_template", ""),
            condition_value=step_data.get("condition_value", ""),
            clear_before_fill=step_data.get("clear_before_fill", False),
            press_key_after=step_data.get("press_key_after", recorded_action.key_pressed or ""),
            wait_after=int(step_data.get("wait_after", 500)),
            timeout=int(step_data.get("timeout", 30000)),
            continue_on_error=step_data.get("continue_on_error", False),
            is_active=True,
        )
        step_order += 10
        steps_created += 1

    # Link session to workflow
    session.generated_workflow = workflow
    session.save(update_fields=["generated_workflow"])

    return JsonResponse({
        "success": True,
        "workflow_id": workflow.pk,
        "steps_created": steps_created,
        "message": f"Workflow '{workflow_name}' created with {steps_created} steps",
    })


def _get_or_create_locator(recorded_action, step_name, application, user):
    """Create or reuse a Locator + LocatorStrategy from a RecordedAction."""
    import re as _re

    # Generate a locator name from the best identifier
    raw_name = (
        recorded_action.element_name or
        recorded_action.element_aria_label or
        (recorded_action.element_id if recorded_action.element_id and
         not recorded_action._is_dynamic_id(recorded_action.element_id) else '') or
        recorded_action.element_placeholder or
        step_name
    )

    # Slugify: lowercase, replace non-alnum with underscore
    slug_name = _re.sub(r'[^a-z0-9]+', '_', raw_name.lower()).strip('_')[:80]
    if not slug_name:
        slug_name = f"element_{recorded_action.order}"

    # Add suffix for uniqueness: append _Loc
    locator_name = f"{slug_name}_Loc"

    # Deduplicate — if same name+application exists, reuse it
    existing = Locator.objects.filter(name=locator_name, application=application).first()
    if existing:
        return existing

    # If name already taken (different application), make unique
    if Locator.objects.filter(name=locator_name).exists():
        locator_name = f"{slug_name}_{recorded_action.order}_Loc"

    locator = Locator.objects.create(
        name=locator_name,
        description=f"Recorded: {step_name} ({recorded_action.element_tag})",
        application=application,
        page_context=recorded_action.page_url or "",
        is_dynamic=bool(recorded_action.element_id and
                       recorded_action._is_dynamic_id(recorded_action.element_id)),
        requires_wait=True,
        default_timeout=30000,
        created_by=user,
    )

    # Create strategies from saved locator_strategies JSON
    strategies = recorded_action.locator_strategies or recorded_action.generate_locator_strategies()
    for strat in strategies:
        try:
            LocatorStrategy.objects.create(
                locator=locator,
                strategy_type=strat["strategy_type"],
                value=strat["value"],
                priority=strat.get("priority", 10),
            )
        except Exception:
            pass

    return locator


# =============================================================================
# JOB DATA CLIPBOARD API
# =============================================================================

@login_required
@require_GET
def api_job_data_clipboard(request, pk):
    """Return clipboard data for a job data record (for AJAX loading)."""
    job_data = get_object_or_404(ERPJobData, pk=pk)
    row_data = job_data.get_row_data()

    # Build product name combination
    product_name_parts = [
        row_data.get('ORDER NO.', ''),
        row_data.get('SERIAL NO', ''),
        row_data.get('SIZE', ''),
        row_data.get('TYPE', ''),
        row_data.get('MAT NO.', ''),
    ]
    product_name = ' '.join(p for p in product_name_parts if p)

    # Cutter BOM data (from job card Excel)
    cutter_bom = job_data.cutter_bom_data or []
    cutter_summary = []
    for cutter in cutter_bom:
        line = {}
        if isinstance(cutter, dict):
            line = {
                'qty': cutter.get('qty', ''),
                'size': cutter.get('size', cutter.get('size_mm', '')),
                'part_no': cutter.get('part_no', cutter.get('mat_number', '')),
                'description': cutter.get('description', cutter.get('item_name', '')),
                'variant': cutter.get('variant', ''),
            }
        cutter_summary.append(line)

    return JsonResponse({
        "success": True,
        "clipboard_data": row_data,
        "product_name": product_name,
        "search_name": row_data.get('SERIAL NO', ''),
        "job_data_label": f"{job_data.work_order_number} - {job_data.serial_number} ({job_data.account})",
        "cutter_bom": cutter_summary,
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
        qs = WorkflowExecution.objects.select_related(
            'workflow', 'executed_by', 'job_data'
        ).order_by("-started_at")

        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)

        workflow_id = self.request.GET.get('workflow', '')
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workflows'] = Workflow.objects.all().order_by('name')
        return context


class ExecutionDetailView(LoginRequiredMixin, DetailView):
    model = WorkflowExecution
    template_name = "erp_automation/execution_detail.html"
    context_object_name = "execution"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['step_executions'] = self.object.step_executions.select_related('step').order_by('step__order')
        return ctx


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
@require_POST
def api_workflow_update_url(request, pk):
    """API: Update a workflow's target URL."""
    workflow = get_object_or_404(Workflow, pk=pk)
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    new_url = body.get('target_url', '').strip()
    if new_url:
        # Ensure URL has protocol prefix
        if not new_url.startswith(('http://', 'https://')):
            new_url = 'https://' + new_url
        workflow.target_url = new_url
        workflow.save(update_fields=['target_url'])
        return JsonResponse({"success": True, "target_url": workflow.target_url})
    else:
        return JsonResponse({"success": False, "message": "URL cannot be empty"}, status=400)


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


# =============================================================================
# JOB DATA VIEWS
# =============================================================================

class JobDataListView(LoginRequiredMixin, ListView):
    """List all ERPJobData records with status filtering and search."""
    model = ERPJobData
    template_name = "erp_automation/job_data_list.html"
    context_object_name = "jobs"

    def get_queryset(self):
        qs = ERPJobData.objects.select_related('route').all()

        # Filter by status
        status = self.request.GET.get('status', '')
        if status and status in dict(ERPJobData.Status.choices):
            qs = qs.filter(status=status)

        # Search on work_order_number, serial_number, account
        search = self.request.GET.get('search', '').strip()
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(work_order_number__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(account__icontains=search)
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ERPJobData.Status.choices
        context['current_status'] = self.request.GET.get('status', '')
        context['current_search'] = self.request.GET.get('search', '')
        return context


class JobDataUploadView(LoginRequiredMixin, View):
    """Upload one or more Job Card .xlsx files, parse them, and create ERPJobData records."""
    template_name = "erp_automation/job_data_upload.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        from apps.erp_automation.services.job_card_parser import parse_job_card
        from apps.erp_automation.services.route_selector import select_route
        import tempfile

        files = request.FILES.getlist('job_card_files')
        if not files:
            messages.error(request, "No files were uploaded.")
            return redirect('erp_automation:job_data_list')

        success_count = 0
        for uploaded_file in files:
            if not uploaded_file.name.endswith('.xlsx'):
                messages.error(request, f"Skipped '{uploaded_file.name}' — only .xlsx files are supported.")
                continue

            tmp_path = None
            try:
                # Save to temp location
                with tempfile.NamedTemporaryFile(
                    suffix='.xlsx', delete=False, dir=settings.BASE_DIR
                ) as tmp:
                    for chunk in uploaded_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                # Parse the job card
                parsed = parse_job_card(tmp_path)

                # Auto-select route
                route = select_route(
                    size_inches=parsed.get('size_inches'),
                    has_port=parsed.get('has_port', False),
                    has_usr=parsed.get('has_usr', False),
                    has_hardfacing=parsed.get('has_hardfacing', False),
                    has_crush_shear=parsed.get('has_crush_shear', False),
                    is_rerun=parsed.get('is_rerun', False),
                    is_inspection_only=parsed.get('is_inspection_only', False),
                    bit_type='FC',
                )

                # Create ERPJobData record
                ERPJobData.objects.create(
                    work_order_number=parsed.get('work_order_number', ''),
                    serial_number=parsed.get('serial_number', ''),
                    size_raw=parsed.get('size_raw', ''),
                    size_inches=parsed.get('size_inches'),
                    smi_type=parsed.get('smi_type', ''),
                    l5_mat_full=parsed.get('l5_mat_full', ''),
                    l5_mat_original=parsed.get('l5_mat_original', ''),
                    date_received=parsed.get('date_received'),
                    account=parsed.get('account', ''),
                    contract_number=parsed.get('contract_number', ''),
                    vendor_number=parsed.get('vendor_number', ''),
                    l3_l4_mat=parsed.get('l3_l4_mat', ''),
                    evaluated_by=parsed.get('evaluated_by', ''),
                    reviewed_by=parsed.get('reviewed_by', ''),
                    body_material=parsed.get('body_material', ''),
                    item_group=parsed.get('item_group', ''),
                    size_class=parsed.get('size_class', ''),
                    has_port=parsed.get('has_port', False),
                    has_usr=parsed.get('has_usr', False),
                    has_hardfacing=parsed.get('has_hardfacing', False),
                    has_crush_shear=parsed.get('has_crush_shear', False),
                    is_rerun=parsed.get('is_rerun', False),
                    is_inspection_only=parsed.get('is_inspection_only', False),
                    is_scrap=parsed.get('is_scrap', False),
                    cutter_bom_data=parsed.get('cutter_bom_data', []),
                    modified_cutters_data=parsed.get('modified_cutters_data', []),
                    source_file=parsed.get('source_file', uploaded_file.name),
                    route=route,
                    route_override=False,
                    status='READY',
                    created_by=request.user,
                )
                success_count += 1
                messages.success(request, f"Parsed '{uploaded_file.name}' successfully.")

            except Exception as e:
                messages.error(request, f"Error parsing '{uploaded_file.name}': {str(e)}")
            finally:
                # Clean up temp file
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)

        if success_count > 0:
            messages.success(request, f"Created {success_count} job data record(s).")

        return redirect('erp_automation:job_data_list')


class JobDataDetailView(LoginRequiredMixin, DetailView):
    """Show all fields of a single ERPJobData record."""
    model = ERPJobData
    template_name = "erp_automation/job_data_detail.html"
    context_object_name = "job"

    def get_queryset(self):
        return ERPJobData.objects.select_related('route')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['routes'] = ERPRoute.objects.filter(is_active=True).order_by('route_number')
        context['status_choices'] = ERPJobData.Status.choices
        context['workflows'] = Workflow.objects.filter(status=WorkflowStatus.ACTIVE).order_by('name')
        context['chains'] = WorkflowChain.objects.filter(status='active').prefetch_related('links').order_by('name')
        context['executions'] = WorkflowExecution.objects.filter(
            job_data=self.object
        ).select_related('workflow').order_by('-started_at')[:10]
        context['chain_executions'] = ChainExecution.objects.filter(
            job_data=self.object
        ).select_related('chain').order_by('-started_at')[:10]
        context['has_credentials'] = 'erp_credentials' in self.request.session
        return context


@login_required
@require_POST
def job_data_update(request, pk):
    """Save edits from the job data detail form."""
    job_data = get_object_or_404(ERPJobData, pk=pk)

    action = request.POST.get('action', 'save')

    # Handle delete action — allow for DRAFT, READY, ERROR, SENT
    if action == 'delete':
        deletable = ('DRAFT', 'READY', 'ERROR', 'SENT')
        if job_data.status not in deletable:
            messages.error(request, f"Cannot delete job data with status '{job_data.get_status_display()}'. Only Draft, Ready, Error, and Sent records can be deleted.")
            return redirect('erp_automation:job_data_detail', pk=job_data.pk)
        wo_number = job_data.work_order_number
        job_data.delete()
        messages.success(request, f"Job data for {wo_number} deleted.")
        return redirect('erp_automation:job_data_list')

    # Handle reset_ready action — reset to READY so user can retry execution
    if action == 'reset_ready':
        if job_data.status in ('ERROR', 'SENT'):
            job_data.status = 'READY'
            job_data.save(update_fields=['status', 'updated_at'])
            messages.success(request, f"Job data for {job_data.work_order_number} reset to Ready. You can now retry execution.")
        else:
            messages.warning(request, f"Cannot reset: current status is {job_data.get_status_display()}.")
        return redirect('erp_automation:job_data_detail', pk=job_data.pk)

    # Handle reset_draft action — full reset back to DRAFT
    if action == 'reset_draft':
        if job_data.status in ('ERROR', 'SENT', 'READY'):
            job_data.status = 'DRAFT'
            job_data.save(update_fields=['status', 'updated_at'])
            messages.success(request, f"Job data for {job_data.work_order_number} reset to Draft.")
        else:
            messages.warning(request, f"Cannot reset: current status is {job_data.get_status_display()}.")
        return redirect('erp_automation:job_data_detail', pk=job_data.pk)

    # Update route
    route_pk = request.POST.get('route')
    if route_pk:
        new_route = get_object_or_404(ERPRoute, pk=route_pk)
        if job_data.route_id != new_route.pk:
            job_data.route = new_route
            job_data.route_override = True
    else:
        if job_data.route_id is not None:
            job_data.route = None
            job_data.route_override = True

    # Update editable fields (item_number is ERP-assigned, not editable here)
    job_data.notes = request.POST.get('notes', '')
    job_data.smi_type = request.POST.get('smi_type', job_data.smi_type)
    job_data.account = request.POST.get('account', job_data.account)
    job_data.l5_mat_full = request.POST.get('l5_mat_full', job_data.l5_mat_full)
    job_data.l5_mat_original = request.POST.get('l5_mat_original', job_data.l5_mat_original)
    job_data.body_material = request.POST.get('body_material', job_data.body_material)
    job_data.item_group = request.POST.get('item_group', job_data.item_group)
    job_data.size_class = request.POST.get('size_class', job_data.size_class)
    job_data.has_port = request.POST.get('has_port') == 'true'

    # Date received
    date_str = request.POST.get('date_received', '')
    if date_str:
        try:
            from datetime import datetime
            job_data.date_received = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Handle mark_ready action
    if action == 'mark_ready':
        job_data.status = 'READY'
        messages.success(request, f"Job data for {job_data.work_order_number} marked as Ready.")
    else:
        messages.success(request, f"Job data for {job_data.work_order_number} updated.")

    job_data.save()
    return redirect('erp_automation:job_data_detail', pk=job_data.pk)


@login_required
@require_POST
def job_data_delete(request, pk):
    """Delete an ERPJobData record. Only COMPLETED records are protected."""
    job_data = get_object_or_404(ERPJobData, pk=pk)

    if job_data.status == 'COMPLETED':
        messages.error(request, f"Cannot delete completed job data. Reset status first if needed.")
        return redirect('erp_automation:job_data_list')

    wo_number = job_data.work_order_number
    job_data.delete()
    messages.success(request, f"Job data for {wo_number} deleted.")
    return redirect('erp_automation:job_data_list')


# =============================================================================
# ROUTE VIEWS
# =============================================================================

class RouteListView(LoginRequiredMixin, ListView):
    """List all ERPRoute records with filtering."""
    model = ERPRoute
    template_name = "erp_automation/route_list.html"
    context_object_name = "routes"

    def get_queryset(self):
        qs = ERPRoute.objects.all()

        bit_type = self.request.GET.get('bit_type', '')
        if bit_type and bit_type in dict(ERPRoute.BitType.choices):
            qs = qs.filter(bit_type=bit_type)

        level = self.request.GET.get('level', '')
        if level and level in dict(ERPRoute.Level.choices):
            qs = qs.filter(level=level)

        approved = self.request.GET.get('approved', '')
        if approved == 'true':
            qs = qs.filter(approved=True)
        elif approved == 'false':
            qs = qs.filter(approved=False)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bit_type_choices'] = ERPRoute.BitType.choices
        context['level_choices'] = ERPRoute.Level.choices
        context['current_bit_type'] = self.request.GET.get('bit_type', '')
        context['current_level'] = self.request.GET.get('level', '')
        context['current_approved'] = self.request.GET.get('approved', '')
        return context


# =============================================================================
# API VIEWS
# =============================================================================

@login_required
@require_GET
def api_select_route(request):
    """API to select a route based on bit characteristics.

    Query params: size_inches, has_port, has_usr, has_hardfacing,
                  has_crush_shear, is_rerun, is_inspection_only, bit_type
    Returns JSON: {success, route: {id, route_number, name}} or {success: false, message}
    """
    from apps.erp_automation.services.route_selector import select_route
    from decimal import Decimal, InvalidOperation

    size_str = request.GET.get('size_inches', '')
    try:
        size_inches = Decimal(size_str) if size_str else None
    except InvalidOperation:
        return JsonResponse({"success": False, "message": f"Invalid size: {size_str}"}, status=400)

    def parse_bool(val):
        return val in ('true', '1', 'True', 'yes')

    route = select_route(
        size_inches=size_inches,
        has_port=parse_bool(request.GET.get('has_port', '')),
        has_usr=parse_bool(request.GET.get('has_usr', '')),
        has_hardfacing=parse_bool(request.GET.get('has_hardfacing', '')),
        has_crush_shear=parse_bool(request.GET.get('has_crush_shear', '')),
        is_rerun=parse_bool(request.GET.get('is_rerun', '')),
        is_inspection_only=parse_bool(request.GET.get('is_inspection_only', '')),
        bit_type=request.GET.get('bit_type', 'FC'),
    )

    if route:
        return JsonResponse({
            "success": True,
            "route": {
                "id": route.pk,
                "route_number": route.route_number,
                "name": route.name,
            }
        })
    else:
        return JsonResponse({
            "success": False,
            "message": "No matching route found for the given parameters."
        })


@login_required
@require_POST
def api_execute_job_data(request, pk):
    """Launch a workflow execution from an ERPJobData record (async, background thread).

    Expects POST JSON: {
        "workflow_id": int (optional, defaults to first active workflow),
        "headless": bool (optional, default False)
    }

    Returns immediately with a redirect to the live execution progress page.
    The execution runs in a background thread with real-time progress polling.
    """
    job_data = get_object_or_404(ERPJobData, pk=pk)

    # Allow READY, ERROR, and SENT (for retrying stuck jobs)
    if job_data.status not in ('READY', 'ERROR', 'SENT'):
        return JsonResponse({
            "success": False,
            "message": f"Job data must be in READY, ERROR, or SENT status to execute. Current: {job_data.get_status_display()}"
        }, status=400)

    # Get credentials from session
    credentials = get_credentials(request)
    if not credentials:
        return JsonResponse({
            "success": False,
            "message": "No ERP credentials set. Please set credentials first.",
            "redirect": "/erp-automation/credentials/"
        }, status=401)

    # Parse request body
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    # Find the workflow to execute
    workflow_id = body.get('workflow_id')
    if workflow_id:
        try:
            workflow = Workflow.objects.get(id=workflow_id, status=WorkflowStatus.ACTIVE)
        except Workflow.DoesNotExist:
            return JsonResponse({"success": False, "message": "Workflow not found or not active."}, status=404)
    else:
        # Default: first active workflow
        workflow = Workflow.objects.filter(status=WorkflowStatus.ACTIVE).first()
        if not workflow:
            return JsonResponse({
                "success": False,
                "message": "No active workflows available. Please create or activate a workflow first."
            }, status=404)

    headless = body.get('headless', False)

    # Build row_data from job data fields
    row_data = job_data.get_row_data()

    # Create execution record
    execution = WorkflowExecution.objects.create(
        workflow=workflow,
        job_data=job_data,
        row_data=row_data,
        sheet_name=job_data.account,
        executed_by=request.user,
        status=ExecutionStatus.RUNNING,
        started_at=timezone.now(),
    )

    # Mark job as SENT
    job_data.status = 'SENT'
    job_data.save(update_fields=['status', 'updated_at'])

    # Get condition value and steps for progress tracking
    condition_value = None
    if workflow.condition_field and row_data:
        cv = row_data.get(workflow.condition_field, "")
        condition_value = str(cv).strip().upper() if cv else None
    steps_list = list(workflow.get_steps_for_condition(condition_value))

    # Initialize live progress state
    with _live_execution_lock:
        _live_execution_state[execution.pk] = {
            "status": "running",
            "total_steps": len(steps_list),
            "current_step_index": 0,
            "current_step": None,
            "completed_steps": [],
            "error": None,
        }

    # Launch execution in background thread
    creds = {"username": credentials["username"], "password": credentials["password"]}
    erp_url = workflow.target_url or credentials.get("erp_url", "")

    thread = threading.Thread(
        target=_live_execution_thread,
        args=(workflow, row_data, execution, job_data, creds, erp_url, headless),
        daemon=True,
        name=f"live-exec-{execution.pk}",
    )
    thread.start()

    return JsonResponse({
        "success": True,
        "execution_id": execution.pk,
        "redirect": f"/erp-automation/live/{execution.pk}/",
        "message": "Execution started",
    })


def _live_execution_thread(workflow, row_data, execution, job_data, credentials, erp_url, headless):
    """Background thread for live workflow execution with progress tracking."""
    global _executor_instance
    logger = logging.getLogger(__name__)
    exec_id = execution.pk

    try:
        from .services.executor import WorkflowExecutor

        if _executor_instance is None:
            _executor_instance = WorkflowExecutor()

        # Setup progress callbacks
        def on_step_start(step, completed, total):
            with _live_execution_lock:
                state = _live_execution_state.get(exec_id)
                if state:
                    state["current_step_index"] = completed
                    state["current_step"] = {
                        "order": step.order,
                        "name": step.name,
                        "action_type": step.action_type,
                    }

        def on_step_complete(step, result):
            with _live_execution_lock:
                state = _live_execution_state.get(exec_id)
                if state:
                    state["completed_steps"].append({
                        "order": step.order,
                        "name": step.name,
                        "status": "success",
                    })

        def on_step_error(step, result):
            with _live_execution_lock:
                state = _live_execution_state.get(exec_id)
                if state:
                    state["completed_steps"].append({
                        "order": step.order,
                        "name": step.name,
                        "status": "failed",
                        "message": result.get("message", ""),
                    })

        _executor_instance.on_step_start = on_step_start
        _executor_instance.on_step_complete = on_step_complete
        _executor_instance.on_step_error = on_step_error

        # Start browser if not already running, or restart if dead/crashed
        need_browser = not _executor_instance.page or not _executor_instance.is_browser_alive()
        if need_browser:
            _executor_instance.stop_browser()
            browser_started = _executor_instance.start_browser(
                url=erp_url,
                credentials=credentials,
                headless=headless,
            )
            if not browser_started:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = "Failed to start browser."
                execution.completed_at = timezone.now()
                execution.save()
                job_data.status = 'ERROR'
                job_data.save(update_fields=['status', 'updated_at'])
                with _live_execution_lock:
                    state = _live_execution_state.get(exec_id)
                    if state:
                        state["status"] = "failed"
                        state["error"] = {"message": "Failed to start browser."}
                return

        # Run the workflow
        result = _executor_instance.execute_workflow(workflow, row_data, execution)

        if result.get("success"):
            job_data.status = 'COMPLETED'
            context_vars = result.get("context", {})
            if context_vars.get("item_number"):
                job_data.item_number = context_vars["item_number"]
            job_data.save(update_fields=['status', 'item_number', 'updated_at'])

            with _live_execution_lock:
                state = _live_execution_state.get(exec_id)
                if state:
                    state["status"] = "completed"
                    state["steps_completed_count"] = result.get("steps_completed", 0)
        else:
            job_data.status = 'ERROR'
            job_data.save(update_fields=['status', 'updated_at'])

            with _live_execution_lock:
                state = _live_execution_state.get(exec_id)
                if state:
                    state["status"] = "failed"
                    state["error"] = {
                        "message": result.get("message", "Unknown error"),
                        "failed_step": result.get("failed_step"),
                        "failed_step_name": result.get("failed_step_name"),
                    }

    except Exception as e:
        import traceback
        logger.error(f"Live execution error for execution {exec_id}: {traceback.format_exc()}")

        try:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)[:500]
            execution.completed_at = timezone.now()
            execution.save()
        except Exception:
            pass

        try:
            job_data.status = 'ERROR'
            job_data.save(update_fields=['status', 'updated_at'])
        except Exception:
            pass

        with _live_execution_lock:
            state = _live_execution_state.get(exec_id)
            if state:
                state["status"] = "failed"
                state["error"] = {"message": f"{type(e).__name__}: {str(e)}"}

    finally:
        # Clear callbacks
        if _executor_instance:
            _executor_instance.on_step_start = None
            _executor_instance.on_step_complete = None
            _executor_instance.on_step_error = None


class LiveExecutionView(LoginRequiredMixin, DetailView):
    """Render the live execution progress page (read-only, like debug page but without locator tools)."""
    model = WorkflowExecution
    template_name = "erp_automation/execution_live.html"
    context_object_name = "execution"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        execution = self.object
        workflow = execution.workflow
        ctx["workflow"] = workflow
        ctx["job_data"] = execution.job_data

        # Get steps matching the condition (same filter as execute_workflow)
        condition_value = None
        if workflow.condition_field and execution.row_data:
            cv = execution.row_data.get(workflow.condition_field, "")
            condition_value = str(cv).strip().upper() if cv else None
        steps = list(workflow.get_steps_for_condition(condition_value))

        ctx["all_steps"] = [
            {"order": s.order, "name": s.name, "action_type": s.action_type}
            for s in steps
        ]
        return ctx


@login_required
@require_GET
def api_poll_live_execution(request, pk):
    """Poll current live execution progress state."""
    with _live_execution_lock:
        state = _live_execution_state.get(pk)

    if state is None:
        # Check the DB for finished status (might have been cleaned up)
        try:
            execution = WorkflowExecution.objects.get(pk=pk)
            if execution.status in ("success",):
                return JsonResponse({
                    "status": "completed",
                    "total_steps": 0,
                    "current_step_index": 0,
                    "current_step": None,
                    "completed_steps": [],
                    "error": None,
                })
            elif execution.status in ("failed",):
                return JsonResponse({
                    "status": "failed",
                    "total_steps": 0,
                    "current_step_index": 0,
                    "current_step": None,
                    "completed_steps": [],
                    "error": {"message": execution.error_message or "Unknown error"},
                })
        except WorkflowExecution.DoesNotExist:
            pass
        return JsonResponse({
            "status": "idle",
            "message": "No active execution found",
            "total_steps": 0,
            "current_step_index": 0,
            "current_step": None,
            "completed_steps": [],
            "error": None,
        })

    return JsonResponse(state)


@login_required
@require_POST
def api_stop_live_execution(request, pk):
    """Stop a live (non-debug) execution."""
    global _executor_instance
    if _executor_instance and _executor_instance.is_running:
        _executor_instance.should_stop = True
        with _live_execution_lock:
            state = _live_execution_state.get(pk)
            if state:
                state["status"] = "stopped"
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "message": "No running execution found"}, status=400)


@login_required
@require_POST
def api_generate_item_number(request, pk):
    """Generate the next ERP item number for a job data record.

    Uses the ItemCounter for the record's item_group to generate a sequential number.
    Returns JSON: {success, item_number}
    """
    job_data = get_object_or_404(ERPJobData, pk=pk)

    if not job_data.item_group:
        return JsonResponse({
            "success": False,
            "message": "No item group set. Cannot generate item number."
        }, status=400)

    if job_data.item_number:
        return JsonResponse({
            "success": False,
            "message": f"Item number already assigned: {job_data.item_number}"
        }, status=400)

    try:
        counter, created = ItemCounter.objects.get_or_create(
            account_type=job_data.item_group,
            defaults={
                'prefix': f"{job_data.item_group}-",
                'current_number': 1,
                'padding': 4,
            }
        )
        item_number = counter.get_next_number()
        job_data.item_number = item_number
        job_data.save(update_fields=['item_number', 'updated_at'])

        return JsonResponse({
            "success": True,
            "item_number": item_number,
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Error generating item number: {str(e)}"
        }, status=500)


# =============================================================================
# DEBUG EXECUTION MODE
# =============================================================================

def _debug_execution_thread(debug_executor, workflow, row_data, execution, credentials, erp_url):
    """Thread target function for debug execution."""
    debug_executor.start_debug(workflow, row_data, execution, credentials, erp_url)


@login_required
@require_POST
def api_start_debug_execution(request, pk):
    """Start workflow execution in debug mode (background thread, pauses on error)."""
    global _debug_executor

    try:
        job_data = get_object_or_404(ERPJobData, pk=pk)

        if job_data.status not in ('READY', 'ERROR', 'SENT'):
            return JsonResponse({
                "success": False,
                "message": f"Job data status is '{job_data.status}', must be READY, ERROR, or SENT"
            }, status=400)

        # Get credentials
        credentials = request.session.get("erp_credentials")
        if not credentials:
            return JsonResponse({
                "success": False,
                "message": "No ERP credentials. Please set them first.",
                "redirect": "/erp-automation/credentials/"
            })

        # Get workflow
        body = json.loads(request.body) if request.body else {}
        workflow_id = body.get("workflow_id")
        if workflow_id:
            workflow = get_object_or_404(Workflow, pk=workflow_id)
        else:
            workflow = Workflow.objects.filter(status="active").first()
            if not workflow:
                return JsonResponse({
                    "success": False,
                    "message": "No active workflow found"
                }, status=400)

        # Stop any existing debug executor
        if _debug_executor is not None:
            try:
                _debug_executor.stop()
                _debug_executor.stop_browser()
            except Exception:
                pass

        # Build row_data
        row_data = job_data.get_row_data()

        # Create execution record
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            job_data=job_data,
            row_data=row_data,
            status="pending",
            executed_by=request.user,
        )
        job_data.status = "SENT"
        job_data.save(update_fields=["status", "updated_at"])

        # Create debug executor
        from .services.executor import DebugExecutor
        _debug_executor = DebugExecutor()

        # Use workflow's target_url (same as regular executor), fall back to credentials
        erp_url = workflow.target_url or credentials.get("erp_url", "")

        # Start the debug thread
        thread = threading.Thread(
            target=_debug_execution_thread,
            args=(_debug_executor, workflow, row_data, execution,
                  {"username": credentials["username"], "password": credentials["password"]},
                  erp_url),
            daemon=True,
            name=f"debug-exec-{pk}",
        )
        thread.start()

        # Wait for browser to be ready (max 90 seconds)
        ready = _debug_executor.ready_event.wait(timeout=90)
        if not ready:
            return JsonResponse({
                "success": False,
                "message": "Browser failed to start within 90 seconds"
            }, status=500)

        return JsonResponse({
            "success": True,
            "execution_id": execution.pk,
            "redirect": f"/erp-automation/debug/{execution.pk}/",
        })

    except Exception as e:
        logger.exception(f"Failed to start debug execution: {e}")
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)


class DebugExecutionView(LoginRequiredMixin, DetailView):
    """Render the debug execution UI page."""
    model = WorkflowExecution
    template_name = "erp_automation/debug_execution.html"
    context_object_name = "execution"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        execution = self.object
        workflow = execution.workflow
        ctx["workflow"] = workflow
        ctx["job_data"] = execution.job_data

        # Get steps matching the condition (same filter as _debug_step_loop)
        condition_value = None
        if workflow.condition_field and execution.row_data:
            cv = execution.row_data.get(workflow.condition_field, "")
            condition_value = str(cv).strip().upper() if cv else None
        steps = list(workflow.get_steps_for_condition(condition_value))

        ctx["all_steps"] = [
            {"order": s.order, "name": s.name, "action_type": s.action_type}
            for s in steps
        ]
        return ctx


@login_required
@require_GET
def api_poll_debug_status(request, pk):
    """Poll current debug execution state."""
    global _debug_executor
    if _debug_executor is None:
        return JsonResponse({"status": "idle", "message": "No debug session active"})

    state = _debug_executor.get_debug_state()
    return JsonResponse(state)


@login_required
@require_POST
def api_debug_resume(request, pk):
    """Resume debug execution (retry current step with updated locator)."""
    global _debug_executor
    if _debug_executor is None:
        return JsonResponse({"success": False, "message": "No debug session"}, status=400)
    _debug_executor.resume()
    return JsonResponse({"success": True})


@login_required
@require_POST
def api_debug_skip(request, pk):
    """Skip the failing step and continue."""
    global _debug_executor
    if _debug_executor is None:
        return JsonResponse({"success": False, "message": "No debug session"}, status=400)
    _debug_executor.skip()
    return JsonResponse({"success": True})


@login_required
@require_POST
def api_debug_stop(request, pk):
    """Stop debug execution."""
    global _debug_executor
    if _debug_executor is None:
        return JsonResponse({"success": False, "message": "No debug session"}, status=400)
    _debug_executor.stop()
    return JsonResponse({"success": True})


@login_required
@require_POST
def api_debug_test_locator(request, pk):
    """Test a locator expression against the current browser page."""
    global _debug_executor
    if _debug_executor is None:
        return JsonResponse({"success": False, "message": "No debug session"}, status=400)

    try:
        body = json.loads(request.body)
        strategy_type = body.get("strategy_type", "xpath")
        value = body.get("value", "")

        if not value:
            return JsonResponse({"success": False, "message": "No locator value provided"}, status=400)

        # Send test command to the debug thread (must run in Playwright thread)
        _debug_executor.send_command("test_locator", {
            "strategy_type": strategy_type,
            "value": value,
        })

        # Wait for result
        result = _debug_executor.get_command_result(timeout=10)
        return JsonResponse({"success": True, "result": result})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@login_required
@require_POST
def api_debug_update_locator(request, pk):
    """Update or add a locator strategy in the database."""
    try:
        body = json.loads(request.body)
        locator_id = body.get("locator_id")
        strategy_type = body.get("strategy_type", "xpath")
        new_value = body.get("value", "")
        priority = body.get("priority", 0)

        if not locator_id or not new_value:
            return JsonResponse({"success": False, "message": "locator_id and value required"}, status=400)

        locator = get_object_or_404(Locator, pk=locator_id)

        # Check if a strategy with this exact value already exists
        existing = LocatorStrategy.objects.filter(
            locator=locator,
            strategy_type=strategy_type,
            value=new_value,
        ).first()

        if existing:
            # Just update priority
            existing.priority = priority
            existing.is_active = True
            existing.save(update_fields=["priority", "is_active"])
            strategy = existing
            created = False
        else:
            # Create new strategy with highest priority
            strategy = LocatorStrategy.objects.create(
                locator=locator,
                strategy_type=strategy_type,
                value=new_value,
                priority=priority,
                is_active=True,
            )
            created = True

        # Bump other strategies' priority down
        locator.strategies.exclude(pk=strategy.pk).filter(
            priority__lte=priority
        ).update(priority=models.F("priority") + 1)

        return JsonResponse({
            "success": True,
            "strategy_id": strategy.pk,
            "created": created,
            "message": f"Locator strategy {'created' if created else 'updated'}"
        })

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# =============================================================================
# DEBUG CHAIN EXECUTION MODE
# =============================================================================

def _debug_chain_thread(debug_executor, chain, job_data, chain_execution, credentials, erp_url):
    """Thread target function for debug chain execution."""
    debug_executor.start_debug_chain(chain, job_data, chain_execution, credentials, erp_url)


@login_required
@require_POST
def api_start_debug_chain(request, pk):
    """Start chain execution in debug mode (background thread, pauses on error).

    POST JSON: { "chain_id": int }
    """
    global _debug_executor

    try:
        job_data = get_object_or_404(ERPJobData, pk=pk)

        if job_data.status not in ('READY', 'ERROR', 'SENT'):
            return JsonResponse({
                "success": False,
                "message": f"Job data status is '{job_data.status}', must be READY, ERROR, or SENT"
            }, status=400)

        # Get credentials
        credentials = request.session.get("erp_credentials")
        if not credentials:
            return JsonResponse({
                "success": False,
                "message": "No ERP credentials. Please set them first.",
                "redirect": "/erp-automation/credentials/"
            })

        # Get chain
        body = json.loads(request.body) if request.body else {}
        chain_id = body.get("chain_id")
        if not chain_id:
            return JsonResponse({"success": False, "message": "chain_id is required"}, status=400)

        try:
            chain = WorkflowChain.objects.get(pk=chain_id, status="active")
        except WorkflowChain.DoesNotExist:
            return JsonResponse({"success": False, "message": "Chain not found or not active."}, status=404)

        active_links = chain.get_active_links()
        if not active_links.exists():
            return JsonResponse({"success": False, "message": "Chain has no active links."}, status=400)

        # Stop any existing debug executor
        if _debug_executor is not None:
            try:
                _debug_executor.stop()
                _debug_executor.stop_browser()
            except Exception:
                pass

        # Create chain execution record
        chain_execution = ChainExecution.objects.create(
            chain=chain,
            job_data=job_data,
            status=ExecutionStatus.PENDING,
            total_links=active_links.count(),
            executed_by=request.user,
        )

        # Mark job as SENT
        job_data.status = 'SENT'
        job_data.save(update_fields=['status', 'updated_at'])

        # Determine ERP URL
        first_link = active_links.first()
        erp_url = first_link.navigate_url or first_link.workflow.target_url or credentials.get("erp_url", "")

        # Create debug executor
        from .services.executor import DebugExecutor
        _debug_executor = DebugExecutor()

        # Start the debug chain thread
        thread = threading.Thread(
            target=_debug_chain_thread,
            args=(_debug_executor, chain, job_data, chain_execution,
                  {"username": credentials["username"], "password": credentials["password"]},
                  erp_url),
            daemon=True,
            name=f"debug-chain-{pk}",
        )
        thread.start()

        # Wait for browser to be ready
        ready = _debug_executor.ready_event.wait(timeout=90)
        if not ready:
            return JsonResponse({
                "success": False,
                "message": "Browser failed to start within 90 seconds"
            }, status=500)

        return JsonResponse({
            "success": True,
            "chain_execution_id": chain_execution.pk,
            "redirect": f"/erp-automation/debug-chain/{chain_execution.pk}/",
        })

    except Exception as e:
        logger.exception(f"Failed to start debug chain execution: {e}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


class DebugChainExecutionView(LoginRequiredMixin, DetailView):
    """Render the debug chain execution UI page."""
    model = ChainExecution
    template_name = "erp_automation/debug_chain_execution.html"
    context_object_name = "execution"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        execution = self.object
        chain = execution.chain
        ctx["chain"] = chain
        ctx["job_data"] = execution.job_data

        # Build links list for the timeline
        links = chain.links.filter(is_active=True).select_related("workflow").order_by("order")
        links_data = []
        for link in links:
            condition_value = None
            wf = link.workflow
            if wf.condition_field and execution.row_data:
                cv = execution.row_data.get(wf.condition_field, "")
                condition_value = str(cv).strip().upper() if cv else None
            steps = list(wf.get_steps_for_condition(condition_value))
            links_data.append({
                "order": link.order,
                "name": link.get_display_name(),
                "workflow_name": wf.name,
                "workflow_id": wf.pk,
                "step_count": len(steps),
                "has_precondition": bool(link.precondition_type),
                "has_condition": bool(link.condition_field and link.condition_value),
                "steps": [{"order": s.order, "name": s.name, "action_type": s.action_type} for s in steps],
            })
        ctx["all_links_json"] = json.dumps(links_data)
        return ctx


# =============================================================================
# WORKFLOW CHAIN VIEWS
# =============================================================================

class ChainListView(LoginRequiredMixin, ListView):
    """List all workflow chains."""
    model = WorkflowChain
    template_name = "erp_automation/chain_list.html"
    context_object_name = "chains"

    def get_queryset(self):
        return WorkflowChain.objects.prefetch_related("links", "executions").all()


class ChainDetailView(LoginRequiredMixin, DetailView):
    """Chain detail: links, recent executions."""
    model = WorkflowChain
    template_name = "erp_automation/chain_detail.html"
    context_object_name = "chain"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        chain = self.object
        ctx["links"] = chain.links.filter(is_active=True).select_related("workflow").order_by("order")
        ctx["recent_executions"] = chain.executions.order_by("-started_at")[:20]
        ctx["available_workflows"] = Workflow.objects.filter(
            status=WorkflowStatus.ACTIVE
        ).order_by("name")
        return ctx


class ChainExecutionDetailView(LoginRequiredMixin, DetailView):
    """Chain execution detail: progress, per-link status."""
    model = ChainExecution
    template_name = "erp_automation/chain_execution_detail.html"
    context_object_name = "execution"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        execution = self.object
        # Get all workflow executions for this chain execution, in link order
        ctx["workflow_executions"] = (
            execution.workflow_executions
            .select_related("workflow")
            .order_by("started_at")
        )
        return ctx


@login_required
@require_POST
def api_execute_chain(request, pk):
    """Launch a chain execution for an ERPJobData record.

    POST JSON: {
        "chain_id": int (required)
    }
    """
    job_data = get_object_or_404(ERPJobData, pk=pk)

    # Allow READY, ERROR, and SENT (for retrying)
    if job_data.status not in ('READY', 'ERROR', 'SENT'):
        return JsonResponse({
            "success": False,
            "message": f"Job data must be in READY, ERROR, or SENT status. Current: {job_data.get_status_display()}"
        }, status=400)

    # Get credentials
    credentials = get_credentials(request)
    if not credentials:
        return JsonResponse({
            "success": False,
            "message": "No ERP credentials set. Please set credentials first.",
            "redirect": "/erp-automation/credentials/"
        }, status=401)

    # Parse request
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    chain_id = body.get("chain_id")
    if not chain_id:
        return JsonResponse({"success": False, "message": "chain_id is required"}, status=400)

    try:
        chain = WorkflowChain.objects.get(pk=chain_id, status="active")
    except WorkflowChain.DoesNotExist:
        return JsonResponse({"success": False, "message": "Chain not found or not active."}, status=404)

    # Validate chain has links
    active_links = chain.get_active_links()
    if not active_links.exists():
        return JsonResponse({"success": False, "message": "Chain has no active links."}, status=400)

    # Create chain execution record
    chain_execution = ChainExecution.objects.create(
        chain=chain,
        job_data=job_data,
        status=ExecutionStatus.PENDING,
        total_links=active_links.count(),
        executed_by=request.user,
    )

    # Mark job as SENT
    job_data.status = 'SENT'
    job_data.save(update_fields=['status', 'updated_at'])

    # Get ERP URL from first link's workflow
    first_link = active_links.first()
    erp_url = first_link.navigate_url or first_link.workflow.target_url or ""

    # Execute chain in background thread
    def _run_chain():
        from .services.chain_executor import ChainExecutor
        executor = ChainExecutor()
        try:
            result = executor.execute_chain(
                chain=chain,
                job_data=job_data,
                credentials=credentials,
                chain_execution=chain_execution,
                erp_url=erp_url,
            )

            # Update job data status based on result
            if result.get("success"):
                job_data.status = 'COMPLETED'
                context_vars = result.get("context", {})
                if context_vars.get("item_number"):
                    job_data.item_number = context_vars["item_number"]
                job_data.save(update_fields=['status', 'item_number', 'updated_at'])
            else:
                job_data.status = 'ERROR'
                job_data.save(update_fields=['status', 'updated_at'])
        except Exception as e:
            import traceback
            logging.getLogger(__name__).error(f"Chain execution error: {traceback.format_exc()}")
            try:
                chain_execution.status = "failed"
                chain_execution.error_message = str(e)[:500]
                chain_execution.completed_at = timezone.now()
                chain_execution.save()
            except Exception:
                pass
            try:
                job_data.status = 'ERROR'
                job_data.save(update_fields=['status', 'updated_at'])
            except Exception:
                pass
        finally:
            executor.cleanup()

    thread = threading.Thread(target=_run_chain, daemon=True)
    thread.start()

    return JsonResponse({
        "success": True,
        "message": f"Chain '{chain.name}' execution started ({active_links.count()} links)",
        "chain_execution_id": chain_execution.pk,
        "redirect": f"/erp-automation/chain-executions/{chain_execution.pk}/",
    })


@login_required
@require_GET
def api_poll_chain_execution(request, pk):
    """Poll chain execution status."""
    try:
        execution = ChainExecution.objects.get(pk=pk)
    except ChainExecution.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    # Get per-link workflow execution status
    wf_executions = []
    for wfe in execution.workflow_executions.select_related("workflow").order_by("started_at"):
        wf_executions.append({
            "workflow_name": wfe.workflow.name,
            "status": wfe.status,
            "started_at": wfe.started_at.isoformat() if wfe.started_at else None,
            "completed_at": wfe.completed_at.isoformat() if wfe.completed_at else None,
            "error_message": wfe.error_message[:200] if wfe.error_message else "",
        })

    return JsonResponse({
        "status": execution.status,
        "total_links": execution.total_links,
        "completed_links": execution.completed_links,
        "current_link_order": execution.current_link_order,
        "progress_percent": execution.progress_percent,
        "error_message": execution.error_message[:300] if execution.error_message else "",
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "workflow_executions": wf_executions,
    })


# =============================================================================
# CHAIN BUILDER UI
# =============================================================================

class ChainCreateView(LoginRequiredMixin, View):
    """Create a new workflow chain via the builder UI."""

    def get(self, request):
        context = {
            "chain": None,
            "existing_links_json": "[]",
        }
        return render(request, "erp_automation/chain_builder.html", context)


class ChainEditView(LoginRequiredMixin, View):
    """Edit an existing workflow chain via the builder UI."""

    def get(self, request, pk):
        chain = get_object_or_404(WorkflowChain, pk=pk)
        links = chain.links.filter(is_active=True).select_related("workflow").order_by("order")

        links_data = []
        for link in links:
            links_data.append({
                "link_id": link.pk,
                "workflow_id": link.workflow_id,
                "workflow_name": link.workflow.name,
                "workflow_status": link.workflow.status,
                "step_count": link.workflow.steps.filter(is_active=True).count(),
                "name": link.name or "",
                "wait_before_ms": link.wait_before_ms,
                "navigate_url": link.navigate_url or "",
                "condition_field": link.condition_field or "",
                "condition_value": link.condition_value or "",
                "context_mapping": link.context_mapping or {},
                "precondition_type": link.precondition_type or "",
                "precondition_selector": link.precondition_selector or "",
                "precondition_value": link.precondition_value or "",
                "skip_if_found": link.skip_if_found,
                "precondition_timeout_ms": link.precondition_timeout_ms,
                "is_active": link.is_active,
            })

        context = {
            "chain": chain,
            "existing_links_json": json.dumps(links_data),
        }
        return render(request, "erp_automation/chain_builder.html", context)


@login_required
@require_GET
def api_chain_segments(request):
    """Return list of active workflows as segments for the chain builder.

    GET /erp-automation/api/chains/segments/
    Returns: { segments: [ { id, name, description, status, step_count, used_count } ] }
    """
    workflows = Workflow.objects.filter(
        status__in=[WorkflowStatus.ACTIVE, WorkflowStatus.DRAFT]
    ).order_by("name")

    segments = []
    for wf in workflows:
        segments.append({
            "id": wf.pk,
            "name": wf.name,
            "description": wf.description or "",
            "status": wf.status,
            "step_count": wf.steps.filter(is_active=True).count(),
            "used_count": WorkflowChainLink.objects.filter(
                workflow=wf, is_active=True
            ).count(),
        })

    return JsonResponse({"segments": segments})


@login_required
@require_POST
def api_chain_create(request):
    """Create a new workflow chain from builder data.

    POST /erp-automation/api/chains/create/
    Body: { name, description, status, condition_field, stop_on_failure,
            keep_browser_open, links: [...] }
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    name = body.get("name", "").strip()
    if not name:
        return JsonResponse({"success": False, "message": "Chain name is required."}, status=400)

    # Check for duplicate name
    if WorkflowChain.objects.filter(name=name).exists():
        return JsonResponse({
            "success": False,
            "message": f"A chain with name '{name}' already exists."
        }, status=400)

    # Validate links
    links_data = body.get("links", [])
    if not links_data:
        return JsonResponse({"success": False, "message": "At least one link is required."}, status=400)

    # Validate all workflow IDs exist
    wf_ids = [l.get("workflow_id") for l in links_data]
    existing_wfs = set(Workflow.objects.filter(pk__in=wf_ids).values_list("pk", flat=True))
    for wf_id in wf_ids:
        if wf_id not in existing_wfs:
            return JsonResponse({
                "success": False,
                "message": f"Workflow #{wf_id} not found."
            }, status=400)

    # Create chain
    chain = WorkflowChain.objects.create(
        name=name,
        description=body.get("description", ""),
        status=body.get("status", "draft"),
        condition_field=body.get("condition_field", ""),
        stop_on_failure=body.get("stop_on_failure", True),
        keep_browser_open=body.get("keep_browser_open", True),
        created_by=request.user,
    )

    # Create links
    for link_data in links_data:
        context_mapping = link_data.get("context_mapping", {})
        if isinstance(context_mapping, str):
            try:
                context_mapping = json.loads(context_mapping)
            except (json.JSONDecodeError, TypeError):
                context_mapping = {}

        WorkflowChainLink.objects.create(
            chain=chain,
            workflow_id=link_data["workflow_id"],
            order=link_data.get("order", 10),
            name=link_data.get("name", ""),
            wait_before_ms=link_data.get("wait_before_ms", 2000),
            navigate_url=link_data.get("navigate_url", ""),
            condition_field=link_data.get("condition_field", ""),
            condition_value=link_data.get("condition_value", ""),
            context_mapping=context_mapping,
            precondition_type=link_data.get("precondition_type", ""),
            precondition_selector=link_data.get("precondition_selector", ""),
            precondition_value=link_data.get("precondition_value", ""),
            skip_if_found=link_data.get("skip_if_found", True),
            precondition_timeout_ms=link_data.get("precondition_timeout_ms", 5000),
            is_active=link_data.get("is_active", True),
        )

    return JsonResponse({
        "success": True,
        "chain_id": chain.pk,
        "message": f"Chain '{chain.name}' created with {len(links_data)} links.",
    })


@login_required
@require_POST
def api_chain_save(request, pk):
    """Update an existing workflow chain from builder data.

    POST /erp-automation/api/chains/<pk>/save/
    Body: { name, description, status, condition_field, stop_on_failure,
            keep_browser_open, links: [...] }
    """
    chain = get_object_or_404(WorkflowChain, pk=pk)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    name = body.get("name", "").strip()
    if not name:
        return JsonResponse({"success": False, "message": "Chain name is required."}, status=400)

    # Check for duplicate name (excluding current chain)
    if WorkflowChain.objects.filter(name=name).exclude(pk=pk).exists():
        return JsonResponse({
            "success": False,
            "message": f"Another chain with name '{name}' already exists."
        }, status=400)

    # Validate links
    links_data = body.get("links", [])
    if not links_data:
        return JsonResponse({"success": False, "message": "At least one link is required."}, status=400)

    # Validate all workflow IDs exist
    wf_ids = [l.get("workflow_id") for l in links_data]
    existing_wfs = set(Workflow.objects.filter(pk__in=wf_ids).values_list("pk", flat=True))
    for wf_id in wf_ids:
        if wf_id not in existing_wfs:
            return JsonResponse({
                "success": False,
                "message": f"Workflow #{wf_id} not found."
            }, status=400)

    # Update chain properties
    chain.name = name
    chain.description = body.get("description", "")
    chain.status = body.get("status", chain.status)
    chain.condition_field = body.get("condition_field", "")
    chain.stop_on_failure = body.get("stop_on_failure", True)
    chain.keep_browser_open = body.get("keep_browser_open", True)
    chain.save()

    # Delete existing links and recreate
    chain.links.all().delete()

    for link_data in links_data:
        context_mapping = link_data.get("context_mapping", {})
        if isinstance(context_mapping, str):
            try:
                context_mapping = json.loads(context_mapping)
            except (json.JSONDecodeError, TypeError):
                context_mapping = {}

        WorkflowChainLink.objects.create(
            chain=chain,
            workflow_id=link_data["workflow_id"],
            order=link_data.get("order", 10),
            name=link_data.get("name", ""),
            wait_before_ms=link_data.get("wait_before_ms", 2000),
            navigate_url=link_data.get("navigate_url", ""),
            condition_field=link_data.get("condition_field", ""),
            condition_value=link_data.get("condition_value", ""),
            context_mapping=context_mapping,
            precondition_type=link_data.get("precondition_type", ""),
            precondition_selector=link_data.get("precondition_selector", ""),
            precondition_value=link_data.get("precondition_value", ""),
            skip_if_found=link_data.get("skip_if_found", True),
            precondition_timeout_ms=link_data.get("precondition_timeout_ms", 5000),
            is_active=link_data.get("is_active", True),
        )

    return JsonResponse({
        "success": True,
        "chain_id": chain.pk,
        "message": f"Chain '{chain.name}' updated with {len(links_data)} links.",
    })


@login_required
@require_POST
def api_chain_delete(request, pk):
    """Delete a workflow chain.

    POST /erp-automation/api/chains/<pk>/delete/
    """
    chain = get_object_or_404(WorkflowChain, pk=pk)

    # Check if chain has any executions
    exec_count = chain.executions.count()
    if exec_count > 0:
        # Soft-delete by archiving
        chain.status = "archived"
        chain.save(update_fields=["status", "updated_at"])
        return JsonResponse({
            "success": True,
            "message": f"Chain '{chain.name}' archived (has {exec_count} execution records).",
        })
    else:
        chain_name = chain.name
        chain.delete()
        return JsonResponse({
            "success": True,
            "message": f"Chain '{chain_name}' deleted.",
        })


# =============================================================================
# WORKFLOW STEP & LOCATOR CRUD APIs
# =============================================================================

@login_required
@require_POST
def api_step_create(request, wf_pk):
    """Create a new workflow step."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    workflow = get_object_or_404(Workflow, pk=wf_pk)
    order = data.get("order")
    if not order:
        last = workflow.steps.order_by("-order").first()
        order = (last.order + 1) if last else 10

    # Resolve or create locator
    locator = None
    locator_id = data.get("locator_id")
    if locator_id:
        locator = Locator.objects.filter(pk=locator_id).first()
    elif data.get("locator_name"):
        locator, _ = Locator.objects.get_or_create(
            name=data["locator_name"],
            defaults={"application": "dynamics365", "is_dynamic": True},
        )

    step = WorkflowStep.objects.create(
        workflow=workflow,
        order=int(order),
        name=data.get("name", "New Step"),
        action_type=data.get("action_type", "click"),
        locator=locator,
        value_static=data.get("value_static", ""),
        value_field=data.get("value_field", ""),
        value_template=data.get("value_template", ""),
        condition_value=data.get("condition_value", ""),
        wait_after=int(data.get("wait_after", 500)),
        timeout=int(data.get("timeout", 30000)),
        continue_on_error=data.get("continue_on_error", False),
        check_for_errors=data.get("check_for_errors", False),
        press_key_after=data.get("press_key_after", ""),
        clear_before_fill=data.get("clear_before_fill", False),
        interaction_mode=data.get("interaction_mode", "auto"),
    )
    return JsonResponse({
        "success": True,
        "step_id": step.pk,
        "message": f"Step {step.order} created",
    })


@login_required
@require_POST
def api_step_update(request, wf_pk, step_pk):
    """Update an existing workflow step."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    step = get_object_or_404(WorkflowStep, pk=step_pk, workflow_id=wf_pk)

    # Update fields if provided
    for field in ["name", "action_type", "value_static", "value_field",
                  "value_template", "condition_value", "press_key_after",
                  "interaction_mode"]:
        if field in data:
            setattr(step, field, data[field])

    for int_field in ["order", "wait_after", "timeout"]:
        if int_field in data:
            setattr(step, int_field, int(data[int_field]))

    for bool_field in ["continue_on_error", "check_for_errors", "clear_before_fill", "is_active"]:
        if bool_field in data:
            setattr(step, bool_field, data[bool_field])

    # Handle locator change
    if "locator_id" in data:
        lid = data["locator_id"]
        step.locator = Locator.objects.filter(pk=lid).first() if lid else None

    step.save()
    return JsonResponse({"success": True, "message": f"Step {step.order} updated"})


@login_required
@require_POST
def api_step_delete(request, wf_pk, step_pk):
    """Delete a workflow step."""
    step = get_object_or_404(WorkflowStep, pk=step_pk, workflow_id=wf_pk)
    order = step.order
    step.delete()
    return JsonResponse({"success": True, "message": f"Step {order} deleted"})


@login_required
@require_POST
def api_locator_create(request):
    """Create a new locator with strategies."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    name = data.get("name", "").strip()
    if not name:
        return JsonResponse({"success": False, "message": "Name required"}, status=400)

    if Locator.objects.filter(name=name).exists():
        return JsonResponse({"success": False, "message": f"Locator '{name}' already exists"}, status=400)

    loc = Locator.objects.create(
        name=name,
        application=data.get("application", "dynamics365"),
        page_context=data.get("page_context", ""),
        is_dynamic=data.get("is_dynamic", True),
        default_timeout=int(data.get("default_timeout", 30000)),
    )

    # Create strategies
    for s in data.get("strategies", []):
        LocatorStrategy.objects.create(
            locator=loc,
            strategy_type=s.get("strategy_type", "xpath"),
            value=s.get("value", ""),
            priority=int(s.get("priority", 0)),
        )

    return JsonResponse({
        "success": True,
        "locator_id": loc.pk,
        "message": f"Locator '{name}' created with {loc.strategies.count()} strategies",
    })


@login_required
@require_POST
def api_locator_update(request, pk):
    """Update a locator and its strategies."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    loc = get_object_or_404(Locator, pk=pk)

    for field in ["name", "application", "page_context"]:
        if field in data:
            setattr(loc, field, data[field])
    for bool_field in ["is_dynamic"]:
        if bool_field in data:
            setattr(loc, bool_field, data[bool_field])
    if "default_timeout" in data:
        loc.default_timeout = int(data["default_timeout"])
    loc.save()

    # Replace strategies if provided
    if "strategies" in data:
        loc.strategies.all().delete()
        for s in data["strategies"]:
            LocatorStrategy.objects.create(
                locator=loc,
                strategy_type=s.get("strategy_type", "xpath"),
                value=s.get("value", ""),
                priority=int(s.get("priority", 0)),
            )

    return JsonResponse({
        "success": True,
        "message": f"Locator '{loc.name}' updated ({loc.strategies.count()} strategies)",
    })


@login_required
@require_GET
def api_locator_search(request):
    """Search locators by name for autocomplete."""
    q = request.GET.get("q", "").strip()
    locators = Locator.objects.all().order_by("name")
    if q:
        locators = locators.filter(name__icontains=q)
    results = [
        {"id": l.pk, "name": l.name, "strategies": l.strategies.count()}
        for l in locators[:30]
    ]
    return JsonResponse({"results": results})


@login_required
@require_GET
def api_locator_detail(request, pk):
    """Get full locator details with strategies."""
    loc = get_object_or_404(Locator, pk=pk)
    strategies = [
        {
            "id": s.pk,
            "strategy_type": s.strategy_type,
            "value": s.value,
            "priority": s.priority,
            "success_count": s.success_count,
            "failure_count": s.failure_count,
        }
        for s in loc.strategies.all().order_by("priority")
    ]
    return JsonResponse({
        "id": loc.pk,
        "name": loc.name,
        "application": loc.application,
        "page_context": loc.page_context,
        "is_dynamic": loc.is_dynamic,
        "default_timeout": loc.default_timeout,
        "strategies": strategies,
    })


@login_required
@require_GET
def api_workflow_steps(request, wf_pk):
    """Get all steps for a workflow as JSON."""
    workflow = get_object_or_404(Workflow, pk=wf_pk)
    steps = []
    for s in workflow.steps.filter(is_active=True).order_by("order"):
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
        steps.append({
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
        })
    return JsonResponse({"steps": steps})
