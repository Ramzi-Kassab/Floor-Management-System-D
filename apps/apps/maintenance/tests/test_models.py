"""
Tests for Maintenance app models.
"""
import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.maintenance.models import (
    EquipmentCategory, Equipment, MaintenanceRequest,
    MaintenanceWorkOrder
)

User = get_user_model()


class TestEquipmentCategoryModel:
    """Tests for EquipmentCategory model."""

    def test_create_category(self, db):
        """Test creating an equipment category."""
        category = EquipmentCategory.objects.create(
            code='COMPRESSORS',
            name='Compressors',
            description='Air compressors',
            is_active=True
        )
        assert category.pk is not None
        assert category.code == 'COMPRESSORS'

    def test_category_str(self, equipment_category):
        """Test category string representation."""
        assert 'PUMPS' in str(equipment_category)
        assert 'Pumps & Motors' in str(equipment_category)

    def test_category_hierarchy(self, db, equipment_category):
        """Test category parent-child relationship."""
        child = EquipmentCategory.objects.create(
            code='CENTRIFUGAL',
            name='Centrifugal Pumps',
            parent=equipment_category
        )
        assert child.parent == equipment_category
        assert child in equipment_category.children.all()

    def test_category_unique_code(self, db, equipment_category):
        """Test category code uniqueness."""
        with pytest.raises(Exception):
            EquipmentCategory.objects.create(
                code='PUMPS',
                name='Duplicate'
            )


class TestEquipmentModel:
    """Tests for Equipment model."""

    def test_create_equipment(self, db, equipment_category):
        """Test creating equipment."""
        equip = Equipment.objects.create(
            code='MOTOR-001',
            name='Electric Motor',
            category=equipment_category,
            status=Equipment.Status.OPERATIONAL
        )
        assert equip.pk is not None
        assert equip.code == 'MOTOR-001'

    def test_equipment_str(self, equipment):
        """Test equipment string representation."""
        assert 'PUMP-001' in str(equipment)
        assert 'Main Circulation Pump' in str(equipment)

    def test_equipment_status_choices(self, db):
        """Test equipment status choices."""
        for status, _ in Equipment.Status.choices:
            equip = Equipment.objects.create(
                code=f'EQUIP-{status}',
                name=f'Equipment {status}',
                status=status
            )
            assert equip.status == status

    def test_equipment_maintenance_schedule(self, equipment):
        """Test equipment maintenance schedule."""
        assert equipment.last_maintenance is not None
        assert equipment.next_maintenance is not None
        assert equipment.maintenance_interval_days == 90

    def test_equipment_unique_code(self, db, equipment):
        """Test equipment code uniqueness."""
        with pytest.raises(Exception):
            Equipment.objects.create(
                code='PUMP-001',
                name='Duplicate'
            )


class TestMaintenanceRequestModel:
    """Tests for MaintenanceRequest model."""

    def test_create_request(self, db, test_user, equipment):
        """Test creating a maintenance request."""
        request = MaintenanceRequest.objects.create(
            request_number='MR-TEST',
            equipment=equipment,
            request_type=MaintenanceRequest.RequestType.BREAKDOWN,
            priority=MaintenanceRequest.Priority.URGENT,
            title='Emergency repair',
            description='Equipment stopped working',
            requested_by=test_user
        )
        assert request.pk is not None
        assert request.request_number == 'MR-TEST'

    def test_request_status_choices(self, db, test_user, equipment):
        """Test request status choices."""
        for i, (status, _) in enumerate(MaintenanceRequest.Status.choices):
            request = MaintenanceRequest.objects.create(
                request_number=f'MR-{i}',
                equipment=equipment,
                request_type=MaintenanceRequest.RequestType.CORRECTIVE,
                priority=MaintenanceRequest.Priority.NORMAL,
                title=f'Request {status}',
                description='Test',
                status=status,
                requested_by=test_user
            )
            assert request.status == status

    def test_request_type_choices(self, db, test_user, equipment):
        """Test request type choices."""
        for i, (req_type, _) in enumerate(MaintenanceRequest.RequestType.choices):
            request = MaintenanceRequest.objects.create(
                request_number=f'MR-TYPE-{i}',
                equipment=equipment,
                request_type=req_type,
                priority=MaintenanceRequest.Priority.NORMAL,
                title=f'Request {req_type}',
                description='Test',
                requested_by=test_user
            )
            assert request.request_type == req_type

    def test_request_approval(self, maintenance_request, approver_user):
        """Test request approval."""
        maintenance_request.status = MaintenanceRequest.Status.APPROVED
        maintenance_request.approved_by = approver_user
        maintenance_request.approved_at = timezone.now()
        maintenance_request.save()
        maintenance_request.refresh_from_db()
        assert maintenance_request.status == MaintenanceRequest.Status.APPROVED
        assert maintenance_request.approved_by == approver_user

    def test_request_unique_number(self, db, maintenance_request, test_user, equipment):
        """Test request number uniqueness."""
        with pytest.raises(Exception):
            MaintenanceRequest.objects.create(
                request_number='MR-001',
                equipment=equipment,
                request_type=MaintenanceRequest.RequestType.CORRECTIVE,
                priority=MaintenanceRequest.Priority.NORMAL,
                title='Duplicate',
                description='Test',
                requested_by=test_user
            )


class TestMaintenanceWorkOrderModel:
    """Tests for MaintenanceWorkOrder model."""

    def test_create_work_order(self, db, test_user, equipment):
        """Test creating a maintenance work order."""
        mwo = MaintenanceWorkOrder.objects.create(
            mwo_number='MWO-TEST',
            equipment=equipment,
            title='Repair work',
            description='Fix the issue',
            status=MaintenanceWorkOrder.Status.PLANNED,
            created_by=test_user
        )
        assert mwo.pk is not None
        assert mwo.mwo_number == 'MWO-TEST'

    def test_work_order_status_transitions(self, maintenance_work_order, test_user):
        """Test work order status transitions."""
        # Start work
        maintenance_work_order.status = MaintenanceWorkOrder.Status.IN_PROGRESS
        maintenance_work_order.actual_start = timezone.now()
        maintenance_work_order.save()
        assert maintenance_work_order.status == MaintenanceWorkOrder.Status.IN_PROGRESS

        # Complete work
        maintenance_work_order.status = MaintenanceWorkOrder.Status.COMPLETED
        maintenance_work_order.actual_end = timezone.now()
        maintenance_work_order.save()
        assert maintenance_work_order.status == MaintenanceWorkOrder.Status.COMPLETED

    def test_work_order_linked_to_request(self, maintenance_work_order, approved_request):
        """Test work order linked to request."""
        assert maintenance_work_order.request == approved_request

    def test_work_order_unique_number(self, db, maintenance_work_order, test_user, equipment):
        """Test work order number uniqueness."""
        with pytest.raises(Exception):
            MaintenanceWorkOrder.objects.create(
                mwo_number='MWO-001',
                equipment=equipment,
                title='Duplicate',
                description='Test',
                created_by=test_user
            )
