from django.urls import path

from . import views

app_name = "procedures"

urlpatterns = [
    # Procedures
    path("", views.ProcedureListView.as_view(), name="procedure_list"),
    path("create/", views.ProcedureCreateView.as_view(), name="procedure_create"),
    path("<int:pk>/", views.ProcedureDetailView.as_view(), name="procedure_detail"),
    path("<int:pk>/edit/", views.ProcedureUpdateView.as_view(), name="procedure_update"),
    # Steps
    path("<int:pk>/steps/add/", views.ProcedureStepCreateView.as_view(), name="step_create"),
    path("<int:pk>/steps/<int:step_pk>/edit/", views.ProcedureStepUpdateView.as_view(), name="step_update"),
    path("<int:pk>/steps/<int:step_pk>/delete/", views.ProcedureStepDeleteView.as_view(), name="step_delete"),
    # Checkpoints
    path("steps/<int:step_pk>/checkpoints/add/", views.StepCheckpointCreateView.as_view(), name="checkpoint_create"),
]
