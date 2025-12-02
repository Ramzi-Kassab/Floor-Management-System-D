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
    # Legacy support
    path("index/", views.index, name="index"),
]
