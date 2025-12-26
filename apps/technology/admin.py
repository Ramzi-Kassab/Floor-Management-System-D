from django.contrib import admin

from .models import (
    BOM, BOMLine, Design, DesignCutterLayout,
    Account, DesignHDBS, DesignSMI, HDBSType, SMIType
)


class BOMLineInline(admin.TabularInline):
    model = BOMLine
    extra = 0


class CutterLayoutInline(admin.TabularInline):
    model = DesignCutterLayout
    extra = 0


class DesignHDBSInline(admin.TabularInline):
    model = DesignHDBS
    extra = 0
    readonly_fields = ['assigned_at']
    raw_id_fields = ['hdbs_type', 'assigned_by']


class DesignSMIInline(admin.TabularInline):
    model = DesignSMI
    extra = 0
    readonly_fields = ['assigned_at']
    raw_id_fields = ['smi_type', 'account', 'assigned_by']


@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display = ["mat_no", "hdbs_type", "smi_type", "size", "category", "status"]
    list_filter = ["category", "status"]
    search_fields = ["mat_no", "hdbs_type", "smi_type"]
    inlines = [DesignHDBSInline, DesignSMIInline, CutterLayoutInline]


@admin.register(BOM)
class BOMAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "design", "status", "revision"]
    list_filter = ["status", "design"]
    search_fields = ["code", "name"]
    inlines = [BOMLineInline]


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "name_ar", "sales_leader", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "name", "name_ar"]


@admin.register(HDBSType)
class HDBSTypeAdmin(admin.ModelAdmin):
    list_display = ["hdbs_name", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["hdbs_name"]
    filter_horizontal = ['sizes']


@admin.register(SMIType)
class SMITypeAdmin(admin.ModelAdmin):
    list_display = ["smi_name", "hdbs_type", "size", "is_active"]
    list_filter = ["is_active", "hdbs_type"]
    search_fields = ["smi_name"]
    raw_id_fields = ['hdbs_type', 'size']
