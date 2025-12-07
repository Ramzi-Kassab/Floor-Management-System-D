"""
Compliance App URLs - Complete Implementation
All 50 URL patterns for 10 models (5 patterns each)
Production-ready for ARDT Floor Management System
"""

from django.urls import path
from . import views

app_name = 'compliance'

urlpatterns = [
    # ========================================================================
    # ComplianceRequirement URLs (5 patterns)
    # ========================================================================
    path('requirements/',
         views.ComplianceRequirementListView.as_view(),
         name='compliancerequirement_list'),
    path('requirements/<int:pk>/',
         views.ComplianceRequirementDetailView.as_view(),
         name='compliancerequirement_detail'),
    path('requirements/create/',
         views.ComplianceRequirementCreateView.as_view(),
         name='compliancerequirement_create'),
    path('requirements/<int:pk>/edit/',
         views.ComplianceRequirementUpdateView.as_view(),
         name='compliancerequirement_update'),
    path('requirements/<int:pk>/delete/',
         views.ComplianceRequirementDeleteView.as_view(),
         name='compliancerequirement_delete'),

    # ========================================================================
    # QualityControl URLs (5 patterns)
    # ========================================================================
    path('qc/',
         views.QualityControlListView.as_view(),
         name='qualitycontrol_list'),
    path('qc/<int:pk>/',
         views.QualityControlDetailView.as_view(),
         name='qualitycontrol_detail'),
    path('qc/create/',
         views.QualityControlCreateView.as_view(),
         name='qualitycontrol_create'),
    path('qc/<int:pk>/edit/',
         views.QualityControlUpdateView.as_view(),
         name='qualitycontrol_update'),
    path('qc/<int:pk>/delete/',
         views.QualityControlDeleteView.as_view(),
         name='qualitycontrol_delete'),

    # ========================================================================
    # NonConformance URLs (5 patterns)
    # ========================================================================
    path('ncr/',
         views.NonConformanceListView.as_view(),
         name='nonconformance_list'),
    path('ncr/<int:pk>/',
         views.NonConformanceDetailView.as_view(),
         name='nonconformance_detail'),
    path('ncr/create/',
         views.NonConformanceCreateView.as_view(),
         name='nonconformance_create'),
    path('ncr/<int:pk>/edit/',
         views.NonConformanceUpdateView.as_view(),
         name='nonconformance_update'),
    path('ncr/<int:pk>/delete/',
         views.NonConformanceDeleteView.as_view(),
         name='nonconformance_delete'),

    # ========================================================================
    # AuditTrail URLs (5 patterns)
    # ========================================================================
    path('audit/',
         views.AuditTrailListView.as_view(),
         name='audittrail_list'),
    path('audit/<int:pk>/',
         views.AuditTrailDetailView.as_view(),
         name='audittrail_detail'),
    path('audit/create/',
         views.AuditTrailCreateView.as_view(),
         name='audittrail_create'),
    path('audit/<int:pk>/edit/',
         views.AuditTrailUpdateView.as_view(),
         name='audittrail_update'),
    path('audit/<int:pk>/delete/',
         views.AuditTrailDeleteView.as_view(),
         name='audittrail_delete'),

    # ========================================================================
    # DocumentControl URLs (5 patterns)
    # ========================================================================
    path('documents/',
         views.DocumentControlListView.as_view(),
         name='documentcontrol_list'),
    path('documents/<int:pk>/',
         views.DocumentControlDetailView.as_view(),
         name='documentcontrol_detail'),
    path('documents/create/',
         views.DocumentControlCreateView.as_view(),
         name='documentcontrol_create'),
    path('documents/<int:pk>/edit/',
         views.DocumentControlUpdateView.as_view(),
         name='documentcontrol_update'),
    path('documents/<int:pk>/delete/',
         views.DocumentControlDeleteView.as_view(),
         name='documentcontrol_delete'),

    # ========================================================================
    # TrainingRecord URLs (5 patterns)
    # ========================================================================
    path('training/',
         views.TrainingRecordListView.as_view(),
         name='trainingrecord_list'),
    path('training/<int:pk>/',
         views.TrainingRecordDetailView.as_view(),
         name='trainingrecord_detail'),
    path('training/create/',
         views.TrainingRecordCreateView.as_view(),
         name='trainingrecord_create'),
    path('training/<int:pk>/edit/',
         views.TrainingRecordUpdateView.as_view(),
         name='trainingrecord_update'),
    path('training/<int:pk>/delete/',
         views.TrainingRecordDeleteView.as_view(),
         name='trainingrecord_delete'),

    # ========================================================================
    # Certification URLs (5 patterns)
    # ========================================================================
    path('certifications/',
         views.CertificationListView.as_view(),
         name='certification_list'),
    path('certifications/<int:pk>/',
         views.CertificationDetailView.as_view(),
         name='certification_detail'),
    path('certifications/create/',
         views.CertificationCreateView.as_view(),
         name='certification_create'),
    path('certifications/<int:pk>/edit/',
         views.CertificationUpdateView.as_view(),
         name='certification_update'),
    path('certifications/<int:pk>/delete/',
         views.CertificationDeleteView.as_view(),
         name='certification_delete'),

    # ========================================================================
    # ComplianceReport URLs (5 patterns)
    # ========================================================================
    path('reports/',
         views.ComplianceReportListView.as_view(),
         name='compliancereport_list'),
    path('reports/<int:pk>/',
         views.ComplianceReportDetailView.as_view(),
         name='compliancereport_detail'),
    path('reports/create/',
         views.ComplianceReportCreateView.as_view(),
         name='compliancereport_create'),
    path('reports/<int:pk>/edit/',
         views.ComplianceReportUpdateView.as_view(),
         name='compliancereport_update'),
    path('reports/<int:pk>/delete/',
         views.ComplianceReportDeleteView.as_view(),
         name='compliancereport_delete'),

    # ========================================================================
    # QualityMetric URLs (5 patterns)
    # ========================================================================
    path('metrics/',
         views.QualityMetricListView.as_view(),
         name='qualitymetric_list'),
    path('metrics/<int:pk>/',
         views.QualityMetricDetailView.as_view(),
         name='qualitymetric_detail'),
    path('metrics/create/',
         views.QualityMetricCreateView.as_view(),
         name='qualitymetric_create'),
    path('metrics/<int:pk>/edit/',
         views.QualityMetricUpdateView.as_view(),
         name='qualitymetric_update'),
    path('metrics/<int:pk>/delete/',
         views.QualityMetricDeleteView.as_view(),
         name='qualitymetric_delete'),

    # ========================================================================
    # InspectionChecklist URLs (5 patterns)
    # ========================================================================
    path('checklists/',
         views.InspectionChecklistListView.as_view(),
         name='inspectionchecklist_list'),
    path('checklists/<int:pk>/',
         views.InspectionChecklistDetailView.as_view(),
         name='inspectionchecklist_detail'),
    path('checklists/create/',
         views.InspectionChecklistCreateView.as_view(),
         name='inspectionchecklist_create'),
    path('checklists/<int:pk>/edit/',
         views.InspectionChecklistUpdateView.as_view(),
         name='inspectionchecklist_update'),
    path('checklists/<int:pk>/delete/',
         views.InspectionChecklistDeleteView.as_view(),
         name='inspectionchecklist_delete'),
]
