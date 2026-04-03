"""
Sprint 7: Compliance & Quality Management Models

Models (10 total):
- Week 1: ComplianceRequirement, QualityControl, NonConformance, AuditTrail
- Week 2: DocumentControl, TrainingRecord, Certification
- Week 3: ComplianceReport, QualityMetric, InspectionChecklist
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class ComplianceRequirement(models.Model):
    """Regulatory and standard requirements tracking."""

    class RequirementType(models.TextChoices):
        ISO_STANDARD = "ISO_STANDARD", "ISO Standard"
        API_SPECIFICATION = "API_SPECIFICATION", "API Specification"
        GOVERNMENT_REGULATION = "GOVERNMENT_REGULATION", "Government Regulation"
        CUSTOMER_REQUIREMENT = "CUSTOMER_REQUIREMENT", "Customer Requirement"
        INDUSTRY_STANDARD = "INDUSTRY_STANDARD", "Industry Standard"
        INTERNAL_POLICY = "INTERNAL_POLICY", "Internal Policy"
        ENVIRONMENTAL = "ENVIRONMENTAL", "Environmental Requirement"
        SAFETY = "SAFETY", "Safety Requirement"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        PENDING = "PENDING", "Pending"
        SUPERSEDED = "SUPERSEDED", "Superseded"
        INACTIVE = "INACTIVE", "Inactive"

    class ComplianceStatus(models.TextChoices):
        COMPLIANT = "COMPLIANT", "Compliant"
        PARTIAL = "PARTIAL", "Partially Compliant"
        NON_COMPLIANT = "NON_COMPLIANT", "Non-Compliant"
        NOT_ASSESSED = "NOT_ASSESSED", "Not Yet Assessed"

    requirement_code = models.CharField(max_length=100, unique=True, db_index=True)
    title = models.CharField(max_length=500)
    requirement_type = models.CharField(max_length=30, choices=RequirementType.choices, db_index=True)
    source_document = models.CharField(max_length=200)
    clause_number = models.CharField(max_length=50, blank=True)
    version = models.CharField(max_length=50, blank=True)
    issuing_authority = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    applicable_scope = models.TextField(blank=True)
    compliance_criteria = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    compliance_status = models.CharField(max_length=20, choices=ComplianceStatus.choices, default=ComplianceStatus.NOT_ASSESSED, db_index=True)
    effective_date = models.DateField()
    review_date = models.DateField(null=True, blank=True)
    last_assessment_date = models.DateField(null=True, blank=True)
    superseded_date = models.DateField(null=True, blank=True)
    responsible_person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_requirements')
    responsible_department = models.CharField(max_length=100, blank=True)
    implementation_notes = models.TextField(blank=True)
    verification_method = models.TextField(blank=True)
    documentation_required = models.TextField(blank=True)
    risk_level = models.CharField(max_length=20, choices=[('CRITICAL', 'Critical'), ('HIGH', 'High'), ('MEDIUM', 'Medium'), ('LOW', 'Low')], default='MEDIUM')
    consequences_of_non_compliance = models.TextField(blank=True)
    assessment_frequency = models.CharField(max_length=50, blank=True)
    last_assessed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assessed_requirements')
    assessment_notes = models.TextField(blank=True)
    supersedes = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='superseded_by_requirements')
    related_requirements = models.ManyToManyField('self', blank=True, symmetrical=True)
    reference_url = models.URLField(blank=True)
    internal_procedure = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_compliance_requirements')

    class Meta:
        db_table = "compliance_requirements"
        ordering = ['requirement_code']

    def __str__(self):
        return f"{self.requirement_code} - {self.title}"

    @property
    def is_active(self):
        if self.status != self.Status.ACTIVE:
            return False
        if self.effective_date > timezone.now().date():
            return False
        return True

    @property
    def is_compliant(self):
        return self.compliance_status == self.ComplianceStatus.COMPLIANT


class QualityControl(models.Model):
    """Quality control checks and inspections."""

    class InspectionType(models.TextChoices):
        INCOMING = "INCOMING", "Incoming Inspection"
        IN_PROCESS = "IN_PROCESS", "In-Process Inspection"
        FINAL = "FINAL", "Final Inspection"
        FIELD_INSPECTION = "FIELD_INSPECTION", "Field Inspection"
        SUPPLIER_AUDIT = "SUPPLIER_AUDIT", "Supplier Audit"
        CUSTOMER_WITNESS = "CUSTOMER_WITNESS", "Customer Witness Point"
        CALIBRATION = "CALIBRATION", "Calibration Verification"

    class Result(models.TextChoices):
        PASS = "PASS", "Pass"
        CONDITIONAL_PASS = "CONDITIONAL_PASS", "Conditional Pass"
        FAIL = "FAIL", "Fail"
        PENDING = "PENDING", "Pending"
        WAIVED = "WAIVED", "Waived"

    inspection_number = models.CharField(max_length=50, unique=True, blank=True, db_index=True)
    inspection_type = models.CharField(max_length=25, choices=InspectionType.choices, db_index=True)
    result = models.CharField(max_length=20, choices=Result.choices, default=Result.PENDING, db_index=True)
    work_order = models.ForeignKey('workorders.WorkOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_controls')
    receipt = models.ForeignKey('supplychain.Receipt', on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_controls')
    site_visit = models.ForeignKey('sales.SiteVisit', on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_controls')
    drill_bit = models.ForeignKey('workorders.DrillBit', on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_controls')
    inspection_date = models.DateField()
    inspection_time = models.TimeField(null=True, blank=True)
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='quality_inspections')
    witness = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='witnessed_inspections')
    inspection_checklist = models.ForeignKey('InspectionChecklist', on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_controls')
    compliance_requirement = models.ForeignKey('ComplianceRequirement', on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_controls')
    findings = models.TextField(blank=True)
    defects_found = models.TextField(blank=True)
    measurements = models.JSONField(null=True, blank=True)
    passed_criteria = models.TextField(blank=True)
    failed_criteria = models.TextField(blank=True)
    disposition = models.CharField(max_length=20, choices=[('ACCEPT', 'Accept'), ('REWORK', 'Rework'), ('REPAIR', 'Repair'), ('SCRAP', 'Scrap'), ('RETURN', 'Return'), ('CONDITIONAL', 'Conditional')], blank=True)
    disposition_notes = models.TextField(blank=True)
    corrective_action_required = models.BooleanField(default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_quality_controls')
    approved_at = models.DateTimeField(null=True, blank=True)
    non_conformance = models.ForeignKey('NonConformance', on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_controls')
    photos_attached = models.BooleanField(default=False)
    report_file = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_quality_controls')

    class Meta:
        db_table = "quality_controls"
        ordering = ['-inspection_date', '-inspection_number']

    def __str__(self):
        return f"{self.inspection_number} - {self.get_inspection_type_display()} - {self.get_result_display()}"

    def save(self, *args, **kwargs):
        if not self.inspection_number:
            self.inspection_number = self._generate_inspection_number()
        super().save(*args, **kwargs)

    def _generate_inspection_number(self):
        year = timezone.now().year
        last = QualityControl.objects.filter(inspection_number__startswith=f'QC-{year}-').order_by('-inspection_number').first()
        if last and last.inspection_number:
            try:
                last_num = int(last.inspection_number.split('-')[2])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        return f"QC-{year}-{new_num:06d}"

    @property
    def is_passed(self):
        return self.result in [self.Result.PASS, self.Result.CONDITIONAL_PASS, self.Result.WAIVED]


class NonConformance(models.Model):
    """Non-Conformance Reports (NCR)."""

    class Source(models.TextChoices):
        QUALITY_INSPECTION = "QUALITY_INSPECTION", "Quality Inspection"
        CUSTOMER_COMPLAINT = "CUSTOMER_COMPLAINT", "Customer Complaint"
        INTERNAL_AUDIT = "INTERNAL_AUDIT", "Internal Audit"
        SUPPLIER_ISSUE = "SUPPLIER_ISSUE", "Supplier Issue"
        PROCESS_DEVIATION = "PROCESS_DEVIATION", "Process Deviation"
        EMPLOYEE_REPORT = "EMPLOYEE_REPORT", "Employee Report"
        OTHER = "OTHER", "Other"

    class Severity(models.TextChoices):
        CRITICAL = "CRITICAL", "Critical"
        MAJOR = "MAJOR", "Major"
        MINOR = "MINOR", "Minor"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        INVESTIGATING = "INVESTIGATING", "Investigating"
        CORRECTIVE_ACTION = "CORRECTIVE_ACTION", "Corrective Action"
        VERIFICATION = "VERIFICATION", "Verification"
        CLOSED = "CLOSED", "Closed"
        REJECTED = "REJECTED", "Rejected"

    ncr_number = models.CharField(max_length=50, unique=True, blank=True, db_index=True)
    source = models.CharField(max_length=30, choices=Source.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.OPEN, db_index=True)
    work_order = models.ForeignKey('workorders.WorkOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='non_conformances')
    quality_control = models.ForeignKey('QualityControl', on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_ncrs')
    vendor = models.ForeignKey('supplychain.Vendor', on_delete=models.SET_NULL, null=True, blank=True, related_name='non_conformances')
    description = models.TextField()
    defect_description = models.TextField()
    detected_date = models.DateField()
    reported_date = models.DateField(auto_now_add=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reported_ncrs')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_ncrs')
    root_cause_analysis = models.TextField(blank=True)
    contributing_factors = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    preventive_action = models.TextField(blank=True)
    target_completion_date = models.DateField(null=True, blank=True)
    actual_completion_date = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_ncrs')
    verification_date = models.DateField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    capa = models.ForeignKey('supplychain.CAPA', on_delete=models.SET_NULL, null=True, blank=True, related_name='non_conformances')
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='closed_compliance_ncrs')
    closed_date = models.DateField(null=True, blank=True)
    closure_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "non_conformances"
        ordering = ['-detected_date', '-ncr_number']

    def __str__(self):
        return f"{self.ncr_number} - {self.get_severity_display()} - {self.description[:50]}"

    def save(self, *args, **kwargs):
        if not self.ncr_number:
            self.ncr_number = self._generate_ncr_number()
        super().save(*args, **kwargs)

    def _generate_ncr_number(self):
        year = timezone.now().year
        last = NonConformance.objects.filter(ncr_number__startswith=f'NCR-{year}-').order_by('-ncr_number').first()
        if last and last.ncr_number:
            try:
                last_num = int(last.ncr_number.split('-')[2])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        return f"NCR-{year}-{new_num:04d}"

    @property
    def is_open(self):
        return self.status not in [self.Status.CLOSED, self.Status.REJECTED]


class AuditTrail(models.Model):
    """System-wide audit trail logging."""

    class Action(models.TextChoices):
        CREATED = "CREATED", "Created"
        UPDATED = "UPDATED", "Updated"
        DELETED = "DELETED", "Deleted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        STATUS_CHANGED = "STATUS_CHANGED", "Status Changed"
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        OTHER = "OTHER", "Other"

    action = models.CharField(max_length=30, choices=Action.choices, db_index=True)
    description = models.TextField()
    model_name = models.CharField(max_length=100, db_index=True)
    object_id = models.IntegerField(db_index=True)
    object_repr = models.CharField(max_length=500, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='audit_trail')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    changes = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "audit_trail"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action} - {self.model_name}"


class DocumentControl(models.Model):
    """Controlled document management system."""

    class DocumentType(models.TextChoices):
        PROCEDURE = "PROCEDURE", "Procedure"
        WORK_INSTRUCTION = "WORK_INSTRUCTION", "Work Instruction"
        FORM = "FORM", "Form"
        SPECIFICATION = "SPECIFICATION", "Specification"
        DRAWING = "DRAWING", "Drawing"
        CERTIFICATE = "CERTIFICATE", "Certificate"
        REPORT = "REPORT", "Report"
        POLICY = "POLICY", "Policy"
        MANUAL = "MANUAL", "Manual"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        REVIEW = "REVIEW", "Review"
        APPROVED = "APPROVED", "Approved"
        OBSOLETE = "OBSOLETE", "Obsolete"
        ARCHIVED = "ARCHIVED", "Archived"

    document_number = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=500)
    document_type = models.CharField(max_length=25, choices=DocumentType.choices)
    version = models.CharField(max_length=20)
    revision_date = models.DateField()
    effective_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    prepared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='prepared_documents')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_documents')
    reviewed_date = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_controlled_documents')
    approved_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    scope = models.TextField(blank=True)
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField(null=True, blank=True)
    file_checksum = models.CharField(max_length=64, blank=True)
    supersedes = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='superseded_by_documents')
    change_summary = models.TextField(blank=True)
    controlled_copy = models.BooleanField(default=True)
    distribution_list = models.TextField(blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    review_frequency_months = models.IntegerField(null=True, blank=True)
    compliance_requirements = models.ManyToManyField('ComplianceRequirement', blank=True, related_name='documents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "document_control"
        ordering = ['document_number', '-version']
        unique_together = [['document_number', 'version']]

    def __str__(self):
        return f"{self.document_number} v{self.version} - {self.title}"

    @property
    def is_current(self):
        """Check if document is current (approved status)."""
        return self.status == self.Status.APPROVED


class TrainingRecord(models.Model):
    """Employee training records."""

    class TrainingType(models.TextChoices):
        ORIENTATION = "ORIENTATION", "Orientation"
        SAFETY = "SAFETY", "Safety"
        TECHNICAL = "TECHNICAL", "Technical"
        QUALITY = "QUALITY", "Quality"
        COMPLIANCE = "COMPLIANCE", "Compliance"
        SOFTWARE = "SOFTWARE", "Software"
        ON_THE_JOB = "ON_THE_JOB", "On-the-Job"
        CERTIFICATION = "CERTIFICATION", "Certification"
        REFRESHER = "REFRESHER", "Refresher"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        FAILED = "FAILED", "Failed"

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='training_records')
    training_type = models.CharField(max_length=20, choices=TrainingType.choices)
    training_title = models.CharField(max_length=500)
    training_description = models.TextField(blank=True)
    training_provider = models.CharField(max_length=200)
    instructor_name = models.CharField(max_length=200, blank=True)
    scheduled_date = models.DateField(null=True, blank=True)
    start_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED, db_index=True)
    passed = models.BooleanField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    certificate_issued_date = models.DateField(null=True, blank=True)
    certificate_expiry_date = models.DateField(null=True, blank=True)
    required_for_position = models.BooleanField(default=False)
    compliance_requirement = models.ForeignKey('ComplianceRequirement', on_delete=models.SET_NULL, null=True, blank=True, related_name='training_records')
    training_materials = models.CharField(max_length=500, blank=True)
    completion_certificate_file = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='recorded_training')

    class Meta:
        db_table = "training_records"
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.employee} - {self.training_title} - {self.start_date}"

    @property
    def is_expired(self):
        if not self.certificate_expiry_date:
            return False
        return timezone.now().date() > self.certificate_expiry_date


class Certification(models.Model):
    """Professional certifications tracking."""

    class Status(models.TextChoices):
        CURRENT = "CURRENT", "Current"
        EXPIRED = "EXPIRED", "Expired"
        SUSPENDED = "SUSPENDED", "Suspended"
        REVOKED = "REVOKED", "Revoked"
        PENDING = "PENDING", "Pending"

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='certifications')
    certification_name = models.CharField(max_length=500)
    certification_body = models.CharField(max_length=200)
    certification_number = models.CharField(max_length=100, blank=True)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CURRENT, db_index=True)
    renewal_required = models.BooleanField(default=True)
    renewal_date = models.DateField(null=True, blank=True)
    renewal_requirements = models.TextField(blank=True)
    verification_url = models.URLField(blank=True)
    certificate_file = models.CharField(max_length=500, blank=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_certifications')
    verified_date = models.DateField(null=True, blank=True)
    compliance_requirement = models.ForeignKey('ComplianceRequirement', on_delete=models.SET_NULL, null=True, blank=True, related_name='certifications')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "certifications"
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.employee} - {self.certification_name}"

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return timezone.now().date() > self.expiry_date

    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return None
        return (self.expiry_date - timezone.now().date()).days


class ComplianceReport(models.Model):
    """Compliance reporting."""

    class ReportType(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        ANNUAL = "ANNUAL", "Annual"
        AUDIT = "AUDIT", "Audit"
        AD_HOC = "AD_HOC", "Ad-Hoc"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        REVIEW = "REVIEW", "Review"
        APPROVED = "APPROVED", "Approved"
        PUBLISHED = "PUBLISHED", "Published"

    report_number = models.CharField(max_length=50, unique=True, blank=True, db_index=True)
    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    title = models.CharField(max_length=500)
    reporting_period_start = models.DateField()
    reporting_period_end = models.DateField()
    prepared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='prepared_compliance_reports')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_compliance_reports')
    approved_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    compliance_requirements = models.ManyToManyField('ComplianceRequirement', blank=True, related_name='compliance_reports')
    compliance_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    non_conformances_count = models.IntegerField(default=0)
    requirements_assessed = models.IntegerField(default=0)
    requirements_compliant = models.IntegerField(default=0)
    executive_summary = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    report_file = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "compliance_reports"
        ordering = ['-reporting_period_end']

    def __str__(self):
        return f"{self.report_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.report_number:
            self.report_number = self._generate_report_number()
        super().save(*args, **kwargs)

    def _generate_report_number(self):
        year = timezone.now().year
        prefix = self.report_type[:3] if self.report_type else 'RPT'
        last = ComplianceReport.objects.filter(report_number__startswith=f'{prefix}-{year}-').order_by('-report_number').first()
        if last and last.report_number:
            try:
                last_num = int(last.report_number.split('-')[2])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        return f"{prefix}-{year}-{new_num:04d}"


class QualityMetric(models.Model):
    """Quality KPIs and metrics tracking."""

    class MetricType(models.TextChoices):
        DEFECT_RATE = "DEFECT_RATE", "Defect Rate"
        ON_TIME_DELIVERY = "ON_TIME_DELIVERY", "On-Time Delivery"
        CUSTOMER_SATISFACTION = "CUSTOMER_SATISFACTION", "Customer Satisfaction"
        NCR_RATE = "NCR_RATE", "NCR Rate"
        FIRST_PASS_YIELD = "FIRST_PASS_YIELD", "First Pass Yield"
        REWORK_RATE = "REWORK_RATE", "Rework Rate"
        SCRAP_RATE = "SCRAP_RATE", "Scrap Rate"
        SUPPLIER_QUALITY = "SUPPLIER_QUALITY", "Supplier Quality"
        AUDIT_SCORE = "AUDIT_SCORE", "Audit Score"
        TRAINING_COMPLETION = "TRAINING_COMPLETION", "Training Completion"
        OTHER = "OTHER", "Other"

    class Trend(models.TextChoices):
        IMPROVING = "IMPROVING", "Improving"
        STABLE = "STABLE", "Stable"
        DECLINING = "DECLINING", "Declining"

    metric_name = models.CharField(max_length=200)
    metric_type = models.CharField(max_length=30, choices=MetricType.choices)
    measurement_period = models.DateField()
    measured_value = models.DecimalField(max_digits=10, decimal_places=4)
    unit_of_measure = models.CharField(max_length=50, default='%')
    target_value = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    threshold_warning = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    threshold_critical = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    trend = models.CharField(max_length=20, choices=Trend.choices, blank=True)
    previous_value = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    responsible_person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_metrics')
    data_source = models.CharField(max_length=200, blank=True)
    calculation_method = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='recorded_metrics')

    class Meta:
        db_table = "quality_metrics"
        ordering = ['-measurement_period', 'metric_name']

    def __str__(self):
        return f"{self.metric_name} - {self.measurement_period}: {self.measured_value}{self.unit_of_measure}"

    @property
    def meets_target(self):
        if not self.target_value:
            return None
        return self.measured_value >= self.target_value


class InspectionChecklist(models.Model):
    """Reusable inspection checklist templates."""

    class InspectionType(models.TextChoices):
        INCOMING = "INCOMING", "Incoming"
        IN_PROCESS = "IN_PROCESS", "In-Process"
        FINAL = "FINAL", "Final"
        FIELD = "FIELD", "Field"

    checklist_code = models.CharField(max_length=50, unique=True)
    checklist_name = models.CharField(max_length=500)
    inspection_type = models.CharField(max_length=25, choices=InspectionType.choices)
    applicable_to = models.TextField()
    checklist_items = models.JSONField()
    compliance_requirement = models.ForeignKey('ComplianceRequirement', on_delete=models.SET_NULL, null=True, blank=True, related_name='inspection_checklists')
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_checklists')

    class Meta:
        db_table = "inspection_checklists"
        ordering = ['checklist_code']

    def __str__(self):
        return f"{self.checklist_code} - {self.checklist_name}"

    @property
    def item_count(self):
        if not self.checklist_items:
            return 0
        return len(self.checklist_items)
