"""
ARDT FMS - Technology Models
Version: 5.5

Tables:
- connection_types (P2) - API connection types reference
- connection_sizes (P2) - Connection sizes reference
- formation_types (P2) - Geological formation types reference
- applications (P2) - Drilling application types reference
- iadc_codes (P2) - IADC classification codes reference
- upper_section_types (P2) - Upper section types (some can't be replaced in KSA)
- connections (P2) - Connection inventory
- breaker_slots (P2) - Breaker slot specifications
- designs (P1)
- boms (P1)
- bom_lines (P1)
- design_cutter_layouts (P1)
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


# =============================================================================
# BIT REFERENCE TABLES (Moved from workorders)
# =============================================================================


class BitSize(models.Model):
    """
    Reference table for standard bit sizes.
    Simple list: 8 1/2", 12 1/4", etc.
    """
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="e.g., '8.500'"
    )
    size_decimal = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        help_text="Size in decimal inches (e.g., 8.500)"
    )
    size_display = models.CharField(
        max_length=20,
        help_text="Display format (e.g., '8 1/2\"')"
    )
    size_inches = models.CharField(
        max_length=20,
        help_text="Fraction format (e.g., '8 1/2')"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional remarks or description"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "bit_sizes"
        ordering = ["size_decimal"]
        verbose_name = "Bit Size"
        verbose_name_plural = "Bit Sizes"

    def __str__(self):
        return self.size_display


class HDBSType(models.Model):
    """
    HDBS Type - Internal Halliburton naming for bit types.
    One HDBS type can have multiple SMI names (1-to-many).
    One HDBS type can work with multiple sizes (M2M).
    """
    hdbs_name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="HDBS Name",
        help_text="Internal HDBS type name (e.g., GT65RHS)"
    )
    sizes = models.ManyToManyField(
        'BitSize',
        blank=True,
        related_name="hdbs_types",
        verbose_name="Compatible Sizes",
        help_text="Bit sizes this type is available in"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description or remarks"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "hdbs_types"
        ordering = ["hdbs_name"]
        verbose_name = "HDBS Type"
        verbose_name_plural = "HDBS Types"

    def __str__(self):
        return self.hdbs_name


class SMIType(models.Model):
    """
    SMI Type - Client-facing naming for bit types.
    Linked to HDBS Type and optionally to a specific Size.
    Different sizes of the same HDBS type can have different SMI names.
    """
    smi_name = models.CharField(
        max_length=50,
        verbose_name="SMI Name",
        help_text="Client-facing type name (e.g., GT65RHs-1)"
    )
    hdbs_type = models.ForeignKey(
        'HDBSType',
        on_delete=models.CASCADE,
        related_name="smi_types",
        verbose_name="HDBS Type",
        help_text="The internal HDBS type this SMI name maps to"
    )
    size = models.ForeignKey(
        'BitSize',
        on_delete=models.CASCADE,
        related_name="smi_types",
        verbose_name="Size",
        null=True,
        blank=True,
        help_text="Specific size for this SMI name (leave blank for all sizes)"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description or remarks"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "smi_types"
        ordering = ["hdbs_type__hdbs_name", "size__size_decimal", "smi_name"]
        verbose_name = "SMI Type"
        verbose_name_plural = "SMI Types"
        # Same SMI name can exist for same HDBS but different sizes
        unique_together = [["smi_name", "hdbs_type", "size"]]

    def __str__(self):
        if self.size:
            return f"{self.smi_name} ({self.hdbs_type.hdbs_name} - {self.size.size_display})"
        return f"{self.smi_name} ({self.hdbs_type.hdbs_name})"


class BitType(models.Model):
    """
    DEPRECATED - Legacy reference table for bit product types.
    Kept for backward compatibility. Use HDBSType and SMIType instead.
    """
    class Category(models.TextChoices):
        FC = "FC", "Fixed Cutter"
        MT = "MT", "Mill Tooth"
        TCI = "TCI", "Tri Cone Inserts"

    class BodyMaterial(models.TextChoices):
        MATRIX = "M", "Matrix"
        STEEL = "S", "Steel"
        NA = "", "N/A"

    class OrderLevel(models.TextChoices):
        LEVEL_3 = "3", "Level 3 - No cutters, upper section separate"
        LEVEL_4 = "4", "Level 4 - No cutters, upper section welded/machined"
        LEVEL_5 = "5", "Level 5 - With cutters brazed"
        LEVEL_6 = "6", "Level 6 - Painted and ready for use"

    # Core fields
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Model code (e.g., 'GT65RHS')"
    )
    name = models.CharField(max_length=100, blank=True)
    series = models.CharField(
        max_length=20,
        blank=True,
        help_text="Series (GT, HD, MM, FX, EM, etc.)"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # Phase 2 fields
    category = models.CharField(
        max_length=10,
        choices=Category.choices,
        default=Category.FC,
        help_text="FC=Fixed Cutter, MT=Mill Tooth, TCI=Tri Cone Inserts"
    )
    smi_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="SMI/Client-facing name (e.g., 'GT65RHs-1')"
    )
    hdbs_name = models.CharField(
        max_length=50,
        blank=True,
        help_text="Internal HDBS name"
    )
    hdbs_mn = models.CharField(
        max_length=20,
        blank=True,
        help_text="HDBS SAP Material Number"
    )
    ref_hdbs_mn = models.CharField(
        max_length=20,
        blank=True,
        help_text="Parent/Reference HDBS Material Number"
    )
    ardt_item_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="ARDT ERP Item Number"
    )
    body_material = models.CharField(
        max_length=1,
        choices=BodyMaterial.choices,
        default=BodyMaterial.NA,
        blank=True,
        help_text="Body material: M=Matrix, S=Steel"
    )
    no_of_blades = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of blades (FC only)"
    )
    cutter_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Cutter size in mm (FC only)"
    )
    gage_length = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Gage length in inches (FC only)"
    )
    order_level = models.CharField(
        max_length=5,
        choices=OrderLevel.choices,
        blank=True,
        help_text="JV Production Level: 3-6"
    )
    size = models.ForeignKey(
        'BitSize',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="bit_types",
        help_text="Standard bit size"
    )

    class Meta:
        db_table = "bit_types"  # Keep same table name
        ordering = ["category", "series", "smi_name", "code"]
        verbose_name = "Bit Type"
        verbose_name_plural = "Bit Types"

    def __str__(self):
        return f"{self.code} - {self.name}"


# =============================================================================
# REFERENCE DATA MODELS (Phase 2)
# =============================================================================


class ConnectionType(models.Model):
    """
    API connection types for drill bits.
    Examples: API-REG, API-IF, API-FH, HT, XT, PAC, DS
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "connection_types"
        ordering = ['code']
        verbose_name = "Connection Type"
        verbose_name_plural = "Connection Types"

    def __str__(self):
        return f"{self.code} - {self.name}"


class ConnectionSize(models.Model):
    """
    Connection sizes for drill bits.
    Examples: 2 3/8", 4 1/2", NC26, NC38
    """
    code = models.CharField(max_length=20, unique=True)
    size_inches = models.CharField(max_length=20)
    size_decimal = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "connection_sizes"
        ordering = ['size_decimal']
        verbose_name = "Connection Size"
        verbose_name_plural = "Connection Sizes"

    def __str__(self):
        return self.size_inches


class FormationType(models.Model):
    """
    Geological formation types - Saudi Arabia focus.
    Examples: Arab-D, Khuff, Unayzah, Jauf, Qusaiba
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    age = models.CharField(max_length=50, blank=True, help_text="Geological age")
    rock_type = models.CharField(max_length=50, blank=True, help_text="Carbonate, Sandstone, Shale")
    hardness = models.CharField(max_length=20, blank=True, help_text="Soft, Medium, Hard")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "formation_types"
        ordering = ['name']
        verbose_name = "Formation Type"
        verbose_name_plural = "Formation Types"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Application(models.Model):
    """
    Drilling application types.
    Examples: Vertical, Directional, Horizontal, RSS, Motor
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "applications"
        ordering = ['name']
        verbose_name = "Application"
        verbose_name_plural = "Applications"

    def __str__(self):
        return f"{self.code} - {self.name}"


class SpecialTechnology(models.Model):
    """
    Special technologies available for drill bit designs.
    Includes: Erosion Sleeve, Crush & Shear, Cerebro Puck, Torpedo, etc.
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "special_technologies"
        ordering = ['name']
        verbose_name = "Special Technology"
        verbose_name_plural = "Special Technologies"

    def __str__(self):
        return self.name


class UpperSectionType(models.Model):
    """
    Upper section (shank/connection) types for PDC bits.
    Some types cannot be replaced/repaired in KSA.
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    can_replace_in_ksa = models.BooleanField(
        default=True,
        verbose_name='Can Replace in KSA',
        help_text='Whether this upper section type can be replaced/repaired in Saudi Arabia'
    )
    remarks = models.TextField(blank=True, help_text='Additional notes about this type')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "upper_section_types"
        ordering = ['name']
        verbose_name = "Upper Section Type"
        verbose_name_plural = "Upper Section Types"

    def __str__(self):
        suffix = "" if self.can_replace_in_ksa else " (Cannot replace in KSA)"
        return f"{self.name}{suffix}"


class Connection(models.Model):
    """
    Connection inventory - tracks specific connections with their properties.
    Used to select pre-defined connections for bit designs.
    """
    mat_no = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='MAT No.',
        help_text='Connection material number'
    )
    connection_type = models.ForeignKey(
        'ConnectionType',
        on_delete=models.PROTECT,
        verbose_name='Type',
        related_name='connections'
    )
    connection_size = models.ForeignKey(
        'ConnectionSize',
        on_delete=models.PROTECT,
        verbose_name='Size',
        related_name='connections'
    )
    special_features = models.TextField(
        blank=True,
        verbose_name='Special Features',
        help_text='Any special features or modifications'
    )
    can_replace_in_ksa = models.BooleanField(
        default=True,
        verbose_name='Can Replace in KSA',
        help_text='Whether this connection can be replaced/repaired in Saudi Arabia'
    )
    upper_section_type = models.ForeignKey(
        'UpperSectionType',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Upper Section Type',
        related_name='connections'
    )
    remarks = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "connections"
        ordering = ['mat_no']
        verbose_name = "Connection"
        verbose_name_plural = "Connections"

    def __str__(self):
        suffix = "" if self.can_replace_in_ksa else " (Cannot replace in KSA)"
        return f"{self.mat_no} - {self.connection_type.code} {self.connection_size.size_inches}{suffix}"


class BreakerSlot(models.Model):
    """
    Bit Breaker Slot specifications.
    The breaker slot is a recess on the shank used for gripping with a bit breaker tool
    during make-up and break-out operations.
    Can be used across multiple bit designs of compatible sizes.
    """

    class Material(models.TextChoices):
        ALLOY_STEEL = "ALLOY", "Alloy Steel"
        STEEL_4140 = "4140", "AISI 4140 Steel"
        STEEL_4145 = "4145", "AISI 4145H Steel"
        STEEL_4340 = "4340", "AISI 4340 Steel"
        CHROME_MOLY = "CrMo", "Chrome-Moly Steel"
        OTHER = "OTHER", "Other"

    mat_no = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='MAT No.',
        help_text='Breaker slot material number'
    )
    slot_width = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        verbose_name='Slot Width (in)',
        help_text='Width of the slot opening in inches'
    )
    slot_depth = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        verbose_name='Slot Depth (in)',
        help_text='Depth of the slot in inches'
    )
    slot_length = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name='Slot Length (in)',
        help_text='Length of the slot along the shank in inches'
    )
    material = models.CharField(
        max_length=10,
        choices=Material.choices,
        default=Material.ALLOY_STEEL,
        verbose_name='Material',
        help_text='Material of the breaker slot / shank'
    )
    hardness = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Hardness (HRC)',
        help_text='Rockwell hardness rating (e.g., 28-32 HRC)'
    )
    compatible_sizes = models.ManyToManyField(
        'BitSize',
        blank=True,
        verbose_name='Compatible Bit Sizes',
        related_name='breaker_slots',
        help_text='Bit sizes this breaker slot is compatible with'
    )
    remarks = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "breaker_slots"
        ordering = ['mat_no']
        verbose_name = "Breaker Slot"
        verbose_name_plural = "Breaker Slots"

    def __str__(self):
        return f"{self.mat_no} - {self.slot_width}x{self.slot_depth}\" ({self.get_material_display()})"


class IADCCode(models.Model):
    """
    IADC classification codes for drill bits.
    PDC: M433, S423, etc. (Body-Formation-CutterSize-Profile)
    Roller Cone: 517, 617, etc. (Series-Type-Bearing-Feature)
    """
    BIT_TYPE_CHOICES = [
        ('FC', 'Fixed Cutter (PDC)'),
        ('RC', 'Roller Cone'),
        ('MT', 'Mill Tooth'),
        ('TCI', 'Tungsten Carbide Insert'),
    ]

    code = models.CharField(max_length=10, unique=True)
    bit_type = models.CharField(max_length=5, choices=BIT_TYPE_CHOICES)

    # PDC specific fields
    body_material = models.CharField(max_length=1, blank=True, help_text="M, S, D")
    formation_hardness = models.CharField(max_length=1, blank=True, help_text="1-8")
    cutter_type = models.CharField(max_length=1, blank=True, help_text="1-4")
    profile = models.CharField(max_length=1, blank=True, help_text="1-4")

    # Roller Cone specific fields
    series = models.CharField(max_length=1, blank=True, help_text="1-8")
    type_code = models.CharField(max_length=1, blank=True, help_text="1-4")
    bearing = models.CharField(max_length=1, blank=True, help_text="1-7")
    feature = models.CharField(max_length=1, blank=True, help_text="A-Z")

    description = models.CharField(max_length=200)
    formation_description = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "iadc_codes"
        ordering = ['bit_type', 'code']
        verbose_name = 'IADC Code'
        verbose_name_plural = 'IADC Codes'

    def __str__(self):
        return f"{self.code} - {self.description}"


# =============================================================================
# DESIGN MODELS
# =============================================================================


class Design(models.Model):
    """
    Bit design specification.
    Updated for Phase 2 with FK relations to reference tables.
    Unique constraint: hdbs_type + size (unique together)
    """

    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY CHOICES
    # ═══════════════════════════════════════════════════════════════════════
    class Category(models.TextChoices):
        FC = "FC", "Fixed Cutter"
        MT = "MT", "Mill Tooth"
        TCI = "TCI", "Tri Cone Inserts"

    class BodyMaterial(models.TextChoices):
        MATRIX = "M", "Matrix"
        STEEL = "S", "Steel"
        NA = "", "N/A"

    class OrderLevel(models.TextChoices):
        LEVEL_3 = "3", "Level 3 - No cutters, upper section separate"
        LEVEL_4 = "4", "Level 4 - No cutters, upper section welded/machined"
        LEVEL_5 = "5", "Level 5 - With cutters brazed"
        LEVEL_6 = "6", "Level 6 - Painted and ready for use"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        OBSOLETE = "OBSOLETE", "Obsolete"

    # ═══════════════════════════════════════════════════════════════════════
    # IDENTITY
    # ═══════════════════════════════════════════════════════════════════════
    mat_no = models.CharField(
        max_length=20,
        unique=True,
        default='',
        verbose_name='MAT No.',
        help_text='HDBS Material Number (SAP)'
    )
    hdbs_type = models.CharField(
        max_length=50,
        default='',
        verbose_name='HDBS Type',
        help_text='Internal Halliburton type code (e.g., GT65RHS)'
    )
    smi_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='SMI Type',
        help_text='Client-facing type (may differ from HDBS Type)'
    )
    ref_mat_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Ref MAT No.',
        help_text='Parent/reference MAT number'
    )
    ardt_item_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='ARDT Item No.',
        help_text='ARDT ERP item number'
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY & SIZE
    # ═══════════════════════════════════════════════════════════════════════
    category = models.CharField(
        max_length=10,
        choices=Category.choices,
        default=Category.FC
    )
    size = models.ForeignKey(
        'BitSize',
        on_delete=models.PROTECT,
        verbose_name='Size',
        null=True,
        blank=True
    )
    series = models.CharField(
        max_length=10,
        blank=True,
        help_text='Product series (GT, HD, MM, EM, etc.)'
    )

    # ═══════════════════════════════════════════════════════════════════════
    # TECHNICAL SPECS (FC Only)
    # ═══════════════════════════════════════════════════════════════════════
    body_material = models.CharField(
        max_length=1,
        choices=BodyMaterial.choices,
        blank=True,
        verbose_name='Body Material'
    )
    no_of_blades = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='No. of Blades'
    )
    total_pockets_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Total Pockets Count',
        help_text='Total number of cutter pockets in the design'
    )
    pocket_rows_count = models.PositiveIntegerField(
        default=1,
        verbose_name='Pocket Rows Count',
        help_text='Number of pocket rows (1-4)',
        validators=[MinValueValidator(1)]
    )
    pocket_layout_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Pocket Layout Number',
        help_text='Identifier for cloning pocket layouts between similar designs'
    )
    cutter_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Cutter Size Grade',
        help_text='Cutter size grade (from HDBS Type 2nd digit)'
    )
    gage_length = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name='Gage Length (in)',
        help_text='Gage length in inches (positive values only)',
        validators=[MinValueValidator(0)]
    )
    gage_relief = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='Gage Relief (thou)',
        help_text='Gage relief in inch thou (positive values only)',
        validators=[MinValueValidator(0)]
    )
    erosion_sleeve = models.BooleanField(
        default=False,
        verbose_name='Erosion Sleeve',
        help_text='Has erosion sleeve protection'
    )

    # ═══════════════════════════════════════════════════════════════════════
    # NOZZLES
    # ═══════════════════════════════════════════════════════════════════════
    nozzle_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Nozzle Count'
    )
    nozzle_bore_size = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Nozzle Bore Size',
        help_text='Fixed bore size in design (e.g., 12/32, 14/32)'
    )
    nozzle_config = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Nozzle Configuration',
        help_text='Layout of nozzles (reference Milling drawing)'
    )
    milling_drawing = models.FileField(
        upload_to="designs/milling/",
        null=True,
        blank=True,
        verbose_name='Milling Drawing',
        help_text='PDF of milling/nozzle layout drawing'
    )
    tfa = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name='TFA (sq.in)',
        help_text='Total Flow Area - positive values only',
        validators=[MinValueValidator(0)]
    )

    # ═══════════════════════════════════════════════════════════════════════
    # PORTS
    # ═══════════════════════════════════════════════════════════════════════
    port_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Port Count'
    )
    port_size = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name='Port Size',
        help_text='Port size - positive values only',
        validators=[MinValueValidator(0)]
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CONNECTION (FK to reference tables)
    # ═══════════════════════════════════════════════════════════════════════
    connection_mat_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Connection MAT No.',
        help_text='Material number of the connection'
    )
    upper_section_type = models.ForeignKey(
        'UpperSectionType',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Upper Section Type',
        related_name='designs',
        help_text='Type of upper section/shank (some cannot be replaced in KSA)'
    )
    connection_type_ref = models.ForeignKey(
        'ConnectionType',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Connection Type',
        related_name='designs'
    )
    connection_size_ref = models.ForeignKey(
        'ConnectionSize',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Connection Size',
        related_name='designs'
    )
    connection_ref = models.ForeignKey(
        'Connection',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Connection',
        related_name='designs',
        help_text='Select a pre-defined connection from the connections table'
    )

    # ═══════════════════════════════════════════════════════════════════════
    # BREAKER SLOT
    # ═══════════════════════════════════════════════════════════════════════
    breaker_slot = models.ForeignKey(
        'BreakerSlot',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Breaker Slot',
        related_name='designs',
        help_text='Select a breaker slot specification for this design'
    )

    # ═══════════════════════════════════════════════════════════════════════
    # APPLICATION (FK to reference tables)
    # ═══════════════════════════════════════════════════════════════════════
    formation_type_ref = models.ForeignKey(
        'FormationType',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Formation Type',
        related_name='designs'
    )
    application_ref = models.ForeignKey(
        'Application',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Application',
        related_name='designs'
    )
    iadc_code_ref = models.ForeignKey(
        'IADCCode',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='IADC Code',
        related_name='designs'
    )

    # ═══════════════════════════════════════════════════════════════════════
    # SPECIAL TECHNOLOGIES (M2M)
    # ═══════════════════════════════════════════════════════════════════════
    special_technologies = models.ManyToManyField(
        'SpecialTechnology',
        blank=True,
        verbose_name='Special Technologies',
        related_name='designs',
        help_text='Select one or more special technologies (Cerebro Puck, Torpedo, etc.)'
    )

    # ═══════════════════════════════════════════════════════════════════════
    # ORDER LEVEL (JV Classification)
    # ═══════════════════════════════════════════════════════════════════════
    order_level = models.CharField(
        max_length=5,
        choices=OrderLevel.choices,
        blank=True,
        verbose_name='Order Level'
    )

    # ═══════════════════════════════════════════════════════════════════════
    # STATUS & REVISION
    # ═══════════════════════════════════════════════════════════════════════
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    revision = models.CharField(
        max_length=10,
        blank=True
    )

    # ═══════════════════════════════════════════════════════════════════════
    # DOCUMENTS
    # ═══════════════════════════════════════════════════════════════════════
    drawing_file = models.FileField(upload_to="designs/drawings/", null=True, blank=True)
    specification_file = models.FileField(upload_to="designs/specs/", null=True, blank=True)

    # ═══════════════════════════════════════════════════════════════════════
    # NOTES
    # ═══════════════════════════════════════════════════════════════════════
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    # ═══════════════════════════════════════════════════════════════════════
    # AUDIT
    # ═══════════════════════════════════════════════════════════════════════
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='designs_created'
    )

    # ═══════════════════════════════════════════════════════════════════════
    # LEGACY FIELDS (for backward compatibility - will be deprecated)
    # ═══════════════════════════════════════════════════════════════════════
    code = models.CharField(max_length=50, blank=True, help_text="Legacy: Use mat_no instead")
    name = models.CharField(max_length=200, blank=True, help_text="Legacy: Use hdbs_type instead")
    bit_type = models.CharField(max_length=20, blank=True, help_text="Legacy: Use category instead")
    size_legacy = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True,
        db_column='size_decimal', help_text="Legacy: Use size FK instead"
    )
    iadc_code = models.CharField(max_length=20, blank=True, help_text="Legacy: Use iadc_code_ref FK instead")
    blade_count = models.IntegerField(null=True, blank=True, help_text="Legacy: Use no_of_blades instead")
    cone_count = models.IntegerField(null=True, blank=True, help_text="Legacy: For RC bits")
    connection_type = models.CharField(max_length=50, blank=True, help_text="Legacy: Use connection_type_ref FK")
    connection_size = models.CharField(max_length=20, blank=True, help_text="Legacy: Use connection_size_ref FK")
    formation_type = models.CharField(max_length=100, blank=True, help_text="Legacy: Use formation_type_ref FK")
    application = models.CharField(max_length=100, blank=True, help_text="Legacy: Use application_ref FK")
    revision_date = models.DateField(null=True, blank=True)
    designed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="designed_bits"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_designs"
    )

    class Meta:
        db_table = "designs"
        ordering = ['category', 'series', 'hdbs_type']
        verbose_name = "Design"
        verbose_name_plural = "Designs"

    def __str__(self):
        if self.size:
            return f"{self.hdbs_type} ({self.size}) - {self.mat_no}"
        return f"{self.hdbs_type} - {self.mat_no}"


class BOM(models.Model):
    """
    🟢 P1: Bill of Materials for designs.
    """

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
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_boms")

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
    """
    🟢 P1: Individual items in a BOM.
    """

    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name="lines")
    line_number = models.IntegerField()

    inventory_item = models.ForeignKey("inventory.InventoryItem", on_delete=models.PROTECT, related_name="bom_lines")

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
    """
    🟢 P1: Cutter layout positions for FC bit designs.
    """

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


# =============================================================================
# POCKET LAYOUT MODELS
# =============================================================================


class PocketSize(models.Model):
    """
    Reference table for pocket/cutter sizes.
    Sizes like 10.5, 16, 19, 1005, 1010, 1218, 1303, etc.
    """
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Size Code',
        help_text='Pocket size code (e.g., 1608, 1613, 19)'
    )
    display_name = models.CharField(
        max_length=50,
        verbose_name='Display Name',
        help_text='Human-readable name'
    )
    diameter_mm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Diameter (mm)',
        help_text='Pocket diameter in millimeters'
    )
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0, help_text='Display order')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "pocket_sizes"
        ordering = ['sort_order', 'code']
        verbose_name = "Pocket Size"
        verbose_name_plural = "Pocket Sizes"

    def __str__(self):
        return self.display_name or self.code


class PocketShape(models.Model):
    """
    Reference table for pocket shapes.
    Flat Bottom, Conical, Spherical, Corner Radius, Open Cylindrical
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    notes = models.TextField(
        blank=True,
        verbose_name='Technical Notes',
        help_text='Additional technical information about this shape'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "pocket_shapes"
        ordering = ['name']
        verbose_name = "Pocket Shape"
        verbose_name_plural = "Pocket Shapes"

    def __str__(self):
        return self.name


class DesignPocketConfig(models.Model):
    """
    Pocket configuration for a design - defines which sizes/shapes are used
    and how many of each.
    """
    class LengthType(models.TextChoices):
        LONG = "L", "Long"
        MEDIUM = "M", "Medium"
        SHORT = "S", "Short"

    design = models.ForeignKey(
        Design,
        on_delete=models.CASCADE,
        related_name='pocket_configs'
    )
    order = models.PositiveIntegerField(
        verbose_name='Order',
        help_text='Display order (1, 2, 3...)'
    )
    pocket_size = models.ForeignKey(
        PocketSize,
        on_delete=models.PROTECT,
        related_name='design_configs'
    )
    length_type = models.CharField(
        max_length=1,
        choices=LengthType.choices,
        default=LengthType.LONG,
        verbose_name='L/M/S',
        help_text='Long, Medium, or Short'
    )
    pocket_shape = models.ForeignKey(
        PocketShape,
        on_delete=models.PROTECT,
        related_name='design_configs'
    )
    count = models.PositiveIntegerField(
        verbose_name='Count',
        help_text='Number of pockets with this configuration'
    )
    color_code = models.CharField(
        max_length=7,
        blank=True,
        verbose_name='Color Code',
        help_text='Hex color for visual identification (e.g., #FF5733)'
    )
    row_number = models.PositiveIntegerField(
        default=1,
        verbose_name='Row Number',
        help_text='Which row this configuration belongs to (1-4)'
    )

    class Meta:
        db_table = "design_pocket_configs"
        ordering = ['design', 'order']
        unique_together = ['design', 'order']
        verbose_name = "Design Pocket Config"
        verbose_name_plural = "Design Pocket Configs"

    def __str__(self):
        return f"{self.design.hdbs_type} - {self.pocket_size.code} x {self.count}"


class DesignPocket(models.Model):
    """
    Individual pocket position in a design.
    Stored by blade, row, and position within blade/row.
    """
    class BladeLocation(models.TextChoices):
        CONE = "C", "Cone"
        NOSE = "N", "Nose"
        TAPER = "T", "Taper"
        SHOULDER = "S", "Shoulder"
        GAGE = "G", "Gage"

    design = models.ForeignKey(
        Design,
        on_delete=models.CASCADE,
        related_name='pockets'
    )
    blade_number = models.PositiveIntegerField(
        verbose_name='Blade',
        help_text='Blade number (1 to no_of_blades)'
    )
    row_number = models.PositiveIntegerField(
        default=1,
        verbose_name='Row',
        help_text='Row number (1 to pocket_rows_count)'
    )
    position_in_row = models.PositiveIntegerField(
        verbose_name='Position in Row',
        help_text='Position within this blade and row'
    )
    position_in_blade = models.PositiveIntegerField(
        verbose_name='Position in Blade',
        help_text='Sequential position within entire blade (across all rows)'
    )
    blade_location = models.CharField(
        max_length=1,
        choices=BladeLocation.choices,
        blank=True,
        null=True,
        verbose_name='Blade Location',
        help_text='Location zone on blade: Cone, Nose, Taper, Shoulder, Gage'
    )
    engagement_order = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Engagement Order',
        help_text='Full engagement sequence order (set in separate tab)'
    )
    pocket_config = models.ForeignKey(
        DesignPocketConfig,
        on_delete=models.PROTECT,
        related_name='pockets',
        verbose_name='Pocket Configuration'
    )
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "design_pockets"
        ordering = ['design', 'blade_number', 'row_number', 'position_in_row']
        unique_together = ['design', 'blade_number', 'row_number', 'position_in_row']
        verbose_name = "Design Pocket"
        verbose_name_plural = "Design Pockets"

    def __str__(self):
        return f"{self.design.hdbs_type} - B{self.blade_number}R{self.row_number}P{self.position_in_row}"
