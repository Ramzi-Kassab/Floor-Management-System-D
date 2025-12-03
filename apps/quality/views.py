"""
ARDT FMS - Quality Views
Version: 5.4 - Sprint 3

Views for Inspection and NCR management.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from apps.accounts.mixins import RoleRequiredMixin

from .forms import InspectionForm, InspectionResultForm, NCRDispositionForm, NCRForm, NCRPhotoForm
from .models import NCR, Inspection, NCRPhoto


# =============================================================================
# INSPECTION VIEWS
# =============================================================================


class InspectionListView(LoginRequiredMixin, ListView):
    """List all inspections with filtering."""

    model = Inspection
    template_name = "quality/inspection_list.html"
    context_object_name = "inspections"
    paginate_by = 25

    def get_queryset(self):
        queryset = Inspection.objects.select_related(
            "work_order", "drill_bit", "inspected_by", "created_by"
        ).order_by("-scheduled_date", "-created_at")

        # Search filter
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(inspection_number__icontains=search)
                | Q(work_order__wo_number__icontains=search)
                | Q(findings__icontains=search)
            )

        # Type filter
        inspection_type = self.request.GET.get("type")
        if inspection_type:
            queryset = queryset.filter(inspection_type=inspection_type)

        # Status filter
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Inspections"
        context["search_query"] = self.request.GET.get("q", "")
        context["current_type"] = self.request.GET.get("type", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["type_choices"] = Inspection.InspectionType.choices
        context["status_choices"] = Inspection.Status.choices
        return context


class InspectionDetailView(LoginRequiredMixin, DetailView):
    """View inspection details."""

    model = Inspection
    template_name = "quality/inspection_detail.html"
    context_object_name = "inspection"

    def get_queryset(self):
        return Inspection.objects.select_related(
            "work_order", "drill_bit", "procedure", "inspected_by", "approved_by", "created_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Inspection {self.object.inspection_number}"
        context["ncrs"] = self.object.ncrs.select_related("detected_by").order_by("-detected_at")
        return context


class InspectionCreateView(LoginRequiredMixin, CreateView):
    """Create a new inspection."""

    model = Inspection
    form_class = InspectionForm
    template_name = "quality/inspection_form.html"
    success_url = reverse_lazy("quality:inspection_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Inspection"
        context["submit_text"] = "Create Inspection"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.inspection_number = self.generate_inspection_number()
        messages.success(self.request, f"Inspection {form.instance.inspection_number} created successfully.")
        return super().form_valid(form)

    def generate_inspection_number(self):
        """Generate unique inspection number."""
        prefix = "INS"
        year = timezone.now().year
        last_inspection = Inspection.objects.filter(
            inspection_number__startswith=f"{prefix}-{year}-"
        ).order_by("-id").first()

        if last_inspection:
            try:
                last_num = int(last_inspection.inspection_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}-{year}-{str(next_num).zfill(4)}"


class InspectionUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing inspection."""

    model = Inspection
    form_class = InspectionForm
    template_name = "quality/inspection_form.html"

    def get_success_url(self):
        return reverse_lazy("quality:inspection_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Inspection {self.object.inspection_number}"
        context["submit_text"] = "Update Inspection"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Inspection {self.object.inspection_number} updated successfully.")
        return super().form_valid(form)


class InspectionCompleteView(LoginRequiredMixin, UpdateView):
    """Complete an inspection with results."""

    model = Inspection
    form_class = InspectionResultForm
    template_name = "quality/inspection_complete.html"

    def get_success_url(self):
        return reverse_lazy("quality:inspection_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Complete Inspection {self.object.inspection_number}"
        context["submit_text"] = "Record Results"
        return context

    def form_valid(self, form):
        form.instance.inspected_by = self.request.user
        form.instance.inspected_at = timezone.now()
        messages.success(self.request, f"Inspection {self.object.inspection_number} completed.")
        return super().form_valid(form)


# =============================================================================
# NCR VIEWS
# =============================================================================


class NCRListView(LoginRequiredMixin, ListView):
    """List all NCRs with filtering."""

    model = NCR
    template_name = "quality/ncr_list.html"
    context_object_name = "ncrs"
    paginate_by = 25

    def get_queryset(self):
        queryset = NCR.objects.select_related(
            "work_order", "inspection", "drill_bit", "detected_by", "disposition_by"
        ).order_by("-detected_at")

        # Search filter
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(ncr_number__icontains=search)
                | Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(work_order__wo_number__icontains=search)
            )

        # Severity filter
        severity = self.request.GET.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        # Status filter
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Non-Conformance Reports"
        context["search_query"] = self.request.GET.get("q", "")
        context["current_severity"] = self.request.GET.get("severity", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["severity_choices"] = NCR.Severity.choices
        context["status_choices"] = NCR.Status.choices
        return context


class NCRDetailView(LoginRequiredMixin, DetailView):
    """View NCR details."""

    model = NCR
    template_name = "quality/ncr_detail.html"
    context_object_name = "ncr"

    def get_queryset(self):
        return NCR.objects.select_related(
            "work_order",
            "inspection",
            "drill_bit",
            "detected_by",
            "investigated_by",
            "disposition_by",
            "closed_by",
            "created_by",
            "rework_work_order",
        ).prefetch_related("photos")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"NCR {self.object.ncr_number}"
        context["photos"] = self.object.photos.all()
        context["photo_form"] = NCRPhotoForm()
        return context


class NCRCreateView(LoginRequiredMixin, CreateView):
    """Create a new NCR."""

    model = NCR
    form_class = NCRForm
    template_name = "quality/ncr_form.html"
    success_url = reverse_lazy("quality:ncr_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create NCR"
        context["submit_text"] = "Create NCR"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.detected_by = self.request.user
        form.instance.detected_at = timezone.now()
        form.instance.ncr_number = self.generate_ncr_number()
        form.instance.status = NCR.Status.OPEN
        messages.success(self.request, f"NCR {form.instance.ncr_number} created successfully.")
        return super().form_valid(form)

    def generate_ncr_number(self):
        """Generate unique NCR number."""
        prefix = "NCR"
        year = timezone.now().year
        last_ncr = NCR.objects.filter(
            ncr_number__startswith=f"{prefix}-{year}-"
        ).order_by("-id").first()

        if last_ncr:
            try:
                last_num = int(last_ncr.ncr_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}-{year}-{str(next_num).zfill(4)}"


class NCRUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing NCR."""

    model = NCR
    form_class = NCRForm
    template_name = "quality/ncr_form.html"

    def get_success_url(self):
        return reverse_lazy("quality:ncr_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit NCR {self.object.ncr_number}"
        context["submit_text"] = "Update NCR"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"NCR {self.object.ncr_number} updated successfully.")
        return super().form_valid(form)


class NCRDispositionView(LoginRequiredMixin, UpdateView):
    """Update NCR disposition and close."""

    model = NCR
    form_class = NCRDispositionForm
    template_name = "quality/ncr_disposition.html"

    def get_success_url(self):
        return reverse_lazy("quality:ncr_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Disposition NCR {self.object.ncr_number}"
        context["submit_text"] = "Update Disposition"
        return context

    def form_valid(self, form):
        if form.instance.status == NCR.Status.CLOSED:
            form.instance.closed_by = self.request.user
            form.instance.closed_at = timezone.now()
        if form.cleaned_data.get("disposition") and not form.instance.disposition_by:
            form.instance.disposition_by = self.request.user
            form.instance.disposition_date = timezone.now().date()
        messages.success(self.request, f"NCR {self.object.ncr_number} disposition updated.")
        return super().form_valid(form)


class NCRPhotoUploadView(LoginRequiredMixin, View):
    """Upload a photo to an NCR."""

    def post(self, request, pk):
        ncr = get_object_or_404(NCR, pk=pk)
        form = NCRPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.ncr = ncr
            photo.taken_by = request.user
            photo.save()
            messages.success(request, "Photo uploaded successfully.")
        else:
            messages.error(request, "Failed to upload photo.")
        return redirect("quality:ncr_detail", pk=pk)


class NCRPhotoDeleteView(LoginRequiredMixin, View):
    """Delete a photo from an NCR."""

    def post(self, request, pk, photo_pk):
        photo = get_object_or_404(NCRPhoto, pk=photo_pk, ncr_id=pk)
        photo.delete()
        messages.success(request, "Photo deleted.")
        return redirect("quality:ncr_detail", pk=pk)
