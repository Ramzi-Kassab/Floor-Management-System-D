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

## Recent Changes (Jan 15, 2026)

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
- **Auto-fill on Item Creation**: When creating new items, defaults from category are applied
- **Category Form Update**: New "Item Defaults" section to configure defaults
- **API Enhancement**: `CategoryAttributesAPIView` now returns `defaults` object

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
- 20 inventory items
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
