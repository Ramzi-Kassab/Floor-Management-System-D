"""
Position → Role sync signal.

When an Employee's position changes, auto-sync their UserRole records:
- Create UserRole (is_position_derived=True) for the new position's linked role
- Remove old is_position_derived=True UserRole from the previous position
- NEVER touch is_position_derived=False records (manually granted extra roles)
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def sync_user_roles_from_position(user, old_position=None, new_position=None):
    """
    Sync UserRole records based on position change.
    Called by signal or manually.
    """
    from apps.accounts.models import Role, UserRole

    # Remove old position-derived roles
    if old_position:
        old_roles = Role.objects.filter(positions=old_position)
        removed = UserRole.objects.filter(
            user=user,
            role__in=old_roles,
            is_position_derived=True,
        ).delete()
        if removed[0]:
            logger.info(f'Removed {removed[0]} position-derived roles from {user} (old position: {old_position})')

    # Add new position-derived roles
    if new_position:
        new_roles = Role.objects.filter(positions=new_position)
        for role in new_roles:
            obj, created = UserRole.objects.get_or_create(
                user=user,
                role=role,
                defaults={
                    'is_position_derived': True,
                    'is_available': True,
                }
            )
            if created:
                logger.info(f'Auto-assigned role {role.code} to {user} from position {new_position}')
            elif not obj.is_position_derived:
                # Role already exists as manual — don't overwrite, just log
                logger.info(f'Role {role.code} already manually assigned to {user}, skipping position sync')


@receiver(post_save, sender='hr.Employee')
def on_employee_save(sender, instance, **kwargs):
    """When Employee is saved, check if position changed and sync roles."""
    if not instance.user_id:
        return

    # Django doesn't track field changes natively — check if position FK changed
    # by comparing with the DB version
    try:
        from apps.hr.models import Employee
        old = Employee.objects.filter(pk=instance.pk).values_list('position_id', flat=True).first()
        if old is None:
            # New record
            if instance.position:
                sync_user_roles_from_position(instance.user, old_position=None, new_position=instance.position)
        elif old != instance.position_id:
            # Position changed
            from apps.organization.models import Position
            old_pos = Position.objects.filter(pk=old).first() if old else None
            sync_user_roles_from_position(instance.user, old_position=old_pos, new_position=instance.position)
    except Exception as e:
        logger.error(f'Position sync failed for {instance}: {e}')
