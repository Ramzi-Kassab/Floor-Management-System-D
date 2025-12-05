# 🚀 SPRINT 5 COMPLETE IMPLEMENTATION GUIDE
## Field Services & DRSS Integration - FULL & COMPREHENSIVE

**Version:** 2.0 - Complete, No Shortcuts  
**Date:** December 6, 2024  
**Approach:** Production-ready with tests, permissions, and full validation  
**Timeline:** 20 working days (4 weeks)  
**Documentation:** 250+ pages complete implementation  

---

## 📚 TABLE OF CONTENTS

### PART 1: OVERVIEW & SETUP
1. [Sprint 5 Philosophy](#philosophy)
2. [Timeline & Scope](#timeline)
3. [Testing Strategy](#testing)
4. [Development Environment Setup](#setup)
5. [Success Criteria](#success)

### PART 2: WEEK 1 - FIELD SERVICE MANAGEMENT
6. [Day 1-2: Field Service Request Models](#day1-2)
7. [Day 3-4: Service Scheduling Models](#day3-4)
8. [Day 5: Service Report & Integration](#day5)

### PART 3: WEEK 2 - DRILL STRING FIELD OPERATIONS
9. [Day 6-7: Field Run Tracking](#day6-7)
10. [Day 8-9: Performance & Inspection](#day8-9)
11. [Day 10: Field Incident Tracking](#day10)

### PART 4: WEEK 3 - FIELD DATA CAPTURE
12. [Day 11-12: Data Entry Models](#day11-12)
13. [Day 13-14: Document & Location](#day13-14)
14. [Day 15: Integration & Permissions](#day15)

### PART 5: WEEK 4 - TESTING & VALIDATION
15. [Day 16-17: Comprehensive Testing](#day16-17)
16. [Day 18: Full Validation](#day18)
17. [Day 19-20: Polish & Production Prep](#day19-20)

---

## 📋 PART 1: OVERVIEW & SETUP

### <a name="philosophy"></a>1. SPRINT 5 PHILOSOPHY

#### What's Different from Sprint 4?

**Sprint 4 Approach (Pragmatic):**
```
✅ Models implemented
✅ Migrations applied
⏭️ Tests deferred
⏭️ Permissions deferred
⏭️ Full validation deferred

Result: Fast (11 days) but incomplete
```

**Sprint 5 Approach (Complete):**
```
✅ Models implemented
✅ Tests written alongside
✅ Permissions included
✅ Forms validated
✅ Views secured
✅ Full validation at checkpoints

Result: Thorough (20 days) and production-ready
```

#### Core Principles:

1. **Write Tests First or Alongside**
   - Never mark a model "done" without tests
   - Achieve 75%+ coverage as you build
   - Test edge cases immediately

2. **Include Permissions From Start**
   - Every view has PermissionRequiredMixin
   - Test permissions immediately
   - No "add later" shortcuts

3. **Validate at Every Step**
   - Daily validation (15 min)
   - Weekly comprehensive validation (1 hour)
   - Don't proceed if issues found

4. **Document as You Build**
   - Add docstrings to every class
   - Comment complex logic
   - Update README continuously

5. **Quality Over Speed**
   - Better to complete Day 3 properly than rush to Day 5
   - Better 15 complete models than 18 incomplete
   - Better 80% coverage than 50%

---

### <a name="timeline"></a>2. TIMELINE & SCOPE

#### Honest Timeline: 20 Working Days

**Week 1: Field Service Management (5 days)**
```
Day 1-2: FieldServiceRequest + ServiceSite (2 models, 40 tests)
Day 3-4: FieldTechnician + ServiceSchedule + SiteVisit (3 models, 55 tests)
Day 5:   ServiceReport + Integration Tests (1 model, 25 tests)

Total: 6 models, 120 tests, Week 1 validation
```

**Week 2: Drill String Field Operations (5 days)**
```
Day 6-7:  FieldDrillStringRun + FieldRunData (2 models, 45 tests)
Day 8-9:  FieldPerformanceLog + FieldInspection + RunHours (3 models, 50 tests)
Day 10:   FieldIncident + Integration Tests (1 model, 25 tests)

Total: 6 models, 120 tests, Week 2 validation
```

**Week 3: Field Data Capture & Integration (5 days)**
```
Day 11-12: FieldDataEntry + FieldPhoto (2 models, 45 tests)
Day 13-14: FieldDocument + GPSLocation (2 models, 40 tests)
Day 15:    FieldWorkOrder + FieldAssetAssignment + Permissions (2 models, 30 tests)

Total: 6 models, 115 tests, Week 3 validation
```

**Week 4: Testing & Production Prep (5 days)**
```
Day 16-17: Comprehensive testing suite (50+ additional tests)
Day 18:    Full validation & documentation
Day 19-20: Polish, security audit, production prep

Total: 50+ tests, full validation, production-ready
```

#### Scope: 18 Models + Complete Testing

**Models Breakdown:**
- 6 Field Service models
- 6 Drill String Field models
- 4 Field Data Capture models
- 2 Integration models

**Testing Breakdown:**
- 250+ unit tests
- 40+ integration tests
- 30+ permission tests
- 20+ edge case tests

**Coverage Targets:**
- Models: 80%+
- Views: 70%+
- Forms: 70%+
- Overall: 75%+

---

### <a name="testing"></a>3. TESTING STRATEGY

#### Testing Philosophy

**Every Feature Gets Tested:**
- Models: field validation, methods, properties, relationships
- Forms: validation, save logic, edge cases
- Views: GET/POST, permissions, error handling
- Integration: end-to-end workflows

**Test Types:**

**1. Unit Tests (Core)**
```python
# Test individual model methods
def test_field_service_request_is_overdue():
    """Test overdue detection logic"""
    request = FieldServiceRequest(...)
    assert request.is_overdue == True

# Test model validation
def test_field_service_request_requires_customer():
    """Test customer field is required"""
    with pytest.raises(ValidationError):
        FieldServiceRequest(...).full_clean()
```

**2. Integration Tests**
```python
# Test complete workflows
def test_field_service_workflow():
    """Test: Request → Schedule → Visit → Report"""
    request = create_request()
    schedule = create_schedule(request)
    visit = create_visit(schedule)
    report = create_report(visit)
    
    assert report.status == "COMPLETED"
    assert request.work_order is not None
```

**3. Permission Tests**
```python
# Test view access control
def test_field_request_create_requires_permission():
    """Test create view requires permission"""
    client.force_login(user_without_permission)
    response = client.post('/field-requests/create/', data)
    assert response.status_code == 403
```

**4. Edge Case Tests**
```python
# Test boundary conditions
def test_field_request_past_date():
    """Test handling of past requested dates"""
    request = FieldServiceRequest(
        requested_date=date.today() - timedelta(days=1)
    )
    assert request.is_overdue == True
```

#### Coverage Requirements

**Minimum Coverage Targets:**
```
Sprint 5 Models:     80%
Sprint 5 Views:      70%
Sprint 5 Forms:      70%
Sprint 5 Utils:      60%
Overall Sprint 5:    75%
```

**How to Check Coverage:**
```bash
# Run tests with coverage
pytest apps/sales/tests/ --cov=apps/sales --cov-report=term-missing

# Generate HTML report
pytest --cov=apps --cov-report=html

# Open htmlcov/index.html to see detailed coverage
```

**Coverage Tools:**
```bash
# Install
pip install pytest-cov coverage --break-system-packages

# Configure in pytest.ini
[tool:pytest]
addopts = --cov=apps --cov-report=term-missing --cov-report=html
```

---

### <a name="setup"></a>4. DEVELOPMENT ENVIRONMENT SETUP

#### Prerequisites

**Python Environment:**
```bash
# Verify Python version
python --version
# Should be 3.10+

# Verify virtual environment
which python
# Should be in your venv

# Install testing dependencies
pip install pytest pytest-django pytest-cov factory-boy faker --break-system-packages
```

**Database Setup:**
```bash
# Ensure PostgreSQL is running
sudo systemctl status postgresql

# Verify database connection
python manage.py dbshell
\dt
\q
```

**Django Configuration:**
```bash
# Verify settings
python manage.py check

# Check migrations status
python manage.py showmigrations
```

#### Testing Configuration

**Create/Update pytest.ini:**
```ini
# pytest.ini in project root

[tool:pytest]
DJANGO_SETTINGS_MODULE = project.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    --reuse-db
    --cov=apps
    --cov-report=term-missing
    --cov-report=html
    -v
markers =
    unit: Unit tests
    integration: Integration tests
    permissions: Permission tests
    slow: Slow running tests
```

**Create conftest.py:**
```python
# apps/conftest.py

import pytest
from django.contrib.auth import get_user_model
from apps.sales.models import Customer, ServiceSite
from apps.workorders.models import WorkOrder, DrillBit
from decimal import Decimal

User = get_user_model()

@pytest.fixture
def user(db):
    """Create a test user"""
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )

@pytest.fixture
def admin_user(db):
    """Create an admin user"""
    return User.objects.create_superuser(
        username='admin',
        password='adminpass123',
        email='admin@example.com'
    )

@pytest.fixture
def customer(db):
    """Create a test customer"""
    return Customer.objects.create(
        name='Test Customer',
        code='CUST001'
    )

@pytest.fixture
def service_site(db, customer):
    """Create a test service site"""
    return ServiceSite.objects.create(
        name='Test Site',
        customer=customer,
        address='123 Test St',
        city='Test City',
        country='Test Country'
    )

@pytest.fixture
def drill_bit(db):
    """Create a test drill bit"""
    return DrillBit.objects.create(
        serial_number='TEST-001',
        bit_type='FC',
        size=Decimal('8.500'),
        status='AVAILABLE'
    )

# Add more fixtures as needed
```

---

### <a name="success"></a>5. SUCCESS CRITERIA

#### Sprint 5 is Complete When ALL Criteria Are Met:

**Models & Database:**
- [ ] All 18 models implemented
- [ ] All fields have help_text
- [ ] All ForeignKeys have related_name
- [ ] All models have __str__ methods
- [ ] All models have Meta classes
- [ ] All models have docstrings
- [ ] All custom methods documented
- [ ] All migrations generated
- [ ] All migrations applied
- [ ] Database integrity verified

**Tests:**
- [ ] 250+ tests written
- [ ] All tests passing (0 failures)
- [ ] 75%+ overall coverage
- [ ] 80%+ model coverage
- [ ] 70%+ view coverage
- [ ] 70%+ form coverage
- [ ] All edge cases covered
- [ ] All integration tests passing
- [ ] All permission tests passing

**Code Quality:**
- [ ] flake8: 0 errors
- [ ] black: all files formatted
- [ ] No TODO comments
- [ ] No FIXME comments
- [ ] No print() debugging statements
- [ ] All imports organized
- [ ] No unused imports
- [ ] No commented-out code

**Permissions & Security:**
- [ ] PermissionRequiredMixin on all views
- [ ] Custom permissions defined
- [ ] Permission tests passing
- [ ] Object-level permissions working
- [ ] Anonymous access blocked
- [ ] Role-based access implemented

**Documentation:**
- [ ] All models documented
- [ ] All views documented
- [ ] All forms documented
- [ ] README updated
- [ ] CHANGELOG updated
- [ ] Sprint 5 summary written
- [ ] API documentation (if applicable)

**Validation:**
- [ ] python manage.py check: 0 issues
- [ ] All daily validations passed
- [ ] All weekly validations passed
- [ ] Final comprehensive validation passed
- [ ] No migration conflicts
- [ ] No database integrity issues

**Integration:**
- [ ] Sales app integration working
- [ ] DRSS app integration working
- [ ] WorkOrders integration working
- [ ] Assets integration working
- [ ] Dispatch integration working
- [ ] All relationships verified

**Production Readiness:**
- [ ] All features working
- [ ] All known bugs fixed
- [ ] Performance acceptable
- [ ] Security audit passed
- [ ] Deployment documentation ready
- [ ] Rollback plan documented

---

## 📋 PART 2: WEEK 1 - FIELD SERVICE MANAGEMENT

### <a name="day1-2"></a>DAY 1-2: FIELD SERVICE REQUEST MODELS

**Timeline:** 2 days (16 hours)  
**Deliverables:** 2 models, 40 tests, migrations, validation  
**Coverage Target:** 80%+  

---

#### MODEL 1: FieldServiceRequest

**Purpose:** Track customer requests for field services, integrate with work orders

**File:** `apps/sales/models.py`

**Add this complete model:**

```python
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class FieldServiceRequest(models.Model):
    """
    Track customer requests for field services.
    
    This model manages the complete lifecycle of field service requests,
    from initial customer submission through scheduling, execution, and completion.
    
    Integrates with:
    - ServiceContract: Links to existing service agreements
    - WorkOrder: Generates work orders for approved requests
    - DrillBit/DrillString: Tracks specific assets requiring service
    - FieldTechnician: Assigns qualified technicians
    - ServiceSite: Specifies service location
    
    Workflow:
    1. DRAFT: Created but not submitted
    2. SUBMITTED: Submitted for review
    3. REVIEWED: Reviewed by coordinator
    4. APPROVED: Approved for scheduling
    5. SCHEDULED: Technician assigned, date set
    6. IN_PROGRESS: Work being performed
    7. COMPLETED: Work finished
    8. CANCELLED: Request cancelled
    
    ISO 9001 References:
    - Clause 8.2: Customer Communication
    - Clause 8.5: Production and Service Provision
    
    Author: Sprint 5 Implementation
    Date: December 2024
    """
    
    class RequestType(models.TextChoices):
        """Types of field service requests"""
        DRILL_BIT_INSPECTION = "DRILL_BIT_INSPECTION", "Drill Bit Inspection"
        DRILL_BIT_REPAIR = "DRILL_BIT_REPAIR", "Drill Bit Repair"
        DRILL_STRING_SERVICE = "DRILL_STRING_SERVICE", "Drill String Service"
        DRILL_STRING_INSPECTION = "DRILL_STRING_INSPECTION", "Drill String Inspection"
        EMERGENCY_REPAIR = "EMERGENCY_REPAIR", "Emergency Repair"
        SCHEDULED_MAINTENANCE = "SCHEDULED_MAINTENANCE", "Scheduled Maintenance"
        TECHNICAL_SUPPORT = "TECHNICAL_SUPPORT", "Technical Support"
        TRAINING = "TRAINING", "Training"
        CONSULTATION = "CONSULTATION", "Consultation"
        OTHER = "OTHER", "Other"
    
    class Priority(models.TextChoices):
        """Priority levels for service requests"""
        LOW = "LOW", "Low - Non-urgent, can be scheduled flexibly"
        MEDIUM = "MEDIUM", "Medium - Standard priority"
        HIGH = "HIGH", "High - Important, schedule soon"
        URGENT = "URGENT", "Urgent - Schedule within 24 hours"
        EMERGENCY = "EMERGENCY", "Emergency - Immediate response required"
    
    class Status(models.TextChoices):
        """Request lifecycle status"""
        DRAFT = "DRAFT", "Draft - Not yet submitted"
        SUBMITTED = "SUBMITTED", "Submitted - Awaiting review"
        REVIEWED = "REVIEWED", "Reviewed - Awaiting approval"
        APPROVED = "APPROVED", "Approved - Ready for scheduling"
        SCHEDULED = "SCHEDULED", "Scheduled - Date and technician assigned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress - Work being performed"
        COMPLETED = "COMPLETED", "Completed - Work finished"
        CANCELLED = "CANCELLED", "Cancelled"
        ON_HOLD = "ON_HOLD", "On Hold - Temporarily paused"
    
    # ===== IDENTIFICATION =====
    
    request_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique request number (auto-generated: FSR-YYYY-####)"
    )
    
    # ===== CUSTOMER INFORMATION =====
    
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.PROTECT,
        related_name='field_service_requests',
        help_text="Customer requesting the service"
    )
    
    service_contract = models.ForeignKey(
        'ServiceContract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='field_requests',
        help_text="Related service contract (if applicable)"
    )
    
    # ===== SERVICE LOCATION =====
    
    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.PROTECT,
        related_name='service_requests',
        help_text="Location where service is needed"
    )
    
    # ===== REQUEST DETAILS =====
    
    request_type = models.CharField(
        max_length=50,
        choices=RequestType.choices,
        db_index=True,
        help_text="Type of service requested"
    )
    
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
        help_text="Request priority level"
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Current request status"
    )
    
    # ===== DESCRIPTION =====
    
    title = models.CharField(
        max_length=200,
        help_text="Brief title/summary of the request"
    )
    
    description = models.TextField(
        help_text="Detailed description of service needed"
    )
    
    customer_notes = models.TextField(
        blank=True,
        help_text="Additional notes from customer"
    )
    
    # ===== ASSETS INVOLVED =====
    
    drill_bits = models.ManyToManyField(
        'workorders.DrillBit',
        blank=True,
        related_name='field_service_requests',
        help_text="Drill bits involved in this request"
    )
    
    drill_strings = models.ManyToManyField(
        'drss.DrillString',
        blank=True,
        related_name='field_service_requests',
        help_text="Drill strings involved in this request"
    )
    
    assets = models.ManyToManyField(
        'assets.Asset',
        blank=True,
        related_name='field_service_requests',
        help_text="Other assets involved in this request"
    )
    
    # ===== SCHEDULING =====
    
    requested_date = models.DateField(
        help_text="Date customer wants service performed"
    )
    
    requested_time_slot = models.CharField(
        max_length=50,
        blank=True,
        help_text="Preferred time slot (e.g., 'Morning', '08:00-12:00', 'Afternoon')"
    )
    
    estimated_duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated service duration in hours"
    )
    
    flexible_scheduling = models.BooleanField(
        default=False,
        help_text="Whether customer is flexible with scheduling"
    )
    
    # ===== ASSIGNMENT =====
    
    assigned_technician = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests',
        help_text="Technician assigned to this request"
    )
    
    assigned_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When technician was assigned"
    )
    
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='field_requests_assigned',
        help_text="User who assigned the technician"
    )
    
    # ===== WORK ORDER INTEGRATION =====
    
    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='field_service_requests',
        help_text="Work order generated from this request"
    )
    
    auto_create_work_order = models.BooleanField(
        default=True,
        help_text="Automatically create work order upon approval"
    )
    
    # ===== CONTACT INFORMATION =====
    
    contact_person = models.CharField(
        max_length=200,
        help_text="On-site contact person name"
    )
    
    contact_phone = models.CharField(
        max_length=50,
        help_text="On-site contact phone number"
    )
    
    contact_email = models.EmailField(
        blank=True,
        help_text="On-site contact email address"
    )
    
    alternate_contact_person = models.CharField(
        max_length=200,
        blank=True,
        help_text="Alternate contact person name"
    )
    
    alternate_contact_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Alternate contact phone number"
    )
    
    # ===== REVIEW & APPROVAL =====
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_field_requests',
        help_text="User who reviewed this request"
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was reviewed"
    )
    
    review_notes = models.TextField(
        blank=True,
        help_text="Notes from the reviewer"
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_field_requests',
        help_text="User who approved this request"
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was approved"
    )
    
    approval_notes = models.TextField(
        blank=True,
        help_text="Notes from approver"
    )
    
    # ===== COMPLETION =====
    
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When work actually started"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When work was completed"
    )
    
    completion_notes = models.TextField(
        blank=True,
        help_text="Notes upon completion"
    )
    
    actual_duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual service duration in hours"
    )
    
    # ===== CANCELLATION =====
    
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was cancelled"
    )
    
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_field_requests',
        help_text="User who cancelled this request"
    )
    
    cancellation_reason = models.TextField(
        blank=True,
        help_text="Reason for cancellation"
    )
    
    # ===== AUDIT TRAIL =====
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this request was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this request was last updated"
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_field_requests',
        help_text="User who created this request"
    )
    
    class Meta:
        db_table = "field_service_requests"
        ordering = ["-created_at"]
        verbose_name = "Field Service Request"
        verbose_name_plural = "Field Service Requests"
        indexes = [
            models.Index(fields=['request_number']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['requested_date']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['service_site', 'status']),
            models.Index(fields=['assigned_technician', 'status']),
        ]
        permissions = [
            ("can_review_field_request", "Can review field service requests"),
            ("can_approve_field_request", "Can approve field service requests"),
            ("can_assign_technician", "Can assign technicians to requests"),
            ("can_cancel_field_request", "Can cancel field service requests"),
        ]
    
    def __str__(self):
        return f"{self.request_number} - {self.customer.name} - {self.title}"
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate request number"""
        if not self.request_number:
            self.request_number = self._generate_request_number()
        
        # Update status timestamps
        if self.status == self.Status.IN_PROGRESS and not self.started_at:
            self.started_at = timezone.now()
        elif self.status == self.Status.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status == self.Status.CANCELLED and not self.cancelled_at:
            self.cancelled_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate model data"""
        super().clean()
        
        # Validate requested date is not in the past (for new requests)
        if not self.pk and self.requested_date:
            if self.requested_date < timezone.now().date():
                raise ValidationError({
                    'requested_date': 'Requested date cannot be in the past'
                })
        
        # Validate technician assignment
        if self.assigned_technician and self.status == self.Status.DRAFT:
            raise ValidationError({
                'assigned_technician': 'Cannot assign technician to draft request'
            })
        
        # Validate duration
        if self.actual_duration_hours and self.estimated_duration_hours:
            if self.actual_duration_hours > self.estimated_duration_hours * 3:
                # This is just a warning, don't raise error
                pass
    
    def _generate_request_number(self):
        """Generate unique request number: FSR-YYYY-####"""
        year = timezone.now().year
        
        # Get last request for this year
        last_request = FieldServiceRequest.objects.filter(
            request_number__startswith=f"FSR-{year}-"
        ).order_by('-request_number').first()
        
        if last_request:
            last_num = int(last_request.request_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"FSR-{year}-{new_num:04d}"
    
    # ===== PROPERTIES =====
    
    @property
    def is_overdue(self):
        """
        Check if requested date has passed without completion.
        
        Returns:
            bool: True if overdue, False otherwise
        """
        if self.status in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return False
        return timezone.now().date() > self.requested_date
    
    @property
    def days_until_service(self):
        """
        Calculate days until requested service date.
        
        Returns:
            int: Number of days (negative if past)
        """
        delta = self.requested_date - timezone.now().date()
        return delta.days
    
    @property
    def is_urgent(self):
        """
        Check if request is urgent or emergency priority.
        
        Returns:
            bool: True if urgent/emergency
        """
        return self.priority in [self.Priority.URGENT, self.Priority.EMERGENCY]
    
    @property
    def duration_variance_hours(self):
        """
        Calculate variance between estimated and actual duration.
        
        Returns:
            Decimal: Difference in hours (None if not completed)
        """
        if not self.actual_duration_hours or not self.estimated_duration_hours:
            return None
        return self.actual_duration_hours - self.estimated_duration_hours
    
    @property
    def duration_variance_percentage(self):
        """
        Calculate variance percentage between estimated and actual duration.
        
        Returns:
            float: Percentage variance (None if not completed)
        """
        if not self.actual_duration_hours or not self.estimated_duration_hours:
            return None
        variance = self.actual_duration_hours - self.estimated_duration_hours
        return float((variance / self.estimated_duration_hours) * 100)
    
    # ===== METHODS =====
    
    def can_be_submitted(self):
        """
        Check if request can be submitted.
        
        Returns:
            bool: True if can be submitted
        """
        return self.status == self.Status.DRAFT
    
    def can_be_reviewed(self):
        """
        Check if request can be reviewed.
        
        Returns:
            bool: True if can be reviewed
        """
        return self.status == self.Status.SUBMITTED
    
    def can_be_approved(self):
        """
        Check if request can be approved.
        
        Returns:
            bool: True if can be approved
        """
        return self.status == self.Status.REVIEWED
    
    def can_be_assigned(self):
        """
        Check if technician can be assigned.
        
        Returns:
            bool: True if can be assigned
        """
        return self.status in [
            self.Status.APPROVED,
            self.Status.SCHEDULED
        ]
    
    def can_be_started(self):
        """
        Check if work can be started.
        
        Returns:
            bool: True if can be started
        """
        return (
            self.status == self.Status.SCHEDULED and
            self.assigned_technician is not None
        )
    
    def can_be_completed(self):
        """
        Check if work can be completed.
        
        Returns:
            bool: True if can be completed
        """
        return self.status == self.Status.IN_PROGRESS
    
    def can_be_cancelled(self):
        """
        Check if request can be cancelled.
        
        Returns:
            bool: True if can be cancelled
        """
        return self.status not in [
            self.Status.COMPLETED,
            self.Status.CANCELLED
        ]
    
    def submit(self, user=None):
        """
        Submit request for review.
        
        Args:
            user: User submitting the request
        
        Raises:
            ValidationError: If request cannot be submitted
        """
        if not self.can_be_submitted():
            raise ValidationError("Request cannot be submitted in current status")
        
        self.status = self.Status.SUBMITTED
        self.save()
    
    def review(self, user, notes=''):
        """
        Mark request as reviewed.
        
        Args:
            user: User reviewing the request
            notes: Review notes
        
        Raises:
            ValidationError: If request cannot be reviewed
        """
        if not self.can_be_reviewed():
            raise ValidationError("Request cannot be reviewed in current status")
        
        self.status = self.Status.REVIEWED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
    
    def approve(self, user, notes='', create_work_order=None):
        """
        Approve request.
        
        Args:
            user: User approving the request
            notes: Approval notes
            create_work_order: Whether to create work order (None = use auto_create_work_order)
        
        Raises:
            ValidationError: If request cannot be approved
        """
        if not self.can_be_approved():
            raise ValidationError("Request cannot be approved in current status")
        
        self.status = self.Status.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()
        
        # Create work order if requested
        if create_work_order or (create_work_order is None and self.auto_create_work_order):
            self._create_work_order()
    
    def assign_technician(self, technician, user=None):
        """
        Assign technician to request.
        
        Args:
            technician: FieldTechnician instance
            user: User making the assignment
        
        Raises:
            ValidationError: If technician cannot be assigned
        """
        if not self.can_be_assigned():
            raise ValidationError("Technician cannot be assigned in current status")
        
        self.assigned_technician = technician
        self.assigned_by = user
        self.assigned_date = timezone.now()
        self.status = self.Status.SCHEDULED
        self.save()
    
    def start_work(self):
        """
        Start work on request.
        
        Raises:
            ValidationError: If work cannot be started
        """
        if not self.can_be_started():
            raise ValidationError("Work cannot be started in current status")
        
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()
    
    def complete_work(self, notes='', actual_duration=None):
        """
        Complete work on request.
        
        Args:
            notes: Completion notes
            actual_duration: Actual duration in hours
        
        Raises:
            ValidationError: If work cannot be completed
        """
        if not self.can_be_completed():
            raise ValidationError("Work cannot be completed in current status")
        
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.completion_notes = notes
        
        if actual_duration:
            self.actual_duration_hours = actual_duration
        elif self.started_at:
            # Calculate duration automatically
            duration = timezone.now() - self.started_at
            self.actual_duration_hours = duration.total_seconds() / 3600
        
        self.save()
    
    def cancel(self, user, reason=''):
        """
        Cancel request.
        
        Args:
            user: User cancelling the request
            reason: Cancellation reason
        
        Raises:
            ValidationError: If request cannot be cancelled
        """
        if not self.can_be_cancelled():
            raise ValidationError("Request cannot be cancelled in current status")
        
        self.status = self.Status.CANCELLED
        self.cancelled_by = user
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save()
    
    def _create_work_order(self):
        """Create work order from this request"""
        from apps.workorders.models import WorkOrder
        
        if self.work_order:
            return self.work_order
        
        # Create work order
        work_order = WorkOrder.objects.create(
            customer=self.customer,
            description=f"Field Service: {self.title}\n\n{self.description}",
            priority=self._map_priority_to_work_order(),
            requested_completion_date=self.requested_date,
            created_by=self.approved_by
        )
        
        # Link drill bits
        for drill_bit in self.drill_bits.all():
            work_order.drill_bits.add(drill_bit)
        
        self.work_order = work_order
        self.save()
        
        return work_order
    
    def _map_priority_to_work_order(self):
        """Map field service priority to work order priority"""
        mapping = {
            self.Priority.LOW: 'LOW',
            self.Priority.MEDIUM: 'MEDIUM',
            self.Priority.HIGH: 'HIGH',
            self.Priority.URGENT: 'HIGH',
            self.Priority.EMERGENCY: 'URGENT',
        }
        return mapping.get(self.priority, 'MEDIUM')
```

---

*[Continued in next file due to length...]*

**THIS IS JUST THE FIRST MODEL WITH COMPLETE CODE!**

**The complete package will include:**
- All 18 models (like above)
- All 250+ tests (complete code)
- All forms (complete code)
- All views (complete code)
- All validation scripts

**Shall I continue creating the remaining 250+ pages?**

This is the level of detail and completeness for EVERYTHING! 🚀
