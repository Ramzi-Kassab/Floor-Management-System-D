"""
ARDT FMS - Sales Models
Version: 5.4

Tables:
- customers (P1)
- customer_contacts (P1)
- customer_document_requirements (P1)
- rigs (P1)
- wells (P1)
- warehouses (P1)
- sales_orders (P1)
- sales_order_lines (P1)

Sprint 5 Additions:
- service_sites (Field Service)
- field_technicians (Field Service)
- field_service_requests (Field Service)
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from decimal import Decimal


class Customer(models.Model):
    """
    🟢 P1: Customer master data.
    """

    class CustomerType(models.TextChoices):
        OPERATOR = "OPERATOR", "Oil Operator"
        CONTRACTOR = "CONTRACTOR", "Drilling Contractor"
        DISTRIBUTOR = "DISTRIBUTOR", "Distributor"
        OTHER = "OTHER", "Other"

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    customer_type = models.CharField(max_length=20, choices=CustomerType.choices, default=CustomerType.OPERATOR)

    # Contact info
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="Saudi Arabia")
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Business info
    tax_id = models.CharField(max_length=50, blank=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    payment_terms = models.CharField(max_length=50, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_aramco = models.BooleanField(default=False, help_text="ARAMCO or ARAMCO contractor")

    # Account manager
    account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_customers"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_customers"
    )

    class Meta:
        db_table = "customers"
        ordering = ["name"]
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return f"{self.code} - {self.name}"


class CustomerContact(models.Model):
    """
    🟢 P1: Customer contact persons.
    """

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "customer_contacts"
        ordering = ["customer", "-is_primary", "name"]
        verbose_name = "Customer Contact"
        verbose_name_plural = "Customer Contacts"

    def __str__(self):
        return f"{self.customer.code} - {self.name}"


class CustomerDocumentRequirement(models.Model):
    """
    🟢 P1: Document requirements specific to each customer.
    """

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="document_requirements")
    document_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=True)
    template_file = models.FileField(upload_to="doc_templates/", null=True, blank=True)

    class Meta:
        db_table = "customer_document_requirements"
        verbose_name = "Customer Document Requirement"
        verbose_name_plural = "Customer Document Requirements"

    def __str__(self):
        return f"{self.customer.code} - {self.document_type}"


class Rig(models.Model):
    """
    🟢 P1: Drilling rigs (ARAMCO and contractor rigs).
    """

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="rigs")
    contractor = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="contracted_rigs")
    rig_type = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rigs"
        ordering = ["code"]
        verbose_name = "Rig"
        verbose_name_plural = "Rigs"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Well(models.Model):
    """
    🟢 P1: Wells being drilled.
    """

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="wells")
    rig = models.ForeignKey(Rig, on_delete=models.SET_NULL, null=True, blank=True, related_name="wells")
    field_name = models.CharField(max_length=100, blank=True)
    spud_date = models.DateField(null=True, blank=True)
    target_depth = models.IntegerField(null=True, blank=True, help_text="Feet")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wells"
        ordering = ["code"]
        verbose_name = "Well"
        verbose_name_plural = "Wells"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Warehouse(models.Model):
    """
    🟢 P1: Warehouses/storage locations (ARDT, ARAMCO, customer).
    """

    class WarehouseType(models.TextChoices):
        ARDT = "ARDT", "ARDT Factory"
        ARAMCO = "ARAMCO", "ARAMCO Warehouse"
        CUSTOMER = "CUSTOMER", "Customer Location"
        RIG = "RIG", "Rig Site"

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    warehouse_type = models.CharField(max_length=20, choices=WarehouseType.choices, default=WarehouseType.ARDT)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="warehouses")
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "warehouses"
        ordering = ["code"]
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouses"

    def __str__(self):
        return f"{self.code} - {self.name}"


class SalesOrder(models.Model):
    """
    🟢 P1: Sales orders for drill bits.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        CONFIRMED = "CONFIRMED", "Confirmed"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        READY = "READY", "Ready for Dispatch"
        DISPATCHED = "DISPATCHED", "Dispatched"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    so_number = models.CharField(max_length=30, unique=True)

    # Customer
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="sales_orders")
    customer_po = models.CharField(max_length=50, blank=True, help_text="Customer PO number")

    # DRSS link (if from ARAMCO)
    drss_request = models.ForeignKey(
        "drss.DRSSRequest", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_orders"
    )

    # Destination
    rig = models.ForeignKey(Rig, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_orders")
    well = models.ForeignKey(Well, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_orders")
    delivery_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="delivery_orders"
    )

    # Dates
    order_date = models.DateField()
    required_date = models.DateField(null=True, blank=True)
    promised_date = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # Financials
    currency = models.CharField(max_length=3, default="SAR")
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Notes
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    # Assignments
    sales_rep = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_orders"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_sales_orders"
    )

    class Meta:
        db_table = "sales_orders"
        ordering = ["-order_date"]
        verbose_name = "Sales Order"
        verbose_name_plural = "Sales Orders"

    def __str__(self):
        return f"{self.so_number}"


class SalesOrderLine(models.Model):
    """
    🟢 P1: Line items in a sales order.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PRODUCTION = "IN_PRODUCTION", "In Production"
        READY = "READY", "Ready"
        DISPATCHED = "DISPATCHED", "Dispatched"
        CANCELLED = "CANCELLED", "Cancelled"

    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="lines")
    line_number = models.IntegerField()

    # DRSS line link (if from ARAMCO)
    drss_request_line = models.ForeignKey(
        "drss.DRSSRequestLine", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_order_lines"
    )

    # Product
    design = models.ForeignKey(
        "technology.Design", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_order_lines"
    )
    description = models.CharField(max_length=500)
    quantity = models.IntegerField(default=1)

    # Pricing
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Link to work order
    work_order = models.ForeignKey(
        "workorders.WorkOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="sales_order_lines"
    )

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sales_order_lines"
        ordering = ["sales_order", "line_number"]
        unique_together = ["sales_order", "line_number"]
        verbose_name = "Sales Order Line"
        verbose_name_plural = "Sales Order Lines"

    def __str__(self):
        return f"{self.sales_order.so_number} - Line {self.line_number}"


# =============================================================================
# SPRINT 5: FIELD SERVICE MODELS
# =============================================================================


class ServiceSite(models.Model):
    """
    Sprint 5: Service Site locations for field service operations.

    Represents customer locations where field services are performed,
    including rig sites, warehouses, and other customer facilities.

    Features:
    - GPS coordinate support for location tracking
    - Access and security information
    - Operating hours and contact details
    - Service history tracking

    ISO 9001 References:
    - Clause 8.5: Production and Service Provision
    """

    class SiteType(models.TextChoices):
        RIG_SITE = "RIG_SITE", "Rig Site"
        WAREHOUSE = "WAREHOUSE", "Warehouse"
        FIELD_OFFICE = "FIELD_OFFICE", "Field Office"
        CUSTOMER_FACILITY = "CUSTOMER_FACILITY", "Customer Facility"
        SERVICE_CENTER = "SERVICE_CENTER", "Service Center"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        UNDER_CONSTRUCTION = "UNDER_CONSTRUCTION", "Under Construction"
        TEMPORARILY_CLOSED = "TEMPORARILY_CLOSED", "Temporarily Closed"

    # ===== IDENTIFICATION =====
    site_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique site code (e.g., SITE-001)"
    )

    name = models.CharField(
        max_length=200,
        help_text="Site name"
    )

    name_ar = models.CharField(
        max_length=200,
        blank=True,
        help_text="Site name in Arabic"
    )

    # ===== CUSTOMER RELATIONSHIP =====
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.PROTECT,
        related_name='service_sites',
        help_text="Customer who owns/operates this site"
    )

    # ===== SITE DETAILS =====
    site_type = models.CharField(
        max_length=30,
        choices=SiteType.choices,
        default=SiteType.RIG_SITE,
        help_text="Type of service site"
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text="Current site status"
    )

    description = models.TextField(
        blank=True,
        help_text="Site description and notes"
    )

    # ===== LOCATION - ADDRESS =====
    address_line1 = models.CharField(
        max_length=200,
        help_text="Primary address line"
    )

    address_line2 = models.CharField(
        max_length=200,
        blank=True,
        help_text="Secondary address line"
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

    # ===== LOCATION - GPS =====
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="GPS latitude coordinate"
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="GPS longitude coordinate"
    )

    elevation_meters = models.IntegerField(
        null=True,
        blank=True,
        help_text="Elevation in meters above sea level"
    )

    # ===== CONTACT INFORMATION =====
    primary_contact_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Primary contact person name"
    )

    primary_contact_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Primary contact phone number"
    )

    primary_contact_email = models.EmailField(
        blank=True,
        help_text="Primary contact email"
    )

    alternate_contact_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Alternate contact person"
    )

    alternate_contact_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Alternate contact phone"
    )

    # ===== ACCESS & SECURITY =====
    access_instructions = models.TextField(
        blank=True,
        help_text="Instructions for accessing the site"
    )

    security_requirements = models.TextField(
        blank=True,
        help_text="Security clearance or requirements"
    )

    requires_escort = models.BooleanField(
        default=False,
        help_text="Whether visitors require an escort"
    )

    requires_ppe = models.BooleanField(
        default=True,
        help_text="Whether PPE is required on site"
    )

    ppe_requirements = models.TextField(
        blank=True,
        help_text="Specific PPE requirements"
    )

    # ===== OPERATING HOURS =====
    operating_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Site operating hours start"
    )

    operating_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text="Site operating hours end"
    )

    is_24_hour = models.BooleanField(
        default=False,
        help_text="Whether site operates 24 hours"
    )

    weekend_operations = models.BooleanField(
        default=False,
        help_text="Whether site operates on weekends"
    )

    # ===== FACILITIES =====
    has_parking = models.BooleanField(default=True)
    has_loading_dock = models.BooleanField(default=False)
    has_storage_area = models.BooleanField(default=False)
    has_workshop = models.BooleanField(default=False)

    facility_notes = models.TextField(
        blank=True,
        help_text="Additional facility information"
    )

    # ===== SERVICE HISTORY =====
    first_service_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of first service at this site"
    )

    last_service_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of most recent service"
    )

    total_service_visits = models.IntegerField(
        default=0,
        help_text="Total number of service visits"
    )

    # ===== STATUS =====
    is_active = models.BooleanField(
        default=True,
        help_text="Whether site is active"
    )

    # ===== LINKED RIG =====
    rig = models.ForeignKey(
        'Rig',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_sites',
        help_text="Associated rig (if applicable)"
    )

    # ===== AUDIT =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_service_sites',
        help_text="User who created this site"
    )

    class Meta:
        db_table = "service_sites"
        ordering = ['customer', 'name']
        verbose_name = "Service Site"
        verbose_name_plural = "Service Sites"
        indexes = [
            models.Index(fields=['site_code']),
            models.Index(fields=['customer', 'is_active']),
            models.Index(fields=['site_type', 'status']),
        ]
        permissions = [
            ("can_view_all_sites", "Can view all service sites"),
            ("can_manage_sites", "Can manage service sites"),
        ]

    def __str__(self):
        return f"{self.site_code} - {self.name}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate site code if not provided"""
        if not self.site_code:
            self.site_code = self._generate_site_code()
        super().save(*args, **kwargs)

    def _generate_site_code(self):
        """Generate unique site code"""
        prefix = "SITE"
        last_site = ServiceSite.objects.filter(
            site_code__startswith=f"{prefix}-"
        ).order_by('-site_code').first()

        if last_site:
            try:
                last_num = int(last_site.site_code.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}-{new_num:04d}"

    @property
    def has_gps_coordinates(self):
        """Check if site has GPS coordinates"""
        return self.latitude is not None and self.longitude is not None

    @property
    def full_address(self):
        """Return formatted full address"""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.append(f"{self.city}, {self.state_province}" if self.state_province else self.city)
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ", ".join(filter(None, parts))

    @property
    def is_operational(self):
        """Check if site is currently operational"""
        return self.status == self.Status.ACTIVE and self.is_active

    def update_service_history(self, service_date):
        """Update service history after a visit"""
        if self.first_service_date is None:
            self.first_service_date = service_date
        self.last_service_date = service_date
        self.total_service_visits += 1
        self.save(update_fields=['first_service_date', 'last_service_date', 'total_service_visits'])


class FieldTechnician(models.Model):
    """
    Sprint 5: Field Service Technicians.

    Represents technicians who perform field service operations.
    Tracks qualifications, certifications, availability, and performance.

    ISO 9001 References:
    - Clause 7.2: Competence
    - Clause 7.3: Awareness
    """

    class EmploymentStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ON_LEAVE = "ON_LEAVE", "On Leave"
        INACTIVE = "INACTIVE", "Inactive"
        TERMINATED = "TERMINATED", "Terminated"

    class SkillLevel(models.TextChoices):
        JUNIOR = "JUNIOR", "Junior"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        SENIOR = "SENIOR", "Senior"
        EXPERT = "EXPERT", "Expert"

    # ===== IDENTIFICATION =====
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique employee ID"
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='field_technician_profile',
        help_text="Linked user account"
    )

    name = models.CharField(
        max_length=200,
        help_text="Full name"
    )

    name_ar = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name in Arabic"
    )

    # ===== CONTACT =====
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
        help_text="Mobile phone number"
    )

    emergency_contact_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Emergency contact name"
    )

    emergency_contact_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Emergency contact phone"
    )

    # ===== EMPLOYMENT =====
    hire_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of hire"
    )

    employment_status = models.CharField(
        max_length=20,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.ACTIVE,
        help_text="Current employment status"
    )

    job_title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Job title"
    )

    department = models.CharField(
        max_length=100,
        blank=True,
        help_text="Department"
    )

    # ===== SKILLS & QUALIFICATIONS =====
    skill_level = models.CharField(
        max_length=20,
        choices=SkillLevel.choices,
        default=SkillLevel.INTERMEDIATE,
        help_text="Skill level"
    )

    specializations = models.TextField(
        blank=True,
        help_text="List of specializations (comma-separated)"
    )

    certifications = models.TextField(
        blank=True,
        help_text="List of certifications (comma-separated)"
    )

    can_perform_inspections = models.BooleanField(
        default=True,
        help_text="Can perform equipment inspections"
    )

    can_perform_repairs = models.BooleanField(
        default=True,
        help_text="Can perform equipment repairs"
    )

    can_perform_training = models.BooleanField(
        default=False,
        help_text="Can perform customer training"
    )

    # ===== LOCATION & AVAILABILITY =====
    home_base_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Home base location"
    )

    service_radius_km = models.IntegerField(
        default=100,
        help_text="Maximum service radius in kilometers"
    )

    available_for_travel = models.BooleanField(
        default=True,
        help_text="Available for travel assignments"
    )

    has_valid_drivers_license = models.BooleanField(
        default=True,
        help_text="Has valid driver's license"
    )

    has_valid_passport = models.BooleanField(
        default=False,
        help_text="Has valid passport for international travel"
    )

    # ===== CURRENT ASSIGNMENT =====
    is_currently_assigned = models.BooleanField(
        default=False,
        help_text="Currently assigned to a job"
    )

    current_location = models.ForeignKey(
        'ServiceSite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_technicians',
        help_text="Current location if on assignment"
    )

    # ===== PERFORMANCE METRICS =====
    total_service_calls = models.IntegerField(
        default=0,
        help_text="Total service calls completed"
    )

    completed_calls = models.IntegerField(
        default=0,
        help_text="Successfully completed service calls"
    )

    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Average customer rating (1-5)"
    )

    on_time_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage of on-time arrivals"
    )

    # ===== AUDIT =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "field_technicians"
        ordering = ['name']
        verbose_name = "Field Technician"
        verbose_name_plural = "Field Technicians"
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['employment_status']),
            models.Index(fields=['skill_level']),
        ]
        permissions = [
            ("can_assign_technicians", "Can assign technicians to requests"),
            ("can_view_technician_performance", "Can view technician performance"),
        ]

    def __str__(self):
        return f"{self.employee_id} - {self.name}"

    @property
    def completion_rate(self):
        """Calculate completion rate percentage"""
        if self.total_service_calls == 0:
            return None
        return (self.completed_calls / self.total_service_calls) * 100

    @property
    def is_available(self):
        """Check if technician is available for assignment"""
        return (
            self.employment_status == self.EmploymentStatus.ACTIVE and
            not self.is_currently_assigned
        )

    def can_service_site(self, site):
        """Check if technician can service a given site"""
        if not self.is_available:
            return False
        return True

    def update_performance_metrics(self, was_successful, was_on_time, rating=None):
        """Update performance metrics after a service call"""
        self.total_service_calls += 1
        if was_successful:
            self.completed_calls += 1

        # Update on-time percentage
        if self.on_time_percentage is None:
            self.on_time_percentage = Decimal('100.00') if was_on_time else Decimal('0.00')
        else:
            current_on_time = int(self.on_time_percentage * (self.total_service_calls - 1) / 100)
            if was_on_time:
                current_on_time += 1
            self.on_time_percentage = Decimal(str(current_on_time * 100 / self.total_service_calls))

        # Update average rating
        if rating is not None:
            if self.average_rating is None:
                self.average_rating = Decimal(str(rating))
            else:
                # Calculate new average
                total_ratings = self.average_rating * (self.total_service_calls - 1)
                self.average_rating = (total_ratings + Decimal(str(rating))) / self.total_service_calls

        self.save()


class FieldServiceRequest(models.Model):
    """
    Sprint 5: Field Service Request tracking.

    Manages the complete lifecycle of field service requests,
    from initial customer submission through execution and completion.

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
    """

    class RequestType(models.TextChoices):
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
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"
        EMERGENCY = "EMERGENCY", "Emergency"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        REVIEWED = "REVIEWED", "Reviewed"
        APPROVED = "APPROVED", "Approved"
        SCHEDULED = "SCHEDULED", "Scheduled"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        ON_HOLD = "ON_HOLD", "On Hold"

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

    # ===== SCHEDULING =====
    requested_date = models.DateField(
        help_text="Date customer wants service performed"
    )

    requested_time_slot = models.CharField(
        max_length=50,
        blank=True,
        help_text="Preferred time slot"
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
        """Override save to auto-generate request number and update timestamps"""
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

    def _generate_request_number(self):
        """Generate unique request number: FSR-YYYY-####"""
        year = timezone.now().year

        last_request = FieldServiceRequest.objects.filter(
            request_number__startswith=f"FSR-{year}-"
        ).order_by('-request_number').first()

        if last_request:
            try:
                last_num = int(last_request.request_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"FSR-{year}-{new_num:04d}"

    # ===== PROPERTIES =====

    @property
    def is_overdue(self):
        """Check if requested date has passed without completion"""
        if self.status in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return False
        return timezone.now().date() > self.requested_date

    @property
    def days_until_service(self):
        """Calculate days until requested service date"""
        delta = self.requested_date - timezone.now().date()
        return delta.days

    @property
    def is_urgent(self):
        """Check if request is urgent or emergency priority"""
        return self.priority in [self.Priority.URGENT, self.Priority.EMERGENCY]

    @property
    def duration_variance_hours(self):
        """Calculate variance between estimated and actual duration"""
        if not self.actual_duration_hours or not self.estimated_duration_hours:
            return None
        return self.actual_duration_hours - self.estimated_duration_hours

    @property
    def duration_variance_percentage(self):
        """Calculate variance percentage between estimated and actual duration"""
        if not self.actual_duration_hours or not self.estimated_duration_hours:
            return None
        if self.estimated_duration_hours == 0:
            return None
        variance = self.actual_duration_hours - self.estimated_duration_hours
        return float((variance / self.estimated_duration_hours) * 100)

    # ===== STATUS CHECK METHODS =====

    def can_be_submitted(self):
        """Check if request can be submitted"""
        return self.status == self.Status.DRAFT

    def can_be_reviewed(self):
        """Check if request can be reviewed"""
        return self.status == self.Status.SUBMITTED

    def can_be_approved(self):
        """Check if request can be approved"""
        return self.status == self.Status.REVIEWED

    def can_be_assigned(self):
        """Check if technician can be assigned"""
        return self.status in [self.Status.APPROVED, self.Status.SCHEDULED]

    def can_be_started(self):
        """Check if work can be started"""
        return (
            self.status == self.Status.SCHEDULED and
            self.assigned_technician is not None
        )

    def can_be_completed(self):
        """Check if work can be completed"""
        return self.status == self.Status.IN_PROGRESS

    def can_be_cancelled(self):
        """Check if request can be cancelled"""
        return self.status not in [self.Status.COMPLETED, self.Status.CANCELLED]

    # ===== WORKFLOW METHODS =====

    def submit(self, user=None):
        """Submit request for review"""
        if not self.can_be_submitted():
            raise ValidationError("Request cannot be submitted in current status")

        self.status = self.Status.SUBMITTED
        self.save()

    def review(self, user, notes=''):
        """Mark request as reviewed"""
        if not self.can_be_reviewed():
            raise ValidationError("Request cannot be reviewed in current status")

        self.status = self.Status.REVIEWED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

    def approve(self, user, notes=''):
        """Approve request"""
        if not self.can_be_approved():
            raise ValidationError("Request cannot be approved in current status")

        self.status = self.Status.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()

    def assign_technician(self, technician, user=None):
        """Assign technician to request"""
        if not self.can_be_assigned():
            raise ValidationError("Technician cannot be assigned in current status")

        self.assigned_technician = technician
        self.assigned_by = user
        self.assigned_date = timezone.now()
        self.status = self.Status.SCHEDULED
        self.save()

        # Update technician assignment status
        technician.is_currently_assigned = True
        technician.save(update_fields=['is_currently_assigned'])

    def start_work(self):
        """Start work on request"""
        if not self.can_be_started():
            raise ValidationError("Work cannot be started in current status")

        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()

    def complete_work(self, notes='', actual_duration=None):
        """Complete work on request"""
        if not self.can_be_completed():
            raise ValidationError("Work cannot be completed in current status")

        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.completion_notes = notes

        if actual_duration:
            self.actual_duration_hours = actual_duration
        elif self.started_at:
            duration = timezone.now() - self.started_at
            self.actual_duration_hours = Decimal(str(duration.total_seconds() / 3600))

        self.save()

        # Update technician assignment status
        if self.assigned_technician:
            self.assigned_technician.is_currently_assigned = False
            self.assigned_technician.save(update_fields=['is_currently_assigned'])

            # Update service site history
            self.service_site.update_service_history(timezone.now().date())

    def cancel(self, user, reason=''):
        """Cancel request"""
        if not self.can_be_cancelled():
            raise ValidationError("Request cannot be cancelled in current status")

        self.status = self.Status.CANCELLED
        self.cancelled_by = user
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save()

        # Release technician if assigned
        if self.assigned_technician:
            self.assigned_technician.is_currently_assigned = False
            self.assigned_technician.save(update_fields=['is_currently_assigned'])


class ServiceSchedule(models.Model):
    """
    Sprint 5: Service Schedule management.

    Manages scheduling of field service appointments including
    technician assignments, time slots, and conflict detection.

    Features:
    - Schedule conflict detection
    - Rescheduling with history
    - Customer confirmation tracking
    - Notification management

    ISO 9001 References:
    - Clause 8.1: Operational Planning and Control
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        CONFIRMED = "CONFIRMED", "Confirmed"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        RESCHEDULED = "RESCHEDULED", "Rescheduled"

    # ===== IDENTIFICATION =====
    schedule_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique schedule number (auto-generated: SCH-YYYY-####)"
    )

    # ===== LINKED ENTITIES =====
    service_request = models.ForeignKey(
        'FieldServiceRequest',
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text="Related field service request"
    )

    technician = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.PROTECT,
        related_name='schedules',
        help_text="Assigned technician"
    )

    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.PROTECT,
        related_name='schedules',
        help_text="Service site location"
    )

    # ===== SCHEDULING DETAILS =====
    scheduled_date = models.DateField(
        db_index=True,
        help_text="Scheduled service date"
    )

    scheduled_start_time = models.TimeField(
        help_text="Scheduled start time"
    )

    scheduled_end_time = models.TimeField(
        help_text="Scheduled end time"
    )

    estimated_duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Estimated duration in hours"
    )

    # ===== STATUS =====
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Current schedule status"
    )

    # ===== CONFIRMATION =====
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_schedules',
        help_text="User who confirmed the schedule"
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the schedule was confirmed"
    )

    customer_confirmed = models.BooleanField(
        default=False,
        help_text="Whether customer confirmed the schedule"
    )

    customer_confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When customer confirmed"
    )

    # ===== RESCHEDULING =====
    original_schedule = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rescheduled_versions',
        help_text="Original schedule if this is a reschedule"
    )

    rescheduled_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rescheduled_from',
        help_text="New schedule if this was rescheduled"
    )

    reschedule_reason = models.TextField(
        blank=True,
        help_text="Reason for rescheduling"
    )

    reschedule_count = models.IntegerField(
        default=0,
        help_text="Number of times rescheduled"
    )

    # ===== NOTIFICATIONS =====
    notification_sent = models.BooleanField(
        default=False,
        help_text="Whether notification was sent"
    )

    notification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was sent"
    )

    reminder_sent = models.BooleanField(
        default=False,
        help_text="Whether reminder was sent"
    )

    reminder_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When reminder was sent"
    )

    # ===== NOTES =====
    scheduling_notes = models.TextField(
        blank=True,
        help_text="Internal scheduling notes"
    )

    special_requirements = models.TextField(
        blank=True,
        help_text="Special requirements for this visit"
    )

    # ===== AUDIT =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_schedules',
        help_text="User who created this schedule"
    )

    class Meta:
        db_table = "service_schedules"
        ordering = ['scheduled_date', 'scheduled_start_time']
        verbose_name = "Service Schedule"
        verbose_name_plural = "Service Schedules"
        indexes = [
            models.Index(fields=['schedule_number']),
            models.Index(fields=['scheduled_date', 'status']),
            models.Index(fields=['technician', 'scheduled_date']),
            models.Index(fields=['service_request', 'status']),
        ]
        permissions = [
            ("can_create_schedules", "Can create service schedules"),
            ("can_confirm_schedules", "Can confirm service schedules"),
            ("can_reschedule", "Can reschedule service appointments"),
        ]

    def __str__(self):
        return f"{self.schedule_number} - {self.scheduled_date}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate schedule number"""
        if not self.schedule_number:
            self.schedule_number = self._generate_schedule_number()
        super().save(*args, **kwargs)

    def _generate_schedule_number(self):
        """Generate unique schedule number: SCH-YYYY-####"""
        year = timezone.now().year

        last_schedule = ServiceSchedule.objects.filter(
            schedule_number__startswith=f"SCH-{year}-"
        ).order_by('-schedule_number').first()

        if last_schedule:
            try:
                last_num = int(last_schedule.schedule_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"SCH-{year}-{new_num:04d}"

    def _times_overlap(self, other):
        """Check if time slots overlap"""
        return not (
            self.scheduled_end_time <= other.scheduled_start_time or
            self.scheduled_start_time >= other.scheduled_end_time
        )

    def check_conflicts(self):
        """
        Check for scheduling conflicts.

        Returns:
            list: List of conflicting schedules
        """
        conflicts = ServiceSchedule.objects.filter(
            technician=self.technician,
            scheduled_date=self.scheduled_date,
            status__in=['CONFIRMED', 'IN_PROGRESS']
        ).exclude(pk=self.pk)

        conflicting = []
        for schedule in conflicts:
            if self._times_overlap(schedule):
                conflicting.append(schedule)

        return conflicting

    def has_conflicts(self):
        """Check if schedule has any conflicts"""
        return len(self.check_conflicts()) > 0

    @property
    def is_past(self):
        """Check if scheduled date is in the past"""
        return self.scheduled_date < timezone.now().date()

    @property
    def is_today(self):
        """Check if scheduled for today"""
        return self.scheduled_date == timezone.now().date()

    @property
    def days_until(self):
        """Calculate days until scheduled date"""
        delta = self.scheduled_date - timezone.now().date()
        return delta.days

    def can_be_confirmed(self):
        """Check if schedule can be confirmed"""
        return self.status == self.Status.DRAFT and not self.has_conflicts()

    def can_be_cancelled(self):
        """Check if schedule can be cancelled"""
        return self.status not in [self.Status.COMPLETED, self.Status.CANCELLED]

    def can_be_rescheduled(self):
        """Check if schedule can be rescheduled"""
        return self.status not in [
            self.Status.COMPLETED,
            self.Status.CANCELLED,
            self.Status.RESCHEDULED
        ]

    def confirm_schedule(self, user):
        """Confirm the schedule"""
        if not self.can_be_confirmed():
            if self.has_conflicts():
                raise ValidationError("Schedule has conflicts that must be resolved")
            raise ValidationError("Schedule cannot be confirmed in current status")

        self.status = self.Status.CONFIRMED
        self.confirmed_by = user
        self.confirmed_at = timezone.now()
        self.save()

    def confirm_by_customer(self):
        """Mark schedule as confirmed by customer"""
        self.customer_confirmed = True
        self.customer_confirmed_at = timezone.now()
        self.save()

    def start_service(self):
        """Mark schedule as in progress"""
        if self.status != self.Status.CONFIRMED:
            raise ValidationError("Can only start confirmed schedules")

        self.status = self.Status.IN_PROGRESS
        self.save()

    def complete_service(self):
        """Mark schedule as completed"""
        if self.status != self.Status.IN_PROGRESS:
            raise ValidationError("Can only complete in-progress schedules")

        self.status = self.Status.COMPLETED
        self.save()

    def cancel_schedule(self, reason=''):
        """Cancel the schedule"""
        if not self.can_be_cancelled():
            raise ValidationError("Schedule cannot be cancelled")

        self.status = self.Status.CANCELLED
        if reason:
            self.scheduling_notes = f"{self.scheduling_notes}\nCancelled: {reason}".strip()
        self.save()

    def reschedule(self, new_date, new_start_time, new_end_time, reason='', user=None):
        """
        Reschedule to a new date/time.

        Creates a new schedule and marks this one as rescheduled.
        """
        if not self.can_be_rescheduled():
            raise ValidationError("Schedule cannot be rescheduled")

        # Create new schedule
        new_schedule = ServiceSchedule.objects.create(
            service_request=self.service_request,
            technician=self.technician,
            service_site=self.service_site,
            scheduled_date=new_date,
            scheduled_start_time=new_start_time,
            scheduled_end_time=new_end_time,
            estimated_duration_hours=self.estimated_duration_hours,
            original_schedule=self,
            reschedule_count=self.reschedule_count + 1,
            scheduling_notes=self.scheduling_notes,
            special_requirements=self.special_requirements,
            created_by=user
        )

        # Mark this schedule as rescheduled
        self.status = self.Status.RESCHEDULED
        self.rescheduled_to = new_schedule
        self.reschedule_reason = reason
        self.save()

        return new_schedule


class SiteVisit(models.Model):
    """
    Sprint 5: Site Visit records.

    Records actual site visits by technicians including
    check-in/check-out, work performed, and outcomes.

    Features:
    - Check-in/check-out tracking
    - Duration calculations
    - Customer feedback collection
    - Photo/document tracking

    ISO 9001 References:
    - Clause 8.5.1: Control of Production and Service Provision
    """

    class VisitType(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled Service"
        EMERGENCY = "EMERGENCY", "Emergency Call"
        FOLLOW_UP = "FOLLOW_UP", "Follow-up Visit"
        INSPECTION = "INSPECTION", "Inspection"
        TRAINING = "TRAINING", "Training"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        EN_ROUTE = "EN_ROUTE", "En Route"
        ARRIVED = "ARRIVED", "Arrived"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        INCOMPLETE = "INCOMPLETE", "Incomplete"

    # ===== IDENTIFICATION =====
    visit_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique visit number (auto-generated: VIS-YYYY-####)"
    )

    # ===== LINKED ENTITIES =====
    service_request = models.ForeignKey(
        'FieldServiceRequest',
        on_delete=models.PROTECT,
        related_name='site_visits',
        help_text="Related field service request"
    )

    schedule = models.ForeignKey(
        'ServiceSchedule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='site_visits',
        help_text="Related schedule"
    )

    technician = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.PROTECT,
        related_name='site_visits',
        help_text="Technician who performed the visit"
    )

    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.PROTECT,
        related_name='site_visits',
        help_text="Site visited"
    )

    # ===== VISIT TIMING =====
    visit_date = models.DateField(
        db_index=True,
        help_text="Date of the visit"
    )

    check_in_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When technician checked in"
    )

    check_out_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When technician checked out"
    )

    actual_duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual visit duration in hours"
    )

    # ===== VISIT DETAILS =====
    visit_type = models.CharField(
        max_length=50,
        choices=VisitType.choices,
        default=VisitType.SCHEDULED,
        help_text="Type of visit"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True,
        help_text="Current visit status"
    )

    # ===== WORK PERFORMED =====
    work_performed = models.TextField(
        blank=True,
        help_text="Description of work performed"
    )

    issues_found = models.TextField(
        blank=True,
        help_text="Issues found during visit"
    )

    parts_used = models.TextField(
        blank=True,
        help_text="Parts/materials used"
    )

    recommendations = models.TextField(
        blank=True,
        help_text="Recommendations for future work"
    )

    # ===== OUTCOMES =====
    visit_successful = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether the visit was successful"
    )

    follow_up_required = models.BooleanField(
        default=False,
        help_text="Whether follow-up is required"
    )

    follow_up_reason = models.TextField(
        blank=True,
        help_text="Reason for follow-up"
    )

    # ===== CUSTOMER FEEDBACK =====
    customer_signature = models.CharField(
        max_length=200,
        blank=True,
        help_text="Customer signature (name)"
    )

    customer_signed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When customer signed"
    )

    customer_satisfaction_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Customer satisfaction rating (1-5)"
    )

    customer_comments = models.TextField(
        blank=True,
        help_text="Customer comments/feedback"
    )

    # ===== ATTACHMENTS =====
    has_photos = models.BooleanField(
        default=False,
        help_text="Whether photos were taken"
    )

    photo_count = models.IntegerField(
        default=0,
        help_text="Number of photos"
    )

    has_documents = models.BooleanField(
        default=False,
        help_text="Whether documents were attached"
    )

    document_count = models.IntegerField(
        default=0,
        help_text="Number of documents"
    )

    # ===== GPS LOCATION =====
    check_in_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Check-in GPS latitude"
    )

    check_in_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Check-in GPS longitude"
    )

    check_out_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Check-out GPS latitude"
    )

    check_out_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Check-out GPS longitude"
    )

    # ===== AUDIT =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "site_visits"
        ordering = ['-visit_date', '-check_in_time']
        verbose_name = "Site Visit"
        verbose_name_plural = "Site Visits"
        indexes = [
            models.Index(fields=['visit_number']),
            models.Index(fields=['visit_date', 'status']),
            models.Index(fields=['technician', 'visit_date']),
            models.Index(fields=['service_site', 'visit_date']),
        ]
        permissions = [
            ("can_check_in_visit", "Can check in to site visit"),
            ("can_complete_visit", "Can complete site visit"),
            ("can_view_all_visits", "Can view all site visits"),
        ]

    def __str__(self):
        return f"{self.visit_number} - {self.visit_date}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate visit number"""
        if not self.visit_number:
            self.visit_number = self._generate_visit_number()
        super().save(*args, **kwargs)

    def _generate_visit_number(self):
        """Generate unique visit number: VIS-YYYY-####"""
        year = timezone.now().year

        last_visit = SiteVisit.objects.filter(
            visit_number__startswith=f"VIS-{year}-"
        ).order_by('-visit_number').first()

        if last_visit:
            try:
                last_num = int(last_visit.visit_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"VIS-{year}-{new_num:04d}"

    @property
    def is_checked_in(self):
        """Check if technician has checked in"""
        return self.check_in_time is not None

    @property
    def is_checked_out(self):
        """Check if technician has checked out"""
        return self.check_out_time is not None

    @property
    def duration_minutes(self):
        """Calculate visit duration in minutes"""
        if not self.check_in_time or not self.check_out_time:
            return None
        delta = self.check_out_time - self.check_in_time
        return int(delta.total_seconds() / 60)

    def can_check_in(self):
        """Check if technician can check in"""
        return self.status in [self.Status.SCHEDULED, self.Status.EN_ROUTE]

    def can_check_out(self):
        """Check if technician can check out"""
        return self.status in [self.Status.ARRIVED, self.Status.IN_PROGRESS]

    def check_in(self, latitude=None, longitude=None):
        """Check in to site visit"""
        if not self.can_check_in():
            raise ValidationError("Cannot check in to this visit")

        self.check_in_time = timezone.now()
        self.status = self.Status.ARRIVED

        if latitude and longitude:
            self.check_in_latitude = Decimal(str(latitude))
            self.check_in_longitude = Decimal(str(longitude))

        self.save()

    def start_work(self):
        """Start work at the site"""
        if self.status != self.Status.ARRIVED:
            raise ValidationError("Must be checked in to start work")

        self.status = self.Status.IN_PROGRESS
        self.save()

    def check_out(self, latitude=None, longitude=None, work_performed='', successful=True):
        """Check out from site visit"""
        if not self.can_check_out():
            raise ValidationError("Cannot check out from this visit")

        self.check_out_time = timezone.now()
        self.status = self.Status.COMPLETED
        self.visit_successful = successful

        if work_performed:
            self.work_performed = work_performed

        if latitude and longitude:
            self.check_out_latitude = Decimal(str(latitude))
            self.check_out_longitude = Decimal(str(longitude))

        # Calculate duration
        if self.check_in_time:
            duration = self.check_out_time - self.check_in_time
            self.actual_duration_hours = Decimal(str(duration.total_seconds() / 3600))

        self.save()

        # Update service site history
        self.service_site.update_service_history(self.visit_date)

    def mark_incomplete(self, reason=''):
        """Mark visit as incomplete"""
        self.status = self.Status.INCOMPLETE
        self.visit_successful = False
        self.follow_up_required = True
        if reason:
            self.follow_up_reason = reason
        self.save()

    def cancel(self, reason=''):
        """Cancel the visit"""
        if self.status in [self.Status.COMPLETED, self.Status.CANCELLED]:
            raise ValidationError("Cannot cancel completed or already cancelled visit")

        self.status = self.Status.CANCELLED
        if reason:
            self.issues_found = f"Cancelled: {reason}"
        self.save()

    def record_customer_signature(self, signature_name, rating=None, comments=''):
        """Record customer signature and feedback"""
        self.customer_signature = signature_name
        self.customer_signed_at = timezone.now()

        if rating:
            self.customer_satisfaction_rating = rating

        if comments:
            self.customer_comments = comments

        self.save()


class ServiceReport(models.Model):
    """
    Sprint 5: Service Report generation.

    Generates comprehensive service reports from site visits
    for customer documentation and internal records.

    Features:
    - Aggregates visit data
    - Cost calculations
    - Approval workflow
    - Customer delivery tracking

    ISO 9001 References:
    - Clause 7.5: Documented Information
    - Clause 8.5.1: Control of Production and Service Provision
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        REVIEW = "REVIEW", "Under Review"
        APPROVED = "APPROVED", "Approved"
        SENT = "SENT", "Sent to Customer"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Customer Acknowledged"
        ARCHIVED = "ARCHIVED", "Archived"

    # ===== IDENTIFICATION =====
    report_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique report number (auto-generated: RPT-YYYY-####)"
    )

    # ===== LINKED ENTITIES =====
    service_request = models.ForeignKey(
        'FieldServiceRequest',
        on_delete=models.PROTECT,
        related_name='service_reports',
        help_text="Related field service request"
    )

    site_visit = models.ForeignKey(
        'SiteVisit',
        on_delete=models.PROTECT,
        related_name='service_reports',
        help_text="Related site visit"
    )

    # ===== REPORT DETAILS =====
    report_date = models.DateField(
        help_text="Report date"
    )

    report_title = models.CharField(
        max_length=200,
        help_text="Report title"
    )

    # ===== CONTENT =====
    executive_summary = models.TextField(
        help_text="Executive summary of the service"
    )

    work_performed_detail = models.TextField(
        help_text="Detailed description of work performed"
    )

    findings = models.TextField(
        blank=True,
        help_text="Findings during service"
    )

    issues_identified = models.TextField(
        blank=True,
        help_text="Issues identified"
    )

    corrective_actions = models.TextField(
        blank=True,
        help_text="Corrective actions taken"
    )

    recommendations = models.TextField(
        blank=True,
        help_text="Recommendations for future"
    )

    # ===== ASSETS SERVICED =====
    drill_bits_serviced = models.ManyToManyField(
        'workorders.DrillBit',
        blank=True,
        related_name='service_reports',
        help_text="Drill bits serviced"
    )

    # ===== PARTS AND MATERIALS =====
    parts_used_detail = models.TextField(
        blank=True,
        help_text="Detailed parts/materials used"
    )

    parts_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total parts cost"
    )

    # ===== TIME AND LABOR =====
    labor_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Total labor hours"
    )

    labor_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total labor cost"
    )

    # ===== TOTALS =====
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total cost (parts + labor)"
    )

    # ===== ATTACHMENTS =====
    has_photos = models.BooleanField(
        default=False,
        help_text="Report includes photos"
    )

    has_diagrams = models.BooleanField(
        default=False,
        help_text="Report includes diagrams"
    )

    has_test_results = models.BooleanField(
        default=False,
        help_text="Report includes test results"
    )

    # ===== STATUS AND APPROVAL =====
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Report status"
    )

    submitted_for_review_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When submitted for review"
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_service_reports',
        help_text="User who approved the report"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the report was approved"
    )

    # ===== CUSTOMER DELIVERY =====
    sent_to_customer_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When sent to customer"
    )

    customer_email = models.EmailField(
        blank=True,
        help_text="Email sent to"
    )

    customer_acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When customer acknowledged"
    )

    # ===== AUDIT =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_service_reports',
        help_text="User who created this report"
    )

    class Meta:
        db_table = "service_reports"
        ordering = ['-report_date']
        verbose_name = "Service Report"
        verbose_name_plural = "Service Reports"
        indexes = [
            models.Index(fields=['report_number']),
            models.Index(fields=['report_date', 'status']),
            models.Index(fields=['service_request']),
        ]
        permissions = [
            ("can_approve_service_reports", "Can approve service reports"),
            ("can_send_to_customer", "Can send reports to customers"),
        ]

    def __str__(self):
        return f"{self.report_number} - {self.report_title}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate report number"""
        if not self.report_number:
            self.report_number = self._generate_report_number()
        super().save(*args, **kwargs)

    def _generate_report_number(self):
        """Generate unique report number: RPT-YYYY-####"""
        year = timezone.now().year

        last_report = ServiceReport.objects.filter(
            report_number__startswith=f"RPT-{year}-"
        ).order_by('-report_number').first()

        if last_report:
            try:
                last_num = int(last_report.report_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"RPT-{year}-{new_num:04d}"

    def calculate_total_cost(self):
        """Calculate total cost from parts and labor"""
        total = Decimal('0.00')
        if self.parts_cost:
            total += self.parts_cost
        if self.labor_cost:
            total += self.labor_cost
        self.total_cost = total
        return total

    def can_be_submitted(self):
        """Check if report can be submitted for review"""
        return self.status == self.Status.DRAFT

    def can_be_approved(self):
        """Check if report can be approved"""
        return self.status == self.Status.REVIEW

    def can_be_sent(self):
        """Check if report can be sent to customer"""
        return self.status == self.Status.APPROVED

    def submit_for_review(self):
        """Submit report for review"""
        if not self.can_be_submitted():
            raise ValidationError("Report cannot be submitted in current status")

        self.status = self.Status.REVIEW
        self.submitted_for_review_at = timezone.now()
        self.save()

    def approve(self, user):
        """Approve the report"""
        if not self.can_be_approved():
            raise ValidationError("Report cannot be approved in current status")

        self.status = self.Status.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()

    def send_to_customer(self, email=None):
        """Mark report as sent to customer"""
        if not self.can_be_sent():
            raise ValidationError("Report cannot be sent in current status")

        self.status = self.Status.SENT
        self.sent_to_customer_at = timezone.now()
        if email:
            self.customer_email = email
        self.save()

    def acknowledge_receipt(self):
        """Mark report as acknowledged by customer"""
        if self.status != self.Status.SENT:
            raise ValidationError("Can only acknowledge sent reports")

        self.status = self.Status.ACKNOWLEDGED
        self.customer_acknowledged_at = timezone.now()
        self.save()

    def archive(self):
        """Archive the report"""
        if self.status not in [self.Status.SENT, self.Status.ACKNOWLEDGED]:
            raise ValidationError("Can only archive sent or acknowledged reports")

        self.status = self.Status.ARCHIVED
        self.save()


# =============================================================================
# SPRINT 5 - WEEK 2: DRILL STRING FIELD OPERATIONS
# =============================================================================


class FieldDrillStringRun(models.Model):
    """
    Track drill bit runs (deployments) in the field.

    A run represents a single deployment of a drill bit in a well, capturing
    all operational parameters, depths, times, and performance data. This is
    the core model for field DRSS integration.

    Features:
    - Complete run lifecycle tracking (planned → in_hole → completed)
    - Depth and footage tracking (start/end depths, footage drilled)
    - Time tracking (spud time, out of hole time, total hours)
    - Parameter recording (WOB, RPM, torque, flow rate)
    - Formation tracking
    - Performance metrics (ROP, cost per foot)
    - Integration with well, rig, and service request

    Integrates with:
    - DrillBit: The bit being run
    - Well: Where the run takes place
    - Rig: Equipment used
    - FieldServiceRequest: Associated service request
    - ServiceSite: Location of the run
    - FieldRunData: Detailed operational data points

    ISO 9001 References:
    - Clause 8.5.1: Control of Production and Service Provision
    - Clause 8.5.2: Identification and Traceability

    Author: Sprint 5 Week 2 Implementation
    Date: December 2024
    """

    class Status(models.TextChoices):
        """Run status choices"""
        PLANNED = "PLANNED", "Planned"
        MOBILIZED = "MOBILIZED", "Mobilized to Site"
        RIG_UP = "RIG_UP", "Rigging Up"
        IN_HOLE = "IN_HOLE", "In Hole"
        DRILLING = "DRILLING", "Drilling"
        TRIPPING = "TRIPPING", "Tripping"
        OUT_OF_HOLE = "OUT_OF_HOLE", "Out of Hole"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class RunType(models.TextChoices):
        """Type of drilling run"""
        SURFACE = "SURFACE", "Surface Hole"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate Hole"
        PRODUCTION = "PRODUCTION", "Production Hole"
        SIDETRACK = "SIDETRACK", "Sidetrack"
        REAMING = "REAMING", "Reaming"
        CORING = "CORING", "Coring"
        OTHER = "OTHER", "Other"

    class TerminationReason(models.TextChoices):
        """Why the run ended"""
        TD_REACHED = "TD_REACHED", "TD Reached"
        CASING_POINT = "CASING_POINT", "Casing Point"
        BIT_WORN = "BIT_WORN", "Bit Worn"
        BIT_DAMAGED = "BIT_DAMAGED", "Bit Damaged"
        FORMATION_CHANGE = "FORMATION_CHANGE", "Formation Change"
        MECHANICAL_ISSUE = "MECHANICAL_ISSUE", "Mechanical Issue"
        CUSTOMER_REQUEST = "CUSTOMER_REQUEST", "Customer Request"
        TRIP_FOR_LOGGING = "TRIP_FOR_LOGGING", "Trip for Logging"
        OTHER = "OTHER", "Other"

    # ===== IDENTIFICATION =====

    run_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique run identifier (auto-generated: RUN-YYYY-####)"
    )

    run_sequence = models.IntegerField(
        default=1,
        help_text="Sequence number for this bit (1st run, 2nd run, etc.)"
    )

    # ===== RELATIONSHIPS =====

    drill_bit = models.ForeignKey(
        'workorders.DrillBit',
        on_delete=models.PROTECT,
        related_name='field_runs',
        help_text="Drill bit being run"
    )

    well = models.ForeignKey(
        'Well',
        on_delete=models.PROTECT,
        related_name='drill_string_runs',
        help_text="Well where run takes place"
    )

    rig = models.ForeignKey(
        'Rig',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drill_string_runs',
        help_text="Rig performing the drilling"
    )

    service_request = models.ForeignKey(
        'FieldServiceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drill_string_runs',
        help_text="Associated field service request"
    )

    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drill_string_runs',
        help_text="Service site location"
    )

    customer = models.ForeignKey(
        'Customer',
        on_delete=models.PROTECT,
        related_name='drill_string_runs',
        help_text="Customer for this run"
    )

    field_technician = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_runs',
        help_text="Field technician supervising the run"
    )

    # ===== RUN DETAILS =====

    run_type = models.CharField(
        max_length=20,
        choices=RunType.choices,
        default=RunType.PRODUCTION,
        help_text="Type of drilling run"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
        db_index=True,
        help_text="Current run status"
    )

    # ===== DEPTH TRACKING =====

    depth_in = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Depth when bit went in hole (feet)"
    )

    depth_out = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Depth when bit came out (feet)"
    )

    footage_drilled = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total footage drilled (calculated or entered)"
    )

    planned_depth = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Planned target depth (feet)"
    )

    # ===== TIME TRACKING =====

    planned_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Planned start date"
    )

    spud_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Time bit entered hole"
    )

    out_of_hole_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Time bit came out of hole"
    )

    total_rotating_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total rotating hours"
    )

    total_circulating_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total circulating hours"
    )

    total_on_bottom_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total on-bottom hours (actual drilling)"
    )

    non_productive_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Non-productive time (repairs, waiting, etc.)"
    )

    # ===== OPERATIONAL PARAMETERS =====

    avg_wob = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average Weight on Bit (klbs)"
    )

    max_wob = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum Weight on Bit (klbs)"
    )

    avg_rpm = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Average RPM"
    )

    max_rpm = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Maximum RPM"
    )

    avg_torque = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average torque (ft-lbs)"
    )

    max_torque = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum torque (ft-lbs)"
    )

    avg_flow_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average flow rate (GPM)"
    )

    avg_standpipe_pressure = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average standpipe pressure (PSI)"
    )

    mud_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Mud weight (PPG)"
    )

    # ===== FORMATION DATA =====

    formation_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Formation(s) drilled"
    )

    formation_description = models.TextField(
        blank=True,
        help_text="Detailed formation description"
    )

    lithology = models.CharField(
        max_length=200,
        blank=True,
        help_text="Rock type(s) encountered"
    )

    formation_hardness = models.CharField(
        max_length=50,
        blank=True,
        help_text="Formation hardness classification"
    )

    # ===== PERFORMANCE METRICS =====

    avg_rop = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average Rate of Penetration (ft/hr)"
    )

    max_rop = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum Rate of Penetration (ft/hr)"
    )

    cost_per_foot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost per foot drilled"
    )

    # ===== BIT CONDITION =====

    dull_grade_in = models.CharField(
        max_length=50,
        blank=True,
        help_text="IADC dull grade going in hole"
    )

    dull_grade_out = models.CharField(
        max_length=50,
        blank=True,
        help_text="IADC dull grade coming out of hole"
    )

    bit_condition_notes = models.TextField(
        blank=True,
        help_text="Notes on bit condition"
    )

    # ===== TERMINATION =====

    termination_reason = models.CharField(
        max_length=30,
        choices=TerminationReason.choices,
        blank=True,
        help_text="Reason run was terminated"
    )

    termination_notes = models.TextField(
        blank=True,
        help_text="Additional notes on run termination"
    )

    # ===== NOTES =====

    operational_notes = models.TextField(
        blank=True,
        help_text="Operational notes and observations"
    )

    issues_encountered = models.TextField(
        blank=True,
        help_text="Issues or problems during run"
    )

    recommendations = models.TextField(
        blank=True,
        help_text="Recommendations for future runs"
    )

    # ===== AUDIT TRAIL =====

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this run record was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this run was last updated"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_field_runs',
        help_text="User who created this run record"
    )

    class Meta:
        db_table = "field_drill_string_runs"
        ordering = ['-spud_time', '-created_at']
        verbose_name = "Field Drill String Run"
        verbose_name_plural = "Field Drill String Runs"
        indexes = [
            models.Index(fields=['run_number']),
            models.Index(fields=['drill_bit', 'status']),
            models.Index(fields=['well', 'status']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['spud_time']),
        ]
        permissions = [
            ("can_start_field_run", "Can start field drill string runs"),
            ("can_complete_field_run", "Can complete field drill string runs"),
            ("can_view_run_performance", "Can view run performance data"),
        ]

    def __str__(self):
        return f"{self.run_number} - {self.drill_bit}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate run number and calculate fields"""
        if not self.run_number:
            self.run_number = self._generate_run_number()

        # Calculate footage if depths are available
        if self.depth_in is not None and self.depth_out is not None:
            self.footage_drilled = self.depth_out - self.depth_in

        super().save(*args, **kwargs)

    def _generate_run_number(self):
        """Generate unique run number: RUN-YYYY-####"""
        year = timezone.now().year

        last_run = FieldDrillStringRun.objects.filter(
            run_number__startswith=f"RUN-{year}-"
        ).order_by('-run_number').first()

        if last_run:
            try:
                last_num = int(last_run.run_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"RUN-{year}-{new_num:04d}"

    # ===== PROPERTIES =====

    @property
    def total_hours(self):
        """Calculate total hours from spud to out of hole"""
        if self.spud_time and self.out_of_hole_time:
            delta = self.out_of_hole_time - self.spud_time
            return round(delta.total_seconds() / 3600, 2)
        return None

    @property
    def productive_hours(self):
        """Calculate productive hours (total minus non-productive)"""
        total = self.total_hours
        if total is not None:
            return round(total - float(self.non_productive_hours or 0), 2)
        return None

    @property
    def is_active(self):
        """Check if run is currently active"""
        return self.status in [
            self.Status.IN_HOLE,
            self.Status.DRILLING,
            self.Status.TRIPPING
        ]

    @property
    def is_completed(self):
        """Check if run is completed"""
        return self.status == self.Status.COMPLETED

    @property
    def depth_progress_percent(self):
        """Calculate progress toward planned depth"""
        if self.planned_depth and self.depth_out:
            return round((float(self.depth_out) / float(self.planned_depth)) * 100, 1)
        return None

    @property
    def calculated_rop(self):
        """Calculate ROP from footage and on-bottom hours"""
        if self.footage_drilled and self.total_on_bottom_hours:
            if float(self.total_on_bottom_hours) > 0:
                return round(float(self.footage_drilled) / float(self.total_on_bottom_hours), 2)
        return None

    # ===== STATUS CHECK METHODS =====

    def can_start(self):
        """Check if run can be started"""
        return self.status in [self.Status.PLANNED, self.Status.MOBILIZED, self.Status.RIG_UP]

    def can_complete(self):
        """Check if run can be completed"""
        return self.status in [self.Status.IN_HOLE, self.Status.DRILLING, self.Status.TRIPPING, self.Status.OUT_OF_HOLE]

    def can_cancel(self):
        """Check if run can be cancelled"""
        return self.status not in [self.Status.COMPLETED, self.Status.CANCELLED]

    # ===== WORKFLOW METHODS =====

    def start_run(self, depth_in=None, spud_time=None):
        """Start the drilling run"""
        if not self.can_start():
            raise ValidationError("Run cannot be started in current status")

        self.status = self.Status.IN_HOLE
        self.spud_time = spud_time or timezone.now()
        if depth_in is not None:
            self.depth_in = depth_in
        self.save()

    def complete_run(self, depth_out=None, termination_reason=None, dull_grade_out=None):
        """Complete the drilling run"""
        if not self.can_complete():
            raise ValidationError("Run cannot be completed in current status")

        self.status = self.Status.COMPLETED
        self.out_of_hole_time = timezone.now()

        if depth_out is not None:
            self.depth_out = depth_out
        if termination_reason:
            self.termination_reason = termination_reason
        if dull_grade_out:
            self.dull_grade_out = dull_grade_out

        self.save()

        # Update drill bit usage
        self._update_bit_usage()

    def cancel_run(self, reason=None):
        """Cancel the run"""
        if not self.can_cancel():
            raise ValidationError("Run cannot be cancelled")

        self.status = self.Status.CANCELLED
        if reason:
            self.termination_notes = reason
        self.save()

    def _update_bit_usage(self):
        """Update drill bit total hours and footage after run completion"""
        if self.drill_bit and self.is_completed:
            if self.total_hours:
                self.drill_bit.total_hours += Decimal(str(self.total_hours))
            if self.footage_drilled:
                self.drill_bit.total_footage += int(self.footage_drilled)
            self.drill_bit.run_count += 1
            self.drill_bit.save()


class FieldRunData(models.Model):
    """
    Capture detailed operational data points during a drill string run.

    This model stores time-series data collected during drilling operations,
    including real-time parameters like WOB, RPM, torque, and ROP at specific
    depths or time intervals.

    Features:
    - Time-stamped data points
    - Depth-correlated measurements
    - All key drilling parameters
    - Data quality indicators
    - Formation correlation

    Integrates with:
    - FieldDrillStringRun: Parent run record
    - FieldTechnician: Who recorded the data

    ISO 9001 References:
    - Clause 7.1.5: Monitoring and Measuring Resources
    - Clause 8.5.1: Control of Production and Service Provision

    Author: Sprint 5 Week 2 Implementation
    Date: December 2024
    """

    class DataSource(models.TextChoices):
        """Source of data"""
        MANUAL = "MANUAL", "Manual Entry"
        EDR = "EDR", "Electronic Drilling Recorder"
        WITS = "WITS", "WITS Transfer"
        MWD = "MWD", "MWD System"
        SENSOR = "SENSOR", "Direct Sensor"
        CALCULATED = "CALCULATED", "Calculated"

    class DataQuality(models.TextChoices):
        """Data quality indicator"""
        GOOD = "GOOD", "Good Quality"
        QUESTIONABLE = "QUESTIONABLE", "Questionable"
        POOR = "POOR", "Poor Quality"
        INTERPOLATED = "INTERPOLATED", "Interpolated"
        ESTIMATED = "ESTIMATED", "Estimated"

    # ===== RELATIONSHIPS =====

    field_run = models.ForeignKey(
        'FieldDrillStringRun',
        on_delete=models.CASCADE,
        related_name='run_data_points',
        help_text="Parent drilling run"
    )

    recorded_by = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_data_points',
        help_text="Technician who recorded this data"
    )

    # ===== TIMESTAMP & DEPTH =====

    timestamp = models.DateTimeField(
        db_index=True,
        help_text="When this data was recorded"
    )

    bit_depth = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_index=True,
        help_text="Bit depth at time of recording (feet)"
    )

    hole_depth = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total hole depth (feet)"
    )

    # ===== DRILLING PARAMETERS =====

    wob = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weight on Bit (klbs)"
    )

    rpm = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Rotary speed (RPM)"
    )

    torque = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Rotary torque (ft-lbs)"
    )

    rop = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Rate of Penetration (ft/hr)"
    )

    # ===== HYDRAULIC PARAMETERS =====

    flow_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Flow rate (GPM)"
    )

    standpipe_pressure = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Standpipe pressure (PSI)"
    )

    differential_pressure = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Differential pressure (PSI)"
    )

    ecd = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Equivalent Circulating Density (PPG)"
    )

    # ===== MUD PROPERTIES =====

    mud_weight_in = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Mud weight in (PPG)"
    )

    mud_weight_out = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Mud weight out (PPG)"
    )

    mud_temperature = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Mud temperature (F)"
    )

    funnel_viscosity = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Funnel viscosity (sec/qt)"
    )

    # ===== HOOK LOAD & BLOCK =====

    hook_load = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hook load (klbs)"
    )

    block_position = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Block position (feet)"
    )

    # ===== MSE & ENERGY =====

    mse = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Mechanical Specific Energy (PSI)"
    )

    bit_hydraulic_power = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Bit hydraulic horsepower (HP)"
    )

    # ===== FORMATION DATA =====

    formation = models.CharField(
        max_length=100,
        blank=True,
        help_text="Current formation being drilled"
    )

    gamma_ray = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Gamma ray reading (API)"
    )

    # ===== DATA QUALITY =====

    data_source = models.CharField(
        max_length=20,
        choices=DataSource.choices,
        default=DataSource.MANUAL,
        help_text="Source of this data"
    )

    data_quality = models.CharField(
        max_length=20,
        choices=DataQuality.choices,
        default=DataQuality.GOOD,
        help_text="Data quality indicator"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Notes about this data point"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    class Meta:
        db_table = "field_run_data"
        ordering = ['field_run', 'timestamp']
        verbose_name = "Field Run Data Point"
        verbose_name_plural = "Field Run Data Points"
        indexes = [
            models.Index(fields=['field_run', 'timestamp']),
            models.Index(fields=['field_run', 'bit_depth']),
            models.Index(fields=['timestamp']),
        ]
        permissions = [
            ("can_record_run_data", "Can record field run data"),
            ("can_edit_run_data", "Can edit field run data"),
        ]

    def __str__(self):
        return f"{self.field_run.run_number} @ {self.bit_depth}ft - {self.timestamp}"

    def clean(self):
        """Validate data point"""
        super().clean()

        # Validate depth is within run range
        if self.field_run:
            if self.field_run.depth_in and self.bit_depth < self.field_run.depth_in:
                raise ValidationError({
                    'bit_depth': 'Bit depth cannot be less than run starting depth'
                })

    @property
    def is_on_bottom(self):
        """Check if bit is on bottom (drilling)"""
        return self.wob is not None and float(self.wob) > 0 and self.rpm is not None and float(self.rpm) > 0

    @property
    def calculated_mse(self):
        """Calculate MSE from parameters if not directly provided"""
        if self.mse:
            return self.mse
        return None


class FieldPerformanceLog(models.Model):
    """
    Log performance metrics and analysis for field drill string runs.

    This model aggregates performance data for analysis, benchmarking,
    and optimization. It captures interval-based performance summaries
    and comparisons against targets.

    Features:
    - Interval-based performance summaries
    - Target vs actual comparisons
    - Formation-specific performance
    - Efficiency calculations
    - Benchmarking data

    Integrates with:
    - FieldDrillStringRun: The run being analyzed
    - Well: Well performance history

    ISO 9001 References:
    - Clause 9.1: Monitoring, Measurement, Analysis, and Evaluation
    - Clause 10.3: Continual Improvement

    Author: Sprint 5 Week 2 Implementation
    Date: December 2024
    """

    class IntervalType(models.TextChoices):
        """Type of logging interval"""
        HOURLY = "HOURLY", "Hourly"
        SHIFT = "SHIFT", "Per Shift"
        DAILY = "DAILY", "Daily"
        STAND = "STAND", "Per Stand"
        FORMATION = "FORMATION", "Per Formation"
        COMPLETE = "COMPLETE", "Complete Run"

    class PerformanceRating(models.TextChoices):
        """Overall performance rating"""
        EXCELLENT = "EXCELLENT", "Excellent"
        GOOD = "GOOD", "Good"
        AVERAGE = "AVERAGE", "Average"
        BELOW_AVERAGE = "BELOW_AVERAGE", "Below Average"
        POOR = "POOR", "Poor"

    # ===== IDENTIFICATION =====

    log_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique log identifier (auto-generated: PERF-YYYY-####)"
    )

    # ===== RELATIONSHIPS =====

    field_run = models.ForeignKey(
        'FieldDrillStringRun',
        on_delete=models.CASCADE,
        related_name='performance_logs',
        help_text="Associated drilling run"
    )

    logged_by = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performance_logs',
        help_text="Technician who created this log"
    )

    # ===== INTERVAL DEFINITION =====

    interval_type = models.CharField(
        max_length=20,
        choices=IntervalType.choices,
        default=IntervalType.DAILY,
        help_text="Type of interval this log covers"
    )

    start_time = models.DateTimeField(
        help_text="Start of logging interval"
    )

    end_time = models.DateTimeField(
        help_text="End of logging interval"
    )

    start_depth = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Depth at start of interval (feet)"
    )

    end_depth = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Depth at end of interval (feet)"
    )

    # ===== PERFORMANCE METRICS =====

    footage_drilled = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Footage drilled in this interval"
    )

    rotating_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Rotating hours in interval"
    )

    on_bottom_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="On-bottom hours in interval"
    )

    avg_rop = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Average ROP for interval (ft/hr)"
    )

    max_rop = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum ROP achieved (ft/hr)"
    )

    min_rop = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum ROP (ft/hr)"
    )

    # ===== TARGET COMPARISONS =====

    target_rop = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Target ROP for this formation (ft/hr)"
    )

    rop_variance_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="ROP variance from target (%)"
    )

    target_footage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Target footage for interval"
    )

    footage_variance_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Footage variance from target (%)"
    )

    # ===== OPERATIONAL PARAMETERS =====

    avg_wob = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average WOB (klbs)"
    )

    avg_rpm = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Average RPM"
    )

    avg_torque = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average torque (ft-lbs)"
    )

    avg_flow_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average flow rate (GPM)"
    )

    avg_mse = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average MSE (PSI)"
    )

    # ===== FORMATION DATA =====

    formation_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Formation(s) drilled in interval"
    )

    formation_hardness = models.CharField(
        max_length=50,
        blank=True,
        help_text="Formation hardness"
    )

    # ===== EFFICIENCY METRICS =====

    drilling_efficiency = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Drilling efficiency (on-bottom/rotating) %"
    )

    connection_time_avg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average connection time (minutes)"
    )

    trip_speed = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Trip speed (ft/hr)"
    )

    # ===== RATING & ANALYSIS =====

    performance_rating = models.CharField(
        max_length=20,
        choices=PerformanceRating.choices,
        default=PerformanceRating.AVERAGE,
        help_text="Overall performance rating"
    )

    performance_notes = models.TextField(
        blank=True,
        help_text="Performance analysis notes"
    )

    optimization_recommendations = models.TextField(
        blank=True,
        help_text="Recommendations for optimization"
    )

    # ===== BENCHMARKING =====

    offset_well_comparison = models.TextField(
        blank=True,
        help_text="Comparison to offset wells"
    )

    historical_comparison = models.TextField(
        blank=True,
        help_text="Comparison to historical runs"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this log was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this log was last updated"
    )

    class Meta:
        db_table = "field_performance_logs"
        ordering = ['-start_time']
        verbose_name = "Field Performance Log"
        verbose_name_plural = "Field Performance Logs"
        indexes = [
            models.Index(fields=['log_number']),
            models.Index(fields=['field_run', 'start_time']),
            models.Index(fields=['performance_rating']),
        ]
        permissions = [
            ("can_create_performance_logs", "Can create performance logs"),
            ("can_analyze_performance", "Can analyze performance data"),
        ]

    def __str__(self):
        return f"{self.log_number} - {self.field_run.run_number}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate log number and calculate metrics"""
        if not self.log_number:
            self.log_number = self._generate_log_number()

        # Calculate variances
        self._calculate_variances()

        # Calculate drilling efficiency
        self._calculate_efficiency()

        super().save(*args, **kwargs)

    def _generate_log_number(self):
        """Generate unique log number: PERF-YYYY-####"""
        year = timezone.now().year

        last_log = FieldPerformanceLog.objects.filter(
            log_number__startswith=f"PERF-{year}-"
        ).order_by('-log_number').first()

        if last_log:
            try:
                last_num = int(last_log.log_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"PERF-{year}-{new_num:04d}"

    def _calculate_variances(self):
        """Calculate variance percentages"""
        if self.target_rop and self.avg_rop:
            self.rop_variance_percent = round(
                ((float(self.avg_rop) - float(self.target_rop)) / float(self.target_rop)) * 100, 2
            )

        if self.target_footage and self.footage_drilled:
            self.footage_variance_percent = round(
                ((float(self.footage_drilled) - float(self.target_footage)) / float(self.target_footage)) * 100, 2
            )

    def _calculate_efficiency(self):
        """Calculate drilling efficiency"""
        if self.rotating_hours and float(self.rotating_hours) > 0 and self.on_bottom_hours:
            self.drilling_efficiency = round(
                (float(self.on_bottom_hours) / float(self.rotating_hours)) * 100, 2
            )

    @property
    def interval_duration_hours(self):
        """Calculate interval duration in hours"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return round(delta.total_seconds() / 3600, 2)
        return None

    @property
    def is_above_target(self):
        """Check if performance is above target"""
        if self.rop_variance_percent is not None:
            return float(self.rop_variance_percent) > 0
        return None


class FieldInspection(models.Model):
    """
    Record field inspections of drill bits and equipment.

    This model tracks inspections performed in the field before, during,
    or after drilling operations. It captures detailed findings, measurements,
    and recommendations.

    Features:
    - Pre-run and post-run inspections
    - Detailed component-level findings
    - Photo references
    - Grading and measurements
    - Recommendations for action

    Integrates with:
    - DrillBit: The bit being inspected
    - FieldDrillStringRun: Associated run (if any)
    - SiteVisit: Site visit during which inspection occurred
    - FieldTechnician: Inspector

    ISO 9001 References:
    - Clause 8.6: Release of Products and Services
    - Clause 8.5.2: Identification and Traceability

    Author: Sprint 5 Week 2 Implementation
    Date: December 2024
    """

    class InspectionType(models.TextChoices):
        """Type of inspection"""
        PRE_RUN = "PRE_RUN", "Pre-Run Inspection"
        MID_RUN = "MID_RUN", "Mid-Run Inspection"
        POST_RUN = "POST_RUN", "Post-Run Inspection"
        DULL_GRADING = "DULL_GRADING", "Dull Grading"
        DAMAGE_ASSESSMENT = "DAMAGE_ASSESSMENT", "Damage Assessment"
        RECEIVING = "RECEIVING", "Receiving Inspection"
        ROUTINE = "ROUTINE", "Routine Inspection"

    class Status(models.TextChoices):
        """Inspection status"""
        SCHEDULED = "SCHEDULED", "Scheduled"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class OverallCondition(models.TextChoices):
        """Overall bit condition rating"""
        EXCELLENT = "EXCELLENT", "Excellent - Ready for Use"
        GOOD = "GOOD", "Good - Minor Wear"
        FAIR = "FAIR", "Fair - Significant Wear"
        POOR = "POOR", "Poor - Requires Repair"
        DAMAGED = "DAMAGED", "Damaged - May Not Be Repairable"
        SCRAPPED = "SCRAPPED", "Scrapped - Beyond Repair"

    class Recommendation(models.TextChoices):
        """Recommended action"""
        RUN_AS_IS = "RUN_AS_IS", "Run As-Is"
        MINOR_REPAIR = "MINOR_REPAIR", "Minor Repair Needed"
        MAJOR_REPAIR = "MAJOR_REPAIR", "Major Repair Needed"
        REWORK = "REWORK", "Rework Required"
        SCRAP = "SCRAP", "Scrap Recommended"
        FURTHER_EVALUATION = "FURTHER_EVALUATION", "Further Evaluation Needed"

    # ===== IDENTIFICATION =====

    inspection_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique inspection identifier (auto-generated: INSP-YYYY-####)"
    )

    # ===== RELATIONSHIPS =====

    drill_bit = models.ForeignKey(
        'workorders.DrillBit',
        on_delete=models.PROTECT,
        related_name='field_inspections',
        help_text="Drill bit being inspected"
    )

    field_run = models.ForeignKey(
        'FieldDrillStringRun',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspections',
        help_text="Associated drilling run"
    )

    site_visit = models.ForeignKey(
        'SiteVisit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspections',
        help_text="Site visit during which inspection occurred"
    )

    inspector = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.SET_NULL,
        null=True,
        related_name='conducted_inspections',
        help_text="Technician who performed inspection"
    )

    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inspections',
        help_text="Location of inspection"
    )

    # ===== INSPECTION DETAILS =====

    inspection_type = models.CharField(
        max_length=20,
        choices=InspectionType.choices,
        default=InspectionType.POST_RUN,
        help_text="Type of inspection"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True,
        help_text="Inspection status"
    )

    inspection_date = models.DateField(
        help_text="Date of inspection"
    )

    inspection_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time inspection started"
    )

    completion_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time inspection completed"
    )

    # ===== DULL GRADING (IADC) =====

    dull_grade = models.CharField(
        max_length=50,
        blank=True,
        help_text="IADC dull grade (e.g., 2-2-WT-A-X-I-NO-TD)"
    )

    inner_rows = models.CharField(
        max_length=10,
        blank=True,
        help_text="Inner rows condition (0-8)"
    )

    outer_rows = models.CharField(
        max_length=10,
        blank=True,
        help_text="Outer rows condition (0-8)"
    )

    dull_characteristic = models.CharField(
        max_length=20,
        blank=True,
        help_text="Primary dull characteristic"
    )

    location = models.CharField(
        max_length=20,
        blank=True,
        help_text="Location of wear/damage"
    )

    bearing_seal = models.CharField(
        max_length=20,
        blank=True,
        help_text="Bearing/seal condition"
    )

    gauge = models.CharField(
        max_length=20,
        blank=True,
        help_text="Gauge condition"
    )

    other_characteristic = models.CharField(
        max_length=50,
        blank=True,
        help_text="Other dull characteristic"
    )

    reason_pulled = models.CharField(
        max_length=50,
        blank=True,
        help_text="Reason pulled from hole"
    )

    # ===== MEASUREMENTS =====

    gauge_measurement = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Gauge measurement (inches)"
    )

    gauge_wear = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Gauge wear amount (inches)"
    )

    body_od = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Body outer diameter (inches)"
    )

    cutter_count_damaged = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of damaged cutters"
    )

    cutter_count_missing = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of missing cutters"
    )

    nozzle_condition = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nozzle condition and sizes"
    )

    # ===== CONDITION ASSESSMENT =====

    overall_condition = models.CharField(
        max_length=20,
        choices=OverallCondition.choices,
        default=OverallCondition.GOOD,
        help_text="Overall condition rating"
    )

    blade_condition = models.TextField(
        blank=True,
        help_text="Blade condition details"
    )

    cutter_condition = models.TextField(
        blank=True,
        help_text="Cutter condition details"
    )

    body_condition = models.TextField(
        blank=True,
        help_text="Body condition details"
    )

    connection_condition = models.TextField(
        blank=True,
        help_text="Connection/thread condition"
    )

    junk_damage = models.BooleanField(
        default=False,
        help_text="Evidence of junk damage"
    )

    junk_damage_description = models.TextField(
        blank=True,
        help_text="Description of junk damage"
    )

    # ===== RECOMMENDATION =====

    recommendation = models.CharField(
        max_length=30,
        choices=Recommendation.choices,
        default=Recommendation.FURTHER_EVALUATION,
        help_text="Recommended action"
    )

    recommendation_notes = models.TextField(
        blank=True,
        help_text="Detailed recommendation notes"
    )

    estimated_remaining_life = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated remaining footage (feet)"
    )

    # ===== PHOTOS & DOCUMENTS =====

    has_photos = models.BooleanField(
        default=False,
        help_text="Photos were taken during inspection"
    )

    photo_count = models.IntegerField(
        default=0,
        help_text="Number of photos taken"
    )

    photo_notes = models.TextField(
        blank=True,
        help_text="Notes about photos"
    )

    # ===== NOTES =====

    findings = models.TextField(
        blank=True,
        help_text="Detailed inspection findings"
    )

    customer_representative = models.CharField(
        max_length=200,
        blank=True,
        help_text="Customer representative present"
    )

    customer_signature = models.BooleanField(
        default=False,
        help_text="Customer signed inspection report"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_field_inspections',
        help_text="User who created this record"
    )

    class Meta:
        db_table = "field_inspections"
        ordering = ['-inspection_date', '-inspection_time']
        verbose_name = "Field Inspection"
        verbose_name_plural = "Field Inspections"
        indexes = [
            models.Index(fields=['inspection_number']),
            models.Index(fields=['drill_bit', 'inspection_type']),
            models.Index(fields=['inspection_date', 'status']),
            models.Index(fields=['overall_condition']),
        ]
        permissions = [
            ("can_conduct_inspections", "Can conduct field inspections"),
            ("can_approve_inspections", "Can approve inspection reports"),
        ]

    def __str__(self):
        return f"{self.inspection_number} - {self.drill_bit}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate inspection number"""
        if not self.inspection_number:
            self.inspection_number = self._generate_inspection_number()
        super().save(*args, **kwargs)

    def _generate_inspection_number(self):
        """Generate unique inspection number: INSP-YYYY-####"""
        year = timezone.now().year

        last_insp = FieldInspection.objects.filter(
            inspection_number__startswith=f"INSP-{year}-"
        ).order_by('-inspection_number').first()

        if last_insp:
            try:
                last_num = int(last_insp.inspection_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"INSP-{year}-{new_num:04d}"

    # ===== PROPERTIES =====

    @property
    def is_completed(self):
        """Check if inspection is completed"""
        return self.status == self.Status.COMPLETED

    @property
    def requires_repair(self):
        """Check if inspection recommends repair"""
        return self.recommendation in [
            self.Recommendation.MINOR_REPAIR,
            self.Recommendation.MAJOR_REPAIR,
            self.Recommendation.REWORK
        ]

    @property
    def duration_minutes(self):
        """Calculate inspection duration"""
        if self.inspection_time and self.completion_time:
            from datetime import datetime
            start = datetime.combine(self.inspection_date, self.inspection_time)
            end = datetime.combine(self.inspection_date, self.completion_time)
            delta = end - start
            return round(delta.total_seconds() / 60, 0)
        return None

    # ===== WORKFLOW METHODS =====

    def start_inspection(self):
        """Start the inspection"""
        if self.status != self.Status.SCHEDULED:
            raise ValidationError("Can only start scheduled inspections")

        self.status = self.Status.IN_PROGRESS
        self.inspection_time = timezone.now().time()
        self.save()

    def complete_inspection(self, dull_grade=None, overall_condition=None, recommendation=None):
        """Complete the inspection"""
        if self.status != self.Status.IN_PROGRESS:
            raise ValidationError("Can only complete in-progress inspections")

        self.status = self.Status.COMPLETED
        self.completion_time = timezone.now().time()

        if dull_grade:
            self.dull_grade = dull_grade
        if overall_condition:
            self.overall_condition = overall_condition
        if recommendation:
            self.recommendation = recommendation

        self.save()


class RunHours(models.Model):
    """
    Track running hours for drill bits.

    This model records incremental hours of operation for drill bits,
    supporting both real-time tracking during runs and historical
    hour logging. Essential for maintenance scheduling and cost tracking.

    Features:
    - Incremental hour logging
    - Multiple hour types (rotating, circulating, on-bottom)
    - Run association
    - Automatic cumulative calculations
    - Hour validation

    Integrates with:
    - DrillBit: The bit being tracked
    - FieldDrillStringRun: Associated run (if any)
    - FieldTechnician: Who recorded the hours

    ISO 9001 References:
    - Clause 7.1.5.2: Measurement Traceability
    - Clause 8.5.2: Identification and Traceability

    Author: Sprint 5 Week 2 Implementation
    Date: December 2024
    """

    class HourType(models.TextChoices):
        """Type of hours being recorded"""
        ROTATING = "ROTATING", "Rotating Hours"
        CIRCULATING = "CIRCULATING", "Circulating Hours"
        ON_BOTTOM = "ON_BOTTOM", "On Bottom Hours"
        TOTAL = "TOTAL", "Total Hours"
        REAMING = "REAMING", "Reaming Hours"
        TRIPPING = "TRIPPING", "Tripping Hours"

    class EntrySource(models.TextChoices):
        """Source of hour entry"""
        MANUAL = "MANUAL", "Manual Entry"
        EDR = "EDR", "EDR System"
        CALCULATED = "CALCULATED", "Calculated from Run"
        IMPORTED = "IMPORTED", "Imported Data"

    # ===== RELATIONSHIPS =====

    drill_bit = models.ForeignKey(
        'workorders.DrillBit',
        on_delete=models.CASCADE,
        related_name='hour_logs',
        help_text="Drill bit being tracked"
    )

    field_run = models.ForeignKey(
        'FieldDrillStringRun',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hour_logs',
        help_text="Associated drilling run"
    )

    recorded_by = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_hours',
        help_text="Technician who recorded hours"
    )

    # ===== HOUR DETAILS =====

    hour_type = models.CharField(
        max_length=20,
        choices=HourType.choices,
        default=HourType.TOTAL,
        help_text="Type of hours"
    )

    hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Hours to add"
    )

    cumulative_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cumulative hours after this entry"
    )

    # ===== TIMING =====

    record_date = models.DateField(
        help_text="Date hours were accumulated"
    )

    start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Start time of operation"
    )

    end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="End time of operation"
    )

    # ===== CONTEXT =====

    entry_source = models.CharField(
        max_length=20,
        choices=EntrySource.choices,
        default=EntrySource.MANUAL,
        help_text="Source of this entry"
    )

    depth_at_start = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Depth at start of period (feet)"
    )

    depth_at_end = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Depth at end of period (feet)"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Notes about this hour entry"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_run_hours',
        help_text="User who created this record"
    )

    class Meta:
        db_table = "run_hours"
        ordering = ['-record_date', '-created_at']
        verbose_name = "Run Hours"
        verbose_name_plural = "Run Hours"
        indexes = [
            models.Index(fields=['drill_bit', 'hour_type']),
            models.Index(fields=['drill_bit', 'record_date']),
            models.Index(fields=['field_run']),
        ]
        permissions = [
            ("can_record_run_hours", "Can record run hours"),
            ("can_adjust_hours", "Can adjust hour entries"),
        ]

    def __str__(self):
        return f"{self.drill_bit} - {self.hours}hrs ({self.hour_type}) - {self.record_date}"

    def save(self, *args, **kwargs):
        """Override save to calculate cumulative hours"""
        if self.cumulative_hours is None:
            self._calculate_cumulative()
        super().save(*args, **kwargs)

        # Update drill bit total hours
        self._update_bit_hours()

    def _calculate_cumulative(self):
        """Calculate cumulative hours for this bit and hour type"""
        previous = RunHours.objects.filter(
            drill_bit=self.drill_bit,
            hour_type=self.hour_type,
            record_date__lte=self.record_date
        ).exclude(pk=self.pk).order_by('-record_date', '-created_at').first()

        if previous and previous.cumulative_hours:
            self.cumulative_hours = previous.cumulative_hours + self.hours
        else:
            self.cumulative_hours = self.hours

    def _update_bit_hours(self):
        """Update drill bit total hours"""
        if self.drill_bit and self.hour_type == self.HourType.TOTAL:
            total = RunHours.objects.filter(
                drill_bit=self.drill_bit,
                hour_type=self.HourType.TOTAL
            ).aggregate(total=models.Sum('hours'))['total'] or Decimal('0')

            self.drill_bit.total_hours = total
            self.drill_bit.save(update_fields=['total_hours'])

    def clean(self):
        """Validate hour entry"""
        super().clean()

        if self.hours < 0:
            raise ValidationError({'hours': 'Hours cannot be negative'})

        if self.start_time and self.end_time:
            if self.end_time < self.start_time:
                raise ValidationError({
                    'end_time': 'End time cannot be before start time'
                })

    @property
    def footage_drilled(self):
        """Calculate footage drilled during this period"""
        if self.depth_at_start is not None and self.depth_at_end is not None:
            return self.depth_at_end - self.depth_at_start
        return None


class FieldIncident(models.Model):
    """
    Record incidents that occur during field operations.

    This model captures any incidents, accidents, near-misses, or
    equipment failures that occur in the field. Essential for
    safety tracking, root cause analysis, and continuous improvement.

    Features:
    - Multiple incident categories
    - Severity classification
    - Investigation tracking
    - Corrective action management
    - Regulatory reporting support

    Integrates with:
    - SiteVisit: Site visit during incident
    - FieldDrillStringRun: Run during incident
    - DrillBit: Equipment involved
    - ServiceSite: Location
    - FieldTechnician: Personnel involved

    ISO 9001 References:
    - Clause 10.2: Nonconformity and Corrective Action
    - Clause 8.7: Control of Nonconforming Outputs

    Author: Sprint 5 Week 2 Implementation
    Date: December 2024
    """

    class IncidentCategory(models.TextChoices):
        """Category of incident"""
        SAFETY = "SAFETY", "Safety Incident"
        ENVIRONMENTAL = "ENVIRONMENTAL", "Environmental Incident"
        EQUIPMENT_FAILURE = "EQUIPMENT_FAILURE", "Equipment Failure"
        NEAR_MISS = "NEAR_MISS", "Near Miss"
        QUALITY = "QUALITY", "Quality Issue"
        PROCEDURAL = "PROCEDURAL", "Procedural Violation"
        PROPERTY_DAMAGE = "PROPERTY_DAMAGE", "Property Damage"
        DOWNHOLE = "DOWNHOLE", "Downhole Incident"
        OTHER = "OTHER", "Other"

    class Severity(models.TextChoices):
        """Severity level"""
        MINOR = "MINOR", "Minor - No Injury/Minimal Impact"
        MODERATE = "MODERATE", "Moderate - First Aid/Limited Impact"
        SERIOUS = "SERIOUS", "Serious - Medical Treatment/Significant Impact"
        SEVERE = "SEVERE", "Severe - Lost Time/Major Impact"
        CRITICAL = "CRITICAL", "Critical - Life Threatening/Catastrophic"

    class Status(models.TextChoices):
        """Incident status"""
        REPORTED = "REPORTED", "Reported"
        UNDER_INVESTIGATION = "UNDER_INVESTIGATION", "Under Investigation"
        ROOT_CAUSE_IDENTIFIED = "ROOT_CAUSE_IDENTIFIED", "Root Cause Identified"
        CORRECTIVE_ACTION = "CORRECTIVE_ACTION", "Corrective Action in Progress"
        CLOSED = "CLOSED", "Closed"
        REOPENED = "REOPENED", "Reopened"

    class InjuryType(models.TextChoices):
        """Type of injury if applicable"""
        NONE = "NONE", "No Injury"
        FIRST_AID = "FIRST_AID", "First Aid Case"
        MEDICAL_TREATMENT = "MEDICAL_TREATMENT", "Medical Treatment Case"
        RESTRICTED_WORK = "RESTRICTED_WORK", "Restricted Work Case"
        LOST_TIME = "LOST_TIME", "Lost Time Injury"
        FATALITY = "FATALITY", "Fatality"

    # ===== IDENTIFICATION =====

    incident_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique incident identifier (auto-generated: INC-YYYY-####)"
    )

    # ===== RELATIONSHIPS =====

    site_visit = models.ForeignKey(
        'SiteVisit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents',
        help_text="Site visit during which incident occurred"
    )

    field_run = models.ForeignKey(
        'FieldDrillStringRun',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents',
        help_text="Drilling run during incident"
    )

    drill_bit = models.ForeignKey(
        'workorders.DrillBit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='field_incidents',
        help_text="Equipment involved in incident"
    )

    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents',
        help_text="Location of incident"
    )

    reported_by = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_incidents',
        help_text="Person who reported the incident"
    )

    customer = models.ForeignKey(
        'Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='field_incidents',
        help_text="Customer at time of incident"
    )

    # ===== INCIDENT DETAILS =====

    category = models.CharField(
        max_length=30,
        choices=IncidentCategory.choices,
        default=IncidentCategory.OTHER,
        help_text="Incident category"
    )

    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MINOR,
        help_text="Severity level"
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.REPORTED,
        db_index=True,
        help_text="Current status"
    )

    incident_title = models.CharField(
        max_length=200,
        help_text="Brief title describing incident"
    )

    incident_date = models.DateField(
        help_text="Date incident occurred"
    )

    incident_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time incident occurred"
    )

    location_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Specific location (e.g., rig floor, pipe deck)"
    )

    # ===== DESCRIPTION =====

    description = models.TextField(
        help_text="Detailed description of what happened"
    )

    immediate_actions = models.TextField(
        blank=True,
        help_text="Immediate actions taken"
    )

    conditions_at_time = models.TextField(
        blank=True,
        help_text="Conditions at time of incident (weather, visibility, etc.)"
    )

    equipment_involved = models.TextField(
        blank=True,
        help_text="Equipment involved in incident"
    )

    # ===== INJURY INFORMATION =====

    injury_type = models.CharField(
        max_length=30,
        choices=InjuryType.choices,
        default=InjuryType.NONE,
        help_text="Type of injury if applicable"
    )

    persons_injured = models.IntegerField(
        default=0,
        help_text="Number of persons injured"
    )

    injury_description = models.TextField(
        blank=True,
        help_text="Description of injuries"
    )

    body_parts_affected = models.CharField(
        max_length=200,
        blank=True,
        help_text="Body parts affected"
    )

    medical_treatment_provided = models.TextField(
        blank=True,
        help_text="Medical treatment provided"
    )

    days_lost = models.IntegerField(
        default=0,
        help_text="Days lost due to injury"
    )

    # ===== DAMAGE INFORMATION =====

    property_damage = models.BooleanField(
        default=False,
        help_text="Property damage occurred"
    )

    damage_description = models.TextField(
        blank=True,
        help_text="Description of damage"
    )

    estimated_damage_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated cost of damage"
    )

    # ===== INVESTIGATION =====

    investigation_started = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When investigation began"
    )

    investigation_lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_investigations',
        help_text="Person leading investigation"
    )

    root_cause = models.TextField(
        blank=True,
        help_text="Root cause analysis findings"
    )

    contributing_factors = models.TextField(
        blank=True,
        help_text="Contributing factors identified"
    )

    lessons_learned = models.TextField(
        blank=True,
        help_text="Lessons learned from incident"
    )

    # ===== CORRECTIVE ACTIONS =====

    corrective_actions = models.TextField(
        blank=True,
        help_text="Corrective actions required"
    )

    preventive_actions = models.TextField(
        blank=True,
        help_text="Preventive actions to avoid recurrence"
    )

    corrective_action_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Due date for corrective actions"
    )

    corrective_action_completed = models.BooleanField(
        default=False,
        help_text="Corrective actions completed"
    )

    corrective_action_completed_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date corrective actions completed"
    )

    # ===== REPORTING =====

    reportable_to_client = models.BooleanField(
        default=False,
        help_text="Incident is reportable to client"
    )

    reported_to_client = models.BooleanField(
        default=False,
        help_text="Incident has been reported to client"
    )

    reported_to_client_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date reported to client"
    )

    reportable_to_authority = models.BooleanField(
        default=False,
        help_text="Incident is reportable to regulatory authority"
    )

    reported_to_authority = models.BooleanField(
        default=False,
        help_text="Incident has been reported to authority"
    )

    authority_report_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Regulatory authority report number"
    )

    # ===== CLOSURE =====

    closed_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date incident was closed"
    )

    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_incidents',
        help_text="User who closed the incident"
    )

    closure_notes = models.TextField(
        blank=True,
        help_text="Notes on incident closure"
    )

    # ===== PHOTOS & DOCUMENTS =====

    has_photos = models.BooleanField(
        default=False,
        help_text="Photos are attached"
    )

    photo_count = models.IntegerField(
        default=0,
        help_text="Number of photos"
    )

    has_documents = models.BooleanField(
        default=False,
        help_text="Documents are attached"
    )

    # ===== WITNESS INFORMATION =====

    witnesses = models.TextField(
        blank=True,
        help_text="Names of witnesses"
    )

    witness_statements = models.TextField(
        blank=True,
        help_text="Summary of witness statements"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_field_incidents',
        help_text="User who created this record"
    )

    class Meta:
        db_table = "field_incidents"
        ordering = ['-incident_date', '-incident_time']
        verbose_name = "Field Incident"
        verbose_name_plural = "Field Incidents"
        indexes = [
            models.Index(fields=['incident_number']),
            models.Index(fields=['incident_date', 'severity']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['service_site', 'incident_date']),
        ]
        permissions = [
            ("can_report_incidents", "Can report field incidents"),
            ("can_investigate_incidents", "Can investigate incidents"),
            ("can_close_incidents", "Can close incidents"),
        ]

    def __str__(self):
        return f"{self.incident_number} - {self.incident_title}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate incident number"""
        if not self.incident_number:
            self.incident_number = self._generate_incident_number()
        super().save(*args, **kwargs)

    def _generate_incident_number(self):
        """Generate unique incident number: INC-YYYY-####"""
        year = timezone.now().year

        last_inc = FieldIncident.objects.filter(
            incident_number__startswith=f"INC-{year}-"
        ).order_by('-incident_number').first()

        if last_inc:
            try:
                last_num = int(last_inc.incident_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"INC-{year}-{new_num:04d}"

    # ===== PROPERTIES =====

    @property
    def is_open(self):
        """Check if incident is still open"""
        return self.status not in [self.Status.CLOSED]

    @property
    def is_serious(self):
        """Check if incident is serious or above"""
        return self.severity in [
            self.Severity.SERIOUS,
            self.Severity.SEVERE,
            self.Severity.CRITICAL
        ]

    @property
    def has_injuries(self):
        """Check if incident resulted in injuries"""
        return self.injury_type != self.InjuryType.NONE

    @property
    def days_open(self):
        """Calculate days incident has been open"""
        if self.closed_date:
            return (self.closed_date - self.incident_date).days
        return (timezone.now().date() - self.incident_date).days

    @property
    def corrective_action_overdue(self):
        """Check if corrective actions are overdue"""
        if self.corrective_action_due_date and not self.corrective_action_completed:
            return timezone.now().date() > self.corrective_action_due_date
        return False

    # ===== WORKFLOW METHODS =====

    def start_investigation(self, lead_user):
        """Start investigation of incident"""
        if self.status not in [self.Status.REPORTED, self.Status.REOPENED]:
            raise ValidationError("Can only start investigation for reported or reopened incidents")

        self.status = self.Status.UNDER_INVESTIGATION
        self.investigation_started = timezone.now()
        self.investigation_lead = lead_user
        self.save()

    def record_root_cause(self, root_cause, contributing_factors=None):
        """Record root cause findings"""
        if self.status != self.Status.UNDER_INVESTIGATION:
            raise ValidationError("Can only record root cause during investigation")

        self.status = self.Status.ROOT_CAUSE_IDENTIFIED
        self.root_cause = root_cause
        if contributing_factors:
            self.contributing_factors = contributing_factors
        self.save()

    def close_incident(self, user, notes=None):
        """Close the incident"""
        if self.status == self.Status.CLOSED:
            raise ValidationError("Incident is already closed")

        self.status = self.Status.CLOSED
        self.closed_date = timezone.now().date()
        self.closed_by = user
        if notes:
            self.closure_notes = notes
        self.save()

    def reopen_incident(self, reason):
        """Reopen a closed incident"""
        if self.status != self.Status.CLOSED:
            raise ValidationError("Can only reopen closed incidents")

        self.status = self.Status.REOPENED
        self.closed_date = None
        self.closed_by = None
        self.closure_notes = f"REOPENED: {reason}\n\nPrevious notes: {self.closure_notes}"
        self.save()


# =============================================================================
# SPRINT 5 - WEEK 3: FIELD DATA CAPTURE & INTEGRATION
# =============================================================================


class FieldDataEntry(models.Model):
    """
    Capture structured field data entries from technicians.

    This model provides a flexible mechanism for capturing various types
    of field data including measurements, observations, readings, and
    custom data points. Supports validation rules and data templates.

    Features:
    - Multiple data types (numeric, text, boolean, date, selection)
    - Validation rules per entry type
    - Template-based data collection
    - Batch entry support
    - GPS location tagging
    - Photo attachments

    Integrates with:
    - SiteVisit: Visit during which data was collected
    - FieldDrillStringRun: Associated drilling run
    - FieldTechnician: Technician who entered data
    - ServiceSite: Location of data collection

    ISO 9001 References:
    - Clause 7.1.5: Monitoring and Measuring Resources
    - Clause 8.5.1: Control of Production and Service Provision

    Author: Sprint 5 Week 3 Implementation
    Date: December 2024
    """

    class DataType(models.TextChoices):
        """Type of data being captured"""
        NUMERIC = "NUMERIC", "Numeric Value"
        TEXT = "TEXT", "Text/String"
        BOOLEAN = "BOOLEAN", "Yes/No"
        DATE = "DATE", "Date"
        DATETIME = "DATETIME", "Date and Time"
        SELECTION = "SELECTION", "Selection from List"
        MEASUREMENT = "MEASUREMENT", "Measurement with Unit"
        COORDINATES = "COORDINATES", "GPS Coordinates"
        PERCENTAGE = "PERCENTAGE", "Percentage"
        CURRENCY = "CURRENCY", "Currency Amount"

    class EntryCategory(models.TextChoices):
        """Category of data entry"""
        OPERATIONAL = "OPERATIONAL", "Operational Data"
        SAFETY = "SAFETY", "Safety Observation"
        QUALITY = "QUALITY", "Quality Check"
        ENVIRONMENTAL = "ENVIRONMENTAL", "Environmental Data"
        EQUIPMENT = "EQUIPMENT", "Equipment Reading"
        INSPECTION = "INSPECTION", "Inspection Finding"
        MEASUREMENT = "MEASUREMENT", "Measurement"
        OBSERVATION = "OBSERVATION", "General Observation"
        CUSTOMER = "CUSTOMER", "Customer Feedback"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        """Entry status"""
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        VALIDATED = "VALIDATED", "Validated"
        REJECTED = "REJECTED", "Rejected"
        ARCHIVED = "ARCHIVED", "Archived"

    # ===== IDENTIFICATION =====

    entry_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique entry identifier (auto-generated: DATA-YYYY-####)"
    )

    # ===== RELATIONSHIPS =====

    site_visit = models.ForeignKey(
        'SiteVisit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='data_entries',
        help_text="Site visit during which data was collected"
    )

    field_run = models.ForeignKey(
        'FieldDrillStringRun',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='data_entries',
        help_text="Associated drilling run"
    )

    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='data_entries',
        help_text="Location where data was collected"
    )

    entered_by = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.SET_NULL,
        null=True,
        related_name='data_entries',
        help_text="Technician who entered the data"
    )

    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validated_data_entries',
        help_text="User who validated the entry"
    )

    # ===== ENTRY DETAILS =====

    data_type = models.CharField(
        max_length=20,
        choices=DataType.choices,
        default=DataType.TEXT,
        help_text="Type of data"
    )

    category = models.CharField(
        max_length=20,
        choices=EntryCategory.choices,
        default=EntryCategory.OBSERVATION,
        help_text="Category of entry"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Entry status"
    )

    # ===== DATA DEFINITION =====

    field_name = models.CharField(
        max_length=200,
        help_text="Name/label of the data field"
    )

    field_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Short code for the field"
    )

    description = models.TextField(
        blank=True,
        help_text="Description of what this data represents"
    )

    # ===== DATA VALUES =====

    value_text = models.TextField(
        blank=True,
        help_text="Text value"
    )

    value_numeric = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Numeric value"
    )

    value_boolean = models.BooleanField(
        null=True,
        blank=True,
        help_text="Boolean value"
    )

    value_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date value"
    )

    value_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="DateTime value"
    )

    # ===== MEASUREMENT DETAILS =====

    unit_of_measure = models.CharField(
        max_length=50,
        blank=True,
        help_text="Unit of measurement (e.g., ft, psi, rpm)"
    )

    min_value = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Minimum acceptable value"
    )

    max_value = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Maximum acceptable value"
    )

    target_value = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Target/expected value"
    )

    # ===== LOCATION =====

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="GPS latitude"
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="GPS longitude"
    )

    location_accuracy = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="GPS accuracy in meters"
    )

    # ===== TIMING =====

    entry_date = models.DateField(
        help_text="Date data was collected"
    )

    entry_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time data was collected"
    )

    # ===== VALIDATION =====

    is_validated = models.BooleanField(
        default=False,
        help_text="Entry has been validated"
    )

    validated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When entry was validated"
    )

    validation_notes = models.TextField(
        blank=True,
        help_text="Notes from validation"
    )

    is_out_of_range = models.BooleanField(
        default=False,
        help_text="Value is outside acceptable range"
    )

    out_of_range_reason = models.TextField(
        blank=True,
        help_text="Explanation for out-of-range value"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this entry was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this entry was last updated"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_data_entries',
        help_text="User who created this entry"
    )

    class Meta:
        db_table = "field_data_entries"
        ordering = ['-entry_date', '-entry_time']
        verbose_name = "Field Data Entry"
        verbose_name_plural = "Field Data Entries"
        indexes = [
            models.Index(fields=['entry_number']),
            models.Index(fields=['site_visit', 'entry_date']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['field_name']),
        ]
        permissions = [
            ("can_enter_field_data", "Can enter field data"),
            ("can_validate_field_data", "Can validate field data"),
        ]

    def __str__(self):
        return f"{self.entry_number} - {self.field_name}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate entry number and check ranges"""
        if not self.entry_number:
            self.entry_number = self._generate_entry_number()

        # Check if value is out of range
        self._check_range()

        super().save(*args, **kwargs)

    def _generate_entry_number(self):
        """Generate unique entry number: DATA-YYYY-####"""
        year = timezone.now().year

        last_entry = FieldDataEntry.objects.filter(
            entry_number__startswith=f"DATA-{year}-"
        ).order_by('-entry_number').first()

        if last_entry:
            try:
                last_num = int(last_entry.entry_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"DATA-{year}-{new_num:04d}"

    def _check_range(self):
        """Check if numeric value is within acceptable range"""
        if self.value_numeric is not None:
            if self.min_value is not None and self.value_numeric < self.min_value:
                self.is_out_of_range = True
            elif self.max_value is not None and self.value_numeric > self.max_value:
                self.is_out_of_range = True
            else:
                self.is_out_of_range = False

    @property
    def display_value(self):
        """Get the appropriate display value based on data type"""
        if self.data_type == self.DataType.NUMERIC:
            if self.value_numeric is not None:
                if self.unit_of_measure:
                    return f"{self.value_numeric} {self.unit_of_measure}"
                return str(self.value_numeric)
        elif self.data_type == self.DataType.BOOLEAN:
            if self.value_boolean is not None:
                return "Yes" if self.value_boolean else "No"
        elif self.data_type == self.DataType.DATE:
            if self.value_date:
                return self.value_date.strftime("%Y-%m-%d")
        elif self.data_type == self.DataType.DATETIME:
            if self.value_datetime:
                return self.value_datetime.strftime("%Y-%m-%d %H:%M")
        return self.value_text or ""

    @property
    def variance_from_target(self):
        """Calculate variance from target value"""
        if self.target_value and self.value_numeric:
            return float(self.value_numeric) - float(self.target_value)
        return None

    def validate_entry(self, user, notes=None):
        """Validate the data entry"""
        if self.status != self.Status.SUBMITTED:
            raise ValidationError("Can only validate submitted entries")

        self.status = self.Status.VALIDATED
        self.is_validated = True
        self.validated_by = user
        self.validated_at = timezone.now()
        if notes:
            self.validation_notes = notes
        self.save()

    def reject_entry(self, user, reason):
        """Reject the data entry"""
        if self.status != self.Status.SUBMITTED:
            raise ValidationError("Can only reject submitted entries")

        self.status = self.Status.REJECTED
        self.validated_by = user
        self.validated_at = timezone.now()
        self.validation_notes = f"REJECTED: {reason}"
        self.save()


class FieldPhoto(models.Model):
    """
    Manage photos captured during field operations.

    This model stores metadata about photos taken in the field,
    including location, subject, and categorization. Supports
    linking to various field entities.

    Features:
    - GPS location tagging
    - Multiple category support
    - Linking to field entities
    - Annotation support
    - Thumbnail management

    Integrates with:
    - SiteVisit: Visit during which photo was taken
    - FieldInspection: Inspection documentation
    - FieldIncident: Incident documentation
    - DrillBit: Equipment photos
    - FieldTechnician: Photographer

    ISO 9001 References:
    - Clause 7.5: Documented Information
    - Clause 8.5.2: Identification and Traceability

    Author: Sprint 5 Week 3 Implementation
    Date: December 2024
    """

    class PhotoCategory(models.TextChoices):
        """Category of photo"""
        EQUIPMENT = "EQUIPMENT", "Equipment"
        BIT_CONDITION = "BIT_CONDITION", "Bit Condition"
        DULL_GRADE = "DULL_GRADE", "Dull Grade Documentation"
        DAMAGE = "DAMAGE", "Damage Documentation"
        SITE = "SITE", "Site/Location"
        SAFETY = "SAFETY", "Safety Related"
        INCIDENT = "INCIDENT", "Incident Documentation"
        BEFORE_AFTER = "BEFORE_AFTER", "Before/After Comparison"
        MEASUREMENT = "MEASUREMENT", "Measurement/Reading"
        GENERAL = "GENERAL", "General"
        CUSTOMER_SIGN = "CUSTOMER_SIGN", "Customer Signature"
        OTHER = "OTHER", "Other"

    class PhotoStatus(models.TextChoices):
        """Photo status"""
        PENDING = "PENDING", "Pending Upload"
        UPLOADED = "UPLOADED", "Uploaded"
        PROCESSED = "PROCESSED", "Processed"
        ARCHIVED = "ARCHIVED", "Archived"
        DELETED = "DELETED", "Marked for Deletion"

    # ===== IDENTIFICATION =====

    photo_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique photo identifier (auto-generated: PHOTO-YYYY-####)"
    )

    # ===== RELATIONSHIPS =====

    site_visit = models.ForeignKey(
        'SiteVisit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos',
        help_text="Site visit during which photo was taken"
    )

    field_inspection = models.ForeignKey(
        'FieldInspection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos',
        help_text="Associated inspection"
    )

    field_incident = models.ForeignKey(
        'FieldIncident',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos',
        help_text="Associated incident"
    )

    drill_bit = models.ForeignKey(
        'workorders.DrillBit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='field_photos',
        help_text="Drill bit in photo"
    )

    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos',
        help_text="Location where photo was taken"
    )

    taken_by = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.SET_NULL,
        null=True,
        related_name='photos_taken',
        help_text="Technician who took the photo"
    )

    # ===== PHOTO DETAILS =====

    category = models.CharField(
        max_length=20,
        choices=PhotoCategory.choices,
        default=PhotoCategory.GENERAL,
        help_text="Photo category"
    )

    status = models.CharField(
        max_length=20,
        choices=PhotoStatus.choices,
        default=PhotoStatus.PENDING,
        db_index=True,
        help_text="Photo status"
    )

    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Photo title"
    )

    description = models.TextField(
        blank=True,
        help_text="Photo description"
    )

    # ===== FILE INFORMATION =====

    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to photo file"
    )

    file_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original file name"
    )

    file_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )

    file_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="MIME type"
    )

    thumbnail_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to thumbnail"
    )

    # ===== IMAGE PROPERTIES =====

    width = models.IntegerField(
        null=True,
        blank=True,
        help_text="Image width in pixels"
    )

    height = models.IntegerField(
        null=True,
        blank=True,
        help_text="Image height in pixels"
    )

    orientation = models.CharField(
        max_length=20,
        blank=True,
        help_text="Image orientation"
    )

    # ===== LOCATION =====

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="GPS latitude where photo was taken"
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="GPS longitude where photo was taken"
    )

    location_accuracy = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="GPS accuracy in meters"
    )

    # ===== TIMING =====

    taken_at = models.DateTimeField(
        help_text="When photo was taken"
    )

    uploaded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When photo was uploaded"
    )

    # ===== ANNOTATIONS =====

    has_annotations = models.BooleanField(
        default=False,
        help_text="Photo has annotations"
    )

    annotations = models.TextField(
        blank=True,
        help_text="JSON-encoded annotations"
    )

    # ===== TAGS =====

    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated tags"
    )

    # ===== SEQUENCE =====

    sequence_number = models.IntegerField(
        default=1,
        help_text="Order in sequence (for before/after, etc.)"
    )

    is_primary = models.BooleanField(
        default=False,
        help_text="Primary photo for the entity"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_field_photos',
        help_text="User who created this record"
    )

    class Meta:
        db_table = "field_photos"
        ordering = ['-taken_at']
        verbose_name = "Field Photo"
        verbose_name_plural = "Field Photos"
        indexes = [
            models.Index(fields=['photo_number']),
            models.Index(fields=['site_visit', 'category']),
            models.Index(fields=['drill_bit']),
            models.Index(fields=['taken_at']),
        ]
        permissions = [
            ("can_upload_photos", "Can upload field photos"),
            ("can_delete_photos", "Can delete field photos"),
            ("can_annotate_photos", "Can annotate photos"),
        ]

    def __str__(self):
        return f"{self.photo_number} - {self.title or self.category}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate photo number"""
        if not self.photo_number:
            self.photo_number = self._generate_photo_number()
        super().save(*args, **kwargs)

    def _generate_photo_number(self):
        """Generate unique photo number: PHOTO-YYYY-####"""
        year = timezone.now().year

        last_photo = FieldPhoto.objects.filter(
            photo_number__startswith=f"PHOTO-{year}-"
        ).order_by('-photo_number').first()

        if last_photo:
            try:
                last_num = int(last_photo.photo_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"PHOTO-{year}-{new_num:04d}"

    @property
    def has_location(self):
        """Check if photo has GPS coordinates"""
        return self.latitude is not None and self.longitude is not None

    @property
    def file_size_mb(self):
        """Get file size in MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None

    def mark_uploaded(self):
        """Mark photo as uploaded"""
        self.status = self.PhotoStatus.UPLOADED
        self.uploaded_at = timezone.now()
        self.save()


class FieldDocument(models.Model):
    """
    Manage documents associated with field operations.

    This model tracks documents such as reports, forms, certificates,
    and other paperwork generated or collected in the field.

    Features:
    - Multiple document types
    - Version control
    - Digital signatures
    - Approval workflow
    - Template support

    Integrates with:
    - SiteVisit: Visit-related documents
    - FieldServiceRequest: Request documents
    - ServiceReport: Report attachments
    - FieldTechnician: Document creator

    ISO 9001 References:
    - Clause 7.5: Documented Information
    - Clause 7.5.2: Creating and Updating

    Author: Sprint 5 Week 3 Implementation
    Date: December 2024
    """

    class DocumentType(models.TextChoices):
        """Type of document"""
        REPORT = "REPORT", "Report"
        FORM = "FORM", "Form"
        CERTIFICATE = "CERTIFICATE", "Certificate"
        PERMIT = "PERMIT", "Permit"
        PROCEDURE = "PROCEDURE", "Procedure"
        CHECKLIST = "CHECKLIST", "Checklist"
        DRAWING = "DRAWING", "Drawing/Diagram"
        SPECIFICATION = "SPECIFICATION", "Specification"
        INVOICE = "INVOICE", "Invoice"
        DELIVERY_NOTE = "DELIVERY_NOTE", "Delivery Note"
        SIGN_OFF = "SIGN_OFF", "Sign-Off Document"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        """Document status"""
        DRAFT = "DRAFT", "Draft"
        PENDING_REVIEW = "PENDING_REVIEW", "Pending Review"
        REVIEWED = "REVIEWED", "Reviewed"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SUPERSEDED = "SUPERSEDED", "Superseded"
        ARCHIVED = "ARCHIVED", "Archived"

    # ===== IDENTIFICATION =====

    document_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique document identifier (auto-generated: DOC-YYYY-####)"
    )

    # ===== RELATIONSHIPS =====

    site_visit = models.ForeignKey(
        'SiteVisit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text="Associated site visit"
    )

    service_request = models.ForeignKey(
        'FieldServiceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text="Associated service request"
    )

    service_report = models.ForeignKey(
        'ServiceReport',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attachments',
        help_text="Associated service report"
    )

    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text="Associated service site"
    )

    created_by_technician = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_documents',
        help_text="Technician who created the document"
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_field_documents',
        help_text="User who approved the document"
    )

    # ===== DOCUMENT DETAILS =====

    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.REPORT,
        help_text="Type of document"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Document status"
    )

    title = models.CharField(
        max_length=300,
        help_text="Document title"
    )

    description = models.TextField(
        blank=True,
        help_text="Document description"
    )

    # ===== FILE INFORMATION =====

    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to document file"
    )

    file_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original file name"
    )

    file_size = models.IntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )

    file_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="MIME type"
    )

    # ===== VERSION CONTROL =====

    version = models.CharField(
        max_length=20,
        default="1.0",
        help_text="Document version"
    )

    revision_number = models.IntegerField(
        default=1,
        help_text="Revision number"
    )

    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newer_versions',
        help_text="Previous version of this document"
    )

    # ===== DATES =====

    document_date = models.DateField(
        help_text="Date on the document"
    )

    effective_date = models.DateField(
        null=True,
        blank=True,
        help_text="When document becomes effective"
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="When document expires"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When document was approved"
    )

    # ===== SIGNATURES =====

    requires_signature = models.BooleanField(
        default=False,
        help_text="Document requires signature"
    )

    is_signed = models.BooleanField(
        default=False,
        help_text="Document has been signed"
    )

    signed_by = models.CharField(
        max_length=200,
        blank=True,
        help_text="Who signed the document"
    )

    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When document was signed"
    )

    customer_signed = models.BooleanField(
        default=False,
        help_text="Customer has signed"
    )

    customer_signature_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Customer signatory name"
    )

    customer_signed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When customer signed"
    )

    # ===== CONFIDENTIALITY =====

    is_confidential = models.BooleanField(
        default=False,
        help_text="Document is confidential"
    )

    access_level = models.CharField(
        max_length=50,
        blank=True,
        help_text="Required access level"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )

    review_notes = models.TextField(
        blank=True,
        help_text="Notes from review"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_field_documents',
        help_text="User who created this record"
    )

    class Meta:
        db_table = "field_documents"
        ordering = ['-document_date', '-created_at']
        verbose_name = "Field Document"
        verbose_name_plural = "Field Documents"
        indexes = [
            models.Index(fields=['document_number']),
            models.Index(fields=['document_type', 'status']),
            models.Index(fields=['site_visit']),
            models.Index(fields=['document_date']),
        ]
        permissions = [
            ("can_create_documents", "Can create field documents"),
            ("can_approve_documents", "Can approve field documents"),
            ("can_view_confidential", "Can view confidential documents"),
        ]

    def __str__(self):
        return f"{self.document_number} - {self.title}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate document number"""
        if not self.document_number:
            self.document_number = self._generate_document_number()
        super().save(*args, **kwargs)

    def _generate_document_number(self):
        """Generate unique document number: DOC-YYYY-####"""
        year = timezone.now().year

        last_doc = FieldDocument.objects.filter(
            document_number__startswith=f"DOC-{year}-"
        ).order_by('-document_number').first()

        if last_doc:
            try:
                last_num = int(last_doc.document_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"DOC-{year}-{new_num:04d}"

    @property
    def is_expired(self):
        """Check if document has expired"""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False

    @property
    def file_size_mb(self):
        """Get file size in MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None

    def approve(self, user, notes=None):
        """Approve the document"""
        if self.status not in [self.Status.PENDING_REVIEW, self.Status.REVIEWED]:
            raise ValidationError("Can only approve documents pending review or reviewed")

        self.status = self.Status.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        if notes:
            self.review_notes = notes
        self.save()

    def create_new_version(self):
        """Create a new version of this document"""
        new_doc = FieldDocument.objects.create(
            document_type=self.document_type,
            title=self.title,
            description=self.description,
            site_visit=self.site_visit,
            service_request=self.service_request,
            service_site=self.service_site,
            document_date=timezone.now().date(),
            version=f"{float(self.version) + 0.1:.1f}",
            revision_number=self.revision_number + 1,
            previous_version=self,
            created_by=self.created_by,
        )

        # Mark this version as superseded
        self.status = self.Status.SUPERSEDED
        self.save()

        return new_doc


class GPSLocation(models.Model):
    """
    Track GPS locations and movements during field operations.

    This model records GPS coordinates for tracking personnel,
    equipment, and vehicles in the field. Supports geofencing
    and route tracking.

    Features:
    - Real-time location tracking
    - Historical location data
    - Speed and heading tracking
    - Geofencing support
    - Battery and signal quality

    Integrates with:
    - FieldTechnician: Technician being tracked
    - SiteVisit: Location during visits
    - FieldDrillStringRun: Equipment location

    ISO 9001 References:
    - Clause 8.5.2: Identification and Traceability

    Author: Sprint 5 Week 3 Implementation
    Date: December 2024
    """

    class LocationType(models.TextChoices):
        """Type of location record"""
        AUTOMATIC = "AUTOMATIC", "Automatic Update"
        MANUAL = "MANUAL", "Manual Check-in"
        CHECK_IN = "CHECK_IN", "Site Check-in"
        CHECK_OUT = "CHECK_OUT", "Site Check-out"
        WAYPOINT = "WAYPOINT", "Waypoint"
        ALERT = "ALERT", "Alert Location"

    class SourceDevice(models.TextChoices):
        """Source of GPS data"""
        PHONE = "PHONE", "Mobile Phone"
        TABLET = "TABLET", "Tablet"
        GPS_TRACKER = "GPS_TRACKER", "GPS Tracker Device"
        VEHICLE = "VEHICLE", "Vehicle GPS"
        MANUAL = "MANUAL", "Manual Entry"

    # ===== RELATIONSHIPS =====

    field_technician = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gps_locations',
        help_text="Technician being tracked"
    )

    site_visit = models.ForeignKey(
        'SiteVisit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gps_locations',
        help_text="Associated site visit"
    )

    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gps_locations',
        help_text="Nearby service site"
    )

    # ===== LOCATION DATA =====

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        db_index=True,
        help_text="GPS latitude"
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        db_index=True,
        help_text="GPS longitude"
    )

    altitude = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Altitude in meters"
    )

    accuracy = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Horizontal accuracy in meters"
    )

    altitude_accuracy = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Vertical accuracy in meters"
    )

    # ===== MOVEMENT DATA =====

    speed = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Speed in km/h"
    )

    heading = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Heading in degrees (0-360)"
    )

    # ===== TIMING =====

    recorded_at = models.DateTimeField(
        db_index=True,
        help_text="When location was recorded"
    )

    device_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp from device"
    )

    # ===== RECORD TYPE =====

    location_type = models.CharField(
        max_length=20,
        choices=LocationType.choices,
        default=LocationType.AUTOMATIC,
        help_text="Type of location record"
    )

    source_device = models.CharField(
        max_length=20,
        choices=SourceDevice.choices,
        default=SourceDevice.PHONE,
        help_text="Source of GPS data"
    )

    device_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Device identifier"
    )

    # ===== DEVICE STATUS =====

    battery_level = models.IntegerField(
        null=True,
        blank=True,
        help_text="Battery level percentage"
    )

    signal_strength = models.IntegerField(
        null=True,
        blank=True,
        help_text="Signal strength (dBm)"
    )

    satellites_used = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of satellites used"
    )

    # ===== GEOFENCING =====

    is_inside_geofence = models.BooleanField(
        null=True,
        blank=True,
        help_text="Location is inside designated geofence"
    )

    geofence_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of geofence if applicable"
    )

    distance_from_site = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Distance from service site in meters"
    )

    # ===== ADDRESS =====

    address = models.CharField(
        max_length=500,
        blank=True,
        help_text="Reverse geocoded address"
    )

    # ===== NOTES =====

    notes = models.TextField(
        blank=True,
        help_text="Notes about this location"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    class Meta:
        db_table = "gps_locations"
        ordering = ['-recorded_at']
        verbose_name = "GPS Location"
        verbose_name_plural = "GPS Locations"
        indexes = [
            models.Index(fields=['field_technician', 'recorded_at']),
            models.Index(fields=['site_visit']),
            models.Index(fields=['recorded_at']),
            models.Index(fields=['latitude', 'longitude']),
        ]
        permissions = [
            ("can_view_gps_tracking", "Can view GPS tracking data"),
            ("can_manage_geofencing", "Can manage geofencing"),
        ]

    def __str__(self):
        return f"{self.field_technician} @ {self.latitude}, {self.longitude} - {self.recorded_at}"

    @property
    def coordinates(self):
        """Get coordinates as tuple"""
        return (float(self.latitude), float(self.longitude))

    @property
    def has_movement_data(self):
        """Check if record has movement data"""
        return self.speed is not None or self.heading is not None

    def distance_to(self, other_lat, other_lon):
        """Calculate distance to another point using Haversine formula"""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371000  # Earth's radius in meters

        lat1, lon1 = radians(float(self.latitude)), radians(float(self.longitude))
        lat2, lon2 = radians(float(other_lat)), radians(float(other_lon))

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c


class FieldWorkOrder(models.Model):
    """
    Field work orders for on-site service activities.

    This model manages work orders created and executed in the field,
    tracking tasks, materials, labor, and completion status.

    Features:
    - Task-based work breakdown
    - Material tracking
    - Labor time recording
    - Approval workflow
    - Cost tracking

    Integrates with:
    - FieldServiceRequest: Parent request
    - SiteVisit: Execution visit
    - FieldTechnician: Assigned workers
    - ServiceSite: Work location

    ISO 9001 References:
    - Clause 8.5.1: Control of Production and Service Provision
    - Clause 8.5.6: Control of Changes

    Author: Sprint 5 Week 3 Implementation
    Date: December 2024
    """

    class Status(models.TextChoices):
        """Work order status"""
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        ON_HOLD = "ON_HOLD", "On Hold"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class Priority(models.TextChoices):
        """Priority levels"""
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"
        EMERGENCY = "EMERGENCY", "Emergency"

    class WorkType(models.TextChoices):
        """Type of work"""
        INSPECTION = "INSPECTION", "Inspection"
        REPAIR = "REPAIR", "Repair"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        INSTALLATION = "INSTALLATION", "Installation"
        REPLACEMENT = "REPLACEMENT", "Replacement"
        CALIBRATION = "CALIBRATION", "Calibration"
        TRAINING = "TRAINING", "Training"
        CONSULTATION = "CONSULTATION", "Consultation"
        OTHER = "OTHER", "Other"

    # ===== IDENTIFICATION =====

    work_order_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique work order identifier (auto-generated: FWO-YYYY-####)"
    )

    # ===== RELATIONSHIPS =====

    service_request = models.ForeignKey(
        'FieldServiceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders',
        help_text="Parent service request"
    )

    site_visit = models.ForeignKey(
        'SiteVisit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders',
        help_text="Associated site visit"
    )

    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.PROTECT,
        related_name='work_orders',
        help_text="Work location"
    )

    customer = models.ForeignKey(
        'Customer',
        on_delete=models.PROTECT,
        related_name='field_work_orders',
        help_text="Customer"
    )

    assigned_technician = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_work_orders',
        help_text="Primary assigned technician"
    )

    additional_technicians = models.ManyToManyField(
        'FieldTechnician',
        blank=True,
        related_name='supporting_work_orders',
        help_text="Additional technicians"
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_field_work_orders',
        help_text="User who approved the work order"
    )

    # ===== WORK ORDER DETAILS =====

    work_type = models.CharField(
        max_length=20,
        choices=WorkType.choices,
        default=WorkType.MAINTENANCE,
        help_text="Type of work"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Work order status"
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
        help_text="Priority level"
    )

    title = models.CharField(
        max_length=300,
        help_text="Work order title"
    )

    description = models.TextField(
        help_text="Detailed description of work"
    )

    scope_of_work = models.TextField(
        blank=True,
        help_text="Scope of work to be performed"
    )

    # ===== SCHEDULING =====

    requested_date = models.DateField(
        null=True,
        blank=True,
        help_text="Requested completion date"
    )

    scheduled_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled start time"
    )

    scheduled_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled end time"
    )

    actual_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual start time"
    )

    actual_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual end time"
    )

    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated hours"
    )

    actual_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual hours worked"
    )

    # ===== COST TRACKING =====

    estimated_labor_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated labor cost"
    )

    estimated_material_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated material cost"
    )

    actual_labor_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual labor cost"
    )

    actual_material_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual material cost"
    )

    # ===== COMPLETION =====

    work_performed = models.TextField(
        blank=True,
        help_text="Description of work performed"
    )

    completion_notes = models.TextField(
        blank=True,
        help_text="Completion notes"
    )

    issues_found = models.TextField(
        blank=True,
        help_text="Issues found during work"
    )

    recommendations = models.TextField(
        blank=True,
        help_text="Recommendations for follow-up"
    )

    follow_up_required = models.BooleanField(
        default=False,
        help_text="Follow-up work is required"
    )

    # ===== CUSTOMER SIGN-OFF =====

    customer_signoff = models.BooleanField(
        default=False,
        help_text="Customer has signed off"
    )

    customer_signoff_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Customer signatory name"
    )

    customer_signoff_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When customer signed off"
    )

    customer_feedback = models.TextField(
        blank=True,
        help_text="Customer feedback"
    )

    customer_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Customer satisfaction rating (1-5)"
    )

    # ===== AUDIT =====

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When work order was approved"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_field_work_orders',
        help_text="User who created this record"
    )

    class Meta:
        db_table = "field_work_orders"
        ordering = ['-created_at']
        verbose_name = "Field Work Order"
        verbose_name_plural = "Field Work Orders"
        indexes = [
            models.Index(fields=['work_order_number']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['assigned_technician', 'status']),
            models.Index(fields=['scheduled_start']),
        ]
        permissions = [
            ("can_create_field_work_orders", "Can create field work orders"),
            ("can_approve_field_work_orders", "Can approve field work orders"),
            ("can_assign_technicians", "Can assign technicians to work orders"),
        ]

    def __str__(self):
        return f"{self.work_order_number} - {self.title}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate work order number"""
        if not self.work_order_number:
            self.work_order_number = self._generate_work_order_number()
        super().save(*args, **kwargs)

    def _generate_work_order_number(self):
        """Generate unique work order number: FWO-YYYY-####"""
        year = timezone.now().year

        last_wo = FieldWorkOrder.objects.filter(
            work_order_number__startswith=f"FWO-{year}-"
        ).order_by('-work_order_number').first()

        if last_wo:
            try:
                last_num = int(last_wo.work_order_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"FWO-{year}-{new_num:04d}"

    # ===== PROPERTIES =====

    @property
    def total_estimated_cost(self):
        """Calculate total estimated cost"""
        labor = self.estimated_labor_cost or Decimal('0')
        material = self.estimated_material_cost or Decimal('0')
        return labor + material

    @property
    def total_actual_cost(self):
        """Calculate total actual cost"""
        labor = self.actual_labor_cost or Decimal('0')
        material = self.actual_material_cost or Decimal('0')
        return labor + material

    @property
    def cost_variance(self):
        """Calculate cost variance"""
        if self.total_estimated_cost > 0:
            return self.total_actual_cost - self.total_estimated_cost
        return None

    @property
    def is_overdue(self):
        """Check if work order is overdue"""
        if self.requested_date and self.status not in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return timezone.now().date() > self.requested_date
        return False

    @property
    def duration_hours(self):
        """Calculate actual duration in hours"""
        if self.actual_start and self.actual_end:
            delta = self.actual_end - self.actual_start
            return round(delta.total_seconds() / 3600, 2)
        return None

    # ===== WORKFLOW METHODS =====

    def approve(self, user):
        """Approve the work order"""
        if self.status != self.Status.PENDING:
            raise ValidationError("Can only approve pending work orders")

        self.status = self.Status.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()

    def start_work(self):
        """Start the work order"""
        if self.status not in [self.Status.APPROVED, self.Status.ASSIGNED]:
            raise ValidationError("Can only start approved or assigned work orders")

        self.status = self.Status.IN_PROGRESS
        self.actual_start = timezone.now()
        self.save()

    def complete_work(self, work_performed=None, notes=None):
        """Complete the work order"""
        if self.status != self.Status.IN_PROGRESS:
            raise ValidationError("Can only complete in-progress work orders")

        self.status = self.Status.COMPLETED
        self.actual_end = timezone.now()

        if work_performed:
            self.work_performed = work_performed
        if notes:
            self.completion_notes = notes

        self.save()


class FieldAssetAssignment(models.Model):
    """
    Track assignments of assets to field operations.

    This model manages the assignment and tracking of equipment,
    tools, and other assets to field operations, including
    check-out, check-in, and condition tracking.

    Features:
    - Asset checkout/checkin tracking
    - Condition assessment
    - Usage logging
    - Maintenance tracking
    - Cost allocation

    Integrates with:
    - DrillBit: Assigned drill bits
    - FieldWorkOrder: Work order assignments
    - SiteVisit: Visit assignments
    - FieldTechnician: Asset holder

    ISO 9001 References:
    - Clause 7.1.3: Infrastructure
    - Clause 8.5.2: Identification and Traceability

    Author: Sprint 5 Week 3 Implementation
    Date: December 2024
    """

    class AssetType(models.TextChoices):
        """Type of asset"""
        DRILL_BIT = "DRILL_BIT", "Drill Bit"
        TOOL = "TOOL", "Tool"
        EQUIPMENT = "EQUIPMENT", "Equipment"
        VEHICLE = "VEHICLE", "Vehicle"
        INSTRUMENT = "INSTRUMENT", "Instrument"
        SAFETY_EQUIPMENT = "SAFETY_EQUIPMENT", "Safety Equipment"
        CONSUMABLE = "CONSUMABLE", "Consumable"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        """Assignment status"""
        RESERVED = "RESERVED", "Reserved"
        CHECKED_OUT = "CHECKED_OUT", "Checked Out"
        IN_USE = "IN_USE", "In Use"
        RETURNED = "RETURNED", "Returned"
        LOST = "LOST", "Lost"
        DAMAGED = "DAMAGED", "Damaged"

    class ConditionOnReturn(models.TextChoices):
        """Condition when returned"""
        EXCELLENT = "EXCELLENT", "Excellent"
        GOOD = "GOOD", "Good"
        FAIR = "FAIR", "Fair"
        POOR = "POOR", "Poor"
        DAMAGED = "DAMAGED", "Damaged"
        NOT_RETURNED = "NOT_RETURNED", "Not Returned"

    # ===== IDENTIFICATION =====

    assignment_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique assignment identifier (auto-generated: ASSIGN-YYYY-####)"
    )

    # ===== RELATIONSHIPS =====

    drill_bit = models.ForeignKey(
        'workorders.DrillBit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='field_assignments',
        help_text="Assigned drill bit"
    )

    work_order = models.ForeignKey(
        'FieldWorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_assignments',
        help_text="Associated work order"
    )

    site_visit = models.ForeignKey(
        'SiteVisit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_assignments',
        help_text="Associated site visit"
    )

    service_site = models.ForeignKey(
        'ServiceSite',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_assignments',
        help_text="Destination site"
    )

    assigned_to = models.ForeignKey(
        'FieldTechnician',
        on_delete=models.SET_NULL,
        null=True,
        related_name='asset_assignments',
        help_text="Technician holding the asset"
    )

    checked_out_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='checked_out_assets',
        help_text="User who processed checkout"
    )

    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_in_assets',
        help_text="User who processed checkin"
    )

    # ===== ASSET DETAILS =====

    asset_type = models.CharField(
        max_length=20,
        choices=AssetType.choices,
        default=AssetType.EQUIPMENT,
        help_text="Type of asset"
    )

    asset_name = models.CharField(
        max_length=200,
        help_text="Name/description of asset"
    )

    asset_code = models.CharField(
        max_length=100,
        blank=True,
        help_text="Asset code/serial number"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RESERVED,
        db_index=True,
        help_text="Assignment status"
    )

    quantity = models.IntegerField(
        default=1,
        help_text="Quantity assigned"
    )

    # ===== CHECKOUT =====

    checkout_date = models.DateField(
        help_text="Date asset was checked out"
    )

    checkout_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time asset was checked out"
    )

    expected_return_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected return date"
    )

    checkout_condition = models.TextField(
        blank=True,
        help_text="Condition at checkout"
    )

    checkout_notes = models.TextField(
        blank=True,
        help_text="Notes at checkout"
    )

    # ===== RETURN =====

    return_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date asset was returned"
    )

    return_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time asset was returned"
    )

    condition_on_return = models.CharField(
        max_length=20,
        choices=ConditionOnReturn.choices,
        blank=True,
        help_text="Condition when returned"
    )

    return_notes = models.TextField(
        blank=True,
        help_text="Notes at return"
    )

    # ===== USAGE =====

    hours_used = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hours used"
    )

    usage_notes = models.TextField(
        blank=True,
        help_text="Usage notes"
    )

    # ===== COST =====

    daily_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Daily rental/usage rate"
    )

    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total cost for assignment"
    )

    billable = models.BooleanField(
        default=True,
        help_text="Assignment is billable"
    )

    # ===== MAINTENANCE =====

    requires_maintenance = models.BooleanField(
        default=False,
        help_text="Asset requires maintenance after use"
    )

    maintenance_notes = models.TextField(
        blank=True,
        help_text="Maintenance requirements"
    )

    # ===== AUDIT =====

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_asset_assignments',
        help_text="User who created this record"
    )

    class Meta:
        db_table = "field_asset_assignments"
        ordering = ['-checkout_date', '-created_at']
        verbose_name = "Field Asset Assignment"
        verbose_name_plural = "Field Asset Assignments"
        indexes = [
            models.Index(fields=['assignment_number']),
            models.Index(fields=['drill_bit']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['checkout_date']),
            models.Index(fields=['status']),
        ]
        permissions = [
            ("can_checkout_assets", "Can check out assets"),
            ("can_checkin_assets", "Can check in assets"),
            ("can_manage_assignments", "Can manage asset assignments"),
        ]

    def __str__(self):
        return f"{self.assignment_number} - {self.asset_name}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate assignment number"""
        if not self.assignment_number:
            self.assignment_number = self._generate_assignment_number()

        # Calculate total cost if we have dates and rate
        self._calculate_cost()

        super().save(*args, **kwargs)

    def _generate_assignment_number(self):
        """Generate unique assignment number: ASSIGN-YYYY-####"""
        year = timezone.now().year

        last_assign = FieldAssetAssignment.objects.filter(
            assignment_number__startswith=f"ASSIGN-{year}-"
        ).order_by('-assignment_number').first()

        if last_assign:
            try:
                last_num = int(last_assign.assignment_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"ASSIGN-{year}-{new_num:04d}"

    def _calculate_cost(self):
        """Calculate total cost based on duration and rate"""
        if self.daily_rate and self.checkout_date:
            end_date = self.return_date or timezone.now().date()
            days = (end_date - self.checkout_date).days + 1
            self.total_cost = self.daily_rate * days * self.quantity

    @property
    def is_overdue(self):
        """Check if return is overdue"""
        if self.expected_return_date and self.status in [self.Status.CHECKED_OUT, self.Status.IN_USE]:
            return timezone.now().date() > self.expected_return_date
        return False

    @property
    def days_out(self):
        """Calculate days asset has been out"""
        if self.checkout_date:
            end_date = self.return_date or timezone.now().date()
            return (end_date - self.checkout_date).days
        return 0

    def checkout(self, user, notes=None):
        """Process checkout"""
        if self.status != self.Status.RESERVED:
            raise ValidationError("Can only checkout reserved assets")

        self.status = self.Status.CHECKED_OUT
        self.checked_out_by = user
        self.checkout_time = timezone.now().time()
        if notes:
            self.checkout_notes = notes
        self.save()

    def checkin(self, user, condition, notes=None):
        """Process checkin"""
        if self.status not in [self.Status.CHECKED_OUT, self.Status.IN_USE]:
            raise ValidationError("Asset is not currently checked out")

        self.status = self.Status.RETURNED
        self.checked_in_by = user
        self.return_date = timezone.now().date()
        self.return_time = timezone.now().time()
        self.condition_on_return = condition

        if notes:
            self.return_notes = notes

        # Flag for maintenance if condition is poor or damaged
        if condition in [self.ConditionOnReturn.POOR, self.ConditionOnReturn.DAMAGED]:
            self.requires_maintenance = True

        self.save()
