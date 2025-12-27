from django.contrib import admin

from .models import (
    # Original models
    InventoryCategory,
    InventoryItem,
    InventoryLocation,
    InventoryStock,
    InventoryTransaction,
    # Phase 0: Foundation
    Party,
    ConditionType,
    QualityStatus,
    AdjustmentReason,
    OwnershipType,
    LocationType,
    # Phase 1: Lot Tracking
    MaterialLot,
    UnitOfMeasure,
    ItemUOMConversion,
    # Phase 2: Ledger & Balance
    StockLedger,
    StockBalance,
    # Phase 3: Documents
    GoodsReceiptNote,
    GRNLine,
    StockIssue,
    StockIssueLine,
    StockTransfer,
    StockTransferLine,
    StockAdjustment,
    StockAdjustmentLine,
    # Phase 4: Assets
    Asset,
    AssetMovement,
    # Phase 5: QC Gates
    QualityStatusChange,
    # Phase 6: Reservations
    StockReservation,
    # Phase 7: BOM
    BillOfMaterial,
    BOMLine,
    # Phase 8: Cycle Count
    CycleCountPlan,
    CycleCountSession,
    CycleCountLine,
)


# =============================================================================
# ORIGINAL MODELS
# =============================================================================

@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "parent", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]


@admin.register(InventoryLocation)
class InventoryLocationAdmin(admin.ModelAdmin):
    list_display = ["warehouse", "code", "name", "location_type", "is_active"]
    list_filter = ["warehouse", "location_type", "is_active"]
    search_fields = ["code", "name"]


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "item_type", "tracking_type", "category", "is_active"]
    list_filter = ["item_type", "tracking_type", "category", "is_active", "lifecycle_state"]
    search_fields = ["code", "name", "mpn"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(InventoryStock)
class InventoryStockAdmin(admin.ModelAdmin):
    list_display = ["item", "location", "quantity_on_hand", "quantity_reserved", "quantity_available"]
    list_filter = ["location__warehouse"]
    search_fields = ["item__code", "item__name"]


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ["transaction_number", "transaction_type", "item", "quantity", "transaction_date"]
    list_filter = ["transaction_type", "link_type"]
    search_fields = ["transaction_number", "item__code"]


# =============================================================================
# PHASE 0: FOUNDATION (Master Data)
# =============================================================================

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "party_type", "can_own_stock", "is_active"]
    list_filter = ["party_type", "can_own_stock", "is_active"]
    search_fields = ["code", "name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ConditionType)
class ConditionTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_new", "is_saleable", "cost_multiplier", "is_active"]
    list_filter = ["is_new", "is_saleable", "is_active"]
    search_fields = ["code", "name"]


@admin.register(QualityStatus)
class QualityStatusAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_available", "is_initial", "is_terminal", "is_active"]
    list_filter = ["is_available", "is_initial", "is_terminal", "is_active"]
    search_fields = ["code", "name"]


@admin.register(AdjustmentReason)
class AdjustmentReasonAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "default_direction", "requires_approval", "is_active"]
    list_filter = ["default_direction", "requires_approval", "is_active"]
    search_fields = ["code", "name"]


@admin.register(OwnershipType)
class OwnershipTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_ardt_owned", "affects_balance_sheet", "is_active"]
    list_filter = ["is_ardt_owned", "affects_balance_sheet", "is_active"]
    search_fields = ["code", "name"]


@admin.register(LocationType)
class LocationTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_stockable", "is_internal", "is_active"]
    list_filter = ["is_stockable", "is_internal", "is_active"]
    search_fields = ["code", "name"]


# =============================================================================
# PHASE 1: LOT TRACKING
# =============================================================================

@admin.register(MaterialLot)
class MaterialLotAdmin(admin.ModelAdmin):
    list_display = ["lot_number", "inventory_item", "quantity_on_hand", "status", "condition", "quality_status"]
    list_filter = ["status", "condition", "quality_status", "owner_party"]
    search_fields = ["lot_number", "inventory_item__code"]
    date_hierarchy = "received_date"
    readonly_fields = ["created_at"]


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "unit_type", "symbol", "is_si_base", "is_packaging", "base_unit", "conversion_factor", "is_active"]
    list_filter = ["unit_type", "is_si_base", "is_packaging", "is_active"]
    search_fields = ["code", "name"]
    list_editable = ["is_si_base", "is_packaging", "is_active"]


@admin.register(ItemUOMConversion)
class ItemUOMConversionAdmin(admin.ModelAdmin):
    list_display = ["item", "from_uom", "to_uom", "conversion_factor", "is_default", "is_active"]
    list_filter = ["from_uom", "to_uom", "is_default", "is_active"]
    search_fields = ["item__code", "item__name", "from_uom__code", "to_uom__code"]
    autocomplete_fields = ["item", "from_uom", "to_uom"]
    list_editable = ["conversion_factor", "is_default", "is_active"]


# =============================================================================
# PHASE 2: LEDGER & BALANCE
# =============================================================================

@admin.register(StockLedger)
class StockLedgerAdmin(admin.ModelAdmin):
    list_display = ["entry_number", "transaction_date", "transaction_type", "item", "qty_delta", "location"]
    list_filter = ["transaction_type", "transaction_date"]
    search_fields = ["entry_number", "item__code", "reference_id"]
    date_hierarchy = "transaction_date"
    readonly_fields = ["entry_number", "entry_date", "total_cost"]


@admin.register(StockBalance)
class StockBalanceAdmin(admin.ModelAdmin):
    list_display = ["item", "location", "lot", "owner_party", "quality_status", "qty_on_hand", "qty_available"]
    list_filter = ["quality_status", "condition", "owner_party", "ownership_type"]
    search_fields = ["item__code", "location__code"]
    readonly_fields = ["last_recalc_date"]


# =============================================================================
# PHASE 3: DOCUMENTS
# =============================================================================

class GRNLineInline(admin.TabularInline):
    model = GRNLine
    extra = 0
    readonly_fields = ["total_cost", "is_posted", "posted_at"]


@admin.register(GoodsReceiptNote)
class GoodsReceiptNoteAdmin(admin.ModelAdmin):
    list_display = ["grn_number", "receipt_type", "status", "supplier", "receipt_date", "warehouse"]
    list_filter = ["status", "receipt_type", "warehouse"]
    search_fields = ["grn_number", "source_reference"]
    date_hierarchy = "receipt_date"
    inlines = [GRNLineInline]
    readonly_fields = ["grn_number", "created_at", "updated_at", "posted_date"]


class StockIssueLineInline(admin.TabularInline):
    model = StockIssueLine
    extra = 0
    readonly_fields = ["total_cost", "is_posted", "posted_at"]


@admin.register(StockIssue)
class StockIssueAdmin(admin.ModelAdmin):
    list_display = ["issue_number", "issue_type", "status", "warehouse", "issue_date"]
    list_filter = ["status", "issue_type", "warehouse"]
    search_fields = ["issue_number", "reference"]
    date_hierarchy = "issue_date"
    inlines = [StockIssueLineInline]
    readonly_fields = ["issue_number", "created_at", "updated_at", "posted_date"]


class StockTransferLineInline(admin.TabularInline):
    model = StockTransferLine
    extra = 0
    readonly_fields = ["is_posted", "posted_at"]


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ["transfer_number", "transfer_type", "status", "from_warehouse", "to_warehouse", "transfer_date"]
    list_filter = ["status", "transfer_type", "from_warehouse", "to_warehouse"]
    search_fields = ["transfer_number"]
    date_hierarchy = "transfer_date"
    inlines = [StockTransferLineInline]
    readonly_fields = ["transfer_number", "created_at", "updated_at", "posted_date"]


class StockAdjustmentLineInline(admin.TabularInline):
    model = StockAdjustmentLine
    extra = 0
    readonly_fields = ["qty_adjustment", "total_cost", "is_posted", "posted_at"]


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ["adjustment_number", "adjustment_type", "status", "warehouse", "reason", "adjustment_date"]
    list_filter = ["status", "adjustment_type", "warehouse", "reason"]
    search_fields = ["adjustment_number"]
    date_hierarchy = "adjustment_date"
    inlines = [StockAdjustmentLineInline]
    readonly_fields = ["adjustment_number", "created_at", "updated_at", "posted_date"]


# =============================================================================
# PHASE 4: ASSETS
# =============================================================================

class AssetMovementInline(admin.TabularInline):
    model = AssetMovement
    extra = 0
    readonly_fields = ["movement_number", "movement_date", "created_at"]
    ordering = ["-movement_date"]


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ["serial_number", "item", "status", "condition", "current_location", "owner_party"]
    list_filter = ["status", "condition", "quality_status", "owner_party", "warehouse"]
    search_fields = ["serial_number", "asset_tag", "item__code", "manufacturer_serial"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [AssetMovementInline]
    fieldsets = (
        ("Identification", {
            "fields": ("serial_number", "asset_tag", "item")
        }),
        ("Status & Condition", {
            "fields": ("status", "condition", "quality_status")
        }),
        ("Location", {
            "fields": ("current_location", "warehouse")
        }),
        ("Ownership", {
            "fields": ("owner_party", "ownership_type", "custodian_party")
        }),
        ("Financial", {
            "fields": ("acquisition_cost", "current_value", "salvage_value", "depreciation_method", "useful_life_months"),
            "classes": ("collapse",)
        }),
        ("Dates", {
            "fields": ("acquisition_date", "in_service_date", "warranty_expiry", "next_service_date", "disposal_date"),
            "classes": ("collapse",)
        }),
        ("Usage Metrics", {
            "fields": ("total_run_hours", "total_cycles", "total_footage"),
            "classes": ("collapse",)
        }),
        ("Certification", {
            "fields": ("last_inspection_date", "next_inspection_date", "certification_number", "certification_expiry"),
            "classes": ("collapse",)
        }),
        ("Notes", {
            "fields": ("notes", "specifications")
        }),
    )


@admin.register(AssetMovement)
class AssetMovementAdmin(admin.ModelAdmin):
    list_display = ["movement_number", "asset", "movement_type", "movement_date", "from_location", "to_location"]
    list_filter = ["movement_type", "movement_date"]
    search_fields = ["movement_number", "asset__serial_number"]
    date_hierarchy = "movement_date"
    readonly_fields = ["created_at"]


# =============================================================================
# PHASE 5: QC GATES
# =============================================================================

@admin.register(QualityStatusChange)
class QualityStatusChangeAdmin(admin.ModelAdmin):
    list_display = ["change_number", "change_type", "from_status", "to_status", "change_date", "lot", "asset"]
    list_filter = ["change_type", "from_status", "to_status"]
    search_fields = ["change_number", "lot__lot_number", "asset__serial_number"]
    date_hierarchy = "change_date"
    readonly_fields = ["change_number", "change_date"]


# =============================================================================
# PHASE 6: RESERVATIONS
# =============================================================================

@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ["reservation_number", "item", "qty_reserved", "qty_issued", "status", "reservation_type", "required_date"]
    list_filter = ["status", "reservation_type"]
    search_fields = ["reservation_number", "item__code"]
    readonly_fields = ["reservation_number", "created_at", "updated_at"]


# =============================================================================
# PHASE 7: BOM
# =============================================================================

class BOMLineInline(admin.TabularInline):
    model = BOMLine
    extra = 1
    readonly_fields = ["extended_cost"]


@admin.register(BillOfMaterial)
class BillOfMaterialAdmin(admin.ModelAdmin):
    list_display = ["bom_code", "parent_item", "version", "bom_type", "status", "material_cost", "total_cost"]
    list_filter = ["status", "bom_type"]
    search_fields = ["bom_code", "parent_item__code", "name"]
    inlines = [BOMLineInline]
    readonly_fields = ["material_cost", "total_cost", "created_at", "updated_at"]
    actions = ["recalculate_costs"]

    @admin.action(description="Recalculate costs")
    def recalculate_costs(self, request, queryset):
        for bom in queryset:
            bom.recalculate_costs()
        self.message_user(request, f"Recalculated costs for {queryset.count()} BOMs")


# =============================================================================
# PHASE 8: CYCLE COUNT
# =============================================================================

class CycleCountLineInline(admin.TabularInline):
    model = CycleCountLine
    extra = 0
    readonly_fields = ["qty_variance", "variance_value"]


@admin.register(CycleCountPlan)
class CycleCountPlanAdmin(admin.ModelAdmin):
    list_display = ["plan_code", "name", "plan_type", "status", "warehouse", "start_date"]
    list_filter = ["status", "plan_type", "warehouse"]
    search_fields = ["plan_code", "name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(CycleCountSession)
class CycleCountSessionAdmin(admin.ModelAdmin):
    list_display = ["session_number", "session_date", "status", "warehouse", "total_items", "items_variance", "total_variance_value"]
    list_filter = ["status", "warehouse"]
    search_fields = ["session_number"]
    date_hierarchy = "session_date"
    inlines = [CycleCountLineInline]
    readonly_fields = ["session_number", "created_at", "updated_at"]
