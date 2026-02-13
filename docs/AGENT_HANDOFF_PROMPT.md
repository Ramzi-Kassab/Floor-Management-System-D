# Handoff Prompt for the ERP Automation Development Agent

> **Copy everything below the line and paste it as your first message to the continuing agent.**

---

Hey there, fellow agent 👋

I'm the research agent who spent the last session diving deep into all the ERP reference data, the Flask legacy app, the Excel files, and the business logic behind ARDT's ERP automation. You're the one who built the incredible D365 Smart Interaction System — the recorder, executor, interaction engine, chain system, debug mode, and that beautiful workflow editor UI. Seriously impressive work on those 42 files.

Now it's your turn to take the wheel on D3, and I've left you a comprehensive research document to make sure nothing falls through the cracks.

## Your Research Document

**File:** `docs/ERP_AUTOMATION_RESEARCH.md` (693 lines, committed to git)

This document contains everything I learned from studying:
- All 13 Excel files (now in `docs/erp_reference/`)
- The Flask legacy app (`apps/ERP_Item_creation_automation/` in D2)
- The Job Card structure (29 sheets, evaluation grids, router sheet)
- BITS TRACKING (24 sheets, 5,367+ WOs across 11 accounts)
- The full routes decision matrix (121 approved routes from 228)
- The ERP Items structure (1,160 items across 10 item groups)

## What's In The Document (Section by Section)

1. **Excel Files Inventory** — All 13 files with descriptions, now in `docs/erp_reference/`
2. **Flask App Feature Inventory** — Complete breakdown of the 26-step Create Item workflow, 73 dictionaries, 81 locators, and the 3 main features (Create Item, Movement Journal, BOM Version)
3. **BITS TRACKING Structure** — 11 account sheets with column mappings, 5 summary sheets, account-to-item-group mapping
4. **Job Card Structure** — All 29 sheets documented, the critical "Data" sheet fields, evaluation types, and the router sheet
5. **ERP Routes Decision Matrix** — How 7-10 binary inputs map to 121 approved routes. The full binary encoding scheme for FC repair routes (0091-0122)
6. **ERP Items Structure** — 10 item groups, naming conventions, the Product Dimensions mapping (Config=fixed, Size={{SIZE}}, Color={{MAT NO.}}, Style={{TYPE}})
7. **Data Field Mappings** — Exact mappings from Job Card → BITS TRACKING → ERPJobData model → D365 form fields. Template variables documented.
8. **Flask-to-Django Gap Analysis** — 14 specific gaps with priority ratings. The big ones: duplicate item detection loop (RC-LSTK), Product Dimensions/Variants, BOM Version creation, Movement Journal
9. **Route Selection Engine Specification** — Complete algorithm with the binary encoding scheme, special cases (inspection, re-run), and all edge cases
10. **Phased Recommendations** — 5 phases from "Route Selection" to "Movement Journal + Advanced"

## What's Already Done on D3

Your commit aebdee5 (pushed to GitHub) already has:
- Full models: Locator, LocatorStrategy, Workflow, WorkflowStep, RecordingSession, RecordedAction, WorkflowExecution, StepExecution, ERPJobData, ERPRoute, FieldMapping, ItemCounter, WorkflowChain, WorkflowChainLink, ChainExecution
- InteractionMode enum with 10 D365 modes
- D365InteractionEngine with mode-specific interaction chains
- Recorder, Executor, Locator Engine, Chain Executor services
- Recording → Workflow auto-converter with D365-safe locator generation
- Workflow Editor UI with step CRUD, locator CRUD, searchable locator picker
- Debug execution mode and live execution progress
- Job Card parser and route selector (basic versions)

## What Needs Building Next (My Recommended Order)

### Phase 1: Route Selection Enhancement
The current `route_selector.py` is basic. The research doc has the full binary encoding scheme for routes 0091-0122. You need to handle:
- 32 binary combinations of [Port × USR × HF × C&S × Inspection]
- Two size classes: AB (<12") and JUMBO (≥12")
- Special routes: Re-Run (0124/0125), Inspection-Only (0134/0135)
- Account-based branching (LSTK→RPR-FC-LST, ARAMCO→RPR-FC-AR, UR→RPR-FC-UR, etc.)

### Phase 2: Job Card Parser Enhancement
The parser needs to extract:
- Evaluation data (Receiving, ARDT, Engineer, QC evaluations from sheets 4-12)
- Cutter BOM from "For Plant Use Only" table
- Repair modifiers (hardfacing, USR, crush & shear) from evaluation decisions
- These feed into route selection

### Phase 3: "Create Released Product" Workflow
Port the Flask app's 26-step workflow. Key insight: the Flask uses a JSON-based approach with dictionaries and locators. Your Django system is more sophisticated with the InteractionMode and strategy fallbacks. Map the Flask's 73 dictionaries to your WorkflowStep value templates.

### Phase 4: Duplicate Item Detection
The Flask app has a loop for RC-LSTK items: try creating with sequential suffixes (-01, -02, ..., up to -99) until one doesn't already exist. This needs to be a feature in the executor.

### Phase 5: BOM Version + Production Order + Movement Journal
These are additional D365 workflows that chain together: Create Item → BOM Version → Production Order.

## Key Business Insights You'll Need

1. **Body Material**: If SMI type ends with lowercase 's' → Steel Body (SB), otherwise Matrix Body (MB)
2. **Size parsing**: Job cards use fractions ("3 3/4\"") — need to convert to decimal (3.75)
3. **L5 MAT cleanup**: Remove trailing 'M' from MAT codes (e.g., "1224750M" → "1224750")
4. **Product Dimensions**: Config ID = `RB-FC-ST` (fixed), Size = bit size, Color = L5 MAT, Style = SMI type
5. **Item Groups by Account**: LSTK→RPR-FC-LST, ARAMCO→RPR-FC-AR, UR→RPR-FC-UR, L3→MFG-FC-L3, L4→MFG-FC-L4
6. **Port rule**: Bits < 4" always have port grinding. Bits ≥ 4" never do.

## Git State

- Branch: `dev/2026-02-13-setup`
- All pushed to GitHub
- D3 server runs on port 8001 (`python manage.py runserver 0.0.0.0:8001`)
- The research document and all Excel files are committed

## One Last Thing

Read `docs/ERP_AUTOMATION_RESEARCH.md` before you start coding. It has the exact field mappings, the binary route encoding that took me hours to figure out, and the gap analysis that will save you from missing features. Everything is verified against the actual Excel files — no guessing.

You built the engine. I mapped the road. Now drive. 🚀

— The Research Agent
