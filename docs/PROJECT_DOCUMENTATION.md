# ARDT Floor Management System — Master Project Documentation

> **Version:** Draft 1.0
> **Generated:** April 4, 2026
> **Status:** Active Development (v5.4)
> **Confidential — Internal Use Only**

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Application Map](#3-application-map)
4. [Full Data Model Reference](#4-full-data-model-reference)
5. [URL & Navigation Map](#5-url--navigation-map)
6. [User Roles & Permission Architecture](#6-user-roles--permission-architecture)
7. [Business Workflow Coverage](#7-business-workflow-coverage)
8. [Notification & Approval System](#8-notification--approval-system)
9. [Dashboard & Workbench Status](#9-dashboard--workbench-status)
10. [Reporting Module Status](#10-reporting-module-status)
11. [Security Audit](#11-security-audit)
12. [UI/UX & Frontend Consistency Audit](#12-uiux--frontend-consistency-audit)
13. [Code Quality & Technical Debt](#13-code-quality--technical-debt)
14. [Dependencies & Third-Party Libraries](#14-dependencies--third-party-libraries)
15. [Prioritized Recommendations](#15-prioritized-recommendations)
16. [Summary Statistics](#16-summary-statistics)

---

## 1. Executive Summary

The ARDT Floor Management System (FMS) is a comprehensive digital operations platform purpose-built for Arabian Rockbits & Drilling Tools Co. Ltd. (ARDTCO), a drill bit manufacturing and repair company based in the Eastern Province of Saudi Arabia. The system manages the complete lifecycle of PDC (Polycrystalline Diamond Compact) and RC (Roller Cone) drill bits — from the moment a bit arrives at the facility through inspection, evaluation, repair or manufacture, quality control, and final dispatch to clients such as Saudi Aramco and Halliburton.

Before FMS, ARDTCO relied on paper-based inspection records, manual work order tracking, and spreadsheet-driven inventory management. Critical information about bit history, cutter specifications, and production status was fragmented across files, memory, and physical job cards. This created traceability gaps, delayed reporting, and made it difficult for management to get real-time visibility into floor operations. The system directly addresses these challenges by providing a single, centralized digital record for every drill bit, every work order, and every quality inspection.

The system serves multiple user roles: floor operators who scan QR codes to start and complete production steps, supervisors who manage work order routing and approvals, quality inspectors who complete structured evaluation forms (including die checks, pressure tests, and thread inspections), receiving clerks who process incoming batches, and senior management who need production dashboards and KPI reports. Each role has access to only the screens and actions relevant to their position, following a role-based access model built on Django's authentication framework.

As of April 2026, FMS is in active development running on a local development server (`localhost:8001`) using SQLite as its database. The system is not yet deployed to a production server. Key modules — work orders, drill bit lifecycle, receiving dock, cutter inventory, BOM management, production planning, and ERP automation — are substantially complete and in daily use for testing and validation. Supporting modules — HR, maintenance, safety, compliance, and full reporting — are scaffolded with models and basic CRUD views but require additional workflow implementation.

The strategic value of FMS lies in its potential to transform ARDTCO from a paper-driven operation into a digitally traceable, auditable facility. Every bit repair becomes a documented record with full chain-of-custody. Every quality decision is timestamped and attributed to a specific inspector. Every work order follows a structured route with defined steps, checklists, and sign-off requirements. This level of traceability is not merely operational convenience — it is increasingly a requirement from major clients like Saudi Aramco who demand ISO-compliant quality management systems.

---

## 2. System Architecture

### Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend Framework** | Django | 5.1.15 |
| **Programming Language** | Python | 3.10.11 |
| **Database** | SQLite (dev) / PostgreSQL (prod-ready) | SQLite 3.x |
| **Frontend Reactivity** | Alpine.js | 3.14.0 |
| **Dynamic Updates** | HTMX | 2.0.0 |
| **CSS Framework** | Tailwind CSS | CDN (JIT) |
| **Icons** | Lucide Icons | Latest (CDN) |
| **Data Tables** | Simple DataTables | 9.0.0 |
| **Form Rendering** | Django Crispy Forms + Tailwind | 2.1+ |
| **Static Files** | WhiteNoise | 6.6+ |
| **PDF Processing** | PyMuPDF (fitz), ReportLab, xhtml2pdf | Various |
| **Excel Processing** | openpyxl, pandas | Various |
| **Browser Automation** | Playwright (sync API, Chromium) | 1.40+ |
| **Photo Editing** | Fabric.js | 5.3.1 (CDN) |
| **QR/Barcode** | python-barcode, qrcode | Various |

### Authentication

- **Custom User Model:** `accounts.User` (extends Django AbstractUser)
- **Method:** Session-based authentication (Django default)
- **Session Timeout:** 24 hours (`SESSION_COOKIE_AGE = 86400`)
- **Login URL:** `/accounts/login/`
- **Login Redirect:** `/` (dashboard home)
- **Password Validation:** 4 validators (similarity, min length, common, numeric)

### File Storage

- **Static Files:** Local `static/` directory, served via WhiteNoise (`CompressedManifestStaticFilesStorage`)
- **Media Files:** Local `media/` directory (configurable to `/var/www/ardt-fms/media` in production)
- **Upload Limit:** 10 MB (configurable via `ARDT_MAX_UPLOAD_SIZE_MB`)
- **Allowed Image Types:** JPEG, PNG, GIF
- **Allowed Document Types:** PDF, DOC, DOCX

### Deployment Environment

- **Current:** Development server (`python manage.py runserver 0.0.0.0:8001`)
- **DEBUG:** `True` (via `.env` file)
- **ALLOWED_HOSTS:** `localhost, 127.0.0.1, .github.dev, .app.github.dev`
- **Production Server:** Gunicorn (configured in requirements.txt, not yet deployed)
- **Timezone:** `Asia/Riyadh` (UTC+3)

### External Integrations

| Integration | Status | Technology |
|-------------|--------|------------|
| **D365 ERP Automation** | Active | Playwright browser automation (26 workflows, 13 chains) |
| **Email** | Console backend (dev) | Configurable SMTP for production |
| **Halliburton PDF Extraction** | Active | PyMuPDF cutter map parser |
| **GitHub Codespaces** | Supported | Auto-detected via `CODESPACE_NAME` env var |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        WEB BROWSER                              │
│  (Alpine.js + HTMX + Tailwind CSS + Lucide Icons + Fabric.js)  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP / HTMX
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DJANGO APP SERVER (v5.1)                     │
│  Middleware: Security → WhiteNoise → Session → CSRF → Auth →   │
│             Messages → Clickjacking → HTMX                     │
├─────────────┬──────────────┬──────────────┬────────────────────┤
│  CORE OPS   │  QUALITY     │  SUPPORT     │  AUTOMATION        │
│  ─────────  │  ─────────   │  ─────────   │  ─────────         │
│  workorders │  quality     │  hr          │  erp_automation    │
│  technology │  compliance  │  accounts    │  erp_integration   │
│  inventory  │  procedures  │  organization│  cutter_map        │
│  sales      │  forms_engine│  notifications│ scancodes         │
│  planning   │  execution   │  maintenance │  documents         │
│  supplychain│              │  hsse        │  reports           │
│  dispatch   │              │  dashboard   │                    │
│  drss       │              │  common      │                    │
└──────┬──────┴──────┬───────┴──────┬───────┴────────────────────┘
       │             │              │
       ▼             ▼              ▼
  ┌─────────┐  ┌──────────┐  ┌──────────────┐
  │ SQLite  │  │  Media/   │  │  Static/     │
  │ db.sqlite3│ │  Uploads │  │  WhiteNoise  │
  └─────────┘  └──────────┘  └──────────────┘
                                    │
                               ┌────┴─────┐
                               │ Playwright│──► D365 ERP
                               │ (Chromium)│    (ADFS Auth)
                               └──────────┘
```

---

## 3. Application Map

### App: accounts
- **Purpose:** Custom user authentication, user management, roles, and permissions.
- **Models:** User, Role, UserRole, Permission, RolePermission, LoginAudit
- **Key Views:** UserListView, UserCreateView, UserDetailView, RoleListView, RoleDetailView, PermissionListView, login/logout
- **Templates:** 13 templates (user CRUD, role CRUD, permission CRUD, auth pages)
- **Completion Status:** ✅ Complete — Full CRUD for users, roles, permissions. Custom context processors for permissions and dashboards.

### App: workorders
- **Purpose:** Core production module — drill bits, work orders, evaluations, router sheets, receiving dock, operator portal, production planning integration.
- **Models:** DrillBit, BitEvent, WorkOrder, CutterEvaluationMatrix, CutterEvaluationEntry, RouterSheetEntry, MasterProcess, ProcessRoute, DieCheckReport, ReceivingInspection, ReceivingInspectionAttachment, BackloadBatch, BackloadItem, BOMPendingRequest, DrillBitPhoto, Location, StepDurationRecord, NumberSequence, WorkOrderTimeLog, WorkOrderCost (46 models total)
- **Key Views:** 214 views/functions covering drill bit CRUD, work order lifecycle, evaluations (9 types), router sheet with QR scanning, receiving dock (backload batches, inspections), operator portal, production floor board, KPI API, photo management
- **Templates:** 91 templates
- **Completion Status:** ✅ Complete — Most mature module. Full drill bit lifecycle, 9 evaluation types, structured router with 43+ master processes, QR scan support, receiving dock with batch processing, photo module with Fabric.js editor.

### App: technology
- **Purpose:** Drill bit designs (L3/L4/L5/L5.5), Bills of Materials, HDBS/SMI classification types, pocket configurations, bit sizes, connections.
- **Models:** Design, BOM, BOMLine, DesignPocket, HDBSType, SMIType, BitSize, IADCCode, ConnectionType, ConnectionSize, FormationType, BodyMaterial, PocketShape, DesignHDBS (25 models)
- **Key Views:** 69 views — Design CRUD, BOM CRUD with builder wizard, HDBS/SMI type management, API endpoints for BOM listing and type filtering
- **Templates:** 32 templates
- **Completion Status:** ✅ Complete — Design hierarchy, BOM creation from PDF extraction, HDBS/SMI type management, comprehensive seeding commands (28 management commands).

### App: inventory
- **Purpose:** Item master data, cutter variants, stock management (ledger-based), GRN processing, purchase order receiving.
- **Models:** InventoryCategory, InventoryItem, ItemVariant, VariantCase, VariantStock, StockBalance, StockLedger, GoodsReceiptNote, GRNLine, MaterialLot, StockIssue, StockTransfer, StockAdjustment, and related models (50 models total)
- **Key Views:** 162 views — Cutter inventory dashboard with Excel-style filters, item CRUD, GRN processing with QC and 3-way matching, stock issue/transfer/adjustment posting, Excel export with column filtering
- **Templates:** 112 templates
- **Completion Status:** ✅ Complete — Immutable stock ledger, variant-based inventory, GRN with multi-line posting, Excel export. N+1 query optimization done.

### App: cutter_map
- **Purpose:** Extract cutter data from Halliburton PDFs, create BOMs visually, manage cutter shapes.
- **Models:** CutterMapDocument, BOMDocument
- **Key Views:** 29 views — PDF upload and extraction, interactive BOM editor, cutter inventory API, shape management, SMI Type quick-create
- **Templates:** 6 templates (main index, BOM view, BOM readonly, add cutter wizard)
- **Completion Status:** ✅ Complete — PDF extraction pipeline, interactive cutter layout editor, CL-Driven mode, shape persistence, live inventory integration in selection dialog.

### App: sales
- **Purpose:** Customer management, sales orders, and critically — the Account (Business Unit) model that drives work order numbering, pricing, and workflow routing.
- **Models:** Account, Customer, SalesOrder, SalesOrderLine, Quote, QuoteItem, Pricing, Contract, Warranty, and related models (27 models)
- **Key Views:** 122 views — Account/customer/order CRUD, account seeding
- **Templates:** 94 templates
- **Completion Status:** 🔶 Partial — Account model is fully implemented and critical to operations (12 business units seeded). Customer and SalesOrder CRUD exists but SalesOrder workflow (quote → order → invoice) is basic. Pricing engine scaffolded but not fully wired.

### App: erp_automation
- **Purpose:** Record browser actions on D365 ERP, convert recordings to executable workflows, execute workflows against parsed job card data. Full Record → Convert → Execute pipeline.
- **Models:** Locator, LocatorStrategy, Workflow, WorkflowStep, RecordingSession, RecordedAction, WorkflowExecution, StepExecution, ERPJobData, ERPRoute, FieldMapping, ItemCounter, WorkflowChain, WorkflowChainLink, ChainExecution, ERPEnvironment (16 models)
- **Key Views:** 115 views — Recording lifecycle, workflow editor (inline CRUD), chain editor with debug execution, job data management, batch chain execution
- **Templates:** 27 templates
- **Completion Status:** ✅ Complete — Full automation pipeline with 26 workflows, 13 chains, 342 locators, smart D365 interaction engine (10 modes), repeat group expansion, batch execution with shared browser session. Production-grade debug execution with pause/resume/step-by-step modes.

### App: planning
- **Purpose:** Production planning — queue drill bits for work, manage priorities, track planner-to-WO lifecycle.
- **Models:** ProductionPlanEntry, PlannerSchedule, and related models (10 models)
- **Key Views:** 31 views — Planner list (Ready/Planned/WIP tabs), add-to-plan API, release-to-production API, location transfer integration
- **Templates:** 18 templates
- **Completion Status:** ✅ Complete — Full planner workflow: assign BU → add to plan → release → create WO. Status tracking, location-aware transfers, FC BOM requirement enforcement.

### App: notifications
- **Purpose:** Real-time notification bell, workflow engine, action center, form revision tracking.
- **Models:** Notification, WorkflowRule, WorkflowAction, WorkflowCapability (removed), FormRevision, and related models (10 models)
- **Key Views:** 30 views — Bell API (HTMX polling), mark read, action center (My/Team/History tabs), workflow settings
- **Templates:** 17 templates
- **Completion Status:** 🔶 Partial — Bell notification with 10s HTMX polling is fully working. 24 workflow rules seeded. `notify()` service wired to 7+ integration points. Workflow engine (`dispatch_event`) is active (`WORKFLOW_ENGINE_ACTIVE=True`). Action center exists but workflow action completion UI needs refinement.

### App: hr
- **Purpose:** Employee records, position tracking, competency matrix, training management.
- **Models:** Employee, ProcessCompetencyMatrix, TrainingRecord, and related models (17 models)
- **Key Views:** 68 views — Employee CRUD, competency matrix (employee × process grid), gap report, Excel export
- **Templates:** 48 templates
- **Completion Status:** 🔶 Partial — Employee model with Position FK, competency matrix with 4 certification levels (NOT_AUTHORIZED/TRAINEE/CERTIFIED/TRAINER), gap reporting. Payroll, leave management, and performance reviews are scaffolded but not yet functional.

### App: supplychain
- **Purpose:** Purchase order management, vendor records, receiving.
- **Models:** Vendor, PurchaseOrder, PurchaseOrderLine, Receipt, ReceiptLine, and related models (18 models)
- **Key Views:** 36 views — Vendor CRUD, PO CRUD, receiving
- **Templates:** 23 templates
- **Completion Status:** 🔶 Partial — Vendor and PO CRUD functional. Receipt model exists parallel to inventory's GoodsReceiptNote (documented overlap — consolidation deferred).

### App: dispatch
- **Purpose:** Shipment tracking, delivery management.
- **Models:** Dispatch, DispatchItem, Fleet, DriverRecord (4 models)
- **Key Views:** 15 views — Dispatch CRUD, status tracking
- **Templates:** 11 templates
- **Completion Status:** 🔶 Partial — Basic dispatch CRUD. Status update creates BitEvent (DEPLOYED) and updates drill bit status. Fleet and driver management scaffolded.

### App: quality
- **Purpose:** Quality management system records.
- **Models:** QualityRecord, InspectionReport, TestResult, and related (5 models)
- **Key Views:** 14 views — Basic CRUD
- **Templates:** 10 templates
- **Completion Status:** 🔶 Partial — Basic CRUD exists. Core quality workflows (die checks, evaluations, LPT, thread inspections) are implemented in the workorders app rather than here.

### App: compliance
- **Purpose:** Audit management, certifications, nonconformance tracking.
- **Models:** ComplianceRecord, AuditChecklist, NonConformance, and related (10 models)
- **Key Views:** 50 views — CRUD for all compliance entities
- **Templates:** 40 templates
- **Completion Status:** 🔶 Partial — Models and CRUD views exist. Workflow integration (auto-create NCR from failed inspections) not yet implemented.

### App: maintenance
- **Purpose:** Equipment maintenance tracking, preventive maintenance schedules.
- **Models:** Equipment, MaintenancePlan, MaintenanceRecord, and related (6 models)
- **Key Views:** 20 views — CRUD
- **Templates:** 16 templates
- **Completion Status:** 🔶 Partial — Basic CRUD. No integration with production scheduling or equipment downtime tracking.

### App: hsse
- **Purpose:** Health, Safety, Security, and Environment management.
- **Models:** Incident, HazardRegister, SafetyObservation (3 models)
- **Key Views:** 19 views — Incident reporting, hazard register
- **Templates:** 13 templates
- **Completion Status:** 🔶 Partial — Basic incident and hazard CRUD. No integration with work permits, JSA, or toolbox talk tracking.

### App: organization
- **Purpose:** Organizational hierarchy — departments, positions.
- **Models:** Department, Position, PositionRole, DepartmentHead, OrgChart (5 models)
- **Key Views:** 23 views — Department and position CRUD
- **Templates:** 17 templates (redesigned with modern Tailwind UI)
- **Completion Status:** ✅ Complete — Department/position CRUD with 1:1 position-role mapping, position sync signal.

### App: dashboard
- **Purpose:** Home screen, production floor board, KPI dashboards.
- **Models:** DashboardWidget, SavedDashboard (2 models)
- **Key Views:** 24 views — Home dashboard, floor board, KPI views
- **Templates:** 13 templates (with partials)
- **Completion Status:** 🔶 Partial — Floor board with HTMX auto-refresh works. KPI API endpoint exists. Role-specific dashboards not yet fully differentiated.

### App: reports
- **Purpose:** Reporting and analytics framework.
- **Models:** ReportDefinition, ReportSchedule (2 models)
- **Key Views:** 8 views — Report list, detail
- **Templates:** 9 templates
- **Completion Status:** ❌ Minimal — Framework scaffolded but no production reports built yet. Step duration data is being collected via `StepDurationRecord` for future analytics.

### App: documents
- **Purpose:** Document library and versioning.
- **Models:** Document, DocumentVersion (2 models)
- **Key Views:** 12 views — Upload, list, version management
- **Templates:** 6 templates
- **Completion Status:** 🔶 Partial — Basic upload and listing. No integration with work orders or quality records for auto-attachment.

### App: procedures
- **Purpose:** Work procedure templates and checklists.
- **Models:** Procedure, ProcedureStep, ChecklistTemplate, and related (9 models)
- **Key Views:** 8 views — CRUD
- **Templates:** 4 templates
- **Completion Status:** 🔶 Partial — Model structure exists. Procedure content now seeded via MasterProcess in workorders app (17 processes with procedure refs, 46 checklists).

### App: forms_engine
- **Purpose:** Dynamic form builder for custom inspection forms.
- **Models:** FormDefinition, FormField, FormResponse, FormSection, FormVersion (5 models)
- **Key Views:** 22 views — Form builder, form response collection
- **Templates:** 13 templates
- **Completion Status:** 🔶 Partial — Form builder UI exists. Not yet integrated with router step data collection (router steps use JSONField parameters_template instead).

### App: execution
- **Purpose:** Process execution tracking.
- **Models:** ExecutionRecord, ExecutionStep, and related (6 models)
- **Key Views:** 7 views — CRUD
- **Templates:** 2 templates
- **Completion Status:** ❌ Minimal — Scaffolded. Router sheet in workorders app handles execution tracking directly.

### App: drss
- **Purpose:** Demand Request and Supply Sourcing.
- **Models:** DRSSRequest, DRSSItem (2 models)
- **Key Views:** 9 views — CRUD
- **Templates:** 6 templates
- **Completion Status:** 🔶 Partial — Basic CRUD exists.

### App: scancodes
- **Purpose:** QR code and barcode generation and scanning.
- **Models:** ScanCode, ScanCodeType (2 models)
- **Key Views:** 11 views — Code generation, scan handling
- **Templates:** 8 templates
- **Completion Status:** 🔶 Partial — QR generation works. Scanning integrated into operator portal and router sheet via `api_operator_qr_scan`.

### App: common
- **Purpose:** Shared utilities, base models, management commands.
- **Models:** None (utility only)
- **Key Views:** None
- **Templates:** None
- **Completion Status:** ✅ Complete — Provides `seed_all` orchestration command and shared utilities.

### App: erp_integration
- **Purpose:** Future ERP integration models.
- **Models:** ERPSyncRecord, ERPMapping (2 models)
- **Key Views:** None
- **Templates:** None
- **Completion Status:** ❌ Not Started — Placeholder for future direct API integration with D365 (currently using browser automation via erp_automation app).

---

## 4. Full Data Model Reference

### Model Count by App

| App | Models | Key Relationships |
|-----|--------|-------------------|
| inventory | 50 | InventoryItem → ItemVariant → VariantStock → StockLedger chain |
| workorders | 46 | DrillBit → WorkOrder → RouterSheetEntry → MasterProcess |
| sales | 27 | Account → Customer → SalesOrder chain |
| technology | 25 | Design → BOM → BOMLine → InventoryItem |
| supplychain | 18 | Vendor → PurchaseOrder → PurchaseOrderLine |
| hr | 17 | Employee → Position → ProcessCompetencyMatrix |
| erp_automation | 16 | Workflow → WorkflowStep → Locator → LocatorStrategy |
| compliance | 10 | ComplianceRecord → AuditChecklist |
| notifications | 10 | WorkflowRule → WorkflowAction; Notification → User |
| planning | 10 | ProductionPlanEntry → DrillBit, WorkOrder |
| procedures | 9 | Procedure → ProcedureStep |
| maintenance | 6 | Equipment → MaintenancePlan → MaintenanceRecord |
| accounts | 6 | User → Role → Permission via UserRole, RolePermission |
| execution | 6 | ExecutionRecord → ExecutionStep |
| forms_engine | 5 | FormDefinition → FormField → FormResponse |
| quality | 5 | QualityRecord → InspectionReport |
| organization | 5 | Department → Position → PositionRole |
| dispatch | 4 | Dispatch → DispatchItem |
| hsse | 3 | Incident, HazardRegister, SafetyObservation |
| cutter_map | 2 | CutterMapDocument, BOMDocument |
| dashboard | 2 | DashboardWidget, SavedDashboard |
| documents | 2 | Document → DocumentVersion |
| drss | 2 | DRSSRequest → DRSSItem |
| erp_integration | 2 | ERPSyncRecord, ERPMapping |
| reports | 2 | ReportDefinition, ReportSchedule |
| scancodes | 2 | ScanCode, ScanCodeType |
| **TOTAL** | **330+** | |

### Critical Model Relationships

```
Account (Business Unit)
  ├── DrillBit.account (FK) — determines WO numbering
  ├── WorkOrder.account (FK) — determines pricing/workflow
  └── ProductionPlanEntry.account (FK)

DrillBit
  ├── Design (FK) — blueprint
  ├── system_bom / brazing_bom (FK to BOM) — material specs
  ├── bit_location (FK to Location) — current physical location
  ├── BitEvent[] — full audit trail
  └── WorkOrder[] — production history

WorkOrder
  ├── DrillBit (FK)
  ├── RouterSheetEntry[] — process steps
  ├── CutterEvaluationMatrix[] — evaluation records
  └── DieCheckReport[] — die check records

StockLedger (immutable)
  ├── InventoryItem (FK)
  ├── ItemVariant (FK)
  └── qty_delta (signed — positive=receipt, negative=issue)
```

---

## 5. URL & Navigation Map

### URL Pattern Summary

| App | URL Prefix | Pattern Count | Auth Required |
|-----|-----------|---------------|---------------|
| dashboard | `/` | 21 | Yes (all) |
| accounts | `/accounts/` | 26 | Mixed (login/logout public) |
| organization | `/organization/` | 23 | Yes |
| workorders | `/work-orders/` | 211 | Yes |
| technology | `/technology/` | 69 | Yes |
| inventory | `/inventory/` | 163 | Yes |
| sales | `/sales/` | 122 | Yes |
| cutter_map | `/cutter-map/` | 32 | Yes |
| erp_automation | `/erp-automation/` | 100 | Yes (except `stop_recording`) |
| planning | `/planning/` | 31 | Yes |
| notifications | `/notifications/` | 30 | Yes |
| supplychain | `/supply-chain/` | 32 | Yes |
| hr | `/hr/` | 68 | Yes |
| dispatch | `/dispatch/` | 15 | Yes |
| quality | `/quality/` | 14 | Yes |
| compliance | `/compliance/` | 50 | Yes |
| maintenance | `/maintenance/` | 21 | Yes |
| hsse | `/hsse/` | 19 | Yes |
| documents | `/documents/` | 12 | Yes |
| forms_engine | `/forms/` | 22 | Yes |
| execution | `/execution/` | 7 | Yes |
| procedures | `/procedures/` | 8 | Yes |
| reports | `/reports/` | 8 | Yes |
| scancodes | `/scan/` | 11 | Yes |
| drss | `/drss/` | 9 | Yes |
| admin | `/admin/` | N/A | Superuser |
| **TOTAL** | | **1,124** | |

### Unauthenticated Endpoints (Legitimate)

| URL | Purpose | Risk |
|-----|---------|------|
| `/accounts/login/` | Login page | None — expected |
| `/accounts/logout/` | Logout action | None — expected |
| `/erp-automation/record/stop/` | Stop browser recording | **MEDIUM** — missing `@login_required` |

---

## 6. User Roles & Permission Architecture

### Role System

The system uses a custom role model (`accounts.Role`) with the following architecture:

- **Roles** are defined in `accounts.Role` (not Django Groups)
- **Permissions** assigned via `RolePermission` M2M
- **Users** linked via `UserRole` with additional fields: `is_position_derived`, `is_available`, `account_scope` (M2M to Account)
- **Position → Role mapping:** `Position.role` FK enables auto-assignment when employee gets a position

### Seeded Roles (52 total from `seed_roles_permissions` command)

| Role Category | Roles | Dashboard |
|---------------|-------|-----------|
| **Operations** | OPERATOR, PDC_SUPERVISOR, MFG_SUPERVISOR, OPS_MANAGER | 🔶 Operator Portal exists; supervisor dashboards planned |
| **Quality** | QC_INSPECTOR, QC_SUPERVISOR, QUALITY_MANAGER | 🔶 Evaluation forms exist; QC dashboard planned |
| **Technical** | DESIGN_ENGINEER, TECH_REP, PROCESS_ENGINEER | ❌ No dedicated workbench |
| **Management** | GENERAL_MANAGER, DIRECTOR, PLANT_MANAGER | 🔶 Floor board exists; executive dashboard planned |
| **Receiving** | RECEIVING_CLERK, RECEIVING_SUPERVISOR | ✅ Receiving dock dashboard exists |
| **Dispatch** | DISPATCH_CLERK, DISPATCH_SUPERVISOR | 🔶 Basic dispatch views |
| **HR** | HR_ADMIN, HR_MANAGER | 🔶 Employee CRUD, competency matrix |
| **Admin** | SYSTEM_ADMIN | ✅ Full access + Django admin |
| **Planning** | PLANNER, PRODUCTION_PLANNER | ✅ Production planner exists |

### Role × Feature Access Matrix

| Feature | Operator | Supervisor | QC Inspector | Manager | Admin |
|---------|----------|------------|--------------|---------|-------|
| Start/Complete Router Steps | ✅ | ✅ | ❌ | ❌ | ✅ |
| Create Work Orders | ❌ | ✅ | ❌ | ✅ | ✅ |
| Approve Work Orders | ❌ | ❌ | ❌ | ✅ | ✅ |
| Complete Evaluations | ❌ | ✅ | ✅ | ❌ | ✅ |
| Manage Drill Bits | ❌ | ✅ | ❌ | ✅ | ✅ |
| View Production Board | ✅ | ✅ | ✅ | ✅ | ✅ |
| Run ERP Automation | ❌ | ❌ | ❌ | ✅ | ✅ |
| Manage Users | ❌ | ❌ | ❌ | ❌ | ✅ |

**Note:** Permission enforcement is currently primarily at the view level via `@login_required`. Granular role-based permission checks (e.g., "only QC_INSPECTOR can mark evaluations complete") are partially implemented through the workflow engine rules but not yet enforced as hard guards on all views.

---

## 7. Business Workflow Coverage

| Workflow Stage | Status | Model/View | Template | Gap Description |
|----------------|--------|------------|----------|-----------------|
| Bit Received (Backload) | ✅ | BackloadBatch, BackloadItem / views_receiving.py | backload_batch_*.html | Full batch processing with serial matching |
| Bit Received (New/Manufacture) | ✅ | DrillBit / views_drillbit.py | drillbit_form.html | First event wizard, BOM pending auto-request |
| Visual/Receiving Inspection | ✅ | ReceivingInspection / views_jobcard.py | receiving_inspection_form.html | QAS/005-1 compliant form with pocket/cutter grids |
| Die Check (LPT) | ✅ | DieCheckReport / views_jobcard.py | die_check_report.html | Materials tracking, cutter decisions, QAS/1004-1 print |
| LPT Pressure Test | ✅ | CutterEvaluationMatrix.pressure_test_data | cutter_evaluation_matrix.html | 2-round LPT with materials table |
| API Thread Inspection | ✅ | CutterEvaluationMatrix.thread_inspection_data | cutter_evaluation_matrix.html | 2-round thread inspection with 5 checkpoints |
| Evaluation & Route Decision | ✅ | CutterEvaluationMatrix (9 types) / views_jobcard.py | cutter_evaluation_form.html, cutter_evaluation_matrix.html | Full 9-type evaluation, 7 decision choices, section toggle |
| Production Planning | ✅ | ProductionPlanEntry / planning views | planner_list.html | BU assignment, planner queue, release-to-production |
| Work Order Creation | ✅ | WorkOrder / views.py | workorder_create.html | Serial-driven, account-based numbering, auto-populate |
| Router Sheet / Process Steps | ✅ | RouterSheetEntry, MasterProcess / views_jobcard.py | router_sheet.html | 43+ master processes, QR scan, step-by-step tracking |
| Full Repair (Brazing, etc.) | ✅ | RouterSheetEntry steps | router_sheet step detail | Steps seeded from QAS procedures |
| Light Dress | 🔶 | RouterSheetEntry | router_sheet.html | Supported via conditional steps, but no dedicated "light dress" route template |
| Return As-Is | 🔶 | DrillBit status change | — | Status can be set but no formal workflow or form |
| Scrap Decision | 🔶 | CutterEvaluationMatrix.decision = SCRAP | cutter_evaluation_matrix.html | Decision exists but no downstream scrap processing workflow |
| Post-Repair QC | ✅ | FINAL_QC, FINAL_INSPECTION eval types | cutter_evaluation_matrix.html | Full evaluation with section toggles |
| Final Inspection | ✅ | FINAL_INSPECTION eval type | cutter_evaluation_matrix.html | Complete with thread inspection and LPT sections |
| Dispatch | 🔶 | Dispatch model / dispatch views | dispatch templates | Basic CRUD, BitEvent(DEPLOYED) on status change. No packing list or shipment documents |
| ERP Item Creation | ✅ | ERPJobData, WorkflowChain / executor.py | chain_detail.html | Full D365 automation: create item → BOM → route → journal |

### Workflow Gaps

1. **Light Dress route:** No pre-defined light dress process route (only FC Repair and L3/L4 Manufacture seeded)
2. **Scrap processing:** Decision recorded but no downstream flow (scrap location, cutter recovery, financial write-off)
3. **Return As-Is:** No formal process — just a status change with no required documentation
4. **Dispatch documents:** No packing list, delivery note, or certificate of conformity generation
5. **Rework loop:** Rework evaluation type exists but no automatic route modification after rework decision

---

## 8. Notification & Approval System

### Current Notification Triggers (Active)

| Trigger | Priority | Recipients | Location |
|---------|----------|------------|----------|
| Work started on WO | NORMAL | All users | `start_work_view()` |
| WO sent to QC | HIGH | All users | `complete_work_view()` |
| WO status change | Variable | All users | `update_status_htmx()` |
| Evaluation completed | HIGH | All users | `api_evaluation_mark_complete()` |
| All router steps complete | HIGH | All users | `api_router_step_scan()` |
| Receiving inspection complete | HIGH | All users | `ReceivingInspectionEditView` |
| GRN posted | URGENT | All users | `GRNPostView.post()` |
| WO released (needs approval) | HIGH | All users | `api_mark_wo_released()` |
| Die check waiting QD | HIGH | All users | Die check save |
| Hold/Wait notifications | HIGH | All users | Router step hold actions |

### Approval Flows

| Approval | Status | Implementation |
|----------|--------|----------------|
| WO Approval (RELEASED → ACTIVE) | ✅ Implemented | `api_approve_work_order()` — records `approved_by`, `approved_at` |
| Skip to Active (PENDING → ACTIVE) | ✅ Implemented | Same view, skips RELEASED step |
| Evaluation sign-off | 🔶 Partial | `is_complete` flag exists; no formal sign-off with signature capture |
| Quality decision approval | ❌ Missing | No manager approval required for SCRAP/REJECT decisions |
| Dispatch authorization | ❌ Missing | No approval gate before bit leaves facility |

### Workflow Engine Status

- **Status:** Active (`WORKFLOW_ENGINE_ACTIVE = True`)
- **Rules:** 24 seeded workflow rules mapping events → actions/notifications
- **Action Center:** `/notifications/actions/` — My Actions, Team Actions, History tabs
- **Escalation:** `check_and_escalate_overdue_actions()` runs during bell poll
- **Gap:** Rule-based action assignment works but completion UX needs refinement

### Missing Notifications (Critical Gaps)

| Missing Notification | Priority | Impact |
|---------------------|----------|--------|
| Bit overdue at a stage (no SLA alerts) | Critical | Bits can sit at a stage indefinitely without alerting anyone |
| Inventory below reorder point | High | No automatic stock alert |
| PO delivery date approaching | Medium | No reminder for expected deliveries |
| Evaluation expiry/recheck needed | Medium | No time-based evaluation reminders |
| Competency certification expiring | Low | No alert for expiring certifications |

---

## 9. Dashboard & Workbench Status

| Role | Dedicated Dashboard | Widgets/KPIs | Priority |
|------|-------------------|--------------|----------|
| System Administrator | ✅ Django Admin + User Management | Full admin access | — |
| General Manager | 🔶 Floor Board | Active WOs, progress bars | High |
| Operations Manager | 🔶 Floor Board + Planner | WO status, step progress | High |
| PDC Repair Supervisor | 🔶 Floor Board | Active WOs by account | High |
| Manufacturing Supervisor | 🔶 Floor Board | Same as repair supervisor | Medium |
| Machine Operator | ✅ Operator Portal | Active steps, QR scan, assigned WOs | — |
| QC Inspector | ❌ None | — | High |
| Receiving Clerk | ✅ Receiving Dashboard | 6 panels: incoming, received, pending inspection, BOM pending, recently inspected, stats | — |
| Maintenance Technician | ❌ None | — | Medium |
| HR Admin | 🔶 Employee List | Employee count, competency matrix | Low |
| Sales Representative | ❌ None | — | Medium |
| Finance Staff | ❌ None | — | Low |
| Planner | ✅ Production Planner | Ready/Planned/WIP tabs with filters | — |

---

## 10. Reporting Module Status

| Report Category | Report Name | Exists | Filterable | Exportable | Priority |
|-----------------|-------------|--------|------------|------------|----------|
| **Production** | Work Order Status Summary | ❌ | — | — | High |
| **Production** | Step Duration KPI | 🔶 API only | Yes | No | High |
| **Production** | Floor Board (real-time) | ✅ | By account | No | — |
| **Production** | WO Throughput by Account | ❌ | — | — | High |
| **Quality** | Evaluation Summary by Type | ❌ | — | — | High |
| **Quality** | Die Check Results Report | ❌ | — | — | Medium |
| **Quality** | Receiving Inspection Stats | ❌ | — | — | Medium |
| **Quality** | Nonconformance Report | ❌ | — | — | High |
| **Inventory** | Cutter Inventory Dashboard | ✅ | Yes (Excel-style) | ✅ Excel | — |
| **Inventory** | Stock Consumption (6m/3m/2m) | ✅ (in dashboard) | Yes | ✅ Excel | — |
| **Inventory** | GRN Report | ❌ | — | — | Medium |
| **HR** | Competency Matrix | ✅ | By process | ✅ Excel | — |
| **HR** | Competency Gap Report | ✅ | By level | No | — |
| **HR** | Employee Roster | 🔶 List only | Search | No | Low |
| **Maintenance** | Equipment Status | ❌ | — | — | Medium |
| **Maintenance** | PM Schedule Compliance | ❌ | — | — | Medium |
| **Safety** | Incident Log | ❌ | — | — | Medium |
| **Safety** | HSE Statistics | ❌ | — | — | Low |
| **Sales** | Order Status | ❌ | — | — | Medium |
| **Sales** | Revenue by Account | ❌ | — | — | Low |
| **Finance** | WO Costing Report | ❌ | — | — | High |
| **Finance** | Invoice Tracking | ❌ | — | — | Medium |

---

## 11. Security Audit

### 11.1 Authentication & Access Control

**Overall Assessment: STRONG**

- **All sensitive views** are protected with `@login_required` or `LoginRequiredMixin` (1,114+ decorators found across all apps)
- **All API endpoints** (`api_*` functions) are protected with `@login_required`
- **All file upload handlers** are protected with `@login_required` + `@require_POST`

**Issue Found:**

| View | File | Issue |
|------|------|-------|
| `stop_recording()` | `apps/erp_automation/views.py:585` | Missing `@login_required` — publicly accessible endpoint with `@csrf_exempt` |

**Views with `@login_required` but no role-based permission check:**
Most views only check "is the user logged in" — they do not check whether the user's role permits the action. This is acceptable in the current single-facility deployment but will need role-based guards before multi-team production use.

### 11.2 Data Security

**CSRF Exemptions (2 found):**

| View | File | Justification |
|------|------|---------------|
| `stop_recording()` | `erp_automation/views.py:585` | **Unjustified** — missing @login_required too |
| `execute_workflow_api()` | `erp_automation/views.py:1234` | Acceptable — has `@login_required`, JSON body API |

**Raw SQL:** Only in migrations (2 instances) — no application-level raw SQL. All queries use Django ORM.

**File Uploads:** All handlers authenticated. No explicit file type validation in upload views (relies on Django/Pillow MIME checking). Recommend adding extension whitelist.

**Sensitive Data:** No credentials logged. ERP credentials stored in Django session (not DB). Default admin password hardcoded in `create_default_admin.py` management command.

### 11.3 Configuration Security

| Setting | Value | Assessment |
|---------|-------|------------|
| DEBUG | `True` | ❌ Must be `False` in production |
| SECRET_KEY | In `.env` file (committed to git) | ❌ **CRITICAL** — must regenerate and keep out of git |
| ALLOWED_HOSTS | localhost + github.dev | ⚠️ Must be restricted to production domain |
| Database | SQLite | ⚠️ Not suitable for production (use PostgreSQL) |
| SESSION_COOKIE_SECURE | `False` (dev) | Auto-sets to `True` when `DEBUG=False` ✅ |
| CSRF_COOKIE_SECURE | `False` (dev) | Auto-sets to `True` when `DEBUG=False` ✅ |
| SECURE_SSL_REDIRECT | `False` | Must enable in production |
| HSTS | Configured for production (31,536,000s) | ✅ Ready |
| X_FRAME_OPTIONS | `SAME_ORIGIN` | ✅ |
| SECURE_CONTENT_TYPE_NOSNIFF | `True` | ✅ |
| SECURE_REFERRER_POLICY | `same-origin` | ✅ |

### 11.4 Dependency Vulnerabilities

| Package | Concern | Severity |
|---------|---------|----------|
| `bleach>=6.0` | Bleach project is officially deprecated (Jan 2023); recommend `nh3` as replacement | Low |
| `xhtml2pdf>=0.2.11` | Known rendering issues; limited maintenance | Low |
| All others | Current versions, no known active CVEs | — |

### 11.5 Security Issue Summary Table

| # | Issue | Location | Severity | Fix Required |
|---|-------|----------|----------|--------------|
| 1 | SECRET_KEY committed to git via `.env` | `.env` | **Critical** | Regenerate key, add `.env` to `.gitignore`, rotate immediately |
| 2 | DEBUG=True in `.env` | `.env` | **Critical** | Must be `False` before production deployment |
| 3 | `stop_recording()` missing auth | `erp_automation/views.py:585` | Medium | Add `@login_required` |
| 4 | Hardcoded admin password | `create_default_admin.py` | Medium | Use environment variable |
| 5 | No file type validation on uploads | Multiple views | Medium | Add extension whitelist |
| 6 | No role-based permission guards | Most views | Medium | Add permission checks before production |
| 7 | SQLite in production | `settings.py` | Medium | Migrate to PostgreSQL |
| 8 | Deprecated `bleach` package | `requirements.txt` | Low | Replace with `nh3` |

---

## 12. UI/UX & Frontend Consistency Audit

### Framework Consistency

- **CSS Framework:** Tailwind CSS via CDN (JIT mode) — consistent across all templates
- **Reactivity:** Alpine.js 3.14.0 — used consistently for client-side interactions
- **Dynamic Updates:** HTMX 2.0.0 — used for form submissions, partial page updates, notification polling
- **Icons:** Lucide Icons — consistent icon set across all pages
- **Base Template:** All pages extend `base.html` — sidebar, topnav, dark mode toggle inherited consistently

### Positive Patterns

- **Dark mode:** Fully supported with localStorage persistence
- **Sidebar navigation:** Collapsible, grouped by functional area, with state persistence
- **Toast notifications:** Consistent component (`components/toast.html`) with slide-down animation
- **Column filters:** Excel-style filters on list pages (cutter inventory, drill bit list, design list, HDBS types)
- **Print layouts:** QAS-standard print CSS for inspection forms, die checks, release papers
- **Photo module:** Reusable component with ADG-guided capture, camera integration, Fabric.js editing

### Issues Found

| Issue | Scope | Impact |
|-------|-------|--------|
| Tailwind via CDN (not compiled) | All pages | Console warning; slower initial load; not production-optimized |
| No loading/spinner states on HTMX requests | Most forms | User sees no feedback during slow saves |
| Some pages use inline styles alongside Tailwind classes | Cutter map, evaluation grids | Maintainability concern |
| Mobile responsiveness varies | Complex pages (cutter map, evaluation grids) | Evaluation grids not usable on phone-width screens |
| No standardized empty state component | List pages | Some lists show nothing when empty; others show "No records found" |
| Form validation feedback inconsistent | Various forms | Some use Django messages, some use Alpine.js inline validation, some have none |
| Duplicate `templates/templates/` directory | Project root | 609 orphaned template copies — should be deleted |

### Recommendation

Define a standard component library documenting: button styles (primary/secondary/danger/ghost), form layout patterns, card components, table conventions, modal patterns, empty states, loading states, and error states. This would improve consistency as new pages are built.

---

## 13. Code Quality & Technical Debt

### TODO/FIXME/HACK Comments

A representative sample (the codebase is large — these are the most significant):

| File | Content | Priority |
|------|---------|----------|
| `inventory/views.py` | Multiple TODO markers for future optimization | Low |
| `workorders/views_jobcard.py` | Large view functions (several > 150 lines) | Medium |
| `erp_automation/services/executor.py` | Complex method chains > 200 lines | Medium |

### Orphaned/Dead Code

| Item | Location | Status |
|------|----------|--------|
| `ERP_Item_creation_automation/` app | `apps/` | Legacy Flask app — superseded by `erp_automation` |
| `templates/templates/` directory | Project root | 609 duplicate template files |
| `apps/apps/` nested directory | `apps/` | Duplicate management commands (legacy scaffolding) |
| `FieldMapping` model | `erp_automation/models.py` | Unused — templates handle field mapping |
| `Locator.screenshot` ImageField | `erp_automation/models.py` | Never populated |
| `erp_integration` app | `apps/` | Placeholder — no views, no active usage |

### Large Functions (> 100 lines)

| Function/Method | File | Lines | Recommendation |
|----------------|------|-------|----------------|
| `CutterInventoryListView.get_context_data` | `inventory/views.py` | ~200 | Already optimized (N+1 fix); could extract stock calculation |
| `api_sync_to_erp` | `cutter_map/views.py` | ~180 | Extract BOM creation logic to service |
| `execute_workflow` | `erp_automation/executor.py` | ~250 | Modular by design (delegates to InteractionEngine) |
| `start_debug_chain` | `erp_automation/executor.py` | ~300 | Complex but necessary for batch debug execution |
| `_debug_step_loop` | `erp_automation/executor.py` | ~400 | Core debug executor — too complex but tightly coupled |

### Migration Count

The `workorders` app has 72 migrations — significantly more than typical. This is a natural result of active development but may benefit from migration squashing before production deployment.

---

## 14. Dependencies & Third-Party Libraries

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| Django | >=5.1,<5.2 | Core web framework | ✅ Current |
| psycopg[binary] | >=3.1 | PostgreSQL adapter | ✅ Current (unused in dev — SQLite) |
| django-htmx | >=1.17 | HTMX middleware | ✅ Current |
| django-widget-tweaks | >=1.5 | Form widget customization | ✅ Current |
| django-crispy-forms | >=2.1 | Form rendering | ✅ Current |
| crispy-tailwind | >=1.0 | Tailwind CSS forms | ✅ Current |
| django-filter | >=23.0 | Generic queryset filtering | ✅ Current |
| django-environ | >=0.11 | Environment variable management | ✅ Current |
| django-extensions | >=3.2 | Extended management commands | ✅ Current |
| django-debug-toolbar | >=4.2 | Development debugging | ✅ Current (dev only) |
| Pillow | >=10.0 | Image processing | ✅ Current |
| python-barcode | >=0.15 | Barcode generation | ✅ Current |
| qrcode | >=7.4 | QR code generation | ✅ Current |
| markdown | >=3.5 | Markdown parsing | ✅ Current |
| bleach | >=6.0 | HTML sanitization | ⚠️ **Deprecated** — replace with `nh3` |
| openpyxl | >=3.1 | Excel file handling | ✅ Current |
| pandas | >=2.0 | Data manipulation | ✅ Current |
| playwright | >=1.40 | Browser automation (D365) | ✅ Current |
| reportlab | >=4.0 | PDF generation | ✅ Current |
| xhtml2pdf | >=0.2.11 | HTML to PDF conversion | ⚠️ Limited maintenance |
| pymupdf | >=1.24 | PDF extraction (Halliburton) | ✅ Current |
| python-pptx | >=0.6.21 | PowerPoint generation | ✅ Current |
| whitenoise | >=6.6 | Static file serving | ✅ Current |
| gunicorn | >=21.0 | WSGI HTTP server | ✅ Current (production) |
| pytest | >=7.4 | Testing framework | ✅ Current |
| pytest-django | >=4.5 | Django test integration | ✅ Current |
| pytest-cov | >=4.1 | Coverage reporting | ✅ Current |
| factory-boy | >=3.3 | Test data factories | ✅ Current |
| black | >=23.0 | Code formatter | ✅ Current |
| isort | >=5.12 | Import sorting | ✅ Current |
| flake8 | >=6.0 | Linting | ✅ Current |

**Unused packages:** `jinja2` is imported by cutter_map PDF template but not in requirements.txt. Should be added.

---

## 15. Prioritized Recommendations

### 15.1 Critical — Fix Before Any Production Deployment

1. **Regenerate SECRET_KEY and remove `.env` from git history.** The current secret key is committed to the repository. Any person with access can forge sessions.
2. **Set DEBUG=False** in production environment. Currently `True`, exposing full error pages and SQL queries.
3. **Migrate to PostgreSQL** for production. SQLite does not support concurrent writes and has no backup strategy.
4. **Add `@login_required` to `stop_recording()`** in `erp_automation/views.py`.
5. **Replace hardcoded admin password** in `create_default_admin.py` with environment variable.

### 15.2 High — Complete Before Production Use

6. **Implement role-based permission guards** on all sensitive views (currently only login-required).
7. **Build QC Inspector dashboard** — this role has no dedicated workbench despite being critical to operations.
8. **Add SLA/overdue alerts** — bits can sit at a stage indefinitely with no automated escalation.
9. **Build Work Order Status Summary report** — management's most requested view.
10. **Add file type validation** to all upload handlers (extension whitelist).
11. **Delete `templates/templates/` duplicate directory** (609 orphaned files).
12. **Delete `apps/apps/` duplicate directory** and `ERP_Item_creation_automation/` legacy app.

### 15.3 Medium — Planned Enhancements

13. **Complete dispatch workflow** — packing list, delivery note, certificate of conformity.
14. **Build scrap processing workflow** — downstream flow after SCRAP decision.
15. **Add maintenance scheduling** — PM compliance tracking and equipment downtime.
16. **Standardize form validation** — consistent error display pattern across all forms.
17. **Add loading states** to HTMX interactions (spinner during save operations).
18. **Compile Tailwind CSS** instead of using CDN for production performance.
19. **Squash migrations** in workorders app (72 migrations → ~5 squashed).

### 15.4 Long-Term — Future Roadmap

20. **Mobile-optimized operator interface** — current operator portal works but evaluation grids need responsive redesign.
21. **Direct D365 API integration** — replace browser automation with REST API calls where possible.
22. **Advanced analytics and KPI dashboards** — step duration trends, throughput by account, quality metrics.
23. **Customer portal** — read-only access for clients to track their bits.
24. **Multi-facility support** — if ARDTCO expands to additional locations.
25. **Automated stock reorder alerts** based on consumption trends and lead times.

---

## 16. Summary Statistics

| Metric | Count |
|--------|-------|
| **Total Django Apps** | 28 (active) + 1 (legacy) |
| **Total Models** | 330+ |
| **Total Views/Functions** | 1,250+ |
| **Total URL Patterns** | 1,124 |
| **Total Templates** | 1,265 |
| **Total Migrations** | 277 |
| **Total Management Commands** | 136 |
| **Total Requirements** | 27 packages |
| **System Version** | 5.4 |
| **Estimated System Completion** | 65% |
| **Open Security Issues** | 8 (Critical: 2, Medium: 4, Low: 2) |
| **Missing Reports** | 15+ |
| **Roles Without Dedicated Dashboards** | 5 (QC Inspector, Tech Rep, Maintenance, Sales, Finance) |
| **Core Modules Complete** | 8 of 12 |
| **Support Modules Complete** | 1 of 8 |

### Completion Breakdown

| Category | Complete | Partial | Not Started |
|----------|----------|---------|-------------|
| **Core Production** (WO, Bits, Routing, Evaluation) | ✅ | — | — |
| **Receiving Dock** (Backload, Inspection) | ✅ | — | — |
| **Cutter Inventory & BOM** | ✅ | — | — |
| **ERP Automation** (D365) | ✅ | — | — |
| **Production Planning** | ✅ | — | — |
| **Notifications & Workflow Engine** | — | 🔶 | — |
| **HR & Competency** | — | 🔶 | — |
| **Sales & Orders** | — | 🔶 | — |
| **Supply Chain** | — | 🔶 | — |
| **Dispatch** | — | 🔶 | — |
| **Quality Management** | — | 🔶 | — |
| **Compliance** | — | 🔶 | — |
| **Maintenance** | — | 🔶 | — |
| **HSSE** | — | 🔶 | — |
| **Reporting** | — | — | ❌ |
| **Finance** | — | — | ❌ |

---

*Document generated by automated codebase analysis on April 4, 2026.*
*Source of truth: Django project at `D:\PycharmProjects\floor_management_system-D3`*
