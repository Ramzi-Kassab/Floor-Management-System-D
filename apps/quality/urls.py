from django.urls import path

from . import views

app_name = "quality"

urlpatterns = [
    # Inspections
    path("inspections/", views.InspectionListView.as_view(), name="inspection_list"),
    path("inspections/create/", views.InspectionCreateView.as_view(), name="inspection_create"),
    path("inspections/<int:pk>/", views.InspectionDetailView.as_view(), name="inspection_detail"),
    path("inspections/<int:pk>/edit/", views.InspectionUpdateView.as_view(), name="inspection_update"),
    path("inspections/<int:pk>/complete/", views.InspectionCompleteView.as_view(), name="inspection_complete"),
    # NCRs
    path("ncrs/", views.NCRListView.as_view(), name="ncr_list"),
    path("ncrs/create/", views.NCRCreateView.as_view(), name="ncr_create"),
    path("ncrs/<int:pk>/", views.NCRDetailView.as_view(), name="ncr_detail"),
    path("ncrs/<int:pk>/edit/", views.NCRUpdateView.as_view(), name="ncr_update"),
    path("ncrs/<int:pk>/disposition/", views.NCRDispositionView.as_view(), name="ncr_disposition"),
    path("ncrs/<int:pk>/photos/upload/", views.NCRPhotoUploadView.as_view(), name="ncr_photo_upload"),
    path("ncrs/<int:pk>/photos/<int:photo_pk>/delete/", views.NCRPhotoDeleteView.as_view(), name="ncr_photo_delete"),
]
