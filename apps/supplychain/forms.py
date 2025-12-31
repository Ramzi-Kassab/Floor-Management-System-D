"""
ARDT FMS - Supply Chain Forms
Sprint 6: Supply Chain & Finance Integration
"""

from django import forms

from .models import (
    CAPA,
    CostAllocation,
    ExpenseCategory,
    InvoiceLine,
    InvoiceMatch,
    PaymentAllocation,
    PaymentTerm,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseRequisition,
    PurchaseRequisitionLine,
    Receipt,
    ReceiptLine,
    Supplier,
    Vendor,
    VendorContact,
    VendorInvoice,
    VendorPayment,
)

# Tailwind CSS classes for consistent styling
TAILWIND_INPUT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_SELECT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
TAILWIND_TEXTAREA = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
TAILWIND_CHECKBOX = "w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"


# =============================================================================
# Legacy Forms (backward compatibility)
# =============================================================================

class SupplierForm(forms.ModelForm):
    """Form for legacy Supplier CRUD (use VendorForm for new implementations)."""

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


# =============================================================================
# Week 1: Vendor Management & Purchasing Forms
# =============================================================================

class VendorForm(forms.ModelForm):
    """Form for Vendor management."""

    class Meta:
        model = Vendor
        fields = [
            "name",
            "dba_name",
            "vendor_type",
            "tax_id",
            "registration_number",
            "website",
            "phone",
            "email",
            "address_line_1",
            "address_line_2",
            "city",
            "state_province",
            "postal_code",
            "country",
            "default_payment_term",
            "currency_code",
            "internal_notes",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "dba_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "vendor_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "tax_id": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "registration_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "website": forms.URLInput(attrs={"class": TAILWIND_INPUT}),
            "phone": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "email": forms.EmailInput(attrs={"class": TAILWIND_INPUT}),
            "address_line_1": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "address_line_2": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "city": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "state_province": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "postal_code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "country": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "default_payment_term": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "currency_code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "internal_notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class VendorContactForm(forms.ModelForm):
    """Form for VendorContact."""

    class Meta:
        model = VendorContact
        fields = [
            "first_name",
            "last_name",
            "contact_type",
            "title",
            "department",
            "phone",
            "mobile",
            "email",
            "is_primary",
            "notes",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "last_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "contact_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "title": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "department": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "phone": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "mobile": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "email": forms.EmailInput(attrs={"class": TAILWIND_INPUT}),
            "is_primary": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }


class PurchaseRequisitionForm(forms.ModelForm):
    """Form for Purchase Requisition CRUD."""

    class Meta:
        model = PurchaseRequisition
        fields = ["title", "department", "priority", "required_date", "description", "justification"]
        widgets = {
            "title": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "department": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., Operations, Maintenance, Engineering"}),
            "priority": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "required_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "justification": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
        }


class PurchaseRequisitionLineForm(forms.ModelForm):
    """Form for PR Line Items."""

    class Meta:
        model = PurchaseRequisitionLine
        fields = ["item_description", "quantity_requested", "unit_of_measure", "estimated_unit_price", "notes"]
        widgets = {
            "item_description": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "quantity_requested": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "unit_of_measure": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "estimated_unit_price": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }


class PurchaseOrderForm(forms.ModelForm):
    """Form for Purchase Order CRUD."""

    class Meta:
        model = PurchaseOrder
        fields = ["vendor", "order_type", "order_date", "required_date"]
        widgets = {
            "vendor": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "order_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "order_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "required_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
        }


class PurchaseOrderLineForm(forms.ModelForm):
    """Form for PO Line Items."""

    class Meta:
        model = PurchaseOrderLine
        fields = ["item_description", "quantity_ordered", "unit_of_measure", "unit_price"]
        widgets = {
            "item_description": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "quantity_ordered": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "unit_of_measure": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "unit_price": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
        }


# =============================================================================
# Week 2: Receiving & Invoicing Forms
# =============================================================================

class ReceiptForm(forms.ModelForm):
    """Form for Goods Receipt."""

    class Meta:
        model = Receipt
        fields = ["purchase_order", "receipt_type", "receipt_date"]
        widgets = {
            "purchase_order": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "receipt_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "receipt_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
        }


class ReceiptLineForm(forms.ModelForm):
    """Form for Receipt Line Items."""

    class Meta:
        model = ReceiptLine
        fields = ["po_line", "quantity_received", "quantity_accepted", "quantity_rejected"]
        widgets = {
            "po_line": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "quantity_received": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "quantity_accepted": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "quantity_rejected": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
        }


class VendorInvoiceForm(forms.ModelForm):
    """Form for Vendor Invoice."""

    class Meta:
        model = VendorInvoice
        fields = ["vendor", "vendor_invoice_number", "invoice_date", "due_date", "purchase_order"]
        widgets = {
            "vendor": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "vendor_invoice_number": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "invoice_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "due_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "purchase_order": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }


class InvoiceLineForm(forms.ModelForm):
    """Form for Invoice Line Items."""

    class Meta:
        model = InvoiceLine
        fields = ["description", "quantity", "unit_price", "po_line"]
        widgets = {
            "description": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "quantity": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.001"}),
            "unit_price": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "po_line": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }


# =============================================================================
# Week 3: Costing & Finance Forms
# =============================================================================

class ExpenseCategoryForm(forms.ModelForm):
    """Form for Expense Category."""

    class Meta:
        model = ExpenseCategory
        fields = ["category_code", "category_name", "parent_category", "gl_account_code", "description", "is_active"]
        widgets = {
            "category_code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "category_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "parent_category": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "gl_account_code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }


class CostAllocationForm(forms.ModelForm):
    """Form for Cost Allocation."""

    class Meta:
        model = CostAllocation
        fields = ["cost_type", "description", "work_order", "cost_amount"]
        widgets = {
            "cost_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "description": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "work_order": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "cost_amount": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
        }


class PaymentTermForm(forms.ModelForm):
    """Form for Payment Term."""

    class Meta:
        model = PaymentTerm
        fields = ["term_code", "term_name", "due_days", "discount_days", "discount_percent", "description", "is_active"]
        widgets = {
            "term_code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "term_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "due_days": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "discount_days": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "discount_percent": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }


class VendorPaymentForm(forms.ModelForm):
    """Form for Vendor Payment."""

    class Meta:
        model = VendorPayment
        fields = ["vendor", "payment_method", "payment_date", "payment_amount"]
        widgets = {
            "vendor": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "payment_method": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "payment_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "payment_amount": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
        }


class PaymentAllocationForm(forms.ModelForm):
    """Form for Payment Allocation."""

    class Meta:
        model = PaymentAllocation
        fields = ["vendor_invoice", "allocated_amount"]
        widgets = {
            "vendor_invoice": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "allocated_amount": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"}),
        }


# =============================================================================
# CAPA Forms
# =============================================================================

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


# =============================================================================
# Legacy Form Aliases (for backward compatibility)
# =============================================================================

# These aliases allow old code to still work with new model names
PRLineForm = PurchaseRequisitionLineForm
POLineForm = PurchaseOrderLineForm
GoodsReceiptForm = ReceiptForm
GRNLineForm = ReceiptLineForm
