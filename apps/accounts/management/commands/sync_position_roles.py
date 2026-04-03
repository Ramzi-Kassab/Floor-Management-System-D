"""
Bulk sync UserRole records from Position mappings.
Usage:
    python manage.py sync_position_roles           # sync all active users
    python manage.py sync_position_roles --dry-run  # show what would change
    python manage.py sync_position_roles --user=r.kassab  # sync one user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Sync UserRole records from Position → Role mappings for all active users'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show changes without saving')
        parser.add_argument('--user', type=str, help='Sync a single user by username')

    def handle(self, *args, **options):
        from apps.accounts.signals import sync_user_roles_from_position
        from apps.accounts.models import UserRole
        from apps.hr.models import Employee

        dry_run = options.get('dry_run', False)
        username = options.get('user')

        if username:
            employees = Employee.objects.filter(user__username=username, user__is_active=True).select_related('user', 'position')
        else:
            employees = Employee.objects.filter(user__is_active=True, position__isnull=False).select_related('user', 'position')

        if not employees.exists():
            self.stdout.write('No employees found to sync.')
            return

        processed = 0
        added = 0
        removed = 0

        for emp in employees:
            user = emp.user
            position = emp.position

            if dry_run:
                from apps.accounts.models import Role
                # Show what would happen
                current_derived = set(UserRole.objects.filter(
                    user=user, is_position_derived=True
                ).values_list('role__code', flat=True))

                target_roles = set(Role.objects.filter(
                    positions=position
                ).values_list('code', flat=True)) if position else set()

                to_add = target_roles - current_derived
                to_remove = current_derived - target_roles

                if to_add or to_remove:
                    self.stdout.write(f'  {user.username} (position: {position}):')
                    for code in to_add:
                        self.stdout.write(self.style.SUCCESS(f'    + {code}'))
                        added += 1
                    for code in to_remove:
                        self.stdout.write(self.style.WARNING(f'    - {code}'))
                        removed += 1
            else:
                before = UserRole.objects.filter(user=user, is_position_derived=True).count()
                sync_user_roles_from_position(user, new_position=position)
                after = UserRole.objects.filter(user=user, is_position_derived=True).count()
                diff = after - before
                if diff > 0:
                    added += diff
                elif diff < 0:
                    removed += abs(diff)
                if diff != 0:
                    self.stdout.write(f'  {user.username}: {diff:+d} roles')

            processed += 1

        prefix = 'DRY RUN — ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'\n{prefix}{processed} users processed, {added} roles added, {removed} roles removed'
        ))
