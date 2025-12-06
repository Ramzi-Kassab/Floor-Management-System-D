# ✅ SPRINT 4 EXECUTION CHECKLIST
## For Claude Code Implementation

**Approach:** Pragmatic Option A  
**Timeline:** 11 days  
**Tests/Permissions:** Deferred to final phase  

---

## 📋 QUICK START

### Before You Begin:

- [ ] Read SPRINT4_IMPLEMENTATION_UPDATED.md
- [ ] Have project open in editor
- [ ] Have Django shell ready
- [ ] Have backup of current code

---

## DAY 1-2: DRILL BIT & WORK ORDER ✅

### Add Fields to Existing Models:

**File:** `apps/workorders/models.py`

**DrillBit - Add these fields:**
- [ ] base_serial_number
- [ ] current_display_serial  
- [ ] revision_number
- [ ] is_aramco_contract
- [ ] physical_status
- [ ] accounting_status
- [ ] total_repairs
- [ ] last_repair_date
- [ ] last_repair_type
- [ ] original_cost
- [ ] total_repair_cost
- [ ] current_book_value

**WorkOrder - Add these fields:**
- [ ] repair_type
- [ ] requires_approval
- [ ] approved_by (FK)
- [ ] approved_at
- [ ] estimated_cost
- [ ] actual_cost
- [ ] disposition
- [ ] disposition_notes

**Generate Migrations:**
```bash
python manage.py makemigrations workorders
python manage.py migrate workorders
```

**Test:**
```python
python manage.py shell
from apps.workorders.models import DrillBit
bit = DrillBit.objects.create(
    serial_number="TEST-001",
    base_serial_number="TEST-001",
    bit_type="FC",
    size=8.5,
    is_aramco_contract=True
)
print(f"✅ {bit}")
```

- [ ] Migrations generated
- [ ] Migrations applied
- [ ] Test passed

---

## DAY 3-4: REPAIR WORKFLOW MODELS ✅

**File:** `apps/workorders/models.py`

**Add New Models:**

- [ ] StatusTransitionLog (audit trail)
  - content_type, object_id, GenericForeignKey
  - from_status, to_status
  - changed_by, changed_at, reason

- [ ] BitRepairHistory (repair records)
  - drill_bit FK, work_order FK
  - repair_number, repair_date, repair_type
  - work_performed, parts_replaced
  - labor_cost, material_cost, total_cost
  - condition_before, condition_after
  - serial_before, serial_after

- [ ] SalvageItem (salvaged parts tracking)
  - salvage_number, drill_bit FK
  - salvage_type, description, status
  - condition_rating, reuse_potential
  - warehouse FK, storage_location
  - dates, reuse tracking, value tracking
  - photos

**Generate Migrations:**
```bash
python manage.py makemigrations workorders
python manage.py migrate workorders
```

**Test:**
```python
python manage.py shell
from apps.workorders.models import *
bit = DrillBit.objects.first()

# Test StatusTransitionLog
log = StatusTransitionLog.objects.create(
    content_object=bit,
    from_status='IN_STOCK',
    to_status='IN_REPAIR'
)

# Test BitRepairHistory  
history = BitRepairHistory.objects.create(
    drill_bit=bit,
    repair_number=1,
    repair_date='2024-12-01',
    repair_type='REDRESS',
    labor_cost=2000,
    material_cost=1500
)
print(f"✅ Total: ${history.total_cost}")

# Test SalvageItem
salvage = SalvageItem.objects.create(
    salvage_number='SALV-001',
    drill_bit=bit,
    salvage_type='BODY',
    description='8.5" PDC body',
    salvage_date='2024-12-01'
)
```

- [ ] 3 new models created
- [ ] Migrations generated
- [ ] Migrations applied
- [ ] Tests passed

---

## DAY 5-6: EVALUATION & APPROVAL ✅

**File:** `apps/workorders/models.py`

**Add New Models:**

- [ ] RepairEvaluation
  - evaluation_number, drill_bit FK
  - IADC grading fields
  - damage_assessment, recommended_repair
  - estimated_repair_cost
  - status, repair_recommended
  - requires_approval, approval_authority FK
  - approved_by FK, approved_at
  - evaluated_by FK, evaluated_at
  - resulting_work_order OneToOne

- [ ] RepairApprovalAuthority
  - name, min_amount, max_amount
  - authorized_users M2M
  - requires_justification, active
  - can_approve() method

- [ ] RepairBOM
  - work_order FK, master_bom FK
  - status, costs
  - approved_by FK, approved_at

- [ ] RepairBOMLine
  - repair_bom FK, line_number
  - inventory_item FK
  - quantities (required, issued, consumed)
  - unit_cost, total_cost

**Generate Migrations:**
```bash
python manage.py makemigrations workorders
python manage.py migrate workorders
```

**Test:**
```python
python manage.py shell
from apps.workorders.models import *
from decimal import Decimal

# Create authority
auth = RepairApprovalAuthority.objects.create(
    name="Operations Manager",
    min_amount=Decimal('5000'),
    max_amount=Decimal('25000')
)

# Test evaluation
bit = DrillBit.objects.first()
evaluation = RepairEvaluation.objects.create(
    evaluation_number="EVAL-001",
    drill_bit=bit,
    damage_assessment="Cutters worn",
    estimated_repair_cost=Decimal('7500.00'),
    repair_recommended=True,
    requires_approval=True,
    approval_authority=auth
)

print(f"✅ Can approve: {auth.can_approve(7500)}")
```

- [ ] 4 new models created
- [ ] Migrations generated
- [ ] Migrations applied
- [ ] Approval logic tested

---

## DAY 7-8: PROCESS & COST MODELS ✅

**File:** `apps/workorders/models.py`

**Add New Models:**

- [ ] ProcessRoute
  - route_number, name
  - repair_type, bit_types
  - active, version
  - estimated_duration_hours, estimated_labor_cost

- [ ] ProcessRouteOperation
  - route FK, sequence
  - operation_code, operation_name
  - work_center, standard_hours, labor_rate
  - requires_qc, qc_checklist
  - safety_requirements

- [ ] OperationExecution
  - work_order FK, route_operation FK
  - sequence, status
  - operator FK, start_time, end_time, actual_hours
  - labor_cost
  - qc_performed, qc_passed, qc_by FK
  - operator_notes, issues_encountered

- [ ] WorkOrderCost
  - work_order OneToOne (primary_key)
  - estimated_labor_hours, actual_labor_hours, labor_cost
  - estimated_material_cost, actual_material_cost
  - overhead_rate_percent, overhead_cost
  - subcontractor_cost
  - totals, variance
  - recalculate() method

**Generate Migrations:**
```bash
python manage.py makemigrations workorders
python manage.py migrate workorders
```

**Test:**
```python
python manage.py shell
from apps.workorders.models import *
from decimal import Decimal

# Create route
route = ProcessRoute.objects.create(
    route_number="RT-001",
    name="PDC Redress",
    repair_type="REDRESS"
)

# Create operation
op = ProcessRouteOperation.objects.create(
    route=route,
    sequence=10,
    operation_code="REDRESS",
    operation_name="Redress Cutters",
    standard_hours=Decimal('4.0'),
    labor_rate=Decimal('75.00')
)

# Create execution
wo = WorkOrder.objects.first()
execution = OperationExecution.objects.create(
    work_order=wo,
    route_operation=op,
    sequence=10,
    status='PENDING'
)

# Create cost summary
cost = WorkOrderCost.objects.create(
    work_order=wo,
    estimated_labor_hours=Decimal('4.0'),
    total_estimated_cost=Decimal('5000.00')
)

print(f"✅ Route: {route.operations.count()} operations")
print(f"✅ Cost: ${cost.total_estimated_cost}")
```

- [ ] 4 new models created
- [ ] Migrations generated
- [ ] Migrations applied
- [ ] Process flow tested

---

## DAY 9: INVENTORY ENHANCEMENT ✅

**File:** `apps/inventory/models.py`

**Add New Models:**

- [ ] MaterialLot
  - lot_number, inventory_item FK
  - quantity, received_date, expiry_date
  - vendor FK, purchase_order
  - cert_number, status

- [ ] MaterialConsumption  
  - work_order FK, lot FK
  - quantity_consumed, consumed_at, consumed_by FK
  - operation_execution FK

**Generate Migrations:**
```bash
python manage.py makemigrations inventory
python manage.py migrate inventory
```

**Test:**
```python
python manage.py shell
from apps.inventory.models import *

item = InventoryItem.objects.first()
lot = MaterialLot.objects.create(
    lot_number="LOT-001",
    inventory_item=item,
    quantity=100,
    received_date='2024-12-01',
    status='AVAILABLE'
)

wo = WorkOrder.objects.first()
consumption = MaterialConsumption.objects.create(
    work_order=wo,
    lot=lot,
    quantity_consumed=10
)

print(f"✅ Lot: {lot}")
print(f"✅ Consumption: {consumption}")
```

- [ ] 2 new models created
- [ ] Migrations generated
- [ ] Migrations applied
- [ ] Lot tracking tested

---

## DAY 10: MAINTENANCE ENHANCEMENT ✅

**File:** `apps/maintenance/models.py`

**Add New Model:**

- [ ] EquipmentCalibration
  - equipment FK
  - calibration_date, due_date
  - performed_by, cert_number
  - passed, results_notes
  - certificate (file)
  - is_due property

**Generate Migrations:**
```bash
python manage.py makemigrations maintenance
python manage.py migrate maintenance
```

**Test:**
```python
python manage.py shell
from apps.maintenance.models import *

equipment = Equipment.objects.first()
cal = EquipmentCalibration.objects.create(
    equipment=equipment,
    calibration_date='2024-12-01',
    due_date='2025-12-01',
    performed_by='XYZ Calibration',
    cert_number='CAL-2024-001',
    passed=True
)

print(f"✅ Calibration: {cal}")
print(f"   Due: {cal.is_due}")
```

- [ ] 1 new model created
- [ ] Migrations generated
- [ ] Migrations applied
- [ ] Calibration tracking tested

---

## DAY 11-12: PLANNING & DISPATCH ✅

**No new models needed** - existing apps are sufficient.

**Verify Integration:**
```python
python manage.py shell
from apps.planning.models import *
from apps.dispatch.models import *
from apps.workorders.models import WorkOrder

# Verify work orders can link to plans
wo = WorkOrder.objects.first()
plan = ProductionPlan.objects.first()

# Verify work orders can link to shipments
shipment = Shipment.objects.first()

print("✅ Planning integration verified")
print("✅ Dispatch integration verified")
```

- [ ] Planning integration verified
- [ ] Dispatch integration verified

---

## DAY 13: VALIDATION ✅

### All Migrations Applied:

```bash
python manage.py showmigrations
```

- [ ] All migrations show [X]

### Database Verification:

```bash
python manage.py dbshell
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
\dt workorders_*
```

- [ ] ~131 tables exist
- [ ] All workorders tables present

### Workflow Test:

```python
# Run the comprehensive validation script from the guide
python manage.py shell < test_sprint4.py
```

- [ ] All workflow tests pass
- [ ] Relationships work
- [ ] Calculations correct

---

## DAY 14: DOCUMENTATION ✅

**Create/Update:**

- [ ] `docs/SPRINT4_MODELS.md` - Model documentation
- [ ] `docs/WORKFLOWS.md` - Workflow documentation  
- [ ] `README.md` - Updated with Sprint 4 info

**Document Each Model:**
- Purpose
- Key fields
- Relationships
- Special behaviors
- ISO 9001 / API Q1 compliance notes

---

## 🎯 FINAL VALIDATION

### Model Count:

- [ ] 39 total models documented
- [ ] All models in database
- [ ] All relationships work

### Functionality:

- [ ] Can create Aramco drill bit
- [ ] Serial increments on repair (R1, R2, R3)
- [ ] Approval workflow functions
- [ ] Cost tracking works
- [ ] Status transitions logged
- [ ] Repair history tracked
- [ ] Salvage items tracked
- [ ] Process routes executable
- [ ] Material lots traceable

### Quality:

- [ ] All ForeignKeys have related_name
- [ ] All fields have help_text
- [ ] All models have __str__
- [ ] All models have proper indexes
- [ ] All models have Meta class

---

## ✅ SPRINT 4 COMPLETE WHEN:

1. ✅ All checkboxes above checked
2. ✅ Workflow validation script passes
3. ✅ No migration errors
4. ✅ Documentation complete
5. ✅ Ready for Sprint 5

---

## 🚫 DEFERRED TO LATER:

**DO NOT implement yet:**
- ❌ Comprehensive tests (Phase: Final Testing)
- ❌ Permission checks (Phase: Security Hardening)
- ❌ Forms (Can do basic admin forms)
- ❌ Views (Can do basic admin views)
- ❌ Templates (Can do basic admin templates)

**Focus on:**
- ✅ Models correct and working
- ✅ Migrations applied
- ✅ Database schema complete
- ✅ Basic validation passing

---

## 📞 IF ISSUES OCCUR:

**Circular Dependencies:**
- Use string references: `"sales.Customer"` not `Customer`
- Already handled in code

**Migration Errors:**
```bash
# Reset if needed
python manage.py migrate workorders zero
# Then reapply
python manage.py migrate workorders
```

**Import Errors:**
```python
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
```

---

**GOOD LUCK! 🚀**

**Check off each box as you complete it.**  
**Test after each day.**  
**Fix issues immediately.**  
**Don't accumulate problems.**
