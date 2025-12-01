"""
ARDT FMS - Execution Models
Version: 5.4

Tables:
- procedure_executions (P1)
- step_executions (P1)
- checkpoint_results (P1)
- branch_evaluations (P1)
- form_submissions (P1)
- form_field_values (P1)
"""

from django.db import models
from django.conf import settings


class ProcedureExecution(models.Model):
    """
    🟢 P1: Runtime instance of a procedure being executed.
    
    Links a procedure to a work order and tracks execution progress.
    """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        PAUSED = 'PAUSED', 'Paused'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        FAILED = 'FAILED', 'Failed'
    
    procedure = models.ForeignKey(
        'procedures.Procedure',
        on_delete=models.PROTECT,
        related_name='executions'
    )
    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.CASCADE,
        related_name='procedure_executions'
    )
    
    # Version tracking (captures procedure version at execution time)
    procedure_version = models.CharField(max_length=10, blank=True)
    procedure_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text='Snapshot of procedure at execution time'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Progress
    current_step = models.ForeignKey(
        'procedures.ProcedureStep',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_executions'
    )
    progress_percent = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    total_pause_duration = models.DurationField(null=True, blank=True)
    
    # Assignments
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='started_executions'
    )
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_executions'
    )
    
    # Results
    result_summary = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'procedure_executions'
        ordering = ['-created_at']
        verbose_name = 'Procedure Execution'
        verbose_name_plural = 'Procedure Executions'
        indexes = [
            models.Index(fields=['work_order', 'status']),
            models.Index(fields=['procedure', 'status']),
            models.Index(fields=['status', 'started_at']),
        ]

    def __str__(self):
        return f"{self.work_order.wo_number} - {self.procedure.code}"
    
    @property
    def duration(self):
        """Calculate actual execution duration."""
        if self.started_at and self.completed_at:
            total = self.completed_at - self.started_at
            if self.total_pause_duration:
                total -= self.total_pause_duration
            return total
        return None


class StepExecution(models.Model):
    """
    🟢 P1: Runtime instance of a procedure step being executed.
    """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        SKIPPED = 'SKIPPED', 'Skipped'
        FAILED = 'FAILED', 'Failed'
    
    class Result(models.TextChoices):
        PASS = 'PASS', 'Pass'
        FAIL = 'FAIL', 'Fail'
        NA = 'NA', 'Not Applicable'
        PARTIAL = 'PARTIAL', 'Partial'
    
    execution = models.ForeignKey(
        ProcedureExecution,
        on_delete=models.CASCADE,
        related_name='step_executions'
    )
    step = models.ForeignKey(
        'procedures.ProcedureStep',
        on_delete=models.PROTECT
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    result = models.CharField(
        max_length=20,
        choices=Result.choices,
        null=True,
        blank=True
    )
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Executor
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='executed_steps'
    )
    
    # QR verification
    qr_scanned = models.BooleanField(default=False)
    qr_scan_time = models.DateTimeField(null=True, blank=True)
    scanned_code = models.CharField(max_length=200, blank=True)
    
    # Photo capture
    photo = models.ImageField(upload_to='step_photos/', null=True, blank=True)
    photo_taken_at = models.DateTimeField(null=True, blank=True)
    
    # Signature
    signature = models.ImageField(upload_to='step_signatures/', null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    skip_reason = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'step_executions'
        ordering = ['execution', 'step__step_number']
        verbose_name = 'Step Execution'
        verbose_name_plural = 'Step Executions'
    
    def __str__(self):
        return f"{self.execution} - Step {self.step.step_number}"


class CheckpointResult(models.Model):
    """
    🟢 P1: Results of checkpoint evaluations during step execution.
    """
    
    class Result(models.TextChoices):
        PASS = 'PASS', 'Pass'
        FAIL = 'FAIL', 'Fail'
        NA = 'NA', 'Not Applicable'
    
    step_execution = models.ForeignKey(
        StepExecution,
        on_delete=models.CASCADE,
        related_name='checkpoint_results'
    )
    checkpoint = models.ForeignKey(
        'procedures.StepCheckpoint',
        on_delete=models.PROTECT
    )
    
    result = models.CharField(max_length=20, choices=Result.choices)
    actual_value = models.CharField(max_length=200, blank=True)
    
    # For measurements
    measured_value = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    is_within_tolerance = models.BooleanField(null=True, blank=True)
    
    # Evidence
    photo = models.ImageField(upload_to='checkpoint_photos/', null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # NCR link (if checkpoint failed and NCR created)
    ncr = models.ForeignKey(
        'quality.NCR',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checkpoint_results'
    )
    
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    evaluated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'checkpoint_results'
        ordering = ['step_execution', 'checkpoint__sequence']
        verbose_name = 'Checkpoint Result'
        verbose_name_plural = 'Checkpoint Results'


class BranchEvaluation(models.Model):
    """
    🟢 P1: Records of branch condition evaluations during execution.
    """
    
    step_execution = models.ForeignKey(
        StepExecution,
        on_delete=models.CASCADE,
        related_name='branch_evaluations'
    )
    branch = models.ForeignKey(
        'procedures.StepBranch',
        on_delete=models.PROTECT
    )
    
    condition_met = models.BooleanField()
    evaluated_value = models.CharField(max_length=500, blank=True)
    action_taken = models.CharField(max_length=30, blank=True)
    target_step_id = models.BigIntegerField(null=True, blank=True)
    
    evaluated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'branch_evaluations'
        verbose_name = 'Branch Evaluation'
        verbose_name_plural = 'Branch Evaluations'


class FormSubmission(models.Model):
    """
    🟢 P1: Submissions of form templates during step execution.
    """
    
    step_execution = models.ForeignKey(
        StepExecution,
        on_delete=models.CASCADE,
        related_name='form_submissions'
    )
    form_template = models.ForeignKey(
        'forms_engine.FormTemplate',
        on_delete=models.PROTECT
    )
    
    # Version at submission time
    template_version = models.CharField(max_length=10, blank=True)
    
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # Computed properties stored for quick access
    is_complete = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=True)
    validation_errors = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'form_submissions'
        ordering = ['-submitted_at']
        verbose_name = 'Form Submission'
        verbose_name_plural = 'Form Submissions'
    
    def __str__(self):
        return f"{self.form_template.code} - {self.submitted_at}"


class FormFieldValue(models.Model):
    """
    🟢 P1: Individual field values in a form submission.
    """
    
    submission = models.ForeignKey(
        FormSubmission,
        on_delete=models.CASCADE,
        related_name='field_values'
    )
    field = models.ForeignKey(
        'forms_engine.FormField',
        on_delete=models.PROTECT
    )
    
    # Store all values as text; field type determines interpretation
    value = models.TextField(blank=True)
    
    # For file uploads
    file = models.FileField(upload_to='form_files/', null=True, blank=True)
    
    # Validation
    is_valid = models.BooleanField(default=True)
    validation_message = models.CharField(max_length=500, blank=True)
    
    class Meta:
        db_table = 'form_field_values'
        verbose_name = 'Form Field Value'
        verbose_name_plural = 'Form Field Values'
