"""
APPEND this entire file content to apps/accounts/views.py
=========================================================
Adds full CRUD for: Users, Roles, Permissions, User-Role assignment.
No Django admin dependency for any of these operations.
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)

from .models import Role, Permission, RolePermission, UserRole

User = get_user_model()


# =============================================================================
# USER MANAGEMENT
# =============================================================================

class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_paginate_by(self, queryset):
        per_page = self.request.GET.get('per_page', '25')
        if per_page == 'all':
            return None  # No pagination — show all
        try:
            return int(per_page)
        except (ValueError, TypeError):
            return 25

    def get_queryset(self):
        qs = User.objects.select_related(
            'department', 'position'
        ).prefetch_related('roles').order_by('username')

        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email__icontains=q) |
                Q(employee_id__icontains=q)
            )
        dept = self.request.GET.get('department')
        if dept:
            qs = qs.filter(department_id=dept)

        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)

        role = self.request.GET.get('role')
        if role:
            qs = qs.filter(roles__code=role)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'User Management'
        context['search_query'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_department'] = self.request.GET.get('department', '')
        context['current_role'] = self.request.GET.get('role', '')
        from apps.organization.models import Department
        context['departments'] = Department.objects.filter(is_active=True).order_by('name')
        context['roles'] = Role.objects.filter(is_active=True).order_by('name')
        context['total_count'] = self.get_queryset().count()
        context['per_page'] = self.request.GET.get('per_page', '25')
        return context


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_obj'

    def get_queryset(self):
        return User.objects.select_related(
            'department', 'position'
        ).prefetch_related(
            Prefetch('user_roles', queryset=UserRole.objects.select_related('role'))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'User: {self.object.display_name}'
        context['user_roles'] = self.object.user_roles.select_related('role', 'assigned_by')
        context['available_roles'] = Role.objects.filter(
            is_active=True
        ).exclude(id__in=self.object.roles.values('id'))
        # Competency summary if employee profile exists
        try:
            from apps.hr.models import ProcessCompetencyMatrix
            context['competency_summary'] = ProcessCompetencyMatrix.objects.filter(
                employee=self.object.employee_profile
            ).select_related('master_process').order_by('master_process__category')
        except Exception:
            context['competency_summary'] = []
        return context


class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    template_name = 'accounts/user_form.html'
    fields = [
        'username', 'first_name', 'last_name', 'email',
        'employee_id', 'department', 'position',
        'phone', 'mobile', 'language', 'is_active', 'is_staff',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create User'
        context['is_new'] = True
        context['roles'] = Role.objects.filter(is_active=True).order_by('level', 'name')
        return context

    def form_valid(self, form):
        # Set a temporary password — user will be asked to change
        response = super().form_valid(form)
        self.object.set_password('ChangeMe@123')
        self.object.save()
        # Assign selected roles
        for role_id in self.request.POST.getlist('roles'):
            try:
                role = Role.objects.get(pk=role_id)
                UserRole.objects.get_or_create(
                    user=self.object, role=role,
                    defaults={'assigned_by': self.request.user}
                )
            except Role.DoesNotExist:
                pass
        messages.success(
            self.request,
            f"User '{self.object.username}' created. Default password: ChangeMe@123"
        )
        return response

    def get_success_url(self):
        return reverse_lazy('accounts:user-detail', kwargs={'pk': self.object.pk})


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'accounts/user_form.html'
    fields = [
        'first_name', 'last_name', 'email',
        'employee_id', 'department', 'position',
        'phone', 'mobile', 'language', 'is_active', 'is_staff',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit User: {self.object.display_name}'
        context['is_new'] = False
        context['roles'] = Role.objects.filter(is_active=True).order_by('level', 'name')
        context['assigned_role_ids'] = list(
            self.object.roles.values_list('id', flat=True)
        )
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        # Sync roles from POST
        selected_ids = set(
            int(x) for x in self.request.POST.getlist('roles') if x
        )
        current_ids = set(self.object.roles.values_list('id', flat=True))
        # Add new
        for rid in selected_ids - current_ids:
            try:
                UserRole.objects.get_or_create(
                    user=self.object,
                    role_id=rid,
                    defaults={'assigned_by': self.request.user}
                )
            except Exception:
                pass
        # Remove deselected
        UserRole.objects.filter(
            user=self.object,
            role_id__in=current_ids - selected_ids
        ).delete()
        messages.success(self.request, f"User '{self.object.username}' updated.")
        return response

    def get_success_url(self):
        return reverse_lazy('accounts:user-detail', kwargs={'pk': self.object.pk})


class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user-list')
    context_object_name = 'user_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Delete User: {self.object.display_name}'
        return context

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect('accounts:user-detail', pk=user.pk)
        messages.success(request, f"User '{user.username}' deleted.")
        return super().delete(request, *args, **kwargs)


class UserRoleManageView(LoginRequiredMixin, View):
    """AJAX: Add or remove a role from a user."""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        action = request.POST.get('action')
        role_id = request.POST.get('role_id')
        role = get_object_or_404(Role, pk=role_id)

        if action == 'add':
            ur, created = UserRole.objects.get_or_create(
                user=user, role=role,
                defaults={'assigned_by': request.user, 'is_primary': False}
            )
            messages.success(request, f"Role '{role.name}' assigned to {user.display_name}.")
        elif action == 'remove':
            UserRole.objects.filter(user=user, role=role).delete()
            messages.success(request, f"Role '{role.name}' removed from {user.display_name}.")

        return redirect('accounts:user-detail', pk=pk)


class UserResetPasswordView(LoginRequiredMixin, View):
    """Reset a user's password to default and force change on next login."""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.set_password('ChangeMe@123')
        user.save()
        messages.success(
            request,
            f"Password for '{user.username}' reset to: ChangeMe@123 — user must change on next login."
        )
        return redirect('accounts:user-detail', pk=pk)


# =============================================================================
# ROLE MANAGEMENT
# =============================================================================

class RoleListView(LoginRequiredMixin, ListView):
    model = Role
    template_name = 'accounts/role_list.html'
    context_object_name = 'roles'

    def get_queryset(self):
        return Role.objects.annotate(
            user_count=Count('users', distinct=True),
            permission_count=Count('permissions', distinct=True),
        ).order_by('-level', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Roles & Permissions'
        context['total_roles'] = Role.objects.count()
        context['total_permissions'] = Permission.objects.count()
        return context


class RoleDetailView(LoginRequiredMixin, DetailView):
    model = Role
    template_name = 'accounts/role_detail.html'
    context_object_name = 'role'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Role: {self.object.name}'
        # Group permissions by module
        perms = self.object.permissions.order_by('module', 'code')
        grouped = {}
        for p in perms:
            grouped.setdefault(p.module, []).append(p)
        context['permissions_grouped'] = grouped
        # All permissions for assignment
        all_perms = Permission.objects.order_by('module', 'code')
        all_grouped = {}
        assigned_ids = set(self.object.permissions.values_list('id', flat=True))
        for p in all_perms:
            all_grouped.setdefault(p.module, []).append({
                'perm': p,
                'assigned': p.id in assigned_ids
            })
        context['all_permissions_grouped'] = all_grouped
        context['users_with_role'] = self.object.users.select_related(
            'department', 'position'
        ).order_by('username')
        return context


class RoleCreateView(LoginRequiredMixin, CreateView):
    model = Role
    template_name = 'accounts/role_form.html'
    fields = ['code', 'name', 'description', 'level', 'is_active']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Role'
        context['is_new'] = True
        # All permissions grouped by module for checkbox assignment
        all_perms = Permission.objects.order_by('module', 'code')
        grouped = {}
        for p in all_perms:
            grouped.setdefault(p.module, []).append(p)
        context['permissions_grouped'] = grouped
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        for perm_id in self.request.POST.getlist('permissions'):
            try:
                RolePermission.objects.get_or_create(
                    role=self.object,
                    permission_id=perm_id,
                    defaults={'granted_by': self.request.user}
                )
            except Exception:
                pass
        messages.success(self.request, f"Role '{self.object.name}' created.")
        return response

    def get_success_url(self):
        return reverse_lazy('accounts:role-detail', kwargs={'pk': self.object.pk})


class RoleUpdateView(LoginRequiredMixin, UpdateView):
    model = Role
    template_name = 'accounts/role_form.html'
    fields = ['code', 'name', 'description', 'level', 'is_active']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Role: {self.object.name}'
        context['is_new'] = False
        assigned_ids = set(self.object.permissions.values_list('id', flat=True))
        all_perms = Permission.objects.order_by('module', 'code')
        grouped = {}
        for p in all_perms:
            grouped.setdefault(p.module, []).append({
                'perm': p,
                'assigned': p.id in assigned_ids
            })
        context['permissions_grouped'] = grouped
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        # Sync permissions
        selected_ids = set(
            int(x) for x in self.request.POST.getlist('permissions') if x
        )
        current_ids = set(self.object.permissions.values_list('id', flat=True))
        for pid in selected_ids - current_ids:
            RolePermission.objects.get_or_create(
                role=self.object, permission_id=pid,
                defaults={'granted_by': self.request.user}
            )
        RolePermission.objects.filter(
            role=self.object,
            permission_id__in=current_ids - selected_ids
        ).delete()
        messages.success(self.request, f"Role '{self.object.name}' updated.")
        return response

    def get_success_url(self):
        return reverse_lazy('accounts:role-detail', kwargs={'pk': self.object.pk})


class RoleDeleteView(LoginRequiredMixin, DeleteView):
    model = Role
    template_name = 'accounts/role_confirm_delete.html'
    success_url = reverse_lazy('accounts:role-list')
    context_object_name = 'role'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Delete Role: {self.object.name}'
        context['user_count'] = self.object.users.count()
        return context

    def delete(self, request, *args, **kwargs):
        role = self.get_object()
        if role.is_system:
            messages.error(request, f"'{role.name}' is a system role and cannot be deleted.")
            return redirect('accounts:role-detail', pk=role.pk)
        messages.success(request, f"Role '{role.name}' deleted.")
        return super().delete(request, *args, **kwargs)


# =============================================================================
# PERMISSION MANAGEMENT
# =============================================================================

class PermissionListView(LoginRequiredMixin, ListView):
    model = Permission
    template_name = 'accounts/permission_list.html'
    context_object_name = 'permissions'
    paginate_by = 100

    def get_queryset(self):
        qs = Permission.objects.annotate(
            role_count=Count('roles', distinct=True)
        ).order_by('module', 'code')

        module = self.request.GET.get('module')
        if module:
            qs = qs.filter(module=module)

        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Permissions'
        context['modules'] = Permission.objects.values_list(
            'module', flat=True
        ).distinct().order_by('module')
        context['current_module'] = self.request.GET.get('module', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class PermissionCreateView(LoginRequiredMixin, CreateView):
    model = Permission
    template_name = 'accounts/permission_form.html'
    fields = ['code', 'name', 'description', 'module']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Permission'
        context['modules'] = Permission.objects.values_list(
            'module', flat=True
        ).distinct().order_by('module')
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Permission '{form.instance.code}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('accounts:permission-list')


class PermissionUpdateView(LoginRequiredMixin, UpdateView):
    model = Permission
    template_name = 'accounts/permission_form.html'
    fields = ['code', 'name', 'description', 'module']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Permission: {self.object.code}'
        context['modules'] = Permission.objects.values_list(
            'module', flat=True
        ).distinct().order_by('module')
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Permission '{form.instance.code}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('accounts:permission-list')


class PermissionDeleteView(LoginRequiredMixin, DeleteView):
    model = Permission
    template_name = 'accounts/permission_confirm_delete.html'
    success_url = reverse_lazy('accounts:permission-list')
    context_object_name = 'permission'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Delete Permission: {self.object.code}'
        context['role_count'] = self.object.roles.count()
        return context

    def delete(self, request, *args, **kwargs):
        perm = self.get_object()
        messages.success(request, f"Permission '{perm.code}' deleted.")
        return super().delete(request, *args, **kwargs)
