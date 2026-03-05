"""
ERP Automation Models

Models for browser automation with smart recording and playback.
Stores workflows, locators, recordings, and field mappings.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import json


class LocatorStrategyType(models.TextChoices):
    """Locator strategy types in order of preference."""
    DATA_TESTID = "data-testid", "Data Test ID"
    ARIA_LABEL = "aria-label", "ARIA Label"
    NAME = "name", "Name Attribute"
    ID = "id", "ID Attribute"
    CSS = "css", "CSS Selector"
    XPATH = "xpath", "XPath"
    TEXT = "text", "Text Content"
    TEXT_NEARBY = "text-nearby", "Text Nearby Element"
    ROLE = "role", "ARIA Role"


class ActionType(models.TextChoices):
    """Types of actions that can be performed."""
    CLICK = "click", "Click"
    FILL = "fill", "Fill/Type"
    SELECT = "select", "Select Option"
    CHECK = "check", "Check/Uncheck"
    HOVER = "hover", "Hover"
    SCROLL = "scroll", "Scroll Into View"
    WAIT = "wait", "Wait for Element"
    WAIT_TIME = "wait_time", "Wait (Time)"
    PRESS_KEY = "press_key", "Press Key"
    SCREENSHOT = "screenshot", "Take Screenshot"
    ASSERT_TEXT = "assert_text", "Assert Text"
    ASSERT_VISIBLE = "assert_visible", "Assert Visible"
    CONDITIONAL = "conditional", "Conditional Branch"
    READ_VALUE = "read_value", "Read Value"
    GOTO_URL = "goto_url", "Navigate to URL"
    SELECT_GRID_ROW = "select_grid_row", "Select Grid Row"
    TYPE_TEXT = "type_text", "Type Text (keyboard)"
    NAVIGATE = "navigate", "Navigate (SPA)"
    CLICK_DYNAMIC = "click_dynamic_locator", "Click Dynamic Locator"
    RIGHT_CLICK = "right_click", "Right Click (Context Menu)"


class InteractionMode(models.TextChoices):
    """D365 element interaction modes — determines HOW the executor interacts with an element.

    Each mode has a specific chain of interaction strategies tried in order.
    'auto' detects the mode at runtime from element attributes.
    """
    AUTO = "auto", "Auto-detect"
    STANDARD_INPUT = "standard_input", "Standard Input"
    COMBOBOX = "combobox", "Combobox (Alt+Down)"
    LOOKUP_BUTTON = "lookup_button", "Lookup Button (double-click)"
    CUSTOM_DROPDOWN = "custom_dropdown", "Custom Dropdown"
    SEGMENTED_ENTRY = "segmented_entry", "Segmented Entry"
    CHECKBOX_TOGGLE = "checkbox_toggle", "Checkbox Toggle"
    DIALOG_BUTTON = "dialog_button", "Dialog Button"
    NAV_BUTTON = "nav_button", "Navigation Button"
    TAB_HEADER = "tab_header", "Tab Header"


class WorkflowStatus(models.TextChoices):
    """Workflow execution status."""
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


class ExecutionStatus(models.TextChoices):
    """Execution run status."""
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


# =============================================================================
# LOCATOR MODELS
# =============================================================================

class Locator(models.Model):
    """
    Represents a UI element locator with multiple fallback strategies.
    Smart locators try multiple strategies until one works.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier for this locator (e.g., 'product_number_field')"
    )
    description = models.TextField(
        blank=True,
        help_text="Human-readable description of what this element is"
    )

    # Target application/page context
    application = models.CharField(
        max_length=100,
        default="dynamics365",
        help_text="Target application (e.g., dynamics365, sap)"
    )
    page_context = models.CharField(
        max_length=200,
        blank=True,
        help_text="Page or form where this locator is valid"
    )

    # Screenshot for visual reference
    screenshot = models.ImageField(
        upload_to="erp_automation/locator_screenshots/",
        blank=True,
        null=True,
        help_text="Screenshot of the element for reference"
    )

    # Metadata
    is_dynamic = models.BooleanField(
        default=False,
        help_text="Element has dynamic IDs that change between sessions"
    )
    requires_scroll = models.BooleanField(
        default=False,
        help_text="Element may need scrolling to become visible"
    )
    requires_wait = models.BooleanField(
        default=True,
        help_text="Wait for element to be visible before interacting"
    )
    default_timeout = models.IntegerField(
        default=30000,
        validators=[MinValueValidator(1000)],
        help_text="Default timeout in milliseconds"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_locators"
    )

    class Meta:
        db_table = "erp_automation_locators"
        ordering = ["name"]
        verbose_name = "Locator"
        verbose_name_plural = "Locators"

    def __str__(self):
        return f"{self.name} ({self.application})"

    def get_strategies_ordered(self):
        """Return locator strategies ordered by priority."""
        return self.strategies.filter(is_active=True).order_by("priority")


class LocatorStrategy(models.Model):
    """
    Individual locator strategy with fallback support.
    Multiple strategies per locator for resilience.
    """
    locator = models.ForeignKey(
        Locator,
        on_delete=models.CASCADE,
        related_name="strategies"
    )
    strategy_type = models.CharField(
        max_length=20,
        choices=LocatorStrategyType.choices,
        help_text="Type of locator strategy"
    )
    value = models.TextField(
        help_text="The locator value (XPath, CSS, text, etc.)"
    )
    priority = models.IntegerField(
        default=10,
        help_text="Lower number = higher priority (tried first)"
    )

    # For text-nearby strategy
    offset_direction = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("above", "Above"),
            ("below", "Below"),
            ("left", "Left"),
            ("right", "Right"),
        ],
        help_text="Direction from label text to input (for text-nearby)"
    )

    # Success tracking
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "erp_automation_locator_strategies"
        ordering = ["locator", "priority"]
        unique_together = ["locator", "strategy_type", "value"]

    def __str__(self):
        return f"{self.locator.name} - {self.strategy_type}: {self.value[:50]}"

    @property
    def success_rate(self):
        total = self.success_count + self.failure_count
        if total == 0:
            return 0
        return (self.success_count / total) * 100


# =============================================================================
# WORKFLOW MODELS
# =============================================================================

class Workflow(models.Model):
    """
    A workflow is a sequence of steps to automate a process.
    Supports conditional branching based on data fields.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Workflow name (e.g., 'Create Released Product')"
    )
    description = models.TextField(
        blank=True,
        help_text="What this workflow does"
    )

    # Target URL and application
    target_url = models.URLField(
        blank=True,
        help_text="Default starting URL for this workflow"
    )
    application = models.CharField(
        max_length=100,
        default="dynamics365",
        help_text="Target application"
    )

    # Valid data sources
    valid_sheets = models.JSONField(
        default=list,
        blank=True,
        help_text="List of Excel sheet names this workflow can process"
    )
    required_fields = models.JSONField(
        default=list,
        blank=True,
        help_text="Required data fields for this workflow"
    )

    # Conditional execution
    condition_field = models.CharField(
        max_length=100,
        blank=True,
        help_text="Field name used for conditional branching (e.g., 'FROM' or 'account_type')"
    )

    status = models.CharField(
        max_length=20,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.DRAFT
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_workflows"
    )

    class Meta:
        db_table = "erp_automation_workflows"
        ordering = ["name"]

    def __str__(self):
        return self.name

    # ── Status transition validation ──────────────────────────────
    STATUS_TRANSITIONS = {
        'draft': ['active', 'archived'],
        'active': ['archived'],
        'archived': [],  # terminal
    }

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        if self.pk:
            try:
                original = Workflow.objects.only('status').get(pk=self.pk)
            except Workflow.DoesNotExist:
                return
            if original.status != self.status:
                allowed = self.STATUS_TRANSITIONS.get(original.status, [])
                if self.status not in allowed:
                    raise ValidationError({
                        'status': f"Cannot change status from '{original.get_status_display()}' to "
                                  f"'{self.get_status_display()}'. "
                                  f"Allowed transitions: {', '.join(allowed) or 'none (terminal state)'}."
                    })

    def get_steps_for_condition(self, condition_value=None):
        """Get workflow steps, filtered by condition if applicable.

        Uses case-insensitive matching for condition values to handle
        variations in account names (e.g., 'LSTK' vs 'lstk', 'Hal_Regional' vs 'HAL-REGIONAL').
        """
        steps = self.steps.filter(is_active=True).order_by("order")
        if condition_value:
            # Filter steps that match the condition or have no condition
            # Use iexact for case-insensitive matching
            steps = steps.filter(
                models.Q(condition_value="") |
                models.Q(condition_value__iexact=condition_value)
            )
        return steps


class WorkflowStep(models.Model):
    """
    A single step in a workflow.
    Maps to a locator and action with optional data binding.
    """
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="steps"
    )
    order = models.IntegerField(
        help_text="Execution order (lower = first)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Step name for logging"
    )

    # Action configuration
    action_type = models.CharField(
        max_length=30,
        choices=ActionType.choices,
        default=ActionType.CLICK
    )
    locator = models.ForeignKey(
        Locator,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Element to interact with"
    )

    # Data binding - value can come from Excel data
    value_static = models.TextField(
        blank=True,
        help_text="Static value to enter"
    )
    value_field = models.CharField(
        max_length=100,
        blank=True,
        help_text="Excel column name to get value from (e.g., 'SERIAL NO')"
    )
    value_template = models.CharField(
        max_length=200,
        blank=True,
        help_text="Template with placeholders (e.g., 'RPR-{{FROM}}-{{ID}}')"
    )

    # Conditional execution
    condition_value = models.CharField(
        max_length=100,
        blank=True,
        help_text="Only execute if workflow condition matches this value"
    )

    # D365 interaction mode — determines HOW to interact with the element
    interaction_mode = models.CharField(
        max_length=30,
        choices=InteractionMode.choices,
        default=InteractionMode.AUTO,
        help_text="D365 element interaction mode (auto-detect, combobox, lookup button, etc.)"
    )

    # Step options
    clear_before_fill = models.BooleanField(
        default=False,
        help_text="Clear field before filling"
    )
    press_key_after = models.CharField(
        max_length=50,
        blank=True,
        help_text="Key to press after action (e.g., 'Tab', 'Enter')"
    )
    wait_after = models.IntegerField(
        default=500,
        help_text="Milliseconds to wait after this step"
    )
    timeout = models.IntegerField(
        default=30000,
        help_text="Step timeout in milliseconds"
    )
    max_retries = models.IntegerField(
        default=3,
        help_text="Number of retry attempts on failure"
    )

    # Error handling
    continue_on_error = models.BooleanField(
        default=False,
        help_text="Continue workflow even if this step fails"
    )
    check_for_errors = models.BooleanField(
        default=False,
        help_text="After this step, check for D365 error dialogs"
    )
    error_handler_step = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Step to execute if this step fails"
    )

    # Save result for later use
    save_result_as = models.CharField(
        max_length=100,
        blank=True,
        help_text="Save step result to context with this key"
    )

    # Skip group — when the first COE step in a group fails, skip the rest
    skip_group = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Skip group name. When a COE step with this group fails, all subsequent steps with the same group are skipped."
    )

    # Repeat group — loop a group of steps over an array in row_data
    repeat_group = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Loop group name (e.g., 'bom_lines'). Consecutive steps with the same group repeat together."
    )
    repeat_data_source = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Key in row_data containing the list to iterate (e.g., 'BOM_LINES'). Only needed on the first step of the group."
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "erp_automation_workflow_steps"
        ordering = ["workflow", "order"]
        unique_together = ["workflow", "order"]

    def __str__(self):
        return f"{self.workflow.name} - Step {self.order}: {self.name}"

    def get_value(self, row_data, context):
        """Resolve the value for this step from various sources.

        Priority:
          1. Static value (literal string)
          2. Template with {{}} placeholders (preferred over raw field)
          3. Raw field name (direct column reference, only if no template)
        """
        import re

        # 1. Static value
        if self.value_static:
            return self.value_static

        # 2. Template with placeholders (takes priority over value_field)
        if self.value_template:
            def replacer(match):
                key = match.group(1).strip()
                if row_data and key in row_data:
                    return str(row_data[key])
                if context and key in context:
                    return str(context[key])
                return ""
            return re.sub(r'{{(.*?)}}', replacer, self.value_template)

        # 3. From Excel/data field (only when no template set)
        if self.value_field and row_data:
            return str(row_data.get(self.value_field, ""))

        return ""


# =============================================================================
# RECORDING MODELS
# =============================================================================

class RecordingSessionStatus(models.TextChoices):
    """Recording session status."""
    RECORDING = "recording", "Recording"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class RecordingSession(models.Model):
    """
    A recording session captures user actions in the browser.
    Used to create or update workflows automatically.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    target_url = models.URLField(
        help_text="URL where recording started"
    )

    # Recording state
    status = models.CharField(
        max_length=20,
        choices=RecordingSessionStatus.choices,
        default=RecordingSessionStatus.RECORDING,
        help_text="Current session status"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Optional link to job data for clipboard helper
    job_data = models.ForeignKey(
        'ERPJobData',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recording_sessions",
        help_text="Job data used during recording for copy-paste values"
    )

    # Link to generated workflow
    generated_workflow = models.ForeignKey(
        Workflow,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recording_sessions"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        db_table = "erp_automation_recording_sessions"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Recording: {self.name} ({self.started_at})"


class RecordedAction(models.Model):
    """
    A single recorded action from a recording session.
    Contains all information needed to replay the action.
    """
    session = models.ForeignKey(
        RecordingSession,
        on_delete=models.CASCADE,
        related_name="actions"
    )
    order = models.IntegerField()

    # Action details
    action_type = models.CharField(
        max_length=30,
        choices=ActionType.choices
    )

    # Element identification (multiple strategies captured)
    element_tag = models.CharField(max_length=50, blank=True)
    element_id = models.CharField(max_length=200, blank=True)
    element_name = models.CharField(max_length=200, blank=True)
    element_class = models.TextField(blank=True)
    element_xpath = models.TextField(blank=True)
    element_css = models.TextField(blank=True)
    element_text = models.TextField(blank=True)
    element_aria_label = models.CharField(max_length=200, blank=True)
    element_placeholder = models.CharField(max_length=200, blank=True)
    element_role = models.CharField(
        max_length=50, blank=True,
        help_text="ARIA role (e.g., option, menuitem, checkbox, listbox)"
    )
    element_type = models.CharField(
        max_length=50, blank=True,
        help_text="HTML type attribute (e.g., text, checkbox, radio)"
    )
    element_dyn_control_name = models.CharField(
        max_length=200, blank=True,
        help_text="D365 data-dyn-controlname from ancestor element"
    )
    element_data_testid = models.CharField(
        max_length=200, blank=True,
        help_text="data-testid attribute"
    )

    # Visual context
    element_rect = models.JSONField(
        default=dict,
        blank=True,
        help_text="Bounding box {x, y, width, height}"
    )
    screenshot = models.ImageField(
        upload_to="erp_automation/recordings/",
        blank=True,
        null=True
    )
    page_url = models.URLField(blank=True)
    page_title = models.CharField(max_length=200, blank=True)

    # Input data
    input_value = models.TextField(blank=True)
    key_pressed = models.CharField(max_length=50, blank=True)

    # Locator strategies captured during recording
    locator_strategies = models.JSONField(
        default=list,
        blank=True,
        help_text="Generated locator strategies [{strategy_type, value, priority}, ...]"
    )

    # Timing
    timestamp = models.DateTimeField(auto_now_add=True)
    duration_ms = models.IntegerField(default=0)

    class Meta:
        db_table = "erp_automation_recorded_actions"
        ordering = ["session", "order"]

    def __str__(self):
        return f"{self.session.name} - Action {self.order}: {self.action_type}"

    def get_best_identifier(self):
        """Return the best human-readable identifier for this element."""
        return (
            self.element_name or
            self.element_aria_label or
            self.element_placeholder or
            (self.element_text[:40] if self.element_text else '') or
            self.element_id[:30] if self.element_id else 'element'
        )

    def generate_locator_strategies(self):
        """Generate multiple locator strategies from recorded element data."""
        strategies = []

        # Priority order based on reliability
        if self.element_id and not self._is_dynamic_id(self.element_id):
            strategies.append({
                "strategy_type": "id",
                "value": self.element_id,
                "priority": 1
            })

        if self.element_aria_label:
            strategies.append({
                "strategy_type": "aria-label",
                "value": self.element_aria_label,
                "priority": 2
            })

        if self.element_name:
            strategies.append({
                "strategy_type": "name",
                "value": self.element_name,
                "priority": 3
            })

        if self.element_xpath:
            strategies.append({
                "strategy_type": "xpath",
                "value": self.element_xpath,
                "priority": 5
            })

        if self.element_css:
            strategies.append({
                "strategy_type": "css",
                "value": self.element_css,
                "priority": 6
            })

        if self.element_text:
            strategies.append({
                "strategy_type": "text",
                "value": self.element_text,
                "priority": 7
            })

        return strategies

    def _is_dynamic_id(self, element_id):
        """Check if an ID appears to be dynamically generated."""
        import re
        # Common patterns for dynamic IDs
        dynamic_patterns = [
            r'[0-9a-f]{8}-[0-9a-f]{4}',  # UUID-like
            r'_\d{10,}',  # Timestamp
            r'[A-Za-z]+_\d+_',  # Framework generated
            r'react-',  # React
            r'ng-',  # Angular
        ]
        for pattern in dynamic_patterns:
            if re.search(pattern, element_id):
                return True
        return False


# =============================================================================
# EXECUTION MODELS
# =============================================================================

class WorkflowExecution(models.Model):
    """
    Tracks a workflow execution run.
    """
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="executions"
    )

    status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PENDING
    )

    # Link to ERPJobData (when execution is triggered from parsed job card)
    job_data = models.ForeignKey(
        'ERPJobData',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executions',
        help_text="ERPJobData record this execution was created from"
    )

    # Link to ChainExecution (when this execution is part of a chain)
    chain_execution = models.ForeignKey(
        'ChainExecution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_executions',
        help_text="Parent chain execution (if running as part of a chain)"
    )

    # Data source
    excel_file_path = models.CharField(max_length=500, blank=True)
    sheet_name = models.CharField(max_length=100, blank=True)
    row_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="The Excel row data being processed"
    )

    # Context/variables during execution
    context = models.JSONField(default=dict, blank=True)

    # Results
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        db_table = "erp_automation_executions"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.workflow.name} - {self.status} ({self.started_at})"


class StepExecution(models.Model):
    """
    Tracks individual step execution within a workflow run.
    """
    execution = models.ForeignKey(
        WorkflowExecution,
        on_delete=models.CASCADE,
        related_name="step_executions"
    )
    step = models.ForeignKey(
        WorkflowStep,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PENDING
    )

    # Which locator strategy worked
    locator_strategy_used = models.ForeignKey(
        LocatorStrategy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Results
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    screenshot = models.ImageField(
        upload_to="erp_automation/step_screenshots/",
        blank=True,
        null=True
    )

    class Meta:
        db_table = "erp_automation_step_executions"
        ordering = ["execution", "step__order"]

    def __str__(self):
        return f"{self.execution} - Step {self.step.order}: {self.status}"


# =============================================================================
# FIELD MAPPING MODELS
# =============================================================================

class FieldMapping(models.Model):
    """
    Maps Excel column names to ERP field names.
    Handles variations in column naming.
    """
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="field_mappings"
    )

    excel_column = models.CharField(
        max_length=100,
        help_text="Column name in Excel"
    )
    erp_field = models.CharField(
        max_length=100,
        help_text="Field name in ERP"
    )
    locator = models.ForeignKey(
        Locator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Locator for the ERP field"
    )

    # Transformation
    transform_function = models.CharField(
        max_length=100,
        blank=True,
        choices=[
            ("uppercase", "Uppercase"),
            ("lowercase", "Lowercase"),
            ("trim", "Trim Whitespace"),
            ("date_format", "Format Date"),
            ("number_format", "Format Number"),
        ],
        help_text="Optional transformation to apply"
    )
    default_value = models.CharField(
        max_length=200,
        blank=True,
        help_text="Default value if Excel cell is empty"
    )

    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "erp_automation_field_mappings"
        unique_together = ["workflow", "excel_column"]

    def __str__(self):
        return f"{self.workflow.name}: {self.excel_column} -> {self.erp_field}"


# =============================================================================
# ITEM COUNTER (for auto-generated item numbers)
# =============================================================================

class ItemCounter(models.Model):
    """
    Tracks sequential counters for item number generation.
    Replaces the JSON file approach.
    """
    account_type = models.CharField(
        max_length=50,
        unique=True,
        help_text="Account type (e.g., 'RC-LSTK')"
    )
    prefix = models.CharField(
        max_length=50,
        default="RPR-",
        help_text="Prefix for item numbers"
    )
    current_number = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    padding = models.IntegerField(
        default=4,
        help_text="Zero-padding length"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "erp_automation_item_counters"

    def __str__(self):
        return f"{self.account_type}: {self.get_next_preview()}"

    def get_next_preview(self):
        """Preview the next item number without incrementing."""
        return f"{self.prefix}{self.current_number:0{self.padding}d}"

    def get_next_number(self):
        """Get next item number and increment counter."""
        if self.current_number < 1:
            self.current_number = 1
        number = f"{self.prefix}{self.current_number:0{self.padding}d}"
        self.current_number += 1
        self.save(update_fields=["current_number", "updated_at"])
        return number

    def reset(self, start_at=1):
        """Reset counter to a specific number."""
        self.current_number = max(1, start_at)
        self.save(update_fields=["current_number", "updated_at"])


# =============================================================================
# ERP ROUTE MODEL
# =============================================================================

class ERPRoute(models.Model):
    """
    Stores ERP production routes with their selection criteria.
    Routes are seeded from the Routes Excel and selected automatically
    based on bit size, port, and repair modifiers.
    """

    class BitType(models.TextChoices):
        FC = 'FC', 'Fixed Cutter'
        RC = 'RC', 'Roller Cone'

    class Level(models.TextChoices):
        L3 = 'L3', 'Level 3'
        L4 = 'L4', 'Level 4'
        L5 = 'L5', 'Level 5'
        L6 = 'L6', 'Level 6'
        REPAIR = 'REPAIR', 'Repair'
        RERUN = 'RERUN', 'Re-Run'
        INSPECTION = 'INSPECTION', 'Inspection Only'

    class SizeClass(models.TextChoices):
        AB = 'AB', 'AB (< 12")'
        JUMBO = 'JUMBO', 'Jumbo (>= 12")'

    route_number = models.CharField(max_length=20, unique=True,
        help_text="Route ID in ERP (e.g., ROUTE-0091)")
    name = models.CharField(max_length=200, blank=True,
        help_text="Route name (e.g., FC-R AB With Port Standard)")
    item_group = models.CharField(max_length=50, blank=True,
        help_text="Item group in ERP (e.g., RPR-FC-AR)")

    # Classification
    bit_type = models.CharField(max_length=5, choices=BitType.choices, default='FC')
    level = models.CharField(max_length=15, choices=Level.choices, blank=True)
    size_class = models.CharField(max_length=10, choices=SizeClass.choices, blank=True)
    has_port = models.BooleanField(null=True, blank=True,
        help_text="True=With Port, False=No Port, Null=N/A")

    # Repair modifiers
    has_usr = models.BooleanField(default=False, help_text="Upper Section Replacement")
    has_hardfacing = models.BooleanField(default=False, help_text="Hardfacing/Matrix Repair")
    has_crush_shear = models.BooleanField(default=False, help_text="Crush & Shear")
    has_retro = models.BooleanField(default=False, help_text="Retrofit (L6 only)")
    has_grinding = models.BooleanField(default=False, help_text="Grinding step")

    # RC-specific flags
    is_sealed = models.BooleanField(null=True, blank=True, help_text="RC: Sealed/NonSealed")
    has_cc = models.BooleanField(null=True, blank=True, help_text="RC: With/Without CC")

    # Approval
    approved = models.BooleanField(default=False)
    approved_by = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'erp_automation_routes'
        ordering = ['route_number']
        verbose_name = 'ERP Route'
        verbose_name_plural = 'ERP Routes'

    def __str__(self):
        return f"{self.route_number} - {self.name}" if self.name else self.route_number


# =============================================================================
# ERP JOB DATA MODEL
# =============================================================================

class ERPJobData(models.Model):
    """
    Holds all collected and computed data per work order,
    ready for ERP automation (item creation, production order, etc.).
    Data is parsed from Job Card Excel files.
    """

    class BodyMaterial(models.TextChoices):
        SB = 'SB', 'Steel Body'
        MB = 'MB', 'Matrix Body'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        READY = 'READY', 'Ready for ERP'
        SENT = 'SENT', 'Sent to ERP'
        COMPLETED = 'COMPLETED', 'Completed'
        ERROR = 'ERROR', 'Error'

    # --- Raw data from Job Card Excel ---
    work_order_number = models.CharField(max_length=50,
        help_text="ARDT Work Order Number")
    serial_number = models.CharField(max_length=50,
        help_text="Bit serial number")
    size_raw = models.CharField(max_length=30, blank=True,
        help_text="Raw size from Excel (e.g., '3 3/4\"' or 6.125)")
    size_inches = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True,
        help_text="Parsed numeric size in inches")
    smi_type = models.CharField(max_length=50, blank=True,
        help_text="HDBS/SMI Type (e.g., GT53s, HD54)")
    l5_mat_full = models.CharField(max_length=50, blank=True,
        help_text="Full LV5 Mat # with suffix (e.g., 1224750M)")
    date_received = models.DateField(null=True, blank=True)
    account = models.CharField(max_length=50,
        help_text="Account/FROM (e.g., LSTK, ARAMCO)")
    contract_number = models.CharField(max_length=50, blank=True)
    vendor_number = models.CharField(max_length=50, blank=True)
    l3_l4_mat = models.CharField(max_length=50, blank=True,
        help_text="LV3/LV4 Mat #")
    evaluated_by = models.CharField(max_length=100, blank=True)
    reviewed_by = models.CharField(max_length=100, blank=True)

    # --- Cutter data from Job Card (JSON) ---
    cutter_bom_data = models.JSONField(default=list, blank=True,
        help_text="Cutter BOM with variant breakdown")
    modified_cutters_data = models.JSONField(default=list, blank=True,
        help_text="Modified cutters (cutter swaps)")

    # --- Computed / Derived fields ---
    l5_mat_original = models.CharField(max_length=50, blank=True,
        help_text="Original L5 MAT (digits only, M stripped)")
    body_material = models.CharField(max_length=5, choices=BodyMaterial.choices, blank=True,
        help_text="SB if type starts/ends with 's', else MB")
    item_group = models.CharField(max_length=30, blank=True,
        help_text="ERP Item Group (e.g., RPR-FC-LST)")
    size_class = models.CharField(max_length=10, blank=True,
        help_text="AB (<12\") or JUMBO (>=12\")")
    has_port = models.BooleanField(default=False,
        help_text="True if size < 4\"")

    # --- Repair modifiers (from Job Card) ---
    has_usr = models.BooleanField(default=False,
        help_text="Upper Section Replacement (Data E31)")
    has_hardfacing = models.BooleanField(default=False,
        help_text="Hardfacing/Matrix Repair (Eval D36 or Eval-LSTK R34/U34/X34)")
    has_crush_shear = models.BooleanField(default=False,
        help_text="Crush & Shear (type starts/ends with CS)")
    is_rerun = models.BooleanField(default=False,
        help_text="Re-run job (Data L2=1 or L3=1)")
    is_inspection_only = models.BooleanField(default=False,
        help_text="Initial Bit Inspection only (Data L4=1)")
    is_scrap = models.BooleanField(default=False,
        help_text="Scrap (Data L5=1)")

    # --- Route ---
    route = models.ForeignKey(ERPRoute, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='job_data',
        help_text="Auto-selected or manually overridden route")
    route_override = models.BooleanField(default=False,
        help_text="True if user manually changed the route")

    # --- ERP output ---
    item_number = models.CharField(max_length=50, blank=True,
        help_text="Generated or ERP-assigned item number")
    production_order_number = models.CharField(max_length=50, blank=True)
    transfer_order_number = models.CharField(max_length=50, blank=True)
    movement_journal_number = models.CharField(max_length=50, blank=True,
        help_text="Movement Journal number captured from D365")
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Repair price from quotation sheet")

    # --- Metadata ---
    source_file = models.CharField(max_length=500, blank=True,
        help_text="Original Excel filename")
    status = models.CharField(max_length=20, choices=Status.choices, default='DRAFT')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='erp_job_data')

    class Meta:
        db_table = 'erp_automation_job_data'
        ordering = ['-created_at']
        verbose_name = 'ERP Job Data'
        verbose_name_plural = 'ERP Job Data'

    def __str__(self):
        return f"{self.work_order_number} - {self.serial_number} ({self.status})"

    # ── Status transition validation ──────────────────────────────
    STATUS_TRANSITIONS = {
        'DRAFT': ['READY', 'ERROR'],
        'READY': ['SENT', 'ERROR'],
        'SENT': ['COMPLETED', 'ERROR'],
        'ERROR': ['READY'],          # allow retry after error
        'COMPLETED': [],             # terminal
    }

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        if self.pk:
            try:
                original = ERPJobData.objects.only('status').get(pk=self.pk)
            except ERPJobData.DoesNotExist:
                return
            if original.status != self.status:
                allowed = self.STATUS_TRANSITIONS.get(original.status, [])
                if self.status not in allowed:
                    raise ValidationError({
                        'status': f"Cannot change status from '{original.get_status_display()}' to "
                                  f"'{self.get_status_display()}'. "
                                  f"Allowed transitions: {', '.join(allowed) or 'none (terminal state)'}."
                    })

    def get_active_execution(self):
        """Return (type, execution) for any running/pending execution, or (None, None).

        Checks chain executions first (most common), then standalone workflow executions.
        """
        ce = self.chain_executions.filter(
            status__in=['pending', 'running']
        ).order_by('-started_at').first()
        if ce:
            return ('chain', ce)
        we = self.executions.filter(
            status__in=['pending', 'running'],
            chain_execution__isnull=True,
        ).order_by('-started_at').first()
        if we:
            return ('workflow', we)
        return (None, None)

    def get_active_execution_url(self):
        """Return the redirect URL for the active execution, or empty string."""
        exec_type, active_exec = self.get_active_execution()
        if exec_type == 'chain':
            return f'/erp-automation/chain-executions/{active_exec.pk}/'
        if exec_type == 'workflow':
            return f'/erp-automation/live/{active_exec.pk}/'
        return ''

    def get_display_name(self):
        """Short display name for UI."""
        return f"WO {self.work_order_number}" if self.work_order_number else f"Job #{self.pk}"

    @property
    def job_type(self):
        """Return job type: Scrap, Rerun, or Repair."""
        if self.is_scrap:
            return 'Scrap'
        if self.is_rerun:
            return 'Rerun'
        return 'Repair'

    def _format_size(self):
        """Format size as clean fraction string.

        12.000 → "12", 6.125 → "6 1/8", 8.500 → "8 1/2", etc.
        Falls back to size_raw if size_inches is not set.
        """
        from apps.erp_automation.templatetags.erp_filters import format_size_fraction
        if self.size_inches is not None:
            return format_size_fraction(self.size_inches)
        return self.size_raw or ''

    def get_row_data(self):
        """Convert ERPJobData fields to a row_data dict for workflow template substitution.

        The workflow steps use template variables like {{SERIAL NO}}, {{ORDER NO.}}, etc.
        This method maps the model fields to those exact template variable names.

        Template variables used in the "Create Item" workflow:
          {{ITEM NO}}      — ERP item number (auto-generated or assigned)
          {{ORDER NO.}}    — Work order number
          {{SERIAL NO}}    — Bit serial number
          {{SIZE}}         — Bit size in inches
          {{TYPE}}         — SMI/HDBS Type (e.g., GT53s)
          {{MAT NO.}}      — L5 Material number (original, M stripped)
          {{FROM}}         — Account name (used for conditional branching)

        Also includes extra fields that may be useful for future workflows.
        """
        row = {
            # --- Primary template variables (used by Create Item workflow) ---
            'ITEM NO': self.item_number or '',
            'ORDER NO.': self.work_order_number or '',
            'SERIAL NO': self.serial_number or '',
            'SIZE': self._format_size(),
            'TYPE': self.smi_type or '',
            'MAT NO.': self.l5_mat_original or self.l5_mat_full or '',
            'FROM': self.account or '',

            # --- Extra fields for future workflows ---
            'ACCOUNT': self.account or '',
            'L5_MAT_FULL': self.l5_mat_full or '',
            'L5_MAT_ORIGINAL': self.l5_mat_original or '',
            'BODY_MATERIAL': self.body_material or '',
            'ITEM_GROUP': self.item_group or '',
            'SIZE_CLASS': self.size_class or '',
            'SIZE_RAW': self.size_raw or '',
            'CONTRACT_NO': self.contract_number or '',
            'VENDOR_NO': self.vendor_number or '',
            'ROUTE': self.route.route_number if self.route else '',
            'ROUTE_NAME': self.route.name if self.route else '',
            'WO_NUMBER': self.work_order_number or '',
            'PRICE': str(self.price or ''),

            # --- Job type flags (for conditional chain/workflow execution) ---
            'IS_SCRAP': 'true' if self.is_scrap else 'false',
            'IS_RERUN': 'true' if self.is_rerun else 'false',
            'JOB_TYPE': 'Scrap' if self.is_scrap else ('Rerun' if self.is_rerun else 'Repair'),
            'HAS_ROUTE': 'true' if self.route else 'false',
        }

        # --- Flatten cutter BOM variants into BOM_LINE_N_ITEM / BOM_LINE_N_QTY ---
        # Each variant with an ERP item number becomes a separate BOM line.
        # Supports up to 8 lines (covers all observed ARAMCO recordings: 3-5 lines).
        # For scrap/rerun: skip BOM lines — WF-7B deletes existing lines but adds none.
        flat_lines = []
        if not self.is_scrap and not self.is_rerun:
            for group in (self.cutter_bom_data or []):
                for v in (group.get('variants') or []):
                    erp_no = v.get('erp_item_no', '')
                    qty = v.get('qty', 0)
                    if erp_no and qty:
                        flat_lines.append((erp_no, str(qty)))
        for i in range(8):
            if i < len(flat_lines):
                row[f'BOM_LINE_{i+1}_ITEM'] = flat_lines[i][0]
                row[f'BOM_LINE_{i+1}_QTY'] = flat_lines[i][1]
            else:
                row[f'BOM_LINE_{i+1}_ITEM'] = ''
                row[f'BOM_LINE_{i+1}_QTY'] = ''

        # BOM_LINES: list of dicts for repeat-group loop iteration (unlimited)
        # Empty for scrap/rerun — repeat group produces 0 iterations (no lines added)
        row['BOM_LINES'] = [
            {'ITEM': item, 'QTY': qty}
            for item, qty in flat_lines
        ]

        return row


# =============================================================================
# COMPOSITE WORKFLOW (CHAIN) MODELS
# =============================================================================

class WorkflowChainStatus(models.TextChoices):
    """Chain status."""
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


class WorkflowChain(models.Model):
    """
    A chain of workflows executed in sequence for the same job card.

    Example: "Full LSTK ERP Processing" might chain:
      1. Create Released Product (WF#8)
      2. Create Production Order
      3. Create Transfer Order
      4. Post BOM

    Each sub-workflow remains independently testable/debuggable.
    The browser can stay open between sub-workflows for speed.
    """
    name = models.CharField(
        max_length=150,
        unique=True,
        help_text="Chain name (e.g., 'Full LSTK ERP Processing')"
    )
    description = models.TextField(
        blank=True,
        help_text="What this chain of workflows does"
    )

    # Conditional execution (same concept as Workflow.condition_field)
    condition_field = models.CharField(
        max_length=100,
        blank=True,
        help_text="Field used for conditional branching (e.g., 'FROM')"
    )

    status = models.CharField(
        max_length=20,
        choices=WorkflowChainStatus.choices,
        default=WorkflowChainStatus.DRAFT
    )

    # Execution options
    stop_on_failure = models.BooleanField(
        default=True,
        help_text="Stop chain if a sub-workflow fails"
    )
    keep_browser_open = models.BooleanField(
        default=True,
        help_text="Keep browser open between sub-workflows (faster, preserves login)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_chains"
    )

    class Meta:
        db_table = "erp_automation_workflow_chains"
        ordering = ["name"]
        verbose_name = "Workflow Chain"
        verbose_name_plural = "Workflow Chains"

    def __str__(self):
        return self.name

    def get_active_links(self):
        """Return active links in order."""
        return self.links.filter(is_active=True).order_by("order")

    @property
    def link_count(self):
        return self.links.filter(is_active=True).count()


class WorkflowChainLink(models.Model):
    """
    A single link in a workflow chain — points to a Workflow with
    execution order and optional overrides.

    Supports:
    - Sequential ordering
    - Per-link wait time before starting
    - URL override (navigate to different page before running)
    - Context mapping (pass output vars from previous links into row_data)
    - Conditional skip (only run this link for certain condition values)
    """
    chain = models.ForeignKey(
        WorkflowChain,
        on_delete=models.CASCADE,
        related_name="links"
    )
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.PROTECT,
        related_name="chain_links",
        help_text="The workflow to execute at this position"
    )
    order = models.IntegerField(
        help_text="Execution order within the chain (lower = first)"
    )
    name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Optional label (defaults to workflow name)"
    )

    # Timing
    wait_before_ms = models.IntegerField(
        default=2000,
        help_text="Milliseconds to wait before starting this link"
    )

    # URL override
    navigate_url = models.URLField(
        blank=True,
        help_text="Override workflow's target_url (navigate here before running)"
    )

    # Context mapping: pass outputs from prior links into this link's row_data
    # Example: {"ITEM_FROM_STEP_1": "item_number"}
    #   → row_data["ITEM_FROM_STEP_1"] = context["item_number"]
    context_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text='Map context vars to row_data keys. Example: {"ITEM_NO": "created_item_number"}'
    )

    # Conditional execution (skip this link if condition doesn't match)
    condition_field = models.CharField(
        max_length=100,
        blank=True,
        help_text="Field to check for skipping this link"
    )
    condition_value = models.CharField(
        max_length=100,
        blank=True,
        help_text="Only execute if condition_field matches this value"
    )

    # Page precondition check — inspect live page before running this link
    # If set, the chain executor checks the page for the element/text.
    # skip_if_found=True → skip this link if element IS found (e.g. BOM already exists)
    # skip_if_found=False → skip this link if element is NOT found
    PRECONDITION_TYPES = [
        ("", "No check"),
        ("element_exists", "Element exists (CSS/XPath)"),
        ("text_contains", "Page contains text"),
        ("element_count_gt", "Element count > value"),
    ]
    precondition_type = models.CharField(
        max_length=30,
        blank=True,
        default="",
        choices=PRECONDITION_TYPES,
        help_text="Type of page check before running this link"
    )
    precondition_selector = models.TextField(
        blank=True,
        default="",
        help_text="CSS selector, XPath, or text to search for on the page"
    )
    precondition_value = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Expected value (for count checks) or search text"
    )
    skip_if_found = models.BooleanField(
        default=True,
        help_text="True = skip this link if precondition IS met. False = skip if NOT met."
    )
    precondition_timeout_ms = models.IntegerField(
        default=5000,
        help_text="How long to wait for the precondition check (ms)"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "erp_automation_chain_links"
        ordering = ["chain", "order"]
        unique_together = ["chain", "order"]
        verbose_name = "Chain Link"
        verbose_name_plural = "Chain Links"

    def __str__(self):
        label = self.name or self.workflow.name
        return f"{self.chain.name} → #{self.order}: {label}"

    def get_display_name(self):
        return self.name or self.workflow.name


class ChainExecution(models.Model):
    """
    Tracks a chain execution run.

    Each chain execution creates multiple WorkflowExecution records
    (one per link), linked back via WorkflowExecution.chain_execution FK.
    """
    chain = models.ForeignKey(
        WorkflowChain,
        on_delete=models.CASCADE,
        related_name="executions"
    )
    job_data = models.ForeignKey(
        ERPJobData,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chain_executions",
        help_text="Job data record being processed"
    )

    status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PENDING
    )

    # Row data snapshot
    row_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Initial row_data from job_data.get_row_data()"
    )

    # Accumulated context from all completed links
    context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Accumulated context vars from all completed links"
    )

    # Progress tracking
    total_links = models.IntegerField(default=0)
    completed_links = models.IntegerField(default=0)
    current_link_order = models.IntegerField(
        null=True,
        blank=True,
        help_text="Order of the currently executing link"
    )

    # Results
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        db_table = "erp_automation_chain_executions"
        ordering = ["-started_at"]
        verbose_name = "Chain Execution"
        verbose_name_plural = "Chain Executions"

    def __str__(self):
        return f"{self.chain.name} - {self.status} ({self.started_at})"

    @property
    def progress_percent(self):
        if self.total_links == 0:
            return 0
        return int((self.completed_links / self.total_links) * 100)

    @property
    def duration_seconds(self):
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


# =============================================================================
# ERP ENVIRONMENT
# =============================================================================

class ERPEnvironment(models.Model):
    """
    Stores named ERP environment URLs (e.g. Sandbox, Production).
    Used across all execution contexts: workflow, chain, debug, recording.
    Selected via the credentials page; stored URL goes into session.
    """
    name = models.CharField(max_length=100, unique=True)
    url = models.URLField(max_length=500)
    is_default = models.BooleanField(
        default=False,
        help_text="Default environment pre-selected on credentials page"
    )
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "erp_automation_environments"
        ordering = ["sort_order", "name"]
        verbose_name = "ERP Environment"
        verbose_name_plural = "ERP Environments"

    def __str__(self):
        return f"{self.name} — {self.url}"

    def save(self, *args, **kwargs):
        # Ensure only one default
        if self.is_default:
            ERPEnvironment.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
