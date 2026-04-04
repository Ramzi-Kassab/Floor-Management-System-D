"""
Auto-discover and sync TriggerPoint records from the Django URL resolver.
Finds all action endpoints (POST/create/delete/save/etc.) and creates
TriggerPoint records for each. Safe to run repeatedly — updates existing,
adds new, marks removed as inactive.

Usage:
    python manage.py sync_trigger_points          # full sync
    python manage.py sync_trigger_points --dry-run # show what would change
"""
from django.core.management.base import BaseCommand
from django.urls import get_resolver


# Action keywords that indicate a trigger point
ACTION_KEYWORDS = [
    'create', 'delete', 'save', 'status', 'scan', 'toggle', 'approve',
    'release', 'transfer', 'post', 'complete', 'upload', 'assign',
    'report', 'skip', 'pause', 'resume', 'claim', 'execute', 'start',
    'stop', 'convert', 'confirm', 'mark', 'reorder', 'unskip', 'seed',
    'dispatch', 'close', 'dismiss', 'grant', 'revoke',
]

# App → Category mapping
APP_CATEGORY = {
    'work-orders': 'WORKORDER',
    'workorders': 'WORKORDER',
    'inventory': 'INVENTORY',
    'quality': 'QUALITY',
    'dispatch': 'DISPATCH',
    'sales': 'SALES',
    'technology': 'TECHNOLOGY',
    'cutter-map': 'TECHNOLOGY',
    'compliance': 'COMPLIANCE',
    'hr': 'HR',
    'hsse': 'HR',
    'organization': 'HR',
    'accounts': 'SYSTEM',
    'notifications': 'SYSTEM',
    'erp-automation': 'ERP',
    'maintenance': 'MAINTENANCE',
    'documents': 'SYSTEM',
    'procedures': 'COMPLIANCE',
    'forms': 'SYSTEM',
    'planning': 'PLANNING',
    'reports': 'SYSTEM',
    'supply-chain': 'INVENTORY',
}

# Known workflow event mappings
EVENT_MAP = {
    'api_router_step_scan': 'WO_STARTED',
    'api_step_skip': 'STEP_COMPLETED',
    'api_step_pause': 'STEP_ON_HOLD',
    'api_step_unskip': 'STEP_RESUMED',
    'api_approve_wo': 'WO_APPROVED',
    'api_mark_wo_released': 'WO_RELEASED',
    'api_delete_wo': 'WO_DELETED',
    'api_transfer_bit_location': 'TRANSFER_CONFIRMED',
    'api_confirm_release': 'TRANSFER_CONFIRMED',
    'api_add_to_plan': 'ADDED_TO_PLAN',
    'api_release_plan_entry': 'WO_RELEASED',
    'api_report_quality_issue': 'DIE_CHECK_DECISION',
}

# Icon mapping by keywords
def guess_icon(url, name, view):
    s = (url + name + view).lower()
    if 'delete' in s or 'trash' in s: return 'trash-2'
    if 'create' in s or 'add' in s or 'new' in s: return 'plus'
    if 'approve' in s: return 'shield-check'
    if 'release' in s or 'rocket' in s: return 'rocket'
    if 'transfer' in s: return 'arrow-right-left'
    if 'scan' in s or 'qr' in s: return 'qr-code'
    if 'start' in s or 'play' in s: return 'play'
    if 'stop' in s or 'pause' in s: return 'pause-circle'
    if 'resume' in s: return 'play'
    if 'complete' in s or 'done' in s: return 'check-circle'
    if 'skip' in s: return 'skip-forward'
    if 'upload' in s: return 'upload'
    if 'save' in s: return 'save'
    if 'toggle' in s: return 'toggle-right'
    if 'report' in s or 'issue' in s: return 'flag'
    if 'claim' in s: return 'hand'
    if 'execute' in s: return 'zap'
    if 'dispatch' in s: return 'truck'
    if 'confirm' in s: return 'check-circle'
    if 'status' in s: return 'activity'
    if 'assign' in s: return 'user-plus'
    if 'reorder' in s: return 'list-ordered'
    if 'convert' in s: return 'refresh-cw'
    if 'grant' in s: return 'key'
    if 'revoke' in s: return 'x-circle'
    return 'zap'


def humanize_name(url, name, view):
    """Generate human-readable name from URL name or view name."""
    # Prefer URL name
    s = name or view
    s = s.replace('_', ' ').replace('-', ' ')
    # Remove common prefixes
    for prefix in ['api ', 'Api ']:
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s.strip().title()


def collect_urls(resolver, prefix=''):
    results = []
    for pattern in resolver.url_patterns:
        full = prefix + str(pattern.pattern)
        if hasattr(pattern, 'url_patterns'):
            results.extend(collect_urls(pattern, full))
        else:
            url_name = getattr(pattern, 'name', '') or ''
            callback = getattr(pattern, 'callback', None)
            view_name = ''
            if callback:
                if hasattr(callback, 'view_class'):
                    view_name = callback.view_class.__name__
                elif hasattr(callback, '__name__'):
                    view_name = callback.__name__
            results.append((full, url_name, view_name))
    return results


class Command(BaseCommand):
    help = 'Auto-discover and sync TriggerPoint records from URL resolver'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        from apps.notifications.models import TriggerPoint

        dry_run = options.get('dry_run', False)
        urls = collect_urls(get_resolver())

        # Filter to action endpoints
        actions = []
        for url, name, view in urls:
            if url.startswith('admin/') or url.startswith('__debug__/'):
                continue
            combined = (name + url).lower()
            if any(k in combined for k in ACTION_KEYWORDS):
                app = url.split('/')[0] if '/' in url else 'root'
                actions.append((app, url, name, view))

        # Track what we found
        found_codes = set()
        created = 0
        updated = 0

        for app, url, name, view in actions:
            code = name or view or url[:80]
            if not code or code in found_codes:
                continue
            found_codes.add(code)

            category = APP_CATEGORY.get(app, 'SYSTEM')
            icon = guess_icon(url, name, view)
            human_name = humanize_name(url, name, view)
            event = EVENT_MAP.get(name, '')

            if dry_run:
                exists = TriggerPoint.objects.filter(code=code).exists()
                if not exists:
                    self.stdout.write(f'  NEW: [{category:12s}] {human_name:40s} {code}')
                    created += 1
                continue

            obj, was_created = TriggerPoint.objects.update_or_create(
                code=code,
                defaults={
                    'name': human_name,
                    'category': category,
                    'app_name': app,
                    'icon': icon,
                    'url_pattern': '/' + url,
                    'workflow_event': event,
                    'view_name': view,
                    'is_active': True,
                }
            )
            if was_created:
                created += 1
            else:
                updated += 1

        # Mark triggers not found in URL scan as inactive
        if not dry_run:
            deactivated = TriggerPoint.objects.filter(is_active=True).exclude(
                code__in=found_codes
            ).update(is_active=False)
        else:
            deactivated = 0

        # Update has_workflow_rules flag
        if not dry_run:
            from apps.notifications.models import WorkflowRule
            events_with_rules = set(
                WorkflowRule.objects.filter(is_active=True).values_list('trigger_event', flat=True)
            )
            TriggerPoint.objects.filter(workflow_event__in=events_with_rules).update(has_workflow_rules=True)
            TriggerPoint.objects.exclude(workflow_event__in=events_with_rules).update(has_workflow_rules=False)

        prefix = 'DRY RUN — ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'{prefix}Found {len(found_codes)} trigger points. '
            f'Created: {created}, Updated: {updated}, Deactivated: {deactivated}'
        ))
