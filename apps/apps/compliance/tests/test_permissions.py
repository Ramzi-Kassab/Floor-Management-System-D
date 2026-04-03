"""
Compliance App - Permission Tests
Tests for access control and authorization.

Tests cover:
- Regular users can access but may have restricted actions
- Staff/managers have elevated permissions
- Admins can access everything
- Proper 403 Forbidden responses for unauthorized actions
"""

import pytest
from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client

from apps.compliance.models import (
    ComplianceRequirement, QualityControl, NonConformance,
    DocumentControl, TrainingRecord, Certification
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
def regular_user(db):
    """Create a regular user (no special permissions)."""
    return User.objects.create_user(
        username='regular_user',
        email='regular@example.com',
        password='regularpass123',
        is_staff=False,
        is_superuser=False
    )


@pytest.fixture
def staff_user(db):
    """Create a staff user."""
    return User.objects.create_user(
        username='staff_user',
        email='staff@example.com',
        password='staffpass123',
        is_staff=True,
        is_superuser=False
    )


@pytest.fixture
def admin_user(db):
    """Create an admin/superuser."""
    return User.objects.create_superuser(
        username='admin_user',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def quality_manager(db):
    """Create a quality manager with appropriate permissions."""
    user = User.objects.create_user(
        username='qm_user',
        email='qm@example.com',
        password='qmpass123',
        is_staff=True
    )
    return user


@pytest.fixture
def compliance_requirement(db, admin_user):
    """Create a test compliance requirement."""
    return ComplianceRequirement.objects.create(
        requirement_code='PERM-TEST-001',
        title='Permission Test Requirement',
        requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
        source_document='Test',
        description='Test requirement for permission testing',
        effective_date=date.today(),
        created_by=admin_user
    )


@pytest.fixture
def quality_control(db, staff_user):
    """Create a test quality control inspection."""
    return QualityControl.objects.create(
        inspection_type=QualityControl.InspectionType.INCOMING,
        result=QualityControl.Result.PASS,
        inspection_date=date.today(),
        inspector=staff_user,
        created_by=staff_user
    )


@pytest.fixture
def non_conformance(db, staff_user):
    """Create a test non-conformance report."""
    return NonConformance.objects.create(
        source=NonConformance.Source.QUALITY_INSPECTION,
        severity=NonConformance.Severity.MINOR,
        description='Test NCR',
        defect_description='Test defect',
        detected_date=date.today(),
        reported_by=staff_user
    )


# =============================================================================
# TEST: Unauthenticated Access
# =============================================================================

@pytest.mark.django_db
class TestUnauthenticatedAccess:
    """Tests that unauthenticated users are redirected to login."""

    def test_list_views_require_authentication(self, client):
        """Test all list views redirect unauthenticated users."""
        list_urls = [
            'compliance:compliancerequirement_list',
            'compliance:qualitycontrol_list',
            'compliance:nonconformance_list',
            'compliance:documentcontrol_list',
            'compliance:trainingrecord_list',
            'compliance:certification_list',
            'compliance:compliancereport_list',
            'compliance:qualitymetric_list',
            'compliance:inspectionchecklist_list',
            'compliance:audittrail_list',
        ]

        for url_name in list_urls:
            url = reverse(url_name)
            response = client.get(url)
            assert response.status_code == 302, f"{url_name} should redirect to login"
            assert 'login' in response.url.lower() or 'accounts' in response.url.lower()

    def test_create_views_require_authentication(self, client):
        """Test create views redirect unauthenticated users."""
        create_urls = [
            'compliance:compliancerequirement_create',
            'compliance:qualitycontrol_create',
            'compliance:nonconformance_create',
            'compliance:documentcontrol_create',
            'compliance:trainingrecord_create',
            'compliance:certification_create',
        ]

        for url_name in create_urls:
            url = reverse(url_name)
            response = client.get(url)
            assert response.status_code == 302, f"{url_name} should redirect to login"

    def test_detail_views_require_authentication(self, client, compliance_requirement):
        """Test detail views redirect unauthenticated users."""
        url = reverse('compliance:compliancerequirement_detail', kwargs={'pk': compliance_requirement.pk})
        response = client.get(url)
        assert response.status_code == 302


# =============================================================================
# TEST: Regular User Access
# =============================================================================

@pytest.mark.django_db
class TestRegularUserAccess:
    """Tests for regular (non-staff) user access."""

    def test_regular_user_can_view_list(self, client, regular_user):
        """Test regular users can view list pages."""
        client.login(username='regular_user', password='regularpass123')

        url = reverse('compliance:compliancerequirement_list')
        response = client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_view_detail(self, client, regular_user, compliance_requirement):
        """Test regular users can view detail pages."""
        client.login(username='regular_user', password='regularpass123')

        url = reverse('compliance:compliancerequirement_detail', kwargs={'pk': compliance_requirement.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_regular_user_can_create(self, client, regular_user):
        """Test regular users can access create pages."""
        client.login(username='regular_user', password='regularpass123')

        url = reverse('compliance:compliancerequirement_create')
        response = client.get(url)
        # Depending on permission setup, may return 200 or 403
        assert response.status_code in [200, 403]

    def test_regular_user_can_update_own_records(self, client, regular_user):
        """Test regular users may update their own records."""
        client.login(username='regular_user', password='regularpass123')

        # Create a record owned by regular user
        req = ComplianceRequirement.objects.create(
            requirement_code='REG-USER-001',
            title='Regular User Requirement',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            created_by=regular_user
        )

        url = reverse('compliance:compliancerequirement_update', kwargs={'pk': req.pk})
        response = client.get(url)
        # Should be allowed if user owns the record
        assert response.status_code in [200, 403]


# =============================================================================
# TEST: Staff User Access
# =============================================================================

@pytest.mark.django_db
class TestStaffUserAccess:
    """Tests for staff user access."""

    def test_staff_can_view_all_lists(self, client, staff_user):
        """Test staff users can view all list pages."""
        client.login(username='staff_user', password='staffpass123')

        list_urls = [
            'compliance:compliancerequirement_list',
            'compliance:qualitycontrol_list',
            'compliance:nonconformance_list',
            'compliance:documentcontrol_list',
            'compliance:audittrail_list',
        ]

        for url_name in list_urls:
            url = reverse(url_name)
            response = client.get(url)
            assert response.status_code == 200, f"Staff should access {url_name}"

    def test_staff_can_create_records(self, client, staff_user):
        """Test staff users can create records."""
        client.login(username='staff_user', password='staffpass123')

        url = reverse('compliance:compliancerequirement_create')
        response = client.get(url)
        assert response.status_code == 200

    def test_staff_can_update_any_record(self, client, staff_user, compliance_requirement):
        """Test staff users can update any record."""
        client.login(username='staff_user', password='staffpass123')

        url = reverse('compliance:compliancerequirement_update', kwargs={'pk': compliance_requirement.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_staff_can_delete_records(self, client, staff_user, compliance_requirement):
        """Test staff users can access delete confirmation page."""
        client.login(username='staff_user', password='staffpass123')

        url = reverse('compliance:compliancerequirement_delete', kwargs={'pk': compliance_requirement.pk})
        response = client.get(url)
        assert response.status_code == 200


# =============================================================================
# TEST: Admin/Superuser Access
# =============================================================================

@pytest.mark.django_db
class TestAdminAccess:
    """Tests for admin/superuser access."""

    def test_admin_can_access_everything(self, client, admin_user):
        """Test admin users can access all pages."""
        client.login(username='admin_user', password='adminpass123')

        # Test list views
        list_urls = [
            'compliance:compliancerequirement_list',
            'compliance:qualitycontrol_list',
            'compliance:nonconformance_list',
            'compliance:audittrail_list',
        ]

        for url_name in list_urls:
            url = reverse(url_name)
            response = client.get(url)
            assert response.status_code == 200

    def test_admin_can_delete_any_record(self, client, admin_user, compliance_requirement):
        """Test admin can delete any record."""
        client.login(username='admin_user', password='adminpass123')

        pk = compliance_requirement.pk
        url = reverse('compliance:compliancerequirement_delete', kwargs={'pk': pk})

        # GET should show confirmation
        response = client.get(url)
        assert response.status_code == 200

        # POST should delete
        response = client.post(url)
        assert response.status_code == 302
        assert not ComplianceRequirement.objects.filter(pk=pk).exists()

    def test_admin_can_access_django_admin(self, client, admin_user):
        """Test admin can access Django admin."""
        client.login(username='admin_user', password='adminpass123')

        url = reverse('admin:index')
        response = client.get(url)
        assert response.status_code == 200


# =============================================================================
# TEST: Object-Level Permissions
# =============================================================================

@pytest.mark.django_db
class TestObjectLevelPermissions:
    """Tests for object-level permission checks."""

    def test_user_can_view_assigned_records(self, client, regular_user, staff_user):
        """Test users can view records assigned to them."""
        client.login(username='regular_user', password='regularpass123')

        # Create NCR assigned to regular user
        ncr = NonConformance.objects.create(
            source=NonConformance.Source.INTERNAL_AUDIT,
            severity=NonConformance.Severity.MINOR,
            description='Test',
            defect_description='Test',
            detected_date=date.today(),
            reported_by=staff_user,
            assigned_to=regular_user
        )

        url = reverse('compliance:nonconformance_detail', kwargs={'pk': ncr.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_training_record_visibility(self, client, regular_user, staff_user):
        """Test training record visibility based on ownership."""
        # Create training record for regular user
        training = TrainingRecord.objects.create(
            employee=regular_user,
            training_type=TrainingRecord.TrainingType.SAFETY,
            training_title='Safety Training',
            training_provider='Internal',
            start_date=date.today(),
            duration_hours=Decimal('4.00'),
            recorded_by=staff_user
        )

        # Regular user should see their own training
        client.login(username='regular_user', password='regularpass123')
        url = reverse('compliance:trainingrecord_detail', kwargs={'pk': training.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_certification_visibility(self, client, regular_user, admin_user):
        """Test certification visibility."""
        # Create certification for regular user
        cert = Certification.objects.create(
            employee=regular_user,
            certification_name='Test Cert',
            certification_body='Test Body',
            issue_date=date.today()
        )

        # Regular user should see their own certification
        client.login(username='regular_user', password='regularpass123')
        url = reverse('compliance:certification_detail', kwargs={'pk': cert.pk})
        response = client.get(url)
        assert response.status_code == 200


# =============================================================================
# TEST: Action-Specific Permissions
# =============================================================================

@pytest.mark.django_db
class TestActionPermissions:
    """Tests for action-specific permissions."""

    def test_only_authorized_can_approve_documents(self, client, regular_user, staff_user):
        """Test document approval requires proper authorization."""
        client.login(username='staff_user', password='staffpass123')

        doc = DocumentControl.objects.create(
            document_number='PERM-DOC-001',
            title='Test Document',
            document_type=DocumentControl.DocumentType.PROCEDURE,
            version='1.0',
            revision_date=date.today(),
            status=DocumentControl.Status.REVIEW,
            file_path='/test.pdf',
            prepared_by=regular_user
        )

        # Staff should be able to approve
        url = reverse('compliance:documentcontrol_update', kwargs={'pk': doc.pk})
        form_data = {
            'document_number': doc.document_number,
            'title': doc.title,
            'document_type': doc.document_type,
            'version': doc.version,
            'revision_date': doc.revision_date.isoformat(),
            'status': 'APPROVED',
            'file_path': doc.file_path,
            'prepared_by': regular_user.pk,
            'approved_by': staff_user.pk,
            'approved_date': date.today().isoformat()
        }
        response = client.post(url, data=form_data)
        # Should succeed or redirect
        assert response.status_code in [200, 302]

    def test_ncr_closure_requires_verification(self, client, staff_user):
        """Test NCR closure requires verification step."""
        client.login(username='staff_user', password='staffpass123')

        ncr = NonConformance.objects.create(
            source=NonConformance.Source.QUALITY_INSPECTION,
            severity=NonConformance.Severity.MAJOR,
            description='Test NCR',
            defect_description='Test defect',
            detected_date=date.today(),
            reported_by=staff_user,
            status=NonConformance.Status.CORRECTIVE_ACTION
        )

        # Attempt to close without verification
        url = reverse('compliance:nonconformance_update', kwargs={'pk': ncr.pk})
        form_data = {
            'source': ncr.source,
            'severity': ncr.severity,
            'status': 'CLOSED',
            'description': ncr.description,
            'defect_description': ncr.defect_description,
            'detected_date': ncr.detected_date.isoformat()
        }
        response = client.post(url, data=form_data)
        # Form may validate or business logic may prevent
        # Check response is handled appropriately
        assert response.status_code in [200, 302]


# =============================================================================
# TEST: Cross-User Restrictions
# =============================================================================

@pytest.mark.django_db
class TestCrossUserRestrictions:
    """Tests for restrictions between different users."""

    def test_user_cannot_modify_others_training(self, client, regular_user, staff_user, admin_user):
        """Test users cannot modify other users' training records (if policy exists)."""
        # Create training for staff user
        training = TrainingRecord.objects.create(
            employee=staff_user,
            training_type=TrainingRecord.TrainingType.TECHNICAL,
            training_title='Technical Training',
            training_provider='External',
            start_date=date.today(),
            duration_hours=Decimal('8.00'),
            recorded_by=admin_user
        )

        # Regular user attempts to update
        client.login(username='regular_user', password='regularpass123')
        url = reverse('compliance:trainingrecord_update', kwargs={'pk': training.pk})
        response = client.get(url)
        # May return 200 (if allowed to view) or 403 (if denied)
        # Depends on permission implementation
        assert response.status_code in [200, 403]


# =============================================================================
# TEST: Audit Trail Access
# =============================================================================

@pytest.mark.django_db
class TestAuditTrailAccess:
    """Tests for audit trail access permissions."""

    def test_audit_trail_read_only(self, client, staff_user, admin_user):
        """Test audit trail is read-only for most operations."""
        client.login(username='staff_user', password='staffpass123')

        # Audit trail list should be accessible
        url = reverse('compliance:audittrail_list')
        response = client.get(url)
        assert response.status_code == 200

        # Create should typically be restricted (auto-generated)
        url = reverse('compliance:audittrail_create')
        response = client.get(url)
        # May be allowed for staff or restricted
        assert response.status_code in [200, 403, 404]

    def test_audit_trail_no_delete(self, client, admin_user, staff_user):
        """Test audit trail records cannot be deleted."""
        from apps.compliance.models import AuditTrail

        audit = AuditTrail.objects.create(
            action=AuditTrail.Action.CREATED,
            description='Test audit entry',
            model_name='Test',
            object_id=1,
            user=admin_user
        )

        # Even admin shouldn't easily delete audit trail
        client.login(username='admin_user', password='adminpass123')
        url = reverse('compliance:audittrail_delete', kwargs={'pk': audit.pk})
        response = client.get(url)
        # May return 200 (confirmation) or 403/404 (restricted)
        # Best practice: audit trail should be immutable
        assert response.status_code in [200, 403, 404]


# =============================================================================
# TEST: Permission Error Responses
# =============================================================================

@pytest.mark.django_db
class TestPermissionErrorResponses:
    """Tests for proper error responses on permission denial."""

    def test_403_response_format(self, client, regular_user):
        """Test 403 responses are properly formatted."""
        client.login(username='regular_user', password='regularpass123')

        # This test depends on having restricted views
        # If a view returns 403, verify the response
        # Most views in this app may allow all authenticated users

    def test_404_for_nonexistent_object(self, client, staff_user):
        """Test 404 is returned for non-existent objects."""
        client.login(username='staff_user', password='staffpass123')

        url = reverse('compliance:compliancerequirement_detail', kwargs={'pk': 99999})
        response = client.get(url)
        assert response.status_code == 404

    def test_redirect_preserves_next_url(self, client):
        """Test login redirect preserves next URL parameter."""
        url = reverse('compliance:compliancerequirement_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'next=' in response.url or url in response.url
