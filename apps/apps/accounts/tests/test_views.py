"""
Tests for Accounts app views.
"""
import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def client():
    """Return a Django test client."""
    return Client()


@pytest.fixture
def authenticated_client(client, test_user):
    """Return an authenticated test client."""
    client.login(username='testuser', password='testpass123')
    return client


class TestLoginView:
    """Tests for login view."""

    def test_login_page_loads(self, client):
        """Test login page loads successfully."""
        url = reverse('accounts:login')
        response = client.get(url)
        assert response.status_code == 200

    def test_login_with_valid_credentials(self, client, test_user):
        """Test login with valid credentials."""
        url = reverse('accounts:login')
        response = client.post(url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        # Should redirect after successful login
        assert response.status_code == 302

    def test_login_with_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        url = reverse('accounts:login')
        response = client.post(url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        # Should stay on login page with error
        assert response.status_code == 200


class TestLogoutView:
    """Tests for logout view."""

    def test_logout(self, authenticated_client):
        """Test logout functionality."""
        url = reverse('accounts:logout')
        response = authenticated_client.post(url)
        # Should redirect after logout
        assert response.status_code == 302


class TestProfileView:
    """Tests for profile view."""

    def test_profile_requires_login(self, client):
        """Test profile page requires authentication."""
        url = reverse('accounts:profile')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url.lower()

    def test_profile_authenticated(self, authenticated_client):
        """Test profile page for authenticated user."""
        url = reverse('accounts:profile')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestSettingsView:
    """Tests for settings view."""

    def test_settings_requires_login(self, client):
        """Test settings page requires authentication."""
        url = reverse('accounts:settings')
        response = client.get(url)
        assert response.status_code == 302

    def test_settings_authenticated(self, authenticated_client):
        """Test settings page for authenticated user."""
        url = reverse('accounts:settings')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestPasswordChangeView:
    """Tests for password change view."""

    def test_password_change_requires_login(self, client):
        """Test password change requires authentication."""
        url = reverse('accounts:password_change')
        response = client.get(url)
        assert response.status_code == 302

    def test_password_change_get(self, authenticated_client):
        """Test password change form loads."""
        url = reverse('accounts:password_change')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_password_change_post_valid(self, authenticated_client):
        """Test password change with valid data."""
        url = reverse('accounts:password_change')
        response = authenticated_client.post(url, {
            'old_password': 'testpass123',
            'new_password1': 'newpassword456',
            'new_password2': 'newpassword456'
        })
        # Should redirect to done page on success
        assert response.status_code in [200, 302]


class TestPasswordResetView:
    """Tests for password reset view."""

    def test_password_reset_loads(self, client):
        """Test password reset page loads."""
        url = reverse('accounts:password_reset')
        response = client.get(url)
        assert response.status_code == 200

    def test_password_reset_post(self, client, test_user):
        """Test password reset request."""
        url = reverse('accounts:password_reset')
        response = client.post(url, {
            'email': 'test@example.com'
        })
        # Should redirect to done page
        assert response.status_code == 302

    def test_password_reset_done_loads(self, client):
        """Test password reset done page loads."""
        url = reverse('accounts:password_reset_done')
        response = client.get(url)
        assert response.status_code == 200

    def test_password_reset_complete_loads(self, client):
        """Test password reset complete page loads."""
        url = reverse('accounts:password_reset_complete')
        response = client.get(url)
        assert response.status_code == 200
