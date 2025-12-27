"""
ARDT FMS - Technology Forms
Version: 5.4 - Sprint 3

Forms for Design, BOM, and Cutter Layout management.
"""

from django import forms

from .models import (
    BOM, BOMLine, BitSize, BitType, BreakerSlot, Connection, Design,
    DesignCutterLayout, HDBSType, SMIType, DesignHDBS, DesignSMI
)
from apps.sales.models import Account

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
            # Identity (merged with Category & Technical Specs)
            # Row 1: Order Level, Category, MAT No., Ref MAT No.
            "order_level",
            "category",
            "mat_no",
            "ref_mat_no",
            # Row 2: Size, HDBS Type, SMI Type, IADC Code
            "size",
            "hdbs_type",
            "smi_type",
            "iadc_code_ref",
            # Row 3: ARDT Item No. (standalone)
            "ardt_item_no",
            # Row 4 Auto-fill: Body Material, Series, No. of Blades, Cutter Size Grade
            "body_material",
            "series",
            "no_of_blades",
            "cutter_size",
            # Row 5: Total Cutters Count, Gage Length, Gage Relief
            "total_pockets_count",
            "gage_length",
            "gage_relief",
            # Nozzles & Ports (Hydraulics)
            "nozzle_count",
            "nozzle_bore_size",
            "nozzle_config",
            "milling_drawing",
            "port_count",
            "port_size",
            # Connection (modal picker)
            "connection_ref",
            # Breaker Slot (modal picker)
            "breaker_slot",
            # Application
            "formation_type_ref",
            "application_ref",
            # Special Technologies (includes Erosion Sleeve)
            "special_technologies",
            # Status
            "status",
            "revision",
            # Notes
            "description",
            "notes",
            # Pocket Layout Number
            "pocket_layout_number",
        ]
        widgets = {
            # Category & Classification
            "category": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "body_material": forms.Select(attrs={"class": TAILWIND_SELECT, "id": "id_body_material"}),
            "size": forms.Select(attrs={"class": TAILWIND_SELECT}),
            # Identity
            "mat_no": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., 800012345"}),
            "hdbs_type": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., GT65RHS", "id": "id_hdbs_type"}),
            "smi_type": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Client-facing type"}),
            "ref_mat_no": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Reference MAT No."}),
            "ardt_item_no": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "ARDT Item No."}),
            "series": forms.TextInput(attrs={"class": TAILWIND_INPUT + " bg-gray-100", "id": "id_series", "readonly": "readonly"}),
            # Technical Specs
            "no_of_blades": forms.NumberInput(attrs={"class": TAILWIND_INPUT + " bg-gray-100", "min": 0, "id": "id_no_of_blades", "readonly": "readonly"}),
            "cutter_size": forms.NumberInput(attrs={"class": TAILWIND_INPUT + " bg-gray-100", "min": 0, "id": "id_cutter_size", "readonly": "readonly"}),
            "total_pockets_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 0, "placeholder": "Total cutters"}),
            "gage_length": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "min": "0", "placeholder": "inches"}),
            "gage_relief": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.1", "min": "0", "placeholder": "thou"}),
            "order_level": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "iadc_code_ref": forms.Select(attrs={"class": TAILWIND_SELECT}),
            # Nozzles & Ports
            "nozzle_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 0}),
            "nozzle_bore_size": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., 12/32"}),
            "nozzle_config": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Layout (see Milling Drawing)"}),
            "milling_drawing": forms.FileInput(attrs={"class": TAILWIND_INPUT, "accept": ".pdf"}),
            "port_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 0}),
            "port_size": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "min": "0"}),
            # Connection (modal picker - hidden input)
            "connection_ref": forms.HiddenInput(attrs={"id": "id_connection_ref"}),
            # Breaker Slot (modal picker - hidden input)
            "breaker_slot": forms.HiddenInput(attrs={"id": "id_breaker_slot"}),
            # Application
            "formation_type_ref": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "application_ref": forms.Select(attrs={"class": TAILWIND_SELECT}),
            # Special Technologies
            "special_technologies": forms.CheckboxSelectMultiple(attrs={"class": "space-y-2"}),
            # Status
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "revision": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "A"}),
            # Notes
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA + " bg-gray-100", "rows": 2, "id": "id_description", "readonly": "readonly"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            # Pocket Layout Number
            "pocket_layout_number": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Auto-generated"}),
        }
        labels = {
            "mat_no": "MAT No.",
            "hdbs_type": "HDBS Type",
            "smi_type": "SMI Type",
            "ref_mat_no": "Ref MAT No.",
            "ardt_item_no": "ARDT Item No.",
            "body_material": "Body Material",
            "no_of_blades": "No. of Blades",
            "cutter_size": "Cutter Size Grade",
            "total_pockets_count": "Total Cutters Count",
            "gage_length": "Gage Length (in)",
            "gage_relief": "Gage Relief (thou)",
            "nozzle_count": "Nozzle Count",
            "nozzle_bore_size": "Nozzle Bore Size",
            "nozzle_config": "Nozzle Config",
            "milling_drawing": "Milling Drawing (PDF)",
            "port_count": "Port Count",
            "port_size": "Port Size",
            "connection_ref": "Connection",
            "breaker_slot": "Breaker Slot",
            "formation_type_ref": "Formation Type",
            "application_ref": "Application",
            "iadc_code_ref": "IADC Code",
            "special_technologies": "Special Technologies",
            "order_level": "Order Level",
            "pocket_layout_number": "Pocket Layout No.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make most fields optional
        required_fields = ["mat_no", "hdbs_type", "category", "status"]
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False

        # Only show active sizes in the dropdown
        self.fields["size"].queryset = BitSize.objects.filter(is_active=True).order_by("size_decimal")


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


class ConnectionForm(forms.ModelForm):
    """Form for creating and editing Connections."""

    class Meta:
        model = Connection
        fields = [
            "mat_no",
            "connection_type",
            "connection_size",
            "special_features",
            "can_replace_in_ksa",
            "remarks",
            "is_active",
        ]
        widgets = {
            "mat_no": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., 1754845"}),
            "connection_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "connection_size": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "special_features": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2, "placeholder": "Any special features or modifications"}),
            "can_replace_in_ksa": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"}),
            "remarks": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"}),
        }
        labels = {
            "mat_no": "MAT No.",
            "connection_type": "Connection Type",
            "connection_size": "Connection Size",
            "special_features": "Special Features",
            "can_replace_in_ksa": "Can Replace in KSA",
            "remarks": "Remarks",
            "is_active": "Active",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["special_features"].required = False
        self.fields["remarks"].required = False


class BreakerSlotForm(forms.ModelForm):
    """Form for creating and editing Breaker Slots."""

    class Meta:
        model = BreakerSlot
        fields = [
            "mat_no",
            "slot_width",
            "slot_depth",
            "slot_length",
            "material",
            "hardness",
            "compatible_sizes",
            "remarks",
            "is_active",
        ]
        widgets = {
            "mat_no": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., BS-001"}),
            "slot_width": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "min": "0", "placeholder": "inches"}),
            "slot_depth": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "min": "0", "placeholder": "inches"}),
            "slot_length": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "min": "0", "placeholder": "inches (optional)"}),
            "material": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "hardness": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., 28-32 HRC"}),
            "compatible_sizes": forms.CheckboxSelectMultiple(attrs={"class": "space-y-2"}),
            "remarks": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"}),
        }
        labels = {
            "mat_no": "MAT No.",
            "slot_width": "Slot Width (in)",
            "slot_depth": "Slot Depth (in)",
            "slot_length": "Slot Length (in)",
            "material": "Material",
            "hardness": "Hardness (HRC)",
            "compatible_sizes": "Compatible Bit Sizes",
            "remarks": "Remarks",
            "is_active": "Active",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slot_length"].required = False
        self.fields["hardness"].required = False
        self.fields["compatible_sizes"].required = False
        self.fields["remarks"].required = False


class BitSizeForm(forms.ModelForm):
    """Form for creating and editing Bit Sizes - simple list."""

    class Meta:
        model = BitSize
        fields = [
            "size_display",
            "size_decimal",
            "code",
            "size_inches",
            "description",
            "is_active",
        ]
        widgets = {
            "size_display": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": 'e.g., 8 1/2"'}),
            "size_decimal": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "min": "0", "placeholder": "e.g., 8.500"}),
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., 8.500"}),
            "size_inches": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., 8 1/2"}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2, "placeholder": "Optional remarks"}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"}),
        }
        labels = {
            "size_display": "Size",
            "size_decimal": "Decimal Value",
            "code": "Code",
            "size_inches": "Fraction",
            "description": "Description / Remarks",
            "is_active": "Active",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].required = False


class HDBSTypeForm(forms.ModelForm):
    """Form for creating and editing HDBS Types (Internal naming)."""

    class Meta:
        model = HDBSType
        fields = [
            "hdbs_name",
            "sizes",
            "description",
            "is_active",
        ]
        widgets = {
            "hdbs_name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., GT65RHS"}),
            "sizes": forms.CheckboxSelectMultiple(attrs={"class": "space-y-2"}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2, "placeholder": "Optional description"}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"}),
        }
        labels = {
            "hdbs_name": "HDBS Name (Internal)",
            "sizes": "Compatible Sizes",
            "description": "Description",
            "is_active": "Active",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sizes"].required = True  # At least one size is required
        self.fields["description"].required = False
        # Only show active sizes
        self.fields["sizes"].queryset = BitSize.objects.filter(is_active=True).order_by("size_decimal")

    def clean_sizes(self):
        """Validate that at least one size is selected."""
        sizes = self.cleaned_data.get("sizes")
        if not sizes or sizes.count() == 0:
            raise forms.ValidationError("At least one size must be selected.")
        return sizes


class SMITypeForm(forms.ModelForm):
    """Form for creating and editing SMI Types (Client-facing naming)."""

    class Meta:
        model = SMIType
        fields = [
            "smi_name",
            "hdbs_type",
            "size",
            "description",
            "is_active",
        ]
        widgets = {
            "smi_name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., GT65RHs-1"}),
            "hdbs_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "size": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2, "placeholder": "Optional description"}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"}),
        }
        labels = {
            "smi_name": "SMI Name (Client-Facing)",
            "hdbs_type": "HDBS Type",
            "size": "Size",
            "description": "Description",
            "is_active": "Active",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].required = False
        self.fields["size"].required = True  # Size is required for SMI types
        # Only show active sizes
        self.fields["size"].queryset = BitSize.objects.filter(is_active=True).order_by("size_decimal")


class DesignHDBSForm(forms.ModelForm):
    """Form for assigning HDBS Type to a Design."""

    class Meta:
        model = DesignHDBS
        fields = [
            "design",
            "hdbs_type",
            "is_current",
            "notes",
        ]
        widgets = {
            "design": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "hdbs_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "is_current": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }
        labels = {
            "design": "Design (MAT No.)",
            "hdbs_type": "HDBS Type",
            "is_current": "Current Assignment",
            "notes": "Notes",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notes"].required = False
        # Only show active HDBS types
        self.fields["hdbs_type"].queryset = HDBSType.objects.filter(is_active=True).order_by("hdbs_name")


class DesignSMIForm(forms.ModelForm):
    """Form for assigning SMI Type to a Design (with optional Account)."""

    class Meta:
        model = DesignSMI
        fields = [
            "design",
            "smi_type",
            "account",
            "is_current",
            "notes",
        ]
        widgets = {
            "design": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "smi_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "account": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "is_current": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }
        labels = {
            "design": "Design (MAT No.)",
            "smi_type": "SMI Type",
            "account": "Account (Aramco Division)",
            "is_current": "Current Assignment",
            "notes": "Notes",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["account"].required = False  # Global if no account
        self.fields["notes"].required = False
        # Only show active SMI types and accounts
        self.fields["smi_type"].queryset = SMIType.objects.filter(is_active=True).select_related("hdbs_type", "size")
        self.fields["account"].queryset = Account.objects.filter(is_active=True).order_by("code")
