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

    UOM Categories:
    - SI Base Units: M, KG, L, EA (standard reference)
    - Conversion Units: Fixed conversion to SI base (IN→M, LB→KG)
    - Packaging Units: Variable conversion per item (ROLL, CARTON, DRUM)
    """

    class UnitType(models.TextChoices):
        # Core measurements
        QUANTITY = "QUANTITY", "Quantity (Count)"
        LENGTH = "LENGTH", "Length"
        WEIGHT = "WEIGHT", "Weight/Mass"
        VOLUME = "VOLUME", "Volume"
        AREA = "AREA", "Area"
        TIME = "TIME", "Time"
        # Mechanical
        PRESSURE = "PRESSURE", "Pressure"
        TEMPERATURE = "TEMPERATURE", "Temperature"
        ROTATIONAL_SPEED = "ROTATIONAL_SPEED", "Rotational Speed"
        TORQUE = "TORQUE", "Torque"
        POWER = "POWER", "Power"
        FORCE = "FORCE", "Force"
        ENERGY = "ENERGY", "Energy"
        # Electrical
        VOLTAGE = "VOLTAGE", "Voltage"
        CURRENT = "CURRENT", "Current"
        RESISTANCE = "RESISTANCE", "Resistance"
        FREQUENCY = "FREQUENCY", "Frequency"
        # Flow & Speed
        FLOW_RATE = "FLOW_RATE", "Flow Rate"
        SPEED = "SPEED", "Speed"
        # Material Properties
        HARDNESS = "HARDNESS", "Hardness"
        STRESS = "STRESS", "Stress/Strength"
        DENSITY = "DENSITY", "Density"
        VISCOSITY = "VISCOSITY", "Viscosity"
        # Ratios & Concentrations
        RATIO = "RATIO", "Ratio/Percentage"
        CONCENTRATION = "CONCENTRATION", "Concentration"
        # Angular
        ANGLE = "ANGLE", "Angle"
        # Specifications
        THREAD_SPEC = "THREAD_SPEC", "Thread Specification"
        WIRE_SPEC = "WIRE_SPEC", "Wire Specification"
        SURFACE_FINISH = "SURFACE_FINISH", "Surface Finish"
        ABRASIVE_SPEC = "ABRASIVE_SPEC", "Abrasive Specification"
        PARTICLE_SIZE = "PARTICLE_SIZE", "Particle Size"
        # Environmental
        CHEMICAL = "CHEMICAL", "Chemical Property"
        SOUND = "SOUND", "Sound/Noise"
        ILLUMINATION = "ILLUMINATION", "Illumination"
        LUMINOUS_FLUX = "LUMINOUS_FLUX", "Luminous Flux"
        # Packaging
        PACKAGING = "PACKAGING", "Packaging"
        # Other
        OTHER = "OTHER", "Other"

    code = models.CharField(max_length=10, unique=True, help_text="Short code (EA, KG, M, etc.)")
    name = models.CharField(max_length=50, help_text="Full name (Each, Kilogram, Meter)")
    unit_type = models.CharField(max_length=20, choices=UnitType.choices, default=UnitType.QUANTITY)
    symbol = models.CharField(max_length=10, blank=True, help_text="Symbol for display (kg, m, L)")

    # SI Base unit flag
    is_si_base = models.BooleanField(
        default=False,
        help_text="Is this an SI standard base unit? (M, KG, L, EA)"
    )

    # Packaging unit flag (requires item-level conversion)
    is_packaging = models.BooleanField(
        default=False,
        help_text="Is this a packaging unit with variable conversion per item? (ROLL, CARTON, DRUM)"
    )

    # Conversion to base unit (for fixed conversion units like IN→M)
    base_unit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="derived_units",
        help_text="Base unit for conversion (for non-packaging units)"
    )
    conversion_factor = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=1,
        help_text="Multiply by this to convert to base unit (for non-packaging units)"
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

    def convert_to_base(self, quantity):
        """Convert quantity to SI base unit (for fixed conversion units)."""
        from decimal import Decimal
        if self.is_si_base:
            return Decimal(str(quantity))
        if self.is_packaging:
            raise ValueError("Packaging units require item-specific conversion. Use ItemUOMConversion.")
        return Decimal(str(quantity)) * self.conversion_factor

    def convert_from_base(self, quantity):
        """Convert quantity from base unit to this unit."""
        from decimal import Decimal
        if self.is_si_base or self.conversion_factor == 0:
            return Decimal(str(quantity))
        if self.is_packaging:
            raise ValueError("Packaging units require item-specific conversion.")
        return Decimal(str(quantity)) / self.conversion_factor

    def convert_to(self, quantity, target_unit):
        """
        Convert quantity from this unit to target unit.
        Both units must have the same base unit (same unit_type).

        Example:
            inches = UnitOfMeasure.objects.get(code='IN')
            feet = UnitOfMeasure.objects.get(code='FT')
            result = inches.convert_to(12, feet)  # Returns 1.0
        """
        from decimal import Decimal

        if self.is_packaging or target_unit.is_packaging:
            raise ValueError("Packaging units require item-specific conversion.")

        # Same unit - no conversion needed
        if self.pk == target_unit.pk:
            return Decimal(str(quantity))

        # Get base units
        self_base = self.base_unit or self
        target_base = target_unit.base_unit or target_unit

        # Must have same base unit
        if self_base.pk != target_base.pk:
            raise ValueError(
                f"Cannot convert between {self.code} and {target_unit.code}: "
                f"different base units ({self_base.code} vs {target_base.code})"
            )

        # Convert: source -> base -> target
        base_quantity = self.convert_to_base(quantity)
        return target_unit.convert_from_base(base_quantity)

    def get_compatible_units(self):
        """Get all units that can be converted to/from this unit."""
        base = self.base_unit or self
        return UnitOfMeasure.objects.filter(
            models.Q(pk=base.pk) | models.Q(base_unit=base)
        ).exclude(is_packaging=True).order_by('code')

    def format_value(self, quantity, precision=2):
        """Format a quantity with this unit's symbol."""
        from decimal import Decimal
        val = Decimal(str(quantity))
        symbol = self.symbol or self.code
        return f"{val:.{precision}f} {symbol}"

    @classmethod
    def get_base_unit_for_type(cls, unit_type):
        """Get the SI base unit for a given unit type."""
        return cls.objects.filter(
            unit_type=unit_type,
            is_si_base=True
        ).first()


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

    # Advanced name template with conditional logic
    name_template_config = models.JSONField(
        null=True,
        blank=True,
        help_text='''
        Structured name template with conditional logic. Format:
        {
            "parts": [
                {"type": "attr", "code": "material"},
                {"type": "text", "value": " Cutter "},
                {"type": "conditional", "if": {"attr": "grade", "op": "not_empty"}, "then": {"type": "attr", "code": "grade"}}
            ]
        }
        '''
    )

    # Default values for items in this category (auto-fill on item creation)
    class Currency(models.TextChoices):
        SAR = "SAR", "SAR (Saudi Riyal)"
        USD = "USD", "USD (US Dollar)"

    default_currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.SAR,
        help_text="Default currency for items in this category"
    )
    default_min_stock = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Default minimum stock level for items in this category"
    )
    default_reorder_qty = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Default reorder quantity for items in this category"
    )

    # Packaging defaults
    default_purchase_uom = models.ForeignKey(
        "UnitOfMeasure",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="category_purchase_defaults",
        help_text="Default 'Buy As' unit for items in this category"
    )
    default_release_uom = models.ForeignKey(
        "UnitOfMeasure",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="category_release_defaults",
        help_text="Default 'Issue As' unit for items in this category"
    )
    default_conversion_factor = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1,
        help_text="Default qty per package (Buy→Issue conversion)"
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

    class DataType(models.TextChoices):
        TEXT = "text", "Text"
        NUMBER = "number", "Number"
        DECIMAL = "decimal", "Decimal"
        BOOLEAN = "boolean", "Yes/No"
        DATE = "date", "Date"
        SELECT = "select", "Select (Dropdown)"
        ENUM = "enum", "Enum"

    class Classification(models.TextChoices):
        PHYS = "PHYS", "Physical Dimensions"
        TECH = "TECH", "Technical Specifications"
        CONN = "CONN", "Connection & Thread"
        MATL = "MATL", "Material & Composition"
        IADC = "IADC", "IADC & Drilling Specifications"
        OPER = "OPER", "Operational Parameters"
        IDEN = "IDEN", "Identification & Commercial"
        QUAL = "QUAL", "Quality & Compliance"
        STOR = "STOR", "Storage & Logistics"
        SAFE = "SAFE", "Safety & PPE"
        TOOL = "TOOL", "Tools & Equipment"
        CONS = "CONS", "Consumables"
        ELEC = "ELEC", "Electrical Components"
        FAST = "FAST", "Fasteners"
        GEN = "GEN", "General Attributes"

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique code (e.g., size, color, material)"
    )
    name = models.CharField(max_length=100, help_text="Display name (e.g., Size, Color, Material)")
    description = models.TextField(blank=True, help_text="Optional description of this attribute")

    # Classification for organizing attributes
    classification = models.CharField(
        max_length=10,
        choices=Classification.choices,
        default=Classification.GEN,
        help_text="Attribute classification category"
    )

    # Suggested data type (used as default when adding to CategoryAttribute)
    data_type = models.CharField(
        max_length=20,
        choices=DataType.choices,
        default=DataType.TEXT,
        help_text="Suggested data type for this attribute"
    )

    # Notes for usage guidance
    notes = models.TextField(blank=True, help_text="Usage notes or guidance for this attribute")

    is_active = models.BooleanField(default=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attributes"
        ordering = ["classification", "name"]
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
    - For Clothing: Size is TEXT type with options [S, M, L, XL] → dropdown
    - For Tools: Size is NUMBER type with unit "mm" and options [6, 8, 10, 12]
    - For Shelf Life: NUMBER type with unit "months" and options [6, 12, 18, 24]
    """

    class AttributeType(models.TextChoices):
        TEXT = "TEXT", "Text"           # With options = dropdown, without = free text
        NUMBER = "NUMBER", "Number"     # With options = dropdown + custom, unit/min/max
        BOOLEAN = "BOOLEAN", "Yes/No"
        DATE = "DATE", "Date"

    class NumberType(models.TextChoices):
        INTEGER = "INTEGER", "Integer (whole numbers)"
        DECIMAL = "DECIMAL", "Decimal (with decimals)"

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

    # ==========================================================================
    # NUMBER type configuration
    # ==========================================================================
    number_type = models.CharField(
        max_length=20,
        choices=NumberType.choices,
        default=NumberType.DECIMAL,
        help_text="For NUMBER: Integer (whole numbers) or Decimal"
    )
    allow_negative = models.BooleanField(
        default=True,
        help_text="For NUMBER: Allow negative values?"
    )
    decimal_places = models.PositiveSmallIntegerField(
        default=2,
        help_text="For DECIMAL: Number of decimal places (0-10)"
    )
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

    # ==========================================================================
    # TEXT type configuration
    # ==========================================================================
    max_length = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="For TEXT: Maximum character length"
    )
    is_multiline = models.BooleanField(
        default=False,
        help_text="For TEXT: Allow multiple lines (textarea vs input)"
    )

    # ==========================================================================
    # Common configuration (all types)
    # ==========================================================================
    placeholder = models.CharField(
        max_length=200,
        blank=True,
        help_text="Placeholder/hint text shown in input field"
    )
    field_help_text = models.TextField(
        blank=True,
        help_text="Help text/description shown below the field"
    )

    # Options for dropdown - works with TEXT and NUMBER
    options = models.JSONField(
        null=True,
        blank=True,
        help_text='Dropdown options: ["Option1", "Option2"]. TEXT with options = dropdown. NUMBER with options = common values.'
    )

    # Default value for new items
    default_value = models.CharField(
        max_length=500,
        blank=True,
        help_text="Default value when creating new items"
    )

    # Conditional rules for computed/dependent values
    conditional_rules = models.JSONField(
        null=True,
        blank=True,
        help_text='''
        Rules to auto-set value based on other attributes. Format:
        {
            "rules": [
                {
                    "conditions": [
                        {"attr": "cutter_shape", "op": "in", "value": ["Machete", "Chisel"]},
                        {"attr": "size", "op": "gt", "value": 16}
                    ],
                    "logic": "AND",
                    "result": "0",
                    "message": "Non-rotatable due to Machete/Chisel shape"
                }
            ],
            "locked": true
        }
        Operators: eq, ne, in, nin, contains, gt, gte, lt, lte, empty, not_empty
        '''
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

    # Blocking controls
    is_blocked = models.BooleanField(default=False, help_text="Master block - prevents all transactions")
    blocked_for_issue = models.BooleanField(default=False, help_text="Block from stock issues/sales")
    blocked_for_receipt = models.BooleanField(default=False, help_text="Block from receiving/purchase")
    blocked_for_production = models.BooleanField(default=False, help_text="Block from BOM/manufacturing")
    blocked_for_counting = models.BooleanField(default=False, help_text="Block from inventory counts")
    block_reason = models.CharField(max_length=255, blank=True, help_text="Reason for blocking")

    # Shelf life (CORE - for expiry tracking)
    shelf_life_days = models.IntegerField(null=True, blank=True, help_text="Shelf life in days")

    # Image
    image = models.ImageField(upload_to="inventory/", null=True, blank=True)

    # Packaging: Purchase vs Release UOM
    purchase_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items_purchase_uom",
        help_text="Unit for purchasing (e.g., CARTON, BOX)"
    )
    release_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items_release_uom",
        help_text="Unit for issuing/releasing (e.g., EACH, PC)"
    )
    purchase_to_release_factor = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="1 purchase UOM = X release UOM (e.g., 1 CARTON = 100 EA)"
    )

    # In-Floor Tracking
    issued_to_floor = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        default=0,
        help_text="Quantity currently issued to production floor"
    )
    floor_location = models.CharField(
        max_length=100,
        blank=True,
        help_text="Current location on production floor (e.g., Machine A, Workstation 5)"
    )
    estimated_consumption_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Estimated daily consumption rate for forecasting"
    )
    floor_reorder_point = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="When floor stock drops below this, trigger replenishment"
    )

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
    def cost_per_base_unit(self):
        """
        Calculate cost per base unit for comparison between items with different packaging.
        If item is purchased in cartons but released by pieces, shows cost per piece.
        """
        from decimal import Decimal
        if self.standard_cost and self.purchase_to_release_factor and self.purchase_to_release_factor > 0:
            return Decimal(str(self.standard_cost)) / Decimal(str(self.purchase_to_release_factor))
        return self.standard_cost or Decimal('0')

    @property
    def alternate_currency_cost(self):
        """
        Calculate cost in alternate currency using fixed exchange rate.
        Default: SAR to USD (3.75 SAR = 1 USD)
        """
        from decimal import Decimal
        from django.conf import settings as django_settings
        exchange_rate = getattr(django_settings, 'SAR_TO_USD_RATE', Decimal('3.75'))
        if self.currency == 'SAR' and self.standard_cost:
            return Decimal(str(self.standard_cost)) / exchange_rate
        elif self.currency == 'USD' and self.standard_cost:
            return Decimal(str(self.standard_cost)) * exchange_rate
        return self.standard_cost or Decimal('0')

    @property
    def days_until_floor_reorder(self):
        """Estimate days until floor stock needs replenishment."""
        if self.estimated_consumption_per_day and self.estimated_consumption_per_day > 0:
            available = self.issued_to_floor - (self.floor_reorder_point or 0)
            if available > 0:
                from decimal import Decimal
                return int(Decimal(str(available)) / Decimal(str(self.estimated_consumption_per_day)))
        return None

    def get_related_items(self):
        """Get all related items (both directions)."""
        from itertools import chain
        outgoing = self.related_to.filter(is_active=True).select_related('to_item')
        incoming = self.related_from.filter(is_active=True).select_related('from_item')
        return {
            'outgoing': list(outgoing),
            'incoming': list(incoming),
            'all': list(chain(
                [(r.to_item, r.status, r.get_status_display()) for r in outgoing],
                [(r.from_item, r.status, r.get_status_display()) for r in incoming]
            ))
        }

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


class ItemRelationship(models.Model):
    """
    Bidirectional relationships between inventory items.
    Used for similar items, replacements, alternatives, etc.

    Status options define the relationship type:
    - EQUAL: Items are equivalent/interchangeable
    - OBSOLETE: from_item is obsolete, use to_item instead
    - UNAVAILABLE: from_item temporarily unavailable, use to_item as alternative
    - BLOCKED: from_item is blocked, use to_item instead
    - USE_UNTIL_CONSUME: from_item should be used until consumed, then switch to to_item
    """

    class RelationshipStatus(models.TextChoices):
        EQUAL = "EQUAL", "Equal/Interchangeable"
        OBSOLETE = "OBSOLETE", "Obsolete (use alternative)"
        UNAVAILABLE = "UNAVAILABLE", "Temporarily Unavailable"
        BLOCKED = "BLOCKED", "Blocked (use alternative)"
        USE_UNTIL_CONSUME = "USE_UNTIL_CONSUME", "Use Until Consumed"

    from_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="related_to"
    )
    to_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="related_from"
    )
    status = models.CharField(
        max_length=20,
        choices=RelationshipStatus.choices,
        default=RelationshipStatus.EQUAL,
        help_text="Relationship type/status"
    )
    notes = models.TextField(blank=True, help_text="Additional notes about the relationship")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_item_relationships"
    )

    class Meta:
        db_table = "item_relationships"
        unique_together = ["from_item", "to_item"]
        verbose_name = "Item Relationship"
        verbose_name_plural = "Item Relationships"
        ordering = ["from_item", "status"]

    def __str__(self):
        return f"{self.from_item.code} → {self.to_item.code} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        """Create bidirectional relationship automatically."""
        super().save(*args, **kwargs)

        # Check if reverse relationship exists
        reverse_exists = ItemRelationship.objects.filter(
            from_item=self.to_item,
            to_item=self.from_item
        ).exists()

        if not reverse_exists and self.from_item != self.to_item:
            # Create reverse relationship with appropriate status
            reverse_status = self.status
            if self.status == self.RelationshipStatus.OBSOLETE:
                # Reverse of "obsolete" means "is replacement for"
                reverse_status = self.RelationshipStatus.EQUAL
            elif self.status == self.RelationshipStatus.USE_UNTIL_CONSUME:
                # Reverse means "replaces after consumed"
                reverse_status = self.RelationshipStatus.EQUAL

            ItemRelationship.objects.create(
                from_item=self.to_item,
                to_item=self.from_item,
                status=reverse_status,
                notes=f"Auto-created reverse of: {self.notes}" if self.notes else "Auto-created reverse relationship",
                is_active=self.is_active,
                created_by=self.created_by
            )


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
        """Return the appropriate value based on attribute type, formatted correctly."""
        attr_type = self.attribute.attribute_type
        if attr_type == CategoryAttribute.AttributeType.NUMBER:
            if self.number_value is None:
                return None
            # Format based on number_type (INTEGER vs DECIMAL)
            number_type = getattr(self.attribute, 'number_type', 'DECIMAL')
            if number_type == 'INTEGER':
                # Display as integer (no decimals)
                return int(self.number_value)
            else:
                # Display as decimal, removing trailing zeros
                from decimal import Decimal
                if isinstance(self.number_value, Decimal):
                    # Normalize to remove trailing zeros, but keep at least one decimal if needed
                    normalized = self.number_value.normalize()
                    # If it's a whole number, return as int
                    if normalized == normalized.to_integral_value():
                        return int(normalized)
                    return str(normalized)
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


class ItemUOMConversion(models.Model):
    """
    Item-specific UOM conversion for packaging units.

    Used when the conversion factor varies by item:
    - Roll of Tape A = 100 meters
    - Roll of Tape B = 50 meters
    - Carton of Screws = 24 each
    - Drum of Oil = 200 liters

    This allows each item to define its own pack sizes while
    still converting everything to SI base units for reporting.
    """

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="uom_conversions"
    )
    from_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name="item_conversions_from",
        help_text="Packaging/alternate unit (ROLL, CARTON, DRUM)"
    )
    to_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name="item_conversions_to",
        help_text="Base unit to convert to (M, KG, L, EA)"
    )
    conversion_factor = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        help_text="1 from_uom = X to_uom (e.g., 1 ROLL = 100 M)"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Default conversion for this item's packaging unit"
    )
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "item_uom_conversions"
        unique_together = ["item", "from_uom", "to_uom"]
        verbose_name = "Item UOM Conversion"
        verbose_name_plural = "Item UOM Conversions"
        ordering = ["item", "from_uom"]

    def __str__(self):
        return f"{self.item.code}: 1 {self.from_uom.code} = {self.conversion_factor} {self.to_uom.code}"

    def convert(self, quantity):
        """Convert quantity from packaging unit to base unit."""
        from decimal import Decimal
        return Decimal(str(quantity)) * self.conversion_factor

    def reverse_convert(self, quantity):
        """Convert quantity from base unit to packaging unit."""
        from decimal import Decimal
        return Decimal(str(quantity)) / self.conversion_factor


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

    # Auto-generated code: ITEM-CODE-CASE-CODE (blank allowed, generated in view)
    code = models.CharField(max_length=100, unique=True, blank=True)

    # Optional: Customer for CLIENT ownership variants
    customer = models.ForeignKey(
        "sales.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="item_variants"
    )

    # Account for CLIENT ownership variants (e.g., LSTK, Core Heads, Regional)
    class AccountType(models.TextChoices):
        LSTK = "LSTK", "LSTK"
        CORE_HEADS = "CORE_HEADS", "Core Heads"
        REGIONAL = "REGIONAL", "Regional"

    account = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        blank=True,
        help_text="Account type for CLIENT ownership variants"
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

    class BitCategory(models.TextChoices):
        """Category of drill bit design."""
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

    # Bit identification (field kept as bit_type for backward compatibility)
    bit_type = models.CharField(max_length=20, choices=BitCategory.choices, default=BitCategory.PDC)
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


# =============================================================================
# PHASE 2: STOCK LEDGER & BALANCE (Ledger-Based Inventory)
# =============================================================================

class StockLedger(models.Model):
    """
    Immutable stock ledger - the source of truth for all inventory quantities.

    Design Principles:
    - IMMUTABLE: Ledger entries are never updated or deleted (only reversed)
    - SINGLE-LOCATION: Each entry affects one location with signed qty_delta
    - IDEMPOTENT: reference_type + reference_id ensures no duplicate postings
    - COMPLETE: Captures WHO owns, WHAT relationship, WHERE, and quality state

    Stock balance is calculated by summing qty_delta grouped by dimensions.
    This is the foundation of double-entry inventory accounting.
    """

    class TransactionType(models.TextChoices):
        # Inbound
        RECEIPT = "RECEIPT", "Goods Receipt"
        RETURN_IN = "RETURN_IN", "Customer Return (Inbound)"
        TRANSFER_IN = "TRANSFER_IN", "Transfer In"
        ADJUSTMENT_IN = "ADJ_IN", "Adjustment (Increase)"

        # Outbound
        ISSUE = "ISSUE", "Goods Issue"
        RETURN_OUT = "RETURN_OUT", "Return to Vendor (Outbound)"
        TRANSFER_OUT = "TRANSFER_OUT", "Transfer Out"
        ADJUSTMENT_OUT = "ADJ_OUT", "Adjustment (Decrease)"
        SCRAP = "SCRAP", "Scrap/Disposal"
        CONSUMPTION = "CONSUMPTION", "WO Material Consumption"

        # Quality/Status changes (qty=0, but state changes)
        QC_RELEASE = "QC_RELEASE", "QC Release"
        QC_BLOCK = "QC_BLOCK", "QC Block"
        QC_QUARANTINE = "QC_QUARANTINE", "QC Quarantine"

        # Ownership changes (qty=0, ownership dimension changes)
        OWNERSHIP_CHANGE = "OWNER_CHG", "Ownership Change"

    # Unique entry identifier
    entry_number = models.CharField(
        max_length=50, unique=True,
        help_text="Auto-generated unique entry number (e.g., SL-2024-000001)"
    )
    entry_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When this ledger entry was created (immutable)"
    )
    transaction_date = models.DateField(
        help_text="Business date of the transaction"
    )
    transaction_type = models.CharField(
        max_length=20, choices=TransactionType.choices
    )

    # What item and how much (signed delta)
    item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT,
        related_name="ledger_entries",
        help_text="The inventory item affected"
    )
    qty_delta = models.DecimalField(
        max_digits=15, decimal_places=3,
        help_text="Signed quantity change (+ve = increase, -ve = decrease)"
    )
    uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT,
        related_name="ledger_entries",
        help_text="Unit of measure (should match item.base_uom)"
    )

    # Where (single location per entry)
    location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        related_name="ledger_entries",
        help_text="Location affected by this entry"
    )

    # Lot tracking (optional - for LOT/SERIAL/ASSET tracking)
    lot = models.ForeignKey(
        MaterialLot, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="ledger_entries",
        help_text="Lot reference (required if item.tracking_type in [LOT, SERIAL, ASSET])"
    )

    # Ownership dimensions
    owner_party = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        related_name="ledger_entries",
        help_text="Who owns this stock"
    )
    ownership_type = models.ForeignKey(
        OwnershipType, on_delete=models.PROTECT,
        related_name="ledger_entries",
        help_text="Type of ownership (OWNED, CLIENT, CONSIGNMENT, etc.)"
    )

    # Quality & Condition dimensions
    quality_status = models.ForeignKey(
        QualityStatus, on_delete=models.PROTECT,
        related_name="ledger_entries",
        help_text="Quality status at time of transaction"
    )
    condition = models.ForeignKey(
        ConditionType, on_delete=models.PROTECT,
        related_name="ledger_entries",
        help_text="Physical condition at time of transaction"
    )

    # Cost tracking
    unit_cost = models.DecimalField(
        max_digits=15, decimal_places=4, default=0,
        help_text="Unit cost at time of transaction"
    )
    total_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text="Total cost (qty_delta * unit_cost)"
    )
    currency = models.CharField(max_length=3, default="SAR")

    # Idempotent posting - ensures no duplicate entries
    reference_type = models.CharField(
        max_length=50,
        help_text="Source document type (e.g., 'GRN', 'ISSUE', 'TRANSFER', 'ADJUSTMENT')"
    )
    reference_id = models.CharField(
        max_length=100,
        help_text="Source document ID (e.g., 'GRN-2024-0001-LINE-1')"
    )

    # Optional source document FKs (for direct queries)
    # These are set based on reference_type
    grn_line = models.ForeignKey(
        "inventory.GRNLine", on_delete=models.PROTECT,
        null=True, blank=True, related_name="ledger_entries"
    )
    issue_line = models.ForeignKey(
        "inventory.StockIssueLine", on_delete=models.PROTECT,
        null=True, blank=True, related_name="ledger_entries"
    )
    transfer_line = models.ForeignKey(
        "inventory.StockTransferLine", on_delete=models.PROTECT,
        null=True, blank=True, related_name="ledger_entries"
    )
    adjustment_line = models.ForeignKey(
        "inventory.StockAdjustmentLine", on_delete=models.PROTECT,
        null=True, blank=True, related_name="ledger_entries"
    )

    # Reversal support
    is_reversal = models.BooleanField(
        default=False,
        help_text="Is this entry a reversal of another entry?"
    )
    reverses_entry = models.ForeignKey(
        "self", on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="reversed_by",
        help_text="The entry this reverses (if is_reversal=True)"
    )
    reversed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When this entry was reversed (if reversed)"
    )

    # Audit
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="ledger_entries_created"
    )

    class Meta:
        db_table = "stock_ledger"
        verbose_name = "Stock Ledger Entry"
        verbose_name_plural = "Stock Ledger Entries"
        ordering = ["-entry_date", "-id"]

        # Idempotent posting constraint
        constraints = [
            models.UniqueConstraint(
                fields=["reference_type", "reference_id"],
                name="unique_ledger_reference"
            )
        ]

        indexes = [
            models.Index(fields=["item", "location"]),
            models.Index(fields=["item", "owner_party"]),
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["transaction_type"]),
            models.Index(fields=["reference_type", "reference_id"]),
            models.Index(fields=["lot"]),
            models.Index(fields=["entry_number"]),
        ]

    def __str__(self):
        return f"{self.entry_number}: {self.item.code} {self.qty_delta:+} @ {self.location.code}"

    def save(self, *args, **kwargs):
        # Auto-generate entry number if not set
        if not self.entry_number:
            from django.utils import timezone
            year = timezone.now().year
            last_entry = StockLedger.objects.filter(
                entry_number__startswith=f"SL-{year}-"
            ).order_by("-entry_number").first()

            if last_entry:
                last_num = int(last_entry.entry_number.split("-")[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.entry_number = f"SL-{year}-{new_num:06d}"

        # Calculate total cost
        self.total_cost = self.qty_delta * self.unit_cost

        super().save(*args, **kwargs)


class StockBalance(models.Model):
    """
    Materialized stock balance - aggregated view of current stock levels.

    This table is a denormalized view calculated from StockLedger.
    It provides fast queries for current stock levels without aggregating
    the entire ledger each time.

    Key: item + location + lot + owner_party + ownership_type + quality_status + condition

    Balance Calculation:
    - qty_on_hand = SUM(ledger.qty_delta) for matching dimensions
    - Recalculated periodically or on-demand
    - Can be rebuilt entirely from ledger (ledger is source of truth)
    """

    # Unique combination of dimensions
    item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT,
        related_name="stock_balances"
    )
    location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        related_name="stock_balances"
    )
    lot = models.ForeignKey(
        MaterialLot, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="stock_balances",
        help_text="Null for non-lot-tracked items"
    )

    # Ownership dimensions
    owner_party = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        related_name="stock_balances"
    )
    ownership_type = models.ForeignKey(
        OwnershipType, on_delete=models.PROTECT,
        related_name="stock_balances"
    )

    # Quality & Condition dimensions
    quality_status = models.ForeignKey(
        QualityStatus, on_delete=models.PROTECT,
        related_name="stock_balances"
    )
    condition = models.ForeignKey(
        ConditionType, on_delete=models.PROTECT,
        related_name="stock_balances"
    )

    # Quantities
    qty_on_hand = models.DecimalField(
        max_digits=15, decimal_places=3, default=0,
        help_text="Current quantity on hand"
    )
    qty_reserved = models.DecimalField(
        max_digits=15, decimal_places=3, default=0,
        help_text="Quantity reserved/allocated"
    )
    qty_available = models.DecimalField(
        max_digits=15, decimal_places=3, default=0,
        help_text="Available = on_hand - reserved (denormalized for speed)"
    )

    # Valuation
    total_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text="Total value of stock at this balance"
    )
    avg_unit_cost = models.DecimalField(
        max_digits=15, decimal_places=4, default=0,
        help_text="Average unit cost (total_cost / qty_on_hand)"
    )

    # Tracking
    last_movement_date = models.DateTimeField(
        null=True, blank=True,
        help_text="Last ledger entry date affecting this balance"
    )
    last_recalc_date = models.DateTimeField(
        auto_now=True,
        help_text="When balance was last recalculated"
    )

    class Meta:
        db_table = "stock_balances"
        verbose_name = "Stock Balance"
        verbose_name_plural = "Stock Balances"

        # Unique constraint on all dimension columns
        # Note: lot can be null, so we need conditional unique constraints
        constraints = [
            # For lot-tracked items (lot is NOT NULL)
            models.UniqueConstraint(
                fields=["item", "location", "lot", "owner_party",
                        "ownership_type", "quality_status", "condition"],
                condition=models.Q(lot__isnull=False),
                name="unique_stock_balance_with_lot"
            ),
            # For non-lot-tracked items (lot IS NULL)
            models.UniqueConstraint(
                fields=["item", "location", "owner_party",
                        "ownership_type", "quality_status", "condition"],
                condition=models.Q(lot__isnull=True),
                name="unique_stock_balance_without_lot"
            ),
        ]

        indexes = [
            models.Index(fields=["item"]),
            models.Index(fields=["location"]),
            models.Index(fields=["item", "location"]),
            models.Index(fields=["owner_party"]),
            models.Index(fields=["quality_status"]),
            models.Index(fields=["qty_on_hand"]),
        ]

    def __str__(self):
        lot_str = f" Lot:{self.lot.lot_number}" if self.lot else ""
        return f"{self.item.code}@{self.location.code}{lot_str}: {self.qty_on_hand}"

    def save(self, *args, **kwargs):
        # Recalculate available quantity
        self.qty_available = self.qty_on_hand - self.qty_reserved

        # Recalculate average unit cost
        if self.qty_on_hand > 0:
            self.avg_unit_cost = self.total_cost / self.qty_on_hand
        else:
            self.avg_unit_cost = 0

        super().save(*args, **kwargs)

    @classmethod
    def recalculate_from_ledger(cls, item=None, location=None):
        """
        Recalculate stock balances from ledger entries.

        Can filter by item and/or location for targeted recalculation.
        This is the authoritative way to ensure balances match the ledger.
        """
        from django.db.models import Sum, Max
        from django.db.models.functions import Coalesce

        # Build filter
        ledger_filter = {}
        if item:
            ledger_filter["item"] = item
        if location:
            ledger_filter["location"] = location

        # Get all unique dimension combinations from ledger
        dimension_groups = StockLedger.objects.filter(
            **ledger_filter
        ).values(
            "item", "location", "lot", "owner_party",
            "ownership_type", "quality_status", "condition"
        ).annotate(
            total_qty=Coalesce(Sum("qty_delta"), 0),
            total_cost=Coalesce(Sum("total_cost"), 0),
            last_date=Max("entry_date")
        )

        updated_count = 0
        for group in dimension_groups:
            balance, created = cls.objects.update_or_create(
                item_id=group["item"],
                location_id=group["location"],
                lot_id=group["lot"],
                owner_party_id=group["owner_party"],
                ownership_type_id=group["ownership_type"],
                quality_status_id=group["quality_status"],
                condition_id=group["condition"],
                defaults={
                    "qty_on_hand": group["total_qty"],
                    "total_cost": group["total_cost"],
                    "last_movement_date": group["last_date"],
                }
            )
            updated_count += 1

        return updated_count


# =============================================================================
# PHASE 3: INVENTORY DOCUMENTS (Source Documents for Ledger)
# =============================================================================

class GoodsReceiptNote(models.Model):
    """
    Goods Receipt Note (GRN) - Inbound receiving document.

    Documents the receipt of goods into inventory, whether from:
    - Purchase Orders (vendor receipts)
    - Customer Returns
    - Internal Transfers
    - Opening Balance

    Each GRN line posts to the StockLedger when the GRN is confirmed.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_QC = "PENDING_QC", "Pending QC"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    class ReceiptType(models.TextChoices):
        PURCHASE = "PURCHASE", "Purchase Order Receipt"
        RETURN = "RETURN", "Customer Return"
        TRANSFER = "TRANSFER", "Transfer Receipt"
        OPENING = "OPENING", "Opening Balance"
        OTHER = "OTHER", "Other Receipt"

    # Document identification
    grn_number = models.CharField(
        max_length=50, unique=True,
        help_text="Auto-generated GRN number (e.g., GRN-2024-0001)"
    )
    receipt_type = models.CharField(
        max_length=20, choices=ReceiptType.choices, default=ReceiptType.PURCHASE
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    # Source reference
    purchase_order = models.ForeignKey(
        "supplychain.PurchaseOrder", on_delete=models.PROTECT,
        null=True, blank=True, related_name="grns",
        help_text="Source PO for purchase receipts"
    )
    source_reference = models.CharField(
        max_length=100, blank=True,
        help_text="External reference (e.g., vendor delivery note number)"
    )

    # Supplier/Source party
    supplier = models.ForeignKey(
        "supplychain.Supplier", on_delete=models.PROTECT,
        null=True, blank=True, related_name="grns"
    )

    # Receiving details
    warehouse = models.ForeignKey(
        "sales.Warehouse", on_delete=models.PROTECT,
        related_name="grns",
        help_text="Receiving warehouse"
    )
    receiving_location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        related_name="grns_received",
        help_text="Default receiving location (can be overridden per line)"
    )

    # Dates
    receipt_date = models.DateField(help_text="Date goods received")
    expected_date = models.DateField(null=True, blank=True)
    posted_date = models.DateTimeField(
        null=True, blank=True,
        help_text="When GRN was posted to ledger"
    )

    # Ownership at receipt
    owner_party = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        related_name="grns_received",
        help_text="Who will own the received goods"
    )
    ownership_type = models.ForeignKey(
        OwnershipType, on_delete=models.PROTECT,
        related_name="grns",
        help_text="Ownership type (OWNED, CONSIGNMENT, CLIENT, etc.)"
    )

    # Vendor (preferred over legacy Supplier)
    vendor = models.ForeignKey(
        "supplychain.Vendor", on_delete=models.PROTECT,
        null=True, blank=True, related_name="grns",
        help_text="Vendor for purchase receipts (preferred over supplier)"
    )

    # Quality control
    requires_qc = models.BooleanField(
        default=True,
        help_text="Does this receipt require QC inspection?"
    )
    qc_completed = models.BooleanField(default=False)
    qc_notes = models.TextField(blank=True)

    # QC Workflow Enhancement
    class QCStatus(models.TextChoices):
        NOT_REQUIRED = "NOT_REQUIRED", "QC Not Required"
        PENDING = "PENDING", "Pending Inspection"
        IN_PROGRESS = "IN_PROGRESS", "Inspection In Progress"
        PASSED = "PASSED", "QC Passed"
        FAILED = "FAILED", "QC Failed"
        PARTIAL = "PARTIAL", "Partially Passed"

    qc_status = models.CharField(
        max_length=20, choices=QCStatus.choices, default=QCStatus.PENDING
    )
    qc_inspection = models.ForeignKey(
        "compliance.QualityControl", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="grns",
        help_text="Link to QC inspection record"
    )
    qc_completed_at = models.DateTimeField(null=True, blank=True)
    qc_completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="grns_qc_completed"
    )

    # Posting
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="grns_posted"
    )

    # Variance tracking
    has_quantity_variance = models.BooleanField(
        default=False,
        help_text="True if any line exceeds tolerance"
    )
    variance_approved = models.BooleanField(default=False)
    variance_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="grns_variance_approved"
    )
    variance_approved_at = models.DateTimeField(null=True, blank=True)

    # Three-Way Matching (PO -> GRN -> Invoice)
    class MatchStatus(models.TextChoices):
        NOT_APPLICABLE = "NOT_APPLICABLE", "Not Applicable"
        PENDING = "PENDING", "Pending Match"
        MATCHED = "MATCHED", "Matched"
        EXCEPTION = "EXCEPTION", "Exception"
        RESOLVED = "RESOLVED", "Exception Resolved"

    invoice_match_status = models.CharField(
        max_length=20, choices=MatchStatus.choices,
        default=MatchStatus.NOT_APPLICABLE,
        help_text="Status of three-way match (PO-GRN-Invoice)"
    )
    vendor_invoice = models.ForeignKey(
        "supplychain.VendorInvoice", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="grns",
        help_text="Linked vendor invoice for three-way matching"
    )
    invoice_match = models.ForeignKey(
        "supplychain.InvoiceMatch", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="grns_matched",
        help_text="Link to the three-way match record"
    )

    # Audit
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="grns_created"
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name="grns_confirmed"
    )

    class Meta:
        db_table = "goods_receipt_notes"
        verbose_name = "Goods Receipt Note"
        verbose_name_plural = "Goods Receipt Notes"
        ordering = ["-receipt_date", "-grn_number"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["receipt_date"]),
            models.Index(fields=["supplier"]),
            models.Index(fields=["grn_number"]),
        ]

    def __str__(self):
        return f"{self.grn_number} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.grn_number:
            from django.utils import timezone
            year = timezone.now().year
            last_grn = GoodsReceiptNote.objects.filter(
                grn_number__startswith=f"GRN-{year}-"
            ).order_by("-grn_number").first()

            if last_grn:
                last_num = int(last_grn.grn_number.split("-")[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.grn_number = f"GRN-{year}-{new_num:04d}"

        super().save(*args, **kwargs)

    def calculate_variances(self):
        """
        Calculate and flag quantity variances on all lines.
        Returns True if any variance exceeds tolerance.
        """
        from decimal import Decimal
        has_variance = False

        for line in self.lines.all():
            if line.qty_expected > 0:
                variance = ((line.qty_received - line.qty_expected) / line.qty_expected) * 100
                line.variance_percent = abs(variance)

                if variance > 0:
                    line.variance_type = 'OVER'
                elif variance < 0:
                    line.variance_type = 'SHORT'
                else:
                    line.variance_type = 'NONE'

                # Get tolerance for this item
                tolerance = ReceiptTolerance.get_tolerance_for(
                    item=line.item,
                    category=line.item.category if line.item else None,
                    vendor=self.vendor
                )

                if tolerance:
                    if line.variance_type == 'OVER' and line.variance_percent > tolerance.over_receipt_percent:
                        has_variance = True
                    elif line.variance_type == 'SHORT' and line.variance_percent > tolerance.under_receipt_percent:
                        has_variance = True

                line.save()

        self.has_quantity_variance = has_variance
        self.save(update_fields=['has_quantity_variance'])
        return has_variance

    def can_post(self):
        """Check if GRN can be posted to ledger."""
        if self.status != self.Status.CONFIRMED:
            return False, "GRN must be in CONFIRMED status"

        if self.requires_qc and self.qc_status not in [self.QCStatus.PASSED, self.QCStatus.NOT_REQUIRED, self.QCStatus.PARTIAL]:
            return False, "QC inspection not completed or failed"

        if self.has_quantity_variance and not self.variance_approved:
            return False, "Quantity variances require approval"

        return True, "Ready to post"


class GRNLine(models.Model):
    """
    Line item on a GRN - individual item being received.
    Each line posts one or more ledger entries when the GRN is confirmed.
    """

    grn = models.ForeignKey(
        GoodsReceiptNote, on_delete=models.CASCADE,
        related_name="lines"
    )
    line_number = models.IntegerField()

    # What's being received
    item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT,
        related_name="grn_lines"
    )
    qty_expected = models.DecimalField(
        max_digits=15, decimal_places=3, default=0,
        help_text="Expected quantity from PO"
    )
    qty_received = models.DecimalField(
        max_digits=15, decimal_places=3,
        help_text="Actual quantity received"
    )

    # QC quantities (populated after QC inspection)
    qty_accepted = models.DecimalField(
        max_digits=15, decimal_places=3, default=0,
        help_text="Quantity accepted after QC"
    )
    qty_rejected = models.DecimalField(
        max_digits=15, decimal_places=3, default=0,
        help_text="Quantity rejected during QC"
    )

    uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT,
        related_name="grn_lines"
    )

    # Location override
    location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="grn_lines",
        help_text="Override receiving location (if different from GRN header)"
    )

    # Lot tracking
    lot = models.ForeignKey(
        MaterialLot, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="grn_lines",
        help_text="Lot for lot-tracked items"
    )
    lot_number_received = models.CharField(
        max_length=50, blank=True,
        help_text="Lot number from supplier (if creating new lot)"
    )

    # Condition at receipt
    condition = models.ForeignKey(
        ConditionType, on_delete=models.PROTECT,
        related_name="grn_lines",
        help_text="Condition of goods at receipt"
    )
    quality_status = models.ForeignKey(
        QualityStatus, on_delete=models.PROTECT,
        related_name="grn_lines",
        help_text="Initial quality status (typically QUARANTINE)"
    )

    # Cost
    unit_cost = models.DecimalField(
        max_digits=15, decimal_places=4, default=0
    )
    total_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )

    # PO line reference
    po_line = models.ForeignKey(
        "supplychain.PurchaseOrderLine", on_delete=models.PROTECT,
        null=True, blank=True, related_name="grn_lines"
    )

    # QC per-line status
    class LineQCStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PASSED = "PASSED", "Passed"
        FAILED = "FAILED", "Failed"
        PARTIAL = "PARTIAL", "Partial Pass"

    line_qc_status = models.CharField(
        max_length=20, choices=LineQCStatus.choices, default=LineQCStatus.PENDING
    )
    qc_notes = models.TextField(blank=True, help_text="QC inspection notes")
    qc_defects = models.TextField(blank=True, help_text="Description of defects found")

    # Variance tracking per line
    class VarianceType(models.TextChoices):
        NONE = "NONE", "None"
        SHORT = "SHORT", "Under Receipt"
        OVER = "OVER", "Over Receipt"

    variance_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Variance from expected quantity (%)"
    )
    variance_type = models.CharField(
        max_length=10, choices=VarianceType.choices, default=VarianceType.NONE
    )

    # Status tracking
    is_posted = models.BooleanField(
        default=False,
        help_text="Has this line been posted to ledger?"
    )
    posted_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "grn_lines"
        verbose_name = "GRN Line"
        verbose_name_plural = "GRN Lines"
        ordering = ["grn", "line_number"]
        unique_together = [["grn", "line_number"]]

    def __str__(self):
        return f"{self.grn.grn_number} Line {self.line_number}: {self.item.code}"

    def save(self, *args, **kwargs):
        self.total_cost = self.qty_received * self.unit_cost
        super().save(*args, **kwargs)

    def get_qty_to_post(self):
        """Get quantity to post to ledger (accepted qty if QC done, otherwise received)."""
        if self.grn.requires_qc and self.qty_accepted > 0:
            return self.qty_accepted
        return self.qty_received


class ReceiptTolerance(models.Model):
    """
    Configurable tolerance thresholds for receipt variance handling.
    Can be set per item, category, vendor, or system-wide default.
    """

    class AppliesTo(models.TextChoices):
        SYSTEM = "SYSTEM", "System Default"
        CATEGORY = "CATEGORY", "Category"
        ITEM = "ITEM", "Specific Item"
        VENDOR = "VENDOR", "Vendor"

    applies_to = models.CharField(max_length=20, choices=AppliesTo.choices)
    category = models.ForeignKey(
        InventoryCategory, on_delete=models.CASCADE,
        null=True, blank=True, related_name="receipt_tolerances"
    )
    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE,
        null=True, blank=True, related_name="receipt_tolerances"
    )
    vendor = models.ForeignKey(
        "supplychain.Vendor", on_delete=models.CASCADE,
        null=True, blank=True, related_name="receipt_tolerances"
    )

    # Tolerance thresholds (percentages)
    over_receipt_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00,
        help_text="Maximum over-receipt allowed (%)"
    )
    under_receipt_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00,
        help_text="Maximum under-receipt allowed without approval (%)"
    )

    # QC and closure settings
    require_qc = models.BooleanField(
        default=True,
        help_text="Require QC inspection for items with this tolerance"
    )
    auto_close_on_tolerance = models.BooleanField(
        default=True,
        help_text="Auto-close PO line if within tolerance"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "receipt_tolerances"
        verbose_name = "Receipt Tolerance"
        verbose_name_plural = "Receipt Tolerances"

    def __str__(self):
        if self.applies_to == self.AppliesTo.SYSTEM:
            return "System Default Tolerance"
        elif self.applies_to == self.AppliesTo.CATEGORY:
            return f"Category: {self.category}"
        elif self.applies_to == self.AppliesTo.ITEM:
            return f"Item: {self.item}"
        elif self.applies_to == self.AppliesTo.VENDOR:
            return f"Vendor: {self.vendor}"
        return f"Tolerance {self.pk}"

    @classmethod
    def get_tolerance_for(cls, item=None, category=None, vendor=None):
        """
        Get most specific applicable tolerance.
        Priority: Item > Vendor > Category > System
        """
        # Try item-specific first
        if item:
            tol = cls.objects.filter(
                applies_to=cls.AppliesTo.ITEM,
                item=item,
                is_active=True
            ).first()
            if tol:
                return tol

        # Try vendor-specific
        if vendor:
            tol = cls.objects.filter(
                applies_to=cls.AppliesTo.VENDOR,
                vendor=vendor,
                is_active=True
            ).first()
            if tol:
                return tol

        # Try category-specific
        if category:
            tol = cls.objects.filter(
                applies_to=cls.AppliesTo.CATEGORY,
                category=category,
                is_active=True
            ).first()
            if tol:
                return tol

        # Fall back to system default
        return cls.objects.filter(
            applies_to=cls.AppliesTo.SYSTEM,
            is_active=True
        ).first()


class StockIssue(models.Model):
    """
    Stock Issue document - Outbound goods issue.

    Documents the issue of goods from inventory for:
    - Work Orders (material consumption)
    - Sales Orders
    - Internal consumption
    - Scrap/disposal

    Each line posts negative qty_delta to the StockLedger.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        PICKED = "PICKED", "Picked"
        ISSUED = "ISSUED", "Issued"
        CANCELLED = "CANCELLED", "Cancelled"

    class IssueType(models.TextChoices):
        WORK_ORDER = "WO", "Work Order Issue"
        SALES = "SALES", "Sales Issue"
        INTERNAL = "INTERNAL", "Internal Consumption"
        SCRAP = "SCRAP", "Scrap/Disposal"
        SAMPLE = "SAMPLE", "Sample Issue"
        OTHER = "OTHER", "Other Issue"

    # Document identification
    issue_number = models.CharField(
        max_length=50, unique=True,
        help_text="Auto-generated issue number (e.g., ISS-2024-0001)"
    )
    issue_type = models.CharField(
        max_length=20, choices=IssueType.choices, default=IssueType.WORK_ORDER
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    # Source reference
    work_order = models.ForeignKey(
        "workorders.WorkOrder", on_delete=models.PROTECT,
        null=True, blank=True, related_name="stock_issues"
    )
    sales_order = models.ForeignKey(
        "sales.SalesOrder", on_delete=models.PROTECT,
        null=True, blank=True, related_name="stock_issues"
    )
    reference = models.CharField(
        max_length=100, blank=True,
        help_text="External reference"
    )

    # Issue from
    warehouse = models.ForeignKey(
        "sales.Warehouse", on_delete=models.PROTECT,
        related_name="stock_issues"
    )
    default_location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        related_name="stock_issues",
        help_text="Default issue location"
    )

    # Issue to (destination party)
    issue_to_party = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="stock_issues_received",
        help_text="Party receiving the goods (e.g., rig)"
    )

    # Dates
    issue_date = models.DateField()
    required_date = models.DateField(null=True, blank=True)
    posted_date = models.DateTimeField(null=True, blank=True)

    # Audit
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="stock_issues_created"
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name="stock_issues_issued"
    )

    class Meta:
        db_table = "stock_issues"
        verbose_name = "Stock Issue"
        verbose_name_plural = "Stock Issues"
        ordering = ["-issue_date", "-issue_number"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["issue_date"]),
            models.Index(fields=["issue_number"]),
        ]

    def __str__(self):
        return f"{self.issue_number} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.issue_number:
            from django.utils import timezone
            year = timezone.now().year
            last_issue = StockIssue.objects.filter(
                issue_number__startswith=f"ISS-{year}-"
            ).order_by("-issue_number").first()

            if last_issue:
                last_num = int(last_issue.issue_number.split("-")[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.issue_number = f"ISS-{year}-{new_num:04d}"

        super().save(*args, **kwargs)


class StockIssueLine(models.Model):
    """Line item on a Stock Issue."""

    issue = models.ForeignKey(
        StockIssue, on_delete=models.CASCADE,
        related_name="lines"
    )
    line_number = models.IntegerField()

    # What's being issued
    item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT,
        related_name="issue_lines"
    )
    qty_requested = models.DecimalField(
        max_digits=15, decimal_places=3,
        help_text="Quantity requested"
    )
    qty_issued = models.DecimalField(
        max_digits=15, decimal_places=3, default=0,
        help_text="Actual quantity issued"
    )
    uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT,
        related_name="issue_lines"
    )

    # From where
    location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        related_name="issue_lines"
    )

    # Lot tracking
    lot = models.ForeignKey(
        MaterialLot, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="issue_lines"
    )

    # Stock dimensions at issue
    owner_party = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        related_name="issue_lines"
    )
    ownership_type = models.ForeignKey(
        OwnershipType, on_delete=models.PROTECT,
        related_name="issue_lines"
    )
    condition = models.ForeignKey(
        ConditionType, on_delete=models.PROTECT,
        related_name="issue_lines"
    )
    quality_status = models.ForeignKey(
        QualityStatus, on_delete=models.PROTECT,
        related_name="issue_lines"
    )

    # Cost
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Posting
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "stock_issue_lines"
        verbose_name = "Stock Issue Line"
        verbose_name_plural = "Stock Issue Lines"
        ordering = ["issue", "line_number"]
        unique_together = [["issue", "line_number"]]

    def __str__(self):
        return f"{self.issue.issue_number} Line {self.line_number}: {self.item.code}"


class StockTransfer(models.Model):
    """
    Stock Transfer document - Movement between locations.

    Transfers stock between locations (same or different warehouses).
    Creates two ledger entries: negative from source, positive to destination.
    Can also handle ownership transfers and quality status changes.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending Approval"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        RECEIVED = "RECEIVED", "Received"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class TransferType(models.TextChoices):
        LOCATION = "LOCATION", "Location Transfer"
        WAREHOUSE = "WAREHOUSE", "Warehouse Transfer"
        OWNERSHIP = "OWNERSHIP", "Ownership Transfer"
        QC_STATUS = "QC_STATUS", "Quality Status Change"

    # Document identification
    transfer_number = models.CharField(
        max_length=50, unique=True,
        help_text="Auto-generated transfer number"
    )
    transfer_type = models.CharField(
        max_length=20, choices=TransferType.choices, default=TransferType.LOCATION
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    # From
    from_warehouse = models.ForeignKey(
        "sales.Warehouse", on_delete=models.PROTECT,
        related_name="transfers_out"
    )
    from_location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        related_name="transfers_out"
    )

    # To
    to_warehouse = models.ForeignKey(
        "sales.Warehouse", on_delete=models.PROTECT,
        related_name="transfers_in"
    )
    to_location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        related_name="transfers_in"
    )

    # Ownership change (optional)
    from_owner = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        related_name="transfers_from",
        help_text="Original owner"
    )
    to_owner = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="transfers_to",
        help_text="New owner (if ownership transfer)"
    )

    # Dates
    transfer_date = models.DateField()
    shipped_date = models.DateTimeField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)
    posted_date = models.DateTimeField(null=True, blank=True)

    # Audit
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="transfers_created"
    )

    class Meta:
        db_table = "stock_transfers"
        verbose_name = "Stock Transfer"
        verbose_name_plural = "Stock Transfers"
        ordering = ["-transfer_date", "-transfer_number"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["transfer_date"]),
            models.Index(fields=["transfer_number"]),
        ]

    def __str__(self):
        return f"{self.transfer_number} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.transfer_number:
            from django.utils import timezone
            year = timezone.now().year
            last_transfer = StockTransfer.objects.filter(
                transfer_number__startswith=f"TRF-{year}-"
            ).order_by("-transfer_number").first()

            if last_transfer:
                last_num = int(last_transfer.transfer_number.split("-")[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.transfer_number = f"TRF-{year}-{new_num:04d}"

        super().save(*args, **kwargs)


class StockTransferLine(models.Model):
    """Line item on a Stock Transfer."""

    transfer = models.ForeignKey(
        StockTransfer, on_delete=models.CASCADE,
        related_name="lines"
    )
    line_number = models.IntegerField()

    # What's being transferred
    item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT,
        related_name="transfer_lines"
    )
    qty_requested = models.DecimalField(
        max_digits=15, decimal_places=3
    )
    qty_shipped = models.DecimalField(
        max_digits=15, decimal_places=3, default=0
    )
    qty_received = models.DecimalField(
        max_digits=15, decimal_places=3, default=0
    )
    uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT,
        related_name="transfer_lines"
    )

    # Lot
    lot = models.ForeignKey(
        MaterialLot, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="transfer_lines"
    )

    # Stock dimensions
    ownership_type = models.ForeignKey(
        OwnershipType, on_delete=models.PROTECT,
        related_name="transfer_lines"
    )
    condition = models.ForeignKey(
        ConditionType, on_delete=models.PROTECT,
        related_name="transfer_lines"
    )
    from_quality_status = models.ForeignKey(
        QualityStatus, on_delete=models.PROTECT,
        related_name="transfer_lines_from"
    )
    to_quality_status = models.ForeignKey(
        QualityStatus, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="transfer_lines_to",
        help_text="New quality status (if changing)"
    )

    # Cost
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    # Posting
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "stock_transfer_lines"
        verbose_name = "Stock Transfer Line"
        verbose_name_plural = "Stock Transfer Lines"
        ordering = ["transfer", "line_number"]
        unique_together = [["transfer", "line_number"]]

    def __str__(self):
        return f"{self.transfer.transfer_number} Line {self.line_number}: {self.item.code}"


class StockAdjustment(models.Model):
    """
    Stock Adjustment document - Quantity corrections and adjustments.

    Used for:
    - Cycle count corrections
    - Physical inventory adjustments
    - Write-offs
    - Opening balance initialization
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        POSTED = "POSTED", "Posted"
        CANCELLED = "CANCELLED", "Cancelled"

    class AdjustmentType(models.TextChoices):
        CYCLE_COUNT = "CYCLE", "Cycle Count"
        PHYSICAL = "PHYSICAL", "Physical Inventory"
        WRITE_OFF = "WRITEOFF", "Write Off"
        OPENING = "OPENING", "Opening Balance"
        CORRECTION = "CORRECT", "Correction"
        OTHER = "OTHER", "Other"

    # Document identification
    adjustment_number = models.CharField(
        max_length=50, unique=True
    )
    adjustment_type = models.CharField(
        max_length=20, choices=AdjustmentType.choices, default=AdjustmentType.CORRECTION
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    # Location
    warehouse = models.ForeignKey(
        "sales.Warehouse", on_delete=models.PROTECT,
        related_name="stock_adjustments"
    )
    location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        related_name="stock_adjustments"
    )

    # Reason
    reason = models.ForeignKey(
        AdjustmentReason, on_delete=models.PROTECT,
        related_name="adjustments"
    )

    # Dates
    adjustment_date = models.DateField()
    posted_date = models.DateTimeField(null=True, blank=True)

    # Approval
    requires_approval = models.BooleanField(default=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name="adjustments_approved"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Audit
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="adjustments_created"
    )

    class Meta:
        db_table = "stock_adjustments"
        verbose_name = "Stock Adjustment"
        verbose_name_plural = "Stock Adjustments"
        ordering = ["-adjustment_date", "-adjustment_number"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["adjustment_date"]),
            models.Index(fields=["adjustment_number"]),
        ]

    def __str__(self):
        return f"{self.adjustment_number} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.adjustment_number:
            from django.utils import timezone
            year = timezone.now().year
            last_adj = StockAdjustment.objects.filter(
                adjustment_number__startswith=f"ADJ-{year}-"
            ).order_by("-adjustment_number").first()

            if last_adj:
                last_num = int(last_adj.adjustment_number.split("-")[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.adjustment_number = f"ADJ-{year}-{new_num:04d}"

        super().save(*args, **kwargs)


class StockAdjustmentLine(models.Model):
    """Line item on a Stock Adjustment."""

    adjustment = models.ForeignKey(
        StockAdjustment, on_delete=models.CASCADE,
        related_name="lines"
    )
    line_number = models.IntegerField()

    # What's being adjusted
    item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT,
        related_name="adjustment_lines"
    )
    qty_system = models.DecimalField(
        max_digits=15, decimal_places=3,
        help_text="System quantity before adjustment"
    )
    qty_counted = models.DecimalField(
        max_digits=15, decimal_places=3,
        help_text="Actual counted quantity"
    )
    qty_adjustment = models.DecimalField(
        max_digits=15, decimal_places=3,
        help_text="Difference (counted - system)"
    )
    uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT,
        related_name="adjustment_lines"
    )

    # Lot
    lot = models.ForeignKey(
        MaterialLot, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="adjustment_lines"
    )

    # Stock dimensions
    owner_party = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        related_name="adjustment_lines"
    )
    ownership_type = models.ForeignKey(
        OwnershipType, on_delete=models.PROTECT,
        related_name="adjustment_lines"
    )
    condition = models.ForeignKey(
        ConditionType, on_delete=models.PROTECT,
        related_name="adjustment_lines"
    )
    quality_status = models.ForeignKey(
        QualityStatus, on_delete=models.PROTECT,
        related_name="adjustment_lines"
    )

    # Cost
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Posting
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "stock_adjustment_lines"
        verbose_name = "Stock Adjustment Line"
        verbose_name_plural = "Stock Adjustment Lines"
        ordering = ["adjustment", "line_number"]
        unique_together = [["adjustment", "line_number"]]

    def __str__(self):
        return f"{self.adjustment.adjustment_number} Line {self.line_number}: {self.item.code}"

    def save(self, *args, **kwargs):
        self.qty_adjustment = self.qty_counted - self.qty_system
        self.total_cost = self.qty_adjustment * self.unit_cost
        super().save(*args, **kwargs)


# =============================================================================
# PHASE 4: ASSET TRACKING (Serialized Lifecycle Management)
# =============================================================================

class Asset(models.Model):
    """
    Serialized Asset with full lifecycle tracking.

    Assets are unique, serialized items that require individual tracking
    throughout their lifecycle. Unlike lot-tracked items (which track batches),
    each asset is a unique entity with its own history, location, and status.

    Key capabilities:
    - Unique serial number tracking
    - Full lifecycle management (procurement → operation → disposal)
    - Location and custody tracking
    - Maintenance history linkage
    - Depreciation tracking (optional)
    - Parent-child relationships (assemblies)

    Examples: Drill bits, BHA components, tools, equipment
    """

    class Status(models.TextChoices):
        # Procurement/Receipt
        ON_ORDER = "ON_ORDER", "On Order"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        RECEIVED = "RECEIVED", "Received"

        # Inspection/Quality
        QUARANTINE = "QUARANTINE", "In Quarantine"
        INSPECTION = "INSPECTION", "Under Inspection"
        READY = "READY", "Ready for Use"

        # Operations
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        IN_USE = "IN_USE", "In Use"
        DEPLOYED = "DEPLOYED", "Deployed to Field"

        # Maintenance
        MAINTENANCE = "MAINTENANCE", "Under Maintenance"
        REPAIR = "REPAIR", "Under Repair"
        REFURBISHMENT = "REFURBISHMENT", "In Refurbishment"

        # End of Life
        DAMAGED = "DAMAGED", "Damaged"
        SCRAP = "SCRAP", "Scrapped"
        SOLD = "SOLD", "Sold"
        LOST = "LOST", "Lost"
        RETIRED = "RETIRED", "Retired"

    # Identification
    serial_number = models.CharField(
        max_length=100, unique=True,
        help_text="Unique serial number"
    )
    asset_tag = models.CharField(
        max_length=50, unique=True, blank=True, null=True,
        help_text="Internal asset tag (optional)"
    )

    # Item template (what type of asset this is)
    item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT,
        related_name="assets",
        help_text="Item template defining this asset type"
    )

    # Status and condition
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.RECEIVED
    )
    condition = models.ForeignKey(
        ConditionType, on_delete=models.PROTECT,
        related_name="assets"
    )
    quality_status = models.ForeignKey(
        QualityStatus, on_delete=models.PROTECT,
        related_name="assets"
    )

    # Current location
    current_location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        related_name="assets",
        help_text="Current physical location"
    )
    warehouse = models.ForeignKey(
        "sales.Warehouse", on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="assets"
    )

    # Ownership
    owner_party = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        related_name="owned_assets",
        help_text="Who owns this asset"
    )
    ownership_type = models.ForeignKey(
        OwnershipType, on_delete=models.PROTECT,
        related_name="assets"
    )

    # Custody (who currently has it - may differ from owner)
    custodian_party = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="custody_assets",
        help_text="Who currently has custody (if different from owner)"
    )

    # Lot reference (if received as part of a lot)
    lot = models.ForeignKey(
        MaterialLot, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="assets",
        help_text="Source lot (if applicable)"
    )

    # Source/Procurement
    grn = models.ForeignKey(
        GoodsReceiptNote, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="assets_received"
    )
    purchase_order = models.ForeignKey(
        "supplychain.PurchaseOrder", on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="assets"
    )
    supplier = models.ForeignKey(
        "supplychain.Supplier", on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="assets_supplied"
    )

    # Financial
    acquisition_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    current_value = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    salvage_value = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    depreciation_method = models.CharField(
        max_length=20, blank=True,
        help_text="SL=Straight Line, DD=Declining Balance"
    )
    useful_life_months = models.IntegerField(null=True, blank=True)

    # Dates
    acquisition_date = models.DateField(null=True, blank=True)
    in_service_date = models.DateField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    next_service_date = models.DateField(null=True, blank=True)
    disposal_date = models.DateField(null=True, blank=True)

    # Manufacturer info
    manufacturer_serial = models.CharField(
        max_length=100, blank=True,
        help_text="Manufacturer's serial number (if different)"
    )
    manufacture_date = models.DateField(null=True, blank=True)

    # Parent asset (for assemblies/components)
    parent_asset = models.ForeignKey(
        "self", on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="child_assets",
        help_text="Parent asset if this is a component"
    )

    # Work order reference (if currently deployed)
    current_work_order = models.ForeignKey(
        "workorders.WorkOrder", on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="deployed_assets"
    )

    # Certification/Compliance
    last_inspection_date = models.DateField(null=True, blank=True)
    next_inspection_date = models.DateField(null=True, blank=True)
    certification_number = models.CharField(max_length=100, blank=True)
    certification_expiry = models.DateField(null=True, blank=True)

    # Usage metrics
    total_run_hours = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Total operational hours"
    )
    total_cycles = models.IntegerField(
        default=0,
        help_text="Total operational cycles"
    )
    total_footage = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Total footage drilled (for bits)"
    )

    # Notes
    notes = models.TextField(blank=True)
    specifications = models.JSONField(
        null=True, blank=True,
        help_text="Asset-specific specifications"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="assets_created"
    )

    class Meta:
        db_table = "assets"
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["serial_number"]),
            models.Index(fields=["asset_tag"]),
            models.Index(fields=["status"]),
            models.Index(fields=["item"]),
            models.Index(fields=["current_location"]),
            models.Index(fields=["owner_party"]),
            models.Index(fields=["condition"]),
        ]

    def __str__(self):
        return f"{self.serial_number} ({self.item.code})"

    @property
    def is_available(self):
        """Check if asset is available for use."""
        return self.status in [self.Status.AVAILABLE, self.Status.READY]

    @property
    def is_operational(self):
        """Check if asset is in operational state."""
        return self.status in [
            self.Status.AVAILABLE,
            self.Status.RESERVED,
            self.Status.IN_USE,
            self.Status.DEPLOYED
        ]


class AssetMovement(models.Model):
    """
    Tracks all movements/status changes of an asset.

    Every significant change to an asset creates a movement record,
    providing complete audit trail and lifecycle history.
    """

    class MovementType(models.TextChoices):
        RECEIPT = "RECEIPT", "Initial Receipt"
        TRANSFER = "TRANSFER", "Location Transfer"
        DEPLOY = "DEPLOY", "Deploy to Job"
        RETURN = "RETURN", "Return from Job"
        STATUS_CHANGE = "STATUS", "Status Change"
        MAINTENANCE_IN = "MAINT_IN", "Sent to Maintenance"
        MAINTENANCE_OUT = "MAINT_OUT", "Returned from Maintenance"
        CONDITION_CHANGE = "CONDITION", "Condition Change"
        OWNERSHIP_CHANGE = "OWNER", "Ownership Transfer"
        DISPOSAL = "DISPOSAL", "Disposed/Scrapped"
        ADJUSTMENT = "ADJUST", "Adjustment/Correction"

    asset = models.ForeignKey(
        Asset, on_delete=models.PROTECT,
        related_name="movements"
    )
    movement_number = models.CharField(max_length=50)
    movement_date = models.DateTimeField()
    movement_type = models.CharField(
        max_length=20, choices=MovementType.choices
    )

    # From state
    from_location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="asset_movements_from"
    )
    from_status = models.CharField(max_length=20, blank=True)
    from_condition = models.ForeignKey(
        ConditionType, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="asset_movements_from"
    )
    from_party = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="asset_movements_from"
    )

    # To state
    to_location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="asset_movements_to"
    )
    to_status = models.CharField(max_length=20, blank=True)
    to_condition = models.ForeignKey(
        ConditionType, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="asset_movements_to"
    )
    to_party = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="asset_movements_to"
    )

    # Reference documents
    work_order = models.ForeignKey(
        "workorders.WorkOrder", on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="asset_movements"
    )
    stock_transfer = models.ForeignKey(
        StockTransfer, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="asset_movements"
    )

    # Usage at time of movement (for returns)
    run_hours = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Run hours at this movement"
    )
    cycles = models.IntegerField(default=0)
    footage = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )

    # Audit
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="asset_movements_created"
    )

    # Ledger linkage (for movements that affect stock)
    ledger_entry = models.ForeignKey(
        StockLedger, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="asset_movements"
    )

    class Meta:
        db_table = "asset_movements"
        verbose_name = "Asset Movement"
        verbose_name_plural = "Asset Movements"
        ordering = ["-movement_date"]
        indexes = [
            models.Index(fields=["asset", "movement_date"]),
            models.Index(fields=["movement_type"]),
            models.Index(fields=["movement_number"]),
        ]

    def __str__(self):
        return f"{self.movement_number}: {self.asset.serial_number} - {self.get_movement_type_display()}"


# =============================================================================
# PHASE 5: QC GATES (Quality Status Transitions)
# =============================================================================

class QualityStatusChange(models.Model):
    """
    Tracks all quality status transitions for audit and workflow control.

    Every change from one QualityStatus to another is recorded here,
    providing complete traceability for QC gate compliance.

    Common workflows:
    - QUARANTINE → RELEASED (passed inspection)
    - QUARANTINE → BLOCKED (failed inspection)
    - BLOCKED → QUARANTINE (re-inspection requested)
    - RELEASED → BLOCKED (quality issue discovered)
    """

    class ChangeType(models.TextChoices):
        RECEIPT = "RECEIPT", "Initial Receipt"
        INSPECTION = "INSPECTION", "Inspection Result"
        REWORK = "REWORK", "After Rework"
        RETEST = "RETEST", "Re-test/Re-inspection"
        RELEASE = "RELEASE", "Manual Release"
        BLOCK = "BLOCK", "Manual Block"
        EXPIRY = "EXPIRY", "Expired/Time-based"
        CORRECTION = "CORRECTION", "Data Correction"

    # What changed
    change_number = models.CharField(max_length=50, unique=True)
    change_date = models.DateTimeField(auto_now_add=True)
    change_type = models.CharField(
        max_length=20, choices=ChangeType.choices
    )

    # Transition
    from_status = models.ForeignKey(
        QualityStatus, on_delete=models.PROTECT,
        related_name="changes_from",
        help_text="Previous quality status"
    )
    to_status = models.ForeignKey(
        QualityStatus, on_delete=models.PROTECT,
        related_name="changes_to",
        help_text="New quality status"
    )

    # What was affected (one of these should be set)
    stock_balance = models.ForeignKey(
        StockBalance, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="qc_changes"
    )
    lot = models.ForeignKey(
        MaterialLot, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="qc_changes"
    )
    asset = models.ForeignKey(
        Asset, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="qc_changes"
    )

    # Quantity affected (for partial releases/blocks)
    qty_affected = models.DecimalField(
        max_digits=15, decimal_places=3, null=True, blank=True,
        help_text="Quantity affected (if partial change)"
    )

    # Inspection details
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="inspections_performed"
    )
    inspection_date = models.DateTimeField(null=True, blank=True)
    inspection_notes = models.TextField(blank=True)

    # Approval (for releases)
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="qc_approvals"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Reference documents
    grn = models.ForeignKey(
        GoodsReceiptNote, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="qc_changes"
    )
    work_order = models.ForeignKey(
        "workorders.WorkOrder", on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="qc_changes"
    )

    # Ledger linkage (QC changes post to ledger with qty=0 but status dimension change)
    ledger_entry = models.ForeignKey(
        StockLedger, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="qc_changes"
    )

    # Audit
    reason = models.TextField(help_text="Reason for status change")
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="qc_changes_created"
    )

    class Meta:
        db_table = "quality_status_changes"
        verbose_name = "Quality Status Change"
        verbose_name_plural = "Quality Status Changes"
        ordering = ["-change_date"]
        indexes = [
            models.Index(fields=["from_status", "to_status"]),
            models.Index(fields=["change_date"]),
            models.Index(fields=["lot"]),
            models.Index(fields=["asset"]),
        ]

    def __str__(self):
        return f"{self.change_number}: {self.from_status.code} → {self.to_status.code}"

    def save(self, *args, **kwargs):
        if not self.change_number:
            from django.utils import timezone
            year = timezone.now().year
            last = QualityStatusChange.objects.filter(
                change_number__startswith=f"QC-{year}-"
            ).order_by("-change_number").first()

            if last:
                last_num = int(last.change_number.split("-")[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.change_number = f"QC-{year}-{new_num:05d}"

        super().save(*args, **kwargs)


# =============================================================================
# PHASE 6: STOCK RESERVATIONS
# =============================================================================

class StockReservation(models.Model):
    """
    Stock Reservation - Allocates stock to a demand source.

    Reservations reduce qty_available without reducing qty_on_hand.
    They are consumed when the actual issue happens.

    Use cases:
    - Work Order material reservation
    - Sales Order allocation
    - Transfer requests
    - Customer holds
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PARTIALLY_ISSUED = "PARTIAL", "Partially Issued"
        ISSUED = "ISSUED", "Fully Issued"
        CANCELLED = "CANCELLED", "Cancelled"
        EXPIRED = "EXPIRED", "Expired"

    class ReservationType(models.TextChoices):
        WORK_ORDER = "WO", "Work Order"
        SALES_ORDER = "SO", "Sales Order"
        TRANSFER = "TRANSFER", "Transfer Request"
        CUSTOMER_HOLD = "HOLD", "Customer Hold"
        PROJECT = "PROJECT", "Project Allocation"
        OTHER = "OTHER", "Other"

    # Identification
    reservation_number = models.CharField(max_length=50, unique=True)
    reservation_type = models.CharField(
        max_length=20, choices=ReservationType.choices
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    # What's reserved
    item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT,
        related_name="reservations"
    )
    qty_reserved = models.DecimalField(
        max_digits=15, decimal_places=3,
        help_text="Quantity reserved"
    )
    qty_issued = models.DecimalField(
        max_digits=15, decimal_places=3, default=0,
        help_text="Quantity already issued against this reservation"
    )
    uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT,
        related_name="reservations"
    )

    # From where (optional - can be general or specific)
    location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="reservations",
        help_text="Specific location (if location-specific reservation)"
    )
    lot = models.ForeignKey(
        MaterialLot, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="reservations",
        help_text="Specific lot (if lot-specific reservation)"
    )
    stock_balance = models.ForeignKey(
        StockBalance, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="reservations",
        help_text="Specific stock balance (fully dimensioned reservation)"
    )

    # For whom
    reserved_for_party = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="reservations_for"
    )

    # Demand source (one of these should be set based on type)
    work_order = models.ForeignKey(
        "workorders.WorkOrder", on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="reservations"
    )
    sales_order = models.ForeignKey(
        "sales.SalesOrder", on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="reservations"
    )
    transfer_request = models.ForeignKey(
        StockTransfer, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="reservations"
    )

    # Dates
    reservation_date = models.DateTimeField(auto_now_add=True)
    required_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(
        null=True, blank=True,
        help_text="Reservation expires if not fulfilled by this date"
    )

    # Priority
    priority = models.IntegerField(
        default=5,
        help_text="1=Highest, 10=Lowest"
    )

    # Audit
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="reservations_created"
    )

    class Meta:
        db_table = "stock_reservations"
        verbose_name = "Stock Reservation"
        verbose_name_plural = "Stock Reservations"
        ordering = ["priority", "required_date", "-reservation_date"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["item"]),
            models.Index(fields=["work_order"]),
            models.Index(fields=["required_date"]),
        ]

    def __str__(self):
        return f"{self.reservation_number}: {self.item.code} x {self.qty_reserved}"

    @property
    def qty_remaining(self):
        """Quantity still to be issued."""
        return self.qty_reserved - self.qty_issued

    def save(self, *args, **kwargs):
        if not self.reservation_number:
            from django.utils import timezone
            year = timezone.now().year
            last = StockReservation.objects.filter(
                reservation_number__startswith=f"RES-{year}-"
            ).order_by("-reservation_number").first()

            if last:
                last_num = int(last.reservation_number.split("-")[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.reservation_number = f"RES-{year}-{new_num:05d}"

        super().save(*args, **kwargs)


# =============================================================================
# PHASE 7: BILL OF MATERIALS (BOM)
# =============================================================================

class BillOfMaterial(models.Model):
    """
    Bill of Materials (BOM) - Defines components required for an assembly/service.

    BOMs are used for:
    - Kit/Assembly definitions
    - Work Order material requirements
    - Service job material templates
    - Cost roll-up calculations
    """

    class BOMType(models.TextChoices):
        STANDARD = "STD", "Standard BOM"
        PHANTOM = "PHANTOM", "Phantom/Sub-assembly"
        TEMPLATE = "TEMPLATE", "Template (for estimation)"
        REPAIR = "REPAIR", "Repair BOM"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        OBSOLETE = "OBSOLETE", "Obsolete"

    # Parent item (what's being built/assembled)
    parent_item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT,
        related_name="boms_as_parent",
        help_text="The item being assembled/built"
    )

    # BOM identification
    bom_code = models.CharField(
        max_length=50, unique=True,
        help_text="Unique BOM identifier"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    version = models.CharField(
        max_length=20, default="1.0",
        help_text="BOM version"
    )

    bom_type = models.CharField(
        max_length=20, choices=BOMType.choices, default=BOMType.STANDARD
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    # Quantity produced
    base_quantity = models.DecimalField(
        max_digits=15, decimal_places=3, default=1,
        help_text="Quantity produced by this BOM"
    )
    uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT,
        related_name="boms"
    )

    # Effectivity dates
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)

    # Cost roll-up
    material_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text="Total material cost (sum of components)"
    )
    labor_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    overhead_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    total_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )

    # Work order template linkage
    default_for_wo_type = models.CharField(
        max_length=50, blank=True,
        help_text="Default BOM for this work order type"
    )

    # Audit
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="boms_created"
    )

    class Meta:
        db_table = "bill_of_materials"
        verbose_name = "Bill of Material"
        verbose_name_plural = "Bills of Material"
        ordering = ["parent_item", "version"]
        indexes = [
            models.Index(fields=["parent_item"]),
            models.Index(fields=["status"]),
            models.Index(fields=["bom_code"]),
        ]

    def __str__(self):
        return f"{self.bom_code}: {self.parent_item.code} v{self.version}"

    def recalculate_costs(self):
        """Recalculate total material cost from components."""
        total = sum(line.extended_cost for line in self.lines.all())
        self.material_cost = total
        self.total_cost = self.material_cost + self.labor_cost + self.overhead_cost
        self.save(update_fields=["material_cost", "total_cost", "updated_at"])


class BOMLine(models.Model):
    """
    BOM Line - Individual component in a Bill of Materials.
    """

    class ComponentType(models.TextChoices):
        MATERIAL = "MATERIAL", "Material"
        CONSUMABLE = "CONSUMABLE", "Consumable"
        TOOL = "TOOL", "Tool (non-consumed)"
        SUBASSEMBLY = "SUBASM", "Sub-assembly"

    bom = models.ForeignKey(
        BillOfMaterial, on_delete=models.CASCADE,
        related_name="lines"
    )
    line_number = models.IntegerField()

    # Component item
    component_item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT,
        related_name="bom_usages",
        help_text="Component/material required"
    )
    component_type = models.CharField(
        max_length=20, choices=ComponentType.choices, default=ComponentType.MATERIAL
    )

    # Quantity
    quantity_per = models.DecimalField(
        max_digits=15, decimal_places=6,
        help_text="Quantity per base_quantity of parent"
    )
    uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT,
        related_name="bom_lines"
    )

    # Scrap/Waste allowance
    scrap_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Expected scrap percentage"
    )

    # Cost
    unit_cost = models.DecimalField(
        max_digits=15, decimal_places=4, default=0
    )
    extended_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text="quantity_per * unit_cost * (1 + scrap_percent)"
    )

    # Optional: Substitute items
    is_optional = models.BooleanField(
        default=False,
        help_text="Optional component"
    )
    substitute_group = models.CharField(
        max_length=20, blank=True,
        help_text="Group code for substitute items"
    )

    # Reference designator (for electronics/assemblies)
    reference_designator = models.CharField(
        max_length=50, blank=True,
        help_text="Position/reference on assembly"
    )

    # Operation linkage (for routing integration)
    operation_sequence = models.IntegerField(
        null=True, blank=True,
        help_text="Operation where component is consumed"
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "inventory_bom_lines"
        verbose_name = "BOM Line"
        verbose_name_plural = "BOM Lines"
        ordering = ["bom", "line_number"]
        unique_together = [["bom", "line_number"]]
        indexes = [
            models.Index(fields=["component_item"]),
        ]

    def __str__(self):
        return f"{self.bom.bom_code} L{self.line_number}: {self.component_item.code}"

    def save(self, *args, **kwargs):
        # Calculate extended cost with scrap allowance
        from decimal import Decimal
        scrap_factor = Decimal("1") + (self.scrap_percent / Decimal("100"))
        self.extended_cost = self.quantity_per * self.unit_cost * scrap_factor
        super().save(*args, **kwargs)


# =============================================================================
# PHASE 8: CYCLE COUNT & PHYSICAL INVENTORY
# =============================================================================

class CycleCountPlan(models.Model):
    """
    Cycle Count Plan - Defines counting strategy and schedule.

    Cycle counting is an ongoing process of counting inventory
    on a rotating basis, rather than doing full physical inventories.

    Strategies:
    - ABC Classification: Count A items more frequently
    - Location-based: Count by zone/aisle
    - Random: Random selection each period
    """

    class PlanType(models.TextChoices):
        ABC = "ABC", "ABC Classification"
        LOCATION = "LOCATION", "Location Based"
        RANDOM = "RANDOM", "Random Selection"
        FULL = "FULL", "Full Physical Inventory"
        CUSTOM = "CUSTOM", "Custom Selection"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    # Plan identification
    plan_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    plan_type = models.CharField(
        max_length=20, choices=PlanType.choices, default=PlanType.ABC
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    # Scope
    warehouse = models.ForeignKey(
        "sales.Warehouse", on_delete=models.PROTECT,
        related_name="cycle_count_plans"
    )
    include_locations = models.ManyToManyField(
        InventoryLocation, blank=True,
        related_name="cycle_count_plans"
    )

    # Schedule
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    # ABC frequency (days between counts)
    count_frequency_a = models.IntegerField(
        default=30, help_text="Days between counts for A items"
    )
    count_frequency_b = models.IntegerField(
        default=60, help_text="Days between counts for B items"
    )
    count_frequency_c = models.IntegerField(
        default=90, help_text="Days between counts for C items"
    )

    # Tolerance thresholds
    tolerance_qty_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.0,
        help_text="Acceptable variance percent"
    )
    tolerance_value = models.DecimalField(
        max_digits=15, decimal_places=2, default=100,
        help_text="Acceptable variance value"
    )

    # Auto-adjustment settings
    auto_adjust_within_tolerance = models.BooleanField(
        default=False,
        help_text="Automatically create adjustments within tolerance"
    )
    require_approval_outside_tolerance = models.BooleanField(
        default=True
    )

    # Audit
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="cycle_count_plans_created"
    )

    class Meta:
        db_table = "cycle_count_plans"
        verbose_name = "Cycle Count Plan"
        verbose_name_plural = "Cycle Count Plans"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["warehouse"]),
        ]

    def __str__(self):
        return f"{self.plan_code}: {self.name}"


class CycleCountSession(models.Model):
    """
    Cycle Count Session - A single counting session/batch.

    Each session is a group of items to be counted together,
    generated from a plan or created ad-hoc.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COUNTING = "COUNTING", "Counting"
        REVIEW = "REVIEW", "Under Review"
        APPROVED = "APPROVED", "Approved"
        POSTED = "POSTED", "Posted to Adjustments"
        CANCELLED = "CANCELLED", "Cancelled"

    # Session identification
    session_number = models.CharField(max_length=50, unique=True)
    session_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    # Source
    plan = models.ForeignKey(
        CycleCountPlan, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="sessions"
    )

    # Scope
    warehouse = models.ForeignKey(
        "sales.Warehouse", on_delete=models.PROTECT,
        related_name="cycle_count_sessions"
    )
    location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="cycle_count_sessions"
    )

    # Count details
    count_started_at = models.DateTimeField(null=True, blank=True)
    count_completed_at = models.DateTimeField(null=True, blank=True)
    counter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="cycle_counts_performed"
    )

    # Results summary
    total_items = models.IntegerField(default=0)
    items_counted = models.IntegerField(default=0)
    items_matched = models.IntegerField(default=0)
    items_variance = models.IntegerField(default=0)
    total_variance_value = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )

    # Approval
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="cycle_counts_reviewed"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="cycle_counts_approved"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Posted adjustment
    adjustment = models.OneToOneField(
        StockAdjustment, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="cycle_count_session"
    )

    # Audit
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="cycle_count_sessions_created"
    )

    class Meta:
        db_table = "cycle_count_sessions"
        verbose_name = "Cycle Count Session"
        verbose_name_plural = "Cycle Count Sessions"
        ordering = ["-session_date", "-session_number"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["session_date"]),
            models.Index(fields=["warehouse"]),
        ]

    def __str__(self):
        return f"{self.session_number} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.session_number:
            from django.utils import timezone
            year = timezone.now().year
            last = CycleCountSession.objects.filter(
                session_number__startswith=f"CC-{year}-"
            ).order_by("-session_number").first()

            if last:
                last_num = int(last.session_number.split("-")[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.session_number = f"CC-{year}-{new_num:05d}"

        super().save(*args, **kwargs)


class CycleCountLine(models.Model):
    """
    Cycle Count Line - Individual item to count in a session.
    """

    class CountStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Count"
        COUNTED = "COUNTED", "Counted"
        RECOUNTED = "RECOUNTED", "Recounted"
        VERIFIED = "VERIFIED", "Verified"
        VARIANCE = "VARIANCE", "Variance Found"
        MATCHED = "MATCHED", "Matched"

    session = models.ForeignKey(
        CycleCountSession, on_delete=models.CASCADE,
        related_name="lines"
    )
    line_number = models.IntegerField()

    # What to count
    item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT,
        related_name="cycle_count_lines"
    )
    location = models.ForeignKey(
        InventoryLocation, on_delete=models.PROTECT,
        related_name="cycle_count_lines"
    )
    lot = models.ForeignKey(
        MaterialLot, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="cycle_count_lines"
    )

    # Stock dimensions
    owner_party = models.ForeignKey(
        Party, on_delete=models.PROTECT,
        related_name="cycle_count_lines"
    )
    ownership_type = models.ForeignKey(
        OwnershipType, on_delete=models.PROTECT,
        related_name="cycle_count_lines"
    )
    condition = models.ForeignKey(
        ConditionType, on_delete=models.PROTECT,
        related_name="cycle_count_lines"
    )
    quality_status = models.ForeignKey(
        QualityStatus, on_delete=models.PROTECT,
        related_name="cycle_count_lines"
    )

    # Quantities
    uom = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT,
        related_name="cycle_count_lines"
    )
    qty_system = models.DecimalField(
        max_digits=15, decimal_places=3,
        help_text="System quantity at time of count"
    )
    qty_counted = models.DecimalField(
        max_digits=15, decimal_places=3, null=True, blank=True,
        help_text="First count quantity"
    )
    qty_recounted = models.DecimalField(
        max_digits=15, decimal_places=3, null=True, blank=True,
        help_text="Recount quantity (if variance)"
    )
    qty_final = models.DecimalField(
        max_digits=15, decimal_places=3, null=True, blank=True,
        help_text="Final accepted quantity"
    )
    qty_variance = models.DecimalField(
        max_digits=15, decimal_places=3, null=True, blank=True,
        help_text="Variance (final - system)"
    )

    # Variance value
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    variance_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )

    # Status
    count_status = models.CharField(
        max_length=20, choices=CountStatus.choices, default=CountStatus.PENDING
    )
    counted_at = models.DateTimeField(null=True, blank=True)
    counted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="items_counted"
    )

    # Flags
    requires_recount = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycle_count_lines"
        verbose_name = "Cycle Count Line"
        verbose_name_plural = "Cycle Count Lines"
        ordering = ["session", "line_number"]
        unique_together = [["session", "line_number"]]
        indexes = [
            models.Index(fields=["item"]),
            models.Index(fields=["count_status"]),
        ]

    def __str__(self):
        return f"{self.session.session_number} L{self.line_number}: {self.item.code}"

    def save(self, *args, **kwargs):
        # Calculate variance if final qty is set
        if self.qty_final is not None:
            self.qty_variance = self.qty_final - self.qty_system
            self.variance_value = self.qty_variance * self.unit_cost

            # Update status based on variance
            if self.qty_variance == 0:
                self.count_status = self.CountStatus.MATCHED
            else:
                self.count_status = self.CountStatus.VARIANCE

        super().save(*args, **kwargs)
