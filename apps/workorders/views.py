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
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import DrillBitForm, WorkOrderForm
from .models import DrillBit, WorkOrder
from .utils import generate_drill_bit_qr, generate_work_order_qr


# =============================================================================
# LEGACY VIEWS - DEPRECATED
# These views have been replaced by enhanced versions in views_jobcard.py.
# URLs now redirect to the enhanced views. Kept for reference only.
# =============================================================================


class WorkOrderListView(LoginRequiredMixin, ListView):
    """
    DEPRECATED: Use WorkOrderListEnhancedView in views_jobcard.py instead.
    This class is kept for backward compatibility but the URL route now
    points to the enhanced view.
    """
    pass  # Not used - URL routes to WorkOrderListEnhancedView


class WorkOrderDetailView(LoginRequiredMixin, DetailView):
    """
    DEPRECATED: Use WorkOrderDetailEnhancedView in views_jobcard.py instead.
    This class is kept for backward compatibility but the URL route now
    points to the enhanced view.
    """
    pass  # Not used - URL routes to WorkOrderDetailEnhancedView


class WorkOrderCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new work order with account-based WO number generation.
    """
    model = WorkOrder
    template_name = "workorders/workorder_create.html"

    def get_form_class(self):
        from .forms import WorkOrderCreateEnhancedForm
        return WorkOrderCreateEnhancedForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Work Order"
        from apps.sales.models import Account
        context["accounts"] = Account.objects.filter(is_active=True).order_by('sort_order')
        return context

    def form_valid(self, form):
        account = form.cleaned_data.get('account')
        serial_number = form.cleaned_data.get('serial_number', '').strip()
        form.instance.created_by = self.request.user

        # Generate WO number from account
        if account:
            form.instance.wo_number = account.generate_wo_number()
            if not form.instance.customer and account.customer:
                form.instance.customer = account.customer
        else:
            form.instance.wo_number = self.generate_wo_number()

        # Link drill bit from serial number if not already set via hidden field
        if serial_number and not form.instance.drill_bit_id:
            bit = DrillBit.objects.filter(serial_number=serial_number).first()
            if bit:
                form.instance.drill_bit = bit

        # Sync design/bom from drill bit if not already set
        if form.instance.drill_bit:
            bit = form.instance.drill_bit
            if not form.instance.design and bit.design:
                form.instance.design = bit.design
            if not form.instance.bom:
                form.instance.bom = bit.brazing_bom or bit.system_bom

        messages.success(self.request, f"Work order {form.instance.wo_number} created successfully.")
        return super().form_valid(form)

    def generate_wo_number(self):
        """Fallback WO number generation."""
        prefix = getattr(settings, "ARDT_WO_NUMBER_PREFIX", "WO")
        padding = getattr(settings, "ARDT_WO_NUMBER_PADDING", 6)
        last_wo = WorkOrder.objects.order_by("-id").first()
        next_number = (last_wo.id + 1) if last_wo else 1
        return f"{prefix}-{str(next_number).zfill(padding)}"

    def get_success_url(self):
        return reverse_lazy("workorders:workorder_detail_enhanced", kwargs={"pk": self.object.pk})


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
        context["type_choices"] = DrillBit.BitCategory.choices
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
    from .utils import generate_drill_bit_qr
    drill_bit = get_object_or_404(
        DrillBit.objects.select_related(
            "design", "design__size", "brazing_bom", "brazing_bom__smi_type",
            "bom", "bom__smi_type", "system_bom", "system_bom__smi_type",
        ),
        pk=pk,
    )
    base_url = getattr(settings, "SITE_URL", None) or request.build_absolute_uri("/")[:-1]
    qr_code = generate_drill_bit_qr(drill_bit, base_url)

    # Active BOM for SMI display
    active_bom = drill_bit.brazing_bom or drill_bit.bom or drill_bit.system_bom
    smi_display = str(active_bom.smi_type) if active_bom and active_bom.smi_type else ""
    size_display = ""
    if drill_bit.design and drill_bit.design.size:
        size_display = drill_bit.design.size.size_display
    elif drill_bit.size:
        size_display = f'{drill_bit.size}"'

    return render(
        request, "drillbits/drillbit_qr.html", {
            "drill_bit": drill_bit,
            "page_title": f"QR Code - {drill_bit.serial_number}",
            "qr_code": qr_code,
            "smi_display": smi_display,
            "size_display": size_display,
            "active_bom": active_bom,
        }
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
            queryset = queryset.filter(repair_recommended=(recommendation.lower() == 'true'))

        return queryset.order_by('-evaluated_at')

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


@login_required
@require_GET
def api_drillbit_lookup(request):
    """
    Look up a drill bit by serial number for WO create form auto-population.
    GET /workorders/api/drill-bits/lookup/?serial=XXXXXX
    """
    serial = request.GET.get("serial", "").strip()
    if not serial:
        return JsonResponse({"found": False})

    try:
        bit = DrillBit.objects.select_related(
            "design", "design__size", "brazing_bom", "brazing_bom__smi_type",
            "system_bom", "system_bom__smi_type", "bom", "bom__smi_type",
            "bit_size_ref", "bit_location", "account", "customer",
        ).get(serial_number=serial)
    except DrillBit.DoesNotExist:
        return JsonResponse({"found": False})

    # --- size ---
    size_val = None
    size_display = ""
    if bit.bit_size_ref:
        size_val = str(bit.bit_size_ref.size_decimal) if hasattr(bit.bit_size_ref, "size_decimal") and bit.bit_size_ref.size_decimal else None
        size_display = str(bit.bit_size_ref)
    elif bit.size:
        size_val = str(bit.size)
    if not size_val and bit.design and bit.design.size:
        size_val = str(bit.design.size.size_decimal) if hasattr(bit.design.size, "size_decimal") and bit.design.size.size_decimal else None
        if not size_display:
            size_display = str(bit.design.size)

    # --- bit type ---
    bit_type = bit.bit_type or ""
    bit_type_display = bit.get_bit_type_display() if bit.bit_type else ""

    # --- hdbs_type ---
    hdbs_type = ""
    if bit.design and bit.design.hdbs_type:
        hdbs_type = bit.design.hdbs_type

    # --- smi_type (from most relevant BOM) ---
    smi_type = ""
    active_bom = bit.brazing_bom or bit.system_bom or bit.bom
    if active_bom and hasattr(active_bom, "smi_type") and active_bom.smi_type:
        smi_type = str(active_bom.smi_type)

    # --- design ---
    design_id = bit.design_id
    design_mat_no = ""
    design_level = ""
    if bit.design:
        design_mat_no = getattr(bit.design, "mat_no", "") or ""
        design_level = getattr(bit.design, "order_level", "") or ""

    # --- bom ---
    bom = active_bom
    bom_id = bom.pk if bom else None
    bom_code = ""
    bom_name = ""
    if bom:
        bom_code = getattr(bom, "code", "") or getattr(bom, "brazing_mat_no", "") or getattr(bom, "system_mat_no", "") or ""
        bom_name = str(bom)

    # --- account ---
    account_id = bit.account_id
    account_code = bit.account.code if bit.account and hasattr(bit.account, "code") else ""

    # --- customer ---
    customer_name = str(bit.customer) if bit.customer else ""

    # --- location ---
    current_location = str(bit.bit_location) if bit.bit_location else ""

    # from_location: use bit_location, fall back to last BitEvent location
    from_location = current_location
    if not from_location:
        from .models import BitEvent
        last_event = (
            BitEvent.objects.filter(bit=bit)
            .select_related("location")
            .order_by("-event_date", "-id")
            .first()
        )
        if last_event and hasattr(last_event, "location") and last_event.location:
            from_location = str(last_event.location)

    # --- dates & counts ---
    received_date = bit.received_date.isoformat() if bit.received_date else None
    repair_count = bit.repair_count
    rerun_count = getattr(bit, "rerun_count_factory", 0) + getattr(bit, "rerun_count_field", 0)
    repair_count_usa = getattr(bit, "repair_count_usa", 0)
    rerun_count_factory = getattr(bit, "rerun_count_factory", 0)
    rerun_count_field = getattr(bit, "rerun_count_field", 0)

    # --- bit state ---
    bit_state = "Unknown"
    if bit.status:
        status_map = {
            "NEW": "Component",
            "IN_STOCK": "Finished Good",
            "IN_PRODUCTION": "Component",
            "AT_RIG": "Used",
            "RETURNED": "Used",
            "SCRAPPED": "Scrapped",
        }
        bit_state = status_map.get(bit.status, bit.get_status_display() if hasattr(bit, "get_status_display") else "Unknown")

    return JsonResponse({
        "found": True,
        "drill_bit_id": bit.pk,
        "serial_number": bit.serial_number,
        "size": size_val,
        "size_display": size_display,
        "bit_type": bit_type,
        "bit_type_display": bit_type_display,
        "hdbs_type": hdbs_type,
        "smi_type": smi_type,
        "design_id": design_id,
        "design_mat_no": design_mat_no,
        "design_level": design_level,
        "bom_id": bom_id,
        "bom_code": bom_code,
        "bom_name": bom_name,
        "account_id": account_id,
        "account_code": account_code,
        "customer_name": customer_name,
        "current_location": current_location,
        "from_location": from_location,
        "received_date": received_date,
        "repair_count": repair_count,
        "rerun_count": rerun_count,
        "repair_count_usa": repair_count_usa,
        "rerun_count_factory": rerun_count_factory,
        "rerun_count_field": rerun_count_field,
        "bit_state": bit_state,
    })


@login_required
@require_GET
def api_drillbit_list(request):
    """
    List all drill bits for the serial number picker modal.
    GET /workorders/api/drill-bits/list/
    Returns JSON array of drill bits with key fields for selection.
    """
    bits = DrillBit.objects.select_related(
        "design", "design__size", "account", "brazing_bom", "system_bom", "bom", "bit_size_ref"
    ).order_by("-created_at")[:500]  # Limit to 500 most recent

    result = []
    for bit in bits:
        # Determine design level
        design_level = ""
        if bit.design:
            design_level = getattr(bit.design, "order_level", "") or ""

        # Determine HDBS type
        hdbs_type = ""
        if bit.design and bit.design.hdbs_type:
            hdbs_type = bit.design.hdbs_type

        # Determine size - get display value from BitSize model
        size = ""
        if bit.bit_size_ref:
            size = bit.bit_size_ref.size_display or bit.bit_size_ref.size_inches or str(bit.bit_size_ref.size_decimal)
        elif bit.design and bit.design.size:
            size = bit.design.size.size_display or bit.design.size.size_inches or str(bit.design.size.size_decimal)

        # Determine bit state (Component, Finished Good, Used)
        bit_state = "Unknown"
        if bit.status:
            status_map = {
                "NEW": "Component",
                "IN_STOCK": "Finished Good",
                "IN_PRODUCTION": "Component",
                "AT_RIG": "Used",
                "RETURNED": "Used",
                "SCRAPPED": "Scrapped",
            }
            bit_state = status_map.get(bit.status, bit.get_status_display() if hasattr(bit, "get_status_display") else "Unknown")

        # Rerun count (factory + field)
        rerun_count = (bit.rerun_count_factory or 0) + (bit.rerun_count_field or 0)

        result.append({
            "serial_number": bit.serial_number,
            "size": size,
            "hdbs_type": hdbs_type,
            "account_code": bit.account.code if bit.account else "",
            "bit_state": bit_state,
            "design_level": design_level,
            "repair_count": bit.repair_count or 0,
            "rerun_count": rerun_count,
        })

    return JsonResponse({"bits": result})
