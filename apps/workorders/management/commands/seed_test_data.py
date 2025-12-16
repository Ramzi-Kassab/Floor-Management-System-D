"""
ARDT FMS - Seed Test Data Command
Version: 5.4 - Sprint 1

Creates test data for development and testing purposes.
Usage: python manage.py seed_test_data [--clear]
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with test data for development"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing test data before seeding",
        )
        parser.add_argument(
            "--minimal",
            action="store_true",
            help="Create minimal test data only",
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting test data seeding...")

        if options["clear"]:
            self.clear_test_data()

        # Create test users
        self.create_test_users()

        # Create drill bits
        self.create_drill_bits()

        # Create work orders
        self.create_work_orders(minimal=options["minimal"])

        self.stdout.write(self.style.SUCCESS("Test data seeded successfully!"))

    def clear_test_data(self):
        """Clear existing test data."""
        from apps.workorders.models import DrillBit, WorkOrder

        self.stdout.write("Clearing existing test data...")

        # Delete test work orders
        WorkOrder.objects.filter(wo_number__startswith="WO-TEST").delete()

        # Delete test drill bits
        DrillBit.objects.filter(serial_number__startswith="TEST-").delete()

        # Delete test users (except superusers)
        User.objects.filter(username__startswith="test_", is_superuser=False).delete()

        self.stdout.write(self.style.WARNING("Test data cleared."))

    def create_test_users(self):
        """Create test users with different roles."""
        self.stdout.write("Creating test users...")

        test_users = [
            {
                "username": "test_admin",
                "email": "admin@test.ardt.com",
                "first_name": "Admin",
                "last_name": "User",
                "role": "ADMIN",
            },
            {
                "username": "test_manager",
                "email": "manager@test.ardt.com",
                "first_name": "Manager",
                "last_name": "User",
                "role": "MANAGER",
            },
            {
                "username": "test_planner",
                "email": "planner@test.ardt.com",
                "first_name": "Planner",
                "last_name": "User",
                "role": "PLANNER",
            },
            {
                "username": "test_technician",
                "email": "tech@test.ardt.com",
                "first_name": "Tech",
                "last_name": "User",
                "role": "TECHNICIAN",
            },
            {
                "username": "test_qc",
                "email": "qc@test.ardt.com",
                "first_name": "QC",
                "last_name": "Inspector",
                "role": "QC",
            },
        ]

        created_count = 0
        for user_data in test_users:
            role = user_data.pop("role")
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    **user_data,
                    "is_active": True,
                },
            )
            if created:
                user.set_password("testpass123")
                user.save()

                # Add role using UserRole model
                try:
                    from apps.accounts.models import Role, UserRole

                    role_obj = Role.objects.get(code=role)
                    UserRole.objects.get_or_create(user=user, role=role_obj)
                    self.stdout.write(f"    Assigned role: {role}")
                except Role.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"    Role {role} not found - skipping role assignment"))

                created_count += 1
                self.stdout.write(f"  Created user: {user.username} ({role})")

        self.stdout.write(f"  {created_count} test users created.")

    def create_drill_bits(self):
        """Create test drill bits."""
        from apps.workorders.models import DrillBit

        self.stdout.write("Creating test drill bits...")

        bit_types = list(DrillBit.BitType.choices)
        statuses = list(DrillBit.Status.choices)

        sizes = [
            Decimal("6.000"),
            Decimal("8.500"),
            Decimal("9.875"),
            Decimal("12.250"),
            Decimal("17.500"),
        ]

        iadc_codes = ["M223", "M323", "M423", "S323", "S423", "M222", "S222"]

        created_count = 0
        for i in range(1, 21):  # Create 20 drill bits
            serial = f"TEST-FC-{str(i).zfill(4)}"
            bit, created = DrillBit.objects.get_or_create(
                serial_number=serial,
                defaults={
                    "bit_type": random.choice(bit_types)[0],
                    "size": random.choice(sizes),
                    "iadc_code": random.choice(iadc_codes),
                    "status": random.choice(statuses)[0],
                    "total_hours": Decimal(str(random.randint(0, 500))),
                    "total_footage": random.randint(0, 10000),
                    "run_count": random.randint(0, 5),
                },
            )
            if created:
                created_count += 1

        self.stdout.write(f"  {created_count} test drill bits created.")

    def create_work_orders(self, minimal=False):
        """Create test work orders."""
        from apps.workorders.models import DrillBit, WorkOrder

        self.stdout.write("Creating test work orders...")

        wo_types = list(WorkOrder.WOType.choices)
        statuses = list(WorkOrder.Status.choices)
        priorities = list(WorkOrder.Priority.choices)

        # Get test technician for assignment
        technician = User.objects.filter(username="test_technician").first()

        # Get drill bits for assignment
        drill_bits = list(DrillBit.objects.filter(serial_number__startswith="TEST-")[:10])

        today = timezone.now().date()
        count = 10 if minimal else 30

        created_count = 0
        for i in range(1, count + 1):
            wo_number = f"WO-TEST-{str(i).zfill(4)}"
            wo, created = WorkOrder.objects.get_or_create(
                wo_number=wo_number,
                defaults={
                    "wo_type": random.choice(wo_types)[0],
                    "status": random.choice(statuses)[0],
                    "priority": random.choice(priorities)[0],
                    "drill_bit": random.choice(drill_bits) if drill_bits else None,
                    "assigned_to": technician if random.random() > 0.3 else None,
                    "planned_start": today + timedelta(days=random.randint(-10, 10)),
                    "planned_end": today + timedelta(days=random.randint(5, 30)),
                    "due_date": today + timedelta(days=random.randint(-5, 20)),
                    "description": f"Test work order {i} for development purposes.",
                    "notes": "Auto-generated test data.",
                },
            )
            if created:
                # Set timestamps for in-progress and completed work orders
                if wo.status == "IN_PROGRESS":
                    wo.actual_start = timezone.now() - timedelta(days=random.randint(1, 5))
                    wo.progress_percent = random.randint(10, 90)
                    wo.save()
                elif wo.status == "COMPLETED":
                    wo.actual_start = timezone.now() - timedelta(days=random.randint(5, 15))
                    wo.actual_end = timezone.now() - timedelta(days=random.randint(0, 3))
                    wo.progress_percent = 100
                    wo.save()

                created_count += 1

        self.stdout.write(f"  {created_count} test work orders created.")

        # Summary
        self.stdout.write("")
        self.stdout.write("Test Data Summary:")
        self.stdout.write(f'  - Total drill bits: {DrillBit.objects.filter(serial_number__startswith="TEST-").count()}')
        self.stdout.write(f'  - Total work orders: {WorkOrder.objects.filter(wo_number__startswith="WO-TEST").count()}')
        self.stdout.write("")
        self.stdout.write("Test User Credentials (password: testpass123):")
        self.stdout.write("  - test_admin (Admin)")
        self.stdout.write("  - test_manager (Manager)")
        self.stdout.write("  - test_planner (Planner)")
        self.stdout.write("  - test_technician (Technician)")
        self.stdout.write("  - test_qc (QC Inspector)")
