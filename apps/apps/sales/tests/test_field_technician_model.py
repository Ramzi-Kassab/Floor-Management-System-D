"""
Sprint 5: FieldTechnician Model Tests
Comprehensive test suite for the FieldTechnician model
"""

import pytest
from decimal import Decimal

from apps.sales.models import Customer, ServiceSite, FieldTechnician


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
        name='Test Site',
        customer=customer,
        address_line1='123 Test St',
        city='Test City'
    )


@pytest.fixture
def field_technician(db):
    """Create a test field technician"""
    return FieldTechnician.objects.create(
        employee_id='TECH001',
        name='Test Technician',
        email='tech@example.com',
        phone='+1234567890',
        employment_status='ACTIVE',
        skill_level='INTERMEDIATE'
    )


# =============================================================================
# CREATION TESTS
# =============================================================================

class TestFieldTechnicianCreation:
    """Tests for creating FieldTechnician instances"""

    def test_create_minimal_technician(self, db):
        """Test creating a technician with minimal required fields"""
        tech = FieldTechnician.objects.create(
            employee_id='TECH001',
            name='John Doe',
            email='john@example.com',
            phone='+1234567890'
        )
        assert tech.pk is not None
        assert tech.employment_status == 'ACTIVE'
        assert tech.skill_level == 'INTERMEDIATE'

    def test_create_complete_technician(self, db):
        """Test creating a technician with all fields"""
        tech = FieldTechnician.objects.create(
            employee_id='TECH002',
            name='Jane Smith',
            name_ar='جين سميث',
            email='jane@example.com',
            phone='+1111111111',
            mobile='+2222222222',
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='+3333333333',
            employment_status='ACTIVE',
            job_title='Senior Technician',
            department='Field Services',
            skill_level='SENIOR',
            specializations='Drill bit inspection, Repair',
            certifications='ISO 9001, Safety',
            can_perform_inspections=True,
            can_perform_repairs=True,
            can_perform_training=True,
            home_base_location='Dammam',
            service_radius_km=200,
            available_for_travel=True,
            has_valid_drivers_license=True,
            has_valid_passport=True
        )
        assert tech.pk is not None
        assert tech.skill_level == 'SENIOR'
        assert tech.service_radius_km == 200

    def test_str_representation(self, field_technician):
        """Test string representation"""
        assert field_technician.employee_id in str(field_technician)
        assert field_technician.name in str(field_technician)

    def test_default_values(self, field_technician):
        """Test default field values"""
        assert field_technician.employment_status == 'ACTIVE'
        assert field_technician.skill_level == 'INTERMEDIATE'
        assert field_technician.service_radius_km == 100
        assert field_technician.is_currently_assigned is False
        assert field_technician.total_service_calls == 0
        assert field_technician.completed_calls == 0


# =============================================================================
# PROPERTY TESTS
# =============================================================================

class TestFieldTechnicianProperties:
    """Tests for model properties"""

    def test_completion_rate_with_calls(self, field_technician):
        """Test completion_rate calculation"""
        field_technician.total_service_calls = 10
        field_technician.completed_calls = 8
        field_technician.save()
        assert field_technician.completion_rate == 80.0

    def test_completion_rate_no_calls(self, field_technician):
        """Test completion_rate with no calls"""
        field_technician.total_service_calls = 0
        field_technician.completed_calls = 0
        field_technician.save()
        assert field_technician.completion_rate is None

    def test_completion_rate_perfect(self, field_technician):
        """Test 100% completion rate"""
        field_technician.total_service_calls = 5
        field_technician.completed_calls = 5
        field_technician.save()
        assert field_technician.completion_rate == 100.0

    def test_is_available_when_active_not_assigned(self, field_technician):
        """Test is_available returns True when active and not assigned"""
        field_technician.employment_status = 'ACTIVE'
        field_technician.is_currently_assigned = False
        field_technician.save()
        assert field_technician.is_available is True

    def test_is_available_when_assigned(self, field_technician):
        """Test is_available returns False when assigned"""
        field_technician.employment_status = 'ACTIVE'
        field_technician.is_currently_assigned = True
        field_technician.save()
        assert field_technician.is_available is False

    def test_is_available_when_on_leave(self, field_technician):
        """Test is_available returns False when on leave"""
        field_technician.employment_status = 'ON_LEAVE'
        field_technician.is_currently_assigned = False
        field_technician.save()
        assert field_technician.is_available is False

    def test_is_available_when_inactive(self, field_technician):
        """Test is_available returns False when inactive"""
        field_technician.employment_status = 'INACTIVE'
        field_technician.is_currently_assigned = False
        field_technician.save()
        assert field_technician.is_available is False


# =============================================================================
# METHOD TESTS
# =============================================================================

class TestFieldTechnicianMethods:
    """Tests for model methods"""

    def test_can_service_site_when_available(self, field_technician, service_site):
        """Test can_service_site returns True when available"""
        field_technician.employment_status = 'ACTIVE'
        field_technician.is_currently_assigned = False
        field_technician.save()
        assert field_technician.can_service_site(service_site) is True

    def test_can_service_site_when_unavailable(self, field_technician, service_site):
        """Test can_service_site returns False when unavailable"""
        field_technician.employment_status = 'ACTIVE'
        field_technician.is_currently_assigned = True
        field_technician.save()
        assert field_technician.can_service_site(service_site) is False

    def test_update_performance_metrics_successful(self, field_technician):
        """Test update_performance_metrics with successful call"""
        field_technician.update_performance_metrics(
            was_successful=True,
            was_on_time=True,
            rating=5
        )
        assert field_technician.total_service_calls == 1
        assert field_technician.completed_calls == 1
        assert field_technician.on_time_percentage == Decimal('100.00')
        assert field_technician.average_rating == Decimal('5')

    def test_update_performance_metrics_unsuccessful(self, field_technician):
        """Test update_performance_metrics with unsuccessful call"""
        field_technician.update_performance_metrics(
            was_successful=False,
            was_on_time=False,
            rating=2
        )
        assert field_technician.total_service_calls == 1
        assert field_technician.completed_calls == 0
        assert field_technician.on_time_percentage == Decimal('0.00')

    def test_update_performance_metrics_multiple_calls(self, db):
        """Test update_performance_metrics with multiple calls"""
        tech = FieldTechnician.objects.create(
            employee_id='TECH003',
            name='Multi Call Tech',
            email='multi@example.com',
            phone='123'
        )

        # First call - successful, on time
        tech.update_performance_metrics(True, True, rating=5)
        assert tech.total_service_calls == 1
        assert tech.completed_calls == 1

        # Second call - successful, late
        tech.update_performance_metrics(True, False, rating=4)
        assert tech.total_service_calls == 2
        assert tech.completed_calls == 2

        # Third call - unsuccessful, late
        tech.update_performance_metrics(False, False, rating=2)
        assert tech.total_service_calls == 3
        assert tech.completed_calls == 2


# =============================================================================
# SKILL LEVEL TESTS
# =============================================================================

class TestFieldTechnicianSkillLevels:
    """Tests for different skill levels"""

    def test_junior_skill_level(self, db):
        """Test JUNIOR skill level"""
        tech = FieldTechnician.objects.create(
            employee_id='JR001',
            name='Junior Tech',
            email='jr@example.com',
            phone='123',
            skill_level='JUNIOR'
        )
        assert tech.skill_level == 'JUNIOR'

    def test_intermediate_skill_level(self, db):
        """Test INTERMEDIATE skill level"""
        tech = FieldTechnician.objects.create(
            employee_id='INT001',
            name='Intermediate Tech',
            email='int@example.com',
            phone='123',
            skill_level='INTERMEDIATE'
        )
        assert tech.skill_level == 'INTERMEDIATE'

    def test_senior_skill_level(self, db):
        """Test SENIOR skill level"""
        tech = FieldTechnician.objects.create(
            employee_id='SR001',
            name='Senior Tech',
            email='sr@example.com',
            phone='123',
            skill_level='SENIOR'
        )
        assert tech.skill_level == 'SENIOR'

    def test_expert_skill_level(self, db):
        """Test EXPERT skill level"""
        tech = FieldTechnician.objects.create(
            employee_id='EXP001',
            name='Expert Tech',
            email='exp@example.com',
            phone='123',
            skill_level='EXPERT'
        )
        assert tech.skill_level == 'EXPERT'


# =============================================================================
# EMPLOYMENT STATUS TESTS
# =============================================================================

class TestFieldTechnicianEmploymentStatus:
    """Tests for different employment statuses"""

    def test_active_status(self, db):
        """Test ACTIVE status"""
        tech = FieldTechnician.objects.create(
            employee_id='ACT001',
            name='Active Tech',
            email='act@example.com',
            phone='123',
            employment_status='ACTIVE'
        )
        assert tech.employment_status == 'ACTIVE'

    def test_on_leave_status(self, db):
        """Test ON_LEAVE status"""
        tech = FieldTechnician.objects.create(
            employee_id='LV001',
            name='On Leave Tech',
            email='leave@example.com',
            phone='123',
            employment_status='ON_LEAVE'
        )
        assert tech.employment_status == 'ON_LEAVE'
        assert tech.is_available is False

    def test_inactive_status(self, db):
        """Test INACTIVE status"""
        tech = FieldTechnician.objects.create(
            employee_id='INACT001',
            name='Inactive Tech',
            email='inact@example.com',
            phone='123',
            employment_status='INACTIVE'
        )
        assert tech.employment_status == 'INACTIVE'
        assert tech.is_available is False

    def test_terminated_status(self, db):
        """Test TERMINATED status"""
        tech = FieldTechnician.objects.create(
            employee_id='TERM001',
            name='Terminated Tech',
            email='term@example.com',
            phone='123',
            employment_status='TERMINATED'
        )
        assert tech.employment_status == 'TERMINATED'
        assert tech.is_available is False


# =============================================================================
# RELATIONSHIP TESTS
# =============================================================================

class TestFieldTechnicianRelationships:
    """Tests for model relationships"""

    def test_current_location_relationship(self, field_technician, service_site):
        """Test current_location relationship"""
        field_technician.current_location = service_site
        field_technician.save()
        assert field_technician.current_location == service_site
        assert field_technician in service_site.current_technicians.all()
