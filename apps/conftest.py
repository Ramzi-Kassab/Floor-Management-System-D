"""
Sprint 5 Test Fixtures
Shared fixtures for all Sprint 5 tests
"""

import pytest
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user"""
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user"""
    return User.objects.create_superuser(
        username='admin',
        password='adminpass123',
        email='admin@example.com'
    )


@pytest.fixture
def customer(db):
    """Create a test customer"""
    from apps.sales.models import Customer
    return Customer.objects.create(
        code='CUST001',
        name='Test Customer',
        customer_type='OPERATOR',
        is_active=True
    )


@pytest.fixture
def another_customer(db):
    """Create another test customer"""
    from apps.sales.models import Customer
    return Customer.objects.create(
        code='CUST002',
        name='Another Customer',
        customer_type='CONTRACTOR',
        is_active=True
    )


@pytest.fixture
def service_site(db, customer):
    """Create a test service site"""
    from apps.sales.models import ServiceSite
    return ServiceSite.objects.create(
        site_code='SITE001',
        name='Test Service Site',
        customer=customer,
        site_type='RIG_SITE',
        address_line1='123 Test St',
        city='Test City',
        country='Saudi Arabia',
        is_active=True
    )


@pytest.fixture
def field_technician(db, user):
    """Create a test field technician"""
    from apps.sales.models import FieldTechnician
    return FieldTechnician.objects.create(
        employee_id='TECH001',
        user=user,
        name='Test Technician',
        email='tech@example.com',
        phone='+1234567890',
        employment_status='ACTIVE',
        skill_level='INTERMEDIATE'
    )


@pytest.fixture
def drill_bit(db):
    """Create a test drill bit"""
    from apps.workorders.models import DrillBit
    return DrillBit.objects.create(
        serial_number='TEST-DB-001',
        status='AVAILABLE'
    )


@pytest.fixture
def field_service_request(db, customer, service_site, user):
    """Create a test field service request"""
    from apps.sales.models import FieldServiceRequest
    return FieldServiceRequest.objects.create(
        customer=customer,
        service_site=service_site,
        request_type='DRILL_BIT_INSPECTION',
        priority='MEDIUM',
        title='Test Service Request',
        description='Test description for service request',
        requested_date=date.today() + timedelta(days=7),
        contact_person='John Doe',
        contact_phone='+1234567890',
        created_by=user
    )
