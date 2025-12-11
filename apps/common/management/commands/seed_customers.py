"""
ARDT FMS - Seed Customers Command
Creates real customers from Morning Report 01-02-2025

Usage: python manage.py seed_customers
"""

from django.core.management.base import BaseCommand
from apps.sales.models import Customer


class Command(BaseCommand):
    help = "Seed real ARDT customers from Morning Report data"

    # Real Customers from MASTER_PLAN.md
    CUSTOMERS = [
        # Primary Customer - Saudi Aramco
        {
            "code": "ARAMCO",
            "name": "Saudi Arabian Oil Company (Saudi Aramco)",
            "name_ar": "شركة الزيت العربية السعودية (أرامكو السعودية)",
            "customer_type": "OPERATOR",
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
        # Service Companies (Contractors)
        {
            "code": "BHI",
            "name": "Baker Hughes",
            "name_ar": "بيكر هيوز",
            "customer_type": "CONTRACTOR",
            "city": "Al Khobar",
            "country": "Saudi Arabia",
            "is_aramco": False,
            "is_active": True,
        },
        {
            "code": "SLB",
            "name": "Schlumberger",
            "name_ar": "شلمبرجير",
            "customer_type": "CONTRACTOR",
            "city": "Al Khobar",
            "country": "Saudi Arabia",
            "is_aramco": False,
            "is_active": True,
        },
        {
            "code": "HAL",
            "name": "Halliburton",
            "name_ar": "هاليبرتون",
            "customer_type": "CONTRACTOR",
            "city": "Al Khobar",
            "country": "Saudi Arabia",
            "is_aramco": False,
            "is_active": True,
        },
        {
            "code": "NOV",
            "name": "National Oilwell Varco",
            "name_ar": "ناشيونال أويل ويل فاركو",
            "customer_type": "CONTRACTOR",
            "city": "Al Khobar",
            "country": "Saudi Arabia",
            "is_aramco": False,
            "is_active": True,
        },
        {
            "code": "SWACO",
            "name": "M-I SWACO",
            "name_ar": "إم آي سواكو",
            "customer_type": "CONTRACTOR",
            "city": "Al Khobar",
            "country": "Saudi Arabia",
            "is_aramco": False,
            "is_active": True,
        },
        {
            "code": "RAWABI",
            "name": "Rawabi Holding",
            "name_ar": "شركة روابي القابضة",
            "customer_type": "CONTRACTOR",
            "city": "Dammam",
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
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding ARDT Customers ===\n"))

        force = options.get("force", False)
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for cust_data in self.CUSTOMERS:
            code = cust_data["code"]

            try:
                customer, created = Customer.objects.get_or_create(
                    code=code,
                    defaults=cust_data,
                )

                if created:
                    created_count += 1
                    aramco_flag = " [ARAMCO]" if customer.is_aramco else ""
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Created: {code} - {customer.name}{aramco_flag}")
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

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error creating {code}: {str(e)}")
                )

        # Summary
        self.stdout.write("\n" + "-" * 50)
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.WARNING(f"  Updated: {updated_count}"))
        self.stdout.write(f"  Skipped: {skipped_count}")
        self.stdout.write("-" * 50)

        # Customer list
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Customer List ===\n"))
        self.stdout.write("  Code    | Type       | Name")
        self.stdout.write("  " + "-" * 60)
        for cust in self.CUSTOMERS:
            ctype = cust.get("customer_type", "OTHER")[:10]
            aramco = " *" if cust.get("is_aramco") else ""
            self.stdout.write(
                f"  {cust['code']:<7} | {ctype:<10} | {cust['name']}{aramco}"
            )
        self.stdout.write("\n  * = ARAMCO / ARAMCO Contractor")

        self.stdout.write(self.style.SUCCESS("\n✓ Customer seeding complete!\n"))
