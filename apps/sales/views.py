"""
ARDT FMS - Sales Views
Version: 5.4 - Sprint 2

Views for customer, rig, well, and warehouse management.
"""

import csv
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.core.mixins import ManagerRequiredMixin

from .forms import (
    CustomerContactForm, CustomerForm, RigForm, WarehouseForm, WellForm,
    CustomerDocumentRequirementForm, SalesOrderForm, SalesOrderLineForm,
    ServiceSiteForm, FieldTechnicianForm, FieldServiceRequestForm,
    ServiceScheduleForm, SiteVisitForm, ServiceReportForm,
    FieldDrillStringRunForm, FieldRunDataForm,
    FieldPerformanceLogForm, FieldInspectionForm, RunHoursForm,
    FieldIncidentForm, FieldDataEntryForm, FieldPhotoForm, FieldDocumentForm,
    GPSLocationForm, FieldWorkOrderForm, FieldAssetAssignmentForm
)
from .models import (
    Customer, CustomerContact, Rig, Warehouse, Well,
    CustomerDocumentRequirement, SalesOrder, SalesOrderLine,
    ServiceSite, FieldTechnician, FieldServiceRequest,
    ServiceSchedule, SiteVisit, ServiceReport,
    FieldDrillStringRun, FieldRunData,
    FieldPerformanceLog, FieldInspection, RunHours,
    FieldIncident, FieldDataEntry, FieldPhoto, FieldDocument,
    GPSLocation, FieldWorkOrder, FieldAssetAssignment
)

# =============================================================================
# CUSTOMER VIEWS
# =============================================================================


class CustomerListView(LoginRequiredMixin, ListView):
    """
    List all customers with search and filtering.
    """

    model = Customer
    template_name = "sales/customer_list.html"
    context_object_name = "customers"
    paginate_by = 25

    def get_queryset(self):
        queryset = (
            Customer.objects.select_related("account_manager", "created_by")
            .prefetch_related("contacts", "rigs", "wells")
            .annotate(contact_count=Count("contacts"), rig_count=Count("rigs"), well_count=Count("wells"))
        )

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(name_ar__icontains=search)
                | Q(city__icontains=search)
                | Q(email__icontains=search)
            )

        # Filter by type
        customer_type = self.request.GET.get("type")
        if customer_type:
            queryset = queryset.filter(customer_type=customer_type)

        # Filter by status
        status = self.request.GET.get("status")
        if status == "active":
            queryset = queryset.filter(is_active=True)
        elif status == "inactive":
            queryset = queryset.filter(is_active=False)

        # Filter by ARAMCO
        aramco = self.request.GET.get("aramco")
        if aramco == "yes":
            queryset = queryset.filter(is_aramco=True)
        elif aramco == "no":
            queryset = queryset.filter(is_aramco=False)

        return queryset.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Customers"
        context["customer_types"] = Customer.CustomerType.choices
        context["total_customers"] = Customer.objects.count()
        context["active_customers"] = Customer.objects.filter(is_active=True).count()
        context["aramco_customers"] = Customer.objects.filter(is_aramco=True).count()
        context["current_type"] = self.request.GET.get("type", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["current_aramco"] = self.request.GET.get("aramco", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class CustomerDetailView(LoginRequiredMixin, DetailView):
    """
    View customer details with tabs for contacts, rigs, wells, etc.
    """

    model = Customer
    template_name = "sales/customer_detail.html"
    context_object_name = "customer"

    def get_queryset(self):
        return Customer.objects.select_related("account_manager", "created_by").prefetch_related(
            "contacts", "rigs", "wells", "warehouses"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object
        context["page_title"] = f"Customer: {customer.name}"

        # Related data
        context["contacts"] = customer.contacts.all().order_by("-is_primary", "name")
        context["rigs"] = customer.rigs.all().order_by("code")
        context["wells"] = customer.wells.all().order_by("code")
        context["warehouses"] = customer.warehouses.all().order_by("code")

        # Statistics
        context["stats"] = {
            "total_contacts": customer.contacts.count(),
            "total_rigs": customer.rigs.filter(is_active=True).count(),
            "total_wells": customer.wells.filter(is_active=True).count(),
            "total_warehouses": customer.warehouses.filter(is_active=True).count(),
        }

        # Work orders (if relationship exists)
        if hasattr(customer, "workorder_set"):
            context["recent_work_orders"] = customer.workorder_set.select_related("drill_bit", "assigned_to").order_by(
                "-created_at"
            )[:5]
            context["stats"]["total_work_orders"] = customer.workorder_set.count()
            context["stats"]["active_work_orders"] = customer.workorder_set.filter(
                status__in=["IN_PROGRESS", "PLANNED", "RELEASED"]
            ).count()

        # DRSS requests (if relationship exists)
        if hasattr(customer, "drss_requests"):
            context["recent_drss"] = customer.drss_requests.select_related("rig", "well").order_by("-requested_date")[:5]
            context["stats"]["total_drss"] = customer.drss_requests.count()

        return context


class CustomerCreateView(ManagerRequiredMixin, CreateView):
    """
    Create a new customer.
    """

    model = Customer
    form_class = CustomerForm
    template_name = "sales/customer_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Customer"
        context["submit_text"] = "Create Customer"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        # Auto-generate code if not provided
        if not form.instance.code:
            form.instance.code = self.generate_customer_code()

        messages.success(self.request, f'Customer "{form.instance.name}" created successfully.')
        return super().form_valid(form)

    def generate_customer_code(self):
        """Generate unique customer code."""
        prefix = "CUST"
        last = Customer.objects.order_by("-id").first()
        next_num = (last.id + 1) if last else 1
        return f"{prefix}-{str(next_num).zfill(5)}"

    def get_success_url(self):
        return reverse_lazy("sales:customer_detail", kwargs={"pk": self.object.pk})


class CustomerUpdateView(ManagerRequiredMixin, UpdateView):
    """
    Update an existing customer.
    """

    model = Customer
    form_class = CustomerForm
    template_name = "sales/customer_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Customer: {self.object.name}"
        context["submit_text"] = "Update Customer"
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Customer "{form.instance.name}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:customer_detail", kwargs={"pk": self.object.pk})


# =============================================================================
# CUSTOMER CONTACT VIEWS
# =============================================================================


@login_required
def add_contact(request, customer_pk):
    """Add a contact to a customer."""
    customer = get_object_or_404(Customer, pk=customer_pk)

    if request.method == "POST":
        form = CustomerContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.customer = customer

            # If marked as primary, unmark others
            if contact.is_primary:
                customer.contacts.update(is_primary=False)

            contact.save()
            messages.success(request, f'Contact "{contact.name}" added successfully.')
            return redirect("sales:customer_detail", pk=customer.pk)
    else:
        form = CustomerContactForm()

    return render(
        request,
        "sales/contact_form.html",
        {"form": form, "customer": customer, "page_title": f"Add Contact to {customer.name}"},
    )


@login_required
def edit_contact(request, pk):
    """Edit a customer contact."""
    contact = get_object_or_404(CustomerContact, pk=pk)
    customer = contact.customer

    if request.method == "POST":
        form = CustomerContactForm(request.POST, instance=contact)
        if form.is_valid():
            contact = form.save(commit=False)

            # If marked as primary, unmark others
            if contact.is_primary:
                customer.contacts.exclude(pk=contact.pk).update(is_primary=False)

            contact.save()
            messages.success(request, f'Contact "{contact.name}" updated successfully.')
            return redirect("sales:customer_detail", pk=customer.pk)
    else:
        form = CustomerContactForm(instance=contact)

    return render(
        request,
        "sales/contact_form.html",
        {"form": form, "customer": customer, "contact": contact, "page_title": f"Edit Contact: {contact.name}"},
    )


@login_required
def delete_contact(request, pk):
    """Delete a customer contact."""
    contact = get_object_or_404(CustomerContact, pk=pk)
    customer = contact.customer

    if request.method == "POST":
        name = contact.name
        contact.delete()
        messages.success(request, f'Contact "{name}" deleted.')
        return redirect("sales:customer_detail", pk=customer.pk)

    return render(
        request,
        "sales/contact_confirm_delete.html",
        {"contact": contact, "customer": customer, "page_title": f"Delete Contact: {contact.name}"},
    )


# =============================================================================
# RIG VIEWS
# =============================================================================


class RigListView(LoginRequiredMixin, ListView):
    """
    List all rigs with search and filtering.
    """

    model = Rig
    template_name = "sales/rig_list.html"
    context_object_name = "rigs"
    paginate_by = 25

    def get_queryset(self):
        queryset = Rig.objects.select_related("customer", "contractor").prefetch_related("wells")

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(location__icontains=search)
                | Q(customer__name__icontains=search)
            )

        # Filter by customer
        customer_id = self.request.GET.get("customer")
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        # Filter by status
        status = self.request.GET.get("status")
        if status == "active":
            queryset = queryset.filter(is_active=True)
        elif status == "inactive":
            queryset = queryset.filter(is_active=False)

        return queryset.order_by("code")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Rigs"
        context["total_rigs"] = Rig.objects.count()
        context["active_rigs"] = Rig.objects.filter(is_active=True).count()
        context["customers"] = Customer.objects.filter(is_active=True).order_by("name")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class RigDetailView(LoginRequiredMixin, DetailView):
    """
    View rig details.
    """

    model = Rig
    template_name = "sales/rig_detail.html"
    context_object_name = "rig"

    def get_queryset(self):
        return Rig.objects.select_related("customer", "contractor").prefetch_related("wells", "drss_requests")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rig = self.object
        context["page_title"] = f"Rig: {rig.name}"
        context["wells"] = rig.wells.all().order_by("code")
        context["stats"] = {
            "total_wells": rig.wells.count(),
            "active_wells": rig.wells.filter(is_active=True).count(),
        }
        return context


class RigCreateView(ManagerRequiredMixin, CreateView):
    """
    Register a new rig.
    """

    model = Rig
    form_class = RigForm
    template_name = "sales/rig_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Rig"
        context["submit_text"] = "Register Rig"
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Rig "{form.instance.name}" registered successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:rig_detail", kwargs={"pk": self.object.pk})


class RigUpdateView(ManagerRequiredMixin, UpdateView):
    """
    Update an existing rig.
    """

    model = Rig
    form_class = RigForm
    template_name = "sales/rig_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Rig: {self.object.name}"
        context["submit_text"] = "Update Rig"
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Rig "{form.instance.name}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:rig_detail", kwargs={"pk": self.object.pk})


# =============================================================================
# WELL VIEWS
# =============================================================================


class WellListView(LoginRequiredMixin, ListView):
    """
    List all wells with search and filtering.
    """

    model = Well
    template_name = "sales/well_list.html"
    context_object_name = "wells"
    paginate_by = 25

    def get_queryset(self):
        queryset = Well.objects.select_related("customer", "rig")

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(field_name__icontains=search)
                | Q(customer__name__icontains=search)
            )

        # Filter by customer
        customer_id = self.request.GET.get("customer")
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        # Filter by rig
        rig_id = self.request.GET.get("rig")
        if rig_id:
            queryset = queryset.filter(rig_id=rig_id)

        # Filter by status
        status = self.request.GET.get("status")
        if status == "active":
            queryset = queryset.filter(is_active=True)
        elif status == "inactive":
            queryset = queryset.filter(is_active=False)

        return queryset.order_by("code")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Wells"
        context["total_wells"] = Well.objects.count()
        context["active_wells"] = Well.objects.filter(is_active=True).count()
        context["customers"] = Customer.objects.filter(is_active=True).order_by("name")
        context["rigs"] = Rig.objects.filter(is_active=True).order_by("code")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class WellDetailView(LoginRequiredMixin, DetailView):
    """
    View well details.
    """

    model = Well
    template_name = "sales/well_detail.html"
    context_object_name = "well"

    def get_queryset(self):
        return Well.objects.select_related("customer", "rig")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Well: {self.object.name}"
        return context


class WellCreateView(ManagerRequiredMixin, CreateView):
    """
    Register a new well.
    """

    model = Well
    form_class = WellForm
    template_name = "sales/well_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Well"
        context["submit_text"] = "Register Well"
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Well "{form.instance.name}" registered successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:well_detail", kwargs={"pk": self.object.pk})


class WellUpdateView(ManagerRequiredMixin, UpdateView):
    """
    Update an existing well.
    """

    model = Well
    form_class = WellForm
    template_name = "sales/well_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Well: {self.object.name}"
        context["submit_text"] = "Update Well"
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Well "{form.instance.name}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:well_detail", kwargs={"pk": self.object.pk})


# =============================================================================
# WAREHOUSE VIEWS
# =============================================================================


class WarehouseListView(LoginRequiredMixin, ListView):
    """
    List all warehouses with search and filtering.
    """

    model = Warehouse
    template_name = "sales/warehouse_list.html"
    context_object_name = "warehouses"
    paginate_by = 25

    def get_queryset(self):
        queryset = Warehouse.objects.select_related("customer")

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(city__icontains=search)
                | Q(customer__name__icontains=search)
            )

        # Filter by type
        warehouse_type = self.request.GET.get("type")
        if warehouse_type:
            queryset = queryset.filter(warehouse_type=warehouse_type)

        # Filter by status
        status = self.request.GET.get("status")
        if status == "active":
            queryset = queryset.filter(is_active=True)
        elif status == "inactive":
            queryset = queryset.filter(is_active=False)

        return queryset.order_by("code")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Warehouses"
        context["warehouse_types"] = Warehouse.WarehouseType.choices
        context["total_warehouses"] = Warehouse.objects.count()
        context["active_warehouses"] = Warehouse.objects.filter(is_active=True).count()
        context["search_query"] = self.request.GET.get("q", "")
        context["current_type"] = self.request.GET.get("type", "")
        context["current_status"] = self.request.GET.get("status", "")
        return context


class WarehouseDetailView(LoginRequiredMixin, DetailView):
    """
    View warehouse details.
    """

    model = Warehouse
    template_name = "sales/warehouse_detail.html"
    context_object_name = "warehouse"

    def get_queryset(self):
        return Warehouse.objects.select_related("customer")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Warehouse: {self.object.name}"
        # Placeholder for Sprint 4 inventory integration
        context["total_locations"] = 0
        context["total_stock_items"] = 0
        return context


class WarehouseCreateView(ManagerRequiredMixin, CreateView):
    """
    Create a new warehouse.
    """

    model = Warehouse
    form_class = WarehouseForm
    template_name = "sales/warehouse_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Warehouse"
        context["submit_text"] = "Create Warehouse"
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Warehouse "{form.instance.name}" created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:warehouse_detail", kwargs={"pk": self.object.pk})


class WarehouseUpdateView(ManagerRequiredMixin, UpdateView):
    """
    Update an existing warehouse.
    """

    model = Warehouse
    form_class = WarehouseForm
    template_name = "sales/warehouse_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Warehouse: {self.object.name}"
        context["submit_text"] = "Update Warehouse"
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Warehouse "{form.instance.name}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:warehouse_detail", kwargs={"pk": self.object.pk})


# =============================================================================
# EXPORT VIEWS
# =============================================================================


@login_required
def export_customers_csv(request):
    """Export customers to CSV."""
    response = HttpResponse(content_type="text/csv")
    filename = f'customers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "Code",
            "Name",
            "Name (AR)",
            "Type",
            "ARAMCO",
            "City",
            "Country",
            "Phone",
            "Email",
            "Account Manager",
            "Active",
            "Created",
        ]
    )

    queryset = Customer.objects.select_related("account_manager").order_by("name")

    for c in queryset:
        writer.writerow(
            [
                c.code,
                c.name,
                c.name_ar,
                c.get_customer_type_display(),
                "Yes" if c.is_aramco else "No",
                c.city,
                c.country,
                c.phone,
                c.email,
                c.account_manager.get_full_name() if c.account_manager else "",
                "Yes" if c.is_active else "No",
                c.created_at.strftime("%Y-%m-%d"),
            ]
        )

    return response


@login_required
def export_rigs_csv(request):
    """Export rigs to CSV."""
    response = HttpResponse(content_type="text/csv")
    filename = f'rigs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(["Code", "Name", "Customer", "Contractor", "Type", "Location", "Latitude", "Longitude", "Active"])

    queryset = Rig.objects.select_related("customer", "contractor").order_by("code")

    for r in queryset:
        writer.writerow(
            [
                r.code,
                r.name,
                r.customer.name if r.customer else "",
                r.contractor.name if r.contractor else "",
                r.rig_type,
                r.location,
                r.latitude or "",
                r.longitude or "",
                "Yes" if r.is_active else "No",
            ]
        )

    return response


# =============================================================================
# SALES ORDER VIEWS
# =============================================================================


class SalesOrderListView(LoginRequiredMixin, ListView):
    """List all sales orders with search and filtering."""

    model = SalesOrder
    template_name = "sales/salesorder_list.html"
    context_object_name = "orders"
    paginate_by = 25

    def get_queryset(self):
        queryset = SalesOrder.objects.select_related("customer", "sales_rep", "approved_by")

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) | Q(customer__name__icontains=search)
            )

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-order_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sales Orders"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class SalesOrderDetailView(LoginRequiredMixin, DetailView):
    """View sales order details with order lines."""

    model = SalesOrder
    template_name = "sales/salesorder_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return SalesOrder.objects.select_related(
            "customer", "sales_rep", "approved_by"
        ).prefetch_related("lines__drill_bit")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Sales Order: {self.object.order_number}"
        context["lines"] = self.object.lines.all()
        return context


class SalesOrderCreateView(LoginRequiredMixin, CreateView):
    """Create a new sales order."""

    model = SalesOrder
    form_class = SalesOrderForm
    template_name = "sales/salesorder_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Sales Order"
        context["submit_text"] = "Create Order"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Sales order '{form.instance.order_number}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:salesorder_detail", kwargs={"pk": self.object.pk})


class SalesOrderUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing sales order."""

    model = SalesOrder
    form_class = SalesOrderForm
    template_name = "sales/salesorder_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Sales Order: {self.object.order_number}"
        context["submit_text"] = "Update Order"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Sales order '{form.instance.order_number}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:salesorder_detail", kwargs={"pk": self.object.pk})


class SalesOrderDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a sales order."""

    model = SalesOrder
    template_name = "sales/salesorder_confirm_delete.html"
    success_url = reverse_lazy("sales:salesorder_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Sales Order: {self.object.order_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Sales order '{self.object.order_number}' deleted.")
        return super().form_valid(form)


# =============================================================================
# SERVICE SITE VIEWS
# =============================================================================


class ServiceSiteListView(LoginRequiredMixin, ListView):
    """List all service sites with search and filtering."""

    model = ServiceSite
    template_name = "sales/servicesite_list.html"
    context_object_name = "sites"
    paginate_by = 25

    def get_queryset(self):
        queryset = ServiceSite.objects.select_related("customer")

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(site_number__icontains=search)
                | Q(site_name__icontains=search)
                | Q(rig_name__icontains=search)
            )

        site_type = self.request.GET.get("site_type")
        if site_type:
            queryset = queryset.filter(site_type=site_type)

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Service Sites"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class ServiceSiteDetailView(LoginRequiredMixin, DetailView):
    """View service site details."""

    model = ServiceSite
    template_name = "sales/servicesite_detail.html"
    context_object_name = "site"

    def get_queryset(self):
        return ServiceSite.objects.select_related("customer")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Service Site: {self.object.site_name}"
        return context


class ServiceSiteCreateView(LoginRequiredMixin, CreateView):
    """Create a new service site."""

    model = ServiceSite
    form_class = ServiceSiteForm
    template_name = "sales/servicesite_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Service Site"
        context["submit_text"] = "Create Site"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Service site '{form.instance.site_name}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:servicesite_detail", kwargs={"pk": self.object.pk})


class ServiceSiteUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing service site."""

    model = ServiceSite
    form_class = ServiceSiteForm
    template_name = "sales/servicesite_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Service Site: {self.object.site_name}"
        context["submit_text"] = "Update Site"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Service site '{form.instance.site_name}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:servicesite_detail", kwargs={"pk": self.object.pk})


class ServiceSiteDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a service site."""

    model = ServiceSite
    template_name = "sales/servicesite_confirm_delete.html"
    success_url = reverse_lazy("sales:servicesite_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Service Site: {self.object.site_name}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Service site '{self.object.site_name}' deleted.")
        return super().form_valid(form)


# =============================================================================
# FIELD TECHNICIAN VIEWS
# =============================================================================


class FieldTechnicianListView(LoginRequiredMixin, ListView):
    """List all field technicians with search and filtering."""

    model = FieldTechnician
    template_name = "sales/fieldtechnician_list.html"
    context_object_name = "technicians"
    paginate_by = 25

    def get_queryset(self):
        queryset = FieldTechnician.objects.select_related("employee")

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(tech_id__icontains=search)
                | Q(employee__first_name__icontains=search)
                | Q(employee__last_name__icontains=search)
            )

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("tech_id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Field Technicians"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FieldTechnicianDetailView(LoginRequiredMixin, DetailView):
    """View field technician details."""

    model = FieldTechnician
    template_name = "sales/fieldtechnician_detail.html"
    context_object_name = "technician"

    def get_queryset(self):
        return FieldTechnician.objects.select_related("employee")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Field Technician: {self.object.tech_id}"
        return context


class FieldTechnicianCreateView(LoginRequiredMixin, CreateView):
    """Create a new field technician."""

    model = FieldTechnician
    form_class = FieldTechnicianForm
    template_name = "sales/fieldtechnician_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Field Technician"
        context["submit_text"] = "Create Technician"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Field technician '{form.instance.tech_id}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldtechnician_detail", kwargs={"pk": self.object.pk})


class FieldTechnicianUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing field technician."""

    model = FieldTechnician
    form_class = FieldTechnicianForm
    template_name = "sales/fieldtechnician_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Field Technician: {self.object.tech_id}"
        context["submit_text"] = "Update Technician"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Field technician '{form.instance.tech_id}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldtechnician_detail", kwargs={"pk": self.object.pk})


class FieldTechnicianDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a field technician."""

    model = FieldTechnician
    template_name = "sales/fieldtechnician_confirm_delete.html"
    success_url = reverse_lazy("sales:fieldtechnician_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Field Technician: {self.object.tech_id}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Field technician '{self.object.tech_id}' deleted.")
        return super().form_valid(form)


# =============================================================================
# FIELD SERVICE REQUEST VIEWS
# =============================================================================


class FieldServiceRequestListView(LoginRequiredMixin, ListView):
    """List all field service requests with search and filtering."""

    model = FieldServiceRequest
    template_name = "sales/fieldservicerequest_list.html"
    context_object_name = "requests"
    paginate_by = 25

    def get_queryset(self):
        queryset = FieldServiceRequest.objects.select_related(
            "customer", "service_site", "assigned_technician", "approved_by"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(request_number__icontains=search) | Q(customer__name__icontains=search)
            )

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset.order_by("-requested_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Field Service Requests"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FieldServiceRequestDetailView(LoginRequiredMixin, DetailView):
    """View field service request details."""

    model = FieldServiceRequest
    template_name = "sales/fieldservicerequest_detail.html"
    context_object_name = "request"

    def get_queryset(self):
        return FieldServiceRequest.objects.select_related(
            "customer", "service_site", "assigned_technician", "approved_by", "work_order"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Service Request: {self.object.request_number}"
        return context


class FieldServiceRequestCreateView(LoginRequiredMixin, CreateView):
    """Create a new field service request."""

    model = FieldServiceRequest
    form_class = FieldServiceRequestForm
    template_name = "sales/fieldservicerequest_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Service Request"
        context["submit_text"] = "Create Request"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Service request '{form.instance.request_number}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldservicerequest_detail", kwargs={"pk": self.object.pk})


class FieldServiceRequestUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing field service request."""

    model = FieldServiceRequest
    form_class = FieldServiceRequestForm
    template_name = "sales/fieldservicerequest_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Service Request: {self.object.request_number}"
        context["submit_text"] = "Update Request"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Service request '{form.instance.request_number}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldservicerequest_detail", kwargs={"pk": self.object.pk})


class FieldServiceRequestDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a field service request."""

    model = FieldServiceRequest
    template_name = "sales/fieldservicerequest_confirm_delete.html"
    success_url = reverse_lazy("sales:fieldservicerequest_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Service Request: {self.object.request_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Service request '{self.object.request_number}' deleted.")
        return super().form_valid(form)


# =============================================================================
# SERVICE SCHEDULE VIEWS
# =============================================================================


class ServiceScheduleListView(LoginRequiredMixin, ListView):
    """List all service schedules with search and filtering."""

    model = ServiceSchedule
    template_name = "sales/serviceschedule_list.html"
    context_object_name = "schedules"
    paginate_by = 25

    def get_queryset(self):
        queryset = ServiceSchedule.objects.select_related(
            "service_request", "technician", "service_request__customer"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(schedule_number__icontains=search)
                | Q(service_request__request_number__icontains=search)
            )

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-scheduled_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Service Schedules"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class ServiceScheduleDetailView(LoginRequiredMixin, DetailView):
    """View service schedule details."""

    model = ServiceSchedule
    template_name = "sales/serviceschedule_detail.html"
    context_object_name = "schedule"

    def get_queryset(self):
        return ServiceSchedule.objects.select_related(
            "service_request", "technician", "service_request__customer"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Service Schedule: {self.object.schedule_number}"
        return context


class ServiceScheduleCreateView(LoginRequiredMixin, CreateView):
    """Create a new service schedule."""

    model = ServiceSchedule
    form_class = ServiceScheduleForm
    template_name = "sales/serviceschedule_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Service Schedule"
        context["submit_text"] = "Create Schedule"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Service schedule '{form.instance.schedule_number}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:serviceschedule_detail", kwargs={"pk": self.object.pk})


class ServiceScheduleUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing service schedule."""

    model = ServiceSchedule
    form_class = ServiceScheduleForm
    template_name = "sales/serviceschedule_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Service Schedule: {self.object.schedule_number}"
        context["submit_text"] = "Update Schedule"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Service schedule '{form.instance.schedule_number}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:serviceschedule_detail", kwargs={"pk": self.object.pk})


class ServiceScheduleDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a service schedule."""

    model = ServiceSchedule
    template_name = "sales/serviceschedule_confirm_delete.html"
    success_url = reverse_lazy("sales:serviceschedule_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Service Schedule: {self.object.schedule_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Service schedule '{self.object.schedule_number}' deleted.")
        return super().form_valid(form)


# =============================================================================
# SITE VISIT VIEWS
# =============================================================================


class SiteVisitListView(LoginRequiredMixin, ListView):
    """List all site visits with search and filtering."""

    model = SiteVisit
    template_name = "sales/sitevisit_list.html"
    context_object_name = "visits"
    paginate_by = 25

    def get_queryset(self):
        queryset = SiteVisit.objects.select_related(
            "service_request", "technician", "service_site"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(visit_number__icontains=search)
                | Q(service_request__request_number__icontains=search)
            )

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-check_in_time")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Site Visits"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class SiteVisitDetailView(LoginRequiredMixin, DetailView):
    """View site visit details."""

    model = SiteVisit
    template_name = "sales/sitevisit_detail.html"
    context_object_name = "visit"

    def get_queryset(self):
        return SiteVisit.objects.select_related(
            "service_request", "technician", "service_site"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Site Visit: {self.object.visit_number}"
        return context


class SiteVisitCreateView(LoginRequiredMixin, CreateView):
    """Create a new site visit."""

    model = SiteVisit
    form_class = SiteVisitForm
    template_name = "sales/sitevisit_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Site Visit"
        context["submit_text"] = "Create Visit"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Site visit '{form.instance.visit_number}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:sitevisit_detail", kwargs={"pk": self.object.pk})


class SiteVisitUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing site visit."""

    model = SiteVisit
    form_class = SiteVisitForm
    template_name = "sales/sitevisit_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Site Visit: {self.object.visit_number}"
        context["submit_text"] = "Update Visit"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Site visit '{form.instance.visit_number}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:sitevisit_detail", kwargs={"pk": self.object.pk})


class SiteVisitDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a site visit."""

    model = SiteVisit
    template_name = "sales/sitevisit_confirm_delete.html"
    success_url = reverse_lazy("sales:sitevisit_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Site Visit: {self.object.visit_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Site visit '{self.object.visit_number}' deleted.")
        return super().form_valid(form)


# =============================================================================
# SERVICE REPORT VIEWS
# =============================================================================


class ServiceReportListView(LoginRequiredMixin, ListView):
    """List all service reports with search and filtering."""

    model = ServiceReport
    template_name = "sales/servicereport_list.html"
    context_object_name = "reports"
    paginate_by = 25

    def get_queryset(self):
        queryset = ServiceReport.objects.select_related(
            "service_request", "site_visit", "prepared_by"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(report_number__icontains=search)
                | Q(service_request__request_number__icontains=search)
            )

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-report_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Service Reports"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class ServiceReportDetailView(LoginRequiredMixin, DetailView):
    """View service report details."""

    model = ServiceReport
    template_name = "sales/servicereport_detail.html"
    context_object_name = "report"

    def get_queryset(self):
        return ServiceReport.objects.select_related(
            "service_request", "site_visit", "prepared_by", "approved_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Service Report: {self.object.report_number}"
        return context


class ServiceReportCreateView(LoginRequiredMixin, CreateView):
    """Create a new service report."""

    model = ServiceReport
    form_class = ServiceReportForm
    template_name = "sales/servicereport_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Service Report"
        context["submit_text"] = "Create Report"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.prepared_by = self.request.user
        messages.success(self.request, f"Service report '{form.instance.report_number}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:servicereport_detail", kwargs={"pk": self.object.pk})


class ServiceReportUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing service report."""

    model = ServiceReport
    form_class = ServiceReportForm
    template_name = "sales/servicereport_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Service Report: {self.object.report_number}"
        context["submit_text"] = "Update Report"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Service report '{form.instance.report_number}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:servicereport_detail", kwargs={"pk": self.object.pk})


class ServiceReportDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a service report."""

    model = ServiceReport
    template_name = "sales/servicereport_confirm_delete.html"
    success_url = reverse_lazy("sales:servicereport_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Service Report: {self.object.report_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Service report '{self.object.report_number}' deleted.")
        return super().form_valid(form)


# =============================================================================
# FIELD DRILL STRING RUN VIEWS
# =============================================================================


class FieldDrillStringRunListView(LoginRequiredMixin, ListView):
    """List all field drill string runs with search and filtering."""

    model = FieldDrillStringRun
    template_name = "sales/fielddrillstringrun_list.html"
    context_object_name = "runs"
    paginate_by = 25

    def get_queryset(self):
        queryset = FieldDrillStringRun.objects.select_related(
            "site_visit", "drill_bit", "service_site"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(run_number__icontains=search)
                | Q(drill_bit__serial_number__icontains=search)
            )

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-start_time")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Field Drill String Runs"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FieldDrillStringRunDetailView(LoginRequiredMixin, DetailView):
    """View field drill string run details."""

    model = FieldDrillStringRun
    template_name = "sales/fielddrillstringrun_detail.html"
    context_object_name = "run"

    def get_queryset(self):
        return FieldDrillStringRun.objects.select_related(
            "site_visit", "drill_bit", "service_site"
        ).prefetch_related("field_run_data")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Drill String Run: {self.object.run_number}"
        return context


class FieldDrillStringRunCreateView(LoginRequiredMixin, CreateView):
    """Create a new field drill string run."""

    model = FieldDrillStringRun
    form_class = FieldDrillStringRunForm
    template_name = "sales/fielddrillstringrun_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Drill String Run"
        context["submit_text"] = "Create Run"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Drill string run '{form.instance.run_number}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fielddrillstringrun_detail", kwargs={"pk": self.object.pk})


class FieldDrillStringRunUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing field drill string run."""

    model = FieldDrillStringRun
    form_class = FieldDrillStringRunForm
    template_name = "sales/fielddrillstringrun_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Drill String Run: {self.object.run_number}"
        context["submit_text"] = "Update Run"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Drill string run '{form.instance.run_number}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fielddrillstringrun_detail", kwargs={"pk": self.object.pk})


class FieldDrillStringRunDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a field drill string run."""

    model = FieldDrillStringRun
    template_name = "sales/fielddrillstringrun_confirm_delete.html"
    success_url = reverse_lazy("sales:fielddrillstringrun_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Drill String Run: {self.object.run_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Drill string run '{self.object.run_number}' deleted.")
        return super().form_valid(form)


# =============================================================================
# FIELD RUN DATA VIEWS
# =============================================================================


class FieldRunDataListView(LoginRequiredMixin, ListView):
    """List all field run data with search and filtering."""

    model = FieldRunData
    template_name = "sales/fieldrundata_list.html"
    context_object_name = "data_records"
    paginate_by = 25

    def get_queryset(self):
        queryset = FieldRunData.objects.select_related("drill_string_run", "drill_string_run__drill_bit")

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(drill_string_run__run_number__icontains=search)
            )

        return queryset.order_by("-recorded_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Field Run Data"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FieldRunDataDetailView(LoginRequiredMixin, DetailView):
    """View field run data details."""

    model = FieldRunData
    template_name = "sales/fieldrundata_detail.html"
    context_object_name = "data"

    def get_queryset(self):
        return FieldRunData.objects.select_related("drill_string_run", "drill_string_run__drill_bit")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Field Run Data: {self.object.pk}"
        return context


class FieldRunDataCreateView(LoginRequiredMixin, CreateView):
    """Create new field run data."""

    model = FieldRunData
    form_class = FieldRunDataForm
    template_name = "sales/fieldrundata_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Field Run Data"
        context["submit_text"] = "Create Data Record"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Field run data created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldrundata_detail", kwargs={"pk": self.object.pk})


class FieldRunDataUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing field run data."""

    model = FieldRunData
    form_class = FieldRunDataForm
    template_name = "sales/fieldrundata_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Field Run Data: {self.object.pk}"
        context["submit_text"] = "Update Data Record"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Field run data updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldrundata_detail", kwargs={"pk": self.object.pk})


class FieldRunDataDeleteView(LoginRequiredMixin, DeleteView):
    """Delete field run data."""

    model = FieldRunData
    template_name = "sales/fieldrundata_confirm_delete.html"
    success_url = reverse_lazy("sales:fieldrundata_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Field Run Data: {self.object.pk}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Field run data deleted.")
        return super().form_valid(form)


# =============================================================================
# FIELD PERFORMANCE LOG VIEWS
# =============================================================================


class FieldPerformanceLogListView(LoginRequiredMixin, ListView):
    """List all field performance logs with search and filtering."""

    model = FieldPerformanceLog
    template_name = "sales/fieldperformancelog_list.html"
    context_object_name = "logs"
    paginate_by = 25

    def get_queryset(self):
        queryset = FieldPerformanceLog.objects.select_related(
            "drill_string_run", "technician"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(drill_string_run__run_number__icontains=search)
            )

        return queryset.order_by("-log_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Performance Logs"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FieldPerformanceLogDetailView(LoginRequiredMixin, DetailView):
    """View field performance log details."""

    model = FieldPerformanceLog
    template_name = "sales/fieldperformancelog_detail.html"
    context_object_name = "log"

    def get_queryset(self):
        return FieldPerformanceLog.objects.select_related(
            "drill_string_run", "technician"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Performance Log: {self.object.pk}"
        return context


class FieldPerformanceLogCreateView(LoginRequiredMixin, CreateView):
    """Create a new field performance log."""

    model = FieldPerformanceLog
    form_class = FieldPerformanceLogForm
    template_name = "sales/fieldperformancelog_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Performance Log"
        context["submit_text"] = "Create Log"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Performance log created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldperformancelog_detail", kwargs={"pk": self.object.pk})


class FieldPerformanceLogUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing field performance log."""

    model = FieldPerformanceLog
    form_class = FieldPerformanceLogForm
    template_name = "sales/fieldperformancelog_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Performance Log: {self.object.pk}"
        context["submit_text"] = "Update Log"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Performance log updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldperformancelog_detail", kwargs={"pk": self.object.pk})


class FieldPerformanceLogDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a field performance log."""

    model = FieldPerformanceLog
    template_name = "sales/fieldperformancelog_confirm_delete.html"
    success_url = reverse_lazy("sales:fieldperformancelog_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Performance Log: {self.object.pk}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Performance log deleted.")
        return super().form_valid(form)


# =============================================================================
# FIELD INSPECTION VIEWS
# =============================================================================


class FieldInspectionListView(LoginRequiredMixin, ListView):
    """List all field inspections with search and filtering."""

    model = FieldInspection
    template_name = "sales/fieldinspection_list.html"
    context_object_name = "inspections"
    paginate_by = 25

    def get_queryset(self):
        queryset = FieldInspection.objects.select_related(
            "drill_string_run", "inspector"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(inspection_number__icontains=search)
                | Q(serial_number__icontains=search)
            )

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-inspection_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Field Inspections"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FieldInspectionDetailView(LoginRequiredMixin, DetailView):
    """View field inspection details."""

    model = FieldInspection
    template_name = "sales/fieldinspection_detail.html"
    context_object_name = "inspection"

    def get_queryset(self):
        return FieldInspection.objects.select_related(
            "drill_string_run", "inspector"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Inspection: {self.object.inspection_number}"
        return context


class FieldInspectionCreateView(LoginRequiredMixin, CreateView):
    """Create a new field inspection."""

    model = FieldInspection
    form_class = FieldInspectionForm
    template_name = "sales/fieldinspection_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Inspection"
        context["submit_text"] = "Create Inspection"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Inspection '{form.instance.inspection_number}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldinspection_detail", kwargs={"pk": self.object.pk})


class FieldInspectionUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing field inspection."""

    model = FieldInspection
    form_class = FieldInspectionForm
    template_name = "sales/fieldinspection_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Inspection: {self.object.inspection_number}"
        context["submit_text"] = "Update Inspection"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Inspection '{form.instance.inspection_number}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldinspection_detail", kwargs={"pk": self.object.pk})


class FieldInspectionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a field inspection."""

    model = FieldInspection
    template_name = "sales/fieldinspection_confirm_delete.html"
    success_url = reverse_lazy("sales:fieldinspection_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Inspection: {self.object.inspection_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Inspection '{self.object.inspection_number}' deleted.")
        return super().form_valid(form)


# =============================================================================
# RUN HOURS VIEWS
# =============================================================================


class RunHoursListView(LoginRequiredMixin, ListView):
    """List all run hours records with search and filtering."""

    model = RunHours
    template_name = "sales/runhours_list.html"
    context_object_name = "run_hours"
    paginate_by = 50

    def get_queryset(self):
        queryset = RunHours.objects.select_related(
            "drill_string_run", "technician"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(drill_string_run__run_number__icontains=search)
            )

        return queryset.order_by("-record_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Run Hours"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class RunHoursDetailView(LoginRequiredMixin, DetailView):
    """View run hours details."""

    model = RunHours
    template_name = "sales/runhours_detail.html"
    context_object_name = "run_hour"

    def get_queryset(self):
        return RunHours.objects.select_related(
            "drill_string_run", "technician", "verified_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Run Hours: {self.object.pk}"
        return context


class RunHoursCreateView(LoginRequiredMixin, CreateView):
    """Create a new run hours record."""

    model = RunHours
    form_class = RunHoursForm
    template_name = "sales/runhours_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Run Hours"
        context["submit_text"] = "Create Record"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Run hours record created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:runhours_detail", kwargs={"pk": self.object.pk})


class RunHoursUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing run hours record."""

    model = RunHours
    form_class = RunHoursForm
    template_name = "sales/runhours_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Run Hours: {self.object.pk}"
        context["submit_text"] = "Update Record"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Run hours record updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:runhours_detail", kwargs={"pk": self.object.pk})


class RunHoursDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a run hours record."""

    model = RunHours
    template_name = "sales/runhours_confirm_delete.html"
    success_url = reverse_lazy("sales:runhours_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Run Hours: {self.object.pk}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Run hours record deleted.")
        return super().form_valid(form)


# =============================================================================
# FIELD INCIDENT VIEWS
# =============================================================================


class FieldIncidentListView(LoginRequiredMixin, ListView):
    """List all field incidents with search and filtering."""

    model = FieldIncident
    template_name = "sales/fieldincident_list.html"
    context_object_name = "incidents"
    paginate_by = 25

    def get_queryset(self):
        queryset = FieldIncident.objects.select_related(
            "service_site", "technician", "reported_by"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(incident_number__icontains=search)
            )

        incident_type = self.request.GET.get("incident_type")
        if incident_type:
            queryset = queryset.filter(incident_type=incident_type)

        severity = self.request.GET.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-incident_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Field Incidents"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FieldIncidentDetailView(LoginRequiredMixin, DetailView):
    """View field incident details."""

    model = FieldIncident
    template_name = "sales/fieldincident_detail.html"
    context_object_name = "incident"

    def get_queryset(self):
        return FieldIncident.objects.select_related(
            "service_site", "technician", "reported_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Incident: {self.object.incident_number}"
        return context


class FieldIncidentCreateView(LoginRequiredMixin, CreateView):
    """Create a new field incident."""

    model = FieldIncident
    form_class = FieldIncidentForm
    template_name = "sales/fieldincident_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Incident"
        context["submit_text"] = "Create Incident"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Incident '{form.instance.incident_number}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldincident_detail", kwargs={"pk": self.object.pk})


class FieldIncidentUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing field incident."""

    model = FieldIncident
    form_class = FieldIncidentForm
    template_name = "sales/fieldincident_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Incident: {self.object.incident_number}"
        context["submit_text"] = "Update Incident"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Incident '{form.instance.incident_number}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldincident_detail", kwargs={"pk": self.object.pk})


class FieldIncidentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a field incident."""

    model = FieldIncident
    template_name = "sales/fieldincident_confirm_delete.html"
    success_url = reverse_lazy("sales:fieldincident_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Incident: {self.object.incident_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Incident '{self.object.incident_number}' deleted.")
        return super().form_valid(form)


# =============================================================================
# FIELD DATA ENTRY VIEWS
# =============================================================================


class FieldDataEntryListView(LoginRequiredMixin, ListView):
    """List all field data entries with search and filtering."""

    model = FieldDataEntry
    template_name = "sales/fielddataentry_list.html"
    context_object_name = "entries"
    paginate_by = 50

    def get_queryset(self):
        queryset = FieldDataEntry.objects.select_related(
            "drill_string_run", "recorded_by"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(entry_number__icontains=search)
                | Q(drill_string_run__run_number__icontains=search)
            )

        return queryset.order_by("-entry_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Field Data Entries"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FieldDataEntryDetailView(LoginRequiredMixin, DetailView):
    """View field data entry details."""

    model = FieldDataEntry
    template_name = "sales/fielddataentry_detail.html"
    context_object_name = "entry"

    def get_queryset(self):
        return FieldDataEntry.objects.select_related(
            "drill_string_run", "recorded_by", "verified_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Data Entry: {self.object.entry_number}"
        return context


class FieldDataEntryCreateView(LoginRequiredMixin, CreateView):
    """Create a new field data entry."""

    model = FieldDataEntry
    form_class = FieldDataEntryForm
    template_name = "sales/fielddataentry_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Data Entry"
        context["submit_text"] = "Create Entry"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Data entry '{form.instance.entry_number}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fielddataentry_detail", kwargs={"pk": self.object.pk})


class FieldDataEntryUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing field data entry."""

    model = FieldDataEntry
    form_class = FieldDataEntryForm
    template_name = "sales/fielddataentry_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Data Entry: {self.object.entry_number}"
        context["submit_text"] = "Update Entry"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Data entry '{form.instance.entry_number}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fielddataentry_detail", kwargs={"pk": self.object.pk})


class FieldDataEntryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a field data entry."""

    model = FieldDataEntry
    template_name = "sales/fielddataentry_confirm_delete.html"
    success_url = reverse_lazy("sales:fielddataentry_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Data Entry: {self.object.entry_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Data entry '{self.object.entry_number}' deleted.")
        return super().form_valid(form)


# =============================================================================
# FIELD PHOTO VIEWS
# =============================================================================


class FieldPhotoListView(LoginRequiredMixin, ListView):
    """List all field photos with search and filtering."""

    model = FieldPhoto
    template_name = "sales/fieldphoto_list.html"
    context_object_name = "photos"
    paginate_by = 24

    def get_queryset(self):
        queryset = FieldPhoto.objects.select_related(
            "drill_string_run", "service_site", "taken_by"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(caption__icontains=search)
            )

        photo_type = self.request.GET.get("photo_type")
        if photo_type:
            queryset = queryset.filter(photo_type=photo_type)

        return queryset.order_by("-taken_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Field Photos"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FieldPhotoDetailView(LoginRequiredMixin, DetailView):
    """View field photo details."""

    model = FieldPhoto
    template_name = "sales/fieldphoto_detail.html"
    context_object_name = "photo"

    def get_queryset(self):
        return FieldPhoto.objects.select_related(
            "drill_string_run", "service_site", "taken_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Photo: {self.object.title}"
        return context


class FieldPhotoCreateView(LoginRequiredMixin, CreateView):
    """Upload a new field photo."""

    model = FieldPhoto
    form_class = FieldPhotoForm
    template_name = "sales/fieldphoto_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Upload Photo"
        context["submit_text"] = "Upload"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Photo '{form.instance.title}' uploaded.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldphoto_detail", kwargs={"pk": self.object.pk})


class FieldPhotoUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing field photo."""

    model = FieldPhoto
    form_class = FieldPhotoForm
    template_name = "sales/fieldphoto_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Photo: {self.object.title}"
        context["submit_text"] = "Update"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Photo '{form.instance.title}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldphoto_detail", kwargs={"pk": self.object.pk})


class FieldPhotoDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a field photo."""

    model = FieldPhoto
    template_name = "sales/fieldphoto_confirm_delete.html"
    success_url = reverse_lazy("sales:fieldphoto_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Photo: {self.object.title}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Photo '{self.object.title}' deleted.")
        return super().form_valid(form)


# =============================================================================
# FIELD DOCUMENT VIEWS
# =============================================================================


class FieldDocumentListView(LoginRequiredMixin, ListView):
    """List all field documents with search and filtering."""

    model = FieldDocument
    template_name = "sales/fielddocument_list.html"
    context_object_name = "documents"
    paginate_by = 25

    def get_queryset(self):
        queryset = FieldDocument.objects.select_related(
            "drill_string_run", "service_site", "uploaded_by"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
            )

        document_type = self.request.GET.get("document_type")
        if document_type:
            queryset = queryset.filter(document_type=document_type)

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-document_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Field Documents"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FieldDocumentDetailView(LoginRequiredMixin, DetailView):
    """View field document details."""

    model = FieldDocument
    template_name = "sales/fielddocument_detail.html"
    context_object_name = "document"

    def get_queryset(self):
        return FieldDocument.objects.select_related(
            "drill_string_run", "service_site", "uploaded_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Document: {self.object.title}"
        return context


class FieldDocumentCreateView(LoginRequiredMixin, CreateView):
    """Upload a new field document."""

    model = FieldDocument
    form_class = FieldDocumentForm
    template_name = "sales/fielddocument_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Upload Document"
        context["submit_text"] = "Upload"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Document '{form.instance.title}' uploaded.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fielddocument_detail", kwargs={"pk": self.object.pk})


class FieldDocumentUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing field document."""

    model = FieldDocument
    form_class = FieldDocumentForm
    template_name = "sales/fielddocument_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Document: {self.object.title}"
        context["submit_text"] = "Update"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Document '{form.instance.title}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fielddocument_detail", kwargs={"pk": self.object.pk})


class FieldDocumentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a field document."""

    model = FieldDocument
    template_name = "sales/fielddocument_confirm_delete.html"
    success_url = reverse_lazy("sales:fielddocument_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Document: {self.object.title}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Document '{self.object.title}' deleted.")
        return super().form_valid(form)


# =============================================================================
# GPS LOCATION VIEWS
# =============================================================================


class GPSLocationListView(LoginRequiredMixin, ListView):
    """List all GPS locations with search and filtering."""

    model = GPSLocation
    template_name = "sales/gpslocation_list.html"
    context_object_name = "locations"
    paginate_by = 50

    def get_queryset(self):
        queryset = GPSLocation.objects.select_related(
            "technician", "service_site"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(address__icontains=search)
            )

        return queryset.order_by("-recorded_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "GPS Locations"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class GPSLocationDetailView(LoginRequiredMixin, DetailView):
    """View GPS location details."""

    model = GPSLocation
    template_name = "sales/gpslocation_detail.html"
    context_object_name = "location"

    def get_queryset(self):
        return GPSLocation.objects.select_related(
            "technician", "service_site"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"GPS Location: {self.object.pk}"
        return context


class GPSLocationCreateView(LoginRequiredMixin, CreateView):
    """Create a new GPS location record."""

    model = GPSLocation
    form_class = GPSLocationForm
    template_name = "sales/gpslocation_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New GPS Location"
        context["submit_text"] = "Record Location"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "GPS location recorded.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:gpslocation_detail", kwargs={"pk": self.object.pk})


class GPSLocationUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing GPS location record."""

    model = GPSLocation
    form_class = GPSLocationForm
    template_name = "sales/gpslocation_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit GPS Location: {self.object.pk}"
        context["submit_text"] = "Update Location"
        return context

    def form_valid(self, form):
        messages.success(self.request, "GPS location updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:gpslocation_detail", kwargs={"pk": self.object.pk})


class GPSLocationDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a GPS location record."""

    model = GPSLocation
    template_name = "sales/gpslocation_confirm_delete.html"
    success_url = reverse_lazy("sales:gpslocation_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete GPS Location: {self.object.pk}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "GPS location deleted.")
        return super().form_valid(form)


# =============================================================================
# FIELD WORK ORDER VIEWS
# =============================================================================


class FieldWorkOrderListView(LoginRequiredMixin, ListView):
    """List all field work orders with search and filtering."""

    model = FieldWorkOrder
    template_name = "sales/fieldworkorder_list.html"
    context_object_name = "work_orders"
    paginate_by = 25

    def get_queryset(self):
        queryset = FieldWorkOrder.objects.select_related(
            "service_request", "service_site", "assigned_technician"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(work_order_number__icontains=search)
            )

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset.order_by("-scheduled_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Field Work Orders"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FieldWorkOrderDetailView(LoginRequiredMixin, DetailView):
    """View field work order details."""

    model = FieldWorkOrder
    template_name = "sales/fieldworkorder_detail.html"
    context_object_name = "work_order"

    def get_queryset(self):
        return FieldWorkOrder.objects.select_related(
            "service_request", "service_site", "assigned_technician"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Work Order: {self.object.work_order_number}"
        return context


class FieldWorkOrderCreateView(LoginRequiredMixin, CreateView):
    """Create a new field work order."""

    model = FieldWorkOrder
    form_class = FieldWorkOrderForm
    template_name = "sales/fieldworkorder_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Work Order"
        context["submit_text"] = "Create Work Order"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Work order '{form.instance.work_order_number}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldworkorder_detail", kwargs={"pk": self.object.pk})


class FieldWorkOrderUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing field work order."""

    model = FieldWorkOrder
    form_class = FieldWorkOrderForm
    template_name = "sales/fieldworkorder_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Work Order: {self.object.work_order_number}"
        context["submit_text"] = "Update Work Order"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Work order '{form.instance.work_order_number}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldworkorder_detail", kwargs={"pk": self.object.pk})


class FieldWorkOrderDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a field work order."""

    model = FieldWorkOrder
    template_name = "sales/fieldworkorder_confirm_delete.html"
    success_url = reverse_lazy("sales:fieldworkorder_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Work Order: {self.object.work_order_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Work order '{self.object.work_order_number}' deleted.")
        return super().form_valid(form)


# =============================================================================
# FIELD ASSET ASSIGNMENT VIEWS
# =============================================================================


class FieldAssetAssignmentListView(LoginRequiredMixin, ListView):
    """List all field asset assignments with search and filtering."""

    model = FieldAssetAssignment
    template_name = "sales/fieldassetassignment_list.html"
    context_object_name = "assignments"
    paginate_by = 25

    def get_queryset(self):
        queryset = FieldAssetAssignment.objects.select_related(
            "drill_bit", "service_site", "technician", "assigned_by"
        )

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(assignment_number__icontains=search)
            )

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-assignment_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Asset Assignments"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FieldAssetAssignmentDetailView(LoginRequiredMixin, DetailView):
    """View field asset assignment details."""

    model = FieldAssetAssignment
    template_name = "sales/fieldassetassignment_detail.html"
    context_object_name = "assignment"

    def get_queryset(self):
        return FieldAssetAssignment.objects.select_related(
            "drill_bit", "service_site", "technician", "assigned_by", "returned_to"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Assignment: {self.object.assignment_number}"
        return context


class FieldAssetAssignmentCreateView(LoginRequiredMixin, CreateView):
    """Create a new field asset assignment."""

    model = FieldAssetAssignment
    form_class = FieldAssetAssignmentForm
    template_name = "sales/fieldassetassignment_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Asset Assignment"
        context["submit_text"] = "Create Assignment"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Assignment '{form.instance.assignment_number}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldassetassignment_detail", kwargs={"pk": self.object.pk})


class FieldAssetAssignmentUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing field asset assignment."""

    model = FieldAssetAssignment
    form_class = FieldAssetAssignmentForm
    template_name = "sales/fieldassetassignment_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Assignment: {self.object.assignment_number}"
        context["submit_text"] = "Update Assignment"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Assignment '{form.instance.assignment_number}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("sales:fieldassetassignment_detail", kwargs={"pk": self.object.pk})


class FieldAssetAssignmentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a field asset assignment."""

    model = FieldAssetAssignment
    template_name = "sales/fieldassetassignment_confirm_delete.html"
    success_url = reverse_lazy("sales:fieldassetassignment_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Assignment: {self.object.assignment_number}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Assignment '{self.object.assignment_number}' deleted.")
        return super().form_valid(form)
