"""
ARDT FMS - Permission Mixins
Version: 5.4

Reusable mixins for view-level permission checking.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires user to have specific role(s).
    
    Usage:
        class MyView(RoleRequiredMixin, View):
            required_roles = ['ADMIN', 'MANAGER']
            # or
            required_roles = 'ADMIN'  # single role
    """
    
    required_roles = []
    require_all_roles = False  # If True, user must have ALL roles
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        
        # Superuser bypasses role check
        if self.request.user.is_superuser:
            return True
        
        # Normalize to list
        roles = self.required_roles
        if isinstance(roles, str):
            roles = [roles]
        
        if not roles:
            return True
        
        if self.require_all_roles:
            return self.request.user.has_all_roles(roles)
        return self.request.user.has_any_role(roles)
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You don't have permission to access this page.")
        return redirect('accounts:login')


class PermissionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires user to have specific permission(s).
    
    Usage:
        class MyView(PermissionRequiredMixin, View):
            required_permissions = ['workorders.create', 'workorders.edit']
    """
    
    required_permissions = []
    require_all_permissions = True  # If True, user must have ALL permissions
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        
        # Superuser bypasses permission check
        if self.request.user.is_superuser:
            return True
        
        # Normalize to list
        perms = self.required_permissions
        if isinstance(perms, str):
            perms = [perms]
        
        if not perms:
            return True
        
        if self.require_all_permissions:
            return all(
                self.request.user.has_permission(p) for p in perms
            )
        return any(
            self.request.user.has_permission(p) for p in perms
        )
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You don't have permission to access this page.")
        return redirect('accounts:login')


class OwnerOrRoleMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that allows access if user is owner OR has specific role.
    
    Useful for views where users can access their own records,
    but managers can access all records.
    
    Usage:
        class MyDetailView(OwnerOrRoleMixin, DetailView):
            owner_field = 'created_by'  # or 'assigned_to', etc.
            owner_roles = ['ADMIN', 'MANAGER']
    """
    
    owner_field = 'created_by'
    owner_roles = ['ADMIN', 'MANAGER']
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        
        # Superuser bypasses check
        if self.request.user.is_superuser:
            return True
        
        # Check if user has override role
        if self.request.user.has_any_role(self.owner_roles):
            return True
        
        # Check if user is owner
        obj = self.get_object()
        owner = getattr(obj, self.owner_field, None)
        
        if owner is None:
            return False
        
        # Handle both User object and user ID
        if hasattr(owner, 'pk'):
            return owner.pk == self.request.user.pk
        return owner == self.request.user.pk
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You don't have permission to access this resource.")
        return redirect('accounts:login')


class DepartmentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires user to be in specific department(s).
    
    Usage:
        class MyView(DepartmentRequiredMixin, View):
            required_departments = ['MFG', 'QC']
    """
    
    required_departments = []
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        
        # Superuser bypasses check
        if self.request.user.is_superuser:
            return True
        
        if not self.required_departments:
            return True
        
        user_dept = getattr(self.request.user.department, 'code', None)
        return user_dept in self.required_departments
