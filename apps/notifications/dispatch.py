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


def fire_event(event: str, actor, context: dict) -> list:
    """
    Safe wrapper around dispatch_event().
    Catches all exceptions to prevent workflow failures from breaking
    user-facing views — but ALWAYS logs the full traceback so failures
    are visible in the Django log.
    Never returns None — returns empty list on failure.
    """
    try:
        from .workflow_engine import dispatch_event
        return dispatch_event(event=event, actor=actor, context=context)
    except Exception as e:
        logger.error(
            "fire_event() failed for event=%s actor=%s context_keys=%s error=%s",
            event,
            getattr(actor, 'username', str(actor)),
            list(context.keys()),
            str(e),
            exc_info=True   # includes full traceback in log
        )
        return []
