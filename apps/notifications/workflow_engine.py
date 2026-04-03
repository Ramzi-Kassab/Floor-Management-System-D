"""
Workflow Engine — core dispatch function.
Uses accounts.Role and accounts.UserRole for routing (single assignment system).
"""

import logging
from django.conf import settings
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    WorkflowEvent, ActionType,
    WorkflowRule, WorkflowAction,
    Notification,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def dispatch_event(event: str, actor, context: dict, dry_run: bool = False) -> list:
    """
    Core engine function. Fires when a workflow transition occurs.
    Reads WorkflowRule records from DB, creates WorkflowAction and/or Notification.
    """
    if not getattr(settings, 'WORKFLOW_ENGINE_ACTIVE', False):
        return []

    if actor and 'actor_name' not in context:
        context['actor_name'] = actor.get_full_name() or actor.username

    rules = WorkflowRule.objects.filter(
        trigger_event=event, is_active=True,
    ).select_related(
        'assign_to_role', 'escalate_to_role',
        'notif_recipients_role', 'assign_to_user', 'escalate_to_user',
    ).order_by('order')

    if not rules.exists():
        return []

    created = []
    action_map = {}
    account = context.get('account')

    for rule in rules:
        if rule.trigger_filter and not _matches_filter(rule.trigger_filter, context):
            continue

        action_users = _resolve_action_users(rule, actor, account)
        notif_users = _resolve_notif_users(rule, actor, account)

        title = _render_template(rule.notif_title_template, context) or rule.name
        message = _render_template(rule.notif_message_template, context) or ''
        action_desc = _render_template(rule.action_description_template, context) or title
        action_url = _render_template(rule.action_url_pattern, context) or ''

        if dry_run:
            created.append({
                'rule': rule.name, 'type': rule.rule_type,
                'action_type': rule.action_type,
                'role': rule.assign_to_role.code if rule.assign_to_role else '',
                'action_users': [u.username for u in action_users],
                'notif_users': [u.username for u in notif_users],
                'title': title, 'action_url': action_url,
            })
            continue

        dep_ids = []
        is_blocked = False
        if rule.depends_on_rule_ids:
            for dep_rule_pk in rule.depends_on_rule_ids:
                dep_action_pk = action_map.get(dep_rule_pk)
                if dep_action_pk:
                    dep_ids.append(dep_action_pk)
                    is_blocked = True

        if rule.rule_type in ('ACTION', 'BOTH'):
            due = timezone.now() + timezone.timedelta(hours=rule.deadline_hours) if rule.deadline_hours else None
            escalate_to_user = rule.escalate_to_user
            if not escalate_to_user and rule.escalate_to_role:
                escalate_to_user = _get_first_user_for_role(rule.escalate_to_role)

            if action_users:
                for user in action_users:
                    wa = WorkflowAction.objects.create(
                        title=title, description=action_desc,
                        action_type=rule.action_type, action_url=action_url,
                        trigger_event=event,
                        assigned_to=user, assigned_role=rule.assign_to_role,
                        assigned_by=actor, is_queue_action=rule.is_queue_action,
                        status=WorkflowAction.Status.PENDING,
                        priority=rule.notif_priority,
                        entity_type=context.get('entity_type', ''),
                        entity_id=context.get('entity_id'),
                        source_rule=rule,
                        depends_on_ids=dep_ids, is_blocked=is_blocked,
                        due_date=due,
                        escalate_after_hours=rule.escalate_after_hours,
                        escalate_to=escalate_to_user,
                    )
                    created.append(wa.pk)
                    action_map[rule.pk] = wa.pk
            elif rule.is_queue_action and rule.assign_to_role:
                wa = WorkflowAction.objects.create(
                    title=title, description=action_desc,
                    action_type=rule.action_type, action_url=action_url,
                    trigger_event=event,
                    assigned_to=None, assigned_role=rule.assign_to_role,
                    assigned_by=actor, is_queue_action=True,
                    status=WorkflowAction.Status.PENDING,
                    priority=rule.notif_priority,
                    entity_type=context.get('entity_type', ''),
                    entity_id=context.get('entity_id'),
                    source_rule=rule,
                    depends_on_ids=dep_ids, is_blocked=is_blocked,
                    due_date=due,
                    escalate_after_hours=rule.escalate_after_hours,
                    escalate_to=escalate_to_user,
                )
                created.append(wa.pk)
                action_map[rule.pk] = wa.pk

        if rule.rule_type in ('NOTIFICATION', 'BOTH'):
            notifs = []
            for user in notif_users:
                notifs.append(Notification(
                    recipient=user, actor=actor,
                    title=title[:200], message=message,
                    priority=rule.notif_priority,
                    entity_type=context.get('entity_type', ''),
                    entity_id=context.get('entity_id'),
                    action_url=action_url, action_type=rule.action_type,
                ))
            if notifs:
                Notification.objects.bulk_create(notifs)
                created.extend([n.pk for n in notifs if n.pk])

    return created


def check_and_escalate_overdue_actions():
    """Check for overdue actions and escalate. Called during bell poll."""
    now = timezone.now()
    overdue = WorkflowAction.objects.filter(
        status__in=[WorkflowAction.Status.PENDING, WorkflowAction.Status.CLAIMED],
        due_date__lt=now, escalate_after_hours__isnull=False, escalated_at__isnull=True,
    ).select_related('escalate_to', 'assigned_to')

    for action in overdue[:10]:
        hours_overdue = (now - action.due_date).total_seconds() / 3600
        if hours_overdue < (action.escalate_after_hours or 0):
            continue
        action.status = WorkflowAction.Status.ESCALATED
        action.escalated_at = now
        action.save(update_fields=['status', 'escalated_at', 'updated_at'])
        if action.escalate_to:
            Notification.objects.create(
                recipient=action.escalate_to, actor=action.assigned_to,
                title=f"ESCALATED: {action.title}",
                message=f"Action overdue by {int(hours_overdue)}h.\n{action.description}",
                priority='URGENT',
                entity_type=action.entity_type, entity_id=action.entity_id,
                action_url=action.action_url, action_type=action.action_type,
            )


def complete_action(action_pk, completed_by, result_data=None):
    """Mark a workflow action as completed and unblock dependents."""
    try:
        action = WorkflowAction.objects.get(pk=action_pk)
    except WorkflowAction.DoesNotExist:
        return False
    action.status = WorkflowAction.Status.COMPLETED
    action.completed_at = timezone.now()
    action.completed_by = completed_by
    if result_data:
        action.result_data = result_data
    action.save()
    for dep in WorkflowAction.objects.filter(
        depends_on_ids__contains=[action_pk], is_blocked=True, status='PENDING',
    ):
        all_done = all(
            WorkflowAction.objects.filter(pk=dpk, status='COMPLETED').exists()
            for dpk in dep.depends_on_ids if dpk != action_pk
        )
        if all_done:
            dep.is_blocked = False
            dep.save(update_fields=['is_blocked', 'updated_at'])
    return True


def get_pending_actions_for_user(user):
    """Get pending actions for a user (direct + role queue via accounts.UserRole)."""
    from apps.accounts.models import UserRole

    user_role_ids = list(
        UserRole.objects.filter(
            user=user, is_available=True,
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).values_list('role_id', flat=True)
    )

    return WorkflowAction.objects.filter(
        Q(assigned_to=user) |
        Q(assigned_role_id__in=user_role_ids, is_queue_action=True,
          assigned_to__isnull=True, claimed_by__isnull=True)
    ).filter(
        status__in=[WorkflowAction.Status.PENDING, WorkflowAction.Status.CLAIMED],
        is_blocked=False,
    ).select_related('assigned_to', 'claimed_by', 'assigned_role', 'source_rule'
    ).order_by('due_date', '-priority')


# ─── Helpers ──────────────────────────────────────────────────────────────

def get_available_users_for_role(role, account=None, exclude=None):
    """
    Get available users for an accounts.Role.
    Uses Count annotation to detect empty account_scope.
    """
    from apps.accounts.models import UserRole

    qs = UserRole.objects.filter(
        role=role, is_available=True,
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    ).annotate(
        scope_count=Count('account_scope')
    ).select_related('user')

    if account is not None:
        qs = qs.filter(Q(scope_count=0) | Q(account_scope=account)).distinct()

    users = [ur.user for ur in qs if ur.user.is_active]
    if exclude:
        users = [u for u in users if u != exclude]
    return users


def _matches_filter(filter_dict, context):
    for key, value in filter_dict.items():
        ctx_val = context.get(key)
        if isinstance(value, list):
            if ctx_val not in value:
                return False
        elif ctx_val != value:
            return False
    return True


def _render_template(template_str, context):
    if not template_str:
        return ''
    try:
        return template_str.format_map(_SafeDict(context))
    except Exception:
        return template_str


class _SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


def _resolve_action_users(rule, actor, account=None):
    if rule.assign_to_user:
        return [rule.assign_to_user]
    if rule.assign_to_role:
        return get_available_users_for_role(rule.assign_to_role, account=account, exclude=actor)
    return []


def _resolve_notif_users(rule, actor, account=None):
    if rule.notif_recipients_role:
        return get_available_users_for_role(rule.notif_recipients_role, account=account, exclude=actor)
    return []


def _get_first_user_for_role(role):
    from apps.accounts.models import UserRole
    ur = UserRole.objects.filter(
        role=role, is_available=True,
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    ).select_related('user').first()
    return ur.user if ur else None
