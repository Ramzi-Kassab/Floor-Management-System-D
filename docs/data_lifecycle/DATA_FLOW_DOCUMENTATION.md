# Data Flow Documentation
## Floor Management System - Complete Data Ecosystem

**Version:** 1.0
**Last Updated:** December 2024
**Author:** System Architecture Team

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Data Entry Points Matrix](#2-data-entry-points-matrix)
3. [Core Data Flow Chains](#3-core-data-flow-chains)
4. [Cross-System Integration Flows](#4-cross-system-integration-flows)
5. [Real-Time vs Batch Data Patterns](#5-real-time-vs-batch-data-patterns)
6. [Data Transformation Rules](#6-data-transformation-rules)

---

## 1. Executive Summary

The ARDT Floor Management System processes data across **15 integrated apps** with **56+ models** serving distinct but interconnected business functions. This document maps the complete data journey from entry to consumption.

### Key Statistics
| Metric | Count |
|--------|-------|
| Total Apps | 15 |
| Total Models | 56+ |
| Data Entry Points | 45+ |
| Workflow Stages | 8 per entity (avg) |
| Integration Points | 12 |

---

## 2. Data Entry Points Matrix

### 2.1 Primary Data Entry Points

| Entry Point | Role | Location | Device | Timing | Connectivity |
|-------------|------|----------|--------|--------|--------------|
| **Drill Bit Registration** | Warehouse Clerk | Warehouse | Desktop/Scanner | On Receipt | Online Required |
| **Work Order Creation** | Production Planner | Office | Desktop | Business Hours | Online Required |
| **Field Inspection** | Field Technician | Rig Site | Tablet/Mobile | Real-time | Offline-capable |
| **Customer Order** | Sales Rep | Office/Remote | Desktop/Mobile | Business Hours | Online Required |
| **Time Entry** | Shop Floor Tech | Workshop | Tablet/Kiosk | End of Shift | Online Preferred |
| **Quality Inspection** | QC Inspector | QC Lab | Desktop/Tablet | During Process | Online Required |
| **NCR Creation** | QC Inspector/Anyone | Any | Any Device | Immediate | Online Required |
| **Service Request** | Customer/Sales | Customer Site | Mobile/Portal | Ad-hoc | Online Required |
| **Inventory Transaction** | Warehouse Clerk | Warehouse | Scanner/Desktop | Real-time | Online Required |
| **Training Record** | HR/Supervisor | Office | Desktop | As Completed | Online Required |
| **Equipment Calibration** | Maintenance Tech | Shop Floor | Tablet | Scheduled | Online Preferred |
| **HOC Report** | Any Employee | Any Location | Mobile | Immediate | Offline-capable |

### 2.2 Automated Data Entry Points

| Entry Point | Trigger | Source | Frequency |
|-------------|---------|--------|-----------|
| **Status Transition Log** | Work Order status change | System | Per Event |
| **Audit Trail** | Any data modification | System | Per Event |
| **Cost Calculations** | Material/Labor entry | System | Real-time |
| **Inventory Levels** | Transaction completion | System | Real-time |
| **Notification Generation** | Workflow milestones | System | Per Event |
| **Report Generation** | Scheduled/On-demand | System | Configurable |

### 2.3 External Data Entry Points

| Entry Point | Source | Protocol | Frequency |
|-------------|--------|----------|-----------|
| **Customer Master** | ERP System (SAP/Oracle) | REST API | Daily Sync |
| **Purchase Orders** | ERP System | REST API | Real-time |
| **Sales Orders** | Customer Portal | Web Form | On Demand |
| **Barcode Scans** | Mobile Scanner | Local BLE | Real-time |
| **GPS Coordinates** | Mobile Device | Device API | Per Scan |

---

## 3. Core Data Flow Chains

### 3.1 Drill Bit Complete Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DRILL BIT LIFECYCLE FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

STAGE 1: ACQUISITION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Purchase Order] ──► [Goods Receipt] ──► [DrillBit Created]
     │                     │                    │
     │                     ▼                    ▼
     │              InventoryTransaction   Status: NEW
     │              (type: RECEIPT)        PhysicalStatus: AT_ARDT
     │                                     AccountingStatus: ARDT_OWNED
     │                     │
     └─────────────────────┼──────────────► ScanCode Generated (QR)
                           │
                           ▼
                    QualityControl
                    (type: INCOMING)
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
       [PASSED]                      [FAILED]
            │                             │
            ▼                             ▼
    Status: IN_STOCK              NonConformance Created
                                        │
                                        ▼
                                  [NCR Resolution]

STAGE 2: ALLOCATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Sales Order Created] ──► [Bit Selected] ──► [Reserved]
         │                      │                 │
         ▼                      ▼                 ▼
  SalesOrderLine          DrillBit.status   InventoryReservation
  created                 → ASSIGNED         created
         │                      │
         └──────────────────────┼──────────────► Customer notified
                                │                (Notification)
                                ▼
                          [Dispatch Planning]

STAGE 3: DEPLOYMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Dispatch Created] ──► [Loading] ──► [In Transit] ──► [Delivered]
        │                  │              │               │
        ▼                  ▼              ▼               ▼
   DispatchItem      ScanLog          ScanLog        ScanLog
   created           (CHECK_OUT)      (GPS Track)    (CHECK_IN)
        │                  │              │               │
        ▼                  ▼              ▼               ▼
   DrillBit           Physical        GPS coords      DrillBit
   linked             Status:         recorded        PhysicalStatus:
                      IN_TRANSIT                      AT_CUSTOMER
                                                           │
                                                           ▼
                                                    [Customer Receipt]
                                                    (ServiceSite linked)

STAGE 4: FIELD OPERATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Assigned to Rig] ──► [Drilling Run] ──► [Run Complete] ──► [Inspection]
        │                   │                  │                 │
        ▼                   ▼                  ▼                 ▼
   DrillBit            Performance         Footage           BitEvaluation
   rig (FK)            logs captured       accumulated       created
   well (FK)                │                  │                 │
   Status: IN_FIELD         ▼                  ▼                 ▼
        │              FieldDataEntry     total_footage    IADC grades
        │              recorded           total_hours      recorded
        │                   │                                   │
        │                   ▼                                   ▼
        │              ServiceReport                     Recommendation:
        │              generated                         CONTINUE/REPAIR/SCRAP
        │                                                       │
        └───────────────────────────────────────────────────────┘

STAGE 5: RETURN & EVALUATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Return Initiated] ──► [Transit] ──► [Received at ARDT] ──► [Evaluation]
        │                  │                 │                   │
        ▼                  ▼                 ▼                   ▼
   Dispatch            ScanLog          ScanLog            RepairEvaluation
   return trip         tracking         (CHECK_IN)         created
        │                                    │                   │
        ▼                                    ▼                   ▼
   Status:                             PhysicalStatus:    Damage assessment
   RETURNED                            AT_ARDT            IADC grading
                                            │              Cost estimate
                                            ▼                   │
                                      QualityControl            ▼
                                      (INCOMING)          [Approval Required?]
                                                               │
                                           ┌───────────────────┼───────────────┐
                                           ▼                   ▼               ▼
                                    [< $10K]           [$10K-$50K]      [> $50K]
                                    Auto-approve       Manager          Executive
                                           │           Approval         Approval
                                           └───────────────────┴───────────────┘
                                                               │
                                                               ▼
                                                    RepairEvaluation.status
                                                    → APPROVED

STAGE 6A: REPAIR PATH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Repair Approved] ──► [Work Order] ──► [Production] ──► [QC] ──► [Complete]
        │                  │                │             │           │
        ▼                  ▼                ▼             ▼           ▼
   RepairBOM         WorkOrder          Operations   Inspection   DrillBit
   created           created            executed     performed    Status:
        │            Type: FC_REPAIR         │            │       READY
        │            Status: RELEASED        │            │           │
        ▼                  │                 ▼            ▼           ▼
   RepairBOMLine           ▼           TimeLog       QC Result   Serial number
   (materials)       ProcessRoute      entries       recorded    incremented
        │            assigned              │            │       (revision++)
        ▼                  │               ▼            │           │
   MaterialLot             ▼          WorkOrderCost    │           ▼
   reserved           Operations      updated         │       BitRepairHistory
        │             in sequence          │           │       recorded
        │                  │               │           │           │
        ▼                  ▼               ▼           ▼           ▼
   InventoryTransaction    OperationExecution    ┌────┴───┐   total_repairs++
   (ISSUE)                 per step              │        │   repair cost added
                                            [PASS]   [FAIL]
                                                │        │
                                                │        ▼
                                                │    NCR Created
                                                │    Rework required
                                                │        │
                                                └────────┴──► [Return to stock]

STAGE 6B: SCRAP PATH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Scrap Decision] ──► [Salvage Review] ──► [Disassembly] ──► [Disposal]
        │                  │                   │                │
        ▼                  ▼                   ▼                ▼
   DrillBit          SalvageItem          Parts              SalvageItem
   Status:           created              recovered           Status:
   SCRAPPED               │                   │               SCRAPPED
        │                 ▼                   ▼               or SOLD
        ▼            Salvageable         InventoryItem           │
   AccountingStatus  components          created for            ▼
   WRITTEN_OFF       identified          reusable parts    Final disposition
        │                 │                   │             documented
        ▼                 ▼                   ▼                  │
   Book value        Value               Inventory             ▼
   written off       estimated           updated           [Archive]
```

### 3.2 Customer Order to Delivery Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CUSTOMER ORDER LIFECYCLE FLOW                            │
└─────────────────────────────────────────────────────────────────────────────┘

PHASE 1: ORDER CAPTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Customer Request] ──► [Quote Generated] ──► [Order Confirmed]
        │                     │                     │
        ▼                     ▼                     ▼
   Customer          (Future: Quote           SalesOrder
   lookup/create      module)                 created
        │                     │               Status: DRAFT
        │                     │                     │
        ▼                     │                     ▼
   CustomerContact            │              SalesOrderLine(s)
   associated                 │              created
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
                              ▼
                    [Credit Check] ──► [Terms Verified]
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
          [Approved]                    [On Hold]
               │                             │
               ▼                             ▼
        SalesOrder.status            Task created for
        → CONFIRMED                  Credit team
               │
               ▼
        [Notifications sent]
        - Sales Rep
        - Production Planning
        - Customer (confirmation email)

PHASE 2: ORDER FULFILLMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Order Confirmed] ──► [Production Planning] ──► [Work Orders Created]
        │                     │                        │
        ▼                     ▼                        ▼
   SalesOrder            Each line              WorkOrder per
   Status:               evaluated              line item
   IN_PROGRESS                │                 linked to SO
        │                     ▼                        │
        │              [Stock Check]                   ▼
        │                     │                  SalesOrderLine
        │         ┌───────────┴───────────┐      Status: IN_PRODUCTION
        │         ▼                       ▼            │
        │    [In Stock]             [Not in Stock]    │
        │         │                       │           │
        │         ▼                       ▼           │
        │    Reserve from            Create WO        │
        │    inventory               for production   │
        │         │                       │           │
        │         ▼                       ▼           │
        │    InventoryReservation   WorkOrder        │
        │    created                created          │
        │                                            │
        └────────────────────────────────────────────┘

PHASE 3: PRODUCTION (if required)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Work Order Released] ──► [Production] ──► [QC] ──► [Ready]
        │                      │            │           │
        ▼                      ▼            ▼           ▼
   ProcessRoute          Time/Material  Inspection   SalesOrderLine
   assigned              consumption    results      Status: READY
        │                      │            │           │
        ▼                      ▼            ▼           ▼
   Operations           WorkOrderCost   QC Record   [Packing List
   sequence             accumulated     created      generated]
   defined                                              │
                                                       ▼
                                              All lines ready?
                                                       │
                                          ┌────────────┴────────────┐
                                          ▼                         ▼
                                      [Yes]                      [No]
                                          │                         │
                                          ▼                         ▼
                                    SalesOrder               Partial ship
                                    Status: READY            decision required

PHASE 4: SHIPPING & DELIVERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Dispatch Planned] ──► [Loaded] ──► [In Transit] ──► [Delivered]
        │                 │              │               │
        ▼                 ▼              ▼               ▼
   Dispatch          InventoryTxn    GPS tracking    Proof of
   created           (ISSUE)         (if equipped)   Delivery
        │                 │              │               │
        ▼                 ▼              ▼               ▼
   DispatchItem      Stock levels   Dispatch.status SalesOrder.status
   per SO line       decremented    → IN_TRANSIT    → DELIVERED
        │                                                │
        ▼                                                ▼
   Vehicle                                        [Invoice Generation]
   assigned                                       (Future: Billing module)
        │                                                │
        ▼                                                ▼
   Driver                                          Customer
   assigned                                        notification
```

### 3.3 Field Service Request Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FIELD SERVICE REQUEST LIFECYCLE                           │
└─────────────────────────────────────────────────────────────────────────────┘

INITIATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Service Needed] ──► [Request Created] ──► [Review] ──► [Approval]
        │                   │                 │             │
        ▼                   ▼                 ▼             ▼
   Trigger:           FieldServiceRequest  Operations   Manager/
   - Customer call    Status: DRAFT        review       Customer
   - Scheduled PM     Priority assigned         │       approval
   - Issue detected        │                    ▼             │
        │                  ▼               Status:           ▼
        │             ServiceSite          REVIEWED     Status:
        │             linked                   │        APPROVED
        │                  │                   ▼             │
        └──────────────────┴───────────────────┴─────────────┘

SCHEDULING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Approved] ──► [Technician Selection] ──► [Schedule Confirmed]
     │                  │                        │
     ▼                  ▼                        ▼
 Availability      FieldTechnician          ShiftSchedule
 check             assigned                 created
     │                  │                        │
     ▼                  ▼                        ▼
 Skills match      is_currently_assigned   FSR Status:
 required          → true                  SCHEDULED
     │                  │                        │
     ▼                  ▼                        ▼
 Location          current_location        Notification to:
 proximity         updated                 - Technician
                                          - Customer
                                          - Operations

EXECUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Tech En Route] ──► [Arrive] ──► [Work] ──► [Complete]
       │               │           │            │
       ▼               ▼           ▼            ▼
   Journey        SiteVisit    Service      ServiceReport
   created        created      performed    created
       │               │           │            │
       ▼               ▼           ▼            ▼
   Travel time    Check-in    TimeEntry    Findings
   tracked        ScanLog     recorded     documented
       │               │           │            │
       ▼               ▼           ▼            ▼
   GPS coords     FSR Status: Materials    Photos
   recorded       IN_PROGRESS consumed     captured
                                               │
                                               ▼
                                        FieldDocument
                                        attachments

CLOSURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Work Complete] ──► [Customer Sign-off] ──► [Documentation] ──► [Close]
       │                   │                      │              │
       ▼                   ▼                      ▼              ▼
   ServiceReport      Digital          Report finalized    FSR Status:
   generated          signature        and filed           COMPLETED
       │               captured              │                  │
       ▼                   │                 ▼                  ▼
   Recommendations        ▼            FieldDocument       Metrics
   captured          Approval          saved               updated:
       │             recorded               │               - completed_calls
       │                                    ▼               - average_rating
       ▼                              [Follow-up             - on_time_%
   [Follow-up                          required?]
    needed?]                                │
       │                    ┌───────────────┴───────────────┐
       ├───► [YES] ────────►│    New FSR created           │
       │                    │    (linked to original)       │
       └───► [NO] ─────────►│    Archive and close         │
                            └───────────────────────────────┘
```

### 3.4 Quality Non-Conformance Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    NON-CONFORMANCE (NCR) LIFECYCLE                           │
└─────────────────────────────────────────────────────────────────────────────┘

DETECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Issue Detected] ──► [NCR Created] ──► [Severity Assessment]
       │                  │                    │
       ▼                  ▼                    ▼
   Detection          NCR.status           Severity:
   source:            → OPEN               CRITICAL/MAJOR/MINOR
   - QC Inspection         │                    │
   - Customer complaint    │          ┌────────┴────────┐
   - Internal audit        │          ▼                 ▼
   - Supplier issue        │     [CRITICAL]        [MAJOR/MINOR]
       │                   │          │                 │
       ▼                   ▼          ▼                 ▼
   QualityControl     detected_by  Immediate        Standard
   or Inspection      recorded     containment      process
   linked                          required

INVESTIGATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[NCR Opened] ──► [Investigation] ──► [Root Cause] ──► [Disposition]
       │               │                  │                │
       ▼               ▼                  ▼                ▼
   NCR.status      Team            5-Why or         Decision:
   → INVESTIGATING assigned        Fishbone         USE_AS_IS
       │               │           analysis         REWORK
       │               ▼                │           REPAIR
       │          investigated_by      ▼           SCRAP
       │          recorded         root_cause       RETURN_SUPPLIER
       │               │           documented       DEVIATE
       │               ▼                │                │
       │          AuditTrail           ▼                ▼
       │          entries          [Contributing   disposition_by
       │          logged           factors]        disposition_date
       │                                                │
       │                                                ▼
       │                                         NCR.status
       │                                         → PENDING_DISPOSITION
       │
       └──────────────► [Containment Actions]
                              │
                              ▼
                        Quarantine affected items
                        Customer notification (if shipped)
                        Production hold (if systematic)

CORRECTIVE ACTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Disposition Decided] ──► [Action Plan] ──► [Execute] ──► [Verify]
         │                      │              │            │
         ▼                      ▼              ▼            ▼
    Based on               Corrective      Work Orders   Verification
    disposition:           actions         created       inspection
         │                 defined              │            │
         ├─► REWORK ──────────────────► WorkOrder          │
         │                              (REWORK type)      │
         ├─► REPAIR ──────────────────► WorkOrder          │
         │                              (REPAIR type)      │
         ├─► SCRAP ───────────────────► DrillBit.status    │
         │                              → SCRAPPED         │
         │                              SalvageItem        │
         │                                                 │
         └─► DEVIATE ─────────────────► Engineering       │
                                        approval          │
                                        documented        │
                                             │            │
                                             └────────────┤
                                                          ▼
                                                    NCR.status
                                                    → IN_REWORK

CLOSURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Actions Complete] ──► [Verification] ──► [Effectiveness] ──► [Close]
         │                  │                  │               │
         ▼                  ▼                  ▼               ▼
    All rework         Verification       Monitor for     NCR.status
    complete           inspection         recurrence      → CLOSED
         │             passed                 │               │
         ▼                  │                 ▼               ▼
    QualityControl         ▼            30/60/90 day     closed_by
    (FINAL)           NCR.status        effectiveness    closed_at
    passed            → PENDING_        check            closure_notes
                      VERIFICATION           │
                           │                 ▼
                           │          ComplianceReport
                           │          includes NCR
                           │          statistics
                           │                 │
                           └─────────────────┘
                                    │
                                    ▼
                           [Lessons Learned]
                           - Process improvement
                           - Training updates
                           - Procedure revision
                           (DocumentControl update)
```

### 3.5 Employee Training & Certification Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  TRAINING & CERTIFICATION LIFECYCLE                          │
└─────────────────────────────────────────────────────────────────────────────┘

TRAINING IDENTIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Need Identified] ──► [Training Scheduled] ──► [Enrollment]
        │                    │                      │
        ▼                    ▼                      ▼
   Source:              TrainingRecord         Employee
   - New hire           created                linked
   - Skill gap          Status: SCHEDULED          │
   - Cert expiring           │                     ▼
   - Job requirement         ▼                SkillMatrix
   - Compliance         scheduled_date        gap identified
        │               training_type
        │               provider
        │                    │
        └────────────────────┴──────────────► Notification
                                              to Employee
                                              and Manager

TRAINING DELIVERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Training Start] ──► [In Progress] ──► [Assessment] ──► [Complete]
        │                 │                 │              │
        ▼                 ▼                 ▼              ▼
   TrainingRecord    Attendance       Test/Exam      TrainingRecord
   Status:           tracked          conducted      Status:
   IN_PROGRESS            │                │         COMPLETED or FAILED
        │                 ▼                ▼              │
        │            TimeEntry        score          completion_date
        │            (TRAINING)       recorded       hours_completed
        │                                                │
        │                           ┌────────────────────┤
        │                           ▼                    ▼
        │                      [PASSED]            [FAILED]
        │                           │                    │
        │                           ▼                    ▼
        │                      certificate_         Reschedule
        │                      number assigned      training
        │                           │
        └───────────────────────────┘

CERTIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Training Passed] ──► [Certification Created] ──► [Active]
        │                      │                     │
        ▼                      ▼                     ▼
   If certification       Certification         Employee
   required:              created               qualifications
        │                 Status: CURRENT       updated
        ▼                      │                     │
   SkillMatrix                 ▼                     ▼
   updated:               issue_date            Work eligibility:
   - certified: true      expiry_date           - can_perform_inspections
   - certification_       cert_number           - can_perform_repairs
     expiry                    │                - certification_level
        │                      ▼
        │                 [Monitoring]
        │                      │
        │         ┌────────────┴────────────┐
        │         ▼                         ▼
        │    [60 days before           [Expired]
        │     expiry]                       │
        │         │                         ▼
        │         ▼                    Certification
        │    Notification              Status: EXPIRED
        │    sent for renewal               │
        │         │                         ▼
        │         ▼                    Employee
        │    TrainingRecord            privileges
        │    scheduled for             revoked
        │    renewal                        │
        │         │                         ▼
        └─────────┴────────────────────────►ComplianceReport
                                           includes
                                           certification
                                           status
```

---

## 4. Cross-System Integration Flows

### 4.1 ERP Integration Data Flow

```
                    ┌─────────────────────────────────────────┐
                    │           EXTERNAL ERP SYSTEMS          │
                    │         (SAP / Oracle / NetSuite)       │
                    └─────────────────────────────────────────┘
                                       │
                                       │ REST API / Batch Files
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          ERP INTEGRATION LAYER                                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │   ERPMapping    │    │   ERPSyncLog    │    │  Transformation │          │
│  │                 │    │                 │    │     Engine      │          │
│  │ entity_type     │    │ direction       │    │                 │          │
│  │ ardt_id         │    │ status          │    │ Field mapping   │          │
│  │ erp_system      │    │ request_payload │    │ Value transform │          │
│  │ erp_id          │    │ response_payload│    │ Validation      │          │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘          │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│    CUSTOMERS    │         │   WORK ORDERS   │         │  SALES ORDERS   │
│                 │         │                 │         │                 │
│ Sync: Bidirect  │         │ Sync: Outbound  │         │ Sync: Bidirect  │
│ Freq: Real-time │         │ Freq: Real-time │         │ Freq: Real-time │
│                 │         │                 │         │                 │
│ ARDT → ERP:     │         │ ARDT → ERP:     │         │ ERP → ARDT:     │
│ - New customers │         │ - WO created    │         │ - SO created    │
│ - Updates       │         │ - Status change │         │ - Pricing       │
│                 │         │ - Completion    │         │                 │
│ ERP → ARDT:     │         │ - Cost summary  │         │ ARDT → ERP:     │
│ - Master data   │         │                 │         │ - Fulfillment   │
│ - Credit info   │         │                 │         │ - Shipping      │
└─────────────────┘         └─────────────────┘         └─────────────────┘
         │                             │                             │
         └─────────────────────────────┴─────────────────────────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │   ARDT FMS CORE     │
                            │                     │
                            │ - Customer          │
                            │ - WorkOrder         │
                            │ - SalesOrder        │
                            │ - Inventory         │
                            └─────────────────────┘
```

### 4.2 Notification Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NOTIFICATION DISPATCH FLOW                           │
└─────────────────────────────────────────────────────────────────────────────┘

[Business Event] ──► [Notification Engine] ──► [Template Selection] ──► [Dispatch]
        │                    │                        │                    │
        ▼                    ▼                        ▼                    ▼
   Event Types:        NotificationTemplate     Personalization      Channels:
   - Status change     matched by:              - Recipient name     - In-app
   - Approval needed   - entity_type            - Entity details     - Email
   - Due date          - action                 - Links              - SMS
   - Assignment        - priority               - Context            - Push
        │                    │                        │                    │
        ▼                    ▼                        ▼                    ▼
   Triggers:            Template                Notification          Delivery:
   - WorkOrder.save()   content                 record created       - Immediate
   - FSR.save()         variables               in database          - Batched
   - Leave.save()       defined                      │               - Scheduled
   - NCR.save()              │                       ▼
        │                    │                  NotificationLog
        │                    │                  tracks delivery
        │                    │                  status
        │                    │                       │
        └────────────────────┴───────────────────────┘

Key Notification Triggers:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
| Event                          | Recipients              | Priority |
|--------------------------------|-------------------------|----------|
| Work Order Created             | Assigned technician     | NORMAL   |
| Work Order Ready for QC        | QC Inspector            | HIGH     |
| NCR Created (Critical)         | Quality Manager         | URGENT   |
| Leave Request Submitted        | Employee's Manager      | NORMAL   |
| Certification Expiring         | Employee, HR            | HIGH     |
| Field Service Scheduled        | Technician, Customer    | HIGH     |
| Approval Required              | Approver                | HIGH     |
| Calibration Due                | Maintenance team        | NORMAL   |
| Inventory Low Stock            | Warehouse manager       | HIGH     |
| Customer Order Shipped         | Customer, Sales rep     | NORMAL   |
```

---

## 5. Real-Time vs Batch Data Patterns

### 5.1 Real-Time Data Entry

| Data Type | Trigger | Latency | Validation |
|-----------|---------|---------|------------|
| Barcode Scan | User action | < 1 sec | Immediate |
| Status Update | User action | < 2 sec | Immediate |
| Time Punch | Clock in/out | < 1 sec | Immediate |
| Inspection Result | Form submit | < 3 sec | Full |
| NCR Creation | Form submit | < 3 sec | Full |
| Approval Action | Button click | < 2 sec | Authority check |

### 5.2 Batch Data Processing

| Process | Schedule | Data Volume | Duration |
|---------|----------|-------------|----------|
| ERP Customer Sync | Daily 2 AM | ~1000 records | 15 min |
| Report Generation | Daily 6 AM | Variable | 30 min |
| Certification Expiry Check | Daily 7 AM | All certs | 5 min |
| Inventory Reorder Check | Daily 8 AM | All items | 10 min |
| Compliance Metrics Calc | Weekly Sun | All data | 2 hours |
| Payroll Processing | Bi-weekly | All employees | 1 hour |

### 5.3 Event-Driven Data Updates

| Event | Cascade Updates |
|-------|-----------------|
| Work Order Completed | DrillBit stats, Inventory levels, Customer history, Cost rollup |
| Sales Order Shipped | Inventory deduction, Customer delivery history, Revenue recognition |
| NCR Closed | Quality metrics, Supplier rating, Cost tracking |
| Employee Terminated | Access revoked, Tasks reassigned, Reports archived |

---

## 6. Data Transformation Rules

### 6.1 Calculated Fields

| Entity | Field | Calculation |
|--------|-------|-------------|
| DrillBit | current_book_value | original_cost - total_repair_cost - depreciation |
| WorkOrderCost | variance_percent | (actual - estimated) / estimated * 100 |
| FieldTechnician | on_time_percentage | on_time_completions / total_completions * 100 |
| InventoryStock | quantity_available | quantity_on_hand - quantity_reserved |
| Employee | annual_leave_balance | annual_leave_days - used_leave_days |
| SalesOrder | total_amount | subtotal + tax_amount - discount |

### 6.2 Status Derivation Rules

| Entity | Derived Status | Based On |
|--------|---------------|----------|
| DrillBit.is_available | True | status=IN_STOCK AND physical_status=AT_ARDT |
| WorkOrder.is_overdue | True | due_date < today AND status not in [COMPLETED, CANCELLED] |
| Certification.is_valid | True | status=CURRENT AND expiry_date > today |
| FieldTechnician.can_be_assigned | True | employment_status=ACTIVE AND is_currently_assigned=False |

### 6.3 Aggregation Rules

| Target | Source | Aggregation |
|--------|--------|-------------|
| WorkOrderCost.total_actual_cost | WorkOrderMaterial + WorkOrderTimeLog | SUM of costs |
| DrillBit.total_repairs | BitRepairHistory | COUNT of records |
| Customer.total_orders | SalesOrder | COUNT where customer_id matches |
| ServiceSite.total_service_visits | FieldServiceRequest | COUNT where site_id matches |
| QualityMetric.actual_value | QualityControl | Calculated based on metric type |

---

## Appendix A: Data Flow Symbols Legend

```
━━━━━━━━ Direct data flow
─ ─ ─ ─  Conditional flow
──►      Direction indicator
[Box]    Process/Action
Model    Database entity
Status:  State change
(Note)   Annotation
┌──┐
│  │     System boundary
└──┘
```

---

**Document Control:**
- Created: December 2024
- Review Cycle: Quarterly
- Owner: System Architecture Team
- Classification: Internal Use
