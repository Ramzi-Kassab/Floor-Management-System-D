"""
ARDT FMS - Technology Models
Version: 5.4

Tables:
- designs (P1)
- boms (P1)
- bom_lines (P1)
- design_cutter_layouts (P1)
"""

from django.db import models
from django.conf import settings


class Design(models.Model):
    """
    🟢 P1: Drill bit design master.
    
    Contains specifications for drill bit designs.
    """
    
    class BitType(models.TextChoices):
        FC = 'FC', 'Fixed Cutter (PDC)'
        RC = 'RC', 'Roller Cone'
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ACTIVE = 'ACTIVE', 'Active'
        OBSOLETE = 'OBSOLETE', 'Obsolete'
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    bit_type = models.CharField(max_length=20, choices=BitType.choices)
    
    # Specifications
    size = models.DecimalField(max_digits=6, decimal_places=3, help_text='Size in inches')
    iadc_code = models.CharField(max_length=20, blank=True)
    blade_count = models.IntegerField(null=True, blank=True, help_text='For FC bits')
    cone_count = models.IntegerField(null=True, blank=True, help_text='For RC bits')
    
    # Connection
    connection_type = models.CharField(max_length=50, blank=True)
    connection_size = models.CharField(max_length=20, blank=True)
    
    # Classification
    formation_type = models.CharField(max_length=100, blank=True, help_text='Target formation')
    application = models.CharField(max_length=100, blank=True)
    
    # Technical details
    gauge_protection = models.CharField(max_length=100, blank=True)
    nozzle_config = models.CharField(max_length=100, blank=True)
    tfa = models.DecimalField(
        max_digits=6, 
        decimal_places=3, 
        null=True, 
        blank=True,
        help_text='Total Flow Area'
    )
    
    # Documents
    drawing_file = models.FileField(upload_to='designs/drawings/', null=True, blank=True)
    specification_file = models.FileField(upload_to='designs/specs/', null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    revision = models.CharField(max_length=10, default='A')
    revision_date = models.DateField(null=True, blank=True)
    
    # Ownership
    designed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='designed_bits'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_designs'
    )
    
    # Notes
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_designs'
    )
    
    class Meta:
        db_table = 'designs'
        ordering = ['code']
        verbose_name = 'Design'
        verbose_name_plural = 'Designs'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class BOM(models.Model):
    """
    🟢 P1: Bill of Materials for designs.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ACTIVE = 'ACTIVE', 'Active'
        OBSOLETE = 'OBSOLETE', 'Obsolete'
    
    design = models.ForeignKey(
        Design,
        on_delete=models.CASCADE,
        related_name='boms'
    )
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    revision = models.CharField(max_length=10, default='A')
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    effective_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_boms'
    )
    
    class Meta:
        db_table = 'boms'
        ordering = ['design', 'code']
        verbose_name = 'Bill of Materials'
        verbose_name_plural = 'Bills of Materials'
    
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
    
    bom = models.ForeignKey(
        BOM,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.IntegerField()
    
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.PROTECT,
        related_name='bom_lines'
    )
    
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=20, blank=True)
    
    # Cost (cached from inventory item)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    
    # Position (for assembly)
    position = models.CharField(max_length=50, blank=True, help_text='Assembly position')
    
    # Options
    is_optional = models.BooleanField(default=False)
    is_phantom = models.BooleanField(default=False, help_text='Sub-assembly to be exploded')
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'bom_lines'
        ordering = ['bom', 'line_number']
        unique_together = ['bom', 'line_number']
        verbose_name = 'BOM Line'
        verbose_name_plural = 'BOM Lines'
    
    def __str__(self):
        return f"{self.bom.code} - Line {self.line_number}"
    
    @property
    def line_cost(self):
        return float(self.quantity) * float(self.unit_cost)


class DesignCutterLayout(models.Model):
    """
    🟢 P1: Cutter layout positions for FC bit designs.
    """
    
    design = models.ForeignKey(
        Design,
        on_delete=models.CASCADE,
        related_name='cutter_layouts'
    )
    blade_number = models.IntegerField()
    position_number = models.IntegerField()
    
    # Cutter specifications
    cutter_type = models.CharField(max_length=50)
    cutter_size = models.DecimalField(max_digits=6, decimal_places=2, help_text='mm')
    cutter_grade = models.CharField(max_length=50, blank=True)
    
    # Position
    radial_position = models.DecimalField(max_digits=8, decimal_places=3, help_text='mm from center')
    backrake = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='degrees')
    siderake = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='degrees')
    exposure = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='mm')
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'design_cutter_layouts'
        ordering = ['design', 'blade_number', 'position_number']
        unique_together = ['design', 'blade_number', 'position_number']
        verbose_name = 'Cutter Layout'
        verbose_name_plural = 'Cutter Layouts'
    
    def __str__(self):
        return f"{self.design.code} - Blade {self.blade_number}, Pos {self.position_number}"
