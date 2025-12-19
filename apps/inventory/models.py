"""
ARDT FMS - Inventory Models
Version: 6.0 (Ledger-Based Architecture)

PHASE 0: FOUNDATION (Master Data)
- Party - Unified owner polymorphism (Customer, Vendor, Internal, Rig)
- ConditionType - Item conditions (NEW, USED-RETROFIT, USED-GROUND, etc.)
- QualityStatus - Quality gate states (QUARANTINE, RELEASED, BLOCKED)
- AdjustmentReason - Reasons for stock adjustments
- OwnershipType - Ownership types (ARDT, CLIENT, VENDOR, etc.)

EXISTING TABLES:
- units_of_measure - Master data for units
- inventory_categories (P1) - Enhanced with item_type link, code_prefix, name_template
- inventory_locations (P1) - Enhanced with location_type and party_fk
- inventory_items (P1) - Enhanced with legacy refs, auto-code
- inventory_stock (P1)
- inventory_transactions (P1)
- category_attributes - Smart attributes per category
- item_attribute_values - Attribute values for items
- item_variants - Variant tracking for condition/source
- material_lots - Lot/batch tracking
"""

from django.conf import settings
from django.db import models


# =============================================================================
# PHASE 0: FOUNDATION - MASTER DATA TABLES
# =============================================================================


class Party(models.Model):
    """
    Unified owner polymorphism table.

    All ownership references (stock owner, location owner, movement counterparty)
    point to Party. This provides a single, consistent way to track ownership
    across the system without complex polymorphic joins.

    Party types:
    - CUSTOMER: Links to sales.Customer
    - VENDOR: Links to supplychain.Supplier
    - INTERNAL: Internal departments (e.g., ARDT)
    - RIG: Links to sales.Rig

    Examples:
    - ARDT main warehouse stock: party_type=INTERNAL, code='ARDT'
    - Client-owned stock at ARDT: party_type=CUSTOMER, customer_fk=<customer>
    - Stock at rig: party_type=RIG, rig_fk=<rig>
    """

    class PartyType(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        VENDOR = "VENDOR", "Vendor/Supplier"
        INTERNAL = "INTERNAL", "Internal (ARDT)"
        RIG = "RIG", "Rig Site"

    code = models.CharField(max_length=50, unique=True, help_text="Unique party code")
    name = models.CharField(max_length=200, help_text="Party display name")
    party_type = models.CharField(max_length=20, choices=PartyType.choices)

    # Optional foreign keys to source entities
    customer = models.OneToOneField(
        "sales.Customer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="party",
        help_text="Link to Customer for CUSTOMER type"
    )
    vendor = models.OneToOneField(
        "supplychain.Supplier",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="party",
        help_text="Link to Vendor/Supplier for VENDOR type"
    )
    rig = models.OneToOneField(
        "sales.Rig",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="party",
        help_text="Link to Rig for RIG type"
    )

    # Additional info
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    # Ownership capability (for validation without CHECK constraints)
    can_own_stock = models.BooleanField(
        default=True,
        help_text="Can this party own stock? RIG parties typically cannot own stock directly."
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "parties"
        ordering = ["party_type", "name"]
        verbose_name = "Party"
        verbose_name_plural = "Parties"
        indexes = [
            models.Index(fields=["party_type"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.name} ({self.get_party_type_display()})"

    def save(self, *args, **kwargs):
        # Auto-generate code from linked entity if not set
        if not self.code:
            if self.customer:
                self.code = f"C-{self.customer.code}"
            elif self.vendor:
                self.code = f"V-{self.vendor.code}"
            elif self.rig:
                self.code = f"R-{self.rig.code}"
            else:
                self.code = f"INT-{self.name[:10].upper()}"
        super().save(*args, **kwargs)

    @classmethod
    def get_or_create_for_customer(cls, customer):
        """Get or create a Party for a Customer."""
        party, created = cls.objects.get_or_create(
            customer=customer,
            defaults={
                'code': f"C-{customer.code}",
                'name': customer.name,
                'party_type': cls.PartyType.CUSTOMER,
            }
        )
        return party

    @classmethod
    def get_or_create_for_vendor(cls, vendor):
        """Get or create a Party for a Vendor/Supplier."""
        party, created = cls.objects.get_or_create(
            vendor=vendor,
            defaults={
                'code': f"V-{vendor.code}",
                'name': vendor.name,
                'party_type': cls.PartyType.VENDOR,
            }
        )
        return party

    @classmethod
    def get_or_create_for_rig(cls, rig):
        """Get or create a Party for a Rig."""
        party, created = cls.objects.get_or_create(
            rig=rig,
            defaults={
                'code': f"R-{rig.code}",
                'name': rig.name,
                'party_type': cls.PartyType.RIG,
            }
        )
        return party


class ConditionType(models.Model):
    """
    Master data for item conditions.

    Condition represents the commercial identity of inventory:
    - NEW: Brand new, never used
    - USED-RETROFIT: Used, reconditioned to "as-new" standard
    - USED-GROUND: Used, surface damage repaired
    - USED-E&O: Used, excess and obsolete
    - REFURBISHED: Factory refurbished
    - SCRAP: Damaged beyond repair

    Condition affects pricing, accounting, and which stocks are interchangeable.
    """

    code = models.CharField(max_length=20, unique=True, help_text="Condition code (e.g., NEW, USED-RET)")
    name = models.CharField(max_length=100, help_text="Display name")
    description = models.TextField(blank=True)

    # Categorization
    is_new = models.BooleanField(default=False, help_text="Is this a 'new' condition?")
    is_saleable = models.BooleanField(default=True, help_text="Can items in this condition be sold?")

    # Cost multiplier (1.0 = full price, 0.7 = 70% of new price)
    cost_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.00,
        help_text="Price multiplier relative to NEW (e.g., 0.70 for 70%)"
    )

    # Display
    display_order = models.IntegerField(default=0)
    color_code = models.CharField(max_length=20, blank=True, help_text="CSS color for UI (e.g., #22c55e)")
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class (e.g., fa-star)")

    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "condition_types"
        ordering = ["display_order", "code"]
        verbose_name = "Condition Type"
        verbose_name_plural = "Condition Types"

    def __str__(self):
        return f"{self.code} - {self.name}"


class QualityStatus(models.Model):
    """
    Master data for quality gate states.

    Quality status tracks the QC workflow state:
    - QUARANTINE: Awaiting inspection (default for receipts)
    - RELEASED: Passed QC, available for use
    - BLOCKED: Failed QC, not available for use
    - UNDER_INSPECTION: Currently being inspected
    - PENDING_DISPOSITION: Failed, awaiting decision

    Status transitions are controlled by the QC workflow.
    """

    code = models.CharField(max_length=20, unique=True, help_text="Status code (e.g., QRN, REL, BLK)")
    name = models.CharField(max_length=100, help_text="Display name")
    description = models.TextField(blank=True)

    # Availability flags
    is_available = models.BooleanField(default=False, help_text="Can stock in this status be used/issued?")
    is_initial = models.BooleanField(default=False, help_text="Default status for new receipts?")
    is_terminal = models.BooleanField(default=False, help_text="Is this a final state (no further transitions)?")

    # Allowed transitions (JSON list of status codes)
    allowed_transitions = models.JSONField(
        default=list,
        help_text='List of status codes this can transition to: ["REL", "BLK"]'
    )

    # Display
    display_order = models.IntegerField(default=0)
    color_code = models.CharField(max_length=20, blank=True, help_text="CSS color for UI")
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class")

    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "quality_statuses"
        ordering = ["display_order", "code"]
        verbose_name = "Quality Status"
        verbose_name_plural = "Quality Statuses"

    def __str__(self):
        return f"{self.code} - {self.name}"

    def can_transition_to(self, target_status_code):
        """Check if transition to target status is allowed."""
        return target_status_code in self.allowed_transitions


class AdjustmentReason(models.Model):
    """
    Master data for stock adjustment reasons.

    Used when quantity changes occur outside normal document flow:
    - DAMAGE: Item damaged
    - LOSS: Item lost/missing
    - FOUND: Previously missing item found
    - SCRAP: Item scrapped
    - OBSOLETE: Item obsoleted
    - CYCLE_COUNT: Cycle count adjustment
    - INITIAL: Initial stock entry
    - PRODUCTION_VARIANCE: Production over/under run
    - RETURN_TO_VENDOR: Returned to vendor

    Each reason has a default direction (positive/negative adjustment).
    """

    code = models.CharField(max_length=20, unique=True, help_text="Reason code")
    name = models.CharField(max_length=100, help_text="Display name")
    description = models.TextField(blank=True)

    # Adjustment direction
    default_direction = models.CharField(
        max_length=10,
        choices=[("POSITIVE", "Increase Stock"), ("NEGATIVE", "Decrease Stock"), ("BOTH", "Either")],
        default="NEGATIVE"
    )

    # Accounting impact
    requires_approval = models.BooleanField(default=False, help_text="Requires manager approval?")
    affects_valuation = models.BooleanField(default=True, help_text="Affects inventory valuation?")
    gl_account = models.CharField(max_length=20, blank=True, help_text="Default GL account for posting")

    # Display
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "adjustment_reasons"
        ordering = ["display_order", "code"]
        verbose_name = "Adjustment Reason"
        verbose_name_plural = "Adjustment Reasons"

    def __str__(self):
        return f"{self.code} - {self.name}"


class OwnershipType(models.Model):
    """
    Defines the legal/financial relationship of stock ownership.

    This is SEPARATE from Party (which identifies WHO owns/is responsible).
    OwnershipType defines WHAT the relationship is for financial reporting.

    Core Types (simplified to 4):
    - OWNED: We own the stock (appears on our balance sheet)
    - CLIENT: Client owns stock, we hold it (custodial responsibility)
    - CONSIGNMENT_IN: Vendor owns stock at our location (not our asset)
    - CONSIGNMENT_OUT: We own stock at customer site (our asset, their custody)

    Examples:
    - ARDT owns stock at ARDT warehouse: owner_party=ARDT, ownership_type=OWNED
    - Aramco owns stock at ARDT warehouse: owner_party=Aramco, ownership_type=CLIENT
    - ARDT owns stock at Aramco rig site: owner_party=ARDT, ownership_type=CONSIGNMENT_OUT
    - Baker Hughes stock at ARDT (consignment): owner_party=BakerHughes, ownership_type=CONSIGNMENT_IN

    Financial Impact:
    - OWNED: Asset on ARDT balance sheet
    - CLIENT: Off-balance-sheet, tracked for liability
    - CONSIGNMENT_IN: Off-balance-sheet, vendor's asset
    - CONSIGNMENT_OUT: On ARDT balance sheet (we own it)
    """

    code = models.CharField(max_length=20, unique=True, help_text="Ownership code")
    name = models.CharField(max_length=100, help_text="Display name")
    description = models.TextField(blank=True)

    # Ownership characteristics
    is_ardt_owned = models.BooleanField(default=False, help_text="Is stock owned by ARDT?")
    requires_party = models.BooleanField(default=False, help_text="Requires party reference?")

    # Accounting - clearer naming
    affects_balance_sheet = models.BooleanField(
        default=False,
        help_text="True if this ownership type should appear on ARDT's balance sheet"
    )
    include_in_valuation = models.BooleanField(default=True, help_text="Include in inventory valuation?")

    # Display
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ownership_types"
        ordering = ["display_order", "code"]
        verbose_name = "Ownership Type"
        verbose_name_plural = "Ownership Types"

    def __str__(self):
        return f"{self.code} - {self.name}"


class LocationType(models.Model):
    """
    Master data for location types.

    Categorizes inventory locations by function:
    - WAREHOUSE: Standard storage location
    - QUARANTINE: QC inspection area
    - PRODUCTION: Production/shop floor
    - TRANSIT: In-transit location
    - RIG: Rig site location
    - SCRAP: Scrap/disposal area
    - RECEIVING: Goods receiving area
    - SHIPPING: Goods shipping area

    Location type affects default behaviors (e.g., QUARANTINE locations
    default to quarantine quality status).
    """

    code = models.CharField(max_length=20, unique=True, help_text="Location type code")
    name = models.CharField(max_length=100, help_text="Display name")
    description = models.TextField(blank=True)

    # Behavior flags
    is_stockable = models.BooleanField(default=True, help_text="Can stock be stored here?")
    is_internal = models.BooleanField(default=True, help_text="Is this an internal location?")
    default_quality_status = models.ForeignKey(
        QualityStatus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_location_types",
        help_text="Default quality status for stock received here"
    )

    # Counting/physical inventory
    include_in_cycle_count = models.BooleanField(default=True)

    # Display
    display_order = models.IntegerField(default=0)
    color_code = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "location_types"
        ordering = ["display_order", "code"]
        verbose_name = "Location Type"
        verbose_name_plural = "Location Types"

    def __str__(self):
        return f"{self.code} - {self.name}"


# =============================================================================
# MASTER DATA: UNITS OF MEASURE
# =============================================================================


class UnitOfMeasure(models.Model):
    """
    Master data for units of measure.
    Provides standardized units for inventory items.
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

    # Conversion to base unit (optional)
    base_unit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="derived_units",
        help_text="Base unit for conversion"
    )
    conversion_factor = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=1,
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
        return f"{self.code} - {self.name}"


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


# =============================================================================
# MASTER DATA: ATTRIBUTES (Simple Global List)
# =============================================================================


class Attribute(models.Model):
    """
    Master data for attributes - simple global list of attribute names.
    Examples: Size, Color, Material, Grade, Finish, etc.

    The actual type, unit, validation, and options are defined when
    connecting an attribute to a category via CategoryAttribute.
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique code (e.g., size, color, material)"
    )
    name = models.CharField(max_length=100, help_text="Display name (e.g., Size, Color, Material)")
    description = models.TextField(blank=True, help_text="Optional description of this attribute")
    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attributes"
        ordering = ["name"]
        verbose_name = "Attribute"
        verbose_name_plural = "Attributes"

    def __str__(self):
        return self.name


class CategoryAttribute(models.Model):
    """
    Links an Attribute to a Category with specific configuration.
    This is where type, unit, validation, and options are defined.

    The same Attribute (e.g., "Size") can have different configurations
    per category:
    - For Clothing: Size is SELECT type with options [S, M, L, XL]
    - For Tools: Size is NUMBER type with unit "mm"
    - For Pipes: Size is NUMBER type with unit "inch"
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
        related_name="category_attributes"
    )
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        null=True,  # Temporary for migration
        related_name="category_usages",
        help_text="The attribute being configured for this category"
    )

    # Configuration for this category
    attribute_type = models.CharField(
        max_length=20,
        choices=AttributeType.choices,
        default=AttributeType.TEXT,
        help_text="How this attribute is used in this category"
    )

    # For NUMBER type
    unit = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="category_attributes",
        help_text="Unit of measure for NUMBER type"
    )
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
        ordering = ["category", "display_order"]
        unique_together = ["category", "attribute"]
        verbose_name = "Category Attribute"
        verbose_name_plural = "Category Attributes"

    def __str__(self):
        return f"{self.category.code} - {self.attribute.name}"

    @property
    def code(self):
        """Return the attribute code for backward compatibility."""
        return self.attribute.code

    @property
    def name(self):
        """Return the attribute name for backward compatibility."""
        return self.attribute.name


class InventoryItem(models.Model):
    """
    🟢 P1: Inventory item master.
    Clean architecture: Only universal fields here.
    Category-specific specs go to Attributes.
    Planning params go to ItemPlanning (per warehouse).
    Supplier info goes to ItemSupplier (many-to-many).

    Phase 1 Enhancements:
    - tracking_type: Consolidated tracking method (NONE, LOT, SERIAL, ASSET)
    - base_uom: Required for ledger operations (always store in base UOM)
    - costing_method: AVG (default), FIFO, or STD
    """

    class ItemType(models.TextChoices):
        STOCK_ITEM = "STOCK_ITEM", "Stock Item"
        NON_STOCK = "NON_STOCK", "Non-Stock Item"
        SERVICE = "SERVICE", "Service"
        ASSET_TEMPLATE = "ASSET_TEMPLATE", "Asset Template"
        # Legacy types for backward compatibility
        RAW_MATERIAL = "RAW_MATERIAL", "Raw Material"
        COMPONENT = "COMPONENT", "Component"
        CONSUMABLE = "CONSUMABLE", "Consumable"
        TOOL = "TOOL", "Tool"
        SPARE_PART = "SPARE_PART", "Spare Part"
        FINISHED_GOOD = "FINISHED_GOOD", "Finished Good"

    class LifecycleState(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        OBSOLETE = "OBSOLETE", "Obsolete"

    class Criticality(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class ABCClass(models.TextChoices):
        A = "A", "A - High Value"
        B = "B", "B - Medium Value"
        C = "C", "C - Low Value"

    # Phase 1: Consolidated tracking type
    class TrackingType(models.TextChoices):
        NONE = "NONE", "No Tracking (quantity only)"
        LOT = "LOT", "Lot/Batch Tracking"
        SERIAL = "SERIAL", "Serial Number Tracking"
        ASSET = "ASSET", "Asset Tracking (serialized + lifecycle)"

    # Phase 1: Costing method
    class CostingMethod(models.TextChoices):
        AVG = "AVG", "Weighted Average"
        FIFO = "FIFO", "First In First Out"
        STD = "STD", "Standard Cost"

    # Core identification
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    name_manually_set = models.BooleanField(default=False)

    # Classification
    item_type = models.CharField(max_length=20, choices=ItemType.choices, default=ItemType.STOCK_ITEM)
    category = models.ForeignKey(InventoryCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")
    lifecycle_state = models.CharField(max_length=20, choices=LifecycleState.choices, default=LifecycleState.ACTIVE)
    criticality = models.CharField(max_length=20, choices=Criticality.choices, default=Criticality.MEDIUM, blank=True)
    abc_class = models.CharField(max_length=1, choices=ABCClass.choices, blank=True)

    # Legacy system references
    mat_number = models.CharField(max_length=50, blank=True, help_text="SAP Legacy MAT No.")
    item_number = models.CharField(max_length=50, blank=True, help_text="Parallel ERP Item No.")

    # Unit of measure
    unit = models.CharField(max_length=20, default="EA", help_text="EA, KG, M, etc.")
    uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
        help_text="Preferred: Use UOM FK instead of unit char field"
    )

    # Phase 1: Base UOM for ledger operations (always store quantities in base UOM)
    base_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="items_using_as_base",
        help_text="Base UOM for ledger - all quantities stored in this unit"
    )

    # Phase 1: Consolidated tracking type
    tracking_type = models.CharField(
        max_length=10,
        choices=TrackingType.choices,
        default=TrackingType.NONE,
        help_text="How this item is tracked: NONE, LOT, SERIAL, or ASSET"
    )

    # Phase 1: Costing method for inventory valuation
    costing_method = models.CharField(
        max_length=10,
        choices=CostingMethod.choices,
        default=CostingMethod.AVG,
        help_text="Costing method: AVG (default), FIFO, or STD"
    )

    # Manufacturer / Brand (NEW)
    manufacturer = models.ForeignKey(
        "supplychain.Supplier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manufactured_items",
        help_text="Manufacturer (can be different from supplier)"
    )
    mpn = models.CharField(max_length=100, blank=True, help_text="Manufacturer Part Number")
    brand = models.CharField(max_length=100, blank=True, help_text="Brand name")

    # Cost (kept on item for default/standard cost)
    standard_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    last_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    currency = models.CharField(max_length=3, default="SAR")

    # DEPRECATED: Planning fields - Use ItemPlanning (per warehouse) instead
    min_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0, help_text="DEPRECATED: Use ItemPlanning")
    max_stock = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, help_text="DEPRECATED: Use ItemPlanning")
    reorder_point = models.DecimalField(max_digits=10, decimal_places=3, default=0, help_text="DEPRECATED: Use ItemPlanning")
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0, help_text="DEPRECATED: Use ItemPlanning")
    lead_time_days = models.IntegerField(default=0, help_text="DEPRECATED: Use ItemSupplier")

    # DEPRECATED: Use ItemAttributeValue instead
    specifications = models.JSONField(null=True, blank=True, help_text="DEPRECATED: Use ItemAttributeValue")

    # DEPRECATED: Supplier fields - Use ItemSupplier (many-to-many) instead
    primary_supplier = models.ForeignKey(
        "supplychain.Supplier", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="primary_items", help_text="DEPRECATED: Use ItemSupplier with is_preferred=True"
    )
    supplier_part_number = models.CharField(max_length=100, blank=True, help_text="DEPRECATED: Use ItemSupplier")

    # Traceability flags (CORE - keep here)
    is_active = models.BooleanField(default=True)
    is_serialized = models.BooleanField(default=False, help_text="Track by serial number (is_serial_tracked)")
    is_lot_controlled = models.BooleanField(default=False, help_text="Track by lot/batch (is_lot_tracked)")
    requires_expiry_tracking = models.BooleanField(default=False, help_text="Track expiry dates (is_expiry_tracked)")
    has_variants = models.BooleanField(default=False, help_text="Item has condition/source variants")

    # Shelf life (CORE - for expiry tracking)
    shelf_life_days = models.IntegerField(null=True, blank=True, help_text="Shelf life in days")

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


# =============================================================================
# VARIANT CASE (Master Data)
# =============================================================================


class VariantCase(models.Model):
    """
    Master data table for variant cases.
    Defines standard combinations of Condition + Acquisition + ReclaimCategory + Ownership.
    Examples: NEW-PURCHASED, USED-RECLAIMED-RETROFIT, USED-RECLAIMED-E&O, etc.

    When creating items, users select which variant cases apply to that item.
    """

    class Condition(models.TextChoices):
        NEW = "NEW", "New"
        USED = "USED", "Used"

    class Acquisition(models.TextChoices):
        PURCHASED = "PURCHASED", "Purchased"
        RECLAIMED = "RECLAIMED", "Reclaimed"
        MANUFACTURED = "MANUFACTURED", "Manufactured"
        CLIENT_PROVIDED = "CLIENT_PROVIDED", "Client Provided"

    class ReclaimCategory(models.TextChoices):
        RETROFIT = "RETROFIT", "Retrofit (as New)"
        E_AND_O = "E_AND_O", "E&O (Excessive & Obsolete)"
        GROUND = "GROUND", "Ground (Surface Damage)"
        STANDARD = "STANDARD", "Standard Reclaim"

    class Ownership(models.TextChoices):
        ARDT = "ARDT", "ARDT"
        CLIENT = "CLIENT", "Client"

    code = models.CharField(max_length=30, unique=True, help_text="Unique case code (e.g., NEW-PUR, USED-RET)")
    name = models.CharField(max_length=100, help_text="Display name for this variant case")

    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.NEW)
    acquisition = models.CharField(max_length=20, choices=Acquisition.choices, default=Acquisition.PURCHASED)
    reclaim_category = models.CharField(max_length=20, choices=ReclaimCategory.choices, blank=True)
    ownership = models.CharField(max_length=20, choices=Ownership.choices, default=Ownership.ARDT)

    # For CLIENT ownership - which client this case is for
    client_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Client code for CLIENT ownership cases (e.g., LSTK, Halliburton)"
    )

    description = models.TextField(blank=True, help_text="Description of when this case applies")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "variant_cases"
        ordering = ["display_order", "code"]
        verbose_name = "Variant Case"
        verbose_name_plural = "Variant Cases"

    def __str__(self):
        return f"{self.code} - {self.name}"


# =============================================================================
# ITEM VARIANT (Links Item to VariantCase for stock tracking)
# =============================================================================


class ItemVariant(models.Model):
    """
    Links an InventoryItem to a VariantCase.
    Each ItemVariant is a separate SKU with its own stock tracking.
    """

    base_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="variants"
    )
    variant_case = models.ForeignKey(
        VariantCase,
        on_delete=models.PROTECT,
        related_name="item_variants",
        null=True,  # Temporary for migration - will be made required after data migration
        blank=True
    )

    # Auto-generated code: ITEM-CODE-CASE-CODE
    code = models.CharField(max_length=100, unique=True)

    # Optional: Customer for CLIENT ownership variants
    customer = models.ForeignKey(
        "sales.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="item_variants"
    )

    # Cost for this specific variant
    standard_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    last_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    # Legacy references
    legacy_mat_no = models.CharField(max_length=50, blank=True, help_text="Legacy MAT number")
    erp_item_no = models.CharField(max_length=50, blank=True, help_text="ERP Item number")

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "item_variants"
        ordering = ["base_item", "variant_case"]
        unique_together = ["base_item", "variant_case", "customer"]
        verbose_name = "Item Variant"
        verbose_name_plural = "Item Variants"

    def __str__(self):
        return f"{self.code} ({self.variant_case.name})"

    @property
    def name(self):
        """Generate variant name from base item and case."""
        return f"{self.base_item.name} - {self.variant_case.name}"

    @property
    def total_stock(self):
        """Total stock for this variant across all locations."""
        return self.stock_records.aggregate(total=models.Sum("quantity_on_hand"))["total"] or 0

    def save(self, *args, **kwargs):
        # Auto-generate code if not set
        if not self.code:
            parts = [self.base_item.code, self.variant_case.code]
            if self.customer:
                parts.append(self.customer.code[:6] if hasattr(self.customer, 'code') else "CLI")
            self.code = "-".join(parts)

        # Set has_variants on base item
        if not self.base_item.has_variants:
            self.base_item.has_variants = True
            self.base_item.save(update_fields=["has_variants"])

        super().save(*args, **kwargs)


class InventoryLocation(models.Model):
    """
    🟢 P1: Storage locations within warehouses.

    Enhanced with location_type and party for Phase 0 architecture:
    - location_type: Categorizes location function (WAREHOUSE, QUARANTINE, RIG, etc.)
    - party: Owner/responsible party for this location (for external locations)
    """

    warehouse = models.ForeignKey("sales.Warehouse", on_delete=models.CASCADE, related_name="locations")
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=100)

    # Phase 0: Location categorization
    location_type = models.ForeignKey(
        LocationType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="locations",
        help_text="Location type (WAREHOUSE, QUARANTINE, RIG, etc.)"
    )

    # Phase 0: Owner/responsible party (for external or client locations)
    party = models.ForeignKey(
        Party,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="locations",
        help_text="Owner/responsible party for this location"
    )

    # Location path (e.g., Aisle-Rack-Shelf-Bin)
    aisle = models.CharField(max_length=20, blank=True)
    rack = models.CharField(max_length=20, blank=True)
    shelf = models.CharField(max_length=20, blank=True)
    bin = models.CharField(max_length=20, blank=True)

    # Location flags
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Default receiving location for warehouse")
    allows_negative = models.BooleanField(default=False, help_text="Allow negative stock (for transit locations)")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = "inventory_locations"
        ordering = ["warehouse", "code"]
        unique_together = ["warehouse", "code"]
        verbose_name = "Inventory Location"
        verbose_name_plural = "Inventory Locations"
        indexes = [
            models.Index(fields=["location_type"]),
            models.Index(fields=["party"]),
        ]

    def __str__(self):
        return f"{self.warehouse.code}/{self.code}"

    @property
    def full_path(self):
        """Return the full location path."""
        parts = [self.warehouse.code, self.code]
        if self.aisle:
            parts.append(self.aisle)
        if self.rack:
            parts.append(self.rack)
        if self.shelf:
            parts.append(self.shelf)
        if self.bin:
            parts.append(self.bin)
        return "/".join(parts)

    @property
    def default_quality_status(self):
        """Get default quality status from location type."""
        if self.location_type and self.location_type.default_quality_status:
            return self.location_type.default_quality_status
        return None


class InventoryStock(models.Model):
    """
    Stock levels by location.

    LEDGER-BASED ARCHITECTURE:
    - quantity_on_hand is a CACHED value for performance
    - The source of truth is InventoryTransaction ledger
    - Use recalculate_from_ledger() to sync with transactions
    - All stock changes should go through InventoryTransaction
    """

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="stock_records")
    location = models.ForeignKey(InventoryLocation, on_delete=models.CASCADE, related_name="stock_records")

    # Cached quantities (source of truth is transaction ledger)
    quantity_on_hand = models.DecimalField(max_digits=15, decimal_places=3, default=0, help_text="Cached - recalculate from ledger")
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

    def recalculate_from_ledger(self):
        """
        Recalculate quantity_on_hand from transaction ledger.
        This is the source of truth for inventory.
        """
        from django.db.models import Sum, Case, When, F, DecimalField

        # Get all transactions for this item/location
        transactions = InventoryTransaction.objects.filter(item=self.item)

        # Inbound: to_location matches
        inbound = transactions.filter(to_location=self.location).aggregate(
            total=Sum('quantity')
        )['total'] or 0

        # Outbound: from_location matches
        outbound = transactions.filter(from_location=self.location).aggregate(
            total=Sum('quantity')
        )['total'] or 0

        self.quantity_on_hand = inbound - outbound
        self.quantity_available = float(self.quantity_on_hand) - float(self.quantity_reserved)
        self.save(update_fields=['quantity_on_hand', 'quantity_available'])
        return self.quantity_on_hand

    @classmethod
    def recalculate_all(cls):
        """Recalculate all stock records from ledger."""
        for stock in cls.objects.all():
            stock.recalculate_from_ledger()


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
    Lot/batch tracking for inventory items with full ownership & quality tracking.

    Phase 1 Enhancement: Added condition, quality status, owner, and ownership type
    to enable complete lifecycle tracking of lot-controlled materials.

    Key capabilities:
    - Full traceability of materials used in repairs
    - Ownership tracking (who owns the lot)
    - Quality gate workflow (quarantine → released/blocked)
    - Condition tracking (new, used, refurbished, etc.)
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

    # Phase 1: Condition and Quality Status
    condition = models.ForeignKey(
        ConditionType, on_delete=models.PROTECT, null=True, blank=True,
        related_name="lots",
        help_text="Physical condition of the lot (NEW, USED, REFURB, etc.)"
    )
    quality_status = models.ForeignKey(
        QualityStatus, on_delete=models.PROTECT, null=True, blank=True,
        related_name="lots",
        help_text="QC status - gates what can be done with the lot"
    )

    # Phase 1: Ownership Tracking
    owner_party = models.ForeignKey(
        Party, on_delete=models.PROTECT, null=True, blank=True,
        related_name="owned_lots",
        help_text="Who owns this lot (Party - could be ARDT, customer, or vendor)"
    )
    ownership_type = models.ForeignKey(
        OwnershipType, on_delete=models.PROTECT, null=True, blank=True,
        related_name="lots",
        help_text="Ownership relationship type (OWNED, CLIENT, CONSIGNMENT, etc.)"
    )

    # Status (legacy - being replaced by quality_status workflow)
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
# NEW ARCHITECTURE: Item Planning (Per Warehouse)
# =============================================================================


class ItemPlanning(models.Model):
    """
    Planning parameters per item per warehouse/site.
    Min/max/reorder levels vary by location.
    """

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="planning_records"
    )
    warehouse = models.ForeignKey(
        "sales.Warehouse",
        on_delete=models.CASCADE,
        related_name="item_planning_records"
    )

    # Planning parameters
    min_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    max_stock = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    reorder_point = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    safety_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    # Default storage location in this warehouse
    default_bin = models.ForeignKey(
        InventoryLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_items"
    )

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "item_planning"
        unique_together = ["item", "warehouse"]
        ordering = ["item", "warehouse"]
        verbose_name = "Item Planning"
        verbose_name_plural = "Item Planning Records"

    def __str__(self):
        return f"{self.item.code} @ {self.warehouse.code}"


# =============================================================================
# NEW ARCHITECTURE: Item Supplier (Many-to-Many)
# =============================================================================


class ItemSupplier(models.Model):
    """
    Many-to-many relationship between items and suppliers.
    Stores supplier-specific pricing, lead times, and part numbers.
    """

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="supplier_records"
    )
    supplier = models.ForeignKey(
        "supplychain.Supplier",
        on_delete=models.CASCADE,
        related_name="item_records"
    )

    # Supplier's part number for this item
    supplier_part_number = models.CharField(max_length=100, blank=True)

    # Pricing
    unit_price = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    currency = models.CharField(max_length=3, default="SAR")
    price_valid_from = models.DateField(null=True, blank=True)
    price_valid_to = models.DateField(null=True, blank=True)

    # Ordering
    lead_time_days = models.IntegerField(default=0)
    min_order_qty = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    order_multiple = models.DecimalField(max_digits=10, decimal_places=3, default=1)

    # Priority (1 = preferred supplier)
    priority_rank = models.IntegerField(default=1)
    is_preferred = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "item_suppliers"
        unique_together = ["item", "supplier"]
        ordering = ["item", "priority_rank"]
        verbose_name = "Item Supplier"
        verbose_name_plural = "Item Suppliers"

    def __str__(self):
        return f"{self.item.code} - {self.supplier.name}"


# =============================================================================
# NEW ARCHITECTURE: Item Identifier (Multiple Barcodes)
# =============================================================================


class ItemIdentifier(models.Model):
    """
    Multiple identifiers/barcodes per item.
    Supports different barcode types at different packaging levels.
    """

    class IdentifierType(models.TextChoices):
        EAN13 = "EAN13", "EAN-13 (Unit)"
        EAN14 = "EAN14", "EAN-14 (Case)"
        UPC = "UPC", "UPC-A"
        ITF14 = "ITF14", "ITF-14 (Carton)"
        QR = "QR", "QR Code"
        DATAMATRIX = "DATAMATRIX", "Data Matrix"
        CODE128 = "CODE128", "Code 128"
        CODE39 = "CODE39", "Code 39"
        GS1 = "GS1", "GS1-128"
        INTERNAL = "INTERNAL", "Internal Code"
        SSCC = "SSCC", "SSCC-18 (Pallet)"

    class PackLevel(models.TextChoices):
        UNIT = "UNIT", "Unit/Each"
        INNER = "INNER", "Inner Pack"
        CASE = "CASE", "Case/Box"
        CARTON = "CARTON", "Carton"
        PALLET = "PALLET", "Pallet"

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="identifiers"
    )

    identifier_type = models.CharField(
        max_length=20,
        choices=IdentifierType.choices,
        default=IdentifierType.INTERNAL
    )
    value = models.CharField(max_length=100, help_text="The barcode/identifier value")
    pack_level = models.CharField(
        max_length=20,
        choices=PackLevel.choices,
        default=PackLevel.UNIT
    )

    # Quantity at this pack level
    qty_per_pack = models.IntegerField(default=1, help_text="Units per pack at this level")

    is_primary = models.BooleanField(default=False, help_text="Primary identifier for scanning")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "item_identifiers"
        unique_together = ["item", "identifier_type", "pack_level"]
        ordering = ["item", "pack_level", "identifier_type"]
        verbose_name = "Item Identifier"
        verbose_name_plural = "Item Identifiers"
        indexes = [
            models.Index(fields=["value"]),
        ]

    def __str__(self):
        return f"{self.item.code} - {self.identifier_type} ({self.pack_level})"


# =============================================================================
# SPECIALIZED SPEC TABLES (For Heavy/Critical Domains)
# =============================================================================


class ItemCutterSpec(models.Model):
    """
    Specialized specification table for PDC Cutters.
    Strong validation and better reporting for this critical domain.
    Use Attributes for most categories, but cutters need dedicated specs.
    """

    class Grade(models.TextChoices):
        PREMIUM = "PREMIUM", "Premium"
        STANDARD = "STANDARD", "Standard"
        ECONOMY = "ECONOMY", "Economy"

    class ChamferType(models.TextChoices):
        NONE = "NONE", "No Chamfer"
        SINGLE = "SINGLE", "Single Chamfer"
        DOUBLE = "DOUBLE", "Double Chamfer"
        MULTI = "MULTI", "Multi-Chamfer"

    item = models.OneToOneField(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="cutter_spec",
        primary_key=True
    )

    # Size specs
    cutter_size = models.DecimalField(
        max_digits=6, decimal_places=3,
        help_text="Cutter diameter in mm"
    )
    thickness = models.DecimalField(
        max_digits=6, decimal_places=3,
        null=True, blank=True,
        help_text="Cutter thickness in mm"
    )
    diamond_table_thickness = models.DecimalField(
        max_digits=6, decimal_places=3,
        null=True, blank=True,
        help_text="Diamond table thickness in mm"
    )

    # Material/Grade
    grade = models.CharField(max_length=20, choices=Grade.choices, default=Grade.STANDARD)
    substrate_material = models.CharField(max_length=50, blank=True, help_text="e.g., Tungsten Carbide")

    # Chamfer specs
    chamfer_type = models.CharField(max_length=20, choices=ChamferType.choices, default=ChamferType.NONE)
    chamfer_angle = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    chamfer_size = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)

    # Braze specs
    braze_temp_min = models.IntegerField(null=True, blank=True, help_text="Min braze temp °C")
    braze_temp_max = models.IntegerField(null=True, blank=True, help_text="Max braze temp °C")

    # Performance
    impact_resistance = models.CharField(max_length=20, blank=True)
    abrasion_resistance = models.CharField(max_length=20, blank=True)
    thermal_stability_temp = models.IntegerField(null=True, blank=True, help_text="Max thermal stability °C")

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "item_cutter_specs"
        verbose_name = "Cutter Specification"
        verbose_name_plural = "Cutter Specifications"

    def __str__(self):
        return f"{self.item.code} - {self.cutter_size}mm {self.grade}"


class ItemBitSpec(models.Model):
    """
    Specialized specification table for Drill Bit designs/SKUs.
    Links inventory items that are bit designs to their technical specs.
    Use this for the SKU/design level, not individual serial numbers.
    """

    class BitType(models.TextChoices):
        PDC = "PDC", "PDC (Fixed Cutter)"
        ROLLER_CONE = "RC", "Roller Cone"
        HYBRID = "HYBRID", "Hybrid"
        DIAMOND = "DIAMOND", "Diamond Impregnated"

    item = models.OneToOneField(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="bit_spec",
        primary_key=True
    )

    # Bit identification
    bit_type = models.CharField(max_length=20, choices=BitType.choices, default=BitType.PDC)
    iadc_code = models.CharField(max_length=10, blank=True, help_text="IADC classification code")

    # Size
    bit_size = models.DecimalField(
        max_digits=6, decimal_places=3,
        help_text="Bit diameter in inches"
    )

    # Connection
    connection_type = models.CharField(max_length=50, blank=True, help_text="e.g., API REG, IF")
    connection_size = models.CharField(max_length=20, blank=True, help_text="e.g., 4-1/2 IF")

    # PDC specific
    blade_count = models.IntegerField(null=True, blank=True)
    cutter_count = models.IntegerField(null=True, blank=True)
    cutter_size = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, help_text="Primary cutter size mm")

    # Nozzle configuration
    nozzle_count = models.IntegerField(null=True, blank=True)
    tfa_range_min = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, help_text="Min TFA sq.in")
    tfa_range_max = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, help_text="Max TFA sq.in")

    # Operating parameters
    weight_on_bit_min = models.IntegerField(null=True, blank=True, help_text="Min WOB (klbs)")
    weight_on_bit_max = models.IntegerField(null=True, blank=True, help_text="Max WOB (klbs)")
    rpm_min = models.IntegerField(null=True, blank=True)
    rpm_max = models.IntegerField(null=True, blank=True)

    # Application
    formation_hardness = models.CharField(max_length=50, blank=True, help_text="Soft/Medium/Hard/Very Hard")
    application = models.CharField(max_length=100, blank=True, help_text="e.g., Curve Drilling, Vertical")

    # Design details
    gauge_protection = models.CharField(max_length=50, blank=True)
    body_material = models.CharField(max_length=50, blank=True, help_text="Steel/Matrix")

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "item_bit_specs"
        verbose_name = "Bit Specification"
        verbose_name_plural = "Bit Specifications"

    def __str__(self):
        return f"{self.item.code} - {self.bit_size}\" {self.bit_type}"
