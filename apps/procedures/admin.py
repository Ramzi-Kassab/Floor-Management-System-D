from django.contrib import admin

from .models import (
    CheckpointType,
    Procedure,
    ProcedureStep,
    ProcedureVersion,
    StepBranch,
    StepCheckpoint,
    StepInput,
    StepOutput,
    StepType,
)


class ProcedureStepInline(admin.TabularInline):
    model = ProcedureStep
    extra = 0
    fields = ["step_number", "name", "step_type", "is_mandatory", "estimated_duration_minutes"]
    ordering = ["step_number"]


@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "category", "status", "revision", "is_active"]
    list_filter = ["status", "category", "applies_to", "is_active"]
    search_fields = ["code", "name"]
    ordering = ["code"]
    inlines = [ProcedureStepInline]


@admin.register(StepType)
class StepTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "icon", "color"]
    search_fields = ["code", "name"]


class StepCheckpointInline(admin.TabularInline):
    model = StepCheckpoint
    extra = 0


class StepBranchInline(admin.TabularInline):
    model = StepBranch
    extra = 0
    fk_name = "step"


class StepInputInline(admin.TabularInline):
    model = StepInput
    extra = 0


class StepOutputInline(admin.TabularInline):
    model = StepOutput
    extra = 0


@admin.register(ProcedureStep)
class ProcedureStepAdmin(admin.ModelAdmin):
    list_display = ["procedure", "step_number", "name", "step_type", "is_mandatory"]
    list_filter = ["procedure", "step_type", "is_mandatory"]
    search_fields = ["name", "procedure__code"]
    ordering = ["procedure", "step_number"]
    inlines = [StepCheckpointInline, StepBranchInline, StepInputInline, StepOutputInline]


@admin.register(CheckpointType)
class CheckpointTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "input_type"]
    search_fields = ["code", "name"]


@admin.register(StepCheckpoint)
class StepCheckpointAdmin(admin.ModelAdmin):
    list_display = ["step", "name", "check_type", "is_critical", "failure_action"]
    list_filter = ["check_type", "is_critical", "failure_action"]
    search_fields = ["name", "step__name"]


@admin.register(StepBranch)
class StepBranchAdmin(admin.ModelAdmin):
    list_display = ["step", "condition_description", "then_action", "is_default"]
    list_filter = ["then_action", "is_default"]


@admin.register(StepInput)
class StepInputAdmin(admin.ModelAdmin):
    list_display = ["step", "input_type", "name", "quantity", "is_consumed"]
    list_filter = ["input_type", "is_consumed"]


@admin.register(StepOutput)
class StepOutputAdmin(admin.ModelAdmin):
    list_display = ["step", "output_type", "name", "is_required"]
    list_filter = ["output_type", "is_required"]


@admin.register(ProcedureVersion)
class ProcedureVersionAdmin(admin.ModelAdmin):
    list_display = ["procedure", "version_number", "changed_by", "changed_at"]
    list_filter = ["procedure"]
    ordering = ["procedure", "-version_number"]
