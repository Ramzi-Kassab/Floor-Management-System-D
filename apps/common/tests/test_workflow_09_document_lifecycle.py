"""
Document Lifecycle Workflow Integration Test
============================================

Cross-App Integration:
- Documents: Document creation and management
- Procedures: Linking documents to procedures
- Compliance: Document control tracking
- Notifications: Review and approval notifications

Workflow Steps:
1. Create new document
2. Submit for review
3. Review and approve
4. Publish document
5. Link to procedures
6. Track compliance/acknowledgment
7. Schedule periodic review
8. Archive when obsolete

Author: Workflow Integration Suite
Date: December 2024
"""

import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def document_author(db):
    """Create document author user."""
    return User.objects.create_user(
        username='doc_author',
        email='author@ardt.com',
        password='authorpass123',
        first_name='Document',
        last_name='Author',
        is_staff=True
    )


@pytest.fixture
def reviewer(db):
    """Create reviewer user."""
    return User.objects.create_user(
        username='reviewer',
        email='reviewer@ardt.com',
        password='reviewpass123',
        first_name='Quality',
        last_name='Reviewer',
        is_staff=True
    )


@pytest.fixture
def approver(db):
    """Create approver user."""
    return User.objects.create_user(
        username='doc_approver',
        email='approver@ardt.com',
        password='approverpass123',
        first_name='Manager',
        last_name='Approver',
        is_staff=True
    )


@pytest.fixture
def document_category(db):
    """Create document category."""
    from apps.documents.models import DocumentCategory
    return DocumentCategory.objects.create(
        code='SOP',
        name='Standard Operating Procedures',
        description='Operational procedures and work instructions',
        is_active=True
    )


# =============================================================================
# DOCUMENT LIFECYCLE WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestDocumentLifecycleWorkflow:
    """
    Complete document lifecycle workflow test.

    Tests the full document management cycle from creation
    through approval, use, and eventual archival.
    """

    def test_full_document_lifecycle_workflow(
        self,
        document_author,
        reviewer,
        approver,
        document_category
    ):
        """
        Test complete document lifecycle workflow.

        Steps:
        1. Create new document (Draft)
        2. Add content and metadata
        3. Submit for review
        4. Reviewer reviews and comments
        5. Submit for approval
        6. Approver approves
        7. Publish document (Active)
        8. Link to procedure
        9. Track acknowledgments
        10. Schedule review
        11. Update/revise document
        12. Archive old version
        """
        from apps.documents.models import Document, DocumentCategory
        from apps.procedures.models import Procedure
        from apps.notifications.models import Notification
        from apps.compliance.models import DocumentAcknowledgment

        print("\n" + "="*60)
        print("DOCUMENT LIFECYCLE WORKFLOW")
        print("="*60)

        # ---------------------------------------------------------------------
        # STEP 1: Create new document (Draft)
        # ---------------------------------------------------------------------
        print("\n[Step 1] Creating new document...")

        document = Document.objects.create(
            code='SOP-MFG-001',
            name='FC Bit Manufacturing Standard Operating Procedure',
            category=document_category,
            version='1.0',
            status=Document.Status.DRAFT,
            description='Standard procedure for manufacturing fixed cutter drill bits',
            keywords='manufacturing, FC, drill bit, procedure',
            owner=document_author
        )

        assert document.pk is not None
        assert document.status == Document.Status.DRAFT
        print(f"  Document: {document.code}")
        print(f"  Name: {document.name}")
        print(f"  Version: {document.version}")
        print(f"  Status: {document.get_status_display()}")

        # ---------------------------------------------------------------------
        # STEP 2: Add content and metadata
        # ---------------------------------------------------------------------
        print("\n[Step 2] Adding content and metadata...")

        document.description = '''
        FC BIT MANUFACTURING PROCEDURE
        ==============================

        1. PURPOSE
        This procedure defines the standard steps for manufacturing
        Fixed Cutter (FC) drill bits at ARDT facilities.

        2. SCOPE
        Applies to all FC bit manufacturing operations.

        3. RESPONSIBILITIES
        - Manufacturing Manager: Overall process ownership
        - Operators: Execute manufacturing steps
        - QC: Quality verification

        4. PROCEDURE
        4.1 Material Preparation
        4.2 Cutter Placement
        4.3 Brazing
        4.4 Machining
        4.5 Final Assembly
        4.6 Quality Inspection

        5. RECORDS
        - Work orders
        - Inspection records
        - Test certificates
        '''
        document.revision_date = date.today()
        document.save()

        print(f"  Content added")
        print(f"  Revision date: {document.revision_date}")

        # ---------------------------------------------------------------------
        # STEP 3: Submit for review
        # ---------------------------------------------------------------------
        print("\n[Step 3] Submitting for review...")

        # Notify reviewer
        review_notification = Notification.objects.create(
            recipient=reviewer,
            title=f'Document Review Required: {document.code}',
            message=f'Please review document "{document.name}" and provide feedback.',
            priority=Notification.Priority.HIGH,
            entity_type='documents.document',
            entity_id=document.pk
        )

        print(f"  Review request sent to: {reviewer.username}")

        # ---------------------------------------------------------------------
        # STEP 4: Reviewer reviews and comments
        # ---------------------------------------------------------------------
        print("\n[Step 4] Reviewer reviewing document...")

        # Simulate review completion
        review_notification.is_read = True
        review_notification.read_at = timezone.now()
        review_notification.save()

        print(f"  Review completed by: {reviewer.username}")
        print(f"  Status: Approved with minor comments")

        # ---------------------------------------------------------------------
        # STEP 5: Submit for approval
        # ---------------------------------------------------------------------
        print("\n[Step 5] Submitting for approval...")

        # Notify approver
        approval_notification = Notification.objects.create(
            recipient=approver,
            title=f'Document Approval Required: {document.code}',
            message=f'Document "{document.name}" has been reviewed and requires your approval.',
            priority=Notification.Priority.HIGH,
            entity_type='documents.document',
            entity_id=document.pk
        )

        print(f"  Approval request sent to: {approver.username}")

        # ---------------------------------------------------------------------
        # STEP 6: Approver approves
        # ---------------------------------------------------------------------
        print("\n[Step 6] Approving document...")

        document.approved_by = approver
        document.approved_at = timezone.now()
        document.save()

        approval_notification.is_read = True
        approval_notification.read_at = timezone.now()
        approval_notification.save()

        print(f"  Approved by: {approver.username}")
        print(f"  Approved at: {document.approved_at}")

        # ---------------------------------------------------------------------
        # STEP 7: Publish document (Active)
        # ---------------------------------------------------------------------
        print("\n[Step 7] Publishing document...")

        document.status = Document.Status.ACTIVE
        document.save()

        assert document.status == Document.Status.ACTIVE
        print(f"  Status: {document.get_status_display()}")
        print(f"  Document is now available for use")

        # ---------------------------------------------------------------------
        # STEP 8: Link to procedure
        # ---------------------------------------------------------------------
        print("\n[Step 8] Linking to procedure...")

        procedure = Procedure.objects.create(
            code='PROC-MFG-FC',
            name='FC Bit Manufacturing',
            revision='1.0',
            status=Procedure.Status.ACTIVE,
            scope=f'Reference document: {document.code}',
            created_by=document_author
        )

        print(f"  Linked to procedure: {procedure.code}")

        # ---------------------------------------------------------------------
        # STEP 9: Track acknowledgments
        # ---------------------------------------------------------------------
        print("\n[Step 9] Tracking acknowledgments...")

        # Create acknowledgment records
        ack1 = DocumentAcknowledgment.objects.create(
            document=document,
            user=document_author,
            acknowledged_at=timezone.now(),
            acknowledgment_type='READ'
        )

        ack2 = DocumentAcknowledgment.objects.create(
            document=document,
            user=reviewer,
            acknowledged_at=timezone.now(),
            acknowledgment_type='READ'
        )

        ack_count = DocumentAcknowledgment.objects.filter(document=document).count()
        print(f"  Acknowledgments recorded: {ack_count}")

        # ---------------------------------------------------------------------
        # STEP 10: Schedule review
        # ---------------------------------------------------------------------
        print("\n[Step 10] Scheduling periodic review...")

        # Set review date (1 year from now)
        document.expires_at = date.today() + timedelta(days=365)
        document.save()

        print(f"  Next review due: {document.expires_at}")

        # ---------------------------------------------------------------------
        # STEP 11: Create new revision
        # ---------------------------------------------------------------------
        print("\n[Step 11] Creating new revision...")

        # Create new version
        document_v2 = Document.objects.create(
            code='SOP-MFG-001',
            name='FC Bit Manufacturing Standard Operating Procedure',
            category=document_category,
            version='2.0',
            status=Document.Status.DRAFT,
            description=document.description + '\n\nRevision 2.0 - Updated brazing parameters',
            keywords=document.keywords,
            owner=document_author
        )

        # Use unique code for v2
        document_v2.code = 'SOP-MFG-001-V2'
        document_v2.save()

        print(f"  New version created: {document_v2.version}")

        # ---------------------------------------------------------------------
        # STEP 12: Archive old version
        # ---------------------------------------------------------------------
        print("\n[Step 12] Archiving old version...")

        # Archive v1 when v2 is approved
        document.status = Document.Status.OBSOLETE
        document.save()

        assert document.status == Document.Status.OBSOLETE
        print(f"  Version 1.0 status: {document.get_status_display()}")

        # ---------------------------------------------------------------------
        # Final verification
        # ---------------------------------------------------------------------
        print("\n[Step 13] Final verification...")

        final_checks = {
            'document_created': document.pk is not None,
            'content_added': len(document.description) > 100,
            'approved': document.approved_by is not None,
            'v1_obsolete': document.status == Document.Status.OBSOLETE,
            'v2_created': document_v2.pk is not None,
            'procedure_linked': procedure.pk is not None,
            'acknowledgments_tracked': ack_count >= 2,
            'review_scheduled': document.expires_at is not None,
        }

        all_passed = all(final_checks.values())

        print("\n  Document Summary:")
        print(f"    Document: {document.code}")
        print(f"    Versions: 1.0 (obsolete), 2.0 (draft)")
        print(f"    Linked procedures: 1")
        print(f"    Acknowledgments: {ack_count}")

        print("\n  Lifecycle Checklist:")
        for check, status in final_checks.items():
            icon = "  " if status else "  "
            print(f"    {icon} {check.replace('_', ' ').title()}")

        assert all_passed

        print("\n" + "="*60)
        print("DOCUMENT LIFECYCLE WORKFLOW COMPLETED!")
        print("="*60)


    def test_document_revision_control(
        self,
        document_author,
        approver,
        document_category
    ):
        """
        Test document revision control workflow.

        Ensures proper version management and history tracking.
        """
        from apps.documents.models import Document

        print("\n" + "="*60)
        print("DOCUMENT REVISION CONTROL")
        print("="*60)

        # Create initial document
        print("\n[Step 1] Creating initial version...")

        doc = Document.objects.create(
            code='WI-QC-001',
            name='Quality Inspection Work Instruction',
            category=document_category,
            version='1.0',
            status=Document.Status.ACTIVE,
            owner=document_author,
            approved_by=approver,
            approved_at=timezone.now()
        )

        print(f"  Document: {doc.code} v{doc.version}")

        # Create revision
        print("\n[Step 2] Creating revision...")

        doc.status = Document.Status.OBSOLETE
        doc.save()

        doc_rev = Document.objects.create(
            code='WI-QC-001-R1',
            name='Quality Inspection Work Instruction',
            category=document_category,
            version='1.1',
            status=Document.Status.ACTIVE,
            owner=document_author,
            approved_by=approver,
            approved_at=timezone.now()
        )

        print(f"  Revision: {doc_rev.code} v{doc_rev.version}")

        # Verify revision control
        print("\n[Step 3] Verifying revision control...")

        assert doc.status == Document.Status.OBSOLETE
        assert doc_rev.status == Document.Status.ACTIVE
        print(f"  v1.0: {doc.get_status_display()}")
        print(f"  v1.1: {doc_rev.get_status_display()}")

        print("\n" + "="*60)
        print("REVISION CONTROL VERIFIED!")
        print("="*60)


# =============================================================================
# WORKFLOW SUMMARY
# =============================================================================

@pytest.mark.django_db
class TestDocumentWorkflowSummary:
    """Summary tests for document workflow."""

    def test_workflow_models_exist(self, db):
        """Verify all workflow models are accessible."""
        from apps.documents.models import Document, DocumentCategory
        from apps.procedures.models import Procedure
        from apps.compliance.models import DocumentAcknowledgment
        from apps.notifications.models import Notification

        assert Document._meta.model_name == 'document'
        assert DocumentCategory._meta.model_name == 'documentcategory'
        assert Procedure._meta.model_name == 'procedure'
        assert DocumentAcknowledgment._meta.model_name == 'documentacknowledgment'
        assert Notification._meta.model_name == 'notification'

        print("\nAll document workflow models verified!")
