"""
ARDT FMS - Maintenance App Views
Version: 5.4
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from .forms import (
    EquipmentCategoryForm,
    EquipmentForm,
    MaintenancePartsUsedForm,
    MaintenanceRequestApprovalForm,
    MaintenanceRequestForm,
    MaintenanceWorkOrderCompleteForm,
    MaintenanceWorkOrderForm,
)
from .models import Equipment, EquipmentCategory, MaintenancePartsUsed, MaintenanceRequest, MaintenanceWorkOrder


# =============================================================================
# Equipment Category Views
# =============================================================================


class EquipmentCategoryListView(LoginRequiredMixin, ListView):
    """List equipment categories."""

    model = EquipmentCategory
    template_name = "maintenance/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return EquipmentCategory.objects.filter(parent__isnull=True).prefetch_related("children")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Equipment Categories"
        return context


class EquipmentCategoryCreateView(LoginRequiredMixin, CreateView):
    """Create equipment category."""

    model = EquipmentCategory
    form_class = EquipmentCategoryForm
    template_name = "maintenance/category_form.html"
    success_url = reverse_lazy("maintenance:category_list")

    def form_valid(self, form):
        messages.success(self.request, f"Category '{form.instance.name}' created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Category"
        context["form_title"] = "Create Equipment Category"
        return context


class EquipmentCategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Update equipment category."""

    model = EquipmentCategory
    form_class = EquipmentCategoryForm
    template_name = "maintenance/category_form.html"
    success_url = reverse_lazy("maintenance:category_list")

    def form_valid(self, form):
        messages.success(self.request, f"Category '{form.instance.name}' updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        context["form_title"] = "Edit Equipment Category"
        return context


# =============================================================================
# Equipment Views
# =============================================================================


class EquipmentListView(LoginRequiredMixin, ListView):
    """List all equipment."""

    model = Equipment
    template_name = "maintenance/equipment_list.html"
    context_object_name = "equipment_list"
    paginate_by = 25

    def get_queryset(self):
        qs = Equipment.objects.select_related("category", "department")

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        # Filter by category
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category_id=category)

        # Search
        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(Q(code__icontains=search) | Q(name__icontains=search) | Q(serial_number__icontains=search))

        return qs.order_by("code")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Equipment"
        context["status_choices"] = Equipment.Status.choices
        context["categories"] = EquipmentCategory.objects.filter(is_active=True)
        context["current_status"] = self.request.GET.get("status", "")
        context["current_category"] = self.request.GET.get("category", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class EquipmentDetailView(LoginRequiredMixin, DetailView):
    """View equipment details."""

    model = Equipment
    template_name = "maintenance/equipment_detail.html"
    context_object_name = "equipment"

    def get_queryset(self):
        return Equipment.objects.select_related("category", "department")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipment = self.object
        context["page_title"] = f"{equipment.code} - {equipment.name}"

        # Recent maintenance requests
        context["recent_requests"] = equipment.maintenance_requests.order_by("-requested_at")[:5]

        # Recent work orders
        context["recent_work_orders"] = equipment.work_orders.order_by("-created_at")[:5]

        return context


class EquipmentCreateView(LoginRequiredMixin, CreateView):
    """Create equipment."""

    model = Equipment
    form_class = EquipmentForm
    template_name = "maintenance/equipment_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Equipment '{form.instance.code}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("maintenance:equipment_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Add Equipment"
        context["form_title"] = "Add New Equipment"
        return context


class EquipmentUpdateView(LoginRequiredMixin, UpdateView):
    """Update equipment."""

    model = Equipment
    form_class = EquipmentForm
    template_name = "maintenance/equipment_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Equipment '{form.instance.code}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("maintenance:equipment_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.code}"
        context["form_title"] = "Edit Equipment"
        return context


# =============================================================================
# Maintenance Request Views
# =============================================================================


class RequestListView(LoginRequiredMixin, ListView):
    """List maintenance requests."""

    model = MaintenanceRequest
    template_name = "maintenance/request_list.html"
    context_object_name = "requests"
    paginate_by = 25

    def get_queryset(self):
        qs = MaintenanceRequest.objects.select_related("equipment", "requested_by", "approved_by")

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        # Filter by type
        request_type = self.request.GET.get("type")
        if request_type:
            qs = qs.filter(request_type=request_type)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Maintenance Requests"
        context["status_choices"] = MaintenanceRequest.Status.choices
        context["type_choices"] = MaintenanceRequest.RequestType.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["current_type"] = self.request.GET.get("type", "")
        return context


class RequestDetailView(LoginRequiredMixin, DetailView):
    """View maintenance request details."""

    model = MaintenanceRequest
    template_name = "maintenance/request_detail.html"
    context_object_name = "request"

    def get_queryset(self):
        return MaintenanceRequest.objects.select_related("equipment", "requested_by", "approved_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Request {self.object.request_number}"
        context["work_orders"] = self.object.work_orders.all()
        return context


class RequestCreateView(LoginRequiredMixin, CreateView):
    """Create maintenance request."""

    model = MaintenanceRequest
    form_class = MaintenanceRequestForm
    template_name = "maintenance/request_form.html"

    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        form.instance.request_number = self.generate_request_number()
        messages.success(self.request, f"Request '{form.instance.request_number}' created successfully.")
        return super().form_valid(form)

    def generate_request_number(self):
        """Generate unique request number."""
        prefix = "MR"
        year = timezone.now().year
        last = MaintenanceRequest.objects.filter(request_number__startswith=f"{prefix}-{year}").order_by("-id").first()
        if last:
            try:
                last_num = int(last.request_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        return f"{prefix}-{year}-{str(next_num).zfill(4)}"

    def get_success_url(self):
        return reverse_lazy("maintenance:request_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Request"
        context["form_title"] = "Create Maintenance Request"
        return context


class RequestApproveView(LoginRequiredMixin, View):
    """Approve or reject maintenance request."""

    def post(self, request, pk):
        maint_request = get_object_or_404(MaintenanceRequest, pk=pk)
        action = request.POST.get("action")

        if action == "approve":
            maint_request.status = MaintenanceRequest.Status.APPROVED
            maint_request.approved_by = request.user
            maint_request.approved_at = timezone.now()
            maint_request.save()
            messages.success(request, f"Request {maint_request.request_number} approved.")
        elif action == "reject":
            maint_request.status = MaintenanceRequest.Status.REJECTED
            maint_request.approved_by = request.user
            maint_request.approved_at = timezone.now()
            maint_request.save()
            messages.warning(request, f"Request {maint_request.request_number} rejected.")

        return redirect("maintenance:request_detail", pk=pk)


# =============================================================================
# Maintenance Work Order Views
# =============================================================================


class MWOListView(LoginRequiredMixin, ListView):
    """List maintenance work orders."""

    model = MaintenanceWorkOrder
    template_name = "maintenance/mwo_list.html"
    context_object_name = "work_orders"
    paginate_by = 25

    def get_queryset(self):
        qs = MaintenanceWorkOrder.objects.select_related("equipment", "assigned_to", "created_by")

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Maintenance Work Orders"
        context["status_choices"] = MaintenanceWorkOrder.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        return context


class MWODetailView(LoginRequiredMixin, DetailView):
    """View maintenance work order details."""

    model = MaintenanceWorkOrder
    template_name = "maintenance/mwo_detail.html"
    context_object_name = "mwo"

    def get_queryset(self):
        return MaintenanceWorkOrder.objects.select_related("equipment", "request", "assigned_to", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"MWO {self.object.mwo_number}"
        context["parts_used"] = self.object.parts_used.select_related("inventory_item")
        context["parts_form"] = MaintenancePartsUsedForm()
        return context


class MWOCreateView(LoginRequiredMixin, CreateView):
    """Create maintenance work order."""

    model = MaintenanceWorkOrder
    form_class = MaintenanceWorkOrderForm
    template_name = "maintenance/mwo_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.mwo_number = self.generate_mwo_number()
        messages.success(self.request, f"Work Order '{form.instance.mwo_number}' created successfully.")

        # Update request status if linked
        if form.instance.request:
            form.instance.request.status = MaintenanceRequest.Status.IN_PROGRESS
            form.instance.request.save()

        return super().form_valid(form)

    def generate_mwo_number(self):
        """Generate unique MWO number."""
        prefix = "MWO"
        year = timezone.now().year
        last = MaintenanceWorkOrder.objects.filter(mwo_number__startswith=f"{prefix}-{year}").order_by("-id").first()
        if last:
            try:
                last_num = int(last.mwo_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        return f"{prefix}-{year}-{str(next_num).zfill(4)}"

    def get_success_url(self):
        return reverse_lazy("maintenance:mwo_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Work Order"
        context["form_title"] = "Create Maintenance Work Order"
        return context


class MWOUpdateView(LoginRequiredMixin, UpdateView):
    """Update maintenance work order."""

    model = MaintenanceWorkOrder
    form_class = MaintenanceWorkOrderForm
    template_name = "maintenance/mwo_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Work Order '{form.instance.mwo_number}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("maintenance:mwo_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.mwo_number}"
        context["form_title"] = "Edit Maintenance Work Order"
        return context


class MWOStartView(LoginRequiredMixin, View):
    """Start working on maintenance work order."""

    def post(self, request, pk):
        mwo = get_object_or_404(MaintenanceWorkOrder, pk=pk)

        if mwo.status == MaintenanceWorkOrder.Status.PLANNED:
            mwo.status = MaintenanceWorkOrder.Status.IN_PROGRESS
            mwo.actual_start = timezone.now()
            mwo.save()

            # Update equipment status
            mwo.equipment.status = Equipment.Status.MAINTENANCE
            mwo.equipment.save()

            messages.success(request, f"Started work on {mwo.mwo_number}.")
        else:
            messages.error(request, f"Cannot start work order with status {mwo.get_status_display()}.")

        return redirect("maintenance:mwo_detail", pk=pk)


class MWOCompleteView(LoginRequiredMixin, UpdateView):
    """Complete maintenance work order."""

    model = MaintenanceWorkOrder
    form_class = MaintenanceWorkOrderCompleteForm
    template_name = "maintenance/mwo_complete.html"

    def form_valid(self, form):
        mwo = form.save(commit=False)
        mwo.status = MaintenanceWorkOrder.Status.COMPLETED
        mwo.actual_end = timezone.now()

        # Calculate parts cost
        mwo.parts_cost = sum(p.total_cost for p in mwo.parts_used.all())
        mwo.total_cost = mwo.parts_cost  # Could add labor cost calculation

        mwo.save()

        # Update equipment
        mwo.equipment.status = Equipment.Status.OPERATIONAL
        mwo.equipment.last_maintenance = timezone.now().date()
        if mwo.equipment.maintenance_interval_days:
            from datetime import timedelta

            mwo.equipment.next_maintenance = timezone.now().date() + timedelta(days=mwo.equipment.maintenance_interval_days)
        mwo.equipment.save()

        # Update request if linked
        if mwo.request:
            mwo.request.status = MaintenanceRequest.Status.COMPLETED
            mwo.request.save()

        messages.success(self.request, f"Work Order {mwo.mwo_number} completed successfully.")
        return redirect("maintenance:mwo_detail", pk=mwo.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Complete {self.object.mwo_number}"
        return context


class MWOAddPartView(LoginRequiredMixin, View):
    """Add part to maintenance work order."""

    def post(self, request, pk):
        mwo = get_object_or_404(MaintenanceWorkOrder, pk=pk)
        form = MaintenancePartsUsedForm(request.POST)

        if form.is_valid():
            part = form.save(commit=False)
            part.mwo = mwo

            # Get unit cost from inventory item
            part.unit_cost = part.inventory_item.standard_cost
            part.total_cost = part.quantity * part.unit_cost
            part.save()

            messages.success(request, f"Part added to {mwo.mwo_number}.")
        else:
            messages.error(request, "Failed to add part.")

        return redirect("maintenance:mwo_detail", pk=pk)


# =============================================================================
# Preventive Maintenance Scheduling Views
# =============================================================================


class PreventiveMaintenanceScheduleView(LoginRequiredMixin, ListView):
    """View preventive maintenance schedule for all equipment."""

    model = Equipment
    template_name = "maintenance/pm_schedule.html"
    context_object_name = "equipment_list"

    def get_queryset(self):
        from datetime import timedelta

        today = timezone.now().date()
        days_ahead = int(self.request.GET.get("days", 30))

        # Equipment with scheduled maintenance
        qs = Equipment.objects.filter(
            status__in=[Equipment.Status.OPERATIONAL, Equipment.Status.MAINTENANCE],
            maintenance_interval_days__isnull=False,
        ).select_related("category", "department")

        # Filter by timeframe
        filter_type = self.request.GET.get("filter", "all")
        if filter_type == "overdue":
            qs = qs.filter(next_maintenance__lt=today)
        elif filter_type == "upcoming":
            qs = qs.filter(next_maintenance__gte=today, next_maintenance__lte=today + timedelta(days=days_ahead))
        elif filter_type == "due_today":
            qs = qs.filter(next_maintenance=today)

        return qs.order_by("next_maintenance")

    def get_context_data(self, **kwargs):
        from datetime import timedelta

        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        context["page_title"] = "Preventive Maintenance Schedule"
        context["today"] = today
        context["current_filter"] = self.request.GET.get("filter", "all")
        context["days_ahead"] = int(self.request.GET.get("days", 30))

        # Summary counts
        all_equipment = Equipment.objects.filter(
            status__in=[Equipment.Status.OPERATIONAL, Equipment.Status.MAINTENANCE],
            maintenance_interval_days__isnull=False,
        )
        context["overdue_count"] = all_equipment.filter(next_maintenance__lt=today).count()
        context["due_today_count"] = all_equipment.filter(next_maintenance=today).count()
        context["upcoming_count"] = all_equipment.filter(
            next_maintenance__gt=today,
            next_maintenance__lte=today + timedelta(days=30)
        ).count()

        return context


class GeneratePreventiveMaintenanceView(LoginRequiredMixin, View):
    """Generate preventive maintenance requests for equipment that's due."""

    def get(self, request):
        """Show confirmation page."""
        from django.shortcuts import render

        today = timezone.now().date()

        # Find equipment due for maintenance (including overdue)
        due_equipment = Equipment.objects.filter(
            status=Equipment.Status.OPERATIONAL,
            maintenance_interval_days__isnull=False,
            next_maintenance__lte=today,
        ).exclude(
            # Exclude equipment that already has pending/in-progress maintenance requests
            maintenance_requests__status__in=[
                MaintenanceRequest.Status.PENDING,
                MaintenanceRequest.Status.APPROVED,
                MaintenanceRequest.Status.IN_PROGRESS,
            ]
        ).select_related("category", "department")

        return render(request, "maintenance/pm_generate.html", {
            "page_title": "Generate Preventive Maintenance",
            "equipment_list": due_equipment,
            "count": due_equipment.count(),
        })

    def post(self, request):
        """Create maintenance requests for due equipment."""
        today = timezone.now().date()
        created_count = 0

        # Find equipment due for maintenance
        due_equipment = Equipment.objects.filter(
            status=Equipment.Status.OPERATIONAL,
            maintenance_interval_days__isnull=False,
            next_maintenance__lte=today,
        ).exclude(
            maintenance_requests__status__in=[
                MaintenanceRequest.Status.PENDING,
                MaintenanceRequest.Status.APPROVED,
                MaintenanceRequest.Status.IN_PROGRESS,
            ]
        )

        for equipment in due_equipment:
            # Generate request number
            prefix = "MR"
            year = timezone.now().year
            last = MaintenanceRequest.objects.filter(
                request_number__startswith=f"{prefix}-{year}"
            ).order_by("-id").first()
            if last:
                try:
                    last_num = int(last.request_number.split("-")[-1])
                    next_num = last_num + 1
                except (ValueError, IndexError):
                    next_num = 1
            else:
                next_num = 1
            request_number = f"{prefix}-{year}-{str(next_num).zfill(4)}"

            # Create the maintenance request
            MaintenanceRequest.objects.create(
                request_number=request_number,
                equipment=equipment,
                request_type=MaintenanceRequest.RequestType.PREVENTIVE,
                priority=MaintenanceRequest.Priority.NORMAL,
                title=f"Scheduled Preventive Maintenance - {equipment.code}",
                description=f"Scheduled preventive maintenance for {equipment.name}. "
                           f"Last maintenance: {equipment.last_maintenance or 'Never'}. "
                           f"Maintenance interval: {equipment.maintenance_interval_days} days.",
                status=MaintenanceRequest.Status.PENDING,
                requested_by=request.user,
            )
            created_count += 1

        if created_count > 0:
            messages.success(request, f"Created {created_count} preventive maintenance request(s).")
        else:
            messages.info(request, "No equipment is currently due for preventive maintenance.")

        return redirect("maintenance:pm_schedule")
