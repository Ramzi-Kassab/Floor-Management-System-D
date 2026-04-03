# IAM Redesign Instruction — ARDT FMS
## For: Claude Code Agent
## Priority: Execute in strict order. Do not skip steps.

---

## CONTEXT — WHY THIS INSTRUCTION EXISTS

Phase 1 built a `WorkflowRole` enum with 10 hardcoded values and a `UserWorkflowRole`
model. This approach is wrong for these reasons:

1. A hardcoded enum cannot represent a real organization. You cannot add "General Manager"
   or "Field Engineer" without a code deploy.
2. "WorkflowRole" creates confusion because the system already has a `Role` model in
   `apps/accounts/models.py` that controls page/feature access. Two things called "Role"
   doing different jobs is a design failure.
3. The same position title does not mean the same access. Two "Sales Account Lead" users
   serve different clients and must receive different notifications. A "Supervisor" can
   hold acting management responsibilities while another supervisor with the same title does
   not. The enum cannot express this.
4. The existing system already has `Position` (org structure), `Role` + `Permission`
   (access control), and `UserRole` with `expires_at` (temporary assignments) — all in
   `apps/accounts/models.py` and `apps/organization/models.py`. These were completely
   ignored in Phase 1. The new design must connect to what exists.

This instruction replaces the misaligned parts. Everything else built in Phase 1
(`WorkflowAction`, `WorkflowRule`, `WorkflowEvent`, `ActionType`, `dispatch_event()`,
`complete_action()`) stays and is not touched.

---

## STEP 1 — REMOVE THESE EXACTLY (nothing else)

### 1.1 In `apps/notifications/models.py` — DELETE these two classes entirely:

```
class WorkflowRole(models.TextChoices):   ← DELETE (lines ~385–397)
class UserWorkflowRole(models.Model):     ← DELETE (lines ~399–430)
```

### 1.2 In `apps/notifications/models.py` — CHANGE these fields on existing models:

On `WorkflowRule` model, replace:
```python
# REMOVE these three fields:
assign_to_role       = CharField(max_length=50, choices=WorkflowRole.choices, blank=True)
escalate_to_role     = CharField(max_length=50, choices=WorkflowRole.choices, blank=True)
notif_recipients_role= CharField(max_length=50, choices=WorkflowRole.choices, blank=True)
```
With (FK versions — added after WorkflowCapability model is created in Step 2):
```python
assign_to_capability        = FK('WorkflowCapability', null=True, blank=True,
                                  related_name='rules_assigned')
escalate_to_capability      = FK('WorkflowCapability', null=True, blank=True,
                                  related_name='rules_escalation')
notif_recipients_capability = FK('WorkflowCapability', null=True, blank=True,
                                  related_name='rules_notification')
```

On `WorkflowAction` model, replace:
```python
# REMOVE:
assigned_role = CharField(max_length=50, choices=WorkflowRole.choices, blank=True)
```
With:
```python
assigned_capability = FK('WorkflowCapability', null=True, blank=True,
                          related_name='actions')
```

### 1.3 In `apps/notifications/workflow_engine.py` — REMOVE:

- The import of `WorkflowRole` and `UserWorkflowRole` from models
- The `get_available_users_for_role(role: str, ...)` function — it will be replaced
- Any reference to `UserWorkflowRole.objects.filter(...)` in `get_pending_actions_for_user()`
- Any reference to `rule.assign_to_role` or `rule.notif_recipients_role`
  or `rule.escalate_to_role` — these fields no longer exist

### 1.4 In `apps/notifications/views.py` — REMOVE:

- `WorkflowRoleAssignmentView` class (the old role assignment page)
- `api_workflow_role_assign` function
- `api_workflow_role_remove` function
- `api_workflow_role_toggle` function
- All imports of `WorkflowRole` and `UserWorkflowRole`
- In `WorkflowSettingsView.get_context_data()`: remove the role coverage stats block
  that iterates over `WorkflowRole.choices`

### 1.5 In `apps/notifications/urls.py` — REMOVE:

- URL pattern for `workflow_roles` (the old assignment page)
- URL patterns for `api_workflow_role_assign`, `api_workflow_role_remove`,
  `api_workflow_role_toggle`

### 1.6 Templates — DELETE these files entirely:

- `templates/notifications/workflow_roles.html`

### 1.7 Write and run the migration:

```bash
python manage.py makemigrations notifications --name="remove_workflow_role_enum"
python manage.py migrate
```

If the migration cannot drop `user_workflow_roles` table because it has data,
use `DROP TABLE IF EXISTS user_workflow_roles;` in a RunSQL step — the table was
empty (0 records confirmed in Phase 1 test).

---

## STEP 2 — BUILD THE REPLACEMENT

### 2.1 Add `WorkflowCapability` to `apps/notifications/models.py`

```python
class WorkflowCapability(models.Model):
    """
    Replaces the hardcoded WorkflowRole enum.
    A Capability defines a type of workflow work — who receives which actions
    and notifications from the workflow engine.

    Examples: QC_INSPECTOR, GENERAL_MANAGER, SALES_ACCOUNT_LEAD, FIELD_ENGINEER

    Stored in DB so admins can add new capabilities without code deploys.
    Linked to Positions so that assigning a position auto-grants the right
    capabilities. Per-user overrides are handled in UserCapability.
    """

    code        = CharField(max_length=50, unique=True,
                            help_text='Uppercase code, e.g. QC_INSPECTOR')
    name        = CharField(max_length=100)
    name_ar     = CharField(max_length=100, blank=True)
    description = TextField(blank=True)

    # Which org positions automatically carry this capability.
    # When a user is assigned a Position, they auto-receive all capabilities
    # linked to that Position via this M2M. (Sync is done by signal — see Step 4.)
    positions   = ManyToManyField(
        'organization.Position',
        blank=True,
        related_name='default_capabilities',
        help_text='Users assigned to these positions automatically receive this capability'
    )

    # Visibility flag — user sees ALL workflow actions across all types
    # (management overview, not task-level items).
    # Does not mean they receive every operator action — they see a summary view.
    has_full_visibility = BooleanField(default=False,
                                       help_text='GM / Director level — full overview dashboard')

    # System admin flag — can access Workflow Settings configuration pages
    is_system_admin     = BooleanField(default=False,
                                       help_text='Can configure workflow rules and capabilities')

    is_active   = BooleanField(default=True)
    order       = IntegerField(default=0,
                                help_text='Display order in admin UI')

    created_at  = DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'workflow_capabilities'
        ordering  = ['order', 'name']
        verbose_name = 'Workflow Capability'
        verbose_name_plural = 'Workflow Capabilities'

    def __str__(self):
        return f'{self.code} — {self.name}'
```

### 2.2 Add `UserCapability` to `apps/notifications/models.py`

```python
class UserCapability(models.Model):
    """
    Assigns a WorkflowCapability to a User.

    Source of assignment:
    - is_position_derived=True  → auto-assigned because of User.position
                                   (created/updated by sync signal)
    - is_position_derived=False → manually granted by admin
                                   (e.g. Ramzi gets PRODUCTION_MANAGER on top
                                    of his PRODUCTION_LEAD from his position,
                                    as Acting Operations Manager)

    Data scope:
    - account_scope empty  → capability applies to ALL accounts
    - account_scope set    → capability only applies to those accounts
                              (used for Sales Account Lead: Person A → Aramco only,
                               Person B → Halliburton only — same position, same
                               capability, different data scope)
    """

    user       = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE,
                             related_name='capabilities')
    capability = ForeignKey(WorkflowCapability, on_delete=CASCADE,
                             related_name='user_assignments')

    # Source tracking
    is_position_derived = BooleanField(
        default=False,
        help_text='True = auto-assigned from position. False = manually granted.'
    )

    # Data scope — empty means all accounts
    account_scope = ManyToManyField(
        'sales.Account',
        blank=True,
        related_name='scoped_capabilities',
        help_text='Restrict this capability to specific accounts. '
                  'Leave empty for no restriction (all accounts).'
    )

    # Availability (attendance / Ramadan hours / leave)
    is_available = BooleanField(
        default=True,
        help_text='Uncheck to pause action routing to this user '
                  '(e.g. on leave, Ramadan reduced hours)'
    )

    # Temporal — for acting/delegation assignments
    expires_at  = DateTimeField(
        null=True, blank=True,
        help_text='Leave blank for permanent. Set for acting/delegation assignments.'
    )
    notes       = CharField(
        max_length=200, blank=True,
        help_text='e.g. "Acting Operations Manager — covers for Abdulaziz Al Buobaid"'
    )

    # Audit
    assigned_by = ForeignKey(settings.AUTH_USER_MODEL, on_delete=SET_NULL,
                              null=True, blank=True, related_name='granted_capabilities')
    assigned_at = DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_capabilities'
        unique_together = [('user', 'capability')]
        indexes = [
            # Used by engine on every dispatch — must be fast
            Index(fields=['capability', 'is_available', 'is_position_derived']),
        ]

    def __str__(self):
        scope = ' (scoped)' if self.account_scope.exists() else ''
        source = 'position' if self.is_position_derived else 'manual'
        return f'{self.user} → {self.capability.code}{scope} [{source}]'

    @property
    def is_active(self):
        """False if expired."""
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True
```

### 2.3 Extend `apps/organization/models.py` — add M2M to `Position`

In the existing `Position` model, add two fields (no other changes to Position):

```python
class Position(models.Model):
    # ... ALL EXISTING FIELDS STAY UNCHANGED ...

    # NEW: Default roles for this position (access control)
    # When a user is assigned this Position, they auto-receive these Roles
    default_roles = ManyToManyField(
        'accounts.Role',
        blank=True,
        related_name='default_for_positions',
        help_text='Users assigned to this position automatically receive these roles'
    )

    # NEW: Default capabilities for this position (workflow routing)
    # When a user is assigned this Position, they auto-receive these Capabilities
    default_capabilities = ManyToManyField(
        'notifications.WorkflowCapability',
        blank=True,
        related_name='default_for_positions',
        help_text='Users assigned to this position automatically receive these workflow capabilities'
    )
```

Note: `WorkflowCapability.positions` (the M2M defined in Step 2.1) and
`Position.default_capabilities` (this field) are the SAME relationship accessed
from different sides. Use only ONE of them in the actual migration — define the M2M
on `WorkflowCapability.positions` pointing to `organization.Position`, and access
it via `position.default_capabilities.all()` using the `related_name`. Do not
create a duplicate M2M — Django handles both directions from one definition.

### 2.4 Extend `apps/accounts/models.py` — extend `UserRole`

In the existing `UserRole` through-model, add these fields (no other changes):

```python
class UserRole(models.Model):
    # ... ALL EXISTING FIELDS STAY (user, role, assigned_at, assigned_by,
    #                                expires_at, is_primary) ...

    # NEW: Track whether this role came from the position sync or was manually granted
    is_position_derived = BooleanField(
        default=False,
        help_text='True = auto-assigned from User.position. '
                  'False = manually granted by admin.'
    )

    # NEW: Data scope — empty means all accounts
    account_scope = ManyToManyField(
        'sales.Account',
        blank=True,
        related_name='scoped_user_roles',
        help_text='Restrict this role to specific accounts. Leave empty for no restriction.'
    )

    # NEW: Notes for acting/delegation assignments
    notes = CharField(
        max_length=200, blank=True,
        help_text='e.g. "Acting Ops Manager — temporary until 30/06/2026"'
    )
```

---

## STEP 3 — SEED DEFAULT CAPABILITIES

Create management command:
`apps/notifications/management/commands/seed_workflow_capabilities.py`

This command seeds `WorkflowCapability` records that map to the 10 old enum values,
plus adds the ones the enum was missing. It is idempotent — skip if code already exists.

Seed these capabilities (use `get_or_create(code=...)` for each):

```python
CAPABILITIES = [
    # code                    name                          full_vis  sys_admin
    ('RECEIVING_INSPECTOR',  'Receiving Inspector',          False,    False),
    ('PLANNER',              'Production Planner',           False,    False),
    ('PRODUCTION_MANAGER',   'Production Manager',           False,    False),
    ('PRODUCTION_LEAD',      'Production Lead / Supervisor', False,    False),
    ('OPERATOR',             'Floor Operator',               False,    False),
    ('QC_INSPECTOR',         'QC Inspector',                 False,    False),
    ('TECHNICAL_LEAD',       'Technical Lead',               False,    False),
    ('DISPATCH',             'Dispatch / Shipping',          False,    False),
    ('MANAGEMENT',           'Management',                   True,     False),
    ('SYSTEM_ADMIN',         'System Administrator',         True,     True),
    # New ones the enum could not express:
    ('GENERAL_MANAGER',      'General Manager',              True,     False),
    ('SALES_ACCOUNT_LEAD',   'Sales Account Lead',           False,    False),
    ('FIELD_ENGINEER',       'Field Engineer',               False,    False),
    ('MAINTENANCE',          'Maintenance Technician',       False,    False),
    ('DRIVER',               'Driver / Logistics',           False,    False),
]
```

After creating capabilities, also update the seeded `WorkflowRule` records to point
to the new `WorkflowCapability` FKs:

```python
# Map old role CharField value → new WorkflowCapability code (same values)
for rule in WorkflowRule.objects.all():
    if rule.assign_to_role:
        cap = WorkflowCapability.objects.filter(code=rule.assign_to_role).first()
        if cap:
            rule.assign_to_capability = cap
    if rule.notif_recipients_role:
        cap = WorkflowCapability.objects.filter(code=rule.notif_recipients_role).first()
        if cap:
            rule.notif_recipients_capability = cap
    if rule.escalate_to_role:
        cap = WorkflowCapability.objects.filter(code=rule.escalate_to_role).first()
        if cap:
            rule.escalate_to_capability = cap
    rule.save()
```

---

## STEP 4 — POSITION SYNC SIGNAL

Create `apps/accounts/signals.py` (new file):

```python
"""
Signal: when a User's position changes, sync their roles and workflow capabilities.

Rules:
- Auto-create UserRole records (is_position_derived=True) for each role
  in new_position.default_roles.all()
- Auto-create UserCapability records (is_position_derived=True) for each
  capability in new_position.default_capabilities.all()
- Remove old is_position_derived=True records that no longer apply
  (i.e. from the previous position that the user no longer holds)
- NEVER touch records with is_position_derived=False (manually granted)
- If position is set to None (user removed from position), remove all
  is_position_derived=True records

Function signature:
    def sync_user_access_from_position(user, old_position=None, new_position=None)

Connect to: post_save on User, filtering for changes to the position field.
Also expose as a standalone callable for manual use:
    from apps.accounts.signals import sync_user_access_from_position
    sync_user_access_from_position(user, new_position=position_instance)
"""
```

---

## STEP 5 — UPDATE THE WORKFLOW ENGINE

In `apps/notifications/workflow_engine.py`, replace `get_available_users_for_role()`
with `get_available_users_for_capability()`:

```python
def get_available_users_for_capability(capability: 'WorkflowCapability',
                                        account=None,
                                        exclude=None) -> list:
    """
    Returns list of User objects who:
    - Have an active UserCapability for this capability
    - Are currently available (is_available=True)
    - Have not expired (expires_at is null OR expires_at > now)
    - If account is provided: account_scope is empty (all accounts)
      OR account is in their account_scope

    Falls back to users with is_system_admin capability if no users found.
    """
    from apps.notifications.models import UserCapability
    from django.utils import timezone

    qs = UserCapability.objects.filter(
        capability=capability,
        is_available=True,
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    ).select_related('user')

    if account is not None:
        # Include users with no scope restriction OR users scoped to this account
        qs = qs.filter(
            Q(account_scope__isnull=True) | Q(account_scope=account)
        ).distinct()

    users = [uca.user for uca in qs]

    if exclude:
        users = [u for u in users if u != exclude]

    return users
```

Update all call sites in `dispatch_event()` and `check_and_escalate_overdue_actions()`
to use `get_available_users_for_capability(rule.assign_to_capability, account=context.get('account'))`.

Update `get_pending_actions_for_user()` to query by `UserCapability` instead of
`UserWorkflowRole`:

```python
def get_pending_actions_for_user(user) -> QuerySet:
    """
    Returns pending WorkflowActions for a user.
    Includes:
    1. Actions directly assigned to this user
    2. Queue actions (is_queue_action=True, not yet claimed) for any capability
       the user holds that is currently active and available
    """
    from apps.notifications.models import UserCapability, WorkflowAction
    from django.utils import timezone

    user_capability_ids = UserCapability.objects.filter(
        user=user,
        is_available=True,
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    ).values_list('capability_id', flat=True)

    return WorkflowAction.objects.filter(
        is_blocked=False,
        status__in=['PENDING', 'CLAIMED'],
    ).filter(
        Q(assigned_to=user) |
        Q(
            is_queue_action=True,
            assigned_capability_id__in=user_capability_ids,
            claimed_by__isnull=True,
        )
    ).select_related('assigned_to', 'assigned_capability', 'source_rule')
```

---

## STEP 6 — BUILD THE NEW WORKFLOW CAPABILITIES ADMIN PAGE

This replaces the deleted `workflow_roles.html` page.
URL: `/notifications/settings/workflow/capabilities/`
Named: `notifications:workflow_capabilities`
Sidebar link text: "Workflow Capabilities" (update the sidebar link that previously
said "Workflow Roles")

### Page layout — three sections:

**Section A: Capabilities table**
List of all `WorkflowCapability` records with columns:
`Code | Name | Linked Positions | Active Users | Full Visibility | System Admin | Active`

Each row has: Edit button (inline HTMX), Toggle active, Delete (if no active users).

"Add Capability" button opens an inline form (HTMX) with fields:
`code, name, name_ar, description, positions (multi-select), has_full_visibility,
is_system_admin, order`

**Section B: User Assignments (per capability)**
When a capability row is expanded (Alpine.js toggle):
Show a table of users who have this capability with columns:
`User | Source (Position / Manual) | Account Scope | Available | Expires | Notes | Actions`

"Grant to user" button — inline form (HTMX):
`user (select), account_scope (multi-select, optional), expires_at (optional),
notes (optional)`
Sets `is_position_derived=False` on the created `UserCapability`.

"Remove" button only shown for `is_position_derived=False` records.
Position-derived records show a note: "Auto-assigned from position [position name] —
remove by changing the user's position or editing the position's default capabilities."

**Section C: Position → Capability mapping**
A matrix view showing which positions auto-grant which capabilities.
Rows = Positions (from Organization), Columns = Capabilities.
Checkboxes — clicking a checkbox adds/removes the capability from
`Position.default_capabilities`.
Saves via HTMX PATCH. Shows a "sync now" button that calls
`sync_user_access_from_position()` for all active users (for bulk re-sync after
position mapping changes).

---

## STEP 7 — WRITE AND RUN ALL MIGRATIONS

```bash
python manage.py makemigrations notifications --name="add_workflow_capability_models"
python manage.py makemigrations accounts --name="add_userrole_scope_fields"
python manage.py makemigrations organization --name="add_position_default_capabilities"
python manage.py migrate
python manage.py seed_workflow_capabilities --confirm
```

Verify:
```bash
python manage.py shell -c "
from apps.notifications.models import WorkflowCapability, UserCapability
from apps.notifications.workflow_engine import dispatch_event
print('Capabilities:', WorkflowCapability.objects.count())
print('UserCapabilities:', UserCapability.objects.count())
# Dry run test
result = dispatch_event('WO_RELEASED', actor=None, context={'wo_number': 'TEST-001',
    'serial': '12345678', 'actor_name': 'Test'}, dry_run=True)
print('Dry run rules matched:', len(result))
"
```

---

## WHAT DOES NOT CHANGE

These were built correctly in Phase 1 and must not be touched:

- `WorkflowAction` model — keep exactly as-is (only `assigned_role` CharField
  is replaced by `assigned_capability FK` per Step 1.2 above)
- `WorkflowRule` model — keep, only the three role fields change to FK
- `WorkflowEvent` enum — keep exactly as-is
- `ActionType` enum — keep exactly as-is
- `dispatch_event()` logic — keep, only role lookup function changes
- `complete_action()` — keep exactly as-is
- `check_and_escalate_overdue_actions()` — keep, only role lookup changes
- `Notification` model + `action_type` field — keep exactly as-is
- All 24 seeded `WorkflowRule` records — keep (data updated in Step 3 to use FK)
- `WorkflowSettingsView` — keep, only remove the role coverage stats block
- Action Center page and templates — keep exactly as-is
- Bell fragment enhancements — keep exactly as-is
- Feature flag `WORKFLOW_ENGINE_ACTIVE` — keep

---

## DEFINITION OF DONE

Phase 1 replacement is complete when:

1. `python manage.py check` passes with zero errors
2. `WorkflowRole` enum and `UserWorkflowRole` model do not exist anywhere in the codebase
   (grep confirms: `grep -r "WorkflowRole\|UserWorkflowRole" apps/` returns nothing)
3. `WorkflowCapability` table exists with 15 seeded records
4. `UserCapability` table exists
5. `Position` model has `default_capabilities` M2M
6. `UserRole` model has `is_position_derived`, `account_scope`, `notes` fields
7. Dry run of `dispatch_event('WO_RELEASED', ...)` matches 2 rules and returns planned
   actions (no users assigned yet is fine — table is empty until users are mapped)
8. `/notifications/settings/workflow/capabilities/` page loads without error
9. The Position × Capability matrix in Section C of that page renders all seeded positions
   and capabilities as a grid
10. Sidebar link "Workflow Roles" is renamed to "Workflow Capabilities"
