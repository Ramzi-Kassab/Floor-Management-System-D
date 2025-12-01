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
"""

from django.db import models
from django.conf import settings


class Customer(models.Model):
    """
    🟢 P1: Customer master data.
    """
    
    class CustomerType(models.TextChoices):
        OPERATOR = 'OPERATOR', 'Oil Operator'
        CONTRACTOR = 'CONTRACTOR', 'Drilling Contractor'
        DISTRIBUTOR = 'DISTRIBUTOR', 'Distributor'
        OTHER = 'OTHER', 'Other'
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    customer_type = models.CharField(
        max_length=20,
        choices=CustomerType.choices,
        default=CustomerType.OPERATOR
    )
    
    # Contact info
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Saudi Arabia')
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Business info
    tax_id = models.CharField(max_length=50, blank=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    payment_terms = models.CharField(max_length=50, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_aramco = models.BooleanField(default=False, help_text='ARAMCO or ARAMCO contractor')
    
    # Account manager
    account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_customers'
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_customers'
    )
    
    class Meta:
        db_table = 'customers'
        ordering = ['name']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class CustomerContact(models.Model):
    """
    🟢 P1: Customer contact persons.
    """
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
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
        db_table = 'customer_contacts'
        ordering = ['customer', '-is_primary', 'name']
        verbose_name = 'Customer Contact'
        verbose_name_plural = 'Customer Contacts'
    
    def __str__(self):
        return f"{self.customer.code} - {self.name}"


class CustomerDocumentRequirement(models.Model):
    """
    🟢 P1: Document requirements specific to each customer.
    """
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='document_requirements'
    )
    document_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=True)
    template_file = models.FileField(upload_to='doc_templates/', null=True, blank=True)
    
    class Meta:
        db_table = 'customer_document_requirements'
        verbose_name = 'Customer Document Requirement'
        verbose_name_plural = 'Customer Document Requirements'


class Rig(models.Model):
    """
    🟢 P1: Drilling rigs (ARAMCO and contractor rigs).
    """
    
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rigs'
    )
    contractor = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contracted_rigs'
    )
    rig_type = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rigs'
        ordering = ['code']
        verbose_name = 'Rig'
        verbose_name_plural = 'Rigs'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Well(models.Model):
    """
    🟢 P1: Wells being drilled.
    """
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wells'
    )
    rig = models.ForeignKey(
        Rig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wells'
    )
    field_name = models.CharField(max_length=100, blank=True)
    spud_date = models.DateField(null=True, blank=True)
    target_depth = models.IntegerField(null=True, blank=True, help_text='Feet')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wells'
        ordering = ['code']
        verbose_name = 'Well'
        verbose_name_plural = 'Wells'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Warehouse(models.Model):
    """
    🟢 P1: Warehouses/storage locations (ARDT, ARAMCO, customer).
    """
    
    class WarehouseType(models.TextChoices):
        ARDT = 'ARDT', 'ARDT Factory'
        ARAMCO = 'ARAMCO', 'ARAMCO Warehouse'
        CUSTOMER = 'CUSTOMER', 'Customer Location'
        RIG = 'RIG', 'Rig Site'
    
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    warehouse_type = models.CharField(
        max_length=20,
        choices=WarehouseType.choices,
        default=WarehouseType.ARDT
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouses'
    )
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'warehouses'
        ordering = ['code']
        verbose_name = 'Warehouse'
        verbose_name_plural = 'Warehouses'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class SalesOrder(models.Model):
    """
    🟢 P1: Sales orders for drill bits.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        READY = 'READY', 'Ready for Dispatch'
        DISPATCHED = 'DISPATCHED', 'Dispatched'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    so_number = models.CharField(max_length=30, unique=True)
    
    # Customer
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='sales_orders'
    )
    customer_po = models.CharField(max_length=50, blank=True, help_text='Customer PO number')
    
    # DRSS link (if from ARAMCO)
    drss_request = models.ForeignKey(
        'drss.DRSSRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders'
    )
    
    # Destination
    rig = models.ForeignKey(
        Rig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders'
    )
    well = models.ForeignKey(
        Well,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders'
    )
    delivery_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_orders'
    )
    
    # Dates
    order_date = models.DateField()
    required_date = models.DateField(null=True, blank=True)
    promised_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    # Financials
    currency = models.CharField(max_length=3, default='SAR')
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Notes
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Assignments
    sales_rep = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders'
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sales_orders'
    )
    
    class Meta:
        db_table = 'sales_orders'
        ordering = ['-order_date']
        verbose_name = 'Sales Order'
        verbose_name_plural = 'Sales Orders'
    
    def __str__(self):
        return f"{self.so_number}"


class SalesOrderLine(models.Model):
    """
    🟢 P1: Line items in a sales order.
    """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PRODUCTION = 'IN_PRODUCTION', 'In Production'
        READY = 'READY', 'Ready'
        DISPATCHED = 'DISPATCHED', 'Dispatched'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.IntegerField()
    
    # DRSS line link (if from ARAMCO)
    drss_request_line = models.ForeignKey(
        'drss.DRSSRequestLine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_order_lines'
    )
    
    # Product
    design = models.ForeignKey(
        'technology.Design',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_order_lines'
    )
    description = models.CharField(max_length=500)
    quantity = models.IntegerField(default=1)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Link to work order
    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_order_lines'
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sales_order_lines'
        ordering = ['sales_order', 'line_number']
        unique_together = ['sales_order', 'line_number']
        verbose_name = 'Sales Order Line'
        verbose_name_plural = 'Sales Order Lines'
    
    def __str__(self):
        return f"{self.sales_order.so_number} - Line {self.line_number}"
