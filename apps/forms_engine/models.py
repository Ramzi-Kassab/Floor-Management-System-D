"""
ARDT FMS - Forms Engine Models
Version: 5.4

Tables:
- form_templates (P1)
- form_sections (P1)
- field_types (P1)
- form_fields (P1)
- form_template_versions (P1) - NEW in v5.4
"""

from django.db import models
from django.conf import settings


class FormTemplate(models.Model):
    """
    🟢 P1: Dynamic form templates.
    
    Defines reusable form structures that can be attached to procedure steps.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ACTIVE = 'ACTIVE', 'Active'
        OBSOLETE = 'OBSOLETE', 'Obsolete'
    
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=10, default='1.0')
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_form_templates'
    )
    
    class Meta:
        db_table = 'form_templates'
        ordering = ['code']
        verbose_name = 'Form Template'
        verbose_name_plural = 'Form Templates'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def field_count(self):
        return FormField.objects.filter(section__template=self).count()


class FormSection(models.Model):
    """
    🟢 P1: Sections within a form template.
    
    Groups related fields together.
    """
    
    template = models.ForeignKey(
        FormTemplate,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sequence = models.IntegerField(default=0)
    is_collapsible = models.BooleanField(default=False)
    is_collapsed_default = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'form_sections'
        ordering = ['template', 'sequence']
        verbose_name = 'Form Section'
        verbose_name_plural = 'Form Sections'
    
    def __str__(self):
        return f"{self.template.code} - {self.name}"


class FieldType(models.Model):
    """
    🟢 P1: Types of form fields.
    
    Examples: TEXT, NUMBER, DATE, SELECT, CHECKBOX, FILE, SIGNATURE
    """
    
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    html_input_type = models.CharField(max_length=30, default='text')
    has_options = models.BooleanField(default=False, help_text='Requires dropdown options')
    has_validation = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = 'field_types'
        ordering = ['name']
        verbose_name = 'Field Type'
        verbose_name_plural = 'Field Types'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class FormField(models.Model):
    """
    🟢 P1: Fields within a form section.
    """
    
    section = models.ForeignKey(
        FormSection,
        on_delete=models.CASCADE,
        related_name='fields'
    )
    field_type = models.ForeignKey(
        FieldType,
        on_delete=models.PROTECT
    )
    
    name = models.CharField(max_length=100, help_text='Internal field name')
    label = models.CharField(max_length=200, help_text='Display label')
    placeholder = models.CharField(max_length=200, blank=True)
    help_text = models.TextField(blank=True)
    
    # Validation
    is_required = models.BooleanField(default=False)
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    min_value = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    regex_pattern = models.CharField(max_length=500, blank=True)
    validation_message = models.CharField(max_length=500, blank=True)
    
    # Options (for SELECT, RADIO, CHECKBOX types)
    options = models.JSONField(
        null=True,
        blank=True,
        help_text='[{"value": "A", "label": "Option A"}, ...]'
    )
    
    # Default value
    default_value = models.CharField(max_length=500, blank=True)
    
    # Display
    sequence = models.IntegerField(default=0)
    width = models.CharField(
        max_length=20,
        default='full',
        help_text='full, half, third, quarter'
    )
    is_readonly = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    
    # Conditional display
    depends_on_field = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dependent_fields'
    )
    depends_on_value = models.CharField(max_length=200, blank=True)
    
    class Meta:
        db_table = 'form_fields'
        ordering = ['section', 'sequence']
        verbose_name = 'Form Field'
        verbose_name_plural = 'Form Fields'
    
    def __str__(self):
        return f"{self.section.template.code} - {self.label}"


class FormTemplateVersion(models.Model):
    """
    🟢 P1: Version history for form templates (NEW in v5.4).
    """
    
    template = models.ForeignKey(
        FormTemplate,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.IntegerField()
    
    # Snapshot
    snapshot = models.JSONField(help_text='Full template JSON at this version')
    
    # Change tracking
    change_summary = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'form_template_versions'
        ordering = ['template', '-version_number']
        unique_together = ['template', 'version_number']
        verbose_name = 'Form Template Version'
        verbose_name_plural = 'Form Template Versions'
    
    def __str__(self):
        return f"{self.template.code} v{self.version_number}"
