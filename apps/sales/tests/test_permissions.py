"""
Sales App - Permission Tests
Access control and authorization tests.
"""

import pytest
from django.urls import reverse


# =============================================================================
# UNAUTHENTICATED ACCESS TESTS
# =============================================================================

@pytest.mark.django_db
class TestUnauthenticatedAccess:
    """Tests for unauthenticated access restrictions."""

    def test_customer_list_redirects_to_login(self, client):
        """Test customer list redirects unauthenticated users."""
        url = reverse('sales:customer_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_customer_detail_redirects_to_login(self, client, customer):
        """Test customer detail redirects unauthenticated users."""
        url = reverse('sales:customer_detail', kwargs={'pk': customer.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_customer_create_redirects_to_login(self, client):
        """Test customer create redirects unauthenticated users."""
        url = reverse('sales:customer_create')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_rig_list_redirects_to_login(self, client):
        """Test rig list redirects unauthenticated users."""
        url = reverse('sales:rig_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_well_list_redirects_to_login(self, client):
        """Test well list redirects unauthenticated users."""
        url = reverse('sales:well_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_warehouse_list_redirects_to_login(self, client):
        """Test warehouse list redirects unauthenticated users."""
        url = reverse('sales:warehouse_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_sales_order_list_redirects_to_login(self, client):
        """Test sales order list redirects unauthenticated users."""
        url = reverse('sales:salesorder_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_service_site_list_redirects_to_login(self, client):
        """Test service site list redirects unauthenticated users."""
        url = reverse('sales:servicesite_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_field_technician_list_redirects_to_login(self, client):
        """Test field technician list redirects unauthenticated users."""
        url = reverse('sales:fieldtechnician_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_field_service_request_list_redirects_to_login(self, client):
        """Test field service request list redirects unauthenticated users."""
        url = reverse('sales:fieldservicerequest_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url


# =============================================================================
# AUTHENTICATED USER ACCESS TESTS
# =============================================================================

@pytest.mark.django_db
class TestAuthenticatedUserAccess:
    """Tests for authenticated regular user access."""

    def test_regular_user_can_view_customers(self, authenticated_client, customer):
        """Test regular user can view customers."""
        url = reverse('sales:customer_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_view_customer_detail(self, authenticated_client, customer):
        """Test regular user can view customer detail."""
        url = reverse('sales:customer_detail', kwargs={'pk': customer.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_create_customer(self, authenticated_client):
        """Test regular user can access customer create form."""
        url = reverse('sales:customer_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_view_rigs(self, authenticated_client):
        """Test regular user can view rigs."""
        url = reverse('sales:rig_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_view_wells(self, authenticated_client):
        """Test regular user can view wells."""
        url = reverse('sales:well_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_view_sales_orders(self, authenticated_client):
        """Test regular user can view sales orders."""
        url = reverse('sales:salesorder_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_view_service_sites(self, authenticated_client):
        """Test regular user can view service sites."""
        url = reverse('sales:servicesite_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# STAFF USER ACCESS TESTS
# =============================================================================

@pytest.mark.django_db
class TestStaffUserAccess:
    """Tests for staff user access."""

    def test_staff_user_can_view_all_customers(self, staff_client, customer):
        """Test staff user can view all customers."""
        url = reverse('sales:customer_list')
        response = staff_client.get(url)
        assert response.status_code == 200

    def test_staff_user_can_create_customer(self, staff_client):
        """Test staff user can create customers."""
        url = reverse('sales:customer_create')
        response = staff_client.get(url)
        assert response.status_code == 200

    def test_staff_user_can_update_customer(self, staff_client, customer):
        """Test staff user can update customers."""
        url = reverse('sales:customer_update', kwargs={'pk': customer.pk})
        response = staff_client.get(url)
        assert response.status_code == 200

    def test_staff_user_can_view_sales_orders(self, staff_client, sales_order):
        """Test staff user can view sales orders."""
        url = reverse('sales:salesorder_detail', kwargs={'pk': sales_order.pk})
        response = staff_client.get(url)
        assert response.status_code == 200


# =============================================================================
# ADMIN USER ACCESS TESTS
# =============================================================================

@pytest.mark.django_db
class TestAdminUserAccess:
    """Tests for admin user access."""

    def test_admin_can_view_all_views(self, admin_client, customer, rig, well, sales_order, service_site):
        """Test admin can access all views."""
        urls = [
            reverse('sales:customer_list'),
            reverse('sales:customer_detail', kwargs={'pk': customer.pk}),
            reverse('sales:customer_create'),
            reverse('sales:customer_update', kwargs={'pk': customer.pk}),
            reverse('sales:rig_list'),
            reverse('sales:rig_detail', kwargs={'pk': rig.pk}),
            reverse('sales:well_list'),
            reverse('sales:well_detail', kwargs={'pk': well.pk}),
            reverse('sales:salesorder_list'),
            reverse('sales:salesorder_detail', kwargs={'pk': sales_order.pk}),
            reverse('sales:servicesite_list'),
            reverse('sales:servicesite_detail', kwargs={'pk': service_site.pk}),
        ]
        for url in urls:
            response = admin_client.get(url)
            assert response.status_code == 200, f"Admin denied access to {url}"


# =============================================================================
# CREATE PERMISSION TESTS
# =============================================================================

@pytest.mark.django_db
class TestCreatePermissions:
    """Tests for create operation permissions."""

    def test_create_customer_requires_login(self, client):
        """Test creating customer requires authentication."""
        url = reverse('sales:customer_create')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_create_rig_requires_login(self, client):
        """Test creating rig requires authentication."""
        url = reverse('sales:rig_create')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_create_well_requires_login(self, client):
        """Test creating well requires authentication."""
        url = reverse('sales:well_create')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_create_sales_order_requires_login(self, client):
        """Test creating sales order requires authentication."""
        url = reverse('sales:salesorder_create')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_create_service_site_requires_login(self, client):
        """Test creating service site requires authentication."""
        url = reverse('sales:servicesite_create')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_create_field_service_request_requires_login(self, client):
        """Test creating field service request requires authentication."""
        url = reverse('sales:fieldservicerequest_create')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url


# =============================================================================
# UPDATE PERMISSION TESTS
# =============================================================================

@pytest.mark.django_db
class TestUpdatePermissions:
    """Tests for update operation permissions."""

    def test_update_customer_requires_login(self, client, customer):
        """Test updating customer requires authentication."""
        url = reverse('sales:customer_update', kwargs={'pk': customer.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_update_rig_requires_login(self, client, rig):
        """Test updating rig requires authentication."""
        url = reverse('sales:rig_update', kwargs={'pk': rig.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_update_sales_order_requires_login(self, client, sales_order):
        """Test updating sales order requires authentication."""
        url = reverse('sales:salesorder_update', kwargs={'pk': sales_order.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_authenticated_can_update_customer(self, authenticated_client, customer):
        """Test authenticated user can update customer."""
        url = reverse('sales:customer_update', kwargs={'pk': customer.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_authenticated_can_update_rig(self, authenticated_client, rig):
        """Test authenticated user can update rig."""
        url = reverse('sales:rig_update', kwargs={'pk': rig.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# DELETE PERMISSION TESTS
# =============================================================================

@pytest.mark.django_db
class TestDeletePermissions:
    """Tests for delete operation permissions."""

    def test_delete_customer_requires_login(self, client, customer):
        """Test deleting customer requires authentication."""
        url = reverse('sales:customer_delete', kwargs={'pk': customer.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_authenticated_can_access_delete_confirmation(self, authenticated_client, customer):
        """Test authenticated user can access delete confirmation."""
        url = reverse('sales:customer_delete', kwargs={'pk': customer.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# EXPORT PERMISSION TESTS
# =============================================================================

@pytest.mark.django_db
class TestExportPermissions:
    """Tests for export operation permissions."""

    def test_customer_export_requires_login(self, client):
        """Test customer export requires authentication."""
        url = reverse('sales:customer_export_csv')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_sales_order_export_requires_login(self, client):
        """Test sales order export requires authentication."""
        url = reverse('sales:salesorder_export_csv')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_authenticated_can_export_customers(self, authenticated_client, customer):
        """Test authenticated user can export customers."""
        url = reverse('sales:customer_export_csv')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'

    def test_authenticated_can_export_sales_orders(self, authenticated_client, sales_order):
        """Test authenticated user can export sales orders."""
        url = reverse('sales:salesorder_export_csv')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'


# =============================================================================
# DASHBOARD PERMISSION TESTS
# =============================================================================

@pytest.mark.django_db
class TestDashboardPermissions:
    """Tests for dashboard access permissions."""

    def test_dashboard_requires_login(self, client):
        """Test dashboard requires authentication."""
        url = reverse('sales:dashboard')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_authenticated_can_access_dashboard(self, authenticated_client):
        """Test authenticated user can access dashboard."""
        url = reverse('sales:dashboard')
        response = authenticated_client.get(url)
        assert response.status_code == 200
