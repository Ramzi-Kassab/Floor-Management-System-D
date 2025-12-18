"""
HSSE App - Model Tests
Comprehensive tests for HOCReport, Incident, and Journey models.

Tests cover:
- Instance creation with required fields
- __str__ representation
- Field validation (max_length, choices, unique constraints)
- Foreign key relationships
- Edge cases
"""

import pytest
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from apps.hsse.models import HOCReport, Incident, Journey

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def safety_officer(db):
    """Create a safety officer user."""
    return User.objects.create_user(
        username='safety_officer',
        email='safety@example.com',
        password='safepass123',
        first_name='Safety',
        last_name='Officer'
    )


@pytest.fixture
def driver(db):
    """Create a driver user."""
    return User.objects.create_user(
        username='driver',
        email='driver@example.com',
        password='drivepass123',
        first_name='John',
        last_name='Driver'
    )


@pytest.fixture
def approver(db):
    """Create an approver user."""
    return User.objects.create_user(
        username='approver',
        email='approver@example.com',
        password='approvepass123',
        first_name='Manager',
        last_name='Approver'
    )


@pytest.fixture
def hoc_report(db, user):
    """Create a test HOC report."""
    return HOCReport.objects.create(
        hoc_number='HOC-2024-001',
        category=HOCReport.Category.UNSAFE_ACT,
        location='Manufacturing Floor',
        description='Employee not wearing safety goggles',
        reported_by=user
    )


@pytest.fixture
def incident(db, user):
    """Create a test incident."""
    return Incident.objects.create(
        incident_number='INC-2024-001',
        incident_type=Incident.IncidentType.INJURY,
        severity=Incident.Severity.MINOR,
        occurred_at=timezone.now(),
        location='Workshop Area',
        description='Minor cut on hand from sharp edge',
        reported_by=user
    )


@pytest.fixture
def journey(db, driver, approver):
    """Create a test journey."""
    now = timezone.now()
    return Journey.objects.create(
        journey_number='JRN-2024-001',
        purpose='Site visit to customer location',
        driver=driver,
        departure_location='ARDT Office',
        destination='Customer Site A',
        planned_departure=now + timedelta(hours=1),
        planned_arrival=now + timedelta(hours=3),
        approved_by=approver
    )


# =============================================================================
# HOC REPORT MODEL TESTS
# =============================================================================

class TestHOCReportModel:
    """Tests for the HOCReport model."""

    def test_create_hoc_report(self, db, user):
        """Test creating a HOC report."""
        hoc = HOCReport.objects.create(
            hoc_number='TEST-HOC-001',
            category=HOCReport.Category.NEAR_MISS,
            location='Test Location',
            description='Test near miss observation',
            reported_by=user
        )
        assert hoc.pk is not None
        assert hoc.status == HOCReport.Status.OPEN

    def test_hoc_report_str(self, hoc_report):
        """Test the __str__ method."""
        expected = 'HOC-2024-001 - Unsafe Act'
        assert str(hoc_report) == expected

    def test_hoc_report_unique_number(self, hoc_report, user):
        """Test that HOC number must be unique."""
        with pytest.raises(IntegrityError):
            HOCReport.objects.create(
                hoc_number='HOC-2024-001',  # Duplicate
                category=HOCReport.Category.UNSAFE_CONDITION,
                location='Other Location',
                description='Test',
                reported_by=user
            )

    def test_hoc_report_category_choices(self, db, user):
        """Test all valid category choices."""
        for category_code, category_name in HOCReport.Category.choices:
            hoc = HOCReport.objects.create(
                hoc_number=f'CAT-{category_code}',
                category=category_code,
                location='Test Location',
                description='Test description',
                reported_by=user
            )
            assert hoc.category == category_code

    def test_hoc_report_status_choices(self, db, user):
        """Test all valid status choices."""
        for status_code, status_name in HOCReport.Status.choices:
            hoc = HOCReport.objects.create(
                hoc_number=f'STAT-{status_code}',
                category=HOCReport.Category.POSITIVE,
                location='Test Location',
                description='Test',
                status=status_code,
                reported_by=user
            )
            assert hoc.status == status_code

    def test_hoc_report_with_immediate_action(self, db, user):
        """Test HOC report with immediate action."""
        hoc = HOCReport.objects.create(
            hoc_number='ACTION-HOC-001',
            category=HOCReport.Category.UNSAFE_CONDITION,
            location='Storage Area',
            description='Spill on floor creating slip hazard',
            immediate_action='Area cordoned off, spill cleaned immediately',
            reported_by=user
        )
        assert 'cleaned' in hoc.immediate_action

    def test_hoc_report_timestamp(self, hoc_report):
        """Test auto-generated timestamp."""
        assert hoc_report.reported_at is not None

    def test_hoc_report_positive_observation(self, db, user):
        """Test positive observation category."""
        hoc = HOCReport.objects.create(
            hoc_number='POSITIVE-001',
            category=HOCReport.Category.POSITIVE,
            location='Main Office',
            description='Employee properly using PPE',
            reported_by=user
        )
        assert hoc.category == HOCReport.Category.POSITIVE


# =============================================================================
# INCIDENT MODEL TESTS
# =============================================================================

class TestIncidentModel:
    """Tests for the Incident model."""

    def test_create_incident(self, db, user):
        """Test creating an incident."""
        incident = Incident.objects.create(
            incident_number='TEST-INC-001',
            incident_type=Incident.IncidentType.PROPERTY_DAMAGE,
            severity=Incident.Severity.MODERATE,
            occurred_at=timezone.now(),
            location='Workshop',
            description='Equipment damage during operation',
            reported_by=user
        )
        assert incident.pk is not None
        assert incident.status == Incident.Status.REPORTED

    def test_incident_str(self, incident):
        """Test the __str__ method."""
        expected = 'INC-2024-001 - Minor'
        assert str(incident) == expected

    def test_incident_unique_number(self, incident, user):
        """Test that incident number must be unique."""
        with pytest.raises(IntegrityError):
            Incident.objects.create(
                incident_number='INC-2024-001',  # Duplicate
                incident_type=Incident.IncidentType.FIRE,
                severity=Incident.Severity.MAJOR,
                occurred_at=timezone.now(),
                location='Different Location',
                description='Test',
                reported_by=user
            )

    def test_incident_type_choices(self, db, user):
        """Test all valid incident type choices."""
        for inc_type, type_name in Incident.IncidentType.choices:
            incident = Incident.objects.create(
                incident_number=f'TYPE-{inc_type}',
                incident_type=inc_type,
                severity=Incident.Severity.MINOR,
                occurred_at=timezone.now(),
                location='Test Location',
                description='Test',
                reported_by=user
            )
            assert incident.incident_type == inc_type

    def test_incident_severity_choices(self, db, user):
        """Test all valid severity choices."""
        for severity_code, severity_name in Incident.Severity.choices:
            incident = Incident.objects.create(
                incident_number=f'SEV-{severity_code}',
                incident_type=Incident.IncidentType.OTHER,
                severity=severity_code,
                occurred_at=timezone.now(),
                location='Test Location',
                description='Test',
                reported_by=user
            )
            assert incident.severity == severity_code

    def test_incident_investigation_fields(self, incident):
        """Test incident investigation fields."""
        incident.status = Incident.Status.INVESTIGATING
        incident.investigation_findings = 'Initial investigation findings'
        incident.root_cause = 'Root cause analysis'
        incident.corrective_actions = 'Corrective actions taken'
        incident.save()

        incident.refresh_from_db()
        assert incident.status == Incident.Status.INVESTIGATING
        assert 'findings' in incident.investigation_findings

    def test_incident_closed(self, incident):
        """Test closing an incident."""
        incident.status = Incident.Status.CLOSED
        incident.investigation_findings = 'Complete findings'
        incident.root_cause = 'Identified root cause'
        incident.corrective_actions = 'All actions completed'
        incident.save()

        incident.refresh_from_db()
        assert incident.status == Incident.Status.CLOSED

    def test_incident_critical_severity(self, db, user):
        """Test critical severity incident."""
        incident = Incident.objects.create(
            incident_number='CRITICAL-001',
            incident_type=Incident.IncidentType.FIRE,
            severity=Incident.Severity.CRITICAL,
            occurred_at=timezone.now(),
            location='Manufacturing Area',
            description='Major fire incident',
            immediate_action='Emergency evacuation, fire brigade called',
            reported_by=user
        )
        assert incident.severity == Incident.Severity.CRITICAL


# =============================================================================
# JOURNEY MODEL TESTS
# =============================================================================

class TestJourneyModel:
    """Tests for the Journey model."""

    def test_create_journey(self, db, driver):
        """Test creating a journey."""
        now = timezone.now()
        journey = Journey.objects.create(
            journey_number='TEST-JRN-001',
            purpose='Field visit',
            driver=driver,
            departure_location='Office',
            destination='Field Site',
            planned_departure=now + timedelta(hours=1),
            planned_arrival=now + timedelta(hours=4)
        )
        assert journey.pk is not None
        assert journey.status == Journey.Status.PLANNED

    def test_journey_str(self, journey, driver):
        """Test the __str__ method."""
        expected = f'JRN-2024-001 - {driver.get_full_name()}'
        assert str(journey) == expected

    def test_journey_unique_number(self, journey, driver):
        """Test that journey number must be unique."""
        now = timezone.now()
        with pytest.raises(IntegrityError):
            Journey.objects.create(
                journey_number='JRN-2024-001',  # Duplicate
                purpose='Another trip',
                driver=driver,
                departure_location='Office',
                destination='Another Site',
                planned_departure=now + timedelta(hours=2),
                planned_arrival=now + timedelta(hours=5)
            )

    def test_journey_status_choices(self, db, driver):
        """Test all valid status choices."""
        now = timezone.now()
        for status_code, status_name in Journey.Status.choices:
            journey = Journey.objects.create(
                journey_number=f'STAT-{status_code}',
                purpose='Test journey',
                driver=driver,
                departure_location='Office',
                destination='Destination',
                planned_departure=now + timedelta(hours=1),
                planned_arrival=now + timedelta(hours=3),
                status=status_code
            )
            assert journey.status == status_code

    def test_journey_approval(self, journey, approver):
        """Test journey approval."""
        journey.status = Journey.Status.APPROVED
        journey.approved_by = approver
        journey.save()

        journey.refresh_from_db()
        assert journey.status == Journey.Status.APPROVED
        assert journey.approved_by == approver

    def test_journey_in_progress(self, journey):
        """Test journey in progress with actual departure."""
        journey.status = Journey.Status.IN_PROGRESS
        journey.actual_departure = timezone.now()
        journey.save()

        journey.refresh_from_db()
        assert journey.status == Journey.Status.IN_PROGRESS
        assert journey.actual_departure is not None

    def test_journey_completed(self, journey):
        """Test completed journey."""
        now = timezone.now()
        journey.status = Journey.Status.COMPLETED
        journey.actual_departure = now - timedelta(hours=2)
        journey.actual_arrival = now
        journey.save()

        journey.refresh_from_db()
        assert journey.status == Journey.Status.COMPLETED
        assert journey.actual_arrival is not None

    def test_journey_with_vehicle(self, journey):
        """Test journey with assigned vehicle."""
        from apps.dispatch.models import Vehicle

        vehicle = Vehicle.objects.create(
            code='JRN-VH-001',
            plate_number='JRN-1234'
        )
        journey.vehicle = vehicle
        journey.save()

        journey.refresh_from_db()
        assert journey.vehicle == vehicle

    def test_journey_cancelled(self, journey):
        """Test cancelled journey."""
        journey.status = Journey.Status.CANCELLED
        journey.save()

        journey.refresh_from_db()
        assert journey.status == Journey.Status.CANCELLED


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestHSSEEdgeCases:
    """Edge case tests for HSSE models."""

    def test_hoc_long_description(self, db, user):
        """Test HOC with long description."""
        long_desc = 'X' * 1000
        hoc = HOCReport.objects.create(
            hoc_number='LONG-HOC-001',
            category=HOCReport.Category.UNSAFE_ACT,
            location='Test',
            description=long_desc,
            reported_by=user
        )
        assert len(hoc.description) == 1000

    def test_incident_environmental(self, db, user):
        """Test environmental incident."""
        incident = Incident.objects.create(
            incident_number='ENV-001',
            incident_type=Incident.IncidentType.ENVIRONMENTAL,
            severity=Incident.Severity.MODERATE,
            occurred_at=timezone.now(),
            location='Outside Storage',
            description='Chemical spill requiring cleanup',
            reported_by=user
        )
        assert incident.incident_type == Incident.IncidentType.ENVIRONMENTAL

    def test_journey_same_departure_arrival(self, db, driver):
        """Test journey with same departure and arrival location."""
        now = timezone.now()
        journey = Journey.objects.create(
            journey_number='ROUND-001',
            purpose='Round trip inspection',
            driver=driver,
            departure_location='ARDT Office',
            destination='ARDT Office',  # Same location
            planned_departure=now + timedelta(hours=1),
            planned_arrival=now + timedelta(hours=4)
        )
        assert journey.departure_location == journey.destination

    def test_special_characters_in_location(self, db, user):
        """Test special characters in location field."""
        hoc = HOCReport.objects.create(
            hoc_number='SPECIAL-001',
            category=HOCReport.Category.UNSAFE_CONDITION,
            location='Building A - Floor 2 (Section B/C)',
            description='Test description',
            reported_by=user
        )
        assert '/' in hoc.location
        assert '(' in hoc.location
