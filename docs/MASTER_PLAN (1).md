# ARDT Floor Management System - Master Plan v3.0

> **FOR CLAUDE CODE** - Follow this plan step by step. Do not skip steps.
> **Document**: QAS/105 Rev R - 05/14/2024
> **Source**: Real ARDT data - Do NOT make up data

---

## 1. Development Order

| Step | Task | Why This Order |
|------|------|----------------|
| **1** | Login Page | First thing users see - must work perfectly |
| **2** | Users | Need users to log in - create real ARDT employees |
| **3** | Departments | Organizational structure - users belong to departments |
| **4** | Positions | Job roles within departments |
| **5** | Permissions | Who can do what - based on positions |
| **6** | Customers & Competitors | Real companies: Aramco, Schlumberger, etc. |
| **7** | Rigs | Real rigs: 088TE, GW-88, PA-785, AD-72, AD-74 |
| **8** | Wells | Real wells: QTIF-598, BRRI-350, etc. |

---

## 2. Real Data

### 2.1 Departments (10 Departments)

| Code | Name (EN) | Name (AR) |
|------|-----------|-----------|
| EXEC | Executive Management | الإدارة التنفيذية |
| TECH | Technology | التقنية |
| SALES | Sales | المبيعات |
| OPS | Operations | العمليات |
| QC | Quality | الجودة |
| PROC | Procurement & Logistics | المشتريات واللوجستيات |
| FIN | Finance | المالية |
| HR | HR & Administration | الموارد البشرية والإدارة |
| IT | Information Technology | تقنية المعلومات |
| HSSE | Health, Safety, Security, Environment | الصحة والسلامة والأمن والبيئة |

---

### 2.2 Positions (54 Positions from QAS-105)

#### Executive
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| GM | General Manager | EXEC | Board of Directors |

#### Technology Department
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| TM | Technology Manager | TECH | GM |
| ADE | Application Design Engineer | TECH | Technology Manager |
| AE | Application Engineer | TECH | Technology Manager |

#### Sales Department
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| SM | Sales Manager | SALES | GM |
| SAL | Sales Account Lead | SALES | Sales Manager |
| SAR | Sales Accounts Rep | SALES | Sales Manager |
| FOC | Field Operation Coordinator | SALES | Sales Manager |
| FOS | Field Operation Specialist | SALES | Field Operation Coordinator |
| DBO | Database Operator | SALES | Sales Manager |

#### Operations Department
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| OPM | Operations Manager | OPS | GM |
| MFS | Manufacturing Supervisor | OPS | Operations Manager |
| WLD | Welder | OPS | Manufacturing Supervisor |
| MCH | Machinist | OPS | Manufacturing Supervisor |
| FLT | Floor Technician | OPS | Manufacturing Supervisor |
| CRP | Carpenter | OPS | Manufacturing Supervisor |
| MNT | Maintenance Man | OPS | Manufacturing Supervisor |
| RPS | Repair Supervisor | OPS | Operations Manager |
| RPC | Repair Coordinator | OPS | Repair Supervisor |
| RPT | Repair Technician | OPS | Repair Supervisor |

#### Quality Department
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| QM | Quality Manager | QC | GM |
| QCC | Quality Control Coordinator | QC | Quality Manager |
| FNI | Final Inspector | QC | Quality Control Coordinator |
| QCI | QC Inspector | QC | Quality Control Coordinator |
| QAC | Quality Assurance Coordinator | QC | Quality Manager |
| DOC | Document Controller | QC | Quality Assurance Coordinator |

#### Procurement & Logistics Department
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| PLM | Procurement & Logistics Manager | PROC | GM |
| APL | Assistant Procurement & Logistics Manager | PROC | Procurement & Logistics Manager |
| LGC | Logistics Coordinator | PROC | Procurement & Logistics Manager |
| DSP | Dispatch Inspector | PROC | Procurement & Logistics Manager |
| DRV | Driver | PROC | Procurement & Logistics Manager |
| OPC | Operations Coordinator | PROC | Procurement & Logistics Manager |
| AOC | Assistant Operations Coordinator | PROC | Procurement & Logistics Manager |
| STK | Storekeeper | PROC | Procurement & Logistics Manager |
| PRS | Procurement Supervisor | PROC | Procurement & Logistics Manager |
| PRC | Procurement Specialist | PROC | Procurement Supervisor |

#### Finance Department
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| FC | Finance Controller | FIN | GM |
| CAC | Chief Accountant | FIN | Finance Controller |
| SAC | Senior Accountant | FIN | Finance Controller |
| ACC | Accountant | FIN | Senior Accountant |
| ACK | Accounts Clerk | FIN | Accountant |

#### HR & Administration Department
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| HRM | HR & Administration Manager | HR | GM |
| HRS | HR Supervisor | HR | HR & Admin Manager |
| HRC | HR Coordinator | HR | HR Supervisor |
| ADS | Admin Supervisor | HR | HR & Admin Manager |
| ADC | Admin Coordinator | HR | Admin Supervisor |

#### IT Department
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| ITM | IT & ERP Manager | IT | GM |
| ITC | IT Control Engineer | IT | IT & ERP Manager |
| PRE | Production Encoder | IT | IT & ERP Manager |

#### HSSE Department
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| HSM | HSSE Manager | HSSE | GM |
| HSS | HSE Supervisor | HSSE | HSSE Manager |

#### General/Support
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| GWK | General Worker | OPS | Supervisors |
| GRD | Guard | HSSE | HSE Supervisor |
| OFB | Office Boy | HR | Admin Supervisor |

---

### 2.3 Employees (Real ARDT Staff - 27 People)

#### Executive
| Name | Position | Email | Mobile | Ext |
|------|----------|-------|--------|-----|
| Gustavo Escobar | General Manager | gustavofredy.escobar@halliburton.com | 506-517-855 | - |

#### Technology Department
| Name | Position | Email | Mobile | Ext |
|------|----------|-------|--------|-----|
| Saad Jamal | Technology Manager | saad.jamal@halliburton.com | 500-611-270 | 132 |

#### Sales Department
| Name | Position | Email | Mobile | Ext |
|------|----------|-------|--------|-----|
| Omar Abdel Baset | Sales Manager | omar.abdelbaset@halliburton.com | 537-070-233 | - |
| Ahmed Emad Elsafi | Sales Account Lead | ahmed.elsafi@halliburton.com | 550-103-145 | - |
| Jainuddin Kunjur | Field Operation Specialist | zainukunjur@ardtco.com | 538-250-722 | - |

#### Operations Department
| Name | Position | Email | Mobile | Ext |
|------|----------|-------|--------|-----|
| Abdulaziz Al Buobaid | Operations Manager | azizbuobaid@ardtco.com | 543-331-108 | - |
| Ranjith Shetty | Manufacturing Supervisor | ranjith@ardtco.com | 532-461-019 | - |
| Ramzi Kassab | Repair Supervisor | ramzi@ardtco.com | 570-646-911 | 109 |
| Radi Al Wasmi | Repair Technician | radi@ardtco.com | 505-511-385 | - |
| Habib Salah Al Saba | Repair Technician | habeebs1399@gmail.com | 540-742-881 | - |
| Habib Tahar Al Muhnna | Repair Technician | hbhb-2010@hotmail.com | 501-520-531 | - |

#### Quality Department
| Name | Position | Email | Mobile | Ext |
|------|----------|-------|--------|-----|
| Ahmed Faizan Chisti | Quality Manager | chisti@ardtco.com | 538-071-220 | - |
| Javed Umer Lohar | Quality Assurance Coordinator | javedlohar@ardtco.com | 531-019-157 | - |
| Adil Khan | Final Inspector | adil.khan@ardtco.com | 531-156-753 | - |
| Ali Al Hammad | QC Inspector | ali.alhammad@ardtco.com | 550-868-041 | - |

#### Procurement & Logistics Department
| Name | Position | Email | Mobile | Ext |
|------|----------|-------|--------|-----|
| Muhammad Asad | Procurement & Logistics Manager | muhammad.mukhtar@ardtco.com | 508-921-463 | - |
| Fathima Alhammad | Procurement Supervisor | fatimah@ardtco.com | 556-536-664 | - |
| Riyadh Badaam | Procurement Specialist | riyadh.badaam@ardtco.com | 545-182-942 | - |
| Peerla Imam Peer | Logistics Coordinator | peerla.peer@ardtco.com | 557-468-588 | - |
| Jehad Alghafly | Logistics Coordinator | jehad@ardtco.com | 533-418-111 | - |
| Ajad Vangali | Dispatch Inspector | azad658@gmail.com | 531-017-322 | - |
| Anas Mirza | Storekeeper | - | 540-729-874 | - |
| Layla Al Jubran | Assistant Operations Coordinator | layla@ardtco.com | 533-622-120 | - |

#### Finance Department
| Name | Position | Email | Mobile | Ext |
|------|----------|-------|--------|-----|
| Waseem M. Khan | Finance Controller | wkhan@ardtco.com | 581-691-218 | - |

#### IT Department
| Name | Position | Email | Mobile | Ext |
|------|----------|-------|--------|-----|
| Mohammad Irshad | IT & ERP Manager | irshad@ardtco.com | 547-222-795 | - |

#### HR & Administration Department
| Name | Position | Email | Mobile | Ext |
|------|----------|-------|--------|-----|
| Abdullah Al Farhan | HR & Administration Manager | hr.manager@ardtco.com | 555-000-001 | - |

#### HSSE Department
| Name | Position | Email | Mobile | Ext |
|------|----------|-------|--------|-----|
| Khalid Al Mansour | HSSE Manager | hsse.manager@ardtco.com | 555-000-002 | - |

---

### 2.4 Customers & Competitors

| Code | Company Name | Type | Notes |
|------|--------------|------|-------|
| ARAMCO | Saudi Aramco | Primary Client | Main operator |
| SCHLUM | Schlumberger | Service Competitor | Competes on services |
| HALIBTN | Halliburton | Service Competitor - Client | JV Partner |
| BAKER | Baker Hughes | Service Competitor | Competes on services |
| WEATHER | Weatherford | Service Competitor - Client | Also a client |
| NOV | NOV Inc. | Equipment Supplier - Competitor | Equipment |
| NATPET | National Petroleum | Regional Client | Regional operator |

---

### 2.5 Rigs (From Morning Report 01-02-2025)

| Code | Name | Customer | Type | Status |
|------|------|----------|------|--------|
| 088TE | Rig 088TE | Saudi Aramco | Land Rig | Active |
| GW-88 | Rig GW-88 | Saudi Aramco | Land Rig | Active |
| PA-785 | Rig PA-785 | Saudi Aramco | Land Rig | Active |
| AD-72 | Rig AD-72 | Saudi Aramco | Land Rig | Active |
| AD-74 | Rig AD-74 | Saudi Aramco | Land Rig | Active |

---

### 2.6 Wells - QTIF Field (Qatif)

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

### 2.7 Wells - BRRI Field (Berri)

| Well | Type | Strip Out | Wellsite |
|------|------|-----------|----------|
| BRRI-350 | Workover | - | Active |
| BRRI-380 | Next Location | 100% | 100% |
| BRRI-335 | Next Location | 100% | 100% |
| BRRI-381 | Next Location | 50% | 0% |
| BRRI-212 | Next Location | 0% | 0% |

---

### 2.8 Service Companies

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

---

## 3. Step-by-Step Tasks

### Step 1: Login Page ✅ (If completed)

**Goal:** Professional login page with ARDT branding

**Git commands after completion:**
```bash
git add .
git commit -m "Step 1: Enhanced login page with ARDT branding"
git tag v0.1.0-login
git push origin main --tags
```

---

### Step 2: Users

**Goal:** Seed real ARDT users (27 employees)

**File to create:** `apps/common/management/commands/seed_users.py`

**Command:** `python manage.py seed_users`

**Password for all:** `Ardt@2025` (temporary - users change on first login)

**Git commands after completion:**
```bash
git add .
git commit -m "Step 2: Created seed_users command with 27 real ARDT employees"
git tag v0.1.1-users
git push origin main --tags
```

---

### Step 3: Departments

**Goal:** Seed 10 real departments

**File to create:** `apps/common/management/commands/seed_departments.py`

**Command:** `python manage.py seed_departments`

**Git commands after completion:**
```bash
git add .
git commit -m "Step 3: Created seed_departments command with 10 departments"
git tag v0.1.2-departments
git push origin main --tags
```

---

### Step 4: Positions

**Goal:** Seed 54 real positions from QAS-105

**File to create:** `apps/common/management/commands/seed_positions.py`

**Command:** `python manage.py seed_positions`

**Git commands after completion:**
```bash
git add .
git commit -m "Step 4: Created seed_positions command with 54 positions"
git tag v0.1.3-positions
git push origin main --tags
```

---

### Step 5: Permissions

**Goal:** Set up role-based permissions

**Permission levels:**
1. **Executive** (GM) - Full access
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

### Step 6: Customers & Competitors

**Goal:** Seed real companies (7 companies)

**File to create:** `apps/common/management/commands/seed_companies.py`

**Command:** `python manage.py seed_companies`

**Git commands after completion:**
```bash
git add .
git commit -m "Step 6: Created seed_companies with customers and competitors"
git tag v0.1.5-companies
git push origin main --tags
```

---

### Step 7: Rigs

**Goal:** Seed 5 real rigs from morning report

**File to create:** `apps/common/management/commands/seed_rigs.py`

**Command:** `python manage.py seed_rigs`

**Git commands after completion:**
```bash
git add .
git commit -m "Step 7: Created seed_rigs command with 5 real rigs"
git tag v0.1.6-rigs
git push origin main --tags
```

---

### Step 8: Wells

**Goal:** Seed 22 real wells (17 QTIF + 5 BRRI)

**File to create:** `apps/common/management/commands/seed_wells.py`

**Command:** `python manage.py seed_wells`

**Git commands after completion:**
```bash
git add .
git commit -m "Step 8: Created seed_wells command with 22 real wells"
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
- Make up fake data - ALL data is in this document
- Change model field names after data exists
- Delete migrations - only add new ones
- Skip the git commit after completing a task
- Move to next step before completing current step
- Modify base.html without testing all pages after

### ✅ ALWAYS DO:
- Use ONLY data from this document
- Run `python manage.py check` before committing
- Test the page in browser after each change
- Create a git tag after completing each step
- Follow the step order (1 → 2 → 3 → ...)

---

## 6. Quick Reference

### Company Info
- **Company:** Arabian Rockbits & Drilling Tools Co. Ltd (ARDT)
- **Address:** 69/14 Street, 2nd Industrial City Dammam, Saudi Arabia
- **Phone:** (966) 13-812-1180
- **Domain:** ardtco.com
- **JV Partner:** Halliburton

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

## 7. Summary

| Category | Count | Status |
|----------|-------|--------|
| Departments | 10 | ✅ Ready |
| Positions | 54 | ✅ Ready |
| Employees | 27 | ✅ Ready |
| Companies | 7 | ✅ Ready |
| Rigs | 5 | ✅ Ready |
| Wells | 22 | ✅ Ready |
| Service Companies | 10 | ✅ Ready |

---

*Last updated: December 2025*
*Data source: QAS-105, Morning Report 01-02-2025, Real ARDT contacts*
*Version: 3.0 - Real Data Only*
