"""
ARDT FMS - Seed All Command
Runs all seed commands in the correct order

Usage: python manage.py seed_all
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Run all seed commands in the correct order"

    # Commands to run in order
    SEED_COMMANDS = [
        ("seed_departments", "Departments (10)"),
        ("seed_positions", "Positions (54)"),
        ("seed_users", "Users (27)"),
        ("seed_permissions", "Permissions & Roles"),
        ("seed_customers", "Customers (8)"),
        ("seed_accounts", "Accounts (4 Aramco Divisions)"),
        ("seed_rigs", "Rigs (5)"),
        ("seed_wells", "Wells (21)"),
        ("seed_hdbs_types", "HDBS Types (8)"),
        ("seed_smi_types", "SMI Types (23)"),
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update of existing records",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n" + "=" * 60))
        self.stdout.write(self.style.MIGRATE_HEADING("  ARDT FMS - Seeding All Data (QAS-105)"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60 + "\n"))

        force = options.get("force", False)
        success_count = 0
        error_count = 0

        for cmd_name, display_name in self.SEED_COMMANDS:
            self.stdout.write(f"\n[{success_count + error_count + 1}/{len(self.SEED_COMMANDS)}] Seeding {display_name}...")
            try:
                if force:
                    call_command(cmd_name, "--force")
                else:
                    call_command(cmd_name)
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error: {str(e)}"))
                error_count += 1

        # Final Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.MIGRATE_HEADING("  SEED SUMMARY"))
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS(f"  Successful: {success_count}/{len(self.SEED_COMMANDS)}"))
        if error_count:
            self.stdout.write(self.style.ERROR(f"  Failed: {error_count}/{len(self.SEED_COMMANDS)}"))
        self.stdout.write("=" * 60)

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Login Credentials ===\n"))
        self.stdout.write("  Password for ALL users: Ardt@2025")
        self.stdout.write("\n  Sample Logins:")
        self.stdout.write("    - r.kassab (Ramzi Kassab - Repair Supervisor)")
        self.stdout.write("    - g.escobar (Gustavo Escobar - General Manager)")
        self.stdout.write("    - m.irshad (Mohammad Irshad - IT & ERP Manager)")
        self.stdout.write("    - a.chisti (Ahmed Faizan Chisti - Quality Manager)")

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Data Summary ===\n"))
        self.stdout.write("  - 10 Departments")
        self.stdout.write("  - 54 Positions")
        self.stdout.write("  - 27 Employees")
        self.stdout.write("  - 8 Companies")
        self.stdout.write("  - 4 Accounts (Aramco Divisions)")
        self.stdout.write("  - 5 Rigs")
        self.stdout.write("  - 21 Wells")
        self.stdout.write("  - 8 HDBS Types")
        self.stdout.write("  - 23 SMI Types")

        self.stdout.write(self.style.SUCCESS("\n✓ All seeding complete! System is ready.\n"))
