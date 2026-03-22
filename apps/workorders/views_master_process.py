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
                "parameters_spec": p.parameters_spec or [],
                "checklist_items": p.checklist_items or [],
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

    # JSON fields
    for field in ["time_factors", "parameters_spec", "checklist_items", "applies_to_levels"]:
        if field in data:
            setattr(p, field, data[field])

    p.save()
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
