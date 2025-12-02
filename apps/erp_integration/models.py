"""
ARDT FMS - ERP Integration Models
Version: 5.4

⚪ FUTURE - Beyond v2.0

Tables:
- erp_mappings (FUTURE)
- erp_sync_logs (FUTURE)
"""

from django.conf import settings
from django.db import models


class ERPMapping(models.Model):
    """⚪ FUTURE: Mappings between ARDT and ERP systems."""

    class EntityType(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        ITEM = "ITEM", "Inventory Item"
        WORK_ORDER = "WORK_ORDER", "Work Order"
        SALES_ORDER = "SALES_ORDER", "Sales Order"
        PURCHASE_ORDER = "PURCHASE_ORDER", "Purchase Order"

    entity_type = models.CharField(max_length=30, choices=EntityType.choices)
    ardt_id = models.BigIntegerField()
    erp_system = models.CharField(max_length=50, help_text="SAP, Oracle, etc.")
    erp_id = models.CharField(max_length=100)

    is_active = models.BooleanField(default=True)
    last_synced = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "erp_mappings"
        unique_together = ["entity_type", "ardt_id", "erp_system"]
        verbose_name = "ERP Mapping"
        verbose_name_plural = "ERP Mappings"

    def __str__(self):
        return f"{self.get_entity_type_display()}: {self.ardt_id} → {self.erp_id}"


class ERPSyncLog(models.Model):
    """⚪ FUTURE: Log of ERP synchronization attempts."""

    class Direction(models.TextChoices):
        OUTBOUND = "OUTBOUND", "ARDT → ERP"
        INBOUND = "INBOUND", "ERP → ARDT"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        PARTIAL = "PARTIAL", "Partial"

    erp_system = models.CharField(max_length=50)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    entity_type = models.CharField(max_length=30)
    entity_id = models.BigIntegerField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    request_payload = models.JSONField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "erp_sync_logs"
        ordering = ["-started_at"]
        verbose_name = "ERP Sync Log"
        verbose_name_plural = "ERP Sync Logs"

    def __str__(self):
        return f"{self.entity_type} - {self.get_status_display()} at {self.started_at}"
