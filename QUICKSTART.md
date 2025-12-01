# ARDT FMS v5.4 - Quick Start Guide

## 📦 Package Contents

**File:** `ardt_fms_phase0_complete.tar.gz` (61 KB)

**Contains:**
- Complete Django 5.1 project with 21 apps
- 114 database models
- 119 Python files
- 4 JSON fixtures
- Complete admin configuration
- Requirements.txt with 40 packages
- Documentation (README.md, PHASE_0_COMPLETE.md)

---

## 🚀 Installation Steps

### 1. Extract Archive

```bash
tar -xzf ardt_fms_phase0_complete.tar.gz
cd ardt_fms
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database

```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE ardt_fms;
CREATE USER ardt_user WITH PASSWORD 'SecurePassword123!';
GRANT ALL PRIVILEGES ON DATABASE ardt_fms TO ardt_user;
\q
```

### 5. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
nano .env

# Minimum required settings:
# DATABASE_URL=postgresql://ardt_user:SecurePassword123!@localhost:5432/ardt_fms
# SECRET_KEY=your-secret-key-here
# DEBUG=True
```

### 6. Initialize Database

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Load initial data
python manage.py loaddata fixtures/roles.json
python manage.py loaddata fixtures/step_types.json
python manage.py loaddata fixtures/field_types.json
python manage.py loaddata fixtures/checkpoint_types.json

# Create superuser
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Access at: **http://localhost:8000/admin**

---

## ✅ Verification Checklist

After installation, verify:

- [ ] Server starts without errors
- [ ] Admin login works
- [ ] 21 apps visible in admin
- [ ] 12 roles loaded
- [ ] 10 step types loaded
- [ ] 16 field types loaded
- [ ] 8 checkpoint types loaded
- [ ] Can create a department
- [ ] Can create a user
- [ ] Can assign a role

---

## 📊 What's Included

### Core Applications (P1)
✅ Organization (5 models)  
✅ Accounts (6 models + mixins)  
✅ Procedures (9 models)  
✅ Forms Engine (5 models)  
✅ Execution (6 models)  
✅ DRSS (2 models)  
✅ Sales (8 models)  
✅ Work Orders (7 models)  
✅ Technology (4 models)  
✅ Quality (3 models)  
✅ Inventory (5 models)  
✅ Scan Codes (2 models)  
✅ Notifications (7 models)  
✅ Maintenance (5 models)  
✅ Documents (2 models)  
✅ Planning (10 models) - NEW v5.4

### Extended Operations (P2-P4)
✅ Supply Chain (8 models)  
✅ Dispatch (4 models)  
✅ HR (5 models)  
✅ HSSE (3 models)

### Future
✅ ERP Integration (2 models)

---

## 🔍 Quick Test

```bash
# Django shell test
python manage.py shell

# Test imports
>>> from apps.accounts.models import User, Role
>>> from apps.workorders.models import WorkOrder, DrillBit
>>> from apps.procedures.models import Procedure
>>> Role.objects.count()
12
>>> exit()
```

---

## 📁 Project Structure

```
ardt_fms/
├── ardt_fms/          # Settings & configuration
├── apps/              # 21 Django applications
├── fixtures/          # Initial data (4 files)
├── templates/         # Base templates (empty - Sprint 1)
├── static/            # Static files (empty - Sprint 1)
├── media/             # User uploads
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── manage.py          # Django CLI
├── README.md          # Main documentation
└── PHASE_0_COMPLETE.md # Implementation summary
```

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
python manage.py showmigrations

# Admin
python manage.py createsuperuser
python manage.py changepassword username

# Data
python manage.py loaddata fixtures/roles.json
python manage.py dumpdata accounts.Role > roles_backup.json

# Testing
pytest
pytest --cov
```

---

## 📚 Documentation

1. **README.md** - Complete setup and usage guide
2. **PHASE_0_COMPLETE.md** - Implementation details
3. **Model docstrings** - In each app's models.py
4. **.env.example** - Configuration reference

---

## 🎯 Next Steps (Sprint 1)

Now that Phase 0 is complete, you can start Sprint 1:

1. **Authentication Views**
   - Login/logout
   - Password reset
   - User profile

2. **Dashboard**
   - Home page
   - Role-based widgets
   - Quick stats

3. **Templates**
   - Base template with navigation
   - Component library
   - HTMX integration

4. **Core Views**
   - Department CRUD
   - User management
   - Work order list/detail

---

## ⚠️ Important Notes

### What's NOT Included (Phase 0)
- ❌ No views/templates (admin only)
- ❌ No business logic implementations
- ❌ No API endpoints
- ❌ No frontend code (HTMX/Alpine.js/Tailwind)
- ❌ No authentication views
- ❌ No tests

These will be implemented in Sprint 1+.

### Database Migrations
First-time migrations may take 2-3 minutes due to 114 tables.

### Admin Access
Only the superuser account can access admin initially.  
Use the admin to create departments, roles, and additional users.

---

## 🐛 Troubleshooting

### Import Errors
```bash
# Ensure all apps are in INSTALLED_APPS
python manage.py check
```

### Migration Errors
```bash
# Reset migrations if needed (development only!)
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
python manage.py makemigrations
python manage.py migrate
```

### Database Connection
```bash
# Test database connection
python manage.py dbshell
```

---

## 📞 Support Resources

- **Django Documentation**: https://docs.djangoproject.com/en/5.1/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/16/
- **Project README**: See README.md in project root
- **Model Documentation**: See docstrings in apps/*/models.py

---

## 🎉 Success!

If you've completed all steps and can access the admin panel, **Phase 0 is successfully installed!**

You're now ready to begin Sprint 1 development.

---

**ARDT FMS v5.4 - Phase 0**  
**Status:** ✅ Installation Complete  
**Next:** Sprint 1 - Views & Templates
