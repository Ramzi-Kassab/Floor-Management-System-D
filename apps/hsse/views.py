"""
ARDT FMS - HSSE Views
Version: 5.4

Views for Health, Safety, Security, and Environment management.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView

from .models import HOCReport, Incident, Journey
from .forms import HOCReportForm, IncidentForm, JourneyForm


# =============================================================================
# DASHBOARD VIEW
# =============================================================================


class HSSEDashboardView(LoginRequiredMixin, TemplateView):
    """HSSE dashboard with overview."""

    template_name = "hsse/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "HSSE Dashboard"

        # Stats
        context["open_hoc"] = HOCReport.objects.filter(status='OPEN').count()
        context["open_incidents"] = Incident.objects.exclude(status='CLOSED').count()
        context["active_journeys"] = Journey.objects.filter(status='IN_PROGRESS').count()
        context["pending_approvals"] = Journey.objects.filter(status='PLANNED').count()

        # Recent items
        context["recent_hoc"] = HOCReport.objects.select_related('reported_by').order_by('-reported_at')[:5]
        context["recent_incidents"] = Incident.objects.select_related('reported_by').order_by('-occurred_at')[:5]

        return context


# =============================================================================
# HOC REPORT VIEWS
# =============================================================================


class HOCReportListView(LoginRequiredMixin, ListView):
    """List all HOC reports."""

    model = HOCReport
    template_name = "hsse/hoc_list.html"
    context_object_name = "reports"
    paginate_by = 25

    def get_queryset(self):
        queryset = HOCReport.objects.select_related('reported_by').order_by('-reported_at')

        # Filter by category
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category=category)

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(hoc_number__icontains=search) |
                Q(location__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "HOC Reports"
        context["categories"] = HOCReport.Category.choices
        context["statuses"] = HOCReport.Status.choices
        context["current_category"] = self.request.GET.get("category", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class HOCReportDetailView(LoginRequiredMixin, DetailView):
    """View HOC report details."""

    model = HOCReport
    template_name = "hsse/hoc_detail.html"
    context_object_name = "report"

    def get_queryset(self):
        return HOCReport.objects.select_related('reported_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"HOC: {self.object.hoc_number}"
        return context


class HOCReportCreateView(LoginRequiredMixin, CreateView):
    """Create HOC report."""

    model = HOCReport
    form_class = HOCReportForm
    template_name = "hsse/hoc_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Report Hazard Observation"
        return context

    def form_valid(self, form):
        form.instance.reported_by = self.request.user
        messages.success(self.request, f"HOC Report '{form.instance.hoc_number}' submitted successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("hsse:hoc-detail", kwargs={"pk": self.object.pk})


class HOCReportUpdateView(LoginRequiredMixin, UpdateView):
    """Update HOC report."""

    model = HOCReport
    form_class = HOCReportForm
    template_name = "hsse/hoc_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit: {self.object.hoc_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"HOC Report '{form.instance.hoc_number}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("hsse:hoc-detail", kwargs={"pk": self.object.pk})


class HOCReportDeleteView(LoginRequiredMixin, DeleteView):
    """Delete HOC report."""

    model = HOCReport
    template_name = "hsse/hoc_confirm_delete.html"
    success_url = reverse_lazy("hsse:hoc-list")


# =============================================================================
# INCIDENT VIEWS
# =============================================================================


class IncidentListView(LoginRequiredMixin, ListView):
    """List all incidents."""

    model = Incident
    template_name = "hsse/incident_list.html"
    context_object_name = "incidents"
    paginate_by = 25

    def get_queryset(self):
        queryset = Incident.objects.select_related('reported_by').order_by('-occurred_at')

        # Filter by type
        incident_type = self.request.GET.get("type")
        if incident_type:
            queryset = queryset.filter(incident_type=incident_type)

        # Filter by severity
        severity = self.request.GET.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(incident_number__icontains=search) |
                Q(location__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Incidents"
        context["types"] = Incident.IncidentType.choices
        context["severities"] = Incident.Severity.choices
        context["statuses"] = Incident.Status.choices
        context["current_type"] = self.request.GET.get("type", "")
        context["current_severity"] = self.request.GET.get("severity", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class IncidentDetailView(LoginRequiredMixin, DetailView):
    """View incident details."""

    model = Incident
    template_name = "hsse/incident_detail.html"
    context_object_name = "incident"

    def get_queryset(self):
        return Incident.objects.select_related('reported_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Incident: {self.object.incident_number}"
        return context


class IncidentCreateView(LoginRequiredMixin, CreateView):
    """Create incident report."""

    model = Incident
    form_class = IncidentForm
    template_name = "hsse/incident_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Report Incident"
        return context

    def form_valid(self, form):
        form.instance.reported_by = self.request.user
        messages.success(self.request, f"Incident '{form.instance.incident_number}' reported successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("hsse:incident-detail", kwargs={"pk": self.object.pk})


class IncidentUpdateView(LoginRequiredMixin, UpdateView):
    """Update incident."""

    model = Incident
    form_class = IncidentForm
    template_name = "hsse/incident_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit: {self.object.incident_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Incident '{form.instance.incident_number}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("hsse:incident-detail", kwargs={"pk": self.object.pk})


class IncidentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete incident."""

    model = Incident
    template_name = "hsse/incident_confirm_delete.html"
    success_url = reverse_lazy("hsse:incident-list")


# =============================================================================
# JOURNEY VIEWS
# =============================================================================


class JourneyListView(LoginRequiredMixin, ListView):
    """List all journeys."""

    model = Journey
    template_name = "hsse/journey_list.html"
    context_object_name = "journeys"
    paginate_by = 25

    def get_queryset(self):
        queryset = Journey.objects.select_related('driver', 'vehicle', 'approved_by').order_by('-planned_departure')

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(journey_number__icontains=search) |
                Q(purpose__icontains=search) |
                Q(destination__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Journey Management"
        context["statuses"] = Journey.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class JourneyDetailView(LoginRequiredMixin, DetailView):
    """View journey details."""

    model = Journey
    template_name = "hsse/journey_detail.html"
    context_object_name = "journey"

    def get_queryset(self):
        return Journey.objects.select_related('driver', 'vehicle', 'approved_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Journey: {self.object.journey_number}"
        return context


class JourneyCreateView(LoginRequiredMixin, CreateView):
    """Create journey."""

    model = Journey
    form_class = JourneyForm
    template_name = "hsse/journey_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Plan Journey"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Journey '{form.instance.journey_number}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("hsse:journey-detail", kwargs={"pk": self.object.pk})


class JourneyUpdateView(LoginRequiredMixin, UpdateView):
    """Update journey."""

    model = Journey
    form_class = JourneyForm
    template_name = "hsse/journey_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit: {self.object.journey_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Journey '{form.instance.journey_number}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("hsse:journey-detail", kwargs={"pk": self.object.pk})


class JourneyDeleteView(LoginRequiredMixin, DeleteView):
    """Delete journey."""

    model = Journey
    template_name = "hsse/journey_confirm_delete.html"
    success_url = reverse_lazy("hsse:journey-list")


class JourneyApproveView(LoginRequiredMixin, View):
    """Approve journey."""

    def post(self, request, pk):
        journey = get_object_or_404(Journey, pk=pk)
        if journey.status == 'PLANNED':
            journey.status = 'APPROVED'
            journey.approved_by = request.user
            journey.save()
            messages.success(request, f"Journey '{journey.journey_number}' approved.")
        return redirect('hsse:journey-detail', pk=pk)


class JourneyStartView(LoginRequiredMixin, View):
    """Start journey."""

    def post(self, request, pk):
        journey = get_object_or_404(Journey, pk=pk)
        if journey.status == 'APPROVED':
            journey.status = 'IN_PROGRESS'
            journey.actual_departure = timezone.now()
            journey.save()
            messages.success(request, f"Journey '{journey.journey_number}' started.")
        return redirect('hsse:journey-detail', pk=pk)


class JourneyCompleteView(LoginRequiredMixin, View):
    """Complete journey."""

    def post(self, request, pk):
        journey = get_object_or_404(Journey, pk=pk)
        if journey.status == 'IN_PROGRESS':
            journey.status = 'COMPLETED'
            journey.actual_arrival = timezone.now()
            journey.save()
            messages.success(request, f"Journey '{journey.journey_number}' completed.")
        return redirect('hsse:journey-detail', pk=pk)
