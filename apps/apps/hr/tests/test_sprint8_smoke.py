"""
Sprint 8: HR & Workforce Management - Smoke Tests
FINAL SPRINT - System Completion

Tests all 12 Sprint 8 models:
Week 1: Employee, EmployeeDocument, EmergencyContact, BankAccount
Week 2: PerformanceReview, Goal, SkillMatrix, DisciplinaryAction
Week 3: ShiftSchedule, TimeEntry, LeaveRequest, PayrollPeriod
"""

import pytest
from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.hr.models import (
    Employee,
    EmployeeDocument,
    EmergencyContact,
    BankAccount,
    PerformanceReview,
    Goal,
    SkillMatrix,
    DisciplinaryAction,
    ShiftSchedule,
    TimeEntry,
    LeaveRequest,
    PayrollPeriod,
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
        email='test@example.com',
        password='testpass123',
        first_name='John',
        last_name='Doe'
    )


@pytest.fixture
def manager_user(db):
    """Create a manager user."""
    return User.objects.create_user(
        username='manager',
        email='manager@example.com',
        password='testpass123',
        first_name='Jane',
        last_name='Manager'
    )


@pytest.fixture
def employee(db, user, manager_user):
    """Create a test employee."""
    return Employee.objects.create(
        user=user,
        department='Engineering',
        job_title='Software Engineer',
        hire_date=date(2023, 1, 15),
        employment_type=Employee.EmploymentType.FULL_TIME,
        employment_status=Employee.EmploymentStatus.ACTIVE,
        pay_type=Employee.PayType.SALARIED,
        pay_rate=Decimal('75000.00'),
        created_by=manager_user
    )


@pytest.fixture
def employee_document(db, employee, manager_user):
    """Create a test employee document."""
    return EmployeeDocument.objects.create(
        employee=employee,
        document_type=EmployeeDocument.DocumentType.CONTRACT,
        title='Employment Contract 2023',
        file_path='/documents/contracts/emp001.pdf',
        file_name='employment_contract.pdf',
        file_size=256000,
        file_type='application/pdf',
        status=EmployeeDocument.Status.ACTIVE,
        uploaded_by=manager_user
    )


@pytest.fixture
def emergency_contact(db, employee):
    """Create a test emergency contact."""
    return EmergencyContact.objects.create(
        employee=employee,
        full_name='Jane Doe',
        relationship=EmergencyContact.Relationship.SPOUSE,
        primary_phone='+1234567890',
        is_primary=True,
        priority_order=1
    )


@pytest.fixture
def bank_account(db, employee, manager_user):
    """Create a test bank account."""
    return BankAccount.objects.create(
        employee=employee,
        bank_name='National Bank',
        account_type=BankAccount.AccountType.SALARY,
        account_number='1234567890',
        account_holder_name='John Doe',
        is_primary=True,
        created_by=manager_user
    )


@pytest.fixture
def performance_review(db, employee, manager_user):
    """Create a test performance review."""
    return PerformanceReview.objects.create(
        employee=employee,
        reviewer=manager_user,
        review_type=PerformanceReview.ReviewType.ANNUAL,
        review_period_start=date(2023, 1, 1),
        review_period_end=date(2023, 12, 31),
        review_date=date(2024, 1, 15),
        overall_rating=PerformanceReview.OverallRating.MEETS,
        status=PerformanceReview.Status.COMPLETED
    )


@pytest.fixture
def goal(db, employee, manager_user):
    """Create a test goal."""
    return Goal.objects.create(
        employee=employee,
        title='Complete Python certification',
        description='Obtain Python professional certification',
        goal_type=Goal.GoalType.PERSONAL,
        category=Goal.Category.DEVELOPMENT,
        start_date=date(2024, 1, 1),
        target_date=date(2024, 6, 30),
        status=Goal.Status.IN_PROGRESS,
        progress_percentage=50,
        assigned_by=manager_user
    )


@pytest.fixture
def skill_matrix(db, employee, manager_user):
    """Create a test skill matrix entry."""
    return SkillMatrix.objects.create(
        employee=employee,
        skill_name='Python',
        skill_category=SkillMatrix.SkillCategory.TECHNICAL,
        proficiency_level=SkillMatrix.ProficiencyLevel.ADVANCED,
        years_of_experience=Decimal('5.0'),
        certified=True,
        verified_by=manager_user,
        verified_date=date(2024, 1, 1)
    )


@pytest.fixture
def disciplinary_action(db, employee, manager_user):
    """Create a test disciplinary action."""
    return DisciplinaryAction.objects.create(
        employee=employee,
        action_type=DisciplinaryAction.ActionType.VERBAL_WARNING,
        severity=DisciplinaryAction.Severity.MINOR,
        incident_date=date(2024, 1, 10),
        incident_description='Late arrival to work',
        action_taken='Verbal warning issued',
        issued_by=manager_user,
        status=DisciplinaryAction.Status.ISSUED
    )


@pytest.fixture
def shift_schedule(db, employee, manager_user):
    """Create a test shift schedule."""
    return ShiftSchedule.objects.create(
        employee=employee,
        shift_type=ShiftSchedule.ShiftType.DAY,
        shift_date=date(2024, 1, 15),
        start_time=time(8, 0),
        end_time=time(17, 0),
        break_duration_minutes=60,
        status=ShiftSchedule.Status.SCHEDULED,
        created_by=manager_user
    )


@pytest.fixture
def time_entry(db, employee):
    """Create a test time entry."""
    return TimeEntry.objects.create(
        employee=employee,
        entry_type=TimeEntry.EntryType.REGULAR,
        entry_date=date(2024, 1, 15),
        clock_in_time=time(8, 0),
        clock_out_time=time(17, 0),
        total_hours=Decimal('8.00'),
        status=TimeEntry.Status.SUBMITTED
    )


@pytest.fixture
def leave_request(db, employee):
    """Create a test leave request."""
    return LeaveRequest.objects.create(
        employee=employee,
        leave_type=LeaveRequest.LeaveType.ANNUAL,
        start_date=date(2024, 2, 1),
        end_date=date(2024, 2, 5),
        total_days=Decimal('5.00'),
        reason='Family vacation',
        status=LeaveRequest.Status.PENDING
    )


@pytest.fixture
def payroll_period(db, manager_user):
    """Create a test payroll period."""
    return PayrollPeriod.objects.create(
        period_type=PayrollPeriod.PeriodType.MONTHLY,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        pay_date=date(2024, 2, 1),
        status=PayrollPeriod.Status.OPEN,
        created_by=manager_user
    )


# =============================================================================
# WEEK 1: EMPLOYEE MANAGEMENT TESTS
# =============================================================================


@pytest.mark.django_db
class TestEmployee:
    """Tests for Employee model."""

    def test_create_employee(self, employee):
        """Test employee creation."""
        assert employee.pk is not None
        assert employee.department == 'Engineering'
        assert employee.job_title == 'Software Engineer'

    def test_employee_auto_number(self, employee):
        """Test auto-generated employee number."""
        assert employee.employee_number.startswith('EMP-')
        assert len(employee.employee_number) == 8  # EMP-0001

    def test_employee_str(self, employee):
        """Test employee string representation."""
        assert 'EMP-' in str(employee)
        assert 'John Doe' in str(employee)

    def test_employee_full_name(self, employee):
        """Test full_name property."""
        assert employee.full_name == 'John Doe'

    def test_employee_is_active(self, employee):
        """Test is_active property."""
        assert employee.is_active is True

        employee.employment_status = Employee.EmploymentStatus.TERMINATED
        assert employee.is_active is False

    def test_employee_years_of_service(self, employee):
        """Test years_of_service property."""
        years = employee.years_of_service
        assert years > 0


@pytest.mark.django_db
class TestEmployeeDocument:
    """Tests for EmployeeDocument model."""

    def test_create_employee_document(self, employee_document):
        """Test employee document creation."""
        assert employee_document.pk is not None
        assert employee_document.document_type == EmployeeDocument.DocumentType.CONTRACT

    def test_employee_document_auto_number(self, employee_document):
        """Test auto-generated document number."""
        assert employee_document.document_number.startswith('DOC-')
        assert str(timezone.now().year) in employee_document.document_number

    def test_employee_document_str(self, employee_document):
        """Test document string representation."""
        assert 'DOC-' in str(employee_document)
        assert 'Employment Contract' in str(employee_document)

    def test_employee_document_is_expired(self, employee_document):
        """Test is_expired property."""
        # No expiry date set
        assert employee_document.is_expired is False

        # Set expired date
        employee_document.expiry_date = date(2020, 1, 1)
        assert employee_document.is_expired is True


@pytest.mark.django_db
class TestEmergencyContact:
    """Tests for EmergencyContact model."""

    def test_create_emergency_contact(self, emergency_contact):
        """Test emergency contact creation."""
        assert emergency_contact.pk is not None
        assert emergency_contact.full_name == 'Jane Doe'

    def test_emergency_contact_str(self, emergency_contact):
        """Test string representation."""
        result = str(emergency_contact)
        assert 'Jane Doe' in result
        assert 'Spouse' in result


@pytest.mark.django_db
class TestBankAccount:
    """Tests for BankAccount model."""

    def test_create_bank_account(self, bank_account):
        """Test bank account creation."""
        assert bank_account.pk is not None
        assert bank_account.bank_name == 'National Bank'
        assert bank_account.is_primary is True

    def test_bank_account_str(self, bank_account):
        """Test string representation with masked account."""
        result = str(bank_account)
        assert 'National Bank' in result
        assert '7890' in result  # Last 4 digits


# =============================================================================
# WEEK 2: PERFORMANCE & SKILLS TESTS
# =============================================================================


@pytest.mark.django_db
class TestPerformanceReview:
    """Tests for PerformanceReview model."""

    def test_create_performance_review(self, performance_review):
        """Test performance review creation."""
        assert performance_review.pk is not None
        assert performance_review.review_type == PerformanceReview.ReviewType.ANNUAL

    def test_performance_review_auto_number(self, performance_review):
        """Test auto-generated review number."""
        assert performance_review.review_number.startswith('REV-')

    def test_performance_review_str(self, performance_review):
        """Test string representation."""
        result = str(performance_review)
        assert 'REV-' in result
        assert 'Annual Review' in result

    def test_performance_review_is_completed(self, performance_review):
        """Test is_completed property."""
        assert performance_review.is_completed is True

        performance_review.status = PerformanceReview.Status.DRAFT
        assert performance_review.is_completed is False


@pytest.mark.django_db
class TestGoal:
    """Tests for Goal model."""

    def test_create_goal(self, goal):
        """Test goal creation."""
        assert goal.pk is not None
        assert goal.title == 'Complete Python certification'

    def test_goal_auto_number(self, goal):
        """Test auto-generated goal number."""
        assert goal.goal_number.startswith('GOAL-')

    def test_goal_str(self, goal):
        """Test string representation."""
        assert 'GOAL-' in str(goal)
        assert 'Python certification' in str(goal)

    def test_goal_is_overdue(self, goal):
        """Test is_overdue property."""
        # Future target date
        goal.target_date = date.today() + timedelta(days=30)
        assert goal.is_overdue is False

        # Past target date
        goal.target_date = date.today() - timedelta(days=30)
        assert goal.is_overdue is True

        # Completed goal is never overdue
        goal.status = Goal.Status.COMPLETED
        assert goal.is_overdue is False


@pytest.mark.django_db
class TestSkillMatrix:
    """Tests for SkillMatrix model."""

    def test_create_skill_matrix(self, skill_matrix):
        """Test skill matrix creation."""
        assert skill_matrix.pk is not None
        assert skill_matrix.skill_name == 'Python'
        assert skill_matrix.proficiency_level == SkillMatrix.ProficiencyLevel.ADVANCED

    def test_skill_matrix_str(self, skill_matrix):
        """Test string representation."""
        result = str(skill_matrix)
        assert 'Python' in result
        assert 'Advanced' in result

    def test_skill_matrix_certification_expired(self, skill_matrix):
        """Test certification_is_expired property."""
        # No expiry date
        assert skill_matrix.certification_is_expired is None

        # Future expiry
        skill_matrix.certification_expiry = date.today() + timedelta(days=365)
        assert skill_matrix.certification_is_expired is False

        # Past expiry
        skill_matrix.certification_expiry = date.today() - timedelta(days=30)
        assert skill_matrix.certification_is_expired is True


@pytest.mark.django_db
class TestDisciplinaryAction:
    """Tests for DisciplinaryAction model."""

    def test_create_disciplinary_action(self, disciplinary_action):
        """Test disciplinary action creation."""
        assert disciplinary_action.pk is not None
        assert disciplinary_action.action_type == DisciplinaryAction.ActionType.VERBAL_WARNING

    def test_disciplinary_action_auto_number(self, disciplinary_action):
        """Test auto-generated action number."""
        assert disciplinary_action.action_number.startswith('DA-')

    def test_disciplinary_action_str(self, disciplinary_action):
        """Test string representation."""
        result = str(disciplinary_action)
        assert 'DA-' in result
        assert 'Verbal Warning' in result

    def test_disciplinary_action_is_expired(self, disciplinary_action):
        """Test is_expired property."""
        # No expiry date
        assert disciplinary_action.is_expired is False

        # Future expiry
        disciplinary_action.expiry_date = date.today() + timedelta(days=365)
        assert disciplinary_action.is_expired is False

        # Past expiry
        disciplinary_action.expiry_date = date.today() - timedelta(days=30)
        assert disciplinary_action.is_expired is True


# =============================================================================
# WEEK 3: TIME & SCHEDULING TESTS
# =============================================================================


@pytest.mark.django_db
class TestShiftSchedule:
    """Tests for ShiftSchedule model."""

    def test_create_shift_schedule(self, shift_schedule):
        """Test shift schedule creation."""
        assert shift_schedule.pk is not None
        assert shift_schedule.shift_type == ShiftSchedule.ShiftType.DAY

    def test_shift_schedule_str(self, shift_schedule):
        """Test string representation."""
        result = str(shift_schedule)
        assert '2024-01-15' in result
        assert '08:00' in result

    def test_shift_schedule_scheduled_hours(self, shift_schedule):
        """Test scheduled_hours property."""
        # 8am to 5pm = 9 hours - 1 hour break = 8 hours
        assert shift_schedule.scheduled_hours == 8.0


@pytest.mark.django_db
class TestTimeEntry:
    """Tests for TimeEntry model."""

    def test_create_time_entry(self, time_entry):
        """Test time entry creation."""
        assert time_entry.pk is not None
        assert time_entry.total_hours == Decimal('8.00')

    def test_time_entry_auto_number(self, time_entry):
        """Test auto-generated entry number."""
        assert time_entry.entry_number.startswith('TIME-')

    def test_time_entry_str(self, time_entry):
        """Test string representation."""
        result = str(time_entry)
        assert 'TIME-' in result
        assert '2024-01-15' in result


@pytest.mark.django_db
class TestLeaveRequest:
    """Tests for LeaveRequest model."""

    def test_create_leave_request(self, leave_request):
        """Test leave request creation."""
        assert leave_request.pk is not None
        assert leave_request.leave_type == LeaveRequest.LeaveType.ANNUAL
        assert leave_request.total_days == Decimal('5.00')

    def test_leave_request_auto_number(self, leave_request):
        """Test auto-generated request number."""
        assert leave_request.request_number.startswith('LEAVE-')

    def test_leave_request_str(self, leave_request):
        """Test string representation."""
        result = str(leave_request)
        assert 'LEAVE-' in result
        assert 'Annual Leave' in result

    def test_leave_request_submit(self, leave_request):
        """Test submit method."""
        leave_request.status = LeaveRequest.Status.DRAFT
        leave_request.submit()
        assert leave_request.status == LeaveRequest.Status.PENDING
        assert leave_request.submitted_date is not None

    def test_leave_request_approve(self, leave_request, manager_user):
        """Test approve method."""
        leave_request.approve(manager_user, 'Approved for vacation')
        assert leave_request.status == LeaveRequest.Status.APPROVED
        assert leave_request.approved_by == manager_user
        assert leave_request.approval_comments == 'Approved for vacation'

    def test_leave_request_reject(self, leave_request, manager_user):
        """Test reject method."""
        leave_request.reject(manager_user, 'Insufficient leave balance')
        assert leave_request.status == LeaveRequest.Status.REJECTED
        assert leave_request.rejected_by == manager_user
        assert leave_request.rejection_reason == 'Insufficient leave balance'

    def test_leave_request_cancel(self, leave_request):
        """Test cancel method."""
        leave_request.cancel('Plans changed')
        assert leave_request.status == LeaveRequest.Status.CANCELLED
        assert leave_request.cancellation_reason == 'Plans changed'


@pytest.mark.django_db
class TestPayrollPeriod:
    """Tests for PayrollPeriod model."""

    def test_create_payroll_period(self, payroll_period):
        """Test payroll period creation."""
        assert payroll_period.pk is not None
        assert payroll_period.period_type == PayrollPeriod.PeriodType.MONTHLY

    def test_payroll_period_auto_number(self, payroll_period):
        """Test auto-generated period number."""
        assert payroll_period.period_number.startswith('PAY-')

    def test_payroll_period_str(self, payroll_period):
        """Test string representation."""
        result = str(payroll_period)
        assert 'PAY-' in result
        assert '2024-01-01' in result

    def test_payroll_period_is_open(self, payroll_period):
        """Test is_open property."""
        assert payroll_period.is_open is True

        payroll_period.status = PayrollPeriod.Status.CLOSED
        assert payroll_period.is_open is False


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


@pytest.mark.django_db
class TestEmployeeRelationships:
    """Test relationships between employee and related models."""

    def test_employee_documents_relationship(self, employee, employee_document):
        """Test employee has documents."""
        assert employee.documents.count() == 1
        assert employee.documents.first() == employee_document

    def test_employee_emergency_contacts_relationship(self, employee, emergency_contact):
        """Test employee has emergency contacts."""
        assert employee.emergency_contacts.count() == 1
        assert employee.emergency_contacts.first() == emergency_contact

    def test_employee_bank_accounts_relationship(self, employee, bank_account):
        """Test employee has bank accounts."""
        assert employee.bank_accounts.count() == 1
        assert employee.bank_accounts.first() == bank_account

    def test_employee_performance_reviews_relationship(self, employee, performance_review):
        """Test employee has performance reviews."""
        assert employee.performance_reviews.count() == 1
        assert employee.performance_reviews.first() == performance_review

    def test_employee_goals_relationship(self, employee, goal):
        """Test employee has goals."""
        assert employee.goals.count() == 1
        assert employee.goals.first() == goal

    def test_employee_skills_relationship(self, employee, skill_matrix):
        """Test employee has skills."""
        assert employee.skills.count() == 1
        assert employee.skills.first() == skill_matrix

    def test_employee_disciplinary_actions_relationship(self, employee, disciplinary_action):
        """Test employee has disciplinary actions."""
        assert employee.disciplinary_actions.count() == 1
        assert employee.disciplinary_actions.first() == disciplinary_action

    def test_employee_shift_schedules_relationship(self, employee, shift_schedule):
        """Test employee has shift schedules."""
        assert employee.shift_schedules.count() == 1
        assert employee.shift_schedules.first() == shift_schedule

    def test_employee_time_entries_relationship(self, employee, time_entry):
        """Test employee has time entries."""
        assert employee.time_entries.count() == 1
        assert employee.time_entries.first() == time_entry

    def test_employee_leave_requests_relationship(self, employee, leave_request):
        """Test employee has leave requests."""
        assert employee.employee_leave_requests.count() == 1
        assert employee.employee_leave_requests.first() == leave_request
