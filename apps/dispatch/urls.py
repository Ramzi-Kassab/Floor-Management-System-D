"""
ARDT FMS - Dispatch URLs
Version: 5.4

URL patterns for dispatch management.
"""

from django.urls import path
from . import views

app_name = "dispatch"

urlpatterns = [
    # Dashboard
    path('', views.DispatchDashboardView.as_view(), name='dashboard'),

    # Vehicle Management
    path('vehicles/', views.VehicleListView.as_view(), name='vehicle-list'),
    path('vehicles/<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle-detail'),
    path('vehicles/create/', views.VehicleCreateView.as_view(), name='vehicle-create'),
    path('vehicles/<int:pk>/edit/', views.VehicleUpdateView.as_view(), name='vehicle-update'),
    path('vehicles/<int:pk>/delete/', views.VehicleDeleteView.as_view(), name='vehicle-delete'),

    # Dispatch Management
    path('dispatches/', views.DispatchListView.as_view(), name='dispatch-list'),
    path('dispatches/<int:pk>/', views.DispatchDetailView.as_view(), name='dispatch-detail'),
    path('dispatches/create/', views.DispatchCreateView.as_view(), name='dispatch-create'),
    path('dispatches/<int:pk>/edit/', views.DispatchUpdateView.as_view(), name='dispatch-update'),
    path('dispatches/<int:pk>/delete/', views.DispatchDeleteView.as_view(), name='dispatch-delete'),
    path('dispatches/<int:pk>/status/', views.DispatchStatusUpdateView.as_view(), name='dispatch-status'),

    # Inventory Reservations
    path('reservations/', views.ReservationListView.as_view(), name='reservation-list'),
    path('reservations/create/', views.ReservationCreateView.as_view(), name='reservation-create'),
    path('reservations/<int:pk>/edit/', views.ReservationUpdateView.as_view(), name='reservation-update'),
]
