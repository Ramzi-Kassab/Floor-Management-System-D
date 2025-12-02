"""
ARDT FMS - Work Orders URLs
Version: 5.4 - Sprint 1.5
"""

from django.urls import path

from . import views

app_name = "workorders"

urlpatterns = [
    # Work Order - List and CRUD
    path("", views.WorkOrderListView.as_view(), name="list"),
    path("create/", views.WorkOrderCreateView.as_view(), name="create"),
    path("<int:pk>/", views.WorkOrderDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.WorkOrderUpdateView.as_view(), name="update"),
    # Work Order - Actions
    path("<int:pk>/start/", views.start_work_view, name="start"),
    path("<int:pk>/complete/", views.complete_work_view, name="complete"),
    # Work Order - HTMX endpoints
    path("<int:pk>/status/", views.update_status_htmx, name="status_htmx"),
    path("<int:pk>/row/", views.workorder_row_htmx, name="row_htmx"),
    # Exports
    path("export/csv/", views.export_work_orders_csv, name="export_csv"),
    # Drill Bits
    path("drill-bits/", views.DrillBitListView.as_view(), name="drillbit_list"),
    path("drill-bits/register/", views.DrillBitCreateView.as_view(), name="drillbit_create"),
    path("drill-bits/<int:pk>/", views.DrillBitDetailView.as_view(), name="drillbit_detail"),
    path("drill-bits/<int:pk>/edit/", views.DrillBitUpdateView.as_view(), name="drillbit_update"),
    path("drill-bits/<int:pk>/qr/", views.drillbit_qr_view, name="drillbit_qr"),
    path("drill-bits/export/csv/", views.export_drill_bits_csv, name="drillbit_export_csv"),
    # Alias for template compatibility (workorder_detail -> detail, workorder_edit -> update)
    path("workorder/<int:pk>/", views.WorkOrderDetailView.as_view(), name="workorder_detail"),
    path("workorder/<int:pk>/edit/", views.WorkOrderUpdateView.as_view(), name="workorder_edit"),
]
