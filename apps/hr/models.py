"""
ARDT FMS - HR & Workforce Management Models
Version: 8.0 (Sprint 8 - Final Sprint)

Sprint 8: HR & Workforce Management - System Completion

Models:
Week 1: Employee Management
- Employee (extended profiles, 70+ fields)
- EmployeeDocument (document management)
- EmergencyContact (emergency contacts)
- BankAccount (payroll banking)

Week 2: Performance & Skills
- PerformanceReview (evaluations)
- Goal (objectives tracking)
- SkillMatrix (competencies)
- DisciplinaryAction (disciplinary records)

Week 3: Time & Scheduling
- ShiftSchedule (work scheduling)
- TimeEntry (time tracking)
- LeaveRequest (leave management)
- PayrollPeriod (payroll periods)

Legacy Models (P4 skeleton - preserved):
- Attendance, AttendancePunch, LeaveType, OvertimeRequest
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


# =============================================================================
# WEEK 1: EMPLOYEE MANAGEMENT
# =============================================================================


class Employee(models.Model):
    """
    Extended employee profile and HR records.

    Extends Django User model with comprehensive HR information
    including employment details, compensation, and organizational
    relationships.

    Integrates with:
    - User: One-to-one relationship with Django User
    - FieldTechnician: One-to-one for field service employees
    - TrainingRecord: Employee training history
    - Certification: Employee certifications
    - PerformanceReview: Performance management
    - TimeEntry: Time and attendance

    ISO 9001 Reference:
    - Clause 7.1.2: People (as a resource)
    - Clause 7.2: Competence

    Author: Sprint 8 Implementation - Final Sprint!
    Date: December 2024
    """

    class EmploymentType(models.TextChoices):
        """Types of employment"""
        FULL_TIME = "FULL_TIME", "Full-Time"
        PART_TIME = "PART_TIME", "Part-Time"
        CONTRACT = "CONTRACT", "Contract"
        TEMPORARY = "TEMPORARY", "Temporary"
        INTERN = "INTERN", "Intern"
        SEASONAL = "SEASONAL", "Seasonal"

    class EmploymentStatus(models.TextChoices):
        """Employment status"""
        ACTIVE = "ACTIVE", "Active"
        ON_LEAVE = "ON_LEAVE", "On Leave"
        SUSPENDED = "SUSPENDED", "Suspended"
        TERMINATED = "TERMINATED", "Terminated"
        RETIRED = "RETIRED", "Retired"

    class PayType(models.TextChoices):
        """How employee is paid"""
        HOURLY = "HOURLY", "Hourly"
        SALARIED = "SALARIED", "Salaried"
        COMMISSION = "COMMISSION", "Commission"
        CONTRACT = "CONTRACT", "Contract/Fixed"

    # ===== USER RELATIONSHIP =====

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        help_text="Related Django User account"
    )

    # ===== EMPLOYEE IDENTIFICATION =====

    employee_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique employee number (auto-generated: EMP-####)"
    )

    badge_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Physical badge/ID number"
    )

    # ===== PERSONAL INFORMATION =====

    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Date of birth"
    )

    national_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="National ID / SSN (encrypted in production)"
    )

    passport_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Passport number"
    )

    nationality = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nationality/Citizenship"
    )

    marital_status = models.CharField(
        max_length=20,
        choices=[
            ('SINGLE', 'Single'),
            ('MARRIED', 'Married'),
            ('DIVORCED', 'Divorced'),
            ('WIDOWED', 'Widowed'),
            ('OTHER', 'Other'),
        ],
        blank=True,
        help_text="Marital status"
    )

    # ===== CONTACT INFORMATION =====

    personal_email = models.EmailField(
        blank=True,
        help_text="Personal email address"
    )

    mobile_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Mobile phone number"
    )

    home_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Home phone number"
    )

    # ===== ADDRESS =====

    address_line_1 = models.CharField(
        max_length=500,
        blank=True,
        help_text="Home address line 1"
    )

    address_line_2 = models.CharField(
        max_length=500,
        blank=True,
        help_text="Home address line 2"
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        help_text="City"
    )

    state_province = models.CharField(
        max_length=100,
        blank=True,
        help_text="State or province"
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="Postal/ZIP code"
    )

    country = models.CharField(
        max_length=100,
        default='Saudi Arabia',
        help_text="Country"
    )

    # ===== EMPLOYMENT DETAILS =====

    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
        db_index=True,
        help_text="Type of employment"
    )

    employment_status = models.CharField(
        max_length=20,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.ACTIVE,
        db_index=True,
        help_text="Current employment status"
    )

    hire_date = models.DateField(
        help_text="Date of hire"
    )

    probation_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End of probation period"
    )

    termination_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of termination (if applicable)"
    )

    termination_reason = models.TextField(
        blank=True,
        help_text="Reason for termination"
    )

    # ===== ORGANIZATIONAL STRUCTURE =====

    department = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Department"
    )

    job_title = models.CharField(
        max_length=200,
        help_text="Job title"
    )

    job_description = models.TextField(
        blank=True,
        help_text="Job description and responsibilities"
    )

    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports',
        help_text="Direct manager/supervisor"
    )

    work_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Primary work location/office"
    )

    # ===== COMPENSATION =====

    pay_type = models.CharField(
        max_length=20,
        choices=PayType.choices,
        default=PayType.HOURLY,
        help_text="How employee is paid"
    )

    pay_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hourly rate or annual salary"
    )

    currency_code = models.CharField(
        max_length=3,
        default='SAR',
        help_text="Currency for pay rate (ISO 4217)"
    )

    pay_grade = models.CharField(
        max_length=50,
        blank=True,
        help_text="Pay grade or band"
    )

    # ===== WORK SCHEDULE =====

    standard_hours_per_week = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('40.00'),
        help_text="Standard hours per week"
    )

    work_shift = models.CharField(
        max_length=50,
        blank=True,
        help_text="Standard work shift (e.g., 'Day', 'Night', '8am-5pm')"
    )

    # ===== BENEFITS & ENTITLEMENTS =====

    annual_leave_days = models.IntegerField(
        default=21,
        help_text="Annual leave entitlement (days per year)"
    )

    sick_leave_days = models.IntegerField(
        default=10,
        help_text="Sick leave entitlement (days per year)"
    )

    benefits_enrolled = models.TextField(
        blank=True,
        help_text="Benefits enrolled in (health insurance, pension, etc.)"
    )

    # ===== PERFORMANCE =====

    last_review_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last performance review"
    )

    next_review_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of next scheduled review"
    )

    performance_rating = models.CharField(
        max_length=20,
        choices=[
            ('OUTSTANDING', 'Outstanding'),
            ('EXCEEDS', 'Exceeds Expectations'),
            ('MEETS', 'Meets Expectations'),
            ('NEEDS_IMPROVEMENT', 'Needs Improvement'),
            ('UNSATISFACTORY', 'Unsatisfactory'),
        ],
        blank=True,
        help_text="Most recent performance rating"
    )

    # ===== COMPLIANCE & VERIFICATION =====

    background_check_completed = models.BooleanField(
        default=False,
        help_text="Whether background check was completed"
    )

    background_check_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of background check"
    )

    work_permit_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Work permit/visa number (if applicable)"
    )

    work_permit_expiry = models.DateField(
        null=True,
        blank=True,
        help_text="Work permit expiry date"
    )

    # ===== FIELD SERVICE RELATIONSHIP =====

    is_field_technician = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Is this employee a field service technician?"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Additional notes about employee"
    )

    # ===== AUDIT TRAIL =====

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When employee record was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When employee record was last updated"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_employees',
        help_text="User who created this employee record"
    )

    class Meta:
        db_table = "employees"
        ordering = ['employee_number']
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        indexes = [
            models.Index(fields=['employee_number']),
            models.Index(fields=['employment_status', 'employment_type']),
            models.Index(fields=['department']),
            models.Index(fields=['hire_date']),
        ]
        permissions = [
            ("can_view_employee_compensation", "Can view employee compensation"),
            ("can_manage_employee_records", "Can manage employee records"),
            ("can_terminate_employees", "Can terminate employees"),
        ]

    def __str__(self):
        return f"{self.employee_number} - {self.user.get_full_name() or self.user.username}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate employee number"""
        if not self.employee_number:
            self.employee_number = self._generate_employee_number()
        super().save(*args, **kwargs)

    def _generate_employee_number(self):
        """Generate unique employee number: EMP-####"""
        last_employee = Employee.objects.order_by('-id').first()

        if last_employee and last_employee.employee_number.startswith('EMP-'):
            try:
                last_num = int(last_employee.employee_number.split('-')[1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"EMP-{new_num:04d}"

    # ===== PROPERTIES =====

    @property
    def full_name(self):
        """Get employee's full name"""
        return self.user.get_full_name() or self.user.username

    @property
    def is_active(self):
        """Check if employee is currently active"""
        return self.employment_status == self.EmploymentStatus.ACTIVE

    @property
    def is_on_probation(self):
        """Check if employee is still on probation"""
        if not self.probation_end_date:
            return False
        return timezone.now().date() <= self.probation_end_date

    @property
    def years_of_service(self):
        """Calculate years of service"""
        if self.termination_date:
            end_date = self.termination_date
        else:
            end_date = timezone.now().date()

        delta = end_date - self.hire_date
        return delta.days / 365.25

    @property
    def age(self):
        """Calculate current age"""
        if not self.date_of_birth:
            return None

        today = timezone.now().date()
        age = today.year - self.date_of_birth.year

        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1

        return age

    @property
    def work_permit_is_expired(self):
        """Check if work permit has expired"""
        if not self.work_permit_expiry:
            return None
        return timezone.now().date() > self.work_permit_expiry

    # ===== METHODS =====

    def terminate(self, termination_date, reason, user):
        """Terminate employee."""
        self.employment_status = self.EmploymentStatus.TERMINATED
        self.termination_date = termination_date
        self.termination_reason = reason
        self.save()

    def reactivate(self, user):
        """Reactivate terminated employee"""
        self.employment_status = self.EmploymentStatus.ACTIVE
        self.termination_date = None
        self.termination_reason = ''
        self.save()

    def get_performance_reviews(self):
        """Get all performance reviews"""
        return self.performance_reviews.all()

    def schedule_performance_review(self, review_date):
        """Schedule next performance review"""
        self.next_review_date = review_date
        self.save()


class EmployeeDocument(models.Model):
    """
    Employee documents and records.

    Manages all employee-related documents including contracts,
    certifications, ID documents, and other records.
    """

    class DocumentType(models.TextChoices):
        """Types of employee documents"""
        CONTRACT = "CONTRACT", "Employment Contract"
        ID_DOCUMENT = "ID_DOCUMENT", "ID Document (Passport, National ID)"
        CERTIFICATE = "CERTIFICATE", "Certificate/Diploma"
        MEDICAL = "MEDICAL", "Medical Certificate"
        BACKGROUND_CHECK = "BACKGROUND_CHECK", "Background Check"
        PERFORMANCE_REVIEW = "PERFORMANCE_REVIEW", "Performance Review"
        DISCIPLINARY = "DISCIPLINARY", "Disciplinary Action"
        TERMINATION = "TERMINATION", "Termination Letter"
        OFFER_LETTER = "OFFER_LETTER", "Offer Letter"
        RESIGNATION = "RESIGNATION", "Resignation Letter"
        REFERENCE = "REFERENCE", "Reference Letter"
        TAX_FORM = "TAX_FORM", "Tax Form"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        """Document status"""
        DRAFT = "DRAFT", "Draft"
        PENDING_SIGNATURE = "PENDING_SIGNATURE", "Pending Signature"
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"
        ARCHIVED = "ARCHIVED", "Archived"

    # Employee relationship
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Employee this document belongs to"
    )

    # Document identification
    document_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="Auto-generated: DOC-YYYY-######"
    )

    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
        db_index=True,
        help_text="Type of document"
    )

    title = models.CharField(
        max_length=500,
        help_text="Document title"
    )

    description = models.TextField(
        blank=True,
        help_text="Document description"
    )

    # File information
    file_path = models.CharField(
        max_length=500,
        help_text="Path to document file"
    )

    file_name = models.CharField(
        max_length=500,
        help_text="Original file name"
    )

    file_size = models.IntegerField(
        help_text="File size in bytes"
    )

    file_type = models.CharField(
        max_length=50,
        help_text="MIME type"
    )

    # Dates
    issue_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date document was issued"
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date document expires"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Document status"
    )

    # Signatures
    requires_employee_signature = models.BooleanField(
        default=False,
        help_text="Does this document require employee signature?"
    )

    employee_signed_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date employee signed"
    )

    requires_hr_signature = models.BooleanField(
        default=False,
        help_text="Does this document require HR signature?"
    )

    hr_signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signed_employee_documents',
        help_text="HR representative who signed"
    )

    hr_signed_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date HR signed"
    )

    # Confidentiality
    is_confidential = models.BooleanField(
        default=False,
        help_text="Is this a confidential document?"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    # Audit
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_employee_documents',
        help_text="User who uploaded document"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When document was uploaded"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When document was last updated"
    )

    class Meta:
        db_table = "employee_documents"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['employee', 'document_type']),
            models.Index(fields=['status']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.document_number} - {self.employee.employee_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.document_number:
            self.document_number = self._generate_document_number()
        super().save(*args, **kwargs)

    def _generate_document_number(self):
        """Generate unique document number: DOC-YYYY-######"""
        year = timezone.now().year
        prefix = f"DOC-{year}-"

        last_doc = EmployeeDocument.objects.filter(
            document_number__startswith=prefix
        ).order_by('-document_number').first()

        if last_doc:
            try:
                last_num = int(last_doc.document_number.split('-')[2])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:06d}"

    @property
    def is_expired(self):
        """Check if document has expired"""
        if not self.expiry_date:
            return False
        return timezone.now().date() > self.expiry_date

    @property
    def is_fully_signed(self):
        """Check if all required signatures are complete"""
        if self.requires_employee_signature and not self.employee_signed_date:
            return False
        if self.requires_hr_signature and not self.hr_signed_date:
            return False
        return True


class EmergencyContact(models.Model):
    """
    Emergency contact information for employees.

    Stores contact details for people to notify in case of emergency.
    """

    class Relationship(models.TextChoices):
        """Relationship to employee"""
        SPOUSE = "SPOUSE", "Spouse"
        PARENT = "PARENT", "Parent"
        CHILD = "CHILD", "Child"
        SIBLING = "SIBLING", "Sibling"
        FRIEND = "FRIEND", "Friend"
        OTHER_FAMILY = "OTHER_FAMILY", "Other Family Member"
        OTHER = "OTHER", "Other"

    # Employee relationship
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='emergency_contacts',
        help_text="Employee this contact belongs to"
    )

    # Contact information
    full_name = models.CharField(
        max_length=200,
        help_text="Contact's full name"
    )

    relationship = models.CharField(
        max_length=20,
        choices=Relationship.choices,
        help_text="Relationship to employee"
    )

    primary_phone = models.CharField(
        max_length=50,
        help_text="Primary phone number"
    )

    alternate_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Alternate phone number"
    )

    email = models.EmailField(
        blank=True,
        help_text="Email address"
    )

    # Address
    address = models.TextField(
        blank=True,
        help_text="Full address"
    )

    # Priority
    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the primary emergency contact?"
    )

    priority_order = models.IntegerField(
        default=1,
        help_text="Order to contact (1 = first)"
    )

    # Additional information
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    # Audit
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When contact was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When contact was last updated"
    )

    class Meta:
        db_table = "emergency_contacts"
        ordering = ['employee', 'priority_order']
        indexes = [
            models.Index(fields=['employee', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.employee.employee_number} - {self.full_name} ({self.get_relationship_display()})"


class BankAccount(models.Model):
    """
    Employee bank account information for payroll.

    Stores banking details for salary payments.
    Note: In production, sensitive fields should be encrypted.
    """

    class AccountType(models.TextChoices):
        """Bank account types"""
        CHECKING = "CHECKING", "Checking Account"
        SAVINGS = "SAVINGS", "Savings Account"
        SALARY = "SALARY", "Salary Account"

    # Employee relationship
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='bank_accounts',
        help_text="Employee this account belongs to"
    )

    # Bank information
    bank_name = models.CharField(
        max_length=200,
        help_text="Name of bank"
    )

    bank_branch = models.CharField(
        max_length=200,
        blank=True,
        help_text="Bank branch"
    )

    bank_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Bank/SWIFT code"
    )

    # Account information
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        help_text="Type of account"
    )

    account_number = models.CharField(
        max_length=100,
        help_text="Bank account number (should be encrypted in production)"
    )

    account_holder_name = models.CharField(
        max_length=200,
        help_text="Name on the account"
    )

    # IBAN (for international)
    iban = models.CharField(
        max_length=50,
        blank=True,
        help_text="International Bank Account Number"
    )

    # Primary account
    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the primary account for salary payments?"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Is this account active?"
    )

    verified = models.BooleanField(
        default=False,
        help_text="Has this account been verified?"
    )

    verified_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date account was verified"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    # Audit
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When account was added"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When account was last updated"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_bank_accounts',
        help_text="User who added this account"
    )

    class Meta:
        db_table = "employee_bank_accounts"
        ordering = ['employee', '-is_primary']
        indexes = [
            models.Index(fields=['employee', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.employee.employee_number} - {self.bank_name} - ****{self.account_number[-4:]}"


# =============================================================================
# WEEK 2: PERFORMANCE & SKILLS
# =============================================================================


class PerformanceReview(models.Model):
    """
    Employee performance reviews and evaluations.

    Manages formal performance review process including ratings,
    goals, competencies, and development plans.
    """

    class ReviewType(models.TextChoices):
        """Types of performance reviews"""
        ANNUAL = "ANNUAL", "Annual Review"
        PROBATION = "PROBATION", "Probation Review"
        MID_YEAR = "MID_YEAR", "Mid-Year Review"
        PROJECT = "PROJECT", "Project Review"
        PROMOTION = "PROMOTION", "Promotion Review"

    class Status(models.TextChoices):
        """Review status"""
        DRAFT = "DRAFT", "Draft"
        PENDING_EMPLOYEE = "PENDING_EMPLOYEE", "Pending Employee Input"
        PENDING_MANAGER = "PENDING_MANAGER", "Pending Manager Review"
        PENDING_HR = "PENDING_HR", "Pending HR Approval"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class OverallRating(models.TextChoices):
        """Overall performance ratings"""
        OUTSTANDING = "OUTSTANDING", "Outstanding (5)"
        EXCEEDS = "EXCEEDS", "Exceeds Expectations (4)"
        MEETS = "MEETS", "Meets Expectations (3)"
        NEEDS_IMPROVEMENT = "NEEDS_IMPROVEMENT", "Needs Improvement (2)"
        UNSATISFACTORY = "UNSATISFACTORY", "Unsatisfactory (1)"

    # Review identification
    review_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Auto-generated: REV-YYYY-####"
    )

    # Employee and reviewer
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.PROTECT,
        related_name='performance_reviews',
        help_text="Employee being reviewed"
    )

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='conducted_reviews',
        help_text="Manager conducting review"
    )

    # Review details
    review_type = models.CharField(
        max_length=20,
        choices=ReviewType.choices,
        help_text="Type of review"
    )

    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Review status"
    )

    review_period_start = models.DateField(
        help_text="Start of review period"
    )

    review_period_end = models.DateField(
        help_text="End of review period"
    )

    review_date = models.DateField(
        help_text="Date of review meeting"
    )

    # Ratings
    overall_rating = models.CharField(
        max_length=20,
        choices=OverallRating.choices,
        blank=True,
        help_text="Overall performance rating"
    )

    technical_skills_rating = models.IntegerField(
        null=True,
        blank=True,
        help_text="Rating 1-5"
    )

    communication_rating = models.IntegerField(
        null=True,
        blank=True,
        help_text="Rating 1-5"
    )

    teamwork_rating = models.IntegerField(
        null=True,
        blank=True,
        help_text="Rating 1-5"
    )

    leadership_rating = models.IntegerField(
        null=True,
        blank=True,
        help_text="Rating 1-5"
    )

    initiative_rating = models.IntegerField(
        null=True,
        blank=True,
        help_text="Rating 1-5"
    )

    quality_of_work_rating = models.IntegerField(
        null=True,
        blank=True,
        help_text="Rating 1-5"
    )

    # Detailed evaluation
    strengths = models.TextField(
        blank=True,
        help_text="Employee strengths"
    )

    areas_for_improvement = models.TextField(
        blank=True,
        help_text="Areas for improvement"
    )

    achievements = models.TextField(
        blank=True,
        help_text="Key achievements during period"
    )

    challenges = models.TextField(
        blank=True,
        help_text="Challenges faced"
    )

    # Employee input
    employee_self_assessment = models.TextField(
        blank=True,
        help_text="Employee's self-assessment"
    )

    employee_comments = models.TextField(
        blank=True,
        help_text="Employee's comments on review"
    )

    employee_acknowledged = models.BooleanField(
        default=False,
        help_text="Has employee acknowledged review?"
    )

    employee_acknowledged_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date employee acknowledged"
    )

    # Development plan
    development_plan = models.TextField(
        blank=True,
        help_text="Career development and improvement plan"
    )

    training_recommended = models.TextField(
        blank=True,
        help_text="Recommended training"
    )

    # Goals
    goals_met_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage of goals achieved"
    )

    # Recommendations
    promotion_recommended = models.BooleanField(
        default=False,
        help_text="Is promotion recommended?"
    )

    salary_increase_recommended = models.BooleanField(
        default=False,
        help_text="Is salary increase recommended?"
    )

    salary_increase_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Recommended salary increase %"
    )

    # HR approval
    hr_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_performance_reviews',
        help_text="HR approver"
    )

    hr_approved_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date HR approved"
    )

    hr_comments = models.TextField(
        blank=True,
        help_text="HR comments"
    )

    # Audit
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When review was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When review was last updated"
    )

    class Meta:
        db_table = "performance_reviews"
        ordering = ['-review_date']
        indexes = [
            models.Index(fields=['employee', '-review_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.review_number} - {self.employee.employee_number} - {self.get_review_type_display()}"

    def save(self, *args, **kwargs):
        if not self.review_number:
            self.review_number = self._generate_review_number()
        super().save(*args, **kwargs)

    def _generate_review_number(self):
        """Generate unique review number: REV-YYYY-####"""
        year = timezone.now().year
        prefix = f"REV-{year}-"

        last_review = PerformanceReview.objects.filter(
            review_number__startswith=prefix
        ).order_by('-review_number').first()

        if last_review:
            try:
                last_num = int(last_review.review_number.split('-')[2])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    @property
    def is_completed(self):
        """Check if review is completed"""
        return self.status == self.Status.COMPLETED


class Goal(models.Model):
    """
    Employee goals and objectives tracking.

    Manages goal setting, progress tracking, and completion.
    """

    class GoalType(models.TextChoices):
        """Types of goals"""
        PERSONAL = "PERSONAL", "Personal Goal"
        TEAM = "TEAM", "Team Goal"
        DEPARTMENTAL = "DEPARTMENTAL", "Departmental Goal"
        COMPANY = "COMPANY", "Company Goal"

    class Category(models.TextChoices):
        """Goal categories"""
        PERFORMANCE = "PERFORMANCE", "Performance"
        DEVELOPMENT = "DEVELOPMENT", "Development"
        BEHAVIORAL = "BEHAVIORAL", "Behavioral"
        PROJECT = "PROJECT", "Project"
        TECHNICAL = "TECHNICAL", "Technical"

    class Status(models.TextChoices):
        """Goal status"""
        NOT_STARTED = "NOT_STARTED", "Not Started"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        ON_HOLD = "ON_HOLD", "On Hold"

    # Goal identification
    goal_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Auto-generated: GOAL-YYYY-####"
    )

    # Employee
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='goals',
        help_text="Employee this goal belongs to"
    )

    # Goal details
    title = models.CharField(
        max_length=300,
        help_text="Goal title"
    )

    description = models.TextField(
        help_text="Detailed goal description"
    )

    goal_type = models.CharField(
        max_length=20,
        choices=GoalType.choices,
        default=GoalType.PERSONAL,
        help_text="Type of goal"
    )

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.PERFORMANCE,
        help_text="Goal category"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
        help_text="Current status"
    )

    # Timeline
    start_date = models.DateField(
        help_text="Goal start date"
    )

    target_date = models.DateField(
        help_text="Target completion date"
    )

    completion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual completion date"
    )

    # Progress
    progress_percentage = models.IntegerField(
        default=0,
        help_text="Progress percentage (0-100)"
    )

    measurement_criteria = models.TextField(
        blank=True,
        help_text="How success will be measured"
    )

    # Link to performance review
    related_performance_review = models.ForeignKey(
        'PerformanceReview',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='goals',
        help_text="Related performance review"
    )

    # Manager
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_goals',
        help_text="Manager who assigned goal"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    # Audit
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When goal was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When goal was last updated"
    )

    class Meta:
        db_table = "employee_goals"
        ordering = ['-target_date']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['target_date']),
        ]

    def __str__(self):
        return f"{self.goal_number} - {self.employee.employee_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.goal_number:
            self.goal_number = self._generate_goal_number()
        super().save(*args, **kwargs)

    def _generate_goal_number(self):
        """Generate unique goal number: GOAL-YYYY-####"""
        year = timezone.now().year
        prefix = f"GOAL-{year}-"

        last_goal = Goal.objects.filter(
            goal_number__startswith=prefix
        ).order_by('-goal_number').first()

        if last_goal:
            try:
                last_num = int(last_goal.goal_number.split('-')[2])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    @property
    def is_overdue(self):
        """Check if goal is overdue"""
        if self.status == self.Status.COMPLETED:
            return False
        return timezone.now().date() > self.target_date


class SkillMatrix(models.Model):
    """
    Skills and competencies tracking.

    Manages employee skills, proficiency levels, and certifications.
    """

    class ProficiencyLevel(models.TextChoices):
        """Proficiency levels"""
        BEGINNER = "BEGINNER", "Beginner"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ADVANCED = "ADVANCED", "Advanced"
        EXPERT = "EXPERT", "Expert"

    class SkillCategory(models.TextChoices):
        """Skill categories"""
        TECHNICAL = "TECHNICAL", "Technical"
        SOFT = "SOFT", "Soft Skills"
        LEADERSHIP = "LEADERSHIP", "Leadership"
        INDUSTRY = "INDUSTRY", "Industry-Specific"
        LANGUAGE = "LANGUAGE", "Language"
        SAFETY = "SAFETY", "Safety"
        OTHER = "OTHER", "Other"

    # Employee
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='skills',
        help_text="Employee this skill belongs to"
    )

    # Skill details
    skill_name = models.CharField(
        max_length=200,
        help_text="Name of skill"
    )

    skill_category = models.CharField(
        max_length=20,
        choices=SkillCategory.choices,
        default=SkillCategory.TECHNICAL,
        help_text="Skill category"
    )

    proficiency_level = models.CharField(
        max_length=20,
        choices=ProficiencyLevel.choices,
        default=ProficiencyLevel.BEGINNER,
        help_text="Current proficiency level"
    )

    years_of_experience = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0,
        help_text="Years of experience with this skill"
    )

    last_used_date = models.DateField(
        null=True,
        blank=True,
        help_text="When skill was last used"
    )

    # Certification
    certified = models.BooleanField(
        default=False,
        help_text="Is skill certified?"
    )

    certification_details = models.TextField(
        blank=True,
        help_text="Certification details"
    )

    certification_expiry = models.DateField(
        null=True,
        blank=True,
        help_text="Certification expiry date"
    )

    # Verification
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_skills',
        help_text="Who verified this skill"
    )

    verified_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date skill was verified"
    )

    # Requirements
    required_for_position = models.BooleanField(
        default=False,
        help_text="Is this skill required for employee's position?"
    )

    training_recommended = models.BooleanField(
        default=False,
        help_text="Is training recommended for this skill?"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    # Audit
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When skill was added"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When skill was last updated"
    )

    class Meta:
        db_table = "employee_skills"
        ordering = ['employee', 'skill_name']
        unique_together = [['employee', 'skill_name']]
        indexes = [
            models.Index(fields=['employee', 'skill_category']),
            models.Index(fields=['proficiency_level']),
        ]

    def __str__(self):
        return f"{self.employee.employee_number} - {self.skill_name} ({self.get_proficiency_level_display()})"

    @property
    def certification_is_expired(self):
        """Check if certification has expired"""
        if not self.certification_expiry:
            return None
        return timezone.now().date() > self.certification_expiry


class DisciplinaryAction(models.Model):
    """
    Disciplinary actions and records.

    Manages disciplinary process including warnings, suspensions,
    and corrective actions.
    """

    class ActionType(models.TextChoices):
        """Types of disciplinary actions"""
        VERBAL_WARNING = "VERBAL_WARNING", "Verbal Warning"
        WRITTEN_WARNING = "WRITTEN_WARNING", "Written Warning"
        FINAL_WARNING = "FINAL_WARNING", "Final Warning"
        SUSPENSION = "SUSPENSION", "Suspension"
        DEMOTION = "DEMOTION", "Demotion"
        TERMINATION = "TERMINATION", "Termination"

    class Severity(models.TextChoices):
        """Severity levels"""
        MINOR = "MINOR", "Minor"
        MODERATE = "MODERATE", "Moderate"
        SERIOUS = "SERIOUS", "Serious"
        SEVERE = "SEVERE", "Severe"

    class Status(models.TextChoices):
        """Action status"""
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending"
        ISSUED = "ISSUED", "Issued"
        APPEALED = "APPEALED", "Appealed"
        RESOLVED = "RESOLVED", "Resolved"
        EXPIRED = "EXPIRED", "Expired"

    # Action identification
    action_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Auto-generated: DA-YYYY-####"
    )

    # Employee
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.PROTECT,
        related_name='disciplinary_actions',
        help_text="Employee receiving action"
    )

    # Action details
    action_type = models.CharField(
        max_length=25,
        choices=ActionType.choices,
        help_text="Type of disciplinary action"
    )

    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MINOR,
        help_text="Severity level"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Action status"
    )

    # Incident details
    incident_date = models.DateField(
        help_text="Date of incident"
    )

    incident_description = models.TextField(
        help_text="Description of incident"
    )

    policy_violated = models.TextField(
        blank=True,
        help_text="Policies or rules violated"
    )

    witnesses = models.TextField(
        blank=True,
        help_text="Witnesses to incident"
    )

    # Action taken
    action_taken = models.TextField(
        help_text="Description of action taken"
    )

    consequences = models.TextField(
        blank=True,
        help_text="Consequences of action"
    )

    # Corrective action
    corrective_action_required = models.TextField(
        blank=True,
        help_text="Required corrective actions"
    )

    corrective_action_deadline = models.DateField(
        null=True,
        blank=True,
        help_text="Deadline for corrective action"
    )

    # Appeal
    appeal_filed = models.BooleanField(
        default=False,
        help_text="Has appeal been filed?"
    )

    appeal_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of appeal"
    )

    appeal_outcome = models.TextField(
        blank=True,
        help_text="Outcome of appeal"
    )

    # Issued by
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='issued_disciplinary_actions',
        help_text="Manager who issued action"
    )

    issued_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date action was issued"
    )

    # Employee acknowledgment
    acknowledged_by_employee = models.BooleanField(
        default=False,
        help_text="Has employee acknowledged?"
    )

    acknowledged_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date employee acknowledged"
    )

    employee_comments = models.TextField(
        blank=True,
        help_text="Employee's comments"
    )

    # Expiry (for warnings)
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date action expires"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    # Audit
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When action was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When action was last updated"
    )

    class Meta:
        db_table = "disciplinary_actions"
        ordering = ['-incident_date']
        indexes = [
            models.Index(fields=['employee', '-incident_date']),
            models.Index(fields=['status']),
            models.Index(fields=['action_type']),
        ]

    def __str__(self):
        return f"{self.action_number} - {self.employee.employee_number} - {self.get_action_type_display()}"

    def save(self, *args, **kwargs):
        if not self.action_number:
            self.action_number = self._generate_action_number()
        super().save(*args, **kwargs)

    def _generate_action_number(self):
        """Generate unique action number: DA-YYYY-####"""
        year = timezone.now().year
        prefix = f"DA-{year}-"

        last_action = DisciplinaryAction.objects.filter(
            action_number__startswith=prefix
        ).order_by('-action_number').first()

        if last_action:
            try:
                last_num = int(last_action.action_number.split('-')[2])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    @property
    def is_expired(self):
        """Check if action has expired"""
        if not self.expiry_date:
            return False
        return timezone.now().date() > self.expiry_date


# =============================================================================
# WEEK 3: TIME & SCHEDULING
# =============================================================================


class ShiftSchedule(models.Model):
    """
    Employee work shift scheduling.

    Manages employee work schedules, shifts, and assignments.
    """

    class ShiftType(models.TextChoices):
        """Types of shifts"""
        DAY = "DAY", "Day Shift"
        EVENING = "EVENING", "Evening Shift"
        NIGHT = "NIGHT", "Night Shift"
        ROTATING = "ROTATING", "Rotating Shift"
        ON_CALL = "ON_CALL", "On-Call"
        SPLIT = "SPLIT", "Split Shift"

    class Status(models.TextChoices):
        """Shift status"""
        SCHEDULED = "SCHEDULED", "Scheduled"
        CONFIRMED = "CONFIRMED", "Confirmed"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        NO_SHOW = "NO_SHOW", "No Show"

    # Employee assignment
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.PROTECT,
        related_name='shift_schedules',
        help_text="Employee assigned to shift"
    )

    # Shift details
    shift_type = models.CharField(
        max_length=20,
        choices=ShiftType.choices,
        help_text="Type of shift"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        help_text="Shift status"
    )

    # Date and time
    shift_date = models.DateField(
        db_index=True,
        help_text="Date of shift"
    )

    start_time = models.TimeField(
        help_text="Scheduled start time"
    )

    end_time = models.TimeField(
        help_text="Scheduled end time"
    )

    break_duration_minutes = models.IntegerField(
        default=0,
        help_text="Total break time in minutes"
    )

    # Location
    work_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Work location"
    )

    # Relationship to field work
    site_visit = models.ForeignKey(
        'sales.SiteVisit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shift_schedules',
        help_text="Related site visit if field work"
    )

    # Actual times (filled when shift completes)
    actual_start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Actual start time"
    )

    actual_end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Actual end time"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    cancellation_reason = models.TextField(
        blank=True,
        help_text="Reason for cancellation"
    )

    # Audit
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When shift was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When shift was last updated"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_shifts',
        help_text="User who created shift"
    )

    class Meta:
        db_table = "shift_schedules"
        ordering = ['-shift_date', 'start_time']
        indexes = [
            models.Index(fields=['employee', 'shift_date']),
            models.Index(fields=['shift_date', 'status']),
        ]

    def __str__(self):
        return f"{self.employee.employee_number} - {self.shift_date} {self.start_time}-{self.end_time}"

    @property
    def scheduled_hours(self):
        """Calculate scheduled hours"""
        from datetime import datetime, timedelta

        start = datetime.combine(self.shift_date, self.start_time)
        end = datetime.combine(self.shift_date, self.end_time)

        # Handle overnight shifts
        if end < start:
            end += timedelta(days=1)

        duration = end - start
        hours = duration.total_seconds() / 3600

        # Subtract breaks
        hours -= self.break_duration_minutes / 60

        return round(hours, 2)


class TimeEntry(models.Model):
    """
    Time tracking and attendance.

    Manages employee time entries for work hours tracking.
    """

    class EntryType(models.TextChoices):
        """Types of time entries"""
        REGULAR = "REGULAR", "Regular Work"
        OVERTIME = "OVERTIME", "Overtime"
        HOLIDAY = "HOLIDAY", "Holiday Work"
        SICK = "SICK", "Sick Leave"
        VACATION = "VACATION", "Vacation"
        TRAINING = "TRAINING", "Training"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        """Entry status"""
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    # Entry identification
    entry_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Auto-generated: TIME-YYYY-######"
    )

    # Employee
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.PROTECT,
        related_name='time_entries',
        help_text="Employee this entry belongs to"
    )

    # Entry details
    entry_type = models.CharField(
        max_length=20,
        choices=EntryType.choices,
        default=EntryType.REGULAR,
        help_text="Type of time entry"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Entry status"
    )

    # Date and time
    entry_date = models.DateField(
        db_index=True,
        help_text="Date of entry"
    )

    clock_in_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Clock in time"
    )

    clock_out_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Clock out time"
    )

    # Hours
    total_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Total hours worked"
    )

    break_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Break hours"
    )

    overtime_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Overtime hours"
    )

    # Location
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Work location"
    )

    gps_coordinates = models.CharField(
        max_length=100,
        blank=True,
        help_text="GPS coordinates (lat,long)"
    )

    # Related work
    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_entries',
        help_text="Related work order for labor tracking"
    )

    site_visit = models.ForeignKey(
        'sales.SiteVisit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_entries',
        help_text="Related site visit for field work"
    )

    work_description = models.TextField(
        blank=True,
        help_text="Description of work performed"
    )

    # Approval
    submitted_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date submitted for approval"
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_time_entries',
        help_text="Approver"
    )

    approved_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date approved"
    )

    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    # Audit
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When entry was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When entry was last updated"
    )

    class Meta:
        db_table = "time_entries"
        ordering = ['-entry_date']
        indexes = [
            models.Index(fields=['employee', '-entry_date']),
            models.Index(fields=['status']),
            models.Index(fields=['entry_date']),
        ]

    def __str__(self):
        return f"{self.entry_number} - {self.employee.employee_number} - {self.entry_date}"

    def save(self, *args, **kwargs):
        if not self.entry_number:
            self.entry_number = self._generate_entry_number()
        super().save(*args, **kwargs)

    def _generate_entry_number(self):
        """Generate unique entry number: TIME-YYYY-######"""
        year = timezone.now().year
        prefix = f"TIME-{year}-"

        last_entry = TimeEntry.objects.filter(
            entry_number__startswith=prefix
        ).order_by('-entry_number').first()

        if last_entry:
            try:
                last_num = int(last_entry.entry_number.split('-')[2])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:06d}"


class LeaveRequest(models.Model):
    """
    Employee leave and absence requests.

    Manages all types of employee leave including annual leave,
    sick leave, and other absences.
    """

    class LeaveType(models.TextChoices):
        """Types of leave"""
        ANNUAL = "ANNUAL", "Annual Leave"
        SICK = "SICK", "Sick Leave"
        EMERGENCY = "EMERGENCY", "Emergency Leave"
        MATERNITY = "MATERNITY", "Maternity Leave"
        PATERNITY = "PATERNITY", "Paternity Leave"
        BEREAVEMENT = "BEREAVEMENT", "Bereavement Leave"
        UNPAID = "UNPAID", "Unpaid Leave"
        COMPENSATORY = "COMPENSATORY", "Compensatory Leave"
        STUDY = "STUDY", "Study Leave"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        """Request status"""
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    # Request identification
    request_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Auto-generated: LEAVE-YYYY-####"
    )

    # Employee
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.PROTECT,
        related_name='employee_leave_requests',
        help_text="Employee requesting leave"
    )

    # Leave details
    leave_type = models.CharField(
        max_length=20,
        choices=LeaveType.choices,
        help_text="Type of leave"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Request status"
    )

    start_date = models.DateField(
        db_index=True,
        help_text="Leave start date"
    )

    end_date = models.DateField(
        help_text="Leave end date"
    )

    is_half_day = models.BooleanField(
        default=False,
        help_text="Is this a half-day leave?"
    )

    total_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Total leave days"
    )

    # Reason
    reason = models.TextField(
        help_text="Reason for leave"
    )

    # Supporting documentation
    supporting_document = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to supporting document"
    )

    medical_certificate_required = models.BooleanField(
        default=False,
        help_text="Is medical certificate required?"
    )

    # Approval workflow
    submitted_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date submitted"
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_employee_leave_requests',
        help_text="Approver"
    )

    approved_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date approved"
    )

    approval_comments = models.TextField(
        blank=True,
        help_text="Approval comments"
    )

    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_employee_leave_requests',
        help_text="Who rejected"
    )

    rejected_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date rejected"
    )

    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection"
    )

    # Cancellation
    cancelled_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date cancelled"
    )

    cancellation_reason = models.TextField(
        blank=True,
        help_text="Reason for cancellation"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    # Audit
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When request was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When request was last updated"
    )

    class Meta:
        db_table = "employee_leave_requests"
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['employee', '-start_date']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.request_number} - {self.employee.employee_number} - {self.get_leave_type_display()}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            self.request_number = self._generate_request_number()
        super().save(*args, **kwargs)

    def _generate_request_number(self):
        """Generate unique request number: LEAVE-YYYY-####"""
        year = timezone.now().year
        prefix = f"LEAVE-{year}-"

        last_request = LeaveRequest.objects.filter(
            request_number__startswith=prefix
        ).order_by('-request_number').first()

        if last_request:
            try:
                last_num = int(last_request.request_number.split('-')[2])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    def submit(self):
        """Submit leave request for approval"""
        self.status = self.Status.PENDING
        self.submitted_date = timezone.now().date()
        self.save()

    def approve(self, user, comments=''):
        """Approve leave request"""
        self.status = self.Status.APPROVED
        self.approved_by = user
        self.approved_date = timezone.now().date()
        self.approval_comments = comments
        self.save()

    def reject(self, user, reason):
        """Reject leave request"""
        self.status = self.Status.REJECTED
        self.rejected_by = user
        self.rejected_date = timezone.now().date()
        self.rejection_reason = reason
        self.save()

    def cancel(self, reason):
        """Cancel leave request"""
        self.status = self.Status.CANCELLED
        self.cancelled_date = timezone.now().date()
        self.cancellation_reason = reason
        self.save()


class PayrollPeriod(models.Model):
    """
    Payroll period management.

    Manages payroll periods and processing.
    """

    class PeriodType(models.TextChoices):
        """Types of payroll periods"""
        WEEKLY = "WEEKLY", "Weekly"
        BIWEEKLY = "BIWEEKLY", "Bi-Weekly"
        SEMIMONTHLY = "SEMIMONTHLY", "Semi-Monthly"
        MONTHLY = "MONTHLY", "Monthly"

    class Status(models.TextChoices):
        """Period status"""
        OPEN = "OPEN", "Open"
        PROCESSING = "PROCESSING", "Processing"
        CLOSED = "CLOSED", "Closed"
        PAID = "PAID", "Paid"

    # Period identification
    period_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Auto-generated: PAY-YYYY-##"
    )

    # Period details
    period_type = models.CharField(
        max_length=20,
        choices=PeriodType.choices,
        default=PeriodType.MONTHLY,
        help_text="Type of payroll period"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        help_text="Period status"
    )

    # Dates
    start_date = models.DateField(
        help_text="Period start date"
    )

    end_date = models.DateField(
        help_text="Period end date"
    )

    pay_date = models.DateField(
        help_text="Pay date"
    )

    # Totals
    total_employees = models.IntegerField(
        default=0,
        help_text="Total employees in period"
    )

    total_gross_pay = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total gross pay"
    )

    total_deductions = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total deductions"
    )

    total_net_pay = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total net pay"
    )

    # Processing
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payroll_periods',
        help_text="Who processed payroll"
    )

    processed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When payroll was processed"
    )

    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_payroll_periods',
        help_text="Who approved payroll"
    )

    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When payroll was approved"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    # Audit
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When period was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When period was last updated"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_payroll_periods',
        help_text="Who created period"
    )

    class Meta:
        db_table = "payroll_periods"
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['pay_date']),
        ]

    def __str__(self):
        return f"{self.period_number} - {self.start_date} to {self.end_date}"

    def save(self, *args, **kwargs):
        if not self.period_number:
            self.period_number = self._generate_period_number()
        super().save(*args, **kwargs)

    def _generate_period_number(self):
        """Generate unique period number: PAY-YYYY-##"""
        year = timezone.now().year
        prefix = f"PAY-{year}-"

        last_period = PayrollPeriod.objects.filter(
            period_number__startswith=prefix
        ).order_by('-period_number').first()

        if last_period:
            try:
                last_num = int(last_period.period_number.split('-')[2])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:02d}"

    @property
    def is_open(self):
        """Check if period is open"""
        return self.status == self.Status.OPEN


# =============================================================================
# LEGACY MODELS (P4 Skeleton - Preserved for Compatibility)
# =============================================================================


class Attendance(models.Model):
    """Legacy P4: Daily attendance records."""

    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LEAVE = "LEAVE", "On Leave"
        HOLIDAY = "HOLIDAY", "Holiday"
        HALF_DAY = "HALF_DAY", "Half Day"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )
    date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT
    )

    first_in = models.TimeField(null=True, blank=True)
    last_out = models.TimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "attendance"
        unique_together = ["user", "date"]
        ordering = ["-date", "user"]
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance Records"

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class AttendancePunch(models.Model):
    """Legacy P4: Individual clock in/out punches."""

    class PunchType(models.TextChoices):
        IN = "IN", "Clock In"
        OUT = "OUT", "Clock Out"

    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.CASCADE,
        related_name="punches"
    )
    punch_type = models.CharField(max_length=10, choices=PunchType.choices)
    punch_time = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "attendance_punches"
        ordering = ["attendance", "punch_time"]

    def __str__(self):
        return f"{self.attendance.user.username} - {self.get_punch_type_display()} at {self.punch_time}"


class LeaveType(models.Model):
    """Legacy P4: Types of leave."""

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    days_per_year = models.IntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "leave_types"
        ordering = ["name"]
        verbose_name = "Leave Type"
        verbose_name_plural = "Leave Types"

    def __str__(self):
        return self.name


class OvertimeRequest(models.Model):
    """Legacy P4: Overtime requests."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="overtime_requests"
    )
    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_overtime"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "overtime_requests"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.hours}h)"
