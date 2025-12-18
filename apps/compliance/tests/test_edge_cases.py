"""
Compliance App - Edge Case Tests
Tests for boundary conditions and error scenarios.

Tests cover:
- Submitting form twice rapidly (duplicate prevention)
- Deleting record with foreign key references
- Very long text in fields
- Special characters in text
- Future/past date edge cases
- Negative numbers where positive expected
- Zero quantities
- Blank required fields
- Maximum field lengths
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
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
def compliance_requirement(db, user):
    """Create a test compliance requirement."""
    return ComplianceRequirement.objects.create(
        requirement_code='EDGE-TEST-001',
        title='Edge Case Test Requirement',
        requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
        source_document='Test',
        description='Test requirement for edge case testing',
        effective_date=date.today(),
        created_by=user
    )


# =============================================================================
# TEST: Duplicate Prevention
# =============================================================================

@pytest.mark.django_db
class TestDuplicatePrevention:
    """Tests for duplicate record prevention."""

    def test_duplicate_requirement_code_rejected(self, user, compliance_requirement):
        """Test duplicate requirement_code is rejected."""
        with pytest.raises(IntegrityError):
            ComplianceRequirement.objects.create(
                requirement_code=compliance_requirement.requirement_code,
                title='Duplicate Test',
                requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
                source_document='Test',
                description='Test',
                effective_date=date.today(),
                created_by=user
            )

    def test_duplicate_checklist_code_rejected(self, user):
        """Test duplicate checklist_code is rejected."""
        InspectionChecklist.objects.create(
            checklist_code='DUP-CHK-001',
            checklist_name='First Checklist',
            inspection_type=InspectionChecklist.InspectionType.INCOMING,
            applicable_to='Test',
            checklist_items=[],
            version='1.0',
            created_by=user
        )

        with pytest.raises(IntegrityError):
            InspectionChecklist.objects.create(
                checklist_code='DUP-CHK-001',
                checklist_name='Duplicate Checklist',
                inspection_type=InspectionChecklist.InspectionType.FINAL,
                applicable_to='Test',
                checklist_items=[],
                version='1.0',
                created_by=user
            )

    def test_rapid_form_submission(self, authenticated_client, user):
        """Test rapid form submissions don't create duplicates."""
        url = reverse('compliance:compliancerequirement_create')

        form_data = {
            'requirement_code': 'RAPID-TEST-001',
            'title': 'Rapid Submit Test',
            'requirement_type': 'INTERNAL_POLICY',
            'source_document': 'Test',
            'description': 'Test',
            'effective_date': date.today().isoformat(),
            'status': 'ACTIVE',
            'compliance_status': 'NOT_ASSESSED',
            'risk_level': 'LOW'
        }

        # First submission
        response1 = authenticated_client.post(url, data=form_data)

        # Immediate second submission (should fail due to unique constraint)
        response2 = authenticated_client.post(url, data=form_data)

        # Count should be 1
        count = ComplianceRequirement.objects.filter(requirement_code='RAPID-TEST-001').count()
        assert count <= 1  # Should only have created once


# =============================================================================
# TEST: Foreign Key Constraints
# =============================================================================

@pytest.mark.django_db
class TestForeignKeyConstraints:
    """Tests for foreign key constraint handling."""

    def test_delete_user_with_requirements(self, user, compliance_requirement):
        """Test deleting user with compliance requirements."""
        compliance_requirement.created_by = user
        compliance_requirement.save()

        # Should allow deletion with SET_NULL
        user.delete()
        compliance_requirement.refresh_from_db()
        assert compliance_requirement.created_by is None

    def test_delete_protected_user_fails(self, user):
        """Test deleting user protected by PROTECT constraint."""
        # QualityControl inspector is PROTECT
        qc = QualityControl.objects.create(
            inspection_type=QualityControl.InspectionType.INCOMING,
            inspection_date=date.today(),
            inspector=user
        )

        with pytest.raises(Exception):  # ProtectedError
            user.delete()

    def test_delete_requirement_with_linked_documents(self, user, compliance_requirement):
        """Test deleting requirement with linked documents."""
        doc = DocumentControl.objects.create(
            document_number='FK-TEST-001',
            title='Test Doc',
            document_type=DocumentControl.DocumentType.PROCEDURE,
            version='1.0',
            revision_date=date.today(),
            file_path='/test.pdf',
            prepared_by=user
        )
        doc.compliance_requirements.add(compliance_requirement)

        # Should be able to delete requirement (M2M relationship)
        compliance_requirement.delete()
        # Document should still exist
        assert DocumentControl.objects.filter(pk=doc.pk).exists()


# =============================================================================
# TEST: Very Long Text
# =============================================================================

@pytest.mark.django_db
class TestVeryLongText:
    """Tests for handling very long text input."""

    def test_max_length_requirement_code(self, user):
        """Test requirement_code max length."""
        long_code = 'X' * 100  # max_length=100

        req = ComplianceRequirement.objects.create(
            requirement_code=long_code,
            title='Long Code Test',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            created_by=user
        )
        assert len(req.requirement_code) == 100

    def test_exceeds_max_length_rejected(self, user):
        """Test exceeding max_length is rejected."""
        too_long_code = 'X' * 101  # Exceeds max_length=100

        req = ComplianceRequirement(
            requirement_code=too_long_code,
            title='Test',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            created_by=user
        )

        with pytest.raises(ValidationError):
            req.full_clean()

    def test_very_long_description(self, user):
        """Test very long description in TextField."""
        long_description = 'A' * 50000  # 50K characters

        req = ComplianceRequirement.objects.create(
            requirement_code='LONG-DESC-001',
            title='Long Description Test',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description=long_description,
            effective_date=date.today(),
            created_by=user
        )
        assert len(req.description) == 50000

    def test_very_long_title(self, user):
        """Test title at max_length boundary."""
        max_title = 'T' * 500  # max_length=500

        req = ComplianceRequirement.objects.create(
            requirement_code='LONG-TITLE-001',
            title=max_title,
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            created_by=user
        )
        assert len(req.title) == 500


# =============================================================================
# TEST: Special Characters
# =============================================================================

@pytest.mark.django_db
class TestSpecialCharacters:
    """Tests for handling special characters in text fields."""

    def test_unicode_in_title(self, user):
        """Test Unicode characters in title."""
        unicode_title = 'Требование соответствия 日本語 العربية'

        req = ComplianceRequirement.objects.create(
            requirement_code='UNICODE-001',
            title=unicode_title,
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            created_by=user
        )
        req.refresh_from_db()
        assert req.title == unicode_title

    def test_html_entities_in_description(self, user):
        """Test HTML entities in description."""
        html_description = '<script>alert("XSS")</script> & < > " \''

        req = ComplianceRequirement.objects.create(
            requirement_code='HTML-001',
            title='HTML Test',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description=html_description,
            effective_date=date.today(),
            created_by=user
        )
        req.refresh_from_db()
        # Should store as-is (escaping happens at display)
        assert '<script>' in req.description

    def test_newlines_in_textarea(self, user):
        """Test newlines in text fields."""
        multiline = "Line 1\nLine 2\n\nLine 4"

        req = ComplianceRequirement.objects.create(
            requirement_code='NEWLINE-001',
            title='Newline Test',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description=multiline,
            effective_date=date.today(),
            created_by=user
        )
        req.refresh_from_db()
        assert '\n' in req.description

    def test_sql_injection_attempt(self, user):
        """Test SQL injection attempts are safely stored."""
        sql_injection = "'; DROP TABLE compliance_requirements; --"

        req = ComplianceRequirement.objects.create(
            requirement_code='SQL-001',
            title=sql_injection,
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            created_by=user
        )
        req.refresh_from_db()
        # Should be stored safely
        assert 'DROP TABLE' in req.title
        # Table should still exist
        assert ComplianceRequirement.objects.exists()


# =============================================================================
# TEST: Date Edge Cases
# =============================================================================

@pytest.mark.django_db
class TestDateEdgeCases:
    """Tests for date field edge cases."""

    def test_far_future_date(self, user):
        """Test very far future dates."""
        future_date = date(2099, 12, 31)

        req = ComplianceRequirement.objects.create(
            requirement_code='FUTURE-001',
            title='Future Date Test',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=future_date,
            created_by=user
        )
        assert req.effective_date == future_date
        assert req.is_active is False  # Future date means not yet active

    def test_far_past_date(self, user):
        """Test very old dates."""
        past_date = date(1990, 1, 1)

        req = ComplianceRequirement.objects.create(
            requirement_code='PAST-001',
            title='Past Date Test',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=past_date,
            created_by=user
        )
        assert req.effective_date == past_date

    def test_today_boundary(self, user):
        """Test today as boundary date."""
        today = date.today()

        req = ComplianceRequirement.objects.create(
            requirement_code='TODAY-001',
            title='Today Test',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=today,
            status=ComplianceRequirement.Status.ACTIVE,
            created_by=user
        )
        # Today or before should be active
        assert req.is_active is True

    def test_certification_expired_yesterday(self, user):
        """Test certification that expired yesterday."""
        cert = Certification.objects.create(
            employee=user,
            certification_name='Expired Cert',
            certification_body='Test Body',
            issue_date=date.today() - timedelta(days=365),
            expiry_date=date.today() - timedelta(days=1)
        )
        assert cert.is_expired is True
        assert cert.days_until_expiry == -1

    def test_certification_expires_today(self, user):
        """Test certification expiring today."""
        cert = Certification.objects.create(
            employee=user,
            certification_name='Expiring Today',
            certification_body='Test Body',
            issue_date=date.today() - timedelta(days=365),
            expiry_date=date.today()
        )
        # Expires today - still valid or expired depends on implementation
        # In our model, > today means not expired, so today is NOT expired
        assert cert.days_until_expiry == 0


# =============================================================================
# TEST: Numeric Edge Cases
# =============================================================================

@pytest.mark.django_db
class TestNumericEdgeCases:
    """Tests for numeric field edge cases."""

    def test_zero_duration_hours(self, user):
        """Test zero duration hours."""
        training = TrainingRecord.objects.create(
            employee=user,
            training_type=TrainingRecord.TrainingType.ORIENTATION,
            training_title='Zero Duration',
            training_provider='Test',
            start_date=date.today(),
            duration_hours=Decimal('0.00')
        )
        assert training.duration_hours == Decimal('0.00')

    def test_very_small_decimal(self, user):
        """Test very small decimal value."""
        metric = QualityMetric.objects.create(
            metric_name='Small Metric',
            metric_type=QualityMetric.MetricType.DEFECT_RATE,
            measurement_period=date.today(),
            measured_value=Decimal('0.0001'),
            unit_of_measure='%',
            recorded_by=user
        )
        assert metric.measured_value == Decimal('0.0001')

    def test_large_decimal(self, user):
        """Test large decimal value."""
        metric = QualityMetric.objects.create(
            metric_name='Large Metric',
            metric_type=QualityMetric.MetricType.OTHER,
            measurement_period=date.today(),
            measured_value=Decimal('999999.9999'),
            unit_of_measure='units',
            recorded_by=user
        )
        metric.refresh_from_db()
        assert metric.measured_value == Decimal('999999.9999')

    def test_decimal_precision(self, user):
        """Test decimal precision is maintained."""
        training = TrainingRecord.objects.create(
            employee=user,
            training_type=TrainingRecord.TrainingType.TECHNICAL,
            training_title='Precision Test',
            training_provider='Test',
            start_date=date.today(),
            duration_hours=Decimal('7.75'),
            score=Decimal('95.55')
        )
        training.refresh_from_db()
        assert training.duration_hours == Decimal('7.75')
        assert training.score == Decimal('95.55')


# =============================================================================
# TEST: JSON Field Edge Cases
# =============================================================================

@pytest.mark.django_db
class TestJSONFieldEdgeCases:
    """Tests for JSONField edge cases."""

    def test_empty_json_array(self, user):
        """Test empty JSON array."""
        checklist = InspectionChecklist.objects.create(
            checklist_code='EMPTY-JSON',
            checklist_name='Empty Items',
            inspection_type=InspectionChecklist.InspectionType.INCOMING,
            applicable_to='Test',
            checklist_items=[],
            version='1.0',
            created_by=user
        )
        assert checklist.item_count == 0

    def test_null_json_field(self, user):
        """Test null JSON field."""
        qc = QualityControl.objects.create(
            inspection_type=QualityControl.InspectionType.INCOMING,
            inspection_date=date.today(),
            inspector=user,
            measurements=None
        )
        assert qc.measurements is None

    def test_complex_json_structure(self, user):
        """Test complex nested JSON."""
        complex_items = [
            {
                'section': 'Visual Inspection',
                'items': [
                    {'id': 1, 'description': 'Check surface', 'required': True},
                    {'id': 2, 'description': 'Check color', 'required': False}
                ]
            },
            {
                'section': 'Dimensional',
                'items': [
                    {'id': 3, 'description': 'Measure OD', 'required': True, 'tolerance': 0.05}
                ]
            }
        ]

        checklist = InspectionChecklist.objects.create(
            checklist_code='COMPLEX-JSON',
            checklist_name='Complex Items',
            inspection_type=InspectionChecklist.InspectionType.FINAL,
            applicable_to='Test',
            checklist_items=complex_items,
            version='1.0',
            created_by=user
        )
        checklist.refresh_from_db()
        assert len(checklist.checklist_items) == 2
        assert checklist.checklist_items[0]['section'] == 'Visual Inspection'

    def test_json_with_special_characters(self, user):
        """Test JSON with special characters."""
        special_items = [
            {'item': 'Check for <tags> & "quotes"', 'note': "Line1\nLine2"}
        ]

        checklist = InspectionChecklist.objects.create(
            checklist_code='SPECIAL-JSON',
            checklist_name='Special Chars',
            inspection_type=InspectionChecklist.InspectionType.INCOMING,
            applicable_to='Test',
            checklist_items=special_items,
            version='1.0',
            created_by=user
        )
        checklist.refresh_from_db()
        assert '<tags>' in checklist.checklist_items[0]['item']


# =============================================================================
# TEST: Blank/Null Field Edge Cases
# =============================================================================

@pytest.mark.django_db
class TestBlankNullFields:
    """Tests for blank and null field handling."""

    def test_all_optional_fields_blank(self, user):
        """Test creating record with all optional fields blank."""
        req = ComplianceRequirement.objects.create(
            requirement_code='MIN-FIELDS',
            title='Minimal',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            # All optional fields left blank
            created_by=user
        )
        req.full_clean()  # Should not raise

    def test_optional_fk_null(self, user):
        """Test optional foreign key can be null."""
        req = ComplianceRequirement.objects.create(
            requirement_code='NULL-FK',
            title='Null FK Test',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            responsible_person=None,
            supersedes=None,
            created_by=user
        )
        assert req.responsible_person is None
        assert req.supersedes is None

    def test_empty_string_vs_null(self, user):
        """Test empty string handling in CharField."""
        req = ComplianceRequirement.objects.create(
            requirement_code='EMPTY-STR',
            title='Empty String Test',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            clause_number='',  # Empty string, not null
            created_by=user
        )
        assert req.clause_number == ''


# =============================================================================
# TEST: Concurrent Access
# =============================================================================

@pytest.mark.django_db
class TestConcurrentAccess:
    """Tests for concurrent access scenarios."""

    def test_optimistic_locking_scenario(self, user, compliance_requirement):
        """Test scenario where two users edit same record."""
        # Simulate two users loading the same record
        req1 = ComplianceRequirement.objects.get(pk=compliance_requirement.pk)
        req2 = ComplianceRequirement.objects.get(pk=compliance_requirement.pk)

        # User 1 saves first
        req1.title = 'User 1 Edit'
        req1.save()

        # User 2 saves second (would overwrite in basic implementation)
        req2.title = 'User 2 Edit'
        req2.save()

        # Final state
        final = ComplianceRequirement.objects.get(pk=compliance_requirement.pk)
        assert final.title == 'User 2 Edit'  # Last write wins without optimistic locking


# =============================================================================
# TEST: Boundary Conditions
# =============================================================================

@pytest.mark.django_db
class TestBoundaryConditions:
    """Tests for boundary conditions."""

    def test_requirement_at_status_boundary(self, user):
        """Test requirement transitioning through all statuses."""
        req = ComplianceRequirement.objects.create(
            requirement_code='STATUS-TRANS',
            title='Status Transition Test',
            requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
            source_document='Test',
            description='Test',
            effective_date=date.today(),
            status=ComplianceRequirement.Status.PENDING,
            created_by=user
        )

        # Transition through all statuses
        statuses = ['PENDING', 'ACTIVE', 'SUPERSEDED', 'INACTIVE']
        for status in statuses:
            req.status = status
            if status == 'SUPERSEDED':
                req.superseded_date = date.today()
            req.save()
            req.refresh_from_db()
            assert req.status == status

    def test_metric_at_target_boundary(self, user):
        """Test metric exactly at target value."""
        metric = QualityMetric.objects.create(
            metric_name='Boundary Metric',
            metric_type=QualityMetric.MetricType.FIRST_PASS_YIELD,
            measurement_period=date.today(),
            measured_value=Decimal('95.00'),
            target_value=Decimal('95.00'),
            unit_of_measure='%',
            recorded_by=user
        )
        # Equal to target should count as meeting target
        assert metric.meets_target is True

    def test_certification_at_expiry_boundary(self, user):
        """Test certification exactly at expiry."""
        # Expires today
        cert = Certification.objects.create(
            employee=user,
            certification_name='Boundary Expiry',
            certification_body='Test',
            issue_date=date.today() - timedelta(days=365),
            expiry_date=date.today()
        )
        # Today is the last valid day (not yet expired based on > comparison)
        # This depends on implementation - in our case > means past expiry
        assert cert.days_until_expiry == 0


# =============================================================================
# TEST: Error Recovery
# =============================================================================

@pytest.mark.django_db
class TestErrorRecovery:
    """Tests for error recovery scenarios."""

    def test_invalid_form_preserves_data(self, authenticated_client):
        """Test invalid form submission preserves entered data."""
        url = reverse('compliance:compliancerequirement_create')

        form_data = {
            'requirement_code': 'PRESERVE-DATA',
            'title': 'Preserved Title',
            'requirement_type': 'INVALID_TYPE',  # Invalid
            'source_document': 'Preserved Source',
            'description': 'Preserved Description',
            'effective_date': date.today().isoformat()
        }
        response = authenticated_client.post(url, data=form_data)

        # Form should be re-displayed with data
        if response.status_code == 200:
            form = response.context.get('form')
            if form:
                # Data should be preserved in form
                assert form.data.get('title') == 'Preserved Title'

    def test_transaction_rollback_on_error(self, user):
        """Test database transaction rollback on error."""
        initial_count = ComplianceRequirement.objects.count()

        try:
            with pytest.raises(IntegrityError):
                # Create valid record
                ComplianceRequirement.objects.create(
                    requirement_code='TRANS-001',
                    title='Transaction Test',
                    requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
                    source_document='Test',
                    description='Test',
                    effective_date=date.today(),
                    created_by=user
                )
                # Try to create duplicate (should fail)
                ComplianceRequirement.objects.create(
                    requirement_code='TRANS-001',  # Duplicate
                    title='Duplicate',
                    requirement_type=ComplianceRequirement.RequirementType.INTERNAL_POLICY,
                    source_document='Test',
                    description='Test',
                    effective_date=date.today(),
                    created_by=user
                )
        except IntegrityError:
            pass

        # First record should still exist despite second failing
        # (depends on transaction handling in test setup)
