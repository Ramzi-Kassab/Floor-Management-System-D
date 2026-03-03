"""
Drill Bit Photo API views.
All endpoints under /work-orders/drill-bits/<bit_pk>/photos/
"""
import base64
import json
import os
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from .models import DrillBit, DrillBitPhoto, build_adg_sequence, PHOTO_SETS


def _photo_to_dict(photo):
    """Serialize a DrillBitPhoto to JSON-safe dict."""
    return {
        'id': photo.pk,
        'display_name': photo.display_name,
        'category': photo.category,
        'blade_number': photo.blade_number,
        'photo_number': photo.photo_number,
        'file_url': photo.file_url,
        'original_url': photo.original_url,
        'has_edits': photo.has_edits,
        'capture_mode': photo.capture_mode,
        'sort_order': photo.sort_order,
        'original_filename': photo.original_filename,
        'uploaded_by': (photo.uploaded_by.get_full_name() or photo.uploaded_by.username)
                       if photo.uploaded_by else '',
        'uploaded_at': photo.uploaded_at.strftime('%b %d, %Y %H:%M') if photo.uploaded_at else '',
    }


@login_required
@require_GET
def api_photo_list(request, bit_pk):
    """
    GET /work-orders/drill-bits/<bit_pk>/photos/
    Query params: context_type, context_id (optional filters)
    """
    bit = get_object_or_404(DrillBit, pk=bit_pk)
    qs = DrillBitPhoto.objects.filter(drill_bit=bit)

    ctx_type = request.GET.get('context_type')
    ctx_id = request.GET.get('context_id')
    if ctx_type:
        qs = qs.filter(context_type=ctx_type)
    if ctx_id:
        qs = qs.filter(context_id=ctx_id)

    photos = [_photo_to_dict(p) for p in qs.select_related('uploaded_by')]
    return JsonResponse({'photos': photos})


@login_required
@require_POST
def api_photo_upload(request, bit_pk):
    """
    POST /work-orders/drill-bits/<bit_pk>/photos/upload/
    Multipart form: file + metadata fields.
    """
    bit = get_object_or_404(DrillBit, pk=bit_pk)
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)

    # Metadata from form fields
    display_name = request.POST.get('display_name', '').strip()
    category = request.POST.get('category', 'BLADE').strip()
    blade_number = request.POST.get('blade_number')
    photo_number = request.POST.get('photo_number', '1')
    capture_mode = request.POST.get('capture_mode', 'FREE').strip()
    context_type = request.POST.get('context_type', 'GENERAL').strip()
    context_id = request.POST.get('context_id')
    sort_order = request.POST.get('sort_order', '0')

    # Validate category
    valid_categories = [c[0] for c in DrillBitPhoto.Category.choices]
    if category not in valid_categories:
        category = 'BLADE'

    # Auto-generate sort_order if not provided
    if not sort_order or sort_order == '0':
        last = DrillBitPhoto.objects.filter(drill_bit=bit).order_by('-sort_order').first()
        sort_order = (last.sort_order + 1) if last else 1

    photo = DrillBitPhoto.objects.create(
        drill_bit=bit,
        file=file,
        display_name=display_name or file.name,
        category=category,
        blade_number=int(blade_number) if blade_number else None,
        photo_number=int(photo_number) if photo_number else 1,
        capture_mode=capture_mode,
        context_type=context_type,
        context_id=int(context_id) if context_id else None,
        sort_order=int(sort_order),
        original_filename=file.name,
        uploaded_by=request.user,
    )
    return JsonResponse({'success': True, 'photo': _photo_to_dict(photo)})


@login_required
@require_POST
def api_photo_delete(request, bit_pk, photo_pk):
    """POST /work-orders/drill-bits/<bit_pk>/photos/<photo_pk>/delete/"""
    photo = get_object_or_404(DrillBitPhoto, pk=photo_pk, drill_bit__pk=bit_pk)
    if photo.edited_file:
        photo.edited_file.delete(save=False)
    if photo.file:
        photo.file.delete(save=False)
    photo.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def api_photo_rename(request, bit_pk, photo_pk):
    """POST /work-orders/drill-bits/<bit_pk>/photos/<photo_pk>/rename/"""
    photo = get_object_or_404(DrillBitPhoto, pk=photo_pk, drill_bit__pk=bit_pk)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    new_name = data.get('display_name', '').strip()
    if not new_name:
        return JsonResponse({'success': False, 'error': 'display_name required'}, status=400)

    photo.display_name = new_name
    photo.save(update_fields=['display_name'])
    return JsonResponse({'success': True, 'display_name': photo.display_name})


@login_required
@require_POST
def api_photo_reorder(request, bit_pk):
    """
    POST /work-orders/drill-bits/<bit_pk>/photos/reorder/
    Body: JSON {order: [pk1, pk2, ...]}
    """
    bit = get_object_or_404(DrillBit, pk=bit_pk)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    order = data.get('order', [])
    for idx, pk in enumerate(order):
        DrillBitPhoto.objects.filter(pk=pk, drill_bit=bit).update(sort_order=idx + 1)

    return JsonResponse({'success': True})


@login_required
@require_POST
def api_photo_save_edit(request, bit_pk, photo_pk):
    """
    POST /work-orders/drill-bits/<bit_pk>/photos/<photo_pk>/save-edit/
    Body: JSON {image_data: "data:image/png;base64,..."}
    Saves the Fabric.js canvas export as edited_file (non-destructive).
    """
    photo = get_object_or_404(DrillBitPhoto, pk=photo_pk, drill_bit__pk=bit_pk)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    image_data = data.get('image_data', '')
    if not image_data:
        return JsonResponse({'success': False, 'error': 'image_data required'}, status=400)

    # Strip data-URI prefix
    if ',' in image_data:
        image_data = image_data.split(',', 1)[1]

    try:
        image_bytes = base64.b64decode(image_data)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid base64'}, status=400)

    # Delete old edited_file if exists
    if photo.edited_file:
        photo.edited_file.delete(save=False)

    filename = f"edit_{photo.pk}_{uuid.uuid4().hex[:8]}.png"
    photo.edited_file.save(filename, ContentFile(image_bytes), save=True)

    return JsonResponse({'success': True, 'edited_url': photo.edited_file.url})


@login_required
@require_POST
def api_photo_discard_edit(request, bit_pk, photo_pk):
    """
    POST /work-orders/drill-bits/<bit_pk>/photos/<photo_pk>/discard-edit/
    Deletes edited_file, reverts to original.
    """
    photo = get_object_or_404(DrillBitPhoto, pk=photo_pk, drill_bit__pk=bit_pk)
    if photo.edited_file:
        photo.edited_file.delete(save=False)
        photo.edited_file = None
        photo.save(update_fields=['edited_file'])
    return JsonResponse({'success': True, 'file_url': photo.file.url if photo.file else ''})


@login_required
@require_GET
def api_adg_sequence(request, bit_pk):
    """
    GET /work-orders/drill-bits/<bit_pk>/photos/adg-sequence/
    Returns photo sets (Before, After, ADG) each with their own slot grid.
    Blade count from BOM source_data.blades, default 6.
    """
    bit = get_object_or_404(DrillBit, pk=bit_pk)

    # Determine blade count from BOM
    blade_count = 6  # default
    bom = getattr(bit, 'brazing_bom', None) or getattr(bit, 'system_bom', None)
    if bom and hasattr(bom, 'source_data') and bom.source_data:
        blades = bom.source_data.get('blades', [])
        if blades:
            blade_count = len(blades)

    serial = bit.serial_number or ''

    # Load ALL existing photos for this bit (once)
    existing = DrillBitPhoto.objects.filter(drill_bit=bit).select_related('uploaded_by')
    photo_map = {}
    for p in existing:
        if p.display_name:
            photo_map[p.display_name] = _photo_to_dict(p)

    # Build backward-compat map for old format (B1-Ph1 → first set)
    # Old photos without set prefix match to the first set (Before)
    old_compat_map = {}  # old_name → new_name (first set only)

    sets = []
    for idx, set_name in enumerate(PHOTO_SETS):
        sequence = build_adg_sequence(blade_count, serial, set_name)

        # Build old-format compat map for first set only
        if idx == 0:
            for slot in sequence:
                cat = slot['category']
                if cat == 'BLADE':
                    old_name = f"B{slot['blade_number']}-Ph{slot['photo_number']}"
                elif cat == 'TOP':
                    old_name = 'Top'
                elif cat == 'SIDE':
                    old_name = 'Side'
                else:
                    old_name = f"Extra-{slot['photo_number']}"
                old_compat_map[old_name] = slot['display_name']
                # Also map no-set-prefix format (serial_B1_P1 without set)
                parts = [p for p in [serial] if p]
                no_set_prefix = '_'.join(parts) + '_' if parts else ''
                if cat == 'BLADE':
                    old_compat_map[f"{no_set_prefix}B{slot['blade_number']}_P{slot['photo_number']}"] = slot['display_name']
                elif cat == 'TOP':
                    old_compat_map[f"{no_set_prefix}Top"] = slot['display_name']
                elif cat == 'SIDE':
                    old_compat_map[f"{no_set_prefix}Side"] = slot['display_name']
                else:
                    old_compat_map[f"{no_set_prefix}Extra_{slot['photo_number']}"] = slot['display_name']

        # Overlay existing photos
        filled = 0
        for slot in sequence:
            slot['photo'] = photo_map.get(slot['display_name'], None)
            # Backward compat for first set
            if not slot['photo'] and idx == 0:
                for old_name, new_name in old_compat_map.items():
                    if new_name == slot['display_name'] and old_name in photo_map:
                        slot['photo'] = photo_map[old_name]
                        break
            if slot['photo']:
                filled += 1

        sets.append({
            'name': set_name,
            'sequence': sequence,
            'total_slots': len(sequence),
            'filled_slots': filled,
        })

    return JsonResponse({
        'sets': sets,
        'blade_count': blade_count,
        'set_names': PHOTO_SETS,
    })
