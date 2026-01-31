"""
ARDT FMS - Seed Locations
Phase 2: Products & Drill Bit Tracking

Creates physical locations where drill bits can be tracked.
"""

from django.core.management.base import BaseCommand

from apps.sales.models import Rig
from apps.workorders.models import Location


class Command(BaseCommand):
    help = "Seed locations for ARDT drill bit tracking"

    def handle(self, *args, **options):
        # Base locations (not linked to rigs)
        base_locations = [
            # Receiving / Intake areas
            {
                "code": "RCV-AREA",
                "name": "Receiving Area",
                "location_type": Location.LocationType.RECEIVING,
            },
            {
                "code": "PDC-RCV",
                "name": "PDC Receiving Area",
                "location_type": Location.LocationType.RECEIVING,
            },
            {
                "code": "BACKLOAD",
                "name": "Backload Area",
                "location_type": Location.LocationType.RECEIVING,
            },
            # Warehouses
            {
                "code": "WH-COMP",
                "name": "Components Warehouse",
                "location_type": Location.LocationType.WAREHOUSE,
            },
            {
                "code": "WH-FG",
                "name": "Finished Goods Warehouse",
                "location_type": Location.LocationType.WAREHOUSE,
            },
            # Production / WIP
            {
                "code": "WIP",
                "name": "Work In Progress (WIP)",
                "location_type": Location.LocationType.WIP,
            },
            {
                "code": "RS-MAIN",
                "name": "Repair Shop",
                "location_type": Location.LocationType.REPAIR_SHOP,
            },
            # Dispatch
            {
                "code": "DISPATCH",
                "name": "Dispatch Area",
                "location_type": Location.LocationType.DISPATCH,
            },
            # Inspection / Evaluation / QC
            {
                "code": "FINAL-INSP",
                "name": "Final Inspection Area",
                "location_type": Location.LocationType.INSPECTION,
            },
            {
                "code": "EVAL-AREA",
                "name": "Evaluation Area",
                "location_type": Location.LocationType.EVALUATION,
            },
            {
                "code": "QC-AREA",
                "name": "QC Area",
                "location_type": Location.LocationType.QC,
            },
            # Scrap
            {
                "code": "SCRAP-YARD",
                "name": "Scrap Yard",
                "location_type": Location.LocationType.SCRAP,
            },
            # External
            {
                "code": "USA-HAL",
                "name": "Woodlands, Texas (USA)",
                "location_type": Location.LocationType.USA,
                "address": "Halliburton, 3000 N Sam Houston Pkwy E, Houston, TX 77032",
            },
            {
                "code": "FACTORY",
                "name": "Factory",
                "location_type": Location.LocationType.FACTORY,
            },
            {
                "code": "TRANSIT",
                "name": "In Transit",
                "location_type": Location.LocationType.TRANSIT,
            },
        ]

        created_count = 0
        updated_count = 0

        # Create base locations
        for loc_data in base_locations:
            obj, created = Location.objects.update_or_create(
                code=loc_data["code"],
                defaults={
                    "name": loc_data["name"],
                    "location_type": loc_data["location_type"],
                    "address": loc_data.get("address", ""),
                    "is_active": True,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        # Create rig locations from existing rigs
        rigs = Rig.objects.filter(is_active=True)
        for rig in rigs:
            location_code = f"RIG-{rig.code}"
            obj, created = Location.objects.update_or_create(
                code=location_code,
                defaults={
                    "name": f"Rig {rig.code}",
                    "location_type": Location.LocationType.RIG,
                    "rig": rig,
                    "address": rig.location or "",
                    "is_active": True,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Locations: {created_count} created, {updated_count} updated. "
                f"Total: {Location.objects.count()} ({rigs.count()} rig locations)"
            )
        )
