"""
ERP Integration App - Pytest Configuration and Shared Fixtures
"""

import pytest
from datetime import datetime
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
def erp_mapping(db):
    """ERP mapping fixture."""
    from apps.erp_integration.models import ERPMapping
    return ERPMapping.objects.create(
        entity_type=ERPMapping.EntityType.CUSTOMER,
        ardt_id=1001,
        erp_system='SAP',
        erp_id='SAP-CUST-001',
        is_active=True
    )


@pytest.fixture
def erp_mapping_item(db):
    """ERP mapping for inventory item fixture."""
    from apps.erp_integration.models import ERPMapping
    return ERPMapping.objects.create(
        entity_type=ERPMapping.EntityType.ITEM,
        ardt_id=2001,
        erp_system='SAP',
        erp_id='SAP-ITEM-001',
        is_active=True
    )


@pytest.fixture
def erp_mapping_oracle(db):
    """ERP mapping for Oracle system fixture."""
    from apps.erp_integration.models import ERPMapping
    return ERPMapping.objects.create(
        entity_type=ERPMapping.EntityType.WORK_ORDER,
        ardt_id=3001,
        erp_system='ORACLE',
        erp_id='ORA-WO-001',
        is_active=True
    )


@pytest.fixture
def erp_sync_log(db):
    """ERP sync log fixture."""
    from apps.erp_integration.models import ERPSyncLog
    return ERPSyncLog.objects.create(
        erp_system='SAP',
        direction=ERPSyncLog.Direction.OUTBOUND,
        entity_type='CUSTOMER',
        entity_id=1001,
        status=ERPSyncLog.Status.PENDING,
        request_payload={'customer_id': 1001, 'action': 'create'}
    )


@pytest.fixture
def erp_sync_log_success(db):
    """Successful ERP sync log fixture."""
    from apps.erp_integration.models import ERPSyncLog
    return ERPSyncLog.objects.create(
        erp_system='SAP',
        direction=ERPSyncLog.Direction.OUTBOUND,
        entity_type='ITEM',
        entity_id=2001,
        status=ERPSyncLog.Status.SUCCESS,
        request_payload={'item_id': 2001, 'action': 'update'},
        response_payload={'status': 'ok', 'erp_id': 'SAP-ITEM-001'},
        completed_at=timezone.now()
    )


@pytest.fixture
def erp_sync_log_failed(db):
    """Failed ERP sync log fixture."""
    from apps.erp_integration.models import ERPSyncLog
    return ERPSyncLog.objects.create(
        erp_system='ORACLE',
        direction=ERPSyncLog.Direction.INBOUND,
        entity_type='SALES_ORDER',
        entity_id=5001,
        status=ERPSyncLog.Status.FAILED,
        request_payload={'so_number': 'SO-5001'},
        error_message='Connection timeout after 30 seconds',
        completed_at=timezone.now()
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
