from django.contrib import admin

from .models import (
    AuditLog, Comment, FormRevision, Notification, NotificationTemplate, Task,
    WorkflowRule, WorkflowAction,
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "channel", "is_active"]
    list_filter = ["channel", "is_active"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "recipient", "priority", "is_read", "created_at"]
    list_filter = ["priority", "is_read"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "assigned_to", "status", "priority", "due_date"]
    list_filter = ["status", "priority"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "entity_type", "user", "created_at"]
    list_filter = ["action", "entity_type"]
    readonly_fields = ["user", "action", "entity_type", "entity_id", "old_values", "new_values", "diff", "created_at"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["entity_type", "entity_id", "created_by", "created_at"]
    list_filter = ["entity_type"]


@admin.register(FormRevision)
class FormRevisionAdmin(admin.ModelAdmin):
    list_display = ["entity_type", "entity_id", "revision_number", "document_code", "revised_by", "revised_at"]
    list_filter = ["entity_type", "document_code"]
    readonly_fields = ["snapshot", "changes"]


@admin.register(WorkflowRule)
class WorkflowRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "trigger_event", "rule_type", "action_type", "assign_to_role", "notif_priority", "is_active", "order"]
    list_filter = ["trigger_event", "rule_type", "is_active", "assign_to_role"]
    search_fields = ["name", "description"]
    list_editable = ["is_active", "order"]


@admin.register(WorkflowAction)
class WorkflowActionAdmin(admin.ModelAdmin):
    list_display = ["title", "action_type", "assigned_to", "assigned_role", "status", "priority", "is_blocked", "due_date", "created_at"]
    list_filter = ["status", "action_type", "assigned_role", "priority", "is_blocked"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "updated_at"]


