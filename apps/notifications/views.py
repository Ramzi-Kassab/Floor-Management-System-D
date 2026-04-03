"""
ARDT FMS - Notifications App Views
Version: 5.4
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import CommentForm, NotificationTemplateForm, TaskForm, TaskStatusForm
from .models import AuditLog, Comment, Notification, NotificationTemplate, Task
from .services import get_recent_unread, get_unread_count


# =============================================================================
# Notification Views
# =============================================================================


class NotificationListView(LoginRequiredMixin, ListView):
    """List user's notifications."""

    model = Notification
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        qs = Notification.objects.filter(recipient=self.request.user).select_related("template")

        # Filter by read status
        is_read = self.request.GET.get("is_read")
        if is_read == "true":
            qs = qs.filter(is_read=True)
        elif is_read == "false":
            qs = qs.filter(is_read=False)

        # Filter by priority
        priority = self.request.GET.get("priority")
        if priority:
            qs = qs.filter(priority=priority)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Notifications"
        context["unread_count"] = Notification.objects.filter(recipient=self.request.user, is_read=False).count()
        context["priority_choices"] = Notification.Priority.choices
        context["current_priority"] = self.request.GET.get("priority", "")
        context["current_is_read"] = self.request.GET.get("is_read", "")
        return context


class NotificationMarkReadView(LoginRequiredMixin, View):
    """Mark a notification as read without navigating away.
    GET and POST both mark as read. Neither consumes the action_url —
    the notification stays clickable via its action_url at any time."""

    def get(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        # Redirect back to where the user came from (or notification list)
        referer = request.META.get("HTTP_REFERER", "")
        if referer:
            return redirect(referer)
        return redirect("notifications:notification_list")

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"status": "ok"})
        referer = request.META.get("HTTP_REFERER", "")
        if referer:
            return redirect(referer)
        return redirect("notifications:notification_list")


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    """Mark all notifications as read."""

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
        messages.success(request, "All notifications marked as read.")
        return redirect("notifications:notification_list")


class NotificationDeleteView(LoginRequiredMixin, View):
    """Delete a notification."""

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.delete()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"status": "ok"})

        messages.success(request, "Notification deleted.")
        return redirect("notifications:notification_list")


# =============================================================================
# Bell Fragment View (HTMX polling)
# =============================================================================


class NotificationBellView(LoginRequiredMixin, View):
    """
    Returns the bell dropdown HTML fragment for HTMX polling.
    Called every 10s from the topnav.
    """

    def get(self, request):
        from django.template.loader import render_to_string

        # Passive escalation check on each poll
        try:
            from apps.notifications.workflow_engine import check_and_escalate_overdue_actions
            check_and_escalate_overdue_actions()
        except Exception:
            pass

        unread_count = get_unread_count(request.user)
        recent = get_recent_unread(request.user, limit=5)
        latest_id = recent[0].pk if recent else ""
        read_recent = Notification.objects.filter(
            recipient=request.user, is_read=True
        ).order_by('-created_at')[:5]

        # Pending workflow actions for this user
        pending_actions = []
        pending_action_count = 0
        try:
            from apps.notifications.workflow_engine import get_pending_actions_for_user
            pending_actions = list(get_pending_actions_for_user(request.user)[:5])
            pending_action_count = get_pending_actions_for_user(request.user).count()
        except Exception:
            pass

        html = render_to_string(
            "notifications/partials/bell_fragment.html",
            {
                "unread_count": unread_count,
                "recent_notifications": recent,
                "read_notifications": read_recent,
                "latest_id": latest_id,
                "pending_actions": pending_actions,
                "pending_action_count": pending_action_count,
            },
            request=request,
        )
        from django.http import HttpResponse

        return HttpResponse(html)


class ApiMarkReadView(LoginRequiredMixin, View):
    """Mark a single notification as read. Returns 204 for HTMX."""

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])

        from django.http import HttpResponse

        return HttpResponse(status=204)


class ApiMarkAllReadView(LoginRequiredMixin, View):
    """Mark all unread notifications as read. Returns 204 for HTMX."""

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )

        from django.http import HttpResponse

        return HttpResponse(status=204)


class ClearReadNotificationsView(LoginRequiredMixin, View):
    """Delete all read notifications for the current user."""

    def post(self, request):
        deleted = Notification.objects.filter(
            recipient=request.user, is_read=True
        ).delete()
        return JsonResponse({'success': True, 'deleted': deleted[0]})


class NotificationSettingsView(LoginRequiredMixin, View):
    """Notification preferences page — delivery, muted action/entity types."""

    def get(self, request):
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from .models import ActionType

        prefs = self._get_prefs(request.user)

        # All action types and entity types for toggles
        action_types = ActionType.choices
        entity_types = [
            ('WorkOrder', 'Work Orders'),
            ('DrillBit', 'Drill Bits'),
            ('RouterSheetEntry', 'Router Steps'),
            ('CutterEvaluationMatrix', 'Evaluations'),
            ('ReceivingInspection', 'Receiving Inspections'),
            ('DieCheckReport', 'Die Check Reports'),
            ('StandaloneLPTReport', 'LPT Reports'),
        ]

        from django.shortcuts import render
        return render(request, 'notifications/notification_settings.html', {
            'page_title': 'Notification Settings',
            'prefs': prefs,
            'action_types': action_types,
            'entity_types': entity_types,
            'muted_actions': prefs.get('muted_action_types', []),
            'muted_entities': prefs.get('muted_entity_types', []),
            'sound_prefs': prefs.get('sound', {}),
            'auto_mark_read': prefs.get('auto_mark_read', 'never'),
        })

    def post(self, request):
        import json as _j
        section = request.POST.get('section', '')
        prefs = self._get_prefs(request.user)

        if section == 'muted_actions':
            muted = request.POST.getlist('muted_actions')
            prefs['muted_action_types'] = muted
        elif section == 'muted_entities':
            muted = request.POST.getlist('muted_entities')
            prefs['muted_entity_types'] = muted
        elif section == 'sound':
            for level in ('LOW', 'NORMAL', 'HIGH', 'URGENT'):
                prefs.setdefault('sound', {})[level] = request.POST.get(f'sound_{level}') == 'on'
        elif section == 'auto_mark_read':
            prefs['auto_mark_read'] = request.POST.get('auto_mark_read', 'never')

        self._save_prefs(request.user, prefs)
        return JsonResponse({'success': True, 'saved': section})

    def _get_prefs(self, user):
        try:
            wp = user.preferences
            return (wp.dashboard_widgets or {}).get('notification_prefs', {})
        except Exception:
            return {}

    def _save_prefs(self, user, prefs):
        from apps.accounts.models import UserPreference
        wp, _ = UserPreference.objects.get_or_create(user=user)
        widgets = wp.dashboard_widgets or {}
        widgets['notification_prefs'] = prefs
        wp.dashboard_widgets = widgets
        wp.save(update_fields=['dashboard_widgets'])


# =============================================================================
# Task Views
# =============================================================================


class TaskListView(LoginRequiredMixin, ListView):
    """List tasks assigned to user or created by user."""

    model = Task
    template_name = "notifications/task_list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self):
        view_type = self.request.GET.get("view", "assigned")

        if view_type == "created":
            qs = Task.objects.filter(assigned_by=self.request.user)
        else:
            qs = Task.objects.filter(assigned_to=self.request.user)

        qs = qs.select_related("assigned_to", "assigned_by")

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        # Filter by priority
        priority = self.request.GET.get("priority")
        if priority:
            qs = qs.filter(priority=priority)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Tasks"
        context["status_choices"] = Task.Status.choices
        context["priority_choices"] = Task.Priority.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["current_priority"] = self.request.GET.get("priority", "")
        context["current_view"] = self.request.GET.get("view", "assigned")

        # Counts
        context["pending_count"] = Task.objects.filter(assigned_to=self.request.user, status=Task.Status.PENDING).count()
        context["in_progress_count"] = Task.objects.filter(
            assigned_to=self.request.user, status=Task.Status.IN_PROGRESS
        ).count()

        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    """View task details."""

    model = Task
    template_name = "notifications/task_detail.html"
    context_object_name = "task"

    def get_queryset(self):
        return Task.objects.select_related("assigned_to", "assigned_by")


class TaskCreateView(LoginRequiredMixin, CreateView):
    """Create a new task."""

    model = Task
    form_class = TaskForm
    template_name = "notifications/task_form.html"
    success_url = reverse_lazy("notifications:task_list")

    def form_valid(self, form):
        form.instance.assigned_by = self.request.user
        messages.success(self.request, "Task created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Task"
        context["form_title"] = "Create New Task"
        return context


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """Update task details."""

    model = Task
    form_class = TaskForm
    template_name = "notifications/task_form.html"
    success_url = reverse_lazy("notifications:task_list")

    def form_valid(self, form):
        messages.success(self.request, "Task updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Task"
        context["form_title"] = "Edit Task"
        return context


class TaskStatusUpdateView(LoginRequiredMixin, View):
    """Quick status update for task."""

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)

        # Allow only assignee or creator to update
        if request.user not in [task.assigned_to, task.assigned_by]:
            messages.error(request, "You don't have permission to update this task.")
            return redirect("notifications:task_list")

        new_status = request.POST.get("status")
        if new_status in dict(Task.Status.choices):
            task.status = new_status
            if new_status == Task.Status.COMPLETED:
                task.completed_at = timezone.now()
            task.save()
            messages.success(request, f"Task status updated to {task.get_status_display()}.")

        return redirect("notifications:task_detail", pk=pk)


class TaskCompleteView(LoginRequiredMixin, View):
    """Mark task as completed."""

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
        task.status = Task.Status.COMPLETED
        task.completed_at = timezone.now()
        task.save()
        messages.success(request, "Task marked as completed.")
        return redirect("notifications:task_list")


# =============================================================================
# Notification Template Views
# =============================================================================


class NotificationTemplateListView(LoginRequiredMixin, ListView):
    """List notification templates (admin only)."""

    model = NotificationTemplate
    template_name = "notifications/template_list.html"
    context_object_name = "templates"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Notification Templates"
        return context


class NotificationTemplateCreateView(LoginRequiredMixin, CreateView):
    """Create notification template."""

    model = NotificationTemplate
    form_class = NotificationTemplateForm
    template_name = "notifications/template_form.html"
    success_url = reverse_lazy("notifications:template_list")

    def form_valid(self, form):
        messages.success(self.request, "Template created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Template"
        context["form_title"] = "Create Notification Template"
        return context


class NotificationTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Update notification template."""

    model = NotificationTemplate
    form_class = NotificationTemplateForm
    template_name = "notifications/template_form.html"
    success_url = reverse_lazy("notifications:template_list")

    def form_valid(self, form):
        messages.success(self.request, "Template updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Edit Template"
        context["form_title"] = "Edit Notification Template"
        return context


# =============================================================================
# Audit Log Views
# =============================================================================


class AuditLogListView(LoginRequiredMixin, ListView):
    """List audit logs (admin only)."""

    model = AuditLog
    template_name = "notifications/audit_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user")

        # Filter by action
        action = self.request.GET.get("action")
        if action:
            qs = qs.filter(action=action)

        # Filter by entity type
        entity_type = self.request.GET.get("entity_type")
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Audit Logs"
        context["action_choices"] = AuditLog.Action.choices
        context["current_action"] = self.request.GET.get("action", "")
        context["current_entity_type"] = self.request.GET.get("entity_type", "")

        # Get distinct entity types
        context["entity_types"] = AuditLog.objects.values_list("entity_type", flat=True).distinct()

        return context


class AuditLogDetailView(LoginRequiredMixin, DetailView):
    """View audit log details."""

    model = AuditLog
    template_name = "notifications/audit_detail.html"
    context_object_name = "log"

    def get_queryset(self):
        return AuditLog.objects.select_related("user")


# =============================================================================
# Comment Views (HTMX compatible)
# =============================================================================


class CommentListView(LoginRequiredMixin, View):
    """List comments for an entity (HTMX partial)."""

    def get(self, request, entity_type, entity_id):
        comments = Comment.objects.filter(entity_type=entity_type, entity_id=entity_id, parent__isnull=True).select_related(
            "created_by"
        ).prefetch_related("replies", "replies__created_by")

        from django.template.loader import render_to_string

        html = render_to_string(
            "notifications/partials/comment_list.html",
            {"comments": comments, "entity_type": entity_type, "entity_id": entity_id},
            request=request,
        )

        return JsonResponse({"html": html})


class CommentCreateView(LoginRequiredMixin, View):
    """Create a comment (HTMX)."""

    def post(self, request, entity_type, entity_id):
        content = request.POST.get("content", "").strip()
        parent_id = request.POST.get("parent_id")

        if not content:
            return JsonResponse({"error": "Comment cannot be empty"}, status=400)

        comment = Comment.objects.create(
            entity_type=entity_type,
            entity_id=entity_id,
            content=content,
            parent_id=parent_id if parent_id else None,
            created_by=request.user,
        )

        from django.template.loader import render_to_string

        html = render_to_string(
            "notifications/partials/comment_item.html",
            {"comment": comment},
            request=request,
        )

        return JsonResponse({"html": html, "id": comment.id})


class CommentDeleteView(LoginRequiredMixin, View):
    """Delete a comment."""

    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)

        # Only author can delete
        if comment.created_by != request.user:
            return JsonResponse({"error": "Permission denied"}, status=403)

        comment.delete()
        return JsonResponse({"status": "ok"})


# =============================================================================
# WORKFLOW ENGINE VIEWS
# =============================================================================

class ActionCenterView(LoginRequiredMixin, ListView):
    """Action Center — My Actions, Team Actions, History."""
    template_name = "notifications/action_center.html"
    context_object_name = "actions"
    paginate_by = 30

    def get_queryset(self):
        from .models import WorkflowAction
        from apps.accounts.models import UserRole
        from django.db.models import Q

        tab = self.request.GET.get('tab', 'my')
        user = self.request.user

        user_role_ids = list(
            UserRole.objects.filter(
                user=user, is_available=True,
            ).filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            ).values_list('role_id', flat=True)
        )

        if tab == 'history':
            return WorkflowAction.objects.filter(
                Q(assigned_to=user) | Q(completed_by=user) | Q(claimed_by=user)
            ).filter(
                status__in=['COMPLETED', 'CANCELLED', 'EXPIRED']
            ).select_related('assigned_to', 'completed_by', 'source_rule').order_by('-completed_at')

        elif tab == 'team':
            if not user_role_ids:
                return WorkflowAction.objects.none()
            return WorkflowAction.objects.filter(
                assigned_role_id__in=user_role_ids,
                status__in=['PENDING', 'CLAIMED', 'IN_PROGRESS', 'ESCALATED'],
            ).select_related('assigned_to', 'claimed_by', 'source_rule').order_by('is_blocked', 'due_date', '-priority')

        else:  # 'my'
            return WorkflowAction.objects.filter(
                Q(assigned_to=user) |
                Q(assigned_role_id__in=user_role_ids, is_queue_action=True,
                  claimed_by__isnull=True, assigned_to__isnull=True)
            ).filter(
                status__in=['PENDING', 'CLAIMED', 'IN_PROGRESS', 'ESCALATED'],
                is_blocked=False,
            ).select_related('assigned_to', 'claimed_by', 'source_rule').order_by('due_date', '-priority')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import WorkflowAction, ActionType
        from apps.accounts.models import UserRole

        user = self.request.user
        user_role_ids = list(
            UserRole.objects.filter(
                user=user, is_available=True,
            ).filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            ).values_list('role_id', flat=True)
        )

        ctx['current_tab'] = self.request.GET.get('tab', 'my')
        ctx['page_title'] = 'Action Center'

        my_q = Q(assigned_to=user) | Q(
            assigned_role_id__in=user_role_ids, is_queue_action=True,
            claimed_by__isnull=True, assigned_to__isnull=True
        )
        ctx['my_count'] = WorkflowAction.objects.filter(my_q).filter(
            status__in=['PENDING', 'CLAIMED', 'IN_PROGRESS', 'ESCALATED'],
            is_blocked=False,
        ).count()
        ctx['team_count'] = WorkflowAction.objects.filter(
            assigned_role_id__in=user_role_ids,
            status__in=['PENDING', 'CLAIMED', 'IN_PROGRESS', 'ESCALATED'],
        ).count() if user_role_ids else 0

        ctx['action_types'] = ActionType.choices
        return ctx


class WorkflowSettingsIndexView(LoginRequiredMixin, ListView):
    """Workflow Settings index — entry point for admin configuration."""
    template_name = "notifications/workflow_settings.html"
    context_object_name = "rules"

    def get_queryset(self):
        from .models import WorkflowRule
        return WorkflowRule.objects.all().order_by('trigger_event', 'order')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import WorkflowRule, WorkflowAction, WorkflowEvent
        from django.conf import settings as django_settings

        ctx['page_title'] = 'Workflow Settings'
        ctx['engine_active'] = getattr(django_settings, 'WORKFLOW_ENGINE_ACTIVE', False)
        ctx['total_rules'] = WorkflowRule.objects.count()
        ctx['active_rules'] = WorkflowRule.objects.filter(is_active=True).count()
        ctx['total_actions'] = WorkflowAction.objects.count()
        ctx['pending_actions'] = WorkflowAction.objects.filter(status='PENDING').count()
        from apps.accounts.models import UserRole as _UR, Role as _Role
        ctx['total_cap_assignments'] = _UR.objects.filter(is_available=True).count()
        ctx['events'] = WorkflowEvent.choices

        # Group rules by event
        from collections import defaultdict
        grouped = defaultdict(list)
        for rule in ctx['rules']:
            grouped[rule.trigger_event].append(rule)
        ctx['rules_by_event'] = dict(grouped)

        # Role coverage for workflow
        cap_counts = {}
        for role in _Role.objects.filter(is_active=True).order_by('-level'):
            cnt = _UR.objects.filter(role=role, is_available=True).count()
            cap_counts[role.code] = {'label': role.name, 'count': cnt}
        ctx['cap_counts'] = cap_counts

        return ctx


class WorkflowCapabilityView(LoginRequiredMixin, ListView):
    """Workflow role management — assign roles to users for action routing."""
    template_name = "notifications/workflow_capabilities.html"
    context_object_name = "capabilities"

    def get_queryset(self):
        from apps.accounts.models import Role
        return Role.objects.filter(is_active=True).prefetch_related(
            'user_roles', 'user_roles__user', 'positions'
        ).order_by('-level', 'name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.contrib.auth import get_user_model
        ctx['page_title'] = 'Workflow Role Assignments'
        ctx['users'] = get_user_model().objects.filter(is_active=True).order_by('first_name', 'username')
        return ctx


from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json as _json


@login_required
@require_POST
def api_capability_grant(request):
    """Grant a Role to a user (manual assignment via workflow page)."""
    from apps.accounts.models import Role, UserRole
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff access required'}, status=403)

    data = _json.loads(request.body)
    user_id = data.get('user_id')
    capability_id = data.get('capability_id')  # actually role_id

    if not user_id or not capability_id:
        return JsonResponse({'error': 'user_id and capability_id required', 'success': False})

    from django.contrib.auth import get_user_model
    try:
        user = get_user_model().objects.get(pk=user_id)
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found', 'success': False})

    try:
        role = Role.objects.get(pk=capability_id)
    except Role.DoesNotExist:
        return JsonResponse({'error': 'Role not found', 'success': False})

    obj, created = UserRole.objects.get_or_create(
        user=user, role=role,
        defaults={
            'assigned_by': request.user, 'is_available': True,
            'notes': data.get('notes', ''),
        }
    )
    if not created:
        obj.is_available = True
        obj.save(update_fields=['is_available'])

    return JsonResponse({
        'success': True,
        'message': f'{user.get_full_name() or user.username} granted {role.name}',
    })


@login_required
@require_POST
def api_capability_revoke(request, pk):
    """Revoke a role assignment."""
    from apps.accounts.models import UserRole
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff access required'}, status=403)

    try:
        obj = UserRole.objects.get(pk=pk)
    except UserRole.DoesNotExist:
        return JsonResponse({'error': 'Not found', 'success': False})

    if obj.is_position_derived:
        return JsonResponse({'error': 'Cannot revoke position-derived role. Change the position instead.', 'success': False})

    obj.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def api_capability_toggle_available(request, pk):
    """Toggle is_available on a UserRole."""
    from apps.accounts.models import UserRole
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff access required'}, status=403)

    try:
        obj = UserRole.objects.get(pk=pk)
    except UserRole.DoesNotExist:
        return JsonResponse({'error': 'Not found', 'success': False})

    obj.is_available = not obj.is_available
    obj.save(update_fields=['is_available'])
    return JsonResponse({'success': True, 'is_available': obj.is_available})


@login_required
@require_POST
def api_workflow_action_claim(request, pk):
    """Claim a queue action."""
    from .models import WorkflowAction

    try:
        action = WorkflowAction.objects.get(pk=pk)
    except WorkflowAction.DoesNotExist:
        return JsonResponse({'error': 'Action not found', 'success': False})

    if action.claimed_by and action.claimed_by != request.user:
        return JsonResponse({'error': f'Already claimed by {action.claimed_by.get_full_name()}', 'success': False})

    action.claimed_by = request.user
    action.claimed_at = timezone.now()
    action.status = WorkflowAction.Status.CLAIMED
    action.save(update_fields=['claimed_by', 'claimed_at', 'status', 'updated_at'])

    return JsonResponse({'success': True, 'message': 'Action claimed'})
