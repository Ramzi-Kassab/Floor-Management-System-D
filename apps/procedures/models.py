"""
ARDT FMS - Procedures Models
Version: 5.4

Tables:
- procedures (P1)
- step_types (P1)
- procedure_steps (P1)
- checkpoint_types (P1)
- step_checkpoints (P1)
- step_branches (P1)
- step_inputs (P1)
- step_outputs (P1)
- procedure_versions (P1) - NEW in v5.4
"""

from django.db import models
from django.conf import settings


class Procedure(models.Model):
    """
    🟢 P1: Procedure definitions - the core of the Procedure Engine.
    
    Procedures define step-by-step workflows for manufacturing,
    quality, maintenance, and other processes.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ACTIVE = 'ACTIVE', 'Active'
        OBSOLETE = 'OBSOLETE', 'Obsolete'
    
    class Category(models.TextChoices):
        PRODUCTION = 'PRODUCTION', 'Production'
        QUALITY = 'QUALITY', 'Quality'
        SAFETY = 'SAFETY', 'Safety'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'
        SUPPLY_CHAIN = 'SUPPLY_CHAIN', 'Supply Chain'
        GENERAL = 'GENERAL', 'General'
    
    class AppliesTo(models.TextChoices):
        FC = 'FC', 'Fixed Cutter (FC)'
        RC = 'RC', 'Roller Cone (RC)'
        BOTH = 'BOTH', 'Both FC & RC'
        ALL = 'ALL', 'All Types'
    
    code = models.CharField(max_length=30, unique=True, help_text='e.g., SA-PP-104')
    name = models.CharField(max_length=200)
    revision = models.CharField(max_length=10, blank=True)
    revision_date = models.DateField(null=True, blank=True)
    
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.PRODUCTION
    )
    applies_to = models.CharField(
        max_length=20,
        choices=AppliesTo.choices,
        default=AppliesTo.ALL
    )
    
    scope = models.TextField(blank=True, help_text='Scope and applicability')
    purpose = models.TextField(blank=True, help_text='Purpose and objectives')
    safety_notes = models.TextField(blank=True, help_text='Safety precautions')
    
    responsible_role = models.ForeignKey(
        'accounts.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_procedures'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_procedures'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_procedures'
    )
    effective_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_procedures'
    )
    
    class Meta:
        db_table = 'procedures'
        ordering = ['code']
        verbose_name = 'Procedure'
        verbose_name_plural = 'Procedures'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def step_count(self):
        return self.steps.count()
    
    @property
    def estimated_duration(self):
        """Total estimated duration in minutes."""
        return self.steps.aggregate(
            total=models.Sum('estimated_duration_minutes')
        )['total'] or 0


class StepType(models.Model):
    """
    🟢 P1: Types of steps in procedures.
    
    Examples: OPERATION, INSPECTION, APPROVAL, DECISION, DOCUMENT, PHOTO
    """
    
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text='Icon class/name')
    color = models.CharField(max_length=20, blank=True, help_text='Display color')
    
    class Meta:
        db_table = 'step_types'
        ordering = ['name']
        verbose_name = 'Step Type'
        verbose_name_plural = 'Step Types'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ProcedureStep(models.Model):
    """
    🟢 P1: Steps within a procedure.
    
    Supports dependencies, branching, and conditional execution.
    """
    
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    step_number = models.IntegerField(help_text='10, 20, 30... allows inserting')
    step_code = models.CharField(max_length=30, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    step_type = models.ForeignKey(
        StepType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    responsible_role = models.ForeignKey(
        'accounts.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    reference_procedure_code = models.CharField(
        max_length=30,
        blank=True,
        help_text='Sub-procedure link'
    )
    
    # Step behavior
    is_mandatory = models.BooleanField(default=True)
    is_parallel = models.BooleanField(default=False)
    is_conditional = models.BooleanField(default=False)
    can_skip = models.BooleanField(default=False, help_text='Allow skipping with reason')
    can_go_back = models.BooleanField(default=True, help_text='Allow returning to previous')
    
    # Dependencies
    depends_on_step = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dependent_steps',
        help_text='Must complete this step first'
    )
    dependency_condition = models.JSONField(
        null=True,
        blank=True,
        help_text='Condition: {"field": "result", "operator": "equals", "value": "PASS"}'
    )
    
    # Timing
    estimated_duration_minutes = models.IntegerField(null=True, blank=True)
    time_limit_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text='Max time allowed'
    )
    
    # Requirements
    requires_qr_scan = models.BooleanField(default=False)
    requires_photo = models.BooleanField(default=False)
    requires_signature = models.BooleanField(default=False)
    requires_form = models.BooleanField(default=False, help_text='Has attached form')
    
    # Form link (if requires_form is True)
    form_template = models.ForeignKey(
        'forms_engine.FormTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='procedure_steps'
    )
    
    # Expected output for validation
    expected_output = models.JSONField(
        null=True,
        blank=True,
        help_text='Expected outcomes: {"torque_min": 40, "torque_max": 50}'
    )
    validation_rules = models.JSONField(null=True, blank=True)
    
    sequence = models.IntegerField(default=0, help_text='Display order')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'procedure_steps'
        ordering = ['procedure', 'step_number']
        unique_together = ['procedure', 'step_number']
        verbose_name = 'Procedure Step'
        verbose_name_plural = 'Procedure Steps'
        indexes = [
            models.Index(fields=['procedure']),
            models.Index(fields=['depends_on_step']),
        ]
    
    def __str__(self):
        return f"{self.procedure.code} - Step {self.step_number}: {self.name}"


class CheckpointType(models.Model):
    """
    🟢 P1: Types of checkpoints in inspection steps.
    
    Examples: OK_NOK, PASS_FAIL, YES_NO, MEASURE, SELECT, TEXT, NUMBER
    """
    
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    input_type = models.CharField(
        max_length=30,
        help_text='OK_NOK, PASS_FAIL, YES_NO, MEASURE, SELECT, TEXT, NUMBER'
    )
    
    class Meta:
        db_table = 'checkpoint_types'
        ordering = ['name']
        verbose_name = 'Checkpoint Type'
        verbose_name_plural = 'Checkpoint Types'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class StepCheckpoint(models.Model):
    """
    🟢 P1: Checkpoints for INSPECTION steps.
    
    Defines what needs to be checked and the pass/fail criteria.
    """
    
    class FailureAction(models.TextChoices):
        STOP = 'STOP', 'Stop Procedure'
        NCR = 'NCR', 'Create NCR'
        NOTIFY = 'NOTIFY', 'Notify Only'
        REWORK = 'REWORK', 'Send to Rework'
        CONTINUE = 'CONTINUE', 'Continue Anyway'
    
    step = models.ForeignKey(
        ProcedureStep,
        on_delete=models.CASCADE,
        related_name='checkpoints'
    )
    sequence = models.IntegerField(default=0)
    checkpoint_code = models.CharField(max_length=30, blank=True)
    name = models.CharField(max_length=200)
    
    check_type = models.ForeignKey(
        CheckpointType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    expected_value = models.CharField(max_length=100, blank=True)
    tolerance_min = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    tolerance_max = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    unit = models.CharField(max_length=20, blank=True, help_text='mm, inch, PSI')
    options = models.JSONField(
        null=True,
        blank=True,
        help_text='For dropdown options'
    )
    
    is_critical = models.BooleanField(default=False)
    failure_action = models.CharField(
        max_length=30,
        choices=FailureAction.choices,
        default=FailureAction.NOTIFY
    )
    failure_notify_role = models.ForeignKey(
        'accounts.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    help_text = models.TextField(blank=True)
    photo_required = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'step_checkpoints'
        ordering = ['step', 'sequence']
        verbose_name = 'Step Checkpoint'
        verbose_name_plural = 'Step Checkpoints'
    
    def __str__(self):
        return f"{self.step} - {self.name}"


class StepBranch(models.Model):
    """
    🟢 P1: Branching logic for procedure steps.
    
    Enables conditional routing based on step results.
    """
    
    class Action(models.TextChoices):
        GOTO_STEP = 'GOTO_STEP', 'Go to Step'
        SKIP_STEP = 'SKIP_STEP', 'Skip Step'
        STOP = 'STOP', 'Stop Procedure'
        NCR = 'NCR', 'Create NCR'
        NOTIFY = 'NOTIFY', 'Notify'
        COMPLETE = 'COMPLETE', 'Complete Procedure'
    
    step = models.ForeignKey(
        ProcedureStep,
        on_delete=models.CASCADE,
        related_name='branches'
    )
    sequence = models.IntegerField(default=0)
    condition_description = models.CharField(max_length=200, help_text='Human readable')
    condition_field = models.CharField(max_length=100, help_text='Field to evaluate')
    condition_operator = models.CharField(
        max_length=20,
        help_text='=, !=, >, <, IN, CONTAINS, IS_NULL'
    )
    condition_value = models.CharField(max_length=200, blank=True)
    
    then_action = models.CharField(max_length=30, choices=Action.choices)
    then_target_step = models.ForeignKey(
        ProcedureStep,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incoming_branches'
    )
    then_notify_role = models.ForeignKey(
        'accounts.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    then_message = models.TextField(blank=True)
    
    is_default = models.BooleanField(default=False, help_text='ELSE branch')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'step_branches'
        ordering = ['step', 'sequence']
        verbose_name = 'Step Branch'
        verbose_name_plural = 'Step Branches'
    
    def __str__(self):
        return f"{self.step} - {self.condition_description}"


class StepInput(models.Model):
    """
    🟢 P1: Required inputs for a procedure step.
    
    Materials, tools, equipment, documents needed for the step.
    """
    
    class InputType(models.TextChoices):
        MATERIAL = 'MATERIAL', 'Material'
        TOOL = 'TOOL', 'Tool'
        EQUIPMENT = 'EQUIPMENT', 'Equipment'
        DOCUMENT = 'DOCUMENT', 'Document'
        PPE = 'PPE', 'PPE'
        FORM = 'FORM', 'Form'
    
    step = models.ForeignKey(
        ProcedureStep,
        on_delete=models.CASCADE,
        related_name='inputs'
    )
    input_type = models.CharField(max_length=30, choices=InputType.choices)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    equipment = models.ForeignKey(
        'maintenance.Equipment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    unit = models.CharField(max_length=20, blank=True)
    is_consumed = models.BooleanField(default=False, help_text='Material consumed during step')
    
    class Meta:
        db_table = 'step_inputs'
        ordering = ['step', 'input_type', 'name']
        verbose_name = 'Step Input'
        verbose_name_plural = 'Step Inputs'
    
    def __str__(self):
        return f"{self.step} - {self.input_type}: {self.name}"


class StepOutput(models.Model):
    """
    🟢 P1: Expected outputs from a procedure step.
    
    Defines what should be produced/completed by the step.
    """
    
    class OutputType(models.TextChoices):
        PRODUCT = 'PRODUCT', 'Product'
        DOCUMENT = 'DOCUMENT', 'Document'
        MEASUREMENT = 'MEASUREMENT', 'Measurement'
        PHOTO = 'PHOTO', 'Photo'
        APPROVAL = 'APPROVAL', 'Approval'
        TRANSFER = 'TRANSFER', 'Transfer'
    
    step = models.ForeignKey(
        ProcedureStep,
        on_delete=models.CASCADE,
        related_name='outputs'
    )
    output_type = models.CharField(max_length=30, choices=OutputType.choices)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'step_outputs'
        ordering = ['step', 'output_type', 'name']
        verbose_name = 'Step Output'
        verbose_name_plural = 'Step Outputs'
    
    def __str__(self):
        return f"{self.step} - {self.output_type}: {self.name}"


class ProcedureVersion(models.Model):
    """
    🟢 P1: Version history for procedures (NEW in v5.4).
    
    Tracks changes to procedures for audit purposes.
    """
    
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.IntegerField()
    
    # Snapshot of procedure at this version
    snapshot = models.JSONField(help_text='Full procedure JSON at this version')
    
    # Change tracking
    change_summary = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'procedure_versions'
        ordering = ['procedure', '-version_number']
        unique_together = ['procedure', 'version_number']
        verbose_name = 'Procedure Version'
        verbose_name_plural = 'Procedure Versions'
    
    def __str__(self):
        return f"{self.procedure.code} v{self.version_number}"
