"""
Sprint 7 Smoke Tests: Compliance & Quality Management

Tests all 10 Sprint 7 models for basic CRUD operations
and auto-generated ID functionality.

Models tested:
- Week 1: ComplianceRequirement, QualityControl, NonConformance, AuditTrail
- Week 2: DocumentControl, TrainingRecord, Certification
- Week 3: ComplianceReport, QualityMetric, InspectionChecklist
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model

from apps.compliance.models import (
    ComplianceRequirement,
    QualityControl,
    NonConformance,
    AuditTrail,
    DocumentControl,
    TrainingRecord,
    Certification,
    ComplianceReport,
    QualityMetric,
    InspectionChecklist,
)

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def user(db):
    """Create test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='testpass123'
    )


@pytest.fixture
def compliance_requirement(db, user):
    """Create test compliance requirement"""
    return ComplianceRequirement.objects.create(
        requirement_code="ISO-9001-8.4.1",
        title="Control of Externally Provided Processes",
        requirement_type=ComplianceRequirement.RequirementType.ISO_STANDARD,
        source_document="ISO 9001:2015",
        description="Control of externally provided processes, products and services",
        effective_date=date.today(),
        created_by=user
    )


@pytest.fixture
def quality_control(db, user):
    """Create test quality control inspection"""
    return QualityControl.objects.create(
        inspection_type=QualityControl.InspectionType.INCOMING,
        inspection_date=date.today(),
        inspector=user,
        created_by=user
    )


@pytest.fixture
def non_conformance(db, user):
    """Create test non-conformance"""
    return NonConformance.objects.create(
        source=NonConformance.Source.QUALITY_INSPECTION,
        severity=NonConformance.Severity.MAJOR,
        description="Test non-conformance",
        defect_description="Test defect description",
        detected_date=date.today(),
        reported_by=user
    )


@pytest.fixture
def document_control(db, user):
    """Create test document control"""
    return DocumentControl.objects.create(
        document_number="DOC-001",
        title="Test Procedure",
        document_type=DocumentControl.DocumentType.PROCEDURE,
        version="1.0",
        revision_date=date.today(),
        prepared_by=user,
        file_path="/documents/test.pdf"
    )


@pytest.fixture
def training_record(db, user):
    """Create test training record"""
    return TrainingRecord.objects.create(
        employee=user,
        training_type=TrainingRecord.TrainingType.SAFETY,
        training_title="Safety Training 101",
        training_provider="Internal",
        start_date=date.today(),
        duration_hours=Decimal("8.00"),
        recorded_by=user
    )


@pytest.fixture
def certification(db, user):
    """Create test certification"""
    return Certification.objects.create(
        employee=user,
        certification_name="ISO 9001 Lead Auditor",
        certification_body="IRCA",
        issue_date=date.today(),
        expiry_date=date.today() + timedelta(days=365)
    )


@pytest.fixture
def compliance_report(db, user):
    """Create test compliance report"""
    return ComplianceReport.objects.create(
        report_type=ComplianceReport.ReportType.MONTHLY,
        title="Monthly Compliance Report",
        reporting_period_start=date.today() - timedelta(days=30),
        reporting_period_end=date.today(),
        prepared_by=user
    )


@pytest.fixture
def quality_metric(db, user):
    """Create test quality metric"""
    return QualityMetric.objects.create(
        metric_name="Defect Rate",
        metric_type=QualityMetric.MetricType.DEFECT_RATE,
        measurement_period=date.today(),
        measured_value=Decimal("2.5000"),
        target_value=Decimal("3.0000"),
        recorded_by=user
    )


@pytest.fixture
def inspection_checklist(db, user):
    """Create test inspection checklist"""
    return InspectionChecklist.objects.create(
        checklist_code="CHK-001",
        checklist_name="Incoming Inspection Checklist",
        inspection_type=InspectionChecklist.InspectionType.INCOMING,
        applicable_to="All incoming materials",
        checklist_items=[
            {"item": 1, "description": "Visual inspection", "required": True},
            {"item": 2, "description": "Dimension check", "required": True}
        ],
        version="1.0",
        created_by=user
    )


# =============================================================================
# WEEK 1: COMPLIANCE & QUALITY TESTS
# =============================================================================


class TestComplianceRequirement:
    """Test ComplianceRequirement model"""

    def test_create_compliance_requirement(self, compliance_requirement):
        """Test compliance requirement creation"""
        assert compliance_requirement.pk is not None
        assert compliance_requirement.requirement_code == "ISO-9001-8.4.1"

    def test_compliance_requirement_str(self, compliance_requirement):
        """Test string representation"""
        assert "ISO-9001-8.4.1" in str(compliance_requirement)

    def test_compliance_requirement_is_active(self, compliance_requirement):
        """Test is_active property"""
        assert compliance_requirement.is_active is True

    def test_compliance_requirement_is_compliant(self, compliance_requirement):
        """Test is_compliant property"""
        assert compliance_requirement.is_compliant is False
        compliance_requirement.compliance_status = ComplianceRequirement.ComplianceStatus.COMPLIANT
        compliance_requirement.save()
        assert compliance_requirement.is_compliant is True


class TestQualityControl:
    """Test QualityControl model"""

    def test_create_quality_control(self, quality_control):
        """Test quality control creation"""
        assert quality_control.pk is not None
        assert quality_control.result == QualityControl.Result.PENDING

    def test_quality_control_auto_number(self, quality_control):
        """Test auto-generated inspection number"""
        assert quality_control.inspection_number is not None
        assert "QC-" in quality_control.inspection_number

    def test_quality_control_str(self, quality_control):
        """Test string representation"""
        assert quality_control.inspection_number in str(quality_control)

    def test_quality_control_is_passed(self, quality_control):
        """Test is_passed property"""
        assert quality_control.is_passed is False
        quality_control.result = QualityControl.Result.PASS
        quality_control.save()
        assert quality_control.is_passed is True


class TestNonConformance:
    """Test NonConformance model"""

    def test_create_non_conformance(self, non_conformance):
        """Test non-conformance creation"""
        assert non_conformance.pk is not None
        assert non_conformance.status == NonConformance.Status.OPEN

    def test_non_conformance_auto_number(self, non_conformance):
        """Test auto-generated NCR number"""
        assert non_conformance.ncr_number is not None
        assert "NCR-" in non_conformance.ncr_number

    def test_non_conformance_str(self, non_conformance):
        """Test string representation"""
        assert non_conformance.ncr_number in str(non_conformance)

    def test_non_conformance_is_open(self, non_conformance):
        """Test is_open property"""
        assert non_conformance.is_open is True
        non_conformance.status = NonConformance.Status.CLOSED
        non_conformance.save()
        assert non_conformance.is_open is False


class TestAuditTrail:
    """Test AuditTrail model"""

    def test_create_audit_trail(self, db, user):
        """Test audit trail creation"""
        audit = AuditTrail.objects.create(
            action=AuditTrail.Action.CREATED,
            description="Test record created",
            model_name="TestModel",
            object_id=1,
            user=user
        )
        assert audit.pk is not None
        assert audit.action == AuditTrail.Action.CREATED

    def test_audit_trail_str(self, db, user):
        """Test string representation"""
        audit = AuditTrail.objects.create(
            action=AuditTrail.Action.UPDATED,
            description="Test update",
            model_name="TestModel",
            object_id=1,
            user=user
        )
        assert "UPDATED" in str(audit)
        assert "TestModel" in str(audit)


# =============================================================================
# WEEK 2: DOCUMENTATION & TRAINING TESTS
# =============================================================================


class TestDocumentControl:
    """Test DocumentControl model"""

    def test_create_document_control(self, document_control):
        """Test document control creation"""
        assert document_control.pk is not None
        assert document_control.status == DocumentControl.Status.DRAFT

    def test_document_control_str(self, document_control):
        """Test string representation"""
        assert "DOC-001" in str(document_control)
        assert "v1.0" in str(document_control)

    def test_document_control_is_current(self, document_control):
        """Test is_current property"""
        assert document_control.is_current is False
        document_control.status = DocumentControl.Status.APPROVED
        document_control.save()
        assert document_control.is_current is True


class TestTrainingRecord:
    """Test TrainingRecord model"""

    def test_create_training_record(self, training_record):
        """Test training record creation"""
        assert training_record.pk is not None
        assert training_record.status == TrainingRecord.Status.SCHEDULED

    def test_training_record_str(self, training_record):
        """Test string representation"""
        assert "Safety Training 101" in str(training_record)

    def test_training_record_is_expired(self, training_record):
        """Test is_expired property"""
        assert training_record.is_expired is False
        training_record.certificate_expiry_date = date.today() - timedelta(days=1)
        training_record.save()
        assert training_record.is_expired is True


class TestCertification:
    """Test Certification model"""

    def test_create_certification(self, certification):
        """Test certification creation"""
        assert certification.pk is not None
        assert certification.status == Certification.Status.CURRENT

    def test_certification_str(self, certification):
        """Test string representation"""
        assert "ISO 9001 Lead Auditor" in str(certification)

    def test_certification_is_expired(self, certification):
        """Test is_expired property"""
        assert certification.is_expired is False
        certification.expiry_date = date.today() - timedelta(days=1)
        certification.save()
        assert certification.is_expired is True

    def test_certification_days_until_expiry(self, certification):
        """Test days_until_expiry property"""
        days = certification.days_until_expiry
        assert days is not None
        assert days > 0


# =============================================================================
# WEEK 3: REPORTING & METRICS TESTS
# =============================================================================


class TestComplianceReport:
    """Test ComplianceReport model"""

    def test_create_compliance_report(self, compliance_report):
        """Test compliance report creation"""
        assert compliance_report.pk is not None
        assert compliance_report.status == ComplianceReport.Status.DRAFT

    def test_compliance_report_auto_number(self, compliance_report):
        """Test auto-generated report number"""
        assert compliance_report.report_number is not None
        assert "-" in compliance_report.report_number

    def test_compliance_report_str(self, compliance_report):
        """Test string representation"""
        assert compliance_report.report_number in str(compliance_report)


class TestQualityMetric:
    """Test QualityMetric model"""

    def test_create_quality_metric(self, quality_metric):
        """Test quality metric creation"""
        assert quality_metric.pk is not None
        assert quality_metric.measured_value == Decimal("2.5000")

    def test_quality_metric_str(self, quality_metric):
        """Test string representation"""
        assert "Defect Rate" in str(quality_metric)
        assert "2.5" in str(quality_metric)

    def test_quality_metric_meets_target(self, quality_metric):
        """Test meets_target property"""
        assert quality_metric.meets_target is False
        quality_metric.measured_value = Decimal("3.5000")
        quality_metric.save()
        assert quality_metric.meets_target is True


class TestInspectionChecklist:
    """Test InspectionChecklist model"""

    def test_create_inspection_checklist(self, inspection_checklist):
        """Test inspection checklist creation"""
        assert inspection_checklist.pk is not None
        assert inspection_checklist.is_active is True

    def test_inspection_checklist_str(self, inspection_checklist):
        """Test string representation"""
        assert "CHK-001" in str(inspection_checklist)

    def test_inspection_checklist_item_count(self, inspection_checklist):
        """Test item_count property"""
        assert inspection_checklist.item_count == 2
