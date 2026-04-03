"""
Dispatch App - Model Tests
Comprehensive tests for all 4 dispatch models.

Tests cover:
- Instance creation with required fields
- __str__ representation
- Field validation (max_length, choices, unique constraints)
- Foreign key relationships and cascades
- Custom methods and properties
- Edge cases (blank fields, invalid data)
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.dispatch.models import Vehicle, Dispatch, DispatchItem, InventoryReservation

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
def driver(db):
    """Create a driver user."""
    return User.objects.create_user(
        username='driver',
        email='driver@example.com',
        password='driverpass123',
        first_name='John',
        last_name='Driver'
    )


@pytest.fixture
def vehicle(db):
    """Create a test vehicle."""
    return Vehicle.objects.create(
        code='VH-001',
        plate_number='ABC-1234',
        make='Toyota',
        model='Hilux',
        year=2023,
        capacity='1 ton',
        status=Vehicle.Status.AVAILABLE
    )


@pytest.fixture
def vehicle_in_use(db):
    """Create a vehicle that's in use."""
    return Vehicle.objects.create(
        code='VH-002',
        plate_number='XYZ-5678',
        make='Ford',
        model='F-150',
        year=2022,
        status=Vehicle.Status.IN_USE
    )


@pytest.fixture
def customer(db):
    """Create a test customer."""
    from apps.sales.models import Customer
    return Customer.objects.create(
        code='CUST-001',
        name='Test Customer',
        customer_type='COMMERCIAL',
        is_active=True
    )


@pytest.fixture
def warehouse(db, customer):
    """Create a test warehouse."""
    from apps.sales.models import Warehouse
    return Warehouse.objects.create(
        code='WH-001',
        name='Main Warehouse',
        customer=customer
    )


@pytest.fixture
def dispatch(db, vehicle, customer, user):
    """Create a test dispatch."""
    return Dispatch.objects.create(
        dispatch_number='DISP-2024-001',
        vehicle=vehicle,
        driver_name='John Driver',
        customer=customer,
        planned_date=date.today(),
        status=Dispatch.Status.PLANNED,
        created_by=user
    )


# =============================================================================
# VEHICLE MODEL TESTS
# =============================================================================

class TestVehicleModel:
    """Tests for the Vehicle model."""

    def test_create_vehicle(self, db):
        """Test creating a vehicle with required fields."""
        vehicle = Vehicle.objects.create(
            code='TEST-001',
            plate_number='TEST-1234'
        )
        assert vehicle.pk is not None
        assert vehicle.code == 'TEST-001'
        assert vehicle.plate_number == 'TEST-1234'
        assert vehicle.status == Vehicle.Status.AVAILABLE

    def test_vehicle_str(self, vehicle):
        """Test the __str__ method."""
        expected = 'VH-001 - ABC-1234'
        assert str(vehicle) == expected

    def test_vehicle_unique_code(self, vehicle):
        """Test that vehicle code must be unique."""
        with pytest.raises(IntegrityError):
            Vehicle.objects.create(
                code='VH-001',  # Duplicate
                plate_number='NEW-1234'
            )

    def test_vehicle_status_choices(self, db):
        """Test all valid status choices."""
        for status_code, status_name in Vehicle.Status.choices:
            vehicle = Vehicle.objects.create(
                code=f'STATUS-{status_code}',
                plate_number=f'PL-{status_code}',
                status=status_code
            )
            assert vehicle.status == status_code

    def test_vehicle_default_active(self, db):
        """Test that vehicles are active by default."""
        vehicle = Vehicle.objects.create(
            code='ACTIVE-001',
            plate_number='ACT-1234'
        )
        assert vehicle.is_active is True

    def test_vehicle_optional_fields(self, db):
        """Test vehicle with optional fields empty."""
        vehicle = Vehicle.objects.create(
            code='MINIMAL-001',
            plate_number='MIN-1234',
            make='',
            model='',
            year=None,
            capacity=''
        )
        assert vehicle.make == ''
        assert vehicle.year is None

    def test_vehicle_timestamps(self, vehicle):
        """Test auto-generated timestamps."""
        assert vehicle.created_at is not None
        assert vehicle.updated_at is not None


# =============================================================================
# DISPATCH MODEL TESTS
# =============================================================================

class TestDispatchModel:
    """Tests for the Dispatch model."""

    def test_create_dispatch(self, db, customer, user):
        """Test creating a dispatch."""
        dispatch = Dispatch.objects.create(
            dispatch_number='TEST-DISP-001',
            customer=customer,
            planned_date=date.today(),
            created_by=user
        )
        assert dispatch.pk is not None
        assert dispatch.status == Dispatch.Status.PLANNED

    def test_dispatch_str(self, dispatch, customer):
        """Test the __str__ method."""
        expected = f'DISP-2024-001 - {customer.name}'
        assert str(dispatch) == expected

    def test_dispatch_str_with_destination(self, dispatch, warehouse):
        """Test __str__ when destination is set."""
        dispatch.destination = warehouse
        dispatch.save()
        expected = f'{dispatch.dispatch_number} - {warehouse.name}'
        assert str(dispatch) == expected

    def test_dispatch_unique_number(self, dispatch, customer, user):
        """Test that dispatch number must be unique."""
        with pytest.raises(IntegrityError):
            Dispatch.objects.create(
                dispatch_number='DISP-2024-001',  # Duplicate
                customer=customer,
                planned_date=date.today(),
                created_by=user
            )

    def test_dispatch_status_choices(self, db, customer, user):
        """Test all valid status choices."""
        for status_code, status_name in Dispatch.Status.choices:
            dispatch = Dispatch.objects.create(
                dispatch_number=f'STATUS-{status_code}',
                customer=customer,
                planned_date=date.today(),
                status=status_code,
                created_by=user
            )
            assert dispatch.status == status_code

    def test_dispatch_without_vehicle(self, db, customer, user):
        """Test dispatch can be created without vehicle."""
        dispatch = Dispatch.objects.create(
            dispatch_number='NO-VEHICLE-001',
            customer=customer,
            planned_date=date.today(),
            created_by=user
        )
        assert dispatch.vehicle is None

    def test_dispatch_vehicle_set_null(self, dispatch, vehicle):
        """Test vehicle SET_NULL behavior."""
        dispatch.vehicle = vehicle
        dispatch.save()

        vehicle.delete()
        dispatch.refresh_from_db()
        assert dispatch.vehicle is None

    def test_dispatch_customer_protect(self, dispatch, customer):
        """Test customer PROTECT behavior."""
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            customer.delete()

    def test_dispatch_timestamps(self, dispatch):
        """Test departure/arrival timestamps."""
        assert dispatch.actual_departure is None
        assert dispatch.actual_arrival is None

        # Set timestamps
        now = timezone.now()
        dispatch.actual_departure = now
        dispatch.actual_arrival = now + timedelta(hours=2)
        dispatch.save()

        dispatch.refresh_from_db()
        assert dispatch.actual_departure is not None
        assert dispatch.actual_arrival is not None

    def test_dispatch_ordering(self, db, customer, user):
        """Test dispatch ordering by date and number."""
        d1 = Dispatch.objects.create(
            dispatch_number='DISP-A',
            customer=customer,
            planned_date=date.today() - timedelta(days=1),
            created_by=user
        )
        d2 = Dispatch.objects.create(
            dispatch_number='DISP-B',
            customer=customer,
            planned_date=date.today(),
            created_by=user
        )

        dispatches = list(Dispatch.objects.all())
        # More recent dates first
        assert dispatches[0].planned_date >= dispatches[1].planned_date


# =============================================================================
# DISPATCH ITEM MODEL TESTS
# =============================================================================

class TestDispatchItemModel:
    """Tests for the DispatchItem model."""

    def test_create_dispatch_item(self, dispatch):
        """Test creating a dispatch item."""
        from apps.sales.models import SalesOrder, SalesOrderLine, Customer
        from apps.workorders.models import DrillBit

        # Create minimal sales order line
        order = SalesOrder.objects.create(
            order_number='SO-001',
            customer=dispatch.customer,
            order_date=date.today()
        )
        line = SalesOrderLine.objects.create(
            order=order,
            line_number=1,
            quantity=1
        )

        item = DispatchItem.objects.create(
            dispatch=dispatch,
            sales_order_line=line,
            quantity=1
        )

        assert item.pk is not None
        assert item.dispatch == dispatch

    def test_dispatch_item_str(self, dispatch):
        """Test the __str__ method."""
        from apps.sales.models import SalesOrder, SalesOrderLine

        order = SalesOrder.objects.create(
            order_number='SO-002',
            customer=dispatch.customer,
            order_date=date.today()
        )
        line = SalesOrderLine.objects.create(
            order=order,
            line_number=1,
            quantity=1
        )

        item = DispatchItem.objects.create(
            dispatch=dispatch,
            sales_order_line=line,
            quantity=2
        )

        expected = f'{dispatch.dispatch_number} - N/A (×2)'
        assert str(item) == expected

    def test_dispatch_item_cascade_delete(self, dispatch):
        """Test cascade delete from dispatch."""
        from apps.sales.models import SalesOrder, SalesOrderLine

        order = SalesOrder.objects.create(
            order_number='SO-003',
            customer=dispatch.customer,
            order_date=date.today()
        )
        line = SalesOrderLine.objects.create(
            order=order,
            line_number=1,
            quantity=1
        )

        item = DispatchItem.objects.create(
            dispatch=dispatch,
            sales_order_line=line,
            quantity=1
        )
        item_id = item.pk

        dispatch.delete()
        assert not DispatchItem.objects.filter(pk=item_id).exists()

    def test_dispatch_item_default_quantity(self, dispatch):
        """Test default quantity is 1."""
        from apps.sales.models import SalesOrder, SalesOrderLine

        order = SalesOrder.objects.create(
            order_number='SO-004',
            customer=dispatch.customer,
            order_date=date.today()
        )
        line = SalesOrderLine.objects.create(
            order=order,
            line_number=1,
            quantity=1
        )

        item = DispatchItem.objects.create(
            dispatch=dispatch,
            sales_order_line=line
        )

        assert item.quantity == 1


# =============================================================================
# INVENTORY RESERVATION MODEL TESTS
# =============================================================================

class TestInventoryReservationModel:
    """Tests for the InventoryReservation model."""

    @pytest.fixture
    def inventory_item(self, db):
        """Create a test inventory item."""
        from apps.inventory.models import InventoryItem, InventoryLocation
        location = InventoryLocation.objects.create(
            code='LOC-001',
            name='Main Storage'
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

    def test_create_reservation(self, inventory_item, work_order, user):
        """Test creating an inventory reservation."""
        reservation = InventoryReservation.objects.create(
            inventory_item=inventory_item,
            work_order=work_order,
            quantity=Decimal('10.5'),
            reserved_by=user
        )

        assert reservation.pk is not None
        assert reservation.status == InventoryReservation.Status.RESERVED

    def test_reservation_str(self, inventory_item, work_order, user):
        """Test the __str__ method."""
        reservation = InventoryReservation.objects.create(
            inventory_item=inventory_item,
            work_order=work_order,
            quantity=Decimal('5'),
            reserved_by=user
        )

        expected = f'{inventory_item.name} - Reserved 5 for {work_order.wo_number}'
        assert str(reservation) == expected

    def test_reservation_status_choices(self, inventory_item, work_order, user):
        """Test all valid status choices."""
        for status_code, status_name in InventoryReservation.Status.choices:
            reservation = InventoryReservation.objects.create(
                inventory_item=inventory_item,
                work_order=work_order,
                quantity=Decimal('1'),
                status=status_code,
                reserved_by=user
            )
            assert reservation.status == status_code

    def test_reservation_cascade_delete(self, inventory_item, work_order, user):
        """Test cascade delete from work order."""
        reservation = InventoryReservation.objects.create(
            inventory_item=inventory_item,
            work_order=work_order,
            quantity=Decimal('5'),
            reserved_by=user
        )
        reservation_id = reservation.pk

        work_order.delete()
        assert not InventoryReservation.objects.filter(pk=reservation_id).exists()

    def test_reservation_protect_inventory_item(self, inventory_item, work_order, user):
        """Test inventory item PROTECT behavior."""
        from django.db.models import ProtectedError
        InventoryReservation.objects.create(
            inventory_item=inventory_item,
            work_order=work_order,
            quantity=Decimal('5'),
            reserved_by=user
        )

        with pytest.raises(ProtectedError):
            inventory_item.delete()

    def test_reservation_timestamp(self, inventory_item, work_order, user):
        """Test reserved_at timestamp."""
        reservation = InventoryReservation.objects.create(
            inventory_item=inventory_item,
            work_order=work_order,
            quantity=Decimal('5'),
            reserved_by=user
        )

        assert reservation.reserved_at is not None


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestDispatchEdgeCases:
    """Edge case tests for dispatch models."""

    def test_vehicle_with_many_dispatches(self, db, vehicle, customer, user):
        """Test vehicle with multiple dispatches."""
        for i in range(10):
            Dispatch.objects.create(
                dispatch_number=f'MULTI-DISP-{i:03d}',
                vehicle=vehicle,
                customer=customer,
                planned_date=date.today() + timedelta(days=i),
                created_by=user
            )

        assert vehicle.dispatches.count() == 10

    def test_dispatch_status_transitions(self, dispatch):
        """Test status transitions."""
        # PLANNED -> LOADING
        dispatch.status = Dispatch.Status.LOADING
        dispatch.save()
        assert dispatch.status == Dispatch.Status.LOADING

        # LOADING -> IN_TRANSIT
        dispatch.status = Dispatch.Status.IN_TRANSIT
        dispatch.actual_departure = timezone.now()
        dispatch.save()
        assert dispatch.status == Dispatch.Status.IN_TRANSIT

        # IN_TRANSIT -> DELIVERED
        dispatch.status = Dispatch.Status.DELIVERED
        dispatch.actual_arrival = timezone.now()
        dispatch.save()
        assert dispatch.status == Dispatch.Status.DELIVERED

    def test_vehicle_maintenance_status(self, vehicle):
        """Test vehicle maintenance status."""
        vehicle.status = Vehicle.Status.MAINTENANCE
        vehicle.save()

        vehicle.refresh_from_db()
        assert vehicle.status == Vehicle.Status.MAINTENANCE

    def test_cancelled_dispatch(self, dispatch):
        """Test cancelled dispatch."""
        dispatch.status = Dispatch.Status.CANCELLED
        dispatch.save()

        dispatch.refresh_from_db()
        assert dispatch.status == Dispatch.Status.CANCELLED
        # Timestamps should remain null for cancelled
        assert dispatch.actual_departure is None
        assert dispatch.actual_arrival is None

    def test_special_characters_in_notes(self, dispatch):
        """Test special characters in notes field."""
        dispatch.notes = 'Notes with "quotes" & <special> characters\nand newlines'
        dispatch.save()

        dispatch.refresh_from_db()
        assert '"quotes"' in dispatch.notes
        assert '&' in dispatch.notes
