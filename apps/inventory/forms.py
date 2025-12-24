"""
ARDT FMS - Inventory App Forms
Version: 5.4
"""

from django import forms

from django.forms import inlineformset_factory

from .models import (
    # Original models
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
    # Phase 0: Foundation
    Party,
    ConditionType,
    QualityStatus,
    AdjustmentReason,
    OwnershipType,
    # Phase 1: Lot Tracking
    MaterialLot,
    # Phase 2: Ledger
    StockLedger,
    StockBalance,
    # Phase 3: Documents
    GoodsReceiptNote,
    GRNLine,
    StockIssue,
    StockIssueLine,
    StockTransfer,
    StockTransferLine,
    StockAdjustment as StockAdjustmentDoc,
    StockAdjustmentLine,
    # Phase 4: Assets
    Asset,
    AssetMovement,
    # Phase 5: QC Gates
    QualityStatusChange,
    # Phase 6: Reservations
    StockReservation,
    # Phase 7: BOM
    BillOfMaterial,
    BOMLine,
    # Phase 8: Cycle Count
    CycleCountPlan,
    CycleCountSession,
    CycleCountLine,
)

TAILWIND_INPUT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_SELECT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
TAILWIND_TEXTAREA = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_CHECKBOX = "rounded border-gray-300 text-blue-600 focus:ring-blue-500"


class InventoryCategoryForm(forms.ModelForm):
    """Form for inventory categories."""

    # Hidden field for JSON config from template builder
    name_template_config = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = InventoryCategory
        fields = ["code", "name", "parent", "item_type", "code_prefix", "name_template", "name_template_config", "description", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "CAT-001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Category Name"}),
            "parent": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "item_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "code_prefix": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "CUT, MAT, NOZ"}),
            "name_template": forms.HiddenInput(),  # Now managed by template builder
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }

    def clean_name_template_config(self):
        """Parse JSON config string to dict."""
        config = self.cleaned_data.get('name_template_config')
        if config:
            import json
            try:
                return json.loads(config)
            except json.JSONDecodeError:
                return None
        return None


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


# =============================================================================
# PHASE 3: DOCUMENT FORMS (GRN, Issues, Transfers, Adjustments)
# =============================================================================


class GoodsReceiptNoteForm(forms.ModelForm):
    """Form for Goods Receipt Note header."""

    class Meta:
        model = GoodsReceiptNote
        fields = [
            "receipt_type",
            "warehouse",
            "supplier",
            "receipt_date",
            "source_reference",
            "owner_party",
            "ownership_type",
            "notes",
        ]
        widgets = {
            "receipt_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "warehouse": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "supplier": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "receipt_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "source_reference": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "PO-001 or RMA-001"}),
            "owner_party": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "ownership_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class GRNLineForm(forms.ModelForm):
    """Form for GRN line items."""

    class Meta:
        model = GRNLine
        fields = [
            "item",
            "lot",
            "location",
            "qty_expected",
            "qty_received",
            "unit_cost",
            "condition",
            "quality_status",
            "notes",
        ]
        widgets = {
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "lot": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "location": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "qty_expected": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "qty_received": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "unit_cost": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "condition": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "quality_status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "notes": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
        }


# GRN Line Formset
GRNLineFormSet = inlineformset_factory(
    GoodsReceiptNote,
    GRNLine,
    form=GRNLineForm,
    extra=1,
    can_delete=True,
)


class StockIssueForm(forms.ModelForm):
    """Form for Stock Issue header."""

    class Meta:
        model = StockIssue
        fields = [
            "issue_type",
            "warehouse",
            "issue_date",
            "reference",
            "issue_to_party",
            "notes",
        ]
        widgets = {
            "issue_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "warehouse": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "issue_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "reference": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "JOB-001 or SO-001"}),
            "issue_to_party": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class StockIssueLineForm(forms.ModelForm):
    """Form for Stock Issue line items."""

    class Meta:
        model = StockIssueLine
        fields = [
            "item",
            "lot",
            "location",
            "qty_requested",
            "qty_issued",
            "unit_cost",
            "notes",
        ]
        widgets = {
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "lot": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "location": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "qty_requested": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "qty_issued": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "unit_cost": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "notes": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
        }


StockIssueLineFormSet = inlineformset_factory(
    StockIssue,
    StockIssueLine,
    form=StockIssueLineForm,
    extra=1,
    can_delete=True,
)


class StockTransferForm(forms.ModelForm):
    """Form for Stock Transfer header."""

    class Meta:
        model = StockTransfer
        fields = [
            "transfer_type",
            "from_warehouse",
            "to_warehouse",
            "transfer_date",
            "notes",
        ]
        widgets = {
            "transfer_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "from_warehouse": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "to_warehouse": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "transfer_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class StockTransferLineForm(forms.ModelForm):
    """Form for Stock Transfer line items."""

    class Meta:
        model = StockTransferLine
        fields = [
            "item",
            "lot",
            "qty_requested",
            "qty_shipped",
            "qty_received",
            "notes",
        ]
        widgets = {
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "lot": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "qty_requested": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "qty_shipped": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "qty_received": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "notes": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
        }


StockTransferLineFormSet = inlineformset_factory(
    StockTransfer,
    StockTransferLine,
    form=StockTransferLineForm,
    extra=1,
    can_delete=True,
)


class StockAdjustmentDocForm(forms.ModelForm):
    """Form for Stock Adjustment document header."""

    class Meta:
        model = StockAdjustmentDoc
        fields = [
            "adjustment_type",
            "warehouse",
            "reason",
            "adjustment_date",
            "notes",
        ]
        widgets = {
            "adjustment_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "warehouse": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "reason": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "adjustment_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class StockAdjustmentLineForm(forms.ModelForm):
    """Form for Stock Adjustment line items."""

    class Meta:
        model = StockAdjustmentLine
        fields = [
            "item",
            "lot",
            "qty_system",
            "qty_counted",
            "qty_adjustment",
            "unit_cost",
            "notes",
        ]
        widgets = {
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "lot": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "qty_system": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "readonly": "readonly"}),
            "qty_counted": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "qty_adjustment": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "readonly": "readonly"}),
            "unit_cost": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "notes": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
        }


StockAdjustmentLineFormSet = inlineformset_factory(
    StockAdjustmentDoc,
    StockAdjustmentLine,
    form=StockAdjustmentLineForm,
    extra=1,
    can_delete=True,
)


# =============================================================================
# PHASE 4: ASSET FORMS
# =============================================================================


class AssetForm(forms.ModelForm):
    """Form for Asset master data."""

    class Meta:
        model = Asset
        fields = [
            "serial_number",
            "asset_tag",
            "item",
            "status",
            "condition",
            "quality_status",
            "current_location",
            "warehouse",
            "owner_party",
            "ownership_type",
            "custodian_party",
            "acquisition_date",
            "acquisition_cost",
            "in_service_date",
            "warranty_expiry",
            "next_service_date",
            "notes",
        ]
        widgets = {
            "serial_number": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "S/N or unique identifier"}),
            "asset_tag": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Optional internal tag"}),
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "condition": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "quality_status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "current_location": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "warehouse": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "owner_party": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "ownership_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "custodian_party": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "acquisition_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "acquisition_cost": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
            "in_service_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "warranty_expiry": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "next_service_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class AssetMovementForm(forms.ModelForm):
    """Form for recording Asset movements."""

    class Meta:
        model = AssetMovement
        fields = [
            "movement_type",
            "from_location",
            "to_location",
            "from_status",
            "to_status",
            "reason",
            "notes",
        ]
        widgets = {
            "movement_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "from_location": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "to_location": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "from_status": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "to_status": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "reason": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }


# =============================================================================
# PHASE 5: QC GATES FORMS
# =============================================================================


class QualityStatusChangeForm(forms.ModelForm):
    """Form for recording QC status changes."""

    class Meta:
        model = QualityStatusChange
        fields = [
            "change_type",
            "lot",
            "asset",
            "from_status",
            "to_status",
            "reason",
            "inspection_notes",
            "notes",
        ]
        widgets = {
            "change_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "lot": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "asset": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "from_status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "to_status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "reason": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2, "placeholder": "Reason for status change"}),
            "inspection_notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        lot = cleaned_data.get("lot")
        asset = cleaned_data.get("asset")

        if not lot and not asset:
            raise forms.ValidationError("Either a Lot or an Asset must be specified.")

        if lot and asset:
            raise forms.ValidationError("Specify either a Lot OR an Asset, not both.")

        return cleaned_data


# =============================================================================
# PHASE 6: RESERVATIONS FORMS
# =============================================================================


class StockReservationForm(forms.ModelForm):
    """Form for Stock Reservations."""

    class Meta:
        model = StockReservation
        fields = [
            "reservation_type",
            "item",
            "lot",
            "location",
            "qty_reserved",
            "reserved_for_party",
            "required_date",
            "expiry_date",
            "priority",
            "notes",
        ]
        widgets = {
            "reservation_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "lot": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "location": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "qty_reserved": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "reserved_for_party": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "required_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "expiry_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "priority": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": "1", "max": "10"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }


# =============================================================================
# PHASE 7: BOM FORMS
# =============================================================================


class BillOfMaterialForm(forms.ModelForm):
    """Form for Bill of Material header."""

    class Meta:
        model = BillOfMaterial
        fields = [
            "bom_code",
            "name",
            "parent_item",
            "version",
            "bom_type",
            "status",
            "effective_from",
            "effective_to",
            "base_quantity",
            "labor_cost",
            "overhead_cost",
            "notes",
        ]
        widgets = {
            "bom_code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "BOM-001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "BOM Name"}),
            "parent_item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "version": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "1.0"}),
            "bom_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "effective_from": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "effective_to": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "base_quantity": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "labor_cost": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
            "overhead_cost": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class BOMLineForm(forms.ModelForm):
    """Form for BOM line items (components)."""

    class Meta:
        model = BOMLine
        fields = [
            "line_number",
            "component_item",
            "component_type",
            "quantity_per",
            "uom",
            "is_optional",
            "scrap_percent",
            "notes",
        ]
        widgets = {
            "line_number": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "component_item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "component_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "quantity_per": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "uom": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "is_optional": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "scrap_percent": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01", "placeholder": "%"}),
            "notes": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
        }


BOMLineFormSet = inlineformset_factory(
    BillOfMaterial,
    BOMLine,
    form=BOMLineForm,
    extra=3,
    can_delete=True,
)


# =============================================================================
# PHASE 8: CYCLE COUNT FORMS
# =============================================================================


class CycleCountPlanForm(forms.ModelForm):
    """Form for Cycle Count Plan."""

    class Meta:
        model = CycleCountPlan
        fields = [
            "plan_code",
            "name",
            "plan_type",
            "warehouse",
            "start_date",
            "end_date",
            "count_frequency_a",
            "count_frequency_b",
            "count_frequency_c",
            "notes",
        ]
        widgets = {
            "plan_code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "CCP-2024-001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Q1 2024 Cycle Count"}),
            "plan_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "warehouse": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "start_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "count_frequency_a": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Days for A items"}),
            "count_frequency_b": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Days for B items"}),
            "count_frequency_c": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Days for C items"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class CycleCountSessionForm(forms.ModelForm):
    """Form for Cycle Count Session header."""

    class Meta:
        model = CycleCountSession
        fields = [
            "plan",
            "session_date",
            "warehouse",
            "location",
            "notes",
        ]
        widgets = {
            "plan": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "session_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "warehouse": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "location": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }


class CycleCountLineForm(forms.ModelForm):
    """Form for Cycle Count Line (individual count entries)."""

    class Meta:
        model = CycleCountLine
        fields = [
            "item",
            "lot",
            "location",
            "qty_system",
            "qty_counted",
            "notes",
        ]
        widgets = {
            "item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "lot": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "location": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "qty_system": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001", "readonly": "readonly"}),
            "qty_counted": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "notes": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
        }


CycleCountLineFormSet = inlineformset_factory(
    CycleCountSession,
    CycleCountLine,
    form=CycleCountLineForm,
    extra=5,
    can_delete=True,
)


# =============================================================================
# Reference Data Forms
# =============================================================================


class PartyForm(forms.ModelForm):
    """Form for Party (customers, suppliers, owners)."""

    class Meta:
        model = Party
        fields = [
            "code",
            "name",
            "party_type",
            "can_own_stock",
            "is_active",
            "notes",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "party_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "can_own_stock": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }


class ConditionTypeForm(forms.ModelForm):
    """Form for Condition Type (NEW, USED, REFURB, etc.)."""

    class Meta:
        model = ConditionType
        fields = [
            "code",
            "name",
            "description",
            "is_new",
            "is_saleable",
            "cost_multiplier",
            "display_order",
            "is_active",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
            "is_new": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
            "is_saleable": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
            "cost_multiplier": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
            "display_order": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
        }


class QualityStatusForm(forms.ModelForm):
    """Form for Quality Status (AVAILABLE, HOLD, QUARANTINE, etc.)."""

    class Meta:
        model = QualityStatus
        fields = [
            "code",
            "name",
            "description",
            "is_available",
            "is_initial",
            "is_terminal",
            "display_order",
            "is_active",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
            "is_available": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
            "is_initial": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
            "is_terminal": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
            "display_order": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
        }


class AdjustmentReasonForm(forms.ModelForm):
    """Form for Adjustment Reason codes."""

    class Meta:
        model = AdjustmentReason
        fields = [
            "code",
            "name",
            "description",
            "affects_valuation",
            "requires_approval",
            "is_active",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "description": forms.Textarea(attrs={"class": TAILWIND_INPUT, "rows": 2}),
            "affects_valuation": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
            "requires_approval": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
        }


class OwnershipTypeForm(forms.ModelForm):
    """Form for Ownership Type (OWNED, CONSIGNMENT, CUSTOMER, etc.)."""

    class Meta:
        model = OwnershipType
        fields = [
            "code",
            "name",
            "description",
            "is_ardt_owned",
            "requires_party",
            "affects_balance_sheet",
            "include_in_valuation",
            "display_order",
            "is_active",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "description": forms.Textarea(attrs={"class": TAILWIND_INPUT, "rows": 2}),
            "is_ardt_owned": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
            "requires_party": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
            "affects_balance_sheet": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
            "include_in_valuation": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
            "display_order": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-gray-300"}),
        }
