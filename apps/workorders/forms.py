"""
ARDT FMS - Work Orders Forms
Version: 5.4 - Sprint 1

Form definitions for work order and drill bit management.
"""

from django import forms
from django.core.exceptions import ValidationError

from .models import DrillBit, WorkOrder


class WorkOrderForm(forms.ModelForm):
    """
    Form for creating and editing work orders.
    """

    class Meta:
        model = WorkOrder
        fields = [
            "wo_type",
            "drill_bit",
            "design",
            "customer",
            "sales_order",
            "rig",
            "well",
            "priority",
            "planned_start",
            "planned_end",
            "due_date",
            "assigned_to",
            "department",
            "procedure",
            "description",
            "notes",
        ]
        widgets = {
            "wo_type": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "drill_bit": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "design": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "customer": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "sales_order": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "rig": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "well": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "planned_start": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                }
            ),
            "planned_end": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                }
            ),
            "assigned_to": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "department": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "procedure": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                    "placeholder": "Enter work order description...",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                    "placeholder": "Additional notes...",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        planned_start = cleaned_data.get("planned_start")
        planned_end = cleaned_data.get("planned_end")
        due_date = cleaned_data.get("due_date")

        # Validate date logic
        if planned_start and planned_end:
            if planned_end < planned_start:
                raise ValidationError({"planned_end": "Planned end date cannot be before planned start date."})

        if planned_start and due_date:
            if due_date < planned_start:
                raise ValidationError({"due_date": "Due date cannot be before planned start date."})

        return cleaned_data


class WorkOrderStatusForm(forms.Form):
    """
    Form for updating work order status (used with HTMX).
    """

    status = forms.ChoiceField(
        choices=WorkOrder.Status.choices,
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                "hx-post": "",
                "hx-target": "#status-badge",
                "hx-swap": "outerHTML",
            }
        ),
    )


class DrillBitForm(forms.ModelForm):
    """
    Form for creating and editing drill bits.
    """

    class Meta:
        model = DrillBit
        fields = [
            "serial_number",
            "bit_type",
            "design",
            "size",
            "iadc_code",
            "status",
            "current_location",
            "customer",
            "rig",
            "well",
        ]
        widgets = {
            "serial_number": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white font-mono",
                    "placeholder": "e.g., FC-2024-0001",
                }
            ),
            "bit_type": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "design": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "size": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                    "step": "0.001",
                    "placeholder": "Size in inches",
                }
            ),
            "iadc_code": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white font-mono",
                    "placeholder": "e.g., M423",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "current_location": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "customer": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "rig": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "well": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
        }

    def clean_serial_number(self):
        serial_number = self.cleaned_data.get("serial_number")
        if serial_number:
            serial_number = serial_number.upper().strip()
            # Check uniqueness (excluding current instance for updates)
            qs = DrillBit.objects.filter(serial_number=serial_number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A drill bit with this serial number already exists.")
        return serial_number


class DrillBitFilterForm(forms.Form):
    """
    Form for filtering drill bit list.
    """

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                "placeholder": "Search serial number...",
            }
        ),
    )
    bit_type = forms.ChoiceField(
        required=False,
        choices=[("", "All Types")] + list(DrillBit.BitType.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            }
        ),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All Statuses")] + list(DrillBit.Status.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            }
        ),
    )


class WorkOrderFilterForm(forms.Form):
    """
    Form for filtering work order list.
    """

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                "placeholder": "Search WO number...",
            }
        ),
    )
    wo_type = forms.ChoiceField(
        required=False,
        choices=[("", "All Types")] + list(WorkOrder.WOType.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            }
        ),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All Statuses")] + list(WorkOrder.Status.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            }
        ),
    )
    priority = forms.ChoiceField(
        required=False,
        choices=[("", "All Priorities")] + list(WorkOrder.Priority.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            }
        ),
    )


# ============================================================================
# SPRINT 4 FORMS - Additional 13 Forms for 16 Models
# ============================================================================

from .models import (
    WorkOrderDocument, WorkOrderPhoto, WorkOrderMaterial, WorkOrderTimeLog,
    BitEvaluation, SalvageItem, RepairApprovalAuthority, RepairEvaluation,
    RepairBOM, RepairBOMLine, ProcessRoute, ProcessRouteOperation, WorkOrderCost
)

# Standard CSS class for all form fields
INPUT_CLASS = 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
TEXTAREA_CLASS = INPUT_CLASS
SELECT_CLASS = INPUT_CLASS
CHECKBOX_CLASS = 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700'
FILE_CLASS = 'mt-1 block w-full text-sm text-gray-900 dark:text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'


class WorkOrderDocumentForm(forms.ModelForm):
    """Form for WorkOrderDocument - inline in WorkOrder detail."""
    class Meta:
        model = WorkOrderDocument
        fields = ['document_type', 'name', 'description', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Document name'}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'file': forms.FileInput(attrs={'class': FILE_CLASS}),
        }


class WorkOrderPhotoForm(forms.ModelForm):
    """Form for WorkOrderPhoto - inline in WorkOrder detail."""
    class Meta:
        model = WorkOrderPhoto
        fields = ['photo', 'caption', 'stage']
        widgets = {
            'photo': forms.FileInput(attrs={'class': FILE_CLASS, 'accept': 'image/*'}),
            'caption': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Photo caption'}),
            'stage': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'e.g., Before Repair'}),
        }


class WorkOrderMaterialForm(forms.ModelForm):
    """Form for WorkOrderMaterial - inline in WorkOrder detail."""
    class Meta:
        model = WorkOrderMaterial
        fields = ['inventory_item', 'bom_line', 'planned_quantity', 'issued_quantity',
                  'consumed_quantity', 'returned_quantity', 'unit_cost', 'notes']
        widgets = {
            'inventory_item': forms.Select(attrs={'class': SELECT_CLASS}),
            'bom_line': forms.Select(attrs={'class': SELECT_CLASS}),
            'planned_quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'issued_quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'consumed_quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'returned_quantity': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'unit_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.0001'}),
            'notes': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['bom_line', 'notes']:
            self.fields[field].required = False


class WorkOrderTimeLogForm(forms.ModelForm):
    """Form for WorkOrderTimeLog - inline in WorkOrder detail."""
    class Meta:
        model = WorkOrderTimeLog
        fields = ['user', 'start_time', 'end_time', 'activity_type', 'step',
                  'description', 'hourly_rate']
        widgets = {
            'user': forms.Select(attrs={'class': SELECT_CLASS}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': INPUT_CLASS}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': INPUT_CLASS}),
            'activity_type': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'step': forms.Select(attrs={'class': SELECT_CLASS}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'hourly_rate': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['user', 'end_time', 'activity_type', 'step', 'description', 'hourly_rate']:
            self.fields[field].required = False


class BitEvaluationForm(forms.ModelForm):
    """Form for BitEvaluation - inline in DrillBit detail."""
    class Meta:
        model = BitEvaluation
        fields = ['rig', 'well', 'run_number', 'hours_run', 'footage_drilled',
                  'depth_in', 'depth_out', 'evaluation_date', 'evaluated_by',
                  'inner_rows', 'outer_rows', 'dull_char', 'location', 'bearing_seal',
                  'gauge', 'other_char', 'reason_pulled', 'overall_condition',
                  'recommendation', 'findings', 'recommendations_detail']
        widgets = {
            'rig': forms.Select(attrs={'class': SELECT_CLASS}),
            'well': forms.Select(attrs={'class': SELECT_CLASS}),
            'run_number': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'hours_run': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'footage_drilled': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'depth_in': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'depth_out': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'evaluation_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS}),
            'evaluated_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'inner_rows': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'outer_rows': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'dull_char': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'location': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'bearing_seal': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'gauge': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'other_char': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'reason_pulled': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'overall_condition': forms.Select(attrs={'class': SELECT_CLASS}),
            'recommendation': forms.Select(attrs={'class': SELECT_CLASS}),
            'findings': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3}),
            'recommendations_detail': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['rig', 'well', 'run_number', 'hours_run', 'footage_drilled',
                    'depth_in', 'depth_out', 'evaluated_by', 'inner_rows', 'outer_rows',
                    'dull_char', 'location', 'bearing_seal', 'gauge', 'other_char',
                    'reason_pulled', 'overall_condition', 'recommendation',
                    'findings', 'recommendations_detail']
        for field in optional:
            self.fields[field].required = False


class SalvageItemForm(forms.ModelForm):
    """Form for SalvageItem - Full CRUD."""
    class Meta:
        model = SalvageItem
        fields = ['salvage_number', 'salvage_type', 'description', 'status',
                  'reuse_potential', 'condition_assessment', 'salvaged_date',
                  'work_order', 'drill_bit', 'quantity', 'estimated_value',
                  'disposition', 'disposition_date', 'disposed_by', 'storage_location', 'notes']
        widgets = {
            'salvage_number': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'salvage_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3}),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'reuse_potential': forms.Select(attrs={'class': SELECT_CLASS}),
            'condition_assessment': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3}),
            'salvaged_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS}),
            'work_order': forms.Select(attrs={'class': SELECT_CLASS}),
            'drill_bit': forms.Select(attrs={'class': SELECT_CLASS}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'estimated_value': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'disposition': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'disposition_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS}),
            'disposed_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'storage_location': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'notes': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['work_order', 'drill_bit', 'quantity', 'estimated_value',
                    'disposition', 'disposition_date', 'disposed_by', 'storage_location', 'notes']
        for field in optional:
            self.fields[field].required = False


class RepairApprovalAuthorityForm(forms.ModelForm):
    """Form for RepairApprovalAuthority - Configuration form."""
    class Meta:
        model = RepairApprovalAuthority
        fields = ['name', 'min_amount', 'max_amount', 'requires_justification', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'min_amount': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'max_amount': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'requires_justification': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
        }


class RepairEvaluationForm(forms.ModelForm):
    """Form for RepairEvaluation - Comprehensive repair decision form."""
    class Meta:
        model = RepairEvaluation
        fields = ['evaluation_number', 'drill_bit', 'evaluated_by', 'evaluation_date',
                  'inner_rows_grade', 'outer_rows_grade', 'bearing_condition',
                  'seal_condition', 'gauge_pad_wear_percent', 'body_wear_description',
                  'nozzle_condition', 'cutting_structure_assessment', 'cost_to_repair',
                  'estimated_remaining_life_hours', 'rerun_potential_footage',
                  'repair_cost_vs_new_ratio', 'scrap_value', 'recommendation',
                  'justification', 'approved_by', 'approval_date', 'notes']
        widgets = {
            'evaluation_number': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'drill_bit': forms.Select(attrs={'class': SELECT_CLASS}),
            'evaluated_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'evaluation_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS}),
            'inner_rows_grade': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'outer_rows_grade': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'bearing_condition': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'seal_condition': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'gauge_pad_wear_percent': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.1'}),
            'body_wear_description': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'nozzle_condition': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'cutting_structure_assessment': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'cost_to_repair': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'estimated_remaining_life_hours': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.1'}),
            'rerun_potential_footage': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.1'}),
            'repair_cost_vs_new_ratio': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'scrap_value': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'recommendation': forms.Select(attrs={'class': SELECT_CLASS}),
            'justification': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3}),
            'approved_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'approval_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS}),
            'notes': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['drill_bit', 'evaluated_by', 'evaluation_date', 'inner_rows_grade',
                    'outer_rows_grade', 'bearing_condition', 'seal_condition',
                    'gauge_pad_wear_percent', 'body_wear_description', 'nozzle_condition',
                    'cutting_structure_assessment', 'cost_to_repair',
                    'estimated_remaining_life_hours', 'rerun_potential_footage',
                    'repair_cost_vs_new_ratio', 'scrap_value', 'justification',
                    'approved_by', 'approval_date', 'notes']
        for field in optional:
            self.fields[field].required = False


class RepairBOMForm(forms.ModelForm):
    """Form for RepairBOM - Used with RepairBOMLine inline formset."""
    class Meta:
        model = RepairBOM
        fields = ['drill_bit', 'repair_evaluation', 'status', 'prepared_by', 'prepared_date', 'notes']
        widgets = {
            'drill_bit': forms.Select(attrs={'class': SELECT_CLASS}),
            'repair_evaluation': forms.Select(attrs={'class': SELECT_CLASS}),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'prepared_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'prepared_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS}),
            'notes': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['drill_bit', 'repair_evaluation', 'prepared_by', 'prepared_date', 'notes']:
            self.fields[field].required = False


class RepairBOMLineForm(forms.ModelForm):
    """Form for RepairBOMLine - inline in RepairBOM."""
    class Meta:
        model = RepairBOMLine
        fields = ['line_number', 'inventory_item', 'part_description',
                  'quantity_required', 'quantity_issued', 'notes']
        widgets = {
            'line_number': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'inventory_item': forms.Select(attrs={'class': SELECT_CLASS}),
            'part_description': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quantity_required': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'quantity_issued': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['inventory_item', 'part_description', 'notes']:
            self.fields[field].required = False


class ProcessRouteForm(forms.ModelForm):
    """Form for ProcessRoute - Used with ProcessRouteOperation inline formset."""
    class Meta:
        model = ProcessRoute
        fields = ['route_number', 'name', 'description', 'applicable_bit_types',
                  'version', 'effective_date', 'is_active']
        widgets = {
            'route_number': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'applicable_bit_types': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'version': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'effective_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['description', 'applicable_bit_types', 'version', 'effective_date']:
            self.fields[field].required = False


class ProcessRouteOperationForm(forms.ModelForm):
    """Form for ProcessRouteOperation - inline in ProcessRoute."""
    class Meta:
        model = ProcessRouteOperation
        fields = ['sequence', 'operation_code', 'operation_name', 'workstation',
                  'description', 'setup_time_minutes', 'run_time_minutes',
                  'special_instructions', 'required_skills', 'quality_checkpoints']
        widgets = {
            'sequence': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'operation_code': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'operation_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'workstation': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'setup_time_minutes': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'run_time_minutes': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'special_instructions': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'required_skills': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'quality_checkpoints': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['workstation', 'description', 'special_instructions', 'required_skills', 'quality_checkpoints']
        for field in optional:
            self.fields[field].required = False


class WorkOrderCostForm(forms.ModelForm):
    """Form for WorkOrderCost - Typically one-to-one with WorkOrder."""
    class Meta:
        model = WorkOrderCost
        fields = ['work_order', 'estimated_labor_hours', 'actual_labor_hours',
                  'labor_rate', 'estimated_material_cost', 'actual_material_cost',
                  'estimated_overhead', 'actual_overhead', 'notes']
        widgets = {
            'work_order': forms.Select(attrs={'class': SELECT_CLASS}),
            'estimated_labor_hours': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.1'}),
            'actual_labor_hours': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.1'}),
            'labor_rate': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'estimated_material_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'actual_material_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'estimated_overhead': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'actual_overhead': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['work_order'].required = False
        self.fields['notes'].required = False
