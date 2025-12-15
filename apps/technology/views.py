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
        from apps.workorders.models import BitSize

        queryset = Design.objects.select_related(
            "size", "connection_ref", "connection_ref__connection_type",
            "connection_ref__connection_size", "breaker_slot", "iadc_code_ref"
        ).order_by("-updated_at")

        # General search (MAT No., Ref MAT No., HDBS Type, SMI Type)
        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(mat_no__icontains=search) |
                Q(ref_mat_no__icontains=search) |
                Q(hdbs_type__icontains=search) |
                Q(smi_type__icontains=search)
            )

        # Type search (HDBS Type or SMI Type)
        type_search = self.request.GET.get("type")
        if type_search:
            queryset = queryset.filter(
                Q(hdbs_type__icontains=type_search) |
                Q(smi_type__icontains=type_search)
            )

        # Size filter
        size_id = self.request.GET.get("size")
        if size_id:
            queryset = queryset.filter(size_id=size_id)

        # Status filter
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Category filter
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category=category)

        # Order Level filter
        order_level = self.request.GET.get("order_level")
        if order_level:
            queryset = queryset.filter(order_level=order_level)

        # Sorting
        sort = self.request.GET.get("sort", "-updated_at")
        if sort:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        from apps.workorders.models import BitSize

        context = super().get_context_data(**kwargs)
        context["page_title"] = "Designs"
        context["search_query"] = self.request.GET.get("q", "")
        context["type_search"] = self.request.GET.get("type", "")
        context["current_size"] = self.request.GET.get("size", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["current_category"] = self.request.GET.get("category", "")
        context["current_order_level"] = self.request.GET.get("order_level", "")
        context["current_sort"] = self.request.GET.get("sort", "-updated_at")
        context["category_choices"] = Design.Category.choices
        context["status_choices"] = Design.Status.choices
        context["order_level_choices"] = Design.OrderLevel.choices
        context["sizes"] = BitSize.objects.filter(is_active=True).order_by("size_decimal")
        return context


class DesignDetailView(LoginRequiredMixin, DetailView):
    """View design details with BOM and cutter layouts."""

    model = Design
    template_name = "technology/design_detail.html"
    context_object_name = "design"

    def get_queryset(self):
        return Design.objects.select_related(
            "size", "connection_ref", "connection_ref__connection_type",
            "connection_ref__connection_size", "breaker_slot", "iadc_code_ref",
            "formation_type_ref", "application_ref", "created_by"
        ).prefetch_related("special_technologies")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Design {self.object.hdbs_type}"
        context["boms"] = self.object.boms.select_related("created_by").order_by("-created_at")
        context["cutter_layouts"] = self.object.cutter_layouts.order_by("blade_number", "position_number")
        context["work_orders_count"] = self.object.work_orders.count()

        # Pocket statistics
        pocket_configs = self.object.pocket_configs.all()
        pocket_configs_count = pocket_configs.count()
        pocket_configs_total = sum(c.count for c in pocket_configs)
        pocket_assignments_count = self.object.pockets.count()

        context["pocket_configs_count"] = pocket_configs_count
        context["pocket_configs_total"] = pocket_configs_total
        context["pocket_assignments_count"] = pocket_assignments_count
        context["pocket_layout_complete"] = (
            pocket_configs_count > 0 and
            pocket_assignments_count == pocket_configs_total
        )
        return context


class DesignCreateView(LoginRequiredMixin, CreateView):
    """Create a new design."""

    model = Design
    form_class = DesignForm
    template_name = "technology/design_form.html"
    success_url = reverse_lazy("technology:design_list")

    def get_next_layout_number(self):
        """Generate the next pocket layout number."""
        from django.db.models import Max
        from django.db.models.functions import Cast
        from django.db.models import IntegerField

        # Try to get max numeric layout number
        max_num = Design.objects.filter(
            pocket_layout_number__regex=r'^\d+$'
        ).annotate(
            num=Cast('pocket_layout_number', IntegerField())
        ).aggregate(Max('num'))['num__max']

        return str((max_num or 0) + 1)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Design"
        context["submit_text"] = "Create Design"
        context["next_layout_number"] = self.get_next_layout_number()
        return context

    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill with next layout number
        initial['pocket_layout_number'] = self.get_next_layout_number()
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # Auto-generate layout number if not provided
        if not form.instance.pocket_layout_number:
            form.instance.pocket_layout_number = self.get_next_layout_number()
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


class DesignPocketsView(LoginRequiredMixin, DetailView):
    """Pockets Layout and Features configuration view."""

    model = Design
    template_name = "technology/design_pockets.html"
    context_object_name = "design"

    def get_queryset(self):
        return Design.objects.select_related('size').prefetch_related(
            'pocket_configs__pocket_size',
            'pocket_configs__pocket_shape',
            'pockets__pocket_config'
        )

    def get_context_data(self, **kwargs):
        from .models import PocketSize, PocketShape, DesignPocketConfig

        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Pockets Layout - {self.object.hdbs_type}"

        # Reference data for dropdowns
        context["pocket_sizes"] = PocketSize.objects.filter(is_active=True)
        context["pocket_shapes"] = PocketShape.objects.filter(is_active=True)
        context["length_choices"] = DesignPocketConfig.LengthType.choices

        # Existing configurations for this design
        context["pocket_configs"] = self.object.pocket_configs.select_related(
            'pocket_size', 'pocket_shape'
        ).order_by('order')

        # Existing pockets for this design
        context["pockets"] = self.object.pockets.select_related(
            'pocket_config__pocket_size'
        ).order_by('blade_number', 'row_number', 'position_in_row')

        # Calculate totals for validation
        config_total = sum(c.count for c in context["pocket_configs"])
        entered_total = context["pockets"].count()
        context["config_total"] = config_total
        context["entered_total"] = entered_total

        # Group pockets by blade and row for grid display
        pockets_grid = {}
        for pocket in context["pockets"]:
            blade = pocket.blade_number
            row = pocket.row_number
            if blade not in pockets_grid:
                pockets_grid[blade] = {}
            if row not in pockets_grid[blade]:
                pockets_grid[blade][row] = []
            pockets_grid[blade][row].append(pocket)
        context["pockets_grid"] = pockets_grid

        # Generate color palette for pocket configs
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
                  '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1']
        for i, config in enumerate(context["pocket_configs"]):
            if not config.color_code:
                config.display_color = colors[i % len(colors)]
            else:
                config.display_color = config.color_code

        return context


class PocketConfigCreateView(LoginRequiredMixin, View):
    """Add a pocket configuration to a design."""

    def post(self, request, pk):
        from .models import Design, DesignPocketConfig, PocketSize, PocketShape

        design = get_object_or_404(Design, pk=pk)

        pocket_size_id = request.POST.get('pocket_size')
        length_type = request.POST.get('length_type')
        pocket_shape_id = request.POST.get('pocket_shape')
        count = request.POST.get('count')

        if pocket_size_id and length_type and pocket_shape_id and count:
            # Get the next order number
            last_config = design.pocket_configs.order_by('-order').first()
            next_order = (last_config.order + 1) if last_config else 1

            DesignPocketConfig.objects.create(
                design=design,
                order=next_order,
                pocket_size_id=pocket_size_id,
                length_type=length_type,
                pocket_shape_id=pocket_shape_id,
                count=int(count)
            )
            messages.success(request, "Pocket configuration added successfully.")
        else:
            messages.error(request, "Please fill in all required fields.")

        return redirect('technology:design_pockets', pk=pk)


class PocketConfigDeleteView(LoginRequiredMixin, View):
    """Delete a pocket configuration from a design."""

    def post(self, request, pk, config_pk):
        from .models import DesignPocketConfig

        config = get_object_or_404(DesignPocketConfig, pk=config_pk, design_id=pk)
        config.delete()
        messages.success(request, "Pocket configuration deleted.")
        return redirect('technology:design_pockets', pk=pk)


class DesignPocketsUpdateInfoView(LoginRequiredMixin, View):
    """Update pocket-related fields (rows count, pocket layout number) from pockets page."""

    def post(self, request, pk):
        design = get_object_or_404(Design, pk=pk)

        # Update pocket_rows_count
        rows_count = request.POST.get('pocket_rows_count')
        if rows_count:
            try:
                design.pocket_rows_count = int(rows_count)
            except ValueError:
                pass

        # Update pocket_layout_number
        layout_number = request.POST.get('pocket_layout_number')
        if layout_number is not None:
            design.pocket_layout_number = layout_number if layout_number else None

        design.save(update_fields=['pocket_rows_count', 'pocket_layout_number'])

        # Always return JSON - this is an API endpoint
        return JsonResponse({
            'success': True,
            'pocket_rows_count': design.pocket_rows_count,
            'pocket_layout_number': design.pocket_layout_number or ''
        })


class PocketConfigReorderView(LoginRequiredMixin, View):
    """Reorder pocket configurations (move up/down)."""

    def post(self, request, pk):
        from .models import DesignPocketConfig

        config_id = request.POST.get('config_id')
        direction = request.POST.get('direction')  # 'up' or 'down'

        if not config_id or direction not in ('up', 'down'):
            messages.error(request, "Invalid request.")
            return redirect('technology:design_pockets', pk=pk)

        config = get_object_or_404(DesignPocketConfig, pk=config_id, design_id=pk)
        configs = list(DesignPocketConfig.objects.filter(design_id=pk).order_by('order'))

        current_index = None
        for i, c in enumerate(configs):
            if c.pk == config.pk:
                current_index = i
                break

        if current_index is None:
            return redirect('technology:design_pockets', pk=pk)

        if direction == 'up' and current_index > 0:
            # Swap with previous
            configs[current_index], configs[current_index - 1] = configs[current_index - 1], configs[current_index]
        elif direction == 'down' and current_index < len(configs) - 1:
            # Swap with next
            configs[current_index], configs[current_index + 1] = configs[current_index + 1], configs[current_index]

        # Update order values
        for i, c in enumerate(configs, start=1):
            c.order = i
            c.save(update_fields=['order'])

        return redirect('technology:design_pockets', pk=pk)


class PocketConfigUpdateRowView(LoginRequiredMixin, View):
    """Update the row number of a pocket configuration."""

    def post(self, request, pk):
        from .models import DesignPocketConfig

        config_id = request.POST.get('config_id')
        row_number = request.POST.get('row_number')

        if not config_id or not row_number:
            messages.error(request, "Invalid request.")
            return redirect('technology:design_pockets', pk=pk)

        config = get_object_or_404(DesignPocketConfig, pk=config_id, design_id=pk)

        try:
            config.row_number = int(row_number)
            config.save(update_fields=['row_number'])
        except ValueError:
            messages.error(request, "Invalid row number.")

        return redirect('technology:design_pockets', pk=pk)


class DesignPocketsGridSaveView(LoginRequiredMixin, View):
    """Save grid cell assignments to database."""

    def post(self, request, pk):
        import json
        from .models import DesignPocket, DesignPocketConfig

        design = get_object_or_404(Design, pk=pk)

        try:
            data = json.loads(request.body)
            grid_data = data.get('gridData', {})
            row_separators = data.get('rowSeparators', [])

            # Delete existing pocket assignments
            DesignPocket.objects.filter(design=design).delete()

            # Save new assignments
            for key, config_id in grid_data.items():
                blade, col = key.split('_')
                blade = int(blade)
                col = int(col)

                # Calculate row and position in row based on separators
                row = 1
                row_start = 1
                for sep in sorted(row_separators):
                    if col > sep:
                        row += 1
                        row_start = sep + 1

                position_in_row = col - row_start + 1

                config = DesignPocketConfig.objects.filter(pk=config_id, design=design).first()
                if config:
                    DesignPocket.objects.create(
                        design=design,
                        blade_number=blade,
                        row_number=row,
                        position_in_row=position_in_row,
                        position_in_blade=col,
                        pocket_config=config
                    )

            return JsonResponse({'success': True, 'message': 'Grid saved'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    def get(self, request, pk):
        """Load grid data from database."""
        from .models import DesignPocket

        design = get_object_or_404(Design, pk=pk)
        pockets = DesignPocket.objects.filter(design=design).select_related('pocket_config')

        grid_data = {}
        for pocket in pockets:
            key = f"{pocket.blade_number}_{pocket.position_in_blade}"
            grid_data[key] = pocket.pocket_config_id

        # Calculate row separators from pocket data
        row_separators = []
        if pockets.exists():
            # Find where rows change
            positions_by_row = {}
            for pocket in pockets:
                if pocket.row_number not in positions_by_row:
                    positions_by_row[pocket.row_number] = []
                positions_by_row[pocket.row_number].append(pocket.position_in_blade)

            # Find max position of each row as separator
            for row_num in sorted(positions_by_row.keys())[:-1]:  # All but last row
                max_pos = max(positions_by_row[row_num])
                row_separators.append(max_pos)

        # Also include location data
        location_data = {}
        for pocket in pockets:
            key = f"{pocket.blade_number}_{pocket.position_in_blade}"
            if pocket.blade_location:
                location_data[key] = pocket.blade_location

        return JsonResponse({
            'success': True,
            'gridData': grid_data,
            'rowSeparators': sorted(row_separators),
            'locationData': location_data
        })


class DesignPocketsLocationSaveView(LoginRequiredMixin, View):
    """Save pocket location assignments to database."""

    def post(self, request, pk):
        import json
        from .models import DesignPocket

        design = get_object_or_404(Design, pk=pk)

        try:
            data = json.loads(request.body)
            location_data = data.get('locationData', {})

            # Validate sequential order within each blade AND row
            # Location order: C < N < T < S < G
            # Each row can have its own independent sequence
            location_order = {'C': 1, 'N': 2, 'T': 3, 'S': 4, 'G': 5}

            # Get existing pockets to know which row each column belongs to
            pockets = DesignPocket.objects.filter(design=design)
            col_to_row = {}
            for pocket in pockets:
                col_to_row[f"{pocket.blade_number}_{pocket.position_in_blade}"] = pocket.row_number

            # Group by blade and row
            for blade_num in range(1, design.no_of_blades + 1):
                # Group locations by row
                rows_locations = {}
                for key, loc in location_data.items():
                    b, col = key.split('_')
                    if int(b) == blade_num and loc:
                        row_num = col_to_row.get(key, 1)
                        if row_num not in rows_locations:
                            rows_locations[row_num] = []
                        rows_locations[row_num].append((int(col), loc))

                # Validate each row independently
                for row_num, row_locations in rows_locations.items():
                    # Sort by column position
                    row_locations.sort(key=lambda x: x[0])

                    # Check sequence within this row
                    last_order = 0
                    for col, loc in row_locations:
                        current_order = location_order.get(loc, 0)
                        if current_order < last_order:
                            return JsonResponse({
                                'success': False,
                                'message': f'Invalid sequence on Blade {blade_num}, Row {row_num}: {loc} cannot come after previous location'
                            }, status=400)
                        last_order = current_order

            # Update pocket locations
            for key, location in location_data.items():
                blade, col = key.split('_')
                blade = int(blade)
                col = int(col)

                DesignPocket.objects.filter(
                    design=design,
                    blade_number=blade,
                    position_in_blade=col
                ).update(blade_location=location if location else None)

            return JsonResponse({'success': True, 'message': 'Locations saved'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    def get(self, request, pk):
        """Load location data from database."""
        from .models import DesignPocket

        design = get_object_or_404(Design, pk=pk)
        pockets = DesignPocket.objects.filter(design=design)

        location_data = {}
        for pocket in pockets:
            key = f"{pocket.blade_number}_{pocket.position_in_blade}"
            if pocket.blade_location:
                location_data[key] = pocket.blade_location

        return JsonResponse({
            'success': True,
            'locationData': location_data
        })


class PocketsLayoutListView(LoginRequiredMixin, ListView):
    """List all designs with pockets layout summary."""

    model = Design
    template_name = "technology/pockets_layout_list.html"
    context_object_name = "designs"
    paginate_by = 25

    def get_queryset(self):
        from django.db.models import Count

        queryset = Design.objects.select_related(
            "size", "created_by"
        ).annotate(
            config_count=Count('pocket_configs')
        ).order_by("-updated_at")

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(mat_no__icontains=search) |
                Q(hdbs_type__icontains=search) |
                Q(smi_type__icontains=search)
            )

        size_id = self.request.GET.get("size")
        if size_id:
            queryset = queryset.filter(size_id=size_id)

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        from apps.workorders.models import BitSize

        context = super().get_context_data(**kwargs)
        context["page_title"] = "Pockets Layout"
        context["search_query"] = self.request.GET.get("q", "")
        context["current_size"] = self.request.GET.get("size", "")
        context["current_status"] = self.request.GET.get("status", "")
        context["status_choices"] = Design.Status.choices
        context["sizes"] = BitSize.objects.filter(is_active=True).order_by("size_decimal")
        return context


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
        conn_id = request.GET.get('id', '')
        q = request.GET.get('q', '')
        type_id = request.GET.get('type', '')
        size_id = request.GET.get('size', '')
        can_replace = request.GET.get('can_replace', '')

        # Base queryset
        queryset = Connection.objects.filter(is_active=True).select_related(
            'connection_type', 'connection_size', 'upper_section_type'
        )

        # Apply filters
        if conn_id:
            # Filter by specific ID (for edit mode initialization)
            queryset = queryset.filter(id=conn_id)
        else:
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
        slot_id = request.GET.get('id', '')
        q = request.GET.get('q', '')
        material = request.GET.get('material', '')
        min_width = request.GET.get('min_width', '')
        max_width = request.GET.get('max_width', '')

        # Base queryset
        queryset = BreakerSlot.objects.filter(is_active=True)

        # Apply filters
        if slot_id:
            # Filter by specific ID (for edit mode initialization)
            queryset = queryset.filter(id=slot_id)
        else:
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
                'compatible_sizes': list(slot.compatible_sizes.values_list('size_display', flat=True)),
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
