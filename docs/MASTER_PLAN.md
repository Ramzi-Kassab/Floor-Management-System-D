# ARDT Floor Management System - Master Plan v2.0

> **FOR CLAUDE CODE** - Follow this plan step by step. Do not skip steps.

---

## 1. Development Order

| Step | Task | Why This Order |
|------|------|----------------|
| **1** | Login Page | First thing users see - must work perfectly |
| **2** | Users | Need users to log in - create real ARDT employees |
| **3** | Departments | Organizational structure - users belong to departments |
| **4** | Positions | Job roles within departments |
| **5** | Permissions | Who can do what - based on positions |
| **6** | Customers | Real customers: Saudi Aramco |
| **7** | Rigs | Real rigs: 088TE, GW-88, PA-785, AD-72, AD-74 |
| **8** | Wells | Real wells: QTIF-598, BRRI-350, etc. |

---

## 2. Real Data (From Morning Report 01-02-2025)

### 2.1 Rigs

| Code | Name | Customer | Type |
|------|------|----------|------|
| 088TE | Rig 088TE | Saudi Aramco | Land Rig |
| GW-88 | Rig GW-88 | Saudi Aramco | Land Rig |
| PA-785 | Rig PA-785 | Saudi Aramco | Land Rig |
| AD-72 | Rig AD-72 | Saudi Aramco | Land Rig |
| AD-74 | Rig AD-74 | Saudi Aramco | Land Rig |

### 2.2 Wells - QTIF Field (Qatif)

| Well | Type | Target | Status |
|------|------|--------|--------|
| QTIF-598 | Development Drilling | Arab-C | Drilling |
| QTIF-284 | Next Well (NDP-12) | - | Planned |
| QTIF-545 | Next Well | - | Planned |
| QTIF-277 | Next Well | - | Planned |
| QTIF-790 | PWI (Production Well Injector) | Arab-C | Active |
| QTIF-520 | PWI | UFDL | Active |
| QTIF-521 | PWI | Arab-D | Active |
| QTIF-542 | PWI | UFDL | Active |
| QTIF-630 | WI (Water Injector) | Arab-D | Active |
| QTIF-631 | WI | Arab-D | Active |
| QTIF-632 | PWI | Arab-C | Active |
| QTIF-752 | Injector | Arab-C | Shut-in |
| QTIF-674 | Injector | Arab-C | Shut-in |
| QTIF-501 | Relief Well (Primary) | - | Standby |
| QTIF-773 | Relief Well (Secondary) | - | Standby |
| QTIF-922 | Water Well | - | Active |
| QTIF-300 | - | - | Active |

### 2.3 Wells - BRRI Field (Berri)

| Well | Type | Strip Out | Wellsite |
|------|------|-----------|----------|
| BRRI-350 | Workover | - | Active |
| BRRI-380 | Next Location | 100% | 100% |
| BRRI-335 | Next Location | 100% | 100% |
| BRRI-381 | Next Location | 50% | 0% |
| BRRI-212 | Next Location | 0% | 0% |

### 2.4 Service Companies

| Code | Company Name | Service Type |
|------|--------------|--------------|
| BHI | Baker Hughes | Directional Drilling, MWD/LWD |
| SLB | Schlumberger | Acid Services |
| HAL | Halliburton | Cementing, Kill Pump, Packers |
| NOV | National Oilwell Varco | Drilling Equipment, Jars |
| SWACO | M-I SWACO | Drilling Fluids |
| RAWABI | Rawabi Holding | H2S Monitoring |
| SINOPEC | Sinopec | Zero Discharge System |
| DLG | DLG | Intensifiers |
| GECAT | GECAT | Vacuum Tankers |
| TOTAL | Total Safety | H2S Stand Alone System |

### 2.5 Personnel (From Morning Report)

| Name | Position | Company |
|------|----------|---------|
| IBRAHIM, REDA MOHAMED | Foreman (Day) | ARDT |
| ALJAFARY, ABDULRAHMAN ZAKI | Foreman (Night) | ARDT |
| JAROUDI, BASSAM ADNAN | Engineer | ARDT |
| ELDEEB, TAREK ABD ALLA | Manager | ARDT |
| ABDULMOHSEN ALOTAIBI | Material Expeditor | Aramco |
| TURKI ALMUTAIRI | FCT | Aramco |
| IBRAHIM ELGHRBAWY | Mud Advisor | M-SWACO |
| AHMED SAFWAT | Fluid Supervisor | Baker |

### 2.6 Departments (ARDT)

| Code | Name (EN) | Name (AR) |
|------|-----------|-----------|
| EXEC | Executive Management | الإدارة التنفيذية |
| PROD | Production | الإنتاج |
| QC | Quality Control | مراقبة الجودة |
| TECH | Technical/Engineering | الهندسة والتقنية |
| SALES | Sales & Commercial | المبيعات والتجارة |
| LOG | Logistics & Warehouse | اللوجستيات والمستودعات |
| HR | Human Resources | الموارد البشرية |
| HSSE | Health, Safety, Security, Environment | الصحة والسلامة والأمن والبيئة |
| FIN | Finance & Accounting | المالية والمحاسبة |
| FIELD | Field Operations | العمليات الميدانية |

### 2.7 Positions

| Code | Title | Department | Level |
|------|-------|------------|-------|
| GM | General Manager | EXEC | 1 (Executive) |
| PROD-MGR | Production Manager | PROD | 2 (Manager) |
| PROD-SUP | Production Supervisor | PROD | 3 (Supervisor) |
| PROD-TECH | Production Technician | PROD | 4 (Staff) |
| QC-MGR | QC Manager | QC | 2 (Manager) |
| QC-INSP | QC Inspector | QC | 4 (Staff) |
| TECH-ENG | Design Engineer | TECH | 3 (Supervisor) |
| SALES-MGR | Sales Manager | SALES | 2 (Manager) |
| LOG-MGR | Logistics Manager | LOG | 2 (Manager) |
| FIELD-MGR | Field Manager | FIELD | 2 (Manager) |
| FIELD-FOR | Field Foreman | FIELD | 3 (Supervisor) |
| FIELD-ENG | Field Engineer | FIELD | 3 (Supervisor) |

---

## 3. Step-by-Step Tasks

### Step 1: Login Page

**Goal:** Professional login page with ARDT branding

**Files to modify:**
- `templates/registration/login.html`
- `static/css/login.css` (create if needed)

**Requirements:**
- [ ] ARDT logo and branding
- [ ] Username and password fields
- [ ] Remember me checkbox
- [ ] Error messages for invalid credentials
- [ ] Redirect to dashboard after login
- [ ] Responsive design (mobile friendly)

**Test criteria:**
- [ ] Page loads without errors
- [ ] Can log in with valid credentials
- [ ] Shows error with invalid credentials
- [ ] Redirects to dashboard after login

**Git commands after completion:**
```bash
git add .
git commit -m "Step 1: Enhanced login page with ARDT branding"
git tag v0.1.0-login
git push origin main --tags
```

---

### Step 2: Users

**Goal:** Seed real ARDT users

**File to create:** `apps/common/management/commands/seed_users.py`

**Users to create:**

| Username | Full Name | Position | Department |
|----------|-----------|----------|------------|
| admin | System Admin | GM | EXEC |
| t.eldeeb | Tarek Eldeeb | Manager | FIELD |
| r.ibrahim | Reda Ibrahim | Foreman | FIELD |
| a.aljafary | Abdulrahman Aljafary | Foreman | FIELD |
| b.jaroudi | Bassam Jaroudi | Engineer | FIELD |

**Command:** `python manage.py seed_users`

**Git commands after completion:**
```bash
git add .
git commit -m "Step 2: Created seed_users command with real ARDT personnel"
git tag v0.1.1-users
git push origin main --tags
```

---

### Step 3: Departments

**Goal:** Seed real departments

**File to create:** `apps/common/management/commands/seed_departments.py`

**Command:** `python manage.py seed_departments`

**Git commands after completion:**
```bash
git add .
git commit -m "Step 3: Created seed_departments command"
git tag v0.1.2-departments
git push origin main --tags
```

---

### Step 4: Positions

**Goal:** Seed real positions

**File to create:** `apps/common/management/commands/seed_positions.py`

**Command:** `python manage.py seed_positions`

**Git commands after completion:**
```bash
git add .
git commit -m "Step 4: Created seed_positions command"
git tag v0.1.3-positions
git push origin main --tags
```

---

### Step 5: Permissions

**Goal:** Set up role-based permissions

**Files to modify:**
- `apps/accounts/models.py` (if needed)
- Create permission groups

**Permission levels:**
1. **Executive** - Full access
2. **Manager** - Department access + approvals
3. **Supervisor** - Create/edit within scope
4. **Staff** - View + limited create

**Git commands after completion:**
```bash
git add .
git commit -m "Step 5: Configured role-based permissions"
git tag v0.1.4-permissions
git push origin main --tags
```

---

### Step 6: Customers

**Goal:** Seed real customers

**File to create:** `apps/common/management/commands/seed_customers.py`

**Customer:** Saudi Aramco (primary customer)

**Command:** `python manage.py seed_customers`

**Git commands after completion:**
```bash
git add .
git commit -m "Step 6: Created seed_customers command with Saudi Aramco"
git tag v0.1.5-customers
git push origin main --tags
```

---

### Step 7: Rigs

**Goal:** Seed real rigs from morning report

**File to create:** `apps/common/management/commands/seed_rigs.py`

**Command:** `python manage.py seed_rigs`

**Git commands after completion:**
```bash
git add .
git commit -m "Step 7: Created seed_rigs command with real rig data"
git tag v0.1.6-rigs
git push origin main --tags
```

---

### Step 8: Wells

**Goal:** Seed real wells from morning report

**File to create:** `apps/common/management/commands/seed_wells.py`

**Command:** `python manage.py seed_wells`

**Git commands after completion:**
```bash
git add .
git commit -m "Step 8: Created seed_wells command with real well data"
git tag v0.1.7-wells
git push origin main --tags
```

---

## 4. Git Workflow (For Every Step)

```
1. BEFORE  → git checkout -b enhancement/step-name
2. MAKE    → Make your changes
3. TEST    → Test in browser - must work
4. CHECK   → python manage.py check
5. COMMIT  → git add . && git commit -m "description"
6. TAG     → git tag v0.x.x-step-name
7. PUSH    → git push origin branch-name --tags
```

---

## 5. Rules for Claude Code

### ❌ NEVER DO:
- Change model field names after data exists
- Delete migrations - only add new ones
- Skip the git commit after completing a task
- Move to next step before completing current step
- Modify base.html without testing all pages after

### ✅ ALWAYS DO:
- Run `python manage.py check` before committing
- Test the page in browser after each change
- Create a git tag after completing each step
- Follow the step order (1 → 2 → 3 → ...)
- Use real data from this document

---

## 6. Quick Reference

### Commands

| Action | Command |
|--------|---------|
| Start server | `python manage.py runserver` |
| Check errors | `python manage.py check` |
| Make migrations | `python manage.py makemigrations` |
| Apply migrations | `python manage.py migrate` |
| Create superuser | `python manage.py createsuperuser` |
| Seed all data | `python manage.py seed_all` |

### File Locations

| What | Where |
|------|-------|
| Login template | `templates/registration/login.html` |
| Base template | `templates/base.html` |
| Sidebar | `templates/includes/sidebar.html` |
| User model | `apps/accounts/models.py` |
| Customer model | `apps/sales/models.py` |
| Rig model | `apps/sales/models.py` |
| Well model | `apps/sales/models.py` |
| Management commands | `apps/common/management/commands/` |

---

## 7. Current Instruction

**START WITH STEP 1: LOGIN PAGE**

Tell Claude Code:

> "Read the MASTER_PLAN.md file. Start with Step 1: Login Page. Make it professional with ARDT branding. Test it works. Commit with tag v0.1.0-login. Then tell me you're ready for Step 2."

---

*Last updated: December 2025*
*Data source: Morning Report 01-02-2025*
