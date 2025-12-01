from django.contrib import admin
from .models import Department, Position, Theme, SystemSetting, NumberSequence


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'manager', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['code', 'name']
    ordering = ['code']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'department', 'level', 'is_active']
    list_filter = ['is_active', 'department', 'level']
    search_fields = ['code', 'title']
    ordering = ['department', 'level']


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_dark', 'is_default', 'is_active']
    list_filter = ['is_dark', 'is_default', 'is_active']


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'value_type', 'category', 'is_editable']
    list_filter = ['category', 'value_type', 'is_editable']
    search_fields = ['key', 'description']


@admin.register(NumberSequence)
class NumberSequenceAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'prefix', 'current_value', 'padding']
    search_fields = ['code', 'name']
