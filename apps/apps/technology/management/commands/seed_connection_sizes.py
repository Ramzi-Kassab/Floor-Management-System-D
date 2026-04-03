"""
Seed connection sizes reference data.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.technology.models import ConnectionSize


class Command(BaseCommand):
    help = 'Seed connection sizes reference data'

    def handle(self, *args, **options):
        data = [
            ('2-3/8', '2 3/8"', Decimal('2.375')),
            ('2-7/8', '2 7/8"', Decimal('2.875')),
            ('3-1/2', '3 1/2"', Decimal('3.500')),
            ('4-1/2', '4 1/2"', Decimal('4.500')),
            ('5-1/2', '5 1/2"', Decimal('5.500')),
            ('6-5/8', '6 5/8"', Decimal('6.625')),
            ('7-5/8', '7 5/8"', Decimal('7.625')),
            ('NC26', 'NC26', Decimal('2.625')),
            ('NC31', 'NC31', Decimal('3.125')),
            ('NC38', 'NC38', Decimal('3.750')),
            ('NC46', 'NC46', Decimal('4.625')),
            ('NC50', 'NC50', Decimal('5.000')),
        ]

        created = 0
        for code, size_inches, size_decimal in data:
            obj, was_created = ConnectionSize.objects.get_or_create(
                code=code,
                defaults={'size_inches': size_inches, 'size_decimal': size_decimal}
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'ConnectionSize: {created} created, {len(data) - created} already exist'))
