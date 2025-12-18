"""
Sprint 7: Compliance & Quality Management Admin Configuration

Registers all 10 Sprint 7 models with the Django admin interface.
"""

from django.contrib import admin
from .models import (
    ComplianceRequirement,
    QualityControl,
    NonConformance,
    AuditTrail,
    DocumentControl,
    TrainingRecord,
    Certification,
    ComplianceReport,
    QualityMetric,
    InspectionChecklist,
)


# =============================================================================
# WEEK 1: COMPLIANCE & QUALITY
# =============================================================================


@admin.register(ComplianceRequirement)
class ComplianceRequirementAdmin(admin.ModelAdmin):
    list_display = [
        'requirement_code', 'title', 'requirement_type',
        'status', 'compliance_status', 'effective_date', 'risk_level'
    ]
    list_filter = [
        'requirement_type', 'status', 'compliance_status', 'risk_level'
    ]
    search_fields = ['requirement_code', 'title', 'description', 'source_document']
    date_hierarchy = 'effective_date'
    ordering = ['requirement_code']


@admin.register(QualityControl)
class QualityControlAdmin(admin.ModelAdmin):
    list_display = [
        'inspection_number', 'inspection_type', 'result',
        'inspection_date', 'inspector'
    ]
    list_filter = ['inspection_type', 'result', 'inspection_date']
    search_fields = ['inspection_number', 'findings', 'defects_found']
    date_hierarchy = 'inspection_date'
    ordering = ['-inspection_date', '-inspection_number']


@admin.register(NonConformance)
class NonConformanceAdmin(admin.ModelAdmin):
    list_display = [
        'ncr_number', 'source', 'severity', 'status',
        'detected_date', 'reported_by'
    ]
    list_filter = ['source', 'severity', 'status']
    search_fields = ['ncr_number', 'description', 'defect_description']
    date_hierarchy = 'detected_date'
    ordering = ['-detected_date', '-ncr_number']


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'user', 'action', 'model_name', 'object_id'
    ]
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['description', 'model_name', 'object_repr']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    readonly_fields = [
        'action', 'description', 'model_name', 'object_id',
        'object_repr', 'user', 'timestamp', 'ip_address',
        'user_agent', 'changes'
    ]


# =============================================================================
# WEEK 2: DOCUMENTATION & TRAINING
# =============================================================================


@admin.register(DocumentControl)
class DocumentControlAdmin(admin.ModelAdmin):
    list_display = [
        'document_number', 'version', 'title', 'document_type',
        'status', 'revision_date', 'prepared_by'
    ]
    list_filter = ['document_type', 'status', 'revision_date']
    search_fields = ['document_number', 'title', 'description']
    date_hierarchy = 'revision_date'
    ordering = ['document_number', '-version']


@admin.register(TrainingRecord)
class TrainingRecordAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'training_title', 'training_type',
        'status', 'start_date', 'passed'
    ]
    list_filter = ['training_type', 'status', 'passed', 'required_for_position']
    search_fields = ['training_title', 'training_provider', 'instructor_name']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'certification_name', 'certification_body',
        'status', 'issue_date', 'expiry_date'
    ]
    list_filter = ['status', 'renewal_required', 'verified']
    search_fields = [
        'certification_name', 'certification_body', 'certification_number'
    ]
    date_hierarchy = 'issue_date'
    ordering = ['-issue_date']


# =============================================================================
# WEEK 3: REPORTING & METRICS
# =============================================================================


@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_number', 'title', 'report_type', 'status',
        'reporting_period_start', 'reporting_period_end', 'compliance_score'
    ]
    list_filter = ['report_type', 'status']
    search_fields = ['report_number', 'title', 'executive_summary', 'findings']
    date_hierarchy = 'reporting_period_end'
    ordering = ['-reporting_period_end']


@admin.register(QualityMetric)
class QualityMetricAdmin(admin.ModelAdmin):
    list_display = [
        'metric_name', 'metric_type', 'measurement_period',
        'measured_value', 'unit_of_measure', 'target_value', 'trend'
    ]
    list_filter = ['metric_type', 'trend', 'measurement_period']
    search_fields = ['metric_name', 'department', 'data_source']
    date_hierarchy = 'measurement_period'
    ordering = ['-measurement_period', 'metric_name']


@admin.register(InspectionChecklist)
class InspectionChecklistAdmin(admin.ModelAdmin):
    list_display = [
        'checklist_code', 'checklist_name', 'inspection_type',
        'version', 'is_active'
    ]
    list_filter = ['inspection_type', 'is_active']
    search_fields = ['checklist_code', 'checklist_name', 'applicable_to']
    ordering = ['checklist_code']
