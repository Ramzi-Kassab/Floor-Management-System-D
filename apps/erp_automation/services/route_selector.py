"""
ERP Route Selection Engine

Selects the correct ERP production route based on bit size,
port configuration, and repair modifiers.
"""
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def select_route(size_inches, has_port, has_usr=False, has_hardfacing=False,
                 has_crush_shear=False, is_rerun=False, is_inspection_only=False,
                 bit_type='FC'):
    """Select the best matching ERPRoute for a repair job.

    Args:
        size_inches: Bit size in inches (Decimal or float)
        has_port: Whether bit has port (True/False)
        has_usr: Upper Section Replacement
        has_hardfacing: Hardfacing/Matrix Repair
        has_crush_shear: Crush & Shear special technology
        is_rerun: Re-run job
        is_inspection_only: Initial bit inspection only
        bit_type: 'FC' (Fixed Cutter) or 'RC' (Roller Cone)

    Returns:
        ERPRoute instance or None
    """
    from apps.erp_automation.models import ERPRoute

    size = Decimal(str(size_inches)) if size_inches else Decimal('0')

    # --- Special cases first ---

    # Inspection Only
    if is_inspection_only:
        if bit_type == 'RC':
            route = ERPRoute.objects.filter(route_number='ROUTE-0132').first()
        else:
            route = ERPRoute.objects.filter(route_number='ROUTE-0134').first()
        if route:
            logger.info(f"Selected inspection route: {route}")
        return route

    # Re-Run
    if is_rerun:
        size_class = 'JUMBO' if size >= 12 else 'AB'
        if size_class == 'JUMBO':
            route = ERPRoute.objects.filter(route_number='ROUTE-0125').first()
        else:
            route = ERPRoute.objects.filter(route_number='ROUTE-0124').first()
        if route:
            logger.info(f"Selected re-run route: {route}")
        return route

    # USR only, no repair (ROUTE-0126: FC-R AB No Port NO REPAIR ONLY USR)
    if has_usr and not has_hardfacing and not has_crush_shear and bit_type == 'FC':
        size_class = 'JUMBO' if size >= 12 else 'AB'
        if size_class == 'AB' and not has_port:
            # Check if this is truly "USR only" — the specific route for this
            route = ERPRoute.objects.filter(route_number='ROUTE-0126').first()
            if route:
                logger.info(f"Selected USR-only route: {route}")
                # Note: only use this if the intent is USR without repair.
                # For normal repair + USR, fall through to standard selection.
                # Since we can't distinguish here, fall through to standard.
                pass

    # --- Standard FC Repair route selection ---
    if bit_type == 'FC':
        size_class = 'JUMBO' if size >= 12 else 'AB'
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
            logger.info(f"Selected FC repair route: {route}")
        else:
            logger.warning(
                f"No route found for FC repair: size_class={size_class}, "
                f"port={has_port}, usr={has_usr}, hf={has_hardfacing}, "
                f"cs={has_crush_shear}"
            )
        return route

    # --- RC routes would use different criteria ---
    # (sealed, cc, size thresholds at 17" and 34")
    if bit_type == 'RC':
        logger.warning("RC route selection not yet implemented")
        return None

    return None
