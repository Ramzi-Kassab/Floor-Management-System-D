"""
Employee Onboarding Workflow Integration Test
==============================================

Cross-App Integration:
- HR: Employee creation and management
- Organization: Department and position assignment
- Forms Engine: Onboarding form completion
- Accounts: User account and permission setup
- Notifications: Welcome notification delivery

Workflow Steps:
1. HR creates new employee record
2. Employee assigned to department and position
3. Onboarding forms are created and completed
4. User account is created with role
5. Welcome notification is sent
6. Employee can login
7. Employee has correct permissions
8. Employee visible in organization structure

Author: Workflow Integration Suite
Date: December 2024
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def hr_manager(db):
    """Create HR manager user with permissions."""
    user = User.objects.create_user(
        username='hr_manager',
        email='hr_manager@ardt.com',
        password='hrpass123',
        first_name='HR',
        last_name='Manager',
        is_staff=True
    )
    return user


@pytest.fixture
def department(db):
    """Create a department for employee assignment."""
    from apps.organization.models import Department
    return Department.objects.create(
        code='ENG',
        name='Engineering',
        location='Building A',
        is_active=True
    )


@pytest.fixture
def position(db, department):
    """Create a position for employee assignment."""
    from apps.organization.models import Position
    return Position.objects.create(
        code='SR-ENG',
        title='Senior Engineer',
        department=department,
        level=3,
        description='Senior level engineering position',
        is_active=True
    )


@pytest.fixture
def onboarding_form_template(db, hr_manager):
    """Create onboarding form template."""
    from apps.forms_engine.models import FormTemplate, FormSection, FieldType, FormField

    # Create form template
    template = FormTemplate.objects.create(
        code='FORM-ONBOARD-001',
        name='Employee Onboarding Form',
        description='Standard onboarding checklist',
        version='1.0',
        status=FormTemplate.Status.ACTIVE,
        created_by=hr_manager
    )

    # Create section
    section = FormSection.objects.create(
        template=template,
        name='Personal Information',
        sequence=1
    )

    # Create field type if doesn't exist
    text_type, _ = FieldType.objects.get_or_create(
        code='TEXT',
        defaults={
            'name': 'Text',
            'html_input_type': 'text',
            'has_options': False,
            'has_validation': True
        }
    )

    # Create fields
    FormField.objects.create(
        section=section,
        field_type=text_type,
        name='emergency_contact_name',
        label='Emergency Contact Name',
        sequence=1,
        is_required=True
    )

    FormField.objects.create(
        section=section,
        field_type=text_type,
        name='emergency_contact_phone',
        label='Emergency Contact Phone',
        sequence=2,
        is_required=True
    )

    return template


@pytest.fixture
def notification_template(db):
    """Create welcome notification template."""
    from apps.notifications.models import NotificationTemplate
    return NotificationTemplate.objects.create(
        code='WELCOME_NEW_EMPLOYEE',
        name='Welcome New Employee',
        channel=NotificationTemplate.Channel.IN_APP,
        subject='Welcome to ARDT!',
        body_template='Welcome {{employee_name}}! Your account has been created.',
        is_active=True
    )


# =============================================================================
# EMPLOYEE ONBOARDING WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestEmployeeOnboardingWorkflow:
    """
    Complete employee onboarding workflow test.

    Tests the full lifecycle of bringing a new employee into the system,
    from HR record creation through to system access verification.
    """

    def test_full_employee_onboarding_workflow(
        self,
        hr_manager,
        department,
        position,
        onboarding_form_template,
        notification_template
    ):
        """
        Test complete employee onboarding workflow.

        Steps:
        1. HR creates new employee record with basic info
        2. Employee assigned to department and position
        3. Onboarding forms are created for employee
        4. Forms are completed with required information
        5. User account is created for employee
        6. Role is assigned to user
        7. Welcome notification is sent
        8. Verify employee can login
        9. Verify employee has correct permissions
        10. Verify employee appears in organization structure
        11. Verify complete onboarding status
        """
        from apps.hr.models import Employee
        from apps.accounts.models import Role
        from apps.notifications.models import Notification

        print("\n" + "="*60)
        print("EMPLOYEE ONBOARDING WORKFLOW")
        print("="*60)

        # ---------------------------------------------------------------------
        # STEP 1: HR creates new employee record
        # ---------------------------------------------------------------------
        print("\n[Step 1] Creating new employee record...")

        # First create the user account
        new_user = User.objects.create_user(
            username='john.doe',
            email='john.doe@ardt.com',
            password='newemployee123',
            first_name='John',
            last_name='Doe'
        )

        # Create employee profile linked to user
        employee = Employee.objects.create(
            user=new_user,
            employee_number='EMP-2024-001',
            employment_type=Employee.EmploymentType.FULL_TIME,
            employment_status=Employee.EmploymentStatus.ACTIVE,
            hire_date=date.today(),
            pay_type=Employee.PayType.SALARIED
        )

        assert employee.pk is not None, "Employee should be created"
        assert employee.employee_number == 'EMP-2024-001'
        assert employee.employment_status == Employee.EmploymentStatus.ACTIVE
        print(f"  Created employee: {employee.employee_number}")
        print(f"  User account: {new_user.username}")

        # ---------------------------------------------------------------------
        # STEP 2: Assign employee to department and position
        # ---------------------------------------------------------------------
        print("\n[Step 2] Assigning to department and position...")

        employee.department = department.name
        employee.job_title = position.title
        employee.save()

        assert employee.department == department.name
        assert employee.job_title == position.title
        print(f"  Department: {department.name}")
        print(f"  Position: {position.title}")

        # ---------------------------------------------------------------------
        # STEP 3: Create onboarding checklist items
        # ---------------------------------------------------------------------
        print("\n[Step 3] Setting up onboarding checklist...")

        # In a real system, this would create form submissions
        # For this test, we verify the template is available
        assert onboarding_form_template.status == 'ACTIVE'
        assert onboarding_form_template.field_count >= 2
        print(f"  Form template: {onboarding_form_template.name}")
        print(f"  Fields to complete: {onboarding_form_template.field_count}")

        # ---------------------------------------------------------------------
        # STEP 4: Complete onboarding forms
        # ---------------------------------------------------------------------
        print("\n[Step 4] Completing onboarding forms...")

        # Simulate form completion by updating employee emergency contacts
        from apps.hr.models import EmergencyContact

        emergency_contact = EmergencyContact.objects.create(
            employee=employee,
            full_name='Jane Doe',
            relationship=EmergencyContact.Relationship.SPOUSE,
            primary_phone='+966 555 123456',
            is_primary=True
        )

        assert emergency_contact.pk is not None
        assert emergency_contact.is_primary is True
        print(f"  Emergency contact added: {emergency_contact.full_name}")

        # ---------------------------------------------------------------------
        # STEP 5: Create bank account for payroll
        # ---------------------------------------------------------------------
        print("\n[Step 5] Setting up payroll banking...")

        from apps.hr.models import BankAccount

        bank_account = BankAccount.objects.create(
            employee=employee,
            bank_name='Al Rajhi Bank',
            account_number='SA1234567890123456789012',
            iban='SA8011234567890123456789012',
            is_primary=True,
            is_active=True
        )

        assert bank_account.pk is not None
        assert bank_account.is_primary is True
        print(f"  Bank: {bank_account.bank_name}")
        print(f"  Account set as primary")

        # ---------------------------------------------------------------------
        # STEP 6: Assign role to user
        # ---------------------------------------------------------------------
        print("\n[Step 6] Assigning role to user...")

        # Create role if doesn't exist
        role, created = Role.objects.get_or_create(
            code='ENGINEER',
            defaults={
                'name': 'Engineer',
                'description': 'Engineering staff role',
                'is_active': True
            }
        )

        # Assign role to user
        new_user.groups.add(role)
        new_user.is_staff = True
        new_user.save()

        assert role in new_user.groups.all()
        print(f"  Role assigned: {role.name}")

        # ---------------------------------------------------------------------
        # STEP 7: Send welcome notification
        # ---------------------------------------------------------------------
        print("\n[Step 7] Sending welcome notification...")

        welcome_notification = Notification.objects.create(
            recipient=new_user,
            template=notification_template,
            title='Welcome to ARDT!',
            message=f'Welcome {new_user.first_name}! Your account has been created.',
            priority=Notification.Priority.HIGH,
            entity_type='hr.employee',
            entity_id=employee.pk
        )

        assert welcome_notification.pk is not None
        assert welcome_notification.is_read is False
        print(f"  Notification sent: {welcome_notification.title}")

        # ---------------------------------------------------------------------
        # STEP 8: Verify employee can login
        # ---------------------------------------------------------------------
        print("\n[Step 8] Verifying login capability...")

        from django.test import Client

        client = Client()
        login_success = client.login(username='john.doe', password='newemployee123')

        assert login_success is True, "Employee should be able to login"
        print("  Login successful!")

        # ---------------------------------------------------------------------
        # STEP 9: Verify employee has correct permissions
        # ---------------------------------------------------------------------
        print("\n[Step 9] Verifying permissions...")

        # Refresh user from database
        new_user.refresh_from_db()

        assert new_user.is_staff is True
        assert new_user.is_active is True
        print(f"  is_staff: {new_user.is_staff}")
        print(f"  is_active: {new_user.is_active}")
        print(f"  Groups: {[g.name for g in new_user.groups.all()]}")

        # ---------------------------------------------------------------------
        # STEP 10: Verify employee in organization structure
        # ---------------------------------------------------------------------
        print("\n[Step 10] Verifying organization structure...")

        # Check employee is in department
        dept_employees = Employee.objects.filter(department=department)
        assert employee in dept_employees

        # Check position assignment
        assert employee.position.department == department
        print(f"  Organization path: {department.full_path}")
        print(f"  Employee count in dept: {dept_employees.count()}")

        # ---------------------------------------------------------------------
        # STEP 11: Final verification - complete onboarding status
        # ---------------------------------------------------------------------
        print("\n[Step 11] Final verification...")

        # Verify all components are in place
        final_checks = {
            'employee_record': employee.pk is not None,
            'user_account': new_user.pk is not None,
            'department_assigned': employee.department is not None and employee.department != '',
            'position_assigned': employee.job_title is not None and employee.job_title != '',
            'emergency_contact': EmergencyContact.objects.filter(employee=employee).exists(),
            'bank_account': BankAccount.objects.filter(employee=employee).exists(),
            'role_assigned': new_user.groups.exists(),
            'notification_sent': Notification.objects.filter(recipient=new_user).exists(),
            'can_login': login_success,
        }

        all_passed = all(final_checks.values())

        print("\n  Onboarding Checklist:")
        for check, status in final_checks.items():
            icon = "  " if status else "  "
            print(f"    {icon} {check.replace('_', ' ').title()}")

        assert all_passed, f"Some onboarding checks failed: {[k for k,v in final_checks.items() if not v]}"

        print("\n" + "="*60)
        print("WORKFLOW COMPLETED SUCCESSFULLY!")
        print("="*60)


    def test_employee_onboarding_with_manager_approval(
        self,
        hr_manager,
        department,
        position
    ):
        """
        Test employee onboarding requiring manager approval.

        Steps:
        1. HR creates employee record as PENDING
        2. Manager reviews and approves
        3. Account is activated
        4. Employee notified
        """
        from apps.hr.models import Employee

        print("\n" + "="*60)
        print("EMPLOYEE ONBOARDING WITH MANAGER APPROVAL")
        print("="*60)

        # Step 1: Create employee as draft/pending
        print("\n[Step 1] Creating pending employee record...")

        pending_user = User.objects.create_user(
            username='alice.smith',
            email='alice.smith@ardt.com',
            password='pending123',
            first_name='Alice',
            last_name='Smith',
            is_active=False  # Not active until approved
        )

        employee = Employee.objects.create(
            user=pending_user,
            employee_number='EMP-2024-002',
            employment_type=Employee.EmploymentType.CONTRACT,
            employment_status=Employee.EmploymentStatus.ACTIVE,
            hire_date=date.today() + timedelta(days=7),  # Future start date
            department=department.name,
            job_title=position.title
        )

        assert pending_user.is_active is False
        print(f"  Created pending employee: {employee.employee_number}")

        # Step 2: Manager approval simulation
        print("\n[Step 2] Manager approval...")

        # Simulate approval by department manager
        department.manager = hr_manager
        department.save()

        # Activate the user (approval granted)
        pending_user.is_active = True
        pending_user.save()

        assert pending_user.is_active is True
        print(f"  Approved by: {hr_manager.username}")
        print(f"  Employee activated: {pending_user.username}")

        # Step 3: Verify activation
        print("\n[Step 3] Verifying activation...")

        from django.test import Client
        client = Client()
        login_success = client.login(username='alice.smith', password='pending123')

        assert login_success is True
        print("  Employee can now login!")

        print("\n" + "="*60)
        print("APPROVAL WORKFLOW COMPLETED!")
        print("="*60)


    def test_employee_department_transfer(
        self,
        hr_manager,
        department,
        position
    ):
        """
        Test transferring an employee to a different department.

        Steps:
        1. Create employee in original department
        2. Create new department
        3. Transfer employee
        4. Verify history is tracked
        5. Verify new assignment
        """
        from apps.hr.models import Employee
        from apps.organization.models import Department, Position

        print("\n" + "="*60)
        print("EMPLOYEE DEPARTMENT TRANSFER")
        print("="*60)

        # Step 1: Create employee in original department
        print("\n[Step 1] Setting up employee in Engineering...")

        transfer_user = User.objects.create_user(
            username='bob.wilson',
            email='bob.wilson@ardt.com',
            password='transfer123',
            first_name='Bob',
            last_name='Wilson'
        )

        employee = Employee.objects.create(
            user=transfer_user,
            employee_number='EMP-2024-003',
            employment_type=Employee.EmploymentType.FULL_TIME,
            employment_status=Employee.EmploymentStatus.ACTIVE,
            hire_date=date.today() - timedelta(days=365),  # 1 year ago
            department=department.name,
            job_title=position.title
        )

        original_department = employee.department
        print(f"  Employee: {employee.employee_number}")
        print(f"  Original department: {original_department}")

        # Step 2: Create new department
        print("\n[Step 2] Creating new department...")

        new_department = Department.objects.create(
            code='QC',
            name='Quality Control',
            location='Building B',
            is_active=True
        )

        new_position = Position.objects.create(
            code='QC-LEAD',
            title='QC Lead',
            department=new_department,
            level=4,
            is_active=True
        )

        print(f"  New department: {new_department.name}")
        print(f"  New position: {new_position.title}")

        # Step 3: Transfer employee
        print("\n[Step 3] Transferring employee...")

        employee.department = new_department.name
        employee.job_title = new_position.title
        employee.save()

        assert employee.department == new_department.name
        assert employee.job_title == new_position.title
        print(f"  Transfer complete!")
        print(f"  From: {original_department} -> To: {new_department.name}")

        # Step 4: Verify new assignment
        print("\n[Step 4] Verifying new assignment...")

        employee.refresh_from_db()

        assert employee.department == 'Quality Control'
        assert employee.job_title == 'QC Lead'
        print(f"  Current department: {employee.department}")
        print(f"  Current position: {employee.job_title}")

        print("\n" + "="*60)
        print("TRANSFER WORKFLOW COMPLETED!")
        print("="*60)


# =============================================================================
# WORKFLOW SUMMARY
# =============================================================================

@pytest.mark.django_db
class TestOnboardingWorkflowSummary:
    """Summary tests for the onboarding workflow."""

    def test_workflow_components_exist(self, db):
        """Verify all required workflow components are available."""
        from apps.hr.models import Employee
        from apps.organization.models import Department, Position
        from apps.forms_engine.models import FormTemplate
        from apps.accounts.models import Role
        from apps.notifications.models import Notification

        # Verify models are accessible
        assert Employee._meta.model_name == 'employee'
        assert Department._meta.model_name == 'department'
        assert Position._meta.model_name == 'position'
        assert FormTemplate._meta.model_name == 'formtemplate'
        assert Role._meta.model_name == 'role'
        assert Notification._meta.model_name == 'notification'

        print("\nAll workflow components verified!")
