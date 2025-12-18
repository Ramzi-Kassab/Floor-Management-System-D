from django.urls import path

from . import views

app_name = "maintenance"

urlpatterns = [
    # Equipment Categories
    path("categories/", views.EquipmentCategoryListView.as_view(), name="category_list"),
    path("categories/create/", views.EquipmentCategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", views.EquipmentCategoryUpdateView.as_view(), name="category_update"),
    # Equipment
    path("equipment/", views.EquipmentListView.as_view(), name="equipment_list"),
    path("equipment/create/", views.EquipmentCreateView.as_view(), name="equipment_create"),
    path("equipment/<int:pk>/", views.EquipmentDetailView.as_view(), name="equipment_detail"),
    path("equipment/<int:pk>/edit/", views.EquipmentUpdateView.as_view(), name="equipment_update"),
    # Maintenance Requests
    path("requests/", views.RequestListView.as_view(), name="request_list"),
    path("requests/create/", views.RequestCreateView.as_view(), name="request_create"),
    path("requests/<int:pk>/", views.RequestDetailView.as_view(), name="request_detail"),
    path("requests/<int:pk>/approve/", views.RequestApproveView.as_view(), name="request_approve"),
    # Maintenance Work Orders
    path("", views.MWOListView.as_view(), name="mwo_list"),
    path("work-orders/", views.MWOListView.as_view(), name="work_orders"),
    path("work-orders/create/", views.MWOCreateView.as_view(), name="mwo_create"),
    path("work-orders/<int:pk>/", views.MWODetailView.as_view(), name="mwo_detail"),
    path("work-orders/<int:pk>/edit/", views.MWOUpdateView.as_view(), name="mwo_update"),
    path("work-orders/<int:pk>/start/", views.MWOStartView.as_view(), name="mwo_start"),
    path("work-orders/<int:pk>/complete/", views.MWOCompleteView.as_view(), name="mwo_complete"),
    path("work-orders/<int:pk>/add-part/", views.MWOAddPartView.as_view(), name="mwo_add_part"),
    # Preventive Maintenance Scheduling
    path("schedule/", views.PreventiveMaintenanceScheduleView.as_view(), name="pm_schedule"),
    path("schedule/generate/", views.GeneratePreventiveMaintenanceView.as_view(), name="pm_generate"),
]
