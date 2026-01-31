"""
Cutter Map URL Configuration
"""

from django.urls import path
from . import views

app_name = 'cutter_map'

urlpatterns = [
    # Main page
    path('', views.index, name='index'),

    # BOM view/edit (opens PDF Generator with BOM data)
    path('bom/<int:bom_id>/', views.bom_view, name='bom_view'),

    # Read-only BOM view (for work orders and job cards)
    path('bom/<int:bom_id>/readonly/', views.bom_readonly, name='bom_readonly'),

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

    # Downloads - simple route like Flask (no auth required for direct file access)
    path('download/<str:filename>', views.download_file, name='download_file'),
    # Legacy routes with document_id
    path('download/pdf/<int:document_id>/<str:filename>', views.download_pdf, name='download_pdf'),
    path('download/ppt/<int:document_id>/<str:filename>', views.download_ppt, name='download_ppt'),
    path('download/json/<str:filename>', views.download_json, name='download_json'),

    # Export
    path('export-json/', views.export_json, name='export_json'),
    path('export-json/<int:document_id>/', views.export_json, name='export_json_document'),

    # API Endpoints
    path('api/lookup-design/', views.api_lookup_design, name='api_lookup_design'),
    path('api/sync-to-erp/', views.api_sync_to_erp, name='api_sync_to_erp'),
    path('api/cutter-inventory/', views.api_cutter_inventory, name='api_cutter_inventory'),
    path('api/cutter-shapes/', views.api_cutter_shapes, name='api_cutter_shapes'),
    path('api/create-cutters/', views.api_create_cutters, name='api_create_cutters'),
    path('api/activate-bom/<int:bom_id>/', views.api_activate_bom, name='api_activate_bom'),
    path('api/toggle-original/<int:bom_id>/', views.api_toggle_original, name='api_toggle_original'),
    path('api/bom/<int:bom_id>/system-mat/', views.api_set_system_mat, name='api_set_system_mat'),
    path('api/bom/<int:bom_id>/link-drillbits/', views.api_link_bom_to_drillbits, name='api_link_bom_to_drillbits'),
    path('api/quick-add-smi-type/', views.api_quick_add_smi_type, name='api_quick_add_smi_type'),
    path('api/quick-add-iadc-code/', views.api_quick_add_iadc_code, name='api_quick_add_iadc_code'),
    path('api/dropdown-data/', views.api_dropdown_data, name='api_dropdown_data'),

    # Wizard
    path('add-cutter-wizard/', views.add_cutter_wizard, name='add_cutter_wizard'),
]
