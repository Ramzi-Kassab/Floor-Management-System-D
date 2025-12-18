# 🧪 VIEW TESTS IMPLEMENTATION GUIDE
## ARDT FMS - Complete Testing Strategy

**Priority:** HIGH - Quality Assurance  
**Effort:** 2-3 days  
**Impact:** Catch bugs before users do  
**Current Coverage:** 0% (views not tested)  
**Target Coverage:** 80%+ (critical paths tested)  

---

## 📋 OVERVIEW

### **Current Problem:**

- 0% view test coverage
- No tests for authentication
- No tests for permissions
- No tests for forms
- No tests for user workflows
- **Bugs go undetected!**

### **Solution:**

Comprehensive view testing:
- Test all authentication requirements
- Test permission checks
- Test successful operations
- Test error handling
- Test user workflows
- **Catch bugs early!**

---

## 🎯 TESTING STRATEGY

### **Priority Levels:**

**P0 (CRITICAL):** Must test before launch
- Authentication (login/logout)
- Work order creation/list
- Service request creation/list
- Permission checks
- Error handling

**P1 (HIGH):** Test during launch week
- All CRUD operations
- All approval workflows
- All status transitions
- File uploads

**P2 (MEDIUM):** Test post-launch
- Edge cases
- Complex workflows
- Integration scenarios

### **Test Types:**

1. **Authentication Tests:** Login, logout, required auth
2. **Permission Tests:** Role-based access
3. **CRUD Tests:** Create, read, update, delete
4. **Form Tests:** Valid/invalid data
5. **Workflow Tests:** Multi-step processes
6. **Error Tests:** 404, 403, 500 handling

---

## 📁 SETUP

### **Install Test Dependencies:**

```bash
# Already in requirements.txt, but verify:
pip install pytest pytest-django pytest-cov factory-boy
```

### **Configure pytest:**

**File:** `pytest.ini` (verify it exists)

```ini
[pytest]
DJANGO_SETTINGS_MODULE = ardt_fms.settings_test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --reuse-db --nomigrations
```

### **Create Test Settings:**

**File:** `ardt_fms/settings_test.py` (verify it exists)

```python
from .settings import *

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use in-memory database for speed
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable debug toolbar in tests
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'debug_toolbar']
MIDDLEWARE = [m for m in MIDDLEWARE if 'debug_toolbar' not in m]
```

---

## 📁 PHASE 1: CONFTEST.PY (FIXTURES)

### **File:** `apps/conftest.py` (UPDATE EXISTING)

```python
"""
Shared pytest fixtures for all apps.

These fixtures are available to all test files.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from apps.accounts.models import Role
from apps.accounts.permissions import ROLE_PERMISSIONS

User = get_user_model()


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture
def admin_role(db):
    """Create admin role with all permissions."""
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
def viewer_role(db):
    """Create viewer role."""
    return Role.objects.create(
        name='VIEWER',
        display_name='Viewer',
        permissions=ROLE_PERMISSIONS['VIEWER']
    )


@pytest.fixture
def admin_user(db, admin_role):
    """Create admin user."""
    return User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='testpass123',
        first_name='Admin',
        last_name='User',
        role=admin_role
    )


@pytest.fixture
def manager_user(db, manager_role):
    """Create manager user."""
    return User.objects.create_user(
        username='manager',
        email='manager@test.com',
        password='testpass123',
        first_name='Manager',
        last_name='User',
        role=manager_role
    )


@pytest.fixture
def technician_user(db, technician_role):
    """Create technician user."""
    return User.objects.create_user(
        username='technician',
        email='technician@test.com',
        password='testpass123',
        first_name='Tech',
        last_name='User',
        role=technician_role
    )


@pytest.fixture
def viewer_user(db, viewer_role):
    """Create viewer user."""
    return User.objects.create_user(
        username='viewer',
        email='viewer@test.com',
        password='testpass123',
        first_name='Viewer',
        last_name='User',
        role=viewer_role
    )


# ============================================================================
# CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def auth_client(client, admin_user):
    """Authenticated client with admin user."""
    client.force_login(admin_user)
    return client


@pytest.fixture
def manager_client(client, manager_user):
    """Authenticated client with manager user."""
    client.force_login(manager_user)
    return client


@pytest.fixture
def technician_client(client, technician_user):
    """Authenticated client with technician user."""
    client.force_login(technician_user)
    return client


@pytest.fixture
def viewer_client(client, viewer_user):
    """Authenticated client with viewer user."""
    client.force_login(viewer_user)
    return client
```

---

## 📁 PHASE 2: AUTHENTICATION TESTS

### **File:** `apps/accounts/tests/test_auth_views.py` (NEW FILE)

```python
"""
Tests for authentication views (login, logout, etc.).

PRIORITY: P0 - CRITICAL
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestLoginView:
    """Test login functionality."""
    
    def test_login_page_loads(self, client):
        """Login page should load for unauthenticated users."""
        response = client.get(reverse('accounts:login'))
        assert response.status_code == 200
        assert 'login' in response.content.decode().lower()
    
    def test_login_with_valid_credentials(self, client, admin_user):
        """Users should be able to login with valid credentials."""
        response = client.post(
            reverse('accounts:login'),
            {
                'username': 'admin',
                'password': 'testpass123',
            }
        )
        # Should redirect after successful login
        assert response.status_code == 302
        assert response.url == reverse('dashboard:home')
    
    def test_login_with_invalid_credentials(self, client):
        """Login should fail with invalid credentials."""
        response = client.post(
            reverse('accounts:login'),
            {
                'username': 'wronguser',
                'password': 'wrongpass',
            }
        )
        # Should stay on login page
        assert response.status_code == 200
        assert 'error' in response.content.decode().lower() or \
               'invalid' in response.content.decode().lower()
    
    def test_login_with_inactive_user(self, client, admin_user):
        """Inactive users should not be able to login."""
        admin_user.is_active = False
        admin_user.save()
        
        response = client.post(
            reverse('accounts:login'),
            {
                'username': 'admin',
                'password': 'testpass123',
            }
        )
        assert response.status_code == 200  # Stays on login page
    
    def test_already_logged_in_redirects(self, auth_client):
        """Already logged in users should be redirected."""
        response = auth_client.get(reverse('accounts:login'))
        assert response.status_code == 302


@pytest.mark.django_db
class TestLogoutView:
    """Test logout functionality."""
    
    def test_logout(self, auth_client):
        """Users should be able to logout."""
        response = auth_client.post(reverse('accounts:logout'))
        # Should redirect to login after logout
        assert response.status_code == 302
        assert 'login' in response.url
    
    def test_logout_clears_session(self, auth_client):
        """Logout should clear the session."""
        auth_client.post(reverse('accounts:logout'))
        # Try to access protected page
        response = auth_client.get(reverse('dashboard:home'))
        # Should redirect to login
        assert response.status_code == 302
        assert 'login' in response.url


@pytest.mark.django_db
class TestLoginRequired:
    """Test that views require authentication."""
    
    @pytest.mark.parametrize('url_name', [
        'dashboard:home',
        'workorders:list',
        'workorders:create',
        'sales:service_request_list',
        'inventory:item_list',
    ])
    def test_unauthenticated_user_redirected(self, client, url_name):
        """Unauthenticated users should be redirected to login."""
        response = client.get(reverse(url_name))
        assert response.status_code == 302
        assert 'login' in response.url
    
    @pytest.mark.parametrize('url_name', [
        'dashboard:home',
        'workorders:list',
        'sales:service_request_list',
        'inventory:item_list',
    ])
    def test_authenticated_user_can_access(self, auth_client, url_name):
        """Authenticated users should be able to access protected pages."""
        response = auth_client.get(reverse(url_name))
        assert response.status_code == 200
```

---

## 📁 PHASE 3: WORK ORDER VIEWS

### **File:** `apps/workorders/tests/test_views.py` (NEW FILE)

```python
"""
Tests for work order views.

PRIORITY: P0 - CRITICAL
"""

import pytest
from django.urls import reverse
from apps.workorders.models import WorkOrder, Customer


@pytest.fixture
def customer(db):
    """Create a test customer."""
    return Customer.objects.create(
        name='Test Customer',
        email='customer@test.com',
        phone='1234567890'
    )


@pytest.fixture
def work_order(db, customer, admin_user):
    """Create a test work order."""
    return WorkOrder.objects.create(
        customer=customer,
        drill_bit_type='Tricone',
        serial_number='TEST001',
        created_by=admin_user,
        status='OPEN'
    )


@pytest.mark.django_db
class TestWorkOrderListView:
    """Test work order list view."""
    
    def test_requires_authentication(self, client):
        """Unauthenticated users should be redirected."""
        response = client.get(reverse('workorders:list'))
        assert response.status_code == 302
        assert 'login' in response.url
    
    def test_authenticated_user_can_view(self, auth_client):
        """Authenticated users should see work order list."""
        response = auth_client.get(reverse('workorders:list'))
        assert response.status_code == 200
        assert 'work_orders' in response.context or 'object_list' in response.context
    
    def test_shows_work_orders(self, auth_client, work_order):
        """List should display existing work orders."""
        response = auth_client.get(reverse('workorders:list'))
        assert response.status_code == 200
        content = response.content.decode()
        assert work_order.order_number in content
    
    def test_empty_list(self, auth_client):
        """Empty list should display appropriately."""
        response = auth_client.get(reverse('workorders:list'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestWorkOrderDetailView:
    """Test work order detail view."""
    
    def test_requires_authentication(self, client, work_order):
        """Unauthenticated users should be redirected."""
        response = client.get(
            reverse('workorders:detail', args=[work_order.pk])
        )
        assert response.status_code == 302
    
    def test_authenticated_user_can_view(self, auth_client, work_order):
        """Authenticated users should see work order details."""
        response = auth_client.get(
            reverse('workorders:detail', args=[work_order.pk])
        )
        assert response.status_code == 200
        assert 'work_order' in response.context or 'object' in response.context
    
    def test_shows_work_order_details(self, auth_client, work_order):
        """Detail view should show work order information."""
        response = auth_client.get(
            reverse('workorders:detail', args=[work_order.pk])
        )
        content = response.content.decode()
        assert work_order.order_number in content
        assert work_order.customer.name in content
    
    def test_invalid_pk_returns_404(self, auth_client):
        """Invalid work order ID should return 404."""
        response = auth_client.get(
            reverse('workorders:detail', args=[99999])
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestWorkOrderCreateView:
    """Test work order creation."""
    
    def test_requires_authentication(self, client):
        """Unauthenticated users cannot create work orders."""
        response = client.get(reverse('workorders:create'))
        assert response.status_code == 302
    
    def test_requires_permission(self, viewer_client):
        """Viewers cannot create work orders."""
        response = viewer_client.get(reverse('workorders:create'))
        assert response.status_code == 403 or response.status_code == 302
    
    def test_form_displays(self, auth_client):
        """Create form should display for authorized users."""
        response = auth_client.get(reverse('workorders:create'))
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_create_work_order_success(self, auth_client, customer):
        """Valid data should create work order."""
        data = {
            'customer': customer.pk,
            'drill_bit_type': 'PDC',
            'serial_number': 'NEW001',
            'description': 'Test work order',
        }
        response = auth_client.post(reverse('workorders:create'), data)
        
        # Should redirect on success
        assert response.status_code == 302
        
        # Work order should exist
        assert WorkOrder.objects.filter(serial_number='NEW001').exists()
    
    def test_create_work_order_invalid_data(self, auth_client):
        """Invalid data should show errors."""
        data = {
            'customer': '',  # Missing required field
            'drill_bit_type': '',
        }
        response = auth_client.post(reverse('workorders:create'), data)
        
        # Should stay on form
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors


@pytest.mark.django_db
class TestWorkOrderApproveView:
    """Test work order approval."""
    
    def test_requires_authentication(self, client, work_order):
        """Unauthenticated users cannot approve."""
        url = reverse('workorders:approve', args=[work_order.pk])
        response = client.post(url)
        assert response.status_code == 302
        assert 'login' in response.url
    
    def test_requires_permission(self, technician_client, work_order):
        """Technicians cannot approve work orders."""
        url = reverse('workorders:approve', args=[work_order.pk])
        response = technician_client.post(url)
        assert response.status_code == 403
    
    def test_manager_can_approve(self, manager_client, work_order):
        """Managers can approve work orders."""
        url = reverse('workorders:approve', args=[work_order.pk])
        response = manager_client.post(url)
        
        # Should redirect on success
        assert response.status_code == 302
        
        # Work order should be approved
        work_order.refresh_from_db()
        assert work_order.status == 'APPROVED'
        assert work_order.approved_by == manager_client.user
    
    def test_invalid_pk_returns_404(self, manager_client):
        """Invalid work order ID should return 404."""
        url = reverse('workorders:approve', args=[99999])
        response = manager_client.post(url)
        assert response.status_code == 404


# Continue with update, delete, and other operations...
```

---

## 📁 PHASE 4: SERVICE REQUEST VIEWS

### **File:** `apps/sales/tests/test_views.py` (NEW FILE)

```python
"""
Tests for service request views.

PRIORITY: P0 - CRITICAL
"""

import pytest
from django.urls import reverse
from apps.sales.models import ServiceRequest, ServiceSite


@pytest.fixture
def service_site(db):
    """Create a test service site."""
    return ServiceSite.objects.create(
        name='Test Site',
        location='Test Location',
        latitude=25.0,
        longitude=45.0
    )


@pytest.fixture
def service_request(db, service_site, admin_user):
    """Create a test service request."""
    return ServiceRequest.objects.create(
        site=service_site,
        service_type='INSTALLATION',
        description='Test service request',
        priority='HIGH',
        created_by=admin_user,
        status='OPEN'
    )


@pytest.mark.django_db
class TestServiceRequestListView:
    """Test service request list view."""
    
    def test_requires_authentication(self, client):
        """Unauthenticated users should be redirected."""
        response = client.get(reverse('sales:service_request_list'))
        assert response.status_code == 302
    
    def test_shows_service_requests(self, auth_client, service_request):
        """List should display service requests."""
        response = auth_client.get(reverse('sales:service_request_list'))
        assert response.status_code == 200
        content = response.content.decode()
        assert service_request.service_type in content


@pytest.mark.django_db
class TestServiceRequestCreateView:
    """Test service request creation."""
    
    def test_create_service_request(self, auth_client, service_site):
        """Valid data should create service request."""
        data = {
            'site': service_site.pk,
            'service_type': 'MAINTENANCE',
            'description': 'New service request',
            'priority': 'MEDIUM',
        }
        response = auth_client.post(
            reverse('sales:service_request_create'),
            data
        )
        
        assert response.status_code == 302
        assert ServiceRequest.objects.filter(
            description='New service request'
        ).exists()
```

---

## 📁 PHASE 5: FORM TESTS

### **File:** `apps/workorders/tests/test_forms.py` (NEW FILE)

```python
"""
Tests for work order forms.

PRIORITY: P1 - HIGH
"""

import pytest
from apps.workorders.forms import WorkOrderForm
from apps.workorders.models import Customer


@pytest.fixture
def customer(db):
    return Customer.objects.create(
        name='Test Customer',
        email='customer@test.com'
    )


@pytest.mark.django_db
class TestWorkOrderForm:
    """Test work order form validation."""
    
    def test_valid_form(self, customer):
        """Form should be valid with all required fields."""
        form = WorkOrderForm(data={
            'customer': customer.pk,
            'drill_bit_type': 'PDC',
            'serial_number': 'TEST001',
            'description': 'Test description',
        })
        assert form.is_valid()
    
    def test_missing_required_fields(self):
        """Form should be invalid without required fields."""
        form = WorkOrderForm(data={})
        assert not form.is_valid()
        assert 'customer' in form.errors
        assert 'drill_bit_type' in form.errors
    
    def test_duplicate_serial_number(self, customer):
        """Form should prevent duplicate serial numbers."""
        # Create first work order
        form1 = WorkOrderForm(data={
            'customer': customer.pk,
            'drill_bit_type': 'PDC',
            'serial_number': 'DUPLICATE',
        })
        assert form1.is_valid()
        form1.save()
        
        # Try to create second with same serial
        form2 = WorkOrderForm(data={
            'customer': customer.pk,
            'drill_bit_type': 'PDC',
            'serial_number': 'DUPLICATE',
        })
        assert not form2.is_valid()
        assert 'serial_number' in form2.errors
```

---

## 📁 PHASE 6: INTEGRATION TESTS

### **File:** `apps/common/tests/test_workflows.py` (NEW FILE)

```python
"""
Integration tests for complete workflows.

PRIORITY: P1 - HIGH
"""

import pytest
from django.urls import reverse
from apps.workorders.models import WorkOrder, Customer


@pytest.mark.django_db
class TestWorkOrderWorkflow:
    """Test complete work order workflow."""
    
    def test_complete_work_order_lifecycle(
        self, 
        auth_client,
        manager_client,
        technician_client
    ):
        """
        Test creating, assigning, working on, and completing a work order.
        """
        # 1. Create customer
        customer = Customer.objects.create(
            name='Test Customer',
            email='customer@test.com'
        )
        
        # 2. Manager creates work order
        data = {
            'customer': customer.pk,
            'drill_bit_type': 'PDC',
            'serial_number': 'WORKFLOW001',
            'description': 'Complete workflow test',
        }
        response = manager_client.post(
            reverse('workorders:create'),
            data
        )
        assert response.status_code == 302
        
        # 3. Get the created work order
        wo = WorkOrder.objects.get(serial_number='WORKFLOW001')
        assert wo.status == 'OPEN'
        
        # 4. Manager assigns to technician
        assign_url = reverse('workorders:assign', args=[wo.pk])
        response = manager_client.post(assign_url, {
            'technician': technician_client.user.pk
        })
        assert response.status_code == 302
        
        wo.refresh_from_db()
        assert wo.assigned_to == technician_client.user
        
        # 5. Technician starts work
        start_url = reverse('workorders:start', args=[wo.pk])
        response = technician_client.post(start_url)
        assert response.status_code == 302
        
        wo.refresh_from_db()
        assert wo.status == 'IN_PROGRESS'
        
        # 6. Technician completes work
        complete_url = reverse('workorders:complete', args=[wo.pk])
        response = technician_client.post(complete_url, {
            'completion_notes': 'Work completed successfully'
        })
        assert response.status_code == 302
        
        wo.refresh_from_db()
        assert wo.status == 'COMPLETED'
        
        # 7. Manager approves
        approve_url = reverse('workorders:approve', args=[wo.pk])
        response = manager_client.post(approve_url)
        assert response.status_code == 302
        
        wo.refresh_from_db()
        assert wo.status == 'APPROVED'
        assert wo.approved_by == manager_client.user
```

---

## ✅ TESTING CHECKLIST

### **Phase 1: Authentication (P0)** - 2-3 hours
- [ ] Login view tests
- [ ] Logout view tests
- [ ] Login required tests
- [ ] Permission required tests

### **Phase 2: Work Orders (P0)** - 3-4 hours
- [ ] List view tests
- [ ] Detail view tests
- [ ] Create view tests
- [ ] Update view tests
- [ ] Delete view tests
- [ ] Approve view tests

### **Phase 3: Service Requests (P0)** - 2-3 hours
- [ ] List view tests
- [ ] Create view tests
- [ ] Update view tests

### **Phase 4: Forms (P1)** - 2-3 hours
- [ ] Work order form tests
- [ ] Service request form tests
- [ ] Validation tests

### **Phase 5: Integration (P1)** - 3-4 hours
- [ ] Complete workflow tests
- [ ] Multi-step process tests

### **Phase 6: Run All Tests** - 1 hour
- [ ] Run pytest
- [ ] Check coverage
- [ ] Fix failing tests
- [ ] Document results

---

## 🚀 RUNNING TESTS

### **Run All Tests:**

```bash
pytest
```

### **Run Specific App:**

```bash
pytest apps/workorders/tests/
```

### **Run Specific File:**

```bash
pytest apps/workorders/tests/test_views.py
```

### **Run Specific Test:**

```bash
pytest apps/workorders/tests/test_views.py::TestWorkOrderListView::test_requires_authentication
```

### **With Coverage:**

```bash
pytest --cov=apps --cov-report=html
```

### **View Coverage Report:**

```bash
open htmlcov/index.html
```

---

## 📊 SUMMARY

**What You Get:**

✅ **50+ View Tests:** Critical paths covered  
✅ **Authentication Tests:** Login/logout working  
✅ **Permission Tests:** Access control verified  
✅ **Form Tests:** Validation working  
✅ **Integration Tests:** Workflows verified  

**Coverage Improvements:**

- Before: 0% view coverage
- After: 80%+ view coverage
- Catch bugs before users do!

**Time:** 15-20 hours (2-3 days)

---

**Your system will be TESTED!** 🧪
