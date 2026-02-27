"""
ARDT FMS — Receiving Dock Views
Backload Batches + BOM Pending + Receiving Inspections dashboard.

Two flows:
  REPAIR bits → BackloadBatch → confirm arrival → BitEvent(BACKLOADED) → Evaluation
  NEW bits   → Register → ReceivingInspection (if BOM assigned) → available for manufacture
"""

import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from .models import (
    BackloadBatch,
    BackloadItem,
    BitEvent,
    BOMPendingRequest,
    DrillBit,
    ReceivingInspection,
)
from .forms import BackloadBatchForm


# =============================================================================
# RECEIVING DOCK DASHBOARD
# =============================================================================

class ReceivingDockDashboardView(LoginRequiredMixin, TemplateView):
    """Central receiving dock page showing all active panels."""
    template_name = "workorders/receiving_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)

        # Panel 1: Incoming batches (not completed)
        incoming_batches = BackloadBatch.objects.filter(
            status__in=[
                BackloadBatch.BatchStatus.PENDING,
                BackloadBatch.BatchStatus.ARRIVED,
                BackloadBatch.BatchStatus.PROCESSING,
            ]
        ).select_related("account").order_by("-created_at")[:10]

        # Panel 2: Recently received (7 days)
        recent_events = BitEvent.objects.filter(
            event_type__in=[
                BitEvent.EventType.BACKLOADED,
                BitEvent.EventType.RECEIVED,
            ],
            event_date__gte=seven_days_ago.date(),
        ).select_related("bit", "bit__account").order_by("-event_date", "-id")[:15]

        # Panel 3: Pending receiving inspections (new bits only)
        pending_inspections = ReceivingInspection.objects.filter(
            is_complete=False
        ).select_related(
            "drill_bit", "drill_bit__design", "drill_bit__design__size"
        ).order_by("-created_at")[:10]

        # Panel 4: BOM pending queue
        bom_pending = BOMPendingRequest.objects.filter(
            status=BOMPendingRequest.RequestStatus.OPEN
        ).select_related(
            "drill_bit", "drill_bit__design", "drill_bit__design__size",
            "requested_by",
        ).order_by("-created_at")[:10]

        ctx.update({
            "incoming_batches": incoming_batches,
            "incoming_batches_count": incoming_batches.count(),
            "recent_events": recent_events,
            "recent_events_count": recent_events.count(),
            "pending_inspections": pending_inspections,
            "pending_inspections_count": pending_inspections.count(),
            "bom_pending": bom_pending,
            "bom_pending_count": bom_pending.count(),
        })
        return ctx


# =============================================================================
# BACKLOAD BATCH CRUD
# =============================================================================

class BackloadBatchListView(LoginRequiredMixin, ListView):
    """List all backload batches with filtering."""
    model = BackloadBatch
    template_name = "workorders/backload_batch_list.html"
    context_object_name = "batches"
    paginate_by = 25

    def get_queryset(self):
        qs = BackloadBatch.objects.select_related("account", "customer").order_by("-created_at")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        account = self.request.GET.get("account")
        if account:
            qs = qs.filter(account_id=account)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(batch_number__icontains=q) |
                Q(batch_reference__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.sales.models import Account
        ctx["accounts"] = Account.objects.filter(
            workflow_type__in=["REPAIR", "BOTH"], is_active=True
        ).order_by("sort_order", "name")
        ctx["status_choices"] = BackloadBatch.BatchStatus.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["current_account"] = self.request.GET.get("account", "")
        ctx["current_q"] = self.request.GET.get("q", "")
        return ctx


class BackloadBatchCreateView(LoginRequiredMixin, CreateView):
    """Create a new backload batch with bulk serial entry."""
    model = BackloadBatch
    form_class = BackloadBatchForm
    template_name = "workorders/backload_batch_create.html"

    def form_valid(self, form):
        batch = form.save(commit=False)
        batch.created_by = self.request.user
        batch.save()

        # Show serial cleanup warnings (skipped lines) if any
        if hasattr(form, '_serial_warnings') and form._serial_warnings:
            for w in form._serial_warnings:
                messages.warning(self.request, f"Skipped: {w}")

        # Parse serials and create items
        serials = form.get_serial_list()
        for i, sn in enumerate(serials):
            item = BackloadItem(
                batch=batch,
                serial_number=sn,
                sort_order=i,
            )
            item.save()
            item.attempt_match()

        # Update counts
        batch.update_counts()

        matched = batch.items.filter(match_status=BackloadItem.MatchStatus.MATCHED).count()
        unmatched = batch.items.filter(match_status=BackloadItem.MatchStatus.UNMATCHED).count()
        messages.success(
            self.request,
            f"Batch {batch.batch_number} created with {len(serials)} serials. "
            f"{matched} matched, {unmatched} not found."
        )
        return redirect("workorders:backload_batch_detail", pk=batch.pk)


class BackloadBatchDetailView(LoginRequiredMixin, DetailView):
    """Detail view showing batch items with actions."""
    model = BackloadBatch
    template_name = "workorders/backload_batch_detail.html"
    context_object_name = "batch"

    def get_queryset(self):
        return BackloadBatch.objects.select_related("account", "customer", "created_by")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        items = self.object.items.select_related(
            "drill_bit", "drill_bit__design", "drill_bit__design__size",
            "received_by", "work_order", "bit_event",
        ).order_by("sort_order", "id")
        ctx["items"] = items
        ctx["matched_count"] = items.filter(match_status=BackloadItem.MatchStatus.MATCHED).count()
        ctx["unmatched_count"] = items.filter(match_status=BackloadItem.MatchStatus.UNMATCHED).count()
        ctx["new_registered_count"] = items.filter(match_status=BackloadItem.MatchStatus.NEW_REGISTERED).count()
        ctx["received_count"] = items.exclude(status=BackloadItem.ItemStatus.EXPECTED).count()
        return ctx


# =============================================================================
# BACKLOAD BATCH API ENDPOINTS
# =============================================================================

@login_required
@require_POST
def api_batch_confirm_arrival(request, pk):
    """Confirm arrival of a single item in a batch."""
    batch = get_object_or_404(BackloadBatch, pk=pk)
    data = json.loads(request.body) if request.content_type == "application/json" else request.POST
    item_id = data.get("item_id")
    item = get_object_or_404(BackloadItem, pk=item_id, batch=batch)

    if item.status != BackloadItem.ItemStatus.EXPECTED:
        return JsonResponse({"ok": False, "error": "Item already received."}, status=400)

    if not item.drill_bit:
        return JsonResponse({"ok": False, "error": "No drill bit matched. Register first."}, status=400)

    bit = item.drill_bit
    now = timezone.now()

    # 1. Create BitEvent(BACKLOADED)
    event = BitEvent.objects.create(
        bit=bit,
        event_type=BitEvent.EventType.BACKLOADED,
        event_date=now.date(),
        notes=f"Backload batch {batch.batch_number}",
        performed_by=request.user,
    )

    # 2. Update DrillBit
    bit.lifecycle_status = DrillBit.LifecycleStatus.BACKLOADED
    bit.status = DrillBit.Status.RETURNED
    bit.physical_status = DrillBit.PhysicalStatus.AT_ARDT
    bit.backload_count = (bit.backload_count or 0) + 1
    bit.last_backload_date = now.date()
    bit.save(update_fields=[
        "lifecycle_status", "status", "physical_status",
        "backload_count", "last_backload_date",
    ])

    # 3. Update BackloadItem
    item.status = BackloadItem.ItemStatus.RECEIVED
    item.received_date = now
    item.received_by = request.user
    item.bit_event = event
    item.save(update_fields=["status", "received_date", "received_by", "bit_event"])

    # 4. Update batch counts + auto-status
    batch.update_counts()
    batch.auto_update_status()

    # Set received_date on batch if first arrival
    if not batch.received_date:
        batch.received_date = now.date()
        batch.save(update_fields=["received_date"])

    return JsonResponse({
        "ok": True,
        "item_status": item.get_status_display(),
        "batch_received_count": batch.received_count,
        "batch_status": batch.get_status_display(),
    })


@login_required
@require_POST
def api_batch_confirm_all(request, pk):
    """Confirm arrival of ALL matched, unconfirmed items in a batch."""
    batch = get_object_or_404(BackloadBatch, pk=pk)
    pending_items = batch.items.filter(
        status=BackloadItem.ItemStatus.EXPECTED,
        match_status=BackloadItem.MatchStatus.MATCHED,
        drill_bit__isnull=False,
    )

    now = timezone.now()
    confirmed = 0

    for item in pending_items:
        bit = item.drill_bit
        event = BitEvent.objects.create(
            bit=bit,
            event_type=BitEvent.EventType.BACKLOADED,
            event_date=now.date(),
            notes=f"Backload batch {batch.batch_number} (bulk confirm)",
            performed_by=request.user,
        )
        bit.lifecycle_status = DrillBit.LifecycleStatus.BACKLOADED
        bit.status = DrillBit.Status.RETURNED
        bit.physical_status = DrillBit.PhysicalStatus.AT_ARDT
        bit.backload_count = (bit.backload_count or 0) + 1
        bit.last_backload_date = now.date()
        bit.save(update_fields=[
            "lifecycle_status", "status", "physical_status",
            "backload_count", "last_backload_date",
        ])

        item.status = BackloadItem.ItemStatus.RECEIVED
        item.received_date = now
        item.received_by = request.user
        item.bit_event = event
        item.save(update_fields=["status", "received_date", "received_by", "bit_event"])
        confirmed += 1

    batch.update_counts()
    batch.auto_update_status()
    if not batch.received_date:
        batch.received_date = now.date()
        batch.save(update_fields=["received_date"])

    return JsonResponse({
        "ok": True,
        "confirmed": confirmed,
        "batch_received_count": batch.received_count,
        "batch_status": batch.get_status_display(),
    })


@login_required
@require_POST
def api_batch_register_new_bit(request, pk):
    """Register a new DrillBit for an unmatched serial in the batch."""
    batch = get_object_or_404(BackloadBatch, pk=pk)
    data = json.loads(request.body) if request.content_type == "application/json" else request.POST
    item_id = data.get("item_id")
    item = get_object_or_404(BackloadItem, pk=item_id, batch=batch)

    if item.match_status != BackloadItem.MatchStatus.UNMATCHED:
        return JsonResponse({"ok": False, "error": "Item is not unmatched."}, status=400)

    # Create a new DrillBit
    bit = DrillBit.objects.create(
        serial_number=item.serial_number,
        account=batch.account,
        status=DrillBit.Status.NEW,
        lifecycle_status=DrillBit.LifecycleStatus.NEW,
        physical_status=DrillBit.PhysicalStatus.AT_ARDT,
    )

    item.drill_bit = bit
    item.match_status = BackloadItem.MatchStatus.NEW_REGISTERED
    item.save(update_fields=["drill_bit", "match_status"])

    return JsonResponse({
        "ok": True,
        "drill_bit_id": bit.pk,
        "serial_number": bit.serial_number,
        "match_status": item.get_match_status_display(),
    })


@login_required
@require_POST
def api_batch_rematch(request, pk):
    """Re-attempt matching all UNMATCHED items in a batch."""
    batch = get_object_or_404(BackloadBatch, pk=pk)
    unmatched = batch.items.filter(match_status=BackloadItem.MatchStatus.UNMATCHED)
    rematched = 0
    for item in unmatched:
        old_status = item.match_status
        item.attempt_match()
        if item.match_status == BackloadItem.MatchStatus.MATCHED:
            rematched += 1

    return JsonResponse({
        "ok": True,
        "rematched": rematched,
        "still_unmatched": unmatched.count() - rematched,
    })


# =============================================================================
# BOM PENDING
# =============================================================================

class BOMPendingListView(LoginRequiredMixin, ListView):
    """List BOM pending requests for tech team."""
    model = BOMPendingRequest
    template_name = "workorders/bom_pending_list.html"
    context_object_name = "requests"
    paginate_by = 25

    def get_queryset(self):
        qs = BOMPendingRequest.objects.select_related(
            "drill_bit", "drill_bit__design", "drill_bit__design__size",
            "drill_bit__account", "requested_by", "assigned_by",
        ).order_by("-created_at")
        status = self.request.GET.get("status", "OPEN")
        if status:
            qs = qs.filter(status=status)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(drill_bit__serial_number__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = BOMPendingRequest.RequestStatus.choices
        ctx["current_status"] = self.request.GET.get("status", "OPEN")
        ctx["current_q"] = self.request.GET.get("q", "")
        return ctx


@login_required
@require_POST
def api_create_bom_request(request):
    """Create a BOM pending request for a drill bit."""
    data = json.loads(request.body) if request.content_type == "application/json" else request.POST
    drill_bit_id = data.get("drill_bit_id")
    bit = get_object_or_404(DrillBit, pk=drill_bit_id)

    # Check no open request exists
    existing = BOMPendingRequest.objects.filter(
        drill_bit=bit,
        status=BOMPendingRequest.RequestStatus.OPEN,
    ).exists()
    if existing:
        return JsonResponse({"ok": False, "error": "Open request already exists."}, status=400)

    req = BOMPendingRequest.objects.create(
        drill_bit=bit,
        requested_by=request.user,
        notes=data.get("notes", ""),
    )
    return JsonResponse({"ok": True, "request_id": req.pk})


@login_required
@require_POST
def api_resolve_bom_request(request, pk):
    """Resolve a BOM pending request (mark as ASSIGNED)."""
    bom_req = get_object_or_404(BOMPendingRequest, pk=pk)
    if bom_req.status != BOMPendingRequest.RequestStatus.OPEN:
        return JsonResponse({"ok": False, "error": "Request is not open."}, status=400)

    bom_req.status = BOMPendingRequest.RequestStatus.ASSIGNED
    bom_req.assigned_by = request.user
    bom_req.resolved_at = timezone.now()
    bom_req.save(update_fields=["status", "assigned_by", "resolved_at"])

    return JsonResponse({
        "ok": True,
        "status": bom_req.get_status_display(),
    })


# =============================================================================
# RECEIVING INSPECTION LIST
# =============================================================================

class ReceivingInspectionListView(LoginRequiredMixin, ListView):
    """List all receiving inspections."""
    model = ReceivingInspection
    template_name = "workorders/receiving_inspection_list.html"
    context_object_name = "inspections"
    paginate_by = 25

    def get_queryset(self):
        qs = ReceivingInspection.objects.select_related(
            "drill_bit", "drill_bit__design", "drill_bit__design__size",
        ).order_by("-created_at")
        status = self.request.GET.get("status")
        if status == "pending":
            qs = qs.filter(is_complete=False)
        elif status == "complete":
            qs = qs.filter(is_complete=True)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(drill_bit__serial_number__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["current_q"] = self.request.GET.get("q", "")
        return ctx
