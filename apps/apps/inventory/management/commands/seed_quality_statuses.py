"""
Seed command for QualityStatus - Quality gate state master data.

Usage:
    python manage.py seed_quality_statuses
"""

from django.core.management.base import BaseCommand
from apps.inventory.models import QualityStatus


class Command(BaseCommand):
    help = "Seed quality statuses (QUARANTINE, RELEASED, BLOCKED, etc.)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Quality Statuses...\n")

        # Quality statuses for QC workflow
        # (code, name, description, is_available, is_initial, is_terminal, allowed_transitions, display_order, color_code)
        quality_statuses = [
            (
                "QRN",
                "Quarantine",
                "Awaiting inspection - default status for new receipts",
                False, True, False, ["REL", "BLK", "INS"], 1, "#f59e0b"
            ),
            (
                "INS",
                "Under Inspection",
                "Currently being inspected by QC",
                False, False, False, ["REL", "BLK", "QRN"], 2, "#3b82f6"
            ),
            (
                "REL",
                "Released",
                "Passed QC inspection - available for use/sale",
                True, False, False, ["BLK", "QRN"], 3, "#22c55e"
            ),
            (
                "BLK",
                "Blocked",
                "Failed QC inspection - not available for use",
                False, False, False, ["PND", "SCR", "QRN"], 4, "#ef4444"
            ),
            (
                "PND",
                "Pending Disposition",
                "Failed QC, awaiting decision on disposition",
                False, False, False, ["REL", "SCR", "RTN"], 5, "#8b5cf6"
            ),
            (
                "RTN",
                "Return to Vendor",
                "Marked for return to vendor",
                False, False, True, [], 6, "#f97316"
            ),
            (
                "SCR",
                "Scrap",
                "Marked for scrap disposal",
                False, False, True, [], 7, "#dc2626"
            ),
        ]

        created_count = 0
        for code, name, desc, avail, initial, terminal, transitions, order, color in quality_statuses:
            obj, created = QualityStatus.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": desc,
                    "is_available": avail,
                    "is_initial": initial,
                    "is_terminal": terminal,
                    "allowed_transitions": transitions,
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
                f"\nTotal quality statuses: {QualityStatus.objects.count()} (new: {created_count})"
            )
        )
