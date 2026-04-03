"""
Dispatch App - View Tests
Comprehensive tests for all dispatch views.

Tests cover:
- Dashboard, list, detail, create, update, delete views
- Authentication requirements
- Template rendering
- Form validation
- Redirect behavior
- Status update functionality
"""

import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.dispatch.models import Vehicle, Dispatch, InventoryReservation

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def authenticated_client(client, user):
    """Return an authenticated client."""
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def vehicle(db):
    """Create a test vehicle."""
    return Vehicle.objects.create(
        code='VH-001',
        plate_number='ABC-1234',
        make='Toyota',
        model='Hilux',
        status=Vehicle.Status.AVAILABLE
    )


@pytest.fixture
def customer(db):
    """Create a test customer."""
    from apps.sales.models import Customer
    return Customer.objects.create(
        code='CUST-001',
        name='Test Customer',
        customer_type='COMMERCIAL'
    )


@pytest.fixture
def dispatch(db, vehicle, customer, user):
    """Create a test dispatch."""
    return Dispatch.objects.create(
        dispatch_number='DISP-001',
        vehicle=vehicle,
        customer=customer,
        planned_date=date.today(),
        created_by=user
    )


# =============================================================================
# DASHBOARD VIEW TESTS
# =============================================================================

class TestDispatchDashboardView:
    """Tests for DispatchDashboardView."""

    def test_dashboard_requires_login(self, client):
        """Test dashboard requires authentication."""
        response = client.get(reverse('dispatch:dashboard'))
        assert response.status_code == 302
        assert 'login' in response.url

    def test_dashboard_authenticated(self, authenticated_client):
        """Test dashboard for authenticated user."""
        response = authenticated_client.get(reverse('dispatch:dashboard'))
        assert response.status_code == 200

    def test_dashboard_context(self, authenticated_client, vehicle, dispatch):
        """Test dashboard context data."""
        response = authenticated_client.get(reverse('dispatch:dashboard'))
        assert 'vehicles_available' in response.context
        assert 'dispatches_planned' in response.context
        assert 'recent_dispatches' in response.context


# =============================================================================
# VEHICLE VIEW TESTS
# =============================================================================

class TestVehicleListView:
    """Tests for VehicleListView."""

    def test_vehicle_list_requires_login(self, client):
        """Test vehicle list requires authentication."""
        response = client.get(reverse('dispatch:vehicle-list'))
        assert response.status_code == 302

    def test_vehicle_list_authenticated(self, authenticated_client):
        """Test vehicle list for authenticated user."""
        response = authenticated_client.get(reverse('dispatch:vehicle-list'))
        assert response.status_code == 200
        assert 'vehicles' in response.context

    def test_vehicle_list_filter_status(self, authenticated_client, vehicle):
        """Test filtering vehicles by status."""
        response = authenticated_client.get(
            reverse('dispatch:vehicle-list'),
            {'status': 'AVAILABLE'}
        )
        assert response.status_code == 200

    def test_vehicle_list_search(self, authenticated_client, vehicle):
        """Test vehicle search."""
        response = authenticated_client.get(
            reverse('dispatch:vehicle-list'),
            {'q': 'Toyota'}
        )
        content = str(response.content)
        assert vehicle.code in content


class TestVehicleDetailView:
    """Tests for VehicleDetailView."""

    def test_vehicle_detail_requires_login(self, client, vehicle):
        """Test vehicle detail requires authentication."""
        response = client.get(
            reverse('dispatch:vehicle-detail', kwargs={'pk': vehicle.pk})
        )
        assert response.status_code == 302

    def test_vehicle_detail_authenticated(self, authenticated_client, vehicle):
        """Test vehicle detail for authenticated user."""
        response = authenticated_client.get(
            reverse('dispatch:vehicle-detail', kwargs={'pk': vehicle.pk})
        )
        assert response.status_code == 200
        assert vehicle.code in str(response.content)

    def test_vehicle_detail_404(self, authenticated_client):
        """Test 404 for non-existent vehicle."""
        response = authenticated_client.get(
            reverse('dispatch:vehicle-detail', kwargs={'pk': 99999})
        )
        assert response.status_code == 404


class TestVehicleCreateView:
    """Tests for VehicleCreateView."""

    def test_vehicle_create_get(self, authenticated_client):
        """Test vehicle create GET request."""
        response = authenticated_client.get(reverse('dispatch:vehicle-create'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_vehicle_create_post_valid(self, authenticated_client):
        """Test creating a vehicle via POST."""
        data = {
            'code': 'NEW-001',
            'plate_number': 'NEW-1234',
            'make': 'Ford',
            'model': 'Ranger',
            'year': 2024,
            'capacity': '2 ton',
            'status': 'AVAILABLE',
            'is_active': True
        }
        response = authenticated_client.post(
            reverse('dispatch:vehicle-create'),
            data
        )
        assert response.status_code == 302

        vehicle = Vehicle.objects.get(code='NEW-001')
        assert vehicle.make == 'Ford'


class TestVehicleUpdateView:
    """Tests for VehicleUpdateView."""

    def test_vehicle_update_get(self, authenticated_client, vehicle):
        """Test vehicle update GET request."""
        response = authenticated_client.get(
            reverse('dispatch:vehicle-update', kwargs={'pk': vehicle.pk})
        )
        assert response.status_code == 200
        assert response.context['form'].instance == vehicle

    def test_vehicle_update_post(self, authenticated_client, vehicle):
        """Test updating a vehicle via POST."""
        data = {
            'code': vehicle.code,
            'plate_number': vehicle.plate_number,
            'make': 'Updated Make',
            'model': 'Updated Model',
            'year': 2024,
            'status': 'MAINTENANCE',
            'is_active': True
        }
        response = authenticated_client.post(
            reverse('dispatch:vehicle-update', kwargs={'pk': vehicle.pk}),
            data
        )
        assert response.status_code == 302

        vehicle.refresh_from_db()
        assert vehicle.make == 'Updated Make'
        assert vehicle.status == 'MAINTENANCE'


class TestVehicleDeleteView:
    """Tests for VehicleDeleteView."""

    def test_vehicle_delete_get(self, authenticated_client, vehicle):
        """Test vehicle delete confirmation page."""
        response = authenticated_client.get(
            reverse('dispatch:vehicle-delete', kwargs={'pk': vehicle.pk})
        )
        assert response.status_code == 200

    def test_vehicle_delete_post(self, authenticated_client, vehicle):
        """Test deleting a vehicle via POST."""
        vehicle_id = vehicle.pk
        response = authenticated_client.post(
            reverse('dispatch:vehicle-delete', kwargs={'pk': vehicle.pk})
        )
        assert response.status_code == 302
        assert not Vehicle.objects.filter(pk=vehicle_id).exists()


# =============================================================================
# DISPATCH VIEW TESTS
# =============================================================================

class TestDispatchListView:
    """Tests for DispatchListView."""

    def test_dispatch_list_requires_login(self, client):
        """Test dispatch list requires authentication."""
        response = client.get(reverse('dispatch:dispatch-list'))
        assert response.status_code == 302

    def test_dispatch_list_authenticated(self, authenticated_client, dispatch):
        """Test dispatch list for authenticated user."""
        response = authenticated_client.get(reverse('dispatch:dispatch-list'))
        assert response.status_code == 200
        assert 'dispatches' in response.context

    def test_dispatch_list_filter_status(self, authenticated_client, dispatch):
        """Test filtering dispatches by status."""
        response = authenticated_client.get(
            reverse('dispatch:dispatch-list'),
            {'status': 'PLANNED'}
        )
        assert response.status_code == 200

    def test_dispatch_list_filter_date(self, authenticated_client, dispatch):
        """Test filtering dispatches by date."""
        response = authenticated_client.get(
            reverse('dispatch:dispatch-list'),
            {
                'date_from': str(date.today()),
                'date_to': str(date.today() + timedelta(days=7))
            }
        )
        assert response.status_code == 200


class TestDispatchDetailView:
    """Tests for DispatchDetailView."""

    def test_dispatch_detail_requires_login(self, client, dispatch):
        """Test dispatch detail requires authentication."""
        response = client.get(
            reverse('dispatch:dispatch-detail', kwargs={'pk': dispatch.pk})
        )
        assert response.status_code == 302

    def test_dispatch_detail_authenticated(self, authenticated_client, dispatch):
        """Test dispatch detail for authenticated user."""
        response = authenticated_client.get(
            reverse('dispatch:dispatch-detail', kwargs={'pk': dispatch.pk})
        )
        assert response.status_code == 200
        assert dispatch.dispatch_number in str(response.content)


class TestDispatchCreateView:
    """Tests for DispatchCreateView."""

    def test_dispatch_create_get(self, authenticated_client):
        """Test dispatch create GET request."""
        response = authenticated_client.get(reverse('dispatch:dispatch-create'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_dispatch_create_post_valid(self, authenticated_client, customer, vehicle):
        """Test creating a dispatch via POST."""
        data = {
            'dispatch_number': 'NEW-DISP-001',
            'vehicle': vehicle.pk,
            'driver_name': 'Test Driver',
            'customer': customer.pk,
            'planned_date': str(date.today()),
            'status': 'PLANNED',
            'notes': 'Test notes'
        }
        response = authenticated_client.post(
            reverse('dispatch:dispatch-create'),
            data
        )
        assert response.status_code == 302

        dispatch = Dispatch.objects.get(dispatch_number='NEW-DISP-001')
        assert dispatch.driver_name == 'Test Driver'


class TestDispatchUpdateView:
    """Tests for DispatchUpdateView."""

    def test_dispatch_update_get(self, authenticated_client, dispatch):
        """Test dispatch update GET request."""
        response = authenticated_client.get(
            reverse('dispatch:dispatch-update', kwargs={'pk': dispatch.pk})
        )
        assert response.status_code == 200

    def test_dispatch_update_post(self, authenticated_client, dispatch, customer, vehicle):
        """Test updating a dispatch via POST."""
        data = {
            'dispatch_number': dispatch.dispatch_number,
            'vehicle': vehicle.pk,
            'driver_name': 'Updated Driver',
            'customer': customer.pk,
            'planned_date': str(date.today()),
            'status': 'LOADING',
            'notes': 'Updated notes'
        }
        response = authenticated_client.post(
            reverse('dispatch:dispatch-update', kwargs={'pk': dispatch.pk}),
            data
        )
        assert response.status_code == 302

        dispatch.refresh_from_db()
        assert dispatch.driver_name == 'Updated Driver'


class TestDispatchDeleteView:
    """Tests for DispatchDeleteView."""

    def test_dispatch_delete_get(self, authenticated_client, dispatch):
        """Test dispatch delete confirmation page."""
        response = authenticated_client.get(
            reverse('dispatch:dispatch-delete', kwargs={'pk': dispatch.pk})
        )
        assert response.status_code == 200

    def test_dispatch_delete_post(self, authenticated_client, dispatch):
        """Test deleting a dispatch via POST."""
        dispatch_id = dispatch.pk
        response = authenticated_client.post(
            reverse('dispatch:dispatch-delete', kwargs={'pk': dispatch.pk})
        )
        assert response.status_code == 302
        assert not Dispatch.objects.filter(pk=dispatch_id).exists()


# =============================================================================
# STATUS UPDATE VIEW TESTS
# =============================================================================

class TestDispatchStatusUpdateView:
    """Tests for DispatchStatusUpdateView."""

    def test_status_update_requires_login(self, client, dispatch):
        """Test status update requires authentication."""
        response = client.post(
            reverse('dispatch:dispatch-status-update', kwargs={'pk': dispatch.pk}),
            {'status': 'LOADING'}
        )
        assert response.status_code == 302
        assert 'login' in response.url

    def test_status_update_valid(self, authenticated_client, dispatch):
        """Test valid status update."""
        response = authenticated_client.post(
            reverse('dispatch:dispatch-status-update', kwargs={'pk': dispatch.pk}),
            {'status': 'LOADING'}
        )
        assert response.status_code == 302

        dispatch.refresh_from_db()
        assert dispatch.status == 'LOADING'

    def test_status_update_in_transit_sets_departure(self, authenticated_client, dispatch):
        """Test IN_TRANSIT status sets actual_departure."""
        response = authenticated_client.post(
            reverse('dispatch:dispatch-status-update', kwargs={'pk': dispatch.pk}),
            {'status': 'IN_TRANSIT'}
        )
        assert response.status_code == 302

        dispatch.refresh_from_db()
        assert dispatch.status == 'IN_TRANSIT'
        assert dispatch.actual_departure is not None

    def test_status_update_delivered_sets_arrival(self, authenticated_client, dispatch):
        """Test DELIVERED status sets actual_arrival."""
        # First set to IN_TRANSIT
        dispatch.status = 'IN_TRANSIT'
        dispatch.actual_departure = timezone.now()
        dispatch.save()

        response = authenticated_client.post(
            reverse('dispatch:dispatch-status-update', kwargs={'pk': dispatch.pk}),
            {'status': 'DELIVERED'}
        )
        assert response.status_code == 302

        dispatch.refresh_from_db()
        assert dispatch.status == 'DELIVERED'
        assert dispatch.actual_arrival is not None

    def test_status_update_invalid_status(self, authenticated_client, dispatch):
        """Test invalid status is rejected."""
        response = authenticated_client.post(
            reverse('dispatch:dispatch-status-update', kwargs={'pk': dispatch.pk}),
            {'status': 'INVALID_STATUS'}
        )
        assert response.status_code == 302

        dispatch.refresh_from_db()
        # Status should remain unchanged
        assert dispatch.status == 'PLANNED'


# =============================================================================
# RESERVATION VIEW TESTS
# =============================================================================

class TestReservationViews:
    """Tests for InventoryReservation views."""

    @pytest.fixture
    def inventory_item(self, db):
        """Create a test inventory item."""
        from apps.inventory.models import InventoryItem, InventoryLocation
        location = InventoryLocation.objects.create(
            code='LOC-001',
            name='Test Location'
        )
        return InventoryItem.objects.create(
            sku='SKU-001',
            name='Test Item',
            location=location,
            quantity=100
        )

    @pytest.fixture
    def work_order(self, db, user):
        """Create a test work order."""
        from apps.workorders.models import WorkOrder
        return WorkOrder.objects.create(
            wo_number='WO-001',
            wo_type='MANUFACTURING',
            created_by=user
        )

    @pytest.fixture
    def reservation(self, db, inventory_item, work_order, user):
        """Create a test reservation."""
        from decimal import Decimal
        return InventoryReservation.objects.create(
            inventory_item=inventory_item,
            work_order=work_order,
            quantity=Decimal('10'),
            reserved_by=user
        )

    def test_reservation_list(self, authenticated_client, reservation):
        """Test reservation list view."""
        response = authenticated_client.get(reverse('dispatch:reservation-list'))
        assert response.status_code == 200
        assert 'reservations' in response.context

    def test_reservation_list_filter_status(self, authenticated_client, reservation):
        """Test filtering reservations by status."""
        response = authenticated_client.get(
            reverse('dispatch:reservation-list'),
            {'status': 'RESERVED'}
        )
        assert response.status_code == 200
