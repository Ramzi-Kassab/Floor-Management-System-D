"""
ARDT FMS - Forms Engine URLs
Version: 5.4

URL patterns for the dynamic form builder.
"""

from django.urls import path
from . import views

app_name = "forms_engine"

urlpatterns = [
    # Form Template Management
    path('', views.FormTemplateListView.as_view(), name='template-list'),
    path('<int:pk>/', views.FormTemplateDetailView.as_view(), name='template-detail'),
    path('create/', views.FormTemplateCreateView.as_view(), name='template-create'),
    path('<int:pk>/edit/', views.FormTemplateUpdateView.as_view(), name='template-update'),
    path('<int:pk>/delete/', views.FormTemplateDeleteView.as_view(), name='template-delete'),
    path('<int:pk>/builder/', views.FormTemplateBuilderView.as_view(), name='template-builder'),
    path('<int:pk>/preview/', views.FormPreviewView.as_view(), name='template-preview'),
    path('<int:pk>/duplicate/', views.duplicate_template, name='template-duplicate'),
    path('<int:pk>/activate/', views.activate_template, name='template-activate'),
    path('<int:pk>/deactivate/', views.deactivate_template, name='template-deactivate'),

    # Section Management
    path('<int:template_pk>/section/create/', views.FormSectionCreateView.as_view(), name='section-create'),
    path('section/<int:pk>/edit/', views.FormSectionUpdateView.as_view(), name='section-update'),
    path('section/<int:pk>/delete/', views.FormSectionDeleteView.as_view(), name='section-delete'),

    # Field Management
    path('section/<int:section_pk>/field/create/', views.FormFieldCreateView.as_view(), name='field-create'),
    path('field/<int:pk>/edit/', views.FormFieldUpdateView.as_view(), name='field-update'),
    path('field/<int:pk>/delete/', views.FormFieldDeleteView.as_view(), name='field-delete'),

    # Field Type Management
    path('field-types/', views.FieldTypeListView.as_view(), name='fieldtype-list'),
    path('field-types/create/', views.FieldTypeCreateView.as_view(), name='fieldtype-create'),
    path('field-types/<int:pk>/edit/', views.FieldTypeUpdateView.as_view(), name='fieldtype-update'),
    path('field-types/<int:pk>/delete/', views.FieldTypeDeleteView.as_view(), name='fieldtype-delete'),

    # HTMX/API endpoints
    path('<int:pk>/reorder-sections/', views.reorder_sections_htmx, name='reorder-sections'),
    path('section/<int:pk>/reorder-fields/', views.reorder_fields_htmx, name='reorder-fields'),
]
