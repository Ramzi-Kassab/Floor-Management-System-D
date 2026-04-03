"""
Safety Incident Workflow Integration Test
==========================================

Cross-App Integration:
- HSSE: Incident reporting and investigation
- Notifications: Immediate alerts to safety team
- Documents: Investigation reports and documentation
- HR: Employee training records update
- Compliance: Corrective action tracking

Workflow Steps:
1. Safety incident is reported
2. Immediate notifications sent to safety team
3. Investigation is initiated
4. Evidence/findings are documented
5. Root cause analysis is performed
6. Corrective actions are assigned
7. Employee training records updated
8. Incident is closed
9. Safety report is generated

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
def safety_manager(db):
    """Create safety manager user."""
    return User.objects.create_user(
        username='safety_mgr',
        email='safety@ardt.com',
        password='safetypass123',
        first_name='Safety',
        last_name='Manager',
        is_staff=True
    )


@pytest.fixture
def supervisor(db):
    """Create supervisor user."""
    return User.objects.create_user(
        username='supervisor',
        email='supervisor@ardt.com',
        password='superpass123',
        first_name='Shop',
        last_name='Supervisor',
        is_staff=True
    )


@pytest.fixture
def employee_involved(db):
    """Create employee involved in incident."""
    return User.objects.create_user(
        username='worker01',
        email='worker@ardt.com',
        password='workerpass123',
        first_name='Ahmed',
        last_name='Worker'
    )


@pytest.fixture
def hsse_officer(db):
    """Create HSSE officer user."""
    return User.objects.create_user(
        username='hsse_officer',
        email='hsse@ardt.com',
        password='hssepass123',
        first_name='HSSE',
        last_name='Officer',
        is_staff=True
    )


# =============================================================================
# SAFETY INCIDENT WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestSafetyIncidentWorkflow:
    """
    Complete safety incident workflow test.

    Tests the full cycle from incident reporting through
    investigation, corrective actions, and closure.
    """

    def test_full_safety_incident_workflow(
        self,
        safety_manager,
        supervisor,
        employee_involved,
        hsse_officer
    ):
        """
        Test complete safety incident workflow.

        Steps:
        1. Report safety incident
        2. Send immediate notifications
        3. Initiate investigation
        4. Document evidence and findings
        5. Perform root cause analysis
        6. Assign corrective actions
        7. Update employee training records
        8. Close incident
        9. Generate safety report
        10. Final verification
        """
        from apps.hsse.models import Incident, HOCReport
        from apps.notifications.models import Notification
        from apps.documents.models import Document, DocumentCategory
        from apps.hr.models import Employee
        from apps.compliance.models import NonConformance

        print("\n" + "="*60)
        print("SAFETY INCIDENT WORKFLOW")
        print("="*60)

        # ---------------------------------------------------------------------
        # STEP 1: Report safety incident
        # ---------------------------------------------------------------------
        print("\n[Step 1] Reporting safety incident...")

        incident = Incident.objects.create(
            incident_number='INC-2024-001',
            incident_type=Incident.IncidentType.INJURY,
            severity=Incident.Severity.MODERATE,
            occurred_at=timezone.now() - timedelta(hours=1),
            location='Workshop B - Grinding Area',
            description='''
            Employee was operating grinding machine when a small metal fragment
            struck their forearm causing a minor laceration. Employee was wearing
            safety glasses but not arm guards. First aid administered on site.
            ''',
            immediate_action='First aid applied. Employee sent to medical clinic.',
            status=Incident.Status.REPORTED,
            reported_by=supervisor
        )

        assert incident.pk is not None
        print(f"  Incident Number: {incident.incident_number}")
        print(f"  Type: {incident.get_incident_type_display()}")
        print(f"  Severity: {incident.get_severity_display()}")
        print(f"  Location: {incident.location}")

        # ---------------------------------------------------------------------
        # STEP 2: Send immediate notifications
        # ---------------------------------------------------------------------
        print("\n[Step 2] Sending immediate notifications...")

        # Notify safety manager
        notification_safety = Notification.objects.create(
            recipient=safety_manager,
            title=f'SAFETY ALERT: {incident.get_severity_display()} Incident',
            message=f'Incident {incident.incident_number} reported at {incident.location}. '
                    f'Type: {incident.get_incident_type_display()}. Immediate attention required.',
            priority=Notification.Priority.URGENT,
            entity_type='hsse.incident',
            entity_id=incident.pk
        )

        # Notify HSSE officer
        notification_hsse = Notification.objects.create(
            recipient=hsse_officer,
            title=f'Incident Investigation Required: {incident.incident_number}',
            message=f'Please initiate investigation for incident at {incident.location}.',
            priority=Notification.Priority.HIGH,
            entity_type='hsse.incident',
            entity_id=incident.pk
        )

        notifications_sent = Notification.objects.filter(entity_id=incident.pk).count()
        assert notifications_sent >= 2
        print(f"  Notifications sent: {notifications_sent}")
        print(f"  Recipients: {safety_manager.username}, {hsse_officer.username}")

        # ---------------------------------------------------------------------
        # STEP 3: Initiate investigation
        # ---------------------------------------------------------------------
        print("\n[Step 3] Initiating investigation...")

        incident.status = Incident.Status.INVESTIGATING
        incident.save()

        assert incident.status == Incident.Status.INVESTIGATING
        print(f"  Status: {incident.get_status_display()}")
        print(f"  Lead investigator: {hsse_officer.username}")

        # ---------------------------------------------------------------------
        # STEP 4: Document evidence and findings
        # ---------------------------------------------------------------------
        print("\n[Step 4] Documenting evidence and findings...")

        # Create a Hazard Observation Card for additional context
        hoc = HOCReport.objects.create(
            hoc_number='HOC-2024-001',
            category=HOCReport.Category.UNSAFE_CONDITION,
            location='Workshop B - Grinding Area',
            description='Grinding area lacks adequate PPE signage. Arm guards not readily available.',
            immediate_action='Temporary signage installed. PPE ordered.',
            status=HOCReport.Status.IN_PROGRESS,
            reported_by=hsse_officer
        )

        print(f"  HOC Created: {hoc.hoc_number}")
        print(f"  Category: {hoc.get_category_display()}")

        # Update incident with findings
        incident.investigation_findings = '''
        Investigation Findings:
        1. Employee was operating grinding machine per procedure
        2. Safety glasses were worn but arm protection was not
        3. Arm guards are recommended but not enforced in current procedure
        4. PPE signage in area is outdated and partially obscured
        5. No previous similar incidents in past 12 months

        Contributing Factors:
        - Incomplete PPE enforcement
        - Inadequate safety signage
        - Procedure gap regarding arm protection
        '''
        incident.save()

        print(f"  Investigation findings documented")

        # ---------------------------------------------------------------------
        # STEP 5: Perform root cause analysis
        # ---------------------------------------------------------------------
        print("\n[Step 5] Root cause analysis...")

        incident.root_cause = '''
        ROOT CAUSE ANALYSIS (5-Why Method):

        Why did the injury occur?
        - Metal fragment struck unprotected forearm

        Why was the forearm unprotected?
        - Employee not wearing arm guards

        Why wasn't employee wearing arm guards?
        - Arm guards are "recommended" not "required" in procedure

        Why aren't arm guards required?
        - Original risk assessment didn't identify this as mandatory PPE

        ROOT CAUSE:
        Incomplete risk assessment for grinding operations.
        Arm protection should be mandatory PPE for grinding work.

        Classification: Procedural Gap
        '''
        incident.save()

        print(f"  Root cause identified: Procedural Gap")
        print(f"  Primary cause: Incomplete PPE requirements")

        # ---------------------------------------------------------------------
        # STEP 6: Document corrective actions via NonConformance
        # ---------------------------------------------------------------------
        print("\n[Step 6] Documenting corrective actions...")

        # Create NonConformance records to track corrective actions
        ncr1 = NonConformance.objects.create(
            ncr_number='NCR-SAFETY-001',
            source=NonConformance.Source.EMPLOYEE_REPORT,
            severity=NonConformance.Severity.MAJOR,
            status=NonConformance.Status.CORRECTIVE_ACTION,
            description='Update Grinding Procedure PPE Requirements',
            defect_description='Revise grinding SOP to require arm guards as mandatory PPE.',
            detected_date=date.today(),
            reported_by=hsse_officer,
            assigned_to=supervisor,
            target_completion_date=date.today() + timedelta(days=7),
            corrective_action='Update grinding procedure to mandate arm guards'
        )

        ncr2 = NonConformance.objects.create(
            ncr_number='NCR-SAFETY-002',
            source=NonConformance.Source.EMPLOYEE_REPORT,
            severity=NonConformance.Severity.MAJOR,
            status=NonConformance.Status.CORRECTIVE_ACTION,
            description='Install Updated PPE Signage',
            defect_description='Install clear PPE requirement signs in all grinding areas.',
            detected_date=date.today(),
            reported_by=hsse_officer,
            assigned_to=safety_manager,
            target_completion_date=date.today() + timedelta(days=3),
            corrective_action='Install new PPE signage in all grinding areas'
        )

        ncr3 = NonConformance.objects.create(
            ncr_number='NCR-SAFETY-003',
            source=NonConformance.Source.EMPLOYEE_REPORT,
            severity=NonConformance.Severity.MINOR,
            status=NonConformance.Status.CORRECTIVE_ACTION,
            description='Safety Refresher Training',
            defect_description='Conduct PPE refresher training for all shop floor employees.',
            detected_date=date.today(),
            reported_by=hsse_officer,
            assigned_to=hsse_officer,
            target_completion_date=date.today() + timedelta(days=14),
            corrective_action='Conduct PPE refresher training'
        )

        corrective_ncrs = NonConformance.objects.filter(ncr_number__startswith='NCR-SAFETY')
        assert corrective_ncrs.count() == 3
        print(f"  Corrective actions documented: {corrective_ncrs.count()}")
        for ncr in corrective_ncrs:
            print(f"    - {ncr.ncr_number}: {ncr.description}")

        # Update incident with corrective actions reference
        incident.corrective_actions = f'See NCRs: NCR-SAFETY-001, NCR-SAFETY-002, NCR-SAFETY-003'
        incident.save()

        # ---------------------------------------------------------------------
        # STEP 7: Update employee training records
        # ---------------------------------------------------------------------
        print("\n[Step 7] Scheduling employee training update...")

        # Create employee profile if needed
        employee_profile, _ = Employee.objects.get_or_create(
            user=employee_involved,
            defaults={
                'employee_number': 'EMP-WRK-001',
                'employment_type': Employee.EmploymentType.FULL_TIME,
                'employment_status': Employee.EmploymentStatus.ACTIVE,
                'hire_date': date.today() - timedelta(days=365)
            }
        )

        # Notify employee about required training
        training_notification = Notification.objects.create(
            recipient=employee_involved,
            title='Safety Training Required',
            message=f'Following incident {incident.incident_number}, you are required to '
                    f'complete PPE refresher training within 14 days.',
            priority=Notification.Priority.HIGH,
            entity_type='hsse.incident',
            entity_id=incident.pk
        )

        print(f"  Employee notified: {employee_involved.username}")
        print(f"  Training deadline: {date.today() + timedelta(days=14)}")

        # ---------------------------------------------------------------------
        # STEP 8: Complete corrective actions and close incident
        # ---------------------------------------------------------------------
        print("\n[Step 8] Closing incident...")

        # Complete all NCRs (corrective actions)
        for ncr in corrective_ncrs:
            ncr.status = NonConformance.Status.CLOSED
            ncr.actual_completion_date = date.today()
            ncr.closed_by = ncr.assigned_to
            ncr.closed_date = date.today()
            ncr.save()

        # Close HOC
        hoc.status = HOCReport.Status.CLOSED
        hoc.save()

        # Close incident
        incident.status = Incident.Status.CLOSED
        incident.save()

        assert incident.status == Incident.Status.CLOSED
        print(f"  Incident status: {incident.get_status_display()}")
        print(f"  All corrective actions completed")

        # ---------------------------------------------------------------------
        # STEP 9: Generate safety report
        # ---------------------------------------------------------------------
        print("\n[Step 9] Generating safety report...")

        doc_category, _ = DocumentCategory.objects.get_or_create(
            code='SAFETY-RPT',
            defaults={'name': 'Safety Reports', 'is_active': True}
        )

        safety_report = Document.objects.create(
            code=f'DOC-{incident.incident_number}',
            name=f'Incident Report - {incident.incident_number}',
            category=doc_category,
            version='1.0',
            status=Document.Status.ACTIVE,
            description=f'''
            INCIDENT REPORT
            ===============
            Incident Number: {incident.incident_number}
            Date: {incident.occurred_at}
            Location: {incident.location}
            Type: {incident.get_incident_type_display()}
            Severity: {incident.get_severity_display()}

            DESCRIPTION:
            {incident.description}

            ROOT CAUSE:
            {incident.root_cause}

            CORRECTIVE ACTIONS:
            {incident.corrective_actions}

            STATUS: CLOSED
            ''',
            owner=hsse_officer,
            approved_by=safety_manager,
            approved_at=timezone.now()
        )

        print(f"  Report created: {safety_report.code}")
        print(f"  Approved by: {safety_manager.username}")

        # ---------------------------------------------------------------------
        # STEP 10: Final verification
        # ---------------------------------------------------------------------
        print("\n[Step 10] Final verification...")

        # Mark notifications as read
        for notif in Notification.objects.filter(entity_id=incident.pk):
            notif.is_read = True
            notif.read_at = timezone.now()
            notif.save()

        final_checks = {
            'incident_reported': incident.incident_number is not None,
            'investigation_complete': bool(incident.investigation_findings),
            'root_cause_identified': bool(incident.root_cause),
            'corrective_actions_complete': all(
                ncr.status == NonConformance.Status.CLOSED
                for ncr in corrective_ncrs
            ),
            'hoc_closed': hoc.status == HOCReport.Status.CLOSED,
            'incident_closed': incident.status == Incident.Status.CLOSED,
            'report_generated': safety_report.pk is not None,
            'employee_notified': training_notification.pk is not None,
        }

        all_passed = all(final_checks.values())

        print("\n  Incident Summary:")
        print(f"    Incident: {incident.incident_number}")
        print(f"    Severity: {incident.get_severity_display()}")
        print(f"    Corrective Actions: {corrective_ncrs.count()}")
        print(f"    Days to Close: {(timezone.now() - incident.occurred_at).days}")

        print("\n  Workflow Checklist:")
        for check, status in final_checks.items():
            icon = "  " if status else "  "
            print(f"    {icon} {check.replace('_', ' ').title()}")

        assert all_passed

        print("\n" + "="*60)
        print("SAFETY INCIDENT WORKFLOW COMPLETED!")
        print("="*60)


    def test_near_miss_reporting_workflow(
        self,
        supervisor,
        hsse_officer
    ):
        """
        Test near miss reporting workflow.

        Near misses are important for proactive safety management.
        """
        from apps.hsse.models import HOCReport
        from apps.notifications.models import Notification

        print("\n" + "="*60)
        print("NEAR MISS REPORTING WORKFLOW")
        print("="*60)

        # Step 1: Report near miss
        print("\n[Step 1] Reporting near miss...")

        hoc = HOCReport.objects.create(
            hoc_number='HOC-NM-001',
            category=HOCReport.Category.NEAR_MISS,
            location='Forklift Aisle 3',
            description='Forklift nearly struck pedestrian. Pedestrian walked into aisle without checking.',
            immediate_action='Verbal warning. Reminder to use designated walkways.',
            status=HOCReport.Status.OPEN,
            reported_by=supervisor
        )

        print(f"  HOC Number: {hoc.hoc_number}")
        print(f"  Category: {hoc.get_category_display()}")

        # Step 2: Notify safety team
        print("\n[Step 2] Notifying safety team...")

        notification = Notification.objects.create(
            recipient=hsse_officer,
            title='Near Miss Reported',
            message=f'Near miss {hoc.hoc_number} reported at {hoc.location}',
            priority=Notification.Priority.NORMAL,
            entity_type='hsse.hocreport',
            entity_id=hoc.pk
        )

        print(f"  Notification sent to: {hsse_officer.username}")

        # Step 3: Review and close
        print("\n[Step 3] Reviewing and closing...")

        hoc.status = HOCReport.Status.CLOSED
        hoc.save()

        print(f"  HOC Status: {hoc.get_status_display()}")

        print("\n" + "="*60)
        print("NEAR MISS WORKFLOW COMPLETED!")
        print("="*60)


# =============================================================================
# WORKFLOW SUMMARY
# =============================================================================

@pytest.mark.django_db
class TestSafetyWorkflowSummary:
    """Summary tests for safety workflow."""

    def test_workflow_models_exist(self, db):
        """Verify all workflow models are accessible."""
        from apps.hsse.models import Incident, HOCReport
        from apps.notifications.models import Notification
        from apps.documents.models import Document
        from apps.compliance.models import NonConformance

        assert Incident._meta.model_name == 'incident'
        assert HOCReport._meta.model_name == 'hocreport'
        assert Notification._meta.model_name == 'notification'
        assert Document._meta.model_name == 'document'
        assert NonConformance._meta.model_name == 'nonconformance'

        print("\nAll safety workflow models verified!")
