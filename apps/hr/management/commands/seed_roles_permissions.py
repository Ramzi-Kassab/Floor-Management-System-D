"""
Place this file at:
apps/hr/management/commands/seed_roles_permissions.py

Run with:
    python manage.py seed_roles_permissions

This seeds all roles and permissions needed for ARDT FMS.
Safe to run multiple times — uses get_or_create throughout.
"""

from django.core.management.base import BaseCommand
from apps.accounts.models import Role, Permission, RolePermission


ROLES = [
    # code, name, level, description
    ('ADMIN',           'System Administrator',   100, 'Full system access'),
    ('GM',              'General Manager',         90, 'Executive oversight and final approvals'),
    ('OPS_MANAGER',     'Operations Manager',      80, 'Production and operations management'),
    ('PDC_SUPERVISOR',  'PDC Supervisor',           70, 'PDC department supervision and QC sign-off'),
    ('RC_SUPERVISOR',   'RC Supervisor',            70, 'RC department supervision'),
    ('ENGINEER',        'Technical Engineer',       60, 'Technical evaluation and design authority'),
    ('QC_INSPECTOR',    'QC Inspector',             60, 'Quality control inspections and sign-offs'),
    ('PLANNER',         'Production Planner',       50, 'WO creation, planning, and scheduling'),
    ('BRAZER',          'Brazer / Welder',          30, 'Brazing and welding operations'),
    ('GRINDER',         'Grinder / Machinist',      30, 'Grinding and machining operations'),
    ('OPERATOR',        'Floor Operator',           20, 'General production floor operations'),
    ('RECEIVING',       'Receiving / Dispatch',     20, 'Receiving dock and dispatch operations'),
    ('VIEWER',          'Read-Only Viewer',         10, 'View-only access to system data'),
]


PERMISSIONS = [
    # (code, name, module)

    # ── Work Orders ──────────────────────────────────────────────────
    ('workorders.view',              'View Work Orders',              'workorders'),
    ('workorders.create',            'Create Work Orders',            'workorders'),
    ('workorders.edit',              'Edit Work Orders',              'workorders'),
    ('workorders.delete',            'Delete Work Orders',            'workorders'),
    ('workorders.release',           'Release Work Orders to Production', 'workorders'),
    ('workorders.approve',           'Approve Work Orders',           'workorders'),
    ('workorders.close',             'Close / Complete Work Orders',  'workorders'),

    # ── Router / Production Steps ────────────────────────────────────
    ('router.view',                  'View Router Sheet',             'router'),
    ('router.start_step',            'Start a Production Step',       'router'),
    ('router.complete_step',         'Mark Step Complete',            'router'),
    ('router.skip_step',             'Skip a Step',                   'router'),
    ('router.add_step',              'Add Extra Step',                'router'),
    ('router.edit_step',             'Edit Step Data',                'router'),

    # ── Evaluations ──────────────────────────────────────────────────
    ('evaluations.view',             'View Evaluations',              'evaluations'),
    ('evaluations.create',           'Create Evaluations',            'evaluations'),
    ('evaluations.complete',         'Mark Evaluation Complete',      'evaluations'),
    ('evaluations.print',            'Print Evaluation Reports',      'evaluations'),

    # ── Die Check / LPT / Thread ─────────────────────────────────────
    ('tests.view',                   'View Test Reports',             'tests'),
    ('tests.create',                 'Create Test Reports',           'tests'),
    ('tests.complete',               'Mark Test Complete',            'tests'),

    # ── Drill Bits ───────────────────────────────────────────────────
    ('drillbits.view',               'View Drill Bit Inventory',      'drillbits'),
    ('drillbits.create',             'Register New Drill Bits',       'drillbits'),
    ('drillbits.edit',               'Edit Drill Bit Records',        'drillbits'),
    ('drillbits.delete',             'Delete Drill Bit Records',      'drillbits'),
    ('drillbits.transfer',           'Transfer Drill Bit Location',   'drillbits'),
    ('drillbits.scrap',              'Scrap a Drill Bit',             'drillbits'),

    # ── BOM / Design ─────────────────────────────────────────────────
    ('bom.view',                     'View BOM and Designs',          'bom'),
    ('bom.edit',                     'Edit BOM Records',              'bom'),
    ('bom.approve',                  'Approve BOM Changes',           'bom'),

    # ── Receiving / Dispatch ─────────────────────────────────────────
    ('receiving.view',               'View Receiving Dashboard',      'receiving'),
    ('receiving.process',            'Process Receiving Batches',     'receiving'),
    ('dispatch.view',                'View Dispatch Records',         'dispatch'),
    ('dispatch.process',             'Process Dispatch / Shipments',  'dispatch'),

    # ── NCR ──────────────────────────────────────────────────────────
    ('ncr.view',                     'View NCRs',                     'ncr'),
    ('ncr.create',                   'Create NCRs',                   'ncr'),
    ('ncr.close',                    'Close NCRs',                    'ncr'),

    # ── Approvals ────────────────────────────────────────────────────
    ('approvals.view',               'View Approval Queues',          'approvals'),
    ('approvals.approve',            'Approve Requests',              'approvals'),
    ('approvals.reject',             'Reject Requests',               'approvals'),

    # ── HR ───────────────────────────────────────────────────────────
    ('hr.view',                      'View Employee Records',         'hr'),
    ('hr.edit',                      'Edit Employee Records',         'hr'),
    ('hr.view_compensation',         'View Compensation Data',        'hr'),
    ('hr.manage_competency',         'Manage Competency Matrix',      'hr'),

    # ── KPI / Reports ────────────────────────────────────────────────
    ('reports.view',                 'View Reports',                  'reports'),
    ('reports.export',               'Export Reports',                'reports'),
    ('kpi.view',                     'View KPI Dashboards',           'kpi'),

    # ── Admin ────────────────────────────────────────────────────────
    ('admin.roles',                  'Manage Roles and Permissions',  'admin'),
    ('admin.users',                  'Manage User Accounts',          'admin'),
    ('admin.system',                 'System Configuration',          'admin'),
]


# Role → Permission mapping
# Format: role_code → [list of permission codes]
ROLE_PERMISSIONS = {
    'ADMIN': [p[0] for p in PERMISSIONS],  # All permissions

    'GM': [
        'workorders.view', 'workorders.approve', 'workorders.close',
        'router.view',
        'evaluations.view', 'evaluations.print',
        'drillbits.view',
        'bom.view', 'bom.approve',
        'receiving.view', 'dispatch.view',
        'ncr.view', 'ncr.close',
        'approvals.view', 'approvals.approve', 'approvals.reject',
        'hr.view', 'hr.view_compensation',
        'reports.view', 'reports.export', 'kpi.view',
    ],

    'OPS_MANAGER': [
        'workorders.view', 'workorders.create', 'workorders.edit',
        'workorders.release', 'workorders.approve', 'workorders.close',
        'router.view', 'router.add_step', 'router.skip_step',
        'evaluations.view', 'evaluations.create', 'evaluations.complete', 'evaluations.print',
        'tests.view', 'tests.create', 'tests.complete',
        'drillbits.view', 'drillbits.edit', 'drillbits.transfer',
        'bom.view', 'bom.edit',
        'receiving.view', 'receiving.process',
        'dispatch.view', 'dispatch.process',
        'ncr.view', 'ncr.create', 'ncr.close',
        'approvals.view', 'approvals.approve', 'approvals.reject',
        'hr.view', 'hr.manage_competency',
        'reports.view', 'reports.export', 'kpi.view',
    ],

    'PDC_SUPERVISOR': [
        'workorders.view', 'workorders.create', 'workorders.edit', 'workorders.release',
        'router.view', 'router.start_step', 'router.complete_step',
        'router.skip_step', 'router.add_step', 'router.edit_step',
        'evaluations.view', 'evaluations.create', 'evaluations.complete', 'evaluations.print',
        'tests.view', 'tests.create', 'tests.complete',
        'drillbits.view', 'drillbits.edit', 'drillbits.transfer',
        'bom.view',
        'receiving.view', 'receiving.process',
        'dispatch.view', 'dispatch.process',
        'ncr.view', 'ncr.create', 'ncr.close',
        'approvals.view', 'approvals.approve',
        'hr.view', 'hr.manage_competency',
        'reports.view', 'kpi.view',
    ],

    'RC_SUPERVISOR': [
        'workorders.view', 'workorders.create', 'workorders.edit', 'workorders.release',
        'router.view', 'router.start_step', 'router.complete_step',
        'router.skip_step', 'router.add_step', 'router.edit_step',
        'evaluations.view', 'evaluations.create', 'evaluations.complete', 'evaluations.print',
        'tests.view', 'tests.create', 'tests.complete',
        'drillbits.view', 'drillbits.edit', 'drillbits.transfer',
        'bom.view',
        'receiving.view', 'dispatch.view',
        'ncr.view', 'ncr.create',
        'approvals.view',
        'hr.view',
        'reports.view', 'kpi.view',
    ],

    'ENGINEER': [
        'workorders.view', 'workorders.edit',
        'router.view', 'router.add_step',
        'evaluations.view', 'evaluations.create', 'evaluations.complete', 'evaluations.print',
        'tests.view', 'tests.create', 'tests.complete',
        'drillbits.view',
        'bom.view', 'bom.edit', 'bom.approve',
        'ncr.view', 'ncr.create',
        'reports.view', 'kpi.view',
    ],

    'QC_INSPECTOR': [
        'workorders.view',
        'router.view',
        'evaluations.view', 'evaluations.create', 'evaluations.complete', 'evaluations.print',
        'tests.view', 'tests.create', 'tests.complete',
        'drillbits.view',
        'ncr.view', 'ncr.create',
        'approvals.view', 'approvals.approve',
        'reports.view',
    ],

    'PLANNER': [
        'workorders.view', 'workorders.create', 'workorders.edit', 'workorders.release',
        'router.view',
        'evaluations.view', 'evaluations.print',
        'drillbits.view', 'drillbits.edit',
        'bom.view',
        'receiving.view',
        'dispatch.view', 'dispatch.process',
        'reports.view', 'kpi.view',
    ],

    'BRAZER': [
        'workorders.view',
        'router.view', 'router.start_step', 'router.complete_step', 'router.edit_step',
        'evaluations.view',
        'drillbits.view',
    ],

    'GRINDER': [
        'workorders.view',
        'router.view', 'router.start_step', 'router.complete_step', 'router.edit_step',
        'evaluations.view',
        'drillbits.view',
    ],

    'OPERATOR': [
        'workorders.view',
        'router.view', 'router.start_step', 'router.complete_step', 'router.edit_step',
        'evaluations.view',
        'drillbits.view',
    ],

    'RECEIVING': [
        'workorders.view',
        'drillbits.view',
        'receiving.view', 'receiving.process',
        'dispatch.view', 'dispatch.process',
    ],

    'VIEWER': [
        'workorders.view',
        'router.view',
        'evaluations.view',
        'drillbits.view',
        'reports.view',
    ],
}


class Command(BaseCommand):
    help = 'Seed roles and permissions for ARDT FMS'

    def handle(self, *args, **options):
        self.stdout.write('Seeding roles...')
        role_objects = {}
        for code, name, level, description in ROLES:
            role, created = Role.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'level': level,
                    'description': description,
                    'is_system': True,
                    'is_active': True,
                }
            )
            if not created:
                role.name = name
                role.level = level
                role.description = description
                role.save()
            role_objects[code] = role
            verb = 'Created' if created else 'Updated'
            self.stdout.write(f'  {verb} role: {code}')

        self.stdout.write('Seeding permissions...')
        permission_objects = {}
        for code, name, module in PERMISSIONS:
            perm, created = Permission.objects.get_or_create(
                code=code,
                defaults={'name': name, 'module': module}
            )
            if not created:
                perm.name = name
                perm.module = module
                perm.save()
            permission_objects[code] = perm
            verb = 'Created' if created else 'Updated'
            self.stdout.write(f'  {verb} permission: {code}')

        self.stdout.write('Assigning permissions to roles...')
        for role_code, perm_codes in ROLE_PERMISSIONS.items():
            role = role_objects.get(role_code)
            if not role:
                continue
            count = 0
            for perm_code in perm_codes:
                perm = permission_objects.get(perm_code)
                if perm:
                    _, created = RolePermission.objects.get_or_create(
                        role=role, permission=perm
                    )
                    if created:
                        count += 1
            self.stdout.write(f'  {role_code}: {count} new assignments')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {len(ROLES)} roles, {len(PERMISSIONS)} permissions seeded.'
        ))
        self.stdout.write(
            '\nNext step: Assign roles to users via Django admin or:\n'
            '  from apps.accounts.models import User, Role, UserRole\n'
            '  user = User.objects.get(username="ramzi")\n'
            '  role = Role.objects.get(code="PDC_SUPERVISOR")\n'
            '  UserRole.objects.get_or_create(user=user, role=role)\n'
        )
