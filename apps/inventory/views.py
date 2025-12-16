"""
ARDT FMS - Inventory App Views
Version: 5.4
"""

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q, Sum
from django.shortcuts import get_object_or_404, redirect
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
)
from .models import (
    Attribute,
    CategoryAttribute,
    InventoryCategory,
    InventoryItem,
    InventoryLocation,
    InventoryStock,
    InventoryTransaction,
    ItemBitSpec,
    ItemCutterSpec,
    ItemIdentifier,
    ItemPlanning,
    ItemSupplier,
    ItemVariant,
    UnitOfMeasure,
    VariantCase,
)


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

        # NEW: Identifiers (multiple barcodes/identifiers)
        context["identifiers"] = ItemIdentifier.objects.filter(item=item)

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

        return context


class ItemCreateView(LoginRequiredMixin, CreateView):
    """Create inventory item."""

    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/item_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Item '{form.instance.code}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Item"
        context["form_title"] = "Create Inventory Item"
        context["categories"] = InventoryCategory.objects.filter(is_active=True, parent__isnull=True).prefetch_related("children")
        return context


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    """Update inventory item."""

    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/item_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Item '{form.instance.code}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("inventory:item_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.code}"
        context["form_title"] = "Edit Inventory Item"
        context["categories"] = InventoryCategory.objects.filter(is_active=True, parent__isnull=True).prefetch_related("children")
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
    """List of all attributes (simple name list)."""

    model = Attribute
    template_name = "inventory/attribute_list.html"
    context_object_name = "attributes"
    paginate_by = 50

    def get_queryset(self):
        queryset = Attribute.objects.all()

        # Search filter
        search = self.request.GET.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.order_by("code")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Attributes"
        context["search_query"] = self.request.GET.get("q", "")
        return context


class StandaloneAttributeCreateView(LoginRequiredMixin, CreateView):
    """Create a new attribute."""

    model = Attribute
    template_name = "inventory/standalone_attribute_form.html"
    fields = ["code", "name", "description", "is_active"]

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
    fields = ["name", "description", "is_active"]

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
                "min_value": str(attr.min_value) if attr.min_value else None,
                "max_value": str(attr.max_value) if attr.max_value else None,
                "options": attr.options,
            })

        return JsonResponse({"attributes": data})


class CategoryGenerateCodeAPIView(LoginRequiredMixin, View):
    """API to generate next item code for a category."""

    def get(self, request, category_pk):
        category = get_object_or_404(InventoryCategory, pk=category_pk)
        code = category.generate_next_code()
        return JsonResponse({"code": code})


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
