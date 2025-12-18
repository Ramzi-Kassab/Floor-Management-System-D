"""
ARDT FMS - HR Forms
"""

from django import forms
from .models import (
    Employee, EmployeeDocument, EmergencyContact, BankAccount,
    PerformanceReview, Goal, SkillMatrix, DisciplinaryAction,
    ShiftSchedule, TimeEntry, LeaveRequest, PayrollPeriod,
    Attendance, LeaveType, OvertimeRequest
)


TAILWIND_INPUT = "w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
TAILWIND_SELECT = TAILWIND_INPUT
TAILWIND_TEXTAREA = TAILWIND_INPUT + " resize-y"
TAILWIND_CHECKBOX = "w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"


# =============================================================================
# EMPLOYEE MANAGEMENT FORMS
# =============================================================================


class EmployeeForm(forms.ModelForm):
    """Form for creating/editing employees."""

    class Meta:
        model = Employee
        fields = [
            'user', 'employee_number', 'badge_number',
            'date_of_birth', 'national_id', 'passport_number', 'nationality', 'marital_status',
            'personal_email', 'mobile_phone', 'home_phone',
            'address_line_1', 'address_line_2', 'city', 'state_province', 'postal_code', 'country',
            'employment_type', 'employment_status', 'hire_date', 'probation_end_date',
            'department', 'job_title', 'job_description', 'manager', 'work_location',
            'pay_type', 'pay_rate', 'currency_code', 'pay_grade',
            'standard_hours_per_week', 'work_shift',
            'annual_leave_days', 'sick_leave_days', 'benefits_enrolled',
            'is_field_technician', 'notes'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'employee_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'badge_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'date_of_birth': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'national_id': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'passport_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'nationality': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'marital_status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'personal_email': forms.EmailInput(attrs={'class': TAILWIND_INPUT}),
            'mobile_phone': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'home_phone': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'address_line_1': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'address_line_2': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'city': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'state_province': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'postal_code': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'country': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'employment_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'employment_status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'hire_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'probation_end_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'department': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'job_title': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'job_description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'manager': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'work_location': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'pay_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'pay_rate': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'currency_code': forms.TextInput(attrs={'class': TAILWIND_INPUT, 'maxlength': 3}),
            'pay_grade': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'standard_hours_per_week': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'work_shift': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'annual_leave_days': forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'sick_leave_days': forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'benefits_enrolled': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'is_field_technician': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
        }


class EmployeeDocumentForm(forms.ModelForm):
    """Form for employee documents."""

    class Meta:
        model = EmployeeDocument
        fields = [
            'employee', 'document_type', 'title', 'description',
            'file_path', 'file_name', 'file_size', 'file_type',
            'issue_date', 'expiry_date', 'status',
            'requires_employee_signature', 'requires_hr_signature',
            'is_confidential', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'document_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'title': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'file_path': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'file_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'file_size': forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'file_type': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'issue_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'requires_employee_signature': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'requires_hr_signature': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'is_confidential': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }


class EmergencyContactForm(forms.ModelForm):
    """Form for emergency contacts."""

    class Meta:
        model = EmergencyContact
        fields = [
            'employee', 'full_name', 'relationship', 'primary_phone',
            'alternate_phone', 'email', 'address', 'is_primary', 'priority_order', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'full_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'relationship': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'primary_phone': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'alternate_phone': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'email': forms.EmailInput(attrs={'class': TAILWIND_INPUT}),
            'address': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'is_primary': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'priority_order': forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }


class BankAccountForm(forms.ModelForm):
    """Form for bank accounts."""

    class Meta:
        model = BankAccount
        fields = [
            'employee', 'bank_name', 'bank_branch', 'bank_code',
            'account_type', 'account_number', 'account_holder_name',
            'iban', 'is_primary', 'is_active', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'bank_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'bank_branch': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'bank_code': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'account_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'account_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'account_holder_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'iban': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'is_primary': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'is_active': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }


# =============================================================================
# PERFORMANCE & SKILLS FORMS
# =============================================================================


class PerformanceReviewForm(forms.ModelForm):
    """Form for performance reviews."""

    class Meta:
        model = PerformanceReview
        fields = [
            'employee', 'reviewer', 'review_type', 'status',
            'review_period_start', 'review_period_end', 'review_date',
            'overall_rating', 'technical_skills_rating', 'communication_rating',
            'teamwork_rating', 'leadership_rating', 'initiative_rating', 'quality_of_work_rating',
            'strengths', 'areas_for_improvement', 'achievements', 'challenges',
            'development_plan', 'training_recommended', 'goals_met_percentage',
            'promotion_recommended', 'salary_increase_recommended', 'salary_increase_percentage',
            'hr_comments'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'reviewer': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'review_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'review_period_start': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'review_period_end': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'review_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'overall_rating': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'technical_skills_rating': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'min': 1, 'max': 5}),
            'communication_rating': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'min': 1, 'max': 5}),
            'teamwork_rating': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'min': 1, 'max': 5}),
            'leadership_rating': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'min': 1, 'max': 5}),
            'initiative_rating': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'min': 1, 'max': 5}),
            'quality_of_work_rating': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'min': 1, 'max': 5}),
            'strengths': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'areas_for_improvement': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'achievements': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'challenges': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'development_plan': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'training_recommended': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'goals_met_percentage': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'promotion_recommended': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'salary_increase_recommended': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'salary_increase_percentage': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'hr_comments': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }


class GoalForm(forms.ModelForm):
    """Form for goals."""

    class Meta:
        model = Goal
        fields = [
            'employee', 'title', 'description', 'goal_type', 'category',
            'status', 'start_date', 'target_date', 'progress_percentage',
            'measurement_criteria', 'related_performance_review', 'assigned_by', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'title': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'goal_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'category': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'start_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'target_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'progress_percentage': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'min': 0, 'max': 100}),
            'measurement_criteria': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'related_performance_review': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'assigned_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }


class SkillMatrixForm(forms.ModelForm):
    """Form for skills."""

    class Meta:
        model = SkillMatrix
        fields = [
            'employee', 'skill_name', 'skill_category', 'proficiency_level',
            'years_of_experience', 'last_used_date',
            'certified', 'certification_details', 'certification_expiry',
            'required_for_position', 'training_recommended', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'skill_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'skill_category': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'proficiency_level': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'years_of_experience': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'last_used_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'certified': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'certification_details': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'certification_expiry': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'required_for_position': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'training_recommended': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }


class DisciplinaryActionForm(forms.ModelForm):
    """Form for disciplinary actions."""

    class Meta:
        model = DisciplinaryAction
        fields = [
            'employee', 'action_type', 'severity', 'status',
            'incident_date', 'incident_description', 'policy_violated', 'witnesses',
            'action_taken', 'consequences',
            'corrective_action_required', 'corrective_action_deadline',
            'expiry_date', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'action_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'severity': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'incident_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'incident_description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 4}),
            'policy_violated': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'witnesses': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'action_taken': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'consequences': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'corrective_action_required': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'corrective_action_deadline': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }


# =============================================================================
# TIME & SCHEDULING FORMS
# =============================================================================


class ShiftScheduleForm(forms.ModelForm):
    """Form for shift schedules."""

    class Meta:
        model = ShiftSchedule
        fields = [
            'employee', 'shift_type', 'status',
            'shift_date', 'start_time', 'end_time', 'break_duration_minutes',
            'work_location', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'shift_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'shift_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'break_duration_minutes': forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'work_location': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }


class TimeEntryForm(forms.ModelForm):
    """Form for time entries."""

    class Meta:
        model = TimeEntry
        fields = [
            'employee', 'entry_type', 'status',
            'entry_date', 'clock_in_time', 'clock_out_time',
            'total_hours', 'break_hours', 'overtime_hours',
            'location', 'work_description', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'entry_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'entry_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'clock_in_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'clock_out_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'total_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'break_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'overtime_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'location': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'work_description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }


class LeaveRequestForm(forms.ModelForm):
    """Form for leave requests."""

    class Meta:
        model = LeaveRequest
        fields = [
            'employee', 'leave_type', 'status',
            'start_date', 'end_date', 'is_half_day', 'total_days',
            'reason', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'leave_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'start_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'is_half_day': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'total_days': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.5'}),
            'reason': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }


class PayrollPeriodForm(forms.ModelForm):
    """Form for payroll periods."""

    class Meta:
        model = PayrollPeriod
        fields = [
            'period_type', 'status',
            'start_date', 'end_date', 'pay_date',
            'notes'
        ]
        widgets = {
            'period_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'start_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'pay_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }


# =============================================================================
# LEGACY FORMS
# =============================================================================


class AttendanceForm(forms.ModelForm):
    """Form for attendance (legacy)."""

    class Meta:
        model = Attendance
        fields = ['user', 'date', 'status', 'first_in', 'last_out', 'total_hours', 'notes']
        widgets = {
            'user': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'first_in': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'last_out': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'total_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }


class LeaveTypeForm(forms.ModelForm):
    """Form for leave types (legacy)."""

    class Meta:
        model = LeaveType
        fields = ['code', 'name', 'days_per_year', 'is_paid', 'requires_approval', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'days_per_year': forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'is_paid': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'requires_approval': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'is_active': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
        }


class OvertimeRequestForm(forms.ModelForm):
    """Form for overtime requests (legacy)."""

    class Meta:
        model = OvertimeRequest
        fields = ['user', 'date', 'hours', 'reason', 'status']
        widgets = {
            'user': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.5'}),
            'reason': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
        }


# =============================================================================
# FILTER FORMS
# =============================================================================


class EmployeeFilterForm(forms.Form):
    """Filter form for employees."""
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': TAILWIND_INPUT,
        'placeholder': 'Search employees...'
    }))
    status = forms.ChoiceField(required=False, choices=[('', 'All Status')] + list(Employee.EmploymentStatus.choices), widget=forms.Select(attrs={'class': TAILWIND_SELECT}))
    department = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': TAILWIND_INPUT,
        'placeholder': 'Department'
    }))
    employment_type = forms.ChoiceField(required=False, choices=[('', 'All Types')] + list(Employee.EmploymentType.choices), widget=forms.Select(attrs={'class': TAILWIND_SELECT}))


class TimeEntryFilterForm(forms.Form):
    """Filter form for time entries."""
    employee = forms.ModelChoiceField(required=False, queryset=Employee.objects.all(), widget=forms.Select(attrs={'class': TAILWIND_SELECT}))
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}))
    status = forms.ChoiceField(required=False, choices=[('', 'All Status')] + list(TimeEntry.Status.choices), widget=forms.Select(attrs={'class': TAILWIND_SELECT}))
