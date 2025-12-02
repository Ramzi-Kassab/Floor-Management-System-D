"""
ARDT FMS - Maintenance Models
Version: 5.4

Tables:
- equipment_categories (P1)
- equipment (P1)
- maintenance_requests (P1)
- maintenance_work_orders (P1)
- maintenance_parts_used (P1)
"""

from django.db import models
from django.conf import settings


class EquipmentCategory(models.Model):
    """
    🟢 P1: Categories for equipment.
    """
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'equipment_categories'
        ordering = ['code']
        verbose_name = 'Equipment Category'
        verbose_name_plural = 'Equipment Categories'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Equipment(models.Model):
    """
    🟢 P1: Equipment master.
    """
    
    class Status(models.TextChoices):
        OPERATIONAL = 'OPERATIONAL', 'Operational'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
        BREAKDOWN = 'BREAKDOWN', 'Breakdown'
        DECOMMISSIONED = 'DECOMMISSIONED', 'Decommissioned'
    
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        EquipmentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipment'
    )
    
    # Details
    manufacturer = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    year_of_manufacture = models.IntegerField(null=True, blank=True)
    
    # Location
    department = models.ForeignKey(
        'organization.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    location = models.CharField(max_length=200, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPERATIONAL
    )
    
    # Maintenance schedule
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    maintenance_interval_days = models.IntegerField(null=True, blank=True)
    
    # Calibration (for measuring equipment)
    requires_calibration = models.BooleanField(default=False)
    last_calibration = models.DateField(null=True, blank=True)
    next_calibration = models.DateField(null=True, blank=True)
    
    # Documents
    manual_file = models.FileField(upload_to='equipment/manuals/', null=True, blank=True)
    image = models.ImageField(upload_to='equipment/images/', null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'equipment'
        ordering = ['code']
        verbose_name = 'Equipment'
        verbose_name_plural = 'Equipment'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class MaintenanceRequest(models.Model):
    """
    🟢 P1: Maintenance requests.
    """
    
    class RequestType(models.TextChoices):
        BREAKDOWN = 'BREAKDOWN', 'Breakdown'
        PREVENTIVE = 'PREVENTIVE', 'Preventive'
        CORRECTIVE = 'CORRECTIVE', 'Corrective'
        CALIBRATION = 'CALIBRATION', 'Calibration'
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
    
    request_number = models.CharField(max_length=30, unique=True)
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='maintenance_requests'
    )
    
    request_type = models.CharField(max_length=20, choices=RequestType.choices)
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Requester
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='maintenance_requests'
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    
    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_maintenance_requests'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'maintenance_requests'
        ordering = ['-requested_at']
        verbose_name = 'Maintenance Request'
        verbose_name_plural = 'Maintenance Requests'
    
    def __str__(self):
        return f"{self.request_number} - {self.equipment.code}"


class MaintenanceWorkOrder(models.Model):
    """
    🟢 P1: Maintenance Work Orders (MWO).
    """
    
    class Status(models.TextChoices):
        PLANNED = 'PLANNED', 'Planned'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        ON_HOLD = 'ON_HOLD', 'On Hold'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    mwo_number = models.CharField(max_length=30, unique=True)
    
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='work_orders'
    )
    request = models.ForeignKey(
        MaintenanceRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders'
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Schedule
    planned_start = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_mwos'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED
    )
    
    # Results
    work_performed = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Cost
    labor_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    parts_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_mwos'
    )
    
    class Meta:
        db_table = 'maintenance_work_orders'
        ordering = ['-created_at']
        verbose_name = 'Maintenance Work Order'
        verbose_name_plural = 'Maintenance Work Orders'
    
    def __str__(self):
        return f"{self.mwo_number}"


class MaintenancePartsUsed(models.Model):
    """
    🟢 P1: Parts used in maintenance.
    """
    
    mwo = models.ForeignKey(
        MaintenanceWorkOrder,
        on_delete=models.CASCADE,
        related_name='parts_used'
    )
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='maintenance_usage'
    )
    
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'maintenance_parts_used'
        verbose_name = 'Maintenance Part Used'
        verbose_name_plural = 'Maintenance Parts Used'

    def __str__(self):
        return f"{self.mwo.mwo_number} - {self.inventory_item.name}"
