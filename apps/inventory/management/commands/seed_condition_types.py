"""
Seed command for ConditionType - Item condition master data.

Usage:
    python manage.py seed_condition_types
"""

from django.core.management.base import BaseCommand
from apps.inventory.models import ConditionType


class Command(BaseCommand):
    help = "Seed condition types (NEW, USED-RETROFIT, etc.)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Condition Types...\n")

        # Condition types for inventory items
        # (code, name, description, is_new, is_saleable, cost_multiplier, display_order, color_code)
        condition_types = [
            (
                "NEW",
                "New",
                "Brand new, never used item",
                True, True, 1.00, 1, "#22c55e"
            ),
            (
                "USED-RET",
                "Used - Retrofit",
                "Used item reconditioned to as-new standard (retrofit quality)",
                False, True, 0.85, 2, "#3b82f6"
            ),
            (
                "USED-GRD",
                "Used - Ground",
                "Used item with surface damage repaired by grinding",
                False, True, 0.70, 3, "#8b5cf6"
            ),
            (
                "USED-E&O",
                "Used - E&O",
                "Used item classified as Excess and Obsolete",
                False, True, 0.50, 4, "#f59e0b"
            ),
            (
                "REFURB",
                "Refurbished",
                "Factory refurbished item with warranty",
                False, True, 0.80, 5, "#06b6d4"
            ),
            (
                "RECERT",
                "Recertified",
                "Recertified after inspection (meets original specs)",
                False, True, 0.90, 6, "#14b8a6"
            ),
            (
                "REWORK",
                "Rework",
                "Item being reworked/repaired",
                False, False, 0.60, 7, "#eab308"
            ),
            (
                "SCRAP",
                "Scrap",
                "Damaged beyond repair, for disposal only",
                False, False, 0.00, 8, "#ef4444"
            ),
        ]

        created_count = 0
        for code, name, description, is_new, is_saleable, cost_mult, order, color in condition_types:
            obj, created = ConditionType.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": description,
                    "is_new": is_new,
                    "is_saleable": is_saleable,
                    "cost_multiplier": cost_mult,
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
                f"\nTotal condition types: {ConditionType.objects.count()} (new: {created_count})"
            )
        )
