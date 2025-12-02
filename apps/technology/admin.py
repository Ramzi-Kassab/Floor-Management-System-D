from django.contrib import admin

from .models import BOM, BOMLine, Design, DesignCutterLayout


class BOMLineInline(admin.TabularInline):
    model = BOMLine
    extra = 0


class CutterLayoutInline(admin.TabularInline):
    model = DesignCutterLayout
    extra = 0


@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "bit_type", "size", "status"]
    list_filter = ["bit_type", "status"]
    search_fields = ["code", "name"]
    inlines = [CutterLayoutInline]


@admin.register(BOM)
class BOMAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "design", "status", "revision"]
    list_filter = ["status", "design"]
    search_fields = ["code", "name"]
    inlines = [BOMLineInline]
