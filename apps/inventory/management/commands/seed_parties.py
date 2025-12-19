"""
Seed command for Party - Unified party master data.

Usage:
    python manage.py seed_parties

This seeds the ARDT internal party and creates Party records
for existing Customers, Vendors, and Rigs.
"""

from django.core.management.base import BaseCommand
from apps.inventory.models import Party


class Command(BaseCommand):
    help = "Seed parties (ARDT internal + sync from existing entities)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Parties...\n")

        created_count = 0

        # 1. Create ARDT internal party
        ardt_party, created = Party.objects.get_or_create(
            code="ARDT",
            defaults={
                "name": "ARDT (Internal)",
                "party_type": Party.PartyType.INTERNAL,
                "notes": "Main ARDT internal party for owned inventory",
                "is_active": True,
            }
        )
        if created:
            self.stdout.write(f"  Created: ARDT (Internal)")
            created_count += 1
        else:
            self.stdout.write(f"  Exists: ARDT (Internal)")

        # 2. Create Party records for existing Customers
        try:
            from apps.sales.models import Customer
            customers = Customer.objects.filter(is_active=True)
            for customer in customers:
                party, created = Party.objects.get_or_create(
                    customer=customer,
                    defaults={
                        "code": f"C-{customer.code}",
                        "name": customer.name,
                        "party_type": Party.PartyType.CUSTOMER,
                        "is_active": True,
                    }
                )
                if created:
                    self.stdout.write(f"  Created: {party.code} (Customer)")
                    created_count += 1
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Could not sync Customers: {e}"))

        # 3. Create Party records for existing Vendors/Suppliers
        try:
            from apps.supplychain.models import Supplier
            suppliers = Supplier.objects.filter(is_active=True)
            for supplier in suppliers:
                party, created = Party.objects.get_or_create(
                    vendor=supplier,
                    defaults={
                        "code": f"V-{supplier.code}",
                        "name": supplier.name,
                        "party_type": Party.PartyType.VENDOR,
                        "is_active": True,
                    }
                )
                if created:
                    self.stdout.write(f"  Created: {party.code} (Vendor)")
                    created_count += 1
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Could not sync Vendors: {e}"))

        # 4. Create Party records for existing Rigs
        try:
            from apps.sales.models import Rig
            rigs = Rig.objects.filter(is_active=True)
            for rig in rigs:
                party, created = Party.objects.get_or_create(
                    rig=rig,
                    defaults={
                        "code": f"R-{rig.code}",
                        "name": rig.name,
                        "party_type": Party.PartyType.RIG,
                        "is_active": True,
                    }
                )
                if created:
                    self.stdout.write(f"  Created: {party.code} (Rig)")
                    created_count += 1
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Could not sync Rigs: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTotal parties: {Party.objects.count()} (new: {created_count})"
            )
        )
