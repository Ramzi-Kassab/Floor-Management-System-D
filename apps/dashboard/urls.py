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
    # Dashboard Customization - specific paths MUST come before generic <str:dashboard_type>
    path("customize/", views.customize_dashboard, name="customize"),
    path("customize/save/", views.save_widget_order, name="save_widget_order"),
    path("customize/toggle/<str:widget_id>/", views.toggle_widget, name="toggle_widget"),
    path("customize/reset/", views.reset_dashboard, name="reset_dashboard"),
    # Dashboard type-specific customization paths (must come after specific paths above)
    path("customize/<str:dashboard_type>/", views.customize_dashboard, name="customize_type"),
    path("customize/<str:dashboard_type>/save/", views.save_widget_order, name="save_widget_order_type"),
    path("customize/<str:dashboard_type>/reset/", views.reset_dashboard, name="reset_dashboard_type"),
    # Saved Dashboards
    path("saved/", views.saved_dashboard_list, name="saved_list"),
    path("saved/create/", views.saved_dashboard_create, name="saved_create"),
    path("saved/<int:pk>/", views.saved_dashboard_view, name="saved_view"),
    path("saved/<int:pk>/edit/", views.saved_dashboard_edit, name="saved_edit"),
    path("saved/<int:pk>/delete/", views.saved_dashboard_delete, name="saved_delete"),
    path("saved/<int:pk>/favorite/", views.toggle_dashboard_favorite, name="toggle_favorite"),
    path("save-as/", views.save_as_dashboard, name="save_as"),
    # Legacy support
    path("index/", views.index, name="index"),
]
