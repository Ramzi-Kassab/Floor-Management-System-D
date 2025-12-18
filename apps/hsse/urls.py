"""
ARDT FMS - HSSE URLs
Version: 5.4

URL patterns for HSSE management.
"""

from django.urls import path
from . import views

app_name = "hsse"

urlpatterns = [
    # Dashboard
    path('', views.HSSEDashboardView.as_view(), name='dashboard'),

    # HOC Reports
    path('hoc/', views.HOCReportListView.as_view(), name='hoc-list'),
    path('hoc/<int:pk>/', views.HOCReportDetailView.as_view(), name='hoc-detail'),
    path('hoc/create/', views.HOCReportCreateView.as_view(), name='hoc-create'),
    path('hoc/<int:pk>/edit/', views.HOCReportUpdateView.as_view(), name='hoc-update'),
    path('hoc/<int:pk>/delete/', views.HOCReportDeleteView.as_view(), name='hoc-delete'),

    # Incidents
    path('incidents/', views.IncidentListView.as_view(), name='incident-list'),
    path('incidents/<int:pk>/', views.IncidentDetailView.as_view(), name='incident-detail'),
    path('incidents/create/', views.IncidentCreateView.as_view(), name='incident-create'),
    path('incidents/<int:pk>/edit/', views.IncidentUpdateView.as_view(), name='incident-update'),
    path('incidents/<int:pk>/delete/', views.IncidentDeleteView.as_view(), name='incident-delete'),

    # Journeys
    path('journeys/', views.JourneyListView.as_view(), name='journey-list'),
    path('journeys/<int:pk>/', views.JourneyDetailView.as_view(), name='journey-detail'),
    path('journeys/create/', views.JourneyCreateView.as_view(), name='journey-create'),
    path('journeys/<int:pk>/edit/', views.JourneyUpdateView.as_view(), name='journey-update'),
    path('journeys/<int:pk>/delete/', views.JourneyDeleteView.as_view(), name='journey-delete'),
    path('journeys/<int:pk>/approve/', views.JourneyApproveView.as_view(), name='journey-approve'),
    path('journeys/<int:pk>/start/', views.JourneyStartView.as_view(), name='journey-start'),
    path('journeys/<int:pk>/complete/', views.JourneyCompleteView.as_view(), name='journey-complete'),
]
