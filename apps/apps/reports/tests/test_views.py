"""
Tests for Reports app views.
"""
import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

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


class TestReportsDashboard:
    """Tests for reports dashboard."""

    def test_dashboard_requires_login(self, client):
        url = reverse('reports:dashboard')
        response = client.get(url)
        assert response.status_code == 302

    def test_dashboard_authenticated(self, authenticated_client):
        url = reverse('reports:dashboard')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestWorkOrderReport:
    """Tests for work order reports."""

    def test_workorder_report_requires_login(self, client):
        url = reverse('reports:workorder_report')
        response = client.get(url)
        assert response.status_code == 302

    def test_workorder_report_authenticated(self, authenticated_client):
        url = reverse('reports:workorder_report')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestInventoryReport:
    """Tests for inventory reports."""

    def test_inventory_report_requires_login(self, client):
        url = reverse('reports:inventory_report')
        response = client.get(url)
        assert response.status_code == 302

    def test_inventory_report_authenticated(self, authenticated_client):
        url = reverse('reports:inventory_report')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_low_stock_alert_requires_login(self, client):
        url = reverse('reports:low_stock_alert')
        response = client.get(url)
        assert response.status_code == 302

    def test_low_stock_alert_authenticated(self, authenticated_client):
        url = reverse('reports:low_stock_alert')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestQualityReport:
    """Tests for quality reports."""

    def test_quality_report_requires_login(self, client):
        url = reverse('reports:quality_report')
        response = client.get(url)
        assert response.status_code == 302

    def test_quality_report_authenticated(self, authenticated_client):
        url = reverse('reports:quality_report')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestMaintenanceReport:
    """Tests for maintenance reports."""

    def test_maintenance_report_requires_login(self, client):
        url = reverse('reports:maintenance_report')
        response = client.get(url)
        assert response.status_code == 302

    def test_maintenance_report_authenticated(self, authenticated_client):
        url = reverse('reports:maintenance_report')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_equipment_health_requires_login(self, client):
        url = reverse('reports:equipment_health')
        response = client.get(url)
        assert response.status_code == 302

    def test_equipment_health_authenticated(self, authenticated_client):
        url = reverse('reports:equipment_health')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestSupplyChainReport:
    """Tests for supply chain reports."""

    def test_supplychain_report_requires_login(self, client):
        url = reverse('reports:supplychain_report')
        response = client.get(url)
        assert response.status_code == 302

    def test_supplychain_report_authenticated(self, authenticated_client):
        url = reverse('reports:supplychain_report')
        response = authenticated_client.get(url)
        assert response.status_code == 200
