"""
Cutter Map Admin Configuration
"""

from django.contrib import admin
from .models import CutterMapDocument, CutterMapHistory


@admin.register(CutterMapDocument)
class CutterMapDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'mat_number', 'sn_number', 'original_filename',
        'status', 'is_validated', 'created_by', 'created_at'
    ]
    list_filter = ['status', 'is_validated', 'created_at']
    search_fields = ['mat_number', 'sn_number', 'original_filename']
    readonly_fields = ['created_at', 'updated_at', 'extracted_data', 'edited_data']
    raw_id_fields = ['design', 'created_by']

    fieldsets = (
        ('Document Info', {
            'fields': ('original_filename', 'mat_number', 'sn_number', 'status')
        }),
        ('Files', {
            'fields': ('original_pdf', 'generated_pdf', 'generated_ppt')
        }),
        ('Validation', {
            'fields': ('is_validated', 'validation_messages')
        }),
        ('ERP Link', {
            'fields': ('design',)
        }),
        ('Data', {
            'fields': ('extracted_data', 'edited_data'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CutterMapHistory)
class CutterMapHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['document__mat_number', 'document__original_filename']
    readonly_fields = ['document', 'action', 'details', 'user', 'timestamp']
