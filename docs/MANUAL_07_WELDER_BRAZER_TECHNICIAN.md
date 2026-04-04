# Welder / Brazer Technician — User Manual

**System:** ARDT Floor Management System
**Version:** Draft 1.0
**Date:** April 4, 2026
**Audience:** Welder / Brazer Technician — specialist operator focused on brazing PDC cutters onto drill bit bodies, performing sub-arc welding, hardfacing, and TIG welding operations.

---

## 1. Your Role in the System

As a Welder or Brazer Technician, you perform some of the most critical and precise operations in the drill bit manufacturing and repair process. Brazing attaches PDC cutters to the bit body, sub-arc welding joins the upper and lower assemblies, hardfacing applies wear-resistant material to the bit's gauge and shoulder areas, and TIG welding handles fine detail repairs. The quality of your work directly determines whether a bit will survive downhole conditions.

In the ARDT Floor Management System, you use the same **Operator Portal** as other machine operators. Your steps appear in the router sheet alongside all other production steps. However, your steps often carry additional requirements: specific material checklists (brazing alloys, fluxes, hardfacing wire), temperature parameters, and mandatory quality inspections (die checks, LPT tests) that must be completed before your brazing step can be marked complete.

This manual focuses on the brazing-specific aspects of the system. For general Operator Portal navigation (QR scanning, starting and completing steps, uploading photos), refer to Manual 06 — Machine Operator, which covers those common features in detail. This manual adds the brazing-specific procedures, checklists, and linked quality forms that are unique to your work.

---

## 2. Logging In

1. Open the web browser on your workstation or tablet and go to **http://localhost:8001**.
2. Enter your **Username** and **Password**.
3. Click **Log In**.
4. Navigate to your Operator Portal: click **Production > Operator Portal** in the sidebar, or go directly to **http://localhost:8001/work-orders/operator/**.

**Tip:** Set the Operator Portal as your browser home page for instant access when you start your shift.

---

## 3. Your Workbench

Your workbench is the **Operator Portal**, identical in layout to what other operators see:

- **Scan Job QR Code** button — scan the QR on a work order to jump to your brazing step.
- **My Active Steps** — any brazing or welding steps you have started. These appear with a green pulsing dot if in progress, or an amber dot if paused.
- **My Work Orders** — work orders assigned to you. These typically have brazing or welding as the current or upcoming step.
- **All Active Work Orders** — the complete floor view.

When your brazing step is the current step in a work order, it will appear highlighted in the router sheet. Steps before yours (e.g., Debraze, Machine) must be completed before your step becomes available.

---

## 4. Core Workflows

### 4.1 Starting a Brazing Step

1. Scan the work order QR code or find your step in My Active Steps.
2. The Step View page opens. Confirm the identity bar shows the correct WO number, serial number, and bit size.
3. **Before starting**, verify:
   - The previous steps (Debraze, Machine, etc.) show as Completed in the router sheet.
   - The bit is physically at the correct workstation.
4. Tap the green **START STEP** button. The timer begins.

### 4.2 Working Through Brazing-Specific Checklists

Many brazing and welding steps include built-in checklists that you must complete. These appear in the step detail and may include items such as:

- Brazing alloy type and batch number verified
- Flux applied and coverage confirmed
- Oven temperature within specification
- Cutter placement verified against BOM layout
- Induction coil positioning confirmed
- Personal protective equipment (PPE) in use

For each checklist item, mark it as completed when you have verified the condition. You cannot mark the step complete until all required checklist items are checked.

### 4.3 Entering Process Parameters

Some brazing and welding steps require you to record process parameters. These appear as input fields in the step detail:

- **Brazing temperature** — the peak temperature reached during brazing (in degrees Celsius).
- **Hold time** — how long the brazing temperature was maintained.
- **Flux type and batch** — the specific flux product used.
- **Alloy type** — the brazing alloy specification.
- **Preheat temperature** — for welding operations.
- **Wire feed speed** — for sub-arc and hardfacing.
- **Voltage and amperage** — for welding operations.

Enter each value as requested. These values become part of the permanent quality record for the drill bit.

### 4.4 Completing a Die Check After Brazing

After brazing PDC cutters, a die check (Fluorescent Penetrant Inspection / FPI) is typically required. The die check verifies that no cracks, porosity, or defects were introduced during brazing.

1. The die check step follows your brazing step in the router sheet. When you reach it (or if it is linked to your brazing step), tap the **Die Check Report** link in the Quality Forms panel.
2. The Die Check form opens with six sections:
   - **Section 1 — Header**: Pre-filled with WO number, serial number, size, design, and the stage (Before Brazing or After Repair).
   - **Section 2 — Materials Used**: Record the Cleaner, Penetrant, and Developer products. Each needs: product name, batch/lot number, and expiry date. You can use the QR/barcode scanner to scan material labels directly.
   - **Section 3 — Cutter Grid**: A blade-by-position grid identical to the evaluation matrix. For each cutter position, tap the cell and select a finding:
     - **O** = OK / No Indication
     - **C** = Cracked
     - **H** = Chipped
     - **Y** = Porosity
   - **Section 4 — Decisions Table**: Automatically populated from any non-OK findings. For each flagged cutter, select a decision: Accepted, Rotate, Spin, Replace, or Waiting Quality Decision. Add per-cutter remarks and attach photos if needed.
   - **Section 5 — Result & Remarks**: An auto-generated summary of findings. You can edit the text. The overall result (Accepted, Rejected, or Conditional) is set here.
   - **Section 6 — Photos**: Upload photos of the FPI results using the photo module (ADG guided, camera, or file upload).
3. Click **Save** to save your progress, or **Save & Complete** when finished.
4. Return to the die check step and mark it complete.

**Important:** If any cutter has a "Waiting Quality Decision" status, the system sends a notification to QC personnel. The step may be held until they respond.

### 4.5 Sub-Arc Welding Steps

Sub-arc welding joins the upper connection (pin or box) to the lower bit body. Your step will include:

1. Parameter entry: voltage, amperage, wire feed speed, preheat temperature, interpass temperature.
2. A checklist for fit-up verification, alignment, and tack welds.
3. After welding, a thread inspection may be required (a separate step). The Thread Inspection form has two rounds (Before Repair and After Repair), each with five checkpoints: Pin Face, Thread, Pitch Gauge, Mud Seal, and Other Observation.

### 4.6 Hardfacing Steps

Hardfacing applies wear-resistant material (tungsten carbide or similar) to the gauge and shoulder of the bit. Your step may include:

1. Parameter entry: hardfacing material type, batch number, application temperature, coverage area.
2. A checklist for surface preparation, material compatibility, and visual inspection of the applied hardfacing.
3. A die check after hardfacing to verify no cracking occurred.

### 4.7 Uploading Work Photos

For brazing operations, photos are often required at multiple stages:

1. **Before brazing** — the prepared body with cutters dry-fitted.
2. **After brazing** — the completed braze joints.
3. **Die check results** — FPI images showing fluorescent indications (or lack thereof).

Use the ADG guided sequence in the photo module for systematic blade-by-blade documentation:
- B1-Ph1, B1-Ph2, B1-Ph3 (3 photos per blade)
- Top view, Side view
- Extra slots for close-up details

### 4.8 Pausing, Resuming, and Completing

These work exactly as described in Manual 06:
- **PAUSE** stops the timer during breaks or waiting periods.
- **RESUME** restarts the timer.
- **MARK COMPLETE** records the finish time and advances the work order.

You cannot complete a brazing step if a linked die check or evaluation form has not been completed. A warning will appear in the confirmation modal.

---

## 5. Forms & Data Entry Reference

| Form / Page | How to Access | Key Fields |
|---|---|---|
| Step View (Brazing) | QR scan or Operator Portal | START, PAUSE, COMPLETE, checklist items, parameters |
| Die Check Report (QAS/1004-1) | Step View > Quality Forms > Die Check | Materials (cleaner/penetrant/developer), cutter grid (O/C/H/Y), decisions, result |
| Thread Inspection | Step View > Quality Forms > Thread Inspection | 2 rounds, 5 checkpoints (Pin Face, Thread, Pitch Gauge, Mud Seal, Other), pin height, repair decision |
| LPT Pressure Test (QAS/1004-1) | Step View > Quality Forms > LPT Report | 2 rounds (Before/After), materials table, surface temp, dwell times, result |
| Photo Upload | Inside Die Check or Evaluation forms | Camera, ADG guided, file upload, annotation editor |
| Remarks | Bottom of Step View | Free text, saved to work order record |

---

## 6. Reports Available to You

| Report | Location | Description |
|---|---|---|
| My Active Steps | Operator Portal home | Brazing/welding steps you have started |
| My Work Orders | Operator Portal home | WOs assigned to you |
| Router Sheet | Tap any WO card | Full step sequence showing your brazing step in context |
| Die Check Print | Die Check form > Print button | Printable QAS/1004-1 report with materials, findings, decisions, and signatures |
| Full Job Card | Link at bottom of Step View | Complete WO detail with all evaluations and history |

---

## 7. Notifications & Alerts

You will receive notifications for:

- **Step available** — when the preceding step (e.g., machining) is completed and your brazing step is next.
- **Quality hold** — if QC places a hold on the work order after reviewing your die check results.
- **Waiting Quality Decision resolved** — when QC makes a decision on a flagged cutter from your die check.
- **Work order approved** — when a new WO enters the Active state and production can begin.
- **Step resumed by another operator** — if someone else resumes a step you had paused.

A beep sound plays when a new notification arrives, and the bell icon badge updates in real time.

---

## 8. Approvals & Sign-offs

- **Die Check Report**: When you save and complete a die check, your name and timestamp are recorded as the inspector. This serves as your sign-off on the FPI results.
- **LPT Report**: The pressure test form records the LPT Operator name and the result (Accept / Reject / Conditional). Your entry is the official test record.
- **Thread Inspection**: Your checkpoints and repair decisions are recorded with your identity.
- **Step Completion**: Completing a step records you as the operator who performed the work. This cannot be changed after the fact.
- **Material Traceability**: When you enter material batch numbers and expiry dates in the die check or LPT form, these become part of the permanent traceability record.

If a die check reveals a defect that requires a quality decision, you set the cutter to "Waiting Quality Decision." A QC Inspector then reviews and makes the final call.

---

## 9. Frequently Asked Questions

**Q: The die check form is locked and says "Start the step first." What do I do?**
A: You must tap the **Start Step** button on the step view page before the die check form becomes editable. This ensures the timer is running and the step is officially in progress.

**Q: I scanned a material barcode but the field did not fill in. Why?**
A: The barcode scanner works with standard product barcodes. If the barcode format is not recognized, type the batch number manually into the field. Ensure your browser has camera permission enabled.

**Q: I found a cracked cutter during the die check. What happens next?**
A: Mark the cutter as **C** (Cracked) in the grid. The cutter will appear in the Decisions Table. Select a decision: if you are unsure, choose "Waiting Quality Decision." The system will notify QC personnel. Do not close the die check until QC responds, or save as draft and return later.

**Q: Can I redo a die check if I made an error?**
A: If the die check has not been marked complete, you can edit it freely. If it has been completed, contact your supervisor — they can reopen it from the evaluation list.

**Q: What is the difference between the die check stage "Before Brazing" and "After Repair"?**
A: "Before Brazing" is performed on the debrazed body before new cutters are attached, checking the body for existing defects. "After Repair" is performed after all brazing, welding, and hardfacing work is done, checking the completed assembly for new defects.

**Q: I paused my brazing step but the oven needs to stay running. Does the pause affect the bit?**
A: Pausing the step only stops the system timer — it has no effect on physical equipment. Use pause when you personally are not actively working on the step (e.g., waiting for the oven to reach temperature).

**Q: Where do I see my completed die checks from previous shifts?**
A: Go to the work order detail page (Full Job Card link at the bottom of any step view). The Evaluations tab shows all evaluations and die checks for that work order.

**Q: The system says I need to upload more photos before completing the step. How many are required?**
A: The required count depends on the process. For a 6-blade bit, ADG requires 18 blade photos (3 per blade) plus top and side views — 20 minimum. The photo section shows a progress counter (e.g., "5 of 21 photos taken").

---

## 10. Glossary

| Term | Definition |
|---|---|
| **Brazing** | The process of attaching PDC cutters to the drill bit body using a brazing alloy at high temperature. |
| **Sub-Arc Welding** | An arc welding process used to join the upper connection to the lower bit body. |
| **Hardfacing** | Application of wear-resistant material (tungsten carbide) to the bit's gauge and shoulder surfaces. |
| **TIG Welding** | Tungsten Inert Gas welding — fine detail welding for repairs and connections. |
| **Die Check** | Fluorescent Penetrant Inspection (FPI) — a non-destructive test to find surface cracks and porosity. |
| **LPT** | Liquid Penetrant Test — the materials-based inspection process used in die checks (QAS/1004-1). |
| **FPI** | Fluorescent Penetrant Inspection — another name for the die check process. |
| **QAS/1004-1** | The ARDT quality procedure document number for die check and LPT reporting. |
| **Cutter Grid** | The blade-by-position matrix in the die check form where you record findings for each cutter. |
| **O / C / H / Y** | Die check symbols: OK, Cracked, Chipped, Porosity. |
| **Router Sheet** | The complete sequence of production steps for a work order. |
| **PDC Cutter** | Polycrystalline Diamond Compact cutter — the cutting element brazed onto the drill bit. |
| **ADG** | Automated Data Gathering — the guided photo capture sequence (blade by blade, top, side). |
| **Operator Portal** | The mobile-friendly interface for floor operators. |
| **Step** | A single operation in the production route (e.g., Braze, Sub-Arc Weld, Die Check). |
| **Batch Number** | The manufacturer's lot/batch identifier for consumable materials (flux, alloy, penetrant). |
