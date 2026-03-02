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

import json as _json
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, Count, Sum, F, Max
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView, TemplateView, View
)

from .models import (
    WorkOrder, DrillBit, BitEvent, Location,
    CutterEvaluationMatrix, CutterEvaluationEntry, ReceivingInspection,
    ReceivingInspectionAttachment,
    RouterSheetEntry, EvaluationChecklist,
    LPTReport, APIThreadInspection,
    InstructionRule, InstructionRuleCondition,
    ProcessRoute, ProcessRouteOperation,
    RepairEvaluation, WorkOrderCost, ProductionPlanEntry,
    PlannerSettings, PlannerHoliday,
    EvaluationRoute, EvaluationRouteStep
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

        # Build evaluations list
        account_code = wo.account.code if wo.account else ''
        is_new_bit = wo.wo_type in [WorkOrder.WOType.FC_NEW, WorkOrder.WOType.RC_NEW]
        is_ur = account_code == 'UR'
        is_aramco = account_code == 'ARAMCO'

        # Try to get configured evaluation route for this WO
        # Wrapped in try/except to handle case where evaluation_routes table
        # doesn't exist (migration not applied or database sync issue)
        try:
            evaluation_route = EvaluationRoute.get_route_for_workorder(wo)
        except Exception:
            # Table doesn't exist or other DB error - fall back to legacy
            evaluation_route = None

        evaluations = []

        if evaluation_route:
            # Use configured route steps
            context['evaluation_route'] = evaluation_route
            for step in evaluation_route.steps.all().order_by('order'):
                eval_obj = wo.cutter_evaluations.filter(evaluation_type=step.evaluation_type).first()
                evaluations.append({
                    'type_code': step.evaluation_type,
                    'type_label': step.get_evaluation_type_display(),
                    'evaluation': eval_obj,
                    'exists': eval_obj is not None,
                    'entry_count': len(eval_obj.entries.all()) if eval_obj else 0,
                    'help_text': step.condition_description if step.is_conditional else '',
                    'is_na': False,
                    'is_required': step.is_required,
                    'is_conditional': step.is_conditional,
                    'show_decision_field': step.show_decision_field,
                    'show_cutter_matrix': step.show_cutter_matrix,
                    'show_cutters_details': step.show_cutters_details,
                })
        else:
            # Fallback: Legacy hardcoded flow
            context['evaluation_route'] = None
            eval_flow = [
                # (type_code, type_label, show_condition, help_text)
                ('PDC_EVAL', 'PDC Evaluation', True, 'Starting point - includes Die Check + E-Checklist'),
                ('ARDT', 'ARDT Evaluation (Legacy)', False, 'Legacy - use PDC Evaluation'),
                ('QC', 'QC Evaluation', not is_new_bit, 'N/A for new bits, required for repair'),
                ('ENGINEER', 'Technical Rep. Evaluation', not is_new_bit and not is_ur and not is_aramco, 'N/A for new bits, UR, or Aramco'),
                ('ARAMCO_REP', 'Aramco Rep. Evaluation', is_aramco, 'Aramco inspector evaluation'),
                ('DIE_CHECK', 'Die Check', True, 'Pre-processing die check'),
                ('FINAL_DIE_CHECK', 'Final Die Check', True, 'Post-processing die check'),
                ('FINAL_QC', 'Final QC Evaluation', True, 'Final quality check'),
                ('FINAL_INSPECTION', 'Final Inspection', True, 'Final sign-off'),
                ('REWORK', 'Rework Evaluation', False, 'Only shown when rework is needed'),
                ('RECEIVING', 'Receiving Evaluation', False, 'Component receiving - tracked separately'),
            ]

            for type_code, type_label, show_by_default, help_text in eval_flow:
                eval_obj = wo.cutter_evaluations.filter(evaluation_type=type_code).first()
                show = show_by_default or (eval_obj is not None)
                if show:
                    evaluations.append({
                        'type_code': type_code,
                        'type_label': type_label,
                        'evaluation': eval_obj,
                        'exists': eval_obj is not None,
                        'entry_count': len(eval_obj.entries.all()) if eval_obj else 0,
                        'help_text': help_text,
                        'is_na': not show_by_default and eval_obj is None,
                        'is_required': True,
                        'is_conditional': False,
                        'show_decision_field': True,
                        'show_cutter_matrix': True,
                        'show_cutters_details': True,
                    })

        context['evaluations'] = evaluations
        context['is_new_bit'] = is_new_bit
        context['is_ur'] = is_ur
        context['is_aramco'] = is_aramco

        # Evaluation progress summary
        total_evals = len([e for e in evaluations if not e.get('is_na')])
        complete_evals = len([e for e in evaluations if e.get('exists') and e['evaluation'].is_complete])
        context['eval_progress'] = {
            'total': total_evals,
            'complete': complete_evals,
            'percent': round(complete_evals * 100 / total_evals) if total_evals > 0 else 0,
        }

        # Receiving inspection (from drill bit, if linked)
        if wo.drill_bit_id:
            context['receiving_inspection'] = ReceivingInspection.objects.filter(
                drill_bit_id=wo.drill_bit_id
            ).select_related('inspected_by').first()
        else:
            context['receiving_inspection'] = None

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

        # Status transitions — StatusTransitionLog removed (Feb 2026), was never written to
        context["status_history"] = []

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

        condition = self.request.GET.get("condition")
        if condition:
            queryset = queryset.filter(condition=condition)

        ownership = self.request.GET.get("ownership")
        if ownership:
            queryset = queryset.filter(ownership=ownership)

        bit_type = self.request.GET.get("bit_type")
        if bit_type:
            queryset = queryset.filter(bit_type=bit_type)

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
        context["condition_choices"] = DrillBit.Condition.choices
        context["ownership_choices"] = DrillBit.Ownership.choices
        context["bit_type_choices"] = DrillBit.BitCategory.choices

        context["current_status"] = self.request.GET.get("status", "")
        context["current_condition"] = self.request.GET.get("condition", "")
        context["current_ownership"] = self.request.GET.get("ownership", "")
        context["current_bit_type"] = self.request.GET.get("bit_type", "")
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
            "work_orders", "evaluations", "bit_events",
            "receiving_inspections", "receiving_inspections__inspected_by",
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

        # Evaluations
        context["evaluations"] = bit.evaluations.order_by('-evaluation_date')

        # Receiving Inspections
        context["receiving_inspections"] = bit.receiving_inspections.order_by('-inspection_date')

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

            # Build grid data with row-aligned virtual columns
            # Pads shorter blades so R2 cutters always appear after R1 separator
            from collections import defaultdict
            pocket_list = list(pockets)

            blade_row_counts = defaultdict(int)
            for p in pocket_list:
                blade_row_counts[(p.blade_number, p.row_number)] += 1

            all_blades = sorted(set(p.blade_number for p in pocket_list))
            all_rows = sorted(set(p.row_number for p in pocket_list))

            row_max = {}
            for rn in all_rows:
                row_max[rn] = max(
                    blade_row_counts.get((bn, rn), 0) for bn in all_blades
                )

            row_start = {}
            off = 1
            for rn in all_rows:
                row_start[rn] = off
                off += row_max[rn]

            row_separators = []
            cum = 0
            for rn in all_rows[:-1]:
                cum += row_max[rn]
                row_separators.append(cum)

            grid_data = {}
            location_data = {}
            engagement_data = {}
            for p in pocket_list:
                vcol = row_start[p.row_number] + p.position_in_row - 1
                key = f"{p.blade_number}_{vcol}"
                grid_data[key] = p.pocket_config_id
                if p.blade_location:
                    location_data[key] = p.blade_location
                if p.engagement_order:
                    engagement_data[key] = p.engagement_order

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
            context['pocket_layout'] = wo.design.pockets.order_by('blade_number', 'row_number', 'position_in_row')

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
                max_cutters = max(p.position_in_blade for p in pockets)

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
        # Use json.dumps for safe JS embedding (not Python repr)
        context['saved_cutters_details'] = _json.dumps(matrix.cutters_details or [])

        # BOM lines for pre-populating cutters details (if no saved data)
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

        # Dynamic row range for cutters details table
        num_detail_rows = max(10, len(bom_lines_json), len(matrix.cutters_details or []))
        context['cutter_detail_row_range'] = range(1, num_detail_rows + 1)

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
            data = _json.loads(request.body)
            entries_data = data.get('entries', [])
            remarks = data.get('remarks', '')
            decision = data.get('decision', '')
            cutters_details = data.get('cutters_details', None)
            mark_complete = data.get('mark_complete', None)

            with transaction.atomic():
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
                update_fields = ['general_remark', 'decision', 'cutters_details', 'updated_at']
                matrix.general_remark = remarks
                matrix.decision = decision
                if cutters_details is not None:
                    matrix.cutters_details = cutters_details

                # Mark complete / reopen support
                if mark_complete is True:
                    matrix.is_complete = True
                    matrix.qc_by = request.user
                    matrix.qc_at = timezone.now()
                    update_fields.extend(['is_complete', 'qc_by', 'qc_at'])
                elif mark_complete is False:
                    matrix.is_complete = False
                    update_fields.append('is_complete')

                matrix.save(update_fields=update_fields)

            return JsonResponse({
                'success': True,
                'count': len(entries_data),
                'is_complete': matrix.is_complete,
            })

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


@login_required
@require_POST
def api_evaluation_mark_complete(request, wo_pk, pk):
    """Toggle is_complete on a CutterEvaluationMatrix. Sets qc_by/qc_at on first completion."""
    matrix = get_object_or_404(CutterEvaluationMatrix, pk=pk, work_order_id=wo_pk)
    data = _json.loads(request.body) if request.body else {}
    mark_complete = data.get('mark_complete', True)

    with transaction.atomic():
        matrix.is_complete = bool(mark_complete)
        update_fields = ['is_complete', 'updated_at']
        if mark_complete and not matrix.qc_by:
            matrix.qc_by = request.user
            matrix.qc_at = timezone.now()
            update_fields.extend(['qc_by', 'qc_at'])
        elif not mark_complete:
            # Reopen — keep qc_by/qc_at as audit trail
            pass
        matrix.save(update_fields=update_fields)

    return JsonResponse({
        'success': True,
        'is_complete': matrix.is_complete,
        'qc_by': str(matrix.qc_by) if matrix.qc_by else None,
        'qc_at': matrix.qc_at.isoformat() if matrix.qc_at else None,
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

        # Track item timestamps for auditing
        old_instance = EvaluationChecklist.objects.filter(pk=form.instance.pk).first()
        item_timestamps = form.instance.item_timestamps or {}
        now = timezone.now().isoformat()

        # Check which fields changed and update their timestamps
        checklist_fields = [
            'bit_cleanliness', 'paperwork', 'bit_stamping', 'die_check',
            'ring_gauge_go', 'ring_gauge_no_go', 'nozzle_bore_liner', 'nozzle_threads',
            'apex', 'junk_slot', 'breaker_slot', 'body_condition',
            'mud_seal_surface', 'api_pin', 'inner_diameter', 'overall_pass'
        ]
        for field in checklist_fields:
            new_value = form.cleaned_data.get(field)
            old_value = getattr(old_instance, field, '') if old_instance else ''
            if new_value and new_value != old_value:
                item_timestamps[field] = now

        form.instance.item_timestamps = item_timestamps
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

        # Build WIP queryset - all active work orders that block new WO creation
        # These statuses from DrillBit.ACTIVE_WO_STATUSES must be visible so users
        # can manage them (prevents "phantom" blocking WOs that can't be found)
        wip_statuses = [
            WorkOrder.Status.DRAFT,
            WorkOrder.Status.PLANNED,
            WorkOrder.Status.RELEASED,
            WorkOrder.Status.IN_PROGRESS,
            WorkOrder.Status.ON_HOLD,
            WorkOrder.Status.QC_PENDING,
            WorkOrder.Status.QC_FAILED,
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
            'router_entries'
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
            router_entries = wo.router_entries.all().order_by('step_number')
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
                    Q(step_description__icontains=step_name) |
                    Q(step_description__icontains=step_key)
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
                'current_step': current_step.step_description if current_step else None,
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
    ).select_related('drill_bit', 'account').prefetch_related('router_entries')

    data = []
    for wo in work_orders:
        router_entries = wo.router_entries.all()
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
            'current_step': current.step_description if current else None,
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

    # Add to plan (returns 4-tuple: entry, created, error_code, error_message)
    try:
        entry, created, error_code, error_message = ProductionPlanEntry.add_to_plan(
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
            'error': error_message or 'This drill bit is already in the plan',
            'error_code': error_code or 'IN_PLAN'
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

    # Create the work order (returns 4-tuple: wo, success, error_code, error_message)
    try:
        wo, success, error_code, error_message = entry.create_work_order(user=request.user)

        if not success:
            response = {
                'success': False,
                'error': error_message or 'Failed to create work order',
                'error_code': error_code or 'UNKNOWN'
            }
            # If blocked by existing WO, include link to it
            if error_code == 'ACTIVE_WO' and wo:
                response['blocking_wo_id'] = wo.pk
                response['blocking_wo_number'] = wo.wo_number
                response['blocking_wo_url'] = reverse('workorders:workorder_detail_enhanced', args=[wo.pk])
            return JsonResponse(response)

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


# =============================================================================
# EVALUATION ROUTE BUILDER
# =============================================================================

class EvaluationRouteBuilderView(LoginRequiredMixin, TemplateView):
    """
    Dashboard to configure evaluation routes for different account + bit type combinations.
    Allows drag-and-drop arrangement of evaluation steps.
    """
    template_name = "workorders/evaluation_route_builder.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Import Account model here to avoid circular imports
        from apps.sales.models import Account

        # Get all accounts
        accounts = Account.objects.filter(is_active=True).order_by('sort_order', 'code')

        # Build data structure: account -> bit_type -> route
        route_matrix = {}
        for account in accounts:
            route_matrix[account.code] = {
                'account': account,
                'new_route': None,
                'used_route': None,
            }

        # Get all routes
        routes = EvaluationRoute.objects.filter(is_active=True).select_related('account').prefetch_related('steps')
        for route in routes:
            if route.account.code in route_matrix:
                if route.bit_type == EvaluationRoute.BitType.NEW:
                    route_matrix[route.account.code]['new_route'] = route
                else:
                    route_matrix[route.account.code]['used_route'] = route

        context['route_matrix'] = route_matrix
        context['accounts'] = accounts

        # All available evaluation types
        context['evaluation_types'] = CutterEvaluationMatrix.EvaluationType.choices

        context['page_title'] = 'Evaluation Route Builder'
        context['breadcrumbs'] = [
            {'title': 'Work Orders', 'url': reverse('workorders:enhanced_list')},
            {'title': 'Route Builder', 'url': None}
        ]
        return context


class EvaluationRouteDetailView(LoginRequiredMixin, View):
    """
    View/Edit a specific evaluation route.
    """
    def get(self, request, pk):
        route = get_object_or_404(EvaluationRoute.objects.prefetch_related('steps'), pk=pk)

        # Get steps in order
        steps = route.steps.all().order_by('order')

        # All available evaluation types
        evaluation_types = CutterEvaluationMatrix.EvaluationType.choices

        # Types already in the route
        used_types = set(step.evaluation_type for step in steps)

        # Available types (not yet in route)
        available_types = [(code, label) for code, label in evaluation_types if code not in used_types]

        return render(request, 'workorders/evaluation_route_detail.html', {
            'route': route,
            'steps': steps,
            'evaluation_types': evaluation_types,
            'available_types': available_types,
            'page_title': f'Edit Route: {route.name}',
            'breadcrumbs': [
                {'title': 'Work Orders', 'url': reverse('workorders:enhanced_list')},
                {'title': 'Route Builder', 'url': reverse('workorders:evaluation_route_builder')},
                {'title': route.name, 'url': None}
            ]
        })


@login_required
def api_create_route(request):
    """API to create a new evaluation route."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})

    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})

    account_id = data.get('account_id')
    bit_type = data.get('bit_type')
    name = data.get('name', '')

    if not account_id or not bit_type:
        return JsonResponse({'success': False, 'error': 'account_id and bit_type required'})

    from apps.sales.models import Account
    try:
        account = Account.objects.get(pk=account_id)
    except Account.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Account not found'})

    # Create default name if not provided
    if not name:
        type_label = 'New Build' if bit_type == 'NEW' else 'Repair'
        name = f"{account.code} {type_label} Standard"

    # Check if route already exists
    existing = EvaluationRoute.objects.filter(account=account, bit_type=bit_type, is_active=True).first()
    if existing:
        return JsonResponse({
            'success': False,
            'error': f'Route already exists for {account.code} - {bit_type}',
            'route_id': existing.id
        })

    # Create the route
    route = EvaluationRoute.objects.create(
        name=name,
        account=account,
        bit_type=bit_type,
        is_default=True,
        created_by=request.user
    )

    return JsonResponse({
        'success': True,
        'route_id': route.id,
        'route_name': route.name,
        'message': f'Route created: {route.name}'
    })


@login_required
def api_update_route(request, pk):
    """API to update a route (name, description, etc.)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})

    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})

    try:
        route = EvaluationRoute.objects.get(pk=pk)
    except EvaluationRoute.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Route not found'})

    # Update fields
    if 'name' in data:
        route.name = data['name']
    if 'description' in data:
        route.description = data['description']
    if 'is_active' in data:
        route.is_active = data['is_active']
    if 'is_default' in data:
        # If setting as default, unset others
        if data['is_default']:
            EvaluationRoute.objects.filter(
                account=route.account,
                bit_type=route.bit_type,
                is_default=True
            ).exclude(pk=route.pk).update(is_default=False)
        route.is_default = data['is_default']

    route.save()

    return JsonResponse({
        'success': True,
        'message': 'Route updated'
    })


@login_required
def api_delete_route(request, pk):
    """API to delete (deactivate) a route."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})

    try:
        route = EvaluationRoute.objects.get(pk=pk)
    except EvaluationRoute.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Route not found'})

    # Soft delete - deactivate
    route.is_active = False
    route.save()

    return JsonResponse({
        'success': True,
        'message': f'Route "{route.name}" deleted'
    })


@login_required
def api_add_route_step(request, pk):
    """API to add a step to a route."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})

    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})

    try:
        route = EvaluationRoute.objects.get(pk=pk)
    except EvaluationRoute.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Route not found'})

    evaluation_type = data.get('evaluation_type')
    if not evaluation_type:
        return JsonResponse({'success': False, 'error': 'evaluation_type required'})

    # Check if already exists
    if route.steps.filter(evaluation_type=evaluation_type).exists():
        return JsonResponse({'success': False, 'error': 'Step already exists in route'})

    # Get next order number
    max_order = route.steps.aggregate(max_order=models.Max('order'))['max_order'] or 0

    # Create step
    step = EvaluationRouteStep.objects.create(
        route=route,
        evaluation_type=evaluation_type,
        order=max_order + 1,
        is_required=data.get('is_required', True),
        is_conditional=data.get('is_conditional', False),
        condition_description=data.get('condition_description', ''),
        show_decision_field=data.get('show_decision_field', True),
        show_cutter_matrix=data.get('show_cutter_matrix', True),
        show_cutters_details=data.get('show_cutters_details', True),
    )

    return JsonResponse({
        'success': True,
        'step_id': step.id,
        'message': f'Step added: {step.get_evaluation_type_display()}'
    })


@login_required
def api_update_route_step(request, pk, step_pk):
    """API to update a step in a route."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})

    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})

    try:
        step = EvaluationRouteStep.objects.get(pk=step_pk, route_id=pk)
    except EvaluationRouteStep.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Step not found'})

    # Update fields
    if 'is_required' in data:
        step.is_required = data['is_required']
    if 'is_conditional' in data:
        step.is_conditional = data['is_conditional']
    if 'condition_description' in data:
        step.condition_description = data['condition_description']
    if 'show_decision_field' in data:
        step.show_decision_field = data['show_decision_field']
    if 'show_cutter_matrix' in data:
        step.show_cutter_matrix = data['show_cutter_matrix']
    if 'show_cutters_details' in data:
        step.show_cutters_details = data['show_cutters_details']
    if 'order' in data:
        step.order = data['order']

    step.save()

    return JsonResponse({
        'success': True,
        'message': 'Step updated'
    })


@login_required
def api_delete_route_step(request, pk, step_pk):
    """API to delete a step from a route."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})

    try:
        step = EvaluationRouteStep.objects.get(pk=step_pk, route_id=pk)
    except EvaluationRouteStep.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Step not found'})

    step_name = step.get_evaluation_type_display()
    step.delete()

    return JsonResponse({
        'success': True,
        'message': f'Step "{step_name}" removed'
    })


@login_required
def api_reorder_route_steps(request, pk):
    """API to reorder steps in a route."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})

    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})

    step_order = data.get('step_order', [])  # List of step IDs in new order

    try:
        route = EvaluationRoute.objects.get(pk=pk)
    except EvaluationRoute.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Route not found'})

    # Update order for each step
    for index, step_id in enumerate(step_order):
        EvaluationRouteStep.objects.filter(pk=step_id, route=route).update(order=index)

    return JsonResponse({
        'success': True,
        'message': 'Steps reordered'
    })


@login_required
def api_get_route(request, pk):
    """API to get route data including all steps."""
    try:
        route = EvaluationRoute.objects.prefetch_related('steps').get(pk=pk)
    except EvaluationRoute.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Route not found'})

    steps = []
    for step in route.steps.all().order_by('order'):
        steps.append({
            'id': step.id,
            'evaluation_type': step.evaluation_type,
            'evaluation_type_display': step.get_evaluation_type_display(),
            'order': step.order,
            'is_required': step.is_required,
            'is_conditional': step.is_conditional,
            'condition_description': step.condition_description,
            'show_decision_field': step.show_decision_field,
            'show_cutter_matrix': step.show_cutter_matrix,
            'show_cutters_details': step.show_cutters_details,
        })

    return JsonResponse({
        'success': True,
        'route': {
            'id': route.id,
            'name': route.name,
            'description': route.description,
            'bit_type': route.bit_type,
            'bit_type_display': route.get_bit_type_display(),
            'account_code': route.account.code,
            'is_default': route.is_default,
            'is_active': route.is_active,
            'steps': steps,
        }
    })


@login_required
def api_get_evaluation_types(request):
    """API to get all available evaluation types."""
    types = []
    for code, label in CutterEvaluationMatrix.EvaluationType.choices:
        # Skip legacy types
        if code == 'ARDT':
            continue
        types.append({
            'code': code,
            'label': label,
        })

    return JsonResponse({
        'success': True,
        'evaluation_types': types
    })


# =============================================================================
# RECEIVING INSPECTION (QAS/005-1) — Linked to DrillBit
# =============================================================================

def _get_bom_blade_data(drill_bit):
    """
    Extract blade data from a drill bit's BOM source_data for the evaluation grid.
    Returns (blade_data_list, bom_summary_list, cutter_config_list, has_data, cutter_grid_ctx) tuple.
    blade_data_list: [{name, rows: [{row_key, positions: [{pos_name, cutters: [{type, group, chamfer}]}]}]}]
    cutter_config_list: [{order, color, count, type, group, chamfer}]
    cutter_grid_ctx: dict of JSON strings for pocket-style cutter grid
    """
    bom = drill_bit.brazing_bom or drill_bit.system_bom or getattr(drill_bit, 'bom', None)
    if not bom or not bom.source_data:
        return [], [], [], False, {}

    source_data = bom.source_data if isinstance(bom.source_data, dict) else {}
    raw_blades = source_data.get("blades", [])
    bom_summary = source_data.get("bom", [])

    if not raw_blades:
        return [], bom_summary, [], False, {}

    POSITIONS = ["CONE", "NOSE", "SHOULDER", "GAUGE", "PAD"]
    ROW_KEYS = ["r1", "r2", "r3", "r4"]

    blade_data = []
    for blade in raw_blades:
        blade_name = blade.get("name", "")
        rows = []
        for rk in ROW_KEYS:
            row_data = blade.get(rk, {})
            if not row_data:
                continue
            positions = []
            for pos in POSITIONS:
                cutters = row_data.get(pos, [])
                if cutters:
                    positions.append({
                        "pos_name": pos,
                        "cutters": cutters,  # [{type, group, chamfer}, ...]
                    })
            if positions:
                rows.append({"row_key": rk, "positions": positions})
        if rows:
            blade_data.append({"name": blade_name, "rows": rows})

    # Build BOM summary lookup for size and mat_number per cutter type
    bom_lookup = {}
    for bom_row in bom_summary:
        bkey = f"{bom_row.get('type', '')}|{bom_row.get('chamfer', '')}"
        if bkey not in bom_lookup:
            bom_lookup[bkey] = bom_row

    # Build cutter config list (unique cutter types with colors for the grid)
    CUTTER_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
                     '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1',
                     '#14B8A6', '#F43F5E', '#A855F7', '#22D3EE']
    seen_types = {}
    cutter_config_list = []
    type_idx = 0
    for blade in blade_data:
        for row in blade['rows']:
            for pos in row['positions']:
                for cutter in pos['cutters']:
                    ct = cutter.get('type', '')
                    cg = cutter.get('group', '')
                    cc = cutter.get('chamfer', '')
                    key = f"{ct}|{cg}|{cc}"
                    if key not in seen_types:
                        color = CUTTER_COLORS[type_idx % len(CUTTER_COLORS)]
                        # Cross-reference BOM summary for size and mat_number
                        bom_match = bom_lookup.get(f"{ct}|{cc}", {})
                        seen_types[key] = {
                            'order': type_idx + 1, 'color': color, 'count': 0,
                            'type': ct, 'group': cg, 'chamfer': cc,
                            'size': bom_match.get('size', ''),
                            'mat_number': bom_match.get('mat_number', ''),
                        }
                        type_idx += 1
                    seen_types[key]['count'] += 1
    cutter_config_list = sorted(seen_types.values(), key=lambda x: x['order'])

    # ── Build cutter grid context (pocket-style flat layout) ──
    # Count cutters per row per blade
    blade_row_counts = {}
    for blade in blade_data:
        for row in blade['rows']:
            count = sum(len(pos['cutters']) for pos in row['positions'])
            blade_row_counts[(blade['name'], row['row_key'])] = count

    all_blade_names = [b['name'] for b in blade_data]
    # Determine which rows exist across all blades
    all_row_keys = [rk for rk in ROW_KEYS
                    if any(blade_row_counts.get((bn, rk), 0) > 0 for bn in all_blade_names)]

    # Max cutters per row across all blades (for vertical alignment)
    row_max = {}
    for rk in all_row_keys:
        row_max[rk] = max(blade_row_counts.get((bn, rk), 0) for bn in all_blade_names)

    # Row start offsets (virtual column where each row begins)
    row_start = {}
    col_offset = 1
    for rk in all_row_keys:
        row_start[rk] = col_offset
        col_offset += row_max[rk]

    # Row separators (cumulative end of each row except last)
    row_separators = []
    cumulative = 0
    for rk in all_row_keys[:-1]:
        cumulative += row_max[rk]
        row_separators.append(cumulative)

    max_col = col_offset - 1  # total virtual columns

    # Build grid data: maps "blade_vcol" -> config_order / cell_ref / cutter_number
    cutter_grid_data = {}
    cutter_cell_ref = {}
    cutter_number_data = {}

    for blade in blade_data:
        bn = blade['name']
        cutter_seq = 0
        for rk in all_row_keys:
            row_obj = next((r for r in blade['rows'] if r['row_key'] == rk), None)
            if not row_obj:
                continue
            pos_offset = 0
            for pos in row_obj['positions']:
                pn = pos['pos_name'].upper()
                for i in range(len(pos['cutters'])):
                    cutter_seq += 1
                    vcol = row_start[rk] + pos_offset
                    key = f"{bn}_{vcol}"

                    c = pos['cutters'][i]
                    ct = c.get('type', '')
                    cg = c.get('group', '')
                    cc = c.get('chamfer', '')
                    type_key = f"{ct}|{cg}|{cc}"
                    cfg = seen_types.get(type_key)

                    cutter_grid_data[key] = cfg['order'] if cfg else 0
                    cutter_cell_ref[key] = {'b': bn, 'r': rk, 'p': pn, 'i': i}
                    cutter_number_data[key] = cutter_seq
                    pos_offset += 1

    cutter_grid_ctx = {
        'cutter_grid_data_json': _json.dumps(cutter_grid_data),
        'cutter_cell_ref_json': _json.dumps(cutter_cell_ref),
        'cutter_number_data_json': _json.dumps(cutter_number_data),
        'cutter_row_separators_json': _json.dumps(sorted(row_separators)),
        'cutter_max_col': max_col,
        'cutter_blade_names': all_blade_names,
    }

    return blade_data, bom_summary, cutter_config_list, bool(blade_data), cutter_grid_ctx


def _get_pocket_grid_context(drill_bit):
    """
    Build pocket config + grid data for the receiving inspection template.
    Reuses the same pattern as DrillBitDetailEnhancedView (lines 562-621).
    Returns dict of context keys to add.
    """
    design = drill_bit.design if drill_bit else None
    if not design:
        return {'has_pocket_data': False}

    from apps.technology.models import DesignPocket, DesignPocketConfig

    pockets = DesignPocket.objects.filter(
        design=design
    ).select_related(
        'pocket_config', 'pocket_config__pocket_size', 'pocket_config__pocket_shape'
    ).order_by('blade_number', 'row_number', 'position_in_row')

    if not pockets.exists():
        return {'has_pocket_data': False}

    pocket_configs = DesignPocketConfig.objects.filter(
        design=design
    ).select_related('pocket_size', 'pocket_shape').order_by('order')

    # Build grid data with row-aligned virtual columns
    # Different blades have different cutter counts per row. We pad shorter
    # blades so all R2 cutters appear after the R1 separator, etc.
    from collections import defaultdict
    pocket_list = list(pockets)

    blade_row_counts = defaultdict(int)
    for p in pocket_list:
        blade_row_counts[(p.blade_number, p.row_number)] += 1

    all_blades = sorted(set(p.blade_number for p in pocket_list))
    all_rows = sorted(set(p.row_number for p in pocket_list))

    # Max cutters per row across ALL blades
    row_max = {}
    for row in all_rows:
        row_max[row] = max(
            blade_row_counts.get((blade, row), 0) for blade in all_blades
        )

    # Row start offsets (virtual column where each row begins)
    row_start = {}
    offset = 1
    for row in all_rows:
        row_start[row] = offset
        offset += row_max[row]

    # Row separators — cumulative end of each row except last
    row_separators = []
    cumulative = 0
    for row in all_rows[:-1]:
        cumulative += row_max[row]
        row_separators.append(cumulative)

    max_pos = offset - 1  # total virtual columns

    # Build grid data using virtual columns
    grid_data = {}
    location_data = {}
    for p in pocket_list:
        vcol = row_start[p.row_number] + p.position_in_row - 1
        key = f"{p.blade_number}_{vcol}"
        grid_data[key] = p.pocket_config_id
        if p.blade_location:
            location_data[key] = p.blade_location

    # Config display colors
    colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
              '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1']
    config_data = {}
    config_list = []
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
        config_list.append({
            'order': cfg.order,
            'size': cfg.pocket_size.display_name if cfg.pocket_size else '—',
            'shape': cfg.pocket_shape.name if cfg.pocket_shape else '—',
            'length_type': cfg.get_length_type_display() if hasattr(cfg, 'get_length_type_display') else cfg.length_type or '—',
            'count': cfg.count,
            'color': dc,
        })

    # Determine blade count
    blade_nums = sorted(set(p.blade_number for p in pockets))

    # Sequential pocket numbers per blade (for B2P6 format labels)
    pocket_number_data = {}
    blade_counters = {}
    for p in pocket_list:
        bn = p.blade_number
        if bn not in blade_counters:
            blade_counters[bn] = 0
        blade_counters[bn] += 1
        vcol = row_start[p.row_number] + p.position_in_row - 1
        key = f"{bn}_{vcol}"
        pocket_number_data[key] = blade_counters[bn]

    return {
        'has_pocket_data': True,
        'pocket_grid_data_json': _json.dumps(grid_data),
        'pocket_row_separators_json': _json.dumps(sorted(row_separators)),
        'pocket_location_data_json': _json.dumps(location_data),
        'pocket_config_data_json': _json.dumps(config_data),
        'pocket_number_data_json': _json.dumps(pocket_number_data),
        'pocket_config_list': config_list,
        'pocket_blade_nums': blade_nums,
        'pocket_max_pos': max_pos,
        'pocket_config_total': sum(cfg.count for cfg in pocket_configs),
    }


class ReceivingInspectionCreateView(LoginRequiredMixin, CreateView):
    """Create a new Receiving Inspection for a drill bit."""
    model = ReceivingInspection
    template_name = "workorders/receiving_inspection_form.html"

    def get_form_class(self):
        from .forms import ReceivingInspectionForm
        return ReceivingInspectionForm

    def get_drill_bit(self):
        return get_object_or_404(
            DrillBit.objects.select_related(
                'design', 'design__size', 'bom', 'system_bom', 'brazing_bom',
            ),
            pk=self.kwargs['bit_pk'],
        )

    def dispatch(self, request, *args, **kwargs):
        bit = self.get_drill_bit()
        if bit.status == DrillBit.Status.UNREGISTERED:
            from django.contrib import messages
            messages.error(request, f"Bit {bit.serial_number} has status Unregistered and cannot be inspected. Please register it first.")
            return redirect('workorders:receiving_inspection_list')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        bit = self.get_drill_bit()
        # Fix 2: Default inspection_date to today
        initial['inspection_date'] = timezone.now().date()
        # Fix 1: Auto-fill date_of_receipt from drill bit's received_date
        if bit.received_date:
            initial['date_of_receipt'] = bit.received_date
        else:
            # Fallback: check BitEvent for RECEIVED event
            evt = BitEvent.objects.filter(
                bit=bit, event_type=BitEvent.EventType.RECEIVED
            ).order_by('event_date').first()
            if evt:
                initial['date_of_receipt'] = evt.event_date.date() if evt.event_date else None
            else:
                # Second fallback: check BackloadItem
                from .models import BackloadItem
                bl_item = BackloadItem.objects.filter(
                    drill_bit=bit, received_date__isnull=False
                ).order_by('-received_date').first()
                if bl_item:
                    initial['date_of_receipt'] = bl_item.received_date.date() if bl_item.received_date else None
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bit = self.get_drill_bit()
        context['drill_bit'] = bit
        context['page_title'] = f"New Receiving Inspection — {bit.serial_number}"
        context['is_new'] = True
        context['report_number'] = 'RI-NEW'
        # QAS/005-1 checklist items (all NA for new) — 11 items
        context['checklist_items'] = [
            (1, "Bit Cleanliness", "vi_gauge_pads", "NA"),
            (2, "Ring Gage GO", "vi_bit_face", "NA"),
            (3, "Ring Gage NO GO", "vi_general", "NA"),
            (4, "Nozzle Threads", "vi_nozzles", "NA"),
            (5, "Breaker Slot", "vi_bit_breaker", "NA"),
            (6, "Junk Slot", "vi_junk_slot", "NA"),
            (7, "API Pin Connection", "vi_pin_connection", "NA"),
            (8, "Cutters", "vi_blades", "NA"),
            (9, "No Body Damage", "vi_bit_body", "NA"),
            (10, "Nozzle Liner Fit", "vi_nozzle_liner", "NA"),
            (11, "Q-Note from Vendor", "vi_vendor_note", "NA"),
        ]
        context['checklist_remarks'] = {}

        # BOM blade data for cutter evaluation grid
        blade_data, bom_summary, cutter_config_list, has_bom, cutter_grid_ctx = _get_bom_blade_data(bit)
        context['has_bom_data'] = has_bom
        context['blade_data_json'] = _json.dumps(blade_data)
        context['bom_summary_json'] = _json.dumps(bom_summary)
        context['eval_data_json'] = '{}'
        context['cutter_config_list'] = cutter_config_list
        context['cutter_config_json'] = _json.dumps({
            cfg['order']: {'color': cfg['color'], 'type': cfg['type'], 'group': cfg['group']}
            for cfg in cutter_config_list
        })
        context.update(cutter_grid_ctx)

        # Pocket grid data
        context.update(_get_pocket_grid_context(bit))
        context['pocket_eval_data_json'] = '{}'
        return context

    def _save_json_fields(self, form):
        """Parse and save JSON hidden inputs for eval data, pocket data, and checklist remarks."""
        for field, post_key in [
            ('cutter_evaluation_data', 'cutter_evaluation_data'),
            ('pocket_evaluation_data', 'pocket_evaluation_data'),
            ('checklist_remarks', 'checklist_remarks'),
        ]:
            raw = self.request.POST.get(post_key, '{}')
            try:
                setattr(form.instance, field, _json.loads(raw))
            except (ValueError, TypeError):
                setattr(form.instance, field, {})

    def form_valid(self, form):
        form.instance.drill_bit = self.get_drill_bit()
        form.instance.inspected_by = self.request.user
        if not form.instance.inspection_date:
            form.instance.inspection_date = timezone.now().date()
        self._save_json_fields(form)
        response = super().form_valid(form)
        messages.success(self.request, "Receiving inspection created.")
        return response

    def get_success_url(self):
        return reverse('workorders:receiving_inspection_edit',
                        kwargs={'bit_pk': self.kwargs['bit_pk'], 'pk': self.object.pk})


class ReceivingInspectionEditView(LoginRequiredMixin, UpdateView):
    """Edit an existing Receiving Inspection."""
    model = ReceivingInspection
    template_name = "workorders/receiving_inspection_form.html"

    def get_form_class(self):
        from .forms import ReceivingInspectionForm
        return ReceivingInspectionForm

    def get_queryset(self):
        return ReceivingInspection.objects.select_related(
            'drill_bit', 'drill_bit__design', 'drill_bit__design__size',
            'drill_bit__bom', 'drill_bit__system_bom', 'drill_bit__brazing_bom',
            'work_order', 'inspected_by', 'qc_approved_by'
        ).filter(drill_bit__pk=self.kwargs['bit_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bit = self.object.drill_bit
        context['drill_bit'] = bit
        context['page_title'] = f"Receiving Inspection — {bit.serial_number}"
        context['is_new'] = False
        context['report_number'] = self.object.report_number
        context['checklist_items'] = self.object.checklist_items
        context['checklist_remarks'] = self.object.checklist_remarks or {}
        # QR code for print header
        from apps.workorders.utils import generate_drill_bit_qr
        context['bit_qr_base64'] = generate_drill_bit_qr(bit)
        # BOM blade data for cutter evaluation grid
        blade_data, bom_summary, cutter_config_list, has_bom, cutter_grid_ctx = _get_bom_blade_data(bit)
        context['has_bom_data'] = has_bom
        context['blade_data_json'] = _json.dumps(blade_data)
        context['bom_summary_json'] = _json.dumps(bom_summary)
        context['eval_data_json'] = _json.dumps(self.object.cutter_evaluation_data or {})
        context['cutter_config_list'] = cutter_config_list
        context['cutter_config_json'] = _json.dumps({
            cfg['order']: {'color': cfg['color'], 'type': cfg['type'], 'group': cfg['group']}
            for cfg in cutter_config_list
        })
        context.update(cutter_grid_ctx)
        # Pocket grid data
        context.update(_get_pocket_grid_context(bit))
        context['pocket_eval_data_json'] = _json.dumps(self.object.pocket_evaluation_data or {})
        # Attachments
        context['attachments'] = self.object.attachments.all()
        return context

    def form_valid(self, form):
        # Save JSON fields from hidden inputs
        for field, post_key in [
            ('cutter_evaluation_data', 'cutter_evaluation_data'),
            ('pocket_evaluation_data', 'pocket_evaluation_data'),
            ('checklist_remarks', 'checklist_remarks'),
        ]:
            raw = self.request.POST.get(post_key, '{}')
            try:
                setattr(form.instance, field, _json.loads(raw))
            except (ValueError, TypeError):
                setattr(form.instance, field, {})
        # Check if "mark_complete" was submitted
        mark_complete = self.request.POST.get('mark_complete')
        if mark_complete == 'true' and not form.instance.is_complete:
            form.instance.is_complete = True
            form.instance.qc_approved_by = self.request.user
            form.instance.qc_approved_at = timezone.now()
            messages.success(self.request, "Receiving inspection marked as complete.")
        elif mark_complete == 'false' and form.instance.is_complete:
            form.instance.is_complete = False
            form.instance.qc_approved_by = None
            form.instance.qc_approved_at = None
            messages.success(self.request, "Receiving inspection reopened.")
        else:
            messages.success(self.request, "Receiving inspection saved.")

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('workorders:receiving_inspection_edit',
                        kwargs={'bit_pk': self.kwargs['bit_pk'], 'pk': self.object.pk})


@login_required
@require_POST
def api_receiving_inspection_complete(request, bit_pk, pk):
    """Toggle is_complete on a ReceivingInspection. POST-only."""
    inspection = get_object_or_404(ReceivingInspection, pk=pk, drill_bit__pk=bit_pk)

    if inspection.is_complete:
        # Reopen
        inspection.is_complete = False
        inspection.qc_approved_by = None
        inspection.qc_approved_at = None
        inspection.save(update_fields=['is_complete', 'qc_approved_by', 'qc_approved_at', 'updated_at'])
        return JsonResponse({'success': True, 'is_complete': False, 'message': 'Inspection reopened.'})
    else:
        # Complete
        inspection.is_complete = True
        inspection.qc_approved_by = request.user
        inspection.qc_approved_at = timezone.now()
        inspection.save(update_fields=['is_complete', 'qc_approved_by', 'qc_approved_at', 'updated_at'])
        return JsonResponse({'success': True, 'is_complete': True, 'message': 'Inspection marked complete.'})


@login_required
@require_POST
def api_receiving_inspection_upload(request, bit_pk, pk):
    """Upload an attachment to a receiving inspection."""
    inspection = get_object_or_404(ReceivingInspection, pk=pk, drill_bit__pk=bit_pk)
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
    name = request.POST.get('name', 'Q-Note').strip() or 'Q-Note'
    attachment = ReceivingInspectionAttachment.objects.create(
        inspection=inspection,
        file=file,
        name=name,
        uploaded_by=request.user,
    )
    return JsonResponse({
        'success': True,
        'attachment': {
            'id': attachment.pk,
            'name': attachment.name,
            'file_url': attachment.file.url,
            'file_extension': attachment.file_extension,
            'is_image': attachment.is_image,
            'uploaded_at': attachment.uploaded_at.strftime('%b %d, %Y %H:%M'),
            'uploaded_by': request.user.get_full_name() or request.user.username,
        }
    })


@login_required
@require_POST
def api_receiving_inspection_delete_attachment(request, bit_pk, pk, att_pk):
    """Delete an attachment from a receiving inspection."""
    attachment = get_object_or_404(ReceivingInspectionAttachment, pk=att_pk,
                                  inspection__pk=pk, inspection__drill_bit__pk=bit_pk)
    attachment.file.delete(save=False)
    attachment.delete()
    return JsonResponse({'success': True})


# =============================================================================
# EVALUATION AUTO-CREATE (Standalone per-type URLs)
# =============================================================================

class EvaluationAutoCreateView(LoginRequiredMixin, View):
    """
    GET /workorders/<wo_pk>/evaluation/<type_code>/
    Auto-creates CutterEvaluationMatrix for the given type if not exists,
    then redirects to the matrix editor.
    """
    def get(self, request, wo_pk, type_code):
        wo = get_object_or_404(WorkOrder, pk=wo_pk)
        # Validate type_code
        valid_codes = [c[0] for c in CutterEvaluationMatrix.EvaluationType.choices]
        if type_code not in valid_codes:
            messages.error(request, f"Invalid evaluation type: {type_code}")
            return redirect('workorders:workorder_detail_enhanced', pk=wo.pk)

        matrix, created = CutterEvaluationMatrix.objects.get_or_create(
            work_order=wo,
            evaluation_type=type_code,
            evaluation_number=1,
            defaults={'evaluated_by': request.user}
        )
        if created:
            messages.info(request, f"Created new {matrix.get_evaluation_type_display()}")
        return redirect('workorders:cutter_evaluation_edit', wo_pk=wo.pk, pk=matrix.pk)
