# FMC D Project Chat Summary
**Date:** December 11-12, 2025  
**Project:** Floor Management System for ARDT (Al Rushaid Drilling Tools)

---

## 1. Project Overview

ARDT is a joint venture between Al Rushaid Group and Halliburton, specializing in drill bit manufacturing, repair, and field services for Saudi Aramco and other oil companies.

### Current Project Status
| Component | Status |
|-----------|--------|
| Django Apps | 26 complete |
| Models | 166+ complete |
| Templates | 427 exist (need polish) |
| Views | 202 complete |
| Backend Logic | 98% complete |
| UI/UX | Basic - needs enhancement |
| Data | 0% (empty database) |

---

## 2. Enhancement Priority Order

The agreed-upon enhancement sequence (foundation first):

### Phase 1: Foundation
| Step | Component | Why |
|------|-----------|-----|
| 1 | Login Page | First thing users see |
| 2 | Users | Need users to log in |
| 3 | Departments | Organizational structure |
| 4 | Positions | Job roles in departments |
| 5 | Permissions | Who can do what |

### Phase 2: Master Data
| Step | Component |
|------|-----------|
| 6 | Customers & Companies |
| 7 | Rigs |
| 8 | Wells |
| 9 | Products (Drill Bits) |
| 10 | Inventory |

### Phase 3: Operations
- Work Orders
- Job Cards
- Quality/Inspections
- Logistics/Dispatch

---

## 3. Real Data Requirements

### Departments (10 total)
1. Executive
2. Technology
3. Sales
4. IT
5. Procurement & Logistics (renamed from "Supply Chain")
6. Finance
7. HR & Administration
8. Quality
9. HSSE
10. Operations

### Key Personnel (27 employees identified)

| Name | Position | Department | Email |
|------|----------|------------|-------|
| Gustavo Escobar | General Manager | Executive | gustavofredy.escobar@halliburton.com |
| Saad Jamal | Technology Manager | Technology | saad.jamal@halliburton.com |
| Omar Abdel Baset | Sales Manager | Sales | omar.abdelbaset@halliburton.com |
| Abdulaziz Al Buobaid | Operations Manager | Operations | azizbuobaid@ardtco.com |
| Ramzi Kassab | Repair Supervisor | Operations | ramzi@ardtco.com |
| Ahmed Faizan Chisti | Quality Manager | Quality | chisti@ardtco.com |
| Muhammad Asad | Procurement & Logistics Manager | Procurement & Logistics | muhammad.mukhtar@ardtco.com |
| Waseem M. Khan | Finance Controller | Finance | wkhan@ardtco.com |
| Mohammad Irshad | IT & ERP Manager | IT | irshad@ardtco.com |

*Full list: 27 employees with contact details available in MASTER_PLAN.md*

### Companies/Clients

| Code | Name | Type |
|------|------|------|
| ARAMCO | Saudi Aramco | Primary Client |
| SCHLUM | Schlumberger | Service Competitor |
| HALIBTN | Halliburton | Service Competitor - Client |
| BAKER | Baker Hughes | Service Competitor |
| WEATHER | Weatherford | Service Competitor - Client |
| NOV | NOV Inc. | Equipment Supplier - Competitor |
| NATPET | National Petroleum | Regional Client |
| SPERRY | Sperry Drilling Services | Service Company - Client |

### Real Rigs (from Morning Report)
- 088TE, GW-88, PA-785, AD-72, AD-74
- SP-27, SP-29, SP-259, SP-262, AD-71, HP-703

### Real Wells (from Morning Report)
- QTIF: QTIF-598, QTIF-284, QTIF-545, QTIF-790, QTIF-520, QTIF-630
- BRRI: BRRI-350, BRRI-380, BRRI-335, BRRI-381
- HZEM, JNAB, HMYM, THRY fields

---

## 4. Drill Bit Lifecycle & Tracking

### Serial Number Format
- **Base SN:** 8 digits (e.g., 14141234)
- **Finance SN:** SN + R + (repair_count + rerun_count_factory)
- **Actual Repair SN:** SN + R + repair_count

### Counter Logic

| Counter | Description | Affects Finance SN |
|---------|-------------|-------------------|
| repair_count | Repairs completed at ARDT | ✅ Yes |
| repair_count_usa | Repairs completed in USA | ✅ Yes (via evaluation) |
| rerun_count_factory | Factory reruns (QC/Tech) | ✅ Yes |
| rerun_count_field | Field reruns (no charges) | ❌ No |
| backload_count | Times returned to factory | No |
| deployment_count | Times deployed to field | No |

### Example Lifecycle

```
Backload#  Repair  Rerun  Finance SN      Actual Repair
1          1       -      14141234R1      14141234R1
2          -       1      14141234R2      14141234R1
3          -       1      14141234R3      14141234R1
4          1       -      14141234R4      14141234R2
5          1       -      14141234R5      14141234R3
```

### Status Values

| Status | Description | Location |
|--------|-------------|----------|
| NEW | Just manufactured/received | Warehouse |
| DEPLOYED | At rig site | Rig |
| BACKLOADED | Returned to factory | Receiving |
| EVALUATION | Being assessed | Evaluation Area |
| HOLD | Waiting (parts, decision, investigation) | Factory |
| IN_REPAIR | Repair in progress | Repair Shop |
| REPAIRED | Repair complete, ready | Warehouse |
| USA_REPAIR | Sent to USA for repair | USA |
| RERUN | Ready to deploy (no repair needed) | Warehouse |
| SCRAP | End of life | Scrap Yard |
| SAVED_BODY | Scrapped but body saved | Scrap Yard |

### Lifecycle Flow Diagram

```
                         ┌─────────────────────────────┐
                         │      FIELD RERUN            │
                         │  (no factory, no charges)   │
                         └──────────┬──────────────────┘
                                    │
NEW ──► DEPLOYED ──► [Used] ──► Decision at Field
             ▲                      │
             │           ┌──────────┴──────────┐
             │           ▼                     ▼
             │      FIELD RERUN            BACKLOAD
             │      (deploy again)         (to factory)
             │           │                     │
             │           │                     ▼
             │           │                EVALUATION
             │           │                     │
             │    ┌──────┴────┬────────┬───────┴───────┬──────────┐
             │    ▼           ▼        ▼               ▼          ▼
             │  FACTORY    REPAIR    HOLD         USA_REPAIR    SCRAP
             │  RERUN        │        │               │           │
             │    │          ▼        │               ▼           ▼
             │    │      REPAIRED ◄───┴────── USA_REPAIRED     [END]
             │    │          │                                or SAVED_BODY
             └────┴──────────┘
```

---

## 5. Work Orders vs Job Cards

| Concept | Purpose | Contains |
|---------|---------|----------|
| **Work Order** | High-level authorization ("what to do") | Customer, bit info, deadline, type |
| **Job Card** | Detailed execution document | BOM, cutter map, QC checklist, process route |

### Job Card Processes (from template - corrected)
- Wash
- Evaluate
- LPT (Liquid Penetrant Test)
- De-Braze
- Braze
- Blasting (not "Matrix" - this is separate)
- Matrix Build-up
- Hardfacing
- TIG Welding
- Nozzles Remove
- Tip Grind
- Final Grind
- Pressure Test
- Thread Clean
- Body Clean
- Photo
- QC Inspect
- Final Inspect

**Note:** Process list needs verification against job card template (2025-ARDT-LV4-015-14204328.xlsx)

---

## 6. Bit Types & Sizes (Real Data)

### Sizes
- 3 3/4" (stored as 3.750)
- 3 7/8" (stored as 3.875)
- 6 1/8" (stored as 6.125)
- 8 1/2" (stored as 8.500)
- 12 1/4" (stored as 12.250)

### Types/Models (50+ models)
- **GT Series:** GT53, GT64DH, GT65DH, GT65RHS, GT76H, GTD54H, GTi54H, GTi64H
- **HD Series:** HD54, HD54-2, HD54F, HD54X, HD64, HD64KHF
- **MM Series:** MM64, MMD54H, MMD63, MMD64, MMD65H, MMD76H
- **FX/FM Series:** FX53, FXD63, FXD65, FM3651Z, FMD44
- **HXi Series:** HXi54s, HXi65Dks
- **CS Series:** CS54Os, CS55RKOs
- **SF Series:** SF53, SFD66CH

### BitType Complete Structure (Updated Dec 12)

| Field | Description | Example |
|-------|-------------|---------|
| **category** | Product category | FC, MT, TCI |
| **size** | Bit size (FK to BitSize) | 8.500 (8 1/2") |
| **smi_name** | Client-facing name | MMD53DH, GT65RHs-1 |
| **hdbs_name** | Internal HDBS name | MMD53DH, GT65DH |
| **series** | Product series | GT, HD, MM, EM |
| **hdbs_mn** | HDBS Material Number (SAP) | 2016920 |
| **ref_hdbs_mn** | Parent/Reference MAT | 2013733 |
| **ardt_item_number** | ARDT ERP number | (to be added) |
| **body_material** | M=Matrix, S=Steel | M, S |
| **no_of_blades** | Number of blades (FC only) | 5, 6, 7 |
| **cutter_size** | Cutter size (FC only) | 3, 4, 5, 6 |
| **gage_length** | Gage length | 1.5, 2, 3.5 |
| **order_level** | Production level | 3, 4, 5, 6 |

### Category Types
| Code | Name | Description |
|------|------|-------------|
| FC | Fixed Cutter | PDC bits with blades |
| MT | Mill Tooth | Roller cone - mill tooth |
| TCI | Tri Cone Inserts | Roller cone - tungsten carbide inserts |

### Order Levels (JV Classification)
| Level | Description |
|-------|-------------|
| 3 | Bit without cutters, upper section separate (not welded) |
| 4 | Bit without cutters, upper section welded and machined |
| 5 | Same as Level 4 + cutters brazed on |
| 6 | Same as Level 5 + painted and ready for use |

### Naming Pattern (General - not strict)
```
GT65RHs-1
││││
│││└── Variant
││└─── Cutter Size = 5
│└──── No. of Blades = 6
└───── Series = GT
```
*Note: Pattern is not always consistent, don't rely on it programmatically*

---

## 7. Key Design Decisions

| Topic | Decision |
|-------|----------|
| Serial Number | 8 digits, never changes |
| Size Storage | Decimal (8.500) displayed as fraction (8 1/2") |
| Finance SN | SN + R + (repair_count + rerun_count_factory) |
| Field Reruns | Don't affect Finance SN (no charges) |
| USA Repairs | Increment both usa_repair_count AND repair_count |
| HOLD Status | Can occur at multiple points in lifecycle |
| Scrap Accounting | ScrapRecord captures consumed materials for write-off |
| Work Order vs Job Card | WO = authorization, JC = execution details |

---

## 8. Documents Created

1. **MASTER_PLAN.md** - Complete Phase 1-5 roadmap
2. **MASTER_PLAN_CORRECTION.md** - Instructions to fix wrong seed data
3. **Phase2_Products_Design.md** - Drill bit lifecycle and tracking design

---

## 9. Git Workflow (Safe Development)

```bash
# Before each module:
git checkout -b enhancement/module-name

# After completing & testing:
git commit -m "✅ COMPLETE: Module name with real data"
git tag -a v0.X.0-module-name -m "Description"
git push --tags

# Create checkpoint branch:
git checkout -b checkpoint/module-complete
git push origin checkpoint/module-complete
```

---

## 10. Next Steps

### ✅ Completed (Phase 1)
1. ✅ Login Page - Professional with ARDT branding
2. ✅ Users - 27 real employees seeded
3. ✅ Departments - 10 departments from QAS-105
4. ✅ Positions - 54 positions from QAS-105
5. ✅ Companies - 8 companies (clients + competitors)
6. ✅ Rigs & Wells - Real data from morning report

### 🔄 In Progress
- Fix seed data with MASTER_PLAN_CORRECTION.md (delete wrong data, use correct employees)

### ⏳ Next: Phase 2 - Products & Bit Tracking
1. Implement DrillBit model with all counters
2. Implement BitEvent for lifecycle tracking
3. Implement BitSize and BitType reference data
4. Implement Location model
5. Seed real bit types and sizes from Excel files
6. Add MAT numbers to design (currently missing)

### ⏳ Future Phases
- Phase 3: Work Orders & Job Cards
- Phase 4: Quality/Inspections
- Phase 5: Logistics/Dispatch

---

## 11. Known Issues & Missing Items

| Item | Status | Notes |
|------|--------|-------|
| MAT Numbers | ❌ Missing | Need to add to design |
| Job Card Template | 📋 Needs Review | File: 2025-ARDT-LV4-015-14204328.xlsx |
| Process List | ⚠️ Needs Verification | Compare with actual job card template |

---

## 12. Key Files Shared

| File | Content |
|------|---------|
| Floor-Management-System-D.zip | Project code |
| QAS-105 Job Titles.pdf | 54 positions with responsibilities |
| BITS_TRACKING_10-30-2025.xlsx | 2,105 bits with real data |
| URDD-Fleet_9-12-2025.xlsx | Deployment/fleet data |
| 01-02-2025.pdf | Morning report with rigs/wells |
| 2025-ARDT-LV4-015-14204328.xlsx | Job card template |
| Copy_of_Cutter_Inventory_11-20-2025.xlsx | Cutter inventory |

---

## 13. Implementation Documents (For Claude Code)

| Document | Purpose | Status |
|----------|---------|--------|
| MASTER_PLAN.md | Phase 1 data (users, departments, positions) | ✅ Done |
| MASTER_PLAN_CORRECTION.md | Fix wrong seed data | ✅ Done |
| PHASE2_PRODUCTS_IMPLEMENTATION.md | Phase 2 original guide (models already created) | ✅ Models Done |
| **PHASE2_UPDATE.md** | **UPDATE BitType + Add Web UI** | ⏳ Use This Now |

### What's Already Done by Claude Code:
| Component | Status |
|-----------|--------|
| BitSize model | ✅ 18 sizes created |
| BitType model | ✅ Created BUT needs field updates |
| Location model | ✅ All types created |
| DrillBit model | ✅ With counters and lifecycle |
| BitEvent model | ✅ 20 event types |
| Web UI pages | ❌ Missing - only admin access |

### What Needs to be Done Now (PHASE2_UPDATE.md):
| Task | Description |
|------|-------------|
| Task 1 | UPDATE BitType model - add category, smi_name, hdbs_name, specs, order_level |
| Task 2 | UPDATE BitType admin with new fields |
| Task 3 | Seed real BitType data from ARDT spreadsheet |
| Task 4 | CREATE Web UI pages (list, create, edit, detail) + sidebar navigation |

### How to Use:
1. Upload `docs/PHASE2_UPDATE.md` to GitHub repo
2. Tell Claude Code: "Read docs/PHASE2_UPDATE.md and start with Task 1"

---

## 14. Claude.ai Tips & Troubleshooting

### "Compaction Failed Unexpectedly" Error

**What it is:** An automatic process that summarizes your conversation when the context window gets too full. The error occurs when this process fails.

**Causes:**
- Very long conversations with many tool calls and file operations
- Large project files consuming significant context space
- Extended thinking creating additional content
- Complex file operations (examining templates, cross-referencing documents)

**How to Avoid:**
1. **Start new chats more frequently** - Break complex tasks into smaller conversations
2. **Use fewer files at once** - Work with only essential files for each task
3. **Copy important context before starting fresh** - Paste summary in new chat
4. **Refresh the page** when you see the warning - Sometimes allows recovery
5. **Click ✕ on warning and continue** - Conversation may still proceed

### Project Knowledge (Share Files Across All Chats)

**Problem:** Files uploaded in a chat are only available in that specific conversation.

**Solution:** Use **Project Knowledge** to share files across ALL chats in a project.

**How to Add Files to Project Knowledge:**
1. Go to your project page (click "FMC D" in sidebar)
2. Find "Project Knowledge" section on the right side
3. Click the "+" button to upload files there

| Upload Location | Behavior |
|-----------------|----------|
| In a chat (+ button in chat) | Files only in that conversation |
| In Project Knowledge (project page) | Files available in ALL project chats |

**Benefits:**
- Files available across all chats in the project
- Start fresh chats without re-uploading files
- Helps avoid compaction issues (less context per chat)
- Core documents always accessible

**Recommendation for FMC D Project:**
Upload these to Project Knowledge:
- MASTER_PLAN.md
- Job card templates
- QAS-105 Job Titles.pdf
- Key reference documents

Then start smaller, focused chats for specific tasks.

---

*Summary created: December 12, 2025*  
*Updated: December 13, 2025 - Added BitType complete structure with category, specs, order levels*
