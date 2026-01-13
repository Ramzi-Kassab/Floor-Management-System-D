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

## Key Files
- `apps/technology/` - Design, BOM, HDBS, SMI models
- `apps/cutter_map/` - PDF extraction and cutter mapping
- `apps/cutter_map/views.py:api_sync_to_erp` - Creates BOM from extracted PDF data
- `templates/technology/bom_create_builder.html` - Design selection page
- `templates/cutter_map/index.html` - Cutter map interface

## Database
- SQLite at `db.sqlite3` (NOT tracked in git)
- Run `./hv` to backup database before risky operations
- Run `./hv restore` to recover from backup
- Backups stored in `backups/` directory

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
├── mat_code (e.g., "1283567M1")
├── order_level ("3" or "4")
├── size (FK to BitSize)
├── hdbs_type (FK to HDBSType)
├── pocket_configs (DesignPocketConfig - grouped cutter specs)
└── pockets (DesignPocket - individual pocket positions)

BOM (L5)
├── mat_code (e.g., "1283567M1-001")
├── parent_design (FK to Design)
├── smi_type (FK to SMIType)
└── items (BOMItem - cutter quantities)
```

## Recent Changes (Jan 2026)
- Simplified BOM create page to Design-first workflow
- Added Cutter Map integration for PDF extraction
- Fixed DesignPocketConfig deletion order (pockets before pocket_configs)
- Added `./hv` backup script to prevent data loss

## Known Issues / TODOs
- SMI Types not seeding (missing bit sizes during seed)
- PDF extraction works for Halliburton format only

## Login Credentials (Test)
- Password for all users: `Ardt@2025`
- Sample: `r.kassab`, `g.escobar`, `m.irshad`
