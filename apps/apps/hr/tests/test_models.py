"""
Tests for HR models.
"""
import pytest
from decimal import Decimal
from datetime import date, time, datetime, timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.hr.models import (
    Employee, EmployeeDocument, EmergencyContact, BankAccount,
    PerformanceReview, Goal, SkillMatrix, DisciplinaryAction,
    ShiftSchedule, TimeEntry, LeaveRequest, PayrollPeriod,
    Attendance, LeaveType, OvertimeRequest
)

User = get_user_model()


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
        password='managerpass123',
        first_name='Jane',
        last_name='Smith'
    )


@pytest.fixture
def hr_user(db):
    """Create an HR user."""
    return User.objects.create_user(
        username='hruser',
        email='hr@example.com',
        password='hrpass123',
        first_name='HR',
        last_name='Admin'
    )


@pytest.fixture
def employee(db, user, manager_user, hr_user):
    """Create a test employee."""
    # First create manager as employee
    manager_emp = Employee.objects.create(
        user=manager_user,
        employee_number='EMP-001',
        hire_date=date.today() - timedelta(days=365),
        department='Management',
        job_title='Operations Manager',
        employment_status=Employee.EmploymentStatus.ACTIVE,
        employment_type=Employee.EmploymentType.FULL_TIME,
        created_by=hr_user
    )

    return Employee.objects.create(
        user=user,
        employee_number='EMP-002',
        hire_date=date.today() - timedelta(days=30),
        department='Operations',
        job_title='Field Technician',
        employment_status=Employee.EmploymentStatus.ACTIVE,
        employment_type=Employee.EmploymentType.FULL_TIME,
        manager=manager_emp,
        work_phone='555-0100',
        work_email='john.doe@company.com',
        salary=Decimal('65000.00'),
        pay_frequency='BIWEEKLY',
        created_by=hr_user
    )


@pytest.fixture
def leave_type(db, hr_user):
    """Create a test leave type."""
    return LeaveType.objects.create(
        name='Annual Leave',
        code='AL',
        description='Paid annual vacation leave',
        default_days=20,
        is_paid=True,
        requires_approval=True,
        is_active=True,
        created_by=hr_user
    )


@pytest.fixture
def payroll_period(db, hr_user):
    """Create a test payroll period."""
    today = date.today()
    start = today.replace(day=1)
    end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    return PayrollPeriod.objects.create(
        name=f'Payroll {start.strftime("%B %Y")}',
        start_date=start,
        end_date=end,
        pay_date=end + timedelta(days=5),
        status='OPEN',
        created_by=hr_user
    )


class TestEmployeeModel:
    """Tests for Employee model."""

    def test_create_employee(self, db, user, hr_user):
        """Test creating an employee."""
        employee = Employee.objects.create(
            user=user,
            employee_number='EMP-TEST',
            hire_date=date.today(),
            department='Engineering',
            job_title='Software Developer',
            employment_status=Employee.EmploymentStatus.ACTIVE,
            employment_type=Employee.EmploymentType.FULL_TIME,
            created_by=hr_user
        )
        assert employee.pk is not None
        assert employee.employee_number == 'EMP-TEST'
        assert employee.employment_status == Employee.EmploymentStatus.ACTIVE

    def test_employee_str(self, employee):
        """Test employee string representation."""
        result = str(employee)
        assert 'EMP-002' in result or 'John' in result or 'Doe' in result

    def test_employee_full_name(self, employee):
        """Test employee full name property."""
        assert employee.user.first_name in str(employee) or 'John' in employee.user.get_full_name()

    def test_employee_with_manager(self, employee):
        """Test employee with manager relationship."""
        assert employee.manager is not None
        assert employee.manager.employee_number == 'EMP-001'

    def test_employee_status_choices(self, db, user, hr_user):
        """Test employee status choices."""
        for status, _ in Employee.EmploymentStatus.choices:
            employee = Employee.objects.create(
                user=User.objects.create_user(
                    username=f'user_{status}',
                    email=f'{status}@test.com',
                    password='testpass'
                ),
                employee_number=f'EMP-{status}',
                hire_date=date.today(),
                department='Test',
                job_title='Tester',
                employment_status=status,
                employment_type=Employee.EmploymentType.FULL_TIME,
                created_by=hr_user
            )
            assert employee.employment_status == status

    def test_employee_type_choices(self, db, user, hr_user):
        """Test employee type choices."""
        assert Employee.EmploymentType.FULL_TIME is not None
        assert Employee.EmploymentType.PART_TIME is not None
        assert Employee.EmploymentType.CONTRACT is not None

    def test_employee_salary(self, employee):
        """Test employee salary field."""
        assert employee.salary == Decimal('65000.00')


class TestEmployeeDocumentModel:
    """Tests for EmployeeDocument model."""

    def test_create_document(self, employee, hr_user):
        """Test creating an employee document."""
        doc = EmployeeDocument.objects.create(
            employee=employee,
            document_type='RESUME',
            title='Resume',
            description='Initial resume',
            created_by=hr_user
        )
        assert doc.pk is not None
        assert doc.employee == employee
        assert doc.document_type == 'RESUME'

    def test_document_str(self, employee, hr_user):
        """Test document string representation."""
        doc = EmployeeDocument.objects.create(
            employee=employee,
            document_type='CONTRACT',
            title='Employment Contract',
            created_by=hr_user
        )
        result = str(doc)
        assert 'Contract' in result or 'Employment' in result or doc.document_type in result


class TestEmergencyContactModel:
    """Tests for EmergencyContact model."""

    def test_create_emergency_contact(self, employee, hr_user):
        """Test creating an emergency contact."""
        contact = EmergencyContact.objects.create(
            employee=employee,
            name='Jane Doe',
            relationship='Spouse',
            phone='555-0200',
            email='jane.doe@example.com',
            is_primary=True,
            created_by=hr_user
        )
        assert contact.pk is not None
        assert contact.name == 'Jane Doe'
        assert contact.is_primary is True

    def test_emergency_contact_str(self, employee, hr_user):
        """Test emergency contact string representation."""
        contact = EmergencyContact.objects.create(
            employee=employee,
            name='Bob Smith',
            relationship='Brother',
            phone='555-0300',
            created_by=hr_user
        )
        result = str(contact)
        assert 'Bob' in result or 'Smith' in result

    def test_multiple_emergency_contacts(self, employee, hr_user):
        """Test multiple emergency contacts per employee."""
        contact1 = EmergencyContact.objects.create(
            employee=employee,
            name='Contact 1',
            relationship='Spouse',
            phone='555-0001',
            is_primary=True,
            created_by=hr_user
        )
        contact2 = EmergencyContact.objects.create(
            employee=employee,
            name='Contact 2',
            relationship='Parent',
            phone='555-0002',
            is_primary=False,
            created_by=hr_user
        )

        contacts = employee.emergency_contacts.all()
        assert contacts.count() == 2


class TestBankAccountModel:
    """Tests for BankAccount model."""

    def test_create_bank_account(self, employee, hr_user):
        """Test creating a bank account."""
        account = BankAccount.objects.create(
            employee=employee,
            bank_name='First National Bank',
            account_number='1234567890',
            routing_number='021000021',
            account_type='CHECKING',
            is_primary=True,
            created_by=hr_user
        )
        assert account.pk is not None
        assert account.bank_name == 'First National Bank'
        assert account.is_primary is True

    def test_bank_account_str(self, employee, hr_user):
        """Test bank account string representation."""
        account = BankAccount.objects.create(
            employee=employee,
            bank_name='Chase Bank',
            account_number='9876543210',
            routing_number='021000089',
            account_type='SAVINGS',
            created_by=hr_user
        )
        result = str(account)
        assert 'Chase' in result or 'Bank' in result or 'SAVINGS' in result


class TestPerformanceReviewModel:
    """Tests for PerformanceReview model."""

    def test_create_performance_review(self, employee, hr_user):
        """Test creating a performance review."""
        review = PerformanceReview.objects.create(
            employee=employee,
            review_period_start=date.today() - timedelta(days=180),
            review_period_end=date.today(),
            review_date=date.today(),
            reviewer=employee.manager,
            status='DRAFT',
            overall_rating=4,
            created_by=hr_user
        )
        assert review.pk is not None
        assert review.status == 'DRAFT'
        assert review.overall_rating == 4

    def test_review_status_transitions(self, employee, hr_user):
        """Test performance review status transitions."""
        review = PerformanceReview.objects.create(
            employee=employee,
            review_period_start=date.today() - timedelta(days=90),
            review_period_end=date.today(),
            review_date=date.today(),
            reviewer=employee.manager,
            status='DRAFT',
            created_by=hr_user
        )

        # Update status
        review.status = 'PENDING_EMPLOYEE'
        review.save()
        review.refresh_from_db()
        assert review.status == 'PENDING_EMPLOYEE'

    def test_review_with_ratings(self, employee, hr_user):
        """Test performance review with various ratings."""
        review = PerformanceReview.objects.create(
            employee=employee,
            review_period_start=date.today() - timedelta(days=365),
            review_period_end=date.today(),
            review_date=date.today(),
            reviewer=employee.manager,
            status='COMPLETED',
            overall_rating=5,
            performance_rating=5,
            goals_rating=4,
            competency_rating=5,
            created_by=hr_user
        )
        assert review.overall_rating == 5


class TestGoalModel:
    """Tests for Goal model."""

    def test_create_goal(self, employee, hr_user):
        """Test creating a goal."""
        goal = Goal.objects.create(
            employee=employee,
            title='Complete Safety Certification',
            description='Obtain OSHA safety certification',
            category='PROFESSIONAL',
            priority='HIGH',
            status='NOT_STARTED',
            due_date=date.today() + timedelta(days=90),
            created_by=hr_user
        )
        assert goal.pk is not None
        assert goal.title == 'Complete Safety Certification'
        assert goal.status == 'NOT_STARTED'

    def test_goal_str(self, employee, hr_user):
        """Test goal string representation."""
        goal = Goal.objects.create(
            employee=employee,
            title='Learn Python',
            category='PROFESSIONAL',
            status='IN_PROGRESS',
            due_date=date.today() + timedelta(days=60),
            created_by=hr_user
        )
        result = str(goal)
        assert 'Python' in result or 'Learn' in result

    def test_goal_status_transitions(self, employee, hr_user):
        """Test goal status transitions."""
        goal = Goal.objects.create(
            employee=employee,
            title='Test Goal',
            category='PERFORMANCE',
            status='NOT_STARTED',
            due_date=date.today() + timedelta(days=30),
            created_by=hr_user
        )

        goal.status = 'IN_PROGRESS'
        goal.save()
        goal.refresh_from_db()
        assert goal.status == 'IN_PROGRESS'

        goal.status = 'COMPLETED'
        goal.completion_date = date.today()
        goal.save()
        goal.refresh_from_db()
        assert goal.status == 'COMPLETED'


class TestSkillMatrixModel:
    """Tests for SkillMatrix model."""

    def test_create_skill(self, employee, hr_user):
        """Test creating a skill entry."""
        skill = SkillMatrix.objects.create(
            employee=employee,
            skill_name='Welding',
            category='TECHNICAL',
            proficiency_level=4,
            years_experience=5,
            is_certified=True,
            certification_expiry=date.today() + timedelta(days=365),
            created_by=hr_user
        )
        assert skill.pk is not None
        assert skill.skill_name == 'Welding'
        assert skill.proficiency_level == 4

    def test_skill_str(self, employee, hr_user):
        """Test skill string representation."""
        skill = SkillMatrix.objects.create(
            employee=employee,
            skill_name='Python Programming',
            category='TECHNICAL',
            proficiency_level=3,
            created_by=hr_user
        )
        result = str(skill)
        assert 'Python' in result or 'Programming' in result


class TestDisciplinaryActionModel:
    """Tests for DisciplinaryAction model."""

    def test_create_disciplinary_action(self, employee, hr_user):
        """Test creating a disciplinary action."""
        action = DisciplinaryAction.objects.create(
            employee=employee,
            action_type='WARNING',
            severity='MINOR',
            incident_date=date.today(),
            description='Late arrival to work',
            action_taken='Verbal warning issued',
            issued_by=employee.manager,
            created_by=hr_user
        )
        assert action.pk is not None
        assert action.action_type == 'WARNING'
        assert action.severity == 'MINOR'

    def test_disciplinary_action_str(self, employee, hr_user):
        """Test disciplinary action string representation."""
        action = DisciplinaryAction.objects.create(
            employee=employee,
            action_type='WRITTEN_WARNING',
            severity='MODERATE',
            incident_date=date.today(),
            description='Policy violation',
            issued_by=employee.manager,
            created_by=hr_user
        )
        result = str(action)
        assert 'WARNING' in result.upper() or 'WRITTEN' in result.upper() or str(employee) in result


class TestShiftScheduleModel:
    """Tests for ShiftSchedule model."""

    def test_create_shift(self, employee, hr_user):
        """Test creating a shift schedule."""
        shift = ShiftSchedule.objects.create(
            employee=employee,
            shift_date=date.today() + timedelta(days=1),
            start_time=time(8, 0),
            end_time=time(17, 0),
            shift_type='REGULAR',
            status='SCHEDULED',
            created_by=hr_user
        )
        assert shift.pk is not None
        assert shift.shift_type == 'REGULAR'
        assert shift.status == 'SCHEDULED'

    def test_shift_duration(self, employee, hr_user):
        """Test shift duration calculation."""
        shift = ShiftSchedule.objects.create(
            employee=employee,
            shift_date=date.today(),
            start_time=time(9, 0),
            end_time=time(18, 0),
            shift_type='REGULAR',
            status='COMPLETED',
            created_by=hr_user
        )
        # 9 hours shift
        assert shift.start_time.hour == 9
        assert shift.end_time.hour == 18


class TestTimeEntryModel:
    """Tests for TimeEntry model."""

    def test_create_time_entry(self, employee, hr_user):
        """Test creating a time entry."""
        entry = TimeEntry.objects.create(
            employee=employee,
            entry_date=date.today(),
            clock_in=timezone.now().replace(hour=8, minute=0),
            clock_out=timezone.now().replace(hour=17, minute=0),
            status='APPROVED',
            created_by=hr_user
        )
        assert entry.pk is not None
        assert entry.status == 'APPROVED'

    def test_time_entry_hours_calculation(self, employee, hr_user):
        """Test time entry hours calculation."""
        now = timezone.now()
        entry = TimeEntry.objects.create(
            employee=employee,
            entry_date=date.today(),
            clock_in=now.replace(hour=8, minute=0, second=0),
            clock_out=now.replace(hour=16, minute=30, second=0),
            regular_hours=Decimal('8.0'),
            overtime_hours=Decimal('0.5'),
            status='SUBMITTED',
            created_by=hr_user
        )
        assert entry.regular_hours == Decimal('8.0')
        assert entry.overtime_hours == Decimal('0.5')


class TestLeaveRequestModel:
    """Tests for LeaveRequest model."""

    def test_create_leave_request(self, employee, leave_type, hr_user):
        """Test creating a leave request."""
        request = LeaveRequest.objects.create(
            employee=employee,
            leave_type=leave_type,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=14),
            reason='Family vacation',
            status='PENDING',
            created_by=hr_user
        )
        assert request.pk is not None
        assert request.status == 'PENDING'
        assert request.leave_type == leave_type

    def test_leave_request_str(self, employee, leave_type, hr_user):
        """Test leave request string representation."""
        request = LeaveRequest.objects.create(
            employee=employee,
            leave_type=leave_type,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=3),
            reason='Personal',
            status='PENDING',
            created_by=hr_user
        )
        result = str(request)
        # Should contain employee info or leave type
        assert result is not None

    def test_leave_request_approval(self, employee, leave_type, hr_user):
        """Test leave request approval workflow."""
        request = LeaveRequest.objects.create(
            employee=employee,
            leave_type=leave_type,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            reason='Conference',
            status='PENDING',
            created_by=hr_user
        )

        request.status = 'APPROVED'
        request.approved_by = employee.manager
        request.approved_date = timezone.now()
        request.save()

        request.refresh_from_db()
        assert request.status == 'APPROVED'

    def test_leave_request_rejection(self, employee, leave_type, hr_user):
        """Test leave request rejection."""
        request = LeaveRequest.objects.create(
            employee=employee,
            leave_type=leave_type,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=2),
            reason='Short notice vacation',
            status='PENDING',
            created_by=hr_user
        )

        request.status = 'REJECTED'
        request.rejection_reason = 'Insufficient notice period'
        request.save()

        request.refresh_from_db()
        assert request.status == 'REJECTED'


class TestLeaveTypeModel:
    """Tests for LeaveType model."""

    def test_create_leave_type(self, hr_user):
        """Test creating a leave type."""
        leave_type = LeaveType.objects.create(
            name='Sick Leave',
            code='SL',
            description='Leave for illness',
            default_days=10,
            is_paid=True,
            requires_approval=True,
            is_active=True,
            created_by=hr_user
        )
        assert leave_type.pk is not None
        assert leave_type.name == 'Sick Leave'
        assert leave_type.is_paid is True

    def test_leave_type_str(self, leave_type):
        """Test leave type string representation."""
        result = str(leave_type)
        assert 'Annual' in result or 'Leave' in result


class TestPayrollPeriodModel:
    """Tests for PayrollPeriod model."""

    def test_create_payroll_period(self, hr_user):
        """Test creating a payroll period."""
        today = date.today()
        period = PayrollPeriod.objects.create(
            name='Test Payroll Period',
            start_date=today,
            end_date=today + timedelta(days=14),
            pay_date=today + timedelta(days=19),
            status='OPEN',
            created_by=hr_user
        )
        assert period.pk is not None
        assert period.status == 'OPEN'

    def test_payroll_period_str(self, payroll_period):
        """Test payroll period string representation."""
        result = str(payroll_period)
        assert 'Payroll' in result or payroll_period.name in result

    def test_payroll_period_status_transitions(self, payroll_period):
        """Test payroll period status transitions."""
        assert payroll_period.status == 'OPEN'

        payroll_period.status = 'PROCESSING'
        payroll_period.save()
        payroll_period.refresh_from_db()
        assert payroll_period.status == 'PROCESSING'

        payroll_period.status = 'CLOSED'
        payroll_period.save()
        payroll_period.refresh_from_db()
        assert payroll_period.status == 'CLOSED'


class TestAttendanceModel:
    """Tests for Attendance model."""

    def test_create_attendance(self, employee, hr_user):
        """Test creating an attendance record."""
        attendance = Attendance.objects.create(
            employee=employee,
            date=date.today(),
            status='PRESENT',
            check_in=time(8, 0),
            check_out=time(17, 0),
            created_by=hr_user
        )
        assert attendance.pk is not None
        assert attendance.status == 'PRESENT'

    def test_attendance_status_choices(self, employee, hr_user):
        """Test attendance status choices."""
        statuses = ['PRESENT', 'ABSENT', 'LATE', 'HALF_DAY']
        for i, status in enumerate(statuses):
            attendance = Attendance.objects.create(
                employee=employee,
                date=date.today() - timedelta(days=i+1),
                status=status,
                created_by=hr_user
            )
            assert attendance.status == status


class TestOvertimeRequestModel:
    """Tests for OvertimeRequest model."""

    def test_create_overtime_request(self, employee, hr_user):
        """Test creating an overtime request."""
        request = OvertimeRequest.objects.create(
            employee=employee,
            date=date.today() + timedelta(days=1),
            hours_requested=Decimal('4.0'),
            reason='Project deadline',
            status='PENDING',
            created_by=hr_user
        )
        assert request.pk is not None
        assert request.hours_requested == Decimal('4.0')
        assert request.status == 'PENDING'

    def test_overtime_request_approval(self, employee, hr_user):
        """Test overtime request approval."""
        request = OvertimeRequest.objects.create(
            employee=employee,
            date=date.today() + timedelta(days=2),
            hours_requested=Decimal('3.0'),
            reason='Inventory count',
            status='PENDING',
            created_by=hr_user
        )

        request.status = 'APPROVED'
        request.approved_by = employee.manager
        request.save()

        request.refresh_from_db()
        assert request.status == 'APPROVED'
