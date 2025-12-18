# User Journey Maps
## Floor Management System - Role-Based Data Interactions

**Version:** 1.0
**Last Updated:** December 2024

---

## Table of Contents
1. [Role Overview](#1-role-overview)
2. [Field Technician Journey](#2-field-technician-journey)
3. [QC Inspector Journey](#3-qc-inspector-journey)
4. [Warehouse Clerk Journey](#4-warehouse-clerk-journey)
5. [Production Planner Journey](#5-production-planner-journey)
6. [Shop Floor Technician Journey](#6-shop-floor-technician-journey)
7. [Sales Representative Journey](#7-sales-representative-journey)
8. [Operations Manager Journey](#8-operations-manager-journey)
9. [HR Administrator Journey](#9-hr-administrator-journey)
10. [System Administrator Journey](#10-system-administrator-journey)

---

## 1. Role Overview

### 1.1 Role Hierarchy

```
                        ┌─────────────────┐
                        │  Executive      │
                        │  Management     │
                        └────────┬────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
      ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
      │  Operations   │  │    Quality    │  │     Sales     │
      │   Manager     │  │   Manager     │  │    Manager    │
      └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
              │                  │                  │
    ┌─────────┼─────────┐       │          ┌───────┴───────┐
    ▼         ▼         ▼       ▼          ▼               ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐    ┌───────┐
│Prod.  │ │Ware-  │ │Field  │ │  QC   │ │ Sales │    │Account│
│Planner│ │house  │ │ Tech  │ │Inspec.│ │  Rep  │    │Manager│
└───────┘ └───────┘ └───────┘ └───────┘ └───────┘    └───────┘
    │         │         │         │         │            │
    ▼         ▼         ▼         ▼         ▼            ▼
┌───────┐ ┌───────┐
│Shop   │ │Clerk  │
│Floor  │ │       │
│Tech   │ │       │
└───────┘ └───────┘
```

### 1.2 Primary Data Touchpoints by Role

| Role | Primary Creates | Primary Reads | Primary Updates |
|------|-----------------|---------------|-----------------|
| Field Technician | Inspections, Service Reports, Time Entries | Work Orders, Drill Bits, Service Sites | Field data, Status updates |
| QC Inspector | Quality Controls, NCRs, Inspections | Work Orders, Drill Bits, Materials | QC results, Dispositions |
| Warehouse Clerk | Inventory Transactions, Receipts | Inventory, Work Orders, Dispatches | Stock levels, Locations |
| Production Planner | Work Orders, Schedules | All production data | WO assignments, Priorities |
| Shop Floor Tech | Time Logs, Material Consumption | Work Orders, Process Routes | Operation status |
| Sales Rep | Sales Orders, Customer Records | Customers, Products, Orders | Order status, Customer info |
| Operations Manager | Approvals, Reports | All operational data | Escalations, Decisions |
| HR Admin | Employee Records, Training | All HR data | Employee status, Compliance |
| System Admin | System Config, User Accounts | All system data | Any data (emergency) |

---

## 2. Field Technician Journey

### 2.1 Persona
**Name:** Ahmed Al-Farsi
**Role:** Senior Field Technician
**Location:** Based in Houston, travels to Gulf rigs
**Device:** Rugged tablet with FMS mobile app
**Skills:** PDC bit specialist, 12 years experience

### 2.2 Day-in-Life Scenario

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FIELD TECHNICIAN: DAY IN THE LIFE                         │
└─────────────────────────────────────────────────────────────────────────────┘

05:00 - START OF DAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Login to FMS Mobile] ──► [Check Today's Schedule] ──► [Review Assignments]
         │                         │                         │
         ▼                         ▼                         ▼
    Touch ID           ShiftSchedule              FieldServiceRequest
    authentication     for today                  list (Status: SCHEDULED)
         │                         │                         │
         ▼                         ▼                         ▼
    READ: User         READ: My shifts            READ: FSR details
    notifications      and sites                  - Customer contact
    (5 unread)                                    - Site directions
                                                  - Equipment needed

    📱 Actions:
    - Mark notifications as read
    - Confirm shift schedule
    - Download site maps (offline mode)

06:00 - TRAVEL TO SITE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Start Journey] ──► [GPS Tracking Active] ──► [Arrive at Site]
        │                    │                       │
        ▼                    ▼                       ▼
   Journey.status       Location data           ScanLog created
   → IN_PROGRESS        recorded                (CHECK_IN)
        │               periodically                 │
        ▼                    │                       ▼
   CREATE: Journey           ▼                  FSR.status
   record                GPS coords              → IN_PROGRESS
                         captured

    📱 Actions:
    - Tap "Start Journey"
    - App tracks GPS automatically
    - Scan site QR code on arrival

07:30 - ON-SITE INSPECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Scan Drill Bit QR] ──► [Load Bit History] ──► [Perform Inspection]
         │                     │                      │
         ▼                     ▼                      ▼
    ScanLog              DrillBit              BitEvaluation
    created              full record           created
    (IDENTIFY)           displayed             (INCOMING type)
         │                     │                      │
         ▼                     ▼                      ▼
    READ: Bit            READ: History          CREATE: Evaluation
    serial number        - Total footage        - Condition grades
    validation           - Repair count         - IADC codes
                         - Last inspection      - Photos captured
                         - Customer info        - Recommendations

    📱 Actions:
    - Scan bit serial barcode
    - View historical performance data
    - Fill IADC grading form
    - Take photos (auto-attached)
    - Record measurements
    - Voice-to-text notes

    ⚠️ Pain Points:
    - Slow loading on 3G connection
    - Photo upload delays
    - IADC code dropdown too small on mobile

08:30 - DOCUMENT FINDINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Complete Evaluation] ──► [Generate Report] ──► [Customer Review]
         │                      │                     │
         ▼                      ▼                     ▼
    BitEvaluation         ServiceReport          Customer
    .status               created               signature
    → COMPLETED           auto-generated        captured
         │                      │                     │
         ▼                      ▼                     ▼
    Recommendation:       CREATE: Report        FieldDocument
    REPAIR               - Findings             created
    (Cost: $15,000)      - Recommendation      (signature image)
                         - Photos embedded

    📱 Actions:
    - Submit evaluation form
    - Review auto-generated report
    - Capture customer signature on screen
    - Email report copy to customer

10:00 - TIME & MATERIAL TRACKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Log Work Time] ──► [Record Materials Used] ──► [Update FSR]
        │                    │                       │
        ▼                    ▼                       ▼
   TimeEntry             MaterialUsed           FSR Progress
   created               (if applicable)        updated
        │                    │                       │
        ▼                    ▼                       ▼
   CREATE:               CREATE:               UPDATE:
   - Start/end time      - Item code           - Work performed
   - Work type           - Quantity            - Completion %
   - Linked to FSR       - From truck stock    - Next steps

    📱 Actions:
    - Tap "Log Time" → auto-fills start from check-in
    - Scan materials used from truck inventory
    - Update work completion percentage

12:00 - MIDDAY: SECOND SITE VISIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Travel to Next Site] ──► [Emergency Call] ──► [Reprioritize]
         │                      │                    │
         ▼                      ▼                    ▼
    Journey #2             Notification          FSR Queue
    started                (URGENT)              re-sorted
         │                      │                    │
         ▼                      ▼                    ▼
    Original FSR           READ: New            Original FSR
    put on hold            urgent request       → ON_HOLD
                                                New FSR
                                                → IN_PROGRESS

    📱 Actions:
    - Receive push notification
    - Accept/decline urgent request
    - Contact dispatcher if conflict
    - System auto-updates schedule

14:00 - URGENT SERVICE CALL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Arrive Emergency Site] ──► [Assess Issue] ──► [Perform Repair]
          │                       │                   │
          ▼                       ▼                   ▼
     ScanLog                 Problem             On-site
     (CHECK_IN)              documented          repair
          │                       │              performed
          ▼                       ▼                   │
     Rig operational         FieldIncident           ▼
     disruption noted        created             Bit Status
                             (if safety issue)   restored

    📱 Actions:
    - Quick check-in scan
    - Document issue with photos
    - Access repair procedures (offline cached)
    - Complete emergency repair
    - Document work performed

16:00 - END OF DAY REPORTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Complete All FSRs] ──► [Submit Time] ──► [Sync Data] ──► [Log Off]
         │                   │                │             │
         ▼                   ▼                ▼             ▼
    All FSRs            TimeEntry        Offline data   Session
    Status:             submitted        uploaded       ended
    COMPLETED           for approval          │             │
         │                   │                ▼             ▼
         ▼                   ▼           Supervisor    Device
    ServiceReports      Daily hours      notified     secured
    generated           calculated

    📱 Actions:
    - Review all FSRs from today
    - Submit final time entries
    - Force sync if on WiFi
    - Check tomorrow's schedule
```

### 2.3 Data Created by Field Technician (Daily Average)

| Data Type | Average Count | Typical Fields |
|-----------|---------------|----------------|
| ScanLog | 8-12 | code, purpose, location, GPS |
| TimeEntry | 2-3 | hours, work_type, linked FSR |
| BitEvaluation | 1-2 | IADC grades, photos, recommendation |
| ServiceReport | 1-2 | findings, recommendations |
| FieldDocument | 3-5 | photos, signatures |
| Journey | 2-3 | departure, arrival, mileage |

### 2.4 Pain Points & Improvement Opportunities

| Pain Point | Current Impact | Improvement |
|------------|---------------|-------------|
| Slow photo upload | 5 min delay per site | Background upload queue |
| Offline form complexity | Data loss risk | Better offline validation |
| IADC code entry | Error-prone | Visual picker with images |
| Report generation | Manual formatting | One-click auto-generate |
| Schedule changes | Missed notifications | SMS fallback |

---

## 3. QC Inspector Journey

### 3.1 Persona
**Name:** Sarah Chen
**Role:** Senior QC Inspector
**Location:** ARDT Workshop - Houston
**Device:** Desktop + tablet in QC lab
**Certifications:** API Q1, ISO 9001 Lead Auditor

### 3.2 Day-in-Life Scenario

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      QC INSPECTOR: DAY IN THE LIFE                           │
└─────────────────────────────────────────────────────────────────────────────┘

07:00 - SHIFT START
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Clock In] ──► [Check QC Queue] ──► [Review Priority Items]
      │              │                      │
      ▼              ▼                      ▼
 TimeEntry      WorkOrder list         High-priority
 created        Status: QC_PENDING     items flagged
      │              │                      │
      ▼              ▼                      ▼
 Shift          READ: 12 WOs           Urgent customer
 started        awaiting QC            orders identified

    🖥️ Actions:
    - Badge scan clock-in
    - View QC dashboard
    - Sort by priority/due date
    - Note: 3 URGENT items for Major Oil Co.

07:15 - INCOMING INSPECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Select Incoming WO] ──► [Retrieve Bit] ──► [Inspection Setup]
         │                     │                    │
         ▼                     ▼                    ▼
    WorkOrder              ScanLog              Inspection
    loaded                 (VERIFY)             created
         │                     │                Type: INCOMING
         ▼                     ▼                    │
    READ:                  Confirm               CREATE:
    - WO details           bit matches          - inspection_number
    - Customer specs       work order           - scheduled for now
    - Previous QC notes                         - linked to WO

    🖥️ Actions:
    - Click WO from queue
    - Scan bit barcode to verify
    - System creates inspection record
    - Pull up customer specification document

07:30 - PERFORM INSPECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Visual Inspection] ──► [Dimensional Check] ──► [Document Results]
         │                     │                      │
         ▼                     ▼                      ▼
    Photos               Measurements           QualityControl
    captured             recorded               record updated
         │                     │                      │
         ▼                     ▼                      ▼
    FieldDocument        Digital caliper       Result: PASS/FAIL
    attached             data imported         documented
                         (if equipped)

    🖥️ Actions:
    - Use tablet camera for magnified photos
    - Enter measurements (auto-checks against spec)
    - System highlights out-of-tolerance values in RED
    - Record observations and defects found

08:00 - INSPECTION RESULT: PASS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Mark as Passed] ──► [Update Work Order] ──► [Move to Next]
        │                   │                     │
        ▼                   ▼                     ▼
   Inspection          WorkOrder.status      QC Dashboard
   Status: PASSED      → QC_PASSED           refreshed
        │                   │                     │
        ▼                   ▼                     ▼
   QC Certificate      DrillBit.status       Next item
   generated           → READY               auto-loaded
   (if required)

    🖥️ Actions:
    - Click "Pass" with digital signature
    - System updates all linked records
    - Certificate auto-generated for customer
    - Notification sent to warehouse for dispatch

08:30 - INSPECTION RESULT: FAIL → NCR CREATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Identify Non-Conformance] ──► [Create NCR] ──► [Initiate Containment]
            │                       │                   │
            ▼                       ▼                   ▼
       Defect details           NCR created        Affected items
       documented               NCR Number         quarantined
            │                   auto-assigned           │
            ▼                       │                   ▼
       Photos of                   ▼               InventoryTransaction
       defect attached        Severity            (QUARANTINE)
                              assessed:
                              CRITICAL/MAJOR/MINOR

    🖥️ Actions:
    - Document specific defect
    - System suggests NCR based on defect type
    - Select severity level
    - Identify potential batch impact
    - Initiate containment if systematic issue

    CREATE: NCR Record
    - ncr_number: NCR-2024-0156
    - severity: MAJOR
    - detected_stage: IN_PROCESS
    - description: "Thread pitch 0.005" below min spec"
    - immediate_action: "Quarantine all bits from same lot"

09:00 - NCR INVESTIGATION SUPPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Review NCR Details] ──► [Gather Evidence] ──► [Contribute Findings]
         │                      │                     │
         ▼                      ▼                     ▼
    NCR record              Related data         Investigation
    accessed                collected            notes added
         │                      │                     │
         ▼                      ▼                     ▼
    READ:                  READ:                UPDATE: NCR
    - Initial report       - Material lot       - Contributing factors
    - Defect photos        - Machine history    - Technical analysis
                           - Operator logs      - Recommended disposition

    🖥️ Actions:
    - Access NCR investigation workspace
    - Pull related production data
    - Review material certifications
    - Add technical findings
    - Suggest disposition (REWORK/SCRAP/USE_AS_IS)

10:00 - IN-PROCESS INSPECTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Visit Shop Floor] ──► [In-Process Checks] ──► [Document Results]
         │                     │                     │
         ▼                     ▼                     ▼
    Tablet mode           Random sample        OperationExecution
    activated             inspection           QC fields updated
         │                     │                     │
         ▼                     ▼                     ▼
    Mobile QC             Measurements         qc_performed: True
    interface             taken                qc_passed: True/False
                          in-situ              qc_notes: entered

    📱 Actions:
    - Walk shop floor with tablet
    - Verify operators following procedures
    - Spot-check measurements
    - Sign off operation steps requiring QC

12:00 - LUNCH BREAK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    (System tracks idle time for metrics)

13:00 - FINAL INSPECTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Final QC Queue] ──► [Comprehensive Check] ──► [Certification]
        │                    │                      │
        ▼                    ▼                      ▼
   WorkOrders           Full inspection        QC Certificate
   Status:              checklist              generated
   QC_PENDING           completed                   │
        │                    │                      ▼
        ▼                    ▼                 Customer
   Priority by          InspectionChecklist    documentation
   ship date            items verified         package complete

    🖥️ Actions:
    - Process final inspections by ship date
    - Complete full checklist per customer spec
    - Generate QC certificate with photos
    - Attach to customer documentation package

15:00 - CALIBRATION CHECKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Check Calibration Due] ──► [Verify Equipment] ──► [Record Results]
          │                        │                     │
          ▼                        ▼                     ▼
     Equipment              Calibration            EquipmentCalibration
     list                   performed              record created
     due today                   │                      │
          │                      ▼                      ▼
          ▼                 Passed?              Certificate
     READ:                  Y/N                  uploaded
     - 3 items due

    🖥️ Actions:
    - Review calibration dashboard
    - Perform or verify calibrations
    - Upload calibration certificates
    - Schedule external calibrations if needed

16:00 - END OF DAY REPORTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Review Day's Work] ──► [Update Metrics] ──► [Handoff]
         │                    │                  │
         ▼                    ▼                  ▼
    Daily summary        QualityMetric      Shift notes
    generated            calculations       for next shift
         │               auto-updated            │
         ▼                    │                  ▼
    Inspections:             ▼              Comment
    - Completed: 15     First Pass         created on
    - Passed: 13        Yield: 86.7%       open items
    - Failed: 2

    🖥️ Actions:
    - Review daily inspection summary
    - Add notes for open items
    - Verify all documentation complete
    - Clock out
```

### 3.3 Data Created by QC Inspector (Daily Average)

| Data Type | Average Count | Key Fields |
|-----------|---------------|------------|
| QualityControl | 15-20 | inspection_type, result, findings |
| NCR | 1-3 | severity, description, photos |
| Inspection | 15-20 | type, status, checklist completion |
| EquipmentCalibration | 1-2 | results, certificate |
| Comment | 5-10 | handoff notes, NCR updates |
| FieldDocument | 10-15 | photos, certificates |

### 3.4 Pain Points & Improvement Opportunities

| Pain Point | Current Impact | Improvement |
|------------|---------------|-------------|
| Spec document lookup | 3-5 min per item | Link specs to design record |
| NCR duplicate check | Manual search | Auto-suggest similar NCRs |
| Calibration certificate upload | Manual file naming | Auto-extract from PDF |
| Checklist completion | Manual checkboxes | Smart defaults |
| Cross-shift handoff | Email/verbal | In-app handoff module |

---

## 4. Warehouse Clerk Journey

### 4.1 Persona
**Name:** Carlos Rodriguez
**Role:** Senior Warehouse Clerk
**Location:** Houston Distribution Center
**Device:** Desktop + Handheld scanner
**Shift:** 6 AM - 2 PM

### 4.2 Day-in-Life Scenario

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     WAREHOUSE CLERK: DAY IN THE LIFE                         │
└─────────────────────────────────────────────────────────────────────────────┘

06:00 - SHIFT START
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Clock In] ──► [Check Receiving Schedule] ──► [Review Low Stock Alerts]
      │                  │                           │
      ▼                  ▼                           ▼
 TimeEntry          Expected              InventoryItem
 created            deliveries            reorder alerts
                    today: 3                    │
                         │                      ▼
                         ▼               Items below
                    PurchaseOrder        reorder_point: 8
                    receipts due

    📱 Actions:
    - Badge scan login
    - Check dock schedule
    - Review reorder report
    - Prepare receiving area

06:30 - RECEIVING: GOODS ARRIVAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Truck Arrives] ──► [Verify Shipment] ──► [Create Receipt]
       │                  │                    │
       ▼                  ▼                    ▼
  Check packing      Compare to          GoodsReceipt
  slip               PO expected         created
       │                  │                    │
       ▼                  ▼                    ▼
  Count items        Discrepancies?      InventoryTransaction
  visually           Flag if any         (RECEIPT) created

    📱 Actions:
    - Match delivery to PO in system
    - Count and verify quantities
    - Note any damage or shortages
    - Scan each item barcode
    - System creates receipt transactions

07:00 - RECEIVING: QUALITY HOLD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Place in QC Hold] ──► [Label Items] ──► [Notify QC]
        │                   │                 │
        ▼                   ▼                 ▼
   Move to QC          Print QC          Notification
   staging area        hold labels       sent to QC
        │                   │                 │
        ▼                   ▼                 ▼
   InventoryStock      ScanCode          Task created
   location:           generated         for QC team
   QC_HOLD_ZONE

    📱 Actions:
    - Move items to QC inspection zone
    - Print and attach QC hold labels
    - System auto-notifies QC team
    - Items not available until QC passed

08:00 - PICK & PACK: WORK ORDER MATERIALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[View Pick List] ──► [Locate Items] ──► [Issue Materials]
        │                 │                   │
        ▼                 ▼                   ▼
   WorkOrder         InventoryStock      InventoryTransaction
   material          locations           (ISSUE) created
   requirements      displayed                │
        │                 │                   ▼
        ▼                 ▼               MaterialConsumption
   InventoryReservation                   linked to WO
   list for today                         lot traceability

    📱 Actions:
    - Open material pick list
    - Scanner guides to locations
    - Scan each item picked
    - System verifies lot/serial
    - Issues material to work order
    - Prints traveler labels

09:00 - INVENTORY TRANSFERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Receive Transfer Request] ──► [Pick from Source] ──► [Move to Destination]
            │                         │                       │
            ▼                         ▼                       ▼
       Transfer                  Scan out               Scan in
       request                   from source            at destination
            │                         │                       │
            ▼                         ▼                       ▼
       InventoryTransaction     Stock reduced          Stock increased
       (TRANSFER) created       at from_location       at to_location

    📱 Actions:
    - View pending transfers
    - Pick items at source location
    - Scan items and destination bin
    - Confirm transfer complete

10:00 - DISPATCH PREPARATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[View Dispatch Schedule] ──► [Stage Items] ──► [Load Vehicle]
          │                        │                │
          ▼                        ▼                ▼
     Dispatch               Items picked       DispatchItem
     orders                 for each           loaded status
     for today              dispatch           updated
          │                        │                │
          ▼                        ▼                ▼
     Priority:              Stage at           ScanLog
     - 2 URGENT             loading dock       (CHECK_OUT)
     - 5 NORMAL

    📱 Actions:
    - Review dispatches by priority
    - Pick items per dispatch
    - Stage at dock with labels
    - Verify vs packing slip
    - Scan items onto truck
    - Driver signature capture

11:00 - RETURNS PROCESSING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Customer Return Arrives] ──► [Inspect Condition] ──► [Process Return]
           │                         │                      │
           ▼                         ▼                      ▼
      Return                    Condition            InventoryTransaction
      authorization             assessment           (RETURN) created
      verified                       │                      │
           │                         ▼                      ▼
           ▼                    Good/Damaged?         DrillBit.status
      RMA number                    │                 → RETURNED
      validated              ┌──────┴──────┐
                             ▼             ▼
                         [GOOD]        [DAMAGED]
                             │             │
                             ▼             ▼
                         Return to     NCR created
                         stock         for inspection

    📱 Actions:
    - Verify RMA authorization
    - Inspect returned items
    - Document condition with photos
    - Route to stock or QC hold
    - Update customer credit if applicable

12:00 - CYCLE COUNTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Cycle Count Assignment] ──► [Physical Count] ──► [Reconcile Variances]
           │                        │                     │
           ▼                        ▼                     ▼
      Today's count            Count items          InventoryTransaction
      locations                in location          (CYCLE_COUNT)
           │                        │               if variance
           ▼                        ▼                     │
      10 bins                  Scanner mode              ▼
      assigned                 for counting         InventoryStock
                                                   quantity_on_hand
                                                   adjusted

    📱 Actions:
    - View assigned count locations
    - Count physical items
    - Enter counts in system
    - Investigate large variances
    - Supervisor approval for adjustments > 5%

13:30 - END OF SHIFT REPORTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Shift Summary] ──► [Handoff Notes] ──► [Clock Out]
       │                  │                 │
       ▼                  ▼                 ▼
  Today's activity    Open items        TimeEntry
  summary:            for next          completed
  - Receipts: 3       shift                 │
  - Issues: 45            │                 ▼
  - Transfers: 8          ▼             Total hours
  - Dispatches: 7     Comment           calculated
                      created

    📱 Actions:
    - Review shift activity summary
    - Note pending items for next shift
    - Document any issues
    - Clock out
```

### 4.3 Data Created by Warehouse Clerk (Daily Average)

| Data Type | Average Count | Key Fields |
|-----------|---------------|------------|
| InventoryTransaction | 60-80 | type, quantity, lot, location |
| ScanLog | 100-150 | purpose, location, validation |
| DispatchItem | 15-25 | item, quantity, loaded status |
| MaterialConsumption | 30-50 | lot, quantity, work_order |
| InventoryStock adjustments | 5-10 | quantity corrections |

---

## 5. Production Planner Journey

*(Abbreviated for length - follows similar pattern)*

### Key Activities:
- Review sales order backlog
- Create and schedule work orders
- Assign resources and capacity
- Monitor production progress
- Handle expedites and priorities
- Coordinate with sales on delivery dates

### Primary Data Interactions:
| Action | Creates | Updates | Reads |
|--------|---------|---------|-------|
| Planning | WorkOrder | - | SalesOrder, DrillBit, Capacity |
| Scheduling | - | WO dates, assignments | Resource availability |
| Monitoring | - | WO status, priorities | All production data |
| Reporting | SavedReport | - | Production metrics |

---

## 6. Shop Floor Technician Journey

*(Abbreviated for length)*

### Key Activities:
- Clock in/out to work orders
- Execute operations per route
- Record material consumption
- Report issues and quality checks
- Complete operation steps

### Primary Data Interactions:
| Action | Creates | Updates | Reads |
|--------|---------|---------|-------|
| Time tracking | WorkOrderTimeLog | - | WorkOrder |
| Operations | OperationExecution | Status | ProcessRoute |
| Materials | MaterialConsumption | InventoryStock | MaterialLot |
| Issues | Comment, HOCReport | - | Procedures |

---

## 7. Sales Representative Journey

*(Abbreviated for length)*

### Key Activities:
- Customer relationship management
- Quote generation
- Order entry and tracking
- Delivery coordination
- Issue resolution

### Primary Data Interactions:
| Action | Creates | Updates | Reads |
|--------|---------|---------|-------|
| Customer mgmt | Customer, Contact | Customer info | All customer data |
| Order entry | SalesOrder, Lines | Order status | Products, Inventory |
| Tracking | Comment | Order updates | Production status |
| Service | FieldServiceRequest | FSR status | Site, Technician |

---

## 8. Operations Manager Journey

*(Abbreviated for length)*

### Key Activities:
- Approve work orders > $10K
- Review NCR dispositions
- Monitor KPIs and dashboards
- Handle escalations
- Resource allocation decisions

### Primary Data Interactions:
| Action | Creates | Updates | Reads |
|--------|---------|---------|-------|
| Approvals | - | Approval fields | WO, NCR, Evaluations |
| Reporting | ComplianceReport | - | All operational data |
| Escalations | Task, Comment | Priority | Issues, Delays |

---

## 9. HR Administrator Journey

*(Abbreviated for length)*

### Key Activities:
- Employee onboarding/offboarding
- Training record management
- Certification tracking
- Leave approval
- Payroll support

### Primary Data Interactions:
| Action | Creates | Updates | Reads |
|--------|---------|---------|-------|
| Onboarding | Employee, Documents | - | Position, Department |
| Training | TrainingRecord | Status | Compliance requirements |
| Certification | Certification | Status, expiry | Employee skills |
| Leave | - | LeaveRequest approval | Balances, Schedule |

---

## 10. System Administrator Journey

*(Abbreviated for length)*

### Key Activities:
- User account management
- Permission configuration
- System monitoring
- Data corrections
- Integration maintenance

### Primary Data Interactions:
| Action | Creates | Updates | Reads |
|--------|---------|---------|-------|
| Users | User, UserRole | Permissions | All user data |
| Config | SystemSetting | Settings | All config |
| Corrections | - | Any data (audited) | AuditLog |
| Monitoring | - | - | All system data |

---

## Appendix: Journey Map Template

For creating additional role journeys:

```
ROLE: [Role Name]
PERSONA: [Name, Experience, Location, Device]

TIME - ACTIVITY NAME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Trigger] ──► [Action 1] ──► [Action 2] ──► [Outcome]
     │             │              │             │
     ▼             ▼              ▼             ▼
 Context       Data Op 1     Data Op 2     Result
                                           recorded

    📱/🖥️ User Actions:
    - Step 1
    - Step 2

    CREATE: [Model.field]
    READ: [Model.field]
    UPDATE: [Model.field]
```

---

**Document Control:**
- Created: December 2024
- Review Cycle: Semi-annually
- Owner: UX Team
- Classification: Internal Use
