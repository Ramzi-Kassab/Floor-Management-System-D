# Role Permissions Matrix
## Floor Management System - Access Control Documentation

**Version:** 1.0
**Last Updated:** December 2024

---

## Table of Contents
1. [Role Definitions](#1-role-definitions)
2. [Module Access Matrix](#2-module-access-matrix)
3. [Entity CRUD Permissions](#3-entity-crud-permissions)
4. [Approval Authority Matrix](#4-approval-authority-matrix)
5. [Data Visibility Rules](#5-data-visibility-rules)
6. [Field-Level Permissions](#6-field-level-permissions)
7. [Workflow Permissions](#7-workflow-permissions)

---

## 1. Role Definitions

### 1.1 Role Hierarchy

```
LEVEL 5: SYSTEM_ADMIN
    │
LEVEL 4: EXECUTIVE
    │
    ├── VP_OPERATIONS
    ├── VP_SALES
    └── VP_QUALITY
    │
LEVEL 3: MANAGER
    │
    ├── OPERATIONS_MANAGER
    ├── QUALITY_MANAGER
    ├── SALES_MANAGER
    ├── WAREHOUSE_MANAGER
    ├── HR_MANAGER
    └── MAINTENANCE_MANAGER
    │
LEVEL 2: SUPERVISOR / SPECIALIST
    │
    ├── PRODUCTION_PLANNER
    ├── QC_SUPERVISOR
    ├── WAREHOUSE_SUPERVISOR
    ├── FIELD_SUPERVISOR
    └── ACCOUNT_MANAGER
    │
LEVEL 1: OPERATOR / TECHNICIAN
    │
    ├── SHOP_FLOOR_TECH
    ├── QC_INSPECTOR
    ├── WAREHOUSE_CLERK
    ├── FIELD_TECHNICIAN
    ├── SALES_REP
    └── HR_ADMIN

LEVEL 0: READ-ONLY
    │
    ├── AUDITOR
    └── CUSTOMER_PORTAL
```

### 1.2 Role Descriptions

| Role | Description | Module Access |
|------|-------------|---------------|
| **SYSTEM_ADMIN** | Full system access, configuration, user management | All modules |
| **EXECUTIVE** | Strategic oversight, high-value approvals | All modules (read), Key approvals |
| **OPERATIONS_MANAGER** | Production oversight, WO approval, resource allocation | Workorders, Inventory, Reports |
| **QUALITY_MANAGER** | Quality oversight, NCR disposition, compliance | Compliance, Quality, Reports |
| **SALES_MANAGER** | Sales oversight, pricing authority, customer management | Sales, Reports |
| **WAREHOUSE_MANAGER** | Inventory oversight, dispatch approval | Inventory, Dispatch |
| **HR_MANAGER** | HR oversight, payroll approval | HR, Reports |
| **PRODUCTION_PLANNER** | Work order creation, scheduling | Workorders, Inventory (read) |
| **QC_INSPECTOR** | Quality inspections, NCR creation | Quality, Workorders (limited) |
| **WAREHOUSE_CLERK** | Inventory transactions, receiving/shipping | Inventory, Dispatch |
| **FIELD_TECHNICIAN** | Field service, inspections, reports | Field Service, Mobile |
| **SHOP_FLOOR_TECH** | Operation execution, time logging | Workorders (limited) |
| **SALES_REP** | Order entry, customer service | Sales, Customers |
| **AUDITOR** | Read-only access for compliance review | All modules (read-only) |
| **CUSTOMER_PORTAL** | Limited access to own data | Own orders, Own assets |

---

## 2. Module Access Matrix

### 2.1 Primary Module Access

| Role | Workorders | Sales | Inventory | Compliance | HR | Reports | Admin |
|------|------------|-------|-----------|------------|-----|---------|-------|
| SYSTEM_ADMIN | Full | Full | Full | Full | Full | Full | Full |
| EXECUTIVE | Read | Read | Read | Read | Read | Full | Limited |
| OPS_MANAGER | Full | Read | Full | Read | - | Full | - |
| QUALITY_MGR | Read | - | Read | Full | - | Full | - |
| SALES_MGR | Read | Full | Read | - | - | Full | - |
| WAREHOUSE_MGR | Read | Read | Full | - | - | Limited | - |
| HR_MANAGER | - | - | - | Read | Full | Limited | - |
| PROD_PLANNER | Full | Read | Read | - | - | Limited | - |
| QC_INSPECTOR | Limited | - | - | Limited | - | - | - |
| WAREHOUSE_CLERK | Read | Read | Full | - | - | - | - |
| FIELD_TECH | Limited | Limited | - | - | - | - | - |
| SHOP_FLOOR | Limited | - | Limited | - | - | - | - |
| SALES_REP | Read | Full | Read | - | - | - | - |
| AUDITOR | Read | Read | Read | Read | Read | Read | - |
| CUSTOMER | - | Own | - | - | - | Own | - |

**Legend:** Full = All CRUD, Limited = Specific operations, Read = View only, Own = Own records only, - = No access

---

## 3. Entity CRUD Permissions

### 3.1 Workorders Module

| Entity | Create | Read | Update | Delete | Approve |
|--------|--------|------|--------|--------|---------|
| **DrillBit** |
| SYSTEM_ADMIN | Yes | All | All | Yes | - |
| OPS_MANAGER | Yes | All | All | No | - |
| WAREHOUSE_MGR | Yes | All | Limited | No | - |
| PROD_PLANNER | No | All | Limited | No | - |
| QC_INSPECTOR | No | All | Status only | No | - |
| WAREHOUSE_CLERK | Yes (receipt) | All | Location | No | - |
| FIELD_TECH | No | Assigned | Field data | No | - |
| **WorkOrder** |
| SYSTEM_ADMIN | Yes | All | All | Yes | Yes |
| OPS_MANAGER | Yes | All | All | No | Yes (≤$50K) |
| PROD_PLANNER | Yes | All | Pre-release | No | No |
| QC_INSPECTOR | No | Assigned | QC fields | No | No |
| SHOP_FLOOR | No | Assigned | Time/Material | No | No |
| FIELD_TECH | No | Assigned | Field data | No | No |
| **RepairEvaluation** |
| SYSTEM_ADMIN | Yes | All | All | Yes | Yes |
| OPS_MANAGER | Yes | All | All | No | Yes (≤$50K) |
| EXECUTIVE | No | All | No | No | Yes (>$50K) |
| QC_INSPECTOR | Yes | All | Own | No | No |
| PROD_PLANNER | Yes | All | Own | No | No |

### 3.2 Sales Module

| Entity | Create | Read | Update | Delete | Approve |
|--------|--------|------|--------|--------|---------|
| **Customer** |
| SYSTEM_ADMIN | Yes | All | All | Yes | - |
| SALES_MGR | Yes | All | All | No | - |
| ACCOUNT_MGR | Yes | Assigned | Assigned | No | - |
| SALES_REP | Yes | All | Own created | No | - |
| CUSTOMER | No | Own | Own contact | No | - |
| **SalesOrder** |
| SYSTEM_ADMIN | Yes | All | All | Yes | Yes |
| SALES_MGR | Yes | All | All | No | Yes |
| ACCOUNT_MGR | Yes | Assigned | Assigned | No | No |
| SALES_REP | Yes | All | Own (Draft) | No | No |
| OPS_MANAGER | No | All | No | No | No |
| CUSTOMER | No | Own | No | No | No |
| **FieldServiceRequest** |
| SYSTEM_ADMIN | Yes | All | All | Yes | Yes |
| SALES_MGR | Yes | All | All | No | Yes |
| OPS_MANAGER | Yes | All | All | No | Yes |
| FIELD_TECH | No | Assigned | Execution | No | No |
| CUSTOMER | Yes (limited) | Own | No | No | No |

### 3.3 Inventory Module

| Entity | Create | Read | Update | Delete | Approve |
|--------|--------|------|--------|--------|---------|
| **InventoryItem** |
| SYSTEM_ADMIN | Yes | All | All | Yes | - |
| WAREHOUSE_MGR | Yes | All | All | No | - |
| WAREHOUSE_CLERK | No | All | Limited | No | - |
| PROD_PLANNER | No | All | No | No | - |
| **InventoryTransaction** |
| SYSTEM_ADMIN | Yes | All | All | Yes | Yes |
| WAREHOUSE_MGR | Yes | All | All | No | Yes (adj) |
| WAREHOUSE_CLERK | Yes | All | No | No | No |
| SHOP_FLOOR | Yes (issue) | Own | No | No | No |
| **MaterialLot** |
| SYSTEM_ADMIN | Yes | All | All | Yes | - |
| WAREHOUSE_MGR | Yes | All | All | No | - |
| WAREHOUSE_CLERK | Yes | All | Status | No | - |
| QC_INSPECTOR | No | All | QC status | No | - |

### 3.4 Compliance Module

| Entity | Create | Read | Update | Delete | Approve |
|--------|--------|------|--------|--------|---------|
| **ComplianceRequirement** |
| SYSTEM_ADMIN | Yes | All | All | Yes | - |
| QUALITY_MGR | Yes | All | All | No | - |
| QC_INSPECTOR | No | All | Assessment | No | - |
| AUDITOR | No | All | No | No | - |
| **QualityControl** |
| SYSTEM_ADMIN | Yes | All | All | Yes | Yes |
| QUALITY_MGR | Yes | All | All | No | Yes |
| QC_INSPECTOR | Yes | All | Own | No | No |
| **NCR** |
| SYSTEM_ADMIN | Yes | All | All | Yes | Yes |
| QUALITY_MGR | Yes | All | All | No | Yes |
| QC_INSPECTOR | Yes | All | Investigation | No | No |
| ANY_USER | Yes | Related | No | No | No |
| **TrainingRecord** |
| SYSTEM_ADMIN | Yes | All | All | Yes | - |
| HR_MANAGER | Yes | All | All | No | - |
| QUALITY_MGR | Yes | All | All | No | - |
| EMPLOYEE | No | Own | No | No | - |
| **Certification** |
| SYSTEM_ADMIN | Yes | All | All | Yes | - |
| HR_MANAGER | Yes | All | All | No | - |
| QUALITY_MGR | Yes | All | All | No | - |
| EMPLOYEE | No | Own | No | No | - |

### 3.5 HR Module

| Entity | Create | Read | Update | Delete | Approve |
|--------|--------|------|--------|--------|---------|
| **Employee** |
| SYSTEM_ADMIN | Yes | All | All | Yes | - |
| HR_MANAGER | Yes | All | All | Archive | - |
| HR_ADMIN | Yes | All | Limited | No | - |
| MANAGER | No | Reports | Limited | No | - |
| EMPLOYEE | No | Own | Own profile | No | - |
| **TimeEntry** |
| SYSTEM_ADMIN | Yes | All | All | Yes | Yes |
| HR_MANAGER | Yes | All | All | No | Yes |
| SUPERVISOR | No | Reports | No | No | Yes |
| EMPLOYEE | Yes | Own | Own (draft) | Own (draft) | No |
| **LeaveRequest** |
| SYSTEM_ADMIN | Yes | All | All | Yes | Yes |
| HR_MANAGER | Yes | All | All | No | Yes |
| MANAGER | No | Reports | No | No | Yes |
| EMPLOYEE | Yes | Own | Own (pending) | Own (pending) | No |
| **PerformanceReview** |
| SYSTEM_ADMIN | Yes | All | All | Yes | Yes |
| HR_MANAGER | Yes | All | All | No | Yes |
| MANAGER | Yes | Reports | Own created | No | No |
| EMPLOYEE | No | Own | Self-assessment | No | No |

---

## 4. Approval Authority Matrix

### 4.1 Financial Approvals

| Approval Type | < $1K | $1K - $10K | $10K - $50K | $50K - $100K | > $100K |
|--------------|-------|------------|-------------|--------------|---------|
| **Work Order** | Auto | SUPERVISOR | OPS_MGR | EXECUTIVE | CEO |
| **Repair Eval** | Auto | SUPERVISOR | OPS_MGR | EXECUTIVE | CEO |
| **Purchase Order** | Auto | SUPERVISOR | PROC_MGR | EXECUTIVE | CEO |
| **Sales Discount** | Auto | SALES_REP | SALES_MGR | EXECUTIVE | CEO |
| **Inventory Adj** | Auto | WAREHOUSE_MGR | OPS_MGR | CFO | CFO |

### 4.2 Workflow Approvals

| Approval Type | Authority Level | Escalation Path |
|--------------|-----------------|-----------------|
| **Leave Request** | Direct Manager | HR Manager → VP |
| **Time Correction** | Supervisor | HR Manager |
| **NCR Disposition** | Quality Manager | VP Quality |
| **Document Release** | Department Manager | Quality Manager |
| **Customer Credit** | Sales Manager | CFO |
| **Equipment Scrap** | Operations Manager | CFO |
| **Overtime Auth** | Supervisor | HR Manager |

### 4.3 Escalation Matrix

```
TIME THRESHOLDS FOR ESCALATION:

Level 1 (Initial Approver):
├── 24 hours → Email reminder
├── 48 hours → Escalate to Level 2
└── Notification to requester

Level 2 (Manager):
├── 24 hours → Email reminder
├── 48 hours → Escalate to Level 3
└── Notification to Level 1 + requester

Level 3 (Executive):
├── 12 hours → Email reminder
├── 24 hours → CEO notification
└── Auto-approve with audit flag (configurable)
```

---

## 5. Data Visibility Rules

### 5.1 Record-Level Access

| Scenario | Visibility Rule |
|----------|-----------------|
| **Own Records** | User can see records they created |
| **Department Records** | Users see records from their department |
| **Assigned Records** | Users see records assigned to them |
| **Subordinate Records** | Managers see their direct reports' data |
| **Customer-Specific** | Sales reps see only assigned customers |
| **Site-Specific** | Field techs see assigned service sites |

### 5.2 Implementation Example

```python
class WorkOrderQuerySet(models.QuerySet):
    def for_user(self, user):
        """Filter work orders based on user permissions."""

        if user.has_role('SYSTEM_ADMIN'):
            return self.all()

        if user.has_role('EXECUTIVE'):
            return self.all()

        if user.has_role('OPERATIONS_MANAGER'):
            return self.all()

        if user.has_role('PRODUCTION_PLANNER'):
            return self.all()

        if user.has_role('QC_INSPECTOR'):
            return self.filter(
                models.Q(status__in=['QC_PENDING', 'QC_PASSED', 'QC_FAILED']) |
                models.Q(qc_inspector=user)
            )

        if user.has_role('SHOP_FLOOR_TECH'):
            return self.filter(
                models.Q(assigned_to=user) |
                models.Q(status='IN_PROGRESS', department=user.department)
            )

        if user.has_role('FIELD_TECHNICIAN'):
            return self.filter(
                service_requests__assigned_technician__user=user
            ).distinct()

        # Default: own records only
        return self.filter(created_by=user)
```

### 5.3 Sensitive Data Masking

| Data Type | Full Access | Masked For | Masking Rule |
|-----------|-------------|------------|--------------|
| **Employee SSN** | HR_MANAGER, SYSTEM_ADMIN | Others | Show last 4 digits |
| **Bank Account** | HR_MANAGER, SYSTEM_ADMIN | Others | Show last 4 digits |
| **Salary** | HR_MANAGER, Employee's manager | Others | Hidden |
| **Customer Credit Limit** | SALES_MGR, EXECUTIVE | SALES_REP | Hidden |
| **Cost Data** | MANAGER+, Finance | OPERATOR | Hidden |
| **Pricing Margins** | SALES_MGR, EXECUTIVE | SALES_REP | Hidden |

---

## 6. Field-Level Permissions

### 6.1 WorkOrder Field Access

| Field | VIEW | EDIT (Creator) | EDIT (Planner) | EDIT (Manager) |
|-------|------|----------------|----------------|----------------|
| wo_number | All | - | - | - |
| status | All | Draft only | All | All |
| priority | All | Draft only | All | All |
| drill_bit | All | Pre-release | Pre-release | All |
| customer | All | Pre-release | Pre-release | All |
| estimated_cost | Mgr+ | Draft only | Yes | Yes |
| actual_cost | Mgr+ | - | - | Yes |
| assigned_to | All | - | Yes | Yes |
| approved_by | All | - | - | - |
| notes | All | Yes | Yes | Yes |

### 6.2 Employee Field Access

| Field | Employee | Manager | HR_Admin | HR_Manager |
|-------|----------|---------|----------|------------|
| personal info | Own (read) | - | Edit | Edit |
| contact info | Own (edit) | Reports (read) | Edit | Edit |
| salary info | - | - | Read | Edit |
| bank info | Own (read) | - | Edit | Edit |
| performance | Own (read) | Reports (edit) | Read | Edit |
| leave balance | Own (read) | Reports (read) | Read | Edit |
| disciplinary | - | Reports (read) | Edit | Edit |

### 6.3 SalesOrder Field Access

| Field | Sales Rep | Account Mgr | Sales Mgr | Operations |
|-------|-----------|-------------|-----------|------------|
| customer | Own (edit) | Assigned | All | Read |
| pricing | Edit (draft) | Edit | Edit + Approve | Read |
| discount | Limited | Up to 10% | Up to 30% | - |
| credit_approved | - | - | Yes | - |
| delivery_date | Edit | Edit | Edit | Read |
| status | Limited | Limited | All | Read |

---

## 7. Workflow Permissions

### 7.1 Status Transition Permissions

#### Work Order Transitions

| From → To | SHOP_FLOOR | QC_INSP | PLANNER | OPS_MGR | ADMIN |
|-----------|------------|---------|---------|---------|-------|
| DRAFT → PLANNED | - | - | Yes | Yes | Yes |
| PLANNED → RELEASED | - | - | Yes | Yes | Yes |
| RELEASED → IN_PROGRESS | Yes | - | Yes | Yes | Yes |
| IN_PROGRESS → QC_PENDING | Yes | - | Yes | Yes | Yes |
| QC_PENDING → QC_PASSED | - | Yes | - | Yes | Yes |
| QC_PENDING → QC_FAILED | - | Yes | - | Yes | Yes |
| QC_PASSED → COMPLETED | - | Yes | Yes | Yes | Yes |
| * → CANCELLED | - | - | Yes (draft) | Yes | Yes |
| * → ON_HOLD | - | - | Yes | Yes | Yes |

#### NCR Transitions

| From → To | ANY_USER | QC_INSP | QA_MGR | ADMIN |
|-----------|----------|---------|--------|-------|
| (new) → OPEN | Yes | Yes | Yes | Yes |
| OPEN → INVESTIGATING | - | Yes | Yes | Yes |
| INVESTIGATING → PENDING_DISP | - | Yes | Yes | Yes |
| PENDING_DISP → IN_REWORK | - | - | Yes | Yes |
| IN_REWORK → PENDING_VERIFY | - | Yes | Yes | Yes |
| PENDING_VERIFY → CLOSED | - | - | Yes | Yes |
| * → CANCELLED | - | - | Yes | Yes |

### 7.2 Action Permissions

| Action | Required Role | Conditions |
|--------|---------------|------------|
| Create Work Order | PLANNER+ | - |
| Release Work Order | PLANNER+ | Estimated cost entered |
| Start Work Order | SHOP_FLOOR+ | Assigned to user or department |
| Complete Operation | SHOP_FLOOR+ | Previous operations complete |
| Request QC | SHOP_FLOOR+ | All operations complete |
| Pass QC | QC_INSPECTOR+ | Inspection checklist complete |
| Fail QC | QC_INSPECTOR+ | Defects documented |
| Close Work Order | QC_INSPECTOR+ or PLANNER+ | QC Passed |
| Cancel Work Order | PLANNER+ (draft), OPS_MGR+ (other) | - |
| Approve High-Value | OPS_MGR+ | Based on $ threshold |
| Override Status | SYSTEM_ADMIN | Audit logged |

### 7.3 Bulk Action Permissions

| Action | Minimum Role | Max Records | Audit Required |
|--------|--------------|-------------|----------------|
| Bulk status update | MANAGER | 50 | Yes |
| Bulk assignment | SUPERVISOR | 100 | Yes |
| Bulk delete | SYSTEM_ADMIN | 25 | Yes |
| Bulk export | SUPERVISOR | 10,000 | Yes |
| Bulk import | MANAGER | 1,000 | Yes |

---

## Appendix A: Permission Codes

```python
# Permission code format: app.action_model
# Example: workorders.add_workorder

PERMISSION_CODES = {
    # Workorders
    'workorders.view_workorder': 'View work orders',
    'workorders.add_workorder': 'Create work orders',
    'workorders.change_workorder': 'Edit work orders',
    'workorders.delete_workorder': 'Delete work orders',
    'workorders.release_workorder': 'Release work orders',
    'workorders.approve_workorder': 'Approve high-value work orders',

    # Sales
    'sales.view_salesorder': 'View sales orders',
    'sales.add_salesorder': 'Create sales orders',
    'sales.change_salesorder': 'Edit sales orders',
    'sales.approve_discount': 'Approve sales discounts',

    # Inventory
    'inventory.view_inventoryitem': 'View inventory',
    'inventory.add_inventorytransaction': 'Create inventory transactions',
    'inventory.approve_adjustment': 'Approve inventory adjustments',

    # Compliance
    'compliance.view_ncr': 'View NCRs',
    'compliance.add_ncr': 'Create NCRs',
    'compliance.disposition_ncr': 'Approve NCR dispositions',

    # HR
    'hr.view_employee': 'View employee records',
    'hr.view_salary': 'View salary information',
    'hr.approve_leave': 'Approve leave requests',
    'hr.approve_timeentry': 'Approve time entries',
}
```

## Appendix B: Role Permission Mapping

```python
ROLE_PERMISSIONS = {
    'SYSTEM_ADMIN': ['*'],  # All permissions

    'OPERATIONS_MANAGER': [
        'workorders.*',
        'inventory.view_*',
        'inventory.add_inventorytransaction',
        'compliance.view_*',
        'reports.*',
    ],

    'QUALITY_MANAGER': [
        'compliance.*',
        'workorders.view_*',
        'workorders.change_workorder',  # QC fields only
        'reports.quality_*',
    ],

    'PRODUCTION_PLANNER': [
        'workorders.view_*',
        'workorders.add_workorder',
        'workorders.change_workorder',
        'workorders.release_workorder',
        'inventory.view_*',
        'sales.view_salesorder',
    ],

    'QC_INSPECTOR': [
        'compliance.view_*',
        'compliance.add_qualitycontrol',
        'compliance.add_ncr',
        'compliance.change_ncr',
        'workorders.view_workorder',
        'workorders.change_workorder',  # QC fields only
    ],

    'WAREHOUSE_CLERK': [
        'inventory.view_*',
        'inventory.add_inventorytransaction',
        'inventory.change_inventorystock',
        'dispatch.view_*',
        'dispatch.add_dispatchitem',
    ],

    'FIELD_TECHNICIAN': [
        'sales.view_fieldservicerequest',
        'sales.change_fieldservicerequest',  # Execution fields
        'sales.add_servicereport',
        'workorders.view_workorder',
        'compliance.add_bitevaluation',
    ],

    'SALES_REP': [
        'sales.view_*',
        'sales.add_customer',
        'sales.change_customer',
        'sales.add_salesorder',
        'sales.change_salesorder',  # Own, draft only
    ],
}
```

---

**Document Control:**
- Created: December 2024
- Review Cycle: Quarterly
- Owner: Security Team
- Classification: Internal - Confidential
