"""
Seed connection types reference data.
"""
from django.core.management.base import BaseCommand
from apps.technology.models import ConnectionType


class Command(BaseCommand):
    help = 'Seed connection types reference data'

    def handle(self, *args, **options):
        data = [
            ('API-REG', 'API Regular', 'Standard API regular connection'),
            ('API-IF', 'API Internal Flush', 'Internal flush connection'),
            ('API-FH', 'API Full Hole', 'Full hole connection'),
            ('API-NC', 'API Numbered Connection', 'Numbered connection series'),
            ('HT', 'Hi-Torque', 'High torque connection'),
            ('XT', 'Extreme Torque', 'Extreme torque connection'),
            ('PAC', 'Premium API Connection', 'Premium connection type'),
            ('DS', 'Double Shoulder', 'Double shoulder connection'),
        ]

        created = 0
        for code, name, desc in data:
            obj, was_created = ConnectionType.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc}
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'ConnectionType: {created} created, {len(data) - created} already exist'))
