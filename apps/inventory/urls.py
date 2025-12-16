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
    path("items/import/", views.ItemImportView.as_view(), name="item_import"),
    path("items/export/", views.ItemExportView.as_view(), name="item_export"),
    path("items/import-template/", views.ItemImportTemplateView.as_view(), name="item_import_template"),
    # Transactions
    path("transactions/", views.TransactionListView.as_view(), name="transaction_list"),
    path("transactions/create/", views.TransactionCreateView.as_view(), name="transaction_create"),
    path("transactions/<int:pk>/", views.TransactionDetailView.as_view(), name="transaction_detail"),
    # Stock
    path("stock/", views.StockListView.as_view(), name="stock_list"),
    path("stock/<int:pk>/adjust/", views.StockAdjustView.as_view(), name="stock_adjust"),
    # Attributes (standalone list - just names)
    path("attributes/", views.AttributeListView.as_view(), name="attribute_list"),
    path("attributes/create/", views.StandaloneAttributeCreateView.as_view(), name="attribute_create"),
    path("attributes/<int:pk>/edit/", views.StandaloneAttributeUpdateView.as_view(), name="attribute_update"),
    path("attributes/<int:pk>/delete/", views.StandaloneAttributeDeleteView.as_view(), name="attribute_delete"),
    # Category Attributes (link attribute to category)
    path("category-attributes/", views.CategoryAttributeListView.as_view(), name="category_attribute_list"),
    path("category-attributes/create/", views.CategoryAttributeCreateView.as_view(), name="category_attribute_create"),
    path("category-attributes/<int:pk>/edit/", views.CategoryAttributeUpdateView.as_view(), name="category_attribute_update"),
    path("category-attributes/<int:pk>/delete/", views.CategoryAttributeDeleteView.as_view(), name="category_attribute_delete"),
    # Units of Measure
    path("uom/", views.UnitOfMeasureListView.as_view(), name="uom_list"),
    path("uom/create/", views.UnitOfMeasureCreateView.as_view(), name="uom_create"),
    path("uom/<int:pk>/edit/", views.UnitOfMeasureUpdateView.as_view(), name="uom_update"),
    path("uom/<int:pk>/delete/", views.UnitOfMeasureDeleteView.as_view(), name="uom_delete"),
    # Variant Cases (master data)
    path("variant-cases/", views.VariantCaseListView.as_view(), name="variant_list"),
    path("variant-cases/create/", views.VariantCaseCreateView.as_view(), name="variant_create"),
    path("variant-cases/<int:pk>/edit/", views.VariantCaseUpdateView.as_view(), name="variant_update"),
    path("variant-cases/<int:pk>/delete/", views.VariantCaseDeleteView.as_view(), name="variant_delete"),
    # Item Variants (standalone list)
    path("item-variants/", views.ItemVariantListView.as_view(), name="item_variant_list"),
    path("item-variants/create/", views.StandaloneVariantCreateView.as_view(), name="item_variant_create"),
    path("item-variants/<int:pk>/edit/", views.StandaloneVariantUpdateView.as_view(), name="item_variant_update"),
    path("item-variants/<int:pk>/delete/", views.StandaloneVariantDeleteView.as_view(), name="item_variant_delete"),
    # Item Variants (within item context)
    path("items/<int:item_pk>/variants/create/", views.ItemVariantCreateView.as_view(), name="item_variant_add"),
    path("items/<int:item_pk>/variants/<int:pk>/edit/", views.ItemVariantUpdateView.as_view(), name="item_variant_edit"),
    path("items/<int:item_pk>/variants/<int:pk>/delete/", views.ItemVariantDeleteView.as_view(), name="item_variant_remove"),
    # Material Lots
    path("lots/", views.MaterialLotListView.as_view(), name="lot_list"),
    path("lots/create/", views.MaterialLotCreateView.as_view(), name="lot_create"),
    path("lots/<int:pk>/", views.MaterialLotDetailView.as_view(), name="lot_detail"),
    path("lots/<int:pk>/edit/", views.MaterialLotUpdateView.as_view(), name="lot_update"),
    # Item Planning (per-warehouse)
    path("items/<int:item_pk>/planning/create/", views.ItemPlanningCreateView.as_view(), name="item_planning_create"),
    path("items/<int:item_pk>/planning/<int:pk>/edit/", views.ItemPlanningUpdateView.as_view(), name="item_planning_update"),
    path("items/<int:item_pk>/planning/<int:pk>/delete/", views.ItemPlanningDeleteView.as_view(), name="item_planning_delete"),
    # Item Suppliers (multiple per item)
    path("items/<int:item_pk>/suppliers/create/", views.ItemSupplierCreateView.as_view(), name="item_supplier_create"),
    path("items/<int:item_pk>/suppliers/<int:pk>/edit/", views.ItemSupplierUpdateView.as_view(), name="item_supplier_update"),
    path("items/<int:item_pk>/suppliers/<int:pk>/delete/", views.ItemSupplierDeleteView.as_view(), name="item_supplier_delete"),
    # Item Identifiers (barcodes)
    path("items/<int:item_pk>/identifiers/create/", views.ItemIdentifierCreateView.as_view(), name="item_identifier_create"),
    path("items/<int:item_pk>/identifiers/<int:pk>/edit/", views.ItemIdentifierUpdateView.as_view(), name="item_identifier_update"),
    path("items/<int:item_pk>/identifiers/<int:pk>/delete/", views.ItemIdentifierDeleteView.as_view(), name="item_identifier_delete"),
    # Item Bit Spec
    path("items/<int:item_pk>/bit-spec/create/", views.ItemBitSpecCreateView.as_view(), name="item_bit_spec_create"),
    path("items/<int:item_pk>/bit-spec/edit/", views.ItemBitSpecUpdateView.as_view(), name="item_bit_spec_update"),
    # Item Cutter Spec
    path("items/<int:item_pk>/cutter-spec/create/", views.ItemCutterSpecCreateView.as_view(), name="item_cutter_spec_create"),
    path("items/<int:item_pk>/cutter-spec/edit/", views.ItemCutterSpecUpdateView.as_view(), name="item_cutter_spec_update"),
    # API endpoints
    path("api/categories/<int:category_pk>/attributes/", views.CategoryAttributesAPIView.as_view(), name="api_category_attributes"),
    path("api/categories/<int:category_pk>/generate-code/", views.CategoryGenerateCodeAPIView.as_view(), name="api_category_generate_code"),
]
