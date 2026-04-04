# Operations Manager — User Manual

**System:** ARDT Floor Management System
**Version:** Draft 1.0
**Date:** April 4, 2026
**Audience:** Operations Manager — The person who oversees daily production operations, approves work orders, manages the production planner, assigns business units to drill bits, and coordinates location transfers.

---

## 1. Your Role in the System

As Operations Manager, you are the bridge between executive oversight and shop floor execution. You manage the day-to-day flow of drill bits through the production pipeline: from receiving, through planning and scheduling, to release into production. Your decisions directly control what gets worked on and when.

In the system, you perform three main categories of work. First, **production planning and scheduling**: you decide which drill bits are ready for production, assign business units (such as LSTK, ARAMCO, or Halliburton), set priorities, and release work orders. Second, **work order management**: you approve work orders to transition them from Released to Active status, monitor progress via the Floor Board, and handle exceptions like holds, cancellations, and re-routing. Third, **logistics coordination**: you oversee the movement of drill bits between physical locations (Receiving Area, Production Floor, Evaluation, Dispatch) and ensure the system's location tracking matches reality.

Your role gives you broad visibility across all production modules. You can access the production planner, work order lists, drill bit inventory, Floor Board, receiving dock, and location transfer pages. You are one of the key approvers in the workflow and your actions trigger notifications to supervisors and operators.

---

## 2. Logging In

**Step 1.** Open your browser and go to: `http://localhost:8001/accounts/login/`

**Step 2.** Enter your **Username** and **Password**.

**Step 3.** Click **Log In**. You are taken to the Main Dashboard.

**Troubleshooting:**

| Problem | Solution |
|---------|----------|
| "Invalid username or password" | Verify your username and password. Contact the System Administrator if you have forgotten your credentials. |
| Cannot see Production Planner or Work Orders | Your account may not have the OPS_MANAGER role assigned. Contact the System Administrator. |
| Session expired | Sessions last 24 hours. Log in again. Any unsaved form data will be lost, so always save before stepping away for extended periods. |
| A page shows "403 Forbidden" | You do not have permission for that specific action. Contact the System Administrator. |

---

## 3. Your Workbench

After logging in, you typically navigate to one of your primary work areas. Here is an overview of what each looks like:

**Production Planner** (`Production > Planner`): Three-tab view (Ready, Planned, WIP). Each tab shows a table of drill bits with serial number, design, size, business unit, level, new/repair flag, requester, and priority. The Planned tab is your primary workspace for scheduling.

**Work Order List** (`Production > Work Orders`): A filterable, sortable table of all work orders. Filter by status (Pending, Released, Active, In Progress, QC Pending, Completed), by account, or search by WO number. Status badges are color-coded.

**Floor Board** (`Production > Floor Board`): Real-time card view of work currently in progress. Each card shows the WO number, serial, current step, operator, and progress bar. Auto-refreshes every 30 seconds.

**Drill Bit List** (`Logistics > Drill Bit Inventory > Drill Bits`): The master inventory with customizable column visibility, Excel-style filters and sort, and export to Excel.

**Location Transfers** (`Logistics > Locations > Bit Movements`): Page for confirming physical movement of drill bits between areas.

**Left Sidebar — Key sections:**
- **Production** — Planner, Work Orders, Dashboard, Floor Board
- **Receiving** — Dashboard, Backload Batches, Inspections
- **Logistics** — Drill Bit Inventory, Locations, Bit Movements
- **Notifications** — Bell icon in top nav, Action Center

---

## 4. Core Workflows

### 4.1 Assigning a Business Unit to a Drill Bit

**When:** A drill bit has been received and inspected, and needs to be assigned to a production account before it can enter the planner.

1. Navigate to **Logistics > Drill Bit Inventory > Drill Bits**.
2. Find the drill bit by serial number (use the search bar or column filters).
3. Click the **Business Unit** badge (indigo label) on the bit's row. If no account is assigned, click the pencil icon in that column.
4. The **Business Unit Assignment** modal opens. Fill in:
   - **Business Unit** — Select from the dropdown (LSTK, ARAMCO, Halliburton, UR, L3, L4, etc.)
   - **New / Repair** — Toggle to indicate whether this is a new build or a repair job. The system auto-detects based on the bit's condition, but you can override it.
   - **Requester** — Your name (auto-filled)
   - **Justification** — Optional text explaining the assignment
5. Choose one of two actions:
   - **Assign Only** — Saves the business unit assignment
   - **Assign & Add to Planner** — Saves and immediately creates a planner entry

**What happens next:** The drill bit now appears in the planner's Ready or Planned tab.
**Who is notified:** No automatic notification for assignment alone. Adding to planner is visible to all planner users.
**Common mistakes:** Assigning an FC (Fixed Cutter) bit to the planner without a BOM. The system will block this and show an orange warning: "FC bit has no BOM -- create a BOM first."

### 4.2 Managing the Production Planner

1. Navigate to **Production > Planner**.
2. **Ready Tab:** Shows bits that are eligible for production but not yet scheduled. Review each and decide whether to proceed.
3. **Planned Tab (your primary workspace):** Shows bits scheduled for production. Each row shows serial, design, size, account, level, new/repair, requester, and planned date.
4. To **release a planned entry**:
   - Click the **Release** button on the entry's row.
   - This creates a Work Order and changes the planner entry status to PENDING_RELEASE or directly to RELEASED, depending on whether the bit is already at the production location.
5. To **remove from planner**:
   - Click the **Remove** button. The bit returns to its previous status.

**Planner Status Flow:**
PLANNED --> PENDING_RELEASE --> RELEASED --> WO_CREATED

**What happens next after release:** A work order is created. If the bit is not yet at the production area, a location transfer notification is generated. Once the bit arrives and is confirmed, the WO transitions to Released.

### 4.3 Approving Work Orders (Released to Active)

**When:** A work order has been released (either by you through the planner or by a supervisor) and needs managerial approval before production begins.

1. Navigate to **Production > Work Orders**.
2. Filter by status **Released** to see work orders awaiting approval.
3. Click on a work order number to open its detail page.
4. Review:
   - The drill bit serial number, design, and size
   - The assigned business unit
   - The production route (list of process steps)
   - The BOM (cutter requirements)
5. In the **Quick Actions** section, click **Approve WO**.
6. The status changes to **Active**.

**What happens next:** Operators are notified. The router sheet becomes available, and the first process step can be started.
**Who is notified:** The assigned operator and supervisor receive a HIGH priority notification with a link to the router sheet.
**Location warning:** If the drill bit's physical location is still at Receiving or Warehouse (not at the production area), the system shows a warning. The approval still goes through, but you should verify the bit has been or will be transferred.

**Alternative:** Click **Approve WO (skip to Active)** if the WO is in Pending status, to skip the Released stage for urgent jobs.

### 4.4 Managing Location Transfers

**When:** A drill bit needs to move from one physical area to another (e.g., Receiving Area to Production Floor), and the system must reflect this movement.

1. Navigate to **Logistics > Locations > Bit Movements** (or `/work-orders/location-transfers/`).
2. The page shows pending transfer requests and a form to initiate new transfers.
3. To confirm a transfer:
   - Find the pending transfer (typically generated when a planner entry is released)
   - Verify the drill bit's serial number and destination
   - Click **Confirm Transfer**
4. To create a new transfer manually:
   - Select the drill bit
   - Select the destination location
   - Click **Transfer**

**What happens next:** The drill bit's location is updated in the system. If a Pending work order exists for this bit and the bit arrives at a production area, the WO is automatically transitioned to Released.
**Who is notified:** The operator assigned to the related work order is notified.
**Important rule:** Location transfers must always be done through this page. Drill bit locations should never be changed without going through the transfer process.

### 4.5 Reviewing Router Sheets

1. Open any active or in-progress work order from **Production > Work Orders**.
2. Click the **Router Sheet** tab (or navigate to `/workorders/<pk>/router-sheet/`).
3. The router sheet shows all process steps in order:
   - Step number, name, category (Preparation, Production, QC, Finishing)
   - Status (Pending, In Progress, Completed, Skipped)
   - Operator name and timestamps (start, end, duration)
4. Steps with quality gates are marked. Steps requiring photos or evaluations show requirement indicators.
5. Use this view to identify bottlenecks (steps that have been in progress for too long) or steps that were skipped and may need review.

### 4.6 Deleting a Work Order

**When:** A work order was created in error or needs to be cancelled before production starts.

1. Open the work order detail page.
2. Click **Delete** in the actions area.
3. A three-step confirmation dialog appears:
   - **Step 1:** Confirm you want to delete.
   - **Step 2:** Choose whether to **reverse the physical transaction** (move the bit back to its pre-release location) or leave it where it is.
   - **Step 3:** Choose whether to **return the bit to the planner** (status: Planned) or mark as **Production Cancelled**.
4. Click **Confirm Delete**.

**What happens next:** The WO is deleted. A WO_CANCELLED event is recorded on the drill bit's timeline for audit purposes.
**Who is notified:** All users receive a notification about the cancellation.

---

## 5. Forms & Data Entry Reference

| Form / Page | Location | Required Fields | Notes |
|-------------|----------|-----------------|-------|
| Business Unit Assignment | Drill Bit List > BU badge | Business Unit, New/Repair | Justification optional |
| Planner Release | Production > Planner > Release button | None (auto-populated) | Creates a WO automatically |
| WO Approval | Production > Work Orders > (WO) > Approve | None (single click) | Records your name and timestamp |
| Location Transfer | Logistics > Locations > Bit Movements | Drill bit, Destination | Creates audit event |
| WO Deletion | Production > Work Orders > (WO) > Delete | Confirm (3 steps) | Optionally reverses transaction and returns to planner |
| Work Order Create | Production > Work Orders > Create | Serial Number, Account | Serial auto-populates design/BOM info |

---

## 6. Reports Available to You

| Report | Location | Description |
|--------|----------|-------------|
| Floor Board | Production > Floor Board | Real-time card view of all active WOs, auto-refreshes 30 seconds |
| Production Planner | Production > Planner | Three-tab planning view with bit scheduling |
| Work Order List | Production > Work Orders | Filterable list with status, account, date filters |
| Drill Bit List | Logistics > Drill Bit Inventory > Drill Bits | Full inventory with export to Excel |
| Drill Bit Export | Logistics > Drill Bit Inventory > Export Excel | Excel file with customizable columns |
| Receiving Dashboard | Receiving > Dashboard | Incoming batches, pending inspections, BOM requests |
| Cutter Inventory | Logistics > PDC Cutters > Cutter Inventory | Stock levels by cutter type and variant |
| Competency Matrix | HR & Admin > Competency Matrix | Employee process certifications |
| Stock Valuation | Logistics > Reports > Stock Valuation | Inventory value by item |
| Movement History | Logistics > Reports > Movement History | Drill bit and stock movement audit trail |

---

## 7. Notifications & Alerts

**What you receive:**

| Notification | Priority | Trigger |
|-------------|----------|---------|
| WO released, awaiting approval | HIGH | Supervisor or planner releases a WO |
| WO status changed to QC Pending | HIGH | Production step completed, sent for QC |
| Work order placed on hold | HIGH | Operator or supervisor places a hold |
| WO cancelled | URGENT | Any work order is cancelled |
| Evaluation completed | HIGH | Cutter evaluation finalized |
| All router steps complete | HIGH | A WO's full route is done |
| GRN posted | URGENT | Goods received into inventory |
| Quality decision needed | HIGH | Die check found cutter issues requiring quality decision |

**What you trigger:**
- Approving a WO sends HIGH notifications to the operator and supervisor.
- Cancelling a WO sends URGENT notifications to all users.
- Releasing from planner triggers transfer notifications.

---

## 8. Approvals & Sign-offs

| Action | Required Status | Your Authority | Result |
|--------|----------------|---------------|--------|
| Approve Work Order | Released or Pending | Click "Approve WO" | WO becomes Active |
| Skip to Active | Pending only | Click "Approve WO (skip to Active)" | Bypasses Released stage |
| Release from Planner | Planned | Click "Release" | Creates WO as Pending or Released |
| Delete Work Order | Any pre-production status | Click "Delete" with 3-step confirmation | WO deleted, audit event recorded |

**Audit Trail:** All approvals record your username, timestamp, and the work order number. Visible on the WO detail page and in the notification audit log at `/notifications/audit/`.

---

## 9. Frequently Asked Questions

**Q1: A drill bit is stuck in Pending Release. What should I do?**
A: This means the bit has not been physically transferred to the production area yet. Go to **Logistics > Locations > Bit Movements** and confirm the transfer. Once confirmed, the system automatically transitions the WO.

**Q2: Can I change the business unit after a work order has been created?**
A: Not directly on the work order. You would need to delete the WO, change the business unit on the drill bit, and re-release from the planner.

**Q3: How do I see which operator is working on a specific drill bit right now?**
A: Check the **Floor Board** (`Production > Floor Board`). Each card shows the currently assigned operator. Alternatively, open the WO detail page and check the router sheet for the in-progress step.

**Q4: What is the difference between "Planned" and "Ready" in the planner?**
A: **Ready** means the bit has passed inspection and is eligible for production but has not been formally scheduled. **Planned** means it has been added to the production plan with a priority and target date.

**Q5: Can I approve a WO from my phone?**
A: Yes, the system is accessible from any browser. The interface is responsive. Navigate to the WO detail page and use the Approve button.

**Q6: What happens if I approve a WO but the drill bit is at the wrong location?**
A: The system will show a location warning but will still allow the approval. It is your responsibility to ensure the bit is transferred before production starts. A notification is sent to remind the team.

**Q7: How do I track which bits belong to which client (ARAMCO vs. Halliburton)?**
A: Each drill bit has an assigned **Business Unit** (Account). Filter the drill bit list by the Account column, or filter the planner by account.

**Q8: How many work orders can I approve at once?**
A: Currently, work orders must be approved one at a time. Batch approval is planned for future development.

**Q9: What is L5.5?**
A: L5.5 is a "Brazed head, unwelded upper" — a partially completed bit that needs sub-arc welding and machining. It sits between L5 (full BOM) and a finished product.

**Q10: Where can I see the release paper for a work order?**
A: On the WO detail page, click the indigo **Release** button in the header. This opens a printable Release Paper at `/work-orders/enhanced/<pk>/release-paper/` with QR code, route summary, and signature areas.

---

## 10. Glossary

| Term | Definition |
|------|-----------|
| **Work Order (WO)** | A production job for repairing or manufacturing a drill bit. Follows the status flow: Pending, Released, Active, In Progress, QC Pending, Completed. |
| **Business Unit (Account)** | An organizational category controlling WO numbering and routing (e.g., LSTK, ARAMCO, Halliburton, UR). |
| **Production Planner** | The scheduling tool that manages which drill bits will be worked on and in what order. |
| **Floor Board** | A real-time dashboard showing all active production as visual cards. |
| **Router Sheet** | The ordered list of production steps a drill bit goes through. Each step has requirements and can be tracked by QR scan. |
| **Release Paper** | A printable document accompanying a work order when it enters production. Contains the QR code, route summary, and sign-off areas. |
| **Location Transfer** | The formal process of moving a drill bit from one physical area to another, recorded in the system. |
| **BOM (Bill of Materials)** | The list of cutters and components required for a drill bit design. |
| **FC (Fixed Cutter)** | A type of drill bit that uses PDC cutters (as opposed to RC / Roller Cone bits). |
| **Level (L3/L4/L5/L5.5)** | The design detail level: L3 = base design, L4 = with pocket positions, L5 = full BOM, L5.5 = brazed but unwelded. |
| **Backload** | The process of receiving drill bits back from the field for repair. |
| **Stepper** | The visual status indicator on the WO detail page showing progress: Pending, Released, Active, Progress, QC, Complete. |
