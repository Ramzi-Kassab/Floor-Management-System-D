"""
ARDT FMS - Quality Views
Version: 5.4 - Sprint 3

Views for Inspection and NCR management.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from apps.accounts.mixins import RoleRequiredMixin

from .forms import InspectionForm, InspectionResultForm, NCRDispositionForm, NCRForm, NCRPhotoForm
from .models import NCR, Inspection, NCRPhoto


# =============================================================================
# INSPECTION VIEWS
# =============================================================================


class InspectionListView(LoginRequiredMixin, ListView):
    """List all inspections with filtering."""

    model = Inspection
    template_name = "quality/inspection_list.html"
    context_object_name = "inspections"
    paginate_by = 25

    def get_queryset(self):
        queryset = Inspection.objects.select_related(
            "work_order", "drill_bit", "inspected_by", "created_by"
        ).order_by("-scheduled_date", "-created_at")

        # Search filter
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(inspection_number__icontains=search)
                | Q(work_order__wo_number__icontains=search)
                | Q(findings__icontains=search)
            )

        # Type filter
        inspection_type = self.request.GET.get("type")
        if inspection_type:
            queryset = queryset.filter(inspection_type=inspection_type)

        # Status filter
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Inspections"
        context["search_query"] = self.request.GET.get("q", "")
        context["current_type"] = self.request.GET.get("type", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["type_choices"] = Inspection.InspectionType.choices
        context["status_choices"] = Inspection.Status.choices
        return context


class InspectionDetailView(LoginRequiredMixin, DetailView):
    """View inspection details."""

    model = Inspection
    template_name = "quality/inspection_detail.html"
    context_object_name = "inspection"

    def get_queryset(self):
        return Inspection.objects.select_related(
            "work_order", "drill_bit", "procedure", "inspected_by", "approved_by", "created_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Inspection {self.object.inspection_number}"
        context["ncrs"] = self.object.ncrs.select_related("detected_by").order_by("-detected_at")
        return context


class InspectionCreateView(LoginRequiredMixin, CreateView):
    """Create a new inspection."""

    model = Inspection
    form_class = InspectionForm
    template_name = "quality/inspection_form.html"
    success_url = reverse_lazy("quality:inspection_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Inspection"
        context["submit_text"] = "Create Inspection"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.inspection_number = self.generate_inspection_number()
        messages.success(self.request, f"Inspection {form.instance.inspection_number} created successfully.")
        return super().form_valid(form)

    def generate_inspection_number(self):
        """Generate unique inspection number."""
        prefix = "INS"
        year = timezone.now().year
        last_inspection = Inspection.objects.filter(
            inspection_number__startswith=f"{prefix}-{year}-"
        ).order_by("-id").first()

        if last_inspection:
            try:
                last_num = int(last_inspection.inspection_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}-{year}-{str(next_num).zfill(4)}"


class InspectionUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing inspection."""

    model = Inspection
    form_class = InspectionForm
    template_name = "quality/inspection_form.html"

    def get_success_url(self):
        return reverse_lazy("quality:inspection_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Inspection {self.object.inspection_number}"
        context["submit_text"] = "Update Inspection"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Inspection {self.object.inspection_number} updated successfully.")
        return super().form_valid(form)


class InspectionCompleteView(LoginRequiredMixin, UpdateView):
    """Complete an inspection with results."""

    model = Inspection
    form_class = InspectionResultForm
    template_name = "quality/inspection_complete.html"

    def get_success_url(self):
        return reverse_lazy("quality:inspection_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Complete Inspection {self.object.inspection_number}"
        context["submit_text"] = "Record Results"
        return context

    def form_valid(self, form):
        form.instance.inspected_by = self.request.user
        form.instance.inspected_at = timezone.now()
        messages.success(self.request, f"Inspection {self.object.inspection_number} completed.")
        return super().form_valid(form)


# =============================================================================
# NCR VIEWS
# =============================================================================


class NCRListView(LoginRequiredMixin, ListView):
    """List all NCRs with filtering."""

    model = NCR
    template_name = "quality/ncr_list.html"
    context_object_name = "ncrs"
    paginate_by = 25

    def get_queryset(self):
        queryset = NCR.objects.select_related(
            "work_order", "inspection", "drill_bit", "detected_by", "disposition_by"
        ).order_by("-detected_at")

        # Search filter
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(ncr_number__icontains=search)
                | Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(work_order__wo_number__icontains=search)
            )

        # Severity filter
        severity = self.request.GET.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)

        # Status filter
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Non-Conformance Reports"
        context["search_query"] = self.request.GET.get("q", "")
        context["current_severity"] = self.request.GET.get("severity", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["severity_choices"] = NCR.Severity.choices
        context["status_choices"] = NCR.Status.choices
        return context


class NCRDetailView(LoginRequiredMixin, DetailView):
    """View NCR details."""

    model = NCR
    template_name = "quality/ncr_detail.html"
    context_object_name = "ncr"

    def get_queryset(self):
        return NCR.objects.select_related(
            "work_order",
            "inspection",
            "drill_bit",
            "detected_by",
            "investigated_by",
            "disposition_by",
            "closed_by",
            "created_by",
            "rework_work_order",
        ).prefetch_related("photos")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"NCR {self.object.ncr_number}"
        context["photos"] = self.object.photos.all()
        context["photo_form"] = NCRPhotoForm()
        return context


class NCRCreateView(LoginRequiredMixin, CreateView):
    """Create a new NCR."""

    model = NCR
    form_class = NCRForm
    template_name = "quality/ncr_form.html"
    success_url = reverse_lazy("quality:ncr_list")

    def get_initial(self):
        initial = super().get_initial()
        wo_pk = self.request.GET.get('wo')
        if wo_pk:
            from apps.workorders.models import WorkOrder, DieCheckReport
            wo = WorkOrder.objects.select_related(
                'drill_bit', 'drill_bit__design', 'account'
            ).filter(pk=wo_pk).first()
            if wo:
                initial['work_order'] = wo.pk
                if wo.drill_bit:
                    initial['drill_bit'] = wo.drill_bit.pk
                    serial = wo.drill_bit.serial_number
                else:
                    serial = '?'

                # Build title and description from WO + die check findings
                initial['title'] = f'NCR — WO {wo.wo_number} (S/N {serial})'
                initial['detection_stage'] = 'Production'

                # Find the latest quality issue for this WO to get the summary
                from .models import QualityIssue
                qi = QualityIssue.objects.filter(work_order=wo).order_by('-created_at').first()

                # Find die check findings (section 4 decisions table)
                dc = DieCheckReport.objects.filter(work_order=wo).order_by('-created_at').first()

                desc_parts = [f'WO: {wo.wo_number}', f'Serial: {serial}']
                if wo.account:
                    desc_parts.append(f'Account: {wo.account.name}')
                if wo.drill_bit and wo.drill_bit.design:
                    desc_parts.append(f'Design: {wo.drill_bit.design.mat_no or ""}')

                # Add quality issue summary if exists
                if qi:
                    desc_parts.append(f'\n--- Issue Summary ({qi.issue_number}) ---')
                    desc_parts.append(qi.summary)

                # Add die check findings
                if dc and dc.grid_data:
                    decisions = dc.grid_data.get('decisions', {})
                    if decisions:
                        desc_parts.append('\n--- Die Check Findings ---')
                        for key, dec in decisions.items():
                            if dec.get('decision'):
                                finding = dec.get('finding', '')
                                decision = dec.get('decision', '')
                                remarks = dec.get('remarks', '')
                                line = f'Position {key}: {finding} → {decision}'
                                if remarks:
                                    line += f' ({remarks})'
                                desc_parts.append(line)

                initial['description'] = '\n'.join(desc_parts)

        capa = self.request.GET.get('capa')
        if capa:
            initial['disposition_notes'] = 'CAPA Required'

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create NCR"
        context["submit_text"] = "Create NCR"
        context["is_capa"] = bool(self.request.GET.get('capa'))
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.detected_by = self.request.user
        form.instance.detected_at = timezone.now()
        form.instance.ncr_number = self.generate_ncr_number()
        form.instance.status = NCR.Status.OPEN
        messages.success(self.request, f"NCR {form.instance.ncr_number} created successfully.")
        return super().form_valid(form)

    def generate_ncr_number(self):
        """Generate unique NCR number."""
        prefix = "NCR"
        year = timezone.now().year
        last_ncr = NCR.objects.filter(
            ncr_number__startswith=f"{prefix}-{year}-"
        ).order_by("-id").first()

        if last_ncr:
            try:
                last_num = int(last_ncr.ncr_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}-{year}-{str(next_num).zfill(4)}"


class NCRUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing NCR."""

    model = NCR
    form_class = NCRForm
    template_name = "quality/ncr_form.html"

    def get_success_url(self):
        return reverse_lazy("quality:ncr_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit NCR {self.object.ncr_number}"
        context["submit_text"] = "Update NCR"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"NCR {self.object.ncr_number} updated successfully.")
        return super().form_valid(form)


class NCRDispositionView(LoginRequiredMixin, UpdateView):
    """Update NCR disposition and close."""

    model = NCR
    form_class = NCRDispositionForm
    template_name = "quality/ncr_disposition.html"

    def get_success_url(self):
        return reverse_lazy("quality:ncr_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Disposition NCR {self.object.ncr_number}"
        context["submit_text"] = "Update Disposition"
        return context

    def form_valid(self, form):
        if form.instance.status == NCR.Status.CLOSED:
            form.instance.closed_by = self.request.user
            form.instance.closed_at = timezone.now()
        if form.cleaned_data.get("disposition") and not form.instance.disposition_by:
            form.instance.disposition_by = self.request.user
            form.instance.disposition_date = timezone.now().date()
        messages.success(self.request, f"NCR {self.object.ncr_number} disposition updated.")
        return super().form_valid(form)


class NCRPhotoUploadView(LoginRequiredMixin, View):
    """Upload a photo to an NCR."""

    def post(self, request, pk):
        ncr = get_object_or_404(NCR, pk=pk)
        form = NCRPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.ncr = ncr
            photo.taken_by = request.user
            photo.save()
            messages.success(request, "Photo uploaded successfully.")
        else:
            messages.error(request, "Failed to upload photo.")
        return redirect("quality:ncr_detail", pk=pk)


class NCRPhotoDeleteView(LoginRequiredMixin, View):
    """Delete a photo from an NCR."""

    def post(self, request, pk, photo_pk):
        photo = get_object_or_404(NCRPhoto, pk=photo_pk, ncr_id=pk)
        photo.delete()
        messages.success(request, "Photo deleted.")
        return redirect("quality:ncr_detail", pk=pk)


# =============================================================================
# QUALITY ISSUES (Reported from Die Check, Evaluations, Router Steps)
# =============================================================================

class QualityIssueListView(LoginRequiredMixin, ListView):
    """List all quality issues with filters."""
    template_name = "quality/quality_issue_list.html"
    context_object_name = "issues"
    paginate_by = 25

    def get_queryset(self):
        from .models import QualityIssue
        qs = QualityIssue.objects.select_related(
            'work_order', 'drill_bit', 'reported_by', 'decided_by', 'ncr'
        ).order_by('-created_at')

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import QualityIssue
        ctx['page_title'] = 'Quality Issues'
        ctx['status_choices'] = QualityIssue.Status.choices
        ctx['current_status'] = self.request.GET.get('status', '')
        ctx['open_count'] = QualityIssue.objects.filter(status='OPEN').count()
        return ctx


class QualityIssueDetailView(LoginRequiredMixin, DetailView):
    """Quality issue detail with decision form."""
    template_name = "quality/quality_issue_detail.html"
    context_object_name = "issue"

    def get_queryset(self):
        from .models import QualityIssue
        return QualityIssue.objects.select_related(
            'work_order', 'drill_bit', 'reported_by', 'decided_by', 'ncr'
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .models import QualityIssue, QualityIssueAction
        ctx['page_title'] = f'Issue {self.object.issue_number}'
        ctx['status_choices'] = QualityIssue.Status.choices
        ctx['actions'] = self.object.actions.select_related('performed_by', 'ncr').order_by('performed_at')
        return ctx

    def post(self, request, pk):
        """Handle quality action — multiple actions can be taken on same issue."""
        from .models import QualityIssue, QualityIssueAction

        issue = get_object_or_404(QualityIssue, pk=pk)
        action_type = request.POST.get('action_type', '')
        notes = request.POST.get('notes', '').strip()

        if not action_type:
            messages.error(request, 'Please select an action.')
            return redirect('quality:quality_issue_detail', pk=pk)

        # Create the action record
        action = QualityIssueAction.objects.create(
            issue=issue,
            action_type=action_type,
            notes=notes,
            performed_by=request.user,
        )

        # Update issue status based on action
        status_map = {
            'ACCEPT': 'ACCEPTED',
            'TECHNICAL_ACCEPT': 'ACCEPTED',
            'CREATE_NCR': 'NCR_CREATED',
            'CREATE_NCR_CAPA': 'NCR_CREATED',
            'REWORK': 'REWORK',
            'TECHNICAL_REWORK': 'REWORK',
            'INFORM_TECHNICAL': 'IN_REVIEW',
            'INFORM_CUSTOMER': 'IN_REVIEW',
            'CLOSE': 'CLOSED',
        }
        new_status = status_map.get(action_type)
        if new_status:
            issue.status = new_status
            issue.decided_by = request.user
            issue.decided_at = timezone.now()
            issue.decision_notes = notes
            issue.save()

        # Notify reporter
        try:
            from apps.notifications.services import notify
            action_label = dict(QualityIssueAction.ActionType.choices).get(action_type, action_type)
            notify(
                actor=request.user,
                title=f"{issue.issue_number}: {action_label}",
                message=f"WO: {issue.work_order.wo_number if issue.work_order else '—'}\n{notes}" if notes else f"Action: {action_label}",
                priority="HIGH",
                recipients=issue.reported_by,
                action_url=f'/quality/issues/{issue.pk}/',
                entity_type="QualityIssue",
                entity_id=issue.pk,
                verb="",
            )
        except Exception:
            pass

        # Rework must have NCR
        if action_type == 'REWORK':
            messages.warning(request, 'Rework recorded. You must also create an NCR for this rework.')

        # Redirect to NCR create for NCR actions
        if action_type in ('CREATE_NCR', 'CREATE_NCR_CAPA', 'REWORK'):
            wo_param = f'?wo={issue.work_order_id}' if issue.work_order_id else ''
            capa_param = '&capa=1' if action_type == 'CREATE_NCR_CAPA' else ''
            messages.success(request, f'Action recorded. Create the NCR now.')
            return redirect(f'/quality/ncrs/create/{wo_param}{capa_param}')

        action_label = dict(QualityIssueAction.ActionType.choices).get(action_type, action_type)
        messages.success(request, f'Action recorded: {action_label}')
        return redirect('quality:quality_issue_detail', pk=pk)
