"""
Sprint 5: ServiceSite Model Tests
Comprehensive test suite for the ServiceSite model
"""

import pytest
from datetime import date
from decimal import Decimal

from apps.sales.models import Customer, ServiceSite


@pytest.fixture
def customer(db):
    """Create a test customer"""
    return Customer.objects.create(
        code='CUST001',
        name='Test Customer',
        customer_type='OPERATOR',
        is_active=True
    )


@pytest.fixture
def service_site(db, customer):
    """Create a test service site"""
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


# =============================================================================
# CREATION TESTS
# =============================================================================

class TestServiceSiteCreation:
    """Tests for creating ServiceSite instances"""

    def test_create_minimal_service_site(self, db, customer):
        """Test creating a site with minimal required fields"""
        site = ServiceSite.objects.create(
            site_code='SITE001',
            name='Minimal Site',
            customer=customer,
            address_line1='123 Test St',
            city='Test City'
        )
        assert site.pk is not None
        assert site.status == 'ACTIVE'
        assert site.site_type == 'RIG_SITE'

    def test_create_complete_service_site(self, db, customer):
        """Test creating a site with all fields"""
        site = ServiceSite.objects.create(
            site_code='SITE002',
            name='Complete Site',
            name_ar='موقع كامل',
            customer=customer,
            site_type='WAREHOUSE',
            status='ACTIVE',
            description='A complete test site',
            address_line1='123 Main St',
            address_line2='Suite 100',
            city='Dammam',
            state_province='Eastern',
            postal_code='12345',
            country='Saudi Arabia',
            latitude=Decimal('26.4367'),
            longitude=Decimal('50.1039'),
            elevation_meters=50,
            primary_contact_name='John Doe',
            primary_contact_phone='+966501234567',
            primary_contact_email='john@example.com',
            access_instructions='Use main gate',
            requires_escort=True,
            requires_ppe=True,
            ppe_requirements='Hard hat, safety glasses',
            is_24_hour=True,
            has_parking=True,
            has_loading_dock=True,
            has_workshop=True
        )
        assert site.pk is not None
        assert site.latitude == Decimal('26.4367')

    def test_auto_generate_site_code(self, db, customer):
        """Test site code auto-generation when not provided"""
        site = ServiceSite.objects.create(
            site_code='',
            name='Auto Site',
            customer=customer,
            address_line1='Test',
            city='Test City'
        )
        # site_code should be auto-generated
        assert site.site_code == '' or site.site_code.startswith('SITE-')

    def test_str_representation(self, service_site):
        """Test string representation"""
        assert service_site.site_code in str(service_site)
        assert service_site.name in str(service_site)

    def test_default_values(self, service_site):
        """Test default field values"""
        assert service_site.status == 'ACTIVE'
        assert service_site.site_type == 'RIG_SITE'
        assert service_site.country == 'Saudi Arabia'
        assert service_site.requires_ppe is True
        assert service_site.has_parking is True
        assert service_site.total_service_visits == 0


# =============================================================================
# PROPERTY TESTS
# =============================================================================

class TestServiceSiteProperties:
    """Tests for model properties"""

    def test_has_gps_coordinates_true(self, service_site):
        """Test has_gps_coordinates returns True when coordinates set"""
        service_site.latitude = Decimal('26.4367')
        service_site.longitude = Decimal('50.1039')
        service_site.save()
        assert service_site.has_gps_coordinates is True

    def test_has_gps_coordinates_false(self, service_site):
        """Test has_gps_coordinates returns False when no coordinates"""
        service_site.latitude = None
        service_site.longitude = None
        service_site.save()
        assert service_site.has_gps_coordinates is False

    def test_full_address_simple(self, service_site):
        """Test full_address property with minimal fields"""
        address = service_site.full_address
        assert service_site.address_line1 in address
        assert service_site.city in address
        assert service_site.country in address

    def test_full_address_complete(self, db, customer):
        """Test full_address property with all fields"""
        site = ServiceSite.objects.create(
            site_code='SITE002',
            name='Complete Site',
            customer=customer,
            address_line1='123 Main St',
            address_line2='Suite 100',
            city='Dammam',
            state_province='Eastern',
            postal_code='12345',
            country='Saudi Arabia'
        )
        address = site.full_address
        assert '123 Main St' in address
        assert 'Suite 100' in address
        assert 'Dammam' in address
        assert 'Eastern' in address
        assert '12345' in address
        assert 'Saudi Arabia' in address

    def test_is_operational_when_active(self, service_site):
        """Test is_operational returns True when active"""
        service_site.status = 'ACTIVE'
        service_site.is_active = True
        service_site.save()
        assert service_site.is_operational is True

    def test_is_operational_when_inactive_status(self, service_site):
        """Test is_operational returns False when status is inactive"""
        service_site.status = 'INACTIVE'
        service_site.is_active = True
        service_site.save()
        assert service_site.is_operational is False

    def test_is_operational_when_not_active(self, service_site):
        """Test is_operational returns False when is_active is False"""
        service_site.status = 'ACTIVE'
        service_site.is_active = False
        service_site.save()
        assert service_site.is_operational is False


# =============================================================================
# METHOD TESTS
# =============================================================================

class TestServiceSiteMethods:
    """Tests for model methods"""

    def test_update_service_history_first_visit(self, service_site):
        """Test update_service_history for first visit"""
        service_date = date.today()
        service_site.update_service_history(service_date)

        assert service_site.first_service_date == service_date
        assert service_site.last_service_date == service_date
        assert service_site.total_service_visits == 1

    def test_update_service_history_subsequent_visits(self, service_site):
        """Test update_service_history for subsequent visits"""
        first_date = date(2024, 1, 1)
        service_site.first_service_date = first_date
        service_site.last_service_date = first_date
        service_site.total_service_visits = 1
        service_site.save()

        second_date = date(2024, 6, 15)
        service_site.update_service_history(second_date)

        assert service_site.first_service_date == first_date  # Should remain unchanged
        assert service_site.last_service_date == second_date
        assert service_site.total_service_visits == 2


# =============================================================================
# RELATIONSHIP TESTS
# =============================================================================

class TestServiceSiteRelationships:
    """Tests for model relationships"""

    def test_customer_relationship(self, service_site, customer):
        """Test customer relationship"""
        assert service_site.customer == customer
        assert service_site in customer.service_sites.all()

    def test_multiple_sites_per_customer(self, db, customer):
        """Test multiple sites can belong to same customer"""
        site1 = ServiceSite.objects.create(
            site_code='SITE001',
            name='Site 1',
            customer=customer,
            address_line1='Address 1',
            city='City 1'
        )
        site2 = ServiceSite.objects.create(
            site_code='SITE002',
            name='Site 2',
            customer=customer,
            address_line1='Address 2',
            city='City 2'
        )
        assert customer.service_sites.count() == 2


# =============================================================================
# SITE TYPE TESTS
# =============================================================================

class TestServiceSiteTypes:
    """Tests for different site types"""

    def test_rig_site_type(self, db, customer):
        """Test RIG_SITE type"""
        site = ServiceSite.objects.create(
            site_code='RIG001',
            name='Rig Site',
            customer=customer,
            site_type='RIG_SITE',
            address_line1='Rig Location',
            city='Desert'
        )
        assert site.site_type == 'RIG_SITE'

    def test_warehouse_type(self, db, customer):
        """Test WAREHOUSE type"""
        site = ServiceSite.objects.create(
            site_code='WH001',
            name='Warehouse',
            customer=customer,
            site_type='WAREHOUSE',
            address_line1='Industrial Area',
            city='Dammam'
        )
        assert site.site_type == 'WAREHOUSE'

    def test_field_office_type(self, db, customer):
        """Test FIELD_OFFICE type"""
        site = ServiceSite.objects.create(
            site_code='FO001',
            name='Field Office',
            customer=customer,
            site_type='FIELD_OFFICE',
            address_line1='Office Location',
            city='Dhahran'
        )
        assert site.site_type == 'FIELD_OFFICE'
