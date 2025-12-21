"""
Management command to import existing ERP automation data from JSON files.
Imports locators, workflows, and item counters from the original Flask app.
"""
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from apps.erp_automation.models import (
    Locator, LocatorStrategy, Workflow, WorkflowStep,
    ItemCounter, ActionType, LocatorStrategyType
)


class Command(BaseCommand):
    help = 'Import ERP automation data from JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-dir',
            type=str,
            default='apps/ERP_Item_creation_automation',
            help='Directory containing JSON source files'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import'
        )

    def handle(self, *args, **options):
        source_dir = Path(options['source_dir'])

        if not source_dir.exists():
            self.stderr.write(self.style.ERROR(f'Source directory not found: {source_dir}'))
            return

        if options['clear']:
            self.stdout.write('Clearing existing data...')
            WorkflowStep.objects.all().delete()
            Workflow.objects.all().delete()
            LocatorStrategy.objects.all().delete()
            Locator.objects.all().delete()
            ItemCounter.objects.all().delete()

        # Import locators
        locators_file = source_dir / 'locators.json'
        if locators_file.exists():
            self.import_locators(locators_file)

        # Import dictionaries (step definitions with locator references)
        dict_file = source_dir / 'dictionaries.json'
        if dict_file.exists():
            self.import_dictionaries(dict_file)

        # Import workflows
        workflows_dir = source_dir / 'workflows'
        if workflows_dir.exists():
            self.import_workflows(workflows_dir)

        # Import item counters
        counters_file = source_dir / 'item_counters.json'
        if counters_file.exists():
            self.import_counters(counters_file)

        self.stdout.write(self.style.SUCCESS('Import completed successfully!'))

    def import_locators(self, filepath):
        """Import locators from locators.json"""
        self.stdout.write(f'Importing locators from {filepath}...')

        with open(filepath, 'r') as f:
            locators_data = json.load(f)

        created_count = 0
        for name, data in locators_data.items():
            # Clean up name (remove _Loc suffix for display)
            display_name = name.replace('_Loc', '').replace('_', ' ')

            locator, created = Locator.objects.get_or_create(
                name=name,
                defaults={
                    'description': display_name,
                    'application': 'dynamics365',
                    'is_dynamic': 'contains(@id' in data.get('value', ''),
                    'requires_scroll': False,
                }
            )

            if created:
                created_count += 1
                # Add the primary strategy
                LocatorStrategy.objects.create(
                    locator=locator,
                    strategy_type=self._map_strategy_type(data.get('type', 'xpath')),
                    value=data.get('value', ''),
                    priority=1,
                )

        self.stdout.write(f'  Created {created_count} locators')

    def import_dictionaries(self, filepath):
        """Import step definitions from dictionaries.json"""
        self.stdout.write(f'Importing step definitions from {filepath}...')

        with open(filepath, 'r') as f:
            dict_data = json.load(f)

        # These are step templates that reference locators
        # Store them for workflow import
        self.step_definitions = {}

        for key, data in dict_data.items():
            if isinstance(data, dict) and 'error' not in data:
                self.step_definitions[key] = {
                    'name': data.get('name', key),
                    'locator_name': data.get('locator', ''),
                    'action_value': data.get('option', ''),
                    'delay': data.get('delay', 1),
                    'wait_after': data.get('sleep1', 0.5),
                    'max_retries': data.get('max_retries', 3),
                    'clear_before': data.get('clear_option', False),
                    'keys': [data.get('key1', ''), data.get('key2', ''), data.get('key3', '')],
                    'dependent_locator': data.get('dependent_loc1', ''),
                    'dependent_check_type': 'click' if data.get('dependent_click_check') else ('send' if data.get('dependent_send_check') else None),
                }

        self.stdout.write(f'  Loaded {len(self.step_definitions)} step definitions')

    def import_workflows(self, workflows_dir):
        """Import workflows from workflows/*.json"""
        self.stdout.write(f'Importing workflows from {workflows_dir}...')

        for workflow_file in workflows_dir.glob('*.json'):
            with open(workflow_file, 'r') as f:
                workflow_data = json.load(f)

            workflow_name = workflow_data.get('workflow_name', workflow_file.stem)

            workflow, created = Workflow.objects.get_or_create(
                name=workflow_name,
                defaults={
                    'description': f'Imported workflow: {workflow_name}',
                    'is_active': True,
                    'condition_field': 'ACCOUNT_TYPE',
                }
            )

            if created:
                self.stdout.write(f'  Created workflow: {workflow_name}')

                # Import steps
                steps = workflow_data.get('steps', [])
                order = 1

                for step_ref in steps:
                    # Handle conditional steps (JSON string with locator_by_account)
                    if isinstance(step_ref, str) and step_ref.startswith('{'):
                        try:
                            conditional = json.loads(step_ref)
                            if 'locator_by_account' in conditional:
                                for account_type, step_name in conditional['locator_by_account'].items():
                                    self._create_workflow_step(
                                        workflow, step_name, order,
                                        condition_value=account_type if account_type != 'default' else ''
                                    )
                        except json.JSONDecodeError:
                            pass
                    else:
                        self._create_workflow_step(workflow, step_ref, order)

                    order += 1

    def _create_workflow_step(self, workflow, step_ref, order, condition_value=''):
        """Create a workflow step from a step definition reference"""
        step_def = self.step_definitions.get(step_ref, {})

        if not step_def:
            return

        # Find the locator
        locator = None
        locator_name = step_def.get('locator_name', '')
        if locator_name:
            locator = Locator.objects.filter(name=locator_name).first()

        # Determine action type
        action_value = step_def.get('action_value', '')
        keys = step_def.get('keys', [])

        if action_value and '{{' in action_value:
            action_type = ActionType.FILL
        elif action_value:
            action_type = ActionType.FILL
        elif any(keys):
            action_type = ActionType.PRESS_KEY
        else:
            action_type = ActionType.CLICK

        # Convert wait_after from seconds to milliseconds
        wait_after_ms = int(step_def.get('wait_after', 0.5) * 1000)

        WorkflowStep.objects.create(
            workflow=workflow,
            order=order,
            name=step_def.get('name', step_ref),
            action_type=action_type,
            locator=locator,
            value_template=action_value,
            value_field=self._extract_field_name(action_value),
            wait_after=wait_after_ms,
            max_retries=step_def.get('max_retries', 3),
            condition_value=condition_value,
            clear_before_fill=step_def.get('clear_before', False),
        )

    def _extract_field_name(self, template):
        """Extract field name from template like {{FIELD_NAME}}"""
        import re
        match = re.search(r'\{\{([^}]+)\}\}', template)
        return match.group(1) if match else ''

    def import_counters(self, filepath):
        """Import item counters from item_counters.json"""
        self.stdout.write(f'Importing item counters from {filepath}...')

        with open(filepath, 'r') as f:
            counters_data = json.load(f)

        for account_type, current_number in counters_data.items():
            counter, created = ItemCounter.objects.get_or_create(
                account_type=account_type,
                defaults={
                    'prefix': f'RPR-{account_type[:2]}-',
                    'current_number': current_number,
                    'padding': 4,
                }
            )
            if created:
                self.stdout.write(f'  Created counter: {account_type} = {current_number}')

    def _map_strategy_type(self, source_type):
        """Map source locator type to our strategy type"""
        mapping = {
            'xpath': LocatorStrategyType.XPATH,
            'css': LocatorStrategyType.CSS,
            'id': LocatorStrategyType.ID,
            'name': LocatorStrategyType.NAME,
        }
        return mapping.get(source_type.lower(), LocatorStrategyType.XPATH)
