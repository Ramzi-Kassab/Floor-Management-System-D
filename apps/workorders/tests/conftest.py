"""
Workorders App - Pytest Configuration and Shared Fixtures
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def base_user(db):
    """Base user fixture for all tests."""
    return User.objects.create_user(
        username='base_user',
        email='base@example.com',
        password='basepass123',
        first_name='Base',
        last_name='User'
    )


@pytest.fixture
def staff_user(db):
    """Staff user fixture."""
    return User.objects.create_user(
        username='staff_user',
        email='staff@example.com',
        password='staffpass123',
        is_staff=True
    )


@pytest.fixture
def admin_user(db):
    """Admin/superuser fixture."""
    return User.objects.create_superuser(
        username='admin_user',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def operator_user(db):
    """Operator user for production floor tests."""
    return User.objects.create_user(
        username='operator',
        email='operator@example.com',
        password='operatorpass123',
        first_name='Shop',
        last_name='Operator'
    )


@pytest.fixture
def qc_user(db):
    """Quality control inspector user."""
    return User.objects.create_user(
        username='qc_inspector',
        email='qc@example.com',
        password='qcpass123',
        first_name='QC',
        last_name='Inspector'
    )


@pytest.fixture
def drill_bit(db, base_user):
    """Basic drill bit fixture."""
    from apps.workorders.models import DrillBit
    return DrillBit.objects.create(
        serial_number='FC-TEST-001',
        bit_type=DrillBit.BitCategory.FC,
        size=Decimal('8.500'),
        iadc_code='M423',
        status=DrillBit.Status.IN_STOCK,
        created_by=base_user
    )


@pytest.fixture
def drill_bit_rc(db, base_user):
    """Roller cone drill bit fixture."""
    from apps.workorders.models import DrillBit
    return DrillBit.objects.create(
        serial_number='RC-TEST-001',
        bit_type=DrillBit.BitCategory.RC,
        size=Decimal('12.250'),
        iadc_code='447',
        status=DrillBit.Status.NEW,
        created_by=base_user
    )


@pytest.fixture
def drill_bit_aramco(db, base_user):
    """Aramco contract drill bit with special serial tracking."""
    from apps.workorders.models import DrillBit
    return DrillBit.objects.create(
        serial_number='ARAMCO-001',
        bit_type=DrillBit.BitCategory.FC,
        size=Decimal('8.500'),
        status=DrillBit.Status.IN_STOCK,
        is_aramco_contract=True,
        base_serial_number='ARAMCO-001',
        current_display_serial='ARAMCO-001',
        revision_number=0,
        created_by=base_user
    )


@pytest.fixture
def work_order(db, base_user, drill_bit):
    """Basic work order fixture."""
    from apps.workorders.models import WorkOrder
    return WorkOrder.objects.create(
        wo_number='WO-TEST-001',
        wo_type=WorkOrder.WOType.FC_REPAIR,
        drill_bit=drill_bit,
        priority=WorkOrder.Priority.NORMAL,
        status=WorkOrder.Status.DRAFT,
        planned_start=date.today(),
        planned_end=date.today() + timedelta(days=5),
        due_date=date.today() + timedelta(days=7),
        created_by=base_user
    )


@pytest.fixture
def work_order_in_progress(db, base_user, drill_bit):
    """Work order in progress."""
    from apps.workorders.models import WorkOrder
    return WorkOrder.objects.create(
        wo_number='WO-TEST-002',
        wo_type=WorkOrder.WOType.FC_REPAIR,
        drill_bit=drill_bit,
        priority=WorkOrder.Priority.HIGH,
        status=WorkOrder.Status.IN_PROGRESS,
        actual_start=timezone.now(),
        planned_start=date.today() - timedelta(days=2),
        planned_end=date.today() + timedelta(days=3),
        due_date=date.today() + timedelta(days=5),
        created_by=base_user
    )


@pytest.fixture
def work_order_released(db, base_user, drill_bit):
    """Work order released for production."""
    from apps.workorders.models import WorkOrder
    return WorkOrder.objects.create(
        wo_number='WO-TEST-003',
        wo_type=WorkOrder.WOType.FC_NEW,
        drill_bit=drill_bit,
        priority=WorkOrder.Priority.NORMAL,
        status=WorkOrder.Status.RELEASED,
        planned_start=date.today(),
        due_date=date.today() + timedelta(days=10),
        created_by=base_user
    )


@pytest.fixture
def work_order_overdue(db, base_user, drill_bit_rc):
    """Overdue work order."""
    from apps.workorders.models import WorkOrder
    return WorkOrder.objects.create(
        wo_number='WO-TEST-004',
        wo_type=WorkOrder.WOType.RC_REPAIR,
        drill_bit=drill_bit_rc,
        priority=WorkOrder.Priority.URGENT,
        status=WorkOrder.Status.IN_PROGRESS,
        actual_start=timezone.now() - timedelta(days=10),
        due_date=date.today() - timedelta(days=3),
        created_by=base_user
    )


@pytest.fixture
def bit_evaluation(db, drill_bit, base_user):
    """Bit evaluation fixture."""
    from apps.workorders.models import BitEvaluation
    return BitEvaluation.objects.create(
        drill_bit=drill_bit,
        evaluation_date=date.today(),
        evaluated_by=base_user,
        overall_condition=BitEvaluation.Condition.GOOD,
        recommendation=BitEvaluation.Recommendation.REPAIR,
        hours_run=Decimal('50.5'),
        footage_drilled=1500,
        findings='Minor wear on cutters',
        recommendations_detail='Recommend cutter replacement'
    )


@pytest.fixture
def salvage_item(db, drill_bit, work_order, base_user):
    """Salvage item fixture."""
    from apps.workorders.models import SalvageItem
    return SalvageItem.objects.create(
        salvage_number='SALV-001',
        drill_bit=drill_bit,
        work_order=work_order,
        salvage_type=SalvageItem.SalvageType.CUTTER,
        description='Salvaged cutters from repair',
        status=SalvageItem.Status.AVAILABLE,
        condition_rating=7,
        salvage_date=date.today(),
        estimated_value=Decimal('500.00'),
        created_by=base_user
    )


@pytest.fixture
def repair_approval_authority(db):
    """Repair approval authority fixture."""
    from apps.workorders.models import RepairApprovalAuthority
    return RepairApprovalAuthority.objects.create(
        name='Operations Manager',
        min_amount=Decimal('5000.00'),
        max_amount=Decimal('25000.00'),
        requires_justification=True,
        is_active=True
    )


@pytest.fixture
def repair_evaluation(db, drill_bit, base_user):
    """Repair evaluation fixture."""
    from apps.workorders.models import RepairEvaluation
    return RepairEvaluation.objects.create(
        evaluation_number='EVAL-001',
        drill_bit=drill_bit,
        damage_assessment='Minor cutter damage, gauge wear 5%',
        recommended_repair='Replace 4 cutters, redress gauge pads',
        estimated_labor_hours=Decimal('8.0'),
        estimated_labor_rate=Decimal('75.00'),
        estimated_material_cost=Decimal('1200.00'),
        estimated_overhead=Decimal('150.00'),
        status=RepairEvaluation.Status.PENDING_APPROVAL,
        repair_recommended=True,
        evaluated_by=base_user
    )


@pytest.fixture
def process_route(db, base_user):
    """Process route fixture."""
    from apps.workorders.models import ProcessRoute, WorkOrder
    return ProcessRoute.objects.create(
        route_number='ROUTE-001',
        name='Standard FC Repair Route',
        description='Standard process route for FC bit repairs',
        repair_type=WorkOrder.RepairType.REDRESS,
        bit_types=['FC'],
        is_active=True,
        version=1,
        estimated_duration_hours=Decimal('16.0'),
        estimated_labor_cost=Decimal('1200.00'),
        created_by=base_user
    )


@pytest.fixture
def process_route_operation(db, process_route):
    """Process route operation fixture."""
    from apps.workorders.models import ProcessRouteOperation
    return ProcessRouteOperation.objects.create(
        route=process_route,
        sequence=10,
        operation_code='INSP-01',
        operation_name='Initial Inspection',
        description='Inspect incoming bit for damage',
        work_center='QC',
        standard_hours=Decimal('1.0'),
        labor_rate=Decimal('75.00'),
        requires_qc=True,
        qc_checklist='Check body, cutters, gauge, nozzles'
    )


@pytest.fixture
def repair_bom(db, work_order):
    """Repair BOM fixture."""
    from apps.workorders.models import RepairBOM
    return RepairBOM.objects.create(
        work_order=work_order,
        status=RepairBOM.Status.DRAFT,
        estimated_material_cost=Decimal('2500.00')
    )


@pytest.fixture
def work_order_cost(db, work_order):
    """Work order cost fixture."""
    from apps.workorders.models import WorkOrderCost
    return WorkOrderCost.objects.create(
        work_order=work_order,
        estimated_labor_hours=Decimal('16.0'),
        actual_labor_hours=Decimal('0.0'),
        labor_rate=Decimal('75.00'),
        estimated_material_cost=Decimal('2500.00'),
        actual_material_cost=Decimal('0.0'),
        overhead_rate_percent=Decimal('15.00'),
        total_estimated_cost=Decimal('4375.00')
    )


# Django test client fixtures
@pytest.fixture
def authenticated_client(db, client, base_user):
    """Return an authenticated test client."""
    client.force_login(base_user)
    return client


@pytest.fixture
def staff_client(db, client, staff_user):
    """Return a staff-authenticated test client."""
    client.force_login(staff_user)
    return client


@pytest.fixture
def admin_client(db, client, admin_user):
    """Return an admin-authenticated test client."""
    client.force_login(admin_user)
    return client
