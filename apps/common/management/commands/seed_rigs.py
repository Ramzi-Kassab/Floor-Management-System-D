"""
ARDT FMS - Seed Rigs Command
Creates real drilling rigs from Morning Report 01-02-2025

Usage: python manage.py seed_rigs
"""

from django.core.management.base import BaseCommand
from apps.sales.models import Rig, Customer


class Command(BaseCommand):
    help = "Seed real drilling rigs from Morning Report data"

    # Real Rigs from MASTER_PLAN.md (Morning Report 01-02-2025)
    RIGS = [
        {
            "code": "088TE",
            "name": "Rig 088TE",
            "customer_code": "ARAMCO",
            "rig_type": "Land Rig",
            "location": "Eastern Province, Saudi Arabia",
            "is_active": True,
        },
        {
            "code": "GW-88",
            "name": "Rig GW-88",
            "customer_code": "ARAMCO",
            "rig_type": "Land Rig",
            "location": "Eastern Province, Saudi Arabia",
            "is_active": True,
        },
        {
            "code": "PA-785",
            "name": "Rig PA-785",
            "customer_code": "ARAMCO",
            "rig_type": "Land Rig",
            "location": "Eastern Province, Saudi Arabia",
            "is_active": True,
        },
        {
            "code": "AD-72",
            "name": "Rig AD-72",
            "customer_code": "ARAMCO",
            "rig_type": "Land Rig",
            "location": "Eastern Province, Saudi Arabia",
            "is_active": True,
        },
        {
            "code": "AD-74",
            "name": "Rig AD-74",
            "customer_code": "ARAMCO",
            "rig_type": "Land Rig",
            "location": "Eastern Province, Saudi Arabia",
            "is_active": True,
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update of existing rigs",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding ARDT Rigs ===\n"))

        force = options.get("force", False)
        created_count = 0
        updated_count = 0
        skipped_count = 0

        # Cache customers
        customers = {c.code: c for c in Customer.objects.all()}

        for rig_data in self.RIGS:
            code = rig_data["code"]
            customer_code = rig_data.pop("customer_code")

            # Get customer
            customer = customers.get(customer_code)
            if customer:
                rig_data["customer"] = customer
            else:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ Customer {customer_code} not found for rig {code}")
                )

            try:
                rig, created = Rig.objects.get_or_create(
                    code=code,
                    defaults=rig_data,
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Created: {code} - {rig.name} ({customer_code})")
                    )
                elif force:
                    for key, value in rig_data.items():
                        setattr(rig, key, value)
                    rig.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  ↻ Updated: {code} - {rig.name}")
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.NOTICE(f"  - Skipped (exists): {code}")
                    )

                # Restore customer_code for next iteration
                rig_data["customer_code"] = customer_code
                if "customer" in rig_data:
                    del rig_data["customer"]

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error creating {code}: {str(e)}")
                )
                rig_data["customer_code"] = customer_code
                if "customer" in rig_data:
                    del rig_data["customer"]

        # Summary
        self.stdout.write("\n" + "-" * 50)
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.WARNING(f"  Updated: {updated_count}"))
        self.stdout.write(f"  Skipped: {skipped_count}")
        self.stdout.write("-" * 50)

        # Rig list
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Rig List ===\n"))
        self.stdout.write("  Code     | Name          | Type      | Customer")
        self.stdout.write("  " + "-" * 55)
        for rig in self.RIGS:
            self.stdout.write(
                f"  {rig['code']:<8} | {rig['name']:<13} | {rig['rig_type']:<9} | {rig['customer_code']}"
            )

        self.stdout.write(self.style.SUCCESS("\n✓ Rig seeding complete!\n"))
