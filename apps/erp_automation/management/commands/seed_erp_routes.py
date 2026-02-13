"""
Seed the 37 approved ERP routes into the ERPRoute model.

Includes:
  - 32 FC Repair routes (ROUTE-0091 to ROUTE-0122) using binary pattern
  - 5 special routes (ROUTE-0124, 0125, 0126, 0132, 0134)

Usage:
    python manage.py seed_erp_routes              # Dry run
    python manage.py seed_erp_routes --confirm     # Actually create/update
"""
from django.core.management.base import BaseCommand
from apps.erp_automation.models import ERPRoute


# =============================================================================
# Binary pattern for the 32 FC Repair routes (ROUTE-0091 to ROUTE-0122)
# =============================================================================
#
# 4 groups of 8 routes each:
#   AB With Port:    0091-0098
#   AB No Port:      0099-0106
#   JUMBO With Port: 0107-0114
#   JUMBO No Port:   0115-0122
#
# Within each group of 8, the offset encodes modifier flags:
#   +0 = Standard (no flags)
#   +1 = USR only
#   +2 = HF only
#   +3 = C&S only
#   +4 = USR + HF
#   +5 = USR + C&S
#   +6 = HF + C&S
#   +7 = USR + HF + C&S

GROUPS = [
    # (base_route_number, size_class, has_port)
    (91,  'AB',    True),
    (99,  'AB',    False),
    (107, 'JUMBO', True),
    (115, 'JUMBO', False),
]

MODIFIER_COMBOS = [
    # (offset, has_usr, has_hardfacing, has_crush_shear, label)
    (0, False, False, False, 'Standard'),
    (1, True,  False, False, 'USR'),
    (2, False, True,  False, 'Hardfacing'),
    (3, False, False, True,  'C&S'),
    (4, True,  True,  False, 'USR + Hardfacing'),
    (5, True,  False, True,  'USR + C&S'),
    (6, False, True,  True,  'Hardfacing + C&S'),
    (7, True,  True,  True,  'USR + Hardfacing + C&S'),
]


def _build_repair_routes():
    """Generate the 32 FC Repair routes from the binary pattern."""
    routes = []
    for base, size_class, has_port in GROUPS:
        port_label = 'With Port' if has_port else 'No Port'
        for offset, has_usr, has_hf, has_cs, mod_label in MODIFIER_COMBOS:
            route_num = base + offset
            route_number = f'ROUTE-{route_num:04d}'
            name = f'FC-R {size_class} {port_label} {mod_label}'
            routes.append({
                'route_number': route_number,
                'name': name,
                'item_group': '',
                'bit_type': 'FC',
                'level': 'REPAIR',
                'size_class': size_class,
                'has_port': has_port,
                'has_usr': has_usr,
                'has_hardfacing': has_hf,
                'has_crush_shear': has_cs,
                'has_retro': False,
                'has_grinding': False,
                'is_sealed': None,
                'has_cc': None,
                'approved': True,
                'approved_by': '',
                'is_active': True,
            })
    return routes


# =============================================================================
# Special routes
# =============================================================================

SPECIAL_ROUTES = [
    {
        'route_number': 'ROUTE-0124',
        'name': 'FC-R AB Re-Run',
        'item_group': '',
        'bit_type': 'FC',
        'level': 'RERUN',
        'size_class': 'AB',
        'has_port': None,
        'has_usr': False,
        'has_hardfacing': False,
        'has_crush_shear': False,
        'has_retro': False,
        'has_grinding': False,
        'is_sealed': None,
        'has_cc': None,
        'approved': True,
        'approved_by': '',
        'is_active': True,
    },
    {
        'route_number': 'ROUTE-0125',
        'name': 'FC-R Jumbo Re-Run',
        'item_group': '',
        'bit_type': 'FC',
        'level': 'RERUN',
        'size_class': 'JUMBO',
        'has_port': None,
        'has_usr': False,
        'has_hardfacing': False,
        'has_crush_shear': False,
        'has_retro': False,
        'has_grinding': False,
        'is_sealed': None,
        'has_cc': None,
        'approved': True,
        'approved_by': '',
        'is_active': True,
    },
    {
        'route_number': 'ROUTE-0126',
        'name': 'FC-R AB No Port USR Only',
        'item_group': '',
        'bit_type': 'FC',
        'level': 'REPAIR',
        'size_class': 'AB',
        'has_port': False,
        'has_usr': True,
        'has_hardfacing': False,
        'has_crush_shear': False,
        'has_retro': False,
        'has_grinding': False,
        'is_sealed': None,
        'has_cc': None,
        'approved': True,
        'approved_by': '',
        'is_active': True,
    },
    {
        'route_number': 'ROUTE-0132',
        'name': 'RC Inspection Only',
        'item_group': '',
        'bit_type': 'RC',
        'level': 'INSPECTION',
        'size_class': '',
        'has_port': None,
        'has_usr': False,
        'has_hardfacing': False,
        'has_crush_shear': False,
        'has_retro': False,
        'has_grinding': False,
        'is_sealed': None,
        'has_cc': None,
        'approved': True,
        'approved_by': '',
        'is_active': True,
    },
    {
        'route_number': 'ROUTE-0134',
        'name': 'FC Inspection Only',
        'item_group': '',
        'bit_type': 'FC',
        'level': 'INSPECTION',
        'size_class': '',
        'has_port': None,
        'has_usr': False,
        'has_hardfacing': False,
        'has_crush_shear': False,
        'has_retro': False,
        'has_grinding': False,
        'is_sealed': None,
        'has_cc': None,
        'approved': True,
        'approved_by': '',
        'is_active': True,
    },
]


def _build_all_routes():
    """Build the full list of 37 approved routes."""
    return _build_repair_routes() + SPECIAL_ROUTES


class Command(BaseCommand):
    help = 'Seed the 37 approved ERP routes (32 FC Repair + 5 special)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm', action='store_true',
            help='Actually create/update routes (dry run by default)',
        )

    def handle(self, *args, **options):
        all_routes = _build_all_routes()

        if not options['confirm']:
            self.stdout.write('Dry run. Pass --confirm to create/update routes.\n')
            self.stdout.write(f'{"Route":<15s} {"Name":<45s} {"Type":<5s} {"Level":<12s} '
                              f'{"Size":<6s} {"Port":<6s} {"USR":<5s} {"HF":<5s} {"C&S":<5s}')
            self.stdout.write('-' * 110)
            for r in all_routes:
                port_str = {True: 'Yes', False: 'No', None: '-'}.get(r['has_port'], '-')
                self.stdout.write(
                    f"{r['route_number']:<15s} {r['name']:<45s} {r['bit_type']:<5s} "
                    f"{r['level']:<12s} {r['size_class']:<6s} {port_str:<6s} "
                    f"{'Y' if r['has_usr'] else '-':<5s} "
                    f"{'Y' if r['has_hardfacing'] else '-':<5s} "
                    f"{'Y' if r['has_crush_shear'] else '-':<5s}"
                )
            self.stdout.write(f'\nTotal: {len(all_routes)} routes would be seeded.')
            return

        created_count = 0
        updated_count = 0

        for data in all_routes:
            route_number = data.pop('route_number')
            obj, created = ERPRoute.objects.update_or_create(
                route_number=route_number,
                defaults=data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  Created: {route_number} - {data["name"]}'
                ))
            else:
                updated_count += 1
                self.stdout.write(
                    f'  Updated: {route_number} - {data["name"]}'
                )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Created: {created_count}, Updated: {updated_count}, '
            f'Total: {len(all_routes)}'
        ))
