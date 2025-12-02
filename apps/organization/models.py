"""
ARDT FMS - Organization Models
Version: 5.4

Tables:
- departments (P1)
- positions (P1)
- themes (P1)
- system_settings (P1)
- number_sequences (P1)
"""

from django.conf import settings
from django.db import models


class Department(models.Model):
    """
    🟢 P1: Organizational departments.

    Examples: Manufacturing, Quality, Sales, Logistics
    """

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100, blank=True, help_text="Arabic name")
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_departments"
    )
    location = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "departments"
        ordering = ["code"]
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_path(self):
        """Get full department path (e.g., 'MANUFACTURING > QUALITY')."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class Position(models.Model):
    """
    🟢 P1: Job positions within the organization.

    Examples: Factory Manager, QC Inspector, Senior Technician
    """

    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=100)
    title_ar = models.CharField(max_length=100, blank=True, help_text="Arabic title")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="positions")
    level = models.IntegerField(default=1, help_text="Hierarchy level (1=entry, 5=executive)")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "positions"
        ordering = ["department", "level", "title"]
        verbose_name = "Position"
        verbose_name_plural = "Positions"

    def __str__(self):
        return self.title


class Theme(models.Model):
    """
    🟢 P1: UI themes for user customization.
    """

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    primary_color = models.CharField(max_length=20, default="#0066cc")
    secondary_color = models.CharField(max_length=20, default="#6c757d")
    sidebar_color = models.CharField(max_length=20, default="#1e293b")
    is_dark = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "themes"
        verbose_name = "Theme"
        verbose_name_plural = "Themes"

    def __str__(self):
        return self.name


class SystemSetting(models.Model):
    """
    🟢 P1: System-wide configuration settings.

    Key-value store for system configuration.
    """

    class SettingType(models.TextChoices):
        STRING = "STRING", "String"
        INTEGER = "INTEGER", "Integer"
        BOOLEAN = "BOOLEAN", "Boolean"
        JSON = "JSON", "JSON"
        TEXT = "TEXT", "Text"

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    value_type = models.CharField(max_length=20, choices=SettingType.choices, default=SettingType.STRING)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, default="general")
    is_editable = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "system_settings"
        ordering = ["category", "key"]
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return f"{self.key}: {self.value}"

    def get_value(self):
        """Get typed value."""
        if self.value_type == self.SettingType.INTEGER:
            return int(self.value)
        elif self.value_type == self.SettingType.BOOLEAN:
            return self.value.lower() in ("true", "1", "yes")
        elif self.value_type == self.SettingType.JSON:
            import json

            return json.loads(self.value)
        return self.value


class NumberSequence(models.Model):
    """
    🟢 P1: Auto-incrementing number sequences.

    Used for generating WO numbers, DRSS numbers, etc.
    """

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    prefix = models.CharField(max_length=10, blank=True)
    suffix = models.CharField(max_length=10, blank=True)
    padding = models.IntegerField(default=6, help_text="Number of digits")
    current_value = models.BigIntegerField(default=0)
    increment_by = models.IntegerField(default=1)
    reset_period = models.CharField(max_length=20, blank=True, help_text="YEARLY, MONTHLY, or blank for never")
    last_reset = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "number_sequences"
        verbose_name = "Number Sequence"
        verbose_name_plural = "Number Sequences"

    def __str__(self):
        return f"{self.code}: {self.get_formatted_number()}"

    def get_next_number(self):
        """Get and increment the sequence."""
        self.current_value += self.increment_by
        self.save(update_fields=["current_value"])
        return self.get_formatted_number()

    def get_formatted_number(self):
        """Get formatted number without incrementing."""
        number = str(self.current_value).zfill(self.padding)
        return f"{self.prefix}{number}{self.suffix}"
