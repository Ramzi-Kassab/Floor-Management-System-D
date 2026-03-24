"""
Seed special technologies -- keep only the 7 relevant ones,
deactivate unknowns.

Usage:
    python manage.py seed_special_technologies --confirm
"""
from django.core.management.base import BaseCommand
from apps.technology.models import SpecialTechnology


KEEP_TECHNOLOGIES = [
    {'code': 'CF', 'name': 'Cerebro Force', 'description': 'Cerebro sensor installed from shank side. Remove/install or close cap steps.'},
    {'code': 'CP', 'name': 'Cerebro Puck', 'description': 'Cerebro puck. USR NOT possible in KSA -- contact technical.'},
    {'code': 'TP', 'name': 'Torpedo', 'description': 'Torpedo sensor from internal diameter side. USR IS possible for size >= 8 1/2 in. Thread protector if no torpedo.'},
    {'code': 'CS', 'name': 'Crush & Shear', 'description': 'Crush & shear components. New: install. Repair: replace. Install, heat, TIG weld, cool.'},
    {'code': 'ES', 'name': 'Erosion Sleeve', 'description': 'Erosion sleeve protection. Remove before work, install after.'},
    {'code': 'SL', 'name': 'Shankless', 'description': 'Shankless design. USR NOT possible in KSA -- contact technical.'},
    {'code': 'CR', 'name': 'Cruser', 'description': 'Special cutter type -- affects cutter preparation and BOM handling.'},
]

DEACTIVATE_CODES = ['AXIS', 'DS', 'FM', 'TCD', 'SST', 'RGD', 'VBS']


class Command(BaseCommand):
    help = 'Seed special technologies and deactivate unused ones'

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true', help='Actually create/update')

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write('Dry run. Pass --confirm to apply.')
            self.stdout.write('\nKEEP/CREATE:')
            for t in KEEP_TECHNOLOGIES:
                self.stdout.write(f'  {t["code"]:5s} {t["name"]}')
            self.stdout.write(f'\nDEACTIVATE: {", ".join(DEACTIVATE_CODES)}')
            return

        created = 0
        updated = 0
        for data in KEEP_TECHNOLOGIES:
            obj, was_created = SpecialTechnology.objects.update_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'is_active': True,
                }
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {data["code"]} -- {data["name"]}'))
            else:
                updated += 1
                self.stdout.write(f'  Updated: {data["code"]} -- {data["name"]}')

        deactivated = SpecialTechnology.objects.filter(
            code__in=DEACTIVATE_CODES, is_active=True
        ).update(is_active=False)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {created} created, {updated} updated, {deactivated} deactivated.'
        ))
