from django.contrib import admin

from .models import ERPMapping, ERPSyncLog


@admin.register(ERPMapping)
class ERPMappingAdmin(admin.ModelAdmin):
    list_display = ["entity_type", "ardt_id", "erp_system", "erp_id", "is_active"]


@admin.register(ERPSyncLog)
class ERPSyncLogAdmin(admin.ModelAdmin):
    list_display = ["erp_system", "direction", "entity_type", "status", "started_at"]
