"""
Seed Breaker Slots reference data.
Breaker slots are used for gripping the bit with a bit breaker tool during make-up and break-out.
"""

from django.core.management.base import BaseCommand

from apps.technology.models import BreakerSlot
from apps.workorders.models import BitSize


class Command(BaseCommand):
    help = "Seed Breaker Slots reference data"

    def handle(self, *args, **options):
        # Get bit sizes for compatibility
        sizes = {size.size_inches: size for size in BitSize.objects.all()}

        breaker_slots = [
            # Small bits (6" - 8 1/2")
            {
                "mat_no": "BS-001",
                "slot_width": 25.4,  # 1 inch
                "slot_depth": 12.7,  # 0.5 inch
                "slot_length": 50.8,  # 2 inches
                "material": "4140",
                "hardness": "28-32 HRC",
                "compatible_sizes": ["6", "6 1/2", "6 3/4", "7 7/8", "8 1/2"],
                "remarks": "Standard breaker slot for small PDC bits",
            },
            {
                "mat_no": "BS-002",
                "slot_width": 31.75,  # 1.25 inch
                "slot_depth": 15.88,  # 0.625 inch
                "slot_length": 63.5,  # 2.5 inches
                "material": "4145",
                "hardness": "30-34 HRC",
                "compatible_sizes": ["8 1/2", "8 3/4", "9 1/2", "9 7/8"],
                "remarks": "Medium breaker slot for intermediate PDC bits",
            },
            # Large bits (10" - 12 1/4")
            {
                "mat_no": "BS-003",
                "slot_width": 38.1,  # 1.5 inch
                "slot_depth": 19.05,  # 0.75 inch
                "slot_length": 76.2,  # 3 inches
                "material": "4145",
                "hardness": "30-34 HRC",
                "compatible_sizes": ["10 5/8", "12 1/4"],
                "remarks": "Large breaker slot for large PDC bits",
            },
            # Heavy-duty slot
            {
                "mat_no": "BS-004",
                "slot_width": 44.45,  # 1.75 inch
                "slot_depth": 22.23,  # 0.875 inch
                "slot_length": 88.9,  # 3.5 inches
                "material": "4340",
                "hardness": "32-36 HRC",
                "compatible_sizes": ["12 1/4", "14 3/4", "17 1/2"],
                "remarks": "Heavy-duty breaker slot for large diameter bits",
            },
            # Chrome-Moly high-strength
            {
                "mat_no": "BS-005",
                "slot_width": 31.75,
                "slot_depth": 15.88,
                "slot_length": 63.5,
                "material": "CrMo",
                "hardness": "34-38 HRC",
                "compatible_sizes": ["8 1/2", "8 3/4", "9 1/2"],
                "remarks": "High-strength chrome-moly breaker slot for demanding applications",
            },
        ]

        created = 0
        for slot_data in breaker_slots:
            compatible_size_codes = slot_data.pop("compatible_sizes", [])

            obj, was_created = BreakerSlot.objects.update_or_create(
                mat_no=slot_data["mat_no"],
                defaults={
                    "slot_width": slot_data["slot_width"],
                    "slot_depth": slot_data["slot_depth"],
                    "slot_length": slot_data.get("slot_length"),
                    "material": slot_data["material"],
                    "hardness": slot_data.get("hardness", ""),
                    "remarks": slot_data.get("remarks", ""),
                    "is_active": True,
                },
            )

            # Add compatible sizes
            for size_code in compatible_size_codes:
                if size_code in sizes:
                    obj.compatible_sizes.add(sizes[size_code])

            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"BreakerSlot: {created} created, {len(breaker_slots) - created} already exist"
            )
        )
