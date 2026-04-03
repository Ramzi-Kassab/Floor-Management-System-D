"""
HSSE App - View Tests
Comprehensive tests for HSSE views.

Tests cover:
- Dashboard, list, detail, create, update views
- Authentication requirements
- Form validation
- Status transitions
"""

import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
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
def authenticated_client(client, user):
    """Return an authenticated client."""
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def hoc_report(db, user):
    """Create a test HOC report."""
    return HOCReport.objects.create(
        hoc_number='HOC-001',
        category=HOCReport.Category.UNSAFE_ACT,
        location='Manufacturing Floor',
        description='Test observation',
        reported_by=user
    )


@pytest.fixture
def incident(db, user):
    """Create a test incident."""
    return Incident.objects.create(
        incident_number='INC-001',
        incident_type=Incident.IncidentType.INJURY,
        severity=Incident.Severity.MINOR,
        occurred_at=timezone.now(),
        location='Workshop',
        description='Minor injury',
        reported_by=user
    )


@pytest.fixture
def journey(db, user):
    """Create a test journey."""
    now = timezone.now()
    return Journey.objects.create(
        journey_number='JRN-001',
        purpose='Site visit',
        driver=user,
        departure_location='Office',
        destination='Customer Site',
        planned_departure=now + timedelta(hours=1),
        planned_arrival=now + timedelta(hours=3)
    )


# =============================================================================
# HSSE DASHBOARD VIEW TESTS
# =============================================================================

class TestHSSEDashboardView:
    """Tests for HSSEDashboardView."""

    def test_dashboard_requires_login(self, client):
        """Test dashboard requires authentication."""
        response = client.get(reverse('hsse:dashboard'))
        assert response.status_code == 302
        assert 'login' in response.url

    def test_dashboard_authenticated(self, authenticated_client):
        """Test dashboard for authenticated user."""
        response = authenticated_client.get(reverse('hsse:dashboard'))
        assert response.status_code == 200

    def test_dashboard_context(self, authenticated_client, hoc_report, incident, journey):
        """Test dashboard context data."""
        response = authenticated_client.get(reverse('hsse:dashboard'))
        assert 'page_title' in response.context


# =============================================================================
# HOC REPORT VIEW TESTS
# =============================================================================

class TestHOCReportListView:
    """Tests for HOCReportListView."""

    def test_list_requires_login(self, client):
        """Test list requires authentication."""
        response = client.get(reverse('hsse:hoc-list'))
        assert response.status_code == 302

    def test_list_authenticated(self, authenticated_client, hoc_report):
        """Test list for authenticated user."""
        response = authenticated_client.get(reverse('hsse:hoc-list'))
        assert response.status_code == 200
        assert 'hoc_reports' in response.context

    def test_list_filter_category(self, authenticated_client, hoc_report):
        """Test filtering by category."""
        response = authenticated_client.get(
            reverse('hsse:hoc-list'),
            {'category': 'UNSAFE_ACT'}
        )
        assert response.status_code == 200

    def test_list_filter_status(self, authenticated_client, hoc_report):
        """Test filtering by status."""
        response = authenticated_client.get(
            reverse('hsse:hoc-list'),
            {'status': 'OPEN'}
        )
        assert response.status_code == 200


class TestHOCReportDetailView:
    """Tests for HOCReportDetailView."""

    def test_detail_requires_login(self, client, hoc_report):
        """Test detail requires authentication."""
        response = client.get(
            reverse('hsse:hoc-detail', kwargs={'pk': hoc_report.pk})
        )
        assert response.status_code == 302

    def test_detail_authenticated(self, authenticated_client, hoc_report):
        """Test detail for authenticated user."""
        response = authenticated_client.get(
            reverse('hsse:hoc-detail', kwargs={'pk': hoc_report.pk})
        )
        assert response.status_code == 200


class TestHOCReportCreateView:
    """Tests for HOCReportCreateView."""

    def test_create_get(self, authenticated_client):
        """Test create GET request."""
        response = authenticated_client.get(reverse('hsse:hoc-create'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_create_post_valid(self, authenticated_client):
        """Test creating a HOC report via POST."""
        data = {
            'hoc_number': 'NEW-HOC-001',
            'category': 'NEAR_MISS',
            'location': 'Test Location',
            'description': 'Test near miss observation',
            'status': 'OPEN'
        }
        response = authenticated_client.post(reverse('hsse:hoc-create'), data)
        assert response.status_code == 302

        hoc = HOCReport.objects.get(hoc_number='NEW-HOC-001')
        assert hoc.category == 'NEAR_MISS'


class TestHOCReportUpdateView:
    """Tests for HOCReportUpdateView."""

    def test_update_get(self, authenticated_client, hoc_report):
        """Test update GET request."""
        response = authenticated_client.get(
            reverse('hsse:hoc-update', kwargs={'pk': hoc_report.pk})
        )
        assert response.status_code == 200

    def test_update_post(self, authenticated_client, hoc_report):
        """Test updating a HOC report via POST."""
        data = {
            'hoc_number': hoc_report.hoc_number,
            'category': hoc_report.category,
            'location': hoc_report.location,
            'description': hoc_report.description,
            'status': 'IN_PROGRESS',
            'immediate_action': 'Action taken'
        }
        response = authenticated_client.post(
            reverse('hsse:hoc-update', kwargs={'pk': hoc_report.pk}),
            data
        )
        assert response.status_code == 302

        hoc_report.refresh_from_db()
        assert hoc_report.status == 'IN_PROGRESS'


# =============================================================================
# INCIDENT VIEW TESTS
# =============================================================================

class TestIncidentListView:
    """Tests for IncidentListView."""

    def test_list_requires_login(self, client):
        """Test list requires authentication."""
        response = client.get(reverse('hsse:incident-list'))
        assert response.status_code == 302

    def test_list_authenticated(self, authenticated_client, incident):
        """Test list for authenticated user."""
        response = authenticated_client.get(reverse('hsse:incident-list'))
        assert response.status_code == 200

    def test_list_filter_severity(self, authenticated_client, incident):
        """Test filtering by severity."""
        response = authenticated_client.get(
            reverse('hsse:incident-list'),
            {'severity': 'MINOR'}
        )
        assert response.status_code == 200


class TestIncidentDetailView:
    """Tests for IncidentDetailView."""

    def test_detail_requires_login(self, client, incident):
        """Test detail requires authentication."""
        response = client.get(
            reverse('hsse:incident-detail', kwargs={'pk': incident.pk})
        )
        assert response.status_code == 302

    def test_detail_authenticated(self, authenticated_client, incident):
        """Test detail for authenticated user."""
        response = authenticated_client.get(
            reverse('hsse:incident-detail', kwargs={'pk': incident.pk})
        )
        assert response.status_code == 200


class TestIncidentCreateView:
    """Tests for IncidentCreateView."""

    def test_create_get(self, authenticated_client):
        """Test create GET request."""
        response = authenticated_client.get(reverse('hsse:incident-create'))
        assert response.status_code == 200

    def test_create_post_valid(self, authenticated_client):
        """Test creating an incident via POST."""
        data = {
            'incident_number': 'NEW-INC-001',
            'incident_type': 'PROPERTY_DAMAGE',
            'severity': 'MODERATE',
            'occurred_at': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'location': 'Test Location',
            'description': 'Property damage incident',
            'status': 'REPORTED'
        }
        response = authenticated_client.post(reverse('hsse:incident-create'), data)
        assert response.status_code == 302


# =============================================================================
# JOURNEY VIEW TESTS
# =============================================================================

class TestJourneyListView:
    """Tests for JourneyListView."""

    def test_list_requires_login(self, client):
        """Test list requires authentication."""
        response = client.get(reverse('hsse:journey-list'))
        assert response.status_code == 302

    def test_list_authenticated(self, authenticated_client, journey):
        """Test list for authenticated user."""
        response = authenticated_client.get(reverse('hsse:journey-list'))
        assert response.status_code == 200

    def test_list_filter_status(self, authenticated_client, journey):
        """Test filtering by status."""
        response = authenticated_client.get(
            reverse('hsse:journey-list'),
            {'status': 'PLANNED'}
        )
        assert response.status_code == 200


class TestJourneyDetailView:
    """Tests for JourneyDetailView."""

    def test_detail_requires_login(self, client, journey):
        """Test detail requires authentication."""
        response = client.get(
            reverse('hsse:journey-detail', kwargs={'pk': journey.pk})
        )
        assert response.status_code == 302

    def test_detail_authenticated(self, authenticated_client, journey):
        """Test detail for authenticated user."""
        response = authenticated_client.get(
            reverse('hsse:journey-detail', kwargs={'pk': journey.pk})
        )
        assert response.status_code == 200


class TestJourneyCreateView:
    """Tests for JourneyCreateView."""

    def test_create_get(self, authenticated_client):
        """Test create GET request."""
        response = authenticated_client.get(reverse('hsse:journey-create'))
        assert response.status_code == 200

    def test_create_post_valid(self, authenticated_client, user):
        """Test creating a journey via POST."""
        now = timezone.now()
        data = {
            'journey_number': 'NEW-JRN-001',
            'purpose': 'Business trip',
            'driver': user.pk,
            'departure_location': 'Office',
            'destination': 'Customer Site',
            'planned_departure': (now + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
            'planned_arrival': (now + timedelta(hours=4)).strftime('%Y-%m-%dT%H:%M'),
            'status': 'PLANNED'
        }
        response = authenticated_client.post(reverse('hsse:journey-create'), data)
        assert response.status_code == 302


class TestJourneyUpdateView:
    """Tests for JourneyUpdateView."""

    def test_update_get(self, authenticated_client, journey):
        """Test update GET request."""
        response = authenticated_client.get(
            reverse('hsse:journey-update', kwargs={'pk': journey.pk})
        )
        assert response.status_code == 200


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestHSSEViewEdgeCases:
    """Edge case tests for HSSE views."""

    def test_hoc_404_nonexistent(self, authenticated_client):
        """Test 404 for non-existent HOC report."""
        response = authenticated_client.get(
            reverse('hsse:hoc-detail', kwargs={'pk': 99999})
        )
        assert response.status_code == 404

    def test_incident_404_nonexistent(self, authenticated_client):
        """Test 404 for non-existent incident."""
        response = authenticated_client.get(
            reverse('hsse:incident-detail', kwargs={'pk': 99999})
        )
        assert response.status_code == 404

    def test_journey_404_nonexistent(self, authenticated_client):
        """Test 404 for non-existent journey."""
        response = authenticated_client.get(
            reverse('hsse:journey-detail', kwargs={'pk': 99999})
        )
        assert response.status_code == 404
