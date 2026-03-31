"""
REPLACE apps/accounts/urls.py with this file entirely.
"""

from django.urls import path
from . import views
from . import views_users

app_name = "accounts"

urlpatterns = [
    # ── Authentication ────────────────────────────────────────────────
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),

    # ── Profile & Settings ────────────────────────────────────────────
    path("profile/", views.profile_view, name="profile"),
    path("settings/", views.settings_view, name="settings"),

    # ── Password ──────────────────────────────────────────────────────
    path("password-change/", views.CustomPasswordChangeView.as_view(), name="password_change"),
    path("password-change/done/", views.CustomPasswordChangeDoneView.as_view(), name="password_change_done"),
    path("password-reset/", views.CustomPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", views.CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", views.CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset/complete/", views.CustomPasswordResetCompleteView.as_view(), name="password_reset_complete"),

    # ── User Management ───────────────────────────────────────────────
    path("users/", views_users.UserListView.as_view(), name="user-list"),
    path("users/create/", views_users.UserCreateView.as_view(), name="user-create"),
    path("users/<int:pk>/", views_users.UserDetailView.as_view(), name="user-detail"),
    path("users/<int:pk>/edit/", views_users.UserUpdateView.as_view(), name="user-update"),
    path("users/<int:pk>/delete/", views_users.UserDeleteView.as_view(), name="user-delete"),
    path("users/<int:pk>/roles/", views_users.UserRoleManageView.as_view(), name="user-roles"),
    path("users/<int:pk>/reset-password/", views_users.UserResetPasswordView.as_view(), name="user-reset-password"),

    # ── Role Management ───────────────────────────────────────────────
    path("roles/", views_users.RoleListView.as_view(), name="role-list"),
    path("roles/create/", views_users.RoleCreateView.as_view(), name="role-create"),
    path("roles/<int:pk>/", views_users.RoleDetailView.as_view(), name="role-detail"),
    path("roles/<int:pk>/edit/", views_users.RoleUpdateView.as_view(), name="role-update"),
    path("roles/<int:pk>/delete/", views_users.RoleDeleteView.as_view(), name="role-delete"),

    # ── Permission Management ─────────────────────────────────────────
    path("permissions/", views_users.PermissionListView.as_view(), name="permission-list"),
    path("permissions/create/", views_users.PermissionCreateView.as_view(), name="permission-create"),
    path("permissions/<int:pk>/edit/", views_users.PermissionUpdateView.as_view(), name="permission-update"),
    path("permissions/<int:pk>/delete/", views_users.PermissionDeleteView.as_view(), name="permission-delete"),
]
