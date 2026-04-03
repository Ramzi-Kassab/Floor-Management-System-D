"""
Compliance App Views - Complete Implementation
All 50 CRUD views for 10 models (5 views each)
Production-ready for ARDT Floor Management System
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.utils import timezone

from .forms import (
    ComplianceRequirementForm, QualityControlForm, NonConformanceForm,
    AuditTrailForm, DocumentControlForm, TrainingRecordForm, CertificationForm,
    ComplianceReportForm, QualityMetricForm, InspectionChecklistForm
)
from .models import (
    ComplianceRequirement, QualityControl, NonConformance,
    AuditTrail, DocumentControl, TrainingRecord, Certification,
    ComplianceReport, QualityMetric, InspectionChecklist
)


# ============================================================================
# ComplianceRequirement Views (5 views)
# ============================================================================

class ComplianceRequirementListView(LoginRequiredMixin, ListView):
    """List all compliance requirements with filtering and search"""
    model = ComplianceRequirement
    template_name = "compliance/compliancerequirement_list.html"
    context_object_name = "requirements"
    paginate_by = 25

    def get_queryset(self):
        queryset = ComplianceRequirement.objects.select_related(
            'responsible_person', 'last_assessed_by', 'created_by', 'supersedes'
        ).prefetch_related('related_requirements')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(requirement_code__icontains=search) |
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        req_type = self.request.GET.get('requirement_type')
        if req_type:
            queryset = queryset.filter(requirement_type=req_type)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        compliance_status = self.request.GET.get('compliance_status')
        if compliance_status:
            queryset = queryset.filter(compliance_status=compliance_status)

        risk_level = self.request.GET.get('risk_level')
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)

        sort_by = self.request.GET.get('sort_by', 'requirement_code')
        queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Compliance Requirements'
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ComplianceRequirementDetailView(LoginRequiredMixin, DetailView):
    """View complete details of a compliance requirement"""
    model = ComplianceRequirement
    template_name = "compliance/compliancerequirement_detail.html"
    context_object_name = "requirement"

    def get_queryset(self):
        return ComplianceRequirement.objects.select_related(
            'responsible_person', 'last_assessed_by', 'created_by', 'supersedes'
        ).prefetch_related('related_requirements', 'superseded_by_requirements')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"{self.object.requirement_code}"
        if self.object.review_date:
            days_until_review = (self.object.review_date - timezone.now().date()).days
            context['days_until_review'] = days_until_review
            context['review_is_overdue'] = days_until_review < 0
        return context


class ComplianceRequirementCreateView(LoginRequiredMixin, CreateView):
    """Create a new compliance requirement"""
    model = ComplianceRequirement
    form_class = ComplianceRequirementForm
    template_name = "compliance/compliancerequirement_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Requirement '{form.instance.requirement_code}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:compliancerequirement_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Compliance Requirement'
        context['form_title'] = 'New Compliance Requirement'
        context['submit_text'] = 'Create'
        return context


class ComplianceRequirementUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing compliance requirement"""
    model = ComplianceRequirement
    form_class = ComplianceRequirementForm
    template_name = "compliance/compliancerequirement_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Requirement '{form.instance.requirement_code}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:compliancerequirement_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit {self.object.requirement_code}'
        context['form_title'] = 'Edit Compliance Requirement'
        context['submit_text'] = 'Update'
        return context


class ComplianceRequirementDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a compliance requirement"""
    model = ComplianceRequirement
    template_name = "compliance/compliancerequirement_confirm_delete.html"
    success_url = reverse_lazy('compliance:compliancerequirement_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        code = self.object.requirement_code
        messages.success(request, f"Requirement '{code}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# QualityControl Views (5 views)
# ============================================================================

class QualityControlListView(LoginRequiredMixin, ListView):
    """List all quality control inspections"""
    model = QualityControl
    template_name = "compliance/qualitycontrol_list.html"
    context_object_name = "inspections"
    paginate_by = 25

    def get_queryset(self):
        queryset = QualityControl.objects.select_related(
            'work_order', 'drill_bit', 'inspector', 'approved_by'
        )

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(inspection_number__icontains=search) |
                Q(specification_reference__icontains=search)
            )

        inspection_type = self.request.GET.get('inspection_type')
        if inspection_type:
            queryset = queryset.filter(inspection_type=inspection_type)

        result = self.request.GET.get('result')
        if result:
            queryset = queryset.filter(result=result)

        return queryset.order_by('-inspection_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Quality Control Inspections'
        context['search_query'] = self.request.GET.get('q', '')
        return context


class QualityControlDetailView(LoginRequiredMixin, DetailView):
    """View QC inspection details"""
    model = QualityControl
    template_name = "compliance/qualitycontrol_detail.html"
    context_object_name = "inspection"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"QC Inspection {self.object.inspection_number or self.object.id}"
        return context


class QualityControlCreateView(LoginRequiredMixin, CreateView):
    """Create new QC inspection"""
    model = QualityControl
    form_class = QualityControlForm
    template_name = "compliance/qualitycontrol_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "QC inspection created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:qualitycontrol_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create QC Inspection'
        context['form_title'] = 'New Quality Control Inspection'
        context['submit_text'] = 'Create'
        return context


class QualityControlUpdateView(LoginRequiredMixin, UpdateView):
    """Update QC inspection"""
    model = QualityControl
    form_class = QualityControlForm
    template_name = "compliance/qualitycontrol_form.html"

    def form_valid(self, form):
        messages.success(self.request, "QC inspection updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:qualitycontrol_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit QC Inspection {self.object.pk}'
        context['form_title'] = 'Edit Quality Control Inspection'
        context['submit_text'] = 'Update'
        return context


class QualityControlDeleteView(LoginRequiredMixin, DeleteView):
    """Delete QC inspection"""
    model = QualityControl
    template_name = "compliance/qualitycontrol_confirm_delete.html"
    success_url = reverse_lazy('compliance:qualitycontrol_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "QC inspection deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# NonConformance Views (5 views)
# ============================================================================

class NonConformanceListView(LoginRequiredMixin, ListView):
    """List all non-conformance reports"""
    model = NonConformance
    template_name = "compliance/nonconformance_list.html"
    context_object_name = "ncrs"
    paginate_by = 25

    def get_queryset(self):
        queryset = NonConformance.objects.select_related(
            'detected_by', 'responsible_person', 'verified_by'
        )

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(ncr_number__icontains=search) |
                Q(issue_description__icontains=search)
            )

        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-detected_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Non-Conformance Reports'
        context['search_query'] = self.request.GET.get('q', '')
        return context


class NonConformanceDetailView(LoginRequiredMixin, DetailView):
    """View NCR details"""
    model = NonConformance
    template_name = "compliance/nonconformance_detail.html"
    context_object_name = "ncr"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"NCR {self.object.ncr_number or self.object.id}"
        return context


class NonConformanceCreateView(LoginRequiredMixin, CreateView):
    """Create new NCR"""
    model = NonConformance
    form_class = NonConformanceForm
    template_name = "compliance/nonconformance_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "NCR created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:nonconformance_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create NCR'
        context['form_title'] = 'New Non-Conformance Report'
        context['submit_text'] = 'Create'
        return context


class NonConformanceUpdateView(LoginRequiredMixin, UpdateView):
    """Update NCR"""
    model = NonConformance
    form_class = NonConformanceForm
    template_name = "compliance/nonconformance_form.html"

    def form_valid(self, form):
        messages.success(self.request, "NCR updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:nonconformance_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit NCR {self.object.ncr_number or self.object.pk}'
        context['form_title'] = 'Edit Non-Conformance Report'
        context['submit_text'] = 'Update'
        return context


class NonConformanceDeleteView(LoginRequiredMixin, DeleteView):
    """Delete NCR"""
    model = NonConformance
    template_name = "compliance/nonconformance_confirm_delete.html"
    success_url = reverse_lazy('compliance:nonconformance_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "NCR deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# AuditTrail Views (5 views)
# ============================================================================

class AuditTrailListView(LoginRequiredMixin, ListView):
    """List audit trail entries"""
    model = AuditTrail
    template_name = "compliance/audittrail_list.html"
    context_object_name = "entries"
    paginate_by = 50

    def get_queryset(self):
        queryset = AuditTrail.objects.select_related('user')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(model_name__icontains=search) |
                Q(object_repr__icontains=search)
            )

        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)

        return queryset.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Audit Trail'
        context['search_query'] = self.request.GET.get('q', '')
        return context


class AuditTrailDetailView(LoginRequiredMixin, DetailView):
    """View audit entry details"""
    model = AuditTrail
    template_name = "compliance/audittrail_detail.html"
    context_object_name = "entry"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Audit Entry #{self.object.pk}'
        return context


class AuditTrailCreateView(LoginRequiredMixin, CreateView):
    """Create audit entry (manual)"""
    model = AuditTrail
    form_class = AuditTrailForm
    template_name = "compliance/audittrail_form.html"
    success_url = reverse_lazy('compliance:audittrail_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Audit Entry'
        context['form_title'] = 'New Audit Trail Entry'
        context['submit_text'] = 'Create'
        return context


class AuditTrailUpdateView(LoginRequiredMixin, UpdateView):
    """Update audit entry"""
    model = AuditTrail
    form_class = AuditTrailForm
    template_name = "compliance/audittrail_form.html"
    success_url = reverse_lazy('compliance:audittrail_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Audit Entry #{self.object.pk}'
        context['form_title'] = 'Edit Audit Trail Entry'
        context['submit_text'] = 'Update'
        return context


class AuditTrailDeleteView(LoginRequiredMixin, DeleteView):
    """Delete audit entry"""
    model = AuditTrail
    template_name = "compliance/audittrail_confirm_delete.html"
    success_url = reverse_lazy('compliance:audittrail_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Audit entry deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# DocumentControl Views (5 views)
# ============================================================================

class DocumentControlListView(LoginRequiredMixin, ListView):
    """List controlled documents"""
    model = DocumentControl
    template_name = "compliance/documentcontrol_list.html"
    context_object_name = "documents"
    paginate_by = 25

    def get_queryset(self):
        queryset = DocumentControl.objects.select_related('author', 'reviewer', 'approver')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(document_number__icontains=search) |
                Q(title__icontains=search) |
                Q(keywords__icontains=search)
            )

        document_type = self.request.GET.get('document_type')
        if document_type:
            queryset = queryset.filter(document_type=document_type)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-revision_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Document Control'
        context['search_query'] = self.request.GET.get('q', '')
        return context


class DocumentControlDetailView(LoginRequiredMixin, DetailView):
    """View document details"""
    model = DocumentControl
    template_name = "compliance/documentcontrol_detail.html"
    context_object_name = "document"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'{self.object.document_number}'
        return context


class DocumentControlCreateView(LoginRequiredMixin, CreateView):
    """Create controlled document"""
    model = DocumentControl
    form_class = DocumentControlForm
    template_name = "compliance/documentcontrol_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Document '{form.instance.document_number}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:documentcontrol_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Document'
        context['form_title'] = 'New Controlled Document'
        context['submit_text'] = 'Create'
        return context


class DocumentControlUpdateView(LoginRequiredMixin, UpdateView):
    """Update document"""
    model = DocumentControl
    form_class = DocumentControlForm
    template_name = "compliance/documentcontrol_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Document '{form.instance.document_number}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:documentcontrol_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit {self.object.document_number}'
        context['form_title'] = 'Edit Controlled Document'
        context['submit_text'] = 'Update'
        return context


class DocumentControlDeleteView(LoginRequiredMixin, DeleteView):
    """Delete document"""
    model = DocumentControl
    template_name = "compliance/documentcontrol_confirm_delete.html"
    success_url = reverse_lazy('compliance:documentcontrol_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(request, f"Document '{self.object.document_number}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# TrainingRecord Views (5 views)
# ============================================================================

class TrainingRecordListView(LoginRequiredMixin, ListView):
    """List training records"""
    model = TrainingRecord
    template_name = "compliance/trainingrecord_list.html"
    context_object_name = "trainings"
    paginate_by = 25

    def get_queryset(self):
        queryset = TrainingRecord.objects.select_related('employee', 'created_by')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(training_title__icontains=search) |
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search)
            )

        training_type = self.request.GET.get('training_type')
        if training_type:
            queryset = queryset.filter(training_type=training_type)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-training_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Training Records'
        context['search_query'] = self.request.GET.get('q', '')
        return context


class TrainingRecordDetailView(LoginRequiredMixin, DetailView):
    """View training record details"""
    model = TrainingRecord
    template_name = "compliance/trainingrecord_detail.html"
    context_object_name = "training"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'{self.object.training_title}'
        return context


class TrainingRecordCreateView(LoginRequiredMixin, CreateView):
    """Create training record"""
    model = TrainingRecord
    form_class = TrainingRecordForm
    template_name = "compliance/trainingrecord_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Training record created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:trainingrecord_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Training Record'
        context['form_title'] = 'New Training Record'
        context['submit_text'] = 'Create'
        return context


class TrainingRecordUpdateView(LoginRequiredMixin, UpdateView):
    """Update training record"""
    model = TrainingRecord
    form_class = TrainingRecordForm
    template_name = "compliance/trainingrecord_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Training record updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:trainingrecord_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit Training: {self.object.training_title}'
        context['form_title'] = 'Edit Training Record'
        context['submit_text'] = 'Update'
        return context


class TrainingRecordDeleteView(LoginRequiredMixin, DeleteView):
    """Delete training record"""
    model = TrainingRecord
    template_name = "compliance/trainingrecord_confirm_delete.html"
    success_url = reverse_lazy('compliance:trainingrecord_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Training record deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# Certification Views (5 views)
# ============================================================================

class CertificationListView(LoginRequiredMixin, ListView):
    """List certifications"""
    model = Certification
    template_name = "compliance/certification_list.html"
    context_object_name = "certifications"
    paginate_by = 25

    def get_queryset(self):
        queryset = Certification.objects.select_related('employee', 'verified_by')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(certification_name__icontains=search) |
                Q(certification_number__icontains=search) |
                Q(employee__first_name__icontains=search)
            )

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-expiry_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Certifications'
        context['search_query'] = self.request.GET.get('q', '')
        return context


class CertificationDetailView(LoginRequiredMixin, DetailView):
    """View certification details"""
    model = Certification
    template_name = "compliance/certification_detail.html"
    context_object_name = "certification"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'{self.object.certification_name}'
        return context


class CertificationCreateView(LoginRequiredMixin, CreateView):
    """Create certification"""
    model = Certification
    form_class = CertificationForm
    template_name = "compliance/certification_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Certification created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:certification_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Certification'
        context['form_title'] = 'New Certification'
        context['submit_text'] = 'Create'
        return context


class CertificationUpdateView(LoginRequiredMixin, UpdateView):
    """Update certification"""
    model = Certification
    form_class = CertificationForm
    template_name = "compliance/certification_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Certification updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:certification_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit {self.object.certification_name}'
        context['form_title'] = 'Edit Certification'
        context['submit_text'] = 'Update'
        return context


class CertificationDeleteView(LoginRequiredMixin, DeleteView):
    """Delete certification"""
    model = Certification
    template_name = "compliance/certification_confirm_delete.html"
    success_url = reverse_lazy('compliance:certification_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Certification deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# ComplianceReport Views (5 views)
# ============================================================================

class ComplianceReportListView(LoginRequiredMixin, ListView):
    """List compliance reports"""
    model = ComplianceReport
    template_name = "compliance/compliancereport_list.html"
    context_object_name = "reports"
    paginate_by = 25

    def get_queryset(self):
        queryset = ComplianceReport.objects.select_related('prepared_by', 'reviewed_by', 'approved_by')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(report_number__icontains=search) |
                Q(title__icontains=search)
            )

        report_type = self.request.GET.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-reporting_period_end')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Compliance Reports'
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ComplianceReportDetailView(LoginRequiredMixin, DetailView):
    """View report details"""
    model = ComplianceReport
    template_name = "compliance/compliancereport_detail.html"
    context_object_name = "report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'{self.object.title}'
        return context


class ComplianceReportCreateView(LoginRequiredMixin, CreateView):
    """Create compliance report"""
    model = ComplianceReport
    form_class = ComplianceReportForm
    template_name = "compliance/compliancereport_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Report created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:compliancereport_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Compliance Report'
        context['form_title'] = 'New Compliance Report'
        context['submit_text'] = 'Create'
        return context


class ComplianceReportUpdateView(LoginRequiredMixin, UpdateView):
    """Update report"""
    model = ComplianceReport
    form_class = ComplianceReportForm
    template_name = "compliance/compliancereport_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Report updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:compliancereport_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit {self.object.title}'
        context['form_title'] = 'Edit Compliance Report'
        context['submit_text'] = 'Update'
        return context


class ComplianceReportDeleteView(LoginRequiredMixin, DeleteView):
    """Delete report"""
    model = ComplianceReport
    template_name = "compliance/compliancereport_confirm_delete.html"
    success_url = reverse_lazy('compliance:compliancereport_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Report deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# QualityMetric Views (5 views)
# ============================================================================

class QualityMetricListView(LoginRequiredMixin, ListView):
    """List quality metrics"""
    model = QualityMetric
    template_name = "compliance/qualitymetric_list.html"
    context_object_name = "metrics"
    paginate_by = 25

    def get_queryset(self):
        queryset = QualityMetric.objects.select_related('measured_by', 'created_by')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(Q(metric_name__icontains=search))

        metric_type = self.request.GET.get('metric_type')
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-measurement_period')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Quality Metrics'
        context['search_query'] = self.request.GET.get('q', '')
        return context


class QualityMetricDetailView(LoginRequiredMixin, DetailView):
    """View metric details"""
    model = QualityMetric
    template_name = "compliance/qualitymetric_detail.html"
    context_object_name = "metric"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'{self.object.metric_name}'
        return context


class QualityMetricCreateView(LoginRequiredMixin, CreateView):
    """Create quality metric"""
    model = QualityMetric
    form_class = QualityMetricForm
    template_name = "compliance/qualitymetric_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Metric created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:qualitymetric_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Quality Metric'
        context['form_title'] = 'New Quality Metric'
        context['submit_text'] = 'Create'
        return context


class QualityMetricUpdateView(LoginRequiredMixin, UpdateView):
    """Update metric"""
    model = QualityMetric
    form_class = QualityMetricForm
    template_name = "compliance/qualitymetric_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Metric updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:qualitymetric_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit {self.object.metric_name}'
        context['form_title'] = 'Edit Quality Metric'
        context['submit_text'] = 'Update'
        return context


class QualityMetricDeleteView(LoginRequiredMixin, DeleteView):
    """Delete metric"""
    model = QualityMetric
    template_name = "compliance/qualitymetric_confirm_delete.html"
    success_url = reverse_lazy('compliance:qualitymetric_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Metric deleted successfully.")
        return super().delete(request, *args, **kwargs)


# ============================================================================
# InspectionChecklist Views (5 views)
# ============================================================================

class InspectionChecklistListView(LoginRequiredMixin, ListView):
    """List inspection checklists"""
    model = InspectionChecklist
    template_name = "compliance/inspectionchecklist_list.html"
    context_object_name = "checklists"
    paginate_by = 25

    def get_queryset(self):
        queryset = InspectionChecklist.objects.all()

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(checklist_code__icontains=search) |
                Q(checklist_name__icontains=search)
            )

        inspection_type = self.request.GET.get('inspection_type')
        if inspection_type:
            queryset = queryset.filter(inspection_type=inspection_type)

        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=(is_active == 'true'))

        return queryset.order_by('checklist_code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Inspection Checklists'
        context['search_query'] = self.request.GET.get('q', '')
        return context


class InspectionChecklistDetailView(LoginRequiredMixin, DetailView):
    """View checklist details"""
    model = InspectionChecklist
    template_name = "compliance/inspectionchecklist_detail.html"
    context_object_name = "checklist"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'{self.object.checklist_code}'
        return context


class InspectionChecklistCreateView(LoginRequiredMixin, CreateView):
    """Create inspection checklist"""
    model = InspectionChecklist
    form_class = InspectionChecklistForm
    template_name = "compliance/inspectionchecklist_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Checklist created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:inspectionchecklist_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Inspection Checklist'
        context['form_title'] = 'New Inspection Checklist'
        context['submit_text'] = 'Create'
        return context


class InspectionChecklistUpdateView(LoginRequiredMixin, UpdateView):
    """Update checklist"""
    model = InspectionChecklist
    form_class = InspectionChecklistForm
    template_name = "compliance/inspectionchecklist_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Checklist updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('compliance:inspectionchecklist_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Edit {self.object.checklist_code}'
        context['form_title'] = 'Edit Inspection Checklist'
        context['submit_text'] = 'Update'
        return context


class InspectionChecklistDeleteView(LoginRequiredMixin, DeleteView):
    """Delete checklist"""
    model = InspectionChecklist
    template_name = "compliance/inspectionchecklist_confirm_delete.html"
    success_url = reverse_lazy('compliance:inspectionchecklist_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Checklist deleted successfully.")
        return super().delete(request, *args, **kwargs)
