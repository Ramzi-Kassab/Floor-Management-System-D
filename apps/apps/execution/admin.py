from django.contrib import admin

from .models import (
    BranchEvaluation,
    CheckpointResult,
    FormFieldValue,
    FormSubmission,
    ProcedureExecution,
    StepExecution,
)


@admin.register(ProcedureExecution)
class ProcedureExecutionAdmin(admin.ModelAdmin):
    list_display = ["work_order", "procedure", "status", "progress_percent", "started_at"]
    list_filter = ["status", "procedure"]
    search_fields = ["work_order__wo_number", "procedure__code"]


@admin.register(StepExecution)
class StepExecutionAdmin(admin.ModelAdmin):
    list_display = ["execution", "step", "status", "result", "executed_by"]
    list_filter = ["status", "result"]


@admin.register(CheckpointResult)
class CheckpointResultAdmin(admin.ModelAdmin):
    list_display = ["step_execution", "checkpoint", "result", "evaluated_by"]
    list_filter = ["result"]


@admin.register(BranchEvaluation)
class BranchEvaluationAdmin(admin.ModelAdmin):
    list_display = ["step_execution", "branch", "condition_met", "action_taken"]


@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ["form_template", "step_execution", "submitted_by", "is_complete"]
    list_filter = ["is_complete", "is_valid"]


@admin.register(FormFieldValue)
class FormFieldValueAdmin(admin.ModelAdmin):
    list_display = ["submission", "field", "value", "is_valid"]
