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
    InventoryCategoryForm,
    InventoryItemForm,
    InventoryLocationForm,
    InventoryStockForm,
    InventoryTransactionForm,
    StockAdjustmentForm,
)
from .models import InventoryCategory, InventoryItem, InventoryLocation, InventoryStock, InventoryTransaction


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
        return InventoryItem.objects.select_related("category", "primary_supplier", "created_by")

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
