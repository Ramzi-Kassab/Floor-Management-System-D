"""
Sprint 6 Smoke Tests - Supply Chain & Finance Models

Quick validation tests to ensure basic model functionality works.
Tests: creation, __str__, auto-ID generation, one key relationship.

Week 1 Models - Vendor Management & Purchasing (6):
1. Vendor
2. VendorContact
3. PurchaseRequisition
4. PurchaseRequisitionLine
5. PurchaseOrder
6. PurchaseOrderLine

Week 2 Models - Receiving & Invoicing (5):
7. Receipt
8. ReceiptLine
9. VendorInvoice
10. InvoiceLine
11. InvoiceMatch

Week 3 Models - Costing & Finance (6):
12. ExpenseCategory
13. CostAllocation
14. PaymentTerm
15. VendorPayment
16. PaymentAllocation

Legacy Models (2):
17. Supplier
18. CAPA

Author: Sprint 6 Smoke Test Suite
Date: December 2024
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.supplychain.models import (
    # Week 1 models
    Vendor,
    VendorContact,
    PurchaseRequisition,
    PurchaseRequisitionLine,
    PurchaseOrder,
    PurchaseOrderLine,
    # Week 2 models
    Receipt,
    ReceiptLine,
    VendorInvoice,
    InvoiceLine,
    InvoiceMatch,
    # Week 3 models
    ExpenseCategory,
    CostAllocation,
    PaymentTerm,
    VendorPayment,
    PaymentAllocation,
    # Legacy models
    Supplier,
    CAPA,
)

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def user(db):
    """Create test user"""
    return User.objects.create_user(
        username='supplychain_test',
        password='testpass123',
        email='supplychain@test.com'
    )


@pytest.fixture
def payment_term(db):
    """Create test payment term"""
    return PaymentTerm.objects.create(
        term_code="NET30",
        term_name="Net 30 Days",
        due_days=30,
        discount_days=10,
        discount_percent=Decimal("2.00"),
        is_active=True
    )


@pytest.fixture
def vendor(db, payment_term):
    """Create test vendor"""
    return Vendor.objects.create(
        name="Test Vendor Inc",
        vendor_type=Vendor.VendorType.MATERIALS_SUPPLIER,
        status=Vendor.Status.ACTIVE,
        address_line_1="123 Vendor Street",
        city="Test City",
        country="Saudi Arabia",
        phone="+966-12-345-6789",
        email="vendor@test.com",
        default_payment_term=payment_term
    )


@pytest.fixture
def vendor_contact(db, vendor):
    """Create test vendor contact"""
    return VendorContact.objects.create(
        vendor=vendor,
        first_name="John",
        last_name="Smith",
        contact_type=VendorContact.ContactType.SALES,
        email="john.smith@test.com",
        phone="+966-12-345-6789",
        is_primary=True
    )


@pytest.fixture
def purchase_requisition(db, user):
    """Create test purchase requisition"""
    return PurchaseRequisition.objects.create(
        requested_by=user,
        title="Test Requisition",
        description="Test materials purchase",
        justification="Needed for project",
        priority=PurchaseRequisition.Priority.MEDIUM,
        request_date=date.today(),
        required_date=date.today() + timedelta(days=14)
    )


@pytest.fixture
def pr_line(db, purchase_requisition):
    """Create test PR line"""
    return PurchaseRequisitionLine.objects.create(
        requisition=purchase_requisition,
        line_number=1,
        item_description="Test Material",
        quantity_requested=Decimal("10.000"),
        unit_of_measure="EA",
        estimated_unit_price=Decimal("100.00")
    )


@pytest.fixture
def purchase_order(db, vendor, user):
    """Create test purchase order"""
    return PurchaseOrder.objects.create(
        vendor=vendor,
        order_type=PurchaseOrder.OrderType.STANDARD,
        status=PurchaseOrder.Status.APPROVED,
        order_date=date.today(),
        created_by=user
    )


@pytest.fixture
def po_line(db, purchase_order):
    """Create test PO line"""
    return PurchaseOrderLine.objects.create(
        purchase_order=purchase_order,
        line_number=1,
        item_description="Test Material",
        quantity_ordered=Decimal("10.000"),
        unit_of_measure="EA",
        unit_price=Decimal("100.0000"),
        required_date=date.today() + timedelta(days=14)
    )


@pytest.fixture
def receipt(db, purchase_order, vendor, user):
    """Create test receipt"""
    return Receipt.objects.create(
        purchase_order=purchase_order,
        vendor=vendor,
        receipt_type=Receipt.ReceiptType.GOODS,
        status=Receipt.Status.DRAFT,
        receipt_date=date.today(),
        received_by=user
    )


@pytest.fixture
def receipt_line(db, receipt, po_line):
    """Create test receipt line"""
    return ReceiptLine.objects.create(
        receipt=receipt,
        line_number=1,
        po_line=po_line,
        quantity_received=Decimal("10.000"),
        quantity_accepted=Decimal("10.000"),
        quantity_rejected=Decimal("0.000")
    )


@pytest.fixture
def vendor_invoice(db, vendor, purchase_order):
    """Create test vendor invoice"""
    return VendorInvoice.objects.create(
        vendor=vendor,
        vendor_invoice_number="INV-001",
        purchase_order=purchase_order,
        invoice_date=date.today(),
        received_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        subtotal_amount=Decimal("1000.00"),
        total_amount=Decimal("1000.00")
    )


@pytest.fixture
def invoice_line(db, vendor_invoice, po_line):
    """Create test invoice line"""
    return InvoiceLine.objects.create(
        vendor_invoice=vendor_invoice,
        line_number=1,
        description="Test Material",
        quantity=Decimal("10.000"),
        unit_price=Decimal("100.0000"),
        line_total=Decimal("1000.00"),
        po_line=po_line
    )


@pytest.fixture
def expense_category(db):
    """Create test expense category"""
    return ExpenseCategory.objects.create(
        category_code="MAT001",
        category_name="Materials",
        gl_account_code="5001",
        is_active=True
    )


@pytest.fixture
def supplier(db):
    """Create test supplier (legacy)"""
    return Supplier.objects.create(
        code="SUP001",
        name="Test Supplier",
        is_active=True
    )


# =============================================================================
# WEEK 1 TESTS: VENDOR MANAGEMENT & PURCHASING
# =============================================================================

class TestVendor:
    """Test Vendor model"""

    def test_create_vendor(self, vendor):
        """Test vendor creation"""
        assert vendor.pk is not None
        assert vendor.name == "Test Vendor Inc"
        assert vendor.status == Vendor.Status.ACTIVE

    def test_vendor_auto_code(self, vendor):
        """Test vendor auto-generated code"""
        assert vendor.vendor_code is not None
        assert vendor.vendor_code.startswith("VEND-")

    def test_vendor_str(self, vendor):
        """Test vendor string representation"""
        assert str(vendor) is not None
        assert len(str(vendor)) > 0

    def test_vendor_payment_term_relationship(self, vendor, payment_term):
        """Test vendor payment term relationship"""
        assert vendor.default_payment_term == payment_term


class TestVendorContact:
    """Test VendorContact model"""

    def test_create_vendor_contact(self, vendor_contact):
        """Test vendor contact creation"""
        assert vendor_contact.pk is not None
        assert vendor_contact.first_name == "John"
        assert vendor_contact.is_primary is True

    def test_vendor_contact_vendor_relationship(self, vendor_contact, vendor):
        """Test vendor contact relationship"""
        assert vendor_contact.vendor == vendor

    def test_vendor_contact_str(self, vendor_contact):
        """Test vendor contact string representation"""
        assert str(vendor_contact) is not None


class TestPurchaseRequisition:
    """Test PurchaseRequisition model"""

    def test_create_pr(self, purchase_requisition):
        """Test PR creation"""
        assert purchase_requisition.pk is not None
        assert purchase_requisition.title == "Test Requisition"
        assert purchase_requisition.status == PurchaseRequisition.Status.DRAFT

    def test_pr_auto_number(self, purchase_requisition):
        """Test PR auto-generated number"""
        assert purchase_requisition.requisition_number is not None
        assert "REQ-" in purchase_requisition.requisition_number

    def test_pr_str(self, purchase_requisition):
        """Test PR string representation"""
        assert str(purchase_requisition) is not None


class TestPurchaseRequisitionLine:
    """Test PurchaseRequisitionLine model"""

    def test_create_pr_line(self, pr_line):
        """Test PR line creation"""
        assert pr_line.pk is not None
        assert pr_line.item_description == "Test Material"
        assert pr_line.quantity_requested == Decimal("10.000")

    def test_pr_line_requisition_relationship(self, pr_line, purchase_requisition):
        """Test PR line relationship"""
        assert pr_line.requisition == purchase_requisition


class TestPurchaseOrder:
    """Test PurchaseOrder model"""

    def test_create_po(self, purchase_order):
        """Test PO creation"""
        assert purchase_order.pk is not None
        assert purchase_order.status == PurchaseOrder.Status.APPROVED

    def test_po_auto_number(self, purchase_order):
        """Test PO auto-generated number"""
        assert purchase_order.po_number is not None
        assert "PO-" in purchase_order.po_number

    def test_po_str(self, purchase_order):
        """Test PO string representation"""
        assert str(purchase_order) is not None

    def test_po_vendor_relationship(self, purchase_order, vendor):
        """Test PO vendor relationship"""
        assert purchase_order.vendor == vendor


class TestPurchaseOrderLine:
    """Test PurchaseOrderLine model"""

    def test_create_po_line(self, po_line):
        """Test PO line creation"""
        assert po_line.pk is not None
        assert po_line.item_description == "Test Material"
        assert po_line.quantity_ordered == Decimal("10.000")

    def test_po_line_order_relationship(self, po_line, purchase_order):
        """Test PO line relationship"""
        assert po_line.purchase_order == purchase_order


# =============================================================================
# WEEK 2 TESTS: RECEIVING & INVOICING
# =============================================================================

class TestReceipt:
    """Test Receipt model"""

    def test_create_receipt(self, receipt):
        """Test receipt creation"""
        assert receipt.pk is not None
        assert receipt.status == Receipt.Status.DRAFT

    def test_receipt_auto_number(self, receipt):
        """Test receipt auto-generated number"""
        assert receipt.receipt_number is not None
        assert "RCP-" in receipt.receipt_number

    def test_receipt_str(self, receipt):
        """Test receipt string representation"""
        assert str(receipt) is not None

    def test_receipt_po_relationship(self, receipt, purchase_order):
        """Test receipt PO relationship"""
        assert receipt.purchase_order == purchase_order


class TestReceiptLine:
    """Test ReceiptLine model"""

    def test_create_receipt_line(self, receipt_line):
        """Test receipt line creation"""
        assert receipt_line.pk is not None
        assert receipt_line.quantity_received == Decimal("10.000")

    def test_receipt_line_relationships(self, receipt_line, receipt, po_line):
        """Test receipt line relationships"""
        assert receipt_line.receipt == receipt
        assert receipt_line.po_line == po_line


class TestVendorInvoice:
    """Test VendorInvoice model"""

    def test_create_invoice(self, vendor_invoice):
        """Test invoice creation"""
        assert vendor_invoice.pk is not None
        assert vendor_invoice.vendor_invoice_number == "INV-001"

    def test_invoice_auto_number(self, vendor_invoice):
        """Test invoice auto-generated number"""
        assert vendor_invoice.invoice_number is not None
        assert "INV-" in vendor_invoice.invoice_number

    def test_invoice_str(self, vendor_invoice):
        """Test invoice string representation"""
        assert str(vendor_invoice) is not None

    def test_invoice_vendor_relationship(self, vendor_invoice, vendor):
        """Test invoice vendor relationship"""
        assert vendor_invoice.vendor == vendor


class TestInvoiceLine:
    """Test InvoiceLine model"""

    def test_create_invoice_line(self, invoice_line):
        """Test invoice line creation"""
        assert invoice_line.pk is not None
        assert invoice_line.description == "Test Material"
        assert invoice_line.quantity == Decimal("10.000")

    def test_invoice_line_relationships(self, invoice_line, vendor_invoice, po_line):
        """Test invoice line relationships"""
        assert invoice_line.vendor_invoice == vendor_invoice
        assert invoice_line.po_line == po_line


class TestInvoiceMatch:
    """Test InvoiceMatch model"""

    def test_create_invoice_match(self, db, vendor_invoice, purchase_order, receipt):
        """Test invoice match creation"""
        match = InvoiceMatch.objects.create(
            vendor_invoice=vendor_invoice,
            purchase_order=purchase_order,
            receipt=receipt,
            match_status=InvoiceMatch.MatchStatus.MATCHED
        )
        assert match.pk is not None
        assert match.match_status == InvoiceMatch.MatchStatus.MATCHED


# =============================================================================
# WEEK 3 TESTS: COSTING & FINANCE
# =============================================================================

class TestExpenseCategory:
    """Test ExpenseCategory model"""

    def test_create_expense_category(self, expense_category):
        """Test expense category creation"""
        assert expense_category.pk is not None
        assert expense_category.category_code == "MAT001"
        assert expense_category.is_active is True

    def test_expense_category_str(self, expense_category):
        """Test expense category string representation"""
        assert str(expense_category) is not None


class TestCostAllocation:
    """Test CostAllocation model"""

    def test_create_cost_allocation(self, db, expense_category):
        """Test cost allocation creation"""
        cost = CostAllocation.objects.create(
            cost_type=CostAllocation.CostType.MATERIAL,
            description="Test material cost",
            cost_amount=Decimal("1000.00"),
            cost_date=date.today(),
            expense_category=expense_category
        )
        assert cost.pk is not None
        assert cost.cost_amount == Decimal("1000.00")

    def test_cost_allocation_auto_number(self, db, expense_category):
        """Test cost allocation auto-generated number"""
        cost = CostAllocation.objects.create(
            cost_type=CostAllocation.CostType.MATERIAL,
            description="Test",
            cost_amount=Decimal("500.00"),
            cost_date=date.today(),
            expense_category=expense_category
        )
        assert cost.allocation_number is not None
        assert "COST-" in cost.allocation_number


class TestPaymentTerm:
    """Test PaymentTerm model"""

    def test_create_payment_term(self, payment_term):
        """Test payment term creation"""
        assert payment_term.pk is not None
        assert payment_term.term_code == "NET30"
        assert payment_term.due_days == 30

    def test_payment_term_str(self, payment_term):
        """Test payment term string representation"""
        assert str(payment_term) is not None


class TestVendorPayment:
    """Test VendorPayment model"""

    def test_create_vendor_payment(self, db, vendor):
        """Test vendor payment creation"""
        payment = VendorPayment.objects.create(
            vendor=vendor,
            payment_method=VendorPayment.PaymentMethod.WIRE_TRANSFER,
            payment_date=date.today(),
            payment_amount=Decimal("1000.00")
        )
        assert payment.pk is not None
        assert payment.payment_amount == Decimal("1000.00")

    def test_payment_auto_number(self, db, vendor):
        """Test payment auto-generated number"""
        payment = VendorPayment.objects.create(
            vendor=vendor,
            payment_method=VendorPayment.PaymentMethod.WIRE_TRANSFER,
            payment_date=date.today(),
            payment_amount=Decimal("1000.00")
        )
        assert payment.payment_number is not None
        assert "PAY-" in payment.payment_number


class TestPaymentAllocation:
    """Test PaymentAllocation model"""

    def test_create_payment_allocation(self, db, vendor, vendor_invoice):
        """Test payment allocation creation"""
        payment = VendorPayment.objects.create(
            vendor=vendor,
            payment_method=VendorPayment.PaymentMethod.WIRE_TRANSFER,
            payment_date=date.today(),
            payment_amount=Decimal("1000.00")
        )
        allocation = PaymentAllocation.objects.create(
            payment=payment,
            vendor_invoice=vendor_invoice,
            allocated_amount=Decimal("1000.00")
        )
        assert allocation.pk is not None
        assert allocation.allocated_amount == Decimal("1000.00")


# =============================================================================
# LEGACY MODEL TESTS
# =============================================================================

class TestSupplier:
    """Test Supplier model (legacy)"""

    def test_create_supplier(self, supplier):
        """Test supplier creation"""
        assert supplier.pk is not None
        assert supplier.code == "SUP001"
        assert supplier.is_active is True

    def test_supplier_str(self, supplier):
        """Test supplier string representation"""
        assert str(supplier) is not None


class TestCAPA:
    """Test CAPA model"""

    def test_create_capa(self, db, user):
        """Test CAPA creation"""
        capa = CAPA.objects.create(
            title="Test CAPA",
            description="Test description",
            status=CAPA.Status.OPEN,
            assigned_to=user,
            due_date=date.today() + timedelta(days=30)
        )
        assert capa.pk is not None
        assert capa.title == "Test CAPA"
        assert capa.status == CAPA.Status.OPEN

    def test_capa_auto_number(self, db, user):
        """Test CAPA auto-generated number"""
        capa = CAPA.objects.create(
            title="Test CAPA",
            description="Test",
            status=CAPA.Status.OPEN,
            assigned_to=user,
            due_date=date.today() + timedelta(days=30)
        )
        assert capa.capa_number is not None
        assert "CAPA-" in capa.capa_number
