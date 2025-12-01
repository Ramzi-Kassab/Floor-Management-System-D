# ARDT FMS v5.4 - Django Project Skeleton

**Advanced Rework & Drill Bits Technology - Field Management System**  
Phase 0 Implementation - Complete Database Schema & Project Structure

---

## 📋 Overview

This is the complete Django 5.1 project skeleton for ARDT FMS v5.4, implementing all 114 database tables across 21 applications. The project uses PostgreSQL 16, HTMX 2.0, Alpine.js 3.14, and Tailwind CSS 3.4.

**Implementation Status:**
- ✅ **Phase 0 Complete**: All models, admin, and structure implemented
- ⏳ **Sprint 1+**: Views, templates, and business logic (not included)

---

## 🏗️ Project Structure

```
ardt_fms/
├── ardt_fms/               # Django project settings
│   ├── settings.py         # Complete configuration
│   ├── urls.py            # URL routing with 21 app includes
│   ├── views.py           # Error handlers (400, 403, 404, 500)
│   ├── wsgi.py / asgi.py
│   └── __init__.py
├── apps/                   # 21 Django applications
│   ├── organization/       # 🟢 P1 - Departments, positions, themes
│   ├── accounts/          # 🟢 P1 - Users, roles, permissions + mixins
│   ├── procedures/        # 🟢 P1 - 9 models + step types
│   ├── forms_engine/      # 🟢 P1 - Dynamic forms with 16 field types
│   ├── execution/         # 🟢 P1 - Procedure execution tracking
│   ├── drss/              # 🟢 P1 - ARAMCO DRSS requests
│   ├── sales/             # 🟢 P1 - Customers, orders, rigs, wells
│   ├── workorders/        # 🟢 P1 - WOs, drill bits, materials, time
│   ├── technology/        # 🟢 P1 - Designs, BOMs, cutter layouts
│   ├── quality/           # 🟢 P1 - Inspections, NCRs
│   ├── inventory/         # 🟢 P1 - Items, stock, transactions
│   ├── scancodes/         # 🟢 P1 - QR/Barcode registry
│   ├── notifications/     # 🟢 P1 - Notifications, tasks, audit logs
│   ├── maintenance/       # 🟢 P1 - Equipment, MWOs
│   ├── documents/         # 🟢 P1 - Document management
│   ├── planning/          # 🟢 P1 - Notion-style planning (NEW v5.4)
│   ├── supplychain/       # 🟡 P2 - PRs, POs, suppliers
│   ├── dispatch/          # 🟠 P3 - Vehicles, dispatches
│   ├── hr/                # 🔴 P4 - Attendance, leave
│   ├── hsse/              # 🔴 P4 - HOC, incidents, journey mgmt
│   └── erp_integration/   # ⚪ FUTURE - ERP sync
├── fixtures/              # Initial data
│   ├── roles.json         # 12 system roles
│   ├── step_types.json    # 10 procedure step types
│   ├── field_types.json   # 16 form field types
│   └── checkpoint_types.json # 8 checkpoint types
├── requirements.txt       # 40 Python packages
├── .env.example          # Environment variables template
├── manage.py             # Django CLI
└── README.md             # This file
```

---

## 📊 Database Schema Summary

### Total: 114 Tables Across 21 Apps

- 🟢 **Priority 1** (Core): 81 tables - Essential for basic operations
- 🟡 **Priority 2** (Extended): 8 tables - Supply chain
- 🟠 **Priority 3** (Full): 4 tables - Dispatch & logistics
- 🔴 **Priority 4** (Advanced): 8 tables - HR & HSSE
- ⚪ **FUTURE**: 2 tables - ERP integration

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
- Python 3.11+
- PostgreSQL 16
- Node.js 18+ (for Tailwind CSS)
```

### 2. Setup Database

```sql
CREATE DATABASE ardt_fms;
CREATE USER ardt_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ardt_fms TO ardt_user;
```

### 3. Install & Initialize

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Load initial data
python manage.py loaddata fixtures/roles.json
python manage.py loaddata fixtures/step_types.json
python manage.py loaddata fixtures/field_types.json
python manage.py loaddata fixtures/checkpoint_types.json

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

Access at: http://localhost:8000/admin

---

## 🔑 Key Features

### Core Applications (P1)

**Organization & Accounts**
- Multi-tenant department structure
- Role-based access control with 12 predefined roles
- User preferences and themes
- Number sequence generation

**Procedure Engine**
- 10 step types (Operation, Inspection, Approval, Decision, etc.)
- Dynamic branching with conditional logic
- 8 checkpoint types with tolerance checking
- Version control

**Work Order Management**
- FC/RC drill bit tracking with QR codes
- Multiple WO types (NEW, REWORK, RETROFIT)
- BOM integration
- Material & time tracking
- Bit evaluation workflow

**Quality System**
- Inspections with procedure execution
- NCR workflow with dispositions
- Photo evidence
- CAPA linking

**Planning Module (NEW v5.4)**
- Notion-style boards and sprints
- Wiki pages with versioning
- Labels, watchers, story points

---

## 📦 Technology Stack

- Django 5.1
- PostgreSQL 16
- HTMX 2.0 (Sprint 1+)
- Alpine.js 3.14 (Sprint 1+)
- Tailwind CSS 3.4 (Sprint 1+)
- Celery + Redis (configured)

---

## 🛠️ Common Commands

```bash
# Development
python manage.py runserver
python manage.py shell
python manage.py dbshell

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata fixtures/roles.json

# Testing
pytest
pytest --cov

# Production
python manage.py collectstatic
python manage.py check --deploy
```

---

## 📝 Model Conventions

All models follow consistent patterns:

```python
# Audit fields (standard)
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
created_by = models.ForeignKey(User, ...)

# Status enums
class Status(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'

# Soft delete ready
is_active = models.BooleanField(default=True)

# Meta configuration
class Meta:
    db_table = 'table_name'
    ordering = ['-created_at']
    verbose_name = 'Model Name'
```

---

## 🎯 Next Steps (Sprint 1+)

1. **Templates & Views**: Implement CRUD operations
2. **Authentication**: Login, logout, password reset
3. **Dashboard**: Widgets and KPIs
4. **Business Logic**: WO workflow, procedure execution
5. **Frontend**: HTMX, Alpine.js, Tailwind integration
6. **API**: REST endpoints for mobile app

---

## 🐛 Phase 0 Limitations

- ❌ No views/templates
- ❌ No authentication UI
- ❌ No business logic
- ❌ No API endpoints
- ❌ No file uploads
- ✅ All models defined
- ✅ Admin interface configured
- ✅ Fixtures provided

---

## 📚 Documentation

Each model includes:
- Priority indicator (🟢🟡🟠🔴⚪)
- Comprehensive docstrings
- Choice enums
- Property methods
- Audit fields
- Admin configuration

---

## 🗺️ Roadmap

- **Sprint 1**: Authentication & Dashboard
- **Sprint 2**: Work Orders & Procedures
- **Sprint 3**: Planning & Quality
- **Sprint 4**: Mobile App & API

---

**Status:** ✅ Phase 0 Complete - 114 tables implemented  
**Version:** 5.4  
**Date:** December 2024

---

For detailed information, see model docstrings in each app's `models.py` file.
