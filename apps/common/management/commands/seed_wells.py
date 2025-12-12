"""
ARDT FMS - Seed Wells Command
Creates real wells from Morning Report 01-02-2025

Usage: python manage.py seed_wells
"""

from django.core.management.base import BaseCommand
from apps.sales.models import Well, Rig, Customer


class Command(BaseCommand):
    help = "Seed real wells from Morning Report data"

    # Real Wells from MASTER_PLAN.md (Morning Report 01-02-2025)
    # QTIF = Qatif Field, BRRI = Berri Field
    WELLS = [
        # QTIF Field (Qatif) - Development & Injection Wells
        {
            "code": "QTIF-598",
            "name": "QTIF-598",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "Development Drilling",
            "target": "Arab-C",
            "status": "Drilling",
            "is_active": True,
        },
        {
            "code": "QTIF-284",
            "name": "QTIF-284 (NDP-12)",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "Development Drilling",
            "target": "",
            "status": "Planned",
            "is_active": True,
        },
        {
            "code": "QTIF-545",
            "name": "QTIF-545",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "Development Drilling",
            "target": "",
            "status": "Planned",
            "is_active": True,
        },
        {
            "code": "QTIF-277",
            "name": "QTIF-277",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "Development Drilling",
            "target": "",
            "status": "Planned",
            "is_active": True,
        },
        {
            "code": "QTIF-790",
            "name": "QTIF-790",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "PWI (Production Well Injector)",
            "target": "Arab-C",
            "status": "Active",
            "is_active": True,
        },
        {
            "code": "QTIF-520",
            "name": "QTIF-520",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "PWI",
            "target": "UFDL",
            "status": "Active",
            "is_active": True,
        },
        {
            "code": "QTIF-521",
            "name": "QTIF-521",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "PWI",
            "target": "Arab-D",
            "status": "Active",
            "is_active": True,
        },
        {
            "code": "QTIF-542",
            "name": "QTIF-542",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "PWI",
            "target": "UFDL",
            "status": "Active",
            "is_active": True,
        },
        {
            "code": "QTIF-630",
            "name": "QTIF-630",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "WI (Water Injector)",
            "target": "Arab-D",
            "status": "Active",
            "is_active": True,
        },
        {
            "code": "QTIF-631",
            "name": "QTIF-631",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "WI",
            "target": "Arab-D",
            "status": "Active",
            "is_active": True,
        },
        {
            "code": "QTIF-632",
            "name": "QTIF-632",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "PWI",
            "target": "Arab-C",
            "status": "Active",
            "is_active": True,
        },
        {
            "code": "QTIF-752",
            "name": "QTIF-752",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "Injector",
            "target": "Arab-C",
            "status": "Shut-in",
            "is_active": False,
        },
        {
            "code": "QTIF-674",
            "name": "QTIF-674",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "Injector",
            "target": "Arab-C",
            "status": "Shut-in",
            "is_active": False,
        },
        {
            "code": "QTIF-501",
            "name": "QTIF-501 (Relief Well Primary)",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "Relief Well",
            "target": "",
            "status": "Standby",
            "is_active": True,
        },
        {
            "code": "QTIF-773",
            "name": "QTIF-773 (Relief Well Secondary)",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "Relief Well",
            "target": "",
            "status": "Standby",
            "is_active": True,
        },
        {
            "code": "QTIF-922",
            "name": "QTIF-922",
            "field_name": "Qatif",
            "customer_code": "ARAMCO",
            "well_type": "Water Well",
            "target": "",
            "status": "Active",
            "is_active": True,
        },
        # BRRI Field (Berri) - Workover Wells
        {
            "code": "BRRI-350",
            "name": "BRRI-350",
            "field_name": "Berri",
            "customer_code": "ARAMCO",
            "well_type": "Workover",
            "target": "",
            "status": "Active",
            "is_active": True,
        },
        {
            "code": "BRRI-380",
            "name": "BRRI-380",
            "field_name": "Berri",
            "customer_code": "ARAMCO",
            "well_type": "Next Location",
            "target": "",
            "status": "100% Ready",
            "is_active": True,
        },
        {
            "code": "BRRI-335",
            "name": "BRRI-335",
            "field_name": "Berri",
            "customer_code": "ARAMCO",
            "well_type": "Next Location",
            "target": "",
            "status": "100% Ready",
            "is_active": True,
        },
        {
            "code": "BRRI-381",
            "name": "BRRI-381",
            "field_name": "Berri",
            "customer_code": "ARAMCO",
            "well_type": "Next Location",
            "target": "",
            "status": "50% Ready",
            "is_active": True,
        },
        {
            "code": "BRRI-212",
            "name": "BRRI-212",
            "field_name": "Berri",
            "customer_code": "ARAMCO",
            "well_type": "Next Location",
            "target": "",
            "status": "Planned",
            "is_active": True,
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update of existing wells",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding ARDT Wells ===\n"))

        force = options.get("force", False)
        created_count = 0
        updated_count = 0
        skipped_count = 0

        # Cache customers
        customers = {c.code: c for c in Customer.objects.all()}

        for well_data in self.WELLS:
            code = well_data["code"]
            customer_code = well_data.pop("customer_code")
            # Remove non-model fields for storage
            well_type = well_data.pop("well_type", "")
            target = well_data.pop("target", "")
            status = well_data.pop("status", "")

            # Get customer
            customer = customers.get(customer_code)
            if customer:
                well_data["customer"] = customer

            try:
                well, created = Well.objects.get_or_create(
                    code=code,
                    defaults=well_data,
                )

                if created:
                    created_count += 1
                    field = well_data.get("field_name", "")
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Created: {code} - {field} ({well_type})")
                    )
                elif force:
                    for key, value in well_data.items():
                        setattr(well, key, value)
                    well.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  ↻ Updated: {code}")
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.NOTICE(f"  - Skipped (exists): {code}")
                    )

                # Restore for reference
                well_data["customer_code"] = customer_code
                well_data["well_type"] = well_type
                well_data["target"] = target
                well_data["status"] = status
                if "customer" in well_data:
                    del well_data["customer"]

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error creating {code}: {str(e)}")
                )
                well_data["customer_code"] = customer_code
                well_data["well_type"] = well_type
                well_data["target"] = target
                well_data["status"] = status
                if "customer" in well_data:
                    del well_data["customer"]

        # Summary
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.WARNING(f"  Updated: {updated_count}"))
        self.stdout.write(f"  Skipped: {skipped_count}")
        self.stdout.write("-" * 60)

        # Well statistics
        qtif_count = sum(1 for w in self.WELLS if w["field_name"] == "Qatif")
        brri_count = sum(1 for w in self.WELLS if w["field_name"] == "Berri")

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Well Summary ===\n"))
        self.stdout.write(f"  Qatif Field (QTIF): {qtif_count} wells")
        self.stdout.write(f"  Berri Field (BRRI): {brri_count} wells")
        self.stdout.write(f"  Total: {len(self.WELLS)} wells")

        self.stdout.write(self.style.SUCCESS("\n✓ Well seeding complete!\n"))
