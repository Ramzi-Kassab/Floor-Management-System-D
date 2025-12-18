"""
Sprint 5: ServiceReport Model Tests
Comprehensive test suite for the ServiceReport model
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
    FieldServiceRequest,
    SiteVisit,
    ServiceReport
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
    visit = SiteVisit.objects.create(
        service_request=field_service_request,
        technician=field_technician,
        service_site=service_site,
        visit_date=date.today(),
        visit_type='SCHEDULED',
        status='COMPLETED',
        visit_successful=True,
        work_performed='Completed drill bit inspection'
    )
    return visit


@pytest.fixture
def service_report(db, field_service_request, site_visit, user):
    """Create a test service report"""
    return ServiceReport.objects.create(
        service_request=field_service_request,
        site_visit=site_visit,
        report_date=date.today(),
        report_title='Drill Bit Inspection Report',
        executive_summary='Completed inspection of drill bit.',
        work_performed_detail='Detailed inspection of drill bit including wear analysis.',
        labor_hours=Decimal('3.00'),
        created_by=user
    )


# =============================================================================
# CREATION TESTS
# =============================================================================

class TestServiceReportCreation:
    """Tests for creating ServiceReport instances"""

    def test_create_minimal_report(self, db, field_service_request, site_visit, user):
        """Test creating a report with required fields"""
        report = ServiceReport.objects.create(
            service_request=field_service_request,
            site_visit=site_visit,
            report_date=date.today(),
            report_title='Test Report',
            executive_summary='Test summary',
            work_performed_detail='Test work details',
            labor_hours=Decimal('2.00'),
            created_by=user
        )
        assert report.pk is not None
        assert report.status == 'DRAFT'

    def test_create_complete_report(self, db, field_service_request, site_visit, user):
        """Test creating a report with all fields"""
        report = ServiceReport.objects.create(
            service_request=field_service_request,
            site_visit=site_visit,
            report_date=date.today(),
            report_title='Complete Service Report',
            executive_summary='Full inspection completed.',
            work_performed_detail='Detailed work performed description.',
            findings='No significant issues found.',
            issues_identified='Minor wear on surface.',
            corrective_actions='Recommended monitoring.',
            recommendations='Schedule follow-up in 30 days.',
            parts_used_detail='O-ring seal x1',
            parts_cost=Decimal('50.00'),
            labor_hours=Decimal('4.00'),
            labor_cost=Decimal('200.00'),
            has_photos=True,
            has_test_results=True,
            created_by=user
        )
        assert report.pk is not None
        assert report.parts_cost == Decimal('50.00')
        assert report.labor_cost == Decimal('200.00')

    def test_auto_generate_report_number(self, service_report):
        """Test that report number is auto-generated"""
        year = timezone.now().year
        assert service_report.report_number.startswith(f'RPT-{year}-')

    def test_report_number_format(self, service_report):
        """Test report number format: RPT-YYYY-####"""
        parts = service_report.report_number.split('-')
        assert len(parts) == 3
        assert parts[0] == 'RPT'
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4

    def test_str_representation(self, service_report):
        """Test string representation"""
        assert service_report.report_number in str(service_report)
        assert service_report.report_title in str(service_report)

    def test_default_status(self, service_report):
        """Test default status is DRAFT"""
        assert service_report.status == 'DRAFT'


# =============================================================================
# COST CALCULATION TESTS
# =============================================================================

class TestServiceReportCostCalculation:
    """Tests for cost calculation methods"""

    def test_calculate_total_cost_parts_and_labor(self, service_report):
        """Test calculate_total_cost with both parts and labor"""
        service_report.parts_cost = Decimal('100.00')
        service_report.labor_cost = Decimal('200.00')
        service_report.save()

        total = service_report.calculate_total_cost()
        assert total == Decimal('300.00')
        assert service_report.total_cost == Decimal('300.00')

    def test_calculate_total_cost_parts_only(self, service_report):
        """Test calculate_total_cost with parts only"""
        service_report.parts_cost = Decimal('100.00')
        service_report.labor_cost = None
        service_report.save()

        total = service_report.calculate_total_cost()
        assert total == Decimal('100.00')

    def test_calculate_total_cost_labor_only(self, service_report):
        """Test calculate_total_cost with labor only"""
        service_report.parts_cost = None
        service_report.labor_cost = Decimal('200.00')
        service_report.save()

        total = service_report.calculate_total_cost()
        assert total == Decimal('200.00')

    def test_calculate_total_cost_none(self, service_report):
        """Test calculate_total_cost with no costs"""
        service_report.parts_cost = None
        service_report.labor_cost = None
        service_report.save()

        total = service_report.calculate_total_cost()
        assert total == Decimal('0.00')


# =============================================================================
# STATUS CHECK METHODS TESTS
# =============================================================================

class TestServiceReportStatusChecks:
    """Tests for status check methods"""

    def test_can_be_submitted_from_draft(self, service_report):
        """Test can_be_submitted returns True for DRAFT"""
        assert service_report.can_be_submitted() is True

    def test_cannot_be_submitted_from_review(self, service_report):
        """Test can_be_submitted returns False for REVIEW"""
        service_report.status = 'REVIEW'
        service_report.save()
        assert service_report.can_be_submitted() is False

    def test_can_be_approved_from_review(self, service_report):
        """Test can_be_approved returns True for REVIEW"""
        service_report.status = 'REVIEW'
        service_report.save()
        assert service_report.can_be_approved() is True

    def test_cannot_be_approved_from_draft(self, service_report):
        """Test can_be_approved returns False for DRAFT"""
        assert service_report.can_be_approved() is False

    def test_can_be_sent_from_approved(self, service_report):
        """Test can_be_sent returns True for APPROVED"""
        service_report.status = 'APPROVED'
        service_report.save()
        assert service_report.can_be_sent() is True

    def test_cannot_be_sent_from_draft(self, service_report):
        """Test can_be_sent returns False for DRAFT"""
        assert service_report.can_be_sent() is False


# =============================================================================
# WORKFLOW METHODS TESTS
# =============================================================================

class TestServiceReportWorkflow:
    """Tests for workflow methods"""

    def test_submit_for_review(self, service_report):
        """Test submit_for_review method"""
        service_report.submit_for_review()

        assert service_report.status == 'REVIEW'
        assert service_report.submitted_for_review_at is not None

    def test_submit_for_review_raises_error_if_not_draft(self, service_report):
        """Test submit_for_review raises error if not DRAFT"""
        service_report.status = 'REVIEW'
        service_report.save()

        with pytest.raises(ValidationError):
            service_report.submit_for_review()

    def test_approve(self, service_report, user):
        """Test approve method"""
        service_report.submit_for_review()
        service_report.approve(user)

        assert service_report.status == 'APPROVED'
        assert service_report.approved_by == user
        assert service_report.approved_at is not None

    def test_approve_raises_error_if_not_review(self, service_report, user):
        """Test approve raises error if not REVIEW"""
        with pytest.raises(ValidationError):
            service_report.approve(user)

    def test_send_to_customer(self, service_report, user):
        """Test send_to_customer method"""
        service_report.submit_for_review()
        service_report.approve(user)
        service_report.send_to_customer(email='customer@example.com')

        assert service_report.status == 'SENT'
        assert service_report.sent_to_customer_at is not None
        assert service_report.customer_email == 'customer@example.com'

    def test_send_to_customer_raises_error_if_not_approved(self, service_report):
        """Test send_to_customer raises error if not APPROVED"""
        with pytest.raises(ValidationError):
            service_report.send_to_customer()

    def test_acknowledge_receipt(self, service_report, user):
        """Test acknowledge_receipt method"""
        service_report.submit_for_review()
        service_report.approve(user)
        service_report.send_to_customer()
        service_report.acknowledge_receipt()

        assert service_report.status == 'ACKNOWLEDGED'
        assert service_report.customer_acknowledged_at is not None

    def test_acknowledge_receipt_raises_error_if_not_sent(self, service_report, user):
        """Test acknowledge_receipt raises error if not SENT"""
        service_report.submit_for_review()
        service_report.approve(user)

        with pytest.raises(ValidationError):
            service_report.acknowledge_receipt()

    def test_archive_from_sent(self, service_report, user):
        """Test archive method from SENT status"""
        service_report.submit_for_review()
        service_report.approve(user)
        service_report.send_to_customer()
        service_report.archive()

        assert service_report.status == 'ARCHIVED'

    def test_archive_from_acknowledged(self, service_report, user):
        """Test archive method from ACKNOWLEDGED status"""
        service_report.submit_for_review()
        service_report.approve(user)
        service_report.send_to_customer()
        service_report.acknowledge_receipt()
        service_report.archive()

        assert service_report.status == 'ARCHIVED'

    def test_archive_raises_error_if_not_sent_or_acknowledged(self, service_report, user):
        """Test archive raises error if not SENT or ACKNOWLEDGED"""
        service_report.submit_for_review()
        service_report.approve(user)

        with pytest.raises(ValidationError):
            service_report.archive()


# =============================================================================
# RELATIONSHIP TESTS
# =============================================================================

class TestServiceReportRelationships:
    """Tests for model relationships"""

    def test_service_request_relationship(self, service_report, field_service_request):
        """Test service_request relationship"""
        assert service_report.service_request == field_service_request
        assert service_report in field_service_request.service_reports.all()

    def test_site_visit_relationship(self, service_report, site_visit):
        """Test site_visit relationship"""
        assert service_report.site_visit == site_visit
        assert service_report in site_visit.service_reports.all()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestServiceReportIntegration:
    """Integration tests for complete workflows"""

    def test_complete_report_workflow(self, service_report, user):
        """Test complete report workflow from draft to archived"""
        # Initially draft
        assert service_report.status == 'DRAFT'

        # Submit for review
        service_report.submit_for_review()
        assert service_report.status == 'REVIEW'

        # Approve
        service_report.approve(user)
        assert service_report.status == 'APPROVED'

        # Send to customer
        service_report.send_to_customer(email='customer@test.com')
        assert service_report.status == 'SENT'

        # Customer acknowledges
        service_report.acknowledge_receipt()
        assert service_report.status == 'ACKNOWLEDGED'

        # Archive
        service_report.archive()
        assert service_report.status == 'ARCHIVED'

    def test_report_with_costs(self, db, field_service_request, site_visit, user):
        """Test report with cost calculations"""
        report = ServiceReport.objects.create(
            service_request=field_service_request,
            site_visit=site_visit,
            report_date=date.today(),
            report_title='Cost Report',
            executive_summary='Service completed.',
            work_performed_detail='Full service.',
            labor_hours=Decimal('5.00'),
            labor_cost=Decimal('250.00'),
            parts_cost=Decimal('150.00'),
            created_by=user
        )

        report.calculate_total_cost()
        assert report.total_cost == Decimal('400.00')
