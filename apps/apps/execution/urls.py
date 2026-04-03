from django.urls import path

from . import views

app_name = "execution"

urlpatterns = [
    path("", views.ExecutionListView.as_view(), name="list"),
    path("<int:pk>/", views.ExecutionDetailView.as_view(), name="detail"),
    path("start/<int:wo_pk>/<int:procedure_pk>/", views.ExecutionStartView.as_view(), name="start"),
    path("<int:execution_pk>/steps/<int:step_pk>/complete/", views.StepCompleteView.as_view(), name="step_complete"),
    path("<int:execution_pk>/steps/<int:step_pk>/skip/", views.StepSkipView.as_view(), name="step_skip"),
    path("<int:pk>/pause/", views.ExecutionPauseView.as_view(), name="pause"),
    path("<int:pk>/resume/", views.ExecutionResumeView.as_view(), name="resume"),
]
