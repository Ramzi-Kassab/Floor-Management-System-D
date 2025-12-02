"""
ARDT FMS - Documents URLs
Version: 5.4 - Sprint 2
"""

from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Document Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),

    # Documents
    path('', views.DocumentListView.as_view(), name='document_list'),
    path('upload/', views.DocumentCreateView.as_view(), name='document_create'),
    path('<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('<int:pk>/edit/', views.DocumentUpdateView.as_view(), name='document_update'),

    # Document Actions
    path('<int:pk>/download/', views.document_download, name='document_download'),
    path('<int:pk>/preview/', views.document_preview, name='document_preview'),
    path('<int:pk>/approve/', views.document_approve, name='document_approve'),
    path('<int:pk>/archive/', views.document_archive, name='document_archive'),
]
