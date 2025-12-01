from django.contrib import admin
from .models import ScanCode, ScanLog

@admin.register(ScanCode)
class ScanCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'code_type', 'entity_type', 'is_external', 'is_active']
    list_filter = ['code_type', 'entity_type', 'is_external', 'is_active']
    search_fields = ['code']

@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    list_display = ['raw_code', 'purpose', 'scanned_by', 'scanned_at', 'is_valid']
    list_filter = ['purpose', 'is_valid']
