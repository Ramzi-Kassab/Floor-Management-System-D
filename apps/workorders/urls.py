"""
ARDT FMS - Work Orders URLs
Version: 6.0 - Job Card Enhancement
"""

from django.urls import path

from . import views
from . import views_jobcard
from . import views_drillbit

app_name = "workorders"

urlpatterns = [
    # ========================================================================
    # JOB CARD ENHANCED VIEWS
    # ========================================================================
    # Dashboard
    path("dashboard/", views_jobcard.WorkOrderDashboardView.as_view(), name="dashboard"),

    # Enhanced Work Order List & Detail
    path("enhanced/", views_jobcard.WorkOrderListEnhancedView.as_view(), name="workorder_list_enhanced"),
    path("enhanced/<int:pk>/", views_jobcard.WorkOrderDetailEnhancedView.as_view(), name="workorder_detail_enhanced"),
    path("export/excel/", views_jobcard.export_work_orders_excel, name="export_excel"),

    # Enhanced Drill Bit List & Detail
    path("drill-bits/enhanced/", views_jobcard.DrillBitListEnhancedView.as_view(), name="drillbit_list_enhanced"),
    path("drill-bits/enhanced/<int:pk>/", views_jobcard.DrillBitDetailEnhancedView.as_view(), name="drillbit_detail_enhanced"),
    # Alias: drillbit_list -> drillbit_list_enhanced (for backward compatibility)
    path("drill-bits/", views_jobcard.DrillBitListEnhancedView.as_view(), name="drillbit_list"),

    # ========================================================================
    # DRILL BIT INVENTORY VIEWS
    # ========================================================================
    # Dashboard
    path("drill-bits/inventory/", views_drillbit.DrillBitInventoryDashboardView.as_view(), name="drillbit_inventory_dashboard"),

    # Drill Bit CRUD (new enhanced versions)
    path("drill-bits/new/", views_drillbit.DrillBitCreateView.as_view(), name="drillbit_create"),
    path("drill-bits/<int:pk>/first-event/", views_drillbit.DrillBitFirstEventView.as_view(), name="drillbit_first_event"),
    path("drill-bits/<int:pk>/detail/", views_jobcard.DrillBitDetailEnhancedView.as_view(), name="drillbit_detail"),
    path("drill-bits/<int:pk>/edit/", views_drillbit.DrillBitUpdateView.as_view(), name="drillbit_edit"),
    path("drill-bits/<int:pk>/update/", views_drillbit.DrillBitUpdateView.as_view(), name="drillbit_update"),  # Alias for templates
    path("drill-bits/<int:pk>/delete/", views_drillbit.DrillBitDeleteView.as_view(), name="drillbit_delete"),

    # Drill Bit Actions
    path("drill-bits/<int:pk>/receive/", views_drillbit.DrillBitReceiveView.as_view(), name="drillbit_receive"),
    path("drill-bits/<int:pk>/ship/", views_drillbit.DrillBitShipView.as_view(), name="drillbit_ship"),
    path("drill-bits/<int:pk>/transfer/", views_drillbit.DrillBitTransferView.as_view(), name="drillbit_transfer"),
    path("drill-bits/<int:pk>/return/", views_drillbit.DrillBitReturnView.as_view(), name="drillbit_return"),
    path("drill-bits/<int:pk>/scrap/", views_drillbit.DrillBitScrapView.as_view(), name="drillbit_scrap"),
    path("drill-bits/<int:pk>/start-repair/", views_drillbit.DrillBitStartRepairView.as_view(), name="drillbit_start_repair"),

    # Excel Export
    path("drill-bits/export/excel/", views_drillbit.DrillBitExportExcelView.as_view(), name="drillbit_export_excel"),

    # Bit Events
    path("bit-events/", views_drillbit.BitEventListView.as_view(), name="bitevent_list"),

    # Locations
    path("locations/", views_drillbit.LocationListView.as_view(), name="location_list"),
    path("locations/create/", views_drillbit.LocationCreateView.as_view(), name="location_create"),
    path("locations/<int:pk>/edit/", views_drillbit.LocationUpdateView.as_view(), name="location_edit"),
    path("locations/<int:pk>/delete/", views_drillbit.LocationDeleteView.as_view(), name="location_delete"),

    # API endpoints
    path("api/drill-bits/search/", views_drillbit.DrillBitSearchAPIView.as_view(), name="drillbit_search_api"),
    path("api/drill-bits/lookup/", views.api_drillbit_lookup, name="drillbit_lookup_api"),
    path("api/drill-bits/<int:pk>/quick-event/", views_drillbit.DrillBitQuickEventAPIView.as_view(), name="drillbit_quick_event_api"),

    # Cutter Evaluation Matrix
    path("<int:wo_pk>/cutter-evaluation/create/", views_jobcard.CutterEvaluationCreateView.as_view(), name="cutter_evaluation_create"),
    path("<int:wo_pk>/cutter-evaluation/<int:pk>/", views_jobcard.CutterEvaluationEditView.as_view(), name="cutter_evaluation_edit"),

    # Router Sheet
    path("<int:pk>/router-sheet/", views_jobcard.RouterSheetView.as_view(), name="router_sheet"),
    path("<int:wo_pk>/router-sheet/<int:step_number>/scan/", views_jobcard.router_step_scan, name="router_step_scan"),
    path("<int:wo_pk>/router-sheet/<int:step_number>/api-scan/", views_jobcard.api_router_step_scan, name="api_router_step_scan"),

    # QC Forms
    path("<int:wo_pk>/e-checklist/", views_jobcard.EvaluationChecklistView.as_view(), name="e_checklist"),
    path("<int:wo_pk>/lpt-report/create/", views_jobcard.LPTReportCreateView.as_view(), name="lpt_report_create"),
    path("<int:wo_pk>/api-thread/create/", views_jobcard.APIThreadInspectionCreateView.as_view(), name="api_thread_create"),

    # Instruction Rules
    path("instruction-rules/", views_jobcard.InstructionRuleListView.as_view(), name="instruction_rule_list"),
    path("instruction-rules/create/", views_jobcard.InstructionRuleCreateView.as_view(), name="instruction_rule_create"),
    path("instruction-rules/<int:pk>/edit/", views_jobcard.InstructionRuleUpdateView.as_view(), name="instruction_rule_update"),
    path("instruction-rules/<int:pk>/delete/", views_jobcard.InstructionRuleDeleteView.as_view(), name="instruction_rule_delete"),

    # ========================================================================
    # WORK ORDER VIEWS (Consolidated)
    # ========================================================================
    # Work Order - List (redirects to enhanced view for backward compatibility)
    path("", views_jobcard.WorkOrderListEnhancedView.as_view(), name="list"),
    path("create/", views.WorkOrderCreateView.as_view(), name="create"),
    path("<int:pk>/", views_jobcard.WorkOrderDetailEnhancedView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.WorkOrderUpdateView.as_view(), name="update"),
    # Work Order - Actions
    path("<int:pk>/start/", views.start_work_view, name="start"),
    path("<int:pk>/complete/", views.complete_work_view, name="complete"),
    # Work Order - HTMX endpoints
    path("<int:pk>/status/", views.update_status_htmx, name="status_htmx"),
    path("<int:pk>/row/", views.workorder_row_htmx, name="row_htmx"),
    # Exports
    path("export/csv/", views.export_work_orders_csv, name="export_csv"),
    # Drill Bits (Legacy views - kept for backward compatibility)
    # NOTE: Use enhanced views instead: drillbit_list_enhanced, drillbit_create, drillbit_detail
    path("drill-bits/legacy/", views.DrillBitListView.as_view(), name="drillbit_list_legacy"),
    path("drill-bits/register/", views.DrillBitCreateView.as_view(), name="drillbit_register_legacy"),
    path("drill-bits/<int:pk>/legacy/", views.DrillBitDetailView.as_view(), name="drillbit_detail_legacy"),
    path("drill-bits/<int:pk>/edit-legacy/", views.DrillBitUpdateView.as_view(), name="drillbit_update_legacy"),
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
