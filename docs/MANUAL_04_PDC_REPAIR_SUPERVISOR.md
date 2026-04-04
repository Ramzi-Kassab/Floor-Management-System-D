# PDC Repair Supervisor — User Manual

**System:** ARDT Floor Management System
**Version:** Draft 1.0
**Date:** April 4, 2026
**Audience:** PDC Repair Supervisor — The person who supervises the repair and manufacturing of PDC (Fixed Cutter) drill bits, manages evaluations, oversees router step progress, and coordinates with the cutter inventory and ERP automation systems.

---

## 1. Your Role in the System

As PDC Repair Supervisor, you are the technical leader on the production floor for all Fixed Cutter drill bit operations. You work hands-on with work orders, evaluations, router sheets, and the cutter inventory. While the Operations Manager handles planning and approvals at a higher level, you manage the detailed execution: which cutters go on which bit, whether a cutter needs to be replaced or rotated, when to perform die checks, and how to progress through each step of the production route.

Your daily work in the system revolves around three areas. First, **work order execution**: you create work orders, monitor router sheet progress, start and complete process steps, and handle quality-related decisions during production. Second, **evaluation management**: you create and fill out evaluations (Receiving, PDC, Engineer, QC, Die Check, Final Inspection, and others), recording the condition of every cutter on every blade, making repair-or-replace decisions, and documenting die check results. Third, **cutter inventory and BOM management**: you review cutter stock levels before starting a job, verify that required cutters are available, and use the Cutter Map tool to create or review Bills of Materials.

You also have access to the ERP Automation module, which automates the creation of items, BOMs, and routes in the D365 ERP system. This is an advanced feature used to push job card data into D365 without manual data entry.

---

## 2. Logging In

**Step 1.** Open your browser and go to: `http://localhost:8001/accounts/login/`

**Step 2.** Enter your **Username** and **Password**.

**Step 3.** Click **Log In**.

**Troubleshooting:**

| Problem | Solution |
|---------|----------|
| Cannot log in | Verify your credentials with the System Administrator. Default password for new accounts is `Ardt@2025`. |
| Cannot see Evaluations or Router Sheet | Your account may be missing the PDC_SUPERVISOR role. Contact the System Administrator. |
| Page shows old data after a code update | The server may need to be restarted. Notify the System Administrator. |
| Form does not save | Check for red error messages on required fields. Scroll down to see all validation errors. |

---

## 3. Your Workbench

Your most-used pages are:

**Work Order Detail Page** (`Production > Work Orders > [WO Number]`): The central page for each job. Contains tabs for Overview, Evaluations, Router Sheet, Photos, and History. Shows the drill bit's serial number, design, BOM, account, and status stepper (Pending through Completed).

**Router Sheet** (tab within WO detail): The ordered list of production steps. Each step shows its number, name, status, operator, start/end times, and any special instructions. Steps with requirements (photos, evaluations) show indicators.

**Evaluation Forms** (linked from WO detail > Evaluations tab): Grid-based inspection forms for recording cutter conditions. Different evaluation types serve different stages (Receiving, ARDT, Die Check, Final QC, etc.).

**Cutter Inventory** (`Logistics > PDC Cutters > Cutter Inventory`): Dashboard showing all PDC cutter stock by type, with variant breakdown (New, Reclaimed, Client-provided, etc.), on-order quantities, and design usage.

**Cutter Map** (`Technical > Cutter Map`): The tool for extracting cutter data from Halliburton PDF documents and creating or reviewing BOMs.

**ERP Automation** (`ERP Automation` section in sidebar): Dashboard, job data upload, workflow execution, and recording tools for D365 automation.

---

## 4. Core Workflows

### 4.1 Creating a Work Order

**When:** A drill bit is in the planner and ready for production, or you need to create a WO directly.

1. Navigate to **Production > Work Orders** and click **Create Work Order** (or go to `/workorders/create/`).
2. Enter the **Serial Number** of the drill bit. The system auto-populates:
   - Size, type, HDBS code, SMI type
   - Design MAT number and level
   - L5 MAT / BOM
   - Repair/rerun counts, received date, from-location
3. Select the **Account** (Business Unit). An info card appears showing the account's workflow type, pricing mode, and max repairs.
4. Review the auto-populated fields and click **Save**.

**What happens next:** The WO is created with Pending status. It needs to be released and approved before production starts.
**Who is notified:** The Operations Manager receives a notification.

### 4.2 Working Through the Router Sheet

**When:** A work order has been approved (Active status) and production can begin.

1. Open the work order detail page and click the **Router Sheet** tab.
2. The sheet shows all steps in order. Find the first Pending step.
3. Click the step name to open its detail view. Review:
   - **Instructions** and **Procedure Reference**
   - **Special Instructions** (design-specific or serial-specific notes, shown in a yellow section)
   - **Checklist Items** (verification points that must be completed)
   - **Parameter Fields** (data entry for measurements, temperatures, etc.)
4. Click **Start** (or scan the QR code from the Operator Portal). The step status changes to In Progress and a timer begins.
5. Complete any required checklists and parameter entries.
6. If the step requires photos, upload them using the Photos section.
7. If the step requires an evaluation, create or complete the linked evaluation.
8. Click **Complete** (or scan the QR code to end the step).

**Step Completion Validations:** The system blocks completion if:
- Required checklist items are not filled
- Required parameters are missing values
- The step requires photos and the minimum count has not been met
- The step requires a linked evaluation and it is not complete

**Who is notified:** When all steps are complete, the Operations Manager and QC Inspector are notified.

**Skipping a Step:**
If a step is not applicable (e.g., the bit does not need a specific treatment), click **Skip** and select a reason from the dropdown (N/A, Within Spec, Accepted As-Is, Approved by Supervisor, Not Required, Done Externally, Deferred, Reordered, or Other). Only supervisors and staff can skip steps.

### 4.3 Creating and Completing Evaluations

**When:** At various stages of production (Receiving, before repair, after repair, die check, final QC).

**Creating an evaluation:**
1. On the WO detail page, go to the **Evaluations** tab.
2. Click **Create Evaluation** next to the appropriate type (e.g., "PDC Evaluation", "Die Check", "Final Inspection").
3. Select the **Evaluation Type** from the dropdown. The system auto-configures which sections are included based on the type:
   - **PDC Evaluation**: Checklist + Cutter Grid + Pocket Evaluation + Die Check
   - **Die Check**: Die Check section only
   - **Final Inspection**: Checklist + Cutter Grid + Pocket Evaluation + Thread Inspection
4. You can override the default sections using the **Sections** checkboxes before saving.
5. Click **Save** to create the evaluation.

**Filling out the cutter evaluation grid:**
1. On the evaluation edit page, scroll to the **Cutter Evaluation** section.
2. The grid shows all blades (B1 through B6+) and all cutter positions.
3. Each cell represents one cutter. Click a cell to open the symbol modal.
4. Select one or more symbols:
   - **O** = OK (no issues found)
   - **X** = Replace
   - **R** = Rotate
   - **S** = Spin
   - **L** = Lost
   - **C** = Cracked
   - **H** = Chipped
   - **M** = Misaligned
5. O is exclusive with other findings (you cannot mark a cutter as both OK and Cracked).
6. Click outside the modal or press Escape to close it. Your selection is saved in the cell.

**Filling out the pocket evaluation grid:**
1. Scroll to the **Pocket Evaluation** section.
2. The grid layout matches the cutter grid. Click a pocket cell to open its modal.
3. Select symbols: **O** (OK), **V** (Fin Build Up), **P** (Pocket Build Up), **I** (Impact Arrestor), **F** (Fill).
4. V (Fin Build Up) has an auto-pairing rule: if you set V on a single pocket, the system automatically adds V to the adjacent pocket (minimum two V's required). If V is on the last pocket in a row, it converts to P.

**Completing the evaluation:**
1. After filling all sections, set the **Result** (Accept, Reject, Conditional) in the Decision section.
2. Click **Save & Complete**.

**Who is notified:** Operations Manager and QC receive a HIGH priority notification.

### 4.4 Performing a Die Check

**When:** Before brazing or after repair, to check for cracks, chips, or porosity in cutters.

1. From the WO detail page or router sheet, click the die check action link.
2. The **Die Check Report** page opens with 6 sections:
   - **Header** — WO number, serial, size, design, stage (Before Braze / After Repair)
   - **Materials Used** — Cleaner, Penetrant, Developer (product name, batch number, expiry date). You can scan barcodes using the built-in scanner.
   - **Cutter Evaluation Grid** — Same grid interface as the main evaluation, but with 4 symbols: O (OK), C (Cracked), H (Chipped), Y (Porosity).
   - **Decisions Table** — Auto-populated from flagged (non-OK) cutters. For each flagged cutter, select a decision: Accepted, Rotate, Spin, Replace, or Waiting Quality Decision.
   - **Result & Remarks** — An auto-generated summary of findings that you can edit. Copy button available.
   - **Photos** — Upload photos using the photo module.
3. Click **Save**.

**Who is notified:** If any cutter has a "Waiting Quality Decision" status, a HIGH priority notification is sent to the quality team.

### 4.5 Reviewing Cutter Inventory

**When:** Before starting a repair job, to verify that required cutters are in stock.

1. Navigate to **Logistics > PDC Cutters > Cutter Inventory** (or `/inventory/cutters/`).
2. The page shows a table of all PDC cutter types with columns for:
   - MAT number, size, type, chamfer, family
   - Total stock
   - Variant breakdown: New, ENO (Excess & Obsolete), Retrofit, Ground, Reclaim, LSTK, Client Used
   - On Order quantity
3. Use the **column filters** (click any column header) to filter and sort.
4. Click **Export Excel** to download the data for offline review. Choose visible columns only or all columns, and all records or filtered rows.

### 4.6 Running ERP Automation

**When:** Job card data needs to be pushed to D365 ERP to create released products, BOMs, routes, and movement journals.

1. Navigate to **ERP Automation > Job Data** (or `/erp-automation/job-data/`).
2. Click **Upload** to upload a Job Card Excel file. The parser extracts WO number, serial, size, type, cutter BOM, and other fields.
3. Review the parsed data on the job data detail page. Verify all fields are correct.
4. Ensure ERP credentials are set at **ERP Automation > Credentials**.
5. Select the appropriate **Workflow Chain** (e.g., "ARAMCO FC Repair: Full ERP Flow").
6. Click **Execute** (or **Debug Chain** for step-by-step execution with pause/resume).
7. The system opens a browser, logs into D365, and executes all workflow steps automatically.

**Debug mode features:**
- Step-by-step execution with pause after each step
- Retry failed steps
- Jump to specific segments
- Dismiss D365 informational messages
- Batch execution for multiple jobs sharing one browser session

---

## 5. Forms & Data Entry Reference

| Form / Page | Location | Required Fields | Notes |
|-------------|----------|-----------------|-------|
| Work Order Create | Production > Work Orders > Create | Serial Number, Account | Auto-populates design info from serial |
| Cutter Evaluation Grid | WO > Evaluations > (eval) > Edit | At least one cell marked | Grid is blade x position |
| Pocket Evaluation Grid | WO > Evaluations > (eval) > Edit | At least one cell marked | V auto-pairs with adjacent pocket |
| Die Check Report | WO > Die Check > Create | Materials (cleaner, penetrant, developer), Grid findings | Stage auto-detected from evaluation type |
| Router Step Completion | WO > Router Sheet > (step) > Complete | Checklist, Parameters, Photos, Evaluation (if required) | Blocked until requirements met |
| LPT Pressure Test | WO > Evaluations > (eval with LPT section) | Materials, surface temp, dwell times, result | 2 rounds: Before Brazing / After Tip Grinding |
| Thread Inspection | WO > Evaluations > (eval with Thread section) | 5 checkpoints (OK/Not OK), pin height, repair decision | 2 rounds: Before / After Repair |
| ERP Job Data Upload | ERP Automation > Job Data > Upload | Job Card Excel file | Parser extracts all fields |

---

## 6. Reports Available to You

| Report | Location | Description |
|--------|----------|-------------|
| Work Order List | Production > Work Orders | All WOs with status, account, date filters |
| Floor Board | Production > Floor Board | Real-time view of active production |
| Router Sheet | WO Detail > Router Sheet tab | Full process step status and timing |
| Evaluation Print | WO Detail > Evaluations > (eval) > Print | Printable evaluation with grid, checklist, signatures |
| Die Check Report | WO Detail > Die Check > (report) > Print | QAS/1004-1 format with materials, findings, decisions |
| Bit Data Sheet | Drill Bit Detail > Data Sheet | Printable spec sheet with QR code |
| Cutter Inventory | Logistics > PDC Cutters > Cutter Inventory | Stock by type with variant breakdown |
| Cutter Inventory Export | Cutter Inventory > Export Excel | Excel file with full stock data |
| Receiving Inspection | Drill Bit > Receiving Inspection > Print | QAS/005-1 format checklist and grid |
| Release Paper | WO Detail > Release button | Printable release document with route and QR |

---

## 7. Notifications & Alerts

**What you receive:**

| Notification | Priority | Trigger |
|-------------|----------|---------|
| WO approved for production | HIGH | Operations Manager approves a WO |
| Step requires your attention | NORMAL | Operator encounters a hold or quality issue |
| Evaluation completed | HIGH | A team member finishes an evaluation you manage |
| Quality decision needed | HIGH | Die check flags cutters as "Waiting Quality Decision" |
| Hold placed on WO | HIGH | Operator or QC places a quality hold |
| All router steps complete | HIGH | Full route for a WO is done |
| WO cancelled | URGENT | A work order is cancelled |

**What you trigger:**
- Completing an evaluation sends notifications to the Operations Manager and QC.
- Starting a work order step does not generate a notification.
- Completing the final step sends a notification to all managers.
- Setting a cutter to "Waiting Quality Decision" in a die check sends a notification to the quality team.

---

## 8. Approvals & Sign-offs

| Action | When | Your Authority | What Happens |
|--------|------|---------------|--------------|
| Release Work Order | WO at Pending status | Click "Mark as Released" | WO moves to Released, awaits manager approval |
| Complete Evaluation | All grid cells and decision filled | Click "Save & Complete" | Evaluation locked, notification sent |
| Complete Router Step | Requirements met (checklist, photos, eval) | Click "Complete" or scan QR | Step marked done, next step available |
| Skip Router Step | Step not applicable | Click "Skip" with reason | Step marked Skipped, reason recorded |
| Die Check Decision | Cutter flagged during die check | Set decision per cutter | "Waiting QD" triggers quality notification |

**Print and Sign:** Evaluations and Die Check reports can be printed from their respective pages. The printed format includes signature areas for the Supervisor and QC Inspector. Physical signatures complement the digital audit trail.

---

## 9. Frequently Asked Questions

**Q1: How do I know which cutters are available before starting a repair?**
A: Go to **Logistics > PDC Cutters > Cutter Inventory**. Filter by the cutter MAT number or size from the BOM. Check the "Total" and variant columns to see available stock.

**Q2: Can I edit an evaluation after it has been completed?**
A: Completed evaluations are locked. To make changes, you must **reopen** the evaluation (if no active WO is in progress and the bit is still in the evaluation area). This is gated by the system to prevent changes to data that production has already acted upon.

**Q3: What do the cutter symbols mean?**
A: O = OK, X = Replace, R = Rotate, S = Spin, L = Lost, C = Cracked, H = Chipped, M = Misaligned. For die checks: O = OK, C = Cracked, H = Chipped, Y = Porosity.

**Q4: A router step requires photos but I cannot complete it. What is missing?**
A: The step has a minimum photo requirement based on the process type. Check the requirement indicator on the step. For ADG (Auto Documentation Guide) mode, you need 3 photos per blade plus Top and Side shots. Upload photos in the Photos section of the step or the WO detail.

**Q5: How does the ERP Automation know which route to use?**
A: The Route Selector automatically chooses based on the drill bit's size, port configuration, and repair modifiers (USR, hardfacing, crush & shear). You can review and override the route on the job data detail page.

**Q6: Can I create a BOM from a Halliburton PDF?**
A: Yes. Go to **Technical > Cutter Map**, select the design, upload the PDF. The system extracts all cutter data, blade layouts, and group shapes. Review the data, then click "Create BOM" to save it.

**Q7: What is the difference between a Receiving Inspection and a PDC Evaluation?**
A: A Receiving Inspection (QAS/005-1) is performed when a drill bit first arrives at the facility. It checks the bit's overall condition. A PDC Evaluation is performed during production to assess each individual cutter and make repair/replace decisions.

**Q8: How do I re-run a failed ERP automation step?**
A: In Debug mode, when a step fails, the system pauses and shows the error. You can click **Retry Step** to try again, or **Skip** to move past it. For D365 informational messages (not errors), click **Dismiss & Continue**.

**Q9: Can I reorder router steps?**
A: Yes, but only staff-level users (supervisors) can do this. Use the step reorder function on the router sheet. Pending steps can be moved; completed steps cannot.

**Q10: Where is the printed evaluation report?**
A: On the evaluation edit page, click the **Print** link. The print layout follows the QAS standard format (e.g., QAS/1004-1 for die checks, QAS/005-1 for receiving inspections). Use your browser's print function (Ctrl+P) to send it to a printer or save as PDF.

---

## 10. Glossary

| Term | Definition |
|------|-----------|
| **PDC** | Polycrystalline Diamond Compact — the cutting elements on a Fixed Cutter drill bit. |
| **Router Sheet** | The ordered production route: a list of all process steps a drill bit must go through. |
| **Evaluation** | A formal inspection of cutter condition at a specific production stage. There are 9 types (Receiving, ARDT, Engineer, QC, Die Check, Final Die Check, Final QC, Final Inspection, Rework). |
| **Die Check** | A Liquid Penetrant Test (LPT) inspection of cutters for cracks, chips, or porosity. |
| **BOM (Bill of Materials)** | The exact list of cutters, by MAT number and quantity, required for a specific drill bit design. |
| **Cutter Map** | The tool that extracts cutter data from Halliburton PDFs and creates BOMs. |
| **MAT Number** | Material number — a unique identifier for a cutter type or design (e.g., `1283567M1`). |
| **HDBS** | Halliburton Drill Bit System — the classification code for a drill bit design type. |
| **SMI** | Standard Material Identifier — a specific configuration within an HDBS type. |
| **Variant** | A stock category for cutters: New Purchased, Reclaimed, Client-provided, Retrofit, Ground, etc. |
| **ERP Automation** | The module that automates data entry into D365 (Dynamics 365) by replaying recorded browser actions. |
| **Workflow Chain** | A sequence of workflows that run together (e.g., Login, Create Item, BOM, Route, Journal). |
| **ADG** | Auto Documentation Guide — a standard photo sequence: 3 photos per blade + Top + Side. |
| **LPT** | Liquid Penetrant Test — the die check inspection method using cleaner, penetrant, and developer. |
| **QR Scan** | Scanning a printed QR code on the Release Paper to start or complete a router step via the Operator Portal. |
| **Backload** | Receiving drill bits back from the field for repair. |
| **Floor Board** | Real-time visual display of all active production work orders. |
