"""
ARDT FMS - Organization Views
Version: 5.4

Organization management views.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import Department, Position, Theme, SystemSetting, NumberSequence
from .forms import DepartmentForm, PositionForm, ThemeForm, SystemSettingForm, NumberSequenceForm


# =============================================================================
# DEPARTMENT VIEWS
# =============================================================================


class DepartmentListView(LoginRequiredMixin, ListView):
    """List all departments with filtering."""

    model = Department
    template_name = "organization/department_list.html"
    context_object_name = "departments"
    paginate_by = 25

    def get_queryset(self):
        queryset = Department.objects.select_related('parent', 'manager').annotate(
            position_count=Count('positions'),
            child_count=Count('children')
        ).order_by('code')

        # Filter by active status
        status = self.request.GET.get("status")
        if status == "active":
            queryset = queryset.filter(is_active=True)
        elif status == "inactive":
            queryset = queryset.filter(is_active=False)

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(location__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Departments"
        context["current_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class DepartmentDetailView(LoginRequiredMixin, DetailView):
    """View department details."""

    model = Department
    template_name = "organization/department_detail.html"
    context_object_name = "department"

    def get_queryset(self):
        return Department.objects.select_related('parent', 'manager').prefetch_related('positions', 'children')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Department: {self.object.name}"
        return context


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    """Create a new department."""

    model = Department
    form_class = DepartmentForm
    template_name = "organization/department_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Department"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Department '{form.instance.name}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("organization:department-detail", kwargs={"pk": self.object.pk})


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing department."""

    model = Department
    form_class = DepartmentForm
    template_name = "organization/department_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit: {self.object.name}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Department '{form.instance.name}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("organization:department-detail", kwargs={"pk": self.object.pk})


class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a department."""

    model = Department
    template_name = "organization/department_confirm_delete.html"
    success_url = reverse_lazy("organization:department-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete: {self.object.name}"
        return context

    def delete(self, request, *args, **kwargs):
        department = self.get_object()
        messages.success(request, f"Department '{department.name}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


# =============================================================================
# POSITION VIEWS
# =============================================================================


class PositionListView(LoginRequiredMixin, ListView):
    """List all positions with filtering."""

    model = Position
    template_name = "organization/position_list.html"
    context_object_name = "positions"
    paginate_by = 25

    def get_queryset(self):
        queryset = Position.objects.select_related('department').order_by('department__code', 'level', 'title')

        # Filter by department
        dept = self.request.GET.get("department")
        if dept:
            queryset = queryset.filter(department_id=dept)

        # Filter by active status
        status = self.request.GET.get("status")
        if status == "active":
            queryset = queryset.filter(is_active=True)
        elif status == "inactive":
            queryset = queryset.filter(is_active=False)

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Positions"
        context["departments"] = Department.objects.filter(is_active=True)
        context["current_department"] = self.request.GET.get("department", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class PositionDetailView(LoginRequiredMixin, DetailView):
    """View position details."""

    model = Position
    template_name = "organization/position_detail.html"
    context_object_name = "position"

    def get_queryset(self):
        return Position.objects.select_related('department')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Position: {self.object.title}"
        return context


class PositionCreateView(LoginRequiredMixin, CreateView):
    """Create a new position."""

    model = Position
    form_class = PositionForm
    template_name = "organization/position_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Position"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Position '{form.instance.title}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("organization:position-detail", kwargs={"pk": self.object.pk})


class PositionUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing position."""

    model = Position
    form_class = PositionForm
    template_name = "organization/position_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit: {self.object.title}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Position '{form.instance.title}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("organization:position-detail", kwargs={"pk": self.object.pk})


class PositionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a position."""

    model = Position
    template_name = "organization/position_confirm_delete.html"
    success_url = reverse_lazy("organization:position-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete: {self.object.title}"
        return context


# =============================================================================
# THEME VIEWS
# =============================================================================


class ThemeListView(LoginRequiredMixin, ListView):
    """List all themes."""

    model = Theme
    template_name = "organization/theme_list.html"
    context_object_name = "themes"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Themes"
        return context


class ThemeDetailView(LoginRequiredMixin, DetailView):
    """View theme details."""

    model = Theme
    template_name = "organization/theme_detail.html"
    context_object_name = "theme"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Theme: {self.object.name}"
        return context


class ThemeCreateView(LoginRequiredMixin, CreateView):
    """Create a new theme."""

    model = Theme
    form_class = ThemeForm
    template_name = "organization/theme_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Theme"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Theme '{form.instance.name}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("organization:theme-list")


class ThemeUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing theme."""

    model = Theme
    form_class = ThemeForm
    template_name = "organization/theme_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit: {self.object.name}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Theme '{form.instance.name}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("organization:theme-list")


class ThemeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a theme."""

    model = Theme
    template_name = "organization/theme_confirm_delete.html"
    success_url = reverse_lazy("organization:theme-list")


class ThemeSetDefaultView(LoginRequiredMixin, View):
    """Set a theme as the default."""

    def post(self, request, pk):
        theme = get_object_or_404(Theme, pk=pk)
        # Clear existing default
        Theme.objects.filter(is_default=True).update(is_default=False)
        # Set new default
        theme.is_default = True
        theme.save(update_fields=['is_default'])
        messages.success(request, f"'{theme.name}' is now the default theme.")
        return redirect('organization:theme-detail', pk=pk)


# =============================================================================
# SYSTEM SETTINGS VIEWS
# =============================================================================


class SystemSettingListView(LoginRequiredMixin, ListView):
    """List all system settings."""

    model = SystemSetting
    template_name = "organization/setting_list.html"
    context_object_name = "settings"

    def get_queryset(self):
        queryset = SystemSetting.objects.order_by('category', 'key')

        # Filter by category
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "System Settings"
        context["categories"] = SystemSetting.objects.values_list('category', flat=True).distinct()
        context["current_category"] = self.request.GET.get("category", "")
        return context


class SystemSettingUpdateView(LoginRequiredMixin, UpdateView):
    """Update a system setting."""

    model = SystemSetting
    form_class = SystemSettingForm
    template_name = "organization/setting_form.html"
    success_url = reverse_lazy("organization:setting-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Setting: {self.object.key}"
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f"Setting '{form.instance.key}' updated successfully.")
        return super().form_valid(form)


class SystemSettingCreateView(LoginRequiredMixin, CreateView):
    """Create a new system setting."""

    model = SystemSetting
    form_class = SystemSettingForm
    template_name = "organization/setting_form.html"
    success_url = reverse_lazy("organization:setting-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Setting"
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f"Setting '{form.instance.key}' created successfully.")
        return super().form_valid(form)


# =============================================================================
# NUMBER SEQUENCE VIEWS
# =============================================================================


class NumberSequenceListView(LoginRequiredMixin, ListView):
    """List all number sequences."""

    model = NumberSequence
    template_name = "organization/sequence_list.html"
    context_object_name = "sequences"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Number Sequences"
        return context


class NumberSequenceCreateView(LoginRequiredMixin, CreateView):
    """Create a new number sequence."""

    model = NumberSequence
    form_class = NumberSequenceForm
    template_name = "organization/sequence_form.html"
    success_url = reverse_lazy("organization:sequence-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Number Sequence"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Number sequence '{form.instance.code}' created successfully.")
        return super().form_valid(form)


class NumberSequenceUpdateView(LoginRequiredMixin, UpdateView):
    """Update a number sequence."""

    model = NumberSequence
    form_class = NumberSequenceForm
    template_name = "organization/sequence_form.html"
    success_url = reverse_lazy("organization:sequence-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit: {self.object.code}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Number sequence '{form.instance.code}' updated successfully.")
        return super().form_valid(form)


class NumberSequenceDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a number sequence."""

    model = NumberSequence
    template_name = "organization/sequence_confirm_delete.html"
    success_url = reverse_lazy("organization:sequence-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete: {self.object.code}"
        return context
