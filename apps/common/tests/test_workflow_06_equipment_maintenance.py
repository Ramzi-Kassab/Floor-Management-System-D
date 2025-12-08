"""
Equipment Maintenance Workflow Integration Test
================================================

Cross-App Integration:
- Maintenance: Equipment tracking and work orders
- Technology: Technical specifications and BOMs
- Inventory: Parts requisition and consumption
- Documents: Maintenance reports and documentation
- Notifications: Maintenance alerts and reminders

Workflow Steps:
1. Equipment due for maintenance is identified
2. Maintenance request is created
3. Maintenance is scheduled
4. Required parts are ordered from inventory
5. Maintenance work is performed
6. Equipment records are updated
7. Maintenance report is generated
8. Next maintenance date is scheduled

Author: Workflow Integration Suite
Date: December 2024
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def maintenance_manager(db):
    """Create maintenance manager user."""
    return User.objects.create_user(
        username='maint_manager',
        email='maintenance@ardt.com',
        password='maintpass123',
        first_name='Maintenance',
        last_name='Manager',
        is_staff=True
    )


@pytest.fixture
def technician(db):
    """Create maintenance technician user."""
    return User.objects.create_user(
        username='technician',
        email='tech@ardt.com',
        password='techpass123',
        first_name='John',
        last_name='Technician'
    )


@pytest.fixture
def equipment_category(db):
    """Create equipment category."""
    from apps.maintenance.models import EquipmentCategory
    return EquipmentCategory.objects.create(
        code='CNC',
        name='CNC Machines',
        description='Computer Numerical Control machines',
        is_active=True
    )


@pytest.fixture
def equipment_due_maintenance(db, equipment_category):
    """Create equipment that is due for maintenance."""
    from apps.maintenance.models import Equipment
    return Equipment.objects.create(
        code='CNC-LATHE-001',
        name='CNC Lathe Machine #1',
        category=equipment_category,
        manufacturer='DMG Mori',
        model='NLX 2500',
        serial_number='SN-2020-12345',
        year_of_manufacture=2020,
        location='Shop Floor A',
        status=Equipment.Status.OPERATIONAL,
        last_maintenance=date.today() - timedelta(days=90),  # 90 days ago
        next_maintenance=date.today() - timedelta(days=5),    # 5 days overdue
        maintenance_interval_days=90
    )


@pytest.fixture
def inventory_warehouse(db):
    """Create warehouse for parts inventory."""
    from apps.inventory.models import Warehouse
    return Warehouse.objects.create(
        code='WH-SPARE',
        name='Spare Parts Warehouse',
        is_active=True
    )


@pytest.fixture
def inventory_location(db, inventory_warehouse):
    """Create inventory location."""
    from apps.inventory.models import InventoryLocation
    return InventoryLocation.objects.create(
        warehouse=inventory_warehouse,
        code='SP-001',
        name='Spare Parts Shelf 1'
    )


@pytest.fixture
def spare_part(db, maintenance_manager):
    """Create a spare part for maintenance."""
    from apps.inventory.models import InventoryItem, InventoryCategory, InventoryStock

    category, _ = InventoryCategory.objects.get_or_create(
        code='SPARE',
        defaults={'name': 'Spare Parts', 'is_active': True}
    )

    item = InventoryItem.objects.create(
        code='FILTER-HYD-001',
        name='Hydraulic Filter',
        description='Replacement hydraulic filter for CNC machines',
        item_type=InventoryItem.ItemType.SPARE_PART,
        category=category,
        unit='EA',
        standard_cost=Decimal('75.00'),
        min_stock=Decimal('10.000'),
        is_active=True
    )

    return item


# =============================================================================
# EQUIPMENT MAINTENANCE WORKFLOW TESTS
# =============================================================================

@pytest.mark.django_db
class TestEquipmentMaintenanceWorkflow:
    """
    Complete equipment maintenance workflow test.

    Tests the full cycle from maintenance identification through
    completion and scheduling of next maintenance.
    """

    def test_full_preventive_maintenance_workflow(
        self,
        maintenance_manager,
        technician,
        equipment_due_maintenance,
        spare_part,
        inventory_warehouse,
        inventory_location
    ):
        """
        Test complete preventive maintenance workflow.

        Steps:
        1. Identify equipment due for maintenance
        2. Create maintenance request
        3. Approve and schedule maintenance
        4. Create maintenance work order
        5. Reserve/issue spare parts
        6. Perform maintenance work
        7. Complete and sign off
        8. Update equipment records
        9. Generate maintenance report
        10. Schedule next maintenance
        """
        from apps.maintenance.models import MaintenanceRequest, MaintenanceWorkOrder, MaintenancePartsUsed
        from apps.inventory.models import InventoryStock, InventoryTransaction
        from apps.documents.models import Document, DocumentCategory
        from apps.notifications.models import Notification

        print("\n" + "="*60)
        print("EQUIPMENT PREVENTIVE MAINTENANCE WORKFLOW")
        print("="*60)

        # ---------------------------------------------------------------------
        # STEP 1: Identify equipment due for maintenance
        # ---------------------------------------------------------------------
        print("\n[Step 1] Identifying equipment due for maintenance...")

        equipment = equipment_due_maintenance
        days_overdue = (date.today() - equipment.next_maintenance).days

        assert equipment.next_maintenance < date.today()
        print(f"  Equipment: {equipment.name}")
        print(f"  Code: {equipment.code}")
        print(f"  Last maintenance: {equipment.last_maintenance}")
        print(f"  Next scheduled: {equipment.next_maintenance}")
        print(f"  Days overdue: {days_overdue}")

        # Send maintenance due notification
        notification = Notification.objects.create(
            recipient=maintenance_manager,
            title=f'Maintenance Due: {equipment.code}',
            message=f'{equipment.name} is {days_overdue} days overdue for maintenance.',
            priority=Notification.Priority.HIGH,
            entity_type='maintenance.equipment',
            entity_id=equipment.pk
        )

        print(f"  Alert sent to: {maintenance_manager.username}")

        # ---------------------------------------------------------------------
        # STEP 2: Create maintenance request
        # ---------------------------------------------------------------------
        print("\n[Step 2] Creating maintenance request...")

        request = MaintenanceRequest.objects.create(
            request_number='MR-2024-001',
            equipment=equipment,
            request_type=MaintenanceRequest.RequestType.PREVENTIVE,
            priority=MaintenanceRequest.Priority.NORMAL,
            title=f'Scheduled PM - {equipment.name}',
            description='90-day preventive maintenance - Hydraulic system check, filter replacement, calibration',
            status=MaintenanceRequest.Status.PENDING,
            requested_by=maintenance_manager
        )

        assert request.pk is not None
        print(f"  Request number: {request.request_number}")
        print(f"  Type: {request.get_request_type_display()}")
        print(f"  Status: {request.get_status_display()}")

        # ---------------------------------------------------------------------
        # STEP 3: Approve and schedule maintenance
        # ---------------------------------------------------------------------
        print("\n[Step 3] Approving and scheduling maintenance...")

        request.status = MaintenanceRequest.Status.APPROVED
        request.approved_by = maintenance_manager
        request.approved_at = timezone.now()
        request.save()

        assert request.status == MaintenanceRequest.Status.APPROVED
        print(f"  Approved by: {maintenance_manager.username}")

        # ---------------------------------------------------------------------
        # STEP 4: Create maintenance work order
        # ---------------------------------------------------------------------
        print("\n[Step 4] Creating maintenance work order...")

        work_order = MaintenanceWorkOrder.objects.create(
            mwo_number='MWO-2024-001',
            equipment=equipment,
            request=request,
            title=request.title,
            description=request.description,
            status=MaintenanceWorkOrder.Status.PLANNED,
            planned_start=timezone.now(),
            planned_end=timezone.now() + timedelta(hours=4),
            assigned_to=technician,
            created_by=maintenance_manager
        )

        assert work_order.pk is not None
        print(f"  Work order: {work_order.mwo_number}")
        print(f"  Assigned to: {technician.username}")
        print(f"  Estimated time: 4 hours")

        # ---------------------------------------------------------------------
        # STEP 5: Reserve/issue spare parts
        # ---------------------------------------------------------------------
        print("\n[Step 5] Issuing spare parts from inventory...")

        # Create stock for spare part
        stock = InventoryStock.objects.create(
            item=spare_part,
            location=inventory_location,
            quantity_on_hand=Decimal('50.000'),
            quantity_reserved=Decimal('0.000'),
            quantity_available=Decimal('50.000')
        )

        parts_needed = Decimal('2.000')  # Need 2 filters

        # Reserve parts for work order
        stock.quantity_reserved += parts_needed
        stock.quantity_available -= parts_needed
        stock.save()

        # Record parts used
        parts_used = MaintenancePartsUsed.objects.create(
            work_order=work_order,
            item=spare_part,
            quantity_used=parts_needed,
            unit_cost=spare_part.standard_cost,
            total_cost=parts_needed * spare_part.standard_cost,
            issued_from=inventory_location
        )

        print(f"  Part: {spare_part.name}")
        print(f"  Quantity issued: {parts_needed}")
        print(f"  Cost: ${parts_used.total_cost}")

        # Issue from inventory
        issue_txn = InventoryTransaction.objects.create(
            transaction_number='TXN-MWO-001',
            transaction_type=InventoryTransaction.TransactionType.ISSUE,
            transaction_date=timezone.now(),
            item=spare_part,
            from_location=inventory_location,
            quantity=parts_needed,
            unit=spare_part.unit,
            unit_cost=spare_part.standard_cost,
            total_cost=parts_used.total_cost,
            link_type=InventoryTransaction.LinkType.WORK_ORDER,
            reference_number=work_order.mwo_number,
            notes=f'Parts for {work_order.mwo_number}',
            created_by=maintenance_manager
        )

        # Update stock
        stock.quantity_on_hand -= parts_needed
        stock.quantity_reserved -= parts_needed
        stock.save()

        print(f"  Inventory updated")

        # ---------------------------------------------------------------------
        # STEP 6: Perform maintenance work
        # ---------------------------------------------------------------------
        print("\n[Step 6] Starting maintenance work...")

        work_order.status = MaintenanceWorkOrder.Status.IN_PROGRESS
        work_order.actual_start = timezone.now()
        work_order.save()

        print(f"  Status: {work_order.get_status_display()}")
        print(f"  Started at: {work_order.actual_start}")

        # Simulate work being done
        # - Hydraulic filter replacement
        # - System fluid check
        # - Calibration verification

        # ---------------------------------------------------------------------
        # STEP 7: Complete and sign off
        # ---------------------------------------------------------------------
        print("\n[Step 7] Completing maintenance...")

        work_order.status = MaintenanceWorkOrder.Status.COMPLETED
        work_order.actual_end = timezone.now()
        work_order.completion_notes = '''
        Maintenance completed successfully:
        - Replaced 2x hydraulic filters
        - Checked hydraulic fluid level - OK
        - Performed axis calibration
        - Lubricated guide ways
        - All systems operational
        '''
        work_order.save()

        assert work_order.status == MaintenanceWorkOrder.Status.COMPLETED
        print(f"  Status: {work_order.get_status_display()}")
        print(f"  Completed at: {work_order.actual_end}")

        # ---------------------------------------------------------------------
        # STEP 8: Update equipment records
        # ---------------------------------------------------------------------
        print("\n[Step 8] Updating equipment records...")

        equipment.last_maintenance = date.today()
        equipment.next_maintenance = date.today() + timedelta(days=equipment.maintenance_interval_days)
        equipment.status = Equipment.Status.OPERATIONAL
        equipment.save()

        print(f"  Last maintenance: {equipment.last_maintenance}")
        print(f"  Next scheduled: {equipment.next_maintenance}")
        print(f"  Status: {equipment.get_status_display()}")

        # ---------------------------------------------------------------------
        # STEP 9: Generate maintenance report
        # ---------------------------------------------------------------------
        print("\n[Step 9] Generating maintenance report...")

        # Create document category if doesn't exist
        doc_category, _ = DocumentCategory.objects.get_or_create(
            code='MAINT-RPT',
            defaults={'name': 'Maintenance Reports', 'is_active': True}
        )

        # Create maintenance report document
        report_doc = Document.objects.create(
            code=f'DOC-{work_order.mwo_number}',
            name=f'Maintenance Report - {work_order.mwo_number}',
            category=doc_category,
            version='1.0',
            status=Document.Status.ACTIVE,
            description=f'''
            Preventive Maintenance Report
            Equipment: {equipment.code} - {equipment.name}
            Work Order: {work_order.mwo_number}
            Date: {date.today()}
            Technician: {technician.get_full_name()}

            Work Performed:
            {work_order.completion_notes}

            Parts Used:
            - {spare_part.name} x {parts_needed} @ ${spare_part.standard_cost}/ea

            Total Parts Cost: ${parts_used.total_cost}
            ''',
            owner=maintenance_manager
        )

        print(f"  Report created: {report_doc.code}")
        print(f"  Status: {report_doc.get_status_display()}")

        # ---------------------------------------------------------------------
        # STEP 10: Final verification
        # ---------------------------------------------------------------------
        print("\n[Step 10] Final verification...")

        # Update request status
        request.status = MaintenanceRequest.Status.COMPLETED
        request.save()

        # Mark notification as read
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()

        final_checks = {
            'request_completed': request.status == MaintenanceRequest.Status.COMPLETED,
            'work_order_completed': work_order.status == MaintenanceWorkOrder.Status.COMPLETED,
            'equipment_updated': equipment.last_maintenance == date.today(),
            'next_maintenance_scheduled': equipment.next_maintenance > date.today(),
            'parts_issued': issue_txn.pk is not None,
            'report_generated': report_doc.pk is not None,
            'notification_cleared': notification.is_read is True,
        }

        all_passed = all(final_checks.values())

        print("\n  Maintenance Summary:")
        print(f"    Equipment: {equipment.code}")
        print(f"    Work Order: {work_order.mwo_number}")
        print(f"    Duration: {work_order.actual_end - work_order.actual_start}")
        print(f"    Parts Cost: ${parts_used.total_cost}")

        print("\n  Workflow Checklist:")
        for check, status in final_checks.items():
            icon = "  " if status else "  "
            print(f"    {icon} {check.replace('_', ' ').title()}")

        assert all_passed

        print("\n" + "="*60)
        print("MAINTENANCE WORKFLOW COMPLETED SUCCESSFULLY!")
        print("="*60)


    def test_corrective_maintenance_workflow(
        self,
        maintenance_manager,
        technician,
        equipment_category
    ):
        """
        Test corrective/breakdown maintenance workflow.

        Tests unplanned maintenance due to equipment failure.
        """
        from apps.maintenance.models import Equipment, MaintenanceRequest, MaintenanceWorkOrder

        print("\n" + "="*60)
        print("CORRECTIVE MAINTENANCE WORKFLOW")
        print("="*60)

        # Step 1: Equipment breaks down
        print("\n[Step 1] Equipment breakdown reported...")

        equipment = Equipment.objects.create(
            code='PUMP-HYD-002',
            name='Hydraulic Pump #2',
            category=equipment_category,
            status=Equipment.Status.OPERATIONAL
        )

        # Equipment fails
        equipment.status = Equipment.Status.BREAKDOWN
        equipment.save()

        print(f"  Equipment: {equipment.name}")
        print(f"  Status: {equipment.get_status_display()}")

        # Step 2: Emergency request
        print("\n[Step 2] Creating emergency maintenance request...")

        request = MaintenanceRequest.objects.create(
            request_number='MR-EMERG-001',
            equipment=equipment,
            request_type=MaintenanceRequest.RequestType.BREAKDOWN,
            priority=MaintenanceRequest.Priority.URGENT,
            title='URGENT: Hydraulic pump failure',
            description='Pump showing no pressure output. Production halted.',
            status=MaintenanceRequest.Status.APPROVED,  # Auto-approved for emergency
            requested_by=maintenance_manager,
            approved_by=maintenance_manager,
            approved_at=timezone.now()
        )

        print(f"  Request: {request.request_number}")
        print(f"  Priority: {request.get_priority_display()}")

        # Step 3: Create urgent work order
        print("\n[Step 3] Creating urgent work order...")

        work_order = MaintenanceWorkOrder.objects.create(
            mwo_number='MWO-EMERG-001',
            equipment=equipment,
            request=request,
            title=request.title,
            description=request.description,
            status=MaintenanceWorkOrder.Status.IN_PROGRESS,
            actual_start=timezone.now(),
            assigned_to=technician,
            created_by=maintenance_manager
        )

        print(f"  Work order: {work_order.mwo_number}")
        print(f"  Started immediately")

        # Step 4: Complete repair
        print("\n[Step 4] Completing repair...")

        work_order.status = MaintenanceWorkOrder.Status.COMPLETED
        work_order.actual_end = timezone.now()
        work_order.completion_notes = 'Replaced faulty seal. Pump operational.'
        work_order.save()

        # Restore equipment
        equipment.status = Equipment.Status.OPERATIONAL
        equipment.save()

        print(f"  Repair completed")
        print(f"  Equipment status: {equipment.get_status_display()}")

        print("\n" + "="*60)
        print("CORRECTIVE MAINTENANCE COMPLETED!")
        print("="*60)


# =============================================================================
# WORKFLOW SUMMARY
# =============================================================================

@pytest.mark.django_db
class TestMaintenanceWorkflowSummary:
    """Summary tests for maintenance workflow."""

    def test_workflow_models_exist(self, db):
        """Verify all workflow models are accessible."""
        from apps.maintenance.models import Equipment, MaintenanceRequest, MaintenanceWorkOrder
        from apps.inventory.models import InventoryItem, InventoryStock
        from apps.documents.models import Document

        assert Equipment._meta.model_name == 'equipment'
        assert MaintenanceRequest._meta.model_name == 'maintenancerequest'
        assert MaintenanceWorkOrder._meta.model_name == 'maintenanceworkorder'
        assert InventoryItem._meta.model_name == 'inventoryitem'
        assert Document._meta.model_name == 'document'

        print("\nAll maintenance workflow models verified!")
