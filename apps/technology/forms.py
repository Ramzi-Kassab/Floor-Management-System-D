"""
ARDT FMS - Technology Forms
Version: 5.4 - Sprint 3

Forms for Design, BOM, and Cutter Layout management.
"""

from django import forms

from .models import BOM, BOMLine, Design, DesignCutterLayout

# Tailwind CSS classes
TAILWIND_INPUT = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
TAILWIND_SELECT = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
TAILWIND_TEXTAREA = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"


class DesignForm(forms.ModelForm):
    """Form for creating and editing designs."""

    class Meta:
        model = Design
        fields = [
            "code",
            "name",
            "bit_type",
            "size",
            "iadc_code",
            "blade_count",
            "cone_count",
            "connection_type",
            "connection_size",
            "formation_type",
            "application",
            "gauge_protection",
            "nozzle_config",
            "tfa",
            "status",
            "revision",
            "description",
            "notes",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., FC-8.5-001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Design name"}),
            "bit_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "size": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "placeholder": "Size (inches)"}),
            "iadc_code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "IADC code"}),
            "blade_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 0}),
            "cone_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 0}),
            "connection_type": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., API REG"}),
            "connection_size": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., 4-1/2"}),
            "formation_type": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Target formation"}),
            "application": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Application type"}),
            "gauge_protection": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "nozzle_config": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., 5x12"}),
            "tfa": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "placeholder": "TFA"}),
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "revision": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "A"}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional_fields = [
            "iadc_code", "blade_count", "cone_count", "connection_type",
            "connection_size", "formation_type", "application", "gauge_protection",
            "nozzle_config", "tfa", "description", "notes"
        ]
        for field in optional_fields:
            self.fields[field].required = False


class BOMForm(forms.ModelForm):
    """Form for creating and editing BOMs."""

    class Meta:
        model = BOM
        fields = ["design", "code", "name", "revision", "status", "effective_date", "notes"]
        widgets = {
            "design": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "BOM code"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "BOM name"}),
            "revision": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "A"}),
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "effective_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["effective_date"].required = False
        self.fields["notes"].required = False


class BOMLineForm(forms.ModelForm):
    """Form for BOM line items."""

    class Meta:
        model = BOMLine
        fields = [
            "line_number",
            "inventory_item",
            "quantity",
            "unit",
            "unit_cost",
            "position",
            "is_optional",
            "is_phantom",
            "notes",
        ]
        widgets = {
            "line_number": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 1}),
            "inventory_item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "quantity": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "min": 0}),
            "unit": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "EA, PC, etc."}),
            "unit_cost": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001", "min": 0}),
            "position": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Assembly position"}),
            "is_optional": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"}),
            "is_phantom": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }


class DesignCutterLayoutForm(forms.ModelForm):
    """Form for cutter layout positions."""

    class Meta:
        model = DesignCutterLayout
        fields = [
            "blade_number",
            "position_number",
            "cutter_type",
            "cutter_size",
            "cutter_grade",
            "radial_position",
            "backrake",
            "siderake",
            "exposure",
            "notes",
        ]
        widgets = {
            "blade_number": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 1}),
            "position_number": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 1}),
            "cutter_type": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "PDC, TSP, etc."}),
            "cutter_size": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01", "placeholder": "mm"}),
            "cutter_grade": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "radial_position": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "placeholder": "mm"}),
            "backrake": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01", "placeholder": "degrees"}),
            "siderake": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01", "placeholder": "degrees"}),
            "exposure": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01", "placeholder": "mm"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ["cutter_grade", "backrake", "siderake", "exposure", "notes"]
        for field in optional:
            self.fields[field].required = False
