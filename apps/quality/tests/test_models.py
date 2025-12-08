"""
Tests for Quality app models.
"""
import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.quality.models import Inspection, NCR

User = get_user_model()


class TestInspectionModel:
    """Tests for Inspection model."""

    def test_create_inspection(self, db, test_user, work_order):
        """Test creating an inspection."""
        inspection = Inspection.objects.create(
            inspection_number='INSP-TEST',
            inspection_type=Inspection.InspectionType.INCOMING,
            work_order=work_order,
            scheduled_date=date.today(),
            status=Inspection.Status.SCHEDULED,
            created_by=test_user
        )
        assert inspection.pk is not None
        assert inspection.inspection_number == 'INSP-TEST'

    def test_inspection_str(self, inspection):
        """Test inspection string representation."""
        assert 'INSP-001' in str(inspection)

    def test_inspection_type_choices(self, db, test_user, work_order):
        """Test inspection type choices."""
        for i, (insp_type, _) in enumerate(Inspection.InspectionType.choices):
            insp = Inspection.objects.create(
                inspection_number=f'INSP-TYPE-{i}',
                inspection_type=insp_type,
                work_order=work_order,
                status=Inspection.Status.SCHEDULED,
                created_by=test_user
            )
            assert insp.inspection_type == insp_type

    def test_inspection_status_choices(self, db, test_user, work_order):
        """Test inspection status choices."""
        for i, (status, _) in enumerate(Inspection.Status.choices):
            insp = Inspection.objects.create(
                inspection_number=f'INSP-STATUS-{i}',
                inspection_type=Inspection.InspectionType.IN_PROCESS,
                work_order=work_order,
                status=status,
                created_by=test_user
            )
            assert insp.status == status

    def test_inspection_pass_fail_counts(self, completed_inspection):
        """Test inspection pass/fail counts."""
        assert completed_inspection.pass_count == 10
        assert completed_inspection.fail_count == 0

    def test_inspection_with_inspector(self, completed_inspection, inspector_user):
        """Test inspection with inspector."""
        assert completed_inspection.inspected_by == inspector_user
        assert completed_inspection.inspected_at is not None

    def test_inspection_unique_number(self, db, inspection, test_user, work_order):
        """Test inspection number uniqueness."""
        with pytest.raises(Exception):
            Inspection.objects.create(
                inspection_number='INSP-001',
                inspection_type=Inspection.InspectionType.FINAL,
                work_order=work_order,
                status=Inspection.Status.SCHEDULED,
                created_by=test_user
            )


class TestNCRModel:
    """Tests for NCR model."""

    def test_create_ncr(self, db, test_user, work_order):
        """Test creating an NCR."""
        ncr = NCR.objects.create(
            ncr_number='NCR-TEST',
            work_order=work_order,
            title='Test NCR',
            description='Test description',
            severity=NCR.Severity.MAJOR,
            status=NCR.Status.OPEN,
            detected_at=timezone.now(),
            detected_by=test_user
        )
        assert ncr.pk is not None
        assert ncr.ncr_number == 'NCR-TEST'

    def test_ncr_severity_choices(self, db, test_user, work_order):
        """Test NCR severity choices."""
        for i, (severity, _) in enumerate(NCR.Severity.choices):
            ncr = NCR.objects.create(
                ncr_number=f'NCR-SEV-{i}',
                work_order=work_order,
                title=f'NCR {severity}',
                description='Test',
                severity=severity,
                status=NCR.Status.OPEN,
                detected_at=timezone.now(),
                detected_by=test_user
            )
            assert ncr.severity == severity

    def test_ncr_status_choices(self, db, test_user, work_order):
        """Test NCR status choices."""
        for i, (status, _) in enumerate(NCR.Status.choices):
            ncr = NCR.objects.create(
                ncr_number=f'NCR-STAT-{i}',
                work_order=work_order,
                title=f'NCR {status}',
                description='Test',
                severity=NCR.Severity.MINOR,
                status=status,
                detected_at=timezone.now(),
                detected_by=test_user
            )
            assert ncr.status == status

    def test_ncr_disposition_choices(self, db, test_user, work_order):
        """Test NCR disposition choices."""
        for i, (disp, _) in enumerate(NCR.Disposition.choices):
            ncr = NCR.objects.create(
                ncr_number=f'NCR-DISP-{i}',
                work_order=work_order,
                title=f'NCR {disp}',
                description='Test',
                severity=NCR.Severity.MINOR,
                status=NCR.Status.PENDING_DISPOSITION,
                detected_at=timezone.now(),
                detected_by=test_user,
                disposition=disp
            )
            assert ncr.disposition == disp

    def test_ncr_linked_to_inspection(self, ncr, inspection):
        """Test NCR linked to inspection."""
        assert ncr.inspection == inspection

    def test_ncr_investigation(self, ncr, test_user):
        """Test NCR investigation fields."""
        ncr.status = NCR.Status.INVESTIGATING
        ncr.root_cause = 'Material defect from supplier'
        ncr.investigated_by = test_user
        ncr.save()
        ncr.refresh_from_db()
        assert ncr.status == NCR.Status.INVESTIGATING
        assert ncr.root_cause != ''
        assert ncr.investigated_by == test_user

    def test_ncr_unique_number(self, db, ncr, test_user, work_order):
        """Test NCR number uniqueness."""
        with pytest.raises(Exception):
            NCR.objects.create(
                ncr_number='NCR-001',
                work_order=work_order,
                title='Duplicate',
                description='Test',
                severity=NCR.Severity.MINOR,
                status=NCR.Status.OPEN,
                detected_at=timezone.now(),
                detected_by=test_user
            )

    def test_ncr_closure(self, ncr, test_user):
        """Test NCR closure workflow."""
        ncr.status = NCR.Status.CLOSED
        ncr.disposition = NCR.Disposition.REWORK
        ncr.save()
        ncr.refresh_from_db()
        assert ncr.status == NCR.Status.CLOSED
