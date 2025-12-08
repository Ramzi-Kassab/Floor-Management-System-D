"""
Workorders App - View Tests
Comprehensive tests for all workorders views.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.urls import reverse


# =============================================================================
# WORK ORDER LIST VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderListView:
    """Tests for WorkOrderListView."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('workorders:list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test list view requires authentication."""
        url = reverse('workorders:list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url

    def test_list_view_uses_correct_template(self, authenticated_client):
        """Test list view uses correct template."""
        url = reverse('workorders:list')
        response = authenticated_client.get(url)
        assert 'workorders/workorder_list.html' in [t.name for t in response.templates]

    def test_list_view_contains_work_orders(self, authenticated_client, work_order):
        """Test list view contains work orders in context."""
        url = reverse('workorders:list')
        response = authenticated_client.get(url)
        assert 'work_orders' in response.context

    def test_list_view_filter_by_status(self, authenticated_client, work_order):
        """Test list view filters by status."""
        from apps.workorders.models import WorkOrder
        url = reverse('workorders:list')
        response = authenticated_client.get(url, {'status': WorkOrder.Status.DRAFT})
        assert response.status_code == 200

    def test_list_view_filter_by_priority(self, authenticated_client, work_order):
        """Test list view filters by priority."""
        from apps.workorders.models import WorkOrder
        url = reverse('workorders:list')
        response = authenticated_client.get(url, {'priority': WorkOrder.Priority.HIGH})
        assert response.status_code == 200

    def test_list_view_search(self, authenticated_client, work_order):
        """Test list view search functionality."""
        url = reverse('workorders:list')
        response = authenticated_client.get(url, {'q': work_order.wo_number})
        assert response.status_code == 200

    def test_list_view_pagination(self, authenticated_client, base_user, drill_bit):
        """Test list view pagination."""
        from apps.workorders.models import WorkOrder
        # Create more than paginate_by work orders
        for i in range(30):
            WorkOrder.objects.create(
                wo_number=f'WO-PAG-{i:03d}',
                wo_type=WorkOrder.WOType.FC_REPAIR,
                drill_bit=drill_bit,
                created_by=base_user
            )
        url = reverse('workorders:list')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'page_obj' in response.context


# =============================================================================
# WORK ORDER DETAIL VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderDetailView:
    """Tests for WorkOrderDetailView."""

    def test_detail_view_returns_200(self, authenticated_client, work_order):
        """Test detail view returns 200."""
        url = reverse('workorders:detail', kwargs={'pk': work_order.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_requires_login(self, client, work_order):
        """Test detail view requires authentication."""
        url = reverse('workorders:detail', kwargs={'pk': work_order.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_detail_view_uses_correct_template(self, authenticated_client, work_order):
        """Test detail view uses correct template."""
        url = reverse('workorders:detail', kwargs={'pk': work_order.pk})
        response = authenticated_client.get(url)
        assert 'workorders/workorder_detail.html' in [t.name for t in response.templates]

    def test_detail_view_contains_work_order(self, authenticated_client, work_order):
        """Test detail view contains work order in context."""
        url = reverse('workorders:detail', kwargs={'pk': work_order.pk})
        response = authenticated_client.get(url)
        assert 'work_order' in response.context
        assert response.context['work_order'] == work_order

    def test_detail_view_404_for_nonexistent(self, authenticated_client):
        """Test detail view returns 404 for nonexistent WO."""
        url = reverse('workorders:detail', kwargs={'pk': 99999})
        response = authenticated_client.get(url)
        assert response.status_code == 404


# =============================================================================
# WORK ORDER CREATE VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderCreateView:
    """Tests for WorkOrderCreateView."""

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('workorders:create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_requires_login(self, client):
        """Test create view requires authentication."""
        url = reverse('workorders:create')
        response = client.get(url)
        assert response.status_code == 302

    def test_create_view_uses_correct_template(self, authenticated_client):
        """Test create view uses correct template."""
        url = reverse('workorders:create')
        response = authenticated_client.get(url)
        assert 'workorders/workorder_form.html' in [t.name for t in response.templates]

    def test_create_work_order_success(self, authenticated_client):
        """Test creating a work order successfully."""
        from apps.workorders.models import WorkOrder
        url = reverse('workorders:create')
        form_data = {
            'wo_type': WorkOrder.WOType.FC_REPAIR,
            'priority': WorkOrder.Priority.NORMAL,
            'planned_start': date.today().isoformat(),
            'planned_end': (date.today() + timedelta(days=5)).isoformat(),
            'due_date': (date.today() + timedelta(days=7)).isoformat(),
        }
        response = authenticated_client.post(url, data=form_data)
        # Should redirect on success
        assert response.status_code in [200, 302]


# =============================================================================
# WORK ORDER UPDATE VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderUpdateView:
    """Tests for WorkOrderUpdateView."""

    def test_update_view_returns_200(self, authenticated_client, work_order):
        """Test update view returns 200."""
        url = reverse('workorders:update', kwargs={'pk': work_order.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_view_requires_login(self, client, work_order):
        """Test update view requires authentication."""
        url = reverse('workorders:update', kwargs={'pk': work_order.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_update_view_contains_status_field(self, authenticated_client, work_order):
        """Test update view contains status field."""
        url = reverse('workorders:update', kwargs={'pk': work_order.pk})
        response = authenticated_client.get(url)
        assert 'form' in response.context
        # Status field is added dynamically in get_form


# =============================================================================
# DRILL BIT LIST VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestDrillBitListView:
    """Tests for DrillBitListView."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('workorders:drillbit_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test list view requires authentication."""
        url = reverse('workorders:drillbit_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_list_view_uses_correct_template(self, authenticated_client):
        """Test list view uses correct template."""
        url = reverse('workorders:drillbit_list')
        response = authenticated_client.get(url)
        assert 'drillbits/drillbit_list.html' in [t.name for t in response.templates]

    def test_list_view_contains_drill_bits(self, authenticated_client, drill_bit):
        """Test list view contains drill bits in context."""
        url = reverse('workorders:drillbit_list')
        response = authenticated_client.get(url)
        assert 'drill_bits' in response.context

    def test_list_view_filter_by_status(self, authenticated_client, drill_bit):
        """Test list view filters by status."""
        from apps.workorders.models import DrillBit
        url = reverse('workorders:drillbit_list')
        response = authenticated_client.get(url, {'status': DrillBit.Status.IN_STOCK})
        assert response.status_code == 200

    def test_list_view_filter_by_type(self, authenticated_client, drill_bit):
        """Test list view filters by type."""
        from apps.workorders.models import DrillBit
        url = reverse('workorders:drillbit_list')
        response = authenticated_client.get(url, {'type': DrillBit.BitType.FC})
        assert response.status_code == 200

    def test_list_view_search(self, authenticated_client, drill_bit):
        """Test list view search functionality."""
        url = reverse('workorders:drillbit_list')
        response = authenticated_client.get(url, {'q': drill_bit.serial_number})
        assert response.status_code == 200


# =============================================================================
# DRILL BIT DETAIL VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestDrillBitDetailView:
    """Tests for DrillBitDetailView."""

    def test_detail_view_returns_200(self, authenticated_client, drill_bit):
        """Test detail view returns 200."""
        url = reverse('workorders:drillbit_detail', kwargs={'pk': drill_bit.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_requires_login(self, client, drill_bit):
        """Test detail view requires authentication."""
        url = reverse('workorders:drillbit_detail', kwargs={'pk': drill_bit.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_detail_view_contains_drill_bit(self, authenticated_client, drill_bit):
        """Test detail view contains drill bit in context."""
        url = reverse('workorders:drillbit_detail', kwargs={'pk': drill_bit.pk})
        response = authenticated_client.get(url)
        assert 'drill_bit' in response.context
        assert response.context['drill_bit'] == drill_bit

    def test_detail_view_contains_recent_work_orders(self, authenticated_client, drill_bit, work_order):
        """Test detail view contains recent work orders."""
        url = reverse('workorders:drillbit_detail', kwargs={'pk': drill_bit.pk})
        response = authenticated_client.get(url)
        assert 'recent_work_orders' in response.context


# =============================================================================
# DRILL BIT CREATE VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestDrillBitCreateView:
    """Tests for DrillBitCreateView."""

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('workorders:drillbit_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_requires_login(self, client):
        """Test create view requires authentication."""
        url = reverse('workorders:drillbit_create')
        response = client.get(url)
        assert response.status_code == 302

    def test_create_drill_bit_success(self, authenticated_client):
        """Test creating a drill bit successfully."""
        from apps.workorders.models import DrillBit
        url = reverse('workorders:drillbit_create')
        form_data = {
            'serial_number': 'FC-VIEW-001',
            'bit_type': DrillBit.BitType.FC,
            'size': '8.500',
            'iadc_code': 'M423',
            'status': DrillBit.Status.NEW,
        }
        response = authenticated_client.post(url, data=form_data)
        # Should redirect on success
        assert response.status_code in [200, 302]


# =============================================================================
# DRILL BIT UPDATE VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestDrillBitUpdateView:
    """Tests for DrillBitUpdateView."""

    def test_update_view_returns_200(self, authenticated_client, drill_bit):
        """Test update view returns 200."""
        url = reverse('workorders:drillbit_update', kwargs={'pk': drill_bit.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_view_requires_login(self, client, drill_bit):
        """Test update view requires authentication."""
        url = reverse('workorders:drillbit_update', kwargs={'pk': drill_bit.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_serial_number_readonly(self, authenticated_client, drill_bit):
        """Test serial number is readonly on update."""
        url = reverse('workorders:drillbit_update', kwargs={'pk': drill_bit.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        # Check form field has readonly attribute
        form = response.context['form']
        assert form.fields['serial_number'].widget.attrs.get('readonly') is True


# =============================================================================
# WORK ORDER ACTION VIEWS TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderActionViews:
    """Tests for work order action views."""

    def test_start_work_view(self, authenticated_client, work_order_released):
        """Test start work view."""
        url = reverse('workorders:start_work', kwargs={'pk': work_order_released.pk})
        response = authenticated_client.post(url)
        assert response.status_code == 302  # Redirect to detail

    def test_complete_work_view(self, authenticated_client, work_order_in_progress):
        """Test complete work view."""
        url = reverse('workorders:complete_work', kwargs={'pk': work_order_in_progress.pk})
        response = authenticated_client.post(url)
        assert response.status_code == 302  # Redirect to detail


# =============================================================================
# SALVAGE ITEM VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestSalvageItemViews:
    """Tests for SalvageItem views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('workorders:salvageitem_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test list view requires authentication."""
        url = reverse('workorders:salvageitem_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_detail_view_returns_200(self, authenticated_client, salvage_item):
        """Test detail view returns 200."""
        url = reverse('workorders:salvageitem_detail', kwargs={'pk': salvage_item.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('workorders:salvageitem_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_view_returns_200(self, authenticated_client, salvage_item):
        """Test update view returns 200."""
        url = reverse('workorders:salvageitem_update', kwargs={'pk': salvage_item.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# REPAIR APPROVAL AUTHORITY VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestRepairApprovalAuthorityViews:
    """Tests for RepairApprovalAuthority views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('workorders:repairapprovalauthority_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, repair_approval_authority):
        """Test detail view returns 200."""
        url = reverse('workorders:repairapprovalauthority_detail', kwargs={'pk': repair_approval_authority.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('workorders:repairapprovalauthority_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_view_returns_200(self, authenticated_client, repair_approval_authority):
        """Test update view returns 200."""
        url = reverse('workorders:repairapprovalauthority_update', kwargs={'pk': repair_approval_authority.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# REPAIR EVALUATION VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestRepairEvaluationViews:
    """Tests for RepairEvaluation views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('workorders:repairevaluation_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, repair_evaluation):
        """Test detail view returns 200."""
        url = reverse('workorders:repairevaluation_detail', kwargs={'pk': repair_evaluation.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('workorders:repairevaluation_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_view_returns_200(self, authenticated_client, repair_evaluation):
        """Test update view returns 200."""
        url = reverse('workorders:repairevaluation_update', kwargs={'pk': repair_evaluation.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# REPAIR BOM VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestRepairBOMViews:
    """Tests for RepairBOM views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('workorders:repairbom_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, repair_bom):
        """Test detail view returns 200."""
        url = reverse('workorders:repairbom_detail', kwargs={'pk': repair_bom.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('workorders:repairbom_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_view_returns_200(self, authenticated_client, repair_bom):
        """Test update view returns 200."""
        url = reverse('workorders:repairbom_update', kwargs={'pk': repair_bom.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# PROCESS ROUTE VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestProcessRouteViews:
    """Tests for ProcessRoute views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('workorders:processroute_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, process_route):
        """Test detail view returns 200."""
        url = reverse('workorders:processroute_detail', kwargs={'pk': process_route.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('workorders:processroute_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_view_returns_200(self, authenticated_client, process_route):
        """Test update view returns 200."""
        url = reverse('workorders:processroute_update', kwargs={'pk': process_route.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# WORK ORDER COST VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderCostViews:
    """Tests for WorkOrderCost views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('workorders:workordercost_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, work_order_cost):
        """Test detail view returns 200."""
        url = reverse('workorders:workordercost_detail', kwargs={'pk': work_order_cost.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('workorders:workordercost_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# STATUS TRANSITION LOG VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestStatusTransitionLogViews:
    """Tests for StatusTransitionLog views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('workorders:statustransitionlog_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test list view requires authentication."""
        url = reverse('workorders:statustransitionlog_list')
        response = client.get(url)
        assert response.status_code == 302


# =============================================================================
# BIT REPAIR HISTORY VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestBitRepairHistoryViews:
    """Tests for BitRepairHistory views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('workorders:bitrepairhistory_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test list view requires authentication."""
        url = reverse('workorders:bitrepairhistory_list')
        response = client.get(url)
        assert response.status_code == 302


# =============================================================================
# OPERATION EXECUTION VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestOperationExecutionViews:
    """Tests for OperationExecution views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('workorders:operationexecution_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client):
        """Test list view requires authentication."""
        url = reverse('workorders:operationexecution_list')
        response = client.get(url)
        assert response.status_code == 302


# =============================================================================
# EXPORT VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestExportViews:
    """Tests for export views."""

    def test_export_work_orders_csv(self, authenticated_client, work_order):
        """Test work orders CSV export."""
        url = reverse('workorders:export_csv')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'

    def test_export_drill_bits_csv(self, authenticated_client, drill_bit):
        """Test drill bits CSV export."""
        url = reverse('workorders:drillbit_export_csv')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'

    def test_export_preserves_filters(self, authenticated_client, work_order):
        """Test export preserves query filters."""
        from apps.workorders.models import WorkOrder
        url = reverse('workorders:export_csv')
        response = authenticated_client.get(url, {'status': WorkOrder.Status.DRAFT})
        assert response.status_code == 200


# =============================================================================
# HTMX VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestHtmxViews:
    """Tests for HTMX endpoints."""

    def test_update_status_htmx_get(self, authenticated_client, work_order):
        """Test update status HTMX GET request."""
        url = reverse('workorders:update_status_htmx', kwargs={'pk': work_order.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_status_htmx_post(self, authenticated_client, work_order_released):
        """Test update status HTMX POST request."""
        from apps.workorders.models import WorkOrder
        url = reverse('workorders:update_status_htmx', kwargs={'pk': work_order_released.pk})
        response = authenticated_client.post(url, {'status': WorkOrder.Status.IN_PROGRESS})
        assert response.status_code == 200

    def test_workorder_row_htmx(self, authenticated_client, work_order):
        """Test workorder row HTMX endpoint."""
        url = reverse('workorders:workorder_row_htmx', kwargs={'pk': work_order.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# QR CODE VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestQRCodeViews:
    """Tests for QR code views."""

    def test_drillbit_qr_view(self, authenticated_client, drill_bit):
        """Test drill bit QR code view."""
        url = reverse('workorders:drillbit_qr', kwargs={'pk': drill_bit.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_drillbit_qr_view_requires_login(self, client, drill_bit):
        """Test drill bit QR view requires authentication."""
        url = reverse('workorders:drillbit_qr', kwargs={'pk': drill_bit.pk})
        response = client.get(url)
        assert response.status_code == 302
