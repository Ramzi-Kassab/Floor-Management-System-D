"""
Seed command for Inventory Items and Variants.
Creates sample items for cutters, tools, and spare parts with variants.

Usage:
    python manage.py seed_inventory
"""

from django.core.management.base import BaseCommand
from apps.inventory.models import (
    InventoryCategory, InventoryItem, ItemVariant, UnitOfMeasure
)


class Command(BaseCommand):
    help = "Seed sample inventory items and variants"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Inventory Items and Variants...\n")

        # Get or create necessary categories
        categories = self.ensure_categories()

        # Get default unit
        ea_unit = UnitOfMeasure.objects.filter(code="EA").first()

        # Create sample items
        items_created = 0
        variants_created = 0

        # =====================================================================
        # PDC CUTTERS
        # =====================================================================
        self.stdout.write("\n--- PDC Cutters ---")
        cutter_items = [
            {
                "code": "CUT-1308-STD",
                "name": "PDC Cutter 13.08mm Standard",
                "category": categories.get("cutters"),
                "mat_number": "MAT-CUT-001",
                "item_number": "ERP-CUT-001",
                "standard_cost": 125.00,
            },
            {
                "code": "CUT-1308-PRM",
                "name": "PDC Cutter 13.08mm Premium",
                "category": categories.get("cutters"),
                "mat_number": "MAT-CUT-002",
                "item_number": "ERP-CUT-002",
                "standard_cost": 185.00,
            },
            {
                "code": "CUT-1604-STD",
                "name": "PDC Cutter 16.04mm Standard",
                "category": categories.get("cutters"),
                "mat_number": "MAT-CUT-003",
                "item_number": "ERP-CUT-003",
                "standard_cost": 145.00,
            },
            {
                "code": "CUT-1904-PRM",
                "name": "PDC Cutter 19.04mm Premium",
                "category": categories.get("cutters"),
                "mat_number": "MAT-CUT-004",
                "item_number": "ERP-CUT-004",
                "standard_cost": 225.00,
            },
        ]

        for item_data in cutter_items:
            item, created = InventoryItem.objects.get_or_create(
                code=item_data["code"],
                defaults={
                    "name": item_data["name"],
                    "category": item_data["category"],
                    "item_type": "COMPONENT",
                    "mat_number": item_data.get("mat_number", ""),
                    "item_number": item_data.get("item_number", ""),
                    "unit": "EA",
                    "standard_cost": item_data.get("standard_cost", 0),
                    "has_variants": True,
                    "is_active": True,
                }
            )
            if created:
                items_created += 1
                self.stdout.write(f"  Created Item: {item.code}")
            else:
                self.stdout.write(f"  Exists: {item.code}")

            # Create variants for this cutter
            variants_created += self.create_cutter_variants(item)

        # =====================================================================
        # TOOLS
        # =====================================================================
        self.stdout.write("\n--- Tools ---")
        tool_items = [
            {
                "code": "TOOL-WRN-001",
                "name": "Torque Wrench 1/2 inch",
                "category": categories.get("tools"),
                "mat_number": "MAT-TOOL-001",
                "standard_cost": 450.00,
            },
            {
                "code": "TOOL-GRN-001",
                "name": "Pneumatic Grinder 4 inch",
                "category": categories.get("tools"),
                "mat_number": "MAT-TOOL-002",
                "standard_cost": 850.00,
            },
            {
                "code": "TOOL-DRL-001",
                "name": "Impact Drill Heavy Duty",
                "category": categories.get("tools"),
                "mat_number": "MAT-TOOL-003",
                "standard_cost": 1200.00,
            },
        ]

        for item_data in tool_items:
            item, created = InventoryItem.objects.get_or_create(
                code=item_data["code"],
                defaults={
                    "name": item_data["name"],
                    "category": item_data["category"],
                    "item_type": "TOOL",
                    "mat_number": item_data.get("mat_number", ""),
                    "unit": "EA",
                    "standard_cost": item_data.get("standard_cost", 0),
                    "has_variants": True,
                    "is_active": True,
                }
            )
            if created:
                items_created += 1
                self.stdout.write(f"  Created Item: {item.code}")
            else:
                self.stdout.write(f"  Exists: {item.code}")

            # Create variants for tools (simpler - just NEW/USED)
            variants_created += self.create_tool_variants(item)

        # =====================================================================
        # SPARE PARTS
        # =====================================================================
        self.stdout.write("\n--- Spare Parts ---")
        spare_items = [
            {
                "code": "SPR-BRG-001",
                "name": "Bearing 6205-2RS",
                "category": categories.get("spare_parts"),
                "mat_number": "MAT-SPR-001",
                "standard_cost": 25.00,
            },
            {
                "code": "SPR-SEL-001",
                "name": "Seal Kit Hydraulic Cylinder",
                "category": categories.get("spare_parts"),
                "mat_number": "MAT-SPR-002",
                "standard_cost": 85.00,
            },
            {
                "code": "SPR-FLT-001",
                "name": "Filter Element Hydraulic",
                "category": categories.get("spare_parts"),
                "mat_number": "MAT-SPR-003",
                "standard_cost": 45.00,
            },
            {
                "code": "SPR-NOZ-001",
                "name": "Nozzle 12/32 Standard",
                "category": categories.get("spare_parts"),
                "mat_number": "MAT-SPR-004",
                "standard_cost": 35.00,
            },
        ]

        for item_data in spare_items:
            item, created = InventoryItem.objects.get_or_create(
                code=item_data["code"],
                defaults={
                    "name": item_data["name"],
                    "category": item_data["category"],
                    "item_type": "SPARE_PART",
                    "mat_number": item_data.get("mat_number", ""),
                    "unit": "EA",
                    "standard_cost": item_data.get("standard_cost", 0),
                    "has_variants": True,
                    "is_active": True,
                }
            )
            if created:
                items_created += 1
                self.stdout.write(f"  Created Item: {item.code}")
            else:
                self.stdout.write(f"  Exists: {item.code}")

            # Create variants for spare parts
            variants_created += self.create_spare_variants(item)

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\nCreated {items_created} items and {variants_created} variants"
        ))
        self.stdout.write(f"Total Items: {InventoryItem.objects.count()}")
        self.stdout.write(f"Total Variants: {ItemVariant.objects.count()}")

    def ensure_categories(self):
        """Ensure required categories exist."""
        categories = {}

        cat_data = [
            ("CUT", "PDC Cutters", "COMPONENT"),
            ("TOOL", "Tools", "TOOL"),
            ("SPR", "Spare Parts", "SPARE_PART"),
        ]

        for code, name, item_type in cat_data:
            cat, _ = InventoryCategory.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "item_type": item_type,
                    "code_prefix": code,
                }
            )
            categories[code.lower() + "ters" if code == "CUT" else code.lower().replace("spr", "spare_parts").replace("tool", "tools")] = cat

        # Fix mapping
        categories = {
            "cutters": InventoryCategory.objects.filter(code="CUT").first(),
            "tools": InventoryCategory.objects.filter(code="TOOL").first(),
            "spare_parts": InventoryCategory.objects.filter(code="SPR").first(),
        }

        return categories

    def create_cutter_variants(self, item):
        """Create standard variants for PDC cutters."""
        variants_created = 0

        # Cutter variants based on condition, acquisition, reclaim category
        variant_configs = [
            # New Purchased (ARDT)
            {
                "suffix": "NEW-PUR",
                "condition": "NEW",
                "acquisition": "PURCHASED",
                "ownership": "ARDT",
                "valuation": 100,
                "legacy_mat": f"{item.mat_number}-NEW",
            },
            # Retrofit (reclaimed but as-new quality)
            {
                "suffix": "RET",
                "condition": "NEW",
                "acquisition": "RECLAIMED",
                "reclaim_category": "RETROFIT",
                "ownership": "ARDT",
                "valuation": 85,
                "legacy_mat": f"{item.mat_number}-RET",
            },
            # E&O (Excessive & Obsolete - new but written down)
            {
                "suffix": "EO",
                "condition": "NEW",
                "acquisition": "RECLAIMED",
                "reclaim_category": "E_AND_O",
                "ownership": "ARDT",
                "valuation": 30,
                "legacy_mat": f"{item.mat_number}-EO",
            },
            # Ground Reclaim (surface damage)
            {
                "suffix": "GRD",
                "condition": "USED",
                "acquisition": "RECLAIMED",
                "reclaim_category": "GROUND",
                "ownership": "ARDT",
                "valuation": 40,
                "legacy_mat": f"{item.mat_number}-GRD",
            },
            # Standard Reclaim
            {
                "suffix": "RCL",
                "condition": "USED",
                "acquisition": "RECLAIMED",
                "reclaim_category": "STANDARD",
                "ownership": "ARDT",
                "valuation": 50,
                "legacy_mat": f"{item.mat_number}-RCL",
            },
        ]

        for config in variant_configs:
            code = f"{item.code}-{config['suffix']}"
            variant, created = ItemVariant.objects.get_or_create(
                code=code,
                defaults={
                    "base_item": item,
                    "name": f"{item.name} ({config['suffix']})",
                    "legacy_mat_no": config.get("legacy_mat", ""),
                    "condition": config["condition"],
                    "acquisition": config["acquisition"],
                    "reclaim_category": config.get("reclaim_category", ""),
                    "ownership": config["ownership"],
                    "valuation_percentage": config["valuation"],
                    "standard_cost": float(item.standard_cost) * config["valuation"] / 100,
                    "is_active": True,
                }
            )
            if created:
                variants_created += 1
                self.stdout.write(f"    + Variant: {code} ({config['suffix']})")

        return variants_created

    def create_tool_variants(self, item):
        """Create variants for tools - simpler set."""
        variants_created = 0

        variant_configs = [
            # New Purchased
            {
                "suffix": "NEW",
                "condition": "NEW",
                "acquisition": "PURCHASED",
                "ownership": "ARDT",
                "valuation": 100,
            },
            # Used (internal)
            {
                "suffix": "USED",
                "condition": "USED",
                "acquisition": "PURCHASED",
                "ownership": "ARDT",
                "valuation": 60,
            },
        ]

        for config in variant_configs:
            code = f"{item.code}-{config['suffix']}"
            variant, created = ItemVariant.objects.get_or_create(
                code=code,
                defaults={
                    "base_item": item,
                    "name": f"{item.name} ({config['suffix']})",
                    "condition": config["condition"],
                    "acquisition": config["acquisition"],
                    "ownership": config["ownership"],
                    "valuation_percentage": config["valuation"],
                    "standard_cost": float(item.standard_cost) * config["valuation"] / 100,
                    "is_active": True,
                }
            )
            if created:
                variants_created += 1
                self.stdout.write(f"    + Variant: {code}")

        return variants_created

    def create_spare_variants(self, item):
        """Create variants for spare parts."""
        variants_created = 0

        variant_configs = [
            # New Purchased (ARDT owned)
            {
                "suffix": "NEW-ARDT",
                "condition": "NEW",
                "acquisition": "PURCHASED",
                "ownership": "ARDT",
                "valuation": 100,
            },
            # Reclaimed/refurbished
            {
                "suffix": "RCL",
                "condition": "USED",
                "acquisition": "RECLAIMED",
                "reclaim_category": "STANDARD",
                "ownership": "ARDT",
                "valuation": 50,
            },
        ]

        for config in variant_configs:
            code = f"{item.code}-{config['suffix']}"
            variant, created = ItemVariant.objects.get_or_create(
                code=code,
                defaults={
                    "base_item": item,
                    "name": f"{item.name} ({config['suffix']})",
                    "condition": config["condition"],
                    "acquisition": config["acquisition"],
                    "reclaim_category": config.get("reclaim_category", ""),
                    "ownership": config["ownership"],
                    "valuation_percentage": config["valuation"],
                    "standard_cost": float(item.standard_cost) * config["valuation"] / 100,
                    "is_active": True,
                }
            )
            if created:
                variants_created += 1
                self.stdout.write(f"    + Variant: {code}")

        return variants_created
