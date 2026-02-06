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
    RepairEvaluation, WorkOrderCost, ProductionPlanEntry,
    PlannerSettings, PlannerHoliday
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
            "customer", "drill_bit", "assigned_to", "design", "bom", "account"
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

        # Filter by account
        account_id = self.request.GET.get("account")
        if account_id:
            queryset = queryset.filter(account_id=account_id)

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
        from apps.sales.models import Customer, Account
        context["customers"] = Customer.objects.filter(
            work_orders__isnull=False
        ).distinct().order_by('name')
        context["accounts"] = Account.objects.filter(is_active=True).order_by('sort_order')
        context["current_account"] = self.request.GET.get("account", "")

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

        # Cutter evaluations by type (legacy individual variables)
        context["ardt_evaluation"] = wo.cutter_evaluations.filter(
            evaluation_type=CutterEvaluationMatrix.EvaluationType.ARDT
        ).first()
        context["eng_evaluation"] = wo.cutter_evaluations.filter(
            evaluation_type=CutterEvaluationMatrix.EvaluationType.ENGINEER
        ).first()
        context["rework_evaluation"] = wo.cutter_evaluations.filter(
            evaluation_type=CutterEvaluationMatrix.EvaluationType.REWORK
        ).first()

        # Build evaluations list with all types
        eval_types = CutterEvaluationMatrix.EvaluationType.choices
        evaluations = []
        for type_code, type_label in eval_types:
            eval_obj = wo.cutter_evaluations.filter(evaluation_type=type_code).first()
            evaluations.append({
                'type_code': type_code,
                'type_label': type_label,
                'evaluation': eval_obj,
                'exists': eval_obj is not None,
            })
        context['evaluations'] = evaluations

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
            # Build cutter_shapes dict {int(index): base64_data_uri}
            cutter_shapes = {}
            prefix = "data:image/png;base64,"
            raw_shapes = source_data.get("cutter_shapes", {})
            for k, v in raw_shapes.items():
                try:
                    idx = int(k)
                    data = v.get("data", "") if isinstance(v, dict) else (v if isinstance(v, str) else "")
                    # Fix double data-URI prefix
                    while data.startswith(prefix + prefix):
                        data = data[len(prefix):]
                    cutter_shapes[idx] = data
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
        context['cutter_positions'] = list(range(1, max_cutters + 1))
        context['total_grid_height'] = max_blades * 30
        context['action_choices'] = CutterEvaluationEntry.Action.choices
        context['source_choices'] = CutterEvaluationEntry.CutterSource.choices

        # Saved cutters details (from previous save or BOM data)
        context['saved_cutters_details'] = matrix.cutters_details or []

        # BOM lines for pre-populating cutters details (if no saved data)
        import json as _json
        bom_lines_json = []
        active_bom = None
        if wo.bom:
            active_bom = wo.bom
        elif wo.drill_bit:
            active_bom = getattr(wo.drill_bit, 'brazing_bom', None) or getattr(wo.drill_bit, 'bom', None)
        if active_bom:
            for line in active_bom.lines.select_related('inventory_item').order_by('order_number', 'line_number'):
                part_no = line.hdbs_code or ''
                desc = ''
                if line.inventory_item:
                    part_no = part_no or line.inventory_item.mat_number or line.inventory_item.code
                    desc = line.inventory_item.name
                else:
                    desc = line.cutter_type or ''
                bom_lines_json.append({
                    'qty': line.quantity,
                    'size_mm': line.cutter_size or '',
                    'part_no': part_no,
                    'description': desc,
                    'remarks': '',
                })
        context['bom_lines_json'] = _json.dumps(bom_lines_json)

        # Cutter state history: all prior evaluations for this WO
        prior_evals = wo.cutter_evaluations.exclude(pk=matrix.pk).order_by(
            'evaluation_type', 'evaluation_number'
        ).prefetch_related('entries')
        eval_history = []
        for ev in prior_evals:
            eval_history.append({
                'type': ev.get_evaluation_type_display(),
                'number': ev.evaluation_number,
                'decision': ev.get_decision_display() if ev.decision else '',
                'date': ev.evaluated_at.isoformat() if ev.evaluated_at else '',
                'entry_count': ev.entries.count(),
            })
        context['eval_history'] = eval_history

        # Build cumulative cutter state from all prior evaluations
        # Track per position: last action across all evaluations
        cutter_state = {}
        all_evals_ordered = wo.cutter_evaluations.order_by('created_at').prefetch_related('entries')
        for ev in all_evals_ordered:
            if ev.pk == matrix.pk:
                continue
            for entry in ev.entries.all():
                key = (entry.blade_number, entry.cutter_position)
                if entry.action:
                    prev = cutter_state.get(key, {})
                    history = prev.get('history', [])
                    history.append({
                        'eval_type': ev.get_evaluation_type_display(),
                        'action': entry.action,
                    })
                    cutter_state[key] = {
                        'last_action': entry.action,
                        'history': history,
                    }
        # Convert tuple keys to string for JSON serialization
        cutter_state_serializable = {}
        for (blade, pos), val in cutter_state.items():
            cutter_state_serializable[f"{blade},{pos}"] = val
        context['cutter_state_json'] = _json.dumps(cutter_state_serializable)

        return context

    def post(self, request, *args, **kwargs):
        """Handle grid updates via AJAX — supports both single-cell and bulk JSON."""
        matrix = get_object_or_404(CutterEvaluationMatrix, pk=kwargs['pk'])

        content_type = request.content_type or ''
        if 'application/json' in content_type:
            import json
            data = json.loads(request.body)
            entries_data = data.get('entries', [])
            remarks = data.get('remarks', '')
            decision = data.get('decision', '')
            cutters_details = data.get('cutters_details', None)

            # Clear existing entries and re-create
            matrix.entries.all().delete()
            for e in entries_data:
                CutterEvaluationEntry.objects.create(
                    matrix=matrix,
                    blade_number=e['blade'],
                    cutter_position=e['position'],
                    action=e.get('action', ''),
                )

            # Update matrix fields
            matrix.general_remark = remarks
            matrix.decision = decision
            if cutters_details is not None:
                matrix.cutters_details = cutters_details
            matrix.save(update_fields=['general_remark', 'decision', 'cutters_details', 'updated_at'])

            return JsonResponse({'success': True, 'count': len(entries_data)})

        # Legacy single-cell POST
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

        # If no entries exist, create from the appropriate ProcessRoute
        if not entries:
            route = self._get_route_for_wo(wo)
            if route:
                for op in route.operations.order_by('sequence'):
                    RouterSheetEntry.objects.get_or_create(
                        work_order=wo,
                        step_number=op.sequence,
                        defaults={
                            'step_description': op.operation_name,
                        }
                    )
                entries = list(wo.router_entries.order_by('step_number'))

        context['entries'] = entries

        # Generate WO QR for scanning
        base_url = getattr(settings, "SITE_URL", None)
        context['wo_qr'] = generate_work_order_qr(wo, base_url)

        return context

    def _get_route_for_wo(self, wo):
        """Find the appropriate ProcessRoute for this work order."""
        # Determine workflow type from account
        is_manufacture = False
        if wo.account:
            if wo.account.workflow_type == 'MANUFACTURE':
                is_manufacture = True
            elif wo.account.code in ('L3', 'L4'):
                is_manufacture = True

        # Also check WO type
        if wo.wo_type in ('FC_NEW', 'RC_NEW'):
            is_manufacture = True

        if is_manufacture:
            route = ProcessRoute.objects.filter(
                route_number='RT-FC-MANUFACTURE', is_active=True
            ).first()
        else:
            route = ProcessRoute.objects.filter(
                route_number='RT-FC-REPAIR', is_active=True
            ).first()

        return route


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


@login_required
def api_router_step_scan(request, wo_pk, step_number):
    """
    API endpoint for QR scan - start/complete a router step.
    Returns JSON response for HTMX/fetch usage.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    wo = get_object_or_404(WorkOrder, pk=wo_pk)
    entry = get_object_or_404(RouterSheetEntry, work_order=wo, step_number=step_number)

    action = request.POST.get('action', 'start')
    station_qr = request.POST.get('station_qr', '')

    if action == 'start':
        if entry.qr_scan_start:
            return JsonResponse({'error': 'Step already started', 'success': False})
        entry.qr_scan_start = timezone.now()
        entry.operator = request.user
        entry.station_qr = station_qr
        entry.save()
        return JsonResponse({
            'success': True,
            'step_number': step_number,
            'action': 'started',
            'started_at': entry.qr_scan_start.isoformat(),
            'operator': request.user.get_short_name() or request.user.username,
        })
    elif action == 'end':
        if not entry.qr_scan_start:
            return JsonResponse({'error': 'Step not started yet', 'success': False})
        if entry.is_complete:
            return JsonResponse({'error': 'Step already completed', 'success': False})
        entry.qr_scan_end = timezone.now()
        entry.is_complete = True
        entry.save()
        return JsonResponse({
            'success': True,
            'step_number': step_number,
            'action': 'completed',
            'completed_at': entry.qr_scan_end.isoformat(),
            'duration_minutes': entry.duration_minutes,
        })
    elif action == 'skip':
        entry.is_complete = True
        entry.save()
        return JsonResponse({
            'success': True,
            'step_number': step_number,
            'action': 'skipped',
        })

    return JsonResponse({'error': f'Unknown action: {action}', 'success': False})


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


# =============================================================================
# PRODUCTION PLANNER - WIP Dashboard with Real-time Updates
# =============================================================================

class ProductionPlannerView(LoginRequiredMixin, TemplateView):
    """
    Production Planner Dashboard - Excel BITS TRACKING style WIP view.
    Shows planned bits (no WO), work-in-progress, and completed items.
    Allows adding bits to plan without creating Work Orders.
    """
    template_name = "workorders/production_planner.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.sales.models import Account

        # Get all active accounts
        accounts = Account.objects.filter(is_active=True).order_by('sort_order', 'code')

        # Get filter parameters
        account_filter = self.request.GET.get('account')
        status_filter = self.request.GET.get('status', 'planned')  # planned, wip, completed, all

        # Build WIP queryset - work orders in progress
        wip_statuses = [
            WorkOrder.Status.RELEASED,
            WorkOrder.Status.IN_PROGRESS,
            WorkOrder.Status.QC_PENDING,
        ]

        completed_statuses = [
            WorkOrder.Status.QC_PASSED,
            WorkOrder.Status.COMPLETED,
        ]

        # ========================================
        # PLANNED ENTRIES (No WO yet)
        # ========================================
        planned_qs = ProductionPlanEntry.objects.filter(
            status=ProductionPlanEntry.Status.PLANNED
        ).select_related(
            'drill_bit', 'drill_bit__design', 'account', 'created_by'
        ).order_by('sequence', '-priority', 'planned_date')

        if account_filter:
            planned_qs = planned_qs.filter(account__code=account_filter)

        planned_data = []
        for entry in planned_qs:
            bit = entry.drill_bit
            # Calculate is_overdue
            is_overdue = False
            if entry.due_date:
                is_overdue = entry.due_date < timezone.now().date()
            planned_data.append({
                'entry': entry,
                'serial': bit.serial_number,
                'size': bit.size,
                'type': bit.design.hdbs_type if bit.design else '-',
                'mat_no': bit.mat_number or (bit.design.mat_no if bit.design else '-'),
                'received_date': bit.received_date,
                'account': entry.account.code if entry.account else (bit.account.code if bit.account else '-'),
                'priority': entry.get_priority_display(),
                'planned_date': entry.planned_date,
                'due_date': entry.due_date,
                'is_overdue': is_overdue,
                'notes': entry.notes,
                'intended_type': entry.get_intended_wo_type_display() if entry.intended_wo_type else '-',
            })

        context['planned_data'] = planned_data
        context['total_planned'] = len(planned_data)

        # ========================================
        # WIP / COMPLETED (Work Orders)
        # ========================================
        # Base queryset with all required relations
        base_qs = WorkOrder.objects.select_related(
            'drill_bit', 'drill_bit__design', 'account', 'customer',
            'brazing_bom', 'system_bom', 'assigned_to'
        ).prefetch_related(
            'router_sheet_entries'
        ).order_by('-created_at')

        # Apply account filter
        if account_filter:
            base_qs = base_qs.filter(account__code=account_filter)

        # Apply status filter for WO-based data
        if status_filter == 'wip':
            work_orders = base_qs.filter(status__in=wip_statuses)
        elif status_filter == 'completed':
            work_orders = base_qs.filter(status__in=completed_statuses)
        elif status_filter == 'planned':
            work_orders = WorkOrder.objects.none()  # No WOs for planned view
        else:  # all
            work_orders = base_qs.exclude(status=WorkOrder.Status.CANCELLED)

        # Build WIP data with process step tracking
        wip_data = []
        for wo in work_orders:
            # Get router sheet progress
            router_entries = wo.router_sheet_entries.all().order_by('step_number')
            total_steps = router_entries.count()
            completed_steps = router_entries.filter(
                qr_scan_end__isnull=False
            ).count()
            current_step = router_entries.filter(
                qr_scan_start__isnull=False,
                qr_scan_end__isnull=True
            ).first()

            # Calculate progress percentage
            progress = int((completed_steps / total_steps * 100)) if total_steps > 0 else 0

            # Estimate completion based on remaining steps and average duration
            estimated_completion = None
            if current_step and wo.drill_bit and wo.drill_bit.design:
                # Get process route for this design/account
                route = ProcessRoute.objects.filter(
                    accounts=wo.account,
                    workflow_type=wo.account.workflow_type if wo.account else ProcessRoute.WorkflowType.REPAIR
                ).first()
                if route and route.estimated_duration_hours:
                    remaining_hours = route.estimated_duration_hours * (1 - progress / 100)
                    estimated_completion = timezone.now() + timedelta(hours=remaining_hours)

            # Get step status for key process steps (matching Excel columns)
            step_status = {}
            key_steps = [
                ('buildup', 'Build Up'),
                ('braze', 'Braze'),
                ('grinding', 'Final grinding'),
                ('tip_grinding', 'Tip Grinding'),
                ('qc', '1st check'),
                ('thread_clean', 'Thread Cleaning'),
                ('body_clean', 'Body Cleaning'),
                ('usr', 'USR'),
                ('final', 'Final Inspection'),
            ]
            for step_key, step_name in key_steps:
                # Find matching router entry
                entry = router_entries.filter(
                    Q(step_name__icontains=step_name) |
                    Q(step_name__icontains=step_key)
                ).first()
                if entry:
                    if entry.qr_scan_end:
                        step_status[step_key] = 'done'
                    elif entry.qr_scan_start:
                        step_status[step_key] = 'active'
                    else:
                        step_status[step_key] = 'pending'
                else:
                    step_status[step_key] = 'na'

            wip_data.append({
                'wo': wo,
                'serial': wo.drill_bit.serial_number if wo.drill_bit else '-',
                'size': wo.drill_bit.size if wo.drill_bit else '-',
                'type': wo.drill_bit.design.hdbs_type if wo.drill_bit and wo.drill_bit.design else '-',
                'mat_no': wo.brazing_mat_no or wo.system_mat_no or '-',
                'received_date': wo.actual_start.date() if wo.actual_start else (wo.created_at.date() if wo.created_at else None),
                'account': wo.account.code if wo.account else '-',
                'status': wo.get_status_display(),
                'progress': progress,
                'current_step': current_step.step_name if current_step else None,
                'estimated_completion': estimated_completion,
                'step_status': step_status,
                'completed_steps': completed_steps,
                'total_steps': total_steps,
            })

        # Group by account for the tabs
        wip_by_account = {}
        for item in wip_data:
            acct = item['account']
            if acct not in wip_by_account:
                wip_by_account[acct] = []
            wip_by_account[acct].append(item)

        # Summary statistics
        context['accounts'] = accounts
        context['wip_data'] = wip_data
        context['wip_by_account'] = wip_by_account
        context['total_wip'] = len([w for w in wip_data if w['wo'].status in [s.value for s in wip_statuses]])
        context['completed_today'] = WorkOrder.objects.filter(
            status=WorkOrder.Status.COMPLETED,
            actual_end__date=timezone.now().date()
        ).count()

        # Filter state
        context['current_account'] = account_filter
        context['current_status'] = status_filter

        # Account summaries for quick stats (includes both planned and WIP)
        account_summary = []
        for acct in accounts:
            # Count WIP work orders
            wip_count = WorkOrder.objects.filter(
                account=acct,
                status__in=wip_statuses
            ).count()
            # Count planned entries (no WO yet)
            planned_count = ProductionPlanEntry.objects.filter(
                account=acct,
                status=ProductionPlanEntry.Status.PLANNED
            ).count()
            total_count = wip_count + planned_count
            if total_count > 0:
                account_summary.append({
                    'code': acct.code,
                    'name': acct.name,
                    'wip_count': wip_count,
                    'planned_count': planned_count,
                    'total_count': total_count,
                })
        context['account_summary'] = account_summary

        context['page_title'] = 'Production Planner'
        return context


@login_required
def api_production_wip_status(request):
    """
    API endpoint for real-time WIP status updates.
    Returns JSON with current WIP counts and active step for each work order.
    Used for polling/WebSocket updates.
    """
    wip_statuses = [
        WorkOrder.Status.RELEASED,
        WorkOrder.Status.IN_PROGRESS,
        WorkOrder.Status.QC_PENDING,
    ]

    work_orders = WorkOrder.objects.filter(
        status__in=wip_statuses
    ).select_related('drill_bit', 'account').prefetch_related('router_sheet_entries')

    data = []
    for wo in work_orders:
        router_entries = wo.router_sheet_entries.all()
        total = router_entries.count()
        completed = router_entries.filter(qr_scan_end__isnull=False).count()
        current = router_entries.filter(
            qr_scan_start__isnull=False,
            qr_scan_end__isnull=True
        ).first()

        data.append({
            'wo_id': wo.pk,
            'wo_number': wo.wo_number,
            'serial': wo.drill_bit.serial_number if wo.drill_bit else None,
            'account': wo.account.code if wo.account else None,
            'status': wo.status,
            'progress': int((completed / total * 100)) if total > 0 else 0,
            'current_step': current.step_name if current else None,
            'completed_steps': completed,
            'total_steps': total,
        })

    return JsonResponse({'wip': data, 'timestamp': timezone.now().isoformat()})


class ProductionPlannerCreateWOView(LoginRequiredMixin, TemplateView):
    """
    Quick Work Order creation from Production Planner.
    Lookup by serial number to auto-populate account, design level (L3/L4).
    """
    template_name = "workorders/production_planner_create_wo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.sales.models import Account

        context['accounts'] = Account.objects.filter(is_active=True).order_by('sort_order', 'code')
        context['page_title'] = 'Create Work Order from Planner'
        return context

    def post(self, request, *args, **kwargs):
        from apps.sales.models import Account

        serial_number = request.POST.get('serial_number', '').strip()
        account_code = request.POST.get('account')

        # Lookup existing drill bit
        drill_bit = DrillBit.objects.filter(serial_number=serial_number).first()

        if drill_bit:
            # Drill bit exists - use its account (first time) or provided account
            account = drill_bit.account
            if not account and account_code:
                account = Account.objects.filter(code=account_code).first()
                # Set account on drill bit for first time
                if account:
                    drill_bit.account = account
                    drill_bit.save(update_fields=['account'])
        else:
            # New drill bit - require account
            if not account_code:
                messages.error(request, 'Account is required for new drill bits.')
                return redirect('workorders:production_planner_create_wo')
            account = Account.objects.filter(code=account_code).first()

        if not account:
            messages.error(request, 'Invalid account selected.')
            return redirect('workorders:production_planner_create_wo')

        # Determine WO type based on design level and workflow
        wo_type = WorkOrder.WOType.FC_REPAIR
        if account.workflow_type == 'MANUFACTURE':
            if drill_bit and drill_bit.design:
                level = getattr(drill_bit.design, 'level', 'L3')
                if level == 'L4':
                    wo_type = WorkOrder.WOType.FC_REWORK
                else:
                    wo_type = WorkOrder.WOType.FC_NEW

        # Generate WO number
        wo_number = account.generate_wo_number()

        # Create work order
        wo = WorkOrder.objects.create(
            wo_number=wo_number,
            wo_type=wo_type,
            drill_bit=drill_bit,
            design=drill_bit.design if drill_bit else None,
            account=account,
            status=WorkOrder.Status.DRAFT,
            created_by=request.user,
        )

        messages.success(request, f'Work Order {wo_number} created successfully.')
        return redirect('workorders:workorder_detail_enhanced', pk=wo.pk)


# =============================================================================
# PRODUCTION PLAN API ENDPOINTS
# =============================================================================

@login_required
def api_add_to_plan(request):
    """
    API endpoint to add a drill bit to the production plan.
    POST body: { serial_number, account, priority, planned_date, intended_wo_type, notes }
    """
    import json
    from apps.sales.models import Account

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    serial_number = data.get('serial_number', '').strip()
    if not serial_number:
        return JsonResponse({'success': False, 'error': 'Serial number required'})

    # Find the drill bit
    drill_bit = DrillBit.objects.filter(serial_number=serial_number).first()
    if not drill_bit:
        return JsonResponse({'success': False, 'error': 'Drill bit not found'})

    # Get account
    account = None
    account_code = data.get('account', '').strip()
    if account_code:
        account = Account.objects.filter(code=account_code).first()
    elif drill_bit.account:
        account = drill_bit.account

    # Parse due_date if provided
    due_date_str = data.get('due_date', '')
    due_date = None
    if due_date_str:
        try:
            from datetime import datetime
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass  # Will auto-calculate

    # Add to plan
    try:
        entry, created = ProductionPlanEntry.add_to_plan(
            drill_bit=drill_bit,
            account=account,
            priority=data.get('priority', 'NORMAL'),
            planned_date=data.get('planned_date') or None,
            due_date=due_date,
            intended_wo_type=data.get('intended_wo_type', ''),
            notes=data.get('notes', ''),
            user=request.user
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Database error: {str(e)}'
        }, status=500)

    if not created:
        return JsonResponse({
            'success': False,
            'error': 'This drill bit is already in the plan'
        })

    return JsonResponse({
        'success': True,
        'entry_id': entry.pk,
        'serial_number': serial_number,
        'message': f'Added {serial_number} to production plan'
    })


@login_required
def api_create_wo_from_plan(request):
    """
    API endpoint to create a Work Order from a production plan entry.
    POST with ?entry_id=X
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    entry_id = request.GET.get('entry_id')
    if not entry_id:
        return JsonResponse({'success': False, 'error': 'entry_id required'})

    try:
        entry = ProductionPlanEntry.objects.select_related('drill_bit', 'account').get(pk=entry_id)
    except ProductionPlanEntry.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plan entry not found'})

    if entry.status != ProductionPlanEntry.Status.PLANNED:
        return JsonResponse({'success': False, 'error': 'Entry already has a Work Order'})

    # Create the work order
    try:
        wo = entry.create_work_order(user=request.user)
        return JsonResponse({
            'success': True,
            'wo_id': wo.pk,
            'wo_number': wo.wo_number,
            'redirect_url': reverse('workorders:workorder_detail_enhanced', args=[wo.pk])
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_remove_from_plan(request):
    """
    API endpoint to remove a drill bit from the production plan.
    POST with ?entry_id=X
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    entry_id = request.GET.get('entry_id')
    if not entry_id:
        return JsonResponse({'success': False, 'error': 'entry_id required'})

    try:
        entry = ProductionPlanEntry.objects.get(pk=entry_id)
    except ProductionPlanEntry.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plan entry not found'})

    if entry.status == ProductionPlanEntry.Status.WO_CREATED:
        return JsonResponse({'success': False, 'error': 'Cannot remove - Work Order already created'})

    # Mark as removed (soft delete)
    entry.status = ProductionPlanEntry.Status.REMOVED
    entry.save(update_fields=['status', 'updated_at'])

    return JsonResponse({
        'success': True,
        'message': 'Removed from plan'
    })


# =============================================================================
# PLANNER SETTINGS - Due Date Configuration
# =============================================================================

class PlannerSettingsView(LoginRequiredMixin, TemplateView):
    """
    Control page for Production Planner settings.
    Manage due date calculation, weekends, and holidays.
    """
    template_name = "workorders/planner_settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get singleton settings
        settings_obj = PlannerSettings.get_settings()

        # Get upcoming holidays
        today = timezone.now().date()
        upcoming_holidays = PlannerHoliday.objects.filter(
            date__gte=today,
            is_active=True
        ).order_by('date')[:20]

        # All holidays for editing
        all_holidays = PlannerHoliday.objects.all().order_by('-date')

        context['settings'] = settings_obj
        context['upcoming_holidays'] = upcoming_holidays
        context['all_holidays'] = all_holidays
        context['page_title'] = 'Planner Settings'

        # Day options for weekend selector
        context['day_options'] = [
            (0, 'Monday'),
            (1, 'Tuesday'),
            (2, 'Wednesday'),
            (3, 'Thursday'),
            (4, 'Friday'),
            (5, 'Saturday'),
            (6, 'Sunday'),
        ]

        return context

    def post(self, request, *args, **kwargs):
        """Handle settings update."""
        import json

        settings_obj = PlannerSettings.get_settings()

        # Update due days settings
        default_due_days = request.POST.get('default_due_days')
        ur_due_days = request.POST.get('ur_due_days')

        if default_due_days:
            try:
                settings_obj.default_due_days = int(default_due_days)
            except ValueError:
                pass

        if ur_due_days:
            try:
                settings_obj.ur_due_days = int(ur_due_days)
            except ValueError:
                pass

        # Update weekend days
        weekend_days = request.POST.getlist('weekend_days')
        settings_obj.weekend_days = [int(d) for d in weekend_days]

        settings_obj.updated_by = request.user
        settings_obj.save()

        messages.success(request, 'Planner settings updated successfully.')
        return redirect('workorders:planner_settings')


@login_required
def api_add_holiday(request):
    """API endpoint to add a new holiday."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    date_str = data.get('date', '')
    name = data.get('name', '').strip()

    if not date_str or not name:
        return JsonResponse({'success': False, 'error': 'Date and name are required'})

    try:
        from datetime import datetime
        holiday_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid date format'})

    # Check for duplicate
    if PlannerHoliday.objects.filter(date=holiday_date).exists():
        return JsonResponse({'success': False, 'error': 'Holiday already exists for this date'})

    holiday = PlannerHoliday.objects.create(
        date=holiday_date,
        name=name,
        created_by=request.user
    )

    return JsonResponse({
        'success': True,
        'holiday_id': holiday.pk,
        'message': f'Added holiday: {name}'
    })


@login_required
def api_delete_holiday(request, pk):
    """API endpoint to delete a holiday."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    try:
        holiday = PlannerHoliday.objects.get(pk=pk)
        holiday_name = holiday.name
        holiday.delete()
        return JsonResponse({
            'success': True,
            'message': f'Deleted holiday: {holiday_name}'
        })
    except PlannerHoliday.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Holiday not found'})


@login_required
def api_toggle_holiday(request, pk):
    """API endpoint to toggle holiday active status."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    try:
        holiday = PlannerHoliday.objects.get(pk=pk)
        holiday.is_active = not holiday.is_active
        holiday.save(update_fields=['is_active'])
        return JsonResponse({
            'success': True,
            'is_active': holiday.is_active,
            'message': f'Holiday {"enabled" if holiday.is_active else "disabled"}'
        })
    except PlannerHoliday.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Holiday not found'})


@login_required
def api_preview_due_date(request):
    """API endpoint to preview due date calculation."""
    account_code = request.GET.get('account', '')
    today = timezone.now().date()

    due_date = PlannerSettings.calculate_due_date(
        start_date=today,
        account_code=account_code if account_code else None
    )

    # Get settings for display
    settings_obj = PlannerSettings.get_settings()
    days_used = settings_obj.ur_due_days if account_code == 'UR' else settings_obj.default_due_days

    return JsonResponse({
        'success': True,
        'start_date': today.strftime('%Y-%m-%d'),
        'due_date': due_date.strftime('%Y-%m-%d'),
        'due_date_display': due_date.strftime('%b %d, %Y'),
        'working_days': days_used,
        'account': account_code or 'Default'
    })
