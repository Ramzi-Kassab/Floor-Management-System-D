"""
Sprint 5: SiteVisit Model Tests
Comprehensive test suite for the SiteVisit model
"""

import pytest
from datetime import date, time, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.sales.models import (
    Customer,
    ServiceSite,
    FieldTechnician,
    FieldServiceRequest,
    SiteVisit
)


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
        is_active=True
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


@pytest.fixture
def user(db, django_user_model):
    """Create a test user"""
    return django_user_model.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )


@pytest.fixture
def field_service_request(db, customer, service_site, user):
    """Create a test field service request"""
    return FieldServiceRequest.objects.create(
        customer=customer,
        service_site=service_site,
        request_type='DRILL_BIT_INSPECTION',
        priority='MEDIUM',
        title='Test Service Request',
        description='Test description',
        requested_date=date.today() + timedelta(days=7),
        contact_person='John Doe',
        contact_phone='+1234567890',
        created_by=user
    )


@pytest.fixture
def site_visit(db, field_service_request, field_technician, service_site):
    """Create a test site visit"""
    return SiteVisit.objects.create(
        service_request=field_service_request,
        technician=field_technician,
        service_site=service_site,
        visit_date=date.today(),
        visit_type='SCHEDULED'
    )


# =============================================================================
# CREATION TESTS
# =============================================================================

class TestSiteVisitCreation:
    """Tests for creating SiteVisit instances"""

    def test_create_minimal_visit(self, db, field_service_request, field_technician, service_site):
        """Test creating a visit with minimal required fields"""
        visit = SiteVisit.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            visit_date=date.today()
        )
        assert visit.pk is not None
        assert visit.status == 'SCHEDULED'
        assert visit.visit_type == 'SCHEDULED'

    def test_auto_generate_visit_number(self, site_visit):
        """Test that visit number is auto-generated"""
        year = timezone.now().year
        assert site_visit.visit_number.startswith(f'VIS-{year}-')

    def test_visit_number_format(self, site_visit):
        """Test visit number format: VIS-YYYY-####"""
        parts = site_visit.visit_number.split('-')
        assert len(parts) == 3
        assert parts[0] == 'VIS'
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4

    def test_str_representation(self, site_visit):
        """Test string representation"""
        assert site_visit.visit_number in str(site_visit)

    def test_default_status(self, site_visit):
        """Test default status is SCHEDULED"""
        assert site_visit.status == 'SCHEDULED'

    def test_default_visit_type(self, site_visit):
        """Test default visit type is SCHEDULED"""
        assert site_visit.visit_type == 'SCHEDULED'


# =============================================================================
# CHECK-IN/CHECK-OUT TESTS
# =============================================================================

class TestSiteVisitCheckInOut:
    """Tests for check-in and check-out functionality"""

    def test_check_in(self, site_visit):
        """Test check_in method"""
        site_visit.check_in()
        assert site_visit.status == 'ARRIVED'
        assert site_visit.check_in_time is not None
        assert site_visit.is_checked_in is True

    def test_check_in_with_gps(self, site_visit):
        """Test check_in with GPS coordinates"""
        site_visit.check_in(latitude=26.4367, longitude=50.1039)
        assert site_visit.check_in_latitude == Decimal('26.4367000')
        assert site_visit.check_in_longitude == Decimal('50.1039000')

    def test_check_in_requires_scheduled_or_en_route(self, site_visit):
        """Test check_in only works from SCHEDULED or EN_ROUTE"""
        site_visit.status = 'IN_PROGRESS'
        site_visit.save()
        with pytest.raises(ValidationError):
            site_visit.check_in()

    def test_check_out(self, site_visit):
        """Test check_out method"""
        site_visit.check_in()
        site_visit.start_work()
        site_visit.check_out(work_performed='Completed inspection')

        assert site_visit.status == 'COMPLETED'
        assert site_visit.check_out_time is not None
        assert site_visit.is_checked_out is True
        assert site_visit.visit_successful is True
        assert site_visit.work_performed == 'Completed inspection'

    def test_check_out_with_gps(self, site_visit):
        """Test check_out with GPS coordinates"""
        site_visit.check_in()
        site_visit.start_work()
        site_visit.check_out(latitude=26.4367, longitude=50.1039)

        assert site_visit.check_out_latitude == Decimal('26.4367000')
        assert site_visit.check_out_longitude == Decimal('50.1039000')

    def test_check_out_calculates_duration(self, site_visit):
        """Test that check_out calculates actual duration"""
        # Manually set check-in time to simulate time passing
        site_visit.check_in_time = timezone.now() - timedelta(hours=2)
        site_visit.status = 'IN_PROGRESS'
        site_visit.save()

        site_visit.check_out()

        assert site_visit.actual_duration_hours is not None
        # Duration should be approximately 2 hours
        assert float(site_visit.actual_duration_hours) >= 1.9

    def test_check_out_requires_arrived_or_in_progress(self, site_visit):
        """Test check_out only works from ARRIVED or IN_PROGRESS"""
        with pytest.raises(ValidationError):
            site_visit.check_out()


# =============================================================================
# PROPERTY TESTS
# =============================================================================

class TestSiteVisitProperties:
    """Tests for model properties"""

    def test_is_checked_in_false_initially(self, site_visit):
        """Test is_checked_in returns False when not checked in"""
        assert site_visit.is_checked_in is False

    def test_is_checked_in_true_after_checkin(self, site_visit):
        """Test is_checked_in returns True after check-in"""
        site_visit.check_in()
        assert site_visit.is_checked_in is True

    def test_is_checked_out_false_initially(self, site_visit):
        """Test is_checked_out returns False when not checked out"""
        assert site_visit.is_checked_out is False

    def test_is_checked_out_true_after_checkout(self, site_visit):
        """Test is_checked_out returns True after check-out"""
        site_visit.check_in()
        site_visit.start_work()
        site_visit.check_out()
        assert site_visit.is_checked_out is True

    def test_duration_minutes(self, site_visit):
        """Test duration_minutes calculation"""
        site_visit.check_in_time = timezone.now() - timedelta(hours=1, minutes=30)
        site_visit.check_out_time = timezone.now()
        site_visit.save()

        # Should be approximately 90 minutes
        assert site_visit.duration_minutes >= 89
        assert site_visit.duration_minutes <= 91

    def test_duration_minutes_none_without_checkout(self, site_visit):
        """Test duration_minutes is None without check-out"""
        site_visit.check_in()
        assert site_visit.duration_minutes is None


# =============================================================================
# STATUS CHECK METHODS TESTS
# =============================================================================

class TestSiteVisitStatusChecks:
    """Tests for status check methods"""

    def test_can_check_in_from_scheduled(self, site_visit):
        """Test can_check_in returns True from SCHEDULED"""
        assert site_visit.can_check_in() is True

    def test_can_check_in_from_en_route(self, site_visit):
        """Test can_check_in returns True from EN_ROUTE"""
        site_visit.status = 'EN_ROUTE'
        site_visit.save()
        assert site_visit.can_check_in() is True

    def test_cannot_check_in_from_in_progress(self, site_visit):
        """Test can_check_in returns False from IN_PROGRESS"""
        site_visit.status = 'IN_PROGRESS'
        site_visit.save()
        assert site_visit.can_check_in() is False

    def test_can_check_out_from_arrived(self, site_visit):
        """Test can_check_out returns True from ARRIVED"""
        site_visit.check_in()
        assert site_visit.can_check_out() is True

    def test_can_check_out_from_in_progress(self, site_visit):
        """Test can_check_out returns True from IN_PROGRESS"""
        site_visit.check_in()
        site_visit.start_work()
        assert site_visit.can_check_out() is True

    def test_cannot_check_out_from_scheduled(self, site_visit):
        """Test can_check_out returns False from SCHEDULED"""
        assert site_visit.can_check_out() is False


# =============================================================================
# WORKFLOW METHODS TESTS
# =============================================================================

class TestSiteVisitWorkflow:
    """Tests for workflow methods"""

    def test_start_work(self, site_visit):
        """Test start_work method"""
        site_visit.check_in()
        site_visit.start_work()
        assert site_visit.status == 'IN_PROGRESS'

    def test_start_work_requires_arrived(self, site_visit):
        """Test start_work requires ARRIVED status"""
        with pytest.raises(ValidationError):
            site_visit.start_work()

    def test_mark_incomplete(self, site_visit):
        """Test mark_incomplete method"""
        site_visit.mark_incomplete(reason='Equipment malfunction')

        assert site_visit.status == 'INCOMPLETE'
        assert site_visit.visit_successful is False
        assert site_visit.follow_up_required is True
        assert site_visit.follow_up_reason == 'Equipment malfunction'

    def test_cancel_visit(self, site_visit):
        """Test cancel method"""
        site_visit.cancel(reason='Weather conditions')

        assert site_visit.status == 'CANCELLED'
        assert 'Weather conditions' in site_visit.issues_found

    def test_cannot_cancel_completed_visit(self, site_visit):
        """Test cannot cancel completed visit"""
        site_visit.check_in()
        site_visit.start_work()
        site_visit.check_out()

        with pytest.raises(ValidationError):
            site_visit.cancel()

    def test_record_customer_signature(self, site_visit):
        """Test record_customer_signature method"""
        site_visit.record_customer_signature(
            signature_name='John Doe',
            rating=5,
            comments='Excellent service'
        )

        assert site_visit.customer_signature == 'John Doe'
        assert site_visit.customer_signed_at is not None
        assert site_visit.customer_satisfaction_rating == 5
        assert site_visit.customer_comments == 'Excellent service'


# =============================================================================
# VISIT TYPE TESTS
# =============================================================================

class TestSiteVisitTypes:
    """Tests for different visit types"""

    def test_scheduled_visit(self, db, field_service_request, field_technician, service_site):
        """Test SCHEDULED visit type"""
        visit = SiteVisit.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            visit_date=date.today(),
            visit_type='SCHEDULED'
        )
        assert visit.visit_type == 'SCHEDULED'

    def test_emergency_visit(self, db, field_service_request, field_technician, service_site):
        """Test EMERGENCY visit type"""
        visit = SiteVisit.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            visit_date=date.today(),
            visit_type='EMERGENCY'
        )
        assert visit.visit_type == 'EMERGENCY'

    def test_follow_up_visit(self, db, field_service_request, field_technician, service_site):
        """Test FOLLOW_UP visit type"""
        visit = SiteVisit.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            visit_date=date.today(),
            visit_type='FOLLOW_UP'
        )
        assert visit.visit_type == 'FOLLOW_UP'


# =============================================================================
# RELATIONSHIP TESTS
# =============================================================================

class TestSiteVisitRelationships:
    """Tests for model relationships"""

    def test_service_request_relationship(self, site_visit, field_service_request):
        """Test service_request relationship"""
        assert site_visit.service_request == field_service_request
        assert site_visit in field_service_request.site_visits.all()

    def test_technician_relationship(self, site_visit, field_technician):
        """Test technician relationship"""
        assert site_visit.technician == field_technician
        assert site_visit in field_technician.site_visits.all()

    def test_service_site_relationship(self, site_visit, service_site):
        """Test service_site relationship"""
        assert site_visit.service_site == service_site
        assert site_visit in service_site.site_visits.all()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestSiteVisitIntegration:
    """Integration tests for complete workflows"""

    def test_complete_visit_workflow(self, site_visit):
        """Test complete visit workflow"""
        # Check in
        site_visit.check_in(latitude=26.4367, longitude=50.1039)
        assert site_visit.status == 'ARRIVED'

        # Start work
        site_visit.start_work()
        assert site_visit.status == 'IN_PROGRESS'

        # Check out
        site_visit.check_out(
            latitude=26.4367,
            longitude=50.1039,
            work_performed='Completed full inspection'
        )
        assert site_visit.status == 'COMPLETED'
        assert site_visit.visit_successful is True

        # Record signature
        site_visit.record_customer_signature(
            signature_name='Customer Rep',
            rating=5,
            comments='Great work'
        )
        assert site_visit.customer_signature == 'Customer Rep'

    def test_incomplete_visit_workflow(self, site_visit):
        """Test incomplete visit workflow"""
        site_visit.check_in()
        site_visit.start_work()
        site_visit.mark_incomplete(reason='Parts not available')

        assert site_visit.status == 'INCOMPLETE'
        assert site_visit.follow_up_required is True
        assert site_visit.visit_successful is False
