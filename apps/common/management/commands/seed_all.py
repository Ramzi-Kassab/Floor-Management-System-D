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
        ("seed_departments", "Departments"),
        ("seed_positions", "Positions"),
        ("seed_users", "Users"),
        ("seed_permissions", "Permissions & Roles"),
        ("seed_customers", "Customers"),
        ("seed_rigs", "Rigs"),
        ("seed_wells", "Wells"),
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update of existing records",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n" + "=" * 60))
        self.stdout.write(self.style.MIGRATE_HEADING("  ARDT FMS - Seeding All Data"))
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
        self.stdout.write("  Admin User:")
        self.stdout.write("    Username: admin")
        self.stdout.write("    Password: admin123")
        self.stdout.write("\n  Regular Users (password: ardt2025):")
        self.stdout.write("    - t.eldeeb (Field Manager)")
        self.stdout.write("    - r.ibrahim (Day Foreman)")
        self.stdout.write("    - a.aljafary (Night Foreman)")
        self.stdout.write("    - b.jaroudi (Field Engineer)")

        self.stdout.write(self.style.SUCCESS("\n✓ All seeding complete! System is ready.\n"))
