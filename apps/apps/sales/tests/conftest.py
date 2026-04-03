"""
Sales App - Pytest Configuration and Shared Fixtures
"""

import pytest
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def base_user(db):
    """Base user fixture for all tests."""
    return User.objects.create_user(
        username='base_user',
        email='base@example.com',
        password='basepass123',
        first_name='Base',
        last_name='User'
    )


@pytest.fixture
def staff_user(db):
    """Staff user fixture."""
    return User.objects.create_user(
        username='staff_user',
        email='staff@example.com',
        password='staffpass123',
        is_staff=True
    )


@pytest.fixture
def admin_user(db):
    """Admin/superuser fixture."""
    return User.objects.create_superuser(
        username='admin_user',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def sales_rep(db):
    """Sales representative user fixture."""
    return User.objects.create_user(
        username='sales_rep',
        email='sales@example.com',
        password='salespass123',
        first_name='Sales',
        last_name='Rep'
    )


@pytest.fixture
def field_tech_user(db):
    """Field technician user fixture."""
    return User.objects.create_user(
        username='field_tech',
        email='fieldtech@example.com',
        password='fieldtechpass123',
        first_name='Field',
        last_name='Technician'
    )


@pytest.fixture
def customer(db, base_user):
    """Basic customer fixture."""
    from apps.sales.models import Customer
    return Customer.objects.create(
        code='CUST-001',
        name='Test Oil Company',
        customer_type=Customer.CustomerType.OPERATOR,
        city='Dhahran',
        country='Saudi Arabia',
        email='contact@testoil.com',
        is_active=True,
        created_by=base_user
    )


@pytest.fixture
def customer_aramco(db, base_user):
    """Aramco customer fixture."""
    from apps.sales.models import Customer
    return Customer.objects.create(
        code='ARAMCO-001',
        name='Saudi Aramco',
        name_ar='أرامكو السعودية',
        customer_type=Customer.CustomerType.OPERATOR,
        city='Dhahran',
        country='Saudi Arabia',
        is_aramco=True,
        is_active=True,
        created_by=base_user
    )


@pytest.fixture
def customer_contractor(db, base_user):
    """Contractor customer fixture."""
    from apps.sales.models import Customer
    return Customer.objects.create(
        code='CONT-001',
        name='Drilling Services Inc',
        customer_type=Customer.CustomerType.CONTRACTOR,
        city='Dammam',
        is_active=True,
        created_by=base_user
    )


@pytest.fixture
def customer_contact(db, customer):
    """Customer contact fixture."""
    from apps.sales.models import CustomerContact
    return CustomerContact.objects.create(
        customer=customer,
        name='John Smith',
        title='Operations Manager',
        email='john.smith@testoil.com',
        phone='+966501234567',
        is_primary=True,
        is_active=True
    )


@pytest.fixture
def rig(db, customer, customer_contractor):
    """Rig fixture."""
    from apps.sales.models import Rig
    return Rig.objects.create(
        code='RIG-001',
        name='Test Rig Alpha',
        customer=customer,
        contractor=customer_contractor,
        rig_type='Land Rig',
        location='Ghawar Field',
        latitude=Decimal('25.5000000'),
        longitude=Decimal('49.5000000'),
        is_active=True
    )


@pytest.fixture
def well(db, customer, rig):
    """Well fixture."""
    from apps.sales.models import Well
    return Well.objects.create(
        code='WELL-001',
        name='Test Well Alpha-1',
        customer=customer,
        rig=rig,
        field_name='Ghawar',
        spud_date=date.today() - timedelta(days=30),
        target_depth=15000,
        is_active=True
    )


@pytest.fixture
def warehouse_ardt(db):
    """ARDT warehouse fixture."""
    from apps.sales.models import Warehouse
    return Warehouse.objects.create(
        code='WH-ARDT-001',
        name='ARDT Main Factory',
        warehouse_type=Warehouse.WarehouseType.ARDT,
        city='Dammam',
        is_active=True
    )


@pytest.fixture
def warehouse_customer(db, customer):
    """Customer warehouse fixture."""
    from apps.sales.models import Warehouse
    return Warehouse.objects.create(
        code='WH-CUST-001',
        name='Customer Warehouse',
        warehouse_type=Warehouse.WarehouseType.CUSTOMER,
        customer=customer,
        city='Dhahran',
        is_active=True
    )


@pytest.fixture
def sales_order(db, customer, base_user, warehouse_ardt):
    """Sales order fixture."""
    from apps.sales.models import SalesOrder
    return SalesOrder.objects.create(
        so_number='SO-2024-001',
        customer=customer,
        customer_po='PO-12345',
        order_date=date.today(),
        required_date=date.today() + timedelta(days=14),
        status=SalesOrder.Status.DRAFT,
        currency='SAR',
        created_by=base_user
    )


@pytest.fixture
def sales_order_line(db, sales_order):
    """Sales order line fixture."""
    from apps.sales.models import SalesOrderLine
    return SalesOrderLine.objects.create(
        sales_order=sales_order,
        line_number=1,
        description='8.5" FC Drill Bit - Standard',
        quantity=2,
        unit_price=Decimal('15000.00'),
        line_total=Decimal('30000.00'),
        status=SalesOrderLine.Status.PENDING
    )


@pytest.fixture
def service_site(db, customer):
    """Service site fixture."""
    from apps.sales.models import ServiceSite
    return ServiceSite.objects.create(
        site_code='SITE-001',
        name='Test Rig Site Alpha',
        customer=customer,
        site_type=ServiceSite.SiteType.RIG_SITE,
        status=ServiceSite.Status.ACTIVE,
        address_line1='Ghawar Field',
        city='Dhahran',
        latitude=Decimal('25.5000000'),
        longitude=Decimal('49.5000000'),
        is_active=True
    )


@pytest.fixture
def field_technician(db, field_tech_user):
    """Field technician fixture."""
    from apps.sales.models import FieldTechnician
    return FieldTechnician.objects.create(
        user=field_tech_user,
        employee_id='TECH-001',
        specialization='PDC Bits',
        certification_level='Senior',
        hire_date=date.today() - timedelta(days=365),
        phone='+966501234568',
        is_active=True
    )


@pytest.fixture
def field_service_request(db, customer, service_site, base_user):
    """Field service request fixture."""
    from apps.sales.models import FieldServiceRequest
    return FieldServiceRequest.objects.create(
        request_number='FSR-2024-001',
        customer=customer,
        service_site=service_site,
        request_type=FieldServiceRequest.RequestType.INSPECTION,
        priority=FieldServiceRequest.Priority.NORMAL,
        status=FieldServiceRequest.Status.PENDING,
        requested_date=date.today(),
        description='Routine drill bit inspection',
        created_by=base_user
    )


# Django test client fixtures
@pytest.fixture
def authenticated_client(db, client, base_user):
    """Return an authenticated test client."""
    client.force_login(base_user)
    return client


@pytest.fixture
def staff_client(db, client, staff_user):
    """Return a staff-authenticated test client."""
    client.force_login(staff_user)
    return client


@pytest.fixture
def admin_client(db, client, admin_user):
    """Return an admin-authenticated test client."""
    client.force_login(admin_user)
    return client
