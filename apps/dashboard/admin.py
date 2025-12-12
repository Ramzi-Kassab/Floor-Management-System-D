from django.contrib import admin

from .models import DashboardFavorite, SavedDashboard


@admin.register(SavedDashboard)
class SavedDashboardAdmin(admin.ModelAdmin):
    list_display = ["name", "created_by", "visibility", "widget_count", "is_default", "show_in_sidebar", "created_at"]
    list_filter = ["visibility", "is_default", "show_in_sidebar", "is_active"]
    search_fields = ["name", "description", "created_by__username"]
    filter_horizontal = ["shared_with_roles"]
    readonly_fields = ["created_at", "updated_at", "widget_count"]

    fieldsets = (
        (None, {
            "fields": ("name", "description", "icon", "created_by")
        }),
        ("Widget Configuration", {
            "fields": ("widget_config",),
            "classes": ("collapse",)
        }),
        ("Visibility & Sharing", {
            "fields": ("visibility", "shared_with_roles")
        }),
        ("Settings", {
            "fields": ("is_default", "show_in_sidebar", "is_active")
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(DashboardFavorite)
class DashboardFavoriteAdmin(admin.ModelAdmin):
    list_display = ["user", "dashboard", "order", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "dashboard__name"]
    ordering = ["user", "order"]
