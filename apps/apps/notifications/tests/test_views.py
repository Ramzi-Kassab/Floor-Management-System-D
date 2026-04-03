"""
Tests for Notifications app views.
"""
import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def authenticated_client(client, test_user):
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def notification(db, test_user):
    """Create a test notification."""
    from apps.notifications.models import Notification
    return Notification.objects.create(
        recipient=test_user,
        title='Test Notification',
        message='Test message',
        notification_type='INFO',
        is_read=False
    )


@pytest.fixture
def task(db, test_user):
    """Create a test task."""
    from apps.notifications.models import Task
    return Task.objects.create(
        title='Test Task',
        description='Test description',
        assigned_to=test_user,
        status='PENDING',
        priority='NORMAL',
        due_date=timezone.now().date(),
        created_by=test_user
    )


class TestNotificationViews:
    """Tests for Notification views."""

    def test_notification_list_requires_login(self, client):
        url = reverse('notifications:notification_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_notification_list_authenticated(self, authenticated_client, notification):
        url = reverse('notifications:notification_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_notification_mark_read(self, authenticated_client, notification):
        url = reverse('notifications:notification_read', kwargs={'pk': notification.pk})
        response = authenticated_client.post(url)
        assert response.status_code in [200, 302]

    def test_notification_mark_all_read(self, authenticated_client, notification):
        url = reverse('notifications:notification_mark_all_read')
        response = authenticated_client.post(url)
        assert response.status_code in [200, 302]

    def test_notification_delete(self, authenticated_client, notification):
        url = reverse('notifications:notification_delete', kwargs={'pk': notification.pk})
        response = authenticated_client.post(url)
        assert response.status_code in [200, 302]


class TestTaskViews:
    """Tests for Task views."""

    def test_task_list_requires_login(self, client):
        url = reverse('notifications:task_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_task_list_authenticated(self, authenticated_client, task):
        url = reverse('notifications:task_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_task_detail(self, authenticated_client, task):
        url = reverse('notifications:task_detail', kwargs={'pk': task.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_task_create_get(self, authenticated_client):
        url = reverse('notifications:task_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_task_update_get(self, authenticated_client, task):
        url = reverse('notifications:task_update', kwargs={'pk': task.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_task_complete(self, authenticated_client, task):
        url = reverse('notifications:task_complete', kwargs={'pk': task.pk})
        response = authenticated_client.post(url)
        assert response.status_code in [200, 302]


class TestNotificationTemplateViews:
    """Tests for NotificationTemplate views."""

    def test_template_list_requires_login(self, client):
        url = reverse('notifications:template_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_template_list_authenticated(self, authenticated_client):
        url = reverse('notifications:template_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_template_create_get(self, authenticated_client):
        url = reverse('notifications:template_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestAuditLogViews:
    """Tests for AuditLog views."""

    def test_audit_list_requires_login(self, client):
        url = reverse('notifications:audit_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_audit_list_authenticated(self, authenticated_client):
        url = reverse('notifications:audit_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200
