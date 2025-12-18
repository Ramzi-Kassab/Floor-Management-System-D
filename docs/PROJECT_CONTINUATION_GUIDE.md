# ARDT Floor Management System - Project Continuation Guide

> **IMPORTANT:** Always start from `master` branch and create a new feature branch for your work.

---

## Table of Contents
1. [Getting Started](#1-getting-started)
2. [Project Overview](#2-project-overview)
3. [Mandatory Reading Before Any Changes](#3-mandatory-reading-before-any-changes)
4. [Code Analysis Requirements](#4-code-analysis-requirements)
5. [Coding Standards & Rules](#5-coding-standards--rules)
6. [Common Mistakes to Avoid](#6-common-mistakes-to-avoid)
7. [Development Workflow](#7-development-workflow)
8. [Enhancement Plan - Page by Page](#8-enhancement-plan---page-by-page)
9. [Testing & Validation](#9-testing--validation)
10. [Commit Guidelines](#10-commit-guidelines)

---

## 1. Getting Started

### Branch Setup (REQUIRED FIRST STEP)

```bash
# 1. Clone or navigate to the repository
git clone https://github.com/Ramzi-Kassab/Floor-Management-System-D.git
cd Floor-Management-System-D

# 2. Ensure you're on master and it's up to date
git checkout master
git pull origin master

# 3. Create a new feature branch from master
git checkout -b feature/your-feature-name

# 4. Set up virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Run migrations
python manage.py migrate

# 7. Start development server
python manage.py runserver
```

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your database settings
# Default: SQLite for development, PostgreSQL for production
```

---

## 2. Project Overview

### What is ARDT FMS?
| Attribute | Value |
|-----------|-------|
| **Name** | ARDT Floor Management System |
| **Purpose** | Track drill bit lifecycle, repairs, inventory, work orders |
| **Client** | ARDT (drilling company in Saudi Arabia) |
| **Tech Stack** | Django 4.x, Python 3.11, PostgreSQL, Tailwind CSS, Alpine.js |
| **Scale** | 26 Django apps, 166+ models, 427 templates, 202 views |

### Key Business Rules (DO NOT MODIFY)

| Rule | Format/Description |
|------|---------------------|
| **Drill Bit Serial Number** | Always 8 digits (e.g., `14141234`) |
| **Finance SN** | `serial_number + "R" + (repair_count + rerun_count_factory)` |
| **Actual Repair SN** | `serial_number + "R" + (repair_count + repair_count_usa)` |
| **Design Uniqueness** | Design = Size + HDBS Type (unique together) |
| **Order Levels** | 3=separate, 4=welded, 5=cutters brazed, 6=painted/ready |

### Real Data (LOCKED - DO NOT CHANGE)

| Category | Data |
|----------|------|
| **Departments** | 10 departments (from QAS-105) |
| **Positions** | 54 positions with reporting structure |
| **Employees** | 27 (Gustavo Escobar=GM, Saad Jamal=Tech Manager) |
| **Companies** | 8 (ARAMCO is primary client) |
| **Rigs** | 088TE, GW-88, PA-785, AD-72, AD-74 |
| **Wells** | QTIF-598, BRRI-350, HZEM-611202 |

### Reference Tables (Pre-populated)

| Table | Count | Examples |
|-------|-------|----------|
| BitSize | 18 | 3 3/4" to 17 1/2" |
| BitType | Multiple | FC/MT/TCI categories |
| Location | Multiple | WAREHOUSE, REPAIR_SHOP, RIG |
| ConnectionType | Multiple | API connections |
| ConnectionSize | Multiple | Standard sizes |
| FormationType | Multiple | Rock formations |
| Application | Multiple | Drilling applications |
| IADCCode | Multiple | Industry codes |

---

## 3. Mandatory Reading Before Any Changes

### READ THESE FILES IN ORDER:

```
Priority 1 - Project Context:
├── docs/FMC_D_Chat_Summary.md          # Project overview, real data, decisions
├── docs/MASTER_PLAN.md                  # Phase 1 implementation plan
└── docs/EXECUTIVE_SUMMARY_START_HERE.md # Quick start guide

Priority 2 - Implementation Details:
├── docs/PHASE2_PRODUCTS_IMPLEMENTATION.md  # Phase 2 - Products & Bit Tracking
├── docs/PHASE2_UPDATE.md                   # BitType model updates
└── docs/DESIGN_PAGE_IMPLEMENTATION.md      # Design page with reference tables

Priority 3 - Architecture:
├── docs/ARCHITECTURE.md                 # System architecture
├── docs/PERMISSIONS_IMPLEMENTATION_GUIDE.md # Role-based permissions
└── ARDT_ERD_v5.4_VISION.dbml           # Database schema (DBML format)
```

### Why Reading First is Critical:
1. **Prevents duplicate models** - Many models already exist
2. **Maintains consistency** - Follow established patterns
3. **Preserves business logic** - Don't break existing rules
4. **Saves time** - Avoid rewriting existing functionality

---

## 4. Code Analysis Requirements

### BEFORE suggesting any enhancement, you MUST analyze:

#### 4.1 Project Structure
```bash
# List all apps
ls -la apps/

# Count models, views, templates
find apps/ -name "models.py" -exec grep -l "class.*Model" {} \;
find apps/ -name "views.py" | wc -l
find templates/ -name "*.html" | wc -l
```

#### 4.2 All Existing Models
```bash
# List all model classes
grep -r "class.*models.Model" apps/ --include="*.py"

# Check model relationships
grep -r "ForeignKey\|OneToOneField\|ManyToManyField" apps/ --include="*.py"

# Check for similar model names before creating new ones
grep -ri "class.*YourProposedModelName" apps/ --include="*.py"
```

#### 4.3 All URL Patterns
```bash
# List all URLs to avoid duplicates
grep -r "path\|re_path" apps/*/urls.py
cat ardt_fms/urls.py
```

#### 4.4 Template Structure
```bash
# List all templates
find templates/ -name "*.html"

# Check template inheritance
grep -r "extends" templates/ --include="*.html" | head -20
```

#### 4.5 Admin Registrations
```bash
# Check what's registered in admin
grep -r "admin.site.register\|@admin.register" apps/ --include="*.py"
```

---

## 5. Coding Standards & Rules

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Models | PascalCase | `DrillBit`, `BitType`, `WorkOrder` |
| Fields | snake_case | `serial_number`, `bit_type`, `created_at` |
| URLs (path) | kebab-case | `/drill-bits/`, `/bit-types/`, `/work-orders/` |
| URL names | snake_case | `bittype_list`, `drillbit_detail` |
| Templates | snake_case | `bittype_list.html`, `drillbit_form.html` |
| Views (Class) | PascalCase + View | `BitTypeListView`, `DrillBitCreateView` |
| Views (Function) | snake_case | `bittype_list`, `drillbit_create` |

### Model Rules

```python
# ALWAYS use these patterns:

class YourModel(models.Model):
    # 1. Always add timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 2. Always use PROTECT for critical ForeignKeys
    category = models.ForeignKey(
        'Category',
        on_delete=models.PROTECT,  # Not CASCADE!
        related_name='items'       # Always add related_name
    )

    # 3. Always add Meta class
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'

    # 4. Always add __str__ method
    def __str__(self):
        return self.name
```

### URL Rules

```python
# In apps/yourapp/urls.py
from django.urls import path
from . import views

app_name = 'yourapp'  # ALWAYS set app_name

urlpatterns = [
    # Use consistent naming: model_action
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/create/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('items/<int:pk>/edit/', views.ItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),
]
```

### Template Rules

```html
<!-- All templates MUST extend base.html -->
{% extends 'base.html' %}

{% block title %}Page Title{% endblock %}

{% block content %}
<!-- Your content here -->
{% endblock %}

{% block extra_js %}
<!-- Optional JavaScript -->
{% endblock %}
```

---

## 6. Common Mistakes to Avoid

### NEVER DO THESE:

| Mistake | Why It's Bad | Correct Approach |
|---------|--------------|------------------|
| ❌ Create model without checking if similar exists | Creates duplicates, breaks relationships | Search codebase first |
| ❌ Use different naming conventions | Inconsistency, confusion | Follow standards above |
| ❌ Add URLs without namespace | URL conflicts, template errors | Always set `app_name` |
| ❌ Forget to register models in admin.py | Can't manage in admin | Register immediately |
| ❌ Skip migrations after model changes | Database out of sync | Always run migrations |
| ❌ Create templates outside standard structure | Templates not found | Use `templates/appname/` |
| ❌ Use `CASCADE` for critical FKs | Data loss on delete | Use `PROTECT` |
| ❌ Forget `related_name` on FKs | Can't reverse lookup | Always add it |
| ❌ Hardcode URLs in templates | Breaks when URLs change | Use `{% url 'app:name' %}` |
| ❌ Create duplicate URL names | Routing conflicts | Check existing URLs first |

### Before Creating Any New Model, Ask:

1. Does a model with this name already exist?
2. Does a model with similar PURPOSE already exist?
3. Can I extend an existing model instead?
4. Have I read all related documentation?

---

## 7. Development Workflow

### Step-by-Step Process

```
1. START FROM MASTER
   └── git checkout master && git pull

2. CREATE FEATURE BRANCH
   └── git checkout -b feature/your-feature

3. READ DOCUMENTATION
   └── Read all relevant docs (Section 3)

4. ANALYZE EXISTING CODE
   └── Search for similar models/views/templates

5. PLAN CHANGES
   └── Document what you'll add/modify

6. IMPLEMENT
   └── Follow coding standards (Section 5)

7. TEST
   └── Run checks and tests (Section 9)

8. COMMIT
   └── Use proper commit message (Section 10)

9. PUSH & PR
   └── Push branch, create pull request
```

---

## 8. Enhancement Plan - Page by Page

### CRITICAL: Before implementing ANY page:
1. Check if similar page/functionality exists
2. Read related models and understand relationships
3. Follow existing patterns in similar pages

---

### Phase 1: Core Foundation Pages (Already Implemented)

| # | Page | Status | Location |
|---|------|--------|----------|
| 1.1 | Login/Authentication | ✅ Done | `accounts/` |
| 1.2 | Dashboard | ✅ Done | `dashboard/` |
| 1.3 | User Profile | ✅ Done | `accounts/profile.html` |
| 1.4 | Settings | ✅ Done | `accounts/settings.html` |

---

### Phase 2: Organization & Setup Pages

| # | Page | Status | App | Description |
|---|------|--------|-----|-------------|
| 2.1 | Department List/CRUD | ✅ Done | `organization` | 10 departments |
| 2.2 | Position List/CRUD | ✅ Done | `organization` | 54 positions |
| 2.3 | Employee List/CRUD | ✅ Done | `organization` | 27 employees |
| 2.4 | Company/Customer List | ✅ Done | `organization` | 8 companies |
| 2.5 | Rig Management | ✅ Done | `organization` | Rig tracking |
| 2.6 | Well Management | ✅ Done | `organization` | Well tracking |
| 2.7 | Location Management | ✅ Done | `organization` | Warehouse, shops, etc. |

---

### Phase 3: Inventory & Products Pages

| # | Page | Status | App | Description |
|---|------|--------|-----|-------------|
| 3.1 | Category List/CRUD | ✅ Done | `inventory` | Item categories |
| 3.2 | Item List | ✅ Done | `inventory` | All inventory items |
| 3.3 | Item Detail | ✅ Done | `inventory` | Full item info |
| 3.4 | Item Create/Edit | ✅ Done | `inventory` | Item forms |
| 3.5 | Variant Management | ✅ Done | `inventory` | Item variants |
| 3.6 | Attribute Management | ✅ Done | `inventory` | Custom attributes |
| 3.7 | Unit of Measure | ✅ Done | `inventory` | UOM management |
| 3.8 | Material Lots | ✅ Done | `inventory` | Lot tracking |
| 3.9 | Stock Transactions | 🔄 Review | `inventory` | In/out movements |

---

### Phase 4: Technology & Design Pages

| # | Page | Status | App | Description |
|---|------|--------|-----|-------------|
| 4.1 | Design List | ✅ Done | `technology` | Bit designs |
| 4.2 | Design Detail | ✅ Done | `technology` | Design specs |
| 4.3 | Design Create/Edit | ✅ Done | `technology` | Design forms |
| 4.4 | BitSize Reference | ✅ Done | `technology` | 18 standard sizes |
| 4.5 | Connection Types | ✅ Done | `technology` | API connections |
| 4.6 | Connection Sizes | ✅ Done | `technology` | Connection dimensions |
| 4.7 | Formation Types | ✅ Done | `technology` | Rock formations |
| 4.8 | Applications | ✅ Done | `technology` | Drilling applications |
| 4.9 | IADC Codes | ✅ Done | `technology` | Industry codes |
| 4.10 | Breaker Slots | ✅ Done | `technology` | Slot configurations |
| 4.11 | Pocket Layouts | ✅ Done | `technology` | Pocket configurations |
| 4.12 | Upper Section Types | ✅ Done | `technology` | Section types |

---

### Phase 5: Work Order Pages

| # | Page | Status | App | Description |
|---|------|--------|-----|-------------|
| 5.1 | Work Order List | ✅ Done | `workorders` | All work orders |
| 5.2 | Work Order Detail | ✅ Done | `workorders` | Full WO info |
| 5.3 | Work Order Create | ✅ Done | `workorders` | New WO form |
| 5.4 | Work Order Edit | ✅ Done | `workorders` | Edit WO |
| 5.5 | BitType Management | ✅ Done | `workorders` | Bit type catalog |
| 5.6 | DrillBit Tracking | ✅ Done | `workorders` | Individual bits |
| 5.7 | Bit Evaluation | ✅ Done | `workorders` | Dull grading |
| 5.8 | Status Transitions | ✅ Done | `workorders` | WO workflow |

---

### Phase 6: Quality & Compliance Pages

| # | Page | Status | App | Description |
|---|------|--------|-----|-------------|
| 6.1 | Inspection List | ✅ Done | `quality` | Quality inspections |
| 6.2 | NCR Management | ✅ Done | `quality` | Non-conformance |
| 6.3 | Compliance Requirements | ✅ Done | `compliance` | Requirements tracking |
| 6.4 | Certifications | ✅ Done | `compliance` | Cert management |
| 6.5 | Audit Trails | ✅ Done | `compliance` | Audit logging |
| 6.6 | Training Records | ✅ Done | `compliance` | Employee training |

---

### Phase 7: Operations Pages

| # | Page | Status | App | Description |
|---|------|--------|-----|-------------|
| 7.1 | Dispatch Dashboard | ✅ Done | `dispatch` | Dispatch overview |
| 7.2 | Dispatch Management | ✅ Done | `dispatch` | Dispatch CRUD |
| 7.3 | Vehicle Management | ✅ Done | `dispatch` | Fleet tracking |
| 7.4 | Equipment List | ✅ Done | `maintenance` | Equipment catalog |
| 7.5 | Maintenance Schedule | ✅ Done | `maintenance` | PM schedule |
| 7.6 | Calibration Tracking | ✅ Done | `maintenance` | Tool calibration |

---

### Phase 8: Sales & Field Service Pages

| # | Page | Status | App | Description |
|---|------|--------|-----|-------------|
| 8.1 | Quote Management | ✅ Done | `sales` | Sales quotes |
| 8.2 | Order Management | ✅ Done | `sales` | Sales orders |
| 8.3 | Service Sites | ✅ Done | `sales` | Field locations |
| 8.4 | Field Technicians | ✅ Done | `sales` | Tech assignments |
| 8.5 | Service Requests | ✅ Done | `sales` | Field requests |
| 8.6 | Service Reports | ✅ Done | `sales` | Field reports |

---

### Phase 9: Reporting & Analytics Pages

| # | Page | Status | App | Description |
|---|------|--------|-----|-------------|
| 9.1 | Report Builder | ✅ Done | `reports` | Custom reports |
| 9.2 | Saved Reports | ✅ Done | `reports` | Report library |
| 9.3 | Dashboard Widgets | ✅ Done | `dashboard` | KPI widgets |
| 9.4 | Export Functions | 🔄 Review | `reports` | PDF/Excel export |

---

### Phase 10: Enhancement Priorities (TO DO)

| Priority | Enhancement | App | Description |
|----------|-------------|-----|-------------|
| HIGH | Item Detail Conditional Sections | `inventory` | Show sections based on category flags |
| HIGH | Stock Level Alerts | `inventory` | Low stock notifications |
| MEDIUM | Barcode/QR Integration | `scancodes` | Scan functionality |
| MEDIUM | Advanced Search | `all` | Global search feature |
| MEDIUM | Bulk Operations | `inventory` | Mass updates |
| LOW | Mobile Optimization | `all` | Responsive improvements |
| LOW | Dark Mode | `all` | Theme toggle |

---

### Pending Decision: Conditional Sections in Item Detail

**Question:** Should Suppliers, Identifiers, and Warehouse Planning sections be shown for ALL items, or conditional?

**Recommended Solution:** Add flags to Category model:

```python
# In apps/inventory/models.py - Category model
class Category(models.Model):
    # ... existing fields ...
    show_suppliers = models.BooleanField(default=True, help_text="Show suppliers section for items")
    show_identifiers = models.BooleanField(default=True, help_text="Show identifiers section")
    show_planning = models.BooleanField(default=True, help_text="Show warehouse planning section")
    show_bit_specs = models.BooleanField(default=False, help_text="Show bit specifications")
    show_cutter_specs = models.BooleanField(default=False, help_text="Show cutter specifications")
```

**Implementation Steps:**
1. Add fields to Category model
2. Create migration
3. Update item_detail.html template with conditionals
4. Update Category form to include new fields
5. Set defaults for existing categories

---

## 9. Testing & Validation

### Before Every Commit

```bash
# 1. Check for issues
python manage.py check

# 2. Preview migrations (don't apply yet)
python manage.py makemigrations --dry-run

# 3. If changes needed, create migrations
python manage.py makemigrations

# 4. Apply migrations
python manage.py migrate

# 5. Run tests
python manage.py test

# 6. Test locally
python manage.py runserver
# Visit http://127.0.0.1:8000 and test changes
```

### Validation Checklist

- [ ] No duplicate model names
- [ ] No duplicate URL names
- [ ] All ForeignKeys have `related_name`
- [ ] All ForeignKeys use `PROTECT` (not CASCADE)
- [ ] All templates extend `base.html`
- [ ] All new models registered in `admin.py`
- [ ] Migrations apply without errors
- [ ] No breaking changes to existing functionality
- [ ] Manual testing of new features

---

## 10. Commit Guidelines

### Commit Message Format

```
type(scope): brief description

Detailed description of changes (if needed)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples

```bash
# Feature
git commit -m "feat(inventory): add conditional sections to item detail"

# Fix
git commit -m "fix(workorders): correct bittype URL routing"

# Docs
git commit -m "docs: update PROJECT_CONTINUATION_GUIDE"
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    QUICK REFERENCE                          │
├─────────────────────────────────────────────────────────────┤
│ START:     git checkout master && git pull                  │
│ BRANCH:    git checkout -b feature/name                     │
│ CHECK:     python manage.py check                           │
│ MIGRATE:   python manage.py makemigrations && migrate       │
│ TEST:      python manage.py test                            │
│ RUN:       python manage.py runserver                       │
├─────────────────────────────────────────────────────────────┤
│ Models:    PascalCase (DrillBit)                           │
│ Fields:    snake_case (serial_number)                       │
│ URLs:      kebab-case (/drill-bits/)                        │
│ Templates: snake_case (drillbit_list.html)                  │
├─────────────────────────────────────────────────────────────┤
│ ALWAYS:    Read docs first, search before creating          │
│ NEVER:     Duplicate models, skip migrations, use CASCADE   │
└─────────────────────────────────────────────────────────────┘
```

---

## Getting Help

- **Documentation:** `docs/` folder
- **ERD/Schema:** `ARDT_ERD_v5.4_VISION.dbml`
- **Issues:** GitHub Issues
- **Project Owner:** Ramzi Kassab

---

*Last Updated: December 2024*
*Version: 1.0*
