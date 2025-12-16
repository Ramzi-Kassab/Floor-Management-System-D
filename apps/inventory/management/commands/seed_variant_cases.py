"""
Seed Variant Cases - Master data for item variants.
Creates the standard 10 variant cases used across all items.

Based on user specification:
- 6 ARDT-owned cases (New Stock, Used Stock, Retrofit, E&O, Ground, Standard Reclaim)
- 4 CLIENT-owned cases (LSTK New, LSTK Used, Hall New, Hall Used)
"""
from django.core.management.base import BaseCommand

from apps.inventory.models import VariantCase


class Command(BaseCommand):
    help = "Seed variant cases master data (10 standard cases)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing variant cases before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted_count = VariantCase.objects.all().delete()[0]
            self.stdout.write(f"Deleted {deleted_count} existing variant cases")

        self.stdout.write("Seeding Variant Cases (10 standard cases)...")

        # Define the 10 standard variant cases per user specification
        cases = [
            # ARDT Owned - New/Used Stock
            {
                "code": "ARDT-NEW",
                "name": "ARDT New Stock",
                "condition": "NEW",
                "acquisition": "PURCHASED",
                "reclaim_category": "",
                "ownership": "ARDT",
                "client_code": "",
                "description": "New items purchased and owned by ARDT",
                "display_order": 1,
            },
            {
                "code": "ARDT-USED",
                "name": "ARDT Used Stock",
                "condition": "USED",
                "acquisition": "PURCHASED",
                "reclaim_category": "",
                "ownership": "ARDT",
                "client_code": "",
                "description": "Used items purchased and owned by ARDT",
                "display_order": 2,
            },
            # ARDT Owned - Reclaimed Items
            {
                "code": "ARDT-RET",
                "name": "Retrofit (ARDT)",
                "condition": "NEW",
                "acquisition": "RECLAIMED",
                "reclaim_category": "RETROFIT",
                "ownership": "ARDT",
                "client_code": "",
                "description": "Reclaimed items fully refurbished to new condition",
                "display_order": 3,
            },
            {
                "code": "ARDT-EO",
                "name": "E&O (ARDT)",
                "condition": "NEW",
                "acquisition": "RECLAIMED",
                "reclaim_category": "E_AND_O",
                "ownership": "ARDT",
                "client_code": "",
                "description": "Excess or obsolete inventory, typically discounted",
                "display_order": 4,
            },
            {
                "code": "ARDT-GRD",
                "name": "Ground (ARDT)",
                "condition": "USED",
                "acquisition": "RECLAIMED",
                "reclaim_category": "GROUND",
                "ownership": "ARDT",
                "client_code": "",
                "description": "Reclaimed with surface grinding, partial life remaining",
                "display_order": 5,
            },
            {
                "code": "ARDT-RCL",
                "name": "Standard Reclaim (ARDT)",
                "condition": "USED",
                "acquisition": "RECLAIMED",
                "reclaim_category": "STANDARD",
                "ownership": "ARDT",
                "client_code": "",
                "description": "Standard reclaimed items, usable condition",
                "display_order": 6,
            },
            # CLIENT Owned - LSTK
            {
                "code": "LSTK-NEW",
                "name": "LSTK New",
                "condition": "NEW",
                "acquisition": "CLIENT_PROVIDED",
                "reclaim_category": "",
                "ownership": "CLIENT",
                "client_code": "LSTK",
                "description": "New items provided by LSTK client",
                "display_order": 7,
            },
            {
                "code": "LSTK-USED",
                "name": "LSTK Used",
                "condition": "USED",
                "acquisition": "CLIENT_PROVIDED",
                "reclaim_category": "",
                "ownership": "CLIENT",
                "client_code": "LSTK",
                "description": "Used items provided by LSTK client",
                "display_order": 8,
            },
            # CLIENT Owned - Halliburton
            {
                "code": "HALL-NEW",
                "name": "Hall New",
                "condition": "NEW",
                "acquisition": "CLIENT_PROVIDED",
                "reclaim_category": "",
                "ownership": "CLIENT",
                "client_code": "Halliburton",
                "description": "New items provided by Halliburton client",
                "display_order": 9,
            },
            {
                "code": "HALL-USED",
                "name": "Hall Used",
                "condition": "USED",
                "acquisition": "CLIENT_PROVIDED",
                "reclaim_category": "",
                "ownership": "CLIENT",
                "client_code": "Halliburton",
                "description": "Used items provided by Halliburton client",
                "display_order": 10,
            },
        ]

        created_count = 0
        updated_count = 0
        for case_data in cases:
            case, created = VariantCase.objects.update_or_create(
                code=case_data["code"],
                defaults={
                    "name": case_data["name"],
                    "condition": case_data["condition"],
                    "acquisition": case_data["acquisition"],
                    "reclaim_category": case_data["reclaim_category"],
                    "ownership": case_data["ownership"],
                    "client_code": case_data["client_code"],
                    "description": case_data["description"],
                    "display_order": case_data["display_order"],
                    "is_active": True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"  Created: {case.code} - {case.name}")
            else:
                updated_count += 1
                self.stdout.write(f"  Updated: {case.code} - {case.name}")

        self.stdout.write(self.style.SUCCESS(
            f"\nTotal variant cases: {VariantCase.objects.count()} (created: {created_count}, updated: {updated_count})"
        ))
