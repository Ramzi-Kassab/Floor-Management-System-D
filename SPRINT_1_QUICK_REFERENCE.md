# 🚀 SPRINT 1 - QUICK REFERENCE

Essential commands, URLs, and code snippets for Sprint 1 development.

---

## 🔧 Common Commands

### Development
```bash
# Start dev server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load fixtures
python manage.py loaddata fixtures/roles.json

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test apps.workorders

# Run specific test
python manage.py test apps.workorders.tests.WorkOrderTests.test_wo_creation

# Check for issues
python manage.py check

# Shell
python manage.py shell
```

### Database
```bash
# Show migrations
python manage.py showmigrations

# Show SQL for migration
python manage.py sqlmigrate workorders 0001

# Reset migrations (careful!)
python manage.py migrate workorders zero

# Database backup
pg_dump ardt_fms > backup.sql

# Database restore
psql ardt_fms < backup.sql
```

### Git
```bash
# Check status
git status

# Add files
git add .

# Commit
git commit -m "Sprint 1: Add authentication system"

# Push
git push origin main

# Pull latest
git pull origin main
```

---

## 📁 Project Structure

```
ardt_fms/
├── apps/
│   ├── accounts/         # User & auth
│   ├── workorders/       # Work orders & drill bits
│   ├── dashboard/        # Dashboards
│   └── [18 more apps]
├── templates/
│   ├── base.html
│   ├── base_auth.html
│   ├── components/
│   ├── accounts/
│   ├── workorders/
│   └── dashboard/
├── static/
├── media/
├── fixtures/
├── logs/
└── ardt_fms/            # Project settings
    ├── settings.py
    ├── urls.py
    └── wsgi.py
```

---

## 🔗 Important URLs

### Application URLs
```
/                           → Redirect to dashboard
/dashboard/                 → Dashboard home
/accounts/login/            → Login page
/accounts/logout/           → Logout
/accounts/profile/          → User profile
/workorders/                → Work order list
/workorders/create/         → Create WO
/workorders/<id>/           → WO detail
/workorders/drillbits/      → Drill bit list
/workorders/drillbits/<id>/ → Drill bit detail
/admin/                     → Django admin
```

### URL Patterns
```python
# In urls.py
path('workorders/', include('apps.workorders.urls')),
path('dashboard/', include('apps.dashboard.urls')),
path('accounts/', include('apps.accounts.urls')),
```

---

## 🎨 Tailwind CSS Classes

### Layout
```html
<!-- Container -->
<div class="max-w-7xl mx-auto px-4">

<!-- Grid -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">

<!-- Flex -->
<div class="flex items-center justify-between">

<!-- Spacing -->
<div class="space-y-6">  <!-- Vertical spacing -->
<div class="space-x-4">  <!-- Horizontal spacing -->
```

### Components
```html
<!-- Button Primary -->
<button class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
    Click Me
</button>

<!-- Button Secondary -->
<button class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
    Cancel
</button>

<!-- Input -->
<input type="text" 
       class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">

<!-- Card -->
<div class="bg-white rounded-lg shadow p-6">
    <!-- Content -->
</div>

<!-- Badge -->
<span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
    Active
</span>
```

---

## 📝 Code Snippets

### View Pattern
```python
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.accounts.mixins import RoleRequiredMixin

class MyListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = MyModel
    template_name = 'app/model_list.html'
    context_object_name = 'objects'
    paginate_by = 20
    required_roles = ['PLANNER', 'ADMIN']
    
    def get_queryset(self):
        return super().get_queryset().select_related('related_model')
```

### Form Pattern
```python
from django import forms

class MyForm(forms.ModelForm):
    class Meta:
        model = MyModel
        fields = ['field1', 'field2']
        widgets = {
            'field1': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300'
            })
        }
    
    def clean_field1(self):
        data = self.cleaned_data['field1']
        # Validation logic
        return data
```

### Template Pattern
```html
{% extends 'base.html' %}

{% block title %}My Page{% endblock %}

{% block content %}
<div class="space-y-6">
    <h1 class="text-2xl font-bold">My Page</h1>
    
    {% for item in items %}
        {{ item.name }}
    {% empty %}
        <p>No items found</p>
    {% endfor %}
</div>
{% endblock %}
```

### Test Pattern
```python
from django.test import TestCase

class MyModelTests(TestCase):
    def setUp(self):
        self.obj = MyModel.objects.create(
            field1='value1'
        )
    
    def test_something(self):
        self.assertEqual(self.obj.field1, 'value1')
```

---

## 🔐 Role Checking

### In Views
```python
# Check if user has role
if request.user.has_role('ADMIN'):
    # Admin only code
    pass

# Check if user has any role
if request.user.has_any_role('PLANNER', 'MANAGER'):
    # Planner or Manager code
    pass
```

### In Templates
```html
{% load role_tags %}

{% if request.user|has_role:'ADMIN' %}
    <!-- Admin only content -->
{% endif %}

{% if request.user|has_any_role:'PLANNER,MANAGER' %}
    <!-- Planner or Manager content -->
{% endif %}
```

---

## 🎯 HTMX Examples

### Basic Usage
```html
<!-- Load content on click -->
<button hx-get="/api/data/" 
        hx-target="#result" 
        hx-swap="innerHTML">
    Load Data
</button>

<div id="result"></div>

<!-- Form submission -->
<form hx-post="/api/submit/" 
      hx-target="#response">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

### Django View for HTMX
```python
def htmx_view(request):
    html = render_to_string('partial.html', {'data': data})
    return HttpResponse(html)
```

---

## 🎨 Alpine.js Examples

### Basic Reactive Data
```html
<div x-data="{ open: false }">
    <button @click="open = !open">Toggle</button>
    <div x-show="open">
        Content
    </div>
</div>
```

### Dropdown Menu
```html
<div x-data="{ open: false }">
    <button @click="open = !open">
        Menu
    </button>
    <div x-show="open" @click.away="open = false">
        <!-- Menu items -->
    </div>
</div>
```

---

## 📊 Database Queries

### Optimization
```python
# Select related (ForeignKey, OneToOne)
queryset = Model.objects.select_related('fk_field')

# Prefetch related (ManyToMany, reverse FK)
queryset = Model.objects.prefetch_related('m2m_field')

# Only specific fields
queryset = Model.objects.only('field1', 'field2')

# Defer fields
queryset = Model.objects.defer('large_field')

# Count without loading
count = Model.objects.count()

# Exists check
exists = Model.objects.filter(name='test').exists()
```

### Filtering
```python
# Basic filter
Model.objects.filter(status='ACTIVE')

# Multiple conditions
Model.objects.filter(status='ACTIVE', priority='HIGH')

# OR conditions
from django.db.models import Q
Model.objects.filter(Q(status='ACTIVE') | Q(priority='HIGH'))

# Exclude
Model.objects.exclude(status='CANCELLED')

# Case-insensitive
Model.objects.filter(name__icontains='test')

# Date range
Model.objects.filter(created_at__date=today)
Model.objects.filter(created_at__range=[start, end])
```

---

## 🛠️ Troubleshooting

### Migration Issues
```bash
# Fake a migration
python manage.py migrate app_name 0001 --fake

# Reset all migrations
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
python manage.py makemigrations
python manage.py migrate
```

### Static Files
```bash
# Clear static files
rm -rf staticfiles/*

# Re-collect
python manage.py collectstatic --clear --no-input

# Check settings
DEBUG = True  # Automatically serves static in dev
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'
```

### Permission Issues
```bash
# Check user roles
python manage.py shell
>>> from apps.accounts.models import User
>>> user = User.objects.get(username='test')
>>> user.roles.all()
>>> user.has_role('ADMIN')
```

---

## 🔍 Debugging

### Django Debug Toolbar
```python
# Add to INSTALLED_APPS
'debug_toolbar',

# Add to MIDDLEWARE
'debug_toolbar.middleware.DebugToolbarMiddleware',

# Add to urls.py
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Configure
INTERNAL_IPS = ['127.0.0.1']
```

### Print Debugging
```python
# In views
print(f"User: {request.user}")
print(f"Query: {queryset.query}")

# In templates
{{ variable|pprint }}  # Pretty print
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.debug('Debug message')
logger.info('Info message')
logger.warning('Warning message')
logger.error('Error message')
```

---

## 📚 Useful Resources

- Django Docs: https://docs.djangoproject.com/
- Tailwind Docs: https://tailwindcss.com/docs
- HTMX Docs: https://htmx.org/docs/
- Alpine.js Docs: https://alpinejs.dev/
- Lucide Icons: https://lucide.dev/icons/

---

**Quick Reference - Version 1.0**  
**Last Updated:** December 2024
