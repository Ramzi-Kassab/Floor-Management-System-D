# Machine Operator / CNC Technician — User Manual

**System:** ARDT Floor Management System
**Version:** Draft 1.0
**Date:** April 4, 2026
**Audience:** Machine Operator / CNC Technician — floor operator who performs physical manufacturing and repair work on drill bits, including machining, grinding, debrazing, and assembly operations.

---

## 1. Your Role in the System

As a Machine Operator, you are the hands-on workforce that transforms a drill bit from a work order into a finished product. Your primary interaction with the ARDT Floor Management System happens through the **Operator Portal** — a mobile-friendly interface designed specifically for use on tablets and phones on the shop floor. You do not need to navigate complex menus or fill in lengthy administrative forms.

Your job in the system is to **start production steps, record your progress, and mark steps complete** as you work through the router sheet (the sequence of operations) for each work order. The system tracks your elapsed time on each step, records who performed the work, and ensures that all required quality forms and photos are completed before a step can be closed.

You may also be asked to upload photos of your work using the built-in camera tool, enter process parameters (such as machine settings or measurements), and complete checklists for specific operations. All of this feeds into the quality record for the drill bit and provides full traceability from receipt to dispatch.

---

## 2. Logging In

1. On your tablet or shop floor workstation, open the web browser and go to **http://localhost:8001**.
2. Enter your **Username** and **Password**.
3. Click **Log In**.
4. You will see the main system page. To go directly to your Operator Portal, click **Production > Operator Portal** in the sidebar, or navigate to **http://localhost:8001/work-orders/operator/**.

**Tip:** Bookmark the Operator Portal URL on your device for quick access.

---

## 3. Your Workbench

The **Operator Portal** is your home screen. It is designed for touch screens and shows the following sections:

- **Header Banner** — displays your name and a large **Scan Job QR Code** button. This is the fastest way to find your next step.

- **My Active Steps** — any production steps you have already started but not yet completed. Each card shows the step name, work order number, serial number, and step number. Tap a card to go directly to that step.

- **My Work Orders** — work orders assigned to you. Each card shows the WO number, serial number, work type, account, priority, and due date (highlighted in red if overdue). Tap a card to see the full router sheet.

- **All Active Work Orders** — every work order currently on the shop floor. Useful when picking up unassigned work.

- **Quick Access** — four shortcut tiles: Production Planner, Drill Bit Inventory, Location Transfers, and All Work Orders.

The page refreshes automatically every 5 minutes to keep information current.

---

## 4. Core Workflows

### 4.1 Finding Your Next Step with QR Scan

1. From the Operator Portal, tap the large **Scan Job QR Code** button.
2. The QR Scanner page opens. Tap **Start Camera** to activate your device's camera.
3. Point the camera at the QR code on the work order paper or drill bit label.
4. The system reads the QR code and redirects you to the correct step automatically.

The system understands three QR code formats:
- **WO:WO-2026-0042:STEP:3** — takes you directly to Step 3 of that work order.
- **WO:WO-2026-0042** — takes you to the next pending step for that work order.
- **BIT:12345678** — finds the active work order for that serial number and shows its next step.

**If the camera is not available** (for example, on a desktop computer), you can type the work order number or serial number in the manual entry field below the camera and press **Go to Step**.

### 4.2 Starting a Production Step

1. Navigate to the step (via QR scan, My Active Steps card, or router sheet).
2. The Step View page shows:
   - **Identity Bar** (dark blue) — WO number, serial number, size, and work type.
   - **Step Name Panel** — the step number, description, and current status (Pending, In Progress, Paused, or Completed).
   - **Timer Panel** — a large elapsed time display (HH:MM:SS).
   - **Action Buttons** — the main controls for this step.
3. Tap the green **START STEP** button.
4. The timer begins counting. The step status changes to **In Progress**.

**Important:** You must start the step before you can fill in any linked quality forms. If the step requires a form (such as a die check or evaluation), the form will be locked until the step is started.

### 4.3 Pausing and Resuming a Step

If you need to take a break or wait for materials:
1. Tap the yellow **PAUSE** button.
2. The timer stops. The status changes to **Paused**.
3. When ready to continue, tap the green **RESUME** button. The timer resumes from where it left off.

Paused time is not counted in the active duration.

### 4.4 Completing a Step

1. Ensure all required tasks are finished:
   - If the step has a linked quality form (Die Check, Evaluation, LPT, or Thread Inspection), it must be completed first. A warning will appear if it is not.
   - If the step requires photos, the minimum number must be uploaded.
   - If the step has a checklist, all required items must be checked.
2. Tap the blue **MARK COMPLETE** button.
3. A confirmation modal appears. Add any optional completion remarks.
4. Tap **Confirm**.
5. The timer stops. The step status changes to **Completed**. A green banner shows the completion time and a **Next Step** link appears.

### 4.5 Completing Quality Forms from a Step

Some steps have linked quality forms that appear in the **Quality Forms** panel below the action buttons:

- **Die Check Report** — for fluorescent penetrant inspection steps. Tap the card to open the die check form.
- **Cutter Evaluation** — for cutter inspection steps. Tap to open the evaluation grid.
- **LPT Report** — for liquid penetrant test steps.
- **Thread Inspection** — for API connection check steps.
- **QC Checklist** — for general quality verification steps.

Each form link shows whether the form already exists (edit) or needs to be created (create new). Completed forms show a green check mark.

### 4.6 Entering Remarks

At the bottom of each step page is a **Remarks / Notes** text area. You can type any observations, issues, or notes about the step. Tap **Save remarks** to store them. Remarks are saved to the work order record and are visible to supervisors.

### 4.7 Navigating Between Steps

At the bottom of the step page:
- **Left arrow** — go to the previous step.
- **List icon** (center) — go to the full router sheet.
- **Right arrow** — go to the next step.
- **Full Job Card** link — view the complete work order detail page.

### 4.8 Uploading Photos

When a step requires photos (the photo section appears on the linked quality form):
1. Open the quality form (e.g., Die Check or Evaluation).
2. Scroll to the **Photos** section.
3. Choose a method:
   - **ADG Guided** — follow the guided sequence (Blade 1 Photo 1, Blade 1 Photo 2, etc.). Tap an empty slot to capture.
   - **Camera** — open the device camera directly and capture a photo.
   - **Free Upload** — select a file from your device.
4. After capturing, the photo appears in the gallery. You can add annotations using the built-in editor (draw, arrows, circles, text).

---

## 5. Forms & Data Entry Reference

| Form / Page | How to Access | Key Actions |
|---|---|---|
| Operator Portal Home | Sidebar > Production > Operator Portal | View active steps, scan QR, see all WOs |
| QR Scanner | Operator Portal > Scan Job QR Code | Scan QR or type WO/BIT number manually |
| Step View | QR scan result or tap a step card | START, PAUSE, RESUME, MARK COMPLETE |
| Remarks | Bottom of any Step View page | Free text entry, Save remarks button |
| Photo Upload | Inside linked quality forms | Camera capture, file upload, or ADG guided |
| Die Check Form | Step View > Quality Forms > Die Check | Materials, cutter findings grid, decisions |
| Checklist | Step View > Quality Forms > QC Checklist | Tick off verification items |

---

## 6. Reports Available to You

| Report | Location | Description |
|---|---|---|
| My Active Steps | Operator Portal home page | Steps you have started but not completed |
| My Work Orders | Operator Portal home page | WOs assigned to you with priority and due date |
| All Active WOs | Operator Portal home page | Every active WO on the floor |
| Router Sheet | Tap any WO card | Full list of all steps for a work order with status |
| Full Job Card | Link at bottom of Step View | Complete work order detail including evaluations and history |

---

## 7. Notifications & Alerts

You will receive notifications for:

- **Step resumed by someone else** — if another operator resumes a step you paused.
- **Work order approved** — when a new WO is approved and ready for production.
- **Quality hold** — if QC places a hold on a step you are working on.
- **Waiting for QC** — when a step transitions to waiting status.

Notifications appear on the bell icon in the top navigation bar. The bell shows a count badge when you have unread notifications. A short beep sound plays when a new notification arrives.

---

## 8. Approvals & Sign-offs

As a machine operator, you generally do not approve or sign off on documents. However:

- **Step Completion** counts as your sign-off that the work is done. Your username and timestamp are recorded permanently.
- **Remarks** you enter become part of the official quality record.
- **Photos** you upload are linked to your user account and cannot be altered after upload (though annotations can be added non-destructively).
- **Checklist items** you check off are saved with your identity.

If a step requires supervisor approval before you can proceed, it will show as **Waiting QC** or **Waiting Approval** status. You will be notified when it is released.

---

## 9. Frequently Asked Questions

**Q: The QR scanner says "Camera not available." What do I do?**
A: Your browser may not have permission to use the camera. Check your browser settings and allow camera access for localhost:8001. Alternatively, use the manual entry field below the camera — type the work order number (e.g., WO-2026-0042) and tap Go to Step.

**Q: I accidentally started the wrong step. Can I undo it?**
A: You cannot undo a started step yourself. Contact your supervisor, who can skip the step with a documented reason from the full Router Sheet page.

**Q: The system says I cannot complete the step because a quality form is missing. What should I do?**
A: Tap the quality form link in the Quality Forms panel on the step page. Fill out the required form (e.g., Die Check or Evaluation) and mark it complete. Then return to the step and try completing it again.

**Q: I need to take a long break. Should I pause or complete the step?**
A: Pause the step. This stops the timer and preserves your progress. Complete the step only when the physical work is actually finished.

**Q: Can I work on more than one step at a time?**
A: You can have multiple steps in progress across different work orders, but focus on one at a time for accurate time tracking. The Operator Portal shows all your active steps in the My Active Steps section.

**Q: What do the priority badges mean?**
A: **Critical** (dark red) = must be done immediately. **Urgent** (light red) = high priority. **High** (amber) = above normal. **Normal** (green) = standard priority. **Low** (gray) = can wait.

**Q: My page looks different from what is described here. Why?**
A: The system has a dark mode toggle. Tap the moon/sun icon in the top navigation bar to switch between light and dark modes.

**Q: How do I report a problem with a drill bit during my step?**
A: Enter details in the Remarks field on the step page and save them. If the issue is serious, inform your supervisor verbally as well. Some forms also have a "Report Issue" button.

---

## 10. Glossary

| Term | Definition |
|---|---|
| **Operator Portal** | The mobile-friendly home screen for floor operators, showing active steps and QR scanner. |
| **Router Sheet** | The full sequence of production steps for a work order, from start to finish. |
| **Step** | A single operation in the router sheet (e.g., Debraze, Machine, Braze, Inspect). |
| **QR Code** | A square barcode printed on work order papers that the system can scan to jump to the right step. |
| **Work Order (WO)** | A production job for a specific drill bit, with a unique WO number. |
| **Serial Number** | The unique number stamped on a drill bit (6 or 8 digits). |
| **Timer** | The elapsed time display on the step page that tracks how long you have been working. |
| **Quality Form** | A linked inspection or evaluation document that must be completed as part of a step. |
| **ADG** | Automated Data Gathering — the guided photo capture sequence (blade by blade). |
| **Business Unit (BU)** | The account category (LSTK, ARAMCO, etc.) that determines the work order's workflow. |
| **Priority** | The urgency level of a work order (Critical, Urgent, High, Normal, Low). |
