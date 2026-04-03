from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    # Notifications
    path("", views.NotificationListView.as_view(), name="notification_list"),
    path("<int:pk>/read/", views.NotificationMarkReadView.as_view(), name="notification_read"),
    path("mark-all-read/", views.NotificationMarkAllReadView.as_view(), name="notification_mark_all_read"),
    path("<int:pk>/delete/", views.NotificationDeleteView.as_view(), name="notification_delete"),
    # Bell fragment (HTMX polling)
    path("api/bell/", views.NotificationBellView.as_view(), name="bell_fragment"),
    path("api/<int:pk>/mark-read/", views.ApiMarkReadView.as_view(), name="api_mark_read"),
    path("api/mark-all-read/", views.ApiMarkAllReadView.as_view(), name="api_mark_all_read"),
    # Tasks
    path("tasks/", views.TaskListView.as_view(), name="task_list"),
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task_detail"),
    path("tasks/create/", views.TaskCreateView.as_view(), name="task_create"),
    path("tasks/<int:pk>/edit/", views.TaskUpdateView.as_view(), name="task_update"),
    path("tasks/<int:pk>/status/", views.TaskStatusUpdateView.as_view(), name="task_status"),
    path("tasks/<int:pk>/complete/", views.TaskCompleteView.as_view(), name="task_complete"),
    # Notification Templates
    path("templates/", views.NotificationTemplateListView.as_view(), name="template_list"),
    path("templates/create/", views.NotificationTemplateCreateView.as_view(), name="template_create"),
    path("templates/<int:pk>/edit/", views.NotificationTemplateUpdateView.as_view(), name="template_update"),
    # Audit Logs
    path("audit/", views.AuditLogListView.as_view(), name="audit_list"),
    path("audit/<int:pk>/", views.AuditLogDetailView.as_view(), name="audit_detail"),
    # Comments (API)
    path("comments/<str:entity_type>/<int:entity_id>/", views.CommentListView.as_view(), name="comment_list"),
    path("comments/<str:entity_type>/<int:entity_id>/create/", views.CommentCreateView.as_view(), name="comment_create"),
    path("comments/<int:pk>/delete/", views.CommentDeleteView.as_view(), name="comment_delete"),
    # Workflow Engine
    path("actions/", views.ActionCenterView.as_view(), name="action_center"),
    path("api/actions/<int:pk>/claim/", views.api_workflow_action_claim, name="api_action_claim"),
    # Workflow Settings
    path("settings/workflow/", views.WorkflowSettingsIndexView.as_view(), name="workflow_settings"),
    path("settings/workflow/capabilities/", views.WorkflowCapabilityView.as_view(), name="workflow_capabilities"),
    path("api/workflow/capabilities/grant/", views.api_capability_grant, name="api_capability_grant"),
    path("api/workflow/capabilities/<int:pk>/revoke/", views.api_capability_revoke, name="api_capability_revoke"),
    path("api/workflow/capabilities/<int:pk>/toggle/", views.api_capability_toggle_available, name="api_capability_toggle"),
]
