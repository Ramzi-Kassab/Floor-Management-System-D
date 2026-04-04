# Quality Control Inspector — User Manual

**System:** ARDT Floor Management System
**Version:** Draft 1.0
**Date:** April 4, 2026
**Audience:** Quality Control Inspector — performs quality inspections, cutter evaluations, die checks, LPT pressure tests, thread inspections, and receiving inspections throughout the drill bit lifecycle.

---

## 1. Your Role in the System

As a Quality Control Inspector, you are the gatekeeper of product quality at every stage of the drill bit lifecycle. From the moment a bit arrives at the facility (receiving inspection) through every production step (evaluations, die checks, thread inspections) to the final sign-off before dispatch, your assessments and decisions determine whether a bit proceeds, gets reworked, or is rejected.

The ARDT Floor Management System provides you with structured digital forms for all quality documents, replacing paper-based records with traceable, auditable electronic records. You work with nine types of evaluations, each tailored to a specific stage of production: Receiving, ARDT, Engineer (Tech Rep), QC, Die Check, Final Die Check, Final QC, Final Inspection, and Rework. Each evaluation type automatically includes the relevant sections (cutter grid, pocket evaluation, die check, LPT, thread inspection) based on its purpose.

Your quality records feed directly into the work order lifecycle. A step that requires your evaluation cannot be completed by the operator until you have finished and marked your form complete. Your decisions on individual cutters (OK, Replace, Rotate, Spin) drive the production team's actions. Your receiving inspection result (Accepted, Rejected, Conditional) determines whether a bit enters the production pipeline or is held for further review.

---

## 2. Logging In

1. Open your web browser and go to **http://localhost:8001**.
2. Enter your **Username** and **Password**.
3. Click **Log In**.
4. Your primary work areas are in the sidebar under **Quality** and **Receiving** sections, as well as directly from work order detail pages.

---

## 3. Your Workbench

After logging in, your key areas are:

- **Notification Bell** (top navigation) — shows alerts for evaluations needing review, "Waiting Quality Decision" items from die checks, and work orders sent to QC.
- **Action Center** (Sidebar > Notifications > Actions) — your pending quality actions and tasks.
- **Receiving section** (sidebar, teal icon):
  - **Dashboard** — overview of incoming batches, pending inspections, recently inspected bits.
  - **Inspections** — full list of all receiving inspections with status filters.
- **Work Order pages** — access evaluations from any work order detail page under the Evaluations tab.
- **Router Sheet** — QC-gated steps appear in the router sheet where your inspection is required before the step can be completed.

---

## 4. Core Workflows

### 4.1 Performing a Receiving Inspection (QAS/005-1)

This is your first interaction with every incoming drill bit. The receiving inspection determines whether the bit is accepted for production.

1. Go to **Receiving > Inspections** in the sidebar, or navigate from the drill bit detail page.
2. Click **Create Inspection** for the bit (or find it in the pending inspections list on the Receiving Dashboard).
3. The Receiving Inspection form opens with the header pre-filled:
   - **Report Number**: Auto-generated (RI-0001, RI-0002, etc.).
   - **Serial Number, Size, Type, Design MAT, System MAT**: Pre-filled from the drill bit record.
   - **Inspection Date**: Defaults to today.
   - **Date of Receipt**: Auto-filled from the bit's received date if available.

4. **Section 1 — Inspection Details**: Verify the header information. Edit the Inspection Date and Date of Receipt if needed.

5. **Section 2 — Visual Inspection Checklist**: Go through each checkpoint and mark it as **OK**, **Not OK**, or **N/A**. If "Not OK," enter the reason in the Reason field. Common checkpoints include:
   - Body condition (no visible damage)
   - Cutter condition (no obvious breakage)
   - Connection threads (no stripped or damaged threads)
   - Serial number legibility
   - Nozzle condition

   You can also upload file attachments (Q-Note, Inspection Report, Photo, Damage Report, etc.) using the attachment upload area.

6. **Section 3 — Pocket Evaluation Grid** (if BOM data is available):
   The grid shows all pocket positions arranged by blade. For each pocket, tap the cell to open a positioned modal and select one or more symbols:
   - **D** = Default / No Change
   - **V** = Fin Build Up (auto-pairs with adjacent pocket)
   - **P** = Pocket Build Up
   - **F** = Fill
   - **I** = Impact Arrestor

   **V Auto-Pairing Rule:** When you mark a pocket as V, the system automatically adds V to the adjacent pocket (minimum 2 adjacent V's required). If V is on the last pocket in a row, it converts to P (Pocket Build Up).

7. **Section 4 — Cutter Evaluation Grid** (if BOM data is available):
   The grid shows all cutter positions by blade. The Cutter Config Table above the grid lists each cutter type with its color code. For each cutter position, tap the cell and select one or more findings:
   - **O** = OK
   - **X** = Replace
   - **R** = Rotate
   - **S** = Spin
   - **L** = Lost
   - **C** = Cracked
   - **H** = Chipped
   - **M** = Misaligned

   **O is exclusive** — if you mark a cutter as OK, no other findings can be applied to that cutter.

8. **Section 5 — Decision**:
   - Set the **Result**: Accepted, Rejected, Conditional, or Pending.
   - Enter any **Remarks** about the overall inspection.
   - The inspector name is auto-filled with your login name.

9. **Save Options**:
   - **Save Draft** — saves your progress without completing the inspection. You can return later.
   - **Save & Complete** — saves and marks the inspection as complete. The bit's status updates automatically:
     - Accepted or Conditional: bit moves to **In Evaluation** status at the Evaluation Area.
     - Rejected: bit receives **Rejected** status and remains in the Receiving Area.

10. **Print**: Click the Print button to generate the QAS/005-1 formatted report for physical filing.

### 4.2 Completing a Cutter Evaluation (QAS/1001-1)

Cutter evaluations are performed at multiple stages during production. The system supports nine evaluation types, each with different default sections enabled.

1. Navigate to the work order detail page and click the **Evaluations** tab.
2. Click the evaluation entry to edit, or click the action link on the router sheet step to create a new evaluation.
3. The evaluation type determines which sections are shown:
   - **PDC Evaluation**: Checklist, Cutter Grid, Pocket Evaluation, and optionally Die Check.
   - **QC Evaluation**: Checklist and Cutter Grid.
   - **Final Inspection**: Checklist, Cutter Grid, Pocket Evaluation, and Thread Inspection.
   - **Die Check**: Die Check section only (separate dedicated page).
   - **Rework**: Checklist and Cutter Grid.

4. **Header Fields** (read-only): WO Number, Serial Number, Size, Material Number, Type, From location, Date Received, Contract Number.

5. **Cutter Evaluation Grid**: The blade-by-position matrix. For each cutter:
   - Type a single letter in the cell: **O** (OK), **X** (Replace), **R** (Rotate), **S** (Spin), **F** (Fill), **L** (Lost), **P** (Pocket Build Up), **I** (Impact Arrestor), **V** (Fin Build Up).
   - The cell changes color to indicate the action.
   - The totals row at the bottom shows a count of each action code across all blades.

6. **Cutter State History**: If previous evaluations exist for this work order, each cell with prior history shows an amber bottom border. Hover to see the chain of actions across evaluations (e.g., "Prior: Receiving Evaluation: R then ARDT Evaluation: X").

7. **Section Toggles**: Use the **Sections** dropdown button in the toolbar to enable or disable sections (Checklist, Cutter Grid, Pocket Eval, Die Check, LPT, Thread Inspection). This allows you to customize the form for the specific inspection being performed.

8. **Saving**:
   - **Save** — saves your progress as a draft.
   - **Save & Complete** — marks the evaluation as finished. This unlocks the linked router step for the operator to complete.
   - **Reopen** — if you need to make corrections after completing, click Reopen. Note: reopening is blocked if an active work order depends on this evaluation.

### 4.3 Performing a Die Check (QAS/1004-1)

Die checks are performed before brazing and after repair to detect surface defects using Fluorescent Penetrant Inspection.

1. From the router sheet, click the die check action link, or from the evaluation page, click **Die Check Report**.
2. The Die Check form has six sections:

   **Section 1 — Header**: WO number, serial, size, design, and stage (Before Brazing / After Repair / Other). The stage is auto-detected based on the evaluation context.

   **Section 2 — Materials Used**: Record three LPT materials:
   - **Cleaner**: Product name, batch/lot number, expiry date.
   - **Penetrant**: Product name, batch/lot number, expiry date.
   - **Developer**: Product name, batch/lot number, expiry date.
   You can scan material barcodes using the built-in QR/barcode scanner or type values manually.

   **Section 3 — Cutter Findings Grid**: For each cutter position (blade by position), tap the cell and select findings:
   - **O** = OK / No Indication
   - **C** = Cracked
   - **H** = Chipped
   - **Y** = Porosity

   O is exclusive with all other findings. You can select multiple non-OK findings (e.g., C + H for a cutter that is both cracked and chipped).

   **Section 4 — Decisions Table**: Automatically populated from all non-OK findings. For each flagged cutter:
   - Select a decision: **Accepted**, **Rotate**, **Spin**, **Replace**, or **Waiting Quality Decision**.
   - Add per-cutter remarks.
   - Attach a close-up photo if needed.

   **Section 5 — Result & Remarks**: An auto-generated summary of all findings and decisions. You can edit the text. Set the overall Result (Accepted, Rejected, Conditional). A **Copy** button copies the summary to clipboard for pasting into emails or reports.

   **Section 6 — Photos**: Upload FPI result photos using the photo module.

3. **Save** or **Save & Complete**. If any cutter has "Waiting Quality Decision," the system sends a HIGH priority notification to all users.

4. **Print**: Generates the QAS/1004-1 formatted report with all materials, findings, decisions, and signature areas.

### 4.4 Reviewing LPT Pressure Test Results

The LPT (Liquid Penetrant Test) section appears within evaluation forms when the **LPT** section is enabled.

1. Open the evaluation form and scroll to the **LPT Pressure Test** section.
2. The form has two rounds:
   - **Round 1 — Before Brazing**: Materials used (Cleaner, Penetrant, Developer — each with product name, batch number, expiry), parameters (surface temperature, light intensity, penetrant dwell time, developer dwell time), operator name, result (Accept / Reject / Conditional), and disposition/remarks.
   - **Round 2 — After Tip Grinding**: Same fields as Round 1 for the post-repair inspection.
3. Fill in all fields for each applicable round.
4. The data is saved as part of the overall evaluation when you click Save.

### 4.5 Reviewing Thread Inspections

The Thread Inspection section appears within evaluation forms when the **Thread Inspection** section is enabled.

1. Open the evaluation form and scroll to the **API Thread Inspection** section.
2. The form has two rounds:
   - **Round 1 — Evaluation Before Repair**
   - **Round 2 — Evaluation After Repair**
3. Each round has five checkpoints:
   - **Pin Face** — OK or Not OK, with remarks.
   - **Thread** — OK or Not OK, with remarks.
   - **Pitch Gauge** — OK or Not OK, with remarks.
   - **Mud Seal** — OK or Not OK, with remarks.
   - **Other Observation** — OK or Not OK, with remarks.
4. Additional fields per round: pin height measurement, thread repair decision (Not Required / Required), repair operation type (Repair/Brush or USR), and inspector remarks.
5. Save as part of the overall evaluation.

### 4.6 Marking Evaluations Complete and Unlocking Steps

When you mark an evaluation as complete:
1. The linked router sheet step (if any) is unlocked — the operator can now mark that step as complete.
2. A HIGH priority notification is sent to the production team.
3. The evaluation status changes from Draft/In Progress to Completed.
4. The evaluation's completion date and your name are recorded permanently.

### 4.7 Version History and Audit Trail

Every time you save changes to a receiving inspection, the system records a version:
1. Scroll to the **Version History** section on the inspection form.
2. Each revision shows: revision number, time since creation, author, change summary, and which specific fields changed.
3. This provides a complete audit trail for ISO 9001 compliance.

---

## 5. Forms & Data Entry Reference

| Form / Page | Document Reference | Key Fields |
|---|---|---|
| Receiving Inspection | QAS/005-1 | Checklist (OK/Not OK/NA), Pocket eval grid, Cutter eval grid, Result, Attachments |
| Cutter Evaluation Matrix | QAS/1001-1 | Blade x position grid (O/X/R/S/F/L/P/I/V), Decision, Remarks |
| Die Check Report | QAS/1004-1 | Materials (3 chemicals), Cutter findings (O/C/H/Y), Decisions per cutter, Result |
| LPT Pressure Test | QAS/1004-1 | 2 rounds, Materials table, Surface temp, Dwell times, Result |
| Thread Inspection | API Standard | 2 rounds, 5 checkpoints (OK/Not OK), Pin height, Repair decision |
| Photo Upload | All forms | Camera, ADG guided, File upload, Fabric.js annotation editor |

---

## 6. Reports Available to You

| Report | Location | Description |
|---|---|---|
| Receiving Inspection List | Receiving > Inspections | All inspections with status, result, date filters |
| Receiving Dashboard | Receiving > Dashboard | Pending inspections, recently completed, BOM pending |
| Evaluation Print Report | Evaluation form > Print | Printable QAS/1001-1 formatted evaluation report |
| Die Check Print Report | Die Check form > Print | Printable QAS/1004-1 formatted die check with materials and findings |
| Bit Data Sheet | Drill Bit detail > Data Sheet | Complete bit specification sheet with BOM and work history |
| Work Order Evaluations | WO Detail > Evaluations tab | All evaluations for a specific work order |
| Version History | Receiving Inspection form | Complete revision audit trail for an inspection |

---

## 7. Notifications & Alerts

You will receive notifications for:

- **Sent to QC** (HIGH priority) — when an operator completes a production step and sends the bit to QC. This is your signal to begin inspection.
- **Waiting Quality Decision** (HIGH priority) — when a die check has cutter(s) with unresolved quality decisions needing your review.
- **Evaluation Completed** (HIGH priority) — confirmation when you or a colleague finishes an evaluation.
- **Work Order Status Change** — when a WO moves to QC Pending or is placed on hold.
- **All Router Steps Complete** (HIGH priority) — when all production steps are done and the bit is ready for final inspection.
- **GRN Posted** (URGENT priority) — when new inventory stock is received (relevant for cutter availability).

---

## 8. Approvals & Sign-offs

- **Receiving Inspection Result**: Your result (Accepted / Rejected / Conditional) directly controls the bit's status and production eligibility. This is a formal quality sign-off.
- **Evaluation Completion**: Marking an evaluation complete is your sign-off that the inspection was performed to standard. Your name and timestamp are permanently recorded.
- **Die Check Decisions**: Your per-cutter decisions (Accept, Replace, Rotate, etc.) are production directives. Operators must follow your decisions.
- **Reopen Authority**: You can reopen a completed evaluation for corrections, provided no downstream work order step depends on it in a locked state.
- **Print and Sign**: The printed QAS/005-1 and QAS/1004-1 reports include signature areas for your physical signature, providing a dual digital-plus-physical record.

---

## 9. Frequently Asked Questions

**Q: I need to change my evaluation after marking it complete. Can I reopen it?**
A: Yes, if no active work order step is locked waiting on that evaluation. Click the **Reopen** button on the evaluation form. If the button is grayed out and shows "Locked," it means a downstream step depends on it — contact your supervisor.

**Q: What is the difference between the 9 evaluation types?**
A: Each type corresponds to a production stage: RECEIVING (incoming inspection), ARDT (ARDT internal evaluation), ENGINEER (Tech Rep assessment), QC (quality control checkpoint), DIE_CHECK (FPI test), FINAL_DIE_CHECK (post-repair FPI), FINAL_QC (final quality check), FINAL_INSPECTION (complete final review), and REWORK (re-evaluation after rework). Each type enables different form sections by default.

**Q: A cutter shows an amber border in the evaluation grid. What does this mean?**
A: It means this cutter had findings in a previous evaluation for the same work order. Hover over the cell to see the chain of prior actions (e.g., "Prior: Receiving Evaluation: R then ARDT Evaluation: X"). This helps you track cumulative cutter condition.

**Q: I set a cutter to "Waiting Quality Decision" in the die check. What happens next?**
A: The system sends a HIGH priority notification to all users. The work order may be held until the decision is made. You or another QC inspector can return to the die check and update the decision when ready.

**Q: Can I attach files to a receiving inspection?**
A: Yes. In Section 2 of the receiving inspection form, use the attachment upload area. Supported file types include Q-Note, Inspection Report, Photo, Damage Report, and Other. You can upload PDFs, Excel files, images, and documents.

**Q: How do I print a receiving inspection report?**
A: Click the **Print** button in the top-right corner of the inspection form. The system generates a QAS/005-1 formatted report with the ARDT header, all checklist results, pocket and cutter evaluations (summarized), result, and signature areas.

**Q: I completed an inspection but the result was set to Pending. Can I complete it?**
A: No. The system requires you to set the result to Accepted, Rejected, or Conditional before completing. Change the result from the dropdown in Section 5 and then click Save & Complete.

**Q: What is the V auto-pairing rule in the pocket evaluation?**
A: V (Fin Build Up) requires at least two adjacent pockets to be marked V. When you mark one pocket as V, the system automatically marks the adjacent pocket as V. If V is applied to the last pocket in a row, it converts to P (Pocket Build Up) instead.

**Q: How do I access the die check from the router sheet?**
A: On the router sheet, the die check step has an action link. If a die check already exists, the link says "Edit"; if not, it says "Create." Tap the link to go directly to the die check form.

**Q: Where can I see all completed evaluations across all work orders?**
A: Each work order's detail page has an Evaluations tab showing all evaluations for that WO. For a broader view, the receiving inspection list at Receiving > Inspections shows all receiving inspections with filters.

---

## 10. Glossary

| Term | Definition |
|---|---|
| **Receiving Inspection** | The initial quality check performed on every incoming drill bit (QAS/005-1). |
| **Cutter Evaluation Matrix** | A blade-by-position grid used to assess the condition of every cutter on a drill bit. |
| **Die Check** | Fluorescent Penetrant Inspection (FPI) to detect surface cracks and porosity (QAS/1004-1). |
| **LPT** | Liquid Penetrant Test — the materials and process used in die checks. |
| **FPI** | Fluorescent Penetrant Inspection — synonymous with die check. |
| **Thread Inspection** | API standard inspection of the pin/box connection threads. |
| **O / X / R / S / L / C / H / M** | Cutter evaluation symbols: OK, Replace, Rotate, Spin, Lost, Cracked, Chipped, Misaligned. |
| **O / C / H / Y** | Die check finding symbols: OK, Cracked, Chipped, Porosity. |
| **D / V / P / F / I** | Pocket evaluation symbols: Default, Fin Build Up, Pocket Build Up, Fill, Impact Arrestor. |
| **Accepted / Rejected / Conditional** | The three possible outcomes of an inspection. Conditional means accepted with noted issues. |
| **Router Sheet** | The full sequence of production steps for a work order. |
| **QC Gate** | A step in the router sheet that requires QC sign-off before the operator can proceed. |
| **ADG** | Automated Data Gathering — guided photo capture sequence (blade by blade). |
| **Version History** | The revision audit trail for a receiving inspection, showing all changes made and by whom. |
| **NCR** | Non-Conformance Report — referenced when quality issues are found. |
| **Section Toggles** | Controls on the evaluation form to enable or disable specific sections (Checklist, Grid, LPT, etc.). |
