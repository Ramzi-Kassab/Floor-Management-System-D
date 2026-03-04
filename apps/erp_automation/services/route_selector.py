"""
ERP Route Selection Engine

Selects the correct ERP production route based on bit size, port configuration,
repair modifiers, and account type. Implements the full binary encoding scheme
from the Routes Decision Matrix (121 approved routes from 228 total).

Routes are stored in the ERPRoute model and seeded via seed_erp_routes command.

Binary encoding for FC Repair routes (ROUTE-0091 to ROUTE-0122):
  - 2 size classes: AB (<12"), JUMBO (>=12")
  - 2 port options: With Port, No Port
  - 8 modifier combinations: {USR, Hardfacing, C&S} = 2^3 = 8
  - Total: 2 x 2 x 8 = 32 standard repair routes
  - Plus special: Re-Run (0124/0125), USR-Only (0126), Inspection (0134)

Account -> Item Group mapping:
  LSTK -> RPR-FC-LST
  RC-LSTK -> RPR-RC-LST
  ARAMCO -> RPR-FC-AR
  HALLIBURTON -> RPR-FC-HDB
  Hal_Regional -> RPR-FC-REG
  UR -> (movement journal only, no item)
  WFD -> (movement journal only, no item)
"""
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


# Account -> Item Group mapping (for ERP item creation)
ACCOUNT_TO_ITEM_GROUP = {
    'LSTK': {'FC': 'RPR-FC-LST', 'RC': 'RPR-RC-LST'},
    'RC-LSTK': {'FC': 'RPR-RC-LST', 'RC': 'RPR-RC-LST'},
    'ARAMCO': {'FC': 'RPR-FC-AR', 'RC': 'RPR-RC-AR'},
    'HALLIBURTON': {'FC': 'RPR-FC-HDB', 'RC': 'RPR-FC-HDB'},
    'HDBS': {'FC': 'RPR-FC-HDB', 'RC': 'RPR-FC-HDB'},
    'HAL_REGIONAL': {'FC': 'RPR-FC-REG', 'RC': 'RPR-RC-REG'},
    'Hal_Regional': {'FC': 'RPR-FC-REG', 'RC': 'RPR-RC-REG'},
    'ARDT': {'FC': 'RPR-ARDT', 'RC': 'RPR-ARDT'},
}

# Port rule: bits < 4" ALWAYS have port grinding; bits >= 4" NEVER do
PORT_THRESHOLD = Decimal('4')

# Size class threshold
SIZE_CLASS_THRESHOLD = Decimal('12')


def get_item_group(account, bit_type='FC'):
    """Get the ERP item group for an account and bit type.

    Args:
        account: Account name (e.g., 'LSTK', 'ARAMCO')
        bit_type: 'FC' or 'RC'

    Returns:
        Item group string (e.g., 'RPR-FC-LST') or empty string
    """
    acct_upper = str(account or '').strip().upper()

    # Try exact match first (case-insensitive)
    for key, groups in ACCOUNT_TO_ITEM_GROUP.items():
        if key.upper() == acct_upper:
            return groups.get(bit_type, groups.get('FC', ''))

    logger.warning(f"No item group mapping for account '{account}' (bit_type={bit_type})")
    return ''


def determine_port(size_inches):
    """Determine if a bit has port grinding based on size.

    Business rule: Bits < 4" always have port grinding.
    Bits >= 4" never do (port is a design feature, not a repair choice).

    Args:
        size_inches: Decimal size in inches

    Returns:
        True if bit has port, False otherwise
    """
    if size_inches is None:
        return False
    size = Decimal(str(size_inches))
    return size < PORT_THRESHOLD


def determine_size_class(size_inches):
    """Determine AB or JUMBO size class.

    AB = less than 12" (standard sizes)
    JUMBO = 12" and above

    Args:
        size_inches: Decimal size in inches

    Returns:
        'AB' or 'JUMBO'
    """
    if size_inches is None:
        return 'AB'
    size = Decimal(str(size_inches))
    return 'JUMBO' if size >= SIZE_CLASS_THRESHOLD else 'AB'


def select_route(size_inches, has_port=None, has_usr=False, has_hardfacing=False,
                 has_crush_shear=False, is_rerun=False, is_inspection_only=False,
                 is_scrap=False, bit_type='FC', account=None):
    """Select the best matching ERPRoute for a repair job.

    Implements the full binary encoding decision matrix:
    1. Special cases: Inspection Only, Re-Run
    2. Standard FC Repair: size_class x port x {USR, HF, C&S}
    3. Fallback: try relaxed matches if exact match fails

    Args:
        size_inches: Bit size in inches (Decimal or float)
        has_port: Whether bit has port (True/False/None for auto-detect)
        has_usr: Upper Section Replacement
        has_hardfacing: Hardfacing/Matrix Repair
        has_crush_shear: Crush & Shear special technology
        is_rerun: Re-run job
        is_inspection_only: Initial bit inspection only
        bit_type: 'FC' (Fixed Cutter) or 'RC' (Roller Cone)
        account: Account name (for logging/context)

    Returns:
        ERPRoute instance or None
    """
    from apps.erp_automation.models import ERPRoute

    size = Decimal(str(size_inches)) if size_inches else Decimal('0')

    # Auto-detect port from size if not explicitly provided
    if has_port is None:
        has_port = determine_port(size)

    size_class = determine_size_class(size)

    logger.info(
        f"Route selection: bit_type={bit_type}, size={size}\", "
        f"size_class={size_class}, port={has_port}, "
        f"usr={has_usr}, hf={has_hardfacing}, cs={has_crush_shear}, "
        f"rerun={is_rerun}, scrap={is_scrap}, inspection={is_inspection_only}, "
        f"account={account}"
    )

    # ===================================================================
    # SPECIAL CASES (handled first, before standard selection)
    # ===================================================================

    # Scrap — no route needed
    if is_scrap:
        logger.info("Scrap job — no route assigned")
        return None

    # Inspection Only
    if is_inspection_only:
        if bit_type == 'RC':
            route = ERPRoute.objects.filter(route_number='ROUTE-0132', is_active=True).first()
        else:
            route = ERPRoute.objects.filter(route_number='ROUTE-0134', is_active=True).first()
        if route:
            logger.info(f"Selected inspection route: {route}")
        else:
            logger.warning("No inspection route found in database")
        return route

    # Re-Run
    if is_rerun:
        acct_upper = str(account or '').strip().upper()
        if acct_upper == 'RC-LSTK':
            # RC-LSTK rerun exception
            route_number = 'ROUTE-0134'
        elif size_class == 'JUMBO':
            route_number = 'ROUTE-0125'
        else:
            route_number = 'ROUTE-0124'
        route = ERPRoute.objects.filter(route_number=route_number, is_active=True).first()
        if route:
            logger.info(f"Selected re-run route: {route} (account={account})")
        else:
            logger.warning(f"No re-run route found: {route_number} for size_class={size_class}, account={account}")
        return route

    # ===================================================================
    # STANDARD FC REPAIR ROUTE SELECTION
    # ===================================================================
    if bit_type == 'FC':
        # Try exact match first (the binary encoding)
        route = ERPRoute.objects.filter(
            level='REPAIR',
            bit_type='FC',
            size_class=size_class,
            has_port=has_port,
            has_usr=has_usr,
            has_hardfacing=has_hardfacing,
            has_crush_shear=has_crush_shear,
            approved=True,
            is_active=True,
        ).first()

        if route:
            logger.info(f"Selected FC repair route (exact match): {route}")
            return route

        # --- Fallback 1: Try without C&S (least common modifier) ---
        if has_crush_shear:
            route = ERPRoute.objects.filter(
                level='REPAIR',
                bit_type='FC',
                size_class=size_class,
                has_port=has_port,
                has_usr=has_usr,
                has_hardfacing=has_hardfacing,
                has_crush_shear=False,
                approved=True,
                is_active=True,
            ).first()
            if route:
                logger.warning(
                    f"No exact route for C&S combo, falling back to: {route} "
                    f"(dropping C&S flag)"
                )
                return route

        # --- Fallback 2: Standard route (no modifiers) ---
        route = ERPRoute.objects.filter(
            level='REPAIR',
            bit_type='FC',
            size_class=size_class,
            has_port=has_port,
            has_usr=False,
            has_hardfacing=False,
            has_crush_shear=False,
            approved=True,
            is_active=True,
        ).first()
        if route:
            logger.warning(
                f"No matching modifier route, falling back to standard: {route}"
            )
            return route

        logger.error(
            f"No FC repair route found! size_class={size_class}, "
            f"port={has_port}, usr={has_usr}, hf={has_hardfacing}, "
            f"cs={has_crush_shear}"
        )
        return None

    # ===================================================================
    # RC ROUTE SELECTION (placeholder for future implementation)
    # ===================================================================
    if bit_type == 'RC':
        # RC routes use different criteria: sealed, CC, size sub-categories
        # (Up to 17", Above 17", 34" for Jumbo)
        logger.warning(
            f"RC route selection not yet fully implemented. "
            f"size={size}, sealed=?, cc=?"
        )
        # Try basic match on what we have
        route = ERPRoute.objects.filter(
            bit_type='RC',
            approved=True,
            is_active=True,
        ).first()
        if route:
            logger.info(f"Selected RC route (basic): {route}")
        return route

    return None


def select_route_for_job_data(job_data):
    """Select route for an ERPJobData record and update it.

    Convenience function that extracts all needed fields from the job_data
    model and calls select_route().

    Args:
        job_data: ERPJobData instance

    Returns:
        ERPRoute instance or None. Also updates job_data.route if found.
    """
    route = select_route(
        size_inches=job_data.size_inches,
        has_port=job_data.has_port if job_data.has_port else None,
        has_usr=job_data.has_usr,
        has_hardfacing=job_data.has_hardfacing,
        has_crush_shear=job_data.has_crush_shear,
        is_rerun=job_data.is_rerun,
        is_inspection_only=job_data.is_inspection_only,
        is_scrap=job_data.is_scrap,
        bit_type='FC',  # TODO: detect from smi_type or account
        account=job_data.account,
    )

    if route and not job_data.route_override:
        job_data.route = route
        job_data.save(update_fields=['route', 'updated_at'])
        logger.info(f"Auto-assigned route {route} to job data {job_data}")

    return route


def build_route_name(size_class, has_port, has_usr, has_hardfacing, has_crush_shear):
    """Build the human-readable route name for an FC Repair route.

    Useful for debugging and display.

    Args:
        size_class: 'AB' or 'JUMBO'
        has_port: bool
        has_usr, has_hardfacing, has_crush_shear: modifier booleans

    Returns:
        String like "FC-R AB With Port Standard" or "FC-R JUMBO No Port USR Hardfacing"
    """
    port = "With Port" if has_port else "No Port"

    processes = []
    if has_usr:
        processes.append("USR")
    if has_hardfacing:
        processes.append("Hardfacing/Matrix Repair")
    if has_crush_shear:
        processes.append("C&S")

    suffix = " ".join(processes) if processes else "Standard"

    return f"FC-R {size_class} {port} {suffix}"
