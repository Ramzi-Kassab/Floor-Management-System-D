"""
ARDT FMS - HR URLs
"""

from django.urls import path
from . import views

app_name = "hr"

urlpatterns = [
    # Dashboard
    path('', views.HRDashboardView.as_view(), name='dashboard'),

    # Employees
    path('employees/', views.EmployeeListView.as_view(), name='employee-list'),
    path('employees/create/', views.EmployeeCreateView.as_view(), name='employee-create'),
    path('employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee-detail'),
    path('employees/<int:pk>/edit/', views.EmployeeUpdateView.as_view(), name='employee-update'),
    path('employees/<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee-delete'),

    # Documents
    path('documents/', views.DocumentListView.as_view(), name='document-list'),
    path('documents/create/', views.DocumentCreateView.as_view(), name='document-create'),
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<int:pk>/edit/', views.DocumentUpdateView.as_view(), name='document-update'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document-delete'),

    # Emergency Contacts
    path('emergency-contacts/create/', views.EmergencyContactCreateView.as_view(), name='emergency-contact-create'),
    path('emergency-contacts/<int:pk>/edit/', views.EmergencyContactUpdateView.as_view(), name='emergency-contact-update'),
    path('emergency-contacts/<int:pk>/delete/', views.EmergencyContactDeleteView.as_view(), name='emergency-contact-delete'),

    # Bank Accounts
    path('bank-accounts/create/', views.BankAccountCreateView.as_view(), name='bank-account-create'),
    path('bank-accounts/<int:pk>/edit/', views.BankAccountUpdateView.as_view(), name='bank-account-update'),
    path('bank-accounts/<int:pk>/delete/', views.BankAccountDeleteView.as_view(), name='bank-account-delete'),

    # Performance Reviews
    path('reviews/', views.ReviewListView.as_view(), name='review-list'),
    path('reviews/create/', views.ReviewCreateView.as_view(), name='review-create'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
    path('reviews/<int:pk>/edit/', views.ReviewUpdateView.as_view(), name='review-update'),
    path('reviews/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review-delete'),

    # Goals
    path('goals/', views.GoalListView.as_view(), name='goal-list'),
    path('goals/create/', views.GoalCreateView.as_view(), name='goal-create'),
    path('goals/<int:pk>/', views.GoalDetailView.as_view(), name='goal-detail'),
    path('goals/<int:pk>/edit/', views.GoalUpdateView.as_view(), name='goal-update'),
    path('goals/<int:pk>/delete/', views.GoalDeleteView.as_view(), name='goal-delete'),

    # Skills
    path('skills/', views.SkillListView.as_view(), name='skill-list'),
    path('skills/create/', views.SkillCreateView.as_view(), name='skill-create'),
    path('skills/<int:pk>/edit/', views.SkillUpdateView.as_view(), name='skill-update'),
    path('skills/<int:pk>/delete/', views.SkillDeleteView.as_view(), name='skill-delete'),

    # Disciplinary Actions
    path('disciplinary/', views.DisciplinaryListView.as_view(), name='disciplinary-list'),
    path('disciplinary/create/', views.DisciplinaryCreateView.as_view(), name='disciplinary-create'),
    path('disciplinary/<int:pk>/', views.DisciplinaryDetailView.as_view(), name='disciplinary-detail'),
    path('disciplinary/<int:pk>/edit/', views.DisciplinaryUpdateView.as_view(), name='disciplinary-update'),
    path('disciplinary/<int:pk>/delete/', views.DisciplinaryDeleteView.as_view(), name='disciplinary-delete'),

    # Shift Schedules
    path('shifts/', views.ShiftListView.as_view(), name='shift-list'),
    path('shifts/create/', views.ShiftCreateView.as_view(), name='shift-create'),
    path('shifts/<int:pk>/edit/', views.ShiftUpdateView.as_view(), name='shift-update'),
    path('shifts/<int:pk>/delete/', views.ShiftDeleteView.as_view(), name='shift-delete'),

    # Time Entries
    path('time-entries/', views.TimeEntryListView.as_view(), name='timeentry-list'),
    path('time-entries/create/', views.TimeEntryCreateView.as_view(), name='timeentry-create'),
    path('time-entries/<int:pk>/edit/', views.TimeEntryUpdateView.as_view(), name='timeentry-update'),
    path('time-entries/<int:pk>/delete/', views.TimeEntryDeleteView.as_view(), name='timeentry-delete'),
    path('time-entries/<int:pk>/approve/', views.TimeEntryApproveView.as_view(), name='timeentry-approve'),

    # Leave Requests
    path('leaves/', views.LeaveListView.as_view(), name='leave-list'),
    path('leaves/create/', views.LeaveCreateView.as_view(), name='leave-create'),
    path('leaves/<int:pk>/', views.LeaveDetailView.as_view(), name='leave-detail'),
    path('leaves/<int:pk>/edit/', views.LeaveUpdateView.as_view(), name='leave-update'),
    path('leaves/<int:pk>/delete/', views.LeaveDeleteView.as_view(), name='leave-delete'),
    path('leaves/<int:pk>/approve/', views.LeaveApproveView.as_view(), name='leave-approve'),
    path('leaves/<int:pk>/reject/', views.LeaveRejectView.as_view(), name='leave-reject'),

    # Payroll Periods
    path('payroll/', views.PayrollListView.as_view(), name='payroll-list'),
    path('payroll/create/', views.PayrollCreateView.as_view(), name='payroll-create'),
    path('payroll/<int:pk>/', views.PayrollDetailView.as_view(), name='payroll-detail'),
    path('payroll/<int:pk>/edit/', views.PayrollUpdateView.as_view(), name='payroll-update'),

    # Legacy: Attendance
    path('attendance/', views.AttendanceListView.as_view(), name='attendance-list'),
    path('attendance/create/', views.AttendanceCreateView.as_view(), name='attendance-create'),

    # Legacy: Leave Types
    path('leave-types/', views.LeaveTypeListView.as_view(), name='leavetype-list'),
    path('leave-types/create/', views.LeaveTypeCreateView.as_view(), name='leavetype-create'),
    path('leave-types/<int:pk>/edit/', views.LeaveTypeUpdateView.as_view(), name='leavetype-update'),

    # Legacy: Overtime
    path('overtime/', views.OvertimeListView.as_view(), name='overtime-list'),
    path('overtime/create/', views.OvertimeCreateView.as_view(), name='overtime-create'),
    path('overtime/<int:pk>/approve/', views.OvertimeApproveView.as_view(), name='overtime-approve'),
]
