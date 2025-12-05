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
