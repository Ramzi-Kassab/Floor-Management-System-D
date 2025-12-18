"""
ARDT FMS - Technology Models
Version: 5.4

Tables:
- designs (P1)
- boms (P1)
- bom_lines (P1)
- design_cutter_layouts (P1)
- applications (reference)
- connection_sizes (reference)
- connection_types (reference)
- formation_types (reference)
- iadc_codes (reference)
- special_technologies (reference)
- upper_section_types (reference)
- connections
- breaker_slots
- pocket_shapes (reference)
- pocket_sizes (reference)
- design_pocket_configs
- design_pockets
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


# =============================================================================
# Reference Tables
# =============================================================================

class Application(models.Model):
    """Application types for drill bits."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "applications"
        ordering = ["name"]
        verbose_name = "Application"
        verbose_name_plural = "Applications"

    def __str__(self):
        return self.name


class ConnectionSize(models.Model):
    """Connection sizes for drill bits."""
    code = models.CharField(max_length=20, unique=True)
    size_inches = models.CharField(max_length=20)
    size_decimal = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "connection_sizes"
        ordering = ["size_decimal"]
        verbose_name = "Connection Size"
        verbose_name_plural = "Connection Sizes"

    def __str__(self):
        return f"{self.code} - {self.size_inches}"


class ConnectionType(models.Model):
    """Connection types for drill bits."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "connection_types"
        ordering = ["code"]
        verbose_name = "Connection Type"
        verbose_name_plural = "Connection Types"

    def __str__(self):
        return f"{self.code} - {self.name}"


class FormationType(models.Model):
    """Geological formation types."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    age = models.CharField(max_length=50, blank=True, help_text="Geological age")
    rock_type = models.CharField(max_length=50, blank=True, help_text="Carbonate, Sandstone, Shale")
    hardness = models.CharField(max_length=20, blank=True, help_text="Soft, Medium, Hard")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "formation_types"
        ordering = ["name"]
        verbose_name = "Formation Type"
        verbose_name_plural = "Formation Types"

    def __str__(self):
        return self.name


class IADCCode(models.Model):
    """IADC classification codes."""

    class BitType(models.TextChoices):
        FC = "FC", "Fixed Cutter (PDC)"
        RC = "RC", "Roller Cone"
        MT = "MT", "Mill Tooth"
        TCI = "TCI", "Tungsten Carbide Insert"

    code = models.CharField(max_length=10, unique=True)
    bit_type = models.CharField(max_length=5, choices=BitType.choices)
    body_material = models.CharField(max_length=1, blank=True, help_text="M, S, D")
    formation_hardness = models.CharField(max_length=1, blank=True, help_text="1-8")
    cutter_type = models.CharField(max_length=1, blank=True, help_text="1-4")
    profile = models.CharField(max_length=1, blank=True, help_text="1-4")
    series = models.CharField(max_length=1, blank=True, help_text="1-8")
    type_code = models.CharField(max_length=1, blank=True, help_text="1-4")
    bearing = models.CharField(max_length=1, blank=True, help_text="1-7")
    feature = models.CharField(max_length=1, blank=True, help_text="A-Z")
    description = models.CharField(max_length=200)
    formation_description = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "iadc_codes"
        ordering = ["bit_type", "code"]
        verbose_name = "IADC Code"
        verbose_name_plural = "IADC Codes"

    def __str__(self):
        return f"{self.code} - {self.description}"


class SpecialTechnology(models.Model):
    """Special technologies that can be applied to designs."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "special_technologies"
        ordering = ["name"]
        verbose_name = "Special Technology"
        verbose_name_plural = "Special Technologies"

    def __str__(self):
        return self.name


class UpperSectionType(models.Model):
    """Upper section/shank types."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    can_replace_in_ksa = models.BooleanField(
        default=True,
        verbose_name="Can Replace in KSA",
        help_text="Whether this upper section type can be replaced/repaired in Saudi Arabia"
    )
    remarks = models.TextField(blank=True, help_text="Additional notes about this type")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "upper_section_types"
        ordering = ["name"]
        verbose_name = "Upper Section Type"
        verbose_name_plural = "Upper Section Types"

    def __str__(self):
        return self.name


class PocketShape(models.Model):
    """Pocket shapes for cutter pockets."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    notes = models.TextField(
        blank=True,
        verbose_name="Technical Notes",
        help_text="Additional technical information about this shape"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "pocket_shapes"
        ordering = ["name"]
        verbose_name = "Pocket Shape"
        verbose_name_plural = "Pocket Shapes"

    def __str__(self):
        return self.name


class PocketSize(models.Model):
    """Pocket sizes for cutter pockets."""
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Size Code",
        help_text="Pocket size code (e.g., 1608, 1613, 19)"
    )
    display_name = models.CharField(
        max_length=50,
        verbose_name="Display Name",
        help_text="Human-readable name"
    )
    diameter_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Diameter (mm)",
        help_text="Pocket diameter in millimeters"
    )
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "pocket_sizes"
        ordering = ["sort_order", "code"]
        verbose_name = "Pocket Size"
        verbose_name_plural = "Pocket Sizes"

    def __str__(self):
        return self.display_name


# =============================================================================
# Connection and Breaker Slot Models
# =============================================================================

class Connection(models.Model):
    """Connection specifications."""
    mat_no = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="MAT No.",
        help_text="Connection material number"
    )
    connection_type = models.ForeignKey(
        ConnectionType,
        on_delete=models.PROTECT,
        related_name="connections",
        verbose_name="Type"
    )
    connection_size = models.ForeignKey(
        ConnectionSize,
        on_delete=models.PROTECT,
        related_name="connections",
        verbose_name="Size"
    )
    upper_section_type = models.ForeignKey(
        UpperSectionType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="connections",
        verbose_name="Upper Section Type"
    )
    special_features = models.TextField(
        blank=True,
        verbose_name="Special Features",
        help_text="Any special features or modifications"
    )
    can_replace_in_ksa = models.BooleanField(
        default=True,
        verbose_name="Can Replace in KSA",
        help_text="Whether this connection can be replaced/repaired in Saudi Arabia"
    )
    remarks = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "connections"
        ordering = ["mat_no"]
        verbose_name = "Connection"
        verbose_name_plural = "Connections"

    def __str__(self):
        return f"{self.mat_no} - {self.connection_type.code} {self.connection_size.size_inches}"


class BreakerSlot(models.Model):
    """Breaker slot specifications."""

    class Material(models.TextChoices):
        ALLOY = "ALLOY", "Alloy Steel"
        AISI_4140 = "4140", "AISI 4140 Steel"
        AISI_4145 = "4145", "AISI 4145H Steel"
        AISI_4340 = "4340", "AISI 4340 Steel"
        CRMO = "CrMo", "Chrome-Moly Steel"
        OTHER = "OTHER", "Other"

    mat_no = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="MAT No.",
        help_text="Breaker slot material number"
    )
    slot_width = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Slot Width (mm)",
        help_text="Width of the slot opening in millimeters"
    )
    slot_depth = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Slot Depth (mm)",
        help_text="Depth of the slot in millimeters"
    )
    slot_length = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Slot Length (mm)",
        help_text="Length of the slot along the shank in millimeters"
    )
    material = models.CharField(
        max_length=10,
        choices=Material.choices,
        default=Material.ALLOY,
        verbose_name="Material",
        help_text="Material of the breaker slot / shank"
    )
    hardness = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Hardness (HRC)",
        help_text="Rockwell hardness rating (e.g., 28-32 HRC)"
    )
    compatible_sizes = models.ManyToManyField(
        "workorders.BitSize",
        blank=True,
        related_name="breaker_slots",
        verbose_name="Compatible Bit Sizes",
        help_text="Bit sizes this breaker slot is compatible with"
    )
    remarks = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "breaker_slots"
        ordering = ["mat_no"]
        verbose_name = "Breaker Slot"
        verbose_name_plural = "Breaker Slots"

    def __str__(self):
        return f"{self.mat_no} ({self.slot_width}x{self.slot_depth}mm)"


# =============================================================================
# Design Model
# =============================================================================

class Design(models.Model):
    """
    Drill bit design master.
    Contains specifications for drill bit designs.
    """

    class Category(models.TextChoices):
        FC = "FC", "Fixed Cutter"
        MT = "MT", "Mill Tooth"
        TCI = "TCI", "Tri Cone Inserts"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        OBSOLETE = "OBSOLETE", "Obsolete"

    class BodyMaterial(models.TextChoices):
        MATRIX = "M", "Matrix"
        STEEL = "S", "Steel"
        NA = "", "N/A"

    class OrderLevel(models.TextChoices):
        LEVEL_3 = "3", "Level 3 - No cutters, upper section separate"
        LEVEL_4 = "4", "Level 4 - No cutters, upper section welded/machined"
        LEVEL_5 = "5", "Level 5 - With cutters brazed"
        LEVEL_6 = "6", "Level 6 - Painted and ready for use"

    # Primary Identifiers
    mat_no = models.CharField(
        max_length=20,
        unique=True,
        default="",
        verbose_name="MAT No.",
        help_text="HDBS Material Number (SAP)"
    )
    hdbs_type = models.CharField(
        max_length=50,
        default="",
        verbose_name="HDBS Type",
        help_text="Internal Halliburton type code (e.g., GT65RHS)"
    )
    smi_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="SMI Type",
        help_text="Client-facing type (may differ from HDBS Type)"
    )
    ardt_item_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="ARDT Item No.",
        help_text="ARDT ERP item number"
    )
    ref_mat_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Ref MAT No.",
        help_text="Parent/reference MAT number"
    )

    # Classification
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.FC)
    series = models.CharField(max_length=10, blank=True, help_text="Product series (GT, HD, MM, EM, etc.)")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    order_level = models.CharField(max_length=5, choices=OrderLevel.choices, blank=True, verbose_name="Order Level")

    # Size and Specifications
    size = models.ForeignKey(
        "workorders.BitSize",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Size"
    )
    size_legacy = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        db_column="size_decimal",
        help_text="Legacy: Use size FK instead"
    )
    no_of_blades = models.PositiveIntegerField(null=True, blank=True, verbose_name="No. of Blades")
    body_material = models.CharField(max_length=1, choices=BodyMaterial.choices, blank=True, verbose_name="Body Material")
    cutter_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Cutter Size Grade",
        help_text="Cutter size grade (from HDBS Type 2nd digit)"
    )

    # Gage Specifications
    gage_length = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Gage Length (in)",
        help_text="Gage length in inches (positive values only)"
    )
    gage_relief = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Gage Relief (thou)",
        help_text="Gage relief in inch thou (positive values only)"
    )

    # Nozzle and Port Specifications
    nozzle_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="Nozzle Count")
    nozzle_config = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nozzle Configuration",
        help_text="Layout of nozzles (reference Milling drawing)"
    )
    nozzle_bore_size = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Nozzle Bore Size",
        help_text="Fixed bore size in design (e.g., 12/32, 14/32)"
    )
    port_count = models.PositiveIntegerField(null=True, blank=True, verbose_name="Port Count")
    port_size = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Port Size",
        help_text="Port size - positive values only"
    )
    tfa = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="TFA (sq.in)",
        help_text="Total Flow Area - positive values only"
    )

    # Connection References
    connection_ref = models.ForeignKey(
        Connection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="designs",
        verbose_name="Connection",
        help_text="Select a pre-defined connection from the connections table"
    )
    connection_mat_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Connection MAT No.",
        help_text="Material number of the connection"
    )
    connection_type_ref = models.ForeignKey(
        ConnectionType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="designs",
        verbose_name="Connection Type"
    )
    connection_size_ref = models.ForeignKey(
        ConnectionSize,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="designs",
        verbose_name="Connection Size"
    )
    upper_section_type = models.ForeignKey(
        UpperSectionType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="designs",
        verbose_name="Upper Section Type",
        help_text="Type of upper section/shank (some cannot be replaced in KSA)"
    )
    breaker_slot = models.ForeignKey(
        BreakerSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="designs",
        verbose_name="Breaker Slot",
        help_text="Breaker slot specification for this design"
    )

    # Other References
    application_ref = models.ForeignKey(
        Application,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="designs",
        verbose_name="Application"
    )
    formation_type_ref = models.ForeignKey(
        FormationType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="designs",
        verbose_name="Formation Type"
    )
    iadc_code_ref = models.ForeignKey(
        IADCCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="designs",
        verbose_name="IADC Code"
    )

    # Special Features
    special_technologies = models.ManyToManyField(
        SpecialTechnology,
        blank=True,
        related_name="designs",
        verbose_name="Special Technologies",
        help_text="Select one or more special technologies (Cerebro Puck, Torpedo, etc.)"
    )
    erosion_sleeve = models.BooleanField(
        default=False,
        verbose_name="Erosion Sleeve",
        help_text="Has erosion sleeve protection"
    )

    # Pocket Layout Fields
    pocket_rows_count = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Pocket Rows Count",
        help_text="Number of pocket rows (1-4)"
    )
    total_pockets_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Total Pockets Count",
        help_text="Total number of cutter pockets in the design"
    )
    pocket_layout_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Pocket Layout Number",
        help_text="Identifier for cloning pocket layouts between similar designs"
    )

    # Documents
    drawing_file = models.FileField(upload_to="designs/drawings/", null=True, blank=True)
    specification_file = models.FileField(upload_to="designs/specs/", null=True, blank=True)
    milling_drawing = models.FileField(
        upload_to="designs/milling/",
        null=True,
        blank=True,
        verbose_name="Milling Drawing",
        help_text="PDF of milling/nozzle layout drawing"
    )

    # Revision
    revision = models.CharField(max_length=10, blank=True)
    revision_date = models.DateField(null=True, blank=True)

    # Ownership
    designed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="designed_bits"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_designs"
    )

    # Notes
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    # Legacy fields (kept for backward compatibility)
    code = models.CharField(max_length=50, blank=True, help_text="Legacy: Use mat_no instead")
    name = models.CharField(max_length=200, blank=True, help_text="Legacy: Use hdbs_type instead")
    bit_type = models.CharField(max_length=20, blank=True, help_text="Legacy: Use category instead")
    blade_count = models.IntegerField(null=True, blank=True, help_text="Legacy: Use no_of_blades instead")
    cone_count = models.IntegerField(null=True, blank=True, help_text="Legacy: For RC bits")
    connection_type = models.CharField(max_length=50, blank=True, help_text="Legacy: Use connection_type_ref FK")
    connection_size = models.CharField(max_length=20, blank=True, help_text="Legacy: Use connection_size_ref FK")
    formation_type = models.CharField(max_length=100, blank=True, help_text="Legacy: Use formation_type_ref FK")
    application = models.CharField(max_length=100, blank=True, help_text="Legacy: Use application_ref FK")
    iadc_code = models.CharField(max_length=20, blank=True, help_text="Legacy: Use iadc_code_ref FK instead")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="designs_created"
    )

    class Meta:
        db_table = "designs"
        ordering = ["category", "series", "hdbs_type"]
        verbose_name = "Design"
        verbose_name_plural = "Designs"

    def __str__(self):
        return f"{self.mat_no} - {self.hdbs_type}"

    def get_status_display(self):
        return dict(self.Status.choices).get(self.status, self.status)


# =============================================================================
# Pocket Configuration Models
# =============================================================================

class DesignPocketConfig(models.Model):
    """Configuration for a group of pockets with same specifications."""

    class LengthType(models.TextChoices):
        LONG = "L", "Long"
        MEDIUM = "M", "Medium"
        SHORT = "S", "Short"

    design = models.ForeignKey(
        Design,
        on_delete=models.CASCADE,
        related_name="pocket_configs"
    )
    order = models.PositiveIntegerField(verbose_name="Order", help_text="Display order (1, 2, 3...)")
    row_number = models.PositiveIntegerField(
        default=1,
        verbose_name="Row Number",
        help_text="Which row this configuration belongs to (1-4)"
    )
    pocket_shape = models.ForeignKey(
        PocketShape,
        on_delete=models.PROTECT,
        related_name="design_configs"
    )
    pocket_size = models.ForeignKey(
        PocketSize,
        on_delete=models.PROTECT,
        related_name="design_configs"
    )
    length_type = models.CharField(
        max_length=1,
        choices=LengthType.choices,
        default=LengthType.LONG,
        verbose_name="L/M/S",
        help_text="Long, Medium, or Short"
    )
    count = models.PositiveIntegerField(
        verbose_name="Count",
        help_text="Number of pockets with this configuration"
    )
    color_code = models.CharField(
        max_length=7,
        blank=True,
        verbose_name="Color Code",
        help_text="Hex color for visual identification (e.g., #FF5733)"
    )

    class Meta:
        db_table = "design_pocket_configs"
        ordering = ["design", "order"]
        unique_together = ["design", "order"]
        verbose_name = "Design Pocket Config"
        verbose_name_plural = "Design Pocket Configs"

    def __str__(self):
        return f"{self.design.mat_no} - Config {self.order} ({self.pocket_size.display_name})"


class DesignPocket(models.Model):
    """Individual pocket positions on a design."""

    class BladeLocation(models.TextChoices):
        CONE = "C", "Cone"
        NOSE = "N", "Nose"
        TAPER = "T", "Taper"
        SHOULDER = "S", "Shoulder"
        GAGE = "G", "Gage"

    design = models.ForeignKey(
        Design,
        on_delete=models.CASCADE,
        related_name="pockets"
    )
    pocket_config = models.ForeignKey(
        DesignPocketConfig,
        on_delete=models.PROTECT,
        related_name="pockets",
        verbose_name="Pocket Configuration"
    )
    blade_number = models.PositiveIntegerField(
        verbose_name="Blade",
        help_text="Blade number (1 to no_of_blades)"
    )
    row_number = models.PositiveIntegerField(
        default=1,
        verbose_name="Row",
        help_text="Row number (1 to pocket_rows_count)"
    )
    position_in_row = models.PositiveIntegerField(
        verbose_name="Position in Row",
        help_text="Position within this blade and row"
    )
    position_in_blade = models.PositiveIntegerField(
        verbose_name="Position in Blade",
        help_text="Sequential position within entire blade (across all rows)"
    )
    blade_location = models.CharField(
        max_length=1,
        choices=BladeLocation.choices,
        null=True,
        blank=True,
        verbose_name="Blade Location",
        help_text="Location zone on blade: Cone, Nose, Taper, Shoulder, Gage"
    )
    engagement_order = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Engagement Order",
        help_text="Full engagement sequence order (set in separate tab)"
    )
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "design_pockets"
        ordering = ["design", "blade_number", "row_number", "position_in_row"]
        unique_together = ["design", "blade_number", "row_number", "position_in_row"]
        verbose_name = "Design Pocket"
        verbose_name_plural = "Design Pockets"

    def __str__(self):
        return f"{self.design.mat_no} - B{self.blade_number} R{self.row_number} P{self.position_in_row}"


# =============================================================================
# BOM Models
# =============================================================================

class BOM(models.Model):
    """Bill of Materials for designs."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        OBSOLETE = "OBSOLETE", "Obsolete"

    design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name="boms")
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    revision = models.CharField(max_length=10, default="A")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    effective_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_boms"
    )

    class Meta:
        db_table = "boms"
        ordering = ["design", "code"]
        verbose_name = "Bill of Materials"
        verbose_name_plural = "Bills of Materials"

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def total_cost(self):
        """Calculate total BOM cost."""
        return sum(line.line_cost for line in self.lines.all())


class BOMLine(models.Model):
    """Individual items in a BOM."""

    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name="lines")
    line_number = models.IntegerField()

    inventory_item = models.ForeignKey(
        "inventory.InventoryItem",
        on_delete=models.PROTECT,
        related_name="bom_lines"
    )

    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=20, blank=True)

    # Cost (cached from inventory item)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    # Position (for assembly)
    position = models.CharField(max_length=50, blank=True, help_text="Assembly position")

    # Options
    is_optional = models.BooleanField(default=False)
    is_phantom = models.BooleanField(default=False, help_text="Sub-assembly to be exploded")

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "bom_lines"
        ordering = ["bom", "line_number"]
        unique_together = ["bom", "line_number"]
        verbose_name = "BOM Line"
        verbose_name_plural = "BOM Lines"

    def __str__(self):
        return f"{self.bom.code} - Line {self.line_number}"

    @property
    def line_cost(self):
        return float(self.quantity) * float(self.unit_cost)


class DesignCutterLayout(models.Model):
    """Cutter layout positions for FC bit designs."""

    design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name="cutter_layouts")
    blade_number = models.IntegerField()
    position_number = models.IntegerField()

    # Cutter specifications
    cutter_type = models.CharField(max_length=50)
    cutter_size = models.DecimalField(max_digits=6, decimal_places=2, help_text="mm")
    cutter_grade = models.CharField(max_length=50, blank=True)

    # Position
    radial_position = models.DecimalField(max_digits=8, decimal_places=3, help_text="mm from center")
    backrake = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="degrees")
    siderake = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="degrees")
    exposure = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="mm")

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "design_cutter_layouts"
        ordering = ["design", "blade_number", "position_number"]
        unique_together = ["design", "blade_number", "position_number"]
        verbose_name = "Cutter Layout"
        verbose_name_plural = "Cutter Layouts"

    def __str__(self):
        return f"{self.design.code} - Blade {self.blade_number}, Pos {self.position_number}"
