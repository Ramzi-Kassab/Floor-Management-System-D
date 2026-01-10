"""
Cutter Map Models

Models for managing cutter map PDF documents and their data.
Integrates with the Technology app for Design/BOM relationships.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class CutterMapDocument(models.Model):
    """
    Stores uploaded and generated cutter map PDF documents.
    Links to Design when synced to ERP.
    """

    class Status(models.TextChoices):
        UPLOADED = "UPLOADED", "Uploaded"
        EXTRACTED = "EXTRACTED", "Data Extracted"
        EDITED = "EDITED", "Edited"
        GENERATED = "GENERATED", "PDF Generated"
        SYNCED = "SYNCED", "Synced to ERP"

    # File storage
    original_pdf = models.FileField(
        upload_to='cutter_maps/originals/%Y/%m/',
        verbose_name='Original PDF'
    )
    generated_pdf = models.FileField(
        upload_to='cutter_maps/generated/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Generated PDF'
    )
    generated_ppt = models.FileField(
        upload_to='cutter_maps/generated/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Generated PPT'
    )

    # Extracted data stored as JSON
    extracted_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Extracted Data',
        help_text='JSON data extracted from the original PDF'
    )
    edited_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Edited Data',
        help_text='JSON data after user edits'
    )

    # Header info (extracted for quick reference)
    mat_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='MAT Number'
    )
    sn_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='SN Number'
    )
    original_filename = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Original Filename'
    )

    # Link to ERP (optional)
    design = models.ForeignKey(
        'technology.Design',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cutter_map_documents',
        verbose_name='Linked Design'
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED
    )

    # Validation
    is_validated = models.BooleanField(
        default=False,
        verbose_name='Validated'
    )
    validation_messages = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Validation Messages'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cutter_map_documents'
    )

    class Meta:
        db_table = 'cutter_map_documents'
        ordering = ['-created_at']
        verbose_name = 'Cutter Map Document'
        verbose_name_plural = 'Cutter Map Documents'
        permissions = [
            ('can_upload_cutter_map', 'Can upload cutter map PDFs'),
            ('can_edit_cutter_map', 'Can edit cutter map data'),
            ('can_generate_cutter_map', 'Can generate cutter map PDFs'),
            ('can_sync_cutter_map', 'Can sync cutter map to ERP'),
        ]

    def __str__(self):
        return f"{self.mat_number or self.original_filename} ({self.get_status_display()})"

    def get_data(self):
        """Return edited data if exists, otherwise extracted data."""
        return self.edited_data or self.extracted_data

    def sync_to_design(self):
        """
        Sync extracted/edited data to the linked Design model.
        Creates or updates BOM lines and cutter layouts.
        """
        if not self.design:
            return False

        # TODO: Implement sync logic
        # - Update Design fields from header
        # - Create/update BOMLines from summary
        # - Create/update DesignCutterLayout from blades

        self.status = self.Status.SYNCED
        self.save()
        return True


class CutterMapHistory(models.Model):
    """
    Tracks changes made to cutter map documents.
    """

    class Action(models.TextChoices):
        UPLOAD = "UPLOAD", "Uploaded"
        EXTRACT = "EXTRACT", "Data Extracted"
        EDIT = "EDIT", "Data Edited"
        GENERATE_PDF = "GEN_PDF", "PDF Generated"
        GENERATE_PPT = "GEN_PPT", "PPT Generated"
        VALIDATE = "VALIDATE", "Validated"
        SYNC = "SYNC", "Synced to ERP"

    document = models.ForeignKey(
        CutterMapDocument,
        on_delete=models.CASCADE,
        related_name='history'
    )
    action = models.CharField(
        max_length=20,
        choices=Action.choices
    )
    details = models.JSONField(
        default=dict,
        blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cutter_map_history'
        ordering = ['-timestamp']
        verbose_name = 'Cutter Map History'
        verbose_name_plural = 'Cutter Map History'

    def __str__(self):
        return f"{self.document} - {self.get_action_display()} at {self.timestamp}"
