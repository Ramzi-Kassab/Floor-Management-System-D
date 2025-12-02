"""
ARDT FMS - Work Orders Models
Version: 5.4

Tables:
- drill_bits (P1) - not in DBML but logically needed
- work_orders (P1)
- work_order_documents (P1)
- work_order_photos (P1)
- work_order_materials (P1)
- work_order_time_logs (P1)
- bit_evaluations (P1)
"""

from decimal import Decimal

from django.conf import settings
from django.db import models


class DrillBit(models.Model):
    """
    🟢 P1: Drill bit master - tracks individual bits through their lifecycle.
    """

    class BitType(models.TextChoices):
        FC = "FC", "Fixed Cutter (PDC)"
        RC = "RC", "Roller Cone"

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        IN_STOCK = "IN_STOCK", "In Stock"
        ASSIGNED = "ASSIGNED", "Assigned to WO"
        IN_PRODUCTION = "IN_PRODUCTION", "In Production"
        QC_PENDING = "QC_PENDING", "QC Pending"
        READY = "READY", "Ready for Dispatch"
        DISPATCHED = "DISPATCHED", "Dispatched"
        IN_FIELD = "IN_FIELD", "In Field"
        RETURNED = "RETURNED", "Returned"
        SCRAPPED = "SCRAPPED", "Scrapped"

    serial_number = models.CharField(max_length=50, unique=True)
    bit_type = models.CharField(max_length=20, choices=BitType.choices)

    # Design/specs
    design = models.ForeignKey(
        "technology.Design", on_delete=models.SET_NULL, null=True, blank=True, related_name="drill_bits"
    )
    size = models.DecimalField(max_digits=6, decimal_places=3, help_text="Size in inches")
    iadc_code = models.CharField(max_length=20, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)

    # Location
    current_location = models.ForeignKey(
        "sales.Warehouse", on_delete=models.SET_NULL, null=True, blank=True, related_name="stored_bits"
    )

    # Customer/Job
    customer = models.ForeignKey("sales.Customer", on_delete=models.SET_NULL, null=True, blank=True, related_name="drill_bits")
    rig = models.ForeignKey("sales.Rig", on_delete=models.SET_NULL, null=True, blank=True)
    well = models.ForeignKey("sales.Well", on_delete=models.SET_NULL, null=True, blank=True)

    # Usage tracking
    total_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_footage = models.IntegerField(default=0, help_text="Total feet drilled")
    run_count = models.IntegerField(default=0, help_text="Number of runs")

    # QR Code
    qr_code = models.CharField(max_length=100, unique=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_bits")

    class Meta:
        db_table = "drill_bits"
        ordering = ["-created_at"]
        verbose_name = "Drill Bit"
        verbose_name_plural = "Drill Bits"
        indexes = [
            models.Index(fields=["serial_number"], name="db_serial_idx"),
            models.Index(fields=["status"], name="db_status_idx"),
            models.Index(fields=["bit_type"], name="db_type_idx"),
            models.Index(fields=["customer", "status"], name="db_customer_status_idx"),
        ]

    def __str__(self):
        return f"{self.serial_number} ({self.bit_type})"

    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.qr_code = f"BIT-{self.serial_number}"
        super().save(*args, **kwargs)


class WorkOrder(models.Model):
    """
    🟢 P1: Work orders for manufacturing operations.
    """

    class WOType(models.TextChoices):
        FC_NEW = "FC_NEW", "FC New Build"
        FC_REWORK = "FC_REWORK", "FC Rework"
        FC_REPAIR = "FC_REPAIR", "FC Repair"
        RC_NEW = "RC_NEW", "RC New Build"
        RC_REWORK = "RC_REWORK", "RC Rework"
        RC_REPAIR = "RC_REPAIR", "RC Repair"
        RERUN = "RERUN", "Rerun"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PLANNED = "PLANNED", "Planned"
        RELEASED = "RELEASED", "Released"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        ON_HOLD = "ON_HOLD", "On Hold"
        QC_PENDING = "QC_PENDING", "QC Pending"
        QC_PASSED = "QC_PASSED", "QC Passed"
        QC_FAILED = "QC_FAILED", "QC Failed"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"
        CRITICAL = "CRITICAL", "Critical"

    wo_number = models.CharField(max_length=30, unique=True)
    wo_type = models.CharField(max_length=20, choices=WOType.choices)

    # Product
    drill_bit = models.ForeignKey(DrillBit, on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders")
    design = models.ForeignKey(
        "technology.Design", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders"
    )
    bom = models.ForeignKey("technology.BOM", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders")

    # Customer/Job
    customer = models.ForeignKey(
        "sales.Customer", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders"
    )
    sales_order = models.ForeignKey(
        "sales.SalesOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders"
    )

    # Destination
    rig = models.ForeignKey("sales.Rig", on_delete=models.SET_NULL, null=True, blank=True)
    well = models.ForeignKey("sales.Well", on_delete=models.SET_NULL, null=True, blank=True)

    # Planning
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    planned_start = models.DateField(null=True, blank=True)
    planned_end = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    # Actual
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    progress_percent = models.IntegerField(default=0)

    # Procedure link
    procedure = models.ForeignKey(
        "procedures.Procedure", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders"
    )

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_work_orders"
    )
    department = models.ForeignKey("organization.Department", on_delete=models.SET_NULL, null=True, blank=True)

    # Notes
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_work_orders"
    )

    class Meta:
        db_table = "work_orders"
        ordering = ["-created_at"]
        verbose_name = "Work Order"
        verbose_name_plural = "Work Orders"
        indexes = [
            models.Index(fields=["wo_number"], name="wo_wo_number_idx"),
            models.Index(fields=["status"], name="wo_status_idx"),
            models.Index(fields=["status", "priority"], name="wo_status_priority_idx"),
            models.Index(fields=["status", "due_date"], name="wo_status_due_idx"),
            models.Index(fields=["customer", "status"], name="wo_customer_status_idx"),
            models.Index(fields=["assigned_to", "status"], name="wo_assigned_status_idx"),
            models.Index(fields=["due_date"], name="wo_due_date_idx"),
        ]

    def __str__(self):
        return f"{self.wo_number}"

    @property
    def is_overdue(self):
        """Check if work order is overdue."""
        from django.utils import timezone

        if not self.due_date:
            return False
        if self.status in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return False
        return self.due_date < timezone.now().date()

    @property
    def days_overdue(self):
        """Get number of days overdue (negative if not yet due)."""
        from django.utils import timezone

        if not self.due_date:
            return 0
        delta = timezone.now().date() - self.due_date
        return delta.days

    @property
    def can_start(self):
        """Check if work order can be started."""
        return self.status in [self.Status.PLANNED, self.Status.RELEASED]

    @property
    def can_complete(self):
        """Check if work order can be marked complete."""
        return self.status in [self.Status.IN_PROGRESS, self.Status.QC_PASSED]

    def start_work(self, user=None):
        """
        Start work on this work order.
        Sets status to IN_PROGRESS and records actual_start time.
        """
        from django.utils import timezone

        if not self.can_start:
            raise ValueError(f"Cannot start work order in status {self.status}")

        self.status = self.Status.IN_PROGRESS
        self.actual_start = timezone.now()
        self.save(update_fields=["status", "actual_start", "updated_at"])
        return True

    def complete_work(self, user=None):
        """
        Complete this work order.
        Sets status to COMPLETED and records actual_end time.
        """
        from django.utils import timezone

        if not self.can_complete:
            raise ValueError(f"Cannot complete work order in status {self.status}")

        self.status = self.Status.COMPLETED
        self.actual_end = timezone.now()
        self.progress_percent = 100
        self.save(update_fields=["status", "actual_end", "progress_percent", "updated_at"])
        return True

    def put_on_hold(self, reason=None):
        """Put work order on hold."""
        if self.status not in [self.Status.IN_PROGRESS, self.Status.PLANNED, self.Status.RELEASED]:
            raise ValueError(f"Cannot put work order on hold in status {self.status}")

        self.status = self.Status.ON_HOLD
        if reason:
            self.notes = f"{self.notes}\n[ON HOLD] {reason}".strip()
        self.save(update_fields=["status", "notes", "updated_at"])
        return True

    def submit_for_qc(self):
        """Submit work order for QC inspection."""
        if self.status != self.Status.IN_PROGRESS:
            raise ValueError("Only in-progress work orders can be submitted for QC")

        self.status = self.Status.QC_PENDING
        self.save(update_fields=["status", "updated_at"])
        return True


class WorkOrderDocument(models.Model):
    """
    🟢 P1: Documents attached to work orders.
    """

    class DocType(models.TextChoices):
        DRAWING = "DRAWING", "Drawing"
        SPECIFICATION = "SPECIFICATION", "Specification"
        PROCEDURE = "PROCEDURE", "Procedure"
        INSPECTION = "INSPECTION", "Inspection Report"
        CERTIFICATE = "CERTIFICATE", "Certificate"
        CUSTOMER = "CUSTOMER", "Customer Document"
        OTHER = "OTHER", "Other"

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=20, choices=DocType.choices)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="wo_documents/")
    version = models.CharField(max_length=20, blank=True)

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "work_order_documents"
        ordering = ["work_order", "document_type", "name"]
        verbose_name = "Work Order Document"
        verbose_name_plural = "Work Order Documents"

    def __str__(self):
        return f"{self.work_order.wo_number} - {self.name}"


class WorkOrderPhoto(models.Model):
    """
    🟢 P1: Photos attached to work orders.
    """

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="photos")
    photo = models.ImageField(upload_to="wo_photos/")
    caption = models.CharField(max_length=200, blank=True)
    stage = models.CharField(max_length=50, blank=True, help_text="Production stage")

    taken_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "work_order_photos"
        ordering = ["work_order", "-taken_at"]
        verbose_name = "Work Order Photo"
        verbose_name_plural = "Work Order Photos"

    def __str__(self):
        return f"{self.work_order.wo_number} - Photo {self.pk}"


class WorkOrderMaterial(models.Model):
    """
    🟢 P1: Materials consumed in a work order.
    """

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="materials")
    inventory_item = models.ForeignKey("inventory.InventoryItem", on_delete=models.PROTECT, related_name="wo_consumptions")

    # From BOM
    bom_line = models.ForeignKey("technology.BOMLine", on_delete=models.SET_NULL, null=True, blank=True)

    # Quantities
    planned_quantity = models.DecimalField(max_digits=10, decimal_places=3)
    issued_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    consumed_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    returned_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    # Cost
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "work_order_materials"
        ordering = ["work_order", "inventory_item__name"]
        verbose_name = "Work Order Material"
        verbose_name_plural = "Work Order Materials"

    def __str__(self):
        item_name = self.inventory_item.name if self.inventory_item else "Unknown"
        return f"{self.work_order.wo_number} - {item_name} (×{self.consumed_quantity})"


class WorkOrderTimeLog(models.Model):
    """
    🟢 P1: Time logged against work orders.
    """

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="time_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="wo_time_logs")

    # Time
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)

    # Activity
    activity_type = models.CharField(max_length=50, blank=True)
    step = models.ForeignKey("procedures.ProcedureStep", on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)

    # Cost
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "work_order_time_logs"
        ordering = ["work_order", "-start_time"]
        verbose_name = "Work Order Time Log"
        verbose_name_plural = "Work Order Time Logs"

    def __str__(self):
        username = self.user.username if self.user else "Unknown"
        duration = f"{self.duration_minutes}m" if self.duration_minutes else "In progress"
        return f"{self.work_order.wo_number} - {username} ({duration})"

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
            if self.hourly_rate:
                # Use Decimal for accurate currency calculations
                hours = Decimal(self.duration_minutes) / Decimal(60)
                self.total_cost = hours * self.hourly_rate
        super().save(*args, **kwargs)


class BitEvaluation(models.Model):
    """
    🟢 P1: Evaluation of returned drill bits.
    """

    class Condition(models.TextChoices):
        EXCELLENT = "EXCELLENT", "Excellent"
        GOOD = "GOOD", "Good"
        FAIR = "FAIR", "Fair"
        POOR = "POOR", "Poor"
        SCRAPPED = "SCRAPPED", "Scrapped"

    class Recommendation(models.TextChoices):
        STOCK = "STOCK", "Return to Stock"
        REWORK = "REWORK", "Rework Required"
        REPAIR = "REPAIR", "Repair Required"
        RERUN = "RERUN", "Rerun as-is"
        SCRAP = "SCRAP", "Scrap"

    drill_bit = models.ForeignKey(DrillBit, on_delete=models.CASCADE, related_name="evaluations")

    # Field data
    rig = models.ForeignKey("sales.Rig", on_delete=models.SET_NULL, null=True, blank=True)
    well = models.ForeignKey("sales.Well", on_delete=models.SET_NULL, null=True, blank=True)
    run_number = models.IntegerField(null=True, blank=True)
    hours_run = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    footage_drilled = models.IntegerField(null=True, blank=True)
    depth_in = models.IntegerField(null=True, blank=True, help_text="Feet")
    depth_out = models.IntegerField(null=True, blank=True, help_text="Feet")

    # Evaluation
    evaluation_date = models.DateField()
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="bit_evaluations"
    )

    # IADC dull grading
    inner_rows = models.CharField(max_length=10, blank=True)
    outer_rows = models.CharField(max_length=10, blank=True)
    dull_char = models.CharField(max_length=10, blank=True, help_text="Dull characteristic")
    location = models.CharField(max_length=10, blank=True)
    bearing_seal = models.CharField(max_length=10, blank=True)
    gauge = models.CharField(max_length=10, blank=True)
    other_char = models.CharField(max_length=10, blank=True)
    reason_pulled = models.CharField(max_length=100, blank=True)

    # Assessment
    overall_condition = models.CharField(max_length=20, choices=Condition.choices, null=True, blank=True)
    recommendation = models.CharField(max_length=20, choices=Recommendation.choices, null=True, blank=True)

    # Link to design for traceability
    design = models.ForeignKey(
        "technology.Design", on_delete=models.SET_NULL, null=True, blank=True, related_name="bit_evaluations"
    )

    # Notes
    findings = models.TextField(blank=True)
    recommendations_detail = models.TextField(blank=True)

    # Resulting work order
    resulting_work_order = models.ForeignKey(
        WorkOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="source_evaluations"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bit_evaluations"
        ordering = ["-evaluation_date"]
        verbose_name = "Bit Evaluation"
        verbose_name_plural = "Bit Evaluations"

    def __str__(self):
        return f"{self.drill_bit.serial_number} - {self.evaluation_date}"
