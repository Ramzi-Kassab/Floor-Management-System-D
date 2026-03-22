"""
Seed the Master Process Library with all possible FC bit steps.
Includes inclusion/exclusion rules and parameter specs.

Usage:
    python manage.py seed_master_processes --confirm
"""
from django.core.management.base import BaseCommand
from apps.workorders.models import MasterProcess, ProcessInclusionRule


# All possible processes for PDC bits (new + repair)
PROCESSES = [
    # ═══ RECEIVING & SETUP ═══
    {
        'code': 'RCV-SETUP', 'name': 'Bit Receiving & Setup', 'category': 'RECEIVING',
        'sort_order': 10, 'default_estimated_minutes': 15,
        'instructions_general': 'Receive bit, verify serial number, record initial condition. Check paperwork matches physical bit.',
        'procedure_reference': 'QAS/1006 Rev L, Section 3.1',
        'applies_to_new': True, 'applies_to_repair': True,
    },
    {
        'code': 'VISUAL-INSP', 'name': 'Visual Inspection', 'category': 'EVALUATION',
        'sort_order': 20, 'default_estimated_minutes': 20, 'requires_qc': True,
        'instructions_general': 'Inspect bit for visible damage, cracks, wear, and missing components. Document all findings.',
        'procedure_reference': 'QAS/1006 Rev L, Section 3.2',
        'parameters_spec': [
            {'name': 'Overall Condition', 'type': 'choice', 'choices': ['Good', 'Fair', 'Poor', 'Damaged'], 'required': True},
        ],
        'checklist_items': [
            {'text': 'No visible cracks on body', 'required': True},
            {'text': 'All cutters present', 'required': True},
            {'text': 'Connection threads intact', 'required': True},
            {'text': 'Nozzles/ports condition noted', 'required': False},
        ],
    },
    {
        'code': 'GAUGE-MEAS', 'name': 'Gauge Measurements', 'category': 'EVALUATION',
        'sort_order': 30, 'default_estimated_minutes': 25, 'requires_qc': True,
        'instructions_general': 'Measure TFA, gauge readings (1-3), shank diameter. Record all values.',
        'procedure_reference': 'QAS/1006 Rev L, Section 3.3',
        'parameters_spec': [
            {'name': 'TFA', 'type': 'number', 'unit': 'in²', 'required': True,
             'ranges': {'3 5/8': {'min': 0.3, 'max': 1.5}, '5 7/8': {'min': 0.8, 'max': 3.0},
                        '8 1/2': {'min': 1.5, 'max': 6.0}, '12 1/4': {'min': 3.0, 'max': 10.0},
                        '16': {'min': 5.0, 'max': 15.0}},
             'out_of_range_action': 'WARN'},
            {'name': 'Gauge Reading 1', 'type': 'number', 'unit': 'in', 'required': True, 'out_of_range_action': 'WARN'},
            {'name': 'Gauge Reading 2', 'type': 'number', 'unit': 'in', 'required': True, 'out_of_range_action': 'WARN'},
            {'name': 'Gauge Reading 3', 'type': 'number', 'unit': 'in', 'required': False, 'out_of_range_action': 'WARN'},
            {'name': 'Shank Diameter', 'type': 'number', 'unit': 'mm', 'required': True,
             'ranges': {'3 5/8': {'min': 85.0, 'max': 85.5}, '5 7/8': {'min': 140.0, 'max': 140.5},
                        '8 1/2': {'min': 205.0, 'max': 205.5}, '12 1/4': {'min': 300.0, 'max': 300.5},
                        '16': {'min': 395.0, 'max': 395.5}},
             'out_of_range_action': 'BLOCK'},
        ],
    },

    # ═══ PREPARATION ═══
    {
        'code': 'DEBRAZE-DEC', 'name': 'De-Brazing Decision', 'category': 'PREPARATION',
        'sort_order': 40, 'default_estimated_minutes': 10,
        'instructions_general': 'Determine if de-brazing is needed based on evaluation findings. Record Cerebro removal decision.',
        'applies_to_new': False, 'applies_to_repair': True,
    },
    {
        'code': 'CEREBRO-RMV', 'name': 'Cerebro Device Removal', 'category': 'PREPARATION',
        'sort_order': 45, 'default_estimated_minutes': 20, 'is_default_included': False,
        'instructions_general': 'Remove Cerebro cap, O-ring, and device. Store device safely for reinstallation after production.',
        'safety_notes': 'Handle Cerebro device with care — sensitive electronics.',
        'checklist_items': [
            {'text': 'Cap removed', 'required': True},
            {'text': 'O-ring removed', 'required': True},
            {'text': 'Device removed and stored', 'required': True},
            {'text': 'Cavity cleaned', 'required': True},
        ],
    },
    {
        'code': 'BURNOUT', 'name': 'Burnout Furnace', 'category': 'PREPARATION',
        'sort_order': 50, 'default_estimated_minutes': 120, 'is_default_included': False,
        'instructions_general': 'Place bit in burnout furnace for de-brazing. Monitor temperature and time.',
        'applies_to_new': False, 'applies_to_repair': True,
        'parameters_spec': [
            {'name': 'Furnace Temperature', 'type': 'number', 'unit': '°C', 'required': True, 'default_min': 650, 'default_max': 750, 'out_of_range_action': 'BLOCK'},
            {'name': 'Time in Furnace', 'type': 'number', 'unit': 'min', 'required': True, 'default_min': 90, 'default_max': 180},
        ],
    },
    {
        'code': 'CUTTER-RMV', 'name': 'Cutter Removal & Cleaning', 'category': 'PREPARATION',
        'sort_order': 60, 'default_estimated_minutes': 45,
        'instructions_general': 'Remove old cutters, clean all pockets, prepare surfaces for new brazing.',
        'time_factors': {'per_cutter': 1.5},
        'applies_to_new': False, 'applies_to_repair': True,
    },
    {
        'code': 'CORE-INSP', 'name': 'Core Inspection', 'category': 'EVALUATION',
        'sort_order': 70, 'default_estimated_minutes': 20, 'requires_qc': True,
        'instructions_general': 'Inspect bit body core for cracks, erosion, and structural integrity after cutter removal.',
        'applies_to_new': False, 'applies_to_repair': True,
    },
    {
        'code': 'CUTTER-PREP', 'name': 'Cutter Preparation', 'category': 'PREPARATION',
        'sort_order': 80, 'default_estimated_minutes': 30,
        'instructions_general': 'Prepare new cutters per BOM. Verify cutter types, sizes, and quantities match the BOM.',
        'time_factors': {'per_cutter': 1},
    },
    {
        'code': 'BUILDUP', 'name': 'Pocket Build Up', 'category': 'PREPARATION',
        'sort_order': 85, 'default_estimated_minutes': 60, 'is_default_included': False,
        'instructions_general': 'Build up worn cutter pockets with welding material to restore proper depth and shape.',
        'time_factors': {'per_cutter': 3},
        'safety_notes': 'Welding PPE required. Ensure proper ventilation.',
    },
    {
        'code': 'LAYOUT', 'name': 'Layout & Marking', 'category': 'PREPARATION',
        'sort_order': 90, 'default_estimated_minutes': 20,
        'instructions_general': 'Mark cutter positions per BOM layout. Verify pocket alignment.',
    },
    {
        'code': 'POCKET-PREP', 'name': 'Pocket Preparation', 'category': 'PREPARATION',
        'sort_order': 95, 'default_estimated_minutes': 30,
        'instructions_general': 'Clean and prepare all pockets for brazing. Ensure proper fit for each cutter.',
        'time_factors': {'per_cutter': 1},
    },

    # ═══ BRAZING ═══
    {
        'code': 'BRAZE-L1', 'name': 'First Layer Brazing', 'category': 'BRAZING',
        'sort_order': 100, 'default_estimated_minutes': 90,
        'instructions_general': 'Apply first layer of brazing alloy. Preheat to specified temperature before applying filler.',
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
        'code': 'BRAZE-L2', 'name': 'Second Layer Brazing', 'category': 'BRAZING',
        'sort_order': 110, 'default_estimated_minutes': 60,
        'instructions_general': 'Apply second brazing layer for reinforcement. Ensure complete coverage.',
        'time_factors': {'per_blade': 8},
    },
    {
        'code': 'REWORK', 'name': 'Rework / Touch-up', 'category': 'BRAZING',
        'sort_order': 115, 'default_estimated_minutes': 30, 'is_default_included': False,
        'instructions_general': 'Rework any areas with insufficient brazing. Touch up voids or weak joints.',
    },
    {
        'code': 'COOLDOWN', 'name': 'Cool-down & Thermal Relief', 'category': 'BRAZING',
        'sort_order': 120, 'default_estimated_minutes': 60,
        'instructions_general': 'Allow controlled cooling. Do not force-cool.',
        'parameters_spec': [
            {'name': 'Cool-down Time', 'type': 'number', 'unit': 'min', 'required': True},
            {'name': 'Final Temperature', 'type': 'number', 'unit': '°C', 'required': False},
        ],
    },
    {
        'code': 'STRESS-REL', 'name': 'Thermal Stress Relief', 'category': 'BRAZING',
        'sort_order': 125, 'default_estimated_minutes': 45, 'is_default_included': False,
        'instructions_general': 'Apply thermal stress relief if required by bit design or material.',
    },

    # ═══ GRINDING & FINISHING ═══
    {
        'code': 'POST-BRAZE-INSP', 'name': 'Post-Braze Inspection', 'category': 'QC',
        'sort_order': 130, 'default_estimated_minutes': 20, 'requires_qc': True,
        'instructions_general': 'Inspect all brazed joints for quality. Check for voids, incomplete fills, or misalignment.',
        'checklist_items': [
            {'text': 'All cutters firmly brazed', 'required': True},
            {'text': 'No visible voids or gaps', 'required': True},
            {'text': 'Cutter alignment correct', 'required': True},
            {'text': 'No brazing overflow on body', 'required': True},
        ],
    },
    {
        'code': 'MEAS-VERIFY', 'name': 'Measurements Verification', 'category': 'QC',
        'sort_order': 135, 'default_estimated_minutes': 20, 'requires_qc': True,
        'instructions_general': 'Verify all measurements against specifications. Compare with pre-repair values.',
        'parameters_spec': [
            {'name': 'Final TFA', 'type': 'number', 'unit': 'in²', 'required': True, 'out_of_range_action': 'WARN'},
            {'name': 'Final Gauge', 'type': 'number', 'unit': 'in', 'required': True, 'out_of_range_action': 'WARN'},
        ],
    },
    {
        'code': 'GRINDING', 'name': 'Grinding', 'category': 'GRINDING',
        'sort_order': 140, 'default_estimated_minutes': 45, 'is_default_included': False,
        'instructions_general': 'Grind bit face per specifications. Maintain proper profile.',
        'time_factors': {'size_factor': {'8.5': 1.0, '12.25': 1.5, '16': 2.0}},
    },
    {
        'code': 'TIP-GRIND', 'name': 'Tip Grinding', 'category': 'GRINDING',
        'sort_order': 145, 'default_estimated_minutes': 30,
        'instructions_general': 'Grind cutter tips to restore gauge. Verify with ring gauge after.',
    },
    {
        'code': 'CLEAN-SURF', 'name': 'Cleaning & Surface Prep', 'category': 'FINISHING',
        'sort_order': 150, 'default_estimated_minutes': 20,
        'instructions_general': 'Clean entire bit. Remove all brazing residue, flux, and debris.',
    },

    # ═══ ASSEMBLY ═══
    {
        'code': 'SUB-ARC', 'name': 'Sub-Arc Welding', 'category': 'ASSEMBLY',
        'sort_order': 155, 'default_estimated_minutes': 90, 'is_default_included': False,
        'instructions_general': 'Sub-arc weld upper section to bit head. Verify alignment before welding.',
        'safety_notes': 'Welding PPE required. UV protection.',
        'applies_to_levels': ['3', '5.5'],
    },
    {
        'code': 'MACHINING', 'name': 'Machining', 'category': 'ASSEMBLY',
        'sort_order': 160, 'default_estimated_minutes': 60, 'is_default_included': False,
        'instructions_general': 'Machine welded assembly to final dimensions.',
        'applies_to_levels': ['3', '5.5'],
    },
    {
        'code': 'NOZZLE', 'name': 'Nozzle Installation', 'category': 'ASSEMBLY',
        'sort_order': 165, 'default_estimated_minutes': 20,
        'instructions_general': 'Install nozzles per design specification. Verify bore sizes.',
    },
    {
        'code': 'THREADING', 'name': 'Threading', 'category': 'THREADING',
        'sort_order': 170, 'default_estimated_minutes': 30, 'is_default_included': False,
        'instructions_general': 'Machine or repair connection threads per API specifications.',
        'parameters_spec': [
            {'name': 'Thread Type', 'type': 'text', 'required': True},
            {'name': 'Pin Height', 'type': 'number', 'unit': 'mm', 'required': True, 'out_of_range_action': 'BLOCK'},
        ],
    },
    {
        'code': 'FINAL-ASSY', 'name': 'Final Assembly', 'category': 'ASSEMBLY',
        'sort_order': 175, 'default_estimated_minutes': 20,
        'instructions_general': 'Complete final assembly. Install all remaining components.',
    },

    # ═══ QC & INSPECTION ═══
    {
        'code': 'QC-INSP', 'name': 'Quality Inspection', 'category': 'QC',
        'sort_order': 180, 'default_estimated_minutes': 30, 'requires_qc': True,
        'instructions_general': 'Full quality inspection per procedure. Verify all specifications met.',
    },
    {
        'code': 'DIE-CHECK', 'name': 'Die Check (Fluorescent Penetrant)', 'category': 'QC',
        'sort_order': 185, 'default_estimated_minutes': 45, 'requires_qc': True,
        'instructions_general': 'Perform fluorescent penetrant testing per QAS/1004-1. Clean, apply penetrant, developer, inspect under UV.',
        'procedure_reference': 'QAS/1004-1',
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
    },
    {
        'code': 'PRESSURE-TEST', 'name': 'Pressure Test', 'category': 'QC',
        'sort_order': 190, 'default_estimated_minutes': 30, 'is_default_included': True, 'requires_qc': True,
        'instructions_general': 'Perform pressure test per specifications. Record pressure and hold time.',
        'parameters_spec': [
            {'name': 'Test Pressure', 'type': 'number', 'unit': 'psi', 'required': True, 'out_of_range_action': 'BLOCK'},
            {'name': 'Hold Time', 'type': 'number', 'unit': 'min', 'required': True},
            {'name': 'Result', 'type': 'choice', 'choices': ['Pass', 'Fail'], 'required': True},
        ],
    },
    {
        'code': 'FINAL-DIE', 'name': 'Final Die Check', 'category': 'QC',
        'sort_order': 195, 'default_estimated_minutes': 30, 'requires_qc': True,
        'instructions_general': 'Final fluorescent penetrant test to verify no defects after all processing.',
        'procedure_reference': 'QAS/1004-1',
    },
    {
        'code': 'FINAL-QC', 'name': 'Final QC Evaluation', 'category': 'QC',
        'sort_order': 200, 'default_estimated_minutes': 30, 'requires_qc': True,
        'instructions_general': 'Final quality check. All measurements, documentation, and visual inspection.',
        'checklist_items': [
            {'text': 'All measurements within spec', 'required': True},
            {'text': 'Documentation complete', 'required': True},
            {'text': 'Photos uploaded', 'required': True},
            {'text': 'Die check passed', 'required': True},
        ],
    },
    {
        'code': 'FINAL-INSP', 'name': 'Final Inspection', 'category': 'QC',
        'sort_order': 205, 'default_estimated_minutes': 20, 'requires_qc': True,
        'instructions_general': 'Final sign-off inspection before dispatch preparation.',
    },

    # ═══ FINISHING & DISPATCH ═══
    {
        'code': 'PAINTING', 'name': 'Painting', 'category': 'FINISHING',
        'sort_order': 210, 'default_estimated_minutes': 30,
        'instructions_general': 'Paint bit body per specification. Apply stamping.',
    },
    {
        'code': 'CEREBRO-INST', 'name': 'Cerebro Device Installation', 'category': 'FINISHING',
        'sort_order': 215, 'default_estimated_minutes': 20, 'is_default_included': False,
        'instructions_general': 'Reinstall Cerebro device, O-ring, and cap after all production steps complete.',
        'checklist_items': [
            {'text': 'Cavity clean and dry', 'required': True},
            {'text': 'O-ring installed', 'required': True},
            {'text': 'Device seated properly', 'required': True},
            {'text': 'Cap torqued to spec', 'required': True},
        ],
    },
    {
        'code': 'DOC-REVIEW', 'name': 'Documentation Review', 'category': 'DISPATCH',
        'sort_order': 220, 'default_estimated_minutes': 15,
        'instructions_general': 'Review all work order documentation. Ensure completeness.',
    },
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

    # ═══ SPECIAL OPERATIONS ═══
    {
        'code': 'DYNAMIC-INST', 'name': 'Dynamic Cutter Installation', 'category': 'SPECIAL',
        'sort_order': 105, 'default_estimated_minutes': 45, 'is_default_included': False,
        'instructions_general': 'Install dynamic cutters per BOM specification. These require special handling and orientation.',
        'time_factors': {'per_cutter': 3},
    },
    {
        'code': 'USR', 'name': 'Upper Section Replacement', 'category': 'SPECIAL',
        'sort_order': 155, 'default_estimated_minutes': 90, 'is_default_included': False,
        'instructions_general': 'Replace upper section/shank. Verify thread compatibility.',
        'applies_to_new': False, 'applies_to_repair': True,
    },
    {
        'code': 'HARDFACING', 'name': 'Hardfacing Application', 'category': 'SPECIAL',
        'sort_order': 148, 'default_estimated_minutes': 60, 'is_default_included': False,
        'instructions_general': 'Apply hardfacing to bit body for wear protection.',
        'safety_notes': 'Welding PPE required.',
    },
    {
        'code': 'GAUGE-UNDERCUT', 'name': 'Gauge Undercut', 'category': 'GRINDING',
        'sort_order': 142, 'default_estimated_minutes': 30, 'is_default_included': False,
        'instructions_general': 'Undercut gauge per technical instruction specifications.',
    },
    {
        'code': 'INSOOL-WRAP', 'name': 'Insool Wrap', 'category': 'FINISHING',
        'sort_order': 122, 'default_estimated_minutes': 15, 'is_default_included': False,
        'instructions_general': 'Wrap bit with insool after brazing for controlled cooling. Required for Matrix body material on larger sizes.',
    },
]

# Rules for conditional inclusion/exclusion
RULES = [
    # Cerebro steps — include if bit has Cerebro technology
    {'process': 'CEREBRO-RMV', 'rule_type': 'INCLUDE_IF', 'field_path': 'tech.has_cerebro', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Include Cerebro removal if bit has Cerebro technology'},
    {'process': 'CEREBRO-INST', 'rule_type': 'INCLUDE_IF', 'field_path': 'tech.has_cerebro', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Include Cerebro installation if bit has Cerebro technology'},

    # Pressure test — exclude if bit has ports
    {'process': 'PRESSURE-TEST', 'rule_type': 'EXCLUDE_IF', 'field_path': 'design.has_ports', 'operator': 'EQUALS', 'value': 'True',
     'description': 'No pressure test for bits with ports'},

    # Sub-arc welding — only for L3 and L5.5 (already in applies_to_levels)
    {'process': 'SUB-ARC', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.level', 'operator': 'IN_LIST', 'value': '3,5.5',
     'description': 'Sub-arc welding for L3 and L5.5 bits'},
    {'process': 'MACHINING', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.level', 'operator': 'IN_LIST', 'value': '3,5.5',
     'description': 'Machining after sub-arc for L3 and L5.5'},

    # Burnout — only for repair bits needing de-brazing
    {'process': 'BURNOUT', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_debraze', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Burnout furnace when de-brazing is needed'},

    # Build up — added by evaluator
    {'process': 'BUILDUP', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_buildup', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Pocket build up when evaluator determines pockets are worn'},

    # Grinding — added by evaluator or technical instruction
    {'process': 'GRINDING', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_grinding', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Grinding when evaluator or technical team requests it'},

    # Threading — if thread repair needed
    {'process': 'THREADING', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_thread_repair', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Threading when thread repair is needed'},

    # Stress relief — for larger bits or specific materials
    {'process': 'STRESS-REL', 'rule_type': 'INCLUDE_IF', 'field_path': 'bit.size', 'operator': 'GT', 'value': '12',
     'description': 'Thermal stress relief for bits larger than 12 inches'},

    # Dynamic cutter installation — if BOM has dynamic cutters
    {'process': 'DYNAMIC-INST', 'rule_type': 'INCLUDE_IF', 'field_path': 'bom.has_dynamic_cutters', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Special installation for dynamic cutters'},

    # USR — upper section replacement
    {'process': 'USR', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_usr', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Upper section replacement when needed'},

    # Hardfacing — if evaluator finds it needed
    {'process': 'HARDFACING', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_hardfacing', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Hardfacing when body protection needed'},

    # Gauge undercut — from technical instruction
    {'process': 'GAUGE-UNDERCUT', 'rule_type': 'INCLUDE_IF', 'field_path': 'tech.undercut_gauge', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Gauge undercut per technical instruction'},

    # Insool wrap — for Matrix material on larger sizes
    {'process': 'INSOOL-WRAP', 'rule_type': 'INCLUDE_IF', 'field_path': 'design.body_material', 'operator': 'EQUALS', 'value': 'M',
     'description': 'Insool wrap for Matrix body material'},

    # Rework — added when QC finds issues
    {'process': 'REWORK', 'rule_type': 'INCLUDE_IF', 'field_path': 'eval.needs_rework', 'operator': 'EQUALS', 'value': 'True',
     'description': 'Rework when QC identifies issues'},
]


class Command(BaseCommand):
    help = 'Seed the Master Process Library with FC bit steps and inclusion rules'

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true', help='Actually create/update processes')

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write('Dry run. Pass --confirm to create/update processes.')
            for p in PROCESSES:
                self.stdout.write(f"  {p['code']:20s} {p['name']}")
            self.stdout.write(f'\n  {len(PROCESSES)} processes, {len(RULES)} rules')
            return

        created = 0
        updated = 0
        for data in PROCESSES:
            code = data.pop('code')
            name = data.pop('name')
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

        # Create rules
        rules_created = 0
        for rule_data in RULES:
            proc_code = rule_data.pop('process')
            try:
                proc = MasterProcess.objects.get(code=proc_code)
            except MasterProcess.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Process {proc_code} not found for rule'))
                continue

            _, was_created = ProcessInclusionRule.objects.get_or_create(
                master_process=proc,
                field_path=rule_data['field_path'],
                operator=rule_data['operator'],
                defaults={
                    'rule_type': rule_data['rule_type'],
                    'value': rule_data.get('value', ''),
                    'description': rule_data.get('description', ''),
                }
            )
            if was_created:
                rules_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Processes: {created} created, {updated} updated. Rules: {rules_created} created.'
        ))
