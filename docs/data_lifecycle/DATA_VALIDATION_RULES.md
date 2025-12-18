# Data Validation Rules
## Floor Management System - Comprehensive Validation Matrix

**Version:** 1.0
**Last Updated:** December 2024

---

## Table of Contents
1. [Validation Architecture](#1-validation-architecture)
2. [Field-Level Validation](#2-field-level-validation)
3. [Form-Level Validation](#3-form-level-validation)
4. [Business Logic Validation](#4-business-logic-validation)
5. [Database Constraints](#5-database-constraints)
6. [Workflow Rules](#6-workflow-rules)
7. [Error Messages](#7-error-messages)
8. [Edge Cases](#8-edge-cases)

---

## 1. Validation Architecture

### 1.1 Validation Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VALIDATION PYRAMID                                  │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │  LAYER 5        │  Workflow Rules
                    │  Business       │  - Approval requirements
                    │  Process        │  - State transitions
                    │                 │  - Authority checks
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  LAYER 4        │  Database Constraints
                    │  Data           │  - Unique constraints
                    │  Integrity      │  - Foreign keys
                    │                 │  - Check constraints
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │  LAYER 3                    │  Business Logic
              │  View/Model Methods         │  - Cross-field validation
              │                             │  - Date range checks
              │                             │  - Permission checks
              └──────────────┬──────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │  LAYER 2                                │  Form Validation
        │  Form Clean Methods                     │  - Required fields
        │                                         │  - Format validation
        │                                         │  - Custom clean
        └────────────────────┬────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────┐
│  LAYER 1                                                │  Field Validation
│  Model Field Definitions                                │  - max_length
│                                                         │  - choices
│                                                         │  - null/blank
│                                                         │  - validators
└─────────────────────────────────────────────────────────┘
```

### 1.2 Validation Timing

| Layer | When Executed | Fail Behavior |
|-------|--------------|---------------|
| Layer 1 | Model instantiation | ValidationError |
| Layer 2 | Form.is_valid() | Form errors displayed |
| Layer 3 | View.form_valid() / Model.save() | Exception or redirect |
| Layer 4 | Database commit | IntegrityError |
| Layer 5 | Business process checkpoints | Workflow blocked |

---

## 2. Field-Level Validation

### 2.1 DrillBit Model

| Field | Type | Constraints | Validation Rule |
|-------|------|-------------|-----------------|
| `serial_number` | CharField | max_length=50, unique | Required, alphanumeric with dashes |
| `bit_type` | CharField | choices=[FC, RC] | Must be valid choice |
| `status` | CharField | choices=10 options | Must be valid choice |
| `physical_status` | CharField | choices=5 options | Must be valid choice |
| `accounting_status` | CharField | choices=5 options | Must be valid choice |
| `total_footage` | DecimalField | max_digits=12, decimal_places=2 | >= 0 |
| `total_hours` | DecimalField | max_digits=10, decimal_places=2 | >= 0 |
| `revision_number` | PositiveIntegerField | default=0 | >= 0 |
| `total_repairs` | PositiveIntegerField | default=0 | >= 0 |
| `original_cost` | DecimalField | max_digits=12, decimal_places=2 | >= 0, nullable |
| `current_book_value` | DecimalField | max_digits=12, decimal_places=2 | >= 0, nullable |
| `customer` | ForeignKey | SET_NULL, null=True | Must exist if provided |
| `rig` | ForeignKey | SET_NULL, null=True | Must exist if provided |

### 2.2 WorkOrder Model

| Field | Type | Constraints | Validation Rule |
|-------|------|-------------|-----------------|
| `wo_number` | CharField | max_length=30, unique | Required, auto-generated format: WO-YYYY-NNNNN |
| `wo_type` | CharField | choices=7 options | Required, valid choice |
| `status` | CharField | choices=10 options | Required, default=DRAFT |
| `priority` | CharField | choices=5 options | Required, default=NORMAL |
| `drill_bit` | ForeignKey | SET_NULL, null=True | Must exist if provided |
| `customer` | ForeignKey | SET_NULL, null=True | Must exist if provided |
| `estimated_hours` | DecimalField | max_digits=8, decimal_places=2 | > 0 if provided |
| `actual_hours` | DecimalField | max_digits=8, decimal_places=2 | >= 0 |
| `estimated_cost` | DecimalField | max_digits=12, decimal_places=2 | >= 0 |
| `actual_cost` | DecimalField | max_digits=12, decimal_places=2 | >= 0 |
| `planned_start` | DateTimeField | nullable | If provided, <= planned_end |
| `planned_end` | DateTimeField | nullable | If provided, >= planned_start |
| `actual_start` | DateTimeField | nullable | If provided, <= actual_end |
| `actual_end` | DateTimeField | nullable | If provided, >= actual_start |

### 2.3 SalesOrder Model

| Field | Type | Constraints | Validation Rule |
|-------|------|-------------|-----------------|
| `so_number` | CharField | max_length=30, unique | Required, format: SO-YYYY-NNNNN |
| `customer` | ForeignKey | CASCADE | Required, must exist |
| `status` | CharField | choices=7 options | Required, default=DRAFT |
| `order_date` | DateField | | Required, <= today |
| `required_date` | DateField | nullable | If provided, >= order_date |
| `promised_date` | DateField | nullable | If provided, >= order_date |
| `subtotal` | DecimalField | max_digits=14, decimal_places=2 | >= 0 |
| `tax_amount` | DecimalField | max_digits=12, decimal_places=2 | >= 0 |
| `total_amount` | DecimalField | max_digits=14, decimal_places=2 | = subtotal + tax_amount |
| `credit_approved` | BooleanField | default=False | Required for status > DRAFT |

### 2.4 Employee Model

| Field | Type | Constraints | Validation Rule |
|-------|------|-------------|-----------------|
| `employee_number` | CharField | max_length=20, unique | Required |
| `badge_number` | CharField | max_length=20, unique, nullable | Unique if provided |
| `date_of_birth` | DateField | nullable | < today - 16 years |
| `national_id` | CharField | max_length=50, nullable | Format per country |
| `email` | EmailField | | Valid email format |
| `phone` | CharField | max_length=20, nullable | Valid phone format |
| `hire_date` | DateField | | Required, <= today |
| `termination_date` | DateField | nullable | > hire_date |
| `pay_rate` | DecimalField | max_digits=10, decimal_places=2 | > 0 |
| `annual_leave_days` | PositiveIntegerField | default=21 | >= 0 |

### 2.5 NCR Model

| Field | Type | Constraints | Validation Rule |
|-------|------|-------------|-----------------|
| `ncr_number` | CharField | max_length=30, unique | Auto-generated: NCR-YYYY-NNNNN |
| `title` | CharField | max_length=200 | Required, min 10 chars |
| `severity` | CharField | choices=3 options | Required |
| `status` | CharField | choices=7 options | Required, default=OPEN |
| `description` | TextField | | Required, min 50 chars |
| `detected_at` | DateTimeField | | Required, <= now |
| `detected_by` | ForeignKey | SET_NULL | Required |
| `root_cause` | TextField | nullable | Required for status >= INVESTIGATING |
| `disposition` | CharField | choices=6 options | Required for status >= PENDING_DISPOSITION |
| `estimated_cost` | DecimalField | | >= 0 |
| `actual_cost` | DecimalField | | >= 0, set on closure |

---

## 3. Form-Level Validation

### 3.1 WorkOrder Form Validation

```python
class WorkOrderForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()

        # Date range validation
        planned_start = cleaned_data.get('planned_start')
        planned_end = cleaned_data.get('planned_end')
        if planned_start and planned_end:
            if planned_start > planned_end:
                raise ValidationError({
                    'planned_end': 'Planned end must be after planned start'
                })

        # Drill bit availability check
        drill_bit = cleaned_data.get('drill_bit')
        if drill_bit:
            if drill_bit.status not in ['IN_STOCK', 'RETURNED']:
                raise ValidationError({
                    'drill_bit': f'Drill bit is not available (current status: {drill_bit.status})'
                })

        # Cost estimation required for release
        status = cleaned_data.get('status')
        estimated_cost = cleaned_data.get('estimated_cost')
        if status in ['RELEASED', 'IN_PROGRESS'] and not estimated_cost:
            raise ValidationError({
                'estimated_cost': 'Cost estimate required before releasing work order'
            })

        return cleaned_data
```

### 3.2 SalesOrder Form Validation

```python
class SalesOrderForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()

        customer = cleaned_data.get('customer')
        total_amount = cleaned_data.get('total_amount', 0)

        # Customer credit check
        if customer and total_amount:
            if not customer.is_active:
                raise ValidationError({
                    'customer': 'Customer account is inactive'
                })

            outstanding = customer.get_outstanding_balance()
            if outstanding + total_amount > customer.credit_limit:
                raise ValidationError({
                    'customer': f'Order exceeds credit limit. '
                               f'Available: ${customer.credit_limit - outstanding:.2f}'
                })

        # Date validation
        order_date = cleaned_data.get('order_date')
        required_date = cleaned_data.get('required_date')
        if order_date and required_date:
            if required_date < order_date:
                raise ValidationError({
                    'required_date': 'Required date cannot be before order date'
                })

            # Minimum lead time check
            min_lead_days = 3
            if (required_date - order_date).days < min_lead_days:
                self.add_warning('required_date',
                    f'Less than {min_lead_days} days lead time. '
                    'Confirm with production.')

        return cleaned_data
```

### 3.3 Employee Form Validation

```python
class EmployeeForm(forms.ModelForm):
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = (today - dob).days / 365.25
            if age < 18:
                raise ValidationError('Employee must be at least 18 years old')
            if age > 80:
                raise ValidationError('Please verify date of birth')
        return dob

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check for duplicate email
            qs = Employee.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Email already in use by another employee')
        return email

    def clean(self):
        cleaned_data = super().clean()

        hire_date = cleaned_data.get('hire_date')
        termination_date = cleaned_data.get('termination_date')

        if hire_date and termination_date:
            if termination_date <= hire_date:
                raise ValidationError({
                    'termination_date': 'Termination date must be after hire date'
                })

        return cleaned_data
```

### 3.4 TimeEntry Form Validation

```python
class TimeEntryForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()

        clock_in = cleaned_data.get('clock_in_time')
        clock_out = cleaned_data.get('clock_out_time')
        entry_date = cleaned_data.get('entry_date')
        employee = cleaned_data.get('employee')

        # Time sequence validation
        if clock_in and clock_out:
            if clock_out <= clock_in:
                raise ValidationError({
                    'clock_out_time': 'Clock out must be after clock in'
                })

            # Maximum shift duration
            duration = (clock_out - clock_in).total_seconds() / 3600
            if duration > 16:
                raise ValidationError({
                    'clock_out_time': 'Shift duration cannot exceed 16 hours'
                })

        # No future entries
        if entry_date and entry_date > date.today():
            raise ValidationError({
                'entry_date': 'Cannot create time entries for future dates'
            })

        # No duplicate entries
        if employee and entry_date:
            existing = TimeEntry.objects.filter(
                employee=employee,
                entry_date=entry_date
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError(
                    'Time entry already exists for this employee on this date'
                )

        return cleaned_data
```

---

## 4. Business Logic Validation

### 4.1 Status Transition Rules

#### WorkOrder Status Transitions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WORK ORDER STATUS STATE MACHINE                           │
└─────────────────────────────────────────────────────────────────────────────┘

         ┌─────────┐
         │  DRAFT  │◄────────────────────────────────────────┐
         └────┬────┘                                         │
              │ can_release()                                │
              ▼                                              │
         ┌─────────┐         can_cancel()                   │
         │ PLANNED │─────────────────────────────────┐      │
         └────┬────┘                                 │      │
              │ can_release()                        │      │
              ▼                                      │      │
         ┌─────────┐         can_cancel()           │      │
         │RELEASED │────────────────────────────────┤      │
         └────┬────┘                                │      │
              │ can_start()                         │      │
              ▼                                     │      │
       ┌────────────┐       can_hold()             │      │
       │IN_PROGRESS │◄────────────────┐            │      │
       └──────┬─────┘                 │            │      │
              │                       │            │      │
    ┌─────────┴─────────┐        ┌────┴────┐      │      │
    ▼                   ▼        │ ON_HOLD │      │      │
┌─────────┐      ┌───────────┐   └─────────┘      │      │
│QC_PEND. │      │COMPLETED* │                    ▼      │
└────┬────┘      └───────────┘              ┌──────────┐ │
     │                                      │CANCELLED │ │
     ├───────────┐                          └──────────┘ │
     ▼           ▼                                       │
┌─────────┐ ┌─────────┐                                 │
│QC_PASSED│ │QC_FAILED│─────────────────────────────────┘
└────┬────┘ └─────────┘    (back to DRAFT for rework)
     │
     ▼
┌──────────┐
│COMPLETED │
└──────────┘

* COMPLETED from IN_PROGRESS only when all operations done
```

#### Transition Validation Code

```python
class WorkOrder(models.Model):
    VALID_TRANSITIONS = {
        'DRAFT': ['PLANNED', 'CANCELLED'],
        'PLANNED': ['RELEASED', 'CANCELLED', 'DRAFT'],
        'RELEASED': ['IN_PROGRESS', 'CANCELLED', 'PLANNED'],
        'IN_PROGRESS': ['QC_PENDING', 'ON_HOLD', 'COMPLETED'],
        'ON_HOLD': ['IN_PROGRESS', 'CANCELLED'],
        'QC_PENDING': ['QC_PASSED', 'QC_FAILED'],
        'QC_PASSED': ['COMPLETED'],
        'QC_FAILED': ['DRAFT', 'IN_PROGRESS'],  # Rework path
        'COMPLETED': [],  # Terminal state
        'CANCELLED': [],  # Terminal state
    }

    def can_transition_to(self, new_status):
        """Check if status transition is valid."""
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])

    def transition_to(self, new_status, user):
        """Perform status transition with validation."""
        if not self.can_transition_to(new_status):
            raise ValidationError(
                f'Cannot transition from {self.status} to {new_status}'
            )

        # Additional transition-specific validation
        if new_status == 'RELEASED':
            if not self.estimated_cost:
                raise ValidationError('Cost estimate required to release')
            if not self.assigned_to:
                raise ValidationError('Must assign to technician before release')

        if new_status == 'COMPLETED':
            if self.status != 'QC_PASSED':
                # Check all operations complete
                incomplete = self.operations.exclude(status='COMPLETED')
                if incomplete.exists():
                    raise ValidationError(
                        f'{incomplete.count()} operations not completed'
                    )

        # Log transition
        StatusTransitionLog.objects.create(
            work_order=self,
            from_status=self.status,
            to_status=new_status,
            changed_by=user
        )

        self.status = new_status
        self.save()
```

### 4.2 Approval Authority Validation

```python
class RepairEvaluation(models.Model):
    def requires_approval(self):
        """Determine if approval is needed based on cost."""
        total = self.total_estimated_cost

        if total <= 10000:
            return None  # Auto-approve
        elif total <= 50000:
            return 'MANAGER'
        else:
            return 'EXECUTIVE'

    def can_approve(self, user):
        """Check if user has authority to approve."""
        required_level = self.requires_approval()

        if required_level is None:
            return True

        user_roles = user.roles.values_list('code', flat=True)

        if required_level == 'MANAGER':
            return any(r in ['OPERATIONS_MANAGER', 'QUALITY_MANAGER', 'EXECUTIVE']
                      for r in user_roles)
        elif required_level == 'EXECUTIVE':
            return 'EXECUTIVE' in user_roles

        return False

    def approve(self, user):
        """Approve the evaluation with authority check."""
        if self.status != 'PENDING_APPROVAL':
            raise ValidationError('Evaluation not pending approval')

        if not self.can_approve(user):
            required = self.requires_approval()
            raise PermissionDenied(
                f'Approval requires {required} authority. '
                f'Estimated cost: ${self.total_estimated_cost:.2f}'
            )

        self.status = 'APPROVED'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
```

### 4.3 Cross-Entity Validation

```python
# Validate material availability before work order release
def validate_material_availability(work_order):
    """Check all required materials are available."""
    errors = []

    for material in work_order.materials.all():
        available = material.inventory_item.get_available_quantity(
            location=work_order.warehouse
        )

        if available < material.planned_quantity:
            errors.append({
                'item': material.inventory_item.code,
                'required': material.planned_quantity,
                'available': available,
                'shortage': material.planned_quantity - available
            })

    if errors:
        raise ValidationError({
            'materials': 'Insufficient inventory',
            'details': errors
        })

# Validate certification before assignment
def validate_technician_certification(technician, work_order):
    """Ensure technician has required certifications."""
    required_certs = work_order.get_required_certifications()

    for cert_type in required_certs:
        valid_cert = technician.certifications.filter(
            certification_type=cert_type,
            status='CURRENT',
            expiry_date__gt=date.today()
        ).exists()

        if not valid_cert:
            raise ValidationError(
                f'Technician lacks required {cert_type} certification'
            )
```

---

## 5. Database Constraints

### 5.1 Unique Constraints

| Model | Fields | Constraint Name |
|-------|--------|-----------------|
| DrillBit | serial_number | drillbit_serial_unique |
| WorkOrder | wo_number | workorder_number_unique |
| SalesOrder | so_number | salesorder_number_unique |
| Employee | employee_number | employee_number_unique |
| Employee | badge_number | employee_badge_unique |
| InventoryStock | item, location, lot_number, serial_number | inventory_stock_unique |
| ERPMapping | entity_type, ardt_id, erp_system | erp_mapping_unique |
| SkillMatrix | employee, skill_name | skill_matrix_unique |

### 5.2 Foreign Key Constraints

| Model | Field | Reference | On Delete |
|-------|-------|-----------|-----------|
| WorkOrder | drill_bit | DrillBit | SET_NULL |
| WorkOrder | customer | Customer | SET_NULL |
| WorkOrder | created_by | User | SET_NULL |
| SalesOrder | customer | Customer | CASCADE |
| SalesOrderLine | sales_order | SalesOrder | CASCADE |
| NCR | work_order | WorkOrder | SET_NULL |
| InventoryTransaction | item | InventoryItem | PROTECT |
| MaterialConsumption | lot | MaterialLot | PROTECT |

### 5.3 Check Constraints

```python
# In migration file
class Migration(migrations.Migration):
    operations = [
        migrations.AddConstraint(
            model_name='workorder',
            constraint=models.CheckConstraint(
                check=models.Q(estimated_hours__gte=0),
                name='workorder_estimated_hours_positive'
            ),
        ),
        migrations.AddConstraint(
            model_name='drillbit',
            constraint=models.CheckConstraint(
                check=models.Q(total_footage__gte=0),
                name='drillbit_footage_positive'
            ),
        ),
        migrations.AddConstraint(
            model_name='salesorder',
            constraint=models.CheckConstraint(
                check=models.Q(required_date__gte=models.F('order_date')),
                name='salesorder_dates_valid'
            ),
        ),
    ]
```

---

## 6. Workflow Rules

### 6.1 Approval Workflows

| Entity | Trigger | Approver(s) | Timeout |
|--------|---------|-------------|---------|
| RepairEvaluation > $10K | Creation | Operations Manager | 48 hours |
| RepairEvaluation > $50K | Creation | Executive | 72 hours |
| NCR Disposition | Status change | Quality Manager | 24 hours |
| LeaveRequest | Submission | Direct Manager | 72 hours |
| PurchaseOrder > $5K | Creation | Procurement Manager | 48 hours |
| TimeEntry correction | Submission | Supervisor | 24 hours |

### 6.2 Escalation Rules

```python
class ApprovalWorkflow:
    ESCALATION_RULES = {
        'RepairEvaluation': {
            'initial_timeout': timedelta(hours=48),
            'escalation_levels': [
                ('OPERATIONS_MANAGER', timedelta(hours=48)),
                ('PLANT_MANAGER', timedelta(hours=24)),
                ('VP_OPERATIONS', timedelta(hours=24)),
            ]
        },
        'NCR': {
            'initial_timeout': timedelta(hours=24),
            'escalation_levels': [
                ('QUALITY_MANAGER', timedelta(hours=24)),
                ('QUALITY_DIRECTOR', timedelta(hours=12)),
            ]
        },
    }

    def check_escalation(self, approval_request):
        """Check if approval needs escalation."""
        rules = self.ESCALATION_RULES.get(approval_request.entity_type)
        if not rules:
            return None

        elapsed = timezone.now() - approval_request.created_at

        for level, timeout in rules['escalation_levels']:
            if elapsed > timeout and approval_request.current_level != level:
                return level

        return None
```

### 6.3 Audit Trail Requirements

| Entity | Events Logged | Retention |
|--------|--------------|-----------|
| WorkOrder | All status changes, edits | 7 years |
| DrillBit | All status changes, assignments | Lifetime |
| NCR | All changes | 10 years |
| Certification | All changes | 10 years |
| InventoryTransaction | All transactions | 7 years |
| TimeEntry | All entries and corrections | 3 years |

---

## 7. Error Messages

### 7.1 Standard Error Messages

```python
ERROR_MESSAGES = {
    # Field validation
    'required': 'This field is required.',
    'invalid_choice': 'Select a valid choice. {value} is not available.',
    'max_length': 'Ensure this value has at most {limit} characters.',
    'min_length': 'Ensure this value has at least {limit} characters.',
    'invalid_email': 'Enter a valid email address.',
    'invalid_date': 'Enter a valid date.',
    'invalid_number': 'Enter a valid number.',

    # Business logic
    'status_transition_invalid': 'Cannot change status from {from_status} to {to_status}.',
    'approval_required': 'This action requires approval from {approver_role}.',
    'insufficient_authority': 'You do not have authority to {action}.',
    'credit_exceeded': 'Order exceeds credit limit. Available: {available}.',
    'material_shortage': 'Insufficient {item}. Required: {required}, Available: {available}.',
    'certification_missing': 'Required certification "{cert_type}" is missing or expired.',
    'date_sequence_invalid': '{end_field} must be after {start_field}.',

    # Duplicate prevention
    'duplicate_entry': 'A record already exists for {identifier}.',
    'serial_exists': 'Serial number {serial} is already in use.',

    # Workflow
    'approval_pending': 'Cannot proceed. Approval pending from {approver}.',
    'workflow_blocked': 'Cannot {action}. Prerequisites not met: {missing}.',
}
```

### 7.2 User-Friendly Error Formatting

```python
def format_error_message(code, **kwargs):
    """Format error message with context."""
    template = ERROR_MESSAGES.get(code, 'An error occurred.')
    return template.format(**kwargs)

# Example usage
raise ValidationError(
    format_error_message(
        'material_shortage',
        item='PDC Cutter Grade A',
        required=12,
        available=5
    )
)
# Result: "Insufficient PDC Cutter Grade A. Required: 12, Available: 5."
```

---

## 8. Edge Cases

### 8.1 Null and Empty Value Handling

| Field Type | Null | Blank | Empty String | Validation |
|------------|------|-------|--------------|------------|
| CharField (required) | No | No | Rejected | Must have content |
| CharField (optional) | Yes | Yes | Convert to None | Normalize empties |
| ForeignKey (optional) | Yes | Yes | N/A | Allow null |
| DecimalField (cost) | No | No | N/A | Default to 0.00 |
| DateField (optional) | Yes | Yes | N/A | Allow null |
| TextField (required) | No | No | Rejected | Min length check |

### 8.2 Concurrent Modification Handling

```python
from django.db import transaction
from django.db.models import F

class WorkOrder(models.Model):
    def increment_actual_hours(self, hours):
        """Thread-safe hour increment."""
        with transaction.atomic():
            WorkOrder.objects.filter(pk=self.pk).update(
                actual_hours=F('actual_hours') + hours
            )
            self.refresh_from_db()

    def reserve_materials(self):
        """Atomic material reservation."""
        with transaction.atomic():
            for material in self.materials.all():
                # Lock the inventory row
                stock = InventoryStock.objects.select_for_update().get(
                    item=material.inventory_item,
                    location=self.warehouse
                )

                if stock.quantity_available < material.planned_quantity:
                    raise ValidationError(
                        f'Insufficient {material.inventory_item.code}'
                    )

                stock.quantity_reserved += material.planned_quantity
                stock.save()
```

### 8.3 Timezone Handling

```python
from django.utils import timezone

def validate_datetime_field(value, field_name):
    """Ensure datetime is timezone-aware."""
    if value is None:
        return None

    if timezone.is_naive(value):
        # Assume UTC if naive
        value = timezone.make_aware(value, timezone.utc)

    # Don't allow future dates for entry fields
    if field_name.endswith('_at') and value > timezone.now():
        raise ValidationError(f'{field_name} cannot be in the future')

    return value
```

### 8.4 Unicode and Special Characters

```python
import re

def validate_serial_number(value):
    """Validate serial number format."""
    # Allow alphanumeric, dashes, and underscores only
    pattern = r'^[A-Za-z0-9\-_]+$'
    if not re.match(pattern, value):
        raise ValidationError(
            'Serial number can only contain letters, numbers, dashes, and underscores'
        )
    return value.upper()  # Normalize to uppercase

def sanitize_text_input(value):
    """Remove potentially dangerous characters."""
    if value is None:
        return None

    # Remove null bytes
    value = value.replace('\x00', '')

    # Normalize Unicode
    import unicodedata
    value = unicodedata.normalize('NFC', value)

    # Strip leading/trailing whitespace
    value = value.strip()

    return value
```

---

**Document Control:**
- Created: December 2024
- Review Cycle: Quarterly
- Owner: Development Team
- Classification: Internal Technical
