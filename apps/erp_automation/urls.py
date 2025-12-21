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
    path("api/locators/", views.api_locators, name="api_locators"),
    path("api/item-counter/<str:account_type>/next/", views.api_next_item_number, name="api_next_item_number"),

    # Session credentials
    path("credentials/", views.CredentialsView.as_view(), name="credentials"),
    path("credentials/clear/", views.clear_credentials, name="clear_credentials"),

    # Diagnostics
    path("check-browser/", views.check_browser, name="check_browser"),
]
