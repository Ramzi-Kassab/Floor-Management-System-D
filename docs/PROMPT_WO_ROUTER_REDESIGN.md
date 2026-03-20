# Prompt: Work Order Workflow & Router System Redesign

## Context
You are working on the ARDT Floor Management System — a Django 5.1 ERP for drill bit manufacturing and repair. The system uses HTMX + Alpine.js + Tailwind CSS (CDN) with Lucide icons. No build step.

The company repairs and manufactures drill bits. Each bit goes through a **process route** (33 steps for FC Repair, 26 for L3/L4 Manufacture). Each step can have quality checks, measurements, photos, operator signatures, and timers.

## What We Need
Design and implement a professional **Router Sheet system** with:
1. **Router Sheet page** — vertical stepper showing all process steps, current step highlighted, operator can start/complete steps
2. **Step Detail page** — individual page per step with: timer, QC checklist, photos, signature capture, instructions, measurements/parameters
3. Integration with the existing **Job Card Summary** page (already redesigned)

## Architecture

### URL Structure
```
/workorders/{pk}/                    → Job Card Summary (already done)
/workorders/{pk}/router/             → Router Sheet (vertical stepper) — REDESIGN
/workorders/{pk}/router/{step}/      → Step Detail (timer, QC, photos) — NEW
```

### Technology Stack
- Backend: Django 5.1, Python 3.10, SQLite
- Frontend: HTMX + Alpine.js + Tailwind CSS (CDN) + Lucide Icons
- No React/Vue/build step — all templates are Django templates with Alpine.js
- Server runs at localhost:8001

### Key Design Principles
- **Operator-focused**: Large buttons, touch-friendly, works on tablets at workstations
- **30-second rule**: Any data capture should take under 30 seconds
- **Progressive disclosure**: Summary first, expand for detail
- **Dark mode support**: All templates use `dark:` Tailwind classes
- **Mobile responsive**: Grid cols collapse on small screens

## Files to Read (in order of importance)

### Critical — Read These First
1. `apps/workorders/models.py` — ALL models. Focus on:
   - `WorkOrder` (line ~660): status, type, relationships
   - `DrillBit` (line ~84): serial, status, condition, level
   - `RouterSheetEntry` (line ~2400): step tracking, QR scan, operator, duration
   - `ProcessRoute` and `ProcessRouteOperation` (line ~2500): route templates with steps
   - `CutterEvaluationMatrix` (line ~1200): 9 evaluation types, 6 section flags
   - `DieCheckReport` (line ~1550): die check with grid data
   - `DrillBitPhoto` (line ~3300): photo model with context types
   - `EvaluationChecklist` (line ~1700): 15 QC checkpoints
   - `StandaloneLPTReport` and `StandaloneThreadReport`: quality reports

2. `apps/workorders/views_jobcard.py` — Main views. Focus on:
   - `WorkOrderDetailEnhancedView` (line ~781): job card context data
   - `RouterSheetView` (line ~656): current router sheet view
   - `api_router_step_scan` (line ~): QR scan API for start/end/skip
   - `CutterEvaluationCreateView` / `CutterEvaluationEditView`: evaluation forms
   - `DieCheckCreateView` / `DieCheckEditView`: die check forms

3. `apps/workorders/urls.py` — All URL patterns

4. `apps/workorders/forms.py` — All forms

### Templates — Current State (Read to understand patterns)
5. `templates/workorders/workorder_detail_enhanced.html` — Redesigned job card summary (3 tabs: Overview, Timeline, Photos)
6. `templates/workorders/router_sheet.html` — Current router sheet (needs redesign to vertical stepper)
7. `templates/workorders/cutter_evaluation_matrix.html` — Evaluation grid with pocket/cutter grids, LPT, thread inspection sections
8. `templates/workorders/cutter_evaluation_form.html` — Evaluation create form
9. `templates/workorders/die_check_report.html` — Die check report with materials, cutter findings, decisions
10. `templates/workorders/receiving_inspection_form.html` — Receiving inspection with pocket/cutter grids, photos
11. `templates/workorders/e_checklist_form.html` — 15-item QC checklist

### Reusable Components
12. `templates/components/photo_module.html` — Photo capture/upload/edit component (ADG sequence, camera, gallery, Fabric.js editor)
13. `templates/base.html` — Base layout with sidebar, topnav, dark mode
14. `templates/includes/sidebar.html` — Navigation sidebar

### Seed Data (Understand what process steps exist)
15. `apps/workorders/management/commands/seed_router_steps.py` — FC Repair 33 steps, L3/L4 Manufacture 26 steps

### Related Models (for BOM/Design context)
16. `apps/technology/models.py` — Design, BOM, BOMLine models
17. `apps/sales/models.py` — Account model (drives WO numbering and workflow type)

## Process Route Steps (FC Repair — 33 Steps)

These are the actual manufacturing steps a drill bit goes through during repair:

| # | Step | QC? | Conditional? | Notes |
|---|------|-----|-------------|-------|
| 1 | Bit Receiving & Setup | | | Initial intake |
| 2 | Visual Inspection | Yes | | Check for damage |
| 3 | Measurement (Gauge) | Yes | | TFA, gauge readings |
| 4 | De-Brazing Decision | | | Cerebro Removal: Yes/No |
| 5 | Burnout Furnace | | Yes | If de-brazing |
| 6 | Cutter Removal & Cleaning | | | |
| 7 | Core Inspection | Yes | | |
| 8 | Cutter Preparation | | | |
| 9 | Layout & Marking | | | |
| 10 | Pocket Preparation | | | |
| 11 | First Layer Brazing | | | |
| 12 | Second Layer Brazing | | | |
| 13 | Rework/Touch-up | | Yes | If needed |
| 14 | Cool-down | | | |
| 15 | Thermal Stress Relief | | Yes | If applicable |
| 16 | Post-Braze Inspection | Yes | | |
| 17 | Measurements Verification | Yes | | |
| 18 | Cleaning & Surface Prep | | | |
| 19 | Assembly/Nozzle | | | |
| 20 | Threading | | Yes | If needed |
| 21 | Final Assembly | | | |
| 22 | Quality Inspection | Yes | | |
| 23 | Die Check (FPI) | Yes | | Fluorescent Penetrant |
| 24 | Final Die Check | Yes | | |
| 25 | Documentation Review | | | |
| 26 | Pack & Label | | | |
| 27 | Dispatch Preparation | | | |
| 28 | Dispatch | | | |
| 29-33 | Audit/Archive/Closure | | | |

## Evaluation Types (9 Total)

| Type | When | Sections |
|------|------|----------|
| RECEIVING | On receipt | Checklist, Cutter Grid, Pocket Grid |
| ARDT | Internal QC | Checklist, Grid, Pocket, Die Check |
| ENGINEER | Client rep | Checklist, Grid, Pocket, Die Check |
| QC | QC checkpoint | Checklist, Grid, Pocket, Die Check |
| DIE_CHECK | FPI test | Die Check only (O/C/H/Y symbols) |
| FINAL_DIE_CHECK | Final FPI | Die Check only |
| FINAL_QC | Final checkpoint | Checklist, Grid, Pocket |
| FINAL_INSPECTION | Before dispatch | Checklist, Grid, Pocket, Thread |
| REWORK | After rework | All sections |

## What the Router Sheet Page Should Include

### Vertical Stepper Layout
- Left sidebar: numbered step list with status indicators (done/active/pending/skipped)
- Main area: current step detail panel
- Click any step to view its details

### Step Detail Panel
For each step, show:
- **Step info**: name, description, work center, standard hours
- **Timer**: Start/Pause/Resume/Complete with elapsed time display
- **Operator**: Auto-filled from logged-in user, with override option
- **QC Checklist**: From ProcessRouteOperation.qc_checklist (if requires_qc)
- **Conditional flags**: Cerebro removal Yes/No, O-ring removal Yes/No
- **Photos**: Photo module for step-specific photos
- **Measurements/Parameters**: Any numerical inputs required for the step
- **Remarks**: Free text field
- **Linked evaluations**: If this step triggers an evaluation (e.g., step 23 → Die Check)
- **Navigation**: Previous/Next step buttons

### Progress Tracking
- Overall progress bar
- Time tracking: planned vs actual per step
- Operator history per step

## Existing QR Scan API

The system already has a QR scan API for starting/completing steps:
```
POST /workorders/{wo_pk}/router-sheet/{step}/api-scan/
Body: { action: "start" | "end" | "skip" }
Returns: { success, timestamps, operator, duration }
```

## Database Notes
- SQLite database (not tracked in git)
- Server: `python manage.py runserver 0.0.0.0:8001`
- Venv: `D:\PycharmProjects\floor_management_system-D3\venv\Scripts\python.exe`
- Settings: `DJANGO_SETTINGS_MODULE=ardt_fms.settings`

## Login Credentials
- Password for all users: `Ardt@2025`
- Sample users: `r.kassab`, `g.escobar`, `m.irshad`, `admin`
