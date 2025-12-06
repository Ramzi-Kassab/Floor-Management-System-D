# Demo Guide
## ARDT Floor Management System

---

## Quick Start

### Load Demo Data

```bash
# Load all demo data
python manage.py load_demo_data

# Load specific module only
python manage.py load_demo_data --module=sales
python manage.py load_demo_data --module=supplychain
python manage.py load_demo_data --module=compliance
python manage.py load_demo_data --module=hr
python manage.py load_demo_data --module=workorders

# Clear and reload
python manage.py load_demo_data --clear
```

---

## Demo Credentials

| Username | Password | Role | Access |
|----------|----------|------|--------|
| demo_admin | demo123 | Administrator | Full system access |
| demo_manager | demo123 | Operations Manager | Operations oversight |
| demo_technician | demo123 | Technician | Work order execution |
| demo_qc | demo123 | QC Inspector | Quality inspections |
| demo_planner | demo123 | Planner | Production planning |
| demo_hr | demo123 | HR Coordinator | HR management |
| demo_procurement | demo123 | Procurement | Supply chain |
| demo_field | demo123 | Field Engineer | Field service |

---

## Demo Data Overview

### Work Orders Module

| Data Type | Prefix | Count |
|-----------|--------|-------|
| Drill Bits | DEMO-* | 5 |
| Work Orders | WO-DEMO-* | 5 |

**Sample Drill Bits:**
- DEMO-PDC-001: 8.5" PDC bit
- DEMO-PDC-002: 12.25" PDC bit
- DEMO-TCI-001: 9.875" TCI bit
- DEMO-TCI-002: 17.5" TCI bit
- DEMO-HYBRID-001: 8.5" Hybrid bit

### Sales Module

| Data Type | Prefix | Count |
|-----------|--------|-------|
| Customers | DEMO-* | 5 |
| Service Sites | SITE-DEMO-* | 5 |
| Service Requests | FSR-DEMO-* | 5 |

**Sample Customers:**
- DEMO-ARAMCO: Saudi Aramco (Operator)
- DEMO-ADNOC: ADNOC Drilling (Operator)
- DEMO-PDO: Petroleum Dev Oman (Operator)
- DEMO-SCHLUM: Schlumberger (Contractor)
- DEMO-HALLI: Halliburton (Contractor)

### Supply Chain Module

| Data Type | Prefix | Count |
|-----------|--------|-------|
| Vendors | VND-DEMO-* | 5 |
| Purchase Orders | PO-DEMO-* | 5 |

**Sample Vendors:**
- VND-DEMO-001: PDC Cutters Inc (USA)
- VND-DEMO-002: Bearing Solutions Ltd (Germany)
- VND-DEMO-003: Steel Materials Corp (China)
- VND-DEMO-004: Precision Tools ME (UAE)
- VND-DEMO-005: Advanced Carbide Co (USA)

### Compliance Module

| Data Type | Prefix | Count |
|-----------|--------|-------|
| QC Records | QC-DEMO-* | 5 |
| NCRs | NCR-DEMO-* | 3 |

### HR Module

| Data Type | Count |
|-----------|-------|
| Employees | 7 |
| Leave Requests | 5 |
| Training Programs | 4 |

---

## Demo Scenarios

### Scenario 1: Work Order Lifecycle

**Objective:** Process a drill bit repair from receipt to completion

1. **Login** as `demo_planner`
2. **Create Work Order**
   - Type: REPAIR
   - Drill Bit: DEMO-PDC-001
   - Priority: HIGH
   - Assign to: demo_technician
3. **Release Work Order** - Change status to RELEASED
4. **Login** as `demo_technician`
5. **Start Work** - Change status to IN_PROGRESS
6. **Complete Work** - Change status to QC_PENDING
7. **Login** as `demo_qc`
8. **Perform Inspection** - Create QC record
9. **Pass QC** - Change status to COMPLETED

### Scenario 2: Field Service Request

**Objective:** Handle a customer field service request

1. **Login** as `demo_field`
2. **View Customer** - DEMO-ARAMCO
3. **Create Service Request**
   - Site: Ghawar Field Rig 5
   - Type: DRILL_BIT_INSPECTION
   - Priority: HIGH
4. **Submit Request** - Status changes to SUBMITTED
5. **Login** as `demo_manager`
6. **Review and Approve** - Status changes to APPROVED
7. **Assign Technician** - Create service assignment

### Scenario 3: Procurement Workflow

**Objective:** Create and process a purchase order

1. **Login** as `demo_procurement`
2. **Review Vendors** - Check VND-DEMO-001 status
3. **Create Requisition** - Request PDC cutters
4. **Create Purchase Order**
   - Vendor: PDC Cutters Inc
   - Items: 100x PDC cutters
   - Amount: $45,000
5. **Submit for Approval**
6. **Login** as `demo_manager`
7. **Approve PO**
8. **Record Goods Receipt** when materials arrive

### Scenario 4: Quality Non-Conformance

**Objective:** Handle a quality issue

1. **Login** as `demo_qc`
2. **Create QC Record**
   - Type: RECEIVING
   - Result: FAIL
   - Notes: Material defect found
3. **Create NCR**
   - Type: MATERIAL
   - Severity: HIGH
   - Link to QC record
4. **Login** as `demo_manager`
5. **Review NCR**
6. **Create Corrective Action**
7. **Close NCR** when resolved

### Scenario 5: Employee Management

**Objective:** Process a leave request

1. **Login** as `demo_technician`
2. **View Leave Balance**
3. **Submit Leave Request**
   - Type: ANNUAL
   - Dates: 5 days
   - Reason: Family vacation
4. **Login** as `demo_manager`
5. **Review Request**
6. **Approve Leave**
7. **Login** as `demo_hr`
8. **Verify Leave Records**

---

## Data Relationships

```
Customer (DEMO-ARAMCO)
    └── Service Site (Ghawar Field Rig 5)
            └── Field Service Request (FSR-DEMO-001)
                    └── Service Assignment
                            └── Technician (demo_field)

Vendor (VND-DEMO-001)
    └── Purchase Order (PO-DEMO-001)
            └── PO Items
            └── Goods Receipt
                    └── QC Inspection (QC-DEMO-001)

Work Order (WO-DEMO-001)
    ├── Drill Bit (DEMO-PDC-001)
    ├── Assigned To (demo_technician)
    └── QC Record (QC-DEMO-003)
```

---

## Clean Up Demo Data

To remove all demo data:

```bash
python manage.py load_demo_data --clear
```

This removes:
- All users with `demo_*` prefix
- All records with demo prefixes (DEMO-*, WO-DEMO-*, etc.)

---

## Troubleshooting

### "Module not found" error

Ensure all migrations are applied:
```bash
python manage.py migrate
```

### Demo data not appearing

Check database connection and verify data was created:
```bash
python manage.py shell
>>> from apps.sales.models import Customer
>>> Customer.objects.filter(code__startswith='DEMO').count()
```

### Permission errors

Ensure demo users have appropriate permissions in Django admin.

---

**Version:** 1.0
**Last Updated:** December 2024
