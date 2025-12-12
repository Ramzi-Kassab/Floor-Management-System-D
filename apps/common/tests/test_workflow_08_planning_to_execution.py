"""
Planning to Execution Workflow Integration Test
===============================================

Cross-App Integration:
- Planning: Project and sprint management
- Dispatch: Field scheduling and assignment
- Execution: Procedure execution tracking
- Reports: Progress and completion reporting
- Notifications: Status updates

Workflow Steps:
1. Create project plan
2. Break into tasks/planning items
3. Schedule tasks in sprint
4. Dispatch to field team
5. Execute procedures
6. Track progress
7. Complete tasks
8. Generate completion report

Author: Workflow Integration Suite
Date: December 2024
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def project_manager(db):
    """Create project manager user."""
    return User.objects.create_user(
        username='proj_mgr',
        email='project@ardt.com',
        password='projpass123',
        first_name='Project',
        last_name='Manager',
        is_staff=True
    )


@pytest.fixture
def field_tech(db):
    """Create field technician user."""
    return User.objects.create_user(
        username='field_tech',
        email='fieldtech@ardt.com',
        password='fieldpass123',
        first_name='Field',
        last_name='Technician'
    )


@pytest.fixture
def dispatcher(db):
    """Create dispatcher user."""
    return User.objects.create_user(
        username='dispatcher',
        email='dispatch@ardt.com',
        password='dispatchpass123',
        first_name='John',
        last_name='Dispatcher',
        is_staff=True
    )


@pytest.fixture
def customer(db, project_manager):
    """Create a customer for dispatch."""
    from apps.sales.models import Customer
    return Customer.objects.create(
        code='CUST-FIELD-001',
        name='Aramco Field Operations',
        customer_type=Customer.CustomerType.OPERATOR,
        city='Dhahran',
        country='Saudi Arabia',
        is_active=True,
        created_by=project_manager
    )


@pytest.fixture
def vehicle(db):
    """Create a dispatch vehicle."""
    from apps.dispatch.models import Vehicle
    return Vehicle.objects.create(
        code='VEH-001',
        plate_number='KSA-1234',
        make='Toyota',
        model='Hilux',
        year=2022,
        status=Vehicle.Status.AVAILABLE,
        is_active=True
    )


# =============================================================================
# PLANNING TO EXECUTION WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestPlanningToExecutionWorkflow:
    """
    Complete planning to execution workflow test.

    Tests the full cycle from project planning through
    field execution and completion reporting.
    """

    def test_full_planning_to_execution_workflow(
        self,
        project_manager,
        field_tech,
        dispatcher,
        customer,
        vehicle
    ):
        """
        Test complete planning to execution workflow.

        Steps:
        1. Create project sprint
        2. Create planning board and items
        3. Break into tasks
        4. Schedule tasks
        5. Create dispatch
        6. Start field execution
        7. Track progress
        8. Complete tasks
        9. Close dispatch
        10. Generate report
        """
        from apps.planning.models import Sprint, PlanningBoard, PlanningColumn, PlanningItem
        from apps.dispatch.models import Dispatch, DispatchItem, Vehicle
        from apps.procedures.models import Procedure
        from apps.execution.models import ProcedureExecution
        from apps.workorders.models import WorkOrder, DrillBit
        from apps.notifications.models import Notification

        print("\n" + "="*60)
        print("PLANNING TO EXECUTION WORKFLOW")
        print("="*60)

        # ---------------------------------------------------------------------
        # STEP 1: Create project sprint
        # ---------------------------------------------------------------------
        print("\n[Step 1] Creating project sprint...")

        sprint = Sprint.objects.create(
            name='Field Service Sprint Q4',
            code='SPRINT-Q4-2024',
            goal='Complete all scheduled field service visits',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=14),
            status=Sprint.Status.ACTIVE,
            capacity_points=50,
            owner=project_manager,
            created_by=project_manager
        )

        assert sprint.pk is not None
        print(f"  Sprint: {sprint.code}")
        print(f"  Duration: {sprint.start_date} to {sprint.end_date}")
        print(f"  Capacity: {sprint.capacity_points} points")

        # ---------------------------------------------------------------------
        # STEP 2: Create planning board and columns
        # ---------------------------------------------------------------------
        print("\n[Step 2] Creating planning board...")

        board = PlanningBoard.objects.create(
            name='Field Service Board',
            code='BOARD-FIELD-001',
            description='Track field service activities',
            sprint=sprint,
            owner=project_manager
        )

        # Create columns
        col_backlog = PlanningColumn.objects.create(
            board=board,
            name='Backlog',
            code='BACKLOG',
            sequence=1,
            is_backlog_column=True
        )
        col_todo = PlanningColumn.objects.create(
            board=board,
            name='To Do',
            code='TODO',
            sequence=2
        )
        col_progress = PlanningColumn.objects.create(
            board=board,
            name='In Progress',
            code='IN_PROGRESS',
            sequence=3
        )
        col_done = PlanningColumn.objects.create(
            board=board,
            name='Done',
            code='DONE',
            sequence=4,
            is_done_column=True
        )

        print(f"  Board: {board.name}")
        print(f"  Columns: Backlog, To Do, In Progress, Done")

        # ---------------------------------------------------------------------
        # STEP 3: Create planning items (tasks)
        # ---------------------------------------------------------------------
        print("\n[Step 3] Creating planning items...")

        item1 = PlanningItem.objects.create(
            board=board,
            column=col_backlog,
            code='FIELD-001',
            title='Bit inspection at Rig 15',
            description='Inspect FC bits at customer rig site',
            item_type=PlanningItem.ItemType.TASK,
            priority=PlanningItem.Priority.HIGH,
            story_points=8,
            assignee=field_tech,
            due_date=date.today() + timedelta(days=3),
            created_by=project_manager
        )

        item2 = PlanningItem.objects.create(
            board=board,
            column=col_backlog,
            code='FIELD-002',
            title='Bit delivery to Rig 22',
            description='Deliver repaired bits to customer site',
            item_type=PlanningItem.ItemType.TASK,
            priority=PlanningItem.Priority.MEDIUM,
            story_points=5,
            assignee=field_tech,
            due_date=date.today() + timedelta(days=5),
            created_by=project_manager
        )

        print(f"  Task 1: {item1.title} ({item1.story_points} pts)")
        print(f"  Task 2: {item2.title} ({item2.story_points} pts)")

        # Move to To Do
        item1.column = col_todo
        item1.save()
        item2.column = col_todo
        item2.save()

        # ---------------------------------------------------------------------
        # STEP 4: Schedule tasks
        # ---------------------------------------------------------------------
        print("\n[Step 4] Scheduling tasks...")

        # Create work order for the inspection task
        drill_bit = DrillBit.objects.create(
            serial_number='FC-INSP-001',
            bit_type=DrillBit.BitCategory.FC,
            size=Decimal('8.500'),
            status=DrillBit.Status.IN_FIELD,
            created_by=project_manager
        )

        work_order = WorkOrder.objects.create(
            wo_number='WO-FIELD-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            drill_bit=drill_bit,
            status=WorkOrder.Status.RELEASED,
            planned_start=date.today(),
            due_date=date.today() + timedelta(days=3),
            created_by=project_manager
        )

        print(f"  Work Order: {work_order.wo_number}")
        print(f"  Scheduled: {work_order.planned_start}")

        # ---------------------------------------------------------------------
        # STEP 5: Create dispatch
        # ---------------------------------------------------------------------
        print("\n[Step 5] Creating dispatch...")

        dispatch = Dispatch.objects.create(
            dispatch_number='DISP-2024-001',
            vehicle=vehicle,
            driver_name='Mohammed',
            customer=customer,
            planned_date=date.today(),
            status=Dispatch.Status.PLANNED,
            notes='Field service visit for bit inspection',
            created_by=dispatcher
        )

        # Track dispatch item via work order link
        # Note: DispatchItem requires sales_order_line, so we track via notes
        dispatch.notes = f'{dispatch.notes} - WO: {work_order.wo_number}'
        dispatch.save()

        print(f"  Dispatch: {dispatch.dispatch_number}")
        print(f"  Vehicle: {vehicle.code}")
        print(f"  Driver: {dispatch.driver_name}")

        # ---------------------------------------------------------------------
        # STEP 6: Start field execution
        # ---------------------------------------------------------------------
        print("\n[Step 6] Starting field execution...")

        # Update dispatch status
        dispatch.status = Dispatch.Status.IN_TRANSIT
        dispatch.actual_departure = timezone.now()
        dispatch.save()

        # Update vehicle status
        vehicle.status = Vehicle.Status.IN_USE
        vehicle.save()

        # Move planning item to In Progress
        item1.column = col_progress
        item1.save()

        # Start work order
        work_order.status = WorkOrder.Status.IN_PROGRESS
        work_order.actual_start = date.today()
        work_order.save()

        print(f"  Dispatch status: {dispatch.get_status_display()}")
        print(f"  Work order status: {work_order.get_status_display()}")

        # Create procedure execution
        procedure, _ = Procedure.objects.get_or_create(
            code='PROC-BIT-INSP',
            defaults={
                'name': 'Bit Inspection Procedure',
                'revision': '1.0',
                'status': Procedure.Status.ACTIVE,
                'created_by': project_manager
            }
        )

        execution = ProcedureExecution.objects.create(
            procedure=procedure,
            work_order=work_order,
            status=ProcedureExecution.Status.IN_PROGRESS,
            started_at=timezone.now(),
            started_by=field_tech
        )

        print(f"  Procedure execution started")

        # ---------------------------------------------------------------------
        # STEP 7: Track progress
        # ---------------------------------------------------------------------
        print("\n[Step 7] Tracking progress...")

        # Update progress
        execution.progress_percent = 50
        execution.save()

        print(f"  Execution progress: {execution.progress_percent}%")

        # Send progress notification
        progress_notification = Notification.objects.create(
            recipient=project_manager,
            title=f'Field Task Progress: {item1.title}',
            message=f'Task is 50% complete. Expected completion today.',
            priority=Notification.Priority.NORMAL,
            entity_type='planning.planningitem',
            entity_id=item1.pk
        )

        print(f"  Progress notification sent")

        # ---------------------------------------------------------------------
        # STEP 8: Complete tasks
        # ---------------------------------------------------------------------
        print("\n[Step 8] Completing tasks...")

        # Complete procedure execution
        execution.status = ProcedureExecution.Status.COMPLETED
        execution.completed_at = timezone.now()
        execution.completed_by = field_tech
        execution.progress_percent = 100
        execution.result_summary = 'Bit inspection completed. All measurements within spec.'
        execution.save()

        # Complete work order
        work_order.status = WorkOrder.Status.COMPLETED
        work_order.actual_end = date.today()
        work_order.progress_percent = 100
        work_order.save()

        # Move planning item to Done column
        item1.column = col_done
        item1.completed_date = date.today()
        item1.save()

        # Update sprint progress
        sprint.completed_points += item1.story_points
        sprint.save()

        print(f"  Work order: {work_order.get_status_display()}")
        print(f"  Planning item: Moved to Done column")
        print(f"  Sprint progress: {sprint.completed_points}/{sprint.capacity_points} pts")

        # ---------------------------------------------------------------------
        # STEP 9: Close dispatch
        # ---------------------------------------------------------------------
        print("\n[Step 9] Closing dispatch...")

        dispatch.status = Dispatch.Status.DELIVERED
        dispatch.actual_arrival = timezone.now()
        dispatch.save()

        # Return vehicle
        vehicle.status = Vehicle.Status.AVAILABLE
        vehicle.save()

        print(f"  Dispatch status: {dispatch.get_status_display()}")
        print(f"  Vehicle returned: {vehicle.get_status_display()}")

        # ---------------------------------------------------------------------
        # STEP 10: Final verification
        # ---------------------------------------------------------------------
        print("\n[Step 10] Final verification...")

        final_checks = {
            'sprint_active': sprint.status == Sprint.Status.ACTIVE,
            'board_created': board.pk is not None,
            'tasks_created': PlanningItem.objects.filter(board=board).count() >= 2,
            'work_order_complete': work_order.status == WorkOrder.Status.COMPLETED,
            'dispatch_complete': dispatch.status == Dispatch.Status.DELIVERED,
            'execution_complete': execution.status == ProcedureExecution.Status.COMPLETED,
            'vehicle_returned': vehicle.status == Vehicle.Status.AVAILABLE,
            'sprint_progress_updated': sprint.completed_points > 0,
        }

        all_passed = all(final_checks.values())

        print("\n  Execution Summary:")
        print(f"    Sprint: {sprint.code}")
        print(f"    Tasks completed: 1/{PlanningItem.objects.filter(board=board).count()}")
        print(f"    Sprint progress: {sprint.progress_percent}%")
        print(f"    Dispatch: {dispatch.dispatch_number}")

        print("\n  Workflow Checklist:")
        for check, status in final_checks.items():
            icon = "  " if status else "  "
            print(f"    {icon} {check.replace('_', ' ').title()}")

        assert all_passed

        print("\n" + "="*60)
        print("PLANNING TO EXECUTION WORKFLOW COMPLETED!")
        print("="*60)


# =============================================================================
# WORKFLOW SUMMARY
# =============================================================================

@pytest.mark.django_db
class TestPlanningWorkflowSummary:
    """Summary tests for planning workflow."""

    def test_workflow_models_exist(self, db):
        """Verify all workflow models are accessible."""
        from apps.planning.models import Sprint, PlanningBoard, PlanningItem
        from apps.dispatch.models import Dispatch, Vehicle
        from apps.execution.models import ProcedureExecution
        from apps.workorders.models import WorkOrder

        assert Sprint._meta.model_name == 'sprint'
        assert PlanningBoard._meta.model_name == 'planningboard'
        assert Dispatch._meta.model_name == 'dispatch'
        assert ProcedureExecution._meta.model_name == 'procedureexecution'
        assert WorkOrder._meta.model_name == 'workorder'

        print("\nAll planning workflow models verified!")
