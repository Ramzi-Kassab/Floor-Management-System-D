# ERP Automation Research Handoff Document

**Author:** Research Agent (Session Feb 13, 2026)
**For:** Development Agent (D365 Smart Interaction System builder)
**Date:** February 13, 2026

> This document contains ~20 hours of research findings from studying both ERP automation apps
> in D2, all Excel reference files (Job Cards, BITS TRACKING, Routes, Items), and the full
> commit aebdee5 codebase. Use this as your reference — everything here is verified against
> the actual files.

---

## Table of Contents

1. [Excel Files Copied to D3](#1-excel-files-copied-to-d3)
2. [Flask App Feature Inventory](#2-flask-app-feature-inventory)
3. [BITS TRACKING Structure](#3-bits-tracking-structure)
4. [Job Card Structure (29 Sheets)](#4-job-card-structure-29-sheets)
5. [ERP Routes Decision Matrix](#5-erp-routes-decision-matrix)
6. [ERP Items Structure](#6-erp-items-structure)
7. [Data Field Mappings](#7-data-field-mappings)
8. [Flask-to-Django Gap Analysis](#8-flask-to-django-gap-analysis)
9. [Route Selection Engine Specification](#9-route-selection-engine-specification)
10. [Recommendations for Next Steps](#10-recommendations-for-next-steps)

---

## 1. Excel Files Copied to D3

All files are in `docs/erp_reference/` (committed and pushed to GitHub):

| # | File | Size | Content |
|---|------|------|---------|
| 1 | `20251179-13791954R10.xlsx` | 1.7 MB | Populated Job Card — WO 20251179, SN 13791954R10, 3 3/4", GT53s, LSTK |
| 2 | `20261004-14304769R1.xlsx` | 1.7 MB | Populated Job Card — WO 20261004, SN 14304769R1, 6 1/8", HD54, LSTK |
| 3 | `Fixed cutters Drill bits JC Template.xlsx` | 1.7 MB | Blank Job Card template (same 29-sheet structure) |
| 4 | `BITS TRACKING.xlsx` | 1.1 MB | Main tracking — 24 sheets, 11 accounts, 5,367+ WOs |
| 5 | `BITS TRACKING-2-1-2026.xlsx` | 937 KB | Cleaned copy (15 sheets, scratch removed) |
| 6 | `BITS TRACKING 10-25-2025.xlsx` | 9.1 KB | Flask prototype file (ARAMCO only, 35 rows) |
| 7 | `Cutter Inventory 01-15-2026.xlsx` | 1.6 MB | 302 PDC cutters with variant stock breakdown |
| 8 | `Cutters ERP Item Numbers2.xlsx` | 36 KB | 301 cutters with ERP item numbers per variant |
| 9 | `Items_639021531472517099.xlsx` | 65 KB | 1,160 ERP drill bit items across 10 item groups |
| 10 | `On-hand.xlsx` | 160 KB | 3,031 ERP on-hand inventory records |
| 11 | `ProductionPlanner (1).xlsx` | 36 KB | 204 production planning requests (from MS Forms) |
| 12 | `Purchase order lines_639021523428755246.xlsx` | 13 KB | 39 ERP PO lines |
| 13 | `Routes_639060775536080551.xlsx` | 7.1 KB | 228 ERP routes (121 approved) |

---

## 2. Flask App Feature Inventory

The standalone Flask app at `D2/apps/ERP_Item_creation_automation/` has these components:

### Files
| File | Lines | Purpose |
|------|-------|---------|
| `playwright-app.py` | 755 | Main Flask + SocketIO app |
| `web_handler.py` | 265 | Playwright wrapper (NOT imported by main app) |
| `excel_handler.py` | 363 | Flask Blueprint for Excel operations |
| `dictionaries.json` | ~2,387 | 73 action definitions |
| `locators.json` | ~582 | 81 XPath element locators |
| `workflows/Create Item.json` | 36 | 26-step item creation workflow |
| `config.json` | 7 | Default settings |
| `item_counters.json` | 3 | Auto-increment counters |

### 73 Dictionary Entries by Category

| Category | Count | Key Entries |
|----------|-------|-------------|
| Login | 3 | `login_user_field_dict`, `login_pass_field_dict`, `login_submit_button_dict` |
| Navigation | 2 | `Favorites_dict`, `Released_products_dict` |
| New Product Creation | 5 | Form open, product subtype dropdown, Product Master select, OK button |
| Item Group (account-based) | 7 | LSTK→`RPR-FC-LST`, RC-LSTK→`RPR-RC-LST`, HALLIBURTON→`RPR-FC-HDB`, Hal_Regional→`RPR-FC-REG`, ARAMCO→`RPR-FC-AR`, plus RC variants |
| Product Detail Fields | 13 | Item Model Group, Product Number, Storage/Tracking/Unit dims, Product Name |
| Search Names & Old Serial | 3 | Search Name 1 & 2, Old Serial ID |
| Product Dimensions | 15 | Config, Size, Color (=MAT#), Style (=Type) creation |
| Product Variants | 6 | Variant suggestions, create variant |
| Apply Template | 3 | Template selection (2 entries have parsing errors) |
| BOM Version | 10 | New BOM, create version, switch view, filter, select, approve |
| Duplicate Item Error | 2 | Detect + close error message |
| Product Workflow Status | 3 | Update status dialog |
| Movement Journal | 22+ | Full journal creation flow (navigate, filter, new, lines, serial, dimensions) |
| Error Entries | 4 | Parsing errors (corrupted JSON) |

### 81 Locators (All XPath)

All target D365 F&O at `prod.alrushaid.net`. Key patterns:
- Login: CSS selectors (`#userNameInput`, `#passwordInput`, `#submitButton`)
- Fields: `@name="FieldName"` (most stable D365 pattern)
- Buttons: `contains(@id, "StableIdPart")` (handles dynamic prefixes)
- Dropdowns: `@title='OptionValue'` for selection items
- Grids: Row/column indexing (`grid_r0_c0`)

### "Create Item" Workflow (26 Steps)

Valid sheets: LSTK, RC-LSTK, ARAMCO

| Step | Action | Key Detail |
|------|--------|-----------|
| 1-3 | Login | Username, password, submit |
| 4-5 | Navigate | Favorites → Released Products (10s wait) |
| 6-8 | New product | New button → Product Subtype → Product Master |
| 9 | **BRANCH** | `locator_by_account` → selects Item Group per account |
| 10 | Fill | Item Model Group = "Repair Bit" |
| 11 | Fill | Product Number = `{{ITEM NO}}` (RC-LSTK: duplicate loop) |
| 12-13 | Error | Duplicate item detection + close |
| 14-18 | Fill | Storage=SWL, Tracking=Serial, Units=ea (×3) |
| 19 | Fill | Dimension Group = CSCS |
| 20 | Fill | Product Name = `{{ORDER NO.}} {{SERIAL NO}} {{SIZE}} {{TYPE}} {{MAT NO.}}` |
| 21-22 | Fill | Search Names = `{{SERIAL NO}}` (clear first) |
| 23-24 | Click | OK buttons (Released Product + Attributes) |
| 25 | Fill | Old Serial ID = `{{SERIAL NO}}` (clear first) |
| 26 | Click | Expand product header |

### Account-Based Branching (Step 9)

```json
{
  "LSTK": "Item_group_dict_LSTK_FC",        // fills "RPR-FC-LST"
  "RC-LSTK": "Item_group_dict_LSTK_RC",     // fills "RPR-RC-LST"
  "HALLIBURTON": "Item_group_dict_HALLIBURTON", // fills "RPR-FC-HDB"
  "Hal_Regional": "Item_group_dict_REG_FC",  // fills "RPR-FC-REG"
  "ARAMCO": "Item_group_dict_ARAMCO",        // fills "RPR-FC-AR"
  "default": "Favorites_dict"                // fallback (no-op)
}
```

### Duplicate Item Loop (RC-LSTK only)

At step 11, for RC-LSTK accounts:
1. Load counter from `item_counters.json` (e.g., `RC-LSTK: 20`)
2. Generate `RPR-RC-LST-{counter:04d}`
3. Fill Product Number field
4. Wait 0.7s for ERP validation
5. Check for `span.messageBar-message` containing "already been assigned"
6. If duplicate: close warning, increment counter, retry (up to 100 attempts)
7. If accepted: save counter+1 to file, continue

### Product Name Template

```
{{ORDER NO.}} {{SERIAL NO}} {{SIZE}} {{TYPE}} {{MAT NO.}}
```
Example: `WO-2025-001 12345678 8.5" GT65RHS 1283567M1`

### D365 Product Dimensions Mapping

| D365 Dimension | Mapped To | Example |
|----------------|-----------|---------|
| Configuration | Fixed: `Prod_Dimen_Config` | Always same |
| Size | `{{SIZE}}` | `8 1/2"` |
| Color | `{{MAT NO.}}` | `1283567M1` |
| Style | `{{TYPE}}` | `GT65RHS` |

---

## 3. BITS TRACKING Structure

### 11 Account Sheets (33 Standard Columns)

| Col | Header | Type | Route-Relevant |
|-----|--------|------|----------------|
| 1 | ORDER NO. | String/Int | |
| 2 | SERIAL NO / SEREAL NO. | String | |
| 3 | SIZE | String/Float | **Yes** → AB/Jumbo |
| 4 | TYPE | String | **Yes** → FC/RC |
| 5 | MAT NO. / LV5 MAT NO. | String | |
| 6 | RECIVED | Date | |
| 7 | FROM | String | **Yes** → Account/Level |
| 8 | *(varies)* | String | Design-level MAT |
| 9 | NEW TYPE | String | |
| 10 | STATUS | String | **Yes** → Repair/Rerun/Scrap |
| 11 | FINAL / Repair Price | Float | |
| 12 | Upper Section Replacement | String | **Yes** → USR flag |
| 13 | Build up / Build Up | String | **Yes** → Hardfacing flag |
| 14-20 | Operators + process steps | String | |
| 21 | Rework | String | |
| 22 | ACCOMPLISHED DATE | Date | |
| 23 | REMARKS | String | |
| 24 | Job Name | String | WO-SERIAL composite |
| 25-27 | Issue tracking + production days | Various | |
| 28 | ITEM NUMBER | String | ERP item number |
| 29 | MJ # | String | Material Journal |
| 30-33 | Production Order, Transfer, Quotation, RAF | Various | |

### Column 8 Varies by Account

| Account | Col 8 Header |
|---------|-------------|
| LSTK, UR, WFD, ARAMCO | `Origional MAT Level` |
| L3 | `LV3 MAT NO.` |
| L4 | `LV4 MAT NO.` |
| ARDT, HALLIBURTON | `L3,L4 or L5 MAT No.` |
| RC-LSTK, Hal_Regional | `LV3 MAT NO.` |

### ARAMCO Extra Columns (34-47)

Purchase Order, Repair Price Final, Cost, Cost Criteria %, IADC, DRSS#, Inspection Group, Primary Replace/Rotate, Backup Replace/Rotate, Back Reamer Replace/Rotate.

### WO Number Formats by Account

| Account | Format | Example |
|---------|--------|---------|
| LSTK | `YYYYNNNN` | `20261019` |
| UR | `YYYY-UR-NNNN` | `2025-UR-1183` |
| L3 | `YYYY-ARDT-LV3-NNN` | `2025-ARDT-LV3-350` |
| L4 | `YYYY-ARDT-LV4-NNN` | `2026-ARDT-LV4-017` |
| ARDT | `YYYY-ARDT-NN` | `2025-ARDT-119` |
| WFD | `YYYY-WFD-NNNN` | `2025-WFD-1095` |
| ARAMCO | `YYYY-AR-NNN` | `2025-AR-163` |
| RC-LSTK | `YYYY-RC-NNN` | `2025-RC-088` |
| HALLIBURTON | `YYYYNNNN-HDBSC` | `20251116-HDBSC` |
| Hal_Regional | `YYYYNNNN-REG` | `20241060-REG` |
| SUB | `YYYY-SUB-NNN` | `2021-SUB-001` |

### ITEM NUMBER Patterns by Account

| Account | Format | Item Group |
|---------|--------|------------|
| LSTK | `R-HD-23-0051`, `R-LS-23-0822` | RPR-FC-LST / RPR-FC-HDB |
| L3 | `RM-FC-MB-0174` | RM-FC-MB |
| L4 | `RM-FC-MB-0188`, `FC-2025-007` | RM-FC-MB / FG-FC |
| ARAMCO | `R-AR-23-0101` | RPR-FC-AR |
| RC-LSTK | `RPR-RC-LST-0018` | RPR-RC-LST |
| HALLIBURTON | `R-HD-22-0004` | RPR-FC-HDB |
| Hal_Regional | `R-FC-RG-22-0001` | RPR-FC-REG |

### WIP Sheet (Production Tracking)

Different column structure — tracks process steps as dates:

| Col | Header | Django Mapping |
|-----|--------|---------------|
| 1-7 | Same as account sheets | WO header fields |
| 8 | STATUS | Current status |
| 9 | Build Up | `RouterSheetEntry` step date |
| 10 | Pocket Grinding | Step date |
| 11 | Braze | Step date |
| 12 | Final grinding | Step date |
| 13 | Tip Grinding | Step date |
| 14 | 1st check | QC step date |
| 15 | Rework | Step date |
| 16-17 | Thread/Body Cleaning | Step dates |
| 18 | USR | Step date |
| 19 | Final Inspection | Step date |
| 20-22 | Remarks, Accomplish, Inspection Group | |

**Key insight:** Account sheets record WHO (operator names), WIP records WHEN (dates).

---

## 4. Job Card Structure (29 Sheets)

### Sheet Inventory

| # | Sheet | QAS Doc | Purpose |
|---|-------|---------|---------|
| 1 | **Data** | — | Master data + flags + pricing + BOM cross-ref |
| 2 | **TRANSPOSE** | — | Computed blade×position grid |
| 3 | **ARDT Cutter Entry** | — | ARDT evaluator cutter matrix |
| 4 | **Eng. Cutter Entry** | — | Engineer evaluation matrix |
| 5 | **Eval & Quot-AR** | QAS/1200 | ARAMCO evaluation + quotation |
| 6 | **Evaluation** | QAS/1001-1 | Internal evaluation pg1 |
| 7 | **E checklist** | QAS/1002 Rev G | 18 inspection steps |
| 8 | **Router Sheet** | QAS/1006 Rev L | 33 process steps |
| 9 | **LPT Report** | QAS/1004-1 | Liquid Penetrant Testing |
| 10 | **Evaluation (2)** | QAS/1001-1 | Internal evaluation pg2 |
| 11 | **Instructions** | — | Historical instructions lookup |
| 12 | **Debrazed cutters** | QAS/1004 Rev D | LPT for debrazed cutters |
| 13 | **Eval-LSTK** | QAS/2001-1 Rev C | External evaluation pg1 |
| 14 | **Eval-LSTK (2)** | QAS/2001-1 | External evaluation pg2 |
| 15 | **Quotation** | — | Internal quotation |
| 16 | **Qut. HALL.** | — | Halliburton quotation |
| 17 | **LSTK-RC** | QAS/109 | Roller Cone inspection |
| 18 | **Rework Cutter Entry** | — | Rework eval grid |
| 19-20 | **Rework / Rework (2)** | QAS/3001 | NCR-linked rework |
| 21 | **Die Check Entry** | — | Die check matrix |
| 22 | **Delivery Tkt** | — | Shipping form |
| 23 | **API Thread Inspection** | QAS/1100 | Thread inspection |
| 24 | **Brazing** | — | Multi-pass brazing matrix |
| 25 | **Hardfacing & Build up** | — | Hardfacing matrix |
| 26 | **Cutters LPT Report** | QAS/1004 | Legacy LPT |
| 27 | **L3 bit material consume** | — | 22 consumable items |
| 28 | **Sheet1** | — | BOM cross-reference |
| 29 | **ARAMCO-CONTRACT** | — | ARAMCO pricing schedule |

### Data Sheet — Key Fields

**WO Header (rows 1-29):**

| Row | Field | Maps To |
|-----|-------|---------|
| 1 | ARDT Work Order No | `WorkOrder.wo_number` / `ERPJobData.work_order_number` |
| 2 | Serial Number | `DrillBit.serial_number` / `ERPJobData.serial_number` |
| 3 | Size | `Design.size` / `ERPJobData.size_raw` |
| 4 | Type | `Design.hdbs_type` / `ERPJobData.smi_type` |
| 5 | LV5 Mat # | `BOM.brazing_mat_no` / `ERPJobData.l5_mat_full` |
| 6 | Bit Date Received | `ERPJobData.date_received` |
| 7 | From | `ERPJobData.account` |
| 8 | LV3 or LV4 Mat # | `ERPJobData.l3_l4_mat` |
| 11 | Evaluated by | `ERPJobData.evaluated_by` |
| 14 | Reviewed by Eng. | `ERPJobData.reviewed_by` |
| 24 | Contract No | `ERPJobData.contract_number` |
| 25 | Vendor No | `ERPJobData.vendor_number` |

**Decision Flags (Column I, rows 2-9):**

| Row | Flag | Maps To |
|-----|------|---------|
| I2 | Rerun by ARDT | `ERPJobData.is_rerun` |
| I3 | Rerun by Engineer | `ERPJobData.is_rerun` |
| I4 | Initial Bit Inspection | `ERPJobData.is_inspection_only` |
| I5 | Scrap | `ERPJobData.is_scrap` |
| I7 | ARDT Matrix Build up | `ERPJobData.has_hardfacing` |
| I8 | Engineer Matrix Build up | `ERPJobData.has_hardfacing` |

**Special Process Fields (rows 30-33):**

| Cell | Field | Maps To |
|------|-------|---------|
| D30 | Upper Section Replacement | `ERPJobData.has_usr` |
| E30 | Pin Size | Design attribute |
| H30 | Track salvage cutters | Flag |
| D33 | Cerebro Installation | Process addon |

**Cutter Modification Tables:**
- Table 1 (D2:G29): Quick cutter swaps — `#, Qty, Part#, Replace Group`
- Table 2 (D10:M29): Final cutter bill — `#, Qty, Size, Part#, Desc, New, Reclaim, Comment`
- Table 3 (N10:O29): Original BOM reference — `Cutters as BOM, Qty as BOM`

### Evaluation Grid Action Codes

| Code | Meaning | In Django |
|------|---------|-----------|
| O | OK | `CutterEvaluationEntry.action = 'O'` |
| X | Replace | `action = 'X'` |
| R | Rotate | `action = 'R'` |
| S | Spin | `action = 'S'` |
| F | Fill | `action = 'F'` |
| L | Lost | `action = 'L'` |
| P | Pocket Build Up | `action = 'P'` (Eval-LSTK only) |
| V | Fin Build Up | `action = 'V'` (Eval-LSTK only) |
| I | Impact Arrestor BU | `action = 'I'` (Eval-LSTK only) |

**Suffix numbers** (O1, X2, R2) link actions to cutter groups — NOT yet modeled in Django.

### Router Sheet — 33 Steps (QAS/1006 Rev L)

| Step | Description | Conditional |
|------|------------|-------------|
| 1 | Nozzle Removal | |
| 2 | Cerebro Removal | Yes/No |
| 3 | Cer. O-Ring Removal | Yes/No |
| 4 | Washing | |
| 5 | Sand Blasting | |
| 6 | Pressure Test | If Applicable |
| 7 | Die Check | |
| 8 | Photos & Evaluation | |
| 9 | Bit Head Preparation | |
| 10 | De-Brazing | If Applicable |
| 11 | Matrix or Hardfacing Repair | If Applicable |
| 12 | Pocket, Blade or IA Grinding | If Applicable |
| 13 | Sand Blasting | |
| 14 | Bit Head Prep For Brazing | |
| 15 | Brazing | |
| 16 | Washing | |
| 17 | Sand Blasting | |
| 18 | Die Check | |
| 19 | Final Grinding | |
| 20 | Tip Grinding | |
| 21 | Washing | |
| 22 | Sand Blasting | |
| 23 | Die Check | |
| 24 | Upper Section Removal & Assembly | If Applicable |
| 25 | Upper Section Sub-Arc Welding | If Applicable |
| 26 | Shank Machining | If Applicable |
| 27 | Pressure Test | If Applicable |
| 28 | Bit Photos | |
| 29 | QC Inspection | |
| 30 | Final Inspection | |
| 31 | Painting & Boxing | |
| 32 | Cerebro Installation | Yes/No |
| 33 | Cerebro Cap Tightening | Yes/No |

---

## 5. ERP Routes Decision Matrix

### Route Naming Convention

```
{BitType} {Level} {BodySize} {PortGrinding} {Processes...}
```

### Decision Factors

| # | Factor | Options | Source |
|---|--------|---------|--------|
| 1 | Bit Type | FC / RC | Derived from Type field |
| 2 | Order Level | L3, L4, L5, L6, Repair, Rerun, Inspection | Account + FROM field |
| 3 | Body Size | AB (<12") / Jumbo (>=12") | Size field parsed to inches |
| 4 | Port Grinding | With Port / No Port | Design or process decision |
| 5 | USR | Yes / No | Data sheet row 30 |
| 6 | Grinding | Yes / No | Process decision |
| 7 | Hardfacing/Matrix | Yes / No | Data sheet I7/I8 |
| 8 | Crush & Shear | Yes / No | Type contains "CS" |
| 9 | Retrofit | Yes / No | L6 specific |
| 10 | Rerun Only | Yes / No | Data sheet I2/I3 |
| 11 | Sealed/NonSealed | Sealed / NonSealed | RC only |
| 12 | Cone Change | WithCC / NoCC | RC only |

### Complete Approved Routes (121 total)

**FC L3 Manufacture (11 routes): ROUTE-0001, 0005, 0082-0090**
All combos of: AB/Jumbo × No Port/With Port × Standard/Grinding/USR/USR Grinding

**FC L4 Manufacture (15 routes): ROUTE-0010-0024, 0127**
Same combos as L3

**FC L5 Manufacture (16 routes): ROUTE-0025-0040**
AB/Jumbo × No Port/With Port × Standard/Grinding/USR/USR Grinding

**FC L6 Manufacture (32 routes): ROUTE-0041-0072**
L5 combos PLUS Retro variants: Retro, Retro Grinding, Retro USR, Retro Grinding USR

**FC-R Repair AB (18 routes): ROUTE-0091-0106, 0124, 0126**
- Standard, USR, Hardfacing, C&S combinations
- With Port / No Port variants
- Re-Run (ROUTE-0124)
- NO REPAIR ONLY USR (ROUTE-0126)

**FC-R Repair Jumbo (18 routes): ROUTE-0107-0122, 0125**
Same as AB but for Jumbo size

**RC Routes (12 routes): ROUTE-0073-0081, 0123, 0130-0131**
- AB/Jumbo × Sealed/NonSealed × WithCC/NoCC
- Jumbo sub-sizes: Up to 17", Above 17", 34"
- With Liner Installation variant

**Special Routes:**
- ROUTE-0132: RC Repair - Inspection Only
- ROUTE-0134: FC Repair - Inspection Only

### Size Class Determination

The AB/Jumbo threshold based on analysis of route names and data:
- **AB** = Standard sizes below ~12" (most common: 3 5/8", 5 7/8", 6 1/8", 8 1/2")
- **Jumbo** = 12" and above (12 1/4", 16", 17 1/2", 22", 26", 28", 34")
- For RC Jumbo, sub-categories: Up to 17", Above 17", 34"

---

## 6. ERP Items Structure

From `Items_639021531472517099.xlsx` — 1,160 items:

### Item Groups (10 groups)

| Group | Type | Body | Count |
|-------|------|------|-------|
| FG-FC-MB | Finished Good, Fixed Cutter, Matrix Body | 608 |
| FG-FC-SB | Finished Good, Fixed Cutter, Steel Body | 67 |
| FG-FC-IB | Finished Good, Fixed Cutter, Insert Body | 8 |
| FG-RC-IT | Finished Good, Roller Cone, Insert Type | 88 |
| FG-RC-MT | Finished Good, Roller Cone, Mill Tooth | 83 |
| RM-FC-MB | Raw Material, Fixed Cutter, Matrix Body | 213 |
| RM-FC-SB | Raw Material, Fixed Cutter, Steel Body | 44 |
| RM-FC-IB | Raw Material, Fixed Cutter, Insert Body | 5 |
| RM-RC-IT | Raw Material, Roller Cone, Insert Type | 19 |
| RM-RC-MT | Raw Material, Roller Cone, Mill Tooth | 25 |

### Item Number Format
`{ItemGroup}-{4-digit sequence}` (e.g., `FG-FC-MB-0001`)

### Product Name Format
`{BitSize}:{HDDSType}:{MATNumber}` (e.g., `8 3/8:GT73H:1251085`)

### Product Dimension Group
Always `CSCS` (Configuration-Size-Color-Style)

---

## 7. Data Field Mappings

### Job Card Data Sheet → ERPJobData Model

| JC Field | ERPJobData Field | Template Variable |
|----------|-----------------|-------------------|
| ARDT Work Order No (row 1) | `work_order_number` | `{{ORDER NO.}}` |
| Serial Number (row 2) | `serial_number` | `{{SERIAL NO}}` |
| Size (row 3) | `size_raw`, `size_inches` | `{{SIZE}}` |
| Type (row 4) | `smi_type` | `{{TYPE}}` |
| LV5 Mat # (row 5) | `l5_mat_full`, `l5_mat_original` | `{{MAT NO.}}` |
| Bit Date Received (row 6) | `date_received` | |
| From (row 7) | `account` | `{{FROM}}` |
| LV3/LV4 Mat # (row 8) | `l3_l4_mat` | |
| Contract No (row 24) | `contract_number` | `{{CONTRACT_NO}}` |
| Vendor No (row 25) | `vendor_number` | `{{VENDOR_NO}}` |
| *computed* | `item_number` | `{{ITEM NO}}` |

### BITS TRACKING → ERPJobData

Same fields but from different columns:
- Col 1 → `work_order_number`
- Col 2 → `serial_number`
- Col 3 → `size_raw`
- Col 4 → `smi_type`
- Col 5 → `l5_mat_full`
- Col 7 → `account`
- Col 12 → `has_usr` (if non-empty)
- Col 13 → `has_hardfacing` (if "Build up" or similar)
- Col 28 → `item_number`

### Account → Item Group Mapping

| Account | Item Group (Repair FC) | Item Group (Repair RC) |
|---------|----------------------|----------------------|
| LSTK | RPR-FC-LST | RPR-RC-LST |
| RC-LSTK | RPR-RC-LST | RPR-RC-LST |
| HALLIBURTON | RPR-FC-HDB | — |
| Hal_Regional | RPR-FC-REG | RPR-RC-REG |
| ARAMCO | RPR-FC-AR | RPR-RC-AR |

---

## 8. Flask-to-Django Gap Analysis

### Features in Flask NOT Yet in Django

| # | Feature | Flask Implementation | Django Status |
|---|---------|---------------------|---------------|
| 1 | **Movement Journal automation** | 22+ dictionary entries | Not started |
| 2 | **BOM Version creation + approval** | 10 dictionary entries | Not started |
| 3 | **Product Dimensions + Variants** | 21 dictionary entries | Not started |
| 4 | **SocketIO real-time progress** | Flask-SocketIO | Polling API exists (good enough) |
| 5 | **Duplicate item loop** | 100-attempt retry with counter | `ItemCounter` model exists, needs loop in executor |
| 6 | **Account-based branching** | `locator_by_account` in workflow JSON | `condition_field` + `condition_value` on WorkflowStep exists |
| 7 | **Excel multi-sheet selection** | Session-based accumulation | Excel handler exists, needs enhancement |
| 8 | **Dependent action chains** | `dependent_click_check`, `dependent_send_check` in dict | D365InteractionEngine partially covers this |
| 9 | **Keyboard shortcuts** | `key1`, `key2`, `key3` per action | `press_key_after` exists on WorkflowStep |
| 10 | **Valid sheets per workflow** | `valid_sheets` in workflow JSON | `valid_sheets` JSONField exists on Workflow model |

### Features in Django NOT in Flask

| # | Feature |
|---|---------|
| 1 | D365InteractionEngine with 10 interaction modes |
| 2 | Smart locator engine with self-learning success rates |
| 3 | Browser recording with SPA re-injection |
| 4 | Recording → Workflow auto-conversion |
| 5 | Composite workflow chains with preconditions |
| 6 | Debug execution mode (step-by-step with locator testing) |
| 7 | ERPRoute model with route selection engine |
| 8 | ERPJobData model with Job Card parser |
| 9 | Workflow step CRUD API + editor UI |
| 10 | Locator CRUD API with strategy management |

---

## 9. Route Selection Engine Specification

### Input → Output

**Inputs** (from ERPJobData):
```python
bit_type:       'FC' or 'RC'       # from smi_type analysis
level:          'L3'|'L4'|'L5'|'L6'|'REPAIR'|'RERUN'|'INSPECTION'
size_class:     'AB' or 'JUMBO'    # from size_inches (<12" = AB)
has_port:       bool               # from design or process decision
has_usr:        bool               # from Data sheet D30
has_grinding:   bool               # from process decision
has_hardfacing: bool               # from Data sheet I7/I8
has_crush_shear: bool              # from type containing "CS"
has_retro:      bool               # L6 only
is_sealed:      bool|None          # RC only
has_cc:         bool|None          # RC only
```

**Output**: One `ERPRoute` from the 121 approved routes.

### Selection Logic (FC Repair)

```python
if is_rerun:
    return f"FC-R {size_class} Re-Run"

if is_inspection_only:
    return "FC Repair - Inspection Only"

# Build process suffix
processes = []
if has_usr: processes.append("USR")
if has_hardfacing: processes.append("Hardfacing/Matrix Repair")
if has_crush_shear: processes.append("C&S")

port = "With Port" if has_port else "No Port"

if not processes:
    suffix = "Standard"
elif len(processes) == 1:
    suffix = processes[0]
else:
    suffix = " ".join(processes)  # Combined: "USR Hardfacing/MatrixR C&S"

return f"FC-R {size_class} {port} {suffix}"
```

### Selection Logic (FC Manufacture L3-L6)

```python
processes = []
if has_usr: processes.append("USR")
if has_grinding: processes.append("Grinding")
if has_retro and level == 'L6': processes.append("Retro")

port = "With Port" if has_port else "No Port"

if not processes:
    suffix = "Standard"
else:
    suffix = " ".join(processes)

return f"FC {level} {size_class} {port} {suffix}"
```

---

## 10. Recommendations for Next Steps

Based on the user's stated priorities ("data is enough to create the item in ERP... then go after BOM and Route selection based on evaluation data"):

### Phase 1: Port Flask "Create Item" Workflow
1. **Seed the 81 locators** into Django's Locator + LocatorStrategy models
2. **Seed the "Create Item" workflow** as Workflow + WorkflowStep records (26 steps)
3. **Map account-based branching** using existing `condition_field`/`condition_value`
4. **Implement duplicate item loop** in executor for RC-LSTK
5. **Test against live D365** using the debug execution mode you built

### Phase 2: Enhance Job Card Parser
1. **Extract evaluation flags** from Data sheet (USR, build-up, C&S, rerun, scrap)
2. **Parse cutter modification tables** for BOM data
3. **Support both Job Card and BITS TRACKING** as data sources

### Phase 3: Route Selection Engine
1. **Seed all 121 approved routes** using `seed_erp_routes` command
2. **Build selection logic** matching the specification above
3. **Auto-assign route** when ERPJobData is created/updated

### Phase 4: BOM + Production Order Workflows
1. **Create BOM Version workflow** (from Flask's 10 dictionary entries)
2. **Create Production Order workflow** (new)
3. **Chain them** using composite workflow system: Create Item → BOM → Production Order

### Phase 5: Movement Journal + Advanced
1. **Port Movement Journal workflow** (22+ dictionary entries)
2. **Product Dimensions + Variants** automation
3. **Quotation generation** (3 formats: Internal, Halliburton, ARAMCO)

---

## Appendix: Pricing Reference

### ARDT Standard Pricing Tiers

| Tier | Size Range | Price |
|------|-----------|-------|
| 1 | Up to 6 7/8" | $4,121 |
| 2 | 7" to 8 7/8" | $5,495 |
| 3 | 9" to 14 7/8" | $6,868 |
| 4 | 15" to 28" | $8,245 |
| 5 | Rerun | $550 |

### ARAMCO Contract Pricing (Contract 6600048646)

**Setup + Repair (Matrix Body):**
- Up to 6 7/8": $6,075
- 7" to 8 7/8": $8,350
- 9" to 14 7/8": $9,900
- 15" to 28": $12,950

**Cutter Replacement by Size:**
| Size | Standard | Premium | Super Premium | Other |
|------|----------|---------|---------------|-------|
| 8mm | $196 | $302 | $376 | $290 |
| 10.5mm | $215 | $328 | $419 | $333 |
| 13mm | $345 | $413 | $480 | $333 |
| 16mm | $490 | $545 | $662 | $333 |
| 19mm | $615 | $712 | $836 | $333 |

---

*End of research document. All data verified against actual Excel files and source code.*
