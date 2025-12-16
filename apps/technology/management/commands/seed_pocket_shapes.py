"""
Seeder for PocketShape reference data.
"""
from django.core.management.base import BaseCommand
from apps.technology.models import PocketShape


class Command(BaseCommand):
    help = 'Seed pocket shapes reference data'

    def handle(self, *args, **options):
        pocket_shapes = [
            {
                'code': 'FLAT',
                'name': 'Flat Bottom',
                'description': 'Standard flat bottom pocket',
                'notes': 'The most common shape. Used for all standard cylindrical cutters '
                         '(like Long Substrate (LS) and Short Substrate (SS)), ensuring the '
                         'entire cutter base is supported.'
            },
            {
                'code': 'CONICAL',
                'name': 'Conical',
                'description': 'Conical/Drill Point pocket',
                'notes': "Also known as 'Drill Point.' Used primarily for press-fit stud cutters "
                         "where the cone angle helps lock the cutter in place."
            },
            {
                'code': 'SPHERICAL',
                'name': 'Spherical',
                'description': 'Ball bottom pocket',
                'notes': "Also known as 'Ball Bottom.' Used for seating spherical-base inserts "
                         "(like Ballistic/Button TCI) to aid self-centering and support."
            },
            {
                'code': 'CORNER_RADIUS',
                'name': 'Corner Radius',
                'description': 'Bull nose pocket',
                'notes': "Also known as 'Bull Nose.' This is a flat bottom with rounded corners "
                         "to eliminate stress points, common in high-stress applications."
            },
            {
                'code': 'OPEN_CYL',
                'name': 'Open Cylindrical',
                'description': 'Standard cylindrical pocket opening',
                'notes': "Refers to the pocket for standard cylindrical cutters. The base of this "
                         "pocket is always a Flat Bottom. Long Substrate (LS) and Short Substrate (SS) "
                         "are variations of the cutter type, not the pocket shape."
            },
        ]

        created = 0
        existing = 0

        for data in pocket_shapes:
            obj, was_created = PocketShape.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'notes': data['notes'],
                    'is_active': True,
                }
            )
            if was_created:
                created += 1
            else:
                existing += 1

        self.stdout.write(
            self.style.SUCCESS(f'PocketShape: {created} created, {existing} already exist')
        )
