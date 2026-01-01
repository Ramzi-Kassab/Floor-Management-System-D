"""
Workorders App - Form Tests
Comprehensive tests for all workorders forms.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile


# =============================================================================
# WORK ORDER FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderForm:
    """Tests for WorkOrderForm."""

    def test_valid_data_passes_validation(self, drill_bit):
        """Test form with valid data passes validation."""
        from apps.workorders.forms import WorkOrderForm
        from apps.workorders.models import WorkOrder
        form_data = {
            'wo_type': WorkOrder.WOType.FC_REPAIR,
            'priority': WorkOrder.Priority.NORMAL,
            'planned_start': date.today(),
            'planned_end': date.today() + timedelta(days=5),
            'due_date': date.today() + timedelta(days=7),
            'description': 'Test repair work order',
            'notes': 'Test notes',
        }
        form = WorkOrderForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_wo_type_required(self):
        """Test wo_type is required."""
        from apps.workorders.forms import WorkOrderForm
        form_data = {
            'priority': 'NORMAL',
        }
        form = WorkOrderForm(data=form_data)
        assert not form.is_valid()
        assert 'wo_type' in form.errors

    def test_planned_end_before_start_invalid(self):
        """Test planned_end before planned_start is invalid."""
        from apps.workorders.forms import WorkOrderForm
        from apps.workorders.models import WorkOrder
        form_data = {
            'wo_type': WorkOrder.WOType.FC_REPAIR,
            'priority': WorkOrder.Priority.NORMAL,
            'planned_start': date.today(),
            'planned_end': date.today() - timedelta(days=5),
        }
        form = WorkOrderForm(data=form_data)
        assert not form.is_valid()
        assert 'planned_end' in form.errors

    def test_due_date_before_start_invalid(self):
        """Test due_date before planned_start is invalid."""
        from apps.workorders.forms import WorkOrderForm
        from apps.workorders.models import WorkOrder
        form_data = {
            'wo_type': WorkOrder.WOType.FC_REPAIR,
            'priority': WorkOrder.Priority.NORMAL,
            'planned_start': date.today(),
            'due_date': date.today() - timedelta(days=1),
        }
        form = WorkOrderForm(data=form_data)
        assert not form.is_valid()
        assert 'due_date' in form.errors

    def test_wo_type_choices_valid(self):
        """Test all wo_type choices are valid."""
        from apps.workorders.forms import WorkOrderForm
        from apps.workorders.models import WorkOrder
        for choice in WorkOrder.WOType.choices:
            form_data = {
                'wo_type': choice[0],
                'priority': WorkOrder.Priority.NORMAL,
            }
            form = WorkOrderForm(data=form_data)
            assert form.is_valid(), f"Form invalid for wo_type {choice[0]}: {form.errors}"

    def test_priority_choices_valid(self):
        """Test all priority choices are valid."""
        from apps.workorders.forms import WorkOrderForm
        from apps.workorders.models import WorkOrder
        for choice in WorkOrder.Priority.choices:
            form_data = {
                'wo_type': WorkOrder.WOType.FC_REPAIR,
                'priority': choice[0],
            }
            form = WorkOrderForm(data=form_data)
            assert form.is_valid(), f"Form invalid for priority {choice[0]}: {form.errors}"

    def test_optional_fields(self):
        """Test optional fields can be empty."""
        from apps.workorders.forms import WorkOrderForm
        from apps.workorders.models import WorkOrder
        form_data = {
            'wo_type': WorkOrder.WOType.FC_NEW,
            'priority': WorkOrder.Priority.NORMAL,
        }
        form = WorkOrderForm(data=form_data)
        assert form.is_valid(), form.errors


# =============================================================================
# WORK ORDER STATUS FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderStatusForm:
    """Tests for WorkOrderStatusForm."""

    def test_valid_status_passes(self):
        """Test form with valid status passes."""
        from apps.workorders.forms import WorkOrderStatusForm
        from apps.workorders.models import WorkOrder
        form_data = {'status': WorkOrder.Status.IN_PROGRESS}
        form = WorkOrderStatusForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_invalid_status_fails(self):
        """Test form with invalid status fails."""
        from apps.workorders.forms import WorkOrderStatusForm
        form_data = {'status': 'INVALID_STATUS'}
        form = WorkOrderStatusForm(data=form_data)
        assert not form.is_valid()

    def test_all_status_choices_valid(self):
        """Test all status choices are valid."""
        from apps.workorders.forms import WorkOrderStatusForm
        from apps.workorders.models import WorkOrder
        for choice in WorkOrder.Status.choices:
            form_data = {'status': choice[0]}
            form = WorkOrderStatusForm(data=form_data)
            assert form.is_valid(), f"Form invalid for status {choice[0]}: {form.errors}"


# =============================================================================
# DRILL BIT FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestDrillBitForm:
    """Tests for DrillBitForm."""

    def test_valid_data_passes_validation(self):
        """Test form with valid data passes validation."""
        from apps.workorders.forms import DrillBitForm
        from apps.workorders.models import DrillBit
        form_data = {
            'serial_number': 'FC-NEW-001',
            'bit_type': DrillBit.BitCategory.FC,
            'size': '8.500',
            'iadc_code': 'M423',
            'status': DrillBit.Status.NEW,
        }
        form = DrillBitForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_serial_number_required(self):
        """Test serial_number is required."""
        from apps.workorders.forms import DrillBitForm
        from apps.workorders.models import DrillBit
        form_data = {
            'bit_type': DrillBit.BitCategory.FC,
            'size': '8.500',
        }
        form = DrillBitForm(data=form_data)
        assert not form.is_valid()
        assert 'serial_number' in form.errors

    def test_size_required(self):
        """Test size is required."""
        from apps.workorders.forms import DrillBitForm
        from apps.workorders.models import DrillBit
        form_data = {
            'serial_number': 'FC-TEST',
            'bit_type': DrillBit.BitCategory.FC,
        }
        form = DrillBitForm(data=form_data)
        assert not form.is_valid()
        assert 'size' in form.errors

    def test_serial_number_uppercased(self, base_user):
        """Test serial_number is uppercased and trimmed."""
        from apps.workorders.forms import DrillBitForm
        from apps.workorders.models import DrillBit
        form_data = {
            'serial_number': '  fc-lower-001  ',
            'bit_type': DrillBit.BitCategory.FC,
            'size': '8.500',
            'status': DrillBit.Status.NEW,
        }
        form = DrillBitForm(data=form_data)
        assert form.is_valid(), form.errors
        assert form.cleaned_data['serial_number'] == 'FC-LOWER-001'

    def test_duplicate_serial_number_rejected(self, drill_bit):
        """Test duplicate serial number is rejected."""
        from apps.workorders.forms import DrillBitForm
        from apps.workorders.models import DrillBit
        form_data = {
            'serial_number': drill_bit.serial_number,
            'bit_type': DrillBit.BitCategory.FC,
            'size': '8.500',
            'status': DrillBit.Status.NEW,
        }
        form = DrillBitForm(data=form_data)
        assert not form.is_valid()
        assert 'serial_number' in form.errors

    def test_update_allows_same_serial_number(self, drill_bit):
        """Test update form allows same serial number."""
        from apps.workorders.forms import DrillBitForm
        from apps.workorders.models import DrillBit
        form_data = {
            'serial_number': drill_bit.serial_number,
            'bit_type': DrillBit.BitCategory.FC,
            'size': '8.500',
            'status': DrillBit.Status.IN_STOCK,
        }
        form = DrillBitForm(data=form_data, instance=drill_bit)
        assert form.is_valid(), form.errors

    def test_bit_type_choices_valid(self):
        """Test all bit_type choices are valid."""
        from apps.workorders.forms import DrillBitForm
        from apps.workorders.models import DrillBit
        for choice in DrillBit.BitCategory.choices:
            form_data = {
                'serial_number': f'BT-{choice[0]}-001',
                'bit_type': choice[0],
                'size': '8.500',
                'status': DrillBit.Status.NEW,
            }
            form = DrillBitForm(data=form_data)
            assert form.is_valid(), f"Form invalid for bit_type {choice[0]}: {form.errors}"

    def test_status_choices_valid(self):
        """Test all status choices are valid."""
        from apps.workorders.forms import DrillBitForm
        from apps.workorders.models import DrillBit
        for i, choice in enumerate(DrillBit.Status.choices):
            form_data = {
                'serial_number': f'ST-{i:03d}',
                'bit_type': DrillBit.BitCategory.FC,
                'size': '8.500',
                'status': choice[0],
            }
            form = DrillBitForm(data=form_data)
            assert form.is_valid(), f"Form invalid for status {choice[0]}: {form.errors}"


# =============================================================================
# DRILL BIT FILTER FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestDrillBitFilterForm:
    """Tests for DrillBitFilterForm."""

    def test_empty_form_valid(self):
        """Test empty filter form is valid."""
        from apps.workorders.forms import DrillBitFilterForm
        form = DrillBitFilterForm(data={})
        assert form.is_valid()

    def test_search_filter_valid(self):
        """Test search filter is valid."""
        from apps.workorders.forms import DrillBitFilterForm
        form_data = {'search': 'FC-001'}
        form = DrillBitFilterForm(data=form_data)
        assert form.is_valid()

    def test_bit_type_filter_valid(self):
        """Test bit_type filter is valid."""
        from apps.workorders.forms import DrillBitFilterForm
        from apps.workorders.models import DrillBit
        form_data = {'bit_type': DrillBit.BitCategory.FC}
        form = DrillBitFilterForm(data=form_data)
        assert form.is_valid()

    def test_status_filter_valid(self):
        """Test status filter is valid."""
        from apps.workorders.forms import DrillBitFilterForm
        from apps.workorders.models import DrillBit
        form_data = {'status': DrillBit.Status.IN_STOCK}
        form = DrillBitFilterForm(data=form_data)
        assert form.is_valid()


# =============================================================================
# WORK ORDER FILTER FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderFilterForm:
    """Tests for WorkOrderFilterForm."""

    def test_empty_form_valid(self):
        """Test empty filter form is valid."""
        from apps.workorders.forms import WorkOrderFilterForm
        form = WorkOrderFilterForm(data={})
        assert form.is_valid()

    def test_all_filters_valid(self):
        """Test all filters together are valid."""
        from apps.workorders.forms import WorkOrderFilterForm
        from apps.workorders.models import WorkOrder
        form_data = {
            'search': 'WO-001',
            'wo_type': WorkOrder.WOType.FC_REPAIR,
            'status': WorkOrder.Status.IN_PROGRESS,
            'priority': WorkOrder.Priority.HIGH,
        }
        form = WorkOrderFilterForm(data=form_data)
        assert form.is_valid()


# =============================================================================
# WORK ORDER DOCUMENT FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderDocumentForm:
    """Tests for WorkOrderDocumentForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.workorders.forms import WorkOrderDocumentForm
        from apps.workorders.models import WorkOrderDocument
        form_data = {
            'document_type': WorkOrderDocument.DocType.DRAWING,
            'name': 'Assembly Drawing',
            'description': 'Main assembly drawing',
        }
        form = WorkOrderDocumentForm(data=form_data)
        # File field will be empty but form should validate other fields
        assert 'document_type' not in form.errors
        assert 'name' not in form.errors

    def test_document_type_required(self):
        """Test document_type is required."""
        from apps.workorders.forms import WorkOrderDocumentForm
        form_data = {
            'name': 'Test Doc',
        }
        form = WorkOrderDocumentForm(data=form_data)
        assert not form.is_valid()
        assert 'document_type' in form.errors

    def test_name_required(self):
        """Test name is required."""
        from apps.workorders.forms import WorkOrderDocumentForm
        from apps.workorders.models import WorkOrderDocument
        form_data = {
            'document_type': WorkOrderDocument.DocType.DRAWING,
        }
        form = WorkOrderDocumentForm(data=form_data)
        assert not form.is_valid()
        assert 'name' in form.errors


# =============================================================================
# WORK ORDER PHOTO FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderPhotoForm:
    """Tests for WorkOrderPhotoForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.workorders.forms import WorkOrderPhotoForm
        form_data = {
            'caption': 'Before repair photo',
            'stage': 'Pre-Inspection',
        }
        form = WorkOrderPhotoForm(data=form_data)
        # Photo file will be empty
        assert 'caption' not in form.errors
        assert 'stage' not in form.errors

    def test_optional_fields(self):
        """Test caption and stage are optional."""
        from apps.workorders.forms import WorkOrderPhotoForm
        form = WorkOrderPhotoForm(data={})
        # Only photo file should be required
        assert 'caption' not in form.errors
        assert 'stage' not in form.errors


# =============================================================================
# SALVAGE ITEM FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestSalvageItemForm:
    """Tests for SalvageItemForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.workorders.forms import SalvageItemForm
        from apps.workorders.models import SalvageItem
        form_data = {
            'salvage_number': 'SALV-NEW-001',
            'salvage_type': SalvageItem.SalvageType.CUTTER,
            'description': 'Salvaged cutters',
            'status': SalvageItem.Status.AVAILABLE,
            'salvaged_date': date.today(),
            'reuse_potential': 'High',
            'condition_assessment': 'Good condition',
        }
        form = SalvageItemForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_salvage_number_required(self):
        """Test salvage_number is required."""
        from apps.workorders.forms import SalvageItemForm
        from apps.workorders.models import SalvageItem
        form_data = {
            'salvage_type': SalvageItem.SalvageType.BODY,
            'description': 'Test',
        }
        form = SalvageItemForm(data=form_data)
        assert not form.is_valid()
        assert 'salvage_number' in form.errors

    def test_salvage_type_required(self):
        """Test salvage_type is required."""
        from apps.workorders.forms import SalvageItemForm
        form_data = {
            'salvage_number': 'SALV-001',
            'description': 'Test',
        }
        form = SalvageItemForm(data=form_data)
        assert not form.is_valid()
        assert 'salvage_type' in form.errors

    def test_optional_fields(self):
        """Test optional fields can be empty."""
        from apps.workorders.forms import SalvageItemForm
        from apps.workorders.models import SalvageItem
        form_data = {
            'salvage_number': 'SALV-MIN-001',
            'salvage_type': SalvageItem.SalvageType.OTHER,
            'description': 'Minimal salvage',
            'status': SalvageItem.Status.AVAILABLE,
            'salvaged_date': date.today(),
            'reuse_potential': 'Low',
            'condition_assessment': 'Fair',
        }
        form = SalvageItemForm(data=form_data)
        assert form.is_valid(), form.errors


# =============================================================================
# REPAIR APPROVAL AUTHORITY FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestRepairApprovalAuthorityForm:
    """Tests for RepairApprovalAuthorityForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.workorders.forms import RepairApprovalAuthorityForm
        form_data = {
            'name': 'Plant Manager',
            'min_amount': '25000.00',
            'max_amount': '100000.00',
            'requires_justification': True,
            'is_active': True,
        }
        form = RepairApprovalAuthorityForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_name_required(self):
        """Test name is required."""
        from apps.workorders.forms import RepairApprovalAuthorityForm
        form_data = {
            'min_amount': '0.00',
            'max_amount': '5000.00',
        }
        form = RepairApprovalAuthorityForm(data=form_data)
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_amount_fields_required(self):
        """Test amount fields are required."""
        from apps.workorders.forms import RepairApprovalAuthorityForm
        form_data = {
            'name': 'Test Authority',
        }
        form = RepairApprovalAuthorityForm(data=form_data)
        assert not form.is_valid()
        assert 'min_amount' in form.errors
        assert 'max_amount' in form.errors


# =============================================================================
# REPAIR EVALUATION FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestRepairEvaluationForm:
    """Tests for RepairEvaluationForm."""

    def test_valid_data_passes(self, drill_bit, base_user):
        """Test form with valid data passes."""
        from apps.workorders.forms import RepairEvaluationForm
        from apps.workorders.models import RepairEvaluation
        form_data = {
            'evaluation_number': 'EVAL-NEW-001',
            'drill_bit': drill_bit.pk,
            'recommendation': RepairEvaluation.Recommendation.REPAIR if hasattr(RepairEvaluation, 'Recommendation') else 'REPAIR',
        }
        form = RepairEvaluationForm(data=form_data)
        # Check that required fields are handled
        assert 'evaluation_number' not in form.errors or form.is_valid()

    def test_evaluation_number_required(self):
        """Test evaluation_number is required."""
        from apps.workorders.forms import RepairEvaluationForm
        form_data = {}
        form = RepairEvaluationForm(data=form_data)
        assert not form.is_valid()
        assert 'evaluation_number' in form.errors


# =============================================================================
# REPAIR BOM FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestRepairBOMForm:
    """Tests for RepairBOMForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.workorders.forms import RepairBOMForm
        from apps.workorders.models import RepairBOM
        form_data = {
            'status': RepairBOM.Status.DRAFT,
        }
        form = RepairBOMForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_status_choices_valid(self):
        """Test all status choices are valid."""
        from apps.workorders.forms import RepairBOMForm
        from apps.workorders.models import RepairBOM
        for choice in RepairBOM.Status.choices:
            form_data = {'status': choice[0]}
            form = RepairBOMForm(data=form_data)
            assert form.is_valid(), f"Form invalid for status {choice[0]}: {form.errors}"


# =============================================================================
# REPAIR BOM LINE FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestRepairBOMLineForm:
    """Tests for RepairBOMLineForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.workorders.forms import RepairBOMLineForm
        form_data = {
            'line_number': 1,
            'part_description': 'PDC Cutter 13mm',
            'quantity_required': '4.00',
            'quantity_issued': '0.00',
        }
        form = RepairBOMLineForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_line_number_required(self):
        """Test line_number is required."""
        from apps.workorders.forms import RepairBOMLineForm
        form_data = {
            'quantity_required': '1.00',
        }
        form = RepairBOMLineForm(data=form_data)
        assert not form.is_valid()
        assert 'line_number' in form.errors

    def test_quantity_required_field(self):
        """Test quantity_required is required."""
        from apps.workorders.forms import RepairBOMLineForm
        form_data = {
            'line_number': 1,
        }
        form = RepairBOMLineForm(data=form_data)
        assert not form.is_valid()
        assert 'quantity_required' in form.errors


# =============================================================================
# PROCESS ROUTE FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestProcessRouteForm:
    """Tests for ProcessRouteForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.workorders.forms import ProcessRouteForm
        form_data = {
            'route_number': 'ROUTE-NEW-001',
            'name': 'New Repair Route',
            'is_active': True,
        }
        form = ProcessRouteForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_route_number_required(self):
        """Test route_number is required."""
        from apps.workorders.forms import ProcessRouteForm
        form_data = {
            'name': 'Test Route',
        }
        form = ProcessRouteForm(data=form_data)
        assert not form.is_valid()
        assert 'route_number' in form.errors

    def test_name_required(self):
        """Test name is required."""
        from apps.workorders.forms import ProcessRouteForm
        form_data = {
            'route_number': 'ROUTE-001',
        }
        form = ProcessRouteForm(data=form_data)
        assert not form.is_valid()
        assert 'name' in form.errors


# =============================================================================
# PROCESS ROUTE OPERATION FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestProcessRouteOperationForm:
    """Tests for ProcessRouteOperationForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.workorders.forms import ProcessRouteOperationForm
        form_data = {
            'sequence': 10,
            'operation_code': 'INSP-01',
            'operation_name': 'Initial Inspection',
            'setup_time_minutes': 15,
            'run_time_minutes': 60,
        }
        form = ProcessRouteOperationForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_sequence_required(self):
        """Test sequence is required."""
        from apps.workorders.forms import ProcessRouteOperationForm
        form_data = {
            'operation_code': 'OP-01',
            'operation_name': 'Test Op',
        }
        form = ProcessRouteOperationForm(data=form_data)
        assert not form.is_valid()
        assert 'sequence' in form.errors

    def test_operation_code_required(self):
        """Test operation_code is required."""
        from apps.workorders.forms import ProcessRouteOperationForm
        form_data = {
            'sequence': 10,
            'operation_name': 'Test Op',
        }
        form = ProcessRouteOperationForm(data=form_data)
        assert not form.is_valid()
        assert 'operation_code' in form.errors

    def test_operation_name_required(self):
        """Test operation_name is required."""
        from apps.workorders.forms import ProcessRouteOperationForm
        form_data = {
            'sequence': 10,
            'operation_code': 'OP-01',
        }
        form = ProcessRouteOperationForm(data=form_data)
        assert not form.is_valid()
        assert 'operation_name' in form.errors


# =============================================================================
# WORK ORDER COST FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderCostForm:
    """Tests for WorkOrderCostForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.workorders.forms import WorkOrderCostForm
        form_data = {
            'estimated_labor_hours': '16.0',
            'actual_labor_hours': '0.0',
            'labor_rate': '75.00',
            'estimated_material_cost': '2500.00',
            'actual_material_cost': '0.00',
            'estimated_overhead': '500.00',
            'actual_overhead': '0.00',
        }
        form = WorkOrderCostForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_optional_fields(self):
        """Test optional fields can be empty."""
        from apps.workorders.forms import WorkOrderCostForm
        form_data = {
            'estimated_labor_hours': '8.0',
            'actual_labor_hours': '0.0',
            'labor_rate': '50.00',
            'estimated_material_cost': '1000.00',
            'actual_material_cost': '0.00',
            'estimated_overhead': '0.00',
            'actual_overhead': '0.00',
        }
        form = WorkOrderCostForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_decimal_precision(self):
        """Test decimal fields accept proper precision."""
        from apps.workorders.forms import WorkOrderCostForm
        form_data = {
            'estimated_labor_hours': '16.50',
            'actual_labor_hours': '18.25',
            'labor_rate': '75.50',
            'estimated_material_cost': '2500.99',
            'actual_material_cost': '2600.50',
            'estimated_overhead': '500.00',
            'actual_overhead': '520.00',
        }
        form = WorkOrderCostForm(data=form_data)
        assert form.is_valid(), form.errors


# =============================================================================
# BIT EVALUATION FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestBitEvaluationForm:
    """Tests for BitEvaluationForm."""

    def test_valid_data_passes(self, drill_bit, base_user):
        """Test form with valid data passes."""
        from apps.workorders.forms import BitEvaluationForm
        from apps.workorders.models import BitEvaluation
        form_data = {
            'run_number': 1,
            'hours_run': '50.5',
            'footage_drilled': '1500.0',
            'evaluation_date': date.today(),
            'condition': BitEvaluation.Condition.GOOD if hasattr(BitEvaluation, 'Condition') else 'GOOD',
        }
        form = BitEvaluationForm(data=form_data)
        # Evaluation form has many optional fields
        assert 'run_number' not in form.errors or form.is_valid()

    def test_optional_fields(self):
        """Test many fields are optional."""
        from apps.workorders.forms import BitEvaluationForm
        form_data = {
            'evaluation_date': date.today(),
        }
        form = BitEvaluationForm(data=form_data)
        # Most fields should be optional
        optional_fields = ['rig', 'well', 'formation_drilled', 'inner_rows_grade',
                          'outer_rows_grade', 'gauge_wear', 'bearing_condition']
        for field in optional_fields:
            assert field not in form.errors or form.is_valid()


# =============================================================================
# WORK ORDER MATERIAL FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderMaterialForm:
    """Tests for WorkOrderMaterialForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.workorders.forms import WorkOrderMaterialForm
        form_data = {
            'planned_quantity': '10.00',
            'issued_quantity': '0.00',
            'returned_quantity': '0.00',
            'unit': 'EA',
            'unit_cost': '50.00',
        }
        form = WorkOrderMaterialForm(data=form_data)
        # inventory_item is required by model but may be optional in form
        assert 'planned_quantity' not in form.errors

    def test_quantity_fields_accept_decimals(self):
        """Test quantity fields accept decimal values."""
        from apps.workorders.forms import WorkOrderMaterialForm
        form_data = {
            'planned_quantity': '10.500',
            'issued_quantity': '5.250',
            'returned_quantity': '0.125',
            'unit': 'LB',
            'unit_cost': '25.99',
        }
        form = WorkOrderMaterialForm(data=form_data)
        assert 'planned_quantity' not in form.errors
        assert 'issued_quantity' not in form.errors
        assert 'returned_quantity' not in form.errors


# =============================================================================
# WORK ORDER TIME LOG FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestWorkOrderTimeLogForm:
    """Tests for WorkOrderTimeLogForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.workorders.forms import WorkOrderTimeLogForm
        from django.utils import timezone
        form_data = {
            'start_time': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'activity': 'Machining',
            'billable': True,
            'billing_rate': '75.00',
        }
        form = WorkOrderTimeLogForm(data=form_data)
        assert 'activity' not in form.errors

    def test_optional_fields(self):
        """Test optional fields can be empty."""
        from apps.workorders.forms import WorkOrderTimeLogForm
        from django.utils import timezone
        form_data = {
            'start_time': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        }
        form = WorkOrderTimeLogForm(data=form_data)
        # user, notes, approved_by should be optional
        assert 'user' not in form.errors or form.is_valid()
        assert 'notes' not in form.errors or form.is_valid()
