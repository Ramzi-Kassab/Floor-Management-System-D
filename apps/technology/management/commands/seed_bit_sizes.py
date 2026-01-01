"""
ARDT FMS - Seed Bit Sizes
Phase 2: Products & Drill Bit Tracking

Creates standard bit sizes used in drilling operations.
"""

from django.core.management.base import BaseCommand

from apps.technology.models import BitSize


class Command(BaseCommand):
    help = "Seed standard bit sizes for ARDT drill bit tracking"

    def handle(self, *args, **options):
        bit_sizes = [
            {"code": "3.750", "size_decimal": "3.750", "size_display": '3 3/4"', "size_inches": "3 3/4"},
            {"code": "3.875", "size_decimal": "3.875", "size_display": '3 7/8"', "size_inches": "3 7/8"},
            {"code": "4.750", "size_decimal": "4.750", "size_display": '4 3/4"', "size_inches": "4 3/4"},
            {"code": "5.875", "size_decimal": "5.875", "size_display": '5 7/8"', "size_inches": "5 7/8"},
            {"code": "6.000", "size_decimal": "6.000", "size_display": '6"', "size_inches": "6"},
            {"code": "6.125", "size_decimal": "6.125", "size_display": '6 1/8"', "size_inches": "6 1/8"},
            {"code": "6.500", "size_decimal": "6.500", "size_display": '6 1/2"', "size_inches": "6 1/2"},
            {"code": "6.750", "size_decimal": "6.750", "size_display": '6 3/4"', "size_inches": "6 3/4"},
            {"code": "7.875", "size_decimal": "7.875", "size_display": '7 7/8"', "size_inches": "7 7/8"},
            {"code": "8.375", "size_decimal": "8.375", "size_display": '8 3/8"', "size_inches": "8 3/8"},
            {"code": "8.500", "size_decimal": "8.500", "size_display": '8 1/2"', "size_inches": "8 1/2"},
            {"code": "8.750", "size_decimal": "8.750", "size_display": '8 3/4"', "size_inches": "8 3/4"},
            {"code": "9.500", "size_decimal": "9.500", "size_display": '9 1/2"', "size_inches": "9 1/2"},
            {"code": "9.875", "size_decimal": "9.875", "size_display": '9 7/8"', "size_inches": "9 7/8"},
            {"code": "10.625", "size_decimal": "10.625", "size_display": '10 5/8"', "size_inches": "10 5/8"},
            {"code": "12.250", "size_decimal": "12.250", "size_display": '12 1/4"', "size_inches": "12 1/4"},
            {"code": "14.750", "size_decimal": "14.750", "size_display": '14 3/4"', "size_inches": "14 3/4"},
            {"code": "17.500", "size_decimal": "17.500", "size_display": '17 1/2"', "size_inches": "17 1/2"},
        ]

        created_count = 0
        updated_count = 0

        for size_data in bit_sizes:
            obj, created = BitSize.objects.update_or_create(
                code=size_data["code"],
                defaults={
                    "size_decimal": size_data["size_decimal"],
                    "size_display": size_data["size_display"],
                    "size_inches": size_data["size_inches"],
                    "is_active": True,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Bit Sizes: {created_count} created, {updated_count} updated. Total: {BitSize.objects.count()}"
            )
        )
