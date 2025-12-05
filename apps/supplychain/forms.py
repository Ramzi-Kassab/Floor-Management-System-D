"""
ARDT FMS - Supply Chain Forms
Version: 5.4
"""

from django import forms

from .models import CAPA, GoodsReceipt, GRNLine, POLine, PRLine, PurchaseOrder, PurchaseRequisition, Supplier

# Tailwind CSS classes for consistent styling
TAILWIND_INPUT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_SELECT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
TAILWIND_TEXTAREA = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
TAILWIND_CHECKBOX = "w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"


class SupplierForm(forms.ModelForm):
    """Form for Supplier CRUD."""

    class Meta:
        model = Supplier
        fields = [
            "code",
            "name",
            "contact_person",
            "email",
            "phone",
            "address",
            "country",
            "payment_terms",
            "is_active",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "contact_person": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "email": forms.EmailInput(attrs={"class": TAILWIND_INPUT}),
            "phone": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "address": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "country": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "payment_terms": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., Net 30"}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }


class PurchaseRequisitionForm(forms.ModelForm):
    """Form for Purchase Requisition CRUD."""

    class Meta:
        model = PurchaseRequisition
        fields = ["required_date", "notes"]
        widgets = {
            "required_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class PRLineForm(forms.ModelForm):
    """Form for PR Line."""

    class Meta:
        model = PRLine
        fields = ["inventory_item", "quantity", "notes"]
        widgets = {
            "inventory_item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "quantity": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }


class PurchaseOrderForm(forms.ModelForm):
    """Form for Purchase Order CRUD."""

    class Meta:
        model = PurchaseOrder
        fields = ["supplier", "order_date", "expected_date", "notes"]
        widgets = {
            "supplier": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "order_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "expected_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class POLineForm(forms.ModelForm):
    """Form for PO Line."""

    class Meta:
        model = POLine
        fields = ["inventory_item", "quantity", "unit_price"]
        widgets = {
            "inventory_item": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "quantity": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "unit_price": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
        }


class GoodsReceiptForm(forms.ModelForm):
    """Form for Goods Receipt."""

    class Meta:
        model = GoodsReceipt
        fields = ["po", "receipt_date", "notes"]
        widgets = {
            "po": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "receipt_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class GRNLineForm(forms.ModelForm):
    """Form for GRN Line."""

    class Meta:
        model = GRNLine
        fields = ["po_line", "quantity_received", "lot_number"]
        widgets = {
            "po_line": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "quantity_received": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "lot_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
        }


class CAPAForm(forms.ModelForm):
    """Form for CAPA CRUD."""

    class Meta:
        model = CAPA
        fields = [
            "title",
            "ncr",
            "description",
            "root_cause",
            "corrective_action",
            "preventive_action",
            "status",
            "due_date",
            "assigned_to",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "ncr": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 4}),
            "root_cause": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "corrective_action": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "preventive_action": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "due_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "assigned_to": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }


class PRApprovalForm(forms.Form):
    """Form for PR approval/rejection."""

    ACTION_CHOICES = [
        ("approve", "Approve"),
        ("reject", "Reject"),
    ]

    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.Select(attrs={"class": TAILWIND_SELECT}))
    notes = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2, "placeholder": "Notes..."})
    )
