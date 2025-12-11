# MASTER_PLAN_CORRECTION.md

> **URGENT FOR CLAUDE CODE** - The previous seeding used WRONG data. 
> Delete all seeded records and re-seed with CORRECT data from this file.

---

## ⚠️ PROBLEM

The previous `seed_all` command created WRONG data:
- ❌ Wrong users (5 fake users instead of 27 real employees)
- ❌ Wrong departments (wrong names)
- ❌ Wrong positions (only 12 instead of 54)
- ❌ Wrong company types

---

## 🔧 WHAT TO DO

### Step 1: Delete ALL Existing Seeded Data

Create a management command `apps/common/management/commands/clear_seed_data.py`:

```python
# This command should DELETE all records from:
# - Users (except superuser)
# - Departments
# - Positions  
# - Customers/Companies
# - Rigs
# - Wells
# - Permissions/Roles
```

Run: `python manage.py clear_seed_data`

### Step 2: Update ALL Seed Commands with CORRECT Data Below

---

## ✅ CORRECT DATA

### 2.1 Departments (10 Departments)

**DELETE the old departments and create these:**

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

**WRONG names to DELETE:**
- ❌ "Production" → Use "Operations"
- ❌ "Logistics" → Use "Procurement & Logistics"
- ❌ "Technical" → Use "Technology"
- ❌ "Field Operations" → Merge into "Operations" or "Sales"

---

### 2.2 Positions (54 Positions from QAS-105)

**DELETE all 12 old positions and create these 54:**

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
| APL | Assistant Procurement & Logistics Manager | PROC | PLM |
| LGC | Logistics Coordinator | PROC | PLM |
| DSP | Dispatch Inspector | PROC | PLM |
| DRV | Driver | PROC | PLM |
| OPC | Operations Coordinator | PROC | PLM |
| AOC | Assistant Operations Coordinator | PROC | PLM |
| STK | Storekeeper | PROC | PLM |
| PRS | Procurement Supervisor | PROC | PLM |
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
| HRS | HR Supervisor | HR | HRM |
| HRC | HR Coordinator | HR | HR Supervisor |
| ADS | Admin Supervisor | HR | HRM |
| ADC | Admin Coordinator | HR | Admin Supervisor |

#### IT Department
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| ITM | IT & ERP Manager | IT | GM |
| ITC | IT Control Engineer | IT | ITM |
| PRE | Production Encoder | IT | ITM |

#### HSSE Department
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| HSM | HSSE Manager | HSSE | GM |
| HSS | HSE Supervisor | HSSE | HSM |

#### General/Support
| Code | Title | Department | Reports To |
|------|-------|------------|------------|
| GWK | General Worker | OPS | Supervisors |
| GRD | Guard | HSSE | HSE Supervisor |
| OFB | Office Boy | HR | Admin Supervisor |

---

### 2.3 Users/Employees (27 Real People)

**DELETE all 5 fake users (keep only superuser if exists) and create these 27:**

**Password for all:** `Ardt@2025`

| # | Username | First Name | Last Name | Position | Department | Email | Mobile |
|---|----------|------------|-----------|----------|------------|-------|--------|
| 1 | g.escobar | Gustavo | Escobar | General Manager | EXEC | gustavofredy.escobar@halliburton.com | 506-517-855 |
| 2 | s.jamal | Saad | Jamal | Technology Manager | TECH | saad.jamal@halliburton.com | 500-611-270 |
| 3 | o.abdelbaset | Omar | Abdel Baset | Sales Manager | SALES | omar.abdelbaset@halliburton.com | 537-070-233 |
| 4 | a.elsafi | Ahmed Emad | Elsafi | Sales Account Lead | SALES | ahmed.elsafi@halliburton.com | 550-103-145 |
| 5 | j.kunjur | Jainuddin | Kunjur | Field Operation Specialist | SALES | zainukunjur@ardtco.com | 538-250-722 |
| 6 | a.buobaid | Abdulaziz | Al Buobaid | Operations Manager | OPS | azizbuobaid@ardtco.com | 543-331-108 |
| 7 | r.shetty | Ranjith | Shetty | Manufacturing Supervisor | OPS | ranjith@ardtco.com | 532-461-019 |
| 8 | r.kassab | Ramzi | Kassab | Repair Supervisor | OPS | ramzi@ardtco.com | 570-646-911 |
| 9 | r.alwasmi | Radi | Al Wasmi | Repair Technician | OPS | radi@ardtco.com | 505-511-385 |
| 10 | h.alsaba | Habib Salah | Al Saba | Repair Technician | OPS | habeebs1399@gmail.com | 540-742-881 |
| 11 | h.almuhnna | Habib Tahar | Al Muhnna | Repair Technician | OPS | hbhb-2010@hotmail.com | 501-520-531 |
| 12 | a.chisti | Ahmed Faizan | Chisti | Quality Manager | QC | chisti@ardtco.com | 538-071-220 |
| 13 | j.lohar | Javed Umer | Lohar | Quality Assurance Coordinator | QC | javedlohar@ardtco.com | 531-019-157 |
| 14 | a.khan | Adil | Khan | Final Inspector | QC | adil.khan@ardtco.com | 531-156-753 |
| 15 | a.alhammad | Ali | Al Hammad | QC Inspector | QC | ali.alhammad@ardtco.com | 550-868-041 |
| 16 | m.asad | Muhammad | Asad | Procurement & Logistics Manager | PROC | muhammad.mukhtar@ardtco.com | 508-921-463 |
| 17 | f.alhammad | Fathima | Alhammad | Procurement Supervisor | PROC | fatimah@ardtco.com | 556-536-664 |
| 18 | r.badaam | Riyadh | Badaam | Procurement Specialist | PROC | riyadh.badaam@ardtco.com | 545-182-942 |
| 19 | p.peer | Peerla Imam | Peer | Logistics Coordinator | PROC | peerla.peer@ardtco.com | 557-468-588 |
| 20 | j.alghafly | Jehad | Alghafly | Logistics Coordinator | PROC | jehad@ardtco.com | 533-418-111 |
| 21 | a.vangali | Ajad | Vangali | Dispatch Inspector | PROC | azad658@gmail.com | 531-017-322 |
| 22 | a.mirza | Anas | Mirza | Storekeeper | PROC | storekeeper@ardtco.com | 540-729-874 |
| 23 | l.aljubran | Layla | Al Jubran | Assistant Operations Coordinator | PROC | layla@ardtco.com | 533-622-120 |
| 24 | w.khan | Waseem M. | Khan | Finance Controller | FIN | wkhan@ardtco.com | 581-691-218 |
| 25 | m.irshad | Mohammad | Irshad | IT & ERP Manager | IT | irshad@ardtco.com | 547-222-795 |
| 26 | a.alfarhan | Abdullah | Al Farhan | HR & Administration Manager | HR | hr.manager@ardtco.com | 555-000-001 |
| 27 | k.almansour | Khalid | Al Mansour | HSSE Manager | HSSE | hsse.manager@ardtco.com | 555-000-002 |

---

### 2.4 Customers & Competitors (8 Companies)

**DELETE old customers and create these 8:**

| Code | Company Name | Type | Notes |
|------|--------------|------|-------|
| ARAMCO | Saudi Aramco | Primary Client | Main operator |
| SCHLUM | Schlumberger | Service Competitor | Competes on services |
| HALIBTN | Halliburton | Service Competitor - Client | JV Partner |
| BAKER | Baker Hughes | Service Competitor | Competes on services |
| WEATHER | Weatherford | Service Competitor - Client | Also a client |
| NOV | NOV Inc. | Equipment Supplier - Competitor | Equipment |
| NATPET | National Petroleum | Regional Client | Regional operator |
| SPERRY | Sperry Drilling Services | Service Company - Client | Part of Halliburton, directional drilling, RSS, mud motors. Eastern Province (Saihat, Al Khobar). Historical name: Sperry Sun Saudia |

**Company Types to use:**
- `Primary Client`
- `Regional Client`
- `Service Competitor`
- `Service Competitor - Client`
- `Service Company - Client`
- `Equipment Supplier - Competitor`

---

### 2.5 Rigs (Keep as is - 5 Rigs)

These are correct, no changes needed:

| Code | Name | Customer | Type | Status |
|------|------|----------|------|--------|
| 088TE | Rig 088TE | Saudi Aramco | Land Rig | Active |
| GW-88 | Rig GW-88 | Saudi Aramco | Land Rig | Active |
| PA-785 | Rig PA-785 | Saudi Aramco | Land Rig | Active |
| AD-72 | Rig AD-72 | Saudi Aramco | Land Rig | Active |
| AD-74 | Rig AD-74 | Saudi Aramco | Land Rig | Active |

---

### 2.6 Wells (Keep as is - 21 Wells)

These are correct, no changes needed.

---

## 📋 EXECUTION ORDER

1. **Create** `clear_seed_data.py` command
2. **Run** `python manage.py clear_seed_data` to delete wrong data
3. **Update** `seed_departments.py` with correct 10 departments
4. **Update** `seed_positions.py` with correct 54 positions
5. **Update** `seed_users.py` with correct 27 employees
6. **Update** `seed_customers.py` with correct 8 companies
7. **Run** `python manage.py seed_all --force`
8. **Test** login with `r.kassab` / `Ardt@2025`
9. **Commit** with message: "fix: Corrected all seed data with real ARDT employees and structure"
10. **Tag** as `v0.2.0-data-correction`

---

## 🎯 VERIFICATION

After running, verify:
- [ ] 10 departments exist with correct names
- [ ] 54 positions exist
- [ ] 27 users exist (can login)
- [ ] 8 companies exist with correct types
- [ ] 5 rigs exist
- [ ] 21 wells exist

---

*This correction overwrites MASTER_PLAN.md implementation report*
*Source: Real ARDT data from QAS-105 and company contacts*
