"""
Sprint 5: ServiceSchedule Model Tests
Comprehensive test suite for the ServiceSchedule model
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
    ServiceSchedule
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
def another_technician(db):
    """Create another field technician"""
    return FieldTechnician.objects.create(
        employee_id='TECH002',
        name='Another Technician',
        email='tech2@example.com',
        phone='+0987654321',
        employment_status='ACTIVE',
        skill_level='SENIOR'
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
def service_schedule(db, field_service_request, field_technician, service_site, user):
    """Create a test service schedule"""
    return ServiceSchedule.objects.create(
        service_request=field_service_request,
        technician=field_technician,
        service_site=service_site,
        scheduled_date=date.today() + timedelta(days=7),
        scheduled_start_time=time(9, 0),
        scheduled_end_time=time(12, 0),
        estimated_duration_hours=Decimal('3.00'),
        created_by=user
    )


# =============================================================================
# CREATION TESTS
# =============================================================================

class TestServiceScheduleCreation:
    """Tests for creating ServiceSchedule instances"""

    def test_create_minimal_schedule(self, db, field_service_request, field_technician, service_site, user):
        """Test creating a schedule with required fields"""
        schedule = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=5),
            scheduled_start_time=time(9, 0),
            scheduled_end_time=time(11, 0),
            estimated_duration_hours=Decimal('2.00'),
            created_by=user
        )
        assert schedule.pk is not None
        assert schedule.status == 'DRAFT'

    def test_auto_generate_schedule_number(self, service_schedule):
        """Test that schedule number is auto-generated"""
        year = timezone.now().year
        assert service_schedule.schedule_number.startswith(f'SCH-{year}-')

    def test_schedule_number_format(self, service_schedule):
        """Test schedule number format: SCH-YYYY-####"""
        parts = service_schedule.schedule_number.split('-')
        assert len(parts) == 3
        assert parts[0] == 'SCH'
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4

    def test_str_representation(self, service_schedule):
        """Test string representation"""
        assert service_schedule.schedule_number in str(service_schedule)
        assert str(service_schedule.scheduled_date) in str(service_schedule)

    def test_default_status(self, service_schedule):
        """Test default status is DRAFT"""
        assert service_schedule.status == 'DRAFT'


# =============================================================================
# CONFLICT DETECTION TESTS
# =============================================================================

class TestServiceScheduleConflicts:
    """Tests for schedule conflict detection"""

    def test_no_conflicts_different_dates(self, db, field_service_request, field_technician, service_site, user):
        """Test no conflicts when schedules are on different dates"""
        schedule1 = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=5),
            scheduled_start_time=time(9, 0),
            scheduled_end_time=time(12, 0),
            estimated_duration_hours=Decimal('3.00'),
            status='CONFIRMED',
            created_by=user
        )

        schedule2 = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=6),  # Different date
            scheduled_start_time=time(9, 0),
            scheduled_end_time=time(12, 0),
            estimated_duration_hours=Decimal('3.00'),
            created_by=user
        )

        assert not schedule2.has_conflicts()

    def test_no_conflicts_non_overlapping_times(self, db, field_service_request, field_technician, service_site, user):
        """Test no conflicts when times don't overlap"""
        schedule1 = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=5),
            scheduled_start_time=time(9, 0),
            scheduled_end_time=time(11, 0),
            estimated_duration_hours=Decimal('2.00'),
            status='CONFIRMED',
            created_by=user
        )

        schedule2 = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=5),
            scheduled_start_time=time(13, 0),  # After first ends
            scheduled_end_time=time(15, 0),
            estimated_duration_hours=Decimal('2.00'),
            created_by=user
        )

        assert not schedule2.has_conflicts()

    def test_detects_overlapping_conflict(self, db, field_service_request, field_technician, service_site, user):
        """Test conflict detection for overlapping schedules"""
        schedule1 = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=5),
            scheduled_start_time=time(9, 0),
            scheduled_end_time=time(12, 0),
            estimated_duration_hours=Decimal('3.00'),
            status='CONFIRMED',
            created_by=user
        )

        schedule2 = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=5),
            scheduled_start_time=time(10, 0),  # Overlaps with first
            scheduled_end_time=time(13, 0),
            estimated_duration_hours=Decimal('3.00'),
            created_by=user
        )

        assert schedule2.has_conflicts()
        conflicts = schedule2.check_conflicts()
        assert schedule1 in conflicts

    def test_no_conflicts_different_technicians(self, db, field_service_request, field_technician, another_technician, service_site, user):
        """Test no conflicts when different technicians"""
        schedule1 = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=5),
            scheduled_start_time=time(9, 0),
            scheduled_end_time=time(12, 0),
            estimated_duration_hours=Decimal('3.00'),
            status='CONFIRMED',
            created_by=user
        )

        schedule2 = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=another_technician,  # Different technician
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=5),
            scheduled_start_time=time(9, 0),  # Same time
            scheduled_end_time=time(12, 0),
            estimated_duration_hours=Decimal('3.00'),
            created_by=user
        )

        assert not schedule2.has_conflicts()


# =============================================================================
# PROPERTY TESTS
# =============================================================================

class TestServiceScheduleProperties:
    """Tests for model properties"""

    def test_is_past_for_past_date(self, db, field_service_request, field_technician, service_site, user):
        """Test is_past returns True for past dates"""
        schedule = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=5),
            scheduled_start_time=time(9, 0),
            scheduled_end_time=time(12, 0),
            estimated_duration_hours=Decimal('3.00'),
            created_by=user
        )
        # Update to past date
        ServiceSchedule.objects.filter(pk=schedule.pk).update(
            scheduled_date=date.today() - timedelta(days=1)
        )
        schedule.refresh_from_db()
        assert schedule.is_past is True

    def test_is_today(self, db, field_service_request, field_technician, service_site, user):
        """Test is_today returns True for today's date"""
        schedule = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today(),
            scheduled_start_time=time(9, 0),
            scheduled_end_time=time(12, 0),
            estimated_duration_hours=Decimal('3.00'),
            created_by=user
        )
        assert schedule.is_today is True

    def test_days_until(self, service_schedule):
        """Test days_until calculation"""
        expected_days = 7
        assert service_schedule.days_until == expected_days


# =============================================================================
# STATUS CHECK METHODS TESTS
# =============================================================================

class TestServiceScheduleStatusChecks:
    """Tests for status check methods"""

    def test_can_be_confirmed_from_draft(self, service_schedule):
        """Test can_be_confirmed returns True for draft without conflicts"""
        assert service_schedule.can_be_confirmed() is True

    def test_cannot_be_confirmed_with_conflicts(self, db, field_service_request, field_technician, service_site, user):
        """Test can_be_confirmed returns False with conflicts"""
        # Create confirmed schedule
        ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=5),
            scheduled_start_time=time(9, 0),
            scheduled_end_time=time(12, 0),
            estimated_duration_hours=Decimal('3.00'),
            status='CONFIRMED',
            created_by=user
        )

        # Create overlapping draft
        schedule2 = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=5),
            scheduled_start_time=time(10, 0),
            scheduled_end_time=time(13, 0),
            estimated_duration_hours=Decimal('3.00'),
            created_by=user
        )

        assert schedule2.can_be_confirmed() is False

    def test_can_be_cancelled_from_draft(self, service_schedule):
        """Test can_be_cancelled returns True for draft"""
        assert service_schedule.can_be_cancelled() is True

    def test_cannot_be_cancelled_when_completed(self, service_schedule):
        """Test can_be_cancelled returns False for completed"""
        service_schedule.status = 'COMPLETED'
        service_schedule.save()
        assert service_schedule.can_be_cancelled() is False

    def test_can_be_rescheduled_from_confirmed(self, service_schedule, user):
        """Test can_be_rescheduled returns True for confirmed"""
        service_schedule.confirm_schedule(user)
        assert service_schedule.can_be_rescheduled() is True

    def test_cannot_be_rescheduled_when_completed(self, service_schedule, user):
        """Test can_be_rescheduled returns False for completed"""
        service_schedule.status = 'COMPLETED'
        service_schedule.save()
        assert service_schedule.can_be_rescheduled() is False


# =============================================================================
# WORKFLOW METHODS TESTS
# =============================================================================

class TestServiceScheduleWorkflow:
    """Tests for workflow methods"""

    def test_confirm_schedule(self, service_schedule, user):
        """Test confirm_schedule method"""
        service_schedule.confirm_schedule(user)
        assert service_schedule.status == 'CONFIRMED'
        assert service_schedule.confirmed_by == user
        assert service_schedule.confirmed_at is not None

    def test_confirm_raises_error_with_conflicts(self, db, field_service_request, field_technician, service_site, user):
        """Test confirm_schedule raises error with conflicts"""
        # Create confirmed schedule
        ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=5),
            scheduled_start_time=time(9, 0),
            scheduled_end_time=time(12, 0),
            estimated_duration_hours=Decimal('3.00'),
            status='CONFIRMED',
            created_by=user
        )

        # Try to confirm overlapping schedule
        schedule2 = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=5),
            scheduled_start_time=time(10, 0),
            scheduled_end_time=time(13, 0),
            estimated_duration_hours=Decimal('3.00'),
            created_by=user
        )

        with pytest.raises(ValidationError):
            schedule2.confirm_schedule(user)

    def test_confirm_by_customer(self, service_schedule):
        """Test confirm_by_customer method"""
        service_schedule.confirm_by_customer()
        assert service_schedule.customer_confirmed is True
        assert service_schedule.customer_confirmed_at is not None

    def test_start_service(self, service_schedule, user):
        """Test start_service method"""
        service_schedule.confirm_schedule(user)
        service_schedule.start_service()
        assert service_schedule.status == 'IN_PROGRESS'

    def test_start_service_requires_confirmed(self, service_schedule):
        """Test start_service requires CONFIRMED status"""
        with pytest.raises(ValidationError):
            service_schedule.start_service()

    def test_complete_service(self, service_schedule, user):
        """Test complete_service method"""
        service_schedule.confirm_schedule(user)
        service_schedule.start_service()
        service_schedule.complete_service()
        assert service_schedule.status == 'COMPLETED'

    def test_complete_service_requires_in_progress(self, service_schedule, user):
        """Test complete_service requires IN_PROGRESS status"""
        service_schedule.confirm_schedule(user)
        with pytest.raises(ValidationError):
            service_schedule.complete_service()

    def test_cancel_schedule(self, service_schedule):
        """Test cancel_schedule method"""
        service_schedule.cancel_schedule(reason='Customer cancelled')
        assert service_schedule.status == 'CANCELLED'
        assert 'Customer cancelled' in service_schedule.scheduling_notes

    def test_reschedule(self, service_schedule, user):
        """Test reschedule method"""
        service_schedule.confirm_schedule(user)

        new_date = date.today() + timedelta(days=10)
        new_start = time(14, 0)
        new_end = time(17, 0)

        new_schedule = service_schedule.reschedule(
            new_date=new_date,
            new_start_time=new_start,
            new_end_time=new_end,
            reason='Weather delay',
            user=user
        )

        assert service_schedule.status == 'RESCHEDULED'
        assert service_schedule.rescheduled_to == new_schedule
        assert service_schedule.reschedule_reason == 'Weather delay'

        assert new_schedule.scheduled_date == new_date
        assert new_schedule.scheduled_start_time == new_start
        assert new_schedule.original_schedule == service_schedule
        assert new_schedule.reschedule_count == 1


# =============================================================================
# RELATIONSHIP TESTS
# =============================================================================

class TestServiceScheduleRelationships:
    """Tests for model relationships"""

    def test_service_request_relationship(self, service_schedule, field_service_request):
        """Test service_request relationship"""
        assert service_schedule.service_request == field_service_request
        assert service_schedule in field_service_request.schedules.all()

    def test_technician_relationship(self, service_schedule, field_technician):
        """Test technician relationship"""
        assert service_schedule.technician == field_technician
        assert service_schedule in field_technician.schedules.all()

    def test_service_site_relationship(self, service_schedule, service_site):
        """Test service_site relationship"""
        assert service_schedule.service_site == service_site
        assert service_schedule in service_site.schedules.all()
