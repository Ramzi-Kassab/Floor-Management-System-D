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
        choices=[("", "All Types")] + list(DrillBit.BitCategory.choices),
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
        fields = ['salvage_number', 'drill_bit', 'work_order', 'salvage_type',
                  'description', 'status', 'condition_rating', 'reuse_potential',
                  'warehouse', 'storage_location', 'salvage_date', 'expiry_date',
                  'estimated_value']
        widgets = {
            'salvage_number': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'drill_bit': forms.Select(attrs={'class': SELECT_CLASS}),
            'work_order': forms.Select(attrs={'class': SELECT_CLASS}),
            'salvage_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3}),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'condition_rating': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 1, 'max': 10}),
            'reuse_potential': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'warehouse': forms.Select(attrs={'class': SELECT_CLASS}),
            'storage_location': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'salvage_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS}),
            'estimated_value': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['drill_bit', 'work_order', 'condition_rating', 'reuse_potential',
                    'warehouse', 'storage_location', 'expiry_date', 'estimated_value']
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
        fields = ['evaluation_number', 'drill_bit', 'inner_rows_grade', 'outer_rows_grade',
                  'dull_characteristic', 'location_code', 'gauge_condition',
                  'damage_assessment', 'recommended_repair', 'estimated_labor_hours',
                  'estimated_labor_rate', 'estimated_material_cost', 'estimated_overhead',
                  'status', 'repair_recommended', 'requires_approval', 'approval_authority',
                  'approved_by']
        widgets = {
            'evaluation_number': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'drill_bit': forms.Select(attrs={'class': SELECT_CLASS}),
            'inner_rows_grade': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'outer_rows_grade': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'dull_characteristic': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'location_code': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'gauge_condition': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'damage_assessment': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3}),
            'recommended_repair': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3}),
            'estimated_labor_hours': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'estimated_labor_rate': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'estimated_material_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'estimated_overhead': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'repair_recommended': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'requires_approval': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'approval_authority': forms.Select(attrs={'class': SELECT_CLASS}),
            'approved_by': forms.Select(attrs={'class': SELECT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['inner_rows_grade', 'outer_rows_grade', 'dull_characteristic',
                    'location_code', 'gauge_condition', 'recommended_repair',
                    'estimated_labor_hours', 'estimated_labor_rate', 'estimated_material_cost',
                    'estimated_overhead', 'approval_authority', 'approved_by']
        for field in optional:
            self.fields[field].required = False


class RepairBOMForm(forms.ModelForm):
    """Form for RepairBOM - Used with RepairBOMLine inline formset."""
    class Meta:
        model = RepairBOM
        fields = ['work_order', 'master_bom', 'status', 'estimated_material_cost',
                  'actual_material_cost', 'approved_by']
        widgets = {
            'work_order': forms.Select(attrs={'class': SELECT_CLASS}),
            'master_bom': forms.Select(attrs={'class': SELECT_CLASS}),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'estimated_material_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'actual_material_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'approved_by': forms.Select(attrs={'class': SELECT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['master_bom', 'estimated_material_cost', 'actual_material_cost', 'approved_by']:
            self.fields[field].required = False


class RepairBOMLineForm(forms.ModelForm):
    """Form for RepairBOMLine - inline in RepairBOM."""
    class Meta:
        model = RepairBOMLine
        fields = ['line_number', 'inventory_item', 'quantity_required', 'quantity_issued',
                  'quantity_consumed', 'quantity_returned', 'unit_cost', 'notes']
        widgets = {
            'line_number': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'inventory_item': forms.Select(attrs={'class': SELECT_CLASS}),
            'quantity_required': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'quantity_issued': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'quantity_consumed': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'quantity_returned': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'unit_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.0001'}),
            'notes': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['quantity_issued', 'quantity_consumed', 'quantity_returned', 'unit_cost', 'notes']:
            self.fields[field].required = False


class ProcessRouteForm(forms.ModelForm):
    """Form for ProcessRoute - Used with ProcessRouteOperation inline formset."""
    class Meta:
        model = ProcessRoute
        fields = ['route_number', 'name', 'description', 'repair_type', 'bit_types',
                  'is_active', 'version', 'estimated_duration_hours', 'estimated_labor_cost']
        widgets = {
            'route_number': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'repair_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'bit_types': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '["FC", "RC"]'}),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'version': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'estimated_duration_hours': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'estimated_labor_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['description', 'repair_type', 'bit_types', 'estimated_duration_hours', 'estimated_labor_cost']:
            self.fields[field].required = False


class ProcessRouteOperationForm(forms.ModelForm):
    """Form for ProcessRouteOperation - inline in ProcessRoute."""
    class Meta:
        model = ProcessRouteOperation
        fields = ['sequence', 'operation_code', 'operation_name', 'description',
                  'work_center', 'standard_hours', 'labor_rate', 'requires_qc',
                  'qc_checklist', 'safety_requirements']
        widgets = {
            'sequence': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'operation_code': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'operation_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'work_center': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'standard_hours': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'labor_rate': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'requires_qc': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'qc_checklist': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'safety_requirements': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['description', 'work_center', 'standard_hours', 'labor_rate',
                    'qc_checklist', 'safety_requirements']
        for field in optional:
            self.fields[field].required = False


class WorkOrderCostForm(forms.ModelForm):
    """Form for WorkOrderCost - Typically one-to-one with WorkOrder."""
    class Meta:
        model = WorkOrderCost
        fields = ['estimated_labor_hours', 'actual_labor_hours', 'labor_rate', 'labor_cost',
                  'estimated_material_cost', 'actual_material_cost', 'overhead_rate_percent',
                  'overhead_cost', 'subcontractor_cost', 'total_estimated_cost', 'total_actual_cost']
        widgets = {
            'estimated_labor_hours': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'actual_labor_hours': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'labor_rate': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'labor_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'estimated_material_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'actual_material_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'overhead_rate_percent': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'overhead_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'subcontractor_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'total_estimated_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'total_actual_cost': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False


# ============================================================================
# JOB CARD FORMS - Location, InstructionRule, QC Forms
# ============================================================================

from .models import (
    Location, InstructionRule, InstructionRuleCondition,
    CutterEvaluationMatrix, CutterEvaluationEntry,
    RouterSheetEntry, EvaluationChecklist, LPTReport, APIThreadInspection
)


class LocationForm(forms.ModelForm):
    """Form for Location - manage physical locations for drill bits."""
    class Meta:
        model = Location
        fields = ['code', 'name', 'location_type', 'address', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'e.g., WH-MAIN',
            }),
            'name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'e.g., Main Warehouse',
            }),
            'location_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'address': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2,
                'placeholder': 'Physical address (optional)',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address'].required = False

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
            # Check uniqueness excluding current instance
            qs = Location.objects.filter(code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A location with this code already exists.")
        return code


class InstructionRuleForm(forms.ModelForm):
    """Form for InstructionRule - conditional instructions for work orders."""
    class Meta:
        model = InstructionRule
        fields = ['title', 'wo_type', 'bit_type', 'priority', 'instruction_text', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Rule title',
            }),
            'wo_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'bit_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'priority': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'min': 0,
                'max': 100,
            }),
            'instruction_text': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 4,
                'placeholder': 'Enter the instruction text that will be displayed...',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make wo_type and bit_type optional (for "any" matching)
        self.fields['wo_type'].required = False
        self.fields['bit_type'].required = False


class InstructionRuleConditionForm(forms.ModelForm):
    """Form for InstructionRuleCondition - inline in InstructionRule."""
    class Meta:
        model = InstructionRuleCondition
        fields = ['field_name', 'operator', 'value']
        widgets = {
            'field_name': forms.Select(attrs={'class': SELECT_CLASS}),
            'operator': forms.Select(attrs={'class': SELECT_CLASS}),
            'value': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Value to compare',
            }),
        }


# Formset for InstructionRuleCondition
InstructionRuleConditionFormSet = forms.inlineformset_factory(
    InstructionRule,
    InstructionRuleCondition,
    form=InstructionRuleConditionForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


class CutterEvaluationMatrixForm(forms.ModelForm):
    """Form for CutterEvaluationMatrix - create/edit cutter evaluation."""
    class Meta:
        model = CutterEvaluationMatrix
        fields = ['evaluation_type', 'evaluation_number', 'notes']
        widgets = {
            'evaluation_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'evaluation_number': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'min': 1,
                'max': 3,
            }),
            'notes': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2,
                'placeholder': 'Optional notes...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notes'].required = False


class RouterSheetEntryForm(forms.ModelForm):
    """Form for RouterSheetEntry - process step tracking."""
    class Meta:
        model = RouterSheetEntry
        fields = ['step_number', 'step_name', 'description', 'estimated_hours']
        widgets = {
            'step_number': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'step_name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Step name',
            }),
            'description': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2,
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.25',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['estimated_hours'].required = False


class EvaluationChecklistForm(forms.ModelForm):
    """Form for EvaluationChecklist - E-Checklist for FC bits."""
    class Meta:
        model = EvaluationChecklist
        fields = [
            'bit_cleanliness', 'bit_cleanliness_remarks',
            'paperwork', 'paperwork_remarks',
            'bit_stamping', 'bit_stamping_remarks',
            'die_check', 'die_check_remarks',
            'ring_gauge_go', 'ring_gauge_go_remarks',
            'ring_gauge_no_go', 'ring_gauge_no_go_remarks',
            'nozzle_bore_liner', 'nozzle_bore_liner_remarks',
            'nozzle_threads', 'nozzle_threads_remarks',
            'apex', 'apex_remarks',
            'junk_slot', 'junk_slot_remarks',
            'breaker_slot', 'breaker_slot_remarks',
            'body_condition', 'body_condition_remarks',
            'mud_seal_surface', 'mud_seal_surface_remarks',
            'api_pin', 'api_pin_remarks',
            'inner_diameter', 'inner_diameter_remarks',
            'overall_pass', 'general_remarks',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional
        for field in self.fields:
            self.fields[field].required = False
            # Add styling
            if '_remarks' in field or field == 'general_remarks':
                self.fields[field].widget = forms.TextInput(attrs={
                    'class': INPUT_CLASS,
                    'placeholder': 'Remarks (optional)',
                })
            elif field == 'overall_pass':
                self.fields[field].widget = forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS})
            else:
                self.fields[field].widget = forms.Select(attrs={'class': SELECT_CLASS})


class LPTReportForm(forms.ModelForm):
    """Form for LPTReport - Liquid Penetrant Test documentation."""
    class Meta:
        model = LPTReport
        fields = [
            'test_date', 'surface_condition', 'penetrant_type',
            'penetrant_application_time', 'developer_type', 'developer_dwell_time',
            'temperature', 'lighting_conditions', 'result', 'indications_found',
            'remarks', 'photo'
        ]
        widgets = {
            'test_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS}),
            'surface_condition': forms.Select(attrs={'class': SELECT_CLASS}),
            'penetrant_type': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'penetrant_application_time': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'developer_type': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'developer_dwell_time': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'temperature': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.1'}),
            'lighting_conditions': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'result': forms.Select(attrs={'class': SELECT_CLASS}),
            'indications_found': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3}),
            'remarks': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'photo': forms.FileInput(attrs={'class': FILE_CLASS, 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['penetrant_type', 'penetrant_application_time', 'developer_type',
                    'developer_dwell_time', 'temperature', 'lighting_conditions',
                    'indications_found', 'remarks', 'photo']
        for field in optional:
            self.fields[field].required = False


class APIThreadInspectionForm(forms.ModelForm):
    """Form for APIThreadInspection - API thread inspection documentation."""
    class Meta:
        model = APIThreadInspection
        fields = [
            'inspection_date', 'connection_type', 'thread_form', 'thread_pitch',
            'taper', 'thread_height', 'lead', 'standoff', 'ovality',
            'surface_finish', 'result', 'remarks', 'photo'
        ]
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS}),
            'connection_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'thread_form': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'thread_pitch': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'taper': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'thread_height': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'lead': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'standoff': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'ovality': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.001'}),
            'surface_finish': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.01'}),
            'result': forms.Select(attrs={'class': SELECT_CLASS}),
            'remarks': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2}),
            'photo': forms.FileInput(attrs={'class': FILE_CLASS, 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['thread_form', 'thread_pitch', 'taper', 'thread_height',
                    'lead', 'standoff', 'ovality', 'surface_finish', 'remarks', 'photo']
        for field in optional:
            self.fields[field].required = False


# ============================================================================
# DRILL BIT ACTION FORMS
# ============================================================================

class DrillBitReceiveForm(forms.Form):
    """Form for receiving a drill bit."""
    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
        help_text="Select receiving location"
    )
    received_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2})
    )


class DrillBitShipForm(forms.Form):
    """Form for shipping a drill bit."""
    destination = forms.ModelChoiceField(
        queryset=Location.objects.filter(is_active=True, location_type__in=['RIG', 'WAREHOUSE']),
        required=True,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
        help_text="Select destination location"
    )
    customer = forms.IntegerField(required=False, widget=forms.HiddenInput())
    rig = forms.IntegerField(required=False, widget=forms.HiddenInput())
    shipping_ref = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Shipping reference'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2})
    )


class DrillBitTransferForm(forms.Form):
    """Form for transferring a drill bit between locations."""
    to_location = forms.ModelChoiceField(
        queryset=Location.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
        help_text="Select destination location"
    )
    reason = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Transfer reason'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2})
    )


class DrillBitReturnForm(forms.Form):
    """Form for returning a drill bit from the field."""
    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(is_active=True, location_type__in=['WAREHOUSE', 'EVALUATION', 'REPAIR_SHOP']),
        required=True,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
        help_text="Select receiving location"
    )
    condition = forms.ChoiceField(
        choices=[
            ('GOOD', 'Good'),
            ('DAMAGED', 'Damaged'),
            ('NEEDS_REPAIR', 'Needs Repair'),
            ('SCRAP', 'Scrap'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': SELECT_CLASS})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2})
    )


class DrillBitScrapForm(forms.Form):
    """Form for scrapping a drill bit."""
    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(is_active=True, location_type='SCRAP'),
        required=False,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
        help_text="Select scrap location (optional)"
    )
    reason = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Scrap reason'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2})
    )


class DrillBitStartRepairForm(forms.Form):
    """Form for starting repair on a drill bit."""
    work_order = forms.ModelChoiceField(
        queryset=WorkOrder.objects.filter(status__in=['DRAFT', 'PLANNED', 'RELEASED']),
        required=False,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
        help_text="Link to existing work order (optional)"
    )
    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(is_active=True, location_type='REPAIR_SHOP'),
        required=False,
        widget=forms.Select(attrs={'class': SELECT_CLASS}),
        help_text="Select repair shop location"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 2})
    )
