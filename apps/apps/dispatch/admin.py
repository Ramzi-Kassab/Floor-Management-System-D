from django.contrib import admin

from .models import Dispatch, Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["code", "plate_number", "status", "is_active"]


@admin.register(Dispatch)
class DispatchAdmin(admin.ModelAdmin):
    list_display = ["dispatch_number", "customer", "status", "planned_date"]
