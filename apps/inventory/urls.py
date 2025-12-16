from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    # Categories
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/create/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_update"),
    # Locations
    path("locations/", views.LocationListView.as_view(), name="location_list"),
    path("locations/create/", views.LocationCreateView.as_view(), name="location_create"),
    path("locations/<int:pk>/edit/", views.LocationUpdateView.as_view(), name="location_update"),
    # Items
    path("", views.ItemListView.as_view(), name="item_list"),
    path("items/", views.ItemListView.as_view(), name="items"),
    path("items/create/", views.ItemCreateView.as_view(), name="item_create"),
    path("items/<int:pk>/", views.ItemDetailView.as_view(), name="item_detail"),
    path("items/<int:pk>/edit/", views.ItemUpdateView.as_view(), name="item_update"),
    # Import/Export
    path("items/import/", views.ItemImportView.as_view(), name="item_import"),
    path("items/export/", views.ItemExportView.as_view(), name="item_export"),
    path("items/import/template/", views.ItemImportTemplateView.as_view(), name="item_import_template"),
    # Transactions
    path("transactions/", views.TransactionListView.as_view(), name="transaction_list"),
    path("transactions/create/", views.TransactionCreateView.as_view(), name="transaction_create"),
    path("transactions/<int:pk>/", views.TransactionDetailView.as_view(), name="transaction_detail"),
    # Stock
    path("stock/", views.StockListView.as_view(), name="stock_list"),
    path("stock/<int:pk>/adjust/", views.StockAdjustView.as_view(), name="stock_adjust"),
]
