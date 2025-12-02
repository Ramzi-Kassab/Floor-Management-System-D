from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Permission, Role, RolePermission, User, UserPreference, UserRole


class UserRoleInline(admin.TabularInline):
    model = UserRole
    fk_name = "user"  # Specify which FK to User to use
    extra = 1
    autocomplete_fields = ["role", "assigned_by"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "employee_id", "department", "is_active", "is_staff"]
    list_filter = ["is_active", "is_staff", "department", "roles"]
    search_fields = ["username", "email", "first_name", "last_name", "employee_id"]
    ordering = ["username"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Employee Info", {"fields": ("employee_id", "department", "position")}),
        ("Contact", {"fields": ("phone", "phone_extension", "mobile")}),
        ("Profile", {"fields": ("profile_photo", "signature", "language", "timezone", "theme")}),
    )

    inlines = [UserRoleInline]


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1
    autocomplete_fields = ["permission", "granted_by"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "level", "is_system", "is_active"]
    list_filter = ["is_system", "is_active", "level"]
    search_fields = ["code", "name"]
    inlines = [RolePermissionInline]  # Use inline instead of filter_horizontal


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "module"]
    list_filter = ["module"]
    search_fields = ["code", "name"]


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ["role", "permission", "granted_at", "granted_by"]
    list_filter = ["role"]
    autocomplete_fields = ["role", "permission", "granted_by"]


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "assigned_at", "is_primary"]
    list_filter = ["role", "is_primary"]
    autocomplete_fields = ["user", "role", "assigned_by"]


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user", "default_dashboard", "items_per_page"]
    autocomplete_fields = ["user"]
