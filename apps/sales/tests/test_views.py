"""
Sales App - View Tests
Comprehensive tests for all sales views.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse


# =============================================================================
# CUSTOMER VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestCustomerViews:
    """Tests for Customer views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test customer list view returns 200."""
        url = reverse('sales:customer_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test customer list view requires authentication."""
        url = reverse('sales:customer_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_detail_view_returns_200(self, authenticated_client, customer):
        """Test customer detail view returns 200."""
        url = reverse('sales:customer_detail', kwargs={'pk': customer.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test customer create view returns 200."""
        url = reverse('sales:customer_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_view_returns_200(self, authenticated_client, customer):
        """Test customer update view returns 200."""
        url = reverse('sales:customer_update', kwargs={'pk': customer.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_search(self, authenticated_client, customer):
        """Test customer list view search."""
        url = reverse('sales:customer_list')
        response = authenticated_client.get(url, {'q': customer.name})
        assert response.status_code == 200

    def test_list_view_filter_active(self, authenticated_client, customer):
        """Test customer list view filter by active status."""
        url = reverse('sales:customer_list')
        response = authenticated_client.get(url, {'is_active': 'true'})
        assert response.status_code == 200


# =============================================================================
# CUSTOMER CONTACT VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestCustomerContactViews:
    """Tests for CustomerContact views."""

    def test_list_view_returns_200(self, authenticated_client, customer):
        """Test contact list view returns 200."""
        url = reverse('sales:customercontact_list', kwargs={'customer_pk': customer.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client, customer):
        """Test contact create view returns 200."""
        url = reverse('sales:customercontact_create', kwargs={'customer_pk': customer.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# RIG VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestRigViews:
    """Tests for Rig views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test rig list view returns 200."""
        url = reverse('sales:rig_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test rig list view requires authentication."""
        url = reverse('sales:rig_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_detail_view_returns_200(self, authenticated_client, rig):
        """Test rig detail view returns 200."""
        url = reverse('sales:rig_detail', kwargs={'pk': rig.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test rig create view returns 200."""
        url = reverse('sales:rig_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_view_returns_200(self, authenticated_client, rig):
        """Test rig update view returns 200."""
        url = reverse('sales:rig_update', kwargs={'pk': rig.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# WELL VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestWellViews:
    """Tests for Well views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test well list view returns 200."""
        url = reverse('sales:well_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test well list view requires authentication."""
        url = reverse('sales:well_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_detail_view_returns_200(self, authenticated_client, well):
        """Test well detail view returns 200."""
        url = reverse('sales:well_detail', kwargs={'pk': well.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test well create view returns 200."""
        url = reverse('sales:well_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# WAREHOUSE VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestWarehouseViews:
    """Tests for Warehouse views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test warehouse list view returns 200."""
        url = reverse('sales:warehouse_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test warehouse list view requires authentication."""
        url = reverse('sales:warehouse_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_detail_view_returns_200(self, authenticated_client, warehouse_ardt):
        """Test warehouse detail view returns 200."""
        url = reverse('sales:warehouse_detail', kwargs={'pk': warehouse_ardt.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# SALES ORDER VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestSalesOrderViews:
    """Tests for SalesOrder views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test sales order list view returns 200."""
        url = reverse('sales:salesorder_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test sales order list view requires authentication."""
        url = reverse('sales:salesorder_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_detail_view_returns_200(self, authenticated_client, sales_order):
        """Test sales order detail view returns 200."""
        url = reverse('sales:salesorder_detail', kwargs={'pk': sales_order.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test sales order create view returns 200."""
        url = reverse('sales:salesorder_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_view_returns_200(self, authenticated_client, sales_order):
        """Test sales order update view returns 200."""
        url = reverse('sales:salesorder_update', kwargs={'pk': sales_order.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_filter_by_status(self, authenticated_client, sales_order):
        """Test sales order list view filter by status."""
        from apps.sales.models import SalesOrder
        url = reverse('sales:salesorder_list')
        response = authenticated_client.get(url, {'status': SalesOrder.Status.DRAFT})
        assert response.status_code == 200


# =============================================================================
# SERVICE SITE VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestServiceSiteViews:
    """Tests for ServiceSite views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test service site list view returns 200."""
        url = reverse('sales:servicesite_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test service site list view requires authentication."""
        url = reverse('sales:servicesite_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_detail_view_returns_200(self, authenticated_client, service_site):
        """Test service site detail view returns 200."""
        url = reverse('sales:servicesite_detail', kwargs={'pk': service_site.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test service site create view returns 200."""
        url = reverse('sales:servicesite_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# FIELD TECHNICIAN VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestFieldTechnicianViews:
    """Tests for FieldTechnician views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test field technician list view returns 200."""
        url = reverse('sales:fieldtechnician_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test field technician list view requires authentication."""
        url = reverse('sales:fieldtechnician_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_detail_view_returns_200(self, authenticated_client, field_technician):
        """Test field technician detail view returns 200."""
        url = reverse('sales:fieldtechnician_detail', kwargs={'pk': field_technician.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# FIELD SERVICE REQUEST VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestFieldServiceRequestViews:
    """Tests for FieldServiceRequest views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test field service request list view returns 200."""
        url = reverse('sales:fieldservicerequest_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test field service request list view requires authentication."""
        url = reverse('sales:fieldservicerequest_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_detail_view_returns_200(self, authenticated_client, field_service_request):
        """Test field service request detail view returns 200."""
        url = reverse('sales:fieldservicerequest_detail', kwargs={'pk': field_service_request.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test field service request create view returns 200."""
        url = reverse('sales:fieldservicerequest_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# DASHBOARD/SUMMARY VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestDashboardViews:
    """Tests for dashboard and summary views."""

    def test_sales_dashboard_returns_200(self, authenticated_client):
        """Test sales dashboard returns 200."""
        url = reverse('sales:dashboard')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_sales_dashboard_requires_login(self, client):
        """Test sales dashboard requires authentication."""
        url = reverse('sales:dashboard')
        response = client.get(url)
        assert response.status_code == 302


# =============================================================================
# EXPORT VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestExportViews:
    """Tests for export views."""

    def test_customer_export_csv(self, authenticated_client, customer):
        """Test customer CSV export."""
        url = reverse('sales:customer_export_csv')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'

    def test_sales_order_export_csv(self, authenticated_client, sales_order):
        """Test sales order CSV export."""
        url = reverse('sales:salesorder_export_csv')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'
