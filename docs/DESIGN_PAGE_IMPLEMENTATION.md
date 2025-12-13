# DESIGN PAGE IMPLEMENTATION

**Project:** ARDT Floor Management System  
**Date:** December 13, 2025  
**Purpose:** Update Design model and create reference tables

---

## 🎯 OBJECTIVE

1. Update Design model with correct field names and structure
2. Create reference tables (ConnectionType, ConnectionSize, FormationType, Application, IADCCode)
3. Add nozzle and port fields
4. Prepare connections for future Pockets, Cutters Layout, and Cutters BOM pages

---

## 📋 TASK 1: Create Reference Tables

### 1.1 ConnectionType Model

```python
class ConnectionType(models.Model):
    """API connection types for drill bits"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
```

**Seed Data:**
| code | name | description |
|------|------|-------------|
| API-REG | API Regular | Standard API regular connection |
| API-IF | API Internal Flush | Internal flush connection |
| API-FH | API Full Hole | Full hole connection |
| API-NC | API Numbered Connection | Numbered connection series |
| HT | Hi-Torque | High torque connection |
| XT | Extreme Torque | Extreme torque connection |
| PAC | Premium API Connection | Premium connection type |
| DS | Double Shoulder | Double shoulder connection |

---

### 1.2 ConnectionSize Model

```python
class ConnectionSize(models.Model):
    """Connection sizes for drill bits"""
    code = models.CharField(max_length=20, unique=True)
    size_inches = models.CharField(max_length=20)
    size_decimal = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['size_decimal']
    
    def __str__(self):
        return self.size_inches
```

**Seed Data:**
| code | size_inches | size_decimal |
|------|-------------|--------------|
| 2-3/8 | 2 3/8" | 2.375 |
| 2-7/8 | 2 7/8" | 2.875 |
| 3-1/2 | 3 1/2" | 3.500 |
| 4-1/2 | 4 1/2" | 4.500 |
| 5-1/2 | 5 1/2" | 5.500 |
| 6-5/8 | 6 5/8" | 6.625 |
| 7-5/8 | 7 5/8" | 7.625 |
| NC26 | NC26 | 2.625 |
| NC31 | NC31 | 3.125 |
| NC38 | NC38 | 3.750 |
| NC46 | NC46 | 4.625 |
| NC50 | NC50 | 5.000 |

---

### 1.3 FormationType Model (Saudi Arabia Formations)

```python
class FormationType(models.Model):
    """Geological formation types - Saudi Arabia focus"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    age = models.CharField(max_length=50, blank=True)  # Geological age
    rock_type = models.CharField(max_length=50, blank=True)  # Carbonate, Sandstone, Shale
    hardness = models.CharField(max_length=20, blank=True)  # Soft, Medium, Hard
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
```

**Seed Data (Saudi Arabia Formations):**
| code | name | age | rock_type | hardness |
|------|------|-----|-----------|----------|
| ARAB-D | Arab-D | Late Jurassic | Carbonate | Medium |
| ARAB-C | Arab-C | Late Jurassic | Carbonate | Medium |
| ARAB-A | Arab-A | Late Jurassic | Carbonate | Medium |
| KHUFF | Khuff | Late Permian | Carbonate/Dolomite | Hard |
| KHUFF-A | Khuff-A | Late Permian | Carbonate | Hard |
| KHUFF-B | Khuff-B | Late Permian | Carbonate | Hard |
| KHUFF-C | Khuff-C | Late Permian | Carbonate | Hard |
| UNAYZAH | Unayzah | Permian | Sandstone | Medium |
| UNAYZAH-A | Unayzah-A | Permian | Sandstone | Medium |
| UNAYZAH-B | Unayzah-B | Permian | Sandstone | Medium |
| JAUF | Jauf | Devonian | Sandstone | Medium |
| QUSAIBA | Qusaiba | Silurian | Shale | Soft |
| SAQ | Saq | Cambrian-Ordovician | Sandstone | Hard |
| QASIM | Qasim | Ordovician | Mixed | Medium |
| SARAH | Sarah | Ordovician | Sandstone | Medium |
| ZARQA | Zarqa | Ordovician-Silurian | Sandstone | Medium |
| WASIA | Wasia | Cretaceous | Sandstone | Medium |
| BIYADH | Biyadh | Cretaceous | Sandstone | Medium |
| SHUAIBA | Shuaiba | Cretaceous | Carbonate | Medium |
| HANIFA | Hanifa | Late Jurassic | Carbonate | Medium |
| TUWAIQ | Tuwaiq | Late Jurassic | Carbonate | Medium |

---

### 1.4 Application Model

```python
class Application(models.Model):
    """Drilling application types"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
```

**Seed Data:**
| code | name | description |
|------|------|-------------|
| VERT | Vertical | Standard vertical drilling |
| DIR | Directional | Directional drilling with mud motor |
| HORZ | Horizontal | Horizontal section drilling |
| ERD | Extended Reach | Extended reach drilling |
| RSS | Rotary Steerable | Rotary steerable system drilling |
| MOTOR | Motor Drilling | Positive displacement motor drilling |
| TURB | Turbine | Turbine drilling |
| SLIDE | Slide Drilling | Sliding mode with bent motor |
| ROTATE | Rotary | Standard rotary drilling |
| CURVE | Curve/Build | Build section in directional well |
| LATERAL | Lateral | Lateral section in horizontal well |
| KICKOFF | Kickoff | Kickoff from vertical to directional |
| TANGENT | Tangent | Tangent section hold angle |
| TOPHOLE | Top Hole | Surface/top hole section |
| INTERMED | Intermediate | Intermediate hole section |
| PRODHOLE | Production Hole | Production section drilling |
| REAM | Reaming | Hole opening/reaming operation |
| SIDETRACK | Sidetrack | Sidetrack/whipstock operation |

---

### 1.5 IADCCode Model

```python
class IADCCode(models.Model):
    """IADC classification codes for drill bits"""
    
    BIT_TYPE_CHOICES = [
        ('FC', 'Fixed Cutter (PDC)'),
        ('RC', 'Roller Cone'),
        ('MT', 'Mill Tooth'),
        ('TCI', 'Tungsten Carbide Insert'),
    ]
    
    code = models.CharField(max_length=10, unique=True)  # e.g., "M433", "517X"
    bit_type = models.CharField(max_length=5, choices=BIT_TYPE_CHOICES)
    
    # For PDC bits: Body-Formation-CutterSize-Profile (M433)
    # For Roller Cone: Series-Type-Bearing-Feature (517X)
    
    # PDC specific
    body_material = models.CharField(max_length=1, blank=True)  # M, S, D
    formation_hardness = models.CharField(max_length=1, blank=True)  # 1-8
    cutter_type = models.CharField(max_length=1, blank=True)  # 1-4
    profile = models.CharField(max_length=1, blank=True)  # 1-4
    
    # Roller Cone specific
    series = models.CharField(max_length=1, blank=True)  # 1-8
    type_code = models.CharField(max_length=1, blank=True)  # 1-4
    bearing = models.CharField(max_length=1, blank=True)  # 1-7
    feature = models.CharField(max_length=1, blank=True)  # A-Z
    
    description = models.CharField(max_length=200)
    formation_description = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['bit_type', 'code']
        verbose_name = 'IADC Code'
        verbose_name_plural = 'IADC Codes'
    
    def __str__(self):
        return f"{self.code} - {self.description}"
```

**Seed Data (Common IADC Codes):**

**PDC Bits (Fixed Cutter):**
| code | bit_type | body_material | formation_hardness | cutter_type | profile | description |
|------|----------|---------------|-------------------|-------------|---------|-------------|
| M122 | FC | M | 1 | 2 | 2 | Matrix, soft formation, 13mm cutters, short profile |
| M222 | FC | M | 2 | 2 | 2 | Matrix, soft-medium formation |
| M323 | FC | M | 3 | 2 | 3 | Matrix, medium formation, medium profile |
| M423 | FC | M | 4 | 2 | 3 | Matrix, medium-hard formation |
| M433 | FC | M | 4 | 3 | 3 | Matrix, medium-hard, 16mm cutters |
| M443 | FC | M | 4 | 4 | 3 | Matrix, medium-hard, 19mm cutters |
| M523 | FC | M | 5 | 2 | 3 | Matrix, hard formation |
| M533 | FC | M | 5 | 3 | 3 | Matrix, hard, 16mm cutters |
| M623 | FC | M | 6 | 2 | 3 | Matrix, very hard formation |
| S323 | FC | S | 3 | 2 | 3 | Steel body, medium formation |
| S423 | FC | S | 4 | 2 | 3 | Steel body, medium-hard formation |
| S433 | FC | S | 4 | 3 | 3 | Steel body, medium-hard, 16mm cutters |
| S523 | FC | S | 5 | 2 | 3 | Steel body, hard formation |

**Roller Cone Bits (Mill Tooth - Series 1-3):**
| code | bit_type | series | type_code | bearing | feature | description |
|------|----------|--------|-----------|---------|---------|-------------|
| 111 | MT | 1 | 1 | 1 | | Soft, standard roller bearing |
| 115 | MT | 1 | 1 | 5 | | Soft, sealed roller + gauge |
| 117 | MT | 1 | 1 | 7 | | Soft, sealed journal + gauge |
| 121 | MT | 1 | 2 | 1 | | Soft-medium, standard roller |
| 211 | MT | 2 | 1 | 1 | | Medium, standard roller |
| 217 | MT | 2 | 1 | 7 | | Medium, sealed journal + gauge |
| 311 | MT | 3 | 1 | 1 | | Hard, standard roller |
| 317 | MT | 3 | 1 | 7 | | Hard, sealed journal + gauge |

**Roller Cone Bits (TCI - Series 4-8):**
| code | bit_type | series | type_code | bearing | feature | description |
|------|----------|--------|-----------|---------|---------|-------------|
| 417 | TCI | 4 | 1 | 7 | | Soft, TCI, sealed journal + gauge |
| 437 | TCI | 4 | 3 | 7 | | Soft-medium, TCI |
| 517 | TCI | 5 | 1 | 7 | | Medium, TCI |
| 517X | TCI | 5 | 1 | 7 | X | Medium, TCI, chisel inserts |
| 537 | TCI | 5 | 3 | 7 | | Medium-hard, TCI |
| 617 | TCI | 6 | 1 | 7 | | Hard, TCI |
| 637 | TCI | 6 | 3 | 7 | | Very hard, TCI |
| 717 | TCI | 7 | 1 | 7 | | Extremely hard, TCI |
| 817 | TCI | 8 | 1 | 7 | | Abrasive, TCI |

---

## 📋 TASK 2: Update Design Model

```python
class Design(models.Model):
    """
    Bit design specification
    Unique constraint: hdbs_type + size (unique together)
    """
    
    # ═══════════════════════════════════════════════════════════
    # IDENTITY
    # ═══════════════════════════════════════════════════════════
    mat_no = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name='MAT No.',
        help_text='HDBS Material Number (SAP)'
    )
    hdbs_type = models.CharField(
        max_length=50,
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
    
    # ═══════════════════════════════════════════════════════════
    # CATEGORY & SIZE
    # ═══════════════════════════════════════════════════════════
    CATEGORY_CHOICES = [
        ('FC', 'Fixed Cutter'),
        ('MT', 'Mill Tooth'),
        ('TCI', 'Tri Cone Inserts'),
    ]
    category = models.CharField(
        max_length=10, 
        choices=CATEGORY_CHOICES, 
        default='FC'
    )
    size = models.ForeignKey(
        'workorders.BitSize', 
        on_delete=models.PROTECT,
        verbose_name='Size'
    )
    series = models.CharField(
        max_length=10, 
        blank=True,
        help_text='Product series (GT, HD, MM, EM, etc.)'
    )
    
    # ═══════════════════════════════════════════════════════════
    # TECHNICAL SPECS (FC Only)
    # ═══════════════════════════════════════════════════════════
    BODY_MATERIAL_CHOICES = [
        ('M', 'Matrix'),
        ('S', 'Steel'),
        ('', 'N/A'),
    ]
    body_material = models.CharField(
        max_length=1, 
        choices=BODY_MATERIAL_CHOICES, 
        blank=True,
        verbose_name='Body Material'
    )
    no_of_blades = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name='No. of Blades'
    )
    cutter_size = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name='Cutter Size',
        help_text='Primary cutter size in mm'
    )
    gage_length = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        null=True, 
        blank=True,
        verbose_name='Gage Length'
    )
    gage_relief = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Gage Relief'
    )
    gauge_protection = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Gauge Protection'
    )
    
    # ═══════════════════════════════════════════════════════════
    # NOZZLES
    # ═══════════════════════════════════════════════════════════
    nozzle_count = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name='Nozzle Count'
    )
    nozzle_size = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Nozzle Size',
        help_text='e.g., 12/32, 14/32, or multiple sizes'
    )
    nozzle_config = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Nozzle Configuration'
    )
    tfa = models.DecimalField(
        max_digits=6, 
        decimal_places=3, 
        null=True, 
        blank=True,
        verbose_name='TFA',
        help_text='Total Flow Area (sq. inches)'
    )
    
    # ═══════════════════════════════════════════════════════════
    # PORTS
    # ═══════════════════════════════════════════════════════════
    port_count = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name='Port Count'
    )
    port_size = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Port Size'
    )
    
    # ═══════════════════════════════════════════════════════════
    # CONNECTION
    # ═══════════════════════════════════════════════════════════
    connection_type = models.ForeignKey(
        'ConnectionType', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        verbose_name='Connection Type'
    )
    connection_size = models.ForeignKey(
        'ConnectionSize', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        verbose_name='Connection Size'
    )
    
    # ═══════════════════════════════════════════════════════════
    # APPLICATION
    # ═══════════════════════════════════════════════════════════
    formation_type = models.ForeignKey(
        'FormationType', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        verbose_name='Formation Type'
    )
    application = models.ForeignKey(
        'Application', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        verbose_name='Application'
    )
    iadc_code = models.ForeignKey(
        'IADCCode', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        verbose_name='IADC Code'
    )
    
    # ═══════════════════════════════════════════════════════════
    # ORDER LEVEL (JV Classification)
    # ═══════════════════════════════════════════════════════════
    ORDER_LEVEL_CHOICES = [
        ('3', 'Level 3 - No cutters, upper section separate'),
        ('4', 'Level 4 - No cutters, upper section welded/machined'),
        ('5', 'Level 5 - With cutters brazed'),
        ('6', 'Level 6 - Painted and ready for use'),
    ]
    order_level = models.CharField(
        max_length=5, 
        choices=ORDER_LEVEL_CHOICES, 
        blank=True,
        verbose_name='Order Level'
    )
    
    # ═══════════════════════════════════════════════════════════
    # STATUS & REVISION
    # ═══════════════════════════════════════════════════════════
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('OBSOLETE', 'Obsolete'),
    ]
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='DRAFT'
    )
    revision = models.CharField(
        max_length=10, 
        blank=True
    )
    
    # ═══════════════════════════════════════════════════════════
    # NOTES
    # ═══════════════════════════════════════════════════════════
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # ═══════════════════════════════════════════════════════════
    # AUDIT
    # ═══════════════════════════════════════════════════════════
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='designs_created'
    )
    
    class Meta:
        unique_together = ['hdbs_type', 'size']  # Design = Type + Size
        ordering = ['category', 'series', 'hdbs_type']
    
    def __str__(self):
        return f"{self.hdbs_type} ({self.size}) - {self.mat_no}"
```

---

## 📋 TASK 3: Future Related Models (Connection Points)

These models are placeholders for future implementation. Create them now with basic structure so ForeignKey relations work:

### 3.1 PocketLayout (Future - for Pockets Page)

```python
class PocketLayout(models.Model):
    """Pocket positions on the bit face - Future implementation"""
    design = models.ForeignKey(
        Design, 
        on_delete=models.CASCADE, 
        related_name='pockets'
    )
    pocket_number = models.PositiveIntegerField()
    blade_number = models.PositiveIntegerField()
    position = models.CharField(max_length=50, blank=True)
    pocket_type = models.CharField(max_length=50, blank=True)
    angle = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['design', 'blade_number', 'pocket_number']
        unique_together = ['design', 'blade_number', 'pocket_number']
    
    def __str__(self):
        return f"Pocket {self.pocket_number} on Blade {self.blade_number}"
```

### 3.2 CutterLayout (Future - for Cutters Layout Page)

```python
class CutterLayout(models.Model):
    """Cutter positions mapped to pockets - Future implementation"""
    design = models.ForeignKey(
        Design, 
        on_delete=models.CASCADE, 
        related_name='cutter_layout'
    )
    pocket = models.ForeignKey(
        PocketLayout, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True
    )
    position_number = models.PositiveIntegerField()
    cutter_type = models.CharField(max_length=50, blank=True)
    cutter_size = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    cutter_grade = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['design', 'position_number']
    
    def __str__(self):
        return f"Cutter {self.position_number} - {self.cutter_type}"
```

### 3.3 CuttersBOM (Future - for Cutters BOM Page)

```python
class CuttersBOM(models.Model):
    """Bill of Materials for cutters in a design - Future implementation"""
    design = models.ForeignKey(
        Design, 
        on_delete=models.CASCADE, 
        related_name='cutters_bom'
    )
    cutter_type = models.CharField(max_length=50)
    cutter_size = models.DecimalField(max_digits=4, decimal_places=2)
    cutter_grade = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['design', 'cutter_type', 'cutter_size']
        verbose_name = 'Cutters BOM'
        verbose_name_plural = 'Cutters BOMs'
    
    def __str__(self):
        return f"{self.quantity}x {self.cutter_type} {self.cutter_size}mm"
    
    @property
    def total_cost(self):
        if self.unit_cost:
            return self.quantity * self.unit_cost
        return None
```

---

## 📋 TASK 4: Create Management Commands

### 4.1 seed_connection_types.py

```python
from django.core.management.base import BaseCommand
from apps.engineering.models import ConnectionType

class Command(BaseCommand):
    help = 'Seed connection types'

    def handle(self, *args, **options):
        data = [
            ('API-REG', 'API Regular', 'Standard API regular connection'),
            ('API-IF', 'API Internal Flush', 'Internal flush connection'),
            ('API-FH', 'API Full Hole', 'Full hole connection'),
            ('API-NC', 'API Numbered Connection', 'Numbered connection series'),
            ('HT', 'Hi-Torque', 'High torque connection'),
            ('XT', 'Extreme Torque', 'Extreme torque connection'),
            ('PAC', 'Premium API Connection', 'Premium connection type'),
            ('DS', 'Double Shoulder', 'Double shoulder connection'),
        ]
        
        created = 0
        for code, name, desc in data:
            obj, was_created = ConnectionType.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc}
            )
            if was_created:
                created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ ConnectionType: {created} created'))
```

### 4.2 seed_connection_sizes.py

```python
from django.core.management.base import BaseCommand
from apps.engineering.models import ConnectionSize
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seed connection sizes'

    def handle(self, *args, **options):
        data = [
            ('2-3/8', '2 3/8"', Decimal('2.375')),
            ('2-7/8', '2 7/8"', Decimal('2.875')),
            ('3-1/2', '3 1/2"', Decimal('3.500')),
            ('4-1/2', '4 1/2"', Decimal('4.500')),
            ('5-1/2', '5 1/2"', Decimal('5.500')),
            ('6-5/8', '6 5/8"', Decimal('6.625')),
            ('7-5/8', '7 5/8"', Decimal('7.625')),
            ('NC26', 'NC26', Decimal('2.625')),
            ('NC31', 'NC31', Decimal('3.125')),
            ('NC38', 'NC38', Decimal('3.750')),
            ('NC46', 'NC46', Decimal('4.625')),
            ('NC50', 'NC50', Decimal('5.000')),
        ]
        
        created = 0
        for code, size_inches, size_decimal in data:
            obj, was_created = ConnectionSize.objects.get_or_create(
                code=code,
                defaults={'size_inches': size_inches, 'size_decimal': size_decimal}
            )
            if was_created:
                created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ ConnectionSize: {created} created'))
```

### 4.3 seed_formation_types.py

```python
from django.core.management.base import BaseCommand
from apps.engineering.models import FormationType

class Command(BaseCommand):
    help = 'Seed Saudi Arabia formation types'

    def handle(self, *args, **options):
        data = [
            # code, name, age, rock_type, hardness
            ('ARAB-D', 'Arab-D', 'Late Jurassic', 'Carbonate', 'Medium'),
            ('ARAB-C', 'Arab-C', 'Late Jurassic', 'Carbonate', 'Medium'),
            ('ARAB-A', 'Arab-A', 'Late Jurassic', 'Carbonate', 'Medium'),
            ('KHUFF', 'Khuff', 'Late Permian', 'Carbonate/Dolomite', 'Hard'),
            ('KHUFF-A', 'Khuff-A', 'Late Permian', 'Carbonate', 'Hard'),
            ('KHUFF-B', 'Khuff-B', 'Late Permian', 'Carbonate', 'Hard'),
            ('KHUFF-C', 'Khuff-C', 'Late Permian', 'Carbonate', 'Hard'),
            ('UNAYZAH', 'Unayzah', 'Permian', 'Sandstone', 'Medium'),
            ('UNAYZAH-A', 'Unayzah-A', 'Permian', 'Sandstone', 'Medium'),
            ('UNAYZAH-B', 'Unayzah-B', 'Permian', 'Sandstone', 'Medium'),
            ('JAUF', 'Jauf', 'Devonian', 'Sandstone', 'Medium'),
            ('QUSAIBA', 'Qusaiba', 'Silurian', 'Shale', 'Soft'),
            ('SAQ', 'Saq', 'Cambrian-Ordovician', 'Sandstone', 'Hard'),
            ('QASIM', 'Qasim', 'Ordovician', 'Mixed', 'Medium'),
            ('SARAH', 'Sarah', 'Ordovician', 'Sandstone', 'Medium'),
            ('ZARQA', 'Zarqa', 'Ordovician-Silurian', 'Sandstone', 'Medium'),
            ('WASIA', 'Wasia', 'Cretaceous', 'Sandstone', 'Medium'),
            ('BIYADH', 'Biyadh', 'Cretaceous', 'Sandstone', 'Medium'),
            ('SHUAIBA', 'Shuaiba', 'Cretaceous', 'Carbonate', 'Medium'),
            ('HANIFA', 'Hanifa', 'Late Jurassic', 'Carbonate', 'Medium'),
            ('TUWAIQ', 'Tuwaiq', 'Late Jurassic', 'Carbonate', 'Medium'),
        ]
        
        created = 0
        for code, name, age, rock_type, hardness in data:
            obj, was_created = FormationType.objects.get_or_create(
                code=code,
                defaults={
                    'name': name, 
                    'age': age, 
                    'rock_type': rock_type, 
                    'hardness': hardness
                }
            )
            if was_created:
                created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ FormationType: {created} created'))
```

### 4.4 seed_applications.py

```python
from django.core.management.base import BaseCommand
from apps.engineering.models import Application

class Command(BaseCommand):
    help = 'Seed drilling applications'

    def handle(self, *args, **options):
        data = [
            ('VERT', 'Vertical', 'Standard vertical drilling'),
            ('DIR', 'Directional', 'Directional drilling with mud motor'),
            ('HORZ', 'Horizontal', 'Horizontal section drilling'),
            ('ERD', 'Extended Reach', 'Extended reach drilling'),
            ('RSS', 'Rotary Steerable', 'Rotary steerable system drilling'),
            ('MOTOR', 'Motor Drilling', 'Positive displacement motor drilling'),
            ('TURB', 'Turbine', 'Turbine drilling'),
            ('SLIDE', 'Slide Drilling', 'Sliding mode with bent motor'),
            ('ROTATE', 'Rotary', 'Standard rotary drilling'),
            ('CURVE', 'Curve/Build', 'Build section in directional well'),
            ('LATERAL', 'Lateral', 'Lateral section in horizontal well'),
            ('KICKOFF', 'Kickoff', 'Kickoff from vertical to directional'),
            ('TANGENT', 'Tangent', 'Tangent section hold angle'),
            ('TOPHOLE', 'Top Hole', 'Surface/top hole section'),
            ('INTERMED', 'Intermediate', 'Intermediate hole section'),
            ('PRODHOLE', 'Production Hole', 'Production section drilling'),
            ('REAM', 'Reaming', 'Hole opening/reaming operation'),
            ('SIDETRACK', 'Sidetrack', 'Sidetrack/whipstock operation'),
        ]
        
        created = 0
        for code, name, desc in data:
            obj, was_created = Application.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc}
            )
            if was_created:
                created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ Application: {created} created'))
```

### 4.5 seed_iadc_codes.py

```python
from django.core.management.base import BaseCommand
from apps.engineering.models import IADCCode

class Command(BaseCommand):
    help = 'Seed IADC classification codes'

    def handle(self, *args, **options):
        # PDC Bits
        pdc_data = [
            ('M122', 'FC', 'M', '1', '2', '2', '', '', '', '', 'Matrix, soft formation, 13mm cutters, short profile'),
            ('M222', 'FC', 'M', '2', '2', '2', '', '', '', '', 'Matrix, soft-medium formation'),
            ('M323', 'FC', 'M', '3', '2', '3', '', '', '', '', 'Matrix, medium formation, medium profile'),
            ('M423', 'FC', 'M', '4', '2', '3', '', '', '', '', 'Matrix, medium-hard formation'),
            ('M433', 'FC', 'M', '4', '3', '3', '', '', '', '', 'Matrix, medium-hard, 16mm cutters'),
            ('M443', 'FC', 'M', '4', '4', '3', '', '', '', '', 'Matrix, medium-hard, 19mm cutters'),
            ('M523', 'FC', 'M', '5', '2', '3', '', '', '', '', 'Matrix, hard formation'),
            ('M533', 'FC', 'M', '5', '3', '3', '', '', '', '', 'Matrix, hard, 16mm cutters'),
            ('M623', 'FC', 'M', '6', '2', '3', '', '', '', '', 'Matrix, very hard formation'),
            ('S323', 'FC', 'S', '3', '2', '3', '', '', '', '', 'Steel body, medium formation'),
            ('S423', 'FC', 'S', '4', '2', '3', '', '', '', '', 'Steel body, medium-hard formation'),
            ('S433', 'FC', 'S', '4', '3', '3', '', '', '', '', 'Steel body, medium-hard, 16mm cutters'),
            ('S523', 'FC', 'S', '5', '2', '3', '', '', '', '', 'Steel body, hard formation'),
        ]
        
        # Roller Cone Bits
        rc_data = [
            ('111', 'MT', '', '', '', '', '1', '1', '1', '', 'Soft, standard roller bearing'),
            ('115', 'MT', '', '', '', '', '1', '1', '5', '', 'Soft, sealed roller + gauge'),
            ('117', 'MT', '', '', '', '', '1', '1', '7', '', 'Soft, sealed journal + gauge'),
            ('211', 'MT', '', '', '', '', '2', '1', '1', '', 'Medium, standard roller'),
            ('217', 'MT', '', '', '', '', '2', '1', '7', '', 'Medium, sealed journal + gauge'),
            ('311', 'MT', '', '', '', '', '3', '1', '1', '', 'Hard, standard roller'),
            ('317', 'MT', '', '', '', '', '3', '1', '7', '', 'Hard, sealed journal + gauge'),
            ('417', 'TCI', '', '', '', '', '4', '1', '7', '', 'Soft, TCI, sealed journal + gauge'),
            ('437', 'TCI', '', '', '', '', '4', '3', '7', '', 'Soft-medium, TCI'),
            ('517', 'TCI', '', '', '', '', '5', '1', '7', '', 'Medium, TCI'),
            ('517X', 'TCI', '', '', '', '', '5', '1', '7', 'X', 'Medium, TCI, chisel inserts'),
            ('537', 'TCI', '', '', '', '', '5', '3', '7', '', 'Medium-hard, TCI'),
            ('617', 'TCI', '', '', '', '', '6', '1', '7', '', 'Hard, TCI'),
            ('637', 'TCI', '', '', '', '', '6', '3', '7', '', 'Very hard, TCI'),
            ('717', 'TCI', '', '', '', '', '7', '1', '7', '', 'Extremely hard, TCI'),
            ('817', 'TCI', '', '', '', '', '8', '1', '7', '', 'Abrasive, TCI'),
        ]
        
        created = 0
        
        # Create PDC codes
        for code, bit_type, body, form, cutter, profile, s, t, b, f, desc in pdc_data:
            obj, was_created = IADCCode.objects.get_or_create(
                code=code,
                defaults={
                    'bit_type': bit_type,
                    'body_material': body,
                    'formation_hardness': form,
                    'cutter_type': cutter,
                    'profile': profile,
                    'description': desc,
                }
            )
            if was_created:
                created += 1
        
        # Create Roller Cone codes
        for code, bit_type, body, form, cutter, profile, series, type_c, bearing, feature, desc in rc_data:
            obj, was_created = IADCCode.objects.get_or_create(
                code=code,
                defaults={
                    'bit_type': bit_type,
                    'series': series,
                    'type_code': type_c,
                    'bearing': bearing,
                    'feature': feature,
                    'description': desc,
                }
            )
            if was_created:
                created += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ IADCCode: {created} created'))
```

---

## 📋 TASK 5: Update Design Form Template

```html
{% extends 'base.html' %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold mb-6">
        {% if form.instance.pk %}Edit Design{% else %}Create Design{% endif %}
    </h1>
    
    <form method="post" class="space-y-6">
        {% csrf_token %}
        
        <!-- IDENTITY -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold mb-4 border-b pb-2">Identity</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label class="block text-sm font-medium mb-1">MAT No. *</label>
                    {{ form.mat_no }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Ref MAT No.</label>
                    {{ form.ref_mat_no }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">ARDT Item No.</label>
                    {{ form.ardt_item_no }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">HDBS Type *</label>
                    {{ form.hdbs_type }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">SMI Type</label>
                    {{ form.smi_type }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Series</label>
                    {{ form.series }}
                </div>
            </div>
        </div>
        
        <!-- CATEGORY & SIZE -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold mb-4 border-b pb-2">Category & Size</h2>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Category *</label>
                    {{ form.category }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Size *</label>
                    {{ form.size }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Order Level</label>
                    {{ form.order_level }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">IADC Code</label>
                    {{ form.iadc_code }}
                </div>
            </div>
        </div>
        
        <!-- TECHNICAL SPECS (FC Only) -->
        <div class="bg-white rounded-lg shadow p-6" id="fc-specs">
            <h2 class="text-lg font-semibold mb-4 border-b pb-2">Technical Specs (Fixed Cutter Only)</h2>
            <div class="grid grid-cols-2 md:grid-cols-6 gap-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Body Material</label>
                    {{ form.body_material }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">No. of Blades</label>
                    {{ form.no_of_blades }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Cutter Size (mm)</label>
                    {{ form.cutter_size }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Gage Length</label>
                    {{ form.gage_length }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Gage Relief</label>
                    {{ form.gage_relief }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Gauge Protection</label>
                    {{ form.gauge_protection }}
                </div>
            </div>
        </div>
        
        <!-- NOZZLES & PORTS -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold mb-4 border-b pb-2">Nozzles & Ports</h2>
            <div class="grid grid-cols-2 md:grid-cols-6 gap-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Nozzle Count</label>
                    {{ form.nozzle_count }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Nozzle Size</label>
                    {{ form.nozzle_size }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">TFA (sq.in)</label>
                    {{ form.tfa }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Port Count</label>
                    {{ form.port_count }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Port Size</label>
                    {{ form.port_size }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Nozzle Config</label>
                    {{ form.nozzle_config }}
                </div>
            </div>
        </div>
        
        <!-- CONNECTION -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold mb-4 border-b pb-2">Connection</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Connection Type</label>
                    {{ form.connection_type }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Connection Size</label>
                    {{ form.connection_size }}
                </div>
            </div>
        </div>
        
        <!-- APPLICATION -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold mb-4 border-b pb-2">Application</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Formation Type</label>
                    {{ form.formation_type }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Application</label>
                    {{ form.application }}
                </div>
            </div>
        </div>
        
        <!-- STATUS -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold mb-4 border-b pb-2">Status</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Status</label>
                    {{ form.status }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Revision</label>
                    {{ form.revision }}
                </div>
            </div>
        </div>
        
        <!-- RELATED DATA (Links) -->
        {% if form.instance.pk %}
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold mb-4 border-b pb-2">Related Data</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <a href="{% url 'engineering:design_pockets' form.instance.pk %}" 
                   class="btn btn-outline">
                    📋 Pockets Layout ({{ form.instance.pockets.count }})
                </a>
                <a href="{% url 'engineering:design_cutters' form.instance.pk %}" 
                   class="btn btn-outline">
                    🔧 Cutters Layout ({{ form.instance.cutter_layout.count }})
                </a>
                <a href="{% url 'engineering:design_bom' form.instance.pk %}" 
                   class="btn btn-outline">
                    📦 Cutters BOM ({{ form.instance.cutters_bom.count }})
                </a>
            </div>
        </div>
        {% endif %}
        
        <!-- NOTES -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold mb-4 border-b pb-2">Notes</h2>
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Description</label>
                    {{ form.description }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Notes</label>
                    {{ form.notes }}
                </div>
            </div>
        </div>
        
        <!-- ACTIONS -->
        <div class="flex justify-end gap-4">
            <a href="{% url 'engineering:design_list' %}" class="btn btn-ghost">Cancel</a>
            <button type="submit" class="btn btn-primary">Save Design</button>
        </div>
    </form>
</div>
{% endblock %}
```

---

## 🧪 TESTING CHECKLIST

- [ ] `python manage.py makemigrations` runs without errors
- [ ] `python manage.py migrate` applies cleanly
- [ ] All seed commands run successfully:
  - [ ] `python manage.py seed_connection_types`
  - [ ] `python manage.py seed_connection_sizes`
  - [ ] `python manage.py seed_formation_types`
  - [ ] `python manage.py seed_applications`
  - [ ] `python manage.py seed_iadc_codes`
- [ ] Design form loads with all new fields
- [ ] Dropdowns populate with reference data
- [ ] unique_together constraint works (hdbs_type + size)
- [ ] Related data links show on edit page

---

## 📝 GIT WORKFLOW

```bash
# After reference tables:
git add .
git commit -m "✅ Add reference tables: ConnectionType, ConnectionSize, FormationType, Application, IADCCode"
git tag v0.3.1-reference-tables

# After Design model update:
git add .
git commit -m "✅ Update Design model with correct fields and relations"
git tag v0.3.2-design-model

# After seed commands:
git add .
git commit -m "✅ Add seed commands for reference tables"
git tag v0.3.3-design-seeds

# After form template:
git add .
git commit -m "✅ Update Design form with new layout"
git tag v0.3.4-design-form

git push --tags
```

---

## 🚀 TELL CLAUDE CODE

> "Read docs/DESIGN_PAGE_IMPLEMENTATION.md and start with Task 1: Create the reference tables (ConnectionType, ConnectionSize, FormationType, Application, IADCCode). Make migrations and apply. Then create seed commands and run them. Commit with tag v0.3.1-reference-tables."

---

*Document created: December 13, 2025*
