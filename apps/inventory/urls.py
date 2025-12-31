from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    # Dashboard
    path("dashboard/", views.InventoryDashboardView.as_view(), name="dashboard"),

    # Categories
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/create/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/", views.CategoryDetailView.as_view(), name="category_detail"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),
    # Attributes (simple global list - just names)
    path("attributes/", views.AttributeListView.as_view(), name="attribute_list"),
    path("attributes/create/", views.StandaloneAttributeCreateView.as_view(), name="standalone_attribute_create"),
    path("attributes/<int:pk>/edit/", views.StandaloneAttributeUpdateView.as_view(), name="standalone_attribute_update"),
    path("attributes/<int:pk>/delete/", views.StandaloneAttributeDeleteView.as_view(), name="standalone_attribute_delete"),
    # Category Attributes (link attribute to category with type/unit/validation)
    path("category-attributes/", views.CategoryAttributeListView.as_view(), name="category_attribute_list"),
    path("category-attributes/create/", views.CategoryAttributeCreateView.as_view(), name="category_attribute_create"),
    path("category-attributes/bulk-create/", views.CategoryAttributeBulkCreateView.as_view(), name="category_attribute_bulk_create"),
    path("category-attributes/<int:pk>/edit/", views.CategoryAttributeUpdateView.as_view(), name="category_attribute_update"),
    path("category-attributes/<int:pk>/delete/", views.CategoryAttributeDeleteView.as_view(), name="category_attribute_delete"),
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
    path("items/<int:pk>/clone/", views.ItemCloneView.as_view(), name="item_clone"),
    # Variants (Variant Cases - Master Data) - shows the 10 standard cases
    path("variants/", views.VariantCaseListView.as_view(), name="variant_list"),
    path("variants/create/", views.VariantCaseCreateView.as_view(), name="variant_create"),
    path("variants/<int:pk>/edit/", views.VariantCaseUpdateView.as_view(), name="variant_update"),
    path("variants/<int:pk>/delete/", views.VariantCaseDeleteView.as_view(), name="variant_delete"),
    # Item Variants (link items to variant cases)
    path("item-variants/", views.ItemVariantListView.as_view(), name="item_variant_list"),
    path("items/<int:item_pk>/variants/create/", views.ItemVariantCreateView.as_view(), name="item_variant_create"),
    path("items/<int:item_pk>/variants/bulk-create/", views.BulkVariantCreateView.as_view(), name="bulk_variant_create"),
    path("items/<int:item_pk>/variants/<int:pk>/edit/", views.ItemVariantUpdateView.as_view(), name="item_variant_update"),
    path("items/<int:item_pk>/variants/<int:pk>/delete/", views.ItemVariantDeleteView.as_view(), name="item_variant_delete"),
    path("item-variants/create/", views.StandaloneVariantCreateView.as_view(), name="standalone_variant_create"),
    path("item-variants/<int:pk>/edit/", views.StandaloneVariantUpdateView.as_view(), name="standalone_variant_update"),
    path("item-variants/<int:pk>/delete/", views.StandaloneVariantDeleteView.as_view(), name="standalone_variant_delete"),
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
    # Item Planning (per-warehouse)
    path("items/<int:item_pk>/planning/create/", views.ItemPlanningCreateView.as_view(), name="item_planning_create"),
    path("items/<int:item_pk>/planning/<int:pk>/edit/", views.ItemPlanningUpdateView.as_view(), name="item_planning_update"),
    path("items/<int:item_pk>/planning/<int:pk>/delete/", views.ItemPlanningDeleteView.as_view(), name="item_planning_delete"),
    # Item Supplier (multiple suppliers)
    path("items/<int:item_pk>/suppliers/create/", views.ItemSupplierCreateView.as_view(), name="item_supplier_create"),
    path("items/<int:item_pk>/suppliers/<int:pk>/edit/", views.ItemSupplierUpdateView.as_view(), name="item_supplier_update"),
    path("items/<int:item_pk>/suppliers/<int:pk>/delete/", views.ItemSupplierDeleteView.as_view(), name="item_supplier_delete"),
    # Item Identifier (barcodes)
    path("items/<int:item_pk>/identifiers/create/", views.ItemIdentifierCreateView.as_view(), name="item_identifier_create"),
    path("items/<int:item_pk>/identifiers/<int:pk>/edit/", views.ItemIdentifierUpdateView.as_view(), name="item_identifier_update"),
    path("items/<int:item_pk>/identifiers/<int:pk>/delete/", views.ItemIdentifierDeleteView.as_view(), name="item_identifier_delete"),
    # Item Bit Spec
    path("items/<int:item_pk>/bit-spec/create/", views.ItemBitSpecCreateView.as_view(), name="item_bit_spec_create"),
    path("items/<int:item_pk>/bit-spec/edit/", views.ItemBitSpecUpdateView.as_view(), name="item_bit_spec_update"),
    # Item Cutter Spec
    path("items/<int:item_pk>/cutter-spec/create/", views.ItemCutterSpecCreateView.as_view(), name="item_cutter_spec_create"),
    path("items/<int:item_pk>/cutter-spec/edit/", views.ItemCutterSpecUpdateView.as_view(), name="item_cutter_spec_update"),
    # API Endpoints
    path("api/category/<int:category_pk>/attributes/", views.CategoryAttributesAPIView.as_view(), name="api_category_attributes"),
    path("api/category/<int:category_pk>/generate-code/", views.CategoryGenerateCodeAPIView.as_view(), name="api_category_generate_code"),
    path("api/items/search/", views.ItemSearchAPIView.as_view(), name="api_items_search"),
    path("api/item-relationships/", views.ItemRelationshipAPIView.as_view(), name="api_item_relationships"),
    path("api/item-relationships/<int:pk>/", views.ItemRelationshipAPIView.as_view(), name="api_item_relationship_detail"),
    path("api/warehouse/<int:warehouse_pk>/locations/", views.WarehouseLocationsAPIView.as_view(), name="api_warehouse_locations"),

    # =========================================================================
    # PHASE 2: LEDGER (Read-Only)
    # =========================================================================
    path("ledger/", views.StockLedgerListView.as_view(), name="stock_ledger_list"),
    path("balances/", views.StockBalanceListView.as_view(), name="stock_balance_list"),

    # =========================================================================
    # PHASE 3: DOCUMENTS (GRN, Issues, Transfers, Adjustments)
    # =========================================================================

    # Goods Receipt Notes
    path("grn/", views.GRNListView.as_view(), name="grn_list"),
    path("grn/create/", views.GRNCreateView.as_view(), name="grn_create"),
    path("grn/from-po/<int:po_pk>/", views.GRNFromPOView.as_view(), name="grn_from_po"),
    path("grn/<int:pk>/", views.GRNDetailView.as_view(), name="grn_detail"),
    path("grn/<int:pk>/edit/", views.GRNUpdateView.as_view(), name="grn_update"),
    path("grn/<int:pk>/post/", views.GRNPostView.as_view(), name="grn_post"),
    path("grn/<int:pk>/submit-qc/", views.GRNSubmitForQCView.as_view(), name="grn_submit_qc"),
    path("grn/<int:pk>/qc/", views.GRNQCView.as_view(), name="grn_qc"),
    path("grn/<int:pk>/approve-variance/", views.GRNApproveVarianceView.as_view(), name="grn_approve_variance"),

    # Stock Issues
    path("issues/", views.StockIssueListView.as_view(), name="issue_list"),
    path("issues/create/", views.StockIssueCreateView.as_view(), name="issue_create"),
    path("issues/<int:pk>/", views.StockIssueDetailView.as_view(), name="issue_detail"),
    path("issues/<int:pk>/post/", views.StockIssuePostView.as_view(), name="issue_post"),

    # Stock Transfers
    path("transfers/", views.StockTransferListView.as_view(), name="transfer_list"),
    path("transfers/create/", views.StockTransferCreateView.as_view(), name="transfer_create"),
    path("transfers/<int:pk>/", views.StockTransferDetailView.as_view(), name="transfer_detail"),
    path("transfers/<int:pk>/post/", views.StockTransferPostView.as_view(), name="transfer_post"),

    # Stock Adjustments (Document-based)
    path("adjustments/", views.StockAdjustmentDocListView.as_view(), name="adjustment_list"),
    path("adjustments/create/", views.StockAdjustmentDocCreateView.as_view(), name="adjustment_create"),
    path("adjustments/<int:pk>/", views.StockAdjustmentDocDetailView.as_view(), name="adjustment_detail"),
    path("adjustments/<int:pk>/post/", views.StockAdjustmentDocPostView.as_view(), name="adjustment_post"),

    # =========================================================================
    # PHASE 4: ASSETS
    # =========================================================================
    path("assets/", views.AssetListView.as_view(), name="asset_list"),
    path("assets/create/", views.AssetCreateView.as_view(), name="asset_create"),
    path("assets/<int:pk>/", views.AssetDetailView.as_view(), name="asset_detail"),
    path("assets/<int:pk>/edit/", views.AssetUpdateView.as_view(), name="asset_update"),
    path("assets/<int:asset_pk>/move/", views.AssetMovementCreateView.as_view(), name="asset_move"),

    # =========================================================================
    # PHASE 5: QC GATES
    # =========================================================================
    path("qc/changes/", views.QualityStatusChangeListView.as_view(), name="qc_change_list"),
    path("qc/changes/create/", views.QualityStatusChangeCreateView.as_view(), name="qc_change_create"),

    # =========================================================================
    # PHASE 6: RESERVATIONS
    # =========================================================================
    path("reservations/", views.StockReservationListView.as_view(), name="reservation_list"),
    path("reservations/create/", views.StockReservationCreateView.as_view(), name="reservation_create"),
    path("reservations/<int:pk>/cancel/", views.StockReservationCancelView.as_view(), name="reservation_cancel"),

    # =========================================================================
    # PHASE 7: BOM
    # =========================================================================
    path("bom/", views.BOMListView.as_view(), name="bom_list"),
    path("bom/create/", views.BOMCreateView.as_view(), name="bom_create"),
    path("bom/<int:pk>/", views.BOMDetailView.as_view(), name="bom_detail"),
    path("bom/<int:pk>/edit/", views.BOMUpdateView.as_view(), name="bom_update"),
    path("bom/<int:pk>/recalculate/", views.BOMRecalculateView.as_view(), name="bom_recalculate"),

    # =========================================================================
    # PHASE 8: CYCLE COUNT
    # =========================================================================
    path("cyclecount/plans/", views.CycleCountPlanListView.as_view(), name="cyclecount_plan_list"),
    path("cyclecount/plans/create/", views.CycleCountPlanCreateView.as_view(), name="cyclecount_plan_create"),
    path("cyclecount/sessions/", views.CycleCountSessionListView.as_view(), name="cyclecount_session_list"),
    path("cyclecount/sessions/create/", views.CycleCountSessionCreateView.as_view(), name="cyclecount_session_create"),
    path("cyclecount/sessions/<int:pk>/", views.CycleCountSessionDetailView.as_view(), name="cyclecount_session_detail"),
    path("cyclecount/sessions/<int:pk>/finalize/", views.CycleCountSessionFinalizeView.as_view(), name="cyclecount_session_finalize"),

    # =========================================================================
    # REFERENCE DATA
    # =========================================================================
    # Parties
    path("parties/", views.PartyListView.as_view(), name="party_list"),
    path("parties/create/", views.PartyCreateView.as_view(), name="party_create"),
    path("parties/<int:pk>/edit/", views.PartyUpdateView.as_view(), name="party_update"),

    # Condition Types
    path("conditions/", views.ConditionTypeListView.as_view(), name="condition_list"),
    path("conditions/create/", views.ConditionTypeCreateView.as_view(), name="condition_create"),
    path("conditions/<int:pk>/edit/", views.ConditionTypeUpdateView.as_view(), name="condition_update"),

    # Quality Statuses
    path("quality-statuses/", views.QualityStatusListView.as_view(), name="quality_status_list"),
    path("quality-statuses/create/", views.QualityStatusCreateView.as_view(), name="quality_status_create"),
    path("quality-statuses/<int:pk>/edit/", views.QualityStatusUpdateView.as_view(), name="quality_status_update"),

    # Adjustment Reasons
    path("adjustment-reasons/", views.AdjustmentReasonListView.as_view(), name="adjustment_reason_list"),
    path("adjustment-reasons/create/", views.AdjustmentReasonCreateView.as_view(), name="adjustment_reason_create"),
    path("adjustment-reasons/<int:pk>/edit/", views.AdjustmentReasonUpdateView.as_view(), name="adjustment_reason_update"),

    # Ownership Types
    path("ownership-types/", views.OwnershipTypeListView.as_view(), name="ownership_type_list"),
    path("ownership-types/create/", views.OwnershipTypeCreateView.as_view(), name="ownership_type_create"),
    path("ownership-types/<int:pk>/edit/", views.OwnershipTypeUpdateView.as_view(), name="ownership_type_update"),

    # Receipt Tolerances
    path("tolerances/", views.ReceiptToleranceListView.as_view(), name="tolerance_list"),
    path("tolerances/create/", views.ReceiptToleranceCreateView.as_view(), name="tolerance_create"),
    path("tolerances/<int:pk>/edit/", views.ReceiptToleranceUpdateView.as_view(), name="tolerance_update"),

    # =========================================================================
    # PRINT VIEWS
    # =========================================================================
    path("grn/<int:pk>/print/", views.GRNPrintView.as_view(), name="grn_print"),
    path("issues/<int:pk>/print/", views.IssuePrintView.as_view(), name="issue_print"),
    path("transfers/<int:pk>/print/", views.TransferPrintView.as_view(), name="transfer_print"),
    path("adjustments/<int:pk>/print/", views.AdjustmentPrintView.as_view(), name="adjustment_print"),

    # =========================================================================
    # REPORTS
    # =========================================================================
    path("reports/stock-valuation/", views.StockValuationReportView.as_view(), name="report_stock_valuation"),
    path("reports/movement-history/", views.MovementHistoryReportView.as_view(), name="report_movement_history"),
    path("reports/low-stock/", views.LowStockReportView.as_view(), name="report_low_stock"),
    path("reports/variances/", views.VarianceReportView.as_view(), name="report_variances"),

    # =========================================================================
    # API ENDPOINTS
    # =========================================================================
    path("api/stock-balances/", views.StockBalanceAPIView.as_view(), name="api_stock_balances"),
    path("api/items/lookup/", views.ItemLookupAPIView.as_view(), name="api_item_lookup"),
    path("api/ledger/entries/", views.LedgerEntriesAPIView.as_view(), name="api_ledger_entries"),
    path("api/low-stock/", views.LowStockAPIView.as_view(), name="api_low_stock"),

    # =========================================================================
    # POCKET/MOBILE ACCESS (QR Code Scan)
    # =========================================================================
    path("pocket/login/", views.PocketLoginView.as_view(), name="pocket_login"),
    path("pocket/logout/", views.PocketLogoutView.as_view(), name="pocket_logout"),
    path("pocket/item/<int:pk>/", views.PocketItemView.as_view(), name="pocket_item"),
    path("pocket/item/<int:pk>/action/", views.PocketQuickActionView.as_view(), name="pocket_action"),
]
