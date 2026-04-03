# ARDT FMS — Workflow Engine & Notification System: Master Redesign Brief
## For: Claude Code Agent (CMD)
## Compiled: April 3, 2026
## Status: Final — Ready for Implementation

---

## READING ORDER FOR THIS DOCUMENT

1. Section 1 — What exists today (read carefully, do NOT break anything)
2. Section 2 — The core problem
3. Section 3 — Full architecture design (the target state)
4. Section 4 — Position Dashboards (new requirement)
5. Section 5 — Admin configuration page
6. Section 6 — Phased implementation plan (follow this order exactly)
7. Section 7 — Migration & cleanup of hardcoded notify() calls
8. Section 8 — Constraints and confirmed decisions
9. Section 9 — Files to touch (with caution notes)

---

## SECTION 1: WHAT EXISTS TODAY — DO NOT BREAK

### 1.1 Current Notification Model (`apps/notifications/models.py`)

```python
class Notification(models.Model):
    recipient = ForeignKey(User)           # who receives it
    actor     = ForeignKey(User, nullable) # who triggered it
    title     = CharField(max_length=200)
    message   = TextField()
    priority  = CharField(choices=[LOW, NORMAL, HIGH, URGENT])
    entity_type = CharField(max_length=50) # "WorkOrder", "DrillBit", etc.
    entity_id   = BigIntegerField(nullable)
    action_url  = CharField(max_length=500)
    is_read     = BooleanField(default=False)
    read_at     = DateTimeField(nullable)
    created_at  = DateTimeField(auto_now_add=True)
```

### 1.2 Current Task Model (`apps/notifications/models.py`)
This model exists but is COMPLETELY UNUSED. It will become our WorkflowAction:

```python
class Task(models.Model):
    title, description
    assigned_to = FK(User)
    assigned_by = FK(User, nullable)
    due_date, reminder_date
    status = [PENDING, IN_PROGRESS, COMPLETED, CANCELLED]
    priority = [LOW, NORMAL, HIGH, URGENT]
    entity_type, entity_id
    completed_at, created_at, updated_at
```

### 1.3 Current Notification Service (`apps/notifications/services.py`)
```python
def notify(actor, verb, target=None, recipients=None, priority="NORMAL",
           action_url="", title=None, message=None, entity_type="", entity_id=None):
    # recipients can be: "all", QuerySet, list, single User, or None
    # Creates Notification records via bulk_create()
```

### 1.4 Current Notification Points — ALL 24 HARDCODED CALLS
These are scattered across views. They must continue working until the new engine is tested.
Do NOT remove or modify any of these during Phase 1 or Phase 2. Only remove in Phase 3+.

| # | Location | Event | Current recipients |
|---|----------|-------|-------------------|
| 1 | views_jobcard.py | Evaluation completed | All |
| 2 | views_jobcard.py | Route auto-updated | All |
| 3 | views_jobcard.py | All router steps done | All |
| 4 | views_jobcard.py | Bit released + WO created | All |
| 5 | views_jobcard.py | Release request (no WO yet) | All |
| 6 | views_jobcard.py | Transaction confirmed | All |
| 7 | views_jobcard.py | WO approved | All |
| 8 | views_jobcard.py | WO sent to QC | All |
| 9 | views_jobcard.py | QC passed | All |
| 10 | views_jobcard.py | QC failed | All |
| 11 | views_jobcard.py | WO completed | All |
| 12 | views_jobcard.py | WO deleted | All |
| 13 | views_jobcard.py | Release confirmed at dest | All |
| 14 | views_jobcard.py | Transfer + WO created | All |
| 15 | views_receiving.py | Receiving inspection done | All |
| 16 | views_receiving.py | PDC evaluation completed | All |
| 17 | views_jobcard.py | Die check quality decision | All (broadcast) |
| 18 | views_jobcard.py | Step on hold | All |
| 19 | views_jobcard.py | Step waiting QC/approval/tech | All |
| 20 | views_jobcard.py | Step resumed | Operator only |
| 21 | views_jobcard.py | WO started | All |
| 22 | views_jobcard.py | WO status change | All |
| 23 | views_receiving.py | Cerebro device warning | All |
| 24 | views_jobcard.py | GRN posted | All |

### 1.5 Existing Templates to Preserve
- `templates/notifications/notification_list.html` — will be replaced by Action Center
- `templates/notifications/partials/bell_fragment.html` — will be enhanced
- `templates/workorders/operator_home.html` — will gain Action widget
- `templates/workorders/receiving_dashboard.html` — will gain Action widget
- `templates/workorders/floor_board.html` — will gain Action widget
- `templates/workorders/production_planner.html` — will gain Action widget

### 1.6 URL namespace
- Notification URLs are under `apps/notifications/urls.py`
- Workorder URLs are under `apps/workorders/urls.py` with namespace `workorders`
- The bell fragment polls at a URL in `apps/notifications/urls.py` every 10 seconds

---

## SECTION 2: THE CORE PROBLEM

The current system collapses 3 separate concerns into one hardcoded `notify()` call in each view:
- **Layer 1 — Event**: what happened ("WO was released")
- **Layer 2 — Rule**: what should happen in response ("notify manager, create transfer task for operator")
- **Layer 3 — Output**: the actual notifications and actions created

This means:
1. ALL notifications go to ALL users — no role-based routing
2. No action type — recipient doesn't know what they're supposed to DO
3. No tracking — notification read ≠ action taken
4. No dependencies — action B doesn't wait for action A
5. No escalation — if nobody acts, nothing happens
6. One event creates one notification — but may need multiple people doing different things
7. Behavior change requires code deploy — cannot be configured by admin
8. Position dashboards have no data source — operators/inspectors/planners have no "my work" view

---

## SECTION 3: FULL ARCHITECTURE DESIGN

### 3.1 Three-Layer Separation (THE FUNDAMENTAL PRINCIPLE)

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: EVENTS (always fired by code — NOT configurable)      │
│  dispatch_event(WorkflowEvent.WO_RELEASED, entity=wo, actor=user)│
│  This is just a signal. Zero business logic here.               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: RULES (stored in DB — configurable by admin)          │
│  WorkflowRule: "When WO_RELEASED, create TRANSFER_BIT action    │
│  for OPERATOR role, deadline 4h, escalate to SUPERVISOR"        │
│  WorkflowRule: "When WO_RELEASED, notify PRODUCTION_MANAGER     │
│  with title template 'WO {wo_number} needs your approval'"      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: OUTPUT (created by engine — WorkflowAction records    │
│  and/or Notification records, depending on rule type)           │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 WorkflowEvent Enum

```python
class WorkflowEvent(models.TextChoices):
    # Receiving
    BIT_RECEIVED          = "BIT_RECEIVED",         "Bit Received / Backloaded"
    INSPECTION_ACCEPTED   = "INSPECTION_ACCEPTED",   "Receiving Inspection: Accepted"
    INSPECTION_REJECTED   = "INSPECTION_REJECTED",   "Receiving Inspection: Rejected"
    INSPECTION_CONDITIONAL= "INSPECTION_CONDITIONAL","Receiving Inspection: Conditional"
    CEREBRO_DETECTED      = "CEREBRO_DETECTED",      "Cerebro Device Detected"

    # Planning
    ADDED_TO_PLAN         = "ADDED_TO_PLAN",         "Bit Added to Production Plan"
    WO_RELEASED           = "WO_RELEASED",           "Work Order Released"
    TRANSFER_CONFIRMED    = "TRANSFER_CONFIRMED",    "Bit Transfer Confirmed"

    # Approval
    WO_APPROVED           = "WO_APPROVED",           "Work Order Approved"
    WO_REJECTED           = "WO_REJECTED",           "Work Order Rejected"
    WO_DELETED            = "WO_DELETED",            "Work Order Deleted"

    # Production
    WO_STARTED            = "WO_STARTED",            "Work Started on WO"
    STEP_COMPLETED        = "STEP_COMPLETED",        "Router Step Completed"
    STEP_ON_HOLD          = "STEP_ON_HOLD",          "Step Put On Hold"
    STEP_WAITING_QC       = "STEP_WAITING_QC",       "Step Waiting for QC"
    STEP_WAITING_APPROVAL = "STEP_WAITING_APPROVAL", "Step Waiting for Approval"
    STEP_WAITING_TECH     = "STEP_WAITING_TECH",     "Step Waiting for Tech Review"
    STEP_RESUMED          = "STEP_RESUMED",          "Step Resumed"
    ALL_STEPS_DONE        = "ALL_STEPS_DONE",        "All Router Steps Completed"
    DIE_CHECK_DECISION    = "DIE_CHECK_DECISION",    "Die Check Needs Quality Decision"
    SPECIAL_INSTRUCTION   = "SPECIAL_INSTRUCTION",  "Critical Special Instruction Active"

    # QC & Completion
    WO_SENT_TO_QC         = "WO_SENT_TO_QC",        "WO Sent to QC"
    QC_PASSED             = "QC_PASSED",             "QC Passed"
    QC_FAILED             = "QC_FAILED",             "QC Failed — Rework Needed"
    WO_COMPLETED          = "WO_COMPLETED",          "Work Order Completed"

    # Inventory
    GRN_POSTED            = "GRN_POSTED",            "GRN Posted"
    EVALUATION_COMPLETED  = "EVALUATION_COMPLETED",  "Bit Evaluation Completed"
    ROUTE_UPDATED         = "ROUTE_UPDATED",         "Router Route Auto-Updated"
```

### 3.3 ActionType Enum

```python
class ActionType(models.TextChoices):
    INSPECT_BIT        = "INSPECT_BIT",       "Start Receiving Inspection"
    ADD_TO_PLAN        = "ADD_TO_PLAN",        "Add Bit to Production Plan"
    TRANSFER_BIT       = "TRANSFER_BIT",       "Transfer Bit (Physical Move)"
    APPROVE_WO         = "APPROVE_WO",         "Review & Approve Work Order"
    REJECT_WO          = "REJECT_WO",          "Review & Reject Work Order"
    PRINT_RELEASE      = "PRINT_RELEASE",      "Print Release Paper"
    START_STEP         = "START_STEP",         "Start First Router Step"
    REVIEW_HOLD        = "REVIEW_HOLD",        "Review Hold & Decide Next Action"
    QC_CHECK           = "QC_CHECK",           "Perform QC Check"
    TECH_REVIEW        = "TECH_REVIEW",        "Technical Review Required"
    QUALITY_DECISION   = "QUALITY_DECISION",   "Quality Decision on Cutters"
    CONFIRM_TRANSFER   = "CONFIRM_TRANSFER",   "Confirm Bit Transfer to Destination"
    PREPARE_DISPATCH   = "PREPARE_DISPATCH",   "Prepare Bit for Shipping"
    MAKE_DECISION      = "MAKE_DECISION",      "Decision Required"
    ACKNOWLEDGE        = "ACKNOWLEDGE",        "Acknowledge / Information Only"
    REWORK             = "REWORK",             "Plan & Start Rework"
    ASSIGN_OPERATOR    = "ASSIGN_OPERATOR",    "Assign Operator to WO"
    REPLAN             = "REPLAN",             "Re-plan Bit in Production Planner"
    REMOVE_DEVICE      = "REMOVE_DEVICE",      "Remove Cerebro Device Before Processing"
```

### 3.4 Role Enum (maps to assign_role on rules and UserRole)

```python
class WorkflowRole(models.TextChoices):
    RECEIVING_INSPECTOR  = "RECEIVING_INSPECTOR",  "Receiving Inspector"
    PLANNER              = "PLANNER",              "Planner"
    PRODUCTION_MANAGER   = "PRODUCTION_MANAGER",   "Production Manager"
    PRODUCTION_LEAD      = "PRODUCTION_LEAD",      "Production Lead / Supervisor"
    OPERATOR             = "OPERATOR",             "Floor Operator"
    QC_INSPECTOR         = "QC_INSPECTOR",         "QC Inspector"
    TECHNICAL_LEAD       = "TECHNICAL_LEAD",       "Technical Lead"
    DISPATCH             = "DISPATCH",             "Dispatch / Shipping"
    MANAGEMENT           = "MANAGEMENT",           "Management (Info Only)"
    SYSTEM_ADMIN         = "SYSTEM_ADMIN",         "System Administrator"
```

### 3.5 UserRole Assignment Model (new — solves the 130-user routing problem)

```python
class UserWorkflowRole(models.Model):
    """
    Maps a User to a WorkflowRole. One user can have multiple roles.
    This is separate from Django permissions — it's purely for workflow routing.
    """
    user         = ForeignKey(User, on_delete=CASCADE, related_name='workflow_roles')
    role         = CharField(max_length=50, choices=WorkflowRole.choices)
    is_active    = BooleanField(default=True)
    # Availability — no formal shifts but attendance varies (e.g. Ramadan hours)
    # If False, this user will NOT receive new role-based actions/notifications
    is_available = BooleanField(default=True)
    notes        = CharField(max_length=200, blank=True)  # "Ramadan hours", "On leave", etc.
    assigned_by  = ForeignKey(User, on_delete=SET_NULL, null=True)
    assigned_at  = DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_workflow_roles'
        unique_together = [('user', 'role')]
        indexes = [
            Index(fields=['role', 'is_active', 'is_available'])  # used on every dispatch
        ]
```

**How routing works with this model:**
When the engine needs to find users for role=OPERATOR:
```python
users = UserWorkflowRole.objects.filter(
    role='OPERATOR',
    is_active=True,
    is_available=True
).select_related('user')
```
If no available users found for a role, the action is created but assigned_to=None
and flagged for escalation to SYSTEM_ADMIN immediately.

### 3.6 WorkflowRule Model (the configurable layer — stored in DB, edited by admin)

```python
class WorkflowRule(models.Model):
    """
    Admin-configurable rules that define what happens for each workflow event.
    Replaces all 24 hardcoded notify() calls once migrated.
    """

    class RuleType(models.TextChoices):
        ACTION        = "ACTION",       "Create Action Task Only"
        NOTIFICATION  = "NOTIFICATION", "Send Notification Only"
        BOTH          = "BOTH",         "Create Action + Send Notification"

    # Identity
    name        = CharField(max_length=200)
    description = TextField(blank=True)

    # Trigger
    trigger_event   = CharField(max_length=50, choices=WorkflowEvent.choices)
    trigger_filter  = JSONField(default=dict, blank=True,
                                help_text='Optional filter e.g. {"account_code": "ARAMCO"}')

    # Rule type
    rule_type = CharField(max_length=20, choices=RuleType.choices, default=RuleType.BOTH)

    # --- ACTION FIELDS (used when rule_type includes ACTION) ---
    action_type        = CharField(max_length=50, choices=ActionType.choices, blank=True)
    assign_to_role     = CharField(max_length=50, choices=WorkflowRole.choices, blank=True)
    assign_to_user     = ForeignKey(User, null=True, blank=True,
                                    help_text="Override: assign to specific user instead of role")
    action_url_pattern = CharField(max_length=500, blank=True,
                                   help_text='URL pattern, e.g. /work-orders/{wo_id}/')
    action_description_template = CharField(max_length=500, blank=True,
                                            help_text='e.g. "Transfer {serial} from {from_loc} to {to_loc}"')
    deadline_hours     = IntegerField(null=True, blank=True,
                                      help_text="Hours until action is overdue (blank = no deadline)")
    # Queue vs direct assignment
    is_queue_action    = BooleanField(default=False,
                                      help_text="If True, any available user with the role can claim it")

    # --- ESCALATION FIELDS ---
    escalate_after_hours = IntegerField(null=True, blank=True)
    escalate_to_role     = CharField(max_length=50, choices=WorkflowRole.choices, blank=True)
    escalate_to_user     = ForeignKey(User, null=True, blank=True,
                                       related_name='escalation_rules')

    # --- NOTIFICATION FIELDS (used when rule_type includes NOTIFICATION) ---
    notif_title_template   = CharField(max_length=200, blank=True,
                                        help_text='e.g. "WO {wo_number} needs approval"')
    notif_message_template = TextField(blank=True,
                                        help_text='Supports {wo_number}, {serial}, {actor_name}, etc.')
    notif_recipients_role  = CharField(max_length=50, choices=WorkflowRole.choices, blank=True)
    notif_priority         = CharField(max_length=20, choices=Notification.Priority.choices,
                                        default='NORMAL')

    # --- DEPENDENCY FIELDS ---
    # This rule's action is blocked until the listed sibling rules' actions are complete.
    # Store as JSON list of WorkflowRule PKs to avoid circular FK issues.
    depends_on_rule_ids = JSONField(default=list, blank=True,
                                     help_text="PKs of sibling rules whose actions must complete first")

    # Control
    is_active = BooleanField(default=True)
    order     = IntegerField(default=0,
                              help_text="Execution order when multiple rules fire for same event")

    class Meta:
        db_table  = 'workflow_rules'
        ordering  = ['trigger_event', 'order']
        indexes   = [Index(fields=['trigger_event', 'is_active', 'order'])]

    def __str__(self):
        return f"[{self.trigger_event}] {self.name}"
```

### 3.7 WorkflowAction Model (evolved from existing Task model — DO NOT delete Task, migrate it)

```python
class WorkflowAction(models.Model):
    """
    Evolved from the existing Task model.
    Represents a concrete action that a specific user (or role queue) must take.
    
    MIGRATION NOTE: Rename table 'tasks' → 'workflow_actions', 
    preserve all existing Task fields, add new fields below.
    """

    class Status(models.TextChoices):
        PENDING     = "PENDING",      "Pending"
        CLAIMED     = "CLAIMED",      "Claimed (queue actions only)"
        IN_PROGRESS = "IN_PROGRESS",  "In Progress"
        COMPLETED   = "COMPLETED",    "Completed"
        ESCALATED   = "ESCALATED",    "Escalated"
        CANCELLED   = "CANCELLED",    "Cancelled"
        EXPIRED     = "EXPIRED",      "Expired (deadline passed)"

    # --- EXISTING Task FIELDS (keep as-is) ---
    title         = CharField(max_length=200)
    description   = TextField(blank=True)
    assigned_to   = ForeignKey(User, null=True, blank=True,
                                related_name='workflow_actions')
    assigned_by   = ForeignKey(User, null=True, related_name='created_workflow_actions')
    due_date      = DateTimeField(null=True, blank=True)   # was deadline, keep name
    status        = CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    priority      = CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    entity_type   = CharField(max_length=50, blank=True)
    entity_id     = BigIntegerField(null=True, blank=True)
    completed_at  = DateTimeField(null=True, blank=True)
    created_at    = DateTimeField(auto_now_add=True)
    updated_at    = DateTimeField(auto_now=True)

    # --- NEW FIELDS ---
    # Trigger context
    trigger_event   = CharField(max_length=50, choices=WorkflowEvent.choices, blank=True)

    # Action definition
    action_type     = CharField(max_length=50, choices=ActionType.choices, blank=True)
    action_url      = CharField(max_length=500, blank=True)

    # Role-based assignment (for queue actions)
    assigned_role   = CharField(max_length=50, choices=WorkflowRole.choices, blank=True)
    is_queue_action = BooleanField(default=False)  # True = any role member can claim
    claimed_by      = ForeignKey(User, null=True, blank=True,
                                  related_name='claimed_workflow_actions')
    claimed_at      = DateTimeField(null=True, blank=True)

    # Source rule (which WorkflowRule created this)
    source_rule     = ForeignKey('WorkflowRule', null=True, blank=True,
                                  on_delete=SET_NULL, related_name='actions')

    # Dependencies (denormalized for performance)
    depends_on_ids  = JSONField(default=list,
                                 help_text="PKs of WorkflowAction records that must complete first")
    is_blocked      = BooleanField(default=False)  # True if any dependency is incomplete

    # Escalation
    escalate_after_hours = IntegerField(null=True, blank=True)
    escalate_to          = ForeignKey(User, null=True, blank=True,
                                       related_name='escalation_targets')
    escalated_at         = DateTimeField(null=True, blank=True)

    # Completion tracking
    completed_by    = ForeignKey(User, null=True, blank=True,
                                  related_name='completed_workflow_actions')
    result_data     = JSONField(default=dict, blank=True)

    # Linked notification
    notification    = ForeignKey('Notification', null=True, blank=True,
                                  on_delete=SET_NULL)

    class Meta:
        db_table = 'workflow_actions'   # renamed from 'tasks'
        ordering = ['is_blocked', 'due_date', '-priority']
        indexes  = [
            Index(fields=['assigned_to', 'status', 'is_blocked']),
            Index(fields=['assigned_role', 'status', 'is_blocked']),
            Index(fields=['entity_type', 'entity_id']),
            Index(fields=['trigger_event', 'status']),
        ]
```

### 3.8 The Workflow Engine (`apps/notifications/workflow_engine.py` — NEW FILE)

```python
"""
Workflow Engine — core dispatch function.
Call dispatch_event() from any view or service when a workflow transition occurs.
The engine reads WorkflowRule records from the DB and creates WorkflowAction
and/or Notification records accordingly.

USAGE:
    from apps.notifications.workflow_engine import dispatch_event, WorkflowEvent

    # In your view, after the transition:
    dispatch_event(
        event=WorkflowEvent.WO_RELEASED,
        actor=request.user,
        context={
            'wo': work_order,          # the WorkOrder instance
            'bit': work_order.drill_bit,
            'wo_id': work_order.pk,
            'wo_number': work_order.wo_number,
            'serial': work_order.drill_bit.serial_number,
            'from_loc': work_order.drill_bit.current_location,
        }
    )
"""

def dispatch_event(event: str, actor, context: dict) -> list:
    """
    Core engine function.
    Returns list of created WorkflowAction/Notification PKs for testing.
    
    Steps:
    1. Load all active WorkflowRules for this event, ordered by 'order'
    2. Apply trigger_filter if any (skip rule if context doesn't match)
    3. For each rule:
       a. Resolve recipients/assignees from role (using UserWorkflowRole, is_available=True)
       b. Render title/message/url/description templates using context dict
       c. Create WorkflowAction record if rule_type in [ACTION, BOTH]
       d. Create Notification record if rule_type in [NOTIFICATION, BOTH]
       e. Resolve dependencies (find sibling actions from same dispatch batch)
       f. Set is_blocked=True if depends_on_ids is not empty and deps not yet done
    4. Return created objects
    """
    pass  # Claude Code implements this
```

**Template rendering:** Use Python's `str.format_map(context_dict)` for simple placeholder
replacement. Context dict should always include:
`wo_number, serial, actor_name, actor_role, bit_size, account_code, from_loc, to_loc, step_name, hold_reason`
(any unused keys are ignored).

**Availability check:**
```python
def get_available_users_for_role(role: str) -> QuerySet:
    return User.objects.filter(
        workflow_roles__role=role,
        workflow_roles__is_active=True,
        workflow_roles__is_available=True
    )
    # If result is empty → return escalation user or SYSTEM_ADMIN users
```

### 3.9 Escalation Mechanism (no Celery — uses existing bell polling)

Escalation runs PASSIVELY during the existing 10-second bell poll:

```python
# In the bell fragment view (notifications/views.py):
def bell_fragment(request):
    # Existing: get unread notifications
    # NEW: also check for overdue actions and trigger escalation
    check_and_escalate_overdue_actions(request.user)
    ...

def check_and_escalate_overdue_actions(current_user):
    """
    Called on each bell poll. Checks for actions that:
    - Have status=PENDING or CLAIMED
    - Have due_date in the past
    - Have escalate_after_hours set and that time has passed
    - Have NOT yet been escalated (escalated_at is null)
    
    For each overdue action:
    1. Set status=ESCALATED, escalated_at=now
    2. Create new WorkflowAction for the escalate_to user (copy of original)
    3. Send URGENT Notification to escalate_to user
    4. Highlight original action in red (done via the ESCALATED status in template)
    """
    pass
```

This means escalation fires at most once every 10 seconds per active user,
which is perfectly acceptable for a 130-user system with no real-time requirements.

---

## SECTION 4: POSITION DASHBOARDS

This is a new requirement. Every role/position must have a dashboard that shows
not just notifications but their actual pending WORK from the workflow engine.

### 4.1 Positions That Need Dashboards

| Role | Existing page | Enhancement needed |
|------|---------------|--------------------|
| Receiving Inspector | `receiving_dashboard.html` | Add: Pending INSPECT_BIT actions |
| Planner | `production_planner.html` | Add: ADD_TO_PLAN, REPLAN actions widget |
| Production Manager | (none — needs new page) | APPROVE_WO queue, overdue WOs |
| Production Lead / Supervisor | `floor_board.html` | REVIEW_HOLD actions, ASSIGN_OPERATOR tasks |
| Floor Operator | `operator_home.html` | TRANSFER_BIT, START_STEP, CONFIRM_TRANSFER queue |
| QC Inspector | (none — needs new page) | QC_CHECK queue, QUALITY_DECISION items |
| Technical Lead | (none — needs new page) | TECH_REVIEW, MAKE_DECISION, REMOVE_DEVICE |
| Dispatch | (none — needs new page) | PREPARE_DISPATCH items |
| Management | (none — needs new page) | ACKNOWLEDGE items, summary stats |

### 4.2 Dashboard Widget Component (reusable)

Each dashboard gets a standard "My Actions" widget that can be included in any template:

```html
{% include "notifications/partials/action_widget.html" with role="OPERATOR" %}
```

The widget shows:
- Count of pending actions
- Each action as a card: action type badge, description, deadline countdown, priority indicator
- "Claim" button (for queue actions) or "Go" button (for directly assigned)
- Blocked actions shown grayed with "Waiting for: [description]"
- Overdue actions shown with red border and escalation warning

### 4.3 New Pages Required

**`/dashboard/manager/`** — Production Manager dashboard
- Pending WO approvals (APPROVE_WO actions) with WO details
- Active WOs in production (count by status)
- Overdue actions across all roles (supervisor overview)
- Recent completions

**`/dashboard/qc/`** — QC Inspector dashboard
- Pending QC checks queue (QC_CHECK actions)
- Quality decisions needed (QUALITY_DECISION for die checks)
- QC history (pass/fail rate)

**`/dashboard/technical/`** — Technical Lead dashboard
- Tech reviews needed (TECH_REVIEW)
- Critical decisions (MAKE_DECISION)
- Cerebro removal warnings (REMOVE_DEVICE)

**`/dashboard/dispatch/`** — Dispatch dashboard
- Bits ready for shipping (PREPARE_DISPATCH)
- WOs completed waiting dispatch

**`/dashboard/management/`** — Management overview
- ACKNOWLEDGE items (info-only notifications)
- Summary stats: bits in production, WOs by status, today's completions

### 4.4 Enhance Existing Pages

**`operator_home.html`** — Add action widget at top:
- "You have 3 actions" banner
- Each action card with direct link to the relevant page (Transfer form, Step start, etc.)
- Queue actions show "Claim" button

**`receiving_dashboard.html`** — Add:
- "Bits awaiting inspection" from INSPECT_BIT actions
- Link directly to the inspection form pre-filled with the bit's serial

**`production_planner.html`** — Add:
- "Bits waiting to be planned" from ADD_TO_PLAN actions
- "Bits to re-plan" from REPLAN actions (deleted WOs)

**`floor_board.html`** — Add:
- Holds count with REVIEW_HOLD links
- Steps waiting tech review or QC with direct links

---

## SECTION 5: ADMIN CONFIGURATION PAGE

### 5.1 Access Control
- Only users with `WorkflowRole.SYSTEM_ADMIN` can access workflow configuration
- This is a separate role from operations roles (manager, supervisor, etc.)
- URL: `/settings/workflow/`
- Separate from Django admin — custom views in `apps/notifications/`

### 5.2 Pages Needed

**`/settings/workflow/`** — Workflow Rules Manager
- List all WorkflowEvents in a collapsible tree
- Under each event, show all rules (active/inactive)
- Each rule shows: name, type (ACTION/NOTIFICATION/BOTH), assigned_role, deadline, order
- Toggle active/inactive per rule (HTMX inline toggle)
- Add/Edit/Delete rules
- "Test" button: simulate an event and preview what actions/notifications would fire (dry run)

**`/settings/workflow/rules/create/`** — Rule creation form
- Event selector (dropdown of all WorkflowEvents with descriptions)
- Rule type selector (ACTION / NOTIFICATION / BOTH)
- Conditional fields: show action fields only if type includes ACTION
- Template preview: live preview of rendered title/message with sample context
- Dependency selector: multi-select of sibling rules for same event

**`/settings/workflow/roles/`** — User Role Assignments
- Table of all users with their assigned WorkflowRoles
- Toggle availability per user (is_available flag)
- Bulk assign role to multiple users
- Show "no users assigned" warning for any role that has rules pointing to it

**`/settings/workflow/seed/`** — Default Rules
- "Load default rules" button — seeds all 27 events with the default behavior
  (equivalent to the current hardcoded notify() behavior but as DB records)
- "Reset to defaults" — clears custom rules and re-seeds defaults
- Shows diff: "You have 5 custom rules that differ from defaults"

### 5.3 Seed Data (default rules — these replace the 24 hardcoded calls)

The seed command `python manage.py seed_workflow_rules` creates WorkflowRule records
that exactly replicate the current hardcoded behavior. See Section 7 for the full mapping.

---

## SECTION 6: PHASED IMPLEMENTATION PLAN

### PHASE 1 — Foundation (do this first, nothing breaks)
**Goal: models exist, engine exists, old notify() still works, new engine runs alongside**

1. **Create migration: new models**
   - Add `WorkflowEvent`, `ActionType`, `WorkflowRole` enums to `apps/notifications/models.py`
   - Rename `Task` table to `workflow_actions`, add all new fields
   - Add `WorkflowRule` model
   - Add `UserWorkflowRole` model
   - Add `action_type` CharField to existing `Notification` model
   - Run `makemigrations notifications` and `migrate`

2. **Create `apps/notifications/workflow_engine.py`**
   - `dispatch_event()` function
   - `get_available_users_for_role()` helper
   - `render_template()` helper (str.format_map with safe fallback)
   - `check_and_escalate_overdue_actions()` function
   - Unit-testable: accepts a dry_run=True parameter that returns planned actions without saving

3. **Create seed command: `python manage.py seed_workflow_rules`**
   - Creates all 27 default WorkflowRule records replicating current behavior
   - Idempotent: skip if rule already exists (check by trigger_event + name)

4. **Add `check_and_escalate_overdue_actions()` call to bell poll view**
   - Lightweight — only runs for current user's role, not system-wide scan

5. **Tests**: write tests for dispatch_event() with dry_run=True for at least 5 key events

---

### PHASE 2 — Action Center UI (new pages, nothing removed yet)
**Goal: users can see and act on WorkflowActions. Old notification list still exists.**

1. **Action Center page: `/actions/`**
   - "My Actions" tab: actions assigned_to=request.user OR (assigned_role in user's roles AND is_queue_action=True AND status=PENDING)
   - "Team Actions" tab: all pending actions for user's roles
   - "History" tab: completed actions in last 30 days
   - Action card component with: type badge, description, deadline countdown, "Go"/"Claim" button
   - Filter by: action_type, status, priority
   - Empty state: "No pending actions — you're all clear"

2. **Enhanced bell dropdown**
   - Show pending WorkflowAction count (not just unread notification count)
   - Each item shows action_type badge + description + "Go" button (no more keyword matching)
   - "View All" now links to `/actions/` instead of `/notifications/`

3. **Position dashboard pages** (see Section 4):
   - `/dashboard/manager/`
   - `/dashboard/qc/`
   - `/dashboard/technical/`
   - `/dashboard/dispatch/`
   - Enhance existing: `operator_home.html`, `receiving_dashboard.html`, `production_planner.html`, `floor_board.html`

4. **Action widget partial**: `templates/notifications/partials/action_widget.html`

5. **User Role Assignment page**: `/settings/workflow/roles/`
   - Admin assigns WorkflowRoles to users, toggles availability

---

### PHASE 3 — Workflow Rules Admin + Wire Up Engine to Views
**Goal: admin can configure rules; engine fires on real events alongside old notify()**

1. **Workflow Rules Manager pages** (Section 5.2)
2. **Wire `dispatch_event()` into views** — ADD calls alongside existing notify() calls:
   - Do NOT remove notify() calls yet
   - Add dispatch_event() call immediately after each notify() call
   - Use a feature flag in settings: `WORKFLOW_ENGINE_ACTIVE = True`
   - Both systems run in parallel — duplicates are acceptable during testing

3. **Test each event** by comparing old notifications vs new WorkflowActions created

---

### PHASE 4 — Remove Hardcoded notify() Calls
**Goal: old system fully replaced. One source of truth.**

Only proceed when Phase 3 is confirmed working for all 24 events.

1. Remove all 24 hardcoded `notify()` calls from views
2. Remove any keyword-matching logic from `notification_list.html` and `bell_fragment.html`
3. Keep the `notify()` service function itself (it's still used by the engine internally)
4. Archive `templates/notifications/notification_list.html` → keep old URL redirecting to `/actions/`
5. Final cleanup: remove the feature flag from settings

---

### PHASE 5 — Polish & Escalation Hardening
1. Escalation stress test: verify bell-poll-based escalation fires correctly
2. Availability management: add UI for marking users unavailable (Ramadan hours, leave)
3. Notification history page (read-only archive of all notifications, searchable)
4. Dashboard analytics (completions per day, average response time per action type)

---

## SECTION 7: DEFAULT RULES SEED — EXACT MAPPING

These 24+ rules replicate the current hardcoded behavior exactly.
The seed command creates these as WorkflowRule records.

| Rule name | Event | Type | Action | Notif recipients | Priority |
|-----------|-------|------|--------|-----------------|----------|
| Evaluation completed | EVALUATION_COMPLETED | BOTH | ACKNOWLEDGE (mgmt) | MANAGEMENT | HIGH |
| Route auto-updated | ROUTE_UPDATED | NOTIFICATION | — | PRODUCTION_LEAD | NORMAL |
| All steps done | ALL_STEPS_DONE | BOTH | CONFIRM_TRANSFER (operator) | PRODUCTION_LEAD | HIGH |
| Bit released — operator transfer | WO_RELEASED | ACTION | TRANSFER_BIT → OPERATOR | — | HIGH |
| Bit released — manager approval | WO_RELEASED | BOTH | APPROVE_WO → PROD_MANAGER | PRODUCTION_MANAGER | HIGH |
| Release request | WO_RELEASED | NOTIFICATION | — | PRODUCTION_LEAD | HIGH |
| Transaction confirmed | TRANSFER_CONFIRMED | NOTIFICATION | — | PLANNER | HIGH |
| WO approved | WO_APPROVED | BOTH | START_STEP → OPERATOR | OPERATOR | HIGH |
| WO sent to QC | WO_SENT_TO_QC | BOTH | QC_CHECK → QC_INSPECTOR | QC_INSPECTOR | HIGH |
| QC passed | QC_PASSED | BOTH | PREPARE_DISPATCH → DISPATCH | DISPATCH | HIGH |
| QC failed | QC_FAILED | BOTH | REWORK → PROD_LEAD | PRODUCTION_LEAD | URGENT |
| WO completed | WO_COMPLETED | NOTIFICATION | — | MANAGEMENT | HIGH |
| WO deleted — replan | WO_DELETED | BOTH | REPLAN → PLANNER | PLANNER | HIGH |
| Release confirmed | TRANSFER_CONFIRMED | NOTIFICATION | — | PRODUCTION_LEAD | HIGH |
| Transfer + WO created | WO_RELEASED | NOTIFICATION | — | ALL (broadcast) | HIGH |
| Receiving inspection done | INSPECTION_ACCEPTED | BOTH | ADD_TO_PLAN → PLANNER | PLANNER | HIGH |
| Receiving inspection rejected | INSPECTION_REJECTED | BOTH | MAKE_DECISION → TECH_LEAD | TECHNICAL_LEAD | HIGH |
| PDC evaluation completed | EVALUATION_COMPLETED | NOTIFICATION | — | PRODUCTION_MANAGER | HIGH |
| Die check decision needed | DIE_CHECK_DECISION | BOTH | QUALITY_DECISION → QC_INSPECTOR | QC_INSPECTOR | HIGH |
| Step on hold | STEP_ON_HOLD | BOTH | REVIEW_HOLD → PROD_LEAD | PRODUCTION_LEAD | HIGH |
| Step waiting review | STEP_WAITING_QC | BOTH | QC_CHECK → QC_INSPECTOR | QC_INSPECTOR | HIGH |
| Step waiting approval | STEP_WAITING_APPROVAL | BOTH | APPROVE_WO → PROD_MANAGER | PRODUCTION_MANAGER | HIGH |
| Step waiting tech | STEP_WAITING_TECH | BOTH | TECH_REVIEW → TECH_LEAD | TECHNICAL_LEAD | HIGH |
| Step resumed | STEP_RESUMED | NOTIFICATION | — | OPERATOR (assigned) | NORMAL |
| WO started | WO_STARTED | NOTIFICATION | — | PRODUCTION_LEAD | NORMAL |
| WO status changed | WO_RELEASED | NOTIFICATION | — | PRODUCTION_MANAGER | NORMAL |
| Cerebro detected | CEREBRO_DETECTED | BOTH | REMOVE_DEVICE → TECH_LEAD | TECHNICAL_LEAD | URGENT |
| GRN posted | GRN_POSTED | NOTIFICATION | — | MANAGEMENT | URGENT |

---

## SECTION 8: CONSTRAINTS AND CONFIRMED DECISIONS

### 8.1 Technology
- Django 5.1, Python 3.11, SQLite (migration-ready for Postgres — no SQLite-specific features)
- HTMX for partial updates and polling (10s bell poll)
- Alpine.js for client-side reactivity
- Tailwind CSS (CDN, no build step)
- NO WebSocket, NO Celery, NO Redis — escalation via bell polling only

### 8.2 Confirmed Decisions (from consultation)
- **Shifts**: No formal shifts. Users have varying attendance (e.g. Ramadan shorter hours).
  Handle via `UserWorkflowRole.is_available` flag — admin can mark users unavailable.
  No automatic shift-awareness — manual availability management.
- **Escalation**: BOTH highlight red AND auto-notify escalation person.
  Implemented via bell-polling passive check (no background worker).
- **Workflow Rules admin access**: SYSTEM_ADMIN role only (dedicated role, not operations roles).
  Separate from Django `is_superuser` — can be assigned without full Django admin access.
- **Migration approach**: Feature-flag — build and test engine running in parallel with
  existing notify() calls (WORKFLOW_ENGINE_ACTIVE = True in settings).
  Only remove hardcoded calls in Phase 4 after full parallel testing confirms parity.
- **Transfer actions**: Queue model — TRANSFER_BIT action goes to the OPERATOR role queue.
  Any available operator can claim it. Direct assignment only when a specific user is
  set on the WorkflowRule's `assign_to_user` override field.
- **Scale**: 130 users, ~20-40 active concurrently. Bell poll optimization is required.
  Index on `(assigned_role, status, is_blocked)` is mandatory.

### 8.3 Backwards Compatibility
- `notify()` service function is NOT removed — it's used internally by the engine
- Existing `Notification` model is NOT removed — gains one new field (`action_type`)
- Existing `Task` model IS renamed to `WorkflowAction` — migration required
- All existing template URLs must continue working until Phase 4

---

## SECTION 9: FILES TO TOUCH (AND CAUTION NOTES)

### New files to create:
- `apps/notifications/workflow_engine.py` — dispatch_event(), helpers
- `apps/notifications/workflow_rules_views.py` — admin config pages
- `apps/notifications/workflow_roles_views.py` — user role assignment
- `apps/workorders/dashboard_views.py` — position dashboard pages
- `templates/notifications/action_center.html` — replaces notification_list
- `templates/notifications/partials/action_widget.html` — reusable widget
- `templates/notifications/partials/action_card.html` — single action card
- `templates/workorders/dashboard_manager.html`
- `templates/workorders/dashboard_qc.html`
- `templates/workorders/dashboard_technical.html`
- `templates/workorders/dashboard_dispatch.html`
- `apps/notifications/management/commands/seed_workflow_rules.py`
- `apps/notifications/management/commands/seed_workflow_roles.py`

### Files to modify:
- `apps/notifications/models.py` — add enums, evolve Task, add WorkflowRule, UserWorkflowRole, add action_type to Notification
- `apps/notifications/views.py` — add action center view, bell enhancement, check_and_escalate call
- `apps/notifications/urls.py` — add /actions/ and /settings/workflow/ routes
- `apps/workorders/urls.py` — add dashboard routes
- `templates/notifications/partials/bell_fragment.html` — show action counts, action-type buttons
- `templates/workorders/operator_home.html` — add action widget
- `templates/workorders/receiving_dashboard.html` — add action widget
- `templates/workorders/production_planner.html` — add action widget
- `templates/workorders/floor_board.html` — add action widget
- `ardt_fms/settings.py` — add WORKFLOW_ENGINE_ACTIVE = False (starts disabled, enable for testing)

### Files to modify in Phase 4 ONLY (remove hardcoded notify calls):
- `apps/workorders/views_jobcard.py` — 20 of the 24 hardcoded calls
- `apps/workorders/views_receiving.py` — 4 of the 24 hardcoded calls

### Files to NOT touch:
- Existing migration files
- `apps/workorders/models.py` — no changes needed to workflow models
- Any evaluation or BOM-related views

---

## SECTION 10: WHAT "DONE" LOOKS LIKE

When all phases are complete, the system works as follows:

1. A planner releases a bit → view calls `dispatch_event(WO_RELEASED, actor, context)`
2. Engine reads WorkflowRules for WO_RELEASED → finds 3 active rules
3. Engine creates:
   - WorkflowAction: TRANSFER_BIT, assigned_role=OPERATOR, is_queue_action=True, deadline=+4h
   - WorkflowAction: APPROVE_WO, assigned_to=[manager users], deadline=+8h, escalate_after=8h
   - Notification: sent to PRODUCTION_MANAGER role users with rendered title/message
4. Floor operator opens `operator_home.html` → sees "1 new action: Transfer bit 14414031"
5. Operator claims the transfer action → status=CLAIMED, claimed_by=operator
6. Operator goes to Location Transfers, confirms transfer → action completed via view signal
7. Manager opens their dashboard → sees APPROVE_WO card for this WO
8. Manager approves → action completed, engine fires WO_APPROVED event automatically
9. If manager doesn't act within 8h → next bell poll detects overdue, escalates to plant manager
10. System admin can change the deadline from 8h to 12h via `/settings/workflow/` without a code deploy

---

*Document compiled from: 2-session consultation covering initial brief (WORKFLOW_REDESIGN_PACKAGE.zip),
follow-up architectural analysis, and confirmed decisions from Ramzi Al-... (ARDT PDC Repair Supervisor / Acting Operations Manager).*
*All decisions are confirmed unless marked [TBD].*
