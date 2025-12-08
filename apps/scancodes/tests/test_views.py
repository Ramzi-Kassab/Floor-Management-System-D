"""
Scancodes App - View Tests
Comprehensive tests for scancode views.

Tests cover:
- List, detail, create views
- Scanner interface
- Authentication requirements
- QR code generation
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.scancodes.models import ScanCode, ScanLog

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
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(client, user):
    """Return an authenticated client."""
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def scan_code(db, user):
    """Create a test scan code."""
    return ScanCode.objects.create(
        code='TEST-QR-001',
        code_type=ScanCode.CodeType.QR,
        entity_type=ScanCode.EntityType.DRILL_BIT,
        entity_id=1,
        created_by=user
    )


@pytest.fixture
def scan_log(db, scan_code, user):
    """Create a test scan log."""
    return ScanLog.objects.create(
        scan_code=scan_code,
        raw_code='TEST-QR-001',
        purpose=ScanLog.Purpose.IDENTIFY,
        is_valid=True,
        scanned_by=user
    )


# =============================================================================
# SCAN CODE LIST VIEW TESTS
# =============================================================================

class TestScanCodeListView:
    """Tests for ScanCodeListView."""

    def test_list_requires_login(self, client):
        """Test list view requires authentication."""
        response = client.get(reverse('scancodes:scancode-list'))
        assert response.status_code == 302
        assert 'login' in response.url

    def test_list_authenticated(self, authenticated_client):
        """Test list view for authenticated user."""
        response = authenticated_client.get(reverse('scancodes:scancode-list'))
        assert response.status_code == 200

    def test_list_shows_scancodes(self, authenticated_client, scan_code):
        """Test that scan codes are displayed."""
        response = authenticated_client.get(reverse('scancodes:scancode-list'))
        assert scan_code.code in str(response.content)

    def test_list_filter_by_type(self, authenticated_client, scan_code):
        """Test filtering by code type."""
        response = authenticated_client.get(
            reverse('scancodes:scancode-list'),
            {'code_type': 'QR'}
        )
        assert response.status_code == 200

    def test_list_filter_by_entity_type(self, authenticated_client, scan_code):
        """Test filtering by entity type."""
        response = authenticated_client.get(
            reverse('scancodes:scancode-list'),
            {'entity_type': 'DRILL_BIT'}
        )
        assert response.status_code == 200

    def test_list_search(self, authenticated_client, scan_code):
        """Test search functionality."""
        response = authenticated_client.get(
            reverse('scancodes:scancode-list'),
            {'q': 'TEST-QR'}
        )
        content = str(response.content)
        assert scan_code.code in content


# =============================================================================
# SCAN CODE DETAIL VIEW TESTS
# =============================================================================

class TestScanCodeDetailView:
    """Tests for ScanCodeDetailView."""

    def test_detail_requires_login(self, client, scan_code):
        """Test detail view requires authentication."""
        response = client.get(
            reverse('scancodes:scancode-detail', kwargs={'pk': scan_code.pk})
        )
        assert response.status_code == 302

    def test_detail_authenticated(self, authenticated_client, scan_code):
        """Test detail view for authenticated user."""
        response = authenticated_client.get(
            reverse('scancodes:scancode-detail', kwargs={'pk': scan_code.pk})
        )
        assert response.status_code == 200

    def test_detail_shows_code_info(self, authenticated_client, scan_code):
        """Test that code information is displayed."""
        response = authenticated_client.get(
            reverse('scancodes:scancode-detail', kwargs={'pk': scan_code.pk})
        )
        content = str(response.content)
        assert scan_code.code in content

    def test_detail_404_for_nonexistent(self, authenticated_client):
        """Test 404 for non-existent scan code."""
        response = authenticated_client.get(
            reverse('scancodes:scancode-detail', kwargs={'pk': 99999})
        )
        assert response.status_code == 404


# =============================================================================
# SCAN CODE CREATE VIEW TESTS
# =============================================================================

class TestScanCodeCreateView:
    """Tests for ScanCodeCreateView."""

    def test_create_requires_login(self, client):
        """Test create view requires authentication."""
        response = client.get(reverse('scancodes:scancode-create'))
        assert response.status_code == 302

    def test_create_get(self, authenticated_client):
        """Test create view GET request."""
        response = authenticated_client.get(reverse('scancodes:scancode-create'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_create_post_valid(self, authenticated_client):
        """Test creating a scan code via POST."""
        data = {
            'code': 'NEW-QR-001',
            'code_type': 'QR',
            'entity_type': 'EQUIPMENT',
            'is_external': False,
            'is_active': True
        }
        response = authenticated_client.post(
            reverse('scancodes:scancode-create'),
            data
        )
        assert response.status_code == 302

        scan_code = ScanCode.objects.get(code='NEW-QR-001')
        assert scan_code.entity_type == 'EQUIPMENT'


# =============================================================================
# SCAN LOG LIST VIEW TESTS
# =============================================================================

class TestScanLogListView:
    """Tests for ScanLogListView."""

    def test_scanlog_list_requires_login(self, client):
        """Test scan log list requires authentication."""
        response = client.get(reverse('scancodes:scanlog-list'))
        assert response.status_code == 302

    def test_scanlog_list_authenticated(self, authenticated_client, scan_log):
        """Test scan log list for authenticated user."""
        response = authenticated_client.get(reverse('scancodes:scanlog-list'))
        assert response.status_code == 200


# =============================================================================
# SCAN LOG DETAIL VIEW TESTS
# =============================================================================

class TestScanLogDetailView:
    """Tests for ScanLogDetailView."""

    def test_scanlog_detail_requires_login(self, client, scan_log):
        """Test scan log detail requires authentication."""
        response = client.get(
            reverse('scancodes:scanlog-detail', kwargs={'pk': scan_log.pk})
        )
        assert response.status_code == 302

    def test_scanlog_detail_authenticated(self, authenticated_client, scan_log):
        """Test scan log detail for authenticated user."""
        response = authenticated_client.get(
            reverse('scancodes:scanlog-detail', kwargs={'pk': scan_log.pk})
        )
        assert response.status_code == 200


# =============================================================================
# SCANNER VIEW TESTS
# =============================================================================

class TestScannerView:
    """Tests for Scanner interface view."""

    def test_scanner_requires_login(self, client):
        """Test scanner view requires authentication."""
        response = client.get(reverse('scancodes:scanner'))
        assert response.status_code == 302

    def test_scanner_authenticated(self, authenticated_client):
        """Test scanner view for authenticated user."""
        response = authenticated_client.get(reverse('scancodes:scanner'))
        assert response.status_code == 200


# =============================================================================
# GENERATE VIEW TESTS
# =============================================================================

class TestGenerateView:
    """Tests for QR code generation view."""

    def test_generate_requires_login(self, client):
        """Test generate view requires authentication."""
        response = client.get(reverse('scancodes:generate'))
        assert response.status_code == 302

    def test_generate_authenticated(self, authenticated_client):
        """Test generate view for authenticated user."""
        response = authenticated_client.get(reverse('scancodes:generate'))
        assert response.status_code == 200


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestScanCodeViewEdgeCases:
    """Edge case tests for scancode views."""

    def test_duplicate_code_rejected(self, authenticated_client, scan_code):
        """Test creating duplicate code is rejected."""
        data = {
            'code': scan_code.code,  # Duplicate
            'code_type': 'QR',
            'entity_type': 'DOCUMENT',
            'is_active': True
        }
        response = authenticated_client.post(
            reverse('scancodes:scancode-create'),
            data
        )
        # Should show form with error
        assert response.status_code == 200

    def test_external_scancode_with_source(self, authenticated_client):
        """Test creating external scan code with source."""
        data = {
            'code': 'EXT-ARAMCO-001',
            'code_type': 'BARCODE',
            'entity_type': 'EXTERNAL',
            'is_external': True,
            'external_source': 'ARAMCO',
            'is_active': True
        }
        response = authenticated_client.post(
            reverse('scancodes:scancode-create'),
            data
        )
        assert response.status_code == 302

        scan_code = ScanCode.objects.get(code='EXT-ARAMCO-001')
        assert scan_code.is_external is True
        assert scan_code.external_source == 'ARAMCO'
