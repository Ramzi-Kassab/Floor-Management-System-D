"""
Seeder for PocketSize reference data.
"""
from django.core.management.base import BaseCommand
from apps.technology.models import PocketSize


class Command(BaseCommand):
    help = 'Seed pocket sizes reference data'

    def handle(self, *args, **options):
        pocket_sizes = [
            # Standard sizes (mm based codes)
            {'code': '8', 'display_name': '8mm', 'diameter_mm': 8.0, 'sort_order': 10},
            {'code': '10.5', 'display_name': '10.5mm', 'diameter_mm': 10.5, 'sort_order': 20},
            {'code': '12', 'display_name': '12mm', 'diameter_mm': 12.0, 'sort_order': 30},
            {'code': '13', 'display_name': '13mm', 'diameter_mm': 13.0, 'sort_order': 40},
            {'code': '13x0.9', 'display_name': '13x0.9mm', 'diameter_mm': 13.0, 'sort_order': 45, 'description': '13mm with 0.9 exposure'},
            {'code': '16', 'display_name': '16mm', 'diameter_mm': 16.0, 'sort_order': 50},
            {'code': '19', 'display_name': '19mm', 'diameter_mm': 19.0, 'sort_order': 60},
            # 4-digit codes (size + substrate type codes)
            {'code': '808', 'display_name': '8-08', 'diameter_mm': 8.0, 'sort_order': 100, 'description': '8mm substrate type 08'},
            {'code': '1005', 'display_name': '10-05', 'diameter_mm': 10.0, 'sort_order': 110, 'description': '10mm substrate type 05'},
            {'code': '1010', 'display_name': '10-10', 'diameter_mm': 10.0, 'sort_order': 120, 'description': '10mm substrate type 10'},
            {'code': '1218', 'display_name': '12-18', 'diameter_mm': 12.0, 'sort_order': 130, 'description': '12mm substrate type 18'},
            {'code': '1303', 'display_name': '13-03', 'diameter_mm': 13.0, 'sort_order': 140, 'description': '13mm substrate type 03'},
            {'code': '1308', 'display_name': '13-08', 'diameter_mm': 13.0, 'sort_order': 150, 'description': '13mm substrate type 08'},
            {'code': '1313', 'display_name': '13-13', 'diameter_mm': 13.0, 'sort_order': 160, 'description': '13mm substrate type 13'},
            {'code': '1318', 'display_name': '13-18', 'diameter_mm': 13.0, 'sort_order': 170, 'description': '13mm substrate type 18'},
            {'code': '1608', 'display_name': '16-08', 'diameter_mm': 16.0, 'sort_order': 180, 'description': '16mm substrate type 08'},
            {'code': '1613', 'display_name': '16-13', 'diameter_mm': 16.0, 'sort_order': 190, 'description': '16mm substrate type 13'},
            {'code': '1618', 'display_name': '16-18', 'diameter_mm': 16.0, 'sort_order': 200, 'description': '16mm substrate type 18'},
            {'code': '1908', 'display_name': '19-08', 'diameter_mm': 19.0, 'sort_order': 210, 'description': '19mm substrate type 08'},
            {'code': '1913', 'display_name': '19-13', 'diameter_mm': 19.0, 'sort_order': 220, 'description': '19mm substrate type 13'},
        ]

        created = 0
        updated = 0

        for data in pocket_sizes:
            obj, was_created = PocketSize.objects.update_or_create(
                code=data['code'],
                defaults={
                    'display_name': data['display_name'],
                    'diameter_mm': data.get('diameter_mm'),
                    'description': data.get('description', ''),
                    'sort_order': data['sort_order'],
                    'is_active': True,
                }
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f'PocketSize: {created} created, {updated} updated. Total: {len(pocket_sizes)}')
        )
