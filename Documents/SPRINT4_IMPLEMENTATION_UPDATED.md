# 🚀 SPRINT 4 IMPLEMENTATION - UPDATED & VALIDATED
## Pragmatic Approach: Design + Migrations, Tests/Permissions Later

**Date:** December 5, 2024  
**Approach:** Option A (Pragmatic)  
**Based On:** Real code review + Original Sprint 4 design  
**Status:** Ready for Claude Code implementation  

---

## 🎯 WHAT'S DIFFERENT IN THIS UPDATE

### Changes from Original Sprint 4:

**ADDED:**
- ✅ Migration generation steps (CRITICAL)
- ✅ Model validation checkpoints
- ✅ Verification procedures after each day
- ✅ Circular dependency checks
- ✅ Database testing steps

**DEFERRED:**
- ⏭️ Comprehensive test writing (to final phase)
- ⏭️ Permission checks (to final phase)
- ⏭️ Security hardening (to final phase)

**KEPT:**
- ✅ All 39 models (design is good!)
- ✅ All 35 forms (design is good!)
- ✅ All 74 views (design is good!)
- ✅ All workflows (design is good!)

### Why This Approach:

**Do Now (Migrations):**
- Validates models actually work
- Catches circular dependencies early
- Enables Sprint 5 to proceed
- Only 2-3 hours per sprint

**Do Later (Tests/Permissions):**
- More efficient in batch after all sprints
- Won't slow development velocity
- Can test complete workflows
- Standard agile practice

---

## 📋 SPRINT 4 OVERVIEW - UPDATED

### Scope: Drill Bit Repair Workflow Models

**Apps to Create/Update:**
- `apps/workorders/` - DrillBit and WorkOrder models (ALREADY EXISTS)
- `apps/quality/` - NCR, Inspection models (ALREADY EXISTS)
- `apps/inventory/` - Inventory models (ALREADY EXISTS)
- `apps/maintenance/` - Equipment models (ALREADY EXISTS)
- `apps/planning/` - Production planning (ALREADY EXISTS)
- `apps/dispatch/` - Shipping models (ALREADY EXISTS)

**What We're Adding:**
- Specific drill bit repair fields
- Repair workflow models
- Cost tracking models
- Salvage tracking
- Enhanced relationships

---

## 📅 UPDATED SPRINT 4 TIMELINE

### Days 1-8: Core Models + Migrations (as originally planned)
### Days 9-12: Operations Models + Migrations (updated with migrations)
### Days 13-14: Basic Validation + Documentation (updated approach)

**Total Time:** 11 days (same as original)  
**Key Addition:** Migration generation and validation at each checkpoint

---

## 🔧 DAY 1-2: DRILL BIT & WORK ORDER MODELS

### Part 1: Review Existing Models

**IMPORTANT:** These models ALREADY EXIST in your codebase!

**What I Found:**
```python
# apps/workorders/models.py - ALREADY EXISTS

class DrillBit(models.Model):
    # Basic fields present:
    serial_number = models.CharField(max_length=50, unique=True)
    bit_type = models.CharField(max_length=20, choices=BitType.choices)
    size = models.DecimalField(max_digits=6, decimal_places=3)
    status = models.CharField(max_length=20, choices=Status.choices)
    # ... more fields
    
class WorkOrder(models.Model):
    wo_number = models.CharField(max_length=30, unique=True)
    wo_type = models.CharField(max_length=20, choices=WOType.choices)
    status = models.CharField(max_length=20, choices=Status.choices)
    # ... more fields
```

### Part 2: Add Sprint 4 Specific Fields

**Add to DrillBit model:**

```python
# apps/workorders/models.py - ADD THESE FIELDS

class DrillBit(models.Model):
    # ... existing fields ...
    
    # ADD: Aramco-specific fields (from Sprint 4 corrections)
    base_serial_number = models.CharField(
        max_length=50, 
        help_text="Original serial without revision (e.g., 'ABC-001')"
    )
    current_display_serial = models.CharField(
        max_length=50,
        help_text="Display serial with revision (e.g., 'ABC-001-R2')"
    )
    revision_number = models.IntegerField(
        default=0,
        help_text="Number of repairs (0=new, 1=R1, 2=R2, etc.)"
    )
    is_aramco_contract = models.BooleanField(
        default=False,
        help_text="If True, serial increments on repair (R1, R2, R3)"
    )
    
    # ADD: Enhanced status tracking
    physical_status = models.CharField(
        max_length=20,
        choices=PhysicalStatus.choices,
        default='IN_STOCK',
        help_text="Physical location/condition of bit"
    )
    accounting_status = models.CharField(
        max_length=20,
        choices=AccountingStatus.choices,
        default='ACTIVE',
        help_text="Financial/ownership status"
    )
    
    # ADD: Repair tracking
    total_repairs = models.IntegerField(
        default=0,
        help_text="Total number of repairs performed"
    )
    last_repair_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of most recent repair"
    )
    last_repair_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of last repair performed"
    )
    
    # ADD: Cost tracking
    original_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Original purchase cost"
    )
    total_repair_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Cumulative repair costs"
    )
    current_book_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Current accounting value"
    )
    
    # ADD: Status choices
    class PhysicalStatus(models.TextChoices):
        IN_STOCK = "IN_STOCK", "In Stock"
        IN_REPAIR = "IN_REPAIR", "In Repair Shop"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        AT_CUSTOMER = "AT_CUSTOMER", "At Customer Site"
        IN_FIELD = "IN_FIELD", "In Field (Running)"
        RETURNED = "RETURNED", "Returned from Field"
        SALVAGE_HOLD = "SALVAGE_HOLD", "Salvage Hold"
        SCRAPPED = "SCRAPPED", "Scrapped"
    
    class AccountingStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active Inventory"
        REPAIR_WIP = "REPAIR_WIP", "Repair Work-in-Progress"
        CUSTOMER_OWNED = "CUSTOMER_OWNED", "Customer Owned"
        SCRAPPED = "SCRAPPED", "Scrapped/Written Off"
        SOLD = "SOLD", "Sold"
```

**Add to WorkOrder model:**

```python
# apps/workorders/models.py - ADD THESE FIELDS

class WorkOrder(models.Model):
    # ... existing fields ...
    
    # ADD: Repair-specific fields
    repair_type = models.CharField(
        max_length=50,
        choices=RepairType.choices,
        blank=True,
        help_text="Specific type of repair"
    )
    
    # ADD: Approval tracking
    requires_approval = models.BooleanField(
        default=False,
        help_text="True if cost exceeds approval threshold"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_work_orders",
        help_text="Manager who approved high-cost repair"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Approval timestamp"
    )
    
    # ADD: Cost tracking
    estimated_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Estimated total cost"
    )
    actual_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Actual total cost incurred"
    )
    
    # ADD: Disposition tracking
    disposition = models.CharField(
        max_length=50,
        choices=Disposition.choices,
        blank=True,
        help_text="Final disposition after repair"
    )
    disposition_notes = models.TextField(
        blank=True,
        help_text="Reasoning for disposition decision"
    )
    
    class RepairType(models.TextChoices):
        REDRESS = "REDRESS", "Redress"
        REBUILD = "REBUILD", "Rebuild"
        HARDFACING = "HARDFACING", "Hardfacing"
        BEARING_REPLACEMENT = "BEARING_REPLACEMENT", "Bearing Replacement"
        NOZZLE_REPLACEMENT = "NOZZLE_REPLACEMENT", "Nozzle Replacement"
        GENERAL_REPAIR = "GENERAL_REPAIR", "General Repair"
    
    class Disposition(models.TextChoices):
        RETURN_SERVICE = "RETURN_SERVICE", "Return to Service"
        SCRAP = "SCRAP", "Scrap - Total Loss"
        SCRAP_SAVE_BODY = "SCRAP_SAVE_BODY", "Scrap - Save Body"
        CUSTOMER_DISPOSAL = "CUSTOMER_DISPOSAL", "Customer Disposal"
```

---

### ✅ CHECKPOINT 1: Generate Migrations

**CRITICAL STEP - DO NOT SKIP:**

```bash
# Generate migrations for updated models
python manage.py makemigrations workorders

# Expected output:
# Migrations for 'workorders':
#   apps/workorders/migrations/00XX_add_sprint4_fields.py
#     - Add field base_serial_number to drillbit
#     - Add field current_display_serial to drillbit
#     - Add field revision_number to drillbit
#     - ... (all new fields)

# Apply migrations
python manage.py migrate workorders

# Verify in database
python manage.py dbshell
\d workorders_drillbit  # Should show new columns
```

**Test the Changes:**

```python
# python manage.py shell

from apps.workorders.models import DrillBit, WorkOrder
from decimal import Decimal

# Test 1: Create Aramco contract drill bit
bit = DrillBit.objects.create(
    serial_number="ABC-001",
    base_serial_number="ABC-001",
    current_display_serial="ABC-001",
    bit_type="FC",
    size=Decimal("8.500"),
    is_aramco_contract=True,
    revision_number=0
)
print(f"✅ Created: {bit}")

# Test 2: Simulate repair (increment revision)
bit.revision_number = 1
bit.current_display_serial = "ABC-001-R1"
bit.total_repairs = 1
bit.save()
print(f"✅ After repair: {bit.current_display_serial}")

# Test 3: Create work order
wo = WorkOrder.objects.create(
    wo_number="WO-2024-001",
    wo_type="FC_REPAIR",
    drill_bit=bit,
    repair_type="REDRESS",
    estimated_cost=Decimal("5000.00")
)
print(f"✅ Created WO: {wo}")

# Test 4: Verify relationships
print(f"✅ Bit's work orders: {bit.work_orders.count()}")
```

**Expected Results:**
- ✅ No errors creating objects
- ✅ Relationships work (bit.work_orders.all())
- ✅ New fields save correctly
- ✅ Revision tracking works

---

## 🔧 DAY 3-4: REPAIR WORKFLOW MODELS

### New Models to Create:

**1. StatusTransitionLog** (Audit Trail)

```python
# apps/workorders/models.py - ADD NEW MODEL

class StatusTransitionLog(models.Model):
    """
    Audit log of all status changes for drill bits and work orders.
    ISO 9001 Clause 7.5: Documented Information
    """
    
    # Polymorphic reference (can link to DrillBit or WorkOrder)
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        help_text="Type of object (DrillBit or WorkOrder)"
    )
    object_id = models.PositiveIntegerField(
        help_text="ID of the object"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Status change details
    from_status = models.CharField(
        max_length=50,
        help_text="Previous status"
    )
    to_status = models.CharField(
        max_length=50,
        help_text="New status"
    )
    
    # Who and when
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="status_changes"
    )
    changed_at = models.DateTimeField(
        auto_now_add=True
    )
    
    # Why
    reason = models.TextField(
        blank=True,
        help_text="Reason for status change"
    )
    
    # Context
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text="Physical location when changed"
    )
    
    class Meta:
        db_table = "status_transition_logs"
        ordering = ["-changed_at"]
        verbose_name = "Status Transition Log"
        verbose_name_plural = "Status Transition Logs"
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['changed_at']),
        ]
    
    def __str__(self):
        return f"{self.from_status} → {self.to_status} at {self.changed_at}"
```

**2. BitRepairHistory** (Detailed Repair Records)

```python
# apps/workorders/models.py - ADD NEW MODEL

class BitRepairHistory(models.Model):
    """
    Detailed history of each repair performed on a drill bit.
    API Q1 7.5.3: Identification and Traceability
    """
    
    drill_bit = models.ForeignKey(
        DrillBit,
        on_delete=models.CASCADE,
        related_name="repair_history"
    )
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.SET_NULL,
        null=True,
        related_name="bit_repairs"
    )
    
    # Repair details
    repair_number = models.IntegerField(
        help_text="Sequential repair number (1, 2, 3, etc.)"
    )
    repair_date = models.DateField()
    repair_type = models.CharField(
        max_length=50,
        help_text="Type of repair performed"
    )
    
    # What was done
    work_performed = models.TextField(
        help_text="Description of work performed"
    )
    parts_replaced = models.TextField(
        blank=True,
        help_text="List of parts replaced"
    )
    
    # Cost
    labor_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    material_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Condition
    condition_before = models.CharField(
        max_length=50,
        help_text="Condition when received"
    )
    condition_after = models.CharField(
        max_length=50,
        help_text="Condition after repair"
    )
    
    # Who performed repair
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="repairs_performed"
    )
    
    # Serial number tracking for Aramco
    serial_before = models.CharField(
        max_length=50,
        help_text="Serial number before repair"
    )
    serial_after = models.CharField(
        max_length=50,
        help_text="Serial number after repair (with revision)"
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "bit_repair_history"
        ordering = ["-repair_date"]
        verbose_name = "Bit Repair History"
        verbose_name_plural = "Bit Repair Histories"
        indexes = [
            models.Index(fields=['drill_bit', 'repair_number']),
            models.Index(fields=['repair_date']),
        ]
    
    def __str__(self):
        return f"{self.drill_bit.serial_number} - Repair #{self.repair_number}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total cost
        self.total_cost = self.labor_cost + self.material_cost
        super().save(*args, **kwargs)
```

**3. SalvageItem** (Track Salvaged Parts)

```python
# apps/workorders/models.py - ADD NEW MODEL

class SalvageItem(models.Model):
    """
    Track salvaged components from scrapped drill bits.
    ISO 9001 Clause 8.7: Control of nonconforming outputs
    """
    
    class SalvageType(models.TextChoices):
        BODY = "BODY", "Bit Body"
        CUTTERS = "CUTTERS", "Cutters/Inserts"
        BEARINGS = "BEARINGS", "Bearings"
        NOZZLES = "NOZZLES", "Nozzles"
        COMPONENTS = "COMPONENTS", "Other Components"
        COMPLETE = "COMPLETE", "Complete Unit"
    
    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Received"
        INSPECTED = "INSPECTED", "Inspected"
        STORED = "STORED", "In Storage"
        ALLOCATED = "ALLOCATED", "Allocated for Reuse"
        REUSED = "REUSED", "Reused"
        SCRAPPED = "SCRAPPED", "Scrapped"
    
    salvage_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique salvage tracking number"
    )
    
    # Source
    drill_bit = models.ForeignKey(
        DrillBit,
        on_delete=models.CASCADE,
        related_name="salvaged_items"
    )
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.SET_NULL,
        null=True,
        related_name="salvaged_items"
    )
    
    # What was salvaged
    salvage_type = models.CharField(
        max_length=20,
        choices=SalvageType.choices
    )
    description = models.TextField(
        help_text="Detailed description of salvaged item"
    )
    
    # Condition
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED
    )
    condition_rating = models.CharField(
        max_length=20,
        help_text="Condition (Excellent/Good/Fair/Poor)"
    )
    
    # Reuse potential
    reuse_potential = models.TextField(
        blank=True,
        help_text="Assessment of reuse potential"
    )
    reuse_limitations = models.TextField(
        blank=True,
        help_text="Known limitations or restrictions"
    )
    
    # Storage
    warehouse = models.ForeignKey(
        'sales.Warehouse',
        on_delete=models.SET_NULL,
        null=True,
        related_name="salvage_items"
    )
    storage_location = models.CharField(
        max_length=100,
        blank=True,
        help_text="Specific location in warehouse"
    )
    
    # Dates
    salvage_date = models.DateField(
        help_text="Date item was salvaged"
    )
    inspection_date = models.DateField(
        null=True,
        blank=True
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date after which salvage is no longer viable"
    )
    
    # Reuse tracking
    reused = models.BooleanField(
        default=False
    )
    reuse_work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="salvage_used"
    )
    reuse_date = models.DateField(
        null=True,
        blank=True
    )
    
    # Value
    estimated_salvage_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    actual_value_realized = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Value realized when reused or sold"
    )
    
    # Who
    salvaged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="salvaged_items"
    )
    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspected_salvage"
    )
    
    # Photos
    photo_1 = models.ImageField(
        upload_to="salvage_photos/",
        null=True,
        blank=True
    )
    photo_2 = models.ImageField(
        upload_to="salvage_photos/",
        null=True,
        blank=True
    )
    photo_3 = models.ImageField(
        upload_to="salvage_photos/",
        null=True,
        blank=True
    )
    
    notes = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "salvage_items"
        ordering = ["-salvage_date"]
        verbose_name = "Salvage Item"
        verbose_name_plural = "Salvage Items"
        indexes = [
            models.Index(fields=['salvage_number']),
            models.Index(fields=['status']),
            models.Index(fields=['salvage_date']),
        ]
    
    def __str__(self):
        return f"{self.salvage_number} - {self.salvage_type}"
    
    @property
    def is_expired(self):
        """Check if salvage has expired"""
        if self.expiry_date:
            from django.utils import timezone
            return timezone.now().date() > self.expiry_date
        return False
    
    @property
    def days_in_storage(self):
        """Calculate days in storage"""
        from django.utils import timezone
        return (timezone.now().date() - self.salvage_date).days
```

---

### ✅ CHECKPOINT 2: Generate Migrations for New Models

```bash
# Generate migrations
python manage.py makemigrations workorders

# Expected: 3 new models
# - StatusTransitionLog
# - BitRepairHistory  
# - SalvageItem

# Apply migrations
python manage.py migrate workorders

# Test
python manage.py shell
```

```python
from apps.workorders.models import (
    DrillBit, WorkOrder, StatusTransitionLog,
    BitRepairHistory, SalvageItem
)
from decimal import Decimal
from django.utils import timezone

# Test StatusTransitionLog
bit = DrillBit.objects.first()
log = StatusTransitionLog.objects.create(
    content_object=bit,
    from_status='IN_STOCK',
    to_status='IN_REPAIR',
    reason='Starting repair work'
)
print(f"✅ Status log: {log}")

# Test BitRepairHistory
wo = WorkOrder.objects.first()
history = BitRepairHistory.objects.create(
    drill_bit=bit,
    work_order=wo,
    repair_number=1,
    repair_date=timezone.now().date(),
    repair_type='REDRESS',
    work_performed='Redressed cutters, replaced bearings',
    labor_cost=Decimal('2000.00'),
    material_cost=Decimal('1500.00'),
    serial_before='ABC-001',
    serial_after='ABC-001-R1'
)
print(f"✅ Repair history: {history}")
print(f"   Total cost: ${history.total_cost}")

# Test SalvageItem
salvage = SalvageItem.objects.create(
    salvage_number='SALV-2024-001',
    drill_bit=bit,
    salvage_type='BODY',
    description='8.5" PDC bit body in good condition',
    condition_rating='Good',
    salvage_date=timezone.now().date(),
    estimated_salvage_value=Decimal('3000.00')
)
print(f"✅ Salvage item: {salvage}")

# Test relationships
print(f"✅ Bit repair history count: {bit.repair_history.count()}")
print(f"✅ Bit salvaged items count: {bit.salvaged_items.count()}")
```

---

## 🔧 DAY 5-6: EVALUATION & BOM MODELS

### Update Existing Models:

**RepairEvaluation** (Enhanced BitEvaluation)

```python
# apps/workorders/models.py - UPDATE BitEvaluation to RepairEvaluation

class RepairEvaluation(models.Model):
    """
    Enhanced evaluation model for repair decisions.
    Replaces/extends BitEvaluation with approval workflow.
    """
    
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Evaluation"
        IN_REVIEW = "IN_REVIEW", "In Review"
        APPROVED = "APPROVED", "Approved for Repair"
        REJECTED = "REJECTED", "Rejected - Not Economical"
        COMPLETED = "COMPLETED", "Evaluation Complete"
    
    evaluation_number = models.CharField(
        max_length=50,
        unique=True
    )
    
    drill_bit = models.ForeignKey(
        DrillBit,
        on_delete=models.CASCADE,
        related_name="repair_evaluations"
    )
    
    # Field data (from DRSS or customer)
    hours_run = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    footage_drilled = models.IntegerField(
        null=True,
        blank=True
    )
    pull_condition = models.CharField(
        max_length=100,
        blank=True,
        help_text="Condition when pulled from hole"
    )
    
    # IADC Dull Grading
    inner_rows = models.CharField(max_length=10, blank=True)
    outer_rows = models.CharField(max_length=10, blank=True)
    dull_char = models.CharField(max_length=10, blank=True)
    location = models.CharField(max_length=10, blank=True)
    bearing_seal = models.CharField(max_length=10, blank=True)
    gauge = models.CharField(max_length=10, blank=True)
    
    # Technical evaluation
    damage_assessment = models.TextField(
        help_text="Detailed damage assessment"
    )
    recommended_repair = models.CharField(
        max_length=50,
        blank=True,
        help_text="Recommended repair type"
    )
    estimated_repair_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Decision
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    repair_recommended = models.BooleanField(
        default=False,
        help_text="True if repair is economically viable"
    )
    recommendation_notes = models.TextField(
        blank=True
    )
    
    # Approval (if cost exceeds threshold)
    requires_approval = models.BooleanField(
        default=False
    )
    approval_authority = models.ForeignKey(
        'RepairApprovalAuthority',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Authority level required for approval"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_evaluations"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )
    approval_notes = models.TextField(
        blank=True
    )
    
    # Who evaluated
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="performed_evaluations"
    )
    evaluated_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Resulting action
    resulting_work_order = models.OneToOneField(
        WorkOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_evaluation"
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "repair_evaluations"
        ordering = ["-created_at"]
        verbose_name = "Repair Evaluation"
        verbose_name_plural = "Repair Evaluations"
        indexes = [
            models.Index(fields=['evaluation_number']),
            models.Index(fields=['status']),
            models.Index(fields=['drill_bit']),
        ]
    
    def __str__(self):
        return f"{self.evaluation_number} - {self.drill_bit.serial_number}"
```

**RepairApprovalAuthority** (Authority Matrix)

```python
# apps/workorders/models.py - ADD NEW MODEL

class RepairApprovalAuthority(models.Model):
    """
    Define approval authority levels based on cost thresholds.
    ISO 9001 Clause 5.3: Organizational roles, responsibilities and authorities
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Authority level name (e.g., 'Shop Supervisor', 'Operations Manager')"
    )
    
    # Cost threshold
    min_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Minimum cost requiring this authority"
    )
    max_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum cost this authority can approve (null = unlimited)"
    )
    
    # Who has this authority
    authorized_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="approval_authorities",
        blank=True,
        help_text="Users with this approval authority"
    )
    
    # Settings
    requires_justification = models.BooleanField(
        default=False,
        help_text="Requires written justification for approval"
    )
    active = models.BooleanField(
        default=True
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "repair_approval_authorities"
        ordering = ['min_amount']
        verbose_name = "Repair Approval Authority"
        verbose_name_plural = "Repair Approval Authorities"
    
    def __str__(self):
        if self.max_amount:
            return f"{self.name} (${self.min_amount:,.0f} - ${self.max_amount:,.0f})"
        return f"{self.name} (${self.min_amount:,.0f}+)"
    
    def can_approve(self, amount):
        """Check if this authority can approve given amount"""
        if amount < self.min_amount:
            return False
        if self.max_amount and amount > self.max_amount:
            return False
        return True
```

**RepairBOM** (Bill of Materials)

```python
# apps/workorders/models.py - ADD NEW MODEL

class RepairBOM(models.Model):
    """
    Bill of Materials specific to a repair work order.
    Links to master BOM but allows customization per repair.
    """
    
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="repair_bom"
    )
    
    # Reference to master BOM (if exists)
    master_bom = models.ForeignKey(
        'technology.BOM',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="repair_instances"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('APPROVED', 'Approved'),
            ('ISSUED', 'Issued'),
            ('COMPLETED', 'Completed'),
        ],
        default='DRAFT'
    )
    
    # Costs
    estimated_material_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    actual_material_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    notes = models.TextField(blank=True)
    
    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_repair_boms"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_repair_boms"
    )
    
    class Meta:
        db_table = "repair_boms"
        ordering = ["-created_at"]
        verbose_name = "Repair BOM"
        verbose_name_plural = "Repair BOMs"
    
    def __str__(self):
        return f"BOM for {self.work_order.wo_number}"


class RepairBOMLine(models.Model):
    """Individual line items in a repair BOM"""
    
    repair_bom = models.ForeignKey(
        RepairBOM,
        on_delete=models.CASCADE,
        related_name="lines"
    )
    
    line_number = models.IntegerField(
        help_text="Sequential line number"
    )
    
    # Item
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name="repair_bom_lines"
    )
    
    # Quantity
    quantity_required = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )
    quantity_issued = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0
    )
    quantity_consumed = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0
    )
    
    # Cost
    unit_cost = models.DecimalField(
        max_digits=15,
        decimal_places=4
    )
    total_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = "repair_bom_lines"
        ordering = ['repair_bom', 'line_number']
        unique_together = ['repair_bom', 'line_number']
    
    def __str__(self):
        return f"Line {self.line_number}: {self.inventory_item.name}"
    
    def save(self, *args, **kwargs):
        self.total_cost = self.quantity_consumed * self.unit_cost
        super().save(*args, **kwargs)
```

---

### ✅ CHECKPOINT 3: Generate Migrations

```bash
python manage.py makemigrations workorders
python manage.py migrate workorders

# Test the approval workflow
python manage.py shell
```

```python
from apps.workorders.models import *
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()
supervisor = User.objects.first()

# Create approval authorities
auth_low = RepairApprovalAuthority.objects.create(
    name="Shop Supervisor",
    min_amount=Decimal('0'),
    max_amount=Decimal('5000')
)
auth_low.authorized_users.add(supervisor)

auth_high = RepairApprovalAuthority.objects.create(
    name="Operations Manager",
    min_amount=Decimal('5000'),
    max_amount=Decimal('25000')
)

print(f"✅ Created authorities: {RepairApprovalAuthority.objects.count()}")

# Test evaluation with approval
bit = DrillBit.objects.first()
evaluation = RepairEvaluation.objects.create(
    evaluation_number="EVAL-2024-001",
    drill_bit=bit,
    damage_assessment="Severe cutter damage, bearing wear",
    estimated_repair_cost=Decimal('7500.00'),
    repair_recommended=True,
    requires_approval=True,  # > $5000
    approval_authority=auth_high  # Needs manager
)

print(f"✅ Evaluation requires: {evaluation.approval_authority}")
print(f"   Can supervisor approve $7500? {auth_low.can_approve(7500)}")  # False
print(f"   Can manager approve $7500? {auth_high.can_approve(7500)}")  # True
```

**Expected:**
- ✅ Approval authorities created
- ✅ Threshold checking works
- ✅ Authority assignment works

---

## 📝 DAYS 7-8: PROCESS & COST MODELS

### Process Execution Models:

**ProcessRoute** (Routing for Repair Operations)

```python
# apps/workorders/models.py - ADD NEW MODEL

class ProcessRoute(models.Model):
    """
    Define the sequence of operations for a repair type.
    Similar to manufacturing routing.
    """
    
    route_number = models.CharField(
        max_length=50,
        unique=True
    )
    name = models.CharField(
        max_length=200,
        help_text="Route name (e.g., 'Standard PDC Redress')"
    )
    
    # Applicable to
    repair_type = models.CharField(
        max_length=50,
        help_text="Repair type this route is for"
    )
    bit_types = models.CharField(
        max_length=100,
        blank=True,
        help_text="Applicable bit types (comma-separated)"
    )
    
    # Status
    active = models.BooleanField(default=True)
    version = models.IntegerField(
        default=1,
        help_text="Route version number"
    )
    
    # Estimated totals
    estimated_duration_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    estimated_labor_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    notes = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        db_table = "process_routes"
        ordering = ['route_number']
    
    def __str__(self):
        return f"{self.route_number} - {self.name}"


class ProcessRouteOperation(models.Model):
    """Individual operations within a process route"""
    
    route = models.ForeignKey(
        ProcessRoute,
        on_delete=models.CASCADE,
        related_name="operations"
    )
    
    sequence = models.IntegerField(
        help_text="Operation sequence number"
    )
    operation_code = models.CharField(
        max_length=50
    )
    operation_name = models.CharField(
        max_length=200
    )
    description = models.TextField(blank=True)
    
    # Work center/department
    work_center = models.CharField(
        max_length=100,
        blank=True,
        help_text="Where operation is performed"
    )
    
    # Standards
    standard_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Standard time to complete operation"
    )
    labor_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Labor rate for this operation"
    )
    
    # Quality checks
    requires_qc = models.BooleanField(
        default=False,
        help_text="Requires QC inspection after operation"
    )
    qc_checklist = models.TextField(
        blank=True,
        help_text="QC points to verify"
    )
    
    # Safety
    safety_requirements = models.TextField(
        blank=True,
        help_text="PPE and safety requirements"
    )
    
    class Meta:
        db_table = "process_route_operations"
        ordering = ['route', 'sequence']
        unique_together = ['route', 'sequence']
    
    def __str__(self):
        return f"{self.sequence}. {self.operation_name}"


class OperationExecution(models.Model):
    """Actual execution of an operation on a work order"""
    
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        SKIPPED = "SKIPPED", "Skipped"
        FAILED = "FAILED", "Failed"
    
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="operation_executions"
    )
    
    route_operation = models.ForeignKey(
        ProcessRouteOperation,
        on_delete=models.PROTECT,
        related_name="executions"
    )
    
    # Execution details
    sequence = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Who and when
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="operations_performed"
    )
    start_time = models.DateTimeField(
        null=True,
        blank=True
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True
    )
    actual_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Cost
    labor_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Quality check
    qc_performed = models.BooleanField(default=False)
    qc_passed = models.BooleanField(default=False)
    qc_notes = models.TextField(blank=True)
    qc_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="qc_operations"
    )
    
    # Notes
    operator_notes = models.TextField(
        blank=True,
        help_text="Notes from operator"
    )
    issues_encountered = models.TextField(
        blank=True
    )
    
    class Meta:
        db_table = "operation_executions"
        ordering = ['work_order', 'sequence']
        unique_together = ['work_order', 'sequence']
    
    def __str__(self):
        return f"{self.work_order.wo_number} - Op {self.sequence}"
    
    def calculate_cost(self):
        """Calculate actual labor cost"""
        if self.actual_hours and self.route_operation:
            self.labor_cost = self.actual_hours * self.route_operation.labor_rate
            self.save()
```

**WorkOrderCost** (Cost Tracking)

```python
# apps/workorders/models.py - ADD NEW MODEL

class WorkOrderCost(models.Model):
    """
    Aggregate cost tracking for work order.
    Real-time cost accumulation as work progresses.
    """
    
    work_order = models.OneToOneField(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="cost_summary",
        primary_key=True
    )
    
    # Labor costs
    estimated_labor_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    actual_labor_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    labor_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Material costs
    estimated_material_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    actual_material_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Overhead
    overhead_rate_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15.00,
        help_text="Overhead percentage to apply"
    )
    overhead_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # External costs
    subcontractor_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Cost of outsourced operations"
    )
    
    # Total
    total_estimated_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_actual_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Variance
    cost_variance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Actual - Estimated (negative = under budget)"
    )
    variance_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    # Last updated
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "work_order_costs"
        verbose_name = "Work Order Cost"
        verbose_name_plural = "Work Order Costs"
    
    def __str__(self):
        return f"Costs for {self.work_order.wo_number}"
    
    def recalculate(self):
        """Recalculate all costs from related records"""
        
        # Labor from operations
        ops = self.work_order.operation_executions.all()
        self.actual_labor_hours = sum(op.actual_hours or 0 for op in ops)
        self.labor_cost = sum(op.labor_cost for op in ops)
        
        # Materials from BOM
        if hasattr(self.work_order, 'repair_bom'):
            for bom in self.work_order.repair_bom.all():
                self.actual_material_cost += bom.actual_material_cost
        
        # Overhead
        direct_costs = self.labor_cost + self.actual_material_cost
        self.overhead_cost = direct_costs * (self.overhead_rate_percent / 100)
        
        # Total actual
        self.total_actual_cost = (
            self.labor_cost +
            self.actual_material_cost +
            self.overhead_cost +
            self.subcontractor_cost
        )
        
        # Variance
        self.cost_variance = self.total_actual_cost - self.total_estimated_cost
        if self.total_estimated_cost > 0:
            self.variance_percent = (
                (self.cost_variance / self.total_estimated_cost) * 100
            )
        
        self.save()
        
        # Update work order
        self.work_order.actual_cost = self.total_actual_cost
        self.work_order.save()
```

---

### ✅ CHECKPOINT 4: Generate Migrations for Process Models

```bash
python manage.py makemigrations workorders
python manage.py migrate workorders

# Test process routing
python manage.py shell
```

```python
from apps.workorders.models import *
from decimal import Decimal

# Create a standard route for PDC redress
route = ProcessRoute.objects.create(
    route_number="RT-PDC-REDRESS-001",
    name="Standard PDC Redress",
    repair_type="REDRESS",
    bit_types="FC",
    estimated_duration_hours=Decimal('8.0')
)

# Add operations
op1 = ProcessRouteOperation.objects.create(
    route=route,
    sequence=10,
    operation_code="INSPECT",
    operation_name="Initial Inspection",
    standard_hours=Decimal('0.5'),
    labor_rate=Decimal('50.00'),
    requires_qc=True
)

op2 = ProcessRouteOperation.objects.create(
    route=route,
    sequence=20,
    operation_code="CUTTERS",
    operation_name="Redress Cutters",
    standard_hours=Decimal('4.0'),
    labor_rate=Decimal('75.00'),
    requires_qc=True
)

op3 = ProcessRouteOperation.objects.create(
    route=route,
    sequence=30,
    operation_code="BEARINGS",
    operation_name="Check/Replace Bearings",
    standard_hours=Decimal('2.0'),
    labor_rate=Decimal('60.00'),
    requires_qc=True
)

op4 = ProcessRouteOperation.objects.create(
    route=route,
    sequence=40,
    operation_code="FINAL-QC",
    operation_name="Final QC Inspection",
    standard_hours=Decimal('1.0'),
    labor_rate=Decimal('50.00'),
    requires_qc=True
)

print(f"✅ Created route with {route.operations.count()} operations")

# Create work order and operations
wo = WorkOrder.objects.first()
for op in route.operations.all():
    exec_op = OperationExecution.objects.create(
        work_order=wo,
        route_operation=op,
        sequence=op.sequence,
        status='PENDING'
    )
    print(f"✅ Created execution: {exec_op}")

# Create cost summary
cost = WorkOrderCost.objects.create(
    work_order=wo,
    estimated_labor_hours=route.estimated_duration_hours,
    total_estimated_cost=Decimal('5000.00')
)

print(f"✅ Cost summary: ${cost.total_estimated_cost}")
```

---

## 📊 DAYS 9-12: OPERATIONS MANAGEMENT MODELS

These apps already exist. We're adding Sprint 4-specific enhancements.

### Day 9: Inventory Enhancement

**Add to existing `apps/inventory/models.py`:**

```python
# Lot tracking for materials
class MaterialLot(models.Model):
    """Track material lots for traceability"""
    
    lot_number = models.CharField(max_length=50, unique=True)
    inventory_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="lots"
    )
    
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    received_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    
    # Vendor/PO reference
    vendor = models.ForeignKey(
        'supplychain.Vendor',
        on_delete=models.SET_NULL,
        null=True,
        related_name="material_lots"
    )
    purchase_order = models.CharField(max_length=50, blank=True)
    
    # Certifications
    cert_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Material certification/heat number"
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('QUARANTINE', 'Quarantine'),
            ('AVAILABLE', 'Available'),
            ('DEPLETED', 'Depleted'),
            ('EXPIRED', 'Expired'),
        ],
        default='AVAILABLE'
    )
    
    class Meta:
        db_table = "material_lots"
        ordering = ['-received_date']
    
    def __str__(self):
        return f"{self.lot_number} - {self.inventory_item.name}"


class MaterialConsumption(models.Model):
    """Track which lots were used on which work orders"""
    
    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.CASCADE,
        related_name="material_consumptions"
    )
    
    lot = models.ForeignKey(
        MaterialLot,
        on_delete=models.PROTECT,
        related_name="consumptions"
    )
    
    quantity_consumed = models.DecimalField(max_digits=10, decimal_places=3)
    consumed_at = models.DateTimeField(auto_now_add=True)
    consumed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    # Link to operation if applicable
    operation_execution = models.ForeignKey(
        'workorders.OperationExecution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="material_consumptions"
    )
    
    class Meta:
        db_table = "material_consumptions"
        ordering = ['-consumed_at']
    
    def __str__(self):
        return f"{self.lot.lot_number} → {self.work_order.wo_number}"
```

**Generate migrations:**
```bash
python manage.py makemigrations inventory
python manage.py migrate inventory
```

---

### Day 10: Maintenance Enhancement

**Add to existing `apps/maintenance/models.py`:**

```python
# Equipment calibration tracking
class EquipmentCalibration(models.Model):
    """Track calibration of inspection equipment"""
    
    equipment = models.ForeignKey(
        'Equipment',
        on_delete=models.CASCADE,
        related_name="calibrations"
    )
    
    calibration_date = models.DateField()
    due_date = models.DateField(
        help_text="Next calibration due date"
    )
    
    # Calibration details
    performed_by = models.CharField(
        max_length=200,
        help_text="Calibration service provider"
    )
    cert_number = models.CharField(
        max_length=100,
        help_text="Calibration certificate number"
    )
    
    # Results
    passed = models.BooleanField(default=True)
    results_notes = models.TextField(blank=True)
    
    # Document
    certificate = models.FileField(
        upload_to="calibration_certs/",
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = "equipment_calibrations"
        ordering = ['-calibration_date']
    
    def __str__(self):
        return f"{self.equipment} - {self.calibration_date}"
    
    @property
    def is_due(self):
        from django.utils import timezone
        return timezone.now().date() >= self.due_date
```

**Generate migrations:**
```bash
python manage.py makemigrations maintenance
python manage.py migrate maintenance
```

---

### Days 11-12: Planning & Dispatch

These apps already have good models. Just verify they integrate properly with work orders.

**Verify relationships exist:**
```python
# python manage.py shell

from apps.planning.models import ProductionPlan, ProductionSchedule
from apps.dispatch.models import Shipment
from apps.workorders.models import WorkOrder

# Test: Can link work order to plan?
wo = WorkOrder.objects.first()
plan = ProductionPlan.objects.first()

# Test: Can create shipment for completed WO?
shipment = Shipment.objects.create(...)

print("✅ Integrations verified")
```

---

## 📊 DAYS 13-14: VALIDATION & DOCUMENTATION

### Day 13: Comprehensive Model Validation

**Run All Migrations:**
```bash
# Make sure all migrations are applied
python manage.py showmigrations

# Should show all [X] (applied)
```

**Validate Database:**
```bash
# Connect to database
python manage.py dbshell

# Count tables
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public';
# Should show ~131 tables

# Check key tables exist
\dt workorders_*
\dt quality_*
\dt inventory_*
```

**Test Key Workflows:**

```python
# python manage.py shell

from apps.workorders.models import *
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone

User = get_user_model()
user = User.objects.first()

print("=== TESTING SPRINT 4 MODELS ===\n")

# 1. Create Aramco drill bit
print("1. Creating Aramco drill bit...")
bit = DrillBit.objects.create(
    serial_number="ABC-001",
    base_serial_number="ABC-001",
    current_display_serial="ABC-001",
    bit_type="FC",
    size=Decimal("8.500"),
    is_aramco_contract=True,
    revision_number=0,
    physical_status="IN_STOCK",
    accounting_status="ACTIVE",
    original_cost=Decimal("25000.00")
)
print(f"   ✅ Created: {bit}\n")

# 2. Create evaluation
print("2. Creating repair evaluation...")
evaluation = RepairEvaluation.objects.create(
    evaluation_number="EVAL-2024-001",
    drill_bit=bit,
    damage_assessment="Cutters worn, bearings OK",
    estimated_repair_cost=Decimal("6500.00"),
    repair_recommended=True,
    requires_approval=True,
    evaluated_by=user
)
print(f"   ✅ Created: {evaluation}\n")

# 3. Create work order
print("3. Creating work order...")
wo = WorkOrder.objects.create(
    wo_number="WO-2024-001",
    wo_type="FC_REPAIR",
    drill_bit=bit,
    repair_type="REDRESS",
    estimated_cost=Decimal("6500.00"),
    created_by=user
)
evaluation.resulting_work_order = wo
evaluation.save()
print(f"   ✅ Created: {wo}\n")

# 4. Create process route and operations
print("4. Creating process route...")
route = ProcessRoute.objects.create(
    route_number="RT-001",
    name="PDC Redress",
    repair_type="REDRESS"
)

op = ProcessRouteOperation.objects.create(
    route=route,
    sequence=10,
    operation_code="REDRESS",
    operation_name="Redress Cutters",
    standard_hours=Decimal("4.0"),
    labor_rate=Decimal("75.00")
)

execution = OperationExecution.objects.create(
    work_order=wo,
    route_operation=op,
    sequence=10,
    operator=user,
    start_time=timezone.now()
)
print(f"   ✅ Created: {execution}\n")

# 5. Create cost summary
print("5. Creating cost summary...")
cost = WorkOrderCost.objects.create(
    work_order=wo,
    estimated_labor_hours=Decimal("4.0"),
    total_estimated_cost=Decimal("6500.00")
)
print(f"   ✅ Created: {cost}\n")

# 6. Create repair history
print("6. Creating repair history...")
history = BitRepairHistory.objects.create(
    drill_bit=bit,
    work_order=wo,
    repair_number=1,
    repair_date=timezone.now().date(),
    repair_type="REDRESS",
    work_performed="Redressed all cutters, lubricated bearings",
    labor_cost=Decimal("3000.00"),
    material_cost=Decimal("2500.00"),
    serial_before="ABC-001",
    serial_after="ABC-001-R1",
    technician=user
)
print(f"   ✅ Created: {history}")
print(f"   Total cost: ${history.total_cost}\n")

# 7. Test status transitions
print("7. Testing status transitions...")
log = StatusTransitionLog.objects.create(
    content_object=wo,
    from_status="DRAFT",
    to_status="RELEASED",
    changed_by=user,
    reason="Approved for repair"
)
print(f"   ✅ Created: {log}\n")

# 8. Test salvage item
print("8. Creating salvage item...")
salvage = SalvageItem.objects.create(
    salvage_number="SALV-001",
    drill_bit=bit,
    salvage_type="BODY",
    description="8.5\" PDC bit body",
    condition_rating="Good",
    salvage_date=timezone.now().date(),
    salvaged_by=user
)
print(f"   ✅ Created: {salvage}\n")

# 9. Verify relationships
print("9. Verifying relationships...")
print(f"   Bit work orders: {bit.work_orders.count()}")
print(f"   Bit repair history: {bit.repair_history.count()}")
print(f"   Bit evaluations: {bit.repair_evaluations.count()}")
print(f"   Bit salvage items: {bit.salvaged_items.count()}")
print(f"   WO operations: {wo.operation_executions.count()}")
print(f"   WO has cost summary: {hasattr(wo, 'cost_summary')}")
print()

print("=== ALL TESTS PASSED ✅ ===")
print("Sprint 4 models are working correctly!")
```

**Expected Output:**
```
=== TESTING SPRINT 4 MODELS ===

1. Creating Aramco drill bit...
   ✅ Created: ABC-001 (FC)

2. Creating repair evaluation...
   ✅ Created: EVAL-2024-001 - ABC-001

3. Creating work order...
   ✅ Created: WO-2024-001

... (all tests pass)

=== ALL TESTS PASSED ✅ ===
Sprint 4 models are working correctly!
```

---

### Day 14: Documentation

**Create Model Documentation:**

```bash
# Create docs/SPRINT4_MODELS.md
```

Document structure:
```markdown
# Sprint 4 Models Documentation

## Core Models

### DrillBit
- **Purpose:** Track individual drill bits through lifecycle
- **Key Fields:** serial_number, revision_number, is_aramco_contract
- **Relationships:** work_orders, repair_history, evaluations
- **Special Behavior:** Serial number increments on Aramco repairs

### WorkOrder
- **Purpose:** Manage repair work orders
- **Key Fields:** wo_number, repair_type, disposition
- **Relationships:** drill_bit, operations, costs
- **Special Behavior:** Approval required if cost > threshold

... (document all 39 models)
```

---

## ✅ SPRINT 4 COMPLETION CHECKLIST

### Models (39 total)

**Core Repair Models:**
- [ ] DrillBit (enhanced with Sprint 4 fields)
- [ ] WorkOrder (enhanced with repair fields)
- [ ] StatusTransitionLog
- [ ] BitRepairHistory
- [ ] SalvageItem

**Evaluation & Approval:**
- [ ] RepairEvaluation
- [ ] RepairApprovalAuthority

**BOM & Materials:**
- [ ] RepairBOM
- [ ] RepairBOMLine

**Process Execution:**
- [ ] ProcessRoute
- [ ] ProcessRouteOperation
- [ ] OperationExecution

**Cost Tracking:**
- [ ] WorkOrderCost

**Inventory Enhancement:**
- [ ] MaterialLot
- [ ] MaterialConsumption

**Maintenance Enhancement:**
- [ ] EquipmentCalibration

**Quality Models:** (existing, verified)
- [ ] NCR
- [ ] Inspection
- [ ] QualityCheckpoint
- [ ] FinalQCInspection

**Planning/Dispatch:** (existing, verified integration)

---

### Migrations

- [ ] All models have migration files
- [ ] All migrations applied successfully
- [ ] Database tables created
- [ ] No migration errors
- [ ] Circular dependencies resolved

---

### Validation

- [ ] Can create all model instances
- [ ] All relationships work
- [ ] ForeignKey reverse relations work
- [ ] Calculated fields work (e.g., total_cost)
- [ ] Status transitions work
- [ ] Approval workflow works
- [ ] Complete workflow test passes

---

### Documentation

- [ ] Model documentation complete
- [ ] Field descriptions clear
- [ ] Relationships documented
- [ ] Special behaviors noted
- [ ] ISO 9001 / API Q1 compliance noted

---

## 🎯 NEXT STEPS AFTER SPRINT 4

**Immediate:**
- ✅ Sprint 4 models validated and working
- ✅ Database schema complete
- ✅ Ready for Sprint 5

**Sprint 5-7:**
- Continue with remaining features
- Generate migrations at end of each sprint
- Keep database in sync

**After All Sprints (Final Phase):**
- Write comprehensive tests (20% coverage)
- Add permission checks system-wide
- Security hardening
- Performance optimization
- Production deployment

---

## 📞 NOTES FOR CLAUDE CODE

### When Implementing:

1. **Start with Day 1-2:** Review existing models, add Sprint 4 fields
2. **Generate migrations after each day:** Don't wait until end
3. **Test as you go:** Run validation scripts after each checkpoint
4. **Fix issues immediately:** Don't accumulate problems
5. **Document as you build:** Add docstrings and comments

### Common Issues to Watch:

**Circular Dependencies:**
- workorders ↔ sales (use string references)
- quality ↔ workorders (use string references)
- Already handled in code with "app.Model" syntax

**Missing Imports:**
```python
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
```

**Related Names:**
All ForeignKeys have explicit `related_name` - this is intentional!

---

## 🎉 SUCCESS CRITERIA

**Sprint 4 is complete when:**

1. ✅ All 39 models exist in database
2. ✅ All migrations applied without errors
3. ✅ Workflow validation script passes
4. ✅ Can create drill bit, evaluate, repair, complete
5. ✅ Cost tracking works
6. ✅ Approval workflow functions
7. ✅ Serial number increment works for Aramco bits
8. ✅ Salvage tracking works
9. ✅ All relationships verified
10. ✅ Documentation complete

**Then proceed to Sprint 5!**

---

**END OF SPRINT 4 IMPLEMENTATION GUIDE**

**Version:** 2.0 - Updated with real code review findings  
**Date:** December 5, 2024  
**Approach:** Pragmatic - Models + Migrations, Tests/Permissions deferred  
**Status:** Ready for implementation by Claude Code  

**Good luck! 🚀**
