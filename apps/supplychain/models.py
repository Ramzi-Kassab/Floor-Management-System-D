"""
ARDT FMS - Supply Chain Models
Version: 5.4

🟡 P2 - Extended Operations

Tables:
- suppliers (P2)
- purchase_requisitions (P2)
- pr_lines (P2)
- purchase_orders (P2)
- po_lines (P2)
- goods_receipts (P2)
- grn_lines (P2)
- capas (P2)
"""

from django.conf import settings
from django.db import models


class Supplier(models.Model):
    """🟡 P2: Supplier master."""

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    payment_terms = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "suppliers"
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"

    def __str__(self):
        return f"{self.code} - {self.name}"


class PurchaseRequisition(models.Model):
    """🟡 P2: Purchase Requisitions."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        ORDERED = "ORDERED", "Ordered"
        CANCELLED = "CANCELLED", "Cancelled"

    pr_number = models.CharField(max_length=30, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    required_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="purchase_requisitions"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_prs"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "purchase_requisitions"
        verbose_name = "Purchase Requisition"
        verbose_name_plural = "Purchase Requisitions"

    def __str__(self):
        return self.pr_number


class PRLine(models.Model):
    """🟡 P2: Purchase Requisition Lines."""

    pr = models.ForeignKey(PurchaseRequisition, on_delete=models.CASCADE, related_name="lines")
    line_number = models.IntegerField()
    inventory_item = models.ForeignKey("inventory.InventoryItem", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "pr_lines"
        unique_together = ["pr", "line_number"]

    def __str__(self):
        return f"{self.pr.pr_number} - Line {self.line_number}"


class PurchaseOrder(models.Model):
    """🟡 P2: Purchase Orders."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent to Supplier"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PARTIAL = "PARTIAL", "Partially Received"
        RECEIVED = "RECEIVED", "Fully Received"
        CANCELLED = "CANCELLED", "Cancelled"

    po_number = models.CharField(max_length=30, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    order_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "purchase_orders"
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"

    def __str__(self):
        return self.po_number


class POLine(models.Model):
    """🟡 P2: Purchase Order Lines."""

    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    line_number = models.IntegerField()
    inventory_item = models.ForeignKey("inventory.InventoryItem", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(max_digits=15, decimal_places=4)
    received_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    class Meta:
        db_table = "po_lines"
        unique_together = ["po", "line_number"]

    def __str__(self):
        return f"{self.po.po_number} - Line {self.line_number}"


class GoodsReceipt(models.Model):
    """🟡 P2: Goods Receipt Notes."""

    grn_number = models.CharField(max_length=30, unique=True)
    po = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="receipts")
    receipt_date = models.DateField()
    notes = models.TextField(blank=True)

    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "goods_receipts"
        verbose_name = "Goods Receipt"
        verbose_name_plural = "Goods Receipts"

    def __str__(self):
        return self.grn_number


class GRNLine(models.Model):
    """🟡 P2: Goods Receipt Lines."""

    grn = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name="lines")
    po_line = models.ForeignKey(POLine, on_delete=models.PROTECT)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=3)
    lot_number = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "grn_lines"

    def __str__(self):
        return f"{self.grn.grn_number} - {self.po_line}"


class CAPA(models.Model):
    """🟡 P2: Corrective and Preventive Actions."""

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        VERIFICATION = "VERIFICATION", "Pending Verification"
        CLOSED = "CLOSED", "Closed"

    capa_number = models.CharField(max_length=30, unique=True)
    ncr = models.ForeignKey("quality.NCR", on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    preventive_action = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    due_date = models.DateField(null=True, blank=True)

    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "capas"
        verbose_name = "CAPA"
        verbose_name_plural = "CAPAs"

    def __str__(self):
        return f"{self.capa_number} - {self.title}"
