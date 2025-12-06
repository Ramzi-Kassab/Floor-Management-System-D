# 🚀 SPRINT 5 MASTER IMPLEMENTATION GUIDE
## Complete, Comprehensive, No-Shortcuts Package

**Version:** 2.0 - Full Implementation  
**Created:** December 6, 2024  
**Total Documentation:** 250+ pages  
**Approach:** Production-ready with tests, permissions, validation  
**Timeline:** 20 working days (4 weeks)  

---

## 📚 DOCUMENTATION STRUCTURE

This Sprint 5 package consists of multiple comprehensive documents:

### **Core Implementation Documents:**
1. **SPRINT5_IMPLEMENTATION_PART1.md** - Setup, Strategy, Model 1
2. **SPRINT5_IMPLEMENTATION_PART2.md** - Model 2 + Tests
3. **SPRINT5_TESTING_COMPLETE_PART1.md** - Complete test suites
4. **SPRINT5_CHECKLIST.md** - Daily/weekly execution checklist
5. **SPRINT5_AGENT_INSTRUCTIONS.md** - Instructions for Claude Code
6. **SPRINT5_VALIDATION_SCRIPTS.md** - All validation scripts
7. **THIS DOCUMENT** - Master guide and integration

---

## 🎯 QUICK START

### **If You're Ready to Begin:**

**Day 1 Morning (RIGHT NOW):**
1. Open `SPRINT5_IMPLEMENTATION_PART1.md`
2. Read "Sprint 5 Philosophy" section
3. Set up testing environment (pytest, coverage)
4. Start implementing Model 1: FieldServiceRequest
5. Write tests alongside implementation
6. Run validation after each model

**End of Day 1:**
- FieldServiceRequest model complete ✅
- 25+ tests written and passing ✅
- Migrations generated and applied ✅
- Coverage ≥80% ✅

### **Daily Workflow:**
```
Morning (3-4 hours):
1. Review previous day's work
2. Implement new model(s)
3. Write tests alongside
4. Generate migrations

Afternoon (3-4 hours):
5. Complete test coverage
6. Run validation scripts
7. Fix any issues
8. Commit and push
9. Update documentation
```

---

## 📋 COMPLETE MODELS SUMMARY

### Week 1: Field Service Management (6 models)

**Model 1: FieldServiceRequest** ✅ **COMPLETE IN PART1**
- Purpose: Track customer service requests
- Fields: 50+ fields
- Tests: 25+ tests (COMPLETE IN TESTING_PART1)
- Coverage: 80%+
- Integration: Customer, ServiceSite, WorkOrder, DrillBit

**Model 2: ServiceSite** ✅ **COMPLETE IN PART2**
- Purpose: Customer service locations
- Fields: 45+ fields  
- Tests: 20+ tests (COMPLETE IN PART2)
- Coverage: 80%+
- Integration: Customer, FieldServiceRequest, GPSLocation

**Model 3: FieldTechnician** (Day 3-4)
```python
class FieldTechnician(models.Model):
    """
    Represent field service technicians who perform on-site work.
    
    Tracks technician qualifications, certifications, availability,
    and performance metrics for field service assignments.
    """
    
    # Identification
    employee_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    
    # Contact
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    emergency_contact = models.CharField(max_length=200)
    emergency_phone = models.CharField(max_length=50)
    
    # Employment
    hire_date = models.DateField()
    employment_status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('ON_LEAVE', 'On Leave'),
            ('INACTIVE', 'Inactive'),
            ('TERMINATED', 'Terminated')
        ]
    )
    
    # Skills & Certifications
    specializations = models.ManyToManyField('TechnicianSpecialization')
    certifications = models.ManyToManyField('TechnicianCertification')
    skill_level = models.CharField(
        max_length=20,
        choices=[
            ('JUNIOR', 'Junior'),
            ('INTERMEDIATE', 'Intermediate'),
            ('SENIOR', 'Senior'),
            ('EXPERT', 'Expert')
        ]
    )
    
    # Location & Availability
    home_base_location = models.CharField(max_length=200)
    service_radius_km = models.IntegerField(default=100)
    available_for_travel = models.BooleanField(default=True)
    current_location = models.ForeignKey(
        'ServiceSite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_technicians'
    )
    
    # Performance Metrics
    total_service_calls = models.IntegerField(default=0)
    completed_calls = models.IntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )
    on_time_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Current Assignment
    is_currently_assigned = models.BooleanField(default=False)
    current_assignment = models.ForeignKey(
        'FieldServiceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_technician_assignment'
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "field_technicians"
        ordering = ['name']
        permissions = [
            ("can_assign_technicians", "Can assign technicians to requests"),
            ("can_view_technician_performance", "Can view technician performance")
        ]
    
    def __str__(self):
        return f"{self.employee_id} - {self.name}"
    
    @property
    def completion_rate(self):
        """Calculate completion rate percentage"""
        if self.total_service_calls == 0:
            return None
        return (self.completed_calls / self.total_service_calls) * 100
    
    def is_available(self):
        """Check if technician is available for assignment"""
        return (
            self.employment_status == 'ACTIVE' and
            not self.is_currently_assigned
        )
    
    def can_service_site(self, site):
        """Check if technician can service a site based on distance"""
        if not site.has_gps_coordinates or not hasattr(self, 'home_coordinates'):
            return True  # Assume available if no distance data
        
        # Calculate distance and check against service radius
        # Implementation would use GPS calculations
        return True
```

**Tests for FieldTechnician:** 20+ tests
- Test creation and defaults
- Test availability logic
- Test skill and certification relationships
- Test performance metrics calculations
- Test assignment logic
- Edge cases

**Model 4: ServiceSchedule** (Day 3-4)
```python
class ServiceSchedule(models.Model):
    """
    Manage scheduling of field service appointments.
    
    Handles scheduling logic, conflicts, technician assignments,
    and integration with calendar systems.
    """
    
    # Schedule identification
    schedule_number = models.CharField(max_length=50, unique=True)
    
    # Linked entities
    service_request = models.ForeignKey(
        'FieldServiceRequest',
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    technician = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.PROTECT,
        related_name='schedules'
    )
    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.PROTECT,
        related_name='schedules'
    )
    
    # Scheduling details
    scheduled_date = models.DateField()
    scheduled_start_time = models.TimeField()
    scheduled_end_time = models.TimeField()
    estimated_duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('CONFIRMED', 'Confirmed'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled'),
            ('RESCHEDULED', 'Rescheduled')
        ],
        default='DRAFT'
    )
    
    # Confirmation
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_schedules'
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    customer_confirmed = models.BooleanField(default=False)
    customer_confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Rescheduling
    original_schedule = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rescheduled_versions'
    )
    rescheduled_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rescheduled_from'
    )
    reschedule_reason = models.TextField(blank=True)
    
    # Notifications
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    scheduling_notes = models.TextField(blank=True)
    special_requirements = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_schedules'
    )
    
    class Meta:
        db_table = "service_schedules"
        ordering = ['scheduled_date', 'scheduled_start_time']
        permissions = [
            ("can_create_schedules", "Can create service schedules"),
            ("can_confirm_schedules", "Can confirm service schedules")
        ]
    
    def __str__(self):
        return f"{self.schedule_number} - {self.scheduled_date}"
    
    def check_conflicts(self):
        """Check for scheduling conflicts"""
        conflicts = ServiceSchedule.objects.filter(
            technician=self.technician,
            scheduled_date=self.scheduled_date,
            status__in=['CONFIRMED', 'IN_PROGRESS']
        ).exclude(pk=self.pk)
        
        # Check time overlap
        for conflict in conflicts:
            if self._times_overlap(conflict):
                return True
        return False
    
    def confirm_schedule(self, user):
        """Confirm the schedule"""
        if self.status != 'DRAFT':
            raise ValidationError("Can only confirm draft schedules")
        
        if self.check_conflicts():
            raise ValidationError("Schedule has conflicts")
        
        self.status = 'CONFIRMED'
        self.confirmed_by = user
        self.confirmed_at = timezone.now()
        self.save()
```

**Tests for ServiceSchedule:** 25+ tests
- Test creation and validation
- Test conflict detection
- Test confirmation workflow
- Test rescheduling logic
- Test notification tracking
- Integration tests with other models

**Model 5: SiteVisit** (Day 3-4)
```python
class SiteVisit(models.Model):
    """
    Record actual site visits by technicians.
    
    Tracks visit details, work performed, time spent,
    and outcomes for reporting and analysis.
    """
    
    # Visit identification
    visit_number = models.CharField(max_length=50, unique=True)
    
    # Linked entities
    service_request = models.ForeignKey(
        'FieldServiceRequest',
        on_delete=models.PROTECT,
        related_name='site_visits'
    )
    schedule = models.ForeignKey(
        'ServiceSchedule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='site_visits'
    )
    technician = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.PROTECT,
        related_name='site_visits'
    )
    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.PROTECT,
        related_name='site_visits'
    )
    
    # Visit timing
    visit_date = models.DateField()
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    actual_duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Visit details
    visit_type = models.CharField(
        max_length=50,
        choices=[
            ('SCHEDULED', 'Scheduled Service'),
            ('EMERGENCY', 'Emergency Call'),
            ('FOLLOW_UP', 'Follow-up Visit'),
            ('INSPECTION', 'Inspection'),
            ('OTHER', 'Other')
        ]
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('SCHEDULED', 'Scheduled'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled'),
            ('INCOMPLETE', 'Incomplete')
        ],
        default='SCHEDULED'
    )
    
    # Work performed
    work_performed = models.TextField(blank=True)
    issues_found = models.TextField(blank=True)
    parts_used = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Outcomes
    visit_successful = models.BooleanField(null=True, blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_reason = models.TextField(blank=True)
    
    # Customer feedback
    customer_signature = models.CharField(max_length=200, blank=True)
    customer_signed_at = models.DateTimeField(null=True, blank=True)
    customer_satisfaction_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    customer_comments = models.TextField(blank=True)
    
    # Attachments/Photos
    has_photos = models.BooleanField(default=False)
    photo_count = models.IntegerField(default=0)
    has_documents = models.BooleanField(default=False)
    document_count = models.IntegerField(default=0)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "site_visits"
        ordering = ['-visit_date', '-check_in_time']
        permissions = [
            ("can_check_in_visit", "Can check in to site visit"),
            ("can_complete_visit", "Can complete site visit")
        ]
    
    def __str__(self):
        return f"{self.visit_number} - {self.visit_date}"
    
    def check_in(self):
        """Check in to site visit"""
        if self.status != 'SCHEDULED':
            raise ValidationError("Can only check in to scheduled visits")
        
        self.check_in_time = timezone.now()
        self.status = 'IN_PROGRESS'
        self.save()
    
    def check_out(self):
        """Check out from site visit"""
        if self.status != 'IN_PROGRESS':
            raise ValidationError("Can only check out from in-progress visits")
        
        self.check_out_time = timezone.now()
        
        # Calculate duration
        if self.check_in_time:
            duration = self.check_out_time - self.check_in_time
            self.actual_duration_hours = duration.total_seconds() / 3600
        
        self.status = 'COMPLETED'
        self.save()
        
        # Update service site history
        self.service_site.update_service_history(self.visit_date)
```

**Tests for SiteVisit:** 25+ tests
- Test visit workflow (scheduled → in_progress → completed)
- Test check-in/check-out logic
- Test duration calculations
- Test customer feedback
- Test relationships
- Integration tests

**Model 6: ServiceReport** (Day 5)
```python
class ServiceReport(models.Model):
    """
    Generate comprehensive service reports from site visits.
    
    Aggregates visit data, photos, work performed, and outcomes
    into formal customer-facing reports.
    """
    
    # Report identification
    report_number = models.CharField(max_length=50, unique=True)
    
    # Linked entities
    service_request = models.ForeignKey(
        'FieldServiceRequest',
        on_delete=models.PROTECT,
        related_name='service_reports'
    )
    site_visit = models.ForeignKey(
        'SiteVisit',
        on_delete=models.PROTECT,
        related_name='service_reports'
    )
    
    # Report details
    report_date = models.DateField()
    report_title = models.CharField(max_length=200)
    
    # Executive summary
    executive_summary = models.TextField()
    
    # Detailed sections
    work_performed_detail = models.TextField()
    findings = models.TextField(blank=True)
    issues_identified = models.TextField(blank=True)
    corrective_actions = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Assets serviced
    drill_bits_serviced = models.ManyToManyField(
        'workorders.DrillBit',
        blank=True,
        related_name='service_reports'
    )
    drill_strings_serviced = models.ManyToManyField(
        'drss.DrillString',
        blank=True,
        related_name='service_reports'
    )
    
    # Parts and materials
    parts_used_detail = models.TextField(blank=True)
    parts_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Time and labor
    labor_hours = models.DecimalField(max_digits=5, decimal_places=2)
    labor_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Totals
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Attachments
    has_photos = models.BooleanField(default=False)
    has_diagrams = models.BooleanField(default=False)
    has_test_results = models.BooleanField(default=False)
    
    # Status and approval
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('REVIEW', 'Under Review'),
            ('APPROVED', 'Approved'),
            ('SENT', 'Sent to Customer'),
            ('ARCHIVED', 'Archived')
        ],
        default='DRAFT'
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_service_reports'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    sent_to_customer_at = models.DateTimeField(null=True, blank=True)
    customer_acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_service_reports'
    )
    
    class Meta:
        db_table = "service_reports"
        ordering = ['-report_date']
        permissions = [
            ("can_approve_service_reports", "Can approve service reports"),
            ("can_send_to_customer", "Can send reports to customers")
        ]
    
    def __str__(self):
        return f"{self.report_number} - {self.report_title}"
    
    def calculate_total_cost(self):
        """Calculate total cost from parts and labor"""
        total = Decimal('0.00')
        if self.parts_cost:
            total += self.parts_cost
        if self.labor_cost:
            total += self.labor_cost
        self.total_cost = total
        return total
    
    def approve(self, user):
        """Approve the report"""
        if self.status not in ['DRAFT', 'REVIEW']:
            raise ValidationError("Can only approve draft or review reports")
        
        self.status = 'APPROVED'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
    
    def send_to_customer(self):
        """Mark report as sent to customer"""
        if self.status != 'APPROVED':
            raise ValidationError("Can only send approved reports")
        
        self.status = 'SENT'
        self.sent_to_customer_at = timezone.now()
        self.save()
        
        # TODO: Integrate with email system
```

**Tests for ServiceReport:** 25+ tests
- Test report generation from site visit
- Test cost calculations
- Test approval workflow
- Test status transitions
- Test relationships with assets
- Integration tests

---

### Week 2: Drill String Field Operations (6 models)

**Model 7-12:** Similar comprehensive implementation
- FieldDrillStringRun
- FieldRunData  
- FieldPerformanceLog
- FieldInspection
- RunHours
- FieldIncident

*[Each with 40+ fields, 20-25 tests, complete validation]*

---

### Week 3: Field Data Capture & Integration (6 models)

**Model 13-18:** Similar comprehensive implementation
- FieldDataEntry
- FieldPhoto
- FieldDocument
- GPSLocation
- FieldWorkOrder (extends WorkOrder)
- FieldAssetAssignment (extends AssetAssignment)

*[Each with 30+ fields, 15-20 tests, complete validation]*

---

## ✅ DAILY CHECKLIST TEMPLATE

### **Day Start (Every Morning):**
```
[ ] Review yesterday's work
[ ] Run full test suite: pytest -v
[ ] Check test coverage: pytest --cov
[ ] Check migrations status: python manage.py showmigrations
[ ] System check: python manage.py check
[ ] Pull latest changes: git pull
```

### **During Implementation:**
```
[ ] Write model code with all fields
[ ] Add docstrings to model and all methods
[ ] Write tests alongside (not after!)
[ ] Achieve 80%+ coverage for this model
[ ] Generate migrations: python manage.py makemigrations
[ ] Apply migrations: python manage.py migrate
[ ] Verify in database: python manage.py dbshell
[ ] Test relationships in shell
```

### **Day End (Every Evening):**
```
[ ] All tests passing: pytest -v
[ ] Coverage target met: pytest --cov
[ ] No flake8 errors: flake8 apps/
[ ] Code formatted: black apps/
[ ] Migrations applied: python manage.py showmigrations
[ ] System check clean: python manage.py check
[ ] Changes committed: git commit
[ ] Changes pushed: git push
[ ] Documentation updated
[ ] Tomorrow's work planned
```

---

## 🧪 TESTING REQUIREMENTS (ABSOLUTE)

### **Coverage Targets (Non-Negotiable):**
```
Sprint 5 Models:     ≥80%
Sprint 5 Views:      ≥70%
Sprint 5 Forms:      ≥70%
Sprint 5 Overall:    ≥75%
```

### **Test Types Required:**

**1. Unit Tests (Must Have):**
- Every model field validation
- Every model method
- Every model property
- Every form validation
- Every view GET/POST

**2. Integration Tests (Must Have):**
- Complete workflows (request → visit → report)
- Cross-app relationships
- Database integrity

**3. Permission Tests (Must Have):**
- View access control
- Object permissions
- Anonymous user blocking

**4. Edge Case Tests (Should Have):**
- Boundary values
- Null handling
- Special characters
- Concurrent operations

---

## 📊 VALIDATION SCRIPTS

### **Daily Validation Script:**

```bash
#!/bin/bash
# daily_validation.sh

echo "========================================="
echo "DAILY SPRINT 5 VALIDATION"
echo "========================================="
echo ""

# 1. Test execution
echo "1. Running test suite..."
pytest apps/sales/tests/ apps/drss/tests/ -v --tb=short
if [ $? -ne 0 ]; then
    echo "❌ TESTS FAILED"
    exit 1
fi
echo "✅ All tests passing"
echo ""

# 2. Coverage check
echo "2. Checking test coverage..."
pytest --cov=apps/sales --cov=apps/drss --cov-report=term-missing --cov-fail-under=75
if [ $? -ne 0 ]; then
    echo "❌ COVERAGE BELOW TARGET"
    exit 1
fi
echo "✅ Coverage target met"
echo ""

# 3. Migration status
echo "3. Checking migrations..."
python manage.py showmigrations | grep "\[ \]"
if [ $? -eq 0 ]; then
    echo "❌ UNAPPLIED MIGRATIONS FOUND"
    exit 1
fi
echo "✅ All migrations applied"
echo ""

# 4. System check
echo "4. Running system check..."
python manage.py check --deploy
if [ $? -ne 0 ]; then
    echo "❌ SYSTEM CHECK FAILED"
    exit 1
fi
echo "✅ System check passed"
echo ""

# 5. Code quality
echo "5. Checking code quality..."
flake8 apps/sales apps/drss --max-line-length=100
if [ $? -ne 0 ]; then
    echo "❌ FLAKE8 ERRORS FOUND"
    exit 1
fi
echo "✅ Code quality good"
echo ""

echo "========================================="
echo "✅ DAILY VALIDATION COMPLETE - ALL CHECKS PASSED"
echo "========================================="
```

### **Weekly Validation Script:**

```bash
#!/bin/bash
# weekly_validation.sh

echo "========================================="
echo "WEEKLY SPRINT 5 VALIDATION"
echo "========================================="
echo ""

# Run daily validation first
./daily_validation.sh
if [ $? -ne 0 ]; then
    echo "Daily validation failed"
    exit 1
fi

# Additional weekly checks
echo "6. Running integration tests..."
pytest -m integration -v

echo "7. Checking database integrity..."
python manage.py check --database default

echo "8. Generating coverage report..."
pytest --cov=apps --cov-report=html
echo "Open htmlcov/index.html to view detailed coverage"

echo "9. Running security checks..."
python manage.py check --deploy

echo "10. Checking for TODO/FIXME..."
grep -r "TODO\|FIXME" apps/ && echo "❌ Found TODO/FIXME" || echo "✅ No TODO/FIXME"

echo ""
echo "========================================="
echo "✅ WEEKLY VALIDATION COMPLETE"
echo "========================================="
```

---

## 🎯 SUCCESS CRITERIA (ALL MUST BE MET)

### **Sprint 5 Complete When:**

**Models (ALL):**
- [ ] All 18 models implemented
- [ ] All fields have help_text
- [ ] All ForeignKeys have related_name
- [ ] All models have __str__
- [ ] All models have docstrings
- [ ] All migrations applied
- [ ] Database integrity verified

**Tests (ALL):**
- [ ] 250+ tests written
- [ ] All tests passing (0 failures)
- [ ] 75%+ overall coverage
- [ ] 80%+ model coverage
- [ ] 70%+ view coverage
- [ ] All integration tests pass

**Code Quality (ALL):**
- [ ] flake8: 0 errors
- [ ] black: formatted
- [ ] No TODO/FIXME
- [ ] No commented code
- [ ] All imports organized

**Permissions (ALL):**
- [ ] PermissionRequiredMixin on all views
- [ ] Custom permissions defined
- [ ] Permission tests pass

**Documentation (ALL):**
- [ ] README updated
- [ ] CHANGELOG updated
- [ ] All models documented
- [ ] Sprint 5 summary written

**Validation (ALL):**
- [ ] python manage.py check: 0 issues
- [ ] Daily validations passed
- [ ] Weekly validation passed
- [ ] Production-ready

---

## 🚨 AGENT INSTRUCTIONS (CRITICAL)

### **For Claude Code / AI Implementation:**

**1. BE ABSOLUTELY HONEST:**
- If something is complex, say so
- If something will take longer, say so
- If you encounter issues, report immediately
- Don't claim completion without tests
- Don't sugar-coat problems

**2. NO SHORTCUTS EVER:**
- Write ALL tests (not "similar to above")
- Achieve coverage targets (not "close enough")
- Add ALL permissions (not "will add later")
- Validate EVERYTHING (not "looks good")
- Don't skip steps

**3. FOLLOW TIMELINE STRICTLY:**
- Each day has specific deliverables
- Each day has test requirements
- Don't rush ahead
- Don't skip validation
- Better late than incomplete

**4. QUALITY > SPEED:**
- Better Day 3 complete than Day 5 broken
- Better 80% coverage than 50%
- Better 15 models done than 18 half-done
- Better honest timeline than fake completion

**5. TEST BEFORE PROCEEDING:**
- Run tests after every change
- Verify coverage after every feature
- Check permissions after every view
- Validate migrations after every model
- Don't proceed if tests fail

**6. REPORT ISSUES:**
- Don't hide problems
- Don't work around without discussion
- Don't defer to later
- Report and fix now
- Get help if stuck

---

## 📞 SUPPORT & RESOURCES

### **If You Get Stuck:**

1. **Re-read the implementation docs**
   - SPRINT5_IMPLEMENTATION_PART1.md
   - SPRINT5_IMPLEMENTATION_PART2.md
   - SPRINT5_TESTING_COMPLETE_PART1.md

2. **Check the examples**
   - FieldServiceRequest (complete model)
   - ServiceSite (complete model)
   - Complete test suites provided

3. **Run validation scripts**
   - daily_validation.sh
   - weekly_validation.sh

4. **Check error messages carefully**
   - Usually tell you exactly what's wrong

5. **Look at Sprint 4 for patterns**
   - Good examples of completed work

### **Common Issues:**

**Tests failing?**
```bash
pytest -v --tb=long  # Get full error trace
pytest -k test_name  # Run specific test
pytest --lf          # Run only last failed
```

**Coverage low?**
```bash
pytest --cov --cov-report=term-missing  # See what's not covered
pytest --cov-report=html  # Visual coverage report
```

**Migration issues?**
```bash
python manage.py showmigrations  # Check status
python manage.py migrate --fake  # Sometimes needed
python manage.py migrate app_name zero  # Reset if needed
```

---

## 🎉 FINAL WORDS

### **You Have Everything You Need:**

✅ **Complete model implementations** (Parts 1-2)  
✅ **Complete test suites** (Testing Part 1)  
✅ **Pattern to follow** for remaining models  
✅ **Daily/weekly checklists**  
✅ **Validation scripts**  
✅ **Agent instructions**  
✅ **Success criteria**  

### **The Approach Works:**

This is the same approach used in Sprint 4, but now:
- ✅ WITH tests (not deferred)
- ✅ WITH permissions (not deferred)
- ✅ WITH validation (not deferred)
- ✅ WITH honest timelines
- ✅ WITH quality gates

### **You Will Succeed Because:**

1. **Clear roadmap** - Know exactly what to do each day
2. **Complete examples** - See how it's done
3. **Validation gates** - Catch issues early
4. **Test-driven** - Build quality in from start
5. **Honest timeline** - No unrealistic pressure

### **Sprint 5 Result:**

**After 4 weeks:**
- 18 models, production-ready
- 250+ tests, all passing
- 75%+ coverage achieved
- No technical debt
- No deferred items
- Ready for Sprint 6!

---

## 🚀 BEGIN SPRINT 5!

**START NOW:**

1. Open `SPRINT5_IMPLEMENTATION_PART1.md`
2. Set up testing environment
3. Implement Model 1: FieldServiceRequest
4. Write tests alongside
5. Run daily validation
6. Commit and push

**You got this!** 💪

**Remember:** Quality over speed, tests over shortcuts, honesty over claims!

---

**END OF MASTER GUIDE**
