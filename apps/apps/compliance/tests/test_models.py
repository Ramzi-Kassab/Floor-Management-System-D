"""
Compliance App - Model Tests
Comprehensive tests for all 10 compliance models.

Tests cover:
- Instance creation with required fields
- __str__ representation
- Field validation (max_length, choices, unique constraints)
- Foreign key relationships and cascades
- Custom methods and properties
- Edge cases (blank fields, invalid data)
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.compliance.models import (
    ComplianceRequirement, QualityControl, NonConformance,
    AuditTrail, DocumentControl, TrainingRecord, Certification,
    ComplianceReport, QualityMetric, InspectionChecklist
)

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
def inspector(db):
    """Create an inspector user."""
    return User.objects.create_user(
        username='inspector',
        email='inspector@example.com',
        password='insppass123',
        first_name='Quality',
        last_name='Inspector'
    )


@pytest.fixture
def manager(db):
    """Create a manager user."""
    return User.objects.create_user(
        username='manager',
        email='manager@example.com',
        password='mgrpass123',
        first_name='Team',
        last_name='Manager'
    )


@pytest.fixture
def compliance_requirement(db, user):
    """Create a test compliance requirement."""
    return ComplianceRequirement.objects.create(
        requirement_code='ISO-9001-8.2.1',
        title='Customer Communication Requirements',
        requirement_type=ComplianceRequirement.RequirementType.ISO_STANDARD,
        source_document='ISO 9001:2015',
        description='Requirements for customer communication processes',
        effective_date=date.today(),
        created_by=user
    )


@pytest.fixture
def quality_control(db, inspector):
    """Create a test quality control inspection."""
    return QualityControl.objects.create(
        inspection_type=QualityControl.InspectionType.INCOMING,
        result=QualityControl.Result.PENDING,
        inspection_date=date.today(),
        inspector=inspector,
        created_by=inspector
    )


@pytest.fixture
def non_conformance(db, user):
    """Create a test non-conformance report."""
    return NonConformance.objects.create(
        source=NonConformance.Source.QUALITY_INSPECTION,
        severity=NonConformance.Severity.MAJOR,
        description='Test NCR description',
        defect_description='Dimensional out of tolerance',
        detected_date=date.today(),
        reported_by=user
    )


@pytest.fixture
def document_control(db, user):
    """Create a test controlled document."""
    return DocumentControl.objects.create(
        document_number='DOC-001',
        title='Test Procedure',
        document_type=DocumentControl.DocumentType.PROCEDURE,
        version='1.0',
        revision_date=date.today(),
        file_path='/documents/test.pdf',
        prepared_by=user
    )


@pytest.fixture
def training_record(db, user):
    """Create a test training record."""
    return TrainingRecord.objects.create(
        employee=user,
        training_type=TrainingRecord.TrainingType.SAFETY,
        training_title='Safety Orientation',
        training_provider='Internal',
        start_date=date.today(),
        duration_hours=Decimal('4.00')
    )


@pytest.fixture
def certification(db, user):
    """Create a test certification."""
    return Certification.objects.create(
        employee=user,
        certification_name='ISO Lead Auditor',
        certification_body='IRCA',
        issue_date=date.today() - timedelta(days=365),
        expiry_date=date.today() + timedelta(days=365)
    )


@pytest.fixture
def compliance_report(db, user):
    """Create a test compliance report."""
    return ComplianceReport.objects.create(
        report_type=ComplianceReport.ReportType.QUARTERLY,
        title='Q1 2024 Compliance Report',
        reporting_period_start=date(2024, 1, 1),
        reporting_period_end=date(2024, 3, 31),
        prepared_by=user
    )


@pytest.fixture
def quality_metric(db, user):
    """Create a test quality metric."""
    return QualityMetric.objects.create(
        metric_name='First Pass Yield',
        metric_type=QualityMetric.MetricType.FIRST_PASS_YIELD,
        measurement_period=date.today(),
        measured_value=Decimal('95.50'),
        unit_of_measure='%',
        recorded_by=user
    )


@pytest.fixture
def inspection_checklist(db, user):
    """Create a test inspection checklist."""
    return InspectionChecklist.objects.create(
        checklist_code='CHK-001',
        checklist_name='Incoming Inspection Checklist',
        inspection_type=InspectionChecklist.InspectionType.INCOMING,
        applicable_to='All incoming materials',
        checklist_items=[
            {'item': 'Visual inspection', 'required': True},
            {'item': 'Dimensional check', 'required': True},
            {'item': 'Documentation review', 'required': False}
        ],
        version='1.0',
        created_by=user
    )


# =============================================================================
# TEST: ComplianceRequirement Model
# =============================================================================

@pytest.mark.django_db
class TestComplianceRequirementModel:
    """Tests for ComplianceRequirement model."""

    def test_create_compliance_requirement(self, user):
        """Test creating a compliance requirement with required fields."""
        req = ComplianceRequirement.objects.create(
            requirement_code='API-SPEC-5CT',
            title='API Specification 5CT - Casing and Tubing',
            requirement_type=ComplianceRequirement.RequirementType.API_SPECIFICATION,
            source_document='API Spec 5CT',
            description='Requirements for casing and tubing',
            effective_date=date.today(),
            created_by=user
        )
        assert req.pk is not None
        assert req.requirement_code == 'API-SPEC-5CT'
        assert req.status == ComplianceRequirement.Status.ACTIVE
        assert req.compliance_status == ComplianceRequirement.ComplianceStatus.NOT_ASSESSED

    def test_str_representation(self, compliance_requirement):
        """Test __str__ returns meaningful string."""
        expected = f"{compliance_requirement.requirement_code} - {compliance_requirement.title}"
        assert str(compliance_requirement) == expected

    def test_requirement_code_unique(self, user, compliance_requirement):
        """Test requirement_code must be unique."""
        with pytest.raises(IntegrityError):
            ComplianceRequirement.objects.create(
                requirement_code=compliance_requirement.requirement_code,
                title='Duplicate Code Test',
                requirement_type=ComplianceRequirement.RequirementType.ISO_STANDARD,
                source_document='Test Doc',
                description='Test',
                effective_date=date.today(),
                created_by=user
            )

    def test_requirement_type_choices(self, compliance_requirement):
        """Test requirement_type accepts valid choices."""
        for choice, _ in ComplianceRequirement.RequirementType.choices:
            compliance_requirement.requirement_type = choice
            compliance_requirement.full_clean()  # Should not raise

    def test_invalid_requirement_type(self, compliance_requirement):
        """Test invalid requirement_type raises error."""
        compliance_requirement.requirement_type = 'INVALID_TYPE'
        with pytest.raises(ValidationError):
            compliance_requirement.full_clean()

    def test_status_choices(self, compliance_requirement):
        """Test status accepts valid choices."""
        for choice, _ in ComplianceRequirement.Status.choices:
            compliance_requirement.status = choice
            compliance_requirement.full_clean()

    def test_compliance_status_choices(self, compliance_requirement):
        """Test compliance_status accepts valid choices."""
        for choice, _ in ComplianceRequirement.ComplianceStatus.choices:
            compliance_requirement.compliance_status = choice
            compliance_requirement.full_clean()

    def test_risk_level_choices(self, compliance_requirement):
        """Test risk_level accepts valid choices."""
        for choice in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            compliance_requirement.risk_level = choice
            compliance_requirement.full_clean()

    def test_is_active_property_active_status(self, compliance_requirement):
        """Test is_active returns True for active status with past effective date."""
        compliance_requirement.status = ComplianceRequirement.Status.ACTIVE
        compliance_requirement.effective_date = date.today() - timedelta(days=1)
        compliance_requirement.save()
        assert compliance_requirement.is_active is True

    def test_is_active_property_inactive_status(self, compliance_requirement):
        """Test is_active returns False for inactive status."""
        compliance_requirement.status = ComplianceRequirement.Status.INACTIVE
        compliance_requirement.save()
        assert compliance_requirement.is_active is False

    def test_is_active_property_future_effective_date(self, compliance_requirement):
        """Test is_active returns False for future effective date."""
        compliance_requirement.effective_date = date.today() + timedelta(days=30)
        compliance_requirement.save()
        assert compliance_requirement.is_active is False

    def test_is_compliant_property_true(self, compliance_requirement):
        """Test is_compliant returns True when status is COMPLIANT."""
        compliance_requirement.compliance_status = ComplianceRequirement.ComplianceStatus.COMPLIANT
        compliance_requirement.save()
        assert compliance_requirement.is_compliant is True

    def test_is_compliant_property_false(self, compliance_requirement):
        """Test is_compliant returns False when status is not COMPLIANT."""
        compliance_requirement.compliance_status = ComplianceRequirement.ComplianceStatus.NON_COMPLIANT
        compliance_requirement.save()
        assert compliance_requirement.is_compliant is False

    def test_self_referential_supersedes(self, user, compliance_requirement):
        """Test supersedes FK to self works."""
        new_req = ComplianceRequirement.objects.create(
            requirement_code='ISO-9001-8.2.1-REV2',
            title='Revised Customer Communication Requirements',
            requirement_type=ComplianceRequirement.RequirementType.ISO_STANDARD,
            source_document='ISO 9001:2015',
            description='Revised requirements',
            effective_date=date.today(),
            supersedes=compliance_requirement,
            created_by=user
        )
        assert new_req.supersedes == compliance_requirement
        assert compliance_requirement.superseded_by_requirements.first() == new_req

    def test_related_requirements_m2m(self, user, compliance_requirement):
        """Test related_requirements many-to-many field."""
        related_req = ComplianceRequirement.objects.create(
            requirement_code='ISO-9001-8.2.2',
            title='Related Requirement',
            requirement_type=ComplianceRequirement.RequirementType.ISO_STANDARD,
            source_document='ISO 9001:2015',
            description='Related requirement',
            effective_date=date.today(),
            created_by=user
        )
        compliance_requirement.related_requirements.add(related_req)
        assert related_req in compliance_requirement.related_requirements.all()
        # Symmetric relationship
        assert compliance_requirement in related_req.related_requirements.all()

    def test_responsible_person_set_null_on_delete(self, user, compliance_requirement):
        """Test responsible_person is set to NULL when user is deleted."""
        compliance_requirement.responsible_person = user
        compliance_requirement.save()
        user_id = user.id
        user.delete()
        compliance_requirement.refresh_from_db()
        assert compliance_requirement.responsible_person is None

    def test_blank_optional_fields(self, user):
        """Test optional fields accept blank values."""
        req = ComplianceRequirement.objects.create(
            requirement_code='TEST-BLANK',
            title='Test Blank Fields',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test description',
            effective_date=date.today(),
            clause_number='',
            version='',
            issuing_authority='',
            applicable_scope='',
            created_by=user
        )
        req.full_clean()  # Should not raise


# =============================================================================
# TEST: QualityControl Model
# =============================================================================

@pytest.mark.django_db
class TestQualityControlModel:
    """Tests for QualityControl model."""

    def test_create_quality_control(self, inspector):
        """Test creating a quality control inspection."""
        qc = QualityControl.objects.create(
            inspection_type=QualityControl.InspectionType.FINAL,
            result=QualityControl.Result.PASS,
            inspection_date=date.today(),
            inspector=inspector,
            findings='All checks passed',
            created_by=inspector
        )
        assert qc.pk is not None
        assert qc.inspection_number.startswith('QC-')
        assert qc.result == QualityControl.Result.PASS

    def test_str_representation(self, quality_control):
        """Test __str__ returns meaningful string."""
        result = str(quality_control)
        assert quality_control.inspection_number in result
        assert quality_control.get_inspection_type_display() in result

    def test_auto_generate_inspection_number(self, inspector):
        """Test inspection number is auto-generated."""
        qc = QualityControl.objects.create(
            inspection_type=QualityControl.InspectionType.INCOMING,
            inspection_date=date.today(),
            inspector=inspector
        )
        assert qc.inspection_number is not None
        year = timezone.now().year
        assert f'QC-{year}-' in qc.inspection_number

    def test_inspection_number_unique(self, inspector):
        """Test inspection_number must be unique."""
        qc1 = QualityControl.objects.create(
            inspection_number='QC-UNIQUE-001',
            inspection_type=QualityControl.InspectionType.INCOMING,
            inspection_date=date.today(),
            inspector=inspector
        )
        with pytest.raises(IntegrityError):
            QualityControl.objects.create(
                inspection_number='QC-UNIQUE-001',
                inspection_type=QualityControl.InspectionType.FINAL,
                inspection_date=date.today(),
                inspector=inspector
            )

    def test_inspection_type_choices(self, quality_control):
        """Test inspection_type accepts valid choices."""
        for choice, _ in QualityControl.InspectionType.choices:
            quality_control.inspection_type = choice
            quality_control.full_clean()

    def test_result_choices(self, quality_control):
        """Test result accepts valid choices."""
        for choice, _ in QualityControl.Result.choices:
            quality_control.result = choice
            quality_control.full_clean()

    def test_is_passed_property_pass(self, quality_control):
        """Test is_passed returns True for PASS result."""
        quality_control.result = QualityControl.Result.PASS
        assert quality_control.is_passed is True

    def test_is_passed_property_conditional_pass(self, quality_control):
        """Test is_passed returns True for CONDITIONAL_PASS result."""
        quality_control.result = QualityControl.Result.CONDITIONAL_PASS
        assert quality_control.is_passed is True

    def test_is_passed_property_waived(self, quality_control):
        """Test is_passed returns True for WAIVED result."""
        quality_control.result = QualityControl.Result.WAIVED
        assert quality_control.is_passed is True

    def test_is_passed_property_fail(self, quality_control):
        """Test is_passed returns False for FAIL result."""
        quality_control.result = QualityControl.Result.FAIL
        assert quality_control.is_passed is False

    def test_is_passed_property_pending(self, quality_control):
        """Test is_passed returns False for PENDING result."""
        quality_control.result = QualityControl.Result.PENDING
        assert quality_control.is_passed is False

    def test_inspector_protect_on_delete(self, inspector, quality_control):
        """Test inspector cannot be deleted if referenced."""
        with pytest.raises(Exception):  # ProtectedError
            inspector.delete()

    def test_measurements_json_field(self, quality_control):
        """Test measurements JSONField accepts valid JSON."""
        quality_control.measurements = {
            'diameter': 25.4,
            'length': 100.0,
            'tolerance': 0.05
        }
        quality_control.save()
        quality_control.refresh_from_db()
        assert quality_control.measurements['diameter'] == 25.4

    def test_compliance_requirement_fk(self, quality_control, compliance_requirement):
        """Test foreign key to ComplianceRequirement."""
        quality_control.compliance_requirement = compliance_requirement
        quality_control.save()
        assert quality_control.compliance_requirement == compliance_requirement
        assert quality_control in compliance_requirement.quality_controls.all()


# =============================================================================
# TEST: NonConformance Model
# =============================================================================

@pytest.mark.django_db
class TestNonConformanceModel:
    """Tests for NonConformance model."""

    def test_create_non_conformance(self, user):
        """Test creating a non-conformance report."""
        ncr = NonConformance.objects.create(
            source=NonConformance.Source.QUALITY_INSPECTION,
            severity=NonConformance.Severity.CRITICAL,
            description='Critical NCR',
            defect_description='Major dimensional deviation',
            detected_date=date.today(),
            reported_by=user
        )
        assert ncr.pk is not None
        assert ncr.ncr_number.startswith('NCR-')
        assert ncr.status == NonConformance.Status.OPEN

    def test_str_representation(self, non_conformance):
        """Test __str__ returns meaningful string."""
        result = str(non_conformance)
        assert non_conformance.ncr_number in result
        assert non_conformance.get_severity_display() in result

    def test_auto_generate_ncr_number(self, user):
        """Test NCR number is auto-generated."""
        ncr = NonConformance.objects.create(
            source=NonConformance.Source.CUSTOMER_COMPLAINT,
            severity=NonConformance.Severity.MINOR,
            description='Test NCR',
            defect_description='Test defect',
            detected_date=date.today(),
            reported_by=user
        )
        year = timezone.now().year
        assert f'NCR-{year}-' in ncr.ncr_number

    def test_ncr_number_unique(self, user):
        """Test ncr_number must be unique."""
        ncr1 = NonConformance.objects.create(
            ncr_number='NCR-UNIQUE-001',
            source=NonConformance.Source.INTERNAL_AUDIT,
            severity=NonConformance.Severity.MAJOR,
            description='NCR 1',
            defect_description='Defect 1',
            detected_date=date.today(),
            reported_by=user
        )
        with pytest.raises(IntegrityError):
            NonConformance.objects.create(
                ncr_number='NCR-UNIQUE-001',
                source=NonConformance.Source.SUPPLIER_ISSUE,
                severity=NonConformance.Severity.MINOR,
                description='NCR 2',
                defect_description='Defect 2',
                detected_date=date.today(),
                reported_by=user
            )

    def test_source_choices(self, non_conformance):
        """Test source accepts valid choices."""
        for choice, _ in NonConformance.Source.choices:
            non_conformance.source = choice
            non_conformance.full_clean()

    def test_severity_choices(self, non_conformance):
        """Test severity accepts valid choices."""
        for choice, _ in NonConformance.Severity.choices:
            non_conformance.severity = choice
            non_conformance.full_clean()

    def test_status_choices(self, non_conformance):
        """Test status accepts valid choices."""
        for choice, _ in NonConformance.Status.choices:
            non_conformance.status = choice
            non_conformance.full_clean()

    def test_is_open_property_open_status(self, non_conformance):
        """Test is_open returns True for OPEN status."""
        non_conformance.status = NonConformance.Status.OPEN
        assert non_conformance.is_open is True

    def test_is_open_property_investigating(self, non_conformance):
        """Test is_open returns True for INVESTIGATING status."""
        non_conformance.status = NonConformance.Status.INVESTIGATING
        assert non_conformance.is_open is True

    def test_is_open_property_closed(self, non_conformance):
        """Test is_open returns False for CLOSED status."""
        non_conformance.status = NonConformance.Status.CLOSED
        assert non_conformance.is_open is False

    def test_is_open_property_rejected(self, non_conformance):
        """Test is_open returns False for REJECTED status."""
        non_conformance.status = NonConformance.Status.REJECTED
        assert non_conformance.is_open is False

    def test_reported_by_protect_on_delete(self, user, non_conformance):
        """Test reported_by cannot be deleted if referenced."""
        with pytest.raises(Exception):  # ProtectedError
            user.delete()

    def test_assigned_to_set_null_on_delete(self, user, manager, non_conformance):
        """Test assigned_to is set to NULL when user is deleted."""
        non_conformance.assigned_to = manager
        non_conformance.save()
        manager.delete()
        non_conformance.refresh_from_db()
        assert non_conformance.assigned_to is None


# =============================================================================
# TEST: AuditTrail Model
# =============================================================================

@pytest.mark.django_db
class TestAuditTrailModel:
    """Tests for AuditTrail model."""

    def test_create_audit_trail(self, user):
        """Test creating an audit trail entry."""
        audit = AuditTrail.objects.create(
            action=AuditTrail.Action.CREATED,
            description='Created new compliance requirement',
            model_name='ComplianceRequirement',
            object_id=1,
            object_repr='ISO-9001-8.2.1 - Customer Communication',
            user=user
        )
        assert audit.pk is not None
        assert audit.timestamp is not None

    def test_str_representation(self, user):
        """Test __str__ returns meaningful string."""
        audit = AuditTrail.objects.create(
            action=AuditTrail.Action.UPDATED,
            description='Updated document',
            model_name='DocumentControl',
            object_id=5,
            user=user
        )
        result = str(audit)
        assert str(audit.user) in result or user.username in result
        assert 'UPDATED' in result or audit.get_action_display() in result

    def test_action_choices(self, user):
        """Test action accepts valid choices."""
        for choice, _ in AuditTrail.Action.choices:
            audit = AuditTrail(
                action=choice,
                description='Test',
                model_name='Test',
                object_id=1,
                user=user
            )
            audit.full_clean()

    def test_changes_json_field(self, user):
        """Test changes JSONField stores data correctly."""
        audit = AuditTrail.objects.create(
            action=AuditTrail.Action.UPDATED,
            description='Updated status',
            model_name='NonConformance',
            object_id=10,
            user=user,
            changes={
                'old': {'status': 'OPEN'},
                'new': {'status': 'CLOSED'}
            }
        )
        audit.refresh_from_db()
        assert audit.changes['old']['status'] == 'OPEN'
        assert audit.changes['new']['status'] == 'CLOSED'

    def test_ip_address_field(self, user):
        """Test ip_address GenericIPAddressField."""
        # IPv4
        audit_v4 = AuditTrail.objects.create(
            action=AuditTrail.Action.LOGIN,
            description='User login',
            model_name='User',
            object_id=1,
            user=user,
            ip_address='192.168.1.100'
        )
        assert audit_v4.ip_address == '192.168.1.100'

        # IPv6
        audit_v6 = AuditTrail.objects.create(
            action=AuditTrail.Action.LOGIN,
            description='User login',
            model_name='User',
            object_id=1,
            user=user,
            ip_address='2001:db8::1'
        )
        assert audit_v6.ip_address == '2001:db8::1'

    def test_timestamp_auto_now_add(self, user):
        """Test timestamp is automatically set on creation."""
        before = timezone.now()
        audit = AuditTrail.objects.create(
            action=AuditTrail.Action.CREATED,
            description='Test',
            model_name='Test',
            object_id=1,
            user=user
        )
        after = timezone.now()
        assert before <= audit.timestamp <= after

    def test_user_set_null_on_delete(self, user):
        """Test user is set to NULL when user is deleted."""
        audit = AuditTrail.objects.create(
            action=AuditTrail.Action.CREATED,
            description='Test',
            model_name='Test',
            object_id=1,
            user=user
        )
        user.delete()
        audit.refresh_from_db()
        assert audit.user is None


# =============================================================================
# TEST: DocumentControl Model
# =============================================================================

@pytest.mark.django_db
class TestDocumentControlModel:
    """Tests for DocumentControl model."""

    def test_create_document_control(self, user):
        """Test creating a controlled document."""
        doc = DocumentControl.objects.create(
            document_number='PROC-QMS-001',
            title='Quality Management System Procedure',
            document_type=DocumentControl.DocumentType.PROCEDURE,
            version='1.0',
            revision_date=date.today(),
            file_path='/documents/qms/proc-001.pdf',
            prepared_by=user
        )
        assert doc.pk is not None
        assert doc.status == DocumentControl.Status.DRAFT

    def test_str_representation(self, document_control):
        """Test __str__ returns meaningful string."""
        result = str(document_control)
        assert document_control.document_number in result
        assert document_control.version in result
        assert document_control.title in result

    def test_unique_together_document_version(self, user, document_control):
        """Test document_number and version must be unique together."""
        with pytest.raises(IntegrityError):
            DocumentControl.objects.create(
                document_number=document_control.document_number,
                title='Duplicate',
                document_type=DocumentControl.DocumentType.PROCEDURE,
                version=document_control.version,
                revision_date=date.today(),
                file_path='/duplicate.pdf',
                prepared_by=user
            )

    def test_same_document_different_versions(self, user, document_control):
        """Test same document_number with different versions is allowed."""
        doc_v2 = DocumentControl.objects.create(
            document_number=document_control.document_number,
            title='Test Procedure v2',
            document_type=DocumentControl.DocumentType.PROCEDURE,
            version='2.0',
            revision_date=date.today(),
            file_path='/documents/test-v2.pdf',
            prepared_by=user,
            supersedes=document_control
        )
        assert doc_v2.pk is not None
        assert doc_v2.supersedes == document_control

    def test_document_type_choices(self, document_control):
        """Test document_type accepts valid choices."""
        for choice, _ in DocumentControl.DocumentType.choices:
            document_control.document_type = choice
            document_control.full_clean()

    def test_status_choices(self, document_control):
        """Test status accepts valid choices."""
        for choice, _ in DocumentControl.Status.choices:
            document_control.status = choice
            document_control.full_clean()

    def test_is_current_property_approved(self, document_control):
        """Test is_current returns True for APPROVED status."""
        document_control.status = DocumentControl.Status.APPROVED
        assert document_control.is_current is True

    def test_is_current_property_draft(self, document_control):
        """Test is_current returns False for DRAFT status."""
        document_control.status = DocumentControl.Status.DRAFT
        assert document_control.is_current is False

    def test_is_current_property_obsolete(self, document_control):
        """Test is_current returns False for OBSOLETE status."""
        document_control.status = DocumentControl.Status.OBSOLETE
        assert document_control.is_current is False

    def test_compliance_requirements_m2m(self, document_control, compliance_requirement):
        """Test many-to-many relationship with compliance requirements."""
        document_control.compliance_requirements.add(compliance_requirement)
        assert compliance_requirement in document_control.compliance_requirements.all()
        assert document_control in compliance_requirement.documents.all()

    def test_self_referential_supersedes(self, user, document_control):
        """Test supersedes FK to self works."""
        doc_v2 = DocumentControl.objects.create(
            document_number='DOC-002',
            title='New Document',
            document_type=DocumentControl.DocumentType.PROCEDURE,
            version='1.0',
            revision_date=date.today(),
            file_path='/new.pdf',
            prepared_by=user,
            supersedes=document_control
        )
        assert doc_v2.supersedes == document_control
        assert doc_v2 in document_control.superseded_by_documents.all()


# =============================================================================
# TEST: TrainingRecord Model
# =============================================================================

@pytest.mark.django_db
class TestTrainingRecordModel:
    """Tests for TrainingRecord model."""

    def test_create_training_record(self, user):
        """Test creating a training record."""
        training = TrainingRecord.objects.create(
            employee=user,
            training_type=TrainingRecord.TrainingType.TECHNICAL,
            training_title='Advanced Quality Techniques',
            training_provider='External Training Co',
            start_date=date.today(),
            duration_hours=Decimal('16.00')
        )
        assert training.pk is not None
        assert training.status == TrainingRecord.Status.SCHEDULED

    def test_str_representation(self, training_record):
        """Test __str__ returns meaningful string."""
        result = str(training_record)
        assert str(training_record.employee) in result or training_record.employee.username in result
        assert training_record.training_title in result

    def test_training_type_choices(self, training_record):
        """Test training_type accepts valid choices."""
        for choice, _ in TrainingRecord.TrainingType.choices:
            training_record.training_type = choice
            training_record.full_clean()

    def test_status_choices(self, training_record):
        """Test status accepts valid choices."""
        for choice, _ in TrainingRecord.Status.choices:
            training_record.status = choice
            training_record.full_clean()

    def test_is_expired_property_no_expiry(self, training_record):
        """Test is_expired returns False when no expiry date."""
        training_record.certificate_expiry_date = None
        assert training_record.is_expired is False

    def test_is_expired_property_future_expiry(self, training_record):
        """Test is_expired returns False for future expiry date."""
        training_record.certificate_expiry_date = date.today() + timedelta(days=365)
        training_record.save()
        assert training_record.is_expired is False

    def test_is_expired_property_past_expiry(self, training_record):
        """Test is_expired returns True for past expiry date."""
        training_record.certificate_expiry_date = date.today() - timedelta(days=1)
        training_record.save()
        assert training_record.is_expired is True

    def test_employee_protect_on_delete(self, user, training_record):
        """Test employee cannot be deleted if training record exists."""
        with pytest.raises(Exception):  # ProtectedError
            user.delete()

    def test_duration_hours_decimal(self, training_record):
        """Test duration_hours accepts decimal values."""
        training_record.duration_hours = Decimal('7.50')
        training_record.save()
        training_record.refresh_from_db()
        assert training_record.duration_hours == Decimal('7.50')

    def test_score_decimal(self, training_record):
        """Test score accepts decimal values."""
        training_record.score = Decimal('95.75')
        training_record.save()
        training_record.refresh_from_db()
        assert training_record.score == Decimal('95.75')


# =============================================================================
# TEST: Certification Model
# =============================================================================

@pytest.mark.django_db
class TestCertificationModel:
    """Tests for Certification model."""

    def test_create_certification(self, user):
        """Test creating a certification."""
        cert = Certification.objects.create(
            employee=user,
            certification_name='AWS Certified Solutions Architect',
            certification_body='Amazon Web Services',
            issue_date=date.today()
        )
        assert cert.pk is not None
        assert cert.status == Certification.Status.CURRENT

    def test_str_representation(self, certification):
        """Test __str__ returns meaningful string."""
        result = str(certification)
        assert str(certification.employee) in result or certification.employee.username in result
        assert certification.certification_name in result

    def test_status_choices(self, certification):
        """Test status accepts valid choices."""
        for choice, _ in Certification.Status.choices:
            certification.status = choice
            certification.full_clean()

    def test_is_expired_property_no_expiry(self, certification):
        """Test is_expired returns False when no expiry date."""
        certification.expiry_date = None
        certification.save()
        assert certification.is_expired is False

    def test_is_expired_property_future_expiry(self, certification):
        """Test is_expired returns False for future expiry date."""
        certification.expiry_date = date.today() + timedelta(days=30)
        certification.save()
        assert certification.is_expired is False

    def test_is_expired_property_past_expiry(self, certification):
        """Test is_expired returns True for past expiry date."""
        certification.expiry_date = date.today() - timedelta(days=1)
        certification.save()
        assert certification.is_expired is True

    def test_days_until_expiry_property(self, certification):
        """Test days_until_expiry returns correct value."""
        certification.expiry_date = date.today() + timedelta(days=30)
        certification.save()
        assert certification.days_until_expiry == 30

    def test_days_until_expiry_property_no_expiry(self, certification):
        """Test days_until_expiry returns None when no expiry date."""
        certification.expiry_date = None
        certification.save()
        assert certification.days_until_expiry is None

    def test_days_until_expiry_property_negative(self, certification):
        """Test days_until_expiry returns negative for expired cert."""
        certification.expiry_date = date.today() - timedelta(days=10)
        certification.save()
        assert certification.days_until_expiry == -10

    def test_employee_protect_on_delete(self, user, certification):
        """Test employee cannot be deleted if certification exists."""
        with pytest.raises(Exception):  # ProtectedError
            user.delete()

    def test_verified_by_set_null_on_delete(self, certification, manager):
        """Test verified_by is set to NULL when user is deleted."""
        certification.verified_by = manager
        certification.verified = True
        certification.verified_date = date.today()
        certification.save()
        manager.delete()
        certification.refresh_from_db()
        assert certification.verified_by is None


# =============================================================================
# TEST: ComplianceReport Model
# =============================================================================

@pytest.mark.django_db
class TestComplianceReportModel:
    """Tests for ComplianceReport model."""

    def test_create_compliance_report(self, user):
        """Test creating a compliance report."""
        report = ComplianceReport.objects.create(
            report_type=ComplianceReport.ReportType.ANNUAL,
            title='2024 Annual Compliance Report',
            reporting_period_start=date(2024, 1, 1),
            reporting_period_end=date(2024, 12, 31),
            prepared_by=user
        )
        assert report.pk is not None
        assert report.report_number.startswith('ANN-')
        assert report.status == ComplianceReport.Status.DRAFT

    def test_str_representation(self, compliance_report):
        """Test __str__ returns meaningful string."""
        result = str(compliance_report)
        assert compliance_report.report_number in result
        assert compliance_report.title in result

    def test_auto_generate_report_number(self, user):
        """Test report number is auto-generated with type prefix."""
        quarterly = ComplianceReport.objects.create(
            report_type=ComplianceReport.ReportType.QUARTERLY,
            title='Q2 Report',
            reporting_period_start=date(2024, 4, 1),
            reporting_period_end=date(2024, 6, 30),
            prepared_by=user
        )
        assert 'QUA-' in quarterly.report_number

        monthly = ComplianceReport.objects.create(
            report_type=ComplianceReport.ReportType.MONTHLY,
            title='May Report',
            reporting_period_start=date(2024, 5, 1),
            reporting_period_end=date(2024, 5, 31),
            prepared_by=user
        )
        assert 'MON-' in monthly.report_number

    def test_report_number_unique(self, user):
        """Test report_number must be unique."""
        report1 = ComplianceReport.objects.create(
            report_number='RPT-UNIQUE-001',
            report_type=ComplianceReport.ReportType.AD_HOC,
            title='Report 1',
            reporting_period_start=date(2024, 1, 1),
            reporting_period_end=date(2024, 1, 31),
            prepared_by=user
        )
        with pytest.raises(IntegrityError):
            ComplianceReport.objects.create(
                report_number='RPT-UNIQUE-001',
                report_type=ComplianceReport.ReportType.AD_HOC,
                title='Report 2',
                reporting_period_start=date(2024, 2, 1),
                reporting_period_end=date(2024, 2, 28),
                prepared_by=user
            )

    def test_report_type_choices(self, compliance_report):
        """Test report_type accepts valid choices."""
        for choice, _ in ComplianceReport.ReportType.choices:
            compliance_report.report_type = choice
            compliance_report.full_clean()

    def test_status_choices(self, compliance_report):
        """Test status accepts valid choices."""
        for choice, _ in ComplianceReport.Status.choices:
            compliance_report.status = choice
            compliance_report.full_clean()

    def test_compliance_requirements_m2m(self, compliance_report, compliance_requirement):
        """Test many-to-many relationship with compliance requirements."""
        compliance_report.compliance_requirements.add(compliance_requirement)
        assert compliance_requirement in compliance_report.compliance_requirements.all()

    def test_compliance_score_decimal(self, compliance_report):
        """Test compliance_score accepts decimal values."""
        compliance_report.compliance_score = Decimal('87.50')
        compliance_report.requirements_assessed = 100
        compliance_report.requirements_compliant = 88
        compliance_report.save()
        compliance_report.refresh_from_db()
        assert compliance_report.compliance_score == Decimal('87.50')


# =============================================================================
# TEST: QualityMetric Model
# =============================================================================

@pytest.mark.django_db
class TestQualityMetricModel:
    """Tests for QualityMetric model."""

    def test_create_quality_metric(self, user):
        """Test creating a quality metric."""
        metric = QualityMetric.objects.create(
            metric_name='Customer Satisfaction Score',
            metric_type=QualityMetric.MetricType.CUSTOMER_SATISFACTION,
            measurement_period=date.today(),
            measured_value=Decimal('4.50'),
            unit_of_measure='Rating (1-5)',
            recorded_by=user
        )
        assert metric.pk is not None

    def test_str_representation(self, quality_metric):
        """Test __str__ returns meaningful string."""
        result = str(quality_metric)
        assert quality_metric.metric_name in result
        assert str(quality_metric.measured_value) in result

    def test_metric_type_choices(self, quality_metric):
        """Test metric_type accepts valid choices."""
        for choice, _ in QualityMetric.MetricType.choices:
            quality_metric.metric_type = choice
            quality_metric.full_clean()

    def test_trend_choices(self, quality_metric):
        """Test trend accepts valid choices."""
        for choice, _ in QualityMetric.Trend.choices:
            quality_metric.trend = choice
            quality_metric.full_clean()

    def test_meets_target_property_true(self, quality_metric):
        """Test meets_target returns True when value >= target."""
        quality_metric.target_value = Decimal('90.00')
        quality_metric.measured_value = Decimal('95.50')
        quality_metric.save()
        assert quality_metric.meets_target is True

    def test_meets_target_property_false(self, quality_metric):
        """Test meets_target returns False when value < target."""
        quality_metric.target_value = Decimal('98.00')
        quality_metric.measured_value = Decimal('95.50')
        quality_metric.save()
        assert quality_metric.meets_target is False

    def test_meets_target_property_no_target(self, quality_metric):
        """Test meets_target returns None when no target set."""
        quality_metric.target_value = None
        quality_metric.save()
        assert quality_metric.meets_target is None

    def test_measured_value_precision(self, quality_metric):
        """Test measured_value accepts high precision decimals."""
        quality_metric.measured_value = Decimal('99.9999')
        quality_metric.save()
        quality_metric.refresh_from_db()
        assert quality_metric.measured_value == Decimal('99.9999')

    def test_previous_value_for_trend(self, quality_metric):
        """Test previous_value can be stored for trend analysis."""
        quality_metric.previous_value = Decimal('92.00')
        quality_metric.trend = QualityMetric.Trend.IMPROVING
        quality_metric.save()
        quality_metric.refresh_from_db()
        assert quality_metric.previous_value == Decimal('92.00')
        assert quality_metric.trend == QualityMetric.Trend.IMPROVING


# =============================================================================
# TEST: InspectionChecklist Model
# =============================================================================

@pytest.mark.django_db
class TestInspectionChecklistModel:
    """Tests for InspectionChecklist model."""

    def test_create_inspection_checklist(self, user):
        """Test creating an inspection checklist."""
        checklist = InspectionChecklist.objects.create(
            checklist_code='CHK-FINAL-001',
            checklist_name='Final Inspection Checklist',
            inspection_type=InspectionChecklist.InspectionType.FINAL,
            applicable_to='All finished products',
            checklist_items=[
                {'item': 'Visual inspection', 'required': True},
                {'item': 'Functional test', 'required': True}
            ],
            version='1.0',
            created_by=user
        )
        assert checklist.pk is not None
        assert checklist.is_active is True

    def test_str_representation(self, inspection_checklist):
        """Test __str__ returns meaningful string."""
        result = str(inspection_checklist)
        assert inspection_checklist.checklist_code in result
        assert inspection_checklist.checklist_name in result

    def test_checklist_code_unique(self, user, inspection_checklist):
        """Test checklist_code must be unique."""
        with pytest.raises(IntegrityError):
            InspectionChecklist.objects.create(
                checklist_code=inspection_checklist.checklist_code,
                checklist_name='Duplicate',
                inspection_type=InspectionChecklist.InspectionType.INCOMING,
                applicable_to='Test',
                checklist_items=[{'item': 'Test'}],
                version='1.0',
                created_by=user
            )

    def test_inspection_type_choices(self, inspection_checklist):
        """Test inspection_type accepts valid choices."""
        for choice, _ in InspectionChecklist.InspectionType.choices:
            inspection_checklist.inspection_type = choice
            inspection_checklist.full_clean()

    def test_item_count_property(self, inspection_checklist):
        """Test item_count returns correct number of items."""
        assert inspection_checklist.item_count == 3

    def test_item_count_property_empty(self, user):
        """Test item_count returns 0 for empty checklist."""
        checklist = InspectionChecklist.objects.create(
            checklist_code='CHK-EMPTY',
            checklist_name='Empty Checklist',
            inspection_type=InspectionChecklist.InspectionType.INCOMING,
            applicable_to='Test',
            checklist_items=[],
            version='1.0',
            created_by=user
        )
        assert checklist.item_count == 0

    def test_item_count_property_null(self, user):
        """Test item_count returns 0 for null checklist_items."""
        checklist = InspectionChecklist.objects.create(
            checklist_code='CHK-NULL',
            checklist_name='Null Checklist',
            inspection_type=InspectionChecklist.InspectionType.INCOMING,
            applicable_to='Test',
            checklist_items=None,
            version='1.0',
            created_by=user
        )
        assert checklist.item_count == 0

    def test_checklist_items_json_structure(self, inspection_checklist):
        """Test checklist_items stores JSON correctly."""
        inspection_checklist.refresh_from_db()
        items = inspection_checklist.checklist_items
        assert isinstance(items, list)
        assert len(items) == 3
        assert items[0]['item'] == 'Visual inspection'
        assert items[0]['required'] is True

    def test_is_active_default_true(self, user):
        """Test is_active defaults to True."""
        checklist = InspectionChecklist.objects.create(
            checklist_code='CHK-ACTIVE',
            checklist_name='Active Checklist',
            inspection_type=InspectionChecklist.InspectionType.IN_PROCESS,
            applicable_to='All products',
            checklist_items=[{'item': 'Check'}],
            version='1.0',
            created_by=user
        )
        assert checklist.is_active is True

    def test_compliance_requirement_fk(self, inspection_checklist, compliance_requirement):
        """Test foreign key to ComplianceRequirement."""
        inspection_checklist.compliance_requirement = compliance_requirement
        inspection_checklist.save()
        assert inspection_checklist.compliance_requirement == compliance_requirement
        assert inspection_checklist in compliance_requirement.inspection_checklists.all()


# =============================================================================
# TEST: Model Ordering
# =============================================================================

@pytest.mark.django_db
class TestModelOrdering:
    """Tests for default model ordering."""

    def test_compliance_requirement_ordering(self, user):
        """Test ComplianceRequirement orders by requirement_code."""
        ComplianceRequirement.objects.create(
            requirement_code='ZZZ-001',
            title='Z Requirement',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            created_by=user
        )
        ComplianceRequirement.objects.create(
            requirement_code='AAA-001',
            title='A Requirement',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            created_by=user
        )
        reqs = list(ComplianceRequirement.objects.all())
        assert reqs[0].requirement_code < reqs[-1].requirement_code

    def test_quality_control_ordering(self, inspector):
        """Test QualityControl orders by -inspection_date, -inspection_number."""
        qc1 = QualityControl.objects.create(
            inspection_type=QualityControl.InspectionType.INCOMING,
            inspection_date=date.today() - timedelta(days=5),
            inspector=inspector
        )
        qc2 = QualityControl.objects.create(
            inspection_type=QualityControl.InspectionType.FINAL,
            inspection_date=date.today(),
            inspector=inspector
        )
        qcs = list(QualityControl.objects.all())
        assert qcs[0].inspection_date >= qcs[-1].inspection_date

    def test_audit_trail_ordering(self, user):
        """Test AuditTrail orders by -timestamp (most recent first)."""
        # Create with slight delay to ensure different timestamps
        audit1 = AuditTrail.objects.create(
            action=AuditTrail.Action.CREATED,
            description='First',
            model_name='Test',
            object_id=1,
            user=user
        )
        audit2 = AuditTrail.objects.create(
            action=AuditTrail.Action.UPDATED,
            description='Second',
            model_name='Test',
            object_id=1,
            user=user
        )
        audits = list(AuditTrail.objects.all())
        assert audits[0].timestamp >= audits[-1].timestamp
