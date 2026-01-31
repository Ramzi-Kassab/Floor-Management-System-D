# ARDT Floor Management System - Complete Project Guide

## Table of Contents
1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Business Domain](#business-domain)
5. [Django Apps Reference](#django-apps-reference)
6. [Database & Models](#database--models)
7. [Key Workflows](#key-workflows)
8. [URL Structure](#url-structure)
9. [Frontend Patterns](#frontend-patterns)
10. [Common Commands](#common-commands)
11. [Development Guidelines](#development-guidelines)
12. [Current State & Known Issues](#current-state--known-issues)

---

## Overview

**ARDT Floor Management System** is a comprehensive ERP-style application for **ARDT**, a drill bit manufacturing and repair company. The system manages:
- **PDC Cutter Inventory** - tracking cutters by variant (new, reclaimed, etc.)
- **Drill Bit Designs** (L3/L4) and **BOMs** (L5)
- **Drill Bit Lifecycle** - from receipt to deployment to repair
- **Work Orders / Job Cards** - manufacturing and repair workflows
- **Supply Chain** - purchase orders, GRNs, vendors

**Primary Users**: ARDT warehouse staff, engineers, QC personnel, and management.

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Django 5.1 (Python 3.11+) |
| **Database** | SQLite (`db.sqlite3`) - NOT tracked in git |
| **Frontend** | HTMX + Alpine.js + Tailwind CSS |
| **Icons** | Lucide Icons |
| **Excel Export** | openpyxl |
| **PDF Processing** | PyMuPDF (fitz) for Halliburton PDF extraction |
| **Template Engine** | Django Templates + Jinja2 (for some PDF generation) |

### Frontend Architecture
- **HTMX**: Partial page updates, form submissions, infinite scroll
- **Alpine.js**: Client-side reactivity (column toggles, modals, filters)
- **Tailwind CSS**: Utility-first styling with dark mode support
- **No build step**: CDN-loaded (Tailwind via CDN in development)

---

## Project Structure

```
Floor-Management-System-D/
├── apps/                          # Django applications
│   ├── accounts/                  # User authentication & profiles
│   ├── cutter_map/                # PDF extraction & cutter mapping
│   ├── inventory/                 # Items, variants, stock, GRNs
│   ├── sales/                     # Customers, quotes, orders
│   ├── supplychain/               # POs, vendors, receiving
│   ├── technology/                # Designs, BOMs, HDBS/SMI types
│   └── workorders/                # Work orders, drill bits, job cards
├── config/                        # Django settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── templates/                     # Global templates
│   ├── base.html                  # Main layout with sidebar
│   ├── components/                # Reusable components
│   └── {app_name}/                # App-specific templates
├── static/                        # Static files (CSS, JS, images)
├── data/                          # Data exports (JSON)
├── docs/                          # Documentation & Excel imports
├── backups/                       # Database backups (from ./hv)
├── manage.py
├── requirements.txt
├── CLAUDE.md                      # This file
├── hc                             # Health check script
└── hv                             # Database backup/restore script
```

---

## Business Domain

### Core Concepts

#### Drill Bit Hierarchy
```
Design (L3/L4)                    # Blueprint - what the bit looks like
    └── BOM (L5)                  # Bill of Materials - what cutters to use
         └── Drill Bit           # Physical asset with serial number
              └── Work Order     # Manufacturing or repair job
```

#### Order Levels
| Level | Name | Description |
|-------|------|-------------|
| L3 | Design (No Cutters) | Base design without cutter specifications |
| L4 | Design (With Pockets) | Design with pocket positions defined |
| L5 | BOM | Complete Bill of Materials with cutter assignments |

#### Key Business Terms
- **MAT Code**: Material number (e.g., `1283567M1` for design, `1283567M1-001` for BOM)
- **HDBS**: Halliburton Drill Bit System - classification codes for cutters
- **SMI**: Standard Material Identifier - specific configuration
- **PDC Cutter**: Polycrystalline Diamond Compact cutter (the cutting elements)
- **Blade**: A drill bit has 6 blades, each with multiple cutter positions
- **Pocket**: Individual position on a blade where a cutter is placed

#### Cutter Variant Cases
| Code | Description | Use Case |
|------|-------------|----------|
| NEW-PUR | New Purchased | Fresh from supplier |
| NEW-EO | ENO As New | Evaluated as new condition |
| NEW-RET | Retrofit as New | Retrofitted, counts as new |
| NEW-CLI | Client Stock (LSTK) | Halliburton consignment |
| USED-GRD | ENO Ground | Ground/refurbished |
| USED-RCL | ARDT Reclaimed | Reclaimed by ARDT |
| USED-CLI | Client Used | Customer's used cutters |

---

## Django Apps Reference

### `apps/inventory/` - Inventory Management
**Purpose**: Manage items, variants, stock levels, and documents (GRNs, POs)

**Key Models**:
- `InventoryCategory` - Hierarchical categories with attributes
- `InventoryItem` - Base item (e.g., a cutter type)
- `ItemVariant` - Variant of item (e.g., NEW-PUR variant of cutter)
- `VariantStock` - Stock quantity per variant per location
- `StockLedger` - Immutable ledger of all stock movements
- `GoodsReceivedNote` (GRN) - Receiving documents
- `GRNLine` - Individual lines on a GRN

**Key Views** (`apps/inventory/views.py`):
- `CutterInventoryListView` - Dashboard at `/inventory/cutters/`
- `CutterInventoryExportView` - Excel export at `/inventory/cutters/export/`
- `ItemListView` - Generic item list at `/inventory/`
- `ItemCreateView` / `ItemUpdateView` - Item CRUD

**Key URLs**:
- `/inventory/` - Item list
- `/inventory/cutters/` - PDC Cutter dashboard
- `/inventory/cutters/export/` - Export to Excel
- `/inventory/items/<pk>/` - Item detail
- `/inventory/grn/` - GRN list

### `apps/technology/` - Designs & BOMs
**Purpose**: Manage drill bit designs and bills of materials

**Key Models**:
- `Design` - Drill bit design (L3/L4)
- `BOM` - Bill of Materials (L5)
- `BOMLine` - Individual cutter requirement in BOM
- `DesignPocket` - Pocket position on a design
- `HDBSType` / `SMIType` - Classification types
- `BitSize` - Drill bit sizes

**Key Views** (`apps/technology/views.py`):
- `BOMCreateView` - Create BOM at `/technology/boms/create/`
- `BOMDetailView` - BOM detail at `/technology/boms/<pk>/`
- `DesignListView` - Design list at `/technology/designs/`

**Key URLs**:
- `/technology/designs/` - Design list
- `/technology/boms/` - BOM list
- `/technology/boms/create/` - BOM creation workflow
- `/technology/boms/<pk>/` - BOM detail

### `apps/cutter_map/` - PDF Extraction & Cutter Mapping
**Purpose**: Extract cutter data from Halliburton PDFs and create BOMs

**Key Views** (`apps/cutter_map/views.py`):
- `index` - Main cutter map interface at `/cutter-map/`
- `api_sync_to_erp` - API to create BOM from extracted data (also saves cutter shapes to inventory items)
- `api_cutter_inventory` - API returning PDC cutters with variant stock breakdown, on-order qty, design usage
- `api_cutter_shapes` - API returning saved cutter shape images from `InventoryItem.shape_image_base64`
- `bom_view` - View/edit existing BOM at `/cutter-map/bom/<id>/` (enriches shapes from inventory)
- `bom_readonly` - Read-only BOM view for work orders (enriches shapes from inventory)
- `add_cutter_wizard` - Wizard to add unmatched cutters to inventory
- `_enrich_cutter_shapes_from_inventory()` - Helper that fills missing `cutter_shapes` in source_data from inventory items by MAT #

**Key URLs**:
- `/cutter-map/` - Main interface
- `/cutter-map/bom/<id>/` - View BOM in cutter map
- `/cutter-map/api/cutter-inventory/` - Live cutter inventory with variant stock (Tabulator dialog)
- `/cutter-map/api/cutter-shapes/` - Saved cutter shapes from DB (shape picker)
- `/cutter-map/add-cutter-wizard/` - Add cutter wizard

### `apps/workorders/` - Work Orders & Drill Bits
**Purpose**: Manage drill bit lifecycle, work orders, and job cards

**Key Models**:
- `DrillBit` - Physical drill bit with serial number
- `BitEvent` - Lifecycle events (received, shipped, etc.)
- `WorkOrder` - Manufacturing or repair job
- `Location` - Warehouse, shop floor, rig, etc.
- `CutterEvaluationMatrix` - Blade × position evaluation grid
- `RouterSheetEntry` - Process step tracking

**Key Views**:
- `views_drillbit.py` - Drill bit CRUD and actions
- `views_jobcard.py` - Job card/work order management

**Key URLs**:
- `/work-orders/drill-bits/` - Drill bit list
- `/work-orders/drill-bits/new/` - Register new drill bit
- `/work-orders/drill-bits/<pk>/` - Drill bit detail
- `/workorders/dashboard/` - Work order dashboard
- `/workorders/enhanced/` - Enhanced work order list

### `apps/supplychain/` - Purchase Orders & Vendors
**Purpose**: Manage vendors and purchase orders

**Key Models**:
- `Vendor` - Supplier information
- `PurchaseOrder` - Purchase order header
- `PurchaseOrderLine` - Individual PO lines

**Key URLs**:
- `/supplychain/vendors/` - Vendor list
- `/supplychain/purchase-orders/` - PO list

### `apps/sales/` - Customers & Sales
**Purpose**: Manage customers and sales orders

**Key Models**:
- `Customer` - Customer master data
- `SalesOrder` - Sales order header

---

## Database & Models

### Key Model Relationships

```
InventoryCategory (hierarchical)
    └── InventoryItem
         ├── ItemAttributeValue (specs like size, type)
         └── ItemVariant (NEW-PUR, USED-RCL, etc.)
              └── VariantStock (qty per location)

Design (L3/L4)
    ├── DesignPocket (positions)
    └── BOM (L5)
         ├── BOMLine → InventoryItem
         └── DrillBit (linked via brazing_bom or system_bom)
              └── BitEvent (lifecycle tracking)

PurchaseOrder
    └── PurchaseOrderLine → InventoryItem
         └── GRNLine → GoodsReceivedNote
              └── StockLedger (immutable record)
```

### StockLedger - Source of Truth
The `StockLedger` model is an **immutable ledger** for all stock movements:
- Never updated or deleted, only new entries or reversals
- Fields: `qty_delta` (signed quantity), `transaction_type`, `item`, `variant`, `location`
- Stock balances calculated by summing `qty_delta`

### Important Fields

**InventoryItem**:
- `code` - Unique item code (e.g., `CUT-0001`)
- `mat_number` - SAP Legacy MAT No. (used for HDBS code matching)
- `category` - FK to InventoryCategory
- `is_blocked` - Prevents deletion
- `notes` - Free text remarks
- `shape_image_base64` - Cutter shape image as base64 data URI (linked by MAT # during BOM sync)

**ItemVariant**:
- `variant_case` - FK to VariantCase (NEW-PUR, etc.)
- `erp_item_no` - ERP item number (globally unique)
- `customer` - FK to Customer (for consignment)
- `account` - Account code (e.g., "LSTK")

**BOM**:
- `source_data` - JSONField storing complete PDF extraction data
- `design` - FK to Design
- `brazing_mat_no` / `system_mat_no` - MAT codes

---

## Key Workflows

### 1. BOM Creation from PDF
```
1. User goes to /technology/boms/create/
2. Selects a Design (L3/L4)
3. Clicks "Open Cutter Map" → /cutter-map/?design_id=X
4. Uploads Halliburton PDF
5. System extracts blade/cutter data
6. User reviews and edits cutter assignments
7. Clicks "Create BOM" → api_sync_to_erp
8. BOM created with source_data saved
9. If unmatched cutters → redirect to Cutter Wizard
```

### 2. Drill Bit Registration
```
1. User goes to /work-orders/drill-bits/new/
2. Enters serial number (6-8 digits)
3. Selects Design and optionally BOM
4. Redirected to First Event Wizard
5. Chooses initial event (Received, Intake, In Production, Skip)
6. Drill bit created with initial status
```

### 3. Stock Receipt (GRN)
```
1. Create GRN at /inventory/grn/create/
2. Add lines with PO reference
3. Enter received quantities
4. Post GRN → creates StockLedger entries
5. Stock levels updated automatically
```

### 4. Cutter Inventory Export
```
1. Go to /inventory/cutters/
2. Optionally apply column filters
3. Click "Export Excel"
4. Choose: visible/all columns, all/filtered records
5. Download Excel file with formatting
```

---

## URL Structure

### URL Patterns by App

| App | URL Prefix | Config File |
|-----|------------|-------------|
| inventory | `/inventory/` | `apps/inventory/urls.py` |
| technology | `/technology/` | `apps/technology/urls.py` |
| cutter_map | `/cutter-map/` | `apps/cutter_map/urls.py` |
| workorders | `/work-orders/`, `/workorders/` | `apps/workorders/urls.py` |
| supplychain | `/supplychain/` | `apps/supplychain/urls.py` |
| sales | `/sales/` | `apps/sales/urls.py` |

### API Endpoints
Most API endpoints follow the pattern: `/{app}/api/{resource}/`
- `/cutter-map/api/sync-to-erp/` - Create BOM from cutter map (POST)
- `/cutter-map/api/cutter-inventory/` - Live PDC cutter inventory with variant stock breakdown (GET, optional `?design_id=`)
- `/cutter-map/api/cutter-shapes/` - Saved cutter shape images from DB (GET)
- `/cutter-map/api/create-cutters/` - Create missing inventory items (POST)
- `/cutter-map/api/activate-bom/<id>/` - Activate a BOM (POST)
- `/work-orders/api/drill-bits/search/` - Search drill bits
- `/inventory/api/categories/<pk>/attributes/` - Get category attributes

---

## Frontend Patterns

### Alpine.js Components
Most pages use Alpine.js for interactivity:

```javascript
// Typical page structure
<div x-data="pageName()" x-init="init()">
    // Component content
</div>

<script>
function pageName() {
    return {
        // State
        columns: { col1: true, col2: false },
        freezePanes: false,

        // Methods
        init() {
            this.loadPreferences();
        },
        savePreferences() {
            localStorage.setItem('key', JSON.stringify(this.columns));
        }
    };
}
</script>
```

### Column Filtering (Cutter Inventory)
The cutter inventory page has Excel-like column filters:
- Click column header to open filter menu
- Sort ascending/descending
- Filter by specific values (checkboxes)
- Custom filter (contains, equals, etc.)
- Multiple filters can be active simultaneously
- Visual indicator (blue header) for filtered columns
- "Clear All Filters" button

### Cutter Selection Dialog (Cutter Map)
The cutter map's "Select Cutter MAT" dialog uses **Tabulator.js** with live inventory data:
- Data loaded from `/cutter-map/api/cutter-inventory/` (pre-loaded on page load)
- Columns: BOM, MAT #, Size, Type, Chamfer, Family, Total, variant breakdown (New, ENO, Retro, Ground, Reclaim, LSTK, Cli Used), On Order
- Toggle filters: **Available Only**, **On Order**, **Used for Design** (cutters in prior BOMs for same design)
- **Variants** column toggle to show/hide stock breakdown
- Number filters (min >=) on all stock/variant columns
- Size lock/unlock for compatibility control
- Three open modes: `openMatTableDialog()` (edit BOM), `openAddNewCutterDialog()` (add to blade), `openMatTableDialogForNewItem()` (new BOM item)
- All share `_buildMatTable()` for Tabulator initialization

### Cutter Shape Management
- Shapes extracted from Halliburton PDFs (base64) and stored in `BOM.source_data.cutter_shapes` (keyed by group index)
- During BOM sync (`api_sync_to_erp`), shapes are also saved to `InventoryItem.shape_image_base64` (linked by MAT #)
- When loading BOMs, `_enrich_cutter_shapes_from_inventory()` fills missing shapes from inventory items
- Shape picker in Deep Edit modal: "Saved" button loads shapes from `/cutter-map/api/cutter-shapes/`, or user can upload from PC

### CL-Driven Mode (Cutter Layout)
- Toggle in both **Edit Layout** and **Deep Edit** tabs (shared `editState.clDrivenMode` state)
- When OFF: BOM Qty is read-only, CL add/replace/delete does not change BOM counts
- When ON: All CL operations (add, replace, delete, paste row) automatically update BOM Qty
- BOM Qty input fields disabled unless CL-Driven is enabled

### LocalStorage Keys
- `cutterInventoryPrefs` - Column visibility, freeze mode
- `cutterInventoryPageSize` - Page size preference
- Various other preferences per page

---

## Common Commands

### Database Management
```bash
# Health check (runs migrations, seeds, git status)
./hc

# Backup database
./hv

# Restore from backup
./hv restore

# List backups
./hv list

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Seeding Data
```bash
# Seed all data
python manage.py seed_all

# Seed test designs
python manage.py seed_test_designs

# Seed drill bit inventory
python manage.py seed_drillbit_inventory --confirm

# Import cutters from Excel
python manage.py import_cutters_excel --confirm

# Import stock from ERP On-hand.xlsx
python manage.py import_stock_from_onhand --confirm

# Clear test cutter data
python manage.py clear_test_cutters --confirm
```

### Development
```bash
# Run development server
python manage.py runserver 0.0.0.0:8000

# Shell
python manage.py shell

# Check for issues
python manage.py check
```

---

## Development Guidelines

### Code Style
- Follow Django conventions
- Use class-based views where appropriate
- Keep views focused (single responsibility)
- Use `select_related` and `prefetch_related` for optimization

### Template Conventions
- All pages extend `base.html` (includes sidebar, topnav, dark mode)
- Use `{% block content %}` for page content
- Use `{% block extra_css %}` and `{% block extra_js %}` for page-specific assets
- Alpine.js components defined in `<script>` at bottom of template
- Use Lucide icons: `<i data-lucide="icon-name" class="w-4 h-4"></i>`
- **Cutter map pattern**: Large standalone pages use `.cutter-map-app` wrapper with scoped CSS and `margin: -1.5rem` to cancel base layout padding for full-width display

### Model Conventions
- Use `is_active` soft delete pattern
- Use `created_at`, `updated_at` timestamps
- Use `created_by` for audit trail
- FK fields use `related_name` for reverse access

### Error Handling
- Use Django messages framework for user feedback
- Catch `ProtectedError` for FK constraint violations
- Validate forms in `clean()` and `form_valid()`

### Testing Changes
1. Always backup database before risky operations: `./hv`
2. Test in browser with multiple scenarios
3. Check Django admin for data integrity
4. Review console for JavaScript errors

---

## Current State & Known Issues

### Data State (as of Jan 23, 2026)
- **301+ PDC cutter items** imported from Excel
- **848+ item variants** with unique ERP numbers
- **14 designs** in database
- **3+ BOMs** created
- **354 attributes** defined
- **42 inventory categories**

### Known Issues
1. **SMI Types**: Not seeding properly (missing bit sizes)
2. **PDF Extraction**: Only works with Halliburton PDF format
3. **Tailwind CDN**: Console warning about CDN usage (not critical)
4. **Alpine x-collapse**: Plugin warning (not critical)

### Recent Enhancements (Jan 23, 2026)
- **Export Dialog**: Column and record filtering options for Excel export
- **Multi-Column Filters**: Can filter multiple columns simultaneously
- **Filter Indicators**: Visual indicators for active column filters
- **Statistics Dashboard**: Comprehensive variant totals and health metrics
- **Item Code Generation**: Fixed to skip existing codes

### Recent Enhancements (Jan 28, 2026)
- **Cutter Shapes linked to PDC Cutters by MAT #**: `InventoryItem.shape_image_base64` field stores cutter shape images; saved during BOM sync, enriched on BOM load
- **Shape Picker in Deep Edit**: "Saved" button in cutter modal opens a grid of DB-saved shapes (from `/cutter-map/api/cutter-shapes/`)
- **Live Cutter Inventory in Selection Dialog**: Replaced hardcoded test data with real-time inventory from `/cutter-map/api/cutter-inventory/`, showing variant stock breakdown (New, ENO, Retro, Ground, Reclaim, LSTK, Client Used), on-order quantities, and design usage flags
- **Toggle Filters**: Available Only, On Order, Used for Design; plus Variants column toggle
- **Number Filters**: Min >= filters on all stock/variant/on-order columns
- **PDF BOM Table Cleanup**: Removed shape images from BOM table index column in generated PDF (shapes still in CL circles and group legend)
- **CL-Driven BOM Qty Gating**: Deep Edit tab now has CL-Driven toggle; all 7 code paths (add, replace, delete, paste, modal save, context add) gated behind `editState.clDrivenMode`
- **PDF Group Shape Extraction**: Drawing-based table cell detection using filled rectangles; standalone number detection alongside comma-separated groups
- **Cutter Map Sidebar Integration**: Cutter map page (`index.html`) now extends `base.html`, gaining the sidebar navigation, topnav with dark mode toggle, and consistent layout. CSS selectors scoped to `.cutter-map-app` to avoid conflicts with Tailwind base styles. Negative margin on wrapper cancels base layout padding for edge-to-edge display.

### Recent Enhancements (Jan 31, 2026)
- **BOM Create Design Table Filters & Sort**: `/technology/boms/create/` design selection table now has Excel-style column filters and sort on all data columns (Level, MAT No., HDBS Type, Size, Status, BOMs). Click header to open dropdown with Sort Asc/Desc, value checkboxes, search within values, Select All toggle. Blue header text indicates active filter. Works alongside existing search box. Template: `templates/technology/bom_create_builder.html`. Filter dropdown HTML is placed between `{% endblock page_header %}` and `{% block content %}`.
- **PDF Group Shape Extraction Robustness**: Fixed `extract_images()` in `apps/cutter_map/utils/pdf_extractor.py` to handle all edge cases:
  1. **All image placements iterated**: `page.get_image_rects(xref)` now loops over ALL rects (not just `rects[0]`), so when the same image xref is placed at multiple positions (e.g. two group rows), every placement is collected.
  2. **Synthetic cell bounds**: `_detect_group_table_cells()` now synthesises cells from group text Y bounds when no PDF drawing boundary exists for a row. Previously, rows without border/background drawings were silently missed.
  3. **Fallback classifier**: Image classification Step 3 fallback (branch #4) no longer requires `not group_table_cells` — it also runs when cells exist but an image missed all of them. Constrained by `_in_group_column_x()` (uses detected column X range with column-width tolerance) and Y band from `group_data` to prevent CL-area images from leaking in.
  4. **Helper `_in_group_column_x()`**: New function that checks image center against the detected shape column X range (with one-column-width tolerance), falling back to broad heuristic only when no cells exist.

### PDF Extractor Architecture Notes
The PDF extraction pipeline in `apps/cutter_map/utils/pdf_extractor.py` follows this flow:
```
extract_pdf_data(pdf_path)            # Main entry point
  ├── extract_words_with_style(page)  # Step 1: text with coordinates
  ├── extract_shapes(page)            # Step 3: vector drawings
  ├── extract_header(words)           # Step 4: header metadata
  ├── extract_bom(words, shapes)      # Step 5: BOM table rows
  ├── extract_blades_v2(raw_words)    # Step 6: blade/CL data
  ├── extract_groups(words, raw_words)# Step 7: group legend → (groups, has_legend, group_data, group_format)
  └── extract_images(page, doc, group_data, group_format)  # Step 8: images
       ├── _detect_group_table_cells()  # Find shape column cells from PDF drawings
       ├── Step 2: Collect images (all placements per xref, dedup by rect)
       ├── Step 3: Classify (logo, group shape via cell match, drill bit face, fallback)
       └── Step 4: Match group shapes to group text via _match_group_text_to_row()
```
- `group_format` can be `'comma'`, `'multi_row'`, `'vertical'`, or `'unknown'`
- `group_data` for multi_row: `[{'values': '2', 'parsed': [2], 'y': 55.1, 'y1': 62.3, 'x0': 850.5}, ...]`
- `_detect_group_table_cells()` identifies shape column from filled-rectangle drawings; synthesises cells for unmatched group text rows
- Test PDFs in `docs/`: `2030271.pdf`, `13472099_B.pdf`, `1248668M.pdf`, `1283277_B.pdf`, `2020054_B.pdf`
- To test extraction: `DJANGO_SETTINGS_MODULE=ardt_fms.settings python3 -c "import django; django.setup(); from apps.cutter_map.utils.pdf_extractor import extract_pdf_data; r = extract_pdf_data('docs/2030271.pdf'); print(r['images']['group_shapes'])"`

### Login Credentials (Test)
- **Password for all users**: `Ardt@2025`
- **Sample users**: `r.kassab`, `g.escobar`, `m.irshad`

---

## Quick Reference

### Important File Locations

| Purpose | File |
|---------|------|
| Main URL config | `config/urls.py` |
| Django settings | `ardt_fms/settings.py` (`DJANGO_SETTINGS_MODULE=ardt_fms.settings`) |
| Base template | `templates/base.html` |
| Sidebar | `templates/includes/sidebar.html` |
| Top Navigation | `templates/includes/topnav.html` |
| Cutter inventory | `templates/inventory/cutter_inventory_list.html` |
| Cutter map (main) | `templates/cutter_map/index.html` |
| Item form | `templates/inventory/item_form.html` |
| Drill bit list | `templates/workorders/drillbit_list_enhanced.html` |
| PDF template (Jinja2) | `apps/cutter_map/utils/templates/pdf_template.html` |
| BOM create page | `templates/technology/bom_create_builder.html` |
| PDF extractor | `apps/cutter_map/utils/pdf_extractor.py` |
| PDF generator | `apps/cutter_map/utils/pdf_generator.py` |

### Key View Classes

| View | File | URL |
|------|------|-----|
| CutterInventoryListView | `apps/inventory/views.py:1540` | `/inventory/cutters/` |
| CutterInventoryExportView | `apps/inventory/views.py:3208` | `/inventory/cutters/export/` |
| ItemCreateView | `apps/inventory/views.py:700+` | `/inventory/items/create/` |
| BOMCreateWithBuilderView | `apps/technology/views.py:2737` | `/technology/boms/create/` |
| DrillBitListEnhancedView | `apps/workorders/views_drillbit.py` | `/work-orders/drill-bits/` |

### Database Queries
```python
# Get PDC cutters with variants
InventoryItem.objects.filter(
    category__code="CUT-PDC",
    is_active=True
).prefetch_related("variants", "attribute_values")

# Get stock for a variant
VariantStock.objects.filter(variant=variant).aggregate(
    total=Sum("quantity_on_hand")
)

# Get consumption from ledger
StockLedger.objects.filter(
    item=item,
    transaction_type="ISSUE",
    transaction_date__gte=date
).aggregate(total=Sum("qty_delta"))
```

---

## Need Help?

1. **Check this file first** for patterns and conventions
2. **Run `./hc`** to ensure database is healthy
3. **Backup with `./hv`** before making changes
4. **Check Django admin** at `/admin/` for data inspection
5. **Review browser console** for JavaScript errors
