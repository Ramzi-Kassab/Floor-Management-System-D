"""
ARDT FMS - Permission Context Processors
Version: 5.4

Context processors for template-level permission checking.
"""


def permissions(request):
    """
    Add permission helper functions to template context.

    Usage in templates:
        {% if perms.has_role.ADMIN %}
            Admin content here
        {% endif %}

        {% if perms.has_permission.workorders_create %}
            <a href="{% url 'workorders:create' %}">Create Work Order</a>
        {% endif %}
    """
    if not request.user.is_authenticated:
        return {
            'perms': PermissionChecker(None),
            'user_roles': [],
            'user_permissions': [],
        }

    return {
        'perms': PermissionChecker(request.user),
        'user_roles': request.user.role_codes if hasattr(request.user, 'role_codes') else [],
        'user_permissions': request.user.get_permissions() if hasattr(request.user, 'get_permissions') else [],
    }


class PermissionChecker:
    """
    Helper class for checking permissions in templates.
    """

    def __init__(self, user):
        self.user = user
        self.has_role = RoleChecker(user)
        self.has_permission = PermChecker(user)

    def __bool__(self):
        return self.user is not None and self.user.is_authenticated


class RoleChecker:
    """
    Check if user has a specific role.

    Usage: perms.has_role.ADMIN
    """

    def __init__(self, user):
        self.user = user
        self._cache = {}

    def __getattr__(self, role_code):
        if role_code.startswith('_'):
            raise AttributeError(role_code)

        if role_code not in self._cache:
            if self.user is None or not self.user.is_authenticated:
                self._cache[role_code] = False
            elif self.user.is_superuser:
                self._cache[role_code] = True
            else:
                self._cache[role_code] = self.user.has_role(role_code)

        return self._cache[role_code]


class PermChecker:
    """
    Check if user has a specific permission.

    Usage: perms.has_permission.workorders_create
    (Note: use underscore instead of dot in template)
    """

    def __init__(self, user):
        self.user = user
        self._cache = {}

    def __getattr__(self, perm_code):
        if perm_code.startswith('_'):
            raise AttributeError(perm_code)

        # Convert underscore to dot for permission lookup
        actual_perm = perm_code.replace('_', '.', 1)

        if actual_perm not in self._cache:
            if self.user is None or not self.user.is_authenticated:
                self._cache[actual_perm] = False
            elif self.user.is_superuser:
                self._cache[actual_perm] = True
            else:
                self._cache[actual_perm] = self.user.has_permission(actual_perm)

        return self._cache[actual_perm]
