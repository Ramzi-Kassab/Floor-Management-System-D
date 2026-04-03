"""
ARDT FMS - Quality Models
Version: 5.4

Tables:
- inspections (P1)
- ncrs (P1)
- ncr_photos (P1)
"""

from django.conf import settings
from django.db import models


class Inspection(models.Model):
    """
    🟢 P1: Quality inspections.
    """

    class InspectionType(models.TextChoices):
        INCOMING = "INCOMING", "Incoming Inspection"
        IN_PROCESS = "IN_PROCESS", "In-Process Inspection"
        FINAL = "FINAL", "Final Inspection"
        CUSTOMER = "CUSTOMER", "Customer Inspection"
        THIRD_PARTY = "THIRD_PARTY", "Third Party Inspection"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        PASSED = "PASSED", "Passed"
        FAILED = "FAILED", "Failed"
        CONDITIONAL = "CONDITIONAL", "Conditional Pass"
        CANCELLED = "CANCELLED", "Cancelled"

    inspection_number = models.CharField(max_length=30, unique=True)
    inspection_type = models.CharField(max_length=20, choices=InspectionType.choices)

    # What is being inspected
    work_order = models.ForeignKey("workorders.WorkOrder", on_delete=models.CASCADE, related_name="inspections")
    drill_bit = models.ForeignKey(
        "workorders.DrillBit", on_delete=models.SET_NULL, null=True, blank=True, related_name="inspections"
    )

    # Procedure link
    procedure = models.ForeignKey("procedures.Procedure", on_delete=models.SET_NULL, null=True, blank=True, related_name="inspections")
    procedure_execution = models.ForeignKey("execution.ProcedureExecution", on_delete=models.SET_NULL, null=True, blank=True, related_name="inspections")

    # Schedule
    scheduled_date = models.DateField(null=True, blank=True)

    # Execution
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="performed_inspections"
    )
    inspected_at = models.DateTimeField(null=True, blank=True)

    # Results
    findings = models.TextField(blank=True)
    pass_count = models.IntegerField(default=0)
    fail_count = models.IntegerField(default=0)

    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_inspections"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_inspections"
    )

    class Meta:
        db_table = "inspections"
        ordering = ["-scheduled_date"]
        verbose_name = "Inspection"
        verbose_name_plural = "Inspections"
        indexes = [
            models.Index(fields=["inspection_number"], name="insp_number_idx"),
            models.Index(fields=["status"], name="insp_status_idx"),
            models.Index(fields=["work_order", "status"], name="insp_wo_status_idx"),
        ]

    def __str__(self):
        return f"{self.inspection_number}"


class NCR(models.Model):
    """
    🟢 P1: Non-Conformance Reports.
    """

    class Severity(models.TextChoices):
        MINOR = "MINOR", "Minor"
        MAJOR = "MAJOR", "Major"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        INVESTIGATING = "INVESTIGATING", "Under Investigation"
        PENDING_DISPOSITION = "PENDING_DISPOSITION", "Pending Disposition"
        IN_REWORK = "IN_REWORK", "In Rework"
        PENDING_VERIFICATION = "PENDING_VERIFICATION", "Pending Verification"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"

    class Disposition(models.TextChoices):
        USE_AS_IS = "USE_AS_IS", "Use As Is"
        REWORK = "REWORK", "Rework"
        REPAIR = "REPAIR", "Repair"
        SCRAP = "SCRAP", "Scrap"
        RETURN_SUPPLIER = "RETURN_SUPPLIER", "Return to Supplier"
        DEVIATE = "DEVIATE", "Deviation/Concession"

    ncr_number = models.CharField(max_length=30, unique=True)

    # Source
    work_order = models.ForeignKey(
        "workorders.WorkOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="ncrs"
    )
    inspection = models.ForeignKey(Inspection, on_delete=models.SET_NULL, null=True, blank=True, related_name="ncrs")
    drill_bit = models.ForeignKey("workorders.DrillBit", on_delete=models.SET_NULL, null=True, blank=True, related_name="ncrs")
    inventory_item = models.ForeignKey(
        "inventory.InventoryItem", on_delete=models.SET_NULL, null=True, blank=True, related_name="ncrs"
    )

    # Description
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=Severity.choices)

    # Detection
    detected_at = models.DateTimeField()
    detected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="detected_ncrs"
    )
    detection_stage = models.CharField(max_length=100, blank=True)

    # Investigation
    root_cause = models.TextField(blank=True)
    investigated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="investigated_ncrs"
    )

    # Disposition
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN)
    disposition = models.CharField(max_length=30, choices=Disposition.choices, null=True, blank=True)
    disposition_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="dispositioned_ncrs"
    )
    disposition_date = models.DateField(null=True, blank=True)
    disposition_notes = models.TextField(blank=True)

    # Rework WO link
    rework_work_order = models.ForeignKey(
        "workorders.WorkOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="source_ncrs"
    )

    # Closure
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="closed_ncrs"
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closure_notes = models.TextField(blank=True)

    # Cost
    estimated_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_ncrs")

    class Meta:
        db_table = "ncrs"
        ordering = ["-detected_at"]
        verbose_name = "NCR"
        verbose_name_plural = "NCRs"
        indexes = [
            models.Index(fields=["ncr_number"], name="ncr_number_idx"),
            models.Index(fields=["status"], name="ncr_status_idx"),
            models.Index(fields=["severity"], name="ncr_severity_idx"),
            models.Index(fields=["work_order", "status"], name="ncr_wo_status_idx"),
        ]

    def __str__(self):
        return f"{self.ncr_number} - {self.title}"


class NCRPhoto(models.Model):
    """
    🟢 P1: Photos attached to NCRs.
    """

    ncr = models.ForeignKey(NCR, on_delete=models.CASCADE, related_name="photos")
    photo = models.ImageField(upload_to="ncr_photos/")
    caption = models.CharField(max_length=200, blank=True)

    taken_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ncr_photos")
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ncr_photos"
        ordering = ["ncr", "-taken_at"]
        verbose_name = "NCR Photo"
        verbose_name_plural = "NCR Photos"
        indexes = [
            models.Index(fields=["ncr"]),
        ]

    def __str__(self):
        return f"{self.ncr.ncr_number} - Photo {self.pk}"


class QualityIssue(models.Model):
    """
    Issue reported from a process step (Die Check, Evaluation, etc.).
    The operator reports → Quality team reviews → decides action.
    Decision reflects back to the source page and WO.
    """
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open — Pending Review"
        IN_REVIEW = "IN_REVIEW", "In Review"
        ACCEPTED = "ACCEPTED", "Accepted — No Action Needed"
        NCR_CREATED = "NCR_CREATED", "NCR Created"
        REWORK = "REWORK", "Rework Required"
        CLOSED = "CLOSED", "Closed"

    # Identity
    issue_number = models.CharField(max_length=30, unique=True, blank=True)

    # Source
    work_order = models.ForeignKey(
        'workorders.WorkOrder', on_delete=models.CASCADE, null=True, blank=True, related_name='quality_issues')
    drill_bit = models.ForeignKey(
        'workorders.DrillBit', on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_issues')
    source_step = models.CharField(max_length=100, blank=True,
        help_text='e.g. "Die Check (Receiving)", "PDC Evaluation"')
    router_step_number = models.IntegerField(null=True, blank=True)

    # Content — the auto-generated summary from the dedicated page
    summary = models.TextField(help_text='Auto-generated summary from the process page')
    additional_remarks = models.TextField(blank=True)

    # Status & Decision
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.OPEN)
    decision_notes = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='quality_decisions')
    decided_at = models.DateTimeField(null=True, blank=True)

    # Links created by quality decision
    ncr = models.ForeignKey(
        NCR, on_delete=models.SET_NULL, null=True, blank=True, related_name='source_issues')

    # Audit
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reported_quality_issues')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quality_issues'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['work_order', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.issue_number} — {self.source_step} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.issue_number:
            self.issue_number = self._generate_number()
        super().save(*args, **kwargs)

    def _generate_number(self):
        from django.utils import timezone
        year = timezone.now().year
        last = QualityIssue.objects.filter(
            issue_number__startswith=f'QI-{year}-'
        ).order_by('-issue_number').first()
        if last:
            try:
                num = int(last.issue_number.split('-')[-1]) + 1
            except ValueError:
                num = 1
        else:
            num = 1
        return f"QI-{year}-{num:04d}"


class QualityIssueAction(models.Model):
    """
    One action taken on a QualityIssue. Multiple actions can be chained.
    E.g.: Inform Technical → Technical accepts → Quality creates NCR + Rework.
    """
    class ActionType(models.TextChoices):
        ACCEPT = "ACCEPT", "Accepted — No Action Needed"
        CREATE_NCR = "CREATE_NCR", "Create NCR"
        CREATE_NCR_CAPA = "CREATE_NCR_CAPA", "Create NCR with CAPA"
        REWORK = "REWORK", "Rework Required"
        INFORM_TECHNICAL = "INFORM_TECHNICAL", "Inform Technical Team"
        INFORM_CUSTOMER = "INFORM_CUSTOMER", "Inform Customer"
        TECHNICAL_ACCEPT = "TECHNICAL_ACCEPT", "Technical: Accept As-Is"
        TECHNICAL_REWORK = "TECHNICAL_REWORK", "Technical: Rework Needed"
        CLOSE = "CLOSE", "Close Issue"
        NOTE = "NOTE", "Add Note"

    issue = models.ForeignKey(QualityIssue, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=25, choices=ActionType.choices)
    notes = models.TextField(blank=True)

    # Who and when
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='quality_issue_actions')
    performed_at = models.DateTimeField(auto_now_add=True)

    # Links created by this action
    ncr = models.ForeignKey(NCR, on_delete=models.SET_NULL, null=True, blank=True,
        help_text='NCR created by this action')

    class Meta:
        db_table = 'quality_issue_actions'
        ordering = ['performed_at']

    def __str__(self):
        return f"{self.issue.issue_number}: {self.get_action_type_display()} by {self.performed_by}"
