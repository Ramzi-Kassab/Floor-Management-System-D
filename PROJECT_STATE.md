# Project State - ARDT Floor Management System

**Last Updated**: January 2026
**Branch**: `full-system-backup`

## System Overview

ARDT Floor Management System (FMS) is a Django-based ERP for managing PDC drill bit manufacturing operations, including inventory management, procurement, supply chain, and field services.

## Current Database State

### Users
| Username | Name | Role |
|----------|------|------|
| admin | Ramzi Kassab | Superuser |

### Inventory Items (16 total)

#### PDC Cutters (CT-PDC Category) - 13 items
| Code | Description | Unit |
|------|-------------|------|
| CT-0001 | 418525 1308 CT31 Drop In | EA |
| CT-0002 | 871781 13MM Long CT200 18C | EA |
| CT-0003 | 738227 1308 CR31 18C | EA |
| CT-0004 | 1039036 1313 CT138 18C | EA |
| CT-0005 | 1176641 1613 CT155 18C | EA |
| CT-0006 | 1228502 1618 CT182 U | EA |
| CT-0007 | 1261321 1613 CT155 U-60 | EA |
| CT-0008 | 2002243 1308 CT188 U-60 | EA |
| CT-0009 | 1162285 1313 CT154 U | EA |
| CT-0010 | 2002299 1613 CT187 U-60 | EA |
| CT-0011 | 2002244 1313 CT188 U-60 | EA |
| CT-0012 | 2002186 1313 CT187 U-60 | EA |
| CT-0013 | 1228501 1618 | EA |

#### Test Items (BOD-BLANK Category) - 3 items
| Code | Description |
|------|-------------|
| TEST-BRG-001 | Bearing 6205-2RS |
| TEST-CUT-001 | PDC Cutter 13mm Standard |
| TEST-SEL-001 | Seal Kit Hydraulic |

### Category Hierarchy (42 categories)

```
ROOT
├── BODIES (Bit Bodies)
│   ├── BOD-BLANK (Steel Blanks)
│   ├── BOD-CAST (Cast Bodies)
│   └── BOD-MOLD (Matrix Molds)
├── CUTTERS
│   ├── CT-PDC (PDC Cutters) ← Main category in use
│   ├── CT-IMP (Impregnated Diamond)
│   ├── CT-NAT (Natural Diamond)
│   └── CT-TSP (TSP Cutters)
├── MATRIX (Matrix Materials)
│   ├── MAT-TC (Tungsten Carbide)
│   ├── MAT-CU (Copper Powders)
│   ├── MAT-NI (Nickel Powders)
│   └── MAT-BIND (Binders)
├── NOZZLES
│   ├── NOZ-STD (Standard)
│   ├── NOZ-TC (Tungsten Carbide)
│   └── NOZ-PLUG (Plugs)
├── CONSUMABLES
│   ├── CON-BRAZE (Brazing Alloys)
│   ├── CON-FLUX (Flux)
│   ├── CON-ABRAS (Abrasives)
│   ├── CON-CHEM (Chemicals)
│   └── CON-COAT (Coatings)
├── STEEL (Steel Components)
│   ├── STL-BLADE (Blades)
│   ├── STL-PIN (Pins & Studs)
│   └── STL-RING (Rings & Collars)
├── TOOLS
│   ├── TL-CUT (Cutting Tools)
│   ├── TL-GRIND (Grinding Tools)
│   ├── TL-MEAS (Measuring Tools)
│   └── TL-FIX (Fixtures)
├── SPARE (Spare Parts)
│   ├── SP-CNC (CNC Spares)
│   ├── SP-FURN (Furnace Spares)
│   └── SP-PUMP (Pump Spares)
├── PACKAGING
│   ├── PKG-BOX (Boxes)
│   ├── PKG-WRAP (Wrapping)
│   └── PKG-PROT (Thread Protectors)
└── SAFETY (Safety Equipment)
```

### Customers (8)
| Code | Name | Type |
|------|------|------|
| ARAMCO | Saudi Aramco | OPERATOR |
| NATPET | National Petroleum | OPERATOR |
| HALIBTN | Halliburton | CONTRACTOR |
| SCHLUM | Schlumberger | CONTRACTOR |
| BAKER | Baker Hughes | CONTRACTOR |
| WEATHER | Weatherford | CONTRACTOR |
| SPERRY | Sperry Drilling Services | CONTRACTOR |
| NOV | NOV Inc. | DISTRIBUTOR |

### Rigs (5) - All Saudi Aramco
| Code | Name |
|------|------|
| 088TE | Rig 088TE |
| AD-72 | Rig AD-72 |
| AD-74 | Rig AD-74 |
| GW-88 | Rig GW-88 |
| PA-785 | Rig PA-785 |

### Business Accounts (4)
| Code | Name |
|------|------|
| OIL | Oil Division |
| GAS | Gas Division |
| OFFSHORE | Offshore Division |
| LSTK | LSTK Division |

### Vendors & Suppliers

#### Vendors (New Model)
| Code | Name | Status | Type |
|------|------|--------|------|
| VND-000001 | Halliburton / HDBS | ACTIVE | MATERIALS_SUPPLIER |
| VEND-TEST-001 | Test Supplier Inc. | APPROVED | SUPPLIER |

#### Suppliers (Legacy Model)
| Code | Name | Country |
|------|------|---------|
| VND-000001 | Halliburton / HDBS | - |
| VND-000011 | Eastern Boundary Contracting Est. | KSA |

### Warehouse & Locations
| Warehouse | Code | Locations |
|-----------|------|-----------|
| WH-MAIN | Main Warehouse (ARDT) | RCV-01 (Receiving Area) |

### Current Stock

#### InventoryStock (Simple - for item views)
| Item | Location | Qty On Hand |
|------|----------|-------------|
| CT-0003 | RCV-01 | 5 EA |

#### StockBalance (Detailed - with dimensions)
| Item | Location | Qty | Owner | QC Status |
|------|----------|-----|-------|-----------|
| CT-0003 | RCV-01 | 5 | ARDT (Internal) | Available |

### Transaction Documents

#### Purchase Requisitions (10)
| Number | Title | Status |
|--------|-------|--------|
| REQ-2025-0001 | PR for PDC Cutters | CONVERTED_TO_PO |
| REQ-2025-0003 | PR for PDC Cutters | CONVERTED_TO_PO |
| REQ-2025-0005 | PR for PDC Cutters | CONVERTED_TO_PO |
| REQ-2025-0007 | PR for PDC Cutters | CONVERTED_TO_PO |
| REQ-2025-0010 | PDC Items | CONVERTED_TO_PO |
| REQ-2025-0002 | PR for Bearings (Draft) | DRAFT |
| REQ-2025-0004 | PR for Bearings (Draft) | DRAFT |
| REQ-2025-0006 | PR for Bearings (Draft) | DRAFT |
| REQ-2025-0008 | PR for Bearings (Draft) | DRAFT |
| REQ-2025-0009 | PDC Items | DRAFT |

#### Purchase Orders (10)
| Number | Vendor | Status | Lines |
|--------|--------|--------|-------|
| PO-2026-000001 | Halliburton / HDBS | COMPLETED | 2 |
| PO-2025-000007 | Test Supplier Inc. | SENT | 3 |
| PO-2025-000005 | Test Supplier Inc. | SENT | 3 |
| PO-2025-000003 | Test Supplier Inc. | SENT | 3 |
| PO-2025-000001 | Test Supplier Inc. | SENT | 3 |
| Others | Test Supplier Inc. | DRAFT | 0-2 |

#### Goods Receipt Notes (11)
| Number | PO | Status |
|--------|-----|--------|
| GRN-2026-0003 | PO-2026-000001 | CONFIRMED |
| GRN-2025-0007 | PO-2025-000007 | CONFIRMED |
| GRN-2025-0005 | PO-2025-000005 | CONFIRMED |
| GRN-2025-0003 | PO-2025-000003 | CONFIRMED |
| GRN-2025-0001 | PO-2025-000001 | CONFIRMED |
| Others | Various | DRAFT |

### Reference Data

#### Condition Types
| Code | Name | New? | Saleable? |
|------|------|------|-----------|
| NEW | New | Yes | Yes |
| USED-RET | Used - Retrofit | No | Yes |
| USED-GRD | Used - Ground | No | Yes |
| USED-E&O | Used - E&O | No | Yes |
| REFURB | Refurbished | No | Yes |
| RECERT | Recertified | No | Yes |
| REWORK | Rework | No | No |
| SCRAP | Scrap | No | No |

#### Quality Statuses
| Code | Name | Available? |
|------|------|------------|
| REL | Released | Yes |
| AVAIL | Available | No |
| QRN | Quarantine | No |
| INS | Under Inspection | No |
| BLK | Blocked | No |
| PND | Pending Disposition | No |
| RTN | Return to Vendor | No |
| SCR | Scrap | No |

#### Ownership Types
| Code | Name | ARDT Owned? |
|------|------|-------------|
| OWNED | Owned by ARDT | Yes |
| CLIENT | Client Owned | No |
| CONSIGN-IN | Consignment In | No |
| CONSIGN-OUT | Consignment Out | Yes |

#### Variant Cases (7)
| Code | Name | Condition | Ownership |
|------|------|-----------|-----------|
| NEW-PUR | New Purchased | NEW | ARDT |
| USED-RET | Retrofit (as New) | NEW | ARDT |
| USED-EO | E&O (Excess & Obsolete) | NEW | ARDT |
| USED-GRD | Ground (Surface Damage) | USED | ARDT |
| USED-RCL | Standard Reclaim | USED | ARDT |
| CLI-NEW | Client New | NEW | CLIENT |
| CLI-RCL | Client Reclaim | USED | CLIENT |

#### Location Types (13)
| Code | Name | Stockable |
|------|------|-----------|
| RECEIVING | Receiving Area | Yes |
| WH | Warehouse | Yes |
| QRN | Quarantine | Yes |
| RECV | Receiving | Yes |
| SHIP | Shipping | Yes |
| PROD | Production | Yes |
| WIP | Work in Progress | Yes |
| RIG | Rig Site | Yes |
| CUST | Customer Site | Yes |
| TRANSIT | In Transit | Yes |
| SCRAP | Scrap | Yes |
| HOLD | Hold | Yes |
| RETURN | Returns | Yes |

### Internal Party
| Code | Name | Type |
|------|------|------|
| ARDT | ARDT (Internal) | INTERNAL |

## File Counts
- **Templates**: 100+ HTML files
- **Models**: 80+ Django models
- **Views**: 5600+ lines in inventory views alone
- **Apps**: 15+ Django apps
