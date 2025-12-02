from django.contrib import admin

from .models import NCR, Inspection, NCRPhoto


class NCRPhotoInline(admin.TabularInline):
    model = NCRPhoto
    extra = 0


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ["inspection_number", "inspection_type", "work_order", "status", "inspected_at"]
    list_filter = ["inspection_type", "status"]
    search_fields = ["inspection_number", "work_order__wo_number"]


@admin.register(NCR)
class NCRAdmin(admin.ModelAdmin):
    list_display = ["ncr_number", "title", "severity", "status", "disposition"]
    list_filter = ["severity", "status", "disposition"]
    search_fields = ["ncr_number", "title"]
    inlines = [NCRPhotoInline]
