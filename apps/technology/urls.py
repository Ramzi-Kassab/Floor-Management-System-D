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
    path("designs/<int:pk>/pockets/", views.DesignPocketsView.as_view(), name="design_pockets"),
    path("designs/<int:pk>/pockets/update-info/", views.DesignPocketsUpdateInfoView.as_view(), name="design_pockets_update_info"),
    path("designs/<int:pk>/pockets/config/add/", views.PocketConfigCreateView.as_view(), name="pocket_config_create"),
    path("designs/<int:pk>/pockets/config/<int:config_pk>/delete/", views.PocketConfigDeleteView.as_view(), name="pocket_config_delete"),
    path("designs/<int:pk>/pockets/config/reorder/", views.PocketConfigReorderView.as_view(), name="pocket_config_reorder"),
    path("designs/<int:pk>/pockets/config/update-row/", views.PocketConfigUpdateRowView.as_view(), name="pocket_config_update_row"),
    path("designs/<int:pk>/pockets/grid/", views.DesignPocketsGridSaveView.as_view(), name="design_pockets_grid"),
    path("designs/<int:pk>/pockets/locations/", views.DesignPocketsLocationSaveView.as_view(), name="design_pockets_locations"),
    path("designs/<int:pk>/pockets/engagements/", views.DesignPocketsEngagementSaveView.as_view(), name="design_pockets_engagements"),
    # Pockets Layout (general list)
    path("pockets-layout/", views.PocketsLayoutListView.as_view(), name="pockets_layout_list"),
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
