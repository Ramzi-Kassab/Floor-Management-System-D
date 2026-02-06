"""
ARDT FMS - Work Orders Admin
Comprehensive admin registration for all workorders models.
"""

from django.contrib import admin

from .models import (
    # Core Models
    BitEvaluation,
    DrillBit,
    Location,
    BitEvent,
    WorkOrder,
    WorkOrderDocument,
    WorkOrderMaterial,
    WorkOrderPhoto,
    WorkOrderTimeLog,
    # Sprint 4 Models
    StatusTransitionLog,
    BitRepairHistory,
    SalvageItem,
    RepairApprovalAuthority,
    RepairEvaluation,
    RepairBOM,
    RepairBOMLine,
    ProcessRoute,
    ProcessRouteOperation,
    OperationExecution,
    WorkOrderCost,
    # Job Card Models
    CutterEvaluationMatrix,
    CutterEvaluationEntry,
    RouterSheetEntry,
    EvaluationChecklist,
    LPTReport,
    APIThreadInspection,
    InstructionRule,
    InstructionRuleCondition,
    # Production Planning
    ProductionPlanEntry,
)


# =============================================================================
# LOCATION & BIT EVENT
# =============================================================================

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "location_type", "is_active"]
    list_filter = ["location_type", "is_active"]
    search_fields = ["code", "name"]
    ordering = ["location_type", "name"]


@admin.register(BitEvent)
class BitEventAdmin(admin.ModelAdmin):
    list_display = ["bit", "event_type", "event_date", "location", "performed_by"]
    list_filter = ["event_type", "location"]
    search_fields = ["bit__serial_number", "notes"]
    list_select_related = ["bit", "location", "performed_by", "work_order"]
    date_hierarchy = "event_date"
    readonly_fields = ["created_at"]


# =============================================================================
# DRILL BIT
# =============================================================================

@admin.register(DrillBit)
class DrillBitAdmin(admin.ModelAdmin):
    list_display = [
        "serial_number", "bit_type", "size", "lifecycle_status",
        "physical_status", "bit_location", "customer"
    ]
    list_filter = ["bit_type", "status", "lifecycle_status", "physical_status", "customer"]
    search_fields = ["serial_number", "qr_code", "mat_number"]
    list_select_related = ["design", "customer", "current_location", "bit_location"]
    readonly_fields = ["created_at", "updated_at", "qr_code"]
    fieldsets = (
        ("Basic Info", {
            "fields": ("serial_number", "bit_type", "size", "mat_number", "iadc_code", "qr_code")
        }),
        ("Status", {
            "fields": ("status", "lifecycle_status", "physical_status", "accounting_status")
        }),
        ("Design & Location", {
            "fields": ("design", "bit_location", "current_location")
        }),
        ("Customer & Tracking", {
            "fields": ("customer", "rig", "well")
        }),
        ("Costs", {
            "fields": ("original_cost", "total_repair_cost", "current_book_value")
        }),
        ("Counters", {
            "fields": ("deployment_count", "backload_count", "repair_count", "repair_count_usa")
        }),
        ("Dates", {
            "fields": ("received_date", "scrap_date", "last_deployed_date", "last_backload_date")
        }),
        ("Aramco Contract", {
            "fields": ("is_aramco_contract", "base_serial_number", "current_display_serial", "revision_number"),
            "classes": ("collapse",)
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )


# =============================================================================
# WORK ORDER
# =============================================================================

class WorkOrderMaterialInline(admin.TabularInline):
    model = WorkOrderMaterial
    extra = 0


class WorkOrderDocumentInline(admin.TabularInline):
    model = WorkOrderDocument
    extra = 0


class WorkOrderPhotoInline(admin.TabularInline):
    model = WorkOrderPhoto
    extra = 0


class WorkOrderTimeLogInline(admin.TabularInline):
    model = WorkOrderTimeLog
    extra = 0


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ["wo_number", "wo_type", "status", "priority", "customer", "drill_bit", "due_date"]
    list_filter = ["status", "wo_type", "priority", "customer"]
    search_fields = ["wo_number", "customer__name", "drill_bit__serial_number"]
    list_select_related = ["customer", "drill_bit", "assigned_to", "design"]
    inlines = [WorkOrderMaterialInline, WorkOrderDocumentInline, WorkOrderPhotoInline, WorkOrderTimeLogInline]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Basic Info", {
            "fields": ("wo_number", "wo_type", "status", "priority")
        }),
        ("Product", {
            "fields": ("drill_bit", "design", "bom")
        }),
        ("Customer & Destination", {
            "fields": ("customer", "sales_order", "rig", "well")
        }),
        ("Job Card Fields", {
            "fields": ("brazing_mat_no", "system_mat_no", "drss_no", "reference_po_no", "contract_no"),
            "classes": ("collapse",)
        }),
        ("Scheduling", {
            "fields": ("start_date", "due_date", "completed_date", "assigned_to")
        }),
        ("Notes", {
            "fields": ("description", "notes")
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )


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


# =============================================================================
# STATUS TRANSITION LOG
# =============================================================================

@admin.register(StatusTransitionLog)
class StatusTransitionLogAdmin(admin.ModelAdmin):
    list_display = ["content_object", "from_status", "to_status", "changed_by", "changed_at"]
    list_filter = ["from_status", "to_status"]
    search_fields = ["reason"]
    list_select_related = ["changed_by"]
    date_hierarchy = "changed_at"
    readonly_fields = ["changed_at"]


# =============================================================================
# BIT REPAIR HISTORY
# =============================================================================

@admin.register(BitRepairHistory)
class BitRepairHistoryAdmin(admin.ModelAdmin):
    list_display = ["drill_bit", "repair_number", "repair_type", "repair_date", "total_cost"]
    list_filter = ["repair_type"]
    search_fields = ["drill_bit__serial_number"]
    list_select_related = ["drill_bit", "work_order"]
    date_hierarchy = "repair_date"


# =============================================================================
# SALVAGE ITEMS
# =============================================================================

@admin.register(SalvageItem)
class SalvageItemAdmin(admin.ModelAdmin):
    list_display = ["salvage_number", "work_order", "salvage_type", "status", "condition_rating", "salvage_date"]
    list_filter = ["salvage_type", "status"]
    list_select_related = ["work_order", "drill_bit"]
    search_fields = ["salvage_number", "description"]
    date_hierarchy = "salvage_date"


# =============================================================================
# REPAIR APPROVAL AUTHORITY
# =============================================================================

@admin.register(RepairApprovalAuthority)
class RepairApprovalAuthorityAdmin(admin.ModelAdmin):
    list_display = ["name", "min_amount", "max_amount", "is_active"]
    list_filter = ["is_active"]


# =============================================================================
# REPAIR EVALUATION
# =============================================================================

@admin.register(RepairEvaluation)
class RepairEvaluationAdmin(admin.ModelAdmin):
    list_display = ["evaluation_number", "drill_bit", "status", "repair_recommended", "evaluated_by"]
    list_filter = ["status", "repair_recommended"]
    list_select_related = ["drill_bit", "evaluated_by", "approved_by"]
    search_fields = ["evaluation_number", "drill_bit__serial_number"]


# =============================================================================
# REPAIR BOM
# =============================================================================

class RepairBOMLineInline(admin.TabularInline):
    model = RepairBOMLine
    extra = 0


@admin.register(RepairBOM)
class RepairBOMAdmin(admin.ModelAdmin):
    list_display = ["work_order", "status", "estimated_material_cost", "actual_material_cost"]
    list_filter = ["status"]
    list_select_related = ["work_order", "approved_by"]
    inlines = [RepairBOMLineInline]
    date_hierarchy = "created_at"


# =============================================================================
# PROCESS ROUTE
# =============================================================================

class ProcessRouteOperationInline(admin.TabularInline):
    model = ProcessRouteOperation
    extra = 0
    ordering = ["sequence"]


@admin.register(ProcessRoute)
class ProcessRouteAdmin(admin.ModelAdmin):
    list_display = ["route_number", "name", "repair_type", "is_active", "version"]
    list_filter = ["repair_type", "is_active"]
    search_fields = ["route_number", "name"]
    inlines = [ProcessRouteOperationInline]


@admin.register(OperationExecution)
class OperationExecutionAdmin(admin.ModelAdmin):
    list_display = ["work_order", "route_operation", "sequence", "status", "start_time", "end_time"]
    list_filter = ["status"]
    list_select_related = ["work_order", "route_operation", "operator"]


# =============================================================================
# WORK ORDER COST
# =============================================================================

@admin.register(WorkOrderCost)
class WorkOrderCostAdmin(admin.ModelAdmin):
    list_display = ["work_order", "labor_cost", "actual_material_cost", "overhead_cost", "total_actual_cost"]
    readonly_fields = ["total_actual_cost"]


# =============================================================================
# CUTTER EVALUATION MATRIX
# =============================================================================

class CutterEvaluationEntryInline(admin.TabularInline):
    model = CutterEvaluationEntry
    extra = 0
    ordering = ["blade_number", "cutter_position"]


@admin.register(CutterEvaluationMatrix)
class CutterEvaluationMatrixAdmin(admin.ModelAdmin):
    list_display = ["work_order", "evaluation_type", "evaluation_number", "evaluated_by", "evaluated_at"]
    list_filter = ["evaluation_type"]
    list_select_related = ["work_order", "evaluated_by"]
    inlines = [CutterEvaluationEntryInline]


# =============================================================================
# ROUTER SHEET ENTRY
# =============================================================================

@admin.register(RouterSheetEntry)
class RouterSheetEntryAdmin(admin.ModelAdmin):
    list_display = ["work_order", "step_number", "step_description", "is_complete", "operator"]
    list_filter = ["is_complete"]
    list_select_related = ["work_order", "operator"]
    ordering = ["work_order", "step_number"]


# =============================================================================
# EVALUATION CHECKLIST (E-Checklist)
# =============================================================================

@admin.register(EvaluationChecklist)
class EvaluationChecklistAdmin(admin.ModelAdmin):
    list_display = ["work_order", "inspector", "inspection_date", "pass_count", "fail_count"]
    list_select_related = ["work_order", "inspector"]
    date_hierarchy = "inspection_date"


# =============================================================================
# LPT REPORT
# =============================================================================

@admin.register(LPTReport)
class LPTReportAdmin(admin.ModelAdmin):
    list_display = ["report_number", "work_order", "test_type", "result", "lpt_operator"]
    list_filter = ["result", "test_type"]
    list_select_related = ["work_order", "lpt_operator"]
    date_hierarchy = "created_at"


# =============================================================================
# API THREAD INSPECTION
# =============================================================================

@admin.register(APIThreadInspection)
class APIThreadInspectionAdmin(admin.ModelAdmin):
    list_display = ["inspection_number", "work_order", "inspection_date", "final_result", "inspector"]
    list_filter = ["final_result", "thread_repair_required"]
    list_select_related = ["work_order", "inspector"]
    date_hierarchy = "inspection_date"


# =============================================================================
# INSTRUCTION RULES
# =============================================================================

class InstructionRuleConditionInline(admin.TabularInline):
    model = InstructionRuleCondition
    extra = 0


@admin.register(InstructionRule)
class InstructionRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "priority", "is_active", "created_at"]
    list_filter = ["priority", "is_active"]
    search_fields = ["name", "instruction_text", "description"]
    ordering = ["-priority", "name"]
    inlines = [InstructionRuleConditionInline]


# =============================================================================
# PRODUCTION PLAN ENTRY
# =============================================================================

@admin.register(ProductionPlanEntry)
class ProductionPlanEntryAdmin(admin.ModelAdmin):
    list_display = [
        "drill_bit", "account", "priority", "status",
        "planned_date", "work_order", "created_at"
    ]
    list_filter = ["status", "priority", "account"]
    search_fields = ["drill_bit__serial_number", "notes"]
    list_select_related = ["drill_bit", "account", "work_order"]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["sequence", "-priority", "planned_date"]
    raw_id_fields = ["drill_bit", "work_order"]

    actions = ["create_work_orders"]

    @admin.action(description="Create Work Orders for selected entries")
    def create_work_orders(self, request, queryset):
        created = 0
        for entry in queryset.filter(status=ProductionPlanEntry.Status.PLANNED):
            entry.create_work_order(user=request.user)
            created += 1
        self.message_user(request, f"Created {created} work orders.")
