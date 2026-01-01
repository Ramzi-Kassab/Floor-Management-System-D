# Floor Management System - Context for Claude Sessions

## Project Overview
Django-based Floor Management System (FMS) for inventory, supply chain, and operations management. Built with Django 4.x, Tailwind CSS, Alpine.js, and Lucide icons.

## Tech Stack
- **Backend**: Django 4.x, Python 3.11+
- **Frontend**: Tailwind CSS, Alpine.js, Lucide icons
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Start Command**: `./hc` (runs Django dev server)

## App Structure

### 1. `apps/inventory/` - Core Inventory Management
**Models** (`models.py`):
- `InventoryCategory` - Item categories with hierarchical structure
- `InventoryItem` - Master item records (code, name, unit, tracking_type, base_uom, costing_method)
- `ItemVariant` - Item variants with VariantCase combinations
- `InventoryStock` - Stock levels by item+location+lot_number+serial_number (what item detail pages read)
- `StockBalance` - Detailed stock with dimensions (owner_party, ownership_type, quality_status, condition)
- `InventoryLocation` - Warehouse locations (warehouse FK, code, location_type)
- `InventoryTransaction` - Stock movement ledger
- `Lot` - Lot/batch tracking
- `GoodsReceiptNote` (GRN) - Receipt documents with status workflow (DRAFT→PENDING_QC→CONFIRMED→POSTED)
- `GRNLine` - GRN line items
- `StockIssue`, `StockTransfer`, `StockAdjustmentDoc` - Other inventory documents

**Key Views** (`views.py`):
- `ItemDetailView` - Shows item with `total_stock` from `stock_records` (InventoryStock)
- `GRNFromPOView` - Create GRN from PO
- `GRNPostView` - Posts GRN to inventory, calls `_update_stock_balance()` which updates BOTH StockBalance AND InventoryStock
- `SyncStockFromBalancesView` - Syncs StockBalance → InventoryStock (URL: `/inventory/admin/sync-stock/`)

**Important**: `InventoryItem.total_stock` property reads from `stock_records` (InventoryStock model), NOT StockBalance.

### 2. `apps/supplychain/` - Procurement & Supply Chain
**Models** (`models.py`):
- `Supplier` - Legacy supplier model (where user's existing vendor data is stored)
- `Vendor` - New vendor model (required by PurchaseOrder FK)
- `PurchaseRequisition` (PR) - Request documents with status (DRAFT→SUBMITTED→APPROVED→CONVERTED)
- `PurchaseRequisitionLine` - PR line items
- `PurchaseOrder` (PO) - Order documents with status (DRAFT→APPROVED→SENT→PARTIALLY_RECEIVED→COMPLETED)
- `PurchaseOrderLine` - PO line items with quantity_ordered, quantity_received

**Key Views** (`views.py`):
- `PRSubmitView` - Submit PR for approval (DRAFT→SUBMITTED)
- `PRConvertToPOView` - Convert approved PR to PO, handles both Vendor and Supplier selection (auto-creates Vendor from Supplier if needed)
- `POApproveView`, `POSendView` - PO workflow actions

**Workflow**: PR (create→submit→approve) → PO (convert→approve→send) → GRN (create from PO→QC→post)

### 3. `apps/accounts/` - User Management
- Custom user model with roles
- `TrustedDevice` for device trust/remember me

### 4. `apps/sales/` - Sales & Customers
- `Customer` model
- Sales orders (if implemented)

### 5. `apps/core/` - Shared Utilities
- Base models, mixins
- Common utilities

### 6. `apps/operations/` - Operations Management
- Work orders, maintenance

## Key Templates

### Layout
- `templates/base.html` - Main layout with sidebar
- `templates/includes/sidebar.html` - Navigation sidebar

### Inventory
- `templates/inventory/item_detail.html` - Item detail with Stock Summary showing `total_stock`
- `templates/inventory/ledger/stock_balance_list.html` - Stock balances page with "Sync to Items" button
- `templates/inventory/documents/grn_*.html` - GRN templates

### Supply Chain
- `templates/supplychain/pr_detail.html` - PR detail with Submit button for DRAFT PRs
- `templates/supplychain/pr_convert_to_po.html` - PR to PO conversion with vendor/supplier dropdown
- `templates/supplychain/po_detail.html` - PO detail with "Receive Goods" button (links to inventory:grn_from_po)

## Recent Fixes (This Session)

1. **PR Submit Button** - Added PRSubmitView and button to PR detail for DRAFT→SUBMITTED transition

2. **Vendor/Supplier Handling** - PR to PO conversion now shows both Vendors AND Suppliers in dropdown, auto-creates Vendor from Supplier when selected

3. **GRN Form Field** - Fixed template to use `form.purchase_order` instead of `form.po`

4. **GRN Template Errors** - Fixed multiple field references (description→item.name, supplier_name→vendor.name)

5. **Inventory Display Fix** - GRN posting now updates BOTH StockBalance AND InventoryStock so item pages show correct quantities

6. **Sync Button** - Added "Sync to Items" button on Stock Balances page to sync existing data

## URL Patterns

### Inventory (`/inventory/`)
- `/inventory/items/` - Item list
- `/inventory/items/<pk>/` - Item detail
- `/inventory/ledger/balances/` - Stock balances (name: `balance_list`)
- `/inventory/admin/sync-stock/` - Sync endpoint (name: `sync_stock`)
- `/inventory/grn/from-po/<po_pk>/` - Create GRN from PO (name: `grn_from_po`)
- `/inventory/grn/<pk>/post/` - Post GRN (name: `grn_post`)

### Supply Chain (`/supply-chain/`)
- `/supply-chain/pr/` - PR list
- `/supply-chain/pr/<pk>/` - PR detail
- `/supply-chain/pr/<pk>/submit/` - Submit PR (name: `pr_submit`)
- `/supply-chain/pr/<pk>/convert-to-po/` - Convert to PO (name: `pr_convert_to_po`)
- `/supply-chain/po/` - PO list
- `/supply-chain/po/<pk>/` - PO detail

## Database Relationships

```
PurchaseRequisition (PR)
    └── PurchaseRequisitionLine (items from InventoryItem)
            ↓ (convert)
PurchaseOrder (PO) → Vendor (FK)
    └── PurchaseOrderLine (items, qty_ordered, qty_received)
            ↓ (receive)
GoodsReceiptNote (GRN) → PO (FK), Vendor (FK)
    └── GRNLine (item, qty_received, qty_accepted)
            ↓ (post)
StockBalance (detailed: item+location+lot+owner+quality+condition)
InventoryStock (simple: item+location+lot_number+serial_number)
            ↓ (read by)
InventoryItem.total_stock → sum of stock_records.quantity_on_hand
```

## Development Notes

1. **Two Stock Models**:
   - `StockBalance` = detailed with dimensions (for reporting)
   - `InventoryStock` = simple (for item views via `stock_records` relation)
   - Both must be updated when posting inventory documents

2. **Two Vendor Models**:
   - `Supplier` = legacy model (existing data here)
   - `Vendor` = new model (PO.vendor FK points here)
   - PR→PO conversion auto-creates Vendor from Supplier

3. **GRN Workflow**: DRAFT → PENDING_QC (if requires_qc) → CONFIRMED → POSTED

4. **Item Tracking Types**: NONE, LOT, SERIAL, ASSET

## Branch Information
- Development branch: `claude/setup-codespaces-DtYwm`
- User debug branch: `user-debug-branch`
