"""
Seed command for AdjustmentReason - Stock adjustment reason master data.

Usage:
    python manage.py seed_adjustment_reasons
"""

from django.core.management.base import BaseCommand
from apps.inventory.models import AdjustmentReason


class Command(BaseCommand):
    help = "Seed adjustment reasons (DAMAGE, LOSS, FOUND, etc.)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Adjustment Reasons...\n")

        # Adjustment reasons for stock changes outside normal document flow
        # (code, name, description, direction, requires_approval, affects_valuation, display_order)
        adjustment_reasons = [
            (
                "INITIAL",
                "Initial Stock",
                "Initial stock entry during system setup",
                "POSITIVE", False, True, 1
            ),
            (
                "CYCLE",
                "Cycle Count",
                "Adjustment from cycle count discrepancy",
                "BOTH", False, True, 2
            ),
            (
                "PHYS",
                "Physical Inventory",
                "Adjustment from annual physical inventory",
                "BOTH", True, True, 3
            ),
            (
                "FOUND",
                "Found",
                "Previously missing item found",
                "POSITIVE", False, True, 4
            ),
            (
                "LOSS",
                "Loss",
                "Item lost or missing",
                "NEGATIVE", True, True, 5
            ),
            (
                "DAMAGE",
                "Damage",
                "Item damaged and unusable",
                "NEGATIVE", True, True, 6
            ),
            (
                "SCRAP",
                "Scrap",
                "Item scrapped",
                "NEGATIVE", True, True, 7
            ),
            (
                "OBSOLETE",
                "Obsolete",
                "Item obsoleted and removed from inventory",
                "NEGATIVE", True, True, 8
            ),
            (
                "PRODVAR",
                "Production Variance",
                "Production over/under run adjustment",
                "BOTH", False, True, 9
            ),
            (
                "RTV",
                "Return to Vendor",
                "Returned to vendor",
                "NEGATIVE", False, True, 10
            ),
            (
                "SAMPLE",
                "Sample",
                "Issued as sample (no sale)",
                "NEGATIVE", False, True, 11
            ),
            (
                "DONATION",
                "Donation",
                "Donated item",
                "NEGATIVE", True, True, 12
            ),
            (
                "THEFT",
                "Theft",
                "Item stolen",
                "NEGATIVE", True, True, 13
            ),
            (
                "EXPIRY",
                "Expiry",
                "Item expired and removed",
                "NEGATIVE", False, True, 14
            ),
            (
                "QUALITY",
                "Quality Rejection",
                "Rejected due to quality issues",
                "NEGATIVE", True, True, 15
            ),
            (
                "RECLASSIFY",
                "Reclassification",
                "Reclassified to different condition/category",
                "BOTH", False, False, 16
            ),
            (
                "CORRECTION",
                "Data Correction",
                "Correction of data entry error",
                "BOTH", True, True, 17
            ),
        ]

        created_count = 0
        for code, name, desc, direction, approval, valuation, order in adjustment_reasons:
            obj, created = AdjustmentReason.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": desc,
                    "default_direction": direction,
                    "requires_approval": approval,
                    "affects_valuation": valuation,
                    "display_order": order,
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
                f"\nTotal adjustment reasons: {AdjustmentReason.objects.count()} (new: {created_count})"
            )
        )
