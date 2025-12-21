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

    def get_steps_for_condition(self, condition_value=None):
        """Get workflow steps, filtered by condition if applicable."""
        steps = self.steps.filter(is_active=True).order_by("order")
        if condition_value:
            # Filter steps that match the condition or have no condition
            steps = steps.filter(
                models.Q(condition_value="") |
                models.Q(condition_value=condition_value)
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
        max_length=20,
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
        """Resolve the value for this step from various sources."""
        import re

        # 1. Static value
        if self.value_static:
            return self.value_static

        # 2. From Excel field
        if self.value_field and row_data:
            return str(row_data.get(self.value_field, ""))

        # 3. Template with placeholders
        if self.value_template:
            def replacer(match):
                key = match.group(1).strip()
                if row_data and key in row_data:
                    return str(row_data[key])
                if context and key in context:
                    return str(context[key])
                return ""
            return re.sub(r'{{(.*?)}}', replacer, self.value_template)

        return ""


# =============================================================================
# RECORDING MODELS
# =============================================================================

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
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

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
        max_length=20,
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

    # Timing
    timestamp = models.DateTimeField(auto_now_add=True)
    duration_ms = models.IntegerField(default=0)

    class Meta:
        db_table = "erp_automation_recorded_actions"
        ordering = ["session", "order"]

    def __str__(self):
        return f"{self.session.name} - Action {self.order}: {self.action_type}"

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
        number = f"{self.prefix}{self.current_number:0{self.padding}d}"
        self.current_number += 1
        self.save(update_fields=["current_number", "updated_at"])
        return number

    def reset(self, start_at=1):
        """Reset counter to a specific number."""
        self.current_number = start_at
        self.save(update_fields=["current_number", "updated_at"])
