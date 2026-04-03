"""
ARDT FMS - Reports Admin
Version: 5.4
"""

from django.contrib import admin

from .models import ReportExportLog, SavedReport


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    """Admin for saved reports."""

    list_display = ["name", "report_type", "created_by", "is_public", "last_run", "updated_at"]
    list_filter = ["report_type", "is_public", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at", "last_run"]


@admin.register(ReportExportLog)
class ReportExportLogAdmin(admin.ModelAdmin):
    """Admin for report export logs."""

    list_display = ["report_type", "export_format", "record_count", "exported_by", "exported_at"]
    list_filter = ["report_type", "export_format", "exported_at"]
    readonly_fields = ["report_type", "export_format", "filters_applied", "record_count", "exported_by", "exported_at"]
    date_hierarchy = "exported_at"
