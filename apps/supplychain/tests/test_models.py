"""
Supplychain App - Model Tests
Comprehensive tests for supply chain and finance models.

Tests cover:
- Vendor management (Vendor, VendorContact)
- Purchasing (PurchaseRequisition, PurchaseOrder, PurchaseOrderLine)
- Receiving (Receipt, ReceiptLine)
- Invoicing (VendorInvoice, InvoiceLine, InvoiceMatch)
- Finance (CostAllocation, PaymentTerm, VendorPayment)
- Legacy models (Supplier, CAPA)
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.supplychain.models import (
    Vendor, VendorContact, PurchaseRequisition, PurchaseRequisitionLine,
    PurchaseOrder, PurchaseOrderLine, Receipt, ReceiptLine,
    VendorInvoice, InvoiceLine, InvoiceMatch,
    CostAllocation, ExpenseCategory, PaymentTerm, VendorPayment, PaymentAllocation,
    Supplier, CAPA
)

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def approver(db):
    """Create an approver user."""
    return User.objects.create_user(
        username='approver',
        email='approver@example.com',
        password='approvepass123',
        first_name='Approve',
        last_name='User'
    )


@pytest.fixture
def payment_term(db):
    """Create a payment term."""
    return PaymentTerm.objects.create(
        term_code='NET30',
        term_name='Net 30 Days',
        due_days=30,
        discount_days=10,
        discount_percent=Decimal('2.00')
    )


@pytest.fixture
def vendor(db, user, payment_term):
    """Create a test vendor."""
    return Vendor.objects.create(
        name='Test Vendor Inc.',
        vendor_type=Vendor.VendorType.MATERIALS_SUPPLIER,
        status=Vendor.Status.ACTIVE,
        qualification_level=Vendor.QualificationLevel.STANDARD,
        address_line_1='123 Test Street',
        city='Test City',
        phone='+1-555-1234',
        email='vendor@testvendor.com',
        default_payment_term=payment_term,
        created_by=user
    )


@pytest.fixture
def vendor_contact(db, vendor, user):
    """Create a vendor contact."""
    return VendorContact.objects.create(
        vendor=vendor,
        first_name='John',
        last_name='Contact',
        contact_type=VendorContact.ContactType.SALES,
        email='john@testvendor.com',
        phone='+1-555-5678',
        is_primary=True,
        created_by=user
    )


@pytest.fixture
def purchase_requisition(db, user):
    """Create a purchase requisition."""
    return PurchaseRequisition.objects.create(
        requested_by=user,
        department='Manufacturing',
        title='Raw Materials Request',
        description='Request for steel plates',
        request_date=date.today(),
        required_date=date.today() + timedelta(days=14)
    )


@pytest.fixture
def purchase_order(db, vendor, user):
    """Create a purchase order."""
    return PurchaseOrder.objects.create(
        vendor=vendor,
        order_type=PurchaseOrder.OrderType.STANDARD,
        order_date=date.today(),
        required_date=date.today() + timedelta(days=14),
        created_by=user
    )


@pytest.fixture
def expense_category(db):
    """Create an expense category."""
    return ExpenseCategory.objects.create(
        category_code='MAT',
        category_name='Materials',
        gl_account_code='5000',
        is_billable=True
    )


# =============================================================================
# VENDOR MODEL TESTS
# =============================================================================

class TestVendorModel:
    """Tests for the Vendor model."""

    def test_create_vendor(self, db, user):
        """Test creating a vendor."""
        vendor = Vendor.objects.create(
            name='New Vendor',
            address_line_1='456 Vendor St',
            city='Vendor City',
            phone='+1-555-0000',
            email='new@vendor.com',
            created_by=user
        )
        assert vendor.pk is not None
        assert vendor.vendor_code.startswith('VEND-')
        assert vendor.status == Vendor.Status.PROSPECT

    def test_vendor_str(self, vendor):
        """Test the __str__ method."""
        assert vendor.name in str(vendor)

    def test_vendor_unique_code(self, vendor, user):
        """Test that vendor_code must be unique."""
        with pytest.raises(IntegrityError):
            Vendor.objects.create(
                vendor_code=vendor.vendor_code,  # Duplicate
                name='Another Vendor',
                address_line_1='789 Test St',
                city='Test City',
                phone='+1-555-9999',
                email='another@vendor.com',
                created_by=user
            )

    def test_vendor_auto_code_generation(self, db, user):
        """Test automatic vendor code generation."""
        vendor1 = Vendor.objects.create(
            name='Vendor 1',
            address_line_1='Test',
            city='Test',
            phone='123',
            email='v1@test.com',
            created_by=user
        )
        vendor2 = Vendor.objects.create(
            name='Vendor 2',
            address_line_1='Test',
            city='Test',
            phone='456',
            email='v2@test.com',
            created_by=user
        )
        # Vendor codes should be sequential
        assert vendor1.vendor_code != vendor2.vendor_code

    def test_vendor_status_choices(self, db, user):
        """Test all valid status choices."""
        for status_code, status_name in Vendor.Status.choices:
            vendor = Vendor.objects.create(
                name=f'Vendor {status_code}',
                status=status_code,
                address_line_1='Test',
                city='Test',
                phone='123',
                email=f'{status_code}@test.com',
                created_by=user
            )
            assert vendor.status == status_code

    def test_vendor_qualification_level(self, vendor):
        """Test vendor qualification level."""
        assert vendor.qualification_level == Vendor.QualificationLevel.STANDARD
        assert vendor.is_qualified is True

    def test_vendor_qualify_method(self, vendor, user):
        """Test vendor qualification method."""
        vendor.status = Vendor.Status.PROSPECT
        vendor.qualification_level = Vendor.QualificationLevel.NOT_QUALIFIED
        vendor.save()

        expiry = date.today() + timedelta(days=365)
        vendor.qualify(
            level=Vendor.QualificationLevel.PREFERRED,
            user=user,
            notes='Quality audit passed',
            expiry_date=expiry
        )

        vendor.refresh_from_db()
        assert vendor.qualification_level == Vendor.QualificationLevel.PREFERRED
        assert vendor.qualification_expiry_date == expiry
        assert vendor.qualified_by == user

    def test_vendor_activate_method(self, vendor):
        """Test vendor activation."""
        vendor.status = Vendor.Status.QUALIFIED
        vendor.save()

        vendor.activate()

        vendor.refresh_from_db()
        assert vendor.status == Vendor.Status.ACTIVE
        assert vendor.active_since is not None

    def test_vendor_suspend_method(self, vendor):
        """Test vendor suspension."""
        vendor.suspend('Payment issues')

        vendor.refresh_from_db()
        assert vendor.status == Vendor.Status.SUSPENDED
        assert 'Payment' in vendor.suspension_reason

    def test_vendor_properties(self, vendor):
        """Test vendor properties."""
        assert vendor.is_active is True
        assert vendor.is_qualified is True
        assert vendor.can_receive_orders is True


# =============================================================================
# VENDOR CONTACT MODEL TESTS
# =============================================================================

class TestVendorContactModel:
    """Tests for the VendorContact model."""

    def test_create_contact(self, vendor, user):
        """Test creating a vendor contact."""
        contact = VendorContact.objects.create(
            vendor=vendor,
            first_name='Jane',
            last_name='Doe',
            email='jane@vendor.com',
            phone='+1-555-1111',
            created_by=user
        )
        assert contact.pk is not None

    def test_contact_str(self, vendor_contact):
        """Test the __str__ method."""
        assert 'John Contact' in str(vendor_contact)

    def test_contact_full_name(self, vendor_contact):
        """Test full_name property."""
        assert vendor_contact.full_name == 'John Contact'

    def test_contact_make_primary(self, vendor, user):
        """Test making a contact primary."""
        contact1 = VendorContact.objects.create(
            vendor=vendor,
            first_name='Contact',
            last_name='One',
            email='c1@vendor.com',
            phone='111',
            is_primary=True,
            created_by=user
        )
        contact2 = VendorContact.objects.create(
            vendor=vendor,
            first_name='Contact',
            last_name='Two',
            email='c2@vendor.com',
            phone='222',
            is_primary=False,
            created_by=user
        )

        contact2.make_primary()

        contact1.refresh_from_db()
        contact2.refresh_from_db()
        assert contact1.is_primary is False
        assert contact2.is_primary is True


# =============================================================================
# PURCHASE REQUISITION MODEL TESTS
# =============================================================================

class TestPurchaseRequisitionModel:
    """Tests for the PurchaseRequisition model."""

    def test_create_requisition(self, db, user):
        """Test creating a purchase requisition."""
        pr = PurchaseRequisition.objects.create(
            requested_by=user,
            department='Production',
            title='Materials Request',
            description='Need materials',
            request_date=date.today(),
            required_date=date.today() + timedelta(days=7)
        )
        assert pr.pk is not None
        assert pr.requisition_number.startswith('REQ-')
        assert pr.status == PurchaseRequisition.Status.DRAFT

    def test_requisition_str(self, purchase_requisition):
        """Test the __str__ method."""
        assert purchase_requisition.title in str(purchase_requisition)

    def test_requisition_submit(self, purchase_requisition):
        """Test submitting a requisition."""
        purchase_requisition.submit()

        purchase_requisition.refresh_from_db()
        assert purchase_requisition.status == PurchaseRequisition.Status.SUBMITTED
        assert purchase_requisition.submitted_at is not None

    def test_requisition_approve(self, purchase_requisition, approver):
        """Test approving a requisition."""
        purchase_requisition.status = PurchaseRequisition.Status.SUBMITTED
        purchase_requisition.save()

        purchase_requisition.approve(approver, 'Approved')

        purchase_requisition.refresh_from_db()
        assert purchase_requisition.status == PurchaseRequisition.Status.APPROVED
        assert purchase_requisition.approved_by == approver

    def test_requisition_reject(self, purchase_requisition, approver):
        """Test rejecting a requisition."""
        purchase_requisition.status = PurchaseRequisition.Status.SUBMITTED
        purchase_requisition.save()

        purchase_requisition.reject(approver, 'Budget exceeded')

        purchase_requisition.refresh_from_db()
        assert purchase_requisition.status == PurchaseRequisition.Status.REJECTED
        assert 'Budget' in purchase_requisition.rejection_reason


# =============================================================================
# PURCHASE ORDER MODEL TESTS
# =============================================================================

class TestPurchaseOrderModel:
    """Tests for the PurchaseOrder model."""

    def test_create_purchase_order(self, vendor, user):
        """Test creating a purchase order."""
        po = PurchaseOrder.objects.create(
            vendor=vendor,
            order_date=date.today(),
            created_by=user
        )
        assert po.pk is not None
        assert po.po_number.startswith('PO-')
        assert po.status == PurchaseOrder.Status.DRAFT

    def test_purchase_order_str(self, purchase_order):
        """Test the __str__ method."""
        assert purchase_order.vendor.name in str(purchase_order)

    def test_purchase_order_totals(self, purchase_order):
        """Test PO totals calculation."""
        # Add lines
        PurchaseOrderLine.objects.create(
            purchase_order=purchase_order,
            line_number=1,
            item_description='Item 1',
            quantity_ordered=Decimal('10'),
            unit_of_measure='EA',
            unit_price=Decimal('100.00'),
            required_date=date.today() + timedelta(days=7)
        )
        PurchaseOrderLine.objects.create(
            purchase_order=purchase_order,
            line_number=2,
            item_description='Item 2',
            quantity_ordered=Decimal('5'),
            unit_of_measure='EA',
            unit_price=Decimal('50.00'),
            required_date=date.today() + timedelta(days=7)
        )

        purchase_order.calculate_totals()

        purchase_order.refresh_from_db()
        assert purchase_order.subtotal_amount == Decimal('1250.00')


# =============================================================================
# RECEIPT MODEL TESTS
# =============================================================================

class TestReceiptModel:
    """Tests for the Receipt model."""

    def test_create_receipt(self, purchase_order, vendor, user):
        """Test creating a receipt."""
        receipt = Receipt.objects.create(
            purchase_order=purchase_order,
            vendor=vendor,
            receipt_date=date.today(),
            received_by=user
        )
        assert receipt.pk is not None
        assert receipt.receipt_number.startswith('RCP-')
        assert receipt.status == Receipt.Status.DRAFT

    def test_receipt_str(self, purchase_order, vendor, user):
        """Test the __str__ method."""
        receipt = Receipt.objects.create(
            purchase_order=purchase_order,
            vendor=vendor,
            receipt_date=date.today(),
            received_by=user
        )
        assert purchase_order.po_number in str(receipt)


# =============================================================================
# VENDOR INVOICE MODEL TESTS
# =============================================================================

class TestVendorInvoiceModel:
    """Tests for the VendorInvoice model."""

    def test_create_invoice(self, vendor, purchase_order, user):
        """Test creating a vendor invoice."""
        invoice = VendorInvoice.objects.create(
            vendor=vendor,
            vendor_invoice_number='INV-001',
            purchase_order=purchase_order,
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            received_date=date.today(),
            subtotal_amount=Decimal('1000.00'),
            total_amount=Decimal('1000.00'),
            created_by=user
        )
        assert invoice.pk is not None
        assert invoice.invoice_number.startswith('INV-')
        assert invoice.status == VendorInvoice.Status.PENDING

    def test_invoice_amount_outstanding(self, vendor, purchase_order, user):
        """Test amount_outstanding property."""
        invoice = VendorInvoice.objects.create(
            vendor=vendor,
            vendor_invoice_number='INV-002',
            purchase_order=purchase_order,
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            received_date=date.today(),
            subtotal_amount=Decimal('1000.00'),
            total_amount=Decimal('1000.00'),
            amount_paid=Decimal('400.00'),
            created_by=user
        )
        assert invoice.amount_outstanding == Decimal('600.00')

    def test_invoice_is_overdue(self, vendor, purchase_order, user):
        """Test is_overdue property."""
        invoice = VendorInvoice.objects.create(
            vendor=vendor,
            vendor_invoice_number='INV-003',
            purchase_order=purchase_order,
            invoice_date=date.today() - timedelta(days=45),
            due_date=date.today() - timedelta(days=15),
            received_date=date.today() - timedelta(days=45),
            subtotal_amount=Decimal('500.00'),
            total_amount=Decimal('500.00'),
            created_by=user
        )
        assert invoice.is_overdue is True


# =============================================================================
# PAYMENT TERM MODEL TESTS
# =============================================================================

class TestPaymentTermModel:
    """Tests for the PaymentTerm model."""

    def test_create_payment_term(self, db):
        """Test creating a payment term."""
        term = PaymentTerm.objects.create(
            term_code='NET45',
            term_name='Net 45 Days',
            due_days=45
        )
        assert term.pk is not None

    def test_payment_term_str(self, payment_term):
        """Test the __str__ method."""
        assert 'NET30' in str(payment_term)

    def test_calculate_due_date(self, payment_term):
        """Test due date calculation."""
        invoice_date = date.today()
        due_date = payment_term.calculate_due_date(invoice_date)
        expected = invoice_date + timedelta(days=30)
        assert due_date == expected


# =============================================================================
# VENDOR PAYMENT MODEL TESTS
# =============================================================================

class TestVendorPaymentModel:
    """Tests for the VendorPayment model."""

    def test_create_payment(self, vendor, user):
        """Test creating a vendor payment."""
        payment = VendorPayment.objects.create(
            vendor=vendor,
            payment_date=date.today(),
            payment_method=VendorPayment.PaymentMethod.WIRE_TRANSFER,
            payment_amount=Decimal('5000.00'),
            created_by=user
        )
        assert payment.pk is not None
        assert payment.payment_number.startswith('PAY-')
        assert payment.status == VendorPayment.Status.PENDING

    def test_payment_str(self, vendor, user):
        """Test the __str__ method."""
        payment = VendorPayment.objects.create(
            vendor=vendor,
            payment_date=date.today(),
            payment_method=VendorPayment.PaymentMethod.CHECK,
            payment_amount=Decimal('1000.00'),
            created_by=user
        )
        assert vendor.name in str(payment)


# =============================================================================
# COST ALLOCATION MODEL TESTS
# =============================================================================

class TestCostAllocationModel:
    """Tests for the CostAllocation model."""

    def test_create_cost_allocation(self, expense_category, user):
        """Test creating a cost allocation."""
        allocation = CostAllocation.objects.create(
            cost_type=CostAllocation.CostType.MATERIAL,
            description='Material cost for job',
            cost_amount=Decimal('500.00'),
            expense_category=expense_category,
            cost_date=date.today(),
            created_by=user
        )
        assert allocation.pk is not None
        assert allocation.allocation_number.startswith('COST-')


# =============================================================================
# LEGACY MODEL TESTS
# =============================================================================

class TestLegacyModels:
    """Tests for legacy models (Supplier, CAPA)."""

    def test_create_supplier(self, db):
        """Test creating a legacy supplier."""
        supplier = Supplier.objects.create(
            code='SUP-001',
            name='Legacy Supplier'
        )
        assert supplier.pk is not None
        assert supplier.is_active is True

    def test_supplier_str(self, db):
        """Test supplier __str__ method."""
        supplier = Supplier.objects.create(
            code='SUP-002',
            name='Test Supplier'
        )
        assert 'SUP-002' in str(supplier)

    def test_create_capa(self, db, user):
        """Test creating a CAPA."""
        capa = CAPA.objects.create(
            title='Test CAPA',
            description='Test corrective action',
            assigned_to=user
        )
        assert capa.pk is not None
        assert capa.capa_number.startswith('CAPA-')
        assert capa.status == CAPA.Status.OPEN


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestSupplychainEdgeCases:
    """Edge case tests for supplychain models."""

    def test_vendor_with_many_orders(self, vendor, user):
        """Test vendor with multiple purchase orders."""
        for i in range(5):
            PurchaseOrder.objects.create(
                vendor=vendor,
                order_date=date.today(),
                created_by=user
            )
        assert vendor.purchase_orders.count() == 5

    def test_po_line_quantity_tracking(self, purchase_order):
        """Test PO line quantity tracking."""
        line = PurchaseOrderLine.objects.create(
            purchase_order=purchase_order,
            line_number=1,
            item_description='Test Item',
            quantity_ordered=Decimal('100'),
            unit_of_measure='EA',
            unit_price=Decimal('10.00'),
            required_date=date.today() + timedelta(days=7)
        )
        assert line.quantity_outstanding == Decimal('100')
        assert line.is_fully_received is False

        line.quantity_received = Decimal('100')
        line.save()
        assert line.is_fully_received is True

    def test_special_characters_in_descriptions(self, vendor, user):
        """Test special characters in fields."""
        po = PurchaseOrder.objects.create(
            vendor=vendor,
            order_date=date.today(),
            special_instructions='Use "special" packaging & <handle with care>',
            created_by=user
        )
        assert '"special"' in po.special_instructions
        assert '&' in po.special_instructions
