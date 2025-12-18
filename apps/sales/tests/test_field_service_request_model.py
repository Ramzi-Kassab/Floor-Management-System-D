"""
Sprint 5: FieldServiceRequest Model Tests
Comprehensive test suite for the FieldServiceRequest model

Test coverage targets:
- Model creation and validation
- Auto-generation of request numbers
- Status transitions and workflow methods
- Properties (is_overdue, is_urgent, etc.)
- Relationships with Customer, ServiceSite, FieldTechnician
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.sales.models import (
    Customer,
    ServiceSite,
    FieldTechnician,
    FieldServiceRequest
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
        country='Saudi Arabia',
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
        description='Test description for service request',
        requested_date=date.today() + timedelta(days=7),
        contact_person='John Doe',
        contact_phone='+1234567890',
        created_by=user
    )


# =============================================================================
# CREATION TESTS
# =============================================================================

class TestFieldServiceRequestCreation:
    """Tests for creating FieldServiceRequest instances"""

    def test_create_minimal_field_service_request(self, db, customer, service_site, user):
        """Test creating a request with minimal required fields"""
        request = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Minimal Request',
            description='Test description',
            requested_date=date.today() + timedelta(days=7),
            contact_person='John Doe',
            contact_phone='+1234567890',
            created_by=user
        )
        assert request.pk is not None
        assert request.status == 'DRAFT'
        assert request.priority == 'MEDIUM'

    def test_create_complete_field_service_request(self, db, customer, service_site, user, field_technician):
        """Test creating a request with all fields populated"""
        request = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type='EMERGENCY_REPAIR',
            priority='URGENT',
            status='APPROVED',
            title='Complete Request',
            description='Full description with all details',
            customer_notes='Customer provided notes',
            requested_date=date.today() + timedelta(days=3),
            requested_time_slot='Morning',
            estimated_duration_hours=Decimal('4.5'),
            flexible_scheduling=True,
            contact_person='Jane Smith',
            contact_phone='+0987654321',
            contact_email='jane@example.com',
            alternate_contact_person='John Backup',
            alternate_contact_phone='+1111111111',
            created_by=user
        )
        assert request.pk is not None
        assert request.priority == 'URGENT'
        assert request.estimated_duration_hours == Decimal('4.5')

    def test_auto_generate_request_number(self, db, customer, service_site, user):
        """Test that request number is auto-generated"""
        request = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Test Request',
            description='Test',
            requested_date=date.today() + timedelta(days=7),
            contact_person='Test',
            contact_phone='123',
            created_by=user
        )
        year = timezone.now().year
        assert request.request_number.startswith(f'FSR-{year}-')

    def test_request_number_format(self, db, customer, service_site, user):
        """Test request number format: FSR-YYYY-####"""
        request = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Test Request',
            description='Test',
            requested_date=date.today() + timedelta(days=7),
            contact_person='Test',
            contact_phone='123',
            created_by=user
        )
        parts = request.request_number.split('-')
        assert len(parts) == 3
        assert parts[0] == 'FSR'
        assert len(parts[1]) == 4  # Year
        assert len(parts[2]) == 4  # Sequential number

    def test_request_number_uniqueness(self, db, customer, service_site, user):
        """Test that request numbers are unique"""
        request1 = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Request 1',
            description='Test',
            requested_date=date.today() + timedelta(days=7),
            contact_person='Test',
            contact_phone='123',
            created_by=user
        )
        request2 = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Request 2',
            description='Test',
            requested_date=date.today() + timedelta(days=7),
            contact_person='Test',
            contact_phone='123',
            created_by=user
        )
        assert request1.request_number != request2.request_number

    def test_sequential_request_numbers(self, db, customer, service_site, user):
        """Test that request numbers increment sequentially"""
        request1 = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Request 1',
            description='Test',
            requested_date=date.today() + timedelta(days=7),
            contact_person='Test',
            contact_phone='123',
            created_by=user
        )
        request2 = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Request 2',
            description='Test',
            requested_date=date.today() + timedelta(days=7),
            contact_person='Test',
            contact_phone='123',
            created_by=user
        )
        num1 = int(request1.request_number.split('-')[-1])
        num2 = int(request2.request_number.split('-')[-1])
        assert num2 == num1 + 1

    def test_str_representation(self, field_service_request):
        """Test string representation"""
        assert field_service_request.customer.name in str(field_service_request)
        assert field_service_request.title in str(field_service_request)

    def test_default_status_is_draft(self, field_service_request):
        """Test that default status is DRAFT"""
        assert field_service_request.status == 'DRAFT'

    def test_default_priority_is_medium(self, db, customer, service_site, user):
        """Test that default priority is MEDIUM"""
        request = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Test Request',
            description='Test',
            requested_date=date.today() + timedelta(days=7),
            contact_person='Test',
            contact_phone='123',
            created_by=user
        )
        assert request.priority == 'MEDIUM'


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestFieldServiceRequestValidation:
    """Tests for model validation"""

    def test_validate_past_requested_date_for_new_request(self, db, customer, service_site, user):
        """Test that past requested date raises validation error for new requests"""
        request = FieldServiceRequest(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Test Request',
            description='Test',
            requested_date=date.today() - timedelta(days=1),
            contact_person='Test',
            contact_phone='123',
            created_by=user
        )
        with pytest.raises(ValidationError) as exc_info:
            request.full_clean()
        assert 'requested_date' in str(exc_info.value)

    def test_validate_technician_on_draft_request(self, db, customer, service_site, user, field_technician):
        """Test that technician cannot be assigned to draft request"""
        request = FieldServiceRequest(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Test Request',
            description='Test',
            requested_date=date.today() + timedelta(days=7),
            contact_person='Test',
            contact_phone='123',
            created_by=user,
            status='DRAFT',
            assigned_technician=field_technician
        )
        with pytest.raises(ValidationError) as exc_info:
            request.full_clean()
        assert 'assigned_technician' in str(exc_info.value)


# =============================================================================
# PROPERTY TESTS
# =============================================================================

class TestFieldServiceRequestProperties:
    """Tests for model properties"""

    def test_is_overdue_future_date(self, field_service_request):
        """Test is_overdue returns False for future dates"""
        field_service_request.requested_date = date.today() + timedelta(days=7)
        field_service_request.save()
        assert field_service_request.is_overdue is False

    def test_is_overdue_past_date(self, db, customer, service_site, user):
        """Test is_overdue returns True for past dates"""
        # Create with future date first
        request = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Test',
            description='Test',
            requested_date=date.today() + timedelta(days=7),
            contact_person='Test',
            contact_phone='123',
            created_by=user
        )
        # Now update to past date (bypassing validation)
        FieldServiceRequest.objects.filter(pk=request.pk).update(
            requested_date=date.today() - timedelta(days=1)
        )
        request.refresh_from_db()
        assert request.is_overdue is True

    def test_is_overdue_completed_request(self, db, customer, service_site, user):
        """Test is_overdue returns False for completed requests"""
        request = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Test',
            description='Test',
            requested_date=date.today() + timedelta(days=7),
            contact_person='Test',
            contact_phone='123',
            created_by=user,
            status='COMPLETED'
        )
        # Update to past date
        FieldServiceRequest.objects.filter(pk=request.pk).update(
            requested_date=date.today() - timedelta(days=1)
        )
        request.refresh_from_db()
        assert request.is_overdue is False

    def test_days_until_service_positive(self, field_service_request):
        """Test days_until_service for future date"""
        field_service_request.requested_date = date.today() + timedelta(days=7)
        field_service_request.save()
        assert field_service_request.days_until_service == 7

    def test_days_until_service_negative(self, db, customer, service_site, user):
        """Test days_until_service for past date"""
        request = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Test',
            description='Test',
            requested_date=date.today() + timedelta(days=7),
            contact_person='Test',
            contact_phone='123',
            created_by=user
        )
        FieldServiceRequest.objects.filter(pk=request.pk).update(
            requested_date=date.today() - timedelta(days=3)
        )
        request.refresh_from_db()
        assert request.days_until_service == -3

    def test_is_urgent_for_urgent_priority(self, field_service_request):
        """Test is_urgent returns True for URGENT priority"""
        field_service_request.priority = 'URGENT'
        assert field_service_request.is_urgent is True

    def test_is_urgent_for_emergency_priority(self, field_service_request):
        """Test is_urgent returns True for EMERGENCY priority"""
        field_service_request.priority = 'EMERGENCY'
        assert field_service_request.is_urgent is True

    def test_is_urgent_for_medium_priority(self, field_service_request):
        """Test is_urgent returns False for MEDIUM priority"""
        field_service_request.priority = 'MEDIUM'
        assert field_service_request.is_urgent is False

    def test_duration_variance_hours(self, field_service_request):
        """Test duration variance calculation"""
        field_service_request.estimated_duration_hours = Decimal('4.0')
        field_service_request.actual_duration_hours = Decimal('5.0')
        field_service_request.save()
        assert field_service_request.duration_variance_hours == Decimal('1.0')

    def test_duration_variance_hours_none_when_incomplete(self, field_service_request):
        """Test duration variance is None when actual is not set"""
        field_service_request.estimated_duration_hours = Decimal('4.0')
        field_service_request.actual_duration_hours = None
        assert field_service_request.duration_variance_hours is None

    def test_duration_variance_percentage(self, field_service_request):
        """Test duration variance percentage calculation"""
        field_service_request.estimated_duration_hours = Decimal('4.0')
        field_service_request.actual_duration_hours = Decimal('5.0')
        field_service_request.save()
        assert field_service_request.duration_variance_percentage == 25.0


# =============================================================================
# STATUS CHECK METHODS TESTS
# =============================================================================

class TestFieldServiceRequestStatusChecks:
    """Tests for status check methods"""

    def test_can_be_submitted_from_draft(self, field_service_request):
        """Test can_be_submitted returns True for draft requests"""
        field_service_request.status = 'DRAFT'
        assert field_service_request.can_be_submitted() is True

    def test_can_be_submitted_from_non_draft(self, field_service_request):
        """Test can_be_submitted returns False for non-draft requests"""
        field_service_request.status = 'SUBMITTED'
        assert field_service_request.can_be_submitted() is False

    def test_can_be_reviewed_from_submitted(self, field_service_request):
        """Test can_be_reviewed returns True for submitted requests"""
        field_service_request.status = 'SUBMITTED'
        assert field_service_request.can_be_reviewed() is True

    def test_can_be_reviewed_from_non_submitted(self, field_service_request):
        """Test can_be_reviewed returns False for non-submitted requests"""
        field_service_request.status = 'DRAFT'
        assert field_service_request.can_be_reviewed() is False

    def test_can_be_approved_from_reviewed(self, field_service_request):
        """Test can_be_approved returns True for reviewed requests"""
        field_service_request.status = 'REVIEWED'
        assert field_service_request.can_be_approved() is True

    def test_can_be_assigned_from_approved(self, field_service_request):
        """Test can_be_assigned returns True for approved requests"""
        field_service_request.status = 'APPROVED'
        assert field_service_request.can_be_assigned() is True

    def test_can_be_started_with_technician(self, field_service_request, field_technician):
        """Test can_be_started returns True when scheduled with technician"""
        field_service_request.status = 'SCHEDULED'
        field_service_request.assigned_technician = field_technician
        assert field_service_request.can_be_started() is True

    def test_can_be_started_without_technician(self, field_service_request):
        """Test can_be_started returns False when no technician assigned"""
        field_service_request.status = 'SCHEDULED'
        field_service_request.assigned_technician = None
        assert field_service_request.can_be_started() is False

    def test_can_be_completed_from_in_progress(self, field_service_request):
        """Test can_be_completed returns True for in-progress requests"""
        field_service_request.status = 'IN_PROGRESS'
        assert field_service_request.can_be_completed() is True

    def test_can_be_cancelled_from_draft(self, field_service_request):
        """Test can_be_cancelled returns True for draft requests"""
        field_service_request.status = 'DRAFT'
        assert field_service_request.can_be_cancelled() is True

    def test_cannot_be_cancelled_when_completed(self, field_service_request):
        """Test can_be_cancelled returns False for completed requests"""
        field_service_request.status = 'COMPLETED'
        assert field_service_request.can_be_cancelled() is False


# =============================================================================
# WORKFLOW METHODS TESTS
# =============================================================================

class TestFieldServiceRequestWorkflow:
    """Tests for workflow methods"""

    def test_submit_method(self, field_service_request):
        """Test submit method changes status to SUBMITTED"""
        field_service_request.status = 'DRAFT'
        field_service_request.save()
        field_service_request.submit()
        assert field_service_request.status == 'SUBMITTED'

    def test_submit_raises_error_when_not_draft(self, field_service_request):
        """Test submit raises error when not in DRAFT status"""
        field_service_request.status = 'SUBMITTED'
        field_service_request.save()
        with pytest.raises(ValidationError):
            field_service_request.submit()

    def test_review_method(self, field_service_request, user):
        """Test review method changes status to REVIEWED"""
        field_service_request.status = 'SUBMITTED'
        field_service_request.save()
        field_service_request.review(user, notes='Review notes')
        assert field_service_request.status == 'REVIEWED'
        assert field_service_request.reviewed_by == user
        assert field_service_request.review_notes == 'Review notes'
        assert field_service_request.reviewed_at is not None

    def test_review_raises_error_when_not_submitted(self, field_service_request, user):
        """Test review raises error when not in SUBMITTED status"""
        field_service_request.status = 'DRAFT'
        field_service_request.save()
        with pytest.raises(ValidationError):
            field_service_request.review(user)

    def test_approve_method(self, field_service_request, user):
        """Test approve method changes status to APPROVED"""
        field_service_request.status = 'REVIEWED'
        field_service_request.save()
        field_service_request.approve(user, notes='Approval notes')
        assert field_service_request.status == 'APPROVED'
        assert field_service_request.approved_by == user
        assert field_service_request.approval_notes == 'Approval notes'
        assert field_service_request.approved_at is not None

    def test_assign_technician_method(self, field_service_request, field_technician, user):
        """Test assign_technician method"""
        field_service_request.status = 'APPROVED'
        field_service_request.save()
        field_service_request.assign_technician(field_technician, user)
        assert field_service_request.status == 'SCHEDULED'
        assert field_service_request.assigned_technician == field_technician
        assert field_service_request.assigned_by == user
        assert field_service_request.assigned_date is not None

    def test_assign_technician_updates_technician_status(self, field_service_request, field_technician, user):
        """Test that assigning technician updates technician's is_currently_assigned"""
        field_service_request.status = 'APPROVED'
        field_service_request.save()
        field_technician.is_currently_assigned = False
        field_technician.save()

        field_service_request.assign_technician(field_technician, user)
        field_technician.refresh_from_db()
        assert field_technician.is_currently_assigned is True

    def test_start_work_method(self, field_service_request, field_technician):
        """Test start_work method"""
        field_service_request.status = 'SCHEDULED'
        field_service_request.assigned_technician = field_technician
        field_service_request.save()
        field_service_request.start_work()
        assert field_service_request.status == 'IN_PROGRESS'
        assert field_service_request.started_at is not None

    def test_complete_work_method(self, field_service_request, field_technician):
        """Test complete_work method"""
        field_service_request.status = 'IN_PROGRESS'
        field_service_request.assigned_technician = field_technician
        field_service_request.started_at = timezone.now() - timedelta(hours=2)
        field_service_request.save()
        field_service_request.complete_work(notes='Work completed successfully')
        assert field_service_request.status == 'COMPLETED'
        assert field_service_request.completed_at is not None
        assert field_service_request.completion_notes == 'Work completed successfully'

    def test_complete_work_calculates_duration(self, field_service_request, field_technician):
        """Test that complete_work calculates actual duration"""
        field_service_request.status = 'IN_PROGRESS'
        field_service_request.assigned_technician = field_technician
        field_service_request.started_at = timezone.now() - timedelta(hours=3)
        field_service_request.save()
        field_service_request.complete_work()
        assert field_service_request.actual_duration_hours is not None
        # Should be approximately 3 hours
        assert float(field_service_request.actual_duration_hours) >= 2.9

    def test_complete_work_releases_technician(self, field_service_request, field_technician):
        """Test that complete_work releases technician"""
        field_service_request.status = 'IN_PROGRESS'
        field_service_request.assigned_technician = field_technician
        field_service_request.started_at = timezone.now()
        field_service_request.save()
        field_technician.is_currently_assigned = True
        field_technician.save()

        field_service_request.complete_work()
        field_technician.refresh_from_db()
        assert field_technician.is_currently_assigned is False

    def test_cancel_method(self, field_service_request, user):
        """Test cancel method"""
        field_service_request.status = 'DRAFT'
        field_service_request.save()
        field_service_request.cancel(user, reason='Customer request')
        assert field_service_request.status == 'CANCELLED'
        assert field_service_request.cancelled_by == user
        assert field_service_request.cancellation_reason == 'Customer request'
        assert field_service_request.cancelled_at is not None

    def test_cancel_raises_error_when_completed(self, field_service_request, user):
        """Test cancel raises error for completed requests"""
        field_service_request.status = 'COMPLETED'
        field_service_request.save()
        with pytest.raises(ValidationError):
            field_service_request.cancel(user)

    def test_cancel_releases_technician(self, field_service_request, field_technician, user):
        """Test that cancel releases assigned technician"""
        field_service_request.status = 'SCHEDULED'
        field_service_request.assigned_technician = field_technician
        field_service_request.save()
        field_technician.is_currently_assigned = True
        field_technician.save()

        field_service_request.cancel(user)
        field_technician.refresh_from_db()
        assert field_technician.is_currently_assigned is False


# =============================================================================
# RELATIONSHIP TESTS
# =============================================================================

class TestFieldServiceRequestRelationships:
    """Tests for model relationships"""

    def test_customer_relationship(self, field_service_request, customer):
        """Test customer relationship"""
        assert field_service_request.customer == customer
        assert field_service_request in customer.field_service_requests.all()

    def test_service_site_relationship(self, field_service_request, service_site):
        """Test service_site relationship"""
        assert field_service_request.service_site == service_site
        assert field_service_request in service_site.service_requests.all()

    def test_assigned_technician_relationship(self, field_service_request, field_technician):
        """Test assigned_technician relationship"""
        field_service_request.assigned_technician = field_technician
        field_service_request.save()
        assert field_service_request in field_technician.assigned_requests.all()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestFieldServiceRequestIntegration:
    """Integration tests for complete workflows"""

    def test_complete_workflow(self, db, customer, service_site, field_technician, user):
        """Test complete workflow from creation to completion"""
        # Create request
        request = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type='DRILL_BIT_INSPECTION',
            title='Full Workflow Test',
            description='Testing complete workflow',
            requested_date=date.today() + timedelta(days=7),
            contact_person='Test User',
            contact_phone='123456789',
            created_by=user
        )
        assert request.status == 'DRAFT'

        # Submit
        request.submit()
        assert request.status == 'SUBMITTED'

        # Review
        request.review(user, notes='Reviewed and looks good')
        assert request.status == 'REVIEWED'

        # Approve
        request.approve(user)
        assert request.status == 'APPROVED'

        # Assign technician
        request.assign_technician(field_technician, user)
        assert request.status == 'SCHEDULED'
        assert field_technician.is_currently_assigned is True

        # Start work
        request.start_work()
        assert request.status == 'IN_PROGRESS'

        # Complete work
        request.complete_work(notes='All inspections completed')
        assert request.status == 'COMPLETED'
        assert request.actual_duration_hours is not None

        # Verify technician is released
        field_technician.refresh_from_db()
        assert field_technician.is_currently_assigned is False
