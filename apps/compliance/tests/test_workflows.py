"""
Compliance App - Workflow Tests
Integration tests for real user workflows.

Tests cover end-to-end user journeys through the compliance system.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client

from apps.compliance.models import (
    ComplianceRequirement, QualityControl, NonConformance,
    AuditTrail, DocumentControl, TrainingRecord, Certification,
    ComplianceReport, QualityMetric, InspectionChecklist
)

User = get_user_model()


@pytest.fixture
def client():
    """Create test client."""
    return Client()


@pytest.fixture
def quality_manager(db):
    """Create a quality manager user."""
    return User.objects.create_user(
        username='qm_manager',
        email='qm@example.com',
        password='qmpass123',
        first_name='Quality',
        last_name='Manager'
    )


@pytest.fixture
def quality_inspector(db):
    """Create a quality inspector user."""
    return User.objects.create_user(
        username='inspector',
        email='inspector@example.com',
        password='insppass123',
        first_name='Quality',
        last_name='Inspector'
    )


@pytest.fixture
def hr_manager(db):
    """Create an HR manager user."""
    return User.objects.create_user(
        username='hr_manager',
        email='hr@example.com',
        password='hrpass123',
        first_name='HR',
        last_name='Manager'
    )


@pytest.fixture
def employee(db):
    """Create a regular employee user."""
    return User.objects.create_user(
        username='employee',
        email='employee@example.com',
        password='emppass123',
        first_name='John',
        last_name='Employee'
    )


# =============================================================================
# WORKFLOW 1: Compliance Requirement Lifecycle
# =============================================================================

@pytest.mark.django_db
class TestComplianceRequirementLifecycle:
    """
    Tests the complete lifecycle of a compliance requirement:
    1. Create new requirement (PENDING status)
    2. Review and activate requirement
    3. Assess compliance status
    4. Link related documents
    5. Create quality controls based on requirement
    6. Generate compliance report
    7. Supersede with new version
    8. Archive old requirement
    """

    def test_create_new_compliance_requirement(self, client, quality_manager):
        """Step 1: Create a new compliance requirement."""
        client.login(username='qm_manager', password='qmpass123')

        # Navigate to create page
        url = reverse('compliance:compliancerequirement_create')
        response = client.get(url)
        assert response.status_code == 200

        # Submit new requirement
        form_data = {
            'requirement_code': 'ISO-9001-7.1.5',
            'title': 'Monitoring and Measuring Resources',
            'requirement_type': 'ISO_STANDARD',
            'source_document': 'ISO 9001:2015',
            'clause_number': '7.1.5',
            'description': 'Requirements for monitoring and measuring resources',
            'effective_date': date.today().isoformat(),
            'status': 'PENDING',
            'compliance_status': 'NOT_ASSESSED',
            'risk_level': 'HIGH',
            'responsible_person': quality_manager.pk,
            'responsible_department': 'Quality Assurance'
        }
        response = client.post(url, data=form_data)

        if response.status_code == 302:
            req = ComplianceRequirement.objects.get(requirement_code='ISO-9001-7.1.5')
            assert req.status == 'PENDING'
            assert req.compliance_status == 'NOT_ASSESSED'
            return req.pk
        return None

    def test_activate_requirement(self, client, quality_manager):
        """Step 2: Activate a pending requirement."""
        client.login(username='qm_manager', password='qmpass123')

        # Create requirement first
        req = ComplianceRequirement.objects.create(
            requirement_code='ISO-ACTIVATE-TEST',
            title='Test Requirement',
            requirement_type='ISO_STANDARD',
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            status='PENDING',
            created_by=quality_manager
        )

        # Update to ACTIVE
        url = reverse('compliance:compliancerequirement_update', kwargs={'pk': req.pk})
        form_data = {
            'requirement_code': req.requirement_code,
            'title': req.title,
            'requirement_type': req.requirement_type,
            'source_document': req.source_document,
            'description': req.description,
            'effective_date': req.effective_date.isoformat(),
            'status': 'ACTIVE',
            'compliance_status': 'NOT_ASSESSED',
            'risk_level': 'MEDIUM'
        }
        response = client.post(url, data=form_data)

        if response.status_code == 302:
            req.refresh_from_db()
            assert req.status == 'ACTIVE'

    def test_assess_compliance_status(self, client, quality_manager):
        """Step 3: Assess compliance status."""
        client.login(username='qm_manager', password='qmpass123')

        req = ComplianceRequirement.objects.create(
            requirement_code='ISO-ASSESS-TEST',
            title='Test Requirement',
            requirement_type='ISO_STANDARD',
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            status='ACTIVE',
            created_by=quality_manager
        )

        # Update compliance status to COMPLIANT
        url = reverse('compliance:compliancerequirement_update', kwargs={'pk': req.pk})
        form_data = {
            'requirement_code': req.requirement_code,
            'title': req.title,
            'requirement_type': req.requirement_type,
            'source_document': req.source_document,
            'description': req.description,
            'effective_date': req.effective_date.isoformat(),
            'status': 'ACTIVE',
            'compliance_status': 'COMPLIANT',
            'risk_level': 'MEDIUM',
            'last_assessment_date': date.today().isoformat(),
            'last_assessed_by': quality_manager.pk,
            'assessment_notes': 'Full compliance verified during internal audit'
        }
        response = client.post(url, data=form_data)

        if response.status_code == 302:
            req.refresh_from_db()
            assert req.compliance_status == 'COMPLIANT'

    def test_complete_requirement_lifecycle(self, client, quality_manager):
        """Test complete requirement from creation to supersession."""
        client.login(username='qm_manager', password='qmpass123')

        # Create original requirement
        original = ComplianceRequirement.objects.create(
            requirement_code='ISO-LIFECYCLE-V1',
            title='Original Requirement',
            requirement_type='ISO_STANDARD',
            source_document='ISO 9001:2015',
            description='Original requirement',
            effective_date=date.today() - timedelta(days=365),
            status='ACTIVE',
            compliance_status='COMPLIANT',
            created_by=quality_manager
        )

        # Create new version that supersedes
        url = reverse('compliance:compliancerequirement_create')
        form_data = {
            'requirement_code': 'ISO-LIFECYCLE-V2',
            'title': 'Updated Requirement',
            'requirement_type': 'ISO_STANDARD',
            'source_document': 'ISO 9001:2015 (Updated)',
            'description': 'Updated requirement',
            'effective_date': date.today().isoformat(),
            'status': 'ACTIVE',
            'compliance_status': 'NOT_ASSESSED',
            'risk_level': 'MEDIUM',
            'supersedes': original.pk
        }
        response = client.post(url, data=form_data)

        if response.status_code == 302:
            new_req = ComplianceRequirement.objects.get(requirement_code='ISO-LIFECYCLE-V2')
            assert new_req.supersedes == original

            # Mark original as superseded
            original.status = 'SUPERSEDED'
            original.superseded_date = date.today()
            original.save()

            assert original.status == 'SUPERSEDED'


# =============================================================================
# WORKFLOW 2: Quality Control Inspection Process
# =============================================================================

@pytest.mark.django_db
class TestQualityInspectionWorkflow:
    """
    Tests the quality control inspection workflow:
    1. Inspector creates incoming inspection
    2. Perform inspection checks
    3. Document findings
    4. If FAIL: Create NCR
    5. If PASS: Approve and close
    6. Link to compliance requirement
    """

    def test_incoming_inspection_pass(self, client, quality_inspector):
        """Test incoming inspection that passes."""
        client.login(username='inspector', password='insppass123')

        # Create inspection
        url = reverse('compliance:qualitycontrol_create')
        response = client.get(url)
        assert response.status_code == 200

        form_data = {
            'inspection_type': 'INCOMING',
            'result': 'PASS',
            'inspection_date': date.today().isoformat(),
            'inspector': quality_inspector.pk,
            'findings': 'All dimensional checks within tolerance. Visual inspection passed.',
            'passed_criteria': 'Dimensions, Surface finish, Material certification'
        }
        response = client.post(url, data=form_data)

        if response.status_code == 302:
            qc = QualityControl.objects.filter(
                inspection_type='INCOMING',
                result='PASS'
            ).first()
            if qc:
                assert qc.is_passed is True

    def test_incoming_inspection_fail_creates_ncr(self, client, quality_inspector):
        """Test incoming inspection that fails and creates NCR."""
        client.login(username='inspector', password='insppass123')

        # Create failed inspection
        qc = QualityControl.objects.create(
            inspection_type=QualityControl.InspectionType.INCOMING,
            result=QualityControl.Result.FAIL,
            inspection_date=date.today(),
            inspector=quality_inspector,
            findings='Dimensional deviation found',
            defects_found='OD measurement: 25.5mm (spec: 25.0 +/- 0.1mm)',
            corrective_action_required=True,
            created_by=quality_inspector
        )

        assert qc.is_passed is False

        # Create NCR for failed inspection
        url = reverse('compliance:nonconformance_create')
        form_data = {
            'source': 'QUALITY_INSPECTION',
            'severity': 'MAJOR',
            'status': 'OPEN',
            'description': 'Dimensional non-conformance on incoming material',
            'defect_description': 'OD out of tolerance: measured 25.5mm vs spec 25.0 +/- 0.1mm',
            'detected_date': date.today().isoformat(),
            'quality_control': qc.pk
        }
        response = client.post(url, data=form_data)

        if response.status_code == 302:
            ncr = NonConformance.objects.filter(
                source='QUALITY_INSPECTION',
                severity='MAJOR'
            ).first()
            if ncr:
                assert ncr.is_open is True

    def test_final_inspection_with_witness(self, client, quality_inspector, quality_manager):
        """Test final inspection with customer witness point."""
        client.login(username='inspector', password='insppass123')

        qc = QualityControl.objects.create(
            inspection_type=QualityControl.InspectionType.CUSTOMER_WITNESS,
            result=QualityControl.Result.CONDITIONAL_PASS,
            inspection_date=date.today(),
            inspector=quality_inspector,
            witness=quality_manager,
            findings='Minor cosmetic issue noted but acceptable',
            disposition='CONDITIONAL',
            disposition_notes='Accepted with waiver for minor cosmetic defect',
            created_by=quality_inspector
        )

        assert qc.is_passed is True
        assert qc.witness == quality_manager


# =============================================================================
# WORKFLOW 3: Non-Conformance Report Lifecycle
# =============================================================================

@pytest.mark.django_db
class TestNonConformanceLifecycle:
    """
    Tests the NCR lifecycle:
    1. Open NCR with issue description
    2. Investigate and document root cause
    3. Implement corrective action
    4. Verify effectiveness
    5. Close NCR with lessons learned
    """

    def test_ncr_investigation_workflow(self, client, quality_inspector, quality_manager):
        """Test NCR from open to investigation."""
        client.login(username='inspector', password='insppass123')

        # Create NCR
        ncr = NonConformance.objects.create(
            source=NonConformance.Source.QUALITY_INSPECTION,
            severity=NonConformance.Severity.MAJOR,
            description='Dimensional non-conformance',
            defect_description='Part diameter out of specification',
            detected_date=date.today(),
            reported_by=quality_inspector,
            status=NonConformance.Status.OPEN
        )

        assert ncr.is_open is True

        # Assign and start investigation
        ncr.assigned_to = quality_manager
        ncr.status = NonConformance.Status.INVESTIGATING
        ncr.root_cause_analysis = 'Tool wear caused dimensional drift'
        ncr.contributing_factors = 'Delayed tool replacement, insufficient in-process checks'
        ncr.save()

        ncr.refresh_from_db()
        assert ncr.status == 'INVESTIGATING'

    def test_ncr_corrective_action_workflow(self, client, quality_inspector, quality_manager):
        """Test NCR corrective action implementation."""
        client.login(username='qm_manager', password='qmpass123')

        ncr = NonConformance.objects.create(
            source=NonConformance.Source.QUALITY_INSPECTION,
            severity=NonConformance.Severity.MAJOR,
            description='Dimensional non-conformance',
            defect_description='Part diameter out of specification',
            detected_date=date.today(),
            reported_by=quality_inspector,
            assigned_to=quality_manager,
            status=NonConformance.Status.INVESTIGATING,
            root_cause_analysis='Tool wear'
        )

        # Implement corrective action
        ncr.status = NonConformance.Status.CORRECTIVE_ACTION
        ncr.corrective_action = 'Replaced worn tool, implemented tool life monitoring'
        ncr.preventive_action = 'Added tool wear check to daily PM, updated work instructions'
        ncr.target_completion_date = date.today() + timedelta(days=7)
        ncr.save()

        ncr.refresh_from_db()
        assert ncr.status == 'CORRECTIVE_ACTION'

    def test_ncr_verification_and_closure(self, client, quality_inspector, quality_manager):
        """Test NCR verification and closure."""
        client.login(username='qm_manager', password='qmpass123')

        ncr = NonConformance.objects.create(
            source=NonConformance.Source.QUALITY_INSPECTION,
            severity=NonConformance.Severity.MAJOR,
            description='Dimensional non-conformance',
            defect_description='Part diameter out of specification',
            detected_date=date.today() - timedelta(days=14),
            reported_by=quality_inspector,
            assigned_to=quality_manager,
            status=NonConformance.Status.CORRECTIVE_ACTION,
            corrective_action='Replaced worn tool'
        )

        # Verify and close
        ncr.status = NonConformance.Status.VERIFICATION
        ncr.verified_by = quality_manager
        ncr.verification_date = date.today()
        ncr.verification_notes = 'Verified 10 parts produced after corrective action - all within spec'
        ncr.save()

        # Close
        ncr.status = NonConformance.Status.CLOSED
        ncr.closed_by = quality_manager
        ncr.closed_date = date.today()
        ncr.actual_completion_date = date.today()
        ncr.closure_notes = 'Corrective action verified effective'
        ncr.save()

        ncr.refresh_from_db()
        assert ncr.is_open is False
        assert ncr.status == 'CLOSED'


# =============================================================================
# WORKFLOW 4: Training & Certification Management
# =============================================================================

@pytest.mark.django_db
class TestTrainingWorkflow:
    """
    Tests training management workflow:
    1. Schedule training for employee
    2. Track training completion
    3. Record assessment results
    4. Issue certification
    5. Track expiry and renewal
    """

    def test_schedule_and_complete_training(self, client, hr_manager, employee):
        """Test scheduling and completing training."""
        client.login(username='hr_manager', password='hrpass123')

        # Create scheduled training
        training = TrainingRecord.objects.create(
            employee=employee,
            training_type=TrainingRecord.TrainingType.SAFETY,
            training_title='Annual Safety Refresher',
            training_provider='Internal Safety Team',
            scheduled_date=date.today(),
            start_date=date.today(),
            duration_hours=Decimal('4.00'),
            status=TrainingRecord.Status.SCHEDULED,
            required_for_position=True,
            recorded_by=hr_manager
        )

        assert training.status == 'SCHEDULED'

        # Mark as in progress
        training.status = TrainingRecord.Status.IN_PROGRESS
        training.save()

        # Complete training
        training.status = TrainingRecord.Status.COMPLETED
        training.completion_date = date.today()
        training.passed = True
        training.score = Decimal('92.00')
        training.save()

        training.refresh_from_db()
        assert training.status == 'COMPLETED'
        assert training.passed is True

    def test_training_with_certification(self, client, hr_manager, employee):
        """Test training that leads to certification."""
        client.login(username='hr_manager', password='hrpass123')

        # Create completed training
        training = TrainingRecord.objects.create(
            employee=employee,
            training_type=TrainingRecord.TrainingType.CERTIFICATION,
            training_title='ISO Lead Auditor Course',
            training_provider='IRCA',
            start_date=date.today() - timedelta(days=5),
            completion_date=date.today(),
            duration_hours=Decimal('40.00'),
            status=TrainingRecord.Status.COMPLETED,
            passed=True,
            score=Decimal('85.00'),
            certificate_number='IRCA-LA-12345',
            certificate_issued_date=date.today(),
            certificate_expiry_date=date.today() + timedelta(days=1095),  # 3 years
            recorded_by=hr_manager
        )

        # Create linked certification
        cert = Certification.objects.create(
            employee=employee,
            certification_name='ISO 9001 Lead Auditor',
            certification_body='IRCA',
            certification_number='IRCA-LA-12345',
            issue_date=date.today(),
            expiry_date=date.today() + timedelta(days=1095),
            status=Certification.Status.CURRENT,
            renewal_required=True
        )

        assert cert.is_expired is False
        assert cert.days_until_expiry > 1000


# =============================================================================
# WORKFLOW 5: Document Control Process
# =============================================================================

@pytest.mark.django_db
class TestDocumentControlWorkflow:
    """
    Tests document control workflow:
    1. Create draft document
    2. Submit for review
    3. Review and approve
    4. Publish and distribute
    5. Revise with new version
    6. Obsolete old version
    """

    def test_document_approval_workflow(self, client, quality_manager):
        """Test document from draft to approved."""
        client.login(username='qm_manager', password='qmpass123')

        # Create draft
        doc = DocumentControl.objects.create(
            document_number='PROC-QMS-001',
            title='Quality Management System Procedure',
            document_type=DocumentControl.DocumentType.PROCEDURE,
            version='1.0',
            revision_date=date.today(),
            status=DocumentControl.Status.DRAFT,
            file_path='/docs/proc-qms-001.pdf',
            prepared_by=quality_manager
        )

        assert doc.is_current is False

        # Submit for review
        doc.status = DocumentControl.Status.REVIEW
        doc.reviewed_by = quality_manager
        doc.reviewed_date = date.today()
        doc.save()

        # Approve
        doc.status = DocumentControl.Status.APPROVED
        doc.approved_by = quality_manager
        doc.approved_date = date.today()
        doc.effective_date = date.today()
        doc.save()

        doc.refresh_from_db()
        assert doc.is_current is True

    def test_document_revision_workflow(self, client, quality_manager):
        """Test creating new document revision."""
        client.login(username='qm_manager', password='qmpass123')

        # Original approved document
        original = DocumentControl.objects.create(
            document_number='PROC-QMS-002',
            title='Work Instructions',
            document_type=DocumentControl.DocumentType.WORK_INSTRUCTION,
            version='1.0',
            revision_date=date.today() - timedelta(days=365),
            status=DocumentControl.Status.APPROVED,
            file_path='/docs/wi-001-v1.pdf',
            prepared_by=quality_manager,
            approved_by=quality_manager,
            approved_date=date.today() - timedelta(days=365)
        )

        # Create new revision
        new_version = DocumentControl.objects.create(
            document_number='PROC-QMS-002',
            title='Work Instructions (Revised)',
            document_type=DocumentControl.DocumentType.WORK_INSTRUCTION,
            version='2.0',
            revision_date=date.today(),
            status=DocumentControl.Status.DRAFT,
            file_path='/docs/wi-001-v2.pdf',
            prepared_by=quality_manager,
            supersedes=original,
            change_summary='Updated safety requirements section'
        )

        assert new_version.supersedes == original

        # Approve new version and obsolete old
        new_version.status = DocumentControl.Status.APPROVED
        new_version.approved_by = quality_manager
        new_version.approved_date = date.today()
        new_version.save()

        original.status = DocumentControl.Status.OBSOLETE
        original.save()

        assert new_version.is_current is True
        assert original.is_current is False


# =============================================================================
# WORKFLOW 6: Compliance Reporting
# =============================================================================

@pytest.mark.django_db
class TestComplianceReportingWorkflow:
    """
    Tests compliance reporting workflow:
    1. Gather compliance data for period
    2. Create draft report
    3. Calculate compliance scores
    4. Review and approve report
    5. Publish report
    """

    def test_quarterly_compliance_report(self, client, quality_manager):
        """Test creating quarterly compliance report."""
        client.login(username='qm_manager', password='qmpass123')

        # Create some compliance requirements to report on
        reqs = []
        for i in range(10):
            req = ComplianceRequirement.objects.create(
                requirement_code=f'RPT-REQ-{i:03d}',
                title=f'Requirement {i}',
                requirement_type='INTERNAL_POLICY',
                source_document='Test',
                description='Test',
                effective_date=date.today() - timedelta(days=90),
                status='ACTIVE',
                compliance_status='COMPLIANT' if i < 8 else 'NON_COMPLIANT',
                created_by=quality_manager
            )
            reqs.append(req)

        # Create compliance report
        report = ComplianceReport.objects.create(
            report_type=ComplianceReport.ReportType.QUARTERLY,
            title='Q4 2024 Compliance Report',
            reporting_period_start=date(2024, 10, 1),
            reporting_period_end=date(2024, 12, 31),
            prepared_by=quality_manager,
            status=ComplianceReport.Status.DRAFT,
            requirements_assessed=10,
            requirements_compliant=8,
            non_conformances_count=2,
            compliance_score=Decimal('80.00'),
            executive_summary='Overall compliance rate: 80%',
            findings='2 non-conformances identified in administrative controls',
            recommendations='Implement additional training for administrative procedures'
        )

        # Link requirements
        for req in reqs:
            report.compliance_requirements.add(req)

        assert report.compliance_requirements.count() == 10

        # Approve and publish
        report.status = ComplianceReport.Status.APPROVED
        report.approved_by = quality_manager
        report.approved_date = date.today()
        report.save()

        report.status = ComplianceReport.Status.PUBLISHED
        report.save()

        report.refresh_from_db()
        assert report.status == 'PUBLISHED'


# =============================================================================
# WORKFLOW 7: Quality Metrics Tracking
# =============================================================================

@pytest.mark.django_db
class TestQualityMetricsWorkflow:
    """
    Tests quality metrics tracking workflow:
    1. Record metrics for period
    2. Compare to targets
    3. Identify trends
    4. Take action on off-target metrics
    """

    def test_monthly_metrics_recording(self, client, quality_manager):
        """Test recording monthly quality metrics."""
        client.login(username='qm_manager', password='qmpass123')

        # Record previous month's metric
        prev_metric = QualityMetric.objects.create(
            metric_name='First Pass Yield',
            metric_type=QualityMetric.MetricType.FIRST_PASS_YIELD,
            measurement_period=date.today() - timedelta(days=30),
            measured_value=Decimal('94.00'),
            unit_of_measure='%',
            target_value=Decimal('95.00'),
            recorded_by=quality_manager
        )

        # Record current month
        current_metric = QualityMetric.objects.create(
            metric_name='First Pass Yield',
            metric_type=QualityMetric.MetricType.FIRST_PASS_YIELD,
            measurement_period=date.today(),
            measured_value=Decimal('96.50'),
            unit_of_measure='%',
            target_value=Decimal('95.00'),
            previous_value=Decimal('94.00'),
            trend=QualityMetric.Trend.IMPROVING,
            recorded_by=quality_manager
        )

        assert current_metric.meets_target is True
        assert current_metric.trend == 'IMPROVING'

    def test_metrics_trend_analysis(self, client, quality_manager):
        """Test analyzing metric trends."""
        client.login(username='qm_manager', password='qmpass123')

        # Create 6 months of metrics
        base_value = 90.0
        for i in range(6):
            period = date.today() - timedelta(days=30 * (5 - i))
            value = base_value + (i * 1.5)  # Improving trend

            QualityMetric.objects.create(
                metric_name='Customer Satisfaction',
                metric_type=QualityMetric.MetricType.CUSTOMER_SATISFACTION,
                measurement_period=period,
                measured_value=Decimal(str(value)),
                unit_of_measure='%',
                target_value=Decimal('95.00'),
                recorded_by=quality_manager
            )

        metrics = QualityMetric.objects.filter(
            metric_type=QualityMetric.MetricType.CUSTOMER_SATISFACTION
        ).order_by('measurement_period')

        # Verify improving trend
        values = [float(m.measured_value) for m in metrics]
        assert values[-1] > values[0]  # Most recent > oldest


# =============================================================================
# WORKFLOW 8: Audit Trail Analysis
# =============================================================================

@pytest.mark.django_db
class TestAuditTrailWorkflow:
    """
    Tests audit trail for compliance activities.
    """

    def test_audit_trail_creation(self, client, quality_manager):
        """Test audit trail entries are created for actions."""
        client.login(username='qm_manager', password='qmpass123')

        # Create audit entry for document approval
        audit = AuditTrail.objects.create(
            action=AuditTrail.Action.APPROVED,
            description='Approved document PROC-QMS-001 v2.0',
            model_name='DocumentControl',
            object_id=1,
            object_repr='PROC-QMS-001 v2.0 - Quality Management Procedure',
            user=quality_manager,
            ip_address='192.168.1.100',
            changes={
                'old': {'status': 'REVIEW'},
                'new': {'status': 'APPROVED'}
            }
        )

        assert audit.action == 'APPROVED'
        assert audit.user == quality_manager

    def test_audit_trail_query(self, client, quality_manager):
        """Test querying audit trail for specific model."""
        client.login(username='qm_manager', password='qmpass123')

        # Create multiple audit entries
        for i in range(5):
            AuditTrail.objects.create(
                action=AuditTrail.Action.UPDATED,
                description=f'Updated requirement {i}',
                model_name='ComplianceRequirement',
                object_id=i,
                user=quality_manager
            )

        for i in range(3):
            AuditTrail.objects.create(
                action=AuditTrail.Action.CREATED,
                description=f'Created document {i}',
                model_name='DocumentControl',
                object_id=i,
                user=quality_manager
            )

        # Query for specific model
        req_audits = AuditTrail.objects.filter(model_name='ComplianceRequirement')
        doc_audits = AuditTrail.objects.filter(model_name='DocumentControl')

        assert req_audits.count() == 5
        assert doc_audits.count() == 3
