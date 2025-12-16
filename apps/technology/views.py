"""
ARDT FMS - Technology Views
Version: 5.4 - Sprint 3

Views for Design, BOM, and Cutter Layout management.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from .forms import BOMForm, BOMLineForm, DesignCutterLayoutForm, DesignForm
from .models import BOM, BOMLine, Design, DesignCutterLayout


# =============================================================================
# DESIGN VIEWS
# =============================================================================


class DesignListView(LoginRequiredMixin, ListView):
    """List all designs with filtering."""

    model = Design
    template_name = "technology/design_list.html"
    context_object_name = "designs"
    paginate_by = 25

    def get_queryset(self):
        queryset = Design.objects.select_related("designed_by", "created_by").order_by("code")

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(name__icontains=search) | Q(iadc_code__icontains=search)
            )

        bit_type = self.request.GET.get("bit_type")
        if bit_type:
            queryset = queryset.filter(bit_type=bit_type)

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Designs"
        context["search_query"] = self.request.GET.get("q", "")
        context["current_bit_type"] = self.request.GET.get("bit_type", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["bit_type_choices"] = Design.BitType.choices
        context["status_choices"] = Design.Status.choices
        return context


class DesignDetailView(LoginRequiredMixin, DetailView):
    """View design details with BOM and cutter layouts."""

    model = Design
    template_name = "technology/design_detail.html"
    context_object_name = "design"

    def get_queryset(self):
        return Design.objects.select_related("designed_by", "approved_by", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Design {self.object.code}"
        context["boms"] = self.object.boms.select_related("created_by").order_by("-created_at")
        context["cutter_layouts"] = self.object.cutter_layouts.order_by("blade_number", "position_number")
        context["work_orders_count"] = self.object.work_orders.count()
        return context


class DesignCreateView(LoginRequiredMixin, CreateView):
    """Create a new design."""

    model = Design
    form_class = DesignForm
    template_name = "technology/design_form.html"
    success_url = reverse_lazy("technology:design_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Design"
        context["submit_text"] = "Create Design"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Design {form.instance.code} created successfully.")
        return super().form_valid(form)


class DesignUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing design."""

    model = Design
    form_class = DesignForm
    template_name = "technology/design_form.html"

    def get_success_url(self):
        return reverse_lazy("technology:design_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Design {self.object.code}"
        context["submit_text"] = "Update Design"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Design {self.object.code} updated successfully.")
        return super().form_valid(form)


# =============================================================================
# BOM VIEWS
# =============================================================================


class BOMListView(LoginRequiredMixin, ListView):
    """List all BOMs."""

    model = BOM
    template_name = "technology/bom_list.html"
    context_object_name = "boms"
    paginate_by = 25

    def get_queryset(self):
        queryset = BOM.objects.select_related("design", "created_by").order_by("-created_at")

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(name__icontains=search) | Q(design__code__icontains=search)
            )

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Bills of Materials"
        context["search_query"] = self.request.GET.get("q", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["status_choices"] = BOM.Status.choices
        return context


class BOMDetailView(LoginRequiredMixin, DetailView):
    """View BOM details with line items."""

    model = BOM
    template_name = "technology/bom_detail.html"
    context_object_name = "bom"

    def get_queryset(self):
        return BOM.objects.select_related("design", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"BOM {self.object.code}"
        context["lines"] = self.object.lines.select_related("inventory_item").order_by("line_number")
        context["total_cost"] = self.object.total_cost
        context["line_form"] = BOMLineForm()
        return context


class BOMCreateView(LoginRequiredMixin, CreateView):
    """Create a new BOM."""

    model = BOM
    form_class = BOMForm
    template_name = "technology/bom_form.html"
    success_url = reverse_lazy("technology:bom_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create BOM"
        context["submit_text"] = "Create BOM"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"BOM {form.instance.code} created successfully.")
        return super().form_valid(form)


class BOMUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing BOM."""

    model = BOM
    form_class = BOMForm
    template_name = "technology/bom_form.html"

    def get_success_url(self):
        return reverse_lazy("technology:bom_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit BOM {self.object.code}"
        context["submit_text"] = "Update BOM"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"BOM {self.object.code} updated successfully.")
        return super().form_valid(form)


class BOMLineCreateView(LoginRequiredMixin, View):
    """Add a line to a BOM."""

    def post(self, request, pk):
        bom = get_object_or_404(BOM, pk=pk)
        form = BOMLineForm(request.POST)
        if form.is_valid():
            line = form.save(commit=False)
            line.bom = bom
            line.save()
            messages.success(request, "Line added successfully.")
        else:
            messages.error(request, "Failed to add line.")
        return redirect("technology:bom_detail", pk=pk)


class BOMLineDeleteView(LoginRequiredMixin, View):
    """Delete a line from a BOM."""

    def post(self, request, pk, line_pk):
        line = get_object_or_404(BOMLine, pk=line_pk, bom_id=pk)
        line.delete()
        messages.success(request, "Line deleted.")
        return redirect("technology:bom_detail", pk=pk)


# =============================================================================
# CUTTER LAYOUT VIEWS
# =============================================================================


class CutterLayoutCreateView(LoginRequiredMixin, View):
    """Add a cutter layout to a design."""

    def post(self, request, design_pk):
        design = get_object_or_404(Design, pk=design_pk)
        form = DesignCutterLayoutForm(request.POST)
        if form.is_valid():
            layout = form.save(commit=False)
            layout.design = design
            layout.save()
            messages.success(request, "Cutter layout added.")
        else:
            messages.error(request, "Failed to add cutter layout.")
        return redirect("technology:design_detail", pk=design_pk)


class CutterLayoutDeleteView(LoginRequiredMixin, View):
    """Delete a cutter layout from a design."""

    def post(self, request, design_pk, layout_pk):
        layout = get_object_or_404(DesignCutterLayout, pk=layout_pk, design_id=design_pk)
        layout.delete()
        messages.success(request, "Cutter layout deleted.")
        return redirect("technology:design_detail", pk=design_pk)
