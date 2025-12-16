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
    # ========================================================================
    # SPRINT 4 URLs - Additional Models
    # ========================================================================
    # SalvageItem URLs (5 patterns)
    path("salvage/", views.SalvageItemListView.as_view(), name="salvageitem_list"),
    path("salvage/<int:pk>/", views.SalvageItemDetailView.as_view(), name="salvageitem_detail"),
    path("salvage/create/", views.SalvageItemCreateView.as_view(), name="salvageitem_create"),
    path("salvage/<int:pk>/edit/", views.SalvageItemUpdateView.as_view(), name="salvageitem_update"),
    path("salvage/<int:pk>/delete/", views.SalvageItemDeleteView.as_view(), name="salvageitem_delete"),
    # RepairApprovalAuthority URLs (5 patterns)
    path("approval-authorities/", views.RepairApprovalAuthorityListView.as_view(), name="repairapprovalauthority_list"),
    path("approval-authorities/<int:pk>/", views.RepairApprovalAuthorityDetailView.as_view(), name="repairapprovalauthority_detail"),
    path("approval-authorities/create/", views.RepairApprovalAuthorityCreateView.as_view(), name="repairapprovalauthority_create"),
    path("approval-authorities/<int:pk>/edit/", views.RepairApprovalAuthorityUpdateView.as_view(), name="repairapprovalauthority_update"),
    path("approval-authorities/<int:pk>/delete/", views.RepairApprovalAuthorityDeleteView.as_view(), name="repairapprovalauthority_delete"),
    # RepairEvaluation URLs (5 patterns)
    path("repair-evaluations/", views.RepairEvaluationListView.as_view(), name="repairevaluation_list"),
    path("repair-evaluations/<int:pk>/", views.RepairEvaluationDetailView.as_view(), name="repairevaluation_detail"),
    path("repair-evaluations/create/", views.RepairEvaluationCreateView.as_view(), name="repairevaluation_create"),
    path("repair-evaluations/<int:pk>/edit/", views.RepairEvaluationUpdateView.as_view(), name="repairevaluation_update"),
    path("repair-evaluations/<int:pk>/delete/", views.RepairEvaluationDeleteView.as_view(), name="repairevaluation_delete"),
    # RepairBOM URLs (5 patterns)
    path("repair-bom/", views.RepairBOMListView.as_view(), name="repairbom_list"),
    path("repair-bom/<int:pk>/", views.RepairBOMDetailView.as_view(), name="repairbom_detail"),
    path("repair-bom/create/", views.RepairBOMCreateView.as_view(), name="repairbom_create"),
    path("repair-bom/<int:pk>/edit/", views.RepairBOMUpdateView.as_view(), name="repairbom_update"),
    path("repair-bom/<int:pk>/delete/", views.RepairBOMDeleteView.as_view(), name="repairbom_delete"),
    # ProcessRoute URLs (5 patterns)
    path("process-routes/", views.ProcessRouteListView.as_view(), name="processroute_list"),
    path("process-routes/<int:pk>/", views.ProcessRouteDetailView.as_view(), name="processroute_detail"),
    path("process-routes/create/", views.ProcessRouteCreateView.as_view(), name="processroute_create"),
    path("process-routes/<int:pk>/edit/", views.ProcessRouteUpdateView.as_view(), name="processroute_update"),
    path("process-routes/<int:pk>/delete/", views.ProcessRouteDeleteView.as_view(), name="processroute_delete"),
    # WorkOrderCost URLs (5 patterns)
    path("costs/", views.WorkOrderCostListView.as_view(), name="workordercost_list"),
    path("costs/<int:pk>/", views.WorkOrderCostDetailView.as_view(), name="workordercost_detail"),
    path("costs/create/", views.WorkOrderCostCreateView.as_view(), name="workordercost_create"),
    path("costs/<int:pk>/edit/", views.WorkOrderCostUpdateView.as_view(), name="workordercost_update"),
    path("costs/<int:pk>/delete/", views.WorkOrderCostDeleteView.as_view(), name="workordercost_delete"),
    # View-Only URLs (3 patterns)
    path("status-logs/", views.StatusTransitionLogListView.as_view(), name="statustransitionlog_list"),
    path("repair-history/", views.BitRepairHistoryListView.as_view(), name="bitrepairhistory_list"),
    path("operation-executions/", views.OperationExecutionListView.as_view(), name="operationexecution_list"),
]
