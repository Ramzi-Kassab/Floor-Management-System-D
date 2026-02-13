"""
ERP Automation Admin

Admin interface for managing workflows, locators, and executions.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Locator,
    LocatorStrategy,
    Workflow,
    WorkflowStep,
    RecordingSession,
    RecordedAction,
    WorkflowExecution,
    StepExecution,
    FieldMapping,
    ItemCounter,
    ERPRoute,
    ERPJobData,
    WorkflowChain,
    WorkflowChainLink,
    ChainExecution,
)


# =============================================================================
# INLINE ADMINS
# =============================================================================

class LocatorStrategyInline(admin.TabularInline):
    model = LocatorStrategy
    extra = 1
    fields = ["strategy_type", "value", "priority", "is_active", "success_rate_display"]
    readonly_fields = ["success_rate_display"]

    def success_rate_display(self, obj):
        if obj.pk:
            rate = obj.success_rate
            color = "green" if rate > 80 else "orange" if rate > 50 else "red"
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, rate
            )
        return "-"
    success_rate_display.short_description = "Success Rate"


class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 1
    fields = [
        "order", "name", "action_type", "locator",
        "value_field", "value_static", "condition_value", "is_active"
    ]
    autocomplete_fields = ["locator"]
    ordering = ["order"]


class FieldMappingInline(admin.TabularInline):
    model = FieldMapping
    extra = 1
    fields = ["excel_column", "erp_field", "locator", "is_required", "is_active"]
    autocomplete_fields = ["locator"]


class RecordedActionInline(admin.TabularInline):
    model = RecordedAction
    extra = 0
    fields = ["order", "action_type", "element_name", "input_value", "timestamp"]
    readonly_fields = ["order", "action_type", "element_name", "input_value", "timestamp"]
    ordering = ["order"]

    def has_add_permission(self, request, obj=None):
        return False


class StepExecutionInline(admin.TabularInline):
    model = StepExecution
    extra = 0
    fields = ["step", "status", "started_at", "completed_at", "retry_count", "error_message"]
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


# =============================================================================
# MODEL ADMINS
# =============================================================================

@admin.register(Locator)
class LocatorAdmin(admin.ModelAdmin):
    list_display = [
        "name", "application", "page_context",
        "is_dynamic", "requires_scroll", "strategy_count", "updated_at"
    ]
    list_filter = ["application", "is_dynamic", "requires_scroll"]
    search_fields = ["name", "description", "page_context"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [LocatorStrategyInline]

    fieldsets = (
        (None, {
            "fields": ("name", "description")
        }),
        ("Context", {
            "fields": ("application", "page_context", "screenshot")
        }),
        ("Behavior", {
            "fields": ("is_dynamic", "requires_scroll", "requires_wait", "default_timeout")
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def strategy_count(self, obj):
        count = obj.strategies.filter(is_active=True).count()
        return format_html('<strong>{}</strong>', count)
    strategy_count.short_description = "Strategies"


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = [
        "name", "application", "status",
        "step_count", "execution_count", "updated_at"
    ]
    list_filter = ["application", "status"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [WorkflowStepInline, FieldMappingInline]

    fieldsets = (
        (None, {
            "fields": ("name", "description", "status")
        }),
        ("Target", {
            "fields": ("target_url", "application")
        }),
        ("Data Configuration", {
            "fields": ("valid_sheets", "required_fields", "condition_field")
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def step_count(self, obj):
        return obj.steps.filter(is_active=True).count()
    step_count.short_description = "Steps"

    def execution_count(self, obj):
        total = obj.executions.count()
        success = obj.executions.filter(status="success").count()
        return format_html('{} <span style="color:green;">({})</span>', total, success)
    execution_count.short_description = "Executions"


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = [
        "workflow", "order", "name", "action_type",
        "locator", "condition_value", "is_active"
    ]
    list_filter = ["workflow", "action_type", "is_active"]
    search_fields = ["name", "workflow__name"]
    autocomplete_fields = ["workflow", "locator", "error_handler_step"]
    ordering = ["workflow", "order"]

    fieldsets = (
        (None, {
            "fields": ("workflow", "order", "name", "is_active")
        }),
        ("Action", {
            "fields": ("action_type", "locator")
        }),
        ("Value", {
            "fields": ("value_static", "value_field", "value_template")
        }),
        ("Conditional", {
            "fields": ("condition_value",)
        }),
        ("Options", {
            "fields": (
                "clear_before_fill", "press_key_after",
                "wait_after", "timeout", "max_retries"
            ),
            "classes": ("collapse",)
        }),
        ("Error Handling", {
            "fields": ("continue_on_error", "error_handler_step", "save_result_as"),
            "classes": ("collapse",)
        }),
    )


@admin.register(RecordingSession)
class RecordingSessionAdmin(admin.ModelAdmin):
    list_display = [
        "name", "target_url", "is_active",
        "action_count", "started_at", "ended_at"
    ]
    list_filter = ["is_active"]
    search_fields = ["name", "target_url"]
    readonly_fields = ["started_at"]
    inlines = [RecordedActionInline]

    def action_count(self, obj):
        return obj.actions.count()
    action_count.short_description = "Actions"


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = [
        "workflow", "status", "job_data", "sheet_name",
        "started_at", "completed_at", "executed_by"
    ]
    list_filter = ["status", "workflow"]
    search_fields = ["workflow__name", "job_data__work_order_number"]
    readonly_fields = [
        "workflow", "status", "job_data", "excel_file_path", "sheet_name",
        "row_data", "context", "started_at", "completed_at",
        "error_message", "executed_by"
    ]
    inlines = [StepExecutionInline]

    def has_add_permission(self, request):
        return False


@admin.register(ItemCounter)
class ItemCounterAdmin(admin.ModelAdmin):
    list_display = [
        "account_type", "prefix", "current_number",
        "next_preview", "updated_at"
    ]
    search_fields = ["account_type", "prefix"]
    readonly_fields = ["updated_at"]

    def next_preview(self, obj):
        return format_html('<code>{}</code>', obj.get_next_preview())
    next_preview.short_description = "Next Number"

    actions = ["reset_counters"]

    @admin.action(description="Reset selected counters to 1")
    def reset_counters(self, request, queryset):
        for counter in queryset:
            counter.reset(1)
        self.message_user(request, f"Reset {queryset.count()} counters")


# =============================================================================
# REGISTER REMAINING MODELS
# =============================================================================

@admin.register(LocatorStrategy)
class LocatorStrategyAdmin(admin.ModelAdmin):
    list_display = [
        "locator", "strategy_type", "value_preview",
        "priority", "success_rate_display", "is_active"
    ]
    list_filter = ["strategy_type", "is_active", "locator__application"]
    search_fields = ["locator__name", "value"]
    autocomplete_fields = ["locator"]

    def value_preview(self, obj):
        return obj.value[:60] + "..." if len(obj.value) > 60 else obj.value
    value_preview.short_description = "Value"

    def success_rate_display(self, obj):
        rate = obj.success_rate
        color = "green" if rate > 80 else "orange" if rate > 50 else "red"
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, rate
        )
    success_rate_display.short_description = "Success Rate"


@admin.register(FieldMapping)
class FieldMappingAdmin(admin.ModelAdmin):
    list_display = [
        "workflow", "excel_column", "erp_field",
        "locator", "is_required", "is_active"
    ]
    list_filter = ["workflow", "is_required", "is_active"]
    search_fields = ["excel_column", "erp_field", "workflow__name"]
    autocomplete_fields = ["workflow", "locator"]


@admin.register(RecordedAction)
class RecordedActionAdmin(admin.ModelAdmin):
    list_display = [
        "session", "order", "action_type",
        "element_name", "input_preview", "timestamp"
    ]
    list_filter = ["action_type", "session"]
    search_fields = ["element_name", "element_id", "input_value"]
    readonly_fields = [
        "session", "order", "action_type", "element_tag",
        "element_id", "element_name", "element_class",
        "element_xpath", "element_css", "element_text",
        "element_aria_label", "element_placeholder",
        "element_rect", "screenshot", "page_url", "page_title",
        "input_value", "key_pressed", "timestamp", "duration_ms"
    ]

    def input_preview(self, obj):
        return obj.input_value[:30] + "..." if len(obj.input_value) > 30 else obj.input_value
    input_preview.short_description = "Input"

    def has_add_permission(self, request):
        return False


# =============================================================================
# ERP ROUTE & JOB DATA ADMINS
# =============================================================================

@admin.register(ERPRoute)
class ERPRouteAdmin(admin.ModelAdmin):
    list_display = [
        "route_number", "name", "bit_type", "level", "size_class",
        "has_port", "has_usr", "has_hardfacing", "has_crush_shear",
        "approved", "is_active"
    ]
    list_filter = [
        "bit_type", "level", "size_class", "approved", "is_active",
        "has_port", "has_usr", "has_hardfacing", "has_crush_shear"
    ]
    search_fields = ["route_number", "name", "item_group"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (None, {
            "fields": ("route_number", "name", "item_group")
        }),
        ("Classification", {
            "fields": ("bit_type", "level", "size_class", "has_port")
        }),
        ("FC Repair Modifiers", {
            "fields": ("has_usr", "has_hardfacing", "has_crush_shear",
                       "has_retro", "has_grinding")
        }),
        ("RC-Specific", {
            "fields": ("is_sealed", "has_cc"),
            "classes": ("collapse",)
        }),
        ("Approval", {
            "fields": ("approved", "approved_by", "is_active")
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(ERPJobData)
class ERPJobDataAdmin(admin.ModelAdmin):
    list_display = [
        "work_order_number", "serial_number", "size_raw", "account",
        "item_group", "body_material", "route", "status", "created_at"
    ]
    list_filter = ["status", "account", "item_group", "body_material", "size_class"]
    search_fields = ["work_order_number", "serial_number", "l5_mat_full", "l5_mat_original"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["route"]
    raw_id_fields = ["created_by"]

    fieldsets = (
        (None, {
            "fields": ("work_order_number", "serial_number", "status", "source_file")
        }),
        ("Raw Data", {
            "fields": ("size_raw", "size_inches", "smi_type", "l5_mat_full",
                       "date_received", "account", "contract_number", "vendor_number",
                       "l3_l4_mat", "evaluated_by", "reviewed_by")
        }),
        ("Derived Fields", {
            "fields": ("l5_mat_original", "body_material", "item_group",
                       "size_class", "has_port")
        }),
        ("Repair Modifiers", {
            "fields": ("has_usr", "has_hardfacing", "has_crush_shear",
                       "is_rerun", "is_inspection_only", "is_scrap")
        }),
        ("Route", {
            "fields": ("route", "route_override")
        }),
        ("ERP Output", {
            "fields": ("item_number", "production_order_number", "transfer_order_number")
        }),
        ("Cutter Data (JSON)", {
            "fields": ("cutter_bom_data", "modified_cutters_data"),
            "classes": ("collapse",)
        }),
        ("Notes & Metadata", {
            "fields": ("notes", "created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


# =============================================================================
# WORKFLOW CHAIN ADMINS
# =============================================================================

class WorkflowChainLinkInline(admin.TabularInline):
    model = WorkflowChainLink
    extra = 1
    fields = [
        "order", "workflow", "name", "wait_before_ms",
        "navigate_url", "condition_value", "is_active"
    ]
    autocomplete_fields = ["workflow"]
    ordering = ["order"]


@admin.register(WorkflowChain)
class WorkflowChainAdmin(admin.ModelAdmin):
    list_display = [
        "name", "status", "link_count_display",
        "execution_count_display", "keep_browser_open",
        "stop_on_failure", "updated_at"
    ]
    list_filter = ["status"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [WorkflowChainLinkInline]

    fieldsets = (
        (None, {
            "fields": ("name", "description", "status")
        }),
        ("Execution Options", {
            "fields": ("condition_field", "stop_on_failure", "keep_browser_open")
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def link_count_display(self, obj):
        count = obj.links.filter(is_active=True).count()
        return format_html('<strong>{}</strong>', count)
    link_count_display.short_description = "Links"

    def execution_count_display(self, obj):
        total = obj.executions.count()
        success = obj.executions.filter(status="success").count()
        return format_html('{} <span style="color:green;">({})</span>', total, success)
    execution_count_display.short_description = "Executions"


@admin.register(WorkflowChainLink)
class WorkflowChainLinkAdmin(admin.ModelAdmin):
    list_display = [
        "chain", "order", "workflow", "name",
        "wait_before_ms", "condition_value", "is_active"
    ]
    list_filter = ["chain", "is_active"]
    search_fields = ["chain__name", "workflow__name", "name"]
    autocomplete_fields = ["chain", "workflow"]
    ordering = ["chain", "order"]


@admin.register(ChainExecution)
class ChainExecutionAdmin(admin.ModelAdmin):
    list_display = [
        "chain", "job_data", "status",
        "progress_display", "started_at", "completed_at", "executed_by"
    ]
    list_filter = ["status", "chain"]
    search_fields = ["chain__name", "job_data__work_order_number"]
    readonly_fields = [
        "chain", "job_data", "status", "row_data", "context",
        "total_links", "completed_links", "current_link_order",
        "started_at", "completed_at", "error_message", "executed_by"
    ]

    def progress_display(self, obj):
        pct = obj.progress_percent
        color = "green" if pct == 100 else "orange" if pct > 0 else "gray"
        return format_html(
            '<span style="color: {};">{}/{} ({}%)</span>',
            color, obj.completed_links, obj.total_links, pct
        )
    progress_display.short_description = "Progress"

    def has_add_permission(self, request):
        return False
