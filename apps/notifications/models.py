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

from django.conf import settings
from django.db import models
from django.utils import timezone


class NotificationTemplate(models.Model):
    """
    🟢 P1: Templates for notifications.
    """

    class Channel(models.TextChoices):
        IN_APP = "IN_APP", "In-App"
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"
        PUSH = "PUSH", "Push Notification"

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    channel = models.CharField(max_length=20, choices=Channel.choices)

    subject = models.CharField(max_length=200)
    body_template = models.TextField(help_text="Supports {{variable}} placeholders")

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "notification_templates"
        ordering = ["code"]
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Notification(models.Model):
    """
    🟢 P1: User notifications.
    """

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="notifications_sent",
    )

    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications")

    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)

    # Link to related entity
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.BigIntegerField(null=True, blank=True)
    action_url = models.CharField(max_length=500, blank=True)
    action_type = models.CharField(max_length=50, blank=True,
        help_text='ActionType enum value for smart button rendering')

    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"], name="notif_bell_idx"),
        ]

    def __str__(self):
        return f"{self.title} -> {self.recipient}"


class NotificationLog(models.Model):
    """
    🟢 P1: Log of notification delivery attempts.
    """

    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="logs")
    channel = models.CharField(max_length=20)

    sent_at = models.DateTimeField(auto_now_add=True)
    is_delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)

    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "notification_logs"
        ordering = ["-sent_at"]
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"

    def __str__(self):
        status = "Delivered" if self.is_delivered else "Pending"
        return f"{self.channel} - {status} at {self.sent_at}"


class Task(models.Model):
    """
    🟢 P1: Lightweight task/reminder system.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Assignment
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assigned_tasks")
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_tasks"
    )

    # Dates
    due_date = models.DateTimeField(null=True, blank=True)
    reminder_date = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)

    # Link to entity
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.BigIntegerField(null=True, blank=True)

    # Completion
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tasks"
        ordering = ["due_date", "-priority"]
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return self.title


class AuditLog(models.Model):
    """
    🟢 P1: Full audit trail with JSON diff.
    """

    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"
        VIEW = "VIEW", "View"
        EXPORT = "EXPORT", "Export"
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"

    # Who
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="audit_logs")

    # What
    action = models.CharField(max_length=20, choices=Action.choices)
    entity_type = models.CharField(max_length=100)
    entity_id = models.BigIntegerField(null=True, blank=True)
    entity_repr = models.CharField(max_length=500, blank=True, help_text="String representation")

    # Changes
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    diff = models.JSONField(null=True, blank=True, help_text="Computed difference")

    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["user", "created_at"]),
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
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")

    # Mentions
    mentioned_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="mentioned_in_comments")

    # Author
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="comments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Edit tracking
    is_edited = models.BooleanField(default=False)

    class Meta:
        db_table = "comments"
        ordering = ["created_at"]
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self):
        return f"Comment by {self.created_by} on {self.entity_type}"


class CommentAttachment(models.Model):
    """
    🟢 P1: Attachments for comments.
    """

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="comment_attachments/")
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "comment_attachments"
        verbose_name = "Comment Attachment"
        verbose_name_plural = "Comment Attachments"

    def __str__(self):
        return f"Attachment: {self.filename}"


class FormRevision(models.Model):
    """
    Quality form version tracking — captures snapshots + diffs per save.
    """

    entity_type = models.CharField(max_length=100)
    entity_id = models.BigIntegerField()
    revision_number = models.IntegerField()

    document_code = models.CharField(max_length=50, blank=True, help_text="e.g. QAS/005-1")

    snapshot = models.JSONField(default=dict, help_text="Full form data at this revision")
    changes = models.JSONField(default=dict, help_text="{field: {old: X, new: Y}}")
    change_summary = models.CharField(max_length=500, blank=True)

    revised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="form_revisions",
    )
    revised_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "form_revisions"
        ordering = ["-revision_number"]
        verbose_name = "Form Revision"
        verbose_name_plural = "Form Revisions"
        unique_together = [("entity_type", "entity_id", "revision_number")]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self):
        return f"{self.entity_type} #{self.entity_id} Rev {self.revision_number}"


# =============================================================================
# WORKFLOW ENGINE MODELS
# =============================================================================

class WorkflowEvent(models.TextChoices):
    """All workflow transitions that can trigger actions/notifications."""
    # Receiving
    BIT_RECEIVED           = "BIT_RECEIVED",          "Bit Received / Backloaded"
    INSPECTION_ACCEPTED    = "INSPECTION_ACCEPTED",    "Receiving Inspection: Accepted"
    INSPECTION_REJECTED    = "INSPECTION_REJECTED",    "Receiving Inspection: Rejected"
    INSPECTION_CONDITIONAL = "INSPECTION_CONDITIONAL", "Receiving Inspection: Conditional"
    CEREBRO_DETECTED       = "CEREBRO_DETECTED",       "Cerebro Device Detected"
    # Planning
    ADDED_TO_PLAN          = "ADDED_TO_PLAN",          "Bit Added to Production Plan"
    WO_RELEASED            = "WO_RELEASED",            "Work Order Released"
    TRANSFER_CONFIRMED     = "TRANSFER_CONFIRMED",     "Bit Transfer Confirmed"
    # Approval
    WO_APPROVED            = "WO_APPROVED",            "Work Order Approved"
    WO_REJECTED            = "WO_REJECTED",            "Work Order Rejected"
    WO_DELETED             = "WO_DELETED",             "Work Order Deleted"
    # Production
    WO_STARTED             = "WO_STARTED",             "Work Started on WO"
    STEP_COMPLETED         = "STEP_COMPLETED",         "Router Step Completed"
    STEP_ON_HOLD           = "STEP_ON_HOLD",           "Step Put On Hold"
    STEP_WAITING_QC        = "STEP_WAITING_QC",        "Step Waiting for QC"
    STEP_WAITING_APPROVAL  = "STEP_WAITING_APPROVAL",  "Step Waiting for Approval"
    STEP_WAITING_TECH      = "STEP_WAITING_TECH",      "Step Waiting for Tech Review"
    STEP_RESUMED           = "STEP_RESUMED",           "Step Resumed"
    ALL_STEPS_DONE         = "ALL_STEPS_DONE",         "All Router Steps Completed"
    DIE_CHECK_DECISION     = "DIE_CHECK_DECISION",     "Die Check Needs Quality Decision"
    SPECIAL_INSTRUCTION    = "SPECIAL_INSTRUCTION",    "Critical Special Instruction Active"
    # QC & Completion
    WO_SENT_TO_QC          = "WO_SENT_TO_QC",         "WO Sent to QC"
    QC_PASSED              = "QC_PASSED",              "QC Passed"
    QC_FAILED              = "QC_FAILED",              "QC Failed — Rework Needed"
    WO_COMPLETED           = "WO_COMPLETED",           "Work Order Completed"
    # Inventory
    GRN_POSTED             = "GRN_POSTED",             "GRN Posted"
    EVALUATION_COMPLETED   = "EVALUATION_COMPLETED",   "Bit Evaluation Completed"
    ROUTE_UPDATED          = "ROUTE_UPDATED",          "Router Route Auto-Updated"


class ActionType(models.TextChoices):
    """Types of actions that can be assigned to users."""
    INSPECT_BIT      = "INSPECT_BIT",      "Start Receiving Inspection"
    ADD_TO_PLAN      = "ADD_TO_PLAN",      "Add Bit to Production Plan"
    TRANSFER_BIT     = "TRANSFER_BIT",     "Transfer Bit (Physical Move)"
    APPROVE_WO       = "APPROVE_WO",       "Review & Approve Work Order"
    PRINT_RELEASE    = "PRINT_RELEASE",    "Print Release Paper"
    START_STEP       = "START_STEP",       "Start First Router Step"
    REVIEW_HOLD      = "REVIEW_HOLD",      "Review Hold & Decide Next Action"
    QC_CHECK         = "QC_CHECK",         "Perform QC Check"
    TECH_REVIEW      = "TECH_REVIEW",      "Technical Review Required"
    QUALITY_DECISION = "QUALITY_DECISION", "Quality Decision on Cutters"
    CONFIRM_TRANSFER = "CONFIRM_TRANSFER", "Confirm Bit Transfer to Destination"
    PREPARE_DISPATCH = "PREPARE_DISPATCH", "Prepare Bit for Shipping"
    MAKE_DECISION    = "MAKE_DECISION",    "Decision Required"
    ACKNOWLEDGE      = "ACKNOWLEDGE",      "Acknowledge / Information Only"
    REWORK           = "REWORK",           "Plan & Start Rework"
    ASSIGN_OPERATOR  = "ASSIGN_OPERATOR",  "Assign Operator to WO"
    REPLAN           = "REPLAN",           "Re-plan Bit in Production Planner"
    REMOVE_DEVICE    = "REMOVE_DEVICE",    "Remove Cerebro Device Before Processing"



class WorkflowRule(models.Model):
    """
    Admin-configurable rules that define what happens for each workflow event.
    Replaces hardcoded notify() calls with DB-driven configuration.
    """
    class RuleType(models.TextChoices):
        ACTION       = "ACTION",       "Create Action Task Only"
        NOTIFICATION = "NOTIFICATION", "Send Notification Only"
        BOTH         = "BOTH",         "Create Action + Send Notification"

    # Identity
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Trigger
    trigger_event = models.CharField(max_length=50, choices=WorkflowEvent.choices)
    trigger_filter = models.JSONField(default=dict, blank=True,
        help_text='Optional filter e.g. {"account_code": "ARAMCO"}')

    # Rule type
    rule_type = models.CharField(max_length=20, choices=RuleType.choices, default=RuleType.BOTH)

    # Action fields
    action_type = models.CharField(max_length=50, choices=ActionType.choices, blank=True)
    assign_to_role = models.ForeignKey(
        'accounts.Role', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='workflow_rules_assigned',
        help_text='Role that determines who receives this action')
    assign_to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='workflow_rule_assignments',
        help_text='Override: assign to specific user instead of capability')
    action_url_pattern = models.CharField(max_length=500, blank=True,
        help_text='URL pattern with placeholders e.g. /work-orders/{wo_id}/')
    action_description_template = models.CharField(max_length=500, blank=True,
        help_text='e.g. "Transfer {serial} from {from_loc} to {to_loc}"')
    deadline_hours = models.IntegerField(null=True, blank=True,
        help_text='Hours until action is overdue')
    is_queue_action = models.BooleanField(default=False,
        help_text='If True, any available user with the capability can claim it')

    # Escalation
    escalate_after_hours = models.IntegerField(null=True, blank=True)
    escalate_to_role = models.ForeignKey(
        'accounts.Role', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='workflow_rules_escalation')
    escalate_to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='workflow_escalation_rules')

    # Notification fields
    notif_title_template = models.CharField(max_length=200, blank=True,
        help_text='e.g. "WO {wo_number} needs approval"')
    notif_message_template = models.TextField(blank=True,
        help_text='Supports {wo_number}, {serial}, {actor_name}, etc.')
    notif_recipients_role = models.ForeignKey(
        'accounts.Role', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='workflow_rules_notification',
        help_text='Role that determines who receives this notification')
    notif_priority = models.CharField(max_length=20, choices=Notification.Priority.choices, default='NORMAL')

    # Dependencies
    depends_on_rule_ids = models.JSONField(default=list, blank=True,
        help_text='PKs of sibling rules whose actions must complete first')

    # Control
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text='Execution order for same event')

    class Meta:
        db_table = 'workflow_rules'
        ordering = ['trigger_event', 'order']
        indexes = [
            models.Index(fields=['trigger_event', 'is_active', 'order'],
                         name='idx_wr_event_active_order'),
        ]

    def __str__(self):
        return f"[{self.trigger_event}] {self.name}"


class WorkflowAction(models.Model):
    """
    A concrete action that a specific user (or role queue) must take.
    Created by the workflow engine when dispatch_event() fires.
    """
    class Status(models.TextChoices):
        PENDING     = "PENDING",      "Pending"
        CLAIMED     = "CLAIMED",      "Claimed"
        IN_PROGRESS = "IN_PROGRESS",  "In Progress"
        COMPLETED   = "COMPLETED",    "Completed"
        ESCALATED   = "ESCALATED",    "Escalated"
        CANCELLED   = "CANCELLED",    "Cancelled"
        EXPIRED     = "EXPIRED",      "Expired"

    # What to do
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    action_type = models.CharField(max_length=50, choices=ActionType.choices, blank=True)
    action_url = models.CharField(max_length=500, blank=True)
    trigger_event = models.CharField(max_length=50, choices=WorkflowEvent.choices, blank=True)

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='workflow_actions')
    assigned_role = models.ForeignKey(
        'accounts.Role', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='workflow_actions')
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='created_workflow_actions')
    is_queue_action = models.BooleanField(default=False)
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='claimed_workflow_actions')
    claimed_at = models.DateTimeField(null=True, blank=True)

    # Status & priority
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=20, choices=Notification.Priority.choices, default='NORMAL')

    # Entity link
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.BigIntegerField(null=True, blank=True)

    # Source
    source_rule = models.ForeignKey(
        WorkflowRule, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='actions')

    # Dependencies
    depends_on_ids = models.JSONField(default=list, blank=True,
        help_text='PKs of WorkflowAction records that must complete first')
    is_blocked = models.BooleanField(default=False)

    # Deadlines & escalation
    due_date = models.DateTimeField(null=True, blank=True)
    escalate_after_hours = models.IntegerField(null=True, blank=True)
    escalate_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='escalation_targets')
    escalated_at = models.DateTimeField(null=True, blank=True)

    # Completion
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='completed_workflow_actions')
    result_data = models.JSONField(default=dict, blank=True)

    # Linked notification
    notification = models.ForeignKey(
        Notification, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='workflow_actions')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workflow_actions'
        ordering = ['is_blocked', 'due_date', '-priority']
        indexes = [
            models.Index(fields=['assigned_to', 'status', 'is_blocked'],
                         name='idx_wa_user_status'),
            models.Index(fields=['assigned_role', 'status', 'is_blocked'],
                         name='idx_wa_role_status'),
            models.Index(fields=['entity_type', 'entity_id'],
                         name='idx_wa_entity'),
            models.Index(fields=['trigger_event', 'status'],
                         name='idx_wa_event_status'),
        ]

    def __str__(self):
        return f"[{self.get_action_type_display()}] {self.title}"
