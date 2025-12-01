"""
ARDT FMS - Dispatch Models
Version: 5.4

🟠 P3 - Full Operations

Tables:
- vehicles (P3)
- dispatches (P3)
- dispatch_items (P3)
- inventory_reservations (P3)
"""

from django.db import models
from django.conf import settings


class Vehicle(models.Model):
    """🟠 P3: Fleet vehicles."""
    
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        IN_USE = 'IN_USE', 'In Use'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
        OUT_OF_SERVICE = 'OUT_OF_SERVICE', 'Out of Service'
    
    code = models.CharField(max_length=20, unique=True)
    plate_number = models.CharField(max_length=20)
    make = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=50, blank=True)
    year = models.IntegerField(null=True, blank=True)
    capacity = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehicles'
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'
    
    def __str__(self):
        return f"{self.code} - {self.plate_number}"


class Dispatch(models.Model):
    """🟠 P3: Dispatch records."""
    
    class Status(models.TextChoices):
        PLANNED = 'PLANNED', 'Planned'
        LOADING = 'LOADING', 'Loading'
        IN_TRANSIT = 'IN_TRANSIT', 'In Transit'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    dispatch_number = models.CharField(max_length=30, unique=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    
    # Destination
    customer = models.ForeignKey('sales.Customer', on_delete=models.PROTECT)
    destination = models.ForeignKey('sales.Warehouse', on_delete=models.SET_NULL, null=True, blank=True)
    rig = models.ForeignKey('sales.Rig', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Dates
    planned_date = models.DateField()
    actual_departure = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dispatches'
        verbose_name = 'Dispatch'
        verbose_name_plural = 'Dispatches'


class DispatchItem(models.Model):
    """🟠 P3: Items in a dispatch."""
    
    dispatch = models.ForeignKey(Dispatch, on_delete=models.CASCADE, related_name='items')
    sales_order_line = models.ForeignKey('sales.SalesOrderLine', on_delete=models.PROTECT)
    drill_bit = models.ForeignKey('workorders.DrillBit', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'dispatch_items'


class InventoryReservation(models.Model):
    """🟠 P3: Inventory reservations for work orders."""
    
    class Status(models.TextChoices):
        RESERVED = 'RESERVED', 'Reserved'
        ISSUED = 'ISSUED', 'Issued'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    inventory_item = models.ForeignKey('inventory.InventoryItem', on_delete=models.PROTECT)
    work_order = models.ForeignKey('workorders.WorkOrder', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RESERVED)
    
    reserved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    reserved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_reservations'
