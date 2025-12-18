"""
ARDT FMS - Role Template Tags
Version: 5.4 - Sprint 1

Custom template tags for role-based access control in templates.
"""

from django import template

register = template.Library()


@register.filter
def has_role(user, role):
    """
    Check if user has a specific role.

    Usage in templates:
        {% load role_tags %}
        {% if user|has_role:"ADMIN" %}
            ... admin content ...
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False

    # Check for superuser
    if user.is_superuser:
        return True

    # Use the model's has_role method if available
    if hasattr(user, "has_role"):
        return user.has_role(role)

    return False


@register.filter
def has_any_role(user, roles):
    """
    Check if user has any of the specified roles (comma-separated).

    Usage in templates:
        {% load role_tags %}
        {% if user|has_any_role:"ADMIN,MANAGER" %}
            ... admin or manager content ...
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    role_list = [r.strip() for r in roles.split(",")]

    if hasattr(user, "has_role"):
        return any(user.has_role(role) for role in role_list)

    return False


@register.filter
def has_all_roles(user, roles):
    """
    Check if user has all of the specified roles (comma-separated).

    Usage in templates:
        {% load role_tags %}
        {% if user|has_all_roles:"MANAGER,QC" %}
            ... content for users with both roles ...
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    role_list = [r.strip() for r in roles.split(",")]

    if hasattr(user, "has_role"):
        return all(user.has_role(role) for role in role_list)

    return False


@register.simple_tag
def user_roles(user):
    """
    Get list of user's roles as a comma-separated string.

    Usage in templates:
        {% load role_tags %}
        {% user_roles user as roles %}
        {{ roles }}
    """
    if not user or not user.is_authenticated:
        return ""

    if hasattr(user, "role_codes"):
        roles = user.role_codes
        if roles:
            return ", ".join(roles)

    return ""


@register.filter
def is_technician(user):
    """Shortcut filter for technician role check."""
    return has_role(user, "TECHNICIAN")


@register.filter
def is_manager(user):
    """Shortcut filter for manager role check."""
    return has_any_role(user, "ADMIN,MANAGER")


@register.filter
def is_planner(user):
    """Shortcut filter for planner role check."""
    return has_role(user, "PLANNER")


@register.filter
def is_qc(user):
    """Shortcut filter for QC role check."""
    return has_role(user, "QC")


@register.filter
def can_edit_workorder(user):
    """Check if user can edit work orders."""
    return has_any_role(user, "ADMIN,MANAGER,PLANNER")


@register.filter
def can_view_reports(user):
    """Check if user can view reports."""
    return has_any_role(user, "ADMIN,MANAGER,PLANNER,QC")


@register.inclusion_tag("components/user_avatar.html")
def show_avatar(user, size="md", show_name=False, show_role=False):
    """
    Render user avatar component.

    Usage in templates:
        {% load role_tags %}
        {% show_avatar user %}
        {% show_avatar user "lg" True %}
    """
    return {
        "user": user,
        "size": size,
        "show_name": show_name,
        "show_role": show_role,
    }


@register.inclusion_tag("components/status_badge.html")
def status_badge(status, status_display=None):
    """
    Render status badge component.

    Usage in templates:
        {% load role_tags %}
        {% status_badge work_order.status work_order.get_status_display %}
    """
    return {
        "status": status,
        "status_display": status_display or status,
    }


@register.inclusion_tag("components/priority_badge.html")
def priority_badge(priority, priority_display=None):
    """
    Render priority badge component.

    Usage in templates:
        {% load role_tags %}
        {% priority_badge work_order.priority work_order.get_priority_display %}
    """
    return {
        "priority": priority,
        "priority_display": priority_display or priority,
    }


@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary by key.

    Usage in templates:
        {% load role_tags %}
        {{ my_dict|get_item:key_var }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
