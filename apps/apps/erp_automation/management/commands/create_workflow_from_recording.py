"""
Create a clean workflow from a Recording Session.

Reads raw recorded actions from DB, deduplicates (click+fill pairs
on same element → keep only the last fill), detects D365 UI patterns,
maps known values to job-data template variables (auto-detecting from
linked job data when possible), inserts navigation waits, and creates
proper Locator + LocatorStrategy records with D365-safe contains
XPath fallbacks.

Pipeline:
    1. Deduplicate (D365-aware: preserves dropdown openers)
    2. Skip login steps (handled by executor._handle_login)
    3. Annotate D365 patterns (checkbox, dialog OK, dropdown option)
    4. Create workflow steps with smart locators + auto value templates
    5. Validate (warn about potential issues)

Usage:
    python manage.py create_workflow_from_recording              # uses latest session with 50+ actions
    python manage.py create_workflow_from_recording --session=7  # specific session
"""
import re
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.erp_automation.models import (
    Workflow, WorkflowStep, Locator, LocatorStrategy,
    RecordingSession, RecordedAction,
)


# ── Value mapping: recorded values → template variables ──────────────
# Keys are element_name (the field identifier).
# Values are either:
#   - ("static", "value"): always the same
#   - ("template", "{{FIELD_NAME}}"): resolved from job data
# NOTE: Auto-detection from linked job_data is tried FIRST.
#       This map is the FALLBACK when no job_data is linked.
VALUE_MAP = {
    # Item Group → from job data
    "ItemGroupId": ("template", "{{ITEM_GROUP}}"),
    # Model Group → always "Repair Bit"
    "ModelGroupId": ("static", "Repair Bit"),
    # Storage Dimension → always "SWL"
    "StorageDimensionGroup_Name": ("static", "SWL"),
    # Tracking Dimension → always "Serial"
    "TrackingDimensionGroup_Name": ("static", "Serial"),
    # Product Dimension → always "CSCS"
    "ProductDimensionGroup_Name": ("static", "CSCS"),
    # Units — all "ea"
    "InventUnitId": ("static", "ea"),
    "PurchUnitId": ("static", "ea"),
    "SalesUnitId": ("static", "ea"),
    "BOMUnitId": ("static", "ea"),
    # Search Name → Serial number
    "Identification_SearchName": ("template", "{{SERIAL NO}}"),
    # Product Name → composite field (all 5 parts)
    "Identification_Name": ("template", "{{ORDER NO.}} {{SERIAL NO}} {{SIZE}} {{TYPE}} {{MAT NO.}}"),
    # Old Serial ID
    "InventTable_Inf_InventSerialId": ("template", "{{SERIAL NO}}"),
    # Configuration → always "SB"
    "Configuration": ("static", "SB"),
    # Size → from job data
    "Size": ("template", "{{SIZE}}"),
    # Color → L5 MAT number
    "Color": ("template", "{{L5_MAT_FULL}}"),
    # Style → Type (HDBS)
    "Style": ("template", "{{TYPE}}"),
}

# Mapping for D365 dimension fields that have EMPTY element_name
# and dynamic element_id like "EcoResSize_Name_9392_0_0_input".
# Key: substring to match in element_id → value mapping.
ELEMENT_ID_VALUE_MAP = {
    "EcoResConfiguration_Name": ("static", "SB"),
    "EcoResSize_Name": ("template", "{{SIZE}}"),
    "EcoResColor_Name": ("template", "{{L5_MAT_FULL}}"),
    "EcoResStyle_Name": ("template", "{{TYPE}}"),
}

# Steps to skip entirely (login is handled by executor._handle_login)
SKIP_ELEMENT_NAMES = {"UserName", "Password"}
SKIP_ELEMENT_IDS = {"userNameInput", "passwordInput", "svgHolder"}

# Wait-after overrides for specific elements (by stable ID or name)
WAIT_OVERRIDES = {
    "SystemDefinedNewButton": 3000,
    "OKButton": 5000,
    "OkButton": 5000,
    "EcoResProductMasterDimensionPerCompany": 3000,
    "NewConfiguration": 1500,
    "NewSize": 1500,
    "NewColor": 1500,
    "NewStyle": 1500,
    "SystemDefinedCloseButton": 2000,
    "EcoResProductVariantsAction": 3000,
    "EcoResProductVariantPerCompanyMgr": 3000,
    "SuggestAllButton": 3000,
    "CommandButtonOk": 3000,
}

# ── Generic aria-labels that should NEVER be used as primary locator ──
# These match dozens of elements on a typical D365 page.
GENERIC_ARIA_LABELS = {
    'Name', 'ea', 'Back', 'Close', 'OK', 'Ok', 'Cancel',
    'Yes', 'No', 'Search', 'Edit', 'Delete', 'Save',
    'New', 'Open', 'Add', 'Remove', 'Filter', 'Expand',
    'Collapse', 'More', 'Less', 'Next', 'Previous',
    'Toggle', 'Menu', 'Options', 'Settings', 'Help', 'Info',
    'More options', 'Show details', 'Hide details', 'Refresh',
    'Select', 'Clear', 'Submit', 'Apply', 'Reset',
}


class Command(BaseCommand):
    help = "Create workflow from a recording session"

    def add_arguments(self, parser):
        parser.add_argument('--session', type=int, help='Recording session ID')
        parser.add_argument('--name', type=str,
                            default='Create Released Product (Recorded v2)',
                            help='Workflow name')

    def handle(self, *args, **options):
        # Find session
        session_id = options.get('session')
        if session_id:
            try:
                session = RecordingSession.objects.get(pk=session_id)
            except RecordingSession.DoesNotExist:
                self.stderr.write(f"Session #{session_id} not found")
                return
        else:
            # Use latest session with 50+ actions
            for s in RecordingSession.objects.order_by('-started_at'):
                if s.actions.count() >= 50:
                    session = s
                    break
            else:
                self.stderr.write("No session with 50+ actions found")
                return

        raw_actions = list(session.actions.order_by('order'))
        self.stdout.write(f"Session #{session.pk}: {len(raw_actions)} raw actions")

        # Cache job data row for auto-template detection
        self._row_data = None
        if session.job_data:
            try:
                self._row_data = session.job_data.get_row_data()
                self.stdout.write(f"Linked job data: WO {session.job_data.work_order_number}")
            except Exception:
                pass

        # ── Step 1: Deduplicate (D365-aware) ───────────────
        clean = self._deduplicate(raw_actions)
        self.stdout.write(f"After dedup: {len(clean)} actions")

        # ── Step 2: Skip login steps ───────────────────────
        clean = self._skip_login(clean)
        self.stdout.write(f"After skip login: {len(clean)} actions")

        # ── Step 3: Annotate D365 patterns ─────────────────
        self._annotate_d365_patterns(clean)

        # ── Step 4: Create workflow ────────────────────────
        wf_name = options.get('name', 'Create Released Product (Recorded v2)')
        wf = self._create_workflow(wf_name, session, clean)

        # ── Step 5: Validate ──────────────────────────────
        warnings = self._validate_workflow(wf)

        self.stdout.write(self.style.SUCCESS(
            f"\nCreated WF#{wf.pk} \"{wf.name}\" with {wf.steps.count()} steps"
        ))
        if warnings:
            self.stdout.write(f"  ({len(warnings)} warnings — review above)")

        # Print summary
        self.stdout.write("-" * 120)
        for s in wf.steps.order_by('order'):
            loc_info = s.locator.name if s.locator else "NO LOCATOR"
            val = s.value_template or s.value_static or ""
            strat_count = s.locator.strategies.count() if s.locator else 0
            mode = getattr(s, 'interaction_mode', 'auto') or 'auto'
            mode_short = mode[:8] if mode != 'auto' else '·'
            self.stdout.write(
                f"  {s.order:4d}: {s.action_type:10s} | {mode_short:8s} | "
                f"{s.name:42s} | {val[:25]:25s} | {loc_info[:30]} ({strat_count} strats)"
            )

    # ─────────────────────────────────────────────────────────────────
    #  PHASE 1: DEDUPLICATION (D365-aware)
    # ─────────────────────────────────────────────────────────────────

    def _deduplicate(self, actions):
        """Remove duplicate actions with D365-aware pattern detection.

        Patterns to collapse:
        - click on field + fill on same field → keep only fill
          UNLESS the click is a dropdown opener (look-ahead detects option select)
        - fill + fill on same field → keep last fill (final value)
        - click on "Name" label div → skip (noise from D365 dropdown close)
        - standalone Tab/Enter keypress after fill → skip (handled by press_key_after)
        """
        result = []
        i = 0
        while i < len(actions):
            action = actions[i]

            # Skip "click on Name" div noise (D365 dropdown close clicks)
            if self._is_noise_click(action):
                i += 1
                continue

            # click + fill on SAME element → keep only fill
            # UNLESS the click is a dropdown opener
            if action.action_type == 'click' and i + 1 < len(actions):
                next_action = actions[i + 1]
                if (self._same_element(action, next_action)
                        and next_action.action_type == 'fill'):
                    # Check: is this a dropdown opener?
                    if not self._is_dropdown_open_click(actions, i):
                        i += 1  # skip the redundant focus-click
                        continue

            # fill + fill on same element → keep last fill
            if action.action_type == 'fill' and i + 1 < len(actions):
                next_action = actions[i + 1]
                if (self._same_element(action, next_action)
                        and next_action.action_type == 'fill'):
                    i += 1  # skip — next fill has the final value
                    continue

            # Standalone Tab after fill → skip (press_key_after handles it)
            if (action.action_type == 'press_key'
                    and (action.key_pressed or '').lower() in ('tab', 'enter')
                    and i > 0 and actions[i - 1].action_type == 'fill'):
                i += 1
                continue

            result.append(action)
            i += 1

        return result

    def _is_noise_click(self, action):
        """Check if this click is D365 noise (empty-looking click)."""
        if action.action_type != 'click':
            return False
        # Click on bare "Name" input with no ID — D365 dropdown close artifact
        if (action.element_tag == 'input'
                and action.element_name == 'Name'
                and not action.element_id):
            return True
        return False

    def _same_element(self, a, b):
        """Check if two actions target the same element."""
        if a.element_name and a.element_name == b.element_name:
            return True
        if a.element_id and a.element_id == b.element_id:
            return True
        return False

    def _is_dropdown_open_click(self, actions, click_idx):
        """Check if click at click_idx is a D365 dropdown opener.

        D365 custom dropdowns: user clicks the input field to open a dropdown
        list, then clicks an option (li/span with role=option/menuitem).
        We need to KEEP this click — it opens the dropdown.

        Look ahead up to 5 actions for a 'select' or 'click' on a DIFFERENT
        element that looks like a dropdown option.
        """
        click_action = actions[click_idx]
        if click_action.element_tag not in ('input', 'div', 'span', 'button'):
            return False

        for j in range(click_idx + 1, min(click_idx + 6, len(actions))):
            next_a = actions[j]

            # If it's a select action (recorder detected dropdown option), this is a dropdown flow
            if next_a.action_type == 'select':
                return True

            # If it's a click on a different element that looks like an option
            if (next_a.action_type == 'click'
                    and not self._same_element(click_action, next_a)):
                # Check for dropdown-option indicators
                role = getattr(next_a, 'element_role', '') or ''
                tag = next_a.element_tag or ''
                cls = next_a.element_class or ''

                if role.lower() in ('option', 'menuitem', 'treeitem', 'listitem'):
                    return True
                if tag in ('li',) and 'list' in cls.lower():
                    return True
                # D365 dropdown options are often inside fixedDataTable
                if 'fixedDataTable' in cls or 'dyn-selectableRow' in cls:
                    return True

            # If we hit a fill on a different field, stop looking
            if (next_a.action_type == 'fill'
                    and not self._same_element(click_action, next_a)):
                break

        return False

    # ─────────────────────────────────────────────────────────────────
    #  PHASE 2: SKIP LOGIN
    # ─────────────────────────────────────────────────────────────────

    def _skip_login(self, actions):
        """Remove login-related actions (handled by executor._handle_login)."""
        result = []
        for action in actions:
            name = action.element_name or ""
            eid = action.element_id or ""

            if name in SKIP_ELEMENT_NAMES:
                continue
            if eid in SKIP_ELEMENT_IDS:
                continue
            # Skip clicks on ADFS-related elements
            if 'adfs' in (action.page_url or '').lower() and action.action_type == 'click':
                continue

            result.append(action)

        return result

    # ─────────────────────────────────────────────────────────────────
    #  PHASE 3: D365 PATTERN ANNOTATION
    # ─────────────────────────────────────────────────────────────────

    def _annotate_d365_patterns(self, actions):
        """Annotate each action with D365 UI patterns for smarter conversion.

        Detects:
        - checkbox: aria-label in (No, Yes) with checkbox indicators
        - dialog_ok: OKButton/OkButton/CommandButtonOk elements
        - dropdown_option: element with role=option/menuitem

        Also extracts page_context from D365 URL ?mi= parameter.
        """
        for i, action in enumerate(actions):
            action._d365_pattern = None
            action._d365_page_context = self._extract_page_context(action.page_url)

            aria = action.element_aria_label or ''
            name = action.element_name or ''
            cls = action.element_class or ''
            role = getattr(action, 'element_role', '') or ''
            etype = getattr(action, 'element_type', '') or ''

            # Checkbox: aria-label "No"/"Yes" + checkbox indicators
            if (action.action_type == 'click'
                    and aria in ('No', 'Yes')
                    and ('checkbox' in cls.lower()
                         or 'dyn-checkbox' in cls.lower()
                         or role == 'checkbox'
                         or etype == 'checkbox')):
                action._d365_pattern = 'checkbox'

            # Dialog OK button
            if (action.action_type == 'click'
                    and any(ok in name for ok in ('OKButton', 'OkButton', 'CommandButtonOk'))):
                action._d365_pattern = 'dialog_ok'

            # Dropdown option
            if role.lower() in ('option', 'menuitem', 'treeitem', 'listitem'):
                action._d365_pattern = 'dropdown_option'

    def _extract_page_context(self, url):
        """Extract D365 page context from URL (e.g., 'EcoResProductCreate')."""
        if not url:
            return ''
        m = re.search(r'[?&]mi=(\w+)', url)
        return m.group(1) if m else ''

    # ─────────────────────────────────────────────────────────────────
    #  PHASE 4: CREATE WORKFLOW
    # ─────────────────────────────────────────────────────────────────

    def _create_workflow(self, name, session, clean_actions):
        """Create Django Workflow with steps, locators, and strategies.

        IMPORTANT: Only creates steps from the actual recording data.
        No fabricated/hardcoded steps are added — the recording captures
        everything the user did, including Favorites clicks, navigation, etc.
        """
        wf, created = Workflow.objects.get_or_create(
            name=name,
            defaults={
                "description": f"Auto-generated from Recording Session #{session.pk}. "
                               "Includes product creation, dimensions, variants, and release.",
                "target_url": "https://sandbox.alrushaid.net/namespaces/AXSF/"
                              "?cmp=ardt&mi=DefaultDashboard",
                "application": "dynamics365",
                "status": "active",
                "valid_sheets": ["LSTK", "RC-LSTK", "ARAMCO",
                                 "HALLIBURTON", "HAL_REGIONAL"],
                "condition_field": "FROM",
            }
        )

        if not created:
            old_count = wf.steps.count()
            # Also clean up orphaned locators from the old workflow
            old_locator_ids = list(
                wf.steps.filter(locator__isnull=False)
                .values_list('locator_id', flat=True)
            )
            wf.steps.all().delete()
            # Delete locators that are no longer used by any step
            for loc_id in old_locator_ids:
                loc = Locator.objects.filter(pk=loc_id).first()
                if loc and not loc.workflowstep_set.exists():
                    loc.strategies.all().delete()
                    loc.delete()
            self.stdout.write(f"Cleared {old_count} existing steps from WF#{wf.pk}")
        else:
            self.stdout.write(self.style.SUCCESS(f"Created new WF#{wf.pk}"))

        # Link session
        session.generated_workflow = wf
        session.save()

        # Add a "Wait for dashboard" step at the beginning
        WorkflowStep.objects.create(
            workflow=wf,
            order=10,
            name="Wait for dashboard to load",
            action_type="wait_time",
            value_static="10000",
            wait_after=0,
            timeout=15000,
            max_retries=1,
        )

        # Process recorded actions — use sequential numbering starting from 20
        # Each step increments by 1, preserving the exact recording order.
        step_order = 20
        for action in clean_actions:
            step_order = self._create_step_from_action(wf, action, step_order)
            step_order += 1

        return wf

    def _create_step_from_action(self, wf, action, order):
        """Create a WorkflowStep from a RecordedAction."""
        action_type = action.action_type
        element_name = action.element_name or ""
        element_id = action.element_id or ""
        key_field = element_name or element_id

        # D365 never uses native <select> elements — all dropdowns are custom
        # divs/lis with ARIA roles. Map 'select' to 'click' to avoid
        # Playwright's select_option() failing on non-<select> elements.
        if action_type == 'select':
            action_type = 'click'

        # Navigate events → wait_time step
        if action_type == 'navigate':
            WorkflowStep.objects.create(
                workflow=wf,
                order=order,
                name=f"Wait for page: {(action.page_title or 'loading')[:40]}",
                action_type="navigate",
                wait_after=5000,
                timeout=45000,
                max_retries=1,
            )
            return order

        # Determine value (priority: auto-detect → VALUE_MAP → ELEMENT_ID_VALUE_MAP → static)
        value_static = ""
        value_template = ""
        mapped = False

        # Priority 1: Auto-detect from linked job data
        if action_type == 'fill' and self._row_data:
            auto_result = self._auto_detect_value_template(action)
            if auto_result:
                vtype, vval = auto_result
                if vtype == "template":
                    value_template = vval
                else:
                    value_static = vval
                mapped = True

        # Priority 2: VALUE_MAP by element_name
        if action_type == 'fill' and not mapped and key_field in VALUE_MAP:
            vtype, vval = VALUE_MAP[key_field]
            if vtype == "template":
                value_template = vval
            else:
                value_static = vval
            mapped = True

        # Priority 3: ELEMENT_ID_VALUE_MAP for dimension fields (empty element_name)
        if action_type == 'fill' and not mapped and element_id:
            for id_pattern, (vtype, vval) in ELEMENT_ID_VALUE_MAP.items():
                if id_pattern in element_id:
                    if vtype == "template":
                        value_template = vval
                    else:
                        value_static = vval
                    mapped = True
                    break

        # Priority 4: Static recorded value
        if action_type == 'fill' and not mapped:
            value_static = action.input_value or ""
        elif action_type == 'select' and not mapped:
            value_static = action.input_value or ""

        # Create locator from recorded strategies (with D365 pattern awareness)
        locator = None
        if action_type not in ('navigate', 'press_key', 'wait_time'):
            locator = self._create_locator_from_action(action)

        # Generate step name
        step_name = self._generate_step_name(action)

        # Wait-after override
        stable_id = self._extract_stable_id(element_id)
        wait_after = WAIT_OVERRIDES.get(stable_id, WAIT_OVERRIDES.get(element_id, 500))
        if action_type == 'fill':
            wait_after = max(wait_after, 800)

        # Press key after fill
        press_key = ""
        if action_type == 'fill':
            press_key = "Tab"

        # Determine D365 interaction mode
        interaction_mode = self._determine_interaction_mode(action)

        WorkflowStep.objects.create(
            workflow=wf,
            order=order,
            name=step_name,
            action_type=action_type,
            locator=locator,
            value_static=value_static,
            value_template=value_template,
            wait_after=wait_after,
            timeout=45000,
            max_retries=3,
            press_key_after=press_key,
            clear_before_fill=action_type == 'fill',
            interaction_mode=interaction_mode,
        )
        return order

    # ─────────────────────────────────────────────────────────────────
    #  AUTO VALUE TEMPLATE DETECTION
    # ─────────────────────────────────────────────────────────────────

    def _auto_detect_value_template(self, action):
        """Compare fill value to linked job_data to auto-detect template variables.

        Returns (type, value) tuple: ("template", "{{FIELD}}") or ("static", "value") or None.

        Detection:
        1. Exact match: input_value == row_data[FIELD] → {{FIELD}}
        2. Composite match: input contains multiple field values → "{{F1}} {{F2}} {{F3}}"
        """
        if action.action_type != 'fill' or not action.input_value:
            return None

        if not self._row_data:
            return None

        input_val = str(action.input_value).strip()
        if not input_val or len(input_val) < 2:
            return None

        # 1. Exact match against any row_data field
        for field_name, field_value in self._row_data.items():
            fv = str(field_value).strip()
            if fv and fv == input_val:
                return ("template", "{{" + field_name + "}}")

        # 2. Composite match: input contains multiple field values
        #    Sort by value length descending to avoid partial matches
        #    (e.g., match "13791954R10" before "1379")
        remaining = input_val
        field_matches = []
        sorted_fields = sorted(
            self._row_data.items(),
            key=lambda x: -len(str(x[1]).strip())
        )
        for field_name, field_value in sorted_fields:
            fv = str(field_value).strip()
            if fv and len(fv) >= 3 and fv in remaining:
                remaining = remaining.replace(fv, "{{" + field_name + "}}", 1)
                field_matches.append(field_name)

        if len(field_matches) >= 2 and remaining != input_val:
            return ("template", remaining)

        return None

    # ─────────────────────────────────────────────────────────────────
    #  INTERACTION MODE DETECTION
    # ─────────────────────────────────────────────────────────────────

    def _determine_interaction_mode(self, action):
        """Map a recorded action to a D365 interaction mode.

        Uses element attributes captured during recording to classify
        the element type. The executor uses this mode to select the
        right interaction chain (e.g., double-click for lookup buttons,
        Alt+Down for comboboxes, etc.).

        Returns an InteractionMode string value.
        """
        role = getattr(action, 'element_role', '') or ''
        el_class = getattr(action, 'element_class', '') or ''
        el_type = getattr(action, 'element_type', '') or ''
        d365_pattern = getattr(action, '_d365_pattern', '') or ''
        tag = getattr(action, 'element_tag', '') or ''
        dyn_control = getattr(action, 'element_dyn_control_name', '') or ''

        # Lookup buttons need double-click
        if 'lookupButton' in el_class:
            return 'lookup_button'

        # Combobox needs Alt+ArrowDown
        if role == 'combobox':
            return 'combobox'

        # D365 checkbox pattern (from annotation)
        if d365_pattern == 'checkbox':
            return 'checkbox_toggle'
        if role == 'checkbox' or el_type == 'checkbox':
            return 'checkbox_toggle'
        if 'checkbox' in el_class.lower() or 'ToggleSwitch' in el_class:
            return 'checkbox_toggle'

        # Dialog OK/Cancel/Yes/No buttons
        if d365_pattern == 'dialog_ok':
            return 'dialog_button'
        if 'CommandButton' in el_class:
            return 'dialog_button'

        # Dropdown option (being selected, not the trigger)
        if d365_pattern == 'dropdown_option':
            return 'custom_dropdown'
        if role in ('option', 'menuitem', 'treeitem', 'listitem'):
            return 'custom_dropdown'

        # Tab headers
        if role == 'tab':
            return 'tab_header'

        # Navigation/toolbar buttons
        if tag == 'button' and 'SystemDefined' in el_class:
            return 'nav_button'

        # Segmented entry
        if 'segmented' in el_class.lower() or 'segment' in dyn_control.lower():
            return 'segmented_entry'

        # Auto-detect at runtime for everything else
        return 'auto'

    # ─────────────────────────────────────────────────────────────────
    #  LOCATOR CREATION
    # ─────────────────────────────────────────────────────────────────

    def _create_locator_from_action(self, action):
        """Create a Locator with strategies from a recorded action.

        D365 pattern-aware:
        - checkbox: skip generic aria-label, use @name or contains(@id)
        - dialog_ok: page-context in locator name for disambiguation
        - generic aria-labels (No, Yes, OK, etc): never primary strategy

        Strategy priority:
        1. Double-contains XPath (PRIMARY for D365 dynamic-prefix fields)
        2. Exact @id for static elements
        3. @name for form fields (promoted to P0 when aria-label is blacklisted)
        4. Single contains(@id) fallback
        5. Text content for buttons/links
        6. aria-label (only non-generic)
        """
        element_name = action.element_name or ""
        element_id = action.element_id or ""
        element_text = (action.element_text or "")[:50]
        element_aria = action.element_aria_label or ""
        tag = action.element_tag or ""
        d365_pattern = getattr(action, '_d365_pattern', None)
        page_context = getattr(action, '_d365_page_context', '') or ''

        # ── Try to reuse an existing proven locator ──────────────
        existing_loc = self._find_existing_locator(action)
        if existing_loc:
            return existing_loc

        # ── Build locator name ───────────────────────────────────
        stable_id = self._extract_stable_id(element_id)
        if element_name:
            key = element_name
        elif element_aria and element_aria not in GENERIC_ARIA_LABELS:
            key = element_aria.replace(' ', '_')
        elif self._has_d365_dynamic_id(element_id):
            prefix, suffix = self._split_d365_id_for_contains(element_id)
            key = f"{prefix.rstrip('_')}_{suffix}" if prefix and suffix else stable_id or f"action_{action.order}"
        elif stable_id and stable_id not in ('input', 'header', 'label', 'button'):
            key = stable_id
        elif element_text:
            key = element_text[:20].replace(' ', '_')
        else:
            key = f"action_{action.order}"

        # For dialog_ok pattern, qualify with page context for disambiguation
        if d365_pattern == 'dialog_ok' and page_context:
            key = f"{key}_{page_context}"

        loc_name = f"rec_v2_{key}"

        # Check if rec_v2_ locator already exists
        existing = Locator.objects.filter(name=loc_name).first()
        if existing:
            return existing

        # ── Build strategies ──────────────────────────────────────
        has_dynamic_prefix = self._has_d365_dynamic_id(element_id)
        is_checkbox = d365_pattern == 'checkbox'
        aria_is_generic = element_aria in GENERIC_ARIA_LABELS

        strategies = []
        priority = 1

        # For checkboxes with generic aria-label: promote @name to top
        if is_checkbox and element_name:
            strategies.append(("xpath", f'//*[@name="{element_name}"]', priority))
            priority += 1
        # When aria-label is blacklisted but @name exists: promote @name
        elif aria_is_generic and element_name and element_name not in ('Name',):
            strategies.append(("name", element_name, priority))
            priority += 1

        # ── Double-contains XPath (PRIMARY for D365 fields) ──────
        if has_dynamic_prefix and element_id:
            page_prefix, field_suffix = self._split_d365_id_for_contains(element_id)
            if page_prefix and field_suffix and len(field_suffix) > 3:
                xpath = f'//*[contains(@id, "{page_prefix}") and contains(@id, "{field_suffix}")]'
                strategies.append(("xpath", xpath, priority))
                priority += 1

        # ── Exact @id for static elements ────────────────────────
        if element_id and not has_dynamic_prefix:
            strategies.append(("xpath", f'//*[@id="{element_id}"]', priority))
            priority += 1

        # ── @name attribute (for form inputs) ────────────────────
        # Only if not already added above
        name_already_added = any(
            s[0] in ('name', 'xpath') and f'@name="{element_name}"' in s[1]
            for s in strategies
        ) if element_name else False
        if element_name and element_name not in ('Name',) and not name_already_added:
            strategies.append(("xpath", f'//*[@name="{element_name}"]', priority))
            priority += 1

        # ── Single contains(@id) fallback ────────────────────────
        stable_id_v = self._extract_stable_id(element_id)
        if stable_id_v and stable_id_v != element_id and len(stable_id_v) > 5:
            contains_xpath = f'//*[contains(@id, "{stable_id_v}")]'
            if stable_id_v not in ('input', 'header', 'label', 'button', 'Name_input'):
                existing_vals = {s[1] for s in strategies}
                if contains_xpath not in existing_vals:
                    strategies.append(("xpath", contains_xpath, priority))
                    priority += 1

        # ── Text content (for buttons, links, tabs, nav items) ───
        if element_text and tag in ("button", "a", "li", "span"):
            clean_text = element_text.split('\n')[0].strip()
            if clean_text and len(clean_text) < 40 and len(clean_text) > 1:
                strategies.append(("text", clean_text, priority))
                priority += 1

        # ── aria-label (only for NON-generic labels) ─────────────
        if element_aria and not aria_is_generic and not is_checkbox:
            strategies.append(("xpath", f'//*[@aria-label="{element_aria}"]', priority))
            priority += 1

        return self._get_or_create_locator(
            loc_name, strategies,
            f"Recording: {action.element_name or action.element_id or action.element_text[:30] if action.element_text else ''}",
            page_context=page_context,
        )

    def _get_or_create_locator(self, name, strategies, description="", page_context=""):
        """Create locator with strategies if it doesn't exist."""
        has_dynamic = any(
            'contains(@id' in s[1] for s in strategies if s[0] == 'xpath'
        )

        locator, created = Locator.objects.get_or_create(
            name=name,
            defaults={
                "application": "dynamics365",
                "description": description,
                "is_dynamic": has_dynamic,
                "page_context": page_context,
            }
        )
        if created:
            for stype, sval, spri in strategies:
                LocatorStrategy.objects.create(
                    locator=locator,
                    strategy_type=stype,
                    value=sval,
                    priority=spri,
                )
        return locator

    def _generate_step_name(self, action):
        """Generate a human-readable step name."""
        action_type = action.action_type
        ident = (action.element_name or action.element_aria_label or
                 action.element_id or (action.element_text or "")[:30] or "element")

        if action_type == "click":
            return f"Click {ident}"
        elif action_type == "fill":
            return f"Fill {ident}"
        elif action_type == "select":
            val = (action.input_value or "")[:30]
            return f"Select {val or ident}"
        elif action_type == "press_key":
            return f"Press {action.key_pressed or 'key'}"
        elif action_type == "navigate":
            return f"Navigate: {(action.page_title or '')[:40]}"
        return f"{action_type} {ident}"

    # ─────────────────────────────────────────────────────────────────
    #  LOCATOR REUSE (find existing proven locators)
    # ─────────────────────────────────────────────────────────────────

    def _find_existing_locator(self, action):
        """Try to find an existing proven locator for this element.

        Matches by element_name, stable ID parts, or double-contains patterns.
        Searches both proven locators (non-rec_v2_) AND locators with
        success_count > 0 from any workflow.
        """
        element_name = action.element_name or ""
        element_id = action.element_id or ""
        stable_id = self._extract_stable_id(element_id)

        # Base queryset: non-rec_v2_ locators (proven/manual)
        base_qs = LocatorStrategy.objects.filter(
            locator__application="dynamics365",
        ).exclude(
            locator__name__startswith="rec_v2_"
        ).select_related('locator')

        # Also search locators with proven success (any name)
        proven_qs = LocatorStrategy.objects.filter(
            locator__application="dynamics365",
            success_count__gt=0,
        ).select_related('locator')

        for qs in [base_qs, proven_qs]:
            # Strategy 1: Match by @name attribute
            if element_name:
                matches = qs.filter(
                    strategy_type="xpath",
                    value__contains=f'@name="{element_name}"',
                )
                if matches.exists():
                    return matches.first().locator

                matches = qs.filter(
                    strategy_type="name",
                    value=element_name,
                )
                if matches.exists():
                    return matches.first().locator

            # Strategy 2: Match by double-contains
            if element_id and self._has_d365_dynamic_id(element_id):
                prefix, suffix = self._split_d365_id_for_contains(element_id)

                if prefix and suffix and len(suffix) > 3:
                    matches = qs.filter(
                        strategy_type="xpath",
                        value__contains=f'contains(@id, "{prefix}")',
                    ).filter(
                        value__contains=f'contains(@id, "{suffix}")',
                    )
                    if matches.exists():
                        return matches.first().locator

                    # Try with leading underscore on suffix
                    matches = qs.filter(
                        strategy_type="xpath",
                        value__contains=f'contains(@id, "{prefix}")',
                    ).filter(
                        value__contains=f'contains(@id, "_{suffix}")',
                    )
                    if matches.exists():
                        return matches.first().locator

                # Try: prefix base + suffix substring
                prefix_base = prefix.rstrip('_') if prefix else ""
                if prefix_base and len(prefix_base) > 5 and suffix:
                    for match in qs.filter(
                        strategy_type="xpath",
                        value__contains=f'contains(@id, "{prefix_base}")',
                    ):
                        if suffix in match.value:
                            return match.locator

            # Strategy 3: Match by stable ID in contains xpath
            if stable_id and len(stable_id) > 5:
                matches = qs.filter(
                    strategy_type="xpath",
                    value__contains=f'contains(@id, "{stable_id}")',
                )
                if matches.exists():
                    return matches.first().locator

            # Strategy 4: Match by exact ID (only for static IDs)
            if element_id and not self._has_d365_dynamic_id(element_id):
                matches = qs.filter(
                    strategy_type="xpath",
                    value__contains=f'@id="{element_id}"',
                )
                if matches.exists():
                    return matches.first().locator

        return None

    # ─────────────────────────────────────────────────────────────────
    #  PHASE 5: POST-CONVERSION VALIDATION
    # ─────────────────────────────────────────────────────────────────

    def _validate_workflow(self, wf):
        """Run post-conversion validation. Prints warnings for review."""
        warnings = []
        steps = list(wf.steps.order_by('order'))

        # 1. Consecutive clicks on same locator (likely need different locators)
        for i in range(len(steps) - 1):
            s1, s2 = steps[i], steps[i + 1]
            if (s1.action_type == 'click' and s2.action_type == 'click'
                    and s1.locator_id and s1.locator_id == s2.locator_id):
                warnings.append(
                    f"Steps {s1.order} and {s2.order} both click the same "
                    f"locator '{s1.locator.name}' — may need different locators "
                    f"(e.g., two OK buttons for different dialogs)."
                )

        # 2. Generic aria-label as primary strategy
        for step in steps:
            if not step.locator:
                continue
            primary = (step.locator.strategies
                       .filter(is_active=True)
                       .order_by('priority').first())
            if primary and primary.strategy_type == 'xpath':
                for label in GENERIC_ARIA_LABELS:
                    if f'@aria-label="{label}"' in primary.value:
                        # Check it's the ONLY strategy — if there are better ones, ok
                        strat_count = step.locator.strategies.filter(is_active=True).count()
                        if strat_count <= 1:
                            warnings.append(
                                f"Step {step.order} '{step.name}' uses generic "
                                f"aria-label '{label}' as ONLY locator strategy."
                            )
                        break

        # 3. Fill steps without value mappings
        for step in steps:
            if (step.action_type == 'fill'
                    and not step.value_static
                    and not step.value_template
                    and not step.value_field):
                warnings.append(
                    f"Step {step.order} '{step.name}' is a fill step "
                    f"with no value mapping."
                )

        # 4. Click/fill/select steps with no locator
        for step in steps:
            if step.action_type in ('click', 'fill', 'select') and not step.locator:
                warnings.append(
                    f"Step {step.order} '{step.name}' has no locator."
                )

        # 5. Interaction mode summary
        mode_counts = {}
        for step in steps:
            mode = getattr(step, 'interaction_mode', 'auto') or 'auto'
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        if mode_counts:
            modes_str = ', '.join(f"{m}={c}" for m, c in sorted(mode_counts.items()))
            self.stdout.write(f"  Interaction modes: {modes_str}")

        for w in warnings:
            self.stdout.write(self.style.WARNING(f"  [!] {w}"))

        return warnings

    # ─────────────────────────────────────────────────────────────────
    #  D365 ID UTILITIES
    # ─────────────────────────────────────────────────────────────────

    def _has_d365_dynamic_id(self, element_id):
        """Check if an element ID has dynamic numeric segments (D365 pattern)."""
        if not element_id:
            return False
        return bool(re.search(r'_\d+_', element_id))

    def _split_d365_id_for_contains(self, element_id):
        """Split a D365 dynamic ID into stable text parts for double-contains XPath.

        D365 IDs have a dynamic "session number" that changes between sessions.
        Small numbers like 0, 0_0 are stable row/column indices and are kept in suffix.

        Examples:
          "EcoResProductCreate_3_ItemGroupId_input"
              → ("EcoResProductCreate_", "ItemGroupId_input")
          "EcoResConfiguration_Name_9392_0_0_input"
              → ("EcoResConfiguration_Name_", "0_0_input")
          "Sel_7008_0_0_input"
              → ("Sel_", "0_0_input")
        """
        if not element_id:
            return "", ""

        parts = element_id.split('_')

        # Find the FIRST "large" dynamic number (the session ID)
        dynamic_idx = None
        for i, part in enumerate(parts):
            if re.match(r'^\d+$', part):
                num_val = int(part)
                if num_val >= 2 or (dynamic_idx is None and num_val >= 0):
                    if dynamic_idx is None:
                        dynamic_idx = i
                        break

        if dynamic_idx is None:
            return "", element_id

        prefix_parts = parts[:dynamic_idx]
        prefix = '_'.join(prefix_parts) + '_' if prefix_parts else ""

        suffix_parts = parts[dynamic_idx + 1:]
        suffix = '_'.join(suffix_parts) if suffix_parts else ""

        return prefix, suffix

    def _extract_stable_id(self, element_id):
        """Extract stable suffix from D365 prefixed IDs.

        E.g., "ecoresproductdetailsextendedgrid_2_SystemDefinedNewButton"
           → "SystemDefinedNewButton"
        """
        if not element_id:
            return ""
        parts = element_id.split('_')
        if len(parts) >= 2:
            last = parts[-1]
            second_last = parts[-2]
            if re.match(r'^\d+$', second_last):
                return last
            return '_'.join(parts[-2:])
        return element_id
