"""
ARDT FMS - HR & Workforce Management Admin
Sprint 8: Final Sprint - System Completion
"""

from django.contrib import admin

from .models import (
    # Sprint 8 Models
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
    # Legacy Models
    Attendance,
    AttendancePunch,
    LeaveType,
    OvertimeRequest,
)


# =============================================================================
# WEEK 1: EMPLOYEE MANAGEMENT
# =============================================================================


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'employee_number', 'user', 'department', 'job_title',
        'employment_status', 'employment_type', 'hire_date'
    ]
    list_filter = [
        'employment_status', 'employment_type', 'department',
        'is_field_technician', 'pay_type'
    ]
    search_fields = [
        'employee_number', 'user__username', 'user__first_name',
        'user__last_name', 'job_title', 'department'
    ]
    date_hierarchy = 'hire_date'
    ordering = ['employee_number']
    readonly_fields = ['employee_number', 'created_at', 'updated_at']
    fieldsets = (
        ('Employee Identification', {
            'fields': ('user', 'employee_number', 'badge_number')
        }),
        ('Personal Information', {
            'fields': (
                'date_of_birth', 'national_id', 'passport_number',
                'nationality', 'marital_status'
            )
        }),
        ('Contact Information', {
            'fields': ('personal_email', 'mobile_phone', 'home_phone')
        }),
        ('Address', {
            'fields': (
                'address_line_1', 'address_line_2', 'city',
                'state_province', 'postal_code', 'country'
            )
        }),
        ('Employment Details', {
            'fields': (
                'employment_type', 'employment_status', 'hire_date',
                'probation_end_date', 'termination_date', 'termination_reason'
            )
        }),
        ('Organization', {
            'fields': (
                'department', 'job_title', 'job_description',
                'manager', 'work_location'
            )
        }),
        ('Compensation', {
            'fields': (
                'pay_type', 'pay_rate', 'currency_code', 'pay_grade',
                'standard_hours_per_week', 'work_shift'
            )
        }),
        ('Benefits', {
            'fields': ('annual_leave_days', 'sick_leave_days', 'benefits_enrolled')
        }),
        ('Performance', {
            'fields': (
                'last_review_date', 'next_review_date', 'performance_rating'
            )
        }),
        ('Compliance', {
            'fields': (
                'background_check_completed', 'background_check_date',
                'work_permit_number', 'work_permit_expiry'
            )
        }),
        ('Field Service', {
            'fields': ('is_field_technician',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'document_number', 'employee', 'document_type', 'title',
        'status', 'expiry_date'
    ]
    list_filter = ['document_type', 'status', 'is_confidential']
    search_fields = ['document_number', 'title', 'employee__employee_number']
    date_hierarchy = 'uploaded_at'
    ordering = ['-uploaded_at']
    readonly_fields = ['document_number', 'uploaded_at', 'updated_at']


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'full_name', 'relationship', 'primary_phone',
        'is_primary', 'priority_order'
    ]
    list_filter = ['relationship', 'is_primary']
    search_fields = ['full_name', 'employee__employee_number', 'primary_phone']
    ordering = ['employee', 'priority_order']


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'bank_name', 'account_type', 'is_primary',
        'is_active', 'verified'
    ]
    list_filter = ['account_type', 'is_primary', 'is_active', 'verified']
    search_fields = ['employee__employee_number', 'bank_name', 'account_holder_name']
    ordering = ['employee', '-is_primary']
    readonly_fields = ['created_at', 'updated_at']


# =============================================================================
# WEEK 2: PERFORMANCE & SKILLS
# =============================================================================


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = [
        'review_number', 'employee', 'review_type', 'review_date',
        'overall_rating', 'status'
    ]
    list_filter = ['review_type', 'status', 'overall_rating']
    search_fields = ['review_number', 'employee__employee_number']
    date_hierarchy = 'review_date'
    ordering = ['-review_date']
    readonly_fields = ['review_number', 'created_at', 'updated_at']


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = [
        'goal_number', 'employee', 'title', 'goal_type',
        'status', 'progress_percentage', 'target_date'
    ]
    list_filter = ['goal_type', 'category', 'status']
    search_fields = ['goal_number', 'title', 'employee__employee_number']
    date_hierarchy = 'target_date'
    ordering = ['-target_date']
    readonly_fields = ['goal_number', 'created_at', 'updated_at']


@admin.register(SkillMatrix)
class SkillMatrixAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'skill_name', 'skill_category', 'proficiency_level',
        'years_of_experience', 'certified'
    ]
    list_filter = ['skill_category', 'proficiency_level', 'certified']
    search_fields = ['skill_name', 'employee__employee_number']
    ordering = ['employee', 'skill_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DisciplinaryAction)
class DisciplinaryActionAdmin(admin.ModelAdmin):
    list_display = [
        'action_number', 'employee', 'action_type', 'severity',
        'incident_date', 'status'
    ]
    list_filter = ['action_type', 'severity', 'status']
    search_fields = ['action_number', 'employee__employee_number']
    date_hierarchy = 'incident_date'
    ordering = ['-incident_date']
    readonly_fields = ['action_number', 'created_at', 'updated_at']


# =============================================================================
# WEEK 3: TIME & SCHEDULING
# =============================================================================


@admin.register(ShiftSchedule)
class ShiftScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'shift_date', 'shift_type', 'start_time',
        'end_time', 'status'
    ]
    list_filter = ['shift_type', 'status']
    search_fields = ['employee__employee_number']
    date_hierarchy = 'shift_date'
    ordering = ['-shift_date', 'start_time']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = [
        'entry_number', 'employee', 'entry_date', 'entry_type',
        'total_hours', 'overtime_hours', 'status'
    ]
    list_filter = ['entry_type', 'status']
    search_fields = ['entry_number', 'employee__employee_number']
    date_hierarchy = 'entry_date'
    ordering = ['-entry_date']
    readonly_fields = ['entry_number', 'created_at', 'updated_at']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_number', 'employee', 'leave_type', 'start_date',
        'end_date', 'total_days', 'status'
    ]
    list_filter = ['leave_type', 'status']
    search_fields = ['request_number', 'employee__employee_number']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    readonly_fields = ['request_number', 'created_at', 'updated_at']


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = [
        'period_number', 'period_type', 'start_date', 'end_date',
        'pay_date', 'total_employees', 'status'
    ]
    list_filter = ['period_type', 'status']
    search_fields = ['period_number']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    readonly_fields = ['period_number', 'created_at', 'updated_at']


# =============================================================================
# LEGACY MODELS (P4 Skeleton - Preserved)
# =============================================================================


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'status', 'total_hours']
    list_filter = ['status']
    search_fields = ['user__username']
    date_hierarchy = 'date'


@admin.register(AttendancePunch)
class AttendancePunchAdmin(admin.ModelAdmin):
    list_display = ['attendance', 'punch_type', 'punch_time', 'location']
    list_filter = ['punch_type']


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'days_per_year', 'is_paid', 'is_active']
    list_filter = ['is_paid', 'is_active']


@admin.register(OvertimeRequest)
class OvertimeRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'hours', 'status']
    list_filter = ['status']
    date_hierarchy = 'date'
