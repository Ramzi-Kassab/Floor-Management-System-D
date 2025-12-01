"""
ARDT FMS - Inventory Models
Version: 5.4

Tables:
- inventory_categories (P1)
- inventory_locations (P1)
- inventory_items (P1)
- inventory_stock (P1)
- inventory_transactions (P1)
"""

from django.db import models
from django.conf import settings


class InventoryCategory(models.Model):
    """
    🟢 P1: Categories for inventory items.
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
        db_table = 'inventory_categories'
        ordering = ['code']
        verbose_name = 'Inventory Category'
        verbose_name_plural = 'Inventory Categories'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class InventoryLocation(models.Model):
    """
    🟢 P1: Storage locations within warehouses.
    """
    
    warehouse = models.ForeignKey(
        'sales.Warehouse',
        on_delete=models.CASCADE,
        related_name='locations'
    )
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    
    # Location path (e.g., Aisle-Rack-Shelf-Bin)
    aisle = models.CharField(max_length=20, blank=True)
    rack = models.CharField(max_length=20, blank=True)
    shelf = models.CharField(max_length=20, blank=True)
    bin = models.CharField(max_length=20, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'inventory_locations'
        ordering = ['warehouse', 'code']
        unique_together = ['warehouse', 'code']
        verbose_name = 'Inventory Location'
        verbose_name_plural = 'Inventory Locations'
    
    def __str__(self):
        return f"{self.warehouse.code}/{self.code}"


class InventoryItem(models.Model):
    """
    🟢 P1: Inventory item master.
    """
    
    class ItemType(models.TextChoices):
        RAW_MATERIAL = 'RAW_MATERIAL', 'Raw Material'
        COMPONENT = 'COMPONENT', 'Component'
        CONSUMABLE = 'CONSUMABLE', 'Consumable'
        TOOL = 'TOOL', 'Tool'
        SPARE_PART = 'SPARE_PART', 'Spare Part'
        FINISHED_GOOD = 'FINISHED_GOOD', 'Finished Good'
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    category = models.ForeignKey(
        InventoryCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items'
    )
    
    # Units
    unit = models.CharField(max_length=20, default='EA', help_text='EA, KG, M, etc.')
    
    # Cost
    standard_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    last_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    currency = models.CharField(max_length=3, default='SAR')
    
    # Stock levels
    min_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    max_stock = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    reorder_point = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    
    # Lead time
    lead_time_days = models.IntegerField(default=0)
    
    # Specifications
    specifications = models.JSONField(null=True, blank=True)
    
    # Supplier
    primary_supplier = models.ForeignKey(
        'supplychain.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_items'
    )
    supplier_part_number = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_serialized = models.BooleanField(default=False, help_text='Track by serial number')
    is_lot_controlled = models.BooleanField(default=False, help_text='Track by lot/batch')
    
    # Image
    image = models.ImageField(upload_to='inventory/', null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_items'
    )
    
    class Meta:
        db_table = 'inventory_items'
        ordering = ['code']
        verbose_name = 'Inventory Item'
        verbose_name_plural = 'Inventory Items'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def total_stock(self):
        """Total stock across all locations."""
        return self.stock_records.aggregate(
            total=models.Sum('quantity_on_hand')
        )['total'] or 0


class InventoryStock(models.Model):
    """
    🟢 P1: Stock levels by location.
    """
    
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='stock_records'
    )
    location = models.ForeignKey(
        InventoryLocation,
        on_delete=models.CASCADE,
        related_name='stock_records'
    )
    
    quantity_on_hand = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    quantity_reserved = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    quantity_available = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    
    # Lot/Serial tracking
    lot_number = models.CharField(max_length=50, blank=True)
    serial_number = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    last_count_date = models.DateField(null=True, blank=True)
    last_movement_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'inventory_stock'
        unique_together = ['item', 'location', 'lot_number', 'serial_number']
        verbose_name = 'Inventory Stock'
        verbose_name_plural = 'Inventory Stock'
    
    def __str__(self):
        return f"{self.item.code} @ {self.location}: {self.quantity_on_hand}"
    
    def save(self, *args, **kwargs):
        self.quantity_available = float(self.quantity_on_hand) - float(self.quantity_reserved)
        super().save(*args, **kwargs)


class InventoryTransaction(models.Model):
    """
    🟢 P1: Inventory movements and transactions.
    """
    
    class TransactionType(models.TextChoices):
        RECEIPT = 'RECEIPT', 'Receipt'
        ISSUE = 'ISSUE', 'Issue'
        TRANSFER = 'TRANSFER', 'Transfer'
        ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
        RETURN = 'RETURN', 'Return'
        SCRAP = 'SCRAP', 'Scrap'
        CYCLE_COUNT = 'CYCLE_COUNT', 'Cycle Count'
    
    class LinkType(models.TextChoices):
        WORK_ORDER = 'WORK_ORDER', 'Work Order'
        PURCHASE_ORDER = 'PURCHASE_ORDER', 'Purchase Order'
        SALES_ORDER = 'SALES_ORDER', 'Sales Order'
        MWO = 'MWO', 'Maintenance Work Order'
        MANUAL = 'MANUAL', 'Manual'
    
    transaction_number = models.CharField(max_length=30, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    transaction_date = models.DateTimeField()
    
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    
    # Location
    from_location = models.ForeignKey(
        InventoryLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='outbound_transactions'
    )
    to_location = models.ForeignKey(
        InventoryLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inbound_transactions'
    )
    
    # Quantity
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    unit = models.CharField(max_length=20)
    
    # Cost
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Lot/Serial
    lot_number = models.CharField(max_length=50, blank=True)
    serial_number = models.CharField(max_length=50, blank=True)
    
    # Link to source document
    link_type = models.CharField(
        max_length=30,
        choices=LinkType.choices,
        null=True,
        blank=True
    )
    link_id = models.BigIntegerField(null=True, blank=True)
    reference_number = models.CharField(max_length=50, blank=True)
    
    reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inventory_transactions'
    )
    
    class Meta:
        db_table = 'inventory_transactions'
        ordering = ['-transaction_date']
        verbose_name = 'Inventory Transaction'
        verbose_name_plural = 'Inventory Transactions'
    
    def __str__(self):
        return f"{self.transaction_number} - {self.transaction_type}"
