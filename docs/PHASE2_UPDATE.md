# PHASE 2 UPDATE: BitType Enhancement & Web UI

**Project:** ARDT Floor Management System  
**Phase:** 2 - UPDATE (Not fresh implementation)  
**Prerequisites:** Phase 2 models already exist (BitSize, BitType, Location, DrillBit, BitEvent)

---

## 🎯 OBJECTIVE

UPDATE the existing BitType model to add missing fields and CREATE Web UI pages.

**This is NOT a fresh implementation - models already exist!**

---

## ✅ ALREADY DONE (Do Not Recreate)

| Model | Status | Notes |
|-------|--------|-------|
| BitSize | ✅ Exists | 18 sizes created |
| BitType | ✅ Exists | BUT needs field updates |
| Location | ✅ Exists | All location types created |
| DrillBit | ✅ Exists | With counters and lifecycle |
| BitEvent | ✅ Exists | 20 event types |

---

## 📋 TASK 1: Update BitType Model

**Location:** `apps/workorders/models.py`

**Current BitType** (check existing fields first):
```python
class BitType(models.Model):
    code = models.CharField(...)
    name = models.CharField(...)
    series = models.CharField(...)
    description = models.TextField(...)
    is_active = models.BooleanField(...)
```

**ADD these new fields:**
```python
class BitType(models.Model):
    # KEEP existing fields, ADD these:
    
    # Category (NEW)
    CATEGORY_CHOICES = [
        ('FC', 'Fixed Cutter'),
        ('MT', 'Mill Tooth'),      # Roller cone
        ('TCI', 'Tri Cone Inserts'),  # Roller cone
    ]
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='FC')
    
    # Size reference (NEW)
    size = models.ForeignKey('BitSize', on_delete=models.PROTECT, null=True, blank=True)
    
    # Naming - rename 'code' to 'smi_name' or add new field
    smi_name = models.CharField(max_length=50, blank=True)  # Client-facing name
    hdbs_name = models.CharField(max_length=50, blank=True)  # Internal HDBS name
    # 'code' can stay as is, or migrate data to smi_name
    
    # Material Numbers (NEW)
    hdbs_mn = models.CharField(max_length=20, blank=True)  # HDBS SAP number
    ref_hdbs_mn = models.CharField(max_length=20, blank=True)  # Parent/reference MAT
    ardt_item_number = models.CharField(max_length=20, blank=True)  # ARDT ERP number
    
    # Technical Specs - FC only (NEW)
    BODY_MATERIAL_CHOICES = [
        ('M', 'Matrix'),
        ('S', 'Steel'),
        ('', 'N/A'),
    ]
    body_material = models.CharField(max_length=1, choices=BODY_MATERIAL_CHOICES, blank=True)
    no_of_blades = models.PositiveIntegerField(null=True, blank=True)
    cutter_size = models.PositiveIntegerField(null=True, blank=True)
    gage_length = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    # Order/Production Level - JV Classification (NEW)
    ORDER_LEVEL_CHOICES = [
        ('3', 'Level 3 - No cutters, upper section separate'),
        ('4', 'Level 4 - No cutters, upper section welded/machined'),
        ('5', 'Level 5 - With cutters brazed'),
        ('6', 'Level 6 - Painted and ready for use'),
    ]
    order_level = models.CharField(max_length=5, choices=ORDER_LEVEL_CHOICES, blank=True)
```

**Migration Steps:**
```bash
# 1. Add new fields with null=True, blank=True to avoid migration issues
python manage.py makemigrations workorders

# 2. Apply migration
python manage.py migrate

# 3. Verify in admin
python manage.py runserver
# Go to /admin/workorders/bittype/ and check new fields appear
```

---

## 📋 TASK 2: Update BitType Admin

**Location:** `apps/workorders/admin.py`

```python
@admin.register(BitType)
class BitTypeAdmin(admin.ModelAdmin):
    list_display = ['smi_name', 'category', 'size', 'hdbs_name', 'hdbs_mn', 
                    'body_material', 'no_of_blades', 'cutter_size', 'order_level', 'is_active']
    list_filter = ['category', 'series', 'body_material', 'order_level', 'is_active']
    search_fields = ['smi_name', 'hdbs_name', 'hdbs_mn', 'code', 'name']
    ordering = ['category', 'series', 'smi_name']
    
    fieldsets = (
        ('Identity', {
            'fields': ('category', 'size', 'smi_name', 'hdbs_name', 'series')
        }),
        ('Material Numbers', {
            'fields': ('hdbs_mn', 'ref_hdbs_mn', 'ardt_item_number')
        }),
        ('Technical Specs (FC Only)', {
            'fields': ('body_material', 'no_of_blades', 'cutter_size', 'gage_length'),
            'classes': ('collapse',),
        }),
        ('Production', {
            'fields': ('order_level',)
        }),
        ('Status', {
            'fields': ('is_active', 'description')
        }),
    )
```

---

## 📋 TASK 3: Seed Real BitType Data

**Create:** `apps/workorders/management/commands/update_bit_types.py`

```python
from django.core.management.base import BaseCommand
from apps.workorders.models import BitType, BitSize

class Command(BaseCommand):
    help = 'Update BitType records with real data from ARDT'

    def handle(self, *args, **options):
        # Real data from ARDT spreadsheet
        bit_types_data = [
            # category, size_decimal, smi_name, hdbs_name, series, hdbs_mn, ref_hdbs_mn, body_material, blades, cutter, gage, level
            ('FC', 3.625, 'MMD53DH', 'MMD53DH', 'MM', '2016920', '2013733', 'M', 5, 3, 2.0, '4'),
            ('FC', 3.625, 'MMD53DH-2', 'MMD53DH', 'MM', '2025595', '1228690', 'M', 5, 3, 1.5, '4'),
            ('FC', 5.875, 'EM65D', 'EM65D', 'EM', '2017993', '1235768', 'M', 6, 5, 1.5, '4'),
            ('FC', 5.875, 'EM65DX', '', 'EM', '2021067', '', 'M', 6, 5, None, '4'),
            ('FC', 6.125, 'GTD54H', 'GTD54H', 'GT', '1145824', '1137349', 'M', 5, 4, 1.5, '4'),
            ('FC', 6.125, 'GT64KHO', 'GT64KHO', 'GT', '1198387', '1160951', 'M', 6, 4, 1.5, '4'),
            ('FC', 8.375, 'GT65DH-1', 'GT65DH', 'GT', '1246020', '1141517', 'M', 6, 5, 2.0, '4'),
            ('FC', 8.375, 'EM75D', 'EM75D', 'EM', '1272920', '1141517', 'M', 7, 5, 2.0, '4'),
            ('FC', 8.5, 'GT65RHs-1', 'GT65RHs-1', 'GT', '2022318', '1269498', 'S', 6, 5, 3.5, '4'),
            ('FC', 12.25, 'HD65Os', 'HD65Os', 'HD', '1270865', '1218014', 'S', 6, 5, 2.5, '4'),
            ('FC', 16.0, 'HD76DF', 'HD76DF', 'HD', '2019988', '1266749', 'M', 7, 6, 4.0, '4'),
            ('TCI', 28.0, 'EBXT12S', '435W', '', '2023982', '739244', '', None, None, None, ''),
            ('MT', 5.875, 'Q4R', '217M', '', '720942', '497455', '', None, None, None, ''),
            ('MT', 6.125, 'QH1R', '117W', '', '537077', '', '', None, None, None, ''),
            ('MT', 8.5, 'AB1GRC', '217', '', '2027933', '', '', None, None, None, ''),
        ]
        
        created = 0
        updated = 0
        
        for data in bit_types_data:
            cat, size_dec, smi, hdbs, series, mn, ref_mn, body, blades, cutter, gage, level = data
            
            # Get or create BitSize
            size = None
            if size_dec:
                size = BitSize.objects.filter(size_decimal=size_dec).first()
            
            # Update or create BitType
            bit_type, was_created = BitType.objects.update_or_create(
                hdbs_mn=mn,  # Use MAT number as unique identifier
                defaults={
                    'category': cat,
                    'size': size,
                    'smi_name': smi,
                    'hdbs_name': hdbs,
                    'series': series,
                    'ref_hdbs_mn': ref_mn,
                    'body_material': body,
                    'no_of_blades': blades,
                    'cutter_size': cutter,
                    'gage_length': gage,
                    'order_level': level,
                    'is_active': True,
                }
            )
            
            if was_created:
                created += 1
            else:
                updated += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'✅ BitTypes: {created} created, {updated} updated'
        ))
```

**Run:**
```bash
python manage.py update_bit_types
```

---

## 📋 TASK 4: Create Web UI Pages

### 4.1 URL Patterns

**Add to:** `apps/workorders/urls.py`
```python
# BitType URLs
path('bit-types/', views.BitTypeListView.as_view(), name='bittype_list'),
path('bit-types/create/', views.BitTypeCreateView.as_view(), name='bittype_create'),
path('bit-types/<int:pk>/', views.BitTypeDetailView.as_view(), name='bittype_detail'),
path('bit-types/<int:pk>/edit/', views.BitTypeUpdateView.as_view(), name='bittype_update'),

# BitSize URLs  
path('bit-sizes/', views.BitSizeListView.as_view(), name='bitsize_list'),

# Location URLs
path('locations/', views.LocationListView.as_view(), name='location_list'),
```

### 4.2 Views

**Add to:** `apps/workorders/views.py`
```python
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from .models import BitType, BitSize, Location

class BitTypeListView(LoginRequiredMixin, ListView):
    model = BitType
    template_name = 'workorders/bittype_list.html'
    context_object_name = 'bit_types'
    paginate_by = 25
    
    def get_queryset(self):
        qs = super().get_queryset().select_related('size')
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)
        
        # Filter by series
        series = self.request.GET.get('series')
        if series:
            qs = qs.filter(series=series)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(smi_name__icontains=search) |
                Q(hdbs_name__icontains=search) |
                Q(hdbs_mn__icontains=search)
            )
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = BitType.CATEGORY_CHOICES
        context['series_list'] = BitType.objects.values_list('series', flat=True).distinct().order_by('series')
        return context


class BitTypeCreateView(LoginRequiredMixin, CreateView):
    model = BitType
    template_name = 'workorders/bittype_form.html'
    fields = ['category', 'size', 'smi_name', 'hdbs_name', 'series', 
              'hdbs_mn', 'ref_hdbs_mn', 'ardt_item_number',
              'body_material', 'no_of_blades', 'cutter_size', 'gage_length',
              'order_level', 'description', 'is_active']
    success_url = reverse_lazy('workorders:bittype_list')


class BitTypeDetailView(LoginRequiredMixin, DetailView):
    model = BitType
    template_name = 'workorders/bittype_detail.html'
    context_object_name = 'bit_type'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get drill bits of this type
        context['drill_bits'] = self.object.drillbit_set.all()[:20]
        return context


class BitTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = BitType
    template_name = 'workorders/bittype_form.html'
    fields = ['category', 'size', 'smi_name', 'hdbs_name', 'series', 
              'hdbs_mn', 'ref_hdbs_mn', 'ardt_item_number',
              'body_material', 'no_of_blades', 'cutter_size', 'gage_length',
              'order_level', 'description', 'is_active']
    success_url = reverse_lazy('workorders:bittype_list')


class BitSizeListView(LoginRequiredMixin, ListView):
    model = BitSize
    template_name = 'workorders/bitsize_list.html'
    context_object_name = 'bit_sizes'


class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    template_name = 'workorders/location_list.html'
    context_object_name = 'locations'
    
    def get_queryset(self):
        qs = super().get_queryset()
        location_type = self.request.GET.get('type')
        if location_type:
            qs = qs.filter(location_type=location_type)
        return qs
```

### 4.3 Templates

**Create:** `templates/workorders/bittype_list.html`
```html
{% extends 'base.html' %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold">Bit Types</h1>
        <a href="{% url 'workorders:bittype_create' %}" class="btn btn-primary">
            + Add Bit Type
        </a>
    </div>
    
    <!-- Filters -->
    <div class="bg-white rounded-lg shadow p-4 mb-6">
        <form method="get" class="flex gap-4 flex-wrap">
            <select name="category" class="select select-bordered">
                <option value="">All Categories</option>
                {% for code, name in categories %}
                <option value="{{ code }}" {% if request.GET.category == code %}selected{% endif %}>{{ name }}</option>
                {% endfor %}
            </select>
            
            <select name="series" class="select select-bordered">
                <option value="">All Series</option>
                {% for s in series_list %}
                {% if s %}
                <option value="{{ s }}" {% if request.GET.series == s %}selected{% endif %}>{{ s }}</option>
                {% endif %}
                {% endfor %}
            </select>
            
            <input type="text" name="search" placeholder="Search..." 
                   value="{{ request.GET.search }}" class="input input-bordered">
            
            <button type="submit" class="btn">Filter</button>
            <a href="{% url 'workorders:bittype_list' %}" class="btn btn-ghost">Clear</a>
        </form>
    </div>
    
    <!-- Table -->
    <div class="bg-white rounded-lg shadow overflow-x-auto">
        <table class="table w-full">
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Size</th>
                    <th>SMI Name</th>
                    <th>HDBS Name</th>
                    <th>HDBS MN</th>
                    <th>Body</th>
                    <th>Blades</th>
                    <th>Cutter</th>
                    <th>Level</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for bt in bit_types %}
                <tr>
                    <td>{{ bt.get_category_display }}</td>
                    <td>{{ bt.size.size_display|default:"-" }}</td>
                    <td><strong>{{ bt.smi_name }}</strong></td>
                    <td>{{ bt.hdbs_name|default:"-" }}</td>
                    <td>{{ bt.hdbs_mn }}</td>
                    <td>{{ bt.get_body_material_display|default:"-" }}</td>
                    <td>{{ bt.no_of_blades|default:"-" }}</td>
                    <td>{{ bt.cutter_size|default:"-" }}</td>
                    <td>{{ bt.order_level|default:"-" }}</td>
                    <td>
                        <a href="{% url 'workorders:bittype_detail' bt.pk %}" class="btn btn-sm">View</a>
                        <a href="{% url 'workorders:bittype_update' bt.pk %}" class="btn btn-sm">Edit</a>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="10" class="text-center py-8 text-gray-500">No bit types found</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <!-- Pagination -->
    {% if page_obj.has_other_pages %}
    <div class="flex justify-center mt-6">
        <div class="btn-group">
            {% if page_obj.has_previous %}
            <a href="?page={{ page_obj.previous_page_number }}" class="btn">«</a>
            {% endif %}
            <span class="btn">Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}</span>
            {% if page_obj.has_next %}
            <a href="?page={{ page_obj.next_page_number }}" class="btn">»</a>
            {% endif %}
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}
```

### 4.4 Add to Sidebar

**Add under Technical or Reference Data section:**
```html
<li x-data="{ open: false }">
    <button @click="open = !open" class="flex items-center justify-between w-full ...">
        <span>Reference Data</span>
        <svg :class="{ 'rotate-180': open }" class="w-4 h-4 transition-transform" ...>...</svg>
    </button>
    <ul x-show="open" x-collapse class="pl-4 space-y-1">
        <li><a href="{% url 'workorders:bittype_list' %}">Bit Types</a></li>
        <li><a href="{% url 'workorders:bitsize_list' %}">Bit Sizes</a></li>
        <li><a href="{% url 'workorders:location_list' %}">Locations</a></li>
    </ul>
</li>
```

---

## 🧪 TESTING CHECKLIST

- [ ] Migration applies without errors
- [ ] New BitType fields visible in admin
- [ ] `python manage.py update_bit_types` runs successfully
- [ ] `/workorders/bit-types/` list page loads
- [ ] Filters (category, series, search) work
- [ ] Create new BitType works
- [ ] Edit existing BitType works
- [ ] Sidebar navigation links work

---

## 📝 GIT WORKFLOW

```bash
# After Task 1-2 (Model + Admin updates):
git add .
git commit -m "✅ Update BitType model with category, specs, order_level fields"
git tag v0.2.7-bittype-update

# After Task 3 (Seed data):
git add .
git commit -m "✅ Add update_bit_types command with real ARDT data"
git tag v0.2.8-bittype-data

# After Task 4 (Web UI):
git add .
git commit -m "✅ Add BitType/BitSize/Location web UI pages"
git tag v0.2.9-bittype-webui

git push --tags
```

---

## 🚀 TELL CLAUDE CODE

> "Read docs/PHASE2_UPDATE.md. The Phase 2 models already exist. 
> Start with Task 1: Update the BitType model by ADDING the new fields (category, size FK, smi_name, hdbs_name, hdbs_mn, ref_hdbs_mn, ardt_item_number, body_material, no_of_blades, cutter_size, gage_length, order_level). 
> Make migrations and apply. 
> Then update admin to show new fields. 
> Test in admin. 
> Commit with tag v0.2.7-bittype-update."

---

*Document created: December 13, 2025*
