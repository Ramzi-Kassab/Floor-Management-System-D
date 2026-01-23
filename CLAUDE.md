# ARDT Floor Management System - Project Context

## Overview
Floor Management System for ARDT (drill bit manufacturing). Django 5.1 + SQLite + HTMX/Alpine.js.

## Key Business Concepts
- **BOM Hierarchy**: L3/L4 (design without cutters) → L5 (design with cutters/MAT code)
- **Design**: A drill bit design identified by MAT code (e.g., 1283567M1)
- **HDBS**: Halliburton Drill Bit System - classification system for designs
- **SMI**: Standard Material Identifier - specific configuration within HDBS
- **Cutter Map**: Visual tool to map PDC cutters on a drill bit from PDF extraction

## Current Workflow (BOM Creation)
1. User goes to `/technology/boms/create/`
2. Selects a Design (L3/L4) from table
3. Clicks "Open Cutter Map" → redirects to `/cutter-map/` with design context
4. Uploads Halliburton PDF → extracts blade/cutter data
5. Clicks "Create BOM" → calls `api_sync_to_erp` to create L5 BOM
6. If unmatched cutters found → redirects to Cutter Wizard (`/cutter-map/add-cutter-wizard/`)

## Key Files
- `apps/technology/` - Design, BOM, HDBS, SMI models
- `apps/cutter_map/` - PDF extraction and cutter mapping
- `apps/cutter_map/views.py:api_sync_to_erp` - Creates BOM from extracted PDF data
- `apps/cutter_map/views.py:add_cutter_wizard` - Step-by-step wizard for adding cutters to inventory
- `apps/inventory/views.py` - Inventory item management with cutter wizard integration
- `templates/technology/bom_create_builder.html` - Design selection page
- `templates/cutter_map/index.html` - Cutter map interface
- `templates/cutter_map/add_cutter_wizard.html` - Cutter wizard UI

## Database
- SQLite at `db.sqlite3` (NOT tracked in git)
- Run `./hv` to backup database before risky operations
- Run `./hv restore` to recover from backup
- Backups stored in `backups/` directory
- Technology data exports in `data/technology_data_*.json`

## Common Commands
```bash
./hc              # Health check - runs migrations, seeds, checks git
./hv              # Create database backup
./hv restore      # Restore from backup
./hv list         # List available backups
python manage.py runserver 0.0.0.0:8000
python manage.py seed_all
python manage.py seed_test_designs
```

## Models Structure
```
Design (L3/L4)
├── mat_no (e.g., "1283567M1")
├── order_level ("3" or "4")
├── size (FK to BitSize)
├── hdbs_type (FK to HDBSType)
├── pocket_configs (DesignPocketConfig - grouped cutter specs)
└── pockets (DesignPocket - individual pocket positions)

BOM (L5)
├── mat_no (e.g., "1283567M1-001")
├── design (FK to Design)
├── smi_type (FK to SMIType)
└── items (BOMItem - cutter quantities linked to InventoryItem)

InventoryItem
├── code (e.g., HDBS code like "CT179")
├── category (FK to InventoryCategory, e.g., "PDC Cutters")
├── is_blocked (prevents deletion if True)
├── blocked_reason (why blocked)
└── attribute_values (ItemAttributeValue - cutter specs)
```

## Recent Changes (Jan 23, 2026)

### Multiple Serial Number Selection for BOM
- **Multi-select SNs**: When creating a BOM, user can select multiple drill bits (serial numbers) to link
- **Checkbox UI**: Added checkboxes for each available drill bit with "Select All" option
- **Bulk linking**: BOM created once, linked to all selected serial numbers
- **Post-creation linking**: "Link to More Serial Numbers" button on success dialog allows adding more SNs later
- **New endpoint**: `api_link_bom_to_drillbits` for linking existing BOM to additional drill bits

### Drill Bit Edit Form Improvements
- **Identity-only editing**: Only `serial_number`, `design`, `brazing_bom`, `system_bom` fields editable
- **BOM dropdowns**: Brazing BOM and System BOM shown as dropdowns filtered by selected design
- **Design change handling**: Changing design clears BOM selections and reloads available BOMs
- **New form**: `DrillBitUpdateForm` in `apps/workorders/forms.py`

### Drill Bits List Page Enhancements
- **Freeze mode**: Toggle to freeze first columns while scrolling horizontally
- **Full page mode**: Toggle to expand table to full viewport
- **Styling**: Matches Cutter Inventory page layout

### Existing BOM Detection on BOM Create
- **Dialog on existing BOMs**: When selecting a design that already has BOMs, shows dialog with options
- **View existing BOM**: Click any existing BOM to open it in Cutter Map (edit mode)
- **Create new BOM**: Option to proceed with uploading a new PDF file
- **BOM type labels**: Shows Brazing/System type labels in the existing BOMs list

### Bug Fixes
- **URL path fix**: Changed `/workorders/api/drill-bits/search/` to `/work-orders/api/drill-bits/search/` (matching URL conf)

## Recent Changes (Jan 21, 2026)

### Blade Location Zones Update
- **Removed TAPER zone**: Not used in frontend, removed from backend
- **Added PAD zone**: New zone with purple color (#a855f7), code 'P'
- **Correct order**: CONE → NOSE → SHOULDER → GAGE → PAD (C, N, S, G, P)
- **DesignPocket.BladeLocation** updated to match frontend positions
- **Zone row in Pockets Layout**: Changed from mirroring B1 data to static legend showing all zones

### BOM Detail Page Redesign
- **Removed old Builder**: `/technology/boms/<pk>/builder/` link removed (obsolete)
- **New View/Edit Layout buttons**: Opens PDF Generator with BOM data pre-loaded
  - View Layout: `/cutter-map/bom/<bom_id>/` - view-only mode
  - Edit Layout: `/cutter-map/bom/<bom_id>/?edit=1` - full editing enabled
- **source_data JSONField** added to BOM model to store complete PDF data
- **api_sync_to_erp** now saves header, summary, and blades to `bom.source_data`

### Data Flow for BOM ↔ PDF Generator
```
PDF Upload → Extract → Edit → Create BOM → source_data saved
                                    ↓
BOM Detail → View/Edit Layout → PDF Generator (pre-populated)
```

**What's saved in BOM.source_data:**
- `header`: mat_number, sn_number, date_created, revision_level, software_version
- `summary`: array of cutter specs (index, type, chamfer, mat_number, size, count, fill_color)
- `blades`: complete blade layout with r1-r4 rows and positions

### Bug Fixes (Cutter Map)
- **Fixed blade number extraction**: Was using `blade.get('blade_id')` which doesn't exist; now parses from `blade.name` (e.g., "B1" → 1)
- **Fixed blade location extraction**: Was using `cell.get('pos')` which doesn't exist; now uses `pos_key` (dictionary key like 'CONE', 'NOSE')
- **Result**: All 6 blades now populate correctly in Pockets Grid and Location Assignment Grid

### New Files
- `apps/cutter_map/views.py:bom_view` - View BOM in PDF Generator
- `templates/cutter_map/bom_no_data.html` - Message when BOM has no source_data
- `apps/technology/migrations/0023-0025` - PAD zone and source_data migrations

### Old BOM Builder Removed
The manual BOM Builder (`/technology/boms/<pk>/builder/`) has been removed and fully replaced by the Cutter Map PDF Generator:
- **Removed URLs**: `bom_builder`, `bom_builder_add_line`, `bom_builder_update_line`, `bom_builder_delete_line`, `bom_builder_reorder`, `bom_builder_search_items`
- **Removed Views**: `BOMBuilderView`, `BOMBuilderAddLineView`, `BOMBuilderUpdateLineView`, `BOMBuilderDeleteLineView`, `BOMBuilderReorderView`, `BOMBuilderSearchItemsView`
- **Removed Template**: `templates/technology/bom_builder.html`
- **Updated Redirects**: BOM clone and PDF import now redirect to `cutter_map:bom_view` or `technology:bom_detail`
- **Replacement**: Use `/cutter-map/bom/<bom_id>/` for viewing/editing BOM layout

### Drill Bit Registration Simplified (Identity vs State)
Registration now captures **identity only** - dynamic state is tracked via events.

**Identity (fixed at registration):**
- Serial Number (6-8 digits from Halliburton USA)
- Design (L3/L4 - determines bit type and size)
- BOM (L5 - optional)

**State (dynamic, tracked via BitEvent):**
- Location (changes with TRANSFER, DEPLOY, RECEIVE events)
- Customer (assigned via intake or deployment)
- Status (lifecycle_status, physical_status, accounting_status)

**Business Model:**
- ARDT-owned bits: For sale or rental service (Sperry, etc.)
- Customer-owned bits: Halliburton/Aramco bits brought in for service
- Serial numbers arrive in batches (2-3 at a time) after ordering

### First Event Wizard (After Registration)
After registering a drill bit (identity only), user is redirected to `/workorders/drill-bits/<pk>/first-event/`:

**Event Options:**
1. 📦 **Received at ARDT** - New bit physically arrived at warehouse
2. 🔧 **Customer Intake** - Customer brought bit for repair/service
3. 🏭 **In Production (USA)** - Bit still being manufactured
4. ⏭️ **Skip for Now** - Just register identity, add events later

**New View**: `DrillBitFirstEventView` at `apps/workorders/views_drillbit.py`
**New Template**: `templates/workorders/drillbit_first_event.html`
**Updated Form**: `DrillBitCreateForm` now only has `serial_number`, `design`, `bom` fields

## Previous Changes (Jan 18, 2026)

### Job Card / Work Order System Enhancement
A comprehensive Job Card system has been implemented to digitize the paper-based job card workflow for drill bit manufacturing and repair.

#### New Models (apps/workorders/models.py)
- **CutterEvaluationMatrix**: Blade × Cutter position grid for tracking cutter actions
  - Evaluation types: ARDT, ENGINEER, REWORK
  - Supports 3 parallel evaluations per work order
- **CutterEvaluationEntry**: Individual blade/position entries with actions (O=OK, X=Replace, R=Rotate, S=Spin, D=Damaged, M=Missing)
- **InstructionRule**: Rule-based instructions system with conditions
  - Filter by WO type and Bit type
  - Priority-based ordering
  - Condition evaluation against work order fields
- **InstructionRuleCondition**: Field-based conditions (equals, contains, greater_than, etc.)
- **RouterSheetEntry**: Process steps with QR scan tracking for start/end times
- **EvaluationChecklist**: 15-point E-Checklist for FC bit evaluation
- **LPTReport**: Liquid Penetrant Test documentation
- **APIThreadInspection**: API pin/thread inspection form

#### WorkOrder Model Updates
New Job Card specific fields:
- `brazing_mat_no`: Free text L5 MAT# for brazing operations
- `system_mat_no`: Fixed L5 MAT# shared with client/sales
- `drss_no`, `reference_po_no`, `contract_no`: Reference numbers
- `from_location_text`, `bit_received_date`: Incoming bit info
- `evaluated_by`, `evaluated_at`, `qc_by`, `qc_at`, `reviewed_by_eng`, `eng_review_at`: Signature tracking

#### New Views (apps/workorders/views_jobcard.py)
- **WorkOrderDashboardView**: Summary cards, quick actions, recent work orders at `/workorders/dashboard/`
- **WorkOrderListEnhancedView**: Excel-like filtering with column filters at `/workorders/enhanced/`
- **WorkOrderDetailEnhancedView**: Job Card detail with tabs (Overview, Cutter Evaluation, Router Sheet, QC Forms, Instructions, History)
- **DrillBitListEnhancedView**: Enhanced drill bit list with lifecycle tracking at `/workorders/drill-bits/enhanced/`
- **DrillBitDetailEnhancedView**: Full bit history with events and repairs
- **CutterEvaluationCreateView/EditView**: Interactive matrix editor for blade/cutter evaluations
- **RouterSheetView**: Step-by-step tracking with QR scanning support
- **EvaluationChecklistView**: E-Checklist form (15 checkpoints)
- **LPTReportCreateView**: LPT test documentation form
- **APIThreadInspectionCreateView**: API thread inspection form
- **InstructionRuleListView/Create/Update/Delete**: Manage conditional instructions
- **export_work_orders_excel**: Excel export with openpyxl

#### New Templates
- `templates/workorders/dashboard.html` - Main dashboard
- `templates/workorders/workorder_list_enhanced.html` - Enhanced list with column filters
- `templates/workorders/workorder_detail_enhanced.html` - Job Card with tabs
- `templates/workorders/drillbit_list_enhanced.html` - Drill bit list
- `templates/workorders/drillbit_detail_enhanced.html` - Drill bit detail
- `templates/workorders/cutter_evaluation_form.html` - Create evaluation
- `templates/workorders/cutter_evaluation_matrix.html` - Interactive grid editor
- `templates/workorders/router_sheet.html` - Router sheet with QR support
- `templates/workorders/e_checklist_form.html` - E-Checklist (15 items)
- `templates/workorders/lpt_report_form.html` - LPT test form
- `templates/workorders/api_thread_form.html` - API thread inspection
- `templates/workorders/instruction_rule_list.html` - Rules list
- `templates/workorders/instruction_rule_form.html` - Rule create/edit
- `templates/workorders/instruction_rule_confirm_delete.html` - Delete confirmation

#### Sidebar Updates
Under Production section:
- Dashboard (highlighted) - `/workorders/dashboard/`
- Job Cards - `/workorders/enhanced/`
- Work Orders - `/workorders/` (original list)
- Drill Bits - `/workorders/drill-bits/enhanced/`
- Job Card Tools sub-section:
  - Instructions - `/workorders/instruction-rules/`
  - Process Routes
  - WO Costs

#### Key Features
1. **Cutter Evaluation Matrix**: Click-to-edit grid for blade × cutter positions
2. **Router Sheet QR Tracking**: Start/end time tracking per step with QR scan support
3. **Instruction Rules Engine**: Conditional instructions based on WO type, bit type, and custom conditions
4. **QC Forms**: E-Checklist, LPT Reports, API Thread Inspections
5. **Modern UI**: Responsive design, dark mode support, Excel-like column filters
6. **Excel Export**: Professional formatting with frozen headers

### Drill Bit Inventory System (Jan 19, 2026)
Comprehensive drill bit inventory management with lifecycle tracking, events, and location management.

#### Existing Models Used
- **DrillBit**: Full model with serial numbers (6-8 digits), status tracking, location, customer, costs, repair history
  - Serial numbers: 8 digits for PDC Fixed Cutter, 6-8 for Tri-cone
  - Multiple status fields: `lifecycle_status`, `physical_status`, `accounting_status`
  - Cost tracking: `original_cost`, `total_repair_cost`, `current_book_value`
  - Repair counters: `repair_count`, `deployment_count`, `backload_count`
- **BitEvent**: Lifecycle event tracking with 20+ event types (RECEIVED, DEPLOYED, BACKLOADED, REPAIR_START, etc.)
- **Location**: Predefined locations (WAREHOUSE, REPAIR_SHOP, QC, RIG, EVALUATION, SCRAP, etc.)
- **sales.Customer**: Customer master for ownership tracking

#### New Views (apps/workorders/views_drillbit.py)
- **DrillBitInventoryDashboardView**: Summary cards (total bits, by type, available, in repair) at `/workorders/drill-bits/inventory/`
  - Aggregations by status, lifecycle, customer, location, size
  - Cost summaries (original, repair, book value)
  - Recent events feed
- **DrillBitCreateView**: Register new bit with existing serial at `/workorders/drill-bits/new/`
- **DrillBitUpdateView**: Edit bit details at `/workorders/drill-bits/<pk>/edit/`
- **DrillBitDeleteView**: Mark as scrapped at `/workorders/drill-bits/<pk>/delete/`
- **DrillBitReceiveView**: Record receipt at `/workorders/drill-bits/<pk>/receive/`
- **DrillBitShipView**: Record shipment to customer/rig at `/workorders/drill-bits/<pk>/ship/`
- **DrillBitTransferView**: Location transfer at `/workorders/drill-bits/<pk>/transfer/`
- **DrillBitReturnView**: Record return from field at `/workorders/drill-bits/<pk>/return/`
- **DrillBitScrapView**: Mark as scrapped with reason at `/workorders/drill-bits/<pk>/scrap/`
- **DrillBitStartRepairView**: Start repair/production at `/workorders/drill-bits/<pk>/start-repair/`
- **LocationListView/CreateView/UpdateView/DeleteView**: Manage locations at `/workorders/locations/`
- **BitEventListView**: View all events at `/workorders/bit-events/`
- **DrillBitExportExcelView**: Excel export at `/workorders/drill-bits/export/excel/`
- **DrillBitSearchAPIView**: API for autocomplete at `/workorders/api/drill-bits/search/`

#### New Templates
- `templates/workorders/drillbit_inventory_dashboard.html` - Inventory dashboard with cards and charts
- `templates/workorders/drillbit_form.html` - Create/edit drill bit form
- `templates/workorders/drillbit_confirm_delete.html` - Scrap confirmation
- `templates/workorders/drillbit_action_receive.html` - Receive action form
- `templates/workorders/drillbit_action_ship.html` - Ship action form
- `templates/workorders/drillbit_action_transfer.html` - Transfer action form
- `templates/workorders/drillbit_action_return.html` - Return action form
- `templates/workorders/drillbit_action_scrap.html` - Scrap action form
- `templates/workorders/drillbit_action_start_repair.html` - Start repair form
- `templates/workorders/location_list.html` - Locations list
- `templates/workorders/location_form.html` - Location create/edit
- `templates/workorders/location_confirm_delete.html` - Location delete confirmation
- `templates/workorders/bitevent_list.html` - Event history list

#### Sidebar Updates
Under Production > Drill Bit Inventory sub-section:
- Inventory Dashboard - `/workorders/drill-bits/inventory/`
- Register New Bit - `/workorders/drill-bits/new/`
- Locations - `/workorders/locations/`
- Bit Events - `/workorders/bit-events/`
- Export Excel - `/workorders/drill-bits/export/excel/`

#### Management Command
```bash
python manage.py seed_drillbit_inventory           # Preview mode
python manage.py seed_drillbit_inventory --confirm # Create test data
python manage.py seed_drillbit_inventory --confirm --bits 50  # Create 50 test bits
```
Creates:
- 11 predefined locations (Warehouse, Repair Shop, QC Area, Rig Sites, etc.)
- Sample drill bits with various statuses and lifecycle events

#### Key Features
1. **Serial Number Support**: 8 digits for PDC, 6-8 for Tri-cone (not auto-generated - accepts existing serials)
2. **Lifecycle Event Tracking**: Full audit trail with BitEvent model
3. **Location Management**: Predefined locations with types (WAREHOUSE, REPAIR_SHOP, RIG, etc.)
4. **Action Buttons**: Quick actions for receive, ship, transfer, return, scrap, start repair
5. **Dashboard Aggregations**: Summary by status, lifecycle, customer, location
6. **Excel Export**: Professional formatting with all drill bit data
7. **Customer Integration**: Links to existing sales.Customer model

### Production Readiness Improvements (Jan 19, 2026)

#### Forms Enhancement (apps/workorders/forms.py)
Added comprehensive form classes for all Job Card features:
- **LocationForm**: Create/edit locations with validation
- **InstructionRuleForm**: Rule management with inline condition formset
- **InstructionRuleConditionFormSet**: Inline formset for rule conditions
- **CutterEvaluationMatrixForm**: Create/edit cutter evaluations
- **RouterSheetEntryForm**: Process step tracking
- **EvaluationChecklistForm**: E-Checklist with 15 checkpoints
- **LPTReportForm**: Liquid Penetrant Test documentation
- **APIThreadInspectionForm**: API thread inspection
- **DrillBitReceiveForm/ShipForm/TransferForm/ReturnForm/ScrapForm/StartRepairForm**: Action forms with validation

#### Status Transition Logging (apps/workorders/utils.py)
- **log_status_transition()**: Records status changes with GenericForeignKey support
- **get_status_history()**: Retrieve status history for any model instance
- **can_workorder_transition()**: Validate work order status transitions
- **can_drillbit_lifecycle_transition()**: Validate drill bit lifecycle transitions
- Predefined transition rules for work orders and drill bits

#### Admin Registration (apps/workorders/admin.py)
Comprehensive admin for all 30+ models:
- Location, BitEvent, DrillBit with full fieldsets
- WorkOrder with inlines (Materials, Documents, Photos, TimeLogs)
- StatusTransitionLog, BitRepairHistory, SalvageItem
- RepairApprovalAuthority, RepairEvaluation
- RepairBOM with RepairBOMLine inline
- ProcessRoute with ProcessRouteOperation inline
- WorkOrderCost
- CutterEvaluationMatrix with CutterEvaluationEntry inline
- RouterSheetEntry, EvaluationChecklist, LPTReport, APIThreadInspection
- InstructionRule with InstructionRuleCondition inline

#### Template Improvements
- **cutter_evaluation_matrix.html**: Fixed CSRF token for AJAX operations
- **instruction_rule_form.html**: Added inline formset UI for conditions with JavaScript add/delete functionality
- Error handling and validation feedback in drill bit action views

#### Error Handling
- Location validation in drill bit action views (receive, transfer)
- Same-location transfer prevention
- Exception handling with user-friendly error messages

## Previous Changes (Jan 17, 2026)

### Cutter Inventory Column Updates
- **Renamed Column**: "Client Stk" → "LSTK Rcl" (specifically for Client Reclaim with Halliburton + LSTK account)
- **Column Reorder**: Retrofit moved from Stock Variants (green) to Stock Totals (blue) section
- **New Column Order**: ENO New, ENO Grd, ARDT Rcl, LSTK Rcl | Retrofit, New Stock, Total New
- **Updated Export**: CSV export matches new column structure

### Cross-Table Item Number Uniqueness
- **InventoryItem.code** and **ItemVariant.code** now validated for global uniqueness
- **ItemVariant.erp_item_no** validated for uniqueness across all variants
- Validation runs in both `clean()` method (forms) and `save()` method (direct calls)
- Prevents creating an item with a code that exists as a variant code, and vice versa
- Prevents duplicate ERP Item Numbers across variants
- Prepares system for importing real cutter data with unique ERP item numbers

### QR Code Print Labels for Variants
- **New View**: `VariantPrintLabelView` at `/inventory/items/{item_pk}/variants/{pk}/print-label/`
- **Multiple Copies**: Supports 1-50 copies per print job
- **Label Sizes**: Small (1.5"×1"), Medium (2"×1"), Large (3"×1.5")
- **Variant Detail Page**: Split into "Quick Print" (window.print) and "Print Labels" (dedicated view)
- **Print CSS**: Added print-specific styles to variant detail page

### Management Commands for Cutter Data
- **clear_test_cutters**: Remove test PDC cutter data (items, variants, attributes, stock)
  ```bash
  python manage.py clear_test_cutters           # Preview mode
  python manage.py clear_test_cutters --confirm # Actually delete
  python manage.py clear_test_cutters --keep-count 5 --confirm
  ```
- **import_cutters_excel**: Import real cutter data from Excel
  ```bash
  python manage.py import_cutters_excel           # Preview mode
  python manage.py import_cutters_excel --confirm # Actually import
  python manage.py import_cutters_excel --skip-existing --confirm
  ```
  - Reads from `docs/Cutters ERP Item Numbers2.xlsx`
  - Creates base items with attributes (Type, Size, Chamfer, Family, Shape)
  - Creates variants with unique ERP item numbers per variant case

### GRN Delete Functionality
- **New View**: `GRNDeleteView` at `/inventory/grn/<pk>/delete/`
- **Restriction**: Only DRAFT status GRNs can be deleted
- **UI**: Delete button appears on GRN detail page for DRAFT GRNs
- **Cascade**: Automatically deletes associated GRN lines

### Bug Fixes
- **ItemListView Category Filter**: Now handles both numeric IDs and category codes (e.g., `?category=CUT-PDC`)
- **ERP Item No Validation Display**: Added error message display to variant edit form template
- **Management Commands Model Imports**: Fixed `ItemStock` → `InventoryStock`, `Attribute` → `CategoryAttribute`

### PDC Cutter Import - Corrected Attribute Mappings (Jan 18, 2026)
- **Fixed import_cutters_excel** command with correct attribute mappings:
  - `item_number` attribute ← "New Stock" column (ERP Item No, e.g., CT-0062)
  - `hdbs_code` attribute ← "MN" column (HDBS MAT number, e.g., 802065)
  - `cutter_type` attribute ← "Cutter Type" column (e.g., CT97, OBS ERC)
  - `diameter` attribute ← First 2 digits of Size (e.g., 13 from 1313)
  - `length` attribute ← Last 2 digits of Size (e.g., 13 from 1313, or N/A if only 2 digits)
  - `cutter_size`, `chamfer`, `family`, `cutter_shape` ← direct column mapping
- **LSTK Variant Support**: NEW-CLI variants get `account="LSTK"` and `customer=Halliburton`
- **18 PDC Cutter Attributes** now linked to CUT-PDC category
- Successfully imported **301 PDC cutter items** with **848 variants** from Excel

### Cutter Inventory Dashboard Enhancements (Jan 18, 2026)
- **Pagination**: Always visible with page size selector (50, 100, 200, 500, All)
  - "All" option loads all records for column filters to work on complete dataset
  - Shows note when paginated: "Column filters only work on visible rows"
  - Shows green checkmark when "All" selected: "✓ Column filters work on all data"
- **Export to Excel**: Changed from CSV to Excel (.xlsx) format
  - Professional formatting with header styles
  - Frozen header row and first 3 columns
  - Export includes all attributes, stock variants, consumption, safety stock
- **Button update**: "Export" → "Export Excel" with spreadsheet icon

## Previous Changes (Jan 16, 2026)

### Pricing System
- **PriceList Model**: Supports 3 types - LSTK (fixed tiers), COST_PLUS (markup %), MATRIX (size × quality)
- **PriceTier**: Size-based pricing (e.g., 8-10mm = $272, 12-13mm = $360, 16mm = $497)
- **PriceMatrixRule**: Size × Quality matrix pricing (e.g., 16mm × NEW = $500)
- **LandingCostType**: Cost types like SHIPPING, CUSTOMS, HANDLING with allocation methods
- **LandingCostRecord**: Actual costs per GRN with `allocate()` method
- **LandingCostAllocation**: Distributed costs per GRN line (per-unit amount)
- **ItemPrice**: Cached/calculated prices with landed cost component
- **New URLs**: `/inventory/pricing/`, `/inventory/pricing/landing-cost-types/`
- **Sidebar**: New "Pricing" section under Logistics with Price Lists and Landing Cost Types

### Variant Stock Dashboard
- **New View**: `VariantStockListView` at `/inventory/variant-stock/`
- **Filtering**: By category, item, variant case
- **Display**: Stock breakdown by variant (NEW, USED, etc.) with totals
- **Sidebar**: Added under Logistics > Items & Stock

### Item Detail Page Improvements
- **Fixed**: `is_bit_item`/`is_cutter_item` logic overlap - PDC Cutters no longer show Bit Specifications
- **Cleaned Up**: Bit/Cutter Specifications sections only show when data exists (not empty prompts)
- **Styling**: Improved spec cards with colored backgrounds, icons, and grouped Operating Parameters

### Cutter Inventory Management
- **Cutter Dashboard**: New view at `/inventory/cutters/` matching Excel format
  - **Attribute Columns**: Shape, Size, Type (HDBS), Chamfer, Family, Category
  - **Stock by Variant**: NEW-EO, GRD-EO, USED-RCL, CLI-RCL columns
  - **New Stock**: NEW-PUR only
  - **Total New**: NEW-PUR + NEW-EO + NEW-RET (Retrofit as New)
  - **Consumption**: 6M, 3M, 2M columns (yellow background)
  - **Safety Stock**: Calculated from 2M consumption using Excel formula:
    - Buffer: >=300 → +10, >=200 → +5, >=100 → +5, >=5 → +2, else → +1
    - Rounded up to nearest 5
  - **Forecast**: Total New + On Order - BOM Requirement
  - **Remarks**: Notes field (editable)
  - Red row highlight when forecast < safety stock
- **Cutter Orders**: New view at `/inventory/cutters/orders/` showing PO lines for PDC cutters
  - Summary cards: Total Ordered, Received, Pending
  - Filters by status and cutter item
  - Links to PO details
- **Sidebar**: New "PDC Cutters" section under Logistics with Cutter Inventory and Cutter Orders
- **Variant Case Updates**: Corrected codes for better clarity
  - NEW-ENO → NEW-EO (New E&O)
  - USED-GRD → GRD-EO (E&O Ground)
  - USED-STD → USED-RCL (Used Reclaimed)
  - CLI-USED → CLI-RCL (Client Reclaimed)
- **Model Changes**: Added `notes` field to InventoryItem for remarks column
- **Template Filter**: Added `get_item` filter for dictionary access in templates

### Bug Fixes
- **Decimal Fix**: Variant bulk create now uses `Decimal()` instead of `float` for cost calculations

## Previous Changes (Jan 15, 2026)

### Cutter Map Improvements
- **Re-index Fix**: Now fills gaps even when starting from 1 (e.g., 1,3,5 → 1,2,3)
- **Add/Replace Mode**: Buttons moved to Cutter Layout header for better proximity to CL
- **Type/Chamfer Sync**: When changing cutter group in edit modal, type/chamfer auto-sync from BOM item
- **Shape Auto-population**: Extracted PDF group_shapes automatically populate cutter_shapes on load
- **BOM Count Updates**: Correctly updates when cutter group changes during edit
- **Full Size Comparison**: Size mismatch now compares full 4-digit size codes (1313 ≠ 1308), not just diameter
- **MAT Dropdown Grouping**: Shows exact size matches first, then other same-diameter options grouped by size

### UX Improvements
- Increased text sizes: cutter type 7px (was 5px), chamfer 6px (was 4px)
- Better hover states with visual feedback on cutter actions
- Modern button styling with shadows and transitions
- Improved BOM table readability (11px font, better contrast)
- Section headers with rounded corners and better typography

### Category Defaults Feature
- **New Fields on InventoryCategory**: `default_currency`, `default_min_stock`, `default_reorder_qty`
- **Packaging Defaults**: `default_purchase_uom`, `default_release_uom`, `default_conversion_factor`
- **Auto-fill on Item Creation**: When creating new items, defaults from category are applied
- **Category Form Update**: New "Item Defaults" section with stock and packaging defaults
- **API Enhancement**: `CategoryAttributesAPIView` now returns `defaults` object including packaging

### Variant Stock Integration (Foundation)
- **StockLedger Enhancement**: Added `variant` FK to track variant-level stock movements
- **Document Lines**: Added `variant` FK to GRNLine, StockIssueLine, StockTransferLine, StockAdjustmentLine
- **VariantStock Methods**: Added `recalculate_from_ledger()` and `update_from_ledger_entry()` class method
- **Architecture**: Variants now share the immutable ledger system with base items
- **Note**: Views need to be updated to use variant FK when posting transactions

## Previous Changes (Jan 14, 2026)

### Cutter Wizard & Inventory Integration
- **Cutter Wizard** (`add_cutter_wizard`): Step-by-step UI to add unmatched PDC cutters from PDF extraction to inventory
- **Smart Parsing**: Auto-parses cutter sizes (e.g., "1613" → diameter=16mm, length=13mm, length_class=Standard)
- **Quick Add**: Users can add new attribute options on-the-fly when extracted values don't match existing dropdowns
- **Blocking Controls**: Inventory items can be marked as blocked to prevent accidental deletion

### BOM-Inventory Flow
- When BOM is created from PDF, cutters are matched to existing inventory items by HDBS code
- Unmatched cutters are tracked and user is prompted to add them via wizard
- Wizard pre-fills inventory form with parsed cutter data (size, type, chamfer, etc.)

### Design Management
- Added view/review action for designs from BOM create page
- Added delete functionality for designs (with protected FK handling)
- Pocket reset and unmatched cutters warning in BOM success dialog

## Current Data State
- 14 designs in database
- 3 BOMs created
- **301+ PDC cutter items** (imported from Excel)
- **848+ item variants** with unique ERP item numbers
- 354 attributes defined
- 42 inventory categories

## Known Issues / TODOs
- SMI Types not seeding (missing bit sizes during seed)
- PDF extraction works for Halliburton format only
- `CutterMapDocument.sync_to_design()` method has placeholder TODO (but sync is handled via `api_sync_to_erp` view)

## Dependencies Note
- `jinja2` is required but not in requirements.txt (needed for PDF generation)

## Login Credentials (Test)
- Password for all users: `Ardt@2025`
- Sample: `r.kassab`, `g.escobar`, `m.irshad`
