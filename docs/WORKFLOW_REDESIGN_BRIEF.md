# Workflow & Notification System Redesign Brief

## For: AI Agent Consultation
## Project: ARDT Operational System (Drill Bit Manufacturing & Repair)
## Date: April 3, 2026

---

## 1. WHAT THIS PROJECT IS

ARDT is a drill bit manufacturing and repair company. This Django web application manages:
- **Drill Bit Lifecycle**: Receiving → Inspection → Planning → Production → QC → Dispatch
- **Work Orders**: Manufacturing and repair jobs with router sheets (step-by-step production processes)
- **Inventory**: PDC Cutters, BOMs, stock ledger
- **ERP Automation**: Browser-based D365 automation

**Tech Stack**: Django 5.1, Python 3.11, SQLite, HTMX + Alpine.js + Tailwind CSS, no frontend build step.

---

## 2. THE PROBLEM

The current notification system is **ad-hoc**: views call `notify()` with free text, and there's no systematic connection between:
- **Workflow transitions** (what happened)
- **Required actions** (what someone must DO in response)
- **Action routing** (WHO must do it, with what input, producing what output)
- **Dependencies** (action B can't start until action A is complete)
- **Escalation** (what happens if nobody acts within X hours)

We need to redesign this as a proper **Workflow Action Engine** where every business event creates structured, trackable actions for the right people.

---

## 3. CURRENT WORKFLOW (End-to-End Production Lifecycle)

### 3.1 Receiving
```
Drill bit arrives at ARDT (backload batch or new shipment)
→ DrillBit created with status RECEIVED/UNREGISTERED
→ Assigned to a Location (Receiving Area or Backload Area)
→ Receiving Inspection performed (ACCEPTED / REJECTED / CONDITIONAL)
→ If ACCEPTED: status → IN_EVALUATION, location → Evaluation Area
→ If REJECTED: status → REJECTED, stays in Receiving
```

### 3.2 Planning
```
Planner assigns Business Unit (Account) to the bit
→ Planner adds bit to Production Planner (status PLANNED)
→ Planner releases the bit → creates Work Order
→ WO starts as PENDING
→ Floor operator must physically transfer the bit to production area
→ When transfer confirmed → WO status → RELEASED
→ Manager must approve → WO status → ACTIVE
```

### 3.3 Production
```
WO ACTIVE → operator can start first router step
→ Router sheet has 10-40 steps (built dynamically from Smart Route Engine)
→ Steps must be executed in ORDER (can't skip ahead without supervisor)
→ Each step: START → work → record parameters/checklist → COMPLETE
→ Steps can be: PAUSED, ON_HOLD (with reason), SKIPPED (with reason)
→ Hold reasons: Equipment Failure, Material Shortage, Quality Hold, Technical Review, etc.
→ Skip reasons: N/A, Within Spec, Accepted As-Is, Approved by Supervisor, etc.
→ Some steps link to dedicated quality forms (Die Check, Cutter Evaluation, LPT, Thread Inspection)
→ Some steps require photos before completion
→ Some steps require linked evaluation to be complete
→ CRITICAL special instructions can block step start
```

### 3.4 QC & Completion
```
All steps complete → WO → QC_PENDING
→ QC inspector reviews → PASSED or FAILED
→ If PASSED → WO → COMPLETED, bit → ready for dispatch
→ If FAILED → WO → needs rework (new steps or repeat)
```

### 3.5 Dispatch
```
Bit transferred to Finished Goods warehouse
→ Dispatch inspection
→ Painting & boxing
→ Shipped to customer
```

---

## 4. CURRENT NOTIFICATION SYSTEM

### 4.1 Model (apps/notifications/models.py)
```python
class Notification(models.Model):
    recipient = ForeignKey(User)           # Who receives it
    actor = ForeignKey(User, nullable)     # Who triggered it
    title = CharField(max_length=200)      # Headline
    message = TextField()                  # Full body
    priority = CharField(choices=[LOW, NORMAL, HIGH, URGENT])
    entity_type = CharField(max_length=50) # "WorkOrder", "DrillBit", etc.
    entity_id = BigIntegerField(nullable)  # PK of related entity
    action_url = CharField(max_length=500) # URL to navigate to
    is_read = BooleanField(default=False)
    read_at = DateTimeField(nullable)
    created_at = DateTimeField(auto_now_add)
```

### 4.2 Service (apps/notifications/services.py)
```python
def notify(actor, verb, target=None, recipients=None, priority="NORMAL",
           action_url="", title=None, message=None, entity_type="", entity_id=None):
    # recipients can be: "all", QuerySet, list, single User, or None (=all)
    # Creates Notification records via bulk_create()
```

### 4.3 Current Notification Points (24 total)
All are ad-hoc `notify()` calls scattered across views:

| # | Event | Verb/Title | Priority | Action URL | Recipients |
|---|-------|-----------|----------|------------|------------|
| 1 | Evaluation completed | "completed {type} evaluation" | HIGH | WO detail | All |
| 2 | Route auto-updated | "route updated after evaluation" | NORMAL | Router sheet | All |
| 3 | All router steps done | "All router steps completed" | HIGH | Location transfers | All |
| 4 | Bit released + WO created | "released and created WO" | HIGH | WO detail | All |
| 5 | Release request (no WO yet) | "requests release of" | HIGH | WO detail | All |
| 6 | Transaction confirmed | "confirmed transaction" | HIGH | WO detail | All |
| 7 | WO approved | "WO approved — production can start" | HIGH | WO detail | All |
| 8 | WO sent to QC | "sent WO to QC" | HIGH | WO detail | All |
| 9 | QC passed | "QC passed WO" | HIGH | WO detail | All |
| 10 | QC failed | "QC failed — rework needed" | URGENT | WO detail | All |
| 11 | WO completed | "completed WO" | HIGH | WO detail | All |
| 12 | WO deleted | "WO deleted for {serial}" | HIGH | Planner/bit/transfers | All |
| 13 | Release confirmed (at dest) | "confirmed release" | HIGH | WO detail | All |
| 14 | Transfer + WO created | "transferred and created WO" | HIGH | WO detail | All |
| 15 | Receiving inspection done | "completed receiving inspection" | HIGH | Inspection edit | All |
| 16 | PDC evaluation completed | "completed PDC evaluation" | HIGH | WO detail | All |
| 17 | Die check quality decision | "requested quality decision" | HIGH | Die check page | All (broadcast) |
| 18 | Step on hold | "put step on hold" | HIGH | Step detail | All |
| 19 | Step waiting QC/approval/tech | "requested {type} review" | HIGH | Step detail | All |
| 20 | Step resumed | "resumed step" | NORMAL | Step detail | Operator only |
| 21 | WO started | "started work on" | NORMAL | WO detail | All |
| 22 | WO status change | "changed status to" | Variable | WO detail | All |
| 23 | Cerebro device warning | "bit with Cerebro installed" | URGENT | Bit detail | All |
| 24 | GRN posted | "posted GRN" | URGENT | GRN detail | All |

### 4.4 Problems with Current System
1. **All notifications go to ALL users** — no role-based routing
2. **No action type** — recipient doesn't know what they're supposed to DO
3. **No input/output tracking** — no way to know if the action was taken
4. **No dependencies** — action B doesn't know to wait for action A
5. **No escalation** — if nobody acts, nothing happens
6. **No completion tracking** — notification is "read" but action may not be done
7. **One event = one notification** — but one event may require MULTIPLE people to act
8. **Free-text messages** — action buttons are keyword-matched (fragile)

---

## 5. PROPOSED WORKFLOW ACTION ARCHITECTURE

### 5.1 Core Concept
Every workflow transition creates one or more **WorkflowActions** (tasks). Each action:
- Is assigned to a specific **role/user/team**
- Has a specific **action type** (what they must do)
- Has **required input** (what data they must provide)
- Produces **expected output** (what changes when done)
- May have **dependencies** (other actions that must complete first)
- Has a **deadline** and **escalation path**

### 5.2 Proposed Model
```python
class WorkflowAction(models.Model):
    # What triggered this action
    trigger_event = CharField(choices=WorkflowEvent.choices)  # RELEASE, HOLD, INSPECTION_DONE, etc.
    trigger_entity_type = CharField()  # "WorkOrder", "DrillBit", "RouterSheetEntry"
    trigger_entity_id = BigIntegerField()

    # Who must act
    assigned_to = ForeignKey(User, nullable)        # Specific user
    assigned_role = CharField(choices=Role.choices)  # Or a role (OPERATOR, MANAGER, QC_INSPECTOR, etc.)

    # What they must do
    action_type = CharField(choices=ActionType.choices)  # APPROVE, TRANSFER, INSPECT, REVIEW, START, etc.
    action_url = CharField()        # Page where the action is performed
    description = TextField()       # Human-readable "what to do"

    # Required input/output
    required_input = JSONField()    # What data fields must be filled
    expected_output = JSONField()   # What state changes when done

    # Status tracking
    status = CharField(choices=[PENDING, IN_PROGRESS, COMPLETED, ESCALATED, CANCELLED, EXPIRED])
    completed_at = DateTimeField(nullable)
    completed_by = ForeignKey(User, nullable)
    result_data = JSONField()       # What the user actually provided

    # Dependencies
    depends_on = ManyToManyField('self', symmetrical=False)  # Actions that must complete first
    is_blocked = BooleanField()     # Computed: True if any dependency is incomplete

    # Escalation
    deadline = DateTimeField(nullable)
    escalate_after_hours = IntegerField(nullable)
    escalate_to = ForeignKey(User, nullable)
    escalated_at = DateTimeField(nullable)

    # Notifications sent for this action
    notification = ForeignKey(Notification, nullable)  # The notification that was sent

    created_at = DateTimeField(auto_now_add)
    created_by = ForeignKey(User)
```

### 5.3 Example: WO Release Chain
```
Event: Planner releases bit (serial 14414031)

WorkflowAction #1:
  trigger_event: WO_RELEASED
  action_type: TRANSFER_BIT
  assigned_role: FLOOR_OPERATOR
  description: "Transfer bit 14414031 from Evaluation Area to Production Bay 1"
  action_url: /work-orders/location-transfers/?serial=14414031&dest=WIP-BAY1
  required_input: {confirm_transfer: true, carried_by: "name"}
  status: PENDING
  deadline: +4 hours
  escalate_to: Supervisor

WorkflowAction #2:
  trigger_event: WO_RELEASED
  action_type: APPROVE_WO
  assigned_role: PRODUCTION_MANAGER
  description: "Review and approve WO 2026-AR-005 for serial 14414031"
  action_url: /work-orders/enhanced/48/
  required_input: {decision: "approve|reject", notes: "optional"}
  status: PENDING
  deadline: +8 hours
  escalate_to: Plant Manager

WorkflowAction #3:
  trigger_event: WO_RELEASED
  action_type: PRINT_RELEASE_PAPER
  assigned_role: PRODUCTION_LEAD
  description: "Print release paper and file in WO packet"
  action_url: /work-orders/enhanced/48/release-paper/
  depends_on: [#1, #2]  ← blocked until transfer AND approval done
  required_input: {printed: true, filed: true}
  status: BLOCKED

WorkflowAction #4:
  trigger_event: WO_APPROVED
  action_type: START_PRODUCTION
  assigned_role: OPERATOR
  description: "Start first router step on WO 2026-AR-005"
  action_url: /work-orders/48/router-sheet/
  depends_on: [#3]  ← blocked until release paper done
  status: BLOCKED
```

### 5.4 Action Types Catalog

| Action Type | Label | Performed On | Input Required | Output |
|-------------|-------|-------------|----------------|--------|
| INSPECT_BIT | Start Inspection | Receiving Inspection form | Full inspection data | Result: ACCEPTED/REJECTED |
| ADD_TO_PLAN | Add to Planner | Planner page | Account, priority | Plan entry created |
| TRANSFER_BIT | Transfer Bit | Location Transfers page | Confirm source/dest | Bit location updated |
| APPROVE_WO | Approve Work Order | WO Detail page | Approve/Reject decision | WO → ACTIVE or REJECTED |
| PRINT_RELEASE | Print Release Paper | Release Paper page | Print confirmation | Paper filed |
| START_STEP | Start Router Step | Router Sheet / Step Detail | QR scan or button | Timer starts |
| REVIEW_HOLD | Review Hold | Step Detail page | Decision: fix/reassign/escalate | Step resumed or escalated |
| QC_CHECK | QC Review | Step Detail / Evaluation form | Pass/Fail + remarks | QC result recorded |
| TECH_REVIEW | Technical Review | Step Detail page | Assessment + decision | Technical guidance provided |
| QUALITY_DECISION | Quality Decision | Die Check page | Decision per cutter | Decisions recorded |
| CONFIRM_TRANSFER | Confirm Transfer | Location Transfers page | Transfer confirmation | Bit at new location |
| PREPARE_DISPATCH | Prepare Dispatch | Dispatch page | Packaging confirmation | Ready for shipping |
| MAKE_DECISION | Decision Required | Custom modal/form | Decision + notes | Decision recorded |
| ACKNOWLEDGE | Acknowledge | Notification page | Click acknowledge | Info received |
| REWORK | Start Rework | WO Detail | Rework plan | New steps added |
| ASSIGN_OPERATOR | Assign Operator | Planner/WO page | Select operator | Operator assigned |

### 5.5 Workflow Events

| Event Code | Description | Actions Created |
|-----------|-------------|-----------------|
| BIT_RECEIVED | New bit registered/backloaded | INSPECT_BIT → Inspector |
| INSPECTION_ACCEPTED | Inspection passed | ADD_TO_PLAN → Planner |
| INSPECTION_REJECTED | Inspection failed | MAKE_DECISION → Technical Lead |
| ADDED_TO_PLAN | Bit in planner | ACKNOWLEDGE → Manager (info) |
| WO_RELEASED | WO created from planner | TRANSFER_BIT → Operator, APPROVE_WO → Manager |
| TRANSFER_CONFIRMED | Bit physically moved | ACKNOWLEDGE → Planner |
| WO_APPROVED | Manager approved WO | START_STEP → Operator, PRINT_RELEASE → Production Lead |
| WO_REJECTED | Manager rejected WO | MAKE_DECISION → Planner |
| STEP_COMPLETED | Router step done | (Next step auto-available) |
| STEP_ON_HOLD | Step put on hold | REVIEW_HOLD → Supervisor |
| STEP_WAITING_QC | Step needs QC | QC_CHECK → QC Inspector |
| STEP_WAITING_APPROVAL | Step needs approval | APPROVE → Manager |
| STEP_WAITING_TECH | Step needs tech review | TECH_REVIEW → Technical Lead |
| ALL_STEPS_DONE | All router steps complete | CONFIRM_TRANSFER → Operator |
| QC_PASSED | QC approved the WO | PREPARE_DISPATCH → Dispatch |
| QC_FAILED | QC rejected the WO | REWORK → Production Lead |
| WO_COMPLETED | WO fully done | ACKNOWLEDGE → Management |
| WO_DELETED | WO deleted | REPLAN → Planner (or TRANSFER_BIT if reversal) |
| CEREBRO_WARNING | Cerebro device detected | TECH_REVIEW → Technical Team |
| DIE_CHECK_WAITING | Cutter needs quality decision | QUALITY_DECISION → QC Manager |
| GRN_POSTED | Goods received | ACKNOWLEDGE → Warehouse (info) |
| SPECIAL_INSTRUCTION | Critical instruction active | TECH_REVIEW → Named person |

---

## 6. USER ROLES IN THE SYSTEM

| Role | Typical Actions | Example Users |
|------|----------------|---------------|
| RECEIVING_INSPECTOR | INSPECT_BIT | Receiving staff |
| PLANNER | ADD_TO_PLAN, REPLAN, release bits | Planning team |
| PRODUCTION_MANAGER | APPROVE_WO, REVIEW_HOLD | Department managers |
| PRODUCTION_LEAD | PRINT_RELEASE, ASSIGN_OPERATOR | Shift supervisors |
| OPERATOR | START_STEP, TRANSFER_BIT | Floor workers |
| QC_INSPECTOR | QC_CHECK, QUALITY_DECISION | Quality team |
| TECHNICAL_LEAD | TECH_REVIEW, MAKE_DECISION | Engineers |
| DISPATCH | PREPARE_DISPATCH | Shipping team |
| MANAGEMENT | ACKNOWLEDGE (info only) | Plant managers |

---

## 7. UI REQUIREMENTS

### 7.1 Action Center (replaces Notification List)
- **My Actions** tab: pending actions assigned to me, grouped by type
- **Team Actions** tab: pending actions for my role/team
- **History** tab: completed actions with timestamps, who did what
- Each action card shows: what to do, deadline, priority, "Go" button to the right page
- Blocked actions shown grayed out with "Waiting for: [action description]"
- Overdue actions highlighted red with escalation warning

### 7.2 Dashboard Widgets
- "5 WOs awaiting your approval" → click → filtered action list
- "3 bits need transfer" → click → Location Transfers with queue
- "2 steps on hold" → click → filtered hold review list
- Per-role dashboard showing only relevant action counts

### 7.3 Bell Dropdown (enhanced)
- Show pending actions (not just notifications)
- Action-type buttons instead of generic "Open"
- Count shows pending ACTIONS, not just unread notifications

### 7.4 Inline Actions on Entity Pages
- WO Detail page: show pending actions for this WO
- Drill Bit Detail: show pending actions for this bit
- Router Step Detail: show pending actions for this step

---

## 8. EXISTING SYSTEM ARCHITECTURE

### 8.1 Key Django Apps
- `apps/workorders/` — Drill bits, WOs, router sheets, evaluations, planner
- `apps/notifications/` — Current notification system
- `apps/accounts/` — Users, roles, permissions
- `apps/sales/` — Accounts (12 business units that drive WO numbering)
- `apps/inventory/` — Items, stock, GRN
- `apps/hr/` — Employees, competency matrix

### 8.2 Key Models for Workflow
- `DrillBit` — status: RECEIVED, IN_EVALUATION, IN_STOCK, IN_PRODUCTION, etc.
- `WorkOrder` — status: PENDING, RELEASED, ACTIVE, IN_PROGRESS, QC_PENDING, COMPLETED, etc.
- `RouterSheetEntry` — step_status: PENDING, IN_PROGRESS, PAUSED, ON_HOLD, SKIPPED, COMPLETED
- `ProductionPlanEntry` — status: PLANNED, PENDING_RELEASE, RELEASED, WO_CREATED, REMOVED, CANCELLED
- `CutterEvaluationMatrix` — status: DRAFT, IN_PROGRESS, COMPLETED, APPROVED
- `ReceivingInspection` — result: PENDING, ACCEPTED, REJECTED, CONDITIONAL
- `Location` — physical locations (Receiving Area, WIP Bay 1, Evaluation Area, FG Warehouse, etc.)
- `BitEvent` — audit trail of all lifecycle events (TRANSFER, RELEASED_TO_PROD, WO_CANCELLED, NOTE)
- `Account` — business unit (LSTK, ARAMCO, UR, L3, L4, etc.) that determines WO numbering and routing

### 8.3 Current User Model
- Django's built-in User with `is_staff` for supervisors, `is_superuser` for admins
- `apps/accounts/models.py` has `Role` and `Permission` models
- `apps/hr/models.py` has `Employee` model with `position` FK
- No formal role-to-notification-routing exists

### 8.4 Frontend Patterns
- HTMX for partial page updates and polling (notifications poll every 10s)
- Alpine.js for client-side reactivity (modals, toggles, forms)
- Tailwind CSS for styling with dark mode support
- No build step — CDN-loaded
- Toast notifications for success/error feedback
- Audio beep (AudioContext) for new notifications

---

## 9. WHAT WE NEED FROM THE CONSULTATION

1. **Redesign the workflow action model** — validate the proposed architecture, suggest improvements
2. **Design the Action Center page** — UI/UX for the main action management page
3. **Design notification routing** — how to map events → actions → roles → specific users
4. **Design dependency management** — how to handle action chains (A must complete before B)
5. **Design escalation** — time-based escalation rules, who gets escalated to
6. **Design the integration points** — where in the existing code to hook the workflow engine
7. **Suggest a phased implementation plan** — what to build first, what can wait

---

## 10. FILES INCLUDED IN THIS ZIP

### Models
- `apps/workorders/models.py` — All workflow models (DrillBit, WorkOrder, RouterSheetEntry, MasterProcess, etc.)
- `apps/notifications/models.py` — Notification, NotificationTemplate, Task, FormRevision
- `apps/accounts/models.py` — User extensions, Role, Permission
- `apps/sales/models.py` — Account (business units)

### Views (workflow-related)
- `apps/workorders/views_jobcard.py` — Main workflow views (WO detail, router sheet, step detail, all APIs)
- `apps/workorders/views_receiving.py` — Receiving dock views
- `apps/workorders/views_drillbit.py` — Drill bit lifecycle views
- `apps/notifications/views.py` — Notification views
- `apps/notifications/services.py` — notify() service

### Templates (key workflow pages)
- `templates/workorders/workorder_detail_enhanced.html` — WO detail page
- `templates/workorders/router_sheet.html` — Router sheet (step stepper)
- `templates/workorders/router_step_detail.html` — Individual step work page
- `templates/workorders/release_paper.html` — Release paper
- `templates/workorders/location_transfers.html` — Bit transfer page
- `templates/workorders/production_planner.html` — Production planner
- `templates/workorders/floor_board.html` — Production floor board
- `templates/workorders/operator_home.html` — Operator portal
- `templates/workorders/operator_step_view.html` — Mobile operator step view
- `templates/workorders/receiving_dashboard.html` — Receiving dock dashboard
- `templates/notifications/notification_list.html` — Current notification list
- `templates/notifications/partials/bell_fragment.html` — Bell dropdown

### URLs
- `apps/workorders/urls.py` — All workflow URL patterns
- `apps/notifications/urls.py` — Notification URL patterns

### Configuration
- `CLAUDE.md` — Full project documentation (very detailed, 3000+ lines)
- `ardt_fms/settings.py` — Django settings

---

## 11. KEY CONSTRAINTS

1. **No WebSocket/Redis** — stick with HTMX polling (upgradeable later)
2. **SQLite database** — no Postgres-specific features
3. **No frontend build step** — Alpine.js + HTMX + Tailwind CDN
4. **Single server** — runs on localhost:8001, will move to Linux server
5. **Small team** — ~20 users total, 5-10 active at any time
6. **Must be backwards compatible** — existing notifications should still work during migration
