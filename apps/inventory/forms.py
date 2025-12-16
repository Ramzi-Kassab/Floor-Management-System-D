"""
ARDT FMS - Inventory App Forms
Version: 5.6
"""

from django import forms

from .models import (
    CategoryAttribute,
    InventoryCategory,
    InventoryItem,
    InventoryLocation,
    InventoryStock,
    InventoryTransaction,
    ItemAttributeValue,
    ItemVariant,
    MaterialLot,
    UnitOfMeasure,
)

TAILWIND_INPUT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_SELECT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
TAILWIND_TEXTAREA = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_CHECKBOX = "rounded border-gray-300 text-blue-600 focus:ring-blue-500"
TAILWIND_INPUT_SM = "w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"


class InventoryCategoryForm(forms.ModelForm):
    """Form for inventory categories with enhanced fields."""

    class Meta:
        model = InventoryCategory
        fields = [
            "code",
            "name",
            "parent",
            "item_type",
            "code_prefix",
            "name_template",
            "description",
            "is_active",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "CUTTERS"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Category Name"}),
            "parent": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "item_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "code_prefix": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "CUT (for auto-code)"}),
            "name_template": forms.TextInput(attrs={
                "class": TAILWIND_INPUT,
                "placeholder": "{material} {type} {size}mm {grade}"
            }),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }
        help_texts = {
            "code_prefix": "Prefix for auto-generated item codes (e.g., CUT → CUT-0001)",
            "name_template": "Template using {attribute_code} placeholders for auto-naming items",
        }


class CategoryAttributeForm(forms.ModelForm):
    """Form for category attributes."""

    class Meta:
        model = CategoryAttribute
        fields = [
            "code",
            "name",
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
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT_SM, "placeholder": "size"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT_SM, "placeholder": "Size"}),
            "attribute_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "unit": forms.TextInput(attrs={"class": TAILWIND_INPUT_SM, "placeholder": "mm"}),
            "min_value": forms.NumberInput(attrs={"class": TAILWIND_INPUT_SM, "step": "0.0001"}),
            "max_value": forms.NumberInput(attrs={"class": TAILWIND_INPUT_SM, "step": "0.0001"}),
            "options": forms.Textarea(attrs={
                "class": TAILWIND_TEXTAREA,
                "rows": 2,
                "placeholder": '["Option1", "Option2"] or [{"value": "opt1", "label": "Option 1"}]'
            }),
            "is_required": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "is_used_in_name": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "display_order": forms.NumberInput(attrs={"class": TAILWIND_INPUT_SM}),
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
    """Form for inventory items with enhanced fields."""

    class Meta:
        model = InventoryItem
        fields = [
            "code",
            "name",
            "description",
            "item_type",
            "category",
            "mat_number",
            "item_number",
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
            "code": forms.TextInput(attrs={
                "class": TAILWIND_INPUT,
                "placeholder": "Auto-generated or enter manually"
            }),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Item Name"}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "item_type": forms.Select(attrs={"class": TAILWIND_SELECT, "id": "id_item_type"}),
            "category": forms.Select(attrs={"class": TAILWIND_SELECT, "id": "id_category"}),
            "mat_number": forms.TextInput(attrs={
                "class": TAILWIND_INPUT,
                "placeholder": "SAP Legacy MAT No."
            }),
            "item_number": forms.TextInput(attrs={
                "class": TAILWIND_INPUT,
                "placeholder": "ERP Item No."
            }),
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


class ItemVariantForm(forms.ModelForm):
    """Form for item variants."""

    class Meta:
        model = ItemVariant
        fields = [
            "code",
            "name",
            "condition",
            "source_type",
            "customer",
            "standard_cost",
            "last_cost",
            "valuation_percentage",
            "source_bit_serial",
            "source_work_order",
            "is_active",
            "notes",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Auto-generated"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Variant Name"}),
            "condition": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "source_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "customer": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "standard_cost": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
            "last_cost": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
            "valuation_percentage": forms.NumberInput(attrs={
                "class": TAILWIND_INPUT,
                "step": "0.01",
                "min": "0",
                "max": "100"
            }),
            "source_bit_serial": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "source_work_order": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }


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


# =============================================================================
# MASTER DATA FORMS
# =============================================================================


class UnitOfMeasureForm(forms.ModelForm):
    """Form for units of measure."""

    class Meta:
        model = UnitOfMeasure
        fields = [
            "code",
            "name",
            "unit_type",
            "symbol",
            "base_unit",
            "conversion_factor",
            "is_active",
            "description",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "KG, M, EA"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Kilogram, Meter, Each"}),
            "unit_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "symbol": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "kg, m, pcs"}),
            "base_unit": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "conversion_factor": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.000001"}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }


class MaterialLotForm(forms.ModelForm):
    """Form for material lots."""

    class Meta:
        model = MaterialLot
        fields = [
            "lot_number",
            "inventory_item",
            "initial_quantity",
            "quantity_on_hand",
            "received_date",
            "manufacture_date",
            "expiry_date",
            "vendor",
            "purchase_order",
            "vendor_lot_number",
            "cert_number",
            "certificate",
            "location",
            "status",
            "unit_cost",
        ]
        widgets = {
            "lot_number": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "LOT-2024-001"}),
            "inventory_item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "initial_quantity": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "quantity_on_hand": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "received_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "manufacture_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "expiry_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "vendor": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "purchase_order": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "vendor_lot_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "cert_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "certificate": forms.FileInput(attrs={"class": TAILWIND_INPUT}),
            "location": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "unit_cost": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
        }
