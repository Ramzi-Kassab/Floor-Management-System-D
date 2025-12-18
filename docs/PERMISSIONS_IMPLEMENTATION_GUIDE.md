# 🔐 ROLE-BASED PERMISSIONS IMPLEMENTATION GUIDE
## ARDT FMS - Complete Step-by-Step Implementation

**Priority:** HIGH - Security Critical  
**Effort:** 1-2 days  
**Impact:** Controls who can access what in the system  

---

## 📋 OVERVIEW

### **Current Problem:**

All logged-in users can access everything:
- Technicians can approve work orders
- Viewers can delete data
- Anyone can access financial reports
- **This is a security risk!**

### **Solution:**

Implement Role-Based Access Control (RBAC):
- Define user roles (Admin, Manager, Technician, Viewer)
- Assign permissions to each role
- Check permissions in views and templates
- **Secure the system!**

---

## 🎯 IMPLEMENTATION PLAN

### **Phase 1:** Create Role Model (30 min)
### **Phase 2:** Add Permissions (1 hour)
### **Phase 3:** Update User Model (30 min)
### **Phase 4:** Create Decorators (1 hour)
### **Phase 5:** Apply to Views (3-4 hours)
### **Phase 6:** Update Templates (2-3 hours)
### **Phase 7:** Testing (2 hours)

**Total:** 10-12 hours across 1-2 days

---

## 📁 PHASE 1: CREATE ROLE MODEL

### **File:** `apps/accounts/models.py`

**Add this to your existing file:**

```python
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class Role(models.Model):
    """
    User roles for role-based access control (RBAC).
    
    Defines what users with this role can do in the system.
    """
    
    # Role Types
    ADMIN = 'ADMIN'
    MANAGER = 'MANAGER'
    TECHNICIAN = 'TECHNICIAN'
    VIEWER = 'VIEWER'
    
    ROLE_CHOICES = [
        (ADMIN, 'Administrator'),
        (MANAGER, 'Manager'),
        (TECHNICIAN, 'Technician'),
        (VIEWER, 'Viewer'),
    ]
    
    name = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        unique=True,
        help_text="Role name"
    )
    
    display_name = models.CharField(
        max_length=50,
        help_text="Human-readable role name"
    )
    
    description = models.TextField(
        blank=True,
        help_text="What this role can do"
    )
    
    # Permissions - stored as JSON for flexibility
    permissions = models.JSONField(
        default=dict,
        help_text="Permissions for this role"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this role is currently active"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_role'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']
    
    def __str__(self):
        return self.display_name
    
    def has_permission(self, permission):
        """Check if this role has a specific permission."""
        return self.permissions.get(permission, False)
    
    def get_permissions_list(self):
        """Get list of permissions this role has."""
        return [perm for perm, has_it in self.permissions.items() if has_it]


# Update your existing User model to include role
class User(AbstractUser):
    """Extended user model with role-based permissions."""
    
    # Add role field
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name='users',
        null=True,  # Temporarily nullable for migration
        blank=True,
        help_text="User's role in the system"
    )
    
    # ... keep all your existing fields ...
    
    def has_role(self, role_name):
        """Check if user has a specific role."""
        return self.role and self.role.name == role_name
    
    def has_any_role(self, *role_names):
        """Check if user has any of the specified roles."""
        return self.role and self.role.name in role_names
    
    def has_permission(self, permission):
        """Check if user's role has a specific permission."""
        if self.is_superuser:
            return True
        return self.role and self.role.has_permission(permission)
    
    @property
    def role_display(self):
        """Get user's role display name."""
        return self.role.display_name if self.role else 'No Role'
```

---

## 📁 PHASE 2: DEFINE PERMISSIONS

### **File:** `apps/accounts/permissions.py` (NEW FILE)

```python
"""
Permission definitions for ARDT FMS.

This file defines all permissions used in the system.
"""

# Work Orders Permissions
WORKORDER_VIEW = 'workorder_view'
WORKORDER_CREATE = 'workorder_create'
WORKORDER_EDIT = 'workorder_edit'
WORKORDER_DELETE = 'workorder_delete'
WORKORDER_APPROVE = 'workorder_approve'
WORKORDER_ASSIGN = 'workorder_assign'

# Service Requests Permissions
SERVICE_REQUEST_VIEW = 'service_request_view'
SERVICE_REQUEST_CREATE = 'service_request_create'
SERVICE_REQUEST_EDIT = 'service_request_edit'
SERVICE_REQUEST_DELETE = 'service_request_delete'
SERVICE_REQUEST_APPROVE = 'service_request_approve'

# Inventory Permissions
INVENTORY_VIEW = 'inventory_view'
INVENTORY_EDIT = 'inventory_edit'
INVENTORY_ADJUST = 'inventory_adjust'
INVENTORY_APPROVE_PURCHASE = 'inventory_approve_purchase'

# Quality Permissions
QUALITY_VIEW = 'quality_view'
QUALITY_CREATE = 'quality_create'
QUALITY_APPROVE = 'quality_approve'

# User Management Permissions
USER_VIEW = 'user_view'
USER_CREATE = 'user_create'
USER_EDIT = 'user_edit'
USER_DELETE = 'user_delete'

# Reports Permissions
REPORTS_VIEW = 'reports_view'
REPORTS_FINANCIAL = 'reports_financial'
REPORTS_EXPORT = 'reports_export'

# Settings Permissions
SETTINGS_VIEW = 'settings_view'
SETTINGS_EDIT = 'settings_edit'


# Role Definitions
ROLE_PERMISSIONS = {
    'ADMIN': {
        # Administrators can do everything
        WORKORDER_VIEW: True,
        WORKORDER_CREATE: True,
        WORKORDER_EDIT: True,
        WORKORDER_DELETE: True,
        WORKORDER_APPROVE: True,
        WORKORDER_ASSIGN: True,
        
        SERVICE_REQUEST_VIEW: True,
        SERVICE_REQUEST_CREATE: True,
        SERVICE_REQUEST_EDIT: True,
        SERVICE_REQUEST_DELETE: True,
        SERVICE_REQUEST_APPROVE: True,
        
        INVENTORY_VIEW: True,
        INVENTORY_EDIT: True,
        INVENTORY_ADJUST: True,
        INVENTORY_APPROVE_PURCHASE: True,
        
        QUALITY_VIEW: True,
        QUALITY_CREATE: True,
        QUALITY_APPROVE: True,
        
        USER_VIEW: True,
        USER_CREATE: True,
        USER_EDIT: True,
        USER_DELETE: True,
        
        REPORTS_VIEW: True,
        REPORTS_FINANCIAL: True,
        REPORTS_EXPORT: True,
        
        SETTINGS_VIEW: True,
        SETTINGS_EDIT: True,
    },
    
    'MANAGER': {
        # Managers can view, create, edit, and approve
        WORKORDER_VIEW: True,
        WORKORDER_CREATE: True,
        WORKORDER_EDIT: True,
        WORKORDER_DELETE: False,  # Cannot delete
        WORKORDER_APPROVE: True,
        WORKORDER_ASSIGN: True,
        
        SERVICE_REQUEST_VIEW: True,
        SERVICE_REQUEST_CREATE: True,
        SERVICE_REQUEST_EDIT: True,
        SERVICE_REQUEST_DELETE: False,
        SERVICE_REQUEST_APPROVE: True,
        
        INVENTORY_VIEW: True,
        INVENTORY_EDIT: True,
        INVENTORY_ADJUST: True,
        INVENTORY_APPROVE_PURCHASE: True,
        
        QUALITY_VIEW: True,
        QUALITY_CREATE: True,
        QUALITY_APPROVE: True,
        
        USER_VIEW: True,
        USER_CREATE: False,  # Cannot create users
        USER_EDIT: False,
        USER_DELETE: False,
        
        REPORTS_VIEW: True,
        REPORTS_FINANCIAL: True,
        REPORTS_EXPORT: True,
        
        SETTINGS_VIEW: True,
        SETTINGS_EDIT: False,  # Cannot edit settings
    },
    
    'TECHNICIAN': {
        # Technicians can view and edit their assigned work
        WORKORDER_VIEW: True,
        WORKORDER_CREATE: False,  # Cannot create
        WORKORDER_EDIT: True,  # Can edit assigned work
        WORKORDER_DELETE: False,
        WORKORDER_APPROVE: False,
        WORKORDER_ASSIGN: False,
        
        SERVICE_REQUEST_VIEW: True,
        SERVICE_REQUEST_CREATE: False,
        SERVICE_REQUEST_EDIT: True,
        SERVICE_REQUEST_DELETE: False,
        SERVICE_REQUEST_APPROVE: False,
        
        INVENTORY_VIEW: True,
        INVENTORY_EDIT: False,
        INVENTORY_ADJUST: False,
        INVENTORY_APPROVE_PURCHASE: False,
        
        QUALITY_VIEW: True,
        QUALITY_CREATE: True,  # Can create quality records
        QUALITY_APPROVE: False,
        
        USER_VIEW: False,
        USER_CREATE: False,
        USER_EDIT: False,
        USER_DELETE: False,
        
        REPORTS_VIEW: True,
        REPORTS_FINANCIAL: False,  # Cannot see financial reports
        REPORTS_EXPORT: False,
        
        SETTINGS_VIEW: False,
        SETTINGS_EDIT: False,
    },
    
    'VIEWER': {
        # Viewers can only view, nothing else
        WORKORDER_VIEW: True,
        WORKORDER_CREATE: False,
        WORKORDER_EDIT: False,
        WORKORDER_DELETE: False,
        WORKORDER_APPROVE: False,
        WORKORDER_ASSIGN: False,
        
        SERVICE_REQUEST_VIEW: True,
        SERVICE_REQUEST_CREATE: False,
        SERVICE_REQUEST_EDIT: False,
        SERVICE_REQUEST_DELETE: False,
        SERVICE_REQUEST_APPROVE: False,
        
        INVENTORY_VIEW: True,
        INVENTORY_EDIT: False,
        INVENTORY_ADJUST: False,
        INVENTORY_APPROVE_PURCHASE: False,
        
        QUALITY_VIEW: True,
        QUALITY_CREATE: False,
        QUALITY_APPROVE: False,
        
        USER_VIEW: False,
        USER_CREATE: False,
        USER_EDIT: False,
        USER_DELETE: False,
        
        REPORTS_VIEW: True,
        REPORTS_FINANCIAL: False,
        REPORTS_EXPORT: False,
        
        SETTINGS_VIEW: False,
        SETTINGS_EDIT: False,
    },
}
```

---

## 📁 PHASE 3: MIGRATION

### **Create Migration:**

```bash
python manage.py makemigrations accounts
python manage.py migrate accounts
```

### **Create Default Roles:**

**File:** `apps/accounts/management/commands/create_default_roles.py` (NEW FILE)

```python
from django.core.management.base import BaseCommand
from apps.accounts.models import Role
from apps.accounts.permissions import ROLE_PERMISSIONS


class Command(BaseCommand):
    help = 'Create default roles with permissions'
    
    def handle(self, *args, **kwargs):
        for role_name, permissions in ROLE_PERMISSIONS.items():
            role, created = Role.objects.update_or_create(
                name=role_name,
                defaults={
                    'display_name': role_name.capitalize(),
                    'description': f'{role_name.capitalize()} role',
                    'permissions': permissions,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created role: {role_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Updated role: {role_name}')
                )
```

**Run it:**

```bash
python manage.py create_default_roles
```

---

## 📁 PHASE 4: CREATE DECORATORS

### **File:** `apps/accounts/decorators.py` (NEW FILE)

```python
"""
Permission decorators for views.
"""

from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def require_permission(permission):
    """
    Decorator to check if user has a specific permission.
    
    Usage:
        @require_permission('workorder_approve')
        def approve_workorder(request, pk):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.has_permission(permission):
                return view_func(request, *args, **kwargs)
            
            messages.error(
                request,
                'You do not have permission to perform this action.'
            )
            return HttpResponseForbidden(
                'Permission denied. You do not have the required role.'
            )
        return wrapper
    return decorator


def require_role(role_name):
    """
    Decorator to check if user has a specific role.
    
    Usage:
        @require_role('MANAGER')
        def manager_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.has_role(role_name):
                return view_func(request, *args, **kwargs)
            
            messages.error(
                request,
                f'You must be a {role_name} to access this page.'
            )
            return redirect('dashboard:home')
        return wrapper
    return decorator


def require_any_role(*role_names):
    """
    Decorator to check if user has any of the specified roles.
    
    Usage:
        @require_any_role('ADMIN', 'MANAGER')
        def admin_or_manager_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.has_any_role(*role_names):
                return view_func(request, *args, **kwargs)
            
            messages.error(
                request,
                f'You must be one of: {", ".join(role_names)} to access this page.'
            )
            return redirect('dashboard:home')
        return wrapper
    return decorator
```

---

## 📁 PHASE 5: APPLY TO VIEWS

### **Example 1: Work Orders**

**File:** `apps/workorders/views.py`

**BEFORE:**
```python
from django.contrib.auth.decorators import login_required

@login_required
def approve_workorder(request, pk):
    # Anyone logged in can approve!
    workorder = get_object_or_404(WorkOrder, pk=pk)
    workorder.status = 'APPROVED'
    workorder.save()
    return redirect('workorders:detail', pk=pk)
```

**AFTER:**
```python
from apps.accounts.decorators import require_permission
from apps.accounts.permissions import WORKORDER_APPROVE

@require_permission(WORKORDER_APPROVE)
def approve_workorder(request, pk):
    # Only users with approve permission can access
    workorder = get_object_or_404(WorkOrder, pk=pk)
    workorder.status = 'APPROVED'
    workorder.approved_by = request.user
    workorder.approved_at = timezone.now()
    workorder.save()
    return redirect('workorders:detail', pk=pk)
```

### **Example 2: Class-Based Views**

**File:** `apps/workorders/views.py`

```python
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import CreateView
from apps.accounts.permissions import WORKORDER_CREATE


class WorkOrderCreateView(UserPassesTestMixin, CreateView):
    model = WorkOrder
    template_name = 'workorders/create.html'
    fields = ['customer', 'drill_bit_type', 'serial_number']
    
    def test_func(self):
        """Check if user has permission."""
        return self.request.user.has_permission(WORKORDER_CREATE)
    
    def handle_no_permission(self):
        """Handle users without permission."""
        messages.error(
            self.request,
            'You do not have permission to create work orders.'
        )
        return redirect('workorders:list')
```

### **Priority Views to Protect:**

**1. Approval Actions (HIGH):**
- `apps/workorders/views.py`: approve_workorder
- `apps/sales/views.py`: approve_service_request
- `apps/quality/views.py`: approve_inspection

**2. Delete Actions (HIGH):**
- All delete views across all apps

**3. Financial Views (HIGH):**
- `apps/reports/views.py`: financial_reports
- `apps/supplychain/views.py`: purchase_order views

**4. User Management (HIGH):**
- `apps/accounts/views.py`: create/edit/delete user views

**5. Settings (MEDIUM):**
- Any settings/configuration views

---

## 📁 PHASE 6: UPDATE TEMPLATES

### **Example: Show/Hide Buttons**

**File:** `templates/workorders/detail.html`

**BEFORE:**
```html
<!-- Everyone sees approve button -->
<button class="btn btn-success">Approve</button>
<button class="btn btn-danger">Delete</button>
```

**AFTER:**
```html
{% load accounts_tags %}

<!-- Only show approve button if user has permission -->
{% if request.user|has_permission:'workorder_approve' %}
  <button class="btn btn-success">Approve</button>
{% endif %}

<!-- Only show delete button if user has permission -->
{% if request.user|has_permission:'workorder_delete' %}
  <button class="btn btn-danger">Delete</button>
{% endif %}
```

### **Create Template Tag:**

**File:** `apps/accounts/templatetags/accounts_tags.py` (NEW FILE)

```python
from django import template

register = template.Library()


@register.filter
def has_permission(user, permission):
    """Template filter to check if user has permission."""
    return user.has_permission(permission)


@register.filter
def has_role(user, role_name):
    """Template filter to check if user has role."""
    return user.has_role(role_name)
```

### **Navigation Menu Example:**

**File:** `templates/base.html`

```html
{% load accounts_tags %}

<nav>
  <!-- Everyone sees these -->
  <a href="{% url 'dashboard:home' %}">Dashboard</a>
  <a href="{% url 'workorders:list' %}">Work Orders</a>
  
  <!-- Only managers and admins see this -->
  {% if request.user|has_role:'ADMIN' or request.user|has_role:'MANAGER' %}
    <a href="{% url 'reports:financial' %}">Financial Reports</a>
  {% endif %}
  
  <!-- Only admins see this -->
  {% if request.user|has_role:'ADMIN' %}
    <a href="{% url 'accounts:user_list' %}">User Management</a>
    <a href="{% url 'settings:index' %}">Settings</a>
  {% endif %}
</nav>
```

---

## 📁 PHASE 7: TESTING

### **File:** `apps/accounts/tests/test_permissions.py` (NEW FILE)

```python
import pytest
from django.contrib.auth import get_user_model
from apps.accounts.models import Role
from apps.accounts.permissions import (
    WORKORDER_APPROVE,
    WORKORDER_VIEW,
    ROLE_PERMISSIONS
)

User = get_user_model()


@pytest.fixture
def admin_role(db):
    """Create admin role."""
    return Role.objects.create(
        name='ADMIN',
        display_name='Administrator',
        permissions=ROLE_PERMISSIONS['ADMIN']
    )


@pytest.fixture
def manager_role(db):
    """Create manager role."""
    return Role.objects.create(
        name='MANAGER',
        display_name='Manager',
        permissions=ROLE_PERMISSIONS['MANAGER']
    )


@pytest.fixture
def technician_role(db):
    """Create technician role."""
    return Role.objects.create(
        name='TECHNICIAN',
        display_name='Technician',
        permissions=ROLE_PERMISSIONS['TECHNICIAN']
    )


@pytest.fixture
def admin_user(db, admin_role):
    """Create admin user."""
    return User.objects.create_user(
        username='admin',
        password='password',
        role=admin_role
    )


@pytest.fixture
def manager_user(db, manager_role):
    """Create manager user."""
    return User.objects.create_user(
        username='manager',
        password='password',
        role=manager_role
    )


@pytest.fixture
def technician_user(db, technician_role):
    """Create technician user."""
    return User.objects.create_user(
        username='technician',
        password='password',
        role=technician_role
    )


class TestRolePermissions:
    """Test role-based permissions."""
    
    def test_admin_has_all_permissions(self, admin_user):
        """Admin should have all permissions."""
        assert admin_user.has_permission(WORKORDER_APPROVE)
        assert admin_user.has_permission(WORKORDER_VIEW)
    
    def test_manager_can_approve(self, manager_user):
        """Manager should be able to approve."""
        assert manager_user.has_permission(WORKORDER_APPROVE)
    
    def test_technician_cannot_approve(self, technician_user):
        """Technician should not be able to approve."""
        assert not technician_user.has_permission(WORKORDER_APPROVE)
    
    def test_technician_can_view(self, technician_user):
        """Technician should be able to view."""
        assert technician_user.has_permission(WORKORDER_VIEW)


class TestViewPermissions:
    """Test view permission decorators."""
    
    def test_approve_view_requires_permission(self, client, technician_user):
        """Technician cannot access approve view."""
        client.force_login(technician_user)
        response = client.get('/workorders/1/approve/')
        assert response.status_code == 403  # Forbidden
    
    def test_approve_view_allows_manager(self, client, manager_user):
        """Manager can access approve view."""
        client.force_login(manager_user)
        response = client.get('/workorders/1/approve/')
        assert response.status_code == 200  # OK
```

**Run tests:**

```bash
pytest apps/accounts/tests/test_permissions.py -v
```

---

## ✅ CHECKLIST

### **Implementation Checklist:**

- [ ] Created Role model
- [ ] Created permissions.py with all permissions
- [ ] Created migration for Role
- [ ] Created create_default_roles command
- [ ] Ran create_default_roles command
- [ ] Created decorators.py
- [ ] Created template tags
- [ ] Applied decorators to critical views
- [ ] Updated templates to show/hide based on permissions
- [ ] Created permission tests
- [ ] Ran all tests
- [ ] Assigned roles to existing users
- [ ] Tested in browser

---

## 🚀 NEXT STEPS

After implementing permissions:

1. **Assign Roles to Users:**
   ```python
   python manage.py shell
   >>> from django.contrib.auth import get_user_model
   >>> from apps.accounts.models import Role
   >>> User = get_user_model()
   >>> admin_role = Role.objects.get(name='ADMIN')
   >>> user = User.objects.get(username='john')
   >>> user.role = admin_role
   >>> user.save()
   ```

2. **Update User Creation:**
   - Add role field to user creation forms
   - Default new users to VIEWER role

3. **Documentation:**
   - Document role permissions in USER_GUIDE.md
   - Document role management in ADMIN_GUIDE.md

---

## 📊 SUMMARY

**What You Get:**

✅ **4 Roles:** Admin, Manager, Technician, Viewer  
✅ **20+ Permissions:** Fine-grained access control  
✅ **View Decorators:** Easy to apply to any view  
✅ **Template Tags:** Show/hide UI elements  
✅ **Tests:** Ensure permissions work correctly  

**Security Improvements:**

✅ Only authorized users can approve  
✅ Only authorized users can delete  
✅ Only authorized users see financial data  
✅ Only authorized users can manage users  

**Time:** 10-12 hours (1-2 days)

---

**Your system will be SECURE!** 🔐
