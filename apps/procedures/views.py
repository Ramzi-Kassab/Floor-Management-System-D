"""
ARDT FMS - Procedures Views
Version: 5.4 - Sprint 3

Views for Procedure management.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from .forms import ProcedureForm, ProcedureStepForm, StepCheckpointForm
from .models import Procedure, ProcedureStep, StepCheckpoint


class ProcedureListView(LoginRequiredMixin, ListView):
    """List all procedures with filtering."""

    model = Procedure
    template_name = "procedures/procedure_list.html"
    context_object_name = "procedures"
    paginate_by = 25

    def get_queryset(self):
        queryset = Procedure.objects.select_related("responsible_role", "created_by").order_by("code")

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(Q(code__icontains=search) | Q(name__icontains=search))

        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category=category)

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Procedures"
        context["search_query"] = self.request.GET.get("q", "")
        context["current_category"] = self.request.GET.get("category", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["category_choices"] = Procedure.Category.choices
        context["status_choices"] = Procedure.Status.choices
        return context


class ProcedureDetailView(LoginRequiredMixin, DetailView):
    """View procedure details with steps."""

    model = Procedure
    template_name = "procedures/procedure_detail.html"
    context_object_name = "procedure"

    def get_queryset(self):
        return Procedure.objects.select_related("responsible_role", "reviewed_by", "approved_by", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Procedure {self.object.code}"
        context["steps"] = self.object.steps.select_related("step_type", "responsible_role").prefetch_related(
            "checkpoints"
        ).order_by("step_number")
        context["step_form"] = ProcedureStepForm()
        return context


class ProcedureCreateView(LoginRequiredMixin, CreateView):
    """Create a new procedure."""

    model = Procedure
    form_class = ProcedureForm
    template_name = "procedures/procedure_form.html"
    success_url = reverse_lazy("procedures:procedure_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Procedure"
        context["submit_text"] = "Create Procedure"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Procedure {form.instance.code} created successfully.")
        return super().form_valid(form)


class ProcedureUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing procedure."""

    model = Procedure
    form_class = ProcedureForm
    template_name = "procedures/procedure_form.html"

    def get_success_url(self):
        return reverse_lazy("procedures:procedure_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Procedure {self.object.code}"
        context["submit_text"] = "Update Procedure"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Procedure {self.object.code} updated successfully.")
        return super().form_valid(form)


class ProcedureStepCreateView(LoginRequiredMixin, View):
    """Add a step to a procedure."""

    def post(self, request, pk):
        procedure = get_object_or_404(Procedure, pk=pk)
        form = ProcedureStepForm(request.POST)
        if form.is_valid():
            step = form.save(commit=False)
            step.procedure = procedure
            step.save()
            messages.success(request, "Step added successfully.")
        else:
            messages.error(request, "Failed to add step.")
        return redirect("procedures:procedure_detail", pk=pk)


class ProcedureStepUpdateView(LoginRequiredMixin, UpdateView):
    """Update a procedure step."""

    model = ProcedureStep
    form_class = ProcedureStepForm
    template_name = "procedures/step_form.html"

    def get_success_url(self):
        return reverse_lazy("procedures:procedure_detail", kwargs={"pk": self.object.procedure.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Step {self.object.step_number}"
        context["procedure"] = self.object.procedure
        return context

    def form_valid(self, form):
        messages.success(self.request, "Step updated successfully.")
        return super().form_valid(form)


class ProcedureStepDeleteView(LoginRequiredMixin, View):
    """Delete a step from a procedure."""

    def post(self, request, pk, step_pk):
        step = get_object_or_404(ProcedureStep, pk=step_pk, procedure_id=pk)
        step.delete()
        messages.success(request, "Step deleted.")
        return redirect("procedures:procedure_detail", pk=pk)


class StepCheckpointCreateView(LoginRequiredMixin, View):
    """Add a checkpoint to a step."""

    def post(self, request, step_pk):
        step = get_object_or_404(ProcedureStep, pk=step_pk)
        form = StepCheckpointForm(request.POST)
        if form.is_valid():
            checkpoint = form.save(commit=False)
            checkpoint.step = step
            checkpoint.save()
            messages.success(request, "Checkpoint added.")
        else:
            messages.error(request, "Failed to add checkpoint.")
        return redirect("procedures:procedure_detail", pk=step.procedure.pk)
