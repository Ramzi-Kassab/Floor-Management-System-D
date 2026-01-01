# Next Steps - ARDT Floor Management System

## Current State Summary

### What's Working
- ✅ Item master data with 16 items (13 PDC cutters + 3 test items)
- ✅ Category hierarchy (42 categories)
- ✅ Customer and Rig master data (8 customers, 5 rigs)
- ✅ Vendor/Supplier management (2 vendors, 2 suppliers)
- ✅ PR → PO → GRN workflow (tested end-to-end)
- ✅ GRN posting updates both InventoryStock and StockBalance
- ✅ Stock visibility on item detail pages
- ✅ Sync endpoint for legacy data

### What Needs Attention
- ⚠️ Only 1 warehouse location (RCV-01)
- ⚠️ No production floor locations
- ⚠️ Stock Issues/Transfers not tested
- ⚠️ No cycle counting sessions
- ⚠️ Supplier → Vendor migration incomplete

---

## Priority 1: Complete Warehouse Setup

### 1.1 Create Standard Locations
```
WH-MAIN (Main Warehouse)
├── RCV-01: Receiving Area (exists) ✓
├── RCV-02: Receiving Inspection
├── QRN-01: Quarantine Area
├── STG-01: Staging Area
├── STK-A01: Storage Aisle A, Rack 01
├── STK-A02: Storage Aisle A, Rack 02
├── STK-B01: Storage Aisle B, Rack 01
├── PROD-01: Production Floor
├── WIP-01: Work in Progress
├── SHIP-01: Shipping Dock
└── SCRAP-01: Scrap/Disposal
```

### 1.2 Create Additional Warehouses (Future)
- WH-PROD: Production Warehouse
- WH-FIELD: Field Service Warehouse
- WH-CUST: Customer Consignment

---

## Priority 2: Stock Movement Workflows

### 2.1 Stock Issue (Consumption)
**Use Case**: Issue cutters to production work order

Flow:
1. Create Stock Issue document
2. Select items and quantities
3. Specify destination (work order, cost center)
4. Post to update inventory

**Test Scenario**:
- Issue 2 EA of CT-0003 from RCV-01 to PROD-01
- Verify stock reduces from 5 to 3

### 2.2 Stock Transfer
**Use Case**: Move stock between locations

Flow:
1. Create Transfer document
2. Specify from/to locations
3. Optional: Change ownership, condition, or quality status
4. Post to move stock

**Test Scenario**:
- Transfer 3 EA of CT-0003 from RCV-01 to STK-A01
- Verify stock balances update correctly

### 2.3 Stock Adjustment
**Use Case**: Correct inventory discrepancies

Types:
- Cycle count adjustment
- Physical inventory correction
- Write-off
- Opening balance

---

## Priority 3: Item Data Enhancement

### 3.1 Add Cutter Specifications
PDC Cutters need detailed specs:

| Field | Example Values |
|-------|----------------|
| Cutter Size | 8mm, 13mm, 16mm, 19mm |
| Diamond Table Thickness | 2.0mm, 2.5mm, 3.0mm |
| Grade | Premium, Standard, Economy |
| Chamfer Type | None, Standard, Aggressive |
| Substrate Material | WC-Co, WC-Ni |

**Action**: Use `ItemCutterSpec` model for CT-* items

### 3.2 Add Item Photos
- Product images for visual identification
- Microscope images for QC
- Damage photos for claims

### 3.3 Set Up Item Suppliers
Link items to suppliers with:
- Supplier part number
- Unit price and currency
- Lead time
- Minimum order quantity

---

## Priority 4: Production Integration

### 4.1 Work Order System
**Purpose**: Track bit manufacturing jobs

Components needed:
- Work Order header (job number, customer, design)
- BOM explosion (materials required)
- Operations routing
- Material consumption tracking

### 4.2 BOM (Bill of Materials)
Define material requirements for each bit design:

```
Bit Design: 8.5" 5-blade PDC
├── 28 × CT-0003 (1308 cutter)
├── 14 × CT-0005 (1613 cutter)
├── 1 × BOD-BLANK (steel body)
├── 200g × MAT-TC (tungsten carbide)
└── 50g × CON-BRAZE (brazing alloy)
```

### 4.3 Material Consumption
Track actual material usage per work order:
- Compare planned vs actual
- Calculate variance
- Update inventory automatically

---

## Priority 5: Field Service Integration

### 5.1 Field Technician App (Pocket Mode)
Mobile-friendly interface for:
- View item details
- Consume stock (quick issue)
- Receive stock (quick receipt)
- Scan barcodes

**Exists at**: `/pocket/` routes

### 5.2 Rig Site Inventory
Track cutters at rig locations:
- RIG-088TE, RIG-AD72, etc.
- Field consumption tracking
- Bit run data collection

### 5.3 Reclaim Processing
Workflow for returned cutters:
1. Receive from field
2. Inspect and grade
3. Classify (E&O, Retrofit, Scrap)
4. Return to stock with new variant case

---

## Priority 6: Reporting

### 6.1 Inventory Reports
- Stock on Hand by Location
- Stock Valuation Report
- Slow-Moving Inventory
- Reorder Report

### 6.2 Procurement Reports
- Open PO Report
- Vendor Performance
- Price Variance Analysis
- Receipt History

### 6.3 Consumption Reports
- Usage by Work Order
- Cost per Bit
- Material Variance

---

## Priority 7: Integration

### 7.1 Barcode Implementation
- Generate labels for items, locations, lots
- Scanner integration for receiving
- Mobile scanning for stock moves

### 7.2 ERP Integration (Future)
- SAP Material Master sync
- Financial posting to GL
- Vendor payment integration

### 7.3 HDBS API (Future)
- Real-time pricing from Halliburton
- Order placement
- Delivery tracking

---

## Quick Wins (Can Do Now)

1. **Create more warehouse locations** via admin
2. **Test Stock Issue workflow** with existing stock
3. **Add cutter specs** to CT-* items using ItemCutterSpec
4. **Link items to HDBS supplier** via ItemSupplier
5. **Run cycle count** for CT-0003 to verify accuracy
6. **Post pending GRNs** (GRN-2026-0003 is CONFIRMED, not POSTED)

---

## Technical Debt

1. **Supplier Migration**: Move data from Supplier to Vendor model
2. **Quality Status Fix**: `AVAIL` should be `is_available=True`
3. **Template Cleanup**: Some templates reference non-existent fields
4. **Test Coverage**: Need unit tests for posting workflows
5. **Performance**: Large inventory views need pagination/caching

---

## Recommended Development Order

```
Phase 1: Foundation (Now)
├── Complete warehouse locations
├── Test all document workflows
└── Fix remaining bugs

Phase 2: Production (Next)
├── Work Order system
├── BOM management
├── Material consumption

Phase 3: Field Service
├── Pocket mode enhancements
├── Rig inventory tracking
├── Reclaim processing

Phase 4: Reporting & Analytics
├── Standard reports
├── Dashboard widgets
├── Export capabilities

Phase 5: Integration
├── Barcode/RFID
├── ERP connection
├── Vendor APIs
```
