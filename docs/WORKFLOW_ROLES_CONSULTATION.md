# Workflow Roles Design Problem — Consultation Request

## Date: April 3, 2026
## For: AI Agent Review
## From: ARDT Operational System development team

---

## THE PROBLEM

We implemented a Workflow Engine (Phase 1) with 10 hardcoded abstract roles for action routing:

```python
class WorkflowRole(models.TextChoices):
    RECEIVING_INSPECTOR = "RECEIVING_INSPECTOR"
    PLANNER             = "PLANNER"
    PRODUCTION_MANAGER  = "PRODUCTION_MANAGER"
    PRODUCTION_LEAD     = "PRODUCTION_LEAD"
    OPERATOR            = "OPERATOR"
    QC_INSPECTOR        = "QC_INSPECTOR"
    TECHNICAL_LEAD      = "TECHNICAL_LEAD"
    DISPATCH            = "DISPATCH"
    MANAGEMENT          = "MANAGEMENT"
    SYSTEM_ADMIN        = "SYSTEM_ADMIN"
```

The project owner (Eng. Ramzi Kassab, Supervisor / Acting Operations Manager) identified these problems:

### Problem 1: Where does the GM fit?
The General Manager doesn't fit neatly into any of these. "MANAGEMENT" is too vague — the GM needs to see everything but also needs specific approvals that a Plant Manager or Operations Director might not need.

### Problem 2: One person, multiple overlapping roles
Eng. Ramzi is:
- A **Supervisor** (PRODUCTION_LEAD) — reviews holds, assigns operators
- The **System Admin** (SYSTEM_ADMIN) — configures workflow rules
- The **Acting Operations Manager** — approves WOs, makes strategic decisions
- Sometimes acts as **Technical Lead** — technical reviews on special bits

He shares the "Supervisor" title with another person who may NOT need system admin access or operations approval authority.

### Problem 3: The system already has richer role/position data
The existing system has THREE overlapping role systems:
1. **Organization > Positions** — HR job titles (20+ positions like "Senior Machinist", "QC Inspector Level 2", "Brazing Operator")
2. **Users & Access > Roles** — Django permission groups (controls page access)
3. **Workflow Roles** — The new 10 abstract categories (controls action routing)

This creates confusion: "Where do I assign someone? Which system controls what?"

### Problem 4: Too rigid
10 enum choices can't cover all real-world scenarios:
- Field Engineers (visit rigs, report back)
- Sales team (need visibility into production status)
- Drivers (need dispatch notifications)
- Security guards (need entry/exit logging)
- Customer representatives (need read-only status updates)
- External auditors (temporary access)

---

## WHAT EXISTS IN THE SYSTEM

### Organization Positions (apps/hr/models.py → apps/organization/models.py)
```python
class Position(models.Model):
    name = CharField(max_length=200)         # "Senior Machinist", "QC Inspector Level 2"
    department = ForeignKey(Department)       # Production, Quality, Maintenance, etc.
    description = TextField()
    level = IntegerField()                   # Seniority level
    is_active = BooleanField()
```
Currently ~20+ positions defined.

### Employee (apps/hr/models.py)
```python
class Employee(models.Model):
    user = OneToOneField(User)
    employee_id = CharField()
    position = ForeignKey(Position)          # Links employee to their position
    department = ForeignKey(Department)
    status = CharField()                     # ACTIVE, ON_LEAVE, RESIGNED, etc.
```

### Django Roles (apps/accounts/models.py)
```python
class Role(models.Model):
    name = CharField()                       # "Production Team", "QC Team", "Admin"
    permissions = ManyToManyField(Permission) # Django permissions
    description = TextField()
```
Users can be assigned to multiple Django Roles which control page access.

### NEW: Workflow Roles (apps/notifications/models.py)
```python
class UserWorkflowRole(models.Model):
    user = ForeignKey(User)
    role = CharField(choices=WorkflowRole.choices)  # One of 10 hardcoded values
    is_active = BooleanField()
    is_available = BooleanField()  # For attendance/availability
```
This is what we're questioning — is this the right approach?

### Workflow Rules (apps/notifications/models.py)
```python
class WorkflowRule(models.Model):
    trigger_event = CharField(choices=WorkflowEvent.choices)
    assign_to_role = CharField(choices=WorkflowRole.choices)  # ← Routes to this role
    notif_recipients_role = CharField(choices=WorkflowRole.choices)
    # ... action_type, deadlines, escalation, etc.
```
Rules reference WorkflowRole to determine WHO gets the action/notification.

---

## QUESTIONS FOR CONSULTATION

1. **Should we keep WorkflowRole as a hardcoded enum or make it a DB model?**
   - Enum: simple, fast, but rigid — can't add new roles without code deploy
   - DB model: flexible, admin can create new roles, but needs more complex UI

2. **Should we link Positions to Workflow Roles?**
   - e.g., Position "QC Inspector Level 2" → automatically gets WorkflowRole "QC_INSPECTOR"
   - This means the Position defines what workflow actions someone receives
   - But one person can have responsibilities beyond their position title

3. **Should we merge/simplify the 3 role systems?**
   - Option A: Keep all 3 separate (positions=HR, roles=access, workflow=routing) — clear separation but confusing
   - Option B: Make Position the single source — position determines both access AND workflow routing
   - Option C: Keep Django Roles for access, but make Workflow Roles dynamic (DB model linked to Positions)

4. **How to handle the "supervisor with admin access" case?**
   - One person needs workflow actions for PRODUCTION_LEAD + SYSTEM_ADMIN + PRODUCTION_MANAGER
   - Another person with same title (Supervisor) only needs PRODUCTION_LEAD
   - Should this be per-user override or position-based?

5. **How to handle the GM / Director level?**
   - They need visibility into everything but shouldn't receive every operator-level action
   - They need specific high-level actions (strategic approvals, budget decisions)
   - Suggestion: a "visibility" concept separate from "action routing"?

---

## OUR CURRENT LEANING

Make WorkflowRole a **DB model** instead of an enum:
```python
class WorkflowRoleDefinition(models.Model):
    code = CharField(unique=True)      # "QC_INSPECTOR", "GM", "FIELD_ENGINEER"
    name = CharField()                 # "QC Inspector", "General Manager"
    description = TextField()
    positions = ManyToManyField(Position, blank=True)  # Auto-assign to these positions
    can_see_all_actions = BooleanField(default=False)   # GM/Director visibility
    is_active = BooleanField()
```

Then `UserWorkflowRole.role` becomes a FK to this model instead of a CharField with choices.

But we want your opinion before changing the architecture.

---

## FILES INCLUDED

- `apps/notifications/models.py` — WorkflowRole enum, UserWorkflowRole, WorkflowRule, WorkflowAction
- `apps/notifications/workflow_engine.py` — dispatch_event(), role resolution logic
- `apps/notifications/views.py` — Action Center, Role Assignment views
- `apps/hr/models.py` — Employee, Position (via FK)
- `apps/accounts/models.py` — User model, Role, Permission
- `apps/organization/models.py` — Department, Position models
- `templates/notifications/workflow_roles.html` — Current role assignment UI
- `templates/notifications/workflow_settings.html` — Settings page showing rules + role coverage
- `docs/WORKFLOW_ENGINE_MASTER_BRIEF.md` — Original architecture design document
