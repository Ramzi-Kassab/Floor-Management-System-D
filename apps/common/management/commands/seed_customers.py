"""
ARDT FMS - Seed Customers Command
Creates real customers and competitors from QAS-105

Usage: python manage.py seed_customers
"""

from django.core.management.base import BaseCommand
from apps.sales.models import Customer


class Command(BaseCommand):
    help = "Seed real ARDT customers and competitors"

    # Real Customers & Competitors from MASTER_PLAN v3.0
    # Types: Primary Client, Regional Client, Service Competitor, Service Competitor - Client,
    #        Service Company - Client, Equipment Supplier - Competitor
    CUSTOMERS = [
        # Primary Client - Saudi Aramco
        {
            "code": "ARAMCO",
            "name": "Saudi Aramco",
            "name_ar": "أرامكو السعودية",
            "customer_type": "OPERATOR",
            "company_type": "Primary Client",
            "address": "Dhahran 31311, P.O. Box 5000",
            "city": "Dhahran",
            "country": "Saudi Arabia",
            "phone": "+966-13-872-0000",
            "email": "contact@aramco.com",
            "website": "https://www.aramco.com",
            "is_aramco": True,
            "is_active": True,
            "payment_terms": "Net 60",
        },
        # Competitors & Service Companies
        {
            "code": "SCHLUM",
            "name": "Schlumberger",
            "name_ar": "شلمبرجير",
            "customer_type": "CONTRACTOR",
            "company_type": "Service Competitor",
            "city": "Al Khobar",
            "country": "Saudi Arabia",
            "is_aramco": False,
            "is_active": True,
        },
        {
            "code": "HALIBTN",
            "name": "Halliburton",
            "name_ar": "هاليبرتون",
            "customer_type": "CONTRACTOR",
            "company_type": "Service Competitor - Client",
            "city": "Al Khobar",
            "country": "Saudi Arabia",
            "is_aramco": False,
            "is_active": True,
        },
        {
            "code": "BAKER",
            "name": "Baker Hughes",
            "name_ar": "بيكر هيوز",
            "customer_type": "CONTRACTOR",
            "company_type": "Service Competitor",
            "city": "Al Khobar",
            "country": "Saudi Arabia",
            "is_aramco": False,
            "is_active": True,
        },
        {
            "code": "WEATHER",
            "name": "Weatherford",
            "name_ar": "ويذرفورد",
            "customer_type": "CONTRACTOR",
            "company_type": "Service Competitor - Client",
            "city": "Al Khobar",
            "country": "Saudi Arabia",
            "is_aramco": False,
            "is_active": True,
        },
        {
            "code": "NOV",
            "name": "NOV Inc.",
            "name_ar": "إن أو في",
            "customer_type": "DISTRIBUTOR",
            "company_type": "Equipment Supplier - Competitor",
            "city": "Al Khobar",
            "country": "Saudi Arabia",
            "is_aramco": False,
            "is_active": True,
        },
        {
            "code": "NATPET",
            "name": "National Petroleum",
            "name_ar": "البترول الوطنية",
            "customer_type": "OPERATOR",
            "company_type": "Regional Client",
            "city": "Dammam",
            "country": "Saudi Arabia",
            "is_aramco": False,
            "is_active": True,
        },
        {
            "code": "SPERRY",
            "name": "Sperry Drilling Services",
            "name_ar": "سبيري لخدمات الحفر",
            "customer_type": "CONTRACTOR",
            "company_type": "Service Company - Client",
            "address": "Saihat, Eastern Province",
            "city": "Al Khobar",
            "country": "Saudi Arabia",
            "is_aramco": False,
            "is_active": True,
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update of existing customers",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding ARDT Customers & Competitors (8 Total) ===\n"))

        force = options.get("force", False)
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for cust_data in self.CUSTOMERS:
            code = cust_data["code"]
            # Extract company_type for display (not a model field)
            company_type = cust_data.pop("company_type", "Other")

            try:
                customer, created = Customer.objects.get_or_create(
                    code=code,
                    defaults=cust_data,
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Created: {code} - {customer.name} [{company_type}]")
                    )
                elif force:
                    for key, value in cust_data.items():
                        setattr(customer, key, value)
                    customer.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  ↻ Updated: {code} - {customer.name}")
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.NOTICE(f"  - Skipped (exists): {code}")
                    )

                # Restore company_type for reference
                cust_data["company_type"] = company_type

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error creating {code}: {str(e)}")
                )
                cust_data["company_type"] = company_type

        # Summary
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.WARNING(f"  Updated: {updated_count}"))
        self.stdout.write(f"  Skipped: {skipped_count}")
        self.stdout.write("-" * 60)

        # Customer list by type
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Companies by Type ===\n"))

        type_groups = {}
        for cust in self.CUSTOMERS:
            ctype = cust.get("company_type", "Other")
            if ctype not in type_groups:
                type_groups[ctype] = []
            type_groups[ctype].append(cust)

        for ctype, companies in sorted(type_groups.items()):
            self.stdout.write(f"\n  {ctype}:")
            for c in companies:
                self.stdout.write(f"    - {c['code']}: {c['name']}")

        self.stdout.write(f"\n  Total: {len(self.CUSTOMERS)} companies")
        self.stdout.write(self.style.SUCCESS("\n✓ Customer seeding complete!\n"))
