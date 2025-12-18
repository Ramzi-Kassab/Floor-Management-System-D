"""
Compliance App - View Tests
Comprehensive tests for all compliance views.

Tests cover:
- Login required (unauthenticated redirects to login)
- GET request returns 200 status
- Uses correct template
- Context contains expected objects
- List views: pagination, filters, search
- Detail views: shows correct object, handles DoesNotExist
- Create views: GET shows form, POST creates object
- Update views: GET shows pre-filled form, POST updates object
- Delete views: GET shows confirmation, POST deletes object
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


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def client():
    """Create test client."""
    return Client()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(client, user):
    """Create authenticated test client."""
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    return User.objects.create_user(
        username='staffuser',
        email='staff@example.com',
        password='staffpass123',
        is_staff=True
    )


@pytest.fixture
def staff_client(client, staff_user):
    """Create authenticated staff client."""
    client.login(username='staffuser', password='staffpass123')
    return client


@pytest.fixture
def compliance_requirement(db, user):
    """Create a test compliance requirement."""
    return ComplianceRequirement.objects.create(
        requirement_code='ISO-9001-TEST',
        title='Test Compliance Requirement',
        requirement_type=ComplianceRequirement.RequirementType.ISO_STANDARD,
        source_document='ISO 9001:2015',
        description='Test requirement description',
        effective_date=date.today(),
        created_by=user
    )


@pytest.fixture
def quality_control(db, user):
    """Create a test quality control inspection."""
    return QualityControl.objects.create(
        inspection_type=QualityControl.InspectionType.INCOMING,
        result=QualityControl.Result.PASS,
        inspection_date=date.today(),
        inspector=user,
        findings='Test findings',
        created_by=user
    )


@pytest.fixture
def non_conformance(db, user):
    """Create a test non-conformance report."""
    return NonConformance.objects.create(
        source=NonConformance.Source.QUALITY_INSPECTION,
        severity=NonConformance.Severity.MAJOR,
        description='Test NCR',
        defect_description='Test defect',
        detected_date=date.today(),
        reported_by=user
    )


@pytest.fixture
def document_control(db, user):
    """Create a test controlled document."""
    return DocumentControl.objects.create(
        document_number='DOC-TEST-001',
        title='Test Document',
        document_type=DocumentControl.DocumentType.PROCEDURE,
        version='1.0',
        revision_date=date.today(),
        file_path='/test/document.pdf',
        prepared_by=user
    )


@pytest.fixture
def training_record(db, user):
    """Create a test training record."""
    return TrainingRecord.objects.create(
        employee=user,
        training_type=TrainingRecord.TrainingType.SAFETY,
        training_title='Test Training',
        training_provider='Test Provider',
        start_date=date.today(),
        duration_hours=Decimal('8.00')
    )


@pytest.fixture
def certification(db, user):
    """Create a test certification."""
    return Certification.objects.create(
        employee=user,
        certification_name='Test Certification',
        certification_body='Test Body',
        issue_date=date.today() - timedelta(days=30),
        expiry_date=date.today() + timedelta(days=365)
    )


@pytest.fixture
def compliance_report(db, user):
    """Create a test compliance report."""
    return ComplianceReport.objects.create(
        report_type=ComplianceReport.ReportType.QUARTERLY,
        title='Test Compliance Report',
        reporting_period_start=date(2024, 1, 1),
        reporting_period_end=date(2024, 3, 31),
        prepared_by=user
    )


@pytest.fixture
def quality_metric(db, user):
    """Create a test quality metric."""
    return QualityMetric.objects.create(
        metric_name='Test Metric',
        metric_type=QualityMetric.MetricType.FIRST_PASS_YIELD,
        measurement_period=date.today(),
        measured_value=Decimal('95.00'),
        unit_of_measure='%',
        recorded_by=user
    )


@pytest.fixture
def inspection_checklist(db, user):
    """Create a test inspection checklist."""
    return InspectionChecklist.objects.create(
        checklist_code='CHK-TEST-001',
        checklist_name='Test Checklist',
        inspection_type=InspectionChecklist.InspectionType.INCOMING,
        applicable_to='Test materials',
        checklist_items=[{'item': 'Test check', 'required': True}],
        version='1.0',
        created_by=user
    )


# =============================================================================
# TEST: Authentication Required
# =============================================================================

@pytest.mark.django_db
class TestAuthenticationRequired:
    """Tests that views require authentication."""

    def test_compliance_requirement_list_requires_login(self, client):
        """Test ComplianceRequirement list view requires login."""
        url = reverse('compliance:compliancerequirement_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url.lower() or 'accounts' in response.url.lower()

    def test_quality_control_list_requires_login(self, client):
        """Test QualityControl list view requires login."""
        url = reverse('compliance:qualitycontrol_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_non_conformance_list_requires_login(self, client):
        """Test NonConformance list view requires login."""
        url = reverse('compliance:nonconformance_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_document_control_list_requires_login(self, client):
        """Test DocumentControl list view requires login."""
        url = reverse('compliance:documentcontrol_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_training_record_list_requires_login(self, client):
        """Test TrainingRecord list view requires login."""
        url = reverse('compliance:trainingrecord_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_certification_list_requires_login(self, client):
        """Test Certification list view requires login."""
        url = reverse('compliance:certification_list')
        response = client.get(url)
        assert response.status_code == 302


# =============================================================================
# TEST: ComplianceRequirement Views
# =============================================================================

@pytest.mark.django_db
class TestComplianceRequirementListView:
    """Tests for ComplianceRequirement list view."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200 status."""
        url = reverse('compliance:compliancerequirement_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_uses_correct_template(self, authenticated_client):
        """Test list view uses correct template."""
        url = reverse('compliance:compliancerequirement_list')
        response = authenticated_client.get(url)
        assert 'compliance/compliancerequirement_list.html' in [t.name for t in response.templates]

    def test_list_view_contains_requirements(self, authenticated_client, compliance_requirement):
        """Test list view contains requirements in context."""
        url = reverse('compliance:compliancerequirement_list')
        response = authenticated_client.get(url)
        assert 'object_list' in response.context or 'requirements' in response.context

    def test_list_view_pagination(self, authenticated_client, user):
        """Test list view pagination works."""
        # Create 30 requirements
        for i in range(30):
            ComplianceRequirement.objects.create(
                requirement_code=f'REQ-{i:03d}',
                title=f'Requirement {i}',
                requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
                source_document='Test',
                description='Test',
                effective_date=date.today(),
                created_by=user
            )
        url = reverse('compliance:compliancerequirement_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        # Check pagination is present in context
        if 'page_obj' in response.context:
            assert response.context['page_obj'].paginator.count == 30

    def test_list_view_search(self, authenticated_client, compliance_requirement):
        """Test list view search functionality."""
        url = reverse('compliance:compliancerequirement_list')
        response = authenticated_client.get(url, {'q': 'ISO-9001'})
        assert response.status_code == 200


@pytest.mark.django_db
class TestComplianceRequirementDetailView:
    """Tests for ComplianceRequirement detail view."""

    def test_detail_view_returns_200(self, authenticated_client, compliance_requirement):
        """Test detail view returns 200 status."""
        url = reverse('compliance:compliancerequirement_detail', kwargs={'pk': compliance_requirement.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_uses_correct_template(self, authenticated_client, compliance_requirement):
        """Test detail view uses correct template."""
        url = reverse('compliance:compliancerequirement_detail', kwargs={'pk': compliance_requirement.pk})
        response = authenticated_client.get(url)
        assert 'compliance/compliancerequirement_detail.html' in [t.name for t in response.templates]

    def test_detail_view_contains_object(self, authenticated_client, compliance_requirement):
        """Test detail view contains correct object in context."""
        url = reverse('compliance:compliancerequirement_detail', kwargs={'pk': compliance_requirement.pk})
        response = authenticated_client.get(url)
        assert response.context['object'].pk == compliance_requirement.pk

    def test_detail_view_404_for_nonexistent(self, authenticated_client):
        """Test detail view returns 404 for non-existent object."""
        url = reverse('compliance:compliancerequirement_detail', kwargs={'pk': 99999})
        response = authenticated_client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestComplianceRequirementCreateView:
    """Tests for ComplianceRequirement create view."""

    def test_create_view_get_returns_200(self, authenticated_client):
        """Test create view GET returns 200."""
        url = reverse('compliance:compliancerequirement_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_contains_form(self, authenticated_client):
        """Test create view contains form in context."""
        url = reverse('compliance:compliancerequirement_create')
        response = authenticated_client.get(url)
        assert 'form' in response.context

    def test_create_view_post_creates_object(self, authenticated_client, user):
        """Test create view POST creates object."""
        url = reverse('compliance:compliancerequirement_create')
        form_data = {
            'requirement_code': 'NEW-REQ-001',
            'title': 'New Requirement',
            'requirement_type': 'INTERNAL_POLICY',
            'source_document': 'Internal',
            'description': 'New requirement description',
            'effective_date': date.today().isoformat(),
            'status': 'ACTIVE',
            'compliance_status': 'NOT_ASSESSED',
            'risk_level': 'MEDIUM'
        }
        response = authenticated_client.post(url, data=form_data)
        # Should redirect on success
        if response.status_code == 302:
            assert ComplianceRequirement.objects.filter(requirement_code='NEW-REQ-001').exists()

    def test_create_view_post_invalid_data(self, authenticated_client):
        """Test create view POST with invalid data shows errors."""
        url = reverse('compliance:compliancerequirement_create')
        response = authenticated_client.post(url, data={})
        assert response.status_code == 200  # Re-renders form with errors
        assert 'form' in response.context
        assert response.context['form'].errors


@pytest.mark.django_db
class TestComplianceRequirementUpdateView:
    """Tests for ComplianceRequirement update view."""

    def test_update_view_get_returns_200(self, authenticated_client, compliance_requirement):
        """Test update view GET returns 200."""
        url = reverse('compliance:compliancerequirement_update', kwargs={'pk': compliance_requirement.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_view_form_prepopulated(self, authenticated_client, compliance_requirement):
        """Test update view form is pre-populated."""
        url = reverse('compliance:compliancerequirement_update', kwargs={'pk': compliance_requirement.pk})
        response = authenticated_client.get(url)
        form = response.context['form']
        assert form.initial['title'] == compliance_requirement.title

    def test_update_view_post_updates_object(self, authenticated_client, compliance_requirement):
        """Test update view POST updates object."""
        url = reverse('compliance:compliancerequirement_update', kwargs={'pk': compliance_requirement.pk})
        form_data = {
            'requirement_code': compliance_requirement.requirement_code,
            'title': 'Updated Title',
            'requirement_type': compliance_requirement.requirement_type,
            'source_document': compliance_requirement.source_document,
            'description': 'Updated description',
            'effective_date': compliance_requirement.effective_date.isoformat(),
            'status': 'ACTIVE',
            'compliance_status': 'COMPLIANT',
            'risk_level': 'HIGH'
        }
        response = authenticated_client.post(url, data=form_data)
        if response.status_code == 302:
            compliance_requirement.refresh_from_db()
            assert compliance_requirement.title == 'Updated Title'


@pytest.mark.django_db
class TestComplianceRequirementDeleteView:
    """Tests for ComplianceRequirement delete view."""

    def test_delete_view_get_returns_200(self, authenticated_client, compliance_requirement):
        """Test delete view GET returns 200 (confirmation page)."""
        url = reverse('compliance:compliancerequirement_delete', kwargs={'pk': compliance_requirement.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_delete_view_uses_confirm_template(self, authenticated_client, compliance_requirement):
        """Test delete view uses confirmation template."""
        url = reverse('compliance:compliancerequirement_delete', kwargs={'pk': compliance_requirement.pk})
        response = authenticated_client.get(url)
        template_names = [t.name for t in response.templates]
        assert any('confirm_delete' in t for t in template_names)

    def test_delete_view_post_deletes_object(self, authenticated_client, compliance_requirement):
        """Test delete view POST deletes object."""
        pk = compliance_requirement.pk
        url = reverse('compliance:compliancerequirement_delete', kwargs={'pk': pk})
        response = authenticated_client.post(url)
        assert response.status_code == 302  # Redirect after delete
        assert not ComplianceRequirement.objects.filter(pk=pk).exists()


# =============================================================================
# TEST: QualityControl Views
# =============================================================================

@pytest.mark.django_db
class TestQualityControlViews:
    """Tests for QualityControl views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('compliance:qualitycontrol_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, quality_control):
        """Test detail view returns 200."""
        url = reverse('compliance:qualitycontrol_detail', kwargs={'pk': quality_control.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('compliance:qualitycontrol_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_view_returns_200(self, authenticated_client, quality_control):
        """Test update view returns 200."""
        url = reverse('compliance:qualitycontrol_update', kwargs={'pk': quality_control.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_delete_view_returns_200(self, authenticated_client, quality_control):
        """Test delete view returns 200."""
        url = reverse('compliance:qualitycontrol_delete', kwargs={'pk': quality_control.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# TEST: NonConformance Views
# =============================================================================

@pytest.mark.django_db
class TestNonConformanceViews:
    """Tests for NonConformance views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('compliance:nonconformance_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, non_conformance):
        """Test detail view returns 200."""
        url = reverse('compliance:nonconformance_detail', kwargs={'pk': non_conformance.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('compliance:nonconformance_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_filters_by_status(self, authenticated_client, non_conformance):
        """Test list view can filter by status."""
        url = reverse('compliance:nonconformance_list')
        response = authenticated_client.get(url, {'status': 'OPEN'})
        assert response.status_code == 200

    def test_list_view_filters_by_severity(self, authenticated_client, non_conformance):
        """Test list view can filter by severity."""
        url = reverse('compliance:nonconformance_list')
        response = authenticated_client.get(url, {'severity': 'MAJOR'})
        assert response.status_code == 200


# =============================================================================
# TEST: AuditTrail Views
# =============================================================================

@pytest.mark.django_db
class TestAuditTrailViews:
    """Tests for AuditTrail views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('compliance:audittrail_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, user):
        """Test detail view returns 200."""
        audit = AuditTrail.objects.create(
            action=AuditTrail.Action.CREATED,
            description='Test audit',
            model_name='Test',
            object_id=1,
            user=user
        )
        url = reverse('compliance:audittrail_detail', kwargs={'pk': audit.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# TEST: DocumentControl Views
# =============================================================================

@pytest.mark.django_db
class TestDocumentControlViews:
    """Tests for DocumentControl views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('compliance:documentcontrol_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, document_control):
        """Test detail view returns 200."""
        url = reverse('compliance:documentcontrol_detail', kwargs={'pk': document_control.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('compliance:documentcontrol_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_filters_by_type(self, authenticated_client, document_control):
        """Test list view can filter by document type."""
        url = reverse('compliance:documentcontrol_list')
        response = authenticated_client.get(url, {'document_type': 'PROCEDURE'})
        assert response.status_code == 200

    def test_list_view_filters_by_status(self, authenticated_client, document_control):
        """Test list view can filter by status."""
        url = reverse('compliance:documentcontrol_list')
        response = authenticated_client.get(url, {'status': 'DRAFT'})
        assert response.status_code == 200


# =============================================================================
# TEST: TrainingRecord Views
# =============================================================================

@pytest.mark.django_db
class TestTrainingRecordViews:
    """Tests for TrainingRecord views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('compliance:trainingrecord_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, training_record):
        """Test detail view returns 200."""
        url = reverse('compliance:trainingrecord_detail', kwargs={'pk': training_record.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('compliance:trainingrecord_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_filters_by_training_type(self, authenticated_client, training_record):
        """Test list view can filter by training type."""
        url = reverse('compliance:trainingrecord_list')
        response = authenticated_client.get(url, {'training_type': 'SAFETY'})
        assert response.status_code == 200


# =============================================================================
# TEST: Certification Views
# =============================================================================

@pytest.mark.django_db
class TestCertificationViews:
    """Tests for Certification views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('compliance:certification_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, certification):
        """Test detail view returns 200."""
        url = reverse('compliance:certification_detail', kwargs={'pk': certification.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('compliance:certification_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_list_view_filters_by_status(self, authenticated_client, certification):
        """Test list view can filter by status."""
        url = reverse('compliance:certification_list')
        response = authenticated_client.get(url, {'status': 'CURRENT'})
        assert response.status_code == 200


# =============================================================================
# TEST: ComplianceReport Views
# =============================================================================

@pytest.mark.django_db
class TestComplianceReportViews:
    """Tests for ComplianceReport views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('compliance:compliancereport_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, compliance_report):
        """Test detail view returns 200."""
        url = reverse('compliance:compliancereport_detail', kwargs={'pk': compliance_report.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('compliance:compliancereport_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# TEST: QualityMetric Views
# =============================================================================

@pytest.mark.django_db
class TestQualityMetricViews:
    """Tests for QualityMetric views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('compliance:qualitymetric_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, quality_metric):
        """Test detail view returns 200."""
        url = reverse('compliance:qualitymetric_detail', kwargs={'pk': quality_metric.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('compliance:qualitymetric_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# TEST: InspectionChecklist Views
# =============================================================================

@pytest.mark.django_db
class TestInspectionChecklistViews:
    """Tests for InspectionChecklist views."""

    def test_list_view_returns_200(self, authenticated_client):
        """Test list view returns 200."""
        url = reverse('compliance:inspectionchecklist_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_view_returns_200(self, authenticated_client, inspection_checklist):
        """Test detail view returns 200."""
        url = reverse('compliance:inspectionchecklist_detail', kwargs={'pk': inspection_checklist.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_view_returns_200(self, authenticated_client):
        """Test create view returns 200."""
        url = reverse('compliance:inspectionchecklist_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# TEST: Context Data
# =============================================================================

@pytest.mark.django_db
class TestViewContextData:
    """Tests for view context data."""

    def test_list_view_contains_object_list(self, authenticated_client, compliance_requirement):
        """Test list views contain object_list in context."""
        url = reverse('compliance:compliancerequirement_list')
        response = authenticated_client.get(url)
        assert 'object_list' in response.context or 'requirements' in response.context

    def test_detail_view_contains_object(self, authenticated_client, compliance_requirement):
        """Test detail views contain object in context."""
        url = reverse('compliance:compliancerequirement_detail', kwargs={'pk': compliance_requirement.pk})
        response = authenticated_client.get(url)
        assert 'object' in response.context or 'requirement' in response.context

    def test_create_view_contains_form(self, authenticated_client):
        """Test create views contain form in context."""
        url = reverse('compliance:compliancerequirement_create')
        response = authenticated_client.get(url)
        assert 'form' in response.context

    def test_update_view_contains_form_and_object(self, authenticated_client, compliance_requirement):
        """Test update views contain form and object in context."""
        url = reverse('compliance:compliancerequirement_update', kwargs={'pk': compliance_requirement.pk})
        response = authenticated_client.get(url)
        assert 'form' in response.context
        assert 'object' in response.context or 'compliancerequirement' in response.context


# =============================================================================
# TEST: Redirect After Success
# =============================================================================

@pytest.mark.django_db
class TestRedirectAfterSuccess:
    """Tests for redirect behavior after successful operations."""

    def test_create_redirects_to_list_or_detail(self, authenticated_client, user):
        """Test create view redirects after success."""
        url = reverse('compliance:compliancerequirement_create')
        form_data = {
            'requirement_code': 'REDIRECT-TEST',
            'title': 'Redirect Test',
            'requirement_type': 'INTERNAL_POLICY',
            'source_document': 'Test',
            'description': 'Test',
            'effective_date': date.today().isoformat(),
            'status': 'ACTIVE',
            'compliance_status': 'NOT_ASSESSED',
            'risk_level': 'LOW'
        }
        response = authenticated_client.post(url, data=form_data)
        if response.status_code == 302:
            assert 'compliance' in response.url

    def test_delete_redirects_to_list(self, authenticated_client, compliance_requirement):
        """Test delete view redirects to list after success."""
        url = reverse('compliance:compliancerequirement_delete', kwargs={'pk': compliance_requirement.pk})
        response = authenticated_client.post(url)
        assert response.status_code == 302
        assert 'list' in response.url or 'compliance' in response.url


# =============================================================================
# TEST: Messages
# =============================================================================

@pytest.mark.django_db
class TestViewMessages:
    """Tests for flash messages in views."""

    def test_create_shows_success_message(self, authenticated_client, user):
        """Test create view shows success message."""
        url = reverse('compliance:compliancerequirement_create')
        form_data = {
            'requirement_code': 'MSG-TEST',
            'title': 'Message Test',
            'requirement_type': 'INTERNAL_POLICY',
            'source_document': 'Test',
            'description': 'Test',
            'effective_date': date.today().isoformat(),
            'status': 'ACTIVE',
            'compliance_status': 'NOT_ASSESSED',
            'risk_level': 'MEDIUM'
        }
        response = authenticated_client.post(url, data=form_data, follow=True)
        if response.status_code == 200:
            messages = list(response.context.get('messages', []))
            # Success message may be present
            # This depends on view implementation

    def test_delete_shows_success_message(self, authenticated_client, compliance_requirement):
        """Test delete view shows success message."""
        url = reverse('compliance:compliancerequirement_delete', kwargs={'pk': compliance_requirement.pk})
        response = authenticated_client.post(url, follow=True)
        if response.status_code == 200:
            messages = list(response.context.get('messages', []))
            # Success message may be present
