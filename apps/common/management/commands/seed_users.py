"""
ARDT FMS - Seed Users Command
Creates real ARDT personnel from Morning Report 01-02-2025

Usage: python manage.py seed_users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Seed real ARDT users from Morning Report data"

    # Real ARDT Personnel from MASTER_PLAN.md
    USERS = [
        {
            "username": "admin",
            "password": "admin123",
            "first_name": "System",
            "last_name": "Administrator",
            "email": "admin@ardt.com",
            "employee_id": "ARDT-001",
            "is_staff": True,
            "is_superuser": True,
            "phone": "+966-13-XXX-XXXX",
            "mobile": "+966-5X-XXX-XXXX",
            "language": "en",
            "timezone": "Asia/Riyadh",
        },
        {
            "username": "t.eldeeb",
            "password": "ardt2025",
            "first_name": "Tarek",
            "last_name": "Eldeeb",
            "email": "t.eldeeb@ardt.com",
            "employee_id": "ARDT-002",
            "is_staff": True,
            "is_superuser": False,
            "phone": "+966-13-XXX-XXXX",
            "mobile": "+966-5X-XXX-XXXX",
            "language": "en",
            "timezone": "Asia/Riyadh",
        },
        {
            "username": "r.ibrahim",
            "password": "ardt2025",
            "first_name": "Reda",
            "last_name": "Ibrahim",
            "email": "r.ibrahim@ardt.com",
            "employee_id": "ARDT-003",
            "is_staff": False,
            "is_superuser": False,
            "phone": "+966-13-XXX-XXXX",
            "mobile": "+966-5X-XXX-XXXX",
            "language": "ar",
            "timezone": "Asia/Riyadh",
        },
        {
            "username": "a.aljafary",
            "password": "ardt2025",
            "first_name": "Abdulrahman",
            "last_name": "Aljafary",
            "email": "a.aljafary@ardt.com",
            "employee_id": "ARDT-004",
            "is_staff": False,
            "is_superuser": False,
            "phone": "+966-13-XXX-XXXX",
            "mobile": "+966-5X-XXX-XXXX",
            "language": "ar",
            "timezone": "Asia/Riyadh",
        },
        {
            "username": "b.jaroudi",
            "password": "ardt2025",
            "first_name": "Bassam",
            "last_name": "Jaroudi",
            "email": "b.jaroudi@ardt.com",
            "employee_id": "ARDT-005",
            "is_staff": False,
            "is_superuser": False,
            "phone": "+966-13-XXX-XXXX",
            "mobile": "+966-5X-XXX-XXXX",
            "language": "en",
            "timezone": "Asia/Riyadh",
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force recreation of existing users (updates password)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding ARDT Users ===\n"))

        force = options.get("force", False)
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for user_data in self.USERS:
            username = user_data["username"]
            password = user_data.pop("password")

            try:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults=user_data,
                )

                if created:
                    user.set_password(password)
                    user.save()
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Created user: {username} ({user.get_full_name()})")
                    )
                elif force:
                    # Update existing user
                    for key, value in user_data.items():
                        setattr(user, key, value)
                    user.set_password(password)
                    user.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  ↻ Updated user: {username}")
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.NOTICE(f"  - Skipped (exists): {username}")
                    )

                # Add password back for next iteration reference
                user_data["password"] = password

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error creating {username}: {str(e)}")
                )

        # Summary
        self.stdout.write("\n" + "-" * 40)
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.WARNING(f"  Updated: {updated_count}"))
        self.stdout.write(f"  Skipped: {skipped_count}")
        self.stdout.write("-" * 40)

        # Login info
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Login Credentials ===\n"))
        self.stdout.write("  Admin User:")
        self.stdout.write("    Username: admin")
        self.stdout.write("    Password: admin123")
        self.stdout.write("\n  Regular Users (password: ardt2025):")
        self.stdout.write("    - t.eldeeb (Tarek Eldeeb - Manager)")
        self.stdout.write("    - r.ibrahim (Reda Ibrahim - Day Foreman)")
        self.stdout.write("    - a.aljafary (Abdulrahman Aljafary - Night Foreman)")
        self.stdout.write("    - b.jaroudi (Bassam Jaroudi - Engineer)")
        self.stdout.write("")

        self.stdout.write(self.style.SUCCESS("\n✓ User seeding complete!\n"))
