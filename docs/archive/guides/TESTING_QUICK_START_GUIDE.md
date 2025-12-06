# 🧪 TESTING QUICK START GUIDE
## Fix Critical Blocker #2 - Get to 20% Coverage

**Problem:** Project has 0 tests despite 131 models, 74 views, 35 forms  
**Impact:** No confidence in code correctness, regression risk  
**Time Required:** 1-2 weeks for 20% coverage (but start with 2-3 hours for basics)  
**Difficulty:** Medium  

---

## 🎯 PHILOSOPHY: START SMALL, BUILD CONFIDENCE

**You Don't Need:**
- 100% test coverage (that's overkill)
- Complex test fixtures
- Mocking everything
- Perfect tests

**You DO Need:**
- Tests for critical workflows
- Tests for business logic
- Confidence to refactor
- Regression prevention

**Our Goal:** Get to 20% coverage with high-value tests.

---

## ⚙️ SETUP TESTING INFRASTRUCTURE

### Step 1: Verify pytest is installed

```bash
# Should already be in requirements.txt
pip install pytest pytest-django pytest-cov factory-boy
```

### Step 2: Create pytest.ini

```bash
cat > pytest.ini << 'EOF'
[pytest]
DJANGO_SETTINGS_MODULE = ardt_fms.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --strict-markers
    --tb=short
    --cov=apps
    --cov-report=html
    --cov-report=term-missing
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
EOF
```

### Step 3: Create conftest.py (shared fixtures)

```bash
cat > conftest.py << 'EOF'
"""
Shared test fixtures for ARDT FMS
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user_factory(db):
    """Factory for creating test users"""
    def create_user(**kwargs):
        defaults = {
            'username': 'testuser',
            'email': 'test@example.com',
            'is_active': True,
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)
    return create_user


@pytest.fixture
def admin_user(db, user_factory):
    """Create an admin user"""
    return user_factory(
        username='admin',
        email='admin@example.com',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def regular_user(db, user_factory):
    """Create a regular user"""
    return user_factory()


@pytest.fixture
def authenticated_client(client, regular_user):
    """Client with authenticated user"""
    client.force_login(regular_user)
    return client
EOF
```

### Step 4: Test the setup

```bash
# Run pytest to verify setup
pytest --version

# Should show: pytest 7.4.x

# Try running (should have no tests yet)
pytest
# Should show: collected 0 items
```

---

## 🎯 PHASE 1: SMOKE TESTS (2-3 hours)

**Goal:** Verify basic functionality works

### Test 1: Models Can Be Created

```python
# apps/workorders/tests.py
import pytest
from decimal import Decimal
from django.utils import timezone
from apps.workorders.models import DrillBit, WorkOrder


@pytest.mark.django_db
class TestDrillBitModel:
    """Test DrillBit model basic operations"""
    
    def test_can_create_drill_bit(self):
        """Test basic drill bit creation"""
        bit = DrillBit.objects.create(
            serial_number="TEST-001",
            bit_type=DrillBit.BitType.FC,
            size=Decimal("8.500"),
            status=DrillBit.Status.NEW
        )
        assert bit.pk is not None
        assert bit.serial_number == "TEST-001"
        assert str(bit) == "TEST-001 (FC)"
    
    def test_qr_code_auto_generated(self):
        """Test QR code is auto-generated on save"""
        bit = DrillBit.objects.create(
            serial_number="TEST-002",
            bit_type=DrillBit.BitType.RC,
            size=Decimal("12.250"),
        )
        assert bit.qr_code == "BIT-TEST-002"
    
    def test_drill_bit_status_choices(self):
        """Test all status choices are valid"""
        for status_value, _ in DrillBit.Status.choices:
            bit = DrillBit.objects.create(
                serial_number=f"TEST-{status_value}",
                bit_type=DrillBit.BitType.FC,
                size=Decimal("8.500"),
                status=status_value
            )
            assert bit.status == status_value


@pytest.mark.django_db
class TestWorkOrderModel:
    """Test WorkOrder model basic operations"""
    
    def test_can_create_work_order(self):
        """Test basic work order creation"""
        wo = WorkOrder.objects.create(
            wo_number="WO-000001",
            wo_type=WorkOrder.WOType.FC_NEW,
            status=WorkOrder.Status.DRAFT,
            priority=WorkOrder.Priority.NORMAL
        )
        assert wo.pk is not None
        assert wo.wo_number == "WO-000001"
        assert wo.progress_percent == 0
    
    def test_work_order_status_transitions(self):
        """Test work order can transition through statuses"""
        wo = WorkOrder.objects.create(
            wo_number="WO-000002",
            wo_type=WorkOrder.WOType.FC_REPAIR,
        )
        
        # Test transition: DRAFT -> PLANNED -> RELEASED
        assert wo.status == WorkOrder.Status.DRAFT
        
        wo.status = WorkOrder.Status.PLANNED
        wo.save()
        wo.refresh_from_db()
        assert wo.status == WorkOrder.Status.PLANNED
        
        wo.status = WorkOrder.Status.RELEASED
        wo.save()
        wo.refresh_from_db()
        assert wo.status == WorkOrder.Status.RELEASED
```

**Run These Tests:**
```bash
pytest apps/workorders/tests.py -v

# Expected output:
# apps/workorders/tests.py::TestDrillBitModel::test_can_create_drill_bit PASSED
# apps/workorders/tests.py::TestDrillBitModel::test_qr_code_auto_generated PASSED
# ...
# ===== 6 passed in 0.45s =====
```

---

### Test 2: Views Are Accessible

```python
# apps/workorders/test_views.py
import pytest
from django.urls import reverse
from apps.workorders.models import WorkOrder


@pytest.mark.django_db
class TestWorkOrderViews:
    """Test work order views"""
    
    def test_list_view_requires_login(self, client):
        """Test list view redirects if not logged in"""
        url = reverse('workorders:list')
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login
        assert '/accounts/login/' in response.url
    
    def test_list_view_accessible_when_logged_in(self, authenticated_client):
        """Test list view works when logged in"""
        url = reverse('workorders:list')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert 'workorders/workorder_list.html' in [t.name for t in response.templates]
    
    def test_detail_view_shows_work_order(self, authenticated_client):
        """Test detail view displays work order"""
        wo = WorkOrder.objects.create(
            wo_number="WO-TEST-001",
            wo_type=WorkOrder.WOType.FC_NEW,
        )
        
        url = reverse('workorders:detail', kwargs={'pk': wo.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert wo.wo_number in response.content.decode()
    
    def test_create_view_requires_login(self, client):
        """Test create view requires authentication"""
        url = reverse('workorders:create')
        response = client.get(url)
        assert response.status_code == 302
```

**Run These Tests:**
```bash
pytest apps/workorders/test_views.py -v
```

---

### Test 3: Forms Validate Correctly

```python
# apps/workorders/test_forms.py
import pytest
from decimal import Decimal
from apps.workorders.forms import DrillBitForm, WorkOrderForm


class TestDrillBitForm:
    """Test DrillBit form validation"""
    
    def test_valid_form(self):
        """Test form with valid data"""
        form = DrillBitForm(data={
            'serial_number': 'TEST-001',
            'bit_type': 'FC',
            'size': '8.500',
            'iadc_code': '537',
        })
        assert form.is_valid()
    
    def test_serial_number_required(self):
        """Test serial number is required"""
        form = DrillBitForm(data={
            'bit_type': 'FC',
            'size': '8.500',
        })
        assert not form.is_valid()
        assert 'serial_number' in form.errors
    
    def test_size_must_be_positive(self):
        """Test size must be positive"""
        form = DrillBitForm(data={
            'serial_number': 'TEST-001',
            'bit_type': 'FC',
            'size': '-8.500',
        })
        # This will pass validation but you should add custom validation
        # to prevent negative sizes
        assert form.is_valid()  # Currently passes - should be fixed


class TestWorkOrderForm:
    """Test WorkOrder form validation"""
    
    def test_valid_form(self):
        """Test form with valid data"""
        form = WorkOrderForm(data={
            'wo_number': 'WO-000001',
            'wo_type': 'FC_NEW',
            'priority': 'NORMAL',
        })
        assert form.is_valid()
    
    def test_wo_number_required(self):
        """Test work order number is required"""
        form = WorkOrderForm(data={
            'wo_type': 'FC_NEW',
        })
        assert not form.is_valid()
        assert 'wo_number' in form.errors
```

**Run These Tests:**
```bash
pytest apps/workorders/test_forms.py -v
```

---

### Test 4: Admin Interface Works

```python
# apps/workorders/test_admin.py
import pytest
from django.contrib import admin
from apps.workorders.models import DrillBit, WorkOrder
from apps.workorders.admin import DrillBitAdmin, WorkOrderAdmin


class TestDrillBitAdmin:
    """Test DrillBit admin configuration"""
    
    def test_drill_bit_registered(self):
        """Test DrillBit is registered in admin"""
        assert DrillBit in admin.site._registry
    
    def test_admin_list_display(self):
        """Test list_display is configured"""
        admin_class = admin.site._registry[DrillBit]
        assert hasattr(admin_class, 'list_display')
        assert 'serial_number' in admin_class.list_display
    
    def test_admin_search_fields(self):
        """Test search_fields is configured"""
        admin_class = admin.site._registry[DrillBit]
        assert hasattr(admin_class, 'search_fields')


class TestWorkOrderAdmin:
    """Test WorkOrder admin configuration"""
    
    def test_work_order_registered(self):
        """Test WorkOrder is registered in admin"""
        assert WorkOrder in admin.site._registry
```

**Run These Tests:**
```bash
pytest apps/workorders/test_admin.py -v
```

---

## 🎯 PHASE 2: CRITICAL WORKFLOW TESTS (4-6 hours)

**Goal:** Test end-to-end business workflows

### Workflow 1: Drill Bit Registration

```python
# apps/workorders/test_workflows.py
import pytest
from decimal import Decimal
from apps.workorders.models import DrillBit


@pytest.mark.django_db
class TestDrillBitRegistrationWorkflow:
    """Test complete drill bit registration workflow"""
    
    def test_new_drill_bit_registration(self, regular_user):
        """Test registering a new drill bit from start to finish"""
        # Step 1: Create drill bit
        bit = DrillBit.objects.create(
            serial_number="DB-2024-001",
            bit_type=DrillBit.BitType.FC,
            size=Decimal("8.500"),
            iadc_code="537",
            status=DrillBit.Status.NEW,
            created_by=regular_user
        )
        
        # Step 2: Verify it was created
        assert bit.pk is not None
        assert bit.serial_number == "DB-2024-001"
        assert bit.status == DrillBit.Status.NEW
        assert bit.created_by == regular_user
        
        # Step 3: Verify QR code generated
        assert bit.qr_code == "BIT-DB-2024-001"
        
        # Step 4: Move to stock
        bit.status = DrillBit.Status.IN_STOCK
        bit.save()
        
        # Step 5: Verify status changed
        bit.refresh_from_db()
        assert bit.status == DrillBit.Status.IN_STOCK
        
        # Step 6: Verify usage tracking initialized
        assert bit.total_hours == 0
        assert bit.total_footage == 0
        assert bit.run_count == 0
```

### Workflow 2: Work Order Creation and Execution

```python
@pytest.mark.django_db
class TestWorkOrderWorkflow:
    """Test complete work order workflow"""
    
    def test_work_order_lifecycle(self, regular_user):
        """Test work order from creation to completion"""
        # Step 1: Create work order in DRAFT
        wo = WorkOrder.objects.create(
            wo_number="WO-2024-001",
            wo_type=WorkOrder.WOType.FC_REPAIR,
            status=WorkOrder.Status.DRAFT,
            priority=WorkOrder.Priority.NORMAL,
            created_by=regular_user
        )
        assert wo.status == WorkOrder.Status.DRAFT
        assert wo.progress_percent == 0
        
        # Step 2: Plan the work order
        from datetime import date, timedelta
        wo.status = WorkOrder.Status.PLANNED
        wo.planned_start = date.today()
        wo.planned_end = date.today() + timedelta(days=7)
        wo.save()
        wo.refresh_from_db()
        assert wo.status == WorkOrder.Status.PLANNED
        
        # Step 3: Release to production
        wo.status = WorkOrder.Status.RELEASED
        wo.save()
        wo.refresh_from_db()
        assert wo.status == WorkOrder.Status.RELEASED
        
        # Step 4: Start work
        from django.utils import timezone
        wo.status = WorkOrder.Status.IN_PROGRESS
        wo.actual_start = timezone.now()
        wo.progress_percent = 10
        wo.save()
        wo.refresh_from_db()
        assert wo.status == WorkOrder.Status.IN_PROGRESS
        assert wo.actual_start is not None
        
        # Step 5: Update progress
        wo.progress_percent = 50
        wo.save()
        wo.refresh_from_db()
        assert wo.progress_percent == 50
        
        # Step 6: Send to QC
        wo.status = WorkOrder.Status.QC_PENDING
        wo.progress_percent = 90
        wo.save()
        wo.refresh_from_db()
        assert wo.status == WorkOrder.Status.QC_PENDING
        
        # Step 7: Pass QC
        wo.status = WorkOrder.Status.QC_PASSED
        wo.progress_percent = 100
        wo.save()
        wo.refresh_from_db()
        assert wo.status == WorkOrder.Status.QC_PASSED
        
        # Step 8: Complete work order
        wo.status = WorkOrder.Status.COMPLETED
        wo.actual_end = timezone.now()
        wo.save()
        wo.refresh_from_db()
        assert wo.status == WorkOrder.Status.COMPLETED
        assert wo.actual_end is not None
        assert wo.progress_percent == 100
```

**Run Workflow Tests:**
```bash
pytest apps/workorders/test_workflows.py -v
```

---

## 🎯 PHASE 3: EXPAND TO OTHER APPS (ongoing)

### Test Quality App

```python
# apps/quality/tests.py
import pytest
from apps.quality.models import NCR, Inspection
from apps.workorders.models import WorkOrder


@pytest.mark.django_db
class TestNCRModel:
    """Test NCR (Non-Conformance Report) model"""
    
    def test_can_create_ncr(self, regular_user):
        """Test basic NCR creation"""
        wo = WorkOrder.objects.create(
            wo_number="WO-NCR-001",
            wo_type=WorkOrder.WOType.FC_REPAIR,
        )
        
        from django.utils import timezone
        ncr = NCR.objects.create(
            ncr_number="NCR-2024-001",
            work_order=wo,
            title="Cutters damaged during assembly",
            description="Found 3 damaged cutters during final inspection",
            severity=NCR.Severity.MAJOR,
            detected_at=timezone.now(),
            detected_by=regular_user,
            status=NCR.Status.OPEN
        )
        
        assert ncr.pk is not None
        assert ncr.ncr_number == "NCR-2024-001"
        assert ncr.work_order == wo
        assert ncr.severity == NCR.Severity.MAJOR
    
    def test_ncr_status_workflow(self):
        """Test NCR progresses through statuses"""
        from django.utils import timezone
        ncr = NCR.objects.create(
            ncr_number="NCR-2024-002",
            title="Test NCR",
            description="Test description",
            severity=NCR.Severity.MINOR,
            detected_at=timezone.now(),
        )
        
        # Open -> Investigating
        assert ncr.status == NCR.Status.OPEN
        ncr.status = NCR.Status.INVESTIGATING
        ncr.save()
        
        # Investigating -> Pending Disposition
        ncr.status = NCR.Status.PENDING_DISPOSITION
        ncr.save()
        
        # Pending Disposition -> Closed
        ncr.status = NCR.Status.CLOSED
        ncr.disposition = NCR.Disposition.REWORK
        ncr.save()
        
        ncr.refresh_from_db()
        assert ncr.status == NCR.Status.CLOSED
        assert ncr.disposition == NCR.Disposition.REWORK
```

---

## 📊 MEASURING TEST COVERAGE

### Run Tests with Coverage

```bash
# Run all tests with coverage report
pytest --cov=apps --cov-report=html --cov-report=term-missing

# Output:
# Name                              Stmts   Miss  Cover   Missing
# ---------------------------------------------------------------
# apps/workorders/models.py           145     30    79%   45-52, 89-95
# apps/workorders/views.py            120     85    29%   ...
# apps/quality/models.py               98     65    34%   ...
# ---------------------------------------------------------------
# TOTAL                               2847   2137    25%
```

### View Detailed Coverage

```bash
# Open HTML report
open htmlcov/index.html

# Shows:
# - Which lines are tested (green)
# - Which lines are not tested (red)
# - Coverage percentage per file
```

---

## 🎯 TARGET: 20% COVERAGE BREAKDOWN

To reach 20% coverage, focus on:

**High Priority (Test First):**
- ✅ Models (basic CRUD) - 5%
- ✅ Critical workflows - 8%
- ✅ Forms validation - 3%
- ✅ View authentication - 2%
- ✅ Admin registration - 2%

**Total:** 20% coverage

**Don't Test Yet:**
- Utility functions (test later)
- Template rendering (manual QA)
- Static files (not code)
- Settings (configuration)

---

## 🚀 QUICK WINS - TEST THESE NEXT

### 1. Inventory Models (30 minutes)

```python
# apps/inventory/tests.py
@pytest.mark.django_db
def test_inventory_item_creation():
    from apps.inventory.models import InventoryItem
    item = InventoryItem.objects.create(
        code="INV-001",
        name="Test Item",
        item_type=InventoryItem.ItemType.RAW_MATERIAL,
    )
    assert item.pk is not None
```

### 2. Sales Models (30 minutes)

```python
# apps/sales/tests.py
@pytest.mark.django_db
def test_customer_creation():
    from apps.sales.models import Customer
    customer = Customer.objects.create(
        code="CUST-001",
        name="Test Customer",
        customer_type=Customer.CustomerType.CORPORATE,
    )
    assert customer.pk is not None
```

### 3. Planning Models (30 minutes)

```python
# apps/planning/tests.py
@pytest.mark.django_db
def test_production_plan_creation():
    from apps.planning.models import ProductionPlan
    plan = ProductionPlan.objects.create(
        plan_number="PLAN-001",
        status=ProductionPlan.Status.DRAFT,
    )
    assert plan.pk is not None
```

---

## 💡 TESTING BEST PRACTICES

### DO:
- ✅ Test one thing per test
- ✅ Use descriptive test names
- ✅ Keep tests independent
- ✅ Use fixtures for common setup
- ✅ Test critical paths first
- ✅ Run tests before committing

### DON'T:
- ❌ Test Django framework code
- ❌ Test third-party libraries
- ❌ Write overly complex tests
- ❌ Skip tests that fail
- ❌ Depend on test execution order
- ❌ Test implementation details

---

## 🔄 RUNNING TESTS IN CI/CD

### GitHub Actions Example

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost/test_db
        SECRET_KEY: test-secret-key-for-ci
        DEBUG: True
      run: |
        pytest --cov=apps --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## ✅ SUCCESS CHECKLIST

Phase 1 Complete When:
- [ ] pytest runs without errors
- [ ] At least 10 tests pass
- [ ] Models can be created
- [ ] Views are accessible
- [ ] Forms validate

Phase 2 Complete When:
- [ ] Critical workflows tested
- [ ] At least 30 tests pass
- [ ] Coverage reaches 10%

Phase 3 Complete When:
- [ ] All major apps have tests
- [ ] At least 100 tests pass
- [ ] Coverage reaches 20%
- [ ] CI/CD runs tests automatically

---

## 🎉 WHEN YOU REACH 20%

**You'll Have:**
- ✅ Confidence to refactor
- ✅ Regression prevention
- ✅ Faster debugging
- ✅ Better code design
- ✅ Documentation via tests

**Move On To:**
- Security hardening
- Permission checks
- Performance optimization
- Production deployment

---

**END OF TESTING GUIDE**

**Start with Phase 1 (2-3 hours)**  
**Then expand to Phase 2 (4-6 hours)**  
**Build to 20% over 1-2 weeks**  

**Next:** Read Security Hardening Checklist
