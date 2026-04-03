"""
ARDT FMS - HR Views
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)

from .models import (
    Employee, EmployeeDocument, EmergencyContact, BankAccount,
    PerformanceReview, Goal, SkillMatrix, DisciplinaryAction,
    ShiftSchedule, TimeEntry, LeaveRequest, PayrollPeriod,
    Attendance, LeaveType, OvertimeRequest
)
from .forms import (
    EmployeeForm, EmployeeDocumentForm, EmergencyContactForm, BankAccountForm,
    PerformanceReviewForm, GoalForm, SkillMatrixForm, DisciplinaryActionForm,
    ShiftScheduleForm, TimeEntryForm, LeaveRequestForm, PayrollPeriodForm,
    AttendanceForm, LeaveTypeForm, OvertimeRequestForm
)


# =============================================================================
# DASHBOARD
# =============================================================================


class HRDashboardView(LoginRequiredMixin, TemplateView):
    """HR Dashboard with overview statistics."""
    template_name = 'hr/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Employee stats
        context['total_employees'] = Employee.objects.filter(employment_status='ACTIVE').count()
        context['new_this_month'] = Employee.objects.filter(
            hire_date__year=today.year,
            hire_date__month=today.month
        ).count()
        context['on_leave'] = Employee.objects.filter(employment_status='ON_LEAVE').count()

        # Leave requests
        context['pending_leaves'] = LeaveRequest.objects.filter(status='PENDING').count()
        context['approved_leaves_today'] = LeaveRequest.objects.filter(
            status='APPROVED',
            start_date__lte=today,
            end_date__gte=today
        ).count()

        # Time entries
        context['pending_timesheets'] = TimeEntry.objects.filter(status='SUBMITTED').count()

        # Performance reviews
        context['pending_reviews'] = PerformanceReview.objects.filter(
            status__in=['DRAFT', 'PENDING_EMPLOYEE', 'PENDING_MANAGER', 'PENDING_HR']
        ).count()

        # Payroll
        context['open_payroll_periods'] = PayrollPeriod.objects.filter(status='OPEN').count()

        # Recent employees
        context['recent_employees'] = Employee.objects.select_related('user').order_by('-created_at')[:5]

        # Pending leave requests
        context['recent_leave_requests'] = LeaveRequest.objects.select_related(
            'employee__user'
        ).filter(status='PENDING').order_by('-created_at')[:5]

        context['page_title'] = 'HR Dashboard'
        return context


# =============================================================================
# EMPLOYEE MANAGEMENT
# =============================================================================


class EmployeeListView(LoginRequiredMixin, ListView):
    """List all employees."""
    model = Employee
    template_name = 'hr/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 20

    def get_queryset(self):
        queryset = Employee.objects.select_related('user', 'manager__user').order_by('-created_at')

        # Search
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(employee_number__icontains=q) |
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(user__email__icontains=q) |
                Q(department__icontains=q) |
                Q(job_title__icontains=q)
            )

        # Filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(employment_status=status)

        emp_type = self.request.GET.get('type')
        if emp_type:
            queryset = queryset.filter(employment_type=emp_type)

        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(department__icontains=department)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Employees'
        context['search_query'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_type'] = self.request.GET.get('type', '')
        context['statuses'] = Employee.EmploymentStatus.choices
        context['types'] = Employee.EmploymentType.choices
        return context


class EmployeeDetailView(LoginRequiredMixin, DetailView):
    """View employee details."""
    model = Employee
    template_name = 'hr/employee_detail.html'
    context_object_name = 'employee'

    def get_queryset(self):
        return Employee.objects.select_related(
            'user', 'manager__user', 'created_by'
        ).prefetch_related(
            'documents', 'emergency_contacts', 'bank_accounts',
            'performance_reviews', 'goals', 'skills',
            'disciplinary_actions', 'employee_leave_requests'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.object.employee_number
        context['emergency_contacts'] = self.object.emergency_contacts.all()[:3]
        context['recent_documents'] = self.object.documents.all()[:5]
        context['recent_reviews'] = self.object.performance_reviews.all()[:3]
        context['active_goals'] = self.object.goals.filter(status__in=['NOT_STARTED', 'IN_PROGRESS'])[:5]
        context['skills'] = self.object.skills.all()[:10]
        return context


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    """Create new employee."""
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Employee created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:employee-detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Add Employee'
        return context


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    """Update employee."""
    model = Employee
    form_class = EmployeeForm
    template_name = 'hr/employee_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Employee updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:employee-detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit {self.object.employee_number}'
        return context


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete employee."""
    model = Employee
    template_name = 'hr/employee_confirm_delete.html'
    success_url = reverse_lazy('hr:employee-list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Employee deleted successfully.')
        return super().delete(request, *args, **kwargs)


# =============================================================================
# EMPLOYEE DOCUMENTS
# =============================================================================


class DocumentListView(LoginRequiredMixin, ListView):
    """List employee documents."""
    model = EmployeeDocument
    template_name = 'hr/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        queryset = EmployeeDocument.objects.select_related('employee__user').order_by('-uploaded_at')

        employee_id = self.request.GET.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        doc_type = self.request.GET.get('type')
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Employee Documents'
        context['doc_types'] = EmployeeDocument.DocumentType.choices
        return context


class DocumentDetailView(LoginRequiredMixin, DetailView):
    """View document details."""
    model = EmployeeDocument
    template_name = 'hr/document_detail.html'
    context_object_name = 'document'

    def get_queryset(self):
        return EmployeeDocument.objects.select_related('employee__user', 'uploaded_by', 'hr_signed_by')


class DocumentCreateView(LoginRequiredMixin, CreateView):
    """Create new document."""
    model = EmployeeDocument
    form_class = EmployeeDocumentForm
    template_name = 'hr/document_form.html'

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Document uploaded successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:document-detail', kwargs={'pk': self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        employee_id = self.request.GET.get('employee')
        if employee_id:
            initial['employee'] = employee_id
        return initial


class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    """Update document."""
    model = EmployeeDocument
    form_class = EmployeeDocumentForm
    template_name = 'hr/document_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Document updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:document-detail', kwargs={'pk': self.object.pk})


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete document."""
    model = EmployeeDocument
    template_name = 'hr/document_confirm_delete.html'
    success_url = reverse_lazy('hr:document-list')


# =============================================================================
# EMERGENCY CONTACTS
# =============================================================================


class EmergencyContactCreateView(LoginRequiredMixin, CreateView):
    """Create emergency contact."""
    model = EmergencyContact
    form_class = EmergencyContactForm
    template_name = 'hr/emergency_contact_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Emergency contact added successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:employee-detail', kwargs={'pk': self.object.employee.pk})

    def get_initial(self):
        initial = super().get_initial()
        employee_id = self.request.GET.get('employee')
        if employee_id:
            initial['employee'] = employee_id
        return initial


class EmergencyContactUpdateView(LoginRequiredMixin, UpdateView):
    """Update emergency contact."""
    model = EmergencyContact
    form_class = EmergencyContactForm
    template_name = 'hr/emergency_contact_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Emergency contact updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:employee-detail', kwargs={'pk': self.object.employee.pk})


class EmergencyContactDeleteView(LoginRequiredMixin, DeleteView):
    """Delete emergency contact."""
    model = EmergencyContact
    template_name = 'hr/emergency_contact_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('hr:employee-detail', kwargs={'pk': self.object.employee.pk})


# =============================================================================
# BANK ACCOUNTS
# =============================================================================


class BankAccountCreateView(LoginRequiredMixin, CreateView):
    """Create bank account."""
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'hr/bank_account_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Bank account added successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:employee-detail', kwargs={'pk': self.object.employee.pk})

    def get_initial(self):
        initial = super().get_initial()
        employee_id = self.request.GET.get('employee')
        if employee_id:
            initial['employee'] = employee_id
        return initial


class BankAccountUpdateView(LoginRequiredMixin, UpdateView):
    """Update bank account."""
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'hr/bank_account_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Bank account updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:employee-detail', kwargs={'pk': self.object.employee.pk})


class BankAccountDeleteView(LoginRequiredMixin, DeleteView):
    """Delete bank account."""
    model = BankAccount
    template_name = 'hr/bank_account_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('hr:employee-detail', kwargs={'pk': self.object.employee.pk})


# =============================================================================
# PERFORMANCE REVIEWS
# =============================================================================


class ReviewListView(LoginRequiredMixin, ListView):
    """List performance reviews."""
    model = PerformanceReview
    template_name = 'hr/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        queryset = PerformanceReview.objects.select_related(
            'employee__user', 'reviewer'
        ).order_by('-review_date')

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        review_type = self.request.GET.get('type')
        if review_type:
            queryset = queryset.filter(review_type=review_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Performance Reviews'
        context['statuses'] = PerformanceReview.Status.choices
        context['types'] = PerformanceReview.ReviewType.choices
        return context


class ReviewDetailView(LoginRequiredMixin, DetailView):
    """View review details."""
    model = PerformanceReview
    template_name = 'hr/review_detail.html'
    context_object_name = 'review'

    def get_queryset(self):
        return PerformanceReview.objects.select_related(
            'employee__user', 'reviewer', 'hr_approved_by'
        ).prefetch_related('goals')


class ReviewCreateView(LoginRequiredMixin, CreateView):
    """Create performance review."""
    model = PerformanceReview
    form_class = PerformanceReviewForm
    template_name = 'hr/review_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Performance review created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:review-detail', kwargs={'pk': self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        initial['reviewer'] = self.request.user
        employee_id = self.request.GET.get('employee')
        if employee_id:
            initial['employee'] = employee_id
        return initial


class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    """Update performance review."""
    model = PerformanceReview
    form_class = PerformanceReviewForm
    template_name = 'hr/review_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Performance review updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:review-detail', kwargs={'pk': self.object.pk})


class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    """Delete performance review."""
    model = PerformanceReview
    template_name = 'hr/review_confirm_delete.html'
    success_url = reverse_lazy('hr:review-list')


# =============================================================================
# GOALS
# =============================================================================


class GoalListView(LoginRequiredMixin, ListView):
    """List goals."""
    model = Goal
    template_name = 'hr/goal_list.html'
    context_object_name = 'goals'
    paginate_by = 20

    def get_queryset(self):
        queryset = Goal.objects.select_related('employee__user', 'assigned_by').order_by('-target_date')

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Goals'
        context['statuses'] = Goal.Status.choices
        context['categories'] = Goal.Category.choices
        return context


class GoalDetailView(LoginRequiredMixin, DetailView):
    """View goal details."""
    model = Goal
    template_name = 'hr/goal_detail.html'
    context_object_name = 'goal'

    def get_queryset(self):
        return Goal.objects.select_related('employee__user', 'assigned_by', 'related_performance_review')


class GoalCreateView(LoginRequiredMixin, CreateView):
    """Create goal."""
    model = Goal
    form_class = GoalForm
    template_name = 'hr/goal_form.html'

    def form_valid(self, form):
        form.instance.assigned_by = self.request.user
        messages.success(self.request, 'Goal created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:goal-detail', kwargs={'pk': self.object.pk})


class GoalUpdateView(LoginRequiredMixin, UpdateView):
    """Update goal."""
    model = Goal
    form_class = GoalForm
    template_name = 'hr/goal_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Goal updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:goal-detail', kwargs={'pk': self.object.pk})


class GoalDeleteView(LoginRequiredMixin, DeleteView):
    """Delete goal."""
    model = Goal
    template_name = 'hr/goal_confirm_delete.html'
    success_url = reverse_lazy('hr:goal-list')


# =============================================================================
# SKILLS
# =============================================================================


class SkillListView(LoginRequiredMixin, ListView):
    """List skills."""
    model = SkillMatrix
    template_name = 'hr/skill_list.html'
    context_object_name = 'skills'
    paginate_by = 20

    def get_queryset(self):
        queryset = SkillMatrix.objects.select_related('employee__user', 'verified_by').order_by('skill_name')

        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(skill_category=category)

        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(proficiency_level=level)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Skills Matrix'
        context['categories'] = SkillMatrix.SkillCategory.choices
        context['levels'] = SkillMatrix.ProficiencyLevel.choices
        return context


class SkillCreateView(LoginRequiredMixin, CreateView):
    """Create skill."""
    model = SkillMatrix
    form_class = SkillMatrixForm
    template_name = 'hr/skill_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Skill added successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:employee-detail', kwargs={'pk': self.object.employee.pk})


class SkillUpdateView(LoginRequiredMixin, UpdateView):
    """Update skill."""
    model = SkillMatrix
    form_class = SkillMatrixForm
    template_name = 'hr/skill_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Skill updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:employee-detail', kwargs={'pk': self.object.employee.pk})


class SkillDeleteView(LoginRequiredMixin, DeleteView):
    """Delete skill."""
    model = SkillMatrix
    template_name = 'hr/skill_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('hr:employee-detail', kwargs={'pk': self.object.employee.pk})


# =============================================================================
# DISCIPLINARY ACTIONS
# =============================================================================


class DisciplinaryListView(LoginRequiredMixin, ListView):
    """List disciplinary actions."""
    model = DisciplinaryAction
    template_name = 'hr/disciplinary_list.html'
    context_object_name = 'actions'
    paginate_by = 20

    def get_queryset(self):
        queryset = DisciplinaryAction.objects.select_related(
            'employee__user', 'issued_by'
        ).order_by('-incident_date')

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        action_type = self.request.GET.get('type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Disciplinary Actions'
        context['statuses'] = DisciplinaryAction.Status.choices
        context['types'] = DisciplinaryAction.ActionType.choices
        return context


class DisciplinaryDetailView(LoginRequiredMixin, DetailView):
    """View disciplinary action details."""
    model = DisciplinaryAction
    template_name = 'hr/disciplinary_detail.html'
    context_object_name = 'action'

    def get_queryset(self):
        return DisciplinaryAction.objects.select_related('employee__user', 'issued_by')


class DisciplinaryCreateView(LoginRequiredMixin, CreateView):
    """Create disciplinary action."""
    model = DisciplinaryAction
    form_class = DisciplinaryActionForm
    template_name = 'hr/disciplinary_form.html'

    def form_valid(self, form):
        form.instance.issued_by = self.request.user
        messages.success(self.request, 'Disciplinary action created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:disciplinary-detail', kwargs={'pk': self.object.pk})


class DisciplinaryUpdateView(LoginRequiredMixin, UpdateView):
    """Update disciplinary action."""
    model = DisciplinaryAction
    form_class = DisciplinaryActionForm
    template_name = 'hr/disciplinary_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Disciplinary action updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:disciplinary-detail', kwargs={'pk': self.object.pk})


class DisciplinaryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete disciplinary action."""
    model = DisciplinaryAction
    template_name = 'hr/disciplinary_confirm_delete.html'
    success_url = reverse_lazy('hr:disciplinary-list')


# =============================================================================
# SHIFT SCHEDULES
# =============================================================================


class ShiftListView(LoginRequiredMixin, ListView):
    """List shift schedules."""
    model = ShiftSchedule
    template_name = 'hr/shift_list.html'
    context_object_name = 'shifts'
    paginate_by = 20

    def get_queryset(self):
        queryset = ShiftSchedule.objects.select_related('employee__user').order_by('-shift_date')

        employee_id = self.request.GET.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        date = self.request.GET.get('date')
        if date:
            queryset = queryset.filter(shift_date=date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Shift Schedules'
        context['statuses'] = ShiftSchedule.Status.choices
        context['types'] = ShiftSchedule.ShiftType.choices
        return context


class ShiftCreateView(LoginRequiredMixin, CreateView):
    """Create shift schedule."""
    model = ShiftSchedule
    form_class = ShiftScheduleForm
    template_name = 'hr/shift_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Shift scheduled successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:shift-list')


class ShiftUpdateView(LoginRequiredMixin, UpdateView):
    """Update shift schedule."""
    model = ShiftSchedule
    form_class = ShiftScheduleForm
    template_name = 'hr/shift_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Shift updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:shift-list')


class ShiftDeleteView(LoginRequiredMixin, DeleteView):
    """Delete shift schedule."""
    model = ShiftSchedule
    template_name = 'hr/shift_confirm_delete.html'
    success_url = reverse_lazy('hr:shift-list')


# =============================================================================
# TIME ENTRIES
# =============================================================================


class TimeEntryListView(LoginRequiredMixin, ListView):
    """List time entries."""
    model = TimeEntry
    template_name = 'hr/timeentry_list.html'
    context_object_name = 'entries'
    paginate_by = 20

    def get_queryset(self):
        queryset = TimeEntry.objects.select_related('employee__user', 'approved_by').order_by('-entry_date')

        employee_id = self.request.GET.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Time Entries'
        context['statuses'] = TimeEntry.Status.choices
        context['types'] = TimeEntry.EntryType.choices
        return context


class TimeEntryCreateView(LoginRequiredMixin, CreateView):
    """Create time entry."""
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = 'hr/timeentry_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Time entry created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:timeentry-list')


class TimeEntryUpdateView(LoginRequiredMixin, UpdateView):
    """Update time entry."""
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = 'hr/timeentry_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Time entry updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:timeentry-list')


class TimeEntryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete time entry."""
    model = TimeEntry
    template_name = 'hr/timeentry_confirm_delete.html'
    success_url = reverse_lazy('hr:timeentry-list')


class TimeEntryApproveView(LoginRequiredMixin, View):
    """Approve time entry."""

    def post(self, request, pk):
        entry = get_object_or_404(TimeEntry, pk=pk)
        if entry.status == 'SUBMITTED':
            entry.status = 'APPROVED'
            entry.approved_by = request.user
            entry.approved_date = timezone.now().date()
            entry.save()
            messages.success(request, 'Time entry approved.')
        return redirect('hr:timeentry-list')


# =============================================================================
# LEAVE REQUESTS
# =============================================================================


class LeaveListView(LoginRequiredMixin, ListView):
    """List leave requests."""
    model = LeaveRequest
    template_name = 'hr/leave_list.html'
    context_object_name = 'leaves'
    paginate_by = 20

    def get_queryset(self):
        queryset = LeaveRequest.objects.select_related(
            'employee__user', 'approved_by'
        ).order_by('-start_date')

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        leave_type = self.request.GET.get('type')
        if leave_type:
            queryset = queryset.filter(leave_type=leave_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Leave Requests'
        context['statuses'] = LeaveRequest.Status.choices
        context['types'] = LeaveRequest.LeaveType.choices
        return context


class LeaveDetailView(LoginRequiredMixin, DetailView):
    """View leave request details."""
    model = LeaveRequest
    template_name = 'hr/leave_detail.html'
    context_object_name = 'leave'

    def get_queryset(self):
        return LeaveRequest.objects.select_related('employee__user', 'approved_by', 'rejected_by')


class LeaveCreateView(LoginRequiredMixin, CreateView):
    """Create leave request."""
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'hr/leave_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Leave request created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:leave-detail', kwargs={'pk': self.object.pk})


class LeaveUpdateView(LoginRequiredMixin, UpdateView):
    """Update leave request."""
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'hr/leave_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Leave request updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:leave-detail', kwargs={'pk': self.object.pk})


class LeaveDeleteView(LoginRequiredMixin, DeleteView):
    """Delete leave request."""
    model = LeaveRequest
    template_name = 'hr/leave_confirm_delete.html'
    success_url = reverse_lazy('hr:leave-list')


class LeaveApproveView(LoginRequiredMixin, View):
    """Approve leave request."""

    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        if leave.status == 'PENDING':
            leave.approve(request.user)
            messages.success(request, 'Leave request approved.')
        return redirect('hr:leave-detail', pk=pk)


class LeaveRejectView(LoginRequiredMixin, View):
    """Reject leave request."""

    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        if leave.status == 'PENDING':
            reason = request.POST.get('reason', '')
            leave.reject(request.user, reason)
            messages.success(request, 'Leave request rejected.')
        return redirect('hr:leave-detail', pk=pk)


# =============================================================================
# PAYROLL PERIODS
# =============================================================================


class PayrollListView(LoginRequiredMixin, ListView):
    """List payroll periods."""
    model = PayrollPeriod
    template_name = 'hr/payroll_list.html'
    context_object_name = 'periods'
    paginate_by = 20

    def get_queryset(self):
        queryset = PayrollPeriod.objects.select_related(
            'processed_by', 'approved_by'
        ).order_by('-start_date')

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Payroll Periods'
        context['statuses'] = PayrollPeriod.Status.choices
        return context


class PayrollDetailView(LoginRequiredMixin, DetailView):
    """View payroll period details."""
    model = PayrollPeriod
    template_name = 'hr/payroll_detail.html'
    context_object_name = 'period'

    def get_queryset(self):
        return PayrollPeriod.objects.select_related('processed_by', 'approved_by', 'created_by')


class PayrollCreateView(LoginRequiredMixin, CreateView):
    """Create payroll period."""
    model = PayrollPeriod
    form_class = PayrollPeriodForm
    template_name = 'hr/payroll_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Payroll period created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:payroll-detail', kwargs={'pk': self.object.pk})


class PayrollUpdateView(LoginRequiredMixin, UpdateView):
    """Update payroll period."""
    model = PayrollPeriod
    form_class = PayrollPeriodForm
    template_name = 'hr/payroll_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Payroll period updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('hr:payroll-detail', kwargs={'pk': self.object.pk})


# =============================================================================
# LEGACY VIEWS
# =============================================================================


class AttendanceListView(LoginRequiredMixin, ListView):
    """List attendance records."""
    model = Attendance
    template_name = 'hr/attendance_list.html'
    context_object_name = 'records'
    paginate_by = 20

    def get_queryset(self):
        return Attendance.objects.select_related('user').order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Attendance Records'
        context['statuses'] = Attendance.Status.choices
        return context


class AttendanceCreateView(LoginRequiredMixin, CreateView):
    """Create attendance record."""
    model = Attendance
    form_class = AttendanceForm
    template_name = 'hr/attendance_form.html'
    success_url = reverse_lazy('hr:attendance-list')


class LeaveTypeListView(LoginRequiredMixin, ListView):
    """List leave types."""
    model = LeaveType
    template_name = 'hr/leavetype_list.html'
    context_object_name = 'types'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Leave Types'
        return context


class LeaveTypeCreateView(LoginRequiredMixin, CreateView):
    """Create leave type."""
    model = LeaveType
    form_class = LeaveTypeForm
    template_name = 'hr/leavetype_form.html'
    success_url = reverse_lazy('hr:leavetype-list')


class LeaveTypeUpdateView(LoginRequiredMixin, UpdateView):
    """Update leave type."""
    model = LeaveType
    form_class = LeaveTypeForm
    template_name = 'hr/leavetype_form.html'
    success_url = reverse_lazy('hr:leavetype-list')


class OvertimeListView(LoginRequiredMixin, ListView):
    """List overtime requests."""
    model = OvertimeRequest
    template_name = 'hr/overtime_list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        return OvertimeRequest.objects.select_related('user', 'approved_by').order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Overtime Requests'
        context['statuses'] = OvertimeRequest.Status.choices
        return context


class OvertimeCreateView(LoginRequiredMixin, CreateView):
    """Create overtime request."""
    model = OvertimeRequest
    form_class = OvertimeRequestForm
    template_name = 'hr/overtime_form.html'
    success_url = reverse_lazy('hr:overtime-list')


class OvertimeApproveView(LoginRequiredMixin, View):
    """Approve overtime request."""

    def post(self, request, pk):
        overtime = get_object_or_404(OvertimeRequest, pk=pk)
        if overtime.status == 'PENDING':
            overtime.status = 'APPROVED'
            overtime.approved_by = request.user
            overtime.save()
            messages.success(request, 'Overtime request approved.')
        return redirect('hr:overtime-list')
