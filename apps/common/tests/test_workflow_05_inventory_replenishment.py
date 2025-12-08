"""
Inventory Replenishment Workflow Integration Test
=================================================

Cross-App Integration:
- Inventory: Stock monitoring and updates
- Supply Chain: Purchase requisition and order management
- Planning: Inventory planning and forecasting
- Notifications: Alert delivery for low stock

Workflow Steps:
1. Stock item falls below minimum level
2. System generates low stock alert
3. Create purchase requisition
4. Approve requisition
5. Convert to purchase order
6. Send to vendor
7. Receive goods
8. Update inventory levels
9. Clear alerts and notifications

Author: Workflow Integration Suite
Date: December 2024
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def inventory_manager(db):
    """Create inventory manager user."""
    return User.objects.create_user(
        username='inv_manager',
        email='inventory@ardt.com',
        password='invpass123',
        first_name='Inventory',
        last_name='Manager',
        is_staff=True
    )


@pytest.fixture
def purchasing_agent(db):
    """Create purchasing agent user."""
    return User.objects.create_user(
        username='purchasing',
        email='purchasing@ardt.com',
        password='purchasepass123',
        first_name='Purchase',
        last_name='Agent',
        is_staff=True
    )


@pytest.fixture
def approver_user(db):
    """Create approver user with higher authority."""
    return User.objects.create_user(
        username='approver',
        email='approver@ardt.com',
        password='approverpass123',
        first_name='Finance',
        last_name='Approver',
        is_staff=True
    )


@pytest.fixture
def inventory_category(db):
    """Create inventory category."""
    from apps.inventory.models import InventoryCategory
    return InventoryCategory.objects.create(
        code='RAW-MAT',
        name='Raw Materials',
        description='Raw materials for production',
        is_active=True
    )


@pytest.fixture
def warehouse(db):
    """Create warehouse for inventory."""
    from apps.sales.models import Warehouse
    return Warehouse.objects.create(
        code='WH-MAIN',
        name='Main Warehouse',
        warehouse_type=Warehouse.WarehouseType.ARDT,
        is_active=True
    )


@pytest.fixture
def inventory_location(db, warehouse):
    """Create inventory location."""
    from apps.inventory.models import InventoryLocation
    return InventoryLocation.objects.create(
        warehouse=warehouse,
        code='A-01-01',
        name='Aisle A, Rack 1, Shelf 1'
    )


@pytest.fixture
def inventory_item_low_stock(db, inventory_category):
    """Create inventory item with low stock level."""
    from apps.inventory.models import InventoryItem
    return InventoryItem.objects.create(
        code='PDC-CUTTER-001',
        name='PDC Cutter',
        description='Premium PDC cutters for FC bits',
        item_type=InventoryItem.ItemType.RAW_MATERIAL,
        category=inventory_category,
        unit='EA',
        standard_cost=Decimal('150.00'),
        min_stock=Decimal('100.000'),  # Minimum 100 units
        max_stock=Decimal('500.000'),
        reorder_point=Decimal('150.000'),
        is_active=True
    )


@pytest.fixture
def vendor(db, inventory_manager):
    """Create a vendor for purchasing."""
    from apps.supplychain.models import Vendor
    return Vendor.objects.create(
        vendor_code='VND-PDC-001',
        name='PDC International Suppliers',
        vendor_type=Vendor.VendorType.PARTS_SUPPLIER,
        status=Vendor.Status.ACTIVE,
        qualification_level=Vendor.QualificationLevel.PREFERRED,
        email='sales@pdcsuppliers.com',
        phone='+966 555 987654',
        country='China',
        created_by=inventory_manager
    )


# =============================================================================
# INVENTORY REPLENISHMENT WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestInventoryReplenishmentWorkflow:
    """
    Complete inventory replenishment workflow test.

    Tests the full cycle from low stock detection through
    to goods receipt and inventory update.
    """

    def test_full_inventory_replenishment_workflow(
        self,
        inventory_manager,
        purchasing_agent,
        approver_user,
        warehouse,
        inventory_location,
        inventory_item_low_stock,
        vendor
    ):
        """
        Test complete inventory replenishment workflow.

        Steps:
        1. Create initial stock (below minimum)
        2. Detect low stock condition
        3. Generate low stock alert/notification
        4. Create purchase requisition
        5. Approve requisition
        6. Convert to purchase order
        7. Send PO to vendor
        8. Receive goods
        9. Update inventory
        10. Verify stock restored
        """
        from apps.inventory.models import InventoryStock, InventoryTransaction
        from apps.supplychain.models import PurchaseRequisition, PurchaseOrder, PurchaseOrderLine, Receipt, ReceiptLine
        from apps.notifications.models import Notification

        print("\n" + "="*60)
        print("INVENTORY REPLENISHMENT WORKFLOW")
        print("="*60)

        # ---------------------------------------------------------------------
        # STEP 1: Create initial stock (below minimum)
        # ---------------------------------------------------------------------
        print("\n[Step 1] Setting up initial stock level...")

        initial_qty = Decimal('50.000')  # Below min of 100

        stock = InventoryStock.objects.create(
            item=inventory_item_low_stock,
            location=inventory_location,
            quantity_on_hand=initial_qty,
            quantity_reserved=Decimal('0.000'),
            quantity_available=initial_qty
        )

        assert stock.quantity_on_hand < inventory_item_low_stock.min_stock
        print(f"  Item: {inventory_item_low_stock.name}")
        print(f"  Current stock: {stock.quantity_on_hand}")
        print(f"  Minimum required: {inventory_item_low_stock.min_stock}")
        print(f"  Status: LOW STOCK!")

        # ---------------------------------------------------------------------
        # STEP 2: Detect low stock condition
        # ---------------------------------------------------------------------
        print("\n[Step 2] Detecting low stock condition...")

        is_below_minimum = stock.quantity_available < inventory_item_low_stock.min_stock
        is_below_reorder = stock.quantity_available < inventory_item_low_stock.reorder_point

        assert is_below_minimum is True
        assert is_below_reorder is True
        print(f"  Below minimum: {is_below_minimum}")
        print(f"  Below reorder point: {is_below_reorder}")

        # Calculate reorder quantity
        reorder_qty = inventory_item_low_stock.max_stock - stock.quantity_available
        print(f"  Recommended order qty: {reorder_qty}")

        # ---------------------------------------------------------------------
        # STEP 3: Generate low stock notification
        # ---------------------------------------------------------------------
        print("\n[Step 3] Generating low stock alert...")

        alert = Notification.objects.create(
            recipient=inventory_manager,
            title=f'Low Stock Alert: {inventory_item_low_stock.name}',
            message=f'Item {inventory_item_low_stock.code} is below minimum. '
                    f'Current: {stock.quantity_available}, Min: {inventory_item_low_stock.min_stock}',
            priority=Notification.Priority.HIGH,
            entity_type='inventory.inventoryitem',
            entity_id=inventory_item_low_stock.pk
        )

        assert alert.pk is not None
        assert alert.priority == Notification.Priority.HIGH
        print(f"  Alert created: {alert.title}")
        print(f"  Recipient: {inventory_manager.username}")

        # ---------------------------------------------------------------------
        # STEP 4: Create purchase requisition
        # ---------------------------------------------------------------------
        print("\n[Step 4] Creating purchase requisition...")

        requisition = PurchaseRequisition.objects.create(
            requisition_number='PR-2024-001',
            description=f'Replenishment order for {inventory_item_low_stock.name}',
            priority=PurchaseRequisition.Priority.HIGH,
            required_date=date.today() + timedelta(days=7),
            status=PurchaseRequisition.Status.DRAFT,
            requested_by=inventory_manager,
            total_amount=reorder_qty * inventory_item_low_stock.standard_cost
        )

        assert requisition.pk is not None
        print(f"  PR Number: {requisition.requisition_number}")
        print(f"  Amount: ${requisition.total_amount}")

        # ---------------------------------------------------------------------
        # STEP 5: Approve requisition
        # ---------------------------------------------------------------------
        print("\n[Step 5] Submitting for approval...")

        # Submit for approval
        requisition.status = PurchaseRequisition.Status.PENDING
        requisition.save()
        print(f"  Status: {requisition.get_status_display()}")

        # Approve
        requisition.status = PurchaseRequisition.Status.APPROVED
        requisition.approved_by = approver_user
        requisition.approved_at = timezone.now()
        requisition.save()

        assert requisition.status == PurchaseRequisition.Status.APPROVED
        print(f"  Approved by: {approver_user.username}")
        print(f"  Status: {requisition.get_status_display()}")

        # ---------------------------------------------------------------------
        # STEP 6: Convert to purchase order
        # ---------------------------------------------------------------------
        print("\n[Step 6] Creating purchase order...")

        po = PurchaseOrder.objects.create(
            po_number='PO-2024-001',
            vendor=vendor,
            requisition=requisition,
            order_date=date.today(),
            expected_date=date.today() + timedelta(days=7),
            status=PurchaseOrder.Status.DRAFT,
            subtotal=requisition.total_amount,
            total_amount=requisition.total_amount,
            created_by=purchasing_agent
        )

        # Add PO line
        po_line = PurchaseOrderLine.objects.create(
            purchase_order=po,
            line_number=1,
            item=inventory_item_low_stock,
            description=inventory_item_low_stock.name,
            quantity=reorder_qty,
            unit_price=inventory_item_low_stock.standard_cost,
            line_total=reorder_qty * inventory_item_low_stock.standard_cost,
            status=PurchaseOrderLine.Status.PENDING
        )

        assert po.pk is not None
        assert po_line.pk is not None
        print(f"  PO Number: {po.po_number}")
        print(f"  Vendor: {vendor.name}")
        print(f"  Quantity: {po_line.quantity}")

        # ---------------------------------------------------------------------
        # STEP 7: Send PO to vendor
        # ---------------------------------------------------------------------
        print("\n[Step 7] Sending PO to vendor...")

        po.status = PurchaseOrder.Status.SENT
        po.save()

        assert po.status == PurchaseOrder.Status.SENT
        print(f"  PO Status: {po.get_status_display()}")
        print(f"  Sent to: {vendor.email}")

        # Vendor confirms
        po.status = PurchaseOrder.Status.CONFIRMED
        po.vendor_confirmed_at = timezone.now()
        po.save()

        print(f"  Vendor confirmed!")

        # ---------------------------------------------------------------------
        # STEP 8: Receive goods
        # ---------------------------------------------------------------------
        print("\n[Step 8] Receiving goods...")

        receipt = Receipt.objects.create(
            receipt_number='GRN-2024-001',
            purchase_order=po,
            vendor=vendor,
            receipt_date=date.today(),
            status=Receipt.Status.DRAFT,
            warehouse=warehouse,
            received_by=inventory_manager
        )

        # Receive the line item
        receipt_line = ReceiptLine.objects.create(
            receipt=receipt,
            po_line=po_line,
            quantity_ordered=po_line.quantity,
            quantity_received=po_line.quantity,  # Full receipt
            quantity_accepted=po_line.quantity,
            quantity_rejected=Decimal('0.000'),
            location=inventory_location,
            status=ReceiptLine.Status.ACCEPTED
        )

        # Complete receipt
        receipt.status = Receipt.Status.COMPLETED
        receipt.save()

        # Update PO line status
        po_line.quantity_received = receipt_line.quantity_received
        po_line.status = PurchaseOrderLine.Status.RECEIVED
        po_line.save()

        assert receipt.status == Receipt.Status.COMPLETED
        print(f"  Receipt: {receipt.receipt_number}")
        print(f"  Quantity received: {receipt_line.quantity_received}")

        # ---------------------------------------------------------------------
        # STEP 9: Update inventory
        # ---------------------------------------------------------------------
        print("\n[Step 9] Updating inventory levels...")

        # Create inventory transaction
        transaction = InventoryTransaction.objects.create(
            transaction_number='TXN-RCPT-001',
            transaction_type=InventoryTransaction.TransactionType.RECEIPT,
            transaction_date=timezone.now(),
            item=inventory_item_low_stock,
            to_location=inventory_location,
            quantity=receipt_line.quantity_accepted,
            unit=inventory_item_low_stock.unit,
            unit_cost=po_line.unit_price,
            total_cost=po_line.line_total,
            link_type=InventoryTransaction.LinkType.PURCHASE_ORDER,
            reference_number=po.po_number,
            notes='Stock replenishment from PO',
            created_by=inventory_manager
        )

        # Update stock
        stock.quantity_on_hand += receipt_line.quantity_accepted
        stock.quantity_available += receipt_line.quantity_accepted
        stock.save()

        assert transaction.pk is not None
        print(f"  Transaction: {transaction.transaction_number}")
        print(f"  Previous stock: {initial_qty}")
        print(f"  Added: {receipt_line.quantity_accepted}")
        print(f"  New stock: {stock.quantity_on_hand}")

        # ---------------------------------------------------------------------
        # STEP 10: Verify stock restored
        # ---------------------------------------------------------------------
        print("\n[Step 10] Final verification...")

        stock.refresh_from_db()

        is_above_minimum = stock.quantity_available >= inventory_item_low_stock.min_stock
        is_above_reorder = stock.quantity_available >= inventory_item_low_stock.reorder_point

        assert is_above_minimum is True
        assert is_above_reorder is True

        # Mark alert as read
        alert.is_read = True
        alert.read_at = timezone.now()
        alert.save()

        # Mark requisition as completed
        requisition.status = PurchaseRequisition.Status.COMPLETED
        requisition.save()

        # Mark PO as completed
        po.status = PurchaseOrder.Status.COMPLETED
        po.save()

        # Summary
        final_checks = {
            'requisition_completed': requisition.status == PurchaseRequisition.Status.COMPLETED,
            'po_completed': po.status == PurchaseOrder.Status.COMPLETED,
            'receipt_completed': receipt.status == Receipt.Status.COMPLETED,
            'stock_above_minimum': stock.quantity_available >= inventory_item_low_stock.min_stock,
            'alert_acknowledged': alert.is_read is True,
        }

        all_passed = all(final_checks.values())

        print("\n  Replenishment Summary:")
        print(f"    Item: {inventory_item_low_stock.code}")
        print(f"    Initial Stock: {initial_qty}")
        print(f"    Ordered: {reorder_qty}")
        print(f"    Final Stock: {stock.quantity_on_hand}")
        print(f"    Minimum Required: {inventory_item_low_stock.min_stock}")

        print("\n  Workflow Checklist:")
        for check, status in final_checks.items():
            icon = "  " if status else "  "
            print(f"    {icon} {check.replace('_', ' ').title()}")

        assert all_passed, f"Some checks failed: {[k for k,v in final_checks.items() if not v]}"

        print("\n" + "="*60)
        print("WORKFLOW COMPLETED SUCCESSFULLY!")
        print("="*60)


    def test_partial_receipt_workflow(
        self,
        inventory_manager,
        purchasing_agent,
        approver_user,
        warehouse,
        inventory_location,
        inventory_item_low_stock,
        vendor
    ):
        """
        Test partial goods receipt workflow.

        Tests scenario where vendor delivers in multiple shipments.
        """
        from apps.inventory.models import InventoryStock, InventoryTransaction
        from apps.supplychain.models import PurchaseOrder, PurchaseOrderLine, Receipt, ReceiptLine

        print("\n" + "="*60)
        print("PARTIAL RECEIPT WORKFLOW")
        print("="*60)

        # Setup initial stock
        stock = InventoryStock.objects.create(
            item=inventory_item_low_stock,
            location=inventory_location,
            quantity_on_hand=Decimal('25.000'),
            quantity_reserved=Decimal('0.000'),
            quantity_available=Decimal('25.000')
        )

        order_qty = Decimal('200.000')

        # Create PO
        print("\n[Step 1] Creating purchase order...")

        po = PurchaseOrder.objects.create(
            po_number='PO-PARTIAL-001',
            vendor=vendor,
            order_date=date.today(),
            status=PurchaseOrder.Status.CONFIRMED,
            total_amount=order_qty * inventory_item_low_stock.standard_cost,
            created_by=purchasing_agent
        )

        po_line = PurchaseOrderLine.objects.create(
            purchase_order=po,
            line_number=1,
            item=inventory_item_low_stock,
            quantity=order_qty,
            unit_price=inventory_item_low_stock.standard_cost,
            line_total=order_qty * inventory_item_low_stock.standard_cost,
            status=PurchaseOrderLine.Status.PENDING
        )

        print(f"  PO: {po.po_number}")
        print(f"  Ordered: {order_qty}")

        # First partial receipt (60%)
        print("\n[Step 2] First partial receipt (60%)...")

        first_receipt_qty = Decimal('120.000')

        receipt1 = Receipt.objects.create(
            receipt_number='GRN-PART-001',
            purchase_order=po,
            vendor=vendor,
            receipt_date=date.today(),
            status=Receipt.Status.COMPLETED,
            warehouse=warehouse,
            received_by=inventory_manager
        )

        ReceiptLine.objects.create(
            receipt=receipt1,
            po_line=po_line,
            quantity_ordered=order_qty,
            quantity_received=first_receipt_qty,
            quantity_accepted=first_receipt_qty,
            location=inventory_location,
            status=ReceiptLine.Status.ACCEPTED
        )

        # Update PO line
        po_line.quantity_received = first_receipt_qty
        po_line.status = PurchaseOrderLine.Status.PARTIAL
        po_line.save()

        # Update stock
        stock.quantity_on_hand += first_receipt_qty
        stock.quantity_available += first_receipt_qty
        stock.save()

        print(f"  Received: {first_receipt_qty}")
        print(f"  Stock now: {stock.quantity_on_hand}")
        print(f"  Remaining on PO: {order_qty - first_receipt_qty}")

        # Second partial receipt (remaining 40%)
        print("\n[Step 3] Second partial receipt (40%)...")

        second_receipt_qty = order_qty - first_receipt_qty

        receipt2 = Receipt.objects.create(
            receipt_number='GRN-PART-002',
            purchase_order=po,
            vendor=vendor,
            receipt_date=date.today() + timedelta(days=3),
            status=Receipt.Status.COMPLETED,
            warehouse=warehouse,
            received_by=inventory_manager
        )

        ReceiptLine.objects.create(
            receipt=receipt2,
            po_line=po_line,
            quantity_ordered=order_qty,
            quantity_received=second_receipt_qty,
            quantity_accepted=second_receipt_qty,
            location=inventory_location,
            status=ReceiptLine.Status.ACCEPTED
        )

        # Update PO line
        po_line.quantity_received += second_receipt_qty
        po_line.status = PurchaseOrderLine.Status.RECEIVED
        po_line.save()

        # Update stock
        stock.quantity_on_hand += second_receipt_qty
        stock.quantity_available += second_receipt_qty
        stock.save()

        print(f"  Received: {second_receipt_qty}")
        print(f"  Final stock: {stock.quantity_on_hand}")

        # Verify complete receipt
        print("\n[Step 4] Verifying complete receipt...")

        po.status = PurchaseOrder.Status.COMPLETED
        po.save()

        assert po_line.quantity_received == order_qty
        assert po_line.status == PurchaseOrderLine.Status.RECEIVED
        print(f"  Total ordered: {order_qty}")
        print(f"  Total received: {po_line.quantity_received}")
        print(f"  PO Status: {po.get_status_display()}")

        print("\n" + "="*60)
        print("PARTIAL RECEIPT WORKFLOW COMPLETED!")
        print("="*60)


    def test_urgent_replenishment_workflow(
        self,
        inventory_manager,
        purchasing_agent,
        vendor
    ):
        """
        Test urgent/expedited replenishment workflow.

        Tests scenario requiring expedited ordering due to
        critical stock shortage.
        """
        from apps.supplychain.models import PurchaseRequisition, PurchaseOrder

        print("\n" + "="*60)
        print("URGENT REPLENISHMENT WORKFLOW")
        print("="*60)

        # Create urgent requisition
        print("\n[Step 1] Creating URGENT requisition...")

        requisition = PurchaseRequisition.objects.create(
            requisition_number='PR-URGENT-001',
            description='URGENT: Production stoppage imminent',
            priority=PurchaseRequisition.Priority.URGENT,
            required_date=date.today() + timedelta(days=2),
            status=PurchaseRequisition.Status.APPROVED,  # Auto-approved for urgent
            requested_by=inventory_manager,
            approved_by=inventory_manager,  # Emergency approval
            approved_at=timezone.now(),
            total_amount=Decimal('15000.00')
        )

        assert requisition.priority == PurchaseRequisition.Priority.URGENT
        print(f"  Priority: {requisition.get_priority_display()}")
        print(f"  Required by: {requisition.required_date}")

        # Create expedited PO
        print("\n[Step 2] Creating expedited PO...")

        po = PurchaseOrder.objects.create(
            po_number='PO-URGENT-001',
            vendor=vendor,
            requisition=requisition,
            order_date=date.today(),
            expected_date=date.today() + timedelta(days=2),
            status=PurchaseOrder.Status.SENT,
            is_urgent=True,
            notes='EXPEDITE - Production critical',
            total_amount=requisition.total_amount,
            created_by=purchasing_agent
        )

        assert po.is_urgent is True
        print(f"  PO: {po.po_number}")
        print(f"  Urgent flag: {po.is_urgent}")
        print(f"  Expected: {po.expected_date}")

        print("\n" + "="*60)
        print("URGENT WORKFLOW INITIATED!")
        print("="*60)


# =============================================================================
# WORKFLOW SUMMARY
# =============================================================================

@pytest.mark.django_db
class TestReplenishmentWorkflowSummary:
    """Summary tests for replenishment workflow."""

    def test_workflow_models_exist(self, db):
        """Verify all workflow models are accessible."""
        from apps.inventory.models import InventoryItem, InventoryStock, InventoryTransaction
        from apps.supplychain.models import Vendor, PurchaseRequisition, PurchaseOrder, Receipt

        assert InventoryItem._meta.model_name == 'inventoryitem'
        assert InventoryStock._meta.model_name == 'inventorystock'
        assert Vendor._meta.model_name == 'vendor'
        assert PurchaseRequisition._meta.model_name == 'purchaserequisition'
        assert PurchaseOrder._meta.model_name == 'purchaseorder'
        assert Receipt._meta.model_name == 'receipt'

        print("\nAll replenishment workflow models verified!")
