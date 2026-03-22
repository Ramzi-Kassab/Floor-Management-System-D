"""
ARDT FMS - Work Orders URLs
Version: 6.0 - Job Card Enhancement
"""

from django.urls import path
from django.views.generic import RedirectView

from . import views
from . import views_jobcard
from . import views_drillbit
from . import views_photos
from . import views_receiving

app_name = "workorders"

urlpatterns = [
    # ========================================================================
    # RECEIVING DOCK
    # ========================================================================
    path("receiving/", views_receiving.ReceivingDockDashboardView.as_view(), name="receiving_dashboard"),
    path("receiving/batches/", views_receiving.BackloadBatchListView.as_view(), name="backload_batch_list"),
    path("receiving/batches/create/", views_receiving.BackloadBatchCreateView.as_view(), name="backload_batch_create"),
    path("receiving/batches/<int:pk>/", views_receiving.BackloadBatchDetailView.as_view(), name="backload_batch_detail"),
    # NOTE: confirm-item, confirm-all, register-new removed (Feb 2026) — auto-processed on batch creation
    path("receiving/batches/<int:pk>/rematch/", views_receiving.api_batch_rematch, name="api_batch_rematch"),
    path("receiving/batches/<int:pk>/remove-item/", views_receiving.api_batch_remove_item, name="api_batch_remove_item"),
    path("receiving/batches/<int:pk>/add-items/", views_receiving.api_batch_add_items, name="api_batch_add_items"),
    path("receiving/batches/<int:pk>/edit-serial/", views_receiving.api_batch_edit_serial, name="api_batch_edit_serial"),
    path("receiving/batches/<int:pk>/replace-serial/", views_receiving.api_batch_replace_serial, name="api_batch_replace_serial"),
    path("receiving/batches/<int:pk>/upload-attachment/", views_receiving.api_batch_upload_attachment, name="api_batch_upload_attachment"),
    path("receiving/batches/<int:pk>/delete-attachment/<int:att_pk>/", views_receiving.api_batch_delete_attachment, name="api_batch_delete_attachment"),
    path("receiving/inspections/", views_receiving.ReceivingInspectionListView.as_view(), name="receiving_inspection_list"),
    path("receiving/bom-pending/", views_receiving.BOMPendingListView.as_view(), name="bom_pending_list"),
    path("receiving/api/bom-request/", views_receiving.api_create_bom_request, name="api_create_bom_request"),
    path("receiving/api/bom-request/<int:pk>/resolve/", views_receiving.api_resolve_bom_request, name="api_resolve_bom_request"),

    # ========================================================================
    # JOB CARD ENHANCED VIEWS
    # ========================================================================
    # Dashboard
    path("dashboard/", views_jobcard.WorkOrderDashboardView.as_view(), name="dashboard"),

    # Production Planner (WIP Dashboard)
    path("production-planner/", views_jobcard.ProductionPlannerView.as_view(), name="production_planner"),
    path("production-planner/create-wo/", views_jobcard.ProductionPlannerCreateWOView.as_view(), name="production_planner_create_wo"),
    path("production-planner/settings/", views_jobcard.PlannerSettingsView.as_view(), name="planner_settings"),
    path("api/production-wip-status/", views_jobcard.api_production_wip_status, name="api_production_wip_status"),
    # Production Plan API
    path("api/add-to-plan/", views_jobcard.api_add_to_plan, name="api_add_to_plan"),
    path("api/create-wo-from-plan/", views_jobcard.api_create_wo_from_plan, name="api_create_wo_from_plan"),
    path("api/release-plan-entry/", views_jobcard.api_release_plan_entry, name="api_release_plan_entry"),
    path("api/delete-wo/<int:pk>/", views_jobcard.api_delete_work_order, name="api_delete_wo"),
    path("api/delete-evaluation/<int:pk>/", views_jobcard.api_delete_evaluation, name="api_delete_evaluation"),
    path("api/restore-plan-entry/<int:bit_pk>/", views_jobcard.api_restore_plan_entry, name="api_restore_plan_entry"),
    path("api/remove-from-plan/", views_jobcard.api_remove_from_plan, name="api_remove_from_plan"),
    path("api/update-plan-due-date/", views_jobcard.api_update_plan_due_date, name="api_update_plan_due_date"),
    path("api/update-plan-entry/", views_jobcard.api_update_plan_entry, name="api_update_plan_entry"),
    path("api/bit-timeline/<int:bit_pk>/", views_jobcard.api_bit_timeline, name="api_bit_timeline"),
    path("api/update-plan-account/", views_jobcard.api_update_plan_account, name="api_update_plan_account"),
    path("api/update-bit-account/", views_jobcard.api_update_bit_account, name="api_update_bit_account"),
    path("api/assign-bit-bom/", views_jobcard.api_assign_bit_bom, name="api_assign_bit_bom"),
    path("api/transfer-bit-location/", views_jobcard.api_transfer_bit_location, name="api_transfer_bit_location"),
    path("api/delete-transfer/<int:pk>/", views_jobcard.api_delete_transfer, name="api_delete_transfer"),
    path("api/edit-transfer/<int:pk>/", views_jobcard.api_edit_transfer, name="api_edit_transfer"),
    path("api/locations/", views_jobcard.api_locations_list, name="api_locations_list"),
    path("api/change-wo-account/", views_jobcard.api_change_wo_account, name="api_change_wo_account"),
    # Planner Settings API
    path("api/holiday/add/", views_jobcard.api_add_holiday, name="api_add_holiday"),
    path("api/holiday/<int:pk>/delete/", views_jobcard.api_delete_holiday, name="api_delete_holiday"),
    path("api/holiday/<int:pk>/toggle/", views_jobcard.api_toggle_holiday, name="api_toggle_holiday"),
    path("api/preview-due-date/", views_jobcard.api_preview_due_date, name="api_preview_due_date"),

    # Location Transfers
    path("location-transfers/", views_jobcard.LocationTransferView.as_view(), name="location_transfers"),
    path("all-locations/", views_jobcard.AllLocationsView.as_view(), name="all_locations"),
    path("api/toggle-location/<int:pk>/", views_jobcard.api_toggle_location, name="api_toggle_location"),

    # Evaluation Route Builder
    path("evaluation-routes/", views_jobcard.EvaluationRouteBuilderView.as_view(), name="evaluation_route_builder"),
    path("evaluation-routes/<int:pk>/", views_jobcard.EvaluationRouteDetailView.as_view(), name="evaluation_route_detail"),
    # Evaluation Route API
    path("api/evaluation-routes/create/", views_jobcard.api_create_route, name="api_create_route"),
    path("api/evaluation-routes/<int:pk>/update/", views_jobcard.api_update_route, name="api_update_route"),
    path("api/evaluation-routes/<int:pk>/delete/", views_jobcard.api_delete_route, name="api_delete_route"),
    path("api/evaluation-routes/<int:pk>/", views_jobcard.api_get_route, name="api_get_route"),
    path("api/evaluation-routes/<int:pk>/steps/add/", views_jobcard.api_add_route_step, name="api_add_route_step"),
    path("api/evaluation-routes/<int:pk>/steps/<int:step_pk>/update/", views_jobcard.api_update_route_step, name="api_update_route_step"),
    path("api/evaluation-routes/<int:pk>/steps/<int:step_pk>/delete/", views_jobcard.api_delete_route_step, name="api_delete_route_step"),
    path("api/evaluation-routes/<int:pk>/steps/reorder/", views_jobcard.api_reorder_route_steps, name="api_reorder_route_steps"),
    path("api/evaluation-types/", views_jobcard.api_get_evaluation_types, name="api_get_evaluation_types"),

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

    # QR Labels (multi-size, supports ?bits=1,2,3)
    path("drill-bits/qr-labels/", views_drillbit.DrillBitQRLabelsView.as_view(), name="drillbit_qr_labels"),

    # Excel Export
    path("drill-bits/export/excel/", views_drillbit.DrillBitExportExcelView.as_view(), name="drillbit_export_excel"),

    # Bit Events
    path("bit-events/", views_drillbit.BitEventListView.as_view(), name="bitevent_list"),

    # Locations
    path("locations/", RedirectView.as_view(url='/work-orders/all-locations/', permanent=False), name="location_list"),
    path("locations/create/", views_drillbit.LocationCreateView.as_view(), name="location_create"),
    path("locations/<int:pk>/edit/", views_drillbit.LocationUpdateView.as_view(), name="location_edit"),
    path("locations/<int:pk>/delete/", views_drillbit.LocationDeleteView.as_view(), name="location_delete"),

    # API endpoints
    path("api/drill-bits/search/", views_drillbit.DrillBitSearchAPIView.as_view(), name="drillbit_search_api"),
    path("api/drill-bits/lookup/", views.api_drillbit_lookup, name="drillbit_lookup_api"),
    path("api/drill-bits/list/", views.api_drillbit_list, name="drillbit_list_api"),
    path("api/drill-bits/<int:pk>/quick-event/", views_drillbit.DrillBitQuickEventAPIView.as_view(), name="drillbit_quick_event_api"),

    # Cutter Evaluation Matrix
    path("<int:wo_pk>/cutter-evaluation/create/", views_jobcard.CutterEvaluationCreateView.as_view(), name="cutter_evaluation_create"),
    path("<int:wo_pk>/cutter-evaluation/<int:pk>/", views_jobcard.CutterEvaluationEditView.as_view(), name="cutter_evaluation_edit"),
    path("<int:wo_pk>/cutter-evaluation/<int:pk>/mark-complete/", views_jobcard.api_evaluation_mark_complete, name="cutter_evaluation_mark_complete"),

    # Pre-Repair Evaluation (PDC_EVAL — new page cloned from receiving inspection)
    path("<int:wo_pk>/pre-repair-eval/<int:pk>/", views_jobcard.PreRepairEvalEditView.as_view(), name="pre_repair_eval_edit"),

    # Standalone Test Pages (Die Check, LPT, API Thread)
    path("<int:wo_pk>/die-check/create/<int:eval_pk>/", views_jobcard.DieCheckReportView.as_view(), name="die_check_create"),
    path("<int:wo_pk>/die-check/<int:pk>/edit/<int:eval_pk>/", views_jobcard.DieCheckReportView.as_view(), name="die_check_edit"),
    path("<int:wo_pk>/lpt/create/<int:eval_pk>/", views_jobcard.StandaloneLPTReportView.as_view(), name="lpt_report_standalone_create"),
    path("<int:wo_pk>/lpt/<int:pk>/edit/<int:eval_pk>/", views_jobcard.StandaloneLPTReportView.as_view(), name="lpt_report_standalone_edit"),
    path("<int:wo_pk>/thread/create/<int:eval_pk>/", views_jobcard.StandaloneThreadReportView.as_view(), name="thread_report_create"),
    path("<int:wo_pk>/thread/<int:pk>/edit/<int:eval_pk>/", views_jobcard.StandaloneThreadReportView.as_view(), name="thread_report_edit"),

    # Evaluation Auto-Create (standalone per-type URL)
    path("<int:wo_pk>/evaluation/<str:type_code>/", views_jobcard.EvaluationAutoCreateView.as_view(), name="evaluation_auto"),

    # Receiving Inspection (linked to drill bit)
    path("drill-bits/<int:bit_pk>/receiving-inspection/create/", views_jobcard.ReceivingInspectionCreateView.as_view(), name="receiving_inspection_create"),
    path("drill-bits/<int:bit_pk>/receiving-inspection/<int:pk>/", views_jobcard.ReceivingInspectionEditView.as_view(), name="receiving_inspection_edit"),
    path("drill-bits/<int:bit_pk>/receiving-inspection/<int:pk>/mark-complete/", views_jobcard.api_receiving_inspection_complete, name="receiving_inspection_mark_complete"),
    path("drill-bits/<int:bit_pk>/receiving-inspection/<int:pk>/upload/", views_jobcard.api_receiving_inspection_upload, name="receiving_inspection_upload"),
    path("drill-bits/<int:bit_pk>/receiving-inspection/<int:pk>/attachment/<int:att_pk>/delete/", views_jobcard.api_receiving_inspection_delete_attachment, name="receiving_inspection_delete_attachment"),

    # Drill Bit Photos
    path("drill-bits/<int:bit_pk>/photos/", views_photos.api_photo_list, name="photo_list"),
    path("drill-bits/<int:bit_pk>/photos/upload/", views_photos.api_photo_upload, name="photo_upload"),
    path("drill-bits/<int:bit_pk>/photos/reorder/", views_photos.api_photo_reorder, name="photo_reorder"),
    path("drill-bits/<int:bit_pk>/photos/adg-sequence/", views_photos.api_adg_sequence, name="photo_adg_sequence"),
    path("drill-bits/<int:bit_pk>/photos/<int:photo_pk>/delete/", views_photos.api_photo_delete, name="photo_delete"),
    path("drill-bits/<int:bit_pk>/photos/<int:photo_pk>/rename/", views_photos.api_photo_rename, name="photo_rename"),
    path("drill-bits/<int:bit_pk>/photos/<int:photo_pk>/save-edit/", views_photos.api_photo_save_edit, name="photo_save_edit"),
    path("drill-bits/<int:bit_pk>/photos/<int:photo_pk>/discard-edit/", views_photos.api_photo_discard_edit, name="photo_discard_edit"),

    # Router Sheet
    path("<int:pk>/router-sheet/", views_jobcard.RouterSheetView.as_view(), name="router_sheet"),
    path("<int:wo_pk>/router-sheet/<int:step_number>/scan/", views_jobcard.router_step_scan, name="router_step_scan"),
    path("<int:wo_pk>/router-sheet/<int:step_number>/api-scan/", views_jobcard.api_router_step_scan, name="api_router_step_scan"),

    # Router Step Detail (operator work page)
    path("<int:wo_pk>/router/<int:step_number>/", views_jobcard.RouterStepDetailView.as_view(), name="router_step_detail"),
    path("<int:wo_pk>/router/api/save-data/<int:step_number>/", views_jobcard.api_step_save_data, name="api_step_save_data"),
    path("<int:wo_pk>/router/api/add-step/", views_jobcard.api_step_add, name="api_step_add"),
    path("<int:wo_pk>/router/api/skip/<int:step_number>/", views_jobcard.api_step_skip, name="api_step_skip"),
    path("<int:wo_pk>/router/api/pause/<int:step_number>/", views_jobcard.api_step_pause, name="api_step_pause"),

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
    # ProcessRoute URLs (5 patterns — legacy CRUD)
    path("process-routes/", views.ProcessRouteListView.as_view(), name="processroute_list"),
    path("process-routes/<int:pk>/", views.ProcessRouteDetailView.as_view(), name="processroute_detail"),
    path("process-routes/create/", views.ProcessRouteCreateView.as_view(), name="processroute_create"),
    path("process-routes/<int:pk>/edit/", views.ProcessRouteUpdateView.as_view(), name="processroute_update"),
    path("process-routes/<int:pk>/delete/", views.ProcessRouteDeleteView.as_view(), name="processroute_delete"),
    # Route Template Builder (inline editor)
    path("route-builder/<int:pk>/", views_jobcard.RouteBuilderView.as_view(), name="route_builder"),
    path("route-builder/create/", views_jobcard.RouteBuilderCreateView.as_view(), name="route_builder_create"),
    path("api/route/<int:pk>/save-header/", views_jobcard.api_route_save_header, name="api_route_save_header"),
    path("api/route/<int:pk>/operation/<int:op_pk>/save/", views_jobcard.api_route_save_operation, name="api_route_save_operation"),
    path("api/route/<int:pk>/operation/add/", views_jobcard.api_route_add_operation, name="api_route_add_operation"),
    path("api/route/<int:pk>/operation/<int:op_pk>/delete/", views_jobcard.api_route_delete_operation, name="api_route_delete_operation"),
    path("api/route/<int:pk>/reorder/", views_jobcard.api_route_reorder, name="api_route_reorder"),
    path("api/route/<int:pk>/clone/", views_jobcard.api_route_clone, name="api_route_clone"),
    path("api/route/<int:pk>/delete/", views_jobcard.api_route_delete, name="api_route_delete"),
    # WorkOrderCost URLs (5 patterns)
    path("costs/", views.WorkOrderCostListView.as_view(), name="workordercost_list"),
    path("costs/<int:pk>/", views.WorkOrderCostDetailView.as_view(), name="workordercost_detail"),
    path("costs/create/", views.WorkOrderCostCreateView.as_view(), name="workordercost_create"),
    path("costs/<int:pk>/edit/", views.WorkOrderCostUpdateView.as_view(), name="workordercost_update"),
    path("costs/<int:pk>/delete/", views.WorkOrderCostDeleteView.as_view(), name="workordercost_delete"),
    # NOTE: StatusTransitionLog, BitRepairHistory, OperationExecution URLs removed (Feb 2026)
]
