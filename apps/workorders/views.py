"""
ARDT FMS - Work Orders Views
Version: 5.4 - Sprint 1.5

Work order management views with optimized queries and exports.
"""

import csv
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import DrillBitForm, WorkOrderForm
from .models import DrillBit, WorkOrder
from .utils import generate_drill_bit_qr, generate_work_order_qr


class WorkOrderListView(LoginRequiredMixin, ListView):
    """
    List all work orders with filtering and pagination.
    """

    model = WorkOrder
    template_name = "workorders/workorder_list.html"
    context_object_name = "work_orders"
    paginate_by = 25

    def get_queryset(self):
        queryset = WorkOrder.objects.select_related("customer", "drill_bit", "assigned_to", "design").order_by("-created_at")

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filter by priority
        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(wo_number__icontains=search)
                | Q(customer__name__icontains=search)
                | Q(drill_bit__serial_number__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Work Orders"
        context["status_choices"] = WorkOrder.Status.choices
        context["priority_choices"] = WorkOrder.Priority.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["current_priority"] = self.request.GET.get("priority", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class WorkOrderDetailView(LoginRequiredMixin, DetailView):
    """
    View work order details.
    """

    model = WorkOrder
    template_name = "workorders/workorder_detail.html"
    context_object_name = "work_order"

    def get_queryset(self):
        return WorkOrder.objects.select_related(
            "customer",
            "drill_bit",
            "assigned_to",
            "design",
            "sales_order",
            "rig",
            "well",
            "procedure",
            "department",
            "created_by",
        ).prefetch_related("documents", "photos", "materials", "time_logs")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Work Order {self.object.wo_number}"
        # Generate QR code for the work order
        base_url = getattr(settings, "SITE_URL", None)
        context["qr_code"] = generate_work_order_qr(self.object, base_url)
        return context


class WorkOrderCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new work order.
    """

    model = WorkOrder
    form_class = WorkOrderForm
    template_name = "workorders/workorder_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Work Order"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.wo_number = self.generate_wo_number()
        messages.success(self.request, f"Work order {form.instance.wo_number} created successfully.")
        return super().form_valid(form)

    def generate_wo_number(self):
        """Generate unique work order number."""
        prefix = getattr(settings, "ARDT_WO_NUMBER_PREFIX", "WO")
        padding = getattr(settings, "ARDT_WO_NUMBER_PADDING", 6)

        last_wo = WorkOrder.objects.order_by("-id").first()
        next_number = (last_wo.id + 1) if last_wo else 1

        return f"{prefix}-{str(next_number).zfill(padding)}"

    def get_success_url(self):
        return reverse_lazy("workorders:detail", kwargs={"pk": self.object.pk})


class WorkOrderUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing work order.
    """

    model = WorkOrder
    form_class = WorkOrderForm
    template_name = "workorders/workorder_form.html"

    def get_form(self, form_class=None):
        """Add status field for updates."""
        form = super().get_form(form_class)
        # Add status field for updates (not in create form)
        from django import forms as django_forms

        form.fields["status"] = django_forms.ChoiceField(
            choices=WorkOrder.Status.choices,
            widget=django_forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Work Order {self.object.wo_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Work order {form.instance.wo_number} updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("workorders:detail", kwargs={"pk": self.object.pk})


@login_required
def start_work_view(request, pk):
    """
    Start working on a work order.
    """
    work_order = get_object_or_404(WorkOrder, pk=pk)

    if request.method == "POST":
        if work_order.status in ["RELEASED", "PLANNED"]:
            work_order.status = "IN_PROGRESS"
            work_order.actual_start = timezone.now()
            work_order.save()
            messages.success(request, f"Started working on {work_order.wo_number}.")
        else:
            messages.error(request, f"Cannot start work order with status {work_order.get_status_display()}.")

    return redirect("workorders:detail", pk=pk)


@login_required
def complete_work_view(request, pk):
    """
    Complete a work order (send to QC).
    """
    work_order = get_object_or_404(WorkOrder, pk=pk)

    if request.method == "POST":
        if work_order.status == "IN_PROGRESS":
            work_order.status = "QC_PENDING"
            work_order.save()
            messages.success(request, f"{work_order.wo_number} sent to QC for inspection.")
        else:
            messages.error(request, f"Cannot complete work order with status {work_order.get_status_display()}.")

    return redirect("workorders:detail", pk=pk)


# =============================================================================
# DRILL BIT VIEWS
# =============================================================================


class DrillBitListView(LoginRequiredMixin, ListView):
    """
    List all drill bits with filtering and pagination.
    """

    model = DrillBit
    template_name = "drillbits/drillbit_list.html"
    context_object_name = "drill_bits"
    paginate_by = 25

    def get_queryset(self):
        queryset = DrillBit.objects.select_related("design", "customer", "current_location", "created_by").order_by(
            "-created_at"
        )

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filter by type
        bit_type = self.request.GET.get("type")
        if bit_type:
            queryset = queryset.filter(bit_type=bit_type)

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(serial_number__icontains=search) | Q(iadc_code__icontains=search) | Q(customer__name__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Drill Bits"
        context["status_choices"] = DrillBit.Status.choices
        context["type_choices"] = DrillBit.BitType.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["current_type"] = self.request.GET.get("type", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class DrillBitDetailView(LoginRequiredMixin, DetailView):
    """
    View drill bit details with QR code.
    """

    model = DrillBit
    template_name = "drillbits/drillbit_detail.html"
    context_object_name = "drill_bit"

    def get_queryset(self):
        return DrillBit.objects.select_related(
            "design", "customer", "current_location", "rig", "well", "created_by"
        ).prefetch_related("work_orders", "evaluations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Drill Bit {self.object.serial_number}"
        # Get recent work orders for this drill bit
        context["recent_work_orders"] = self.object.work_orders.order_by("-created_at")[:5]
        # Generate QR code for the drill bit
        base_url = getattr(settings, "SITE_URL", None)
        context["qr_code"] = generate_drill_bit_qr(self.object, base_url)
        return context


class DrillBitCreateView(LoginRequiredMixin, CreateView):
    """
    Register a new drill bit.
    """

    model = DrillBit
    form_class = DrillBitForm
    template_name = "drillbits/drillbit_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Register Drill Bit"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Drill bit {form.instance.serial_number} registered successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("workorders:drillbit_detail", kwargs={"pk": self.object.pk})


class DrillBitUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update drill bit information.
    """

    model = DrillBit
    form_class = DrillBitForm
    template_name = "drillbits/drillbit_form.html"

    def get_form(self, form_class=None):
        """Make serial_number read-only for updates."""
        form = super().get_form(form_class)
        form.fields["serial_number"].widget.attrs["readonly"] = True
        form.fields["serial_number"].help_text = "Serial number cannot be changed after creation"
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Drill Bit {self.object.serial_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Drill bit {form.instance.serial_number} updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("workorders:drillbit_detail", kwargs={"pk": self.object.pk})


@login_required
def drillbit_qr_view(request, pk):
    """
    Display QR code for a drill bit.
    """
    drill_bit = get_object_or_404(DrillBit, pk=pk)
    return render(
        request, "drillbits/drillbit_qr.html", {"drill_bit": drill_bit, "page_title": f"QR Code - {drill_bit.serial_number}"}
    )


# =============================================================================
# HTMX VIEWS
# =============================================================================


@login_required
def update_status_htmx(request, pk):
    """
    HTMX endpoint for updating work order status.
    Returns partial HTML for the status badge.
    """
    work_order = get_object_or_404(WorkOrder, pk=pk)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status and new_status in dict(WorkOrder.Status.choices):
            old_status = work_order.status
            work_order.status = new_status

            # Update timestamps based on status change
            if new_status == "IN_PROGRESS" and old_status in ["PLANNED", "RELEASED"]:
                work_order.actual_start = timezone.now()
            elif new_status == "COMPLETED":
                work_order.actual_end = timezone.now()
                work_order.progress_percent = 100

            work_order.save()

            # Return the partial template for HTMX swap
            return render(
                request,
                "partials/status_badge.html",
                {
                    "object_id": work_order.pk,
                    "status": work_order.status,
                    "status_display": work_order.get_status_display(),
                },
            )

    # GET request - return current status badge
    return render(
        request,
        "partials/status_badge.html",
        {
            "object_id": work_order.pk,
            "status": work_order.status,
            "status_display": work_order.get_status_display(),
        },
    )


@login_required
def workorder_row_htmx(request, pk):
    """
    HTMX endpoint for returning a single work order row.
    Used for refreshing a row after updates.
    """
    work_order = get_object_or_404(WorkOrder.objects.select_related("customer", "drill_bit", "assigned_to"), pk=pk)
    return render(
        request,
        "partials/workorder_row.html",
        {
            "work_order": work_order,
        },
    )


# =============================================================================
# EXPORT VIEWS
# =============================================================================


@login_required
def export_work_orders_csv(request):
    """
    Export work orders to CSV file.
    Preserves any active filters from the list view.
    """
    response = HttpResponse(content_type="text/csv")
    filename = f'workorders_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "WO Number",
            "Type",
            "Customer",
            "Drill Bit",
            "Status",
            "Priority",
            "Due Date",
            "Assigned To",
            "Progress %",
            "Created At",
        ]
    )

    # Build queryset with same filters as list view
    queryset = WorkOrder.objects.select_related("customer", "drill_bit", "assigned_to").order_by("-created_at")

    # Apply filters from request
    status = request.GET.get("status")
    if status:
        queryset = queryset.filter(status=status)

    priority = request.GET.get("priority")
    if priority:
        queryset = queryset.filter(priority=priority)

    search = request.GET.get("q")
    if search:
        queryset = queryset.filter(Q(wo_number__icontains=search) | Q(customer__name__icontains=search))

    for wo in queryset:
        writer.writerow(
            [
                wo.wo_number,
                wo.get_wo_type_display(),
                wo.customer.name if wo.customer else "",
                wo.drill_bit.serial_number if wo.drill_bit else "",
                wo.get_status_display(),
                wo.get_priority_display(),
                wo.due_date.strftime("%Y-%m-%d") if wo.due_date else "",
                wo.assigned_to.get_full_name() if wo.assigned_to else "",
                wo.progress_percent,
                wo.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )

    return response


@login_required
def export_drill_bits_csv(request):
    """
    Export drill bits to CSV file.
    Preserves any active filters from the list view.
    """
    response = HttpResponse(content_type="text/csv")
    filename = f'drillbits_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "Serial Number",
            "Type",
            "Size",
            "IADC Code",
            "Status",
            "Customer",
            "Location",
            "Total Hours",
            "Total Footage",
            "Run Count",
        ]
    )

    # Build queryset with same filters as list view
    queryset = DrillBit.objects.select_related("customer", "current_location").order_by("-created_at")

    # Apply filters from request
    status = request.GET.get("status")
    if status:
        queryset = queryset.filter(status=status)

    bit_type = request.GET.get("type")
    if bit_type:
        queryset = queryset.filter(bit_type=bit_type)

    search = request.GET.get("q")
    if search:
        queryset = queryset.filter(Q(serial_number__icontains=search) | Q(iadc_code__icontains=search))

    for bit in queryset:
        writer.writerow(
            [
                bit.serial_number,
                bit.get_bit_type_display(),
                str(bit.size),
                bit.iadc_code,
                bit.get_status_display(),
                bit.customer.name if bit.customer else "",
                bit.current_location.name if bit.current_location else "",
                str(bit.total_hours),
                bit.total_footage,
                bit.run_count,
            ]
        )

    return response


# =============================================================================
# SPRINT 4 VIEWS - Additional Models
# =============================================================================

from .forms import (
    SalvageItemForm, RepairApprovalAuthorityForm, RepairEvaluationForm,
    RepairBOMForm, ProcessRouteForm, WorkOrderCostForm
)
from .models import (
    SalvageItem, RepairApprovalAuthority, RepairEvaluation,
    RepairBOM, ProcessRoute, WorkOrderCost,
    StatusTransitionLog, BitRepairHistory, OperationExecution
)


# ============================================================================
# SalvageItem Views (5 views)
# ============================================================================

class SalvageItemListView(LoginRequiredMixin, ListView):
    """List all salvage items"""
    model = SalvageItem
    template_name = "workorders/salvageitem_list.html"
    context_object_name = "items"
    paginate_by = 25

    def get_queryset(self):
        queryset = SalvageItem.objects.select_related('work_order', 'drill_bit', 'disposed_by')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(salvage_number__icontains=search) |
                Q(description__icontains=search)
            )

        salvage_type = self.request.GET.get('salvage_type')
        if salvage_type:
            queryset = queryset.filter(salvage_type=salvage_type)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-salvaged_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Salvage Items'
        return context


class SalvageItemDetailView(LoginRequiredMixin, DetailView):
    """View salvage item details"""
    model = SalvageItem
    template_name = "workorders/salvageitem_detail.html"
    context_object_name = "item"


class SalvageItemCreateView(LoginRequiredMixin, CreateView):
    """Create new salvage item"""
    model = SalvageItem
    form_class = SalvageItemForm
    template_name = "workorders/salvageitem_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Salvage item '{form.instance.salvage_number}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:salvageitem_detail', kwargs={'pk': self.object.pk})


class SalvageItemUpdateView(LoginRequiredMixin, UpdateView):
    """Update salvage item"""
    model = SalvageItem
    form_class = SalvageItemForm
    template_name = "workorders/salvageitem_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Salvage item '{form.instance.salvage_number}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:salvageitem_detail', kwargs={'pk': self.object.pk})


class SalvageItemDeleteView(LoginRequiredMixin, DeleteView):
    """Delete salvage item"""
    model = SalvageItem
    template_name = "workorders/salvageitem_confirm_delete.html"
    success_url = reverse_lazy('workorders:salvageitem_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(request, f"Salvage item '{self.object.salvage_number}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# RepairApprovalAuthority Views (5 views)
# ============================================================================

class RepairApprovalAuthorityListView(LoginRequiredMixin, ListView):
    """List repair approval authorities"""
    model = RepairApprovalAuthority
    template_name = "workorders/repairapprovalauthority_list.html"
    context_object_name = "authorities"
    paginate_by = 25

    def get_queryset(self):
        queryset = RepairApprovalAuthority.objects.all()

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(name__icontains=search)

        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=(is_active == 'true'))

        return queryset.order_by('min_amount')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Repair Approval Authorities'
        return context


class RepairApprovalAuthorityDetailView(LoginRequiredMixin, DetailView):
    """View authority details"""
    model = RepairApprovalAuthority
    template_name = "workorders/repairapprovalauthority_detail.html"
    context_object_name = "authority"


class RepairApprovalAuthorityCreateView(LoginRequiredMixin, CreateView):
    """Create approval authority"""
    model = RepairApprovalAuthority
    form_class = RepairApprovalAuthorityForm
    template_name = "workorders/repairapprovalauthority_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Approval authority '{form.instance.name}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:repairapprovalauthority_detail', kwargs={'pk': self.object.pk})


class RepairApprovalAuthorityUpdateView(LoginRequiredMixin, UpdateView):
    """Update approval authority"""
    model = RepairApprovalAuthority
    form_class = RepairApprovalAuthorityForm
    template_name = "workorders/repairapprovalauthority_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Approval authority '{form.instance.name}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:repairapprovalauthority_detail', kwargs={'pk': self.object.pk})


class RepairApprovalAuthorityDeleteView(LoginRequiredMixin, DeleteView):
    """Delete approval authority"""
    model = RepairApprovalAuthority
    template_name = "workorders/repairapprovalauthority_confirm_delete.html"
    success_url = reverse_lazy('workorders:repairapprovalauthority_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(request, f"Approval authority '{self.object.name}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# RepairEvaluation Views (5 views)
# ============================================================================

class RepairEvaluationListView(LoginRequiredMixin, ListView):
    """List repair evaluations"""
    model = RepairEvaluation
    template_name = "workorders/repairevaluation_list.html"
    context_object_name = "evaluations"
    paginate_by = 25

    def get_queryset(self):
        queryset = RepairEvaluation.objects.select_related('drill_bit', 'evaluated_by', 'approved_by')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(evaluation_number__icontains=search) |
                Q(drill_bit__serial_number__icontains=search)
            )

        recommendation = self.request.GET.get('recommendation')
        if recommendation:
            queryset = queryset.filter(recommendation=recommendation)

        return queryset.order_by('-evaluation_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Repair Evaluations'
        return context


class RepairEvaluationDetailView(LoginRequiredMixin, DetailView):
    """View evaluation details"""
    model = RepairEvaluation
    template_name = "workorders/repairevaluation_detail.html"
    context_object_name = "evaluation"


class RepairEvaluationCreateView(LoginRequiredMixin, CreateView):
    """Create repair evaluation"""
    model = RepairEvaluation
    form_class = RepairEvaluationForm
    template_name = "workorders/repairevaluation_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Repair evaluation '{form.instance.evaluation_number}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:repairevaluation_detail', kwargs={'pk': self.object.pk})


class RepairEvaluationUpdateView(LoginRequiredMixin, UpdateView):
    """Update evaluation"""
    model = RepairEvaluation
    form_class = RepairEvaluationForm
    template_name = "workorders/repairevaluation_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Repair evaluation '{form.instance.evaluation_number}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:repairevaluation_detail', kwargs={'pk': self.object.pk})


class RepairEvaluationDeleteView(LoginRequiredMixin, DeleteView):
    """Delete evaluation"""
    model = RepairEvaluation
    template_name = "workorders/repairevaluation_confirm_delete.html"
    success_url = reverse_lazy('workorders:repairevaluation_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(request, f"Repair evaluation '{self.object.evaluation_number}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# RepairBOM Views (5 views)
# ============================================================================

class RepairBOMListView(LoginRequiredMixin, ListView):
    """List repair BOMs"""
    model = RepairBOM
    template_name = "workorders/repairbom_list.html"
    context_object_name = "boms"
    paginate_by = 25

    def get_queryset(self):
        queryset = RepairBOM.objects.select_related('drill_bit', 'repair_evaluation', 'prepared_by')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(drill_bit__serial_number__icontains=search)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-prepared_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Repair BOMs'
        return context


class RepairBOMDetailView(LoginRequiredMixin, DetailView):
    """View BOM details with lines"""
    model = RepairBOM
    template_name = "workorders/repairbom_detail.html"
    context_object_name = "bom"

    def get_queryset(self):
        return RepairBOM.objects.select_related('drill_bit', 'repair_evaluation', 'prepared_by').prefetch_related('lines__inventory_item')


class RepairBOMCreateView(LoginRequiredMixin, CreateView):
    """Create repair BOM"""
    model = RepairBOM
    form_class = RepairBOMForm
    template_name = "workorders/repairbom_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Repair BOM created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:repairbom_detail', kwargs={'pk': self.object.pk})


class RepairBOMUpdateView(LoginRequiredMixin, UpdateView):
    """Update repair BOM"""
    model = RepairBOM
    form_class = RepairBOMForm
    template_name = "workorders/repairbom_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Repair BOM updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:repairbom_detail', kwargs={'pk': self.object.pk})


class RepairBOMDeleteView(LoginRequiredMixin, DeleteView):
    """Delete repair BOM"""
    model = RepairBOM
    template_name = "workorders/repairbom_confirm_delete.html"
    success_url = reverse_lazy('workorders:repairbom_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Repair BOM deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# ProcessRoute Views (5 views)
# ============================================================================

class ProcessRouteListView(LoginRequiredMixin, ListView):
    """List process routes"""
    model = ProcessRoute
    template_name = "workorders/processroute_list.html"
    context_object_name = "routes"
    paginate_by = 25

    def get_queryset(self):
        queryset = ProcessRoute.objects.all()

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(route_number__icontains=search) |
                Q(name__icontains=search)
            )

        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=(is_active == 'true'))

        return queryset.order_by('route_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Process Routes'
        return context


class ProcessRouteDetailView(LoginRequiredMixin, DetailView):
    """View route details with operations"""
    model = ProcessRoute
    template_name = "workorders/processroute_detail.html"
    context_object_name = "route"

    def get_queryset(self):
        return ProcessRoute.objects.prefetch_related('operations')


class ProcessRouteCreateView(LoginRequiredMixin, CreateView):
    """Create process route"""
    model = ProcessRoute
    form_class = ProcessRouteForm
    template_name = "workorders/processroute_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Process route '{form.instance.route_number}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:processroute_detail', kwargs={'pk': self.object.pk})


class ProcessRouteUpdateView(LoginRequiredMixin, UpdateView):
    """Update process route"""
    model = ProcessRoute
    form_class = ProcessRouteForm
    template_name = "workorders/processroute_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Process route '{form.instance.route_number}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:processroute_detail', kwargs={'pk': self.object.pk})


class ProcessRouteDeleteView(LoginRequiredMixin, DeleteView):
    """Delete process route"""
    model = ProcessRoute
    template_name = "workorders/processroute_confirm_delete.html"
    success_url = reverse_lazy('workorders:processroute_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(request, f"Process route '{self.object.route_number}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# WorkOrderCost Views (5 views)
# ============================================================================

class WorkOrderCostListView(LoginRequiredMixin, ListView):
    """List work order costs"""
    model = WorkOrderCost
    template_name = "workorders/workordercost_list.html"
    context_object_name = "costs"
    paginate_by = 25

    def get_queryset(self):
        queryset = WorkOrderCost.objects.select_related('work_order')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(work_order__wo_number__icontains=search)

        return queryset.order_by('-work_order__created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Work Order Costs'
        return context


class WorkOrderCostDetailView(LoginRequiredMixin, DetailView):
    """View cost details"""
    model = WorkOrderCost
    template_name = "workorders/workordercost_detail.html"
    context_object_name = "cost"


class WorkOrderCostCreateView(LoginRequiredMixin, CreateView):
    """Create work order cost"""
    model = WorkOrderCost
    form_class = WorkOrderCostForm
    template_name = "workorders/workordercost_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Work order cost record created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:workordercost_detail', kwargs={'pk': self.object.pk})


class WorkOrderCostUpdateView(LoginRequiredMixin, UpdateView):
    """Update work order cost"""
    model = WorkOrderCost
    form_class = WorkOrderCostForm
    template_name = "workorders/workordercost_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Work order cost record updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:workordercost_detail', kwargs={'pk': self.object.pk})


class WorkOrderCostDeleteView(LoginRequiredMixin, DeleteView):
    """Delete work order cost"""
    model = WorkOrderCost
    template_name = "workorders/workordercost_confirm_delete.html"
    success_url = reverse_lazy('workorders:workordercost_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Work order cost record deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# StatusTransitionLog Views (VIEW-ONLY - 1 view)
# ============================================================================

class StatusTransitionLogListView(LoginRequiredMixin, ListView):
    """List status transition logs (view-only)"""
    model = StatusTransitionLog
    template_name = "workorders/statustransitionlog_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        queryset = StatusTransitionLog.objects.select_related('changed_by')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(from_status__icontains=search) |
                Q(to_status__icontains=search) |
                Q(reason__icontains=search)
            )

        return queryset.order_by('-changed_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Status Transition Logs'
        return context


# ============================================================================
# BitRepairHistory Views (VIEW-ONLY - 1 view)
# ============================================================================

class BitRepairHistoryListView(LoginRequiredMixin, ListView):
    """List bit repair history (view-only)"""
    model = BitRepairHistory
    template_name = "workorders/bitrepairhistory_list.html"
    context_object_name = "repairs"
    paginate_by = 25

    def get_queryset(self):
        queryset = BitRepairHistory.objects.select_related('drill_bit', 'quality_inspector')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(drill_bit__serial_number__icontains=search) |
                Q(work_performed__icontains=search)
            )

        repair_type = self.request.GET.get('repair_type')
        if repair_type:
            queryset = queryset.filter(repair_type=repair_type)

        return queryset.order_by('-repair_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Bit Repair History'
        return context


# ============================================================================
# OperationExecution Views (VIEW-ONLY - 1 view)
# ============================================================================

class OperationExecutionListView(LoginRequiredMixin, ListView):
    """List operation executions (view-only)"""
    model = OperationExecution
    template_name = "workorders/operationexecution_list.html"
    context_object_name = "executions"
    paginate_by = 25

    def get_queryset(self):
        queryset = OperationExecution.objects.select_related(
            'work_order', 'process_route_operation', 'operator'
        )

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(work_order__wo_number__icontains=search)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Operation Executions'
        return context
