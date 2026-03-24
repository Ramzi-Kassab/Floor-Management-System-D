"""
ARDT FMS - Master Process & Special Instruction Views
Inline editing for the master process library and special instructions manager.
"""

import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from .models import MasterProcess, ProcessInclusionRule, SpecialInstruction


# ============================================================================
# MASTER PROCESS LIST + EDITOR
# ============================================================================

class MasterProcessListView(LoginRequiredMixin, TemplateView):
    template_name = "workorders/master_process_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        processes = MasterProcess.objects.prefetch_related("inclusion_rules").all()
        processes_data = []
        for p in processes:
            rules = []
            for r in p.inclusion_rules.all():
                rules.append({
                    "pk": r.pk,
                    "rule_type": r.rule_type,
                    "field_path": r.field_path,
                    "operator": r.operator,
                    "value": r.value,
                    "priority": r.priority,
                    "description": r.description,
                })
            processes_data.append({
                "pk": p.pk,
                "code": p.code,
                "name": p.name,
                "category": p.category,
                "description": p.description,
                "instructions_general": p.instructions_general,
                "procedure_reference": p.procedure_reference,
                "procedure_doc_url": p.procedure_doc_url,
                "safety_notes": p.safety_notes,
                "default_estimated_minutes": p.default_estimated_minutes,
                "time_factors": p.time_factors or {},
                "parameters": [
                    {'pk': pr.pk, 'name': pr.name, 'type': pr.param_type, 'unit': pr.unit,
                     'required': pr.is_required, 'condition': pr.condition_field or '',
                     'condition_op': pr.condition_operator, 'condition_val': pr.condition_value}
                    for pr in p.process_parameters.filter(is_active=True).order_by('sort_order')
                ],
                "checklist": [
                    {'pk': ci.pk, 'text': ci.text, 'required': ci.is_required,
                     'condition': ci.condition_field or '',
                     'condition_op': ci.condition_operator, 'condition_val': ci.condition_value}
                    for ci in p.process_checklist_items.filter(is_active=True).order_by('sort_order')
                ],
                "requires_qc": p.requires_qc,
                "is_default_included": p.is_default_included,
                "sort_order": p.sort_order,
                "applies_to_new": p.applies_to_new,
                "applies_to_repair": p.applies_to_repair,
                "applies_to_levels": p.applies_to_levels or [],
                "is_active": p.is_active,
                "dedicated_page": p.dedicated_page or '',
                "dedicated_icon": p.dedicated_icon or '',
                "step_mode": p.step_mode or 'ACTIVE',
                "insertion_points": p.insertion_points or [],
                "rule_expression": p.rule_expression or {},
                "rules": rules,
            })

        ctx["processes_json"] = json.dumps(processes_data)
        ctx["process_count"] = len(processes_data)
        ctx["categories_json"] = json.dumps(
            [{"value": c[0], "label": c[1]} for c in MasterProcess.Category.choices]
        )
        ctx["rule_types_json"] = json.dumps(
            [{"value": c[0], "label": c[1]} for c in ProcessInclusionRule.RuleType.choices]
        )
        ctx["operators_json"] = json.dumps(
            [{"value": c[0], "label": c[1]} for c in ProcessInclusionRule.Operator.choices]
        )
        return ctx


def _parse_json_body(request):
    """Parse JSON body from request, return dict."""
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return None


@login_required
def api_master_process_create(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = _parse_json_body(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = (data.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "Name is required"}, status=400)

    # Auto-generate code from name if not provided
    code = (data.get("code") or "").strip()
    if not code:
        # Generate: take first letters of each word, uppercase, add number if exists
        words = name.upper().replace('(', '').replace(')', '').split()
        base = '-'.join(w[:4] for w in words[:3])
        code = base
        suffix = 1
        while MasterProcess.objects.filter(code=code).exists():
            code = f"{base}-{suffix}"
            suffix += 1

    if MasterProcess.objects.filter(code=code).exists():
        return JsonResponse({"error": f"Code '{code}' already exists"}, status=400)

    p = MasterProcess.objects.create(
        code=code,
        name=name,
        category=data.get("category", "SPECIAL"),
        sort_order=data.get("sort_order", 100),
        default_estimated_minutes=data.get("default_estimated_minutes", 30),
        is_active=True,
        is_default_included=True,
        applies_to_new=True,
        applies_to_repair=True,
    )
    return JsonResponse({
        "ok": True,
        "pk": p.pk,
        "code": p.code,
        "name": p.name,
    })


@login_required
def api_master_process_save(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    p = get_object_or_404(MasterProcess, pk=pk)
    data = _parse_json_body(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Update scalar fields
    for field in [
        "code", "name", "category", "description",
        "instructions_general", "procedure_reference", "procedure_doc_url",
        "safety_notes", "dedicated_page", "dedicated_icon", "step_mode",
    ]:
        if field in data:
            setattr(p, field, (data[field] or "").strip() if isinstance(data[field], str) else data[field])

    for field in ["default_estimated_minutes", "sort_order"]:
        if field in data:
            try:
                setattr(p, field, int(data[field]))
            except (ValueError, TypeError):
                pass

    for field in ["requires_qc", "is_default_included", "is_active", "applies_to_new", "applies_to_repair"]:
        if field in data:
            setattr(p, field, bool(data[field]))

    # JSON fields (parameters_spec and checklist_items removed — use tables now)
    for field in ["time_factors", "applies_to_levels", "insertion_points", "rule_expression"]:
        if field in data:
            setattr(p, field, data[field])

    p.save()

    # Handle table-based checklist and parameter updates
    from apps.workorders.models import ProcessChecklistItem, ProcessParameter
    if "checklist" in data and isinstance(data["checklist"], list):
        p.process_checklist_items.all().delete()
        for i, item in enumerate(data["checklist"]):
            ProcessChecklistItem.objects.create(
                master_process=p,
                text=item.get('text', ''),
                is_required=item.get('required', True),
                sort_order=(i + 1) * 10,
                condition_field=item.get('condition', ''),
                condition_operator=item.get('condition_op', 'EQUALS'),
                condition_value=item.get('condition_val', ''),
            )

    if "parameters" in data and isinstance(data["parameters"], list):
        p.process_parameters.all().delete()
        for i, param in enumerate(data["parameters"]):
            ProcessParameter.objects.create(
                master_process=p,
                name=param.get('name', ''),
                param_type=param.get('type', 'text'),
                unit=param.get('unit', ''),
                is_required=param.get('required', False),
                sort_order=(i + 1) * 10,
                min_value=param.get('min'),
                max_value=param.get('max'),
                choices_list=param.get('choices', []),
                condition_field=param.get('condition', ''),
                condition_operator=param.get('condition_op', 'EQUALS'),
                condition_value=param.get('condition_val', ''),
            )

    return JsonResponse({"ok": True})


@login_required
def api_master_process_delete(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    p = get_object_or_404(MasterProcess, pk=pk)
    code = p.code
    p.delete()
    return JsonResponse({"ok": True, "deleted": code})


# ============================================================================
# INCLUSION RULES
# ============================================================================

@login_required
def api_master_process_detail(request, pk):
    """Return full details for a single MasterProcess (GET)."""
    p = get_object_or_404(MasterProcess, pk=pk)
    rules = []
    for r in p.inclusion_rules.all().order_by('-priority', 'pk'):
        rules.append({
            "pk": r.pk,
            "rule_type": r.rule_type,
            "field_path": r.field_path,
            "operator": r.operator,
            "value": r.value,
            "priority": r.priority,
            "description": r.description,
        })

    # Use effective (inherited) values for display
    params = [
        {'pk': pr.pk, 'name': pr.name, 'type': pr.param_type, 'unit': pr.unit,
         'required': pr.is_required, 'condition': pr.condition_field or '',
         'condition_op': pr.condition_operator, 'condition_val': pr.condition_value}
        for pr in p._get_own_or_parent('process_parameters')
    ]
    checks = [
        {'pk': ci.pk, 'text': ci.text, 'required': ci.is_required,
         'condition': ci.condition_field or '',
         'condition_op': ci.condition_operator, 'condition_val': ci.condition_value}
        for ci in p._get_own_or_parent('process_checklist_items')
    ]

    # Parent/sibling info
    parent_info = None
    siblings = []
    if p.parent_process:
        parent_info = {
            "pk": p.parent_process.pk,
            "code": p.parent_process.code,
            "name": p.parent_process.name,
        }
        siblings = [
            {"pk": s.pk, "code": s.code, "name": s.name}
            for s in p.parent_process.children.filter(is_active=True).exclude(pk=p.pk).order_by('sort_order')
        ]

    return JsonResponse({
        "pk": p.pk,
        "code": p.code,
        "name": p.name,
        "category": p.category,
        "description": p.description,
        "instructions_general": p.effective_instructions,
        "own_instructions": p.instructions_general,
        "procedure_reference": p.effective_procedure_reference,
        "safety_notes": p.effective_safety_notes,
        "default_estimated_minutes": p.effective_estimated_minutes,
        "requires_qc": p.effective_requires_qc,
        "is_default_included": p.is_default_included,
        "is_active": p.is_active,
        "sort_order": p.sort_order,
        "applies_to_new": p.applies_to_new,
        "applies_to_repair": p.applies_to_repair,
        "applies_to_levels": p.applies_to_levels or [],
        "step_mode": p.step_mode or 'ACTIVE',
        "dedicated_page": p.effective_dedicated_page,
        "rule_expression": p.rule_expression or {},
        "rules": rules,
        "parameters": params,
        "checklist": checks,
        "parent": parent_info,
        "siblings": siblings,
        "is_child": p.is_child,
        "inherited_from_parent": p.is_child and not p.instructions_general,
    })


@login_required
def api_master_process_reorder(request):
    """Bulk update sort_order for multiple processes. POST body: {order: [{pk, sort_order}, ...]}"""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    data = _parse_json_body(request)
    if not data or 'order' not in data:
        return JsonResponse({"error": "Invalid JSON — need {order: [{pk, sort_order}, ...]}"}, status=400)

    updated = 0
    for item in data['order']:
        pk = item.get('pk')
        sort_order = item.get('sort_order')
        if pk and sort_order is not None:
            MasterProcess.objects.filter(pk=pk).update(sort_order=int(sort_order))
            updated += 1

    return JsonResponse({"ok": True, "updated": updated})


@login_required
def api_inclusion_rule_save(request, process_pk):
    """Create or update an inclusion rule for a master process."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    mp = get_object_or_404(MasterProcess, pk=process_pk)
    data = _parse_json_body(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    rule_pk = data.get("pk")
    if rule_pk:
        rule = get_object_or_404(ProcessInclusionRule, pk=rule_pk, master_process=mp)
    else:
        rule = ProcessInclusionRule(master_process=mp)

    rule.rule_type = data.get("rule_type", "INCLUDE_IF")
    rule.field_path = (data.get("field_path") or "").strip()
    rule.operator = data.get("operator", "EQUALS")
    rule.value = (data.get("value") or "").strip()
    try:
        rule.priority = int(data.get("priority") or 10)
    except (ValueError, TypeError):
        rule.priority = 10
    rule.description = (data.get("description") or "").strip()

    if not rule.field_path:
        return JsonResponse({"error": "field_path is required"}, status=400)

    rule.save()
    return JsonResponse({
        "ok": True,
        "pk": rule.pk,
        "rule_type": rule.rule_type,
        "field_path": rule.field_path,
        "operator": rule.operator,
        "value": rule.value,
        "priority": rule.priority,
        "description": rule.description,
    })


@login_required
def api_inclusion_rule_delete(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    rule = get_object_or_404(ProcessInclusionRule, pk=pk)
    rule.delete()
    return JsonResponse({"ok": True})


# ============================================================================
# SPECIAL INSTRUCTIONS
# ============================================================================

class SpecialInstructionListView(LoginRequiredMixin, TemplateView):
    template_name = "workorders/special_instruction_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        instructions = (
            SpecialInstruction.objects
            .select_related("target_process", "design", "created_by")
            .all()
        )

        instructions_data = []
        for si in instructions:
            instructions_data.append({
                "pk": si.pk,
                "instruction_text": si.instruction_text,
                "priority": si.priority,
                "applies_to": si.applies_to,
                "target_process_pk": si.target_process_id,
                "target_process_name": str(si.target_process) if si.target_process else "",
                "design_pk": si.design_id,
                "design_display": str(si.design) if si.design else "",
                "serial_number": si.serial_number,
                "size_min": str(si.size_min) if si.size_min else "",
                "size_max": str(si.size_max) if si.size_max else "",
                "body_material": si.body_material,
                "valid_from": si.valid_from.isoformat() if si.valid_from else "",
                "valid_to": si.valid_to.isoformat() if si.valid_to else "",
                "is_active": si.is_active,
                "created_by_name": si.created_by.get_full_name() or si.created_by.username if si.created_by else "",
                "created_at": si.created_at.strftime("%Y-%m-%d %H:%M") if si.created_at else "",
            })

        # Master processes for the target dropdown
        processes = MasterProcess.objects.filter(is_active=True).order_by("sort_order", "name")
        processes_choices = [{"pk": p.pk, "label": f"[{p.code}] {p.name}"} for p in processes]

        # Designs for the design picker
        from apps.technology.models import Design
        designs = Design.objects.filter(is_active=True).order_by("mat_no")
        designs_choices = [{"pk": d.pk, "label": f"{d.mat_no} — {d.name}"} for d in designs]

        ctx["instructions_json"] = json.dumps(instructions_data)
        ctx["instruction_count"] = len(instructions_data)
        ctx["processes_choices_json"] = json.dumps(processes_choices)
        ctx["designs_choices_json"] = json.dumps(designs_choices)
        ctx["priorities_json"] = json.dumps(
            [{"value": c[0], "label": c[1]} for c in SpecialInstruction.Priority.choices]
        )
        ctx["applies_to_json"] = json.dumps(
            [{"value": c[0], "label": c[1]} for c in SpecialInstruction.AppliesTo.choices]
        )
        return ctx


@login_required
def api_special_instruction_save(request):
    """Create or update a special instruction."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = _parse_json_body(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    pk = data.get("pk")
    if pk:
        si = get_object_or_404(SpecialInstruction, pk=pk)
    else:
        si = SpecialInstruction(created_by=request.user)

    si.instruction_text = (data.get("instruction_text") or "").strip()
    if not si.instruction_text:
        return JsonResponse({"error": "Instruction text is required"}, status=400)

    si.priority = data.get("priority", "NORMAL")
    si.applies_to = data.get("applies_to", "ALL")
    si.serial_number = (data.get("serial_number") or "").strip()
    si.body_material = (data.get("body_material") or "").strip()
    si.is_active = data.get("is_active", True)

    # Target process
    tp_pk = data.get("target_process_pk")
    if tp_pk:
        si.target_process_id = int(tp_pk)
    else:
        si.target_process = None

    # Design
    d_pk = data.get("design_pk")
    if d_pk:
        si.design_id = int(d_pk)
    else:
        si.design = None

    # Size range
    size_min = data.get("size_min")
    si.size_min = float(size_min) if size_min else None
    size_max = data.get("size_max")
    si.size_max = float(size_max) if size_max else None

    # Date range
    from datetime import date as date_type
    valid_from = data.get("valid_from")
    si.valid_from = valid_from if valid_from else None
    valid_to = data.get("valid_to")
    si.valid_to = valid_to if valid_to else None

    si.save()

    return JsonResponse({
        "ok": True,
        "pk": si.pk,
        "instruction_text": si.instruction_text,
        "priority": si.priority,
        "applies_to": si.applies_to,
        "target_process_pk": si.target_process_id,
        "target_process_name": str(si.target_process) if si.target_process else "",
        "design_pk": si.design_id,
        "design_display": str(si.design) if si.design else "",
        "serial_number": si.serial_number,
        "size_min": str(si.size_min) if si.size_min else "",
        "size_max": str(si.size_max) if si.size_max else "",
        "body_material": si.body_material,
        "valid_from": si.valid_from.isoformat() if si.valid_from else "",
        "valid_to": si.valid_to.isoformat() if si.valid_to else "",
        "is_active": si.is_active,
        "created_by_name": si.created_by.get_full_name() or si.created_by.username if si.created_by else "",
        "created_at": si.created_at.strftime("%Y-%m-%d %H:%M") if si.created_at else "",
    })


@login_required
def api_special_instruction_delete(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    si = get_object_or_404(SpecialInstruction, pk=pk)
    si.delete()
    return JsonResponse({"ok": True})


# =============================================================================
# ROUTE PREVIEW (simulation)
# =============================================================================

class RoutePreviewView(LoginRequiredMixin, TemplateView):
    """Simulate route assembly — see what steps the engine would generate."""
    template_name = "workorders/route_preview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.sales.models import Account
        from apps.technology.models import BitSize
        context['accounts'] = Account.objects.filter(is_active=True).order_by('sort_order')
        context['sizes'] = BitSize.objects.filter(is_active=True).order_by('size_decimal')
        return context


@login_required
def api_route_preview(request):
    """
    Simulate route assembly from configuration (no real drill bit needed).
    POST body: config dict with level, is_repair, account, size, body_material, etc.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = _parse_json_body(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    from apps.workorders.models import (
        MasterProcess, evaluate_rule_expression, SpecialInstruction
    )

    # Build a synthetic context from the config
    def _bool(key, default=False):
        v = data.get(key, default)
        return str(v).lower() in ('true', '1') if isinstance(v, str) else bool(v)

    is_repair = _bool('is_repair')
    has_ports = _bool('has_ports')
    has_cerebro_force = _bool('has_cerebro_force')
    has_cerebro_puck = _bool('has_cerebro_puck')

    context = {
        # Bit attributes
        'bit.level': data.get('level', '4'),
        'bit.size': float(data.get('size', 8.5)),
        'bit.type': 'FC',
        'bit.account': data.get('account', ''),
        'bit.is_repair': is_repair,
        'bit.is_new': not is_repair,
        'bit.condition': 'USED' if is_repair else 'COMPONENTS',
        'bit.is_core_head': _bool('is_core_head'),
        'bit.has_nozzles': _bool('has_nozzles'),
        'bit.has_erosion_sleeve': _bool('has_erosion_sleeve_installed'),
        'bit.has_cerebro': _bool('has_cerebro_installed'),
        'bit.is_painted': _bool('is_painted'),
        # Design attributes
        'design.body_material': data.get('body_material', 'S'),
        'design.has_ports': has_ports,
        'design.port_count': 1 if has_ports else 0,
        'design.no_of_blades': 6,
        'design.total_pockets_count': 50,
        'design.erosion_sleeve': _bool('design_erosion_sleeve'),
        # Special technologies (by code)
        'tech.has_cerebro': has_cerebro_force or has_cerebro_puck,
        'tech.has_cerebro_force': has_cerebro_force,
        'tech.has_cerebro_puck': has_cerebro_puck,
        'tech.has_torpedo': _bool('has_torpedo'),
        'tech.has_crush_shear': _bool('has_crush_shear'),
        'tech.has_erosion_sleeve': _bool('tech_erosion_sleeve'),
        'tech.has_shankless': _bool('has_shankless'),
        'tech.has_cruser': _bool('has_cruser'),
        'tech.has_weld_over_void': _bool('has_weld_over_void'),
        # BOM
        'bom.has_dynamic_cutters': _bool('has_dynamic_cutters'),
        'bom.has_lines': True,
        # Evaluation findings
        'eval.needs_brazing': _bool('needs_brazing'),
        'eval.needs_cutter_removal': _bool('needs_cutter_removal'),
        'eval.needs_debraze': _bool('needs_debraze'),
        'eval.needs_buildup': _bool('needs_buildup'),
        'eval.needs_tig': _bool('needs_tig'),
        'eval.needs_hardfacing': _bool('needs_hardfacing'),
        'eval.needs_grinding': _bool('needs_grinding'),
        'eval.needs_rework': _bool('needs_rework'),
        'eval.needs_usr': _bool('needs_usr'),
        'eval.needs_thread_repair': _bool('needs_thread_repair'),
        'eval.needs_shank_cleaning': _bool('needs_shank_cleaning'),
        'eval.buildup_on_pocket': _bool('buildup_on_pocket'),
        'eval.tig_on_pocket': _bool('tig_on_pocket'),
        'eval.hardfacing_on_pocket': _bool('hardfacing_on_pocket'),
        # Technical instructions
        'tech.instruction_debraze': _bool('instruction_debraze'),
        'tech.undercut_gauge': _bool('undercut_gauge'),
        # Position choices
        'config.l3_pt_position': data.get('l3_pt_position', 'early'),
        'config.usr_pt_position': data.get('usr_pt_position', 'early'),
    }

    level = context['bit.level']

    # Get all active processes
    processes = MasterProcess.objects.filter(is_active=True).prefetch_related('inclusion_rules')
    if is_repair:
        processes = processes.filter(applies_to_repair=True)
    else:
        processes = processes.filter(applies_to_new=True)

    # Pass 1: non-MULTI
    applicable = []
    multi_processes = []
    for proc in processes:
        if proc.applies_to_levels and level and level not in proc.applies_to_levels:
            continue
        if proc.step_mode == 'MULTI' and proc.insertion_points:
            multi_processes.append(proc)
            continue
        if proc.rule_expression:
            include = evaluate_rule_expression(proc.rule_expression, context)
        else:
            include = proc.is_default_included
            for rule in proc.inclusion_rules.all():
                matches = rule.evaluate(context)
                if rule.rule_type == 'INCLUDE_IF' and matches:
                    include = True
                elif rule.rule_type == 'EXCLUDE_IF' and matches:
                    include = False
                    break
        if include:
            applicable.append(proc)

    applicable.sort(key=lambda p: p.sort_order)

    # Build steps
    def _step_dict(proc, name_override=None, conditional=None):
        return {
            'pk': proc.pk,
            'code': proc.code,
            'name': name_override or proc.name,
            'category': proc.category,
            'description': proc.description or '',
            'estimated_minutes': proc.default_estimated_minutes,
            'params_count': proc.process_parameters.filter(is_active=True).count(),
            'checks_count': proc.process_checklist_items.filter(is_active=True).count(),
            'requires_qc': proc.requires_qc,
            'step_mode': proc.step_mode,
            'is_conditional': conditional if conditional is not None else (not proc.is_default_included),
            'has_dedicated_page': bool(proc.dedicated_page),
            'attach_to_previous': proc.attach_to_previous,
        }

    steps = [_step_dict(proc) for proc in applicable]

    # Pass 2: MULTI insertion points
    for proc in multi_processes:
        for ip in (proc.insertion_points or []):
            if not ip.get('auto_include', True):
                continue
            ip_rule = ip.get('rule_expression', ip.get('rules', []))
            if isinstance(ip_rule, list):
                ip_rule = {'type': 'AND', 'conditions': ip_rule} if ip_rule else {}
            if not evaluate_rule_expression(ip_rule, context):
                continue
            after_code = ip.get('after_process_code', '')
            insert_idx = len(steps)
            if after_code:
                for i, s in enumerate(steps):
                    if s['code'] == after_code:
                        insert_idx = i + 1
                        break
            steps.insert(insert_idx, _step_dict(proc, ip.get('label'), True))

    total_minutes = sum(s['estimated_minutes'] for s in steps)

    # Warnings for conflicting selections
    warnings = []
    if _bool('needs_usr'):
        blockers = []
        if _bool('has_cerebro_puck'):
            blockers.append('Cerebro Puck')
        if _bool('has_cerebro_force'):
            blockers.append('Cerebro Force')
        if _bool('has_shankless'):
            blockers.append('Shankless')
        if _bool('has_weld_over_void'):
            blockers.append('Weld Over Void')
        if _bool('is_core_head'):
            blockers.append('Core Head')
        if blockers:
            warnings.append(
                'Upper Section Replacement (USR) cannot be performed in KSA '
                'due to design feature: ' + ', '.join(blockers) + '. '
                'Options: Accept as-is, Send to USA for repair, Hold, or Scrap. '
                'Contact technical team for advice.'
            )

    return JsonResponse({
        'success': True,
        'steps': steps,
        'total_minutes': total_minutes,
        'step_count': len(steps),
        'warnings': warnings,
    })
