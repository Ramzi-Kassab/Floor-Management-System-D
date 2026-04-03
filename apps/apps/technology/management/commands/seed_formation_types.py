"""
Seed formation types reference data (Saudi Arabia formations).
"""
from django.core.management.base import BaseCommand
from apps.technology.models import FormationType


class Command(BaseCommand):
    help = 'Seed Saudi Arabia formation types reference data'

    def handle(self, *args, **options):
        data = [
            # code, name, age, rock_type, hardness
            ('ARAB-D', 'Arab-D', 'Late Jurassic', 'Carbonate', 'Medium'),
            ('ARAB-C', 'Arab-C', 'Late Jurassic', 'Carbonate', 'Medium'),
            ('ARAB-A', 'Arab-A', 'Late Jurassic', 'Carbonate', 'Medium'),
            ('KHUFF', 'Khuff', 'Late Permian', 'Carbonate/Dolomite', 'Hard'),
            ('KHUFF-A', 'Khuff-A', 'Late Permian', 'Carbonate', 'Hard'),
            ('KHUFF-B', 'Khuff-B', 'Late Permian', 'Carbonate', 'Hard'),
            ('KHUFF-C', 'Khuff-C', 'Late Permian', 'Carbonate', 'Hard'),
            ('UNAYZAH', 'Unayzah', 'Permian', 'Sandstone', 'Medium'),
            ('UNAYZAH-A', 'Unayzah-A', 'Permian', 'Sandstone', 'Medium'),
            ('UNAYZAH-B', 'Unayzah-B', 'Permian', 'Sandstone', 'Medium'),
            ('JAUF', 'Jauf', 'Devonian', 'Sandstone', 'Medium'),
            ('QUSAIBA', 'Qusaiba', 'Silurian', 'Shale', 'Soft'),
            ('SAQ', 'Saq', 'Cambrian-Ordovician', 'Sandstone', 'Hard'),
            ('QASIM', 'Qasim', 'Ordovician', 'Mixed', 'Medium'),
            ('SARAH', 'Sarah', 'Ordovician', 'Sandstone', 'Medium'),
            ('ZARQA', 'Zarqa', 'Ordovician-Silurian', 'Sandstone', 'Medium'),
            ('WASIA', 'Wasia', 'Cretaceous', 'Sandstone', 'Medium'),
            ('BIYADH', 'Biyadh', 'Cretaceous', 'Sandstone', 'Medium'),
            ('SHUAIBA', 'Shuaiba', 'Cretaceous', 'Carbonate', 'Medium'),
            ('HANIFA', 'Hanifa', 'Late Jurassic', 'Carbonate', 'Medium'),
            ('TUWAIQ', 'Tuwaiq', 'Late Jurassic', 'Carbonate', 'Medium'),
        ]

        created = 0
        for code, name, age, rock_type, hardness in data:
            obj, was_created = FormationType.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'age': age,
                    'rock_type': rock_type,
                    'hardness': hardness
                }
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'FormationType: {created} created, {len(data) - created} already exist'))
