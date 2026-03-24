"""
Seed the Master Process Library with all FC bit steps.
Includes inclusion/exclusion rules per the corrected process table.

Usage:
    python manage.py seed_master_processes --confirm
"""
from django.core.management.base import BaseCommand
from apps.workorders.models import MasterProcess, ProcessInclusionRule


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLETE PROCESS TABLE — corrected Mar 2026
# ═══════════════════════════════════════════════════════════════════════════════

PROCESSES = [
    # ─── RECEIVING ─────────────────────────────────────────────────────────
    {
        'code': 'PRINT-RELEASE', 'name': 'Print Release Document', 'category': 'RECEIVING',
        'sort_order': 8, 'default_estimated_minutes': 5,
        'instructions_general': 'Print release document for the work order.',
    },
    {
        'code': 'RCV-SETUP', 'name': 'Receiving & Preparation', 'category': 'RECEIVING',
        'sort_order': 10, 'default_estimated_minutes': 15,
        'instructions_general': (
            'Decan, read serial, feed system, print pages. '
            'Checklist: tungsten liner existence + drawing (steel body), '
            'cerebro/torpedo cap status (if cerebro/torpedo tech).'
        ),
        'procedure_reference': 'QAS/1006 Rev L, Section 3.1',
        'checklist_items': [
            {'text': 'Verify serial number matches paperwork', 'required': True},
            {'text': 'Check tungsten nozzle bore liner existence', 'required': False,
             'condition_field': 'design.body_material', 'condition_operator': 'EQUALS', 'condition_value': 'S'},
            {'text': 'Check tungsten liner drawing available', 'required': False,
             'condition_field': 'design.body_material', 'condition_operator': 'EQUALS', 'condition_value': 'S'},
            {'text': 'Check cerebro cap status', 'required': False,
             'condition_field': 'tech.has_cerebro', 'condition_operator': 'EQUALS', 'condition_value': 'True'},
            {'text': 'Check torpedo housing / thread protector status', 'required': False,
             'condition_field': 'tech.has_torpedo', 'condition_operator': 'EQUALS', 'condition_value': 'True'},
        ],
    },
    {
        'code': 'RMV-NOZZLE', 'name': 'Remove Nozzles & O-Rings', 'category': 'PREPARATION',
        'sort_order': 15, 'default_estimated_minutes': 15, 'is_default_included': False,
        'instructions_general': 'Remove all nozzles and O-rings. Store for reinstallation.',
    },
    {
        'code': 'RMV-EROSION', 'name': 'Remove Erosion Sleeve', 'category': 'PREPARATION',
        'sort_order': 16, 'default_estimated_minutes': 20, 'is_default_included': False,
        'instructions_general': 'Remove erosion sleeve before further processing.',
    },
    {
        'code': 'WASH-BIT', 'name': 'Wash Bit', 'category': 'PREPARATION',
        'sort_order': 17, 'default_estimated_minutes': 20, 'is_default_included': False,
        'instructions_general': 'Wash bit to remove field debris and contamination.',
        'applies_to_new': False, 'applies_to_repair': True,
    },
    {
        'code': 'SAND-BLAST', 'name': 'Sand Blast', 'category': 'PREPARATION',
        'sort_order': 18, 'default_estimated_minutes': 20, 'is_default_included': False,
        'instructions_general': 'Sand blast bit body to remove paint, corrosion, and surface contaminants.',
    },

    # ─── EVALUATION ────────────────────────────────────────────────────────
    {
        'code': 'VISUAL-INSP', 'name': 'Production Receiving Evaluation', 'category': 'EVALUATION',
        'sort_order': 20, 'default_estimated_minutes': 30, 'requires_qc': True,
        'instructions_general': (
            'Full production evaluation. Evaluator decides all needed work: '
            'cutter replacement, build up, hardfacing, USR, threading, grinding, etc.'
        ),
        'procedure_reference': 'QAS/1006 Rev L, Section 3.2',
        'dedicated_page': 'cutter_eval',
    },
    {
        'code': 'PRINT-PACKET', 'name': 'Print WO Packet', 'category': 'EVALUATION',
        'sort_order': 38, 'default_estimated_minutes': 5,
        'instructions_general': 'Print work order packet with all evaluation findings and instructions.',
    },

    # ─── PREPARATION ───────────────────────────────────────────────────────
    {
        'code': 'DEBRAZE-DEC', 'name': 'De-Braze Decision & Prep', 'category': 'PREPARATION',
        'sort_order': 40, 'default_estimated_minutes': 10, 'is_default_included': False,
        'instructions_general': (
            'Technical instruction driven. Route: evaluation → sand blast → '
            'preparation (cover cutters by flux, close holes by mud, install thermocouple, '
            'heat in kiln) → debraze (remove cutters) → cool down → sand blast → take photos → '
            'send body to warehouse. Cutters: sand blast → die check → document → QC approval → store.'
        ),
        'applies_to_new': True, 'applies_to_repair': True,
    },
    {
        'code': 'CEREBRO-RMV', 'name': 'Cerebro Cap, O-Ring & Device Removal', 'category': 'PREPARATION',
        'sort_order': 45, 'default_estimated_minutes': 20, 'is_default_included': False,
        'instructions_general': (
            'Always remove cap and O-ring even if no device inside. '
            'If device present, remove and store safely for reinstallation.'
        ),
        'safety_notes': 'Handle Cerebro device with care — sensitive electronics.',
        'checklist_items': [
            {'text': 'Cap removed', 'required': True},
            {'text': 'O-ring removed', 'required': True},
            {'text': 'Device removed and stored (if present)', 'required': True},
            {'text': 'Cavity cleaned', 'required': True},
        ],
    },
    {
        'code': 'TORPEDO-RMV', 'name': 'Torpedo Housing & Thread Protector Removal', 'category': 'PREPARATION',
        'sort_order': 46, 'default_estimated_minutes': 20, 'is_default_included': False,
        'instructions_general': 'Remove torpedo housing or thread protector from internal diameter side.',
        'checklist_items': [
            {'text': 'Housing / thread protector removed', 'required': True},
            {'text': 'Internal thread inspected', 'required': True},
        ],
    },
    {
        'code': 'HEATING', 'name': 'Heating (De-Braze)', 'category': 'PREPARATION',
        'sort_order': 50, 'default_estimated_minutes': 120, 'is_default_included': False,
        'instructions_general': 'Heat bit in kiln to loosen braze for cutter removal. Not all repairs — only when evaluation determines debraze is needed.',
        'parameters_spec': [
            {'name': 'Kiln Temperature', 'type': 'number', 'unit': '°C', 'required': True, 'default_min': 650, 'default_max': 750, 'out_of_range_action': 'BLOCK'},
            {'name': 'Time in Kiln', 'type': 'number', 'unit': 'min', 'required': True, 'default_min': 90, 'default_max': 180},
        ],
    },
    {
        'code': 'CUTTER-RMV', 'name': 'Cutter Removal & Cleaning', 'category': 'PREPARATION',
        'sort_order': 60, 'default_estimated_minutes': 45, 'is_default_included': False,
        'instructions_general': (
            'Remove cutters and clean pockets. Evaluation-driven: needed when build up, '
            'hardfacing, or cutter replacement is required. Applies to both repair and new bits.'
        ),
        'time_factors': {'per_cutter': 1.5},
        'applies_to_new': True, 'applies_to_repair': True,
    },
    {
        'code': 'BUILDUP', 'name': 'Build Up (Pocket or Body)', 'category': 'PREPARATION',
        'sort_order': 85, 'default_estimated_minutes': 60, 'is_default_included': False,
        'instructions_general': (
            'Build up worn pockets or body areas. Both Steel and Matrix body. '
            'Process includes: heating → build up → cooling → sand blast → pocket cleaning.'
        ),
        'time_factors': {'per_cutter': 3},
        'safety_notes': 'Welding PPE required. Ensure proper ventilation.',
    },
    {
        'code': 'TIG-WELD', 'name': 'TIG Welding', 'category': 'PREPARATION',
        'sort_order': 86, 'default_estimated_minutes': 45, 'is_default_included': False,
        'instructions_general': 'TIG welding for steel body bits. Evaluation-driven.',
        'safety_notes': 'Welding PPE required.',
    },
    {
        'code': 'HARDFACING', 'name': 'Hardfacing (Body or Pocket)', 'category': 'PREPARATION',
        'sort_order': 87, 'default_estimated_minutes': 60, 'is_default_included': False,
        'instructions_general': (
            'Apply hardfacing to steel body for wear protection. '
            'Process includes: heating → hardfacing → cooling → sand blast.'
        ),
        'safety_notes': 'Welding PPE required.',
    },
    {
        'code': 'POST-BUILDUP-CLEAN', 'name': 'Pocket Cleaning After Build Up', 'category': 'PREPARATION',
        'sort_order': 88, 'default_estimated_minutes': 30, 'is_default_included': False,
        'instructions_general': (
            'Clean pockets after build up / hardfacing sand blast. '
            'If only body work (no pocket build up) → skip to brazing.'
        ),
        'time_factors': {'per_cutter': 1},
    },

    # ─── PRE-BRAZE PREPARATION ─────────────────────────────────────────────
    {
        'code': 'DYNAMIC-PREP', 'name': 'Dynamic Cutter Stator Preparation', 'category': 'PREPARATION',
        'sort_order': 89, 'default_estimated_minutes': 30, 'is_default_included': False,
        'instructions_general': 'Prepare stators with graphite plugs before brazing.',
        'time_factors': {'per_cutter': 3},
    },
    {
        'code': 'PRE-BRAZE-PREP', 'name': 'Pre-Braze Preparation', 'category': 'PREPARATION',
        'sort_order': 90, 'default_estimated_minutes': 60, 'is_default_included': False,
        'instructions_general': (
            'Sand blast body and cutters, add brazing discs to pockets, add paste flux, '
            'close holes by mud, load cutters on bit, cover by steel foil, '
            'install thermocouple, load bit to kiln, add cutters that cannot be loaded to cutter oven.'
        ),
        'time_factors': {'per_blade': 5, 'per_cutter': 1},
    },

    # ─── BRAZING ───────────────────────────────────────────────────────────
    {
        'code': 'BRAZING', 'name': 'Brazing', 'category': 'BRAZING',
        'sort_order': 100, 'default_estimated_minutes': 90, 'is_default_included': False,
        'instructions_general': (
            'Single brazing process. Required only if cutters need to be replaced, spun, or rotated. '
            'Not needed for rerun or minor-repair-only jobs.'
        ),
        'procedure_reference': 'QAS/1006 Rev L, Section 4.11',
        'parameters_spec': [
            {'name': 'Preheat Temperature', 'type': 'number', 'unit': '°C', 'required': True, 'default_min': 650, 'default_max': 700, 'out_of_range_action': 'BLOCK'},
            {'name': 'Brazing Temperature', 'type': 'number', 'unit': '°C', 'required': True, 'default_min': 680, 'default_max': 720, 'out_of_range_action': 'BLOCK'},
            {'name': 'Hold Time', 'type': 'number', 'unit': 'min', 'required': True, 'default_min': 10, 'default_max': 20},
            {'name': 'Filler Alloy', 'type': 'text', 'required': True},
        ],
        'time_factors': {'per_blade': 10, 'size_factor': {'8.5': 1.0, '12.25': 1.3, '16': 1.6}},
    },
    {
        'code': 'INSOOL-WRAP', 'name': 'Insool Wrap', 'category': 'BRAZING',
        'sort_order': 112, 'default_estimated_minutes': 15, 'is_default_included': False,
        'instructions_general': (
            'Wrap bit with insool after brazing for controlled cooling. '
            'Required for: Matrix body >12 inches, or any Core Head (regardless of size).'
        ),
    },
    {
        'code': 'REWORK', 'name': 'Rework / Touch-up', 'category': 'BRAZING',
        'sort_order': 115, 'default_estimated_minutes': 30, 'is_default_included': False,
        'instructions_general': 'Rework any areas with insufficient brazing. Touch up voids or weak joints.',
    },
    {
        'code': 'COOLDOWN', 'name': 'Cool-down', 'category': 'BRAZING',
        'sort_order': 120, 'default_estimated_minutes': 60, 'is_default_included': False,
        'step_mode': 'PASSIVE',
        'instructions_general': 'Allow controlled cooling after brazing. Do not force-cool.',
        'parameters_spec': [
            {'name': 'Cool-down Time', 'type': 'number', 'unit': 'min', 'required': True},
            {'name': 'Final Temperature', 'type': 'number', 'unit': '°C', 'required': False},
        ],
    },

    {
        'code': 'SOAKING', 'name': 'Soaking in Bit Bath', 'category': 'BRAZING',
        'sort_order': 122, 'default_estimated_minutes': 30, 'is_default_included': False,
        'step_mode': 'PASSIVE',
        'instructions_general': 'Soak bit in bit bath after cool-down.',
    },
    {
        'code': 'POST-BRAZE-BLAST', 'name': 'Sand Blast (Post-Braze)', 'category': 'BRAZING',
        'sort_order': 124, 'default_estimated_minutes': 20, 'is_default_included': False,
        'instructions_general': 'Sand blast bit after soaking, before grinding.',
    },

    # ─── POST-BRAZE ────────────────────────────────────────────────────────
    {
        'code': 'POST-BRAZE-INSP', 'name': 'Post-Braze Inspection', 'category': 'QC',
        'sort_order': 130, 'default_estimated_minutes': 20, 'requires_qc': True,
        'is_default_included': False,
        'instructions_general': 'Post-braze inspection. Aramco repair only.',
        'checklist_items': [
            {'text': 'All cutters firmly brazed', 'required': True},
            {'text': 'No visible voids or gaps', 'required': True},
            {'text': 'Cutter alignment correct', 'required': True},
            {'text': 'No brazing overflow on body', 'required': True},
        ],
    },

    # ─── GRINDING ──────────────────────────────────────────────────────────
    {
        'code': 'CORE-GRIND', 'name': 'Core Area Grinding', 'category': 'GRINDING',
        'sort_order': 137, 'default_estimated_minutes': 30, 'is_default_included': False,
        'instructions_general': 'Grind core area. Core head bits only.',
    },
    {
        'code': 'GRINDING', 'name': 'Finish Grinding', 'category': 'GRINDING',
        'sort_order': 140, 'default_estimated_minutes': 45, 'is_default_included': False,
        'instructions_general': (
            'Hand-held grinder with pointed stones to clean excessive braze after brazing '
            'or to remove tungs from body damage and make it smooth.'
        ),
        'time_factors': {'size_factor': {'8.5': 1.0, '12.25': 1.5, '16': 2.0}},
    },
    {
        'code': 'TIP-GRIND', 'name': 'Tip Grinding', 'category': 'GRINDING',
        'sort_order': 143, 'default_estimated_minutes': 30, 'is_default_included': False,
        'instructions_general': 'Grind cutter tips to restore gauge. Verify with ring gauge after. Only if brazing was done.',
    },
    {
        'code': 'GAUGE-UNDERCUT', 'name': 'Gauge Undercut', 'category': 'GRINDING',
        'sort_order': 144, 'default_estimated_minutes': 30, 'is_default_included': False,
        'instructions_general': 'Undercut gauge per technical instruction specifications.',
    },
    {
        'code': 'POST-GRIND-WASH', 'name': 'Washing (Post-Grinding)', 'category': 'GRINDING',
        'sort_order': 145, 'default_estimated_minutes': 15, 'is_default_included': False,
        'instructions_general': 'Wash bit after tip grinding and undercut, before die check.',
    },
    {
        'code': 'PRE-DC-BLAST', 'name': 'Sand Blast (Pre-Die Check)', 'category': 'GRINDING',
        'sort_order': 146, 'default_estimated_minutes': 15, 'is_default_included': False,
        'instructions_general': 'Sand blast after washing, before die check.',
    },
    {
        'code': 'DYNAMIC-POST', 'name': 'Dynamic Cutter — Remove Graphite', 'category': 'GRINDING',
        'sort_order': 147, 'default_estimated_minutes': 20, 'is_default_included': False,
        'instructions_general': 'Remove graphite plugs from stators after tip grinding.',
    },

    # ─── DIE CHECK (MULTI-INSTANCE) ───────────────────────────────────────
    {
        'code': 'DIE-CHECK', 'name': 'Die Check (Fluorescent Penetrant)', 'category': 'QC',
        'sort_order': 148, 'default_estimated_minutes': 45, 'requires_qc': True,
        'step_mode': 'MULTI',
        'instructions_general': 'Perform fluorescent penetrant testing per QAS/1004-1.',
        'procedure_reference': 'QAS/1004-1',
        'dedicated_page': 'die_check',
        'parameters_spec': [
            {'name': 'Surface Temperature', 'type': 'number', 'unit': '°C', 'required': True, 'default_min': 15, 'default_max': 50, 'out_of_range_action': 'BLOCK'},
            {'name': 'Penetrant Dwell Time', 'type': 'number', 'unit': 'min', 'required': True, 'default_min': 10, 'default_max': 30},
            {'name': 'Developer Dwell Time', 'type': 'number', 'unit': 'min', 'required': True, 'default_min': 10, 'default_max': 30},
        ],
        'checklist_items': [
            {'text': 'Surface cleaned before application', 'required': True},
            {'text': 'Penetrant applied evenly', 'required': True},
            {'text': 'Excess penetrant removed', 'required': True},
            {'text': 'Developer applied', 'required': True},
            {'text': 'UV inspection performed', 'required': True},
        ],
        # Insertion points configurable on ANY process by evaluator
        'insertion_points': [
            {'label': 'Die Check — Post Braze', 'after_process_code': 'POST-BRAZE-INSP', 'auto_include': False},
            {'label': 'Die Check — After Grinding', 'after_process_code': 'TIP-GRIND', 'auto_include': False},
            {'label': 'Die Check — After Machining', 'after_process_code': 'SHANK-MACH', 'auto_include': False},
            {'label': 'Die Check — Final', 'after_process_code': 'FINAL-QC', 'auto_include': False},
        ],
    },

    # ─── ASSEMBLY ──────────────────────────────────────────────────────────
    {
        'code': 'SUB-ARC', 'name': 'Sub-Arc Welding', 'category': 'ASSEMBLY',
        'sort_order': 155, 'default_estimated_minutes': 90, 'is_default_included': False,
        'instructions_general': 'Sub-arc weld upper section to bit head. Verify alignment before welding.',
        'safety_notes': 'Welding PPE required. UV protection.',
        'applies_to_levels': ['3', '5.5'],
    },
    {
        'code': 'USR', 'name': 'Upper Section Replacement', 'category': 'ASSEMBLY',
        'sort_order': 156, 'default_estimated_minutes': 90, 'is_default_included': False,
        'instructions_general': (
            'Replace upper section/shank. '
            'BLOCKED if: shankless OR cerebro puck OR weld-over-void design. '
            'If blocked → message "Contact technical team" (accept as-is / send to USA / hold / scrap). '
            'Torpedo designs: USR IS possible (size >= 8 1/2").'
        ),
        'applies_to_new': False, 'applies_to_repair': True,
    },
    {
        'code': 'SHANK-CLEAN', 'name': 'Shank Cleaning', 'category': 'ASSEMBLY',
        'sort_order': 157, 'default_estimated_minutes': 30, 'is_default_included': False,
        'instructions_general': 'Clean shank area. Sub-type determined by evaluator: by machining or by grinding.',
    },
    {
        'code': 'SHANK-MACH', 'name': 'Shank Machining', 'category': 'ASSEMBLY',
        'sort_order': 160, 'default_estimated_minutes': 60, 'is_default_included': False,
        'instructions_general': 'Machine shank after sub-arc welding to final dimensions. L3 and L5.5 only.',
        'applies_to_levels': ['3', '5.5'],
    },
    {
        'code': 'POST-MACH-DC', 'name': 'Post-Machining Die Check', 'category': 'QC',
        'sort_order': 162, 'default_estimated_minutes': 30, 'requires_qc': True,
        'is_default_included': False,
        'instructions_general': 'Die check after shank machining. For L3/L5.5 bits with ports.',
        'applies_to_levels': ['3', '5.5'],
    },
    {
        'code': 'POST-MACH-PT', 'name': 'Post-Machining Pressure Test', 'category': 'QC',
        'sort_order': 163, 'default_estimated_minutes': 30, 'requires_qc': True,
        'is_default_included': False,
        'instructions_general': 'Pressure test after shank machining. For L3/L5.5 bits without ports.',
        'applies_to_levels': ['3', '5.5'],
    },
    {
        'code': 'THREADING', 'name': 'Thread Repair', 'category': 'THREADING',
        'sort_order': 170, 'default_estimated_minutes': 30, 'is_default_included': False,
        'instructions_general': 'Machine or repair connection threads per API specifications. Sub-type: machining or grinding.',
        'parameters_spec': [
            {'name': 'Thread Type', 'type': 'text', 'required': True},
            {'name': 'Pin Height', 'type': 'number', 'unit': 'mm', 'required': True, 'out_of_range_action': 'BLOCK'},
        ],
    },

    # ─── PRE-FINAL QC ─────────────────────────────────────────────────────
    {
        'code': 'PRE-FINAL-CHECK', 'name': 'Quick Check Before Assembly', 'category': 'QC',
        'sort_order': 176, 'default_estimated_minutes': 10, 'is_default_included': False,
        'requires_qc': True,
        'instructions_general': (
            'Quick die check to verify no rework is needed before installing '
            'dynamic cutter rotors or crush & shear components.'
        ),
    },
    {
        'code': 'DYNAMIC-INST', 'name': 'Dynamic Cutter Rotor Installation', 'category': 'SPECIAL',
        'sort_order': 177, 'default_estimated_minutes': 45, 'is_default_included': False,
        'instructions_general': 'Install rotor part of dynamic cutters before final QC.',
        'time_factors': {'per_cutter': 3},
    },
    {
        'code': 'CS-INST', 'name': 'Crush & Shear Installation', 'category': 'SPECIAL',
        'sort_order': 178, 'default_estimated_minutes': 60, 'is_default_included': False,
        'instructions_general': (
            'Install crush & shear components → heat → TIG weld → cool. '
            'New bits: install. Repair bits: replace. Before final QC.'
        ),
        'safety_notes': 'Welding PPE required for TIG step.',
    },

    # ─── FINAL QC ─────────────────────────────────────────────────────────
    {
        'code': 'FINAL-QC', 'name': 'Final QC Evaluation', 'category': 'QC',
        'sort_order': 200, 'default_estimated_minutes': 30, 'requires_qc': True,
        'instructions_general': 'Final quality check. All measurements, documentation, and visual inspection.',
        'dedicated_page': 'cutter_eval',
        'checklist_items': [
            {'text': 'All measurements within spec', 'required': True},
            {'text': 'Documentation complete', 'required': True},
            {'text': 'Photos uploaded', 'required': True},
            {'text': 'Die check passed', 'required': True},
        ],
    },
    {
        'code': 'PRESSURE-TEST', 'name': 'Pressure Test', 'category': 'QC',
        'sort_order': 190, 'default_estimated_minutes': 30, 'is_default_included': False,
        'requires_qc': True,
        'instructions_general': (
            'Pressure test. For L4 bits without ports: by default after Final QC. '
            'For L3/L5.5 bits without ports: after shank machining (POST-MACH-PT handles that). '
            'Also available if evaluator requests after Final QC.'
        ),
        'parameters_spec': [
            {'name': 'Test Pressure', 'type': 'number', 'unit': 'psi', 'required': True, 'out_of_range_action': 'BLOCK'},
            {'name': 'Hold Time', 'type': 'number', 'unit': 'min', 'required': True},
            {'name': 'Result', 'type': 'choice', 'choices': ['Pass', 'Fail'], 'required': True},
        ],
    },
    {
        'code': 'FINAL-INSP', 'name': 'Final Inspection', 'category': 'QC',
        'sort_order': 205, 'default_estimated_minutes': 20, 'requires_qc': True,
        'instructions_general': 'Final sign-off inspection. Includes documentation review.',
    },

    # ─── FINISHING ─────────────────────────────────────────────────────────
    {
        'code': 'INST-EROSION', 'name': 'Install Erosion Sleeve', 'category': 'FINISHING',
        'sort_order': 208, 'default_estimated_minutes': 20, 'is_default_included': False,
        'instructions_general': 'Install erosion sleeve per design specification.',
    },
    {
        'code': 'INST-TUNGSTEN', 'name': 'Install Tungsten Nozzle Bore Liner', 'category': 'FINISHING',
        'sort_order': 209, 'default_estimated_minutes': 20, 'is_default_included': False,
        'instructions_general': 'Install tungsten nozzle bore liner. Uses the liner and drawing checked at receiving.',
    },
    {
        'code': 'PAINTING', 'name': 'Painting', 'category': 'FINISHING',
        'sort_order': 210, 'default_estimated_minutes': 30,
        'instructions_general': 'Paint bit body per specification. Apply stamping.',
    },
    {
        'code': 'CEREBRO-INST', 'name': 'Cerebro Installation or Cap Close', 'category': 'FINISHING',
        'sort_order': 215, 'default_estimated_minutes': 20, 'is_default_included': False,
        'instructions_general': (
            'If instruction for full install → install Cerebro device, O-ring, and cap. '
            'If no instruction → close cap and install O-ring only.'
        ),
        'checklist_items': [
            {'text': 'Cavity clean and dry', 'required': True},
            {'text': 'O-ring installed', 'required': True},
            {'text': 'Device seated properly (if full install)', 'required': False},
            {'text': 'Cap torqued to spec', 'required': True},
        ],
    },
    {
        'code': 'TORPEDO-INST', 'name': 'Torpedo Installation or Thread Protector', 'category': 'FINISHING',
        'sort_order': 216, 'default_estimated_minutes': 20, 'is_default_included': False,
        'instructions_general': (
            'If torpedo available → install torpedo housing from internal diameter side. '
            'If no torpedo → install thread protector to protect internal thread. '
            'Size >= 8 1/2".'
        ),
    },

    # ─── DISPATCH ──────────────────────────────────────────────────────────
    {
        'code': 'PACK-LABEL', 'name': 'Pack & Label', 'category': 'DISPATCH',
        'sort_order': 225, 'default_estimated_minutes': 15,
        'instructions_general': 'Pack bit in protective case. Apply labels and shipping documents.',
    },
    {
        'code': 'DISPATCH', 'name': 'Dispatch Preparation', 'category': 'DISPATCH',
        'sort_order': 230, 'default_estimated_minutes': 10,
        'instructions_general': 'Prepare for dispatch. Verify destination and transport.',
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# RULES — conditional inclusion/exclusion
# ═══════════════════════════════════════════════════════════════════════════════

RULES = [
    # ── Receiving / Preparation ──
    {'process': 'RMV-NOZZLE', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.has_nozzles', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Remove nozzles if installed'},
    {'process': 'RMV-EROSION', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.has_erosion_sleeve', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Remove erosion sleeve if installed'},
    {'process': 'WASH-BIT', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.is_repair', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Wash bit for repair jobs'},
    {'process': 'SAND-BLAST', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.is_repair', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Sand blast for repair jobs'},
    {'process': 'SAND-BLAST', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.is_painted', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Sand blast if painted'},

    # ── Cerebro / Torpedo ──
    {'process': 'CEREBRO-RMV', 'rule_type': 'INCLUDE_IF', 'field_path': 'tech.has_cerebro', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Remove cerebro cap/device if design has cerebro technology'},
    {'process': 'CEREBRO-INST', 'rule_type': 'INCLUDE_IF', 'field_path': 'tech.has_cerebro', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Install cerebro or close cap if design has cerebro technology'},
    {'process': 'TORPEDO-RMV', 'rule_type': 'INCLUDE_IF', 'field_path': 'tech.has_torpedo', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Remove torpedo housing/thread protector if torpedo design'},
    {'process': 'TORPEDO-INST', 'rule_type': 'INCLUDE_IF', 'field_path': 'tech.has_torpedo', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Install torpedo or thread protector if torpedo design'},

    # ── Debraze (technical instruction driven) ──
    {'process': 'DEBRAZE-DEC', 'rule_type': 'INCLUDE_IF', 'field_path': 'tech.instruction_debraze', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Debraze decision when technical instruction requires it'},
    {'process': 'HEATING', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_debraze', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Heating when debraze is needed'},
    {'process': 'CUTTER-RMV', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_cutter_removal', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Cutter removal when evaluation requires it (build up, hardface, replacement)'},

    # ── Eval-driven preparation ──
    {'process': 'BUILDUP', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_buildup', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Build up when evaluator determines needed'},
    {'process': 'TIG-WELD', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_tig', 'operator': 'EQUALS', 'value': 'True',
     'description': 'TIG welding when evaluator determines needed'},
    {'process': 'TIG-WELD', 'rule_type': 'EXCLUDE_IF', 'field_path': 'design.body_material', 'operator': 'NOT_EQUALS', 'value': 'S',
     'description': 'TIG welding only for steel body', 'priority': 20},
    {'process': 'HARDFACING', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_hardfacing', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Hardfacing when evaluator determines needed'},
    {'process': 'HARDFACING', 'rule_type': 'EXCLUDE_IF', 'field_path': 'design.body_material', 'operator': 'NOT_EQUALS', 'value': 'S',
     'description': 'Hardfacing only for steel body', 'priority': 20},
    {'process': 'POST-BUILDUP-CLEAN', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_buildup', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Pocket cleaning after build up'},
    {'process': 'REWORK', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_rework', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Rework when QC identifies issues'},
    {'process': 'GRINDING', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_grinding', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Finish grinding when evaluator requests it'},
    {'process': 'GAUGE-UNDERCUT', 'rule_type': 'INCLUDE_IF', 'field_path': 'tech.undercut_gauge', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Gauge undercut per technical instruction'},

    # ── Brazing (eval-driven) ──
    {'process': 'PRE-BRAZE-PREP', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_brazing', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Pre-braze preparation when brazing is needed'},
    {'process': 'BRAZING', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_brazing', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Brazing when cutters need replace/spin/rotate'},
    {'process': 'COOLDOWN', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_brazing', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Cool-down after brazing'},
    {'process': 'SOAKING', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_brazing', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Soaking in bit bath after cool-down'},
    {'process': 'POST-BRAZE-BLAST', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_brazing', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Sand blast after soaking before grinding'},
    {'process': 'TIP-GRIND', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_brazing', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Tip grinding after brazing'},
    {'process': 'POST-GRIND-WASH', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_brazing', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Washing after tip grinding before die check'},
    {'process': 'PRE-DC-BLAST', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_brazing', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Sand blast after washing before die check'},

    # ── Insool wrap ──
    # Rule expression handles: (body_material=M AND size>12) OR is_core_head
    # Using rule_expression on the process instead of simple rules

    # ── Dynamic cutters (3-phase) ──
    {'process': 'DYNAMIC-PREP', 'rule_type': 'INCLUDE_IF', 'field_path': 'bom.has_dynamic_cutters', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Stator preparation with graphite plugs for dynamic cutters'},
    {'process': 'DYNAMIC-POST', 'rule_type': 'INCLUDE_IF', 'field_path': 'bom.has_dynamic_cutters', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Remove graphite plugs after tip grinding'},
    {'process': 'DYNAMIC-INST', 'rule_type': 'INCLUDE_IF', 'field_path': 'bom.has_dynamic_cutters', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Install dynamic cutter rotors before final QC'},
    {'process': 'PRE-FINAL-CHECK', 'rule_type': 'INCLUDE_IF', 'field_path': 'bom.has_dynamic_cutters', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Quick check before dynamic cutter installation'},

    # ── Crush & shear ──
    {'process': 'CS-INST', 'rule_type': 'INCLUDE_IF', 'field_path': 'tech.has_crush_shear', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Install/replace crush & shear components'},
    {'process': 'PRE-FINAL-CHECK', 'rule_type': 'INCLUDE_IF', 'field_path': 'tech.has_crush_shear', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Quick check before C&S installation'},

    # ── Post-braze inspection (Aramco repair only) ──
    {'process': 'POST-BRAZE-INSP', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.account', 'operator': 'EQUALS', 'value': 'ARAMCO',
     'description': 'Post-braze inspection for Aramco account'},
    {'process': 'POST-BRAZE-INSP', 'rule_type': 'EXCLUDE_IF', 'field_path': 'bit.is_new', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Post-braze inspection only for repair', 'priority': 20},

    # ── Core head ──
    {'process': 'CORE-GRIND', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.is_core_head', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Core area grinding for core head bits'},

    # ── Assembly: Sub-arc / machining / post-machining tests ──
    {'process': 'SUB-ARC', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.level', 'operator': 'IN_LIST', 'value': '3,5.5',
     'description': 'Sub-arc welding for L3 and L5.5'},
    {'process': 'SHANK-MACH', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.level', 'operator': 'IN_LIST', 'value': '3,5.5',
     'description': 'Shank machining after sub-arc for L3 and L5.5'},
    {'process': 'POST-MACH-DC', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.level', 'operator': 'IN_LIST', 'value': '3,5.5',
     'description': 'Post-machining die check for L3/L5.5'},
    {'process': 'POST-MACH-DC', 'rule_type': 'EXCLUDE_IF', 'field_path': 'design.has_ports', 'operator': 'NOT_EQUALS', 'value': 'True',
     'description': 'Post-machining die check only if has ports', 'priority': 20},
    {'process': 'POST-MACH-PT', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.level', 'operator': 'IN_LIST', 'value': '3,5.5',
     'description': 'Post-machining pressure test for L3/L5.5'},
    {'process': 'POST-MACH-PT', 'rule_type': 'EXCLUDE_IF', 'field_path': 'design.has_ports', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Post-machining pressure test only if NO ports', 'priority': 20},

    # ── Pressure test (L4 default, no ports) ──
    {'process': 'PRESSURE-TEST', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.level', 'operator': 'IN_LIST', 'value': '4,5',
     'description': 'Pressure test default for L4/L5 bits'},
    {'process': 'PRESSURE-TEST', 'rule_type': 'EXCLUDE_IF', 'field_path': 'design.has_ports', 'operator': 'EQUALS', 'value': 'True',
     'description': 'No pressure test if has ports', 'priority': 20},

    # ── USR (eval-driven with blocking) ──
    {'process': 'USR', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_usr', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Upper section replacement when evaluation requires it'},

    # ── Shank cleaning / threading ──
    {'process': 'SHANK-CLEAN', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_shank_cleaning', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Shank cleaning when evaluation requires it'},
    {'process': 'THREADING', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_thread_repair', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Thread repair when evaluation requires it'},

    # ── Finishing ──
    {'process': 'INST-EROSION', 'rule_type': 'INCLUDE_IF', 'field_path': 'design.erosion_sleeve', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Install erosion sleeve if design has it'},
    {'process': 'INST-TUNGSTEN', 'rule_type': 'INCLUDE_IF', 'field_path': 'design.body_material', 'operator': 'EQUALS', 'value': 'S',
     'description': 'Install tungsten liner for steel body'},
]


# ═══════════════════════════════════════════════════════════════════════════════
# Rule expressions for complex conditions (AND/OR logic)
# ═══════════════════════════════════════════════════════════════════════════════

RULE_EXPRESSIONS = {
    # Insool wrap: (Matrix body AND size > 12) OR core head
    'INSOOL-WRAP': {
        'type': 'OR',
        'conditions': [
            {
                'type': 'AND',
                'conditions': [
                    {'field': 'design.body_material', 'op': 'EQUALS', 'val': 'M'},
                    {'field': 'bit.size', 'op': 'GT', 'val': '12'},
                ]
            },
            {'field': 'bit.is_core_head', 'op': 'EQUALS', 'val': 'True'},
        ]
    },
}


class Command(BaseCommand):
    help = 'Seed the Master Process Library with FC bit steps and inclusion rules'

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true', help='Actually create/update processes')
        parser.add_argument('--clean', action='store_true', help='Delete all existing processes and rules first')

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write('Dry run. Pass --confirm to create/update processes.')
            for p in PROCESSES:
                self.stdout.write(f"  {p['code']:20s} {p['name']}")
            self.stdout.write(f'\n  {len(PROCESSES)} processes, {len(RULES)} rules')
            return

        if options['clean']:
            deleted_rules = ProcessInclusionRule.objects.all().delete()
            deleted_procs = MasterProcess.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f'Cleaned: {deleted_procs[0]} processes, {deleted_rules[0]} rules'
            ))

        created = 0
        updated = 0
        for data in PROCESSES:
            data = dict(data)  # copy to avoid mutating the source
            code = data.pop('code')
            name = data.pop('name')

            # Pop non-model fields
            data.pop('parameters_spec', None)
            data.pop('checklist_items', None)
            data.pop('insertion_points', None)

            # Set rule_expression if defined
            if code in RULE_EXPRESSIONS:
                data['rule_expression'] = RULE_EXPRESSIONS[code]

            # Always ensure active processes are active
            data['is_active'] = True

            obj, was_created = MasterProcess.objects.update_or_create(
                code=code,
                defaults={'name': name, **data}
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {code} — {name}'))
            else:
                updated += 1
                self.stdout.write(f'  Updated: {code} — {name}')

        # Delete old processes that are no longer in the table
        active_codes = {p['code'] for p in PROCESSES}
        removed_codes = ['BRAZE-L1', 'BRAZE-L2', 'STRESS-REL', 'MEAS-VERIFY',
                         'CLEAN-SURF', 'NOZZLE', 'FINAL-ASSY', 'DOC-REVIEW',
                         'BURNOUT', 'CUTTER-PREP', 'LAYOUT', 'POCKET-PREP',
                         'CORE-INSP', 'FINAL-DIE', 'QC-INSP', 'MACHINING',
                         'GAUGE-MEAS']
        deleted_count, _ = MasterProcess.objects.filter(code__in=removed_codes).delete()
        if deleted_count:
            self.stdout.write(self.style.WARNING(f'  Deleted {deleted_count} old processes'))

        # Create/update rules — clear old rules first for clean slate
        ProcessInclusionRule.objects.filter(
            master_process__code__in=active_codes
        ).delete()

        rules_created = 0
        for rule_data in RULES:
            rule_data = dict(rule_data)  # copy
            proc_code = rule_data.pop('process')
            try:
                proc = MasterProcess.objects.get(code=proc_code)
            except MasterProcess.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Process {proc_code} not found for rule'))
                continue

            ProcessInclusionRule.objects.create(
                master_process=proc,
                rule_type=rule_data['rule_type'],
                field_path=rule_data['field_path'],
                operator=rule_data['operator'],
                value=rule_data.get('value', ''),
                description=rule_data.get('description', ''),
                priority=rule_data.get('priority', 10),
            )
            rules_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Processes: {created} created, {updated} updated. '
            f'Rules: {rules_created} created.'
        ))
