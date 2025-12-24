"""
ARDT FMS - Inventory App Views
Version: 5.4
"""

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View

from .forms import (
    CategoryAttributeForm,
    InventoryCategoryForm,
    InventoryItemForm,
    InventoryLocationForm,
    InventoryStockForm,
    InventoryTransactionForm,
    ItemBitSpecForm,
    ItemCutterSpecForm,
    ItemIdentifierForm,
    ItemPlanningForm,
    ItemSupplierForm,
    StockAdjustmentForm,
    # Reference Data Forms
    PartyForm,
    ConditionTypeForm,
    QualityStatusForm,
    AdjustmentReasonForm,
    OwnershipTypeForm,
)
from .models import (
    Attribute,
    CategoryAttribute,
    InventoryCategory,
    InventoryItem,
    InventoryLocation,
    InventoryStock,
    InventoryTransaction,
    ItemAttributeValue,
    ItemBitSpec,
    ItemCutterSpec,
    ItemIdentifier,
    ItemPlanning,
    ItemRelationship,
    ItemSupplier,
    ItemVariant,
    UnitOfMeasure,
    VariantCase,
    # Reference Data
    Party,
    ConditionType,
    QualityStatus,
    AdjustmentReason,
    OwnershipType,
)


# =============================================================================
# Dashboard View
# =============================================================================


class InventoryDashboardView(LoginRequiredMixin, View):
    """Inventory dashboard with stats and quick actions."""

    template_name = "inventory/dashboard.html"

    def get(self, request):
        from django.shortcuts import render
        from .models import (
            GoodsReceiptNote, StockIssue, StockTransfer,
            StockAdjustment as StockAdjustmentDoc, StockLedger,
            Asset, BillOfMaterial, StockReservation,
        )

        # Calculate stats
        stats = {
            "total_items": InventoryItem.objects.filter(is_active=True).count(),
            "total_stock_value": StockLedger.objects.aggregate(
                total=Sum(F("qty_delta") * F("unit_cost"))
            )["total"] or 0,
            "low_stock_count": InventoryStock.objects.filter(
                quantity_on_hand__lt=F("item__reorder_point")
            ).count(),
            "active_reservations": StockReservation.objects.filter(
                status="PENDING"
            ).count(),
            "draft_grns": GoodsReceiptNote.objects.filter(status="DRAFT").count(),
            "draft_issues": StockIssue.objects.filter(status="DRAFT").count(),
            "draft_transfers": StockTransfer.objects.filter(status="DRAFT").count(),
            "draft_adjustments": StockAdjustmentDoc.objects.filter(status="DRAFT").count(),
            "total_assets": Asset.objects.count(),
            "active_boms": BillOfMaterial.objects.filter(status="ACTIVE").count(),
        }

        # Recent ledger entries
        recent_ledger = StockLedger.objects.select_related(
            "item", "location"
        ).order_by("-transaction_date")[:10]

        return render(request, self.template_name, {
            "stats": stats,
            "recent_ledger": recent_ledger,
            "page_title": "Inventory Dashboard",
        })


# =============================================================================
# Category Views
# =============================================================================


class CategoryListView(LoginRequiredMixin, ListView):
    """List all inventory categories."""

    model = InventoryCategory
    template_name = "inventory/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return InventoryCategory.objects.filter(parent__isnull=True).prefetch_related("children")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Inventory Categories"
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Create inventory category."""

    model = InventoryCategory
    form_class = InventoryCategoryForm
    template_name = "inventory/category_form.html"
    success_url = reverse_lazy("inventory:category_list")

    def form_valid(self, form):
        messages.success(self.request, f"Category '{form.instance.name}' created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Category"
        context["form_title"] = "Create Inventory Category"
        return context


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Update inventory category."""

    model = InventoryCategory
    form_class = InventoryCategoryForm
    template_name = "inventory/category_form.html"
    success_url = reverse_lazy("inventory:category_list")

    def form_valid(self, form):
        messages.success(self.request, f"Category '{form.instance.name}' updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        context["form_title"] = "Edit Category"

        # Child categories
        context["child_categories"] = self.object.children.all()

        # Own attributes (directly on this category)
        context["own_attributes"] = self.object.category_attributes.select_related(
            "attribute", "unit"
        ).order_by("display_order")

        # Inherited attributes from parent categories
        inherited = []
        parent = self.object.parent
        while parent:
            for attr in parent.category_attributes.select_related(
                "attribute", "unit"
            ).order_by("display_order"):
                inherited.append(attr)
            parent = parent.parent
        context["inherited_attributes"] = inherited

        # Parent category info for code prefix suggestions
        if self.object.parent:
            context["parent_category"] = self.object.parent

        return context


class CategoryDetailView(LoginRequiredMixin, DetailView):
    """View category details with attributes."""

    model = InventoryCategory
    template_name = "inventory/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"{self.object.code} - {self.object.name}"

        # Own attributes (directly on this category)
        context["own_attributes"] = self.object.category_attributes.select_related("attribute", "unit").order_by("display_order")

        # Inherited attributes from parent categories
        inherited = []
        parent = self.object.parent
        while parent:
            for attr in parent.category_attributes.select_related("attribute", "unit").order_by("display_order"):
                inherited.append(attr)
            parent = parent.parent
        context["inherited_attributes"] = inherited

        # Child categories
        context["child_categories"] = self.object.children.all()

        # Items in this category
        context["items"] = self.object.items.all()[:10]
        context["items_count"] = self.object.items.count()
        return context


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete inventory category."""

    model = InventoryCategory
    template_name = "inventory/category_confirm_delete.html"
    success_url = reverse_lazy("inventory:category_list")

    def form_valid(self, form):
        messages.success(self.request, f"Category '{self.object.name}' deleted successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Delete Category"
        return context


# =============================================================================
# Location Views
# =============================================================================


class LocationListView(LoginRequiredMixin, ListView):
    """List all inventory locations."""

    model = InventoryLocation
    template_name = "inventory/location_list.html"
    context_object_name = "locations"
    paginate_by = 25

    def get_queryset(self):
        qs = InventoryLocation.objects.select_related("warehouse")

        warehouse = self.request.GET.get("warehouse")
        if warehouse:
            qs = qs.filter(warehouse_id=warehouse)

        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(Q(code__icontains=search) | Q(name__icontains=search))

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Inventory Locations"
        context["search_query"] = self.request.GET.get("q", "")
        from apps.sales.models import Warehouse

        context["warehouses"] = Warehouse.objects.filter(is_active=True)
        context["current_warehouse"] = self.request.GET.get("warehouse", "")
        return context


class LocationCreateView(LoginRequiredMixin, CreateView):
    """Create inventory location."""

    model = InventoryLocation
    form_class = InventoryLocationForm
    template_name = "inventory/location_form.html"
    success_url = reverse_lazy("inventory:location_list")

    def form_valid(self, form):
        messages.success(self.request, f"Location '{form.instance.code}' created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Location"
        context["form_title"] = "Create Inventory Location"
        return context


class LocationUpdateView(LoginRequiredMixin, UpdateView):
    """Update inventory location."""

    model = InventoryLocation
    form_class = InventoryLocationForm
    template_name = "inventory/location_form.html"
    success_url = reverse_lazy("inventory:location_list")

    def form_valid(self, form):
        messages.success(self.request, f"Location '{form.instance.code}' updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.code}"
        context["form_title"] = "Edit Location"
        return context


# =============================================================================
# Item Views
# =============================================================================


class ItemListView(LoginRequiredMixin, ListView):
    """List all inventory items."""

    model = InventoryItem
    template_name = "inventory/item_list.html"
    context_object_name = "items"
    paginate_by = 25

    def get_queryset(self):
        qs = InventoryItem.objects.select_related("category", "primary_supplier").annotate(
            current_stock=Sum("stock_records__quantity_on_hand")
        )

        # Filter by category
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category_id=category)

        # Filter by type
        item_type = self.request.GET.get("type")
        if item_type:
            qs = qs.filter(item_type=item_type)

        # Filter by low stock
        low_stock = self.request.GET.get("low_stock")
        if low_stock:
            qs = qs.filter(current_stock__lte=F("min_stock"))

        # Search
        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(Q(code__icontains=search) | Q(name__icontains=search))

        return qs.order_by("code")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Inventory Items"
        context["categories"] = InventoryCategory.objects.filter(is_active=True)
        context["type_choices"] = InventoryItem.ItemType.choices
        context["current_category"] = self.request.GET.get("category", "")
        context["current_type"] = self.request.GET.get("type", "")
        context["search_query"] = self.request.GET.get("q", "")
        context["low_stock_filter"] = self.request.GET.get("low_stock", "")
        return context


class ItemDetailView(LoginRequiredMixin, DetailView):
    """View inventory item details."""

    model = InventoryItem
    template_name = "inventory/item_detail.html"
    context_object_name = "item"

    def get_queryset(self):
        return InventoryItem.objects.select_related("category", "primary_supplier", "created_by", "manufacturer", "uom")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = self.object
        context["page_title"] = f"{item.code} - {item.name}"

        # Stock by location
        context["stock_by_location"] = item.stock_records.select_related("location", "location__warehouse")

        # Recent transactions
        context["recent_transactions"] = item.transactions.select_related("created_by", "from_location", "to_location").order_by(
            "-transaction_date"
        )[:10]

        # Total stock
        context["total_stock"] = item.total_stock

        # Is low stock?
        context["is_low_stock"] = item.total_stock <= item.min_stock

        # NEW: Planning data (per-warehouse min/max/reorder)
        context["planning_records"] = ItemPlanning.objects.filter(item=item).select_related("warehouse")

        # NEW: Suppliers (multiple suppliers per item)
        context["suppliers"] = ItemSupplier.objects.filter(item=item).select_related("supplier")

        # NEW: Identifiers (multiple barcodes/identifiers) with generated images
        identifiers = ItemIdentifier.objects.filter(item=item)

        # Generate QR/barcode images for each identifier
        from .utils import generate_identifier_image, generate_inventory_item_qr
        identifiers_with_images = []
        for ident in identifiers:
            identifiers_with_images.append({
                'identifier': ident,
                'image': generate_identifier_image(ident)
            })
        context["identifiers"] = identifiers_with_images

        # Generate default QR code for the item itself
        context["item_qr_code"] = generate_inventory_item_qr(item)

        # NEW: Bit Spec (if exists)
        try:
            context["bit_spec"] = item.bit_spec
        except ItemBitSpec.DoesNotExist:
            context["bit_spec"] = None

        # NEW: Cutter Spec (if exists)
        try:
            context["cutter_spec"] = item.cutter_spec
        except ItemCutterSpec.DoesNotExist:
            context["cutter_spec"] = None

        # Check if item category suggests it's a bit or cutter for showing spec forms
        category_name = item.category.name.lower() if item.category else ""
        context["is_bit_item"] = "bit" in category_name or "pdc" in category_name or "tci" in category_name
        context["is_cutter_item"] = "cutter" in category_name or "pdc" in category_name

        # Category Attributes and Values
        if item.category:
            # Get all attributes for this category (including inherited)
            category_attributes = list(item.category.category_attributes.select_related("attribute", "unit").order_by("display_order"))

            # Get inherited attributes from parent categories
            parent = item.category.parent
            while parent:
                for attr in parent.category_attributes.select_related("attribute", "unit").order_by("display_order"):
                    if attr not in category_attributes:
                        category_attributes.append(attr)
                parent = parent.parent

            context["category_attributes"] = category_attributes

            # Get existing attribute values for this item
            context["attribute_values"] = item.attribute_values.select_related("attribute", "attribute__attribute", "attribute__unit")
        else:
            context["category_attributes"] = []
            context["attribute_values"] = []

        return context


class ItemCreateView(LoginRequiredMixin, CreateView):
    """Create inventory item."""

    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/item_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        # Auto-generate code if not provided
        if not form.instance.code and form.instance.category:
            form.instance.code = form.instance.category.generate_next_code()

        messages.success(self.request, f"Item '{form.instance.name}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Item"
        context["form_title"] = "Create Inventory Item"
        context["categories"] = InventoryCategory.objects.filter(is_active=True, parent__isnull=True).prefetch_related("children")
        context["type_choices"] = InventoryItem.ItemType.choices
        # Only show packaging/quantity UOMs (CARTON, BOX, EACH, PIECE, etc.)
        context["packaging_uoms"] = UnitOfMeasure.objects.filter(
            is_active=True
        ).filter(
            Q(unit_type__in=['QUANTITY', 'PACKAGING']) | Q(is_packaging=True)
        ).order_by('name')
        context["existing_attribute_values"] = "{}"
        return context


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    """Update inventory item."""

    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/item_form.html"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        # Store attribute values from POST to preserve them if form fails
        self._attr_values = {k: v for k, v in request.POST.items() if k.startswith('attr_')}

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        item = self.object

        # Process attribute values from POST data
        for key, value in self.request.POST.items():
            if key.startswith('attr_') and value:
                try:
                    attr_id = int(key.replace('attr_', ''))
                    category_attr = CategoryAttribute.objects.get(pk=attr_id)

                    # Create or update the attribute value
                    attr_value, created = ItemAttributeValue.objects.get_or_create(
                        item=item,
                        attribute=category_attr
                    )

                    # Set the appropriate value field based on type
                    if category_attr.attribute_type == 'NUMBER':
                        attr_value.number_value = value
                        attr_value.text_value = ''
                    elif category_attr.attribute_type == 'BOOLEAN':
                        attr_value.boolean_value = value.lower() in ('true', '1', 'yes', 'on')
                        attr_value.text_value = ''
                    elif category_attr.attribute_type == 'DATE':
                        attr_value.date_value = value
                        attr_value.text_value = ''
                    else:
                        attr_value.text_value = value

                    attr_value.save()
                except (ValueError, CategoryAttribute.DoesNotExist) as e:
                    print(f"Error saving attribute {key}: {e}")

        messages.success(self.request, f"Item '{form.instance.code}' updated successfully.")
        return response

    def form_invalid(self, form):
        # Log form errors for debugging
        print(f"Form errors: {form.errors}")
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.code}"
        context["form_title"] = "Edit Inventory Item"
        context["categories"] = InventoryCategory.objects.filter(is_active=True, parent__isnull=True).prefetch_related("children")
        context["type_choices"] = InventoryItem.ItemType.choices
        # Only show packaging/quantity UOMs (CARTON, BOX, EACH, PIECE, etc.)
        context["packaging_uoms"] = UnitOfMeasure.objects.filter(
            is_active=True
        ).filter(
            Q(unit_type__in=['QUANTITY', 'PACKAGING']) | Q(is_packaging=True)
        ).order_by('name')

        # Pass existing attribute values for pre-populating the form
        if self.object.category:
            existing_values = {}
            for av in self.object.attribute_values.select_related('attribute', 'attribute__attribute'):
                code = av.attribute.attribute.code if av.attribute.attribute else str(av.attribute.pk)
                # Convert Decimal to float/string for JSON serialization
                val = av.display_value
                if val is not None and hasattr(val, '__float__'):
                    val = float(val)
                existing_values[code] = val
            import json
            context["existing_attribute_values"] = json.dumps(existing_values)
        else:
            context["existing_attribute_values"] = "{}"
        return context


# =============================================================================
# Transaction Views
# =============================================================================


class TransactionListView(LoginRequiredMixin, ListView):
    """List all inventory transactions."""

    model = InventoryTransaction
    template_name = "inventory/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 50

    def get_queryset(self):
        qs = InventoryTransaction.objects.select_related("item", "from_location", "to_location", "created_by")

        # Filter by type
        trans_type = self.request.GET.get("type")
        if trans_type:
            qs = qs.filter(transaction_type=trans_type)

        # Filter by item
        item = self.request.GET.get("item")
        if item:
            qs = qs.filter(item_id=item)

        # Search
        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(Q(transaction_number__icontains=search) | Q(reference_number__icontains=search))

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Inventory Transactions"
        context["type_choices"] = InventoryTransaction.TransactionType.choices
        context["current_type"] = self.request.GET.get("type", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


class TransactionDetailView(LoginRequiredMixin, DetailView):
    """View transaction details."""

    model = InventoryTransaction
    template_name = "inventory/transaction_detail.html"
    context_object_name = "transaction"

    def get_queryset(self):
        return InventoryTransaction.objects.select_related("item", "from_location", "to_location", "created_by")


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Create inventory transaction."""

    model = InventoryTransaction
    form_class = InventoryTransactionForm
    template_name = "inventory/transaction_form.html"
    success_url = reverse_lazy("inventory:transaction_list")

    def form_valid(self, form):
        transaction = form.save(commit=False)
        transaction.created_by = self.request.user
        transaction.transaction_date = timezone.now()
        transaction.transaction_number = self.generate_transaction_number()

        # Calculate total cost
        transaction.total_cost = transaction.quantity * transaction.unit_cost

        transaction.save()

        # Update stock levels
        self.update_stock(transaction)

        messages.success(self.request, f"Transaction '{transaction.transaction_number}' created successfully.")
        return redirect(self.success_url)

    def generate_transaction_number(self):
        """Generate unique transaction number."""
        prefix = "TXN"
        today = timezone.now().strftime("%Y%m%d")
        last = InventoryTransaction.objects.filter(transaction_number__startswith=f"{prefix}-{today}").order_by("-id").first()
        if last:
            try:
                last_num = int(last.transaction_number.split("-")[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        return f"{prefix}-{today}-{str(next_num).zfill(4)}"

    def update_stock(self, transaction):
        """Update stock levels based on transaction."""
        if transaction.transaction_type == "RECEIPT":
            # Add to destination
            stock, _ = InventoryStock.objects.get_or_create(
                item=transaction.item, location=transaction.to_location, defaults={"quantity_on_hand": 0}
            )
            stock.quantity_on_hand = F("quantity_on_hand") + transaction.quantity
            stock.last_movement_date = timezone.now()
            stock.save()

        elif transaction.transaction_type == "ISSUE":
            # Remove from source
            try:
                stock = InventoryStock.objects.get(item=transaction.item, location=transaction.from_location)
                stock.quantity_on_hand = F("quantity_on_hand") - transaction.quantity
                stock.last_movement_date = timezone.now()
                stock.save()
            except InventoryStock.DoesNotExist:
                pass

        elif transaction.transaction_type == "TRANSFER":
            # Remove from source
            try:
                from_stock = InventoryStock.objects.get(item=transaction.item, location=transaction.from_location)
                from_stock.quantity_on_hand = F("quantity_on_hand") - transaction.quantity
                from_stock.last_movement_date = timezone.now()
                from_stock.save()
            except InventoryStock.DoesNotExist:
                pass

            # Add to destination
            to_stock, _ = InventoryStock.objects.get_or_create(
                item=transaction.item, location=transaction.to_location, defaults={"quantity_on_hand": 0}
            )
            to_stock.quantity_on_hand = F("quantity_on_hand") + transaction.quantity
            to_stock.last_movement_date = timezone.now()
            to_stock.save()

        elif transaction.transaction_type == "ADJUSTMENT":
            # Adjustment can be positive or negative
            if transaction.to_location:
                stock, _ = InventoryStock.objects.get_or_create(
                    item=transaction.item, location=transaction.to_location, defaults={"quantity_on_hand": 0}
                )
                stock.quantity_on_hand = F("quantity_on_hand") + transaction.quantity
                stock.last_movement_date = timezone.now()
                stock.save()
            elif transaction.from_location:
                try:
                    stock = InventoryStock.objects.get(item=transaction.item, location=transaction.from_location)
                    stock.quantity_on_hand = F("quantity_on_hand") - transaction.quantity
                    stock.last_movement_date = timezone.now()
                    stock.save()
                except InventoryStock.DoesNotExist:
                    pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Transaction"
        context["form_title"] = "Create Inventory Transaction"
        return context


# =============================================================================
# Stock Views
# =============================================================================


class StockListView(LoginRequiredMixin, ListView):
    """List all stock records."""

    model = InventoryStock
    template_name = "inventory/stock_list.html"
    context_object_name = "stock_records"
    paginate_by = 50

    def get_queryset(self):
        qs = InventoryStock.objects.select_related("item", "location", "location__warehouse").filter(quantity_on_hand__gt=0)

        # Filter by warehouse
        warehouse = self.request.GET.get("warehouse")
        if warehouse:
            qs = qs.filter(location__warehouse_id=warehouse)

        # Filter by item
        item = self.request.GET.get("item")
        if item:
            qs = qs.filter(item_id=item)

        return qs.order_by("item__code", "location__code")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Stock Levels"
        from apps.sales.models import Warehouse

        context["warehouses"] = Warehouse.objects.filter(is_active=True)
        context["current_warehouse"] = self.request.GET.get("warehouse", "")
        return context


class StockAdjustView(LoginRequiredMixin, View):
    """Quick stock adjustment view."""

    def post(self, request, pk):
        stock = get_object_or_404(InventoryStock, pk=pk)
        form = StockAdjustmentForm(request.POST)

        if form.is_valid():
            adjustment_type = form.cleaned_data["adjustment_type"]
            quantity = form.cleaned_data["quantity"]
            reason = form.cleaned_data["reason"]
            notes = form.cleaned_data["notes"]

            # Create transaction
            trans_type = "ADJUSTMENT"
            transaction = InventoryTransaction.objects.create(
                transaction_number=f"ADJ-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                transaction_type=trans_type,
                transaction_date=timezone.now(),
                item=stock.item,
                from_location=stock.location if adjustment_type == "REMOVE" else None,
                to_location=stock.location if adjustment_type == "ADD" else None,
                quantity=quantity,
                unit=stock.item.unit,
                reason=reason,
                notes=notes,
                created_by=request.user,
            )

            # Update stock
            if adjustment_type == "ADD":
                stock.quantity_on_hand = F("quantity_on_hand") + quantity
            else:
                stock.quantity_on_hand = F("quantity_on_hand") - quantity
            stock.last_movement_date = timezone.now()
            stock.save()

            messages.success(request, f"Stock adjusted successfully. Transaction: {transaction.transaction_number}")
        else:
            messages.error(request, "Invalid adjustment data.")

        return redirect("inventory:item_detail", pk=stock.item.pk)


# =============================================================================
# Attribute Views (Simple global list - just names)
# =============================================================================


class AttributeListView(LoginRequiredMixin, ListView):
    """List of all attributes (simple name list) with client-side sort/filter."""

    model = Attribute
    template_name = "inventory/attribute_list.html"
    context_object_name = "attributes"
    # No pagination - client-side filtering handles all data

    def get_queryset(self):
        # Load all attributes for client-side filtering/sorting
        return Attribute.objects.all().order_by("classification", "name")

    def get_context_data(self, **kwargs):
        import json
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Attributes"
        context["search_query"] = self.request.GET.get("q", "")
        context["selected_classification"] = self.request.GET.get("classification", "")
        context["classification_choices"] = Attribute.Classification.choices
        context["type_choices"] = Attribute.DataType.choices

        # Serialize attributes as JSON for safe JavaScript consumption
        attributes_json = []
        for attr in context["attributes"]:
            attributes_json.append({
                "id": attr.id,
                "code": attr.code or "",
                "name": attr.name or "",
                "classification": attr.classification or "",
                "type": attr.data_type or "",
                "typeDisplay": attr.get_data_type_display() or "",
                "isActive": attr.is_active,
                "status": "active" if attr.is_active else "inactive",
                "usedIn": attr.category_usages.count(),
                "editUrl": f"/inventory/attributes/{attr.pk}/edit/",
                "deleteUrl": f"/inventory/attributes/{attr.pk}/delete/",
                "visible": True
            })
        context["attributes_json"] = json.dumps(attributes_json)
        return context


class StandaloneAttributeCreateView(LoginRequiredMixin, CreateView):
    """Create a new attribute."""

    model = Attribute
    template_name = "inventory/standalone_attribute_form.html"
    fields = ["code", "name", "classification", "data_type", "description", "notes", "is_active"]

    def form_valid(self, form):
        messages.success(self.request, f"Attribute '{form.instance.name}' created with code {form.instance.code}.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:attribute_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Attribute"
        context["form_title"] = "Create New Attribute"
        return context


class StandaloneAttributeUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an attribute (code is read-only)."""

    model = Attribute
    template_name = "inventory/standalone_attribute_form.html"
    fields = ["name", "classification", "data_type", "description", "notes", "is_active"]

    def form_valid(self, form):
        messages.success(self.request, f"Attribute '{form.instance.name}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:attribute_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        context["form_title"] = f"Edit Attribute: {self.object.name}"
        return context


class StandaloneAttributeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an attribute."""

    model = Attribute
    template_name = "inventory/standalone_attribute_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("inventory:attribute_list")

    def form_valid(self, form):
        messages.success(self.request, f"Attribute '{self.object.name}' deleted.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Delete Attribute"
        return context


# =============================================================================
# Category Attribute Views (Link Attribute to Category with config)
# =============================================================================


class CategoryAttributeListView(LoginRequiredMixin, ListView):
    """List of category-attribute mappings."""

    model = CategoryAttribute
    template_name = "inventory/category_attribute_list.html"
    context_object_name = "attributes"
    paginate_by = 50

    def get_queryset(self):
        queryset = CategoryAttribute.objects.select_related("category", "attribute", "unit")

        # Search filter
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(attribute__code__icontains=search) |
                Q(attribute__name__icontains=search) |
                Q(category__name__icontains=search)
            )

        # Category filter
        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset.order_by("category__name", "display_order")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Category Attributes"
        context["search_query"] = self.request.GET.get("q", "")
        context["selected_category"] = self.request.GET.get("category", "")
        context["categories"] = InventoryCategory.objects.all().order_by("name")
        context["attribute_types"] = CategoryAttribute.AttributeType.choices
        return context


class CategoryAttributeCreateView(LoginRequiredMixin, CreateView):
    """Link an attribute to a category with type/unit/validation."""

    model = CategoryAttribute
    template_name = "inventory/category_attribute_form.html"
    form_class = CategoryAttributeForm

    def get_initial(self):
        initial = super().get_initial()
        category_pk = self.request.GET.get("category")
        if category_pk:
            initial["category"] = category_pk
        return initial

    def form_valid(self, form):
        messages.success(self.request, f"Attribute linked to category.")
        return super().form_valid(form)

    def get_success_url(self):
        # Return to category detail if we came from there
        if self.object.category:
            return reverse_lazy("inventory:category_detail", kwargs={"pk": self.object.category.pk})
        return reverse_lazy("inventory:category_attribute_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get category from query param
        category_pk = self.request.GET.get("category")
        if category_pk:
            context["category"] = get_object_or_404(InventoryCategory, pk=category_pk)
        else:
            context["category"] = None
        context["page_title"] = "Link Attribute to Category"
        context["form_title"] = "Configure Attribute for Category"
        context["categories"] = InventoryCategory.objects.all().order_by("name")
        context["attributes"] = Attribute.objects.filter(is_active=True).order_by("name")
        context["units"] = UnitOfMeasure.objects.filter(is_active=True).order_by("name")
        context["attribute_types"] = CategoryAttribute.AttributeType.choices
        return context


class CategoryAttributeUpdateView(LoginRequiredMixin, UpdateView):
    """Update category-attribute configuration."""

    model = CategoryAttribute
    template_name = "inventory/category_attribute_form.html"
    form_class = CategoryAttributeForm

    def form_valid(self, form):
        messages.success(self.request, f"Category attribute updated.")
        return super().form_valid(form)

    def get_success_url(self):
        if self.object.category:
            return reverse_lazy("inventory:category_detail", kwargs={"pk": self.object.category.pk})
        return reverse_lazy("inventory:category_attribute_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.object.category
        context["page_title"] = "Edit Category Attribute"
        attr_name = self.object.attribute.name if self.object.attribute else "Unknown"
        context["form_title"] = f"Edit: {attr_name} in {self.object.category.name}"
        context["categories"] = InventoryCategory.objects.all().order_by("name")
        context["attributes"] = Attribute.objects.filter(is_active=True).order_by("name")
        context["units"] = UnitOfMeasure.objects.filter(is_active=True).order_by("name")
        context["attribute_types"] = CategoryAttribute.AttributeType.choices
        return context


class CategoryAttributeDeleteView(LoginRequiredMixin, DeleteView):
    """Remove attribute from category."""

    model = CategoryAttribute
    template_name = "inventory/category_attribute_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("inventory:category_attribute_list")

    def form_valid(self, form):
        messages.success(self.request, f"Attribute removed from category.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Remove Attribute from Category"
        return context


class CategoryAttributeBulkCreateView(LoginRequiredMixin, View):
    """
    Bulk add attributes to a category with a two-phase form:
    Phase 1: Select attributes from a filterable table
    Phase 2: Configure each selected attribute (type, unit, validation, etc.)
    """
    template_name = "inventory/category_attribute_bulk_form.html"

    def get_category(self):
        category_pk = self.request.GET.get("category") or self.request.POST.get("category")
        if category_pk:
            return get_object_or_404(InventoryCategory, pk=category_pk)
        return None

    def _serialize_attributes_json(self, attributes, existing_attr_ids):
        """Serialize attributes list to JSON for safe JavaScript consumption."""
        import json
        attrs_list = []
        for attr in attributes:
            attrs_list.append({
                "id": attr.id,
                "code": attr.code or "",
                "name": attr.name or "",
                "classification": attr.classification or "",
                "dataType": attr.data_type or "",
                "isLinked": attr.id in existing_attr_ids,
                "selected": attr.id in existing_attr_ids,
            })
        return json.dumps(attrs_list)

    def _serialize_existing_configs_json(self, existing_cat_attrs):
        """Serialize existing category attribute configs to JSON."""
        import json
        configs = {}
        for attr_id, ca in existing_cat_attrs.items():
            configs[str(attr_id)] = {
                "type": ca.attribute_type or "TEXT",
                "unit": ca.unit_id if ca.unit_id else "",
                "min": str(ca.min_value) if ca.min_value is not None else "",
                "max": str(ca.max_value) if ca.max_value is not None else "",
                "options": ca.options if ca.options else "",
                "defaultValue": ca.default_value or "",
                "rules": ca.conditional_rules if ca.conditional_rules else None,
                "required": ca.is_required,
                "inName": ca.is_used_in_name,
                "order": ca.display_order or 0,
            }
        return json.dumps(configs)

    def get(self, request):
        category = self.get_category()
        if not category:
            messages.error(request, "Please select a category first.")
            return redirect("inventory:category_list")

        # Get existing category attributes with their config for this category
        existing_cat_attrs = {
            ca.attribute_id: ca
            for ca in CategoryAttribute.objects.filter(category=category)
            .select_related("attribute", "unit")
        }
        existing_attr_ids = set(existing_cat_attrs.keys())

        # Get all available attributes (include already linked for bulk edit)
        attributes = Attribute.objects.filter(is_active=True).order_by("classification", "name")

        context = {
            "category": category,
            "attributes": attributes,
            "existing_attr_ids": existing_attr_ids,  # For pre-checking in template
            "existing_cat_attrs": existing_cat_attrs,  # For pre-filling config values
            "attributes_json": self._serialize_attributes_json(attributes, existing_attr_ids),
            "classifications": Attribute.Classification.choices,
            "attribute_types": CategoryAttribute.AttributeType.choices,
            "units": UnitOfMeasure.objects.filter(is_active=True).order_by("unit_type", "name"),
            "page_title": f"Bulk Add/Edit Attributes - {category.name}",
            "phase": "select",  # or "configure"
        }
        return render(request, self.template_name, context)

    def post(self, request):
        category = self.get_category()
        if not category:
            messages.error(request, "Category not found.")
            return redirect("inventory:category_list")

        phase = request.POST.get("phase", "select")

        if phase == "select":
            # Phase 1: User selected attributes, show configuration form
            selected_ids = request.POST.getlist("selected_attributes")
            if not selected_ids:
                messages.warning(request, "Please select at least one attribute.")
                return redirect(f"{request.path}?category={category.pk}")

            attributes = Attribute.objects.filter(id__in=selected_ids, is_active=True)

            # Get existing configurations for pre-filling the form
            existing_cat_attrs = {
                ca.attribute_id: ca
                for ca in CategoryAttribute.objects.filter(
                    category=category, attribute_id__in=selected_ids
                ).select_related("unit")
            }

            context = {
                "category": category,
                "selected_attributes": attributes,
                "existing_cat_attrs": existing_cat_attrs,  # For pre-filling config values
                "existing_configs_json": self._serialize_existing_configs_json(existing_cat_attrs),
                "attribute_types": CategoryAttribute.AttributeType.choices,
                "units": UnitOfMeasure.objects.filter(is_active=True).order_by("unit_type", "name"),
                "page_title": f"Configure Attributes for {category.name}",
                "phase": "configure",
            }
            return render(request, self.template_name, context)

        elif phase == "configure":
            # Phase 2: Save all configurations (create or update)
            attribute_ids = request.POST.getlist("attribute_id")
            created_count = 0
            updated_count = 0
            errors = []

            for attr_id in attribute_ids:
                try:
                    attribute = Attribute.objects.get(id=attr_id)

                    # Get configuration values for this attribute
                    attr_type = request.POST.get(f"type_{attr_id}", "TEXT")
                    unit_id = request.POST.get(f"unit_{attr_id}") or None
                    min_val = request.POST.get(f"min_{attr_id}") or None
                    max_val = request.POST.get(f"max_{attr_id}") or None
                    options = request.POST.get(f"options_{attr_id}") or None
                    default_value = request.POST.get(f"default_{attr_id}", "").strip()
                    rules_json = request.POST.get(f"rules_{attr_id}") or None
                    is_required = request.POST.get(f"required_{attr_id}") == "on"
                    is_used_in_name = request.POST.get(f"in_name_{attr_id}") == "on"
                    display_order = request.POST.get(f"order_{attr_id}") or 0

                    # Parse options if provided
                    if options:
                        try:
                            import json
                            options = json.loads(options)
                        except json.JSONDecodeError:
                            # Try comma-separated values
                            options = [o.strip() for o in options.split(",") if o.strip()]

                    # Parse conditional rules if provided
                    conditional_rules = None
                    if rules_json:
                        try:
                            import json
                            conditional_rules = json.loads(rules_json)
                        except json.JSONDecodeError:
                            pass

                    # Create or update CategoryAttribute
                    cat_attr, created = CategoryAttribute.objects.update_or_create(
                        category=category,
                        attribute=attribute,
                        defaults={
                            "attribute_type": attr_type,
                            "unit_id": unit_id if unit_id else None,
                            "min_value": min_val if min_val else None,
                            "max_value": max_val if max_val else None,
                            "options": options,
                            "default_value": default_value,
                            "conditional_rules": conditional_rules,
                            "is_required": is_required,
                            "is_used_in_name": is_used_in_name,
                            "display_order": int(display_order),
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as e:
                    errors.append(f"Error saving {attr_id}: {str(e)}")

            if created_count > 0 or updated_count > 0:
                msg_parts = []
                if created_count > 0:
                    msg_parts.append(f"added {created_count}")
                if updated_count > 0:
                    msg_parts.append(f"updated {updated_count}")
                messages.success(request, f"Successfully {' and '.join(msg_parts)} attributes.")
            if errors:
                for error in errors:
                    messages.error(request, error)

            return redirect("inventory:category_detail", pk=category.pk)

        return redirect(f"{request.path}?category={category.pk}")


# =============================================================================
# Item Variant Views
# =============================================================================


# =============================================================================
# Variant Case Views (Master Data)
# =============================================================================


class VariantCaseListView(LoginRequiredMixin, ListView):
    """List all variant cases (master data)."""

    model = VariantCase
    template_name = "inventory/variant_case_list.html"
    context_object_name = "cases"
    paginate_by = 50

    def get_queryset(self):
        return VariantCase.objects.all().order_by("display_order", "code")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Variant Cases"
        return context


class VariantCaseCreateView(LoginRequiredMixin, CreateView):
    """Create a new variant case."""

    model = VariantCase
    template_name = "inventory/variant_case_form.html"
    fields = ["code", "name", "condition", "acquisition", "reclaim_category", "ownership", "client_code", "description", "display_order", "is_active"]

    def form_valid(self, form):
        messages.success(self.request, f"Variant case '{form.instance.name}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:variant_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Variant Case"
        context["form_title"] = "Create New Variant Case"
        return context


class VariantCaseUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a variant case."""

    model = VariantCase
    template_name = "inventory/variant_case_form.html"
    fields = ["code", "name", "condition", "acquisition", "reclaim_category", "ownership", "client_code", "description", "display_order", "is_active"]

    def form_valid(self, form):
        messages.success(self.request, f"Variant case '{form.instance.name}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:variant_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        context["form_title"] = f"Edit Variant Case: {self.object.name}"
        return context


class VariantCaseDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a variant case."""

    model = VariantCase
    template_name = "inventory/variant_case_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("inventory:variant_list")

    def form_valid(self, form):
        messages.success(self.request, f"Variant case '{self.object.name}' deleted.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Delete Variant Case"
        return context


# =============================================================================
# Item Variant Views (Item-to-Case links)
# =============================================================================


class ItemVariantListView(LoginRequiredMixin, ListView):
    """List all item variants (item-to-case links)."""

    model = ItemVariant
    template_name = "inventory/item_variant_list.html"
    context_object_name = "variants"
    paginate_by = 50

    def get_queryset(self):
        queryset = ItemVariant.objects.select_related("base_item", "variant_case", "customer")

        # Search filter
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(base_item__name__icontains=search) |
                Q(variant_case__name__icontains=search)
            )

        return queryset.order_by("base_item__code", "variant_case__display_order")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Item Variants"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class StandaloneVariantCreateView(LoginRequiredMixin, CreateView):
    """Create variant from variants list (with base item and case selection)."""

    model = ItemVariant
    template_name = "inventory/standalone_variant_form.html"
    fields = ["base_item", "variant_case", "customer", "standard_cost", "last_cost", "legacy_mat_no", "erp_item_no", "is_active", "notes"]

    def form_valid(self, form):
        messages.success(self.request, f"Variant '{form.instance.code}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_variant_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Variant"
        context["form_title"] = "Create New Variant"
        context["items"] = InventoryItem.objects.filter(is_active=True).order_by("code")
        context["variant_cases"] = VariantCase.objects.filter(is_active=True).order_by("display_order")
        return context


class StandaloneVariantUpdateView(LoginRequiredMixin, UpdateView):
    """Edit variant from variants list."""

    model = ItemVariant
    template_name = "inventory/standalone_variant_form.html"
    fields = ["base_item", "variant_case", "customer", "standard_cost", "last_cost", "legacy_mat_no", "erp_item_no", "is_active", "notes"]

    def form_valid(self, form):
        messages.success(self.request, f"Variant '{form.instance.code}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_variant_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.code}"
        context["form_title"] = f"Edit Variant: {self.object.code}"
        context["items"] = InventoryItem.objects.filter(is_active=True).order_by("code")
        context["variant_cases"] = VariantCase.objects.filter(is_active=True).order_by("display_order")
        return context


class StandaloneVariantDeleteView(LoginRequiredMixin, DeleteView):
    """Delete variant from variants list."""

    model = ItemVariant
    template_name = "inventory/standalone_variant_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("inventory:item_variant_list")

    def form_valid(self, form):
        messages.success(self.request, f"Variant '{self.object.code}' deleted.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Delete Variant"
        return context


# =============================================================================
# Unit of Measure Views
# =============================================================================


class UnitOfMeasureListView(LoginRequiredMixin, ListView):
    """List all units of measure."""

    model = UnitOfMeasure
    template_name = "inventory/uom_list.html"
    context_object_name = "units"
    paginate_by = 50

    def get_queryset(self):
        queryset = UnitOfMeasure.objects.select_related("base_unit")

        # Search filter
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )

        # Type filter
        unit_type = self.request.GET.get("type")
        if unit_type:
            queryset = queryset.filter(unit_type=unit_type)

        return queryset.order_by("unit_type", "name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Units of Measure"
        context["search_query"] = self.request.GET.get("q", "")
        context["selected_type"] = self.request.GET.get("type", "")
        context["unit_types"] = UnitOfMeasure.UnitType.choices
        return context


class UnitOfMeasureCreateView(LoginRequiredMixin, CreateView):
    """Create a new unit of measure."""

    model = UnitOfMeasure
    template_name = "inventory/uom_form.html"
    fields = ["code", "name", "symbol", "unit_type", "base_unit", "conversion_factor", "description", "is_active"]

    def form_valid(self, form):
        messages.success(self.request, f"Unit '{form.instance.name}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:uom_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Unit"
        context["form_title"] = "Create Unit of Measure"
        return context


class UnitOfMeasureUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a unit of measure."""

    model = UnitOfMeasure
    template_name = "inventory/uom_form.html"
    fields = ["code", "name", "symbol", "unit_type", "base_unit", "conversion_factor", "description", "is_active"]

    def form_valid(self, form):
        messages.success(self.request, f"Unit '{form.instance.name}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:uom_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        context["form_title"] = f"Edit Unit: {self.object.name}"
        return context


class UnitOfMeasureDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a unit of measure."""

    model = UnitOfMeasure
    template_name = "inventory/uom_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("inventory:uom_list")

    def form_valid(self, form):
        messages.success(self.request, f"Unit '{self.object.name}' deleted.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Delete Unit"
        return context


# =============================================================================
# Item Variant Views (within item context)
# =============================================================================


class ItemVariantCreateView(LoginRequiredMixin, CreateView):
    """Create variant for a specific item (link to a VariantCase)."""

    model = ItemVariant
    template_name = "inventory/item_variant_form.html"
    fields = ["variant_case", "customer", "standard_cost", "last_cost", "legacy_mat_no", "erp_item_no", "is_active", "notes"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = f"Create Variant for {item.code}"
        context["form_title"] = f"Create Variant for {item.name}"
        context["variant_cases"] = VariantCase.objects.filter(is_active=True).order_by("display_order", "code")
        return context

    def form_valid(self, form):
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        form.instance.base_item = item
        # Auto-generate code if not provided
        if not form.instance.code:
            parts = [item.code, form.instance.variant_case.code]
            if form.instance.customer:
                parts.append(form.instance.customer.code[:6] if hasattr(form.instance.customer, 'code') else "CLI")
            form.instance.code = "-".join(parts)
        messages.success(self.request, f"Variant '{form.instance.code}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


class ItemVariantUpdateView(LoginRequiredMixin, UpdateView):
    """Update variant for a specific item."""

    model = ItemVariant
    template_name = "inventory/item_variant_form.html"
    fields = ["variant_case", "customer", "standard_cost", "last_cost", "legacy_mat_no", "erp_item_no", "is_active", "notes"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = f"Edit {self.object.code}"
        context["form_title"] = f"Edit Variant: {self.object.code}"
        context["variant_cases"] = VariantCase.objects.filter(is_active=True).order_by("display_order", "code")
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Variant '{form.instance.code}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


class ItemVariantDeleteView(LoginRequiredMixin, DeleteView):
    """Delete variant for a specific item."""

    model = ItemVariant
    template_name = "inventory/item_variant_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = "Delete Variant"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Variant '{self.object.code}' deleted.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


# =============================================================================
# Material Lot Views
# =============================================================================

from .models import MaterialLot


class MaterialLotListView(LoginRequiredMixin, ListView):
    """List all material lots."""

    model = MaterialLot
    template_name = "inventory/lot_list.html"
    context_object_name = "lots"
    paginate_by = 50

    def get_queryset(self):
        queryset = MaterialLot.objects.select_related("inventory_item", "vendor", "location")

        # Search filter
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(lot_number__icontains=search) |
                Q(inventory_item__name__icontains=search) |
                Q(inventory_item__code__icontains=search)
            )

        return queryset.order_by("-received_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Material Lots"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class MaterialLotCreateView(LoginRequiredMixin, CreateView):
    """Create a new material lot."""

    model = MaterialLot
    template_name = "inventory/lot_form.html"
    fields = ["inventory_item", "lot_number", "vendor", "location", "initial_quantity", "quantity_on_hand", "unit_cost", "received_date", "expiry_date", "cert_number"]

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Lot '{form.instance.lot_number}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:lot_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Lot"
        context["form_title"] = "Create Material Lot"
        return context


class MaterialLotDetailView(LoginRequiredMixin, DetailView):
    """View material lot details."""

    model = MaterialLot
    template_name = "inventory/lot_detail.html"
    context_object_name = "lot"

    def get_queryset(self):
        return MaterialLot.objects.select_related("inventory_item", "vendor", "location", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Lot {self.object.lot_number}"
        return context


class MaterialLotUpdateView(LoginRequiredMixin, UpdateView):
    """Update a material lot."""

    model = MaterialLot
    template_name = "inventory/lot_form.html"
    fields = ["inventory_item", "lot_number", "vendor", "location", "initial_quantity", "quantity_on_hand", "unit_cost", "received_date", "expiry_date", "cert_number", "status"]

    def form_valid(self, form):
        messages.success(self.request, f"Lot '{form.instance.lot_number}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:lot_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.lot_number}"
        context["form_title"] = f"Edit Lot: {self.object.lot_number}"
        return context


# =============================================================================
# Import/Export Views
# =============================================================================

from django.http import HttpResponse, JsonResponse
import csv


class ItemImportView(LoginRequiredMixin, View):
    """Import items from CSV."""

    template_name = "inventory/item_import.html"

    def get(self, request):
        from django.shortcuts import render
        return render(request, self.template_name, {"page_title": "Import Items"})

    def post(self, request):
        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            messages.error(request, "Please select a CSV file.")
            return redirect("inventory:item_import")

        try:
            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)

            created_count = 0
            for row in reader:
                if not row.get("code") or not row.get("name"):
                    continue

                item, created = InventoryItem.objects.get_or_create(
                    code=row["code"],
                    defaults={
                        "name": row.get("name", ""),
                        "description": row.get("description", ""),
                        "item_type": row.get("item_type", "COMPONENT"),
                        "unit": row.get("unit", "EA"),
                        "is_active": True,
                    }
                )
                if created:
                    created_count += 1

            messages.success(request, f"Import complete. {created_count} items created.")
        except Exception as e:
            messages.error(request, f"Import failed: {str(e)}")

        return redirect("inventory:item_list")


class ItemExportView(LoginRequiredMixin, View):
    """Export items to CSV."""

    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="inventory_items.csv"'

        writer = csv.writer(response)
        writer.writerow(["code", "name", "description", "item_type", "category", "unit", "standard_cost", "min_stock", "is_active"])

        items = InventoryItem.objects.select_related("category").all()
        for item in items:
            writer.writerow([
                item.code,
                item.name,
                item.description,
                item.item_type,
                item.category.name if item.category else "",
                item.unit,
                item.standard_cost,
                item.min_stock,
                item.is_active,
            ])

        return response


class ItemImportTemplateView(LoginRequiredMixin, View):
    """Download CSV template for item import."""

    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="item_import_template.csv"'

        writer = csv.writer(response)
        writer.writerow(["code", "name", "description", "item_type", "unit"])
        writer.writerow(["ITEM-001", "Sample Item", "Description here", "COMPONENT", "EA"])

        return response


# =============================================================================
# API Views
# =============================================================================


class CategoryAttributesAPIView(LoginRequiredMixin, View):
    """API to get attributes for a category."""

    def get(self, request, category_pk):
        category = get_object_or_404(InventoryCategory, pk=category_pk)
        attributes = category.category_attributes.select_related("attribute", "unit").order_by("display_order")

        data = []
        for attr in attributes:
            data.append({
                "id": attr.id,
                "code": attr.attribute.code if attr.attribute else "",
                "name": attr.attribute.name if attr.attribute else "",
                "attribute_type": attr.attribute_type,
                "unit": attr.unit.symbol if attr.unit else "",
                "is_required": attr.is_required,
                "is_used_in_name": attr.is_used_in_name,
                "min_value": str(attr.min_value) if attr.min_value else None,
                "max_value": str(attr.max_value) if attr.max_value else None,
                "options": attr.options,
            })

        return JsonResponse({
            "attributes": data,
            "name_template": category.name_template or "",
            "name_template_config": category.name_template_config or None
        })


class CategoryGenerateCodeAPIView(LoginRequiredMixin, View):
    """API to generate next item code for a category."""

    def get(self, request, category_pk):
        category = get_object_or_404(InventoryCategory, pk=category_pk)
        code = category.generate_next_code()
        return JsonResponse({"code": code})

    def post(self, request, category_pk):
        """Also handle POST for CSRF-protected requests."""
        return self.get(request, category_pk)


class ItemSearchAPIView(LoginRequiredMixin, View):
    """API to search for inventory items."""

    def get(self, request):
        query = request.GET.get("q", "").strip()
        if len(query) < 2:
            return JsonResponse({"items": []})

        items = InventoryItem.objects.filter(
            Q(code__icontains=query) | Q(name__icontains=query)
        ).filter(is_active=True)[:20]

        data = [{"id": item.pk, "code": item.code, "name": item.name} for item in items]
        return JsonResponse({"items": data})


class ItemRelationshipAPIView(LoginRequiredMixin, View):
    """API to manage item relationships."""

    def post(self, request):
        import json
        try:
            data = json.loads(request.body)
            from_item_id = data.get("from_item")
            to_item_id = data.get("to_item")
            status = data.get("status", "EQUAL")
            notes = data.get("notes", "")

            if not from_item_id or not to_item_id:
                return JsonResponse({"error": "Both from_item and to_item are required"}, status=400)

            if from_item_id == to_item_id:
                return JsonResponse({"error": "Cannot create relationship to self"}, status=400)

            from_item = get_object_or_404(InventoryItem, pk=from_item_id)
            to_item = get_object_or_404(InventoryItem, pk=to_item_id)

            # Check if relationship already exists
            if ItemRelationship.objects.filter(from_item=from_item, to_item=to_item).exists():
                return JsonResponse({"error": "Relationship already exists"}, status=400)

            # Create the relationship (bidirectional is handled in model.save())
            relationship = ItemRelationship.objects.create(
                from_item=from_item,
                to_item=to_item,
                status=status,
                notes=notes,
                created_by=request.user
            )

            return JsonResponse({
                "success": True,
                "id": relationship.pk,
                "message": f"Relationship created: {from_item.code} → {to_item.code}"
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def delete(self, request, pk):
        relationship = get_object_or_404(ItemRelationship, pk=pk)
        # Also delete the reverse relationship
        ItemRelationship.objects.filter(
            from_item=relationship.to_item,
            to_item=relationship.from_item
        ).delete()
        relationship.delete()
        return JsonResponse({"success": True})


# =============================================================================
# Item Planning Views (per-warehouse planning)
# =============================================================================


class ItemPlanningCreateView(LoginRequiredMixin, CreateView):
    """Create planning record for an item."""

    model = ItemPlanning
    form_class = ItemPlanningForm
    template_name = "inventory/item_planning_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = f"Add Planning for {item.code}"
        context["form_title"] = "Add Warehouse Planning"
        return context

    def form_valid(self, form):
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        form.instance.item = item
        messages.success(self.request, "Planning record added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


class ItemPlanningUpdateView(LoginRequiredMixin, UpdateView):
    """Update planning record."""

    model = ItemPlanning
    form_class = ItemPlanningForm
    template_name = "inventory/item_planning_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = f"Edit Planning for {item.code}"
        context["form_title"] = "Edit Warehouse Planning"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Planning record updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


class ItemPlanningDeleteView(LoginRequiredMixin, DeleteView):
    """Delete planning record."""

    model = ItemPlanning
    template_name = "inventory/item_planning_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = "Delete Planning"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Planning record deleted.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


# =============================================================================
# Item Supplier Views (multiple suppliers per item)
# =============================================================================


class ItemSupplierCreateView(LoginRequiredMixin, CreateView):
    """Add supplier to an item."""

    model = ItemSupplier
    form_class = ItemSupplierForm
    template_name = "inventory/item_supplier_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = f"Add Supplier for {item.code}"
        context["form_title"] = "Add Supplier"
        return context

    def form_valid(self, form):
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        form.instance.item = item
        messages.success(self.request, "Supplier added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


class ItemSupplierUpdateView(LoginRequiredMixin, UpdateView):
    """Update item supplier."""

    model = ItemSupplier
    form_class = ItemSupplierForm
    template_name = "inventory/item_supplier_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = f"Edit Supplier for {item.code}"
        context["form_title"] = "Edit Supplier"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Supplier updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


class ItemSupplierDeleteView(LoginRequiredMixin, DeleteView):
    """Delete item supplier."""

    model = ItemSupplier
    template_name = "inventory/item_supplier_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = "Delete Supplier"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Supplier removed.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


# =============================================================================
# Item Identifier Views (barcodes, QR codes, etc.)
# =============================================================================


class ItemIdentifierCreateView(LoginRequiredMixin, CreateView):
    """Add identifier to an item."""

    model = ItemIdentifier
    form_class = ItemIdentifierForm
    template_name = "inventory/item_identifier_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = f"Add Identifier for {item.code}"
        context["form_title"] = "Add Barcode/Identifier"
        return context

    def form_valid(self, form):
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        form.instance.item = item
        messages.success(self.request, "Identifier added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


class ItemIdentifierUpdateView(LoginRequiredMixin, UpdateView):
    """Update item identifier."""

    model = ItemIdentifier
    form_class = ItemIdentifierForm
    template_name = "inventory/item_identifier_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = f"Edit Identifier for {item.code}"
        context["form_title"] = "Edit Barcode/Identifier"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Identifier updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


class ItemIdentifierDeleteView(LoginRequiredMixin, DeleteView):
    """Delete item identifier."""

    model = ItemIdentifier
    template_name = "inventory/item_identifier_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = "Delete Identifier"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Identifier removed.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


# =============================================================================
# Item Bit Spec Views
# =============================================================================


class ItemBitSpecCreateView(LoginRequiredMixin, CreateView):
    """Add bit specification to an item."""

    model = ItemBitSpec
    form_class = ItemBitSpecForm
    template_name = "inventory/item_bit_spec_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = f"Add Bit Spec for {item.code}"
        context["form_title"] = "Bit Specifications"
        return context

    def form_valid(self, form):
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        form.instance.item = item
        messages.success(self.request, "Bit specifications added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


class ItemBitSpecUpdateView(LoginRequiredMixin, UpdateView):
    """Update bit specification."""

    model = ItemBitSpec
    form_class = ItemBitSpecForm
    template_name = "inventory/item_bit_spec_form.html"

    def get_object(self, queryset=None):
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        return get_object_or_404(ItemBitSpec, item=item)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = f"Edit Bit Spec for {item.code}"
        context["form_title"] = "Edit Bit Specifications"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Bit specifications updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


# =============================================================================
# Item Cutter Spec Views
# =============================================================================


class ItemCutterSpecCreateView(LoginRequiredMixin, CreateView):
    """Add cutter specification to an item."""

    model = ItemCutterSpec
    form_class = ItemCutterSpecForm
    template_name = "inventory/item_cutter_spec_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = f"Add Cutter Spec for {item.code}"
        context["form_title"] = "Cutter Specifications"
        return context

    def form_valid(self, form):
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        form.instance.item = item
        messages.success(self.request, "Cutter specifications added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


class ItemCutterSpecUpdateView(LoginRequiredMixin, UpdateView):
    """Update cutter specification."""

    model = ItemCutterSpec
    form_class = ItemCutterSpecForm
    template_name = "inventory/item_cutter_spec_form.html"

    def get_object(self, queryset=None):
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        return get_object_or_404(ItemCutterSpec, item=item)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(InventoryItem, pk=self.kwargs["item_pk"])
        context["item"] = item
        context["page_title"] = f"Edit Cutter Spec for {item.code}"
        context["form_title"] = "Edit Cutter Specifications"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Cutter specifications updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.kwargs["item_pk"]})


# =============================================================================
# PHASE 2: LEDGER VIEWS (Read-Only)
# =============================================================================

from .models import (
    StockLedger,
    StockBalance,
    GoodsReceiptNote,
    GRNLine,
    StockIssue,
    StockIssueLine,
    StockTransfer,
    StockTransferLine,
    StockAdjustment as StockAdjustmentDoc,
    StockAdjustmentLine,
    Asset,
    AssetMovement,
    QualityStatusChange,
    StockReservation,
    BillOfMaterial,
    BOMLine,
    CycleCountPlan,
    CycleCountSession,
    CycleCountLine,
    Party,
    ConditionType,
    QualityStatus,
    AdjustmentReason,
    OwnershipType,
)

from .forms import (
    GoodsReceiptNoteForm,
    GRNLineFormSet,
    StockIssueForm,
    StockIssueLineFormSet,
    StockTransferForm,
    StockTransferLineFormSet,
    StockAdjustmentDocForm,
    StockAdjustmentLineFormSet,
    AssetForm,
    AssetMovementForm,
    QualityStatusChangeForm,
    StockReservationForm,
    BillOfMaterialForm,
    BOMLineFormSet,
    CycleCountPlanForm,
    CycleCountSessionForm,
    CycleCountLineFormSet,
)


class StockLedgerListView(LoginRequiredMixin, ListView):
    """View stock ledger entries (immutable audit trail)."""

    model = StockLedger
    template_name = "inventory/ledger/stock_ledger_list.html"
    context_object_name = "entries"
    paginate_by = 50

    def get_queryset(self):
        qs = StockLedger.objects.select_related(
            "item", "location", "lot", "owner_party", "quality_status"
        ).order_by("-transaction_date", "-entry_number")

        # Filters
        item = self.request.GET.get("item")
        if item:
            qs = qs.filter(item_id=item)

        location = self.request.GET.get("location")
        if location:
            qs = qs.filter(location_id=location)

        trans_type = self.request.GET.get("type")
        if trans_type:
            qs = qs.filter(transaction_type=trans_type)

        date_from = self.request.GET.get("date_from")
        if date_from:
            qs = qs.filter(transaction_date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            qs = qs.filter(transaction_date__lte=date_to)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Stock Ledger"
        context["items"] = InventoryItem.objects.filter(is_active=True)
        context["locations"] = InventoryLocation.objects.filter(is_active=True)
        context["transaction_types"] = StockLedger.TransactionType.choices
        return context


class StockBalanceListView(LoginRequiredMixin, ListView):
    """View current stock balances (materialized view)."""

    model = StockBalance
    template_name = "inventory/ledger/stock_balance_list.html"
    context_object_name = "balances"
    paginate_by = 50

    def get_queryset(self):
        qs = StockBalance.objects.select_related(
            "item", "location", "lot", "owner_party", "quality_status", "condition", "ownership_type"
        ).filter(qty_on_hand__gt=0).order_by("item__code", "location__code")

        # Filters
        item = self.request.GET.get("item")
        if item:
            qs = qs.filter(item_id=item)

        location = self.request.GET.get("location")
        if location:
            qs = qs.filter(location_id=location)

        owner = self.request.GET.get("owner")
        if owner:
            qs = qs.filter(owner_party_id=owner)

        quality = self.request.GET.get("quality")
        if quality:
            qs = qs.filter(quality_status_id=quality)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Stock Balances"
        context["items"] = InventoryItem.objects.filter(is_active=True)
        context["locations"] = InventoryLocation.objects.filter(is_active=True)
        context["parties"] = Party.objects.filter(is_active=True, can_own_stock=True)
        context["quality_statuses"] = QualityStatus.objects.filter(is_active=True)
        return context


# =============================================================================
# PHASE 3: DOCUMENT VIEWS (GRN, Issues, Transfers, Adjustments)
# =============================================================================


class GRNListView(LoginRequiredMixin, ListView):
    """List all Goods Receipt Notes."""

    model = GoodsReceiptNote
    template_name = "inventory/documents/grn_list.html"
    context_object_name = "grns"
    paginate_by = 25

    def get_queryset(self):
        qs = GoodsReceiptNote.objects.select_related(
            "warehouse", "supplier", "owner_party", "created_by"
        ).order_by("-receipt_date", "-grn_number")

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        warehouse = self.request.GET.get("warehouse")
        if warehouse:
            qs = qs.filter(warehouse_id=warehouse)

        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(
                Q(grn_number__icontains=search) | Q(source_reference__icontains=search)
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Goods Receipt Notes"
        context["status_choices"] = GoodsReceiptNote.Status.choices
        from apps.sales.models import Warehouse
        context["warehouses"] = Warehouse.objects.filter(is_active=True)
        return context


class GRNCreateView(LoginRequiredMixin, CreateView):
    """Create a new Goods Receipt Note with lines."""

    model = GoodsReceiptNote
    form_class = GoodsReceiptNoteForm
    template_name = "inventory/documents/grn_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Goods Receipt"
        context["form_title"] = "Create Goods Receipt Note"
        if self.request.POST:
            context["lines_formset"] = GRNLineFormSet(self.request.POST, instance=self.object)
        else:
            context["lines_formset"] = GRNLineFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context["lines_formset"]

        form.instance.created_by = self.request.user
        self.object = form.save()

        if lines_formset.is_valid():
            lines_formset.instance = self.object
            lines_formset.save()
            messages.success(self.request, f"GRN {self.object.grn_number} created successfully.")
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("inventory:grn_detail", kwargs={"pk": self.object.pk})


class GRNDetailView(LoginRequiredMixin, DetailView):
    """View GRN details with lines."""

    model = GoodsReceiptNote
    template_name = "inventory/documents/grn_detail.html"
    context_object_name = "grn"

    def get_queryset(self):
        return GoodsReceiptNote.objects.select_related(
            "warehouse", "supplier", "owner_party", "ownership_type", "created_by"
        ).prefetch_related("lines__item", "lines__location", "lines__lot")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"GRN {self.object.grn_number}"
        context["lines"] = self.object.lines.all()
        return context


class GRNUpdateView(LoginRequiredMixin, UpdateView):
    """Update GRN (only if DRAFT)."""

    model = GoodsReceiptNote
    form_class = GoodsReceiptNoteForm
    template_name = "inventory/documents/grn_form.html"

    def get_queryset(self):
        return GoodsReceiptNote.objects.filter(status="DRAFT")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.grn_number}"
        context["form_title"] = "Edit Goods Receipt Note"
        if self.request.POST:
            context["lines_formset"] = GRNLineFormSet(self.request.POST, instance=self.object)
        else:
            context["lines_formset"] = GRNLineFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context["lines_formset"]

        self.object = form.save()

        if lines_formset.is_valid():
            lines_formset.save()
            messages.success(self.request, f"GRN {self.object.grn_number} updated successfully.")
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("inventory:grn_detail", kwargs={"pk": self.object.pk})


class GRNPostView(LoginRequiredMixin, View):
    """Post a GRN to create ledger entries."""

    def post(self, request, pk):
        grn = get_object_or_404(GoodsReceiptNote, pk=pk)

        if grn.status != "DRAFT":
            messages.error(request, "Only DRAFT GRNs can be posted.")
            return redirect("inventory:grn_detail", pk=pk)

        try:
            # Post each line
            for line in grn.lines.filter(is_posted=False):
                # Create ledger entry for each line
                StockLedger.objects.create(
                    transaction_type="RECEIPT",
                    transaction_date=grn.receipt_date,
                    item=line.item,
                    location=line.location,
                    lot=line.lot,
                    qty_delta=line.qty_received,
                    unit_cost=line.unit_cost,
                    total_cost=line.total_cost,
                    owner_party=grn.owner_party,
                    ownership_type=grn.ownership_type,
                    condition=line.condition,
                    quality_status=line.quality_status,
                    reference_type="GRN",
                    reference_id=str(grn.pk),
                    created_by=request.user,
                )
                line.is_posted = True
                line.posted_at = timezone.now()
                line.save()

            # Update GRN status
            grn.status = "POSTED"
            grn.posted_date = timezone.now()
            grn.posted_by = request.user
            grn.save()

            messages.success(request, f"GRN {grn.grn_number} posted successfully.")
        except Exception as e:
            messages.error(request, f"Error posting GRN: {str(e)}")

        return redirect("inventory:grn_detail", pk=pk)


# Stock Issue Views
class StockIssueListView(LoginRequiredMixin, ListView):
    """List all Stock Issues."""

    model = StockIssue
    template_name = "inventory/documents/issue_list.html"
    context_object_name = "issues"
    paginate_by = 25

    def get_queryset(self):
        qs = StockIssue.objects.select_related(
            "warehouse", "issued_to_party", "created_by"
        ).order_by("-issue_date", "-issue_number")

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Stock Issues"
        context["status_choices"] = StockIssue.Status.choices
        return context


class StockIssueCreateView(LoginRequiredMixin, CreateView):
    """Create a new Stock Issue."""

    model = StockIssue
    form_class = StockIssueForm
    template_name = "inventory/documents/issue_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Stock Issue"
        context["form_title"] = "Create Stock Issue"
        if self.request.POST:
            context["lines_formset"] = StockIssueLineFormSet(self.request.POST, instance=self.object)
        else:
            context["lines_formset"] = StockIssueLineFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context["lines_formset"]

        form.instance.created_by = self.request.user
        self.object = form.save()

        if lines_formset.is_valid():
            lines_formset.instance = self.object
            lines_formset.save()
            messages.success(self.request, f"Issue {self.object.issue_number} created.")
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("inventory:issue_detail", kwargs={"pk": self.object.pk})


class StockIssueDetailView(LoginRequiredMixin, DetailView):
    """View Stock Issue details."""

    model = StockIssue
    template_name = "inventory/documents/issue_detail.html"
    context_object_name = "issue"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Issue {self.object.issue_number}"
        context["lines"] = self.object.lines.select_related("item", "from_location", "lot")
        return context


class StockIssuePostView(LoginRequiredMixin, View):
    """Post a Stock Issue to create ledger entries."""

    def post(self, request, pk):
        issue = get_object_or_404(StockIssue, pk=pk)

        if issue.status != "DRAFT":
            messages.error(request, "Only DRAFT issues can be posted.")
            return redirect("inventory:issue_detail", pk=pk)

        try:
            for line in issue.lines.filter(is_posted=False):
                StockLedger.objects.create(
                    transaction_type="ISSUE",
                    transaction_date=issue.issue_date,
                    item=line.item,
                    location=line.from_location,
                    lot=line.lot,
                    qty_delta=-line.qty_issued,  # Negative for issue
                    unit_cost=line.unit_cost,
                    total_cost=line.total_cost,
                    reference_type="ISSUE",
                    reference_id=str(issue.pk),
                    created_by=request.user,
                )
                line.is_posted = True
                line.posted_at = timezone.now()
                line.save()

            issue.status = "POSTED"
            issue.posted_date = timezone.now()
            issue.posted_by = request.user
            issue.save()

            messages.success(request, f"Issue {issue.issue_number} posted.")
        except Exception as e:
            messages.error(request, f"Error posting issue: {str(e)}")

        return redirect("inventory:issue_detail", pk=pk)


# Stock Transfer Views
class StockTransferListView(LoginRequiredMixin, ListView):
    """List all Stock Transfers."""

    model = StockTransfer
    template_name = "inventory/documents/transfer_list.html"
    context_object_name = "transfers"
    paginate_by = 25

    def get_queryset(self):
        return StockTransfer.objects.select_related(
            "from_warehouse", "to_warehouse", "created_by"
        ).order_by("-transfer_date", "-transfer_number")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Stock Transfers"
        context["status_choices"] = StockTransfer.Status.choices
        return context


class StockTransferCreateView(LoginRequiredMixin, CreateView):
    """Create a new Stock Transfer."""

    model = StockTransfer
    form_class = StockTransferForm
    template_name = "inventory/documents/transfer_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Stock Transfer"
        context["form_title"] = "Create Stock Transfer"
        if self.request.POST:
            context["lines_formset"] = StockTransferLineFormSet(self.request.POST, instance=self.object)
        else:
            context["lines_formset"] = StockTransferLineFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context["lines_formset"]

        form.instance.created_by = self.request.user
        self.object = form.save()

        if lines_formset.is_valid():
            lines_formset.instance = self.object
            lines_formset.save()
            messages.success(self.request, f"Transfer {self.object.transfer_number} created.")
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("inventory:transfer_detail", kwargs={"pk": self.object.pk})


class StockTransferDetailView(LoginRequiredMixin, DetailView):
    """View Stock Transfer details."""

    model = StockTransfer
    template_name = "inventory/documents/transfer_detail.html"
    context_object_name = "transfer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Transfer {self.object.transfer_number}"
        context["lines"] = self.object.lines.select_related("item", "from_location", "to_location", "lot")
        return context


class StockTransferPostView(LoginRequiredMixin, View):
    """Post a Stock Transfer to create ledger entries."""

    def post(self, request, pk):
        transfer = get_object_or_404(StockTransfer, pk=pk)

        if transfer.status != "DRAFT":
            messages.error(request, "Only DRAFT transfers can be posted.")
            return redirect("inventory:transfer_detail", pk=pk)

        try:
            for line in transfer.lines.filter(is_posted=False):
                # Create OUT entry (from location)
                StockLedger.objects.create(
                    transaction_type="TRANSFER_OUT",
                    transaction_date=transfer.transfer_date,
                    item=line.item,
                    location=line.from_location,
                    lot=line.lot,
                    qty_delta=-line.qty_transferred,
                    reference_type="TRANSFER",
                    reference_id=str(transfer.pk),
                    created_by=request.user,
                )
                # Create IN entry (to location)
                StockLedger.objects.create(
                    transaction_type="TRANSFER_IN",
                    transaction_date=transfer.transfer_date,
                    item=line.item,
                    location=line.to_location,
                    lot=line.lot,
                    qty_delta=line.qty_transferred,
                    reference_type="TRANSFER",
                    reference_id=str(transfer.pk),
                    created_by=request.user,
                )
                line.is_posted = True
                line.posted_at = timezone.now()
                line.save()

            transfer.status = "POSTED"
            transfer.posted_date = timezone.now()
            transfer.posted_by = request.user
            transfer.save()

            messages.success(request, f"Transfer {transfer.transfer_number} posted.")
        except Exception as e:
            messages.error(request, f"Error posting transfer: {str(e)}")

        return redirect("inventory:transfer_detail", pk=pk)


# Stock Adjustment Document Views
class StockAdjustmentDocListView(LoginRequiredMixin, ListView):
    """List all Stock Adjustment documents."""

    model = StockAdjustmentDoc
    template_name = "inventory/documents/adjustment_list.html"
    context_object_name = "adjustments"
    paginate_by = 25

    def get_queryset(self):
        return StockAdjustmentDoc.objects.select_related(
            "warehouse", "reason", "created_by"
        ).order_by("-adjustment_date", "-adjustment_number")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Stock Adjustments"
        context["status_choices"] = StockAdjustmentDoc.Status.choices
        return context


class StockAdjustmentDocCreateView(LoginRequiredMixin, CreateView):
    """Create a new Stock Adjustment document."""

    model = StockAdjustmentDoc
    form_class = StockAdjustmentDocForm
    template_name = "inventory/documents/adjustment_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Stock Adjustment"
        context["form_title"] = "Create Stock Adjustment"
        if self.request.POST:
            context["lines_formset"] = StockAdjustmentLineFormSet(self.request.POST, instance=self.object)
        else:
            context["lines_formset"] = StockAdjustmentLineFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context["lines_formset"]

        form.instance.created_by = self.request.user
        self.object = form.save()

        if lines_formset.is_valid():
            lines_formset.instance = self.object
            lines_formset.save()
            messages.success(self.request, f"Adjustment {self.object.adjustment_number} created.")
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("inventory:adjustment_detail", kwargs={"pk": self.object.pk})


class StockAdjustmentDocDetailView(LoginRequiredMixin, DetailView):
    """View Stock Adjustment details."""

    model = StockAdjustmentDoc
    template_name = "inventory/documents/adjustment_detail.html"
    context_object_name = "adjustment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Adjustment {self.object.adjustment_number}"
        context["lines"] = self.object.lines.select_related("item", "location", "lot")
        return context


class StockAdjustmentDocPostView(LoginRequiredMixin, View):
    """Post a Stock Adjustment to create ledger entries."""

    def post(self, request, pk):
        adjustment = get_object_or_404(StockAdjustmentDoc, pk=pk)

        if adjustment.status != "DRAFT":
            messages.error(request, "Only DRAFT adjustments can be posted.")
            return redirect("inventory:adjustment_detail", pk=pk)

        try:
            for line in adjustment.lines.filter(is_posted=False):
                # qty_adjustment = qty_actual - qty_system
                StockLedger.objects.create(
                    transaction_type="ADJUSTMENT",
                    transaction_date=adjustment.adjustment_date,
                    item=line.item,
                    location=line.location,
                    lot=line.lot,
                    qty_delta=line.qty_adjustment,
                    unit_cost=line.unit_cost,
                    total_cost=line.total_cost,
                    reference_type="ADJUSTMENT",
                    reference_id=str(adjustment.pk),
                    created_by=request.user,
                )
                line.is_posted = True
                line.posted_at = timezone.now()
                line.save()

            adjustment.status = "POSTED"
            adjustment.posted_date = timezone.now()
            adjustment.posted_by = request.user
            adjustment.save()

            messages.success(request, f"Adjustment {adjustment.adjustment_number} posted.")
        except Exception as e:
            messages.error(request, f"Error posting adjustment: {str(e)}")

        return redirect("inventory:adjustment_detail", pk=pk)


# =============================================================================
# PHASE 4: ASSET VIEWS
# =============================================================================


class AssetListView(LoginRequiredMixin, ListView):
    """List all Assets."""

    model = Asset
    template_name = "inventory/assets/asset_list.html"
    context_object_name = "assets"
    paginate_by = 25

    def get_queryset(self):
        qs = Asset.objects.select_related(
            "item", "condition", "quality_status", "current_location", "warehouse", "owner_party"
        ).order_by("-created_at")

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        warehouse = self.request.GET.get("warehouse")
        if warehouse:
            qs = qs.filter(warehouse_id=warehouse)

        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(
                Q(serial_number__icontains=search) |
                Q(asset_tag__icontains=search) |
                Q(item__code__icontains=search)
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Asset Register"
        context["status_choices"] = Asset.Status.choices
        from apps.sales.models import Warehouse
        context["warehouses"] = Warehouse.objects.filter(is_active=True)
        return context


class AssetCreateView(LoginRequiredMixin, CreateView):
    """Create a new Asset."""

    model = Asset
    form_class = AssetForm
    template_name = "inventory/assets/asset_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Asset {form.instance.serial_number} created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:asset_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Asset"
        context["form_title"] = "Create Asset"
        return context


class AssetDetailView(LoginRequiredMixin, DetailView):
    """View Asset details with movement history."""

    model = Asset
    template_name = "inventory/assets/asset_detail.html"
    context_object_name = "asset"

    def get_queryset(self):
        return Asset.objects.select_related(
            "item", "condition", "quality_status", "current_location",
            "warehouse", "owner_party", "ownership_type", "custodian_party"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Asset {self.object.serial_number}"
        context["movements"] = self.object.movements.select_related(
            "from_location", "to_location", "created_by"
        ).order_by("-movement_date")[:20]
        return context


class AssetUpdateView(LoginRequiredMixin, UpdateView):
    """Update Asset."""

    model = Asset
    form_class = AssetForm
    template_name = "inventory/assets/asset_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Asset {form.instance.serial_number} updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:asset_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.serial_number}"
        context["form_title"] = "Edit Asset"
        return context


class AssetMovementCreateView(LoginRequiredMixin, CreateView):
    """Record an asset movement."""

    model = AssetMovement
    form_class = AssetMovementForm
    template_name = "inventory/assets/movement_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = get_object_or_404(Asset, pk=self.kwargs["asset_pk"])
        context["asset"] = asset
        context["page_title"] = f"Move Asset {asset.serial_number}"
        context["form_title"] = "Record Asset Movement"
        return context

    def form_valid(self, form):
        asset = get_object_or_404(Asset, pk=self.kwargs["asset_pk"])
        form.instance.asset = asset
        form.instance.created_by = self.request.user

        # Update asset location if movement is location-based
        if form.instance.to_location:
            asset.current_location = form.instance.to_location
        if form.instance.to_status:
            asset.status = form.instance.to_status
        asset.save()

        messages.success(self.request, "Asset movement recorded.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:asset_detail", kwargs={"pk": self.kwargs["asset_pk"]})


# =============================================================================
# PHASE 5: QC GATES VIEWS
# =============================================================================


class QualityStatusChangeListView(LoginRequiredMixin, ListView):
    """List QC status changes."""

    model = QualityStatusChange
    template_name = "inventory/qc/qc_change_list.html"
    context_object_name = "changes"
    paginate_by = 25

    def get_queryset(self):
        return QualityStatusChange.objects.select_related(
            "lot", "asset", "from_status", "to_status", "changed_by"
        ).order_by("-change_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "QC Status Changes"
        return context


class QualityStatusChangeCreateView(LoginRequiredMixin, CreateView):
    """Record a QC status change."""

    model = QualityStatusChange
    form_class = QualityStatusChangeForm
    template_name = "inventory/qc/qc_change_form.html"

    def form_valid(self, form):
        form.instance.changed_by = self.request.user

        # Update the lot or asset's quality status
        if form.instance.lot:
            form.instance.lot.quality_status = form.instance.to_status
            form.instance.lot.save()
        elif form.instance.asset:
            form.instance.asset.quality_status = form.instance.to_status
            form.instance.asset.save()

        messages.success(self.request, "QC status change recorded.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:qc_change_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New QC Status Change"
        context["form_title"] = "Record QC Status Change"
        return context


# =============================================================================
# PHASE 6: RESERVATION VIEWS
# =============================================================================


class StockReservationListView(LoginRequiredMixin, ListView):
    """List stock reservations."""

    model = StockReservation
    template_name = "inventory/reservations/reservation_list.html"
    context_object_name = "reservations"
    paginate_by = 25

    def get_queryset(self):
        qs = StockReservation.objects.select_related(
            "item", "lot", "location", "created_by"
        ).order_by("-created_at")

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Stock Reservations"
        context["status_choices"] = StockReservation.Status.choices
        return context


class StockReservationCreateView(LoginRequiredMixin, CreateView):
    """Create a stock reservation."""

    model = StockReservation
    form_class = StockReservationForm
    template_name = "inventory/reservations/reservation_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Reservation {form.instance.reservation_number} created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:reservation_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Reservation"
        context["form_title"] = "Create Stock Reservation"
        return context


class StockReservationCancelView(LoginRequiredMixin, View):
    """Cancel a stock reservation."""

    def post(self, request, pk):
        reservation = get_object_or_404(StockReservation, pk=pk)

        if reservation.status not in ["PENDING", "CONFIRMED"]:
            messages.error(request, "Only PENDING or CONFIRMED reservations can be cancelled.")
            return redirect("inventory:reservation_list")

        reservation.status = "CANCELLED"
        reservation.save()
        messages.success(request, f"Reservation {reservation.reservation_number} cancelled.")

        return redirect("inventory:reservation_list")


# =============================================================================
# PHASE 7: BOM VIEWS
# =============================================================================


class BOMListView(LoginRequiredMixin, ListView):
    """List all BOMs."""

    model = BillOfMaterial
    template_name = "inventory/bom/bom_list.html"
    context_object_name = "boms"
    paginate_by = 25

    def get_queryset(self):
        qs = BillOfMaterial.objects.select_related(
            "parent_item", "created_by"
        ).order_by("-created_at")

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(
                Q(bom_code__icontains=search) |
                Q(name__icontains=search) |
                Q(parent_item__code__icontains=search)
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Bills of Material"
        context["status_choices"] = BillOfMaterial.Status.choices
        return context


class BOMCreateView(LoginRequiredMixin, CreateView):
    """Create a new BOM."""

    model = BillOfMaterial
    form_class = BillOfMaterialForm
    template_name = "inventory/bom/bom_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New BOM"
        context["form_title"] = "Create Bill of Material"
        if self.request.POST:
            context["lines_formset"] = BOMLineFormSet(self.request.POST, instance=self.object)
        else:
            context["lines_formset"] = BOMLineFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context["lines_formset"]

        form.instance.created_by = self.request.user
        self.object = form.save()

        if lines_formset.is_valid():
            lines_formset.instance = self.object
            lines_formset.save()
            self.object.recalculate_costs()
            messages.success(self.request, f"BOM {self.object.bom_code} created.")
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("inventory:bom_detail", kwargs={"pk": self.object.pk})


class BOMDetailView(LoginRequiredMixin, DetailView):
    """View BOM details with components."""

    model = BillOfMaterial
    template_name = "inventory/bom/bom_detail.html"
    context_object_name = "bom"

    def get_queryset(self):
        return BillOfMaterial.objects.select_related("parent_item", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"BOM {self.object.bom_code}"
        context["lines"] = self.object.lines.select_related("component_item", "uom").order_by("line_number")
        return context


class BOMUpdateView(LoginRequiredMixin, UpdateView):
    """Update a BOM."""

    model = BillOfMaterial
    form_class = BillOfMaterialForm
    template_name = "inventory/bom/bom_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.bom_code}"
        context["form_title"] = "Edit Bill of Material"
        if self.request.POST:
            context["lines_formset"] = BOMLineFormSet(self.request.POST, instance=self.object)
        else:
            context["lines_formset"] = BOMLineFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context["lines_formset"]

        self.object = form.save()

        if lines_formset.is_valid():
            lines_formset.save()
            self.object.recalculate_costs()
            messages.success(self.request, f"BOM {self.object.bom_code} updated.")
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("inventory:bom_detail", kwargs={"pk": self.object.pk})


class BOMRecalculateView(LoginRequiredMixin, View):
    """Recalculate BOM costs."""

    def post(self, request, pk):
        bom = get_object_or_404(BillOfMaterial, pk=pk)
        bom.recalculate_costs()
        messages.success(request, f"BOM {bom.bom_code} costs recalculated.")
        return redirect("inventory:bom_detail", pk=pk)


# =============================================================================
# PHASE 8: CYCLE COUNT VIEWS
# =============================================================================


class CycleCountPlanListView(LoginRequiredMixin, ListView):
    """List cycle count plans."""

    model = CycleCountPlan
    template_name = "inventory/cyclecount/plan_list.html"
    context_object_name = "plans"
    paginate_by = 25

    def get_queryset(self):
        return CycleCountPlan.objects.select_related(
            "warehouse", "created_by"
        ).order_by("-start_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Cycle Count Plans"
        context["status_choices"] = CycleCountPlan.Status.choices
        return context


class CycleCountPlanCreateView(LoginRequiredMixin, CreateView):
    """Create a cycle count plan."""

    model = CycleCountPlan
    form_class = CycleCountPlanForm
    template_name = "inventory/cyclecount/plan_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Cycle count plan {form.instance.plan_code} created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:cyclecount_plan_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Cycle Count Plan"
        context["form_title"] = "Create Cycle Count Plan"
        return context


class CycleCountSessionListView(LoginRequiredMixin, ListView):
    """List cycle count sessions."""

    model = CycleCountSession
    template_name = "inventory/cyclecount/session_list.html"
    context_object_name = "sessions"
    paginate_by = 25

    def get_queryset(self):
        return CycleCountSession.objects.select_related(
            "plan", "warehouse", "location", "counted_by"
        ).order_by("-session_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Cycle Count Sessions"
        context["status_choices"] = CycleCountSession.Status.choices
        return context


class CycleCountSessionCreateView(LoginRequiredMixin, CreateView):
    """Create a cycle count session."""

    model = CycleCountSession
    form_class = CycleCountSessionForm
    template_name = "inventory/cyclecount/session_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Count Session"
        context["form_title"] = "Create Cycle Count Session"
        if self.request.POST:
            context["lines_formset"] = CycleCountLineFormSet(self.request.POST, instance=self.object)
        else:
            context["lines_formset"] = CycleCountLineFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        lines_formset = context["lines_formset"]

        form.instance.counted_by = self.request.user
        self.object = form.save()

        if lines_formset.is_valid():
            lines_formset.instance = self.object
            lines_formset.save()
            messages.success(self.request, f"Session {self.object.session_number} created.")
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy("inventory:cyclecount_session_detail", kwargs={"pk": self.object.pk})


class CycleCountSessionDetailView(LoginRequiredMixin, DetailView):
    """View cycle count session with lines."""

    model = CycleCountSession
    template_name = "inventory/cyclecount/session_detail.html"
    context_object_name = "session"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Session {self.object.session_number}"
        context["lines"] = self.object.lines.select_related("item", "lot", "location", "counted_by")
        return context


class CycleCountSessionFinalizeView(LoginRequiredMixin, View):
    """Finalize a cycle count session and create adjustments."""

    def post(self, request, pk):
        session = get_object_or_404(CycleCountSession, pk=pk)

        if session.status != "IN_PROGRESS":
            messages.error(request, "Only IN_PROGRESS sessions can be finalized.")
            return redirect("inventory:cyclecount_session_detail", pk=pk)

        # Calculate totals
        lines = session.lines.all()
        session.total_items = lines.count()
        session.items_counted = lines.exclude(qty_counted__isnull=True).count()
        session.items_variance = lines.exclude(qty_variance=0).count()
        session.total_variance_value = sum(line.variance_value or 0 for line in lines)

        session.status = "COMPLETED"
        session.save()

        messages.success(request, f"Session {session.session_number} finalized.")
        return redirect("inventory:cyclecount_session_detail", pk=pk)


# =============================================================================
# Reference Data Views
# =============================================================================


class PartyListView(LoginRequiredMixin, ListView):
    """List all parties (customers, suppliers, owners)."""

    model = Party
    template_name = "inventory/refdata/party_list.html"
    context_object_name = "parties"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Parties"
        return context


class PartyCreateView(LoginRequiredMixin, CreateView):
    """Create a new party."""

    model = Party
    form_class = PartyForm
    template_name = "inventory/refdata/party_form.html"
    success_url = reverse_lazy("inventory:party_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Party"
        context["form_title"] = "Create Party"
        return context


class PartyUpdateView(LoginRequiredMixin, UpdateView):
    """Update a party."""

    model = Party
    form_class = PartyForm
    template_name = "inventory/refdata/party_form.html"
    success_url = reverse_lazy("inventory:party_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Edit Party"
        context["form_title"] = f"Edit {self.object.name}"
        return context


class ConditionTypeListView(LoginRequiredMixin, ListView):
    """List all condition types."""

    model = ConditionType
    template_name = "inventory/refdata/condition_list.html"
    context_object_name = "conditions"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Condition Types"
        return context


class ConditionTypeCreateView(LoginRequiredMixin, CreateView):
    """Create a new condition type."""

    model = ConditionType
    form_class = ConditionTypeForm
    template_name = "inventory/refdata/condition_form.html"
    success_url = reverse_lazy("inventory:condition_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Condition Type"
        context["form_title"] = "Create Condition Type"
        return context


class ConditionTypeUpdateView(LoginRequiredMixin, UpdateView):
    """Update a condition type."""

    model = ConditionType
    form_class = ConditionTypeForm
    template_name = "inventory/refdata/condition_form.html"
    success_url = reverse_lazy("inventory:condition_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Edit Condition Type"
        context["form_title"] = f"Edit {self.object.name}"
        return context


class QualityStatusListView(LoginRequiredMixin, ListView):
    """List all quality statuses."""

    model = QualityStatus
    template_name = "inventory/refdata/quality_status_list.html"
    context_object_name = "statuses"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Quality Statuses"
        return context


class QualityStatusCreateView(LoginRequiredMixin, CreateView):
    """Create a new quality status."""

    model = QualityStatus
    form_class = QualityStatusForm
    template_name = "inventory/refdata/quality_status_form.html"
    success_url = reverse_lazy("inventory:quality_status_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Quality Status"
        context["form_title"] = "Create Quality Status"
        return context


class QualityStatusUpdateView(LoginRequiredMixin, UpdateView):
    """Update a quality status."""

    model = QualityStatus
    form_class = QualityStatusForm
    template_name = "inventory/refdata/quality_status_form.html"
    success_url = reverse_lazy("inventory:quality_status_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Edit Quality Status"
        context["form_title"] = f"Edit {self.object.name}"
        return context


class AdjustmentReasonListView(LoginRequiredMixin, ListView):
    """List all adjustment reasons."""

    model = AdjustmentReason
    template_name = "inventory/refdata/adjustment_reason_list.html"
    context_object_name = "reasons"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Adjustment Reasons"
        return context


class AdjustmentReasonCreateView(LoginRequiredMixin, CreateView):
    """Create a new adjustment reason."""

    model = AdjustmentReason
    form_class = AdjustmentReasonForm
    template_name = "inventory/refdata/adjustment_reason_form.html"
    success_url = reverse_lazy("inventory:adjustment_reason_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Adjustment Reason"
        context["form_title"] = "Create Adjustment Reason"
        return context


class AdjustmentReasonUpdateView(LoginRequiredMixin, UpdateView):
    """Update an adjustment reason."""

    model = AdjustmentReason
    form_class = AdjustmentReasonForm
    template_name = "inventory/refdata/adjustment_reason_form.html"
    success_url = reverse_lazy("inventory:adjustment_reason_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Edit Adjustment Reason"
        context["form_title"] = f"Edit {self.object.name}"
        return context


class OwnershipTypeListView(LoginRequiredMixin, ListView):
    """List all ownership types."""

    model = OwnershipType
    template_name = "inventory/refdata/ownership_type_list.html"
    context_object_name = "types"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Ownership Types"
        return context


class OwnershipTypeCreateView(LoginRequiredMixin, CreateView):
    """Create a new ownership type."""

    model = OwnershipType
    form_class = OwnershipTypeForm
    template_name = "inventory/refdata/ownership_type_form.html"
    success_url = reverse_lazy("inventory:ownership_type_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Ownership Type"
        context["form_title"] = "Create Ownership Type"
        return context


class OwnershipTypeUpdateView(LoginRequiredMixin, UpdateView):
    """Update an ownership type."""

    model = OwnershipType
    form_class = OwnershipTypeForm
    template_name = "inventory/refdata/ownership_type_form.html"
    success_url = reverse_lazy("inventory:ownership_type_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Edit Ownership Type"
        context["form_title"] = f"Edit {self.object.name}"
        return context


# =============================================================================
# PRINT VIEWS
# =============================================================================


class GRNPrintView(LoginRequiredMixin, DetailView):
    """Print-friendly view for GRN documents."""

    template_name = "inventory/print/grn_print.html"
    context_object_name = "grn"

    def get_queryset(self):
        from .models import GoodsReceiptNote
        return GoodsReceiptNote.objects.select_related(
            "warehouse", "supplier_party", "owner_party", "ownership_type"
        )

    def get_context_data(self, **kwargs):
        from .models import GRNLine
        context = super().get_context_data(**kwargs)
        context["lines"] = GRNLine.objects.filter(grn=self.object).select_related(
            "item", "location", "lot"
        ).order_by("id")
        return context


class IssuePrintView(LoginRequiredMixin, DetailView):
    """Print-friendly view for Stock Issue documents."""

    template_name = "inventory/print/issue_print.html"
    context_object_name = "issue"

    def get_queryset(self):
        from .models import StockIssue
        return StockIssue.objects.select_related("warehouse", "recipient_party")

    def get_context_data(self, **kwargs):
        from .models import StockIssueLine
        context = super().get_context_data(**kwargs)
        context["lines"] = StockIssueLine.objects.filter(issue=self.object).select_related(
            "item", "location", "lot"
        ).order_by("id")
        return context


class TransferPrintView(LoginRequiredMixin, DetailView):
    """Print-friendly view for Stock Transfer documents."""

    template_name = "inventory/print/transfer_print.html"
    context_object_name = "transfer"

    def get_queryset(self):
        from .models import StockTransfer
        return StockTransfer.objects.select_related("from_warehouse", "to_warehouse")

    def get_context_data(self, **kwargs):
        from .models import StockTransferLine
        context = super().get_context_data(**kwargs)
        context["lines"] = StockTransferLine.objects.filter(transfer=self.object).select_related(
            "item", "from_location", "to_location"
        ).order_by("id")
        return context


class AdjustmentPrintView(LoginRequiredMixin, DetailView):
    """Print-friendly view for Stock Adjustment documents."""

    template_name = "inventory/print/adjustment_print.html"
    context_object_name = "adjustment"

    def get_queryset(self):
        from .models import StockAdjustment as StockAdjustmentDoc
        return StockAdjustmentDoc.objects.select_related("warehouse", "reason")

    def get_context_data(self, **kwargs):
        from .models import StockAdjustmentLine
        context = super().get_context_data(**kwargs)
        context["lines"] = StockAdjustmentLine.objects.filter(adjustment=self.object).select_related(
            "item", "location"
        ).order_by("id")
        return context


# =============================================================================
# REPORTS
# =============================================================================


class StockValuationReportView(LoginRequiredMixin, View):
    """Stock valuation report showing current inventory value."""

    template_name = "inventory/reports/stock_valuation.html"

    def get(self, request):
        from django.shortcuts import render
        from django.db.models import Sum, F, Value, DecimalField
        from django.db.models.functions import Coalesce
        from .models import StockLedger, Warehouse

        # Get filters
        warehouse_id = request.GET.get("warehouse")
        category_id = request.GET.get("category")

        # Build queryset - aggregate by item, location
        queryset = StockLedger.objects.values(
            "item__id", "item__code", "item__name", "item__category__name",
            "location__id", "location__code", "location__warehouse__name"
        ).annotate(
            qty_balance=Sum("qty_delta"),
            total_value=Sum(F("qty_delta") * F("unit_cost"), output_field=DecimalField(max_digits=18, decimal_places=4))
        ).filter(qty_balance__gt=0).order_by("item__code", "location__code")

        if warehouse_id:
            queryset = queryset.filter(location__warehouse_id=warehouse_id)
        if category_id:
            queryset = queryset.filter(item__category_id=category_id)

        # Calculate totals
        totals = queryset.aggregate(
            total_qty=Sum("qty_balance"),
            grand_total=Sum("total_value")
        )

        context = {
            "page_title": "Stock Valuation Report",
            "items": list(queryset),
            "totals": totals,
            "warehouses": Warehouse.objects.filter(is_active=True).order_by("name"),
            "categories": InventoryCategory.objects.filter(is_active=True).order_by("name"),
            "selected_warehouse": warehouse_id,
            "selected_category": category_id,
        }
        return render(request, self.template_name, context)


class MovementHistoryReportView(LoginRequiredMixin, View):
    """Movement history report showing all stock movements."""

    template_name = "inventory/reports/movement_history.html"

    def get(self, request):
        from django.shortcuts import render
        from .models import StockLedger, Warehouse
        from datetime import datetime, timedelta

        # Get filters
        warehouse_id = request.GET.get("warehouse")
        item_id = request.GET.get("item")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        # Default to last 30 days if no dates specified
        if not date_to:
            date_to = timezone.now().date()
        else:
            date_to = datetime.strptime(date_to, "%Y-%m-%d").date()

        if not date_from:
            date_from = date_to - timedelta(days=30)
        else:
            date_from = datetime.strptime(date_from, "%Y-%m-%d").date()

        # Build queryset
        queryset = StockLedger.objects.select_related(
            "item", "location", "location__warehouse", "lot", "created_by"
        ).filter(
            transaction_date__date__gte=date_from,
            transaction_date__date__lte=date_to
        ).order_by("-transaction_date")

        if warehouse_id:
            queryset = queryset.filter(location__warehouse_id=warehouse_id)
        if item_id:
            queryset = queryset.filter(item_id=item_id)

        # Calculate totals
        totals = queryset.aggregate(
            total_in=Sum("qty_delta", filter=Q(qty_delta__gt=0)),
            total_out=Sum("qty_delta", filter=Q(qty_delta__lt=0))
        )

        context = {
            "page_title": "Movement History Report",
            "movements": queryset[:500],  # Limit to 500 records
            "totals": totals,
            "warehouses": Warehouse.objects.filter(is_active=True).order_by("name"),
            "items": InventoryItem.objects.filter(is_active=True).order_by("code")[:100],
            "selected_warehouse": warehouse_id,
            "selected_item": item_id,
            "date_from": date_from.strftime("%Y-%m-%d"),
            "date_to": date_to.strftime("%Y-%m-%d"),
        }
        return render(request, self.template_name, context)


class LowStockReportView(LoginRequiredMixin, View):
    """Report showing items below reorder point."""

    template_name = "inventory/reports/low_stock.html"

    def get(self, request):
        from django.shortcuts import render
        from .models import Warehouse

        # Get filters
        warehouse_id = request.GET.get("warehouse")

        # Build queryset - items below reorder point
        queryset = InventoryStock.objects.select_related(
            "item", "location", "location__warehouse"
        ).filter(
            quantity__lt=F("reorder_point"),
            item__is_active=True
        ).order_by("item__code")

        if warehouse_id:
            queryset = queryset.filter(location__warehouse_id=warehouse_id)

        context = {
            "page_title": "Low Stock Report",
            "items": queryset,
            "warehouses": Warehouse.objects.filter(is_active=True).order_by("name"),
            "selected_warehouse": warehouse_id,
        }
        return render(request, self.template_name, context)


# =============================================================================
# API ENDPOINTS
# =============================================================================


class StockBalanceAPIView(LoginRequiredMixin, View):
    """API to get stock balances aggregated from ledger."""

    def get(self, request):
        from django.http import JsonResponse
        from .models import StockLedger

        # Get filters
        warehouse_id = request.GET.get("warehouse")
        item_id = request.GET.get("item")
        location_id = request.GET.get("location")

        # Build queryset - aggregate by item, location
        queryset = StockLedger.objects.values(
            "item__id", "item__code", "item__name",
            "location__id", "location__code", "location__warehouse__name"
        ).annotate(
            qty_balance=Sum("qty_delta")
        ).filter(qty_balance__gt=0).order_by("item__code")

        if warehouse_id:
            queryset = queryset.filter(location__warehouse_id=warehouse_id)
        if item_id:
            queryset = queryset.filter(item_id=item_id)
        if location_id:
            queryset = queryset.filter(location_id=location_id)

        data = []
        for row in queryset[:500]:  # Limit results
            data.append({
                "item_id": row["item__id"],
                "item_code": row["item__code"],
                "item_name": row["item__name"],
                "location_id": row["location__id"],
                "location_code": row["location__code"],
                "warehouse": row["location__warehouse__name"],
                "qty_balance": float(row["qty_balance"]),
            })

        return JsonResponse({"balances": data, "count": len(data)})


class ItemLookupAPIView(LoginRequiredMixin, View):
    """API to lookup items by code or name."""

    def get(self, request):
        from django.http import JsonResponse

        query = request.GET.get("q", "")
        category_id = request.GET.get("category")
        limit = min(int(request.GET.get("limit", 20)), 100)

        queryset = InventoryItem.objects.filter(is_active=True)

        if query:
            queryset = queryset.filter(
                Q(code__icontains=query) | Q(name__icontains=query)
            )
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        queryset = queryset.select_related("category", "primary_uom")[:limit]

        data = []
        for item in queryset:
            data.append({
                "id": item.id,
                "code": item.code,
                "name": item.name,
                "category": item.category.name if item.category else None,
                "uom": item.primary_uom.symbol if item.primary_uom else None,
                "description": item.description or "",
            })

        return JsonResponse({"items": data, "count": len(data)})


class LedgerEntriesAPIView(LoginRequiredMixin, View):
    """API to get ledger entries with filters."""

    def get(self, request):
        from django.http import JsonResponse
        from .models import StockLedger
        from datetime import datetime, timedelta

        # Get filters
        item_id = request.GET.get("item")
        location_id = request.GET.get("location")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")
        limit = min(int(request.GET.get("limit", 100)), 500)

        queryset = StockLedger.objects.select_related(
            "item", "location", "lot"
        ).order_by("-transaction_date")

        if item_id:
            queryset = queryset.filter(item_id=item_id)
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        if date_from:
            queryset = queryset.filter(transaction_date__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__date__lte=date_to)

        queryset = queryset[:limit]

        data = []
        for entry in queryset:
            data.append({
                "id": entry.id,
                "transaction_date": entry.transaction_date.isoformat(),
                "document_type": entry.document_type,
                "document_number": entry.document_number,
                "item_code": entry.item.code,
                "item_name": entry.item.name,
                "location_code": entry.location.code,
                "lot_number": entry.lot.lot_number if entry.lot else None,
                "qty_delta": float(entry.qty_delta),
                "unit_cost": float(entry.unit_cost),
                "running_balance": float(entry.running_balance) if entry.running_balance else None,
            })

        return JsonResponse({"entries": data, "count": len(data)})


class LowStockAPIView(LoginRequiredMixin, View):
    """API to get items below reorder point."""

    def get(self, request):
        from django.http import JsonResponse

        warehouse_id = request.GET.get("warehouse")

        queryset = InventoryStock.objects.select_related(
            "item", "location", "location__warehouse"
        ).filter(
            quantity__lt=F("reorder_point"),
            item__is_active=True
        ).order_by("item__code")

        if warehouse_id:
            queryset = queryset.filter(location__warehouse_id=warehouse_id)

        data = []
        for stock in queryset[:200]:
            data.append({
                "item_id": stock.item.id,
                "item_code": stock.item.code,
                "item_name": stock.item.name,
                "location_code": stock.location.code,
                "warehouse": stock.location.warehouse.name,
                "current_qty": float(stock.quantity),
                "reorder_point": float(stock.reorder_point),
                "shortage": float(stock.reorder_point - stock.quantity),
            })

        return JsonResponse({"low_stock_items": data, "count": len(data)})
