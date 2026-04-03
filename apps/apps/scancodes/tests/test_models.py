"""
Scancodes App - Model Tests
Comprehensive tests for ScanCode and ScanLog models.

Tests cover:
- Instance creation with required fields
- __str__ representation
- Field validation (max_length, choices, unique constraints)
- Foreign key relationships
- Edge cases
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from apps.scancodes.models import ScanCode, ScanLog

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
def scanner_user(db):
    """Create a scanner user."""
    return User.objects.create_user(
        username='scanner',
        email='scanner@example.com',
        password='scanpass123',
        first_name='QR',
        last_name='Scanner'
    )


@pytest.fixture
def scan_code(db, user):
    """Create a test scan code."""
    return ScanCode.objects.create(
        code='ARDT-QR-001-2024',
        code_type=ScanCode.CodeType.QR,
        entity_type=ScanCode.EntityType.DRILL_BIT,
        entity_id=1,
        created_by=user
    )


@pytest.fixture
def external_scan_code(db, user):
    """Create an external scan code."""
    return ScanCode.objects.create(
        code='ARAMCO-EXT-12345',
        code_type=ScanCode.CodeType.BARCODE,
        entity_type=ScanCode.EntityType.EXTERNAL,
        is_external=True,
        external_source='ARAMCO',
        created_by=user
    )


@pytest.fixture
def scan_log(db, scan_code, scanner_user):
    """Create a test scan log."""
    return ScanLog.objects.create(
        scan_code=scan_code,
        raw_code='ARDT-QR-001-2024',
        purpose=ScanLog.Purpose.IDENTIFY,
        is_valid=True,
        scanned_by=scanner_user
    )


# =============================================================================
# SCAN CODE MODEL TESTS
# =============================================================================

class TestScanCodeModel:
    """Tests for the ScanCode model."""

    def test_create_scan_code(self, db, user):
        """Test creating a scan code."""
        scan_code = ScanCode.objects.create(
            code='TEST-QR-001',
            code_type=ScanCode.CodeType.QR,
            entity_type=ScanCode.EntityType.WORK_ORDER,
            entity_id=100,
            created_by=user
        )
        assert scan_code.pk is not None
        assert scan_code.code == 'TEST-QR-001'
        assert scan_code.is_active is True

    def test_scan_code_str(self, scan_code):
        """Test the __str__ method."""
        expected = 'ARDT-QR-001-2024 (DRILL_BIT)'
        assert str(scan_code) == expected

    def test_scan_code_unique_code(self, scan_code, user):
        """Test that code must be unique."""
        with pytest.raises(IntegrityError):
            ScanCode.objects.create(
                code='ARDT-QR-001-2024',  # Duplicate
                entity_type=ScanCode.EntityType.EQUIPMENT,
                created_by=user
            )

    def test_scan_code_type_choices(self, db, user):
        """Test all valid code type choices."""
        for code_type, type_name in ScanCode.CodeType.choices:
            scan_code = ScanCode.objects.create(
                code=f'TYPE-{code_type}',
                code_type=code_type,
                entity_type=ScanCode.EntityType.DOCUMENT,
                created_by=user
            )
            assert scan_code.code_type == code_type

    def test_scan_code_entity_type_choices(self, db, user):
        """Test all valid entity type choices."""
        for entity_type, type_name in ScanCode.EntityType.choices:
            scan_code = ScanCode.objects.create(
                code=f'ENTITY-{entity_type}',
                entity_type=entity_type,
                created_by=user
            )
            assert scan_code.entity_type == entity_type

    def test_external_scan_code(self, external_scan_code):
        """Test external scan code properties."""
        assert external_scan_code.is_external is True
        assert external_scan_code.external_source == 'ARAMCO'

    def test_scan_code_encoded_data(self, db, user):
        """Test scan code with encoded JSON data."""
        encoded_data = {
            'serial_number': 'SN-12345',
            'manufacturer': 'ARDT',
            'batch': 'B2024-001'
        }
        scan_code = ScanCode.objects.create(
            code='DATA-QR-001',
            entity_type=ScanCode.EntityType.DRILL_BIT,
            encoded_data=encoded_data,
            created_by=user
        )
        assert scan_code.encoded_data['serial_number'] == 'SN-12345'
        assert scan_code.encoded_data['manufacturer'] == 'ARDT'

    def test_scan_code_null_entity_id(self, db, user):
        """Test scan code without entity ID."""
        scan_code = ScanCode.objects.create(
            code='NO-ENTITY-001',
            entity_type=ScanCode.EntityType.EXTERNAL,
            entity_id=None,
            created_by=user
        )
        assert scan_code.entity_id is None

    def test_scan_code_timestamps(self, scan_code):
        """Test auto-generated timestamp."""
        assert scan_code.created_at is not None


# =============================================================================
# SCAN LOG MODEL TESTS
# =============================================================================

class TestScanLogModel:
    """Tests for the ScanLog model."""

    def test_create_scan_log(self, scan_code, scanner_user):
        """Test creating a scan log."""
        scan_log = ScanLog.objects.create(
            scan_code=scan_code,
            raw_code='ARDT-QR-001-2024',
            purpose=ScanLog.Purpose.VERIFY,
            scanned_by=scanner_user
        )
        assert scan_log.pk is not None
        assert scan_log.is_valid is True

    def test_scan_log_str(self, scan_log):
        """Test the __str__ method."""
        expected = f'ARDT-QR-001-2024 @ {scan_log.scanned_at}'
        assert str(scan_log) == expected

    def test_scan_log_purpose_choices(self, scan_code, scanner_user):
        """Test all valid purpose choices."""
        for purpose_code, purpose_name in ScanLog.Purpose.choices:
            scan_log = ScanLog.objects.create(
                scan_code=scan_code,
                raw_code=f'RAW-{purpose_code}',
                purpose=purpose_code,
                scanned_by=scanner_user
            )
            assert scan_log.purpose == purpose_code

    def test_scan_log_invalid_scan(self, scan_code, scanner_user):
        """Test invalid scan log entry."""
        scan_log = ScanLog.objects.create(
            scan_code=scan_code,
            raw_code='INVALID-QR',
            purpose=ScanLog.Purpose.IDENTIFY,
            is_valid=False,
            validation_message='QR code not recognized in system',
            scanned_by=scanner_user
        )
        assert scan_log.is_valid is False
        assert 'not recognized' in scan_log.validation_message

    def test_scan_log_with_location(self, scan_code, scanner_user):
        """Test scan log with GPS coordinates."""
        scan_log = ScanLog.objects.create(
            scan_code=scan_code,
            raw_code='LOC-QR-001',
            purpose=ScanLog.Purpose.CHECK_IN,
            latitude=Decimal('24.7136'),
            longitude=Decimal('46.6753'),
            scanned_by=scanner_user
        )
        assert scan_log.latitude == Decimal('24.7136')
        assert scan_log.longitude == Decimal('46.6753')

    def test_scan_log_device_info(self, scan_code, scanner_user):
        """Test scan log with device information."""
        scan_log = ScanLog.objects.create(
            scan_code=scan_code,
            raw_code='DEVICE-QR-001',
            purpose=ScanLog.Purpose.IDENTIFY,
            device_info='iPhone 15 Pro, iOS 17.2, ARDT FMS App v2.1',
            scanned_by=scanner_user
        )
        assert 'iPhone' in scan_log.device_info

    def test_scan_log_null_scan_code(self, scanner_user):
        """Test scan log for unrecognized code."""
        scan_log = ScanLog.objects.create(
            scan_code=None,
            raw_code='UNKNOWN-12345',
            purpose=ScanLog.Purpose.IDENTIFY,
            is_valid=False,
            validation_message='Code not found in system',
            scanned_by=scanner_user
        )
        assert scan_log.scan_code is None
        assert scan_log.raw_code == 'UNKNOWN-12345'

    def test_scan_log_ordering(self, scan_code, scanner_user):
        """Test scan log ordering by timestamp."""
        log1 = ScanLog.objects.create(
            scan_code=scan_code,
            raw_code='LOG-1',
            purpose=ScanLog.Purpose.IDENTIFY,
            scanned_by=scanner_user
        )
        log2 = ScanLog.objects.create(
            scan_code=scan_code,
            raw_code='LOG-2',
            purpose=ScanLog.Purpose.VERIFY,
            scanned_by=scanner_user
        )

        logs = list(ScanLog.objects.all())
        # Most recent first
        assert logs[0].pk == log2.pk

    def test_scan_log_with_work_order(self, scan_code, scanner_user, user):
        """Test scan log associated with work order."""
        from apps.workorders.models import WorkOrder

        work_order = WorkOrder.objects.create(
            wo_number='WO-SCAN-001',
            wo_type='MANUFACTURING',
            created_by=user
        )

        scan_log = ScanLog.objects.create(
            scan_code=scan_code,
            raw_code='WO-SCAN',
            purpose=ScanLog.Purpose.STEP_COMPLETE,
            work_order=work_order,
            scanned_by=scanner_user
        )
        assert scan_log.work_order == work_order


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestScanCodeEdgeCases:
    """Edge case tests for scancode models."""

    def test_long_scan_code(self, db, user):
        """Test scan code with maximum length."""
        long_code = 'X' * 200
        scan_code = ScanCode.objects.create(
            code=long_code,
            entity_type=ScanCode.EntityType.DOCUMENT,
            created_by=user
        )
        assert len(scan_code.code) == 200

    def test_special_characters_in_code(self, db, user):
        """Test scan code with special characters."""
        scan_code = ScanCode.objects.create(
            code='CODE-WITH_SPECIAL/CHARS:123',
            entity_type=ScanCode.EntityType.EQUIPMENT,
            created_by=user
        )
        assert '/' in scan_code.code
        assert ':' in scan_code.code

    def test_datamatrix_code_type(self, db, user):
        """Test Data Matrix code type."""
        scan_code = ScanCode.objects.create(
            code='DM-001-ABCD',
            code_type=ScanCode.CodeType.DATAMATRIX,
            entity_type=ScanCode.EntityType.INVENTORY_ITEM,
            created_by=user
        )
        assert scan_code.code_type == ScanCode.CodeType.DATAMATRIX

    def test_multiple_scans_same_code(self, scan_code, scanner_user):
        """Test multiple scan logs for same code."""
        for i in range(5):
            ScanLog.objects.create(
                scan_code=scan_code,
                raw_code=scan_code.code,
                purpose=ScanLog.Purpose.IDENTIFY,
                scanned_by=scanner_user
            )

        assert scan_code.scan_logs.count() == 5

    def test_scan_code_deactivation(self, scan_code):
        """Test deactivating a scan code."""
        scan_code.is_active = False
        scan_code.save()

        scan_code.refresh_from_db()
        assert scan_code.is_active is False

    def test_transfer_scan_purpose(self, scan_code, scanner_user):
        """Test transfer scan purpose."""
        scan_log = ScanLog.objects.create(
            scan_code=scan_code,
            raw_code=scan_code.code,
            purpose=ScanLog.Purpose.TRANSFER,
            scanned_by=scanner_user
        )
        assert scan_log.purpose == ScanLog.Purpose.TRANSFER
