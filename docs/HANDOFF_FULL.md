# FMS Project Handoff — Full Session Recap

## FIRST THING TO DO
```bash
cd "D:/PycharmProjects/floor_management_system-D3"
git add -A
git commit -m "Phase 2 WIP: pre-repair eval page, standalone test models, migration 0037, placeholder templates"
git push origin master
git log --oneline -3
```

---

## Project Info
- **Location:** `D:/PycharmProjects/floor_management_system-D3`
- **Server:** `http://localhost:8001`
- **Venv:** `venv/Scripts/python.exe`
- **Branch:** master
- **Last committed before this session:** `376f286` — Evaluation System Phase 1

---

## Session Story — What Ramzi Asked For & What Was Built

### Phase 1 (COMMITTED at `376f286`)

**Ramzi's request:** Build a multi-section evaluation form with LPT pressure test, API thread inspection, section toggles.

**What was built:**
- Expanded `CutterEvaluationMatrix` model with 13 new fields via migration `0036`:
  - Section flags: `include_checklist`, `include_cutter_grid`, `include_pocket_eval`, `include_die_check`, `include_pressure_test`, `include_thread_inspection`
  - JSONFields: `pressure_test_data`, `thread_inspection_data`
  - Status flow: DRAFT → IN_PROGRESS → COMPLETED → APPROVED → REJECTED
  - Auto-generated `inspection_number` (EV-YYYY-NNNN)
- `SECTION_DEFAULTS` dict on model mapping eval types to default include_* flags
- `MANUFACTURE_OVERRIDES` dict for manufacture workflow overrides
- `apply_section_defaults(workflow_type)` model method
- LPT Pressure Test section in `cutter_evaluation_matrix.html` (gated by `{% if include_pressure_test %}`)
- API Thread Inspection section (gated by `{% if include_thread_inspection %}`)
- Fixed Django `split` filter bug — replaced with 5 hardcoded `<tr>` rows
- JS functions: `collectPressureTestData()`, `populatePressureTest()`, `collectThreadInspectionData()`, `populateThreadInspection()`
- "Sections" dropdown button in toolbar to toggle sections on edit page
- Section checkboxes on create form with JS auto-toggle on eval type change
- Test data: WO pk=31 `TEST-EVAL-001`, eval pk=1 (PDC+die), pk=2 (final+thread), pk=3 (ALL sections)

---

### Phase 2 (NOT YET COMMITTED — files saved on disk)

**Ramzi's feedback:** "I checked the page which you created, its not like what I imagined!"

**Ramzi's exact request:**
> "We have the best page and the most completed one is `http://localhost:8001/work-orders/drill-bits/54/receiving-inspection/2/` — lets take a copy of it and make it for pre-repair evaluation. We need to make few changes:
> 1. Add an icon to request pressure test, another for API test, a third for Die check — these icons will lead to separate pages handling only one of these tests.
> 2. Once we complete this evaluation and its related pages, we need to remove what you did for this part.
> 3. Die check is a requirement for pre-repair evaluation — the checklist needs to be auto filled as OK or Not OK with all remarks from the test and a link to the related test.
> 4. Same thing for the API pin, but here it's not a requirement — it can be requested by a link next to the checklist related point and it can be empty and visual inspection can be enough."

**Agent clarification questions & Ramzi's answers:**
- Q: Should checklist auto-fill with result + link when Die Check/LPT completed? **A: Yes**
- Q: Die Check page — single grid table (not two tabs)? **A: Yes, one table, placeholder for now**
- Q: Icon click → navigate to separate Die Check form page (new model/record)? **A: Yes (option a)**
- Q: Remove the embedded LPT/Thread sections from old template? **A: Use exactly the same page as receiving inspection — which has none of those parts. New template replaces cutter_evaluation_matrix.html**
- Q: New template or replace existing? **A: New template, cloned from receiving inspection, replaces cutter_evaluation_matrix.html**
- Q: Separate records (new models) for Die Check/LPT/Thread linked to WO via FK? **A: Yes, correct. And can be connected to the serial number if there is no WO.**

**What was built:**

#### New Models (`apps/workorders/models.py`, end of file ~line 3770)
```
DieCheckReport          → db_table="die_check_reports"
StandaloneLPTReport     → db_table="standalone_lpt_reports"  (result max_length=15)
StandaloneThreadReport  → db_table="standalone_thread_reports"
```
All 3 models have FK to: `WorkOrder (null=True)`, `DrillBit (null=True)`, `CutterEvaluationMatrix (null=True, SET_NULL)`
This allows connection to serial number even if no WO exists.

#### Migration `0037_standalone_test_reports.py` — ALREADY APPLIED TO DB
```bash
# Confirmed applied:
# Applying workorders.0037_standalone_test_reports... OK
```

#### Updated Import (`apps/workorders/views_jobcard.py`, ~line 37)
```python
LPTReport, APIThreadInspection,
DieCheckReport, StandaloneLPTReport, StandaloneThreadReport,  # NEW LINE
```

#### New Views (end of `apps/workorders/views_jobcard.py`)

**`PreRepairEvalEditView`** — main page
- Template: `pre_repair_evaluation.html`
- GET: loads matrix, builds 18-item PDC_EVAL checklist from `CHECKLIST_ITEMS`, loads die_check/pocket/cutter grid data, loads linked test reports
- POST JSON: saves checklist_data, cutter grid (→ die_check_data), pocket grid (→ pocket_evaluation_data), decision, remarks, mark_complete
- POST form: standard form save with version tracking via `create_form_revision`

**`DieCheckReportView`** — standalone die check
- Template: `die_check_report.html`
- Saves `grid_data` (JSON), `result`, `remarks`
- On complete: auto-fills checklist item "Die Check" (item #4) as OK/NOT_OK with remark "Die Check: Pass (Report #N)"
- Redirects back to pre_repair_eval_edit after save

**`StandaloneLPTReportView`** — standalone LPT
- Template: `standalone_lpt_report.html`
- On complete: auto-fills checklist item "Pressure Test (Where Applicable)" (item #16)

**`StandaloneThreadReportView`** — standalone API thread
- Template: `standalone_thread_report.html`
- On complete: auto-fills checklist item "API Pin" (item #14) — optional

#### PDC_EVAL Redirect in `CutterEvaluationCreateView.get_success_url()` (~line 720)
```python
if self.object.evaluation_type == 'PDC_EVAL':
    return reverse('workorders:pre_repair_eval_edit', kwargs={
        'wo_pk': self.kwargs['wo_pk'],
        'pk': self.object.pk
    })
```
Same redirect added in `EvaluationAutoCreateView` (~line 3421).

#### New URLs (`apps/workorders/urls.py`)
```python
# Pre-Repair Evaluation (PDC_EVAL)
path("<int:wo_pk>/pre-repair-eval/<int:pk>/",
     views_jobcard.PreRepairEvalEditView.as_view(), name="pre_repair_eval_edit"),

# Standalone Test Pages
path("<int:wo_pk>/die-check/create/<int:eval_pk>/",
     views_jobcard.DieCheckReportView.as_view(), name="die_check_create"),
path("<int:wo_pk>/die-check/<int:pk>/edit/<int:eval_pk>/",
     views_jobcard.DieCheckReportView.as_view(), name="die_check_edit"),
path("<int:wo_pk>/lpt/create/<int:eval_pk>/",
     views_jobcard.StandaloneLPTReportView.as_view(), name="lpt_report_standalone_create"),
path("<int:wo_pk>/lpt/<int:pk>/edit/<int:eval_pk>/",
     views_jobcard.StandaloneLPTReportView.as_view(), name="lpt_report_standalone_edit"),
path("<int:wo_pk>/thread/create/<int:eval_pk>/",
     views_jobcard.StandaloneThreadReportView.as_view(), name="thread_report_create"),
path("<int:wo_pk>/thread/<int:pk>/edit/<int:eval_pk>/",
     views_jobcard.StandaloneThreadReportView.as_view(), name="thread_report_edit"),
```

#### New Templates
- `templates/workorders/pre_repair_evaluation.html` — 1286 lines
  - Cloned from `receiving_inspection_form.html` (~2060 lines)
  - Header: QAS/1002, "Internal Evaluation Sheet"
  - JSON-based 18-item checklist (not form fields)
  - 3 icon buttons in header toolbar linking to die_check_create / lpt_report_standalone_create / thread_report_create
  - Checklist items #4, #14, #16 show auto-fill badge + link when linked report exists
  - Decision section uses `CutterEvaluationMatrix.Decision` choices
  - AJAX JSON save (same pattern as receiving inspection)
- `templates/workorders/die_check_report.html` — ~110 lines, placeholder
- `templates/workorders/standalone_lpt_report.html` — placeholder
- `templates/workorders/standalone_thread_report.html` — placeholder

---

## Test Data in DB
- WO pk=31, `TEST-EVAL-001`, drill bit serial=`17894562`, design=`2022318`
- Eval pk=1 → PDC_EVAL → URL: `http://localhost:8001/work-orders/31/pre-repair-eval/1/`
- Eval pk=2 → FINAL_INSPECTION
- Eval pk=3 → ALL sections enabled

Login: any user, password `Ardt@2025`

---

## Verify Files Exist (Run After Committing)
```bash
ls templates/workorders/pre_repair_evaluation.html
ls templates/workorders/die_check_report.html
ls apps/workorders/migrations/0037_standalone_test_reports.py
grep -n "PreRepairEvalEditView" apps/workorders/views_jobcard.py
grep -n "pre_repair_eval_edit" apps/workorders/urls.py
grep -n "DieCheckReport" apps/workorders/models.py | tail -5
python manage.py showmigrations workorders | grep 003
```

---

## What Still Needs Doing (Exact Priority Order)

1. **Commit** (command at top of this file)
2. **Test** `http://localhost:8001/work-orders/31/pre-repair-eval/1/` — check for template errors, JS errors in browser console
3. **Fix any errors** in `pre_repair_evaluation.html` — it's a 1286-line clone and may have broken variable references
4. **Build Die Check standalone page properly:**
   - Single grid table (blade × cutter positions) — one table, not two tabs
   - Save/load grid_data as JSON
   - Result field (PASS/FAIL/PARTIAL), remarks, mark complete button
   - Back button → returns to pre-repair eval page
5. **Build LPT standalone page** — QAS/1004-1, materials table (Cleaner/Penetrant/Developer with product/batch/expiry), surface temp, light intensity, dwell times, result, operator
6. **Build API Thread standalone page** — 5 checkpoints (Pin Face, Thread, Pitch Gauge, Mud Seal, Other Observation), OK/Not OK radios, pin height, repair decision
7. **Test auto-fill flow:**
   - Complete a die check → go back to eval → checklist item #4 should show OK/NOT_OK with "See Report #N" link
   - Same for LPT → item #16
   - Same for Thread → item #14 (optional)
8. **Remove old embedded LPT/Thread HTML sections** from `cutter_evaluation_matrix.html` (the sections added in Phase 1 — no longer needed since they're standalone pages now)
9. **Update CLAUDE.md** with all Phase 2 changes

---

## Key Architecture Reference

### Checklist Data JSON Format (stored in `matrix.checklist_data`)
```json
[
  {"item": "Die Check", "status": "OK", "reason": "", "remarks": "Die Check: Pass (Report #5)"},
  {"item": "API Pin", "status": "", "reason": "", "remarks": ""},
  {"item": "Pressure Test (Where Applicable)", "status": "NOT_OK", "reason": "", "remarks": "LPT: Fail (Report #2)"}
]
```

### CutterEvaluationMatrix Fields Used by Pre-Repair Page
| Field | Type | Purpose |
|---|---|---|
| `checklist_data` | JSONField | 18-item checklist |
| `die_check_data` | JSONField | cutter evaluation grid |
| `pocket_evaluation_data` | JSONField | pocket grid |
| `decision` | CharField | REPAIR/SCRAP/REWORK etc. |
| `general_remark` | TextField | overall remarks |
| `is_complete` | BooleanField | completion status |
| `inspection_number` | CharField | EV-YYYY-NNNN |
| `qc_by` | FK User | who completed |
| `qc_at` | DateTimeField | when completed |

### PDC_EVAL Checklist Items (18 items, index in CHECKLIST_ITEMS dict)
- Item #4 = `"Die Check"` → **required** → auto-filled by `DieCheckReport`
- Item #14 = `"API Pin"` → **optional** → auto-filled by `StandaloneThreadReport`
- Item #16 = `"Pressure Test (Where Applicable)"` → auto-filled by `StandaloneLPTReport`

### Gold Standard Reference Page
- URL: `http://localhost:8001/work-orders/drill-bits/54/receiving-inspection/2/`
- Template: `templates/workorders/receiving_inspection_form.html` (~2060 lines)
- This is the UI/UX reference — `pre_repair_evaluation.html` was cloned from it

### Helper Functions Available in views_jobcard.py
- `_get_bom_blade_data(bit)` — returns blade_data, bom_summary, cutter_config_list, has_bom, cutter_grid_ctx
- `_get_pocket_grid_context(bit)` — returns pocket grid context dict (~line 2917)
- `_json` = `import json as _json`
- `notify(...)` — notification helper
- `create_form_revision(...)` — version tracking helper
- `timezone` = `from django.utils import timezone`

---

## Important Notes for Next Agent
- **Do NOT rename** `StandaloneLPTReport` back to `LPTReport` — there is already an old `LPTReport` model in the file (~line 2630). Same for `APIThreadInspection` which already exists.
- **Migration 0037 is already applied** — do not re-run it or recreate it.
- **CLAUDE.md is very large** (188k chars) — agent warned about performance impact. Use `/memory` to trim if needed.
- **The old `cutter_evaluation_matrix.html`** still has the embedded LPT/Thread sections from Phase 1 — these should be removed AFTER standalone pages are confirmed working.
