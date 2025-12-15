from django.urls import path

from . import views

app_name = "technology"

urlpatterns = [
    # Designs
    path("designs/", views.DesignListView.as_view(), name="design_list"),
    path("designs/create/", views.DesignCreateView.as_view(), name="design_create"),
    path("designs/<int:pk>/", views.DesignDetailView.as_view(), name="design_detail"),
    path("designs/<int:pk>/edit/", views.DesignUpdateView.as_view(), name="design_update"),
    path("designs/<int:design_pk>/cutters/add/", views.CutterLayoutCreateView.as_view(), name="cutter_create"),
    path("designs/<int:design_pk>/cutters/<int:layout_pk>/delete/", views.CutterLayoutDeleteView.as_view(), name="cutter_delete"),
    # BOMs
    path("boms/", views.BOMListView.as_view(), name="bom_list"),
    path("boms/create/", views.BOMCreateView.as_view(), name="bom_create"),
    path("boms/<int:pk>/", views.BOMDetailView.as_view(), name="bom_detail"),
    path("boms/<int:pk>/edit/", views.BOMUpdateView.as_view(), name="bom_update"),
    path("boms/<int:pk>/lines/add/", views.BOMLineCreateView.as_view(), name="bom_line_create"),
    path("boms/<int:pk>/lines/<int:line_pk>/delete/", views.BOMLineDeleteView.as_view(), name="bom_line_delete"),
    # Connections
    path("connections/", views.ConnectionListView.as_view(), name="connection_list"),
    path("connections/create/", views.ConnectionCreateView.as_view(), name="connection_create"),
    path("connections/<int:pk>/", views.ConnectionDetailView.as_view(), name="connection_detail"),
    path("connections/<int:pk>/edit/", views.ConnectionUpdateView.as_view(), name="connection_update"),
    path("connections/<int:pk>/delete/", views.ConnectionDeleteView.as_view(), name="connection_delete"),
    # Breaker Slots
    path("breaker-slots/", views.BreakerSlotListView.as_view(), name="breaker_slot_list"),
    path("breaker-slots/create/", views.BreakerSlotCreateView.as_view(), name="breaker_slot_create"),
    path("breaker-slots/<int:pk>/", views.BreakerSlotDetailView.as_view(), name="breaker_slot_detail"),
    path("breaker-slots/<int:pk>/edit/", views.BreakerSlotUpdateView.as_view(), name="breaker_slot_update"),
    path("breaker-slots/<int:pk>/delete/", views.BreakerSlotDeleteView.as_view(), name="breaker_slot_delete"),
    # API endpoints (for modal pickers)
    path("api/connections/", views.APIConnectionsView.as_view(), name="api_connections"),
    path("api/breaker-slots/", views.APIBreakerSlotsView.as_view(), name="api_breaker_slots"),
]
