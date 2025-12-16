from django.contrib import admin

from .models import (
    BitEvaluation,
    BitEvent,
    BitSize,
    BitType,
    DrillBit,
    Location,
    WorkOrder,
    WorkOrderDocument,
    WorkOrderMaterial,
    WorkOrderPhoto,
    WorkOrderTimeLog,
)


# =============================================================================
# PHASE 2: REFERENCE DATA ADMIN
# =============================================================================


@admin.register(BitSize)
class BitSizeAdmin(admin.ModelAdmin):
    list_display = ["code", "size_decimal", "size_display", "size_inches", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "size_display"]
    ordering = ["size_decimal"]


@admin.register(BitType)
class BitTypeAdmin(admin.ModelAdmin):
    list_display = [
        "smi_name", "category", "size", "hdbs_name", "hdbs_mn",
        "body_material", "no_of_blades", "cutter_size", "order_level", "is_active"
    ]
    list_filter = ["category", "series", "body_material", "order_level", "is_active"]
    search_fields = ["smi_name", "hdbs_name", "hdbs_mn", "code", "name"]
    ordering = ["category", "series", "smi_name"]
    list_select_related = ["size"]

    fieldsets = (
        ("Identity", {
            "fields": ("category", "size", "smi_name", "hdbs_name", "series")
        }),
        ("Material Numbers", {
            "fields": ("hdbs_mn", "ref_hdbs_mn", "ardt_item_number")
        }),
        ("Technical Specs (FC Only)", {
            "fields": ("body_material", "no_of_blades", "cutter_size", "gage_length"),
            "classes": ("collapse",),
        }),
        ("Production", {
            "fields": ("order_level",)
        }),
        ("Legacy Fields", {
            "fields": ("code", "name"),
            "classes": ("collapse",),
        }),
        ("Status", {
            "fields": ("is_active", "description")
        }),
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "location_type", "rig", "is_active"]
    list_filter = ["location_type", "is_active"]
    search_fields = ["code", "name"]
    list_select_related = ["rig"]
    ordering = ["location_type", "name"]


@admin.register(BitEvent)
class BitEventAdmin(admin.ModelAdmin):
    list_display = ["bit", "event_type", "event_date", "performed_by", "location"]
    list_filter = ["event_type", "location"]
    search_fields = ["bit__serial_number", "notes"]
    list_select_related = ["bit", "performed_by", "location", "rig", "well"]
    date_hierarchy = "event_date"
    ordering = ["-event_date"]


# =============================================================================
# ORIGINAL ADMIN
# =============================================================================


@admin.register(DrillBit)
class DrillBitAdmin(admin.ModelAdmin):
    list_display = [
        "serial_number", "bit_type", "product_type", "bit_size_ref",
        "lifecycle_status", "status", "customer", "bit_location"
    ]
    list_filter = ["bit_type", "status", "lifecycle_status", "customer", "product_type"]
    search_fields = ["serial_number", "qr_code", "mat_number"]
    list_select_related = ["design", "customer", "current_location", "product_type", "bit_size_ref", "bit_location"]
    readonly_fields = ["finance_sn", "actual_repair_sn", "total_lifecycle_events"]

    fieldsets = (
        ("Identity", {
            "fields": ("serial_number", "bit_type", "product_type", "bit_size_ref", "mat_number", "qr_code")
        }),
        ("Status", {
            "fields": ("status", "lifecycle_status", "physical_status", "accounting_status")
        }),
        ("Location", {
            "fields": ("current_location", "bit_location", "customer", "rig", "well")
        }),
        ("Phase 2 Counters", {
            "fields": (
                "repair_count", "repair_count_usa", "rerun_count_factory", "rerun_count_field",
                "backload_count", "deployment_count"
            ),
            "classes": ("collapse",)
        }),
        ("Calculated Serial Numbers", {
            "fields": ("finance_sn", "actual_repair_sn", "total_lifecycle_events"),
            "classes": ("collapse",)
        }),
        ("Key Dates", {
            "fields": ("received_date", "last_deployed_date", "last_backload_date", "scrap_date"),
            "classes": ("collapse",)
        }),
        ("Sprint 4 Fields", {
            "fields": (
                "base_serial_number", "current_display_serial", "revision_number", "is_aramco_contract",
                "total_repairs", "last_repair_date", "last_repair_type",
                "original_cost", "total_repair_cost", "current_book_value"
            ),
            "classes": ("collapse",)
        }),
        ("Usage", {
            "fields": ("total_hours", "total_footage", "run_count"),
            "classes": ("collapse",)
        }),
    )


class WorkOrderMaterialInline(admin.TabularInline):
    model = WorkOrderMaterial
    extra = 0


class WorkOrderDocumentInline(admin.TabularInline):
    model = WorkOrderDocument
    extra = 0


class WorkOrderPhotoInline(admin.TabularInline):
    model = WorkOrderPhoto
    extra = 0


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ["wo_number", "wo_type", "status", "priority", "customer", "due_date"]
    list_filter = ["status", "wo_type", "priority", "customer"]
    search_fields = ["wo_number", "customer__name"]
    list_select_related = ["customer", "drill_bit", "assigned_to", "design"]
    inlines = [WorkOrderMaterialInline, WorkOrderDocumentInline, WorkOrderPhotoInline]


@admin.register(WorkOrderTimeLog)
class WorkOrderTimeLogAdmin(admin.ModelAdmin):
    list_display = ["work_order", "user", "start_time", "duration_minutes", "activity_type"]
    list_filter = ["activity_type"]
    list_select_related = ["work_order", "user"]


@admin.register(BitEvaluation)
class BitEvaluationAdmin(admin.ModelAdmin):
    list_display = ["drill_bit", "evaluation_date", "overall_condition", "recommendation"]
    list_filter = ["overall_condition", "recommendation"]
    list_select_related = ["drill_bit", "evaluated_by"]
