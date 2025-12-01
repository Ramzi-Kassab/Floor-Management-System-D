from django.contrib import admin
from .models import Supplier, PurchaseRequisition, PurchaseOrder, GoodsReceipt, CAPA

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active']

@admin.register(PurchaseRequisition)
class PRAdmin(admin.ModelAdmin):
    list_display = ['pr_number', 'status', 'requested_by']

@admin.register(PurchaseOrder)
class POAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'supplier', 'status', 'order_date']

@admin.register(GoodsReceipt)
class GRNAdmin(admin.ModelAdmin):
    list_display = ['grn_number', 'po', 'receipt_date']

@admin.register(CAPA)
class CAPAAdmin(admin.ModelAdmin):
    list_display = ['capa_number', 'title', 'status']
