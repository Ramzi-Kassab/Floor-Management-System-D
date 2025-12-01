from django.contrib import admin
from .models import DocumentCategory, Document

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'is_active']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'status', 'version']
    list_filter = ['status', 'category']
    search_fields = ['code', 'name']
