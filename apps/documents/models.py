"""
ARDT FMS - Documents Models
Version: 5.4

Tables:
- document_categories (P1)
- documents (P1)
"""

from django.conf import settings
from django.db import models


class DocumentCategory(models.Model):
    """
    🟢 P1: Categories for documents.
    """

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "document_categories"
        ordering = ["code"]
        verbose_name = "Document Category"
        verbose_name_plural = "Document Categories"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Document(models.Model):
    """
    🟢 P1: Document management.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        OBSOLETE = "OBSOLETE", "Obsolete"
        ARCHIVED = "ARCHIVED", "Archived"

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")

    # File
    file = models.FileField(upload_to="documents/")
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)

    # Version control
    version = models.CharField(max_length=20, default="1.0")
    revision_date = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # Metadata
    description = models.TextField(blank=True)
    keywords = models.CharField(max_length=500, blank=True)

    # Access control
    is_confidential = models.BooleanField(default=False)
    access_roles = models.ManyToManyField("accounts.Role", blank=True, related_name="accessible_documents")

    # Ownership
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="owned_documents")

    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_documents"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Expiry
    expires_at = models.DateField(null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_documents"
    )

    class Meta:
        db_table = "documents"
        ordering = ["-created_at"]
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return f"{self.code} - {self.name}"
