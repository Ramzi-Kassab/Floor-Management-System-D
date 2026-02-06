"""
Seed default evaluation routes for common account + bit type combinations.

Usage:
    python manage.py seed_evaluation_routes --confirm
    python manage.py seed_evaluation_routes --list
    python manage.py seed_evaluation_routes --clear --confirm
"""
from django.core.management.base import BaseCommand
from apps.workorders.models import EvaluationRoute, EvaluationRouteStep, CutterEvaluationMatrix
from apps.sales.models import Account


class Command(BaseCommand):
    help = "Seed default evaluation routes for accounts"

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm seeding of routes'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all current routes'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing routes before seeding'
        )

    def handle(self, *args, **options):
        if options['list']:
            return self.list_routes()

        if options['clear']:
            if not options['confirm']:
                self.stdout.write(self.style.WARNING(
                    'Use --confirm to actually clear all routes'
                ))
                return
            cleared = EvaluationRoute.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Cleared {cleared[0]} routes'))

        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                'Use --confirm to seed routes. Use --list to see current routes.'
            ))
            return

        self.seed_routes()

    def list_routes(self):
        """List all current evaluation routes."""
        routes = EvaluationRoute.objects.select_related('account').prefetch_related('steps')

        if not routes.exists():
            self.stdout.write('No evaluation routes configured.')
            return

        for route in routes:
            steps = route.steps.all().order_by('order')
            step_list = ', '.join([f"{s.order}.{s.evaluation_type}" for s in steps])
            status = '(default)' if route.is_default else ''
            self.stdout.write(
                f"[{route.account.code}] {route.get_bit_type_display()}: {route.name} {status}"
            )
            self.stdout.write(f"    Steps: {step_list or '(none)'}")

    def seed_routes(self):
        """Seed default evaluation routes."""
        # Define route configurations
        # Format: (account_code, bit_type, route_name, steps)
        # Steps format: [(eval_type, is_required, is_conditional, help_text)]

        ET = CutterEvaluationMatrix.EvaluationType

        # Standard repair steps (most accounts)
        standard_repair_steps = [
            (ET.PDC_EVAL, True, False, ''),
            (ET.QC, True, False, ''),
            (ET.DIE_CHECK, True, False, ''),
            (ET.FINAL_DIE_CHECK, True, False, ''),
            (ET.FINAL_QC, True, False, ''),
            (ET.FINAL_INSPECTION, True, False, ''),
        ]

        # Standard new build steps
        standard_new_steps = [
            (ET.PDC_EVAL, True, False, ''),
            (ET.DIE_CHECK, True, False, ''),
            (ET.FINAL_DIE_CHECK, True, False, ''),
            (ET.FINAL_QC, True, False, ''),
            (ET.FINAL_INSPECTION, True, False, ''),
        ]

        # ARAMCO steps (includes Aramco Rep)
        aramco_repair_steps = [
            (ET.PDC_EVAL, True, False, ''),
            (ET.QC, True, False, ''),
            (ET.ARAMCO_REP, True, False, 'Aramco inspector evaluation'),
            (ET.DIE_CHECK, True, False, ''),
            (ET.FINAL_DIE_CHECK, True, False, ''),
            (ET.FINAL_QC, True, False, ''),
            (ET.FINAL_INSPECTION, True, False, ''),
        ]

        aramco_new_steps = [
            (ET.PDC_EVAL, True, False, ''),
            (ET.ARAMCO_REP, True, False, 'Aramco inspector evaluation'),
            (ET.DIE_CHECK, True, False, ''),
            (ET.FINAL_DIE_CHECK, True, False, ''),
            (ET.FINAL_QC, True, False, ''),
            (ET.FINAL_INSPECTION, True, False, ''),
        ]

        # LSTK steps (includes Tech Rep)
        lstk_repair_steps = [
            (ET.PDC_EVAL, True, False, ''),
            (ET.QC, True, False, ''),
            (ET.ENGINEER, False, True, 'Only if customer requests'),
            (ET.DIE_CHECK, True, False, ''),
            (ET.FINAL_DIE_CHECK, True, False, ''),
            (ET.FINAL_QC, True, False, ''),
            (ET.FINAL_INSPECTION, True, False, ''),
        ]

        # Route definitions
        route_configs = [
            # LSTK
            ('LSTK', 'NEW', 'LSTK New Build', standard_new_steps),
            ('LSTK', 'USED', 'LSTK Repair', lstk_repair_steps),

            # ARAMCO
            ('ARAMCO', 'NEW', 'ARAMCO New Build', aramco_new_steps),
            ('ARAMCO', 'USED', 'ARAMCO Repair', aramco_repair_steps),

            # UR - simplified (no tech rep)
            ('UR', 'NEW', 'UR New Build', standard_new_steps),
            ('UR', 'USED', 'UR Repair', standard_repair_steps),

            # L3/L4 manufacture only
            ('L3', 'NEW', 'L3 Manufacture', standard_new_steps),
            ('L4', 'NEW', 'L4 Manufacture', standard_new_steps),

            # ARDT internal
            ('ARDT', 'NEW', 'ARDT New Build', standard_new_steps),
            ('ARDT', 'USED', 'ARDT Repair', standard_repair_steps),

            # HALLIBURTON
            ('HALLIBURTON', 'NEW', 'Halliburton New Build', standard_new_steps),
            ('HALLIBURTON', 'USED', 'Halliburton Repair', lstk_repair_steps),

            # HAL_REGIONAL
            ('HAL_REGIONAL', 'NEW', 'Regional New Build', standard_new_steps),
            ('HAL_REGIONAL', 'USED', 'Regional Repair', standard_repair_steps),

            # WFD
            ('WFD', 'NEW', 'WFD New Build', standard_new_steps),
            ('WFD', 'USED', 'WFD Repair', standard_repair_steps),

            # RC-LSTK
            ('RC-LSTK', 'NEW', 'RC-LSTK New Build', standard_new_steps),
            ('RC-LSTK', 'USED', 'RC-LSTK Repair', standard_repair_steps),

            # SUB
            ('SUB', 'NEW', 'SUB New Build', standard_new_steps),
            ('SUB', 'USED', 'SUB Repair', standard_repair_steps),
        ]

        created_count = 0
        skipped_count = 0

        for account_code, bit_type, route_name, steps in route_configs:
            try:
                account = Account.objects.get(code=account_code)
            except Account.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'Account {account_code} not found, skipping'
                ))
                continue

            # Check if route already exists
            existing = EvaluationRoute.objects.filter(
                account=account,
                bit_type=bit_type
            ).first()

            if existing:
                self.stdout.write(self.style.WARNING(
                    f'Route already exists: {account_code} {bit_type}, skipping'
                ))
                skipped_count += 1
                continue

            # Create route
            route = EvaluationRoute.objects.create(
                name=route_name,
                account=account,
                bit_type=bit_type,
                is_default=True,
                is_active=True
            )

            # Create steps
            for order, (eval_type, is_required, is_conditional, help_text) in enumerate(steps, 1):
                EvaluationRouteStep.objects.create(
                    route=route,
                    evaluation_type=eval_type,
                    order=order,
                    is_required=is_required,
                    is_conditional=is_conditional,
                    condition_description=help_text,
                    show_decision_field=True,
                    show_cutter_matrix=True,
                    show_cutters_details=True
                )

            self.stdout.write(self.style.SUCCESS(
                f'Created route: {account_code} {bit_type} with {len(steps)} steps'
            ))
            created_count += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done: {created_count} routes created, {skipped_count} skipped'
        ))
