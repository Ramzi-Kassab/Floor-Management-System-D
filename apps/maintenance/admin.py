from django.contrib import admin

from .models import (
    Equipment,
    EquipmentCategory,
    MaintenancePartsUsed,
    MaintenanceRequest,
    MaintenanceWorkOrder,
)


@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "parent", "is_active"]


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "category", "status", "next_maintenance"]
    list_filter = ["status", "category"]


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ["request_number", "equipment", "request_type", "status", "priority"]
    list_filter = ["status", "request_type", "priority"]


class MaintenancePartsUsedInline(admin.TabularInline):
    model = MaintenancePartsUsed
    extra = 0


@admin.register(MaintenanceWorkOrder)
class MaintenanceWorkOrderAdmin(admin.ModelAdmin):
    list_display = ["mwo_number", "equipment", "status", "assigned_to"]
    list_filter = ["status"]
    inlines = [MaintenancePartsUsedInline]
