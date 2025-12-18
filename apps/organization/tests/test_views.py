"""
Organization App - View Tests
Comprehensive tests for organization views.

Tests cover:
- List, detail, create, update, delete views
- Authentication requirements
- Form validation
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.organization.models import (
    Department, Position, Theme, SystemSetting, NumberSequence
)

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
def department(db):
    """Create a test department."""
    return Department.objects.create(
        code='TEST-DEPT',
        name='Test Department',
        location='Building A'
    )


@pytest.fixture
def position(db, department):
    """Create a test position."""
    return Position.objects.create(
        code='TEST-POS',
        title='Test Position',
        department=department,
        level=2
    )


@pytest.fixture
def theme(db):
    """Create a test theme."""
    return Theme.objects.create(
        code='TEST-THEME',
        name='Test Theme',
        primary_color='#0066cc'
    )


@pytest.fixture
def system_setting(db):
    """Create a test system setting."""
    return SystemSetting.objects.create(
        key='test_setting',
        value='test_value',
        category='general'
    )


@pytest.fixture
def number_sequence(db):
    """Create a test number sequence."""
    return NumberSequence.objects.create(
        code='TEST-SEQ',
        name='Test Sequence',
        prefix='TS-',
        padding=4
    )


# =============================================================================
# DEPARTMENT VIEW TESTS
# =============================================================================

class TestDepartmentListView:
    """Tests for DepartmentListView."""

    def test_list_requires_login(self, client):
        """Test list requires authentication."""
        response = client.get(reverse('organization:department-list'))
        assert response.status_code == 302
        assert 'login' in response.url

    def test_list_authenticated(self, authenticated_client, department):
        """Test list for authenticated user."""
        response = authenticated_client.get(reverse('organization:department-list'))
        assert response.status_code == 200
        assert 'departments' in response.context

    def test_list_shows_departments(self, authenticated_client, department):
        """Test that departments are displayed."""
        response = authenticated_client.get(reverse('organization:department-list'))
        assert department.name in str(response.content)


class TestDepartmentDetailView:
    """Tests for DepartmentDetailView."""

    def test_detail_requires_login(self, client, department):
        """Test detail requires authentication."""
        response = client.get(
            reverse('organization:department-detail', kwargs={'pk': department.pk})
        )
        assert response.status_code == 302

    def test_detail_authenticated(self, authenticated_client, department):
        """Test detail for authenticated user."""
        response = authenticated_client.get(
            reverse('organization:department-detail', kwargs={'pk': department.pk})
        )
        assert response.status_code == 200

    def test_detail_404_nonexistent(self, authenticated_client):
        """Test 404 for non-existent department."""
        response = authenticated_client.get(
            reverse('organization:department-detail', kwargs={'pk': 99999})
        )
        assert response.status_code == 404


class TestDepartmentCreateView:
    """Tests for DepartmentCreateView."""

    def test_create_get(self, authenticated_client):
        """Test create GET request."""
        response = authenticated_client.get(reverse('organization:department-create'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_create_post_valid(self, authenticated_client):
        """Test creating a department via POST."""
        data = {
            'code': 'NEW-DEPT',
            'name': 'New Department',
            'location': 'Building B',
            'is_active': True
        }
        response = authenticated_client.post(
            reverse('organization:department-create'),
            data
        )
        assert response.status_code == 302

        dept = Department.objects.get(code='NEW-DEPT')
        assert dept.name == 'New Department'


class TestDepartmentUpdateView:
    """Tests for DepartmentUpdateView."""

    def test_update_get(self, authenticated_client, department):
        """Test update GET request."""
        response = authenticated_client.get(
            reverse('organization:department-update', kwargs={'pk': department.pk})
        )
        assert response.status_code == 200

    def test_update_post(self, authenticated_client, department):
        """Test updating a department via POST."""
        data = {
            'code': department.code,
            'name': 'Updated Department',
            'location': 'New Location',
            'is_active': True
        }
        response = authenticated_client.post(
            reverse('organization:department-update', kwargs={'pk': department.pk}),
            data
        )
        assert response.status_code == 302

        department.refresh_from_db()
        assert department.name == 'Updated Department'


# =============================================================================
# POSITION VIEW TESTS
# =============================================================================

class TestPositionListView:
    """Tests for PositionListView."""

    def test_list_requires_login(self, client):
        """Test list requires authentication."""
        response = client.get(reverse('organization:position-list'))
        assert response.status_code == 302

    def test_list_authenticated(self, authenticated_client, position):
        """Test list for authenticated user."""
        response = authenticated_client.get(reverse('organization:position-list'))
        assert response.status_code == 200


class TestPositionDetailView:
    """Tests for PositionDetailView."""

    def test_detail_requires_login(self, client, position):
        """Test detail requires authentication."""
        response = client.get(
            reverse('organization:position-detail', kwargs={'pk': position.pk})
        )
        assert response.status_code == 302

    def test_detail_authenticated(self, authenticated_client, position):
        """Test detail for authenticated user."""
        response = authenticated_client.get(
            reverse('organization:position-detail', kwargs={'pk': position.pk})
        )
        assert response.status_code == 200


class TestPositionCreateView:
    """Tests for PositionCreateView."""

    def test_create_get(self, authenticated_client):
        """Test create GET request."""
        response = authenticated_client.get(reverse('organization:position-create'))
        assert response.status_code == 200

    def test_create_post_valid(self, authenticated_client, department):
        """Test creating a position via POST."""
        data = {
            'code': 'NEW-POS',
            'title': 'New Position',
            'department': department.pk,
            'level': 3,
            'is_active': True
        }
        response = authenticated_client.post(
            reverse('organization:position-create'),
            data
        )
        assert response.status_code == 302


# =============================================================================
# NUMBER SEQUENCE VIEW TESTS
# =============================================================================

class TestSequenceListView:
    """Tests for SequenceListView."""

    def test_list_requires_login(self, client):
        """Test list requires authentication."""
        response = client.get(reverse('organization:sequence-list'))
        assert response.status_code == 302

    def test_list_authenticated(self, authenticated_client, number_sequence):
        """Test list for authenticated user."""
        response = authenticated_client.get(reverse('organization:sequence-list'))
        assert response.status_code == 200


class TestSequenceDetailView:
    """Tests for SequenceDetailView."""

    def test_detail_requires_login(self, client, number_sequence):
        """Test detail requires authentication."""
        response = client.get(
            reverse('organization:sequence-detail', kwargs={'pk': number_sequence.pk})
        )
        assert response.status_code == 302

    def test_detail_authenticated(self, authenticated_client, number_sequence):
        """Test detail for authenticated user."""
        response = authenticated_client.get(
            reverse('organization:sequence-detail', kwargs={'pk': number_sequence.pk})
        )
        assert response.status_code == 200


class TestSequenceCreateView:
    """Tests for SequenceCreateView."""

    def test_create_get(self, authenticated_client):
        """Test create GET request."""
        response = authenticated_client.get(reverse('organization:sequence-create'))
        assert response.status_code == 200

    def test_create_post_valid(self, authenticated_client):
        """Test creating a sequence via POST."""
        data = {
            'code': 'NEW-SEQ',
            'name': 'New Sequence',
            'prefix': 'NS-',
            'suffix': '',
            'padding': 6,
            'current_value': 0,
            'increment_by': 1,
            'reset_period': ''
        }
        response = authenticated_client.post(
            reverse('organization:sequence-create'),
            data
        )
        assert response.status_code == 302

        seq = NumberSequence.objects.get(code='NEW-SEQ')
        assert seq.prefix == 'NS-'


class TestSequenceDeleteView:
    """Tests for SequenceDeleteView."""

    def test_delete_get(self, authenticated_client, number_sequence):
        """Test delete confirmation page."""
        response = authenticated_client.get(
            reverse('organization:sequence-delete', kwargs={'pk': number_sequence.pk})
        )
        assert response.status_code == 200

    def test_delete_post(self, authenticated_client, number_sequence):
        """Test deleting a sequence via POST."""
        seq_id = number_sequence.pk
        response = authenticated_client.post(
            reverse('organization:sequence-delete', kwargs={'pk': number_sequence.pk})
        )
        assert response.status_code == 302
        assert not NumberSequence.objects.filter(pk=seq_id).exists()


# =============================================================================
# SETTINGS VIEW TESTS
# =============================================================================

class TestSettingsListView:
    """Tests for SettingsListView."""

    def test_list_requires_login(self, client):
        """Test list requires authentication."""
        response = client.get(reverse('organization:settings-list'))
        assert response.status_code == 302

    def test_list_authenticated(self, authenticated_client, system_setting):
        """Test list for authenticated user."""
        response = authenticated_client.get(reverse('organization:settings-list'))
        assert response.status_code == 200


class TestSettingsUpdateView:
    """Tests for SettingsUpdateView."""

    def test_update_get(self, authenticated_client, system_setting):
        """Test update GET request."""
        response = authenticated_client.get(
            reverse('organization:setting-update', kwargs={'pk': system_setting.pk})
        )
        assert response.status_code == 200

    def test_update_post(self, authenticated_client, system_setting):
        """Test updating a setting via POST."""
        data = {
            'key': system_setting.key,
            'value': 'updated_value',
            'value_type': 'STRING',
            'description': 'Updated description',
            'category': 'general',
            'is_editable': True
        }
        response = authenticated_client.post(
            reverse('organization:setting-update', kwargs={'pk': system_setting.pk}),
            data
        )
        assert response.status_code == 302

        system_setting.refresh_from_db()
        assert system_setting.value == 'updated_value'


# =============================================================================
# THEME VIEW TESTS
# =============================================================================

class TestThemeListView:
    """Tests for ThemeListView."""

    def test_list_requires_login(self, client):
        """Test list requires authentication."""
        response = client.get(reverse('organization:theme-list'))
        assert response.status_code == 302

    def test_list_authenticated(self, authenticated_client, theme):
        """Test list for authenticated user."""
        response = authenticated_client.get(reverse('organization:theme-list'))
        assert response.status_code == 200


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestOrganizationViewEdgeCases:
    """Edge case tests for organization views."""

    def test_department_with_parent(self, authenticated_client, department):
        """Test creating department with parent."""
        data = {
            'code': 'CHILD-DEPT',
            'name': 'Child Department',
            'parent': department.pk,
            'is_active': True
        }
        response = authenticated_client.post(
            reverse('organization:department-create'),
            data
        )
        assert response.status_code == 302

        child = Department.objects.get(code='CHILD-DEPT')
        assert child.parent == department

    def test_duplicate_department_code(self, authenticated_client, department):
        """Test creating department with duplicate code."""
        data = {
            'code': department.code,  # Duplicate
            'name': 'Another Department',
            'is_active': True
        }
        response = authenticated_client.post(
            reverse('organization:department-create'),
            data
        )
        # Should return form with errors
        assert response.status_code == 200
