"""
ARDT FMS - Forms Engine Views
Version: 5.4

Dynamic form builder views.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)

from .models import FormTemplate, FormSection, FormField, FieldType, FormTemplateVersion
from .forms import FormTemplateForm, FormSectionForm, FormFieldForm, FieldTypeForm


# =============================================================================
# FORM TEMPLATE VIEWS
# =============================================================================


class FormTemplateListView(LoginRequiredMixin, ListView):
    """List all form templates with filtering and pagination."""

    model = FormTemplate
    template_name = "forms_engine/template_list.html"
    context_object_name = "templates"
    paginate_by = 20

    def get_queryset(self):
        queryset = FormTemplate.objects.annotate(
            section_count=Count('sections', distinct=True),
            field_count=Count('sections__fields', distinct=True)
        ).order_by('-updated_at')

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Form Templates"
        context["status_choices"] = FormTemplate.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FormTemplateDetailView(LoginRequiredMixin, DetailView):
    """View form template details."""

    model = FormTemplate
    template_name = "forms_engine/template_detail.html"
    context_object_name = "template"

    def get_queryset(self):
        return FormTemplate.objects.prefetch_related(
            'sections__fields__field_type',
            'versions'
        ).select_related('created_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Form Template: {self.object.name}"
        context["field_types"] = FieldType.objects.all()
        return context


class FormTemplateCreateView(LoginRequiredMixin, CreateView):
    """Create a new form template."""

    model = FormTemplate
    form_class = FormTemplateForm
    template_name = "forms_engine/template_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Form Template"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Form template '{form.instance.name}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("forms_engine:template-detail", kwargs={"pk": self.object.pk})


class FormTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing form template."""

    model = FormTemplate
    form_class = FormTemplateForm
    template_name = "forms_engine/template_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit: {self.object.name}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Form template '{form.instance.name}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("forms_engine:template-detail", kwargs={"pk": self.object.pk})


class FormTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a form template."""

    model = FormTemplate
    template_name = "forms_engine/template_confirm_delete.html"
    success_url = reverse_lazy("forms_engine:template-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete: {self.object.name}"
        return context

    def delete(self, request, *args, **kwargs):
        template = self.get_object()
        messages.success(request, f"Form template '{template.name}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


class FormTemplateBuilderView(LoginRequiredMixin, DetailView):
    """Interactive form builder for a template."""

    model = FormTemplate
    template_name = "forms_engine/template_builder.html"
    context_object_name = "template"

    def get_queryset(self):
        return FormTemplate.objects.prefetch_related(
            'sections__fields__field_type'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Form Builder: {self.object.name}"
        context["field_types"] = FieldType.objects.all()
        context["section_form"] = FormSectionForm()
        context["field_form"] = FormFieldForm()
        return context


# =============================================================================
# FORM SECTION VIEWS
# =============================================================================


class FormSectionCreateView(LoginRequiredMixin, CreateView):
    """Add a section to a form template."""

    model = FormSection
    form_class = FormSectionForm
    template_name = "forms_engine/section_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.template_obj = get_object_or_404(FormTemplate, pk=self.kwargs['template_pk'])
        context["page_title"] = f"Add Section to {self.template_obj.name}"
        context["template"] = self.template_obj
        return context

    def form_valid(self, form):
        template = get_object_or_404(FormTemplate, pk=self.kwargs['template_pk'])
        form.instance.template = template
        # Auto-set sequence if not provided
        if not form.instance.sequence:
            max_seq = template.sections.aggregate(max_seq=Max('sequence'))['max_seq']
            form.instance.sequence = (max_seq or 0) + 1
        messages.success(self.request, f"Section '{form.instance.name}' added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("forms_engine:template-builder", kwargs={"pk": self.kwargs['template_pk']})


class FormSectionUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a form section."""

    model = FormSection
    form_class = FormSectionForm
    template_name = "forms_engine/section_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Section: {self.object.name}"
        context["template"] = self.object.template
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Section '{form.instance.name}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("forms_engine:template-builder", kwargs={"pk": self.object.template.pk})


class FormSectionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a form section."""

    model = FormSection
    template_name = "forms_engine/section_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Section: {self.object.name}"
        return context

    def get_success_url(self):
        return reverse_lazy("forms_engine:template-builder", kwargs={"pk": self.object.template.pk})

    def delete(self, request, *args, **kwargs):
        section = self.get_object()
        messages.success(request, f"Section '{section.name}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


# =============================================================================
# FORM FIELD VIEWS
# =============================================================================


class FormFieldCreateView(LoginRequiredMixin, CreateView):
    """Add a field to a section."""

    model = FormField
    form_class = FormFieldForm
    template_name = "forms_engine/field_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limit depends_on_field to fields in the same template
        section = get_object_or_404(FormSection, pk=self.kwargs['section_pk'])
        form.fields['depends_on_field'].queryset = FormField.objects.filter(
            section__template=section.template
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.section = get_object_or_404(FormSection, pk=self.kwargs['section_pk'])
        context["page_title"] = f"Add Field to {self.section.name}"
        context["section"] = self.section
        context["template"] = self.section.template
        return context

    def form_valid(self, form):
        section = get_object_or_404(FormSection, pk=self.kwargs['section_pk'])
        form.instance.section = section
        # Auto-set sequence if not provided
        if not form.instance.sequence:
            max_seq = section.fields.aggregate(max_seq=Max('sequence'))['max_seq']
            form.instance.sequence = (max_seq or 0) + 1
        messages.success(self.request, f"Field '{form.instance.label}' added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        section = get_object_or_404(FormSection, pk=self.kwargs['section_pk'])
        return reverse_lazy("forms_engine:template-builder", kwargs={"pk": section.template.pk})


class FormFieldUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a form field."""

    model = FormField
    form_class = FormFieldForm
    template_name = "forms_engine/field_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limit depends_on_field to fields in the same template (excluding self)
        form.fields['depends_on_field'].queryset = FormField.objects.filter(
            section__template=self.object.section.template
        ).exclude(pk=self.object.pk)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Field: {self.object.label}"
        context["section"] = self.object.section
        context["template"] = self.object.section.template
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Field '{form.instance.label}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("forms_engine:template-builder", kwargs={"pk": self.object.section.template.pk})


class FormFieldDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a form field."""

    model = FormField
    template_name = "forms_engine/field_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Field: {self.object.label}"
        return context

    def get_success_url(self):
        return reverse_lazy("forms_engine:template-builder", kwargs={"pk": self.object.section.template.pk})

    def delete(self, request, *args, **kwargs):
        field = self.get_object()
        messages.success(request, f"Field '{field.label}' deleted successfully.")
        return super().delete(request, *args, **kwargs)


# =============================================================================
# FIELD TYPE VIEWS
# =============================================================================


class FieldTypeListView(LoginRequiredMixin, ListView):
    """List all field types."""

    model = FieldType
    template_name = "forms_engine/fieldtype_list.html"
    context_object_name = "field_types"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Field Types"
        return context


class FieldTypeCreateView(LoginRequiredMixin, CreateView):
    """Create a new field type."""

    model = FieldType
    form_class = FieldTypeForm
    template_name = "forms_engine/fieldtype_form.html"
    success_url = reverse_lazy("forms_engine:fieldtype-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Field Type"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Field type '{form.instance.name}' created successfully.")
        return super().form_valid(form)


class FieldTypeUpdateView(LoginRequiredMixin, UpdateView):
    """Update a field type."""

    model = FieldType
    form_class = FieldTypeForm
    template_name = "forms_engine/fieldtype_form.html"
    success_url = reverse_lazy("forms_engine:fieldtype-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Field Type: {self.object.name}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Field type '{form.instance.name}' updated successfully.")
        return super().form_valid(form)


class FieldTypeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a field type."""

    model = FieldType
    template_name = "forms_engine/fieldtype_confirm_delete.html"
    success_url = reverse_lazy("forms_engine:fieldtype-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Field Type: {self.object.name}"
        return context


# =============================================================================
# FORM RENDERING & PREVIEW VIEWS
# =============================================================================


class FormPreviewView(LoginRequiredMixin, DetailView):
    """Preview how a form template will be rendered."""

    model = FormTemplate
    template_name = "forms_engine/form_preview.html"
    context_object_name = "template"

    def get_queryset(self):
        return FormTemplate.objects.prefetch_related(
            'sections__fields__field_type'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Preview: {self.object.name}"
        context["preview_mode"] = True
        return context


# =============================================================================
# HTMX / API VIEWS
# =============================================================================


@login_required
def reorder_sections_htmx(request, pk):
    """HTMX endpoint for reordering sections via drag-and-drop."""
    if request.method == "POST":
        template = get_object_or_404(FormTemplate, pk=pk)
        section_ids = request.POST.getlist('section_ids[]')

        for index, section_id in enumerate(section_ids):
            FormSection.objects.filter(pk=section_id, template=template).update(sequence=index)

        return JsonResponse({"success": True})

    return JsonResponse({"success": False}, status=400)


@login_required
def reorder_fields_htmx(request, pk):
    """HTMX endpoint for reordering fields within a section."""
    if request.method == "POST":
        section = get_object_or_404(FormSection, pk=pk)
        field_ids = request.POST.getlist('field_ids[]')

        for index, field_id in enumerate(field_ids):
            FormField.objects.filter(pk=field_id, section=section).update(sequence=index)

        return JsonResponse({"success": True})

    return JsonResponse({"success": False}, status=400)


@login_required
def duplicate_template(request, pk):
    """Duplicate a form template."""
    if request.method == "POST":
        original = get_object_or_404(FormTemplate, pk=pk)

        # Create new template with unique code
        new_template = FormTemplate.objects.create(
            code=f"{original.code}-COPY",
            name=f"{original.name} (Copy)",
            description=original.description,
            status=FormTemplate.Status.DRAFT,
            created_by=request.user
        )

        # Duplicate sections and fields
        for section in original.sections.all():
            new_section = FormSection.objects.create(
                template=new_template,
                name=section.name,
                description=section.description,
                sequence=section.sequence,
                is_collapsible=section.is_collapsible,
                is_collapsed_default=section.is_collapsed_default
            )

            for field in section.fields.all():
                FormField.objects.create(
                    section=new_section,
                    field_type=field.field_type,
                    name=field.name,
                    label=field.label,
                    placeholder=field.placeholder,
                    help_text=field.help_text,
                    is_required=field.is_required,
                    min_length=field.min_length,
                    max_length=field.max_length,
                    min_value=field.min_value,
                    max_value=field.max_value,
                    regex_pattern=field.regex_pattern,
                    validation_message=field.validation_message,
                    options=field.options,
                    default_value=field.default_value,
                    sequence=field.sequence,
                    width=field.width,
                    is_readonly=field.is_readonly,
                    is_hidden=field.is_hidden
                )

        messages.success(request, f"Form template duplicated as '{new_template.name}'.")
        return redirect("forms_engine:template-detail", pk=new_template.pk)

    return redirect("forms_engine:template-list")


@login_required
def activate_template(request, pk):
    """Activate a form template."""
    if request.method == "POST":
        template = get_object_or_404(FormTemplate, pk=pk)
        template.status = FormTemplate.Status.ACTIVE
        template.save()
        messages.success(request, f"Form template '{template.name}' activated.")

    return redirect("forms_engine:template-detail", pk=pk)


@login_required
def deactivate_template(request, pk):
    """Deactivate a form template."""
    if request.method == "POST":
        template = get_object_or_404(FormTemplate, pk=pk)
        template.status = FormTemplate.Status.DRAFT
        template.save()
        messages.success(request, f"Form template '{template.name}' deactivated.")

    return redirect("forms_engine:template-detail", pk=pk)
