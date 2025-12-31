"""
Seed Variant Cases - Master data for item variants.
Creates the standard ~10 variant cases used across all items.
"""
from django.core.management.base import BaseCommand

from apps.inventory.models import VariantCase


class Command(BaseCommand):
    help = "Seed variant cases master data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Variant Cases...")

        # Define the standard variant cases
        cases = [
            # NEW Items - ARDT Owned
            {
                "code": "NEW-PUR",
                "name": "New Purchased",
                "condition": "NEW",
                "acquisition": "PURCHASED",
                "reclaim_category": "",
                "ownership": "ARDT",
                "description": "Brand new items purchased from suppliers",
                "display_order": 1,
            },
            {
                "code": "NEW-MFG",
                "name": "New Manufactured",
                "condition": "NEW",
                "acquisition": "MANUFACTURED",
                "reclaim_category": "",
                "ownership": "ARDT",
                "description": "New items manufactured in-house",
                "display_order": 2,
            },
            {
                "code": "NEW-RET",
                "name": "Retrofit (as New)",
                "condition": "NEW",
                "acquisition": "RECLAIMED",
                "reclaim_category": "RETROFIT",
                "ownership": "ARDT",
                "description": "Reclaimed items fully refurbished to new condition",
                "display_order": 3,
            },
            {
                "code": "NEW-ENO",
                "name": "E&O (Excess & Obsolete)",
                "condition": "NEW",
                "acquisition": "RECLAIMED",
                "reclaim_category": "E_AND_O",
                "ownership": "ARDT",
                "description": "Excess or obsolete inventory, new condition but discounted",
                "display_order": 4,
            },
            # USED Items - ARDT Owned
            {
                "code": "USED-GRD",
                "name": "Ground (Surface Damage)",
                "condition": "USED",
                "acquisition": "RECLAIMED",
                "reclaim_category": "GROUND",
                "ownership": "ARDT",
                "description": "Reclaimed with surface grinding, partial life remaining",
                "display_order": 5,
            },
            {
                "code": "USED-STD",
                "name": "Standard Reclaim",
                "condition": "USED",
                "acquisition": "RECLAIMED",
                "reclaim_category": "STANDARD",
                "ownership": "ARDT",
                "description": "Standard reclaimed items, usable condition",
                "display_order": 6,
            },
            # CLIENT Owned Items
            {
                "code": "CLI-NEW",
                "name": "Client New",
                "condition": "NEW",
                "acquisition": "CLIENT_PROVIDED",
                "reclaim_category": "",
                "ownership": "CLIENT",
                "description": "New items provided by client for repair work",
                "display_order": 7,
            },
            {
                "code": "CLI-USED",
                "name": "Client Used",
                "condition": "USED",
                "acquisition": "CLIENT_PROVIDED",
                "reclaim_category": "",
                "ownership": "CLIENT",
                "description": "Used/reclaimed items provided by client",
                "display_order": 8,
            },
        ]

        created_count = 0
        for case_data in cases:
            case, created = VariantCase.objects.update_or_create(
                code=case_data["code"],
                defaults={
                    "name": case_data["name"],
                    "condition": case_data["condition"],
                    "acquisition": case_data["acquisition"],
                    "reclaim_category": case_data["reclaim_category"],
                    "ownership": case_data["ownership"],
                    "description": case_data["description"],
                    "display_order": case_data["display_order"],
                    "is_active": True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"  Created: {case.code} - {case.name}")
            else:
                self.stdout.write(f"  Updated: {case.code} - {case.name}")

        self.stdout.write(self.style.SUCCESS(f"\nTotal variant cases: {VariantCase.objects.count()} (new: {created_count})"))
