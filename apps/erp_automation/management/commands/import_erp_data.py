"""
Management command to import existing ERP automation data from JSON files.
Imports locators, workflows (with steps from dictionaries), and item counters
from the original standalone Flask/Playwright app.

Source files:
  locators.json       - 145 XPath-based UI locators for Dynamics 365
  dictionaries.json   - 107 action definitions with locator refs, values, keys, retries
  workflows/Create Item.json - 26-step workflow with conditional account branching
  item_counters.json  - Sequential item counters per account type
"""
import json
import re
from pathlib import Path
from django.core.management.base import BaseCommand
from apps.erp_automation.models import (
    Locator, LocatorStrategy, Workflow, WorkflowStep,
    ItemCounter, ActionType, LocatorStrategyType, WorkflowStatus
)


# Default source dir in the main project
DEFAULT_SOURCE_DIR = 'D:/PycharmProjects/floor_management_system-D2/apps/ERP_Item_creation_automation'

# Default ERP URL
DEFAULT_ERP_URL = 'https://prod.alrushaid.net/namespaces/AXSF/?cmp=ardt&mi=PurchReqPreparedByMe'


class Command(BaseCommand):
    help = 'Import ERP automation data from JSON files (locators, workflow, counters)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-dir',
            type=str,
            default=DEFAULT_SOURCE_DIR,
            help='Directory containing JSON source files'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Required flag to confirm the import'
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                'Dry run — pass --confirm to actually import.\n'
                'This will import locators, workflow steps, and item counters '
                'from the legacy ERP automation JSON files.'
            ))
            # Show what would be imported
            source_dir = Path(options['source_dir'])
            if source_dir.exists():
                for f in ['locators.json', 'dictionaries.json', 'item_counters.json']:
                    fp = source_dir / f
                    if fp.exists():
                        with open(fp) as fh:
                            data = json.load(fh)
                        self.stdout.write(f'  {f}: {len(data)} entries')
                wf_dir = source_dir / 'workflows'
                if wf_dir.exists():
                    for wf in wf_dir.glob('*.json'):
                        with open(wf) as fh:
                            data = json.load(fh)
                        self.stdout.write(f'  workflows/{wf.name}: {len(data.get("steps", []))} steps')
            return

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
            self.stdout.write(self.style.WARNING('  Cleared all workflows, locators, and counters'))

        # Step 1: Import locators
        locators_file = source_dir / 'locators.json'
        if locators_file.exists():
            self.import_locators(locators_file)
        else:
            self.stderr.write(f'  locators.json not found at {locators_file}')

        # Step 2: Load dictionaries (step definitions for workflow import)
        dict_file = source_dir / 'dictionaries.json'
        self.step_definitions = {}
        if dict_file.exists():
            self.load_dictionaries(dict_file)
        else:
            self.stderr.write(f'  dictionaries.json not found at {dict_file}')

        # Step 3: Import workflows
        workflows_dir = source_dir / 'workflows'
        if workflows_dir.exists():
            self.import_workflows(workflows_dir)
        else:
            self.stderr.write(f'  workflows/ directory not found at {workflows_dir}')

        # Step 4: Import item counters
        counters_file = source_dir / 'item_counters.json'
        if counters_file.exists():
            self.import_counters(counters_file)
        else:
            self.stdout.write(f'  item_counters.json not found (skipping)')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Import Summary ==='))
        self.stdout.write(f'  Locators:      {Locator.objects.count()}')
        self.stdout.write(f'  Strategies:    {LocatorStrategy.objects.count()}')
        self.stdout.write(f'  Workflows:     {Workflow.objects.count()}')
        self.stdout.write(f'  Steps:         {WorkflowStep.objects.count()}')
        self.stdout.write(f'  Counters:      {ItemCounter.objects.count()}')
        self.stdout.write(self.style.SUCCESS('Import completed successfully!'))

    # -------------------------------------------------------------------------
    # LOCATORS
    # -------------------------------------------------------------------------

    def import_locators(self, filepath):
        """Import locators from locators.json.

        Each entry: "name_Loc": {"type": "xpath", "value": "//xpath/..."}
        Creates a Locator + primary LocatorStrategy (xpath).
        """
        self.stdout.write(f'Importing locators from {filepath.name}...')

        with open(filepath, 'r') as f:
            locators_data = json.load(f)

        created = 0
        updated = 0
        for name, data in locators_data.items():
            display_name = name.replace('_Loc', '').replace('_', ' ')
            xpath_value = data.get('value', '')

            locator, was_created = Locator.objects.update_or_create(
                name=name,
                defaults={
                    'description': display_name,
                    'application': 'dynamics365',
                    'is_dynamic': 'contains(@id' in xpath_value,
                    'requires_scroll': False,
                    'requires_wait': True,
                }
            )

            # Ensure there's a primary XPath strategy
            strategy, strat_created = LocatorStrategy.objects.update_or_create(
                locator=locator,
                strategy_type=self._map_strategy_type(data.get('type', 'xpath')),
                value=xpath_value,
                defaults={
                    'priority': 1,
                    'is_active': True,
                }
            )

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(f'  Locators: {created} created, {updated} updated')

    # -------------------------------------------------------------------------
    # DICTIONARIES (step definitions)
    # -------------------------------------------------------------------------

    def load_dictionaries(self, filepath):
        """Load step definitions from dictionaries.json into memory.

        Each entry is an action definition with:
          name, locator, option (value/template), keys, retries, delays,
          dependent actions, clear options, etc.
        """
        self.stdout.write(f'Loading step definitions from {filepath.name}...')

        with open(filepath, 'r') as f:
            dict_data = json.load(f)

        for key, data in dict_data.items():
            if not isinstance(data, dict):
                continue

            option = str(data.get('option', '') or '').strip()
            # Remove wrapping quotes from template values like '"{{ITEM NO}}"'
            if option.startswith('"') and option.endswith('"'):
                option = option[1:-1]

            keys = [
                str(data.get('key1', '') or '').strip(),
                str(data.get('key2', '') or '').strip(),
                str(data.get('key3', '') or '').strip(),
            ]

            self.step_definitions[key] = {
                'name': data.get('name', key.replace('_dict', '').replace('_', ' ')),
                'locator_name': str(data.get('locator', '') or ''),
                'option': option,
                'has_template': '{{' in option,
                'delay': data.get('delay', 1),
                'wait_after': data.get('sleep1', 0.5),
                'max_retries': data.get('max_retries', 3),
                'clear_before': bool(data.get('clear_option', False)),
                'keys': keys,
                'counter': data.get('counter', 1),
                # Dependent action info
                'dependent_click': bool(data.get('dependent_click_check')),
                'dependent_send': bool(data.get('dependent_send_check')),
                'dependent_loc1': str(data.get('dependent_loc1', '') or ''),
                'dependent_loc2': str(data.get('dependent_loc2', '') or ''),
                'dependent_val': str(data.get('dependent_val', '') or ''),
                'dependent_multi': bool(data.get('dependent_multi_check')),
                'max_dependent_retries': data.get('max_dependent_retries', 3),
                # Raw dict for reference
                'raw': data,
            }

        self.stdout.write(f'  Loaded {len(self.step_definitions)} step definitions')

    # -------------------------------------------------------------------------
    # WORKFLOWS
    # -------------------------------------------------------------------------

    def import_workflows(self, workflows_dir):
        """Import workflows from workflows/*.json.

        Each workflow JSON has:
          workflow_name, steps (list of step_ref strings or conditional dicts),
          valid_sheets (list of account names).
        """
        self.stdout.write(f'Importing workflows from {workflows_dir}...')

        for workflow_file in workflows_dir.glob('*.json'):
            with open(workflow_file, 'r') as f:
                workflow_data = json.load(f)

            workflow_name = workflow_data.get('workflow_name', workflow_file.stem)
            valid_sheets = workflow_data.get('valid_sheets', [])

            workflow, created = Workflow.objects.update_or_create(
                name=workflow_name,
                defaults={
                    'description': f'ERP workflow: {workflow_name}',
                    'target_url': DEFAULT_ERP_URL,
                    'application': 'dynamics365',
                    'status': WorkflowStatus.ACTIVE,
                    'valid_sheets': valid_sheets,
                    'condition_field': 'FROM',
                }
            )

            if not created:
                # Clear existing steps for re-import
                workflow.steps.all().delete()

            self.stdout.write(f'  Workflow: {workflow_name} ({"created" if created else "updated"})')

            # Import steps
            steps = workflow_data.get('steps', [])
            order = 1

            for step_ref in steps:
                if isinstance(step_ref, dict):
                    # Conditional step (dict with locator_by_account)
                    order = self._import_conditional_step(workflow, step_ref, order)
                elif isinstance(step_ref, str) and step_ref.startswith('{'):
                    # JSON string that needs parsing
                    try:
                        conditional = json.loads(step_ref)
                        order = self._import_conditional_step(workflow, conditional, order)
                    except json.JSONDecodeError:
                        self.stderr.write(f'    Could not parse conditional step: {step_ref[:80]}')
                else:
                    # Normal step reference
                    order = self._import_step(workflow, step_ref, order)

            self.stdout.write(f'    Imported {order - 1} steps')

    def _import_conditional_step(self, workflow, conditional, order):
        """Import a conditional step with account-based branching.

        Creates one WorkflowStep per account variant, each with condition_value set.
        """
        if 'locator_by_account' in conditional:
            for account, step_ref in conditional['locator_by_account'].items():
                condition_val = account if account != 'default' else ''
                order = self._import_step(
                    workflow, step_ref, order,
                    condition_value=condition_val,
                    step_name_prefix=f'[{account}] ' if account != 'default' else '[default] '
                )
        return order

    def _import_step(self, workflow, step_ref, order, condition_value='', step_name_prefix=''):
        """Create a WorkflowStep from a step definition reference."""
        step_def = self.step_definitions.get(step_ref)

        if not step_def:
            # Step not in dictionaries — create a placeholder
            self.stdout.write(
                self.style.WARNING(f'    Step {order}: "{step_ref}" not in dictionaries (placeholder created)')
            )
            WorkflowStep.objects.create(
                workflow=workflow,
                order=order,
                name=f'{step_name_prefix}{step_ref.replace("_dict", "").replace("_", " ")}',
                action_type=ActionType.CLICK,
                continue_on_error=True,
                condition_value=condition_value,
            )
            return order + 1

        # Find the locator
        locator = None
        locator_name = step_def.get('locator_name', '')
        if locator_name:
            locator = Locator.objects.filter(name=locator_name).first()

        # Determine action type and value fields
        option = step_def.get('option', '')
        keys = step_def.get('keys', ['', '', ''])
        has_template = step_def.get('has_template', False)

        if option and has_template:
            action_type = ActionType.FILL
            value_template = option
            value_static = ''
            value_field = self._extract_first_field(option)
        elif option:
            action_type = ActionType.FILL
            value_template = ''
            value_static = option
            value_field = ''
        elif any(k for k in keys if k):
            action_type = ActionType.PRESS_KEY
            value_template = ''
            value_static = ''
            value_field = ''
        else:
            action_type = ActionType.CLICK
            value_template = ''
            value_static = ''
            value_field = ''

        # Press key after action (key1)
        press_key = keys[0] if keys[0] else ''
        # Map key names
        key_map = {'ENTER': 'Enter', 'TAB': 'Tab', 'ESCAPE': 'Escape'}
        press_key = key_map.get(press_key.upper(), press_key) if press_key else ''

        # Convert wait_after from seconds to milliseconds
        wait_after_ms = int(float(step_def.get('wait_after', 0.5)) * 1000)

        WorkflowStep.objects.create(
            workflow=workflow,
            order=order,
            name=f'{step_name_prefix}{step_def.get("name", step_ref)}',
            action_type=action_type,
            locator=locator,
            value_static=value_static,
            value_template=value_template,
            value_field=value_field,
            press_key_after=press_key if action_type != ActionType.PRESS_KEY else '',
            wait_after=wait_after_ms,
            max_retries=step_def.get('max_retries', 3),
            condition_value=condition_value,
            clear_before_fill=step_def.get('clear_before', False),
            continue_on_error=False,
        )
        return order + 1

    def _extract_first_field(self, template):
        """Extract first field name from template like '{{ORDER NO.}} {{SERIAL NO}}'."""
        match = re.search(r'\{\{([^}]+)\}\}', template)
        return match.group(1).strip() if match else ''

    # -------------------------------------------------------------------------
    # COUNTERS
    # -------------------------------------------------------------------------

    def import_counters(self, filepath):
        """Import item counters from item_counters.json."""
        self.stdout.write(f'Importing item counters from {filepath.name}...')

        with open(filepath, 'r') as f:
            counters_data = json.load(f)

        for account_type, current_number in counters_data.items():
            # Derive prefix from account type
            prefix = f'RPR-'
            counter, created = ItemCounter.objects.update_or_create(
                account_type=account_type,
                defaults={
                    'prefix': prefix,
                    'current_number': current_number,
                    'padding': 4,
                }
            )
            action = 'created' if created else 'updated'
            self.stdout.write(f'  Counter {account_type}: {current_number} ({action})')

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _map_strategy_type(self, source_type):
        """Map source locator type string to LocatorStrategyType enum."""
        mapping = {
            'xpath': LocatorStrategyType.XPATH,
            'css': LocatorStrategyType.CSS,
            'id': LocatorStrategyType.ID,
            'name': LocatorStrategyType.NAME,
        }
        return mapping.get(source_type.lower(), LocatorStrategyType.XPATH)
