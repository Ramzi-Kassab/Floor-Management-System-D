"""
ARDT FMS - Supply Chain Admin Configuration
Sprint 6: Supply Chain & Finance Integration
"""
from django.contrib import admin

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


# =============================================================================
# Week 1: Vendor Management & Purchasing
# =============================================================================

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """Admin for Vendor Management"""
    list_display = ["vendor_code", "name", "status", "vendor_type", "is_active"]
    list_filter = ["status", "vendor_type", "country"]
    search_fields = ["vendor_code", "name", "tax_id"]
    readonly_fields = ["vendor_code", "created_at", "updated_at"]
    ordering = ["-created_at"]


@admin.register(VendorContact)
class VendorContactAdmin(admin.ModelAdmin):
    """Admin for Vendor Contacts"""
    list_display = ["vendor", "first_name", "last_name", "contact_type", "is_primary", "email"]
    list_filter = ["contact_type", "is_primary"]
    search_fields = ["first_name", "last_name", "email", "vendor__name"]
    list_select_related = ["vendor"]


@admin.register(PurchaseRequisition)
class PurchaseRequisitionAdmin(admin.ModelAdmin):
    """Admin for Purchase Requisitions"""
    list_display = ["requisition_number", "status", "priority", "requested_by", "required_date"]
    list_filter = ["status", "priority"]
    search_fields = ["requisition_number", "title", "description"]
    readonly_fields = ["requisition_number", "created_at", "updated_at"]
    list_select_related = ["requested_by", "department"]


@admin.register(PurchaseRequisitionLine)
class PurchaseRequisitionLineAdmin(admin.ModelAdmin):
    """Admin for PR Line Items"""
    list_display = ["requisition", "line_number", "item_description", "quantity_requested", "estimated_unit_price"]
    list_filter = ["requisition__status"]
    list_select_related = ["requisition"]


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """Admin for Purchase Orders"""
    list_display = ["po_number", "vendor", "status", "order_date", "total_amount"]
    list_filter = ["status", "order_type"]
    search_fields = ["po_number", "vendor__name"]
    readonly_fields = ["po_number", "created_at", "updated_at"]
    list_select_related = ["vendor", "created_by"]


@admin.register(PurchaseOrderLine)
class PurchaseOrderLineAdmin(admin.ModelAdmin):
    """Admin for PO Line Items"""
    list_display = ["purchase_order", "line_number", "item_description", "quantity_ordered", "unit_price"]
    list_filter = ["purchase_order__status"]
    list_select_related = ["purchase_order", "purchase_order__vendor"]


# =============================================================================
# Week 2: Receiving & Invoicing
# =============================================================================

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    """Admin for Goods Receipts"""
    list_display = ["receipt_number", "purchase_order", "status", "receipt_date"]
    list_filter = ["status", "receipt_type"]
    search_fields = ["receipt_number", "purchase_order__po_number"]
    readonly_fields = ["receipt_number", "created_at", "updated_at"]
    list_select_related = ["purchase_order", "purchase_order__vendor", "received_by"]


@admin.register(ReceiptLine)
class ReceiptLineAdmin(admin.ModelAdmin):
    """Admin for Receipt Line Items"""
    list_display = ["receipt", "line_number", "quantity_received", "inspection_status"]
    list_filter = ["inspection_status"]
    list_select_related = ["receipt", "po_line"]


@admin.register(VendorInvoice)
class VendorInvoiceAdmin(admin.ModelAdmin):
    """Admin for Vendor Invoices"""
    list_display = ["invoice_number", "vendor", "status", "invoice_date", "total_amount"]
    list_filter = ["status"]
    search_fields = ["invoice_number", "vendor_invoice_number", "vendor__name"]
    readonly_fields = ["invoice_number", "created_at", "updated_at"]
    list_select_related = ["vendor"]


@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    """Admin for Invoice Line Items"""
    list_display = ["vendor_invoice", "line_number", "description", "quantity", "unit_price"]
    list_filter = ["vendor_invoice__status"]
    list_select_related = ["vendor_invoice", "po_line"]


@admin.register(InvoiceMatch)
class InvoiceMatchAdmin(admin.ModelAdmin):
    """Admin for Three-Way Matching"""
    list_display = ["vendor_invoice", "purchase_order", "receipt", "match_status"]
    list_filter = ["match_status"]
    list_select_related = ["vendor_invoice", "purchase_order", "receipt"]


# =============================================================================
# Week 3: Costing & Finance
# =============================================================================

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    """Admin for Expense Categories"""
    list_display = ["category_code", "category_name", "parent_category", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["category_code", "category_name"]
    list_select_related = ["parent_category"]


@admin.register(CostAllocation)
class CostAllocationAdmin(admin.ModelAdmin):
    """Admin for Cost Allocations"""
    list_display = ["allocation_number", "cost_type", "cost_amount", "work_order"]
    list_filter = ["cost_type"]
    search_fields = ["allocation_number", "description"]
    readonly_fields = ["allocation_number", "created_at", "updated_at"]
    list_select_related = ["work_order", "expense_category"]


@admin.register(PaymentTerm)
class PaymentTermAdmin(admin.ModelAdmin):
    """Admin for Payment Terms"""
    list_display = ["term_code", "term_name", "due_days", "discount_days", "discount_percent", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["term_code", "term_name"]


@admin.register(VendorPayment)
class VendorPaymentAdmin(admin.ModelAdmin):
    """Admin for Vendor Payments"""
    list_display = ["payment_number", "vendor", "status", "payment_date", "payment_amount"]
    list_filter = ["status", "payment_method"]
    search_fields = ["payment_number", "vendor__name"]
    readonly_fields = ["payment_number", "created_at", "updated_at"]
    list_select_related = ["vendor"]


@admin.register(PaymentAllocation)
class PaymentAllocationAdmin(admin.ModelAdmin):
    """Admin for Payment Allocations"""
    list_display = ["payment", "vendor_invoice", "allocated_amount"]
    search_fields = ["payment__payment_number", "vendor_invoice__invoice_number"]
    list_select_related = ["payment", "vendor_invoice"]


# =============================================================================
# Legacy Models (for backward compatibility)
# =============================================================================

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Legacy Supplier Admin (deprecated - use Vendor instead)"""
    list_display = ["code", "name", "is_active"]
    list_filter = ["is_active"]


@admin.register(CAPA)
class CAPAAdmin(admin.ModelAdmin):
    """Admin for CAPA (Corrective and Preventive Action)"""
    list_display = ["capa_number", "title", "status"]
    list_filter = ["status"]
    search_fields = ["capa_number", "title"]
