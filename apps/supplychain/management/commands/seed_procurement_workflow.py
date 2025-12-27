"""
Seed command for Procurement Workflow Test Data.

Creates sample data for the full procurement workflow:
PR (Purchase Requisition) → PO (Purchase Order) → GRN (Goods Receipt Note)

Usage:
    python manage.py seed_procurement_workflow
    python manage.py seed_procurement_workflow --post-grn  # Also posts the GRN

This creates:
- 1 Vendor (if not exists)
- 2 Purchase Requisitions (1 approved, 1 draft)
- 2 Purchase Orders (1 sent, 1 draft)
- 2 GRNs (1 confirmed ready to post, 1 draft)
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = "Seed procurement workflow test data (PR → PO → GRN)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--post-grn',
            action='store_true',
            help='Also post the GRN to create stock ledger entries',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("Seeding Procurement Workflow Test Data")
        self.stdout.write("=" * 60)

        # Get admin user
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            admin = User.objects.first()
        if not admin:
            self.stdout.write(self.style.ERROR("No users found! Create a user first."))
            return

        self.stdout.write(f"Using user: {admin.username}")

        if options['clear']:
            self.clear_test_data()

        # Step 1: Ensure base data exists
        vendor = self.ensure_vendor()
        warehouse = self.ensure_warehouse()
        location = self.ensure_location(warehouse)
        items = self.ensure_items()
        owner_party = self.ensure_party()
        ownership_type = self.ensure_ownership_type()
        condition = self.ensure_condition()
        quality_status = self.ensure_quality_status()
        uom = self.ensure_uom()

        # Step 2: Create Purchase Requisitions
        pr1 = self.create_purchase_requisition(
            admin, items, "PR for PDC Cutters", approved=True
        )
        pr2 = self.create_purchase_requisition(
            admin, items[:2], "PR for Bearings (Draft)", approved=False
        )

        # Step 3: Create Purchase Orders
        po1 = self.create_purchase_order(
            admin, vendor, items, pr1, "Sent PO", sent=True
        )
        po2 = self.create_purchase_order(
            admin, vendor, items[:2], None, "Draft PO", sent=False
        )

        # Step 4: Create GRNs
        grn1 = self.create_grn(
            admin, po1, warehouse, location, owner_party, ownership_type,
            condition, quality_status, uom, "Ready GRN", confirmed=True
        )
        grn2 = self.create_grn(
            admin, po2, warehouse, location, owner_party, ownership_type,
            condition, quality_status, uom, "Draft GRN", confirmed=False
        )

        # Step 5: Optionally post the GRN
        if options['post_grn'] and grn1:
            self.post_grn(grn1, admin)

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("Procurement Workflow Data Created!"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"\nPurchase Requisitions:")
        self.stdout.write(f"  - {pr1.requisition_number if pr1 else 'N/A'} (Approved)")
        self.stdout.write(f"  - {pr2.requisition_number if pr2 else 'N/A'} (Draft)")
        self.stdout.write(f"\nPurchase Orders:")
        self.stdout.write(f"  - {po1.po_number if po1 else 'N/A'} (Sent to Vendor)")
        self.stdout.write(f"  - {po2.po_number if po2 else 'N/A'} (Draft)")
        self.stdout.write(f"\nGoods Receipt Notes:")
        self.stdout.write(f"  - {grn1.grn_number if grn1 else 'N/A'} (Confirmed)")
        self.stdout.write(f"  - {grn2.grn_number if grn2 else 'N/A'} (Draft)")

        self.stdout.write(self.style.SUCCESS("\nWorkflow paths to test:"))
        self.stdout.write("  1. Sidebar → Logistics → Purchasing → Requisitions")
        self.stdout.write("  2. Sidebar → Logistics → Purchasing → POs")
        self.stdout.write("  3. Sidebar → Logistics → Inv Documents → GRN")
        self.stdout.write("  4. Sidebar → Logistics → Master Data → Receipt Tolerances")
        self.stdout.write("  5. Sidebar → Logistics → Inv Documents → Variances")

    def clear_test_data(self):
        """Clear existing test data."""
        from apps.supplychain.models import PurchaseRequisition, PurchaseOrder
        from apps.inventory.models import GoodsReceiptNote, StockLedger, GRNLine

        self.stdout.write("\nClearing existing test data...")
        # First delete ledger entries that reference test GRNs
        test_grns = GoodsReceiptNote.objects.filter(notes__contains="[TEST]")
        test_grn_lines = GRNLine.objects.filter(grn__in=test_grns)
        StockLedger.objects.filter(grn_line__in=test_grn_lines).delete()
        # Now delete GRNs (lines will cascade)
        test_grns.delete()
        PurchaseOrder.objects.filter(internal_notes__contains="[TEST]").delete()
        PurchaseRequisition.objects.filter(description__contains="[TEST]").delete()
        self.stdout.write("  Done.")

    def ensure_vendor(self):
        """Ensure a test vendor exists."""
        from apps.supplychain.models import Vendor

        vendor, created = Vendor.objects.get_or_create(
            vendor_code="VEND-TEST-001",
            defaults={
                "name": "Test Supplier Inc.",
                "vendor_type": "SUPPLIER",
                "status": "APPROVED",
                "currency_code": "USD",
            }
        )
        if created:
            self.stdout.write(f"  Created Vendor: {vendor.name}")
        else:
            self.stdout.write(f"  Using Vendor: {vendor.name}")
        return vendor

    def ensure_warehouse(self):
        """Ensure a warehouse exists."""
        from apps.sales.models import Warehouse

        warehouse = Warehouse.objects.first()
        if not warehouse:
            warehouse = Warehouse.objects.create(
                code="WH-MAIN",
                name="Main Warehouse",
                is_active=True,
            )
            self.stdout.write(f"  Created Warehouse: {warehouse.name}")
        else:
            self.stdout.write(f"  Using Warehouse: {warehouse.name}")
        return warehouse

    def ensure_location(self, warehouse):
        """Ensure a receiving location exists."""
        from apps.inventory.models import InventoryLocation, LocationType

        location = InventoryLocation.objects.filter(warehouse=warehouse).first()
        if not location:
            # Ensure location type exists
            loc_type, _ = LocationType.objects.get_or_create(
                code="RECEIVING",
                defaults={"name": "Receiving Area", "is_active": True}
            )
            location = InventoryLocation.objects.create(
                code="RCV-01",
                name="Receiving Area",
                warehouse=warehouse,
                location_type=loc_type,
                is_active=True,
            )
            self.stdout.write(f"  Created Location: {location.name}")
        else:
            self.stdout.write(f"  Using Location: {location.name}")
        return location

    def ensure_items(self):
        """Ensure inventory items exist."""
        from apps.inventory.models import InventoryItem, InventoryCategory

        items = []
        category = InventoryCategory.objects.first()

        item_data = [
            ("TEST-CUT-001", "PDC Cutter 13mm Standard", Decimal("125.00")),
            ("TEST-BRG-001", "Bearing 6205-2RS", Decimal("25.00")),
            ("TEST-SEL-001", "Seal Kit Hydraulic", Decimal("85.00")),
        ]

        for code, name, cost in item_data:
            item, created = InventoryItem.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "category": category,
                    "item_type": "COMPONENT",
                    "unit": "EA",
                    "standard_cost": cost,
                    "is_active": True,
                }
            )
            items.append(item)
            if created:
                self.stdout.write(f"  Created Item: {item.code}")

        self.stdout.write(f"  Using {len(items)} inventory items")
        return items

    def ensure_party(self):
        """Ensure owner party exists."""
        from apps.inventory.models import Party

        party, created = Party.objects.get_or_create(
            code="ARDT",
            defaults={
                "name": "ARDT (Company)",
                "party_type": "INTERNAL",
                "can_own_stock": True,
                "is_active": True,
            }
        )
        if created:
            self.stdout.write(f"  Created Party: {party.name}")
        return party

    def ensure_ownership_type(self):
        """Ensure ownership type exists."""
        from apps.inventory.models import OwnershipType

        otype, created = OwnershipType.objects.get_or_create(
            code="OWNED",
            defaults={
                "name": "Company Owned",
                "description": "Stock owned by the company",
                "is_active": True,
            }
        )
        if created:
            self.stdout.write(f"  Created Ownership Type: {otype.name}")
        return otype

    def ensure_condition(self):
        """Ensure condition type exists."""
        from apps.inventory.models import ConditionType

        cond, created = ConditionType.objects.get_or_create(
            code="NEW",
            defaults={
                "name": "New",
                "description": "Brand new item",
                "is_active": True,
            }
        )
        if created:
            self.stdout.write(f"  Created Condition: {cond.name}")
        return cond

    def ensure_quality_status(self):
        """Ensure quality status exists."""
        from apps.inventory.models import QualityStatus

        qs, created = QualityStatus.objects.get_or_create(
            code="AVAIL",
            defaults={
                "name": "Available",
                "description": "Available for use",
                "is_active": True,
            }
        )
        if created:
            self.stdout.write(f"  Created Quality Status: {qs.name}")
        return qs

    def ensure_uom(self):
        """Ensure unit of measure exists."""
        from apps.inventory.models import UnitOfMeasure

        uom, created = UnitOfMeasure.objects.get_or_create(
            code="EA",
            defaults={
                "name": "Each",
                "is_active": True,
            }
        )
        if created:
            self.stdout.write(f"  Created UoM: {uom.name}")
        return uom

    def create_purchase_requisition(self, user, items, title, approved=False):
        """Create a purchase requisition with lines."""
        from apps.supplychain.models import PurchaseRequisition, PurchaseRequisitionLine

        try:
            pr = PurchaseRequisition.objects.create(
                title=title,
                description=f"[TEST] {title}",
                department="Operations",
                priority="MEDIUM",
                request_date=timezone.now().date(),
                required_date=timezone.now().date() + timedelta(days=14),
                status="APPROVED" if approved else "DRAFT",
                requested_by=user,
                approved_by=user if approved else None,
                approved_at=timezone.now() if approved else None,
            )

            for i, item in enumerate(items, 1):
                PurchaseRequisitionLine.objects.create(
                    requisition=pr,
                    line_number=i,
                    item_description=item.name,
                    quantity_requested=Decimal("10"),
                    unit_of_measure=item.unit,
                    estimated_unit_price=item.standard_cost,
                    inventory_item=item,
                )

            self.stdout.write(f"  Created PR: {pr.requisition_number} ({pr.get_status_display()})")
            return pr
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  PR creation failed: {e}"))
            return None

    def create_purchase_order(self, user, vendor, items, pr, description, sent=False):
        """Create a purchase order with lines."""
        from apps.supplychain.models import PurchaseOrder, PurchaseOrderLine

        try:
            status = "SENT" if sent else "DRAFT"
            po = PurchaseOrder.objects.create(
                vendor=vendor,
                order_type="STANDARD",
                order_date=timezone.now().date(),
                required_date=timezone.now().date() + timedelta(days=14),
                status=status,
                internal_notes=f"[TEST] {description}",
                created_by=user,
                approved_by=user if sent else None,
                approved_at=timezone.now() if sent else None,
                sent_to_vendor_at=timezone.now() if sent else None,
            )

            # Link to PR if provided - check if the field exists
            # PR to PO relationship may be through converted_to_po on the PR side
            if pr:
                pr.converted_to_po = po
                pr.status = "CONVERTED_TO_PO"
                pr.save()

            total = Decimal("0")
            for i, item in enumerate(items, 1):
                qty = Decimal("10")
                line_total = qty * item.standard_cost
                total += line_total

                PurchaseOrderLine.objects.create(
                    purchase_order=po,
                    line_number=i,
                    item_description=item.name,
                    inventory_item=item,
                    quantity_ordered=qty,
                    unit_of_measure=item.unit,
                    unit_price=item.standard_cost,
                    line_total=line_total,
                    required_date=timezone.now().date() + timedelta(days=14),
                )

            po.subtotal_amount = total
            po.total_amount = total
            po.save()

            self.stdout.write(f"  Created PO: {po.po_number} ({po.get_status_display()})")
            return po
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  PO creation failed: {e}"))
            return None

    def create_grn(self, user, po, warehouse, location, owner_party, ownership_type,
                   condition, quality_status, uom, description, confirmed=False):
        """Create a GRN from a PO."""
        from apps.inventory.models import GoodsReceiptNote, GRNLine

        try:
            status = "CONFIRMED" if confirmed else "DRAFT"
            grn = GoodsReceiptNote.objects.create(
                receipt_type="PURCHASE",
                status=status,
                purchase_order=po,
                vendor=po.vendor,
                warehouse=warehouse,
                receiving_location=location,
                receipt_date=timezone.now().date(),
                owner_party=owner_party,
                ownership_type=ownership_type,
                requires_qc=False,
                qc_status="NOT_REQUIRED",
                notes=f"[TEST] {description}",
                created_by=user,
                confirmed_by=user if confirmed else None,
            )

            # Create GRN lines from PO lines
            for i, po_line in enumerate(po.lines.all(), 1):
                # Simulate some variance for testing
                qty_expected = po_line.quantity_ordered
                qty_received = qty_expected  # Exact match

                GRNLine.objects.create(
                    grn=grn,
                    line_number=i,
                    item=po_line.inventory_item,
                    qty_expected=qty_expected,
                    qty_received=qty_received,
                    qty_accepted=qty_received,
                    uom=uom,
                    location=location,
                    condition=condition,
                    quality_status=quality_status,
                    unit_cost=po_line.unit_price,
                    total_cost=qty_received * po_line.unit_price,
                )

            self.stdout.write(f"  Created GRN: {grn.grn_number} ({grn.get_status_display()})")
            return grn
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  GRN creation failed: {e}"))
            import traceback
            traceback.print_exc()
            return None

    def post_grn(self, grn, user):
        """Post a GRN to create stock ledger entries."""
        from apps.inventory.models import StockLedger, InventoryStock
        from django.db.models import F

        self.stdout.write(f"\nPosting GRN: {grn.grn_number}...")

        try:
            for line in grn.lines.all():
                # Create stock ledger entry
                StockLedger.objects.create(
                    item=line.item,
                    location=line.location,
                    transaction_type="RECEIPT",
                    transaction_date=grn.receipt_date,
                    qty_delta=line.qty_received,
                    uom=line.uom,
                    unit_cost=line.unit_cost,
                    total_cost=line.total_cost,
                    reference_type="GRN",
                    reference_id=f"{grn.grn_number}-LINE-{line.line_number}",
                    grn_line=line,
                    condition=line.condition,
                    quality_status=line.quality_status,
                    owner_party=grn.owner_party,
                    ownership_type=grn.ownership_type,
                    notes=f"Receipt from {grn.grn_number}",
                    created_by=user,
                )

                # Update stock balance using raw update to avoid model save issues
                stock, created = InventoryStock.objects.get_or_create(
                    item=line.item,
                    location=line.location,
                    defaults={'quantity_on_hand': 0}
                )
                InventoryStock.objects.filter(pk=stock.pk).update(
                    quantity_on_hand=F('quantity_on_hand') + line.qty_received
                )

                line.is_posted = True
                line.posted_at = timezone.now()
                line.save()

            grn.status = "POSTED"
            grn.posted_date = timezone.now()
            grn.posted_by = user
            grn.save()

            self.stdout.write(self.style.SUCCESS(f"  GRN {grn.grn_number} posted successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Failed to post GRN: {e}"))
            import traceback
            traceback.print_exc()
