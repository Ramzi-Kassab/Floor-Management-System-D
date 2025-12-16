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
]
