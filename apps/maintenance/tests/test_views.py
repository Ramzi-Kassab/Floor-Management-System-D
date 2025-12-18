"""
Tests for Maintenance app views.
"""
import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from apps.common.tests.base import BaseCRUDTest, BasePermissionTest
from apps.maintenance.models import Equipment, MaintenanceRequest, MaintenanceWorkOrder

User = get_user_model()


class TestEquipmentCategoryViews:
    """Tests for EquipmentCategory views."""

    def test_category_list_requires_login(self, client):
        """Test category list requires authentication."""
        url = reverse('maintenance:category_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_category_list_authenticated(self, authenticated_client, equipment_category):
        """Test category list for authenticated users."""
        url = reverse('maintenance:category_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_category_create_get(self, authenticated_client):
        """Test category create form."""
        url = reverse('maintenance:category_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_category_update_get(self, authenticated_client, equipment_category):
        """Test category update form."""
        url = reverse('maintenance:category_update', kwargs={'pk': equipment_category.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestEquipmentViews(BaseCRUDTest):
    """Tests for Equipment views."""

    app_name = 'maintenance'
    model_name = 'equipment'
    url_list = 'maintenance:equipment_list'
    url_detail = 'maintenance:equipment_detail'
    url_create = 'maintenance:equipment_create'
    url_update = 'maintenance:equipment_update'
    url_delete = None
    template_list = 'maintenance/equipment_list.html'
    template_detail = 'maintenance/equipment_detail.html'
    template_form = 'maintenance/equipment_form.html'
    test_delete = False

    @pytest.fixture
    def test_object(self, equipment):
        """Use equipment fixture as test object."""
        return equipment

    @pytest.fixture
    def valid_data(self, equipment_category):
        """Valid data for equipment creation."""
        return {
            'code': 'EQUIP-NEW',
            'name': 'New Equipment',
            'status': Equipment.Status.OPERATIONAL,
        }


class TestMaintenanceRequestViews:
    """Tests for MaintenanceRequest views."""

    def test_request_list_requires_login(self, client):
        """Test request list requires authentication."""
        url = reverse('maintenance:request_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_request_list_authenticated(self, authenticated_client, maintenance_request):
        """Test request list for authenticated users."""
        url = reverse('maintenance:request_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_request_detail(self, authenticated_client, maintenance_request):
        """Test request detail view."""
        url = reverse('maintenance:request_detail', kwargs={'pk': maintenance_request.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_request_create_get(self, authenticated_client):
        """Test request create form."""
        url = reverse('maintenance:request_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_request_approve_requires_login(self, client, maintenance_request):
        """Test request approve requires authentication."""
        url = reverse('maintenance:request_approve', kwargs={'pk': maintenance_request.pk})
        response = client.get(url)
        assert response.status_code == 302


class TestMWOViews:
    """Tests for MaintenanceWorkOrder views."""

    def test_mwo_list_requires_login(self, client):
        """Test MWO list requires authentication."""
        url = reverse('maintenance:mwo_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_mwo_list_authenticated(self, authenticated_client, maintenance_work_order):
        """Test MWO list for authenticated users."""
        url = reverse('maintenance:mwo_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_mwo_detail(self, authenticated_client, maintenance_work_order):
        """Test MWO detail view."""
        url = reverse('maintenance:mwo_detail', kwargs={'pk': maintenance_work_order.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_mwo_create_get(self, authenticated_client):
        """Test MWO create form."""
        url = reverse('maintenance:mwo_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_mwo_update_get(self, authenticated_client, maintenance_work_order):
        """Test MWO update form."""
        url = reverse('maintenance:mwo_update', kwargs={'pk': maintenance_work_order.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_mwo_start_requires_login(self, client, maintenance_work_order):
        """Test MWO start requires authentication."""
        url = reverse('maintenance:mwo_start', kwargs={'pk': maintenance_work_order.pk})
        response = client.post(url)
        assert response.status_code == 302

    def test_mwo_complete_requires_login(self, client, maintenance_work_order):
        """Test MWO complete requires authentication."""
        url = reverse('maintenance:mwo_complete', kwargs={'pk': maintenance_work_order.pk})
        response = client.post(url)
        assert response.status_code == 302


class TestPreventiveMaintenanceViews:
    """Tests for Preventive Maintenance schedule views."""

    def test_pm_schedule_requires_login(self, client):
        """Test PM schedule requires authentication."""
        url = reverse('maintenance:pm_schedule')
        response = client.get(url)
        assert response.status_code == 302

    def test_pm_schedule_authenticated(self, authenticated_client):
        """Test PM schedule for authenticated users."""
        url = reverse('maintenance:pm_schedule')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestMaintenancePermissions(BasePermissionTest):
    """Test maintenance permissions."""

    url_name = 'maintenance:equipment_list'

    def test_equipment_list_requires_auth(self, client):
        """Test equipment list requires authentication."""
        url = reverse(self.url_name)
        response = client.get(url)
        assert response.status_code == 302
