"""
Compliance App Forms - Complete Implementation
All 10 models with full validation and widgets
Production-ready for ARDT Floor Management System
"""

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import (
    ComplianceRequirement, QualityControl, NonConformance,
    AuditTrail, DocumentControl, TrainingRecord, Certification,
    ComplianceReport, QualityMetric, InspectionChecklist
)

User = get_user_model()

# Standard Tailwind CSS classes for form widgets
INPUT_CLASS = 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
SELECT_CLASS = 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
TEXTAREA_CLASS = 'mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500'
CHECKBOX_CLASS = 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700'
FILE_CLASS = 'mt-1 block w-full text-sm text-gray-900 dark:text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'


# ============================================================================
# FORM 1: ComplianceRequirement
# ============================================================================

class ComplianceRequirementForm(forms.ModelForm):
    """
    Complete form for ComplianceRequirement.
    Manages regulatory and standard requirements tracking.
    """

    class Meta:
        model = ComplianceRequirement
        fields = [
            'requirement_code', 'title', 'requirement_type', 'source_document',
            'clause_number', 'version', 'issuing_authority', 'description',
            'applicable_scope', 'compliance_criteria', 'status', 'compliance_status',
            'effective_date', 'review_date', 'last_assessment_date', 'superseded_date',
            'responsible_person', 'responsible_department', 'implementation_notes',
            'verification_method', 'documentation_required', 'risk_level',
            'consequences_of_non_compliance', 'assessment_frequency', 'last_assessed_by',
            'assessment_notes', 'supersedes', 'related_requirements', 'reference_url',
            'internal_procedure'
        ]
        widgets = {
            'requirement_code': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'e.g., ISO-9001-2015-8.2.1'
            }),
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Requirement title'
            }),
            'requirement_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'source_document': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'e.g., ISO 9001:2015'
            }),
            'clause_number': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'e.g., 8.2.1'
            }),
            'version': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': '2015'
            }),
            'issuing_authority': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'ISO, API, Government Agency'
            }),
            'description': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 4,
                'placeholder': 'Detailed description of the requirement...'
            }),
            'applicable_scope': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3,
                'placeholder': 'Which processes/departments does this apply to?'
            }),
            'compliance_criteria': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3,
                'placeholder': 'How is compliance measured?'
            }),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'compliance_status': forms.Select(attrs={'class': SELECT_CLASS}),
            'effective_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'review_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'last_assessment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'superseded_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'responsible_person': forms.Select(attrs={'class': SELECT_CLASS}),
            'responsible_department': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'implementation_notes': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'verification_method': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
            'documentation_required': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
            'risk_level': forms.Select(attrs={'class': SELECT_CLASS}),
            'consequences_of_non_compliance': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
            'assessment_frequency': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'e.g., Quarterly, Annually'
            }),
            'last_assessed_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'assessment_notes': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'supersedes': forms.Select(attrs={'class': SELECT_CLASS}),
            'related_requirements': forms.SelectMultiple(attrs={
                'class': SELECT_CLASS,
                'size': 5
            }),
            'reference_url': forms.URLInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'https://...'
            }),
            'internal_procedure': forms.TextInput(attrs={'class': INPUT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional_fields = [
            'clause_number', 'version', 'issuing_authority', 'applicable_scope',
            'compliance_criteria', 'review_date', 'last_assessment_date',
            'superseded_date', 'responsible_person', 'responsible_department',
            'implementation_notes', 'verification_method', 'documentation_required',
            'consequences_of_non_compliance', 'assessment_frequency',
            'last_assessed_by', 'assessment_notes', 'supersedes',
            'related_requirements', 'reference_url', 'internal_procedure'
        ]
        for field in optional_fields:
            if field in self.fields:
                self.fields[field].required = False

    def clean_requirement_code(self):
        """Validate and format requirement code"""
        code = self.cleaned_data.get('requirement_code')
        if code:
            code = code.upper().strip()
        return code

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        superseded_date = cleaned_data.get('superseded_date')

        if status == 'SUPERSEDED' and not superseded_date:
            self.add_error('superseded_date', 'Superseded date is required when status is SUPERSEDED')

        return cleaned_data


# ============================================================================
# FORM 2: QualityControl
# ============================================================================

class QualityControlForm(forms.ModelForm):
    """
    Complete form for QualityControl.
    Handles inspection records with full validation.
    """

    class Meta:
        model = QualityControl
        fields = [
            'inspection_number', 'inspection_type', 'result', 'work_order', 'receipt',
            'drill_bit', 'inventory_item', 'equipment', 'inspection_date', 'inspector',
            'inspection_location', 'specification_reference', 'acceptance_criteria',
            'sampling_method', 'sample_size', 'test_equipment_used', 'measurement_results',
            'defects_found', 'corrective_action', 'preventive_action', 'approved_by',
            'approval_date', 'certificate_number', 'certificate_issued', 'remarks',
            'attachments', 'non_conformance'
        ]
        widgets = {
            'inspection_number': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Auto-generated if left blank'
            }),
            'inspection_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'result': forms.Select(attrs={'class': SELECT_CLASS}),
            'work_order': forms.Select(attrs={'class': SELECT_CLASS}),
            'receipt': forms.Select(attrs={'class': SELECT_CLASS}),
            'drill_bit': forms.Select(attrs={'class': SELECT_CLASS}),
            'inventory_item': forms.Select(attrs={'class': SELECT_CLASS}),
            'equipment': forms.Select(attrs={'class': SELECT_CLASS}),
            'inspection_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'inspector': forms.Select(attrs={'class': SELECT_CLASS}),
            'inspection_location': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'specification_reference': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'acceptance_criteria': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'sampling_method': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
            'sample_size': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'test_equipment_used': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'measurement_results': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 4,
                'placeholder': 'Enter JSON data or key measurement results'
            }),
            'defects_found': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'corrective_action': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'preventive_action': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'approved_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'approval_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'certificate_number': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'certificate_issued': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'remarks': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'attachments': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
            'non_conformance': forms.Select(attrs={'class': SELECT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['inspection_type', 'result']:
                field.required = False

    def clean(self):
        """Validation for quality control"""
        cleaned_data = super().clean()
        result = cleaned_data.get('result')
        defects_found = cleaned_data.get('defects_found')

        if result in ['FAIL', 'CONDITIONAL'] and not defects_found:
            self.add_error('defects_found', 'Please document defects found for failed/conditional inspections')

        return cleaned_data


# ============================================================================
# FORM 3: NonConformance
# ============================================================================

class NonConformanceForm(forms.ModelForm):
    """
    Complete form for NonConformance.
    Manages non-conformance reports (NCRs).
    """

    class Meta:
        model = NonConformance
        fields = [
            'ncr_number', 'source', 'severity', 'status', 'issue_description',
            'work_order', 'quality_control', 'supplier', 'inventory_item', 'drill_bit',
            'detected_date', 'detected_by', 'detection_stage', 'root_cause',
            'containment_action', 'containment_date', 'corrective_action',
            'corrective_action_date', 'responsible_person', 'target_completion_date',
            'actual_completion_date', 'verification_method', 'verified_by',
            'verification_date', 'cost_impact', 'follow_up_required', 'follow_up_date',
            'lessons_learned'
        ]
        widgets = {
            'ncr_number': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Auto-generated if left blank'
            }),
            'source': forms.Select(attrs={'class': SELECT_CLASS}),
            'severity': forms.Select(attrs={'class': SELECT_CLASS}),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'issue_description': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 4,
                'placeholder': 'Describe the non-conformance in detail...'
            }),
            'work_order': forms.Select(attrs={'class': SELECT_CLASS}),
            'quality_control': forms.Select(attrs={'class': SELECT_CLASS}),
            'supplier': forms.Select(attrs={'class': SELECT_CLASS}),
            'inventory_item': forms.Select(attrs={'class': SELECT_CLASS}),
            'drill_bit': forms.Select(attrs={'class': SELECT_CLASS}),
            'detected_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'detected_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'detection_stage': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'root_cause': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'containment_action': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'containment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'corrective_action': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'corrective_action_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'responsible_person': forms.Select(attrs={'class': SELECT_CLASS}),
            'target_completion_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'actual_completion_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'verification_method': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
            'verified_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'verification_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'cost_impact': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.01'
            }),
            'follow_up_required': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'follow_up_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'lessons_learned': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_fields = ['source', 'severity', 'status', 'issue_description']
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False


# ============================================================================
# FORM 4: AuditTrail
# ============================================================================

class AuditTrailForm(forms.ModelForm):
    """
    Complete form for AuditTrail.
    Typically auto-generated but can be manually created.
    """

    class Meta:
        model = AuditTrail
        fields = [
            'action', 'description', 'model_name', 'object_id', 'object_repr',
            'timestamp', 'user', 'ip_address', 'user_agent', 'changes'
        ]
        widgets = {
            'action': forms.Select(attrs={'class': SELECT_CLASS}),
            'description': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'model_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'object_id': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'object_repr': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'timestamp': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': INPUT_CLASS
            }),
            'user': forms.Select(attrs={'class': SELECT_CLASS}),
            'ip_address': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'user_agent': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
            'changes': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 4,
                'placeholder': 'JSON data of changes'
            }),
        }


# ============================================================================
# FORM 5: DocumentControl
# ============================================================================

class DocumentControlForm(forms.ModelForm):
    """
    Complete form for DocumentControl.
    Manages controlled documents.
    """

    class Meta:
        model = DocumentControl
        fields = [
            'document_number', 'title', 'document_type', 'version', 'revision_date',
            'status', 'author', 'reviewer', 'approver', 'review_date', 'approval_date',
            'effective_date', 'expiry_date', 'supersedes', 'department',
            'distribution_list', 'document_file', 'summary', 'keywords',
            'related_documents', 'retention_period', 'archive_date', 'archived_by',
            'change_description'
        ]
        widgets = {
            'document_number': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'e.g., DOC-2024-001'
            }),
            'title': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'document_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'version': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': '1.0'
            }),
            'revision_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'author': forms.Select(attrs={'class': SELECT_CLASS}),
            'reviewer': forms.Select(attrs={'class': SELECT_CLASS}),
            'approver': forms.Select(attrs={'class': SELECT_CLASS}),
            'review_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'approval_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'effective_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'supersedes': forms.Select(attrs={'class': SELECT_CLASS}),
            'department': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'distribution_list': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
            'document_file': forms.FileInput(attrs={'class': FILE_CLASS}),
            'summary': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'keywords': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Comma-separated keywords'
            }),
            'related_documents': forms.SelectMultiple(attrs={
                'class': SELECT_CLASS,
                'size': 5
            }),
            'retention_period': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'e.g., 7 years'
            }),
            'archive_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'archived_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'change_description': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_fields = ['document_number', 'title', 'document_type', 'version', 'revision_date', 'status']
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False


# ============================================================================
# FORM 6: TrainingRecord
# ============================================================================

class TrainingRecordForm(forms.ModelForm):
    """
    Complete form for TrainingRecord.
    Tracks employee training records.
    """

    class Meta:
        model = TrainingRecord
        fields = [
            'employee', 'training_type', 'training_title', 'training_description',
            'training_provider', 'training_date', 'status', 'training_duration_hours',
            'instructor', 'location', 'training_materials', 'assessment_type',
            'assessment_score', 'passing_score', 'certification_number',
            'certificate_issued', 'certificate_expiry_date', 'competency_level',
            'training_cost', 'retraining_required_date', 'retraining_frequency',
            'notes', 'attachments'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': SELECT_CLASS}),
            'training_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'training_title': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'training_description': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'training_provider': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'training_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'training_duration_hours': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.5'
            }),
            'instructor': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'location': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'training_materials': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
            'assessment_type': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'assessment_score': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.01'
            }),
            'passing_score': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.01'
            }),
            'certification_number': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'certificate_issued': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'certificate_expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'competency_level': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'training_cost': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.01'
            }),
            'retraining_required_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'retraining_frequency': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'e.g., Annually, Every 2 years'
            }),
            'notes': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'attachments': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_fields = ['employee', 'training_type', 'training_title', 'training_description', 'training_provider', 'training_date', 'status']
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False


# ============================================================================
# FORM 7: Certification
# ============================================================================

class CertificationForm(forms.ModelForm):
    """
    Complete form for Certification.
    Manages employee certifications.
    """

    class Meta:
        model = Certification
        fields = [
            'employee', 'certification_name', 'certification_body', 'certification_number',
            'issue_date', 'expiry_date', 'status', 'level', 'scope', 'verification_method',
            'verified_by', 'verification_date', 'renewal_requirements',
            'renewal_notification_days', 'cost', 'certificate_file', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': SELECT_CLASS}),
            'certification_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'certification_body': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'certification_number': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'issue_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'level': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'scope': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
            'verification_method': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'verified_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'verification_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'renewal_requirements': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
            'renewal_notification_days': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'cost': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.01'
            }),
            'certificate_file': forms.FileInput(attrs={'class': FILE_CLASS}),
            'notes': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_fields = ['employee', 'certification_name', 'certification_body', 'certification_number', 'issue_date', 'expiry_date', 'status']
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False


# ============================================================================
# FORM 8: ComplianceReport
# ============================================================================

class ComplianceReportForm(forms.ModelForm):
    """
    Complete form for ComplianceReport.
    Manages compliance reports.
    """

    class Meta:
        model = ComplianceReport
        fields = [
            'report_number', 'report_type', 'title', 'reporting_period_start',
            'reporting_period_end', 'status', 'prepared_by', 'reviewed_by',
            'approved_by', 'preparation_date', 'review_date', 'approval_date',
            'executive_summary', 'findings', 'recommendations', 'action_items',
            'report_file', 'distribution_list'
        ]
        widgets = {
            'report_number': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Auto-generated if left blank'
            }),
            'report_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'title': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'reporting_period_start': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'reporting_period_end': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'prepared_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'reviewed_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'approved_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'preparation_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'review_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'approval_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'executive_summary': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 4
            }),
            'findings': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 5
            }),
            'recommendations': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 4
            }),
            'action_items': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
            'report_file': forms.FileInput(attrs={'class': FILE_CLASS}),
            'distribution_list': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_fields = ['report_type', 'title', 'reporting_period_start', 'reporting_period_end', 'status']
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False


# ============================================================================
# FORM 9: QualityMetric
# ============================================================================

class QualityMetricForm(forms.ModelForm):
    """
    Complete form for QualityMetric.
    Tracks quality metrics and KPIs.
    """

    class Meta:
        model = QualityMetric
        fields = [
            'metric_name', 'metric_type', 'measurement_period', 'measured_value',
            'unit_of_measure', 'status', 'target_value', 'minimum_acceptable',
            'maximum_acceptable', 'measurement_method', 'data_source', 'measured_by',
            'variance_percentage', 'trend', 'notes'
        ]
        widgets = {
            'metric_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'metric_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'measurement_period': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'measured_value': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.01'
            }),
            'unit_of_measure': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'target_value': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.01'
            }),
            'minimum_acceptable': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.01'
            }),
            'maximum_acceptable': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.01'
            }),
            'measurement_method': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
            'data_source': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'measured_by': forms.Select(attrs={'class': SELECT_CLASS}),
            'variance_percentage': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.01'
            }),
            'trend': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'notes': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_fields = ['metric_name', 'metric_type', 'measurement_period', 'measured_value', 'unit_of_measure', 'status']
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False


# ============================================================================
# FORM 10: InspectionChecklist
# ============================================================================

class InspectionChecklistForm(forms.ModelForm):
    """
    Complete form for InspectionChecklist.
    Manages inspection checklists.
    """

    class Meta:
        model = InspectionChecklist
        fields = [
            'checklist_code', 'checklist_name', 'inspection_type', 'applicable_to',
            'checklist_items', 'is_active', 'version', 'effective_date', 'revision_date'
        ]
        widgets = {
            'checklist_code': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'checklist_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'inspection_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'applicable_to': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2
            }),
            'checklist_items': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 6,
                'placeholder': 'Enter JSON array of checklist items'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'version': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'effective_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
            'revision_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_fields = ['checklist_code', 'checklist_name', 'inspection_type', 'applicable_to', 'checklist_items', 'is_active']
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False
