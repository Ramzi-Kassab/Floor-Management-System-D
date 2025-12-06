"""
Sprint 5 Smoke Tests - All 18 Models

Quick validation tests to ensure basic model functionality works.
Tests: creation, __str__, auto-ID generation, one key relationship.

Week 1 Models (6):
1. ServiceSite
2. FieldTechnician
3. FieldServiceRequest
4. ServiceSchedule
5. SiteVisit
6. ServiceReport

Week 2 Models (6):
7. FieldDrillStringRun
8. FieldRunData
9. FieldPerformanceLog
10. FieldInspection
11. RunHours
12. FieldIncident

Week 3 Models (6):
13. FieldDataEntry
14. FieldPhoto
15. FieldDocument
16. GPSLocation
17. FieldWorkOrder
18. FieldAssetAssignment

Author: Sprint 5 Smoke Test Suite
Date: December 2024
"""

import pytest
from decimal import Decimal
from datetime import date, time, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.sales.models import (
    # Base models
    Customer,
    Well,
    # Week 1 models
    ServiceSite,
    FieldTechnician,
    FieldServiceRequest,
    ServiceSchedule,
    SiteVisit,
    ServiceReport,
    # Week 2 models
    FieldDrillStringRun,
    FieldRunData,
    FieldPerformanceLog,
    FieldInspection,
    RunHours,
    FieldIncident,
    # Week 3 models
    FieldDataEntry,
    FieldPhoto,
    FieldDocument,
    GPSLocation,
    FieldWorkOrder,
    FieldAssetAssignment,
)
from apps.workorders.models import DrillBit

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
def well(db, customer):
    """Create test well"""
    return Well.objects.create(
        customer=customer,
        code="WELL-SMOKE-001",
        name="Smoke Test Well #1",
        is_active=True
    )


@pytest.fixture
def drill_bit(db):
    """Create test drill bit"""
    return DrillBit.objects.create(
        serial_number="SN-SMOKE-001",
        bit_type="PDC",
        size=Decimal("8.500"),
        status="AVAILABLE"
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


@pytest.fixture
def field_run(db, drill_bit, well, customer):
    """Create test field drill string run"""
    return FieldDrillStringRun.objects.create(
        drill_bit=drill_bit,
        well=well,
        customer=customer,
        run_type=FieldDrillStringRun.RunType.PRODUCTION,
        status=FieldDrillStringRun.Status.PLANNED
    )


# =============================================================================
# WEEK 1: SERVICE SITE SMOKE TESTS
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
# WEEK 1: FIELD TECHNICIAN SMOKE TESTS
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
# WEEK 1: FIELD SERVICE REQUEST SMOKE TESTS
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
# WEEK 1: SERVICE SCHEDULE SMOKE TESTS
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
# WEEK 1: SITE VISIT SMOKE TESTS
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
# WEEK 1: SERVICE REPORT SMOKE TESTS
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


# =============================================================================
# WEEK 2: FIELD DRILL STRING RUN SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestFieldDrillStringRunSmoke:
    """Smoke tests for FieldDrillStringRun model"""

    @pytest.mark.django_db
    def test_creation(self, drill_bit, well, customer):
        """Smoke test: Model can be created"""
        run = FieldDrillStringRun.objects.create(
            drill_bit=drill_bit,
            well=well,
            customer=customer,
            run_type=FieldDrillStringRun.RunType.SURFACE,
            status=FieldDrillStringRun.Status.PLANNED
        )
        assert run.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, field_run):
        """Smoke test: __str__ works"""
        result = str(field_run)
        assert "RUN-" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, drill_bit, well, customer):
        """Smoke test: Auto-generated run_number works"""
        run = FieldDrillStringRun.objects.create(
            drill_bit=drill_bit,
            well=well,
            customer=customer
        )
        assert run.run_number.startswith("RUN-")

    @pytest.mark.django_db
    def test_drill_bit_relationship(self, field_run, drill_bit):
        """Smoke test: DrillBit relationship works"""
        assert field_run.drill_bit == drill_bit
        assert field_run in drill_bit.field_runs.all()


# =============================================================================
# WEEK 2: FIELD RUN DATA SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestFieldRunDataSmoke:
    """Smoke tests for FieldRunData model"""

    @pytest.mark.django_db
    def test_creation(self, field_run):
        """Smoke test: Model can be created"""
        data = FieldRunData.objects.create(
            field_run=field_run,
            timestamp=timezone.now(),
            bit_depth=Decimal("5000.00")
        )
        assert data.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, field_run):
        """Smoke test: __str__ works"""
        data = FieldRunData.objects.create(
            field_run=field_run,
            timestamp=timezone.now(),
            bit_depth=Decimal("5000.00")
        )
        result = str(data)
        assert result is not None

    @pytest.mark.django_db
    def test_field_run_relationship(self, field_run):
        """Smoke test: FieldDrillStringRun relationship works"""
        data = FieldRunData.objects.create(
            field_run=field_run,
            timestamp=timezone.now(),
            bit_depth=Decimal("5000.00")
        )
        assert data.field_run == field_run
        assert data in field_run.run_data_points.all()


# =============================================================================
# WEEK 2: FIELD PERFORMANCE LOG SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestFieldPerformanceLogSmoke:
    """Smoke tests for FieldPerformanceLog model"""

    @pytest.mark.django_db
    def test_creation(self, field_run):
        """Smoke test: Model can be created"""
        log = FieldPerformanceLog.objects.create(
            field_run=field_run,
            interval_type=FieldPerformanceLog.IntervalType.DAILY,
            start_time=timezone.now() - timedelta(hours=8),
            end_time=timezone.now(),
            start_depth=Decimal("4500.00"),
            end_depth=Decimal("5000.00"),
            footage_drilled=Decimal("500.00"),
            rotating_hours=Decimal("6.5"),
            on_bottom_hours=Decimal("5.0"),
            avg_rop=Decimal("76.92")
        )
        assert log.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, field_run):
        """Smoke test: __str__ works"""
        log = FieldPerformanceLog.objects.create(
            field_run=field_run,
            interval_type=FieldPerformanceLog.IntervalType.DAILY,
            start_time=timezone.now() - timedelta(hours=8),
            end_time=timezone.now(),
            start_depth=Decimal("4500.00"),
            end_depth=Decimal("5000.00"),
            footage_drilled=Decimal("500.00"),
            rotating_hours=Decimal("6.5"),
            on_bottom_hours=Decimal("5.0"),
            avg_rop=Decimal("76.92")
        )
        result = str(log)
        assert "PERF-" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, field_run):
        """Smoke test: Auto-generated log_number works"""
        log = FieldPerformanceLog.objects.create(
            field_run=field_run,
            interval_type=FieldPerformanceLog.IntervalType.SHIFT,
            start_time=timezone.now() - timedelta(hours=4),
            end_time=timezone.now(),
            start_depth=Decimal("5000.00"),
            end_depth=Decimal("5200.00"),
            footage_drilled=Decimal("200.00"),
            rotating_hours=Decimal("3.0"),
            on_bottom_hours=Decimal("2.5"),
            avg_rop=Decimal("80.00")
        )
        assert log.log_number.startswith("PERF-")


# =============================================================================
# WEEK 2: FIELD INSPECTION SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestFieldInspectionSmoke:
    """Smoke tests for FieldInspection model"""

    @pytest.mark.django_db
    def test_creation(self, drill_bit):
        """Smoke test: Model can be created"""
        inspection = FieldInspection.objects.create(
            drill_bit=drill_bit,
            inspection_type=FieldInspection.InspectionType.POST_RUN,
            status=FieldInspection.Status.SCHEDULED,
            inspection_date=date.today()
        )
        assert inspection.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, drill_bit):
        """Smoke test: __str__ works"""
        inspection = FieldInspection.objects.create(
            drill_bit=drill_bit,
            inspection_date=date.today()
        )
        result = str(inspection)
        assert "INSP-" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, drill_bit):
        """Smoke test: Auto-generated inspection_number works"""
        inspection = FieldInspection.objects.create(
            drill_bit=drill_bit,
            inspection_date=date.today()
        )
        assert inspection.inspection_number.startswith("INSP-")

    @pytest.mark.django_db
    def test_drill_bit_relationship(self, drill_bit):
        """Smoke test: DrillBit relationship works"""
        inspection = FieldInspection.objects.create(
            drill_bit=drill_bit,
            inspection_date=date.today()
        )
        assert inspection.drill_bit == drill_bit
        assert inspection in drill_bit.field_inspections.all()


# =============================================================================
# WEEK 2: RUN HOURS SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestRunHoursSmoke:
    """Smoke tests for RunHours model"""

    @pytest.mark.django_db
    def test_creation(self, drill_bit):
        """Smoke test: Model can be created"""
        hours = RunHours.objects.create(
            drill_bit=drill_bit,
            hour_type=RunHours.HourType.ROTATING,
            hours=Decimal("8.5"),
            record_date=date.today()
        )
        assert hours.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, drill_bit):
        """Smoke test: __str__ works"""
        hours = RunHours.objects.create(
            drill_bit=drill_bit,
            hours=Decimal("8.5"),
            record_date=date.today()
        )
        result = str(hours)
        assert result is not None

    @pytest.mark.django_db
    def test_drill_bit_relationship(self, drill_bit):
        """Smoke test: DrillBit relationship works"""
        hours = RunHours.objects.create(
            drill_bit=drill_bit,
            hours=Decimal("8.5"),
            record_date=date.today()
        )
        assert hours.drill_bit == drill_bit
        assert hours in drill_bit.hour_logs.all()


# =============================================================================
# WEEK 2: FIELD INCIDENT SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestFieldIncidentSmoke:
    """Smoke tests for FieldIncident model"""

    @pytest.mark.django_db
    def test_creation(self, field_technician):
        """Smoke test: Model can be created"""
        incident = FieldIncident.objects.create(
            reported_by=field_technician,
            category=FieldIncident.IncidentCategory.NEAR_MISS,
            severity=FieldIncident.Severity.MINOR,
            incident_title="Smoke test incident",
            incident_date=date.today()
        )
        assert incident.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, field_technician):
        """Smoke test: __str__ works"""
        incident = FieldIncident.objects.create(
            reported_by=field_technician,
            incident_title="Smoke test incident",
            incident_date=date.today()
        )
        result = str(incident)
        assert "INC-" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, field_technician):
        """Smoke test: Auto-generated incident_number works"""
        incident = FieldIncident.objects.create(
            reported_by=field_technician,
            incident_title="Auto ID test incident",
            incident_date=date.today()
        )
        assert incident.incident_number.startswith("INC-")


# =============================================================================
# WEEK 3: FIELD DATA ENTRY SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestFieldDataEntrySmoke:
    """Smoke tests for FieldDataEntry model"""

    @pytest.mark.django_db
    def test_creation(self, field_technician):
        """Smoke test: Model can be created"""
        entry = FieldDataEntry.objects.create(
            entered_by=field_technician,
            data_type=FieldDataEntry.DataType.NUMERIC,
            category=FieldDataEntry.EntryCategory.MEASUREMENT,
            field_name="WOB Reading",
            value_numeric=Decimal("25.5"),
            entry_date=date.today()
        )
        assert entry.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, field_technician):
        """Smoke test: __str__ works"""
        entry = FieldDataEntry.objects.create(
            entered_by=field_technician,
            field_name="WOB Reading",
            entry_date=date.today()
        )
        result = str(entry)
        assert "DATA-" in result or "WOB Reading" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, field_technician):
        """Smoke test: Auto-generated entry_number works"""
        entry = FieldDataEntry.objects.create(
            entered_by=field_technician,
            field_name="RPM Reading",
            entry_date=date.today()
        )
        assert entry.entry_number.startswith("DATA-")


# =============================================================================
# WEEK 3: FIELD PHOTO SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestFieldPhotoSmoke:
    """Smoke tests for FieldPhoto model"""

    @pytest.mark.django_db
    def test_creation(self, field_technician):
        """Smoke test: Model can be created"""
        photo = FieldPhoto.objects.create(
            taken_by=field_technician,
            category=FieldPhoto.PhotoCategory.EQUIPMENT,
            title="Smoke test photo",
            taken_at=timezone.now()
        )
        assert photo.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, field_technician):
        """Smoke test: __str__ works"""
        photo = FieldPhoto.objects.create(
            taken_by=field_technician,
            title="Smoke test photo",
            taken_at=timezone.now()
        )
        result = str(photo)
        assert "PHOTO-" in result or "Smoke test photo" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, field_technician):
        """Smoke test: Auto-generated photo_number works"""
        photo = FieldPhoto.objects.create(
            taken_by=field_technician,
            taken_at=timezone.now()
        )
        assert photo.photo_number.startswith("PHOTO-")


# =============================================================================
# WEEK 3: FIELD DOCUMENT SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestFieldDocumentSmoke:
    """Smoke tests for FieldDocument model"""

    @pytest.mark.django_db
    def test_creation(self, user):
        """Smoke test: Model can be created"""
        doc = FieldDocument.objects.create(
            document_type=FieldDocument.DocumentType.REPORT,
            title="Smoke Test Report",
            document_date=date.today(),
            created_by=user
        )
        assert doc.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, user):
        """Smoke test: __str__ works"""
        doc = FieldDocument.objects.create(
            title="Smoke Test Report",
            document_date=date.today(),
            created_by=user
        )
        result = str(doc)
        assert "DOC-" in result or "Smoke Test Report" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, user):
        """Smoke test: Auto-generated document_number works"""
        doc = FieldDocument.objects.create(
            title="Auto ID Test Report",
            document_date=date.today(),
            created_by=user
        )
        assert doc.document_number.startswith("DOC-")


# =============================================================================
# WEEK 3: GPS LOCATION SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestGPSLocationSmoke:
    """Smoke tests for GPSLocation model"""

    @pytest.mark.django_db
    def test_creation(self, field_technician):
        """Smoke test: Model can be created"""
        location = GPSLocation.objects.create(
            field_technician=field_technician,
            latitude=Decimal("29.7604"),
            longitude=Decimal("-95.3698"),
            recorded_at=timezone.now()
        )
        assert location.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, field_technician):
        """Smoke test: __str__ works"""
        location = GPSLocation.objects.create(
            field_technician=field_technician,
            latitude=Decimal("29.7604"),
            longitude=Decimal("-95.3698"),
            recorded_at=timezone.now()
        )
        result = str(location)
        assert result is not None

    @pytest.mark.django_db
    def test_technician_relationship(self, field_technician):
        """Smoke test: FieldTechnician relationship works"""
        location = GPSLocation.objects.create(
            field_technician=field_technician,
            latitude=Decimal("29.7604"),
            longitude=Decimal("-95.3698"),
            recorded_at=timezone.now()
        )
        assert location.field_technician == field_technician
        assert location in field_technician.gps_locations.all()


# =============================================================================
# WEEK 3: FIELD WORK ORDER SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestFieldWorkOrderSmoke:
    """Smoke tests for FieldWorkOrder model"""

    @pytest.mark.django_db
    def test_creation(self, customer, service_site):
        """Smoke test: Model can be created"""
        wo = FieldWorkOrder.objects.create(
            service_site=service_site,
            customer=customer,
            work_type=FieldWorkOrder.WorkType.MAINTENANCE,
            title="Smoke test work order",
            description="Test description"
        )
        assert wo.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, customer, service_site):
        """Smoke test: __str__ works"""
        wo = FieldWorkOrder.objects.create(
            service_site=service_site,
            customer=customer,
            title="Smoke test work order",
            description="Test description"
        )
        result = str(wo)
        assert "FWO-" in result or "Smoke test work order" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, customer, service_site):
        """Smoke test: Auto-generated work_order_number works"""
        wo = FieldWorkOrder.objects.create(
            service_site=service_site,
            customer=customer,
            title="Auto ID test",
            description="Test"
        )
        assert wo.work_order_number.startswith("FWO-")

    @pytest.mark.django_db
    def test_customer_relationship(self, customer, service_site):
        """Smoke test: Customer relationship works"""
        wo = FieldWorkOrder.objects.create(
            service_site=service_site,
            customer=customer,
            title="Test WO",
            description="Test"
        )
        assert wo.customer == customer
        assert wo in customer.field_work_orders.all()


# =============================================================================
# WEEK 3: FIELD ASSET ASSIGNMENT SMOKE TESTS
# =============================================================================

@pytest.mark.smoke
class TestFieldAssetAssignmentSmoke:
    """Smoke tests for FieldAssetAssignment model"""

    @pytest.mark.django_db
    def test_creation(self, field_technician, user):
        """Smoke test: Model can be created"""
        assignment = FieldAssetAssignment.objects.create(
            assigned_to=field_technician,
            checked_out_by=user,
            asset_type=FieldAssetAssignment.AssetType.TOOL,
            asset_name="Smoke Test Tool",
            checkout_date=date.today()
        )
        assert assignment.pk is not None

    @pytest.mark.django_db
    def test_str_representation(self, field_technician, user):
        """Smoke test: __str__ works"""
        assignment = FieldAssetAssignment.objects.create(
            assigned_to=field_technician,
            checked_out_by=user,
            asset_name="Smoke Test Tool",
            checkout_date=date.today()
        )
        result = str(assignment)
        assert "ASSIGN-" in result or "Smoke Test Tool" in result

    @pytest.mark.django_db
    def test_auto_generated_id(self, field_technician, user):
        """Smoke test: Auto-generated assignment_number works"""
        assignment = FieldAssetAssignment.objects.create(
            assigned_to=field_technician,
            checked_out_by=user,
            asset_name="Auto ID Test Tool",
            checkout_date=date.today()
        )
        assert assignment.assignment_number.startswith("ASSIGN-")

    @pytest.mark.django_db
    def test_technician_relationship(self, field_technician, user):
        """Smoke test: FieldTechnician relationship works"""
        assignment = FieldAssetAssignment.objects.create(
            assigned_to=field_technician,
            checked_out_by=user,
            asset_name="Test Tool",
            checkout_date=date.today()
        )
        assert assignment.assigned_to == field_technician
        assert assignment in field_technician.asset_assignments.all()
