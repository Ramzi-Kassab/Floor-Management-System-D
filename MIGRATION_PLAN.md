# Migration Plan - ARDT Floor Management System

## Overview

This document outlines migration strategies for:
1. Legacy Supplier → Vendor migration
2. Historical data import
3. Stock balance synchronization
4. Production deployment

---

## Migration 1: Supplier to Vendor

### Current State
```
Supplier (Legacy)          Vendor (New)
─────────────────         ──────────────
VND-000001: Halliburton   VND-000001: Halliburton ✓
VND-000011: Eastern Bdry  (not migrated)
```

### Migration Steps

#### Step 1: Audit Existing Suppliers
```python
from apps.supplychain.models import Supplier, Vendor

# Find suppliers without corresponding vendors
for s in Supplier.objects.all():
    exists = Vendor.objects.filter(vendor_code=s.code).exists()
    print(f"{s.code}: {s.name} - {'EXISTS' if exists else 'NEEDS MIGRATION'}")
```

#### Step 2: Create Vendors from Suppliers
```python
from apps.supplychain.models import Supplier, Vendor

for supplier in Supplier.objects.filter(is_active=True):
    vendor, created = Vendor.objects.get_or_create(
        vendor_code=supplier.code,
        defaults={
            'name': supplier.name,
            'email': supplier.email or '',
            'phone': supplier.phone or '',
            'address_line_1': (supplier.address or '')[:200],
            'country': supplier.country or '',
            'status': Vendor.Status.ACTIVE,
            'vendor_type': 'MATERIALS_SUPPLIER',
        }
    )
    if created:
        print(f"Created Vendor: {vendor.vendor_code}")
    else:
        print(f"Vendor exists: {vendor.vendor_code}")
```

#### Step 3: Update References
After migration, update any remaining Supplier references:
- ItemSupplier → Link to Vendor instead
- Historical POs → Keep Supplier reference for audit trail

#### Step 4: Deactivate Legacy Suppliers
```python
# Mark migrated suppliers as inactive
Supplier.objects.filter(
    code__in=Vendor.objects.values_list('vendor_code', flat=True)
).update(is_active=False)
```

---

## Migration 2: Stock Balance Synchronization

### Problem
GRNs posted before the fix only updated `StockBalance`, not `InventoryStock`.
Item detail pages read from `InventoryStock`, showing incorrect quantities.

### Solution: Sync Endpoint
URL: `/inventory/admin/sync-stock/`

### How It Works
```python
# Aggregates StockBalance by item+location+lot
# Creates/updates InventoryStock records

for balance in StockBalance.objects.all():
    inv_stock, _ = InventoryStock.objects.get_or_create(
        item=balance.item,
        location=balance.location,
        lot_number=balance.lot.lot_number if balance.lot else '',
        serial_number='',
    )
    inv_stock.quantity_on_hand = balance.qty_on_hand
    inv_stock.save()
```

### When to Run
- After importing historical data
- After manual database corrections
- If item pages show wrong quantities

### Access
1. Go to `/inventory/ledger/balances/`
2. Click green "Sync to Items" button
3. Confirm the sync

---

## Migration 3: Historical Data Import

### Item Master Import

#### CSV Format
```csv
code,name,category_code,unit,description,min_stock,reorder_point
CT-0014,1234567 1613 CT200,CT-PDC,EA,New cutter type,10,5
CT-0015,9876543 1308 CT155,CT-PDC,EA,Another cutter,20,10
```

#### Import Script
```python
import csv
from apps.inventory.models import InventoryItem, InventoryCategory

with open('items.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        category = InventoryCategory.objects.get(code=row['category_code'])
        item, created = InventoryItem.objects.get_or_create(
            code=row['code'],
            defaults={
                'name': row['name'],
                'category': category,
                'unit': row['unit'],
                'description': row['description'],
                'min_stock': int(row['min_stock']),
                'reorder_point': int(row['reorder_point']),
            }
        )
        print(f"{'Created' if created else 'Exists'}: {item.code}")
```

### Opening Stock Import

#### CSV Format
```csv
item_code,location_code,quantity,lot_number,unit_cost
CT-0003,RCV-01,100,LOT-2025-001,25.50
CT-0004,STK-A01,50,,30.00
```

#### Import Script
```python
import csv
from decimal import Decimal
from apps.inventory.models import (
    InventoryItem, InventoryLocation, InventoryStock,
    StockBalance, Party, OwnershipType, QualityStatus, ConditionType
)

# Get defaults
ardt_party = Party.objects.get(code='ARDT')
owned = OwnershipType.objects.get(code='OWNED')
available = QualityStatus.objects.get(code='AVAIL')
new_condition = ConditionType.objects.get(code='NEW')

with open('opening_stock.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        item = InventoryItem.objects.get(code=row['item_code'])
        location = InventoryLocation.objects.get(code=row['location_code'])
        qty = Decimal(row['quantity'])
        cost = Decimal(row['unit_cost'])

        # Create InventoryStock
        stock, _ = InventoryStock.objects.get_or_create(
            item=item,
            location=location,
            lot_number=row.get('lot_number', ''),
            serial_number='',
            defaults={'quantity_on_hand': 0}
        )
        stock.quantity_on_hand += qty
        stock.save()

        # Create StockBalance
        balance, _ = StockBalance.objects.get_or_create(
            item=item,
            location=location,
            lot=None,  # Create Lot if needed
            owner_party=ardt_party,
            ownership_type=owned,
            quality_status=available,
            condition=new_condition,
            defaults={'qty_on_hand': 0, 'total_cost': 0}
        )
        balance.qty_on_hand += qty
        balance.total_cost += qty * cost
        balance.save()

        print(f"Imported: {item.code} @ {location.code}: {qty}")
```

---

## Migration 4: Customer/Rig Data

### Current Data
- 8 Customers (Aramco, Halliburton, Schlumberger, etc.)
- 5 Rigs (all Aramco)

### Additional Data Needed
```csv
# customers.csv
code,name,customer_type,country,contact_email
ADNOC,ADNOC,OPERATOR,UAE,procurement@adnoc.ae
TAQA,TAQA,OPERATOR,UAE,supply@taqa.ae

# rigs.csv
code,name,customer_code,rig_type,location
RIG-101,Rig 101,ARAMCO,LAND,Eastern Province
RIG-102,Rig 102,ARAMCO,OFFSHORE,Arabian Gulf
```

---

## Migration 5: Vendor Catalog (HDBS Items)

### Goal
Import full HDBS cutter catalog with specifications.

### CSV Format
```csv
hdbs_pn,description,size_mm,grade,chamfer_type,price_usd
418525,1308 CT31 Drop In,13,PREMIUM,STANDARD,28.50
871781,13MM Long CT200 18C,13,STANDARD,NONE,22.00
738227,1308 CR31 18C,13,PREMIUM,AGGRESSIVE,32.00
```

### Import Strategy
1. Create items with HDBS part number as name
2. Add cutter specs via `ItemCutterSpec`
3. Link to HDBS vendor via `ItemSupplier`
4. Set standard costs

---

## Migration 6: Production Deployment

### Pre-Deployment Checklist

#### Database
- [ ] Backup current SQLite database
- [ ] Export fixtures: `python manage.py dumpdata > backup.json`
- [ ] Set up PostgreSQL on production server
- [ ] Run migrations
- [ ] Load seed data (categories, UOMs, etc.)

#### Environment
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up static file serving (nginx/whitenoise)
- [ ] Configure HTTPS
- [ ] Set secure SECRET_KEY

#### Data Migration
- [ ] Import master data (items, customers, vendors)
- [ ] Import opening balances (via Stock Adjustment)
- [ ] Verify all counts match source system
- [ ] Run sync to ensure InventoryStock matches StockBalance

### Deployment Commands
```bash
# On production server
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py loaddata fixtures/seed_data.json
supervisorctl restart fms
```

---

## Rollback Procedures

### Database Rollback
```bash
# Restore from backup
pg_restore -d fms_prod backup_20260101.dump

# Or for SQLite
cp db.sqlite3.backup db.sqlite3
```

### Code Rollback
```bash
# Revert to previous release
git checkout v1.0.0
pip install -r requirements.txt
python manage.py migrate
supervisorctl restart fms
```

---

## Data Validation Queries

### Verify Stock Integrity
```python
# Check InventoryStock matches StockBalance
from django.db.models import Sum

for item in InventoryItem.objects.all():
    inv_total = item.stock_records.aggregate(
        total=Sum('quantity_on_hand')
    )['total'] or 0

    bal_total = StockBalance.objects.filter(item=item).aggregate(
        total=Sum('qty_on_hand')
    )['total'] or 0

    if inv_total != bal_total:
        print(f"MISMATCH: {item.code} - Stock: {inv_total}, Balance: {bal_total}")
```

### Verify PO/GRN Linkage
```python
# Check all GRN lines link to valid PO lines
for grn in GoodsReceiptNote.objects.all():
    if grn.purchase_order:
        po_items = set(grn.purchase_order.lines.values_list('inventory_item_id', flat=True))
        grn_items = set(grn.lines.values_list('item_id', flat=True))

        orphans = grn_items - po_items
        if orphans:
            print(f"{grn.grn_number}: Items not on PO: {orphans}")
```

---

## Support Contacts

- **System Admin**: admin@ardt.com
- **Database Issues**: dba@ardt.com
- **Development**: dev@ardt.com
