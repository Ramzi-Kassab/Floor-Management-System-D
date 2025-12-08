"""
Quality App Test Fixtures
"""
import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.quality.models import Inspection, NCR

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
def inspector_user(db):
    """Create an inspector user."""
    return User.objects.create_user(
        username='inspector',
        email='inspector@example.com',
        password='testpass123'
    )


@pytest.fixture
def work_order(db, test_user):
    """Create a test work order."""
    from apps.workorders.models import WorkOrder
    return WorkOrder.objects.create(
        work_order_number='WO-QC-001',
        title='Test Work Order',
        description='Test description',
        status='IN_PROGRESS',
        created_by=test_user
    )


@pytest.fixture
def drill_bit(db):
    """Create a test drill bit."""
    from apps.workorders.models import DrillBit
    return DrillBit.objects.create(
        serial_number='DB-QC-001',
        status='IN_SERVICE'
    )


@pytest.fixture
def inspection(db, test_user, work_order):
    """Create a test inspection."""
    return Inspection.objects.create(
        inspection_number='INSP-001',
        inspection_type=Inspection.InspectionType.IN_PROCESS,
        work_order=work_order,
        scheduled_date=date.today(),
        status=Inspection.Status.SCHEDULED,
        created_by=test_user
    )


@pytest.fixture
def completed_inspection(db, test_user, inspector_user, work_order):
    """Create a completed inspection."""
    return Inspection.objects.create(
        inspection_number='INSP-002',
        inspection_type=Inspection.InspectionType.FINAL,
        work_order=work_order,
        scheduled_date=date.today() - timedelta(days=1),
        status=Inspection.Status.PASSED,
        inspected_by=inspector_user,
        inspected_at=timezone.now(),
        pass_count=10,
        fail_count=0,
        created_by=test_user
    )


@pytest.fixture
def ncr(db, test_user, work_order, inspection):
    """Create a test NCR."""
    return NCR.objects.create(
        ncr_number='NCR-001',
        work_order=work_order,
        inspection=inspection,
        title='Surface defect detected',
        description='Surface crack found during inspection',
        severity=NCR.Severity.MINOR,
        status=NCR.Status.OPEN,
        detected_at=timezone.now(),
        detected_by=test_user,
        detection_stage='In-Process Inspection'
    )


# Fixtures for base class tests
@pytest.fixture
def test_object(inspection):
    """Default test object for base class tests."""
    return inspection


@pytest.fixture
def valid_data(work_order):
    """Valid data for inspection creation."""
    return {
        'inspection_number': 'INSP-NEW',
        'inspection_type': Inspection.InspectionType.INCOMING,
        'work_order': work_order.pk,
        'scheduled_date': date.today(),
        'status': Inspection.Status.SCHEDULED,
    }
