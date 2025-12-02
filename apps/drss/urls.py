"""
ARDT FMS - DRSS URLs
Version: 5.4 - Sprint 2

URL patterns for DRSS request management.
"""

from django.urls import path
from . import views

app_name = 'drss'

urlpatterns = [
    # ==========================================================================
    # DRSS REQUEST URLS
    # ==========================================================================
    path('', views.DRSSListView.as_view(), name='drss_list'),
    path('create/', views.DRSSCreateView.as_view(), name='drss_create'),
    path('<int:pk>/', views.DRSSDetailView.as_view(), name='drss_detail'),
    path('<int:pk>/edit/', views.DRSSUpdateView.as_view(), name='drss_update'),
    path('<int:pk>/status/', views.update_status, name='update_status'),
    path('export/', views.export_csv, name='drss_export'),

    # ==========================================================================
    # DRSS LINE URLS
    # ==========================================================================
    path('<int:drss_pk>/lines/add/', views.add_line, name='line_add'),
    path('lines/<int:pk>/evaluate/', views.evaluate_line, name='line_evaluate'),
    path('lines/<int:pk>/delete/', views.delete_line, name='line_delete'),
]
