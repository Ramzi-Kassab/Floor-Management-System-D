"""
Seed comprehensive test data for the inventory system.
Creates locations, items, stock records, documents, assets, BOMs, etc.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Seed comprehensive test data for inventory system"

    def handle(self, *args, **options):
        from apps.inventory.models import (
            InventoryCategory, InventoryItem, InventoryLocation, InventoryStock,
            UnitOfMeasure, MaterialLot, Party, ConditionType, QualityStatus,
            OwnershipType, LocationType, AdjustmentReason,
            StockLedger, StockBalance, GoodsReceiptNote, GRNLine,
            StockIssue, StockIssueLine, StockTransfer, StockTransferLine,
            StockAdjustment, StockAdjustmentLine, Asset, AssetMovement,
            BillOfMaterial, BOMLine, StockReservation,
            CycleCountPlan, CycleCountSession, CycleCountLine,
        )
        from apps.sales.models import Warehouse

        self.stdout.write("Seeding Inventory Test Data...")

        # Get or create admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username="admin", email="admin@ardt.com", password="admin123"
            )

        # Get reference data
        quality_statuses = {qs.code: qs for qs in QualityStatus.objects.all()}
        condition_types = {ct.code: ct for ct in ConditionType.objects.all()}
        ownership_types = {ot.code: ot for ot in OwnershipType.objects.all()}
        location_types = {lt.code: lt for lt in LocationType.objects.all()}
        adjustment_reasons = {ar.code: ar for ar in AdjustmentReason.objects.all()}
        parties = {p.code: p for p in Party.objects.all()}

        # =====================================================
        # 1. CREATE WAREHOUSES
        # =====================================================
        self.stdout.write("  Creating warehouses...")
        warehouses_data = [
            {"code": "WH-MAIN", "name": "Main Warehouse", "city": "Dammam"},
            {"code": "WH-PROD", "name": "Production Warehouse", "city": "Dammam"},
            {"code": "WH-QC", "name": "QC Hold Warehouse", "city": "Dammam"},
            {"code": "WH-SHIP", "name": "Shipping Warehouse", "city": "Dammam"},
            {"code": "WH-RIG01", "name": "Rig Site Alpha", "city": "Jubail"},
        ]
        warehouses = {}
        for wh_data in warehouses_data:
            wh, created = Warehouse.objects.get_or_create(
                code=wh_data["code"],
                defaults={"name": wh_data["name"], "city": wh_data["city"], "is_active": True}
            )
            warehouses[wh_data["code"]] = wh
            if created:
                self.stdout.write(f"    Created: {wh.name}")

        # =====================================================
        # 2. CREATE INVENTORY LOCATIONS
        # =====================================================
        self.stdout.write("  Creating inventory locations...")
        loc_type_wh = location_types.get("WH")
        loc_type_qrn = location_types.get("QRN")
        loc_type_recv = location_types.get("RECV")
        loc_type_ship = location_types.get("SHIP")
        loc_type_prod = location_types.get("PROD")
        loc_type_rig = location_types.get("RIG")

        locations_data = [
            {"code": "WH-MAIN-A1", "name": "Main WH - Aisle A1", "warehouse": "WH-MAIN", "loc_type": loc_type_wh},
            {"code": "WH-MAIN-A2", "name": "Main WH - Aisle A2", "warehouse": "WH-MAIN", "loc_type": loc_type_wh},
            {"code": "WH-MAIN-B1", "name": "Main WH - Aisle B1", "warehouse": "WH-MAIN", "loc_type": loc_type_wh},
            {"code": "WH-PROD-01", "name": "Production Floor 1", "warehouse": "WH-PROD", "loc_type": loc_type_prod},
            {"code": "WH-PROD-02", "name": "Production Floor 2", "warehouse": "WH-PROD", "loc_type": loc_type_prod},
            {"code": "WH-QC-HOLD", "name": "QC Hold Area", "warehouse": "WH-QC", "loc_type": loc_type_qrn},
            {"code": "WH-RECV-01", "name": "Receiving Dock 1", "warehouse": "WH-MAIN", "loc_type": loc_type_recv},
            {"code": "WH-SHIP-01", "name": "Shipping Dock 1", "warehouse": "WH-SHIP", "loc_type": loc_type_ship},
            {"code": "RIG-ALPHA-01", "name": "Rig Alpha Storage", "warehouse": "WH-RIG01", "loc_type": loc_type_rig},
        ]
        locations = {}
        for loc_data in locations_data:
            loc, created = InventoryLocation.objects.get_or_create(
                code=loc_data["code"],
                defaults={
                    "name": loc_data["name"],
                    "warehouse": warehouses.get(loc_data["warehouse"]),
                    "location_type": loc_data["loc_type"],
                    "is_active": True,
                }
            )
            locations[loc_data["code"]] = loc
            if created:
                self.stdout.write(f"    Created: {loc.name}")

        # =====================================================
        # 3. CREATE UNITS OF MEASURE
        # =====================================================
        self.stdout.write("  Creating units of measure...")
        uom_data = [
            {"code": "EA", "name": "Each", "unit_type": "QUANTITY"},
            {"code": "PC", "name": "Piece", "unit_type": "QUANTITY"},
            {"code": "KG", "name": "Kilogram", "unit_type": "WEIGHT"},
            {"code": "LB", "name": "Pound", "unit_type": "WEIGHT"},
            {"code": "M", "name": "Meter", "unit_type": "LENGTH"},
            {"code": "FT", "name": "Foot", "unit_type": "LENGTH"},
            {"code": "L", "name": "Liter", "unit_type": "VOLUME"},
            {"code": "GAL", "name": "Gallon", "unit_type": "VOLUME"},
            {"code": "BOX", "name": "Box", "unit_type": "QUANTITY"},
            {"code": "SET", "name": "Set", "unit_type": "QUANTITY"},
        ]
        uoms = {}
        for u in uom_data:
            uom, created = UnitOfMeasure.objects.get_or_create(
                code=u["code"],
                defaults={"name": u["name"], "unit_type": u["unit_type"], "is_active": True}
            )
            uoms[u["code"]] = uom

        # =====================================================
        # 4. CREATE INVENTORY CATEGORIES
        # =====================================================
        self.stdout.write("  Creating inventory categories...")
        categories_data = [
            {"code": "RAW", "name": "Raw Materials"},
            {"code": "COMP", "name": "Components"},
            {"code": "FG", "name": "Finished Goods"},
            {"code": "CONS", "name": "Consumables"},
            {"code": "SPARE", "name": "Spare Parts"},
            {"code": "TOOL", "name": "Tools & Equipment"},
        ]
        categories = {}
        for cat_data in categories_data:
            cat, created = InventoryCategory.objects.get_or_create(
                code=cat_data["code"],
                defaults={"name": cat_data["name"], "is_active": True}
            )
            categories[cat_data["code"]] = cat

        # =====================================================
        # 5. CREATE INVENTORY ITEMS
        # =====================================================
        self.stdout.write("  Creating inventory items...")
        items_data = [
            # Raw Materials
            {"code": "RM-TUNGSTEN-01", "name": "Tungsten Carbide Powder Grade A", "category": "RAW", "uom": "KG", "cost": 250.00, "reorder": 50, "min": 20},
            {"code": "RM-STEEL-01", "name": "Steel Alloy Round Bar 4140", "category": "RAW", "uom": "KG", "cost": 15.50, "reorder": 200, "min": 100},
            {"code": "RM-COPPER-01", "name": "Copper Brazing Rod", "category": "RAW", "uom": "KG", "cost": 45.00, "reorder": 30, "min": 15},
            # Components
            {"code": "COMP-PDC-8MM", "name": "PDC Cutter 8mm", "category": "COMP", "uom": "EA", "cost": 125.00, "reorder": 500, "min": 200},
            {"code": "COMP-PDC-13MM", "name": "PDC Cutter 13mm", "category": "COMP", "uom": "EA", "cost": 175.00, "reorder": 400, "min": 150},
            {"code": "COMP-PDC-16MM", "name": "PDC Cutter 16mm", "category": "COMP", "uom": "EA", "cost": 225.00, "reorder": 300, "min": 100},
            {"code": "COMP-NOZZLE-01", "name": "Nozzle Assembly Standard", "category": "COMP", "uom": "EA", "cost": 85.00, "reorder": 100, "min": 50},
            {"code": "COMP-BEARING-01", "name": "Sealed Bearing Assembly", "category": "COMP", "uom": "EA", "cost": 320.00, "reorder": 50, "min": 20},
            # Finished Goods
            {"code": "FG-BIT-812", "name": "PDC Bit 8-1/2\" Matrix Body", "category": "FG", "uom": "EA", "cost": 15000.00, "reorder": 5, "min": 2},
            {"code": "FG-BIT-614", "name": "PDC Bit 6-1/4\" Steel Body", "category": "FG", "uom": "EA", "cost": 8500.00, "reorder": 8, "min": 3},
            {"code": "FG-BIT-1214", "name": "PDC Bit 12-1/4\" Matrix Body", "category": "FG", "uom": "EA", "cost": 25000.00, "reorder": 3, "min": 1},
            # Consumables
            {"code": "CONS-COOLANT-01", "name": "Cutting Coolant", "category": "CONS", "uom": "L", "cost": 12.50, "reorder": 200, "min": 100},
            {"code": "CONS-ABRASIVE-01", "name": "Abrasive Compound Fine", "category": "CONS", "uom": "KG", "cost": 35.00, "reorder": 50, "min": 25},
            {"code": "CONS-FLUX-01", "name": "Brazing Flux Type B", "category": "CONS", "uom": "KG", "cost": 28.00, "reorder": 30, "min": 15},
            # Spare Parts
            {"code": "SPARE-SEAL-01", "name": "O-Ring Seal Kit", "category": "SPARE", "uom": "SET", "cost": 45.00, "reorder": 100, "min": 50},
            {"code": "SPARE-FILTER-01", "name": "Hydraulic Filter Element", "category": "SPARE", "uom": "EA", "cost": 65.00, "reorder": 30, "min": 15},
            # Tools
            {"code": "TOOL-GAGE-01", "name": "Cutter Pocket Gauge Set", "category": "TOOL", "uom": "SET", "cost": 850.00, "reorder": 5, "min": 2},
            {"code": "TOOL-TORQUE-01", "name": "Torque Wrench 100-500 Nm", "category": "TOOL", "uom": "EA", "cost": 450.00, "reorder": 3, "min": 1},
        ]
        items = {}
        for item_data in items_data:
            item, created = InventoryItem.objects.get_or_create(
                code=item_data["code"],
                defaults={
                    "name": item_data["name"],
                    "category": categories.get(item_data["category"]),
                    "uom": uoms.get(item_data["uom"]),
                    "standard_cost": Decimal(str(item_data["cost"])),
                    "reorder_point": item_data["reorder"],
                    "min_stock": item_data["min"],
                    "is_active": True,
                }
            )
            items[item_data["code"]] = item
            if created:
                self.stdout.write(f"    Created: {item.name}")

        # =====================================================
        # 6. CREATE INVENTORY STOCK RECORDS
        # =====================================================
        self.stdout.write("  Creating stock records...")
        stock_data = [
            {"item": "RM-TUNGSTEN-01", "location": "WH-MAIN-A1", "qty": 75.5},
            {"item": "RM-STEEL-01", "location": "WH-MAIN-A1", "qty": 350.0},
            {"item": "RM-COPPER-01", "location": "WH-MAIN-A2", "qty": 45.0},
            {"item": "COMP-PDC-8MM", "location": "WH-MAIN-B1", "qty": 850},
            {"item": "COMP-PDC-13MM", "location": "WH-MAIN-B1", "qty": 620},
            {"item": "COMP-PDC-16MM", "location": "WH-MAIN-B1", "qty": 380},
            {"item": "COMP-NOZZLE-01", "location": "WH-PROD-01", "qty": 145},
            {"item": "COMP-BEARING-01", "location": "WH-PROD-01", "qty": 68},
            {"item": "FG-BIT-812", "location": "WH-SHIP-01", "qty": 12},
            {"item": "FG-BIT-614", "location": "WH-SHIP-01", "qty": 18},
            {"item": "FG-BIT-1214", "location": "WH-SHIP-01", "qty": 6},
            {"item": "CONS-COOLANT-01", "location": "WH-PROD-02", "qty": 350},
            {"item": "CONS-ABRASIVE-01", "location": "WH-PROD-02", "qty": 85},
            {"item": "SPARE-SEAL-01", "location": "WH-MAIN-A2", "qty": 180},
            {"item": "TOOL-GAGE-01", "location": "WH-PROD-01", "qty": 8},
        ]
        for stock_rec in stock_data:
            item = items.get(stock_rec["item"])
            loc = locations.get(stock_rec["location"])
            if item and loc:
                stock, created = InventoryStock.objects.get_or_create(
                    item=item, location=loc,
                    defaults={
                        "quantity_on_hand": Decimal(str(stock_rec["qty"])),
                        "quantity_available": Decimal(str(stock_rec["qty"])),
                    }
                )

        # =====================================================
        # 7. CREATE STOCK BALANCES (Ledger-based)
        # =====================================================
        self.stdout.write("  Creating stock balances...")
        ardt_party = parties.get("ARDT")
        owned_type = ownership_types.get("OWNED")
        avail_status = quality_statuses.get("AVL") or quality_statuses.get("REL")
        new_condition = condition_types.get("NEW")

        for stock_rec in stock_data[:10]:
            item = items.get(stock_rec["item"])
            loc = locations.get(stock_rec["location"])
            if item and loc:
                StockBalance.objects.get_or_create(
                    item=item,
                    location=loc,
                    lot=None,
                    owner_party=ardt_party,
                    defaults={
                        "ownership_type": owned_type,
                        "condition": new_condition,
                        "quality_status": avail_status,
                        "qty_on_hand": Decimal(str(stock_rec["qty"])),
                        "qty_reserved": Decimal("0"),
                        "qty_available": Decimal(str(stock_rec["qty"])),
                        "avg_unit_cost": item.standard_cost or Decimal("0"),
                        "total_cost": Decimal(str(stock_rec["qty"])) * (item.standard_cost or Decimal("0")),
                    }
                )

        # =====================================================
        # 8. CREATE GOODS RECEIPT NOTES
        # =====================================================
        self.stdout.write("  Creating GRNs...")
        from apps.supplychain.models import Supplier
        supplier, _ = Supplier.objects.get_or_create(
            code="SUP-001",
            defaults={"name": "Baker Hughes Supply Co.", "is_active": True}
        )

        # Get ownership type for GRNs
        owned_type = ownership_types.get("OWNED") or list(ownership_types.values())[0] if ownership_types else None

        for i in range(1, 6):
            grn, created = GoodsReceiptNote.objects.get_or_create(
                grn_number=f"GRN-2024-{i:04d}",
                defaults={
                    "receipt_date": timezone.now().date() - timedelta(days=random.randint(1, 60)),
                    "warehouse": warehouses.get("WH-MAIN"),
                    "supplier": supplier,
                    "receiving_location": locations.get("WH-RECV-01"),
                    "owner_party": ardt_party,
                    "ownership_type": owned_type,
                    "status": random.choice(["DRAFT", "CONFIRMED"]),
                    "notes": f"Test GRN {i}",
                    "created_by": admin_user,
                }
            )
            if created:
                # Add lines
                for j, item_code in enumerate(random.sample(list(items.keys())[:8], 3)):
                    item = items[item_code]
                    default_uom = uoms.get("EA") or list(uoms.values())[0] if uoms else None
                    default_condition = list(condition_types.values())[0] if condition_types else None
                    default_qs = list(quality_statuses.values())[0] if quality_statuses else None
                    if default_uom and default_condition and default_qs:
                        GRNLine.objects.create(
                            grn=grn,
                            line_number=j + 1,
                            item=item,
                            qty_expected=Decimal(str(random.randint(10, 100))),
                            qty_received=Decimal(str(random.randint(10, 100))),
                            uom=default_uom,
                            unit_cost=item.standard_cost or Decimal("10.00"),
                            location=locations.get("WH-MAIN-A1"),
                            condition=default_condition,
                            quality_status=default_qs,
                        )
                self.stdout.write(f"    Created: {grn.grn_number}")

        # =====================================================
        # 9. CREATE STOCK ISSUES
        # =====================================================
        self.stdout.write("  Creating stock issues...")
        # Use ardt_party already created in stock balance section
        default_party = ardt_party
        for i in range(1, 4):
            issue, created = StockIssue.objects.get_or_create(
                issue_number=f"ISS-2024-{i:04d}",
                defaults={
                    "issue_date": timezone.now().date() - timedelta(days=random.randint(1, 30)),
                    "issue_type": random.choice(["WO", "INTERNAL", "SALES"]),
                    "warehouse": warehouses.get("WH-MAIN"),
                    "default_location": locations.get("WH-MAIN-A1"),
                    "status": random.choice(["DRAFT", "ISSUED"]),
                    "notes": f"Test Issue {i}",
                    "created_by": admin_user,
                }
            )
            if created:
                for j, item_code in enumerate(random.sample(list(items.keys())[:8], 2)):
                    item = items[item_code]
                    loc = locations.get("WH-MAIN-A1")
                    # Get first available dimension types
                    default_uom = uoms.get("EA") or list(uoms.values())[0] if uoms else None
                    default_ownership = list(ownership_types.values())[0] if ownership_types else None
                    default_condition = list(condition_types.values())[0] if condition_types else None
                    default_qs = list(quality_statuses.values())[0] if quality_statuses else None
                    if default_uom and default_ownership and default_condition and default_qs:
                        StockIssueLine.objects.create(
                            issue=issue,
                            line_number=j + 1,
                            item=item,
                            qty_requested=Decimal(str(random.randint(5, 20))),
                            qty_issued=Decimal(str(random.randint(5, 20))),
                            uom=default_uom,
                            location=loc,
                            owner_party=default_party,
                            ownership_type=default_ownership,
                            condition=default_condition,
                            quality_status=default_qs,
                        )
                self.stdout.write(f"    Created: {issue.issue_number}")

        # =====================================================
        # 10. CREATE STOCK TRANSFERS
        # =====================================================
        self.stdout.write("  Creating stock transfers...")
        for i in range(1, 3):
            transfer, created = StockTransfer.objects.get_or_create(
                transfer_number=f"TRF-2024-{i:04d}",
                defaults={
                    "transfer_date": timezone.now().date() - timedelta(days=random.randint(1, 20)),
                    "from_warehouse": warehouses.get("WH-MAIN"),
                    "from_location": locations.get("WH-MAIN-A1"),
                    "to_warehouse": warehouses.get("WH-PROD"),
                    "to_location": locations.get("WH-PROD-01"),
                    "from_owner": default_party,
                    "status": random.choice(["DRAFT", "IN_TRANSIT", "COMPLETED"]),
                    "notes": f"Test Transfer {i}",
                    "created_by": admin_user,
                }
            )
            if created:
                for j, item_code in enumerate(random.sample(list(items.keys())[:6], 2)):
                    item = items[item_code]
                    default_uom = uoms.get("EA") or list(uoms.values())[0] if uoms else None
                    default_ownership = list(ownership_types.values())[0] if ownership_types else None
                    default_condition = list(condition_types.values())[0] if condition_types else None
                    default_qs = list(quality_statuses.values())[0] if quality_statuses else None
                    if default_uom and default_ownership and default_condition and default_qs:
                        StockTransferLine.objects.create(
                            transfer=transfer,
                            line_number=j + 1,
                            item=item,
                            qty_requested=Decimal(str(random.randint(10, 50))),
                            qty_shipped=Decimal(str(random.randint(10, 50))),
                            qty_received=Decimal(str(random.randint(10, 50))),
                            uom=default_uom,
                            ownership_type=default_ownership,
                            condition=default_condition,
                            from_quality_status=default_qs,
                        )
                self.stdout.write(f"    Created: {transfer.transfer_number}")

        # =====================================================
        # 11. CREATE STOCK ADJUSTMENTS
        # =====================================================
        self.stdout.write("  Creating stock adjustments...")
        # Get or create an adjustment reason
        reason_cc = adjustment_reasons.get("CC") or adjustment_reasons.get("CYCLE") or list(adjustment_reasons.values())[0] if adjustment_reasons else None
        if not reason_cc:
            reason_cc, _ = AdjustmentReason.objects.get_or_create(
                code="CC", defaults={"name": "Cycle Count", "is_active": True}
            )
        for i in range(1, 3):
            adj, created = StockAdjustment.objects.get_or_create(
                adjustment_number=f"ADJ-2024-{i:04d}",
                defaults={
                    "adjustment_date": timezone.now().date() - timedelta(days=random.randint(1, 15)),
                    "adjustment_type": "CYCLE",
                    "warehouse": warehouses.get("WH-MAIN"),
                    "location": locations.get("WH-MAIN-A1"),
                    "reason": reason_cc,
                    "status": random.choice(["DRAFT", "APPROVED", "POSTED"]),
                    "notes": f"Cycle count adjustment {i}",
                    "created_by": admin_user,
                }
            )
            if created:
                for j, item_code in enumerate(random.sample(list(items.keys())[:5], 2)):
                    item = items[item_code]
                    default_uom = uoms.get("EA") or list(uoms.values())[0] if uoms else None
                    default_ownership = list(ownership_types.values())[0] if ownership_types else None
                    default_condition = list(condition_types.values())[0] if condition_types else None
                    default_qs = list(quality_statuses.values())[0] if quality_statuses else None
                    if default_uom and default_ownership and default_condition and default_qs:
                        qty_sys = Decimal(str(random.randint(50, 100)))
                        qty_cnt = Decimal(str(random.randint(48, 102)))
                        StockAdjustmentLine.objects.create(
                            adjustment=adj,
                            line_number=j + 1,
                            item=item,
                            qty_system=qty_sys,
                            qty_counted=qty_cnt,
                            qty_adjustment=qty_cnt - qty_sys,
                            uom=default_uom,
                            owner_party=default_party,
                            ownership_type=default_ownership,
                            condition=default_condition,
                            quality_status=default_qs,
                        )
                self.stdout.write(f"    Created: {adj.adjustment_number}")

        # =====================================================
        # 12. CREATE ASSETS
        # =====================================================
        self.stdout.write("  Creating assets...")
        # Get default dimension types for assets
        default_condition = new_condition or list(condition_types.values())[0] if condition_types else None
        default_qs = avail_status or list(quality_statuses.values())[0] if quality_statuses else None
        default_ownership = owned_type or list(ownership_types.values())[0] if ownership_types else None
        default_owner = ardt_party or list(parties.values())[0] if parties else None

        if default_condition and default_qs and default_ownership and default_owner:
            for i in range(1, 6):
                item = items.get("FG-BIT-812") or list(items.values())[0]
                asset, created = Asset.objects.get_or_create(
                    serial_number=f"SN-2024-{i:05d}",
                    defaults={
                        "asset_tag": f"AST-{i:05d}",
                        "item": item,
                        "status": random.choice(["AVAILABLE", "IN_USE", "MAINTENANCE"]),
                        "current_location": locations.get("WH-SHIP-01"),
                        "owner_party": default_owner,
                        "ownership_type": default_ownership,
                        "condition": default_condition,
                        "quality_status": default_qs,
                        "acquisition_date": timezone.now().date() - timedelta(days=random.randint(30, 365)),
                        "acquisition_cost": item.standard_cost or Decimal("10000.00"),
                    }
                )
                if created:
                    self.stdout.write(f"    Created: {asset.serial_number}")
        else:
            self.stdout.write("    Skipped assets - missing dimension types")

        # =====================================================
        # 13. CREATE BILLS OF MATERIAL
        # =====================================================
        self.stdout.write("  Creating BOMs...")
        fg_item = items.get("FG-BIT-812")
        if fg_item:
            bom, created = BillOfMaterial.objects.get_or_create(
                bom_code="BOM-BIT812-001",
                defaults={
                    "name": "PDC Bit 8-1/2\" Standard BOM",
                    "parent_item": fg_item,
                    "version": "1.0",
                    "status": "ACTIVE",
                    "bom_type": "PRODUCTION",
                    "base_quantity": Decimal("1"),
                    "uom": uoms.get("EA"),
                    "created_by": admin_user,
                }
            )
            if created:
                components = [
                    ("COMP-PDC-13MM", 48),
                    ("COMP-PDC-16MM", 12),
                    ("COMP-NOZZLE-01", 6),
                    ("COMP-BEARING-01", 1),
                    ("RM-TUNGSTEN-01", 15),
                ]
                for ln, (comp_code, qty) in enumerate(components, 1):
                    comp = items.get(comp_code)
                    if comp:
                        BOMLine.objects.create(
                            bom=bom,
                            line_number=ln,
                            component_item=comp,
                            quantity_per=Decimal(str(qty)),
                            uom=comp.uom or uoms.get("EA"),
                        )
                self.stdout.write(f"    Created: {bom.bom_code}")

        # =====================================================
        # 14. CREATE STOCK RESERVATIONS
        # =====================================================
        self.stdout.write("  Creating reservations...")
        default_uom = uoms.get("EA") or list(uoms.values())[0] if uoms else None
        if default_uom:
            for i in range(1, 4):
                item = list(items.values())[i]
                res, created = StockReservation.objects.get_or_create(
                    reservation_number=f"RES-2024-{i:04d}",
                    defaults={
                        "reservation_type": "WO",
                        "status": "PENDING",
                        "item": item,
                        "uom": item.uom or default_uom,
                        "qty_reserved": Decimal(str(random.randint(5, 25))),
                        "required_date": timezone.now().date() + timedelta(days=random.randint(7, 30)),
                        "created_by": admin_user,
                    }
                )
                if created:
                    self.stdout.write(f"    Created: {res.reservation_number}")
        else:
            self.stdout.write("    Skipped reservations - no UOM available")

        # =====================================================
        # 15. CREATE CYCLE COUNT PLANS
        # =====================================================
        self.stdout.write("  Creating cycle count plans...")
        plan, created = CycleCountPlan.objects.get_or_create(
            plan_code="CCP-2024-001",
            defaults={
                "name": "Monthly High-Value Items Count",
                "plan_type": "ABC",
                "status": "ACTIVE",
                "warehouse": warehouses.get("WH-MAIN"),
                "start_date": timezone.now().date(),
                "count_frequency_a": 30,
                "count_frequency_b": 60,
                "count_frequency_c": 90,
                "created_by": admin_user,
            }
        )
        if created:
            self.stdout.write(f"    Created: {plan.plan_code}")

        # =====================================================
        # SUMMARY
        # =====================================================
        self.stdout.write(self.style.SUCCESS("\nInventory Test Data Summary:"))
        self.stdout.write(f"  Warehouses: {Warehouse.objects.count()}")
        self.stdout.write(f"  Locations: {InventoryLocation.objects.count()}")
        self.stdout.write(f"  Items: {InventoryItem.objects.count()}")
        self.stdout.write(f"  Stock Records: {InventoryStock.objects.count()}")
        self.stdout.write(f"  Stock Balances: {StockBalance.objects.count()}")
        self.stdout.write(f"  GRNs: {GoodsReceiptNote.objects.count()}")
        self.stdout.write(f"  Stock Issues: {StockIssue.objects.count()}")
        self.stdout.write(f"  Transfers: {StockTransfer.objects.count()}")
        self.stdout.write(f"  Adjustments: {StockAdjustment.objects.count()}")
        self.stdout.write(f"  Assets: {Asset.objects.count()}")
        self.stdout.write(f"  BOMs: {BillOfMaterial.objects.count()}")
        self.stdout.write(f"  Reservations: {StockReservation.objects.count()}")
        self.stdout.write(f"  Cycle Count Plans: {CycleCountPlan.objects.count()}")
        self.stdout.write(self.style.SUCCESS("\nDone!"))
