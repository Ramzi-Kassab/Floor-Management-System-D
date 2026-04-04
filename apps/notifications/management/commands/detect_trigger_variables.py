"""
Scan source code for fire_event() calls and extract context variable names.
Updates TriggerPoint.context_variables for each trigger that has a workflow_event.

Usage: python manage.py detect_trigger_variables
"""
import re
import os
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Auto-detect context variables from fire_event() calls in source code'

    def handle(self, *args, **options):
        from apps.notifications.models import TriggerPoint

        # Scan all Python files in apps/ for fire_event() calls
        event_vars = {}  # event_code -> set of variable names
        apps_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), 'apps')

        for root, dirs, files in os.walk(apps_dir):
            dirs[:] = [d for d in dirs if d != '__pycache__' and d != 'migrations']
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                filepath = os.path.join(root, fname)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception:
                    continue

                # Find fire_event('EVENT_NAME', ..., { ... })
                # Pattern: fire_event('EVENT_NAME' followed by a dict within ~10 lines
                for match in re.finditer(
                    r"fire_event\(\s*['\"]([A-Z_]+)['\"].*?\{([^}]+)\}",
                    content, re.DOTALL
                ):
                    event = match.group(1)
                    dict_content = match.group(2)

                    # Extract key names from the dict
                    keys = re.findall(r"'([a-z_]+)'\s*:", dict_content)
                    if event not in event_vars:
                        event_vars[event] = set()
                    event_vars[event].update(keys)

        # Update TriggerPoint records
        updated = 0
        for event, vars_set in event_vars.items():
            var_list = sorted(vars_set)
            count = TriggerPoint.objects.filter(
                workflow_event=event
            ).update(context_variables=var_list)
            if count:
                updated += count
                self.stdout.write(f'  {event:25s} -> {var_list}')

        # Also set common variables for triggers without specific detection
        common_vars = ['wo_number', 'wo_id', 'serial', 'bit_id', 'actor_name', 'entity_type', 'entity_id']
        no_vars = TriggerPoint.objects.filter(
            workflow_event__isnull=False,
            context_variables=[],
        ).exclude(workflow_event='')
        if no_vars.exists():
            no_vars.update(context_variables=common_vars)
            self.stdout.write(f'  Set common variables on {no_vars.count()} triggers without specific detection')

        self.stdout.write(self.style.SUCCESS(f'\nUpdated {updated} triggers with detected variables'))
        self.stdout.write(f'Events scanned: {len(event_vars)}')
