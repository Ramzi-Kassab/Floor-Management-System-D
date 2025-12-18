"""
Quality NCR Resolution Workflow Integration Test
================================================

Cross-App Integration:
- Quality: NCR creation and tracking
- Compliance: Corrective action management
- Procedures: Procedure updates
- HSSE: Safety-related quality issues
- Documents: Investigation reports

Workflow Steps:
1. Detect quality issue
2. Create Non-Conformance Report (NCR)
3. Investigate root cause
4. Document findings
5. Create corrective action
6. Update procedures if needed
7. Retrain staff (HSSE)
8. Verify effectiveness
9. Close NCR

Author: Workflow Integration Suite
Date: December 2024
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def qc_inspector(db):
    """Create QC inspector user."""
    return User.objects.create_user(
        username='qc_inspector',
        email='qc@ardt.com',
        password='qcpass123',
        first_name='QC',
        last_name='Inspector'
    )


@pytest.fixture
def quality_manager(db):
    """Create quality manager user."""
    return User.objects.create_user(
        username='quality_mgr',
        email='quality@ardt.com',
        password='qualitypass123',
        first_name='Quality',
        last_name='Manager',
        is_staff=True
    )


@pytest.fixture
def production_supervisor(db):
    """Create production supervisor user."""
    return User.objects.create_user(
        username='prod_super',
        email='production@ardt.com',
        password='prodpass123',
        first_name='Production',
        last_name='Supervisor',
        is_staff=True
    )


@pytest.fixture
def work_order_for_ncr(db, qc_inspector):
    """Create a work order for NCR testing."""
    from apps.workorders.models import WorkOrder, DrillBit

    drill_bit = DrillBit.objects.create(
        serial_number='FC-NCR-001',
        bit_type=DrillBit.BitType.FC,
        size=Decimal('8.500'),
        status=DrillBit.Status.IN_PRODUCTION,
        created_by=qc_inspector
    )

    return WorkOrder.objects.create(
        wo_number='WO-NCR-001',
        wo_type=WorkOrder.WOType.FC_REPAIR,
        drill_bit=drill_bit,
        status=WorkOrder.Status.QC_PENDING,
        created_by=qc_inspector
    )


# =============================================================================
# QUALITY NCR RESOLUTION WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestQualityNCRResolutionWorkflow:
    """
    Complete Quality NCR Resolution workflow test.

    Tests the full cycle from quality issue detection through
    corrective action implementation and NCR closure.
    """

    def test_full_ncr_resolution_workflow(
        self,
        qc_inspector,
        quality_manager,
        production_supervisor,
        work_order_for_ncr
    ):
        """
        Test complete NCR resolution workflow.

        Steps:
        1. Detect quality issue during inspection
        2. Create NCR
        3. Initial containment actions
        4. Investigate root cause
        5. Document findings
        6. Create corrective action plan
        7. Implement corrective actions
        8. Update procedures
        9. Verify effectiveness
        10. Close NCR
        """
        from apps.quality.models import Inspection, NCR
        from apps.compliance.models import NonConformance
        from apps.procedures.models import Procedure
        from apps.documents.models import Document, DocumentCategory
        from apps.notifications.models import Notification

        print("\n" + "="*60)
        print("QUALITY NCR RESOLUTION WORKFLOW")
        print("="*60)

        work_order = work_order_for_ncr

        # ---------------------------------------------------------------------
        # STEP 1: Detect quality issue during inspection
        # ---------------------------------------------------------------------
        print("\n[Step 1] Conducting inspection...")

        inspection = Inspection.objects.create(
            inspection_number='INSP-NCR-001',
            inspection_type=Inspection.InspectionType.FINAL,
            work_order=work_order,
            scheduled_date=date.today(),
            status=Inspection.Status.FAILED,
            inspected_by=qc_inspector,
            inspected_at=timezone.now(),
            pass_count=8,
            fail_count=2,
            notes='Dimensional check failed on 2 cutters',
            created_by=qc_inspector
        )

        assert inspection.status == Inspection.Status.FAILED
        print(f"  Inspection: {inspection.inspection_number}")
        print(f"  Result: {inspection.get_status_display()}")
        print(f"  Pass/Fail: {inspection.pass_count}/{inspection.fail_count}")

        # ---------------------------------------------------------------------
        # STEP 2: Create NCR
        # ---------------------------------------------------------------------
        print("\n[Step 2] Creating NCR...")

        ncr = NCR.objects.create(
            ncr_number='NCR-2024-001',
            work_order=work_order,
            inspection=inspection,
            title='Cutter dimensional non-conformance',
            description='''
            During final inspection of WO-NCR-001, two cutters were found
            to be out of dimensional specification:
            - Cutter #3: OD 12.52mm (spec: 12.50 +/- 0.01mm)
            - Cutter #7: OD 12.53mm (spec: 12.50 +/- 0.01mm)

            Both cutters exceed upper tolerance limit.
            ''',
            severity=NCR.Severity.MAJOR,
            status=NCR.Status.OPEN,
            detected_at=timezone.now(),
            detected_by=qc_inspector,
            detection_stage='Final Inspection'
        )

        assert ncr.pk is not None
        print(f"  NCR Number: {ncr.ncr_number}")
        print(f"  Severity: {ncr.get_severity_display()}")
        print(f"  Status: {ncr.get_status_display()}")

        # Notify quality manager
        ncr_notification = Notification.objects.create(
            recipient=quality_manager,
            title=f'NCR Created: {ncr.ncr_number}',
            message=f'New {ncr.get_severity_display()} NCR requires attention.',
            priority=Notification.Priority.HIGH,
            entity_type='quality.ncr',
            entity_id=ncr.pk
        )

        print(f"  Quality manager notified")

        # ---------------------------------------------------------------------
        # STEP 3: Initial containment actions
        # ---------------------------------------------------------------------
        print("\n[Step 3] Implementing containment...")

        # Update NCR with containment
        ncr.status = NCR.Status.INVESTIGATING
        ncr.save()

        # Mark affected items
        work_order.status = work_order.Status.ON_HOLD
        work_order.notes = f'On hold pending NCR {ncr.ncr_number} resolution'
        work_order.save()

        print(f"  Work order status: {work_order.get_status_display()}")
        print(f"  NCR status: {ncr.get_status_display()}")

        # ---------------------------------------------------------------------
        # STEP 4: Investigate root cause
        # ---------------------------------------------------------------------
        print("\n[Step 4] Investigating root cause...")

        # Perform investigation
        ncr.root_cause = '''
        ROOT CAUSE INVESTIGATION
        ========================

        5-Why Analysis:
        1. Why were cutters out of spec?
           - Cutters were oversized from supplier

        2. Why did oversized cutters get to final assembly?
           - Incoming inspection didn't catch the defect

        3. Why didn't incoming inspection catch it?
           - Sample-based inspection missed these pieces

        4. Why was sample inspection used?
           - Cost reduction measure implemented Q3

        5. Why wasn't 100% inspection maintained?
           - Procedure update without proper risk assessment

        ROOT CAUSE: Inadequate incoming inspection procedure
        '''
        ncr.investigated_by = quality_manager
        ncr.save()

        print(f"  Investigation completed")
        print(f"  Root cause: Inadequate incoming inspection")

        # ---------------------------------------------------------------------
        # STEP 5: Document findings
        # ---------------------------------------------------------------------
        print("\n[Step 5] Documenting findings...")

        doc_category, _ = DocumentCategory.objects.get_or_create(
            code='NCR-RPT',
            defaults={'name': 'NCR Reports', 'is_active': True}
        )

        investigation_report = Document.objects.create(
            code=f'DOC-{ncr.ncr_number}',
            name=f'Investigation Report - {ncr.ncr_number}',
            category=doc_category,
            version='1.0',
            status=Document.Status.ACTIVE,
            description=ncr.root_cause,
            owner=quality_manager,
            approved_by=quality_manager,
            approved_at=timezone.now()
        )

        print(f"  Report created: {investigation_report.code}")

        # ---------------------------------------------------------------------
        # STEP 6: Create corrective action plan (via NonConformance records)
        # ---------------------------------------------------------------------
        print("\n[Step 6] Creating corrective action plan...")

        # Immediate action
        ca1 = NonConformance.objects.create(
            ncr_number='CA-NCR-001',
            source=NonConformance.Source.QUALITY_INSPECTION,
            severity=NonConformance.Severity.MAJOR,
            status=NonConformance.Status.CORRECTIVE_ACTION,
            description='Return non-conforming cutters to supplier',
            defect_description='Return oversized cutters and request replacement.',
            detected_date=date.today(),
            reported_by=quality_manager,
            assigned_to=production_supervisor,
            target_completion_date=date.today() + timedelta(days=3),
            corrective_action='Return parts and get replacements'
        )

        # Preventive action
        ca2 = NonConformance.objects.create(
            ncr_number='CA-NCR-002',
            source=NonConformance.Source.QUALITY_INSPECTION,
            severity=NonConformance.Severity.MAJOR,
            status=NonConformance.Status.CORRECTIVE_ACTION,
            description='Update incoming inspection procedure',
            defect_description='Implement 100% dimensional inspection for critical components.',
            detected_date=date.today(),
            reported_by=quality_manager,
            assigned_to=quality_manager,
            target_completion_date=date.today() + timedelta(days=7),
            corrective_action='Revise incoming inspection procedure'
        )

        # Training action
        ca3 = NonConformance.objects.create(
            ncr_number='CA-NCR-003',
            source=NonConformance.Source.QUALITY_INSPECTION,
            severity=NonConformance.Severity.MINOR,
            status=NonConformance.Status.CORRECTIVE_ACTION,
            description='Inspector training on critical measurements',
            defect_description='Train all QC inspectors on critical dimension requirements.',
            detected_date=date.today(),
            reported_by=quality_manager,
            assigned_to=qc_inspector,
            target_completion_date=date.today() + timedelta(days=14),
            corrective_action='Conduct training for all inspectors'
        )

        print(f"  Corrective actions created: 3")
        print(f"    - {ca1.ncr_number}: {ca1.description}")
        print(f"    - {ca2.ncr_number}: {ca2.description}")
        print(f"    - {ca3.ncr_number}: {ca3.description}")

        # ---------------------------------------------------------------------
        # STEP 7: Implement corrective actions
        # ---------------------------------------------------------------------
        print("\n[Step 7] Implementing corrective actions...")

        # Complete CA1 - Return parts
        ca1.status = NonConformance.Status.CLOSED
        ca1.actual_completion_date = date.today()
        ca1.closed_by = production_supervisor
        ca1.closed_date = date.today()
        ca1.closure_notes = 'Non-conforming cutters returned. Replacements received and verified.'
        ca1.save()

        print(f"  {ca1.ncr_number}: Completed")

        # Complete CA2 - Update procedure
        ca2.status = NonConformance.Status.CLOSED
        ca2.actual_completion_date = date.today()
        ca2.closed_by = quality_manager
        ca2.closed_date = date.today()
        ca2.closure_notes = 'Incoming inspection procedure updated to require 100% inspection.'
        ca2.save()

        print(f"  {ca2.ncr_number}: Completed")

        # ---------------------------------------------------------------------
        # STEP 8: Update procedures
        # ---------------------------------------------------------------------
        print("\n[Step 8] Updating procedures...")

        procedure, _ = Procedure.objects.get_or_create(
            code='PROC-IQC-001',
            defaults={
                'name': 'Incoming Quality Control',
                'revision': '1.0',
                'status': Procedure.Status.DRAFT,
                'created_by': quality_manager
            }
        )

        # Update to new revision
        procedure.revision = '2.0'
        procedure.status = Procedure.Status.ACTIVE
        procedure.scope = 'Updated per NCR-2024-001: 100% inspection for critical components'
        procedure.save()

        print(f"  Procedure updated: {procedure.code} v{procedure.revision}")

        # ---------------------------------------------------------------------
        # STEP 9: Complete training and verify effectiveness
        # ---------------------------------------------------------------------
        print("\n[Step 9] Completing training and verification...")

        # Complete CA3 - Training
        ca3.status = NonConformance.Status.CLOSED
        ca3.actual_completion_date = date.today()
        ca3.closed_by = qc_inspector
        ca3.closed_date = date.today()
        ca3.closure_notes = 'All inspectors trained. Training records updated.'
        ca3.save()

        print(f"  {ca3.ncr_number}: Completed")

        # Verify effectiveness - update NCR status to pending verification
        ncr.status = NCR.Status.PENDING_VERIFICATION
        ncr.closure_notes = '''
        Effectiveness Verification:
        - Reviewed 5 subsequent incoming lots
        - 100% inspection performed on all
        - No non-conformances detected
        - Procedure changes effective
        '''
        ncr.save()

        print(f"  Effectiveness verified")

        # ---------------------------------------------------------------------
        # STEP 10: Close NCR
        # ---------------------------------------------------------------------
        print("\n[Step 10] Closing NCR...")

        # Determine disposition
        ncr.disposition = NCR.Disposition.REWORK
        ncr.disposition_notes = 'Replace non-conforming cutters with verified parts'
        ncr.status = NCR.Status.CLOSED
        ncr.closed_at = timezone.now()
        ncr.closed_by = quality_manager
        ncr.save()

        # Resume work order
        work_order.status = work_order.Status.IN_PROGRESS
        work_order.notes = f'Resumed after NCR {ncr.ncr_number} closure'
        work_order.save()

        assert ncr.status == NCR.Status.CLOSED
        print(f"  NCR Status: {ncr.get_status_display()}")
        print(f"  Disposition: {ncr.get_disposition_display()}")
        print(f"  Work order resumed")

        # Mark notification as read
        ncr_notification.is_read = True
        ncr_notification.read_at = timezone.now()
        ncr_notification.save()

        # ---------------------------------------------------------------------
        # Final verification
        # ---------------------------------------------------------------------
        print("\n[Step 11] Final verification...")

        corrective_actions = NonConformance.objects.filter(ncr_number__startswith='CA-NCR')

        final_checks = {
            'inspection_completed': inspection.status == Inspection.Status.FAILED,
            'ncr_created': ncr.pk is not None,
            'root_cause_identified': bool(ncr.root_cause),
            'report_generated': investigation_report.pk is not None,
            'all_ca_completed': all(
                ca.status == NonConformance.Status.CLOSED
                for ca in corrective_actions
            ),
            'procedure_updated': procedure.revision == '2.0',
            'effectiveness_verified': bool(ncr.closure_notes),
            'ncr_closed': ncr.status == NCR.Status.CLOSED,
            'work_order_resumed': work_order.status == work_order.Status.IN_PROGRESS,
        }

        all_passed = all(final_checks.values())

        print("\n  NCR Resolution Summary:")
        print(f"    NCR: {ncr.ncr_number}")
        print(f"    Severity: {ncr.get_severity_display()}")
        print(f"    Disposition: {ncr.get_disposition_display()}")
        print(f"    Corrective Actions: {corrective_actions.count()}")
        print(f"    Days to Close: {(ncr.closed_at - ncr.detected_at).days}")

        print("\n  Workflow Checklist:")
        for check, status in final_checks.items():
            icon = "  " if status else "  "
            print(f"    {icon} {check.replace('_', ' ').title()}")

        assert all_passed

        print("\n" + "="*60)
        print("NCR RESOLUTION WORKFLOW COMPLETED!")
        print("="*60)


    def test_minor_ncr_quick_resolution(
        self,
        qc_inspector,
        quality_manager
    ):
        """
        Test quick resolution for minor NCRs.

        Minor NCRs may have a simplified workflow.
        """
        from apps.quality.models import NCR
        from apps.workorders.models import WorkOrder, DrillBit

        print("\n" + "="*60)
        print("MINOR NCR QUICK RESOLUTION")
        print("="*60)

        # Create work order
        drill_bit = DrillBit.objects.create(
            serial_number='FC-MINOR-001',
            bit_type=DrillBit.BitType.FC,
            size=Decimal('8.500'),
            created_by=qc_inspector
        )

        work_order = WorkOrder.objects.create(
            wo_number='WO-MINOR-001',
            wo_type=WorkOrder.WOType.FC_REPAIR,
            drill_bit=drill_bit,
            status=WorkOrder.Status.IN_PROGRESS,
            created_by=qc_inspector
        )

        # Create minor NCR
        print("\n[Step 1] Creating minor NCR...")

        ncr = NCR.objects.create(
            ncr_number='NCR-MINOR-001',
            work_order=work_order,
            title='Minor cosmetic defect',
            description='Small surface scratch on non-functional area',
            severity=NCR.Severity.MINOR,
            status=NCR.Status.OPEN,
            detected_at=timezone.now(),
            detected_by=qc_inspector,
            detection_stage='In-Process'
        )

        print(f"  NCR: {ncr.ncr_number}")
        print(f"  Severity: {ncr.get_severity_display()}")

        # Quick resolution
        print("\n[Step 2] Quick resolution...")

        ncr.disposition = NCR.Disposition.USE_AS_IS
        ncr.disposition_notes = 'Cosmetic only. Does not affect function or safety.'
        ncr.status = NCR.Status.CLOSED
        ncr.closed_at = timezone.now()
        ncr.closed_by = quality_manager
        ncr.save()

        assert ncr.status == NCR.Status.CLOSED
        print(f"  Disposition: {ncr.get_disposition_display()}")
        print(f"  Status: {ncr.get_status_display()}")

        print("\n" + "="*60)
        print("MINOR NCR RESOLVED!")
        print("="*60)


# =============================================================================
# WORKFLOW SUMMARY
# =============================================================================

@pytest.mark.django_db
class TestNCRWorkflowSummary:
    """Summary tests for NCR workflow."""

    def test_workflow_models_exist(self, db):
        """Verify all workflow models are accessible."""
        from apps.quality.models import Inspection, NCR
        from apps.compliance.models import NonConformance
        from apps.procedures.models import Procedure
        from apps.documents.models import Document
        from apps.workorders.models import WorkOrder

        assert Inspection._meta.model_name == 'inspection'
        assert NCR._meta.model_name == 'ncr'
        assert NonConformance._meta.model_name == 'nonconformance'
        assert Procedure._meta.model_name == 'procedure'
        assert Document._meta.model_name == 'document'
        assert WorkOrder._meta.model_name == 'workorder'

        print("\nAll NCR workflow models verified!")
