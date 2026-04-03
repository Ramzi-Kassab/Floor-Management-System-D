"""
Convenience wrapper: fires both the old notify() and new dispatch_event() in one call.
During Phase 3 parallel testing, both systems run side by side.
After Phase 4, the notify() calls inside each view will be removed and only dispatch_event() remains.

Usage:
    from apps.notifications.dispatch import fire_event

    fire_event(
        event='WO_RELEASED',
        actor=request.user,
        context={
            'wo_id': wo.pk,
            'wo_number': wo.wo_number,
            'serial': bit.serial_number,
            'entity_type': 'WorkOrder',
            'entity_id': wo.pk,
        }
    )
"""
import logging

logger = logging.getLogger(__name__)


def fire_event(event: str, actor, context: dict):
    """
    Fire a workflow event through the new engine.
    Safe to call even if the engine is disabled — silently returns.
    The old notify() calls remain in the views until Phase 4.
    """
    try:
        from .workflow_engine import dispatch_event
        dispatch_event(event=event, actor=actor, context=context)
    except Exception as e:
        logger.warning(f'dispatch_event({event}) failed: {e}')
