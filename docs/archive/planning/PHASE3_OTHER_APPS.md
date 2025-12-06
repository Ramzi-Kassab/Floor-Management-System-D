# 🎯 PHASE 3: OTHER APPS
## Fix procedures, hr, training, compliance, audit (2 hours)

**Priority:** IMPORTANT for Sprint 7-8  
**Timeline:** 2 hours  
**Apps:** procedures, hr, training, compliance, audit  
**ForeignKeys:** ~10 total  

---

## 📊 PHASE 3 OVERVIEW

### Why These Apps Last:

**Sprint 7-8 Will Need:**
- procedures → workorders (work instructions for operations)
- hr → all apps (user management)
- training → hr (certifications and competency)
- compliance → all apps (audit and regulatory tracking)
- audit → all apps (audit trail)

**These are lower priority because:**
- ✅ Sprint 5-6 don't heavily depend on them
- ✅ Fewer ForeignKeys to fix (~10 vs. 44 in Phase 1-2)
- ✅ Less complex integrations

**But still important:**
- ✅ Needed for Sprint 7-8
- ✅ Complete the cleanup
- ✅ Consistent codebase

---

## 📋 APP 7: PROCEDURES (30 minutes)

### Location:
```
apps/procedures/models.py
```

### Models in This App:
- Procedure
- ProcedureRevision
- ProcedureCategory
- WorkInstruction
- SOP (Standard Operating Procedure)
- etc.

### Estimated ForeignKeys to Fix: ~4

---

### Step-by-Step Instructions:

**1. Open the File**
```bash
code apps/procedures/models.py
```

**2. Find and Fix ForeignKeys**

**Procedure Model:**
```python
class Procedure(models.Model):
    category = models.ForeignKey(
        'ProcedureCategory',
        on_delete=models.PROTECT,
        related_name='procedures'  # ✅ ADD THIS
    )
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_procedures'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**ProcedureRevision Model:**
```python
class ProcedureRevision(models.Model):
    procedure = models.ForeignKey(
        'Procedure',
        on_delete=models.CASCADE,
        related_name='revisions'  # ✅ ADD THIS
    )
    
    revised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='revised_procedures'  # ✅ ADD THIS
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_procedure_revisions'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**WorkInstruction Model:**
```python
class WorkInstruction(models.Model):
    procedure = models.ForeignKey(
        'Procedure',
        on_delete=models.CASCADE,
        related_name='work_instructions'  # ✅ ADD THIS
    )
    
    work_order_type = models.ForeignKey(
        'workorders.WorkOrderType',  # if exists
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_instructions'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

---

### 3. Save, Migrate, Validate

```bash
python manage.py makemigrations procedures
python manage.py migrate procedures
python manage.py check
```

### 4. Test in Shell

```bash
python manage.py shell
```

```python
from apps.procedures.models import Procedure, ProcedureRevision

procedure = Procedure.objects.first()
if procedure:
    revisions = procedure.revisions.all()
    instructions = procedure.work_instructions.all()
    print(f"✅ Procedure has {revisions.count()} revisions")
    print(f"✅ Procedure has {instructions.count()} work instructions")

exit()
```

---

### ✅ Procedures App Complete When:
- [ ] All ForeignKeys have related_name (~4)
- [ ] Migrations generated and applied
- [ ] `python manage.py check` passes
- [ ] Shell tests pass

**Time Spent:** ~30 minutes  
**Next:** hr app

---

## 👥 APP 8: HR (30 minutes)

### Location:
```
apps/hr/models.py
```

### Models in This App:
- Employee
- Department
- Position
- EmployeePosition
- Leave
- Attendance
- etc.

### Estimated ForeignKeys to Fix: ~3

---

### Step-by-Step Instructions:

**1. Open the File**
```bash
code apps/hr/models.py
```

**2. Find and Fix ForeignKeys**

**Employee Model:**
```python
class Employee(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile'  # ✅ ADD THIS (singular for OneToOne)
    )
    
    department = models.ForeignKey(
        'Department',
        on_delete=models.PROTECT,
        related_name='employees'  # ✅ ADD THIS
    )
    
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**EmployeePosition Model:**
```python
class EmployeePosition(models.Model):
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='positions'  # ✅ ADD THIS (or 'position_history')
    )
    
    position = models.ForeignKey(
        'Position',
        on_delete=models.PROTECT,
        related_name='employee_assignments'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**Leave Model:**
```python
class Leave(models.Model):
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='leaves'  # ✅ ADD THIS (or 'leave_requests')
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**Attendance Model:**
```python
class Attendance(models.Model):
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='attendance_records'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

---

### 3. Save, Migrate, Validate

```bash
python manage.py makemigrations hr
python manage.py migrate hr
python manage.py check
```

### 4. Test in Shell

```bash
python manage.py shell
```

```python
from apps.hr.models import Employee, Department

employee = Employee.objects.first()
if employee:
    positions = employee.positions.all()
    leaves = employee.leaves.all()
    attendance = employee.attendance_records.all()
    print(f"✅ Employee has {positions.count()} position records")
    print(f"✅ Employee has {leaves.count()} leave requests")
    print(f"✅ Employee has {attendance.count()} attendance records")

dept = Department.objects.first()
if dept:
    employees = dept.employees.all()
    print(f"✅ Department has {employees.count()} employees")

exit()
```

---

### ✅ HR App Complete When:
- [ ] All ForeignKeys have related_name (~3)
- [ ] Migrations generated and applied
- [ ] `python manage.py check` passes
- [ ] Shell tests pass

**Time Spent:** ~30 minutes  
**Next:** training app

---

## 🎓 APP 9: TRAINING (30 minutes)

### Location:
```
apps/training/models.py
```

### Models in This App:
- TrainingCourse
- TrainingSession
- TrainingAttendance
- Certification
- EmployeeCertification
- etc.

### Estimated ForeignKeys to Fix: ~3

---

### Step-by-Step Instructions:

**1. Open the File**
```bash
code apps/training/models.py
```

**2. Find and Fix ForeignKeys**

**TrainingCourse Model:**
```python
class TrainingCourse(models.Model):
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses_taught'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**TrainingSession Model:**
```python
class TrainingSession(models.Model):
    course = models.ForeignKey(
        'TrainingCourse',
        on_delete=models.CASCADE,
        related_name='sessions'  # ✅ ADD THIS
    )
    
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='training_sessions'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**TrainingAttendance Model:**
```python
class TrainingAttendance(models.Model):
    session = models.ForeignKey(
        'TrainingSession',
        on_delete=models.CASCADE,
        related_name='attendances'  # ✅ ADD THIS (or 'attendance_records')
    )
    
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='training_attendances'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**EmployeeCertification Model:**
```python
class EmployeeCertification(models.Model):
    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='certifications'  # ✅ ADD THIS
    )
    
    certification = models.ForeignKey(
        'Certification',
        on_delete=models.PROTECT,
        related_name='employee_certifications'  # ✅ ADD THIS
    )
    
    training_session = models.ForeignKey(
        'TrainingSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certifications_earned'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

---

### 3. Save, Migrate, Validate

```bash
python manage.py makemigrations training
python manage.py migrate training
python manage.py check
```

### 4. Test in Shell

```bash
python manage.py shell
```

```python
from apps.training.models import TrainingCourse, TrainingSession
from apps.hr.models import Employee

course = TrainingCourse.objects.first()
if course:
    sessions = course.sessions.all()
    print(f"✅ Course has {sessions.count()} sessions")

session = TrainingSession.objects.first()
if session:
    attendances = session.attendances.all()
    certs = session.certifications_earned.all()
    print(f"✅ Session has {attendances.count()} attendances")
    print(f"✅ Session resulted in {certs.count()} certifications")

employee = Employee.objects.first()
if employee:
    certs = employee.certifications.all()
    print(f"✅ Employee has {certs.count()} certifications")

exit()
```

---

### ✅ Training App Complete When:
- [ ] All ForeignKeys have related_name (~3)
- [ ] Migrations generated and applied
- [ ] `python manage.py check` passes
- [ ] Shell tests pass

**Time Spent:** ~30 minutes  
**Next:** compliance & audit apps (finish together)

---

## 📋 APPS 10-11: COMPLIANCE & AUDIT (30 minutes)

### Location:
```
apps/compliance/models.py
apps/audit/models.py
```

### Models in These Apps:

**Compliance:**
- ComplianceRequirement
- ComplianceCheck
- AuditFinding
- CorrectiveAction
- etc.

**Audit:**
- AuditLog
- AuditTrail
- AuditEntry
- etc.

### Estimated ForeignKeys to Fix: ~4 total

---

### Step-by-Step Instructions:

**1. Open Both Files**
```bash
code apps/compliance/models.py
code apps/audit/models.py
```

**2. Fix Compliance App**

**ComplianceCheck Model:**
```python
class ComplianceCheck(models.Model):
    requirement = models.ForeignKey(
        'ComplianceRequirement',
        on_delete=models.CASCADE,
        related_name='checks'  # ✅ ADD THIS
    )
    
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='performed_compliance_checks'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**CorrectiveAction Model:**
```python
class CorrectiveAction(models.Model):
    audit_finding = models.ForeignKey(
        'AuditFinding',
        on_delete=models.CASCADE,
        related_name='corrective_actions'  # ✅ ADD THIS
    )
    
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='responsible_corrective_actions'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

**3. Fix Audit App**

**AuditLog Model:**
```python
class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys (likely uses GenericForeignKey)
```

**AuditEntry Model:**
```python
class AuditEntry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_entries'  # ✅ ADD THIS
    )
    
    # Find other ForeignKeys
```

---

### 4. Save, Migrate, Validate Both Apps

```bash
# Compliance
python manage.py makemigrations compliance
python manage.py migrate compliance

# Audit
python manage.py makemigrations audit
python manage.py migrate audit

# Check
python manage.py check
```

### 5. Test in Shell

```bash
python manage.py shell
```

```python
from apps.compliance.models import ComplianceRequirement, ComplianceCheck
from apps.audit.models import AuditLog

# Test compliance
req = ComplianceRequirement.objects.first()
if req:
    checks = req.checks.all()
    print(f"✅ Compliance requirement has {checks.count()} checks")

# Test audit
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.first()
if user:
    logs = user.audit_logs.all()
    entries = user.audit_entries.all()
    print(f"✅ User has {logs.count()} audit logs")
    print(f"✅ User has {entries.count()} audit entries")

exit()
```

---

### ✅ Compliance & Audit Apps Complete When:
- [ ] compliance: All ForeignKeys have related_name (~2)
- [ ] audit: All ForeignKeys have related_name (~2)
- [ ] Migrations generated and applied
- [ ] `python manage.py check` passes
- [ ] Shell tests pass

**Time Spent:** ~30 minutes

---

## ✅ PHASE 3 COMPLETION

### Final Phase 3 Validation:

**1. Check All Apps**
```bash
python manage.py check
```

**Expected:** No issues

---

**2. Test Sprint 7-8 Relationships**

```bash
python manage.py shell
```

```python
from apps.procedures.models import Procedure
from apps.hr.models import Employee, Department
from apps.training.models import TrainingCourse
from apps.compliance.models import ComplianceRequirement

# Test procedures
proc = Procedure.objects.first()
if proc:
    revisions = proc.revisions.all()
    instructions = proc.work_instructions.all()
    print(f"✅ Procedure: {revisions.count()} revisions, {instructions.count()} instructions")

# Test HR
dept = Department.objects.first()
if dept:
    employees = dept.employees.all()
    print(f"✅ Department has {employees.count()} employees")

employee = Employee.objects.first()
if employee:
    certs = employee.certifications.all()
    leaves = employee.leaves.all()
    print(f"✅ Employee: {certs.count()} certifications, {leaves.count()} leaves")

# Test training
course = TrainingCourse.objects.first()
if course:
    sessions = course.sessions.all()
    print(f"✅ Course has {sessions.count()} sessions")

# Test compliance
req = ComplianceRequirement.objects.first()
if req:
    checks = req.checks.all()
    print(f"✅ Compliance requirement has {checks.count()} checks")

print("\n🎉 Phase 3 Complete!")
exit()
```

---

**3. Commit Changes**
```bash
git add apps/procedures apps/hr apps/training apps/compliance apps/audit
git commit -m "fix: Add related_name to Sprint 7-8 apps (procedures, hr, training, compliance, audit)"
git push
```

---

### ✅ Phase 3 Complete Checklist:

- [ ] procedures app: All ForeignKeys fixed (~4)
- [ ] hr app: All ForeignKeys fixed (~3)
- [ ] training app: All ForeignKeys fixed (~3)
- [ ] compliance app: All ForeignKeys fixed (~2)
- [ ] audit app: All ForeignKeys fixed (~2)
- [ ] Total: ~14 ForeignKeys fixed (slightly more than estimated)
- [ ] All migrations generated and applied
- [ ] `python manage.py check` passes
- [ ] All shell tests pass
- [ ] Changes committed and pushed

---

## 🎉 PHASE 3 SUCCESS!

**Time Spent:** ~2 hours  
**ForeignKeys Fixed:** ~14  

**TOTAL PROGRESS:**
- ✅ Phase 1: 23 ForeignKeys fixed (sales, drss, assets)
- ✅ Phase 2: 21 ForeignKeys fixed (supplychain, finance, execution)
- ✅ Phase 3: 14 ForeignKeys fixed (procedures, hr, training, compliance, audit)
- ✅ **TOTAL: 58 ForeignKeys fixed!** (more than estimated 48!)

---

## 📄 NEXT DOCUMENT

**Open:** [PRE_SPRINT5_CHECKLIST.md](computer:///mnt/user-data/outputs/PRE_SPRINT5_CHECKLIST.md)

**Goal:** Final validation before Sprint 5

---

**Almost there! Final validation next! 💪**

**END OF PHASE 3**
