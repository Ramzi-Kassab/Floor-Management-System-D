"""
ARDT FMS - Documents Views
Version: 5.4 - Sprint 2

Views for document management.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.mixins import ManagerRequiredMixin

from .forms import DocumentCategoryForm, DocumentForm
from .models import Document, DocumentCategory

# =============================================================================
# DOCUMENT CATEGORY VIEWS
# =============================================================================


class CategoryListView(LoginRequiredMixin, ListView):
    """List all document categories."""

    model = DocumentCategory
    template_name = "documents/category_list.html"
    context_object_name = "categories"
    paginate_by = 25

    def get_queryset(self):
        queryset = DocumentCategory.objects.annotate(document_count=Count("documents"))

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(name__icontains=search) | Q(description__icontains=search)
            )

        # Filter by active status
        is_active = self.request.GET.get("is_active")
        if is_active == "true":
            queryset = queryset.filter(is_active=True)
        elif is_active == "false":
            queryset = queryset.filter(is_active=False)

        return queryset.order_by("code")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Document Categories"
        context["total_categories"] = DocumentCategory.objects.count()
        context["active_categories"] = DocumentCategory.objects.filter(is_active=True).count()
        context["search_query"] = self.request.GET.get("q", "")
        return context


class CategoryDetailView(LoginRequiredMixin, DetailView):
    """View category details with documents."""

    model = DocumentCategory
    template_name = "documents/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object
        context["page_title"] = f"Category: {category.name}"
        context["documents"] = category.documents.all().order_by("-created_at")[:20]
        context["children"] = category.children.filter(is_active=True)
        context["document_count"] = category.documents.count()
        return context


class CategoryCreateView(ManagerRequiredMixin, CreateView):
    """Create a new document category."""

    model = DocumentCategory
    form_class = DocumentCategoryForm
    template_name = "documents/category_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Category"
        context["submit_text"] = "Create Category"
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("documents:category_detail", kwargs={"pk": self.object.pk})


class CategoryUpdateView(ManagerRequiredMixin, UpdateView):
    """Update an existing document category."""

    model = DocumentCategory
    form_class = DocumentCategoryForm
    template_name = "documents/category_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Category: {self.object.name}"
        context["submit_text"] = "Update Category"
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("documents:category_detail", kwargs={"pk": self.object.pk})


# =============================================================================
# DOCUMENT VIEWS
# =============================================================================


class DocumentListView(LoginRequiredMixin, ListView):
    """List all documents with search and filtering."""

    model = Document
    template_name = "documents/document_list.html"
    context_object_name = "documents"
    paginate_by = 25

    def get_queryset(self):
        queryset = Document.objects.select_related("category", "owner", "created_by", "approved_by")

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search)
                | Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(keywords__icontains=search)
            )

        # Filter by category
        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filter by confidential
        is_confidential = self.request.GET.get("confidential")
        if is_confidential == "true":
            queryset = queryset.filter(is_confidential=True)
        elif is_confidential == "false":
            queryset = queryset.filter(is_confidential=False)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Documents"
        context["categories"] = DocumentCategory.objects.filter(is_active=True).order_by("name")
        context["statuses"] = Document.Status.choices
        context["search_query"] = self.request.GET.get("q", "")
        context["current_category"] = self.request.GET.get("category", "")
        context["current_status"] = self.request.GET.get("status", "")

        # Stats
        context["stats"] = {
            "total": Document.objects.count(),
            "active": Document.objects.filter(status="ACTIVE").count(),
            "draft": Document.objects.filter(status="DRAFT").count(),
            "confidential": Document.objects.filter(is_confidential=True).count(),
        }
        return context


class DocumentDetailView(LoginRequiredMixin, DetailView):
    """View document details."""

    model = Document
    template_name = "documents/document_detail.html"
    context_object_name = "document"

    def get_queryset(self):
        return Document.objects.select_related("category", "owner", "created_by", "approved_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doc = self.object
        context["page_title"] = f"Document: {doc.name}"

        # Check if file is previewable
        previewable_types = ["application/pdf", "image/jpeg", "image/png", "image/gif"]
        context["is_previewable"] = doc.mime_type in previewable_types

        # Check if expired
        if doc.expires_at:
            context["is_expired"] = doc.expires_at < timezone.now().date()
        else:
            context["is_expired"] = False

        # Format file size
        context["formatted_size"] = self.format_file_size(doc.file_size)

        return context

    def format_file_size(self, size_bytes):
        """Format file size to human readable string."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


class DocumentCreateView(ManagerRequiredMixin, CreateView):
    """Upload a new document."""

    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Upload Document"
        context["submit_text"] = "Upload Document"
        return context

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Document "{form.instance.name}" uploaded successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("documents:document_detail", kwargs={"pk": self.object.pk})


class DocumentUpdateView(ManagerRequiredMixin, UpdateView):
    """Update an existing document."""

    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Document: {self.object.name}"
        context["submit_text"] = "Update Document"
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Document "{form.instance.name}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("documents:document_detail", kwargs={"pk": self.object.pk})


# =============================================================================
# DOCUMENT ACTIONS
# =============================================================================


@login_required
def document_download(request, pk):
    """Download a document file."""
    document = get_object_or_404(Document, pk=pk)

    if not document.file:
        raise Http404("Document file not found")

    response = FileResponse(document.file.open("rb"), as_attachment=True, filename=document.file.name.split("/")[-1])
    return response


@login_required
def document_preview(request, pk):
    """Preview a document (for PDF and images)."""
    document = get_object_or_404(Document, pk=pk)

    if not document.file:
        raise Http404("Document file not found")

    previewable_types = ["application/pdf", "image/jpeg", "image/png", "image/gif"]
    if document.mime_type not in previewable_types:
        messages.warning(request, "This document type cannot be previewed. Download instead.")
        return redirect("documents:document_detail", pk=pk)

    response = FileResponse(document.file.open("rb"), content_type=document.mime_type)
    return response


@login_required
def document_approve(request, pk):
    """Approve a document (change status to ACTIVE)."""
    document = get_object_or_404(Document, pk=pk)

    if request.method == "POST":
        document.status = Document.Status.ACTIVE
        document.approved_by = request.user
        document.approved_at = timezone.now()
        document.save()
        messages.success(request, f'Document "{document.name}" approved and activated.')

    return redirect("documents:document_detail", pk=pk)


@login_required
def document_archive(request, pk):
    """Archive a document."""
    document = get_object_or_404(Document, pk=pk)

    if request.method == "POST":
        document.status = Document.Status.ARCHIVED
        document.save()
        messages.success(request, f'Document "{document.name}" archived.')

    return redirect("documents:document_detail", pk=pk)
