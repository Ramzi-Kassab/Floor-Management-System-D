"""
ARDT FMS - Work Orders Models
Version: 5.4 - Sprint 4 Enhanced

Tables:
- drill_bits (P1) - Drill bit lifecycle tracking with repair history
- work_orders (P1) - Manufacturing/repair work orders
- work_order_documents (P1)
- work_order_photos (P1)
- work_order_materials (P1)
- work_order_time_logs (P1)
- bit_evaluations (P1)

Sprint 4 Additions:
- status_transition_logs - Audit trail for status changes
- bit_repair_history - Complete repair history per bit
- salvage_items - Tracking of salvaged parts
- repair_evaluations - Detailed repair assessments
- repair_approval_authorities - Cost-based approval thresholds
- repair_boms - Repair-specific bill of materials
- repair_bom_lines - BOM line items
- process_routes - Repair routing templates
- process_route_operations - Operations within routes
- operation_executions - Actual operation tracking
- work_order_costs - Cost summary per work order
"""

from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
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

    # Sprint 4: Serial number tracking for Aramco contract
    base_serial_number = models.CharField(
        max_length=50, blank=True,
        help_text="Original serial number before any repairs (for Aramco: stays same)"
    )
    current_display_serial = models.CharField(
        max_length=60, blank=True,
        help_text="Current display serial (e.g., SN-R1, SN-R2 for Aramco)"
    )
    revision_number = models.IntegerField(
        default=0,
        help_text="Number of repairs/revisions (0=new, 1=R1, 2=R2, etc.)"
    )
    is_aramco_contract = models.BooleanField(
        default=False,
        help_text="If true, serial increments on repair (R1, R2, R3)"
    )

    # Sprint 4: Physical and accounting status
    class PhysicalStatus(models.TextChoices):
        AT_ARDT = "AT_ARDT", "At ARDT Facility"
        AT_CUSTOMER = "AT_CUSTOMER", "At Customer Site"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        AT_RIG = "AT_RIG", "At Rig Site"
        SCRAPPED = "SCRAPPED", "Scrapped"

    class AccountingStatus(models.TextChoices):
        ARDT_OWNED = "ARDT_OWNED", "ARDT Owned"
        CUSTOMER_OWNED = "CUSTOMER_OWNED", "Customer Owned"
        ON_CONSIGNMENT = "ON_CONSIGNMENT", "On Consignment"
        SOLD = "SOLD", "Sold"
        WRITTEN_OFF = "WRITTEN_OFF", "Written Off"

    physical_status = models.CharField(
        max_length=20, choices=PhysicalStatus.choices,
        default=PhysicalStatus.AT_ARDT, blank=True
    )
    accounting_status = models.CharField(
        max_length=20, choices=AccountingStatus.choices,
        default=AccountingStatus.ARDT_OWNED, blank=True
    )

    # Sprint 4: Repair tracking
    total_repairs = models.IntegerField(default=0, help_text="Total number of repairs performed")
    last_repair_date = models.DateField(null=True, blank=True)
    last_repair_type = models.CharField(max_length=50, blank=True)

    # Sprint 4: Cost tracking
    original_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text="Original purchase/manufacturing cost"
    )
    total_repair_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text="Total cost of all repairs"
    )
    current_book_value = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text="Current accounting book value"
    )

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
    rig = models.ForeignKey("sales.Rig", on_delete=models.SET_NULL, null=True, blank=True, related_name="drill_bits")
    well = models.ForeignKey("sales.Well", on_delete=models.SET_NULL, null=True, blank=True, related_name="drill_bits")

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
    rig = models.ForeignKey("sales.Rig", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders")
    well = models.ForeignKey("sales.Well", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders")

    # Sprint 4: Repair-specific fields
    class RepairType(models.TextChoices):
        REDRESS = "REDRESS", "Redress"
        MAJOR_REPAIR = "MAJOR_REPAIR", "Major Repair"
        MINOR_REPAIR = "MINOR_REPAIR", "Minor Repair"
        REBUILD = "REBUILD", "Rebuild"
        REFURBISH = "REFURBISH", "Refurbish"

    class Disposition(models.TextChoices):
        RETURN_TO_STOCK = "RETURN_TO_STOCK", "Return to Stock"
        SHIP_TO_CUSTOMER = "SHIP_TO_CUSTOMER", "Ship to Customer"
        SCRAP = "SCRAP", "Scrap"
        PENDING = "PENDING", "Pending Decision"

    repair_type = models.CharField(
        max_length=20, choices=RepairType.choices,
        null=True, blank=True, help_text="Type of repair for repair work orders"
    )

    # Sprint 4: Approval workflow
    requires_approval = models.BooleanField(
        default=False, help_text="True if work order requires management approval"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="approved_work_orders"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Sprint 4: Cost estimates
    estimated_cost = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text="Estimated total cost before work starts"
    )
    actual_cost = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        help_text="Actual total cost after completion"
    )

    # Sprint 4: Disposition
    disposition = models.CharField(
        max_length=20, choices=Disposition.choices,
        null=True, blank=True, help_text="Final disposition of the bit"
    )
    disposition_notes = models.TextField(blank=True)

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
    department = models.ForeignKey("organization.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders")

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

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="uploaded_wo_documents")
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

    taken_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="taken_wo_photos")
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
    bom_line = models.ForeignKey("technology.BOMLine", on_delete=models.SET_NULL, null=True, blank=True, related_name="wo_materials")

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
    step = models.ForeignKey("procedures.ProcedureStep", on_delete=models.SET_NULL, null=True, blank=True, related_name="wo_time_logs")
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
    rig = models.ForeignKey("sales.Rig", on_delete=models.SET_NULL, null=True, blank=True, related_name="bit_evaluations")
    well = models.ForeignKey("sales.Well", on_delete=models.SET_NULL, null=True, blank=True, related_name="bit_evaluations")
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


# =============================================================================
# SPRINT 4: STATUS TRACKING & AUDIT
# =============================================================================

class StatusTransitionLog(models.Model):
    """
    Sprint 4: Audit trail for status changes on any model.
    Uses GenericForeignKey to track status changes across DrillBit, WorkOrder, etc.
    """
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='status_transition_logs'
    )
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    from_status = models.CharField(max_length=30, blank=True)
    to_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="status_transitions"
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, help_text="Reason for status change")

    class Meta:
        db_table = "status_transition_logs"
        ordering = ["-changed_at"]
        verbose_name = "Status Transition Log"
        verbose_name_plural = "Status Transition Logs"
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["changed_at"]),
        ]

    def __str__(self):
        return f"{self.content_type.model} #{self.object_id}: {self.from_status} → {self.to_status}"


class BitRepairHistory(models.Model):
    """
    Sprint 4: Complete repair history for a drill bit.
    Tracks every repair performed, costs, and condition changes.
    """
    class RepairType(models.TextChoices):
        REDRESS = "REDRESS", "Redress"
        MAJOR_REPAIR = "MAJOR_REPAIR", "Major Repair"
        MINOR_REPAIR = "MINOR_REPAIR", "Minor Repair"
        REBUILD = "REBUILD", "Rebuild"
        REFURBISH = "REFURBISH", "Refurbish"

    drill_bit = models.ForeignKey(
        DrillBit, on_delete=models.CASCADE, related_name="repair_history"
    )
    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="bit_repair_records"
    )

    repair_number = models.IntegerField(help_text="Repair sequence number for this bit")
    repair_date = models.DateField()
    repair_type = models.CharField(max_length=20, choices=RepairType.choices)

    # Work details
    work_performed = models.TextField(blank=True)
    parts_replaced = models.TextField(blank=True)

    # Costs
    labor_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    material_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    overhead_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    @property
    def total_cost(self):
        return self.labor_cost + self.material_cost + self.overhead_cost

    # Condition
    condition_before = models.CharField(max_length=50, blank=True)
    condition_after = models.CharField(max_length=50, blank=True)

    # Serial tracking for Aramco
    serial_before = models.CharField(max_length=60, blank=True)
    serial_after = models.CharField(max_length=60, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="created_repair_records"
    )

    class Meta:
        db_table = "bit_repair_history"
        ordering = ["drill_bit", "-repair_number"]
        verbose_name = "Bit Repair History"
        verbose_name_plural = "Bit Repair Histories"
        unique_together = ["drill_bit", "repair_number"]

    def __str__(self):
        return f"{self.drill_bit.serial_number} - Repair #{self.repair_number}"


class SalvageItem(models.Model):
    """
    Sprint 4: Tracking of salvaged parts from scrapped or repaired bits.
    """
    class SalvageType(models.TextChoices):
        BODY = "BODY", "Bit Body"
        CUTTER = "CUTTER", "Cutter"
        NOZZLE = "NOZZLE", "Nozzle"
        BEARING = "BEARING", "Bearing"
        CONE = "CONE", "Cone"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available for Reuse"
        RESERVED = "RESERVED", "Reserved"
        CONSUMED = "CONSUMED", "Consumed in Repair"
        SCRAPPED = "SCRAPPED", "Scrapped"

    salvage_number = models.CharField(max_length=30, unique=True)
    drill_bit = models.ForeignKey(
        DrillBit, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="salvaged_items"
    )
    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="salvaged_items"
    )

    salvage_type = models.CharField(max_length=20, choices=SalvageType.choices)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)

    # Condition assessment
    condition_rating = models.IntegerField(
        null=True, blank=True,
        help_text="Condition rating 1-10 (10=excellent)"
    )
    reuse_potential = models.CharField(max_length=100, blank=True)

    # Location
    warehouse = models.ForeignKey(
        "sales.Warehouse", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="salvage_items"
    )
    storage_location = models.CharField(max_length=100, blank=True)

    # Dates
    salvage_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)

    # Reuse tracking
    reused_in_work_order = models.ForeignKey(
        WorkOrder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reused_salvage_items"
    )
    reused_date = models.DateField(null=True, blank=True)

    # Value
    estimated_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Photo
    photo = models.ImageField(upload_to="salvage_photos/", null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="created_salvage_items"
    )

    class Meta:
        db_table = "salvage_items"
        ordering = ["-salvage_date"]
        verbose_name = "Salvage Item"
        verbose_name_plural = "Salvage Items"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["salvage_type"]),
        ]

    def __str__(self):
        return f"{self.salvage_number} - {self.salvage_type}"


# =============================================================================
# SPRINT 4: EVALUATION & APPROVAL
# =============================================================================

class RepairApprovalAuthority(models.Model):
    """
    Sprint 4: Defines approval authorities based on cost thresholds.
    E.g., costs < $5000 = auto-approve, $5000-$25000 = Operations Manager, etc.
    """
    name = models.CharField(max_length=100)
    min_amount = models.DecimalField(max_digits=15, decimal_places=2)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2)
    authorized_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="approval_authorities", blank=True
    )
    requires_justification = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "repair_approval_authorities"
        ordering = ["min_amount"]
        verbose_name = "Repair Approval Authority"
        verbose_name_plural = "Repair Approval Authorities"

    def __str__(self):
        return f"{self.name} (${self.min_amount:,.0f} - ${self.max_amount:,.0f})"

    def can_approve(self, amount):
        """Check if this authority can approve the given amount."""
        return self.min_amount <= Decimal(str(amount)) <= self.max_amount


class RepairEvaluation(models.Model):
    """
    Sprint 4: Detailed repair evaluation with cost estimation and approval workflow.
    """
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        COMPLETED = "COMPLETED", "Completed"

    evaluation_number = models.CharField(max_length=30, unique=True)
    drill_bit = models.ForeignKey(
        DrillBit, on_delete=models.CASCADE, related_name="repair_evaluations"
    )

    # IADC grading
    inner_rows_grade = models.CharField(max_length=10, blank=True)
    outer_rows_grade = models.CharField(max_length=10, blank=True)
    dull_characteristic = models.CharField(max_length=20, blank=True)
    location_code = models.CharField(max_length=10, blank=True)
    gauge_condition = models.CharField(max_length=20, blank=True)

    # Damage assessment
    damage_assessment = models.TextField()
    recommended_repair = models.TextField(blank=True)

    # Cost estimation
    estimated_labor_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    estimated_labor_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_material_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    estimated_overhead = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    @property
    def estimated_repair_cost(self):
        labor = self.estimated_labor_hours * self.estimated_labor_rate
        return labor + self.estimated_material_cost + self.estimated_overhead

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    repair_recommended = models.BooleanField(default=True)

    # Approval
    requires_approval = models.BooleanField(default=False)
    approval_authority = models.ForeignKey(
        RepairApprovalAuthority, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="evaluations"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_evaluations"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)

    # Evaluator
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="performed_evaluations"
    )
    evaluated_at = models.DateTimeField(auto_now_add=True)

    # Link to resulting work order
    resulting_work_order = models.OneToOneField(
        WorkOrder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="repair_evaluation"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "repair_evaluations"
        ordering = ["-created_at"]
        verbose_name = "Repair Evaluation"
        verbose_name_plural = "Repair Evaluations"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["drill_bit", "status"]),
        ]

    def __str__(self):
        return f"{self.evaluation_number} - {self.drill_bit.serial_number}"


class RepairBOM(models.Model):
    """
    Sprint 4: Repair-specific Bill of Materials.
    """
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        APPROVED = "APPROVED", "Approved"
        ISSUED = "ISSUED", "Issued"
        COMPLETED = "COMPLETED", "Completed"

    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name="repair_boms"
    )
    master_bom = models.ForeignKey(
        "technology.BOM", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="repair_boms"
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # Costs
    estimated_material_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    actual_material_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_repair_boms"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "repair_boms"
        ordering = ["-created_at"]
        verbose_name = "Repair BOM"
        verbose_name_plural = "Repair BOMs"

    def __str__(self):
        return f"RepairBOM for {self.work_order.wo_number}"

    def calculate_costs(self):
        """Calculate estimated and actual costs from lines."""
        from django.db.models import Sum
        totals = self.lines.aggregate(
            estimated=Sum("estimated_total"),
            actual=Sum("actual_total")
        )
        self.estimated_material_cost = totals["estimated"] or 0
        self.actual_material_cost = totals["actual"] or 0
        self.save(update_fields=["estimated_material_cost", "actual_material_cost"])


class RepairBOMLine(models.Model):
    """
    Sprint 4: Line items in a Repair BOM.
    """
    repair_bom = models.ForeignKey(
        RepairBOM, on_delete=models.CASCADE, related_name="lines"
    )
    line_number = models.IntegerField()

    inventory_item = models.ForeignKey(
        "inventory.InventoryItem", on_delete=models.PROTECT,
        related_name="repair_bom_lines"
    )

    # Quantities
    quantity_required = models.DecimalField(max_digits=10, decimal_places=3)
    quantity_issued = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    quantity_consumed = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    quantity_returned = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    # Costs
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    @property
    def estimated_total(self):
        return self.quantity_required * self.unit_cost

    @property
    def actual_total(self):
        return (self.quantity_consumed - self.quantity_returned) * self.unit_cost

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "repair_bom_lines"
        ordering = ["repair_bom", "line_number"]
        unique_together = ["repair_bom", "line_number"]
        verbose_name = "Repair BOM Line"
        verbose_name_plural = "Repair BOM Lines"

    def __str__(self):
        return f"{self.repair_bom.work_order.wo_number} Line {self.line_number}"


# =============================================================================
# SPRINT 4: PROCESS ROUTING & EXECUTION
# =============================================================================

class ProcessRoute(models.Model):
    """
    Sprint 4: Template for repair process routing.
    Defines the sequence of operations for a specific repair type.
    """
    route_number = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Applicability
    repair_type = models.CharField(
        max_length=20, choices=WorkOrder.RepairType.choices,
        null=True, blank=True
    )
    bit_types = models.JSONField(
        null=True, blank=True,
        help_text="List of applicable bit types, e.g., ['FC', 'RC']"
    )

    # Status
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)

    # Estimated totals
    estimated_duration_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    estimated_labor_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="created_routes"
    )

    class Meta:
        db_table = "process_routes"
        ordering = ["route_number"]
        verbose_name = "Process Route"
        verbose_name_plural = "Process Routes"

    def __str__(self):
        return f"{self.route_number} - {self.name}"


class ProcessRouteOperation(models.Model):
    """
    Sprint 4: Individual operations within a process route.
    """
    route = models.ForeignKey(
        ProcessRoute, on_delete=models.CASCADE, related_name="operations"
    )
    sequence = models.IntegerField(help_text="Operation sequence number (10, 20, 30...)")

    operation_code = models.CharField(max_length=20)
    operation_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Work center
    work_center = models.CharField(max_length=50, blank=True)

    # Time and cost
    standard_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    labor_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # QC requirements
    requires_qc = models.BooleanField(default=False)
    qc_checklist = models.TextField(blank=True)

    # Safety
    safety_requirements = models.TextField(blank=True)

    class Meta:
        db_table = "process_route_operations"
        ordering = ["route", "sequence"]
        unique_together = ["route", "sequence"]
        verbose_name = "Process Route Operation"
        verbose_name_plural = "Process Route Operations"

    def __str__(self):
        return f"{self.route.route_number} Seq {self.sequence}: {self.operation_name}"


class OperationExecution(models.Model):
    """
    Sprint 4: Actual execution of an operation on a work order.
    """
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        SKIPPED = "SKIPPED", "Skipped"

    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name="operation_executions"
    )
    route_operation = models.ForeignKey(
        ProcessRouteOperation, on_delete=models.PROTECT,
        related_name="executions"
    )
    sequence = models.IntegerField()

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Operator
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="operation_executions"
    )

    # Time tracking
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    # Cost
    labor_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # QC
    qc_performed = models.BooleanField(default=False)
    qc_passed = models.BooleanField(null=True, blank=True)
    qc_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="qc_operations"
    )
    qc_notes = models.TextField(blank=True)

    # Notes
    operator_notes = models.TextField(blank=True)
    issues_encountered = models.TextField(blank=True)

    class Meta:
        db_table = "operation_executions"
        ordering = ["work_order", "sequence"]
        verbose_name = "Operation Execution"
        verbose_name_plural = "Operation Executions"
        indexes = [
            models.Index(fields=["work_order", "status"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.work_order.wo_number} Op {self.sequence}: {self.status}"


class WorkOrderCost(models.Model):
    """
    Sprint 4: Cost summary for a work order.
    Aggregates all costs (labor, materials, overhead) in one place.
    """
    work_order = models.OneToOneField(
        WorkOrder, on_delete=models.CASCADE,
        primary_key=True, related_name="cost_summary"
    )

    # Labor
    estimated_labor_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    actual_labor_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    labor_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Materials
    estimated_material_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    actual_material_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Overhead
    overhead_rate_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overhead_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Subcontractor
    subcontractor_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Totals
    total_estimated_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_actual_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    @property
    def variance(self):
        return self.total_actual_cost - self.total_estimated_cost

    @property
    def variance_percent(self):
        if self.total_estimated_cost:
            return (self.variance / self.total_estimated_cost) * 100
        return 0

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "work_order_costs"
        verbose_name = "Work Order Cost"
        verbose_name_plural = "Work Order Costs"

    def __str__(self):
        return f"Costs for {self.work_order.wo_number}"

    def recalculate(self):
        """Recalculate all costs from related records."""
        # Labor from operation executions
        from django.db.models import Sum
        labor_agg = self.work_order.operation_executions.aggregate(
            hours=Sum("actual_hours"),
            cost=Sum("labor_cost")
        )
        self.actual_labor_hours = labor_agg["hours"] or 0
        self.labor_cost = labor_agg["cost"] or 0

        # Materials from repair BOMs
        material_agg = self.work_order.repair_boms.aggregate(
            cost=Sum("actual_material_cost")
        )
        self.actual_material_cost = material_agg["cost"] or 0

        # Overhead
        subtotal = self.labor_cost + self.actual_material_cost
        self.overhead_cost = subtotal * (self.overhead_rate_percent / 100)

        # Total
        self.total_actual_cost = (
            self.labor_cost +
            self.actual_material_cost +
            self.overhead_cost +
            self.subcontractor_cost
        )

        self.save()
