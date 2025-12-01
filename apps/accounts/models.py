"""
ARDT FMS - Accounts Models
Version: 5.4

Tables:
- users (P1) - Custom User model
- roles (P1)
- permissions (P1)
- role_permissions (P1)
- user_roles (P1)
- user_preferences (P1)
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager."""
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """Create and save a regular User."""
        if not username:
            raise ValueError('Users must have a username')
        
        email = self.normalize_email(email) if email else None
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Create and save a SuperUser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    🟢 P1: Custom User model with additional fields.
    
    Extends Django's AbstractUser to add employee_id, department,
    position, and other ARDT-specific fields.
    """
    
    # Override email to make it optional but unique when provided
    email = models.EmailField(_('email address'), blank=True, null=True, unique=True)
    
    # Employee Information
    employee_id = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True,
        help_text='HR Employee ID'
    )
    department = models.ForeignKey(
        'organization.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    position = models.ForeignKey(
        'organization.Position',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    
    # Contact Information
    phone = models.CharField(max_length=20, blank=True)
    phone_extension = models.CharField(max_length=10, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    
    # Profile
    profile_photo = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True
    )
    signature = models.ImageField(
        upload_to='signatures/',
        null=True,
        blank=True,
        help_text='Digital signature for approvals'
    )
    
    # Localization
    language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='Asia/Riyadh')
    
    # Theme
    theme = models.ForeignKey(
        'organization.Theme',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    # Relationships
    roles = models.ManyToManyField(
        'Role',
        through='UserRole',
        related_name='users'
    )
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username}"
    
    @property
    def display_name(self):
        """Get display name (full name or username)."""
        return self.get_full_name() or self.username
    
    @property
    def role_codes(self):
        """Get list of role codes for this user."""
        return list(self.roles.values_list('code', flat=True))
    
    def has_role(self, role_code):
        """Check if user has a specific role."""
        return role_code in self.role_codes
    
    def has_any_role(self, role_codes):
        """Check if user has any of the specified roles."""
        return any(code in self.role_codes for code in role_codes)
    
    def has_all_roles(self, role_codes):
        """Check if user has all of the specified roles."""
        return all(code in self.role_codes for code in role_codes)
    
    def get_permissions(self):
        """Get all permission codes for this user."""
        return list(
            Permission.objects.filter(
                roles__in=self.roles.all()
            ).values_list('code', flat=True).distinct()
        )
    
    def has_permission(self, permission_code):
        """Check if user has a specific permission."""
        if self.is_superuser:
            return True
        return permission_code in self.get_permissions()


class Role(models.Model):
    """
    🟢 P1: User roles for authorization.
    
    Roles define what users can do in the system.
    """
    
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(
        default=False,
        help_text='System roles cannot be deleted'
    )
    is_active = models.BooleanField(default=True)
    
    # Hierarchy
    level = models.IntegerField(
        default=1,
        help_text='Role hierarchy level (higher = more authority)'
    )
    
    # Permissions
    permissions = models.ManyToManyField(
        'Permission',
        through='RolePermission',
        related_name='roles'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'roles'
        ordering = ['-level', 'name']
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Permission(models.Model):
    """
    🟢 P1: Granular permissions for authorization.
    """
    
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    module = models.CharField(
        max_length=50,
        help_text='Module this permission belongs to'
    )
    
    class Meta:
        db_table = 'permissions'
        ordering = ['module', 'code']
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
    
    def __str__(self):
        return f"{self.module}.{self.code}"


class RolePermission(models.Model):
    """
    🟢 P1: Many-to-many relationship between roles and permissions.
    """
    
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_role_permissions'
    )
    
    class Meta:
        db_table = 'role_permissions'
        unique_together = ['role', 'permission']
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'


class UserRole(models.Model):
    """
    🟢 P1: Many-to-many relationship between users and roles.
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_user_roles'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Temporary role assignment'
    )
    is_primary = models.BooleanField(
        default=False,
        help_text='Primary role for display purposes'
    )
    
    class Meta:
        db_table = 'user_roles'
        unique_together = ['user', 'role']
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'


class UserPreference(models.Model):
    """
    🟢 P1: User-specific preferences and settings.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    
    # Dashboard
    default_dashboard = models.CharField(max_length=50, default='main')
    dashboard_widgets = models.JSONField(
        default=dict,
        help_text='Widget configuration'
    )
    
    # Notifications
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    notification_sound = models.BooleanField(default=True)
    
    # Display
    items_per_page = models.IntegerField(default=25)
    date_format = models.CharField(max_length=20, default='DD/MM/YYYY')
    time_format = models.CharField(max_length=20, default='HH:mm')
    
    # Sidebar
    sidebar_collapsed = models.BooleanField(default=False)
    favorite_modules = models.JSONField(
        default=list,
        help_text='List of pinned module codes'
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'
        verbose_name = 'User Preference'
        verbose_name_plural = 'User Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user}"
