# 🎯 PHASE 1: SPRINT 5 DEPENDENCIES
## Fix sales, drss, assets Apps (3 hours)

**Priority:** CRITICAL for Sprint 5  
**Timeline:** 3 hours  
**Apps:** sales, drss, assets  
**ForeignKeys:** ~23 total  

---

## 📊 PHASE 1 OVERVIEW

### Why These Apps First:

**Sprint 5 (Field Services) Will Need:**
- sales → workorders (customer field service requests)
- drss → workorders (drill string tracking in field)
- assets → workorders (equipment used in field)
- dispatch → workorders (logistics to field)

**Without related_name fixed:**
- ❌ Circular dependency issues
- ❌ Confusing reverse relationships
- ❌ Integration problems
- ❌ Mid-sprint debugging nightmares

**With related_name fixed:**
- ✅ Clean integration
- ✅ Clear relationships
- ✅ Easy debugging
- ✅ Smooth Sprint 5

---

## 🏢 APP 1: SALES (1 hour)

### Location:
```
apps/sales/models.py
```

### Models in This App:
- Customer
- Quote
- SalesOrder
- OrderLine
- ServiceContract
- FieldServiceRequest
- CustomerContact
- Warehouse (may have FKs)

### Estimated ForeignKeys to Fix: ~10

---

### Step-by-Step Instructions:

**1. Open the File**
```bash
cd /path/to/your/project
code apps/sales/models.py
# or
vim apps/sales/models.py
```

**2. Find Models with ForeignKeys**

Look for patterns like:
```python
class SomeModel(models.Model):
    other_model = models.ForeignKey(
        'OtherModel',
        on_delete=models.PROTECT
        # No related_name here ❌
    )
```

---

### Common ForeignKeys in Sales App:

**Customer Model:**
```python
class Customer(models.Model):
    # Likely has:
    # - assigned_to (User) → needs related_name='managed_customers'
    # - created_by (User) → needs related_name='created_customers'
    # - company (Organization) → needs related_name='customers'
    
    # Find and add related_name to each
```

**Quote Model:**
```python
class Quote(models.Model):
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.PROTECT,
        related_name='quotes'  # ✅ ADD THIS
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_quotes'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys without related_name
```

**SalesOrder Model:**
```python
class SalesOrder(models.Model):
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.PROTECT,
        related_name='sales_orders'  # ✅ ADD THIS
    )
    
    quote = models.ForeignKey(
        'Quote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders'  # ✅ ADD THIS
    )
    
    warehouse = models.ForeignKey(
        'Warehouse',
        on_delete=models.PROTECT,
        related_name='sales_orders'  # ✅ ADD THIS
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sales_orders'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys without related_name
```

**OrderLine Model:**
```python
class OrderLine(models.Model):
    order = models.ForeignKey(
        'SalesOrder',
        on_delete=models.CASCADE,
        related_name='lines'  # ✅ ADD THIS (or 'order_lines')
    )
    
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='order_lines'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys without related_name
```

**ServiceContract Model:**
```python
class ServiceContract(models.Model):
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.PROTECT,
        related_name='service_contracts'  # ✅ ADD THIS
    )
    
    sales_order = models.ForeignKey(
        'SalesOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_contracts'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys without related_name
```

**FieldServiceRequest Model:**
```python
class FieldServiceRequest(models.Model):
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.PROTECT,
        related_name='field_service_requests'  # ✅ ADD THIS
    )
    
    service_contract = models.ForeignKey(
        'ServiceContract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='field_requests'  # ✅ ADD THIS
    )
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_field_requests'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys without related_name
```

---

### 3. Save the File

After adding all related_name attributes, save the file.

---

### 4. Generate Migrations

```bash
python manage.py makemigrations sales
```

**Expected Output:**
```
Migrations for 'sales':
  apps/sales/migrations/00XX_add_related_names.py
    - Alter field customer on salesorder
    - Alter field created_by on quote
    - ... (all the changes)
```

---

### 5. Apply Migrations

```bash
python manage.py migrate sales
```

**Expected Output:**
```
Running migrations:
  Applying sales.00XX_add_related_names... OK
```

---

### 6. Validate

```bash
python manage.py check
```

**Expected Output:**
```
System check identified no issues (0 silenced).
```

---

### 7. Test in Shell

```bash
python manage.py shell
```

```python
from apps.sales.models import Customer, Quote, SalesOrder

# Test 1: Get a customer
customer = Customer.objects.first()

# Test 2: Access related quotes (should work now)
quotes = customer.quotes.all()
print(f"✅ Customer has {quotes.count()} quotes")

# Test 3: Access related sales orders
orders = customer.sales_orders.all()
print(f"✅ Customer has {orders.count()} sales orders")

# Test 4: Access field service requests
requests = customer.field_service_requests.all()
print(f"✅ Customer has {requests.count()} field requests")

# If all work, sales app is fixed! ✅
exit()
```

---

### ✅ Sales App Complete When:
- [ ] All ForeignKeys have related_name
- [ ] Migrations generated
- [ ] Migrations applied
- [ ] `python manage.py check` passes
- [ ] Shell tests pass
- [ ] No errors

**Time Spent:** ~1 hour  
**Next:** drss app

---

## 🔧 APP 2: DRSS (1 hour)

### Location:
```
apps/drss/models.py
```

### What is DRSS:
Drill String Running Service - tracks drill strings used in the field

### Models in This App:
- DrillString
- DrillStringComponent
- DrillStringRun
- RunSheet
- TorqueSheet
- DailyReport
- etc.

### Estimated ForeignKeys to Fix: ~8

---

### Step-by-Step Instructions:

**1. Open the File**
```bash
code apps/drss/models.py
```

**2. Find and Fix ForeignKeys**

**DrillString Model:**
```python
class DrillString(models.Model):
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.PROTECT,
        related_name='drill_strings'  # ✅ ADD THIS
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_drill_strings'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**DrillStringComponent Model:**
```python
class DrillStringComponent(models.Model):
    drill_string = models.ForeignKey(
        'DrillString',
        on_delete=models.CASCADE,
        related_name='components'  # ✅ ADD THIS
    )
    
    drill_bit = models.ForeignKey(
        'workorders.DrillBit',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='drss_components'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**DrillStringRun Model:**
```python
class DrillStringRun(models.Model):
    drill_string = models.ForeignKey(
        'DrillString',
        on_delete=models.CASCADE,
        related_name='runs'  # ✅ ADD THIS
    )
    
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.PROTECT,
        related_name='drill_string_runs'  # ✅ ADD THIS
    )
    
    rig = models.ForeignKey(
        'Rig',  # if Rig model exists
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='drill_string_runs'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**RunSheet Model:**
```python
class RunSheet(models.Model):
    drill_string_run = models.ForeignKey(
        'DrillStringRun',
        on_delete=models.CASCADE,
        related_name='run_sheets'  # ✅ ADD THIS
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_run_sheets'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**TorqueSheet Model:**
```python
class TorqueSheet(models.Model):
    drill_string_run = models.ForeignKey(
        'DrillStringRun',
        on_delete=models.CASCADE,
        related_name='torque_sheets'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**DailyReport Model:**
```python
class DailyReport(models.Model):
    drill_string_run = models.ForeignKey(
        'DrillStringRun',
        on_delete=models.CASCADE,
        related_name='daily_reports'  # ✅ ADD THIS
    )
    
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_daily_reports'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

---

### 3. Save the File

---

### 4. Generate Migrations

```bash
python manage.py makemigrations drss
```

---

### 5. Apply Migrations

```bash
python manage.py migrate drss
```

---

### 6. Validate

```bash
python manage.py check
```

---

### 7. Test in Shell

```bash
python manage.py shell
```

```python
from apps.drss.models import DrillString, DrillStringRun, RunSheet

# Test drill string relationships
drill_string = DrillString.objects.first()
if drill_string:
    components = drill_string.components.all()
    runs = drill_string.runs.all()
    print(f"✅ DrillString has {components.count()} components")
    print(f"✅ DrillString has {runs.count()} runs")

# Test drill string run relationships
run = DrillStringRun.objects.first()
if run:
    sheets = run.run_sheets.all()
    torque_sheets = run.torque_sheets.all()
    reports = run.daily_reports.all()
    print(f"✅ DrillStringRun has {sheets.count()} run sheets")
    print(f"✅ DrillStringRun has {torque_sheets.count()} torque sheets")
    print(f"✅ DrillStringRun has {reports.count()} daily reports")

exit()
```

---

### ✅ DRSS App Complete When:
- [ ] All ForeignKeys have related_name
- [ ] Migrations generated and applied
- [ ] `python manage.py check` passes
- [ ] Shell tests pass

**Time Spent:** ~1 hour  
**Next:** assets app

---

## 🏭 APP 3: ASSETS (45 minutes)

### Location:
```
apps/assets/models.py
```

### Models in This App:
- Asset
- AssetCategory
- AssetMaintenance
- AssetLocation
- AssetAssignment
- etc.

### Estimated ForeignKeys to Fix: ~5

---

### Step-by-Step Instructions:

**1. Open the File**
```bash
code apps/assets/models.py
```

**2. Find and Fix ForeignKeys**

**Asset Model:**
```python
class Asset(models.Model):
    category = models.ForeignKey(
        'AssetCategory',
        on_delete=models.PROTECT,
        related_name='assets'  # ✅ ADD THIS
    )
    
    current_location = models.ForeignKey(
        'AssetLocation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_assets'  # ✅ ADD THIS
    )
    
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_assets'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**AssetMaintenance Model:**
```python
class AssetMaintenance(models.Model):
    asset = models.ForeignKey(
        'Asset',
        on_delete=models.CASCADE,
        related_name='maintenance_records'  # ✅ ADD THIS
    )
    
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='performed_maintenance'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**AssetAssignment Model:**
```python
class AssetAssignment(models.Model):
    asset = models.ForeignKey(
        'Asset',
        on_delete=models.CASCADE,
        related_name='assignments'  # ✅ ADD THIS
    )
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='asset_assignments'  # ✅ ADD THIS
    )
    
    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_assignments'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

---

### 3. Save the File

---

### 4. Generate Migrations

```bash
python manage.py makemigrations assets
```

---

### 5. Apply Migrations

```bash
python manage.py migrate assets
```

---

### 6. Validate

```bash
python manage.py check
```

---

### 7. Test in Shell

```bash
python manage.py shell
```

```python
from apps.assets.models import Asset, AssetMaintenance, AssetAssignment

# Test asset relationships
asset = Asset.objects.first()
if asset:
    maintenance = asset.maintenance_records.all()
    assignments = asset.assignments.all()
    print(f"✅ Asset has {maintenance.count()} maintenance records")
    print(f"✅ Asset has {assignments.count()} assignments")

exit()
```

---

### ✅ Assets App Complete When:
- [ ] All ForeignKeys have related_name
- [ ] Migrations generated and applied
- [ ] `python manage.py check` passes
- [ ] Shell tests pass

**Time Spent:** ~45 minutes

---

## ✅ PHASE 1 COMPLETION

### Final Phase 1 Validation:

**1. Check All Apps**
```bash
python manage.py check
```

**Expected:** No issues

---

**2. Test Key Relationships**

```bash
python manage.py shell
```

```python
from apps.sales.models import Customer
from apps.drss.models import DrillString
from apps.assets.models import Asset

# Test Sprint 5 critical relationships
customer = Customer.objects.first()
if customer:
    print(f"✅ Customer sales orders: {customer.sales_orders.count()}")
    print(f"✅ Customer drill strings: {customer.drill_strings.count()}")
    print(f"✅ Customer field requests: {customer.field_service_requests.count()}")

# Test drill string
drill_string = DrillString.objects.first()
if drill_string:
    print(f"✅ DrillString components: {drill_string.components.count()}")
    print(f"✅ DrillString runs: {drill_string.runs.count()}")

# Test asset
asset = Asset.objects.first()
if asset:
    print(f"✅ Asset assignments: {asset.assignments.count()}")

print("\n🎉 Phase 1 Complete!")
exit()
```

---

**3. Commit Changes**
```bash
git add apps/sales apps/drss apps/assets
git commit -m "fix: Add related_name to Sprint 5 dependencies (sales, drss, assets)"
git push
```

---

### ✅ Phase 1 Complete Checklist:

- [ ] sales app: All ForeignKeys fixed (~10)
- [ ] drss app: All ForeignKeys fixed (~8)
- [ ] assets app: All ForeignKeys fixed (~5)
- [ ] Total: ~23 ForeignKeys fixed
- [ ] All migrations generated and applied
- [ ] `python manage.py check` passes
- [ ] All shell tests pass
- [ ] Changes committed and pushed

---

## 🎉 PHASE 1 SUCCESS!

**Time Spent:** ~3 hours  
**ForeignKeys Fixed:** ~23  
**Impact:** Sprint 5 dependencies resolved  

**Next:** Take a 15-minute break, then proceed to Phase 2!

---

## 📄 NEXT DOCUMENT

**Open:** [PHASE2_SPRINT6_DEPS.md](computer:///mnt/user-data/outputs/PHASE2_SPRINT6_DEPS.md)

**Goal:** Fix supplychain, finance, execution apps (3 hours)

---

**Great work! 💪**

**END OF PHASE 1**
