"""
Clear all seeded data from the database.

This command removes all seeded records to allow re-seeding with correct data.
Keeps superuser accounts intact.
"""

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Clear all seeded data (users, departments, positions, customers, rigs, wells, roles, permissions)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirm deletion without prompting",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  WARNING: This will DELETE all seeded data!\n"
                    "   - Users (except superusers)\n"
                    "   - Departments\n"
                    "   - Positions\n"
                    "   - Customers\n"
                    "   - Rigs\n"
                    "   - Wells\n"
                    "   - Roles & Permissions\n"
                )
            )
            confirm = input("Type 'yes' to confirm: ")
            if confirm.lower() != "yes":
                self.stdout.write(self.style.ERROR("Aborted."))
                return

        self.stdout.write("\n🗑️  Clearing seeded data...\n")

        with transaction.atomic():
            # Import models
            from apps.accounts.models import User, Role, Permission, UserRole, RolePermission
            from apps.organization.models import Department, Position
            from apps.sales.models import Customer, Rig, Well

            # Count before deletion
            counts = {
                "users": User.objects.filter(is_superuser=False).count(),
                "departments": Department.objects.count(),
                "positions": Position.objects.count(),
                "customers": Customer.objects.count(),
                "rigs": Rig.objects.count(),
                "wells": Well.objects.count(),
                "roles": Role.objects.count(),
                "permissions": Permission.objects.count(),
                "user_roles": UserRole.objects.count(),
                "role_permissions": RolePermission.objects.count(),
            }

            # Delete in correct order (respect foreign keys)

            # 1. Delete UserRoles first (depends on User and Role)
            deleted = UserRole.objects.all().delete()[0]
            self.stdout.write(f"   ✓ Deleted {deleted} user-role assignments")

            # 2. Delete RolePermissions (depends on Role and Permission)
            deleted = RolePermission.objects.all().delete()[0]
            self.stdout.write(f"   ✓ Deleted {deleted} role-permission assignments")

            # 3. Delete Wells (depends on Rig and Customer)
            deleted = Well.objects.all().delete()[0]
            self.stdout.write(f"   ✓ Deleted {deleted} wells")

            # 4. Delete Rigs (depends on Customer)
            deleted = Rig.objects.all().delete()[0]
            self.stdout.write(f"   ✓ Deleted {deleted} rigs")

            # 5. Delete Customers
            deleted = Customer.objects.all().delete()[0]
            self.stdout.write(f"   ✓ Deleted {deleted} customers")

            # 6. Delete Users (except superusers)
            deleted = User.objects.filter(is_superuser=False).delete()[0]
            self.stdout.write(f"   ✓ Deleted {deleted} users (kept superusers)")

            # 7. Delete Positions (depends on Department)
            deleted = Position.objects.all().delete()[0]
            self.stdout.write(f"   ✓ Deleted {deleted} positions")

            # 8. Delete Departments
            deleted = Department.objects.all().delete()[0]
            self.stdout.write(f"   ✓ Deleted {deleted} departments")

            # 9. Delete Roles
            deleted = Role.objects.all().delete()[0]
            self.stdout.write(f"   ✓ Deleted {deleted} roles")

            # 10. Delete Permissions
            deleted = Permission.objects.all().delete()[0]
            self.stdout.write(f"   ✓ Deleted {deleted} permissions")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Successfully cleared all seeded data!\n"
                f"\n   Summary of deleted records:\n"
                f"   - Users: {counts['users']}\n"
                f"   - Departments: {counts['departments']}\n"
                f"   - Positions: {counts['positions']}\n"
                f"   - Customers: {counts['customers']}\n"
                f"   - Rigs: {counts['rigs']}\n"
                f"   - Wells: {counts['wells']}\n"
                f"   - Roles: {counts['roles']}\n"
                f"   - Permissions: {counts['permissions']}\n"
                f"\n   Run 'python manage.py seed_all' to re-seed with correct data.\n"
            )
        )
