"""
Sprint 5 Smoke Tests - Week 1 Models

Quick validation tests to ensure basic model functionality works.
Tests: creation, __str__, auto-ID generation, one key relationship.

Models tested:
1. ServiceSite
2. FieldTechnician
3. FieldServiceRequest
4. ServiceSchedule
5. SiteVisit
6. ServiceReport

Author: Sprint 5 Smoke Test Suite
Date: December 2024
"""

import pytest
from decimal import Decimal
from datetime import date, time, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.sales.models import (
    Customer,
    ServiceSite,
    FieldTechnician,
    FieldServiceRequest,
    ServiceSchedule,
    SiteVisit,
    ServiceReport,
)

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def user(db):
    """Create test user"""
    return User.objects.create_user(
        username='smoketest',
        password='testpass123',
        email='smoke@test.com'
    )


@pytest.fixture
def customer(db):
    """Create test customer"""
    return Customer.objects.create(
        code="SMOKE001",
        name="Smoke Test Customer",
        customer_type="OPERATOR",
        is_active=True
    )


@pytest.fixture
def service_site(db, customer):
    """Create test service site"""
    return ServiceSite.objects.create(
        customer=customer,
        name="Smoke Test Site",
        site_type=ServiceSite.SiteType.RIG_SITE,
        status=ServiceSite.Status.ACTIVE,
        address_line1="123 Test St",
        city="Test City",
        country="Saudi Arabia"
    )


@pytest.fixture
def field_technician(db, user):
    """Create test field technician"""
    return FieldTechnician.objects.create(
        user=user,
        employee_id="TECH001",
        name="Smoke Tester",
        skill_level=FieldTechnician.SkillLevel.SENIOR,
        employment_status=FieldTechnician.EmploymentStatus.ACTIVE
    )


@pytest.fixture
def field_service_request(db, customer, service_site, field_technician):
    """Create test field service request"""
    return FieldServiceRequest.objects.create(
        customer=customer,
        service_site=service_site,
        assigned_technician=field_technician,
        request_type=FieldServiceRequest.RequestType.DRILL_BIT_INSPECTION,
        priority=FieldServiceRequest.Priority.MEDIUM,
        status=FieldServiceRequest.Status.APPROVED,
        title="Smoke test request",
        description="Description for smoke test",
        requested_date=date.today() + timedelta(days=7),
        contact_person="John Doe",
        contact_phone="+966501234567"
    )


@pytest.fixture
def service_schedule(db, field_service_request, service_site, field_technician):
    """Create test service schedule"""
    return ServiceSchedule.objects.create(
        service_request=field_service_request,
        technician=field_technician,
        service_site=service_site,
        scheduled_date=date.today() + timedelta(days=7),
        scheduled_start_time=time(9, 0),
        scheduled_end_time=time(12, 0),
        estimated_duration_hours=Decimal("3.0"),
        status=ServiceSchedule.Status.DRAFT
    )


@pytest.fixture
def site_visit(db, field_service_request, service_site, field_technician):
    """Create test site visit"""
    return SiteVisit.objects.create(
        service_request=field_service_request,
        service_site=service_site,
        technician=field_technician,
        visit_type=SiteVisit.VisitType.SCHEDULED,
        status=SiteVisit.Status.SCHEDULED,
        visit_date=date.today()
    )


@pytest.fixture
def service_report(db, field_service_request, site_visit):
    """Create test service report"""
    return ServiceReport.objects.create(
        service_request=field_service_request,
        site_visit=site_visit,
        report_date=date.today(),
        report_title="Smoke Test Service Report",
        executive_summary="This is a smoke test report",
        work_performed_detail="Work details for smoke test",
        labor_hours=Decimal("3.0"),
        status=ServiceReport.Status.DRAFT
    )


# =============================================================================
# SERVICE SITE SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestServiceSiteSmoke:
    """Smoke tests for ServiceSite model"""

    @pytest.mark.django_db
    def test_creation(self, customer):
        """Smoke test: Model can be created"""
        site = ServiceSite.objects.create(
            customer=customer,
            name="Test Site",
            site_type=ServiceSite.SiteType.WAREHOUSE,
            address_line1="456 Warehouse Ave",
            city="Riyadh"
        )
        assert site.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, service_site):
        """Smoke test: __str__ works"""
        result = str(service_site)
        assert "SITE-" in result or "Smoke Test Site" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, customer):
        """Smoke test: Auto-generated site_code works"""
        site = ServiceSite.objects.create(
            customer=customer,
            name="Auto ID Test Site",
            address_line1="789 Auto St",
            city="Jeddah"
        )
        assert site.site_code.startswith("SITE-")

    @pytest.mark.django_db
    def test_customer_relationship(self, service_site, customer):
        """Smoke test: Customer relationship works"""
        assert service_site.customer == customer
        assert service_site in customer.service_sites.all()


# =============================================================================
# FIELD TECHNICIAN SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestFieldTechnicianSmoke:
    """Smoke tests for FieldTechnician model"""

    @pytest.mark.django_db
    def test_creation(self, user):
        """Smoke test: Model can be created"""
        tech = FieldTechnician.objects.create(
            user=user,
            employee_id="TECH002",
            name="Test Tech",
            skill_level=FieldTechnician.SkillLevel.INTERMEDIATE,
            employment_status=FieldTechnician.EmploymentStatus.ACTIVE
        )
        assert tech.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, field_technician):
        """Smoke test: __str__ works"""
        result = str(field_technician)
        assert "TECH001" in result or "Smoke Tester" in result

    @pytest.mark.django_db
    def test_user_relationship(self, field_technician, user):
        """Smoke test: User relationship works"""
        assert field_technician.user == user
        assert hasattr(user, 'field_technician_profile')


# =============================================================================
# FIELD SERVICE REQUEST SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestFieldServiceRequestSmoke:
    """Smoke tests for FieldServiceRequest model"""

    @pytest.mark.django_db
    def test_creation(self, customer, service_site):
        """Smoke test: Model can be created"""
        request = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type=FieldServiceRequest.RequestType.DRILL_BIT_REPAIR,
            priority=FieldServiceRequest.Priority.HIGH,
            title="Test repair request",
            description="Test description",
            requested_date=date.today() + timedelta(days=14),
            contact_person="Jane Doe",
            contact_phone="+966509876543"
        )
        assert request.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, field_service_request):
        """Smoke test: __str__ works"""
        result = str(field_service_request)
        assert "FSR-" in result or "Smoke test request" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, customer, service_site):
        """Smoke test: Auto-generated request_number works"""
        request = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type=FieldServiceRequest.RequestType.EMERGENCY_REPAIR,
            title="Auto ID test",
            description="Test",
            requested_date=date.today(),
            contact_person="Test",
            contact_phone="+966500000000"
        )
        assert request.request_number.startswith("FSR-")

    @pytest.mark.django_db
    def test_customer_relationship(self, field_service_request, customer):
        """Smoke test: Customer relationship works"""
        assert field_service_request.customer == customer
        assert field_service_request in customer.field_service_requests.all()


# =============================================================================
# SERVICE SCHEDULE SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestServiceScheduleSmoke:
    """Smoke tests for ServiceSchedule model"""

    @pytest.mark.django_db
    def test_creation(self, field_service_request, field_technician, service_site):
        """Smoke test: Model can be created"""
        schedule = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=14),
            scheduled_start_time=time(14, 0),
            scheduled_end_time=time(17, 0),
            estimated_duration_hours=Decimal("3.0")
        )
        assert schedule.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, service_schedule):
        """Smoke test: __str__ works"""
        result = str(service_schedule)
        assert "SCH-" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, field_service_request, field_technician, service_site):
        """Smoke test: Auto-generated schedule_number works"""
        schedule = ServiceSchedule.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            scheduled_date=date.today() + timedelta(days=21),
            scheduled_start_time=time(8, 0),
            scheduled_end_time=time(10, 0),
            estimated_duration_hours=Decimal("2.0")
        )
        assert schedule.schedule_number.startswith("SCH-")
        year = timezone.now().year
        assert str(year) in schedule.schedule_number

    @pytest.mark.django_db
    def test_technician_relationship(self, service_schedule, field_technician):
        """Smoke test: Technician relationship works"""
        assert service_schedule.technician == field_technician
        assert service_schedule in field_technician.schedules.all()


# =============================================================================
# SITE VISIT SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestSiteVisitSmoke:
    """Smoke tests for SiteVisit model"""

    @pytest.mark.django_db
    def test_creation(self, field_service_request, field_technician, service_site):
        """Smoke test: Model can be created"""
        visit = SiteVisit.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            visit_type=SiteVisit.VisitType.EMERGENCY,
            status=SiteVisit.Status.SCHEDULED,
            visit_date=date.today()
        )
        assert visit.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, site_visit):
        """Smoke test: __str__ works"""
        result = str(site_visit)
        assert "VIS-" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, field_service_request, field_technician, service_site):
        """Smoke test: Auto-generated visit_number works"""
        visit = SiteVisit.objects.create(
            service_request=field_service_request,
            technician=field_technician,
            service_site=service_site,
            visit_type=SiteVisit.VisitType.FOLLOW_UP,
            visit_date=date.today() + timedelta(days=1)
        )
        assert visit.visit_number.startswith("VIS-")
        year = timezone.now().year
        assert str(year) in visit.visit_number

    @pytest.mark.django_db
    def test_service_request_relationship(self, site_visit, field_service_request):
        """Smoke test: FieldServiceRequest relationship works"""
        assert site_visit.service_request == field_service_request
        assert site_visit in field_service_request.site_visits.all()


# =============================================================================
# SERVICE REPORT SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestServiceReportSmoke:
    """Smoke tests for ServiceReport model"""

    @pytest.mark.django_db
    def test_creation(self, field_service_request, site_visit):
        """Smoke test: Model can be created"""
        report = ServiceReport.objects.create(
            service_request=field_service_request,
            site_visit=site_visit,
            report_date=date.today(),
            report_title="Test Report",
            executive_summary="Summary",
            work_performed_detail="Details",
            labor_hours=Decimal("4.0")
        )
        assert report.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, service_report):
        """Smoke test: __str__ works"""
        result = str(service_report)
        assert "RPT-" in result or "Smoke Test Service Report" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, field_service_request, site_visit):
        """Smoke test: Auto-generated report_number works"""
        report = ServiceReport.objects.create(
            service_request=field_service_request,
            site_visit=site_visit,
            report_date=date.today(),
            report_title="Auto ID Test Report",
            executive_summary="Testing auto ID generation",
            work_performed_detail="Test work",
            labor_hours=Decimal("2.5")
        )
        assert report.report_number.startswith("RPT-")
        year = timezone.now().year
        assert str(year) in report.report_number

    @pytest.mark.django_db
    def test_site_visit_relationship(self, service_report, site_visit):
        """Smoke test: SiteVisit relationship works"""
        assert service_report.site_visit == site_visit
        assert service_report in site_visit.service_reports.all()
