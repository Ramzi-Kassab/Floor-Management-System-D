# Cutter Inventory Management System - Requirements Document

**Version:** 1.0
**Date:** January 16, 2026
**Branch:** claude/explore-models-j9CSu
**Reference File:** `Cutter Inventory 01-15-2026.xlsx`

---

## 1. Executive Summary

This document describes the requirements for implementing a dedicated **Cutter Inventory View** in the ARDT Floor Management System. The goal is to replicate and improve upon the functionality currently managed in the Excel file `Cutter Inventory 01-15-2026.xlsx`, providing real-time visibility into:

- PDC Cutter stock levels by variant (NEW, E&O, Ground, Reclaimed, Client)
- Consumption history (2, 3, 6 months)
- BOM requirements from scheduled drill bits
- Purchase order tracking for cutters
- Safety stock monitoring and forecasting

---

## 2. Current Excel File Analysis

### 2.1 Purpose

The Excel file serves as the **master tracking system for PDC cutter inventory**, connecting:
- Individual cutter items (by Material Number/HDBS code)
- Stock levels by source/condition (New, E&O, Ground, Reclaimed, Client)
- Demand from drill bit BOMs (L5 level)
- Purchase orders and receipts
- Consumption transactions

### 2.2 Important Sheets

| Sheet Name | Purpose | Row Count |
|------------|---------|-----------|
| **Cutters Inventory 12-30-2025** | Master cutter inventory with stock by variant, consumption, BOM requirement, orders, forecast | 304 cutters |
| **L3&L4 BOMs & Cutters 12-30-2025** | Links drill bits (by Serial No.) to L3/L4 designs to L5 BOMs to cutter requirements | 924 rows |
| **Cutters Orders Updates** | Purchase order tracking with ordered qty, received qty, balance | 750 orders |
| **Cutters Consumption Updates** | Transaction log of every cutter issue/receipt by drill bit | 6,473 transactions |

### 2.3 Key Relationships

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         BIT HIERARCHY                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Drill Bit (Serial No.)                                                │
│        │                                                                 │
│        ▼                                                                 │
│   L3/L4 Design (HDBS MAT No.)  ─── Describes the bit design             │
│        │                            (without cutters)                    │
│        │                                                                 │
│        ▼                                                                 │
│   L5 BOM (MAT No.)  ─────────────── Specifies cutters for this design   │
│        │                            (one L3/L4 can have multiple L5s)    │
│        │                                                                 │
│        ▼                                                                 │
│   Cutter Items (Component MAT)  ─── Individual cutter types with qty    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Inventory Sheet Column Mapping

| Excel Column | Description | Maps To |
|--------------|-------------|---------|
| MN | Material Number (SAP) | `InventoryItem.mat_number` |
| Product name | Full cutter description | `InventoryItem.name` |
| Cutter | Cutter type code (CT97, CT182, etc.) | Attribute: `cutter_type` |
| Size | Size code (1313, 1608, etc.) | Attribute: `cutter_size` |
| Chamfer | Chamfer type (10C, 18C, 0.018", etc.) | Attribute: `chamfer` |
| Family | Category (Premium, Standard, DoC Control) | Attribute: `family` |
| **Stock Columns:** | | |
| ENO As New Cutter | E&O condition - new | `VariantStock` where variant=NEW-EO |
| ENO Ground Cutter | E&O condition - ground | `VariantStock` where variant=GRD-EO |
| ARDT Reclaim Cutter | ARDT reclaimed | `VariantStock` where variant=USED-RCL |
| LSTK Reclaim Cutter | Client (Halliburton LSTK) reclaimed | `VariantStock` where variant=CLI-RCL |
| New Stock | Brand new purchased | `VariantStock` where variant=NEW-PUR |
| Total New | Sum of all new condition variants | Calculated |
| **Planning Columns:** | | |
| 6 months consumption | Consumption in last 6 months | Aggregated from `StockLedger` |
| 3 months consumption | Consumption in last 3 months | Aggregated from `StockLedger` |
| 2 months consumption | = 6 months / 3 | Calculated |
| Safety Stock | Based on 2 month consumption (approx) | `ItemPlanning.safety_stock` |
| BOM requirement | Total cutters needed from all BOMs for drill bits in warehouse | Calculated from `BOMLine` |
| On Order | Quantity ordered but not received | From `PurchaseOrderLine.quantity_outstanding` |
| Total Stock - Forecast | Available - Required + On Order | Calculated |

---

## 3. Current System Analysis

### 3.1 Existing Models (What Already Exists)

| Component | Model | Status |
|-----------|-------|--------|
| Cutter master data | `InventoryItem` + `ItemAttributeValue` | EXISTS |
| Cutter attributes | `CategoryAttribute` for PDC Cutters | EXISTS (18 attributes) |
| Variant tracking | `ItemVariant` + `VariantCase` | EXISTS (needs code fixes) |
| Stock by variant | `VariantStock` | EXISTS |
| Transaction ledger | `StockLedger` | EXISTS |
| Safety stock | `ItemPlanning.safety_stock` | EXISTS |
| BOM structure | `BOM` + `BOMLine` | EXISTS |
| Work order consumption | `WorkOrderMaterial` | EXISTS |
| Purchase orders | `PurchaseOrder` + `PurchaseOrderLine` | EXISTS |
| Goods receipts | `Receipt` + `ReceiptLine` | EXISTS |
| Drill bit tracking | `DrillBit` (by serial) | EXISTS |
| Design hierarchy | `Design` (L3/L4) → `BOM` (L5) | EXISTS |

### 3.2 PDC Cutter Attributes (Already Configured)

The PDC Cutters category (`CUT-PDC`) has 18 attributes:

| Attribute | Type | Required | In Name |
|-----------|------|----------|---------|
| hdbs_code | TEXT | Yes | Yes |
| cutter_size | TEXT (dropdown) | Yes | Yes |
| cutter_type | TEXT (dropdown) | Yes | Yes |
| chamfer | TEXT (dropdown) | No | Yes |
| family | TEXT | No | Yes |
| cutter_grade | TEXT (dropdown) | No | Yes |
| diameter | NUMBER | No | No |
| length | NUMBER | No | No |
| length_class | TEXT (dropdown) | No | No |
| cutter_shape | TEXT (dropdown) | No | No |
| substrate_shape | TEXT (dropdown) | No | No |
| diamond_thickness | NUMBER | No | No |
| separator_type | TEXT (dropdown) | No | No |
| use | TEXT (dropdown) | No | No |
| rotatability | TEXT (dropdown) | No | No |
| dynamic | TEXT (dropdown) | No | No |
| item_number | TEXT | No | No |
| additional_description | TEXT (multiline) | No | No |

---

## 4. Gap Analysis

### 4.1 Variant Case Corrections Required

The current `VariantCase` codes need correction to match actual conditions:

| Current Code | Current Name | Issue | Correct Code | Correct Name |
|--------------|--------------|-------|--------------|--------------|
| USED-RET | Retrofit (as New) | Condition is NEW, not USED | **NEW-RET** | Retrofit (as New) |
| USED-EO | E&O (Excess & Obsolete) | Condition is NEW, not USED | **NEW-EO** | E&O (as New) |
| USED-GRD | Ground (Surface Damage) | Should clarify E&O source | **GRD-EO** | E&O Ground |

**Complete Variant Case Table (Corrected):**

| Code | Name | Condition | Acquisition | Reclaim Category | Ownership | Excel Column |
|------|------|-----------|-------------|------------------|-----------|--------------|
| NEW-PUR | New Purchased | New | Purchased | - | ARDT | New Stock |
| NEW-RET | Retrofit (as New) | New | Reclaimed | Retrofit | ARDT | (not in file) |
| NEW-EO | E&O (as New) | New | Reclaimed | E&O | ARDT | ENO As New |
| GRD-EO | E&O Ground | Used | Reclaimed | Ground | ARDT | ENO Ground |
| USED-RCL | Standard Reclaim | Used | Reclaimed | Standard | ARDT | ARDT Reclaim |
| CLI-NEW | Client New | New | Client Provided | - | Client | (not in file) |
| CLI-RCL | Client Reclaim | Used | Client Provided | - | Client | LSTK Reclaim |

### 4.2 Missing Features

| Feature | Priority | Description |
|---------|----------|-------------|
| **Cutter Inventory Dashboard** | HIGH | Main view showing all cutters with stock by variant, consumption, BOM requirement, orders, forecast |
| **Consumption Aggregation** | HIGH | Calculate 2/3/6 month consumption from StockLedger |
| **BOM Requirement Calculation** | HIGH | Sum cutter quantities from BOMLines for all drill bits in warehouse |
| **On Order Calculation** | HIGH | Sum outstanding PO line quantities for each cutter |
| **Forecast Calculation** | HIGH | Available - BOM Requirement + On Order |
| **Cutter Orders View** | MEDIUM | Dedicated view showing only cutter-related POs (NEW-PUR variant only) |
| **Safety Stock Alerts** | MEDIUM | Highlight cutters below safety stock |

### 4.3 Data Flow Requirements

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CUTTER INVENTORY VIEW DATA SOURCES                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STOCK LEVELS                                                            │
│  ────────────                                                            │
│  VariantStock.quantity_on_hand                                          │
│  WHERE variant.base_item.category = 'PDC Cutters'                       │
│  GROUP BY variant.variant_case                                          │
│                                                                          │
│  CONSUMPTION (2/3/6 months)                                             │
│  ──────────────────────────                                             │
│  StockLedger.qty_delta (negative = consumption)                         │
│  WHERE transaction_type IN ('ISSUE', 'CONSUMPTION')                     │
│  AND transaction_date >= (today - 6 months)                             │
│  GROUP BY item, time_period                                             │
│                                                                          │
│  BOM REQUIREMENT                                                         │
│  ───────────────                                                         │
│  BOMLine.quantity                                                       │
│  WHERE bom.design IN (designs with drill_bits in warehouse)             │
│  OR WHERE bom IN (boms linked to work_orders in progress)               │
│  GROUP BY inventory_item                                                │
│                                                                          │
│  ON ORDER                                                                │
│  ────────                                                                │
│  PurchaseOrderLine.quantity_ordered - quantity_received                 │
│  WHERE inventory_item.category = 'PDC Cutters'                          │
│  AND purchase_order.status NOT IN ('COMPLETED', 'CANCELLED')            │
│  GROUP BY inventory_item                                                │
│                                                                          │
│  SAFETY STOCK                                                            │
│  ────────────                                                            │
│  ItemPlanning.safety_stock                                              │
│  WHERE item.category = 'PDC Cutters'                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Requirements for Cutter Inventory View

### 5.1 Functional Requirements

#### FR-1: Cutter Inventory Dashboard
- Display all PDC Cutter items in a filterable, sortable table
- Show stock breakdown by variant case (NEW-PUR, NEW-EO, GRD-EO, USED-RCL, CLI-RCL)
- Show total available stock (sum of all variants)
- Allow filtering by: cutter type, size, chamfer, family, stock status

#### FR-2: Consumption History
- Display 6 month, 3 month, and 2 month consumption totals
- 2 month consumption = 6 month consumption / 3
- Source data from StockLedger where transaction_type is ISSUE or CONSUMPTION

#### FR-3: BOM Requirement
- Calculate total cutters needed from all L5 BOMs
- Include BOMs linked to:
  - Drill bits currently in warehouse (any status)
  - Work orders in progress
- Display as single "BOM Requirement" column

#### FR-4: On Order Tracking
- Show total quantity on order from PurchaseOrderLines
- Only include POs that are not COMPLETED or CANCELLED
- Calculate as: quantity_ordered - quantity_received

#### FR-5: Forecast Calculation
- Formula: Total Stock - BOM Requirement + On Order
- Highlight negative forecasts (shortage warning)

#### FR-6: Safety Stock Monitoring
- Display safety stock level from ItemPlanning
- Highlight items where Total Stock < Safety Stock
- Safety stock calculation: based on 2 month consumption (approximate)

#### FR-7: Cutter Orders View
- Dedicated view showing only cutter-related purchase orders
- Filter: inventory_item.category = 'PDC Cutters'
- Show: PO#, Order Date, Cutter details, Ordered Qty, Received Qty, Balance
- Only for NEW-PUR variant (new stock purchases)

### 5.2 UI/UX Requirements

#### UR-1: Main Dashboard Layout
```
┌─────────────────────────────────────────────────────────────────────────┐
│  CUTTER INVENTORY                                            [Export]   │
├─────────────────────────────────────────────────────────────────────────┤
│  Filters: [Type ▼] [Size ▼] [Family ▼] [Stock Status ▼] [Search...]    │
├─────────────────────────────────────────────────────────────────────────┤
│  Summary Cards:                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Total    │ │ NEW-PUR  │ │ NEW-EO   │ │ GRD-EO   │ │ On Order │      │
│  │ 12,450   │ │ 5,200    │ │ 3,100    │ │ 2,150    │ │ 1,500    │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
├─────────────────────────────────────────────────────────────────────────┤
│  # │ MN     │ Name          │NEW │E&O │GRD │RCL │CLI │Tot │6M │3M │2M │SS │BOM │Ord │Fcst│
│  ──┼────────┼───────────────┼────┼────┼────┼────┼────┼────┼───┼───┼───┼───┼────┼────┼────│
│  1 │ 802065 │ 1313 CT97 10C │  0 │  0 │  0 │  2 │  0 │  2 │11 │11 │ 4 │ 5 │  0 │  0 │  2 │
│  2 │ 179734 │ 13MM M1 IA-STL│137 │  0 │  0 │  0 │  9 │146 │140│70 │47 │50 │342 │  0 │-196│
│  ...                                                                     │
└─────────────────────────────────────────────────────────────────────────┘

Legend:
- NEW = NEW-PUR (New Purchased)
- E&O = NEW-EO (E&O as New)
- GRD = GRD-EO (E&O Ground)
- RCL = USED-RCL (ARDT Reclaim)
- CLI = CLI-RCL (Client Reclaim)
- Tot = Total Stock
- 6M/3M/2M = Consumption (months)
- SS = Safety Stock
- BOM = BOM Requirement
- Ord = On Order
- Fcst = Forecast (Tot - BOM + Ord)
```

#### UR-2: Row Highlighting
- **Red background**: Forecast < 0 (shortage)
- **Yellow background**: Total Stock < Safety Stock
- **Green background**: Forecast > Safety Stock (healthy)

#### UR-3: Drill-down Capabilities
- Click cutter row → Item detail page
- Click BOM Requirement → List of BOMs requiring this cutter
- Click On Order → List of PO lines for this cutter
- Click Consumption → Transaction history (separate view)

---

## 6. Implementation Recommendations

### Phase 1: Data Model Fixes (Variant Cases)
1. Update `VariantCase` codes:
   - Rename USED-RET → NEW-RET
   - Rename USED-EO → NEW-EO
   - Rename USED-GRD → GRD-EO (and update name to "E&O Ground")
2. Update related `ItemVariant` records
3. Update seed data in `seed_variant_cases.py`

### Phase 2: Cutter Inventory Dashboard
1. Create new view: `CutterInventoryListView`
2. Create template: `inventory/cutter_inventory_list.html`
3. Add URL: `/inventory/cutters/`
4. Implement:
   - Stock aggregation by variant
   - Consumption calculation (6/3/2 months)
   - BOM requirement calculation
   - On Order calculation
   - Forecast calculation
   - Safety stock comparison

### Phase 3: Cutter Orders View
1. Create new view: `CutterOrderListView`
2. Create template: `inventory/cutter_orders_list.html`
3. Add URL: `/inventory/cutters/orders/`
4. Filter PurchaseOrderLine where inventory_item is PDC Cutter

### Phase 4: Navigation & Integration
1. Add sidebar menu items under "Logistics" or new "Cutters" section
2. Add dashboard widgets for cutter inventory summary
3. Add alerts for cutters below safety stock

---

## 7. Appendix

### A. Excel Column to System Field Mapping

| Excel Column | System Source | Calculation |
|--------------|---------------|-------------|
| # | Auto-increment | Row number |
| MN | `InventoryItem.mat_number` | Direct |
| Product name | `InventoryItem.name` | Direct |
| Cutter | `ItemAttributeValue` (cutter_type) | Via attribute |
| Size | `ItemAttributeValue` (cutter_size) | Via attribute |
| Chamfer | `ItemAttributeValue` (chamfer) | Via attribute |
| Family | `ItemAttributeValue` (family) | Via attribute |
| ENO As New Cutter | `VariantStock.quantity_on_hand` | WHERE variant_case='NEW-EO' |
| ENO Ground Cutter | `VariantStock.quantity_on_hand` | WHERE variant_case='GRD-EO' |
| ARDT Reclaim Cutter | `VariantStock.quantity_on_hand` | WHERE variant_case='USED-RCL' |
| LSTK Reclaim Cutter | `VariantStock.quantity_on_hand` | WHERE variant_case='CLI-RCL' |
| New Stock | `VariantStock.quantity_on_hand` | WHERE variant_case='NEW-PUR' |
| Total New | Sum of all variant stocks | Calculated |
| 6 months consumption | `StockLedger` aggregation | SUM(qty_delta) WHERE date >= -6mo AND type=ISSUE |
| 3 months consumption | `StockLedger` aggregation | SUM(qty_delta) WHERE date >= -3mo AND type=ISSUE |
| 2 months consumption | Calculated | 6_months / 3 |
| Safety Stock | `ItemPlanning.safety_stock` | Direct |
| BOM requirement | `BOMLine.quantity` | SUM WHERE linked to warehouse drill bits |
| On Order | `PurchaseOrderLine` | SUM(ordered - received) WHERE status != COMPLETED |
| Total Stock - Forecast | Calculated | Total - BOM_req + On_Order |

### B. Variant Case Example Codes

For a cutter with HDBS MAT `1130198`:

| Variant Case | Example Code |
|--------------|--------------|
| NEW-PUR | CT-0118 |
| NEW-RET | RTRO-0118 |
| NEW-EO | ENO-CT-0118 |
| GRD-EO | (follows similar pattern) |
| USED-RCL | RCLM-ARDT-0015 |
| CLI-RCL | RCLM-0118 |

### C. Safety Stock Formula

From the Excel file:
```
Safety Stock ≈ 2 Month Consumption (with approximation)
2 Month Consumption = 6 Month Consumption / 3
```

---

## 8. Agent Prompt for Implementation

To implement this feature, use the following prompt:

```
Read the document at docs/CUTTER_INVENTORY_REQUIREMENTS.md for complete requirements.

Implement the Cutter Inventory Management feature in phases:

PHASE 1: Fix Variant Cases
- Update seed_variant_cases.py with corrected codes:
  - USED-RET → NEW-RET
  - USED-EO → NEW-EO
  - USED-GRD → GRD-EO (rename to "E&O Ground")

PHASE 2: Create Cutter Inventory Dashboard
- New view: CutterInventoryListView at /inventory/cutters/
- Template: inventory/cutter_inventory_list.html
- Features:
  - Stock by variant (NEW-PUR, NEW-EO, GRD-EO, USED-RCL, CLI-RCL)
  - Consumption aggregation (2/3/6 months from StockLedger)
  - BOM requirement calculation (from BOMLine)
  - On Order calculation (from PurchaseOrderLine)
  - Forecast = Total - BOM Requirement + On Order
  - Safety stock comparison with highlighting

PHASE 3: Create Cutter Orders View
- New view: CutterOrderListView at /inventory/cutters/orders/
- Filter PO lines for PDC Cutter items only
- Show: PO#, Date, Cutter, Ordered, Received, Balance

Refer to existing models:
- InventoryItem (category='PDC Cutters')
- ItemVariant + VariantCase
- VariantStock
- StockLedger (for consumption)
- BOMLine (for BOM requirement)
- PurchaseOrderLine (for on order)
- ItemPlanning (for safety stock)
```

---

**Document End**
