"""
ARDT FMS - Dashboard URLs
Version: 5.4 - Sprint 1
"""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    # Home - redirects based on role
    path("", views.home_view, name="home"),
    # Role-specific dashboards
    path("main/", views.main_dashboard, name="main"),
    path("manager/", views.manager_dashboard, name="manager"),
    path("planner/", views.planner_dashboard, name="planner"),
    path("technician/", views.technician_dashboard, name="technician"),
    path("qc/", views.qc_dashboard, name="qc"),
    # Dashboard Customization
    path("customize/", views.customize_dashboard, name="customize"),
    path("customize/save/", views.save_widget_order, name="save_widget_order"),
    path("customize/toggle/<str:widget_id>/", views.toggle_widget, name="toggle_widget"),
    path("customize/reset/", views.reset_dashboard, name="reset_dashboard"),
    # Legacy support
    path("index/", views.index, name="index"),
]
