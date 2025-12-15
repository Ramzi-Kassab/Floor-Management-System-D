"""
ARDT FMS - Technology Views
Version: 5.4 - Sprint 3

Views for Design, BOM, and Cutter Layout management.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View

from django.http import JsonResponse

from .forms import BOMForm, BOMLineForm, BreakerSlotForm, ConnectionForm, DesignCutterLayoutForm, DesignForm
from .models import BOM, BOMLine, BreakerSlot, Connection, ConnectionSize, ConnectionType, Design, DesignCutterLayout


# =============================================================================
# DESIGN VIEWS
# =============================================================================


class DesignListView(LoginRequiredMixin, ListView):
    """List all designs with filtering."""

    model = Design
    template_name = "technology/design_list.html"
    context_object_name = "designs"
    paginate_by = 25

    def get_queryset(self):
        queryset = Design.objects.select_related("designed_by", "created_by").order_by("code")

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(name__icontains=search) | Q(iadc_code__icontains=search)
            )

        bit_type = self.request.GET.get("bit_type")
        if bit_type:
            queryset = queryset.filter(bit_type=bit_type)

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Designs"
        context["search_query"] = self.request.GET.get("q", "")
        context["current_bit_type"] = self.request.GET.get("bit_type", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["bit_type_choices"] = Design.Category.choices
        context["status_choices"] = Design.Status.choices
        return context


class DesignDetailView(LoginRequiredMixin, DetailView):
    """View design details with BOM and cutter layouts."""

    model = Design
    template_name = "technology/design_detail.html"
    context_object_name = "design"

    def get_queryset(self):
        return Design.objects.select_related("designed_by", "approved_by", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Design {self.object.hdbs_type}"
        context["boms"] = self.object.boms.select_related("created_by").order_by("-created_at")
        context["cutter_layouts"] = self.object.cutter_layouts.order_by("blade_number", "position_number")
        context["work_orders_count"] = self.object.work_orders.count()
        return context


class DesignCreateView(LoginRequiredMixin, CreateView):
    """Create a new design."""

    model = Design
    form_class = DesignForm
    template_name = "technology/design_form.html"
    success_url = reverse_lazy("technology:design_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Design"
        context["submit_text"] = "Create Design"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Design {form.instance.hdbs_type} created successfully.")
        return super().form_valid(form)


class DesignUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing design."""

    model = Design
    form_class = DesignForm
    template_name = "technology/design_form.html"

    def get_success_url(self):
        return reverse_lazy("technology:design_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Design {self.object.hdbs_type}"
        context["submit_text"] = "Update Design"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Design {self.object.hdbs_type} updated successfully.")
        return super().form_valid(form)


# =============================================================================
# BOM VIEWS
# =============================================================================


class BOMListView(LoginRequiredMixin, ListView):
    """List all BOMs."""

    model = BOM
    template_name = "technology/bom_list.html"
    context_object_name = "boms"
    paginate_by = 25

    def get_queryset(self):
        queryset = BOM.objects.select_related("design", "created_by").order_by("-created_at")

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(name__icontains=search) | Q(design__code__icontains=search)
            )

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Bills of Materials"
        context["search_query"] = self.request.GET.get("q", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["status_choices"] = BOM.Status.choices
        return context


class BOMDetailView(LoginRequiredMixin, DetailView):
    """View BOM details with line items."""

    model = BOM
    template_name = "technology/bom_detail.html"
    context_object_name = "bom"

    def get_queryset(self):
        return BOM.objects.select_related("design", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"BOM {self.object.code}"
        context["lines"] = self.object.lines.select_related("inventory_item").order_by("line_number")
        context["total_cost"] = self.object.total_cost
        context["line_form"] = BOMLineForm()
        return context


class BOMCreateView(LoginRequiredMixin, CreateView):
    """Create a new BOM."""

    model = BOM
    form_class = BOMForm
    template_name = "technology/bom_form.html"
    success_url = reverse_lazy("technology:bom_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create BOM"
        context["submit_text"] = "Create BOM"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"BOM {form.instance.code} created successfully.")
        return super().form_valid(form)


class BOMUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing BOM."""

    model = BOM
    form_class = BOMForm
    template_name = "technology/bom_form.html"

    def get_success_url(self):
        return reverse_lazy("technology:bom_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit BOM {self.object.code}"
        context["submit_text"] = "Update BOM"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"BOM {self.object.code} updated successfully.")
        return super().form_valid(form)


class BOMLineCreateView(LoginRequiredMixin, View):
    """Add a line to a BOM."""

    def post(self, request, pk):
        bom = get_object_or_404(BOM, pk=pk)
        form = BOMLineForm(request.POST)
        if form.is_valid():
            line = form.save(commit=False)
            line.bom = bom
            line.save()
            messages.success(request, "Line added successfully.")
        else:
            messages.error(request, "Failed to add line.")
        return redirect("technology:bom_detail", pk=pk)


class BOMLineDeleteView(LoginRequiredMixin, View):
    """Delete a line from a BOM."""

    def post(self, request, pk, line_pk):
        line = get_object_or_404(BOMLine, pk=line_pk, bom_id=pk)
        line.delete()
        messages.success(request, "Line deleted.")
        return redirect("technology:bom_detail", pk=pk)


# =============================================================================
# CUTTER LAYOUT VIEWS
# =============================================================================


class CutterLayoutCreateView(LoginRequiredMixin, View):
    """Add a cutter layout to a design."""

    def post(self, request, design_pk):
        design = get_object_or_404(Design, pk=design_pk)
        form = DesignCutterLayoutForm(request.POST)
        if form.is_valid():
            layout = form.save(commit=False)
            layout.design = design
            layout.save()
            messages.success(request, "Cutter layout added.")
        else:
            messages.error(request, "Failed to add cutter layout.")
        return redirect("technology:design_detail", pk=design_pk)


class CutterLayoutDeleteView(LoginRequiredMixin, View):
    """Delete a cutter layout from a design."""

    def post(self, request, design_pk, layout_pk):
        layout = get_object_or_404(DesignCutterLayout, pk=layout_pk, design_id=design_pk)
        layout.delete()
        messages.success(request, "Cutter layout deleted.")
        return redirect("technology:design_detail", pk=design_pk)


# =============================================================================
# API VIEWS (for modal pickers)
# =============================================================================


class APIConnectionsView(LoginRequiredMixin, View):
    """API endpoint for connection selection modal."""

    def get(self, request):
        # Get filter parameters
        q = request.GET.get('q', '')
        type_id = request.GET.get('type', '')
        size_id = request.GET.get('size', '')
        can_replace = request.GET.get('can_replace', '')

        # Base queryset
        queryset = Connection.objects.filter(is_active=True).select_related(
            'connection_type', 'connection_size', 'upper_section_type'
        )

        # Apply filters
        if q:
            queryset = queryset.filter(mat_no__icontains=q)
        if type_id:
            queryset = queryset.filter(connection_type_id=type_id)
        if size_id:
            queryset = queryset.filter(connection_size_id=size_id)
        if can_replace == 'true':
            queryset = queryset.filter(can_replace_in_ksa=True)
        elif can_replace == 'false':
            queryset = queryset.filter(can_replace_in_ksa=False)

        # Build response
        connections = []
        for conn in queryset[:100]:
            connections.append({
                'id': conn.id,
                'mat_no': conn.mat_no,
                'type': conn.connection_type.code,
                'type_name': conn.connection_type.name,
                'size': conn.connection_size.size_inches,
                'upper_section': conn.upper_section_type.name if conn.upper_section_type else None,
                'can_replace_in_ksa': conn.can_replace_in_ksa,
                'special_features': conn.special_features,
            })

        # Build filter options
        types = ConnectionType.objects.filter(is_active=True).values('id', 'code', 'name')
        sizes = ConnectionSize.objects.filter(is_active=True).values('id', 'size_inches')

        return JsonResponse({
            'connections': connections,
            'filters': {
                'types': [{'id': t['id'], 'code': t['code'], 'name': t['name']} for t in types],
                'sizes': [{'id': s['id'], 'size': s['size_inches']} for s in sizes],
            }
        })


class APIBreakerSlotsView(LoginRequiredMixin, View):
    """API endpoint for breaker slot selection modal."""

    def get(self, request):
        # Get filter parameters
        q = request.GET.get('q', '')
        material = request.GET.get('material', '')
        min_width = request.GET.get('min_width', '')
        max_width = request.GET.get('max_width', '')

        # Base queryset
        queryset = BreakerSlot.objects.filter(is_active=True)

        # Apply filters
        if q:
            queryset = queryset.filter(mat_no__icontains=q)
        if material:
            queryset = queryset.filter(material=material)
        if min_width:
            queryset = queryset.filter(slot_width__gte=float(min_width))
        if max_width:
            queryset = queryset.filter(slot_width__lte=float(max_width))

        # Build response
        breaker_slots = []
        for slot in queryset[:100]:
            breaker_slots.append({
                'id': slot.id,
                'mat_no': slot.mat_no,
                'slot_width': str(slot.slot_width),
                'slot_depth': str(slot.slot_depth),
                'slot_length': str(slot.slot_length) if slot.slot_length else None,
                'material': slot.material,
                'material_display': slot.get_material_display(),
                'hardness': slot.hardness,
                'compatible_sizes': list(slot.compatible_sizes.values_list('size', flat=True)),
            })

        # Build filter options - material choices from model
        materials = [{'code': code, 'name': name} for code, name in BreakerSlot.Material.choices]

        return JsonResponse({
            'breaker_slots': breaker_slots,
            'filters': {
                'materials': materials,
            }
        })


# =============================================================================
# CONNECTION CRUD VIEWS
# =============================================================================


class ConnectionListView(LoginRequiredMixin, ListView):
    """List all connections with filtering."""

    model = Connection
    template_name = "technology/connection_list.html"
    context_object_name = "connections"
    paginate_by = 25

    def get_queryset(self):
        queryset = Connection.objects.select_related(
            'connection_type', 'connection_size', 'upper_section_type'
        ).order_by('mat_no')

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(mat_no__icontains=search) |
                Q(connection_type__code__icontains=search) |
                Q(connection_type__name__icontains=search)
            )

        type_filter = self.request.GET.get("type")
        if type_filter:
            queryset = queryset.filter(connection_type_id=type_filter)

        size_filter = self.request.GET.get("size")
        if size_filter:
            queryset = queryset.filter(connection_size_id=size_filter)

        ksa_filter = self.request.GET.get("ksa")
        if ksa_filter == "yes":
            queryset = queryset.filter(can_replace_in_ksa=True)
        elif ksa_filter == "no":
            queryset = queryset.filter(can_replace_in_ksa=False)

        if not self.request.GET.get("show_inactive"):
            queryset = queryset.filter(is_active=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["connection_types"] = ConnectionType.objects.filter(is_active=True)
        context["connection_sizes"] = ConnectionSize.objects.filter(is_active=True)
        return context


class ConnectionDetailView(LoginRequiredMixin, DetailView):
    """View connection details including related designs."""

    model = Connection
    template_name = "technology/connection_detail.html"
    context_object_name = "connection"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get designs using this connection
        context["related_designs"] = self.object.designs.select_related('size').order_by('hdbs_type')
        return context


class ConnectionCreateView(LoginRequiredMixin, CreateView):
    """Create a new connection."""

    model = Connection
    form_class = ConnectionForm
    template_name = "technology/connection_form.html"
    success_url = reverse_lazy("technology:connection_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Connection"
        context["submit_text"] = "Create Connection"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Connection {form.instance.mat_no} created successfully.")
        return super().form_valid(form)


class ConnectionUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing connection."""

    model = Connection
    form_class = ConnectionForm
    template_name = "technology/connection_form.html"

    def get_success_url(self):
        return reverse_lazy("technology:connection_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Connection {self.object.mat_no}"
        context["submit_text"] = "Update Connection"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Connection {self.object.mat_no} updated successfully.")
        return super().form_valid(form)


class ConnectionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a connection."""

    model = Connection
    template_name = "technology/connection_confirm_delete.html"
    success_url = reverse_lazy("technology:connection_list")

    def form_valid(self, form):
        messages.success(self.request, f"Connection {self.object.mat_no} deleted.")
        return super().form_valid(form)


# =============================================================================
# BREAKER SLOT CRUD VIEWS
# =============================================================================


class BreakerSlotListView(LoginRequiredMixin, ListView):
    """List all breaker slots with filtering."""

    model = BreakerSlot
    template_name = "technology/breaker_slot_list.html"
    context_object_name = "breaker_slots"
    paginate_by = 25

    def get_queryset(self):
        queryset = BreakerSlot.objects.prefetch_related('compatible_sizes').order_by('mat_no')

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(mat_no__icontains=search)

        material_filter = self.request.GET.get("material")
        if material_filter:
            queryset = queryset.filter(material=material_filter)

        if not self.request.GET.get("show_inactive"):
            queryset = queryset.filter(is_active=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["material_choices"] = BreakerSlot.Material.choices
        return context


class BreakerSlotDetailView(LoginRequiredMixin, DetailView):
    """View breaker slot details including related designs."""

    model = BreakerSlot
    template_name = "technology/breaker_slot_detail.html"
    context_object_name = "breaker_slot"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get designs using this breaker slot
        context["related_designs"] = self.object.designs.select_related('size').order_by('hdbs_type')
        return context


class BreakerSlotCreateView(LoginRequiredMixin, CreateView):
    """Create a new breaker slot."""

    model = BreakerSlot
    form_class = BreakerSlotForm
    template_name = "technology/breaker_slot_form.html"
    success_url = reverse_lazy("technology:breaker_slot_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Breaker Slot"
        context["submit_text"] = "Create Breaker Slot"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Breaker Slot {form.instance.mat_no} created successfully.")
        return super().form_valid(form)


class BreakerSlotUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing breaker slot."""

    model = BreakerSlot
    form_class = BreakerSlotForm
    template_name = "technology/breaker_slot_form.html"

    def get_success_url(self):
        return reverse_lazy("technology:breaker_slot_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Breaker Slot {self.object.mat_no}"
        context["submit_text"] = "Update Breaker Slot"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Breaker Slot {self.object.mat_no} updated successfully.")
        return super().form_valid(form)


class BreakerSlotDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a breaker slot."""

    model = BreakerSlot
    template_name = "technology/breaker_slot_confirm_delete.html"
    success_url = reverse_lazy("technology:breaker_slot_list")

    def form_valid(self, form):
        messages.success(self.request, f"Breaker Slot {self.object.mat_no} deleted.")
        return super().form_valid(form)
