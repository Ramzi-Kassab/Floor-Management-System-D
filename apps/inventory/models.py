"""
ARDT FMS - Inventory Models
Version: 5.5

Tables:
- inventory_categories (P1) - Enhanced with item_type link, code_prefix, name_template
- inventory_locations (P1)
- inventory_items (P1) - Enhanced with legacy refs, auto-code
- inventory_stock (P1)
- inventory_transactions (P1)
- category_attributes (NEW) - Smart attributes per category
- item_attribute_values (NEW) - Attribute values for items
- item_variants (NEW) - Variant tracking for condition/source
"""

from django.conf import settings
from django.db import models


class InventoryCategory(models.Model):
    """
    🟢 P1: Categories for inventory items.
    Enhanced with item_type mapping, code generation, and name templates.
    """

    class ItemType(models.TextChoices):
        RAW_MATERIAL = "RAW_MATERIAL", "Raw Material"
        COMPONENT = "COMPONENT", "Component"
        CONSUMABLE = "CONSUMABLE", "Consumable"
        TOOL = "TOOL", "Tool"
        SPARE_PART = "SPARE_PART", "Spare Part"
        FINISHED_GOOD = "FINISHED_GOOD", "Finished Good"

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # NEW: Item type mapping - selecting category auto-sets item type
    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices,
        default=ItemType.COMPONENT,
        help_text="Default item type for items in this category"
    )

    # NEW: Code generation settings
    code_prefix = models.CharField(
        max_length=10,
        blank=True,
        help_text="Prefix for auto-generated item codes (e.g., CUT, MAT, NOZ)"
    )
    next_sequence = models.IntegerField(
        default=1,
        help_text="Next sequence number for code generation"
    )

    # NEW: Name template for auto-generating item names from attributes
    name_template = models.CharField(
        max_length=500,
        blank=True,
        help_text="Template for auto-name: {size}mm {material} {grade} (uses attribute codes)"
    )

    class Meta:
        db_table = "inventory_categories"
        ordering = ["code"]
        verbose_name = "Inventory Category"
        verbose_name_plural = "Inventory Categories"

    def __str__(self):
        return f"{self.code} - {self.name}"

    def generate_next_code(self):
        """Generate the next item code for this category."""
        prefix = self.code_prefix or self.code[:3].upper()
        code = f"{prefix}-{str(self.next_sequence).zfill(4)}"
        self.next_sequence += 1
        self.save(update_fields=["next_sequence"])
        return code


class CategoryAttribute(models.Model):
    """
    NEW: Defines attributes for each category.
    Each category can have multiple attributes with validation rules.
    """

    class AttributeType(models.TextChoices):
        TEXT = "TEXT", "Text"
        NUMBER = "NUMBER", "Number"
        SELECT = "SELECT", "Select (Dropdown)"
        BOOLEAN = "BOOLEAN", "Yes/No"
        DATE = "DATE", "Date"

    category = models.ForeignKey(
        InventoryCategory,
        on_delete=models.CASCADE,
        related_name="attributes"
    )
    code = models.CharField(max_length=50, help_text="Attribute code for templates (e.g., size, material)")
    name = models.CharField(max_length=100, help_text="Display name")
    attribute_type = models.CharField(max_length=20, choices=AttributeType.choices, default=AttributeType.TEXT)

    # For NUMBER type
    unit = models.CharField(max_length=20, blank=True, help_text="Unit of measure (mm, kg, etc.)")
    min_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    max_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)

    # For SELECT type - JSON array of options
    options = models.JSONField(
        null=True,
        blank=True,
        help_text='Options for SELECT type: ["Option1", "Option2"] or [{"value": "opt1", "label": "Option 1"}]'
    )

    # Validation
    is_required = models.BooleanField(default=False)
    is_used_in_name = models.BooleanField(default=False, help_text="Include in auto-generated item name")

    # Display order
    display_order = models.IntegerField(default=0)

    # For inherited attributes from parent category
    is_inherited = models.BooleanField(default=False)

    class Meta:
        db_table = "category_attributes"
        ordering = ["category", "display_order", "name"]
        unique_together = ["category", "code"]
        verbose_name = "Category Attribute"
        verbose_name_plural = "Category Attributes"

    def __str__(self):
        return f"{self.category.code} - {self.name}"


class InventoryItem(models.Model):
    """
    🟢 P1: Inventory item master.
    Enhanced with legacy references and auto-code generation.
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

    # NEW: Flag to indicate if name was manually modified
    name_manually_set = models.BooleanField(default=False)

    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    category = models.ForeignKey(InventoryCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")

    # NEW: Legacy system references
    mat_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="SAP Legacy MAT No."
    )
    item_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Parallel ERP Item No."
    )

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

    # Specifications (legacy - now using ItemAttributeValue)
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

    # NEW: Has variants flag
    has_variants = models.BooleanField(default=False, help_text="Item has condition/source variants")

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
        indexes = [
            models.Index(fields=["mat_number"]),
            models.Index(fields=["item_number"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def total_stock(self):
        """Total stock across all locations (base item only)."""
        return self.stock_records.aggregate(total=models.Sum("quantity_on_hand"))["total"] or 0

    @property
    def total_stock_with_variants(self):
        """Total stock including all variants."""
        base_stock = self.total_stock
        variant_stock = sum(v.total_stock for v in self.variants.all())
        return base_stock + variant_stock

    def generate_name_from_attributes(self):
        """Generate item name from category template and attribute values."""
        if not self.category or not self.category.name_template:
            return self.name

        template = self.category.name_template
        for attr_value in self.attribute_values.select_related("attribute"):
            placeholder = "{" + attr_value.attribute.code + "}"
            if placeholder in template:
                display_value = attr_value.display_value
                if attr_value.attribute.unit:
                    display_value = f"{display_value}{attr_value.attribute.unit}"
                template = template.replace(placeholder, str(display_value))

        # Clean up any unreplaced placeholders
        import re
        template = re.sub(r'\{[^}]+\}', '', template)
        template = ' '.join(template.split())  # Clean extra spaces

        return template.strip() or self.name


class ItemAttributeValue(models.Model):
    """
    NEW: Stores attribute values for inventory items.
    Links items to their category-specific attribute values.
    """

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="attribute_values"
    )
    attribute = models.ForeignKey(
        CategoryAttribute,
        on_delete=models.CASCADE,
        related_name="values"
    )

    # Value storage (flexible)
    text_value = models.CharField(max_length=500, blank=True)
    number_value = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    boolean_value = models.BooleanField(null=True, blank=True)
    date_value = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "item_attribute_values"
        unique_together = ["item", "attribute"]
        verbose_name = "Item Attribute Value"
        verbose_name_plural = "Item Attribute Values"

    def __str__(self):
        return f"{self.item.code} - {self.attribute.name}: {self.display_value}"

    @property
    def display_value(self):
        """Return the appropriate value based on attribute type."""
        attr_type = self.attribute.attribute_type
        if attr_type == CategoryAttribute.AttributeType.NUMBER:
            return self.number_value
        elif attr_type == CategoryAttribute.AttributeType.BOOLEAN:
            return "Yes" if self.boolean_value else "No"
        elif attr_type == CategoryAttribute.AttributeType.DATE:
            return self.date_value
        else:
            return self.text_value

    @display_value.setter
    def display_value(self, value):
        """Set the appropriate value based on attribute type."""
        attr_type = self.attribute.attribute_type
        if attr_type == CategoryAttribute.AttributeType.NUMBER:
            self.number_value = value
        elif attr_type == CategoryAttribute.AttributeType.BOOLEAN:
            self.boolean_value = bool(value)
        elif attr_type == CategoryAttribute.AttributeType.DATE:
            self.date_value = value
        else:
            self.text_value = str(value) if value else ""


class ItemVariant(models.Model):
    """
    NEW: Tracks item variants based on condition and source.
    Each variant is a separate SKU with its own stock tracking.
    """

    class Condition(models.TextChoices):
        NEW = "NEW", "New"
        RECLAIMED = "RECLAIMED", "Reclaimed"
        USED = "USED", "Used"
        REFURBISHED = "REFURBISHED", "Refurbished"

    class SourceType(models.TextChoices):
        PURCHASED = "PURCHASED", "Purchased New"
        RETROFIT = "RETROFIT", "Retrofit (New Reclaimed)"
        E_AND_O = "E_AND_O", "E&O (Excessive & Obsolete)"
        ARDT_RECLAIMED = "ARDT_RECLAIMED", "ARDT Reclaimed Used"
        LSTK_RECLAIMED = "LSTK_RECLAIMED", "LSTK (Halliburton) Reclaimed"
        CLIENT_SPECIFIC = "CLIENT_SPECIFIC", "Client Specific"

    # Link to base item
    base_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="variants"
    )

    # Variant code (auto-generated: BASE-CODE-VARIANT-SUFFIX)
    code = models.CharField(max_length=60, unique=True)
    name = models.CharField(max_length=250)

    # Condition and source
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.NEW)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.PURCHASED)

    # Customer (for CLIENT_SPECIFIC source)
    customer = models.ForeignKey(
        "sales.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="item_variants"
    )

    # Cost (different from base item)
    standard_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    last_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    # Valuation percentage (e.g., E&O = 30% of original)
    valuation_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100,
        help_text="Percentage of base item cost for valuation"
    )

    # Source tracking
    source_bit_serial = models.CharField(
        max_length=100,
        blank=True,
        help_text="Serial number of source bit (for reclaimed items)"
    )
    source_work_order = models.CharField(
        max_length=50,
        blank=True,
        help_text="Work order that produced this reclaimed item"
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Notes
    notes = models.TextField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_variants"
    )

    class Meta:
        db_table = "item_variants"
        ordering = ["base_item", "condition", "source_type"]
        verbose_name = "Item Variant"
        verbose_name_plural = "Item Variants"
        indexes = [
            models.Index(fields=["condition"]),
            models.Index(fields=["source_type"]),
            models.Index(fields=["base_item", "condition"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.get_condition_display()} ({self.get_source_type_display()})"

    @property
    def total_stock(self):
        """Total stock for this variant across all locations."""
        return self.stock_records.aggregate(total=models.Sum("quantity_on_hand"))["total"] or 0

    def save(self, *args, **kwargs):
        # Auto-generate code if not set
        if not self.code:
            suffix = f"{self.condition[:3]}-{self.source_type[:3]}"
            self.code = f"{self.base_item.code}-{suffix}"

        # Auto-generate name if not set
        if not self.name:
            self.name = f"{self.base_item.name} ({self.get_condition_display()} - {self.get_source_type_display()})"

        # Set has_variants on base item
        if not self.base_item.has_variants:
            self.base_item.has_variants = True
            self.base_item.save(update_fields=["has_variants"])

        super().save(*args, **kwargs)


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


class VariantStock(models.Model):
    """
    Stock tracking for item variants.
    Similar to InventoryStock but for variants.
    """

    variant = models.ForeignKey(ItemVariant, on_delete=models.CASCADE, related_name="stock_records")
    location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, related_name="variant_stock_records")

    quantity_on_hand = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    quantity_reserved = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    quantity_available = models.DecimalField(max_digits=15, decimal_places=3, default=0)

    # Lot/Serial tracking
    lot_number = models.CharField(max_length=50, blank=True)
    serial_number = models.CharField(max_length=50, blank=True)

    last_movement_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "variant_stock"
        unique_together = ["variant", "location", "lot_number", "serial_number"]
        verbose_name = "Variant Stock"
        verbose_name_plural = "Variant Stock"

    def __str__(self):
        return f"{self.variant.code} @ {self.location}: {self.quantity_on_hand}"

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
