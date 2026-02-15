"""
ERP Automation URLs
"""
from django.urls import path
from . import views

app_name = "erp_automation"

urlpatterns = [
    # Dashboard
    path("", views.DashboardView.as_view(), name="dashboard"),

    # Workflows
    path("workflows/", views.WorkflowListView.as_view(), name="workflow_list"),
    path("workflows/<int:pk>/", views.WorkflowDetailView.as_view(), name="workflow_detail"),
    path("workflows/<int:pk>/execute/", views.WorkflowExecuteView.as_view(), name="workflow_execute"),

    # Locators
    path("locators/", views.LocatorListView.as_view(), name="locator_list"),
    path("locators/<int:pk>/", views.LocatorDetailView.as_view(), name="locator_detail"),

    # Recording
    path("record/", views.RecordingView.as_view(), name="record"),
    path("record/start/", views.start_recording, name="start_recording"),
    path("record/stop/", views.stop_recording, name="stop_recording"),
    path("record/poll/", views.poll_recording, name="poll_recording"),
    path("record/<int:pk>/", views.RecordingDetailView.as_view(), name="recording_detail"),
    path("record/<int:pk>/convert/", views.convert_recording_to_workflow, name="convert_recording"),
    path("record/<int:pk>/quick-convert/", views.quick_convert_recording, name="quick_convert_recording"),

    # Excel Handler
    path("excel/", views.ExcelHandlerView.as_view(), name="excel_handler"),
    path("excel/upload/", views.excel_upload, name="excel_upload"),
    path("excel/read-sheet/", views.excel_read_sheet, name="excel_read_sheet"),
    path("excel/select-rows/", views.select_rows_for_execution, name="select_rows"),

    # Field Mappings
    path("mappings/", views.FieldMappingListView.as_view(), name="field_mapping_list"),
    path("mappings/add/", views.FieldMappingFormView.as_view(), name="field_mapping_add"),
    path("mappings/<int:pk>/edit/", views.FieldMappingFormView.as_view(), name="field_mapping_edit"),
    path("mappings/<int:pk>/delete/", views.FieldMappingDeleteView.as_view(), name="field_mapping_delete"),

    # Execution
    path("execute/", views.execute_workflow_api, name="execute_workflow"),
    path("executions/", views.ExecutionListView.as_view(), name="execution_list"),
    path("executions/<int:pk>/", views.ExecutionDetailView.as_view(), name="execution_detail"),

    # API endpoints
    path("api/workflows/", views.api_workflows, name="api_workflows"),
    path("api/workflows/<int:pk>/update-url/", views.api_workflow_update_url, name="api_workflow_update_url"),
    path("api/locators/", views.api_locators, name="api_locators"),
    path("api/item-counter/<str:account_type>/next/", views.api_next_item_number, name="api_next_item_number"),

    # Session credentials
    path("credentials/", views.CredentialsView.as_view(), name="credentials"),
    path("credentials/clear/", views.clear_credentials, name="clear_credentials"),

    # Diagnostics
    path("check-browser/", views.check_browser, name="check_browser"),
    path("test-browser/", views.test_browser, name="test_browser"),

    # Job Data Preparation
    path("job-data/", views.JobDataListView.as_view(), name="job_data_list"),
    path("job-data/upload/", views.JobDataUploadView.as_view(), name="job_data_upload"),
    path("job-data/<int:pk>/", views.JobDataDetailView.as_view(), name="job_data_detail"),
    path("job-data/<int:pk>/update/", views.job_data_update, name="job_data_update"),
    path("job-data/<int:pk>/delete/", views.job_data_delete, name="job_data_delete"),

    # Routes Reference
    path("routes/", views.RouteListView.as_view(), name="route_list"),

    # Job Data APIs
    path("api/job-data/<int:pk>/clipboard/", views.api_job_data_clipboard, name="api_job_data_clipboard"),
    path("api/routes/select/", views.api_select_route, name="api_select_route"),
    path("api/job-data/<int:pk>/generate-item-number/", views.api_generate_item_number, name="api_generate_item_number"),
    path("api/job-data/<int:pk>/execute/", views.api_execute_job_data, name="api_execute_job_data"),

    # Workflow Chains
    path("chains/", views.ChainListView.as_view(), name="chain_list"),
    path("chains/create/", views.ChainCreateView.as_view(), name="chain_create"),
    path("chains/<int:pk>/", views.ChainDetailView.as_view(), name="chain_detail"),
    path("chains/<int:pk>/edit/", views.ChainEditView.as_view(), name="chain_edit"),
    path("chain-executions/<int:pk>/", views.ChainExecutionDetailView.as_view(), name="chain_execution_detail"),
    path("api/chains/segments/", views.api_chain_segments, name="api_chain_segments"),
    path("api/chains/create/", views.api_chain_create, name="api_chain_create"),
    path("api/chains/<int:pk>/save/", views.api_chain_save, name="api_chain_save"),
    path("api/chains/<int:pk>/delete/", views.api_chain_delete, name="api_chain_delete"),
    path("api/job-data/<int:pk>/execute-chain/", views.api_execute_chain, name="api_execute_chain"),
    path("api/chain-executions/<int:pk>/poll/", views.api_poll_chain_execution, name="api_poll_chain_execution"),

    # Live Execution Progress
    path("live/<int:pk>/", views.LiveExecutionView.as_view(), name="live_execution"),
    path("api/live/<int:pk>/poll/", views.api_poll_live_execution, name="api_poll_live"),
    path("api/live/<int:pk>/stop/", views.api_stop_live_execution, name="api_stop_live"),

    # Debug Execution Mode (single workflow)
    path("api/job-data/<int:pk>/debug-execute/", views.api_start_debug_execution, name="api_start_debug"),
    path("debug/<int:pk>/", views.DebugExecutionView.as_view(), name="debug_execution"),
    path("api/debug/<int:pk>/poll/", views.api_poll_debug_status, name="api_poll_debug"),
    path("api/debug/<int:pk>/resume/", views.api_debug_resume, name="api_debug_resume"),
    path("api/debug/<int:pk>/skip/", views.api_debug_skip, name="api_debug_skip"),
    path("api/debug/<int:pk>/stop/", views.api_debug_stop, name="api_debug_stop"),
    path("api/debug/<int:pk>/test-locator/", views.api_debug_test_locator, name="api_debug_test_locator"),
    path("api/debug/<int:pk>/update-locator/", views.api_debug_update_locator, name="api_debug_update_locator"),

    # Debug Chain Execution Mode (reuses debug/* API endpoints above)
    path("api/job-data/<int:pk>/debug-chain/", views.api_start_debug_chain, name="api_start_debug_chain"),
    path("debug-chain/<int:pk>/", views.DebugChainExecutionView.as_view(), name="debug_chain_execution"),

    # Workflow Step CRUD
    path("api/workflows/<int:wf_pk>/steps/", views.api_workflow_steps, name="api_workflow_steps"),
    path("api/workflows/<int:wf_pk>/steps/create/", views.api_step_create, name="api_step_create"),
    path("api/workflows/<int:wf_pk>/steps/<int:step_pk>/update/", views.api_step_update, name="api_step_update"),
    path("api/workflows/<int:wf_pk>/steps/<int:step_pk>/delete/", views.api_step_delete, name="api_step_delete"),

    # Locator CRUD
    path("api/locators/create/", views.api_locator_create, name="api_locator_create"),
    path("api/locators/<int:pk>/update/", views.api_locator_update, name="api_locator_update"),
    path("api/locators/<int:pk>/detail/", views.api_locator_detail, name="api_locator_detail_api"),
    path("api/locators/search/", views.api_locator_search, name="api_locator_search"),

    # Chain Editor APIs
    path("api/chains/<int:pk>/all-steps/", views.api_chain_all_steps, name="api_chain_all_steps"),
    path("api/chains/move-step/", views.api_chain_move_step, name="api_chain_move_step"),
    path("api/chains/split-segment/", views.api_chain_split_segment, name="api_chain_split_segment"),
    path("api/chains/merge-segments/", views.api_chain_merge_segments, name="api_chain_merge_segments"),
    path("api/debug/<int:pk>/rerun-from-step/", views.api_debug_rerun_from_step, name="api_debug_rerun_from_step"),
    path("api/debug/<int:pk>/run-single-step/", views.api_debug_run_single_step, name="api_debug_run_single_step"),
    path("api/debug/<int:pk>/breakpoints/", views.api_debug_set_breakpoints, name="api_debug_breakpoints"),

    # ERP Environments CRUD
    path("api/environments/", views.api_environment_list, name="api_environment_list"),
    path("api/environments/create/", views.api_environment_create, name="api_environment_create"),
    path("api/environments/<int:pk>/update/", views.api_environment_update, name="api_environment_update"),
    path("api/environments/<int:pk>/delete/", views.api_environment_delete, name="api_environment_delete"),
    path("api/environments/<int:pk>/set-default/", views.api_environment_set_default, name="api_environment_set_default"),
]
