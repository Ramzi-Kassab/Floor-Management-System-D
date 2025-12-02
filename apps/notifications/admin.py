from django.contrib import admin

from .models import AuditLog, Comment, Notification, NotificationTemplate, Task


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
