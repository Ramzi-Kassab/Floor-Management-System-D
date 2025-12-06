# 🔧 MIGRATION GENERATION GUIDE
## Fix Critical Blocker #1 - Step by Step

**Problem:** Project has 131 models but ZERO migrations  
**Impact:** Database cannot be created, project cannot run  
**Time Required:** 2-3 hours  
**Difficulty:** Medium (circular dependencies may occur)  

---

## 🎯 WHAT WE'RE DOING

**Goal:** Generate migration files for all 25 apps so Django can create the database.

**What This Does:**
- Creates `migrations/` folder in each app
- Generates `0001_initial.py` for each app
- Allows `python manage.py migrate` to work
- Creates all database tables

---

## ⚠️ BEFORE YOU START

### 1. Backup Everything

```bash
# Create a backup branch
git checkout -b backup-before-migrations
git add .
git commit -m "Backup before generating migrations"
git push origin backup-before-migrations

# Return to main work
git checkout -b add-migrations
```

### 2. Verify Environment

```bash
# Check Python version
python --version  # Should be 3.10+

# Check Django version
python -c "import django; print(django.get_version())"  # Should be 5.1+

# Check database connection
python manage.py check
```

### 3. Create Test Database

```bash
# If using PostgreSQL (recommended)
createdb ardt_fms_test

# Update .env for test database
DATABASE_URL=postgres://user:password@localhost/ardt_fms_test
```

---

## 📋 STEP-BY-STEP PROCESS

### Phase 1: Core Apps (No Dependencies)

These apps don't depend on others, so we'll create their migrations first.

#### Step 1.1: Organization (Foundation)

```bash
python manage.py makemigrations organization
```

**Expected Output:**
```
Migrations for 'organization':
  apps/organization/migrations/0001_initial.py
    - Create model Department
    - Create model Position
    - Create model Theme
    ...
```

**If Errors:**
- Check models.py for syntax errors
- Check for missing imports
- Fix and retry

#### Step 1.2: Accounts (Depends on organization)

```bash
python manage.py makemigrations accounts
```

**Expected Output:**
```
Migrations for 'accounts':
  apps/accounts/migrations/0001_initial.py
    - Create model User
    - Create model Role
    - Create model UserProfile
    ...
```

#### Step 1.3: Technology (Foundation)

```bash
python manage.py makemigrations technology
```

#### Step 1.4: Forms Engine (Foundation)

```bash
python manage.py makemigrations forms_engine
```

**Checkpoint:**
```bash
# Verify migrations created
find apps -name "0001_initial.py" | wc -l
# Should show 4
```

---

### Phase 2: Business Apps (Have Dependencies)

These apps reference the foundation apps.

#### Step 2.1: Sales

```bash
python manage.py makemigrations sales
```

**Possible Error:**
```
apps.sales.models.Customer: (fields.E300) Field defines a relation with model 'accounts.User', 
which is either not installed, or is abstract.
```

**Fix:**
Ensure accounts migrations were created in Phase 1.

#### Step 2.2: Inventory

```bash
python manage.py makemigrations inventory
```

#### Step 2.3: Procedures

```bash
python manage.py makemigrations procedures
```

#### Step 2.4: Quality

```bash
python manage.py makemigrations quality
```

#### Step 2.5: Work Orders

```bash
python manage.py makemigrations workorders
```

**Possible Error:**
```
apps.workorders.models.DrillBit: (fields.E300) Field defines a relation with model 'sales.Customer', 
which is either not installed, or is abstract.
```

**Fix:**
Ensure sales migrations were created first.

---

### Phase 3: Execution & Integration Apps

#### Step 3.1: Execution

```bash
python manage.py makemigrations execution
```

#### Step 3.2: Planning

```bash
python manage.py makemigrations planning
```

#### Step 3.3: DRSS

```bash
python manage.py makemigrations drss
```

---

### Phase 4: Support Apps

#### Step 4.1: Documents

```bash
python manage.py makemigrations documents
```

#### Step 4.2: Scancodes

```bash
python manage.py makemigrations scancodes
```

#### Step 4.3: Notifications

```bash
python manage.py makemigrations notifications
```

#### Step 4.4: Maintenance

```bash
python manage.py makemigrations maintenance
```

#### Step 4.5: Reports

```bash
python manage.py makemigrations reports
```

---

### Phase 5: Future/Skeleton Apps

#### Step 5.1: Supply Chain

```bash
python manage.py makemigrations supplychain
```

#### Step 5.2: Dispatch

```bash
python manage.py makemigrations dispatch
```

#### Step 5.3: HR

```bash
python manage.py makemigrations hr
```

#### Step 5.4: HSSE

```bash
python manage.py makemigrations hsse
```

#### Step 5.5: ERP Integration

```bash
python manage.py makemigrations erp_integration
```

#### Step 5.6: Dashboard

```bash
python manage.py makemigrations dashboard
```

---

### Phase 6: Verify All Migrations

```bash
# Count migration files
find apps -name "0001_initial.py" | wc -l
# Should show 25 (one for each app)

# List all apps with migrations
python manage.py showmigrations
```

**Expected Output:**
```
accounts
 [ ] 0001_initial
dashboard
 [ ] 0001_initial
dispatch
 [ ] 0001_initial
...
```

---

## 🚨 TROUBLESHOOTING COMMON ISSUES

### Error 1: Circular Dependency

**Error Message:**
```
django.db.migrations.exceptions.CircularDependencyError: 
apps.workorders.models.WorkOrder -> apps.sales.models.Customer
apps.sales.models.SalesOrder -> apps.workorders.models.WorkOrder
```

**Solution A: String References (Recommended)**
Already done in your code! Good job.

**Solution B: Break the Cycle**
```bash
# Create sales migrations first
python manage.py makemigrations sales

# Then workorders
python manage.py makemigrations workorders

# Django will create proper dependencies
```

**Solution C: Manual Dependency Editing**
```python
# If still failing, edit migration file
# apps/workorders/migrations/0001_initial.py

class Migration(migrations.Migration):
    dependencies = [
        ('sales', '0001_initial'),  # Add explicit dependency
    ]
```

---

### Error 2: Model Not Found

**Error Message:**
```
apps.quality.models.NCR: (fields.E300) Field defines a relation with model 'workorders.WorkOrder', 
which is either not installed, or is abstract.
```

**Solution:**
Create migrations for the referenced app first:
```bash
python manage.py makemigrations workorders
python manage.py makemigrations quality
```

---

### Error 3: Conflicting Migrations

**Error Message:**
```
CommandError: Conflicting migrations detected; multiple leaf nodes in the migration graph
```

**Solution:**
```bash
# Merge conflicting migrations
python manage.py makemigrations --merge app_name
```

---

### Error 4: No Changes Detected

**Command:**
```bash
python manage.py makemigrations app_name
```

**Output:**
```
No changes detected in app 'app_name'
```

**Reasons:**
1. App already has migrations (check `migrations/` folder)
2. App has no models (check `models.py`)
3. Models not imported in `__init__.py`

**Solution:**
```bash
# Force creation if needed
python manage.py makemigrations app_name --empty

# Or check if models file is empty
cat apps/app_name/models.py
```

---

### Error 5: Auth User Model Issues

**Error Message:**
```
ValueError: The field admin.LogEntry.user was declared with a lazy reference to 'accounts.user', 
but app 'accounts' isn't installed
```

**Solution:**
Ensure `AUTH_USER_MODEL` is set correctly in settings.py:
```python
# ardt_fms/settings.py
AUTH_USER_MODEL = 'accounts.User'
```

---

## 🗄️ APPLYING MIGRATIONS TO DATABASE

After ALL migrations are created:

### Step 1: Check Status

```bash
python manage.py showmigrations
```

All should show `[ ]` (not applied).

### Step 2: Apply Migrations

```bash
# Apply all migrations
python manage.py migrate

# Or apply one app at a time if issues
python manage.py migrate organization
python manage.py migrate accounts
python manage.py migrate sales
# ... etc
```

**Expected Output:**
```
Operations to perform:
  Apply all migrations: accounts, admin, auth, contenttypes, dashboard, ...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying accounts.0001_initial... OK
  Applying admin.0001_initial... OK
  ...
  Applying workorders.0001_initial... OK
```

### Step 3: Verify Database

```bash
# Connect to database
python manage.py dbshell

# List tables (PostgreSQL)
\dt

# Should see: accounts_user, workorders_workorder, etc.
```

---

## ✅ VALIDATION CHECKLIST

After completing all steps:

- [ ] All 25 apps have `migrations/` folder
- [ ] All 25 apps have `0001_initial.py` file
- [ ] `python manage.py showmigrations` shows all migrations
- [ ] `python manage.py migrate` completes successfully
- [ ] Database tables created (check with `\dt` in psql)
- [ ] No error messages
- [ ] `python manage.py check` shows no issues

---

## 🔄 IF SOMETHING GOES WRONG

### Nuclear Option: Start Over

**If migrations are hopelessly broken:**

```bash
# 1. Delete all migration files
find apps -path "*/migrations/*.py" -not -name "__init__.py" -delete

# 2. Delete migration folders (careful!)
find apps -name "migrations" -type d -exec rm -rf {} +

# 3. Drop and recreate database
dropdb ardt_fms_test
createdb ardt_fms_test

# 4. Recreate migrations following this guide

# 5. Apply migrations
python manage.py migrate
```

### Partial Reset: One App

**If one app's migrations are broken:**

```bash
# 1. Delete that app's migrations
rm -rf apps/problem_app/migrations/

# 2. Recreate migrations
python manage.py makemigrations problem_app

# 3. Fake the migration if database already has tables
python manage.py migrate problem_app --fake-initial
```

---

## 📊 EXPECTED FINAL STATE

### File Structure

```
apps/
├── accounts/
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py  ← Created!
│   ├── models.py
│   └── ...
├── workorders/
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py  ← Created!
│   ├── models.py
│   └── ...
└── ... (25 apps total)
```

### Database Tables

```sql
-- Should have ~131 tables
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public';

-- Sample tables:
accounts_user
accounts_role
workorders_drillbit
workorders_workorder
quality_inspection
quality_ncr
inventory_inventoryitem
...
```

---

## 📝 COMMIT YOUR WORK

```bash
# Add all migrations
git add apps/*/migrations/

# Commit
git commit -m "Generate initial migrations for all 25 apps

- Created migrations for all models
- Fixed circular dependency issues
- Verified database creation
- All tables created successfully"

# Push
git push origin add-migrations
```

---

## 🎯 WHAT'S NEXT

After migrations are created and applied:

1. ✅ Create superuser
   ```bash
   python manage.py createsuperuser
   ```

2. ✅ Test admin interface
   ```bash
   python manage.py runserver
   # Visit http://localhost:8000/admin/
   ```

3. ✅ Create basic test data
   ```bash
   python manage.py shell
   >>> from apps.accounts.models import User
   >>> User.objects.create(...)
   ```

4. ✅ Run the application
   ```bash
   python manage.py runserver
   # Visit http://localhost:8000/
   ```

5. ➡️ Move on to **Testing Guide** (next document)

---

## 💡 PRO TIPS

### Tip 1: Use Migration Squashing Later

After initial migrations work:
```bash
# Combine multiple migrations into one
python manage.py squashmigrations app_name 0001 0010
```

### Tip 2: Always Review Generated Migrations

```bash
# Before applying, review the migration file
cat apps/app_name/migrations/0001_initial.py

# Look for:
# - Correct field types
# - Proper relationships
# - Sensible defaults
```

### Tip 3: Document Migration Issues

Create `docs/MIGRATION_LOG.md`:
```markdown
# Migration Issues Log

## 2024-12-05: Initial Migration Generation

### Issues Encountered:
1. Circular dependency between workorders and sales
   - Fixed by: Creating sales first
   
2. Missing AUTH_USER_MODEL
   - Fixed by: Verifying settings.py

### Time Taken: 2.5 hours
### Final Status: SUCCESS
```

---

## 🎉 SUCCESS CRITERIA

You'll know you're successful when:

✅ No errors during `makemigrations`  
✅ No errors during `migrate`  
✅ Can create superuser  
✅ Admin interface loads  
✅ Can create objects via admin  
✅ Database tables exist  
✅ Application starts without errors  

**When all these pass, you've fixed Critical Blocker #1!** 🎊

---

**END OF MIGRATION GUIDE**

**Estimated Time:** 2-3 hours  
**Difficulty:** Medium  
**Success Rate:** 95% if following guide  

**Next:** Read the Testing Quick Start Guide
