"""
ARDT FMS - Supply Chain Views
Sprint 6: Supply Chain & Finance Integration
"""

import io

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMessage
from django.db.models import Count, F, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView, View

from .forms import (
    CAPAForm,
    PRApprovalForm,
    PurchaseOrderForm,
    PurchaseOrderLineForm,
    PurchaseRequisitionForm,
    PurchaseRequisitionLineForm,
    ReceiptForm,
    ReceiptLineForm,
    SupplierForm,
    VendorForm,
)
from .models import (
    CAPA,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseRequisition,
    PurchaseRequisitionLine,
    Receipt,
    ReceiptLine,
    Supplier,
    Vendor,
)

User = get_user_model()


# =============================================================================
# Supplier Views (Legacy - use Vendor for new implementations)
# =============================================================================


class SupplierListView(LoginRequiredMixin, ListView):
    """List all suppliers (legacy)."""

    model = Supplier
    template_name = "supplychain/supplier_list.html"
    context_object_name = "suppliers"

    def get_queryset(self):
        qs = Supplier.objects.all()

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))

        active = self.request.GET.get("active")
        if active == "1":
            qs = qs.filter(status="ACTIVE")
        elif active == "0":
            qs = qs.exclude(status="ACTIVE")

        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Suppliers"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class SupplierDetailView(LoginRequiredMixin, DetailView):
    """Supplier detail view (legacy)."""

    model = Supplier
    template_name = "supplychain/supplier_detail.html"
    context_object_name = "supplier"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.code
        return context


class SupplierCreateView(LoginRequiredMixin, CreateView):
    """Create a new supplier (legacy)."""

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
    """Update a supplier (legacy)."""

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
# Vendor Views (Sprint 6)
# =============================================================================


class VendorListView(LoginRequiredMixin, ListView):
    """List all vendors."""

    model = Vendor
    template_name = "supplychain/vendor_list.html"
    context_object_name = "vendors"

    def get_queryset(self):
        qs = Vendor.objects.annotate(po_count=Count("purchase_orders"))

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(vendor_id__icontains=q) | Q(company_name__icontains=q))

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        return qs.order_by("company_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Vendors"
        context["search_query"] = self.request.GET.get("q", "")
        context["status_choices"] = Vendor.Status.choices
        return context


class VendorDetailView(LoginRequiredMixin, DetailView):
    """Vendor detail view."""

    model = Vendor
    template_name = "supplychain/vendor_detail.html"
    context_object_name = "vendor"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.vendor_id
        context["contacts"] = self.object.contacts.all()
        context["recent_pos"] = self.object.purchase_orders.order_by("-created_at")[:10]
        return context


class VendorCreateView(LoginRequiredMixin, CreateView):
    """Create a new vendor."""

    model = Vendor
    form_class = VendorForm
    template_name = "supplychain/vendor_form.html"
    success_url = reverse_lazy("supplychain:vendor_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Vendor"
        context["form_title"] = "Create Vendor"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Vendor created successfully.")
        return super().form_valid(form)


class VendorUpdateView(LoginRequiredMixin, UpdateView):
    """Update a vendor."""

    model = Vendor
    form_class = VendorForm
    template_name = "supplychain/vendor_form.html"

    def get_success_url(self):
        return reverse_lazy("supplychain:vendor_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.vendor_id}"
        context["form_title"] = f"Edit Vendor - {self.object.company_name}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Vendor updated successfully.")
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
        return PurchaseRequisition.objects.select_related(
            "requested_by", "approved_by"
        ).prefetch_related("lines__inventory_item")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.requisition_number
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
        form.instance.requested_by = self.request.user
        form.instance.request_date = timezone.now().date()
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
                "page_title": f"Review {pr.requisition_number}",
            },
        )


class PRAddLineView(LoginRequiredMixin, CreateView):
    """Add line to PR."""

    model = PurchaseRequisitionLine
    form_class = PurchaseRequisitionLineForm
    template_name = "supplychain/pr_line_form.html"

    def get_context_data(self, **kwargs):
        from apps.inventory.models import InventoryCategory

        context = super().get_context_data(**kwargs)
        context["pr"] = get_object_or_404(PurchaseRequisition, pk=self.kwargs["pk"])
        context["page_title"] = "Add Line"
        context["categories"] = InventoryCategory.objects.filter(is_active=True).order_by("name")
        return context

    def form_valid(self, form):
        pr = get_object_or_404(PurchaseRequisition, pk=self.kwargs["pk"])
        form.instance.requisition = pr
        last_line = pr.lines.order_by("-line_number").first()
        form.instance.line_number = (last_line.line_number + 1) if last_line else 1

        messages.success(self.request, "Line added successfully.")
        response = super().form_valid(form)

        # Handle "Add & Add Another" button
        if "add_another" in self.request.POST:
            return redirect("supplychain:pr_add_line", pk=self.kwargs["pk"])

        return response

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
        qs = PurchaseOrder.objects.select_related("vendor", "created_by").annotate(line_count=Count("lines"))

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        vendor = self.request.GET.get("vendor")
        if vendor:
            qs = qs.filter(vendor_id=vendor)

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Purchase Orders"
        context["status_choices"] = PurchaseOrder.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["vendors"] = Vendor.objects.filter(status="ACTIVE")
        return context


class PODetailView(LoginRequiredMixin, DetailView):
    """PO detail view."""

    model = PurchaseOrder
    template_name = "supplychain/po_detail.html"
    context_object_name = "po"

    def get_queryset(self):
        return PurchaseOrder.objects.select_related("vendor", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.po_number
        context["lines"] = self.object.lines.all()
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

    model = PurchaseOrderLine
    form_class = PurchaseOrderLineForm
    template_name = "supplychain/po_line_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["po"] = get_object_or_404(PurchaseOrder, pk=self.kwargs["pk"])
        context["page_title"] = "Add Line"
        return context

    def form_valid(self, form):
        po = get_object_or_404(PurchaseOrder, pk=self.kwargs["pk"])
        form.instance.purchase_order = po
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
# Receipt Views (formerly Goods Receipt / GRN)
# =============================================================================


class ReceiptListView(LoginRequiredMixin, ListView):
    """List goods receipts."""

    model = Receipt
    template_name = "supplychain/grn_list.html"
    context_object_name = "receipts"

    def get_queryset(self):
        return Receipt.objects.select_related("purchase_order__vendor", "received_by").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Goods Receipts"
        return context


class ReceiptDetailView(LoginRequiredMixin, DetailView):
    """Receipt detail view."""

    model = Receipt
    template_name = "supplychain/grn_detail.html"
    context_object_name = "grn"

    def get_queryset(self):
        return Receipt.objects.select_related("purchase_order__vendor", "received_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.receipt_number
        context["lines"] = self.object.lines.select_related("po_line")
        return context


class ReceiptCreateView(LoginRequiredMixin, CreateView):
    """Create a new Receipt."""

    model = Receipt
    form_class = ReceiptForm
    template_name = "supplychain/grn_form.html"

    def get_form(self):
        form = super().get_form()
        # Only show confirmed/partially received POs
        form.fields["purchase_order"].queryset = PurchaseOrder.objects.filter(
            status__in=[PurchaseOrder.Status.APPROVED, PurchaseOrder.Status.PARTIALLY_RECEIVED]
        )
        return form

    def get_initial(self):
        initial = super().get_initial()
        po_pk = self.request.GET.get("po")
        if po_pk:
            initial["purchase_order"] = po_pk
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
        form.instance.received_by = self.request.user
        messages.success(self.request, "Goods Receipt created successfully.")
        return super().form_valid(form)


class ReceiptAddLineView(LoginRequiredMixin, CreateView):
    """Add line to Receipt."""

    model = ReceiptLine
    form_class = ReceiptLineForm
    template_name = "supplychain/grn_line_form.html"

    def get_form(self):
        form = super().get_form()
        receipt = get_object_or_404(Receipt, pk=self.kwargs["pk"])
        form.fields["po_line"].queryset = receipt.purchase_order.lines.all()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grn"] = get_object_or_404(Receipt, pk=self.kwargs["pk"])
        context["page_title"] = "Add Receipt Line"
        return context

    def form_valid(self, form):
        receipt = get_object_or_404(Receipt, pk=self.kwargs["pk"])
        form.instance.receipt = receipt

        # Update PO line received quantity
        po_line = form.instance.po_line
        po_line.quantity_received += form.instance.quantity_received
        po_line.save()

        messages.success(self.request, "Receipt line added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("supplychain:grn_detail", kwargs={"pk": self.kwargs["pk"]})


# Legacy view aliases for backward compatibility
GRNListView = ReceiptListView
GRNDetailView = ReceiptDetailView
GRNCreateView = ReceiptCreateView
GRNAddLineView = ReceiptAddLineView


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


# =============================================================================
# PO PDF and Email Views
# =============================================================================


class POPDFView(LoginRequiredMixin, View):
    """Generate PDF for a Purchase Order."""

    def get(self, request, pk):
        from xhtml2pdf import pisa

        po = get_object_or_404(
            PurchaseOrder.objects.select_related("vendor", "created_by"),
            pk=pk
        )
        lines = po.lines.all()

        # Render HTML template
        html_content = render_to_string("supplychain/po_pdf.html", {
            "po": po,
            "lines": lines,
            "company_name": getattr(django_settings, "COMPANY_NAME", "ARDT FMS"),
        })

        # Create PDF
        buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=buffer)

        if pisa_status.err:
            return HttpResponse("Error generating PDF", status=500)

        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{po.po_number}.pdf"'
        return response


class POEmailView(LoginRequiredMixin, View):
    """Email PO to vendor."""

    def get(self, request, pk):
        """Show confirmation page."""
        from django.shortcuts import render

        po = get_object_or_404(
            PurchaseOrder.objects.select_related("vendor"),
            pk=pk
        )

        if not po.vendor.primary_email:
            messages.error(request, "Vendor does not have an email address configured.")
            return redirect("supplychain:po_detail", pk=pk)

        return render(request, "supplychain/po_email_confirm.html", {
            "po": po,
            "page_title": f"Email {po.po_number}",
        })

    def post(self, request, pk):
        """Send the email with PDF attachment."""
        from xhtml2pdf import pisa

        po = get_object_or_404(
            PurchaseOrder.objects.select_related("vendor", "created_by"),
            pk=pk
        )
        lines = po.lines.all()

        if not po.vendor.primary_email:
            messages.error(request, "Vendor does not have an email address.")
            return redirect("supplychain:po_detail", pk=pk)

        # Generate PDF
        html_content = render_to_string("supplychain/po_pdf.html", {
            "po": po,
            "lines": lines,
            "company_name": getattr(django_settings, "COMPANY_NAME", "ARDT FMS"),
        })

        buffer = io.BytesIO()
        pisa.CreatePDF(html_content, dest=buffer)
        buffer.seek(0)
        pdf_content = buffer.read()

        # Compose email
        subject = f"Purchase Order {po.po_number}"
        body = render_to_string("supplychain/po_email_body.html", {
            "po": po,
            "sender_name": request.user.get_full_name() or request.user.username,
        })

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            to=[po.vendor.primary_email],
        )
        email.attach(f"{po.po_number}.pdf", pdf_content, "application/pdf")

        try:
            email.send()
            # Update PO status to SENT if it's still in DRAFT
            if po.status == PurchaseOrder.Status.DRAFT:
                po.status = PurchaseOrder.Status.SENT
                po.save()
            messages.success(request, f"Purchase Order sent to {po.vendor.primary_email}")
        except Exception as e:
            messages.error(request, f"Failed to send email: {str(e)}")

        return redirect("supplychain:po_detail", pk=pk)
