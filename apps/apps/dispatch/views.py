"""
ARDT FMS - Dispatch Views
Version: 5.4

Views for dispatch and fleet management.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView

from .models import Vehicle, Dispatch, DispatchItem, InventoryReservation
from .forms import VehicleForm, DispatchForm, DispatchItemForm, InventoryReservationForm


# =============================================================================
# DASHBOARD VIEW
# =============================================================================


class DispatchDashboardView(LoginRequiredMixin, TemplateView):
    """Dispatch dashboard with overview."""

    template_name = "dispatch/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Dispatch Dashboard"

        # Stats
        context["vehicles_available"] = Vehicle.objects.filter(status='AVAILABLE', is_active=True).count()
        context["vehicles_in_use"] = Vehicle.objects.filter(status='IN_USE').count()
        context["dispatches_planned"] = Dispatch.objects.filter(status='PLANNED').count()
        context["dispatches_in_transit"] = Dispatch.objects.filter(status='IN_TRANSIT').count()

        # Recent dispatches
        context["recent_dispatches"] = Dispatch.objects.select_related(
            'vehicle', 'customer'
        ).order_by('-created_at')[:10]

        return context


# =============================================================================
# VEHICLE VIEWS
# =============================================================================


class VehicleListView(LoginRequiredMixin, ListView):
    """List all vehicles."""

    model = Vehicle
    template_name = "dispatch/vehicle_list.html"
    context_object_name = "vehicles"
    paginate_by = 25

    def get_queryset(self):
        queryset = Vehicle.objects.annotate(
            dispatch_count=Count('dispatches')
        ).order_by('code')

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filter by active
        active = self.request.GET.get("active")
        if active == "yes":
            queryset = queryset.filter(is_active=True)
        elif active == "no":
            queryset = queryset.filter(is_active=False)

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(plate_number__icontains=search) |
                Q(make__icontains=search) |
                Q(model__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Fleet Vehicles"
        context["status_choices"] = Vehicle.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class VehicleDetailView(LoginRequiredMixin, DetailView):
    """View vehicle details."""

    model = Vehicle
    template_name = "dispatch/vehicle_detail.html"
    context_object_name = "vehicle"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Vehicle: {self.object.code}"
        context["recent_dispatches"] = self.object.dispatches.select_related('customer').order_by('-planned_date')[:10]
        return context


class VehicleCreateView(LoginRequiredMixin, CreateView):
    """Create a new vehicle."""

    model = Vehicle
    form_class = VehicleForm
    template_name = "dispatch/vehicle_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Add Vehicle"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Vehicle '{form.instance.code}' added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dispatch:vehicle-detail", kwargs={"pk": self.object.pk})


class VehicleUpdateView(LoginRequiredMixin, UpdateView):
    """Update vehicle."""

    model = Vehicle
    form_class = VehicleForm
    template_name = "dispatch/vehicle_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit: {self.object.code}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Vehicle '{form.instance.code}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dispatch:vehicle-detail", kwargs={"pk": self.object.pk})


class VehicleDeleteView(LoginRequiredMixin, DeleteView):
    """Delete vehicle."""

    model = Vehicle
    template_name = "dispatch/vehicle_confirm_delete.html"
    success_url = reverse_lazy("dispatch:vehicle-list")


# =============================================================================
# DISPATCH VIEWS
# =============================================================================


class DispatchListView(LoginRequiredMixin, ListView):
    """List all dispatches."""

    model = Dispatch
    template_name = "dispatch/dispatch_list.html"
    context_object_name = "dispatches"
    paginate_by = 25

    def get_queryset(self):
        queryset = Dispatch.objects.select_related(
            'vehicle', 'customer', 'destination', 'created_by'
        ).prefetch_related('items').order_by('-planned_date')

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filter by date
        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(planned_date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(planned_date__lte=date_to)

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(dispatch_number__icontains=search) |
                Q(customer__name__icontains=search) |
                Q(driver_name__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Dispatches"
        context["status_choices"] = Dispatch.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class DispatchDetailView(LoginRequiredMixin, DetailView):
    """View dispatch details."""

    model = Dispatch
    template_name = "dispatch/dispatch_detail.html"
    context_object_name = "dispatch"

    def get_queryset(self):
        return Dispatch.objects.select_related(
            'vehicle', 'customer', 'destination', 'rig', 'created_by'
        ).prefetch_related('items__drill_bit', 'items__sales_order_line')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Dispatch: {self.object.dispatch_number}"
        return context


class DispatchCreateView(LoginRequiredMixin, CreateView):
    """Create a new dispatch."""

    model = Dispatch
    form_class = DispatchForm
    template_name = "dispatch/dispatch_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Dispatch"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Dispatch '{form.instance.dispatch_number}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dispatch:dispatch-detail", kwargs={"pk": self.object.pk})


class DispatchUpdateView(LoginRequiredMixin, UpdateView):
    """Update dispatch."""

    model = Dispatch
    form_class = DispatchForm
    template_name = "dispatch/dispatch_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit: {self.object.dispatch_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Dispatch '{form.instance.dispatch_number}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dispatch:dispatch-detail", kwargs={"pk": self.object.pk})


class DispatchDeleteView(LoginRequiredMixin, DeleteView):
    """Delete dispatch."""

    model = Dispatch
    template_name = "dispatch/dispatch_confirm_delete.html"
    success_url = reverse_lazy("dispatch:dispatch-list")


class DispatchStatusUpdateView(LoginRequiredMixin, View):
    """Update dispatch status."""

    def post(self, request, pk):
        dispatch = get_object_or_404(Dispatch, pk=pk)
        new_status = request.POST.get('status')

        if new_status in dict(Dispatch.Status.choices):
            old_status = dispatch.status
            dispatch.status = new_status

            # Set timestamps based on status
            if new_status == 'IN_TRANSIT' and not dispatch.actual_departure:
                dispatch.actual_departure = timezone.now()
            elif new_status == 'DELIVERED' and not dispatch.actual_arrival:
                dispatch.actual_arrival = timezone.now()

            dispatch.save()
            messages.success(request, f"Dispatch status updated to {dispatch.get_status_display()}.")
        else:
            messages.error(request, "Invalid status.")

        return redirect('dispatch:dispatch-detail', pk=pk)


# =============================================================================
# INVENTORY RESERVATION VIEWS
# =============================================================================


class ReservationListView(LoginRequiredMixin, ListView):
    """List inventory reservations."""

    model = InventoryReservation
    template_name = "dispatch/reservation_list.html"
    context_object_name = "reservations"
    paginate_by = 25

    def get_queryset(self):
        queryset = InventoryReservation.objects.select_related(
            'inventory_item', 'work_order', 'reserved_by'
        ).order_by('-reserved_at')

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Inventory Reservations"
        context["status_choices"] = InventoryReservation.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        return context


class ReservationCreateView(LoginRequiredMixin, CreateView):
    """Create inventory reservation."""

    model = InventoryReservation
    form_class = InventoryReservationForm
    template_name = "dispatch/reservation_form.html"
    success_url = reverse_lazy("dispatch:reservation-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Reservation"
        return context

    def form_valid(self, form):
        form.instance.reserved_by = self.request.user
        messages.success(self.request, "Reservation created successfully.")
        return super().form_valid(form)


class ReservationUpdateView(LoginRequiredMixin, UpdateView):
    """Update reservation status."""

    model = InventoryReservation
    form_class = InventoryReservationForm
    template_name = "dispatch/reservation_form.html"
    success_url = reverse_lazy("dispatch:reservation-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Edit Reservation"
        return context
