"""
ARDT FMS - Work Orders Views
Version: 5.4 - Sprint 1.5

Work order management views with optimized queries and exports.
"""

import csv
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from django.http import HttpResponse

from .models import WorkOrder, DrillBit
from .utils import generate_work_order_qr, generate_drill_bit_qr


class WorkOrderListView(LoginRequiredMixin, ListView):
    """
    List all work orders with filtering and pagination.
    """
    model = WorkOrder
    template_name = 'workorders/workorder_list.html'
    context_object_name = 'work_orders'
    paginate_by = 25

    def get_queryset(self):
        queryset = WorkOrder.objects.select_related(
            'customer', 'drill_bit', 'assigned_to', 'design'
        ).order_by('-created_at')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by priority
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(wo_number__icontains=search) |
                Q(customer__name__icontains=search) |
                Q(drill_bit__serial_number__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Work Orders'
        context['status_choices'] = WorkOrder.Status.choices
        context['priority_choices'] = WorkOrder.Priority.choices
        context['current_status'] = self.request.GET.get('status', '')
        context['current_priority'] = self.request.GET.get('priority', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class WorkOrderDetailView(LoginRequiredMixin, DetailView):
    """
    View work order details.
    """
    model = WorkOrder
    template_name = 'workorders/workorder_detail.html'
    context_object_name = 'work_order'

    def get_queryset(self):
        return WorkOrder.objects.select_related(
            'customer', 'drill_bit', 'assigned_to', 'design',
            'sales_order', 'rig', 'well', 'procedure', 'department', 'created_by'
        ).prefetch_related(
            'documents', 'photos', 'materials', 'time_logs'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Work Order {self.object.wo_number}'
        # Generate QR code for the work order
        base_url = getattr(settings, 'SITE_URL', None)
        context['qr_code'] = generate_work_order_qr(self.object, base_url)
        return context


class WorkOrderCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new work order.
    """
    model = WorkOrder
    template_name = 'workorders/workorder_form.html'
    fields = [
        'wo_type', 'drill_bit', 'design', 'customer', 'sales_order',
        'rig', 'well', 'priority', 'planned_start', 'planned_end',
        'due_date', 'assigned_to', 'department', 'description', 'notes'
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'New Work Order'
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.wo_number = self.generate_wo_number()
        messages.success(self.request, f'Work order {form.instance.wo_number} created successfully.')
        return super().form_valid(form)

    def generate_wo_number(self):
        """Generate unique work order number."""
        prefix = getattr(settings, 'ARDT_WO_NUMBER_PREFIX', 'WO')
        padding = getattr(settings, 'ARDT_WO_NUMBER_PADDING', 6)

        last_wo = WorkOrder.objects.order_by('-id').first()
        next_number = (last_wo.id + 1) if last_wo else 1

        return f"{prefix}-{str(next_number).zfill(padding)}"

    def get_success_url(self):
        return reverse_lazy('workorders:detail', kwargs={'pk': self.object.pk})


class WorkOrderUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing work order.
    """
    model = WorkOrder
    template_name = 'workorders/workorder_form.html'
    fields = [
        'wo_type', 'drill_bit', 'design', 'customer', 'sales_order',
        'rig', 'well', 'priority', 'planned_start', 'planned_end',
        'due_date', 'status', 'assigned_to', 'department', 'description', 'notes'
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Work Order {self.object.wo_number}'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Work order {form.instance.wo_number} updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:detail', kwargs={'pk': self.object.pk})


@login_required
def start_work_view(request, pk):
    """
    Start working on a work order.
    """
    work_order = get_object_or_404(WorkOrder, pk=pk)

    if request.method == 'POST':
        if work_order.status in ['RELEASED', 'PLANNED']:
            work_order.status = 'IN_PROGRESS'
            work_order.actual_start = timezone.now()
            work_order.save()
            messages.success(request, f'Started working on {work_order.wo_number}.')
        else:
            messages.error(request, f'Cannot start work order with status {work_order.get_status_display()}.')

    return redirect('workorders:detail', pk=pk)


@login_required
def complete_work_view(request, pk):
    """
    Complete a work order (send to QC).
    """
    work_order = get_object_or_404(WorkOrder, pk=pk)

    if request.method == 'POST':
        if work_order.status == 'IN_PROGRESS':
            work_order.status = 'QC_PENDING'
            work_order.save()
            messages.success(request, f'{work_order.wo_number} sent to QC for inspection.')
        else:
            messages.error(request, f'Cannot complete work order with status {work_order.get_status_display()}.')

    return redirect('workorders:detail', pk=pk)


# =============================================================================
# DRILL BIT VIEWS
# =============================================================================

class DrillBitListView(LoginRequiredMixin, ListView):
    """
    List all drill bits with filtering and pagination.
    """
    model = DrillBit
    template_name = 'drillbits/drillbit_list.html'
    context_object_name = 'drill_bits'
    paginate_by = 25

    def get_queryset(self):
        queryset = DrillBit.objects.select_related(
            'design', 'customer', 'current_location', 'created_by'
        ).order_by('-created_at')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by type
        bit_type = self.request.GET.get('type')
        if bit_type:
            queryset = queryset.filter(bit_type=bit_type)

        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(serial_number__icontains=search) |
                Q(iadc_code__icontains=search) |
                Q(customer__name__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Drill Bits'
        context['status_choices'] = DrillBit.Status.choices
        context['type_choices'] = DrillBit.BitType.choices
        context['current_status'] = self.request.GET.get('status', '')
        context['current_type'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class DrillBitDetailView(LoginRequiredMixin, DetailView):
    """
    View drill bit details with QR code.
    """
    model = DrillBit
    template_name = 'drillbits/drillbit_detail.html'
    context_object_name = 'drill_bit'

    def get_queryset(self):
        return DrillBit.objects.select_related(
            'design', 'customer', 'current_location', 'rig', 'well', 'created_by'
        ).prefetch_related(
            'work_orders', 'evaluations'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Drill Bit {self.object.serial_number}'
        # Get recent work orders for this drill bit
        context['recent_work_orders'] = self.object.work_orders.order_by('-created_at')[:5]
        # Generate QR code for the drill bit
        base_url = getattr(settings, 'SITE_URL', None)
        context['qr_code'] = generate_drill_bit_qr(self.object, base_url)
        return context


class DrillBitCreateView(LoginRequiredMixin, CreateView):
    """
    Register a new drill bit.
    """
    model = DrillBit
    template_name = 'drillbits/drillbit_form.html'
    fields = [
        'serial_number', 'bit_type', 'design', 'size', 'iadc_code',
        'status', 'current_location', 'customer', 'rig', 'well'
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Register Drill Bit'
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Drill bit {form.instance.serial_number} registered successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:drillbit_detail', kwargs={'pk': self.object.pk})


class DrillBitUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update drill bit information.
    """
    model = DrillBit
    template_name = 'drillbits/drillbit_form.html'
    fields = [
        'bit_type', 'design', 'size', 'iadc_code',
        'status', 'current_location', 'customer', 'rig', 'well',
        'total_hours', 'total_footage', 'run_count'
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Drill Bit {self.object.serial_number}'
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Drill bit {form.instance.serial_number} updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('workorders:drillbit_detail', kwargs={'pk': self.object.pk})


@login_required
def drillbit_qr_view(request, pk):
    """
    Display QR code for a drill bit.
    """
    drill_bit = get_object_or_404(DrillBit, pk=pk)
    return render(request, 'drillbits/drillbit_qr.html', {
        'drill_bit': drill_bit,
        'page_title': f'QR Code - {drill_bit.serial_number}'
    })


# =============================================================================
# HTMX VIEWS
# =============================================================================

@login_required
def update_status_htmx(request, pk):
    """
    HTMX endpoint for updating work order status.
    Returns partial HTML for the status badge.
    """
    from django.http import HttpResponse

    work_order = get_object_or_404(WorkOrder, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status and new_status in dict(WorkOrder.Status.choices):
            old_status = work_order.status
            work_order.status = new_status

            # Update timestamps based on status change
            if new_status == 'IN_PROGRESS' and old_status in ['PLANNED', 'RELEASED']:
                work_order.actual_start = timezone.now()
            elif new_status == 'COMPLETED':
                work_order.actual_end = timezone.now()
                work_order.progress_percent = 100

            work_order.save()

            # Return the partial template for HTMX swap
            return render(request, 'partials/status_badge.html', {
                'object_id': work_order.pk,
                'status': work_order.status,
                'status_display': work_order.get_status_display(),
            })

    # GET request - return current status badge
    return render(request, 'partials/status_badge.html', {
        'object_id': work_order.pk,
        'status': work_order.status,
        'status_display': work_order.get_status_display(),
    })


@login_required
def workorder_row_htmx(request, pk):
    """
    HTMX endpoint for returning a single work order row.
    Used for refreshing a row after updates.
    """
    work_order = get_object_or_404(
        WorkOrder.objects.select_related(
            'customer', 'drill_bit', 'assigned_to'
        ),
        pk=pk
    )
    return render(request, 'partials/workorder_row.html', {
        'work_order': work_order,
    })


# =============================================================================
# EXPORT VIEWS
# =============================================================================

@login_required
def export_work_orders_csv(request):
    """
    Export work orders to CSV file.
    Preserves any active filters from the list view.
    """
    response = HttpResponse(content_type='text/csv')
    filename = f'workorders_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'WO Number', 'Type', 'Customer', 'Drill Bit', 'Status', 'Priority',
        'Due Date', 'Assigned To', 'Progress %', 'Created At'
    ])

    # Build queryset with same filters as list view
    queryset = WorkOrder.objects.select_related(
        'customer', 'drill_bit', 'assigned_to'
    ).order_by('-created_at')

    # Apply filters from request
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)

    priority = request.GET.get('priority')
    if priority:
        queryset = queryset.filter(priority=priority)

    search = request.GET.get('q')
    if search:
        queryset = queryset.filter(
            Q(wo_number__icontains=search) |
            Q(customer__name__icontains=search)
        )

    for wo in queryset:
        writer.writerow([
            wo.wo_number,
            wo.get_wo_type_display(),
            wo.customer.name if wo.customer else '',
            wo.drill_bit.serial_number if wo.drill_bit else '',
            wo.get_status_display(),
            wo.get_priority_display(),
            wo.due_date.strftime('%Y-%m-%d') if wo.due_date else '',
            wo.assigned_to.get_full_name() if wo.assigned_to else '',
            wo.progress_percent,
            wo.created_at.strftime('%Y-%m-%d %H:%M'),
        ])

    return response


@login_required
def export_drill_bits_csv(request):
    """
    Export drill bits to CSV file.
    Preserves any active filters from the list view.
    """
    response = HttpResponse(content_type='text/csv')
    filename = f'drillbits_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Serial Number', 'Type', 'Size', 'IADC Code', 'Status',
        'Customer', 'Location', 'Total Hours', 'Total Footage', 'Run Count'
    ])

    # Build queryset with same filters as list view
    queryset = DrillBit.objects.select_related(
        'customer', 'current_location'
    ).order_by('-created_at')

    # Apply filters from request
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)

    bit_type = request.GET.get('type')
    if bit_type:
        queryset = queryset.filter(bit_type=bit_type)

    search = request.GET.get('q')
    if search:
        queryset = queryset.filter(
            Q(serial_number__icontains=search) |
            Q(iadc_code__icontains=search)
        )

    for bit in queryset:
        writer.writerow([
            bit.serial_number,
            bit.get_bit_type_display(),
            str(bit.size),
            bit.iadc_code,
            bit.get_status_display(),
            bit.customer.name if bit.customer else '',
            bit.current_location.name if bit.current_location else '',
            str(bit.total_hours),
            bit.total_footage,
            bit.run_count,
        ])

    return response
