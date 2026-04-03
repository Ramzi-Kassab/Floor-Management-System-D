"""
ARDT FMS - Planning URLs
Version: 5.4
"""

from django.urls import path

from . import views

app_name = "planning"

urlpatterns = [
    # Sprints
    path("sprints/", views.SprintListView.as_view(), name="sprint_list"),
    path("sprints/create/", views.SprintCreateView.as_view(), name="sprint_create"),
    path("sprints/<int:pk>/", views.SprintDetailView.as_view(), name="sprint_detail"),
    path("sprints/<int:pk>/edit/", views.SprintUpdateView.as_view(), name="sprint_update"),
    path("sprints/<int:pk>/delete/", views.SprintDeleteView.as_view(), name="sprint_delete"),
    # Boards
    path("boards/", views.BoardListView.as_view(), name="board_list"),
    path("boards/create/", views.BoardCreateView.as_view(), name="board_create"),
    path("boards/<int:pk>/", views.BoardDetailView.as_view(), name="board_detail"),
    path("boards/<int:pk>/edit/", views.BoardUpdateView.as_view(), name="board_update"),
    path("boards/<int:pk>/delete/", views.BoardDeleteView.as_view(), name="board_delete"),
    # Columns
    path("columns/create/", views.ColumnCreateView.as_view(), name="column_create"),
    path("columns/<int:pk>/edit/", views.ColumnUpdateView.as_view(), name="column_update"),
    path("columns/<int:pk>/delete/", views.ColumnDeleteView.as_view(), name="column_delete"),
    # Items
    path("items/", views.ItemListView.as_view(), name="item_list"),
    path("items/create/", views.ItemCreateView.as_view(), name="item_create"),
    path("items/<int:pk>/", views.ItemDetailView.as_view(), name="item_detail"),
    path("items/<int:pk>/edit/", views.ItemUpdateView.as_view(), name="item_update"),
    path("items/<int:pk>/delete/", views.ItemDeleteView.as_view(), name="item_delete"),
    # Labels
    path("labels/", views.LabelListView.as_view(), name="label_list"),
    path("labels/create/", views.LabelCreateView.as_view(), name="label_create"),
    path("labels/<int:pk>/edit/", views.LabelUpdateView.as_view(), name="label_update"),
    path("labels/<int:pk>/delete/", views.LabelDeleteView.as_view(), name="label_delete"),
    # Wiki
    path("wiki/", views.WikiSpaceListView.as_view(), name="wiki_list"),
    path("wiki/create/", views.WikiSpaceCreateView.as_view(), name="wiki_space_create"),
    path("wiki/<int:pk>/", views.WikiSpaceDetailView.as_view(), name="wiki_space_detail"),
    path("wiki/<int:pk>/edit/", views.WikiSpaceUpdateView.as_view(), name="wiki_space_update"),
    path("wiki/<int:pk>/delete/", views.WikiSpaceDeleteView.as_view(), name="wiki_space_delete"),
    # Wiki Pages
    path("wiki/pages/create/", views.WikiPageCreateView.as_view(), name="wiki_page_create"),
    path("wiki/pages/<int:pk>/", views.WikiPageDetailView.as_view(), name="wiki_page_detail"),
    path("wiki/pages/<int:pk>/edit/", views.WikiPageUpdateView.as_view(), name="wiki_page_update"),
    path("wiki/pages/<int:pk>/delete/", views.WikiPageDeleteView.as_view(), name="wiki_page_delete"),
]
