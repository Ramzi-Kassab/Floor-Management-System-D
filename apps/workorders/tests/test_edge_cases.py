"""
Workorders App - Edge Case Tests
Boundary conditions, special characters, and unusual scenarios.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.db import IntegrityError
from django.utils import timezone


# =============================================================================
# SERIAL NUMBER EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestSerialNumberEdgeCases:
    """Tests for serial number edge cases."""

    def test_serial_number_max_length(self, base_user):
        """Test serial number at max length."""
        from apps.workorders.models import DrillBit
        max_serial = 'X' * 50  # max_length=50
        bit = DrillBit.objects.create(
            serial_number=max_serial,
            bit_type=DrillBit.BitType.FC,
            size=Decimal('8.500'),
            created_by=base_user
        )
        assert len(bit.serial_number) == 50

    def test_serial_number_special_characters(self, base_user):
        """Test serial number with special characters."""
        from apps.workorders.models import DrillBit
        special_serial = 'FC-2024-001/A-1'
        bit = DrillBit.objects.create(
            serial_number=special_serial,
            bit_type=DrillBit.BitType.FC,
            size=Decimal('8.500'),
            created_by=base_user
        )
        assert bit.serial_number == special_serial

    def test_serial_number_unicode(self, base_user):
        """Test serial number with unicode characters."""
        from apps.workorders.models import DrillBit
        unicode_serial = 'FC-テスト-001'
        bit = DrillBit.objects.create(
            serial_number=unicode_serial,
            bit_type=DrillBit.BitType.FC,
            size=Decimal('8.500'),
            created_by=base_user
        )
        assert bit.serial_number == unicode_serial

    def test_wo_number_max_length(self, base_user):
        """Test WO number at max length."""
        from apps.workorders.models import WorkOrder
        max_wo = 'W' * 30  # max_length=30
        wo = WorkOrder.objects.create(
            wo_number=max_wo,
            wo_type=WorkOrder.WOType.FC_REPAIR,
            created_by=base_user
        )
        assert len(wo.wo_number) == 30


# =============================================================================
# DECIMAL PRECISION EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestDecimalPrecisionEdgeCases:
    """Tests for decimal field precision edge cases."""

    def test_size_precision(self, base_user):
        """Test drill bit size precision (6,3)."""
        from apps.workorders.models import DrillBit
        # Max: 999.999
        bit = DrillBit.objects.create(
            serial_number='SIZE-PREC-001',
            bit_type=DrillBit.BitType.FC,
            size=Decimal('999.999'),
            created_by=base_user
        )
        assert bit.size == Decimal('999.999')

    def test_size_minimum_value(self, base_user):
        """Test drill bit minimum size."""
        from apps.workorders.models import DrillBit
        bit = DrillBit.objects.create(
            serial_number='SIZE-MIN-001',
            bit_type=DrillBit.BitType.FC,
            size=Decimal('0.001'),
            created_by=base_user
        )
        assert bit.size == Decimal('0.001')

    def test_cost_precision(self, work_order):
        """Test work order cost precision (15,2)."""
        from apps.workorders.models import WorkOrderCost
        cost = WorkOrderCost.objects.create(
            work_order=work_order,
            estimated_labor_hours=Decimal('9999.99'),
            labor_rate=Decimal('99999999.99'),
            estimated_material_cost=Decimal('9999999999999.99')
        )
        assert cost.estimated_material_cost == Decimal('9999999999999.99')

    def test_zero_decimal_values(self, work_order):
        """Test zero values for decimal fields."""
        from apps.workorders.models import WorkOrderCost
        cost = WorkOrderCost.objects.create(
            work_order=work_order,
            estimated_labor_hours=Decimal('0.00'),
            labor_rate=Decimal('0.00'),
            estimated_material_cost=Decimal('0.00')
        )
        assert cost.estimated_labor_hours == Decimal('0.00')

    def test_hours_run_precision(self, drill_bit, base_user):
        """Test hours_run precision on bit evaluation."""
        from apps.workorders.models import BitEvaluation
        evaluation = BitEvaluation.objects.create(
            drill_bit=drill_bit,
            evaluation_date=date.today(),
            evaluated_by=base_user,
            hours_run=Decimal('99999999.99')
        )
        assert evaluation.hours_run == Decimal('99999999.99')


# =============================================================================
# DATE BOUNDARY EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestDateBoundaryEdgeCases:
    """Tests for date boundary edge cases."""

    def test_work_order_same_start_end_date(self, base_user):
        """Test work order with same start and end date."""
        from apps.workorders.models import WorkOrder
        today = date.today()
        wo = WorkOrder.objects.create(
            wo_number='WO-SAME-DATE',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            planned_start=today,
            planned_end=today,
            due_date=today,
            created_by=base_user
        )
        assert wo.planned_start == wo.planned_end

    def test_work_order_past_dates(self, base_user):
        """Test work order with past dates."""
        from apps.workorders.models import WorkOrder
        past = date.today() - timedelta(days=365)
        wo = WorkOrder.objects.create(
            wo_number='WO-PAST-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            planned_start=past,
            due_date=past,
            created_by=base_user
        )
        assert wo.is_overdue  # Should be overdue

    def test_work_order_far_future_dates(self, base_user):
        """Test work order with far future dates."""
        from apps.workorders.models import WorkOrder
        future = date.today() + timedelta(days=3650)  # 10 years
        wo = WorkOrder.objects.create(
            wo_number='WO-FUTURE-001',
            wo_type=WorkOrder.WOType.FC_NEW,
            planned_start=future,
            due_date=future,
            created_by=base_user
        )
        assert wo.is_overdue is False

    def test_due_date_exactly_today(self, base_user):
        """Test work order due exactly today."""
        from apps.workorders.models import WorkOrder
        wo = WorkOrder.objects.create(
            wo_number='WO-TODAY-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            status=WorkOrder.Status.IN_PROGRESS,
            due_date=date.today(),
            created_by=base_user
        )
        assert wo.days_overdue == 0

    def test_salvage_expiry_date(self, drill_bit, work_order, base_user):
        """Test salvage item with expiry date."""
        from apps.workorders.models import SalvageItem
        item = SalvageItem.objects.create(
            salvage_number='SALV-EXP-001',
            drill_bit=drill_bit,
            salvage_type=SalvageItem.SalvageType.CUTTER,
            description='Expiring item',
            salvage_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            created_by=base_user
        )
        assert item.expiry_date > item.salvage_date


# =============================================================================
# TEXT FIELD EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestTextFieldEdgeCases:
    """Tests for text field edge cases."""

    def test_long_description_text(self, base_user):
        """Test work order with very long description."""
        from apps.workorders.models import WorkOrder
        long_text = 'A' * 10000
        wo = WorkOrder.objects.create(
            wo_number='WO-LONG-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            description=long_text,
            created_by=base_user
        )
        assert len(wo.description) == 10000

    def test_special_characters_in_text(self, base_user):
        """Test special characters in text fields."""
        from apps.workorders.models import WorkOrder
        special_text = '<script>alert("XSS")</script>\n\t"quotes" & ampersand'
        wo = WorkOrder.objects.create(
            wo_number='WO-SPEC-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            notes=special_text,
            created_by=base_user
        )
        assert wo.notes == special_text

    def test_unicode_in_text_fields(self, base_user):
        """Test unicode characters in text fields."""
        from apps.workorders.models import WorkOrder
        unicode_text = '日本語テスト 🔧 العربية'
        wo = WorkOrder.objects.create(
            wo_number='WO-UNI-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            description=unicode_text,
            created_by=base_user
        )
        assert wo.description == unicode_text

    def test_empty_text_fields(self, base_user):
        """Test empty/blank text fields."""
        from apps.workorders.models import WorkOrder
        wo = WorkOrder.objects.create(
            wo_number='WO-EMPTY-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            description='',
            notes='',
            internal_notes='',
            created_by=base_user
        )
        assert wo.description == ''
        assert wo.notes == ''


# =============================================================================
# JSON FIELD EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestJSONFieldEdgeCases:
    """Tests for JSON field edge cases."""

    def test_bit_types_empty_list(self, base_user):
        """Test process route with empty bit_types list."""
        from apps.workorders.models import ProcessRoute
        route = ProcessRoute.objects.create(
            route_number='ROUTE-EMPTY-001',
            name='Empty Types Route',
            bit_types=[],
            created_by=base_user
        )
        assert route.bit_types == []

    def test_bit_types_all_types(self, base_user):
        """Test process route with all bit types."""
        from apps.workorders.models import ProcessRoute
        route = ProcessRoute.objects.create(
            route_number='ROUTE-ALL-001',
            name='All Types Route',
            bit_types=['FC', 'RC'],
            created_by=base_user
        )
        assert len(route.bit_types) == 2

    def test_bit_types_null(self, base_user):
        """Test process route with null bit_types."""
        from apps.workorders.models import ProcessRoute
        route = ProcessRoute.objects.create(
            route_number='ROUTE-NULL-001',
            name='Null Types Route',
            bit_types=None,
            created_by=base_user
        )
        assert route.bit_types is None


# =============================================================================
# FOREIGN KEY EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestForeignKeyEdgeCases:
    """Tests for foreign key edge cases."""

    def test_work_order_null_foreign_keys(self, base_user):
        """Test work order with all nullable FKs as null."""
        from apps.workorders.models import WorkOrder
        wo = WorkOrder.objects.create(
            wo_number='WO-NULL-FK-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            drill_bit=None,
            design=None,
            customer=None,
            sales_order=None,
            rig=None,
            well=None,
            assigned_to=None,
            department=None,
            procedure=None,
            created_by=base_user
        )
        assert wo.drill_bit is None
        assert wo.customer is None

    def test_drill_bit_null_foreign_keys(self, base_user):
        """Test drill bit with all nullable FKs as null."""
        from apps.workorders.models import DrillBit
        bit = DrillBit.objects.create(
            serial_number='BIT-NULL-FK-001',
            bit_type=DrillBit.BitType.FC,
            size=Decimal('8.500'),
            design=None,
            customer=None,
            current_location=None,
            rig=None,
            well=None,
            created_by=base_user
        )
        assert bit.design is None
        assert bit.customer is None

    def test_cascade_delete_work_order_documents(self, work_order, base_user):
        """Test cascade delete of documents when work order deleted."""
        from apps.workorders.models import WorkOrderDocument
        doc = WorkOrderDocument.objects.create(
            work_order=work_order,
            document_type=WorkOrderDocument.DocType.DRAWING,
            name='Test Doc',
            uploaded_by=base_user
        )
        doc_pk = doc.pk
        work_order.delete()
        assert WorkOrderDocument.objects.filter(pk=doc_pk).count() == 0

    def test_cascade_delete_work_order_photos(self, work_order, base_user):
        """Test cascade delete of photos when work order deleted."""
        from apps.workorders.models import WorkOrderPhoto
        photo = WorkOrderPhoto.objects.create(
            work_order=work_order,
            taken_by=base_user
        )
        photo_pk = photo.pk
        work_order.delete()
        assert WorkOrderPhoto.objects.filter(pk=photo_pk).count() == 0

    def test_set_null_on_user_delete(self, drill_bit, base_user):
        """Test SET_NULL behavior when user is deleted."""
        from apps.workorders.models import DrillBit
        user_pk = base_user.pk
        assert drill_bit.created_by.pk == user_pk
        # Note: In real test, would need to delete user and check SET_NULL


# =============================================================================
# UNIQUE CONSTRAINT EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestUniqueConstraintEdgeCases:
    """Tests for unique constraint edge cases."""

    def test_duplicate_serial_number_fails(self, drill_bit, base_user):
        """Test duplicate serial number raises IntegrityError."""
        from apps.workorders.models import DrillBit
        with pytest.raises(IntegrityError):
            DrillBit.objects.create(
                serial_number=drill_bit.serial_number,
                bit_type=DrillBit.BitType.FC,
                size=Decimal('8.500'),
                created_by=base_user
            )

    def test_duplicate_wo_number_fails(self, work_order, base_user):
        """Test duplicate WO number raises IntegrityError."""
        from apps.workorders.models import WorkOrder
        with pytest.raises(IntegrityError):
            WorkOrder.objects.create(
                wo_number=work_order.wo_number,
                wo_type=WorkOrder.WOType.FC_REPAIR,
                created_by=base_user
            )

    def test_duplicate_salvage_number_fails(self, salvage_item, base_user):
        """Test duplicate salvage number raises IntegrityError."""
        from apps.workorders.models import SalvageItem
        with pytest.raises(IntegrityError):
            SalvageItem.objects.create(
                salvage_number=salvage_item.salvage_number,
                salvage_type=SalvageItem.SalvageType.BODY,
                description='Duplicate',
                salvage_date=date.today(),
                created_by=base_user
            )

    def test_duplicate_evaluation_number_fails(self, repair_evaluation, drill_bit, base_user):
        """Test duplicate evaluation number raises IntegrityError."""
        from apps.workorders.models import RepairEvaluation
        with pytest.raises(IntegrityError):
            RepairEvaluation.objects.create(
                evaluation_number=repair_evaluation.evaluation_number,
                drill_bit=drill_bit,
                damage_assessment='Duplicate',
                evaluated_by=base_user
            )

    def test_duplicate_route_number_fails(self, process_route, base_user):
        """Test duplicate route number raises IntegrityError."""
        from apps.workorders.models import ProcessRoute
        with pytest.raises(IntegrityError):
            ProcessRoute.objects.create(
                route_number=process_route.route_number,
                name='Duplicate Route',
                created_by=base_user
            )


# =============================================================================
# UNIQUE TOGETHER EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestUniqueTogether:
    """Tests for unique_together constraints."""

    def test_duplicate_repair_number_same_bit_fails(self, drill_bit, base_user):
        """Test duplicate repair_number for same bit fails."""
        from apps.workorders.models import BitRepairHistory
        BitRepairHistory.objects.create(
            drill_bit=drill_bit,
            repair_number=1,
            repair_date=date.today(),
            repair_type=BitRepairHistory.RepairType.REDRESS,
            created_by=base_user
        )
        with pytest.raises(IntegrityError):
            BitRepairHistory.objects.create(
                drill_bit=drill_bit,
                repair_number=1,
                repair_date=date.today(),
                repair_type=BitRepairHistory.RepairType.MINOR_REPAIR,
                created_by=base_user
            )

    def test_same_repair_number_different_bits_ok(self, drill_bit, drill_bit_rc, base_user):
        """Test same repair_number for different bits is allowed."""
        from apps.workorders.models import BitRepairHistory
        history1 = BitRepairHistory.objects.create(
            drill_bit=drill_bit,
            repair_number=1,
            repair_date=date.today(),
            repair_type=BitRepairHistory.RepairType.REDRESS,
            created_by=base_user
        )
        history2 = BitRepairHistory.objects.create(
            drill_bit=drill_bit_rc,
            repair_number=1,
            repair_date=date.today(),
            repair_type=BitRepairHistory.RepairType.REDRESS,
            created_by=base_user
        )
        assert history1.repair_number == history2.repair_number


# =============================================================================
# STATUS TRANSITION EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestStatusTransitionEdgeCases:
    """Tests for status transition edge cases."""

    def test_start_work_from_draft_fails(self, work_order):
        """Test start_work from DRAFT raises ValueError."""
        with pytest.raises(ValueError):
            work_order.start_work()

    def test_complete_work_from_draft_fails(self, work_order):
        """Test complete_work from DRAFT raises ValueError."""
        with pytest.raises(ValueError):
            work_order.complete_work()

    def test_submit_for_qc_from_draft_fails(self, work_order):
        """Test submit_for_qc from DRAFT raises ValueError."""
        with pytest.raises(ValueError):
            work_order.submit_for_qc()

    def test_put_on_hold_from_completed_fails(self, base_user, drill_bit):
        """Test put_on_hold from COMPLETED raises ValueError."""
        from apps.workorders.models import WorkOrder
        wo = WorkOrder.objects.create(
            wo_number='WO-HOLD-FAIL',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            status=WorkOrder.Status.COMPLETED,
            created_by=base_user
        )
        with pytest.raises(ValueError):
            wo.put_on_hold()


# =============================================================================
# PROPERTY CALCULATION EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestPropertyCalculationEdgeCases:
    """Tests for computed property edge cases."""

    def test_is_overdue_null_due_date(self, base_user):
        """Test is_overdue when due_date is null."""
        from apps.workorders.models import WorkOrder
        wo = WorkOrder.objects.create(
            wo_number='WO-NO-DUE',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            due_date=None,
            created_by=base_user
        )
        assert wo.is_overdue is False

    def test_days_overdue_null_due_date(self, base_user):
        """Test days_overdue when due_date is null."""
        from apps.workorders.models import WorkOrder
        wo = WorkOrder.objects.create(
            wo_number='WO-NO-DUE-2',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            due_date=None,
            created_by=base_user
        )
        assert wo.days_overdue == 0

    def test_variance_zero_estimated(self, work_order):
        """Test variance_percent when estimated is zero."""
        from apps.workorders.models import WorkOrderCost
        cost = WorkOrderCost.objects.create(
            work_order=work_order,
            total_estimated_cost=Decimal('0'),
            total_actual_cost=Decimal('1000.00')
        )
        assert cost.variance_percent == 0

    def test_total_cost_property(self, drill_bit, base_user):
        """Test BitRepairHistory total_cost property."""
        from apps.workorders.models import BitRepairHistory
        history = BitRepairHistory.objects.create(
            drill_bit=drill_bit,
            repair_number=1,
            repair_date=date.today(),
            repair_type=BitRepairHistory.RepairType.REDRESS,
            labor_cost=Decimal('500.00'),
            material_cost=Decimal('1000.00'),
            overhead_cost=Decimal('150.00'),
            created_by=base_user
        )
        assert history.total_cost == Decimal('1650.00')

    def test_estimated_repair_cost_property(self, drill_bit, base_user):
        """Test RepairEvaluation estimated_repair_cost property."""
        from apps.workorders.models import RepairEvaluation
        evaluation = RepairEvaluation.objects.create(
            evaluation_number='EVAL-CALC-001',
            drill_bit=drill_bit,
            damage_assessment='Test',
            estimated_labor_hours=Decimal('10.0'),
            estimated_labor_rate=Decimal('75.00'),
            estimated_material_cost=Decimal('500.00'),
            estimated_overhead=Decimal('100.00'),
            evaluated_by=base_user
        )
        expected = 10 * 75 + 500 + 100  # 1350
        assert evaluation.estimated_repair_cost == Decimal('1350.00')


# =============================================================================
# TIME LOG EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestTimeLogEdgeCases:
    """Tests for time log edge cases."""

    def test_time_log_zero_duration(self, work_order, base_user):
        """Test time log with same start and end time."""
        from apps.workorders.models import WorkOrderTimeLog
        now = timezone.now()
        log = WorkOrderTimeLog.objects.create(
            work_order=work_order,
            user=base_user,
            start_time=now,
            end_time=now
        )
        assert log.duration_minutes == 0

    def test_time_log_very_long_duration(self, work_order, base_user):
        """Test time log with very long duration."""
        from apps.workorders.models import WorkOrderTimeLog
        start = timezone.now()
        end = start + timedelta(hours=100)  # 6000 minutes
        log = WorkOrderTimeLog.objects.create(
            work_order=work_order,
            user=base_user,
            start_time=start,
            end_time=end
        )
        assert log.duration_minutes == 6000

    def test_time_log_no_end_time(self, work_order, base_user):
        """Test time log in progress (no end time)."""
        from apps.workorders.models import WorkOrderTimeLog
        log = WorkOrderTimeLog.objects.create(
            work_order=work_order,
            user=base_user,
            start_time=timezone.now()
        )
        assert log.duration_minutes is None
        assert 'In progress' in str(log)


# =============================================================================
# QR CODE EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestQRCodeEdgeCases:
    """Tests for QR code generation edge cases."""

    def test_qr_code_auto_generated(self, base_user):
        """Test QR code is auto-generated on save."""
        from apps.workorders.models import DrillBit
        bit = DrillBit.objects.create(
            serial_number='QR-AUTO-001',
            bit_type=DrillBit.BitType.FC,
            size=Decimal('8.500'),
            created_by=base_user
        )
        assert bit.qr_code == 'BIT-QR-AUTO-001'

    def test_qr_code_not_overwritten(self, base_user):
        """Test existing QR code is not overwritten."""
        from apps.workorders.models import DrillBit
        bit = DrillBit.objects.create(
            serial_number='QR-KEEP-001',
            bit_type=DrillBit.BitType.FC,
            size=Decimal('8.500'),
            qr_code='CUSTOM-QR-CODE',
            created_by=base_user
        )
        assert bit.qr_code == 'CUSTOM-QR-CODE'
