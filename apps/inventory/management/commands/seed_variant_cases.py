"""
Seed Variant Cases - Master data for item variants.
Creates the standard variant cases used across all items.

Key Variant Cases for PDC Cutters:
- NEW-PUR: New Purchased (from suppliers)
- NEW-EO: E&O (Excess & Obsolete, new condition but discounted)
- GRD-EO: E&O Ground (ground cutters moved to E&O stock)
- USED-RCL: Used Reclaimed (standard reclaim)
- CLI-RCL: Client Reclaimed (client-provided used cutters)
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
                "code": "NEW-EO",
                "name": "E&O (Excess & Obsolete)",
                "condition": "NEW",
                "acquisition": "RECLAIMED",
                "reclaim_category": "E_AND_O",
                "ownership": "ARDT",
                "description": "Excess or obsolete inventory, new condition but discounted",
                "display_order": 4,
            },
            # E&O Ground - Ground cutters that go into E&O stock
            {
                "code": "GRD-EO",
                "name": "E&O Ground",
                "condition": "USED",
                "acquisition": "RECLAIMED",
                "reclaim_category": "GROUND",
                "ownership": "ARDT",
                "description": "Ground cutters (surface damage) moved to E&O stock",
                "display_order": 5,
            },
            # USED Items - ARDT Owned
            {
                "code": "USED-RCL",
                "name": "Used Reclaimed",
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
                "code": "CLI-RCL",
                "name": "Client Reclaimed",
                "condition": "USED",
                "acquisition": "CLIENT_PROVIDED",
                "reclaim_category": "",
                "ownership": "CLIENT",
                "description": "Used/reclaimed items provided by client",
                "display_order": 8,
            },
        ]

        # Track old codes to clean up
        old_codes = ["NEW-ENO", "USED-GRD", "USED-STD", "CLI-USED"]

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

        # Deactivate old codes if they exist
        deactivated = VariantCase.objects.filter(code__in=old_codes).update(is_active=False)
        if deactivated:
            self.stdout.write(f"  Deactivated {deactivated} old variant case(s)")

        self.stdout.write(self.style.SUCCESS(f"\nTotal active variant cases: {VariantCase.objects.filter(is_active=True).count()} (new: {created_count})"))
