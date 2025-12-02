"""
ARDT FMS - Permission Mixins
Version: 5.4 - Sprint 1.5

Reusable permission mixins for class-based views.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin that requires the user to have specific role(s).

    Usage:
        class MyView(RoleRequiredMixin, View):
            required_roles = ['MANAGER', 'ADMIN']
    """
    required_roles = []
    role_failure_url = 'dashboard:home'
    role_failure_message = 'You do not have permission to access this page.'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if self.required_roles and not self._check_roles(request.user):
            messages.error(request, self.role_failure_message)
            return redirect(self.role_failure_url)

        return super().dispatch(request, *args, **kwargs)

    def _check_roles(self, user):
        """Check if user has any of the required roles."""
        if user.is_superuser:
            return True

        if hasattr(user, 'has_any_role'):
            return user.has_any_role(*self.required_roles)

        if hasattr(user, 'has_role'):
            return any(user.has_role(role) for role in self.required_roles)

        return False


class AdminRequiredMixin(RoleRequiredMixin):
    """Require admin role."""
    required_roles = ['ADMIN']
    role_failure_message = 'Administrator access required.'


class ManagerRequiredMixin(RoleRequiredMixin):
    """Require manager or admin role."""
    required_roles = ['MANAGER', 'ADMIN']
    role_failure_message = 'Manager access required.'


class PlannerRequiredMixin(RoleRequiredMixin):
    """Require planner, manager, or admin role."""
    required_roles = ['PLANNER', 'MANAGER', 'ADMIN']
    role_failure_message = 'Planner access required.'


class TechnicianRequiredMixin(RoleRequiredMixin):
    """Require technician role (or manager/admin)."""
    required_roles = ['TECHNICIAN', 'MANAGER', 'ADMIN']
    role_failure_message = 'Technician access required.'


class QCRequiredMixin(RoleRequiredMixin):
    """Require QC inspector role (or manager/admin)."""
    required_roles = ['QC', 'MANAGER', 'ADMIN']
    role_failure_message = 'QC Inspector access required.'


class WorkOrderEditMixin(RoleRequiredMixin):
    """Can edit work orders - planners, managers, admins."""
    required_roles = ['PLANNER', 'MANAGER', 'ADMIN']
    role_failure_message = 'You do not have permission to edit work orders.'


class ReportsAccessMixin(RoleRequiredMixin):
    """Can access reports - QC, planners, managers, admins."""
    required_roles = ['QC', 'PLANNER', 'MANAGER', 'ADMIN']
    role_failure_message = 'You do not have permission to view reports.'


class AjaxResponseMixin:
    """
    Mixin for AJAX/HTMX responses.
    Returns JSON or partial HTML based on request type.
    """

    def is_ajax_request(self):
        """Check if request is AJAX or HTMX."""
        request = getattr(self, 'request', None)
        if not request:
            return False
        return (
            request.headers.get('HX-Request') == 'true' or
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        )
