"""
Seed command for LocationType - Location type master data.

Usage:
    python manage.py seed_location_types
"""

from django.core.management.base import BaseCommand
from apps.inventory.models import LocationType, QualityStatus


class Command(BaseCommand):
    help = "Seed location types (WAREHOUSE, QUARANTINE, RIG, etc.)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Location Types...\n")

        # Get quarantine quality status for default
        qrn_status = QualityStatus.objects.filter(code="QRN").first()

        # Location types categorizing inventory locations
        # (code, name, description, is_stockable, is_internal, default_qc_code, include_in_count, display_order, color_code)
        location_types = [
            (
                "WH",
                "Warehouse",
                "Standard warehouse storage location",
                True, True, None, True, 1, "#22c55e"
            ),
            (
                "QRN",
                "Quarantine",
                "Quarantine/inspection area - goods awaiting QC",
                True, True, "QRN", True, 2, "#f59e0b"
            ),
            (
                "RECV",
                "Receiving",
                "Goods receiving dock/area",
                True, True, "QRN", False, 3, "#3b82f6"
            ),
            (
                "SHIP",
                "Shipping",
                "Shipping dock/staging area",
                True, True, None, False, 4, "#8b5cf6"
            ),
            (
                "PROD",
                "Production",
                "Production floor/shop floor location",
                True, True, None, True, 5, "#06b6d4"
            ),
            (
                "WIP",
                "Work in Progress",
                "Work-in-progress staging area",
                True, True, None, True, 6, "#14b8a6"
            ),
            (
                "RIG",
                "Rig Site",
                "External rig site location",
                True, False, None, False, 7, "#f97316"
            ),
            (
                "CUST",
                "Customer Site",
                "Customer location (for consignment out)",
                True, False, None, False, 8, "#ec4899"
            ),
            (
                "TRANSIT",
                "In Transit",
                "Virtual location for goods in transit",
                True, True, None, False, 9, "#64748b"
            ),
            (
                "SCRAP",
                "Scrap",
                "Scrap/disposal holding area",
                True, True, None, False, 10, "#ef4444"
            ),
            (
                "HOLD",
                "Hold",
                "General hold area (blocked stock)",
                True, True, "BLK", True, 11, "#dc2626"
            ),
            (
                "RETURN",
                "Returns",
                "Customer returns processing area",
                True, True, "QRN", False, 12, "#eab308"
            ),
        ]

        created_count = 0
        for code, name, desc, stockable, internal, qc_code, count, order, color in location_types:
            # Get quality status for default
            default_qc = None
            if qc_code:
                default_qc = QualityStatus.objects.filter(code=qc_code).first()

            obj, created = LocationType.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": desc,
                    "is_stockable": stockable,
                    "is_internal": internal,
                    "default_quality_status": default_qc,
                    "include_in_cycle_count": count,
                    "display_order": order,
                    "color_code": color,
                    "is_active": True,
                }
            )
            if created:
                self.stdout.write(f"  Created: {name}")
                created_count += 1
            else:
                self.stdout.write(f"  Exists: {name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTotal location types: {LocationType.objects.count()} (new: {created_count})"
            )
        )
