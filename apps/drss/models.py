"""
ARDT FMS - DRSS Models
Version: 5.4

Tables:
- drss_requests (P1)
- drss_request_lines (P1)

DRSS = Drill Request Service System (ARAMCO SMI Bit Request)
"""

from django.db import models
from django.conf import settings


class DRSSRequest(models.Model):
    """
    🟢 P1: ARAMCO DRSS (Drill Request Service System) requests.
    
    DRSS is ARAMCO's system for requesting drill bits. This table
    captures incoming requests that need to be evaluated and fulfilled.
    """
    
    class Status(models.TextChoices):
        RECEIVED = 'RECEIVED', 'Received'
        EVALUATING = 'EVALUATING', 'Evaluating'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        PARTIAL = 'PARTIAL', 'Partially Fulfilled'
        FULFILLED = 'FULFILLED', 'Fulfilled'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    class Priority(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
        CRITICAL = 'CRITICAL', 'Critical'
    
    # DRSS Reference
    drss_number = models.CharField(max_length=50, unique=True, help_text='ARAMCO DRSS Number')
    external_reference = models.CharField(max_length=100, blank=True, help_text='Additional ARAMCO ref')
    
    # Source
    customer = models.ForeignKey(
        'sales.Customer',
        on_delete=models.PROTECT,
        related_name='drss_requests'
    )
    rig = models.ForeignKey(
        'sales.Rig',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drss_requests'
    )
    well = models.ForeignKey(
        'sales.Well',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drss_requests'
    )
    
    # Request details
    requested_date = models.DateField(help_text='Date request was made')
    required_date = models.DateField(help_text='Date bits are needed')
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED
    )
    
    # Processing
    received_at = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_drss'
    )
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluated_drss'
    )
    evaluated_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    customer_notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'drss_requests'
        ordering = ['-requested_date', '-priority']
        verbose_name = 'DRSS Request'
        verbose_name_plural = 'DRSS Requests'
    
    def __str__(self):
        return f"DRSS-{self.drss_number}"
    
    @property
    def line_count(self):
        return self.lines.count()
    
    @property
    def fulfilled_count(self):
        return self.lines.filter(status='FULFILLED').count()


class DRSSRequestLine(models.Model):
    """
    🟢 P1: Individual bit requests within a DRSS request.
    
    Each line represents one bit requirement with its fulfillment option.
    """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Evaluation'
        EVALUATING = 'EVALUATING', 'Under Evaluation'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        FULFILLED = 'FULFILLED', 'Fulfilled'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    class FulfillmentOption(models.TextChoices):
        STOCK = 'STOCK', 'From Stock'
        TRANSFER = 'TRANSFER', 'Transfer from Location'
        BUILD_NEW = 'BUILD_NEW', 'Build New'
        RETROFIT = 'RETROFIT', 'Retrofit Existing'
        REWORK = 'REWORK', 'Rework/Repair'
    
    drss_request = models.ForeignKey(
        DRSSRequest,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.IntegerField()
    
    # Requested bit specifications
    bit_type = models.CharField(max_length=20, help_text='FC/RC')
    bit_size = models.DecimalField(max_digits=6, decimal_places=3, help_text='Size in inches')
    design = models.ForeignKey(
        'technology.Design',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drss_lines'
    )
    design_code = models.CharField(max_length=50, blank=True, help_text='Requested design')
    quantity = models.IntegerField(default=1)
    
    # Requirements
    iadc_code = models.CharField(max_length=20, blank=True)
    formation = models.CharField(max_length=100, blank=True)
    depth_from = models.IntegerField(null=True, blank=True, help_text='Feet')
    depth_to = models.IntegerField(null=True, blank=True, help_text='Feet')
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Fulfillment decision
    fulfillment_option = models.CharField(
        max_length=20,
        choices=FulfillmentOption.choices,
        null=True,
        blank=True
    )
    fulfillment_notes = models.TextField(blank=True)
    
    # Links to fulfillment
    sales_order_line = models.ForeignKey(
        'sales.SalesOrderLine',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drss_lines'
    )
    work_order = models.ForeignKey(
        'workorders.WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drss_lines'
    )
    source_bit = models.ForeignKey(
        'workorders.DrillBit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drss_source_lines',
        help_text='Existing bit for STOCK/TRANSFER/REWORK'
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'drss_request_lines'
        ordering = ['drss_request', 'line_number']
        unique_together = ['drss_request', 'line_number']
        verbose_name = 'DRSS Request Line'
        verbose_name_plural = 'DRSS Request Lines'
    
    def __str__(self):
        return f"{self.drss_request} - Line {self.line_number}"
