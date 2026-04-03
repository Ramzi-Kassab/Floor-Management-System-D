"""
Seed process route templates with the 33 FC Bit Repair steps from the JC Template (QAS/1006 Rev L),
and a separate L3/L4 manufacture route.

Usage:
    python manage.py seed_router_steps --confirm
"""
from django.core.management.base import BaseCommand
from apps.workorders.models import ProcessRoute, ProcessRouteOperation


# 33 steps from FC Bit Repair Router Sheet (QAS/1006, Rev L)
FC_REPAIR_STEPS = [
    {'seq': 10, 'code': 'NOZZLE_REMOVAL', 'name': 'Nozzle Removal', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'PREP'},
    {'seq': 20, 'code': 'CEREBRO_REMOVAL', 'name': 'Cerebro Removal', 'conditional': False, 'yes_no': True, 'qc': False, 'center': 'PREP'},
    {'seq': 30, 'code': 'ORING_REMOVAL', 'name': 'Cer. O-Ring Removal', 'conditional': False, 'yes_no': True, 'qc': False, 'center': 'PREP'},
    {'seq': 40, 'code': 'WASHING_1', 'name': 'Washing', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'WASH'},
    {'seq': 50, 'code': 'SANDBLAST_1', 'name': 'Sand Blasting', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'BLAST'},
    {'seq': 60, 'code': 'PRESSURE_TEST_1', 'name': 'Pressure Test', 'conditional': True, 'yes_no': False, 'qc': False, 'center': 'TEST'},
    {'seq': 70, 'code': 'DIE_CHECK_1', 'name': 'Die Check', 'conditional': False, 'yes_no': False, 'qc': True, 'center': 'INSPECT'},
    {'seq': 80, 'code': 'PHOTOS_EVAL', 'name': 'Photos & Evaluation', 'conditional': False, 'yes_no': False, 'qc': True, 'center': 'EVAL'},
    {'seq': 90, 'code': 'HEAD_PREP_1', 'name': 'Bit Head Preparation', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'PREP'},
    {'seq': 100, 'code': 'DEBRAZING', 'name': 'De-Brazing', 'conditional': True, 'yes_no': False, 'qc': False, 'center': 'FURNACE'},
    {'seq': 110, 'code': 'MATRIX_REPAIR', 'name': 'Matrix or Hardfacing Repair', 'conditional': True, 'yes_no': False, 'qc': False, 'center': 'REPAIR'},
    {'seq': 120, 'code': 'GRINDING_1', 'name': 'Pocket, Blade or IA Grinding', 'conditional': True, 'yes_no': False, 'qc': False, 'center': 'GRIND'},
    {'seq': 130, 'code': 'SANDBLAST_2', 'name': 'Sand Blasting', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'BLAST'},
    {'seq': 140, 'code': 'HEAD_PREP_2', 'name': 'Bit Head Preparation For Brazing', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'PREP'},
    {'seq': 150, 'code': 'BRAZING', 'name': 'Brazing', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'FURNACE'},
    {'seq': 160, 'code': 'WASHING_2', 'name': 'Washing', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'WASH'},
    {'seq': 170, 'code': 'SANDBLAST_3', 'name': 'Sand Blasting', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'BLAST'},
    {'seq': 180, 'code': 'DIE_CHECK_2', 'name': 'Die Check', 'conditional': False, 'yes_no': False, 'qc': True, 'center': 'INSPECT'},
    {'seq': 190, 'code': 'FINAL_GRINDING', 'name': 'Final Grinding', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'GRIND'},
    {'seq': 200, 'code': 'TIP_GRINDING', 'name': 'Tip Grinding', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'GRIND'},
    {'seq': 210, 'code': 'WASHING_3', 'name': 'Washing', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'WASH'},
    {'seq': 220, 'code': 'SANDBLAST_4', 'name': 'Sand Blasting', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'BLAST'},
    {'seq': 230, 'code': 'DIE_CHECK_3', 'name': 'Die Check', 'conditional': False, 'yes_no': False, 'qc': True, 'center': 'INSPECT'},
    {'seq': 240, 'code': 'UPPER_REMOVAL', 'name': 'Upper Section Removal & Assembly', 'conditional': True, 'yes_no': False, 'qc': False, 'center': 'MACHINE'},
    {'seq': 250, 'code': 'UPPER_WELDING', 'name': 'Upper Section Sub-Arc Welding', 'conditional': True, 'yes_no': False, 'qc': False, 'center': 'WELD'},
    {'seq': 260, 'code': 'SHANK_MACHINING', 'name': 'Shank Machining', 'conditional': True, 'yes_no': False, 'qc': False, 'center': 'MACHINE'},
    {'seq': 270, 'code': 'PRESSURE_TEST_2', 'name': 'Pressure Test', 'conditional': True, 'yes_no': False, 'qc': False, 'center': 'TEST'},
    {'seq': 280, 'code': 'BIT_PHOTOS', 'name': 'Bit Photos', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'PHOTO'},
    {'seq': 290, 'code': 'QC_INSPECTION', 'name': 'QC Inspection', 'conditional': False, 'yes_no': False, 'qc': True, 'center': 'QC'},
    {'seq': 300, 'code': 'FINAL_INSPECTION', 'name': 'Final Inspection', 'conditional': False, 'yes_no': False, 'qc': True, 'center': 'QC'},
    {'seq': 310, 'code': 'PAINTING_BOXING', 'name': 'Painting & Boxing', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'FINISH'},
    {'seq': 320, 'code': 'CEREBRO_INSTALL', 'name': 'Cerebro Installation', 'conditional': False, 'yes_no': True, 'qc': False, 'center': 'FINISH'},
    {'seq': 330, 'code': 'CEREBRO_CAP', 'name': 'Cerebro Cap Tightening', 'conditional': False, 'yes_no': True, 'qc': False, 'center': 'FINISH'},
]

# L3/L4 manufacture route — different steps (no receiving, no debrazing, no evaluation of existing cutters)
L3_L4_MANUFACTURE_STEPS = [
    {'seq': 10, 'code': 'BIT_BODY_PREP', 'name': 'Bit Body Preparation', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'PREP'},
    {'seq': 20, 'code': 'SANDBLAST_1', 'name': 'Sand Blasting', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'BLAST'},
    {'seq': 30, 'code': 'DIE_CHECK_1', 'name': 'Die Check', 'conditional': False, 'yes_no': False, 'qc': True, 'center': 'INSPECT'},
    {'seq': 40, 'code': 'POCKET_GRINDING', 'name': 'Pocket & Blade Grinding', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'GRIND'},
    {'seq': 50, 'code': 'SANDBLAST_2', 'name': 'Sand Blasting', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'BLAST'},
    {'seq': 60, 'code': 'HEAD_PREP', 'name': 'Bit Head Preparation For Brazing', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'PREP'},
    {'seq': 70, 'code': 'BRAZING', 'name': 'Brazing', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'FURNACE'},
    {'seq': 80, 'code': 'WASHING_1', 'name': 'Washing', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'WASH'},
    {'seq': 90, 'code': 'SANDBLAST_3', 'name': 'Sand Blasting', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'BLAST'},
    {'seq': 100, 'code': 'DIE_CHECK_2', 'name': 'Die Check', 'conditional': False, 'yes_no': False, 'qc': True, 'center': 'INSPECT'},
    {'seq': 110, 'code': 'FINAL_GRINDING', 'name': 'Final Grinding', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'GRIND'},
    {'seq': 120, 'code': 'TIP_GRINDING', 'name': 'Tip Grinding', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'GRIND'},
    {'seq': 130, 'code': 'WASHING_2', 'name': 'Washing', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'WASH'},
    {'seq': 140, 'code': 'SANDBLAST_4', 'name': 'Sand Blasting', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'BLAST'},
    {'seq': 150, 'code': 'DIE_CHECK_3', 'name': 'Die Check', 'conditional': False, 'yes_no': False, 'qc': True, 'center': 'INSPECT'},
    {'seq': 160, 'code': 'UPPER_ASSEMBLY', 'name': 'Upper Section Assembly', 'conditional': True, 'yes_no': False, 'qc': False, 'center': 'MACHINE'},
    {'seq': 170, 'code': 'UPPER_WELDING', 'name': 'Upper Section Sub-Arc Welding', 'conditional': True, 'yes_no': False, 'qc': False, 'center': 'WELD'},
    {'seq': 180, 'code': 'SHANK_MACHINING', 'name': 'Shank Machining', 'conditional': True, 'yes_no': False, 'qc': False, 'center': 'MACHINE'},
    {'seq': 190, 'code': 'PRESSURE_TEST', 'name': 'Pressure Test', 'conditional': True, 'yes_no': False, 'qc': False, 'center': 'TEST'},
    {'seq': 200, 'code': 'BIT_PHOTOS', 'name': 'Bit Photos', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'PHOTO'},
    {'seq': 210, 'code': 'QC_INSPECTION', 'name': 'QC Inspection', 'conditional': False, 'yes_no': False, 'qc': True, 'center': 'QC'},
    {'seq': 220, 'code': 'FINAL_INSPECTION', 'name': 'Final Inspection', 'conditional': False, 'yes_no': False, 'qc': True, 'center': 'QC'},
    {'seq': 230, 'code': 'PAINTING_BOXING', 'name': 'Painting & Boxing', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'FINISH'},
    {'seq': 240, 'code': 'NOZZLE_INSTALL', 'name': 'Nozzle Installation', 'conditional': False, 'yes_no': False, 'qc': False, 'center': 'FINISH'},
    {'seq': 250, 'code': 'CEREBRO_INSTALL', 'name': 'Cerebro Installation', 'conditional': False, 'yes_no': True, 'qc': False, 'center': 'FINISH'},
    {'seq': 260, 'code': 'CEREBRO_CAP', 'name': 'Cerebro Cap Tightening', 'conditional': False, 'yes_no': True, 'qc': False, 'center': 'FINISH'},
]


class Command(BaseCommand):
    help = 'Seed FC Bit Repair (33 steps) and L3/L4 Manufacture route templates'

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true', help='Actually create routes')

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write('Dry run. Pass --confirm to seed routes.')
            self.stdout.write(f'  FC Repair route: {len(FC_REPAIR_STEPS)} steps')
            self.stdout.write(f'  L3/L4 Manufacture route: {len(L3_L4_MANUFACTURE_STEPS)} steps')
            return

        self._seed_route(
            route_number='RT-FC-REPAIR',
            name='FC Bit Repair Router Sheet (QAS/1006 Rev L)',
            description='Standard 33-step repair process for fixed cutter (PDC) drill bits.',
            workflow_type='REPAIR',
            bit_types=['FC'],
            steps=FC_REPAIR_STEPS,
        )

        self._seed_route(
            route_number='RT-FC-MANUFACTURE',
            name='FC Bit L3/L4 Manufacture Router Sheet',
            description='New build process for Level 3/Level 4 fixed cutter drill bits.',
            workflow_type='MANUFACTURE',
            bit_types=['FC'],
            steps=L3_L4_MANUFACTURE_STEPS,
        )

        self.stdout.write(self.style.SUCCESS('Done seeding process routes.'))

    def _seed_route(self, route_number, name, description, workflow_type, bit_types, steps):
        route, created = ProcessRoute.objects.update_or_create(
            route_number=route_number,
            defaults={
                'name': name,
                'description': description,
                'workflow_type': workflow_type,
                'bit_types': bit_types,
                'is_active': True,
            }
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(f'  {action} route: {route_number} — {name}')

        # Clear existing operations and re-seed
        route.operations.all().delete()
        for step in steps:
            ProcessRouteOperation.objects.create(
                route=route,
                sequence=step['seq'],
                operation_code=step['code'],
                operation_name=step['name'],
                work_center=step['center'],
                requires_qc=step['qc'],
                is_conditional=step['conditional'],
                has_yes_no=step['yes_no'],
            )
        self.stdout.write(f'    → {len(steps)} operations seeded')
