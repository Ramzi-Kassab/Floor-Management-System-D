"""
ARDT FMS - DRSS Views
Version: 5.4 - Sprint 2

Views for DRSS (Drill Request Service System) management.
"""

import csv
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.mixins import PlannerRequiredMixin
from apps.sales.models import Customer

from .forms import (
    DRSSEvaluationForm,
    DRSSRequestForm,
    DRSSRequestLineForm,
    DRSSRequestLineFormSet,
)
from .models import DRSSRequest, DRSSRequestLine

# =============================================================================
# DRSS REQUEST VIEWS
# =============================================================================


class DRSSListView(LoginRequiredMixin, ListView):
    """
    List all DRSS requests with search and filtering.
    """

    model = DRSSRequest
    template_name = "drss/drss_list.html"
    context_object_name = "requests"
    paginate_by = 25

    def get_queryset(self):
        queryset = (
            DRSSRequest.objects.select_related("customer", "rig", "well", "received_by", "evaluated_by")
            .prefetch_related("lines")
            .annotate(total_lines=Count("lines"), fulfilled_lines=Count("lines", filter=Q(lines__status="FULFILLED")))
        )

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(drss_number__icontains=search)
                | Q(external_reference__icontains=search)
                | Q(customer__name__icontains=search)
                | Q(rig__name__icontains=search)
            )

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filter by priority
        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        # Filter by customer
        customer_id = self.request.GET.get("customer")
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        # Filter by date range
        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(required_date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(required_date__lte=date_to)

        return queryset.order_by("-requested_date", "-priority")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "DRSS Requests"
        context["statuses"] = DRSSRequest.Status.choices
        context["priorities"] = DRSSRequest.Priority.choices
        context["customers"] = Customer.objects.filter(is_active=True, is_aramco=True).order_by("name")

        # Stats
        today = timezone.now().date()
        week_end = today + timedelta(days=7)

        context["stats"] = {
            "total": DRSSRequest.objects.count(),
            "pending": DRSSRequest.objects.filter(status__in=["RECEIVED", "EVALUATING"]).count(),
            "due_this_week": DRSSRequest.objects.filter(
                required_date__range=[today, week_end], status__in=["RECEIVED", "EVALUATING", "CONFIRMED"]
            ).count(),
            "overdue": DRSSRequest.objects.filter(
                required_date__lt=today, status__in=["RECEIVED", "EVALUATING", "CONFIRMED", "PARTIAL"]
            ).count(),
        }

        context["search_query"] = self.request.GET.get("q", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["current_priority"] = self.request.GET.get("priority", "")
        return context


class DRSSDetailView(LoginRequiredMixin, DetailView):
    """
    View DRSS request details with all lines.
    """

    model = DRSSRequest
    template_name = "drss/drss_detail.html"
    context_object_name = "drss"

    def get_queryset(self):
        return DRSSRequest.objects.select_related("customer", "rig", "well", "received_by", "evaluated_by").prefetch_related(
            "lines", "lines__work_order", "lines__source_bit"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        drss = self.object
        context["page_title"] = f"DRSS: {drss.drss_number}"
        context["lines"] = drss.lines.all().order_by("line_number")

        # Stats
        lines = drss.lines.all()
        context["stats"] = {
            "total_lines": lines.count(),
            "pending": lines.filter(status="PENDING").count(),
            "evaluating": lines.filter(status="EVALUATING").count(),
            "confirmed": lines.filter(status="CONFIRMED").count(),
            "fulfilled": lines.filter(status="FULFILLED").count(),
            "cancelled": lines.filter(status="CANCELLED").count(),
            "total_quantity": lines.aggregate(total=Sum("quantity"))["total"] or 0,
        }

        # Check if overdue
        today = timezone.now().date()
        context["is_overdue"] = drss.required_date < today and drss.status not in ["FULFILLED", "CANCELLED"]

        return context


class DRSSCreateView(PlannerRequiredMixin, CreateView):
    """
    Create a new DRSS request.
    """

    model = DRSSRequest
    form_class = DRSSRequestForm
    template_name = "drss/drss_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New DRSS Request"
        context["submit_text"] = "Create DRSS Request"

        if self.request.POST:
            context["lines_formset"] = DRSSRequestLineFormSet(self.request.POST)
        else:
            context["lines_formset"] = DRSSRequestLineFormSet()

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context["lines_formset"]

        with transaction.atomic():
            form.instance.received_by = self.request.user
            self.object = form.save()

            if lines_formset.is_valid():
                lines_formset.instance = self.object
                lines_formset.save()
            else:
                return self.form_invalid(form)

        messages.success(self.request, f"DRSS Request {self.object.drss_number} created successfully.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("drss:drss_detail", kwargs={"pk": self.object.pk})


class DRSSUpdateView(PlannerRequiredMixin, UpdateView):
    """
    Update an existing DRSS request.
    """

    model = DRSSRequest
    form_class = DRSSRequestForm
    template_name = "drss/drss_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit DRSS: {self.object.drss_number}"
        context["submit_text"] = "Update DRSS Request"

        if self.request.POST:
            context["lines_formset"] = DRSSRequestLineFormSet(self.request.POST, instance=self.object)
        else:
            context["lines_formset"] = DRSSRequestLineFormSet(instance=self.object)

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context["lines_formset"]

        with transaction.atomic():
            self.object = form.save()

            if lines_formset.is_valid():
                lines_formset.save()
            else:
                return self.form_invalid(form)

        messages.success(self.request, f"DRSS Request {self.object.drss_number} updated successfully.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("drss:drss_detail", kwargs={"pk": self.object.pk})


# =============================================================================
# DRSS LINE VIEWS
# =============================================================================


@login_required
def evaluate_line(request, pk):
    """
    Evaluate a single DRSS request line.
    """
    line = get_object_or_404(DRSSRequestLine, pk=pk)
    drss = line.drss_request

    if request.method == "POST":
        form = DRSSEvaluationForm(request.POST, instance=line)
        if form.is_valid():
            line = form.save(commit=False)

            # Update parent DRSS status if needed
            if line.status == "CONFIRMED" and drss.status == "RECEIVED":
                drss.status = DRSSRequest.Status.EVALUATING
                drss.evaluated_by = request.user
                drss.evaluated_at = timezone.now()
                drss.save()

            line.save()
            messages.success(request, f"Line {line.line_number} updated successfully.")
            return redirect("drss:drss_detail", pk=drss.pk)
    else:
        form = DRSSEvaluationForm(instance=line)

    return render(
        request,
        "drss/line_evaluate.html",
        {"form": form, "line": line, "drss": drss, "page_title": f"Evaluate Line {line.line_number}"},
    )


@login_required
def add_line(request, drss_pk):
    """
    Add a new line to a DRSS request.
    """
    drss = get_object_or_404(DRSSRequest, pk=drss_pk)

    if request.method == "POST":
        form = DRSSRequestLineForm(request.POST)
        if form.is_valid():
            line = form.save(commit=False)
            line.drss_request = drss

            # Auto-assign line number if not provided
            if not line.line_number:
                max_line = drss.lines.order_by("-line_number").first()
                line.line_number = (max_line.line_number + 1) if max_line else 1

            line.save()
            messages.success(request, f"Line {line.line_number} added successfully.")
            return redirect("drss:drss_detail", pk=drss.pk)
    else:
        # Pre-fill line number
        max_line = drss.lines.order_by("-line_number").first()
        initial_line = (max_line.line_number + 1) if max_line else 1
        form = DRSSRequestLineForm(initial={"line_number": initial_line})

    return render(
        request, "drss/line_form.html", {"form": form, "drss": drss, "page_title": f"Add Line to {drss.drss_number}"}
    )


@login_required
def delete_line(request, pk):
    """
    Delete a DRSS request line.
    """
    line = get_object_or_404(DRSSRequestLine, pk=pk)
    drss = line.drss_request

    if request.method == "POST":
        line_number = line.line_number
        line.delete()
        messages.success(request, f"Line {line_number} deleted.")
        return redirect("drss:drss_detail", pk=drss.pk)

    return render(
        request, "drss/line_confirm_delete.html", {"line": line, "drss": drss, "page_title": f"Delete Line {line.line_number}"}
    )


# =============================================================================
# STATUS UPDATES
# =============================================================================


@login_required
def update_status(request, pk):
    """
    Update DRSS request status (HTMX endpoint).
    """
    drss = get_object_or_404(DRSSRequest, pk=pk)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status and new_status in dict(DRSSRequest.Status.choices):
            old_status = drss.status
            drss.status = new_status

            # Track evaluation
            if new_status == "EVALUATING" and old_status == "RECEIVED":
                drss.evaluated_by = request.user
                drss.evaluated_at = timezone.now()

            drss.save()
            messages.success(request, f"Status updated to {drss.get_status_display()}.")

    return redirect("drss:drss_detail", pk=pk)


# =============================================================================
# EXPORT
# =============================================================================


@login_required
def export_csv(request):
    """Export DRSS requests to CSV."""
    response = HttpResponse(content_type="text/csv")
    filename = f'drss_requests_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "DRSS Number",
            "Customer",
            "Rig",
            "Well",
            "Status",
            "Priority",
            "Requested Date",
            "Required Date",
            "Lines",
            "Fulfilled",
        ]
    )

    queryset = (
        DRSSRequest.objects.select_related("customer", "rig", "well").prefetch_related("lines").order_by("-requested_date")
    )

    for d in queryset:
        writer.writerow(
            [
                d.drss_number,
                d.customer.name,
                d.rig.name if d.rig else "",
                d.well.name if d.well else "",
                d.get_status_display(),
                d.get_priority_display(),
                d.requested_date.strftime("%Y-%m-%d"),
                d.required_date.strftime("%Y-%m-%d"),
                d.line_count,
                d.fulfilled_count,
            ]
        )

    return response
