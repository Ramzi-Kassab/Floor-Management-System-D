from django.contrib import admin
from .models import FormTemplate, FormSection, FieldType, FormField, FormTemplateVersion

class FormSectionInline(admin.TabularInline):
    model = FormSection
    extra = 0

class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 0

@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'status', 'version', 'is_active']
    list_filter = ['status', 'is_active']
    search_fields = ['code', 'name']
    inlines = [FormSectionInline]

@admin.register(FormSection)
class FormSectionAdmin(admin.ModelAdmin):
    list_display = ['template', 'name', 'sequence']
    list_filter = ['template']
    inlines = [FormFieldInline]

@admin.register(FieldType)
class FieldTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'html_input_type', 'has_options']

@admin.register(FormField)
class FormFieldAdmin(admin.ModelAdmin):
    list_display = ['section', 'label', 'field_type', 'is_required', 'sequence']
    list_filter = ['field_type', 'is_required']

@admin.register(FormTemplateVersion)
class FormTemplateVersionAdmin(admin.ModelAdmin):
    list_display = ['template', 'version_number', 'changed_by', 'changed_at']
