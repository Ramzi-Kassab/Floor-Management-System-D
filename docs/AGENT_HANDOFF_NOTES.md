# Agent Handoff Notes — Route & Org System
# Date: 2026-03-27
# Context: Shared with another agent working on HR/Org/Access pages

## 1. RELATIONSHIP MAP (as-built, verified)

```
POSITION (organization.Position)     ROLE (accounts.Role)
  54 records                           17 records (4 original + 13 new)
  "QC Inspector L3"                    "ADMIN", "GM", "OPS_MANAGER",
  "Brazing Technician L2"             "PDC_SUPERVISOR", "RC_SUPERVISOR",
       |                               "ENGINEER", "QC_INSPECTOR", "PLANNER",
       | FK (User.position)            "BRAZER", "GRINDER", "OPERATOR",
       | FK (Employee.position) ←NEW   "RECEIVING", "VIEWER"
       v                               |
     USER (accounts.User)              | M2M via UserRole (with is_primary,
       ^                               |   assigned_by, expires_at)
       | OneToOne                       v
       |                             USER
  EMPLOYEE (hr.Employee)
       |
       | FK (Employee.department) ←CHANGED from CharField to FK
       v
  DEPARTMENT (organization.Department)
       |
       v
  ProcessCompetencyMatrix ←NEW
    employee FK → Employee
    master_process FK → MasterProcess (workorders)
    level: NOT_AUTHORIZED / TRAINEE / CERTIFIED / TRAINER
    certified_date, certified_by, expiry_date
```

## 2. POSITION vs ROLE — THEY ARE DIFFERENT THINGS

- **Position** = job function (WHAT you do): "PDC Brazing Technician Level 2"
  - Drives: competency matrix, training requirements, KPI grouping
  - 54 positions across 10 departments
  - Has `level` field (1-5) for seniority

- **Role** = access level (WHAT you can see/do in the system): "PDC_SUPERVISOR"
  - Drives: view permissions, approval authority, sidebar visibility
  - 17 roles with 49 permissions (321 assignments)
  - Has `is_system` flag for non-deletable roles

- One user can have multiple roles (M2M) but one position (FK)
- A "Brazing Technician" (position) typically has "OPERATOR" (role)
- A "PDC Supervisor" (position) typically has "PDC_SUPERVISOR" (role)

## 3. PERMISSIONS EXIST BUT ARE NOT ENFORCED

The entire permission infrastructure is built:
- `@role_required('ADMIN', 'PDC_SUPERVISOR')` decorator
- `PermissionRequiredMixin` for CBVs
- `RoleRequiredMixin` for role-based access
- Template tag: `{% if user|has_role:"ADMIN" %}`

But ZERO production views use them. Every view uses only `@login_required`.
This is intentional for now — enforcement is planned for a later sprint.
DO NOT start enforcing without the user's explicit approval.

## 4. PROCESS COMPETENCY MATRIX — HOW IT WORKS

`ProcessCompetencyMatrix` links Employee × MasterProcess with a level.
Key methods:
- `get_qualified_users_for_process(master_process)` → queryset of qualified Users
- `can_user_perform(user, master_process)` → True/False
- `get_gap_report_for_position(position)` → list of gaps

The competency matrix page at `/hr/competency/` shows a grid of employees × processes.
The gap report at `/hr/competency/gaps/` shows who is not certified for what.

## 5. MASTER PROCESS SYSTEM — CRITICAL CONTEXT

The route engine has 65+ MasterProcess records organized in families:
- 6 parent processes (_BASE_DIE_CHECK, _BASE_SAND_BLAST, etc.)
- Children inherit: instructions, parameters, checklist, time estimates
- Each child has its own: name, sort_order, inclusion rules, position in route

Rules use `ProcessInclusionRule` (field_path/operator/value) or `rule_expression` (JSON AND/OR/NOT).
Context fields available: `bit.level`, `design.body_material`, `eval.needs_brazing`, `tech.has_cerebro`, etc.

DO NOT use `step_mode='MULTI'` with insertion_points — the user explicitly rejected this
approach. Use standalone duplicate processes instead (feedback saved in memory).

## 6. ROUTER SHEET ENTRY — KPI FIELDS

Each step execution records denormalized context for fast KPI queries:
- `kpi_bit_size`, `kpi_body_material`, `kpi_design_mat`, `kpi_is_repair`
- `kpi_is_core_head`, `kpi_account`, `kpi_is_passive`
- `duration_gross_seconds`, `duration_net_seconds`
- `parent_process_code` — for family grouping

These are captured via `snapshot_kpi_context()` at step start
and `compute_durations()` at step completion.

## 7. EMPLOYEE MODEL — CURRENT STATE

Employee has 0 records in DB. The HR module is functional but unused.
Key fields now:
- `department` = FK to organization.Department (was free-text, just changed)
- `department_legacy` = old free-text value (kept for migration)
- `position` = FK to organization.Position (just added)
- `job_title` = free-text display name (kept as override/legacy)
- `user` = OneToOne to accounts.User

The User model ALSO has `department` and `position` FKs directly.
This means both User and Employee can point to the same Position/Department.
When building queries, prefer User.position over Employee.position
since Employee records may not exist for all users.

## 8. WHAT THE USER CARES ABOUT MOST

From working with this user extensively:
1. NO over-engineering — keep it simple, use existing patterns
2. NO silent changes — always show what changed and where
3. Processes should be standalone duplicates, not MULTI insertions
4. Every location change must go through the Location Transfers page
5. The route preview page at /work-orders/route-preview/ is the primary
   tool for testing route assembly — changes should be visible there
6. The user prefers to reorder processes visually, not in code
7. Deletion is preferred over deactivation for removed processes
