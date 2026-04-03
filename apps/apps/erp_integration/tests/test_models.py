"""
ERP Integration App - Model Tests
Comprehensive tests for ERP integration models.
"""

import pytest
from datetime import datetime
from django.db import IntegrityError
from django.utils import timezone


# =============================================================================
# ERP MAPPING MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestERPMappingModel:
    """Tests for ERPMapping model."""

    def test_create_erp_mapping(self):
        """Test basic ERP mapping creation."""
        from apps.erp_integration.models import ERPMapping
        mapping = ERPMapping.objects.create(
            entity_type=ERPMapping.EntityType.CUSTOMER,
            ardt_id=1,
            erp_system='SAP',
            erp_id='SAP-001'
        )
        assert mapping.pk is not None
        assert mapping.entity_type == 'CUSTOMER'

    def test_str_representation(self, erp_mapping):
        """Test __str__ method."""
        expected = f"{erp_mapping.get_entity_type_display()}: {erp_mapping.ardt_id} → {erp_mapping.erp_id}"
        assert str(erp_mapping) == expected

    def test_entity_type_choices(self):
        """Test all entity type choices."""
        from apps.erp_integration.models import ERPMapping
        for choice in ERPMapping.EntityType.choices:
            mapping = ERPMapping.objects.create(
                entity_type=choice[0],
                ardt_id=100 + ERPMapping.EntityType.choices.index(choice),
                erp_system='TEST',
                erp_id=f'TEST-{choice[0]}'
            )
            assert mapping.entity_type == choice[0]

    def test_unique_together_constraint(self, erp_mapping):
        """Test unique_together constraint on entity_type, ardt_id, erp_system."""
        from apps.erp_integration.models import ERPMapping
        with pytest.raises(IntegrityError):
            ERPMapping.objects.create(
                entity_type=erp_mapping.entity_type,
                ardt_id=erp_mapping.ardt_id,
                erp_system=erp_mapping.erp_system,
                erp_id='DIFFERENT-ID'
            )

    def test_same_ardt_id_different_erp_systems_allowed(self, erp_mapping):
        """Test same ardt_id with different ERP systems is allowed."""
        from apps.erp_integration.models import ERPMapping
        mapping2 = ERPMapping.objects.create(
            entity_type=erp_mapping.entity_type,
            ardt_id=erp_mapping.ardt_id,
            erp_system='ORACLE',  # Different system
            erp_id='ORA-001'
        )
        assert mapping2.pk is not None

    def test_same_ardt_id_different_entity_types_allowed(self, erp_mapping):
        """Test same ardt_id with different entity types is allowed."""
        from apps.erp_integration.models import ERPMapping
        mapping2 = ERPMapping.objects.create(
            entity_type=ERPMapping.EntityType.ITEM,  # Different type
            ardt_id=erp_mapping.ardt_id,
            erp_system=erp_mapping.erp_system,
            erp_id='SAP-ITEM-001'
        )
        assert mapping2.pk is not None

    def test_default_is_active(self):
        """Test default is_active value."""
        from apps.erp_integration.models import ERPMapping
        mapping = ERPMapping.objects.create(
            entity_type=ERPMapping.EntityType.CUSTOMER,
            ardt_id=9999,
            erp_system='SAP',
            erp_id='DEFAULT-TEST'
        )
        assert mapping.is_active is True

    def test_last_synced_null_by_default(self):
        """Test last_synced is null by default."""
        from apps.erp_integration.models import ERPMapping
        mapping = ERPMapping.objects.create(
            entity_type=ERPMapping.EntityType.CUSTOMER,
            ardt_id=9998,
            erp_system='SAP',
            erp_id='SYNC-TEST'
        )
        assert mapping.last_synced is None

    def test_last_synced_can_be_set(self, erp_mapping):
        """Test last_synced can be set."""
        now = timezone.now()
        erp_mapping.last_synced = now
        erp_mapping.save()
        erp_mapping.refresh_from_db()
        assert erp_mapping.last_synced is not None

    def test_timestamps_auto_populated(self):
        """Test created_at and updated_at are auto-populated."""
        from apps.erp_integration.models import ERPMapping
        mapping = ERPMapping.objects.create(
            entity_type=ERPMapping.EntityType.CUSTOMER,
            ardt_id=9997,
            erp_system='SAP',
            erp_id='TIMESTAMP-TEST'
        )
        assert mapping.created_at is not None
        assert mapping.updated_at is not None

    def test_erp_system_max_length(self):
        """Test erp_system at max length (50 chars)."""
        from apps.erp_integration.models import ERPMapping
        max_system = 'S' * 50
        mapping = ERPMapping.objects.create(
            entity_type=ERPMapping.EntityType.CUSTOMER,
            ardt_id=9996,
            erp_system=max_system,
            erp_id='MAX-SYSTEM'
        )
        assert len(mapping.erp_system) == 50

    def test_erp_id_max_length(self):
        """Test erp_id at max length (100 chars)."""
        from apps.erp_integration.models import ERPMapping
        max_id = 'I' * 100
        mapping = ERPMapping.objects.create(
            entity_type=ERPMapping.EntityType.CUSTOMER,
            ardt_id=9995,
            erp_system='SAP',
            erp_id=max_id
        )
        assert len(mapping.erp_id) == 100


# =============================================================================
# ERP SYNC LOG MODEL TESTS
# =============================================================================

@pytest.mark.django_db
class TestERPSyncLogModel:
    """Tests for ERPSyncLog model."""

    def test_create_sync_log(self):
        """Test basic sync log creation."""
        from apps.erp_integration.models import ERPSyncLog
        log = ERPSyncLog.objects.create(
            erp_system='SAP',
            direction=ERPSyncLog.Direction.OUTBOUND,
            entity_type='CUSTOMER',
            entity_id=1
        )
        assert log.pk is not None

    def test_str_representation(self, erp_sync_log):
        """Test __str__ method."""
        expected = f"{erp_sync_log.entity_type} - {erp_sync_log.get_status_display()} at {erp_sync_log.started_at}"
        assert str(erp_sync_log) == expected

    def test_direction_choices(self):
        """Test all direction choices."""
        from apps.erp_integration.models import ERPSyncLog
        for choice in ERPSyncLog.Direction.choices:
            log = ERPSyncLog.objects.create(
                erp_system='TEST',
                direction=choice[0],
                entity_type='TEST'
            )
            assert log.direction == choice[0]

    def test_status_choices(self):
        """Test all status choices."""
        from apps.erp_integration.models import ERPSyncLog
        for choice in ERPSyncLog.Status.choices:
            log = ERPSyncLog.objects.create(
                erp_system='TEST',
                direction=ERPSyncLog.Direction.OUTBOUND,
                entity_type='TEST',
                status=choice[0]
            )
            assert log.status == choice[0]

    def test_default_status(self):
        """Test default status is PENDING."""
        from apps.erp_integration.models import ERPSyncLog
        log = ERPSyncLog.objects.create(
            erp_system='SAP',
            direction=ERPSyncLog.Direction.OUTBOUND,
            entity_type='CUSTOMER'
        )
        assert log.status == ERPSyncLog.Status.PENDING

    def test_entity_id_nullable(self):
        """Test entity_id can be null."""
        from apps.erp_integration.models import ERPSyncLog
        log = ERPSyncLog.objects.create(
            erp_system='SAP',
            direction=ERPSyncLog.Direction.OUTBOUND,
            entity_type='BATCH',
            entity_id=None
        )
        assert log.entity_id is None

    def test_request_payload_json(self, erp_sync_log):
        """Test request_payload is stored as JSON."""
        assert erp_sync_log.request_payload == {'customer_id': 1001, 'action': 'create'}

    def test_response_payload_json(self, erp_sync_log_success):
        """Test response_payload is stored as JSON."""
        assert erp_sync_log_success.response_payload == {'status': 'ok', 'erp_id': 'SAP-ITEM-001'}

    def test_error_message_on_failure(self, erp_sync_log_failed):
        """Test error_message is set on failure."""
        assert 'Connection timeout' in erp_sync_log_failed.error_message
        assert erp_sync_log_failed.status == 'FAILED'

    def test_completed_at_null_when_pending(self, erp_sync_log):
        """Test completed_at is null when status is pending."""
        assert erp_sync_log.completed_at is None

    def test_completed_at_set_on_completion(self, erp_sync_log_success):
        """Test completed_at is set when sync completes."""
        assert erp_sync_log_success.completed_at is not None

    def test_started_at_auto_populated(self):
        """Test started_at is auto-populated."""
        from apps.erp_integration.models import ERPSyncLog
        log = ERPSyncLog.objects.create(
            erp_system='SAP',
            direction=ERPSyncLog.Direction.OUTBOUND,
            entity_type='CUSTOMER'
        )
        assert log.started_at is not None

    def test_ordering_by_started_at_desc(self):
        """Test default ordering is by started_at descending."""
        from apps.erp_integration.models import ERPSyncLog
        log1 = ERPSyncLog.objects.create(
            erp_system='SAP',
            direction=ERPSyncLog.Direction.OUTBOUND,
            entity_type='FIRST'
        )
        log2 = ERPSyncLog.objects.create(
            erp_system='SAP',
            direction=ERPSyncLog.Direction.OUTBOUND,
            entity_type='SECOND'
        )
        logs = list(ERPSyncLog.objects.all())
        assert logs[0].entity_type == 'SECOND'  # Most recent first

    def test_complex_request_payload(self):
        """Test complex nested JSON in request_payload."""
        from apps.erp_integration.models import ERPSyncLog
        complex_payload = {
            'customer': {
                'id': 1001,
                'name': 'Test Customer',
                'contacts': [
                    {'name': 'John', 'email': 'john@test.com'},
                    {'name': 'Jane', 'email': 'jane@test.com'}
                ]
            },
            'action': 'create',
            'timestamp': '2024-01-15T10:30:00Z'
        }
        log = ERPSyncLog.objects.create(
            erp_system='SAP',
            direction=ERPSyncLog.Direction.OUTBOUND,
            entity_type='CUSTOMER',
            request_payload=complex_payload
        )
        log.refresh_from_db()
        assert log.request_payload['customer']['contacts'][0]['name'] == 'John'

    def test_empty_error_message(self, erp_sync_log_success):
        """Test error_message is empty on success."""
        assert erp_sync_log_success.error_message == ''

    def test_erp_system_max_length(self):
        """Test erp_system at max length (50 chars)."""
        from apps.erp_integration.models import ERPSyncLog
        max_system = 'E' * 50
        log = ERPSyncLog.objects.create(
            erp_system=max_system,
            direction=ERPSyncLog.Direction.OUTBOUND,
            entity_type='TEST'
        )
        assert len(log.erp_system) == 50

    def test_entity_type_max_length(self):
        """Test entity_type at max length (30 chars)."""
        from apps.erp_integration.models import ERPSyncLog
        max_type = 'T' * 30
        log = ERPSyncLog.objects.create(
            erp_system='SAP',
            direction=ERPSyncLog.Direction.OUTBOUND,
            entity_type=max_type
        )
        assert len(log.entity_type) == 30


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

@pytest.mark.django_db
class TestERPIntegrationScenarios:
    """Integration tests for ERP mapping and sync log scenarios."""

    def test_mapping_with_sync_logs(self):
        """Test creating mapping and associated sync logs."""
        from apps.erp_integration.models import ERPMapping, ERPSyncLog

        # Create mapping
        mapping = ERPMapping.objects.create(
            entity_type=ERPMapping.EntityType.CUSTOMER,
            ardt_id=5001,
            erp_system='SAP',
            erp_id='SAP-CUST-5001'
        )

        # Create initial sync log
        log1 = ERPSyncLog.objects.create(
            erp_system='SAP',
            direction=ERPSyncLog.Direction.OUTBOUND,
            entity_type='CUSTOMER',
            entity_id=5001,
            status=ERPSyncLog.Status.SUCCESS,
            request_payload={'action': 'create'},
            response_payload={'status': 'created'},
            completed_at=timezone.now()
        )

        # Update mapping sync time
        mapping.last_synced = log1.completed_at
        mapping.save()

        assert mapping.last_synced is not None

    def test_multiple_erp_systems_for_entity(self):
        """Test entity mapped to multiple ERP systems."""
        from apps.erp_integration.models import ERPMapping

        ardt_customer_id = 7001

        # SAP mapping
        sap_mapping = ERPMapping.objects.create(
            entity_type=ERPMapping.EntityType.CUSTOMER,
            ardt_id=ardt_customer_id,
            erp_system='SAP',
            erp_id='SAP-7001'
        )

        # Oracle mapping
        oracle_mapping = ERPMapping.objects.create(
            entity_type=ERPMapping.EntityType.CUSTOMER,
            ardt_id=ardt_customer_id,
            erp_system='ORACLE',
            erp_id='ORA-7001'
        )

        # Microsoft Dynamics mapping
        dynamics_mapping = ERPMapping.objects.create(
            entity_type=ERPMapping.EntityType.CUSTOMER,
            ardt_id=ardt_customer_id,
            erp_system='DYNAMICS',
            erp_id='DYN-7001'
        )

        # Verify all mappings exist
        mappings = ERPMapping.objects.filter(ardt_id=ardt_customer_id)
        assert mappings.count() == 3

    def test_sync_lifecycle_tracking(self):
        """Test tracking a sync through its lifecycle."""
        from apps.erp_integration.models import ERPSyncLog

        # 1. Create pending sync
        log = ERPSyncLog.objects.create(
            erp_system='SAP',
            direction=ERPSyncLog.Direction.OUTBOUND,
            entity_type='SALES_ORDER',
            entity_id=8001,
            status=ERPSyncLog.Status.PENDING,
            request_payload={'so_number': 'SO-8001'}
        )
        assert log.status == ERPSyncLog.Status.PENDING
        assert log.completed_at is None

        # 2. Mark as success
        log.status = ERPSyncLog.Status.SUCCESS
        log.response_payload = {'erp_so_number': 'SAP-SO-8001'}
        log.completed_at = timezone.now()
        log.save()

        log.refresh_from_db()
        assert log.status == ERPSyncLog.Status.SUCCESS
        assert log.completed_at is not None

    def test_batch_sync_scenario(self):
        """Test batch synchronization scenario."""
        from apps.erp_integration.models import ERPSyncLog

        # Batch sync without specific entity_id
        batch_log = ERPSyncLog.objects.create(
            erp_system='SAP',
            direction=ERPSyncLog.Direction.OUTBOUND,
            entity_type='CUSTOMER_BATCH',
            entity_id=None,
            status=ERPSyncLog.Status.SUCCESS,
            request_payload={'batch_size': 100, 'start_id': 1, 'end_id': 100},
            response_payload={'synced': 98, 'failed': 2},
            completed_at=timezone.now()
        )

        assert batch_log.entity_id is None
        assert batch_log.request_payload['batch_size'] == 100
        assert batch_log.response_payload['synced'] == 98

    def test_deactivate_mapping(self, erp_mapping):
        """Test deactivating an ERP mapping."""
        erp_mapping.is_active = False
        erp_mapping.save()
        erp_mapping.refresh_from_db()
        assert erp_mapping.is_active is False
