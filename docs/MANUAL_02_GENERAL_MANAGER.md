# General Manager / Senior Management — User Manual

**System:** ARDT Floor Management System
**Version:** Draft 1.0
**Date:** April 4, 2026
**Audience:** General Manager / Senior Management — Executive leaders who need high-level visibility into production status, workforce competency, and key performance indicators.

---

## 1. Your Role in the System

As General Manager or a member of senior management, your interaction with the ARDT Floor Management System is focused on oversight, approval, and strategic decision-making. You are not expected to enter data or operate production forms. Instead, the system provides you with real-time visibility into what is happening on the shop floor, which work orders need your attention, and where bottlenecks or quality issues are emerging.

Your primary use of the system is reviewing dashboards, approving work orders that require managerial sign-off, monitoring the production planner for capacity and scheduling concerns, and reviewing workforce competency reports to ensure operators are properly certified for the processes they perform.

The system's role-based access ensures that you see the information relevant to your level. Dashboards consolidate data from drill bit receiving, production, quality control, and dispatch into summary views. The notification bell in the top navigation keeps you informed of events that require your attention, such as work orders sent for approval or quality holds.

**Important note:** Several executive-level reporting features are currently under active development. This manual clearly marks which features are fully operational and which are planned for future release.

---

## 2. Logging In

**Step 1.** Open your web browser and navigate to:
`http://localhost:8001/accounts/login/`

**Step 2.** Enter your **Username** and **Password**.

**Step 3.** Click **Log In**. You will be taken to the Main Dashboard.

**Troubleshooting:**

| Problem | Solution |
|---------|----------|
| "Invalid username or password" | Check for typos. Usernames are case-sensitive. Try the default password `Ardt@2025` if your account was recently created. |
| Session expired after a long meeting | Sessions last 24 hours. Simply log in again. No data is lost. |
| Cannot access a certain page | Contact the System Administrator to verify your role assignment includes GENERAL_MANAGER. |
| Pages load slowly | The system runs on a local server. If response times are consistently slow, ask IT to check server resources. |

---

## 3. Your Workbench

After logging in, you arrive at the **Main Dashboard**. From here, you can navigate to the views most relevant to your role:

**Top Navigation Bar:**
- **Global Search** (center) — Type any work order number, drill bit serial, or procedure name to find it instantly. Press Ctrl+K from any page to focus the search bar.
- **Notification Bell** (top right) — Shows unread notification count. Click to see recent alerts such as work orders awaiting your approval or quality escalations.
- **Dark Mode Toggle** — Switch between light and dark display themes for comfort.
- **Profile Menu** — Click your initials to access Profile, Settings, or Sign Out.

**Left Sidebar — Key sections for your role:**
- **Dashboard > Manager** — The executive overview dashboard.
- **Dashboard > Planner** — Production scheduling overview.
- **Production > Planner** — The active production plan with Ready, Planned, and WIP tabs.
- **Production > Work Orders** — Full list of all work orders with status filters.
- **Production > Floor Board** — Real-time card view of active work on the shop floor.
- **Logistics > Drill Bit Inventory > Drill Bits** — Complete inventory of all drill bits.
- **HR & Admin > Competency Matrix** — Employee certification status grid.
- **HR & Admin > Training Gaps** — Processes lacking certified coverage.

---

## 4. Core Workflows

### 4.1 Reviewing the Production Floor Board

**When:** Anytime you want a real-time snapshot of active production.

1. Navigate to **Production > Floor Board** (sidebar, or `/work-orders/floor-board/`).
2. The page displays a card for each active work order. Each card shows:
   - Work order number and drill bit serial number
   - Current step name and progress bar
   - Assigned operator name
   - Hold status (if applicable, shown in amber)
3. The page auto-refreshes every 30 seconds.
4. Click any card to open the full work order detail page.

**What you see:** A visual overview of everything happening on the floor right now. Cards are color-coded by status. Work orders on hold are highlighted.

### 4.2 Reviewing Key Performance Indicators (KPIs)

**Current Status:** The KPI dashboard is under active development. The following features are available:

- **Step Duration API** (`/work-orders/api/kpi/step-durations/`) provides aggregated timing data per process step. This data can be filtered by bit size, body material, operator, and account.
- **Manager Dashboard** (`Dashboard > Manager`) provides summary counts of active work orders, bits in production, and pending approvals.

**Under Development:**
- Graphical KPI charts (throughput, cycle time, first-pass yield)
- Comparative period analysis (this week vs. last week)
- Export to PDF for board presentations

### 4.3 Approving Work Orders

**When:** You receive a notification that a work order has been released and needs managerial approval before production can begin.

1. Click the notification in the bell dropdown, or navigate to **Production > Work Orders**.
2. Find the work order with status **Released** (shown as a blue badge).
3. Click on the work order number to open its detail page.
4. Review the information: drill bit serial, design, BOM, account (business unit), and assigned route.
5. In the **Quick Actions** area, click **Approve WO**.
6. The status changes from Released to **Active**.

**What happens next:** The operators are notified that the work order is approved and production can begin. The first router step becomes available.
**Who is notified:** The assigned operator and the PDC Supervisor receive a notification.
**Common mistakes:** Approving a work order without verifying that the drill bit has been physically transferred to the production area. The system will show a location warning if the bit is still at the receiving area.

**Note:** You can also approve directly from the Pending status (skipping Released), which is useful for urgent jobs. Click **Approve WO (skip to Active)** on the work order detail page.

### 4.4 Reviewing the Production Planner

1. Navigate to **Production > Planner** (or `/work-orders/planner/`).
2. The planner has three tabs:
   - **Ready** — Drill bits cleared for production but not yet scheduled.
   - **Planned** — Bits with assigned priority and target dates.
   - **WIP (Work in Progress)** — Bits currently in production with active work orders.
3. Each row shows the serial number, design, size, business unit, level (L3/L4/L5), new/repair status, and requester.
4. Use this view to assess production capacity and identify scheduling conflicts.

### 4.5 Reviewing Workforce Competency

1. Navigate to **HR & Admin > Competency Matrix** (or `/hr/competency/`).
2. The matrix displays a grid of employees (rows) versus master processes (columns).
3. Each cell shows the employee's certification level:
   - **Not Authorized** — Cannot perform this process
   - **Trainee** — Under training, requires supervision
   - **Certified** — Authorized to perform independently
   - **Trainer** — Can train others
4. Click on any cell to see certification details (date, expiry, training hours).

**Training Gaps Report:**
Navigate to **HR & Admin > Training Gaps** (or `/hr/competency/gaps/`) to see processes that have insufficient certified or trainer-level coverage. This is critical for ISO 9001 compliance (Clause 7.2).

---

## 5. Forms & Data Entry Reference

As a General Manager, you primarily view data rather than enter it. The forms you interact with are:

| Form / Page | Location | Your Action | Notes |
|-------------|----------|-------------|-------|
| Work Order Approval | Production > Work Orders > (WO) | Click "Approve WO" | Requires Released or Pending status |
| Notification Settings | Profile Menu > Settings | Configure which notifications you receive | Can mute low-priority alerts |
| Competency Matrix | HR & Admin > Competency Matrix | View only (editing is for HR Admin) | Export to Excel available |

---

## 6. Reports Available to You

| Report | Location | Status | Description |
|--------|----------|--------|-------------|
| Floor Board | Production > Floor Board | Operational | Real-time production status cards, auto-refresh every 30 seconds |
| Manager Dashboard | Dashboard > Manager | Operational | Summary counts and status overview |
| Production Planner | Production > Planner | Operational | Full planning view with Ready/Planned/WIP tabs |
| Work Order List | Production > Work Orders | Operational | Filterable list of all work orders with status, account, dates |
| Drill Bit List | Logistics > Drill Bit Inventory > Drill Bits | Operational | Complete bit inventory with export to Excel |
| Competency Matrix | HR & Admin > Competency Matrix | Operational | Employee-process authorization grid with Excel export |
| Training Gaps | HR & Admin > Training Gaps | Operational | Processes lacking certified operators |
| Step Duration KPI | API only | Operational | Aggregated timing data per process step |
| Stock Valuation | Logistics > Reports > Stock Valuation | Operational | Current inventory value by item and variant |
| Throughput Dashboard | Planned | Under Development | Visual charts for production throughput over time |
| Executive PDF Reports | Planned | Under Development | Printable summary reports for board meetings |

---

## 7. Notifications & Alerts

**What you receive:**

| Notification | Priority | When it triggers |
|-------------|----------|-----------------|
| Work Order sent for approval | HIGH | An Operations Manager or Supervisor releases a WO |
| Quality hold placed | HIGH | QC Inspector places a WO on hold |
| WO Cancelled | URGENT | Any work order is cancelled |
| Evaluation completed | HIGH | A cutter evaluation or receiving inspection is finalized |
| Router sheet fully completed | HIGH | All process steps for a WO are done |
| GRN posted | URGENT | Goods received note posted (inventory changed) |

**How notifications work:** The bell icon in the top-right corner updates every 10 seconds. A brief audio tone plays when a new notification arrives. Click the bell to see up to 5 recent notifications. Click "View All" for the complete list at `/notifications/`.

**What you trigger:** Approving a work order sends a HIGH priority notification to the assigned operator and supervisor.

---

## 8. Approvals & Sign-offs

| Approval | Your Authority | How to Perform | What Happens After |
|----------|---------------|----------------|-------------------|
| Work Order Approval | RELEASED to ACTIVE | Click "Approve WO" on WO detail page | Production can begin; operators notified |
| Skip to Active | PENDING directly to ACTIVE | Click "Approve WO (skip to Active)" | Bypasses the Released stage for urgent jobs |

**Audit Trail:** Every approval records your username, timestamp, and the work order number. This information is visible on the work order detail page in the Account & Dates card and in the system audit log.

**Delegation:** If you are unavailable, the Operations Manager role also has approval authority for day-to-day work orders. Ensure at least one OPS_MANAGER is assigned in the system.

---

## 9. Frequently Asked Questions

**Q1: How do I see how many work orders are currently in production?**
A: The Floor Board (`Production > Floor Board`) shows all active work orders as cards. The Production Dashboard (`Production > Dashboard`) shows aggregate counts.

**Q2: Can I see historical production data?**
A: The Work Order list (`Production > Work Orders`) can be filtered by status, account, and date range. Step-level timing data is available via the KPI API. Graphical trend reports are under development.

**Q3: How do I know if a drill bit has been inspected and cleared?**
A: Open the drill bit detail page (click its serial number anywhere in the system). The Events timeline shows all inspection results. A green "Accepted" badge means it passed receiving inspection.

**Q4: What does "L3", "L4", "L5" mean in the planner?**
A: These are design order levels. L3 is a base design without cutter specifications. L4 adds pocket positions. L5 is a complete Bill of Materials with all cutters specified. L5.5 is a brazed head that still needs welding and machining.

**Q5: Can I approve multiple work orders at once?**
A: Not currently. Each work order must be approved individually from its detail page. Batch approval is planned for a future release.

**Q6: How do I check if we have enough cutters in stock for upcoming jobs?**
A: Navigate to **Logistics > PDC Cutters > Cutter Inventory** (`/inventory/cutters/`). This page shows stock levels by cutter type, broken down by variant (New, Reclaimed, Client-provided, etc.), with on-order quantities.

**Q7: What is the Floor Board refresh rate?**
A: The Floor Board automatically refreshes every 30 seconds. You do not need to manually reload the page.

**Q8: Who can I contact if the system is down or behaving unexpectedly?**
A: Contact the System Administrator. If the server is not responding, IT staff should check whether the Python process on port 8001 is running.

**Q9: Are my approval actions recorded for audit purposes?**
A: Yes. Every approval records your username, the timestamp, and the work order number. The audit log is accessible at `/notifications/audit/`.

---

## 10. Glossary

| Term | Definition |
|------|-----------|
| **Work Order (WO)** | A formal job record for repairing or manufacturing a drill bit. Identified by a number like `2026-LSTK-1001`. |
| **Business Unit (Account)** | An organizational category that determines work order numbering, pricing, and routing. Examples: LSTK, ARAMCO, Halliburton. |
| **Floor Board** | A real-time visual display of all active work orders on the production floor. |
| **Router Sheet** | The ordered list of process steps that a drill bit must go through during production (e.g., Debraze, Sub-Arc Weld, Brazing, QC). |
| **Evaluation** | A formal inspection of the drill bit's cutters, body, and threads at various stages of production. |
| **Competency Matrix** | A grid mapping employees to production processes with their certification level (Trainee, Certified, Trainer). |
| **BOM (Bill of Materials)** | A list of all cutters and components required for a specific drill bit design. |
| **PDC** | Polycrystalline Diamond Compact — the type of cutting elements used on fixed cutter drill bits. |
| **HDBS** | Halliburton Drill Bit System — a classification code system for drill bit types. |
| **KPI** | Key Performance Indicator — a measurable value demonstrating operational effectiveness. |
| **GRN** | Goods Received Note — a document confirming physical receipt of ordered materials into inventory. |
| **Notification Bell** | The bell icon in the top-right corner that shows real-time alerts. Updates every 10 seconds. |
