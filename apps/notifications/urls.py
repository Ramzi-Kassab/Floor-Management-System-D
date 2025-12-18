from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    # Notifications
    path("", views.NotificationListView.as_view(), name="notification_list"),
    path("<int:pk>/read/", views.NotificationMarkReadView.as_view(), name="notification_read"),
    path("mark-all-read/", views.NotificationMarkAllReadView.as_view(), name="notification_mark_all_read"),
    path("<int:pk>/delete/", views.NotificationDeleteView.as_view(), name="notification_delete"),
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
]
