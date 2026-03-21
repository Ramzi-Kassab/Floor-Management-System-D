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
- work_order_costs - Cost summary per work order
"""

from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


# =============================================================================
# REFERENCE TABLES
# =============================================================================
# Note: BitSize and BitType models have been moved to apps.technology.models


class Location(models.Model):
    """
    Physical locations where bits can be stored/tracked.
    """
    class LocationType(models.TextChoices):
        WAREHOUSE = "WAREHOUSE", "Warehouse"
        RECEIVING = "RECEIVING", "Receiving Area"
        WIP = "WIP", "Work In Progress"
        DISPATCH = "DISPATCH", "Dispatch Area"
        INSPECTION = "INSPECTION", "Inspection Area"
        REPAIR_SHOP = "REPAIR_SHOP", "Repair Shop"
        RIG = "RIG", "Rig Site"
        EVALUATION = "EVALUATION", "Evaluation Area"
        QC = "QC", "QC Area"
        SCRAP = "SCRAP", "Scrap Yard"
        USA = "USA", "USA Facility"
        FACTORY = "FACTORY", "Factory"
        TRANSIT = "TRANSIT", "In Transit"

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=20, choices=LocationType.choices)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    rig = models.ForeignKey(
        "sales.Rig",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bit_locations",
        help_text="Link to rig if location_type is RIG"
    )

    class Meta:
        db_table = "locations"
        ordering = ["location_type", "name"]
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"


class DrillBit(models.Model):
    """
    🟢 P1: Drill bit master - tracks individual bits through their lifecycle.
    """

    class BitCategory(models.TextChoices):
        """Category of drill bit - FC (Fixed Cutter/PDC) or RC (Roller Cone)."""
        FC = "FC", "Fixed Cutter (PDC)"
        RC = "RC", "Roller Cone"

    class Status(models.TextChoices):
        """Process status — where is this bit in the workflow?"""
        ORDERED = "ORDERED", "Ordered"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        UNREGISTERED = "UNREGISTERED", "Unregistered"
        RECEIVING = "RECEIVING", "Receiving"
        RECEIVED = "RECEIVED", "Received"
        IN_COMPONENTS = "IN_COMPONENTS", "In Components"
        IN_EVALUATION = "IN_EVALUATION", "In Evaluation"
        IN_PRODUCTION = "IN_PRODUCTION", "In Production"
        IN_PRODUCTION_USA = "IN_PRODUCTION_USA", "In Production (USA)"
        IN_REPAIR = "IN_REPAIR", "In Repair"
        IN_STOCK = "IN_STOCK", "In Stock"
        DISPATCHED = "DISPATCHED", "Dispatched"
        IN_FIELD = "IN_FIELD", "In Field"
        BACKLOADED = "BACKLOADED", "Backloaded"
        HOLD = "HOLD", "On Hold"
        REJECTED = "REJECTED", "Rejected"
        USA_REPAIR = "USA_REPAIR", "USA Repair"
        DE_BRAZED = "DE_BRAZED", "De-Brazed"
        SAVED_BODY = "SAVED_BODY", "Saved Body"
        SCRAPPED = "SCRAPPED", "Scrapped"

    class Condition(models.TextChoices):
        """What IS this bit right now?"""
        COMPONENTS = "COMPONENTS", "Components"
        FINISHED_GOOD = "FINISHED_GOOD", "Finished Good"
        REPAIRED = "REPAIRED", "Repaired"
        RERUN = "RERUN", "Rerun"
        RETROFITTED = "RETROFITTED", "Retrofitted"
        USED = "USED", "Used"
        NOT_USED = "NOT_USED", "Not Used"
        DE_BRAZED = "DE_BRAZED", "De-Brazed"
        SAVED_BODY = "SAVED_BODY", "Saved Body"
        SCRAPPED = "SCRAPPED", "Scrapped"

    class Ownership(models.TextChoices):
        """Commercial arrangement — who owns/controls this bit?"""
        RENTAL = "RENTAL", "Rental"
        CUSTOMER = "CUSTOMER", "Customer"
        MANUFACTURE = "MANUFACTURE", "Manufacture"
        TRIAL = "TRIAL", "Trial"
        ARDT = "ARDT", "ARDT"

    serial_number = models.CharField(max_length=50, unique=True)
    # Note: Field kept as bit_type for backward compatibility, but uses BitCategory choices
    bit_type = models.CharField(
        max_length=20,
        choices=BitCategory.choices,
        default=BitCategory.FC,
        help_text="Bit category: FC (Fixed Cutter) or RC (Roller Cone)"
    )

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
        help_text="Legacy: use account instead. If true, serial increments on repair."
    )
    account = models.ForeignKey(
        'sales.Account', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='drill_bits',
        help_text='Account this bit belongs to (LSTK, ARAMCO, UR, L3, L4, ARDT, etc.)'
    )

    # Sprint 4: Physical and accounting status (LEGACY — kept for backward compat)
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

    # === NEW 4-Column Model (Feb 2026) ===
    condition = models.CharField(
        max_length=20, choices=Condition.choices,
        default=Condition.COMPONENTS, blank=True,
        help_text="What IS this bit right now? (Finished Good, Used, Repaired, etc.)"
    )
    ownership = models.CharField(
        max_length=20, choices=Ownership.choices,
        default=Ownership.ARDT, blank=True,
        help_text="Commercial arrangement (Rental, Customer, Manufacture, Trial, ARDT)"
    )
    is_trial = models.BooleanField(
        default=False,
        help_text="Trial/test bit — always ARDT-owned"
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
    bom = models.ForeignKey(
        "technology.BOM", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="drill_bits",
        help_text="Legacy: L5 BOM (use brazing_bom/system_bom instead)"
    )
    brazing_bom = models.ForeignKey(
        "technology.BOM", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="drillbits_brazing",
        verbose_name="Brazing BOM",
        help_text="L5 Brazing BOM - internal/production (may have cutter suffix)"
    )
    system_bom = models.ForeignKey(
        "technology.BOM", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="drillbits_system",
        verbose_name="System BOM",
        help_text="L5 System BOM - client-facing (fixed MAT#)"
    )
    # Order level: L3/L4 from design, L5 when BOM is assigned
    level = models.CharField(
        max_length=5, blank=True,
        help_text="Order level: 3=Design only, 4=Design welded, 5=With BOM/cutters"
    )

    size = models.DecimalField(max_digits=6, decimal_places=3, help_text="Size in inches")
    iadc_code = models.CharField(max_length=20, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNREGISTERED)

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

    # Change log — [{field, old, new, who, when}, ...]
    change_log = models.JSONField(default=list, blank=True, help_text='Audit trail of field changes')

    def log_change(self, field, old_value, new_value, user=None):
        """Record a field change in the audit log."""
        from django.utils import timezone
        if str(old_value) == str(new_value):
            return
        entry = {
            'field': field,
            'old': str(old_value) if old_value else '',
            'new': str(new_value) if new_value else '',
            'who': (user.get_full_name() or user.username) if user else '',
            'when': timezone.now().isoformat(),
        }
        if not isinstance(self.change_log, list):
            self.change_log = []
        self.change_log.append(entry)

    def get_release_destination_code(self):
        """Return the location code where this bit should go when released for production."""
        level = self.level or (self.design.order_level if self.design else '')
        if level in ('3', '5.5'):
            return 'SUB-ARC'  # Sub Arc Welding Area
        elif level == '4':
            return 'PDC-EVAL'  # PDC Evaluation Area
        else:
            return 'WIP'  # General production floor (repair)

    def get_release_destination(self):
        """Return the Location object for release destination."""
        code = self.get_release_destination_code()
        return Location.objects.filter(code=code, is_active=True).first()

    def move_to(self, location_code_or_type, reason='', user=None):
        """
        Move bit to a new location by code or location_type.
        Creates BitEvent(TRANSFER) and updates current_location + bit_location.
        Returns the new Location or None if not found.
        """
        from django.utils import timezone
        new_loc = Location.objects.filter(
            models.Q(code=location_code_or_type) | models.Q(location_type=location_code_or_type),
            is_active=True
        ).first()
        if not new_loc:
            return None
        from_loc = self.bit_location
        if from_loc and from_loc.pk == new_loc.pk:
            return new_loc  # already there
        self.log_change('Location', str(from_loc) if from_loc else '—', str(new_loc), user)
        self.bit_location = new_loc
        self.save(update_fields=['bit_location', 'change_log', 'updated_at'])
        BitEvent.objects.create(
            bit=self,
            event_type=BitEvent.EventType.TRANSFER,
            event_date=timezone.now(),
            location=new_loc,
            from_location=from_loc,
            to_location=new_loc,
            notes=reason or f'Auto-moved to {new_loc.name}',
            performed_by=user,
        )
        return new_loc

    # Phase 2: Bit Tracking fields (from migration 0005)
    # LEGACY — kept for data migration; new code uses `status` + `condition` instead
    class LifecycleStatus(models.TextChoices):
        NEW = "NEW", "New"
        DEPLOYED = "DEPLOYED", "Deployed"
        BACKLOADED = "BACKLOADED", "Backloaded"
        EVALUATION = "EVALUATION", "In Evaluation"
        HOLD = "HOLD", "On Hold"
        IN_REPAIR = "IN_REPAIR", "In Repair"
        REPAIRED = "REPAIRED", "Repaired"
        USA_REPAIR = "USA_REPAIR", "USA Repair"
        RERUN = "RERUN", "Rerun Ready"
        SCRAP = "SCRAP", "Scrapped"
        SAVED_BODY = "SAVED_BODY", "Saved Body"

    lifecycle_status = models.CharField(
        max_length=20,
        choices=LifecycleStatus.choices,
        default=LifecycleStatus.NEW,
        blank=True,
        help_text="LEGACY — use status + condition instead"
    )
    mat_number = models.CharField(max_length=20, blank=True, help_text="MAT number for inventory")
    received_date = models.DateField(null=True, blank=True, help_text="Date bit was received")
    scrap_date = models.DateField(null=True, blank=True, help_text="Date bit was scrapped")

    # Deployment counters
    deployment_count = models.PositiveIntegerField(default=0, help_text="Times deployed")
    backload_count = models.PositiveIntegerField(default=0, help_text="Times returned to factory")
    last_deployed_date = models.DateField(null=True, blank=True, help_text="Last deployment date")
    last_backload_date = models.DateField(null=True, blank=True, help_text="Last backload date")

    # Repair counters
    repair_count = models.PositiveIntegerField(default=0, help_text="Repairs completed at ARDT")
    repair_count_usa = models.PositiveIntegerField(default=0, help_text="Repairs completed in USA")
    rerun_count_factory = models.PositiveIntegerField(default=0, help_text="Factory reruns (charged)")
    rerun_count_field = models.PositiveIntegerField(default=0, help_text="Field reruns (no charge)")

    # Phase 2: Reference links (BitSize and BitType now in technology app)
    bit_size_ref = models.ForeignKey(
        "technology.BitSize",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="drill_bits",
        help_text="Standard bit size reference"
    )
    product_type = models.ForeignKey(
        "technology.BitType",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="drill_bits",
        help_text="Product model (e.g., GT65RHS)"
    )
    bit_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_bits",
        help_text="Current physical location (Phase 2)"
    )

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

    def sync_from_design(self):
        """
        Auto-populate fields from linked Design and BOM.
        Call this when design or bom changes.
        """
        if self.bom and self.bom.design:
            # If BOM is set, use its design
            self.design = self.bom.design

        if self.design:
            # Sync from Design
            if self.design.size:
                self.bit_size_ref = self.design.size
                self.size = self.design.size.size_decimal if hasattr(self.design.size, 'size_decimal') else self.design.size.size
            if self.design.category:
                self.bit_type = self.design.category
            if self.design.iadc_code:
                self.iadc_code = self.design.iadc_code
            if hasattr(self.design, 'product_type') and self.design.product_type:
                self.product_type = self.design.product_type
            # Level: from design (L3/L4) — only if not already set by user
            # User may have explicitly set L5, so don't overwrite that
            if not self.level and self.design.order_level:
                self.level = self.design.order_level

        # Sync MAT number from BOM if present
        has_bom = self.bom_id or self.brazing_bom_id or self.system_bom_id
        if has_bom and self.bom and self.bom.code:
            self.mat_number = self.bom.code
        elif self.bom and self.bom.code:
            self.mat_number = self.bom.code

    # Account code → Ownership mapping
    ACCOUNT_OWNERSHIP_MAP = {
        'UR': Ownership.RENTAL,
        'WFD': Ownership.RENTAL,
        'ARAMCO': Ownership.CUSTOMER,
        'LSTK': Ownership.CUSTOMER,
        'RC-LSTK': Ownership.CUSTOMER,
        'HALLIBURTON': Ownership.CUSTOMER,
        'HAL_REGIONAL': Ownership.CUSTOMER,
        'SUB': Ownership.CUSTOMER,
        'L3': Ownership.MANUFACTURE,
        'L4': Ownership.MANUFACTURE,
        'ARDT': Ownership.ARDT,
    }

    def determine_initial_status(self):
        """
        Determine the correct initial status based on design/BOM presence.

        Business rules:
          - No design                        → UNREGISTERED
          - Has design (L3/L4), with or
            without BOM (L5)                 → ORDERED, condition=COMPONENTS

        Note: Having a BOM does NOT make a bit FINISHED_GOOD or IN_STOCK.
        FINISHED_GOOD is only set after manufacturing is complete.
        L5 (BOM) is tracked as part of the bit's identity but does not
        change the initial condition.
        """
        if self.design_id:
            self.status = self.Status.ORDERED
            self.condition = self.Condition.COMPONENTS
        else:
            self.status = self.Status.UNREGISTERED
            # condition stays as-is (caller sets it, e.g. NOT_USED from batch)

    def derive_ownership(self):
        """Derive ownership from account + is_trial flag. Call before save when account changes."""
        if self.is_trial:
            self.ownership = self.Ownership.TRIAL
        elif self.account_id:
            account_code = self.account.code if hasattr(self.account, 'code') else ''
            self.ownership = self.ACCOUNT_OWNERSHIP_MAP.get(account_code, self.Ownership.ARDT)
        else:
            self.ownership = self.Ownership.ARDT

    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.qr_code = f"BIT-{self.serial_number}"
        super().save(*args, **kwargs)

    # =========================================================================
    # LIFECYCLE MANAGEMENT METHODS
    # =========================================================================

    # Work Order statuses that indicate active/in-progress work
    ACTIVE_WO_STATUSES = [
        'DRAFT', 'PLANNED', 'RELEASED', 'IN_PROGRESS',
        'ON_HOLD', 'QC_PENDING', 'QC_PASSED', 'QC_FAILED'
    ]

    # Work Order statuses that indicate completed/finalized work
    FINAL_WO_STATUSES = ['COMPLETED', 'CANCELLED']

    def has_active_work_order(self):
        """
        Check if this drill bit has any active (non-completed, non-cancelled) work order.
        Returns True if there's an active WO blocking new work.
        """
        return self.work_orders.filter(status__in=self.ACTIVE_WO_STATUSES).exists()

    def get_active_work_order(self):
        """
        Get the active work order for this drill bit, if any.
        Returns the WO object or None.
        """
        return self.work_orders.filter(status__in=self.ACTIVE_WO_STATUSES).first()

    def is_in_production_plan(self):
        """
        Check if this drill bit is currently in the production plan (PLANNED status).
        """
        return self.plan_entries.filter(status='PLANNED').exists()

    def get_active_plan_entry(self):
        """
        Get the active production plan entry for this drill bit, if any.
        """
        return self.plan_entries.filter(status='PLANNED').first()

    def is_available_for_planning(self):
        """
        Check if this drill bit can be added to the production plan.
        Returns True if:
        - No active work order exists
        - Not already in the production plan
        """
        if self.has_active_work_order():
            return False
        if self.is_in_production_plan():
            return False
        return True

    def get_blocking_reason(self):
        """
        Get the reason why this drill bit cannot be planned.
        Returns a tuple of (reason_code, message) or (None, None) if available.
        """
        # Check for active work order first
        active_wo = self.get_active_work_order()
        if active_wo:
            return (
                'ACTIVE_WO',
                f"Active Work Order {active_wo.wo_number} ({active_wo.get_status_display()})"
            )

        # Check for active plan entry
        plan_entry = self.get_active_plan_entry()
        if plan_entry:
            return (
                'IN_PLAN',
                f"Already in production plan (#{plan_entry.pk})"
            )

        return (None, None)

    def get_availability_status(self):
        """
        Get a structured availability status for UI display.
        Returns dict with: available, status_code, status_label, blocking_reason, blocking_wo
        """
        active_wo = self.get_active_work_order()
        if active_wo:
            return {
                'available': False,
                'status_code': 'ACTIVE_WO',
                'status_label': 'In WIP',
                'blocking_reason': f"WO: {active_wo.wo_number}",
                'blocking_wo': active_wo,
                'blocking_wo_id': active_wo.pk,
            }

        plan_entry = self.get_active_plan_entry()
        if plan_entry:
            return {
                'available': False,
                'status_code': 'IN_PLAN',
                'status_label': 'Planned',
                'blocking_reason': f"Plan entry #{plan_entry.pk}",
                'blocking_wo': None,
                'blocking_wo_id': None,
            }

        return {
            'available': True,
            'status_code': 'AVAILABLE',
            'status_label': 'Available',
            'blocking_reason': None,
            'blocking_wo': None,
            'blocking_wo_id': None,
        }


class BitEvent(models.Model):
    """
    Track all lifecycle events for a drill bit (Phase 2).
    """
    class EventType(models.TextChoices):
        RECEIVED = "RECEIVED", "Received (New)"
        DEPLOYED = "DEPLOYED", "Deployed to Rig"
        BACKLOADED = "BACKLOADED", "Backloaded to Factory"
        EVALUATION_START = "EVALUATION_START", "Evaluation Started"
        EVALUATION_COMPLETE = "EVALUATION_COMPLETE", "Evaluation Complete"
        REPAIR_DECISION = "REPAIR_DECISION", "Decision: Repair"
        RERUN_DECISION_FACTORY = "RERUN_DECISION_FACTORY", "Decision: Rerun (Factory)"
        RERUN_DECISION_FIELD = "RERUN_DECISION_FIELD", "Decision: Rerun (Field)"
        USA_REPAIR_DECISION = "USA_REPAIR_DECISION", "Decision: USA Repair"
        SCRAP_DECISION = "SCRAP_DECISION", "Decision: Scrap"
        HOLD_DECISION = "HOLD_DECISION", "Decision: Hold"
        REPAIR_START = "REPAIR_START", "Repair Started"
        REPAIR_COMPLETE = "REPAIR_COMPLETE", "Repair Complete"
        USA_REPAIR_SENT = "USA_REPAIR_SENT", "Sent to USA"
        USA_REPAIR_RECEIVED = "USA_REPAIR_RECEIVED", "Received from USA"
        QC_PASS = "QC_PASS", "QC Passed"
        QC_FAIL = "QC_FAIL", "QC Failed"
        TRANSFER = "TRANSFER", "Stock Transfer"
        RELOCATION = "RELOCATION", "Relocation (Rig to Rig)"
        SCRAPPED = "SCRAPPED", "Scrapped"
        BODY_SAVED = "BODY_SAVED", "Body Saved"

    bit = models.ForeignKey(
        DrillBit,
        on_delete=models.CASCADE,
        related_name="bit_events"
    )
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    event_date = models.DateTimeField()
    notes = models.TextField(blank=True)

    # Location tracking
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="bit_events"
    )
    from_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bit_events_from"
    )
    to_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bit_events_to"
    )

    # Related entities
    work_order = models.ForeignKey(
        "WorkOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bit_events"
    )
    rig = models.ForeignKey(
        "sales.Rig",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bit_events"
    )
    well = models.ForeignKey(
        "sales.Well",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bit_events"
    )

    # Audit
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="performed_bit_events"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bit_events"
        ordering = ["-event_date"]
        verbose_name = "Bit Event"
        verbose_name_plural = "Bit Events"
        indexes = [
            models.Index(fields=["bit", "event_date"], name="bit_events_bit_id_201c1f_idx"),
            models.Index(fields=["event_type"], name="bit_events_event_t_1b7af6_idx"),
            models.Index(fields=["performed_by", "event_date"], name="bit_events_perform_6e3064_idx"),
        ]

    def __str__(self):
        return f"{self.bit.serial_number} - {self.get_event_type_display()} ({self.event_date})"


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

    # Account & Customer
    account = models.ForeignKey(
        'sales.Account', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='work_orders',
        help_text='Account driving WO number, pricing, and workflow rules'
    )
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

    # Job Card Specific Fields
    brazing_mat_no = models.CharField(
        max_length=100, blank=True,
        help_text="Brazing MAT# - Free text (e.g., 123456M1, 3251477-Testing Trifex)"
    )
    system_mat_no = models.CharField(
        max_length=50, blank=True,
        help_text="System L5 MAT# - Fixed, shared with client/sales"
    )
    brazing_bom = models.ForeignKey(
        "technology.BOM", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="workorders_brazing",
        verbose_name="Brazing BOM",
        help_text="L5 Brazing BOM - internal/production"
    )
    system_bom = models.ForeignKey(
        "technology.BOM", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="workorders_system",
        verbose_name="System BOM",
        help_text="L5 System BOM - client-facing"
    )
    drss_no = models.CharField(
        max_length=50, blank=True,
        help_text="DRSS Request Number"
    )
    reference_po_no = models.CharField(
        max_length=50, blank=True,
        help_text="Reference/PO Number"
    )
    contract_no = models.CharField(
        max_length=50, blank=True,
        help_text="Contract Number"
    )
    from_location_text = models.CharField(
        max_length=100, blank=True,
        help_text="Source location text (e.g., ARAMCO, LSTK, ARDT-LV4)"
    )
    bit_received_date = models.DateField(
        null=True, blank=True,
        help_text="Date bit was received for this work order"
    )

    # Evaluation tracking
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="wo_evaluations_performed"
    )
    evaluated_at = models.DateTimeField(null=True, blank=True)
    qc_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="wo_qc_performed"
    )
    qc_at = models.DateTimeField(null=True, blank=True)
    reviewed_by_eng = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="wo_eng_reviews"
    )
    eng_review_at = models.DateTimeField(null=True, blank=True)

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

    # Status transition rules — forward flow with hold/cancel branches
    STATUS_TRANSITIONS = {
        'DRAFT': ['PLANNED', 'RELEASED', 'CANCELLED'],
        'PLANNED': ['RELEASED', 'ON_HOLD', 'CANCELLED'],
        'RELEASED': ['IN_PROGRESS', 'ON_HOLD', 'CANCELLED'],
        'IN_PROGRESS': ['QC_PENDING', 'ON_HOLD', 'CANCELLED'],
        'ON_HOLD': ['PLANNED', 'RELEASED', 'IN_PROGRESS', 'CANCELLED'],
        'QC_PENDING': ['QC_PASSED', 'QC_FAILED', 'ON_HOLD'],
        'QC_FAILED': ['IN_PROGRESS', 'ON_HOLD', 'CANCELLED'],
        'QC_PASSED': ['COMPLETED'],
        'COMPLETED': [],  # terminal
        'CANCELLED': [],  # terminal
    }

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

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        if self.pk:
            try:
                original = WorkOrder.objects.only('status').get(pk=self.pk)
            except WorkOrder.DoesNotExist:
                return
            if original.status != self.status:
                allowed = self.STATUS_TRANSITIONS.get(original.status, [])
                if self.status not in allowed:
                    raise ValidationError({
                        'status': f"Cannot change work order status from {original.get_status_display()} to "
                                  f"{self.get_status_display()}. "
                                  f"Allowed: {', '.join(allowed) or 'none (terminal state)'}."
                    })

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

# NOTE: StatusTransitionLog model REMOVED (Feb 2026) — never written to in production.
# Utility functions log_status_transition() and get_status_history() also removed from utils.py.

# NOTE: BitRepairHistory model REMOVED (Feb 2026) — never written to in production.
# DrillBit.repair_count tracks repairs; CutterEvaluationMatrix tracks evaluations.


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
    workflow_type = models.CharField(
        max_length=20, blank=True, default='REPAIR',
        help_text='REPAIR or MANUFACTURE — determines which route template to use'
    )
    accounts = models.ManyToManyField(
        'sales.Account', blank=True, related_name='process_routes',
        help_text='Accounts this route applies to (empty = all accounts)'
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

    # Conditional step
    is_conditional = models.BooleanField(
        default=False,
        help_text='Step marked "If Applicable" — may be skipped'
    )
    has_yes_no = models.BooleanField(
        default=False,
        help_text='Step requires Yes/No answer (e.g., Cerebro Removal: Yes/No)'
    )

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


# NOTE: OperationExecution model REMOVED (Feb 2026) — never written to in production.
# RouterSheetEntry is the active step-tracking system for work orders.


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
        from django.db.models import Sum
        # NOTE: OperationExecution-based labor calculation removed (Feb 2026)
        # Labor hours/cost should be tracked via WorkOrderTimeLog instead
        labor_agg = self.work_order.time_logs.aggregate(
            minutes=Sum("duration_minutes")
        )
        total_minutes = labor_agg["minutes"] or 0
        self.actual_labor_hours = Decimal(str(total_minutes)) / Decimal("60")

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


# =============================================================================
# JOB CARD ENHANCEMENTS - Cutter Evaluation & QC Forms
# =============================================================================

class CutterEvaluationMatrix(models.Model):
    """
    Cutter evaluation matrix for a work order.
    Links to the design's pocket layout and tracks evaluations
    for each cutter position (blade × cutter position from ID to Gauge).
    Tracks decision outcome and cutter state across multiple evaluation stages.
    """
    class EvaluationType(models.TextChoices):
        # Component receiving (separate from WO flow - updates drill bit inventory)
        RECEIVING = "RECEIVING", "Receiving Evaluation"
        # Main WO flow - PDC Evaluation is the starting point (includes Die Check + E-Checklist)
        PDC_EVAL = "PDC_EVAL", "PDC Evaluation"       # Renamed from ARDT - starting point for production WO
        QC = "QC", "QC Evaluation"                     # N/A for new bits, required for repair
        ENGINEER = "ENGINEER", "Technical Rep. Evaluation"  # N/A for new/UR, optional for Aramco
        ARAMCO_REP = "ARAMCO_REP", "Aramco Rep. Evaluation"  # Aramco inspector evaluation
        DIE_CHECK = "DIE_CHECK", "Die Check"
        FINAL_DIE_CHECK = "FINAL_DIE_CHECK", "Final Die Check"
        FINAL_QC = "FINAL_QC", "Final QC Evaluation"
        FINAL_INSPECTION = "FINAL_INSPECTION", "Final Inspection"
        REWORK = "REWORK", "Rework Evaluation"
        # Legacy support
        ARDT = "ARDT", "ARDT Evaluation (Legacy)"

    # Checklist items per evaluation type
    # Key: evaluation_type value, Value: list of checklist item labels
    CHECKLIST_ITEMS = {
        # Pre-repair evaluation checklist (QAS/1002)
        'PDC_EVAL': [
            'Bit Cleanliness (Washing & Sand Blasting)',
            'Paperwork',
            'Bit Stamping',
            'Die Check',
            'Ring Gauge (Go Gauge)',
            'Ring Gauge (No Go Gauge)',
            'Nozzle BoreLiner (Where Applicable)',
            'Nozzle Threads',
            'Apex',
            'Junk Slot',
            'Breaker Slot',
            'Body Condition',
            'Mud Seal Surface',
            'API Pin',
            'Inner Diameter',
            'Pressure Test (Where Applicable)',
            'Photos Update To The Server',
            'Other Comments (If Any)',
        ],
        # Receiving inspection checklist (QAS/005-1)
        'RECEIVING': [
            'Bit Cleanliness',
            'Ring Gage GO',
            'Ring Gage NO GO',
            'Nozzle Threads',
            'Breaker Slot',
            'Junk Slot',
            'API Pin',
            'Cutters',
            'No Body Damage',
            'Nozzle Liner Fit',
            'Q-Note from Vendor',
        ],
        # QC evaluation
        'QC': [
            'Bit Cleanliness',
            'Ring Gauge (Go Gauge)',
            'Ring Gauge (No Go Gauge)',
            'Nozzle Threads',
            'Nozzle BoreLiner',
            'Breaker Slot',
            'Junk Slot',
            'Body Condition',
            'API Pin',
            'Cutters Condition',
            'Gauge Pads',
            'Bit Face',
            'Pressure Test (Where Applicable)',
        ],
        # Final Inspection
        'FINAL_INSPECTION': [
            'Bit Cleanliness',
            'Ring Gauge (Go Gauge)',
            'Ring Gauge (No Go Gauge)',
            'Nozzle Threads',
            'Nozzle BoreLiner',
            'Breaker Slot',
            'Junk Slot',
            'Body Condition',
            'API Pin',
            'Cutters Condition',
            'Gauge Pads',
            'Bit Face',
            'Mud Seal Surface',
            'Bit Stamping',
            'Pressure Test (Where Applicable)',
            'Photos Update To The Server',
        ],
        # Final QC
        'FINAL_QC': [
            'Bit Cleanliness',
            'Ring Gauge (Go Gauge)',
            'Ring Gauge (No Go Gauge)',
            'Nozzle Threads',
            'Nozzle BoreLiner',
            'Breaker Slot',
            'Junk Slot',
            'Body Condition',
            'API Pin',
            'Cutters Condition',
            'Gauge Pads',
            'Bit Face',
            'Pressure Test (Where Applicable)',
        ],
    }

    class Decision(models.TextChoices):
        REPAIR = "REPAIR", "For Repair"
        RERUN = "RERUN", "For Rerun"
        SCRAP = "SCRAP", "For Scrap"
        DEBRAZE = "DEBRAZE", "De-braze"
        CUTTER_RETROFIT = "CUTTER_RETROFIT", "Cutter Retrofit"
        NEW_BUILD = "NEW_BUILD", "New Build"
        BODY_RETROFIT = "BODY_RETROFIT", "Body Retrofit"

    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name="cutter_evaluations"
    )
    evaluation_type = models.CharField(max_length=20, choices=EvaluationType.choices)
    evaluation_number = models.IntegerField(default=1, help_text="Evaluation sequence (for multiple evaluations)")

    # Decision outcome
    decision = models.CharField(
        max_length=20, choices=Decision.choices,
        blank=True, help_text="Evaluation outcome decision"
    )

    # Evaluator info
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="cutter_evaluations_performed"
    )
    evaluated_at = models.DateTimeField(null=True, blank=True)
    qc_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="cutter_evaluations_qc"
    )
    qc_at = models.DateTimeField(null=True, blank=True)

    # Remarks
    ardt_remark = models.TextField(blank=True, help_text="ARDT evaluation remarks")
    eng_remark = models.TextField(blank=True, help_text="Engineer evaluation remarks")
    general_remark = models.TextField(blank=True)

    # Hardfacing/Build-up decisions
    ardt_matrix_buildup = models.BooleanField(default=False, help_text="ARDT Matrix Build up required")
    eng_matrix_buildup = models.BooleanField(default=False, help_text="Engineer Matrix Build up required")

    # NCR reference for rework
    ncr_ref_no = models.CharField(max_length=50, blank=True, help_text="NCR Reference Number for rework")

    # Cutters details JSON (plant use table)
    cutters_details = models.JSONField(
        null=True, blank=True,
        help_text="Cutters details for plant use: [{qty, size_mm, part_no, description, remarks}]"
    )

    # Checklist data: [{item: str, status: 'OK'|'NOT_OK'|'NA'|'', remarks: str}]
    checklist_data = models.JSONField(
        null=True, blank=True,
        help_text="Evaluation checklist items with OK/Not OK/NA status and remarks"
    )

    # Pocket evaluation data (same format as ReceivingInspection.pocket_evaluation_data)
    pocket_evaluation_data = models.JSONField(
        null=True, blank=True,
        help_text="Pocket evaluation grid: {blade: {row: {pos: {shape: str, length: str}}}}"
    )

    # Die check grids: {die_check_1: {blade: {pos: value}}, die_check_2: {...}, remarks_1: str, remarks_2: str}
    die_check_data = models.JSONField(
        null=True, blank=True,
        help_text="Die check evaluation grids (two rounds) with remarks"
    )

    # Pressure test (LPT) data — QAS/1004-1
    # {before: {timing, materials: [{type, product, batch, expiry}], surface_temp, light_intensity,
    #           penetrant_dwell, developer_dwell, operator, result, remarks},
    #  after: {same structure}}
    pressure_test_data = models.JSONField(
        null=True, blank=True,
        help_text="Liquid Penetrant Testing data (QAS/1004-1) — before/after rounds"
    )

    # API Thread Inspection data
    # {evaluation: {checkpoints: [{item, ok, remarks}], pin_height, repair_required, repair_ops: [],
    #               inspector, remarks},
    #  after_repair: {same structure}}
    thread_inspection_data = models.JSONField(
        null=True, blank=True,
        help_text="API Thread Inspection data — evaluation and after-repair rounds"
    )

    # Section visibility flags — defaults computed from evaluation_type at creation
    include_checklist = models.BooleanField(default=True)
    include_cutter_grid = models.BooleanField(default=True)
    include_pocket_eval = models.BooleanField(default=True)
    include_die_check = models.BooleanField(default=False)
    include_pressure_test = models.BooleanField(default=False)
    include_thread_inspection = models.BooleanField(default=False)

    # FI Report Number — auto-assigned when Final Inspection is approved
    fi_report_number = models.CharField(
        max_length=30, blank=True,
        help_text="Final Inspection Report number, auto-assigned on FI approval"
    )

    # Auto-generated evaluation number (e.g., EV-2026-0001)
    inspection_number = models.CharField(
        max_length=30, blank=True,
        help_text="Auto-generated evaluation reference number"
    )

    # Schedule
    scheduled_date = models.DateField(
        null=True, blank=True,
        help_text="Scheduled date for this evaluation"
    )

    # Status flow: DRAFT → IN_PROGRESS → COMPLETED → APPROVED
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    # Keep is_complete for backward compatibility (derived from status)
    is_complete = models.BooleanField(default=False)

    # Approval (separate from QC sign-off)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_cutter_evaluations"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Remark annotations (user clarifications on auto-generated remarks) ──
    pocket_remark_annotations = models.JSONField(
        default=dict, blank=True,
        help_text="User annotations per pocket remark segment: {segKey: {text, before, after}}"
    )
    cutter_remark_annotations = models.JSONField(
        default=dict, blank=True,
        help_text="User annotations per cutter remark segment: {segKey: {text, before, after}}"
    )
    pocket_auto_remarks = models.TextField(
        blank=True, help_text="Auto-generated pocket remarks text"
    )
    cutter_auto_remarks = models.TextField(
        blank=True, help_text="Auto-generated cutter remarks text"
    )

    # Default section visibility per evaluation type
    SECTION_DEFAULTS = {
        'RECEIVING': {
            'include_checklist': True, 'include_cutter_grid': True,
            'include_pocket_eval': True, 'include_die_check': False,
            'include_pressure_test': False, 'include_thread_inspection': False,
        },
        'PDC_EVAL': {
            'include_checklist': True, 'include_cutter_grid': True,
            'include_pocket_eval': True, 'include_die_check': True,
            'include_pressure_test': False, 'include_thread_inspection': False,
        },
        'QC': {
            'include_checklist': True, 'include_cutter_grid': True,
            'include_pocket_eval': True, 'include_die_check': False,
            'include_pressure_test': False, 'include_thread_inspection': False,
        },
        'ENGINEER': {
            'include_checklist': False, 'include_cutter_grid': True,
            'include_pocket_eval': False, 'include_die_check': False,
            'include_pressure_test': False, 'include_thread_inspection': False,
        },
        'ARAMCO_REP': {
            'include_checklist': False, 'include_cutter_grid': True,
            'include_pocket_eval': False, 'include_die_check': False,
            'include_pressure_test': False, 'include_thread_inspection': False,
        },
        'DIE_CHECK': {
            'include_checklist': False, 'include_cutter_grid': False,
            'include_pocket_eval': False, 'include_die_check': True,
            'include_pressure_test': False, 'include_thread_inspection': False,
        },
        'FINAL_DIE_CHECK': {
            'include_checklist': False, 'include_cutter_grid': False,
            'include_pocket_eval': False, 'include_die_check': True,
            'include_pressure_test': False, 'include_thread_inspection': False,
        },
        'FINAL_QC': {
            'include_checklist': True, 'include_cutter_grid': True,
            'include_pocket_eval': True, 'include_die_check': False,
            'include_pressure_test': False, 'include_thread_inspection': False,
        },
        'FINAL_INSPECTION': {
            'include_checklist': True, 'include_cutter_grid': True,
            'include_pocket_eval': True, 'include_die_check': False,
            'include_pressure_test': False, 'include_thread_inspection': True,
        },
        'REWORK': {
            'include_checklist': True, 'include_cutter_grid': True,
            'include_pocket_eval': False, 'include_die_check': False,
            'include_pressure_test': False, 'include_thread_inspection': False,
        },
    }

    # Manufacture override: PDC_EVAL without die check by default
    MANUFACTURE_OVERRIDES = {
        'PDC_EVAL': {'include_die_check': False},
    }

    def apply_section_defaults(self, workflow_type=None):
        """Set include_* flags from evaluation type defaults + workflow overrides."""
        defaults = self.SECTION_DEFAULTS.get(self.evaluation_type, {})
        for field, value in defaults.items():
            setattr(self, field, value)
        # Apply manufacture overrides
        if workflow_type == 'MANUFACTURE':
            overrides = self.MANUFACTURE_OVERRIDES.get(self.evaluation_type, {})
            for field, value in overrides.items():
                setattr(self, field, value)

    class Meta:
        db_table = "cutter_evaluation_matrices"
        ordering = ["work_order", "evaluation_type", "evaluation_number"]
        unique_together = ["work_order", "evaluation_type", "evaluation_number"]
        verbose_name = "Cutter Evaluation Matrix"
        verbose_name_plural = "Cutter Evaluation Matrices"

    def __str__(self):
        return f"{self.work_order.wo_number} - {self.get_evaluation_type_display()} #{self.evaluation_number}"


class CutterEvaluationEntry(models.Model):
    """
    Individual cutter evaluation entry within a matrix.
    Each entry represents one cutter position on one blade.
    """
    class Action(models.TextChoices):
        OK = "O", "OK - No action needed"
        REPLACE = "X", "Replace"
        ROTATE = "R", "Rotate"
        SPIN = "S", "Spin"
        FILL = "F", "Fill"
        LOST = "L", "Lost"
        POCKET_BUILDUP = "P", "Pocket Build Up"
        IMPACT_ARRESTOR = "I", "Impact Arrestor Build Up"
        FIN_BUILDUP = "V", "Fin Build Up"
        BLANK = "", "Not evaluated"

    class CutterSource(models.TextChoices):
        NEW = "NEW", "New Cutter"
        RECLAIM = "RECLAIM", "Reclaim Cutter"
        EXISTING = "EXISTING", "Existing (no change)"

    matrix = models.ForeignKey(
        CutterEvaluationMatrix, on_delete=models.CASCADE, related_name="entries"
    )

    # Position on the bit
    blade_number = models.IntegerField(help_text="Blade number (1-12)")
    cutter_position = models.IntegerField(help_text="Cutter position from ID to Gauge (1-15+)")

    # Evaluation action
    action = models.CharField(max_length=1, choices=Action.choices, default=Action.BLANK)

    # Cutter details (if replacing)
    cutter_source = models.CharField(
        max_length=10, choices=CutterSource.choices,
        blank=True, help_text="Source of replacement cutter"
    )
    cutter_item = models.ForeignKey(
        "inventory.InventoryItem", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="evaluation_entries", help_text="Replacement cutter from inventory"
    )
    cutter_size = models.CharField(max_length=10, blank=True, help_text="Cutter size code (e.g., 1313, 1608)")
    cutter_type = models.CharField(max_length=20, blank=True, help_text="Cutter type/HDBS code")
    cutter_chamfer = models.CharField(max_length=10, blank=True)

    # Notes
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "cutter_evaluation_entries"
        ordering = ["matrix", "blade_number", "cutter_position"]
        unique_together = ["matrix", "blade_number", "cutter_position"]
        verbose_name = "Cutter Evaluation Entry"
        verbose_name_plural = "Cutter Evaluation Entries"

    def __str__(self):
        return f"Blade {self.blade_number}, Pos {self.cutter_position}: {self.get_action_display()}"


class ReceivingInspection(models.Model):
    """
    FC Bit Receiving Inspection per QAS/005-1.
    Linked to DrillBit (happens before WO exists).
    Optional WO FK set when WO is created later.
    """
    class InspectionResult(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        CONDITIONAL = "CONDITIONAL", "Conditional Accept"

    # Core links
    drill_bit = models.ForeignKey(
        DrillBit, on_delete=models.CASCADE, related_name="receiving_inspections"
    )
    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="receiving_inspections"
    )

    # Header
    inspection_date = models.DateField(null=True, blank=True)
    po_number = models.CharField(max_length=50, blank=True)
    client_name = models.CharField(max_length=100, blank=True)
    date_of_receipt = models.DateField(null=True, blank=True, verbose_name="Date of Receipt")

    # ── Visual Inspection Checklist per QAS/005-1 (11 items, each OK/NOT_OK/NA) ──
    CHECKLIST_CHOICES = [("OK", "OK"), ("NOT_OK", "Not OK"), ("NA", "N/A")]
    vi_pin_connection = models.CharField(
        max_length=6, choices=CHECKLIST_CHOICES, default="NA",
        verbose_name="API Pin Connection"
    )
    vi_bit_body = models.CharField(
        max_length=6, choices=CHECKLIST_CHOICES, default="NA",
        verbose_name="No Body Damage"
    )
    vi_bit_breaker = models.CharField(
        max_length=6, choices=CHECKLIST_CHOICES, default="NA",
        verbose_name="Breaker Slot"
    )
    vi_blades = models.CharField(
        max_length=6, choices=CHECKLIST_CHOICES, default="NA",
        verbose_name="Cutters"
    )
    vi_nozzles = models.CharField(
        max_length=6, choices=CHECKLIST_CHOICES, default="NA",
        verbose_name="Nozzle Threads"
    )
    vi_junk_slot = models.CharField(
        max_length=6, choices=CHECKLIST_CHOICES, default="NA",
        verbose_name="Junk Slot"
    )
    vi_gauge_pads = models.CharField(
        max_length=6, choices=CHECKLIST_CHOICES, default="NA",
        verbose_name="Bit Cleanliness"
    )
    vi_bit_face = models.CharField(
        max_length=6, choices=CHECKLIST_CHOICES, default="NA",
        verbose_name="Ring Gage GO"
    )
    vi_general = models.CharField(
        max_length=6, choices=CHECKLIST_CHOICES, default="NA",
        verbose_name="Ring Gage NO GO"
    )
    vi_nozzle_liner = models.CharField(
        max_length=6, choices=CHECKLIST_CHOICES, default="NA",
        verbose_name="Nozzle Liner Fit"
    )
    vi_vendor_note = models.CharField(
        max_length=6, choices=CHECKLIST_CHOICES, default="NA",
        verbose_name="Q-Note from Vendor"
    )
    # ── Per-item remarks for checklist ──
    checklist_remarks = models.JSONField(
        default=dict, blank=True,
        help_text="Per-item remarks and reason: {field_name: {reason: '', remarks: ''}}"
    )

    # ── Cutter Condition Counts ──
    cutters_total = models.IntegerField(default=0, verbose_name="Total Cutters")
    cutters_chipped = models.IntegerField(default=0, verbose_name="Chipped")
    cutters_broken = models.IntegerField(default=0, verbose_name="Broken")
    cutters_worn = models.IntegerField(default=0, verbose_name="Worn")
    cutters_missing = models.IntegerField(default=0, verbose_name="Missing")

    # ── Measurements ──
    tfa = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True,
        verbose_name="TFA", help_text="Total Flow Area"
    )
    gauge_reading_1 = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True,
        verbose_name="Gauge Reading 1"
    )
    gauge_reading_2 = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True,
        verbose_name="Gauge Reading 2"
    )
    gauge_reading_3 = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True,
        verbose_name="Gauge Reading 3"
    )

    # ── Per-Pocket Cutter Evaluation (from BOM blade data) ──
    cutter_evaluation_data = models.JSONField(
        default=dict, blank=True,
        help_text="Per-pocket cutter evaluation: {blade: {row: {position: {idx: {action, remarks}}}}}"
    )
    # ── Per-Pocket Condition Evaluation (from design pockets) ──
    pocket_evaluation_data = models.JSONField(
        default=dict, blank=True,
        help_text="Per-pocket condition: {blade_pos: symbols_string} e.g. {'1_3': 'IPV', '2_5': 'TD'}"
    )
    # ── Remark annotations (user clarifications on auto-generated remarks) ──
    pocket_remark_annotations = models.JSONField(
        default=dict, blank=True,
        help_text="User annotations per pocket remark segment: {segKey: text}"
    )
    cutter_remark_annotations = models.JSONField(
        default=dict, blank=True,
        help_text="User annotations per cutter remark segment: {segKey: text}"
    )
    pocket_auto_remarks = models.TextField(
        blank=True, help_text="Auto-generated pocket remarks text"
    )
    cutter_auto_remarks = models.TextField(
        blank=True, help_text="Auto-generated cutter remarks text"
    )

    # ── Decision ──
    result = models.CharField(
        max_length=12, choices=InspectionResult.choices,
        default=InspectionResult.PENDING, verbose_name="Inspection Result"
    )
    remarks = models.TextField(blank=True)

    # ── Signatures ──
    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="receiving_inspections_performed"
    )
    qc_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="receiving_inspections_approved"
    )
    qc_approved_at = models.DateTimeField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "receiving_inspections"
        ordering = ["-inspection_date", "-created_at"]
        verbose_name = "Receiving Inspection"
        verbose_name_plural = "Receiving Inspections"

    def __str__(self):
        return f"RI-{self.drill_bit.serial_number} ({self.get_result_display()})"

    @property
    def cutters_good(self):
        """Cutters in good condition = total - (chipped + broken + worn + missing)."""
        return max(0, self.cutters_total - self.cutters_chipped - self.cutters_broken - self.cutters_worn - self.cutters_missing)

    @property
    def checklist_items(self):
        """Return list of (num, label, field_name, value) tuples per QAS/005-1."""
        return [
            (1, "Bit Cleanliness", "vi_gauge_pads", self.vi_gauge_pads),
            (2, "Ring Gage GO", "vi_bit_face", self.vi_bit_face),
            (3, "Ring Gage NO GO", "vi_general", self.vi_general),
            (4, "Nozzle Threads", "vi_nozzles", self.vi_nozzles),
            (5, "Breaker Slot", "vi_bit_breaker", self.vi_bit_breaker),
            (6, "Junk Slot", "vi_junk_slot", self.vi_junk_slot),
            (7, "API Pin Connection", "vi_pin_connection", self.vi_pin_connection),
            (8, "Cutters", "vi_blades", self.vi_blades),
            (9, "No Body Damage", "vi_bit_body", self.vi_bit_body),
            (10, "Nozzle Liner Fit", "vi_nozzle_liner", self.vi_nozzle_liner),
            (11, "Q-Note from Vendor", "vi_vendor_note", self.vi_vendor_note),
        ]

    @property
    def report_number(self):
        """Auto-generated report number from PK."""
        if self.pk:
            return f"RI-{self.pk:04d}"
        return "RI-NEW"


class ReceivingInspectionAttachment(models.Model):
    """File attachments for receiving inspections (Q-Note, photos, etc.)."""
    inspection = models.ForeignKey(
        ReceivingInspection, on_delete=models.CASCADE, related_name='attachments'
    )
    file = models.FileField(upload_to='receiving_inspections/%Y/%m/')
    name = models.CharField(max_length=100, default='Q-Note',
                           help_text="Document name (e.g., Q-Note, Photo, Additional)")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "receiving_inspection_attachments"
        ordering = ['uploaded_at']

    def __str__(self):
        return f"{self.name} — {self.inspection}"

    @property
    def file_extension(self):
        import os
        return os.path.splitext(self.file.name)[1].lower() if self.file else ''

    @property
    def is_image(self):
        return self.file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']


def build_adg_sequence(blade_count: int, serial_number: str = '',
                       set_name: str = '') -> list:
    """
    Generate the full photo sequence for a given blade count and set name.
    Fixed 3 photos per blade, then Top, Side, then Extra slots.
    Format: {serial}_{set}_B1_P1 (e.g. 14414030R2_Before_B1_P1)
    Returns: [{'display_name': '14414030R2_Before_B1_P1', 'short_label': 'B1-P1',
               'category': 'BLADE', 'blade_number': 1, 'photo_number': 1}, ...]
    """
    parts = [p for p in [serial_number, set_name] if p]
    prefix = '_'.join(parts) + '_' if parts else ''
    sequence = []
    for b in range(1, blade_count + 1):
        for ph in range(1, 4):
            sequence.append({
                'display_name': f'{prefix}B{b}_P{ph}',
                'short_label': f'B{b}-P{ph}',
                'category': 'BLADE',
                'blade_number': b,
                'photo_number': ph,
            })
    sequence.append({'display_name': f'{prefix}Top', 'short_label': 'Top',
                     'category': 'TOP', 'blade_number': None, 'photo_number': 1})
    sequence.append({'display_name': f'{prefix}Side', 'short_label': 'Side',
                     'category': 'SIDE', 'blade_number': None, 'photo_number': 1})
    for i in range(1, 10):
        sequence.append({'display_name': f'{prefix}Extra_{i}', 'short_label': f'Extra-{i}',
                         'category': 'EXTRA', 'blade_number': None, 'photo_number': i})
    return sequence


# Default photo sets — each gets its own slot grid
PHOTO_SETS = ['Before', 'After', 'ADG']


class DrillBitPhoto(models.Model):
    """
    Photo of a drill bit, taken at any stage (receiving, evaluation, WO, etc.)
    Always linked to the physical DrillBit. Optional context records which
    document/evaluation the photo was captured during.
    """

    class Category(models.TextChoices):
        BLADE  = "BLADE", "Blade"
        TOP    = "TOP", "Top View"
        SIDE   = "SIDE", "Side View"
        DETAIL = "DETAIL", "Detail / Close-up"
        EXTRA  = "EXTRA", "Extra"

    class ContextType(models.TextChoices):
        RECEIVING_INSPECTION = "RECEIVING", "Receiving Inspection"
        CUTTER_EVALUATION    = "EVALUATION", "Cutter Evaluation"
        WORK_ORDER           = "WO", "Work Order"
        GENERAL              = "GENERAL", "General"

    # Core links
    drill_bit = models.ForeignKey(
        DrillBit, on_delete=models.CASCADE, related_name="bit_photos"
    )
    context_type = models.CharField(
        max_length=20, choices=ContextType.choices,
        default=ContextType.GENERAL, blank=True
    )
    context_id = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="PK of the related document (ReceivingInspection, etc.)"
    )

    # Photo naming / sequencing
    category = models.CharField(
        max_length=10, choices=Category.choices, default=Category.BLADE
    )
    blade_number = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Blade number (1-based) for BLADE category photos"
    )
    photo_number = models.PositiveSmallIntegerField(
        default=1, help_text="Sequence within the blade/category"
    )
    display_name = models.CharField(
        max_length=50, blank=True,
        help_text="Human label: B1-Ph1, Top, Side, Extra-1, etc."
    )

    # Files
    original_filename = models.CharField(max_length=255, blank=True)
    file = models.ImageField(upload_to="drill_bit_photos/%Y/%m/")
    edited_file = models.ImageField(
        upload_to="drill_bit_photos/edited/%Y/%m/",
        null=True, blank=True
    )

    # Capture metadata
    capture_mode = models.CharField(
        max_length=10,
        choices=[("ADG", "ADG Guided"), ("CAMERA", "Camera"), ("FREE", "Free Upload")],
        default="FREE"
    )
    sort_order = models.PositiveIntegerField(default=0, db_index=True)

    # Audit
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="uploaded_bit_photos"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drill_bit_photos"
        ordering = ["drill_bit", "sort_order", "uploaded_at"]
        verbose_name = "Drill Bit Photo"
        verbose_name_plural = "Drill Bit Photos"

    def __str__(self):
        name = self.display_name or f"Photo {self.pk}"
        return f"{self.drill_bit.serial_number} — {name}"

    @property
    def active_file(self):
        """Return edited_file if it exists, else original file."""
        return self.edited_file if self.edited_file else self.file

    @property
    def file_url(self):
        return self.active_file.url if self.active_file else ""

    @property
    def original_url(self):
        return self.file.url if self.file else ""

    @property
    def has_edits(self):
        return bool(self.edited_file)


class InstructionRule(models.Model):
    """
    Rule-based instruction system.
    Allows users to define conditions that trigger specific instructions
    for work orders based on design, MAT number, customer, etc.
    """
    class Priority(models.IntegerChoices):
        LOW = 1, "Low"
        NORMAL = 5, "Normal"
        HIGH = 8, "High"
        CRITICAL = 10, "Critical"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instruction_text = models.TextField(help_text="The instruction to display when conditions match")

    # Priority determines display order
    priority = models.IntegerField(choices=Priority.choices, default=Priority.NORMAL)

    # Applicability filters (simple field-based matching)
    # These are OR conditions within the same rule
    applies_to_wo_types = models.JSONField(
        null=True, blank=True,
        help_text="List of WO types this applies to, e.g., ['FC_REPAIR', 'FC_REWORK']"
    )
    applies_to_bit_types = models.JSONField(
        null=True, blank=True,
        help_text="List of bit types, e.g., ['FC', 'RC']"
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="created_instruction_rules"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_instruction_rules"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "instruction_rules"
        ordering = ["-priority", "name"]
        verbose_name = "Instruction Rule"
        verbose_name_plural = "Instruction Rules"

    def __str__(self):
        return f"{self.name} (Priority: {self.priority})"


class InstructionRuleCondition(models.Model):
    """
    Individual conditions within an instruction rule.
    All conditions within a rule are evaluated with AND logic.
    """
    class Operator(models.TextChoices):
        EQUALS = "eq", "Equals"
        NOT_EQUALS = "ne", "Not Equals"
        CONTAINS = "contains", "Contains"
        STARTS_WITH = "starts", "Starts With"
        ENDS_WITH = "ends", "Ends With"
        GREATER_THAN = "gt", "Greater Than"
        LESS_THAN = "lt", "Less Than"
        IN_LIST = "in", "In List"
        NOT_IN_LIST = "not_in", "Not In List"
        IS_NULL = "null", "Is Null"
        IS_NOT_NULL = "not_null", "Is Not Null"

    class FieldSource(models.TextChoices):
        WORK_ORDER = "wo", "Work Order"
        DRILL_BIT = "bit", "Drill Bit"
        DESIGN = "design", "Design"
        CUSTOMER = "customer", "Customer"
        BOM = "bom", "BOM"

    rule = models.ForeignKey(
        InstructionRule, on_delete=models.CASCADE, related_name="conditions"
    )

    # What to check
    field_source = models.CharField(max_length=20, choices=FieldSource.choices)
    field_name = models.CharField(max_length=100, help_text="Field name to check (e.g., 'mat_number', 'size')")
    operator = models.CharField(max_length=20, choices=Operator.choices)
    value = models.CharField(max_length=500, help_text="Value to compare against (comma-separated for IN/NOT_IN)")

    class Meta:
        db_table = "instruction_rule_conditions"
        ordering = ["rule", "id"]
        verbose_name = "Instruction Rule Condition"
        verbose_name_plural = "Instruction Rule Conditions"

    def __str__(self):
        return f"{self.field_source}.{self.field_name} {self.operator} {self.value}"

    def evaluate(self, work_order):
        """Evaluate this condition against a work order."""
        # Get the source object
        if self.field_source == self.FieldSource.WORK_ORDER:
            obj = work_order
        elif self.field_source == self.FieldSource.DRILL_BIT:
            obj = work_order.drill_bit
        elif self.field_source == self.FieldSource.DESIGN:
            obj = work_order.design
        elif self.field_source == self.FieldSource.CUSTOMER:
            obj = work_order.customer
        elif self.field_source == self.FieldSource.BOM:
            obj = work_order.bom
        else:
            return False

        if obj is None:
            return self.operator in [self.Operator.IS_NULL]

        # Get field value
        try:
            field_value = getattr(obj, self.field_name, None)
            if callable(field_value):
                field_value = field_value()
        except AttributeError:
            return False

        # Convert to string for comparison
        field_str = str(field_value) if field_value is not None else ""
        compare_value = self.value

        # Evaluate based on operator
        if self.operator == self.Operator.EQUALS:
            return field_str.lower() == compare_value.lower()
        elif self.operator == self.Operator.NOT_EQUALS:
            return field_str.lower() != compare_value.lower()
        elif self.operator == self.Operator.CONTAINS:
            return compare_value.lower() in field_str.lower()
        elif self.operator == self.Operator.STARTS_WITH:
            return field_str.lower().startswith(compare_value.lower())
        elif self.operator == self.Operator.ENDS_WITH:
            return field_str.lower().endswith(compare_value.lower())
        elif self.operator == self.Operator.IN_LIST:
            values = [v.strip().lower() for v in compare_value.split(",")]
            return field_str.lower() in values
        elif self.operator == self.Operator.NOT_IN_LIST:
            values = [v.strip().lower() for v in compare_value.split(",")]
            return field_str.lower() not in values
        elif self.operator == self.Operator.IS_NULL:
            return field_value is None or field_str == ""
        elif self.operator == self.Operator.IS_NOT_NULL:
            return field_value is not None and field_str != ""
        elif self.operator in [self.Operator.GREATER_THAN, self.Operator.LESS_THAN]:
            try:
                field_num = float(field_str)
                compare_num = float(compare_value)
                if self.operator == self.Operator.GREATER_THAN:
                    return field_num > compare_num
                else:
                    return field_num < compare_num
            except (ValueError, TypeError):
                return False

        return False


class LPTReport(models.Model):
    """
    Liquid Penetrant Testing Report for quality control.
    Can be for new cutters, reclaimed cutters, or full bit inspection.
    """
    class TestType(models.TextChoices):
        NEW_CUTTER = "NEW_CUTTER", "New Cutters"
        RECLAIM_CUTTER = "RECLAIM_CUTTER", "Reclaimed Cutters"
        NEW_BIT = "NEW_BIT", "New Bit"
        REPAIR_BEFORE = "REPAIR_BEFORE", "Before Repair"
        REPAIR_AFTER = "REPAIR_AFTER", "After Repair (Tip Grinding)"
        DEBRAZED = "DEBRAZED", "Debrazed Cutters"

    class Result(models.TextChoices):
        PASS = "PASS", "Pass"
        FAIL = "FAIL", "Fail"
        CONDITIONAL = "CONDITIONAL", "Conditional Pass"
        PENDING = "PENDING", "Pending Evaluation"

    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name="lpt_reports"
    )
    report_number = models.CharField(max_length=30, unique=True)
    test_type = models.CharField(max_length=20, choices=TestType.choices)

    # Technique info
    technique = models.CharField(
        max_length=100, default="Fluorescent - Washable Technique",
        help_text="Testing technique used"
    )
    procedure_ref = models.CharField(
        max_length=100, default="SA-PP-1013 Liquid Penetrant Testing",
        help_text="Procedure reference"
    )

    # Materials used
    cleaner_product = models.CharField(max_length=100, default="Water")
    cleaner_batch = models.CharField(max_length=50, blank=True)
    cleaner_expiry = models.DateField(null=True, blank=True)

    penetrant_product = models.CharField(max_length=100, blank=True)
    penetrant_batch = models.CharField(max_length=50, blank=True)
    penetrant_expiry = models.DateField(null=True, blank=True)

    developer_product = models.CharField(max_length=100, blank=True)
    developer_batch = models.CharField(max_length=50, blank=True)
    developer_expiry = models.DateField(null=True, blank=True)

    # Test parameters
    surface_temperature = models.CharField(max_length=50, blank=True)
    penetrant_dwell_time = models.CharField(max_length=50, blank=True)
    light_intensity = models.CharField(max_length=50, blank=True)
    developer_dwell_time = models.CharField(max_length=50, blank=True)

    # Operator info
    lpt_operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="lpt_reports_operated"
    )
    operator_date = models.DateField(null=True, blank=True)

    # Evaluator info
    lpt_evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lpt_reports_evaluated"
    )
    evaluator_date = models.DateField(null=True, blank=True)

    # Result
    result = models.CharField(max_length=20, choices=Result.choices, default=Result.PENDING)
    disposition = models.TextField(blank=True, help_text="Disposition/Remarks")

    # For cutter-specific LPT
    cutter_details = models.JSONField(
        null=True, blank=True,
        help_text="Array of cutter details: [{size, type, sap_no, qty, category, remark}]"
    )

    # Photos
    photo_before = models.ImageField(upload_to="lpt_photos/", null=True, blank=True)
    photo_after = models.ImageField(upload_to="lpt_photos/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lpt_reports"
        ordering = ["-created_at"]
        verbose_name = "LPT Report"
        verbose_name_plural = "LPT Reports"

    def __str__(self):
        return f"{self.report_number} - {self.get_test_type_display()}"


class APIThreadInspection(models.Model):
    """
    API Thread Inspection form for pin/thread quality checks.
    """
    class RepairRequired(models.TextChoices):
        YES = "YES", "Required"
        NO = "NO", "Not Required"

    class Result(models.TextChoices):
        PASS = "PASS", "Pass"
        FAIL = "FAIL", "Fail"
        CONDITIONAL = "CONDITIONAL", "Conditional"

    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name="api_thread_inspections"
    )
    inspection_number = models.CharField(max_length=30, unique=True)
    pin_size = models.CharField(max_length=50, blank=True)

    # Initial evaluation checkpoints
    pin_face_ok = models.BooleanField(null=True, blank=True)
    pin_face_remarks = models.CharField(max_length=200, blank=True)

    thread_ok = models.BooleanField(null=True, blank=True)
    thread_remarks = models.CharField(max_length=200, blank=True)

    pitch_gauge_ok = models.BooleanField(null=True, blank=True)
    pitch_gauge_remarks = models.CharField(max_length=200, blank=True)

    mud_seal_ok = models.BooleanField(null=True, blank=True)
    mud_seal_remarks = models.CharField(max_length=200, blank=True)

    other_observation = models.TextField(blank=True)
    pin_height = models.CharField(max_length=50, blank=True)

    # Repair decision
    thread_repair_required = models.CharField(
        max_length=10, choices=RepairRequired.choices, blank=True
    )
    repair_brush_selected = models.BooleanField(default=False)
    upper_section_replacement = models.BooleanField(default=False)

    # After repair checkpoints
    after_pin_face_ok = models.BooleanField(null=True, blank=True)
    after_pin_face_remarks = models.CharField(max_length=200, blank=True)

    after_thread_ok = models.BooleanField(null=True, blank=True)
    after_thread_remarks = models.CharField(max_length=200, blank=True)

    after_pitch_gauge_ok = models.BooleanField(null=True, blank=True)
    after_pitch_gauge_remarks = models.CharField(max_length=200, blank=True)

    after_mud_seal_ok = models.BooleanField(null=True, blank=True)
    after_mud_seal_remarks = models.CharField(max_length=200, blank=True)

    # Result
    initial_result = models.CharField(max_length=20, choices=Result.choices, blank=True)
    final_result = models.CharField(max_length=20, choices=Result.choices, blank=True)

    # Inspector info
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="api_inspections_performed"
    )
    inspection_date = models.DateField(null=True, blank=True)

    # QC sign-off
    qc_inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="api_inspections_qc"
    )
    qc_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "api_thread_inspections"
        ordering = ["-created_at"]
        verbose_name = "API Thread Inspection"
        verbose_name_plural = "API Thread Inspections"

    def __str__(self):
        return f"{self.inspection_number} - {self.work_order.wo_number}"


class RouterSheetEntry(models.Model):
    """
    Individual step entry in a router sheet with QR-based time tracking.
    """
    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name="router_entries"
    )
    # NOTE: operation_execution OneToOneField to OperationExecution REMOVED (Feb 2026)

    # Step info (can be standalone if no ProcessRoute assigned)
    step_number = models.IntegerField()
    step_description = models.CharField(max_length=200)

    # QR-based time tracking
    qr_scan_start = models.DateTimeField(null=True, blank=True, help_text="QR scan timestamp for start")
    qr_scan_end = models.DateTimeField(null=True, blank=True, help_text="QR scan timestamp for end")
    station_qr = models.CharField(max_length=100, blank=True, help_text="Station QR code scanned")

    # Manual time entry (fallback)
    manual_date = models.DateField(null=True, blank=True)
    manual_time_receipt = models.TimeField(null=True, blank=True)

    # Operator
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="router_entries_operated"
    )
    operator_signature = models.ImageField(upload_to="signatures/", null=True, blank=True)

    # Status
    is_complete = models.BooleanField(default=False)

    # Remarks
    remarks = models.TextField(blank=True)

    # Special fields for certain steps
    cerebro_removal = models.BooleanField(null=True, blank=True, help_text="Cerebro Removal: Yes/No/NA")
    oring_removal = models.BooleanField(null=True, blank=True, help_text="Cer. O-Ring Removal: Yes/No/NA")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "router_sheet_entries"
        ordering = ["work_order", "step_number"]
        unique_together = ["work_order", "step_number"]
        verbose_name = "Router Sheet Entry"
        verbose_name_plural = "Router Sheet Entries"

    def __str__(self):
        return f"{self.work_order.wo_number} Step {self.step_number}: {self.step_description}"

    @property
    def duration_minutes(self):
        """Calculate duration from QR scans or manual entry."""
        if self.qr_scan_start and self.qr_scan_end:
            delta = self.qr_scan_end - self.qr_scan_start
            return int(delta.total_seconds() / 60)
        return None


class EvaluationChecklist(models.Model):
    """
    FC BIT EVALUATION CHECKLIST - Standard QC checklist for bit evaluation.
    """
    class Result(models.TextChoices):
        OK = "OK", "OK"
        NOT_OK = "NOT_OK", "Not OK"
        NA = "NA", "N/A"

    work_order = models.OneToOneField(
        WorkOrder, on_delete=models.CASCADE, related_name="evaluation_checklist"
    )

    # Checklist items
    bit_cleanliness = models.CharField(max_length=10, choices=Result.choices, blank=True)
    bit_cleanliness_remarks = models.CharField(max_length=200, blank=True)

    paperwork = models.CharField(max_length=10, choices=Result.choices, blank=True)
    paperwork_remarks = models.CharField(max_length=200, blank=True)

    bit_stamping = models.CharField(max_length=10, choices=Result.choices, blank=True)
    bit_stamping_remarks = models.CharField(max_length=200, blank=True)

    die_check = models.CharField(max_length=10, choices=Result.choices, blank=True)
    die_check_remarks = models.CharField(max_length=200, blank=True)

    ring_gauge_go = models.CharField(max_length=10, choices=Result.choices, blank=True)
    ring_gauge_go_remarks = models.CharField(max_length=200, blank=True)

    ring_gauge_no_go = models.CharField(max_length=10, choices=Result.choices, blank=True)
    ring_gauge_no_go_remarks = models.CharField(max_length=200, blank=True)

    nozzle_bore_liner = models.CharField(max_length=10, choices=Result.choices, blank=True)
    nozzle_bore_liner_remarks = models.CharField(max_length=200, blank=True)

    nozzle_threads = models.CharField(max_length=10, choices=Result.choices, blank=True)
    nozzle_threads_remarks = models.CharField(max_length=200, blank=True)

    apex = models.CharField(max_length=10, choices=Result.choices, blank=True)
    apex_remarks = models.CharField(max_length=200, blank=True)

    junk_slot = models.CharField(max_length=10, choices=Result.choices, blank=True)
    junk_slot_remarks = models.CharField(max_length=200, blank=True)

    breaker_slot = models.CharField(max_length=10, choices=Result.choices, blank=True)
    breaker_slot_remarks = models.CharField(max_length=200, blank=True)

    body_condition = models.CharField(max_length=10, choices=Result.choices, blank=True)
    body_condition_remarks = models.CharField(max_length=200, blank=True)

    mud_seal_surface = models.CharField(max_length=10, choices=Result.choices, blank=True)
    mud_seal_surface_remarks = models.CharField(max_length=200, blank=True)

    api_pin = models.CharField(max_length=10, choices=Result.choices, blank=True)
    api_pin_remarks = models.CharField(max_length=200, blank=True)

    inner_diameter = models.CharField(max_length=10, choices=Result.choices, blank=True)
    inner_diameter_remarks = models.CharField(max_length=200, blank=True)

    # Overall result
    overall_pass = models.CharField(max_length=10, choices=Result.choices, blank=True, default='')
    general_remarks = models.TextField(blank=True)

    # Item timestamps for auditing (JSONField: {"bit_cleanliness": "2026-02-06T12:30:00Z", ...})
    item_timestamps = models.JSONField(default=dict, blank=True, help_text='Timestamps when each item was last updated')

    # Inspector info
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="evaluation_checklists_performed"
    )
    inspection_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evaluation_checklists"
        verbose_name = "Evaluation Checklist"
        verbose_name_plural = "Evaluation Checklists"

    def __str__(self):
        return f"E-Checklist for {self.work_order.wo_number}"

    @property
    def pass_count(self):
        """Count of OK items."""
        count = 0
        for field in self._meta.fields:
            if field.name.endswith('_remarks'):
                continue
            if field.choices and hasattr(self, field.name):
                val = getattr(self, field.name)
                if val == self.Result.OK:
                    count += 1
        return count

    @property
    def fail_count(self):
        """Count of NOT_OK items."""
        count = 0
        for field in self._meta.fields:
            if field.name.endswith('_remarks'):
                continue
            if field.choices and hasattr(self, field.name):
                val = getattr(self, field.name)
                if val == self.Result.NOT_OK:
                    count += 1
        return count


class ProductionPlanEntry(models.Model):
    """
    Production Plan Entry - a drill bit queued for work without creating a Work Order.
    Allows planning work before committing to WO creation.
    """

    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        PENDING_RELEASE = "PENDING_RELEASE", "Pending Release"
        RELEASED = "RELEASED", "Released"
        WO_CREATED = "WO_CREATED", "WO Created"
        REMOVED = "REMOVED", "Removed"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    drill_bit = models.ForeignKey(
        DrillBit, on_delete=models.PROTECT, related_name='plan_entries',
        help_text='Drill bit to be planned for production'
    )
    account = models.ForeignKey(
        'sales.Account', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='plan_entries',
        help_text='Account for this planned work'
    )
    work_order = models.OneToOneField(
        WorkOrder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='plan_entry',
        help_text='Work Order created from this plan entry'
    )

    # Planning fields
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    planned_date = models.DateField(null=True, blank=True, help_text='Target date for starting work')
    due_date = models.DateField(null=True, blank=True, help_text='Target date for completing work (auto-calculated: 6 days, 4 for UR)')
    sequence = models.IntegerField(default=0, help_text='Sequence order in the plan')

    # Intended work type
    intended_wo_type = models.CharField(
        max_length=20, choices=WorkOrder.WOType.choices, blank=True,
        help_text='Intended work order type when WO is created'
    )

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)

    # Notes
    notes = models.TextField(blank=True, help_text='Planning notes or remarks')

    # Brazing date (auto-calculated from planned_date + offset)
    planned_brazing_date = models.DateField(
        null=True, blank=True,
        help_text='Estimated brazing date (auto-calculated from due date rules)'
    )

    # Due date change history — array of {old, new, reason, by, at}
    due_date_history = models.JSONField(
        default=list, blank=True,
        help_text='History of due date changes [{old, new, reason, changed_by, changed_at}]'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='created_plan_entries'
    )

    class Meta:
        db_table = "production_plan_entries"
        verbose_name = "Production Plan Entry"
        verbose_name_plural = "Production Plan Entries"
        ordering = ['sequence', '-priority', 'planned_date', 'created_at']

    def __str__(self):
        return f"Plan: {self.drill_bit.serial_number} ({self.get_status_display()})"

    def create_work_order(self, user=None):
        """
        Create a Work Order from this plan entry.

        Returns tuple: (work_order, success, error_code, error_message)
        - If successful: (work_order, True, None, None)
        - If WO already exists: (existing_wo, True, None, None)
        - If drill bit has active WO: (None, False, 'ACTIVE_WO', message)
        """
        if self.work_order:
            return (self.work_order, True, None, None)

        # CRITICAL VALIDATION: Check if drill bit already has an active work order
        # This prevents duplicate WOs even if validation was bypassed at add_to_plan
        active_wo = self.drill_bit.get_active_work_order()
        if active_wo:
            return (
                active_wo,  # Return the blocking WO so frontend can link to it
                False,
                'ACTIVE_WO',
                f"Cannot create WO: Drill bit {self.drill_bit.serial_number} already has "
                f"active Work Order {active_wo.wo_number} ({active_wo.get_status_display()}). "
                f"View it in the WIP tab or at /work-orders/enhanced/{active_wo.pk}/"
            )

        # Determine WO type
        wo_type = self.intended_wo_type or WorkOrder.WOType.FC_REPAIR

        # Generate WO number using account
        if self.account:
            wo_number = self.account.generate_wo_number()
        else:
            from django.utils import timezone
            wo_number = f"WO-{timezone.now().strftime('%Y%m%d%H%M%S')}"

        # Create the work order with RELEASED status (ready to start)
        work_order = WorkOrder.objects.create(
            wo_number=wo_number,
            wo_type=wo_type,
            drill_bit=self.drill_bit,
            design=self.drill_bit.design,
            account=self.account or self.drill_bit.account,
            status=WorkOrder.Status.RELEASED,
            priority=self.priority,
            planned_start=self.planned_date,
            created_by=user,
        )

        # Update plan entry
        self.work_order = work_order
        self.status = self.Status.WO_CREATED
        self.save(update_fields=['work_order', 'status', 'updated_at'])

        return (work_order, True, None, None)

    @classmethod
    def add_to_plan(cls, drill_bit, account=None, priority='NORMAL', planned_date=None,
                    due_date=None, intended_wo_type='', notes='', user=None):
        """
        Add a drill bit to the production plan.

        Returns tuple: (entry, created, error_code, error_message)
        - If successful: (entry, True, None, None)
        - If already in plan: (existing_entry, False, 'IN_PLAN', 'Already in production plan')
        - If has active WO: (None, False, 'ACTIVE_WO', 'Has active work order WO-XXX')
        """
        from datetime import timedelta
        from django.utils import timezone

        # VALIDATION 1: Check if drill bit has an active work order
        active_wo = drill_bit.get_active_work_order()
        if active_wo:
            return (
                None,
                False,
                'ACTIVE_WO',
                f"Cannot add to plan: Active Work Order {active_wo.wo_number} ({active_wo.get_status_display()})"
            )

        # VALIDATION 2: Check for existing active plan entry
        existing = cls.objects.filter(
            drill_bit=drill_bit,
            status=cls.Status.PLANNED
        ).first()

        if existing:
            return (existing, False, 'IN_PLAN', 'This drill bit is already in the production plan')

        # Get max sequence for ordering
        max_seq = cls.objects.filter(status=cls.Status.PLANNED).aggregate(
            max_seq=models.Max('sequence')
        )['max_seq'] or 0

        # Determine effective account
        effective_account = account or drill_bit.account

        # Auto-calculate due_date if not provided
        # Uses PlannerSettings to consider working days, weekends, and holidays
        if due_date is None:
            account_code = effective_account.code if effective_account else None
            due_date = PlannerSettings.calculate_due_date(
                start_date=timezone.now().date(),
                account_code=account_code
            )

        # Auto-calculate planned brazing date (~60% through the schedule)
        brazing_date = None
        if due_date:
            start = planned_date or timezone.now().date()
            total_days = (due_date - start).days
            brazing_offset = max(1, int(total_days * 0.6))
            brazing_date = PlannerSettings.calculate_due_date(
                start_date=start,
                account_code=effective_account.code if effective_account else None
            )
            # Brazing is ~60% into the schedule
            from datetime import timedelta as _td
            brazing_date = start + _td(days=brazing_offset)

        entry = cls.objects.create(
            drill_bit=drill_bit,
            account=effective_account,
            priority=priority,
            planned_date=planned_date,
            due_date=due_date,
            planned_brazing_date=brazing_date,
            intended_wo_type=intended_wo_type,
            sequence=max_seq + 1,
            notes=notes,
            created_by=user,
        )
        return (entry, True, None, None)  # Created successfully


class PlannerSettings(models.Model):
    """
    Singleton model for Production Planner settings.
    Controls due date calculation, weekend days, and working hours.
    """
    # Due date settings per account type
    default_due_days = models.PositiveIntegerField(
        default=6,
        help_text='Default working days for due date calculation'
    )
    ur_due_days = models.PositiveIntegerField(
        default=4,
        help_text='Working days for UR account due date'
    )

    # Weekend configuration (multi-select stored as JSON)
    # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
    weekend_days = models.JSONField(
        default=list,
        help_text='Days of the week that are weekends (0=Mon, 4=Fri, 5=Sat, 6=Sun)'
    )

    # Audit
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "planner_settings"
        verbose_name = "Planner Settings"
        verbose_name_plural = "Planner Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Prevent deletion of singleton
        pass

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance."""
        obj, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'default_due_days': 6,
                'ur_due_days': 4,
                'weekend_days': [4, 5],  # Friday=4, Saturday=5 (Sunday=6 is first working day)
            }
        )
        return obj

    @classmethod
    def calculate_due_date(cls, start_date, account_code=None):
        """
        Calculate due date considering working days, weekends, and holidays.
        Weekend: Friday (4) and Saturday (5). First working day: Sunday (6).

        Args:
            start_date: The starting date (usually today)
            account_code: Account code to determine number of days (UR gets fewer days)

        Returns:
            due_date: The calculated due date
        """
        from datetime import timedelta

        settings_obj = cls.get_settings()

        # Determine number of working days based on account
        if account_code == 'UR':
            working_days_needed = settings_obj.ur_due_days
        else:
            working_days_needed = settings_obj.default_due_days

        # Get weekend days (convert to set for faster lookup)
        # Default: Friday (4), Saturday (5)
        weekend_days = set(settings_obj.weekend_days or [4, 5])

        # Get holidays for the relevant period (next 30 days should be enough)
        end_search = start_date + timedelta(days=working_days_needed + 30)
        holidays = set(
            PlannerHoliday.objects.filter(
                date__gte=start_date,
                date__lte=end_search,
                is_active=True
            ).values_list('date', flat=True)
        )

        # Count working days
        current_date = start_date
        working_days_counted = 0

        while working_days_counted < working_days_needed:
            current_date += timedelta(days=1)

            # Check if it's a working day
            # weekday(): 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
            weekday = current_date.weekday()

            if weekday not in weekend_days and current_date not in holidays:
                working_days_counted += 1

        return current_date

    def get_weekend_display(self):
        """Return human-readable weekend days."""
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return [day_names[d] for d in (self.weekend_days or [])]


class PlannerHoliday(models.Model):
    """
    Holidays that should be excluded from due date calculations.
    """
    date = models.DateField(unique=True)
    name = models.CharField(max_length=100, help_text='Holiday name')
    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_holidays'
    )

    class Meta:
        db_table = "planner_holidays"
        verbose_name = "Planner Holiday"
        verbose_name_plural = "Planner Holidays"
        ordering = ['date']

    def __str__(self):
        return f"{self.name} ({self.date})"


# =============================================================================
# EVALUATION ROUTE BUILDER
# =============================================================================

class EvaluationRoute(models.Model):
    """
    Configurable evaluation route for different bit types and accounts.
    Defines which evaluation steps are needed and in what order.
    """
    class BitType(models.TextChoices):
        NEW = 'NEW', 'New Build'
        USED = 'USED', 'Used/Repair'

    name = models.CharField(
        max_length=100,
        help_text='Route name (e.g., "LSTK Repair Standard", "ARAMCO New Build")'
    )
    description = models.TextField(blank=True, help_text='Description of when this route applies')

    bit_type = models.CharField(
        max_length=10,
        choices=BitType.choices,
        help_text='New build or repair/used'
    )

    account = models.ForeignKey(
        'sales.Account',
        on_delete=models.CASCADE,
        related_name='evaluation_routes',
        help_text='Account this route applies to'
    )

    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(
        default=False,
        help_text='If true, this is the default route for the account+bit_type combination'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_eval_routes'
    )

    class Meta:
        db_table = "evaluation_routes"
        verbose_name = "Evaluation Route"
        verbose_name_plural = "Evaluation Routes"
        ordering = ['account__code', 'bit_type', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['account', 'bit_type'],
                condition=models.Q(is_default=True),
                name='unique_default_route_per_account_bittype'
            )
        ]

    def __str__(self):
        return f"{self.account.code} - {self.get_bit_type_display()} - {self.name}"

    @classmethod
    def get_route_for_workorder(cls, work_order):
        """
        Get the applicable evaluation route for a work order.
        Determines bit_type from WO type and finds matching route.
        """
        # Determine bit type from WO type
        wo_type = work_order.wo_type
        if wo_type in ['NEW', 'L3', 'L4', 'NEW_BUILD']:
            bit_type = cls.BitType.NEW
        else:
            bit_type = cls.BitType.USED

        account = work_order.account
        if not account:
            return None

        # Find default route for account + bit_type
        route = cls.objects.filter(
            account=account,
            bit_type=bit_type,
            is_default=True,
            is_active=True
        ).first()

        # Fallback to any active route for account + bit_type
        if not route:
            route = cls.objects.filter(
                account=account,
                bit_type=bit_type,
                is_active=True
            ).first()

        return route


class EvaluationRouteStep(models.Model):
    """
    Individual step in an evaluation route.
    Maps to CutterEvaluationMatrix.EvaluationType values.
    """
    route = models.ForeignKey(
        EvaluationRoute,
        on_delete=models.CASCADE,
        related_name='steps'
    )

    evaluation_type = models.CharField(
        max_length=20,
        choices=CutterEvaluationMatrix.EvaluationType.choices,
        help_text='The type of evaluation'
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text='Order in the evaluation sequence (lower = first)'
    )

    is_required = models.BooleanField(
        default=True,
        help_text='If true, this step must be completed'
    )

    is_conditional = models.BooleanField(
        default=False,
        help_text='If true, step may be skipped based on conditions'
    )

    condition_description = models.CharField(
        max_length=255,
        blank=True,
        help_text='Describe when this step is needed (e.g., "Only if customer requests")'
    )

    # Display options
    show_decision_field = models.BooleanField(
        default=True,
        help_text='Show decision dropdown (Repair/Scrap/etc.)'
    )

    show_cutter_matrix = models.BooleanField(
        default=True,
        help_text='Show the blade × position cutter matrix'
    )

    show_cutters_details = models.BooleanField(
        default=True,
        help_text='Show the cutters details table (plant use)'
    )

    class Meta:
        db_table = "evaluation_route_steps"
        verbose_name = "Evaluation Route Step"
        verbose_name_plural = "Evaluation Route Steps"
        ordering = ['route', 'order']
        unique_together = ['route', 'evaluation_type']

    def __str__(self):
        req = "Required" if self.is_required else "Optional"
        return f"{self.route.name} - Step {self.order}: {self.get_evaluation_type_display()} ({req})"


# ═══════════════════════════════════════════════════════════════════
# RECEIVING DOCK — Backload Batches + BOM Pending
# ═══════════════════════════════════════════════════════════════════

class BackloadBatch(models.Model):
    """
    Physical receiving of drill bits. Creating a batch = receiving the bits.
    Ops pastes serial numbers, system auto-matches to existing DrillBit records,
    auto-confirms matched items, and auto-raises BOM/registration requests.
    """

    class BatchStatus(models.TextChoices):
        ARRIVED = "ARRIVED", "Arrived"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"

    class BatchType(models.TextChoices):
        REPAIR = "REPAIR", "Repair Bits (Backload)"
        NEW = "NEW", "New Bits (Received)"

    batch_number = models.CharField(max_length=30, unique=True, editable=False)
    batch_type = models.CharField(
        max_length=10, choices=BatchType.choices,
        default=BatchType.REPAIR,
        help_text="Classify bits — mixing NEW and REPAIR not allowed"
    )
    batch_reference = models.CharField(
        max_length=100, blank=True,
        help_text="Email reference, backload paper number, etc."
    )
    account = models.ForeignKey(
        "sales.Account", on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="backload_batches",
        help_text="Auto-populated from matched drill bits"
    )
    customer = models.ForeignKey(
        "sales.Customer", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="backload_batches",
        help_text="Auto-filled from account.customer"
    )
    expected_date = models.DateField(
        null=True, blank=True,
        help_text="When bits are expected to arrive"
    )
    received_date = models.DateField(
        null=True, blank=True,
        help_text="When batch physically arrived"
    )
    item_count = models.PositiveIntegerField(
        default=0,
        help_text="Total items in batch (auto from items.count())"
    )
    received_count = models.PositiveIntegerField(
        default=0,
        help_text="How many confirmed arrived"
    )
    status = models.CharField(
        max_length=20, choices=BatchStatus.choices,
        default=BatchStatus.ARRIVED
    )
    reference_file = models.FileField(
        upload_to="backload_references/%Y/%m/",
        blank=True, null=True,
        help_text="Attachment: email (.msg/.eml), PDF, Excel, image, etc."
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="created_backload_batches"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "backload_batches"
        verbose_name = "Backload Batch"
        verbose_name_plural = "Backload Batches"
        ordering = ["-created_at"]

    def __str__(self):
        label = self.get_batch_type_display() if self.batch_type else "Batch"
        return f"{self.batch_number} ({label})"

    def save(self, *args, **kwargs):
        if not self.batch_number:
            self.batch_number = self.generate_batch_number()
        # Auto-fill customer from account (if account set)
        if self.account_id and not self.customer_id:
            try:
                self.customer = self.account.customer
            except Exception:
                pass
        super().save(*args, **kwargs)

    @staticmethod
    def generate_batch_number():
        """Generate BL-YYYY-NNN using NumberSequence."""
        from apps.organization.models import NumberSequence
        from django.utils import timezone

        year = timezone.now().year
        seq_code = f"BACKLOAD-{year}"
        seq, _ = NumberSequence.objects.select_for_update().get_or_create(
            code=seq_code,
            defaults={
                "name": f"Backload Batch {year}",
                "prefix": f"BL-{year}-",
                "padding": 3,
                "increment_by": 1,
            }
        )
        return seq.get_next_number()

    def update_counts(self):
        """Recalculate item_count and received_count from items."""
        self.item_count = self.items.count()
        self.received_count = self.items.filter(
            status=BackloadItem.ItemStatus.RECEIVED,
        ).count()
        self.save(update_fields=["item_count", "received_count", "updated_at"])

    def auto_update_status(self):
        """Auto-transition batch status based on items.

        Batch-level status flow:
          ARRIVED → batch just created, no inspections started
          PROCESSING → at least one item is being inspected or received
          COMPLETED → all items received
        """
        if self.item_count == 0:
            return

        # Count items that have moved beyond ARRIVED/UNREGISTERED
        active_count = self.items.filter(
            status__in=[
                BackloadItem.ItemStatus.PROCESSING,
                BackloadItem.ItemStatus.RECEIVED,
                BackloadItem.ItemStatus.HOLD,
            ]
        ).count()

        if self.received_count >= self.item_count:
            new_status = self.BatchStatus.COMPLETED
        elif active_count > 0:
            new_status = self.BatchStatus.PROCESSING
        else:
            new_status = self.BatchStatus.ARRIVED

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=["status", "updated_at"])


class BackloadBatchAttachment(models.Model):
    """File attachment for a backload batch (one-to-many)."""
    batch = models.ForeignKey(
        BackloadBatch, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="backload_references/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0, help_text="Size in bytes")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "backload_batch_attachments"
        ordering = ["uploaded_at"]

    def __str__(self):
        return self.original_filename


class BackloadItem(models.Model):
    """
    Individual bit entry in a backload batch.
    Serial number pasted from email/paper, auto-matched to existing DrillBit.
    """

    class ItemStatus(models.TextChoices):
        ARRIVED = "ARRIVED", "Arrived"
        UNREGISTERED = "UNREGISTERED", "Unregistered"
        PROCESSING = "PROCESSING", "Processing"
        RECEIVED = "RECEIVED", "Received"
        HOLD = "HOLD", "Hold"

    class MatchStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        MATCHED = "MATCHED", "Matched"
        UNMATCHED = "UNMATCHED", "Not Found"
        NEW_REGISTERED = "NEW_REGISTERED", "Unregistered"

    batch = models.ForeignKey(
        BackloadBatch, on_delete=models.CASCADE,
        related_name="items"
    )
    serial_number = models.CharField(max_length=50)
    drill_bit = models.ForeignKey(
        "DrillBit", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="backload_items"
    )
    status = models.CharField(
        max_length=20, choices=ItemStatus.choices,
        default=ItemStatus.ARRIVED
    )
    match_status = models.CharField(
        max_length=20, choices=MatchStatus.choices,
        default=MatchStatus.PENDING
    )
    received_date = models.DateTimeField(
        null=True, blank=True,
        help_text="When this specific bit was confirmed arrived"
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="received_backload_items"
    )
    work_order = models.ForeignKey(
        "WorkOrder", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="backload_items"
    )
    bit_event = models.ForeignKey(
        "BitEvent", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="backload_items"
    )
    notes = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "backload_items"
        verbose_name = "Backload Item"
        verbose_name_plural = "Backload Items"
        ordering = ["sort_order", "id"]
        unique_together = [("batch", "serial_number")]

    def __str__(self):
        return f"{self.serial_number} ({self.batch.batch_number})"

    def attempt_match(self):
        """Try to match serial_number to an existing DrillBit."""
        try:
            bit = DrillBit.objects.get(serial_number=self.serial_number)
            self.drill_bit = bit
            self.match_status = self.MatchStatus.MATCHED
        except DrillBit.DoesNotExist:
            self.drill_bit = None
            self.match_status = self.MatchStatus.UNMATCHED
        except DrillBit.MultipleObjectsReturned:
            # Edge case — take first match
            bit = DrillBit.objects.filter(serial_number=self.serial_number).first()
            self.drill_bit = bit
            self.match_status = self.MatchStatus.MATCHED
        self.save(update_fields=["drill_bit", "match_status"])


class BOMPendingRequest(models.Model):
    """
    Request for tech team to assign BOM to a drill bit.
    Auto-created when a new bit is registered without a BOM.
    """

    class RequestStatus(models.TextChoices):
        OPEN = "OPEN", "Open"
        ASSIGNED = "ASSIGNED", "BOM Assigned"
        CANCELLED = "CANCELLED", "Cancelled"

    drill_bit = models.ForeignKey(
        "DrillBit", on_delete=models.CASCADE,
        related_name="bom_pending_requests"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="bom_requests_created"
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="bom_requests_resolved"
    )
    status = models.CharField(
        max_length=20, choices=RequestStatus.choices,
        default=RequestStatus.OPEN
    )
    notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bom_pending_requests"
        verbose_name = "BOM Pending Request"
        verbose_name_plural = "BOM Pending Requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"BOM Request: {self.drill_bit.serial_number} ({self.get_status_display()})"


# =============================================================================
# STANDALONE TEST REPORTS — Die Check, LPT, API Thread Inspection
# These are separate pages linked to evaluations, with auto-fill to checklists.
# =============================================================================

class DieCheckReport(models.Model):
    """
    Standalone Die Check report linked to WO or DrillBit.
    Also captures LPT materials used (Penetrant, Developer) per QAS/1004-1.
    Auto-detects stage (Before Braze / After Repair / Other) from existing reports.
    """

    class Stage(models.TextChoices):
        BEFORE_BRAZE = "BEFORE_BRAZE", "Before Braze"
        AFTER_REPAIR = "AFTER_REPAIR", "After Repair"
        OTHER = "OTHER", "Other"

    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, null=True, blank=True,
        related_name="die_check_reports"
    )
    drill_bit = models.ForeignKey(
        DrillBit, on_delete=models.CASCADE, null=True, blank=True,
        related_name="die_check_reports"
    )
    evaluation = models.ForeignKey(
        CutterEvaluationMatrix, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="die_check_reports",
        help_text="Linked evaluation (auto-fills checklist item when completed)"
    )

    report_number = models.CharField(max_length=30, blank=True)
    stage = models.CharField(
        max_length=20, choices=Stage.choices, default=Stage.BEFORE_BRAZE,
        help_text="Stage in the repair process when this die check was performed"
    )

    # Grid data: {blade: {position: {value: 'OK'|'NG'|'', remarks: ''}}}
    grid_data = models.JSONField(
        null=True, blank=True,
        help_text="Die check grid: blade → position → result"
    )

    # LPT materials used during the die check (Penetrant, Developer)
    # Format: {penetrant: {product, batch, expiry}, developer: {product, batch, expiry}}
    materials_data = models.JSONField(
        null=True, blank=True,
        help_text="LPT materials: penetrant & developer product, batch, expiry"
    )

    result = models.CharField(
        max_length=10, blank=True,
        choices=[('PASS', 'Pass'), ('FAIL', 'Fail'), ('PARTIAL', 'Partial')],
    )
    remarks = models.TextField(blank=True)

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="die_checks_performed"
    )
    performed_at = models.DateTimeField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "die_check_reports"
        ordering = ["-created_at"]

    def __str__(self):
        ref = self.work_order.wo_number if self.work_order else (
            self.drill_bit.serial_number if self.drill_bit else "?")
        return f"Die Check {self.report_number} ({self.get_stage_display()}) — {ref}"

    @classmethod
    def auto_detect_stage(cls, work_order):
        """Auto-detect stage based on how many die checks already exist for this WO."""
        count = cls.objects.filter(work_order=work_order).count()
        if count == 0:
            return cls.Stage.BEFORE_BRAZE
        return cls.Stage.AFTER_REPAIR


class StandaloneLPTReport(models.Model):
    """
    Standalone Liquid Penetrant Testing (LPT/Pressure Test) report per QAS/1004-1.
    Linked to WO or DrillBit. Auto-fills checklist item when completed.
    Separate from legacy LPTReport which is WO-only.
    """
    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, null=True, blank=True,
        related_name="standalone_lpt_reports"
    )
    drill_bit = models.ForeignKey(
        DrillBit, on_delete=models.CASCADE, null=True, blank=True,
        related_name="standalone_lpt_reports"
    )
    evaluation = models.ForeignKey(
        CutterEvaluationMatrix, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="standalone_lpt_reports",
        help_text="Linked evaluation (auto-fills checklist item when completed)"
    )

    report_number = models.CharField(max_length=30, blank=True)

    # LPT data (JSON): {timing, materials: [{type, product, batch, expiry}],
    #   surface_temp, light_intensity, penetrant_dwell, developer_dwell,
    #   operator, result, remarks, indications: [{location, size, type}]}
    test_data = models.JSONField(
        null=True, blank=True,
        help_text="LPT test parameters and results per QAS/1004-1"
    )

    result = models.CharField(
        max_length=15, blank=True,
        choices=[('PASS', 'Pass'), ('FAIL', 'Fail'), ('INCONCLUSIVE', 'Inconclusive')],
    )
    remarks = models.TextField(blank=True)

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="standalone_lpt_tests_performed"
    )
    performed_at = models.DateTimeField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "standalone_lpt_reports"
        ordering = ["-created_at"]

    def __str__(self):
        ref = self.work_order.wo_number if self.work_order else (
            self.drill_bit.serial_number if self.drill_bit else "?")
        return f"LPT {self.report_number} — {ref}"


class StandaloneThreadReport(models.Model):
    """
    Standalone API Thread Inspection report.
    Linked to WO or DrillBit. Optional — visual inspection may suffice.
    Separate from legacy APIThreadInspection which is WO-only.
    """
    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, null=True, blank=True,
        related_name="standalone_thread_reports"
    )
    drill_bit = models.ForeignKey(
        DrillBit, on_delete=models.CASCADE, null=True, blank=True,
        related_name="standalone_thread_reports"
    )
    evaluation = models.ForeignKey(
        CutterEvaluationMatrix, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="standalone_thread_reports",
        help_text="Linked evaluation (auto-fills checklist item when completed)"
    )

    report_number = models.CharField(max_length=30, blank=True)

    # Inspection data (JSON): {checkpoints: [{item, ok, remarks}],
    #   pin_height, connection_type, connection_size,
    #   repair_required, repair_ops: [], inspector, remarks}
    inspection_data = models.JSONField(
        null=True, blank=True,
        help_text="API Thread checkpoints and measurements"
    )

    result = models.CharField(
        max_length=10, blank=True,
        choices=[('PASS', 'Pass'), ('FAIL', 'Fail')],
    )
    remarks = models.TextField(blank=True)

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="standalone_thread_inspections_performed"
    )
    performed_at = models.DateTimeField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "standalone_thread_reports"
        ordering = ["-created_at"]

    def __str__(self):
        ref = self.work_order.wo_number if self.work_order else (
            self.drill_bit.serial_number if self.drill_bit else "?")
        return f"Thread Inspection {self.report_number} — {ref}"

