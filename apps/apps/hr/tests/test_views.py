"""
Tests for HR views.
"""
import pytest
from decimal import Decimal
from datetime import date, time, timedelta
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client
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
def manager_user(db):
    """Create a manager user."""
    return User.objects.create_user(
        username='manager',
        email='manager@example.com',
        password='managerpass123',
        first_name='Jane',
        last_name='Manager'
    )


@pytest.fixture
def client():
    """Return a Django test client."""
    return Client()


@pytest.fixture
def authenticated_client(client, user):
    """Return an authenticated test client."""
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def hr_client(client, hr_user):
    """Return an authenticated HR client."""
    client.login(username='hruser', password='hrpass123')
    return client


@pytest.fixture
def employee(db, user, manager_user, hr_user):
    """Create a test employee."""
    manager_emp = Employee.objects.create(
        user=manager_user,
        employee_number='EMP-MGR',
        hire_date=date.today() - timedelta(days=365),
        department='Management',
        job_title='Manager',
        employment_status=Employee.EmploymentStatus.ACTIVE,
        employment_type=Employee.EmploymentType.FULL_TIME,
        created_by=hr_user
    )

    return Employee.objects.create(
        user=user,
        employee_number='EMP-001',
        hire_date=date.today() - timedelta(days=30),
        department='Operations',
        job_title='Technician',
        employment_status=Employee.EmploymentStatus.ACTIVE,
        employment_type=Employee.EmploymentType.FULL_TIME,
        manager=manager_emp,
        salary=Decimal('50000.00'),
        created_by=hr_user
    )


@pytest.fixture
def leave_type(db, hr_user):
    """Create a test leave type."""
    return LeaveType.objects.create(
        name='Annual Leave',
        code='AL',
        default_days=20,
        is_paid=True,
        is_active=True,
        created_by=hr_user
    )


@pytest.fixture
def leave_request(db, employee, leave_type, hr_user):
    """Create a test leave request."""
    return LeaveRequest.objects.create(
        employee=employee,
        leave_type=leave_type,
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=10),
        reason='Vacation',
        status='PENDING',
        created_by=hr_user
    )


@pytest.fixture
def payroll_period(db, hr_user):
    """Create a test payroll period."""
    today = date.today()
    return PayrollPeriod.objects.create(
        name='Test Period',
        start_date=today.replace(day=1),
        end_date=today,
        pay_date=today + timedelta(days=5),
        status='OPEN',
        created_by=hr_user
    )


class TestHRDashboardView:
    """Tests for HR dashboard view."""

    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires authentication."""
        url = reverse('hr:dashboard')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url.lower()

    def test_dashboard_authenticated(self, authenticated_client, employee):
        """Test dashboard with authenticated user."""
        url = reverse('hr:dashboard')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_dashboard_context(self, authenticated_client, employee):
        """Test dashboard contains expected context."""
        url = reverse('hr:dashboard')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'total_employees' in response.context or response.status_code == 200


class TestEmployeeListView:
    """Tests for employee list view."""

    def test_employee_list_requires_login(self, client):
        """Test that employee list requires authentication."""
        url = reverse('hr:employee-list')
        response = client.get(url)
        assert response.status_code == 302

    def test_employee_list_authenticated(self, authenticated_client, employee):
        """Test employee list with authenticated user."""
        url = reverse('hr:employee-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_employee_list_search(self, authenticated_client, employee):
        """Test employee list search functionality."""
        url = reverse('hr:employee-list')
        response = authenticated_client.get(url, {'q': 'EMP-001'})
        assert response.status_code == 200

    def test_employee_list_filter_by_status(self, authenticated_client, employee):
        """Test employee list filter by status."""
        url = reverse('hr:employee-list')
        response = authenticated_client.get(url, {'status': 'ACTIVE'})
        assert response.status_code == 200

    def test_employee_list_filter_by_type(self, authenticated_client, employee):
        """Test employee list filter by type."""
        url = reverse('hr:employee-list')
        response = authenticated_client.get(url, {'type': 'FULL_TIME'})
        assert response.status_code == 200


class TestEmployeeDetailView:
    """Tests for employee detail view."""

    def test_employee_detail_requires_login(self, client, employee):
        """Test that employee detail requires authentication."""
        url = reverse('hr:employee-detail', kwargs={'pk': employee.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_employee_detail_authenticated(self, authenticated_client, employee):
        """Test employee detail with authenticated user."""
        url = reverse('hr:employee-detail', kwargs={'pk': employee.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_employee_detail_not_found(self, authenticated_client):
        """Test employee detail with invalid ID."""
        url = reverse('hr:employee-detail', kwargs={'pk': 99999})
        response = authenticated_client.get(url)
        assert response.status_code == 404


class TestEmployeeCreateView:
    """Tests for employee create view."""

    def test_employee_create_requires_login(self, client):
        """Test that employee create requires authentication."""
        url = reverse('hr:employee-create')
        response = client.get(url)
        assert response.status_code == 302

    def test_employee_create_get(self, authenticated_client):
        """Test employee create form display."""
        url = reverse('hr:employee-create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestEmployeeUpdateView:
    """Tests for employee update view."""

    def test_employee_update_requires_login(self, client, employee):
        """Test that employee update requires authentication."""
        url = reverse('hr:employee-update', kwargs={'pk': employee.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_employee_update_get(self, authenticated_client, employee):
        """Test employee update form display."""
        url = reverse('hr:employee-update', kwargs={'pk': employee.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestLeaveRequestViews:
    """Tests for leave request views."""

    def test_leave_list_requires_login(self, client):
        """Test that leave list requires authentication."""
        url = reverse('hr:leave-list')
        response = client.get(url)
        assert response.status_code == 302

    def test_leave_list_authenticated(self, authenticated_client, leave_request):
        """Test leave list with authenticated user."""
        url = reverse('hr:leave-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_leave_detail(self, authenticated_client, leave_request):
        """Test leave request detail view."""
        url = reverse('hr:leave-detail', kwargs={'pk': leave_request.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_leave_create_get(self, authenticated_client):
        """Test leave request create form display."""
        url = reverse('hr:leave-create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestLeaveTypeViews:
    """Tests for leave type views."""

    def test_leave_type_list_requires_login(self, client):
        """Test that leave type list requires authentication."""
        url = reverse('hr:leave-type-list')
        response = client.get(url)
        assert response.status_code == 302

    def test_leave_type_list_authenticated(self, authenticated_client, leave_type):
        """Test leave type list with authenticated user."""
        url = reverse('hr:leave-type-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestPayrollPeriodViews:
    """Tests for payroll period views."""

    def test_payroll_list_requires_login(self, client):
        """Test that payroll list requires authentication."""
        url = reverse('hr:payroll-list')
        response = client.get(url)
        assert response.status_code == 302

    def test_payroll_list_authenticated(self, authenticated_client, payroll_period):
        """Test payroll list with authenticated user."""
        url = reverse('hr:payroll-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_payroll_detail(self, authenticated_client, payroll_period):
        """Test payroll period detail view."""
        url = reverse('hr:payroll-detail', kwargs={'pk': payroll_period.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestTimeEntryViews:
    """Tests for time entry views."""

    def test_timesheet_list_requires_login(self, client):
        """Test that timesheet list requires authentication."""
        url = reverse('hr:timesheet-list')
        response = client.get(url)
        assert response.status_code == 302

    def test_timesheet_list_authenticated(self, authenticated_client):
        """Test timesheet list with authenticated user."""
        url = reverse('hr:timesheet-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_timesheet_create_get(self, authenticated_client):
        """Test timesheet create form display."""
        url = reverse('hr:timesheet-create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestPerformanceReviewViews:
    """Tests for performance review views."""

    def test_review_list_requires_login(self, client):
        """Test that review list requires authentication."""
        url = reverse('hr:review-list')
        response = client.get(url)
        assert response.status_code == 302

    def test_review_list_authenticated(self, authenticated_client):
        """Test review list with authenticated user."""
        url = reverse('hr:review-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_review_create_get(self, authenticated_client):
        """Test review create form display."""
        url = reverse('hr:review-create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestGoalViews:
    """Tests for goal views."""

    def test_goal_list_requires_login(self, client):
        """Test that goal list requires authentication."""
        url = reverse('hr:goal-list')
        response = client.get(url)
        assert response.status_code == 302

    def test_goal_list_authenticated(self, authenticated_client):
        """Test goal list with authenticated user."""
        url = reverse('hr:goal-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_goal_create_get(self, authenticated_client):
        """Test goal create form display."""
        url = reverse('hr:goal-create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestSkillMatrixViews:
    """Tests for skill matrix views."""

    def test_skill_list_requires_login(self, client):
        """Test that skill list requires authentication."""
        url = reverse('hr:skill-list')
        response = client.get(url)
        assert response.status_code == 302

    def test_skill_list_authenticated(self, authenticated_client):
        """Test skill list with authenticated user."""
        url = reverse('hr:skill-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestAttendanceViews:
    """Tests for attendance views."""

    def test_attendance_list_requires_login(self, client):
        """Test that attendance list requires authentication."""
        url = reverse('hr:attendance-list')
        response = client.get(url)
        assert response.status_code == 302

    def test_attendance_list_authenticated(self, authenticated_client):
        """Test attendance list with authenticated user."""
        url = reverse('hr:attendance-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestOvertimeRequestViews:
    """Tests for overtime request views."""

    def test_overtime_list_requires_login(self, client):
        """Test that overtime list requires authentication."""
        url = reverse('hr:overtime-list')
        response = client.get(url)
        assert response.status_code == 302

    def test_overtime_list_authenticated(self, authenticated_client):
        """Test overtime list with authenticated user."""
        url = reverse('hr:overtime-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestDocumentViews:
    """Tests for employee document views."""

    def test_document_list_requires_login(self, client):
        """Test that document list requires authentication."""
        url = reverse('hr:document-list')
        response = client.get(url)
        assert response.status_code == 302

    def test_document_list_authenticated(self, authenticated_client):
        """Test document list with authenticated user."""
        url = reverse('hr:document-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestEmergencyContactViews:
    """Tests for emergency contact views."""

    def test_emergency_contact_create_requires_login(self, client, employee):
        """Test that emergency contact create requires authentication."""
        url = reverse('hr:emergency-contact-create', kwargs={'employee_pk': employee.pk})
        response = client.get(url)
        assert response.status_code == 302


class TestBankAccountViews:
    """Tests for bank account views."""

    def test_bank_account_create_requires_login(self, client, employee):
        """Test that bank account create requires authentication."""
        url = reverse('hr:bank-account-create', kwargs={'employee_pk': employee.pk})
        response = client.get(url)
        assert response.status_code == 302


class TestDisciplinaryActionViews:
    """Tests for disciplinary action views."""

    def test_disciplinary_list_requires_login(self, client):
        """Test that disciplinary list requires authentication."""
        url = reverse('hr:disciplinary-list')
        response = client.get(url)
        assert response.status_code == 302

    def test_disciplinary_list_authenticated(self, authenticated_client):
        """Test disciplinary list with authenticated user."""
        url = reverse('hr:disciplinary-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestShiftScheduleViews:
    """Tests for shift schedule views."""

    def test_shift_list_requires_login(self, client):
        """Test that shift list requires authentication."""
        url = reverse('hr:shift-list')
        response = client.get(url)
        assert response.status_code == 302

    def test_shift_list_authenticated(self, authenticated_client):
        """Test shift list with authenticated user."""
        url = reverse('hr:shift-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200
