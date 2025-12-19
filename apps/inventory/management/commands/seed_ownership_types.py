"""
Seed command for OwnershipType - Ownership type master data.

Usage:
    python manage.py seed_ownership_types
"""

from django.core.management.base import BaseCommand
from apps.inventory.models import OwnershipType


class Command(BaseCommand):
    help = "Seed ownership types (OWNED, CLIENT, CONSIGNMENT, etc.)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Ownership Types...\n")

        # Ownership types defining stock ownership relationship
        # (code, name, description, is_ardt_owned, requires_party, include_in_valuation, display_order)
        ownership_types = [
            (
                "OWNED",
                "ARDT Owned",
                "Stock fully owned by ARDT",
                True, False, True, 1
            ),
            (
                "CLIENT",
                "Client Owned",
                "Client-owned stock held by ARDT (client property)",
                False, True, False, 2
            ),
            (
                "CONSIGN-IN",
                "Consignment In",
                "Vendor-owned stock at ARDT (consignment inventory)",
                False, True, False, 3
            ),
            (
                "CONSIGN-OUT",
                "Consignment Out",
                "ARDT-owned stock at customer site (VMI)",
                True, True, True, 4
            ),
            (
                "THIRD-PARTY",
                "Third Party",
                "Third-party stock being processed (tolling/processing)",
                False, True, False, 5
            ),
            (
                "LOAN",
                "Loaned",
                "Equipment on loan (temporary)",
                False, True, False, 6
            ),
            (
                "RENTAL",
                "Rental",
                "Rental equipment",
                False, True, False, 7
            ),
            (
                "DEMO",
                "Demo",
                "Demo/evaluation stock (temporary)",
                True, False, True, 8
            ),
            (
                "FREE-ISSUE",
                "Free Issue",
                "Free-issued by customer for processing",
                False, True, False, 9
            ),
        ]

        created_count = 0
        for code, name, desc, ardt_owned, req_party, valuation, order in ownership_types:
            obj, created = OwnershipType.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": desc,
                    "is_ardt_owned": ardt_owned,
                    "requires_party": req_party,
                    "include_in_valuation": valuation,
                    "display_order": order,
                    "is_active": True,
                }
            )
            if created:
                self.stdout.write(f"  Created: {name}")
                created_count += 1
            else:
                self.stdout.write(f"  Exists: {name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTotal ownership types: {OwnershipType.objects.count()} (new: {created_count})"
            )
        )
