# Next Session: Trigger & Rules Editor Redesign

## What Exists Now
- `TriggerPoint` model with 462 auto-discovered records from URL resolver
- `WorkflowRule` model with 24 seeded rules
- Workflow Rules page at `/notifications/settings/workflow/rules/` (basic, needs redesign)
- All Triggers tab at `/notifications/actions/?tab=triggers` (lists all 462 triggers)
- `sync_trigger_points` management command for auto-discovery

## What Needs To Be Built

### 1. Trigger Detail/Edit Page
URL: `/notifications/settings/workflow/triggers/<pk>/`

Shows ONE trigger point with:
- Trigger info: icon, name, description, page, who triggers, URL pattern
- Editable fields: name, description, icon, category, typical_role
- ALL rules for this trigger listed as rows below
- Each rule row is fully editable (type, action type, role, priority, deadline)
- Add new rule button for this trigger
- Delete rule button per row

### 2. Update All Triggers Tab
When clicking a trigger in `/notifications/actions/?tab=triggers`:
- If trigger has rules → go to trigger detail page showing its rules
- If trigger has no rules → go to trigger detail page with empty rules + "Add Rule" button

### 3. Update Workflow Rules Page
`/notifications/settings/workflow/rules/` should ONLY show triggers that have rules configured.
Each trigger is a collapsible card with its rules as inline-editable rows.
"Add trigger" button → dropdown of all 462 triggers → creates first rule for it.

### 4. Trigger CRUD
- Edit trigger metadata (name, description, icon, category) from the detail page
- Triggers auto-sync via `sync_trigger_points` command but admin can enrich descriptions
- New triggers auto-discovered on next sync — admin only needs to add rules

### 5. Keep sync_trigger_points Working
- Run on deploy or periodically
- Creates new triggers for new URLs
- Marks removed URLs as inactive
- Never deletes — just deactivates (preserves rule history)

## Key Files
- `apps/notifications/models.py` — TriggerPoint, WorkflowRule, WorkflowAction
- `apps/notifications/views.py` — WorkflowRuleListView, ActionCenterView
- `apps/notifications/urls.py` — rule CRUD APIs
- `templates/notifications/workflow_rules_editor.html` — rules page template
- `templates/notifications/action_center.html` — All Triggers tab
- `apps/notifications/management/commands/sync_trigger_points.py` — auto-discovery

## Other Pending Items
- Wire remaining 13 fire_event() calls (Phase 3 completion)
- Phase 4: Remove old notify() calls
- Printable forms (DC, evaluations, NCR)
- Dispatch→Field→Return lifecycle
- Dead code cleanup (templates/templates/, apps/apps/)
- App rename to "ARDT Operations System"
