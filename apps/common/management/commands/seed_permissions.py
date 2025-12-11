"""
ARDT FMS - Seed Permissions Command
Creates roles and permissions for role-based access control

Usage: python manage.py seed_permissions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import Role, Permission, RolePermission, UserRole
from apps.organization.models import Department, Position

User = get_user_model()


class Command(BaseCommand):
    help = "Seed roles and permissions for ARDT FMS"

    # Roles with hierarchy levels (higher = more authority)
    # Level: 1=Staff, 2=Supervisor, 3=Manager, 4=Executive
    ROLES = [
        {
            "code": "EXECUTIVE",
            "name": "Executive",
            "description": "Full system access - GM and directors",
            "level": 4,
            "is_system": True,
        },
        {
            "code": "MANAGER",
            "name": "Manager",
            "description": "Department access with approvals",
            "level": 3,
            "is_system": True,
        },
        {
            "code": "SUPERVISOR",
            "name": "Supervisor",
            "description": "Create/edit within scope",
            "level": 2,
            "is_system": True,
        },
        {
            "code": "STAFF",
            "name": "Staff",
            "description": "View and limited create",
            "level": 1,
            "is_system": True,
        },
    ]

    # Permissions by module
    PERMISSIONS = [
        # Dashboard
        {"code": "dashboard.view", "name": "View Dashboard", "module": "dashboard"},
        # Users
        {"code": "users.view", "name": "View Users", "module": "users"},
        {"code": "users.create", "name": "Create Users", "module": "users"},
        {"code": "users.edit", "name": "Edit Users", "module": "users"},
        {"code": "users.delete", "name": "Delete Users", "module": "users"},
        # Departments
        {"code": "departments.view", "name": "View Departments", "module": "organization"},
        {"code": "departments.manage", "name": "Manage Departments", "module": "organization"},
        # Work Orders
        {"code": "workorders.view", "name": "View Work Orders", "module": "workorders"},
        {"code": "workorders.create", "name": "Create Work Orders", "module": "workorders"},
        {"code": "workorders.edit", "name": "Edit Work Orders", "module": "workorders"},
        {"code": "workorders.approve", "name": "Approve Work Orders", "module": "workorders"},
        {"code": "workorders.delete", "name": "Delete Work Orders", "module": "workorders"},
        # Quality
        {"code": "quality.view", "name": "View Quality Records", "module": "quality"},
        {"code": "quality.create", "name": "Create Quality Records", "module": "quality"},
        {"code": "quality.approve", "name": "Approve Quality Records", "module": "quality"},
        # Inventory
        {"code": "inventory.view", "name": "View Inventory", "module": "inventory"},
        {"code": "inventory.manage", "name": "Manage Inventory", "module": "inventory"},
        {"code": "inventory.adjust", "name": "Adjust Inventory", "module": "inventory"},
        # Sales
        {"code": "sales.view", "name": "View Sales Data", "module": "sales"},
        {"code": "sales.create", "name": "Create Sales Orders", "module": "sales"},
        {"code": "sales.manage", "name": "Manage Sales", "module": "sales"},
        # Field Operations
        {"code": "field.view", "name": "View Field Data", "module": "field"},
        {"code": "field.create", "name": "Create Field Records", "module": "field"},
        {"code": "field.manage", "name": "Manage Field Operations", "module": "field"},
        # Reports
        {"code": "reports.view", "name": "View Reports", "module": "reports"},
        {"code": "reports.export", "name": "Export Reports", "module": "reports"},
        # Admin
        {"code": "admin.access", "name": "Access Admin Panel", "module": "admin"},
        {"code": "admin.full", "name": "Full Admin Access", "module": "admin"},
    ]

    # Role-Permission mappings
    ROLE_PERMISSIONS = {
        "EXECUTIVE": [
            # Full access to everything
            "dashboard.view", "users.view", "users.create", "users.edit", "users.delete",
            "departments.view", "departments.manage",
            "workorders.view", "workorders.create", "workorders.edit", "workorders.approve", "workorders.delete",
            "quality.view", "quality.create", "quality.approve",
            "inventory.view", "inventory.manage", "inventory.adjust",
            "sales.view", "sales.create", "sales.manage",
            "field.view", "field.create", "field.manage",
            "reports.view", "reports.export",
            "admin.access", "admin.full",
        ],
        "MANAGER": [
            # Department access + approvals (no admin)
            "dashboard.view", "users.view",
            "departments.view",
            "workorders.view", "workorders.create", "workorders.edit", "workorders.approve",
            "quality.view", "quality.create", "quality.approve",
            "inventory.view", "inventory.manage",
            "sales.view", "sales.create", "sales.manage",
            "field.view", "field.create", "field.manage",
            "reports.view", "reports.export",
        ],
        "SUPERVISOR": [
            # Create/edit within scope
            "dashboard.view",
            "departments.view",
            "workorders.view", "workorders.create", "workorders.edit",
            "quality.view", "quality.create",
            "inventory.view",
            "sales.view", "sales.create",
            "field.view", "field.create",
            "reports.view",
        ],
        "STAFF": [
            # View + limited create
            "dashboard.view",
            "departments.view",
            "workorders.view", "workorders.create",
            "quality.view",
            "inventory.view",
            "sales.view",
            "field.view", "field.create",
            "reports.view",
        ],
    }

    # User-Role mappings based on position level
    USER_ROLE_MAPPING = {
        "admin": "EXECUTIVE",
        "t.eldeeb": "MANAGER",      # Field Manager
        "r.ibrahim": "SUPERVISOR",   # Day Foreman
        "a.aljafary": "SUPERVISOR",  # Night Foreman
        "b.jaroudi": "SUPERVISOR",   # Engineer
    }

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding Permissions & Roles ===\n"))

        # 1. Create Permissions
        self.stdout.write("Creating permissions...")
        perm_count = 0
        for perm_data in self.PERMISSIONS:
            perm, created = Permission.objects.get_or_create(
                code=perm_data["code"],
                defaults=perm_data,
            )
            if created:
                perm_count += 1
        self.stdout.write(self.style.SUCCESS(f"  ✓ Created {perm_count} permissions"))

        # 2. Create Roles
        self.stdout.write("\nCreating roles...")
        role_count = 0
        roles = {}
        for role_data in self.ROLES:
            role, created = Role.objects.get_or_create(
                code=role_data["code"],
                defaults=role_data,
            )
            roles[role.code] = role
            if created:
                role_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Created role: {role.name} (Level {role.level})"))
            else:
                self.stdout.write(f"  - Exists: {role.name}")
        self.stdout.write(self.style.SUCCESS(f"  Total: {len(roles)} roles"))

        # 3. Assign Permissions to Roles
        self.stdout.write("\nAssigning permissions to roles...")
        for role_code, perm_codes in self.ROLE_PERMISSIONS.items():
            role = roles.get(role_code)
            if not role:
                continue

            assigned = 0
            for perm_code in perm_codes:
                try:
                    perm = Permission.objects.get(code=perm_code)
                    rp, created = RolePermission.objects.get_or_create(
                        role=role,
                        permission=perm,
                    )
                    if created:
                        assigned += 1
                except Permission.DoesNotExist:
                    pass

            self.stdout.write(f"  {role_code}: {assigned} new permissions assigned")

        # 4. Assign Roles to Users
        self.stdout.write("\nAssigning roles to users...")
        for username, role_code in self.USER_ROLE_MAPPING.items():
            try:
                user = User.objects.get(username=username)
                role = roles.get(role_code)
                if role:
                    ur, created = UserRole.objects.get_or_create(
                        user=user,
                        role=role,
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"  ✓ {username} → {role_code}"))
                    else:
                        self.stdout.write(f"  - {username} already has {role_code}")
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  ⚠ User {username} not found"))

        # 5. Update user departments and positions
        self.stdout.write("\nUpdating user departments and positions...")
        self._assign_user_departments()

        # Summary
        self.stdout.write("\n" + "-" * 50)
        self.stdout.write(self.style.MIGRATE_HEADING("=== Permission Summary ==="))
        self.stdout.write(f"  Permissions: {Permission.objects.count()}")
        self.stdout.write(f"  Roles: {Role.objects.count()}")
        self.stdout.write(f"  Role-Permission links: {RolePermission.objects.count()}")
        self.stdout.write(f"  User-Role links: {UserRole.objects.count()}")
        self.stdout.write("-" * 50)

        self.stdout.write(self.style.SUCCESS("\n✓ Permissions seeding complete!\n"))

    def _assign_user_departments(self):
        """Assign departments and positions to seeded users."""
        assignments = [
            {"username": "admin", "dept": "EXEC", "position": "GM"},
            {"username": "t.eldeeb", "dept": "FIELD", "position": "FIELD-MGR"},
            {"username": "r.ibrahim", "dept": "FIELD", "position": "FIELD-FOR"},
            {"username": "a.aljafary", "dept": "FIELD", "position": "FIELD-FOR"},
            {"username": "b.jaroudi", "dept": "FIELD", "position": "FIELD-ENG"},
        ]

        for assignment in assignments:
            try:
                user = User.objects.get(username=assignment["username"])
                dept = Department.objects.filter(code=assignment["dept"]).first()
                position = Position.objects.filter(code=assignment["position"]).first()

                updated = False
                if dept and user.department != dept:
                    user.department = dept
                    updated = True
                if position and user.position != position:
                    user.position = position
                    updated = True

                if updated:
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ {assignment['username']} → {assignment['dept']}/{assignment['position']}")
                    )
            except User.DoesNotExist:
                pass
