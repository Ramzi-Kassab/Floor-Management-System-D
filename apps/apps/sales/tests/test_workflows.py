"""
Sales App - Integration/Workflow Tests
End-to-end tests for complete user workflows.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone


# =============================================================================
# SALES ORDER LIFECYCLE WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestSalesOrderLifecycleWorkflow:
    """Tests for complete sales order lifecycle."""

    def test_full_sales_order_lifecycle(self, customer, base_user, warehouse_ardt):
        """Test complete sales order lifecycle: Draft → Confirmed → Delivered."""
        from apps.sales.models import SalesOrder, SalesOrderLine

        # 1. Create sales order (DRAFT)
        so = SalesOrder.objects.create(
            so_number='SO-LIFE-001',
            customer=customer,
            customer_po='PO-12345',
            order_date=date.today(),
            required_date=date.today() + timedelta(days=14),
            status=SalesOrder.Status.DRAFT,
            created_by=base_user
        )
        assert so.status == SalesOrder.Status.DRAFT

        # 2. Add line items
        line1 = SalesOrderLine.objects.create(
            sales_order=so,
            line_number=1,
            description='8.5" FC Drill Bit',
            quantity=2,
            unit_price=Decimal('15000.00'),
            line_total=Decimal('30000.00')
        )
        line2 = SalesOrderLine.objects.create(
            sales_order=so,
            line_number=2,
            description='12.25" RC Drill Bit',
            quantity=1,
            unit_price=Decimal('25000.00'),
            line_total=Decimal('25000.00')
        )

        # Calculate totals
        so.subtotal = line1.line_total + line2.line_total
        so.tax_amount = so.subtotal * Decimal('0.15')  # 15% VAT
        so.total_amount = so.subtotal + so.tax_amount
        so.save()

        # 3. Confirm order
        so.status = SalesOrder.Status.CONFIRMED
        so.save()
        assert so.status == SalesOrder.Status.CONFIRMED

        # 4. Start production (IN_PROGRESS)
        so.status = SalesOrder.Status.IN_PROGRESS
        so.save()
        for line in so.lines.all():
            line.status = SalesOrderLine.Status.IN_PRODUCTION
            line.save()

        # 5. Ready for dispatch
        so.status = SalesOrder.Status.READY
        so.save()
        for line in so.lines.all():
            line.status = SalesOrderLine.Status.READY
            line.save()

        # 6. Dispatch
        so.status = SalesOrder.Status.DISPATCHED
        so.save()
        for line in so.lines.all():
            line.status = SalesOrderLine.Status.DISPATCHED
            line.save()

        # 7. Deliver
        so.status = SalesOrder.Status.DELIVERED
        so.save()
        assert so.status == SalesOrder.Status.DELIVERED

    def test_sales_order_cancellation_workflow(self, customer, base_user):
        """Test sales order cancellation workflow."""
        from apps.sales.models import SalesOrder, SalesOrderLine

        # Create order
        so = SalesOrder.objects.create(
            so_number='SO-CANCEL-001',
            customer=customer,
            order_date=date.today(),
            status=SalesOrder.Status.DRAFT,
            created_by=base_user
        )

        # Add line
        SalesOrderLine.objects.create(
            sales_order=so,
            line_number=1,
            description='Test Bit',
            quantity=1,
            unit_price=Decimal('10000.00')
        )

        # Cancel order
        so.status = SalesOrder.Status.CANCELLED
        so.notes = 'Cancelled by customer request'
        so.save()

        # Cancel lines
        for line in so.lines.all():
            line.status = SalesOrderLine.Status.CANCELLED
            line.save()

        assert so.status == SalesOrder.Status.CANCELLED
        assert so.lines.first().status == SalesOrderLine.Status.CANCELLED


# =============================================================================
# CUSTOMER ONBOARDING WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestCustomerOnboardingWorkflow:
    """Tests for customer onboarding workflow."""

    def test_full_customer_onboarding(self, base_user):
        """Test complete customer onboarding with contacts and requirements."""
        from apps.sales.models import Customer, CustomerContact, CustomerDocumentRequirement

        # 1. Create customer
        customer = Customer.objects.create(
            code='CUST-ONBOARD-001',
            name='New Onboarded Customer',
            customer_type=Customer.CustomerType.OPERATOR,
            city='Riyadh',
            country='Saudi Arabia',
            email='contact@newcustomer.com',
            credit_limit=Decimal('500000.00'),
            payment_terms='Net 30',
            is_active=True,
            created_by=base_user
        )

        # 2. Add primary contact
        primary_contact = CustomerContact.objects.create(
            customer=customer,
            name='Ahmed Al-Saud',
            title='Procurement Manager',
            email='ahmed@newcustomer.com',
            phone='+966501234567',
            is_primary=True,
            is_active=True
        )

        # 3. Add secondary contact
        secondary_contact = CustomerContact.objects.create(
            customer=customer,
            name='Khalid Ibrahim',
            title='Operations Manager',
            email='khalid@newcustomer.com',
            is_primary=False,
            is_active=True
        )

        # 4. Add document requirements
        doc_req1 = CustomerDocumentRequirement.objects.create(
            customer=customer,
            document_type='Certificate of Origin',
            description='Required for all international shipments',
            is_required=True
        )
        doc_req2 = CustomerDocumentRequirement.objects.create(
            customer=customer,
            document_type='Material Test Certificate',
            is_required=True
        )

        # Verify setup
        assert customer.contacts.count() == 2
        assert customer.contacts.filter(is_primary=True).count() == 1
        assert customer.document_requirements.count() == 2


# =============================================================================
# FIELD SERVICE WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestFieldServiceWorkflow:
    """Tests for field service request workflow."""

    def test_full_field_service_request_workflow(self, customer, service_site, field_technician, base_user):
        """Test complete field service request workflow."""
        from apps.sales.models import FieldServiceRequest

        # 1. Create service request
        request = FieldServiceRequest.objects.create(
            request_number='FSR-FLOW-001',
            customer=customer,
            service_site=service_site,
            request_type=FieldServiceRequest.RequestType.INSPECTION,
            priority=FieldServiceRequest.Priority.HIGH,
            status=FieldServiceRequest.Status.PENDING,
            requested_date=date.today(),
            description='Urgent bit inspection required',
            created_by=base_user
        )
        assert request.status == FieldServiceRequest.Status.PENDING

        # 2. Assign technician
        request.assigned_technician = field_technician
        request.status = FieldServiceRequest.Status.ASSIGNED
        request.save()
        assert request.status == FieldServiceRequest.Status.ASSIGNED

        # 3. Technician en route
        request.status = FieldServiceRequest.Status.IN_PROGRESS
        request.actual_start_date = timezone.now()
        request.save()
        assert request.status == FieldServiceRequest.Status.IN_PROGRESS

        # 4. Complete service
        request.status = FieldServiceRequest.Status.COMPLETED
        request.actual_end_date = timezone.now()
        request.completion_notes = 'Inspection completed. Bit in good condition.'
        request.save()
        assert request.status == FieldServiceRequest.Status.COMPLETED


# =============================================================================
# RIG AND WELL LIFECYCLE WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestRigWellLifecycleWorkflow:
    """Tests for rig and well lifecycle."""

    def test_rig_assignment_workflow(self, customer, customer_contractor):
        """Test rig assignment to customer with wells."""
        from apps.sales.models import Rig, Well

        # 1. Create rig
        rig = Rig.objects.create(
            code='RIG-WORKFLOW-001',
            name='Workflow Test Rig',
            customer=customer,
            contractor=customer_contractor,
            rig_type='Land Rig',
            location='Test Field',
            is_active=True
        )

        # 2. Create first well
        well1 = Well.objects.create(
            code='WELL-WF-001',
            name='Workflow Well 1',
            customer=customer,
            rig=rig,
            field_name='Test Field',
            spud_date=date.today(),
            target_depth=12000,
            is_active=True
        )

        # 3. Complete first well
        well1.is_active = False
        well1.save()

        # 4. Move rig to second well
        well2 = Well.objects.create(
            code='WELL-WF-002',
            name='Workflow Well 2',
            customer=customer,
            rig=rig,
            field_name='Test Field',
            spud_date=date.today() + timedelta(days=30),
            target_depth=15000,
            is_active=True
        )

        # Verify rig has both wells in history
        assert rig.wells.count() == 2


# =============================================================================
# SERVICE SITE MANAGEMENT WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestServiceSiteWorkflow:
    """Tests for service site management workflow."""

    def test_service_site_activation_workflow(self, customer):
        """Test service site activation and service history."""
        from apps.sales.models import ServiceSite

        # 1. Create site (under construction)
        site = ServiceSite.objects.create(
            site_code='SITE-WF-001',
            name='Workflow Test Site',
            customer=customer,
            site_type=ServiceSite.SiteType.RIG_SITE,
            status=ServiceSite.Status.UNDER_CONSTRUCTION,
            address_line1='New Field Location',
            city='Dhahran',
            is_active=False
        )
        assert site.status == ServiceSite.Status.UNDER_CONSTRUCTION

        # 2. Activate site
        site.status = ServiceSite.Status.ACTIVE
        site.is_active = True
        site.first_service_date = date.today()
        site.save()
        assert site.status == ServiceSite.Status.ACTIVE

        # 3. Track service visits
        site.total_service_visits += 1
        site.last_service_date = date.today()
        site.save()

        # 4. Temporarily close
        site.status = ServiceSite.Status.TEMPORARILY_CLOSED
        site.save()
        assert site.status == ServiceSite.Status.TEMPORARILY_CLOSED


# =============================================================================
# PRICING AND DISCOUNT WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestPricingWorkflow:
    """Tests for pricing and discount calculations."""

    def test_sales_order_pricing_calculation(self, customer, base_user):
        """Test complete sales order pricing with discounts."""
        from apps.sales.models import SalesOrder, SalesOrderLine

        # Create order
        so = SalesOrder.objects.create(
            so_number='SO-PRICE-001',
            customer=customer,
            order_date=date.today(),
            created_by=base_user
        )

        # Add lines with different discounts
        line1 = SalesOrderLine.objects.create(
            sales_order=so,
            line_number=1,
            description='Standard Bit',
            quantity=5,
            unit_price=Decimal('10000.00'),
            discount_percent=Decimal('10.00')  # 10% discount
        )
        # Calculate line1 total: 5 * 10000 * (1 - 0.10) = 45000
        line1.line_total = line1.quantity * line1.unit_price * (1 - line1.discount_percent / 100)
        line1.save()

        line2 = SalesOrderLine.objects.create(
            sales_order=so,
            line_number=2,
            description='Premium Bit',
            quantity=2,
            unit_price=Decimal('25000.00'),
            discount_percent=Decimal('5.00')  # 5% discount
        )
        # Calculate line2 total: 2 * 25000 * (1 - 0.05) = 47500
        line2.line_total = line2.quantity * line2.unit_price * (1 - line2.discount_percent / 100)
        line2.save()

        # Calculate order totals
        so.subtotal = line1.line_total + line2.line_total  # 92500
        so.tax_amount = so.subtotal * Decimal('0.15')  # 13875
        so.total_amount = so.subtotal + so.tax_amount  # 106375
        so.save()

        assert so.subtotal == Decimal('92500.00')
        assert so.tax_amount == Decimal('13875.00')
        assert so.total_amount == Decimal('106375.00')


# =============================================================================
# CUSTOMER CREDIT WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestCustomerCreditWorkflow:
    """Tests for customer credit management workflow."""

    def test_credit_limit_validation(self, base_user):
        """Test customer credit limit validation."""
        from apps.sales.models import Customer, SalesOrder

        # Create customer with credit limit
        customer = Customer.objects.create(
            code='CUST-CREDIT-001',
            name='Credit Test Customer',
            credit_limit=Decimal('100000.00'),
            created_by=base_user
        )

        # Create order within limit
        so1 = SalesOrder.objects.create(
            so_number='SO-CREDIT-001',
            customer=customer,
            order_date=date.today(),
            total_amount=Decimal('50000.00'),
            created_by=base_user
        )

        # Create second order
        so2 = SalesOrder.objects.create(
            so_number='SO-CREDIT-002',
            customer=customer,
            order_date=date.today(),
            total_amount=Decimal('40000.00'),
            created_by=base_user
        )

        # Calculate total outstanding
        total_outstanding = so1.total_amount + so2.total_amount
        remaining_credit = customer.credit_limit - total_outstanding

        assert total_outstanding == Decimal('90000.00')
        assert remaining_credit == Decimal('10000.00')


# =============================================================================
# MULTI-CUSTOMER SALES WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestMultiCustomerWorkflow:
    """Tests for handling multiple customers."""

    def test_customer_hierarchy_workflow(self, base_user):
        """Test operator-contractor relationship workflow."""
        from apps.sales.models import Customer, Rig

        # Create operator
        operator = Customer.objects.create(
            code='OP-HIER-001',
            name='Oil Operator Co',
            customer_type=Customer.CustomerType.OPERATOR,
            is_aramco=True,
            created_by=base_user
        )

        # Create contractor
        contractor = Customer.objects.create(
            code='CONT-HIER-001',
            name='Drilling Contractor Inc',
            customer_type=Customer.CustomerType.CONTRACTOR,
            created_by=base_user
        )

        # Create rig with both relationships
        rig = Rig.objects.create(
            code='RIG-HIER-001',
            name='Hierarchy Test Rig',
            customer=operator,
            contractor=contractor,
            is_active=True
        )

        # Verify relationships
        assert rig.customer == operator
        assert rig.contractor == contractor
        assert rig in operator.rigs.all()
        assert rig in contractor.contracted_rigs.all()
