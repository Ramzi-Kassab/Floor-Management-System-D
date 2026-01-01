"""
ARDT FMS - Seed Accounts Command
Creates Aramco division accounts (Oil, Gas, LSTK, Offshore)

Usage: python manage.py seed_accounts
"""

from django.core.management.base import BaseCommand
from apps.sales.models import Account


class Command(BaseCommand):
    help = "Seed Aramco division accounts"

    ACCOUNTS = [
        {
            "code": "OIL",
            "name": "Oil Division",
            "name_ar": "قسم النفط",
            "description": "Saudi Aramco Oil Division - primary oil drilling operations",
        },
        {
            "code": "GAS",
            "name": "Gas Division",
            "name_ar": "قسم الغاز",
            "description": "Saudi Aramco Gas Division - natural gas exploration and production",
        },
        {
            "code": "LSTK",
            "name": "LSTK Division",
            "name_ar": "قسم المقاولات",
            "description": "Lump Sum Turnkey Division - project-based drilling contracts",
        },
        {
            "code": "OFFSHORE",
            "name": "Offshore Division",
            "name_ar": "القسم البحري",
            "description": "Saudi Aramco Offshore Division - offshore drilling operations",
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update of existing accounts",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding Aramco Division Accounts ===\n"))

        force = options.get("force", False)
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for acct_data in self.ACCOUNTS:
            code = acct_data["code"]

            try:
                account, created = Account.objects.get_or_create(
                    code=code,
                    defaults=acct_data,
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  + Created: {code} - {account.name}")
                    )
                elif force:
                    for key, value in acct_data.items():
                        setattr(account, key, value)
                    account.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  ~ Updated: {code} - {account.name}")
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.NOTICE(f"  - Skipped (exists): {code}")
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  x Error creating {code}: {str(e)}")
                )

        # Summary
        self.stdout.write("\n" + "-" * 50)
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.WARNING(f"  Updated: {updated_count}"))
        self.stdout.write(f"  Skipped: {skipped_count}")
        self.stdout.write("-" * 50)

        self.stdout.write(self.style.SUCCESS("\nAccount seeding complete!\n"))
