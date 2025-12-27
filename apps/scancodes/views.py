"""
ARDT FMS - Scan Codes Views
Version: 5.4

Views for scan code management and scanning operations.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView

from .models import ScanCode, ScanLog
from .forms import ScanCodeForm, ScanLogFilterForm, QuickScanForm


# =============================================================================
# SCAN CODE VIEWS
# =============================================================================


class ScanCodeListView(LoginRequiredMixin, ListView):
    """List all scan codes with filtering."""

    model = ScanCode
    template_name = "scancodes/scancode_list.html"
    context_object_name = "scancodes"
    paginate_by = 25

    def get_queryset(self):
        queryset = ScanCode.objects.select_related('created_by').annotate(
            scan_count=Count('scan_logs')
        ).order_by('-created_at')

        # Filter by code type
        code_type = self.request.GET.get("code_type")
        if code_type:
            queryset = queryset.filter(code_type=code_type)

        # Filter by entity type
        entity_type = self.request.GET.get("entity_type")
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)

        # Filter by status
        status = self.request.GET.get("status")
        if status == "active":
            queryset = queryset.filter(is_active=True)
        elif status == "inactive":
            queryset = queryset.filter(is_active=False)

        # Filter by external
        external = self.request.GET.get("external")
        if external == "yes":
            queryset = queryset.filter(is_external=True)
        elif external == "no":
            queryset = queryset.filter(is_external=False)

        # Search
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(external_source__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Scan Codes"
        context["code_types"] = ScanCode.CodeType.choices
        context["entity_types"] = ScanCode.EntityType.choices
        context["current_code_type"] = self.request.GET.get("code_type", "")
        context["current_entity_type"] = self.request.GET.get("entity_type", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class ScanCodeDetailView(LoginRequiredMixin, DetailView):
    """View scan code details with scan history."""

    model = ScanCode
    template_name = "scancodes/scancode_detail.html"
    context_object_name = "scancode"

    def get_queryset(self):
        return ScanCode.objects.select_related('created_by').prefetch_related('scan_logs__scanned_by')

    def get_context_data(self, **kwargs):
        from apps.inventory.utils import generate_qr_code_base64, generate_barcode_base64

        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Scan Code: {self.object.code}"
        context["recent_scans"] = self.object.scan_logs.all()[:20]

        # Generate code image based on type
        if self.object.code_type == 'QR':
            context["code_image"] = generate_qr_code_base64(self.object.code, size=8, border=2)
        elif self.object.code_type == 'BARCODE':
            context["code_image"] = generate_barcode_base64(self.object.code, 'code128')
        else:
            context["code_image"] = generate_qr_code_base64(self.object.code, size=8, border=2)

        return context


class ScanCodeCreateView(LoginRequiredMixin, CreateView):
    """Create a new scan code."""

    model = ScanCode
    form_class = ScanCodeForm
    template_name = "scancodes/scancode_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Register New Scan Code"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Scan code '{form.instance.code}' registered successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("scancodes:scancode-detail", kwargs={"pk": self.object.pk})


class ScanCodeUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing scan code."""

    model = ScanCode
    form_class = ScanCodeForm
    template_name = "scancodes/scancode_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit: {self.object.code}"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Scan code '{form.instance.code}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("scancodes:scancode-detail", kwargs={"pk": self.object.pk})


class ScanCodeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a scan code."""

    model = ScanCode
    template_name = "scancodes/scancode_confirm_delete.html"
    success_url = reverse_lazy("scancodes:scancode-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete: {self.object.code}"
        return context


# =============================================================================
# SCAN LOG VIEWS
# =============================================================================


class ScanLogListView(LoginRequiredMixin, ListView):
    """List all scan logs with filtering."""

    model = ScanLog
    template_name = "scancodes/scanlog_list.html"
    context_object_name = "scanlogs"
    paginate_by = 50

    def get_queryset(self):
        queryset = ScanLog.objects.select_related(
            'scan_code', 'scanned_by', 'work_order', 'location'
        ).order_by('-scanned_at')

        # Filter by purpose
        purpose = self.request.GET.get("purpose")
        if purpose:
            queryset = queryset.filter(purpose=purpose)

        # Filter by validity
        is_valid = self.request.GET.get("is_valid")
        if is_valid == "true":
            queryset = queryset.filter(is_valid=True)
        elif is_valid == "false":
            queryset = queryset.filter(is_valid=False)

        # Filter by date
        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(scanned_at__date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(scanned_at__date__lte=date_to)

        # Search by code
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(raw_code__icontains=search)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Scan History"
        context["purposes"] = ScanLog.Purpose.choices
        context["filter_form"] = ScanLogFilterForm(self.request.GET)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class ScanLogDetailView(LoginRequiredMixin, DetailView):
    """View scan log details."""

    model = ScanLog
    template_name = "scancodes/scanlog_detail.html"
    context_object_name = "scanlog"

    def get_queryset(self):
        return ScanLog.objects.select_related(
            'scan_code', 'scanned_by', 'work_order', 'step_execution', 'location'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Scan Log #{self.object.pk}"
        return context


# =============================================================================
# SCANNER VIEWS
# =============================================================================


class ScannerView(LoginRequiredMixin, TemplateView):
    """Quick scan interface."""

    template_name = "scancodes/scanner.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Scanner"
        context["form"] = QuickScanForm()
        return context


class VerifyScanView(LoginRequiredMixin, View):
    """API endpoint to verify a scanned code."""

    def post(self, request):
        code = request.POST.get('code', '').strip()
        purpose = request.POST.get('purpose', 'IDENTIFY')

        if not code:
            return JsonResponse({'success': False, 'error': 'No code provided'}, status=400)

        # Look up the scan code
        scan_code = ScanCode.objects.filter(code=code).first()

        # Create scan log
        scan_log = ScanLog.objects.create(
            scan_code=scan_code,
            raw_code=code,
            purpose=purpose,
            is_valid=scan_code is not None and scan_code.is_active,
            validation_message='Code verified' if scan_code else 'Unknown code',
            scanned_by=request.user,
            device_info=request.META.get('HTTP_USER_AGENT', '')[:200]
        )

        if scan_code and scan_code.is_active:
            return JsonResponse({
                'success': True,
                'scan_log_id': scan_log.pk,
                'code': scan_code.code,
                'code_type': scan_code.get_code_type_display(),
                'entity_type': scan_code.get_entity_type_display(),
                'entity_id': scan_code.entity_id,
                'is_external': scan_code.is_external,
                'external_source': scan_code.external_source,
            })
        elif scan_code and not scan_code.is_active:
            return JsonResponse({
                'success': False,
                'scan_log_id': scan_log.pk,
                'error': 'Code is inactive',
                'code': scan_code.code
            })
        else:
            return JsonResponse({
                'success': False,
                'scan_log_id': scan_log.pk,
                'error': 'Unknown code'
            })


class GenerateCodeView(LoginRequiredMixin, TemplateView):
    """Generate QR codes for entities."""

    template_name = "scancodes/generate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Generate QR Codes"
        context["entity_types"] = ScanCode.EntityType.choices
        return context

    def post(self, request, *args, **kwargs):
        """Handle QR code generation request."""
        import json
        import uuid
        from apps.inventory.utils import generate_qr_code_base64

        entity_type = request.POST.get('entity_type', '')
        entity_id = request.POST.get('entity_id', '')
        custom_data = request.POST.get('custom_data', '').strip()

        # Validate inputs
        errors = []
        if not entity_type:
            errors.append("Entity type is required.")

        parsed_data = None
        if custom_data:
            try:
                parsed_data = json.loads(custom_data)
            except json.JSONDecodeError:
                errors.append("Invalid JSON in custom data field.")

        if errors:
            context = self.get_context_data(**kwargs)
            context['errors'] = errors
            return self.render_to_response(context)

        # Generate unique code
        entity_id_int = int(entity_id) if entity_id else None
        code_prefix = f"ARDT-{entity_type[:3]}"
        unique_id = str(uuid.uuid4())[:8].upper()

        if entity_id_int:
            code = f"{code_prefix}-{entity_id_int}-{unique_id}"
        else:
            code = f"{code_prefix}-{unique_id}"

        # Create or get scan code
        scan_code, created = ScanCode.objects.get_or_create(
            code=code,
            defaults={
                'code_type': ScanCode.CodeType.QR,
                'entity_type': entity_type,
                'entity_id': entity_id_int,
                'encoded_data': parsed_data,
                'created_by': request.user,
            }
        )

        # Generate QR code image
        qr_image = generate_qr_code_base64(code, size=8, border=2)

        context = self.get_context_data(**kwargs)
        context['generated_code'] = scan_code
        context['qr_image'] = qr_image
        context['is_new'] = created
        return self.render_to_response(context)


class BatchGenerateView(LoginRequiredMixin, View):
    """Generate QR codes for multiple entities."""

    def get(self, request):
        entity_type = request.GET.get('type', '')
        from apps.inventory.utils import generate_qr_code_base64

        items = []
        if entity_type == 'INVENTORY_ITEM':
            from apps.inventory.models import InventoryItem
            items = InventoryItem.objects.filter(is_active=True)[:50]
        elif entity_type == 'LOCATION':
            from apps.inventory.models import InventoryLocation
            items = InventoryLocation.objects.filter(is_active=True)[:50]

        # Generate codes for each item
        generated = []
        for item in items:
            code = f"ARDT-{entity_type[:3]}-{item.pk}"

            scan_code, created = ScanCode.objects.get_or_create(
                entity_type=entity_type,
                entity_id=item.pk,
                defaults={
                    'code': code,
                    'code_type': ScanCode.CodeType.QR,
                    'created_by': request.user,
                }
            )

            generated.append({
                'item': item,
                'scan_code': scan_code,
                'qr_image': generate_qr_code_base64(scan_code.code, size=6, border=2),
                'is_new': created,
            })

        return JsonResponse({
            'success': True,
            'count': len(generated),
            'items': [{'code': g['scan_code'].code, 'id': g['item'].pk} for g in generated]
        })
