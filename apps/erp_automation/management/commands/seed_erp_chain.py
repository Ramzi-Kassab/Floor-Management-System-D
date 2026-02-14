"""
Seed 13 sub-workflows + 1 chain for the complete "ARAMCO FC Repair: Full ERP Flow".

Based on 4 live D365 recordings (sessions pk=13-16) on prod.alrushaid.net.
Covers the COMPLETE item creation + BOM + Route + Release + Movement Journal flow.

  WF-0:  Open Browser & Login (6 steps)
  WF-1:  Navigate to Released Products (3 steps)
  WF-2:  Create Released Product (~18 steps, account-branched)
  WF-2B: Capture Item Number (3 steps) -- reads D365-generated Item # into context
  WF-3:  Set Product Dimensions (14 steps)
  WF-4:  Create Product Variants (6 steps)
  WF-5:  Create BOM Version + First Approval (14 steps)
  WF-6:  Create BOM (Copy Dialog) (8 steps)
  WF-7:  Enter BOM Lines (36 steps) -- up to 8 BOM lines, continue_on_error
  WF-8:  Approve BOM + Activate Version (8 steps)
  WF-9:  Route Registration (14 steps)
  WF-10: Release Product (4 steps)
  WF-11: Movement Journal (20 steps)

Usage:
    python manage.py seed_erp_chain
    python manage.py seed_erp_chain --force   # Delete existing and recreate
    python manage.py seed_erp_chain --dry-run  # Preview without changes
"""
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


# =============================================================================
# LOCATOR DEFINITIONS
# =============================================================================
# Each locator: {name, desc, ctx, mode, strategies: [(type, value, priority)]}

LOCATORS = {
    # -------------------------------------------------------------------------
    # LOGIN (handled by executor ADFS, but locators needed for explicit steps)
    # -------------------------------------------------------------------------
    "login_user": {
        "name": "login_user_field",
        "desc": "ADFS Login username input",
        "ctx": "ADFS Login",
        "mode": "standard_input",
        "strategies": [
            ("id", "userNameInput", 0),
            ("xpath", "//*[@id='userNameInput']", 5),
        ],
    },
    "login_pass": {
        "name": "login_pass_field",
        "desc": "ADFS Login password input",
        "ctx": "ADFS Login",
        "mode": "standard_input",
        "strategies": [
            ("id", "passwordInput", 0),
            ("xpath", "//*[@id='passwordInput']", 5),
        ],
    },
    "login_submit": {
        "name": "login_submit_button",
        "desc": "ADFS Login submit button",
        "ctx": "ADFS Login",
        "mode": "dialog_button",
        "strategies": [
            ("id", "submitButton", 0),
            ("xpath", "//*[@id='submitButton']", 5),
        ],
    },

    # -------------------------------------------------------------------------
    # NAVIGATION
    # -------------------------------------------------------------------------
    "favorites": {
        "name": "d365_favorites",
        "desc": "D365 Favorites navigation panel",
        "ctx": "D365 Home",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[@id="navPaneFavoritesID"]/span[2]', 0),
            ("id", "navPaneFavoritesID", 5),
        ],
    },
    "released_products_link": {
        "name": "d365_released_products_link",
        "desc": "Released Products link in favorites",
        "ctx": "D365 Favorites",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//a[@class='modulesPane-linkText' and text()='Released products']", 0),
            ("text", "Released products", 5),
        ],
    },

    # -------------------------------------------------------------------------
    # NEW RELEASED PRODUCT DIALOG
    # -------------------------------------------------------------------------
    "new_released_product_btn": {
        "name": "d365_new_released_product_btn",
        "desc": "New button on Released Products grid",
        "ctx": "Released Products",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//*[contains(@id, 'ecoresproductdetailsextendedgrid') and contains(@id, 'SystemDefinedNewButton_label')]", 0),
        ],
    },
    "product_subtype_dropdown": {
        "name": "d365_product_subtype_dropdown",
        "desc": "Product subtype dropdown button in new product dialog",
        "ctx": "New Released Product",
        "mode": "custom_dropdown",
        "strategies": [
            ("xpath", "/html/body/div[2]/div/div[7]/div[2]/div/div[5]/div/div[1]/div[2]/div[1]/div[2]/div/div/div[2]/div", 0),
        ],
    },
    "product_master_option": {
        "name": "d365_product_master_option",
        "desc": "Product Master option in subtype dropdown",
        "ctx": "New Released Product",
        "mode": "custom_dropdown",
        "strategies": [
            ("xpath", "/html/body/ul/li[2]", 0),
        ],
    },

    # -------------------------------------------------------------------------
    # ITEM GROUP (single locator, value varies by account)
    # -------------------------------------------------------------------------
    "item_group_field": {
        "name": "d365_item_group_field",
        "desc": "Item Group input field (value varies by account)",
        "ctx": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("name", "ItemGroupId", 0),
            ("xpath", '//*[@name="ItemGroupId"]', 5),
        ],
    },

    # -------------------------------------------------------------------------
    # PRODUCT DETAIL FIELDS
    # -------------------------------------------------------------------------
    "model_group": {
        "name": "d365_item_model_group",
        "desc": "Item Model Group input (combobox, value: Repair Bit)",
        "ctx": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductCreate_") and contains(@id, "ModelGroupId_input")]', 0),
        ],
    },
    "storage_dim_group": {
        "name": "d365_storage_dimension_group",
        "desc": "Storage Dimension Group input (value: SWL)",
        "ctx": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductCreate_") and contains(@id, "StorageDimensionGroup_Name_input")]', 0),
        ],
    },
    "tracking_dim_group": {
        "name": "d365_tracking_dimension_group",
        "desc": "Tracking Dimension Group input (value: Serial)",
        "ctx": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductCreate_") and contains(@id, "TrackingDimensionGroup_Name_input")]', 0),
        ],
    },
    "search_name": {
        "name": "d365_search_name",
        "desc": "Search Name input (value: Serial Number)",
        "ctx": "New Released Product",
        "mode": "standard_input",
        "strategies": [
            ("name", "Identification_SearchName", 0),
            ("xpath", '//input[@name="Identification_SearchName"]', 5),
        ],
    },
    "product_dim_group": {
        "name": "d365_product_dimension_group",
        "desc": "Product Dimension Group input (value: CSCS)",
        "ctx": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("name", "ProductDimensionGroup_Name", 0),
            ("xpath", '//*[@name="ProductDimensionGroup_Name"]', 5),
        ],
    },
    "product_name": {
        "name": "d365_product_name",
        "desc": "Product Name input (composite: WO Serial Size Type MAT)",
        "ctx": "New Released Product",
        "mode": "standard_input",
        "strategies": [
            ("name", "Identification_Name", 0),
            ("xpath", '//input[@name="Identification_Name"]', 5),
        ],
    },
    "inventory_unit": {
        "name": "d365_inventory_unit",
        "desc": "Inventory Unit of Measure input (value: ea)",
        "ctx": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductCreate_") and contains(@id, "InventUnitId_input")]', 0),
        ],
    },
    "purchase_unit": {
        "name": "d365_purchase_unit",
        "desc": "Purchase Unit of Measure input (value: ea)",
        "ctx": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductCreate_") and contains(@id, "PurchUnitId_input")]', 0),
        ],
    },
    "sales_unit": {
        "name": "d365_sales_unit",
        "desc": "Sales Unit of Measure input (value: ea)",
        "ctx": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductCreate_") and contains(@id, "SalesUnitId_input")]', 0),
        ],
    },
    "bom_unit": {
        "name": "d365_bom_unit",
        "desc": "BOM Unit of Measure input (value: ea)",
        "ctx": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductCreate_") and contains(@id, "BOMUnitId_input")]', 0),
            ("name", "BOMUnitId", 5),
        ],
    },

    # -------------------------------------------------------------------------
    # OK BUTTONS
    # -------------------------------------------------------------------------
    "ok_btn_released_product": {
        "name": "d365_ok_button_released_product",
        "desc": "OK button on Released Product creation dialog",
        "ctx": "New Released Product",
        "mode": "dialog_button",
        "strategies": [
            ("name", "OKButton", 0),
            ("xpath", "//button[@name='OKButton']", 5),
        ],
    },
    "ok_btn_attribute": {
        "name": "d365_ok_button_attribute",
        "desc": "OK button on attribute assignment dialog",
        "ctx": "Released Product Detail",
        "mode": "dialog_button",
        "strategies": [
            ("name", "OkButton", 0),
            ("xpath", "//button[@name='OkButton']", 5),
        ],
    },

    # -------------------------------------------------------------------------
    # SERIAL ID & ITEM NUMBER (post-creation)
    # -------------------------------------------------------------------------
    "old_serial_id": {
        "name": "d365_old_serial_id",
        "desc": "Old Serial ID field on released product detail",
        "ctx": "Released Product Detail",
        "mode": "standard_input",
        "strategies": [
            ("name", "InventTable_Inf_InventSerialId", 0),
            ("xpath", "//input[@name='InventTable_Inf_InventSerialId']", 5),
        ],
    },
    "item_number_grid": {
        "name": "d365_item_number_grid",
        "desc": "Item Number field on Released Product detail (read-only, D365-generated)",
        "ctx": "Released Product Detail",
        "mode": "auto",
        "strategies": [
            ("xpath", '//*[contains(@id, "InventTable_ItemId") and contains(@id, "input")]', 0),
            ("name", "InventTable_ItemId", 5),
        ],
    },

    # -------------------------------------------------------------------------
    # PRODUCT DIMENSIONS
    # -------------------------------------------------------------------------
    "product_dimensions_link": {
        "name": "d365_product_dimensions_link",
        "desc": "Product Dimensions link/button on product detail",
        "ctx": "Released Product Detail",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//span[contains(@aria-describedby, "EcoResProductMasterDimensionPerCompany_helptext")]', 0),
        ],
    },
    "dim_config_tab": {
        "name": "d365_dim_config_tab",
        "desc": "Configuration tab in product dimensions dialog",
        "ctx": "Product Dimensions",
        "mode": "tab_header",
        "strategies": [
            ("xpath", '//li[contains(@id, "TabPageConfigurations_header")]', 0),
        ],
    },
    "dim_config_new": {
        "name": "d365_dim_config_new_btn",
        "desc": "New button on Configuration dimension tab",
        "ctx": "Product Dimensions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductMasterDimension") and contains(@id, "NewConfiguration")]/div/span[1]', 0),
        ],
    },
    "dim_config_name": {
        "name": "d365_dim_config_name_input",
        "desc": "Configuration name input (value: {{BODY_MATERIAL}} = MB)",
        "ctx": "Product Dimensions",
        "mode": "standard_input",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResConfiguration_Name_") and contains(@id, "_0_0_input")]', 0),
        ],
    },
    "dim_size_tab": {
        "name": "d365_dim_size_tab",
        "desc": "Size tab in product dimensions dialog",
        "ctx": "Product Dimensions",
        "mode": "tab_header",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductMasterDimension") and contains(@id, "TabPageSizes_header")]', 0),
        ],
    },
    "dim_size_new": {
        "name": "d365_dim_size_new_btn",
        "desc": "New button on Size dimension tab",
        "ctx": "Product Dimensions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductMasterDimension") and contains(@id, "NewSize_label")]', 0),
        ],
    },
    "dim_size_name": {
        "name": "d365_dim_size_name_input",
        "desc": "Size name input (value: {{SIZE}})",
        "ctx": "Product Dimensions",
        "mode": "standard_input",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResSize_Name") and contains(@id, "0_0_input")]', 0),
        ],
    },
    "dim_color_tab": {
        "name": "d365_dim_color_tab",
        "desc": "Color tab in product dimensions dialog (Color = L5 MAT FULL)",
        "ctx": "Product Dimensions",
        "mode": "tab_header",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductMasterDimension") and contains(@id, "TabPageColors_header")]', 0),
        ],
    },
    "dim_color_new": {
        "name": "d365_dim_color_new_btn",
        "desc": "New button on Color dimension tab",
        "ctx": "Product Dimensions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductMasterDimension") and contains(@id, "NewColor_label")]', 0),
        ],
    },
    "dim_color_name": {
        "name": "d365_dim_color_name_input",
        "desc": "Color name input (value: {{L5_MAT_FULL}})",
        "ctx": "Product Dimensions",
        "mode": "standard_input",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResColor_Name") and contains(@id, "0_0_input")]', 0),
        ],
    },
    "dim_style_tab": {
        "name": "d365_dim_style_tab",
        "desc": "Style tab in product dimensions dialog (Style = TYPE)",
        "ctx": "Product Dimensions",
        "mode": "tab_header",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductMasterDimension") and contains(@id, "TabPageStyles_header")]', 0),
        ],
    },
    "dim_style_new": {
        "name": "d365_dim_style_new_btn",
        "desc": "New button on Style dimension tab",
        "ctx": "Product Dimensions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductMasterDimension") and contains(@id, "NewStyle_label")]', 0),
        ],
    },
    "dim_style_name": {
        "name": "d365_dim_style_name_input",
        "desc": "Style name input (value: {{TYPE}} = SMI type)",
        "ctx": "Product Dimensions",
        "mode": "standard_input",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResStyle_Name") and contains(@id, "0_0_input")]', 0),
        ],
    },
    "close_product_dimensions": {
        "name": "d365_close_product_dimensions",
        "desc": "Close button on product dimensions dialog",
        "ctx": "Product Dimensions",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductMasterDimension") and contains(@id, "SystemDefinedCloseButton")]/div/span[1]', 0),
        ],
    },

    # -------------------------------------------------------------------------
    # PRODUCT VARIANTS
    # -------------------------------------------------------------------------
    "product_variants_btn": {
        "name": "d365_product_variants_btn",
        "desc": "Released Product Variants button on product detail action pane",
        "ctx": "Released Product Detail",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "ecoresproductdetailsextendedgrid") and contains(@id, "EcoResProductVariantsAction_label")]', 0),
        ],
    },
    "variant_suggestions_btn": {
        "name": "d365_variant_suggestions_btn",
        "desc": "Variant Suggestions button on variants page",
        "ctx": "Product Variants",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductVariantsPerCompany") and contains(@id, "EcoResProductVariantPerCompanyMgr_label")]', 0),
        ],
    },
    "suggest_all_btn": {
        "name": "d365_suggest_all_btn",
        "desc": "Suggest All button in variant suggestions dialog",
        "ctx": "Variant Suggestions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductVariantSuggestionsEnhanced") and contains(@id, "SuggestAllButton_label")]', 0),
            ("xpath", '//*[contains(@id, "SuggestButton_label")]', 5),
        ],
    },
    "suggested_variant_checkbox": {
        "name": "d365_suggested_variant_checkbox",
        "desc": "Checkbox for suggested variant in suggestions grid",
        "ctx": "Variant Suggestions",
        "mode": "checkbox_toggle",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResTmpProductModelSuggestions_selected") and contains(@id, "0_0_container")]/div/span', 0),
        ],
    },
    "create_variants_btn": {
        "name": "d365_create_variants_btn",
        "desc": "Create button in variant suggestions dialog (OK/Create)",
        "ctx": "Variant Suggestions",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductVariantSuggestionsEnhanced") and contains(@id, "CommandButtonOk_label")]', 0),
        ],
    },
    "close_variants_page": {
        "name": "d365_close_variants_page",
        "desc": "Close button on product variants page",
        "ctx": "Product Variants",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResProductVariantsPerCompany") and contains(@id, "SystemDefinedCloseButton")]/div/span[1]', 0),
        ],
    },

    # -------------------------------------------------------------------------
    # BOM VERSION (Engineer tab => BOM Versions)
    # -------------------------------------------------------------------------
    "engineer_header_tab": {
        "name": "d365_engineer_header_tab",
        "desc": "Engineer action pane tab on Released Product detail",
        "ctx": "Released Product Detail",
        "mode": "tab_header",
        "strategies": [
            ("xpath", '//*[contains(@id, "ecoresproductdetailsextendedgrid") and contains(@id, "ActionPaneTabEngineer_button")]/span', 0),
        ],
    },
    "bom_versions_btn": {
        "name": "d365_bom_versions_btn",
        "desc": "BOM Versions button under Engineer tab",
        "ctx": "Released Product Detail",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "ecoresproductdetailsextendedgrid") and contains(@id, "BOMConsistOfAction_label")]', 0),
        ],
    },
    "new_bom_flyout_btn": {
        "name": "d365_new_bom_flyout_btn",
        "desc": "New flyout menu button on BOM Versions form",
        "ctx": "BOM Versions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMConsistOf") and contains(@id, "NewFormMenuButton_label")]', 0),
        ],
    },
    "create_bom_version_label": {
        "name": "d365_create_bom_version_label",
        "desc": "Create BOM Version option in New flyout menu",
        "ctx": "BOM Versions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMConsistOf") and contains(@id, "CreateBOMVersion_label")]', 0),
        ],
    },
    "create_bom_label": {
        "name": "d365_create_bom_label",
        "desc": "Create BOM option in New flyout menu",
        "ctx": "BOM Versions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMConsistOf") and contains(@id, "CreateBOM_label")]', 0),
            ("text", "Create BOM", 5),
        ],
    },

    # --- BOM Version Name Lookup ---
    "bom_version_name_dd": {
        "name": "d365_bom_version_name_dd",
        "desc": "BOM Version Name dropdown (lookup button)",
        "ctx": "BOM Versions",
        "mode": "custom_dropdown",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMConsistOf") and contains(@id, "General_BOMVersion_BOMId")]/div/div', 0),
        ],
    },
    "bom_switch_view_dd": {
        "name": "d365_bom_switch_view_dd",
        "desc": "Switch View dropdown in BOM lookup dialog",
        "ctx": "BOM Lookup",
        "mode": "custom_dropdown",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMIdLookup") and contains(@id, "switchView")]/div/div[2]/div', 0),
        ],
    },
    "bom_switch_view_all": {
        "name": "d365_bom_switch_view_all_option",
        "desc": "'All bills of materials' option in Switch View dropdown",
        "ctx": "BOM Lookup",
        "mode": "custom_dropdown",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMIdLookup") and contains(@id, "switchView_list_item1")]', 0),
        ],
    },
    "bom_table_name_header": {
        "name": "d365_bom_table_name_header",
        "desc": "BOM table Name column header (for opening filter)",
        "ctx": "BOM Lookup",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMTableAll_Name") and contains(@id, "0_header")]', 0),
        ],
    },
    "bom_table_name_filter": {
        "name": "d365_bom_table_name_filter_input",
        "desc": "Filter input for BOM Name column",
        "ctx": "BOM Lookup",
        "mode": "standard_input",
        "strategies": [
            ("xpath", '//*[contains(@id, "FilterField_BOMTableAll_Name_Name_Input") and contains(@id, "0_input")]', 0),
        ],
    },
    "bom_apply_filters": {
        "name": "d365_bom_table_apply_filters",
        "desc": "Apply Filters button on BOM table",
        "ctx": "BOM Lookup",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMTableAll_Name") and contains(@id, "ApplyFilters")]', 0),
        ],
    },
    "bom_name_line_select": {
        "name": "d365_bom_name_line_select",
        "desc": "First BOM name row in filtered table (select it)",
        "ctx": "BOM Lookup",
        "mode": "auto",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMTableAll_Name") and contains(@id, "0_0_input")]', 0),
        ],
    },

    # --- BOM Version Action Pane ---
    "version_action_pane_tab": {
        "name": "d365_version_action_pane_tab",
        "desc": "Version action pane tab on BOM Consist Of form",
        "ctx": "BOM Versions",
        "mode": "tab_header",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMConsistOf") and contains(@id, "BOMVersionActionPaneTab_button")]/span', 0),
        ],
    },
    "bom_version_approve_btn": {
        "name": "d365_bom_version_approve_btn",
        "desc": "BOM Version Approve button",
        "ctx": "BOM Versions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMConsistOf") and contains(@id, "BOMVersionApprove_label")]', 0),
        ],
    },
    "approve_dialog_ok": {
        "name": "d365_approve_dialog_ok",
        "desc": "OK button on Approve dialog (generic, used for BOM and Route approval)",
        "ctx": "Approve Dialog",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "Dialog") and contains(@id, "OkButton")]', 0),
            ("name", "OkButton", 5),
        ],
    },

    # -------------------------------------------------------------------------
    # CREATE BOM DIALOG (Copy flow)
    # -------------------------------------------------------------------------
    "create_bom_name_input": {
        "name": "d365_create_bom_name_input",
        "desc": "BOM Name field in Create BOM dialog",
        "ctx": "Create BOM Dialog",
        "mode": "standard_input",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMCreate") and contains(@id, "Name_input")]', 0),
            ("name", "Name", 5),
        ],
    },
    "create_bom_copy_toggle": {
        "name": "d365_create_bom_copy_toggle",
        "desc": "Copy checkbox/toggle in Create BOM dialog",
        "ctx": "Create BOM Dialog",
        "mode": "checkbox_toggle",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMCreate") and contains(@id, "CopyBOM")]//span', 0),
            ("xpath", '//*[contains(@id, "CopyBOM")]', 5),
        ],
    },
    "create_bom_site_dd": {
        "name": "d365_create_bom_site_dd",
        "desc": "Site dropdown input in Create BOM dialog",
        "ctx": "Create BOM Dialog",
        "mode": "combobox",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMCreate") and contains(@id, "InventSiteId_input")]', 0),
        ],
    },
    "create_bom_site_option": {
        "name": "d365_create_bom_site_option",
        "desc": "ARDT Site option row in Site dropdown list",
        "ctx": "Create BOM Dialog",
        "mode": "custom_dropdown",
        "strategies": [
            ("xpath", '//tr[contains(@id, "InventSiteId") and contains(@id, "grid_0_0")]', 0),
            ("xpath", '//td[text()="ARDT Site"]', 5),
        ],
    },
    "create_bom_ok": {
        "name": "d365_create_bom_ok",
        "desc": "OK button on Create BOM dialog",
        "ctx": "Create BOM Dialog",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMCreate") and contains(@id, "OkButton")]', 0),
        ],
    },

    # --- BOM Route Copy dialog (FromConfigId selection) ---
    "from_config_id_dd": {
        "name": "d365_from_config_id_dd",
        "desc": "FromConfigId dropdown in BOM/Route Copy dialog",
        "ctx": "BOM Route Copy",
        "mode": "combobox",
        "strategies": [
            ("name", "FromConfigId", 0),
            ("xpath", '//*[@name="FromConfigId"]', 5),
        ],
    },
    "bom_route_copy_ok": {
        "name": "d365_bom_route_copy_ok",
        "desc": "OK button on BOM/Route Copy dialog",
        "ctx": "BOM Route Copy",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMRouteCopyDialog") and contains(@id, "Ok")]', 0),
            ("name", "OkButton", 5),
        ],
    },

    # -------------------------------------------------------------------------
    # BOM LINES (BOM Table grid)
    # -------------------------------------------------------------------------
    "bom_line_delete_btn": {
        "name": "d365_bom_line_delete_btn",
        "desc": "Delete button for BOM line in BOM Table grid",
        "ctx": "BOM Table",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMTable") and contains(@id, "SystemDefinedDeleteButton_label")]', 0),
        ],
    },
    "bom_line_delete_yes": {
        "name": "d365_bom_line_delete_yes",
        "desc": "Yes button on delete confirmation dialog",
        "ctx": "BOM Table",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "Dialog") and contains(@id, "Yes")]', 0),
            ("name", "Yes", 5),
        ],
    },
    "bom_line_new_btn": {
        "name": "d365_bom_line_new_btn",
        "desc": "New BOM Line button in BOM Table grid",
        "ctx": "BOM Table",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMTable") and contains(@id, "SystemDefinedNewButton_label")]', 0),
        ],
    },
    "bom_line_item_number": {
        "name": "d365_bom_line_item_number",
        "desc": "Item Number field on BOM line row",
        "ctx": "BOM Table",
        "mode": "combobox",
        "strategies": [
            ("name", "BOM_ItemId", 0),
            ("xpath", '//*[@name="BOM_ItemId"]', 5),
        ],
    },
    "bom_line_item_confirm": {
        "name": "d365_bom_line_item_confirm",
        "desc": "Click to confirm item lookup (search name / grid row)",
        "ctx": "BOM Table",
        "mode": "auto",
        "strategies": [
            ("name", "BOM_ItemName", 0),
            ("xpath", '//*[@name="BOM_ItemName"]', 5),
        ],
    },
    "bom_line_quantity": {
        "name": "d365_bom_line_quantity",
        "desc": "Quantity field on BOM line row",
        "ctx": "BOM Table",
        "mode": "standard_input",
        "strategies": [
            ("name", "BOM_BOMQty", 0),
            ("xpath", '//*[@name="BOM_BOMQty"]', 5),
        ],
    },

    # --- BOM Approval from BOM Table ---
    "bom_table_action_tab": {
        "name": "d365_bom_table_action_tab",
        "desc": "BOM action pane tab on BOM Table form",
        "ctx": "BOM Table",
        "mode": "tab_header",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMTable") and contains(@id, "ActionPaneHeaderBOM_button")]/span', 0),
        ],
    },
    "bom_approve_btn": {
        "name": "d365_bom_approve_btn",
        "desc": "BOM Approve button on BOM Table",
        "ctx": "BOM Table",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMTable") and contains(@id, "BOMApprove_label")]', 0),
        ],
    },

    # -------------------------------------------------------------------------
    # BOM VERSION ACTIVATE
    # -------------------------------------------------------------------------
    "bom_version_activate_btn": {
        "name": "d365_bom_version_activate_btn",
        "desc": "Activate button on BOM Version",
        "ctx": "BOM Versions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMConsistOf") and contains(@id, "BOMVersionActivate_label")]', 0),
        ],
    },
    "close_bom_consist_of": {
        "name": "d365_close_bom_consist_of",
        "desc": "Close / Back button on BOM Consist Of page",
        "ctx": "BOM Versions",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "BOMConsistOf") and contains(@id, "SystemDefinedCloseButton")]/div/span[1]', 0),
        ],
    },

    # -------------------------------------------------------------------------
    # ROUTE REGISTRATION
    # -------------------------------------------------------------------------
    "route_table_link": {
        "name": "d365_route_table_link",
        "desc": "Route Table link in favorites/navigation",
        "ctx": "D365 Favorites",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//a[@class='modulesPane-linkText' and contains(text(), 'Route')]", 0),
            ("text", "Routes", 5),
        ],
    },
    "route_number_header": {
        "name": "d365_route_number_header",
        "desc": "Route Number column header for filter",
        "ctx": "Route Table",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "RouteTable_RouteId") and contains(@id, "header")]', 0),
        ],
    },
    "route_number_filter": {
        "name": "d365_route_number_filter_input",
        "desc": "Route Number filter input field",
        "ctx": "Route Table",
        "mode": "standard_input",
        "strategies": [
            ("xpath", '//*[contains(@id, "FilterField_RouteTable_RouteId") and contains(@id, "input")]', 0),
        ],
    },
    "route_apply_filters": {
        "name": "d365_route_apply_filters",
        "desc": "Apply Filters button on Route table",
        "ctx": "Route Table",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "RouteTable_RouteId") and contains(@id, "ApplyFilters")]', 0),
        ],
    },
    "route_row_select": {
        "name": "d365_route_row_select",
        "desc": "First Route row in filtered table",
        "ctx": "Route Table",
        "mode": "auto",
        "strategies": [
            ("xpath", '//*[contains(@id, "RouteTable_RouteId") and contains(@id, "0_0")]', 0),
        ],
    },
    "route_item_number": {
        "name": "d365_route_item_number",
        "desc": "Item Number field on Route Version",
        "ctx": "Route Table",
        "mode": "combobox",
        "strategies": [
            ("name", "RouteVersion_ItemId", 0),
            ("xpath", '//*[@name="RouteVersion_ItemId"]', 5),
        ],
    },
    "route_config_dd": {
        "name": "d365_route_config_dd",
        "desc": "Config dropdown on Route Version",
        "ctx": "Route Table",
        "mode": "combobox",
        "strategies": [
            ("name", "RouteVersion_ConfigId", 0),
            ("xpath", '//*[@name="RouteVersion_ConfigId"]', 5),
        ],
    },
    "route_site_dd": {
        "name": "d365_route_site_dd",
        "desc": "Site dropdown on Route Version",
        "ctx": "Route Table",
        "mode": "combobox",
        "strategies": [
            ("name", "RouteVersion_InventSiteId", 0),
            ("xpath", '//*[@name="RouteVersion_InventSiteId"]', 5),
        ],
    },
    "route_version_approve_btn": {
        "name": "d365_route_version_approve_btn",
        "desc": "Approve button on Route Version",
        "ctx": "Route Table",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "RouteTable") and contains(@id, "RouteVersionApprove_label")]', 0),
        ],
    },
    "route_version_activate_btn": {
        "name": "d365_route_version_activate_btn",
        "desc": "Activate button on Route Version",
        "ctx": "Route Table",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "RouteTable") and contains(@id, "RouteVersionActivate_label")]', 0),
        ],
    },

    # -------------------------------------------------------------------------
    # RELEASE PRODUCT
    # -------------------------------------------------------------------------
    "release_products_link": {
        "name": "d365_release_products_link",
        "desc": "Release Products link in favorites/navigation",
        "ctx": "D365 Favorites",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//a[@class='modulesPane-linkText' and contains(text(), 'Release')]", 0),
            ("text", "Release product variants", 5),
        ],
    },
    "release_item_number": {
        "name": "d365_release_item_number",
        "desc": "Item Number field on Release Products form",
        "ctx": "Release Products",
        "mode": "combobox",
        "strategies": [
            ("name", "EcoResReleasedProductVariant_ItemId", 0),
            ("xpath", '//*[@name="EcoResReleasedProductVariant_ItemId"]', 5),
        ],
    },
    "release_ok_btn": {
        "name": "d365_release_ok_btn",
        "desc": "OK/Release button on Release Products form",
        "ctx": "Release Products",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "EcoResReleasedProduct") and contains(@id, "OkButton")]', 0),
            ("name", "OkButton", 5),
        ],
    },

    # -------------------------------------------------------------------------
    # MOVEMENT JOURNAL
    # -------------------------------------------------------------------------
    "movement_journal_link": {
        "name": "d365_movement_journal_link",
        "desc": "Movement Journal link in favorites/navigation",
        "ctx": "D365 Favorites",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//a[@class='modulesPane-linkText' and contains(text(), 'Movement')]", 0),
            ("text", "Movement", 5),
        ],
    },
    "journal_new_btn": {
        "name": "d365_journal_new_btn",
        "desc": "New button on Movement Journal list",
        "ctx": "Movement Journal",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "InventJournalTableMovement") and contains(@id, "SystemDefinedNewButton_label")]', 0),
        ],
    },
    "journal_name_dd": {
        "name": "d365_journal_name_dd",
        "desc": "Journal Name dropdown/lookup",
        "ctx": "Movement Journal",
        "mode": "combobox",
        "strategies": [
            ("name", "Overview_JournalNameId", 0),
            ("xpath", '//*[@name="Overview_JournalNameId"]', 5),
        ],
    },
    "journal_name_row": {
        "name": "d365_journal_name_row",
        "desc": "Journal Name lookup row (ARAMCO Repair journal)",
        "ctx": "Movement Journal",
        "mode": "auto",
        "strategies": [
            ("xpath", '//*[contains(@id, "InventJournalName_JournalNameId") and contains(@id, "0_0")]', 0),
        ],
    },
    "journal_warehouse": {
        "name": "d365_journal_warehouse",
        "desc": "Default Warehouse field on journal header",
        "ctx": "Movement Journal",
        "mode": "combobox",
        "strategies": [
            ("name", "Overview_InventLocationId", 0),
            ("xpath", '//*[@name="Overview_InventLocationId"]', 5),
        ],
    },
    "journal_warehouse_row": {
        "name": "d365_journal_warehouse_row",
        "desc": "Warehouse lookup row selection",
        "ctx": "Movement Journal",
        "mode": "auto",
        "strategies": [
            ("xpath", '//*[contains(@id, "InventLocation_InventLocationId") and contains(@id, "0_0")]', 0),
        ],
    },
    "journal_description": {
        "name": "d365_journal_description",
        "desc": "Description field on journal header",
        "ctx": "Movement Journal",
        "mode": "standard_input",
        "strategies": [
            ("name", "Overview_Description", 0),
            ("xpath", '//*[@name="Overview_Description"]', 5),
        ],
    },
    "journal_ok_btn": {
        "name": "d365_journal_ok_btn",
        "desc": "OK button to create journal",
        "ctx": "Movement Journal",
        "mode": "dialog_button",
        "strategies": [
            ("name", "OkButton", 0),
            ("xpath", "//button[@name='OkButton']", 5),
        ],
    },
    "journal_lines_btn": {
        "name": "d365_journal_lines_btn",
        "desc": "Journal Lines button to enter lines",
        "ctx": "Movement Journal",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "InventJournalTableMovement") and contains(@id, "ButtonLines_label")]', 0),
        ],
    },
    "journal_line_item_number": {
        "name": "d365_journal_line_item_number",
        "desc": "Item Number field on journal line",
        "ctx": "Journal Lines",
        "mode": "combobox",
        "strategies": [
            ("name", "InventJournalTrans_ItemId", 0),
            ("xpath", '//*[@name="InventJournalTrans_ItemId"]', 5),
        ],
    },
    "journal_line_config_dd": {
        "name": "d365_journal_line_config_dd",
        "desc": "Config dimension dropdown on journal line",
        "ctx": "Journal Lines",
        "mode": "combobox",
        "strategies": [
            ("name", "inventDimCombinationRecId_InventoryDimension1_ConfigId", 0),
        ],
    },
    "journal_line_serial_dd": {
        "name": "d365_journal_line_serial_dd",
        "desc": "Serial Number field on journal line",
        "ctx": "Journal Lines",
        "mode": "combobox",
        "strategies": [
            ("name", "inventDimCombinationRecId_InventoryDimension1_InventSerialId", 0),
        ],
    },
    "journal_line_new_serial_btn": {
        "name": "d365_journal_line_new_serial_btn",
        "desc": "New Serial Number button (opens serial form)",
        "ctx": "Journal Lines",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "InventSerial") and contains(@id, "SystemDefinedNewButton")]', 0),
        ],
    },
    "journal_serial_input": {
        "name": "d365_journal_serial_input",
        "desc": "Serial Number input field on serial form",
        "ctx": "Serial Number Form",
        "mode": "standard_input",
        "strategies": [
            ("name", "InventSerial_InventSerialId", 0),
            ("xpath", '//*[@name="InventSerial_InventSerialId"]', 5),
        ],
    },
    "close_serial_form": {
        "name": "d365_close_serial_form",
        "desc": "Close button on serial number form",
        "ctx": "Serial Number Form",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "InventSerial") and contains(@id, "SystemDefinedCloseButton")]/div/span[1]', 0),
        ],
    },
    "journal_post_btn": {
        "name": "d365_journal_post_btn",
        "desc": "Post button on journal",
        "ctx": "Journal Lines",
        "mode": "nav_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "InventJournalMovement") and contains(@id, "PostJournal_label")]', 0),
        ],
    },
    "journal_post_ok": {
        "name": "d365_journal_post_ok",
        "desc": "OK button on Post confirmation dialog",
        "ctx": "Journal Lines",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "Dialog") and contains(@id, "OkButton")]', 0),
            ("name", "OkButton", 5),
        ],
    },

    # -------------------------------------------------------------------------
    # GENERIC CLOSE / BACK
    # -------------------------------------------------------------------------
    "generic_close_btn": {
        "name": "d365_generic_close_btn",
        "desc": "Generic Close/Back button (SystemDefinedCloseButton)",
        "ctx": "D365 Global",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", '//*[contains(@id, "SystemDefinedCloseButton")]/div/span[1]', 0),
        ],
    },

    # -------------------------------------------------------------------------
    # ERROR DETECTION
    # -------------------------------------------------------------------------
    "error_message_bar": {
        "name": "d365_error_message_bar",
        "desc": "D365 error message bar",
        "ctx": "D365 Global",
        "mode": "auto",
        "strategies": [
            ("css", "span.messageBar-message", 0),
            ("xpath", "//span[@class='messageBar-message']", 5),
        ],
    },
    "error_message_close": {
        "name": "d365_error_message_close_btn",
        "desc": "Close button for error message bar",
        "ctx": "D365 Global",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", "//button[@aria-label='Close' and contains(@class, 'messageBar-closeIcon')]", 0),
        ],
    },
}


# =============================================================================
# WORKFLOW DEFINITIONS
# =============================================================================
# Each step: (order, name, action_type, locator_key, value_source, extra_kwargs)
# value_source: None, "static:X", "template:{{X}}", "field:X"

WORKFLOWS = {
    # =========================================================================
    # WF-0: OPEN BROWSER & LOGIN (6 steps)
    # =========================================================================
    "wf0_login": {
        "name": "WF-0: Open Browser & Login",
        "desc": "Navigate to D365 ERP and authenticate via ADFS login page",
        "condition_field": "",
        "steps": [
            (10, "Navigate to D365", "navigate", None, None,
             {"wait_after": 5000}),
            (11, "Wait for login page", "wait_time", None, "static:3000", {}),
            (12, "Fill Username", "fill", "login_user", "template:{{ERP_USERNAME}}",
             {"wait_after": 500, "interaction_mode": "standard_input"}),
            (13, "Fill Password", "fill", "login_pass", "template:{{ERP_PASSWORD}}",
             {"wait_after": 500, "interaction_mode": "standard_input"}),
            (14, "Click Sign In", "click", "login_submit", None,
             {"wait_after": 5000, "interaction_mode": "dialog_button"}),
            (15, "Wait for D365 home page", "wait_time", None, "static:5000", {}),
        ],
    },

    # =========================================================================
    # WF-1: NAVIGATE TO RELEASED PRODUCTS (3 steps)
    # =========================================================================
    "wf1_navigate": {
        "name": "WF-1: Navigate to Released Products",
        "desc": "Navigate from D365 home to the Released Products list page",
        "condition_field": "",
        "steps": [
            (10, "Click Favorites", "click", "favorites", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),
            (11, "Click Released Products", "click", "released_products_link", None,
             {"wait_after": 10000, "interaction_mode": "nav_button"}),
            (12, "Wait for page load", "wait_time", None, "static:2000", {}),
        ],
    },

    # =========================================================================
    # WF-2: CREATE RELEASED PRODUCT (~18 steps)
    # Removed Product Number (Item # auto-generated by D365)
    # Added BOM Unit field
    # =========================================================================
    "wf2_create_product": {
        "name": "WF-2: Create Released Product",
        "desc": "Create a new Released Product in D365 - Item # auto-generated by D365",
        "condition_field": "FROM",
        "steps": [
            # --- Open dialog ---
            (10, "Click New Released Product", "click", "new_released_product_btn", None,
             {"wait_after": 5000, "interaction_mode": "nav_button"}),
            (11, "Click Product Subtype Dropdown", "click", "product_subtype_dropdown", None,
             {"wait_after": 1000, "interaction_mode": "custom_dropdown"}),
            (12, "Select Product Master", "click", "product_master_option", None,
             {"wait_after": 1000, "interaction_mode": "custom_dropdown"}),

            # --- Item Group (account-branched) ---
            (20, "Fill Item Group (LSTK)", "fill", "item_group_field", "static:RPR-FC-LST",
             {"wait_after": 1000, "interaction_mode": "combobox", "condition_value": "LSTK",
              "press_key_after": "Enter"}),
            (21, "Fill Item Group (RC-LSTK)", "fill", "item_group_field", "static:RPR-RC-LST",
             {"wait_after": 1000, "interaction_mode": "combobox", "condition_value": "RC-LSTK",
              "press_key_after": "Enter"}),
            (22, "Fill Item Group (HALLIBURTON)", "fill", "item_group_field", "static:RPR-FC-HDB",
             {"wait_after": 1000, "interaction_mode": "combobox", "condition_value": "HALLIBURTON",
              "press_key_after": "Enter"}),
            (23, "Fill Item Group (Hal_Regional)", "fill", "item_group_field", "static:RPR-FC-REG",
             {"wait_after": 1000, "interaction_mode": "combobox", "condition_value": "Hal_Regional",
              "press_key_after": "Enter"}),
            (24, "Fill Item Group (ARAMCO)", "fill", "item_group_field", "static:RPR-FC-AR",
             {"wait_after": 1000, "interaction_mode": "combobox", "condition_value": "ARAMCO",
              "press_key_after": "Enter"}),

            # --- Core fields (order matches D365 tab order from recordings) ---
            (30, "Fill Item Model Group", "fill", "model_group", "static:Repair Bit",
             {"wait_after": 1000, "interaction_mode": "combobox", "press_key_after": "Enter"}),
            (31, "Fill Storage Dimension Group", "fill", "storage_dim_group", "static:SWL",
             {"wait_after": 1000, "interaction_mode": "combobox", "press_key_after": "Enter"}),
            (32, "Fill Tracking Dimension Group", "fill", "tracking_dim_group", "static:Serial",
             {"wait_after": 1000, "interaction_mode": "combobox", "press_key_after": "Enter"}),
            (33, "Fill Search Name", "fill", "search_name", "template:{{SERIAL NO}}",
             {"wait_after": 500, "interaction_mode": "standard_input", "clear_before_fill": True}),
            (34, "Fill Product Dimension Group", "fill", "product_dim_group", "static:CSCS",
             {"wait_after": 500, "interaction_mode": "combobox"}),
            (35, "Fill Product Name", "fill", "product_name",
             "template:{{ORDER NO.}} {{SERIAL NO}} {{SIZE}} {{TYPE}} {{MAT NO.}}",
             {"wait_after": 500, "interaction_mode": "standard_input"}),
            (36, "Fill Inventory Unit", "fill", "inventory_unit", "static:ea",
             {"wait_after": 1000, "interaction_mode": "combobox", "press_key_after": "Enter"}),
            (37, "Fill Purchase Unit", "fill", "purchase_unit", "static:ea",
             {"wait_after": 1000, "interaction_mode": "combobox", "press_key_after": "Enter"}),
            (38, "Fill Sales Unit", "fill", "sales_unit", "static:ea",
             {"wait_after": 1000, "interaction_mode": "combobox", "press_key_after": "Enter"}),
            (39, "Fill BOM Unit", "fill", "bom_unit", "static:ea",
             {"wait_after": 1000, "interaction_mode": "combobox", "press_key_after": "Enter"}),

            # --- OK Buttons ---
            (50, "Click OK (Released Product)", "click", "ok_btn_released_product", None,
             {"wait_after": 3000, "interaction_mode": "dialog_button",
              "check_for_errors": True}),
            (51, "Click OK (Attributes)", "click", "ok_btn_attribute", None,
             {"wait_after": 2000, "interaction_mode": "dialog_button",
              "check_for_errors": True}),

            # --- Post-creation: Serial ID ---
            (60, "Fill Old Serial ID", "fill", "old_serial_id", "template:{{SERIAL NO}}",
             {"wait_after": 1000, "interaction_mode": "standard_input",
              "clear_before_fill": True, "continue_on_error": True}),
        ],
    },

    # =========================================================================
    # WF-2B: CAPTURE ITEM NUMBER (3 steps) -- NEW
    # Reads the D365-generated Item # and saves to context_vars["ITEM_NO"]
    # =========================================================================
    "wf2b_capture_item": {
        "name": "WF-2B: Capture Item Number",
        "desc": "Read the D365-generated Item Number from the product detail page",
        "condition_field": "",
        "steps": [
            (10, "Wait for page to settle", "wait_time", None, "static:2000", {}),
            (11, "Read Item Number", "read_value", "item_number_grid", None,
             {"wait_after": 1000, "save_result_as": "ITEM_NO"}),
            (12, "Post-read wait", "wait_time", None, "static:1000", {}),
        ],
    },

    # =========================================================================
    # WF-3: SET PRODUCT DIMENSIONS (14 steps)
    # Config = {{BODY_MATERIAL}} (MB), Color = {{L5_MAT_FULL}} (with M suffix)
    # =========================================================================
    "wf3_dimensions": {
        "name": "WF-3: Set Product Dimensions",
        "desc": "Set Config (BODY_MATERIAL), Size, Color (L5_MAT_FULL), and Style (TYPE)",
        "condition_field": "",
        "steps": [
            (10, "Click Product Dimensions", "click", "product_dimensions_link", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),

            # Config = BODY_MATERIAL (e.g. MB)
            (20, "Click Config Tab", "click", "dim_config_tab", None,
             {"wait_after": 2000, "interaction_mode": "tab_header"}),
            (21, "Click Config New", "click", "dim_config_new", None,
             {"wait_after": 2000, "interaction_mode": "nav_button"}),
            (22, "Fill Config Name", "fill", "dim_config_name", "template:{{BODY_MATERIAL}}",
             {"wait_after": 1000, "interaction_mode": "standard_input", "press_key_after": "Tab"}),

            # Size
            (30, "Click Size Tab", "click", "dim_size_tab", None,
             {"wait_after": 2000, "interaction_mode": "tab_header"}),
            (31, "Click Size New", "click", "dim_size_new", None,
             {"wait_after": 2000, "interaction_mode": "nav_button"}),
            (32, "Fill Size Name", "fill", "dim_size_name", "template:{{SIZE}}",
             {"wait_after": 1000, "interaction_mode": "standard_input", "press_key_after": "Tab"}),

            # Color = L5_MAT_FULL (includes M suffix)
            (40, "Click Color Tab", "click", "dim_color_tab", None,
             {"wait_after": 2000, "interaction_mode": "tab_header"}),
            (41, "Click Color New", "click", "dim_color_new", None,
             {"wait_after": 2000, "interaction_mode": "nav_button"}),
            (42, "Fill Color Name", "fill", "dim_color_name", "template:{{L5_MAT_FULL}}",
             {"wait_after": 1000, "interaction_mode": "standard_input", "press_key_after": "Tab"}),

            # Style = TYPE (SMI type)
            (50, "Click Style Tab", "click", "dim_style_tab", None,
             {"wait_after": 2000, "interaction_mode": "tab_header"}),
            (51, "Click Style New", "click", "dim_style_new", None,
             {"wait_after": 2000, "interaction_mode": "nav_button"}),
            (52, "Fill Style Name", "fill", "dim_style_name", "template:{{TYPE}}",
             {"wait_after": 1000, "interaction_mode": "standard_input", "press_key_after": "Tab"}),

            # Close
            (60, "Close Product Dimensions", "click", "close_product_dimensions", None,
             {"wait_after": 3000, "interaction_mode": "dialog_button"}),
        ],
    },

    # =========================================================================
    # WF-4: CREATE PRODUCT VARIANTS (6 steps) -- SIMPLIFIED
    # Removed "Variant Header" click (not in recordings). Use Suggest All.
    # =========================================================================
    "wf4_variants": {
        "name": "WF-4: Create Product Variants",
        "desc": "Generate and create product variants from dimension combinations",
        "condition_field": "",
        "steps": [
            (10, "Click Released Product Variants", "click", "product_variants_btn", None,
             {"wait_after": 5000, "interaction_mode": "nav_button"}),
            (11, "Click Variant Suggestions", "click", "variant_suggestions_btn", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),
            (12, "Click Suggest All", "click", "suggest_all_btn", None,
             {"wait_after": 5000, "interaction_mode": "nav_button"}),
            (13, "Select Suggested Variant", "click", "suggested_variant_checkbox", None,
             {"wait_after": 2000, "interaction_mode": "checkbox_toggle"}),
            (14, "Click Create Variants", "click", "create_variants_btn", None,
             {"wait_after": 5000, "interaction_mode": "dialog_button",
              "check_for_errors": True}),
            (15, "Close Variants Page", "click", "close_variants_page", None,
             {"wait_after": 3000, "interaction_mode": "dialog_button",
              "continue_on_error": True}),
        ],
    },

    # =========================================================================
    # WF-5: CREATE BOM VERSION + FIRST APPROVAL (14 steps) -- REWRITTEN
    # Engineer tab => BOM Versions => Create BOM Version => lookup BOM => approve
    # =========================================================================
    "wf5_bom_version": {
        "name": "WF-5: Create BOM Version + First Approval",
        "desc": "Create BOM Version, link to existing BOM by MAT NO., approve the version",
        "condition_field": "",
        "steps": [
            (10, "Click Engineer Header Tab", "click", "engineer_header_tab", None,
             {"wait_after": 2000, "interaction_mode": "tab_header"}),
            (11, "Click BOM Versions", "click", "bom_versions_btn", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),
            (12, "Click New Flyout Menu", "click", "new_bom_flyout_btn", None,
             {"wait_after": 2000, "interaction_mode": "nav_button"}),
            (13, "Click Create BOM Version", "click", "create_bom_version_label", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),

            # --- BOM Name Lookup ---
            (14, "Click BOM Version Name Dropdown", "click", "bom_version_name_dd", None,
             {"wait_after": 2000, "interaction_mode": "custom_dropdown"}),
            (15, "Click Switch View Dropdown", "click", "bom_switch_view_dd", None,
             {"wait_after": 2000, "interaction_mode": "custom_dropdown"}),
            (16, "Select All Bills of Materials", "click", "bom_switch_view_all", None,
             {"wait_after": 3000, "interaction_mode": "custom_dropdown"}),
            (17, "Click BOM Name Header (filter)", "click", "bom_table_name_header", None,
             {"wait_after": 1000, "interaction_mode": "nav_button"}),
            (18, "Fill BOM Name Filter", "fill", "bom_table_name_filter", "template:{{MAT NO.}}",
             {"wait_after": 2000, "interaction_mode": "standard_input",
              "press_key_after": "Enter"}),
            (19, "Click Apply Filters", "click", "bom_apply_filters", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),
            (20, "Select BOM Name Line", "click", "bom_name_line_select", None,
             {"wait_after": 2000, "interaction_mode": "auto"}),

            # --- Approve BOM Version (first approval) ---
            (21, "Click Version Action Pane Tab", "click", "version_action_pane_tab", None,
             {"wait_after": 1000, "interaction_mode": "tab_header"}),
            (22, "Click BOM Version Approve", "click", "bom_version_approve_btn", None,
             {"wait_after": 2000, "interaction_mode": "nav_button"}),
            (23, "Click Approve OK", "click", "approve_dialog_ok", None,
             {"wait_after": 3000, "interaction_mode": "dialog_button",
              "check_for_errors": True}),
        ],
    },

    # =========================================================================
    # WF-6: CREATE BOM (COPY DIALOG) (8 steps) -- NEW
    # =========================================================================
    "wf6_create_bom": {
        "name": "WF-6: Create BOM (Copy)",
        "desc": "Create a new BOM using Copy from existing BOM template",
        "condition_field": "",
        "steps": [
            (10, "Click New Flyout Menu", "click", "new_bom_flyout_btn", None,
             {"wait_after": 2000, "interaction_mode": "nav_button"}),
            (11, "Click Create BOM", "click", "create_bom_label", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),
            (12, "Fill BOM Name", "fill", "create_bom_name_input",
             "template:{{L5_MAT_FULL}}-{{SERIAL NO}}",
             {"wait_after": 1000, "interaction_mode": "standard_input",
              "clear_before_fill": True}),
            (13, "Toggle Copy ON", "click", "create_bom_copy_toggle", None,
             {"wait_after": 1000, "interaction_mode": "checkbox_toggle"}),
            (14, "Fill Site (ARDT Site)", "fill", "create_bom_site_dd", "static:ARDT Site",
             {"wait_after": 2000, "interaction_mode": "combobox", "clear_before_fill": True}),
            (15, "Select Site Option", "click", "create_bom_site_option", None,
             {"wait_after": 1000, "interaction_mode": "custom_dropdown"}),
            (16, "Click Create BOM OK", "click", "create_bom_ok", None,
             {"wait_after": 5000, "interaction_mode": "dialog_button",
              "check_for_errors": True}),
            # --- Copy dialog: select FromConfigId = MB ---
            (17, "Select From Config (MB)", "fill", "from_config_id_dd",
             "template:{{BODY_MATERIAL}}",
             {"wait_after": 2000, "interaction_mode": "combobox",
              "press_key_after": "Enter"}),
            (18, "Click BOM Route Copy OK", "click", "bom_route_copy_ok", None,
             {"wait_after": 5000, "interaction_mode": "dialog_button",
              "check_for_errors": True}),
        ],
    },

    # =========================================================================
    # WF-7: ENTER BOM LINES (up to 8 lines x 4 steps + 4 delete overhead)
    # All steps have continue_on_error=True so empty BOM lines are skipped
    # =========================================================================
    "wf7_bom_lines": {
        "name": "WF-7: Enter BOM Lines",
        "desc": "Delete existing lines and enter up to 8 BOM lines from cutter_bom_data",
        "condition_field": "",
        "steps": [
            # --- Delete existing lines (copied from BOM template) ---
            (10, "Delete existing BOM line 1", "click", "bom_line_delete_btn", None,
             {"wait_after": 1000, "interaction_mode": "nav_button", "continue_on_error": True}),
            (11, "Confirm delete 1", "click", "bom_line_delete_yes", None,
             {"wait_after": 1000, "interaction_mode": "dialog_button", "continue_on_error": True}),
            (12, "Delete existing BOM line 2", "click", "bom_line_delete_btn", None,
             {"wait_after": 1000, "interaction_mode": "nav_button", "continue_on_error": True}),
            (13, "Confirm delete 2", "click", "bom_line_delete_yes", None,
             {"wait_after": 1000, "interaction_mode": "dialog_button", "continue_on_error": True}),

            # --- BOM Line 1 ---
            (20, "New BOM Line 1", "click", "bom_line_new_btn", None,
             {"wait_after": 1000, "interaction_mode": "nav_button", "continue_on_error": True}),
            (21, "Fill Item Number 1", "fill", "bom_line_item_number",
             "template:{{BOM_LINE_1_ITEM}}",
             {"wait_after": 1000, "interaction_mode": "combobox", "continue_on_error": True,
              "press_key_after": "Enter"}),
            (22, "Confirm Item 1", "click", "bom_line_item_confirm", None,
             {"wait_after": 500, "interaction_mode": "auto", "continue_on_error": True}),
            (23, "Fill Quantity 1", "fill", "bom_line_quantity",
             "template:{{BOM_LINE_1_QTY}}",
             {"wait_after": 1000, "interaction_mode": "standard_input", "continue_on_error": True,
              "clear_before_fill": True, "press_key_after": "Tab"}),

            # --- BOM Line 2 ---
            (30, "New BOM Line 2", "click", "bom_line_new_btn", None,
             {"wait_after": 1000, "interaction_mode": "nav_button", "continue_on_error": True}),
            (31, "Fill Item Number 2", "fill", "bom_line_item_number",
             "template:{{BOM_LINE_2_ITEM}}",
             {"wait_after": 1000, "interaction_mode": "combobox", "continue_on_error": True,
              "press_key_after": "Enter"}),
            (32, "Confirm Item 2", "click", "bom_line_item_confirm", None,
             {"wait_after": 500, "interaction_mode": "auto", "continue_on_error": True}),
            (33, "Fill Quantity 2", "fill", "bom_line_quantity",
             "template:{{BOM_LINE_2_QTY}}",
             {"wait_after": 1000, "interaction_mode": "standard_input", "continue_on_error": True,
              "clear_before_fill": True, "press_key_after": "Tab"}),

            # --- BOM Line 3 ---
            (40, "New BOM Line 3", "click", "bom_line_new_btn", None,
             {"wait_after": 1000, "interaction_mode": "nav_button", "continue_on_error": True}),
            (41, "Fill Item Number 3", "fill", "bom_line_item_number",
             "template:{{BOM_LINE_3_ITEM}}",
             {"wait_after": 1000, "interaction_mode": "combobox", "continue_on_error": True,
              "press_key_after": "Enter"}),
            (42, "Confirm Item 3", "click", "bom_line_item_confirm", None,
             {"wait_after": 500, "interaction_mode": "auto", "continue_on_error": True}),
            (43, "Fill Quantity 3", "fill", "bom_line_quantity",
             "template:{{BOM_LINE_3_QTY}}",
             {"wait_after": 1000, "interaction_mode": "standard_input", "continue_on_error": True,
              "clear_before_fill": True, "press_key_after": "Tab"}),

            # --- BOM Line 4 ---
            (50, "New BOM Line 4", "click", "bom_line_new_btn", None,
             {"wait_after": 1000, "interaction_mode": "nav_button", "continue_on_error": True}),
            (51, "Fill Item Number 4", "fill", "bom_line_item_number",
             "template:{{BOM_LINE_4_ITEM}}",
             {"wait_after": 1000, "interaction_mode": "combobox", "continue_on_error": True,
              "press_key_after": "Enter"}),
            (52, "Confirm Item 4", "click", "bom_line_item_confirm", None,
             {"wait_after": 500, "interaction_mode": "auto", "continue_on_error": True}),
            (53, "Fill Quantity 4", "fill", "bom_line_quantity",
             "template:{{BOM_LINE_4_QTY}}",
             {"wait_after": 1000, "interaction_mode": "standard_input", "continue_on_error": True,
              "clear_before_fill": True, "press_key_after": "Tab"}),

            # --- BOM Line 5 ---
            (60, "New BOM Line 5", "click", "bom_line_new_btn", None,
             {"wait_after": 1000, "interaction_mode": "nav_button", "continue_on_error": True}),
            (61, "Fill Item Number 5", "fill", "bom_line_item_number",
             "template:{{BOM_LINE_5_ITEM}}",
             {"wait_after": 1000, "interaction_mode": "combobox", "continue_on_error": True,
              "press_key_after": "Enter"}),
            (62, "Confirm Item 5", "click", "bom_line_item_confirm", None,
             {"wait_after": 500, "interaction_mode": "auto", "continue_on_error": True}),
            (63, "Fill Quantity 5", "fill", "bom_line_quantity",
             "template:{{BOM_LINE_5_QTY}}",
             {"wait_after": 1000, "interaction_mode": "standard_input", "continue_on_error": True,
              "clear_before_fill": True, "press_key_after": "Tab"}),

            # --- BOM Line 6 ---
            (70, "New BOM Line 6", "click", "bom_line_new_btn", None,
             {"wait_after": 1000, "interaction_mode": "nav_button", "continue_on_error": True}),
            (71, "Fill Item Number 6", "fill", "bom_line_item_number",
             "template:{{BOM_LINE_6_ITEM}}",
             {"wait_after": 1000, "interaction_mode": "combobox", "continue_on_error": True,
              "press_key_after": "Enter"}),
            (72, "Confirm Item 6", "click", "bom_line_item_confirm", None,
             {"wait_after": 500, "interaction_mode": "auto", "continue_on_error": True}),
            (73, "Fill Quantity 6", "fill", "bom_line_quantity",
             "template:{{BOM_LINE_6_QTY}}",
             {"wait_after": 1000, "interaction_mode": "standard_input", "continue_on_error": True,
              "clear_before_fill": True, "press_key_after": "Tab"}),

            # --- BOM Line 7 ---
            (80, "New BOM Line 7", "click", "bom_line_new_btn", None,
             {"wait_after": 1000, "interaction_mode": "nav_button", "continue_on_error": True}),
            (81, "Fill Item Number 7", "fill", "bom_line_item_number",
             "template:{{BOM_LINE_7_ITEM}}",
             {"wait_after": 1000, "interaction_mode": "combobox", "continue_on_error": True,
              "press_key_after": "Enter"}),
            (82, "Confirm Item 7", "click", "bom_line_item_confirm", None,
             {"wait_after": 500, "interaction_mode": "auto", "continue_on_error": True}),
            (83, "Fill Quantity 7", "fill", "bom_line_quantity",
             "template:{{BOM_LINE_7_QTY}}",
             {"wait_after": 1000, "interaction_mode": "standard_input", "continue_on_error": True,
              "clear_before_fill": True, "press_key_after": "Tab"}),

            # --- BOM Line 8 ---
            (90, "New BOM Line 8", "click", "bom_line_new_btn", None,
             {"wait_after": 1000, "interaction_mode": "nav_button", "continue_on_error": True}),
            (91, "Fill Item Number 8", "fill", "bom_line_item_number",
             "template:{{BOM_LINE_8_ITEM}}",
             {"wait_after": 1000, "interaction_mode": "combobox", "continue_on_error": True,
              "press_key_after": "Enter"}),
            (92, "Confirm Item 8", "click", "bom_line_item_confirm", None,
             {"wait_after": 500, "interaction_mode": "auto", "continue_on_error": True}),
            (93, "Fill Quantity 8", "fill", "bom_line_quantity",
             "template:{{BOM_LINE_8_QTY}}",
             {"wait_after": 1000, "interaction_mode": "standard_input", "continue_on_error": True,
              "clear_before_fill": True, "press_key_after": "Tab"}),
        ],
    },

    # =========================================================================
    # WF-8: APPROVE BOM + ACTIVATE VERSION (8 steps) -- NEW
    # Approve the BOM from BOM Table, then go back and approve+activate version
    # =========================================================================
    "wf8_approve_activate": {
        "name": "WF-8: Approve BOM + Activate Version",
        "desc": "Approve the BOM, go back to BOM Versions, approve and activate the version",
        "condition_field": "",
        "steps": [
            # --- Approve BOM from BOM Table ---
            (10, "Click BOM Action Pane Tab", "click", "bom_table_action_tab", None,
             {"wait_after": 1000, "interaction_mode": "tab_header"}),
            (11, "Click BOM Approve", "click", "bom_approve_btn", None,
             {"wait_after": 2000, "interaction_mode": "nav_button"}),
            (12, "Click Approve Dialog OK", "click", "approve_dialog_ok", None,
             {"wait_after": 3000, "interaction_mode": "dialog_button",
              "check_for_errors": True}),

            # --- Go back to BOM Versions ---
            (13, "Close BOM Table (Back)", "click", "generic_close_btn", None,
             {"wait_after": 3000, "interaction_mode": "dialog_button"}),
            (14, "Wait for navigation", "wait_time", None, "static:2000", {}),

            # --- Approve BOM Version (second approval) ---
            (15, "Click Version Action Pane Tab", "click", "version_action_pane_tab", None,
             {"wait_after": 1000, "interaction_mode": "tab_header"}),
            (16, "Click BOM Version Approve", "click", "bom_version_approve_btn", None,
             {"wait_after": 2000, "interaction_mode": "nav_button"}),
            (17, "Click Approve Dialog OK", "click", "approve_dialog_ok", None,
             {"wait_after": 3000, "interaction_mode": "dialog_button",
              "check_for_errors": True}),

            # --- Activate ---
            (18, "Click Activate", "click", "bom_version_activate_btn", None,
             {"wait_after": 3000, "interaction_mode": "nav_button",
              "check_for_errors": True}),

            # --- Close BOM Consist Of ---
            (19, "Close BOM Consist Of (Back)", "click", "close_bom_consist_of", None,
             {"wait_after": 3000, "interaction_mode": "dialog_button"}),
            (20, "Wait for navigation back", "wait_time", None, "static:2000", {}),
        ],
    },

    # =========================================================================
    # WF-9: ROUTE REGISTRATION (14 steps) -- NEW
    # Navigate to Route Table, find route, set item/config/site, approve+activate
    # =========================================================================
    "wf9_route": {
        "name": "WF-9: Route Registration",
        "desc": "Navigate to Route Table, register item on route, approve and activate",
        "condition_field": "",
        "steps": [
            (10, "Click Favorites", "click", "favorites", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),
            (11, "Click Route Table", "click", "route_table_link", None,
             {"wait_after": 8000, "interaction_mode": "nav_button"}),
            (12, "Wait for Route page", "wait_time", None, "static:3000", {}),

            # --- Filter by Route Number ---
            (13, "Click Route Number Header (filter)", "click", "route_number_header", None,
             {"wait_after": 1000, "interaction_mode": "nav_button"}),
            (14, "Fill Route Number Filter", "fill", "route_number_filter",
             "template:{{ROUTE}}",
             {"wait_after": 2000, "interaction_mode": "standard_input",
              "press_key_after": "Enter"}),
            (15, "Click Apply Filters", "click", "route_apply_filters", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),
            (16, "Select Route Row", "click", "route_row_select", None,
             {"wait_after": 2000, "interaction_mode": "auto"}),

            # --- Fill Route Version fields ---
            (17, "Fill Item Number", "fill", "route_item_number",
             "template:{{ITEM_NO}}",
             {"wait_after": 2000, "interaction_mode": "combobox",
              "press_key_after": "Enter"}),
            (18, "Fill Config (MB)", "fill", "route_config_dd",
             "template:{{BODY_MATERIAL}}",
             {"wait_after": 1000, "interaction_mode": "combobox",
              "press_key_after": "Enter"}),
            (19, "Fill Site (ARDT)", "fill", "route_site_dd", "static:ARDT",
             {"wait_after": 1000, "interaction_mode": "combobox",
              "press_key_after": "Enter"}),

            # --- Approve + Activate ---
            (20, "Click Approve Route Version", "click", "route_version_approve_btn", None,
             {"wait_after": 2000, "interaction_mode": "nav_button"}),
            (21, "Click Approve Dialog OK", "click", "approve_dialog_ok", None,
             {"wait_after": 3000, "interaction_mode": "dialog_button",
              "check_for_errors": True}),
            (22, "Click Activate Route Version", "click", "route_version_activate_btn", None,
             {"wait_after": 3000, "interaction_mode": "nav_button",
              "check_for_errors": True}),
            (23, "Post-activate wait", "wait_time", None, "static:2000", {}),
        ],
    },

    # =========================================================================
    # WF-10: RELEASE PRODUCT (4 steps) -- NEW
    # Navigate to Release Products, enter item number, release
    # =========================================================================
    "wf10_release": {
        "name": "WF-10: Release Product",
        "desc": "Navigate to Release Products page and release the item",
        "condition_field": "",
        "steps": [
            (10, "Click Favorites", "click", "favorites", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),
            (11, "Click Release Products Link", "click", "release_products_link", None,
             {"wait_after": 8000, "interaction_mode": "nav_button"}),
            (12, "Fill Item Number", "fill", "release_item_number",
             "template:{{ITEM_NO}}",
             {"wait_after": 2000, "interaction_mode": "combobox",
              "press_key_after": "Enter"}),
            (13, "Click Release OK", "click", "release_ok_btn", None,
             {"wait_after": 5000, "interaction_mode": "dialog_button",
              "check_for_errors": True}),
        ],
    },

    # =========================================================================
    # WF-11: MOVEMENT JOURNAL (20 steps) -- NEW
    # Navigate to Movement Journal, create journal, add line, post
    # =========================================================================
    "wf11_movement_journal": {
        "name": "WF-11: Movement Journal",
        "desc": "Create Movement Journal with item, serial number, and post it",
        "condition_field": "",
        "steps": [
            (10, "Click Favorites", "click", "favorites", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),
            (11, "Click Movement Journal", "click", "movement_journal_link", None,
             {"wait_after": 8000, "interaction_mode": "nav_button"}),
            (12, "Wait for Journal page", "wait_time", None, "static:3000", {}),

            # --- Create New Journal ---
            (13, "Click New Journal", "click", "journal_new_btn", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),
            (14, "Click Journal Name Dropdown", "click", "journal_name_dd", None,
             {"wait_after": 2000, "interaction_mode": "combobox"}),
            (15, "Select Journal Name Row", "click", "journal_name_row", None,
             {"wait_after": 2000, "interaction_mode": "auto"}),
            (16, "Fill Warehouse", "fill", "journal_warehouse", "static:r w",
             {"wait_after": 2000, "interaction_mode": "combobox"}),
            (17, "Select Warehouse Row", "click", "journal_warehouse_row", None,
             {"wait_after": 1000, "interaction_mode": "auto"}),
            (18, "Fill Description", "fill", "journal_description",
             "template:{{SERIAL NO}}",
             {"wait_after": 1000, "interaction_mode": "standard_input",
              "clear_before_fill": True}),
            (19, "Click OK (Create Journal)", "click", "journal_ok_btn", None,
             {"wait_after": 5000, "interaction_mode": "dialog_button"}),

            # --- Journal Lines ---
            (20, "Click Journal Lines", "click", "journal_lines_btn", None,
             {"wait_after": 5000, "interaction_mode": "nav_button"}),
            (21, "Fill Item Number", "fill", "journal_line_item_number",
             "template:{{ITEM_NO}}",
             {"wait_after": 2000, "interaction_mode": "combobox",
              "press_key_after": "Enter"}),
            (22, "Fill Config Dimension", "fill", "journal_line_config_dd",
             "template:{{BODY_MATERIAL}}",
             {"wait_after": 1000, "interaction_mode": "combobox",
              "press_key_after": "Enter"}),

            # --- Serial Number ---
            (23, "Click Serial Number field", "click", "journal_line_serial_dd", None,
             {"wait_after": 1000, "interaction_mode": "combobox"}),
            (24, "Click New Serial Button", "click", "journal_line_new_serial_btn", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),
            (25, "Fill Serial Number", "fill", "journal_serial_input",
             "template:{{SERIAL NO}}",
             {"wait_after": 1000, "interaction_mode": "standard_input"}),
            (26, "Close Serial Form", "click", "close_serial_form", None,
             {"wait_after": 2000, "interaction_mode": "dialog_button"}),
            (27, "Fill Serial in Journal Line", "fill", "journal_line_serial_dd",
             "template:{{SERIAL NO}}",
             {"wait_after": 1000, "interaction_mode": "combobox",
              "press_key_after": "Enter"}),

            # --- Post ---
            (28, "Click Post Journal", "click", "journal_post_btn", None,
             {"wait_after": 3000, "interaction_mode": "nav_button"}),
            (29, "Click Post OK", "click", "journal_post_ok", None,
             {"wait_after": 5000, "interaction_mode": "dialog_button",
              "check_for_errors": True}),
        ],
    },
}


# =============================================================================
# CHAIN LINKS
# =============================================================================
# (workflow_key, order, wait_before_ms, context_mapping)
# context_mapping: dict mapping context var names => row_data keys for downstream use

CHAIN_LINKS = [
    ("wf0_login",           5,  3000, {}),
    ("wf1_navigate",       10,  2000, {}),
    ("wf2_create_product", 20,  1000, {}),
    ("wf2b_capture_item",  25,  2000, {}),
    ("wf3_dimensions",     30,  1000, {"ITEM_NO": "ITEM_NO"}),
    ("wf4_variants",       40,  1000, {}),
    ("wf5_bom_version",    50,  2000, {}),
    ("wf6_create_bom",     55,  1000, {}),
    ("wf7_bom_lines",      60,  1000, {}),
    ("wf8_approve_activate", 65, 1000, {}),
    ("wf9_route",          70,  2000, {"ITEM_NO": "ITEM_NO"}),
    ("wf10_release",       75,  1000, {"ITEM_NO": "ITEM_NO"}),
    ("wf11_movement_journal", 80, 2000, {"ITEM_NO": "ITEM_NO"}),
]


class Command(BaseCommand):
    help = "Seed 13 sub-workflows + 1 chain for ARAMCO FC Repair: Full ERP Flow"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force', action='store_true',
            help='Delete existing chain/workflows and recreate',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        from apps.erp_automation.models import (
            Locator, LocatorStrategy, Workflow, WorkflowStep,
            WorkflowChain, WorkflowChainLink,
        )

        force = options['force']
        dry_run = options['dry_run']

        CHAIN_NAME = "ARAMCO FC Repair: Full ERP Flow"

        if dry_run:
            self.stdout.write(self.style.WARNING("=== DRY RUN MODE ==="))

        # --- Check existing ---
        existing_chain = WorkflowChain.objects.filter(name=CHAIN_NAME).first()
        if existing_chain and not force:
            self.stdout.write(self.style.ERROR(
                f"Chain '{CHAIN_NAME}' already exists (pk={existing_chain.pk}). "
                f"Use --force to delete and recreate."
            ))
            return

        if existing_chain and force and not dry_run:
            existing_chain.delete()
            self.stdout.write(self.style.WARNING(
                f"Deleted existing chain '{CHAIN_NAME}'"
            ))

        # Also delete old chain name if exists
        old_chain = WorkflowChain.objects.filter(
            name="FC Repair: Create Product + BOM"
        ).first()
        if old_chain and force and not dry_run:
            old_chain.delete()
            self.stdout.write(self.style.WARNING(
                "Deleted old chain 'FC Repair: Create Product + BOM'"
            ))

        # Delete existing sub-workflows if force
        if force and not dry_run:
            for wf_key, wf_def in WORKFLOWS.items():
                old = Workflow.objects.filter(name=wf_def["name"]).first()
                if old:
                    step_count = old.steps.count()
                    old.delete()
                    self.stdout.write(self.style.WARNING(
                        f"  Deleted workflow '{wf_def['name']}' ({step_count} steps)"
                    ))
            # Also clean up old workflow names
            old_names = [
                "WF-5: Create BOM Version",
                "WF-6: Approve BOM Version",
            ]
            for old_name in old_names:
                old_wf = Workflow.objects.filter(name=old_name).first()
                if old_wf:
                    old_wf.delete()
                    self.stdout.write(self.style.WARNING(
                        f"  Deleted old workflow '{old_name}'"
                    ))

        # =====================================================================
        # STEP 1: CREATE LOCATORS
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n[1/3] Creating Locators..."
        ))
        locator_map = {}
        created_locs = 0
        reused_locs = 0

        for loc_key, loc_def in LOCATORS.items():
            django_name = loc_def["name"]

            if dry_run:
                self.stdout.write(f"  Would create/reuse locator: {django_name}")
                locator_map[loc_key] = None
                created_locs += 1
                continue

            locator = Locator.objects.filter(name=django_name).first()
            if locator:
                reused_locs += 1
                locator_map[loc_key] = locator
                if force:
                    locator.strategies.all().delete()
                    for s_type, s_value, s_priority in loc_def["strategies"]:
                        LocatorStrategy.objects.create(
                            locator=locator,
                            strategy_type=s_type,
                            value=s_value,
                            priority=s_priority,
                        )
                    locator.description = loc_def.get("desc", "")
                    locator.page_context = loc_def.get("ctx", "")
                    locator.save()
                continue

            locator = Locator.objects.create(
                name=django_name,
                description=loc_def.get("desc", ""),
                page_context=loc_def.get("ctx", ""),
                application="D365",
                is_dynamic=False,
            )
            for s_type, s_value, s_priority in loc_def["strategies"]:
                LocatorStrategy.objects.create(
                    locator=locator,
                    strategy_type=s_type,
                    value=s_value,
                    priority=s_priority,
                )
            locator_map[loc_key] = locator
            created_locs += 1

        self.stdout.write(self.style.SUCCESS(
            f"  Locators: {created_locs} created, {reused_locs} reused "
            f"({len(LOCATORS)} total)"
        ))

        # =====================================================================
        # STEP 2: CREATE WORKFLOWS + STEPS
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n[2/3] Creating Workflows..."
        ))
        workflow_map = {}
        total_steps = 0

        for wf_key, wf_def in WORKFLOWS.items():
            wf_name = wf_def["name"]
            steps = wf_def["steps"]

            if dry_run:
                self.stdout.write(
                    f"  Would create workflow: {wf_name} ({len(steps)} steps)"
                )
                workflow_map[wf_key] = None
                total_steps += len(steps)
                continue

            existing_wf = Workflow.objects.filter(name=wf_name).first()
            if existing_wf:
                self.stdout.write(self.style.WARNING(
                    f"  Workflow '{wf_name}' already exists (pk={existing_wf.pk}), skipping"
                ))
                workflow_map[wf_key] = existing_wf
                continue

            workflow = Workflow.objects.create(
                name=wf_name,
                description=wf_def.get("desc", ""),
                target_url="https://ardt.operations.dynamics.com/",
                application="D365",
                condition_field=wf_def.get("condition_field", ""),
                status="active",
            )
            workflow_map[wf_key] = workflow
            step_count = 0

            for order, name, action_type, loc_key, value_source, extra in steps:
                locator = locator_map.get(loc_key) if loc_key else None

                # Parse value source
                value_static = ""
                value_template = ""
                value_field = ""
                if value_source:
                    if value_source.startswith("static:"):
                        value_static = value_source[7:]
                    elif value_source.startswith("template:"):
                        value_template = value_source[9:]
                    elif value_source.startswith("field:"):
                        value_field = value_source[6:]

                WorkflowStep.objects.create(
                    workflow=workflow,
                    order=order,
                    name=name,
                    action_type=action_type,
                    locator=locator,
                    value_static=value_static,
                    value_template=value_template,
                    value_field=value_field,
                    condition_value=extra.get("condition_value", ""),
                    wait_after=int(extra.get("wait_after", 500)),
                    timeout=int(extra.get("timeout", 30000)),
                    continue_on_error=extra.get("continue_on_error", False),
                    check_for_errors=extra.get("check_for_errors", False),
                    press_key_after=extra.get("press_key_after", ""),
                    clear_before_fill=extra.get("clear_before_fill", False),
                    interaction_mode=extra.get("interaction_mode", "auto"),
                    save_result_as=extra.get("save_result_as", ""),
                    is_active=True,
                )
                step_count += 1
                total_steps += 1

            self.stdout.write(self.style.SUCCESS(
                f"  Created workflow: {wf_name} (pk={workflow.pk}, {step_count} steps)"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"  Total: {len(WORKFLOWS)} workflows, {total_steps} steps"
        ))

        # =====================================================================
        # STEP 3: CREATE CHAIN
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n[3/3] Creating Chain..."
        ))

        if dry_run:
            self.stdout.write(f"  Would create chain: {CHAIN_NAME}")
            for wf_key, order, wait_ms, ctx_map in CHAIN_LINKS:
                wf_name = WORKFLOWS[wf_key]["name"]
                ctx_str = f" context_mapping={ctx_map}" if ctx_map else ""
                self.stdout.write(
                    f"    Link {order}: {wf_name} (wait {wait_ms}ms){ctx_str}"
                )
            self.stdout.write(self.style.WARNING("\n=== DRY RUN COMPLETE ==="))
            return

        chain = WorkflowChain.objects.create(
            name=CHAIN_NAME,
            description=(
                "Complete ARAMCO FC Repair ERP flow: login, create released product, "
                "capture auto-generated item number, set dimensions, create variants, "
                "create BOM version, create BOM (copy), enter BOM lines, approve BOM, "
                "activate version, register route, release product, movement journal."
            ),
            condition_field="FROM",
            keep_browser_open=True,
            stop_on_failure=True,
        )

        for wf_key, order, wait_ms, ctx_map in CHAIN_LINKS:
            wf = workflow_map.get(wf_key)
            if not wf:
                self.stdout.write(self.style.ERROR(
                    f"  Workflow '{wf_key}' not found in map, skipping link"
                ))
                continue

            WorkflowChainLink.objects.create(
                chain=chain,
                workflow=wf,
                order=order,
                wait_before_ms=wait_ms,
                context_mapping=ctx_map if ctx_map else {},
            )

        link_count = chain.links.count()
        self.stdout.write(self.style.SUCCESS(
            f"  Created chain: {CHAIN_NAME} (pk={chain.pk}, {link_count} links)"
        ))

        # =====================================================================
        # SUMMARY
        # =====================================================================
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== SEED COMPLETE ==="))
        self.stdout.write(f"  Locators:  {created_locs + reused_locs}")
        self.stdout.write(f"  Workflows: {len(WORKFLOWS)}")
        self.stdout.write(f"  Steps:     {total_steps}")
        self.stdout.write(f"  Chain:     {CHAIN_NAME} ({link_count} links)")
        self.stdout.write("")
        self.stdout.write("  Chain execution order:")
        for wf_key, order, wait_ms, ctx_map in CHAIN_LINKS:
            wf_name = WORKFLOWS[wf_key]["name"]
            ctx_str = ""
            if ctx_map:
                ctx_str = f"  [context: {ctx_map}]"
            self.stdout.write(f"    {order:3d}. {wf_name}{ctx_str}")
