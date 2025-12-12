# PHASE 2: Products & Bit Tracking Implementation

**Project:** ARDT Floor Management System  
**Phase:** 2 - Products & Drill Bit Tracking  
**Prerequisites:** Phase 1 Complete (Users, Departments, Positions, Companies, Rigs, Wells)

---

## 🎯 OBJECTIVE

Implement the core drill bit tracking system that captures the complete lifecycle of every bit from NEW to SCRAP.

---

## 📋 IMPLEMENTATION ORDER

Follow this EXACT order. Do NOT skip steps.

### Step 2.1: Reference Data Models

**Location:** `apps/workorders/models.py` or create `apps/products/models.py`

#### 2.1.1 BitSize Model
```python
class BitSize(models.Model):
    """Standard bit sizes - stored as decimal, displayed as fraction"""
    code = models.CharField(max_length=20, unique=True)  # e.g., "8.500"
    size_decimal = models.DecimalField(max_digits=6, decimal_places=3)  # 8.500
    size_display = models.CharField(max_length=20)  # "8 1/2""
    size_inches = models.CharField(max_length=20)  # "8 1/2"
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.size_display
```

**Seed Data:**
| code | size_decimal | size_display | size_inches |
|------|--------------|--------------|-------------|
| 3.750 | 3.750 | 3 3/4" | 3 3/4 |
| 3.875 | 3.875 | 3 7/8" | 3 7/8 |
| 6.125 | 6.125 | 6 1/8" | 6 1/8 |
| 8.500 | 8.500 | 8 1/2" | 8 1/2 |
| 12.250 | 12.250 | 12 1/4" | 12 1/4 |

#### 2.1.2 BitType Model
```python
class BitType(models.Model):
    """Product models/types - the design of the bit"""
    code = models.CharField(max_length=50, unique=True)  # e.g., "GT65RHS"
    name = models.CharField(max_length=100)
    series = models.CharField(max_length=20, blank=True)  # GT, HD, MM, FX, etc.
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.code
```

**Seed Data (Sample - 35+ types):**
| code | name | series |
|------|------|--------|
| GT53 | GT53 | GT |
| GT64DH | GT64DH | GT |
| GT65DH | GT65DH | GT |
| GT65RHS | GT65RHS | GT |
| GT65RHS-1 | GT65RHS-1 | GT |
| GT76H | GT76H | GT |
| GTD54H | GTD54H | GT |
| GTD55H | GTD55H | GT |
| GTi54H | GTi54H | GT |
| GTi64H | GTi64H | GT |
| GTi65H | GTi65H | GT |
| GTi76H | GTi76H | GT |
| HD54 | HD54 | HD |
| HD54-2 | HD54-2 | HD |
| HD54-3 | HD54-3 | HD |
| HD54F | HD54F | HD |
| HD54O | HD54O | HD |
| HD54X | HD54X | HD |
| HD64 | HD64 | HD |
| HD64KHF | HD64KHF | HD |
| HD64KHO | HD64KHO | HD |
| MM64 | MM64 | MM |
| MMD54H | MMD54H | MM |
| MMD63 | MMD63 | MM |
| MMD64 | MMD64 | MM |
| MMD64H | MMD64H | MM |
| MMD65H | MMD65H | MM |
| MMD76H | MMD76H | MM |
| MME63 | MME63 | MM |
| MMG64H | MMG64H | MM |
| FX53 | FX53 | FX |
| FXD63 | FXD63 | FX |
| FXD65 | FXD65 | FX |
| HXi54s | HXi54s | HXi |
| HXi65Dks | HXi65Dks | HXi |

---

### Step 2.2: Location Model

```python
class Location(models.Model):
    """Physical locations where bits can be"""
    LOCATION_TYPES = [
        ('WAREHOUSE', 'Warehouse'),
        ('REPAIR_SHOP', 'Repair Shop'),
        ('RIG', 'Rig Site'),
        ('EVALUATION', 'Evaluation Area'),
        ('QC', 'QC Area'),
        ('SCRAP', 'Scrap Yard'),
        ('USA', 'USA Facility'),
        ('TRANSIT', 'In Transit'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES)
    rig = models.ForeignKey('sales.Rig', null=True, blank=True, on_delete=models.SET_NULL)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.location_type})"
```

**Seed Data:**
| code | name | location_type | rig |
|------|------|---------------|-----|
| WH-MAIN | Main Warehouse | WAREHOUSE | null |
| RS-MAIN | Repair Shop | REPAIR_SHOP | null |
| EVAL-AREA | Evaluation Area | EVALUATION | null |
| QC-AREA | QC Area | QC | null |
| SCRAP-YARD | Scrap Yard | SCRAP | null |
| USA-HAL | Halliburton USA | USA | null |
| RIG-088TE | Rig 088TE | RIG | (link to Rig) |
| RIG-GW88 | Rig GW-88 | RIG | (link to Rig) |
| RIG-AD72 | Rig AD-72 | RIG | (link to Rig) |

---

### Step 2.3: DrillBit Model (Main Asset)

```python
class DrillBit(models.Model):
    """Main drill bit asset - tracks the complete lifecycle"""
    
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('DEPLOYED', 'Deployed'),
        ('BACKLOADED', 'Backloaded'),
        ('EVALUATION', 'In Evaluation'),
        ('HOLD', 'On Hold'),
        ('IN_REPAIR', 'In Repair'),
        ('REPAIRED', 'Repaired'),
        ('USA_REPAIR', 'USA Repair'),
        ('RERUN', 'Rerun Ready'),
        ('SCRAP', 'Scrapped'),
        ('SAVED_BODY', 'Saved Body'),
    ]
    
    # Identity (never changes)
    serial_number = models.CharField(max_length=8, unique=True)  # 8 digits only
    bit_type = models.ForeignKey(BitType, on_delete=models.PROTECT)
    bit_size = models.ForeignKey(BitSize, on_delete=models.PROTECT)
    mat_number = models.CharField(max_length=20, blank=True)  # MAT number
    
    # Ownership
    customer = models.ForeignKey('sales.Customer', on_delete=models.PROTECT)
    
    # Counters (the story of the bit)
    repair_count = models.PositiveIntegerField(default=0)  # Repairs at ARDT
    repair_count_usa = models.PositiveIntegerField(default=0)  # Repairs in USA
    rerun_count_factory = models.PositiveIntegerField(default=0)  # Factory reruns (charged)
    rerun_count_field = models.PositiveIntegerField(default=0)  # Field reruns (no charge)
    backload_count = models.PositiveIntegerField(default=0)  # Times returned to factory
    deployment_count = models.PositiveIntegerField(default=0)  # Times deployed
    
    # Current State
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    current_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='current_bits')
    current_rig = models.ForeignKey('sales.Rig', null=True, blank=True, on_delete=models.SET_NULL)
    current_well = models.ForeignKey('sales.Well', null=True, blank=True, on_delete=models.SET_NULL)
    
    # Timestamps
    received_date = models.DateField(null=True, blank=True)
    last_deployed_date = models.DateField(null=True, blank=True)
    last_backload_date = models.DateField(null=True, blank=True)
    scrap_date = models.DateField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='bits_created')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.serial_number} - {self.bit_type}"
    
    @property
    def finance_sn(self):
        """Serial number for Finance/Invoicing
        Formula: SN + R + (repair_count + rerun_count_factory)
        """
        total = self.repair_count + self.rerun_count_factory
        if total > 0:
            return f"{self.serial_number}R{total}"
        return self.serial_number
    
    @property
    def actual_repair_sn(self):
        """Serial number showing actual repairs
        Formula: SN + R + (repair_count + repair_count_usa)
        """
        total = self.repair_count + self.repair_count_usa
        if total > 0:
            return f"{self.serial_number}R{total}"
        return self.serial_number
    
    @property
    def total_events(self):
        """Total lifecycle events"""
        return self.repair_count + self.repair_count_usa + self.rerun_count_factory + self.rerun_count_field
```

---

### Step 2.4: BitEvent Model (Lifecycle History)

```python
class BitEvent(models.Model):
    """Every event in a bit's life - the complete story from birth to death"""
    
    EVENT_TYPES = [
        # Lifecycle events
        ('RECEIVED', 'Received (New)'),
        ('DEPLOYED', 'Deployed to Rig'),
        ('BACKLOADED', 'Backloaded to Factory'),
        ('EVALUATION_START', 'Evaluation Started'),
        ('EVALUATION_COMPLETE', 'Evaluation Complete'),
        
        # Decision events
        ('REPAIR_DECISION', 'Decision: Repair'),
        ('RERUN_DECISION_FACTORY', 'Decision: Rerun (Factory)'),
        ('RERUN_DECISION_FIELD', 'Decision: Rerun (Field)'),
        ('USA_REPAIR_DECISION', 'Decision: USA Repair'),
        ('SCRAP_DECISION', 'Decision: Scrap'),
        ('HOLD_DECISION', 'Decision: Hold'),
        
        # Repair events
        ('REPAIR_START', 'Repair Started'),
        ('REPAIR_COMPLETE', 'Repair Complete'),
        ('USA_REPAIR_SENT', 'Sent to USA'),
        ('USA_REPAIR_RECEIVED', 'Received from USA'),
        
        # QC events
        ('QC_PASS', 'QC Passed'),
        ('QC_FAIL', 'QC Failed'),
        
        # Logistics events
        ('TRANSFER', 'Stock Transfer'),
        ('RELOCATION', 'Relocation (Rig to Rig)'),
        
        # End of life
        ('SCRAPPED', 'Scrapped'),
        ('BODY_SAVED', 'Body Saved'),
    ]
    
    bit = models.ForeignKey(DrillBit, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    event_date = models.DateTimeField()
    
    # Who and where
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    
    # Context (optional based on event type)
    from_location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL, related_name='events_from')
    to_location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL, related_name='events_to')
    rig = models.ForeignKey('sales.Rig', null=True, blank=True, on_delete=models.SET_NULL)
    well = models.ForeignKey('sales.Well', null=True, blank=True, on_delete=models.SET_NULL)
    
    # Related records
    work_order = models.ForeignKey('WorkOrder', null=True, blank=True, on_delete=models.SET_NULL)
    job_card = models.ForeignKey('JobCard', null=True, blank=True, on_delete=models.SET_NULL)
    
    # Notes (for things not tracked elsewhere)
    notes = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-event_date']
    
    def __str__(self):
        return f"{self.bit.serial_number} - {self.get_event_type_display()} - {self.event_date}"
```

---

### Step 2.5: Create Management Commands

Create seed commands in order:

```bash
apps/workorders/management/commands/
├── seed_bit_sizes.py      # Step 2.5.1
├── seed_bit_types.py      # Step 2.5.2
├── seed_locations.py      # Step 2.5.3
└── seed_sample_bits.py    # Step 2.5.4 (optional - for testing)
```

---

## 🧪 TESTING CHECKLIST

After implementation, verify:

- [ ] `python manage.py makemigrations` runs without errors
- [ ] `python manage.py migrate` applies cleanly
- [ ] `python manage.py seed_bit_sizes` creates 5 sizes
- [ ] `python manage.py seed_bit_types` creates 35+ types
- [ ] `python manage.py seed_locations` creates 9+ locations
- [ ] Admin can view/edit BitSize, BitType, Location, DrillBit, BitEvent
- [ ] DrillBit.finance_sn property returns correct format
- [ ] DrillBit.actual_repair_sn property returns correct format

---

## 📝 GIT WORKFLOW

After each sub-step:

```bash
# After Step 2.1:
git add .
git commit -m "✅ Phase 2.1: BitSize and BitType models"
git tag v0.2.1-bit-reference-data

# After Step 2.2:
git add .
git commit -m "✅ Phase 2.2: Location model"
git tag v0.2.2-locations

# After Step 2.3:
git add .
git commit -m "✅ Phase 2.3: DrillBit model with counters"
git tag v0.2.3-drillbit

# After Step 2.4:
git add .
git commit -m "✅ Phase 2.4: BitEvent lifecycle tracking"
git tag v0.2.4-bit-events

# After Step 2.5 (all seeds):
git add .
git commit -m "✅ Phase 2.5: Seed commands and data"
git tag v0.2.5-seeds

# Final:
git push --tags
```

---

## ⚠️ IMPORTANT RULES

1. **DO NOT** change serial_number format - it's always 8 digits
2. **DO NOT** manually set finance_sn - it's calculated
3. **DO NOT** skip BitEvent records - every action must be logged
4. **DO** use ForeignKey with PROTECT for critical relationships
5. **DO** create migrations after each model change
6. **DO** test seed commands before committing

---

## 📁 FILES TO UPDATE

1. `apps/workorders/models.py` - Add new models
2. `apps/workorders/admin.py` - Register new models
3. `apps/workorders/management/commands/` - Add seed commands
4. `docs/MASTER_PLAN.md` - Mark Phase 2 as complete when done

---

## 🚀 START COMMAND

Tell Claude Code:

> "Read docs/PHASE2_PRODUCTS_IMPLEMENTATION.md and start with Step 2.1: Create BitSize and BitType models. Create the models, make migrations, and create seed commands. Test everything. Commit with tag v0.2.1-bit-reference-data."

---

*Document created: December 12, 2025*
