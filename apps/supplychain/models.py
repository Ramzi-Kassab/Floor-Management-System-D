"""
ARDT FMS - Supply Chain & Finance Models
Sprint 6: Complete Supply Chain Integration

Models:
Week 1 - Vendor Management & Purchasing:
1. Vendor - Supplier master data with qualification
2. VendorContact - Vendor contact persons
3. PurchaseRequisition - Internal purchase requests
4. PurchaseOrder - Purchase orders to vendors
5. PurchaseOrderLine - PO line items

Week 2 - Receiving & Invoicing:
6. Receipt - Goods/services receipt
7. ReceiptLine - Receipt line items
8. VendorInvoice - Vendor invoices
9. InvoiceLine - Invoice line items
10. InvoiceMatch - Three-way match validation

Week 3 - Costing & Finance:
11. CostAllocation - Job cost tracking
12. ExpenseCategory - Expense classification
13. PaymentTerm - Payment terms master
14. VendorPayment - Payment tracking
15. PaymentAllocation - Payment to invoice allocation

Legacy Models (retained for compatibility):
- Supplier (deprecated - use Vendor)
- CAPA - Corrective and Preventive Actions

Author: Sprint 6 Implementation
Date: December 2024
"""

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


# =============================================================================
# WEEK 1: VENDOR MANAGEMENT & PURCHASING
# =============================================================================


class Vendor(models.Model):
    """
    Supplier and service provider master data.

    Manages vendor information, qualifications, performance metrics,
    and relationships for procurement and supply chain operations.

    Integrates with:
    - PurchaseOrder: Creates purchase orders to vendors
    - VendorInvoice: Receives invoices from vendors
    - VendorPayment: Tracks payments to vendors
    - Receipt: Receives goods/services from vendors

    ISO 9001 References:
    - Clause 8.4: Control of Externally Provided Processes
    - Clause 8.4.1: Supplier Evaluation and Selection

    Author: Sprint 6 Implementation
    Date: December 2024
    """

    class VendorType(models.TextChoices):
        """Types of vendors"""
        MATERIALS_SUPPLIER = "MATERIALS_SUPPLIER", "Materials Supplier"
        PARTS_SUPPLIER = "PARTS_SUPPLIER", "Parts Supplier"
        SERVICE_PROVIDER = "SERVICE_PROVIDER", "Service Provider"
        CONTRACTOR = "CONTRACTOR", "Contractor"
        MANUFACTURER = "MANUFACTURER", "Manufacturer"
        DISTRIBUTOR = "DISTRIBUTOR", "Distributor"
        CONSULTANT = "CONSULTANT", "Consultant"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        """Vendor status"""
        PROSPECT = "PROSPECT", "Prospect - Under evaluation"
        QUALIFIED = "QUALIFIED", "Qualified - Approved for business"
        ACTIVE = "ACTIVE", "Active - Currently doing business"
        INACTIVE = "INACTIVE", "Inactive - Not currently active"
        SUSPENDED = "SUSPENDED", "Suspended - Temporarily blocked"
        DISQUALIFIED = "DISQUALIFIED", "Disqualified - Not approved"

    class QualificationLevel(models.TextChoices):
        """Quality qualification level"""
        NOT_QUALIFIED = "NOT_QUALIFIED", "Not Qualified"
        BASIC = "BASIC", "Basic - Standard products only"
        STANDARD = "STANDARD", "Standard - Most products"
        PREFERRED = "PREFERRED", "Preferred - All products"
        STRATEGIC = "STRATEGIC", "Strategic Partner"

    # ===== IDENTIFICATION =====

    vendor_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique vendor code (auto-generated: VEND-####)"
    )

    name = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Legal vendor/company name"
    )

    name_ar = models.CharField(
        max_length=200,
        blank=True,
        help_text="Vendor name in Arabic"
    )

    dba_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Doing Business As (DBA) name if different"
    )

    # ===== CLASSIFICATION =====

    vendor_type = models.CharField(
        max_length=30,
        choices=VendorType.choices,
        default=VendorType.MATERIALS_SUPPLIER,
        help_text="Primary vendor type/category"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROSPECT,
        db_index=True,
        help_text="Current vendor status"
    )

    qualification_level = models.CharField(
        max_length=20,
        choices=QualificationLevel.choices,
        default=QualificationLevel.NOT_QUALIFIED,
        help_text="Quality qualification level"
    )

    # ===== COMPANY INFORMATION =====

    tax_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Tax ID / VAT number"
    )

    registration_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Business registration number"
    )

    website = models.URLField(
        blank=True,
        help_text="Company website"
    )

    year_established = models.IntegerField(
        null=True,
        blank=True,
        help_text="Year company was established"
    )

    employee_count = models.IntegerField(
        null=True,
        blank=True,
        help_text="Approximate number of employees"
    )

    # ===== ADDRESS =====

    address_line_1 = models.CharField(
        max_length=500,
        help_text="Street address line 1"
    )

    address_line_2 = models.CharField(
        max_length=500,
        blank=True,
        help_text="Street address line 2"
    )

    city = models.CharField(
        max_length=100,
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
        default="Saudi Arabia",
        help_text="Country"
    )

    # ===== CONTACT INFORMATION =====

    phone = models.CharField(
        max_length=50,
        help_text="Main phone number"
    )

    fax = models.CharField(
        max_length=50,
        blank=True,
        help_text="Fax number"
    )

    email = models.EmailField(
        help_text="Main email address"
    )

    accounts_payable_email = models.EmailField(
        blank=True,
        help_text="AP/invoicing email address"
    )

    # ===== PAYMENT TERMS =====

    default_payment_term = models.ForeignKey(
        'PaymentTerm',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendors',
        help_text="Default payment terms for this vendor"
    )

    currency_code = models.CharField(
        max_length=3,
        default='USD',
        help_text="Default currency (ISO 4217 code)"
    )

    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Credit limit amount"
    )

    # ===== PERFORMANCE METRICS =====

    on_time_delivery_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="On-time delivery percentage"
    )

    quality_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Quality rating (1-5 scale)"
    )

    total_purchase_orders = models.IntegerField(
        default=0,
        help_text="Total number of POs issued"
    )

    total_purchase_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total value of all purchases"
    )

    last_purchase_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last purchase order"
    )

    # ===== CAPABILITIES =====

    product_categories = models.TextField(
        blank=True,
        help_text="Products/services this vendor can supply"
    )

    certifications = models.TextField(
        blank=True,
        help_text="Quality certifications (ISO, API, etc.)"
    )

    capabilities = models.TextField(
        blank=True,
        help_text="Special capabilities or expertise"
    )

    minimum_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum order value required"
    )

    lead_time_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Typical lead time in days"
    )

    # ===== QUALIFICATION =====

    qualification_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date vendor was qualified"
    )

    qualification_expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date qualification expires"
    )

    qualified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qualified_vendors',
        help_text="User who qualified this vendor"
    )

    qualification_notes = models.TextField(
        blank=True,
        help_text="Notes on qualification process and criteria"
    )

    # ===== STATUS MANAGEMENT =====

    active_since = models.DateField(
        null=True,
        blank=True,
        help_text="Date vendor became active"
    )

    inactive_since = models.DateField(
        null=True,
        blank=True,
        help_text="Date vendor became inactive"
    )

    suspension_reason = models.TextField(
        blank=True,
        help_text="Reason for suspension if applicable"
    )

    # ===== INSURANCE & COMPLIANCE =====

    insurance_certificate_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Insurance certificate number"
    )

    insurance_expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Insurance expiry date"
    )

    liability_coverage_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Liability insurance coverage amount"
    )

    compliance_documents_verified = models.BooleanField(
        default=False,
        help_text="Whether compliance documents have been verified"
    )

    # ===== BANKING (for payments) =====

    bank_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Bank name for payments"
    )

    bank_account_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Bank account number"
    )

    bank_routing_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Bank routing/SWIFT code"
    )

    iban = models.CharField(
        max_length=50,
        blank=True,
        help_text="IBAN for international transfers"
    )

    # ===== NOTES =====

    internal_notes = models.TextField(
        blank=True,
        help_text="Internal notes (not visible to vendor)"
    )

    purchasing_notes = models.TextField(
        blank=True,
        help_text="Notes for purchasing team"
    )

    # ===== AUDIT TRAIL =====

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When vendor was added to system"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When vendor was last updated"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_vendors',
        help_text="User who created vendor record"
    )

    class Meta:
        db_table = "vendors"
        ordering = ['name']
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"
        indexes = [
            models.Index(fields=['vendor_code']),
            models.Index(fields=['status', 'qualification_level']),
            models.Index(fields=['vendor_type', 'status']),
            models.Index(fields=['name']),
        ]
        permissions = [
            ("can_qualify_vendors", "Can qualify and approve vendors"),
            ("can_suspend_vendors", "Can suspend vendors"),
            ("can_view_vendor_financials", "Can view vendor financial data"),
        ]

    def __str__(self):
        return f"{self.vendor_code} - {self.name}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate vendor code"""
        if not self.vendor_code:
            self.vendor_code = self._generate_vendor_code()
        super().save(*args, **kwargs)

    def _generate_vendor_code(self):
        """Generate unique vendor code: VEND-####"""
        last_vendor = Vendor.objects.filter(
            vendor_code__startswith='VEND-'
        ).order_by('-vendor_code').first()

        if last_vendor:
            try:
                last_num = int(last_vendor.vendor_code.split('-')[1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"VEND-{new_num:04d}"

    # ===== PROPERTIES =====

    @property
    def is_active(self):
        """Check if vendor is currently active"""
        return self.status == self.Status.ACTIVE

    @property
    def is_qualified(self):
        """Check if vendor is qualified"""
        return self.qualification_level != self.QualificationLevel.NOT_QUALIFIED

    @property
    def can_receive_orders(self):
        """Check if vendor can receive purchase orders"""
        return (
            self.status in [self.Status.QUALIFIED, self.Status.ACTIVE] and
            self.is_qualified
        )

    @property
    def qualification_is_expired(self):
        """Check if qualification has expired"""
        if not self.qualification_expiry_date:
            return False
        return timezone.now().date() > self.qualification_expiry_date

    @property
    def insurance_is_expired(self):
        """Check if insurance has expired"""
        if not self.insurance_expiry_date:
            return None
        return timezone.now().date() > self.insurance_expiry_date

    @property
    def average_order_value(self):
        """Calculate average purchase order value"""
        if self.total_purchase_orders == 0:
            return Decimal('0.00')
        return self.total_purchase_value / self.total_purchase_orders

    # ===== METHODS =====

    def qualify(self, level, user, notes='', expiry_date=None):
        """Qualify vendor at specified level."""
        self.qualification_level = level
        self.qualification_date = timezone.now().date()
        self.qualification_expiry_date = expiry_date
        self.qualified_by = user
        self.qualification_notes = notes

        if self.status == self.Status.PROSPECT:
            self.status = self.Status.QUALIFIED

        self.save()

    def activate(self):
        """Activate vendor for business"""
        if not self.is_qualified:
            raise ValidationError("Cannot activate unqualified vendor")

        self.status = self.Status.ACTIVE
        self.active_since = timezone.now().date()
        self.inactive_since = None
        self.save()

    def deactivate(self):
        """Deactivate vendor"""
        self.status = self.Status.INACTIVE
        self.inactive_since = timezone.now().date()
        self.save()

    def suspend(self, reason):
        """Suspend vendor from business."""
        self.status = self.Status.SUSPENDED
        self.suspension_reason = reason
        self.save()


class VendorContact(models.Model):
    """
    Contact persons at vendor organizations.

    Manages contact information for vendor personnel including
    buyers, sales reps, technical support, and account managers.

    ISO 9001 Reference:
    - Clause 8.4.3: Information for External Providers
    """

    class ContactType(models.TextChoices):
        """Types of vendor contacts"""
        SALES = "SALES", "Sales Representative"
        PURCHASING = "PURCHASING", "Purchasing/Buyer"
        TECHNICAL = "TECHNICAL", "Technical Support"
        ACCOUNT_MANAGER = "ACCOUNT_MANAGER", "Account Manager"
        BILLING = "BILLING", "Billing/Accounts Receivable"
        QUALITY = "QUALITY", "Quality Manager"
        LOGISTICS = "LOGISTICS", "Logistics/Shipping"
        EXECUTIVE = "EXECUTIVE", "Executive"
        OTHER = "OTHER", "Other"

    # ===== VENDOR RELATIONSHIP =====

    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.CASCADE,
        related_name='contacts',
        help_text="Vendor this contact belongs to"
    )

    # ===== CONTACT INFORMATION =====

    first_name = models.CharField(
        max_length=100,
        help_text="Contact first name"
    )

    last_name = models.CharField(
        max_length=100,
        help_text="Contact last name"
    )

    title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Job title"
    )

    contact_type = models.CharField(
        max_length=20,
        choices=ContactType.choices,
        default=ContactType.SALES,
        help_text="Type of contact"
    )

    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="Department"
    )

    # ===== CONTACT DETAILS =====

    email = models.EmailField(
        help_text="Email address"
    )

    phone = models.CharField(
        max_length=50,
        help_text="Phone number"
    )

    mobile = models.CharField(
        max_length=50,
        blank=True,
        help_text="Mobile number"
    )

    fax = models.CharField(
        max_length=50,
        blank=True,
        help_text="Fax number"
    )

    # ===== STATUS =====

    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the primary contact?"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Is this contact still active?"
    )

    receive_purchase_orders = models.BooleanField(
        default=False,
        help_text="Send purchase orders to this contact"
    )

    receive_invoices = models.BooleanField(
        default=False,
        help_text="Send invoice-related communications to this contact"
    )

    receive_quality_notices = models.BooleanField(
        default=False,
        help_text="Send quality notifications to this contact"
    )

    # ===== PREFERENCES =====

    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ('EMAIL', 'Email'),
            ('PHONE', 'Phone'),
            ('MOBILE', 'Mobile'),
        ],
        default='EMAIL',
        help_text="Preferred method of contact"
    )

    language_preference = models.CharField(
        max_length=10,
        default='EN',
        help_text="Language preference (ISO code)"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Notes about this contact"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_vendor_contacts'
    )

    class Meta:
        db_table = "vendor_contacts"
        ordering = ['vendor__name', 'last_name', 'first_name']
        verbose_name = "Vendor Contact"
        verbose_name_plural = "Vendor Contacts"
        indexes = [
            models.Index(fields=['vendor', 'is_primary']),
            models.Index(fields=['vendor', 'contact_type']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.vendor.name}) - {self.get_contact_type_display()}"

    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"

    @property
    def name_with_title(self):
        """Get name with title"""
        if self.title:
            return f"{self.full_name}, {self.title}"
        return self.full_name

    def make_primary(self):
        """Make this contact the primary contact"""
        self.vendor.contacts.filter(is_primary=True).update(is_primary=False)
        self.is_primary = True
        self.save()


class PurchaseRequisition(models.Model):
    """
    Internal purchase requisitions.

    Workflow: DRAFT → SUBMITTED → APPROVED → CONVERTED_TO_PO

    Manages internal requests for purchasing before converting
    to actual purchase orders. Supports approval workflow.

    ISO 9001 Reference:
    - Clause 8.4.1: Determination of requirements for external providers
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted for Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CONVERTED_TO_PO = "CONVERTED_TO_PO", "Converted to PO"
        CANCELLED = "CANCELLED", "Cancelled"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    # ===== IDENTIFICATION =====

    requisition_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique requisition number (auto-generated: REQ-YYYY-####)"
    )

    # ===== REQUESTOR INFORMATION =====

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='requisitions_requested',
        help_text="User who requested the purchase"
    )

    department = models.CharField(
        max_length=100,
        help_text="Requesting department"
    )

    # ===== REQUEST DETAILS =====

    title = models.CharField(
        max_length=200,
        help_text="Brief title for the requisition"
    )

    description = models.TextField(
        help_text="Detailed description of what is needed"
    )

    justification = models.TextField(
        blank=True,
        help_text="Business justification for the purchase"
    )

    # ===== STATUS AND PRIORITY =====

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Current requisition status"
    )

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text="Request priority"
    )

    # ===== DATES =====

    request_date = models.DateField(
        help_text="Date requisition was created"
    )

    required_date = models.DateField(
        help_text="Date items are needed by"
    )

    # ===== APPROVAL WORKFLOW =====

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When submitted for approval"
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requisitions_approved',
        help_text="User who approved"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When approved"
    )

    approval_notes = models.TextField(
        blank=True,
        help_text="Approval notes"
    )

    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requisitions_rejected',
        help_text="User who rejected"
    )

    rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When rejected"
    )

    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection"
    )

    # ===== CONVERSION TO PO =====

    converted_to_po = models.ForeignKey(
        'PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_requisitions',
        help_text="PO created from this requisition"
    )

    converted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When converted to PO"
    )

    # ===== RELATED ENTITIES =====

    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_requisitions',
        help_text="Work order this requisition supports"
    )

    # ===== BUDGET TRACKING =====

    estimated_total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated total cost"
    )

    budget_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Budget code for allocation"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "purchase_requisitions"
        ordering = ['-request_date', '-requisition_number']
        verbose_name = "Purchase Requisition"
        verbose_name_plural = "Purchase Requisitions"
        indexes = [
            models.Index(fields=['requisition_number']),
            models.Index(fields=['status']),
            models.Index(fields=['requested_by', 'status']),
        ]

    def __str__(self):
        return f"{self.requisition_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.requisition_number:
            self.requisition_number = self._generate_requisition_number()
        super().save(*args, **kwargs)

    def _generate_requisition_number(self):
        """Generate unique requisition number: REQ-YYYY-####"""
        year = timezone.now().year
        last_req = PurchaseRequisition.objects.filter(
            requisition_number__startswith=f"REQ-{year}-"
        ).order_by('-requisition_number').first()

        if last_req:
            try:
                last_num = int(last_req.requisition_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"REQ-{year}-{new_num:04d}"

    def submit(self):
        """Submit for approval"""
        if self.status != self.Status.DRAFT:
            raise ValidationError("Can only submit draft requisitions")
        self.status = self.Status.SUBMITTED
        self.submitted_at = timezone.now()
        self.save()

    def approve(self, user, notes=''):
        """Approve requisition"""
        if self.status != self.Status.SUBMITTED:
            raise ValidationError("Can only approve submitted requisitions")
        self.status = self.Status.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()

    def reject(self, user, reason):
        """Reject requisition"""
        if self.status != self.Status.SUBMITTED:
            raise ValidationError("Can only reject submitted requisitions")
        self.status = self.Status.REJECTED
        self.rejected_by = user
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        self.save()


class PurchaseRequisitionLine(models.Model):
    """Purchase Requisition line items"""

    requisition = models.ForeignKey(
        'PurchaseRequisition',
        on_delete=models.CASCADE,
        related_name='lines',
        help_text="Parent requisition"
    )

    line_number = models.IntegerField(
        help_text="Line sequence number"
    )

    # ===== ITEM DETAILS =====

    item_description = models.CharField(
        max_length=500,
        help_text="Description of item/service"
    )

    part_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Part number if known"
    )

    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requisition_lines',
        help_text="Link to inventory item"
    )

    # ===== QUANTITIES =====

    quantity_requested = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text="Quantity requested"
    )

    unit_of_measure = models.CharField(
        max_length=20,
        help_text="Unit of measure"
    )

    # ===== PRICING =====

    estimated_unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Estimated unit price"
    )

    estimated_line_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated line total"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Line notes"
    )

    class Meta:
        db_table = "purchase_requisition_lines"
        ordering = ['requisition', 'line_number']
        unique_together = [['requisition', 'line_number']]

    def __str__(self):
        return f"{self.requisition.requisition_number} - Line {self.line_number}"


class PurchaseOrder(models.Model):
    """
    Purchase orders issued to vendors.

    Workflow: DRAFT → APPROVED → SENT → ACKNOWLEDGED → COMPLETED

    Main purchasing document for procuring goods and services.
    Supports approval workflow and three-way matching.

    ISO 9001 Reference:
    - Clause 8.4.2: Type and extent of control of external provision
    - Clause 8.4.3: Information for external providers
    """

    class OrderType(models.TextChoices):
        STANDARD = "STANDARD", "Standard Purchase Order"
        BLANKET = "BLANKET", "Blanket PO (Framework Agreement)"
        CONTRACT = "CONTRACT", "Contract PO"
        SERVICE = "SERVICE", "Service Order"
        RENTAL = "RENTAL", "Equipment Rental"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        SENT = "SENT", "Sent to Vendor"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged by Vendor"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED", "Partially Received"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        CLOSED = "CLOSED", "Closed"

    # ===== IDENTIFICATION =====

    po_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique PO number (auto-generated: PO-YYYY-######)"
    )

    # ===== VENDOR INFORMATION =====

    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        help_text="Vendor to purchase from"
    )

    vendor_contact = models.ForeignKey(
        'VendorContact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders',
        help_text="Vendor contact person"
    )

    # ===== ORDER DETAILS =====

    order_type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.STANDARD,
        help_text="Type of purchase order"
    )

    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Current PO status"
    )

    # ===== DATES =====

    order_date = models.DateField(
        help_text="Date PO was created"
    )

    required_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date items are needed"
    )

    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected delivery date from vendor"
    )

    # ===== DELIVERY LOCATION =====

    ship_to_site = models.ForeignKey(
        'sales.ServiceSite',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='purchase_orders',
        help_text="Delivery location"
    )

    ship_to_address = models.TextField(
        blank=True,
        help_text="Delivery address if not to a site"
    )

    shipping_instructions = models.TextField(
        blank=True,
        help_text="Special shipping instructions"
    )

    # ===== PAYMENT TERMS =====

    payment_term = models.ForeignKey(
        'PaymentTerm',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='purchase_orders',
        help_text="Payment terms"
    )

    # ===== FINANCIAL =====

    currency_code = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency"
    )

    subtotal_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Subtotal before tax"
    )

    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Tax amount"
    )

    shipping_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Shipping/freight amount"
    )

    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Discount amount"
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total PO amount"
    )

    # ===== APPROVAL WORKFLOW =====

    submitted_for_approval_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When submitted for approval"
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchase_orders',
        help_text="User who approved"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When approved"
    )

    # ===== VENDOR ACKNOWLEDGMENT =====

    sent_to_vendor_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When sent to vendor"
    )

    acknowledged_by_vendor = models.BooleanField(
        default=False,
        help_text="Has vendor acknowledged?"
    )

    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When vendor acknowledged"
    )

    vendor_reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Vendor's reference/confirmation number"
    )

    # ===== RELATED ENTITIES =====

    requisition = models.ForeignKey(
        'PurchaseRequisition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders',
        help_text="Source requisition"
    )

    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='po_orders',
        help_text="Related work order"
    )

    # ===== TERMS AND CONDITIONS =====

    terms_and_conditions = models.TextField(
        blank=True,
        help_text="Terms and conditions"
    )

    special_instructions = models.TextField(
        blank=True,
        help_text="Special instructions for vendor"
    )

    # ===== NOTES =====

    internal_notes = models.TextField(
        blank=True,
        help_text="Internal notes (not sent to vendor)"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_pos',
        help_text="User who created PO"
    )

    class Meta:
        db_table = "purchase_orders_v2"
        ordering = ['-order_date', '-po_number']
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"
        indexes = [
            models.Index(fields=['po_number']),
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['order_date']),
            models.Index(fields=['status']),
        ]
        permissions = [
            ("can_approve_purchase_orders", "Can approve purchase orders"),
            ("can_send_purchase_orders", "Can send POs to vendors"),
        ]

    def __str__(self):
        return f"{self.po_number} - {self.vendor.name}"

    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = self._generate_po_number()
        super().save(*args, **kwargs)

    def _generate_po_number(self):
        """Generate unique PO number: PO-YYYY-######"""
        year = timezone.now().year
        last_po = PurchaseOrder.objects.filter(
            po_number__startswith=f"PO-{year}-"
        ).order_by('-po_number').first()

        if last_po:
            try:
                last_num = int(last_po.po_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"PO-{year}-{new_num:06d}"

    def calculate_totals(self):
        """Recalculate PO totals from lines"""
        lines = self.lines.filter(is_cancelled=False)
        self.subtotal_amount = sum(line.line_total or Decimal('0.00') for line in lines)
        self.total_amount = self.subtotal_amount + self.tax_amount + self.shipping_amount - self.discount_amount
        self.save()

    @property
    def is_fully_received(self):
        """Check if all lines are fully received"""
        return all(line.is_fully_received for line in self.lines.filter(is_cancelled=False))


class PurchaseOrderLine(models.Model):
    """Individual line items on purchase orders."""

    # ===== PARENT PO =====

    purchase_order = models.ForeignKey(
        'PurchaseOrder',
        on_delete=models.CASCADE,
        related_name='lines',
        help_text="Parent purchase order"
    )

    line_number = models.IntegerField(
        help_text="Line sequence number"
    )

    # ===== ITEM IDENTIFICATION =====

    item_description = models.CharField(
        max_length=500,
        help_text="Item description"
    )

    part_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Internal part number"
    )

    manufacturer_part_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Manufacturer's part number"
    )

    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_order_lines',
        help_text="Link to inventory item"
    )

    # ===== QUANTITIES =====

    quantity_ordered = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text="Quantity ordered"
    )

    quantity_received = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        help_text="Quantity received so far"
    )

    quantity_invoiced = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        help_text="Quantity invoiced so far"
    )

    unit_of_measure = models.CharField(
        max_length=20,
        help_text="Unit of measure"
    )

    # ===== PRICING =====

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Unit price"
    )

    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Line discount percentage"
    )

    tax_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Tax percentage"
    )

    line_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Line total (calculated)"
    )

    # ===== DELIVERY =====

    required_date = models.DateField(
        help_text="Line required date"
    )

    promised_date = models.DateField(
        null=True,
        blank=True,
        help_text="Vendor promised date"
    )

    # ===== STATUS TRACKING =====

    is_cancelled = models.BooleanField(
        default=False,
        help_text="Is line cancelled?"
    )

    is_closed = models.BooleanField(
        default=False,
        help_text="Is line closed (manually or fully received)?"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Line notes"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "purchase_order_lines_v2"
        ordering = ['purchase_order', 'line_number']
        unique_together = [['purchase_order', 'line_number']]

    def __str__(self):
        return f"{self.purchase_order.po_number} - Line {self.line_number}: {self.item_description[:50]}"

    def save(self, *args, **kwargs):
        self.calculate_line_total()
        super().save(*args, **kwargs)

    def calculate_line_total(self):
        """Calculate line total"""
        base = self.quantity_ordered * self.unit_price
        discount = base * (self.discount_percent / 100)
        self.line_total = base - discount

    @property
    def quantity_outstanding(self):
        """Calculate outstanding quantity to receive"""
        return self.quantity_ordered - self.quantity_received

    @property
    def is_fully_received(self):
        """Check if line is fully received"""
        return self.quantity_received >= self.quantity_ordered


# =============================================================================
# WEEK 2: RECEIVING & INVOICING
# =============================================================================


class Receipt(models.Model):
    """
    Receipts of goods/services from vendors.

    Workflow: DRAFT → INSPECTING → ACCEPTED/REJECTED → COMPLETED

    Records receipt of items ordered via purchase orders.

    ISO 9001 Reference:
    - Clause 8.6: Release of products and services
    """

    class ReceiptType(models.TextChoices):
        GOODS = "GOODS", "Goods Receipt"
        SERVICES = "SERVICES", "Services Receipt"
        RETURN = "RETURN", "Return from Customer"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        INSPECTING = "INSPECTING", "Under Inspection"
        ACCEPTED = "ACCEPTED", "Accepted"
        PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED", "Partially Accepted"
        REJECTED = "REJECTED", "Rejected"
        COMPLETED = "COMPLETED", "Completed"

    # ===== IDENTIFICATION =====

    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique receipt number (auto-generated: RCP-YYYY-######)"
    )

    # ===== PURCHASE ORDER REFERENCE =====

    purchase_order = models.ForeignKey(
        'PurchaseOrder',
        on_delete=models.PROTECT,
        related_name='receipts',
        help_text="Related purchase order"
    )

    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.PROTECT,
        related_name='receipts',
        help_text="Vendor who delivered"
    )

    # ===== RECEIPT DETAILS =====

    receipt_type = models.CharField(
        max_length=20,
        choices=ReceiptType.choices,
        default=ReceiptType.GOODS,
        help_text="Type of receipt"
    )

    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Receipt status"
    )

    # ===== DATES =====

    receipt_date = models.DateField(
        help_text="Date of receipt"
    )

    expected_receipt_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected delivery date"
    )

    # ===== SHIPPING INFORMATION =====

    packing_slip_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Vendor's packing slip number"
    )

    carrier = models.CharField(
        max_length=100,
        blank=True,
        help_text="Shipping carrier"
    )

    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Tracking number"
    )

    # ===== RECEIVED BY =====

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='goods_received',
        help_text="User who received goods"
    )

    # ===== INSPECTION =====

    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receipts_inspected',
        help_text="User who performed inspection"
    )

    inspection_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of inspection"
    )

    inspection_notes = models.TextField(
        blank=True,
        help_text="Inspection notes"
    )

    # ===== QUALITY =====

    quality_acceptable = models.BooleanField(
        null=True,
        blank=True,
        help_text="Overall quality acceptable?"
    )

    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection if applicable"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="General notes"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "receipts"
        ordering = ['-receipt_date', '-receipt_number']
        verbose_name = "Receipt"
        verbose_name_plural = "Receipts"
        indexes = [
            models.Index(fields=['receipt_number']),
            models.Index(fields=['purchase_order', 'status']),
            models.Index(fields=['receipt_date']),
        ]

    def __str__(self):
        return f"{self.receipt_number} - PO {self.purchase_order.po_number}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self._generate_receipt_number()
        super().save(*args, **kwargs)

    def _generate_receipt_number(self):
        """Generate unique receipt number: RCP-YYYY-######"""
        year = timezone.now().year
        last_rcp = Receipt.objects.filter(
            receipt_number__startswith=f"RCP-{year}-"
        ).order_by('-receipt_number').first()

        if last_rcp:
            try:
                last_num = int(last_rcp.receipt_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"RCP-{year}-{new_num:06d}"


class ReceiptLine(models.Model):
    """Individual items received on a receipt."""

    receipt = models.ForeignKey(
        'Receipt',
        on_delete=models.CASCADE,
        related_name='lines',
        help_text="Parent receipt"
    )

    line_number = models.IntegerField(
        help_text="Line sequence number"
    )

    po_line = models.ForeignKey(
        'PurchaseOrderLine',
        on_delete=models.PROTECT,
        related_name='receipt_lines',
        help_text="Related PO line"
    )

    # ===== QUANTITIES =====

    quantity_received = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text="Quantity received"
    )

    quantity_accepted = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        help_text="Quantity accepted after inspection"
    )

    quantity_rejected = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        help_text="Quantity rejected"
    )

    # ===== INSPECTION =====

    inspection_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Inspection'),
            ('PASSED', 'Passed'),
            ('FAILED', 'Failed'),
            ('PARTIAL', 'Partially Passed'),
        ],
        default='PENDING',
        help_text="Inspection status"
    )

    defect_description = models.TextField(
        blank=True,
        help_text="Description of any defects"
    )

    # ===== STORAGE =====

    storage_location_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Storage location code where items were stored"
    )

    lot_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Lot/batch number"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Line notes"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "receipt_lines"
        ordering = ['receipt', 'line_number']
        unique_together = [['receipt', 'line_number']]

    def __str__(self):
        return f"{self.receipt.receipt_number} - Line {self.line_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update PO line received quantity
        self.po_line.quantity_received = sum(
            rl.quantity_accepted for rl in self.po_line.receipt_lines.all()
        )
        self.po_line.save()


class VendorInvoice(models.Model):
    """
    Invoices received from vendors for payment.

    Workflow: PENDING → MATCHED → APPROVED → PAID

    Supports three-way matching: PO + Receipt + Invoice

    ISO 9001 Reference:
    - Clause 8.4.3: Information for external providers (payment)
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Review"
        MATCHED = "MATCHED", "Matched to PO/Receipt"
        MATCH_EXCEPTION = "MATCH_EXCEPTION", "Matching Exception"
        APPROVED = "APPROVED", "Approved for Payment"
        REJECTED = "REJECTED", "Rejected"
        PAID = "PAID", "Paid"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partially Paid"

    # ===== IDENTIFICATION =====

    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Internal invoice number (auto-generated: INV-YYYY-######)"
    )

    vendor_invoice_number = models.CharField(
        max_length=100,
        help_text="Vendor's invoice number"
    )

    # ===== VENDOR =====

    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.PROTECT,
        related_name='vendor_invoices',
        help_text="Vendor who sent invoice"
    )

    # ===== REFERENCES =====

    purchase_order = models.ForeignKey(
        'PurchaseOrder',
        on_delete=models.PROTECT,
        related_name='vendor_invoices',
        help_text="Related purchase order"
    )

    # ===== DATES =====

    invoice_date = models.DateField(
        help_text="Invoice date"
    )

    due_date = models.DateField(
        help_text="Payment due date"
    )

    received_date = models.DateField(
        help_text="Date invoice was received"
    )

    # ===== AMOUNTS =====

    currency_code = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency"
    )

    subtotal_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Subtotal before tax"
    )

    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Tax amount"
    )

    shipping_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Shipping/freight"
    )

    other_charges = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Other charges"
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total invoice amount"
    )

    amount_paid = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount paid so far"
    )

    # ===== STATUS =====

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="Invoice status"
    )

    # ===== MATCHING =====

    is_matched = models.BooleanField(
        default=False,
        help_text="Has invoice been matched?"
    )

    match_exception_reason = models.TextField(
        blank=True,
        help_text="Reason for match exception"
    )

    # ===== APPROVAL =====

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_vendor_invoices',
        help_text="User who approved"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When approved"
    )

    # ===== PAYMENT TERMS =====

    payment_term = models.ForeignKey(
        'PaymentTerm',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='vendor_invoices',
        help_text="Payment terms"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Notes"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_vendor_invoices'
    )

    class Meta:
        db_table = "vendor_invoices"
        ordering = ['-invoice_date']
        verbose_name = "Vendor Invoice"
        verbose_name_plural = "Vendor Invoices"
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.vendor.name} - {self.total_amount}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self._generate_invoice_number()
        super().save(*args, **kwargs)

    def _generate_invoice_number(self):
        """Generate unique invoice number: INV-YYYY-######"""
        year = timezone.now().year
        last_inv = VendorInvoice.objects.filter(
            invoice_number__startswith=f"INV-{year}-"
        ).order_by('-invoice_number').first()

        if last_inv:
            try:
                last_num = int(last_inv.invoice_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"INV-{year}-{new_num:06d}"

    @property
    def amount_outstanding(self):
        """Calculate outstanding balance"""
        return self.total_amount - self.amount_paid

    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return timezone.now().date() > self.due_date and self.status not in ['PAID', 'REJECTED']


class InvoiceLine(models.Model):
    """Line items on vendor invoices."""

    vendor_invoice = models.ForeignKey(
        'VendorInvoice',
        on_delete=models.CASCADE,
        related_name='lines',
        help_text="Parent invoice"
    )

    line_number = models.IntegerField(
        help_text="Line sequence number"
    )

    # ===== MATCHING =====

    po_line = models.ForeignKey(
        'PurchaseOrderLine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_lines',
        help_text="Matched PO line"
    )

    receipt_line = models.ForeignKey(
        'ReceiptLine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_lines',
        help_text="Matched receipt line"
    )

    # ===== ITEM DETAILS =====

    description = models.CharField(
        max_length=500,
        help_text="Item description"
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text="Quantity invoiced"
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        help_text="Unit price"
    )

    line_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Line total"
    )

    # ===== VARIANCE =====

    variance_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Variance from PO (if any)"
    )

    variance_reason = models.TextField(
        blank=True,
        help_text="Reason for variance"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Line notes"
    )

    class Meta:
        db_table = "invoice_lines"
        ordering = ['vendor_invoice', 'line_number']
        unique_together = [['vendor_invoice', 'line_number']]

    def __str__(self):
        return f"{self.vendor_invoice.invoice_number} - Line {self.line_number}"


class InvoiceMatch(models.Model):
    """Three-way match validation between PO, Receipt, and Invoice."""

    class MatchStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Match"
        MATCHED = "MATCHED", "Matched"
        EXCEPTION = "EXCEPTION", "Exception"
        RESOLVED = "RESOLVED", "Exception Resolved"

    vendor_invoice = models.ForeignKey(
        'VendorInvoice',
        on_delete=models.CASCADE,
        related_name='matches',
        help_text="Invoice being matched"
    )

    purchase_order = models.ForeignKey(
        'PurchaseOrder',
        on_delete=models.PROTECT,
        related_name='invoice_matches',
        help_text="PO being matched"
    )

    receipt = models.ForeignKey(
        'Receipt',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_matches',
        help_text="Receipt being matched"
    )

    # ===== MATCH RESULTS =====

    match_status = models.CharField(
        max_length=20,
        choices=MatchStatus.choices,
        default=MatchStatus.PENDING,
        help_text="Match status"
    )

    price_variance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Price variance (Invoice - PO)"
    )

    quantity_variance = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0.000'),
        help_text="Quantity variance"
    )

    price_variance_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Price variance percentage"
    )

    # ===== MATCHING DETAILS =====

    match_performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invoice_matches_performed',
        help_text="User who performed match"
    )

    match_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When match was performed"
    )

    # ===== EXCEPTION HANDLING =====

    exception_notes = models.TextField(
        blank=True,
        help_text="Notes on exception"
    )

    resolution_notes = models.TextField(
        blank=True,
        help_text="How exception was resolved"
    )

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_matches_resolved',
        help_text="User who resolved exception"
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When exception was resolved"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoice_matches"
        verbose_name = "Invoice Match"
        verbose_name_plural = "Invoice Matches"

    def __str__(self):
        return f"Match: {self.vendor_invoice.invoice_number} - {self.match_status}"


# =============================================================================
# WEEK 3: COSTING & FINANCE
# =============================================================================


class ExpenseCategory(models.Model):
    """Expense classification for cost tracking."""

    category_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique category code"
    )

    category_name = models.CharField(
        max_length=100,
        help_text="Category name"
    )

    parent_category = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories',
        help_text="Parent category for hierarchy"
    )

    description = models.TextField(
        blank=True,
        help_text="Category description"
    )

    gl_account_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="GL account for posting"
    )

    is_billable = models.BooleanField(
        default=False,
        help_text="Can be billed to customer?"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Is category active?"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "expense_categories"
        ordering = ['category_code']
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"

    def __str__(self):
        return f"{self.category_code} - {self.category_name}"


class CostAllocation(models.Model):
    """Cost allocation to work orders and jobs."""

    class CostType(models.TextChoices):
        MATERIAL = "MATERIAL", "Material Cost"
        LABOR = "LABOR", "Labor Cost"
        OVERHEAD = "OVERHEAD", "Overhead Cost"
        EQUIPMENT = "EQUIPMENT", "Equipment Cost"
        SUBCONTRACTOR = "SUBCONTRACTOR", "Subcontractor Cost"
        OTHER = "OTHER", "Other Cost"

    # ===== IDENTIFICATION =====

    allocation_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique allocation number (auto-generated: COST-YYYY-####)"
    )

    # ===== COST DETAILS =====

    cost_type = models.CharField(
        max_length=20,
        choices=CostType.choices,
        help_text="Type of cost"
    )

    description = models.CharField(
        max_length=500,
        help_text="Cost description"
    )

    # ===== ALLOCATION TARGET =====

    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cost_allocations',
        help_text="Work order to allocate cost to"
    )

    drill_bit = models.ForeignKey(
        'workorders.DrillBit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cost_allocations',
        help_text="Related drill bit"
    )

    # ===== COST INFORMATION =====

    cost_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Cost amount"
    )

    currency_code = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency"
    )

    # ===== SOURCE DOCUMENTS =====

    vendor_invoice = models.ForeignKey(
        'VendorInvoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cost_allocations',
        help_text="Source vendor invoice"
    )

    purchase_order = models.ForeignKey(
        'PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cost_allocations',
        help_text="Source purchase order"
    )

    # ===== CATEGORIZATION =====

    expense_category = models.ForeignKey(
        'ExpenseCategory',
        on_delete=models.PROTECT,
        related_name='cost_allocations',
        help_text="Expense category"
    )

    # ===== GL POSTING =====

    gl_account_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="GL account code"
    )

    posted_to_gl = models.BooleanField(
        default=False,
        help_text="Has been posted to GL?"
    )

    gl_posting_date = models.DateField(
        null=True,
        blank=True,
        help_text="GL posting date"
    )

    # ===== DATES =====

    cost_date = models.DateField(
        help_text="Date of cost"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Notes"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_cost_allocations'
    )

    class Meta:
        db_table = "cost_allocations"
        ordering = ['-cost_date']
        verbose_name = "Cost Allocation"
        verbose_name_plural = "Cost Allocations"
        indexes = [
            models.Index(fields=['allocation_number']),
            models.Index(fields=['work_order', 'cost_type']),
            models.Index(fields=['cost_date']),
        ]

    def __str__(self):
        return f"{self.allocation_number} - {self.work_order} - {self.cost_amount}"

    def save(self, *args, **kwargs):
        if not self.allocation_number:
            self.allocation_number = self._generate_allocation_number()
        super().save(*args, **kwargs)

    def _generate_allocation_number(self):
        """Generate unique allocation number: COST-YYYY-####"""
        year = timezone.now().year
        last_alloc = CostAllocation.objects.filter(
            allocation_number__startswith=f"COST-{year}-"
        ).order_by('-allocation_number').first()

        if last_alloc:
            try:
                last_num = int(last_alloc.allocation_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"COST-{year}-{new_num:04d}"


class PaymentTerm(models.Model):
    """Payment terms master data."""

    term_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Payment term code (e.g., NET30)"
    )

    term_name = models.CharField(
        max_length=100,
        help_text="Payment term name"
    )

    description = models.TextField(
        blank=True,
        help_text="Description"
    )

    due_days = models.IntegerField(
        help_text="Days until payment is due"
    )

    discount_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Days to qualify for early payment discount"
    )

    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Early payment discount percentage"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Is term active?"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment_terms"
        ordering = ['due_days', 'term_code']
        verbose_name = "Payment Term"
        verbose_name_plural = "Payment Terms"

    def __str__(self):
        return f"{self.term_code} - {self.term_name}"

    def calculate_due_date(self, invoice_date):
        """Calculate due date from invoice date"""
        from datetime import timedelta
        return invoice_date + timedelta(days=self.due_days)


class VendorPayment(models.Model):
    """Payments made to vendors."""

    class PaymentMethod(models.TextChoices):
        CHECK = "CHECK", "Check"
        WIRE_TRANSFER = "WIRE_TRANSFER", "Wire Transfer"
        ACH = "ACH", "ACH Transfer"
        CREDIT_CARD = "CREDIT_CARD", "Credit Card"
        CASH = "CASH", "Cash"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    # ===== IDENTIFICATION =====

    payment_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique payment number (auto-generated: PAY-YYYY-######)"
    )

    # ===== VENDOR =====

    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.PROTECT,
        related_name='payments',
        help_text="Vendor receiving payment"
    )

    # ===== PAYMENT DETAILS =====

    payment_date = models.DateField(
        help_text="Payment date"
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        help_text="Payment method"
    )

    payment_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total payment amount"
    )

    currency_code = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency"
    )

    # ===== PAYMENT INSTRUMENT =====

    check_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Check number if payment by check"
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Transaction reference number"
    )

    # ===== BANK ACCOUNT =====

    bank_account = models.CharField(
        max_length=100,
        blank=True,
        help_text="Bank account used"
    )

    # ===== STATUS =====

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="Payment status"
    )

    # ===== GL POSTING =====

    posted_to_gl = models.BooleanField(
        default=False,
        help_text="Has been posted to GL?"
    )

    gl_posting_date = models.DateField(
        null=True,
        blank=True,
        help_text="GL posting date"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Payment notes"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_vendor_payments'
    )

    class Meta:
        db_table = "vendor_payments"
        ordering = ['-payment_date']
        verbose_name = "Vendor Payment"
        verbose_name_plural = "Vendor Payments"
        indexes = [
            models.Index(fields=['payment_number']),
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['payment_date']),
        ]

    def __str__(self):
        return f"{self.payment_number} - {self.vendor.name} - {self.payment_amount}"

    def save(self, *args, **kwargs):
        if not self.payment_number:
            self.payment_number = self._generate_payment_number()
        super().save(*args, **kwargs)

    def _generate_payment_number(self):
        """Generate unique payment number: PAY-YYYY-######"""
        year = timezone.now().year
        last_pay = VendorPayment.objects.filter(
            payment_number__startswith=f"PAY-{year}-"
        ).order_by('-payment_number').first()

        if last_pay:
            try:
                last_num = int(last_pay.payment_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"PAY-{year}-{new_num:06d}"


class PaymentAllocation(models.Model):
    """Link payments to specific invoices with allocated amounts."""

    payment = models.ForeignKey(
        'VendorPayment',
        on_delete=models.CASCADE,
        related_name='allocations',
        help_text="Payment"
    )

    vendor_invoice = models.ForeignKey(
        'VendorInvoice',
        on_delete=models.CASCADE,
        related_name='payment_allocations',
        help_text="Invoice being paid"
    )

    allocated_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Amount allocated to this invoice"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_allocations"
        unique_together = [['payment', 'vendor_invoice']]
        verbose_name = "Payment Allocation"
        verbose_name_plural = "Payment Allocations"

    def __str__(self):
        return f"{self.payment.payment_number} → {self.vendor_invoice.invoice_number}: {self.allocated_amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update invoice paid amount
        total_paid = self.vendor_invoice.payment_allocations.aggregate(
            total=models.Sum('allocated_amount')
        )['total'] or Decimal('0.00')
        self.vendor_invoice.amount_paid = total_paid
        if total_paid >= self.vendor_invoice.total_amount:
            self.vendor_invoice.status = VendorInvoice.Status.PAID
        elif total_paid > 0:
            self.vendor_invoice.status = VendorInvoice.Status.PARTIALLY_PAID
        self.vendor_invoice.save()


# =============================================================================
# LEGACY MODELS (retained for compatibility)
# =============================================================================


class Supplier(models.Model):
    """
    🟡 LEGACY: Basic supplier master.
    DEPRECATED: Use Vendor model instead for new implementations.
    """

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    payment_terms = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "suppliers"
        verbose_name = "Supplier (Legacy)"
        verbose_name_plural = "Suppliers (Legacy)"

    def __str__(self):
        return f"{self.code} - {self.name}"


class CAPA(models.Model):
    """🟡 P2: Corrective and Preventive Actions."""

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        VERIFICATION = "VERIFICATION", "Pending Verification"
        CLOSED = "CLOSED", "Closed"

    capa_number = models.CharField(max_length=30, unique=True, blank=True)
    ncr = models.ForeignKey(
        "quality.NCR",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="capas"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    preventive_action = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    due_date = models.DateField(null=True, blank=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_capas"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "capas"
        verbose_name = "CAPA"
        verbose_name_plural = "CAPAs"

    def __str__(self):
        return f"{self.capa_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.capa_number:
            # Generate auto CAPA number
            from django.utils import timezone
            year = timezone.now().year
            last = CAPA.objects.filter(
                capa_number__startswith=f"CAPA-{year}"
            ).order_by('-capa_number').first()

            if last and last.capa_number:
                try:
                    last_num = int(last.capa_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.capa_number = f"CAPA-{year}-{new_num:04d}"

        super().save(*args, **kwargs)
