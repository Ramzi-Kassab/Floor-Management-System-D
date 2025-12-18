"""
ARDT FMS - Maintenance App Forms
Version: 5.4
"""

from django import forms

from .models import Equipment, EquipmentCategory, MaintenancePartsUsed, MaintenanceRequest, MaintenanceWorkOrder

TAILWIND_INPUT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_SELECT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
TAILWIND_TEXTAREA = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_CHECKBOX = "rounded border-gray-300 text-blue-600 focus:ring-blue-500"


class EquipmentCategoryForm(forms.ModelForm):
    """Form for equipment categories."""

    class Meta:
        model = EquipmentCategory
        fields = ["code", "name", "parent", "description", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "EQ-CAT-001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Category Name"}),
            "parent": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }


class EquipmentForm(forms.ModelForm):
    """Form for equipment."""

    class Meta:
        model = Equipment
        fields = [
            "code",
            "name",
            "category",
            "manufacturer",
            "model",
            "serial_number",
            "year_of_manufacture",
            "department",
            "location",
            "status",
            "maintenance_interval_days",
            "requires_calibration",
            "notes",
            "manual_file",
            "image",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "EQ-001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Equipment Name"}),
            "category": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "manufacturer": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "model": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "serial_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "year_of_manufacture": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "department": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "location": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Building/Room"}),
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "maintenance_interval_days": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "requires_calibration": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "manual_file": forms.FileInput(attrs={"class": TAILWIND_INPUT}),
            "image": forms.FileInput(attrs={"class": TAILWIND_INPUT}),
        }


class MaintenanceRequestForm(forms.ModelForm):
    """Form for maintenance requests."""

    class Meta:
        model = MaintenanceRequest
        fields = ["equipment", "request_type", "priority", "title", "description"]
        widgets = {
            "equipment": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "request_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "priority": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "title": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Brief description of issue"}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 4, "placeholder": "Detailed description..."}),
        }


class MaintenanceRequestApprovalForm(forms.ModelForm):
    """Form for approving/rejecting maintenance requests."""

    class Meta:
        model = MaintenanceRequest
        fields = ["status"]
        widgets = {
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = [
            ("APPROVED", "Approve"),
            ("REJECTED", "Reject"),
        ]


class MaintenanceWorkOrderForm(forms.ModelForm):
    """Form for maintenance work orders."""

    class Meta:
        model = MaintenanceWorkOrder
        fields = [
            "equipment",
            "request",
            "title",
            "description",
            "planned_start",
            "planned_end",
            "assigned_to",
        ]
        widgets = {
            "equipment": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "request": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "title": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 4}),
            "planned_start": forms.DateTimeInput(attrs={"class": TAILWIND_INPUT, "type": "datetime-local"}),
            "planned_end": forms.DateTimeInput(attrs={"class": TAILWIND_INPUT, "type": "datetime-local"}),
            "assigned_to": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }


class MaintenanceWorkOrderCompleteForm(forms.ModelForm):
    """Form for completing maintenance work orders."""

    class Meta:
        model = MaintenanceWorkOrder
        fields = ["work_performed", "findings", "recommendations", "labor_hours"]
        widgets = {
            "work_performed": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 4, "placeholder": "Describe the work performed..."}),
            "findings": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Any findings during maintenance..."}),
            "recommendations": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Recommendations for future..."}),
            "labor_hours": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.5"}),
        }


class MaintenancePartsUsedForm(forms.ModelForm):
    """Form for parts used in maintenance."""

    class Meta:
        model = MaintenancePartsUsed
        fields = ["inventory_item", "quantity", "notes"]
        widgets = {
            "inventory_item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "quantity": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }
