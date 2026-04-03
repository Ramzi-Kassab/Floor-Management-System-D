"""
Seed Upper Section Types reference data.
Some types cannot be replaced/repaired in KSA.
"""

from django.core.management.base import BaseCommand

from apps.technology.models import UpperSectionType


class Command(BaseCommand):
    help = "Seed Upper Section Types reference data"

    def handle(self, *args, **options):
        upper_section_types = [
            # Can be replaced in KSA
            {
                "code": "STD",
                "name": "Standard Shank",
                "description": "Standard threaded shank connection",
                "can_replace_in_ksa": True,
                "remarks": "Most common type, easily replaceable",
            },
            {
                "code": "EXT",
                "name": "Extended Shank",
                "description": "Extended length shank for specific BHA requirements",
                "can_replace_in_ksa": True,
                "remarks": "Longer shank version, replaceable in KSA",
            },
            {
                "code": "TPW",
                "name": "Two-Piece Welded",
                "description": "Two-piece design with welded connection",
                "can_replace_in_ksa": True,
                "remarks": "Can be repaired by re-welding in KSA",
            },
            # Cannot be replaced in KSA
            {
                "code": "WOS",
                "name": "Welded Over Slot",
                "description": "Welded over slot design for specific applications",
                "can_replace_in_ksa": False,
                "remarks": "Requires special manufacturing process, cannot replace in KSA",
            },
            {
                "code": "SL",
                "name": "Shankless",
                "description": "Integral shankless design",
                "can_replace_in_ksa": False,
                "remarks": "No separate shank - integral body design, cannot be replaced",
            },
            {
                "code": "INT",
                "name": "Integral Body",
                "description": "Full integral body design without separate upper section",
                "can_replace_in_ksa": False,
                "remarks": "Single-piece body, cannot separate upper section",
            },
            {
                "code": "FW",
                "name": "Fusion Welded",
                "description": "Fusion welded connection requiring specialized equipment",
                "can_replace_in_ksa": False,
                "remarks": "Requires specialized fusion welding equipment not available in KSA",
            },
        ]

        created = 0
        for type_data in upper_section_types:
            obj, was_created = UpperSectionType.objects.update_or_create(
                code=type_data["code"],
                defaults={
                    "name": type_data["name"],
                    "description": type_data["description"],
                    "can_replace_in_ksa": type_data["can_replace_in_ksa"],
                    "remarks": type_data["remarks"],
                    "is_active": True,
                },
            )
            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"UpperSectionType: {created} created, {len(upper_section_types) - created} already exist"
            )
        )
