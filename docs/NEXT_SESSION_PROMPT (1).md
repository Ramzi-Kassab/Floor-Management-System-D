# Agent Instruction — Next Session
## Read this entire document before touching any file.

---

## STEP 0 — CONFLICT AND EXISTENCE CHECK (do this first, before any code)

Before executing any task below, answer these questions in writing and wait
for confirmation if any conflict is found:

1. **`fire_event()` location**: Is it in `apps/notifications/dispatch.py` or
   `apps/notifications/workflow_engine.py`? Show the exact function signature
   and the full exception handling block. Confirm whether exceptions are logged
   or silently swallowed.

2. **Existing logging**: Does `workflow_engine.py` already import and use a
   logger (`logging.getLogger`)? Show the current state before changing anything.

3. **`seed_workflow_rules.py`**: Open
   `apps/notifications/management/commands/seed_workflow_rules.py` and check
   whether it still imports `WorkflowRole`. Show the import block. Confirm
   whether running it would crash.

4. **`workflow_roles.html`**: Confirm this file still exists at
   `templates/notifications/workflow_roles.html`. Confirm no URL pattern or
   view references it anymore. Show the grep result:
   `grep -r "workflow_roles" apps/ templates/`

5. **Existing live test query**: Run this exact shell command and show the full
   output before doing anything else:
   ```
   python manage.py shell -c "
   from apps.notifications.models import WorkflowAction
   wa = WorkflowAction.objects.order_by('-created_at').first()
   if wa:
       print('trigger_event:', wa.trigger_event)
       print('assigned_to:', wa.assigned_to)
       print('assigned_role:', wa.assigned_role)
       print('status:', wa.status)
       print('is_blocked:', wa.is_blocked)
   else:
       print('NO WorkflowAction records exist yet')
   "
   ```

6. **Existing `fire_event()` call sites**: Run this and show the output:
   `grep -rn "fire_event\|dispatch_event" apps/workorders/ apps/notifications/`
   This confirms which views already have engine wiring and which do not.

7. **`notify()` call count**: Run this and show the count:
   `grep -rn "notify(" apps/workorders/ apps/inventory/ | grep -v "test\|#" | wc -l`
   And show the full list:
   `grep -rn "notify(" apps/workorders/ apps/inventory/ | grep -v "test\|#"`

8. **Conflict check — production planner**: Open
   `templates/workorders/production_planner.html` and check whether
   `action_widget.html` is already included anywhere in the file. Show the
   grep result before adding it.

9. **Conflict check — position dashboards**: Check whether any of these URLs
   already exist in any `urls.py`:
   `/dashboard/manager/`, `/dashboard/qc/`, `/dashboard/technical/`,
   `/dashboard/dispatch/`, `/dashboard/management/`
   Run: `grep -rn "dashboard/manager\|dashboard/qc\|dashboard/technical\|dashboard/dispatch\|dashboard/management" apps/`

10. **Conflict check — existing dashboard views**: Check whether
    `apps/workorders/dashboard_views.py` already exists. If it does, show its
    contents before creating anything new.

**If any conflict or unexpected state is found in steps 1–10, stop and report
it. Do not proceed until confirmed.**

---

## TASK 1 — Fix `fire_event()` Silent Failure (CRITICAL — do first)

**Why**: During Phase 3 parallel testing, if the engine fails silently you
cannot compare old vs new behavior. Silent failures make the parallel test
meaningless.

**What to do**:

Locate `fire_event()` (either in `apps/notifications/dispatch.py` or
`workflow_engine.py`). The current exception block must be changed from
silent swallow to logged failure. Replace whatever silent handling exists with:

```python
import logging
logger = logging.getLogger(__name__)

def fire_event(event: str, actor, context: dict) -> list:
    """
    Safe wrapper around dispatch_event().
    Catches all exceptions to prevent workflow failures from breaking
    user-facing views — but ALWAYS logs the full traceback so failures
    are visible in the Django log.
    Never returns None — returns empty list on failure.
    """
    try:
        return dispatch_event(event=event, actor=actor, context=context)
    except Exception as e:
        logger.error(
            "fire_event() failed for event=%s actor=%s context_keys=%s error=%s",
            event,
            getattr(actor, 'username', str(actor)),
            list(context.keys()),
            str(e),
            exc_info=True   # ← includes full traceback in log
        )
        return []
```

After making this change, verify the logger is configured in Django settings
to actually write to a file or console. Run:
```
python manage.py shell -c "
import logging
logger = logging.getLogger('apps.notifications.workflow_engine')
logger.error('TEST — fire_event logger is working')
print('Logger handlers:', logger.handlers)
print('Root handlers:', logging.getLogger().handlers)
"
```
Confirm the TEST message appears somewhere (console or log file).

---

## TASK 2 — Live End-to-End Role Routing Test (CRITICAL — do before Phase 3 continues)

**Why**: Everything in Phase 3 and Phase 4 depends on role-based routing
working correctly. This has not been confirmed with a live test yet.
A shell query of existing records is not enough — the event must be
triggered through the real UI so the actual view code fires.

### Step A — Pre-flight: check rules and role assignments first

Run this before touching the UI:

```python
python manage.py shell -c "
from apps.notifications.models import WorkflowAction, WorkflowRule
from apps.accounts.models import Role, UserRole

# 1. Show all WorkflowRules for WO_RELEASED
rules = WorkflowRule.objects.filter(trigger_event='WO_RELEASED', is_active=True)
print('=== Rules for WO_RELEASED ===')
for r in rules:
    print(f'  Rule: {r.name}')
    print(f'    assign_to_role: {r.assign_to_role}')
    print(f'    notif_recipients_role: {r.notif_recipients_role}')
    print(f'    action_type: {r.action_type}')

# 2. Show who is in those roles
print()
print('=== Users assigned to routing roles ===')
for r in rules:
    if r.assign_to_role_id:
        role = r.assign_to_role
        users = UserRole.objects.filter(
            role=role, is_available=True
        ).select_related('user')
        print(f'  Role {role.code}: {[ur.user.username for ur in users]}')

# 3. Count existing WO_RELEASED actions before the live test
print()
existing = WorkflowAction.objects.filter(trigger_event='WO_RELEASED').count()
print(f'=== Existing WO_RELEASED actions before test: {existing} ===')
"
```

If rules show `assign_to_role=None` for any rule — stop and fix the rule FK
before proceeding. Do not continue to Step B with broken rules.

If users list is empty for any role — report it. This is a data gap
not a code bug. The test can still proceed but assigned_to will be None.

### Step B — Live trigger through the UI (do NOT use the shell for this)

1. Open `http://localhost:8001/work-orders/planner/` in the browser
2. Find a WO that is currently in `PENDING` or `PLANNED` status
3. Release it through the normal UI release button — the same action a
   real planner would take
4. Do not simulate this with a shell command — the view code must fire
   so that `fire_event()` is called from the actual request/response cycle

### Step C — Query immediately after the UI release

Run this exact query right after the release:

```python
python manage.py shell -c "
from apps.notifications.models import WorkflowAction, Notification

# Check WorkflowActions created by the release
print('=== WorkflowActions for WO_RELEASED (last 5) ===')
actions = WorkflowAction.objects.filter(
    trigger_event='WO_RELEASED'
).order_by('-created_at')[:5]

if not actions:
    print('ERROR: NO WO_RELEASED actions found — fire_event() is not wired')
    print('Check that fire_event() is called in the release view')
else:
    for wa in actions:
        print('---')
        print(f'  action_type:    {wa.action_type}')
        print(f'  assigned_to:    {wa.assigned_to}')
        print(f'  assigned_role:  {wa.assigned_role}')
        print(f'  status:         {wa.status}')
        print(f'  is_blocked:     {wa.is_blocked}')
        print(f'  created_at:     {wa.created_at}')

# Confirm old notify() also fired (parallel running check)
print()
print('=== Recent Notifications for same event (parallel check) ===')
notifs = Notification.objects.order_by('-created_at')[:3]
for n in notifs:
    print(f'  [{n.created_at}] {n.title} -> {n.recipient}')
"
```

### Step D — Confirm the result

Report the outcome against these exact criteria:

| Check | Pass condition | Fail condition |
|-------|---------------|----------------|
| Actions created | At least 1 `WO_RELEASED` action exists | Zero records found |
| Role routing | `assigned_role` is not None OR `assigned_to` is a specific user | Both are None simultaneously |
| Not broadcast | `assigned_to` is one user (or None for queue) | `assigned_to` has multiple records for same event going to ALL users |
| Parallel running | At least 1 new `Notification` record also exists | notify() stopped firing |
| Dependency | At least 1 action has `is_blocked=True` (PRINT_RELEASE depends on TRANSFER+APPROVE) | All actions PENDING with no blocked ones |

**If any check fails**: Stop, report the failure with the exact output,
and do not proceed to Task 3 until it is fixed. Role routing failure
means Phase 4 (removing hardcoded notify() calls) is not safe.

**If users list was empty (from Step A) and assigned_to is None**:
This is expected — report which roles need user assignments. The admin
must assign real users to those roles via
`http://localhost:8001/notifications/settings/workflow/capabilities/`
before the engine can route to specific people.

---

## TASK 3 — Wire Remaining `fire_event()` Calls (Phase 3 completion)

**Why**: 19 of the 28 `notify()` call sites are not yet wired to the engine.
Two of them are entry-point events that must be wired before Phase 4 is safe.

**Wire these in priority order. For each one:**
1. Find the exact `notify()` call in the view
2. Add `fire_event()` call immediately AFTER the `notify()` call (not before,
   not replacing — after)
3. Build the context dict from the variables already available in that view
4. Do NOT remove the `notify()` call

**Priority A — wire these first (entry points and safety):**

| Event | Location to find | Context needed |
|-------|-----------------|----------------|
| `INSPECTION_ACCEPTED` | `views_receiving.py` — after inspection result saved as ACCEPTED | `bit`, `serial`, `inspection`, `actor_name` |
| `INSPECTION_REJECTED` | `views_receiving.py` — after inspection result saved as REJECTED | `bit`, `serial`, `inspection`, `actor_name` |
| `BIT_RECEIVED` | `views_receiving.py` — after new DrillBit created/backloaded | `bit`, `serial`, `actor_name` |
| `CEREBRO_DETECTED` | `views_receiving.py` — after Cerebro warning notify() | `bit`, `serial`, `actor_name` |
| `TRANSFER_CONFIRMED` | `views_jobcard.py` — after transfer confirmation notify() | `wo`, `wo_number`, `serial`, `bit`, `actor_name` |

**Priority B — wire these after Priority A is confirmed working:**

| Event | Location | Context needed |
|-------|----------|----------------|
| `WO_STARTED` | `views_jobcard.py` | `wo`, `wo_number`, `serial`, `actor_name` |
| `STEP_RESUMED` | `views_jobcard.py` | `wo`, `step`, `step_name`, `actor_name` |
| `EVALUATION_COMPLETED` | `views_jobcard.py` | `wo`, `wo_number`, `serial`, `actor_name` |
| `ROUTE_UPDATED` | `views_jobcard.py` | `wo`, `wo_number`, `serial`, `actor_name` |
| `GRN_POSTED` | `apps/inventory/views.py` | `grn`, `actor_name` |

**For each wiring, after adding the call, confirm it did not break the
existing view by checking `python manage.py check` passes.**

---

## TASK 4 — Add Action Widget to Production Planner

**Why**: The brief specifies the action widget on 4 pages. 3 are done.
Production planner is the missing one.

**Before doing anything**: Open `templates/workorders/production_planner.html`
and grep for `action_widget` to confirm it is not already there.

**What to do**: Add this include near the top of the main content area,
above the planner grid, matching the same pattern used in
`operator_home.html`, `receiving_dashboard.html`, and `floor_board.html`:

```html
{% include "notifications/partials/action_widget.html" with
   role_filter="PLANNER" show_replan=True %}
```

The widget should show `ADD_TO_PLAN` and `REPLAN` action types for planner
users. If the action_widget partial does not support `role_filter` parameter
yet, add that support to the partial so it filters by action type relevant
to the page context.

---

## TASK 5 — Cleanup Dead Files and Deprecated Code

**These are safe to clean because they have zero data and zero active
references. Confirm each before deleting.**

1. **Delete `templates/notifications/workflow_roles.html`** — only if grep
   confirms no URL or view references it.
   Confirm: `grep -rn "workflow_roles" apps/ templates/`

2. **Fix `seed_workflow_rules.py`** — if it still imports `WorkflowRole`
   (which no longer exists), either:
   - Remove the import and mark the command as deprecated with a docstring
     saying "superseded by seed_workflow_capabilities — do not run"
   - Or delete the file entirely if `seed_workflow_capabilities` fully
     replaces it
   Confirm which command is the current canonical seed command before deciding.

3. **The unused `Task` model/table** — do NOT delete this in this session.
   It requires a careful migration check. Just add a comment to the model:
   `# NOTE: Superseded by WorkflowAction. Keep for migration history.`
   Flag it for removal in Phase 5.

---

## TASK 6 — Position Dashboards (Phase 2 completion)

**Before building**: Run the conflict check from Step 0 item 9 above.
If any dashboard URL already exists, show the existing view before creating
a new one.

Build these 5 pages. Each follows the same pattern:

```
URL:      /dashboard/{role}/
View:     DashboardView (role-specific subclass)
Template: templates/workorders/dashboard_{role}.html
Sidebar:  Add link under the relevant role section
```

**Manager Dashboard — `/dashboard/manager/`**
Content:
- Action widget filtered to `APPROVE_WO` actions (pending WO approvals)
- Table of all WOs with status `PENDING` (awaiting approval) — columns:
  WO Number, Serial, Account, Released by, Released at, Age (hours)
- Table of all WOs currently `IN_PROGRESS` — count by step name
- Overdue actions (any role) — supervisor overview table

**QC Dashboard — `/dashboard/qc/`**
Content:
- Action widget filtered to `QC_CHECK` and `QUALITY_DECISION` actions
- WOs with status `QC_PENDING` — pending QC review queue
- Recent QC decisions (last 20) — Pass/Fail with WO number and date

**Technical Dashboard — `/dashboard/technical/`**
Content:
- Action widget filtered to `TECH_REVIEW`, `MAKE_DECISION`, `REMOVE_DEVICE`
- Steps currently `ON_HOLD` with reason `TECHNICAL_REVIEW` — direct links
- Active `CEREBRO_DETECTED` warnings if any

**Dispatch Dashboard — `/dashboard/dispatch/`**
Content:
- Action widget filtered to `PREPARE_DISPATCH`
- WOs with status `COMPLETED` not yet dispatched — with serial, account, age

**Management Dashboard — `/dashboard/management/`**
Content:
- Action widget filtered to `ACKNOWLEDGE` actions
- Summary counts: Bits in production / WOs active / WOs completed today /
  Steps on hold
- No operator-level task details — high-level overview only

**Access control**: Each dashboard should check that the requesting user has
a `UserRole` with the relevant role (or `is_superuser`). If not, return 403.
Use the existing `has_role()` method on the User model.

**Add sidebar links** for each dashboard. Check existing sidebar structure
in `templates/includes/sidebar.html` before adding — find the right section
for each role and add the link there. Do not create a new sidebar section if
an appropriate one already exists.

---

## TASK 7 — Bulk Position Sync Management Command

**Why**: When admin changes which roles a Position maps to (via the
Position × Capability matrix), existing users with that position are not
automatically re-synced. The signal only fires on new employee saves.

Create:
`apps/accounts/management/commands/sync_position_roles.py`

```
Usage: python manage.py sync_position_roles
       python manage.py sync_position_roles --dry-run
       python manage.py sync_position_roles --user=username

What it does:
- Iterates all active Users who have a position set
- For each user, calls sync_user_roles_from_position(user)
- Reports: X users processed, Y roles added, Z roles removed
- --dry-run: shows what would change without saving
- --user: run for a single user only
```

---

## FINAL VERIFICATION CHECKLIST

After completing all tasks, run these checks in order and show the output
of each:

```bash
# 1. No errors
python manage.py check

# 2. fire_event logger confirmed working
python manage.py shell -c "
from apps.notifications.dispatch import fire_event
result = fire_event('WO_RELEASED', actor=None, context={
    'wo_number': 'TEST-000', 'serial': '00000000', 'actor_name': 'Test'
})
print('fire_event result:', result)
print('(empty list is OK — no users assigned to roles yet)')
"

# 3. Confirm no dead WorkflowRole references
grep -rn "WorkflowRole\|UserWorkflowRole" apps/ | grep -v ".pyc\|migration\|#"

# 4. Confirm all 5 dashboard URLs resolve
python manage.py shell -c "
from django.urls import reverse
pages = ['dashboard_manager','dashboard_qc','dashboard_technical',
         'dashboard_dispatch','dashboard_management']
for p in pages:
    try:
        print(p, '→', reverse('workorders:' + p))
    except Exception as e:
        print(p, '→ MISSING:', e)
"

# 5. Confirm action widget is now on all 4 pages
grep -l "action_widget" templates/workorders/operator_home.html \
  templates/workorders/receiving_dashboard.html \
  templates/workorders/floor_board.html \
  templates/workorders/production_planner.html

# 6. Confirm fire_event wired to at least Priority A events
grep -n "fire_event\|dispatch_event" apps/workorders/views_receiving.py
```

All 6 checks must pass before this session is considered complete.
