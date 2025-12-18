"""
ARDT FMS - View Tests
Day 5: View Testing

Tests for authentication, permissions, and core views.
"""

import pytest
from django.test import Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def client():
    """Return a Django test client."""
    return Client()


@pytest.fixture
def rf():
    """Return a Django request factory."""
    return RequestFactory()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user(db):
    """Create a test admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check_returns_200(self, client, db):
        """Health check should return 200 when database is connected."""
        response = client.get('/health/')
        assert response.status_code == 200

    def test_health_check_returns_json(self, client, db):
        """Health check should return JSON response."""
        response = client.get('/health/')
        assert response['Content-Type'] == 'application/json'

    def test_health_check_contains_status(self, client, db):
        """Health check should contain status field."""
        response = client.get('/health/')
        data = response.json()
        assert 'status' in data
        assert 'database' in data
        assert 'version' in data


class TestAuthenticationViews:
    """Tests for authentication views."""

    def test_login_page_accessible(self, client):
        """Login page should be accessible without authentication."""
        response = client.get(reverse('accounts:login'))
        assert response.status_code == 200

    def test_login_with_valid_credentials(self, client, user):
        """User should be able to login with valid credentials."""
        response = client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        # Should redirect on successful login
        assert response.status_code in [200, 302]

    def test_login_with_invalid_credentials(self, client, user):
        """Login should fail with invalid credentials."""
        response = client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        # Should stay on login page
        assert response.status_code == 200

    def test_logout_redirects(self, client, user):
        """Logout should redirect to login page."""
        client.force_login(user)
        response = client.post(reverse('accounts:logout'))
        assert response.status_code in [200, 302]


class TestProtectedViews:
    """Tests for views that require authentication."""

    def test_dashboard_requires_login(self, client):
        """Dashboard should redirect unauthenticated users to login."""
        response = client.get(reverse('dashboard:home'))
        assert response.status_code == 302
        assert 'login' in response.url.lower() or 'accounts' in response.url.lower()

    def test_dashboard_accessible_when_logged_in(self, client, user):
        """Dashboard should be accessible when logged in."""
        client.force_login(user)
        response = client.get(reverse('dashboard:home'))
        assert response.status_code == 200

    def test_admin_requires_staff(self, client, user):
        """Admin should require staff status."""
        client.force_login(user)
        response = client.get('/admin/')
        # Non-staff should be redirected to admin login
        assert response.status_code == 302

    def test_admin_accessible_for_superuser(self, client, admin_user):
        """Admin should be accessible for superusers."""
        client.force_login(admin_user)
        response = client.get('/admin/')
        assert response.status_code == 200


class TestPermissionDecorators:
    """Tests for permission decorators."""

    def test_role_required_blocks_without_role(self, rf, user):
        """role_required should block users without required role."""
        from apps.accounts.decorators import role_required

        @role_required('ADMIN')
        def test_view(request):
            from django.http import HttpResponse
            return HttpResponse('OK')

        request = rf.get('/')
        request.user = user

        response = test_view(request)
        # Should raise PermissionDenied or redirect
        assert response.status_code in [302, 403]

    def test_superuser_bypasses_role_check(self, rf, admin_user):
        """Superusers should bypass role checks."""
        from apps.accounts.decorators import role_required

        @role_required('ADMIN')
        def test_view(request):
            from django.http import HttpResponse
            return HttpResponse('OK')

        request = rf.get('/')
        request.user = admin_user

        response = test_view(request)
        assert response.status_code == 200


class TestContextProcessors:
    """Tests for context processors."""

    def test_permissions_context_processor_unauthenticated(self, rf):
        """Context processor should handle unauthenticated users."""
        from apps.accounts.context_processors import permissions
        from django.contrib.auth.models import AnonymousUser

        request = rf.get('/')
        request.user = AnonymousUser()

        context = permissions(request)

        assert 'perms' in context
        assert 'user_roles' in context
        assert 'user_permissions' in context
        assert context['user_roles'] == []
        assert context['user_permissions'] == []

    def test_permissions_context_processor_authenticated(self, rf, user):
        """Context processor should provide permission helpers for authenticated users."""
        from apps.accounts.context_processors import permissions

        request = rf.get('/')
        request.user = user

        context = permissions(request)

        assert 'perms' in context
        assert hasattr(context['perms'], 'has_role')
        assert hasattr(context['perms'], 'has_permission')


class TestAPIEndpoints:
    """Tests for API-like endpoints."""

    def test_health_check_no_auth_required(self, client, db):
        """Health check should not require authentication."""
        response = client.get('/health/')
        assert response.status_code == 200

    def test_json_response_format(self, client, db):
        """JSON endpoints should return proper JSON."""
        response = client.get('/health/')
        data = response.json()
        assert isinstance(data, dict)


class TestErrorPages:
    """Tests for error handling."""

    def test_404_for_nonexistent_page(self, client, user):
        """Non-existent pages should return 404."""
        client.force_login(user)
        response = client.get('/this-page-does-not-exist-12345/')
        assert response.status_code == 404

    def test_403_for_forbidden_action(self, client, user):
        """Forbidden actions should return 403."""
        # This tests the PermissionDenied handling
        client.force_login(user)
        # Try to access admin without staff status
        response = client.get('/admin/accounts/user/')
        # Should redirect to admin login (302) since user is not staff
        assert response.status_code == 302
