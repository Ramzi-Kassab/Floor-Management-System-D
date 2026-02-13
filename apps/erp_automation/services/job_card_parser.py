"""
Job Card Excel Parser

Parses individual Job Card Excel files (one per work order) and extracts
all data needed for ERP item creation, including cutter BOM with variant
breakdown and ERP item number lookup.
"""
import os
import re
import logging
from decimal import Decimal, InvalidOperation

import openpyxl

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

ACCOUNT_TO_ITEM_GROUP = {
    'LSTK': 'RPR-FC-LST',
    'ARAMCO': 'RPR-FC-AR',
    'HALLIBURTON': 'RPR-FC-HDB',
    'HDBS': 'RPR-FC-HDB',
    'HAL_REGIONAL': 'RPR-FC-REG',
    'REGIONAL': 'RPR-FC-REG',
    'ARDT': 'RPR-ARDT',
    'RC-LSTK': 'RPR-RC-LST',
    'RC-ARAMCO': 'RPR-RC-AR',
    'RC-REGIONAL': 'RPR-RC-REG',
    # These don't get items:
    # UR, WFD, SUB → movement journal only
    # L3, L4 → handled by other team
}

# Column M remark patterns → variant case codes
# Longest match first to avoid partial matches (e.g., "ARDT RCLM" before "RCLM")
REMARK_TO_VARIANT = {
    'ARDT RCLM': 'USED-RCL',     # ARDT Reclaim → RCLM-ARDT-*
    'ARDT RCL': 'USED-RCL',
    'ENO GRD': 'NEW-EO',         # ENO Ground — treat as ENO (not yet in ERP)
    'GROUND': 'NEW-EO',          # Ground — treat as ENO
    'GRD': 'NEW-EO',             # Ground — treat as ENO
    'ENO': 'NEW-EO',             # ENO As New → ENO-CT-*
    'RCLM': 'NEW-CLI',           # Plain RCLM = LSTK Reclaim → RCLM-*
    'RTRO': 'NEW-RET',           # Retrofit → RTRO-*
    'RTR': 'NEW-RET',
    'RETROFIT': 'NEW-RET',
    'NEW': 'NEW-PUR',            # Explicit new
}


# =============================================================================
# DERIVATION FUNCTIONS
# =============================================================================

def parse_size_to_inches(raw_size):
    """Convert size string to Decimal inches.

    Handles:
      - Numeric: 6.125 → 6.125
      - Fraction string: '3 3/4"' → 3.75
      - Whole string: '12"' → 12
      - Combined: '12 1/4"' → 12.25
      - Slash only: '3/4"' → 0.75
    """
    if raw_size is None:
        return None

    if isinstance(raw_size, (int, float)):
        return Decimal(str(raw_size))

    s = str(raw_size).strip().strip('"').strip("'").strip('"').strip()
    if not s:
        return None

    try:
        return Decimal(s)
    except InvalidOperation:
        pass

    # Try "whole fraction" pattern: "3 3/4", "12 1/4"
    m = re.match(r'^(\d+)\s+(\d+)/(\d+)$', s)
    if m:
        whole = int(m.group(1))
        num = int(m.group(2))
        den = int(m.group(3))
        if den > 0:
            return Decimal(str(whole)) + Decimal(str(num)) / Decimal(str(den))

    # Try fraction only: "3/4"
    m = re.match(r'^(\d+)/(\d+)$', s)
    if m:
        num = int(m.group(1))
        den = int(m.group(2))
        if den > 0:
            return Decimal(str(num)) / Decimal(str(den))

    # Try whole number only: "12"
    m = re.match(r'^(\d+)$', s)
    if m:
        return Decimal(m.group(1))

    # Try "N x N" pattern (e.g., "8 1/2 x 3 1/4" — take first part)
    parts = re.split(r'\s*[xX×]\s*', s)
    if len(parts) > 1:
        return parse_size_to_inches(parts[0])

    logger.warning(f"Could not parse size: {repr(raw_size)}")
    return None


def derive_body_material(smi_type):
    """Determine body material from SMI Type.

    If type starts or ends with 's' (case-insensitive) → SB (Steel Body)
    Otherwise → MB (Matrix Body)
    """
    t = str(smi_type or '').strip()
    if t and (t[0].lower() == 's' or t[-1].lower() == 's'):
        return 'SB'
    return 'MB'


def derive_crush_shear(smi_type):
    """Detect Crush & Shear from SMI Type.

    True if type starts or ends with 'CS' (case-insensitive).
    """
    t = str(smi_type or '').strip().upper()
    if not t:
        return False
    return t.startswith('CS') or t.endswith('CS')


def derive_original_l5_mat(l5_mat_full):
    """Strip M and everything after it from L5 MAT.

    Examples:
      '1224750M'  → '1224750'
      '1224750M1' → '1224750'
      '1251085M2' → '1251085'
      '1224750'   → '1224750' (no M, unchanged)
    """
    return re.split(r'[Mm]', str(l5_mat_full or '').strip())[0]


# =============================================================================
# CUTTER VARIANT PARSING
# =============================================================================

def parse_cutter_variants(new_qty, reclaim_qty, additional_comment, part_no):
    """Parse columns K, L, M into a list of variant allocations.

    RULE: If column M has bracketed remarks like [1 ARDT RCLM][2 RCLM],
    it is the COMPLETE authoritative breakdown — columns K and L are IGNORED.
    Only if M is empty, fall back to K (New) and L (LSTK Reclaim).

    Returns list of dicts:
      [{'variant_case': 'NEW-PUR', 'qty': 1, 'part_no': '717748'}, ...]
    """
    variants = []
    comment = str(additional_comment or '').strip()

    # Parse bracketed remarks: [1 ARDT RCLM], [2 RCLM], [1 NEW], [2 ENO]
    remark_items = re.findall(r'\[(\d+)\s+([^\]]+)\]', comment)

    if remark_items:
        # --- Column M is authoritative: ignore K and L ---
        for qty_str, remark_type in remark_items:
            qty = int(qty_str)
            remark_upper = remark_type.strip().upper()
            # Match against known variant types (longest match first)
            matched = False
            for key in sorted(REMARK_TO_VARIANT.keys(), key=len, reverse=True):
                if key in remark_upper:
                    variants.append({
                        'variant_case': REMARK_TO_VARIANT[key],
                        'qty': qty,
                        'part_no': part_no,
                    })
                    matched = True
                    break
            if not matched:
                variants.append({
                    'variant_case': 'UNKNOWN',
                    'qty': qty,
                    'part_no': part_no,
                    'remark': remark_type.strip(),
                })
    else:
        # --- Legacy fallback: use K and L ---
        nq = int(new_qty) if new_qty and str(new_qty).strip() else 0
        if nq > 0:
            variants.append({
                'variant_case': 'NEW-PUR',
                'qty': nq,
                'part_no': part_no,
            })

        rq = int(reclaim_qty) if reclaim_qty and str(reclaim_qty).strip() else 0
        if rq > 0:
            variants.append({
                'variant_case': 'NEW-CLI',  # Column L = LSTK Reclaim → RCLM-*
                'qty': rq,
                'part_no': part_no,
            })

    return variants


def lookup_erp_item_number(part_no, variant_case_code):
    """Find the ERP item number for a cutter by HDBS MAT # and variant case.

    Queries InventoryItem by mat_number, then finds the matching ItemVariant.
    Returns the erp_item_no string, or None if not found.
    """
    try:
        from apps.inventory.models import ItemVariant
        variant = ItemVariant.objects.select_related(
            'base_item', 'variant_case'
        ).filter(
            base_item__mat_number=str(part_no),
            variant_case__code=variant_case_code,
            is_active=True,
        ).first()
        if variant:
            return variant.erp_item_no or None
        return None
    except Exception as e:
        logger.warning(f"Error looking up ERP item for {part_no}/{variant_case_code}: {e}")
        return None


# =============================================================================
# MAIN PARSER
# =============================================================================

def parse_job_card(file_path):
    """Parse a Job Card Excel file and return a dict for ERPJobData creation.

    Reads the 'Data' sheet for core fields, cutter BOM, modified cutters,
    job status flags, and USR. Also checks 'Evaluation' and 'Eval-LSTK'
    sheets for hardfacing/build-up detection.

    Args:
        file_path: Path to the Job Card .xlsx file

    Returns:
        dict with all fields needed to create an ERPJobData record
    """
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb['Data']

    # --- Core fields (B column) ---
    wo_number = ws['B1'].value
    serial = ws['B2'].value
    raw_size = ws['B3'].value
    smi_type = str(ws['B4'].value or '').strip()
    l5_mat_full = str(ws['B5'].value or '').strip()
    date_received = ws['B6'].value
    account = str(ws['B7'].value or '').strip()
    l3_l4_mat = ws['B8'].value
    evaluated_by = ws['B11'].value
    reviewed_by = ws['B14'].value
    contract_number = ws['B24'].value
    vendor_number = ws['B25'].value

    # --- USR detection (E31 = Pin Size for USR) ---
    usr_pin_size = ws['E31'].value

    # --- Job status flags (I2:L5) ---
    l2 = ws['L2'].value
    l3 = ws['L3'].value
    l4 = ws['L4'].value
    l5 = ws['L5'].value
    is_rerun = (l2 == 1 or l3 == 1)
    is_inspection_only = (l4 == 1)
    is_scrap = (l5 == 1)

    # --- Parse size ---
    size_inches = parse_size_to_inches(raw_size)

    # --- Parse cutter BOM (rows 12-28) with variant info ---
    cutter_bom = []
    for row in range(12, 29):
        group = ws.cell(row=row, column=4).value    # D = group #
        qty = ws.cell(row=row, column=5).value       # E = BOM qty
        size = ws.cell(row=row, column=6).value      # F = cutter size
        part_no = ws.cell(row=row, column=7).value   # G = part #
        desc = ws.cell(row=row, column=8).value      # H = description
        new_qty = ws.cell(row=row, column=11).value   # K = new qty
        rcl_qty = ws.cell(row=row, column=12).value   # L = reclaim qty
        comment = ws.cell(row=row, column=13).value   # M = additional comment

        # Skip empty rows (no part# or placeholder spaces)
        if not part_no or not str(part_no).strip():
            continue
        size_str = str(size or '').strip()
        if size_str == '' or size_str == ' ':
            continue

        pn = str(part_no).strip()
        variants = parse_cutter_variants(new_qty, rcl_qty, comment, pn)

        # Lookup ERP item numbers for each variant
        for v in variants:
            v['erp_item_no'] = lookup_erp_item_number(pn, v['variant_case'])

        cutter_bom.append({
            'group': int(group) if group else len(cutter_bom) + 1,
            'qty': int(qty) if qty else 0,
            'size': size_str,
            'part_no': pn,
            'description': str(desc or '').strip(),
            'new_qty': int(new_qty) if new_qty and str(new_qty).strip() else 0,
            'reclaim_qty': int(rcl_qty) if rcl_qty and str(rcl_qty).strip() else 0,
            'additional_comment': str(comment or '').strip(),
            'variants': variants,
        })

    # --- Parse modified cutters (rows 4-10) ---
    modified_cutters = []
    for row in range(4, 11):
        group = ws.cell(row=row, column=4).value    # D
        qty = ws.cell(row=row, column=5).value       # E
        part_no = ws.cell(row=row, column=6).value   # F
        replaces = ws.cell(row=row, column=7).value  # G
        if part_no and str(part_no).strip():
            modified_cutters.append({
                'group': int(group) if group else None,
                'qty': int(qty) if qty else None,
                'part_no': str(part_no).strip(),
                'replaces_group': int(replaces) if replaces else None,
            })

    # --- Detect hardfacing / build-up ---
    has_hardfacing = False

    # Method 1: Check Evaluation sheet D36 for "build" keyword
    if 'Evaluation' in wb.sheetnames:
        eval_ws = wb['Evaluation']
        remarks = str(eval_ws['D36'].value or '').lower()
        if 'build' in remarks:
            has_hardfacing = True

    # Method 2: Check Eval-LSTK sheet R34, U34, X34 for non-zero build-up counts
    if not has_hardfacing and 'Eval-LSTK' in wb.sheetnames:
        lstk_ws = wb['Eval-LSTK']
        for cell_ref in ['R34', 'U34', 'X34']:
            val = lstk_ws[cell_ref].value
            try:
                if val and int(val) > 0:
                    has_hardfacing = True
                    break
            except (ValueError, TypeError):
                pass

    wb.close()

    # --- Handle date_received ---
    from datetime import datetime, date
    if isinstance(date_received, datetime):
        date_received = date_received.date()
    elif not isinstance(date_received, date):
        date_received = None

    # --- Build result ---
    return {
        'work_order_number': str(wo_number or '').strip(),
        'serial_number': str(serial or '').strip(),
        'size_raw': str(raw_size or '').strip(),
        'size_inches': size_inches,
        'smi_type': smi_type,
        'l5_mat_full': l5_mat_full,
        'l5_mat_original': derive_original_l5_mat(l5_mat_full),
        'date_received': date_received,
        'account': account,
        'contract_number': str(contract_number or '').strip(),
        'vendor_number': str(vendor_number or '').strip(),
        'l3_l4_mat': str(l3_l4_mat or '').strip(),
        'evaluated_by': str(evaluated_by or '').strip(),
        'reviewed_by': str(reviewed_by or '').strip(),
        'body_material': derive_body_material(smi_type),
        'item_group': ACCOUNT_TO_ITEM_GROUP.get(account, ''),
        'size_class': 'JUMBO' if size_inches and size_inches >= 12 else 'AB',
        'has_port': bool(size_inches and size_inches < 4),
        'has_usr': bool(usr_pin_size and str(usr_pin_size).strip()),
        'has_hardfacing': has_hardfacing,
        'has_crush_shear': derive_crush_shear(smi_type),
        'is_rerun': is_rerun,
        'is_inspection_only': is_inspection_only,
        'is_scrap': is_scrap,
        'cutter_bom_data': cutter_bom,
        'modified_cutters_data': modified_cutters,
        'source_file': os.path.basename(file_path),
    }
