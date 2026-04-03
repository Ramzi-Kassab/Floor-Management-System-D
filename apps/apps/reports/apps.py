"""
ARDT FMS - Reports App Configuration
Version: 5.4
"""

from django.apps import AppConfig


class ReportsConfig(AppConfig):
    """Reports application configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reports"
    verbose_name = "Reports & Analytics"
