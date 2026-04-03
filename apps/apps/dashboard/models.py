"""
ARDT FMS - Dashboard Models
Version: 5.4

Models for saved/custom dashboards.
"""

from django.db import models
from django.conf import settings


class SavedDashboard(models.Model):
    """
    User-created custom dashboard configurations.

    Users can create named dashboards with custom widget layouts,
    save them, and optionally share them with specific roles.
    """

    class Visibility(models.TextChoices):
        PRIVATE = "PRIVATE", "Private (only me)"
        SHARED = "SHARED", "Shared with roles"
        PUBLIC = "PUBLIC", "Public (all users)"

    # Basic info
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default="layout-dashboard")

    # Ownership
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_dashboards"
    )

    # Widget configuration (same format as UserPreference.dashboard_widgets)
    widget_config = models.JSONField(default=list, help_text="Widget layout configuration")

    # Visibility and sharing
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE
    )
    shared_with_roles = models.ManyToManyField(
        "accounts.Role",
        blank=True,
        related_name="shared_dashboards",
        help_text="Roles that can view this dashboard"
    )

    # Settings
    is_default = models.BooleanField(
        default=False,
        help_text="Make this dashboard the default for users with access"
    )
    show_in_sidebar = models.BooleanField(
        default=True,
        help_text="Show this dashboard in the sidebar"
    )

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dashboard_saved"
        verbose_name = "Saved Dashboard"
        verbose_name_plural = "Saved Dashboards"
        ordering = ["-is_default", "name"]

    def __str__(self):
        return f"{self.name} ({self.created_by.username})"

    @property
    def widget_count(self):
        """Return the number of widgets in this dashboard."""
        if isinstance(self.widget_config, list):
            return len([w for w in self.widget_config if w.get("visible", True)])
        return 0

    @property
    def dashboard_type_key(self):
        """Return a unique key for this saved dashboard for user preferences."""
        return f"saved_{self.pk}"

    def can_view(self, user):
        """Check if a user can view this dashboard."""
        # Owner can always view
        if self.created_by == user:
            return True

        # Public dashboards are visible to all
        if self.visibility == self.Visibility.PUBLIC:
            return True

        # Shared dashboards are visible to users with matching roles
        if self.visibility == self.Visibility.SHARED:
            user_roles = user.roles.all()
            shared_roles = self.shared_with_roles.all()
            return any(role in shared_roles for role in user_roles)

        return False

    def can_edit(self, user):
        """Check if a user can edit this dashboard."""
        # Only owner can edit
        return self.created_by == user or user.is_superuser


class DashboardFavorite(models.Model):
    """
    Track which dashboards a user has favorited/pinned.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_dashboards"
    )
    dashboard = models.ForeignKey(
        SavedDashboard,
        on_delete=models.CASCADE,
        related_name="favorited_by"
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dashboard_favorites"
        unique_together = ["user", "dashboard"]
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.dashboard.name}"
