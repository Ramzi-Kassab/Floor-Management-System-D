"""
ARDT FMS — Receiving Dock Views
Backload Batches + BOM Pending + Receiving Inspections dashboard.

Two flows:
  REPAIR bits → BackloadBatch → confirm arrival → BitEvent(BACKLOADED) → Evaluation
  NEW bits   → Register → ReceivingInspection (if BOM assigned) → available for manufacture
"""

import json
import re
from datetime import timedelta
from decimal import Decimal

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
    BackloadBatchAttachment,
    BackloadItem,
    BitEvent,
    BOMPendingRequest,
    DrillBit,
    Location,
    ReceivingInspection,
)
from .forms import BackloadBatchForm


# =============================================================================
# SHARED HELPERS (used by batch create + add-items + replace-serial APIs)
# =============================================================================

def _parse_serials(raw_text):
    """Parse raw serial text into validated list + errors.

    Returns (cleaned_list, error_list).
    Strips non-digit characters, validates 6 or 8 digit length, deduplicates.
    """
    cleaned = []
    errors = []
    seen = set()
    for line in raw_text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        digits = re.sub(r'\D', '', line)
        if not digits:
            errors.append(f"'{line}': no digits found")
            continue
        if len(digits) not in (6, 8):
            errors.append(f"'{digits}': must be 6 or 8 digits")
            continue
        if digits in seen:
            errors.append(f"'{digits}': duplicate")
            continue
        seen.add(digits)
        cleaned.append(digits)
    return cleaned, errors


def _create_and_process_items(batch, serials, user):
    """Create BackloadItems, match, and auto-process. Returns result counts.

    Auto-processing:
      - MATCHED items: existing DrillBit updated with BACKLOADED status
      - UNMATCHED items: new DrillBit auto-created, then processed same way
      - Creates BitEvent(BACKLOADED) for all items
      - Updates DrillBit status fields
      - Raises BOMPendingRequest if no BOM assigned
    """
    now = timezone.now()
    # Outside shipments (NEW) → Receiving Area; local backload (REPAIR) → Backload Area
    if batch.batch_type == BackloadBatch.BatchType.NEW:
        receiving_loc = Location.objects.filter(code='RCV-AREA').first()
    else:
        receiving_loc = Location.objects.filter(code='BACKLOAD').first()
    # Fallback if specific location doesn't exist
    if not receiving_loc:
        receiving_loc = Location.objects.filter(
            location_type=Location.LocationType.RECEIVING
        ).first()

    start_order = batch.items.count()
    matched = 0
    new_registered = 0
    bom_pending = 0

    for i, sn in enumerate(serials):
        item = BackloadItem(batch=batch, serial_number=sn, sort_order=start_order + i)
        item.save()
        item.attempt_match()

        # If unmatched, auto-register as a new DrillBit
        if item.match_status == BackloadItem.MatchStatus.UNMATCHED:
            bit_type = DrillBit.BitCategory.FC if len(sn) == 8 else DrillBit.BitCategory.RC
            new_bit = DrillBit(
                serial_number=sn,
                bit_type=bit_type,
                size=Decimal("0"),
                status=DrillBit.Status.UNREGISTERED,
                account=batch.account,
                customer=batch.customer,
            )
            new_bit.save()
            item.drill_bit = new_bit
            item.match_status = BackloadItem.MatchStatus.NEW_REGISTERED
            item.save(update_fields=["drill_bit", "match_status"])
            new_registered += 1

        # Now process all items that have a drill_bit
        if item.drill_bit:
            bit = item.drill_bit
            is_new = item.match_status == BackloadItem.MatchStatus.NEW_REGISTERED

            # Create BitEvent — BACKLOADED for known bits, RECEIVED for new
            event_type = BitEvent.EventType.RECEIVED if is_new else BitEvent.EventType.BACKLOADED
            event = BitEvent.objects.create(
                bit=bit,
                event_type=event_type,
                event_date=now,
                location=receiving_loc,
                notes=f"Backload batch {batch.batch_number}",
                performed_by=user,
            )

            # Status/condition based on level:
            #   L5          → RECEIVING + FINISHED_GOOD
            #   L3/L4       → RECEIVING + COMPONENTS
            #   No level    → repair bit, original BACKLOADED logic
            if bit.level == '5':
                batch_status = DrillBit.Status.RECEIVING
                batch_condition = DrillBit.Condition.FINISHED_GOOD
            elif bit.level in ('3', '4', '5.5'):
                batch_status = DrillBit.Status.RECEIVING
                batch_condition = DrillBit.Condition.COMPONENTS
            else:
                # Repair bit — no level set
                batch_status = None
                if batch.batch_type == BackloadBatch.BatchType.NEW:
                    batch_condition = DrillBit.Condition.NOT_USED
                else:
                    batch_condition = DrillBit.Condition.USED

            if is_new:
                bit.condition = batch_condition
                if batch_status:
                    bit.status = batch_status
                else:
                    bit.determine_initial_status()
                bit.physical_status = DrillBit.PhysicalStatus.AT_ARDT
                bit.bit_location = receiving_loc
                bit.last_backload_date = now.date()
                bit.derive_ownership()
                bit.save(update_fields=[
                    "status", "condition", "ownership",
                    "physical_status", "bit_location",
                    "last_backload_date",
                ])
            else:
                bit.lifecycle_status = DrillBit.LifecycleStatus.BACKLOADED
                bit.status = batch_status or DrillBit.Status.BACKLOADED
                bit.condition = batch_condition
                bit.physical_status = DrillBit.PhysicalStatus.AT_ARDT
                bit.bit_location = receiving_loc
                bit.backload_count = (bit.backload_count or 0) + 1
                bit.last_backload_date = now.date()
                bit.derive_ownership()
                bit.save(update_fields=[
                    "lifecycle_status", "status", "condition", "ownership",
                    "physical_status", "bit_location",
                    "backload_count", "last_backload_date",
                ])
                matched += 1

            # Set item status: UNREGISTERED if bit has no design, else ARRIVED
            if bit.status == DrillBit.Status.UNREGISTERED:
                item.status = BackloadItem.ItemStatus.UNREGISTERED
            else:
                item.status = BackloadItem.ItemStatus.ARRIVED
            item.received_date = now
            item.received_by = user
            item.bit_event = event
            item.save(update_fields=["status", "received_date", "received_by", "bit_event"])

            # Auto-raise BOM pending if bit has no BOM
            if not bit.bom and not bit.brazing_bom and not bit.system_bom:
                if not BOMPendingRequest.objects.filter(
                    drill_bit=bit,
                    status=BOMPendingRequest.RequestStatus.OPEN,
                ).exists():
                    BOMPendingRequest.objects.create(
                        drill_bit=bit,
                        requested_by=user,
                        notes=f"Auto: No BOM at receiving (batch {batch.batch_number}).",
                    )
                    bom_pending += 1

    batch.update_counts()
    batch.auto_update_status()

    return {"matched": matched, "new_registered": new_registered, "bom_pending": bom_pending}


def _auto_process_single_item(item, user, batch):
    """Auto-process a single BackloadItem after match/register. Returns result counts.

    If item is UNMATCHED, auto-registers a new DrillBit first.
    """
    now = timezone.now()
    # Outside shipments (NEW) → Receiving Area; local backload (REPAIR) → Backload Area
    if batch.batch_type == BackloadBatch.BatchType.NEW:
        receiving_loc = Location.objects.filter(code='RCV-AREA').first()
    else:
        receiving_loc = Location.objects.filter(code='BACKLOAD').first()
    if not receiving_loc:
        receiving_loc = Location.objects.filter(
            location_type=Location.LocationType.RECEIVING
        ).first()

    matched = 0
    new_registered = 0
    bom_pending = 0

    # Auto-register unmatched items
    if item.match_status == BackloadItem.MatchStatus.UNMATCHED:
        sn = item.serial_number
        bit_type = DrillBit.BitCategory.FC if len(sn) == 8 else DrillBit.BitCategory.RC
        new_bit = DrillBit(
            serial_number=sn,
            bit_type=bit_type,
            size=Decimal("0"),
            status=DrillBit.Status.UNREGISTERED,
            account=batch.account,
            customer=batch.customer,
        )
        new_bit.save()
        item.drill_bit = new_bit
        item.match_status = BackloadItem.MatchStatus.NEW_REGISTERED
        item.save(update_fields=["drill_bit", "match_status"])
        new_registered = 1

    # Process all items with a drill_bit
    if item.drill_bit:
        bit = item.drill_bit
        is_new = item.match_status == BackloadItem.MatchStatus.NEW_REGISTERED

        event_type = BitEvent.EventType.RECEIVED if is_new else BitEvent.EventType.BACKLOADED
        event = BitEvent.objects.create(
            bit=bit,
            event_type=event_type,
            event_date=now,
            location=receiving_loc,
            notes=f"Backload batch {batch.batch_number}",
            performed_by=user,
        )

        # Status/condition based on level:
        #   L5          → RECEIVING + FINISHED_GOOD
        #   L3/L4       → RECEIVING + COMPONENTS
        #   No level    → repair bit, original BACKLOADED logic
        if bit.level == '5':
            batch_status = DrillBit.Status.RECEIVING
            batch_condition = DrillBit.Condition.FINISHED_GOOD
        elif bit.level in ('3', '4', '5.5'):
            batch_status = DrillBit.Status.RECEIVING
            batch_condition = DrillBit.Condition.COMPONENTS
        else:
            batch_status = None
            if batch.batch_type == BackloadBatch.BatchType.NEW:
                batch_condition = DrillBit.Condition.NOT_USED
            else:
                batch_condition = DrillBit.Condition.USED

        if is_new:
            bit.condition = batch_condition
            if batch_status:
                bit.status = batch_status
            else:
                bit.determine_initial_status()
            bit.physical_status = DrillBit.PhysicalStatus.AT_ARDT
            bit.bit_location = receiving_loc
            bit.last_backload_date = now.date()
            bit.derive_ownership()
            bit.save(update_fields=[
                "status", "condition", "ownership",
                "physical_status", "bit_location",
                "last_backload_date",
            ])
        else:
            bit.lifecycle_status = DrillBit.LifecycleStatus.BACKLOADED
            bit.status = batch_status or DrillBit.Status.BACKLOADED
            bit.condition = batch_condition
            bit.physical_status = DrillBit.PhysicalStatus.AT_ARDT
            bit.bit_location = receiving_loc
            bit.backload_count = (bit.backload_count or 0) + 1
            bit.last_backload_date = now.date()
            bit.derive_ownership()
            bit.save(update_fields=[
                "lifecycle_status", "status", "condition", "ownership",
                "physical_status", "bit_location",
                "backload_count", "last_backload_date",
            ])
            matched = 1

        # Set item status: UNREGISTERED if bit has no design, else ARRIVED
        if bit.status == DrillBit.Status.UNREGISTERED:
            item.status = BackloadItem.ItemStatus.UNREGISTERED
        else:
            item.status = BackloadItem.ItemStatus.ARRIVED
        item.received_date = now
        item.received_by = user
        item.bit_event = event
        item.save(update_fields=["status", "received_date", "received_by", "bit_event"])

        if not bit.bom and not bit.brazing_bom and not bit.system_bom:
            if not BOMPendingRequest.objects.filter(
                drill_bit=bit,
                status=BOMPendingRequest.RequestStatus.OPEN,
            ).exists():
                BOMPendingRequest.objects.create(
                    drill_bit=bit,
                    requested_by=user,
                    notes=f"Auto: No BOM at receiving (batch {batch.batch_number}).",
                )
                bom_pending = 1

    return {"matched": matched, "new_registered": new_registered, "bom_pending": bom_pending}


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

        # Panel 3: Pending receiving inspections (exclude UNREGISTERED bits)
        pending_inspections = ReceivingInspection.objects.filter(
            is_complete=False
        ).exclude(
            drill_bit__status=DrillBit.Status.UNREGISTERED
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

        # Panel 5: Pending registration (UNMATCHED items in active batches)
        pending_registration = BackloadItem.objects.filter(
            match_status=BackloadItem.MatchStatus.UNMATCHED,
            batch__status__in=[
                BackloadBatch.BatchStatus.ARRIVED,
                BackloadBatch.BatchStatus.PROCESSING,
            ],
        ).select_related(
            "batch",
        ).order_by("-batch__created_at", "sort_order")[:15]

        # Panel 6: Recently inspected (completed inspections)
        recently_inspected = ReceivingInspection.objects.filter(
            is_complete=True
        ).select_related(
            "drill_bit", "drill_bit__design", "drill_bit__design__size",
            "inspected_by",
        ).order_by("-updated_at")[:10]

        ctx.update({
            "incoming_batches": incoming_batches,
            "incoming_batches_count": incoming_batches.count(),
            "recent_events": recent_events,
            "recent_events_count": recent_events.count(),
            "pending_inspections": pending_inspections,
            "pending_inspections_count": pending_inspections.count(),
            "bom_pending": bom_pending,
            "bom_pending_count": bom_pending.count(),
            "recently_inspected": recently_inspected,
            "recently_inspected_count": recently_inspected.count(),
            "pending_registration": pending_registration,
            "pending_registration_count": BackloadItem.objects.filter(
                match_status=BackloadItem.MatchStatus.UNMATCHED,
                batch__status__in=[
                    BackloadBatch.BatchStatus.ARRIVED,
                    BackloadBatch.BatchStatus.PROCESSING,
                ],
            ).count(),
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
        batch_type = self.request.GET.get("batch_type")
        if batch_type:
            qs = qs.filter(batch_type=batch_type)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(batch_number__icontains=q) |
                Q(batch_reference__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = BackloadBatch.BatchStatus.choices
        ctx["type_choices"] = BackloadBatch.BatchType.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["current_type"] = self.request.GET.get("batch_type", "")
        ctx["current_q"] = self.request.GET.get("q", "")
        return ctx


class BackloadBatchCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new backload batch with bulk serial entry.
    Creating a batch = physically receiving the bits.
    Auto-processes: match → confirm → raise BOM requests.
    """
    model = BackloadBatch
    form_class = BackloadBatchForm
    template_name = "workorders/backload_batch_create.html"

    def form_valid(self, form):
        batch = form.save(commit=False)
        batch.created_by = self.request.user
        batch.save()

        # Handle multiple file uploads
        max_file_size = 25 * 1024 * 1024  # 25 MB per file
        for f in self.request.FILES.getlist("attachments"):
            if f.size <= max_file_size:
                BackloadBatchAttachment.objects.create(
                    batch=batch,
                    file=f,
                    original_filename=f.name,
                    file_size=f.size,
                    uploaded_by=self.request.user,
                )

        # Show serial cleanup warnings (skipped lines) if any
        if hasattr(form, '_serial_warnings') and form._serial_warnings:
            for w in form._serial_warnings:
                messages.warning(self.request, f"Skipped: {w}")

        # ── Create items, match, and auto-process (shared helper) ──
        serials = form.get_serial_list()
        results = _create_and_process_items(batch, serials, self.request.user)

        # ── Update batch received date ──
        batch.received_date = timezone.now().date()
        batch.save(update_fields=["received_date"])

        # ── Build success message ──
        matched_count = results["matched"]
        new_count = results["new_registered"]
        bom_pending_count = results["bom_pending"]
        total_received = matched_count + new_count
        msg = f"Batch {batch.batch_number}: {total_received} received"
        if matched_count and new_count:
            msg += f" ({matched_count} matched, {new_count} new)"
        elif new_count:
            msg += f" ({new_count} new)"
        msg += "."
        if bom_pending_count:
            msg += f" {bom_pending_count} BOM request(s) raised."
        messages.success(self.request, msg)

        return redirect("workorders:backload_batch_detail", pk=batch.pk)


class BackloadBatchDetailView(LoginRequiredMixin, DetailView):
    """Informational detail view — no action buttons.
    Shows receiving status, clickable serials for matched items, status badges.
    """
    model = BackloadBatch
    template_name = "workorders/backload_batch_detail.html"
    context_object_name = "batch"

    def get_queryset(self):
        return BackloadBatch.objects.select_related(
            "account", "customer", "created_by"
        ).prefetch_related("attachments")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        items = self.object.items.select_related(
            "drill_bit", "drill_bit__design", "drill_bit__design__size",
            "drill_bit__bom", "drill_bit__brazing_bom", "drill_bit__system_bom",
            "drill_bit__account",
            "received_by", "work_order", "bit_event",
        ).order_by("sort_order", "id")
        ctx["items"] = items
        ctx["attachments"] = self.object.attachments.all()
        ctx["matched_count"] = items.filter(
            match_status__in=[BackloadItem.MatchStatus.MATCHED, BackloadItem.MatchStatus.NEW_REGISTERED]
        ).count()
        ctx["unmatched_count"] = items.filter(match_status=BackloadItem.MatchStatus.UNMATCHED).count()
        ctx["received_count"] = items.filter(status=BackloadItem.ItemStatus.RECEIVED).count()
        ctx["total_count"] = items.count()
        return ctx


# =============================================================================
# BACKLOAD BATCH API ENDPOINTS
# NOTE: confirm-item, confirm-all, register-new removed (Feb 2026)
#       — auto-processed on batch creation in BackloadBatchCreateView.form_valid()
# =============================================================================

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


@login_required
@require_POST
def api_batch_remove_item(request, pk):
    """Remove a serial number from a batch (undo a mistaken entry).

    Reverses any side-effects:
      - Deletes the BitEvent if one was auto-created
      - Resets DrillBit lifecycle/status fields that were set on receiving
      - Cancels any BOMPendingRequest that was auto-raised for this item
      - Updates batch counts
    """
    batch = get_object_or_404(BackloadBatch, pk=pk)
    data = json.loads(request.body) if request.content_type == "application/json" else request.POST
    item_id = data.get("item_id")
    item = get_object_or_404(BackloadItem, pk=item_id, batch=batch)

    serial = item.serial_number
    bit = item.drill_bit
    reversed_event = False

    # 1. Reverse BitEvent if one was created during auto-confirm
    if item.bit_event:
        event = item.bit_event
        item.bit_event = None
        item.save(update_fields=["bit_event"])
        event.delete()
        reversed_event = True

    # 2. Reset DrillBit status if it was modified by receiving
    if bit and reversed_event:
        # Decrement backload_count (don't go below 0)
        bit.backload_count = max((bit.backload_count or 0) - 1, 0)
        # Only reset lifecycle/status if this was the most recent event
        # (i.e. the bit is still in BACKLOADED state)
        if bit.lifecycle_status == DrillBit.LifecycleStatus.BACKLOADED:
            # Check if there are other remaining BACKLOADED events
            other_backloads = BitEvent.objects.filter(
                bit=bit,
                event_type=BitEvent.EventType.BACKLOADED,
            ).exists()
            if not other_backloads:
                # No other backload events — reset to the bit's state before receiving
                bit.lifecycle_status = DrillBit.LifecycleStatus.NEW
                bit.status = DrillBit.Status.RECEIVING
                bit.condition = DrillBit.Condition.COMPONENTS
        bit.save(update_fields=[
            "lifecycle_status", "status", "condition", "backload_count",
        ])

    # 3. Cancel any BOMPendingRequest that was auto-raised for this bit
    if bit:
        BOMPendingRequest.objects.filter(
            drill_bit=bit,
            status=BOMPendingRequest.RequestStatus.OPEN,
        ).update(status=BOMPendingRequest.RequestStatus.CANCELLED)

    # 4. Delete the BackloadItem
    item.delete()

    # 5. Update batch counts + auto-status
    batch.update_counts()
    batch.auto_update_status()

    return JsonResponse({
        "ok": True,
        "serial": serial,
        "reversed_event": reversed_event,
    })


@login_required
@require_POST
def api_batch_upload_attachment(request, pk):
    """Upload one or more files to an existing batch (from detail page)."""
    batch = get_object_or_404(BackloadBatch, pk=pk)
    max_file_size = 25 * 1024 * 1024  # 25 MB per file
    uploaded = []
    for f in request.FILES.getlist("files"):
        if f.size > max_file_size:
            continue
        att = BackloadBatchAttachment.objects.create(
            batch=batch,
            file=f,
            original_filename=f.name,
            file_size=f.size,
            uploaded_by=request.user,
        )
        uploaded.append({
            "id": att.pk,
            "name": att.original_filename,
            "size": att.file_size,
            "url": att.file.url,
        })
    return JsonResponse({"ok": True, "uploaded": uploaded, "count": len(uploaded)})


@login_required
@require_POST
def api_batch_delete_attachment(request, pk, att_pk):
    """Delete an attachment from a batch."""
    batch = get_object_or_404(BackloadBatch, pk=pk)
    att = get_object_or_404(BackloadBatchAttachment, pk=att_pk, batch=batch)
    # Delete the file from storage too
    if att.file:
        att.file.delete(save=False)
    att.delete()
    return JsonResponse({"ok": True})


@login_required
@require_POST
def api_batch_add_items(request, pk):
    """Add more serials to an existing batch (bits missed during creation).

    Expects JSON body: {"serials": "one\\nper\\nline"}
    Validates, deduplicates against existing batch items, creates + auto-processes.
    """
    batch = get_object_or_404(BackloadBatch, pk=pk)
    data = json.loads(request.body)
    raw_serials = data.get("serials", "")

    # Parse and validate
    cleaned, errors = _parse_serials(raw_serials)

    # Check for duplicates against existing batch items
    existing = set(batch.items.values_list("serial_number", flat=True))
    dupes = [s for s in cleaned if s in existing]
    new_serials = [s for s in cleaned if s not in existing]

    if not new_serials:
        return JsonResponse({
            "ok": False,
            "error": "No new serials to add." + (
                f" ({len(dupes)} duplicate(s) skipped.)" if dupes else ""
            ) + (
                f" ({len(errors)} invalid.)" if errors else ""
            ),
        })

    # Create items + auto-process (shared helper)
    results = _create_and_process_items(batch, new_serials, request.user)

    return JsonResponse({
        "ok": True,
        "added": len(new_serials),
        "matched": results["matched"],
        "new_registered": results["new_registered"],
        "duplicates": dupes,
        "errors": errors,
        "bom_requests": results["bom_pending"],
    })


@login_required
@require_POST
def api_batch_edit_serial(request, pk):
    """Update a serial number (rename) — keeps all history.

    Changes the serial on both BackloadItem and DrillBit.
    Since all other models reference DrillBit via FK, the rename
    cascades automatically to WOs, BitEvents, evaluations, etc.
    """
    batch = get_object_or_404(BackloadBatch, pk=pk)
    data = json.loads(request.body)
    item_id = data.get("item_id")
    new_serial = data.get("new_serial", "").strip()

    item = get_object_or_404(BackloadItem, pk=item_id, batch=batch)
    old_serial = item.serial_number

    # Validate new serial (digits only, 6 or 8 chars)
    digits = re.sub(r'\D', '', new_serial)
    if len(digits) not in (6, 8):
        return JsonResponse({"ok": False, "error": "Serial must be 6 or 8 digits"})
    new_serial = digits

    # Same serial — no-op
    if new_serial == old_serial:
        return JsonResponse({"ok": True, "old_serial": old_serial, "new_serial": new_serial})

    # Check new serial doesn't already exist in this batch
    if batch.items.filter(serial_number=new_serial).exclude(pk=item.pk).exists():
        return JsonResponse({"ok": False, "error": "Serial already in this batch"})

    # Check if new serial matches a DIFFERENT existing DrillBit
    existing_bit = DrillBit.objects.filter(serial_number=new_serial).first()
    if existing_bit and item.drill_bit and existing_bit.pk != item.drill_bit.pk:
        return JsonResponse({"ok": False, "error": f"Serial {new_serial} already registered to a different drill bit"})

    # Update BackloadItem serial
    item.serial_number = new_serial
    item.save(update_fields=["serial_number"])

    # Update DrillBit serial if one exists
    if item.drill_bit:
        item.drill_bit.serial_number = new_serial
        item.drill_bit.save(update_fields=["serial_number"])

        # Also update any OTHER BackloadItems that reference this drill_bit
        # (e.g. the same bit appearing in a different batch)
        BackloadItem.objects.filter(
            drill_bit=item.drill_bit
        ).exclude(pk=item.pk).update(serial_number=new_serial)

    return JsonResponse({"ok": True, "old_serial": old_serial, "new_serial": new_serial})


@login_required
@require_POST
def api_batch_replace_serial(request, pk):
    """Replace a serial (clean slate) — removes old item + DrillBit, creates fresh item.

    This is the nuclear option: deletes the old BackloadItem and its DrillBit
    (if the DrillBit has no WorkOrders), then creates a new item with the correct serial.
    """
    batch = get_object_or_404(BackloadBatch, pk=pk)
    data = json.loads(request.body)
    item_id = data.get("item_id")
    new_serial = data.get("new_serial", "").strip()

    item = get_object_or_404(BackloadItem, pk=item_id, batch=batch)
    old_serial = item.serial_number
    bit = item.drill_bit

    # Validate new serial
    digits = re.sub(r'\D', '', new_serial)
    if len(digits) not in (6, 8):
        return JsonResponse({"ok": False, "error": "Serial must be 6 or 8 digits"})
    new_serial = digits

    # Collect impact summary for the response
    impact = {"events_deleted": 0, "wo_orphaned": 0, "inspections_deleted": 0}

    if bit:
        # Count what will be affected
        impact["events_deleted"] = bit.bit_events.count()
        impact["wo_orphaned"] = bit.work_orders.count()
        impact["inspections_deleted"] = bit.receiving_inspections.count()

        # Detach BitEvent from item first
        if item.bit_event:
            item.bit_event = None
            item.save(update_fields=["bit_event"])

        # Cancel BOM requests for this bit
        BOMPendingRequest.objects.filter(
            drill_bit=bit,
            status=BOMPendingRequest.RequestStatus.OPEN,
        ).update(status=BOMPendingRequest.RequestStatus.CANCELLED)

        # If bit has WorkOrders → just detach (WOs survive, lose bit reference via SET_NULL)
        # If bit has no WOs → safe to delete (CASCADE removes BitEvents, Inspections, etc.)
        has_work_orders = bit.work_orders.exists()
        if not has_work_orders:
            # Detach item from bit before deleting bit (avoid FK issues)
            item.drill_bit = None
            item.save(update_fields=["drill_bit"])
            bit.delete()
        else:
            item.drill_bit = None
            item.save(update_fields=["drill_bit"])

    # Delete the old BackloadItem
    item.delete()

    # Create fresh item with new serial
    new_item = BackloadItem(
        batch=batch,
        serial_number=new_serial,
        sort_order=batch.items.count(),
    )
    new_item.save()
    new_item.attempt_match()

    # Auto-process if matched
    _auto_process_single_item(new_item, request.user, batch)

    # Update batch counts
    batch.update_counts()
    batch.auto_update_status()

    return JsonResponse({
        "ok": True,
        "old_serial": old_serial,
        "new_serial": new_serial,
        "impact": impact,
        "new_status": new_item.get_match_status_display(),
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
    """List all receiving inspections + bits awaiting inspection."""
    model = ReceivingInspection
    template_name = "workorders/receiving_inspection_list.html"
    context_object_name = "inspections"
    paginate_by = 25

    def get_queryset(self):
        qs = ReceivingInspection.objects.select_related(
            "drill_bit", "drill_bit__design", "drill_bit__design__size",
            "drill_bit__account",
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

        # Bits awaiting inspection: recently received (backloaded) bits
        # that do NOT have any ReceivingInspection yet
        from apps.workorders.models import DrillBit, BitEvent
        inspected_bit_ids = ReceivingInspection.objects.values_list("drill_bit_id", flat=True)
        awaiting = DrillBit.objects.filter(
            status__in=[
                DrillBit.Status.RECEIVING,
                DrillBit.Status.UNREGISTERED,
                DrillBit.Status.BACKLOADED,
                DrillBit.Status.IN_STOCK,
            ]
        ).exclude(
            pk__in=inspected_bit_ids
        ).select_related(
            "design", "design__size", "account",
        ).order_by("-created_at")[:50]
        ctx["awaiting_inspection"] = awaiting
        return ctx
