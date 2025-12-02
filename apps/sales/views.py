"""
ARDT FMS - Sales Views
Version: 5.4 - Sprint 2

Views for customer, rig, well, and warehouse management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.http import HttpResponse
from django.utils import timezone

import csv
from datetime import datetime

from apps.core.mixins import ManagerRequiredMixin
from .models import Customer, CustomerContact, Rig, Well, Warehouse
from .forms import CustomerForm, CustomerContactForm, RigForm, WellForm, WarehouseForm


# =============================================================================
# CUSTOMER VIEWS
# =============================================================================

class CustomerListView(LoginRequiredMixin, ListView):
    """
    List all customers with search and filtering.
    """
    model = Customer
    template_name = 'sales/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 25

    def get_queryset(self):
        queryset = Customer.objects.select_related(
            'account_manager', 'created_by'
        ).prefetch_related(
            'contacts', 'rigs', 'wells'
        ).annotate(
            contact_count=Count('contacts'),
            rig_count=Count('rigs'),
            well_count=Count('wells')
        )

        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(name_ar__icontains=search) |
                Q(city__icontains=search) |
                Q(email__icontains=search)
            )

        # Filter by type
        customer_type = self.request.GET.get('type')
        if customer_type:
            queryset = queryset.filter(customer_type=customer_type)

        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        # Filter by ARAMCO
        aramco = self.request.GET.get('aramco')
        if aramco == 'yes':
            queryset = queryset.filter(is_aramco=True)
        elif aramco == 'no':
            queryset = queryset.filter(is_aramco=False)

        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Customers'
        context['customer_types'] = Customer.CustomerType.choices
        context['total_customers'] = Customer.objects.count()
        context['active_customers'] = Customer.objects.filter(is_active=True).count()
        context['aramco_customers'] = Customer.objects.filter(is_aramco=True).count()
        context['current_type'] = self.request.GET.get('type', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_aramco'] = self.request.GET.get('aramco', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class CustomerDetailView(LoginRequiredMixin, DetailView):
    """
    View customer details with tabs for contacts, rigs, wells, etc.
    """
    model = Customer
    template_name = 'sales/customer_detail.html'
    context_object_name = 'customer'

    def get_queryset(self):
        return Customer.objects.select_related(
            'account_manager', 'created_by'
        ).prefetch_related(
            'contacts', 'rigs', 'wells', 'warehouses'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object
        context['page_title'] = f'Customer: {customer.name}'

        # Related data
        context['contacts'] = customer.contacts.all().order_by('-is_primary', 'name')
        context['rigs'] = customer.rigs.all().order_by('code')
        context['wells'] = customer.wells.all().order_by('code')
        context['warehouses'] = customer.warehouses.all().order_by('code')

        # Statistics
        context['stats'] = {
            'total_contacts': customer.contacts.count(),
            'total_rigs': customer.rigs.filter(is_active=True).count(),
            'total_wells': customer.wells.filter(is_active=True).count(),
            'total_warehouses': customer.warehouses.filter(is_active=True).count(),
        }

        # Work orders (if relationship exists)
        if hasattr(customer, 'workorder_set'):
            context['recent_work_orders'] = customer.workorder_set.select_related(
                'drill_bit', 'assigned_to'
            ).order_by('-created_at')[:5]
            context['stats']['total_work_orders'] = customer.workorder_set.count()
            context['stats']['active_work_orders'] = customer.workorder_set.filter(
                status__in=['IN_PROGRESS', 'PLANNED', 'RELEASED']
            ).count()

        # DRSS requests (if relationship exists)
        if hasattr(customer, 'drss_requests'):
            context['recent_drss'] = customer.drss_requests.select_related(
                'rig', 'well'
            ).order_by('-requested_date')[:5]
            context['stats']['total_drss'] = customer.drss_requests.count()

        return context


class CustomerCreateView(ManagerRequiredMixin, CreateView):
    """
    Create a new customer.
    """
    model = Customer
    form_class = CustomerForm
    template_name = 'sales/customer_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'New Customer'
        context['submit_text'] = 'Create Customer'
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
        prefix = 'CUST'
        last = Customer.objects.order_by('-id').first()
        next_num = (last.id + 1) if last else 1
        return f"{prefix}-{str(next_num).zfill(5)}"

    def get_success_url(self):
        return reverse_lazy('sales:customer_detail', kwargs={'pk': self.object.pk})


class CustomerUpdateView(ManagerRequiredMixin, UpdateView):
    """
    Update an existing customer.
    """
    model = Customer
    form_class = CustomerForm
    template_name = 'sales/customer_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Customer: {self.object.name}'
        context['submit_text'] = 'Update Customer'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Customer "{form.instance.name}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('sales:customer_detail', kwargs={'pk': self.object.pk})


# =============================================================================
# CUSTOMER CONTACT VIEWS
# =============================================================================

@login_required
def add_contact(request, customer_pk):
    """Add a contact to a customer."""
    customer = get_object_or_404(Customer, pk=customer_pk)

    if request.method == 'POST':
        form = CustomerContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.customer = customer

            # If marked as primary, unmark others
            if contact.is_primary:
                customer.contacts.update(is_primary=False)

            contact.save()
            messages.success(request, f'Contact "{contact.name}" added successfully.')
            return redirect('sales:customer_detail', pk=customer.pk)
    else:
        form = CustomerContactForm()

    return render(request, 'sales/contact_form.html', {
        'form': form,
        'customer': customer,
        'page_title': f'Add Contact to {customer.name}'
    })


@login_required
def edit_contact(request, pk):
    """Edit a customer contact."""
    contact = get_object_or_404(CustomerContact, pk=pk)
    customer = contact.customer

    if request.method == 'POST':
        form = CustomerContactForm(request.POST, instance=contact)
        if form.is_valid():
            contact = form.save(commit=False)

            # If marked as primary, unmark others
            if contact.is_primary:
                customer.contacts.exclude(pk=contact.pk).update(is_primary=False)

            contact.save()
            messages.success(request, f'Contact "{contact.name}" updated successfully.')
            return redirect('sales:customer_detail', pk=customer.pk)
    else:
        form = CustomerContactForm(instance=contact)

    return render(request, 'sales/contact_form.html', {
        'form': form,
        'customer': customer,
        'contact': contact,
        'page_title': f'Edit Contact: {contact.name}'
    })


@login_required
def delete_contact(request, pk):
    """Delete a customer contact."""
    contact = get_object_or_404(CustomerContact, pk=pk)
    customer = contact.customer

    if request.method == 'POST':
        name = contact.name
        contact.delete()
        messages.success(request, f'Contact "{name}" deleted.')
        return redirect('sales:customer_detail', pk=customer.pk)

    return render(request, 'sales/contact_confirm_delete.html', {
        'contact': contact,
        'customer': customer,
        'page_title': f'Delete Contact: {contact.name}'
    })


# =============================================================================
# RIG VIEWS
# =============================================================================

class RigListView(LoginRequiredMixin, ListView):
    """
    List all rigs with search and filtering.
    """
    model = Rig
    template_name = 'sales/rig_list.html'
    context_object_name = 'rigs'
    paginate_by = 25

    def get_queryset(self):
        queryset = Rig.objects.select_related(
            'customer', 'contractor'
        ).prefetch_related('wells')

        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(location__icontains=search) |
                Q(customer__name__icontains=search)
            )

        # Filter by customer
        customer_id = self.request.GET.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset.order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Rigs'
        context['total_rigs'] = Rig.objects.count()
        context['active_rigs'] = Rig.objects.filter(is_active=True).count()
        context['customers'] = Customer.objects.filter(is_active=True).order_by('name')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class RigDetailView(LoginRequiredMixin, DetailView):
    """
    View rig details.
    """
    model = Rig
    template_name = 'sales/rig_detail.html'
    context_object_name = 'rig'

    def get_queryset(self):
        return Rig.objects.select_related(
            'customer', 'contractor'
        ).prefetch_related('wells', 'drss_requests')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rig = self.object
        context['page_title'] = f'Rig: {rig.name}'
        context['wells'] = rig.wells.all().order_by('code')
        context['stats'] = {
            'total_wells': rig.wells.count(),
            'active_wells': rig.wells.filter(is_active=True).count(),
        }
        return context


class RigCreateView(ManagerRequiredMixin, CreateView):
    """
    Register a new rig.
    """
    model = Rig
    form_class = RigForm
    template_name = 'sales/rig_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'New Rig'
        context['submit_text'] = 'Register Rig'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Rig "{form.instance.name}" registered successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('sales:rig_detail', kwargs={'pk': self.object.pk})


class RigUpdateView(ManagerRequiredMixin, UpdateView):
    """
    Update an existing rig.
    """
    model = Rig
    form_class = RigForm
    template_name = 'sales/rig_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Rig: {self.object.name}'
        context['submit_text'] = 'Update Rig'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Rig "{form.instance.name}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('sales:rig_detail', kwargs={'pk': self.object.pk})


# =============================================================================
# WELL VIEWS
# =============================================================================

class WellListView(LoginRequiredMixin, ListView):
    """
    List all wells with search and filtering.
    """
    model = Well
    template_name = 'sales/well_list.html'
    context_object_name = 'wells'
    paginate_by = 25

    def get_queryset(self):
        queryset = Well.objects.select_related('customer', 'rig')

        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(field_name__icontains=search) |
                Q(customer__name__icontains=search)
            )

        # Filter by customer
        customer_id = self.request.GET.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        # Filter by rig
        rig_id = self.request.GET.get('rig')
        if rig_id:
            queryset = queryset.filter(rig_id=rig_id)

        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset.order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Wells'
        context['total_wells'] = Well.objects.count()
        context['active_wells'] = Well.objects.filter(is_active=True).count()
        context['customers'] = Customer.objects.filter(is_active=True).order_by('name')
        context['rigs'] = Rig.objects.filter(is_active=True).order_by('code')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class WellDetailView(LoginRequiredMixin, DetailView):
    """
    View well details.
    """
    model = Well
    template_name = 'sales/well_detail.html'
    context_object_name = 'well'

    def get_queryset(self):
        return Well.objects.select_related('customer', 'rig')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Well: {self.object.name}'
        return context


class WellCreateView(ManagerRequiredMixin, CreateView):
    """
    Register a new well.
    """
    model = Well
    form_class = WellForm
    template_name = 'sales/well_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'New Well'
        context['submit_text'] = 'Register Well'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Well "{form.instance.name}" registered successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('sales:well_detail', kwargs={'pk': self.object.pk})


class WellUpdateView(ManagerRequiredMixin, UpdateView):
    """
    Update an existing well.
    """
    model = Well
    form_class = WellForm
    template_name = 'sales/well_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Well: {self.object.name}'
        context['submit_text'] = 'Update Well'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Well "{form.instance.name}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('sales:well_detail', kwargs={'pk': self.object.pk})


# =============================================================================
# EXPORT VIEWS
# =============================================================================

@login_required
def export_customers_csv(request):
    """Export customers to CSV."""
    response = HttpResponse(content_type='text/csv')
    filename = f'customers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Code', 'Name', 'Name (AR)', 'Type', 'ARAMCO',
        'City', 'Country', 'Phone', 'Email',
        'Account Manager', 'Active', 'Created'
    ])

    queryset = Customer.objects.select_related('account_manager').order_by('name')

    for c in queryset:
        writer.writerow([
            c.code,
            c.name,
            c.name_ar,
            c.get_customer_type_display(),
            'Yes' if c.is_aramco else 'No',
            c.city,
            c.country,
            c.phone,
            c.email,
            c.account_manager.get_full_name() if c.account_manager else '',
            'Yes' if c.is_active else 'No',
            c.created_at.strftime('%Y-%m-%d'),
        ])

    return response


@login_required
def export_rigs_csv(request):
    """Export rigs to CSV."""
    response = HttpResponse(content_type='text/csv')
    filename = f'rigs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Code', 'Name', 'Customer', 'Contractor', 'Type',
        'Location', 'Latitude', 'Longitude', 'Active'
    ])

    queryset = Rig.objects.select_related('customer', 'contractor').order_by('code')

    for r in queryset:
        writer.writerow([
            r.code,
            r.name,
            r.customer.name if r.customer else '',
            r.contractor.name if r.contractor else '',
            r.rig_type,
            r.location,
            r.latitude or '',
            r.longitude or '',
            'Yes' if r.is_active else 'No',
        ])

    return response
