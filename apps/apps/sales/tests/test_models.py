"""
Sales App - Model Tests
Comprehensive tests for all sales models.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.db import IntegrityError


# =============================================================================
# CUSTOMER MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestCustomerModel:
    """Tests for Customer model."""

    def test_create_customer(self, base_user):
        """Test basic customer creation."""
        from apps.sales.models import Customer
        customer = Customer.objects.create(
            code='CUST-NEW-001',
            name='New Test Company',
            customer_type=Customer.CustomerType.OPERATOR,
            city='Riyadh',
            created_by=base_user
        )
        assert customer.pk is not None
        assert customer.code == 'CUST-NEW-001'

    def test_str_representation(self, customer):
        """Test __str__ method."""
        expected = f"{customer.code} - {customer.name}"
        assert str(customer) == expected

    def test_unique_code(self, customer, base_user):
        """Test customer code uniqueness constraint."""
        from apps.sales.models import Customer
        with pytest.raises(IntegrityError):
            Customer.objects.create(
                code=customer.code,
                name='Duplicate Code',
                created_by=base_user
            )

    def test_customer_type_choices(self, customer):
        """Test customer type choices."""
        from apps.sales.models import Customer
        assert customer.customer_type in [c[0] for c in Customer.CustomerType.choices]

    def test_aramco_customer(self, customer_aramco):
        """Test Aramco customer flag."""
        assert customer_aramco.is_aramco is True
        assert customer_aramco.name_ar == 'أرامكو السعودية'

    def test_contractor_customer(self, customer_contractor):
        """Test contractor customer type."""
        from apps.sales.models import Customer
        assert customer_contractor.customer_type == Customer.CustomerType.CONTRACTOR

    def test_default_values(self, base_user):
        """Test default field values."""
        from apps.sales.models import Customer
        customer = Customer.objects.create(
            code='DEF-001',
            name='Default Test',
            created_by=base_user
        )
        assert customer.country == 'Saudi Arabia'
        assert customer.is_active is True
        assert customer.is_aramco is False


# =============================================================================
# CUSTOMER CONTACT MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestCustomerContactModel:
    """Tests for CustomerContact model."""

    def test_create_contact(self, customer):
        """Test basic contact creation."""
        from apps.sales.models import CustomerContact
        contact = CustomerContact.objects.create(
            customer=customer,
            name='Jane Doe',
            title='Project Manager',
            email='jane@testoil.com',
            is_primary=False
        )
        assert contact.pk is not None

    def test_str_representation(self, customer_contact):
        """Test __str__ method."""
        expected = f"{customer_contact.customer.code} - {customer_contact.name}"
        assert str(customer_contact) == expected

    def test_cascade_delete(self, customer, customer_contact):
        """Test contacts are deleted when customer is deleted."""
        from apps.sales.models import CustomerContact
        contact_pk = customer_contact.pk
        customer.delete()
        assert CustomerContact.objects.filter(pk=contact_pk).count() == 0

    def test_multiple_contacts(self, customer):
        """Test multiple contacts per customer."""
        from apps.sales.models import CustomerContact
        contact1 = CustomerContact.objects.create(
            customer=customer,
            name='Contact 1',
            is_primary=True
        )
        contact2 = CustomerContact.objects.create(
            customer=customer,
            name='Contact 2',
            is_primary=False
        )
        assert customer.contacts.count() == 2


# =============================================================================
# RIG MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestRigModel:
    """Tests for Rig model."""

    def test_create_rig(self, customer):
        """Test basic rig creation."""
        from apps.sales.models import Rig
        rig = Rig.objects.create(
            code='RIG-NEW-001',
            name='New Test Rig',
            customer=customer,
            rig_type='Jack-Up'
        )
        assert rig.pk is not None

    def test_str_representation(self, rig):
        """Test __str__ method."""
        expected = f"{rig.code} - {rig.name}"
        assert str(rig) == expected

    def test_unique_code(self, rig, customer):
        """Test rig code uniqueness constraint."""
        from apps.sales.models import Rig
        with pytest.raises(IntegrityError):
            Rig.objects.create(
                code=rig.code,
                name='Duplicate Rig',
                customer=customer
            )

    def test_gps_coordinates(self, rig):
        """Test GPS coordinate storage."""
        assert rig.latitude == Decimal('25.5000000')
        assert rig.longitude == Decimal('49.5000000')

    def test_customer_set_null(self, rig, customer):
        """Test customer FK is SET_NULL on delete."""
        from apps.sales.models import Rig
        customer.delete()
        rig.refresh_from_db()
        assert rig.customer is None


# =============================================================================
# WELL MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestWellModel:
    """Tests for Well model."""

    def test_create_well(self, customer):
        """Test basic well creation."""
        from apps.sales.models import Well
        well = Well.objects.create(
            code='WELL-NEW-001',
            name='New Test Well',
            customer=customer,
            field_name='Test Field',
            target_depth=20000
        )
        assert well.pk is not None

    def test_str_representation(self, well):
        """Test __str__ method."""
        expected = f"{well.code} - {well.name}"
        assert str(well) == expected

    def test_unique_code(self, well, customer):
        """Test well code uniqueness constraint."""
        from apps.sales.models import Well
        with pytest.raises(IntegrityError):
            Well.objects.create(
                code=well.code,
                name='Duplicate Well',
                customer=customer
            )

    def test_rig_relationship(self, well, rig):
        """Test well-rig relationship."""
        assert well.rig == rig
        assert well in rig.wells.all()


# =============================================================================
# WAREHOUSE MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestWarehouseModel:
    """Tests for Warehouse model."""

    def test_create_warehouse(self):
        """Test basic warehouse creation."""
        from apps.sales.models import Warehouse
        warehouse = Warehouse.objects.create(
            code='WH-NEW-001',
            name='New Warehouse',
            warehouse_type=Warehouse.WarehouseType.ARDT
        )
        assert warehouse.pk is not None

    def test_str_representation(self, warehouse_ardt):
        """Test __str__ method."""
        expected = f"{warehouse_ardt.code} - {warehouse_ardt.name}"
        assert str(warehouse_ardt) == expected

    def test_unique_code(self, warehouse_ardt):
        """Test warehouse code uniqueness constraint."""
        from apps.sales.models import Warehouse
        with pytest.raises(IntegrityError):
            Warehouse.objects.create(
                code=warehouse_ardt.code,
                name='Duplicate Warehouse'
            )

    def test_warehouse_type_choices(self, warehouse_ardt, warehouse_customer):
        """Test warehouse type choices."""
        from apps.sales.models import Warehouse
        assert warehouse_ardt.warehouse_type == Warehouse.WarehouseType.ARDT
        assert warehouse_customer.warehouse_type == Warehouse.WarehouseType.CUSTOMER


# =============================================================================
# SALES ORDER MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestSalesOrderModel:
    """Tests for SalesOrder model."""

    def test_create_sales_order(self, customer, base_user):
        """Test basic sales order creation."""
        from apps.sales.models import SalesOrder
        so = SalesOrder.objects.create(
            so_number='SO-NEW-001',
            customer=customer,
            order_date=date.today(),
            created_by=base_user
        )
        assert so.pk is not None

    def test_str_representation(self, sales_order):
        """Test __str__ method."""
        assert str(sales_order) == sales_order.so_number

    def test_unique_so_number(self, sales_order, customer, base_user):
        """Test SO number uniqueness constraint."""
        from apps.sales.models import SalesOrder
        with pytest.raises(IntegrityError):
            SalesOrder.objects.create(
                so_number=sales_order.so_number,
                customer=customer,
                order_date=date.today(),
                created_by=base_user
            )

    def test_status_choices(self, sales_order):
        """Test status choices."""
        from apps.sales.models import SalesOrder
        assert sales_order.status in [c[0] for c in SalesOrder.Status.choices]

    def test_customer_protect(self, sales_order, customer):
        """Test customer FK is PROTECT on delete."""
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            customer.delete()

    def test_default_values(self, customer, base_user):
        """Test default field values."""
        from apps.sales.models import SalesOrder
        so = SalesOrder.objects.create(
            so_number='SO-DEF-001',
            customer=customer,
            order_date=date.today(),
            created_by=base_user
        )
        assert so.currency == 'SAR'
        assert so.subtotal == Decimal('0')
        assert so.status == SalesOrder.Status.DRAFT


# =============================================================================
# SALES ORDER LINE MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestSalesOrderLineModel:
    """Tests for SalesOrderLine model."""

    def test_create_line(self, sales_order):
        """Test basic line creation."""
        from apps.sales.models import SalesOrderLine
        line = SalesOrderLine.objects.create(
            sales_order=sales_order,
            line_number=2,
            description='12.25" RC Drill Bit',
            quantity=1,
            unit_price=Decimal('25000.00')
        )
        assert line.pk is not None

    def test_str_representation(self, sales_order_line):
        """Test __str__ method."""
        expected = f"{sales_order_line.sales_order.so_number} - Line {sales_order_line.line_number}"
        assert str(sales_order_line) == expected

    def test_cascade_delete(self, sales_order, sales_order_line):
        """Test lines are deleted when order is deleted."""
        from apps.sales.models import SalesOrderLine
        line_pk = sales_order_line.pk
        sales_order.delete()
        assert SalesOrderLine.objects.filter(pk=line_pk).count() == 0

    def test_unique_together_constraint(self, sales_order, sales_order_line):
        """Test unique together constraint on sales_order and line_number."""
        from apps.sales.models import SalesOrderLine
        with pytest.raises(IntegrityError):
            SalesOrderLine.objects.create(
                sales_order=sales_order,
                line_number=sales_order_line.line_number,
                description='Duplicate line'
            )


# =============================================================================
# SERVICE SITE MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestServiceSiteModel:
    """Tests for ServiceSite model."""

    def test_create_service_site(self, customer):
        """Test basic service site creation."""
        from apps.sales.models import ServiceSite
        site = ServiceSite.objects.create(
            site_code='SITE-NEW-001',
            name='New Service Site',
            customer=customer,
            site_type=ServiceSite.SiteType.RIG_SITE,
            address_line1='Field Location',
            city='Dhahran'
        )
        assert site.pk is not None

    def test_str_representation(self, service_site):
        """Test __str__ method."""
        expected = f"{service_site.site_code} - {service_site.name}"
        assert str(service_site) == expected

    def test_unique_site_code(self, service_site, customer):
        """Test site code uniqueness constraint."""
        from apps.sales.models import ServiceSite
        with pytest.raises(IntegrityError):
            ServiceSite.objects.create(
                site_code=service_site.site_code,
                name='Duplicate Site',
                customer=customer,
                address_line1='Address',
                city='City'
            )

    def test_site_type_choices(self, service_site):
        """Test site type choices."""
        from apps.sales.models import ServiceSite
        assert service_site.site_type in [c[0] for c in ServiceSite.SiteType.choices]

    def test_status_choices(self, service_site):
        """Test status choices."""
        from apps.sales.models import ServiceSite
        assert service_site.status in [c[0] for c in ServiceSite.Status.choices]

    def test_gps_coordinates(self, service_site):
        """Test GPS coordinate storage."""
        assert service_site.latitude == Decimal('25.5000000')
        assert service_site.longitude == Decimal('49.5000000')


# =============================================================================
# FIELD TECHNICIAN MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestFieldTechnicianModel:
    """Tests for FieldTechnician model."""

    def test_create_technician(self, field_tech_user):
        """Test basic technician creation."""
        from apps.sales.models import FieldTechnician
        tech = FieldTechnician.objects.create(
            user=field_tech_user,
            employee_id='TECH-NEW-001',
            specialization='Roller Cone',
            hire_date=date.today()
        )
        assert tech.pk is not None

    def test_str_representation(self, field_technician):
        """Test __str__ method."""
        expected = f"{field_technician.employee_id} - {field_technician.user.get_full_name()}"
        assert str(field_technician) == expected

    def test_user_one_to_one(self, field_technician, field_tech_user):
        """Test user one-to-one relationship."""
        assert field_technician.user == field_tech_user


# =============================================================================
# FIELD SERVICE REQUEST MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestFieldServiceRequestModel:
    """Tests for FieldServiceRequest model."""

    def test_create_request(self, customer, service_site, base_user):
        """Test basic request creation."""
        from apps.sales.models import FieldServiceRequest
        request = FieldServiceRequest.objects.create(
            request_number='FSR-NEW-001',
            customer=customer,
            service_site=service_site,
            request_type=FieldServiceRequest.RequestType.REPAIR,
            priority=FieldServiceRequest.Priority.HIGH,
            requested_date=date.today(),
            description='Urgent repair needed',
            created_by=base_user
        )
        assert request.pk is not None

    def test_str_representation(self, field_service_request):
        """Test __str__ method."""
        assert field_service_request.request_number in str(field_service_request)

    def test_unique_request_number(self, field_service_request, customer, service_site, base_user):
        """Test request number uniqueness constraint."""
        from apps.sales.models import FieldServiceRequest
        with pytest.raises(IntegrityError):
            FieldServiceRequest.objects.create(
                request_number=field_service_request.request_number,
                customer=customer,
                service_site=service_site,
                request_type=FieldServiceRequest.RequestType.INSPECTION,
                requested_date=date.today(),
                description='Duplicate',
                created_by=base_user
            )

    def test_request_type_choices(self, field_service_request):
        """Test request type choices."""
        from apps.sales.models import FieldServiceRequest
        assert field_service_request.request_type in [c[0] for c in FieldServiceRequest.RequestType.choices]

    def test_priority_choices(self, field_service_request):
        """Test priority choices."""
        from apps.sales.models import FieldServiceRequest
        assert field_service_request.priority in [c[0] for c in FieldServiceRequest.Priority.choices]

    def test_status_choices(self, field_service_request):
        """Test status choices."""
        from apps.sales.models import FieldServiceRequest
        assert field_service_request.status in [c[0] for c in FieldServiceRequest.Status.choices]


# =============================================================================
# CUSTOMER DOCUMENT REQUIREMENT MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestCustomerDocumentRequirementModel:
    """Tests for CustomerDocumentRequirement model."""

    def test_create_requirement(self, customer):
        """Test basic requirement creation."""
        from apps.sales.models import CustomerDocumentRequirement
        req = CustomerDocumentRequirement.objects.create(
            customer=customer,
            document_type='Certificate of Origin',
            description='Required for all shipments',
            is_required=True
        )
        assert req.pk is not None

    def test_str_representation(self, customer):
        """Test __str__ method."""
        from apps.sales.models import CustomerDocumentRequirement
        req = CustomerDocumentRequirement.objects.create(
            customer=customer,
            document_type='Test Doc',
            is_required=True
        )
        expected = f"{customer.code} - Test Doc"
        assert str(req) == expected

    def test_cascade_delete(self, customer):
        """Test requirements are deleted when customer is deleted."""
        from apps.sales.models import CustomerDocumentRequirement
        req = CustomerDocumentRequirement.objects.create(
            customer=customer,
            document_type='To Delete',
            is_required=False
        )
        req_pk = req.pk
        customer.delete()
        assert CustomerDocumentRequirement.objects.filter(pk=req_pk).count() == 0


# =============================================================================
# GPS COORDINATE PRECISION TESTS
# =============================================================================

@pytest.mark.django_db
class TestGPSCoordinatePrecision:
    """Tests for GPS coordinate precision across models."""

    def test_rig_gps_precision(self, customer):
        """Test rig GPS coordinate precision."""
        from apps.sales.models import Rig
        rig = Rig.objects.create(
            code='GPS-TEST-001',
            name='GPS Test Rig',
            latitude=Decimal('25.1234567'),
            longitude=Decimal('49.9876543')
        )
        assert rig.latitude == Decimal('25.1234567')
        assert rig.longitude == Decimal('49.9876543')

    def test_service_site_gps_precision(self, customer):
        """Test service site GPS coordinate precision."""
        from apps.sales.models import ServiceSite
        site = ServiceSite.objects.create(
            site_code='GPS-SITE-001',
            name='GPS Test Site',
            customer=customer,
            address_line1='Test Address',
            city='Test City',
            latitude=Decimal('26.1234567'),
            longitude=Decimal('50.9876543')
        )
        assert site.latitude == Decimal('26.1234567')
        assert site.longitude == Decimal('50.9876543')


# =============================================================================
# DECIMAL FIELD PRECISION TESTS
# =============================================================================

@pytest.mark.django_db
class TestDecimalPrecision:
    """Tests for decimal field precision."""

    def test_credit_limit_precision(self, base_user):
        """Test credit limit decimal precision (15,2)."""
        from apps.sales.models import Customer
        customer = Customer.objects.create(
            code='DEC-TEST-001',
            name='Decimal Test',
            credit_limit=Decimal('9999999999999.99'),
            created_by=base_user
        )
        assert customer.credit_limit == Decimal('9999999999999.99')

    def test_sales_order_total_precision(self, customer, base_user):
        """Test sales order total precision (15,2)."""
        from apps.sales.models import SalesOrder
        so = SalesOrder.objects.create(
            so_number='DEC-SO-001',
            customer=customer,
            order_date=date.today(),
            total_amount=Decimal('9999999999999.99'),
            created_by=base_user
        )
        assert so.total_amount == Decimal('9999999999999.99')

    def test_line_price_precision(self, sales_order):
        """Test sales order line price precision."""
        from apps.sales.models import SalesOrderLine
        line = SalesOrderLine.objects.create(
            sales_order=sales_order,
            line_number=10,
            description='Precision Test',
            unit_price=Decimal('99999.99'),
            discount_percent=Decimal('10.50')
        )
        assert line.unit_price == Decimal('99999.99')
        assert line.discount_percent == Decimal('10.50')
