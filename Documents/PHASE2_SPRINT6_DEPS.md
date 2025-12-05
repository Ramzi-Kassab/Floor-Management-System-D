# 🎯 PHASE 2: SPRINT 6 DEPENDENCIES
## Fix supplychain, finance, execution Apps (3 hours)

**Priority:** CRITICAL for Sprint 6  
**Timeline:** 3 hours  
**Apps:** supplychain, finance, execution  
**ForeignKeys:** ~21 total  

---

## 📊 PHASE 2 OVERVIEW

### Why These Apps Next:

**Sprint 6 (Supply Chain & Finance Integration) Will Need:**
- supplychain → inventory (vendor shipments, material tracking)
- supplychain → workorders (material procurement for repairs)
- finance → workorders (cost allocation, invoicing)
- finance → inventory (inventory valuation, COGS)
- execution → workorders (shop floor tracking, labor costs)

**Without related_name fixed:**
- ❌ Circular dependency issues
- ❌ Integration problems
- ❌ Cost tracking confusion
- ❌ Financial reporting errors

**With related_name fixed:**
- ✅ Clean integration
- ✅ Clear cost flows
- ✅ Accurate financial data
- ✅ Smooth Sprint 6

---

## 🏭 APP 4: SUPPLYCHAIN (1 hour)

### Location:
```
apps/supplychain/models.py
```

### Models in This App:
- Vendor
- PurchaseOrder
- PurchaseOrderLine
- Receipt
- ReceiptLine
- VendorQuote
- VendorInvoice
- etc.

### Estimated ForeignKeys to Fix: ~8

---

### Step-by-Step Instructions:

**1. Open the File**
```bash
code apps/supplychain/models.py
```

**2. Find and Fix ForeignKeys**

**Vendor Model:**
```python
class Vendor(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_vendors'  # ✅ ADD THIS
    )
    
    primary_contact = models.ForeignKey(
        'VendorContact',  # if exists
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_for_vendors'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**PurchaseOrder Model:**
```python
class PurchaseOrder(models.Model):
    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.PROTECT,
        related_name='purchase_orders'  # ✅ ADD THIS
    )
    
    warehouse = models.ForeignKey(
        'sales.Warehouse',
        on_delete=models.PROTECT,
        related_name='purchase_orders'  # ✅ ADD THIS
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_purchase_orders'  # ✅ ADD THIS
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchase_orders'  # ✅ ADD THIS
    )
    
    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**PurchaseOrderLine Model:**
```python
class PurchaseOrderLine(models.Model):
    purchase_order = models.ForeignKey(
        'PurchaseOrder',
        on_delete=models.CASCADE,
        related_name='lines'  # ✅ ADD THIS (or 'po_lines')
    )
    
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='purchase_order_lines'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**Receipt Model:**
```python
class Receipt(models.Model):
    purchase_order = models.ForeignKey(
        'PurchaseOrder',
        on_delete=models.PROTECT,
        related_name='receipts'  # ✅ ADD THIS
    )
    
    warehouse = models.ForeignKey(
        'sales.Warehouse',
        on_delete=models.PROTECT,
        related_name='receipts'  # ✅ ADD THIS
    )
    
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_shipments'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**ReceiptLine Model:**
```python
class ReceiptLine(models.Model):
    receipt = models.ForeignKey(
        'Receipt',
        on_delete=models.CASCADE,
        related_name='lines'  # ✅ ADD THIS (or 'receipt_lines')
    )
    
    po_line = models.ForeignKey(
        'PurchaseOrderLine',
        on_delete=models.PROTECT,
        related_name='receipts'  # ✅ ADD THIS (or 'receipt_lines')
    )
    
    lot = models.ForeignKey(
        'inventory.MaterialLot',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receipt_lines'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**VendorInvoice Model:**
```python
class VendorInvoice(models.Model):
    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.PROTECT,
        related_name='invoices'  # ✅ ADD THIS
    )
    
    purchase_order = models.ForeignKey(
        'PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

---

### 3. Save the File

---

### 4. Generate Migrations

```bash
python manage.py makemigrations supplychain
```

---

### 5. Apply Migrations

```bash
python manage.py migrate supplychain
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
from apps.supplychain.models import Vendor, PurchaseOrder, Receipt

# Test vendor relationships
vendor = Vendor.objects.first()
if vendor:
    pos = vendor.purchase_orders.all()
    invoices = vendor.invoices.all()
    print(f"✅ Vendor has {pos.count()} purchase orders")
    print(f"✅ Vendor has {invoices.count()} invoices")

# Test purchase order relationships
po = PurchaseOrder.objects.first()
if po:
    lines = po.lines.all()
    receipts = po.receipts.all()
    print(f"✅ PO has {lines.count()} lines")
    print(f"✅ PO has {receipts.count()} receipts")

exit()
```

---

### ✅ Supplychain App Complete When:
- [ ] All ForeignKeys have related_name
- [ ] Migrations generated and applied
- [ ] `python manage.py check` passes
- [ ] Shell tests pass

**Time Spent:** ~1 hour  
**Next:** finance app

---

## 💰 APP 5: FINANCE (1 hour)

### Location:
```
apps/finance/models.py
```

### Models in This App:
- Invoice
- InvoiceLine
- Payment
- CostCenter
- GLAccount
- JournalEntry
- Budget
- etc.

### Estimated ForeignKeys to Fix: ~6

---

### Step-by-Step Instructions:

**1. Open the File**
```bash
code apps/finance/models.py
```

**2. Find and Fix ForeignKeys**

**Invoice Model:**
```python
class Invoice(models.Model):
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.PROTECT,
        related_name='invoices'  # ✅ ADD THIS
    )
    
    sales_order = models.ForeignKey(
        'sales.SalesOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'  # ✅ ADD THIS
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**InvoiceLine Model:**
```python
class InvoiceLine(models.Model):
    invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.CASCADE,
        related_name='lines'  # ✅ ADD THIS (or 'invoice_lines')
    )
    
    gl_account = models.ForeignKey(
        'GLAccount',
        on_delete=models.PROTECT,
        related_name='invoice_lines'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**Payment Model:**
```python
class Payment(models.Model):
    invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.PROTECT,
        related_name='payments'  # ✅ ADD THIS
    )
    
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_payments'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**JournalEntry Model:**
```python
class JournalEntry(models.Model):
    gl_account = models.ForeignKey(
        'GLAccount',
        on_delete=models.PROTECT,
        related_name='journal_entries'  # ✅ ADD THIS
    )
    
    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entries'  # ✅ ADD THIS
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_journal_entries'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**Budget Model:**
```python
class Budget(models.Model):
    cost_center = models.ForeignKey(
        'CostCenter',
        on_delete=models.CASCADE,
        related_name='budgets'  # ✅ ADD THIS
    )
    
    gl_account = models.ForeignKey(
        'GLAccount',
        on_delete=models.PROTECT,
        related_name='budgets'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

---

### 3. Save the File

---

### 4. Generate Migrations

```bash
python manage.py makemigrations finance
```

---

### 5. Apply Migrations

```bash
python manage.py migrate finance
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
from apps.finance.models import Invoice, Payment

# Test invoice relationships
invoice = Invoice.objects.first()
if invoice:
    lines = invoice.lines.all()
    payments = invoice.payments.all()
    print(f"✅ Invoice has {lines.count()} lines")
    print(f"✅ Invoice has {payments.count()} payments")

exit()
```

---

### ✅ Finance App Complete When:
- [ ] All ForeignKeys have related_name
- [ ] Migrations generated and applied
- [ ] `python manage.py check` passes
- [ ] Shell tests pass

**Time Spent:** ~1 hour  
**Next:** execution app

---

## ⚙️ APP 6: EXECUTION (1 hour)

### Location:
```
apps/execution/models.py
```

### What is Execution:
Shop floor execution - tracks work being performed on work orders

### Models in This App:
- WorkCenter
- Operation
- OperationExecution (may duplicate Sprint 4)
- LaborEntry
- MaterialIssue
- QualityCheckpoint (may link to quality app)
- etc.

### Estimated ForeignKeys to Fix: ~7

---

### Step-by-Step Instructions:

**1. Open the File**
```bash
code apps/execution/models.py
```

**2. Find and Fix ForeignKeys**

**WorkCenter Model:**
```python
class WorkCenter(models.Model):
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_work_centers'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**Operation Model:**
```python
class Operation(models.Model):
    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.CASCADE,
        related_name='execution_operations'  # ✅ ADD THIS
        # Note: May need to disambiguate from workorders.OperationExecution
    )
    
    work_center = models.ForeignKey(
        'WorkCenter',
        on_delete=models.PROTECT,
        related_name='operations'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**LaborEntry Model:**
```python
class LaborEntry(models.Model):
    operation = models.ForeignKey(
        'Operation',
        on_delete=models.CASCADE,
        related_name='labor_entries'  # ✅ ADD THIS
    )
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='labor_entries'  # ✅ ADD THIS
    )
    
    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.CASCADE,
        related_name='labor_entries'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**MaterialIssue Model:**
```python
class MaterialIssue(models.Model):
    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.CASCADE,
        related_name='material_issues'  # ✅ ADD THIS
    )
    
    operation = models.ForeignKey(
        'Operation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='material_issues'  # ✅ ADD THIS
    )
    
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='material_issues'  # ✅ ADD THIS
    )
    
    lot = models.ForeignKey(
        'inventory.MaterialLot',
        on_delete=models.PROTECT,
        related_name='material_issues'  # ✅ ADD THIS
    )
    
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='issued_materials'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**ExecutionCheckpoint Model:**
```python
class ExecutionCheckpoint(models.Model):
    operation = models.ForeignKey(
        'Operation',
        on_delete=models.CASCADE,
        related_name='checkpoints'  # ✅ ADD THIS
    )
    
    quality_checkpoint = models.ForeignKey(
        'quality.QualityCheckpoint',  # if exists
        on_delete=models.PROTECT,
        related_name='executions'  # ✅ ADD THIS
    )
    
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='performed_checkpoints'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

---

### 3. Save the File

---

### 4. Generate Migrations

```bash
python manage.py makemigrations execution
```

---

### 5. Apply Migrations

```bash
python manage.py migrate execution
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
from apps.execution.models import WorkCenter, Operation, LaborEntry, MaterialIssue

# Test work center relationships
wc = WorkCenter.objects.first()
if wc:
    operations = wc.operations.all()
    print(f"✅ WorkCenter has {operations.count()} operations")

# Test operation relationships
operation = Operation.objects.first()
if operation:
    labor = operation.labor_entries.all()
    materials = operation.material_issues.all()
    checkpoints = operation.checkpoints.all()
    print(f"✅ Operation has {labor.count()} labor entries")
    print(f"✅ Operation has {materials.count()} material issues")
    print(f"✅ Operation has {checkpoints.count()} checkpoints")

exit()
```

---

### ✅ Execution App Complete When:
- [ ] All ForeignKeys have related_name
- [ ] Migrations generated and applied
- [ ] `python manage.py check` passes
- [ ] Shell tests pass

**Time Spent:** ~1 hour

---

## ✅ PHASE 2 COMPLETION

### Final Phase 2 Validation:

**1. Check All Apps**
```bash
python manage.py check
```

**Expected:** No issues

---

**2. Test Key Sprint 6 Relationships**

```bash
python manage.py shell
```

```python
from apps.supplychain.models import Vendor, PurchaseOrder
from apps.finance.models import Invoice
from apps.execution.models import Operation
from apps.workorders.models import WorkOrder

# Test supplychain → workorders
po = PurchaseOrder.objects.first()
if po and po.work_order:
    print(f"✅ PO linked to work order: {po.work_order.wo_number}")

# Test finance → workorders
wo = WorkOrder.objects.first()
if wo:
    entries = wo.journal_entries.all()
    print(f"✅ WorkOrder has {entries.count()} journal entries")

# Test execution → workorders
if wo:
    labor = wo.labor_entries.all()
    materials = wo.material_issues.all()
    print(f"✅ WorkOrder has {labor.count()} labor entries")
    print(f"✅ WorkOrder has {materials.count()} material issues")

# Test vendor relationships
vendor = Vendor.objects.first()
if vendor:
    pos = vendor.purchase_orders.all()
    invoices = vendor.invoices.all()
    print(f"✅ Vendor has {pos.count()} purchase orders")
    print(f"✅ Vendor has {invoices.count()} invoices")

print("\n🎉 Phase 2 Complete!")
exit()
```

---

**3. Commit Changes**
```bash
git add apps/supplychain apps/finance apps/execution
git commit -m "fix: Add related_name to Sprint 6 dependencies (supplychain, finance, execution)"
git push
```

---

### ✅ Phase 2 Complete Checklist:

- [ ] supplychain app: All ForeignKeys fixed (~8)
- [ ] finance app: All ForeignKeys fixed (~6)
- [ ] execution app: All ForeignKeys fixed (~7)
- [ ] Total: ~21 ForeignKeys fixed
- [ ] All migrations generated and applied
- [ ] `python manage.py check` passes
- [ ] All shell tests pass
- [ ] Changes committed and pushed

---

## 🎉 PHASE 2 SUCCESS!

**Time Spent:** ~3 hours  
**ForeignKeys Fixed:** ~21  
**Impact:** Sprint 6 dependencies resolved  

**Progress So Far:**
- ✅ Phase 1: 23 ForeignKeys fixed
- ✅ Phase 2: 21 ForeignKeys fixed
- ✅ **Total: 44 ForeignKeys fixed**

**Remaining:** ~4 ForeignKeys in Phase 3

**Next:** Take a 15-minute break, then proceed to Phase 3!

---

## 📄 NEXT DOCUMENT

**Open:** [PHASE3_OTHER_APPS.md](computer:///mnt/user-data/outputs/PHASE3_OTHER_APPS.md)

**Goal:** Fix procedures, hr, training, compliance, audit apps (2 hours)

---

**Excellent progress! 💪**

**END OF PHASE 2**
