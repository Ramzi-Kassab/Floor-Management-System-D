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
- **ERP Automation** - browser-based D365 automation (record, convert, execute)

**Primary Users**: ARDT warehouse staff, engineers, QC personnel, and management.
**Server**: Runs locally on `localhost:8001` (`python manage.py runserver 0.0.0.0:8001`).

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
| **Browser Automation** | Playwright (sync API) for D365 ERP recording & execution |
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
│   ├── erp_automation/             # ERP browser automation (Record → Convert → Execute)
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
- `/cutter-map/api/quick-add-smi-type/` - Quick-create SMI Type (POST, resolves HDBS from design_id)
- `/cutter-map/api/quick-add-iadc-code/` - Quick-create IADC Code (POST)
- `/cutter-map/api/dropdown-data/` - HDBS types and bit sizes for dropdowns (GET)

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

### `apps/erp_automation/` - ERP Browser Automation
**Purpose**: Record browser actions on D365/ERP, convert recordings to executable workflows, execute workflows against parsed job card data. Runs locally on `localhost:8001`.

**Key Models**:
- `Locator` - UI element locator with multiple fallback strategies (name, application, page_context, is_dynamic, default_timeout)
- `LocatorStrategy` - Individual strategy for a locator (strategy_type: id/aria-label/name/css/xpath/text/role, value, priority, success/failure counts)
- `Workflow` - Sequence of automation steps (name, target_url, application, condition_field, status: draft/active/archived)
- `WorkflowStep` - Single step in workflow (order, action_type, locator FK, value_static/value_field/value_template, condition_value, wait_after, continue_on_error). `get_value(row_data, context)` resolves `{{FIELD_NAME}}` templates from job data.
- `RecordingSession` - Browser recording session (name, target_url, status: recording/completed/failed/cancelled, job_data FK, generated_workflow FK)
- `RecordedAction` - Single captured action (order, action_type, element_tag/id/name/class/xpath/css/text/aria_label/placeholder, input_value, locator_strategies JSON, page_url)
- `WorkflowExecution` - Execution run tracking (workflow FK, job_data FK, status: pending/running/success/failed, row_data JSON, error_message)
- `StepExecution` - Per-step execution result (locator_strategy_used FK, retry_count, error_message)
- `ERPJobData` - Parsed job card data ready for ERP (work_order_number, serial_number, size_inches, smi_type, account, route FK, item_number, status: DRAFT/READY/SENT/COMPLETED/ERROR). `get_row_data()` returns dict for template substitution.
- `ERPRoute` - Production route with selection criteria (route_number, bit_type, level, size_class, has_port, repair modifiers)
- `FieldMapping` - Excel column to ERP field mapping (excel_column, erp_field, transform_function)
- `ItemCounter` - Sequential counter for auto-generated item numbers per account type

**Key Services** (`apps/erp_automation/services/`):
- `recorder.py` - Playwright-based browser recorder. Runs in background thread with queue communication. Injects JS to capture clicks/fills/selects. SPA re-injection via `page.on("framenavigated")` for D365 navigation. Uses `no_viewport=True` for desktop-like experience.
- `executor.py` - Workflow executor using Playwright. Opens browser, runs steps sequentially. Handles ADFS login, `navigate` action, D365 custom dropdowns (falls back to `click()` for non-`<select>` elements).
- `locator_engine.py` - Smart locator resolution. Tries strategies in priority order (5s timeout each). Searches main page AND all child frames/iframes for D365 compatibility. `_create_locator()` accepts Page or Frame target.
- `job_card_parser.py` - Parses Job Card Excel files into `ERPJobData` records. Extracts WO number, serial, size, type, cutter BOM, repair modifiers.
- `route_selector.py` - Auto-selects `ERPRoute` based on bit size, port, repair modifiers.

**Key Management Commands**:
- `create_workflow_from_recording` - Converts a `RecordingSession` into a `Workflow` with proper `Locator`/`LocatorStrategy`/`WorkflowStep` models. Smart features: deduplicates click+fill pairs, maps `select`→`click` for D365, strips dynamic ID prefixes for `contains(@id)` xpath, generates value templates from recorded input, sequential step numbering, orphaned locator cleanup on regeneration. Called from UI via "Quick Convert" button or terminal.
- `seed_erp_routes` - Seeds `ERPRoute` records from Excel
- `import_erp_data` - Imports ERP data
- `seed_erp_chain` - Seeds complete ARAMCO FC Repair ERP chain: 13 workflows (login, navigate, create product, capture item#, dimensions, variants, BOM version, BOM copy, BOM lines, approve+activate, route, release, movement journal), 161 steps, 108 locators, 1 chain with 13 links. Use `--force` to recreate, `--dry-run` to preview.

**Key Views** (`apps/erp_automation/views.py`):
- `DashboardView` - Overview at `/erp-automation/`
- `RecordingView` - Start/manage recordings at `/erp-automation/record/`
- `RecordingDetailView` - Review captured actions at `/erp-automation/record/<pk>/`
- `start_recording` / `stop_recording` / `poll_recording` - Recording lifecycle endpoints
- `quick_convert_recording` - POST endpoint, calls `create_workflow_from_recording` via `call_command()`
- `convert_recording_to_workflow` - Manual conversion endpoint
- `JobDataListView` / `JobDataDetailView` / `JobDataUploadView` - Job data CRUD
- `api_execute_job_data` - Execute workflow for a job data record
- `api_job_data_clipboard` - Clipboard data for recording helper
- `api_generate_item_number` - Auto-generate next item number per account
- `CredentialsView` - Session-based ERP credential management
- `api_workflow_steps` - GET all steps for a workflow as JSON with locator details
- `api_step_create` / `api_step_update` / `api_step_delete` - Workflow step CRUD
- `api_locator_create` / `api_locator_update` - Locator CRUD with strategy replacement
- `api_locator_detail` - Full locator details with strategies (GET)
- `api_locator_search` - Search locators by name for autocomplete (GET, max 30)

**Key URLs**:
- `/erp-automation/` - Dashboard
- `/erp-automation/record/` - Recording interface
- `/erp-automation/record/<pk>/` - Recording detail
- `/erp-automation/record/<pk>/quick-convert/` - Quick convert to workflow (POST)
- `/erp-automation/workflows/` - Workflow list
- `/erp-automation/workflows/<pk>/` - Workflow detail
- `/erp-automation/job-data/` - Job data list
- `/erp-automation/job-data/upload/` - Upload job card Excel
- `/erp-automation/job-data/<pk>/` - Job data detail
- `/erp-automation/credentials/` - ERP credentials
- `/erp-automation/routes/` - Routes reference list
- `/erp-automation/excel/` - Excel handler
- `/erp-automation/mappings/` - Field mappings
- `/erp-automation/api/workflows/<pk>/steps/` - List workflow steps (GET)
- `/erp-automation/api/workflows/<pk>/steps/create/` - Create step (POST)
- `/erp-automation/api/workflows/<pk>/steps/<pk>/update/` - Update step (POST)
- `/erp-automation/api/workflows/<pk>/steps/<pk>/delete/` - Delete step (POST)
- `/erp-automation/api/locators/create/` - Create locator with strategies (POST)
- `/erp-automation/api/locators/<pk>/update/` - Update locator & strategies (POST)
- `/erp-automation/api/locators/<pk>/detail/` - Locator details with strategies (GET)
- `/erp-automation/api/locators/search/?q=` - Search locators by name (GET)

**D365 Technical Notes**:
- **Dynamic ID Prefixes**: D365 prepends page-specific prefixes to element IDs (e.g., `ecoresproductdetailsextendedgrid_2_SystemDefinedNewButton`). Locators use `contains(@id, "stableId")` XPath instead of exact `#id`.
- **Custom Dropdowns**: D365 never uses native `<select>` elements — all dropdowns are custom divs/lis/spans with ARIA roles. `select_option()` fails; must use `click()`.
- **SPA Navigation**: URL changes without full page loads. Synthetic `navigate` events created via `setInterval`.
- **Iframes**: Content rendered in iframes. Locator engine searches all frames.
- **ADFS Login**: Microsoft ADFS authentication handled by executor before workflow begins.

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

RecordingSession (browser recording)
    └── RecordedAction (captured clicks/fills/selects)
         └── locator_strategies JSON (generated strategies)

Workflow (executable automation)
    ├── WorkflowStep → Locator → LocatorStrategy (multi-fallback)
    ├── WorkflowExecution → StepExecution (run tracking)
    └── FieldMapping (Excel ↔ ERP field mapping)

ERPJobData (parsed job card)
    ├── ERPRoute (auto-selected production route)
    ├── RecordingSession (optional clipboard helper)
    └── WorkflowExecution (execution runs)
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
- `smi_type` - FK to SMIType (optional, set via Review BOM modal)
- `status` - CharField choices: DRAFT, ACTIVE, OBSOLETE

**Design** (important fields for HDBS/SMI resolution):
- `hdbs_type` - **CharField** (NOT FK) storing HDBS name text (e.g., "GT65RHS")
- `size` - FK to BitSize
- `iadc_code_ref` - FK to IADCCode (optional)

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

### 5. ERP Automation: Record → Convert → Execute
```
1. Upload Job Card Excel at /erp-automation/job-data/upload/
   → Parser extracts WO number, serial, size, type, cutter BOM, etc.
   → ERPJobData record created with status READY
2. Set ERP credentials at /erp-automation/credentials/
3. Go to /erp-automation/record/ → Start Recording
   → Playwright browser opens on D365 sandbox
   → User performs "Create Released Product" flow manually
   → All clicks, fills, selects captured with smart locators
   → Live action panel shows captured actions in real-time
4. Stop Recording → redirected to /erp-automation/record/<pk>/
   → Review all captured actions + locator strategies
5. Click "Quick Convert" → auto-creates workflow
   → Deduplicates click+fill pairs, maps values to templates
   → Generates D365-safe locators with contains-xpath fallbacks
   → Maps select→click (D365 uses custom dropdowns, not native <select>)
6. Go to /erp-automation/jobs/<pk>/ → Click Execute
   → Workflow runs against job data, fills ERP fields automatically
   → Status updates: READY → SENT → COMPLETED or ERROR
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
| erp_automation | `/erp-automation/` | `apps/erp_automation/urls.py` |

### API Endpoints
Most API endpoints follow the pattern: `/{app}/api/{resource}/`
- `/cutter-map/api/sync-to-erp/` - Create BOM from cutter map (POST)
- `/cutter-map/api/cutter-inventory/` - Live PDC cutter inventory with variant stock breakdown (GET, optional `?design_id=`)
- `/cutter-map/api/cutter-shapes/` - Saved cutter shape images from DB (GET)
- `/cutter-map/api/create-cutters/` - Create missing inventory items (POST)
- `/cutter-map/api/activate-bom/<id>/` - Activate a BOM (POST)
- `/work-orders/api/drill-bits/search/` - Search drill bits
- `/inventory/api/categories/<pk>/attributes/` - Get category attributes
- `/workorders/<wo_pk>/router-sheet/<step>/api-scan/` - QR scan start/complete/skip router step (POST)
- `/erp-automation/api/job-data/<pk>/execute/` - Execute workflow for a job data record (POST)
- `/erp-automation/api/job-data/<pk>/clipboard/` - Get clipboard data for recording helper (GET)
- `/erp-automation/record/<pk>/quick-convert/` - Auto-convert recording to workflow (POST)
- `/erp-automation/record/<pk>/convert/` - Manual convert recording to workflow (POST)

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

# Sync HDBS types from design text fields
python manage.py sync_hdbs_from_designs --confirm

# Seed accounts (11 accounts: LSTK, UR, L3, L4, ARDT, WFD, ARAMCO, RC-LSTK, HALLIBURTON, HAL_REGIONAL, SUB)
python manage.py seed_accounts

# Seed router steps (FC Repair 33 steps, L3/L4 Manufacture 26 steps)
python manage.py seed_router_steps

# Clear test cutter data
python manage.py clear_test_cutters --confirm
```

### ERP Automation Commands
```bash
# Convert a recording to workflow (terminal)
python manage.py create_workflow_from_recording --session <pk> --name "Workflow Name"

# Seed ERP production routes from Excel
python manage.py seed_erp_routes

# Import ERP data
python manage.py import_erp_data

# Seed complete ERP chain (13 workflows, 162 steps, 108 locators)
python manage.py seed_erp_chain          # First time
python manage.py seed_erp_chain --force  # Recreate (deletes existing)
python manage.py seed_erp_chain --dry-run # Preview without changes

# Seed ERP environment URLs (Sandbox + Production)
python manage.py seed_erp_environments
```

### Development
```bash
# Run development server (locally on port 8001)
python manage.py runserver 0.0.0.0:8001

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
1. **PDF Extraction**: Only works with Halliburton PDF format
2. **Tailwind CDN**: Console warning about CDN usage (not critical)
3. **Alpine x-collapse**: Plugin warning (not critical)

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

### Recent Enhancements (Jan 31, 2026 - Session 2)
- **SMI Type / IADC Code / Status in Review BOM Modal**: The "Review BOM Before Saving" modal in the cutter map now includes editable fields for SMI Type (picker modal), IADC Code (dropdown + quick-add), and Status (DRAFT/ACTIVE/OBSOLETE). Values persist across save sessions via hidden inputs updated from API response (`smi_type_id`, `iadc_code_id`, `bom_status` returned by `api_sync_to_erp`).
- **SMI Type Picker Modal**: Full modal with "Select Existing" tab (searchable/filterable list from `/technology/api/hdbs-types/`) and "Quick Create" tab. Auto-selects HDBS Type and Size from the design context. Quick Create resolves HDBS by matching `design.hdbs_type` (CharField) against `HDBSType.hdbs_name` to avoid creating duplicate HDBS records.
- **BOM Update Path Saves All Fields**: `api_sync_to_erp` update path (existing BOM) now saves `smi_type`, `status`, and `iadc_code_ref` on design. Previously only `bom_type` and `system_mat_no` were updated.
- **"Save & go to BOMs List" Button**: Review BOM modal has a second save button that saves the BOM then redirects to `/technology/boms/`. Success dialog also has a "Go to BOMs List" navigation link.
- **HDBS Types List Filters & Sort**: `technology/types/` page now has client-side Excel-style column filters, sort, pagination (25/50/100/All), global search, and Show Inactive toggle. Template: `templates/technology/hdbs_type_list.html`.
- **Column Filter Search-then-Apply Fix**: Fixed bug in all 4 templates with Excel-style column filters where typing a search value and clicking Apply did nothing (hidden checkboxes were still counted). Now only visible checkboxes are considered. Fixed in: `hdbs_type_list.html`, `bom_create_builder.html`, `drillbit_form.html`, `drillbit_list_enhanced.html`.
- **sync_hdbs_from_designs Management Command**: `python manage.py sync_hdbs_from_designs --confirm` scans designs with hdbs_type text values, creates missing HDBSType records, links sizes via M2M, and creates DesignHDBS junction records.

### Recent Enhancements (Jan 31, 2026 - Session 3)
- **Account-Based Work Order System**: Full WO creation workflow driven by `Account` model. Each account (LSTK, UR, L3, L4, ARDT, WFD, ARAMCO, RC-LSTK, HALLIBURTON, HAL_REGIONAL, SUB) has its own WO number format, pricing mode, workflow type, max repairs, delivery location, and reviewer label.
- **Account Model Extended** (`apps/sales/models.py`): Added 15+ config fields — `wo_prefix`, `wo_format` (STANDARD/NUMERIC/SUFFIX), `wo_suffix`, `wo_seq_padding`, `wo_seq_start`, `legacy_wo_format`, `contract_number`, `pricing_mode` (STANDARD/LSTK/ARAMCO/ZERO/REGIONAL), `vendor_number`, `workflow_type` (REPAIR/MANUFACTURE/BOTH), `max_repairs`, `repair_suffix_format`, `delivery_location`, `reviewer_label`, `customer` FK, `sort_order`. Methods: `generate_wo_number()` (thread-safe via NumberSequence), `get_repair_suffix()`.
- **Account FK on DrillBit & WorkOrder**: Both models now have `account` FK to `sales.Account`. Bits belong to an account from day one (L3 bit → LSTK or ARAMCO). Account determines WO numbering and workflow.
- **WO Number Formats**: STANDARD (`YYYY-PREFIX-NNN`), NUMERIC (`YYYYNNNN`), SUFFIX (`YYYYNNNN-SUFFIX`). Thread-safe auto-increment via `NumberSequence` model with `select_for_update`.
- **WO Create Page** (`templates/workorders/workorder_create.html`): Account is the primary field. Selecting an account shows an info card with workflow type, pricing mode, max repairs, delivery location. `WorkOrderCreateEnhancedForm` in `apps/workorders/forms.py`.
- **WO List Page Updated**: Account column with indigo badge, account dropdown filter, `select_related('account')` in queryset.
- **Process Routes & Router Steps**: Two seeded routes — FC Repair (33 steps from JC Template QAS/1006 Rev L) and L3/L4 Manufacture (26 steps). `ProcessRouteOperation` has `is_conditional` and `has_yes_no` flags. `ProcessRoute` has `workflow_type` and `accounts` M2M.
- **Router Sheet Auto-Population**: `RouterSheetView._get_route_for_wo()` selects route by account workflow type or WO type. Creates `RouterSheetEntry` records from operations on first view.
- **QR Scan API**: `api_router_step_scan` endpoint (`POST /workorders/<wo_pk>/router-sheet/<step>/api-scan/`) supports `start`, `end`, `skip` actions with state validation. Returns JSON with timestamps, operator, duration.
- **Repair Tracking**: `DrillBit.repair_count` separate from serial number. ARAMCO: max 2 repairs (R, R2 then scrap), 8-digit serials. R suffixes are events, not part of serial identity.
- **11 Accounts Seeded**: LSTK (NUMERIC seq 1001), UR (STANDARD seq 1001), L3 (STANDARD ARDT-LV3), L4 (STANDARD ARDT-LV4), ARDT (STANDARD), WFD (STANDARD seq 1001), ARAMCO (STANDARD AR prefix, max 2 repairs, R{n} suffix), RC-LSTK (STANDARD RC), HALLIBURTON (SUFFIX HDBSC seq 1001), HAL_REGIONAL (SUFFIX REG seq 1001), SUB (STANDARD SUB prefix).

### Recent Enhancements (Feb 2, 2026)
- **Evaluation System Expanded to 9 Types**: `CutterEvaluationMatrix.EvaluationType` now has: RECEIVING, ARDT, ENGINEER (Tech Rep), QC, DIE_CHECK, FINAL_DIE_CHECK, FINAL_QC, FINAL_INSPECTION, REWORK. Evaluation create form (`cutter_evaluation_form.html`) shows all 9 in dropdown; job card detail (`workorder_detail_enhanced.html`) loops over all 9 with Start/Edit links.
- **7 Decision Choices**: `CutterEvaluationMatrix.Decision` choices: REPAIR, RERUN, SCRAP, DEBRAZE, CUTTER_RETROFIT, NEW_BUILD, BODY_RETROFIT. Dropdown on evaluation matrix form replaces old checkboxes.
- **Cutters Details JSONField**: `CutterEvaluationMatrix.cutters_details` (JSONField) stores the "For Plant Use Only" table rows (qty, size_mm, part_no, description, remarks). Saved/loaded via bulk JSON save in `cutter_evaluation_matrix.html`.
- **Cutters Details Pre-Population from BOM**: On first load (no saved data), the cutters details table auto-fills from BOM lines (`active_bom.lines`) — qty, cutter_size, hdbs_code/mat_number, item name. View: `CutterEvaluationEditView` in `views_jobcard.py`.
- **Per-Action Breakdown in Totals**: Evaluation grid totals row shows counts per action (e.g., "X:5 | R:3 | O:20 | L:2") via `updateTotals()` in template JS.
- **Cutter State Tracking Across Evaluations**: `CutterEvaluationEditView` builds cumulative cutter state from all prior evaluations for the WO. Passed as `cutter_state_json` (keyed by "blade,position"). Grid cells with prior history get amber bottom border + tooltip showing chain (e.g., "Prior: Receiving Evaluation: R → ARDT Evaluation: X").
- **Expanded CutterEvaluationEntry Actions**: Added F (Fill), L (Lost), P (Pocket Build Up), I (Impact Arrestor), V (Fin Build Up). Removed D (Damaged), M (Missing).
- **BOM List API**: `GET /technology/api/boms/?design_id=X` returns BOMs for a design. Used by WO create form's BOM selector ("Change" button next to L5 MAT).
- **WO Create Serial-Number-Driven**: WO create form (`workorder_create.html`) redesigned — enter serial number → debounced API lookup (`/workorders/api/drill-bits/lookup/`) auto-populates size, type, HDBS, SMI, design MAT level, L5 MAT/BOM, repair/rerun counts, received date, from location.
- **Migration**: `0014_cutterevaluationmatrix_cutters_details_and_more.py` — adds `decision`, `cutters_details` fields and updates `EvaluationType`/`Action` choices.

### Recent Enhancements (Feb 8, 2026) — ERP Automation Module
- **Full ERP Automation App** (`apps/erp_automation/`): Complete browser automation system for D365 ERP with Record → Convert → Execute workflow. All services run locally on `localhost:8001`.
- **Browser Recorder** (`services/recorder.py`): Playwright-based recorder opens D365 in a real browser, injects JavaScript to capture user actions (clicks, fills, selects, navigates). SPA re-injection via `page.on("framenavigated")` handles D365 page transitions. Background thread with queue communication. `no_viewport=True` for desktop experience. Live polling endpoint updates UI in real-time.
- **Smart Locator Engine** (`services/locator_engine.py`): Multi-strategy element resolution with fallback chain. Searches main page AND all child frames/iframes (critical for D365). Per-strategy 5s timeout. Strategies ordered by priority: data-testid → aria-label → name → id → css → xpath → text → role.
- **Workflow Executor** (`services/executor.py`): Runs workflow steps sequentially via Playwright. Handles ADFS login flow, `navigate` action type, D365 custom dropdowns (click fallback for non-`<select>` elements). Step-level error tracking with retry support.
- **Recording → Workflow Conversion** (`management/commands/create_workflow_from_recording.py`): Smart auto-conversion of recorded actions to workflow models. Deduplicates click+fill pairs, maps `select`→`click` for D365, strips dynamic ID prefixes for `contains(@id)` xpath fallback, generates `{{TEMPLATE}}` value substitution from recorded input, sequential step numbering (20, 21, 22...), orphaned locator cleanup on regeneration. No fabricated/hardcoded steps — only recorded data used.
- **Quick Convert UI Button**: "Quick Convert" button on recording detail page calls `create_workflow_from_recording` via `call_command()` internally. No terminal access needed — full flow works from the browser.
- **Job Card Parser** (`services/job_card_parser.py`): Parses Job Card Excel files into `ERPJobData` records with all fields needed for ERP item creation (WO number, serial, size, type, cutter BOM, account, repair modifiers, body material, item group).
- **Route Selection** (`services/route_selector.py`): Auto-selects production route based on bit size, port presence, repair modifiers (USR, hardfacing, crush & shear).
- **Job Data Detail Page**: Shows parsed data with clipboard copy buttons, route selection dropdown, item number generation, and "Execute Workflow" button. Status tracking: DRAFT → READY → SENT → COMPLETED/ERROR.
- **ERP Route Reference**: Routes list page at `/erp-automation/routes/` with all production routes and their selection criteria.
- **Session Credentials**: ERP login credentials stored in Django session (not DB) for security. Credential management page with save/clear actions.
- **Value Template Resolution**: `WorkflowStep.get_value()` resolves `{{FIELD_NAME}}` placeholders from `ERPJobData.get_row_data()`. Priority: static value → template → field name.
- **D365-Safe Locator Generation**: Recording conversion generates `contains(@id, "stableId")` xpath as fallback strategy to handle D365's dynamic ID prefix prepending.

### Recent Enhancements (Feb 8, 2026 — Session 2) — Workflow Step & Locator Editor UI
- **Workflow Editor Page** (`workflow_detail.html`): Full CRUD UI for editing workflow steps and locators directly from the browser. Replaces the need for JSON file editing (legacy system in `apps/ERP_Item_creation_automation/`). Alpine.js `workflowEditor()` component with inline editing, modals, and toast notifications.
- **Steps Table with Inline Editing**: Each step row shows order, name, action type, locator (clickable), value (color-coded: amber=template, green=static, cyan=field), wait_after, press_key_after badge, clear_before_fill indicator, condition_value badge, continue_on_error badge. Hover reveals edit/duplicate/delete buttons. Click pencil to edit inline with Save/Cancel.
- **Add Step Modal**: Full form with order, action type, step name, condition value, locator picker (searchable dropdown), wait_after, value (static/template/field), press_key_after, clear_before_fill, continue_on_error.
- **Searchable Locator Picker**: Replaced plain Locator ID number input with a searchable dropdown. Type to search all locators by name via `/erp-automation/api/locators/search/`. Click to select — shows selected locator as a blue badge with clear button. Available in both Add Step modal and inline edit mode.
- **Locator Editor Modal**: Click any locator link in the steps table to open full editor. Shows name, page_context, all strategies with type/value/priority/success/fail counts. Can add/remove strategies. Saves via API.
- **Create Locator Inline**: "+ New" button in Add Step modal opens locator creation modal. After saving, new locator auto-populates into the step form.
- **Duplicate Step**: Copy button creates a duplicate step with "(copy)" appended to name, order +1.
- **Workflow Step CRUD APIs** (`apps/erp_automation/views.py`):
  - `GET /erp-automation/api/workflows/<pk>/steps/` — List all steps with locator details
  - `POST /erp-automation/api/workflows/<pk>/steps/create/` — Create step
  - `POST /erp-automation/api/workflows/<pk>/steps/<pk>/update/` — Update step fields
  - `POST /erp-automation/api/workflows/<pk>/steps/<pk>/delete/` — Delete step
- **Locator CRUD APIs** (`apps/erp_automation/views.py`):
  - `POST /erp-automation/api/locators/create/` — Create locator with strategies
  - `POST /erp-automation/api/locators/<pk>/update/` — Update locator, replaces all strategies
  - `GET /erp-automation/api/locators/<pk>/detail/` — Full locator details with strategies
  - `GET /erp-automation/api/locators/search/?q=` — Search locators by name (autocomplete, max 30 results)
- **Workflow List Page Updated**: Workflow names are now clickable links to the editor. Added ⚙️ settings icon (indigo) linking to editor. Removed Django Admin edit link. Only two actions: Edit (⚙️) and Execute (▶️).
- **D365 Combobox Alt+ArrowDown**: Executor (`executor.py`) now detects `role="combobox"` elements after click and automatically presses `Alt+ArrowDown` to open D365 custom dropdowns.
- **D365 Locator Pattern Reference**: For D365 elements, the most reliable locator patterns in priority order:
  1. `name` — Field name attribute (e.g., `FromConfigId`) — most stable, no dynamic prefix
  2. `css` — `input[name="FieldName"]` — backup, also stable
  3. `xpath` — `//*[contains(@id, "StableIdPart_input")]` — handles any dialog prefix
  4. `xpath` — `//*[@data-dyn-controlname="FieldName"]//input` — D365 control wrapper pattern
  5. `xpath` — `//input[@role="combobox" and @name="FieldName"]` — role+name combo

### Recent Enhancements (Feb 9, 2026) — D365 Smart Interaction System
- **InteractionMode per WorkflowStep** (`models.py`): New `InteractionMode` TextChoices class with 10 modes: `auto` (detect at runtime), `standard_input`, `combobox` (Alt+Down), `lookup_button` (double-click), `custom_dropdown`, `segmented_entry`, `checkbox_toggle`, `dialog_button`, `nav_button`, `tab_header`. Field `interaction_mode` on WorkflowStep with default `auto`. Migration 0008.
- **D365InteractionEngine** (`services/executor.py`): New ~250-line class replacing hardcoded D365 interaction handling. Each interaction mode has a specific chain of strategies tried in order with automatic fallbacks. Key methods:
  - `detect_interaction_mode(element)` — Runtime element classification from DOM attributes (role, className, data-dyn-controlname, etc.)
  - `execute_interaction(action_type, element, value, step)` — Delegates to mode-specific chain; tries each strategy in order, falls back on failure
  - Interaction chains per mode: e.g., combobox: click → Alt+Down; lookup_button: click → wait(500) → click again → force-click; checkbox_toggle: click → force-click → press Space
- **Executor Refactored**: `_perform_action()` is now a thin wrapper that delegates to `D365InteractionEngine.execute_interaction()`. Old hardcoded lookupButton/combobox checks removed.
- **Recorder Captures D365 Control Context**: `_store_action()` now extracts and persists `element_dyn_control_name` (from `data-dyn-controlname` ancestor) and `element_data_testid`. New fields on RecordedAction model. `poll_recording()` and `stop_recording()` views save all new fields (also fixed missing `element_role` and `element_type` in `poll_recording()`).
- **Converter Auto-Detects Interaction Mode**: `_determine_interaction_mode()` in `create_workflow_from_recording.py` maps recorded action attributes to interaction modes during conversion. Uses element_class, element_role, d365_pattern, tag, and dyn_control_name.
- **Auto Value Template Detection from Job Data**: `_auto_detect_value_template()` compares fill values against linked `ERPJobData.get_row_data()`. Exact match → `{{FIELD_NAME}}`. Composite match (2+ fields) → `"{{F1}} {{F2}}"`. Longest match first to avoid partial matches.
- **Expanded Generic Aria-Label Blacklist**: 30+ entries (Name, ea, Back, Close, OK, Cancel, etc.). When aria-label is blacklisted, `@name` attribute promoted to priority 0 as primary locator strategy.
- **Post-Conversion Validation**: `_validate_workflow()` prints warnings: consecutive clicks on same locator, generic aria-label as only strategy, fill steps with no value mapping, steps with no locator, interaction mode distribution summary.
- **Workflow Editor: Interaction Mode Column** (`workflow_detail.html`): New "Mode" column in steps table with color-coded badges (gray=auto, green=standard, blue=combobox, orange=lookup, teal=dropdown, violet=segmented, pink=checkbox, yellow=dialog, cyan=nav, indigo=tab). Dropdown selector in inline edit mode and Add Step modal. `duplicateStep()` copies interaction_mode. Sidebar shows mode distribution summary.
- **Step CRUD APIs Updated**: `api_step_create()`, `api_step_update()`, and `api_workflow_steps()` all handle `interaction_mode` field.
- **Composite Workflows** (`models.py`, `services/chain_executor.py`): WorkflowChain, WorkflowChainLink, ChainExecution models for chaining multiple workflows. Chain executor service orchestrates sequential execution with shared browser, context mapping between workflows, condition-based link execution, and progress tracking. Admin registered with TabularInline. Views, URLs, and templates for chain management.

### Recent Enhancements (Feb 14, 2026) — Complete ERP Chain Rewrite
- **New ActionTypes** (`models.py`, `executor.py`): Added `read_value` (reads element value into `context_vars` via `save_result_as` — tries `input_value()` then `inner_text()` then `text_content()`) and `goto_url` (navigates to URL mid-workflow, supports template substitution). Both handled in `_execute_step()` before the locator-required section.
- **BOM Line Flattening** (`models.py`): `ERPJobData.get_row_data()` now flattens `cutter_bom_data` variants into `BOM_LINE_1..8_ITEM` / `BOM_LINE_1..8_QTY` template variables. Iterates all groups/variants, collects `(erp_item_no, qty)` pairs where both are non-empty, pads remaining slots with empty strings.
- **Complete ERP Chain Rewrite** (`seed_erp_chain.py`): Based on 4 live D365 recordings (sessions pk=13-16) on prod.alrushaid.net. Expanded from 7 workflows/74 steps to **13 workflows/161 steps/108 locators/1 chain with 13 links**. Chain name: "ARAMCO FC Repair: Full ERP Flow". Key changes from old chain:
  - **Removed** Product Number field (D365 auto-generates Item # like R-AR-23-0250)
  - **Added** BOM Unit field (`BOMUnitId = ea`) to product creation
  - **Fixed** Config dimension: uses `{{BODY_MATERIAL}}` template (resolves to `MB`) instead of hardcoded `Prod_Dimen_Config`
  - **Fixed** Color dimension: uses `{{L5_MAT_FULL}}` (includes M suffix like `1134806M`) instead of `{{MAT NO.}}`
  - **Simplified** Product Variants: removed Variant Header click, uses Suggest All directly
  - **New WF-2B**: Capture Item Number — uses `read_value` action to read D365-generated item # and save as `ITEM_NO` context variable
  - **New WF-6**: Create BOM (Copy) — creates BOM with copy toggle, selects FromConfigId=MB
  - **New WF-7**: Enter BOM Lines — 8 line blocks x 4 steps each (New, Fill Item, Confirm, Fill Qty), all `continue_on_error=True`. Empty BOM_LINE_N vars gracefully skip.
  - **New WF-8**: Approve BOM + Activate Version — approves BOM from BOM Table, goes back, approves+activates version
  - **New WF-9**: Route Registration — navigates to Route Table, filters by route #, fills item/config/site, approves+activates
  - **New WF-10**: Release Product — navigates to Release Products, enters item #
  - **New WF-11**: Movement Journal — creates journal, adds line with item/config/serial, posts
  - **Context mapping**: `ITEM_NO` propagated from WF-2B to WF-3, WF-9, WF-10, WF-11 via chain link `context_mapping`
- **check_for_errors Field** (`models.py`, migration `0009`): Boolean field on `WorkflowStep` for opt-in D365 error dialog detection after step execution. Executor checks `detect_error_message()` and takes screenshot if error found.
- **Job Card Parser ARAMCO Fixes** (`job_card_parser.py`): Auto-populates `body_material=MB`, `item_group=RPR-FC-AR`, `contract_number`, `vendor_number` for ARAMCO account. Fixed cutter BOM variant lookup to match by `erp_item_no`.
- **ERP Item # Columns** (`cutter_inventory_list.html`, `item_list.html`): Added ERP Item Number column to cutter inventory and item list pages showing `variant.erp_item_no`.
- **Cutter Stock Import** (`import_stock_from_onhand.py`, `import_cutters_excel.py`): Import stock from D365 On-hand inventory Excel. Fixed CLI-RCL variant case mapping (was `NEW-CLI`, corrected to `CLI-RCL` matching `VariantCase.code`).

### Recent Enhancements (Feb 14, 2026) — ERP Environment Selector & Debug Chain Fix
- **ERPEnvironment Model** (`models.py`, migration `0010`): DB-persisted named environment URLs (Sandbox, Production) with `is_default` flag, `sort_order`. `save()` enforces single default. Admin registered.
- **ERP Environment Selector on Credentials Page** (`credentials.html`, `CredentialsView`): Dropdown populated from `ERPEnvironment` model replaces free-text URL input. Options: Sandbox, Production, Custom URL. Hidden `erp_url` field carries resolved URL. Alpine.js `credentialsPage()` component. "Manage Environments" expandable section with inline CRUD (add/edit/delete/set-default).
- **Environment CRUD APIs** (`views.py`, `urls.py`): 5 new endpoints — `api_environment_list`, `api_environment_create`, `api_environment_update`, `api_environment_delete`, `api_environment_set_default`.
- **Recording Page Environment Dropdown** (`recording.html`, `RecordingView`): Environment dropdown before Target URL input. On env change, sets target URL with `?cmp=ardt&mi=DefaultDashboard` suffix.
- **`get_erp_url()` Helper** (`views.py`): Resolves ERP URL with fallback chain: session `erp_url` → DB default environment → first environment → empty string. Used by all 4 execution paths.
- **Debug Chain Executor ERP_URL Fix** (`executor.py` → `start_debug_chain()`): Fixed two bugs — (1) `ERP_URL` was not injected into `accumulated_context`, so `{{ERP_URL}}` templates resolved to empty; (2) `accumulated_context` was not auto-merged into `merged_row_data`, only explicit `context_mapping` was applied. Both now match the regular chain executor in `chain_executor.py`.
- **Chain Executor Context Merge** (`chain_executor.py`): All `accumulated_context` keys auto-merged into `merged_row_data` for every link, so template vars like `{{ERP_URL}}` resolve without explicit `context_mapping`.
- **Seed ERP Environments** (`seed_erp_environments.py`): Seeds Sandbox (`https://sandbox.alrushaid.net/namespaces/AXSF/`, default) and Production (`https://prod.alrushaid.net/namespaces/AXSF/`).
- **Seed ERP Chain Updated** (`seed_erp_chain.py`): All workflows use `target_url=""` (resolved at runtime from session). WF-0 goto_url step uses `template:{{ERP_URL}}?cmp=ardt`. Added step 37 "Click OK (Attributes Dialog)" with `continue_on_error=True` for accounts (ARAMCO, LSTK) that show a "Set attribute values" dialog after filling Inventory Unit.

### Default Rule for List Pages
**Every list page being edited must include**: Excel-style column filters (cascading), sort (A-Z / Z-A with Lucide icons), client-side pagination (25/50/100/All), global search, and visual filter indicators (blue header text). The `applyColumnFilter()` function must only consider visible checkboxes (respect search input filtering).

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
| HDBS types list | `templates/technology/hdbs_type_list.html` |
| Drill bit create form | `templates/workorders/drillbit_form.html` |
| Sync HDBS command | `apps/technology/management/commands/sync_hdbs_from_designs.py` |
| WO create page | `templates/workorders/workorder_create.html` |
| WO list page | `templates/workorders/workorder_list_enhanced.html` |
| Job card detail | `templates/workorders/workorder_detail_enhanced.html` |
| Router sheet | `templates/workorders/router_sheet.html` |
| Seed accounts command | `apps/sales/management/commands/seed_accounts.py` |
| Seed router steps | `apps/workorders/management/commands/seed_router_steps.py` |
| Eval create form | `templates/workorders/cutter_evaluation_form.html` |
| Eval matrix editor | `templates/workorders/cutter_evaluation_matrix.html` |
| Drillbit lookup API | `apps/workorders/views.py` (api_drillbit_lookup) |
| BOM list API | `apps/technology/views.py` (api_boms_list) |
| ERP Automation views | `apps/erp_automation/views.py` |
| ERP Automation models | `apps/erp_automation/models.py` |
| Browser recorder service | `apps/erp_automation/services/recorder.py` |
| Workflow executor service | `apps/erp_automation/services/executor.py` |
| D365 interaction engine | `apps/erp_automation/services/executor.py` (D365InteractionEngine class) |
| Chain executor service | `apps/erp_automation/services/chain_executor.py` |
| Smart locator engine | `apps/erp_automation/services/locator_engine.py` |
| Job card parser | `apps/erp_automation/services/job_card_parser.py` |
| Route selector | `apps/erp_automation/services/route_selector.py` |
| Recording → Workflow converter | `apps/erp_automation/management/commands/create_workflow_from_recording.py` |
| ERP chain seeder | `apps/erp_automation/management/commands/seed_erp_chain.py` |
| ERP recording page | `apps/erp_automation/templates/erp_automation/recording.html` |
| ERP recording detail | `apps/erp_automation/templates/erp_automation/recording_detail.html` |
| ERP job data detail | `apps/erp_automation/templates/erp_automation/job_data_detail.html` |
| ERP job data upload | `apps/erp_automation/templates/erp_automation/job_data_upload.html` |
| ERP dashboard | `apps/erp_automation/templates/erp_automation/dashboard.html` |
| ERP workflow detail (editor) | `apps/erp_automation/templates/erp_automation/workflow_detail.html` |
| ERP workflow list | `apps/erp_automation/templates/erp_automation/workflow_list.html` |
| ERP routes list | `apps/erp_automation/templates/erp_automation/route_list.html` |
| ERP automation URLs | `apps/erp_automation/urls.py` |
| ERP environment model | `apps/erp_automation/models.py` (ERPEnvironment class) |
| Seed ERP environments | `apps/erp_automation/management/commands/seed_erp_environments.py` |
| ERP credentials page | `apps/erp_automation/templates/erp_automation/credentials.html` |

### Key View Classes

| View | File | URL |
|------|------|-----|
| CutterInventoryListView | `apps/inventory/views.py:1540` | `/inventory/cutters/` |
| CutterInventoryExportView | `apps/inventory/views.py:3208` | `/inventory/cutters/export/` |
| ItemCreateView | `apps/inventory/views.py:700+` | `/inventory/items/create/` |
| BOMCreateWithBuilderView | `apps/technology/views.py:2737` | `/technology/boms/create/` |
| DrillBitListEnhancedView | `apps/workorders/views_drillbit.py` | `/work-orders/drill-bits/` |
| WorkOrderCreateView | `apps/workorders/views.py:104` | `/workorders/create/` |
| WorkOrderListEnhancedView | `apps/workorders/views_jobcard.py:99` | `/workorders/enhanced/` |
| WorkOrderDetailEnhancedView | `apps/workorders/views_jobcard.py:197` | `/workorders/enhanced/<pk>/` |
| RouterSheetView | `apps/workorders/views_jobcard.py:656` | `/workorders/<pk>/router-sheet/` |
| CutterEvaluationCreateView | `apps/workorders/views_jobcard.py:548` | `/workorders/<wo_pk>/cutter-evaluation/create/` |
| CutterEvaluationEditView | `apps/workorders/views_jobcard.py:591` | `/workorders/<wo_pk>/cutter-evaluation/<pk>/edit/` |
| api_drillbit_lookup | `apps/workorders/views.py` | `/workorders/api/drill-bits/lookup/` |
| api_boms_list | `apps/technology/views.py` | `/technology/api/boms/` |
| DashboardView (ERP) | `apps/erp_automation/views.py` | `/erp-automation/` |
| RecordingView | `apps/erp_automation/views.py` | `/erp-automation/record/` |
| RecordingDetailView | `apps/erp_automation/views.py` | `/erp-automation/record/<pk>/` |
| quick_convert_recording | `apps/erp_automation/views.py` | `/erp-automation/record/<pk>/quick-convert/` |
| JobDataListView | `apps/erp_automation/views.py` | `/erp-automation/job-data/` |
| JobDataDetailView | `apps/erp_automation/views.py` | `/erp-automation/job-data/<pk>/` |
| JobDataUploadView | `apps/erp_automation/views.py` | `/erp-automation/job-data/upload/` |
| api_execute_job_data | `apps/erp_automation/views.py` | `/erp-automation/api/job-data/<pk>/execute/` |
| WorkflowListView (ERP) | `apps/erp_automation/views.py` | `/erp-automation/workflows/` |
| WorkflowDetailView (ERP) | `apps/erp_automation/views.py` | `/erp-automation/workflows/<pk>/` |
| RouteListView | `apps/erp_automation/views.py` | `/erp-automation/routes/` |
| api_workflow_steps | `apps/erp_automation/views.py` | `/erp-automation/api/workflows/<pk>/steps/` |
| api_step_create | `apps/erp_automation/views.py` | `/erp-automation/api/workflows/<pk>/steps/create/` |
| api_step_update | `apps/erp_automation/views.py` | `/erp-automation/api/workflows/<pk>/steps/<pk>/update/` |
| api_step_delete | `apps/erp_automation/views.py` | `/erp-automation/api/workflows/<pk>/steps/<pk>/delete/` |
| api_locator_create | `apps/erp_automation/views.py` | `/erp-automation/api/locators/create/` |
| api_locator_update | `apps/erp_automation/views.py` | `/erp-automation/api/locators/<pk>/update/` |
| api_locator_detail | `apps/erp_automation/views.py` | `/erp-automation/api/locators/<pk>/detail/` |
| api_locator_search | `apps/erp_automation/views.py` | `/erp-automation/api/locators/search/` |

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

### D3 Environment (Production)
- **Project Path**: `D:\PycharmProjects\floor_management_system-D3`
- **Python Venv**: `D:\PycharmProjects\floor_management_system-D3\venv\Scripts\python.exe`
- **Activate Venv**: `D:\PycharmProjects\floor_management_system-D3\venv\Scripts\activate`
- **Settings Module**: `DJANGO_SETTINGS_MODULE=ardt_fms.settings`
- **Server**: `python manage.py runserver 0.0.0.0:8001` (access at `http://localhost:8001`)
- **Database**: SQLite `db.sqlite3` (NOT tracked in git)
- **Git Remote**: `https://github.com/Ramzi-Kassab/Floor-Management-System-D.git`
- **Branches**: `master` (production), `dev/*` (feature branches)
- **D365 ERP Target**: `https://ardt.operations.dynamics.com/` (ADFS auth)
- **Playwright**: Chromium browser for ERP automation (sync API, installed via `playwright install chromium`)
- **ERP Chain**: "ARAMCO FC Repair: Full ERP Flow" (pk=7) — 13 workflows, 161 steps, 108 locators

---

## Need Help?

1. **Check this file first** for patterns and conventions
2. **Run `./hc`** to ensure database is healthy
3. **Backup with `./hv`** before making changes
4. **Check Django admin** at `/admin/` for data inspection
5. **Review browser console** for JavaScript errors
