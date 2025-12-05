"""
ARDT FMS - Supply Chain Views
Version: 5.4
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView, View

from .forms import (
    CAPAForm,
    GoodsReceiptForm,
    GRNLineForm,
    POLineForm,
    PRApprovalForm,
    PRLineForm,
    PurchaseOrderForm,
    PurchaseRequisitionForm,
    SupplierForm,
)
from .models import CAPA, GoodsReceipt, GRNLine, POLine, PRLine, PurchaseOrder, PurchaseRequisition, Supplier

User = get_user_model()


# =============================================================================
# Supplier Views
# =============================================================================


class SupplierListView(LoginRequiredMixin, ListView):
    """List all suppliers."""

    model = Supplier
    template_name = "supplychain/supplier_list.html"
    context_object_name = "suppliers"

    def get_queryset(self):
        qs = Supplier.objects.annotate(po_count=Count("purchase_orders"))

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))

        active = self.request.GET.get("active")
        if active == "1":
            qs = qs.filter(is_active=True)
        elif active == "0":
            qs = qs.filter(is_active=False)

        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Suppliers"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class SupplierDetailView(LoginRequiredMixin, DetailView):
    """Supplier detail view."""

    model = Supplier
    template_name = "supplychain/supplier_detail.html"
    context_object_name = "supplier"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.code
        context["recent_pos"] = self.object.purchase_orders.order_by("-created_at")[:10]
        return context


class SupplierCreateView(LoginRequiredMixin, CreateView):
    """Create a new supplier."""

    model = Supplier
    form_class = SupplierForm
    template_name = "supplychain/supplier_form.html"
    success_url = reverse_lazy("supplychain:supplier_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Supplier"
        context["form_title"] = "Create Supplier"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Supplier created successfully.")
        return super().form_valid(form)


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    """Update a supplier."""

    model = Supplier
    form_class = SupplierForm
    template_name = "supplychain/supplier_form.html"

    def get_success_url(self):
        return reverse_lazy("supplychain:supplier_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.code}"
        context["form_title"] = f"Edit Supplier - {self.object.code}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Supplier updated successfully.")
        return super().form_valid(form)


# =============================================================================
# Purchase Requisition Views
# =============================================================================


class PRListView(LoginRequiredMixin, ListView):
    """List purchase requisitions."""

    model = PurchaseRequisition
    template_name = "supplychain/pr_list.html"
    context_object_name = "requisitions"

    def get_queryset(self):
        qs = PurchaseRequisition.objects.select_related("requested_by", "approved_by").annotate(line_count=Count("lines"))

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Purchase Requisitions"
        context["status_choices"] = PurchaseRequisition.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        return context


class PRDetailView(LoginRequiredMixin, DetailView):
    """PR detail view."""

    model = PurchaseRequisition
    template_name = "supplychain/pr_detail.html"
    context_object_name = "pr"

    def get_queryset(self):
        return PurchaseRequisition.objects.select_related("requested_by", "approved_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.pr_number
        context["lines"] = self.object.lines.select_related("inventory_item")
        return context


class PRCreateView(LoginRequiredMixin, CreateView):
    """Create a new PR."""

    model = PurchaseRequisition
    form_class = PurchaseRequisitionForm
    template_name = "supplychain/pr_form.html"

    def get_success_url(self):
        return reverse_lazy("supplychain:pr_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Purchase Requisition"
        context["form_title"] = "Create Purchase Requisition"
        return context

    def form_valid(self, form):
        # Generate PR number
        last_pr = PurchaseRequisition.objects.order_by("-id").first()
        next_num = (last_pr.id + 1) if last_pr else 1
        form.instance.pr_number = f"PR-{next_num:06d}"
        form.instance.requested_by = self.request.user

        messages.success(self.request, "Purchase Requisition created successfully.")
        return super().form_valid(form)


class PRApproveView(LoginRequiredMixin, View):
    """Approve or reject a PR."""

    def get(self, request, pk):
        pr = get_object_or_404(PurchaseRequisition, pk=pk)
        form = PRApprovalForm()
        return self.render(request, pr, form)

    def post(self, request, pk):
        pr = get_object_or_404(PurchaseRequisition, pk=pk)
        form = PRApprovalForm(request.POST)

        if form.is_valid():
            action = form.cleaned_data["action"]
            if action == "approve":
                pr.status = PurchaseRequisition.Status.APPROVED
                pr.approved_by = request.user
                messages.success(request, "PR approved successfully.")
            else:
                pr.status = PurchaseRequisition.Status.REJECTED
                messages.info(request, "PR rejected.")
            pr.save()
            return redirect("supplychain:pr_detail", pk=pr.pk)

        return self.render(request, pr, form)

    def render(self, request, pr, form):
        from django.shortcuts import render

        return render(
            request,
            "supplychain/pr_approve.html",
            {
                "pr": pr,
                "form": form,
                "page_title": f"Review {pr.pr_number}",
            },
        )


class PRAddLineView(LoginRequiredMixin, CreateView):
    """Add line to PR."""

    model = PRLine
    form_class = PRLineForm
    template_name = "supplychain/pr_line_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pr"] = get_object_or_404(PurchaseRequisition, pk=self.kwargs["pk"])
        context["page_title"] = "Add Line"
        return context

    def form_valid(self, form):
        pr = get_object_or_404(PurchaseRequisition, pk=self.kwargs["pk"])
        form.instance.pr = pr
        last_line = pr.lines.order_by("-line_number").first()
        form.instance.line_number = (last_line.line_number + 1) if last_line else 1

        messages.success(self.request, "Line added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("supplychain:pr_detail", kwargs={"pk": self.kwargs["pk"]})


# =============================================================================
# Purchase Order Views
# =============================================================================


class POListView(LoginRequiredMixin, ListView):
    """List purchase orders."""

    model = PurchaseOrder
    template_name = "supplychain/po_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        qs = PurchaseOrder.objects.select_related("supplier", "created_by").annotate(line_count=Count("lines"))

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        supplier = self.request.GET.get("supplier")
        if supplier:
            qs = qs.filter(supplier_id=supplier)

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Purchase Orders"
        context["status_choices"] = PurchaseOrder.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["suppliers"] = Supplier.objects.filter(is_active=True)
        return context


class PODetailView(LoginRequiredMixin, DetailView):
    """PO detail view."""

    model = PurchaseOrder
    template_name = "supplychain/po_detail.html"
    context_object_name = "po"

    def get_queryset(self):
        return PurchaseOrder.objects.select_related("supplier", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.po_number
        context["lines"] = self.object.lines.select_related("inventory_item")
        context["receipts"] = self.object.receipts.order_by("-created_at")
        return context


class POCreateView(LoginRequiredMixin, CreateView):
    """Create a new PO."""

    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = "supplychain/po_form.html"

    def get_success_url(self):
        return reverse_lazy("supplychain:po_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Purchase Order"
        context["form_title"] = "Create Purchase Order"
        return context

    def form_valid(self, form):
        # Generate PO number
        last_po = PurchaseOrder.objects.order_by("-id").first()
        next_num = (last_po.id + 1) if last_po else 1
        form.instance.po_number = f"PO-{next_num:06d}"
        form.instance.created_by = self.request.user

        messages.success(self.request, "Purchase Order created successfully.")
        return super().form_valid(form)


class POUpdateView(LoginRequiredMixin, UpdateView):
    """Update a PO."""

    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = "supplychain/po_form.html"

    def get_success_url(self):
        return reverse_lazy("supplychain:po_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.po_number}"
        context["form_title"] = f"Edit PO - {self.object.po_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "PO updated successfully.")
        return super().form_valid(form)


class POAddLineView(LoginRequiredMixin, CreateView):
    """Add line to PO."""

    model = POLine
    form_class = POLineForm
    template_name = "supplychain/po_line_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["po"] = get_object_or_404(PurchaseOrder, pk=self.kwargs["pk"])
        context["page_title"] = "Add Line"
        return context

    def form_valid(self, form):
        po = get_object_or_404(PurchaseOrder, pk=self.kwargs["pk"])
        form.instance.po = po
        last_line = po.lines.order_by("-line_number").first()
        form.instance.line_number = (last_line.line_number + 1) if last_line else 1

        messages.success(self.request, "Line added successfully.")
        response = super().form_valid(form)

        # Update PO total
        total = po.lines.aggregate(total=Sum(F("quantity") * F("unit_price")))["total"] or 0
        po.total_amount = total
        po.save()

        return response

    def get_success_url(self):
        return reverse_lazy("supplychain:po_detail", kwargs={"pk": self.kwargs["pk"]})


# =============================================================================
# Goods Receipt Views
# =============================================================================


class GRNListView(LoginRequiredMixin, ListView):
    """List goods receipts."""

    model = GoodsReceipt
    template_name = "supplychain/grn_list.html"
    context_object_name = "receipts"

    def get_queryset(self):
        return GoodsReceipt.objects.select_related("po__supplier", "received_by").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Goods Receipts"
        return context


class GRNDetailView(LoginRequiredMixin, DetailView):
    """GRN detail view."""

    model = GoodsReceipt
    template_name = "supplychain/grn_detail.html"
    context_object_name = "grn"

    def get_queryset(self):
        return GoodsReceipt.objects.select_related("po__supplier", "received_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.grn_number
        context["lines"] = self.object.lines.select_related("po_line__inventory_item")
        return context


class GRNCreateView(LoginRequiredMixin, CreateView):
    """Create a new GRN."""

    model = GoodsReceipt
    form_class = GoodsReceiptForm
    template_name = "supplychain/grn_form.html"

    def get_form(self):
        form = super().get_form()
        # Only show confirmed/partially received POs
        form.fields["po"].queryset = PurchaseOrder.objects.filter(
            status__in=[PurchaseOrder.Status.CONFIRMED, PurchaseOrder.Status.PARTIAL]
        )
        return form

    def get_initial(self):
        initial = super().get_initial()
        po_pk = self.request.GET.get("po")
        if po_pk:
            initial["po"] = po_pk
        initial["receipt_date"] = timezone.now().date()
        return initial

    def get_success_url(self):
        return reverse_lazy("supplychain:grn_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Goods Receipt"
        context["form_title"] = "Create Goods Receipt"
        return context

    def form_valid(self, form):
        # Generate GRN number
        last_grn = GoodsReceipt.objects.order_by("-id").first()
        next_num = (last_grn.id + 1) if last_grn else 1
        form.instance.grn_number = f"GRN-{next_num:06d}"
        form.instance.received_by = self.request.user

        messages.success(self.request, "Goods Receipt created successfully.")
        return super().form_valid(form)


class GRNAddLineView(LoginRequiredMixin, CreateView):
    """Add line to GRN."""

    model = GRNLine
    form_class = GRNLineForm
    template_name = "supplychain/grn_line_form.html"

    def get_form(self):
        form = super().get_form()
        grn = get_object_or_404(GoodsReceipt, pk=self.kwargs["pk"])
        form.fields["po_line"].queryset = grn.po.lines.all()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grn"] = get_object_or_404(GoodsReceipt, pk=self.kwargs["pk"])
        context["page_title"] = "Add Receipt Line"
        return context

    def form_valid(self, form):
        grn = get_object_or_404(GoodsReceipt, pk=self.kwargs["pk"])
        form.instance.grn = grn

        # Update PO line received quantity
        po_line = form.instance.po_line
        po_line.received_quantity += form.instance.quantity_received
        po_line.save()

        messages.success(self.request, "Receipt line added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("supplychain:grn_detail", kwargs={"pk": self.kwargs["pk"]})


# =============================================================================
# CAPA Views
# =============================================================================


class CAPAListView(LoginRequiredMixin, ListView):
    """List CAPAs."""

    model = CAPA
    template_name = "supplychain/capa_list.html"
    context_object_name = "capas"

    def get_queryset(self):
        qs = CAPA.objects.select_related("ncr", "assigned_to")

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "CAPAs"
        context["status_choices"] = CAPA.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        return context


class CAPADetailView(LoginRequiredMixin, DetailView):
    """CAPA detail view."""

    model = CAPA
    template_name = "supplychain/capa_detail.html"
    context_object_name = "capa"

    def get_queryset(self):
        return CAPA.objects.select_related("ncr", "assigned_to")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.capa_number
        return context


class CAPACreateView(LoginRequiredMixin, CreateView):
    """Create a new CAPA."""

    model = CAPA
    form_class = CAPAForm
    template_name = "supplychain/capa_form.html"

    def get_initial(self):
        initial = super().get_initial()
        ncr_pk = self.request.GET.get("ncr")
        if ncr_pk:
            initial["ncr"] = ncr_pk
        return initial

    def get_success_url(self):
        return reverse_lazy("supplychain:capa_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New CAPA"
        context["form_title"] = "Create CAPA"
        return context

    def form_valid(self, form):
        # Generate CAPA number
        last_capa = CAPA.objects.order_by("-id").first()
        next_num = (last_capa.id + 1) if last_capa else 1
        form.instance.capa_number = f"CAPA-{next_num:06d}"

        messages.success(self.request, "CAPA created successfully.")
        return super().form_valid(form)


class CAPAUpdateView(LoginRequiredMixin, UpdateView):
    """Update a CAPA."""

    model = CAPA
    form_class = CAPAForm
    template_name = "supplychain/capa_form.html"

    def get_success_url(self):
        return reverse_lazy("supplychain:capa_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.capa_number}"
        context["form_title"] = f"Edit CAPA - {self.object.capa_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "CAPA updated successfully.")
        return super().form_valid(form)
