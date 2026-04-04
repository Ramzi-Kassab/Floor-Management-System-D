# ARDT FMS — MASTER DOCUMENTATION & PRESENTATION PROMPT
**Save this file to:** `D:\PycharmProjects\floor_management_system-D3\MASTER_DOCUMENTATION_PROMPT.md`
**How to use:** Paste the single trigger command at the bottom of this file into Claude Code.

---

```
═══════════════════════════════════════════════════════════════════════════════
ARDT FLOOR MANAGEMENT SYSTEM
MASTER DOCUMENTATION, USER MANUALS & EXECUTIVE PRESENTATION
One-Session Autonomous Execution Plan
Model  : Claude Sonnet 4.6
Mode   : Read-only analysis + document generation — NO changes to source code
═══════════════════════════════════════════════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT IDENTITY & CORE MANDATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are a senior technical writer, systems analyst, and presentation designer
working on the ARDT Floor Management System (FMS). You have been assigned to
produce three interconnected deliverables in a single session, in order.

Your core principles for this entire session:
  1. HONESTY FIRST — Never describe a feature that does not exist in the code.
     If something is missing, incomplete, or broken — say so explicitly.
  2. CODE IS THE SOURCE OF TRUTH — Every claim must be backed by what you
     actually read. Never assume, infer, or fabricate functionality.
  3. NO CHANGES TO SOURCE CODE — You are here to observe and document, not fix.
     Do not modify any .py, .html, .js, or migration files.
  4. COMPLETENESS — Do not skip sections. If you cannot determine something,
     write "[NEEDS VERIFICATION]" and continue. Do not leave blank sections.
  5. SEQUENTIAL EXECUTION — Complete Phase 1 fully before starting Phase 2.
     Complete Phase 2 fully before starting Phase 3. Print a completion
     confirmation after each phase before proceeding.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROJECT CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Project Name    : ARDT Floor Management System (FMS)
Company         : Arabian Rockbits & Drilling Tools Co. Ltd. (ARDTCO)
Location        : Eastern Province, Saudi Arabia
Framework       : Django (Python)
Project Root    : D:\PycharmProjects\floor_management_system-D3
Primary Domain  : PDC and RC drill bit repair and manufacturing lifecycle
Key Clients     : Saudi Aramco, Halliburton
System Scope    : Production, Technical, Quality, Sales, HR, Finance, Reporting
Author/Owner    : Ramzi — PDC Repair Supervisor / Acting Operations Manager
Output Folder   : D:\PycharmProjects\floor_management_system-D3\DOCS\

Drill Bit Lifecycle (domain knowledge — use this to validate workflow coverage):
  Received → Visual Inspection → Die Check → LPT/Pressure Test →
  API Thread Inspection → Evaluation & Routing Decision →
  [Full Repair / Light Dress / Return As-Is / Scrap] →
  Repair Steps (Sandblast, Hardfacing, Brazing, Gauge, Cutter Replacement) →
  Post-Repair QC → Final Inspection → Dispatch to Client

Key domain terms to use correctly in all documents:
  PDC   — Polycrystalline Diamond Compact (bit type)
  RC    — Roller Cone (bit type)
  BOM   — Bill of Materials (cutter layout specification)
  CL    — Cutter Layout (visual diagram)
  LPT   — Leak Pressure Test (hydraulic integrity check)
  WO    — Work Order
  FMS   — Floor Management System
  ERP   — Enterprise Resource Planning (D365 Finance & Operations)
  Bit sizes always as fractions: 8 3/8", 12 1/4", 6 1/8" — never decimals

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GLOBAL DISCOVERY — RUN ONCE BEFORE ALL PHASES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before starting Phase 1, perform a full codebase scan. This scan powers all
three phases, so be thorough. Take internal notes as you go.

DISCOVERY CHECKLIST:
  □ Read full directory tree of project root
  □ Read settings.py — note apps, middleware, auth, DB, static/media config
  □ Read requirements.txt — note all packages with versions
  □ For each Django app found, read in full:
      models.py, views.py, urls.py, forms.py, admin.py,
      serializers.py (if any), signals.py (if any), utils.py (if any)
  □ List all templates — group by app and feature
  □ Check migrations/ in each app — count and note anomalies
  □ Check for any .env, config.py, or secrets files
  □ Check for any existing README.md, CLAUDE.md, or documentation files
  □ Check static files structure
  □ Check for any management commands (management/commands/)
  □ Look for any celery tasks, cron jobs, or background workers
  □ Look for any API endpoints or REST framework usage
  □ Check base.html and note the UI framework (Bootstrap version, custom CSS)

After discovery, create the output folder if it does not exist:
  D:\PycharmProjects\floor_management_system-D3\DOCS\
  D:\PycharmProjects\floor_management_system-D3\DOCS\MANUALS\

Then proceed to Phase 1.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 — MASTER PROJECT DOCUMENTATION
Output: DOCS\PROJECT_DOCUMENTATION.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write a single comprehensive Markdown file. Do not rush. Do not skip sections.
Minimum length: 3,500 words. No maximum.

Use this exact structure:

───────────────────────────────────────────────────────────────────────────────

# ARDT Floor Management System — Master Project Documentation

> Version: Draft 1.0
> Generated: [today's date]
> Status: Active Development
> Confidential — Internal Use Only

---

## Table of Contents
(Auto-generate numbered TOC linking to each section)

---

## 1. Executive Summary

Write 4–5 paragraphs covering:
- What the system does in plain business language (no developer terms)
- The specific business problem it solves at ARDTCO
- Who uses it and how it fits into daily operations
- Current deployment status (development / staging / live)
- The strategic value: what becomes possible with FMS that wasn't before

---

## 2. System Architecture

- Full tech stack with exact versions (Django x.x, Python x.x, DB engine)
- Authentication mechanism (session-based, JWT, custom)
- File storage approach (local, cloud, media root)
- Static files handling
- Deployment environment inferred from settings (DEBUG state, ALLOWED_HOSTS)
- Any external integrations detected (ERP, email backend, APIs)
- ASCII architecture diagram:

```
[Browser] ──► [Django App Server]
                    │
            ┌───────┼───────┐
            ▼       ▼       ▼
         [DB]  [Media]  [Static]
```

Expand this diagram to show all detected apps as connected modules.

---

## 3. Application Map

For each Django app detected, write a subsection:

### App: [app_name]
- **Purpose:** (1–2 sentences)
- **Models:** (table with Name | Key Fields | Relationships)
- **Views:** (table with View Name | URL Pattern | Auth Required | Purpose)
- **Templates:** (list)
- **Completion Status:**
  - ✅ Complete
  - 🔶 Partial — describe exactly what's done and what's missing
  - ❌ Not Started

---

## 4. Full Data Model Reference

For every model across all apps:

| App | Model | Key Fields | Relationships | Issues Found |
|-----|-------|------------|---------------|--------------|

Then for each model that has issues, expand:
- Missing __str__ method
- Missing Meta class or ordering
- Missing indexes on frequently queried fields
- Orphaned model (no views reference it)
- Any field type concerns

---

## 5. URL & Navigation Map

Complete URL inventory grouped by app:

| App | URL Pattern | View Name | Auth Required | Status |
|-----|-------------|-----------|---------------|--------|

Flag any URLs that:
- Are accessible without login
- Have no corresponding template
- Lead to views with no permission checks beyond basic login

---

## 6. User Roles & Permission Architecture

- All groups/roles defined in the system
- How permissions are assigned (Django groups, custom decorators, middleware)
- Matrix: Role × Feature × Access Level (View / Edit / Admin / None)
- Roles that exist in code but have no dedicated dashboard or workbench
- Roles that should exist based on domain but are not yet defined

---

## 7. Business Workflow Coverage

Map every stage of the drill bit lifecycle against system implementation:

| Workflow Stage | Implemented | Model/View | Template | Gap Description |
|----------------|-------------|------------|----------|-----------------|
| Bit Received      | ✅/🔶/❌ | ... | ... | ... |
| Visual Inspection | ✅/🔶/❌ | ... | ... | ... |
| Die Check         | ✅/🔶/❌ | ... | ... | ... |
| LPT Test          | ✅/🔶/❌ | ... | ... | ... |
| API Thread Check  | ✅/🔶/❌ | ... | ... | ... |
| Evaluation/Route  | ✅/🔶/❌ | ... | ... | ... |
| Full Repair       | ✅/🔶/❌ | ... | ... | ... |
| Light Dress       | ✅/🔶/❌ | ... | ... | ... |
| Return As-Is      | ✅/🔶/❌ | ... | ... | ... |
| Scrap Decision    | ✅/🔶/❌ | ... | ... | ... |
| Post-Repair QC    | ✅/🔶/❌ | ... | ... | ... |
| Final Inspection  | ✅/🔶/❌ | ... | ... | ... |
| Dispatch          | ✅/🔶/❌ | ... | ... | ... |

Also describe: where workflow breaks, missing transitions, unguarded status changes.

---

## 8. Notification & Approval System

- What notification triggers currently exist in the code (signals, email sends)
- What approval flows exist (multi-step form approvals, manager sign-offs)
- What is designed/planned but not yet implemented
- Critical missing notifications (e.g., no alert when bit is overdue at a stage)
- Rate each gap: Critical / High / Medium / Low

---

## 9. Dashboard & Workbench Status

For each user role, describe:
- Does a dedicated dashboard/workbench exist? (Yes / Partial / No)
- What widgets/KPIs are shown (if it exists)
- What widgets are missing for that role
- Priority of completing it

---

## 10. Reporting Module Status

| Report Category | Report Name | Exists | Filterable | Exportable | Priority |
|-----------------|-------------|--------|------------|------------|----------|
| Production      | ...         | ✅/❌  | ✅/❌      | ✅/❌      | H/M/L    |
| Quality         | ...         | ...    | ...        | ...        | ...      |
| HR              | ...         | ...    | ...        | ...        | ...      |
| Maintenance     | ...         | ...    | ...        | ...        | ...      |
| Safety          | ...         | ...    | ...        | ...        | ...      |
| Sales / Revenue | ...         | ...    | ...        | ...        | ...      |
| Finance         | ...         | ...    | ...        | ...        | ...      |

---

## 11. Security Audit

Be honest. Be thorough. Do not soften findings.

### 11.1 Authentication & Access Control
- Views missing @login_required (list each one with file + line)
- Views with login required but no permission/role check
- Any views with @csrf_exempt (list with justification assessment)
- Any unauthenticated API endpoints

### 11.2 Data Security
- Any raw SQL queries (list with file + line)
- Any unvalidated or unsanitized user inputs
- Any file upload handlers — are file types validated? Size limited?
- Any sensitive data logged or exposed in error messages

### 11.3 Configuration Security
- DEBUG state in settings.py (should be False in production)
- SECRET_KEY — is it hardcoded or pulled from environment?
- ALLOWED_HOSTS — is it properly restricted?
- Database credentials — hardcoded or environment variable?
- HTTPS/SECURE settings (SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, etc.)
- CORS settings (if any)

### 11.4 Dependency Vulnerabilities
- Note any packages that are known to have had CVEs or are outdated
- Note any packages with no recent maintenance activity

### 11.5 Security Issue Summary Table
| Issue | Location | Severity | Fix Required |
|-------|----------|----------|--------------|
| ...   | ...      | Critical/High/Medium/Low | ... |

---

## 12. UI/UX & Frontend Consistency Audit

- Bootstrap version in use — is it consistent across all templates?
- Are there inline styles mixed with class-based styling?
- Is there a single base.html inherited by all templates?
- Inconsistent component patterns (buttons, forms, cards, tables)
- Templates missing responsive/mobile considerations
- Missing loading states, empty states, or error states in UI
- Forms without proper client-side or server-side validation feedback
- Recommend: define a standard component library and style guide

---

## 13. Code Quality & Technical Debt

- List all TODO, FIXME, HACK, and XXX comments found (file + line + content)
- Orphaned templates (exist in templates/ but no view renders them)
- Dead views (exist in views.py but no URL points to them)
- Duplicate logic across views that should be refactored into utilities
- Inconsistent naming conventions (snake_case vs camelCase, etc.)
- Migration anomalies (unapplied, squashed, fake, or conflicting migrations)
- Any large functions (> 100 lines) in views.py that should be split

---

## 14. Dependencies & Third-Party Libraries

Full table from requirements.txt:

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| Django  | x.x.x   | Core framework | Current/Outdated/Deprecated |
| ...     | ...     | ...     | ...    |

Flag any package not actively imported/used in the codebase.

---

## 15. Prioritized Recommendations

### 15.1 Critical — Fix Immediately (Security & Data Integrity)
(Numbered list, most critical first)

### 15.2 High — Complete Before Production
(Features close to done, or broken workflows)

### 15.3 Medium — Planned Enhancements
(UI standardization, reporting, notifications)

### 15.4 Long-Term — Future Roadmap
(Mobile optimization, ERP integration, analytics)

---

## 16. Summary Statistics

Auto-calculate from discovery:
- Total Django apps: [N]
- Total models: [N]
- Total views: [N]
- Total URL patterns: [N]
- Total templates: [N]
- Estimated system completion: [N]%
- Open security issues: [N] (Critical: N, High: N, Medium: N, Low: N)
- Missing reports: [N]
- Roles without dashboards: [N]

───────────────────────────────────────────────────────────────────────────────

After saving PROJECT_DOCUMENTATION.md, print to terminal:
  ✅ PHASE 1 COMPLETE — PROJECT_DOCUMENTATION.md saved
  📊 Stats: [apps] apps, [models] models, [views] views, [templates] templates
  ⚠️  Top 3 Critical Issues: [list them]
  ➡️  Proceeding to Phase 2...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 — USER MANUALS BY ROLE
Output: DOCS\MANUALS\MANUAL_[NN]_[ROLE].md + DOCS\MANUALS\INDEX.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Using what you learned in the Discovery phase and Phase 1, produce one Markdown
manual per user role. Write for a non-developer end user — no Python class names,
no database field names, no Django terminology.

Writing rules:
  - Plain professional English — readable by a shop-floor technician
  - Every workflow step must be a concrete, actionable instruction
  - Describe screens as the user sees them, not as a developer coded them
  - If a feature does not exist yet, write:
    "⚠️ This feature is currently under development and will be available in a
    future update." — then describe what it WILL do when complete.
  - Never write vague steps like "configure the settings" or "open the module."
    Always specify: Menu → Section → Button → Field → Action.

ROLES TO COVER:
Identify all roles from the code. At minimum write a manual for each role below.
For any role not yet implemented, write a placeholder manual with the ⚠️ notice.

  01. System Administrator
  02. General Manager / Senior Management
  03. Operations Manager
  04. PDC Repair Supervisor
  05. Manufacturing Supervisor
  06. Machine Operator / CNC Technician
  07. Welder / Brazer Technician
  08. Quality Control Inspector
  09. Receiving & Dispatch Clerk
  10. Maintenance Technician
  11. HR / Admin Staff
  12. Sales / Customer Service Representative
  13. Finance / Invoicing Staff
  14. Read-Only Viewer (if role exists)
  [Add any additional roles found in the code]

MANUAL TEMPLATE — use this exact structure for every role:

───────────────────────────────────────────────────────────────────────────────

# [Role Title] — User Manual
**System:** ARDT Floor Management System
**Version:** Draft 1.0
**Date:** [today's date]
**Audience:** [Role Title] — [1-line description of who this person is]

---

## 1. Your Role in the System
2–3 paragraphs: what this person does day-to-day, why they use FMS,
and what value the system provides to their specific work.

---

## 2. Logging In

**System URL:** [from settings or deployment config — or write "[To be confirmed]"]

Step-by-step:
1. Open your web browser and go to the system URL above.
2. Enter your username in the Username field.
3. Enter your password in the Password field.
4. Click the **Log In** button.
5. You will be taken to your personal workbench (home screen).

**If you cannot log in:**
- Check your username and password are correct (passwords are case-sensitive).
- If you have forgotten your password, contact your system administrator.
- Do not share your login credentials with anyone.

---

## 3. Your Workbench (Home Screen)

Describe exactly what appears on screen for this role after login:
- Navigation menu items visible (only those this role can see)
- Dashboard widgets, counters, or cards shown
- Quick-action buttons available
- Any alerts or notification badges

⚠️ Write "[WORKBENCH UNDER DEVELOPMENT]" if no dedicated workbench exists yet,
and describe what it will include when complete.

---

## 4. Core Workflows

For each major task this role performs, write a full workflow section:

### Workflow: [Workflow Name]
**What this does:** 1 sentence explaining the purpose.
**When to use it:** The specific situation that triggers this action.
**Before you start:** Any prerequisites (e.g., "The bit must already be received").

**Steps:**
1. From your workbench, click **[Menu Item]** in the navigation bar.
2. Click **[Button or Link name]**.
3. In the **[Field Name]** field, enter [description of what to type/select].
4. [Continue — be specific for every step]
5. Click **[Save / Submit / Confirm]** to complete.

**What happens next:** Describe the outcome and any automatic actions triggered.
**Who is notified:** Who receives a notification or alert after this step.
**Common mistakes:**
- [Mistake 1] → [How to avoid or fix it]
- [Mistake 2] → [How to avoid or fix it]

(Repeat this block for every workflow this role performs)

---

## 5. Forms & Data Entry Reference

| Form Name | Where to Find It | Required Fields | Notes |
|-----------|-----------------|-----------------|-------|
| ...       | Menu → Section  | Field1, Field2  | ...   |

For each required field, describe:
- What valid input looks like
- Common data entry errors to avoid

---

## 6. Reports Available to You

| Report | Location | What It Shows | Filters | Export |
|--------|----------|---------------|---------|--------|
| ...    | ...      | ...           | ...     | PDF/Excel/⚠️ |

⚠️ Write "Under development" for any report not yet built.

---

## 7. Notifications & Alerts

Describe every notification this role:
  - **Receives** (what triggers it, where it appears, what action to take)
  - **Triggers for others** (what their actions send to colleagues)

⚠️ Write "[NOTIFICATION SYSTEM UNDER DEVELOPMENT]" if not yet implemented.

---

## 8. Approvals & Sign-offs

Describe every approval this role:
  - **Must give** (what they are approving and how to approve it in the system)
  - **Must receive** (what they are waiting for before they can proceed)

⚠️ Write "[APPROVAL WORKFLOW UNDER DEVELOPMENT]" if not yet implemented.

---

## 9. Frequently Asked Questions

Write 6–10 realistic Q&A pairs based on the actual workflows above.
Questions should be things this specific role would genuinely ask.

Example format:
**Q: What do I do if I made a mistake in a work order I already submitted?**
A: You can edit a work order as long as its status is still "Draft." Once it has
been moved to "In Progress," contact your supervisor to request a correction.

---

## 10. Glossary

List only the terms relevant to this specific role.
Use plain definitions — no technical jargon.

| Term | Definition |
|------|-----------|
| PDC  | Polycrystalline Diamond Compact — a type of drill bit used in oil & gas drilling. |
| WO   | Work Order — the system record that tracks a drill bit through its entire repair process. |
| ...  | ... |

───────────────────────────────────────────────────────────────────────────────

FILE NAMING:
  DOCS\MANUALS\MANUAL_01_SYSTEM_ADMIN.md
  DOCS\MANUALS\MANUAL_02_GENERAL_MANAGER.md
  DOCS\MANUALS\MANUAL_03_OPERATIONS_MANAGER.md
  DOCS\MANUALS\MANUAL_04_PDC_REPAIR_SUPERVISOR.md
  DOCS\MANUALS\MANUAL_05_MANUFACTURING_SUPERVISOR.md
  DOCS\MANUALS\MANUAL_06_MACHINE_OPERATOR.md
  DOCS\MANUALS\MANUAL_07_WELDER_BRAZER.md
  DOCS\MANUALS\MANUAL_08_QC_INSPECTOR.md
  DOCS\MANUALS\MANUAL_09_RECEIVING_DISPATCH.md
  DOCS\MANUALS\MANUAL_10_MAINTENANCE_TECHNICIAN.md
  DOCS\MANUALS\MANUAL_11_HR_ADMIN.md
  DOCS\MANUALS\MANUAL_12_SALES.md
  DOCS\MANUALS\MANUAL_13_FINANCE.md
  [continue for any additional roles]

AFTER ALL MANUALS ARE WRITTEN, create:
  DOCS\MANUALS\INDEX.md

INDEX.md structure:
# FMS User Manuals — Index
| # | Role | File | Status | Summary |
|---|------|------|--------|---------|
| 01 | System Administrator | MANUAL_01_SYSTEM_ADMIN.md | Complete/Placeholder | 1-line summary |
| ...

After saving all manuals, print to terminal:
  ✅ PHASE 2 COMPLETE — [N] manuals written, INDEX.md created
  📁 Location: DOCS\MANUALS\
  ➡️  Proceeding to Phase 3...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 — EXECUTIVE POWERPOINT PRESENTATION
Output: DOCS\ARDT_FMS_Presentation.pptx (via DOCS\generate_presentation.js)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AUDIENCE:
  General Manager, Operations Leadership, Department Heads, Stakeholders.
  Assume they are NOT technical — no code, no developer terminology.
  They want to understand: what was built, why it matters, and what's next.

INSTALL DEPENDENCIES:
  npm install pptxgenjs
  pip install markitdown

DESIGN SYSTEM:
  Theme     : Industrial Precision (oil & gas, professional, data-driven)
  Motif     : Consistent left-side amber vertical accent bar (8pt) on content slides

  Colors:
    Navy     #1B2A3B   — primary background, authority
    Steel    #2E86AB   — technology, trust, action items
    Amber    #F18F01   — accent, energy, Saudi industrial identity
    Light BG #F4F6F8   — content slide backgrounds
    White    #FFFFFF   — text on dark slides
    Dark     #1B2A3B   — text on light slides
    Green    #2D6A4F   — completed / success indicators
    Red      #C1121F   — missing / critical indicators

  Fonts:
    Titles   : Calibri Bold, 40–44pt
    Subtitles: Calibri, 22–26pt
    Body     : Calibri, 15–17pt
    Captions : Calibri Light, 11–13pt

  Layout rules:
    - 0.5" minimum margin on all sides
    - 0.3" minimum gap between all elements
    - No text-only slides — every slide has at least one visual element
    - Left amber accent bar on all content slides (x:0, y:0, w:0.12", h:7.5", color:#F18F01)
    - Title slides: full navy background, white text
    - Content slides: light gray background #F4F6F8, dark text
    - Alternate section openers: navy background (for visual rhythm)

SLIDE DECK — 15 SLIDES:

SLIDE 01 — Title Slide (full navy background)
  Top-left: White rectangle 1.5"×0.6" labeled "ARDTCO" (logo placeholder)
  Center: Main title "ARDT Floor Management System" (white, 44pt bold)
  Below: Subtitle "Digital Transformation of PDC & RC Drill Bit Operations" (amber, 24pt)
  Below: "Prepared by: Ramzi | [Today's Date]" (white, 14pt)
  Bottom right: Small text "CONFIDENTIAL — INTERNAL USE ONLY" (gray, 11pt)
  Amber accent bar along bottom (full width, 0.15" height)

SLIDE 02 — Agenda (light background)
  Title: "What We'll Cover Today"
  Left amber accent bar
  10 agenda items as numbered blocks (amber number circle + bold title + 1-line desc)
  Items:
    1. The Business Challenge
    2. What is the FMS?
    3. System Architecture
    4. The Drill Bit Lifecycle
    5. Module Status Overview
    6. Role-Based Workbenches
    7. Business Impact & Key Metrics
    8. Security & Access Control
    9. Honest Status & Gaps
    10. Roadmap & Next Steps

SLIDE 03 — The Business Challenge (navy background, section opener)
  Title: "Before FMS — The Challenge" (white, 40pt)
  4 pain-point cards in 2×2 grid (steel blue cards, white text):
    Card 1: "No Visibility" — Work order status tracked manually or not at all
    Card 2: "Paper-Based" — Inspection records on paper, prone to loss and error
    Card 3: "No Audit Trail" — No traceability from receipt to dispatch
    Card 4: "Reporting Gaps" — Management reports built manually from memory
  Bottom strip (amber): "ARDTCO needed a system built for how drill bit repair actually works."

SLIDE 04 — What is the FMS? (light background)
  Title: "The ARDT Floor Management System"
  Top: 2-sentence definition paragraph (from Phase 1 executive summary)
  Three pillars below in equal columns (steel blue header bar + white body):
    Pillar 1: "Complete Lifecycle" — From the moment a bit arrives to the moment it ships
    Pillar 2: "Role-Based Workbenches" — Every user sees exactly what their position needs
    Pillar 3: "Digital Workflow" — Structured routing, approvals, and notifications
  Left amber accent bar

SLIDE 05 — System Architecture (light background)
  Title: "How the System is Built"
  Draw architecture using PptxGenJS shapes:
    Top row: "Web Browser" box (steel) → arrow → "Django Application Server" box (navy)
    Middle row: three boxes below Django: "PostgreSQL Database" | "File Storage" | "Static Assets"
    Bottom row: module boxes in two rows of 4:
      Row 1: Production | Quality | HR | Maintenance
      Row 2: Sales | Finance | Reporting | Notifications
    Color code: Built = steel blue, Partial = amber, Not started = light gray with dashed border
    Each module box shows its actual status (derived from Phase 1 findings — be honest)
  Caption: "All modules share a single database and unified permission system."
  Left amber accent bar

SLIDE 06 — The Drill Bit Lifecycle (light background, wide layout)
  Title: "Every Bit. Every Step. Tracked."
  Horizontal process flow across slide:
    8 rounded rectangles connected by arrows:
    [Receive] → [Inspect] → [Evaluate] → [Route] → [Repair] → [QC] → [Final Check] → [Dispatch]
  Below each box: 1-line description of what happens
  Color each box based on actual implementation status (from Phase 1 Section 7):
    ✅ Implemented = steel blue
    🔶 Partial = amber
    ❌ Not started = light gray
  Legend at bottom right (small): ■ Built  ■ In Progress  ■ Planned
  Left amber accent bar

SLIDE 07 — Module Status Dashboard (light background)
  Title: "System Modules — Current Build Status"
  3×3 grid of module status cards.
  Each card (white card with shadow effect):
    - Module name (navy, 16pt bold)
    - Status badge pill: ✅ COMPLETE (green) / 🔶 IN PROGRESS (amber) / ❌ PLANNED (red)
    - 2-line description of coverage
  Modules (fill status from Phase 1 actual findings — no fabrication):
    Work Orders | Receiving & Dispatch | Evaluation & Routing
    Quality Control | HR & Access | Reporting
    Notifications | Dashboards | Maintenance & Safety
  Left amber accent bar

SLIDE 08 — Role-Based Workbenches (light background)
  Title: "Built Around Your People"
  Subtitle: "Each position has a tailored workbench — only what they need, nothing more."
  Grid of role cards (4 columns):
    Each card: role title + status (Built / In Progress / Planned)
    Roles to include: all roles from Phase 2 manuals list
    Color code by status
  Left amber accent bar

SLIDE 09 — Business Impact & Key Metrics (navy background, section opener)
  Title: "The Value Delivered" (white, 40pt)
  4 large KPI cards in a row:
    Card 1: Number of work order stages tracked (from Phase 1 workflow count)
    Card 2: Number of user roles defined
    Card 3: Number of modules built or in progress
    Card 4: Number of automated workflow steps
  Use REAL numbers from Phase 1 wherever possible.
  If a number cannot be determined, write "Data to be confirmed" — never invent.
  Below cards: 2-sentence impact statement about audit trail, efficiency, and visibility.

SLIDE 10 — Security & Access Control (light background)
  Title: "Built on a Secure Foundation"
  Left column:
    How access is controlled:
    - Role-based permissions (who can see what)
    - Login required on all production views
    - Session management
    - [Any other security features found in Phase 1]
  Right column:
    What is protected:
    - Work order data and bit history
    - BOM and cutter specifications
    - Personnel and HR records
    - Quality inspection results
  Bottom note (amber background strip):
    If security issues were found in Phase 1, write:
    "⚠️ [N] security improvements identified — see project gap report."
    If no issues: "Security audit completed — no critical issues identified."
  Left amber accent bar

SLIDE 11 — Honest Status & Gap Analysis (light background)
  Title: "Where We Are — An Honest Assessment"
  Subtitle: "Transparency in project status enables better planning."
  Table with traffic-light rows (12–15 rows from Phase 1 Section 15):
    Columns: Feature Area | Status | Priority
    Row colors: navy text on green tint (done), amber tint (partial), red tint (missing)
    Pull REAL gap items from Phase 1 — do not invent
  Left amber accent bar

SLIDE 12 — Roadmap to Completion (light background)
  Title: "The Path Forward — 4 Phases"
  Horizontal timeline with 4 phase boxes (left to right):
    Phase 1 "Stabilize" (current):
      • Codebase cleanup & dead code removal
      • Security fixes (from audit)
      • UI/UX standardization across all templates
      • Timeframe: [estimate based on gap count]
    Phase 2 "Complete Core":
      • Dashboard & workbench completion for all roles
      • Full workflow engine with status guards
      • Notification system implementation
      • Timeframe: [estimate]
    Phase 3 "Reporting & Safety":
      • All production, maintenance, and safety reports
      • Export to PDF and Excel
      • Management analytics views
      • Timeframe: [estimate]
    Phase 4 "Scale & Integrate":
      • Mobile-optimized interfaces
      • ERP D365 integration
      • Advanced analytics and KPI dashboards
      • Timeframe: [estimate]
  Color: Current phase = amber, future phases = steel blue (progressively lighter)
  Left amber accent bar

SLIDE 13 — Why This Matters (full navy background, statement slide)
  Center of slide, white text, 28pt:
    "This system replaces paper, spreadsheets, and memory
     with a single source of truth — traceable, auditable,
     and built for the way ARDTCO actually works."
  Below, 3 amber bullet statements (20pt):
    • Every bit tracked from receipt to dispatch — nothing falls through the cracks
    • Every technician, supervisor, and manager sees exactly what they need
    • Every decision backed by real data — not estimates or recollections

SLIDE 14 — Next Steps (light background)
  Title: "Immediate Next Steps"
  Action table (3 columns): Action | Owner | Target
  6–8 rows pulled from Phase 1 Section 15.1 and 15.2 (critical + high priority items)
  Use REAL items from the gap analysis — no placeholders
  Row colors: alternating white and light gray
  Bottom: "Questions & Discussion" centered in amber box
  Left amber accent bar

SLIDE 15 — Closing Slide (full navy background)
  Top: "ARDTCO" white rectangle placeholder (same as Slide 01)
  Center: "ARDT Floor Management System" (white, 36pt bold)
  Below: "Precision. Quality. Performance." (amber, 20pt italic)
  Below: "For questions: Ramzi — PDC Repair Supervisor / Acting Operations Manager"
  Bottom amber bar (full width)

TECHNICAL EXECUTION:

Step 1 — Write the generation script:
  Save to: D:\PycharmProjects\floor_management_system-D3\DOCS\generate_presentation.js
  Use PptxGenJS. Build every slide as specified above using addSlide(), addText(),
  addShape(), and addTable(). All coordinates in inches.

Step 2 — Execute:
  cd D:\PycharmProjects\floor_management_system-D3\DOCS
  node generate_presentation.js

Step 3 — Verify output exists:
  Confirm ARDT_FMS_Presentation.pptx was created and is non-zero size.

Step 4 — Convert to images for QA:
  python scripts/office/soffice.py --headless --convert-to pdf ARDT_FMS_Presentation.pptx
  rm -f slide-*.jpg
  pdftoppm -jpeg -r 150 ARDT_FMS_Presentation.pdf slide
  ls -1 "$PWD"/slide-*.jpg

Step 5 — Visual QA:
  Inspect every slide image. Look for:
    - Text overflow or cut off at edges
    - Overlapping elements
    - Elements outside slide boundaries
    - Low-contrast text (especially white on light or dark on dark)
    - Misaligned shapes or inconsistent margins
    - Any leftover placeholder text
    - Layout inconsistencies across slides

Step 6 — Fix and re-verify:
  Fix all issues found. Regenerate. Re-inspect.
  Do not declare success until at least one fix-verify cycle is complete
  with zero remaining issues.

Step 7 — Content QA:
  python -m markitdown ARDT_FMS_Presentation.pptx
  Confirm all 15 slides have content. Fix any missing or wrong text.

After all QA passes, print to terminal:
  ✅ PHASE 3 COMPLETE — ARDT_FMS_Presentation.pptx saved
  📊 15 slides generated and QA verified
  ➡️  All three phases complete.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL SESSION SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After all three phases complete, print a final summary:

  ══════════════════════════════════════════════════
  ARDT FMS — DOCUMENTATION SESSION COMPLETE
  ══════════════════════════════════════════════════

  OUTPUT FILES:
  ✅ DOCS\PROJECT_DOCUMENTATION.md        — Master technical documentation
  ✅ DOCS\MANUALS\INDEX.md                — Manual index
  ✅ DOCS\MANUALS\MANUAL_01_*.md          — [N] role-specific user manuals
  ✅ DOCS\generate_presentation.js        — Presentation source script
  ✅ DOCS\ARDT_FMS_Presentation.pptx      — Executive presentation (15 slides)

  KEY FINDINGS:
  • Apps: [N] | Models: [N] | Views: [N] | Templates: [N]
  • System completion estimate: [N]%
  • Security issues found: [N] (Critical: N, High: N, Medium: N)
  • Roles without workbenches: [N]
  • Missing reports: [N]
  • Top priority action: [describe #1 critical item]

  All documents saved to:
  D:\PycharmProjects\floor_management_system-D3\DOCS\

  ══════════════════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONSTRAINTS & REMINDERS (Read before executing)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ❌ DO NOT modify any source code file (.py, .html, .js, migration files)
  ❌ DO NOT fabricate features, metrics, or completion percentages
  ❌ DO NOT skip sections — use [NEEDS VERIFICATION] for unknowns
  ❌ DO NOT use decimal notation for drill bit sizes (use fractions: 8 3/8")
  ❌ DO NOT declare a phase complete without printing the confirmation line
  ✅ DO read every file carefully before writing
  ✅ DO use tables and structured formats for comparative data
  ✅ DO be honest about gaps, bugs, and incomplete sections
  ✅ DO complete phases in order: Discovery → Phase 1 → Phase 2 → Phase 3
  ✅ DO run QA on the PowerPoint before declaring Phase 3 complete

═══════════════════════════════════════════════════════════════════════════════
START COMMAND — PASTE THIS INTO CLAUDE CODE TO BEGIN
═══════════════════════════════════════════════════════════════════════════════

Read the file at:
D:\PycharmProjects\floor_management_system-D3\MASTER_DOCUMENTATION_PROMPT.md

Follow every instruction in that file, in order, starting with the Global
Discovery phase. Do not ask clarifying questions — use [NEEDS VERIFICATION]
for anything you cannot determine from the code. Begin now.

═══════════════════════════════════════════════════════════════════════════════
```
