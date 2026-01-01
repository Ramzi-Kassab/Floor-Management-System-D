# Project State - Floor Management System

## Current Database Schema

### Core Apps and Their Primary Models

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INVENTORY APP                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐   │
│  │ InventoryItem   │────▶│ InventoryStock   │     │ StockBalance       │   │
│  │ (Master Data)   │     │ (Simple Stock)   │     │ (Detailed Stock)   │   │
│  │                 │     │                  │     │                    │   │
│  │ - code          │     │ - item (FK)      │     │ - item (FK)        │   │
│  │ - name          │     │ - location (FK)  │     │ - location (FK)    │   │
│  │ - category (FK) │     │ - lot_number     │     │ - lot (FK)         │   │
│  │ - base_uom (FK) │     │ - serial_number  │     │ - owner_party (FK) │   │
│  │ - tracking_type │     │ - qty_on_hand    │     │ - ownership_type   │   │
│  │ - costing_method│     │ - qty_reserved   │     │ - quality_status   │   │
│  │ - lifecycle_state│    │ - qty_available  │     │ - condition (FK)   │   │
│  └─────────────────┘     └──────────────────┘     │ - qty_on_hand      │   │
│         │                        ▲                │ - qty_reserved     │   │
│         │                        │                └────────────────────┘   │
│         │                        │                         ▲               │
│         ▼                        │                         │               │
│  ┌─────────────────┐             │                         │               │
│  │ ItemVariant     │             │                         │               │
│  │                 │             │                         │               │
│  │ - base_item(FK) │     ┌───────┴─────────┐     ┌────────┴────────┐     │
│  │ - variant_case  │     │ GRN Posting     │     │ GRN Posting     │     │
│  │ - customer (FK) │     │ Updates Both    │─────│ Updates Both    │     │
│  │ - account (FK)  │     └─────────────────┘     └─────────────────┘     │
│  └─────────────────┘                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            SUPPLY CHAIN APP                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐   │
│  │ Supplier        │     │ Vendor           │     │ PurchaseOrder      │   │
│  │ (Legacy)        │     │ (New)            │◀────│                    │   │
│  │                 │     │                  │     │ - po_number        │   │
│  │ - code          │     │ - vendor_code    │     │ - vendor (FK)      │   │
│  │ - name          │     │ - name           │     │ - status           │   │
│  │ - email         │     │ - vendor_type    │     │ - order_date       │   │
│  │ - phone         │     │ - status         │     │                    │   │
│  │ - address       │     │ - qualification  │     └────────────────────┘   │
│  │ - country       │     │ - tax_id         │              │               │
│  └─────────────────┘     └──────────────────┘              │               │
│         │                        ▲                         ▼               │
│         │     Auto-create        │              ┌────────────────────┐     │
│         └────────────────────────┘              │ PurchaseOrderLine  │     │
│                                                 │                    │     │
│                                                 │ - inventory_item   │     │
│  ┌─────────────────┐     ┌──────────────────┐   │ - qty_ordered      │     │
│  │ PurchaseReq     │────▶│ Convert to PO    │   │ - qty_received     │     │
│  │                 │     └──────────────────┘   └────────────────────┘     │
│  │ - status:       │                                      │                │
│  │   DRAFT         │                                      ▼                │
│  │   SUBMITTED     │                           ┌────────────────────┐      │
│  │   APPROVED      │                           │ GoodsReceiptNote   │      │
│  │   CONVERTED     │                           │ (GRN)              │      │
│  └─────────────────┘                           │                    │      │
│                                                │ - purchase_order   │      │
│                                                │ - vendor (FK)      │      │
│                                                │ - status:          │      │
│                                                │   DRAFT            │      │
│                                                │   PENDING_QC       │      │
│                                                │   CONFIRMED        │      │
│                                                │   POSTED           │      │
│                                                └────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dimensional Reference Tables (Inventory)

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `Party` | Owner entities (customers, vendors, rigs) | code, name, party_type, can_own_stock |
| `ConditionType` | Item condition (NEW, USED, REFURBISHED) | code, is_new, is_saleable, cost_multiplier |
| `QualityStatus` | QC status (AVAILABLE, HOLD, REJECTED) | code, is_available, allowed_transitions |
| `OwnershipType` | Ownership (ARDT_OWNED, CONSIGNED, CUSTOMER) | code, is_ardt_owned, affects_balance_sheet |
| `LocationType` | Location types (RECEIVING, STORAGE, QC) | code, is_stockable, default_quality_status |
| `UnitOfMeasure` | Units (EA, PC, KG, M) | code, unit_type, base_unit, conversion_factor |

### Document Workflows

```
Purchase Requisition (PR)
    DRAFT → SUBMITTED → APPROVED → CONVERTED (to PO)

Purchase Order (PO)
    DRAFT → APPROVED → SENT → PARTIALLY_RECEIVED → COMPLETED

Goods Receipt Note (GRN)
    DRAFT → PENDING_QC (if requires_qc) → CONFIRMED → POSTED

Stock Issue
    DRAFT → POSTED

Stock Transfer
    DRAFT → PENDING → IN_TRANSIT → RECEIVED → COMPLETED

Stock Adjustment
    DRAFT → PENDING → APPROVED → POSTED
```

## Decisions Made

### 1. Dual Stock Model Architecture
- **InventoryStock**: Simple model for item views (item + location + lot_number + serial_number)
- **StockBalance**: Detailed model with full dimensions (+ owner_party, ownership_type, quality_status, condition)
- **Reason**: Item detail pages need fast, simple queries. Reporting needs dimensional data.
- **Rule**: GRN posting updates BOTH models. Sync endpoint exists for historical data.

### 2. Dual Vendor Model Architecture
- **Supplier**: Legacy model (existing user data stored here)
- **Vendor**: New model with full qualification tracking (PurchaseOrder.vendor FK)
- **Reason**: Existing data in Supplier table, new PO workflow needs Vendor features
- **Rule**: PR→PO conversion auto-creates Vendor from Supplier if needed

### 3. Item Tracking Types
```python
TRACKING_TYPE_CHOICES = [
    ('NONE', 'No Tracking'),      # Simple items
    ('LOT', 'Lot/Batch'),         # Batch tracking
    ('SERIAL', 'Serial Number'),  # Individual tracking
    ('ASSET', 'Asset'),           # Lifecycle management
]
```

### 4. Costing Methods
```python
COSTING_METHOD_CHOICES = [
    ('AVG', 'Weighted Average'),  # Default
    ('FIFO', 'First In First Out'),
    ('STD', 'Standard Cost'),
]
```

### 5. Category-Based Item Configuration
- Categories define attribute templates via `CategoryAttribute`
- Items inherit attributes from category, values stored in `ItemAttributeValue`
- Supports: TEXT, NUMBER, BOOLEAN, DATE, SELECT types
- Conditional rules for dependent attributes

### 6. Variant System
- `VariantCase`: Master combinations (NEW-PURCHASED, USED-RECLAIMED, etc.)
- `ItemVariant`: Item + VariantCase + optional Customer/Account
- Variants have separate stock tracking via `VariantStock`

## Current Data State

| Model | Count | Notes |
|-------|-------|-------|
| InventoryItem | 3 | Test items (TEST-CUT-001, TEST-BRG-001, TEST-SEL-001) |
| InventoryStock | 3 | Stock records at RCV-01 |
| StockBalance | 0 | No detailed balance records |
| Vendor | 1 | Created from Supplier during testing |
| Supplier | 0 | Legacy data may exist |
| PurchaseOrder | 4 | Test POs |
| GoodsReceiptNote | 4 | Test GRNs |
| InventoryCategory | ~10 | Seeded categories |
| InventoryLocation | ~5 | Warehouse locations |

## Key URLs

| URL Pattern | View | Purpose |
|-------------|------|---------|
| `/inventory/items/<pk>/` | ItemDetailView | Item detail with stock |
| `/inventory/ledger/balances/` | StockBalanceListView | Detailed stock by dimension |
| `/inventory/admin/sync-stock/` | SyncStockFromBalancesView | Sync StockBalance → InventoryStock |
| `/inventory/grn/from-po/<pk>/` | GRNFromPOView | Create GRN from PO |
| `/inventory/grn/<pk>/post/` | GRNPostView | Post GRN to inventory |
| `/supply-chain/pr/<pk>/submit/` | PRSubmitView | Submit PR for approval |
| `/supply-chain/pr/<pk>/convert-to-po/` | PRConvertToPOView | Convert PR to PO |

## File Locations

| Component | Path |
|-----------|------|
| Inventory Models | `apps/inventory/models.py` |
| Inventory Views | `apps/inventory/views.py` (5600+ lines) |
| Inventory URLs | `apps/inventory/urls.py` |
| Supply Chain Models | `apps/supplychain/models.py` |
| Supply Chain Views | `apps/supplychain/views.py` |
| Item Detail Template | `templates/inventory/item_detail.html` |
| GRN Templates | `templates/inventory/documents/grn_*.html` |
| PR/PO Templates | `templates/supplychain/*.html` |
| Sidebar | `templates/includes/sidebar.html` |
