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
    """
    Form for creating and editing designs.
    Updated for Phase 2 with FK relations to reference tables.
    """

    class Meta:
        model = Design
        fields = [
            # Identity
            "mat_no",
            "hdbs_type",
            "smi_type",
            "ref_mat_no",
            "ardt_item_no",
            # Category & Size
            "category",
            "size",
            "series",
            # Technical Specs (FC)
            "body_material",
            "no_of_blades",
            "cutter_size",
            "gage_length",
            "gage_relief",
            "erosion_sleeve",
            # Nozzles
            "nozzle_count",
            "nozzle_bore_size",
            "nozzle_config",
            "milling_drawing",
            "tfa",
            # Ports
            "port_count",
            "port_size",
            # Connection (FK)
            "connection_mat_no",
            "connection_type_ref",
            "connection_size_ref",
            # Application (FK)
            "formation_type_ref",
            "application_ref",
            "iadc_code_ref",
            # Special Technologies
            "special_technologies",
            # Order Level
            "order_level",
            # Status
            "status",
            "revision",
            # Notes
            "description",
            "notes",
        ]
        widgets = {
            # Identity
            "mat_no": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., 800012345", "id": "id_mat_no"}),
            "hdbs_type": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., GT65RHS", "id": "id_hdbs_type"}),
            "smi_type": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Client-facing type"}),
            "ref_mat_no": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Reference MAT No."}),
            "ardt_item_no": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "ARDT Item No."}),
            # Category & Size
            "category": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "size": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "series": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Auto-filled from HDBS Type", "id": "id_series", "readonly": "readonly"}),
            # Technical Specs
            "body_material": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "no_of_blades": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 0, "id": "id_no_of_blades", "readonly": "readonly"}),
            "cutter_size": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 0, "id": "id_cutter_size", "readonly": "readonly"}),
            "gage_length": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "min": "0", "placeholder": "inches"}),
            "gage_relief": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.1", "min": "0", "placeholder": "thou"}),
            "erosion_sleeve": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500 h-5 w-5"}),
            # Nozzles
            "nozzle_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 0}),
            "nozzle_bore_size": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., 12/32"}),
            "nozzle_config": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Layout (see Milling Drawing)"}),
            "milling_drawing": forms.FileInput(attrs={"class": TAILWIND_INPUT, "accept": ".pdf"}),
            "tfa": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "min": "0", "placeholder": "sq. in"}),
            # Ports
            "port_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 0}),
            "port_size": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "min": "0"}),
            # Connection
            "connection_mat_no": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Connection material number"}),
            "connection_type_ref": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "connection_size_ref": forms.Select(attrs={"class": TAILWIND_SELECT}),
            # Application
            "formation_type_ref": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "application_ref": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "iadc_code_ref": forms.Select(attrs={"class": TAILWIND_SELECT}),
            # Special Technologies
            "special_technologies": forms.CheckboxSelectMultiple(attrs={"class": "space-y-2"}),
            # Order Level
            "order_level": forms.Select(attrs={"class": TAILWIND_SELECT}),
            # Status
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "revision": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "A"}),
            # Notes
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }
        labels = {
            "mat_no": "MAT No.",
            "hdbs_type": "HDBS Type",
            "smi_type": "SMI Type",
            "ref_mat_no": "Ref MAT No.",
            "ardt_item_no": "ARDT Item No.",
            "no_of_blades": "No. of Blades",
            "cutter_size": "Cutter Size Grade",
            "gage_length": "Gage Length (in)",
            "gage_relief": "Gage Relief (thou)",
            "erosion_sleeve": "Erosion Sleeve",
            "nozzle_count": "Nozzle Count",
            "nozzle_bore_size": "Nozzle Bore Size",
            "nozzle_config": "Nozzle Config",
            "milling_drawing": "Milling Drawing (PDF)",
            "tfa": "TFA (sq.in)",
            "port_count": "Port Count",
            "port_size": "Port Size",
            "connection_mat_no": "Connection MAT No.",
            "connection_type_ref": "Connection Type",
            "connection_size_ref": "Connection Size",
            "formation_type_ref": "Formation Type",
            "application_ref": "Application",
            "iadc_code_ref": "IADC Code",
            "special_technologies": "Special Technologies",
            "order_level": "Order Level",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make most fields optional
        required_fields = ["mat_no", "hdbs_type", "category", "status"]
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False


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
