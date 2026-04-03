"""
ARDT FMS - Reports Models
Version: 5.4
"""

from django.conf import settings
from django.db import models


class SavedReport(models.Model):
    """
    Saved report configurations for users.
    Allows users to save report filters and schedules.
    """

    class ReportType(models.TextChoices):
        WORK_ORDER = "WORK_ORDER", "Work Order Report"
        INVENTORY = "INVENTORY", "Inventory Report"
        QUALITY = "QUALITY", "Quality Report"
        MAINTENANCE = "MAINTENANCE", "Maintenance Report"
        SUPPLY_CHAIN = "SUPPLY_CHAIN", "Supply Chain Report"
        CUSTOM = "CUSTOM", "Custom Report"

    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=30, choices=ReportType.choices)
    description = models.TextField(blank=True)

    # Filter parameters stored as JSON
    filters = models.JSONField(default=dict, blank=True)

    # Ownership
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_reports",
    )
    is_public = models.BooleanField(default=False, help_text="Share with all users")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "saved_reports"
        ordering = ["-updated_at"]
        verbose_name = "Saved Report"
        verbose_name_plural = "Saved Reports"

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"


class ReportExportLog(models.Model):
    """Log of report exports for auditing."""

    class ExportFormat(models.TextChoices):
        EXCEL = "EXCEL", "Excel (.xlsx)"
        CSV = "CSV", "CSV (.csv)"
        PDF = "PDF", "PDF (.pdf)"

    report_type = models.CharField(max_length=50)
    export_format = models.CharField(max_length=10, choices=ExportFormat.choices)
    filters_applied = models.JSONField(default=dict, blank=True)
    record_count = models.IntegerField(default=0)

    # User who exported
    exported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_exports",
    )
    exported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "report_export_logs"
        ordering = ["-exported_at"]
        verbose_name = "Report Export Log"
        verbose_name_plural = "Report Export Logs"

    def __str__(self):
        return f"{self.report_type} - {self.export_format} - {self.exported_at}"
