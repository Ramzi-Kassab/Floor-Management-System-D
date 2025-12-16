from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    # Categories
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/create/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/", views.CategoryDetailView.as_view(), name="category_detail"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),
    # Category Attributes (within category context)
    path("attributes/", views.CategoryAttributeListView.as_view(), name="attribute_list"),
    path("categories/<int:category_pk>/attributes/create/", views.CategoryAttributeCreateView.as_view(), name="category_attribute_create"),
    path("categories/<int:category_pk>/attributes/<int:pk>/edit/", views.CategoryAttributeUpdateView.as_view(), name="category_attribute_update"),
    path("categories/<int:category_pk>/attributes/<int:pk>/delete/", views.CategoryAttributeDeleteView.as_view(), name="category_attribute_delete"),
    # Standalone Attributes (from attributes list)
    path("attributes/create/", views.StandaloneAttributeCreateView.as_view(), name="standalone_attribute_create"),
    path("attributes/<int:pk>/edit/", views.StandaloneAttributeUpdateView.as_view(), name="standalone_attribute_update"),
    path("attributes/<int:pk>/delete/", views.StandaloneAttributeDeleteView.as_view(), name="standalone_attribute_delete"),
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
    # Item Variants (within item context)
    path("variants/", views.ItemVariantListView.as_view(), name="variant_list"),
    path("items/<int:item_pk>/variants/create/", views.ItemVariantCreateView.as_view(), name="item_variant_create"),
    path("items/<int:item_pk>/variants/<int:pk>/edit/", views.ItemVariantUpdateView.as_view(), name="item_variant_update"),
    path("items/<int:item_pk>/variants/<int:pk>/delete/", views.ItemVariantDeleteView.as_view(), name="item_variant_delete"),
    # Standalone Variants (from variants list)
    path("variants/create/", views.StandaloneVariantCreateView.as_view(), name="standalone_variant_create"),
    path("variants/<int:pk>/edit/", views.StandaloneVariantUpdateView.as_view(), name="standalone_variant_update"),
    path("variants/<int:pk>/delete/", views.StandaloneVariantDeleteView.as_view(), name="standalone_variant_delete"),
    # Units of Measure (Master Data)
    path("units/", views.UnitOfMeasureListView.as_view(), name="uom_list"),
    path("units/create/", views.UnitOfMeasureCreateView.as_view(), name="uom_create"),
    path("units/<int:pk>/edit/", views.UnitOfMeasureUpdateView.as_view(), name="uom_update"),
    path("units/<int:pk>/delete/", views.UnitOfMeasureDeleteView.as_view(), name="uom_delete"),
    # Material Lots
    path("lots/", views.MaterialLotListView.as_view(), name="lot_list"),
    path("lots/create/", views.MaterialLotCreateView.as_view(), name="lot_create"),
    path("lots/<int:pk>/", views.MaterialLotDetailView.as_view(), name="lot_detail"),
    path("lots/<int:pk>/edit/", views.MaterialLotUpdateView.as_view(), name="lot_update"),
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
    # API Endpoints
    path("api/category/<int:category_pk>/attributes/", views.CategoryAttributesAPIView.as_view(), name="api_category_attributes"),
    path("api/category/<int:category_pk>/generate-code/", views.CategoryGenerateCodeAPIView.as_view(), name="api_category_generate_code"),
]
