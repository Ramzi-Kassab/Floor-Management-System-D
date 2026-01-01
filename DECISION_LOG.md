# Decision Log - ARDT Floor Management System

This document records key architectural and design decisions made during development.

---

## Decision 1: Dual Stock Model Architecture

**Date**: December 2025
**Status**: Implemented

### Context
The system needs to track inventory at two levels:
1. Simple view for item pages (total stock per item/location)
2. Detailed view for reporting (stock by owner, quality status, condition, etc.)

### Decision
Implement two parallel stock models:

```
InventoryStock (Simple)
├── item (FK)
├── location (FK)
├── lot_number
├── serial_number
├── quantity_on_hand
└── quantity_available

StockBalance (Detailed)
├── item (FK)
├── location (FK)
├── lot (FK)
├── owner_party (FK)
├── ownership_type (FK)
├── quality_status (FK)
├── condition (FK)
├── qty_on_hand
└── qty_reserved
```

### Rationale
- **Performance**: Item detail pages need fast queries without joining 5+ dimension tables
- **Reporting**: Financial and audit reports need full dimensional data
- **Flexibility**: Can aggregate StockBalance for complex reports while InventoryStock serves UI

### Consequences
- GRN posting must update BOTH models
- Sync endpoint needed for historical data migration
- `item.total_stock` property reads from `stock_records` (InventoryStock)

### Implementation
- `_update_stock_balance()` in `apps/inventory/views.py` updates both
- Sync endpoint at `/inventory/admin/sync-stock/`

---

## Decision 2: Dual Vendor Model (Vendor vs Supplier)

**Date**: December 2025
**Status**: Implemented (with migration path)

### Context
System has legacy `Supplier` model with existing data. New procurement workflow needs `Vendor` with qualification tracking.

### Decision
Keep both models:

```
Supplier (Legacy)                    Vendor (New)
├── code                            ├── vendor_code
├── name                            ├── name
├── email                           ├── vendor_type
├── phone                           ├── status (ACTIVE, SUSPENDED, etc.)
├── address                         ├── qualification_level
├── country                         ├── tax_id
└── is_active                       ├── registration_number
                                    └── ... (full vendor management)
```

### Rationale
- Existing supplier data (Halliburton/HDBS, Eastern Boundary) must not be lost
- `PurchaseOrder.vendor` FK requires Vendor model
- Full vendor qualification workflow needed for compliance

### Consequences
- PR → PO conversion shows both Vendors and Suppliers in dropdown
- Auto-creates Vendor from Supplier when Supplier is selected
- Long-term: Migrate all Suppliers to Vendors

### Implementation
- `PRConvertToPOView` in `apps/supplychain/views.py` handles both
- Dropdown uses optgroups: "-- Vendors --" and "-- Suppliers (Legacy) --"

---

## Decision 3: HDBS Integration (Halliburton Drill Bit Services)

**Date**: December 2025
**Status**: Planned

### Context
ARDT sources PDC cutters from Halliburton HDBS. Item codes like `418525 1308 CT31 Drop In` are HDBS part numbers.

### Decision
- Store HDBS part numbers in item name/description
- Vendor `VND-000001` = Halliburton / HDBS
- Future: API integration for pricing and availability

### Rationale
- HDBS is primary cutter supplier
- Part numbers must match HDBS catalog for ordering
- Traceability for quality claims

### Alternatives Considered
- **SMI (Smith Bits)**: Different part numbering system
- **ReedHycalog**: Merged with NOV, different system

### Implementation
- Items CT-0001 through CT-0013 are HDBS cutters
- PO-2026-000001 is first real HDBS order

---

## Decision 4: Category-Based Attribute System

**Date**: December 2025
**Status**: Implemented

### Context
Different item categories need different specifications:
- PDC Cutters: size, grade, chamfer type, diamond table thickness
- Steel Bodies: material grade, heat treatment, dimensions
- Consumables: chemical composition, shelf life

### Decision
Dynamic attribute system:

```
InventoryCategory
    └── CategoryAttribute (many-to-many with Attribute)
            ├── attribute_type (TEXT, NUMBER, BOOLEAN, DATE, SELECT)
            ├── min_value / max_value
            ├── options (for SELECT type)
            ├── default_value
            └── conditional_rules (JSON)

InventoryItem
    └── ItemAttributeValue
            ├── text_value
            ├── number_value
            ├── boolean_value
            └── date_value
```

### Rationale
- Categories define the "template" of required attributes
- Items store actual values
- Conditional rules enable dependent fields (e.g., chamfer_size only if chamfer_type != NONE)

### Implementation
- `apps/inventory/models.py`: Attribute, CategoryAttribute, ItemAttributeValue
- Item forms dynamically render category-specific fields

---

## Decision 5: Variant System for Condition/Ownership Tracking

**Date**: December 2025
**Status**: Implemented

### Context
Same physical item (e.g., 1308 cutter) exists in multiple states:
- New purchased from vendor
- Reclaimed from field
- Client-owned on consignment

### Decision
Variant Case system:

```
VariantCase (Master data)
├── code: NEW-PUR, USED-RCL, CLI-NEW, etc.
├── condition: NEW, USED
├── ownership: ARDT, CLIENT
└── acquisition: PURCHASED, RECLAIMED

ItemVariant
├── base_item (FK to InventoryItem)
├── variant_case (FK to VariantCase)
├── customer (optional FK)
├── account (optional FK)
└── separate stock tracking via VariantStock
```

### Rationale
- Single item master with multiple "faces"
- Clear ownership and condition tracking
- Financial segregation (client stock vs ARDT stock)

### Variant Cases Defined
| Code | Condition | Ownership | Use Case |
|------|-----------|-----------|----------|
| NEW-PUR | NEW | ARDT | Fresh purchase from vendor |
| USED-RET | NEW | ARDT | Retrofit items (like new) |
| USED-EO | NEW | ARDT | Excess & Obsolete |
| USED-GRD | USED | ARDT | Ground cutters |
| USED-RCL | USED | ARDT | Standard reclaim |
| CLI-NEW | NEW | CLIENT | Client's new stock |
| CLI-RCL | USED | CLIENT | Client's reclaimed stock |

---

## Decision 6: Document Workflow States

**Date**: December 2025
**Status**: Implemented

### Context
Documents need approval workflows with clear state transitions.

### Decision
Standard state machines for each document type:

```
Purchase Requisition:
  DRAFT → SUBMITTED → APPROVED → CONVERTED (to PO)
              ↓
           REJECTED

Purchase Order:
  DRAFT → APPROVED → SENT → PARTIALLY_RECEIVED → COMPLETED
              ↓                      ↓
           REJECTED              CANCELLED

Goods Receipt Note:
  DRAFT → PENDING_QC → CONFIRMED → POSTED
              ↓
           REJECTED

Stock Issue / Transfer / Adjustment:
  DRAFT → PENDING → APPROVED → POSTED
              ↓
           CANCELLED
```

### Rationale
- Clear audit trail
- Approval gates for compliance
- Prevents accidental modifications after posting

---

## Decision 7: Party Model for Multi-Entity Ownership

**Date**: December 2025
**Status**: Implemented

### Context
Stock can be owned by:
- ARDT (internal)
- Customers (client-owned)
- Vendors (consignment)
- Rigs (field locations)

### Decision
Generic `Party` model:

```
Party
├── code
├── name
├── party_type (INTERNAL, CUSTOMER, VENDOR, RIG)
├── customer (nullable FK)
├── vendor (nullable FK)
├── rig (nullable FK)
└── can_own_stock (boolean)
```

### Rationale
- Single FK in StockBalance instead of multiple nullable FKs
- Flexible for future entity types
- Supports ownership transfers between any party types

### Current Data
Only `ARDT - ARDT (Internal)` party exists (party_type: INTERNAL)

---

## Decision 8: Unit of Measure System

**Date**: December 2025
**Status**: Implemented

### Context
Items measured in various units:
- Cutters: EA (each), PC (piece)
- Powder: KG, LB, G
- Liquids: L, GAL, ML
- Length: M, FT, IN, MM

### Decision
Comprehensive UOM system with conversions:

```
UnitOfMeasure
├── code
├── name
├── unit_type (COUNT, WEIGHT, LENGTH, VOLUME, etc.)
├── is_si_base
├── is_packaging
├── base_unit (FK to self)
└── conversion_factor

ItemUOMConversion
├── item (FK)
├── from_uom (FK)
├── to_uom (FK)
├── conversion_factor
└── is_default
```

### Rationale
- Items can have multiple valid UOMs (order in boxes, use individually)
- Automatic conversion for inventory calculations
- SI and imperial support for international operations

---

## Decision 9: Quality Control Integration

**Date**: December 2025
**Status**: Implemented

### Context
Received goods need QC inspection before release to inventory.

### Decision
- GRN has `requires_qc` flag (from vendor or item settings)
- QC workflow: DRAFT → PENDING_QC → CONFIRMED → POSTED
- `qty_received` vs `qty_accepted` tracking
- Three-way matching: PO qty vs GRN qty vs Invoice qty

### Quality Statuses
| Code | Available? | Purpose |
|------|------------|---------|
| REL | Yes | Released for use |
| AVAIL | No | Available (legacy) |
| QRN | No | Quarantine |
| INS | No | Under Inspection |
| BLK | No | Blocked |
| PND | No | Pending Disposition |
| RTN | No | Return to Vendor |
| SCR | No | Scrap |

---

## Decision 10: Costing Methods

**Date**: December 2025
**Status**: Implemented (AVG default)

### Context
Need to value inventory for financial reporting.

### Decision
Support three costing methods per item:

```python
COSTING_METHOD_CHOICES = [
    ('AVG', 'Weighted Average'),  # Default
    ('FIFO', 'First In First Out'),
    ('STD', 'Standard Cost'),
]
```

### Implementation
- Default: Weighted Average
- Each GRN posting updates average cost
- StockBalance tracks `avg_unit_cost` and `total_cost`
- Future: FIFO layer tracking

---

## Pending Decisions

### P1: ERP Integration Strategy
- SAP vs Oracle vs standalone
- Real-time vs batch sync
- Master data ownership

### P2: Barcode/RFID Implementation
- Label format standards
- Scanner hardware selection
- Mobile app requirements

### P3: Multi-Warehouse Deployment
- WH-MAIN is only warehouse
- Need: Production floor, QC area, Shipping
- Inter-warehouse transfer workflow
