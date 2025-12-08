"""
Maintenance App Test Fixtures
"""
import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.maintenance.models import (
    EquipmentCategory, Equipment, MaintenanceRequest,
    MaintenanceWorkOrder, MaintenancePartsUsed
)

User = get_user_model()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )


@pytest.fixture
def approver_user(db):
    """Create an approver user."""
    return User.objects.create_user(
        username='approver',
        email='approver@example.com',
        password='testpass123'
    )


@pytest.fixture
def equipment_category(db):
    """Create a test equipment category."""
    return EquipmentCategory.objects.create(
        code='PUMPS',
        name='Pumps & Motors',
        description='Pumping equipment',
        is_active=True
    )


@pytest.fixture
def equipment(db, equipment_category):
    """Create a test equipment."""
    return Equipment.objects.create(
        code='PUMP-001',
        name='Main Circulation Pump',
        category=equipment_category,
        manufacturer='Grundfos',
        model='CRN-45',
        serial_number='SN-2024-001',
        year_of_manufacture=2020,
        location='Pump House A',
        status=Equipment.Status.OPERATIONAL,
        last_maintenance=date.today() - timedelta(days=30),
        next_maintenance=date.today() + timedelta(days=60),
        maintenance_interval_days=90
    )


@pytest.fixture
def maintenance_request(db, test_user, equipment):
    """Create a test maintenance request."""
    return MaintenanceRequest.objects.create(
        request_number='MR-001',
        equipment=equipment,
        request_type=MaintenanceRequest.RequestType.CORRECTIVE,
        priority=MaintenanceRequest.Priority.NORMAL,
        title='Pump vibration issue',
        description='Unusual vibration detected during operation',
        status=MaintenanceRequest.Status.PENDING,
        requested_by=test_user
    )


@pytest.fixture
def approved_request(db, test_user, approver_user, equipment):
    """Create an approved maintenance request."""
    request = MaintenanceRequest.objects.create(
        request_number='MR-002',
        equipment=equipment,
        request_type=MaintenanceRequest.RequestType.PREVENTIVE,
        priority=MaintenanceRequest.Priority.NORMAL,
        title='Scheduled maintenance',
        description='Regular PM',
        status=MaintenanceRequest.Status.APPROVED,
        requested_by=test_user,
        approved_by=approver_user,
        approved_at=timezone.now()
    )
    return request


@pytest.fixture
def maintenance_work_order(db, test_user, equipment, approved_request):
    """Create a test maintenance work order."""
    return MaintenanceWorkOrder.objects.create(
        work_order_number='MWO-001',
        equipment=equipment,
        request=approved_request,
        work_type=MaintenanceWorkOrder.WorkType.PREVENTIVE,
        priority=MaintenanceWorkOrder.Priority.NORMAL,
        title='Preventive maintenance',
        description='Perform scheduled PM',
        status=MaintenanceWorkOrder.Status.PLANNED,
        planned_start=timezone.now(),
        planned_end=timezone.now() + timedelta(hours=4),
        assigned_to=test_user,
        created_by=test_user
    )


# Fixtures for base class tests
@pytest.fixture
def test_object(equipment):
    """Default test object for base class tests."""
    return equipment


@pytest.fixture
def valid_data(equipment_category):
    """Valid data for equipment creation."""
    return {
        'code': 'EQUIP-NEW',
        'name': 'New Equipment',
        'category': equipment_category.pk if equipment_category else None,
        'status': Equipment.Status.OPERATIONAL,
    }
