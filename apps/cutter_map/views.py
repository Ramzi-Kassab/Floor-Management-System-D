"""
Cutter Map Views

Handles PDF upload, extraction, editing, validation, and generation.
"""

import json
import os
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile

from .models import CutterMapDocument, CutterMapHistory
from .forms import CutterMapUploadForm
from .utils.pdf_extractor import extract_pdf_data
from .utils.pdf_generator import HalliburtonPDFGenerator
from .utils.ppt_generator import HalliburtonPPTGenerator


@login_required
def index(request):
    """Main cutter map page - list documents or show editor."""
    documents = CutterMapDocument.objects.filter(
        created_by=request.user
    ).order_by('-created_at')[:20]

    form = CutterMapUploadForm()

    # Check if coming from BOM create page with design info
    design_context = None
    if request.GET.get('from') == 'bom_create':
        design_context = {
            'design_id': request.GET.get('design_id'),
            'design_mat': request.GET.get('design_mat', ''),
            'design_hdbs': request.GET.get('design_hdbs', ''),
            'design_size': request.GET.get('design_size', ''),
            'from_bom_create': True
        }

    return render(request, 'cutter_map/index.html', {
        'documents': documents,
        'form': form,
        'design_context': design_context
    })


@login_required
@require_http_methods(['POST'])
def upload(request):
    """Handle PDF upload and extract data."""
    form = CutterMapUploadForm(request.POST, request.FILES)

    if not form.is_valid():
        return JsonResponse({
            'error': form.errors.get('original_pdf', ['Invalid file'])[0]
        }, status=400)

    # Save the document
    doc = form.save(commit=False)
    doc.created_by = request.user
    doc.original_filename = request.FILES['original_pdf'].name.rsplit('.', 1)[0]
    doc.save()

    # Record history
    CutterMapHistory.objects.create(
        document=doc,
        action=CutterMapHistory.Action.UPLOAD,
        user=request.user
    )

    try:
        # Extract data from PDF
        pdf_path = doc.original_pdf.path
        data = extract_pdf_data(pdf_path)

        # Store extracted data
        doc.extracted_data = data
        doc.mat_number = data.get('header', {}).get('mat_number', '')
        doc.sn_number = data.get('header', {}).get('sn_number', '')
        doc.status = CutterMapDocument.Status.EXTRACTED
        doc.save()

        # Record extraction
        CutterMapHistory.objects.create(
            document=doc,
            action=CutterMapHistory.Action.EXTRACT,
            user=request.user
        )

        # Add document ID and original filename to response
        data['document_id'] = doc.id
        data['original_filename'] = doc.original_filename

        return JsonResponse({
            'success': True,
            'data': data,
            'document_id': doc.id,
            'filename': doc.original_filename
        })

    except Exception as e:
        doc.delete()  # Clean up on failure
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(['POST'])
def save_edits(request, document_id):
    """Save edited data without generating PDF."""
    doc = get_object_or_404(CutterMapDocument, id=document_id, created_by=request.user)

    try:
        data = json.loads(request.body)
        doc.edited_data = data
        doc.status = CutterMapDocument.Status.EDITED
        doc.save()

        CutterMapHistory.objects.create(
            document=doc,
            action=CutterMapHistory.Action.EDIT,
            user=request.user,
            details={'changes': 'Data saved'}
        )

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(['POST'])
def validate(request, document_id=None):
    """Validate data before PDF generation."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    validation = {
        'is_valid': True,
        'messages': []
    }

    try:
        summary = data.get('summary', [])
        blades = data.get('blades', [])

        # Build BOM counts
        bom_counts = {}
        for item in summary:
            idx = item.get('index')
            count = item.get('count', 0)
            if idx is not None:
                bom_counts[idx] = count

        # Build CL counts
        cl_counts = {}
        for blade in blades:
            for row_key in ['r1', 'r2', 'r3', 'r4']:
                row = blade.get(row_key, {})
                if row:
                    for pos, cells in row.items():
                        if isinstance(cells, list):
                            for cell in cells:
                                grp = cell.get('group')
                                if grp:
                                    cl_counts[grp] = cl_counts.get(grp, 0) + 1

        # Check for count mismatches
        all_indices = set(bom_counts.keys()) | set(cl_counts.keys())
        for idx in sorted(all_indices):
            bom_count = bom_counts.get(idx, 0)
            cl_count = cl_counts.get(idx, 0)
            if bom_count != cl_count:
                validation['is_valid'] = False
                validation['messages'].append({
                    'type': 'warning',
                    'code': 'COUNT_MISMATCH',
                    'message': f"Count mismatch: BOM index {idx} has Qty={bom_count}, but CL has {cl_count} cutters"
                })

        # Check for CL groups not in BOM
        unmatched = set(cl_counts.keys()) - set(bom_counts.keys())
        if unmatched:
            validation['is_valid'] = False
            validation['messages'].append({
                'type': 'warning',
                'code': 'UNMATCHED_GROUPS',
                'message': f"CL has group references not in BOM: {sorted(unmatched)}"
            })

        # Check for empty data
        if not summary:
            validation['messages'].append({
                'type': 'warning',
                'code': 'EMPTY_BOM',
                'message': "BOM table is empty"
            })

        if not blades:
            validation['messages'].append({
                'type': 'warning',
                'code': 'EMPTY_CL',
                'message': "Cutter Layout (CL) is empty"
            })

        # Save validation results if document exists
        if document_id:
            doc = get_object_or_404(CutterMapDocument, id=document_id, created_by=request.user)
            doc.is_validated = validation['is_valid']
            doc.validation_messages = validation['messages']
            doc.save()

            CutterMapHistory.objects.create(
                document=doc,
                action=CutterMapHistory.Action.VALIDATE,
                user=request.user,
                details=validation
            )

        return JsonResponse(validation)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'is_valid': False,
            'messages': [{'type': 'error', 'code': 'VALIDATION_ERROR', 'message': str(e)}]
        })


@login_required
@require_http_methods(['POST'])
def generate_pdf(request, document_id=None):
    """Generate PDF from data."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    try:
        header = data.get('header', {})
        original_name = data.get('original_filename', header.get('mat_number', 'output'))
        output_filename = f"{original_name}.pdf"

        # Generate PDF
        generator = HalliburtonPDFGenerator()

        # Create temp file path
        output_dir = os.path.join(settings.MEDIA_ROOT, 'cutter_maps', 'generated')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)

        # Generate returns the actual path (may be .html if PDF backends unavailable)
        actual_output_path = generator.generate(data, output_path)
        actual_filename = os.path.basename(actual_output_path)
        is_html = actual_output_path.endswith('.html')

        # If document exists, save reference
        if document_id:
            doc = get_object_or_404(CutterMapDocument, id=document_id, created_by=request.user)
            doc.edited_data = data
            doc.status = CutterMapDocument.Status.GENERATED

            # Save file to model (only if PDF)
            if not is_html and os.path.exists(actual_output_path):
                with open(actual_output_path, 'rb') as f:
                    doc.generated_pdf.save(actual_filename, ContentFile(f.read()))
            doc.save()

            CutterMapHistory.objects.create(
                document=doc,
                action=CutterMapHistory.Action.GENERATE_PDF,
                user=request.user
            )

        # Determine file type and message
        if is_html:
            file_type = 'html'
            message = 'HTML file generated (PDF backends not available - install playwright or weasyprint)'
        else:
            file_type = 'pdf'
            message = None

        response_data = {
            'success': True,
            'filename': actual_filename,
            'download_url': f'/cutter-map/download/{actual_filename}',
            'output_path': actual_output_path,
            'file_type': file_type
        }
        if message:
            response_data['message'] = message

        return JsonResponse(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(['POST'])
def generate_ppt(request, document_id=None):
    """Generate PowerPoint from data."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    try:
        original_name = data.get('original_filename', data['header']['mat_number'])
        output_filename = f"{original_name}.pptx"

        # Generate PPT
        generator = HalliburtonPPTGenerator()

        # Create output path
        output_dir = os.path.join(settings.MEDIA_ROOT, 'cutter_maps', 'generated')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)

        generator.generate(data, output_path)

        # If document exists, save reference
        if document_id:
            doc = get_object_or_404(CutterMapDocument, id=document_id, created_by=request.user)

            # Save file to model
            with open(output_path, 'rb') as f:
                doc.generated_ppt.save(output_filename, ContentFile(f.read()))
            doc.save()

            CutterMapHistory.objects.create(
                document=doc,
                action=CutterMapHistory.Action.GENERATE_PPT,
                user=request.user
            )

        return JsonResponse({
            'success': True,
            'filename': output_filename,
            'download_url': f'/cutter-map/download/{output_filename}'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def download_pdf(request, document_id, filename):
    """Download generated PDF."""
    if document_id > 0:
        doc = get_object_or_404(CutterMapDocument, id=document_id, created_by=request.user)
        if doc.generated_pdf:
            return FileResponse(doc.generated_pdf.open(), as_attachment=True, filename=filename)

    # Fallback to file path
    file_path = os.path.join(settings.MEDIA_ROOT, 'cutter_maps', 'generated', filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)

    raise Http404("File not found")


@login_required
def download_ppt(request, document_id, filename):
    """Download generated PPT."""
    if document_id > 0:
        doc = get_object_or_404(CutterMapDocument, id=document_id, created_by=request.user)
        if doc.generated_ppt:
            return FileResponse(doc.generated_ppt.open(), as_attachment=True, filename=filename)

    # Fallback to file path
    file_path = os.path.join(settings.MEDIA_ROOT, 'cutter_maps', 'generated', filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)

    raise Http404("File not found")


@login_required
@require_http_methods(['POST'])
def export_json(request, document_id=None):
    """Export data as JSON."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    mat_number = data.get('header', {}).get('mat_number', 'export')
    output_filename = f"export_{mat_number}.json"

    output_dir = os.path.join(settings.MEDIA_ROOT, 'cutter_maps', 'exports')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    return JsonResponse({
        'success': True,
        'filename': output_filename,
        'download_url': f'/cutter-map/download/{output_filename}'
    })


@login_required
def download_json(request, filename):
    """Download exported JSON."""
    file_path = os.path.join(settings.MEDIA_ROOT, 'cutter_maps', 'exports', filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    raise Http404("File not found")


def download_file(request, filename):
    """
    Simple file download - matches Flask /download/<filename> pattern.
    No login required for direct file access (files are in generated folder).
    """
    # Check in generated folder
    file_path = os.path.join(settings.MEDIA_ROOT, 'cutter_maps', 'generated', filename)
    if os.path.exists(file_path):
        # Determine content type based on extension
        if filename.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif filename.lower().endswith('.pptx'):
            content_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        elif filename.lower().endswith('.json'):
            content_type = 'application/json'
        else:
            content_type = 'application/octet-stream'

        response = FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=filename,
            content_type=content_type
        )
        return response

    # Also check exports folder for JSON
    if filename.lower().endswith('.json'):
        file_path = os.path.join(settings.MEDIA_ROOT, 'cutter_maps', 'exports', filename)
        if os.path.exists(file_path):
            return FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=filename,
                content_type='application/json'
            )

    raise Http404("File not found")


@login_required
def editor(request, document_id):
    """Load editor with existing document."""
    doc = get_object_or_404(CutterMapDocument, id=document_id, created_by=request.user)

    return render(request, 'cutter_map/editor.html', {
        'document': doc,
        'data': doc.get_data()
    })


# =============================================================================
# API ENDPOINTS
# =============================================================================

@login_required
def api_lookup_design(request):
    """API: Lookup Design by MAT number."""
    from apps.technology.models import Design

    mat_no = request.GET.get('mat_no', '').strip()

    if not mat_no:
        return JsonResponse({'found': False, 'error': 'No MAT number provided'})

    try:
        design = Design.objects.filter(mat_no=mat_no).first()

        if design:
            return JsonResponse({
                'found': True,
                'design': {
                    'id': design.id,
                    'mat_no': design.mat_no,
                    'hdbs_type': design.hdbs_type,
                    'order_level': design.order_level,
                    'category': design.category,
                    'no_of_blades': design.no_of_blades,
                    'status': design.status,
                }
            })
        else:
            return JsonResponse({'found': False})

    except Exception as e:
        return JsonResponse({'found': False, 'error': str(e)})


@login_required
@require_http_methods(['POST'])
def api_sync_to_erp(request):
    """
    API: Sync extracted PDF data to ERP.

    Creates or links to L3/L4 Design, then creates:
    - L5 BOM with BOMLines
    - DesignPocketConfig entries (grouped by size + substrate_shape)
    - DesignPocket entries from blade CL data

    Accepts either:
    - design_id: Direct link to a pre-selected Design (from BOM create workflow)
    - parent_design_mat: MAT number to look up or create a Design
    """
    from apps.technology.models import (
        Design, BOM, BOMLine, PocketSize, PocketShape,
        DesignPocketConfig, DesignPocket
    )
    from apps.inventory.models import InventoryItem, ItemAttributeValue

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    document_id = payload.get('document_id')
    design_id = payload.get('design_id')  # Direct design ID from BOM create workflow
    parent_design_mat = payload.get('parent_design_mat', '').strip()
    data = payload.get('data', {})

    # Require either design_id or parent_design_mat
    if not design_id and not parent_design_mat:
        return JsonResponse({'success': False, 'error': 'Either design_id or Parent Design MAT is required'}, status=400)

    if not data:
        return JsonResponse({'success': False, 'error': 'No data provided'}, status=400)

    try:
        header = data.get('header', {})
        summary = data.get('summary', [])
        blades = data.get('blades', [])

        # 1. Find or create parent Design (L3/L4)
        parent_design = None

        # First try design_id (from BOM create workflow)
        if design_id:
            try:
                parent_design = Design.objects.get(pk=design_id)
            except Design.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'Design with ID {design_id} not found'}, status=400)

        # Fallback to parent_design_mat lookup/creation
        if not parent_design and parent_design_mat:
            parent_design = Design.objects.filter(mat_no=parent_design_mat).first()

            if not parent_design:
                # Create new Design as L3 (base design)
                parent_design = Design.objects.create(
                    mat_no=parent_design_mat,
                    hdbs_type=f"DRAFT-{parent_design_mat}",
                    category=Design.Category.FC,
                    order_level=Design.OrderLevel.LEVEL_3,
                    status=Design.Status.DRAFT,
                    no_of_blades=len(blades) if blades else None,
                    created_by=request.user
                )

        # Update blade count if we have data
        if blades and not parent_design.no_of_blades:
            parent_design.no_of_blades = len(blades)
            parent_design.save()

        # Determine pocket rows count from blades
        max_row = 1
        for blade in blades:
            for row_key in ['r1', 'r2', 'r3', 'r4']:
                if blade.get(row_key):
                    row_num = int(row_key[1])
                    max_row = max(max_row, row_num)

        if max_row > 1 and parent_design.pocket_rows_count != max_row:
            parent_design.pocket_rows_count = max_row
            parent_design.save()

        # 2. Create L5 BOM
        l5_mat = header.get('mat_number', f'L5-{parent_design_mat}')
        bom_code = l5_mat

        # Check if BOM already exists
        existing_bom = BOM.objects.filter(code=bom_code).first()
        if existing_bom:
            existing_bom.lines.all().delete()
            bom = existing_bom
        else:
            bom = BOM.objects.create(
                design=parent_design,
                code=bom_code,
                name=f"L5 BOM for {parent_design_mat}",
                revision=header.get('revision_level', 'A'),
                status=BOM.Status.DRAFT,
                created_by=request.user
            )

        # 3. Create BOM Lines and build index→item mapping
        # Option to create missing items (from payload)
        create_missing_items = payload.get('create_missing_items', False)

        bom_lines_created = 0
        items_matched = 0
        items_created = 0
        items_unmatched = []
        index_to_item_info = {}  # Maps BOM index to (size, substrate_shape, color)

        for item in summary:
            bom_index = item.get('index', bom_lines_created + 1)
            cutter_size = item.get('size', '')
            hdbs_code = item.get('mat_number', '')
            color_code = item.get('fill_color', '#4A4A4A')
            cutter_chamfer = item.get('chamfer', '')
            cutter_type = item.get('type', '')

            # Try to find matching inventory item
            inv_item = None
            substrate_shape = 'DEFAULT'

            if hdbs_code:
                # Try exact match on mat_number field
                inv_item = InventoryItem.objects.filter(mat_number=hdbs_code).first()

                if not inv_item:
                    # Try match on code field
                    inv_item = InventoryItem.objects.filter(code=hdbs_code).first()

                if not inv_item:
                    # Try attribute lookup (hdbs_code, hdbs, mat_number attributes)
                    attr_match = ItemAttributeValue.objects.filter(
                        attribute__attribute__code__in=['hdbs_code', 'hdbs', 'mat_number', 'hdbs_mat'],
                        text_value=hdbs_code
                    ).select_related('item').first()
                    if attr_match:
                        inv_item = attr_match.item

                if inv_item:
                    items_matched += 1
                    # Get substrate_shape attribute
                    shape_attr = ItemAttributeValue.objects.filter(
                        item=inv_item,
                        attribute__attribute__code__in=['substrate_shape', 'shape', 'pocket_shape']
                    ).first()
                    if shape_attr and shape_attr.text_value:
                        substrate_shape = shape_attr.text_value
                elif create_missing_items:
                    # Create new inventory item for unmatched HDBS code
                    display_name = f"{cutter_size} {cutter_type}".strip() or hdbs_code
                    inv_item = InventoryItem.objects.create(
                        code=hdbs_code,
                        name=display_name,
                        mat_number=hdbs_code,
                        item_type=InventoryItem.ItemType.COMPONENT,
                        unit='EA',
                        description=f"Auto-created from PDF import. Size: {cutter_size}, Type: {cutter_type}, Chamfer: {cutter_chamfer}"
                    )
                    items_created += 1
                else:
                    # Track unmatched items for reporting
                    items_unmatched.append({
                        'hdbs_code': hdbs_code,
                        'size': cutter_size,
                        'type': cutter_type
                    })

            # Create BOM Line with inventory_item link if matched/created
            BOMLine.objects.create(
                bom=bom,
                line_number=bom_index,
                order_number=bom_index,
                quantity=item.get('count', 1),
                cutter_size=cutter_size,
                cutter_chamfer=cutter_chamfer,
                cutter_type=cutter_type,
                hdbs_code=hdbs_code,
                family_number=item.get('family_number', ''),
                color_code=color_code,
                inventory_item=inv_item,  # Link to inventory (may be None if unmatched)
            )
            bom_lines_created += 1

            index_to_item_info[bom_index] = {
                'size': cutter_size,
                'shape': substrate_shape,
                'color': color_code,
                'count': item.get('count', 1)
            }

        # 4. Create DesignPocketConfig entries (grouped by size + shape)
        # Clear existing pockets FIRST (they reference pocket_configs via protected FK)
        # Then clear pocket_configs
        parent_design.pockets.all().delete()
        parent_design.pocket_configs.all().delete()

        # Group by (size, shape)
        config_groups = {}  # (size, shape) → {indices: [], count: 0, color: ''}
        for bom_index, info in index_to_item_info.items():
            key = (info['size'], info['shape'])
            if key not in config_groups:
                config_groups[key] = {
                    'indices': [],
                    'count': 0,
                    'color': info['color']
                }
            config_groups[key]['indices'].append(bom_index)
            config_groups[key]['count'] += info['count']

        # Create PocketSize and PocketShape records, then DesignPocketConfig
        index_to_config = {}  # Maps BOM index → DesignPocketConfig
        pocket_configs_created = 0

        for order, ((size_code, shape_code), group_info) in enumerate(config_groups.items(), start=1):
            # Find or create PocketSize
            pocket_size = PocketSize.objects.filter(code=size_code).first()
            if not pocket_size:
                pocket_size = PocketSize.objects.create(
                    code=size_code,
                    display_name=size_code,
                    is_active=True
                )

            # Find or create PocketShape
            pocket_shape = PocketShape.objects.filter(code=shape_code).first()
            if not pocket_shape:
                pocket_shape = PocketShape.objects.create(
                    code=shape_code,
                    name=shape_code,
                    is_active=True
                )

            # Create DesignPocketConfig
            config = DesignPocketConfig.objects.create(
                design=parent_design,
                order=order,
                pocket_size=pocket_size,
                pocket_shape=pocket_shape,
                count=group_info['count'],
                color_code=group_info['color'],
                row_number=1  # Default to row 1, will be refined by pocket positions
            )
            pocket_configs_created += 1

            # Map all indices in this group to this config
            for idx in group_info['indices']:
                index_to_config[idx] = config

        # 5. Create DesignPocket entries from blade CL data
        pockets_created = 0

        for blade in blades:
            blade_num = blade.get('blade_id', 1)
            position_in_blade = 0

            for row_key in ['r1', 'r2', 'r3', 'r4']:
                row_data = blade.get(row_key, {})
                if not row_data:
                    continue

                row_num = int(row_key[1])  # r1→1, r2→2, etc.
                position_in_row = 0

                # row_data is dict: {"1": [...], "2": [...], ...}
                for pos_key in sorted(row_data.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                    cells = row_data.get(pos_key, [])
                    if not isinstance(cells, list):
                        continue

                    for cell in cells:
                        group = cell.get('group')
                        if group is None:
                            continue

                        position_in_row += 1
                        position_in_blade += 1

                        # Find config for this group
                        config = index_to_config.get(group)
                        if not config:
                            # Fallback: use first config
                            config = parent_design.pocket_configs.first()
                            if not config:
                                continue

                        # Map blade location from position name
                        pos_name = cell.get('pos', '').upper()
                        blade_location = None
                        if 'CONE' in pos_name:
                            blade_location = DesignPocket.BladeLocation.CONE
                        elif 'NOSE' in pos_name:
                            blade_location = DesignPocket.BladeLocation.NOSE
                        elif 'TAPER' in pos_name:
                            blade_location = DesignPocket.BladeLocation.TAPER
                        elif 'SHOULDER' in pos_name:
                            blade_location = DesignPocket.BladeLocation.SHOULDER
                        elif 'GAGE' in pos_name or 'GAUGE' in pos_name:
                            blade_location = DesignPocket.BladeLocation.GAGE

                        DesignPocket.objects.create(
                            design=parent_design,
                            blade_number=blade_num,
                            row_number=row_num,
                            position_in_row=position_in_row,
                            position_in_blade=position_in_blade,
                            blade_location=blade_location,
                            pocket_config=config
                        )
                        pockets_created += 1

        # 6. Update CutterMapDocument if provided
        if document_id:
            doc = CutterMapDocument.objects.filter(id=document_id, created_by=request.user).first()
            if doc:
                doc.design = parent_design
                doc.status = CutterMapDocument.Status.SYNCED
                doc.save()

                CutterMapHistory.objects.create(
                    document=doc,
                    action=CutterMapHistory.Action.SYNC,
                    user=request.user,
                    details={
                        'design_id': parent_design.id,
                        'design_mat': parent_design.mat_no,
                        'bom_id': bom.id,
                        'bom_code': bom.code,
                        'bom_lines_created': bom_lines_created,
                        'pocket_configs_created': pocket_configs_created,
                        'pockets_created': pockets_created,
                        'items_matched': items_matched,
                        'items_created': items_created,
                        'items_unmatched': len(items_unmatched)
                    }
                )

        return JsonResponse({
            'success': True,
            'design_id': parent_design.id,
            'design_mat': parent_design.mat_no,
            'bom_id': bom.id,
            'bom_code': bom.code,
            'bom_lines_created': bom_lines_created,
            'pocket_configs_created': pocket_configs_created,
            'pockets_created': pockets_created,
            # Inventory matching statistics
            'inventory_stats': {
                'items_matched': items_matched,
                'items_created': items_created,
                'items_unmatched': len(items_unmatched),
                'unmatched_items': items_unmatched if items_unmatched else None
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
