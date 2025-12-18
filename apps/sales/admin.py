from django.contrib import admin

from .models import (
    Customer,
    CustomerContact,
    CustomerDocumentRequirement,
    Rig,
    SalesOrder,
    SalesOrderLine,
    Warehouse,
    Well,
)


class CustomerContactInline(admin.TabularInline):
    model = CustomerContact
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "customer_type", "is_aramco", "is_active"]
    list_filter = ["customer_type", "is_aramco", "is_active"]
    search_fields = ["code", "name"]
    inlines = [CustomerContactInline]


@admin.register(Rig)
class RigAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "customer", "is_active"]
    list_filter = ["customer", "is_active"]
    search_fields = ["code", "name"]
    list_select_related = ["customer"]


@admin.register(Well)
class WellAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "customer", "rig", "is_active"]
    list_filter = ["customer", "is_active"]
    search_fields = ["code", "name"]
    list_select_related = ["customer", "rig"]


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "warehouse_type", "is_active"]
    list_filter = ["warehouse_type", "is_active"]


class SalesOrderLineInline(admin.TabularInline):
    model = SalesOrderLine
    extra = 0


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ["so_number", "customer", "status", "order_date", "total_amount"]
    list_filter = ["status", "customer"]
    search_fields = ["so_number", "customer__name"]
    list_select_related = ["customer", "created_by"]
    inlines = [SalesOrderLineInline]


@admin.register(SalesOrderLine)
class SalesOrderLineAdmin(admin.ModelAdmin):
    list_display = ["sales_order", "line_number", "description", "quantity", "status"]
    list_filter = ["status"]
    list_select_related = ["sales_order", "sales_order__customer"]


@admin.register(CustomerDocumentRequirement)
class CustomerDocumentRequirementAdmin(admin.ModelAdmin):
    list_display = ["customer", "document_type", "is_required"]
    list_filter = ["is_required", "customer"]
    search_fields = ["document_type", "customer__name"]
    list_select_related = ["customer"]
