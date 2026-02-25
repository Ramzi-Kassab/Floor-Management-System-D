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
- **323 PDC cutter items** imported from Excel
- **850 item variants** with unique ERP numbers
- **3 designs** in database
- **45 drill bits** registered
- **30 work orders** created
- **26 workflows** (13 active WF-0 through WF-11, plus archived versions)
- **4 workflow chains** (ARAMCO 13-link, LSTK 5-link, Create Item 2-link, Create BOM 4-link)
- **342 locators** with 517 strategies
- **37 ERP routes** seeded
- **7 ERPJobData** records
- **13 recordings** captured

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

### Recent Enhancements (Feb 15, 2026) — Chain Debug Execution & Environment Management
- **Workflow Chain Debug Execution**: Full debug mode for chain execution via `chain_detail.html`. "Debug Chain" button on job data detail page navigates to chain editor with `?start_debug={jobPk}` param. Chain editor auto-starts debug session on load when param present.
- **Debug Polling with Session Expiry Detection**: `debugPoll()` in chain_detail.html checks `content-type` header — if response is HTML instead of JSON (302 redirect to login page followed by HTML login form), stops polling, sets `debugState.sessionExpired = true`, shows red banner with re-login link and resume polling button.
- **24-Hour Session Timeout**: Added `SESSION_COOKIE_AGE = 86400` and `SESSION_SAVE_EVERY_REQUEST = True` to settings.py to prevent session expiry during long debug runs.
- **ERPEnvironment Model**: New model for managing ERP target environments (Sandbox, Production) with name, base_url, description, is_default fields. Migration 0010. Admin registered.
- **Credentials Page Environment Selector**: `credentials.html` expanded with environment dropdown, manage/add/edit/delete UI via Alpine.js `credentialsPage()` component with CRUD API calls.
- **Recording Page Environment Selector**: `recording.html` adds environment dropdown that auto-resolves target URL from selected environment.
- **check_for_errors on WorkflowStep**: New boolean field `check_for_errors` (default False). When True, executor checks for D365 error dialogs after step execution. UI: checkbox in add/edit step forms, ERR badge on step rows in workflow editor.
- **Job Card Parser Major Expansion**: `job_card_parser.py` expanded from ~400 to ~960 lines: label-based cell search for shifted Excel layouts, dual bracket format `[TEXT QTY]`/`[QTY TEXT]` parsing, account aliases, evaluation extraction from 8 sheet types, build-up detection from eval grids, `RCLM`->`CLI-RCL` variant mapping, batch parsing, BITS TRACKING row parser.
- **Route Selector Expansion**: `route_selector.py` expanded from ~102 to ~325 lines: account-to-item-group mapping, auto port/size detection from job data, multi-fallback route matching, `select_route_for_job_data()` convenience function, `build_route_name()` helper, RC route basic matching.
- **Seed Commands**: `seed_erp_chain` (2,062 lines, seeds ARAMCO 13-segment chain with 162 steps), `seed_erp_environments` (Sandbox/Production URLs), `seed_flask_workflow` (Flask port workflow).
- **Clean startDebugChain() in job_data_detail.html**: Removed orphaned `.catch()` blocks from old modal-based approach that caused SyntaxError preventing all JS on the page from loading.

### Recent Enhancements (Feb 15, 2026 — Session 2) — Chain Debug UX Improvements
- **Step Coloring Fix (ID-based tracking)**: `completed_steps` entries in executor.py now include `"id": step.pk` (added to all 8 append calls + 2 current_step dicts). Frontend `getStepDebugStatus()`, spinner check, and `getStepDebugDuration()` all match by `step.id` instead of `step.order`, preventing cross-segment false positive coloring when workflows share step order numbers.
- **Chain-Scoped Display Numbering**: New `getChainStepNumber(segIdx, stepIdx)` helper returns running counter across all segments (segment 0 has N steps, segment 1 starts at N+1, etc.). During debug mode, step `#` column shows chain-scoped number with small `#order` badge for per-workflow reference.
- **Run Segment (Jump-to-Link)**: `debugRunSegment(seg)` rewritten to call new `/api/debug/<pk>/rerun-from-link/` API instead of trying to reuse `debugRunFromStep` (which can't cross segment boundaries). Backend: `rerun_from_link` command in `_pause_and_process_commands()` stores target `link_order` in state, returns `"JUMP_LINK"` from `_debug_step_loop()`, chain while-loop jumps to target link index.
- **Run from Step Restricted**: Per-step play button (▶) now only shown for steps in the currently-running segment (`debugState._runningLinkOrder === seg.link_order`). Prevents attempting cross-segment step jumps which would fail.
- **Step-by-Step "Go" Mode**: New toggle button in debug toolbar ("Step Mode") sends `set_step_by_step` command to executor. When enabled, executor pauses after every successful step with `is_step_pause: true` error info. Pause panel shows green "Step Completed" header with prominent animated "Go →" button. Toggle works both while running and while paused. Status label shows "Step Done — Waiting for Go" during step pause.
- **Chain Link Loop Converted to While**: `start_debug_chain()` link iteration converted from `for` to `while link_idx < len(links)` for jump support. All `continue` statements preceded by `link_idx += 1`.
- **New API Endpoints**: `api_debug_rerun_from_link(request, pk)` — jump to specific chain link; `api_debug_set_step_mode(request, pk)` — toggle step-by-step mode.
- **New URL Patterns**: `api/debug/<int:pk>/rerun-from-link/` and `api/debug/<int:pk>/step-mode/`.

### Recent Enhancements (Feb 16, 2026) — Job Card Parser Fixes
- **False Positive Hardfacing Fix**: Removed Method 4 (eval grid scan for P/V/I action codes) from hardfacing detection. Header text like `"Internal Evaluation Sheet"` in the grid area had its first char `I` matched as Impact Arrestor Build Up, falsely setting `has_hardfacing=True`. Hardfacing now detected by 3 reliable methods only: (1) I7/I8 checkboxes, (2) Evaluation D36 remarks containing `"build"`, (3) Eval-LSTK R34/U34/X34 non-zero counts.
- **Eval Grid Header Filtering**: `_extract_eval_grid()` now skips cells with `len > 3` to prevent header/label text (e.g. `"SERIAL NO:"`, `"SAUDI ARAMCO"`, `"S- SPIN"`, `"O- OK"`) from being counted as action codes. Valid codes are 1-3 chars (e.g. `"R"`, `"X3"`, `"R1"`).
- **EVAL_SHEET_MAP Expanded**: Added `'Eval & Quot-AR'` (ARAMCO evaluation) and `'Rework'` sheets to the evaluation sheet map so their grids are included in evaluation summaries.

### Recent Enhancements (Feb 16, 2026 — Session 2) — D365 Error Detection & Debug UX
- **Smart D365 Error Detection**: `detect_error_message()` in `executor.py` completely rewritten with 3-phase detection strategy: (1) D365-specific error bar selectors (`.messageBar-error`, `.messageBar-critical`) — high confidence, (2) Generic error selectors (`.error-message`, `.alert-danger`) — with ignore pattern filtering, (3) Broad message bar selectors (`span.messageBar-message`, `[role='alert']`) — checks parent element class for info/warning/success and skips non-error bars.
- **D365 Ignore Patterns**: `_D365_IGNORE_PATTERNS` list on `WorkflowExecutor` class with 16 patterns including "please wait", "processing your request", "saved successfully", "has been created", "loading", "validating", etc.
- **800ms Wait Before Error Check**: `_execute_step()` now waits 800ms after step completion before running `detect_error_message()`, allowing transient D365 processing messages to clear.
- **D365 Dialog Error Type**: When `check_for_errors` detects a message, the error result includes `error_type: "d365_dialog"`. This propagates through the debug executor to the frontend via `error_info.error_type`.
- **"Dismiss & Continue" Button**: For D365 dialog errors, the pause panel shows a prominent blue "Dismiss & Continue" button instead of "Retry Step" — since the click action itself succeeded, users can skip past informational D365 messages.
- **Blue Info Display for D365 Messages**: D365 dialog errors show with blue info styling (not red), with header "D365 Message Detected" and descriptive text explaining the click succeeded but D365 showed a message. Includes guidance: "If this is a processing/info message, click Dismiss & Continue."
- **Status Bar**: D365 dialog pauses show "Paused — D365 Message" label with cyan badge/progress bar colors, distinguishing from real errors (amber) and step completions (green).
- **Skip Auto-Heal for D365 Dialogs**: `_debug_step_loop()` skips Phase 1 (auto-heal locator) for `d365_dialog` error types since the action succeeded — goes straight to Phase 2 (pause for user).
- **`dialog_button` Skip Error Check**: Steps with `interaction_mode='dialog_button'` (OK buttons) now skip `check_for_errors` entirely — D365 always shows processing messages after form submissions, which are NOT errors. Removed overly-broad `[class*='error']` selector from Phase 1.
- **Dismiss & Continue API**: New `/api/debug/<pk>/dismiss-continue/` endpoint calls `close_error_dialog()` on the browser to actually close the D365 message bar, then marks the step as **completed** (not skipped). Method: `DebugExecutor.dismiss_and_continue()` → `_pause_and_process_commands()` handles `dismiss_and_continue` command.
- **1500ms Error Check Wait**: Increased wait from 800ms to 1500ms before checking for errors, giving D365 more time to clear transient processing messages.
- **No Auto-Dismiss on Error**: Removed `close_error_dialog()` call from `_execute_step()` error path — let the user decide via the UI whether to dismiss or stop.
- **Duplicate Step Null Fix**: `api_step_create()` changed all `data.get("field", "")` to `data.get("field") or ""` pattern. JSON null → Python None was crashing Django CharFields. Frontend `duplicateStep()` also fixed: added `|| ''` null guards, all missing fields (press_key_after, clear_before_fill, condition_value), and `r.ok` check before `.json()`.
- **BOM Version Dropdown → lookup_button**: Step "Click BOM Version Name Dropdown" (WF 83, PK 1422, locator #416) changed from `custom_dropdown` to `lookup_button` mode. D365 lookup buttons need two clicks (focus then open flyout).
- **Session Expiry Detection in Workflow Editor**: All API calls in `workflow_detail.html` (loadSteps, saveEdit, saveNewStep, deleteStep, duplicateStep, openLocatorModal, saveLocator) now use `_apiFetch()` helper that detects `@login_required` redirects. When Django returns 302→login page (HTML), `fetch()` follows the redirect and returns 200 with HTML content. The helper checks `r.redirected` and `content-type` header — if response isn't JSON, shows "Session expired — please refresh the page and log in" flash message instead of crashing with `"Unexpected token '<'"` JSON parse error. Root cause: `@login_required` + `fetch()` auto-redirect = 200 OK with HTML body, bypassing `!r.ok` check.

### Recent Enhancements (Feb 17, 2026) — WF-7B: Edit BOM Lines + Approve
- **New Workflow WF-7B (pk=92)**: Replaces WF-7, WF-8, WF-90, WF-91 as a single workflow in chain 10 at order 90. 20 active steps: Phase 1 (delete all), Phase 2 (repeat group loop), Phase 3 (approve + activate).
- **Phase 1 — Bulk Delete Existing BOM Lines**: Steps 1, 3, 4. Select-all checkbox (locator 500) → Delete button → Confirm Yes. All `continue_on_error=True`. Gracefully skips for empty BOMs (no rows to select → no dialog appears → COE skips). Ctrl+A step removed (was selecting page text instead of grid rows).
- **Phase 2 — Repeat Group Loop (`bom_lines`)**: Steps 5-10 with `repeat_group='bom_lines'`. Iterates over `BOM_LINES` data from job card. Pattern per iteration: New BOM Line (click, locator 449, wait 1500ms) → Fill Item Number (`type_text`, `{{LOOP_ITEM}}`, press Enter, wait 2000ms) → Click Item Lookup to close dropdown (COE, press Escape) → Click Config Lookup (COE) → Select Config Variant (COE, press Escape) → Fill Quantity (fill, `{{LOOP_QTY}}`, press Tab). For Job pk=14 with 3 BOM lines: 6 steps × 3 = 18 expanded steps.
- **Phase 3 — Approve & Activate**: Steps 11-20. BOM Action Pane Tab → Approve BOM → OK → Close BOM Table → Wait 2s → BOM Version Tab → Version Approve → OK → Activate → Close. `continue_on_error=False`.
- **Chain 10**: 12 active links with clean 10-spacing (10-120).

### Recent Enhancements (Feb 21, 2026) — Repeat Group Expansion & Executor Fixes
- **Repeat Group Expansion Engine**: Implemented in both `execute_workflow()` and `_debug_step_loop()` in `executor.py`. Consecutive steps with the same `repeat_group` value are detected, the data source array is fetched from `row_data[repeat_data_source]`, and steps are expanded: N iterations × M group steps. Loop context variables (`LOOP_ITEM`, `LOOP_QTY`, `LOOP_INDEX`, `LOOP_ITERATION`) are merged into `step_row_data` for template resolution. Works with both normal and debug execution.
- **`BOM_LINES` List in `get_row_data()`**: `ERPJobData.get_row_data()` now returns `BOM_LINES` as a list of `{'ITEM': erp_no, 'QTY': qty}` dicts in addition to the legacy `BOM_LINE_N_ITEM`/`BOM_LINE_N_QTY` keys. This is the data source for the `bom_lines` repeat group.
- **`type_text` Action Handler**: Types into focused element using `keyboard.insert_text()` (bypasses D365 autocomplete). Supports `clear_before_fill` (Ctrl+A → Delete), `press_key_after`, and `wait_after`. No locator needed — operates on whatever has keyboard focus.
- **`press_key` Action Handler Fix**: Added `wait_after` support. Previously returned immediately, skipping the wait_after delay.
- **`select_grid_row` Rewritten — Two-Phase Approach**: Phase 1: JS finds the row and returns coordinates/selector (does NOT click — JS `.click()` doesn't trigger D365 `dyn-hyperlink` navigation). Phase 2: Playwright performs real mouse click via 3 fallback methods: `#id` selector → `input[value]` selector → coordinate click. Supports D365 FixedDataTable grids with virtualized rows.
- **WF-5 BOM Lookup Locator Improvements**: Locator #417 (Switch View Dropdown) got button-class fallback strategy. Locator #418 (All Bills of Materials option) got text-based and `li` text-match fallback strategies. Wait times increased on steps 6 (3000ms) and 7 (5000ms) for D365 rendering.
- **Select-All Checkbox Locator Fix (#500)**: Changed from `@role="checkbox"` (wrong) to `dyn-svg-symbol` class matching the actual SVG checkbox element in the D365 FixedDataTable header. Added 2 fallback strategies targeting `dyn-container` in header.
- **WF-9 Route Registration — Added "Click Add" Step**: New step #17 "Click Add Route Version" with locator #511 (`d365_route_add_btn`) inserted between route selection and field filling. Locator strategies: `routetable...New_CommandButton_label` xpath + text "Add".
- **WF-9 `select_grid_row` Column Header**: Step #16 `value_field` set to "Route number" matching D365's `aria-label` on route grid cells.
- **New Locators Created**: PK 500 (`d365_bom_select_all_checkbox`), 502 (`d365_bom_config_lookup_btn`), 503 (`d365_bom_config_variant_select`), 506 (`d365_bom_item_lookup_btn`), 511 (`d365_route_add_btn`).

### Recent Enhancements (Feb 21, 2026 — Session 2) — type_text Focus Verification & BOM Line Fixes
- **type_text Focus Verification**: `type_text` handler now supports locator-based focus verification. If a locator is assigned to the step, it checks if the correct field has focus before typing. If focus is wrong, clicks the locator to correct it. Logs focus match/mismatch for debugging.
- **BOM Line Tab → Escape**: WF-7B Fill Quantity step changed `press_key_after` from Tab to Escape. Tab was advancing cursor to the next cell ("Per series"), causing the next iteration's item number to be typed into the wrong field.
- **New BOM Line Wait Increase**: Increased "New BOM Line" click wait from 1500ms to 2500ms for D365 to fully render the new row.
- **Locator #512** (`d365_bom_line_item_input`): Created with `name`/`css`/`xpath` strategies targeting `input[name="ItemId"]`, assigned to Fill Item Number step (PK=1737) for focus verification.

### Recent Enhancements (Feb 22, 2026 — Pre-Session) — Grid Helpers, Zoom, Horizontal Scroll
- **`_read_grid_hyperlink_values()`**: New helper method reads all visible `input.dyn-hyperlink` values from the current grid via JS evaluation. Returns sorted list of string values. Used for overshoot detection during `click_dynamic_locator` scrolling — compares visible range against target value to detect when we've scrolled too far.
- **`_scroll_grid_horizontal(direction)`**: New helper scrolls D365 FixedDataTable grids horizontally by dragging the scrollbar face. Uses `drag_to()` approach with manual mouse drag fallback. Supports `left` and `right` directions. Used by `SCROLL_GRID_LEFT`/`SCROLL_GRID_RIGHT` special tokens in `press_key` handler.
- **`_apply_keyboard_zoom()`**: New helper applies browser zoom via `Ctrl+Minus` after first D365 navigation. Reduces viewport zoom to fit more grid columns. Called once per execution session.
- **press_key Special Tokens**: Extended `press_key` handler to support special tokens: `SCROLL_GRID_LEFT`, `SCROLL_GRID_RIGHT` (call `_scroll_grid_horizontal()`), `ZOOM_OUT`, `ZOOM_IN`, `ZOOM_N` (browser zoom via Ctrl+Minus/Plus/0). These work alongside standard key names like `Tab`, `Escape`, `Enter`.
- **Repeat Group s[0].pk Tuple Fix**: Fixed `step.pk` access for repeat-group expanded steps — expanded steps are stored as `(step, iteration_data)` tuples, so the step object needs `s[0]` indexing before accessing `.pk`.
- **type_text Optimization**: Reuses `self.locator_engine` instead of creating new `LocatorEngine` per call. Reduced pre-key wait from 300ms to 100ms. Removed page awareness post-verification block (saved 300-500ms per call).

### Recent Enhancements (Feb 22, 2026) — Dynamic Locators, Select-All Verification, Debug UX
- **`click_dynamic_locator` Action Type**: New executor action that builds locator selectors at runtime by replacing `{{PLACEHOLDER}}` tokens in strategy templates with the step's resolved value. Supports ANY placeholder name (`{{VALUE}}`, `{{ROUTE}}`, `{{ITEM}}`, etc.) via `re.sub(r'\{\{[^}]+\}\}', escaped, strat.value)`. Includes D365 grid scroll support — PageDown up to 30 times to find off-screen elements in virtualized FixedDataTable grids. Used for WF-9 step #15 "Click Route Number Link" with locator #530 (`d365_route_grid_hyperlink`).
- **ActionType Model Expanded**: Added `TYPE_TEXT = "type_text"`, `NAVIGATE = "navigate"`, `CLICK_DYNAMIC = "click_dynamic_locator"` to `ActionType` TextChoices. `max_length` on `WorkflowStep.action_type` and `RecordedAction.action_type` increased from 20 to 30. Migration `0015_add_action_types_and_max_length`.
- **Action Type Dropdowns Updated**: All 4 action type dropdowns (workflow_detail inline edit, workflow_detail add modal, chain_detail inline edit, chain_detail add modal) now include `type_text`, `select_grid_row`, `click_dynamic_locator`, and `read_value`.
- **Select-All Verify & Retry**: After clicking a "select all" step (detected by name containing "select all"), the executor uses `D365PageReader.count_selected_grid_rows()` to verify that rows are actually selected. If not all selected: Retry 1-2 re-finds and clicks the locator element; Retry 3 clicks inside the grid body then presses Ctrl+A. D365 FixedDataTable renders 2-4 duplicate header copies — first click may land on a non-functional shadow copy.
- **`count_selected_grid_rows()` in D365PageReader**: New method in `page_awareness.py`. Counts total vs selected data rows via `aria-selected`, `dyn-marked` class, and `aria-checked` attributes. Also reads header checkbox `aria-checked` state. Supports grid scoping by ID/controlname (e.g. `BOMTable`).
- **Debug Run-From-Step Always Visible**: The ▶ (run from step) and ⚡ (run step only) buttons are now visible whenever debug is active, not just when paused. Slightly dimmed (60% opacity) when execution is running. When clicked while running: auto-enables step-by-step mode to pause at the next step, then queues the rerun/run-single command. Flash message: "Will jump to step X after current step finishes".
- **WF-9 Route Registration Rebuilt**: Completely rebuilt from recording #24 with 20 active steps in 4 phases: NAV (navigate + favorites toggle-safe), FILL (route fields), APPROVE (version approve), ACTIVATE (activate + close). Toggle-safe favorites pattern: Click Favorites (COE) → Try "All routes" (COE) → Re-click Favorites (COE) → Retry "All routes" (COE). Locator #456 fixed to use exact text `//a[@data-dyn-title="All routes"]`.
- **New Locators for WF-9**: #523 (`d365_route_number_hyperlink`), #524 (`d365_route_config_lookup`), #525 (`d365_route_site_lookup`), #526 (`d365_route_versions_tab`), #527 (`d365_route_version_approve_btn`), #528 (`d365_route_version_activate_btn`), #529 (`d365_route_close_btn`), #530 (`d365_route_grid_hyperlink` — dynamic `{{ROUTE}}` template).
- **WF-7B Stabilization Step**: Step #11 "Click Grid Checkbox (accept & stabilize)" added after repeat group to stabilize the BOM grid. Step #7 (Click Item Lookup) deactivated — was reopening lookup after Enter already closed dropdown, causing navigation away. Step #10 `press_key_after` changed from Escape to none.
- **WF-2 Combobox Steps: Enter → Tab**: All combobox steps in WF-2 (Create Released Product) changed from `press_key_after='Enter'` to `press_key_after='Tab'`. Tab cleanly moves focus without triggering D365's heavy combobox validation lookup. Wait times increased to 1500-2000ms. Prevents serial number value from leaking into Tracking Dimension Group field.
- **D365 Page Awareness System**: `page_awareness.py` — `D365PageReader` class with read-only JS evaluation methods: `get_focused_field()`, `get_field_value()`, `count_grid_rows()`, `count_selected_grid_rows()`, `get_grid_row_values()`, `get_page_context()`, `get_error_messages()`, `snapshot()`, `snapshot_short()`. Hooks in executor: pre/post state logging, fill value verification, grid row count verification, select-all verification. Page state panel in chain_detail.html debug UI.

### Recent Enhancements (Feb 22, 2026 — Session 2) — click_dynamic_locator & _click_grid_hyperlink Fixes
- **`click_dynamic_locator` Hybrid Finding (CSS/XPath + JS fallback)**: The action handler uses a two-layer finding strategy. Primary: CSS/XPath selectors from locator strategies with Playwright `is_visible(timeout=2000)` auto-wait — critical because after PageDown, D365 virtualized grids take a few hundred ms to render new rows and Playwright retries during the timeout window. Fallback: JS `.value` property search via `frame.evaluate()` across all frames — runs once with no retry, used when CSS attribute selectors don't match (D365 sometimes sets `.value` via JS without updating the HTML attribute).
- **`_click_grid_hyperlink()` Coordinate-Based dblclick**: Rewritten to use raw `page.mouse.dblclick(cx, cy)` at bounding box coordinates instead of `element.dblclick()`. D365 grid hyperlinks (`input.dyn-hyperlink`) respond to real mouse events for navigation — Playwright's abstracted element-level dblclick selects the row but doesn't trigger D365's hyperlink navigation handler. Three fallback methods: A) `mouse.dblclick(cx,cy)`, B) two rapid `mouse.click(cx,cy)`, C) JS `el.click()` twice. Each method waits 2000ms then checks `element.is_visible()` — only proceeds to next method if element still present.
- **`scroll_into_view_if_needed()` Before Click**: D365 FixedDataTable pre-renders buffer rows just outside the visible viewport. CSS selectors can find these off-screen elements and `is_visible()` returns True (they have dimensions in the DOM). But clicking them has no effect because they're outside the viewport. Fix: call `element.scroll_into_view_if_needed(timeout=3000)` before getting bounding box coordinates, ensuring the element is in the visible viewport when clicked.
- **Grid Focus + Escape for Scroll Mode**: Before scrolling with PageDown, the code clicks `input.dyn-hyperlink.first` to focus the grid. But this puts the cell in edit mode (text selected), and PageDown in edit mode doesn't scroll the grid. Fix: press `Escape` after the focus click to exit cell edit mode, restoring grid-level focus so PageDown scrolls properly.
- **BATCH_SIZE 3→1**: Changed scroll batch from 3 PageDowns to 1 PageDown per check cycle. With batch=3, the grid could scroll 3 pages (~33 rows) past the target in one batch — by the time `_try_all()` runs, the target row is above the viewport and virtualized away. With batch=1, every PageDown is followed by a check, preventing overshoot. MAX_BATCHES increased from 12 to 30 to compensate.

### Recent Enhancements (Feb 22, 2026 — Session 3) — Mouse Wheel Scroll & Activate Button Fix
- **Mouse Wheel Scroll Replaces PageDown**: `click_dynamic_locator` grid scrolling completely rewritten from keyboard PageDown to `page.mouse.wheel(0, 800)`. PageDown was unreliable because it depends on grid keyboard focus — clicking a grid cell enters edit mode, and Escape doesn't always exit it. Mouse wheel events work regardless of focus state. Positions mouse over `.fixedDataTableLayout_body` center (fallback: first `input.dyn-hyperlink` position), then scrolls in 800px increments with 600ms wait between each. Overshoot detection and scroll-back via `mouse.wheel(0, -400)` still works. Grid bottom detection requires 3 consecutive unchanged last visible values to prevent false positives.
- **WF-9 Route Filter Replaces Scroll**: Replaced unreliable scroll-based route finding (step #6 `click_dynamic_locator` with PageDown/wheel scroll) with D365 column filter approach. New steps 7-10: Click Route Number column header (#534) → Fill filter with `{{ROUTE}}` (#535, combobox mode) → Click Apply (#536) → `click_dynamic_locator` (#530) finds the single visible row and dblclicks to navigate. Eliminates all grid scrolling — filter shows only the matching route. Recording pk=26, auto-converted workflow pk=95, locators #534/#535/#536 created during conversion.
- **New Locators for Route Table Filter**: #534 (`rec_v2_RouteTable_GridRouteId_0_header` — column header, xpath contains `RouteTable_GridRouteId` + `0_header`), #535 (`rec_v2_FilterField_RouteTable_GridRouteId_RouteId_Input_0` — filter input, name/aria-label/xpath strategies), #536 (`rec_v2_RouteTable_GridRouteId_ApplyFilters` — Apply button, exact ID + name + contains + text fallbacks).

### Recent Enhancements (Feb 22, 2026 — Session 3 cont.) — Activate Button Locator Fix
- **Locator #465 Fix (d365_route_version_activate_btn)**: WF-9 step #19 "Click Activate Route Version" was finding the `<span class="button-label">` label element but clicking it had no effect. D365 handles button events on the actual `<button>` element, not the label span. Fixed by adding new strategies targeting the button element directly.
- **D365 Button Label Pattern**: D365 toolbar buttons have structure `<button id="prefix_BOMRouteVersionActivate"><span id="prefix_BOMRouteVersionActivate_label" class="button-label">Activate</span></button>`. Clicking the inner `<span>` does NOT trigger the button action. Always target the `<button>` element (exclude `_label` suffix) or use `//button[.//span[text()="ButtonText"]]`.
- **Updated Locator #465 Strategies**: P0 xpath `//*[contains(@id, "BOMRouteVersionActivate") and not(contains(@id, "_label"))]` (button element), P1 xpath `//button[.//span[text()="Activate"]]` (text-based), P2 xpath `//*[contains(@id, "RouteVersionActivate_label")]` (label fallback). Deactivated case-sensitive strategy that had 0 successes / 8 failures.

### D365 Grid Hyperlink Click Pattern (Reference for Future Similar Tasks)
**Problem**: D365 FixedDataTable grids use virtualized rows (only visible rows in DOM) and hyperlink inputs (`input.dyn-hyperlink`) that require double-click to navigate to a detail page. Single click only selects the row.

**Architecture** (`click_dynamic_locator` action in `executor.py`):
```
click_dynamic_locator(value="ROUTE-0117")
  │
  ├── Step 1: Build selectors from locator strategies
  │   └── Replace {{PLACEHOLDER}} tokens with resolved value
  │       e.g. css: input[value="{{ROUTE}}"].dyn-hyperlink → input[value="ROUTE-0117"].dyn-hyperlink
  │
  ├── Step 2: _try_all() — Find element in visible area
  │   ├── _find_and_dblclick_selectors(main_page) — CSS/XPath with 2000ms auto-wait
  │   ├── _find_and_dblclick_selectors(each_iframe) — same for iframes
  │   └── _js_find_and_dblclick() — JS .value search fallback across all frames
  │
  ├── Step 3: If not found → Scroll grid
  │   ├── Focus grid: click input.dyn-hyperlink.first + Escape (exit edit mode)
  │   ├── Loop: 1 PageDown → wait 400ms → _try_all() → check overshoot
  │   ├── Overshoot detection: compare visible values vs target (string compare)
  │   ├── If overshot: scroll back up with PageUp, checking each time
  │   └── Last resort: incremental PageDown scroll
  │
  └── Step 4: _click_grid_hyperlink(element, value) — Navigate
      ├── scroll_into_view_if_needed() — bring off-screen buffer rows into viewport
      ├── Get bounding_box() → cx, cy coordinates
      ├── Method A: page.mouse.dblclick(cx, cy) → wait 2000ms → check is_visible
      ├── Method B: mouse.click + mouse.click (rapid) → wait 2000ms → check
      └── Method C: JS el.click() + el.click() → wait 2000ms
```

**Key Lessons Learned**:
1. **CSS `input[value="X"]` checks HTML attribute, JS `.value` checks property** — D365 may set one or both. Use CSS/XPath as primary (with Playwright auto-wait) and JS `.value` search as fallback.
2. **Playwright auto-wait vs JS evaluate**: `loc.is_visible(timeout=2000)` retries for up to 2s (essential after PageDown when rows need time to render). `frame.evaluate()` runs once immediately with no retry.
3. **`element.dblclick()` ≠ `page.mouse.dblclick(cx, cy)`**: For D365 hyperlinks, raw mouse events at coordinates trigger navigation. Playwright element-level dblclick only selects the row.
4. **D365 pre-renders buffer rows off-screen**: CSS selectors find them, `is_visible()` returns True, but clicks have no effect. Always `scroll_into_view_if_needed()` before clicking.
5. **Grid focus + edit mode blocks scrolling**: Clicking a grid input enters edit mode. Press Escape to restore grid-level focus before using PageDown.
6. **Batch scrolling overshoots**: With BATCH_SIZE>1, PageDown jumps multiple pages and the target row gets virtualized away before the check runs. BATCH_SIZE=1 prevents this.
7. **Post-dblclick wait must be 2000ms**: D365 SPA navigation takes 1-2s. With only 500ms wait, `is_visible()` returns True (element not yet gone), causing Methods B/C to fire extra clicks that confuse D365.
8. **ElementHandle vs Locator API**: `ElementHandle.is_visible()` takes NO parameters. `Locator.is_visible(timeout=X)` accepts timeout. Passing `timeout` to ElementHandle causes TypeError silently caught by except blocks. Use `is_visible()` with no args for compatibility with both types.

**Locator Strategy Pattern for Dynamic Grid Values**:
```
Locator: d365_route_grid_hyperlink (pk=530)
Strategies (ordered by priority):
  P0 css:   input[value="{{ROUTE}}"].dyn-hyperlink
  P1 xpath: //input[@value="{{ROUTE}}" and contains(@class, "dyn-hyperlink")]
  P2 xpath: //input[@value="{{ROUTE}}"]
```
At runtime, `{{ROUTE}}` is replaced with the step's resolved value (e.g. "ROUTE-0117"). Any `{{...}}` placeholder name works — they're all replaced via `re.sub(r'\{\{[^}]+\}\}', escaped, strat.value)`.

### Recent Enhancements (Feb 22, 2026 — Session 4) — WF-9 Filter Cleanup & Chain Data Flow
- **Step #22 "Click Apply Filter" Deactivated**: Step #21 fills the Item Number filter with `press_key_after='Enter'`, which applies the filter and closes the panel instantly. Step #22 "Click Apply Filter" then finds nothing (button already gone). Deactivated as redundant — Enter handles it.
- **Step #21 wait_after Increased to 1500ms**: Gives D365 time to apply the filter and re-render the grid before step #23 (Activate) runs.
- **Locator #522 Hardened**: Added P3 `contains(@id, "RouteVersion_ItemId_ApplyFilters")` fallback xpath strategy (standard D365 dynamic-prefix pattern).
- **Chain 11 Cleaned Up**: Deactivated link #30 (redundant "filter for route number" workflow pk=95) — those filter steps are already integrated into WF-9 steps 7-10. Chain 11 now has 2 active links: WF-0 (login) + WF-9 (route registration).
- **Chain 10 Context Mapping Issue Identified**: WF-2B saves captured item number as `ITEM_NO` (underscore) via `save_result_as`. WF-9 templates use `{{ITEM NO}}` (space). Chain 10 link #100 context_mapping `{'ITEM_NO': 'ITEM_NO'}` puts value under underscore key, but `get_value()` finds the empty space-key from initial row_data first. Fix needed: change context_mapping to `{'ITEM NO': 'ITEM_NO'}` so the captured value overwrites the empty key.
- **D365 Filter Pattern — Enter vs Apply Button**: When D365 combobox filter fields have `press_key_after='Enter'`, Enter applies the filter AND closes the filter panel. No separate "Click Apply" step needed — it's redundant and will fail (element gone). Use Enter on the fill step with adequate `wait_after` instead.

### Recent Enhancements (Feb 24, 2026) — WF-11 Movement Journal: Steps 27-40 & Fixes
- **WF-11 Movement Journal (pk=89) Steps 27-40 Built**: Complete workflow for D365 Movement Journal creation and posting. 40 active steps total covering: navigation, journal creation, config/location/serial handling, journal posting, and home navigation.
- **Config Dimension → Lookup Pattern (Steps 27-28)**: Replaced broken inline `Fill Config Dimension` (old step #27 using `inventDimCombinationRecId_InventoryDimension1_ConfigId`) with two-step lookup pattern: Click Config Lookup Button (locator pk=541, `dyn-lookup-button` within `InventoryDimension1_ConfigId`) → Select Config Variant (locator pk=542, `EcoResProductAllVariants_DisplayProductNumber` grid row). Both `continue_on_error=True`.
- **Scroll Grid Right Before Fill Location (Step 29)**: New `press_key` step with `SCROLL_GRID_RIGHT` value. D365 journal line grid doesn't show Location column without horizontal scrolling. Uses existing `_scroll_grid_horizontal()` mechanism from executor.py. `continue_on_error=True`.
- **Fill Location (Step 30)**: Fills 'Default' into location field (locator pk=543, `InventDim1_wMSLocationId` name strategy). Combobox mode with Tab to confirm.
- **Right-Click Serial Lookup → View Details (Steps 31-32)**: New `right_click` action type opens context menu on serial lookup button (locator pk=544), then clicks "View details" menu item (locator pk=545, text strategy `//span[text()="View details"]`). Navigates to InventSerial page.
- **`right_click` Action Type**: New ActionType enum value `RIGHT_CLICK = "right_click"`. Handler in `D365InteractionEngine.execute_interaction()` uses `element.click(button="right")`. Migration 0016. Added to all 4 action type dropdown templates.
- **Serial Creation on InventSerial Page (Steps 33-35)**: Click New (locator pk=546) → Fill Serial Number with `{{SERIAL NO}}` template (locator pk=547, `InventSerialId` name) → Click Back to return to journal (locator pk=548, `SystemDefinedBackButton` xpath).
- **Locator #546 Fix (`d365_invent_serial_new_btn`)**: Initial xpath `//*[contains(@id, "InventSerial") and contains(@id, "SystemDefinedNewButton")]` matched both `<button>` and inner `<span>` label. Fixed P0 to `//button[contains(@id, "InventSerial") and contains(@id, "SystemDefinedNewButton")]` targeting only the button element.
- **Fill Serial in Journal Line (Step 36)**: Fills serial number into journal line combobox (locator pk=549, `InventDim1_inventSerialId` name strategy). Combobox mode with Tab.
- **Read Movement Journal Number (Step 37)**: `read_value` action reads journal number from field (locator pk=550, `InventJournalTable_JournalId` name + css + xpath strategies). Saves to context via `save_result_as`. `continue_on_error=True`.
- **Post & Home (Steps 38-40)**: Post Journal → Post OK → Click Home. Existing locators for post buttons; new Home button locator (pk=551, `d365_home_btn`).
- **Account-Gated Steps**: Journal Name (steps 5-15) and Customer Account (steps 20-24) steps use `condition_value` field matching account code. Each account gets its specific journal name and customer account.
- **10 New Locators Created (pk=541-550)**: `d365_journal_config_lookup_btn`, `d365_journal_config_variant_select`, `d365_journal_line_location`, `d365_journal_serial_lookup_btn`, `d365_context_menu_view_details`, `d365_invent_serial_new_btn`, `d365_invent_serial_header_input`, `d365_invent_serial_back_btn`, `d365_journal_line_serial_dd`, `d365_journal_number_field`. Each with 3 strategies (name/css/xpath).
- **D365 Button vs Label Pattern Reinforced**: D365 buttons have `<button id="X"><span id="X_label">`. Always target `//button[contains(@id, "...")]` not `//*[contains(@id, "...")]` to avoid matching the inner span which doesn't respond to click events.

### Recent Enhancements (Feb 24, 2026 — Session 2) — WF-7B Scroll Fix & Chain Context Mapping
- **WF-7B Scroll Step Before Select-All**: Added `press_key` step (pk=1847, order 1) with `PageDown` value before Select All Checkbox (step #2). D365 BOM Table page has "Bill of materials header" FastTab section above the grid which pushes the BOM lines grid below the viewport. The scroll brings the grid into view so the select-all checkbox click lands correctly. `continue_on_error=True`, `wait_after=500ms`.
- **WF-7B Step Reordering Cleanup**: Renumbered all 20 active steps cleanly from 1-20 (no gaps). Moved all inactive steps (pk=1739, 1745, 1746, 1742) to high order numbers (9996-9999) to avoid UNIQUE constraint collisions during future reordering.
- **Fractional Horizontal Scroll**: `_scroll_grid_horizontal()` in `executor.py` now accepts `distance_fraction` parameter (0.0-1.0, default 1.0). When fraction < 1.0, scrolls relative to current face position instead of to the edge. press_key handler parses fraction from `SCROLL_GRID_RIGHT:0.3` format (colon-separated). WF-11 step #30 uses `SCROLL_GRID_RIGHT:0.3` for a gentle 30% scroll.
- **Chain Context Mapping Fix (ITEM NO vs ITEM_NO)**: WF-2B (link 40) captures D365-generated item number as `ITEM_NO` (underscore) via `save_result_as`. WF-9 and WF-11 templates use `{{ITEM NO}}` (space). Fixed context_mapping on chain 10 links:
  - Link #100 (WF-9): `{'ITEM_NO': 'ITEM_NO'}` → `{'ITEM NO': 'ITEM_NO'}` — captured value now overwrites the empty space-key
  - Link #110 (Workflow approve): `{'ITEM_NO': 'ITEM_NO'}` — unchanged, templates use `{{ITEM_NO}}` (underscore)
  - Link #120 (WF-11): `{'ITEM_NO': 'ITEM_NO'}` → `{'ITEM NO': 'ITEM_NO'}` — same fix as WF-9
- **Read Journal Number Moved Earlier**: WF-11 step "Read Movement Journal Number" (pk=1844) moved from order 37 to order 19 (after Fill Description, before Click OK). Journal number is available during creation dialog, not after posting.
- **Locator #546 Fix**: `d365_invent_serial_new_btn` P0 xpath changed from `//*[contains(@id...)]` to `//button[contains(@id, "InventSerial") and contains(@id, "SystemDefinedNewButton")]` to avoid matching inner `<span>` label.

### Recent Enhancements (Feb 24, 2026 — Session 3) — WF-7B Grid Activation & WF-9 Site Locator
- **WF-7B Select-All Grid Activation Fix**: D365 FixedDataTable renders 2-4 duplicate header rows. The select-all checkbox xpath `[1]` picks the first copy, which is non-functional before the grid is "activated" by user interaction. Fix: Added "Click Grid Body (activate grid)" step (pk=1848, order 2) with new locator pk=551 (`d365_bom_grid_body_click`) before the Select All step. This clicks any element inside the grid body to initialize it, making the header checkbox functional. Strategies target `fixedDataTableLayout_body//input.dyn-hyperlink` and `role="row"//input`. Wait 800ms after click, 1000ms after select-all.
- **WF-7B Updated Step Order**: 21 active steps (1-21): PageDown → Click Grid Body → Select All → Delete → Confirm → [repeat: New Line, Fill Item, Config, Variant, Qty] → Grid Checkbox → Approve/Activate flow.
- **WF-9 Fill Site Locator Fix (pk=532)**: Old strategies targeted `SiteId`/`RouteVersion_SiteId` (wrong field name). Actual D365 element: `<input id="InventoryDimensions_InventSiteId_..." role="combobox" aria-label="Site">`. New strategies: P0 `aria-label: Site`, P1-P3 xpath with `InventSiteId`, P4 css `input[aria-label="Site"]`. Interaction mode changed from `standard_input` to `combobox`.
- **Chain Context Mapping Fix Verified**: Confirmed `get_value()` template resolution works correctly with new context mappings — captured D365 item number flows through `{'ITEM NO': 'ITEM_NO'}` mapping to resolve `{{ITEM NO}}` templates in WF-9 and WF-11.

### Recent Enhancements (Feb 24, 2026 — Session 4) — Locator Fixes, Movement Journal Number, Result Saving
- **WF-9 Fill Site Locator Refined (pk=532)**: Reduced to 2 clean strategies filtering by `role="combobox"` to disambiguate from readonly duplicates (`role="textbox"`). P0 xpath: `//input[contains(@id, "InventoryDimensions_InventSiteId") and @role="combobox"]`, P1 css: `input[id*="InventoryDimensions_InventSiteId"][role="combobox"]`. D365 renders multiple inputs with similar IDs — editable one has `role="combobox"`, readonly copies have `role="textbox"`.
- **WF-11 Fill Serial Locator Fix (pk=480)**: Old strategy targeted wrong field `inventDimCombinationRecId_InventoryDimension1_InventSerialId`. Actual D365 element: `<input id="InventoryDimensionsGrid_inventSerialId_..." role="combobox">`. New strategies: P0 xpath with `InventoryDimensionsGrid_inventSerialId` + `@role="combobox"`, P1 css equivalent.
- **WF-11 Horizontal Scroll Removed**: Deactivated `SCROLL_GRID_RIGHT` step (pk=1846) before Fill Location. D365 grid columns are always in the DOM (only rows virtualized), so Playwright's `fill()` auto-scrolls elements into view. `_scroll_grid_horizontal()` drag operations generated mousedown/mouseup events D365 interprets as clicks, causing unintended vertical scrolling.
- **WF-11 Config Variant Escape Removed**: Removed `press_key_after='Escape'` from "Select Config Variant" step (pk=1836). Escape was causing issues; click-to-select is sufficient.
- **WF-2 Click OK Continue-on-Error**: Step pk=1392 ("Click OK - Released Product") set to `continue_on_error=True`. When OK dialog is not shown and next field is already available, step can be safely skipped.
- **Movement Journal Number on ERPJobData**: New `movement_journal_number` CharField on `ERPJobData` model. Migration `0017_add_movement_journal_number`. Job data detail page ERP Output section expanded to 4-column grid with Movement Journal # field.
- **Result Saving in All Execution Paths**: After successful chain completion, captured context values are saved back to `ERPJobData`: `ITEM_NO` → `job_data.item_number`, `JOURNAL_NUMBER` → `job_data.movement_journal_number`. Implemented in 3 paths: (1) single workflow execution in views.py, (2) regular chain execution in `chain_executor.py`, (3) debug chain execution in `executor.py` (`start_debug_chain`).
- **D365 Input Disambiguation Pattern**: When D365 renders multiple `<input>` elements with similar IDs (e.g., `InventSiteId_0_0_input`, `_0_1_input`, `_0_2_input`), always filter by `@role="combobox"` for the editable field. Readonly duplicates have `role="textbox"`. This is the definitive pattern for all future D365 locators.

### Recent Enhancements (Feb 24, 2026 — Session 5) — Size Fraction Display & Collapsible Sections
- **Size Fraction Formatting**: All decimal size displays (e.g., `12.000`, `6.125`, `8.500`) now show as clean fractions (`12`, `6 1/8`, `8 1/2`). Uses Python `fractions.Fraction` with `.limit_denominator(32)` for common drill bit denominators (1/8, 1/16, 1/32).
- **`format_size_fraction()` Utility**: New function in `apps/erp_automation/templatetags/erp_filters.py` converts Decimal → fraction string. Handles edge cases: None/empty → "", whole numbers drop `.000`, pure fractions like `0.875` → `7/8`.
- **`size_fraction` Template Filter**: Django template filter `{{ value|size_fraction }}` wraps `format_size_fraction()`. Used in `job_data_detail.html`, `job_data_list.html`, `recording_detail.html`.
- **`ERPJobData._format_size()` Method**: Model method that formats `size_inches` as fraction string, falling back to `size_raw`. Called by `get_row_data()` for the `SIZE` template variable — so `{{SIZE}}` in workflow steps resolves to fraction format (e.g., `8 1/2` not `8.500`).
- **Job Data Detail Collapsible Sections**: All 11 sections in `job_data_detail.html` made collapsible with Alpine.js toggle pattern. Default: Section 1 (Core Info) and Section 7 (ERP Output) open, all others collapsed. "Collapse All / Expand All" buttons at top using `$dispatch('toggle-all-sections')` event pattern.

---

## ERP Automation: Complete Architecture Reference

### Recent Bug Fixes (Feb 25, 2026) — System Audit Fixes
- **Fix #1: WorkOrderCreateEnhancedForm KeyError**: `WorkOrderCreateEnhancedForm.__init__()` in `apps/workorders/forms.py` referenced `self.fields['customer']` and `self.fields['from_location_text']` which were not in `Meta.fields`, causing KeyError on form instantiation. Fixed by adding both fields to `Meta.fields` with `HiddenInput` widgets (they're populated by JS from serial number lookup, same pattern as drill_bit/design/bom).
- **Fix #2: Stock Divergence — Issue/Transfer/Adjustment Missing Updates**: Three posting views (`StockIssuePostView`, `StockTransferPostView`, `StockAdjustmentDocPostView`) in `apps/inventory/views.py` created incomplete `StockLedger` entries and never updated `StockBalance` or `InventoryStock`. Fixes:
  1. **Extracted shared `_update_stock_balance_shared()` function** — standalone utility replacing GRNPostView's private method. Called by all 4 posting views (GRN, Issue, Transfer, Adjustment).
  2. **StockIssuePostView**: Added missing `uom`, `owner_party`, `ownership_type`, `quality_status`, `condition` fields from line; added `issue_line` FK; fixed `reference_id` to be per-line (was per-document — violated UniqueConstraint); added idempotency check; added StockBalance/InventoryStock update; uses enum `TransactionType.ISSUE` instead of string.
  3. **StockTransferPostView**: Fixed non-existent field references (`line.from_location` → `transfer.from_location`, `line.to_location` → `transfer.to_location`, `line.qty_transferred` → `line.qty_shipped`); added all 5 dimension fields with from/to split for owner and quality; separate reference_ids for OUT/IN entries; added StockBalance update for BOTH locations.
  4. **StockAdjustmentDocPostView**: Fixed invalid `transaction_type="ADJUSTMENT"` to use `ADJ_IN`/`ADJ_OUT` based on qty sign; added all 5 dimension fields; added `adjustment_line` FK; per-line reference_id and idempotency.
- **Fix #3: SyncStockFromBalancesView Crash**: Two bugs in `SyncStockFromBalancesView` at `/inventory/admin/sync-stock/`: (1) Referenced non-existent `Lot` model instead of `MaterialLot` (line 7081), (2) Used `redirect('inventory:balance_list')` instead of correct `'inventory:stock_balance_list'` (line 7113).
- **Fix #4: Status Transition Validation**: Added `STATUS_TRANSITIONS` dict and `clean()` method to 7 models to prevent invalid status changes. Django `clean()` is called by `full_clean()` from forms/admin but NOT by direct `Model.save()`. Each model defines allowed transitions and raises `ValidationError` on invalid ones.
  - **Design** (`apps/technology/models.py`): DRAFT → ACTIVE/OBSOLETE, ACTIVE → OBSOLETE, OBSOLETE = terminal
  - **BOM** (`apps/technology/models.py`): Same transitions as Design (DRAFT/ACTIVE/OBSOLETE)
  - **WorkOrder** (`apps/workorders/models.py`): Full 10-status flow: DRAFT → PLANNED → RELEASED → IN_PROGRESS → QC_PENDING → QC_PASSED → COMPLETED. ON_HOLD can resume to PLANNED/RELEASED/IN_PROGRESS. CANCELLED = terminal.
  - **GoodsReceiptNote** (`apps/inventory/models.py`): DRAFT → PENDING_QC/CONFIRMED/CANCELLED. CONFIRMED = terminal (stock posted to ledger, irreversible).
  - **PurchaseOrder** (`apps/supplychain/models.py`): 10-status flow: DRAFT → PENDING_APPROVAL → APPROVED → SENT → ACKNOWLEDGED → IN_PROGRESS → PARTIALLY_RECEIVED → COMPLETED → CLOSED. CANCELLED/CLOSED = terminal.
  - **Workflow** (`apps/erp_automation/models.py`): draft → active/archived, active → archived, archived = terminal. Note: lowercase status values per `WorkflowStatus` choices.
  - **ERPJobData** (`apps/erp_automation/models.py`): DRAFT → READY → SENT → COMPLETED. ERROR can retry back to READY. COMPLETED = terminal.
- **Fix #5: HDBS Case Mismatch**: `sync_hdbs_from_designs` management command used case-sensitive dictionary lookup, causing `Design.hdbs_type='GT65RHs'` to miss `HDBSType.hdbs_name='GT65RHS'`. Fixed by using `.lower()` keys in the lookup dict. DesignHDBS junction table now populated (was empty). Also logs case-match warnings during sync (e.g., "Design 'GT65RHs' -> HDBSType 'GT65RHS'").

---

## ERP Automation: Complete Architecture Reference

### What the System Does (End-to-End)
The ERP Automation module automates D365 (Dynamics 365) ERP operations for drill bit repair job cards. The full pipeline:
1. **Upload** Job Card Excel → `job_card_parser.py` extracts all fields
2. **Route Selection** → `route_selector.py` auto-selects production route
3. **Chain Execution** → `chain_executor.py` runs linked workflows sequentially
4. **Each Workflow** → `executor.py` executes steps via Playwright browser automation
5. **Results Captured** → Item number, journal number saved back to `ERPJobData`

### What Participates in the Chain vs What Doesn't

**Active in Chain Execution (Chain 10 — ARAMCO FC Repair):**
| Link | Workflow | Purpose | Key Templates | Captures |
|------|----------|---------|---------------|----------|
| 10 | WF-0 (Login) | ADFS login | `{{ERP_USERNAME}}`, `{{ERP_PASSWORD}}` | — |
| 20 | WF-1 (Navigate) | Go to Create Product page | — | — |
| 30 | WF-2 (Create Item) | Fill product master fields | `{{SERIAL NO}}`, `{{SIZE}}`, `{{TYPE}}`, `{{FROM}}` | — |
| 40 | WF-2B (Read Item#) | Capture generated item number | — | `ITEM_NO` |
| 50 | WF-3 (Product Details) | Fill dimensions, tracking groups | `{{ITEM_GROUP}}`, `{{BODY_MATERIAL}}` | — |
| 60 | WF-4 (Release Product) | Release and approve | — | — |
| 70 | WF-5 (BOM Lookup) | Navigate to BOM table | `{{MAT NO.}}` | — |
| 80 | WF-6 (BOM Version) | Create BOM version | — | — |
| 90 | WF-7B (BOM Lines) | Delete old + add new BOM lines | `{{LOOP_ITEM}}`, `{{LOOP_QTY}}` (repeat group) | — |
| 100 | WF-9 (Route) | Register production route | `{{ITEM NO}}`, `{{ROUTE}}` | — |
| 110 | WF-10 (Approve) | Approve workflow | `{{ITEM_NO}}` | — |
| 120 | WF-11 (Journal) | Create movement journal | `{{ITEM NO}}`, `{{SERIAL NO}}` | `JOURNAL_NUMBER` |

**NOT in Chain (standalone/utility):**
- Recording sessions — used to create new workflows
- FieldMapping model — designed but unused (templates handle mapping)
- ItemCounter — generates item numbers but chain reads from D365
- ERPEnvironment — just stores URLs for selection

### Context Variable Flow Through Chain
```
Initial row_data (from ERPJobData.get_row_data()):
  {SERIAL NO, SIZE, TYPE, MAT NO., FROM, ACCOUNT, ROUTE, BOM_LINES, ...}

Link 40 (WF-2B): save_result_as="ITEM_NO" → context = {ITEM_NO: "RPR-0042"}

Link 100 (WF-9): context_mapping = {"ITEM NO": "ITEM_NO"}
  → merged row_data: {ITEM NO: "RPR-0042", ...}  (overwrites empty initial value)

Link 120 (WF-11): same context_mapping + save_result_as="JOURNAL_NUMBER"
  → context = {ITEM_NO: "RPR-0042", JOURNAL_NUMBER: "MVT-0891"}

Final: job_data.item_number = "RPR-0042", job_data.movement_journal_number = "MVT-0891"
```

### Action Types Catalog (17 Total)

| Action | Purpose | Locator? | Value? | D365 Notes |
|--------|---------|----------|--------|------------|
| `click` | Click element | Required | — | Uses InteractionMode chain; combobox→Alt+Down, lookup→double-click |
| `fill` | Type into field | Required | Required | Mode-aware: combobox→clear+type+Tab; standard→fill() |
| `select` | Select dropdown option | Required | Required | D365 has NO native `<select>`; clicks the option element |
| `check` | Toggle checkbox | Required | "true"/"false" | D365 checkboxes are custom divs; fallback: click→force-click→Space |
| `type_text` | Type into focused element | Optional (verify) | Required | Uses `keyboard.insert_text()` (bypasses autocomplete); for repeat loops |
| `press_key` | Press keyboard key | — | Key name | Special: `SCROLL_GRID_RIGHT:0.3`, `ZOOM_OUT`, `PageDown` |
| `click_dynamic_locator` | Click element with runtime value | Required (template) | Required | `{{PLACEHOLDER}}` replaced at runtime; mouse wheel grid scroll |
| `select_grid_row` | Find and click grid row | — | Search value | JS scans rows, Playwright mouse-clicks (not JS click) |
| `read_value` | Read field value to context | Required | — | `save_result_as` stores to context; tries input_value→inner_text |
| `navigate` | Wait for SPA navigation | — | — | D365 SPA: waits for domcontentloaded, applies zoom |
| `goto_url` | Navigate to URL | — | URL | 60s timeout, applies zoom after |
| `right_click` | Context menu | Required | — | `element.click(button="right")` |
| `wait_time` | Explicit wait | — | Milliseconds | Direct `page.wait_for_timeout()` |
| `screenshot` | Capture page | — | — | Saved to screenshots dir |
| `assert_text` | Verify text content | Required | Expected text | Substring match |
| `assert_visible` | Verify element visible | Required | — | Boolean check |

### Interaction Modes (10 Total)

| Mode | When Used | Click Chain | Fill Chain |
|------|-----------|------------|------------|
| `auto` | Default — detect at runtime | Detect from DOM attributes | — |
| `standard_input` | Regular text fields | click → force-click | fill() → click+type |
| `combobox` | D365 combobox (`role="combobox"`) | click → Alt+ArrowDown | clear+type → Tab |
| `lookup_button` | D365 lookup "..." buttons | click → 500ms → click again | — |
| `custom_dropdown` | Already-open dropdown options | click | — |
| `checkbox_toggle` | D365 custom checkboxes | click → force-click → Space | — |
| `dialog_button` | OK/Cancel/Yes/No buttons | click → force-click → Enter | — |
| `nav_button` | Toolbar buttons (New/Save) | click → force-click → JS click | — |
| `tab_header` | D365 form tab headers | scroll into view → click | — |
| `segmented_entry` | Multi-part input controls | click → force-click | click+type (segment) |

### D365 Element Patterns — Recording Best Practices

#### Pattern 1: Dynamic IDs (Most Common)
**Problem**: D365 prepends session-specific prefixes: `ecoresproductdetailsextendedgrid_2_SystemDefinedNewButton`
**Solution**: Use `contains(@id)` xpath: `//*[contains(@id, "SystemDefinedNewButton")]`
**Recording**: Converter auto-strips prefix and generates double-contains xpath
**Best Locator**: `xpath: //*[contains(@id, "StablePart1") and contains(@id, "StablePart2")]`

#### Pattern 2: Combobox Fields
**Element**: `<input role="combobox" name="FieldName" aria-label="Label">`
**Interaction**: Click → Alt+ArrowDown (opens dropdown) → Type → Tab (confirms)
**Best Locator**: `name: FieldName` (most stable, no dynamic prefix)
**Alternative**: `xpath: //input[@role="combobox" and @name="FieldName"]`
**NEVER use**: Enter after combobox (triggers heavy validation lookup); use Tab instead

#### Pattern 3: Lookup Buttons ("..." flyout)
**Element**: `<div class="lookupButton">` inside `<div data-dyn-controlname="Config">`
**Interaction**: Click once (focus) → 500ms → Click again (open flyout)
**Best Locator**: `xpath: //*[@data-dyn-controlname="Config"]//div[contains(@class, "lookupButton")]`
**Key**: Two clicks required; single click only focuses the button

#### Pattern 4: Grid Hyperlinks (FixedDataTable)
**Element**: `<input class="dyn-hyperlink" value="ROUTE-0117">`
**Interaction**: Double-click at coordinates (not element.dblclick()) to navigate
**Best Locator**: Dynamic template: `css: input[value="{{ROUTE}}"].dyn-hyperlink`
**Key**: Grid is virtualized — only visible rows in DOM. Must scroll to find off-screen rows.
**Scroll**: Mouse wheel (not PageDown — requires grid focus). Check overshoot after each scroll.

#### Pattern 5: Duplicate Input Fields
**Problem**: D365 renders multiple `<input>` with similar IDs (e.g., `InventSiteId_0_0_input`, `_0_1_input`, `_0_2_input`)
**Editable**: `role="combobox"` — this is the one to target
**Readonly copies**: `role="textbox"` — clicking these does nothing
**Solution**: Always filter by `@role="combobox"` in locator strategies
**Best Locator**: `xpath: //input[contains(@id, "InventSiteId") and @role="combobox"]`

#### Pattern 6: Buttons vs Labels
**Structure**: `<button id="X"><span id="X_label" class="button-label">Text</span></button>`
**Problem**: Clicking `<span>` (the label) does NOT trigger button action
**Solution**: Target `<button>` element, exclude `_label` suffix
**Best Locator**: `xpath: //button[contains(@id, "ActivateBtn") and not(contains(@id, "_label"))]`
**Alternative**: `xpath: //button[.//span[text()="Activate"]]`

#### Pattern 7: FixedDataTable Header Duplicates
**Problem**: D365 grids render 2-4 copies of header rows. Select-all checkbox in first copy is non-functional.
**Solution**: Click any element inside grid body FIRST to "activate" the grid, then click select-all
**Best Practice**: Add a "Click Grid Body" step before "Select All" in workflows

#### Pattern 8: D365 Dialog Buttons (OK/Cancel)
**Element**: `<button class="CommandButton">` with `data-dyn-controlname` containing "ok"/"button"
**Interaction**: Click → force-click fallback → Enter fallback
**Key**: Skip error checking after dialog buttons (D365 always shows processing messages)
**Best Locator**: `xpath: //*[contains(@id, "OKCommand") and not(contains(@id, "_label"))]`

#### Pattern 9: D365 Filter Columns (Grid Filtering)
**Instead of scrolling** to find a row, use D365's built-in column filter:
1. Click column header → opens filter panel
2. Fill filter value (combobox mode, press Enter to apply)
3. Enter applies filter AND closes panel — no separate "Apply" step needed
4. Grid now shows only matching row(s) → click_dynamic_locator finds it immediately
**Key**: Enter on filter field is sufficient. Don't add a "Click Apply" step (redundant — button gone after Enter).

#### Pattern 10: Horizontal Scroll (Grid Columns)
**Avoid explicit scroll steps**: D365 grid columns are always in DOM (only rows virtualized). Playwright's `fill()` and `click()` auto-scroll elements into view via `scrollIntoViewIfNeeded()`.
**If needed**: Use `SCROLL_GRID_RIGHT:0.3` (fractional) — but beware `drag_to()` generates click events that D365 interprets as actions.

### Recorder Limitations — What Cannot Be Captured

| Limitation | Impact | Workaround |
|-----------|--------|------------|
| Drag and drop | Can't record grid reordering | Manual workflow step creation |
| File uploads | Browser security blocks file paths | Manual step with `goto_url` |
| Scroll events | Scroll position not captured | Add explicit scroll steps post-conversion |
| Right-click menus | Captured as click (lose context) | Set `right_click` action type manually |
| D365 keyboard shortcuts (Ctrl+S) | Only Tab/Enter/Escape captured | Add `press_key` steps manually |
| Timing-dependent actions | Pauses between actions lost | Set `wait_after` manually post-conversion |
| Autocomplete selections | Only final value captured | Works — fill + Tab triggers selection |
| Double-click navigation | Two clicks captured separately | Converter should merge (currently doesn't) |

### Converter Limitations — What Needs Manual Fix After Quick-Convert

| Issue | How to Detect | Manual Fix |
|-------|---------------|------------|
| No loop detection | Same 5 steps repeated N times | Set `repeat_group` on steps, add `BOM_LINES` to data |
| No conditional detection | Steps for ARAMCO mixed with LSTK | Set `condition_value` per step |
| Generic aria-label as primary | Converter warns in output | Promote `@name` strategy to P0 |
| Fill without value template | Converter warns "no mapping" | Set `value_template` to `{{FIELD}}` |
| Navigate events as waits | Steps with `navigate` action | Review if actual navigation needed |
| D365 combobox Enter→Tab | All combobox fills use Enter | Change `press_key_after` to Tab |
| Missing wait_after | Fast steps fail on slow network | Increase `wait_after` (1500-3000ms) |

### Unused/Dead Code in the App

| Item | Status | Notes |
|------|--------|-------|
| `FieldMapping` model | Unused | Templates handle mapping; could remove |
| `Workflow.valid_sheets` | Unused | Sheets not validated |
| `Workflow.required_fields` | Unused | No pre-execution validation |
| `Locator.screenshot` | Unused | ImageField never populated |
| `StepExecution.screenshot` | Unused | Captured but not shown in UI |
| `RecordedAction.element_rect` | Captured | Not used in conversion or execution |
| `LocatorStrategy.offset_direction` | Defined | For TEXT_NEARBY strategy (not implemented) |
| `LocatorStrategy.success_count/failure_count` | Tracked | But NOT used for strategy reordering |

### Key Improvements Needed

#### CRITICAL — Production-Grade Headless Execution (Required for Server Deployment)
These 5 enhancements are required before deploying to a hosted Linux server where Playwright runs headless (no visible browser). They ensure errors are diagnosable without a GUI.

1. **Screenshot on error**: When a step fails, automatically capture a full-page screenshot and save it to disk (and link it to the `StepExecution` record). Viewable from the job data detail page and execution history. This is the primary debugging tool in headless mode — replaces "looking at the browser."
2. **Pre-execution validation**: Before opening the browser, validate the entire workflow/chain: all steps have locators, all `{{TEMPLATE}}` variables exist in `row_data`, all required fields are present on the `ERPJobData` record. Fail fast with a clear error report instead of discovering missing data mid-run.
3. **Auto-retry with backoff**: When a step fails (locator not found, click didn't register), automatically retry 2-3 times with increasing wait intervals (1s, 3s, 5s) before giving up. Many D365 failures are transient (slow rendering, network lag). Currently only the debug mode has manual retry.
4. **Execution report**: After a chain completes (or fails), generate a structured summary viewable in the browser: total duration, per-step timing, pass/fail status per step, error messages, and screenshots for failed steps. Replaces the live debug panel for production runs.
5. **Video recording option**: Toggle on `WorkflowExecution` or `ChainExecution` to record the full Playwright session as MP4 video. Playwright supports this natively via `browser.new_context(record_video_dir=...)`. Stored on disk, linked from execution detail page. Essential for diagnosing complex multi-step failures.

#### HIGH Priority
6. **Smart waits based on recording timing**: Capture time deltas between user actions during recording; use actual pauses as `wait_after` values instead of generic 500ms
7. **Loop detection in converter**: Detect repeated step patterns and auto-create `repeat_group` (currently manual)
8. **Network-aware waits**: After click/fill, wait for D365 AJAX to complete (`networkidle`) instead of fixed timer

#### MEDIUM Priority
9. **Strategy success-based reordering**: Use `success_count`/`failure_count` to reorder strategies (already tracked, just not applied)
10. **Dry-run mode**: Find elements without clicking (validate workflow before live run)
11. **Conditional branching in converter**: Detect if-else patterns from recordings (currently all steps are linear)
12. **Error recovery chains**: On step failure, try alternative locator before failing

#### LOW Priority
13. **Scroll event capture in recorder**: Record scroll positions for explicit scroll steps
14. **Keyboard shortcut capture**: Record Ctrl+S, Alt+F4, etc. (currently only Tab/Enter/Escape)
15. **RC (Roller Cone) route selection**: Only FC routes fully implemented
16. **Screenshot comparison for visual regression**: Compare page screenshots to baselines

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

### Development Server Management (CRITICAL)
**The #1 cause of "old code showing" or "404 on data that exists" is zombie Python processes.** When Django's dev server is restarted without killing the previous process, the old server still holds port 8001 and serves stale code.

**Before starting the server, ALWAYS:**
```bash
# 1. Kill ALL Python processes first (Windows)
taskkill //F //IM python.exe

# 2. Verify no python is running
tasklist | grep -i python
# Should output nothing

# 3. Start fresh server from D3
cd "D:\PycharmProjects\floor_management_system-D3"
venv/Scripts/python.exe manage.py runserver 0.0.0.0:8001
```

**Never start a new server without killing the old one first.** Django's auto-reloader spawns child processes that survive the parent being killed.

**Git Worktree vs D3 Directory:**
- **D3** (`D:\PycharmProjects\floor_management_system-D3\`) — The actual project. Server runs from here. Database (`db.sqlite3`) lives here.
- **Worktree** (`C:\Users\HP-i7\.claude-worktrees\floor_management_system-D2\hardcore-hamilton\`) — Claude's editing workspace (a git worktree). Has its own separate `db.sqlite3` (usually empty/outdated). Code changes here are committed to git.
- **After editing in worktree, always sync to D3** so the running server picks up changes.
- **After editing in D3 directly, sync back to worktree** so git tracks the changes.

**Migration Warnings:**
If the server shows "X unapplied migrations", run:
```bash
cd "D:\PycharmProjects\floor_management_system-D3"
venv/Scripts/python.exe manage.py migrate
```
Then restart the server (kill + start fresh).

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
| ERP recording page | `apps/erp_automation/templates/erp_automation/recording.html` |
| ERP recording detail | `apps/erp_automation/templates/erp_automation/recording_detail.html` |
| ERP job data detail | `apps/erp_automation/templates/erp_automation/job_data_detail.html` |
| ERP job data upload | `apps/erp_automation/templates/erp_automation/job_data_upload.html` |
| ERP dashboard | `apps/erp_automation/templates/erp_automation/dashboard.html` |
| ERP workflow detail (editor) | `apps/erp_automation/templates/erp_automation/workflow_detail.html` |
| ERP workflow list | `apps/erp_automation/templates/erp_automation/workflow_list.html` |
| ERP routes list | `apps/erp_automation/templates/erp_automation/route_list.html` |
| ERP automation URLs | `apps/erp_automation/urls.py` |
| ERP chain detail (editor+debug) | `apps/erp_automation/templates/erp_automation/chain_detail.html` |
| ERP chain list | `apps/erp_automation/templates/erp_automation/chain_list.html` |
| Chain executor service | `apps/erp_automation/services/chain_executor.py` |
| Seed ERP chain command | `apps/erp_automation/management/commands/seed_erp_chain.py` |
| Seed ERP environments | `apps/erp_automation/management/commands/seed_erp_environments.py` |

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

## Todo-Enhancement

Items noted for future enhancement. These are not bugs — they are improvements to revisit later.

1. **Stock Issue / Transfer / Adjustment Create Forms**: The create forms for stock documents (`/inventory/issues/create/`, `/inventory/transfers/create/`, `/inventory/adjustments/create/`) are overly complicated and require too many fields (default_location, owner_party, ownership_type, etc.) to create a simple document. Needs UX simplification — auto-populate defaults, reduce required fields, add smart defaults based on item/variant selection.

2. **Audit All Parallel/Duplicate Models**: The system has multiple cases where a model was created and then a parallel one was added doing mostly the same work. Known cases:
   - **Stock tracking**: `VariantStock` vs `InventoryStock` vs `StockBalance` — three models caching stock data from the ledger. Plan: phase out `InventoryStock` (legacy, reads from deprecated `InventoryTransaction`), keep `VariantStock` (cutter dashboards) and `StockBalance` (multi-dimensional).
   - **BOM system**: `apps/inventory/models.py` has `BillOfMaterial`/`BOMLine` AND `apps/technology/models.py` has `BOM`/`BOMLine`. Only the technology version is used. Inventory version is dead code.
   - **Transaction ledger**: Old `InventoryTransaction` ledger vs new `StockLedger`. GRN writes to both. Should consolidate to `StockLedger` only.
   - **Need to scan entire codebase for more cases.**

3. **Phase Out InventoryStock (Legacy Stock Model)**: `InventoryStock` reads from the old `InventoryTransaction` ledger (deprecated). `VariantStock` and `StockBalance` both read from `StockLedger` (the correct system). All views that currently read from `InventoryStock` should be migrated to use `VariantStock` or `StockBalance` queries.

4. **ERP Baseline + Local Tracking Strategy**: The system is NOT the authority for receiving (GRN) — the ERP (D365) is. But the system IS the authority for consumption (issues via work orders). To keep inventory accurate despite this dual-system reality:
   - **Periodic ERP On-Hand Import**: Enhance `import_stock_from_onhand` command to create `StockLedger` entries with `transaction_type='ERP_SYNC'` representing the difference between system balance and ERP balance. This captures all missed GRNs as a single reconciliation adjustment. Store import date for "accurate as of" tracking.
   - **Track Issues Precisely via Work Orders**: Already accurate — every WO tracks what's issued. Fix #2 ensures Issue/Transfer/Adjustment update ALL stock tables.
   - **Stock Formula**: `Accurate Stock = Last ERP Sync Balance - Issues Since Last Sync + Manual GRNs Since Last Sync`
   - **Reconciliation Dashboard**: Show last sync date, days since sync, items with largest discrepancies, items with negative stock (= missed GRN). One-click "Import from ERP" button.
   - **Priority**: Build this AFTER fixing the stock posting (Fix #2) so the issue tracking is solid first.

---

## Master Plan — System Audit & Improvement Roadmap

### Phase 1: Critical Bug Fixes ✅ COMPLETED
| # | Fix | Status | Commit |
|---|-----|--------|--------|
| 1 | WorkOrderCreateEnhancedForm KeyError (`customer`/`from_location_text` not in Meta.fields) | ✅ Done | `9a3d0db` |
| 2 | Stock Divergence — Issue/Transfer/Adjustment posting now updates StockBalance + InventoryStock | ✅ Done | `a121c6f` |
| 3 | SyncStockFromBalancesView — Lot→MaterialLot + balance_list→stock_balance_list | ✅ Done | `62db65b` |
| 4 | Status Transition Validation — clean() + STATUS_TRANSITIONS on 7 models | ✅ Done | `73c8585` |
| 5 | HDBS case mismatch — case-insensitive sync command + data fix | ✅ Done | — |

### Phase 2: ERP Data Reconciliation (DELAYED — waiting for user's D365 export files)
**Context**: IT department refused to stop D365. System coexists with ERP. Issues tracked accurately via WOs, but GRNs may be missed (done in ERP only).

**D365 Export Files Needed** (user will provide):
1. **Inventory Transactions** (`Inventory Management → Inquiries → Transactions`) — ALL posted transactions (movements, receipts, issues). Right-click → Export all rows. Contains: item number, qty, warehouse, serial, date, journal reference.
2. **On-Hand Inventory** (`Inventory Management → Inquiries → On-hand list`) — Current stock snapshot for reconciliation baseline.
3. **Movement Journal Lines** — Via Inventory Transactions filtered by Reference = "Inventory journal"

**Build Plan** (after receiving files):
1. Study exported Excel column structure
2. Build `import_erp_transactions` management command — parses D365 Inventory Transactions Excel, creates StockLedger entries with `transaction_type='ERP_SYNC'`
3. Build `import_erp_onhand` management command — reconciles system balance vs D365 on-hand, creates adjustment entries for discrepancies
4. Build **Reconciliation Dashboard** page — last sync date, discrepancies, negative stock alerts, one-click import button
5. Stock Formula: `Accurate Stock = Last ERP Sync Balance - Issues Since Last Sync + Manual GRNs Since Sync`

### Phase 3: Parallel Model Cleanup
**Goal**: Remove duplicate/parallel models that cause data divergence.

| Duplicate Pair | Keep | Remove | Status |
|----------------|------|--------|--------|
| `VariantStock` vs `InventoryStock` vs `StockBalance` | `VariantStock` + `StockBalance` | `InventoryStock` (legacy) | Pending |
| `InventoryTransaction` vs `StockLedger` | `StockLedger` | `InventoryTransaction` | Pending |
| `inventory.BillOfMaterial/BOMLine` vs `technology.BOM/BOMLine` | `technology.BOM` | `inventory.BillOfMaterial` (dead code) | Pending |
| Other duplicates | TBD — full codebase scan needed | TBD | Pending |

**Approach for each removal**:
1. Find ALL references to the deprecated model (views, templates, management commands, APIs)
2. Migrate each reference to use the replacement model
3. Verify no data loss — run side-by-side comparison queries
4. Remove the deprecated model + migration to drop table
5. Clean up imports

### Phase 4: Remaining Audit Fixes
| # | Category | Issues | Status |
|---|----------|--------|--------|
| 4 | Architectural | Status state machines (7 models) | ✅ Done |
| 5 | Architectural | HDBS case mismatch fix | ✅ Done |
| 6-8 | Architectural | N+1 query, RBAC placeholders, god function refactoring | Pending |
| 9-15 | Missing Features | Validation gaps, missing error handling, incomplete workflows | Pending |
| 16-22 | Dead Code | Unused models, orphaned views, legacy imports | Pending |
| 23-27 | Inconsistencies | Naming conventions, field type mismatches, URL pattern inconsistencies | Pending |

### Workflow for Each Fix
1. Restudy the code (fresh context each session)
2. Run server → give user link to see the bug
3. User confirms the bug
4. Implement fix
5. User verifies fix works
6. Update CLAUDE.md with documentation
7. Sync worktree ↔ D3
8. Commit + push to GitHub

---

## Need Help?

1. **Check this file first** for patterns and conventions
2. **Run `./hc`** to ensure database is healthy
3. **Backup with `./hv`** before making changes
4. **Check Django admin** at `/admin/` for data inspection
5. **Review browser console** for JavaScript errors
