"""
Workorders App - Permission Tests
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

    def test_work_order_list_redirects_to_login(self, client):
        """Test work order list redirects unauthenticated users to login."""
        url = reverse('workorders:list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_work_order_detail_redirects_to_login(self, client, work_order):
        """Test work order detail redirects unauthenticated users to login."""
        url = reverse('workorders:detail', kwargs={'pk': work_order.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_work_order_create_redirects_to_login(self, client):
        """Test work order create redirects unauthenticated users to login."""
        url = reverse('workorders:create')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_work_order_update_redirects_to_login(self, client, work_order):
        """Test work order update redirects unauthenticated users to login."""
        url = reverse('workorders:update', kwargs={'pk': work_order.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_drill_bit_list_redirects_to_login(self, client):
        """Test drill bit list redirects unauthenticated users to login."""
        url = reverse('workorders:drillbit_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_drill_bit_detail_redirects_to_login(self, client, drill_bit):
        """Test drill bit detail redirects unauthenticated users to login."""
        url = reverse('workorders:drillbit_detail', kwargs={'pk': drill_bit.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_drill_bit_create_redirects_to_login(self, client):
        """Test drill bit create redirects unauthenticated users to login."""
        url = reverse('workorders:drillbit_create')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_export_csv_redirects_to_login(self, client):
        """Test CSV export redirects unauthenticated users to login."""
        url = reverse('workorders:export_csv')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_salvage_item_list_redirects_to_login(self, client):
        """Test salvage item list redirects unauthenticated users to login."""
        url = reverse('workorders:salvageitem_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_repair_evaluation_list_redirects_to_login(self, client):
        """Test repair evaluation list redirects unauthenticated users to login."""
        url = reverse('workorders:repairevaluation_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_process_route_list_redirects_to_login(self, client):
        """Test process route list redirects unauthenticated users to login."""
        url = reverse('workorders:processroute_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url


# =============================================================================
# AUTHENTICATED USER ACCESS TESTS
# =============================================================================

@pytest.mark.django_db
class TestAuthenticatedUserAccess:
    """Tests for authenticated regular user access."""

    def test_regular_user_can_view_work_orders(self, authenticated_client, work_order):
        """Test regular user can view work orders."""
        url = reverse('workorders:list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_view_work_order_detail(self, authenticated_client, work_order):
        """Test regular user can view work order detail."""
        url = reverse('workorders:detail', kwargs={'pk': work_order.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_create_work_order(self, authenticated_client):
        """Test regular user can access work order create form."""
        url = reverse('workorders:create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_update_work_order(self, authenticated_client, work_order):
        """Test regular user can access work order update form."""
        url = reverse('workorders:update', kwargs={'pk': work_order.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_view_drill_bits(self, authenticated_client, drill_bit):
        """Test regular user can view drill bits."""
        url = reverse('workorders:drillbit_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_create_drill_bit(self, authenticated_client):
        """Test regular user can access drill bit create form."""
        url = reverse('workorders:drillbit_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_export_csv(self, authenticated_client, work_order):
        """Test regular user can export CSV."""
        url = reverse('workorders:export_csv')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_view_salvage_items(self, authenticated_client):
        """Test regular user can view salvage items."""
        url = reverse('workorders:salvageitem_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_view_repair_evaluations(self, authenticated_client):
        """Test regular user can view repair evaluations."""
        url = reverse('workorders:repairevaluation_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_view_process_routes(self, authenticated_client):
        """Test regular user can view process routes."""
        url = reverse('workorders:processroute_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# STAFF USER ACCESS TESTS
# =============================================================================

@pytest.mark.django_db
class TestStaffUserAccess:
    """Tests for staff user access."""

    def test_staff_user_can_view_work_orders(self, staff_client, work_order):
        """Test staff user can view work orders."""
        url = reverse('workorders:list')
        response = staff_client.get(url)
        assert response.status_code == 200

    def test_staff_user_can_create_work_order(self, staff_client):
        """Test staff user can create work orders."""
        url = reverse('workorders:create')
        response = staff_client.get(url)
        assert response.status_code == 200

    def test_staff_user_can_update_any_work_order(self, staff_client, work_order):
        """Test staff user can update any work order."""
        url = reverse('workorders:update', kwargs={'pk': work_order.pk})
        response = staff_client.get(url)
        assert response.status_code == 200

    def test_staff_user_can_view_status_logs(self, staff_client):
        """Test staff user can view status transition logs."""
        url = reverse('workorders:statustransitionlog_list')
        response = staff_client.get(url)
        assert response.status_code == 200

    def test_staff_user_can_view_bit_repair_history(self, staff_client):
        """Test staff user can view bit repair history."""
        url = reverse('workorders:bitrepairhistory_list')
        response = staff_client.get(url)
        assert response.status_code == 200


# =============================================================================
# ADMIN USER ACCESS TESTS
# =============================================================================

@pytest.mark.django_db
class TestAdminUserAccess:
    """Tests for admin user access."""

    def test_admin_can_view_all_views(self, admin_client, work_order, drill_bit):
        """Test admin can access all views."""
        urls = [
            reverse('workorders:list'),
            reverse('workorders:detail', kwargs={'pk': work_order.pk}),
            reverse('workorders:create'),
            reverse('workorders:update', kwargs={'pk': work_order.pk}),
            reverse('workorders:drillbit_list'),
            reverse('workorders:drillbit_detail', kwargs={'pk': drill_bit.pk}),
            reverse('workorders:salvageitem_list'),
            reverse('workorders:repairevaluation_list'),
            reverse('workorders:processroute_list'),
            reverse('workorders:statustransitionlog_list'),
            reverse('workorders:bitrepairhistory_list'),
        ]
        for url in urls:
            response = admin_client.get(url)
            assert response.status_code == 200, f"Admin denied access to {url}"


# =============================================================================
# ACTION PERMISSION TESTS
# =============================================================================

@pytest.mark.django_db
class TestActionPermissions:
    """Tests for action-specific permissions."""

    def test_authenticated_user_can_start_work(self, authenticated_client, work_order_released):
        """Test authenticated user can start work on a released work order."""
        url = reverse('workorders:start_work', kwargs={'pk': work_order_released.pk})
        response = authenticated_client.post(url)
        assert response.status_code == 302  # Redirect on success

    def test_authenticated_user_can_complete_work(self, authenticated_client, work_order_in_progress):
        """Test authenticated user can complete work on in-progress work order."""
        url = reverse('workorders:complete_work', kwargs={'pk': work_order_in_progress.pk})
        response = authenticated_client.post(url)
        assert response.status_code == 302  # Redirect on success

    def test_unauthenticated_cannot_start_work(self, client, work_order_released):
        """Test unauthenticated user cannot start work."""
        url = reverse('workorders:start_work', kwargs={'pk': work_order_released.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_unauthenticated_cannot_complete_work(self, client, work_order_in_progress):
        """Test unauthenticated user cannot complete work."""
        url = reverse('workorders:complete_work', kwargs={'pk': work_order_in_progress.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert 'login' in response.url


# =============================================================================
# HTMX ENDPOINT PERMISSION TESTS
# =============================================================================

@pytest.mark.django_db
class TestHtmxEndpointPermissions:
    """Tests for HTMX endpoint permissions."""

    def test_htmx_status_update_requires_login(self, client, work_order):
        """Test HTMX status update requires authentication."""
        url = reverse('workorders:update_status_htmx', kwargs={'pk': work_order.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_htmx_row_refresh_requires_login(self, client, work_order):
        """Test HTMX row refresh requires authentication."""
        url = reverse('workorders:workorder_row_htmx', kwargs={'pk': work_order.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_authenticated_can_use_htmx_endpoints(self, authenticated_client, work_order):
        """Test authenticated user can use HTMX endpoints."""
        url = reverse('workorders:update_status_htmx', kwargs={'pk': work_order.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# CRUD PERMISSION TESTS
# =============================================================================

@pytest.mark.django_db
class TestCRUDPermissions:
    """Tests for CRUD operation permissions."""

    def test_create_salvage_item_requires_login(self, client):
        """Test creating salvage item requires authentication."""
        url = reverse('workorders:salvageitem_create')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_update_salvage_item_requires_login(self, client, salvage_item):
        """Test updating salvage item requires authentication."""
        url = reverse('workorders:salvageitem_update', kwargs={'pk': salvage_item.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_create_repair_evaluation_requires_login(self, client):
        """Test creating repair evaluation requires authentication."""
        url = reverse('workorders:repairevaluation_create')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_create_process_route_requires_login(self, client):
        """Test creating process route requires authentication."""
        url = reverse('workorders:processroute_create')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_authenticated_can_create_salvage_item(self, authenticated_client):
        """Test authenticated user can create salvage item."""
        url = reverse('workorders:salvageitem_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_authenticated_can_create_repair_evaluation(self, authenticated_client):
        """Test authenticated user can create repair evaluation."""
        url = reverse('workorders:repairevaluation_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# DELETE PERMISSION TESTS
# =============================================================================

@pytest.mark.django_db
class TestDeletePermissions:
    """Tests for delete operation permissions."""

    def test_delete_salvage_item_requires_login(self, client, salvage_item):
        """Test deleting salvage item requires authentication."""
        url = reverse('workorders:salvageitem_delete', kwargs={'pk': salvage_item.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_authenticated_can_access_delete_confirmation(self, authenticated_client, salvage_item):
        """Test authenticated user can access delete confirmation."""
        url = reverse('workorders:salvageitem_delete', kwargs={'pk': salvage_item.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# EXPORT PERMISSION TESTS
# =============================================================================

@pytest.mark.django_db
class TestExportPermissions:
    """Tests for export operation permissions."""

    def test_work_order_export_requires_login(self, client):
        """Test work order export requires authentication."""
        url = reverse('workorders:export_csv')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_drill_bit_export_requires_login(self, client):
        """Test drill bit export requires authentication."""
        url = reverse('workorders:drillbit_export_csv')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_authenticated_can_export_work_orders(self, authenticated_client, work_order):
        """Test authenticated user can export work orders."""
        url = reverse('workorders:export_csv')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'

    def test_authenticated_can_export_drill_bits(self, authenticated_client, drill_bit):
        """Test authenticated user can export drill bits."""
        url = reverse('workorders:drillbit_export_csv')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'


# =============================================================================
# VIEW-ONLY MODEL PERMISSION TESTS
# =============================================================================

@pytest.mark.django_db
class TestViewOnlyModelPermissions:
    """Tests for view-only models (StatusTransitionLog, BitRepairHistory, OperationExecution)."""

    def test_status_log_list_requires_login(self, client):
        """Test status log list requires authentication."""
        url = reverse('workorders:statustransitionlog_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_repair_history_list_requires_login(self, client):
        """Test repair history list requires authentication."""
        url = reverse('workorders:bitrepairhistory_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_operation_execution_list_requires_login(self, client):
        """Test operation execution list requires authentication."""
        url = reverse('workorders:operationexecution_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_authenticated_can_view_status_logs(self, authenticated_client):
        """Test authenticated user can view status logs."""
        url = reverse('workorders:statustransitionlog_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_authenticated_can_view_repair_history(self, authenticated_client):
        """Test authenticated user can view repair history."""
        url = reverse('workorders:bitrepairhistory_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_authenticated_can_view_operation_executions(self, authenticated_client):
        """Test authenticated user can view operation executions."""
        url = reverse('workorders:operationexecution_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200
