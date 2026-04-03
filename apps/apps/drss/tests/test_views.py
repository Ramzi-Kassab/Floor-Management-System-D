"""
Tests for DRSS app views.
"""
import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from apps.common.tests.base import BaseCRUDTest

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
def drss_request(db, test_user):
    """Create a test DRSS request."""
    from apps.drss.models import DRSSRequest
    return DRSSRequest.objects.create(
        request_number='DRSS-001',
        title='Test DRSS Request',
        description='Test description',
        status='DRAFT',
        created_by=test_user
    )


class TestDRSSViews(BaseCRUDTest):
    """Tests for DRSS views."""

    app_name = 'drss'
    model_name = 'drss'
    url_list = 'drss:drss_list'
    url_detail = 'drss:drss_detail'
    url_create = 'drss:drss_create'
    url_update = 'drss:drss_update'
    url_delete = None
    template_list = 'drss/drss_list.html'
    template_detail = 'drss/drss_detail.html'
    template_form = 'drss/drss_form.html'
    test_delete = False

    @pytest.fixture
    def test_object(self, drss_request):
        return drss_request

    @pytest.fixture
    def valid_data(self):
        return {
            'request_number': 'DRSS-NEW',
            'title': 'New DRSS Request',
            'description': 'New description',
            'status': 'DRAFT',
        }


class TestDRSSLineViews:
    """Tests for DRSS Line views."""

    def test_add_line_requires_login(self, client, drss_request):
        url = reverse('drss:line_add', kwargs={'drss_pk': drss_request.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_add_line_get(self, authenticated_client, drss_request):
        url = reverse('drss:line_add', kwargs={'drss_pk': drss_request.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestDRSSExport:
    """Tests for DRSS export functionality."""

    def test_export_requires_login(self, client):
        url = reverse('drss:drss_export')
        response = client.get(url)
        assert response.status_code == 302

    def test_export_authenticated(self, authenticated_client):
        url = reverse('drss:drss_export')
        response = authenticated_client.get(url)
        assert response.status_code == 200
