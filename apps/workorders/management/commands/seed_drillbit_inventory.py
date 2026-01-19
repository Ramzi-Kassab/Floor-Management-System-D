"""
Management command to seed drill bit inventory test data.

Creates:
- Locations (Warehouse, Repair Shop, QC Area, etc.)
- Sample drill bits with various statuses
- Sample events for drill bit lifecycle

Usage:
    python manage.py seed_drillbit_inventory           # Preview mode
    python manage.py seed_drillbit_inventory --confirm # Actually create
"""

from datetime import timedelta
from decimal import Decimal
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.workorders.models import BitEvent, DrillBit, Location

User = get_user_model()


class Command(BaseCommand):
    help = "Seed drill bit inventory with test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Actually create the data (without this flag, runs in preview mode)",
        )
        parser.add_argument(
            "--bits",
            type=int,
            default=25,
            help="Number of drill bits to create (default: 25)",
        )

    def handle(self, *args, **options):
        confirm = options["confirm"]
        num_bits = options["bits"]

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Drill Bit Inventory Seeder")
        self.stdout.write("=" * 60)

        if not confirm:
            self.stdout.write(
                self.style.WARNING("\nPREVIEW MODE - No data will be created")
            )
            self.stdout.write("Run with --confirm to actually create data\n")

        # Get or create a user for events
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No users found. Please create a user first."))
            return

        self.stdout.write(f"\nUsing user: {user.username}")

        # Create locations
        locations_data = [
            ("WH-MAIN", "Main Warehouse", "WAREHOUSE"),
            ("WH-BITS", "Bit Storage Warehouse", "WAREHOUSE"),
            ("SHOP-1", "Repair Shop 1", "REPAIR_SHOP"),
            ("SHOP-2", "Repair Shop 2", "REPAIR_SHOP"),
            ("EVAL-1", "Evaluation Area", "EVALUATION"),
            ("QC-AREA", "Quality Control Area", "QC"),
            ("SCRAP-YD", "Scrap Yard", "SCRAP"),
            ("USA-FAC", "USA Facility", "USA"),
            ("TRANSIT", "In Transit", "TRANSIT"),
            ("RIG-001", "Rig Site 001 - Aramco", "RIG"),
            ("RIG-002", "Rig Site 002 - SLB", "RIG"),
        ]

        self.stdout.write(f"\nLocations to create: {len(locations_data)}")
        locations_created = 0
        locations = {}

        for code, name, loc_type in locations_data:
            existing = Location.objects.filter(code=code).first()
            if existing:
                locations[code] = existing
                self.stdout.write(f"  - {code}: Already exists")
            else:
                if confirm:
                    loc = Location.objects.create(
                        code=code, name=name, location_type=loc_type, is_active=True
                    )
                    locations[code] = loc
                    locations_created += 1
                self.stdout.write(f"  + {code}: {name} ({loc_type})")

        # Sample drill bit data
        bit_sizes = [Decimal("6.125"), Decimal("8.5"), Decimal("9.5"), Decimal("12.25"), Decimal("17.5")]
        bit_types = ["FC", "RC"]
        lifecycle_statuses = ["NEW", "DEPLOYED", "BACKLOADED", "EVALUATION", "IN_REPAIR", "REPAIRED", "RERUN"]
        physical_statuses = ["AT_ARDT", "AT_CUSTOMER", "IN_TRANSIT", "AT_RIG"]
        accounting_statuses = ["ARDT_OWNED", "CUSTOMER_OWNED", "ON_CONSIGNMENT"]

        self.stdout.write(f"\nDrill bits to create: {num_bits}")
        bits_created = 0

        # Generate serial numbers
        # FC bits: 8 digits (PDC)
        # RC bits: 6-8 digits (Tri-cone)
        for i in range(num_bits):
            bit_type = random.choice(bit_types)

            if bit_type == "FC":
                serial = f"{random.randint(10000000, 99999999)}"
            else:
                serial = f"{random.randint(100000, 99999999)}"

            # Check if serial exists
            if DrillBit.objects.filter(serial_number=serial).exists():
                continue

            size = random.choice(bit_sizes)
            lifecycle = random.choice(lifecycle_statuses)
            physical = random.choice(physical_statuses)
            accounting = random.choice(accounting_statuses)

            # Pick appropriate location based on status
            if lifecycle == "NEW":
                loc_code = "WH-MAIN"
            elif lifecycle == "IN_REPAIR":
                loc_code = random.choice(["SHOP-1", "SHOP-2"])
            elif lifecycle == "EVALUATION":
                loc_code = "EVAL-1"
            elif lifecycle in ["DEPLOYED", "RERUN"]:
                loc_code = random.choice(["RIG-001", "RIG-002"])
                physical = "AT_RIG"
            else:
                loc_code = random.choice(["WH-MAIN", "WH-BITS", "QC-AREA"])

            location = locations.get(loc_code) or Location.objects.filter(code=loc_code).first()

            # Random costs
            original_cost = Decimal(random.randint(15000, 80000))
            repair_cost = Decimal(random.randint(0, 15000)) if lifecycle not in ["NEW"] else Decimal(0)

            # Random dates
            received_date = timezone.now().date() - timedelta(days=random.randint(30, 365))

            # Repair counts
            repair_count = random.randint(0, 5) if lifecycle not in ["NEW"] else 0
            deployment_count = random.randint(0, 10)

            if confirm:
                bit = DrillBit.objects.create(
                    serial_number=serial,
                    bit_type=bit_type,
                    size=size,
                    mat_number=f"MAT{random.randint(1000000, 9999999)}",
                    iadc_code=f"M{random.randint(100, 999)}",
                    lifecycle_status=lifecycle,
                    physical_status=physical,
                    accounting_status=accounting,
                    bit_location=location,
                    status=DrillBit.Status.IN_STOCK if lifecycle == "NEW" else DrillBit.Status.IN_PRODUCTION,
                    original_cost=original_cost,
                    total_repair_cost=repair_cost,
                    current_book_value=original_cost + repair_cost,
                    received_date=received_date,
                    repair_count=repair_count,
                    deployment_count=deployment_count,
                    created_by=user,
                )

                # Create a RECEIVED event
                if location:
                    BitEvent.objects.create(
                        bit=bit,
                        event_type=BitEvent.EventType.RECEIVED,
                        event_date=timezone.make_aware(
                            timezone.datetime.combine(received_date, timezone.datetime.min.time())
                        ),
                        location=location,
                        notes=f"Initial registration. Serial: {serial}",
                        performed_by=user,
                    )

                bits_created += 1

            self.stdout.write(
                f"  {'+ ' if confirm else '  '}{serial}: {bit_type} {size}\" @ {loc_code} ({lifecycle})"
            )

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Summary:")
        self.stdout.write("=" * 60)

        if confirm:
            self.stdout.write(self.style.SUCCESS(f"Locations created: {locations_created}"))
            self.stdout.write(self.style.SUCCESS(f"Drill bits created: {bits_created}"))
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nTotal locations: {Location.objects.count()}"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Total drill bits: {DrillBit.objects.count()}"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"\nWould create {len(locations_data)} locations and {num_bits} drill bits"
                )
            )
            self.stdout.write(
                self.style.WARNING("\nRun with --confirm to actually create data")
            )
