"""
ARDT FMS - Execution Views
Version: 5.4 - Sprint 3

Views for Procedure Execution management.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, ListView, View

from apps.procedures.models import Procedure
from apps.workorders.models import WorkOrder

from .models import ProcedureExecution, StepExecution


class ExecutionListView(LoginRequiredMixin, ListView):
    """List all procedure executions."""

    model = ProcedureExecution
    template_name = "execution/execution_list.html"
    context_object_name = "executions"
    paginate_by = 25

    def get_queryset(self):
        queryset = ProcedureExecution.objects.select_related(
            "procedure", "work_order", "started_by"
        ).order_by("-created_at")

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(work_order__wo_number__icontains=search) | Q(procedure__code__icontains=search)
            )

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Procedure Executions"
        context["search_query"] = self.request.GET.get("q", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["status_choices"] = ProcedureExecution.Status.choices
        return context


class ExecutionDetailView(LoginRequiredMixin, DetailView):
    """View execution details with step progress."""

    model = ProcedureExecution
    template_name = "execution/execution_detail.html"
    context_object_name = "execution"

    def get_queryset(self):
        return ProcedureExecution.objects.select_related(
            "procedure", "work_order", "started_by", "completed_by", "current_step"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Execution - {self.object.work_order.wo_number}"
        context["step_executions"] = self.object.step_executions.select_related(
            "step", "step__step_type", "executed_by"
        ).order_by("step__step_number")

        # Calculate progress
        total = context["step_executions"].count()
        completed = context["step_executions"].filter(status="COMPLETED").count()
        context["progress"] = int((completed / total) * 100) if total > 0 else 0

        return context


class ExecutionStartView(LoginRequiredMixin, View):
    """Start a procedure execution for a work order."""

    def post(self, request, wo_pk, procedure_pk):
        work_order = get_object_or_404(WorkOrder, pk=wo_pk)
        procedure = get_object_or_404(Procedure, pk=procedure_pk)

        # Check if already has an active execution
        existing = ProcedureExecution.objects.filter(
            work_order=work_order,
            status__in=["PENDING", "IN_PROGRESS", "PAUSED"]
        ).first()

        if existing:
            messages.warning(request, "This work order already has an active procedure execution.")
            return redirect("execution:detail", pk=existing.pk)

        # Create execution
        execution = ProcedureExecution.objects.create(
            procedure=procedure,
            work_order=work_order,
            procedure_version=procedure.revision,
            status=ProcedureExecution.Status.IN_PROGRESS,
            started_at=timezone.now(),
            started_by=request.user,
        )

        # Create step executions for all steps
        first_step = None
        for step in procedure.steps.order_by("step_number"):
            step_exec = StepExecution.objects.create(
                execution=execution,
                step=step,
                status=StepExecution.Status.PENDING,
            )
            if first_step is None:
                first_step = step_exec

        # Set first step as current
        if first_step:
            execution.current_step = first_step.step
            first_step.status = StepExecution.Status.IN_PROGRESS
            first_step.started_at = timezone.now()
            first_step.save()
            execution.save()

        messages.success(request, f"Started execution of {procedure.code}.")
        return redirect("execution:detail", pk=execution.pk)


class StepCompleteView(LoginRequiredMixin, View):
    """Complete a step in an execution."""

    def post(self, request, execution_pk, step_pk):
        execution = get_object_or_404(ProcedureExecution, pk=execution_pk)
        step_execution = get_object_or_404(StepExecution, pk=step_pk, execution=execution)

        result = request.POST.get("result", "PASS")
        notes = request.POST.get("notes", "")

        # Complete the step
        step_execution.status = StepExecution.Status.COMPLETED
        step_execution.result = result
        step_execution.notes = notes
        step_execution.completed_at = timezone.now()
        step_execution.executed_by = request.user
        step_execution.save()

        # Find next step
        next_step = execution.step_executions.filter(
            step__step_number__gt=step_execution.step.step_number,
            status=StepExecution.Status.PENDING
        ).order_by("step__step_number").first()

        if next_step:
            # Move to next step
            next_step.status = StepExecution.Status.IN_PROGRESS
            next_step.started_at = timezone.now()
            next_step.save()
            execution.current_step = next_step.step
        else:
            # All steps completed
            execution.status = ProcedureExecution.Status.COMPLETED
            execution.completed_at = timezone.now()
            execution.completed_by = request.user
            execution.current_step = None

        # Update progress
        total = execution.step_executions.count()
        completed = execution.step_executions.filter(status=StepExecution.Status.COMPLETED).count()
        execution.progress_percent = int((completed / total) * 100) if total > 0 else 0
        execution.save()

        messages.success(request, f"Step {step_execution.step.step_number} completed.")
        return redirect("execution:detail", pk=execution_pk)


class StepSkipView(LoginRequiredMixin, View):
    """Skip a step in an execution."""

    def post(self, request, execution_pk, step_pk):
        execution = get_object_or_404(ProcedureExecution, pk=execution_pk)
        step_execution = get_object_or_404(StepExecution, pk=step_pk, execution=execution)

        if not step_execution.step.can_skip:
            messages.error(request, "This step cannot be skipped.")
            return redirect("execution:detail", pk=execution_pk)

        reason = request.POST.get("reason", "")

        step_execution.status = StepExecution.Status.SKIPPED
        step_execution.skip_reason = reason
        step_execution.completed_at = timezone.now()
        step_execution.executed_by = request.user
        step_execution.save()

        # Move to next step
        next_step = execution.step_executions.filter(
            step__step_number__gt=step_execution.step.step_number,
            status=StepExecution.Status.PENDING
        ).order_by("step__step_number").first()

        if next_step:
            next_step.status = StepExecution.Status.IN_PROGRESS
            next_step.started_at = timezone.now()
            next_step.save()
            execution.current_step = next_step.step
            execution.save()

        messages.info(request, f"Step {step_execution.step.step_number} skipped.")
        return redirect("execution:detail", pk=execution_pk)


class ExecutionPauseView(LoginRequiredMixin, View):
    """Pause an execution."""

    def post(self, request, pk):
        execution = get_object_or_404(ProcedureExecution, pk=pk)
        execution.status = ProcedureExecution.Status.PAUSED
        execution.paused_at = timezone.now()
        execution.save()
        messages.info(request, "Execution paused.")
        return redirect("execution:detail", pk=pk)


class ExecutionResumeView(LoginRequiredMixin, View):
    """Resume a paused execution."""

    def post(self, request, pk):
        execution = get_object_or_404(ProcedureExecution, pk=pk)
        execution.status = ProcedureExecution.Status.IN_PROGRESS
        execution.save()
        messages.success(request, "Execution resumed.")
        return redirect("execution:detail", pk=pk)
