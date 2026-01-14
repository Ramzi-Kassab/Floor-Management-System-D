"""
ARDT FMS - Technology Views
Version: 5.4 - Sprint 3

Views for Design, BOM, and Cutter Layout management.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView, View

from django.http import JsonResponse

from .forms import BOMForm, BOMLineForm, BitSizeForm, BreakerSlotForm, ConnectionForm, DesignCutterLayoutForm, DesignForm, HDBSTypeForm, SMITypeForm
from .models import BOM, BOMLine, BitSize, BitType, BreakerSlot, Connection, ConnectionSize, ConnectionType, Design, DesignCutterLayout, HDBSType, SMIType


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
        # Count drafts for the banner (only show if not already filtering by status)
        if not self.request.GET.get("status"):
            context["draft_count"] = Design.objects.filter(status=Design.Status.DRAFT).count()
        else:
            context["draft_count"] = 0
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
        pockets = self.object.pockets.all()
        pocket_assignments_count = pockets.count()

        context["pocket_configs_count"] = pocket_configs_count
        context["pocket_configs_total"] = pocket_configs_total
        context["pocket_assignments_count"] = pocket_assignments_count

        # 3-Tab completion status
        # Tab 1: Grid - complete when all pockets are assigned
        grid_complete = pocket_configs_count > 0 and pocket_assignments_count == pocket_configs_total

        # Tab 2: Locations - complete when all pockets have blade_location
        locations_with_value = sum(1 for p in pockets if p.blade_location)
        locations_complete = pocket_assignments_count > 0 and locations_with_value == pocket_assignments_count

        # Tab 3: Engagements - complete when all pockets have engagement_order
        engagements_with_value = sum(1 for p in pockets if p.engagement_order)
        engagements_complete = pocket_assignments_count > 0 and engagements_with_value == pocket_assignments_count

        context["grid_complete"] = grid_complete
        context["locations_complete"] = locations_complete
        context["engagements_complete"] = engagements_complete

        # Overall pocket layout complete only when all 3 tabs are done
        context["pocket_layout_complete"] = grid_complete and locations_complete and engagements_complete
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
        # Pass 'from' parameter to template for back link customization
        context["from_page"] = self.request.GET.get("from", "")
        return context

    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill with next layout number
        initial['pocket_layout_number'] = self.get_next_layout_number()
        return initial

    def get_success_url(self):
        """Return to the page that initiated the design creation."""
        from_page = self.request.POST.get("from_page") or self.request.GET.get("from", "")

        if from_page == "bom_create":
            # Return to BOM create with the new design pre-selected
            return reverse_lazy("technology:bom_create") + f"?new_design={self.object.pk}"
        elif from_page == "cutter_map":
            # Return to cutter map with the new design
            return f"/cutter-map/?design_id={self.object.pk}&design_mat={self.object.mat_no}&design_hdbs={self.object.hdbs_type}&design_size={self.object.size}&from=design_create"

        # Default: go to design detail
        return reverse_lazy("technology:design_detail", kwargs={"pk": self.object.pk})

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


class DesignDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a design."""

    model = Design
    template_name = "technology/design_confirm_delete.html"
    success_url = reverse_lazy("technology:design_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete Design {self.object.hdbs_type}"
        # Check for related objects that would be deleted
        context["bom_count"] = self.object.boms.count()
        context["pocket_config_count"] = self.object.pocket_configs.count()
        context["pocket_count"] = self.object.pockets.count()
        return context

    def form_valid(self, form):
        design = self.object
        design_name = design.hdbs_type

        # Delete in correct order due to protected foreign keys:
        # 1. DesignPocket references DesignPocketConfig via PROTECT
        # 2. DesignPocketConfig references Design via CASCADE
        # So we must delete pockets first, then pocket_configs, then the design

        # Delete pockets first (they have protected FK to pocket_configs)
        design.pockets.all().delete()

        # Delete pocket configs
        design.pocket_configs.all().delete()

        # Now delete the design (this will cascade delete BOMs, etc.)
        messages.success(self.request, f"Design {design_name} deleted successfully.")
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

        # Check for unmatched cutters in related BOMs
        from .models import BOM, BOMLine
        unmatched_cutters = []
        boms = BOM.objects.filter(parent_design=self.object)
        for bom in boms:
            unmatched_lines = BOMLine.objects.filter(bom=bom, inventory_item__isnull=True)
            for line in unmatched_lines:
                unmatched_cutters.append({
                    'hdbs_code': line.hdbs_code,
                    'size': line.cutter_size,
                    'type': line.cutter_type,
                    'bom_code': bom.code
                })
        context["unmatched_cutters"] = unmatched_cutters
        context["has_unmatched_cutters"] = len(unmatched_cutters) > 0

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

        # Also include engagement data
        engagement_data = {}
        for pocket in pockets:
            key = f"{pocket.blade_number}_{pocket.position_in_blade}"
            if pocket.engagement_order:
                engagement_data[key] = pocket.engagement_order

        return JsonResponse({
            'success': True,
            'gridData': grid_data,
            'rowSeparators': sorted(row_separators),
            'locationData': location_data,
            'engagementData': engagement_data
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


class DesignPocketsEngagementSaveView(LoginRequiredMixin, View):
    """Save engagement order assignments to database."""

    def post(self, request, pk):
        import json
        from .models import DesignPocket

        design = get_object_or_404(Design, pk=pk)

        try:
            data = json.loads(request.body)
            engagement_data = data.get('engagementData', {})

            # Validate uniqueness
            values = [v for v in engagement_data.values() if v]
            if len(values) != len(set(values)):
                return JsonResponse({
                    'success': False,
                    'message': 'Duplicate engagement numbers found'
                }, status=400)

            # Update engagement orders
            for key, order in engagement_data.items():
                blade, col = key.split('_')
                blade = int(blade)
                col = int(col)

                DesignPocket.objects.filter(
                    design=design,
                    blade_number=blade,
                    position_in_blade=col
                ).update(engagement_order=order if order else None)

            return JsonResponse({'success': True, 'message': 'Engagements saved'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    def get(self, request, pk):
        """Load engagement data from database."""
        from .models import DesignPocket

        design = get_object_or_404(Design, pk=pk)
        pockets = DesignPocket.objects.filter(design=design)

        engagement_data = {}
        for pocket in pockets:
            key = f"{pocket.blade_number}_{pocket.position_in_blade}"
            if pocket.engagement_order:
                engagement_data[key] = pocket.engagement_order

        return JsonResponse({
            'success': True,
            'engagementData': engagement_data
        })


class DesignPocketsResetView(LoginRequiredMixin, View):
    """Reset all pocket data for a design (pockets and pocket configs)."""

    def post(self, request, pk):
        from .models import DesignPocket, DesignPocketConfig

        design = get_object_or_404(Design, pk=pk)

        try:
            # Delete in correct order (pockets reference pocket_configs via protected FK)
            pockets_deleted = DesignPocket.objects.filter(design=design).count()
            DesignPocket.objects.filter(design=design).delete()

            configs_deleted = DesignPocketConfig.objects.filter(design=design).count()
            DesignPocketConfig.objects.filter(design=design).delete()

            return JsonResponse({
                'success': True,
                'message': f'Reset complete. Deleted {pockets_deleted} pockets and {configs_deleted} configurations.',
                'pockets_deleted': pockets_deleted,
                'configs_deleted': configs_deleted
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)


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
    """List all BOMs with material availability status."""

    model = BOM
    template_name = "technology/bom_list.html"
    context_object_name = "boms"
    paginate_by = 50  # Higher limit since DataTables handles pagination

    def get_queryset(self):
        from .filters import BOMFilter
        queryset = BOM.objects.select_related(
            "design", "design__size", "design__iadc_code_ref", "created_by",
            "smi_type", "smi_type__hdbs_type"
        ).prefetch_related(
            "lines__inventory_item"
        ).order_by("-created_at")

        # Apply django-filter
        self.filterset = BOMFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        from apps.inventory.models import InventoryStock
        from django.db.models import Sum

        context = super().get_context_data(**kwargs)
        context["page_title"] = "Bills of Materials"
        context["filter"] = self.filterset
        context["sizes"] = BitSize.objects.filter(is_active=True).order_by("size_decimal")

        # Add material availability status for each BOM
        boms_with_status = []
        for bom in context["boms"]:
            all_available = True
            line_count = 0
            for line in bom.lines.all():
                line_count += 1
                if line.inventory_item:
                    stock = InventoryStock.objects.filter(item=line.inventory_item).aggregate(
                        available=Sum('quantity_available')
                    )
                    available = stock['available'] or 0
                    if available < line.quantity:
                        all_available = False
                else:
                    # No inventory item linked - can't check availability
                    all_available = False

            boms_with_status.append({
                'bom': bom,
                'materials_ready': all_available if line_count > 0 else None,
                'line_count': line_count,
            })

        context["boms_with_status"] = boms_with_status
        return context


class BOMDetailView(LoginRequiredMixin, DetailView):
    """View BOM details with line items and inventory availability."""

    model = BOM
    template_name = "technology/bom_detail.html"
    context_object_name = "bom"

    def get_queryset(self):
        return BOM.objects.select_related("design", "created_by")

    def get_context_data(self, **kwargs):
        from apps.inventory.models import InventoryStock
        from django.db.models import Sum

        context = super().get_context_data(**kwargs)
        context["page_title"] = f"BOM {self.object.code}"

        # Get lines with inventory items
        lines = self.object.lines.select_related(
            "inventory_item", "inventory_item__category", "inventory_item__primary_supplier"
        ).order_by("line_number")

        # Enrich lines with stock information
        lines_with_stock = []
        all_available = True

        for line in lines:
            item = line.inventory_item
            required = line.quantity

            # Get total stock for this item (only if inventory_item exists)
            if item:
                stock_data = InventoryStock.objects.filter(
                    item=item
                ).aggregate(
                    total_on_hand=Sum('quantity_on_hand'),
                    total_available=Sum('quantity_available')
                )
                on_hand = stock_data['total_on_hand'] or 0
                available = stock_data['total_available'] or 0
            else:
                # No linked inventory item - show as unavailable
                on_hand = 0
                available = 0

            # Determine availability status
            if available >= required:
                status = 'available'
            elif available > 0:
                status = 'partial'
                all_available = False
            else:
                status = 'unavailable'
                all_available = False

            lines_with_stock.append({
                'line': line,
                'on_hand': on_hand,
                'available': available,
                'required': required,
                'shortage': max(0, required - available),
                'status': status,
            })

        context["lines"] = lines_with_stock
        context["all_materials_available"] = all_available
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


class BOMDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a BOM."""

    model = BOM
    success_url = reverse_lazy("technology:bom_list")

    def post(self, request, *args, **kwargs):
        bom = self.get_object()
        bom_code = bom.code
        bom.delete()
        messages.success(request, f"BOM {bom_code} deleted successfully.")
        return redirect(self.success_url)


class BOMCloneView(LoginRequiredMixin, View):
    """Clone an existing BOM with a new code."""

    def post(self, request, pk):
        import json
        source_bom = get_object_or_404(BOM, pk=pk)

        try:
            data = json.loads(request.body)
            new_code = data.get("new_code", "").strip()
        except json.JSONDecodeError:
            new_code = request.POST.get("new_code", "").strip()

        if not new_code:
            return JsonResponse({"success": False, "error": "New BOM code is required"}, status=400)

        if BOM.objects.filter(code=new_code).exists():
            return JsonResponse({"success": False, "error": f"BOM with code {new_code} already exists"}, status=400)

        # Clone the BOM
        new_bom = BOM.objects.create(
            design=source_bom.design,
            code=new_code,
            name=f"{source_bom.name} (Clone)" if source_bom.name else "",
            revision="A",
            status=BOM.Status.DRAFT,
            created_by=request.user,
        )

        # Clone all lines
        for line in source_bom.lines.all():
            BOMLine.objects.create(
                bom=new_bom,
                order_number=line.order_number,
                inventory_item=line.inventory_item,
                display_name=line.display_name,
                quantity=line.quantity,
                color=line.color,
                notes=line.notes,
            )

        return JsonResponse({
            "success": True,
            "redirect_url": reverse("technology:bom_builder", args=[new_bom.pk])
        })


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
# BOM BUILDER VIEWS (Manual BOM creation with drag-drop)
# =============================================================================


class BOMBuilderView(LoginRequiredMixin, DetailView):
    """
    Manual BOM builder with drag-drop reordering.
    Allows building BOM lines from PDC Cutters inventory items.
    """

    model = BOM
    template_name = "technology/bom_builder.html"
    context_object_name = "bom"

    def get_context_data(self, **kwargs):
        from apps.inventory.models import InventoryCategory, InventoryItem, InventoryStock
        from django.db.models import Sum

        context = super().get_context_data(**kwargs)
        context["page_title"] = f"BOM Builder - {self.object.code}"

        # Get BOM lines ordered by order_number
        lines = self.object.lines.select_related(
            "inventory_item"
        ).order_by("order_number", "line_number")

        # Enrich lines with inventory data and on-order quantities
        lines_with_data = []
        total_shortage = 0

        for line in lines:
            item = line.inventory_item
            stock_data = {"available": 0, "on_order": 0}
            replacements = []

            if item:
                # Get stock availability
                stock = InventoryStock.objects.filter(item=item).aggregate(
                    available=Sum('quantity_available')
                )
                stock_data["available"] = stock['available'] or 0

                # Get on-order quantity from PurchaseOrderLine
                try:
                    from apps.supplychain.models import PurchaseOrderLine
                    on_order = PurchaseOrderLine.objects.filter(
                        item=item,
                        purchase_order__status__in=['SUBMITTED', 'APPROVED', 'ORDERED']
                    ).aggregate(total=Sum('quantity'))
                    stock_data["on_order"] = on_order['total'] or 0
                except Exception:
                    stock_data["on_order"] = 0

            # Calculate shortage
            shortage = max(0, line.quantity - stock_data["available"])
            total_shortage += shortage

            # Find replacement suggestions if there's a shortage
            if shortage > 0 and line.cutter_size:
                replacements = self._find_replacements(
                    line.cutter_size,
                    line.cutter_chamfer,
                    shortage,
                    line.inventory_item
                )

            lines_with_data.append({
                'line': line,
                'available': stock_data["available"],
                'on_order': stock_data["on_order"],
                'shortage': shortage,
                'replacements': replacements,
            })

        context["total_shortage"] = total_shortage

        context["lines"] = lines_with_data

        # Get available cutter items from inventory
        # Try to find PDC Cutters category
        cutter_category = InventoryCategory.objects.filter(
            Q(code__icontains="CUT") | Q(name__icontains="Cutter")
        ).first()

        if cutter_category:
            cutter_items = InventoryItem.objects.filter(
                category=cutter_category,
                is_active=True
            ).select_related("category").prefetch_related("attribute_values", "attribute_values__attribute")[:100]
        else:
            # Fallback: get all active items if no cutter category found
            cutter_items = InventoryItem.objects.filter(
                is_active=True
            ).select_related("category").prefetch_related("attribute_values", "attribute_values__attribute")[:50]

        # Build cutter items with their attributes for display
        cutter_items_data = []
        for item in cutter_items:
            # Get HDBS Code attribute if exists
            hdbs_code = ""
            size = ""
            chamfer = ""
            cutter_type = ""

            for attr in item.attribute_values.all():
                attr_code = attr.attribute.code.lower() if attr.attribute else ""
                if "hdbs" in attr_code or "mat" in attr_code:
                    hdbs_code = attr.text_value
                elif "size" in attr_code:
                    size = attr.text_value
                elif "chamfer" in attr_code:
                    chamfer = attr.text_value
                elif "type" in attr_code:
                    cutter_type = attr.text_value

            cutter_items_data.append({
                'item': item,
                'hdbs_code': hdbs_code or item.code,
                'size': size,
                'chamfer': chamfer,
                'cutter_type': cutter_type,
            })

        context["cutter_items"] = cutter_items_data

        # Default color palette
        context["color_palette"] = BOMLine.DEFAULT_COLORS

        # Design info
        context["design"] = self.object.design

        return context

    def _find_replacements(self, cutter_size, cutter_chamfer, needed_qty, exclude_item=None):
        """
        Find replacement items with same size and potentially different chamfer.
        Size match is strict, chamfer can differ.
        """
        from apps.inventory.models import InventoryCategory, InventoryItem, InventoryStock
        from django.db.models import Sum

        replacements = []

        # Find cutter category
        cutter_category = InventoryCategory.objects.filter(
            Q(code__icontains="CUT") | Q(name__icontains="Cutter")
        ).first()

        if not cutter_category:
            return replacements

        # Get items in cutter category
        items = InventoryItem.objects.filter(
            category=cutter_category,
            is_active=True
        ).prefetch_related("attribute_values", "attribute_values__attribute")

        if exclude_item:
            items = items.exclude(pk=exclude_item.pk)

        for item in items[:50]:  # Limit search
            # Check attributes for size match
            item_size = ""
            item_chamfer = ""

            for attr in item.attribute_values.all():
                attr_code = attr.attribute.code.lower() if attr.attribute else ""
                if "size" in attr_code:
                    item_size = attr.text_value
                elif "chamfer" in attr_code:
                    item_chamfer = attr.text_value

            # Size must match strictly
            if item_size != cutter_size:
                continue

            # Get stock availability
            stock = InventoryStock.objects.filter(item=item).aggregate(
                available=Sum('quantity_available')
            )
            available = stock['available'] or 0

            if available > 0:
                replacements.append({
                    'item': item,
                    'size': item_size,
                    'chamfer': item_chamfer,
                    'available': available,
                    'chamfer_match': item_chamfer == cutter_chamfer,
                })

        # Sort by chamfer match first, then by availability
        replacements.sort(key=lambda x: (-x['chamfer_match'], -x['available']))

        return replacements[:5]  # Return top 5 matches


class BOMBuilderAddLineView(LoginRequiredMixin, View):
    """API: Add a line to BOM from builder."""

    def post(self, request, pk):
        import json
        from apps.inventory.models import InventoryItem

        bom = get_object_or_404(BOM, pk=pk)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

        item_id = data.get("item_id")
        quantity = int(data.get("quantity", 1))
        order_number = int(data.get("order_number", 1))
        color_code = data.get("color_code", "")
        hdbs_code = data.get("hdbs_code", "")
        cutter_size = data.get("cutter_size", "")
        cutter_chamfer = data.get("cutter_chamfer", "")
        cutter_type = data.get("cutter_type", "")

        # Get next line number
        max_line = bom.lines.aggregate(max_line=models.Max("line_number"))
        next_line = (max_line["max_line"] or 0) + 1

        # Get inventory item if provided
        inventory_item = None
        if item_id:
            try:
                inventory_item = InventoryItem.objects.get(pk=item_id)
            except InventoryItem.DoesNotExist:
                pass

        # Create line
        line = BOMLine.objects.create(
            bom=bom,
            line_number=next_line,
            inventory_item=inventory_item,
            quantity=quantity,
            order_number=order_number,
            color_code=color_code or BOMLine.DEFAULT_COLORS[(order_number - 1) % len(BOMLine.DEFAULT_COLORS)],
            hdbs_code=hdbs_code,
            cutter_size=cutter_size,
            cutter_chamfer=cutter_chamfer,
            cutter_type=cutter_type,
        )

        return JsonResponse({
            "success": True,
            "line_id": line.id,
            "line_number": line.line_number,
            "order_number": line.order_number,
            "color_code": line.color_code,
        })


class BOMBuilderUpdateLineView(LoginRequiredMixin, View):
    """API: Update a BOM line."""

    def post(self, request, pk, line_pk):
        import json

        line = get_object_or_404(BOMLine, pk=line_pk, bom_id=pk)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

        # Update fields if provided
        if "quantity" in data:
            line.quantity = int(data["quantity"])
        if "order_number" in data:
            line.order_number = int(data["order_number"])
        if "color_code" in data:
            line.color_code = data["color_code"]
        if "hdbs_code" in data:
            line.hdbs_code = data["hdbs_code"]
        if "cutter_size" in data:
            line.cutter_size = data["cutter_size"]
        if "cutter_chamfer" in data:
            line.cutter_chamfer = data["cutter_chamfer"]
        if "cutter_type" in data:
            line.cutter_type = data["cutter_type"]

        line.save()

        return JsonResponse({
            "success": True,
            "line_id": line.id,
        })


class BOMBuilderDeleteLineView(LoginRequiredMixin, View):
    """API: Delete a BOM line."""

    def post(self, request, pk, line_pk):
        line = get_object_or_404(BOMLine, pk=line_pk, bom_id=pk)
        line.delete()
        return JsonResponse({"success": True})


class BOMBuilderReorderView(LoginRequiredMixin, View):
    """API: Reorder BOM lines via drag-drop."""

    def post(self, request, pk):
        import json

        bom = get_object_or_404(BOM, pk=pk)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

        line_order = data.get("line_order", [])

        # Update order numbers
        for idx, line_id in enumerate(line_order, start=1):
            try:
                line = BOMLine.objects.get(pk=line_id, bom=bom)
                line.order_number = idx
                line.save(update_fields=["order_number"])
            except BOMLine.DoesNotExist:
                continue

        return JsonResponse({"success": True})


class BOMBuilderSearchItemsView(LoginRequiredMixin, View):
    """API: Search inventory items for BOM builder."""

    def get(self, request, pk):
        from apps.inventory.models import InventoryCategory, InventoryItem

        query = request.GET.get("q", "")
        category_code = request.GET.get("category", "")

        items = InventoryItem.objects.filter(is_active=True)

        # Filter by category
        if category_code:
            items = items.filter(category__code=category_code)
        else:
            # Default to cutter-related categories
            cutter_category = InventoryCategory.objects.filter(
                Q(code__icontains="CUT") | Q(name__icontains="Cutter")
            ).first()
            if cutter_category:
                items = items.filter(category=cutter_category)

        # Search
        if query:
            items = items.filter(
                Q(code__icontains=query) |
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )

        items = items.select_related("category").prefetch_related("attributes")[:50]

        results = []
        for item in items:
            # Extract attributes
            hdbs_code = item.code
            size = ""
            chamfer = ""
            cutter_type = ""

            for attr in item.attribute_values.all():
                attr_code = attr.attribute.code.lower() if attr.attribute else ""
                if "hdbs" in attr_code or "mat" in attr_code:
                    hdbs_code = attr.text_value
                elif "size" in attr_code:
                    size = attr.text_value
                elif "chamfer" in attr_code:
                    chamfer = attr.text_value
                elif "type" in attr_code:
                    cutter_type = attr.text_value

            results.append({
                "id": item.id,
                "code": item.code,
                "name": item.name,
                "hdbs_code": hdbs_code,
                "size": size,
                "chamfer": chamfer,
                "cutter_type": cutter_type,
                "category": item.category.name if item.category else "",
            })

        return JsonResponse({"items": results})


# =============================================================================
# BOM PDF IMPORT VIEWS
# =============================================================================


class BOMPDFImportView(LoginRequiredMixin, View):
    """Upload and parse a BOM PDF for import."""

    def get(self, request, pk):
        bom = get_object_or_404(BOM, pk=pk)
        return self._render(request, bom)

    def post(self, request, pk):
        bom = get_object_or_404(BOM, pk=pk)

        if 'pdf_file' not in request.FILES:
            messages.error(request, "Please select a PDF file to upload.")
            return self._render(request, bom)

        pdf_file = request.FILES['pdf_file']

        # Validate file type
        if not pdf_file.name.lower().endswith('.pdf'):
            messages.error(request, "Please upload a PDF file.")
            return self._render(request, bom)

        # Parse PDF
        from apps.technology.services.pdf_parser import parse_bom_pdf

        try:
            pdf_bytes = pdf_file.read()
            parsed_data = parse_bom_pdf(file_bytes=pdf_bytes)

            if parsed_data.errors:
                for err in parsed_data.errors:
                    messages.warning(request, err)

            # Store parsed data in session for confirmation
            request.session['parsed_bom_data'] = {
                'header': {
                    'sn_number': parsed_data.header.sn_number,
                    'mat_number': parsed_data.header.mat_number,
                    'date_created': parsed_data.header.date_created.isoformat() if parsed_data.header.date_created else None,
                    'revision_level': parsed_data.header.revision_level,
                    'software_version': parsed_data.header.software_version,
                },
                'bom_lines': [
                    {
                        'order_number': line.order_number,
                        'size': line.size,
                        'chamfer': line.chamfer,
                        'cutter_type': line.cutter_type,
                        'count': line.count,
                        'mat_number': line.mat_number,
                        'family_number': line.family_number,
                        'color_code': line.color_code,
                    }
                    for line in parsed_data.bom_lines
                ],
                'cutter_positions': [
                    {
                        'blade_number': pos.blade_number,
                        'row_number': pos.row_number,
                        'location': pos.location,
                        'position_in_location': pos.position_in_location,
                        'cutter_type': pos.cutter_type,
                        'order_number': pos.order_number,
                        'chamfer': pos.chamfer,
                    }
                    for pos in parsed_data.cutter_positions
                ],
                'raw_text': parsed_data.raw_text[:5000] if parsed_data.raw_text else '',  # First 5000 chars for debugging
            }

            # Save the PDF file to BOM - reset file position first
            pdf_file.seek(0)
            bom.source_pdf_file = pdf_file
            bom.save(update_fields=['source_pdf_file'])

            return redirect('technology:bom_pdf_import_confirm', pk=pk)

        except Exception as e:
            messages.error(request, f"Error parsing PDF: {str(e)}")
            return self._render(request, bom)

    def _render(self, request, bom):
        from django.shortcuts import render
        return render(request, 'technology/bom_pdf_import.html', {
            'bom': bom,
            'page_title': f"Import PDF - {bom.code}",
        })


class BOMPDFImportConfirmView(LoginRequiredMixin, View):
    """Confirm and apply parsed PDF data to BOM."""

    def get(self, request, pk):
        import json

        bom = get_object_or_404(BOM, pk=pk)

        parsed_data = request.session.get('parsed_bom_data')

        # If no parsed data in session but BOM has a PDF, auto-parse it
        if not parsed_data and bom.source_pdf_file:
            from apps.technology.services.pdf_parser import parse_bom_pdf
            try:
                result = parse_bom_pdf(file_path=bom.source_pdf_file.path)
                parsed_data = {
                    'header': {
                        'sn_number': result.header.sn_number,
                        'mat_number': result.header.mat_number,
                        'date_created': result.header.date_created.isoformat() if result.header.date_created else None,
                        'revision_level': result.header.revision_level,
                        'software_version': result.header.software_version,
                    },
                    'bom_lines': [
                        {
                            'order_number': line.order_number,
                            'size': line.size,
                            'chamfer': line.chamfer,
                            'cutter_type': line.cutter_type,
                            'count': line.count,
                            'mat_number': line.mat_number,
                            'family_number': line.family_number,
                            'color_code': line.color_code,
                        }
                        for line in result.bom_lines
                    ],
                    'cutter_positions': [
                        {
                            'blade_number': pos.blade_number,
                            'row_number': pos.row_number,
                            'location': pos.location,
                            'position_in_location': pos.position_in_location,
                            'cutter_type': pos.cutter_type,
                            'order_number': pos.order_number,
                            'chamfer': pos.chamfer,
                        }
                        for pos in result.cutter_positions
                    ],
                    'raw_text': result.raw_text[:5000] if result.raw_text else '',
                }
                # Store in session for subsequent requests
                request.session['parsed_bom_data'] = parsed_data
                if result.errors:
                    for err in result.errors:
                        messages.warning(request, err)
            except Exception as e:
                messages.error(request, f"Error parsing PDF: {str(e)}")
                return redirect('technology:bom_pdf_import', pk=pk)

        if not parsed_data:
            messages.warning(request, "No parsed data found. Please upload a PDF first.")
            return redirect('technology:bom_pdf_import', pk=pk)

        # Serialize data for JavaScript
        bom_lines_json = json.dumps(parsed_data.get('bom_lines', []))
        cutter_positions_json = json.dumps(parsed_data.get('cutter_positions', []))

        from django.shortcuts import render
        return render(request, 'technology/bom_pdf_import_confirm.html', {
            'bom': bom,
            'parsed_data': parsed_data,
            'bom_lines_json': bom_lines_json,
            'cutter_positions_json': cutter_positions_json,
            'page_title': f"Confirm Import - {bom.code}",
        })

    def post(self, request, pk):
        import json
        from datetime import datetime as dt

        bom = get_object_or_404(BOM, pk=pk)

        parsed_data = request.session.get('parsed_bom_data')
        if not parsed_data:
            messages.error(request, "No parsed data found.")
            return redirect('technology:bom_pdf_import', pk=pk)

        try:
            header = parsed_data['header']

            # Check if we have modified data from the interactive form
            bom_lines_json = request.POST.get('bom_lines_json', '')
            cutter_positions_json = request.POST.get('cutter_positions_json', '')

            if bom_lines_json:
                try:
                    bom_lines_data = json.loads(bom_lines_json)
                except json.JSONDecodeError:
                    bom_lines_data = parsed_data['bom_lines']
            else:
                bom_lines_data = parsed_data['bom_lines']

            if cutter_positions_json:
                try:
                    cutter_positions_data = json.loads(cutter_positions_json)
                except json.JSONDecodeError:
                    cutter_positions_data = parsed_data.get('cutter_positions', [])
            else:
                cutter_positions_data = parsed_data.get('cutter_positions', [])

            # Update BOM with header info
            bom.source_type = BOM.SourceType.PDF_IMPORT
            bom.source_mat_number = header.get('mat_number', '')
            bom.source_sn_number = header.get('sn_number', '')
            bom.source_revision_level = header.get('revision_level', '')
            bom.source_software_version = header.get('software_version', '')

            if header.get('date_created'):
                try:
                    bom.source_date_created = dt.fromisoformat(header['date_created'])
                except (ValueError, TypeError):
                    pass

            bom.save()

            # Clear existing lines if requested
            if request.POST.get('clear_existing') == 'yes':
                bom.lines.all().delete()
                # Also clear cutter positions
                BOMCutterPosition.objects.filter(bom=bom).delete()

            # Get max line number
            max_line = bom.lines.aggregate(max_line=models.Max("line_number"))
            next_line_num = (max_line["max_line"] or 0) + 1

            # Create BOM lines and map order numbers to BOMLine objects
            lines_created = 0
            order_to_line = {}  # Map order_number to BOMLine for grid positions

            for line_data in bom_lines_data:
                bom_line = BOMLine.objects.create(
                    bom=bom,
                    line_number=next_line_num,
                    order_number=line_data['order_number'],
                    quantity=line_data.get('count', 0),
                    color_code=line_data.get('color_code', '#4A4A4A'),
                    cutter_size=line_data.get('size', ''),
                    cutter_chamfer=line_data.get('chamfer', ''),
                    cutter_type=line_data.get('cutter_type', ''),
                    hdbs_code=line_data.get('mat_number', ''),
                    family_number=line_data.get('family_number', ''),
                )
                order_to_line[line_data['order_number']] = bom_line
                next_line_num += 1
                lines_created += 1

            # Import cutter grid positions if requested
            positions_created = 0
            if request.POST.get('import_grid') == 'yes' and cutter_positions_data:
                for pos_data in cutter_positions_data:
                    order_num = pos_data.get('order_number', 1)
                    bom_line = order_to_line.get(order_num)

                    BOMCutterPosition.objects.create(
                        bom=bom,
                        bom_line=bom_line,
                        blade_number=pos_data.get('blade_number', 1),
                        row_number=pos_data.get('row_number', 1),
                        blade_location=pos_data.get('location', 'CONE'),
                        position_in_location=pos_data.get('position_in_location', 1),
                        cutter_type_display=pos_data.get('cutter_type', ''),
                        order_number_display=order_num,
                        chamfer_display=pos_data.get('chamfer', ''),
                    )
                    positions_created += 1

            # Clear session data
            del request.session['parsed_bom_data']

            if positions_created > 0:
                messages.success(request, f"Successfully imported {lines_created} lines and {positions_created} grid positions from PDF.")
            else:
                messages.success(request, f"Successfully imported {lines_created} lines from PDF.")

            return redirect('technology:bom_builder', pk=pk)

        except Exception as e:
            messages.error(request, f"Error applying import: {str(e)}")
            return redirect('technology:bom_pdf_import_confirm', pk=pk)


class BOMPDFServeView(LoginRequiredMixin, View):
    """Serve BOM PDF file without X-Frame-Options to allow embedding."""

    def get(self, request, pk):
        from django.http import FileResponse
        import os

        bom = get_object_or_404(BOM, pk=pk)

        if not bom.source_pdf_file:
            from django.http import HttpResponseNotFound
            return HttpResponseNotFound("No PDF file available")

        file_path = bom.source_pdf_file.path
        if not os.path.exists(file_path):
            from django.http import HttpResponseNotFound
            return HttpResponseNotFound("PDF file not found")

        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
        # Allow embedding in same origin
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response


class BOMPDFExportView(LoginRequiredMixin, View):
    """Export BOM to PDF."""

    def get(self, request, pk):
        from django.http import HttpResponse

        bom = get_object_or_404(BOM, pk=pk)

        try:
            from apps.technology.services.pdf_generator import generate_bom_pdf

            pdf_bytes = generate_bom_pdf(bom)

            # Create response
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            filename = f"BOM_{bom.code}_{bom.revision}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except Exception as e:
            messages.error(request, f"Error generating PDF: {str(e)}")
            return redirect('technology:bom_detail', pk=pk)


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

        # Bit sizes for compatible sizes checkboxes in quick create
        bit_sizes = [{'id': bs.id, 'display': bs.size_display} for bs in BitSize.objects.filter(is_active=True)]

        return JsonResponse({
            'breaker_slots': breaker_slots,
            'filters': {
                'materials': materials,
                'sizes': bit_sizes,
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


# =============================================================================
# QUICK CREATE API VIEWS (for modal quick-create without leaving the page)
# =============================================================================


class APIConnectionCreateView(LoginRequiredMixin, View):
    """API endpoint to create a new connection from the design form modal."""

    def post(self, request):
        import json

        try:
            data = json.loads(request.body)

            # Validate required fields
            mat_no = data.get('mat_no', '').strip()
            connection_type_id = data.get('connection_type')
            connection_size_id = data.get('connection_size')

            if not mat_no:
                return JsonResponse({'success': False, 'error': 'MAT No. is required'}, status=400)
            if not connection_type_id:
                return JsonResponse({'success': False, 'error': 'Connection Type is required'}, status=400)
            if not connection_size_id:
                return JsonResponse({'success': False, 'error': 'Connection Size is required'}, status=400)

            # Check if MAT No. already exists
            if Connection.objects.filter(mat_no=mat_no).exists():
                return JsonResponse({'success': False, 'error': f'Connection with MAT No. {mat_no} already exists'}, status=400)

            # Create the connection
            connection = Connection.objects.create(
                mat_no=mat_no,
                connection_type_id=connection_type_id,
                connection_size_id=connection_size_id,
                special_features=data.get('special_features', ''),
                can_replace_in_ksa=data.get('can_replace_in_ksa', False),
                remarks=data.get('remarks', ''),
                is_active=data.get('is_active', True)
            )

            return JsonResponse({
                'success': True,
                'connection': {
                    'id': connection.id,
                    'mat_no': connection.mat_no,
                    'type': connection.connection_type.code,
                    'type_name': connection.connection_type.name,
                    'size': connection.connection_size.size_inches,
                    'can_replace_in_ksa': connection.can_replace_in_ksa,
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class APIBreakerSlotCreateView(LoginRequiredMixin, View):
    """API endpoint to create a new breaker slot from the design form modal."""

    def post(self, request):
        import json

        try:
            data = json.loads(request.body)

            # Validate required fields
            mat_no = data.get('mat_no', '').strip()
            slot_width = data.get('slot_width')
            slot_depth = data.get('slot_depth')
            material = data.get('material')

            if not mat_no:
                return JsonResponse({'success': False, 'error': 'MAT No. is required'}, status=400)
            if not slot_width:
                return JsonResponse({'success': False, 'error': 'Slot Width is required'}, status=400)
            if not slot_depth:
                return JsonResponse({'success': False, 'error': 'Slot Depth is required'}, status=400)
            if not material:
                return JsonResponse({'success': False, 'error': 'Material is required'}, status=400)

            # Check if MAT No. already exists
            if BreakerSlot.objects.filter(mat_no=mat_no).exists():
                return JsonResponse({'success': False, 'error': f'Breaker Slot with MAT No. {mat_no} already exists'}, status=400)

            # Create the breaker slot
            breaker_slot = BreakerSlot.objects.create(
                mat_no=mat_no,
                slot_width=slot_width,
                slot_depth=slot_depth,
                slot_length=data.get('slot_length') or None,
                material=material,
                hardness=data.get('hardness', ''),
                remarks=data.get('remarks', ''),
                is_active=data.get('is_active', True)
            )

            # Add compatible sizes if provided
            compatible_sizes = data.get('compatible_sizes', [])
            if compatible_sizes:
                breaker_slot.compatible_sizes.set(compatible_sizes)

            return JsonResponse({
                'success': True,
                'breaker_slot': {
                    'id': breaker_slot.id,
                    'mat_no': breaker_slot.mat_no,
                    'slot_width': str(breaker_slot.slot_width),
                    'slot_depth': str(breaker_slot.slot_depth),
                    'material': breaker_slot.material,
                    'material_display': breaker_slot.get_material_display(),
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class APIDesignSaveDraftView(LoginRequiredMixin, View):
    """API endpoint to save a design as draft from the design form."""

    def post(self, request):
        import json

        try:
            data = json.loads(request.body)

            # Validate minimum required fields
            mat_no = data.get('mat_no', '').strip()
            hdbs_type = data.get('hdbs_type', '').strip()

            if not mat_no and not hdbs_type:
                return JsonResponse({
                    'success': False,
                    'error': 'At least MAT No. or HDBS Type is required to save a draft'
                }, status=400)

            # Check for existing draft with same MAT No
            design_id = data.get('design_id')  # For updating existing draft
            if design_id:
                # Update existing design
                try:
                    design = Design.objects.get(id=design_id)
                except Design.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Design not found'}, status=404)
            else:
                # Create new design
                design = Design()

            # Set all provided fields
            design.mat_no = mat_no or f"DRAFT-{Design.objects.count() + 1}"
            design.hdbs_type = hdbs_type or "DRAFT"
            design.status = Design.Status.DRAFT

            # Optional fields
            if data.get('category'):
                design.category = data['category']
            if data.get('size'):
                design.size_id = data['size']
            if data.get('smi_type'):
                design.smi_type = data['smi_type']
            if data.get('ref_mat_no'):
                design.ref_mat_no = data['ref_mat_no']
            if data.get('ardt_item_no'):
                design.ardt_item_no = data['ardt_item_no']
            if data.get('body_material'):
                design.body_material = data['body_material']
            if data.get('series'):
                design.series = data['series']
            if data.get('no_of_blades'):
                design.no_of_blades = data['no_of_blades']
            if data.get('cutter_size'):
                design.cutter_size = data['cutter_size']
            if data.get('total_pockets_count'):
                design.total_pockets_count = data['total_pockets_count']
            if data.get('gage_length'):
                design.gage_length = data['gage_length']
            if data.get('gage_relief'):
                design.gage_relief = data['gage_relief']
            if data.get('nozzle_count'):
                design.nozzle_count = data['nozzle_count']
            if data.get('nozzle_bore_size'):
                design.nozzle_bore_size = data['nozzle_bore_size']
            if data.get('nozzle_config'):
                design.nozzle_config = data['nozzle_config']
            if data.get('port_count'):
                design.port_count = data['port_count']
            if data.get('port_size'):
                design.port_size = data['port_size']
            if data.get('order_level'):
                design.order_level = data['order_level']
            if data.get('iadc_code_ref'):
                design.iadc_code_ref_id = data['iadc_code_ref']
            if data.get('connection_ref'):
                design.connection_ref_id = data['connection_ref']
            if data.get('breaker_slot'):
                design.breaker_slot_id = data['breaker_slot']
            if data.get('formation_type_ref'):
                design.formation_type_ref_id = data['formation_type_ref']
            if data.get('application_ref'):
                design.application_ref_id = data['application_ref']
            if data.get('revision'):
                design.revision = data['revision']
            if data.get('description'):
                design.description = data['description']
            if data.get('notes'):
                design.notes = data['notes']

            design.save()

            return JsonResponse({
                'success': True,
                'design': {
                    'id': design.id,
                    'mat_no': design.mat_no,
                    'hdbs_type': design.hdbs_type,
                    'status': design.status,
                },
                'message': 'Design saved as draft'
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============================================================================
# BIT SIZE CRUD VIEWS (Simple list of sizes)
# =============================================================================


class BitSizeListView(LoginRequiredMixin, ListView):
    """List all bit sizes - simple list."""

    model = BitSize
    template_name = "technology/bit_size_list.html"
    context_object_name = "sizes"
    paginate_by = 50

    def get_queryset(self):
        queryset = BitSize.objects.order_by('size_decimal')

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(size_display__icontains=search) |
                Q(size_inches__icontains=search) |
                Q(description__icontains=search)
            )

        if not self.request.GET.get("show_inactive"):
            queryset = queryset.filter(is_active=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Bit Sizes"
        return context


class BitSizeCreateView(LoginRequiredMixin, CreateView):
    """Create a new bit size."""

    model = BitSize
    form_class = BitSizeForm
    template_name = "technology/bit_size_form.html"
    success_url = reverse_lazy("technology:bit_size_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Add Bit Size"
        context["submit_text"] = "Add Size"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Bit Size {form.instance.size_display} added successfully.")
        return super().form_valid(form)


class BitSizeUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing bit size."""

    model = BitSize
    form_class = BitSizeForm
    template_name = "technology/bit_size_form.html"
    success_url = reverse_lazy("technology:bit_size_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit Size {self.object.size_display}"
        context["submit_text"] = "Save Changes"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Bit Size {self.object.size_display} updated successfully.")
        return super().form_valid(form)


class BitSizeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a bit size."""

    model = BitSize
    template_name = "technology/bit_size_confirm_delete.html"
    success_url = reverse_lazy("technology:bit_size_list")

    def form_valid(self, form):
        messages.success(self.request, f"Bit Size {self.object.size_display} deleted.")
        return super().form_valid(form)


# =============================================================================
# HDBS TYPE CRUD VIEWS (Internal type naming with SMI children)
# =============================================================================


class HDBSTypeListView(LoginRequiredMixin, ListView):
    """List all HDBS types with their SMI names."""

    model = HDBSType
    template_name = "technology/hdbs_type_list.html"
    context_object_name = "hdbs_types"
    paginate_by = 25

    def get_queryset(self):
        queryset = HDBSType.objects.prefetch_related('smi_types', 'smi_types__size', 'sizes').order_by('hdbs_name')

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(hdbs_name__icontains=search) |
                Q(description__icontains=search) |
                Q(smi_types__smi_name__icontains=search)
            ).distinct()

        size = self.request.GET.get("size")
        if size:
            queryset = queryset.filter(sizes__id=size)

        if not self.request.GET.get("show_inactive"):
            queryset = queryset.filter(is_active=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Bit Types (HDBS/SMI)"
        context["sizes"] = BitSize.objects.filter(is_active=True).order_by('size_decimal')

        # Build flat rows for the table: each row = {hdbs, size, smi}
        flat_rows = []
        for hdbs in context["hdbs_types"]:
            sizes = list(hdbs.sizes.filter(is_active=True).order_by('size_decimal'))
            smi_types = list(hdbs.smi_types.select_related('size').all())

            if sizes:
                for size in sizes:
                    # Find SMI types for this specific size OR no size (applies to all)
                    matching_smi = [s for s in smi_types if s.size_id == size.id or s.size_id is None]
                    if matching_smi:
                        for smi in matching_smi:
                            flat_rows.append({'hdbs': hdbs, 'size': size, 'smi': smi})
                    else:
                        # No SMI for this size
                        flat_rows.append({'hdbs': hdbs, 'size': size, 'smi': None})
            else:
                # HDBS has no sizes assigned
                if smi_types:
                    for smi in smi_types:
                        flat_rows.append({'hdbs': hdbs, 'size': None, 'smi': smi})
                else:
                    # No sizes and no SMI types
                    flat_rows.append({'hdbs': hdbs, 'size': None, 'smi': None})

        context["flat_rows"] = flat_rows
        return context


class HDBSTypeDetailView(LoginRequiredMixin, DetailView):
    """View HDBS type details with SMI names and related designs."""

    model = HDBSType
    template_name = "technology/hdbs_type_detail.html"
    context_object_name = "hdbs_type"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get SMI types for this HDBS
        smi_types = self.object.smi_types.select_related('size').order_by('size__size_decimal', 'smi_name')
        context["smi_types"] = smi_types

        # Build flat table rows: each row = (size, smi)
        # If HDBS has sizes, show one row per size with matching SMI types
        # SMI types with size=None apply to all sizes
        type_size_smi_rows = []
        sizes = self.object.sizes.filter(is_active=True).order_by('size_decimal')

        if sizes.exists():
            for size in sizes:
                # Find SMI types for this specific size OR no size (applies to all)
                size_smi_types = [s for s in smi_types if s.size_id == size.id or s.size_id is None]
                if size_smi_types:
                    for smi in size_smi_types:
                        type_size_smi_rows.append({'size': size, 'smi': smi})
                else:
                    # No SMI for this size - show row with empty SMI
                    type_size_smi_rows.append({'size': size, 'smi': None})
        else:
            # HDBS has no sizes assigned - show all SMI types without size
            for smi in smi_types:
                type_size_smi_rows.append({'size': None, 'smi': smi})
            if not smi_types:
                type_size_smi_rows.append({'size': None, 'smi': None})

        context["type_size_smi_rows"] = type_size_smi_rows

        # Get designs using this HDBS type - both legacy field and junction table
        legacy_design_ids = Design.objects.filter(
            hdbs_type__icontains=self.object.hdbs_name
        ).values_list('id', flat=True)
        junction_design_ids = self.object.design_assignments.filter(
            is_current=True
        ).values_list('design_id', flat=True)

        all_design_ids = set(legacy_design_ids) | set(junction_design_ids)
        context["related_designs"] = Design.objects.filter(
            id__in=all_design_ids
        ).select_related('size').order_by('mat_no')[:30]

        # Current design assignments via junction table
        context["design_hdbs_assignments"] = self.object.design_assignments.filter(
            is_current=True
        ).select_related('design', 'design__size', 'assigned_by').order_by('design__mat_no')
        return context


class HDBSTypeCreateView(LoginRequiredMixin, CreateView):
    """Create a new HDBS type."""

    model = HDBSType
    form_class = HDBSTypeForm
    template_name = "technology/hdbs_type_form.html"

    def get_success_url(self):
        # If coming from design or bom form, stay on page with success message
        from_page = self.request.GET.get('from')
        if from_page in ('design', 'bom'):
            return f"{reverse_lazy('technology:hdbs_type_create')}?from={from_page}&created=1"
        return reverse_lazy("technology:hdbs_type_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Add HDBS Type"
        context["submit_text"] = "Add Type"
        context["just_created"] = self.request.GET.get('created') == '1'
        context["from_page"] = self.request.GET.get('from')
        return context

    def form_valid(self, form):
        from_page = self.request.GET.get('from')
        if from_page == 'bom':
            messages.success(self.request, f"HDBS Type {form.instance.hdbs_name} created successfully. You can now close this tab and return to your BOM form.")
        else:
            messages.success(self.request, f"HDBS Type {form.instance.hdbs_name} created successfully. You can now close this tab and return to your Design form.")
        return super().form_valid(form)


class HDBSTypeUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing HDBS type."""

    model = HDBSType
    form_class = HDBSTypeForm
    template_name = "technology/hdbs_type_form.html"

    def get_success_url(self):
        return reverse_lazy("technology:hdbs_type_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit HDBS Type {self.object.hdbs_name}"
        context["submit_text"] = "Save Changes"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"HDBS Type {self.object.hdbs_name} updated successfully.")
        return super().form_valid(form)


class HDBSTypeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an HDBS type."""

    model = HDBSType
    template_name = "technology/hdbs_type_confirm_delete.html"
    success_url = reverse_lazy("technology:hdbs_type_list")

    def form_valid(self, form):
        messages.success(self.request, f"HDBS Type {self.object.hdbs_name} deleted.")
        return super().form_valid(form)


# =============================================================================
# SMI TYPE CRUD VIEWS (Client-facing naming linked to HDBS)
# =============================================================================


class SMITypeCreateView(LoginRequiredMixin, CreateView):
    """Create a new SMI type linked to an HDBS type."""

    model = SMIType
    form_class = SMITypeForm
    template_name = "technology/smi_type_form.html"

    def get_hdbs_type(self):
        """Get the HDBS type from URL or query param."""
        hdbs_pk = self.kwargs.get('hdbs_pk') or self.request.GET.get('hdbs')
        if hdbs_pk:
            return get_object_or_404(HDBSType, pk=hdbs_pk)
        return None

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        hdbs_type = self.get_hdbs_type()
        if hdbs_type:
            # Only show sizes that belong to this HDBS type
            if hdbs_type.sizes.exists():
                form.fields['size'].queryset = hdbs_type.sizes.filter(is_active=True).order_by('size_decimal')
            else:
                # If HDBS has no sizes, show all active sizes
                form.fields['size'].queryset = BitSize.objects.filter(is_active=True).order_by('size_decimal')
        return form

    def get_initial(self):
        initial = super().get_initial()
        # Pre-select HDBS type if provided in URL
        hdbs_pk = self.kwargs.get('hdbs_pk') or self.request.GET.get('hdbs')
        if hdbs_pk:
            initial['hdbs_type'] = hdbs_pk
        # Pre-select size if provided in query string
        size_pk = self.request.GET.get('size')
        if size_pk:
            initial['size'] = size_pk
        return initial

    def get_success_url(self):
        return reverse_lazy("technology:hdbs_type_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Add SMI Type"
        context["submit_text"] = "Add SMI Type"
        hdbs_type = self.get_hdbs_type()
        if hdbs_type:
            context["hdbs_type"] = hdbs_type
        return context

    def form_valid(self, form):
        messages.success(self.request, f"SMI Type {form.instance.smi_name} added successfully.")
        return super().form_valid(form)


class SMITypeCreateStandaloneView(LoginRequiredMixin, CreateView):
    """Create a new SMI type without pre-selected HDBS."""

    model = SMIType
    form_class = SMITypeForm
    template_name = "technology/smi_type_form.html"

    def get_success_url(self):
        # If coming from design or bom form, stay on page with success message
        from_page = self.request.GET.get('from')
        if from_page in ('design', 'bom'):
            return f"{reverse_lazy('technology:smi_type_create_standalone')}?from={from_page}&created=1"
        return reverse_lazy("technology:hdbs_type_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Add SMI Type"
        context["submit_text"] = "Add SMI Type"
        context["just_created"] = self.request.GET.get('created') == '1'
        context["from_page"] = self.request.GET.get('from')
        return context

    def form_valid(self, form):
        from_page = self.request.GET.get('from')
        if from_page == 'bom':
            messages.success(self.request, f"SMI Type {form.instance.smi_name} added successfully. You can now close this tab and return to your BOM form.")
        elif from_page == 'design':
            messages.success(self.request, f"SMI Type {form.instance.smi_name} added successfully. You can now close this tab and return to your Design form.")
        else:
            messages.success(self.request, f"SMI Type {form.instance.smi_name} added successfully.")
        return super().form_valid(form)


class SMITypeUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing SMI type."""

    model = SMIType
    form_class = SMITypeForm
    template_name = "technology/smi_type_form.html"

    def get_success_url(self):
        return reverse_lazy("technology:hdbs_type_detail", kwargs={"pk": self.object.hdbs_type.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit SMI Type {self.object.smi_name}"
        context["submit_text"] = "Save Changes"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"SMI Type {self.object.smi_name} updated successfully.")
        return super().form_valid(form)


class SMITypeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an SMI type."""

    model = SMIType
    template_name = "technology/smi_type_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("technology:hdbs_type_detail", kwargs={"pk": self.object.hdbs_type.pk})

    def form_valid(self, form):
        messages.success(self.request, f"SMI Type {self.object.smi_name} deleted.")
        return super().form_valid(form)


# =============================================================================
# API VIEWS FOR QUICK CREATE (Types)
# =============================================================================


class APIHDBSTypesView(LoginRequiredMixin, View):
    """API endpoint to get HDBS types for dropdowns."""

    def get(self, request):
        # Filter by active status unless show_inactive is set
        show_inactive = request.GET.get('show_inactive')
        if show_inactive:
            hdbs_types = HDBSType.objects.all()
        else:
            hdbs_types = HDBSType.objects.filter(is_active=True)

        # Search filter
        q = request.GET.get('q', '').strip()
        if q:
            hdbs_types = hdbs_types.filter(
                Q(hdbs_name__icontains=q) |
                Q(description__icontains=q) |
                Q(smi_types__smi_name__icontains=q)
            ).distinct()

        # Filter by size - show only HDBS types that have this size selected
        # OR have no sizes (meaning they apply to all sizes)
        size_id = request.GET.get('size', '').strip()
        if size_id:
            hdbs_types = hdbs_types.filter(
                Q(sizes__id=size_id) | Q(sizes__isnull=True)
            ).distinct()

        hdbs_types = hdbs_types.prefetch_related('sizes', 'smi_types').order_by('hdbs_name')

        # Build response with SMI types filtered by size if provided
        data = {'hdbs_types': []}
        for t in hdbs_types:
            # Get SMI types, optionally filtered by size
            if show_inactive:
                smi_qs = t.smi_types.all()
            else:
                smi_qs = t.smi_types.filter(is_active=True)

            # If size is specified, filter SMI types to those matching the size or with no size
            if size_id:
                smi_qs = smi_qs.filter(Q(size_id=size_id) | Q(size__isnull=True))

            smi_list = [
                {'id': s.id, 'smi_name': s.smi_name, 'is_active': s.is_active, 'size_id': s.size_id}
                for s in smi_qs.order_by('smi_name')
            ]

            # If size filter is applied, only show that size; otherwise show all sizes
            if size_id:
                sizes_list = [{'id': s.id, 'display': s.size_display} for s in t.sizes.filter(is_active=True, id=size_id)]
            else:
                sizes_list = [{'id': s.id, 'display': s.size_display} for s in t.sizes.filter(is_active=True)]

            data['hdbs_types'].append({
                'id': t.id,
                'hdbs_name': t.hdbs_name,
                'description': t.description or '',
                'is_active': t.is_active,
                'sizes': sizes_list,
                'smi_types': smi_list
            })

        return JsonResponse(data)


class APIHDBSTypeCreateView(LoginRequiredMixin, View):
    """API endpoint to quick create an HDBS type (optionally with SMI type)."""

    def post(self, request):
        import json
        try:
            data = json.loads(request.body)
            hdbs_name = data.get('hdbs_name', '').strip()

            if not hdbs_name:
                return JsonResponse({'success': False, 'error': 'HDBS Name is required'}, status=400)

            if HDBSType.objects.filter(hdbs_name=hdbs_name).exists():
                return JsonResponse({'success': False, 'error': 'HDBS Type already exists'}, status=400)

            hdbs_type = HDBSType.objects.create(
                hdbs_name=hdbs_name,
                description=data.get('description', ''),
                is_active=True
            )

            # Add sizes if provided
            size_ids = data.get('sizes', [])
            if size_ids:
                hdbs_type.sizes.set(size_ids)

            response_data = {
                'success': True,
                'hdbs_type': {
                    'id': hdbs_type.id,
                    'hdbs_name': hdbs_type.hdbs_name,
                }
            }

            # Also create SMI type if smi_name is provided
            smi_name = data.get('smi_name', '').strip()
            size_id = data.get('size_id')
            if smi_name and size_id:
                try:
                    size = BitSize.objects.get(pk=size_id)
                    # Add the size to HDBS type if not already added
                    hdbs_type.sizes.add(size)

                    smi_type = SMIType.objects.create(
                        smi_name=smi_name,
                        hdbs_type=hdbs_type,
                        size=size,
                        description=data.get('smi_description', ''),
                        is_active=True
                    )
                    response_data['smi_type'] = {
                        'id': smi_type.id,
                        'smi_name': smi_type.smi_name,
                    }
                except BitSize.DoesNotExist:
                    # Size not found, skip SMI creation but don't fail
                    pass

            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class APISMITypeCreateView(LoginRequiredMixin, View):
    """API endpoint to quick create an SMI type (uses size from design form)."""

    def post(self, request):
        import json
        try:
            data = json.loads(request.body)
            smi_name = data.get('smi_name', '').strip()
            hdbs_type_id = data.get('hdbs_type_id')
            size_id = data.get('size_id')

            if not smi_name:
                return JsonResponse({'success': False, 'error': 'SMI Name is required'}, status=400)

            if not hdbs_type_id:
                return JsonResponse({'success': False, 'error': 'HDBS Type is required'}, status=400)

            if not size_id:
                return JsonResponse({'success': False, 'error': 'Please select a Size in the design form first'}, status=400)

            hdbs_type = get_object_or_404(HDBSType, pk=hdbs_type_id)
            size = get_object_or_404(BitSize, pk=size_id)

            if SMIType.objects.filter(smi_name=smi_name, hdbs_type=hdbs_type, size=size).exists():
                return JsonResponse({'success': False, 'error': 'SMI Type already exists for this HDBS and size'}, status=400)

            # Add size to HDBS type's compatible sizes if not already there
            hdbs_type.sizes.add(size)

            smi_type = SMIType.objects.create(
                smi_name=smi_name,
                hdbs_type=hdbs_type,
                size=size,
                description=data.get('description', ''),
                is_active=True
            )

            return JsonResponse({
                'success': True,
                'smi_type': {
                    'id': smi_type.id,
                    'smi_name': smi_type.smi_name,
                    'hdbs_type_id': hdbs_type.id,
                    'hdbs_name': hdbs_type.hdbs_name,
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =============================================================================
# SMI TYPE FILTER API (for BOM creation workflow)
# =============================================================================


class APISMITypesFilterView(LoginRequiredMixin, View):
    """
    API endpoint to get SMI Types filtered by HDBS Type and Size.
    Used in the BOM creation workflow to show only relevant SMI options.
    """

    def get(self, request):
        hdbs_type_id = request.GET.get('hdbs_type_id')
        size_id = request.GET.get('size_id')

        queryset = SMIType.objects.filter(is_active=True)

        if hdbs_type_id:
            queryset = queryset.filter(hdbs_type_id=hdbs_type_id)

        if size_id:
            queryset = queryset.filter(size_id=size_id)

        smi_types = []
        for smi in queryset.select_related('hdbs_type', 'size'):
            smi_types.append({
                'id': smi.id,
                'smi_name': smi.smi_name,
                'hdbs_type_id': smi.hdbs_type_id,
                'hdbs_name': smi.hdbs_type.hdbs_name,
                'size_id': smi.size_id,
                'size_display': str(smi.size) if smi.size else '',
            })

        return JsonResponse({
            'success': True,
            'smi_types': smi_types,
        })


# =============================================================================
# COMBINED BOM CREATE/BUILDER VIEW
# =============================================================================


class BOMCreateWithBuilderView(LoginRequiredMixin, TemplateView):
    """
    BOM creation page - Design selection for Cutter Map workflow.

    This view shows a list of L3/L4 Designs for the user to select,
    then redirects to the Cutter Map app to import PDF and create the BOM.
    """

    template_name = "technology/bom_create_builder.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create BOM"

        # Get designs for selection (L3/L4 only) - include all statuses
        context["designs"] = Design.objects.filter(
            order_level__in=["3", "4"]
        ).select_related("size").prefetch_related(
            "boms"
        ).order_by("-created_at")

        return context


class APIDesignsFilterView(LoginRequiredMixin, View):
    """
    API endpoint to get Designs filtered by HDBS Type and/or Size.
    Used in the BOM creation workflow to show matching designs.
    """

    def get(self, request):
        hdbs_type = request.GET.get('hdbs_type')
        size_id = request.GET.get('size_id')

        queryset = Design.objects.filter(
            order_level__in=["3", "4"],
            status__in=[Design.Status.DRAFT, Design.Status.ACTIVE]
        )

        if hdbs_type:
            queryset = queryset.filter(hdbs_type__icontains=hdbs_type)

        if size_id:
            queryset = queryset.filter(size_id=size_id)

        designs = []
        for d in queryset.select_related("size")[:20]:
            designs.append({
                'id': d.id,
                'mat_no': d.mat_no,
                'hdbs_type': d.hdbs_type,
                'size': str(d.size) if d.size else '',
                'order_level': d.order_level,
                'display': f"{d.mat_no} - {d.hdbs_type} ({d.size})" if d.size else f"{d.mat_no} - {d.hdbs_type}",
            })

        return JsonResponse({
            'success': True,
            'designs': designs,
        })
