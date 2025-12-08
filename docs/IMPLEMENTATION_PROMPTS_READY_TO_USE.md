# 🚀 IMPLEMENTATION PROMPTS - READY TO USE

**Use these prompts in Claude web code to implement recommendations from the analysis report.**

---

## 📋 PROMPT 1: TEST REFACTORING (ELIMINATE 60% DUPLICATION)

Copy-paste this into Claude web code:

```
TASK: Eliminate test code duplication by creating base test classes

CONTEXT:
Current test suite has 19,823 lines with ~60% duplication. Same patterns repeated across all apps:
- Login required tests (100+ occurrences)
- Returns 200 tests (150+ occurrences)  
- Template tests (80+ occurrences)
- Context tests (70+ occurrences)

DELIVERABLE 1: Create Base Test Classes
File: apps/common/tests/base.py

Include:
1. BaseCRUDTest - Reusable CRUD test methods (list, detail, create, update, delete)
2. BaseFormTest - Reusable form validation tests
3. BasePermissionTest - Reusable permission tests

Requirements:
- Use pytest fixtures
- Parameterizable (model, app_name, model_name, create_data)
- Comprehensive assertions
- Clear docstrings

DELIVERABLE 2: Refactor Compliance App Tests
Update apps/compliance/tests/test_views.py to use BaseCRUDTest

Before: 825 lines with duplicated patterns
After: ~150 lines using inheritance

DELIVERABLE 3: Create Migration Guide
Document in apps/common/tests/REFACTORING_GUIDE.md:
- How to use base classes
- Examples for each test type
- Migration checklist for remaining apps

VERIFICATION:
After refactoring, run: pytest apps/compliance/tests/ -v
All tests must still pass.

Report:
- Lines before vs after
- Tests passing/failing
- Time to refactor

BEGIN with creating base.py. Show complete file.
```

---

## 📋 PROMPT 2: DRILL BIT LIFECYCLE INTEGRATION TEST

Copy-paste this into Claude web code:

```
TASK: Create end-to-end workflow integration test for Drill Bit Complete Lifecycle

CONTEXT:
Current "workflow" tests are unit tests. Need true integration tests that simulate real user workflows through the system.

DELIVERABLE: Create apps/common/tests/test_workflow_drill_bit_lifecycle.py

Test name: TestDrillBitCompleteLifecycle

Test method: test_complete_lifecycle_success

WORKFLOW STEPS (all via authenticated_client HTTP requests):

STEP 1: RECEIVE BIT (Warehouse)
- POST to drillbit create endpoint
- Data: serial_number='TEST-DB-LIFECYCLE-001', status='NEW'
- Assert: bit.physical_status == 'AT_ARDT'
- Assert: bit.accounting_status == 'ARDT_OWNED'

STEP 2: INCOMING QC INSPECTION
- POST to qualitycontrol create endpoint
- Data: inspection_type='INCOMING', result='PASS', drill_bit=bit.pk
- Assert: bit.status == 'AVAILABLE'
- Assert: QualityControl record created

STEP 3: CREATE CUSTOMER ORDER
- POST to customer create (if needed)
- POST to salesorder create
- POST to salesorderline create with drill_bit=bit.pk
- Assert: bit.accounting_status == 'CUSTOMER_RENTED'

STEP 4: SHIP TO RIG
- POST to shipment create
- Assert: bit.physical_status == 'AT_CUSTOMER'

STEP 5: CREATE DRILL RUN
- POST to drillstringrun create with bit=bit.pk
- Assert: run.status == 'IN_PROGRESS'

STEP 6: LOG RUN HOURS
- POST to runhours create with run=run.pk, hours=48.5
- Assert: run.total_hours == 48.5

STEP 7: COMPLETE RUN
- POST to drillstringrun update with status='COMPLETED'
- Assert: run.status == 'COMPLETED'

STEP 8: FIELD INSPECTION
- POST to fieldinspection create
- Data: drill_bit=bit.pk, result='REPAIR_NEEDED'
- Assert: inspection created

STEP 9: CREATE REPAIR WORK ORDER
- POST to workorder create
- Data: drill_bit=bit.pk, work_order_type='REPAIR'
- Assert: bit.status == 'IN_REPAIR'

STEP 10: COMPLETE REPAIR
- POST to workorder update with status='COMPLETED'
- Assert: bit.status == 'AVAILABLE'

STEP 11: RETURN TO WAREHOUSE
- Update bit.physical_status = 'AT_ARDT'
- Update bit.accounting_status = 'ARDT_OWNED'

STEP 12: FINAL QC INSPECTION
- POST to qualitycontrol create
- Data: inspection_type='RETURNED_GOODS', result='PASS'

STEP 13: GENERATE INVOICE
- POST to invoice create
- Assert: invoice.amount calculated from rental hours

FINAL VERIFICATION:
- assert bit.drillstringrun_set.count() == 1
- assert bit.fieldinspection_set.count() == 1  
- assert bit.workorder_set.count() == 1
- assert bit.qualitycontrol_set.count() == 2
- Print: "✅ Complete lifecycle verified: {bit.serial_number}"

REQUIREMENTS:
- Use authenticated_client.post() for all steps
- Verify response.status_code after each step
- Refresh objects from DB: obj.refresh_from_db()
- Use proper URL reversing: reverse('app:view_name')
- Handle any foreign key requirements (create related objects as needed)
- Add detailed comments explaining each step

BEGIN with complete test file. Make it production-ready.
```

---

## 📋 PROMPT 3: PERFORMANCE & QUERY OPTIMIZATION TESTS

Copy-paste this into Claude web code:

```
TASK: Add performance tests to catch N+1 queries and slow pages

DELIVERABLE: Create apps/common/tests/test_performance.py

SECTION 1: Query Count Tests

For these views, test query count with 100 records:
- sales:customer_list
- sales:salesorder_list  
- workorders:workorder_list
- compliance:compliancerequirement_list

Pattern:
```python
@pytest.mark.django_db
def test_customer_list_query_count(authenticated_client, user):
    """Test customer list doesn't have N+1 queries"""
    # Create 100 customers
    for i in range(100):
        Customer.objects.create(
            name=f'Customer {i}',
            code=f'CUST{i:03d}',
            customer_type='OPERATOR',
            is_active=True,
            created_by=user
        )
    
    # Should be max 5-10 queries regardless of record count
    from django.test.utils import CaptureQueriesContext
    from django.db import connection
    
    with CaptureQueriesContext(connection) as queries:
        response = authenticated_client.get(reverse('sales:customer_list'))
        assert response.status_code == 200
    
    query_count = len(queries)
    assert query_count <= 10, f"Too many queries: {query_count} (limit: 10)"
    
    # Log queries for debugging
    if query_count > 5:
        print(f"⚠️  Query count: {query_count}")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query['sql'][:100]}...")
```

SECTION 2: Page Load Time Tests

Test these views load under 2 seconds with 1000 records:
- List views for major models
- Detail views with many related objects
- Dashboard

Pattern:
```python
@pytest.mark.slow
@pytest.mark.django_db
def test_customer_list_load_time(authenticated_client, user):
    """Test customer list loads under 2 seconds with 1000 records"""
    import time
    
    # Create 1000 customers
    customers = [
        Customer(
            name=f'Customer {i}',
            code=f'CUST{i:04d}',
            customer_type='OPERATOR',
            is_active=True,
            created_by=user
        )
        for i in range(1000)
    ]
    Customer.objects.bulk_create(customers)
    
    # Measure load time
    start = time.time()
    response = authenticated_client.get(reverse('sales:customer_list'))
    duration = time.time() - start
    
    assert response.status_code == 200
    assert duration < 2.0, f"Page took {duration:.2f}s (limit: 2.0s)"
    print(f"✅ Load time: {duration:.2f}s")
```

SECTION 3: Optimization Tests

Test views use select_related/prefetch_related:

```python
@pytest.mark.django_db
def test_salesorder_detail_optimized(authenticated_client, user, customer):
    """Test sales order detail uses prefetch_related for lines"""
    
    # Create order with 20 lines
    order = SalesOrder.objects.create(
        customer=customer,
        order_number='ORD-TEST-001',
        created_by=user
    )
    
    for i in range(20):
        SalesOrderLine.objects.create(
            order=order,
            line_number=i+1,
            quantity=1
        )
    
    # Should only need 2-3 queries (order + prefetch lines)
    from django.test.utils import CaptureQueriesContext
    from django.db import connection
    
    with CaptureQueriesContext(connection) as queries:
        response = authenticated_client.get(
            reverse('sales:salesorder_detail', args=[order.pk])
        )
        assert response.status_code == 200
    
    query_count = len(queries)
    assert query_count <= 5, f"Not optimized: {query_count} queries (should be ~3)"
```

REQUIREMENTS:
- Use pytest markers (@pytest.mark.slow for time tests)
- Print actual query counts for debugging
- Test with realistic data volumes
- Test both small (10) and large (1000) datasets
- Add fixtures for test data creation

If any tests fail, suggest view optimizations (select_related, prefetch_related).

BEGIN with complete file showing all patterns.
```

---

## 📋 PROMPT 4: CUSTOMER ORDER TO INVOICE WORKFLOW

Copy-paste this into Claude web code:

```
TASK: Create integration test for Customer Order to Invoice workflow

DELIVERABLE: apps/common/tests/test_workflow_order_to_invoice.py

Test name: TestCustomerOrderToInvoiceWorkflow

WORKFLOW:

STEP 1: Create Customer
- POST to customer create
- Data: name='Test Drilling Co', code='TEST-001', customer_type='OPERATOR'
- Verify: customer created successfully

STEP 2: Create Service Site
- POST to servicesite create  
- Data: customer=customer.pk, site_code='RIG-001', site_type='RIG_SITE'
- Verify: site created and linked to customer

STEP 3: Create Sales Order
- POST to salesorder create
- Data: customer=customer.pk, order_number='ORD-001', order_date=today
- Verify: order.status == 'DRAFT'

STEP 4: Add Order Lines (3 drill bits)
- Create 3 drill bits (if not exist)
- POST to salesorderline create 3 times
- Data: order=order.pk, drill_bit=bit.pk, quantity=1, rental_rate=50.00
- Verify: order.lines.count() == 3

STEP 5: Submit Order for Approval
- POST to salesorder update
- Data: status='SUBMITTED'
- Verify: order.status == 'SUBMITTED'

STEP 6: Approve Order (Manager)
- Login as manager user
- POST to salesorder update
- Data: status='APPROVED', approved_by=manager.pk
- Verify: order.status == 'APPROVED'
- Verify: All bits.accounting_status == 'CUSTOMER_RENTED'

STEP 7: Create Shipment
- POST to shipment create
- Data: order=order.pk, shipped_date=today
- Verify: shipment created
- Verify: All bits.physical_status == 'AT_CUSTOMER'

STEP 8: Bits Used in Drilling (48 hours each)
- For each bit, create drill run
- Create run hours entries totaling 48 hours
- Verify: run.total_hours == 48.0

STEP 9: Return Shipment
- POST to shipment update
- Data: returned_date=today + 7 days
- Verify: All bits.physical_status == 'AT_ARDT'

STEP 10: Generate Invoice
- POST to invoice create
- Data: order=order.pk, calculate from rental hours
- Verify: invoice.total_amount == 3 bits × 48 hours × $50/hr = $7,200

STEP 11: Customer Payment
- POST to payment create
- Data: invoice=invoice.pk, amount=$7,200
- Verify: invoice.status == 'PAID'
- Verify: invoice.paid_date is not None

FINAL VERIFICATION:
- assert customer.salesorder_set.count() == 1
- assert order.lines.count() == 3
- assert order.invoice_set.count() == 1
- assert invoice.payment_set.count() == 1
- assert invoice.status == 'PAID'
- assert all(bit.accounting_status == 'ARDT_OWNED' for bit in bits)

Print complete audit trail of the transaction.

BEGIN with complete test file.
```

---

## 📋 PROMPT 5: QUALITY ISSUE RESOLUTION WORKFLOW

Copy-paste this into Claude web code:

```
TASK: Create integration test for Quality Issue (NCR) Resolution workflow

DELIVERABLE: apps/common/tests/test_workflow_ncr_resolution.py

Test name: TestNonConformanceResolutionWorkflow

WORKFLOW:

STEP 1: Operator Discovers Issue
- Create drill bit with issue
- POST to nonconformance create
- Data: 
  * title='Bearing failure'
  * severity='MAJOR'
  * description='Bearing seized during operation'
  * detected_by=operator.pk
  * drill_bit=bit.pk
- Verify: ncr.status == 'OPEN'
- Verify: Notification sent to QC manager

STEP 2: QC Manager Reviews NCR
- Login as QC manager
- POST to nonconformance update
- Data: assigned_to=qc_inspector.pk, status='ASSIGNED'
- Verify: ncr.assigned_to == qc_inspector
- Verify: Email sent to inspector

STEP 3: Inspector Investigates
- Login as QC inspector
- POST to qualitycontrol create (inspection)
- Data: 
  * inspection_type='FAILURE_ANALYSIS'
  * drill_bit=bit.pk
  * findings='Insufficient lubrication, contamination detected'
- POST to nonconformance update
- Data: investigation_notes='Root cause: improper maintenance procedure'
- Verify: ncr.status == 'INVESTIGATING'

STEP 4: Root Cause Analysis
- POST to nonconformance update
- Data:
  * root_cause='MAINTENANCE_PROCEDURE'
  * root_cause_details='Maintenance checklist missing lubrication step'
  * status='ROOT_CAUSE_IDENTIFIED'
- Verify: analysis complete

STEP 5: Corrective Actions
- POST to nonconformance update
- Data:
  * corrective_action='Update maintenance checklist'
  * responsible_party=maintenance_supervisor.pk
  * target_completion_date=today + 30 days
  * status='CORRECTIVE_ACTION_PLANNED'
- Verify: corrective action assigned

STEP 6: Implement Corrective Action
- Update maintenance checklist document
- POST to documentcontrol create
- Data: 
  * document_type='PROCEDURE'
  * title='Drill Bit Maintenance Checklist v2.0'
  * version='2.0'
- POST to nonconformance update
- Data: 
  * corrective_action_completed=True
  * actual_completion_date=today + 15 days
  * status='CORRECTIVE_ACTION_IMPLEMENTED'

STEP 7: Verification
- Login as QC manager
- POST to nonconformance update
- Data:
  * verification_method='Audit 5 maintenance operations'
  * verification_date=today + 20 days
  * verification_result='EFFECTIVE'
  * status='VERIFIED'
- Verify: ncr.status == 'VERIFIED'

STEP 8: Close NCR
- POST to nonconformance update
- Data:
  * status='CLOSED'
  * closed_date=today + 21 days
  * closed_by=qc_manager.pk
- Verify: ncr.status == 'CLOSED'
- Verify: Total time from OPEN to CLOSED is tracked

STEP 9: Preventive Actions
- POST to trainingrecord create
- Data:
  * training_course='Updated Maintenance Procedures'
  * employee=all_maintenance_techs
  * completion_date=today + 30 days
- Verify: All techs trained on new procedure

FINAL VERIFICATION:
- assert ncr.status == 'CLOSED'
- assert ncr.corrective_action_completed == True
- assert ncr.verification_result == 'EFFECTIVE'
- assert DocumentControl v2.0 exists
- assert All maintenance techs have training record
- Calculate and print resolution time

Print complete NCR lifecycle report.

BEGIN with complete test file.
```

---

## 📋 PROMPT 6: RUN ALL TESTS & GENERATE COVERAGE REPORT

Copy-paste this into Claude web code:

```
TASK: Run complete test suite and generate coverage report

STEP 1: Run All Tests
Bash pytest -v --tb=short --maxfail=3 --durations=10

Report:
- Total tests run
- Tests passed/failed
- 10 slowest tests
- Any failures with traceback

STEP 2: Run with Coverage
Bash pytest --cov=apps --cov-report=html --cov-report=term

Report:
- Coverage percentage per app
- Untested lines
- Critical files with <80% coverage

STEP 3: Run Specific Test Categories

Unit tests only:
Bash pytest -v -m "not slow and not integration"

Integration tests:
Bash pytest -v -m "integration"

Slow/Performance tests:
Bash pytest -v -m "slow"

STEP 4: Generate Reports

Create TEST_RESULTS.md with:
- Summary statistics
- Coverage by app
- Failed tests (if any)
- Recommendations for improving coverage
- Performance bottlenecks found

STEP 5: Fix Critical Failures

If any tests fail:
1. Identify root cause
2. Fix code or test
3. Re-run failed tests: pytest --lf (last failed)
4. Verify fix doesn't break other tests

SUCCESS CRITERIA:
- All tests pass (100%)
- Coverage >80% for each app
- No tests >5 seconds (except marked @slow)
- No N+1 query issues

Report final status with recommendations.
```

---

## 📋 PROMPT 7: CREATE TEST SUMMARY DASHBOARD

Copy-paste this into Claude web code:

```
TASK: Create visual test summary dashboard

DELIVERABLE: Create docs/testing/TEST_DASHBOARD.md

Include:

SECTION 1: Test Statistics Table
| App | Files | Tests | Lines | Coverage | Status |
|-----|-------|-------|-------|----------|--------|
| compliance | 7 | 245 | 5,651 | 87% | ✅ |
| workorders | 6 | 189 | 4,367 | 82% | ✅ |
| ... for all apps

SECTION 2: Test Distribution Chart (ASCII)
```
Test Types Distribution:
Unit Tests:      ████████████████████ 60% (520)
Integration:     ████████░░░░░░░░░░░░ 25% (217)
Workflow:        ████░░░░░░░░░░░░░░░░ 10% (87)
Performance:     ██░░░░░░░░░░░░░░░░░░  5% (43)
```

SECTION 3: Coverage by Category
```
Models:     ████████████████████ 95%
Views:      ██████████████████░░ 88%
Forms:      ████████████████░░░░ 82%
Templates:  ████████████░░░░░░░░ 65%
URLs:       ████████████████████ 100%
```

SECTION 4: Critical Metrics
- Total tests: 867
- Tests passing: 867 (100%)
- Average test time: 0.12s
- Slowest test: 4.8s (test_order_invoice_workflow)
- Coverage: 85%

SECTION 5: Recent Test Runs
| Date | Tests | Passed | Failed | Duration | Coverage |
|------|-------|--------|--------|----------|----------|
| Dec 8 | 867 | 867 | 0 | 104s | 85% |

SECTION 6: Action Items
- [ ] Increase template coverage to >75%
- [ ] Add 5 more workflow tests
- [ ] Optimize slowest tests
- [ ] Fix any flaky tests

Update this dashboard after every significant test run.
```

---

## 🎯 USAGE INSTRUCTIONS

1. **Use prompts IN ORDER** - They build on each other
2. **One prompt per session** - Don't combine
3. **Verify after each** - Run tests to confirm
4. **Save outputs** - Document what was created
5. **Iterate if needed** - Refine based on results

---

## ⏱️ ESTIMATED TIME PER PROMPT

| Prompt | Estimated Time | Priority |
|--------|---------------|----------|
| 1. Test Refactoring | 2-3 days | ⚠️ HIGH |
| 2. Drill Bit Workflow | 4-6 hours | ⚠️ HIGH |
| 3. Performance Tests | 3-4 hours | 🔶 MEDIUM |
| 4. Order to Invoice | 4-6 hours | ⚠️ HIGH |
| 5. NCR Resolution | 4-6 hours | 🔶 MEDIUM |
| 6. Run All Tests | 2-3 hours | ⚠️ HIGH |
| 7. Test Dashboard | 1-2 hours | 🟢 LOW |

**Total:** ~3-4 days of focused work

---

## ✅ SUCCESS CRITERIA

After completing all prompts:

- [ ] Test code reduced from 19,823 → ~8,000 lines
- [ ] All tests passing (100%)
- [ ] Coverage >80% per app
- [ ] 5+ workflow integration tests
- [ ] Performance tests catching N+1 queries
- [ ] Test dashboard showing current status
- [ ] Documentation updated

---

**These prompts are production-ready.** Use them in Claude web code to systematically improve your test suite.

