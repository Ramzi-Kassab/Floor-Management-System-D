"""
ARDT FMS - Permission Decorators
Version: 5.4

Function-based view decorators for permission checking.
"""

from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def login_required_with_message(function=None, login_url=None, message=None):
    """
    Decorator that requires login with optional custom message.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if message:
                    from django.contrib import messages
                    messages.warning(request, message)
                return redirect(login_url or 'accounts:login')
            return view_func(request, *args, **kwargs)
        return _wrapped_view

    if function:
        return decorator(function)
    return decorator


def role_required(roles, require_all=False):
    """
    Decorator that requires user to have specific role(s).

    Usage:
        @role_required('ADMIN')
        def my_view(request):
            ...

        @role_required(['ADMIN', 'MANAGER'])
        def my_view(request):
            ...

        @role_required(['ADMIN', 'MANAGER'], require_all=True)
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            # Superuser bypasses role check
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Normalize to list
            role_list = roles if isinstance(roles, (list, tuple)) else [roles]

            if require_all:
                has_permission = request.user.has_all_roles(role_list)
            else:
                has_permission = request.user.has_any_role(role_list)

            if not has_permission:
                raise PermissionDenied("You don't have the required role to access this page.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def permission_required(permissions, require_all=True):
    """
    Decorator that requires user to have specific permission(s).

    Usage:
        @permission_required('workorders.create')
        def my_view(request):
            ...

        @permission_required(['workorders.create', 'workorders.edit'])
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            # Superuser bypasses permission check
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Normalize to list
            perm_list = permissions if isinstance(permissions, (list, tuple)) else [permissions]

            if require_all:
                has_permission = all(request.user.has_permission(p) for p in perm_list)
            else:
                has_permission = any(request.user.has_permission(p) for p in perm_list)

            if not has_permission:
                raise PermissionDenied("You don't have the required permission to access this page.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def department_required(departments):
    """
    Decorator that requires user to be in specific department(s).

    Usage:
        @department_required('MFG')
        def my_view(request):
            ...

        @department_required(['MFG', 'QC'])
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            # Superuser bypasses check
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Normalize to list
            dept_list = departments if isinstance(departments, (list, tuple)) else [departments]

            user_dept = getattr(request.user.department, 'code', None)

            if user_dept not in dept_list:
                raise PermissionDenied("Your department doesn't have access to this page.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def staff_required(view_func):
    """
    Decorator that requires user to be staff.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        if not request.user.is_staff:
            raise PermissionDenied("Staff access required.")

        return view_func(request, *args, **kwargs)
    return _wrapped_view


def superuser_required(view_func):
    """
    Decorator that requires user to be superuser.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        if not request.user.is_superuser:
            raise PermissionDenied("Superuser access required.")

        return view_func(request, *args, **kwargs)
    return _wrapped_view
