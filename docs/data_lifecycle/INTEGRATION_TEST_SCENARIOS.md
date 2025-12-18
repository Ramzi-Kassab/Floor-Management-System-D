# Integration Test Scenarios
## Floor Management System - End-to-End Test Cases

**Version:** 1.0
**Last Updated:** December 2024

---

## Table of Contents
1. [Test Framework Overview](#1-test-framework-overview)
2. [Drill Bit Lifecycle Tests](#2-drill-bit-lifecycle-tests)
3. [Sales Order Workflow Tests](#3-sales-order-workflow-tests)
4. [Quality Management Tests](#4-quality-management-tests)
5. [Field Service Tests](#5-field-service-tests)
6. [Inventory Management Tests](#6-inventory-management-tests)
7. [HR Workflow Tests](#7-hr-workflow-tests)
8. [Cross-Module Integration Tests](#8-cross-module-integration-tests)
9. [Data Integrity Tests](#9-data-integrity-tests)
10. [Performance & Load Tests](#10-performance-load-tests)

---

## 1. Test Framework Overview

### 1.1 Test Categories

| Category | Purpose | Frequency | Environment |
|----------|---------|-----------|-------------|
| Unit Tests | Individual function validation | Per commit | Local |
| Integration Tests | Cross-module workflows | Daily | Staging |
| End-to-End Tests | Complete user journeys | Weekly | Staging |
| Regression Tests | Prevent functionality loss | Per release | Staging |
| Performance Tests | System capacity validation | Monthly | Performance |
| UAT Tests | Business acceptance | Per release | UAT |

### 1.2 Test Data Requirements

```python
# Base fixtures required for all integration tests
REQUIRED_FIXTURES = [
    'fixtures/users.json',           # Test users for each role
    'fixtures/organizations.json',   # Departments, positions
    'fixtures/customers.json',       # Sample customers
    'fixtures/inventory.json',       # Inventory items and stock
    'fixtures/drillbits.json',       # Sample drill bits
    'fixtures/compliance.json',      # Compliance requirements
]

# Test user credentials
TEST_USERS = {
    'admin': {'username': 'test_admin', 'role': 'SYSTEM_ADMIN'},
    'ops_manager': {'username': 'test_ops_mgr', 'role': 'OPERATIONS_MANAGER'},
    'qa_manager': {'username': 'test_qa_mgr', 'role': 'QUALITY_MANAGER'},
    'planner': {'username': 'test_planner', 'role': 'PRODUCTION_PLANNER'},
    'qc_inspector': {'username': 'test_qc', 'role': 'QC_INSPECTOR'},
    'warehouse': {'username': 'test_warehouse', 'role': 'WAREHOUSE_CLERK'},
    'field_tech': {'username': 'test_field', 'role': 'FIELD_TECHNICIAN'},
    'sales_rep': {'username': 'test_sales', 'role': 'SALES_REP'},
}
```

---

## 2. Drill Bit Lifecycle Tests

### 2.1 TEST-DB-001: Complete Repair Workflow

**Objective:** Validate end-to-end drill bit repair from receipt to dispatch

**Prerequisites:**
- Customer exists: CUST-001 (Shell)
- Warehouse location: WH-HOU-01
- Inventory: PDC Cutters (QTY: 50)
- Test user: planner, qc_inspector, warehouse

**Test Steps:**

```python
@pytest.mark.integration
class TestDrillBitRepairWorkflow:
    """
    Test Case: TEST-DB-001
    Complete drill bit repair workflow
    """

    def test_step_01_receive_drill_bit(self, warehouse_user, customer):
        """Step 1: Receive returned drill bit from customer."""
        # Login as warehouse clerk
        self.client.login(username='test_warehouse', password='test123')

        # Create drill bit receipt
        response = self.client.post('/api/drillbits/', {
            'serial_number': 'TEST-DB-2024-001',
            'bit_type': 'PDC',
            'customer': customer.id,
            'status': 'RETURNED',
            'physical_status': 'AT_ARDT',
        })

        assert response.status_code == 201
        drill_bit = DrillBit.objects.get(serial_number='TEST-DB-2024-001')
        assert drill_bit.status == 'RETURNED'

        # Verify scan log created
        assert ScanLog.objects.filter(
            entity_type='DRILL_BIT',
            entity_id=drill_bit.id,
            purpose='CHECK_IN'
        ).exists()

    def test_step_02_create_evaluation(self, planner_user, drill_bit):
        """Step 2: Create repair evaluation."""
        self.client.login(username='test_planner', password='test123')

        response = self.client.post('/api/repair-evaluations/', {
            'drill_bit': drill_bit.id,
            'evaluation_type': 'INCOMING',
            'damage_assessment': 'Cutters worn, body good condition',
            'inner_rows_grade': '4',
            'outer_rows_grade': '5',
            'recommendation': 'REPAIR',
            'estimated_labor_hours': 40,
            'estimated_material_cost': 8000,
        })

        assert response.status_code == 201
        evaluation = RepairEvaluation.objects.get(drill_bit=drill_bit)
        assert evaluation.status == 'DRAFT'

    def test_step_03_submit_for_approval(self, planner_user, evaluation):
        """Step 3: Submit evaluation for approval (> $10K)."""
        self.client.login(username='test_planner', password='test123')

        response = self.client.post(
            f'/api/repair-evaluations/{evaluation.id}/submit/'
        )

        assert response.status_code == 200
        evaluation.refresh_from_db()
        assert evaluation.status == 'PENDING_APPROVAL'

        # Verify notification sent to manager
        assert Notification.objects.filter(
            recipient__roles__code='OPERATIONS_MANAGER',
            entity_type='RepairEvaluation',
            entity_id=evaluation.id
        ).exists()

    def test_step_04_manager_approval(self, ops_manager_user, evaluation):
        """Step 4: Operations manager approves."""
        self.client.login(username='test_ops_mgr', password='test123')

        response = self.client.post(
            f'/api/repair-evaluations/{evaluation.id}/approve/'
        )

        assert response.status_code == 200
        evaluation.refresh_from_db()
        assert evaluation.status == 'APPROVED'
        assert evaluation.approved_by is not None

    def test_step_05_create_work_order(self, planner_user, evaluation):
        """Step 5: Create work order from approved evaluation."""
        self.client.login(username='test_planner', password='test123')

        response = self.client.post('/api/workorders/', {
            'wo_type': 'FC_REPAIR',
            'drill_bit': evaluation.drill_bit.id,
            'repair_evaluation': evaluation.id,
            'priority': 'HIGH',
            'estimated_hours': evaluation.estimated_labor_hours,
            'estimated_cost': evaluation.total_estimated_cost,
        })

        assert response.status_code == 201
        work_order = WorkOrder.objects.get(repair_evaluation=evaluation)
        assert work_order.status == 'DRAFT'

        # Verify BOM created
        assert RepairBOM.objects.filter(work_order=work_order).exists()

    def test_step_06_release_work_order(self, planner_user, work_order):
        """Step 6: Release work order to production."""
        self.client.login(username='test_planner', password='test123')

        # Assign to technician
        work_order.assigned_to = User.objects.get(username='test_shop')
        work_order.save()

        response = self.client.post(
            f'/api/workorders/{work_order.id}/release/'
        )

        assert response.status_code == 200
        work_order.refresh_from_db()
        assert work_order.status == 'RELEASED'

        # Verify materials reserved
        for material in work_order.materials.all():
            assert material.status == 'RESERVED'

    def test_step_07_execute_operations(self, shop_user, work_order):
        """Step 7: Shop floor executes operations."""
        self.client.login(username='test_shop', password='test123')

        # Start work order
        response = self.client.post(
            f'/api/workorders/{work_order.id}/start/'
        )
        assert response.status_code == 200

        # Execute each operation
        for operation in work_order.operations.order_by('sequence'):
            response = self.client.post(
                f'/api/operations/{operation.id}/complete/',
                {
                    'actual_hours': operation.estimated_hours * 0.9,
                    'notes': 'Completed successfully',
                }
            )
            assert response.status_code == 200

        work_order.refresh_from_db()
        assert work_order.status == 'IN_PROGRESS'

    def test_step_08_submit_for_qc(self, shop_user, work_order):
        """Step 8: Submit for QC inspection."""
        self.client.login(username='test_shop', password='test123')

        response = self.client.post(
            f'/api/workorders/{work_order.id}/submit-qc/'
        )

        assert response.status_code == 200
        work_order.refresh_from_db()
        assert work_order.status == 'QC_PENDING'

    def test_step_09_qc_inspection_pass(self, qc_user, work_order):
        """Step 9: QC inspector performs inspection."""
        self.client.login(username='test_qc', password='test123')

        # Create inspection
        response = self.client.post('/api/inspections/', {
            'work_order': work_order.id,
            'inspection_type': 'FINAL',
            'drill_bit': work_order.drill_bit.id,
        })
        inspection = Inspection.objects.get(work_order=work_order)

        # Complete checklist and pass
        response = self.client.post(
            f'/api/inspections/{inspection.id}/complete/',
            {
                'status': 'PASSED',
                'findings': 'All specifications met',
            }
        )

        assert response.status_code == 200
        work_order.refresh_from_db()
        assert work_order.status == 'QC_PASSED'

    def test_step_10_complete_work_order(self, qc_user, work_order):
        """Step 10: Complete work order and update drill bit."""
        self.client.login(username='test_qc', password='test123')

        response = self.client.post(
            f'/api/workorders/{work_order.id}/complete/'
        )

        assert response.status_code == 200
        work_order.refresh_from_db()
        assert work_order.status == 'COMPLETED'

        # Verify drill bit updated
        drill_bit = work_order.drill_bit
        drill_bit.refresh_from_db()
        assert drill_bit.status == 'READY'
        assert drill_bit.total_repairs > 0

        # Verify repair history recorded
        assert BitRepairHistory.objects.filter(
            drill_bit=drill_bit,
            work_order=work_order
        ).exists()

    def test_step_11_dispatch_to_customer(self, warehouse_user, work_order):
        """Step 11: Dispatch repaired bit to customer."""
        self.client.login(username='test_warehouse', password='test123')

        drill_bit = work_order.drill_bit

        # Create dispatch
        response = self.client.post('/api/dispatches/', {
            'customer': drill_bit.customer.id,
            'vehicle': Vehicle.objects.first().id,
            'items': [
                {'drill_bit': drill_bit.id, 'quantity': 1}
            ]
        })

        assert response.status_code == 201
        dispatch = Dispatch.objects.get(
            items__drill_bit=drill_bit
        )
        assert dispatch.status == 'PLANNED'

        # Mark as shipped
        response = self.client.post(
            f'/api/dispatches/{dispatch.id}/ship/'
        )

        drill_bit.refresh_from_db()
        assert drill_bit.physical_status == 'IN_TRANSIT'

    def test_complete_workflow_data_integrity(self, drill_bit):
        """Verify all data correctly linked after workflow."""
        drill_bit.refresh_from_db()

        # Verify chain of records
        evaluation = drill_bit.evaluations.latest('created_at')
        work_order = WorkOrder.objects.get(drill_bit=drill_bit, status='COMPLETED')
        inspection = Inspection.objects.get(work_order=work_order)
        repair_history = BitRepairHistory.objects.get(work_order=work_order)

        assert evaluation.resulting_work_order == work_order
        assert inspection.status == 'PASSED'
        assert repair_history.condition_after is not None

        # Verify costs calculated
        cost = work_order.cost
        assert cost.total_actual_cost > 0
        assert cost.variance is not None
```

### 2.2 TEST-DB-002: Scrap Workflow

**Objective:** Validate drill bit scrap path when repair not viable

```python
@pytest.mark.integration
class TestDrillBitScrapWorkflow:

    def test_evaluation_recommends_scrap(self, planner_user, worn_drill_bit):
        """Evaluation recommends scrap due to condition."""
        response = self.client.post('/api/repair-evaluations/', {
            'drill_bit': worn_drill_bit.id,
            'damage_assessment': 'Severe body damage, beyond repair',
            'recommendation': 'SCRAP',
            'inner_rows_grade': '8',
            'outer_rows_grade': '8',
        })

        evaluation = RepairEvaluation.objects.get(drill_bit=worn_drill_bit)
        assert evaluation.recommendation == 'SCRAP'

    def test_salvage_item_creation(self, warehouse_user, scrapped_bit):
        """Create salvage items from scrapped bit."""
        response = self.client.post('/api/salvage-items/', {
            'source_bit': scrapped_bit.id,
            'item_type': 'CUTTERS',
            'quantity': 24,
            'condition': 'FAIR',
            'estimated_value': 2400,
        })

        assert response.status_code == 201
        salvage = SalvageItem.objects.get(source_bit=scrapped_bit)
        assert salvage.status == 'AVAILABLE'

    def test_drill_bit_write_off(self, ops_manager_user, scrapped_bit):
        """Write off drill bit book value."""
        response = self.client.post(
            f'/api/drillbits/{scrapped_bit.id}/scrap/',
            {'reason': 'Beyond economical repair'}
        )

        scrapped_bit.refresh_from_db()
        assert scrapped_bit.status == 'SCRAPPED'
        assert scrapped_bit.accounting_status == 'WRITTEN_OFF'

        # Verify audit trail
        assert AuditLog.objects.filter(
            entity_type='DrillBit',
            entity_id=scrapped_bit.id,
            action='UPDATE'
        ).exists()
```

---

## 3. Sales Order Workflow Tests

### 3.1 TEST-SO-001: Order to Delivery

```python
@pytest.mark.integration
class TestSalesOrderWorkflow:

    def test_step_01_create_order(self, sales_rep_user, customer):
        """Create new sales order."""
        self.client.login(username='test_sales', password='test123')

        response = self.client.post('/api/sales-orders/', {
            'customer': customer.id,
            'order_date': date.today().isoformat(),
            'required_date': (date.today() + timedelta(days=14)).isoformat(),
            'lines': [
                {
                    'description': 'PDC Bit Repair 8.5"',
                    'quantity': 1,
                    'unit_price': 15000,
                }
            ]
        })

        assert response.status_code == 201
        order = SalesOrder.objects.latest('created_at')
        assert order.status == 'DRAFT'
        assert order.total_amount == 15000

    def test_step_02_credit_check(self, sales_manager_user, order):
        """Confirm order with credit check."""
        self.client.login(username='test_sales_mgr', password='test123')

        # Customer credit limit is 500000, outstanding is 100000
        response = self.client.post(
            f'/api/sales-orders/{order.id}/confirm/'
        )

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == 'CONFIRMED'
        assert order.credit_approved == True

    def test_step_03_credit_exceeded(self, sales_rep_user, over_limit_order):
        """Reject order when credit exceeded."""
        response = self.client.post(
            f'/api/sales-orders/{over_limit_order.id}/confirm/'
        )

        assert response.status_code == 400
        assert 'credit limit' in response.json()['error'].lower()

    def test_step_04_production_trigger(self, planner_user, confirmed_order):
        """Work order created from confirmed sales order."""
        # Verify work orders created for each line
        for line in confirmed_order.lines.all():
            work_order = WorkOrder.objects.filter(
                sales_order_line=line
            ).first()
            assert work_order is not None
            assert work_order.status == 'DRAFT'

    def test_step_05_ready_for_shipment(self, warehouse_user, completed_order):
        """All items ready triggers shipment preparation."""
        # All work orders completed
        for line in completed_order.lines.all():
            line.status = 'READY'
            line.save()

        completed_order.refresh_from_db()
        assert completed_order.status == 'READY'

        # Verify packing list generated
        assert PackingList.objects.filter(
            sales_order=completed_order
        ).exists()

    def test_step_06_dispatch_and_delivery(self, warehouse_user, ready_order):
        """Ship order and confirm delivery."""
        # Create dispatch
        dispatch = Dispatch.objects.create(
            sales_order=ready_order,
            vehicle=Vehicle.objects.first(),
            driver_name='Test Driver',
        )

        # Ship
        response = self.client.post(f'/api/dispatches/{dispatch.id}/ship/')
        assert response.status_code == 200

        ready_order.refresh_from_db()
        assert ready_order.status == 'DISPATCHED'

        # Confirm delivery
        response = self.client.post(
            f'/api/dispatches/{dispatch.id}/deliver/',
            {'delivery_signature': 'base64_signature_data'}
        )

        ready_order.refresh_from_db()
        assert ready_order.status == 'DELIVERED'

        # Verify customer notification
        assert Notification.objects.filter(
            entity_type='SalesOrder',
            entity_id=ready_order.id,
            title__icontains='delivered'
        ).exists()
```

---

## 4. Quality Management Tests

### 4.1 TEST-NCR-001: NCR Investigation Flow

```python
@pytest.mark.integration
class TestNCRWorkflow:

    def test_step_01_ncr_creation_from_inspection(self, qc_user, failed_inspection):
        """Create NCR from failed inspection."""
        response = self.client.post('/api/ncrs/', {
            'inspection': failed_inspection.id,
            'title': 'Thread pitch out of tolerance',
            'severity': 'MAJOR',
            'description': 'Thread pitch 0.005" below minimum specification',
            'detected_stage': 'IN_PROCESS',
        })

        assert response.status_code == 201
        ncr = NCR.objects.latest('created_at')
        assert ncr.status == 'OPEN'
        assert ncr.inspection == failed_inspection

    def test_step_02_containment_action(self, qc_user, open_ncr):
        """Document containment action."""
        response = self.client.post(
            f'/api/ncrs/{open_ncr.id}/containment/',
            {
                'action': 'Quarantine all bits from lot LOT-2024-001',
                'affected_quantity': 5,
            }
        )

        assert response.status_code == 200

        # Verify related items quarantined
        quarantined = DrillBit.objects.filter(
            lot_number='LOT-2024-001',
            status='QUARANTINE'
        ).count()
        assert quarantined == 5

    def test_step_03_investigation(self, qc_user, ncr_with_containment):
        """Document root cause investigation."""
        ncr = ncr_with_containment

        response = self.client.post(
            f'/api/ncrs/{ncr.id}/investigate/',
            {
                'root_cause': 'Thread cutting insert worn beyond tolerance',
                'contributing_factors': 'Insert not changed per schedule',
                'investigation_method': '5-Why Analysis',
            }
        )

        ncr.refresh_from_db()
        assert ncr.status == 'INVESTIGATING'
        assert ncr.root_cause is not None

    def test_step_04_disposition_decision(self, qa_manager_user, investigated_ncr):
        """Quality manager approves disposition."""
        response = self.client.post(
            f'/api/ncrs/{investigated_ncr.id}/disposition/',
            {
                'disposition': 'REWORK',
                'disposition_notes': 'Re-cut threads to specification',
            }
        )

        investigated_ncr.refresh_from_db()
        assert investigated_ncr.status == 'IN_REWORK'
        assert investigated_ncr.disposition == 'REWORK'

        # Verify rework work order created
        assert WorkOrder.objects.filter(
            ncr=investigated_ncr,
            wo_type__contains='REWORK'
        ).exists()

    def test_step_05_verification(self, qc_user, reworked_ncr):
        """Verify corrective action effectiveness."""
        response = self.client.post(
            f'/api/ncrs/{reworked_ncr.id}/verify/',
            {
                'verification_result': 'PASS',
                'verification_notes': 'Re-inspection passed all criteria',
            }
        )

        reworked_ncr.refresh_from_db()
        assert reworked_ncr.status == 'PENDING_VERIFICATION'

    def test_step_06_closure(self, qa_manager_user, verified_ncr):
        """Close NCR with lessons learned."""
        response = self.client.post(
            f'/api/ncrs/{verified_ncr.id}/close/',
            {
                'closure_notes': 'Corrective action effective',
                'preventive_actions': 'Update insert change schedule',
                'lessons_learned': 'Implement proactive insert monitoring',
            }
        )

        verified_ncr.refresh_from_db()
        assert verified_ncr.status == 'CLOSED'
        assert verified_ncr.closed_at is not None

        # Verify metrics updated
        quality_metric = QualityMetric.objects.filter(
            metric_code='NCR_COUNT'
        ).latest('period_end')
        assert quality_metric.actual_value > 0
```

---

## 5. Field Service Tests

### 5.1 TEST-FSR-001: Service Request Lifecycle

```python
@pytest.mark.integration
class TestFieldServiceWorkflow:

    def test_step_01_customer_creates_request(self, customer_portal_user, service_site):
        """Customer creates service request."""
        response = self.client.post('/api/field-service-requests/', {
            'service_site': service_site.id,
            'request_type': 'DRILL_BIT_INSPECTION',
            'description': 'Quarterly inspection required',
            'requested_date': (date.today() + timedelta(days=3)).isoformat(),
            'priority': 'MEDIUM',
        })

        assert response.status_code == 201
        fsr = FieldServiceRequest.objects.latest('created_at')
        assert fsr.status == 'SUBMITTED'

    def test_step_02_operations_review(self, ops_manager_user, submitted_fsr):
        """Operations reviews and approves request."""
        response = self.client.post(
            f'/api/field-service-requests/{submitted_fsr.id}/review/',
            {'review_notes': 'Approved for scheduling'}
        )

        submitted_fsr.refresh_from_db()
        assert submitted_fsr.status == 'REVIEWED'

        response = self.client.post(
            f'/api/field-service-requests/{submitted_fsr.id}/approve/'
        )
        submitted_fsr.refresh_from_db()
        assert submitted_fsr.status == 'APPROVED'

    def test_step_03_technician_assignment(self, ops_manager_user, approved_fsr):
        """Assign qualified technician."""
        # Find available technician with required skills
        technician = FieldTechnician.objects.filter(
            employment_status='ACTIVE',
            is_currently_assigned=False,
            can_perform_inspections=True,
        ).first()

        response = self.client.post(
            f'/api/field-service-requests/{approved_fsr.id}/assign/',
            {'technician': technician.id}
        )

        approved_fsr.refresh_from_db()
        assert approved_fsr.status == 'SCHEDULED'
        assert approved_fsr.assigned_technician == technician

        technician.refresh_from_db()
        assert technician.is_currently_assigned == True

    def test_step_04_technician_starts_service(self, field_tech_user, scheduled_fsr):
        """Technician checks in at site."""
        response = self.client.post(
            f'/api/field-service-requests/{scheduled_fsr.id}/check-in/',
            {
                'latitude': 29.7604,
                'longitude': -95.3698,
            }
        )

        scheduled_fsr.refresh_from_db()
        assert scheduled_fsr.status == 'IN_PROGRESS'
        assert scheduled_fsr.started_at is not None

        # Verify scan log
        assert ScanLog.objects.filter(
            entity_type='ServiceSite',
            purpose='CHECK_IN'
        ).exists()

    def test_step_05_service_execution(self, field_tech_user, in_progress_fsr):
        """Technician performs service and documents."""
        # Create inspection evaluation
        response = self.client.post('/api/bit-evaluations/', {
            'field_service_request': in_progress_fsr.id,
            'drill_bit': in_progress_fsr.service_site.drill_bits.first().id,
            'evaluation_type': 'FIELD',
            'inner_rows_grade': '3',
            'outer_rows_grade': '3',
            'recommendation': 'CONTINUE',
        })

        # Add photos
        response = self.client.post('/api/field-documents/', {
            'field_service_request': in_progress_fsr.id,
            'document_type': 'INSPECTION_PHOTO',
            'file': test_image_file,
        })

        assert response.status_code == 201

    def test_step_06_service_completion(self, field_tech_user, in_progress_fsr):
        """Complete service with customer sign-off."""
        response = self.client.post(
            f'/api/field-service-requests/{in_progress_fsr.id}/complete/',
            {
                'findings_summary': 'Bit in good condition, continue use',
                'recommendations': 'Schedule next inspection in 30 days',
                'customer_signature': 'base64_signature',
                'customer_name': 'John Smith',
            }
        )

        in_progress_fsr.refresh_from_db()
        assert in_progress_fsr.status == 'COMPLETED'
        assert in_progress_fsr.completed_at is not None

        # Verify service report generated
        assert ServiceReport.objects.filter(
            field_service_request=in_progress_fsr
        ).exists()

        # Verify technician freed up
        tech = in_progress_fsr.assigned_technician
        tech.refresh_from_db()
        assert tech.is_currently_assigned == False
        assert tech.completed_calls > 0
```

---

## 6. Inventory Management Tests

### 6.1 TEST-INV-001: Material Consumption Traceability

```python
@pytest.mark.integration
class TestInventoryTraceability:

    def test_lot_traceability_through_production(self):
        """Verify material lot traced from receipt to consumption."""
        # Step 1: Receive material lot
        lot = MaterialLot.objects.create(
            lot_number='LOT-TEST-001',
            inventory_item=self.pdc_cutter,
            initial_quantity=100,
            quantity_on_hand=100,
            vendor=self.vendor,
            cert_number='CERT-001',
        )

        # Step 2: Issue to work order
        consumption = MaterialConsumption.objects.create(
            work_order=self.work_order,
            lot=lot,
            quantity_consumed=12,
            consumed_by=self.shop_user,
        )

        lot.refresh_from_db()
        assert lot.quantity_on_hand == 88
        assert lot.status == 'IN_USE'

        # Step 3: Verify traceability chain
        # From drill bit, trace back to material lot
        drill_bit = self.work_order.drill_bit
        consumptions = MaterialConsumption.objects.filter(
            work_order__drill_bit=drill_bit
        )

        # All materials used on this bit
        materials_used = [c.lot.lot_number for c in consumptions]
        assert 'LOT-TEST-001' in materials_used

        # From lot, find all drill bits it was used on
        bits_using_lot = DrillBit.objects.filter(
            workorder__material_consumptions__lot=lot
        ).distinct()
        assert drill_bit in bits_using_lot
```

---

## 7. HR Workflow Tests

### 7.1 TEST-HR-001: Leave Request Approval

```python
@pytest.mark.integration
class TestLeaveRequestWorkflow:

    def test_leave_request_approval_chain(self):
        """Test leave request from submission to approval."""
        # Employee submits leave
        self.client.login(username='test_employee', password='test123')
        response = self.client.post('/api/leave-requests/', {
            'leave_type': 'ANNUAL',
            'start_date': (date.today() + timedelta(days=7)).isoformat(),
            'end_date': (date.today() + timedelta(days=10)).isoformat(),
            'reason': 'Family vacation',
        })

        leave = LeaveRequest.objects.latest('created_at')
        assert leave.status == 'PENDING'
        assert leave.total_days == 4

        # Manager approves
        self.client.login(username='test_manager', password='test123')
        response = self.client.post(
            f'/api/leave-requests/{leave.id}/approve/'
        )

        leave.refresh_from_db()
        assert leave.status == 'APPROVED'

        # Verify leave balance updated
        employee = leave.employee
        employee.refresh_from_db()
        # Balance should be reduced by 4 days
```

---

## 8. Cross-Module Integration Tests

### 8.1 TEST-CROSS-001: End-to-End Customer Journey

```python
@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndCustomerJourney:
    """
    Complete customer journey from order to delivered repaired bit.
    Crosses: Sales, Workorders, Inventory, Quality, Dispatch modules.
    """

    def test_complete_customer_journey(self):
        """Full journey taking ~15 minutes of simulated time."""
        # 1. Customer places order
        order = self._create_sales_order()

        # 2. Order triggers work order
        work_order = self._verify_work_order_created(order)

        # 3. Materials issued
        self._verify_materials_issued(work_order)

        # 4. Production completed
        self._complete_production(work_order)

        # 5. QC inspection passed
        self._complete_qc_inspection(work_order)

        # 6. Order shipped
        dispatch = self._ship_order(order)

        # 7. Delivery confirmed
        self._confirm_delivery(dispatch)

        # Final verification
        order.refresh_from_db()
        assert order.status == 'DELIVERED'

        # Verify all related records consistent
        self._verify_data_consistency(order)
```

---

## 9. Data Integrity Tests

### 9.1 Constraint Validation Tests

```python
@pytest.mark.integration
class TestDataIntegrity:

    def test_unique_constraints(self):
        """Verify unique constraints enforced."""
        DrillBit.objects.create(serial_number='UNIQUE-001', bit_type='PDC')

        with pytest.raises(IntegrityError):
            DrillBit.objects.create(serial_number='UNIQUE-001', bit_type='RC')

    def test_foreign_key_protection(self):
        """Verify protected foreign keys."""
        # Can't delete inventory item with transactions
        item = InventoryItem.objects.create(code='PROTECTED-001')
        InventoryTransaction.objects.create(item=item, quantity=10)

        with pytest.raises(ProtectedError):
            item.delete()

    def test_cascade_deletion(self):
        """Verify cascade deletes work correctly."""
        order = SalesOrder.objects.create(customer=self.customer)
        line = SalesOrderLine.objects.create(sales_order=order)

        order.delete()
        assert not SalesOrderLine.objects.filter(pk=line.pk).exists()

    def test_audit_trail_completeness(self):
        """Verify all changes logged."""
        drill_bit = DrillBit.objects.create(serial_number='AUDIT-001')

        # Make several changes
        drill_bit.status = 'IN_REPAIR'
        drill_bit.save()
        drill_bit.status = 'READY'
        drill_bit.save()

        # Verify audit log entries
        logs = AuditLog.objects.filter(
            entity_type='DrillBit',
            entity_id=drill_bit.id
        )
        assert logs.count() >= 3  # Create + 2 updates
```

---

## 10. Performance & Load Tests

### 10.1 Response Time Tests

```python
@pytest.mark.performance
class TestPerformance:

    def test_work_order_list_performance(self):
        """Work order list should load < 500ms with 10K records."""
        # Create 10K work orders
        WorkOrderFactory.create_batch(10000)

        start = time.time()
        response = self.client.get('/api/workorders/')
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.5  # 500ms

    def test_report_generation_performance(self):
        """Monthly report should generate < 30 seconds."""
        start = time.time()
        response = self.client.post('/api/reports/monthly/', {
            'month': '2024-12',
        })
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 30

    def test_concurrent_transactions(self):
        """System handles 50 concurrent inventory transactions."""
        import threading

        errors = []

        def make_transaction():
            try:
                InventoryTransaction.objects.create(
                    item=self.item,
                    quantity=1,
                    transaction_type='ISSUE',
                )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=make_transaction) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
```

---

**Document Control:**
- Created: December 2024
- Review Cycle: Per Release
- Owner: QA Team
- Classification: Internal Technical
