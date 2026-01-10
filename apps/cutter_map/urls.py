"""
Cutter Map URL Configuration
"""

from django.urls import path
from . import views

app_name = 'cutter_map'

urlpatterns = [
    # Main page
    path('', views.index, name='index'),

    # Document editor
    path('editor/<int:document_id>/', views.editor, name='editor'),

    # Upload and extraction
    path('upload/', views.upload, name='upload'),

    # Save edits
    path('save/<int:document_id>/', views.save_edits, name='save_edits'),

    # Validation
    path('validate/', views.validate, name='validate'),
    path('validate/<int:document_id>/', views.validate, name='validate_document'),

    # PDF generation
    path('generate/', views.generate_pdf, name='generate_pdf'),
    path('generate/<int:document_id>/', views.generate_pdf, name='generate_pdf_document'),

    # PPT generation
    path('generate-ppt/', views.generate_ppt, name='generate_ppt'),
    path('generate-ppt/<int:document_id>/', views.generate_ppt, name='generate_ppt_document'),

    # Downloads
    path('download/pdf/<int:document_id>/<str:filename>', views.download_pdf, name='download_pdf'),
    path('download/ppt/<int:document_id>/<str:filename>', views.download_ppt, name='download_ppt'),
    path('download/json/<str:filename>', views.download_json, name='download_json'),

    # Export
    path('export-json/', views.export_json, name='export_json'),
    path('export-json/<int:document_id>/', views.export_json, name='export_json_document'),

    # API Endpoints
    path('api/lookup-design/', views.api_lookup_design, name='api_lookup_design'),
    path('api/sync-to-erp/', views.api_sync_to_erp, name='api_sync_to_erp'),
]
