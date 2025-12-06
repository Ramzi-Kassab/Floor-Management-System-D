"""
ARDT FMS - Organization URLs
Version: 5.4

URL patterns for organization management.
"""

from django.urls import path
from . import views

app_name = "organization"

urlpatterns = [
    # Department Management
    path('departments/', views.DepartmentListView.as_view(), name='department-list'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),
    path('departments/create/', views.DepartmentCreateView.as_view(), name='department-create'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department-update'),
    path('departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department-delete'),

    # Position Management
    path('positions/', views.PositionListView.as_view(), name='position-list'),
    path('positions/<int:pk>/', views.PositionDetailView.as_view(), name='position-detail'),
    path('positions/create/', views.PositionCreateView.as_view(), name='position-create'),
    path('positions/<int:pk>/edit/', views.PositionUpdateView.as_view(), name='position-update'),
    path('positions/<int:pk>/delete/', views.PositionDeleteView.as_view(), name='position-delete'),

    # Theme Management
    path('themes/', views.ThemeListView.as_view(), name='theme-list'),
    path('themes/<int:pk>/', views.ThemeDetailView.as_view(), name='theme-detail'),
    path('themes/create/', views.ThemeCreateView.as_view(), name='theme-create'),
    path('themes/<int:pk>/edit/', views.ThemeUpdateView.as_view(), name='theme-update'),
    path('themes/<int:pk>/delete/', views.ThemeDeleteView.as_view(), name='theme-delete'),
    path('themes/<int:pk>/set-default/', views.ThemeSetDefaultView.as_view(), name='theme-set-default'),

    # System Settings
    path('settings/', views.SystemSettingListView.as_view(), name='setting-list'),
    path('settings/create/', views.SystemSettingCreateView.as_view(), name='setting-create'),
    path('settings/<int:pk>/edit/', views.SystemSettingUpdateView.as_view(), name='setting-update'),

    # Number Sequences
    path('sequences/', views.NumberSequenceListView.as_view(), name='sequence-list'),
    path('sequences/create/', views.NumberSequenceCreateView.as_view(), name='sequence-create'),
    path('sequences/<int:pk>/edit/', views.NumberSequenceUpdateView.as_view(), name='sequence-update'),
    path('sequences/<int:pk>/delete/', views.NumberSequenceDeleteView.as_view(), name='sequence-delete'),
]
