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

from django.conf import settings
from django.db import models


class InventoryCategory(models.Model):
    """
    🟢 P1: Categories for inventory items.
    """

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_categories"
        ordering = ["code"]
        verbose_name = "Inventory Category"
        verbose_name_plural = "Inventory Categories"

    def __str__(self):
        return f"{self.code} - {self.name}"


class InventoryLocation(models.Model):
    """
    🟢 P1: Storage locations within warehouses.
    """

    warehouse = models.ForeignKey("sales.Warehouse", on_delete=models.CASCADE, related_name="locations")
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=100)

    # Location path (e.g., Aisle-Rack-Shelf-Bin)
    aisle = models.CharField(max_length=20, blank=True)
    rack = models.CharField(max_length=20, blank=True)
    shelf = models.CharField(max_length=20, blank=True)
    bin = models.CharField(max_length=20, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "inventory_locations"
        ordering = ["warehouse", "code"]
        unique_together = ["warehouse", "code"]
        verbose_name = "Inventory Location"
        verbose_name_plural = "Inventory Locations"

    def __str__(self):
        return f"{self.warehouse.code}/{self.code}"


class InventoryItem(models.Model):
    """
    🟢 P1: Inventory item master.
    """

    class ItemType(models.TextChoices):
        RAW_MATERIAL = "RAW_MATERIAL", "Raw Material"
        COMPONENT = "COMPONENT", "Component"
        CONSUMABLE = "CONSUMABLE", "Consumable"
        TOOL = "TOOL", "Tool"
        SPARE_PART = "SPARE_PART", "Spare Part"
        FINISHED_GOOD = "FINISHED_GOOD", "Finished Good"

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    category = models.ForeignKey(InventoryCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")

    # Units
    unit = models.CharField(max_length=20, default="EA", help_text="EA, KG, M, etc.")

    # Cost
    standard_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    last_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    currency = models.CharField(max_length=3, default="SAR")

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
        "supplychain.Supplier", on_delete=models.SET_NULL, null=True, blank=True, related_name="primary_items"
    )
    supplier_part_number = models.CharField(max_length=100, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_serialized = models.BooleanField(default=False, help_text="Track by serial number")
    is_lot_controlled = models.BooleanField(default=False, help_text="Track by lot/batch")

    # Image
    image = models.ImageField(upload_to="inventory/", null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_items"
    )

    class Meta:
        db_table = "inventory_items"
        ordering = ["code"]
        verbose_name = "Inventory Item"
        verbose_name_plural = "Inventory Items"

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def total_stock(self):
        """Total stock across all locations."""
        return self.stock_records.aggregate(total=models.Sum("quantity_on_hand"))["total"] or 0


class InventoryStock(models.Model):
    """
    🟢 P1: Stock levels by location.
    """

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="stock_records")
    location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, related_name="stock_records")

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
        db_table = "inventory_stock"
        unique_together = ["item", "location", "lot_number", "serial_number"]
        verbose_name = "Inventory Stock"
        verbose_name_plural = "Inventory Stock"

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
        RECEIPT = "RECEIPT", "Receipt"
        ISSUE = "ISSUE", "Issue"
        TRANSFER = "TRANSFER", "Transfer"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        RETURN = "RETURN", "Return"
        SCRAP = "SCRAP", "Scrap"
        CYCLE_COUNT = "CYCLE_COUNT", "Cycle Count"

    class LinkType(models.TextChoices):
        WORK_ORDER = "WORK_ORDER", "Work Order"
        PURCHASE_ORDER = "PURCHASE_ORDER", "Purchase Order"
        SALES_ORDER = "SALES_ORDER", "Sales Order"
        MWO = "MWO", "Maintenance Work Order"
        MANUAL = "MANUAL", "Manual"

    transaction_number = models.CharField(max_length=30, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    transaction_date = models.DateTimeField()

    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="transactions")

    # Location
    from_location = models.ForeignKey(
        InventoryLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name="outbound_transactions"
    )
    to_location = models.ForeignKey(
        InventoryLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name="inbound_transactions"
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
    link_type = models.CharField(max_length=30, choices=LinkType.choices, null=True, blank=True)
    link_id = models.BigIntegerField(null=True, blank=True)
    reference_number = models.CharField(max_length=50, blank=True)

    reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="inventory_transactions"
    )

    class Meta:
        db_table = "inventory_transactions"
        ordering = ["-transaction_date"]
        verbose_name = "Inventory Transaction"
        verbose_name_plural = "Inventory Transactions"

    def __str__(self):
        return f"{self.transaction_number} - {self.transaction_type}"


# =============================================================================
# SPRINT 4: MATERIAL LOT TRACKING
# =============================================================================

class MaterialLot(models.Model):
    """
    Sprint 4: Lot/batch tracking for inventory items.
    Enables full traceability of materials used in repairs.
    """
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        IN_USE = "IN_USE", "In Use"
        CONSUMED = "CONSUMED", "Consumed"
        EXPIRED = "EXPIRED", "Expired"
        QUARANTINED = "QUARANTINED", "Quarantined"

    lot_number = models.CharField(max_length=50, unique=True)
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT, related_name="lots"
    )

    # Quantities
    initial_quantity = models.DecimalField(max_digits=15, decimal_places=3)
    quantity_on_hand = models.DecimalField(max_digits=15, decimal_places=3)
    quantity_reserved = models.DecimalField(max_digits=15, decimal_places=3, default=0)

    @property
    def quantity_available(self):
        return self.quantity_on_hand - self.quantity_reserved

    # Dates
    received_date = models.DateField()
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    # Source
    vendor = models.ForeignKey(
        "supplychain.Supplier", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="material_lots"
    )
    purchase_order = models.CharField(max_length=50, blank=True)
    vendor_lot_number = models.CharField(max_length=50, blank=True)

    # Certification
    cert_number = models.CharField(max_length=100, blank=True)
    certificate = models.FileField(upload_to="lot_certificates/", null=True, blank=True)

    # Location
    location = models.ForeignKey(
        InventoryLocation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lots"
    )

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)

    # Cost
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="created_lots"
    )

    class Meta:
        db_table = "material_lots"
        ordering = ["-received_date", "lot_number"]
        verbose_name = "Material Lot"
        verbose_name_plural = "Material Lots"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["expiry_date"]),
            models.Index(fields=["inventory_item", "status"]),
        ]

    def __str__(self):
        return f"{self.lot_number} - {self.inventory_item.code}"

    @property
    def is_expired(self):
        from django.utils import timezone
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False


class MaterialConsumption(models.Model):
    """
    Sprint 4: Tracks material consumption per work order.
    Links lot-level traceability to work orders.
    """
    work_order = models.ForeignKey(
        "workorders.WorkOrder", on_delete=models.CASCADE,
        related_name="material_consumptions"
    )
    lot = models.ForeignKey(
        MaterialLot, on_delete=models.PROTECT, related_name="consumptions"
    )

    # Quantity consumed
    quantity_consumed = models.DecimalField(max_digits=15, decimal_places=3)
    consumed_at = models.DateTimeField(auto_now_add=True)
    consumed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="material_consumptions"
    )

    # Link to operation (optional)
    operation_execution = models.ForeignKey(
        "workorders.OperationExecution", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="material_consumptions"
    )

    # Cost
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    @property
    def total_cost(self):
        return self.quantity_consumed * self.unit_cost

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "material_consumptions"
        ordering = ["-consumed_at"]
        verbose_name = "Material Consumption"
        verbose_name_plural = "Material Consumptions"
        indexes = [
            models.Index(fields=["work_order"]),
            models.Index(fields=["lot"]),
        ]

    def __str__(self):
        return f"{self.lot.lot_number} - {self.quantity_consumed} for {self.work_order.wo_number}"


# =============================================================================
# UNIT OF MEASURE
# =============================================================================


class UnitOfMeasure(models.Model):
    """
    Unit of measure for inventory items.
    Supports different types: quantity, length, weight, volume, etc.
    """

    class UnitType(models.TextChoices):
        QUANTITY = "QUANTITY", "Quantity (Count)"
        LENGTH = "LENGTH", "Length"
        WEIGHT = "WEIGHT", "Weight/Mass"
        VOLUME = "VOLUME", "Volume"
        AREA = "AREA", "Area"
        TIME = "TIME", "Time"
        OTHER = "OTHER", "Other"

    code = models.CharField(max_length=10, unique=True, help_text="Short code (EA, KG, M, etc.)")
    name = models.CharField(max_length=50, help_text="Full name (Each, Kilogram, Meter)")
    unit_type = models.CharField(max_length=20, choices=UnitType.choices, default=UnitType.QUANTITY)
    symbol = models.CharField(max_length=10, blank=True, help_text="Symbol for display (kg, m, L)")
    conversion_factor = models.DecimalField(
        max_digits=15, decimal_places=6, default=1,
        help_text="Multiply by this to convert to base unit"
    )
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "units_of_measure"
        ordering = ["unit_type", "code"]
        verbose_name = "Unit of Measure"
        verbose_name_plural = "Units of Measure"

    def __str__(self):
        if self.symbol:
            return f"{self.name} ({self.symbol})"
        return self.name


# =============================================================================
# ATTRIBUTE SYSTEM
# =============================================================================


class Attribute(models.Model):
    """
    Reusable attributes that can be linked to categories.
    E.g., Size, Color, Material, Diameter, etc.
    """

    code = models.CharField(max_length=50, unique=True, help_text="Unique code (e.g., size, color, material)")
    name = models.CharField(max_length=100, help_text="Display name (e.g., Size, Color, Material)")
    description = models.TextField(blank=True, help_text="Optional description of this attribute")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attributes"
        ordering = ["name"]
        verbose_name = "Attribute"
        verbose_name_plural = "Attributes"

    def __str__(self):
        return f"{self.code} - {self.name}"


class CategoryAttribute(models.Model):
    """
    Links attributes to categories with specific configuration.
    Defines how an attribute behaves for items in a category.
    """

    class AttributeType(models.TextChoices):
        TEXT = "TEXT", "Text"
        NUMBER = "NUMBER", "Number"
        SELECT = "SELECT", "Select (Dropdown)"
        BOOLEAN = "BOOLEAN", "Yes/No"
        DATE = "DATE", "Date"

    category = models.ForeignKey(
        InventoryCategory, on_delete=models.CASCADE,
        related_name="category_attributes"
    )
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE,
        related_name="category_usages"
    )
    attribute_type = models.CharField(
        max_length=20, choices=AttributeType.choices, default=AttributeType.TEXT,
        help_text="How this attribute is used in this category"
    )
    min_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    max_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    options = models.JSONField(
        null=True, blank=True,
        help_text='Options for SELECT type: ["Option1", "Option2"] or [{"value": "opt1", "label": "Option 1"}]'
    )
    is_required = models.BooleanField(default=False)
    is_used_in_name = models.BooleanField(default=False, help_text="Include in auto-generated item name")
    display_order = models.IntegerField(default=0)
    is_inherited = models.BooleanField(default=False)

    class Meta:
        db_table = "category_attributes"
        ordering = ["category", "display_order"]
        unique_together = ["category", "attribute"]
        verbose_name = "Category Attribute"
        verbose_name_plural = "Category Attributes"

    def __str__(self):
        return f"{self.category.name} - {self.attribute.name}"


class ItemAttributeValue(models.Model):
    """
    Actual attribute values for inventory items.
    Stores values in appropriate typed fields.
    """

    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE,
        related_name="attribute_values"
    )
    category_attribute = models.ForeignKey(
        CategoryAttribute, on_delete=models.CASCADE,
        related_name="values"
    )
    text_value = models.CharField(max_length=500, blank=True)
    number_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    boolean_value = models.BooleanField(null=True, blank=True)
    date_value = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "item_attribute_values"
        unique_together = ["item", "category_attribute"]
        verbose_name = "Item Attribute Value"
        verbose_name_plural = "Item Attribute Values"

    def __str__(self):
        return f"{self.item.code} - {self.category_attribute.attribute.name}"

    @property
    def value(self):
        """Return the appropriate value based on attribute type."""
        attr_type = self.category_attribute.attribute_type
        if attr_type == CategoryAttribute.AttributeType.BOOLEAN:
            return self.boolean_value
        elif attr_type == CategoryAttribute.AttributeType.DATE:
            return self.date_value
        elif attr_type == CategoryAttribute.AttributeType.NUMBER:
            return self.number_value
        return self.text_value


# =============================================================================
# VARIANT SYSTEM
# =============================================================================


class VariantCase(models.Model):
    """
    Predefined variant cases/scenarios.
    E.g., NEW-PUR (New Purchase), USED-RET (Used Return), etc.
    """

    class Condition(models.TextChoices):
        NEW = "NEW", "New"
        USED = "USED", "Used"

    class Source(models.TextChoices):
        PURCHASE = "PURCHASE", "Purchase"
        RETURN = "RETURN", "Return"
        REPAIR = "REPAIR", "Repair"
        RERUN = "RERUN", "Rerun"

    code = models.CharField(max_length=30, unique=True, help_text="Unique case code (e.g., NEW-PUR, USED-RET)")
    name = models.CharField(max_length=100, help_text="Display name for this variant case")
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.NEW)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.PURCHASE)
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "variant_cases"
        ordering = ["display_order", "code"]
        verbose_name = "Variant Case"
        verbose_name_plural = "Variant Cases"

    def __str__(self):
        return f"{self.code} - {self.name}"


class ItemVariant(models.Model):
    """
    Represents a specific variant of an inventory item.
    Variants combine base item with a case (condition/source) and optional client.
    """

    base_item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE,
        related_name="variants"
    )
    variant_case = models.ForeignKey(
        VariantCase, on_delete=models.PROTECT,
        related_name="item_variants"
    )
    client = models.ForeignKey(
        "organization.Customer", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="item_variants",
        help_text="Client-specific variant (if applicable)"
    )

    code = models.CharField(max_length=100, unique=True)
    client_code = models.CharField(max_length=50, blank=True, help_text="Client-specific item code")

    # Costing
    standard_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    last_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    # Legacy identifiers
    legacy_mat_no = models.CharField(max_length=50, blank=True, help_text="Legacy MAT number")
    erp_item_no = models.CharField(max_length=50, blank=True, help_text="ERP Item number")

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="created_variants"
    )

    class Meta:
        db_table = "item_variants"
        ordering = ["base_item", "variant_case"]
        unique_together = ["base_item", "variant_case", "client"]
        verbose_name = "Item Variant"
        verbose_name_plural = "Item Variants"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if not self.code:
            # Auto-generate code: BASE-ITEM-CODE-CASE-CODE[-CLIENT]
            parts = [self.base_item.code, self.variant_case.code]
            if self.client:
                parts.append(self.client.code[:10])
            self.code = "-".join(parts)
        super().save(*args, **kwargs)


class VariantStock(models.Model):
    """
    Stock tracking for item variants by warehouse.
    """

    variant = models.ForeignKey(
        ItemVariant, on_delete=models.CASCADE,
        related_name="stock_records"
    )
    warehouse = models.ForeignKey(
        "sales.Warehouse", on_delete=models.CASCADE,
        related_name="variant_stocks"
    )

    quantity_on_hand = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    quantity_reserved = models.DecimalField(max_digits=15, decimal_places=3, default=0)

    @property
    def quantity_available(self):
        return self.quantity_on_hand - self.quantity_reserved

    min_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    max_stock = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    reorder_point = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    last_movement_date = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "variant_stocks"
        unique_together = ["variant", "warehouse"]
        verbose_name = "Variant Stock"
        verbose_name_plural = "Variant Stocks"

    def __str__(self):
        return f"{self.variant.code} @ {self.warehouse.code}: {self.quantity_on_hand}"


# =============================================================================
# ITEM PLANNING & SUPPLIERS
# =============================================================================


class ItemPlanning(models.Model):
    """
    Warehouse-specific planning parameters for inventory items.
    """

    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE,
        related_name="planning_records"
    )
    warehouse = models.ForeignKey(
        "sales.Warehouse", on_delete=models.CASCADE,
        related_name="item_planning_records"
    )

    # Stock levels
    min_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    max_stock = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    reorder_point = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    # Planning parameters
    safety_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    lead_time_days = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "item_planning"
        unique_together = ["item", "warehouse"]
        verbose_name = "Item Planning"
        verbose_name_plural = "Item Planning Records"

    def __str__(self):
        return f"{self.item.code} @ {self.warehouse.code}"


class ItemSupplier(models.Model):
    """
    Supplier information for inventory items.
    Supports multiple suppliers per item with priority ranking.
    """

    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE,
        related_name="item_suppliers"
    )
    supplier = models.ForeignKey(
        "supplychain.Supplier", on_delete=models.CASCADE,
        related_name="supplied_items"
    )

    supplier_part_number = models.CharField(max_length=100, blank=True)
    supplier_description = models.CharField(max_length=255, blank=True)

    # Pricing
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    currency = models.CharField(max_length=3, default="SAR")
    min_order_qty = models.DecimalField(max_digits=10, decimal_places=3, default=1)

    # Lead time
    lead_time_days = models.IntegerField(default=0)

    # Priority
    priority = models.IntegerField(default=1, help_text="1 = Primary, 2 = Secondary, etc.")
    is_preferred = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "item_suppliers"
        unique_together = ["item", "supplier"]
        ordering = ["item", "priority"]
        verbose_name = "Item Supplier"
        verbose_name_plural = "Item Suppliers"

    def __str__(self):
        return f"{self.item.code} - {self.supplier.name}"


class ItemIdentifier(models.Model):
    """
    Additional identifiers for inventory items.
    Supports multiple identifier types: barcode, RFID, QR, etc.
    """

    class IdentifierType(models.TextChoices):
        BARCODE = "BARCODE", "Barcode"
        QR_CODE = "QR_CODE", "QR Code"
        RFID = "RFID", "RFID Tag"
        SKU = "SKU", "SKU"
        UPC = "UPC", "UPC"
        EAN = "EAN", "EAN"
        MPN = "MPN", "Manufacturer Part Number"
        INTERNAL = "INTERNAL", "Internal Code"
        LEGACY = "LEGACY", "Legacy Code"
        OTHER = "OTHER", "Other"

    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE,
        related_name="identifiers"
    )

    identifier_type = models.CharField(max_length=20, choices=IdentifierType.choices)
    identifier_value = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)

    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "item_identifiers"
        unique_together = ["item", "identifier_type", "identifier_value"]
        verbose_name = "Item Identifier"
        verbose_name_plural = "Item Identifiers"

    def __str__(self):
        return f"{self.item.code} - {self.identifier_type}: {self.identifier_value}"


# =============================================================================
# BIT & CUTTER SPECIFICATIONS
# =============================================================================


class ItemBitSpec(models.Model):
    """
    Bit-specific specifications for inventory items.
    Only applicable to items in bit-related categories.
    """

    item = models.OneToOneField(
        InventoryItem, on_delete=models.CASCADE,
        related_name="bit_spec"
    )

    # Size & Type
    bit_size = models.ForeignKey(
        "workorders.BitSize", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="bit_specs"
    )
    bit_type = models.ForeignKey(
        "workorders.BitType", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="bit_specs"
    )

    # Specifications
    tfa = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        help_text="Total Flow Area (sq in)"
    )
    blade_count = models.IntegerField(null=True, blank=True)
    cutter_count = models.IntegerField(null=True, blank=True)
    nozzle_count = models.IntegerField(null=True, blank=True)

    # IADC
    iadc_code = models.CharField(max_length=10, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "item_bit_specs"
        verbose_name = "Item Bit Specification"
        verbose_name_plural = "Item Bit Specifications"

    def __str__(self):
        return f"Bit Spec: {self.item.code}"


class ItemCutterSpec(models.Model):
    """
    Cutter-specific specifications for inventory items.
    Only applicable to items in cutter-related categories.
    """

    class CutterType(models.TextChoices):
        PDC = "PDC", "PDC"
        TSP = "TSP", "TSP"
        NATURAL_DIAMOND = "NATURAL_DIAMOND", "Natural Diamond"
        IMPREGNATED = "IMPREGNATED", "Impregnated"
        OTHER = "OTHER", "Other"

    class CutterShape(models.TextChoices):
        ROUND = "ROUND", "Round"
        OVAL = "OVAL", "Oval"
        CONICAL = "CONICAL", "Conical"
        DOME = "DOME", "Dome"
        CHISEL = "CHISEL", "Chisel"
        OTHER = "OTHER", "Other"

    item = models.OneToOneField(
        InventoryItem, on_delete=models.CASCADE,
        related_name="cutter_spec"
    )

    # Type & Shape
    cutter_type = models.CharField(
        max_length=20, choices=CutterType.choices, default=CutterType.PDC
    )
    cutter_shape = models.CharField(
        max_length=20, choices=CutterShape.choices, default=CutterShape.ROUND
    )

    # Dimensions (mm)
    diameter = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    thickness = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    chamfer_size = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)

    # Grade
    grade = models.CharField(max_length=50, blank=True)
    substrate = models.CharField(max_length=50, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "item_cutter_specs"
        verbose_name = "Item Cutter Specification"
        verbose_name_plural = "Item Cutter Specifications"

    def __str__(self):
        return f"Cutter Spec: {self.item.code}"
