"""
ARDT FMS - Inventory App Forms
Version: 5.4
"""

from django import forms

from .models import (
    Attribute,
    CategoryAttribute,
    InventoryCategory,
    InventoryItem,
    InventoryLocation,
    InventoryStock,
    InventoryTransaction,
    ItemBitSpec,
    ItemCutterSpec,
    ItemIdentifier,
    ItemPlanning,
    ItemSupplier,
    ItemVariant,
    UnitOfMeasure,
)

TAILWIND_INPUT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_SELECT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
TAILWIND_TEXTAREA = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_CHECKBOX = "rounded border-gray-300 text-blue-600 focus:ring-blue-500"


class InventoryCategoryForm(forms.ModelForm):
    """Form for inventory categories."""

    class Meta:
        model = InventoryCategory
        fields = ["code", "name", "parent", "item_type", "code_prefix", "name_template", "description", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "CAT-001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Category Name"}),
            "parent": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "item_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "code_prefix": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "CUT, MAT, NOZ"}),
            "name_template": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "{size}mm {material} {grade}"}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }


class InventoryLocationForm(forms.ModelForm):
    """Form for inventory locations."""

    class Meta:
        model = InventoryLocation
        fields = ["warehouse", "code", "name", "aisle", "rack", "shelf", "bin", "is_active"]
        widgets = {
            "warehouse": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "LOC-001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Location Name"}),
            "aisle": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "A1"}),
            "rack": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "R1"}),
            "shelf": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "S1"}),
            "bin": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "B1"}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }


class InventoryItemForm(forms.ModelForm):
    """Form for inventory items."""

    class Meta:
        model = InventoryItem
        fields = [
            "code",
            "name",
            "description",
            "item_type",
            "category",
            "unit",
            "standard_cost",
            "currency",
            "min_stock",
            "max_stock",
            "reorder_point",
            "reorder_quantity",
            "lead_time_days",
            "primary_supplier",
            "supplier_part_number",
            "is_active",
            "is_serialized",
            "is_lot_controlled",
            "image",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "ITEM-0001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Item Name"}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "item_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "category": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "unit": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "EA"}),
            "standard_cost": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
            "currency": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "SAR"}),
            "min_stock": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "max_stock": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "reorder_point": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "reorder_quantity": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "lead_time_days": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "primary_supplier": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "supplier_part_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "is_serialized": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "is_lot_controlled": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "image": forms.FileInput(attrs={"class": TAILWIND_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make item_type not required - will get from category default if not provided
        self.fields['item_type'].required = False

    def clean_item_type(self):
        item_type = self.cleaned_data.get('item_type')
        if not item_type:
            # Try to get default from category
            category = self.cleaned_data.get('category')
            if category and category.item_type:
                return category.item_type
            # Final fallback
            return 'STOCK_ITEM'
        return item_type


class InventoryStockForm(forms.ModelForm):
    """Form for inventory stock records."""

    class Meta:
        model = InventoryStock
        fields = ["item", "location", "quantity_on_hand", "quantity_reserved", "lot_number", "serial_number", "expiry_date"]
        widgets = {
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "location": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "quantity_on_hand": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "quantity_reserved": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "lot_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "serial_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "expiry_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
        }


class InventoryTransactionForm(forms.ModelForm):
    """Form for inventory transactions."""

    class Meta:
        model = InventoryTransaction
        fields = [
            "transaction_type",
            "item",
            "from_location",
            "to_location",
            "quantity",
            "unit",
            "unit_cost",
            "lot_number",
            "serial_number",
            "reference_number",
            "reason",
            "notes",
        ]
        widgets = {
            "transaction_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "from_location": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "to_location": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "quantity": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "unit": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "unit_cost": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "lot_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "serial_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "reference_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "reason": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get("transaction_type")
        from_location = cleaned_data.get("from_location")
        to_location = cleaned_data.get("to_location")

        if transaction_type == "TRANSFER" and (not from_location or not to_location):
            raise forms.ValidationError("Transfer transactions require both from and to locations.")

        if transaction_type == "ISSUE" and not from_location:
            raise forms.ValidationError("Issue transactions require a from location.")

        if transaction_type == "RECEIPT" and not to_location:
            raise forms.ValidationError("Receipt transactions require a to location.")

        return cleaned_data


class StockAdjustmentForm(forms.Form):
    """Simple form for stock adjustments."""

    adjustment_type = forms.ChoiceField(
        choices=[("ADD", "Add Stock"), ("REMOVE", "Remove Stock")],
        widget=forms.Select(attrs={"class": TAILWIND_SELECT}),
    )
    quantity = forms.DecimalField(
        min_value=0,
        decimal_places=3,
        widget=forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "placeholder": "Quantity"}),
    )
    reason = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Reason for adjustment"}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2, "placeholder": "Additional notes"}),
    )


class CategoryAttributeForm(forms.ModelForm):
    """Form for linking attributes to categories with configuration."""

    class Meta:
        model = CategoryAttribute
        fields = [
            "category",
            "attribute",
            "attribute_type",
            "unit",
            "min_value",
            "max_value",
            "options",
            "is_required",
            "is_used_in_name",
            "display_order",
        ]
        widgets = {
            "category": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "attribute": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "attribute_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "unit": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "min_value": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "max_value": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "options": forms.Textarea(attrs={
                "class": TAILWIND_TEXTAREA,
                "rows": 2,
                "placeholder": '["Option1", "Option2"]'
            }),
            "is_required": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "is_used_in_name": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "display_order": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
        }


# =============================================================================
# New Architecture Forms
# =============================================================================


class ItemPlanningForm(forms.ModelForm):
    """Form for per-warehouse planning data."""

    class Meta:
        model = ItemPlanning
        fields = ["warehouse", "min_stock", "max_stock", "reorder_point", "reorder_quantity", "is_active"]
        widgets = {
            "warehouse": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "min_stock": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "max_stock": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "reorder_point": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "reorder_quantity": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }


class ItemSupplierForm(forms.ModelForm):
    """Form for item-supplier relationships."""

    class Meta:
        model = ItemSupplier
        fields = [
            "supplier",
            "supplier_part_number",
            "unit_price",
            "currency",
            "lead_time_days",
            "min_order_qty",
            "is_preferred",
            "is_active",
            "notes",
        ]
        widgets = {
            "supplier": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "supplier_part_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "unit_price": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "currency": forms.TextInput(attrs={"class": TAILWIND_INPUT, "value": "SAR"}),
            "lead_time_days": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "min_order_qty": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "is_preferred": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }


class ItemIdentifierForm(forms.ModelForm):
    """Form for item identifiers (barcodes, QR codes, etc.)."""

    class Meta:
        model = ItemIdentifier
        fields = ["identifier_type", "value", "is_primary"]
        widgets = {
            "identifier_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "value": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Enter barcode or identifier"}),
            "is_primary": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }


class ItemBitSpecForm(forms.ModelForm):
    """Form for bit specifications."""

    class Meta:
        model = ItemBitSpec
        fields = [
            "bit_type",
            "iadc_code",
            "bit_size",
            "connection_type",
            "connection_size",
            "blade_count",
            "cutter_count",
            "cutter_size",
            "nozzle_count",
            "tfa_range_min",
            "tfa_range_max",
            "weight_on_bit_min",
            "weight_on_bit_max",
            "rpm_min",
            "rpm_max",
            "formation_hardness",
            "application",
            "gauge_protection",
            "body_material",
            "notes",
        ]
        widgets = {
            "bit_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "iadc_code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., M422"}),
            "bit_size": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "placeholder": "inches"}),
            "connection_type": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., API REG"}),
            "connection_size": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., 6-5/8"}),
            "blade_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "cutter_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "cutter_size": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01", "placeholder": "mm"}),
            "nozzle_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "tfa_range_min": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
            "tfa_range_max": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
            "weight_on_bit_min": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.1", "placeholder": "klb"}),
            "weight_on_bit_max": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.1", "placeholder": "klb"}),
            "rpm_min": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "rpm_max": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "formation_hardness": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., Soft, Medium, Hard"}),
            "application": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., Directional, Vertical"}),
            "gauge_protection": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "body_material": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., Steel, Matrix"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class ItemCutterSpecForm(forms.ModelForm):
    """Form for cutter specifications."""

    class Meta:
        model = ItemCutterSpec
        fields = [
            "cutter_size",
            "thickness",
            "diamond_table_thickness",
            "grade",
            "substrate_material",
            "chamfer_type",
            "chamfer_angle",
            "chamfer_size",
            "braze_temp_min",
            "braze_temp_max",
            "impact_resistance",
            "abrasion_resistance",
            "thermal_stability_temp",
            "notes",
        ]
        widgets = {
            "cutter_size": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01", "placeholder": "mm"}),
            "thickness": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01", "placeholder": "mm"}),
            "diamond_table_thickness": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "placeholder": "mm"}),
            "grade": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., Premium, Standard"}),
            "substrate_material": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., Tungsten Carbide"}),
            "chamfer_type": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., Single, Double"}),
            "chamfer_angle": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.1", "placeholder": "degrees"}),
            "chamfer_size": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01", "placeholder": "mm"}),
            "braze_temp_min": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "placeholder": "C"}),
            "braze_temp_max": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "placeholder": "C"}),
            "impact_resistance": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., High, Medium, Low"}),
            "abrasion_resistance": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., High, Medium, Low"}),
            "thermal_stability_temp": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "placeholder": "C"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }
