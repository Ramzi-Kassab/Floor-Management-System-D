"""
ARDT FMS - Job Card Views
Version: 1.0

Enhanced views for Job Card functionality including:
- Work Order Dashboard with modern UI
- Cutter Evaluation Matrix
- Router Sheet with QR tracking
- QC Forms (LPT, API Thread, E-Checklist)
- Instruction Rules management
"""

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Sum, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView, TemplateView, View
)

from .models import (
    WorkOrder, DrillBit, BitEvent, Location,
    CutterEvaluationMatrix, CutterEvaluationEntry,
    RouterSheetEntry, EvaluationChecklist,
    LPTReport, APIThreadInspection,
    InstructionRule, InstructionRuleCondition,
    ProcessRoute, ProcessRouteOperation, OperationExecution,
    RepairEvaluation, WorkOrderCost
)
from .utils import generate_work_order_qr, generate_drill_bit_qr


# =============================================================================
# WORK ORDER DASHBOARD - Modern UI
# =============================================================================

class WorkOrderDashboardView(LoginRequiredMixin, TemplateView):
    """
    Main Work Order Dashboard with summary cards and quick filters.
    Similar to cutter inventory dashboard.
    """
    template_name = "workorders/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Summary statistics
        total_wo = WorkOrder.objects.count()
        context['total_work_orders'] = total_wo

        # Status breakdown
        context['draft_count'] = WorkOrder.objects.filter(status=WorkOrder.Status.DRAFT).count()
        context['in_progress_count'] = WorkOrder.objects.filter(status=WorkOrder.Status.IN_PROGRESS).count()
        context['qc_pending_count'] = WorkOrder.objects.filter(status=WorkOrder.Status.QC_PENDING).count()
        context['completed_count'] = WorkOrder.objects.filter(status=WorkOrder.Status.COMPLETED).count()

        # Overdue work orders
        today = timezone.now().date()
        context['overdue_count'] = WorkOrder.objects.filter(
            due_date__lt=today
        ).exclude(
            status__in=[WorkOrder.Status.COMPLETED, WorkOrder.Status.CANCELLED]
        ).count()

        # Due this week
        week_end = today + timedelta(days=7)
        context['due_this_week'] = WorkOrder.objects.filter(
            due_date__gte=today,
            due_date__lte=week_end
        ).exclude(
            status__in=[WorkOrder.Status.COMPLETED, WorkOrder.Status.CANCELLED]
        ).count()

        # Recent work orders
        context['recent_work_orders'] = WorkOrder.objects.select_related(
            'customer', 'drill_bit', 'assigned_to'
        ).order_by('-created_at')[:10]

        # Drill bit statistics
        context['total_bits'] = DrillBit.objects.count()
        context['bits_in_production'] = DrillBit.objects.filter(
            status=DrillBit.Status.IN_PRODUCTION
        ).count()
        context['bits_at_rig'] = DrillBit.objects.filter(
            physical_status=DrillBit.PhysicalStatus.AT_RIG
        ).count()

        context['page_title'] = 'Work Orders Dashboard'
        return context


class WorkOrderListEnhancedView(LoginRequiredMixin, ListView):
    """
    Enhanced Work Order List with Excel-like filtering.
    """
    model = WorkOrder
    template_name = "workorders/workorder_list_enhanced.html"
    context_object_name = "work_orders"
    paginate_by = None  # Default to all for column filters

    def get_paginate_by(self, queryset):
        """Allow page size to be changed via query parameter."""
        page_size = self.request.GET.get('page_size', 'all')
        if page_size == 'all':
            return None
        try:
            page_size = int(page_size)
            if page_size in [25, 50, 100, 200]:
                return page_size
        except (ValueError, TypeError):
            pass
        return None

    def get_queryset(self):
        queryset = WorkOrder.objects.select_related(
            "customer", "drill_bit", "assigned_to", "design", "bom"
        ).order_by("-created_at")

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filter by wo_type
        wo_type = self.request.GET.get("wo_type")
        if wo_type:
            queryset = queryset.filter(wo_type=wo_type)

        # Filter by priority
        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        # Filter by customer
        customer_id = self.request.GET.get("customer")
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        # Search
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(wo_number__icontains=search)
                | Q(customer__name__icontains=search)
                | Q(drill_bit__serial_number__icontains=search)
                | Q(drss_no__icontains=search)
                | Q(brazing_mat_no__icontains=search)
            )

        # Date range filter
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Work Orders"
        context["status_choices"] = WorkOrder.Status.choices
        context["wo_type_choices"] = WorkOrder.WOType.choices
        context["priority_choices"] = WorkOrder.Priority.choices

        # Get unique customers for filter
        from apps.sales.models import Customer
        context["customers"] = Customer.objects.filter(
            work_orders__isnull=False
        ).distinct().order_by('name')

        # Current filters
        context["current_status"] = self.request.GET.get("status", "")
        context["current_wo_type"] = self.request.GET.get("wo_type", "")
        context["current_priority"] = self.request.GET.get("priority", "")
        context["current_customer"] = self.request.GET.get("customer", "")
        context["current_search"] = self.request.GET.get("search", "")
        context["date_from"] = self.request.GET.get("date_from", "")
        context["date_to"] = self.request.GET.get("date_to", "")

        # Page size
        paginate_by = self.get_paginate_by(None)
        context["page_size"] = 'all' if paginate_by is None else paginate_by
        context["total_count"] = self.get_queryset().count()

        return context


class WorkOrderDetailEnhancedView(LoginRequiredMixin, DetailView):
    """
    Enhanced Work Order Detail with Job Card tabs.
    """
    model = WorkOrder
    template_name = "workorders/workorder_detail_enhanced.html"
    context_object_name = "work_order"

    def get_queryset(self):
        return WorkOrder.objects.select_related(
            "customer", "drill_bit", "assigned_to", "design", "bom",
            "sales_order", "rig", "well", "procedure", "department",
            "created_by", "evaluated_by", "qc_by", "reviewed_by_eng",
            "approved_by"
        ).prefetch_related(
            "documents", "photos", "materials", "time_logs",
            "cutter_evaluations__entries", "router_entries",
            "lpt_reports", "api_thread_inspections", "repair_boms__lines"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wo = self.object

        context["page_title"] = f"Job Card - {wo.wo_number}"

        # Generate QR code
        base_url = getattr(settings, "SITE_URL", None)
        context["qr_code"] = generate_work_order_qr(wo, base_url)

        # Get applicable instructions
        context["instructions"] = self.get_applicable_instructions(wo)

        # E-Checklist
        try:
            context["e_checklist"] = wo.evaluation_checklist
        except EvaluationChecklist.DoesNotExist:
            context["e_checklist"] = None

        # Cutter evaluations by type
        context["ardt_evaluation"] = wo.cutter_evaluations.filter(
            evaluation_type=CutterEvaluationMatrix.EvaluationType.ARDT
        ).first()
        context["eng_evaluation"] = wo.cutter_evaluations.filter(
            evaluation_type=CutterEvaluationMatrix.EvaluationType.ENGINEER
        ).first()
        context["rework_evaluation"] = wo.cutter_evaluations.filter(
            evaluation_type=CutterEvaluationMatrix.EvaluationType.REWORK
        ).first()

        # Router sheet entries
        context["router_entries"] = wo.router_entries.order_by('step_number')

        # LPT Reports
        context["lpt_reports"] = wo.lpt_reports.order_by('-created_at')

        # API Thread Inspections
        context["api_inspections"] = wo.api_thread_inspections.order_by('-created_at')

        # Cost summary
        try:
            context["cost_summary"] = wo.cost_summary
        except WorkOrderCost.DoesNotExist:
            context["cost_summary"] = None

        # Status transitions
        from django.contrib.contenttypes.models import ContentType
        from .models import StatusTransitionLog
        wo_ct = ContentType.objects.get_for_model(WorkOrder)
        context["status_history"] = StatusTransitionLog.objects.filter(
            content_type=wo_ct,
            object_id=wo.pk
        ).order_by('-changed_at')[:10]

        return context

    def get_applicable_instructions(self, work_order):
        """Get all instructions that apply to this work order."""
        instructions = []

        for rule in InstructionRule.objects.filter(is_active=True):
            # Check WO type filter
            if rule.applies_to_wo_types:
                if work_order.wo_type not in rule.applies_to_wo_types:
                    continue

            # Check bit type filter
            if rule.applies_to_bit_types and work_order.drill_bit:
                if work_order.drill_bit.bit_type not in rule.applies_to_bit_types:
                    continue

            # Check conditions
            conditions_met = True
            for condition in rule.conditions.all():
                if not condition.evaluate(work_order):
                    conditions_met = False
                    break

            if conditions_met:
                instructions.append(rule)

        return sorted(instructions, key=lambda x: -x.priority)


# =============================================================================
# DRILL BIT LIFECYCLE VIEWS
# =============================================================================

class DrillBitListEnhancedView(LoginRequiredMixin, ListView):
    """
    Enhanced Drill Bit List with lifecycle tracking.
    """
    model = DrillBit
    template_name = "workorders/drillbit_list_enhanced.html"
    context_object_name = "drill_bits"
    paginate_by = None

    def get_paginate_by(self, queryset):
        page_size = self.request.GET.get('page_size', 'all')
        if page_size == 'all':
            return None
        try:
            page_size = int(page_size)
            if page_size in [25, 50, 100, 200]:
                return page_size
        except (ValueError, TypeError):
            pass
        return None

    def get_queryset(self):
        queryset = DrillBit.objects.select_related(
            "design", "design__size", "design__connection_ref",
            "design__iadc_code_ref", "design__breaker_slot",
            "design__application_ref", "design__formation_type_ref",
            "bom", "bom__smi_type", "brazing_bom", "brazing_bom__smi_type",
            "system_bom", "system_bom__smi_type",
            "customer", "rig", "well", "current_location", "bit_location"
        ).prefetch_related(
            "design__special_technologies"
        ).order_by("-created_at")

        # Filters
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        lifecycle = self.request.GET.get("lifecycle")
        if lifecycle:
            queryset = queryset.filter(lifecycle_status=lifecycle)

        bit_type = self.request.GET.get("bit_type")
        if bit_type:
            queryset = queryset.filter(bit_type=bit_type)

        physical = self.request.GET.get("physical")
        if physical:
            queryset = queryset.filter(physical_status=physical)

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(serial_number__icontains=search)
                | Q(mat_number__icontains=search)
                | Q(customer__name__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Drill Bits"
        context["status_choices"] = DrillBit.Status.choices
        context["lifecycle_choices"] = DrillBit.LifecycleStatus.choices
        context["bit_type_choices"] = DrillBit.BitCategory.choices
        context["physical_choices"] = DrillBit.PhysicalStatus.choices

        context["current_status"] = self.request.GET.get("status", "")
        context["current_lifecycle"] = self.request.GET.get("lifecycle", "")
        context["current_bit_type"] = self.request.GET.get("bit_type", "")
        context["current_physical"] = self.request.GET.get("physical", "")
        context["current_search"] = self.request.GET.get("search", "")

        paginate_by = self.get_paginate_by(None)
        context["page_size"] = 'all' if paginate_by is None else paginate_by
        context["total_count"] = self.get_queryset().count()

        return context


class DrillBitDetailEnhancedView(LoginRequiredMixin, DetailView):
    """
    Enhanced Drill Bit Detail with full lifecycle history.
    """
    model = DrillBit
    template_name = "workorders/drillbit_detail_enhanced.html"
    context_object_name = "drill_bit"

    def get_queryset(self):
        return DrillBit.objects.select_related(
            "design", "design__size", "design__connection_ref",
            "design__iadc_code_ref", "design__breaker_slot",
            "design__application_ref", "design__formation_type_ref",
            "design__upper_section_type", "design__connection_type_ref",
            "design__connection_size_ref",
            "customer", "rig", "well", "current_location",
            "bit_location", "bit_size_ref", "product_type", "created_by",
            "bom", "bom__smi_type", "brazing_bom", "brazing_bom__smi_type",
            "system_bom", "system_bom__smi_type",
        ).prefetch_related(
            "work_orders", "evaluations", "bit_events", "repair_history",
            "design__special_technologies",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bit = self.object

        context["page_title"] = f"Drill Bit - {bit.serial_number}"

        # Generate QR code
        base_url = getattr(settings, "SITE_URL", None)
        context["qr_code"] = generate_drill_bit_qr(bit, base_url)

        # Event history
        context["events"] = bit.bit_events.order_by('-event_date')[:20]

        # Work orders
        context["work_orders"] = bit.work_orders.order_by('-created_at')

        # Repair history
        context["repairs"] = bit.repair_history.order_by('-repair_number')

        # Evaluations
        context["evaluations"] = bit.evaluations.order_by('-evaluation_date')

        # ── BOM source_data for inline display ──
        active_bom = bit.brazing_bom or bit.bom or bit.system_bom
        if active_bom and active_bom.source_data:
            source_data = active_bom.source_data
            # Enrich cutter shapes from inventory
            try:
                from apps.cutter_map.views import _enrich_cutter_shapes_from_inventory
                _enrich_cutter_shapes_from_inventory(source_data)
            except Exception:
                pass
            context["bom_source_data"] = source_data
            # Build cutter_shapes dict {int(index): base64_data}
            cutter_shapes = {}
            raw_shapes = source_data.get("cutter_shapes", {})
            for k, v in raw_shapes.items():
                try:
                    idx = int(k)
                    if isinstance(v, dict):
                        cutter_shapes[idx] = v.get("data", "")
                    elif isinstance(v, str):
                        cutter_shapes[idx] = v
                except (ValueError, TypeError):
                    pass
            context["cutter_shapes"] = cutter_shapes
        context["active_bom"] = active_bom

        # ── Design pocket layout ──
        design = bit.design
        if design:
            import json as _json
            from apps.technology.models import DesignPocket, DesignPocketConfig
            pockets = DesignPocket.objects.filter(
                design=design
            ).select_related(
                'pocket_config', 'pocket_config__pocket_size', 'pocket_config__pocket_shape'
            ).order_by('blade_number', 'row_number', 'position_in_row')
            context["design_pockets"] = pockets

            pocket_configs = DesignPocketConfig.objects.filter(
                design=design
            ).select_related(
                'pocket_size', 'pocket_shape'
            ).order_by('order')
            context["pocket_configs"] = pocket_configs

            # Build grid data, row separators, location data for Alpine.js read-only grid
            grid_data = {}
            location_data = {}
            engagement_data = {}
            positions_by_row = {}
            for p in pockets:
                key = f"{p.blade_number}_{p.position_in_blade}"
                grid_data[key] = p.pocket_config_id
                if p.blade_location:
                    location_data[key] = p.blade_location
                if p.engagement_order:
                    engagement_data[key] = p.engagement_order
                if p.row_number not in positions_by_row:
                    positions_by_row[p.row_number] = []
                positions_by_row[p.row_number].append(p.position_in_blade)

            row_separators = []
            for row_num in sorted(positions_by_row.keys())[:-1]:
                row_separators.append(max(positions_by_row[row_num]))

            context["pocket_grid_data_json"] = _json.dumps(grid_data)
            context["pocket_row_separators_json"] = _json.dumps(sorted(row_separators))
            context["pocket_location_data_json"] = _json.dumps(location_data)
            context["pocket_engagement_data_json"] = _json.dumps(engagement_data)

            # Generate display colors for configs (same as DesignPocketsView)
            colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
                      '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1']
            config_data = {}
            for i, cfg in enumerate(pocket_configs):
                dc = cfg.color_code if cfg.color_code else colors[i % len(colors)]
                cfg.display_color = dc
                config_data[cfg.pk] = {
                    "count": cfg.count,
                    "order": cfg.order,
                    "color": dc,
                    "name": cfg.pocket_size.display_name if cfg.pocket_size else '',
                    "sizeCode": cfg.pocket_size.code if cfg.pocket_size else '',
                }
            context["pocket_config_data_json"] = _json.dumps(config_data)
            context["config_total"] = sum(cfg.count for cfg in pocket_configs)

        return context


# =============================================================================
# CUTTER EVALUATION MATRIX VIEWS
# =============================================================================

class CutterEvaluationCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new cutter evaluation matrix for a work order.
    """
    model = CutterEvaluationMatrix
    template_name = "workorders/cutter_evaluation_form.html"
    fields = ['evaluation_type', 'ardt_remark', 'eng_remark', 'general_remark',
              'ardt_matrix_buildup', 'eng_matrix_buildup', 'ncr_ref_no']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wo = get_object_or_404(WorkOrder, pk=self.kwargs['wo_pk'])
        context['work_order'] = wo
        context['page_title'] = f"Cutter Evaluation - {wo.wo_number}"

        # Get pocket layout from design if available
        if wo.design:
            context['pocket_layout'] = wo.design.pockets.order_by('blade_number', 'position_number')

        return context

    def form_valid(self, form):
        wo = get_object_or_404(WorkOrder, pk=self.kwargs['wo_pk'])
        form.instance.work_order = wo
        form.instance.evaluated_by = self.request.user
        form.instance.evaluated_at = timezone.now()

        # Set evaluation number
        existing = CutterEvaluationMatrix.objects.filter(
            work_order=wo,
            evaluation_type=form.cleaned_data['evaluation_type']
        ).count()
        form.instance.evaluation_number = existing + 1

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('workorders:cutter_evaluation_edit', kwargs={
            'wo_pk': self.kwargs['wo_pk'],
            'pk': self.object.pk
        })


class CutterEvaluationEditView(LoginRequiredMixin, TemplateView):
    """
    Interactive cutter evaluation matrix editor.
    """
    template_name = "workorders/cutter_evaluation_matrix.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        wo = get_object_or_404(WorkOrder, pk=self.kwargs['wo_pk'])
        matrix = get_object_or_404(CutterEvaluationMatrix, pk=self.kwargs['pk'])

        context['work_order'] = wo
        context['matrix'] = matrix
        context['page_title'] = f"{matrix.get_evaluation_type_display()} - {wo.wo_number}"

        # Build the blade/cutter grid
        # Determine max blades and cutters from design or default
        max_blades = 12
        max_cutters = 15

        if wo.design:
            # Get from pocket layout
            pockets = wo.design.pockets.all()
            if pockets.exists():
                max_blades = max(p.blade_number for p in pockets)
                max_cutters = max(p.position_number for p in pockets)

        # Build evaluation grid
        grid = {}
        for entry in matrix.entries.all():
            grid[(entry.blade_number, entry.cutter_position)] = entry

        # Build rows for template
        rows = []
        for blade in range(1, max_blades + 1):
            row = {'blade': blade, 'cutters': []}
            for cutter in range(1, max_cutters + 1):
                entry = grid.get((blade, cutter))
                row['cutters'].append({
                    'position': cutter,
                    'entry': entry,
                    'action': entry.action if entry else '',
                })
            rows.append(row)

        context['rows'] = rows
        context['max_cutters'] = max_cutters
        context['action_choices'] = CutterEvaluationEntry.Action.choices
        context['source_choices'] = CutterEvaluationEntry.CutterSource.choices

        return context

    def post(self, request, *args, **kwargs):
        """Handle grid updates via AJAX."""
        matrix = get_object_or_404(CutterEvaluationMatrix, pk=kwargs['pk'])

        blade = int(request.POST.get('blade'))
        position = int(request.POST.get('position'))
        action = request.POST.get('action', '')
        source = request.POST.get('source', '')
        notes = request.POST.get('notes', '')

        entry, created = CutterEvaluationEntry.objects.update_or_create(
            matrix=matrix,
            blade_number=blade,
            cutter_position=position,
            defaults={
                'action': action,
                'cutter_source': source,
                'notes': notes,
            }
        )

        return JsonResponse({
            'success': True,
            'entry_id': entry.pk,
            'action': entry.get_action_display(),
        })


# =============================================================================
# ROUTER SHEET VIEWS
# =============================================================================

class RouterSheetView(LoginRequiredMixin, TemplateView):
    """
    Router Sheet with step-by-step tracking and QR scanning.
    """
    template_name = "workorders/router_sheet.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        wo = get_object_or_404(WorkOrder, pk=self.kwargs['pk'])
        context['work_order'] = wo
        context['page_title'] = f"Router Sheet - {wo.wo_number}"

        # Get or create router entries from process route
        entries = list(wo.router_entries.order_by('step_number'))

        # If no entries and there's a procedure, create from template
        if not entries and wo.procedure:
            # Create entries from procedure steps
            for step in wo.procedure.steps.order_by('order'):
                RouterSheetEntry.objects.get_or_create(
                    work_order=wo,
                    step_number=step.order,
                    defaults={
                        'step_description': step.name,
                    }
                )
            entries = list(wo.router_entries.order_by('step_number'))

        # If still no entries, create default FC repair steps
        if not entries and wo.wo_type in ['FC_REPAIR', 'FC_REWORK']:
            default_steps = [
                "Nozzle Removal",
                "Cerebro Removal (if applicable)",
                "O-Ring Removal (if applicable)",
                "Washing",
                "Sand Blasting",
                "Pressure Test (if applicable)",
                "Die Check",
                "Photos & Evaluation",
                "Bit Head Preparation",
                "De-Brazing (if applicable)",
                "Matrix or Hardfacing Repair (if applicable)",
                "Pocket, Blade or IA Grinding (if applicable)",
                "Sand Blasting",
                "Bit Head Preparation For Brazing",
                "Brazing",
                "Final Grinding",
                "Cleaning & Packaging",
                "Final Inspection",
            ]
            for i, desc in enumerate(default_steps, 1):
                RouterSheetEntry.objects.get_or_create(
                    work_order=wo,
                    step_number=i,
                    defaults={'step_description': desc}
                )
            entries = list(wo.router_entries.order_by('step_number'))

        context['entries'] = entries

        # Generate WO QR for scanning
        base_url = getattr(settings, "SITE_URL", None)
        context['wo_qr'] = generate_work_order_qr(wo, base_url)

        return context


@login_required
def router_step_scan(request, wo_pk, step_number):
    """
    Handle QR scan for router step start/end.
    """
    wo = get_object_or_404(WorkOrder, pk=wo_pk)
    entry = get_object_or_404(RouterSheetEntry, work_order=wo, step_number=step_number)

    action = request.POST.get('action', 'start')
    station_qr = request.POST.get('station_qr', '')

    if action == 'start':
        entry.qr_scan_start = timezone.now()
        entry.operator = request.user
        entry.station_qr = station_qr
        entry.save()
        messages.success(request, f"Step {step_number} started")
    elif action == 'end':
        entry.qr_scan_end = timezone.now()
        entry.is_complete = True
        entry.save()
        messages.success(request, f"Step {step_number} completed")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'step_number': step_number,
            'is_complete': entry.is_complete,
            'duration': entry.duration_minutes,
        })

    return redirect('workorders:router_sheet', pk=wo_pk)


# =============================================================================
# QC FORMS VIEWS
# =============================================================================

class EvaluationChecklistView(LoginRequiredMixin, UpdateView):
    """
    E-Checklist form for FC Bit Evaluation.
    """
    model = EvaluationChecklist
    template_name = "workorders/e_checklist_form.html"
    fields = [
        'bit_cleanliness', 'bit_cleanliness_remarks',
        'paperwork', 'paperwork_remarks',
        'bit_stamping', 'bit_stamping_remarks',
        'die_check', 'die_check_remarks',
        'ring_gauge_go', 'ring_gauge_go_remarks',
        'ring_gauge_no_go', 'ring_gauge_no_go_remarks',
        'nozzle_bore_liner', 'nozzle_bore_liner_remarks',
        'nozzle_threads', 'nozzle_threads_remarks',
        'apex', 'apex_remarks',
        'junk_slot', 'junk_slot_remarks',
        'breaker_slot', 'breaker_slot_remarks',
        'body_condition', 'body_condition_remarks',
        'mud_seal_surface', 'mud_seal_surface_remarks',
        'api_pin', 'api_pin_remarks',
        'inner_diameter', 'inner_diameter_remarks',
        'overall_pass', 'general_remarks',
    ]

    def get_object(self, queryset=None):
        wo = get_object_or_404(WorkOrder, pk=self.kwargs['wo_pk'])
        checklist, created = EvaluationChecklist.objects.get_or_create(
            work_order=wo,
            defaults={'inspector': self.request.user}
        )
        return checklist

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['work_order'] = self.object.work_order
        context['page_title'] = f"E-Checklist - {self.object.work_order.wo_number}"
        context['result_choices'] = EvaluationChecklist.Result.choices
        return context

    def form_valid(self, form):
        form.instance.inspector = self.request.user
        form.instance.inspection_date = timezone.now().date()
        messages.success(self.request, "E-Checklist saved successfully")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('workorders:workorder_detail_enhanced', kwargs={'pk': self.kwargs['wo_pk']})


class LPTReportCreateView(LoginRequiredMixin, CreateView):
    """
    Create LPT Report.
    """
    model = LPTReport
    template_name = "workorders/lpt_report_form.html"
    fields = [
        'test_type', 'technique', 'procedure_ref',
        'cleaner_product', 'cleaner_batch', 'cleaner_expiry',
        'penetrant_product', 'penetrant_batch', 'penetrant_expiry',
        'developer_product', 'developer_batch', 'developer_expiry',
        'surface_temperature', 'penetrant_dwell_time',
        'light_intensity', 'developer_dwell_time',
        'result', 'disposition',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wo = get_object_or_404(WorkOrder, pk=self.kwargs['wo_pk'])
        context['work_order'] = wo
        context['page_title'] = f"LPT Report - {wo.wo_number}"
        return context

    def form_valid(self, form):
        wo = get_object_or_404(WorkOrder, pk=self.kwargs['wo_pk'])
        form.instance.work_order = wo
        form.instance.lpt_operator = self.request.user
        form.instance.operator_date = timezone.now().date()

        # Generate report number
        count = LPTReport.objects.filter(work_order=wo).count()
        form.instance.report_number = f"LPT-{wo.wo_number}-{count + 1:02d}"

        messages.success(self.request, "LPT Report created successfully")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('workorders:workorder_detail_enhanced', kwargs={'pk': self.kwargs['wo_pk']})


class APIThreadInspectionCreateView(LoginRequiredMixin, CreateView):
    """
    Create API Thread Inspection.
    """
    model = APIThreadInspection
    template_name = "workorders/api_thread_form.html"
    fields = [
        'pin_size',
        'pin_face_ok', 'pin_face_remarks',
        'thread_ok', 'thread_remarks',
        'pitch_gauge_ok', 'pitch_gauge_remarks',
        'mud_seal_ok', 'mud_seal_remarks',
        'other_observation', 'pin_height',
        'thread_repair_required',
        'repair_brush_selected', 'upper_section_replacement',
        'initial_result',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wo = get_object_or_404(WorkOrder, pk=self.kwargs['wo_pk'])
        context['work_order'] = wo
        context['page_title'] = f"API Thread Inspection - {wo.wo_number}"
        return context

    def form_valid(self, form):
        wo = get_object_or_404(WorkOrder, pk=self.kwargs['wo_pk'])
        form.instance.work_order = wo
        form.instance.inspector = self.request.user
        form.instance.inspection_date = timezone.now().date()

        # Generate inspection number
        count = APIThreadInspection.objects.filter(work_order=wo).count()
        form.instance.inspection_number = f"API-{wo.wo_number}-{count + 1:02d}"

        messages.success(self.request, "API Thread Inspection created successfully")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('workorders:workorder_detail_enhanced', kwargs={'pk': self.kwargs['wo_pk']})


# =============================================================================
# INSTRUCTION RULES VIEWS
# =============================================================================

class InstructionRuleListView(LoginRequiredMixin, ListView):
    """
    List all instruction rules.
    """
    model = InstructionRule
    template_name = "workorders/instruction_rule_list.html"
    context_object_name = "rules"
    paginate_by = 25

    def get_queryset(self):
        queryset = InstructionRule.objects.prefetch_related('conditions').order_by('-priority', 'name')

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(instruction_text__icontains=search)
            )

        active = self.request.GET.get('active')
        if active == 'yes':
            queryset = queryset.filter(is_active=True)
        elif active == 'no':
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Instruction Rules'
        context['current_search'] = self.request.GET.get('search', '')
        context['current_active'] = self.request.GET.get('active', '')
        return context


class InstructionRuleCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new instruction rule with inline conditions.
    """
    model = InstructionRule
    template_name = "workorders/instruction_rule_form.html"
    fields = ['name', 'description', 'instruction_text', 'priority',
              'applies_to_wo_types', 'applies_to_bit_types', 'is_active']
    success_url = reverse_lazy('workorders:instruction_rule_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Instruction Rule'
        context['wo_type_choices'] = WorkOrder.WOType.choices
        context['bit_type_choices'] = DrillBit.BitCategory.choices

        # Add condition formset
        from .forms import InstructionRuleConditionFormSet
        if self.request.POST:
            context['condition_formset'] = InstructionRuleConditionFormSet(
                self.request.POST, prefix='conditions'
            )
        else:
            context['condition_formset'] = InstructionRuleConditionFormSet(prefix='conditions')
        return context

    def form_valid(self, form):
        from .forms import InstructionRuleConditionFormSet
        context = self.get_context_data()
        condition_formset = context['condition_formset']

        form.instance.created_by = self.request.user
        self.object = form.save()

        if condition_formset.is_valid():
            condition_formset.instance = self.object
            condition_formset.save()
        else:
            # Re-render form with errors
            return self.render_to_response(self.get_context_data(form=form))

        messages.success(self.request, "Instruction rule created successfully")
        return redirect(self.success_url)


class InstructionRuleUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an instruction rule with inline conditions.
    """
    model = InstructionRule
    template_name = "workorders/instruction_rule_form.html"
    fields = ['name', 'description', 'instruction_text', 'priority',
              'applies_to_wo_types', 'applies_to_bit_types', 'is_active']
    success_url = reverse_lazy('workorders:instruction_rule_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Rule: {self.object.name}'
        context['wo_type_choices'] = WorkOrder.WOType.choices
        context['bit_type_choices'] = DrillBit.BitCategory.choices

        # Add condition formset
        from .forms import InstructionRuleConditionFormSet
        if self.request.POST:
            context['condition_formset'] = InstructionRuleConditionFormSet(
                self.request.POST, instance=self.object, prefix='conditions'
            )
        else:
            context['condition_formset'] = InstructionRuleConditionFormSet(
                instance=self.object, prefix='conditions'
            )
        return context

    def form_valid(self, form):
        from .forms import InstructionRuleConditionFormSet
        context = self.get_context_data()
        condition_formset = context['condition_formset']

        self.object = form.save()

        if condition_formset.is_valid():
            condition_formset.instance = self.object
            condition_formset.save()
        else:
            # Re-render form with errors
            return self.render_to_response(self.get_context_data(form=form))

        messages.success(self.request, "Instruction rule updated successfully")
        return redirect(self.success_url)


class InstructionRuleDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete an instruction rule.
    """
    model = InstructionRule
    template_name = "workorders/instruction_rule_confirm_delete.html"
    success_url = reverse_lazy('workorders:instruction_rule_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Instruction rule deleted successfully")
        return super().delete(request, *args, **kwargs)


# =============================================================================
# EXPORT VIEWS
# =============================================================================

@login_required
def export_work_orders_excel(request):
    """
    Export work orders to Excel format.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        messages.error(request, "Excel export requires openpyxl library")
        return redirect('workorders:workorder_list_enhanced')

    # Apply same filters as list view
    queryset = WorkOrder.objects.select_related(
        "customer", "drill_bit", "assigned_to", "design"
    ).order_by("-created_at")

    status = request.GET.get("status")
    if status:
        queryset = queryset.filter(status=status)

    wo_type = request.GET.get("wo_type")
    if wo_type:
        queryset = queryset.filter(wo_type=wo_type)

    search = request.GET.get("search")
    if search:
        queryset = queryset.filter(
            Q(wo_number__icontains=search)
            | Q(customer__name__icontains=search)
            | Q(drill_bit__serial_number__icontains=search)
        )

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Work Orders"

    # Headers
    headers = [
        'WO Number', 'Type', 'Status', 'Priority',
        'Serial Number', 'Customer', 'DRSS#', 'Brazing MAT#',
        'Due Date', 'Assigned To', 'Created Date'
    ]

    # Header styling
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')

    # Data rows
    for row_num, wo in enumerate(queryset, 2):
        ws.cell(row=row_num, column=1, value=wo.wo_number)
        ws.cell(row=row_num, column=2, value=wo.get_wo_type_display())
        ws.cell(row=row_num, column=3, value=wo.get_status_display())
        ws.cell(row=row_num, column=4, value=wo.get_priority_display())
        ws.cell(row=row_num, column=5, value=wo.drill_bit.serial_number if wo.drill_bit else '')
        ws.cell(row=row_num, column=6, value=wo.customer.name if wo.customer else '')
        ws.cell(row=row_num, column=7, value=wo.drss_no)
        ws.cell(row=row_num, column=8, value=wo.brazing_mat_no)
        ws.cell(row=row_num, column=9, value=wo.due_date.strftime('%Y-%m-%d') if wo.due_date else '')
        ws.cell(row=row_num, column=10, value=wo.assigned_to.get_full_name() if wo.assigned_to else '')
        ws.cell(row=row_num, column=11, value=wo.created_at.strftime('%Y-%m-%d'))

    # Auto-width columns
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column].width = min(max_length + 2, 50)

    # Freeze header row
    ws.freeze_panes = 'A2'

    # Response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"work_orders_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response
