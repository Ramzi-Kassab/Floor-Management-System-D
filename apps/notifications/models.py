"""
ARDT FMS - Notifications Models
Version: 5.4

Tables:
- notification_templates (P1)
- notifications (P1)
- notification_logs (P1)
- tasks (P1)
- audit_logs (P1)
- comments (P1)
- comment_attachments (P1)
"""

from django.db import models
from django.conf import settings


class NotificationTemplate(models.Model):
    """
    🟢 P1: Templates for notifications.
    """
    
    class Channel(models.TextChoices):
        IN_APP = 'IN_APP', 'In-App'
        EMAIL = 'EMAIL', 'Email'
        SMS = 'SMS', 'SMS'
        PUSH = 'PUSH', 'Push Notification'
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    channel = models.CharField(max_length=20, choices=Channel.choices)
    
    subject = models.CharField(max_length=200)
    body_template = models.TextField(help_text='Supports {{variable}} placeholders')
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'notification_templates'
        ordering = ['code']
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Notification(models.Model):
    """
    🟢 P1: User notifications.
    """
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    
    # Link to related entity
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.BigIntegerField(null=True, blank=True)
    action_url = models.CharField(max_length=500, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.title} -> {self.recipient}"


class NotificationLog(models.Model):
    """
    🟢 P1: Log of notification delivery attempts.
    """
    
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    channel = models.CharField(max_length=20)
    
    sent_at = models.DateTimeField(auto_now_add=True)
    is_delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'notification_logs'
        ordering = ['-sent_at']
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'


class Task(models.Model):
    """
    🟢 P1: Lightweight task/reminder system.
    """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_tasks'
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks'
    )
    
    # Dates
    due_date = models.DateTimeField(null=True, blank=True)
    reminder_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    
    # Link to entity
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.BigIntegerField(null=True, blank=True)
    
    # Completion
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tasks'
        ordering = ['due_date', '-priority']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
    
    def __str__(self):
        return self.title


class AuditLog(models.Model):
    """
    🟢 P1: Full audit trail with JSON diff.
    """
    
    class Action(models.TextChoices):
        CREATE = 'CREATE', 'Create'
        UPDATE = 'UPDATE', 'Update'
        DELETE = 'DELETE', 'Delete'
        VIEW = 'VIEW', 'View'
        EXPORT = 'EXPORT', 'Export'
        LOGIN = 'LOGIN', 'Login'
        LOGOUT = 'LOGOUT', 'Logout'
    
    # Who
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    
    # What
    action = models.CharField(max_length=20, choices=Action.choices)
    entity_type = models.CharField(max_length=100)
    entity_id = models.BigIntegerField(null=True, blank=True)
    entity_repr = models.CharField(max_length=500, blank=True, help_text='String representation')
    
    # Changes
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    diff = models.JSONField(null=True, blank=True, help_text='Computed difference')
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} {self.entity_type} by {self.user}"


class Comment(models.Model):
    """
    🟢 P1: Universal commenting system.
    """
    
    # What is being commented on
    entity_type = models.CharField(max_length=100)
    entity_id = models.BigIntegerField()
    
    # Content
    content = models.TextField()
    
    # Threading
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    # Mentions
    mentioned_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='mentioned_in_comments'
    )
    
    # Author
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='comments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Edit tracking
    is_edited = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'comments'
        ordering = ['created_at']
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
        ]
    
    def __str__(self):
        return f"Comment by {self.created_by} on {self.entity_type}"


class CommentAttachment(models.Model):
    """
    🟢 P1: Attachments for comments.
    """
    
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='comment_attachments/')
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comment_attachments'
        verbose_name = 'Comment Attachment'
        verbose_name_plural = 'Comment Attachments'
