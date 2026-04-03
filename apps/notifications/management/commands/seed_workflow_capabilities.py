"""
Seed WorkflowCapability records and migrate WorkflowRule FK fields.
Usage: python manage.py seed_workflow_capabilities --confirm
"""
from django.core.management.base import BaseCommand
from apps.notifications.models import WorkflowCapability, WorkflowRule


CAPABILITIES = [
    # (code, name, has_full_visibility, is_system_admin, order)
    ('RECEIVING_INSPECTOR',  'Receiving Inspector',          False, False, 10),
    ('PLANNER',              'Production Planner',           False, False, 20),
    ('PRODUCTION_MANAGER',   'Production Manager',           False, False, 30),
    ('PRODUCTION_LEAD',      'Production Lead / Supervisor', False, False, 40),
    ('OPERATOR',             'Floor Operator',               False, False, 50),
    ('QC_INSPECTOR',         'QC Inspector',                 False, False, 60),
    ('TECHNICAL_LEAD',       'Technical Lead',               False, False, 70),
    ('DISPATCH',             'Dispatch / Shipping',          False, False, 80),
    ('MANAGEMENT',           'Management',                   True,  False, 90),
    ('SYSTEM_ADMIN',         'System Administrator',         True,  True,  100),
    # New ones the enum couldn't express
    ('GENERAL_MANAGER',      'General Manager',              True,  False, 5),
    ('SALES_ACCOUNT_LEAD',   'Sales Account Lead',           False, False, 85),
    ('FIELD_ENGINEER',       'Field Engineer',               False, False, 75),
    ('MAINTENANCE',          'Maintenance Technician',       False, False, 55),
    ('DRIVER',               'Driver / Logistics',           False, False, 95),
]


class Command(BaseCommand):
    help = 'Seed WorkflowCapability records and migrate WorkflowRule FKs'

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true')

    def handle(self, *args, **options):
        confirm = options.get('confirm', False)

        # Step 1: Create capabilities
        created = 0
        for code, name, full_vis, sys_admin, order in CAPABILITIES:
            cap, was_created = WorkflowCapability.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'has_full_visibility': full_vis,
                    'is_system_admin': sys_admin,
                    'order': order,
                }
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  CREATED: {code} — {name}'))
            else:
                self.stdout.write(f'  EXISTS: {code}')

        self.stdout.write(f'\nCapabilities: {created} created, {len(CAPABILITIES) - created} existed')

        if not confirm:
            self.stdout.write('\nDry run — run with --confirm to also migrate WorkflowRule FKs')
            return

        # Step 2: Migrate WorkflowRule FK fields from old CharField to new FK
        # The old fields (assign_to_role, notif_recipients_role, escalate_to_role)
        # have been removed from the model. The new FK fields (assign_to_capability, etc.)
        # are empty. We match by the old seeded rule names which used the same codes.
        migrated = 0
        for rule in WorkflowRule.objects.all():
            changed = False

            # Match capability from the seed data — the seed_workflow_rules command
            # used role codes like OPERATOR, PRODUCTION_MANAGER etc. which are now
            # capability codes. We can detect the intended capability from the rule name.
            if not rule.assign_to_capability:
                # Try to determine from rule's action description
                for code, name, _, _, _ in CAPABILITIES:
                    if code.lower().replace('_', ' ') in rule.name.lower():
                        cap = WorkflowCapability.objects.filter(code=code).first()
                        if cap:
                            rule.assign_to_capability = cap
                            changed = True
                            break

            if not rule.notif_recipients_capability:
                # Same heuristic
                for code, name, _, _, _ in CAPABILITIES:
                    if code.lower().replace('_', ' ') in rule.name.lower():
                        cap = WorkflowCapability.objects.filter(code=code).first()
                        if cap:
                            rule.notif_recipients_capability = cap
                            changed = True
                            break

            if changed:
                rule.save()
                migrated += 1
                self.stdout.write(f'  MIGRATED: {rule.name}')

        self.stdout.write(self.style.SUCCESS(f'\nMigrated {migrated} rules'))

        # Step 3: Direct mapping for known rules that the heuristic might miss
        DIRECT_MAP = {
            'Bit received': ('RECEIVING_INSPECTOR', 'RECEIVING_INSPECTOR'),
            'Inspection accepted': ('PLANNER', 'PLANNER'),
            'Inspection rejected': ('TECHNICAL_LEAD', 'TECHNICAL_LEAD'),
            'Cerebro device': ('TECHNICAL_LEAD', 'TECHNICAL_LEAD'),
            'WO released — operator': ('OPERATOR', 'OPERATOR'),
            'WO released — manager': ('PRODUCTION_MANAGER', 'PRODUCTION_MANAGER'),
            'Transfer confirmed': (None, 'PLANNER'),
            'WO approved': ('OPERATOR', 'OPERATOR'),
            'WO deleted': ('PLANNER', 'PLANNER'),
            'Step on hold': ('PRODUCTION_LEAD', 'PRODUCTION_LEAD'),
            'Step waiting QC': ('QC_INSPECTOR', 'QC_INSPECTOR'),
            'Step waiting approval': ('PRODUCTION_MANAGER', 'PRODUCTION_MANAGER'),
            'Step waiting tech': ('TECHNICAL_LEAD', 'TECHNICAL_LEAD'),
            'Step resumed': (None, 'OPERATOR'),
            'All steps done': ('OPERATOR', 'PRODUCTION_LEAD'),
            'Die check': ('QC_INSPECTOR', 'QC_INSPECTOR'),
            'WO sent to QC': ('QC_INSPECTOR', 'QC_INSPECTOR'),
            'QC passed': ('DISPATCH', 'DISPATCH'),
            'QC failed': ('PRODUCTION_LEAD', 'PRODUCTION_LEAD'),
            'WO completed': (None, 'MANAGEMENT'),
            'Evaluation completed': (None, 'PRODUCTION_MANAGER'),
            'Route auto-updated': (None, 'PRODUCTION_LEAD'),
            'GRN posted': (None, 'MANAGEMENT'),
            'WO started': (None, 'PRODUCTION_LEAD'),
        }

        direct_count = 0
        for rule in WorkflowRule.objects.all():
            for prefix, (assign_code, notif_code) in DIRECT_MAP.items():
                if rule.name.startswith(prefix):
                    changed = False
                    if assign_code and not rule.assign_to_capability:
                        cap = WorkflowCapability.objects.filter(code=assign_code).first()
                        if cap:
                            rule.assign_to_capability = cap
                            changed = True
                    if notif_code and not rule.notif_recipients_capability:
                        cap = WorkflowCapability.objects.filter(code=notif_code).first()
                        if cap:
                            rule.notif_recipients_capability = cap
                            changed = True
                    if changed:
                        rule.save()
                        direct_count += 1
                        self.stdout.write(f'  DIRECT: {rule.name} -> assign={assign_code}, notif={notif_code}')
                    break

        self.stdout.write(self.style.SUCCESS(f'Direct mapped {direct_count} rules'))
