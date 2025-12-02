from django.contrib import admin

from .models import HOCReport, Incident, Journey


@admin.register(HOCReport)
class HOCReportAdmin(admin.ModelAdmin):
    list_display = ["hoc_number", "category", "status", "reported_at"]


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ["incident_number", "incident_type", "severity", "status"]


@admin.register(Journey)
class JourneyAdmin(admin.ModelAdmin):
    list_display = ["journey_number", "driver", "status", "planned_departure"]
