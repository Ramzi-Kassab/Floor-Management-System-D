"""
Notification service — all notification creation goes through notify().
"""

import json
import logging

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import FormRevision, Notification

User = get_user_model()
logger = logging.getLogger(__name__)


def notify(
    actor,
    verb,
    target=None,
    recipients=None,
    priority="NORMAL",
    action_url="",
    title=None,
    message=None,
    entity_type="",
    entity_id=None,
):
    """
    Create notifications for one or more recipients.

    Args:
        actor: User who triggered the event
        verb: Short action description (e.g., "completed inspection for")
        target: String describing the target (e.g., "SN 12345678")
        recipients: "all" | QuerySet/list of Users | single User | None
                    "all" broadcasts to all active users except actor
        priority: LOW / NORMAL / HIGH / URGENT
        action_url: URL to navigate to when notification is clicked
        title: Override auto-generated title
        message: Override auto-generated message
        entity_type: Model name for linking (e.g., "WorkOrder")
        entity_id: PK of the linked entity
    """
    if actor is None:
        return []

    # Build title and message
    actor_name = actor.get_short_name() or actor.username
    if title is None:
        title = f"{actor_name} {verb}" + (f" {target}" if target else "")
    if message is None:
        message = title

    # Truncate title to fit model field
    title = title[:200]
    message = message[:2000]

    # Resolve recipients
    if recipients == "all":
        recipient_qs = User.objects.filter(is_active=True).exclude(pk=actor.pk)
    elif recipients is None:
        # Default: all active users except actor
        recipient_qs = User.objects.filter(is_active=True).exclude(pk=actor.pk)
    elif hasattr(recipients, "exclude"):
        # QuerySet
        recipient_qs = recipients.exclude(pk=actor.pk)
    elif isinstance(recipients, (list, tuple)):
        pks = [u.pk if hasattr(u, "pk") else u for u in recipients]
        recipient_qs = User.objects.filter(pk__in=pks).exclude(pk=actor.pk)
    elif hasattr(recipients, "pk"):
        # Single user
        if recipients.pk == actor.pk:
            return []
        recipient_qs = User.objects.filter(pk=recipients.pk)
    else:
        return []

    notifications = [
        Notification(
            recipient=user,
            actor=actor,
            title=title,
            message=message,
            priority=priority,
            action_url=action_url,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        for user in recipient_qs
    ]

    if notifications:
        created = Notification.objects.bulk_create(notifications)
        logger.info("notify: %d notifications created — %s", len(created), title[:80])
        return created

    return []


def get_unread_count(user):
    """Return count of unread notifications for a user."""
    if not user or not user.is_authenticated:
        return 0
    return Notification.objects.filter(recipient=user, is_read=False).count()


def get_recent_unread(user, limit=5):
    """Return the N most recent unread notifications, respecting user mute preferences."""
    if not user or not user.is_authenticated:
        return Notification.objects.none()
    qs = Notification.objects.filter(recipient=user, is_read=False).select_related("actor")

    # Apply muted preferences from UserPreference
    try:
        prefs = user.preferences.dashboard_widgets or {}
        muted_actions = prefs.get('muted_action_types', [])
        muted_entities = prefs.get('muted_entity_types', [])
        if muted_actions:
            qs = qs.exclude(action_type__in=muted_actions)
        if muted_entities:
            qs = qs.exclude(entity_type__in=muted_entities)
    except Exception:
        pass  # No preferences record — show all

    return qs.order_by("-created_at")[:limit]


def get_unread_count_filtered(user):
    """Unread count respecting mute preferences."""
    if not user or not user.is_authenticated:
        return 0
    qs = Notification.objects.filter(recipient=user, is_read=False)
    try:
        prefs = user.preferences.dashboard_widgets or {}
        muted_actions = prefs.get('muted_action_types', [])
        muted_entities = prefs.get('muted_entity_types', [])
        if muted_actions:
            qs = qs.exclude(action_type__in=muted_actions)
        if muted_entities:
            qs = qs.exclude(entity_type__in=muted_entities)
    except Exception:
        pass
    return qs.count()


def create_form_revision(entity_type, entity_id, document_code, snapshot_new,
                         snapshot_old=None, revised_by=None, change_summary=""):
    """
    Create a FormRevision record tracking a quality form change.

    Args:
        entity_type: e.g. "ReceivingInspection"
        entity_id: PK of the entity
        document_code: e.g. "QAS/005-1"
        snapshot_new: dict of current form state
        snapshot_old: dict of previous form state (None for first revision)
        revised_by: User who made the change
        change_summary: human-readable summary

    Returns:
        FormRevision instance
    """
    # Compute next revision number
    last = (
        FormRevision.objects.filter(entity_type=entity_type, entity_id=entity_id)
        .order_by("-revision_number")
        .values_list("revision_number", flat=True)
        .first()
    )
    next_rev = (last or 0) + 1

    # Compute diff
    changes = {}
    if snapshot_old and snapshot_new:
        all_keys = set(list(snapshot_old.keys()) + list(snapshot_new.keys()))
        for key in all_keys:
            old_val = snapshot_old.get(key)
            new_val = snapshot_new.get(key)
            if old_val != new_val:
                changes[key] = {"old": _safe_json(old_val), "new": _safe_json(new_val)}

    if not change_summary and changes:
        changed_fields = list(changes.keys())[:5]
        change_summary = "Changed: " + ", ".join(changed_fields)
        if len(changes) > 5:
            change_summary += f" (+{len(changes) - 5} more)"

    return FormRevision.objects.create(
        entity_type=entity_type,
        entity_id=entity_id,
        revision_number=next_rev,
        document_code=document_code,
        snapshot=snapshot_new or {},
        changes=changes,
        change_summary=change_summary[:500],
        revised_by=revised_by,
    )


def _safe_json(val):
    """Make a value JSON-serializable."""
    if val is None:
        return None
    if isinstance(val, (str, int, float, bool)):
        return val
    try:
        json.dumps(val)
        return val
    except (TypeError, ValueError):
        return str(val)
