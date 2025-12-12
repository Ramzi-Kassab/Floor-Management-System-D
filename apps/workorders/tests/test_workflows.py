"""
Workorders App - Integration/Workflow Tests
End-to-end tests for complete user workflows.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType


# =============================================================================
# WORK ORDER LIFECYCLE WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderLifecycleWorkflow:
    """Tests for complete work order lifecycle from draft to completion."""

    def test_full_work_order_lifecycle(self, base_user, drill_bit):
        """Test complete work order lifecycle: Draft → Released → In Progress → QC → Completed."""
        from apps.workorders.models import WorkOrder

        # 1. Create work order (DRAFT)
        wo = WorkOrder.objects.create(
            wo_number='WO-LIFE-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            drill_bit=drill_bit,
            priority=WorkOrder.Priority.NORMAL,
            status=WorkOrder.Status.DRAFT,
            planned_start=date.today(),
            due_date=date.today() + timedelta(days=7),
            created_by=base_user
        )
        assert wo.status == WorkOrder.Status.DRAFT

        # 2. Release for production
        wo.status = WorkOrder.Status.RELEASED
        wo.save()
        assert wo.can_start is True

        # 3. Start work
        result = wo.start_work()
        assert result is True
        assert wo.status == WorkOrder.Status.IN_PROGRESS
        assert wo.actual_start is not None

        # 4. Submit for QC
        result = wo.submit_for_qc()
        assert result is True
        assert wo.status == WorkOrder.Status.QC_PENDING

        # 5. QC Passed
        wo.status = WorkOrder.Status.QC_PASSED
        wo.save()
        assert wo.can_complete is True

        # 6. Complete work order
        result = wo.complete_work()
        assert result is True
        assert wo.status == WorkOrder.Status.COMPLETED
        assert wo.actual_end is not None
        assert wo.progress_percent == 100

    def test_work_order_on_hold_workflow(self, base_user, drill_bit):
        """Test work order can be put on hold and resumed."""
        from apps.workorders.models import WorkOrder

        # Create and start work order
        wo = WorkOrder.objects.create(
            wo_number='WO-HOLD-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            drill_bit=drill_bit,
            status=WorkOrder.Status.IN_PROGRESS,
            actual_start=timezone.now(),
            created_by=base_user
        )

        # Put on hold
        result = wo.put_on_hold(reason='Waiting for customer approval')
        assert result is True
        assert wo.status == WorkOrder.Status.ON_HOLD
        assert 'Waiting for customer approval' in wo.notes

        # Resume work (would typically be done via view)
        wo.status = WorkOrder.Status.IN_PROGRESS
        wo.save()
        assert wo.status == WorkOrder.Status.IN_PROGRESS

    def test_work_order_qc_failure_workflow(self, base_user, drill_bit):
        """Test work order QC failure and rework workflow."""
        from apps.workorders.models import WorkOrder

        # Create work order in progress
        wo = WorkOrder.objects.create(
            wo_number='WO-QCF-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            drill_bit=drill_bit,
            status=WorkOrder.Status.IN_PROGRESS,
            actual_start=timezone.now(),
            created_by=base_user
        )

        # Submit for QC
        wo.submit_for_qc()
        assert wo.status == WorkOrder.Status.QC_PENDING

        # QC Failed
        wo.status = WorkOrder.Status.QC_FAILED
        wo.notes = 'Failed dimensional check'
        wo.save()

        # Rework - back to IN_PROGRESS
        wo.status = WorkOrder.Status.IN_PROGRESS
        wo.save()
        assert wo.status == WorkOrder.Status.IN_PROGRESS


# =============================================================================
# DRILL BIT LIFECYCLE WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestDrillBitLifecycleWorkflow:
    """Tests for drill bit lifecycle from new to field use."""

    def test_full_drill_bit_lifecycle(self, base_user):
        """Test complete drill bit lifecycle: New → In Stock → Assigned → Dispatched → Field → Returned."""
        from apps.workorders.models import DrillBit

        # 1. Register new bit
        bit = DrillBit.objects.create(
            serial_number='FC-LIFE-001',
            bit_type=DrillBit.BitCategory.FC,
            size=Decimal('8.500'),
            status=DrillBit.Status.NEW,
            created_by=base_user
        )
        assert bit.status == DrillBit.Status.NEW

        # 2. QC passed, move to stock
        bit.status = DrillBit.Status.IN_STOCK
        bit.save()
        assert bit.status == DrillBit.Status.IN_STOCK

        # 3. Assigned to work order
        bit.status = DrillBit.Status.ASSIGNED
        bit.save()
        assert bit.status == DrillBit.Status.ASSIGNED

        # 4. Ready for dispatch
        bit.status = DrillBit.Status.READY
        bit.save()
        assert bit.status == DrillBit.Status.READY

        # 5. Dispatched to customer
        bit.status = DrillBit.Status.DISPATCHED
        bit.physical_status = DrillBit.PhysicalStatus.IN_TRANSIT
        bit.save()
        assert bit.status == DrillBit.Status.DISPATCHED

        # 6. In field
        bit.status = DrillBit.Status.IN_FIELD
        bit.physical_status = DrillBit.PhysicalStatus.AT_RIG
        bit.run_count = 1
        bit.total_hours = Decimal('50.0')
        bit.total_footage = 1500
        bit.save()
        assert bit.run_count == 1

        # 7. Returned
        bit.status = DrillBit.Status.RETURNED
        bit.physical_status = DrillBit.PhysicalStatus.AT_ARDT
        bit.save()
        assert bit.status == DrillBit.Status.RETURNED

    def test_aramco_serial_number_revision_workflow(self, base_user):
        """Test Aramco contract serial number revision on repair."""
        from apps.workorders.models import DrillBit

        # Create Aramco contract bit
        bit = DrillBit.objects.create(
            serial_number='ARAMCO-TEST-001',
            bit_type=DrillBit.BitCategory.FC,
            size=Decimal('8.500'),
            status=DrillBit.Status.IN_STOCK,
            is_aramco_contract=True,
            base_serial_number='ARAMCO-TEST-001',
            current_display_serial='ARAMCO-TEST-001',
            revision_number=0,
            created_by=base_user
        )

        # After first repair
        bit.revision_number = 1
        bit.current_display_serial = 'ARAMCO-TEST-001-R1'
        bit.total_repairs = 1
        bit.last_repair_date = date.today()
        bit.last_repair_type = 'REDRESS'
        bit.save()

        assert bit.revision_number == 1
        assert bit.current_display_serial == 'ARAMCO-TEST-001-R1'
        assert bit.base_serial_number == 'ARAMCO-TEST-001'


# =============================================================================
# REPAIR EVALUATION WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestRepairEvaluationWorkflow:
    """Tests for repair evaluation and approval workflow."""

    def test_full_repair_evaluation_workflow(self, drill_bit, base_user, admin_user):
        """Test complete repair evaluation: Draft → Pending Approval → Approved → WO Created."""
        from apps.workorders.models import RepairEvaluation, WorkOrder

        # 1. Create evaluation (DRAFT)
        evaluation = RepairEvaluation.objects.create(
            evaluation_number='EVAL-FLOW-001',
            drill_bit=drill_bit,
            damage_assessment='Worn cutters, gauge within spec',
            recommended_repair='Replace 4 cutters',
            estimated_labor_hours=Decimal('8.0'),
            estimated_labor_rate=Decimal('75.00'),
            estimated_material_cost=Decimal('1200.00'),
            estimated_overhead=Decimal('150.00'),
            status=RepairEvaluation.Status.DRAFT,
            repair_recommended=True,
            evaluated_by=base_user
        )
        assert evaluation.status == RepairEvaluation.Status.DRAFT

        # 2. Submit for approval
        evaluation.status = RepairEvaluation.Status.PENDING_APPROVAL
        evaluation.requires_approval = True
        evaluation.save()
        assert evaluation.status == RepairEvaluation.Status.PENDING_APPROVAL

        # 3. Approve evaluation
        evaluation.status = RepairEvaluation.Status.APPROVED
        evaluation.approved_by = admin_user
        evaluation.approved_at = timezone.now()
        evaluation.approval_notes = 'Approved for repair'
        evaluation.save()
        assert evaluation.status == RepairEvaluation.Status.APPROVED

        # 4. Create work order from evaluation
        wo = WorkOrder.objects.create(
            wo_number='WO-EVAL-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            drill_bit=drill_bit,
            status=WorkOrder.Status.DRAFT,
            estimated_cost=evaluation.estimated_repair_cost,
            created_by=base_user
        )
        evaluation.resulting_work_order = wo
        evaluation.status = RepairEvaluation.Status.COMPLETED
        evaluation.save()

        assert evaluation.resulting_work_order == wo
        assert evaluation.status == RepairEvaluation.Status.COMPLETED

    def test_repair_evaluation_rejection_workflow(self, drill_bit, base_user, admin_user):
        """Test repair evaluation rejection workflow."""
        from apps.workorders.models import RepairEvaluation

        # Create evaluation
        evaluation = RepairEvaluation.objects.create(
            evaluation_number='EVAL-REJ-001',
            drill_bit=drill_bit,
            damage_assessment='Extensive damage beyond economical repair',
            status=RepairEvaluation.Status.PENDING_APPROVAL,
            repair_recommended=False,
            evaluated_by=base_user
        )

        # Reject evaluation
        evaluation.status = RepairEvaluation.Status.REJECTED
        evaluation.approved_by = admin_user
        evaluation.approved_at = timezone.now()
        evaluation.approval_notes = 'Recommend scrap - repair cost exceeds value'
        evaluation.save()

        assert evaluation.status == RepairEvaluation.Status.REJECTED
        assert 'scrap' in evaluation.approval_notes.lower()


# =============================================================================
# PROCESS ROUTE EXECUTION WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestProcessRouteExecutionWorkflow:
    """Tests for process route execution on work orders."""

    def test_route_operation_execution_workflow(self, work_order, process_route, process_route_operation, operator_user, qc_user):
        """Test executing operations from a process route."""
        from apps.workorders.models import OperationExecution

        # Create operation execution from route
        exec = OperationExecution.objects.create(
            work_order=work_order,
            route_operation=process_route_operation,
            sequence=process_route_operation.sequence,
            status=OperationExecution.Status.PENDING
        )
        assert exec.status == OperationExecution.Status.PENDING

        # Start operation
        exec.status = OperationExecution.Status.IN_PROGRESS
        exec.operator = operator_user
        exec.start_time = timezone.now()
        exec.save()
        assert exec.status == OperationExecution.Status.IN_PROGRESS

        # Complete operation
        exec.status = OperationExecution.Status.COMPLETED
        exec.end_time = timezone.now()
        exec.actual_hours = Decimal('1.5')
        exec.labor_cost = exec.actual_hours * process_route_operation.labor_rate
        exec.save()

        assert exec.status == OperationExecution.Status.COMPLETED
        assert exec.actual_hours == Decimal('1.5')

        # QC if required
        if process_route_operation.requires_qc:
            exec.qc_performed = True
            exec.qc_passed = True
            exec.qc_by = qc_user
            exec.qc_notes = 'Passed all checks'
            exec.save()
            assert exec.qc_passed is True


# =============================================================================
# SALVAGE WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestSalvageWorkflow:
    """Tests for salvage item workflow."""

    def test_full_salvage_workflow(self, drill_bit, work_order, base_user):
        """Test complete salvage workflow: Created → Available → Reserved → Consumed."""
        from apps.workorders.models import SalvageItem, WorkOrder

        # 1. Create salvage item during repair
        salvage = SalvageItem.objects.create(
            salvage_number='SALV-FLOW-001',
            drill_bit=drill_bit,
            work_order=work_order,
            salvage_type=SalvageItem.SalvageType.CUTTER,
            description='Salvaged good cutters',
            status=SalvageItem.Status.AVAILABLE,
            condition_rating=8,
            salvage_date=date.today(),
            estimated_value=Decimal('300.00'),
            created_by=base_user
        )
        assert salvage.status == SalvageItem.Status.AVAILABLE

        # 2. Reserve for another work order
        new_wo = WorkOrder.objects.create(
            wo_number='WO-USE-SALV-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            status=WorkOrder.Status.IN_PROGRESS,
            created_by=base_user
        )
        salvage.status = SalvageItem.Status.RESERVED
        salvage.reused_in_work_order = new_wo
        salvage.save()
        assert salvage.status == SalvageItem.Status.RESERVED

        # 3. Consume in repair
        salvage.status = SalvageItem.Status.CONSUMED
        salvage.reused_date = date.today()
        salvage.save()
        assert salvage.status == SalvageItem.Status.CONSUMED

    def test_salvage_scrap_workflow(self, drill_bit, work_order, base_user):
        """Test salvage item scrap workflow."""
        from apps.workorders.models import SalvageItem

        # Create salvage item
        salvage = SalvageItem.objects.create(
            salvage_number='SALV-SCRAP-001',
            drill_bit=drill_bit,
            work_order=work_order,
            salvage_type=SalvageItem.SalvageType.BEARING,
            description='Damaged bearing',
            status=SalvageItem.Status.AVAILABLE,
            condition_rating=2,  # Poor condition
            salvage_date=date.today(),
            created_by=base_user
        )

        # Decision to scrap due to poor condition
        salvage.status = SalvageItem.Status.SCRAPPED
        salvage.save()
        assert salvage.status == SalvageItem.Status.SCRAPPED


# =============================================================================
# COST TRACKING WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestCostTrackingWorkflow:
    """Tests for work order cost tracking workflow."""

    def test_cost_accumulation_workflow(self, work_order, base_user):
        """Test cost accumulation during work order execution."""
        from apps.workorders.models import WorkOrderCost, WorkOrderTimeLog

        # Create cost record
        cost = WorkOrderCost.objects.create(
            work_order=work_order,
            estimated_labor_hours=Decimal('16.0'),
            labor_rate=Decimal('75.00'),
            estimated_material_cost=Decimal('2500.00'),
            overhead_rate_percent=Decimal('15.00')
        )
        cost.total_estimated_cost = (
            cost.estimated_labor_hours * cost.labor_rate +
            cost.estimated_material_cost +
            (cost.estimated_labor_hours * cost.labor_rate + cost.estimated_material_cost) * cost.overhead_rate_percent / 100
        )
        cost.save()

        # Log time
        log1 = WorkOrderTimeLog.objects.create(
            work_order=work_order,
            user=base_user,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=4),
            hourly_rate=Decimal('75.00')
        )
        log2 = WorkOrderTimeLog.objects.create(
            work_order=work_order,
            user=base_user,
            start_time=timezone.now() + timedelta(hours=5),
            end_time=timezone.now() + timedelta(hours=8),
            hourly_rate=Decimal('75.00')
        )

        # Update actual costs
        total_hours = sum([log.duration_minutes for log in [log1, log2]]) / 60
        cost.actual_labor_hours = Decimal(str(total_hours))
        cost.labor_cost = cost.actual_labor_hours * cost.labor_rate
        cost.save()

        assert cost.actual_labor_hours > 0
        assert cost.labor_cost > 0


# =============================================================================
# STATUS TRANSITION AUDIT WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestStatusAuditWorkflow:
    """Tests for status transition audit trail."""

    def test_status_transition_audit_trail(self, work_order, base_user):
        """Test status transitions are logged."""
        from apps.workorders.models import StatusTransitionLog, WorkOrder

        content_type = ContentType.objects.get_for_model(WorkOrder)

        # Log initial status
        StatusTransitionLog.objects.create(
            content_type=content_type,
            object_id=work_order.pk,
            from_status='',
            to_status='DRAFT',
            changed_by=base_user,
            reason='Work order created'
        )

        # Release
        work_order.status = WorkOrder.Status.RELEASED
        work_order.save()
        StatusTransitionLog.objects.create(
            content_type=content_type,
            object_id=work_order.pk,
            from_status='DRAFT',
            to_status='RELEASED',
            changed_by=base_user,
            reason='Ready for production'
        )

        # Verify audit trail
        logs = StatusTransitionLog.objects.filter(
            content_type=content_type,
            object_id=work_order.pk
        ).order_by('changed_at')

        assert logs.count() == 2
        assert logs[0].to_status == 'DRAFT'
        assert logs[1].to_status == 'RELEASED'
        assert logs[1].from_status == 'DRAFT'


# =============================================================================
# BIT REPAIR HISTORY WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestBitRepairHistoryWorkflow:
    """Tests for bit repair history tracking."""

    def test_repair_history_accumulation(self, drill_bit, base_user):
        """Test repair history accumulates over multiple repairs."""
        from apps.workorders.models import BitRepairHistory, WorkOrder

        # First repair
        wo1 = WorkOrder.objects.create(
            wo_number='WO-HIST-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            drill_bit=drill_bit,
            created_by=base_user
        )
        history1 = BitRepairHistory.objects.create(
            drill_bit=drill_bit,
            work_order=wo1,
            repair_number=1,
            repair_date=date.today() - timedelta(days=90),
            repair_type=BitRepairHistory.RepairType.REDRESS,
            labor_cost=Decimal('400.00'),
            material_cost=Decimal('800.00'),
            created_by=base_user
        )

        # Second repair
        wo2 = WorkOrder.objects.create(
            wo_number='WO-HIST-002',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            drill_bit=drill_bit,
            created_by=base_user
        )
        history2 = BitRepairHistory.objects.create(
            drill_bit=drill_bit,
            work_order=wo2,
            repair_number=2,
            repair_date=date.today(),
            repair_type=BitRepairHistory.RepairType.MAJOR_REPAIR,
            labor_cost=Decimal('800.00'),
            material_cost=Decimal('1500.00'),
            created_by=base_user
        )

        # Update drill bit repair tracking
        drill_bit.total_repairs = 2
        drill_bit.last_repair_date = date.today()
        drill_bit.last_repair_type = 'MAJOR_REPAIR'
        drill_bit.total_repair_cost = (
            history1.total_cost + history2.total_cost
        )
        drill_bit.save()

        assert drill_bit.total_repairs == 2
        assert drill_bit.total_repair_cost == Decimal('3500.00')

        # Verify history records
        history = BitRepairHistory.objects.filter(drill_bit=drill_bit).order_by('repair_number')
        assert history.count() == 2
        assert history[0].repair_number == 1
        assert history[1].repair_number == 2


# =============================================================================
# REPAIR BOM WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestRepairBOMWorkflow:
    """Tests for repair BOM workflow."""

    def test_repair_bom_lifecycle(self, work_order, base_user):
        """Test repair BOM lifecycle: Draft → Approved → Issued → Completed."""
        from apps.workorders.models import RepairBOM

        # 1. Create BOM (DRAFT)
        bom = RepairBOM.objects.create(
            work_order=work_order,
            status=RepairBOM.Status.DRAFT,
            estimated_material_cost=Decimal('2500.00')
        )
        assert bom.status == RepairBOM.Status.DRAFT

        # 2. Approve BOM
        bom.status = RepairBOM.Status.APPROVED
        bom.approved_by = base_user
        bom.approved_at = timezone.now()
        bom.save()
        assert bom.status == RepairBOM.Status.APPROVED

        # 3. Issue materials
        bom.status = RepairBOM.Status.ISSUED
        bom.save()
        assert bom.status == RepairBOM.Status.ISSUED

        # 4. Complete (all materials consumed)
        bom.status = RepairBOM.Status.COMPLETED
        bom.actual_material_cost = Decimal('2650.00')
        bom.save()
        assert bom.status == RepairBOM.Status.COMPLETED
        assert bom.actual_material_cost > bom.estimated_material_cost
