"""
Seed the "Create Released Product" workflow from the Flask legacy app.

Reads the Flask JSON files (locators.json, dictionaries.json, Create Item.json)
and creates proper Django Locator, LocatorStrategy, Workflow, and WorkflowStep records.

This gives us a complete, tested workflow for D365 item creation based on the
production-proven Flask app, but using Django's superior model system with
multi-strategy locators, interaction modes, and value templates.

Usage:
    python manage.py seed_flask_workflow
    python manage.py seed_flask_workflow --force   # Delete existing and recreate
    python manage.py seed_flask_workflow --dry-run  # Show what would be created
"""
import json
import os
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


# =============================================================================
# FLASK LOCATOR -> DJANGO LOCATOR MAPPING
# =============================================================================

# Maps Flask locator keys to Django Locator definitions.
# Each entry: (django_name, description, page_context, is_dynamic, interaction_mode,
#              strategies: [(type, value, priority), ...])
#
# We generate multiple strategies per locator for resilience:
#   1. Primary: The Flask XPath (proven in production)
#   2. Fallback: @name attribute where available (most stable for D365)
#   3. Fallback: contains(@id) for dynamic-prefix-safe matching

FLASK_LOCATORS = {
    # --- Login ---
    "login_user_field_Loc": {
        "name": "login_user_field",
        "description": "ADFS Login username input",
        "page_context": "ADFS Login",
        "mode": "standard_input",
        "strategies": [
            ("id", "userNameInput", 0),
            ("xpath", "//*[@id='userNameInput']", 5),
        ]
    },
    "login_pass_field_Loc": {
        "name": "login_pass_field",
        "description": "ADFS Login password input",
        "page_context": "ADFS Login",
        "mode": "standard_input",
        "strategies": [
            ("id", "passwordInput", 0),
            ("xpath", "//*[@id='passwordInput']", 5),
        ]
    },
    "login_submit_button_Loc": {
        "name": "login_submit_button",
        "description": "ADFS Login submit button",
        "page_context": "ADFS Login",
        "mode": "dialog_button",
        "strategies": [
            ("id", "submitButton", 0),
            ("xpath", "//*[@id='submitButton']", 5),
        ]
    },

    # --- Navigation ---
    "Favorites_Loc": {
        "name": "d365_favorites",
        "description": "D365 Favorites navigation panel",
        "page_context": "D365 Home",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//*[@id=\"navPaneFavoritesID\"]/span[2]", 0),
            ("id", "navPaneFavoritesID", 5),
        ]
    },
    "Released_products_Loc": {
        "name": "d365_released_products_link",
        "description": "Released Products link in favorites",
        "page_context": "D365 Favorites",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//a[@class='modulesPane-linkText' and text()='Released products']", 0),
            ("text", "Released products", 5),
        ]
    },
    "New_released_product_Loc": {
        "name": "d365_new_released_product_btn",
        "description": "New button on Released Products grid",
        "page_context": "Released Products",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//*[contains(@id, 'ecoresproductdetailsextendedgrid') and contains(@id, 'SystemDefinedNewButton_label')]", 0),
        ]
    },

    # --- Product Creation Form ---
    "Product_subtype_Ddown_Button_Loc": {
        "name": "d365_product_subtype_dropdown",
        "description": "Product subtype dropdown button in new product dialog",
        "page_context": "New Released Product",
        "mode": "custom_dropdown",
        "strategies": [
            ("xpath", "/html/body/div[2]/div/div[7]/div[2]/div/div[5]/div/div[1]/div[2]/div[1]/div[2]/div/div/div[2]/div", 0),
        ]
    },
    "Product_Master_Option_RP_Loc": {
        "name": "d365_product_master_option",
        "description": "Product Master option in subtype dropdown",
        "page_context": "New Released Product",
        "mode": "custom_dropdown",
        "strategies": [
            ("xpath", "/html/body/ul/li[2]", 0),
        ]
    },

    # --- Item Group (shared locator, value varies by account) ---
    "Item_group_Loc": {
        "name": "d365_item_group_field",
        "description": "Item Group input field (value varies by account)",
        "page_context": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("name", "ItemGroupId", 0),
            ("xpath", "//*[@name=\"ItemGroupId\"]", 5),
        ]
    },

    # --- Product Detail Fields ---
    "ModelGroupId_input_Loc": {
        "name": "d365_item_model_group",
        "description": "Item Model Group input (combobox, value: Repair Bit)",
        "page_context": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductCreate_\") and contains(@id, \"ModelGroupId_input\")]", 0),
        ]
    },
    "Product_number_Field_Loc": {
        "name": "d365_product_number_field",
        "description": "Product Number input field",
        "page_context": "New Released Product",
        "mode": "standard_input",
        "strategies": [
            ("name", "Identification_ProductNumber", 0),
            ("xpath", "//input[@name=\"Identification_ProductNumber\"]", 5),
        ]
    },
    "already_been_assigned_to_a_product_Error_Message_Loc": {
        "name": "d365_duplicate_item_error",
        "description": "Error message: product number already assigned (for duplicate detection)",
        "page_context": "New Released Product",
        "mode": "auto",
        "strategies": [
            ("xpath", "//span[@class='messageBar-message' and contains(text(), 'already been assigned to a product')]", 0),
        ]
    },
    "already_been_assigned_to_a_product_Error_Message_Close_Loc": {
        "name": "d365_duplicate_item_error_close",
        "description": "Close button on duplicate item error message",
        "page_context": "New Released Product",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", "//button[@aria-label='Close' and contains(@class, 'messageBar-closeIcon')]", 0),
            ("aria-label", "Close", 5),
        ]
    },
    "StorageDimensionGroup_Name_input_Loc": {
        "name": "d365_storage_dimension_group",
        "description": "Storage Dimension Group input (value: SWL)",
        "page_context": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductCreate_\") and contains(@id, \"StorageDimensionGroup_Name_input\")]", 0),
        ]
    },
    "TrackingDimensionGroup_Name_input_Loc": {
        "name": "d365_tracking_dimension_group",
        "description": "Tracking Dimension Group input (value: Serial)",
        "page_context": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductCreate_\") and contains(@id, \"TrackingDimensionGroup_Name_input\")]", 0),
        ]
    },
    "InventUnitId_input_Loc": {
        "name": "d365_inventory_unit",
        "description": "Inventory Unit of Measure input (value: ea)",
        "page_context": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductCreate_\") and contains(@id, \"InventUnitId_input\")]", 0),
        ]
    },
    "Purchase_UnitId_input_Loc": {
        "name": "d365_purchase_unit",
        "description": "Purchase Unit of Measure input (value: ea)",
        "page_context": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductCreate_\") and contains(@id, \"PurchUnitId_input\")]", 0),
        ]
    },
    "SalesUnitId_input_Loc": {
        "name": "d365_sales_unit",
        "description": "Sales Unit of Measure input (value: ea)",
        "page_context": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductCreate_\") and contains(@id, \"SalesUnitId_input\")]", 0),
        ]
    },
    "dimension_group_Loc": {
        "name": "d365_product_dimension_group",
        "description": "Product Dimension Group input (value: CSCS)",
        "page_context": "New Released Product",
        "mode": "combobox",
        "strategies": [
            ("name", "ProductDimensionGroup_Name", 0),
            ("xpath", "//*[@name=\"ProductDimensionGroup_Name\"]", 5),
        ]
    },
    "Product_name_Loc": {
        "name": "d365_product_name",
        "description": "Product Name input (composite: WO Serial Size Type MAT)",
        "page_context": "New Released Product",
        "mode": "standard_input",
        "strategies": [
            ("name", "Identification_Name", 0),
            ("xpath", "//input[@name=\"Identification_Name\"]", 5),
        ]
    },
    "Search_name_1_Loc": {
        "name": "d365_search_name_1",
        "description": "Search Name 1 input (value: Serial Number)",
        "page_context": "New Released Product",
        "mode": "standard_input",
        "strategies": [
            ("name", "Identification_SearchName", 0),
            ("xpath", "//input[@name=\"Identification_SearchName\"]", 5),
        ]
    },
    "Search_name_2_Loc": {
        "name": "d365_search_name_2",
        "description": "Search Name 2 / Name Alias input (value: Serial Number)",
        "page_context": "Released Product Detail",
        "mode": "standard_input",
        "strategies": [
            ("name", "ItemIdentification_NameAlias", 0),
            ("xpath", "//input[@name=\"ItemIdentification_NameAlias\"]", 5),
        ]
    },

    # --- OK Buttons ---
    "ok_button_RP_Loc": {
        "name": "d365_ok_button_released_product",
        "description": "OK button on Released Product creation dialog",
        "page_context": "New Released Product",
        "mode": "dialog_button",
        "strategies": [
            ("name", "OKButton", 0),
            ("xpath", "//button[@name='OKButton']", 5),
        ]
    },
    "ok_button_attribute_Loc": {
        "name": "d365_ok_button_attribute",
        "description": "OK button on attribute assignment dialog",
        "page_context": "Released Product Detail",
        "mode": "dialog_button",
        "strategies": [
            ("name", "OkButton", 0),
            ("xpath", "//button[@name='OkButton']", 5),
        ]
    },

    # --- Old Serial ID & Product Header ---
    "Old_Serial_ID_RP_Loc": {
        "name": "d365_old_serial_id",
        "description": "Old Serial ID field on released product detail",
        "page_context": "Released Product Detail",
        "mode": "standard_input",
        "strategies": [
            ("name", "InventTable_Inf_InventSerialId", 0),
            ("xpath", "//input[@name='InventTable_Inf_InventSerialId']", 5),
        ]
    },
    "Product_header_RP_Loc": {
        "name": "d365_product_header_tab",
        "description": "Product header/tab on released product action pane",
        "page_context": "Released Product Detail",
        "mode": "tab_header",
        "strategies": [
            ("xpath", "//*[contains(@id, \"_ActionPaneTabDefine_button\")]/span", 0),
        ]
    },

    # --- Product Dimensions ---
    "Product_dimensions_RP_Loc": {
        "name": "d365_product_dimensions_link",
        "description": "Product Dimensions link/button on product detail",
        "page_context": "Released Product Detail",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//span[contains(@aria-describedby, \"EcoResProductMasterDimensionPerCompany_helptext\")]", 0),
        ]
    },
    "Product_dim_Config_RP_Loc": {
        "name": "d365_dim_config_tab",
        "description": "Configuration tab in product dimensions dialog",
        "page_context": "Product Dimensions",
        "mode": "tab_header",
        "strategies": [
            ("xpath", "//li[contains(@id, \"TabPageConfigurations_header\")]", 0),
        ]
    },
    "Product_dim_Config_New_RP_Loc": {
        "name": "d365_dim_config_new_btn",
        "description": "New button on Configuration dimension tab",
        "page_context": "Product Dimensions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductMasterDimension\") and contains(@id, \"NewConfiguration\")]/div/span[1]", 0),
        ]
    },
    "Product_dim_Config_Name_RP_Loc": {
        "name": "d365_dim_config_name_input",
        "description": "Configuration name input (value: Prod_Dimen_Config - fixed)",
        "page_context": "Product Dimensions",
        "mode": "standard_input",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResConfiguration_Name_\") and contains(@id, \"_0_0_input\")]", 0),
        ]
    },
    "Product_dim_Size_RP_Loc": {
        "name": "d365_dim_size_tab",
        "description": "Size tab in product dimensions dialog",
        "page_context": "Product Dimensions",
        "mode": "tab_header",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductMasterDimension\") and contains(@id, \"TabPageSizes_header\")]", 0),
        ]
    },
    "Product_dim_Size_New_RP_Loc": {
        "name": "d365_dim_size_new_btn",
        "description": "New button on Size dimension tab",
        "page_context": "Product Dimensions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductMasterDimension\") and contains(@id, \"NewSize_label\")]", 0),
        ]
    },
    "Product_dim_Size_Name_RP_Loc": {
        "name": "d365_dim_size_name_input",
        "description": "Size name input (value: {{SIZE}})",
        "page_context": "Product Dimensions",
        "mode": "standard_input",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResSize_Name\") and contains(@id, \"0_0_input\")]", 0),
        ]
    },
    "Product_dim_Color_RP_Loc": {
        "name": "d365_dim_color_tab",
        "description": "Color tab in product dimensions dialog (Color = MAT NO.)",
        "page_context": "Product Dimensions",
        "mode": "tab_header",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductMasterDimension\") and contains(@id, \"TabPageColors_header\")]", 0),
        ]
    },
    "Product_dim_Color_New_RP_Loc": {
        "name": "d365_dim_color_new_btn",
        "description": "New button on Color dimension tab",
        "page_context": "Product Dimensions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductMasterDimension\") and contains(@id, \"NewColor_label\")]", 0),
        ]
    },
    "Product_dim_Color_Name_RP_Loc": {
        "name": "d365_dim_color_name_input",
        "description": "Color name input (value: {{MAT NO.}} = L5 material number)",
        "page_context": "Product Dimensions",
        "mode": "standard_input",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResColor_Name\") and contains(@id, \"0_0_input\")]", 0),
        ]
    },
    "Product_dim_Style_RP_Loc": {
        "name": "d365_dim_style_tab",
        "description": "Style tab in product dimensions dialog (Style = TYPE)",
        "page_context": "Product Dimensions",
        "mode": "tab_header",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductMasterDimension\") and contains(@id, \"TabPageStyles_header\")]", 0),
        ]
    },
    "Product_dim_Style_New_RP_Loc": {
        "name": "d365_dim_style_new_btn",
        "description": "New button on Style dimension tab",
        "page_context": "Product Dimensions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductMasterDimension\") and contains(@id, \"NewStyle_label\")]", 0),
        ]
    },
    "Product_dim_Style_Name_RP_Loc": {
        "name": "d365_dim_style_name_input",
        "description": "Style name input (value: {{TYPE}} = SMI type)",
        "page_context": "Product Dimensions",
        "mode": "standard_input",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResStyle_Name\") and contains(@id, \"0_0_input\")]", 0),
        ]
    },
    "Close_Product_dimensions_Loc": {
        "name": "d365_close_product_dimensions",
        "description": "Close button on product dimensions dialog",
        "page_context": "Product Dimensions",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductMasterDimension\") and contains(@id, \"SystemDefinedCloseButton\")]/div/span[1]", 0),
        ]
    },

    # --- Product Variants ---
    "Released_product_Variants_PMaster_RP_Loc": {
        "name": "d365_product_variants_btn",
        "description": "Released Product Variants button on product detail action pane",
        "page_context": "Released Product Detail",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//*[contains(@id, \"ecoresproductdetailsextendedgrid\") and contains(@id, \"EcoResProductVariantsAction_label\")]", 0),
        ]
    },
    "P_variant_header_RP_Loc": {
        "name": "d365_variant_header_btn",
        "description": "Product Variant header button on variants page",
        "page_context": "Product Variants",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//button[contains(@id, \"EcoResProductVariantsPerCompany\") and contains(@id, \"ActionPaneTabProductVariant_button\")]", 0),
        ]
    },
    "Released_product_Variant_suggestions_RP_Loc": {
        "name": "d365_variant_suggestions_btn",
        "description": "Variant Suggestions button on variants page",
        "page_context": "Product Variants",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductVariantsPerCompany\") and contains(@id, \"EcoResProductVariantPerCompanyMgr_label\")]", 0),
        ]
    },
    "Suggest_Variant_suggestions_RP_Loc": {
        "name": "d365_suggest_variants_btn",
        "description": "Suggest button in variant suggestions dialog",
        "page_context": "Variant Suggestions",
        "mode": "nav_button",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductVariantSuggestionsEnhanced\") and contains(@id, \"SuggestButton_label\")]", 0),
        ]
    },
    "Suggested_Variant_RP_Loc": {
        "name": "d365_suggested_variant_checkbox",
        "description": "Checkbox for suggested variant in suggestions grid",
        "page_context": "Variant Suggestions",
        "mode": "checkbox_toggle",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResTmpProductModelSuggestions_selected\") and contains(@id, \"0_0_container\")]/div/span", 0),
        ]
    },
    "Create_Variant_suggestions_RP_Loc": {
        "name": "d365_create_variants_btn",
        "description": "Create button in variant suggestions dialog (OK/Create)",
        "page_context": "Variant Suggestions",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductVariantSuggestionsEnhanced\") and contains(@id, \"CommandButtonOk_label\")]", 0),
        ]
    },
    "Close_Variant_suggestions_RP_Loc": {
        "name": "d365_close_variants_page",
        "description": "Close button on product variants page",
        "page_context": "Product Variants",
        "mode": "dialog_button",
        "strategies": [
            ("xpath", "//*[contains(@id, \"EcoResProductVariantsPerCompany\") and contains(@id, \"SystemDefinedCloseButton\")]/div/span[1]", 0),
        ]
    },

    # --- Main Filter (for finding the product after creation) ---
    "ItemNumber_Main_Filter_RP_Loc": {
        "name": "d365_released_products_quick_filter",
        "description": "Quick filter input on Released Products list",
        "page_context": "Released Products",
        "mode": "standard_input",
        "strategies": [
            ("xpath", "//*[contains(@id, \"ecoresproductdetailsextendedgrid\") and contains(@id, \"QuickFilter_Input_input\")]", 0),
        ]
    },
}


# =============================================================================
# WORKFLOW STEP DEFINITIONS
# =============================================================================

# The 26-step "Create Item" workflow from the Flask app, mapped to Django models.
# Extended with Product Dimensions and Variant creation steps (phases after step 26).
#
# Each step: (order, name, action_type, locator_key, value_source, extra_kwargs)
# value_source types:
#   - None: no value (click only)
#   - "static:VALUE": literal value
#   - "template:{{VAR}}": template variable
#   - "field:FIELD_NAME": direct field reference
#   - "condition:ACCOUNT_MAP": account-based branching

WORKFLOW_STEPS = [
    # --- Phase 1: Login (steps 10-12) ---
    # NOTE: Login is handled by executor's ADFS flow, not by workflow steps.
    # We skip login steps and start from navigation.

    # --- Phase 2: Navigation (steps 20-21) ---
    (20, "Click Favorites", "click", "Favorites_Loc", None,
     {"wait_after": 3000, "interaction_mode": "nav_button"}),

    (21, "Click Released Products", "click", "Released_products_Loc", None,
     {"wait_after": 10000, "interaction_mode": "nav_button"}),

    # --- Phase 3: New Product Dialog (steps 30-32) ---
    (30, "Click New Released Product", "click", "New_released_product_Loc", None,
     {"wait_after": 5000, "interaction_mode": "nav_button"}),

    (31, "Click Product Subtype Dropdown", "click", "Product_subtype_Ddown_Button_Loc", None,
     {"wait_after": 1000, "interaction_mode": "custom_dropdown"}),

    (32, "Select Product Master", "click", "Product_Master_Option_RP_Loc", None,
     {"wait_after": 1000, "interaction_mode": "custom_dropdown"}),

    # --- Phase 4: Item Group (account-branched, steps 40-44) ---
    # One step per account, using condition_value to branch
    (40, "Fill Item Group (LSTK)", "fill", "Item_group_Loc", "static:RPR-FC-LST",
     {"wait_after": 1000, "interaction_mode": "combobox", "condition_value": "LSTK",
      "press_key_after": "Enter"}),

    (41, "Fill Item Group (RC-LSTK)", "fill", "Item_group_Loc", "static:RPR-RC-LST",
     {"wait_after": 1000, "interaction_mode": "combobox", "condition_value": "RC-LSTK",
      "press_key_after": "Enter"}),

    (42, "Fill Item Group (HALLIBURTON)", "fill", "Item_group_Loc", "static:RPR-FC-HDB",
     {"wait_after": 1000, "interaction_mode": "combobox", "condition_value": "HALLIBURTON",
      "press_key_after": "Enter"}),

    (43, "Fill Item Group (Hal_Regional)", "fill", "Item_group_Loc", "static:RPR-FC-REG",
     {"wait_after": 1000, "interaction_mode": "combobox", "condition_value": "Hal_Regional",
      "press_key_after": "Enter"}),

    (44, "Fill Item Group (ARAMCO)", "fill", "Item_group_Loc", "static:RPR-FC-AR",
     {"wait_after": 1000, "interaction_mode": "combobox", "condition_value": "ARAMCO",
      "press_key_after": "Enter"}),

    # --- Phase 5: Product Detail Fields (steps 50-63) ---
    (50, "Fill Item Model Group", "fill", "ModelGroupId_input_Loc", "static:Repair Bit",
     {"wait_after": 1000, "interaction_mode": "combobox", "press_key_after": "Enter"}),

    (51, "Fill Product Number", "fill", "Product_number_Field_Loc", "template:{{ITEM NO}}",
     {"wait_after": 1000, "interaction_mode": "standard_input", "press_key_after": "Enter"}),

    # Steps 52-53: Duplicate detection - handled by executor's error detection loop
    # We include them as continue_on_error steps so the workflow can detect and react
    (52, "Check Duplicate Error", "wait", "already_been_assigned_to_a_product_Error_Message_Loc", None,
     {"wait_after": 700, "timeout": 2000, "continue_on_error": True,
      "interaction_mode": "auto"}),

    (53, "Close Duplicate Error", "click", "already_been_assigned_to_a_product_Error_Message_Close_Loc", None,
     {"wait_after": 500, "continue_on_error": True, "interaction_mode": "dialog_button"}),

    (54, "Fill Storage Dimension Group", "fill", "StorageDimensionGroup_Name_input_Loc", "static:SWL",
     {"wait_after": 1000, "interaction_mode": "combobox", "press_key_after": "Enter"}),

    (55, "Fill Tracking Dimension Group", "fill", "TrackingDimensionGroup_Name_input_Loc", "static:Serial",
     {"wait_after": 1000, "interaction_mode": "combobox", "press_key_after": "Enter"}),

    (56, "Fill Inventory Unit", "fill", "InventUnitId_input_Loc", "static:ea",
     {"wait_after": 1000, "interaction_mode": "combobox", "press_key_after": "Enter"}),

    (57, "Fill Purchase Unit", "fill", "Purchase_UnitId_input_Loc", "static:ea",
     {"wait_after": 1000, "interaction_mode": "combobox", "press_key_after": "Enter"}),

    (58, "Fill Sales Unit", "fill", "SalesUnitId_input_Loc", "static:ea",
     {"wait_after": 1000, "interaction_mode": "combobox", "press_key_after": "Enter"}),

    (59, "Fill Product Dimension Group", "fill", "dimension_group_Loc", "static:CSCS",
     {"wait_after": 500, "interaction_mode": "combobox"}),

    (60, "Fill Product Name", "fill", "Product_name_Loc",
     "template:{{ORDER NO.}} {{SERIAL NO}} {{SIZE}} {{TYPE}} {{MAT NO.}}",
     {"wait_after": 500, "interaction_mode": "standard_input"}),

    (61, "Fill Search Name 1", "fill", "Search_name_1_Loc", "template:{{SERIAL NO}}",
     {"wait_after": 500, "interaction_mode": "standard_input", "clear_before_fill": True}),

    (62, "Fill Search Name 2", "fill", "Search_name_2_Loc", "template:{{SERIAL NO}}",
     {"wait_after": 500, "interaction_mode": "standard_input", "clear_before_fill": True}),

    # --- Phase 6: OK Buttons (steps 70-71) ---
    (70, "Click OK (Released Product)", "click", "ok_button_RP_Loc", None,
     {"wait_after": 2000, "interaction_mode": "dialog_button"}),

    (71, "Click OK (Attributes)", "click", "ok_button_attribute_Loc", None,
     {"wait_after": 2000, "interaction_mode": "dialog_button"}),

    # --- Phase 7: Old Serial & Header (steps 80-81) ---
    (80, "Fill Old Serial ID", "fill", "Old_Serial_ID_RP_Loc", "template:{{SERIAL NO}}",
     {"wait_after": 500, "interaction_mode": "standard_input", "clear_before_fill": True}),

    (81, "Click Product Header Tab", "click", "Product_header_RP_Loc", None,
     {"wait_after": 2000, "interaction_mode": "tab_header"}),

    # --- Phase 8: Product Dimensions (steps 90-115) ---
    (90, "Click Product Dimensions", "click", "Product_dimensions_RP_Loc", None,
     {"wait_after": 2000, "interaction_mode": "nav_button"}),

    # Config dimension
    (91, "Click Config Tab", "click", "Product_dim_Config_RP_Loc", None,
     {"wait_after": 2000, "interaction_mode": "tab_header"}),

    (92, "Click Config New", "click", "Product_dim_Config_New_RP_Loc", None,
     {"wait_after": 2000, "interaction_mode": "nav_button"}),

    (93, "Fill Config Name", "fill", "Product_dim_Config_Name_RP_Loc", "static:Prod_Dimen_Config",
     {"wait_after": 2000, "interaction_mode": "standard_input"}),

    # Size dimension
    (94, "Click Size Tab", "click", "Product_dim_Size_RP_Loc", None,
     {"wait_after": 2000, "interaction_mode": "tab_header"}),

    (95, "Click Size New", "click", "Product_dim_Size_New_RP_Loc", None,
     {"wait_after": 2000, "interaction_mode": "nav_button"}),

    (96, "Fill Size Name", "fill", "Product_dim_Size_Name_RP_Loc", "template:{{SIZE}}",
     {"wait_after": 2000, "interaction_mode": "standard_input"}),

    # Color dimension (= MAT NO.)
    (97, "Click Color Tab", "click", "Product_dim_Color_RP_Loc", None,
     {"wait_after": 2000, "interaction_mode": "tab_header"}),

    (98, "Click Color New", "click", "Product_dim_Color_New_RP_Loc", None,
     {"wait_after": 2000, "interaction_mode": "nav_button"}),

    (99, "Fill Color Name (MAT NO.)", "fill", "Product_dim_Color_Name_RP_Loc", "template:{{MAT NO.}}",
     {"wait_after": 2000, "interaction_mode": "standard_input"}),

    # Style dimension (= TYPE)
    (100, "Click Style Tab", "click", "Product_dim_Style_RP_Loc", None,
     {"wait_after": 2000, "interaction_mode": "tab_header"}),

    (101, "Click Style New", "click", "Product_dim_Style_New_RP_Loc", None,
     {"wait_after": 2000, "interaction_mode": "nav_button"}),

    (102, "Fill Style Name (TYPE)", "fill", "Product_dim_Style_Name_RP_Loc", "template:{{TYPE}}",
     {"wait_after": 2000, "interaction_mode": "standard_input"}),

    # Close dimensions
    (103, "Close Product Dimensions", "click", "Close_Product_dimensions_Loc", None,
     {"wait_after": 5000, "interaction_mode": "dialog_button"}),

    # --- Phase 9: Product Variants (steps 110-117) ---
    (110, "Click Released Product Variants", "click", "Released_product_Variants_PMaster_RP_Loc", None,
     {"wait_after": 5000, "interaction_mode": "nav_button"}),

    (111, "Click Variant Header", "click", "P_variant_header_RP_Loc", None,
     {"wait_after": 5000, "interaction_mode": "nav_button"}),

    (112, "Click Variant Suggestions", "click", "Released_product_Variant_suggestions_RP_Loc", None,
     {"wait_after": 5000, "interaction_mode": "nav_button"}),

    (113, "Click Suggest", "click", "Suggest_Variant_suggestions_RP_Loc", None,
     {"wait_after": 5000, "interaction_mode": "nav_button"}),

    (114, "Select Suggested Variant", "click", "Suggested_Variant_RP_Loc", None,
     {"wait_after": 5000, "interaction_mode": "checkbox_toggle"}),

    (115, "Click Create Variants", "click", "Create_Variant_suggestions_RP_Loc", None,
     {"wait_after": 5000, "interaction_mode": "dialog_button"}),

    (116, "Close Variants Page", "click", "Close_Variant_suggestions_RP_Loc", None,
     {"wait_after": 5000, "interaction_mode": "dialog_button"}),
]


class Command(BaseCommand):
    help = "Seed the 'Create Released Product' workflow from Flask legacy app"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete existing workflow and recreate'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes'
        )

    def handle(self, *args, **options):
        from apps.erp_automation.models import (
            Locator, LocatorStrategy, Workflow, WorkflowStep, InteractionMode
        )

        force = options['force']
        dry_run = options['dry_run']

        WORKFLOW_NAME = "Create Released Product (Flask Port)"

        if dry_run:
            self.stdout.write(self.style.WARNING("=== DRY RUN MODE ==="))

        # Check if workflow already exists
        existing = Workflow.objects.filter(name=WORKFLOW_NAME).first()
        if existing and not force:
            self.stdout.write(self.style.ERROR(
                f"Workflow '{WORKFLOW_NAME}' already exists (pk={existing.pk}). "
                f"Use --force to delete and recreate."
            ))
            return

        if existing and force:
            if not dry_run:
                step_count = existing.steps.count()
                existing.delete()
                self.stdout.write(self.style.WARNING(
                    f"Deleted existing workflow '{WORKFLOW_NAME}' with {step_count} steps"
                ))

        # --- Step 1: Create Locators ---
        self.stdout.write(self.style.MIGRATE_HEADING("\n[1/3] Creating Locators..."))
        locator_map = {}  # flask_key -> Django Locator instance
        created_locators = 0
        reused_locators = 0

        for flask_key, loc_def in FLASK_LOCATORS.items():
            django_name = loc_def["name"]

            if dry_run:
                self.stdout.write(f"  Would create locator: {django_name}")
                locator_map[flask_key] = None
                created_locators += 1
                continue

            # Check if locator already exists (by name)
            locator = Locator.objects.filter(name=django_name).first()
            if locator:
                reused_locators += 1
                locator_map[flask_key] = locator
                self.stdout.write(f"  [reuse] Reusing existing locator: {django_name} (pk={locator.pk})")
                # Update strategies if force mode
                if force:
                    locator.strategies.all().delete()
                    for s_type, s_value, s_priority in loc_def["strategies"]:
                        LocatorStrategy.objects.create(
                            locator=locator,
                            strategy_type=s_type,
                            value=s_value,
                            priority=s_priority,
                        )
                continue

            # Create new locator
            locator = Locator.objects.create(
                name=django_name,
                description=loc_def.get("description", ""),
                page_context=loc_def.get("page_context", ""),
                application="dynamics365",
                is_dynamic="contains(@id" in str(loc_def.get("strategies", [])),
                default_timeout=30000,
            )

            # Create strategies
            for s_type, s_value, s_priority in loc_def["strategies"]:
                LocatorStrategy.objects.create(
                    locator=locator,
                    strategy_type=s_type,
                    value=s_value,
                    priority=s_priority,
                )

            locator_map[flask_key] = locator
            created_locators += 1
            self.stdout.write(f"  [+] Created locator: {django_name} "
                            f"({len(loc_def['strategies'])} strategies)")

        self.stdout.write(self.style.SUCCESS(
            f"\n  Locators: {created_locators} created, {reused_locators} reused"
        ))

        if dry_run:
            self.stdout.write(self.style.MIGRATE_HEADING("\n[2/3] Would create workflow steps:"))
            for step_def in WORKFLOW_STEPS:
                order, name = step_def[0], step_def[1]
                self.stdout.write(f"  Step {order}: {name}")
            self.stdout.write(self.style.SUCCESS(
                f"\n  Total: {len(WORKFLOW_STEPS)} steps"
            ))
            return

        # --- Step 2: Create Workflow ---
        self.stdout.write(self.style.MIGRATE_HEADING("\n[2/3] Creating Workflow..."))

        workflow = Workflow.objects.create(
            name=WORKFLOW_NAME,
            description=(
                "Create a Released Product in D365 F&O. "
                "Ported from the Flask legacy app's 26-step workflow, "
                "extended with Product Dimensions and Variant creation. "
                "Supports account-based branching for Item Group selection. "
                "Template variables: {{ITEM NO}}, {{ORDER NO.}}, {{SERIAL NO}}, "
                "{{SIZE}}, {{TYPE}}, {{MAT NO.}}, {{FROM}}"
            ),
            target_url="https://prod.alrushaid.net",
            application="dynamics365",
            valid_sheets=["LSTK", "RC-LSTK", "ARAMCO", "HALLIBURTON", "Hal_Regional"],
            required_fields=["ITEM NO", "ORDER NO.", "SERIAL NO", "SIZE", "TYPE", "MAT NO."],
            condition_field="FROM",
            status="active",
        )
        self.stdout.write(self.style.SUCCESS(
            f"  Created workflow: {workflow.name} (pk={workflow.pk})"
        ))

        # --- Step 3: Create Workflow Steps ---
        self.stdout.write(self.style.MIGRATE_HEADING("\n[3/3] Creating Workflow Steps..."))
        step_count = 0

        for step_def in WORKFLOW_STEPS:
            order = step_def[0]
            name = step_def[1]
            action_type = step_def[2]
            locator_key = step_def[3]
            value_source = step_def[4]
            extra = step_def[5] if len(step_def) > 5 else {}

            # Resolve locator
            locator = locator_map.get(locator_key) if locator_key else None

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

            # Create step
            step = WorkflowStep.objects.create(
                workflow=workflow,
                order=order,
                name=name,
                action_type=action_type,
                locator=locator,
                value_static=value_static,
                value_template=value_template,
                value_field=value_field,
                condition_value=extra.get("condition_value", ""),
                interaction_mode=extra.get("interaction_mode", "auto"),
                clear_before_fill=extra.get("clear_before_fill", False),
                press_key_after=extra.get("press_key_after", ""),
                wait_after=extra.get("wait_after", 500),
                timeout=extra.get("timeout", 30000),
                continue_on_error=extra.get("continue_on_error", False),
            )
            step_count += 1

            # Build display info
            val_display = ""
            if value_static:
                val_display = f" = \"{value_static}\""
            elif value_template:
                val_display = f" = {value_template}"
            elif value_field:
                val_display = f" = [{value_field}]"

            cond_display = ""
            if extra.get("condition_value"):
                cond_display = f" [if FROM={extra['condition_value']}]"

            self.stdout.write(
                f"  Step {order:3d}: {action_type:6s} -> {name}{val_display}{cond_display}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\n  Created {step_count} workflow steps"
        ))

        # --- Summary ---
        self.stdout.write(self.style.MIGRATE_HEADING("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("[OK] Workflow seeded successfully!"))
        self.stdout.write(f"  Workflow: {workflow.name} (pk={workflow.pk})")
        self.stdout.write(f"  Locators: {created_locators + reused_locators}")
        self.stdout.write(f"  Strategies: {sum(len(l['strategies']) for l in FLASK_LOCATORS.values())}")
        self.stdout.write(f"  Steps: {step_count}")
        self.stdout.write(f"  Accounts: LSTK, RC-LSTK, HALLIBURTON, Hal_Regional, ARAMCO")
        self.stdout.write(f"  Condition field: FROM")
        self.stdout.write("")
        self.stdout.write("  Phases:")
        self.stdout.write("    20-21: Navigation (Favorites -> Released Products)")
        self.stdout.write("    30-32: New Product Dialog")
        self.stdout.write("    40-44: Item Group (account-branched)")
        self.stdout.write("    50-62: Product Detail Fields")
        self.stdout.write("    70-71: OK Buttons")
        self.stdout.write("    80-81: Old Serial & Header")
        self.stdout.write("    90-103: Product Dimensions (Config/Size/Color/Style)")
        self.stdout.write("    110-116: Product Variant Creation")
        self.stdout.write("")
        self.stdout.write(f"  View in editor: /erp-automation/workflows/{workflow.pk}/")
        self.stdout.write("=" * 60)
