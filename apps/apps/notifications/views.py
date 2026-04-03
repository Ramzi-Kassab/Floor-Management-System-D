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
    """Mark a notification as read."""

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"status": "ok"})

        if notification.action_url:
            return redirect(notification.action_url)
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
