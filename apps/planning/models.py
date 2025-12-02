"""
ARDT FMS - Planning Models
Version: 5.4 (NEW)

Tables:
- sprints (P1)
- planning_boards (P1)
- planning_columns (P1)
- planning_labels (P1)
- planning_items (P1)
- planning_item_labels (P1)
- planning_item_watchers (P1)
- wiki_spaces (P1)
- wiki_pages (P1)
- wiki_page_versions (P1)

This is the Notion-style planning module for internal project management.
"""

from django.conf import settings
from django.db import models


class Sprint(models.Model):
    """
    🟢 P1: Sprints for agile planning.
    """

    class Status(models.TextChoices):
        PLANNING = "PLANNING", "Planning"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, help_text="e.g., SPRINT-01")
    goal = models.TextField(blank=True)

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNING)

    # Capacity
    capacity_points = models.IntegerField(default=0, help_text="Total story points available")

    # Progress (computed)
    completed_points = models.IntegerField(default=0)

    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="owned_sprints"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_sprints"
    )

    class Meta:
        db_table = "sprints"
        ordering = ["-start_date"]
        verbose_name = "Sprint"
        verbose_name_plural = "Sprints"

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def progress_percent(self):
        if self.capacity_points == 0:
            return 0
        return int((self.completed_points / self.capacity_points) * 100)


class PlanningBoard(models.Model):
    """
    🟢 P1: Kanban boards for planning.
    """

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)

    # Optional sprint link
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name="boards")

    # Icon/Color
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=20, blank=True)

    # Settings
    default_wip_limit = models.IntegerField(default=0, help_text="0 = no limit")

    is_active = models.BooleanField(default=True)

    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="owned_boards"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "planning_boards"
        ordering = ["name"]
        verbose_name = "Planning Board"
        verbose_name_plural = "Planning Boards"

    def __str__(self):
        return self.name


class PlanningColumn(models.Model):
    """
    🟢 P1: Columns in a Kanban board.
    """

    board = models.ForeignKey(PlanningBoard, on_delete=models.CASCADE, related_name="columns")
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20)

    sequence = models.IntegerField(default=0)
    wip_limit = models.IntegerField(default=0, help_text="0 = no limit")

    # Styling
    color = models.CharField(max_length=20, blank=True)

    # Column type
    is_done_column = models.BooleanField(default=False, help_text="Items here count as completed")
    is_backlog_column = models.BooleanField(default=False, help_text="Items here are not started")

    class Meta:
        db_table = "planning_columns"
        ordering = ["board", "sequence"]
        unique_together = ["board", "code"]
        verbose_name = "Planning Column"
        verbose_name_plural = "Planning Columns"

    def __str__(self):
        return f"{self.board.name} - {self.name}"


class PlanningLabel(models.Model):
    """
    🟢 P1: Labels/Tags for planning items.
    """

    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default="#6b7280")
    description = models.TextField(blank=True)

    class Meta:
        db_table = "planning_labels"
        ordering = ["name"]
        verbose_name = "Planning Label"
        verbose_name_plural = "Planning Labels"

    def __str__(self):
        return self.name


class PlanningItem(models.Model):
    """
    🟢 P1: Planning items (Epics, Stories, Tasks, Bugs).
    """

    class ItemType(models.TextChoices):
        EPIC = "EPIC", "Epic"
        STORY = "STORY", "Story"
        TASK = "TASK", "Task"
        BUG = "BUG", "Bug"
        SUBTASK = "SUBTASK", "Subtask"

    class Priority(models.TextChoices):
        LOWEST = "LOWEST", "Lowest"
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        HIGHEST = "HIGHEST", "Highest"

    # Basic info
    code = models.CharField(max_length=20, unique=True, help_text="e.g., ARDT-123")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Markdown supported")

    item_type = models.CharField(max_length=20, choices=ItemType.choices, default=ItemType.TASK)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)

    # Board position
    board = models.ForeignKey(PlanningBoard, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")
    column = models.ForeignKey(PlanningColumn, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")
    position = models.IntegerField(default=0, help_text="Order within column")

    # Sprint
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")

    # Hierarchy
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")

    # Estimation
    story_points = models.IntegerField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # Dates
    due_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)

    # Assignment
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_items"
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reported_items"
    )

    # Labels
    labels = models.ManyToManyField(PlanningLabel, through="PlanningItemLabel", related_name="items")

    # Links to other entities
    work_order = models.ForeignKey(
        "workorders.WorkOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="planning_items"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_planning_items"
    )

    class Meta:
        db_table = "planning_items"
        ordering = ["column", "position"]
        verbose_name = "Planning Item"
        verbose_name_plural = "Planning Items"

    def __str__(self):
        return f"{self.code} - {self.title}"


class PlanningItemLabel(models.Model):
    """
    🟢 P1: Many-to-many between items and labels.
    """

    item = models.ForeignKey(PlanningItem, on_delete=models.CASCADE, related_name="item_labels")
    label = models.ForeignKey(PlanningLabel, on_delete=models.CASCADE, related_name="label_items")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "planning_item_labels"
        unique_together = ["item", "label"]

    def __str__(self):
        return f"{self.item.code} - {self.label.name}"


class PlanningItemWatcher(models.Model):
    """
    🟢 P1: Users watching planning items for notifications.
    """

    item = models.ForeignKey(PlanningItem, on_delete=models.CASCADE, related_name="watchers")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watched_items")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "planning_item_watchers"
        unique_together = ["item", "user"]

    def __str__(self):
        return f"{self.user.username} watching {self.item.code}"


class WikiSpace(models.Model):
    """
    🟢 P1: Wiki spaces (like Notion workspaces).
    """

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)

    is_public = models.BooleanField(default=False, help_text="Visible to all users")

    # Owner
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="owned_wiki_spaces")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wiki_spaces"
        ordering = ["name"]
        verbose_name = "Wiki Space"
        verbose_name_plural = "Wiki Spaces"

    def __str__(self):
        return self.name


class WikiPage(models.Model):
    """
    🟢 P1: Wiki pages (Notion-style pages).
    """

    space = models.ForeignKey(WikiSpace, on_delete=models.CASCADE, related_name="pages")

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    icon = models.CharField(max_length=50, blank=True)
    cover_image = models.ImageField(upload_to="wiki/covers/", null=True, blank=True)

    # Content (Markdown)
    content = models.TextField(blank=True)

    # Hierarchy
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    sequence = models.IntegerField(default=0, help_text="Order within parent")

    # Metadata
    is_published = models.BooleanField(default=True)
    is_template = models.BooleanField(default=False)

    # Stats
    view_count = models.IntegerField(default=0)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_wiki_pages"
    )
    last_edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="last_edited_wiki_pages"
    )

    class Meta:
        db_table = "wiki_pages"
        ordering = ["space", "sequence", "title"]
        unique_together = ["space", "slug"]
        verbose_name = "Wiki Page"
        verbose_name_plural = "Wiki Pages"

    def __str__(self):
        return f"{self.space.code}/{self.slug}"


class WikiPageVersion(models.Model):
    """
    🟢 P1: Version history for wiki pages.
    """

    page = models.ForeignKey(WikiPage, on_delete=models.CASCADE, related_name="versions")
    version_number = models.IntegerField()

    # Snapshot
    title = models.CharField(max_length=200)
    content = models.TextField()

    # Change tracking
    change_summary = models.CharField(max_length=500, blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wiki_page_versions"
        ordering = ["page", "-version_number"]
        unique_together = ["page", "version_number"]
        verbose_name = "Wiki Page Version"
        verbose_name_plural = "Wiki Page Versions"

    def __str__(self):
        return f"{self.page} v{self.version_number}"
