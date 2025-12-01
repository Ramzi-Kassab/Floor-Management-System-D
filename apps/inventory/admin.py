from django.contrib import admin
from .models import InventoryCategory, InventoryLocation, InventoryItem, InventoryStock, InventoryTransaction

@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']

@admin.register(InventoryLocation)
class InventoryLocationAdmin(admin.ModelAdmin):
    list_display = ['warehouse', 'code', 'name', 'is_active']
    list_filter = ['warehouse', 'is_active']
    search_fields = ['code', 'name']

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'item_type', 'category', 'standard_cost', 'is_active']
    list_filter = ['item_type', 'category', 'is_active']
    search_fields = ['code', 'name']

@admin.register(InventoryStock)
class InventoryStockAdmin(admin.ModelAdmin):
    list_display = ['item', 'location', 'quantity_on_hand', 'quantity_reserved', 'quantity_available']
    list_filter = ['location__warehouse']
    search_fields = ['item__code', 'item__name']

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_number', 'transaction_type', 'item', 'quantity', 'transaction_date']
    list_filter = ['transaction_type', 'link_type']
    search_fields = ['transaction_number', 'item__code']
