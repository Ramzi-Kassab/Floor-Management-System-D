"""
ARDT FMS - Inventory App Forms
Version: 5.4
"""

from django import forms

from .models import (
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
)

TAILWIND_INPUT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_SELECT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
TAILWIND_TEXTAREA = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_CHECKBOX = "rounded border-gray-300 text-blue-600 focus:ring-blue-500"


class InventoryCategoryForm(forms.ModelForm):
    """Form for inventory categories."""

    class Meta:
        model = InventoryCategory
        fields = ["code", "name", "parent", "description", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "CAT-001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Category Name"}),
            "parent": forms.Select(attrs={"class": TAILWIND_SELECT}),
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
    """Form for category attributes."""

    class Meta:
        model = CategoryAttribute
        fields = [
            "category",
            "attribute",
            "attribute_type",
            "min_value",
            "max_value",
            "options",
            "is_required",
            "is_used_in_name",
            "display_order",
            "is_inherited",
        ]
        widgets = {
            "category": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "attribute": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "attribute_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "min_value": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "max_value": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "options": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": '["Option1", "Option2"]'}),
            "is_required": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "is_used_in_name": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "display_order": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "is_inherited": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }


class ItemPlanningForm(forms.ModelForm):
    """Form for item planning records."""

    class Meta:
        model = ItemPlanning
        fields = [
            "item",
            "warehouse",
            "min_stock",
            "max_stock",
            "reorder_point",
            "reorder_quantity",
            "safety_stock",
            "lead_time_days",
            "is_active",
            "notes",
        ]
        widgets = {
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "warehouse": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "min_stock": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "max_stock": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "reorder_point": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "reorder_quantity": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "safety_stock": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "lead_time_days": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class ItemSupplierForm(forms.ModelForm):
    """Form for item supplier records."""

    class Meta:
        model = ItemSupplier
        fields = [
            "item",
            "supplier",
            "supplier_part_number",
            "supplier_description",
            "unit_cost",
            "currency",
            "min_order_qty",
            "lead_time_days",
            "priority",
            "is_preferred",
            "is_active",
            "notes",
        ]
        widgets = {
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "supplier": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "supplier_part_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "supplier_description": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "unit_cost": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "currency": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "SAR"}),
            "min_order_qty": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "lead_time_days": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "priority": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": "1"}),
            "is_preferred": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class ItemIdentifierForm(forms.ModelForm):
    """Form for item identifiers."""

    class Meta:
        model = ItemIdentifier
        fields = [
            "item",
            "identifier_type",
            "identifier_value",
            "description",
            "is_primary",
            "is_active",
        ]
        widgets = {
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "identifier_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "identifier_value": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "description": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "is_primary": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }


class ItemBitSpecForm(forms.ModelForm):
    """Form for item bit specifications."""

    class Meta:
        model = ItemBitSpec
        fields = [
            "item",
            "bit_size",
            "bit_type",
            "tfa",
            "blade_count",
            "cutter_count",
            "nozzle_count",
            "iadc_code",
            "notes",
        ]
        widgets = {
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "bit_size": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "bit_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "tfa": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "blade_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "cutter_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "nozzle_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "iadc_code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class ItemCutterSpecForm(forms.ModelForm):
    """Form for item cutter specifications."""

    class Meta:
        model = ItemCutterSpec
        fields = [
            "item",
            "cutter_type",
            "cutter_shape",
            "diameter",
            "thickness",
            "chamfer_size",
            "grade",
            "substrate",
            "notes",
        ]
        widgets = {
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "cutter_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "cutter_shape": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "diameter": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "thickness": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "chamfer_size": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "grade": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "substrate": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }
