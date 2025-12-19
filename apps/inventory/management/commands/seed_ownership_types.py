"""
Seed command for OwnershipType - Ownership type master data.

Simplified to 4 core types for clarity:
- OWNED: We own stock (on our balance sheet)
- CLIENT: Client owns stock, we hold it
- CONSIGNMENT_IN: Vendor owns stock at our location
- CONSIGNMENT_OUT: We own stock at customer site

Usage:
    python manage.py seed_ownership_types
"""

from django.core.management.base import BaseCommand
from apps.inventory.models import OwnershipType


class Command(BaseCommand):
    help = "Seed ownership types (OWNED, CLIENT, CONSIGNMENT_IN, CONSIGNMENT_OUT)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Ownership Types (4 core types)...\n")

        # Ownership types - simplified to 4 core types
        # (code, name, description, is_ardt_owned, requires_party, affects_balance_sheet, include_in_valuation, display_order)
        ownership_types = [
            (
                "OWNED",
                "Owned by ARDT",
                "Stock fully owned by ARDT - appears on our balance sheet as inventory asset",
                True, False, True, True, 1
            ),
            (
                "CLIENT",
                "Client Owned",
                "Client-owned stock held by ARDT - we have custodial responsibility, not ownership",
                False, True, False, False, 2
            ),
            (
                "CONSIGN-IN",
                "Consignment In",
                "Vendor-owned stock at ARDT location - vendor's asset until we use/sell it",
                False, True, False, False, 3
            ),
            (
                "CONSIGN-OUT",
                "Consignment Out",
                "ARDT-owned stock at customer site - our asset in their custody (VMI)",
                True, True, True, True, 4
            ),
        ]

        created_count = 0
        updated_count = 0

        for code, name, desc, ardt_owned, req_party, balance_sheet, valuation, order in ownership_types:
            obj, created = OwnershipType.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": desc,
                    "is_ardt_owned": ardt_owned,
                    "requires_party": req_party,
                    "affects_balance_sheet": balance_sheet,
                    "include_in_valuation": valuation,
                    "display_order": order,
                    "is_active": True,
                }
            )
            if created:
                self.stdout.write(f"  Created: {name}")
                created_count += 1
            else:
                self.stdout.write(f"  Updated: {name}")
                updated_count += 1

        # Deactivate old types that are no longer core
        old_types = OwnershipType.objects.exclude(
            code__in=["OWNED", "CLIENT", "CONSIGN-IN", "CONSIGN-OUT"]
        )
        deactivated = old_types.update(is_active=False)
        if deactivated:
            self.stdout.write(f"  Deactivated {deactivated} legacy ownership types")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nOwnership types: {OwnershipType.objects.filter(is_active=True).count()} active "
                f"(new: {created_count}, updated: {updated_count})"
            )
        )
