"""
ARDT FMS - Dashboard Views
Version: 5.4 - Sprint 1

Role-based dashboard views with KPIs and statistics.
"""

import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import UserPreference


@login_required
def home_view(request):
    """
    Main dashboard home - redirects to role-specific dashboard.
    """
    user = request.user

    # Determine which dashboard to show based on user's highest role
    if user.is_superuser or user.has_role("ADMIN"):
        return redirect("dashboard:manager")
    elif user.has_role("MANAGER"):
        return redirect("dashboard:manager")
    elif user.has_role("PLANNER"):
        return redirect("dashboard:planner")
    elif user.has_role("TECHNICIAN"):
        return redirect("dashboard:technician")
    elif user.has_role("QC"):
        return redirect("dashboard:qc")
    else:
        # Default to main dashboard
        return redirect("dashboard:main")


@login_required
def main_dashboard(request):
    """
    Main dashboard view for all users.
    Shows customized widgets based on user preferences.
    """
    user = request.user

    # Get user's widget layout
    widget_layout = get_user_widget_layout(user, "main")

    # Build widgets with data and styles
    widgets = build_widgets_from_layout(widget_layout, user)

    context = {
        "page_title": "Dashboard",
        "dashboard_type": "main",
        "user": user,
        "widgets": widgets,
        "total_widgets": len(AVAILABLE_WIDGETS),
    }
    return render(request, "dashboard/main.html", context)


@login_required
def manager_dashboard(request):
    """
    Manager dashboard with KPIs and overview statistics.
    Uses dynamic widget system for customization.
    """
    user = request.user

    # Get user's widget layout for manager dashboard
    widget_layout = get_user_widget_layout(user, "manager")

    # Build widgets with data and styles
    widgets = build_widgets_from_layout(widget_layout, user)

    context = {
        "page_title": "Manager Dashboard",
        "dashboard_type": "manager",
        "user": user,
        "widgets": widgets,
        "total_widgets": len(AVAILABLE_WIDGETS),
    }
    return render(request, "dashboard/manager.html", context)


@login_required
def planner_dashboard(request):
    """
    Planner dashboard focused on scheduling and planning.
    Uses dynamic widget system for customization.
    """
    user = request.user

    # Get user's widget layout for planner dashboard
    widget_layout = get_user_widget_layout(user, "planner")

    # Build widgets with data and styles
    widgets = build_widgets_from_layout(widget_layout, user)

    context = {
        "page_title": "Planner Dashboard",
        "dashboard_type": "planner",
        "user": user,
        "widgets": widgets,
        "total_widgets": len(AVAILABLE_WIDGETS),
    }
    return render(request, "dashboard/planner.html", context)


@login_required
def technician_dashboard(request):
    """
    Technician dashboard showing assigned work orders.
    Uses dynamic widget system for customization.
    """
    user = request.user

    # Get user's widget layout for technician dashboard
    widget_layout = get_user_widget_layout(user, "technician")

    # Build widgets with data and styles
    widgets = build_widgets_from_layout(widget_layout, user)

    context = {
        "page_title": "My Dashboard",
        "dashboard_type": "technician",
        "user": user,
        "widgets": widgets,
        "total_widgets": len(AVAILABLE_WIDGETS),
    }
    return render(request, "dashboard/technician.html", context)


@login_required
def qc_dashboard(request):
    """
    QC Inspector dashboard showing inspections and NCRs.
    Uses dynamic widget system for customization.
    """
    user = request.user

    # Get user's widget layout for QC dashboard
    widget_layout = get_user_widget_layout(user, "qc")

    # Build widgets with data and styles
    widgets = build_widgets_from_layout(widget_layout, user)

    context = {
        "page_title": "QC Dashboard",
        "dashboard_type": "qc",
        "user": user,
        "widgets": widgets,
        "total_widgets": len(AVAILABLE_WIDGETS),
    }
    return render(request, "dashboard/qc.html", context)


# Keep old index for backwards compatibility
@login_required
def index(request):
    """Legacy index view - redirects to home."""
    return redirect("dashboard:home")


# =============================================================================
# Dashboard Customization Views
# =============================================================================

# Widget Categories
WIDGET_CATEGORIES = {
    "operations": {
        "name": "Operations",
        "description": "Work orders, production, and workflow tracking",
        "icon": "factory",
        "color": "blue",
    },
    "inventory": {
        "name": "Inventory & Equipment",
        "description": "Stock levels, drill bits, and equipment",
        "icon": "package",
        "color": "green",
    },
    "quality": {
        "name": "Quality & Compliance",
        "description": "NCRs, inspections, and quality metrics",
        "icon": "shield-check",
        "color": "red",
    },
    "sales": {
        "name": "Sales & Customers",
        "description": "Customer activity and sales metrics",
        "icon": "users",
        "color": "purple",
    },
    "maintenance": {
        "name": "Maintenance",
        "description": "Equipment maintenance and scheduling",
        "icon": "wrench",
        "color": "orange",
    },
    "analytics": {
        "name": "Analytics & Reports",
        "description": "Charts, KPIs, and performance metrics",
        "icon": "bar-chart-2",
        "color": "cyan",
    },
    "team": {
        "name": "Team & Resources",
        "description": "Staff activity and workload",
        "icon": "users-2",
        "color": "pink",
    },
    "utilities": {
        "name": "Utilities",
        "description": "Quick links and shortcuts",
        "icon": "grid-3x3",
        "color": "gray",
    },
}

# Master registry of all navigable pages, organized by sidebar section.
# Used by the "Add Page Shortcut" feature in Customize.
PAGE_REGISTRY = [
    {
        "section": "Sales",
        "icon": "trending-up",
        "color": "emerald",
        "pages": [
            {"name": "Accounts", "url": "sales:account_list", "icon": "building-2"},
            {"name": "Customers", "url": "sales:customer_list", "icon": "users"},
            {"name": "Rigs", "url": "sales:rig_list", "icon": "anchor"},
            {"name": "Wells", "url": "sales:well_list", "icon": "target"},
            {"name": "Sales Orders", "url": "sales:salesorder_list", "icon": "shopping-cart"},
            {"name": "Service Sites", "url": "sales:servicesite_list", "icon": "map-pin"},
            {"name": "Service Requests", "url": "sales:fieldservicerequest_list", "icon": "clipboard"},
            {"name": "Site Visits", "url": "sales:sitevisit_list", "icon": "car"},
            {"name": "Service Reports", "url": "sales:servicereport_list", "icon": "file-text"},
            {"name": "Field Engineers", "url": "sales:fieldtechnician_list", "icon": "hard-hat"},
            {"name": "Field Work Orders", "url": "sales:fieldworkorder_list", "icon": "file-check"},
            {"name": "Drill Runs", "url": "sales:fielddrillstringrun_list", "icon": "activity"},
            {"name": "Run Data", "url": "sales:fieldrundata_list", "icon": "database"},
            {"name": "Run Hours", "url": "sales:runhours_list", "icon": "clock"},
            {"name": "Performance Logs", "url": "sales:fieldperformancelog_list", "icon": "line-chart"},
            {"name": "Warehouses", "url": "sales:warehouse_list", "icon": "warehouse"},
        ],
    },
    {
        "section": "Production",
        "icon": "factory",
        "color": "orange",
        "pages": [
            {"name": "Production Dashboard", "url": "workorders:dashboard", "icon": "layout-dashboard"},
            {"name": "Work Orders", "url": "workorders:workorder_list_enhanced", "icon": "clipboard-list"},
            {"name": "Create Work Order", "url": "workorders:create", "icon": "file-plus-2"},
            {"name": "WIP", "url": "execution:list", "icon": "play-circle"},
            {"name": "Instructions", "url": "workorders:instruction_rule_list", "icon": "book-text"},
            {"name": "Process Routes", "url": "workorders:processroute_list", "icon": "git-branch"},
            {"name": "WO Costs", "url": "workorders:workordercost_list", "icon": "dollar-sign"},
            {"name": "Evaluations", "url": "workorders:repairevaluation_list", "icon": "search"},
            {"name": "Repair BOM", "url": "workorders:repairbom_list", "icon": "list"},
            {"name": "Bit History", "url": "workorders:bitrepairhistory_list", "icon": "history"},
            {"name": "Salvage", "url": "workorders:salvageitem_list", "icon": "recycle"},
        ],
    },
    {
        "section": "Technical",
        "icon": "cog",
        "color": "slate",
        "pages": [
            {"name": "Designs", "url": "technology:design_list", "icon": "pen-tool"},
            {"name": "Connections", "url": "technology:connection_list", "icon": "link"},
            {"name": "Breaker Slots", "url": "technology:breaker_slot_list", "icon": "wrench"},
            {"name": "Pockets Layout", "url": "technology:pockets_layout_list", "icon": "grid-3x3"},
            {"name": "Bills of Materials", "url": "technology:bom_list", "icon": "package"},
            {"name": "Create BOM", "url": "technology:bom_create", "icon": "file-plus"},
            {"name": "Cutter Map", "url": "cutter_map:index", "icon": "scan"},
            {"name": "Bit Sizes", "url": "technology:bit_size_list", "icon": "ruler"},
            {"name": "Types (HDBS/SMI)", "url": "technology:hdbs_type_list", "icon": "layers"},
            {"name": "Design Import (ERP)", "url": "technology:design_import", "icon": "upload"},
            {"name": "Design Stock (On-hand)", "url": "technology:design_stock_import", "icon": "package"},
        ],
    },
    {
        "section": "Quality",
        "icon": "check-circle",
        "color": "green",
        "pages": [
            {"name": "Inspections", "url": "quality:inspection_list", "icon": "search"},
            {"name": "NCRs", "url": "quality:ncr_list", "icon": "alert-triangle"},
            {"name": "CAPA", "url": "supplychain:capa_list", "icon": "shield-check"},
            {"name": "Procedures", "url": "procedures:procedure_list", "icon": "book-open"},
            {"name": "Form Templates", "url": "forms_engine:template-list", "icon": "file-check"},
            {"name": "Requirements", "url": "compliance:compliancerequirement_list", "icon": "list-checks"},
            {"name": "Checklists", "url": "compliance:inspectionchecklist_list", "icon": "clipboard-check"},
            {"name": "Audits", "url": "compliance:audittrail_list", "icon": "eye"},
            {"name": "Certifications", "url": "compliance:certification_list", "icon": "award"},
            {"name": "Training", "url": "compliance:trainingrecord_list", "icon": "graduation-cap"},
        ],
    },
    {
        "section": "Logistics",
        "icon": "truck",
        "color": "blue",
        "pages": [
            {"name": "Inventory Dashboard", "url": "inventory:dashboard", "icon": "layout-dashboard"},
            {"name": "Items", "url": "inventory:item_list", "icon": "package"},
            {"name": "Stock Balances", "url": "inventory:stock_balance_list", "icon": "scale"},
            {"name": "Variant Stock", "url": "inventory:variant_stock_list", "icon": "git-branch"},
            {"name": "Stock Ledger", "url": "inventory:stock_ledger_list", "icon": "book"},
            {"name": "Assets", "url": "inventory:asset_list", "icon": "hard-drive"},
            {"name": "Reservations", "url": "inventory:reservation_list", "icon": "bookmark"},
            {"name": "Cutter Inventory", "url": "inventory:cutter_inventory_list", "icon": "circle-dot"},
            {"name": "Cutter Orders", "url": "inventory:cutter_order_list", "icon": "shopping-cart"},
            {"name": "Stock Import (ERP)", "url": "inventory:stock_import", "icon": "upload"},
            {"name": "Drill Bit Inv. Dashboard", "url": "workorders:drillbit_inventory_dashboard", "icon": "layout-dashboard"},
            {"name": "Drill Bits", "url": "workorders:drillbit_list_enhanced", "icon": "disc"},
            {"name": "Register New Bit", "url": "workorders:drillbit_create", "icon": "plus-circle"},
            {"name": "Locations", "url": "workorders:location_list", "icon": "map-pin"},
            {"name": "Bit Events", "url": "workorders:bitevent_list", "icon": "activity"},
            {"name": "Export Drill Bits", "url": "workorders:drillbit_export_excel", "icon": "file-spreadsheet"},
            {"name": "Goods Receipt (GRN)", "url": "inventory:grn_list", "icon": "download"},
            {"name": "Issues", "url": "inventory:issue_list", "icon": "upload"},
            {"name": "Transfers", "url": "inventory:transfer_list", "icon": "arrow-right-left"},
            {"name": "Adjustments", "url": "inventory:adjustment_list", "icon": "settings-2"},
            {"name": "Vendors", "url": "supplychain:supplier_list", "icon": "building-2"},
            {"name": "Requisitions (PR)", "url": "supplychain:pr_list", "icon": "file-input"},
            {"name": "Purchase Orders", "url": "supplychain:po_list", "icon": "file-output"},
            {"name": "Cycle Count", "url": "inventory:cyclecount_plan_list", "icon": "clipboard-check"},
            {"name": "Price Lists", "url": "inventory:pricelist_list", "icon": "tags"},
            {"name": "Stock Valuation", "url": "inventory:report_stock_valuation", "icon": "dollar-sign"},
            {"name": "Movement History", "url": "inventory:report_movement_history", "icon": "activity"},
            {"name": "Low Stock", "url": "inventory:report_low_stock", "icon": "alert-triangle"},
        ],
    },
    {
        "section": "Maintenance",
        "icon": "wrench",
        "color": "amber",
        "pages": [
            {"name": "Equipment", "url": "maintenance:equipment_list", "icon": "cpu"},
            {"name": "Maintenance Requests", "url": "maintenance:request_list", "icon": "alert-circle"},
            {"name": "MWOs", "url": "maintenance:mwo_list", "icon": "tool"},
            {"name": "PM Schedule", "url": "maintenance:pm_schedule", "icon": "calendar-check"},
        ],
    },
]

# Available widgets configuration - Enhanced with categories
AVAILABLE_WIDGETS = {
    # =========================================================================
    # OPERATIONS WIDGETS
    # =========================================================================
    "work_orders_summary": {
        "name": "Work Orders Summary",
        "description": "Active, completed, and overdue work order counts",
        "icon": "clipboard-list",
        "default_size": "medium",
        "category": "operations",
    },
    "recent_work_orders": {
        "name": "Recent Work Orders",
        "description": "List of recently created work orders",
        "icon": "clock",
        "default_size": "large",
        "category": "operations",
    },
    "work_orders_by_status": {
        "name": "Work Orders by Status",
        "description": "Visual breakdown of work orders by current status",
        "icon": "pie-chart",
        "default_size": "medium",
        "category": "operations",
    },
    "work_orders_by_priority": {
        "name": "Work Orders by Priority",
        "description": "High, medium, and low priority work order counts",
        "icon": "signal",
        "default_size": "small",
        "category": "operations",
    },
    "overdue_work_orders": {
        "name": "Overdue Work Orders",
        "description": "Work orders past their due date requiring attention",
        "icon": "alert-circle",
        "default_size": "medium",
        "category": "operations",
    },
    "todays_schedule": {
        "name": "Today's Schedule",
        "description": "Work orders scheduled for today",
        "icon": "calendar-check",
        "default_size": "large",
        "category": "operations",
    },
    "weekly_production": {
        "name": "Weekly Production",
        "description": "Production metrics for the current week",
        "icon": "trending-up",
        "default_size": "medium",
        "category": "operations",
    },

    # =========================================================================
    # INVENTORY & EQUIPMENT WIDGETS
    # =========================================================================
    "drill_bits_status": {
        "name": "Drill Bits Status",
        "description": "Overview of drill bit inventory status",
        "icon": "tool",
        "default_size": "small",
        "category": "inventory",
    },
    "low_stock_alerts": {
        "name": "Low Stock Alerts",
        "description": "Inventory items below reorder point",
        "icon": "package-x",
        "default_size": "medium",
        "category": "inventory",
    },
    "inventory_value": {
        "name": "Inventory Value",
        "description": "Total inventory value and breakdown",
        "icon": "wallet",
        "default_size": "small",
        "category": "inventory",
    },
    "stock_movements": {
        "name": "Stock Movements",
        "description": "Recent stock ins and outs",
        "icon": "arrow-left-right",
        "default_size": "medium",
        "category": "inventory",
    },
    "equipment_status": {
        "name": "Equipment Status",
        "description": "Overview of equipment operational status",
        "icon": "cpu",
        "default_size": "medium",
        "category": "inventory",
    },
    "drill_bit_lifecycle": {
        "name": "Drill Bit Lifecycle",
        "description": "Bits by lifecycle stage: new, in-use, refurbished",
        "icon": "refresh-cw",
        "default_size": "medium",
        "category": "inventory",
    },

    # =========================================================================
    # QUALITY & COMPLIANCE WIDGETS
    # =========================================================================
    "open_ncrs": {
        "name": "Open NCRs",
        "description": "Non-conformance reports requiring attention",
        "icon": "alert-triangle",
        "default_size": "medium",
        "category": "quality",
    },
    "ncr_trends": {
        "name": "NCR Trends",
        "description": "NCR count trends over the past 30 days",
        "icon": "activity",
        "default_size": "large",
        "category": "quality",
    },
    "pending_inspections": {
        "name": "Pending Inspections",
        "description": "Items awaiting quality inspection",
        "icon": "clipboard-check",
        "default_size": "medium",
        "category": "quality",
    },
    "quality_metrics": {
        "name": "Quality Metrics",
        "description": "Pass rate, rejection rate, and rework statistics",
        "icon": "gauge",
        "default_size": "medium",
        "category": "quality",
    },
    "compliance_status": {
        "name": "Compliance Status",
        "description": "Document expiry and compliance alerts",
        "icon": "file-check",
        "default_size": "small",
        "category": "quality",
    },

    # =========================================================================
    # SALES & CUSTOMERS WIDGETS
    # =========================================================================
    "customer_activity": {
        "name": "Customer Activity",
        "description": "Recent customer orders and interactions",
        "icon": "building-2",
        "default_size": "large",
        "category": "sales",
    },
    "top_customers": {
        "name": "Top Customers",
        "description": "Most active customers by work order count",
        "icon": "star",
        "default_size": "medium",
        "category": "sales",
    },
    "customer_count": {
        "name": "Customer Count",
        "description": "Total active and inactive customer count",
        "icon": "users",
        "default_size": "small",
        "category": "sales",
    },
    "work_orders_by_customer": {
        "name": "Work Orders by Customer",
        "description": "Distribution of work orders across customers",
        "icon": "bar-chart",
        "default_size": "large",
        "category": "sales",
    },

    # =========================================================================
    # MAINTENANCE WIDGETS
    # =========================================================================
    "maintenance_due": {
        "name": "Maintenance Due",
        "description": "Equipment due for maintenance",
        "icon": "wrench",
        "default_size": "medium",
        "category": "maintenance",
    },
    "maintenance_calendar": {
        "name": "Maintenance Calendar",
        "description": "Upcoming maintenance schedule this week",
        "icon": "calendar",
        "default_size": "large",
        "category": "maintenance",
    },
    "equipment_health": {
        "name": "Equipment Health",
        "description": "Overall equipment effectiveness metrics",
        "icon": "heart-pulse",
        "default_size": "medium",
        "category": "maintenance",
    },
    "maintenance_history": {
        "name": "Maintenance History",
        "description": "Recent maintenance activities completed",
        "icon": "history",
        "default_size": "medium",
        "category": "maintenance",
    },

    # =========================================================================
    # ANALYTICS & REPORTS WIDGETS
    # =========================================================================
    "kpi_summary": {
        "name": "KPI Summary",
        "description": "Key performance indicators at a glance",
        "icon": "target",
        "default_size": "large",
        "category": "analytics",
    },
    "performance_chart": {
        "name": "Performance Chart",
        "description": "Weekly/monthly performance trends",
        "icon": "line-chart",
        "default_size": "large",
        "category": "analytics",
    },
    "efficiency_metrics": {
        "name": "Efficiency Metrics",
        "description": "Production efficiency and cycle time metrics",
        "icon": "zap",
        "default_size": "medium",
        "category": "analytics",
    },
    "monthly_summary": {
        "name": "Monthly Summary",
        "description": "Month-to-date production and quality summary",
        "icon": "calendar-days",
        "default_size": "medium",
        "category": "analytics",
    },

    # =========================================================================
    # TEAM & RESOURCES WIDGETS
    # =========================================================================
    "team_workload": {
        "name": "Team Workload",
        "description": "Work distribution across team members",
        "icon": "users-2",
        "default_size": "large",
        "category": "team",
    },
    "technician_stats": {
        "name": "Technician Stats",
        "description": "Individual technician performance metrics",
        "icon": "user-check",
        "default_size": "medium",
        "category": "team",
    },
    "staff_availability": {
        "name": "Staff Availability",
        "description": "Team members currently on shift",
        "icon": "user-cog",
        "default_size": "small",
        "category": "team",
    },
    "pending_approvals": {
        "name": "Pending Approvals",
        "description": "Items awaiting your approval",
        "icon": "check-circle",
        "default_size": "small",
        "category": "team",
    },

    # =========================================================================
    # UTILITIES WIDGETS
    # =========================================================================
    "quick_links": {
        "name": "Quick Links",
        "description": "Shortcuts to frequently used modules",
        "icon": "link",
        "default_size": "small",
        "category": "utilities",
    },
    "recent_activity": {
        "name": "Recent Activity",
        "description": "Your recent actions in the system",
        "icon": "scroll",
        "default_size": "medium",
        "category": "utilities",
    },
    "notifications": {
        "name": "Notifications",
        "description": "Unread notifications and alerts",
        "icon": "bell",
        "default_size": "small",
        "category": "utilities",
    },
    "system_status": {
        "name": "System Status",
        "description": "System health and service status",
        "icon": "server",
        "default_size": "small",
        "category": "utilities",
    },
    "weather": {
        "name": "Weather",
        "description": "Current weather conditions at facility",
        "icon": "cloud-sun",
        "default_size": "small",
        "category": "utilities",
    },
    "clock": {
        "name": "Clock",
        "description": "Current date and time display",
        "icon": "clock-3",
        "default_size": "small",
        "category": "utilities",
    },

    # =========================================================================
    # PLANNER-SPECIFIC WIDGETS
    # =========================================================================
    "planner_pending_kpi": {
        "name": "Pending Planning",
        "description": "Count of work orders awaiting scheduling",
        "icon": "clock",
        "default_size": "small",
        "category": "operations",
    },
    "planner_in_progress_kpi": {
        "name": "In Progress",
        "description": "Count of currently active work orders",
        "icon": "loader",
        "default_size": "small",
        "category": "operations",
    },
    "planner_overdue_kpi": {
        "name": "Overdue",
        "description": "Count of overdue work orders needing attention",
        "icon": "alert-circle",
        "default_size": "small",
        "category": "operations",
    },
    "planner_due_this_week_kpi": {
        "name": "Due This Week",
        "description": "Count of work orders due within 7 days",
        "icon": "calendar",
        "default_size": "small",
        "category": "operations",
    },
    "pending_work_orders_list": {
        "name": "Pending Work Orders",
        "description": "List of work orders awaiting scheduling",
        "icon": "list",
        "default_size": "large",
        "category": "operations",
    },
    "in_progress_work_orders_list": {
        "name": "In Progress Work Orders",
        "description": "List of currently active work orders",
        "icon": "play-circle",
        "default_size": "large",
        "category": "operations",
    },
    "overdue_work_orders_table": {
        "name": "Overdue Work Orders Table",
        "description": "Detailed table of overdue work orders",
        "icon": "alert-triangle",
        "default_size": "full",
        "category": "operations",
    },

    # =========================================================================
    # MANAGER-SPECIFIC WIDGETS
    # =========================================================================
    "manager_total_wo_kpi": {
        "name": "Total Work Orders",
        "description": "Total count of all work orders",
        "icon": "clipboard-list",
        "default_size": "small",
        "category": "operations",
    },
    "manager_active_wo_kpi": {
        "name": "Active Work Orders",
        "description": "Count of active work orders",
        "icon": "activity",
        "default_size": "small",
        "category": "operations",
    },
    "manager_completed_week_kpi": {
        "name": "Completed This Week",
        "description": "Work orders completed in the past 7 days",
        "icon": "check-circle",
        "default_size": "small",
        "category": "operations",
    },
    "manager_overdue_kpi": {
        "name": "Overdue Work Orders",
        "description": "Count of overdue work orders",
        "icon": "alert-circle",
        "default_size": "small",
        "category": "operations",
    },
    "manager_drill_bits_kpi": {
        "name": "Drill Bits Overview",
        "description": "Total, in stock, and in production drill bits",
        "icon": "tool",
        "default_size": "small",
        "category": "inventory",
    },
    "work_orders_status_chart": {
        "name": "Work Orders Status Chart",
        "description": "Visual breakdown of work orders by status",
        "icon": "pie-chart",
        "default_size": "large",
        "category": "analytics",
    },

    # =========================================================================
    # TECHNICIAN-SPECIFIC WIDGETS
    # =========================================================================
    "tech_assigned_count_kpi": {
        "name": "My Assigned",
        "description": "Count of work orders assigned to you",
        "icon": "briefcase",
        "default_size": "small",
        "category": "operations",
    },
    "tech_completed_today_kpi": {
        "name": "Completed Today",
        "description": "Work orders you completed today",
        "icon": "check-circle",
        "default_size": "small",
        "category": "operations",
    },
    "tech_current_work_order": {
        "name": "Current Work Order",
        "description": "Your currently active work order",
        "icon": "play",
        "default_size": "large",
        "category": "operations",
    },
    "tech_my_work_orders_list": {
        "name": "My Work Orders",
        "description": "List of work orders assigned to you",
        "icon": "list",
        "default_size": "full",
        "category": "operations",
    },

    # =========================================================================
    # QC-SPECIFIC WIDGETS
    # =========================================================================
    "qc_pending_count_kpi": {
        "name": "Pending QC",
        "description": "Count of items awaiting QC inspection",
        "icon": "clipboard-check",
        "default_size": "small",
        "category": "quality",
    },
    "qc_open_ncrs_kpi": {
        "name": "Open NCRs",
        "description": "Count of open non-conformance reports",
        "icon": "alert-triangle",
        "default_size": "small",
        "category": "quality",
    },
    "qc_pending_list": {
        "name": "Pending QC List",
        "description": "Work orders awaiting quality inspection",
        "icon": "list-checks",
        "default_size": "large",
        "category": "quality",
    },
    "qc_recent_ncrs_list": {
        "name": "Recent NCRs",
        "description": "Recently created non-conformance reports",
        "icon": "file-warning",
        "default_size": "large",
        "category": "quality",
    },
    # =========================================================================
    # PAGE SHORTCUT WIDGETS
    # =========================================================================
}

# Default widget layouts for each dashboard type
DEFAULT_WIDGET_LAYOUT = [
    {"id": "work_orders_summary", "size": "medium", "order": 1, "visible": True},
    {"id": "drill_bits_status", "size": "small", "order": 2, "visible": True},
    {"id": "recent_work_orders", "size": "large", "order": 3, "visible": True},
    {"id": "quick_links", "size": "small", "order": 4, "visible": True},
]

DEFAULT_PLANNER_WIDGET_LAYOUT = [
    {"id": "planner_pending_kpi", "size": "small", "order": 1, "visible": True},
    {"id": "planner_in_progress_kpi", "size": "small", "order": 2, "visible": True},
    {"id": "planner_overdue_kpi", "size": "small", "order": 3, "visible": True},
    {"id": "planner_due_this_week_kpi", "size": "small", "order": 4, "visible": True},
    {"id": "pending_work_orders_list", "size": "large", "order": 5, "visible": True},
    {"id": "in_progress_work_orders_list", "size": "large", "order": 6, "visible": True},
    {"id": "overdue_work_orders_table", "size": "full", "order": 7, "visible": True},
]

DEFAULT_MANAGER_WIDGET_LAYOUT = [
    {"id": "manager_total_wo_kpi", "size": "small", "order": 1, "visible": True},
    {"id": "manager_active_wo_kpi", "size": "small", "order": 2, "visible": True},
    {"id": "manager_completed_week_kpi", "size": "small", "order": 3, "visible": True},
    {"id": "manager_overdue_kpi", "size": "small", "order": 4, "visible": True},
    {"id": "manager_drill_bits_kpi", "size": "medium", "order": 5, "visible": True},
    {"id": "work_orders_status_chart", "size": "large", "order": 6, "visible": True},
    {"id": "recent_work_orders", "size": "large", "order": 7, "visible": True},
]

DEFAULT_TECHNICIAN_WIDGET_LAYOUT = [
    {"id": "tech_assigned_count_kpi", "size": "small", "order": 1, "visible": True},
    {"id": "tech_completed_today_kpi", "size": "small", "order": 2, "visible": True},
    {"id": "tech_current_work_order", "size": "large", "order": 3, "visible": True},
    {"id": "tech_my_work_orders_list", "size": "full", "order": 4, "visible": True},
]

DEFAULT_QC_WIDGET_LAYOUT = [
    {"id": "qc_pending_count_kpi", "size": "small", "order": 1, "visible": True},
    {"id": "qc_open_ncrs_kpi", "size": "small", "order": 2, "visible": True},
    {"id": "qc_pending_list", "size": "large", "order": 3, "visible": True},
    {"id": "qc_recent_ncrs_list", "size": "large", "order": 4, "visible": True},
]

# Map dashboard types to their default layouts
DEFAULT_LAYOUTS = {
    "main": DEFAULT_WIDGET_LAYOUT,
    "planner": DEFAULT_PLANNER_WIDGET_LAYOUT,
    "manager": DEFAULT_MANAGER_WIDGET_LAYOUT,
    "technician": DEFAULT_TECHNICIAN_WIDGET_LAYOUT,
    "qc": DEFAULT_QC_WIDGET_LAYOUT,
}


def _migrate_shortcut_widgets(widget_list):
    """Convert legacy shortcut_* widgets to custom_page_* format in-place."""
    counter = 0
    # Find max existing custom_page_ index
    for w in widget_list:
        if isinstance(w, dict) and w.get("id", "").startswith("custom_page_"):
            idx = int(w["id"].replace("custom_page_", ""), 10)
            if idx >= counter:
                counter = idx + 1

    changed = False
    for w in widget_list:
        if not isinstance(w, dict):
            continue
        wid = w.get("id", "")
        if not wid.startswith("shortcut_"):
            continue
        legacy = LEGACY_SHORTCUT_MAP.get(wid, {})
        if not legacy:
            continue
        # Convert to custom_page_
        w["id"] = f"custom_page_{counter}"
        w.setdefault("url", legacy["url"])
        w.setdefault("page_name", legacy["page_name"])
        w.setdefault("page_icon", legacy["page_icon"])
        counter += 1
        changed = True
    return changed


def get_user_widget_layout(user, dashboard_type="main", default_fallback=None):
    """Get the widget layout for a user and dashboard type, or return default.

    Args:
        user: The user to get layout for
        dashboard_type: The dashboard type (main, manager, planner, etc., or saved_<id>)
        default_fallback: Optional custom default to use instead of global defaults
    """
    try:
        preferences = UserPreference.objects.get(user=user)
        widgets = preferences.dashboard_widgets

        # New format: dict with dashboard_type keys
        if widgets and isinstance(widgets, dict):
            dashboard_widgets = widgets.get(dashboard_type)
            if dashboard_widgets and isinstance(dashboard_widgets, list) and len(dashboard_widgets) > 0:
                # Auto-migrate shortcut_* to custom_page_*
                if _migrate_shortcut_widgets(dashboard_widgets):
                    preferences.dashboard_widgets = widgets
                    preferences.save(update_fields=["dashboard_widgets"])
                return dashboard_widgets
        # Legacy format: just a list (treat as main dashboard)
        elif widgets and isinstance(widgets, list) and len(widgets) > 0:
            if dashboard_type == "main":
                if _migrate_shortcut_widgets(widgets):
                    preferences.dashboard_widgets = {"main": widgets}
                    preferences.save(update_fields=["dashboard_widgets"])
                return widgets
    except UserPreference.DoesNotExist:
        pass

    # Use custom default fallback if provided
    if default_fallback is not None:
        return [w.copy() if isinstance(w, dict) else w for w in default_fallback]

    # Return appropriate default layout for dashboard type
    default_layout = DEFAULT_LAYOUTS.get(dashboard_type, DEFAULT_WIDGET_LAYOUT)
    return [w.copy() for w in default_layout]


# Legacy shortcut widget mapping for backward compatibility with saved layouts
# that reference shortcut_* IDs without url/page_name/page_icon in the config.
LEGACY_SHORTCUT_MAP = {
    "shortcut_designs": {"url": "technology:design_list", "page_name": "Designs", "page_icon": "pen-tool"},
    "shortcut_boms": {"url": "technology:bom_list", "page_name": "Bills of Materials", "page_icon": "package"},
    "shortcut_bom_create": {"url": "technology:bom_create", "page_name": "Create BOM", "page_icon": "file-plus"},
    "shortcut_cutter_map": {"url": "cutter_map:index", "page_name": "Cutter Map", "page_icon": "scan"},
    "shortcut_cutter_inventory": {"url": "inventory:cutter_inventory_list", "page_name": "Cutter Inventory", "page_icon": "circle-dot"},
    "shortcut_items": {"url": "inventory:item_list", "page_name": "Inventory Items", "page_icon": "package"},
    "shortcut_stock_import": {"url": "inventory:stock_import", "page_name": "Stock Import (ERP)", "page_icon": "upload"},
    "shortcut_drill_bits": {"url": "workorders:drillbit_list_enhanced", "page_name": "Drill Bits", "page_icon": "disc"},
    "shortcut_register_bit": {"url": "workorders:drillbit_create", "page_name": "Register New Bit", "page_icon": "plus-circle"},
    "shortcut_work_orders": {"url": "workorders:workorder_list_enhanced", "page_name": "Work Orders", "page_icon": "clipboard-list"},
    "shortcut_create_wo": {"url": "workorders:create", "page_name": "Create Work Order", "page_icon": "file-plus-2"},
    "shortcut_accounts": {"url": "sales:account_list", "page_name": "Accounts", "page_icon": "building-2"},
    "shortcut_customers": {"url": "sales:customer_list", "page_name": "Customers", "page_icon": "users"},
    "shortcut_vendors": {"url": "supplychain:supplier_list", "page_name": "Vendors", "page_icon": "building-2"},
    "shortcut_purchase_orders": {"url": "supplychain:po_list", "page_name": "Purchase Orders", "page_icon": "file-output"},
    "shortcut_grn": {"url": "inventory:grn_list", "page_name": "Goods Receipt (GRN)", "page_icon": "download"},
    "shortcut_hdbs_types": {"url": "technology:hdbs_type_list", "page_name": "Types (HDBS/SMI)", "page_icon": "layers"},
    "shortcut_ncrs": {"url": "quality:ncr_list", "page_name": "NCRs", "page_icon": "alert-triangle"},
    "shortcut_inspections": {"url": "quality:inspection_list", "page_name": "Inspections", "page_icon": "search"},
    "shortcut_process_routes": {"url": "workorders:processroute_list", "page_name": "Process Routes", "page_icon": "git-branch"},
    "shortcut_bit_events": {"url": "workorders:bitevent_list", "page_name": "Bit Events", "page_icon": "activity"},
    "shortcut_stock_ledger": {"url": "inventory:stock_ledger_list", "page_name": "Stock Ledger", "page_icon": "book"},
    "shortcut_locations": {"url": "workorders:location_list", "page_name": "Locations", "page_icon": "map-pin"},
    "shortcut_rigs": {"url": "sales:rig_list", "page_name": "Rigs", "page_icon": "anchor"},
    "shortcut_wells": {"url": "sales:well_list", "page_name": "Wells", "page_icon": "target"},
    "shortcut_sales_orders": {"url": "sales:salesorder_list", "page_name": "Sales Orders", "page_icon": "shopping-cart"},
    "shortcut_pockets_layout": {"url": "technology:pockets_layout_list", "page_name": "Pockets Layout", "page_icon": "grid-3x3"},
    "shortcut_connections": {"url": "technology:connection_list", "page_name": "Connections", "page_icon": "link"},
    "shortcut_equipment": {"url": "maintenance:equipment_list", "page_name": "Equipment", "page_icon": "cpu"},
    "shortcut_procedures": {"url": "procedures:procedure_list", "page_name": "Procedures", "page_icon": "book-open"},
}

def build_widgets_from_layout(widget_layout, user):
    """Build widgets with data and styles from a layout configuration."""
    widgets = []
    for widget_config in widget_layout:
        if widget_config.get("visible", True):
            widget_id = widget_config["id"]
            widget_info = AVAILABLE_WIDGETS.get(widget_id, {})

            # Page shortcuts read from config
            is_page_shortcut = widget_id.startswith("custom_page_")
            if is_page_shortcut:
                name = widget_config.get("page_name", "Page")
                icon = widget_config.get("page_icon", "external-link")
                url = widget_config.get("url", "")
                widget_data = {"url": url, "page_name": name}
            else:
                name = widget_info.get("name", widget_id)
                icon = widget_info.get("icon", "square")
                widget_data = get_widget_data(widget_id, user)

            widgets.append({
                "id": widget_id,
                "name": name,
                "description": f"Shortcut to {name}" if is_page_shortcut else widget_info.get("description", ""),
                "icon": icon,
                "size": widget_config.get("size", "medium"),
                "category": widget_info.get("category", "utilities"),
                "data": widget_data,
                # Style properties
                "color": widget_config.get("color", "blue"),
                "color_intensity": widget_config.get("color_intensity", "medium"),
                "bg_style": widget_config.get("bg_style", "solid"),
                "border_style": widget_config.get("border_style", "none"),
                "border_size": widget_config.get("border_size", "medium"),
                "text_size": widget_config.get("text_size", "normal"),
                "border_radius": widget_config.get("border_radius", "rounded"),
                "show_header": widget_config.get("show_header", True),
            })
    return widgets


def save_user_widget_layout(user, widget_config, dashboard_type="main"):
    """Save widget layout for a specific dashboard type."""
    print(f"[DEBUG] save_user_widget_layout: user={user.username}, dashboard_type={dashboard_type}")
    print(f"[DEBUG] widget_config to save has {len(widget_config)} widgets")
    if widget_config:
        print(f"[DEBUG] First widget being saved: {widget_config[0]}")

    preferences, created = UserPreference.objects.get_or_create(user=user)
    print(f"[DEBUG] UserPreference created={created}")

    # Get existing config or initialize as dict
    existing = preferences.dashboard_widgets
    if not isinstance(existing, dict):
        # Migrate legacy format (list) to new format (dict)
        if isinstance(existing, list) and len(existing) > 0:
            existing = {"main": existing}
        else:
            existing = {}

    # Update the specific dashboard type
    existing[dashboard_type] = widget_config
    preferences.dashboard_widgets = existing
    preferences.save()
    print(f"[DEBUG] Saved! Keys now: {list(preferences.dashboard_widgets.keys())}")
    return preferences


def get_widget_data(widget_id, user):
    """Get data for a specific widget."""
    from apps.quality.models import NCR
    from apps.workorders.models import DrillBit, WorkOrder

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    if widget_id == "work_orders_summary":
        return {
            "total": WorkOrder.objects.count(),
            "active": WorkOrder.objects.filter(status__in=["IN_PROGRESS", "PLANNED", "RELEASED"]).count(),
            "completed_week": WorkOrder.objects.filter(status="COMPLETED", actual_end__date__gte=week_ago).count(),
            "overdue": WorkOrder.objects.filter(
                due_date__lt=today, status__in=["PLANNED", "IN_PROGRESS", "ON_HOLD"]
            ).count(),
        }

    elif widget_id == "drill_bits_status":
        return {
            "total": DrillBit.objects.count(),
            "in_stock": DrillBit.objects.filter(status="IN_STOCK").count(),
            "in_production": DrillBit.objects.filter(status="IN_PRODUCTION").count(),
        }

    elif widget_id == "recent_work_orders":
        return {
            "work_orders": WorkOrder.objects.select_related("customer", "assigned_to").order_by("-created_at")[:5]
        }

    elif widget_id == "overdue_work_orders":
        return {
            "overdue": WorkOrder.objects.filter(
                due_date__lt=today, status__in=["PLANNED", "IN_PROGRESS", "ON_HOLD"]
            ).count(),
        }

    elif widget_id == "maintenance_due":
        from apps.maintenance.models import Equipment

        return {
            "overdue": Equipment.objects.filter(
                status=Equipment.Status.OPERATIONAL,
                maintenance_interval_days__isnull=False,
                next_maintenance__lt=today,
            ).count(),
            "due_soon": Equipment.objects.filter(
                status=Equipment.Status.OPERATIONAL,
                maintenance_interval_days__isnull=False,
                next_maintenance__range=[today, today + timedelta(days=7)],
            ).count(),
        }

    elif widget_id == "open_ncrs":
        return {
            "open": NCR.objects.filter(status__in=["OPEN", "INVESTIGATING"]).count(),
            "critical": NCR.objects.filter(status__in=["OPEN", "INVESTIGATING"], severity="CRITICAL").count(),
        }

    elif widget_id == "low_stock_alerts":
        from django.db.models import Sum
        from apps.inventory.models import InventoryItem

        try:
            # Count items where total stock is below reorder point
            items_below_reorder = 0
            for item in InventoryItem.objects.filter(is_active=True, reorder_point__gt=0):
                if item.total_stock < item.reorder_point:
                    items_below_reorder += 1
            return {"count": items_below_reorder}
        except Exception:
            return {"count": 0}

    elif widget_id == "pending_approvals":
        from apps.supplychain.models import PurchaseRequisition

        return {
            "pr_count": PurchaseRequisition.objects.filter(status="PENDING").count(),
        }

    elif widget_id == "quick_links":
        return {
            "links": [
                {"name": "Work Orders", "url": "workorders:workorder_list_enhanced", "icon": "clipboard-list"},
                {"name": "Inventory", "url": "inventory:item_list", "icon": "package"},
                {"name": "Quality", "url": "quality:ncr_list", "icon": "shield-check"},
                {"name": "Reports", "url": "reports:dashboard", "icon": "bar-chart"},
            ]
        }

    # =========================================================================
    # PLANNER-SPECIFIC WIDGETS
    # =========================================================================
    elif widget_id == "planner_pending_kpi":
        return {
            "count": WorkOrder.objects.filter(status__in=["DRAFT", "PLANNED"]).count(),
            "label": "awaiting scheduling",
        }

    elif widget_id == "planner_in_progress_kpi":
        return {
            "count": WorkOrder.objects.filter(status="IN_PROGRESS").count(),
            "label": "currently active",
        }

    elif widget_id == "planner_overdue_kpi":
        return {
            "count": WorkOrder.objects.filter(
                due_date__lt=today, status__in=["PLANNED", "IN_PROGRESS", "ON_HOLD"]
            ).count(),
            "label": "needs attention",
        }

    elif widget_id == "planner_due_this_week_kpi":
        week_end = today + timedelta(days=7)
        return {
            "count": WorkOrder.objects.filter(
                due_date__range=[today, week_end], status__in=["PLANNED", "IN_PROGRESS"]
            ).count(),
            "label": "upcoming deadlines",
        }

    elif widget_id == "pending_work_orders_list":
        return {
            "work_orders": WorkOrder.objects.filter(status__in=["DRAFT", "PLANNED"])
            .select_related("customer", "drill_bit")
            .order_by("due_date")[:20],
            "count": WorkOrder.objects.filter(status__in=["DRAFT", "PLANNED"]).count(),
        }

    elif widget_id == "in_progress_work_orders_list":
        return {
            "work_orders": WorkOrder.objects.filter(status="IN_PROGRESS")
            .select_related("customer", "assigned_to")
            .order_by("due_date")[:10],
            "count": WorkOrder.objects.filter(status="IN_PROGRESS").count(),
        }

    elif widget_id == "overdue_work_orders_table":
        return {
            "work_orders": WorkOrder.objects.filter(
                due_date__lt=today, status__in=["PLANNED", "IN_PROGRESS", "ON_HOLD"]
            )
            .select_related("customer", "assigned_to")
            .order_by("due_date")[:10],
            "count": WorkOrder.objects.filter(
                due_date__lt=today, status__in=["PLANNED", "IN_PROGRESS", "ON_HOLD"]
            ).count(),
        }

    # =========================================================================
    # MANAGER-SPECIFIC WIDGETS
    # =========================================================================
    elif widget_id == "manager_total_wo_kpi":
        return {
            "count": WorkOrder.objects.count(),
            "label": "total work orders",
        }

    elif widget_id == "manager_active_wo_kpi":
        return {
            "count": WorkOrder.objects.filter(status__in=["IN_PROGRESS", "PLANNED", "RELEASED"]).count(),
            "label": "active",
        }

    elif widget_id == "manager_completed_week_kpi":
        return {
            "count": WorkOrder.objects.filter(status="COMPLETED", actual_end__date__gte=week_ago).count(),
            "label": "completed this week",
        }

    elif widget_id == "manager_overdue_kpi":
        return {
            "count": WorkOrder.objects.filter(
                due_date__lt=today, status__in=["PLANNED", "IN_PROGRESS", "ON_HOLD"]
            ).count(),
            "label": "overdue",
        }

    elif widget_id == "manager_drill_bits_kpi":
        return {
            "total": DrillBit.objects.count(),
            "in_stock": DrillBit.objects.filter(status="IN_STOCK").count(),
            "in_production": DrillBit.objects.filter(status="IN_PRODUCTION").count(),
        }

    elif widget_id == "work_orders_status_chart":
        status_breakdown = WorkOrder.objects.values("status").annotate(count=Count("id")).order_by("status")
        return {
            "status_breakdown": list(status_breakdown),
        }

    # =========================================================================
    # TECHNICIAN-SPECIFIC WIDGETS
    # =========================================================================
    elif widget_id == "tech_assigned_count_kpi":
        return {
            "count": WorkOrder.objects.filter(assigned_to=user)
            .exclude(status__in=["COMPLETED", "CANCELLED"])
            .count(),
            "label": "assigned to you",
        }

    elif widget_id == "tech_completed_today_kpi":
        return {
            "count": WorkOrder.objects.filter(
                assigned_to=user, status="COMPLETED", actual_end__date=today
            ).count(),
            "label": "completed today",
        }

    elif widget_id == "tech_current_work_order":
        current_wo = WorkOrder.objects.filter(assigned_to=user, status="IN_PROGRESS").first()
        return {
            "work_order": current_wo,
        }

    elif widget_id == "tech_my_work_orders_list":
        return {
            "work_orders": WorkOrder.objects.filter(assigned_to=user)
            .exclude(status__in=["COMPLETED", "CANCELLED"])
            .select_related("customer", "drill_bit")
            .order_by("-priority", "due_date"),
        }

    # =========================================================================
    # QC-SPECIFIC WIDGETS
    # =========================================================================
    elif widget_id == "qc_pending_count_kpi":
        return {
            "count": WorkOrder.objects.filter(status="QC_PENDING").count(),
            "label": "awaiting inspection",
        }

    elif widget_id == "qc_open_ncrs_kpi":
        return {
            "count": NCR.objects.filter(
                status__in=["OPEN", "INVESTIGATING", "PENDING_DISPOSITION", "IN_REWORK"]
            ).count(),
            "label": "open NCRs",
        }

    elif widget_id == "qc_pending_list":
        return {
            "work_orders": WorkOrder.objects.filter(status="QC_PENDING")
            .select_related("customer", "assigned_to", "drill_bit")
            .order_by("due_date"),
        }

    elif widget_id == "qc_recent_ncrs_list":
        return {
            "ncrs": NCR.objects.select_related("work_order", "detected_by").order_by("-created_at")[:10],
        }

    # =========================================================================
    # PAGE SHORTCUT WIDGETS
    # =========================================================================
    elif widget_id.startswith("custom_page_"):
        # Page shortcuts - data comes from layout config, not here
        return {}

    return {}


DASHBOARD_TYPE_NAMES = {
    "main": "Main Dashboard",
    "manager": "Manager Dashboard",
    "planner": "Planner Dashboard",
    "technician": "Technician Dashboard",
    "qc": "QC Dashboard",
}


@login_required
def customize_dashboard(request, dashboard_type="main"):
    """
    Dashboard customization page - allows users to configure their widgets.
    Supports per-dashboard customization based on dashboard_type.
    """
    from .models import SavedDashboard

    user = request.user

    # Validate dashboard_type
    valid_types = ["main", "manager", "planner", "technician", "qc"]
    if dashboard_type not in valid_types and not dashboard_type.startswith("saved_"):
        dashboard_type = "main"

    # Get the default fallback for saved dashboards
    saved_dashboard = None
    default_fallback = None
    if dashboard_type.startswith("saved_"):
        saved_id = dashboard_type.replace("saved_", "")
        try:
            saved_dashboard = SavedDashboard.objects.get(pk=int(saved_id))
            default_fallback = saved_dashboard.widget_config
        except (SavedDashboard.DoesNotExist, ValueError):
            pass

    # Determine redirect URL after save
    redirect_url_map = {
        "main": "dashboard:main",
        "manager": "dashboard:manager",
        "planner": "dashboard:planner",
        "technician": "dashboard:technician",
        "qc": "dashboard:qc",
    }

    if request.method == "POST":
        # Parse the widget configuration from POST
        try:
            widget_config = json.loads(request.POST.get("widget_config", "[]"))
            save_user_widget_layout(user, widget_config, dashboard_type)
            # No success message - saves happen frequently and messages are annoying

            # Redirect to the appropriate dashboard
            if dashboard_type.startswith("saved_"):
                saved_id = dashboard_type.replace("saved_", "")
                return redirect("dashboard:saved_view", pk=int(saved_id))
            return redirect(redirect_url_map.get(dashboard_type, "dashboard:main"))
        except json.JSONDecodeError:
            messages.error(request, "Invalid widget configuration.")

    # Get current layout for this dashboard type (with saved dashboard fallback)
    current_layout = get_user_widget_layout(user, dashboard_type, default_fallback=default_fallback)

    # Add widget metadata to current layout
    for widget in current_layout:
        widget_id = widget["id"]
        if widget_id.startswith("custom_page_"):
            widget["name"] = widget.get("page_name", "Page")
            widget["description"] = f"Shortcut to {widget['name']}"
            widget["icon"] = widget.get("page_icon", "external-link")
            widget["url"] = widget.get("url", "")
            widget["category"] = "pages"
        else:
            widget_info = AVAILABLE_WIDGETS.get(widget_id, {})
            widget["name"] = widget_info.get("name", widget_id)
            widget["description"] = widget_info.get("description", "")
            widget["icon"] = widget_info.get("icon", "square")
            widget["category"] = widget_info.get("category", "utilities")
        widget["visible"] = True

    # Get list of active widget IDs
    active_widget_ids = [w["id"] for w in current_layout]

    # Organize widgets by category for the browser
    widgets_by_category = {}
    for widget_id, widget_info in AVAILABLE_WIDGETS.items():
        category = widget_info.get("category", "utilities")
        if category not in widgets_by_category:
            widgets_by_category[category] = []
        widgets_by_category[category].append({
            "id": widget_id,
            "name": widget_info.get("name", widget_id),
            "description": widget_info.get("description", ""),
            "icon": widget_info.get("icon", "square"),
            "default_size": widget_info.get("default_size", "medium"),
            "is_active": widget_id in active_widget_ids,
        })

    # Sort widgets within each category by name
    for category in widgets_by_category:
        widgets_by_category[category].sort(key=lambda x: x["name"])

    # Get dashboard name for title
    if dashboard_type.startswith("saved_"):
        # Use saved_dashboard if we already loaded it, otherwise fetch
        if saved_dashboard:
            dashboard_name = saved_dashboard.name
        else:
            saved_id = dashboard_type.replace("saved_", "")
            try:
                saved_dash = SavedDashboard.objects.get(pk=int(saved_id))
                dashboard_name = saved_dash.name
            except (SavedDashboard.DoesNotExist, ValueError):
                dashboard_name = "Custom Dashboard"
    else:
        dashboard_name = DASHBOARD_TYPE_NAMES.get(dashboard_type, "Dashboard")

    context = {
        "page_title": f"Customize {dashboard_name}",
        "dashboard_type": dashboard_type,
        "dashboard_name": dashboard_name,
        "available_widgets": AVAILABLE_WIDGETS,
        "widget_categories": WIDGET_CATEGORIES,
        "widgets_by_category": widgets_by_category,
        "current_layout": current_layout,
        "current_layout_json": json.dumps(current_layout),
        "total_widgets": len(AVAILABLE_WIDGETS),
        "active_widget_count": len(active_widget_ids),
        "page_registry": PAGE_REGISTRY,
    }
    return render(request, "dashboard/customize.html", context)


@login_required
@require_POST
def save_widget_order(request, dashboard_type="main"):
    """
    AJAX endpoint to save widget order for a specific dashboard type.
    """
    user = request.user

    try:
        data = json.loads(request.body)
        widget_config = data.get("widgets", [])
        # Allow dashboard_type override from request body
        dashboard_type = data.get("dashboard_type", dashboard_type)

        # Debug logging
        print(f"[DEBUG] save_widget_order called: user={user.username}, dashboard_type={dashboard_type}")
        print(f"[DEBUG] widget_config has {len(widget_config)} widgets")
        if widget_config:
            print(f"[DEBUG] First widget: {widget_config[0]}")

        save_user_widget_layout(user, widget_config, dashboard_type)

        return JsonResponse({"success": True})
    except (json.JSONDecodeError, Exception) as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_POST
def toggle_widget(request, widget_id):
    """
    Toggle a widget's visibility.
    """
    user = request.user

    preferences, created = UserPreference.objects.get_or_create(user=user)
    current_layout = get_user_widget_layout(user)

    # Find and toggle the widget
    found = False
    for widget in current_layout:
        if widget["id"] == widget_id:
            widget["visible"] = not widget.get("visible", True)
            found = True
            break

    # If widget not in layout, add it
    if not found and widget_id in AVAILABLE_WIDGETS:
        current_layout.append({
            "id": widget_id,
            "size": AVAILABLE_WIDGETS[widget_id].get("default_size", "medium"),
            "order": len(current_layout) + 1,
            "visible": True,
        })

    preferences.dashboard_widgets = current_layout
    preferences.save()

    return JsonResponse({"success": True})


@login_required
def reset_dashboard(request, dashboard_type="main"):
    """
    Reset dashboard to default layout for a specific dashboard type.
    """
    user = request.user

    # Get the appropriate default layout for this dashboard type
    default_layout = DEFAULT_LAYOUTS.get(dashboard_type, DEFAULT_WIDGET_LAYOUT)
    save_user_widget_layout(user, [w.copy() for w in default_layout], dashboard_type)
    # No success message - user will see the reset visually

    # Redirect to the appropriate dashboard
    redirect_url_map = {
        "main": "dashboard:main",
        "manager": "dashboard:manager",
        "planner": "dashboard:planner",
        "technician": "dashboard:technician",
        "qc": "dashboard:qc",
    }
    if dashboard_type.startswith("saved_"):
        saved_id = dashboard_type.replace("saved_", "")
        return redirect("dashboard:saved_view", pk=int(saved_id))
    return redirect(redirect_url_map.get(dashboard_type, "dashboard:main"))


# =============================================================================
# Saved Dashboard Views
# =============================================================================

from django.db.models import Q
from django.http import Http404
from .models import DashboardFavorite, SavedDashboard


@login_required
def saved_dashboard_list(request):
    """
    List all dashboards the user can access.
    """
    user = request.user

    # Get dashboards the user can see
    user_roles = user.roles.all()

    dashboards = SavedDashboard.objects.filter(
        Q(created_by=user) |  # Own dashboards
        Q(visibility=SavedDashboard.Visibility.PUBLIC) |  # Public dashboards
        Q(visibility=SavedDashboard.Visibility.SHARED, shared_with_roles__in=user_roles)  # Shared with user's roles
    ).distinct().select_related("created_by")

    # Get user's favorites
    favorite_ids = DashboardFavorite.objects.filter(user=user).values_list("dashboard_id", flat=True)

    context = {
        "page_title": "My Dashboards",
        "dashboards": dashboards,
        "favorite_ids": list(favorite_ids),
        "my_dashboards": dashboards.filter(created_by=user),
        "shared_dashboards": dashboards.exclude(created_by=user),
    }
    return render(request, "dashboard/saved_list.html", context)


@login_required
def saved_dashboard_create(request):
    """
    Create a new saved dashboard.
    """
    user = request.user

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        icon = request.POST.get("icon", "layout-dashboard")
        visibility = request.POST.get("visibility", SavedDashboard.Visibility.PRIVATE)
        show_in_sidebar = request.POST.get("show_in_sidebar") == "on"

        if not name:
            messages.error(request, "Dashboard name is required.")
            return redirect("dashboard:saved_create")

        # Get current layout from user preferences
        preferences, _ = UserPreference.objects.get_or_create(user=user)
        widget_config = get_user_widget_layout(user)

        dashboard = SavedDashboard.objects.create(
            name=name,
            description=description,
            icon=icon,
            created_by=user,
            widget_config=widget_config,
            visibility=visibility,
            show_in_sidebar=show_in_sidebar,
        )

        # Handle role sharing
        if visibility == SavedDashboard.Visibility.SHARED:
            role_ids = request.POST.getlist("shared_roles")
            if role_ids:
                from apps.accounts.models import Role
                roles = Role.objects.filter(id__in=role_ids)
                dashboard.shared_with_roles.set(roles)

        messages.success(request, f'Dashboard "{name}" created successfully!')
        return redirect("dashboard:saved_list")

    # Get available roles for sharing
    from apps.accounts.models import Role
    roles = Role.objects.filter(is_active=True)

    context = {
        "page_title": "Create Dashboard",
        "roles": roles,
        "available_icons": [
            "layout-dashboard", "grid-3x3", "bar-chart-2", "pie-chart",
            "line-chart", "activity", "target", "zap", "users", "briefcase",
            "factory", "wrench", "package", "shield-check", "clipboard-list"
        ],
    }
    return render(request, "dashboard/saved_create.html", context)


@login_required
def saved_dashboard_view(request, pk):
    """
    View a saved dashboard.
    Uses dynamic widget system for customization.
    Supports per-user customization via UserPreference.
    """
    user = request.user

    try:
        dashboard = SavedDashboard.objects.select_related("created_by").get(pk=pk)
    except SavedDashboard.DoesNotExist:
        raise Http404("Dashboard not found")

    if not dashboard.can_view(user):
        messages.error(request, "You don't have permission to view this dashboard.")
        return redirect("dashboard:saved_list")

    # Get user's customized layout, falling back to dashboard's original config
    dashboard_type_key = dashboard.dashboard_type_key
    widget_layout = get_user_widget_layout(user, dashboard_type_key, default_fallback=dashboard.widget_config)

    # Debug logging
    print(f"[DEBUG] saved_dashboard_view: dashboard_type_key={dashboard_type_key}")
    print(f"[DEBUG] widget_layout has {len(widget_layout)} widgets")
    if widget_layout:
        print(f"[DEBUG] First widget color: {widget_layout[0].get('color', 'NOT SET')}")

    # Build widgets with data using helper function
    widgets = build_widgets_from_layout(widget_layout, user)

    # Check if user has favorited this dashboard
    is_favorite = DashboardFavorite.objects.filter(user=user, dashboard=dashboard).exists()

    context = {
        "page_title": dashboard.name,
        "dashboard": dashboard,
        "dashboard_type": dashboard.dashboard_type_key,
        "widgets": widgets,
        "is_favorite": is_favorite,
        "can_edit": dashboard.can_edit(user),
    }
    return render(request, "dashboard/saved_view.html", context)


@login_required
def saved_dashboard_edit(request, pk):
    """
    Edit a saved dashboard.
    """
    user = request.user

    try:
        dashboard = SavedDashboard.objects.get(pk=pk)
    except SavedDashboard.DoesNotExist:
        raise Http404("Dashboard not found")

    if not dashboard.can_edit(user):
        messages.error(request, "You don't have permission to edit this dashboard.")
        return redirect("dashboard:saved_list")

    if request.method == "POST":
        dashboard.name = request.POST.get("name", dashboard.name).strip()
        dashboard.description = request.POST.get("description", "").strip()
        dashboard.icon = request.POST.get("icon", "layout-dashboard")
        dashboard.visibility = request.POST.get("visibility", SavedDashboard.Visibility.PRIVATE)
        dashboard.show_in_sidebar = request.POST.get("show_in_sidebar") == "on"

        # Handle widget config if provided
        widget_config = request.POST.get("widget_config")
        if widget_config:
            try:
                dashboard.widget_config = json.loads(widget_config)
            except json.JSONDecodeError:
                pass

        dashboard.save()

        # Handle role sharing
        if dashboard.visibility == SavedDashboard.Visibility.SHARED:
            role_ids = request.POST.getlist("shared_roles")
            from apps.accounts.models import Role
            roles = Role.objects.filter(id__in=role_ids)
            dashboard.shared_with_roles.set(roles)
        else:
            dashboard.shared_with_roles.clear()

        messages.success(request, f'Dashboard "{dashboard.name}" updated successfully!')
        return redirect("dashboard:saved_list")

    # Get available roles for sharing
    from apps.accounts.models import Role
    roles = Role.objects.filter(is_active=True)

    context = {
        "page_title": f"Edit {dashboard.name}",
        "dashboard": dashboard,
        "roles": roles,
        "selected_role_ids": list(dashboard.shared_with_roles.values_list("id", flat=True)),
        "available_icons": [
            "layout-dashboard", "grid-3x3", "bar-chart-2", "pie-chart",
            "line-chart", "activity", "target", "zap", "users", "briefcase",
            "factory", "wrench", "package", "shield-check", "clipboard-list"
        ],
    }
    return render(request, "dashboard/saved_edit.html", context)


@login_required
def saved_dashboard_delete(request, pk):
    """
    Delete a saved dashboard.
    GET: Show confirmation page
    POST: Actually delete
    """
    user = request.user

    try:
        dashboard = SavedDashboard.objects.get(pk=pk)
    except SavedDashboard.DoesNotExist:
        raise Http404("Dashboard not found")

    if not dashboard.can_edit(user):
        messages.error(request, "You don't have permission to delete this dashboard.")
        return redirect("dashboard:saved_list")

    if request.method == "POST":
        name = dashboard.name
        dashboard.delete()
        messages.success(request, f'Dashboard "{name}" deleted successfully!')
        return redirect("dashboard:saved_list")

    # GET request - show confirmation page
    context = {
        "page_title": f"Delete {dashboard.name}",
        "dashboard": dashboard,
    }
    return render(request, "dashboard/saved_delete.html", context)


@login_required
@require_POST
def toggle_dashboard_favorite(request, pk):
    """
    Toggle favorite status for a dashboard.
    """
    user = request.user

    try:
        dashboard = SavedDashboard.objects.get(pk=pk)
    except SavedDashboard.DoesNotExist:
        return JsonResponse({"success": False, "error": "Dashboard not found"}, status=404)

    if not dashboard.can_view(user):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    favorite, created = DashboardFavorite.objects.get_or_create(
        user=user,
        dashboard=dashboard,
        defaults={"order": 0}
    )

    if not created:
        favorite.delete()
        return JsonResponse({"success": True, "favorited": False})

    return JsonResponse({"success": True, "favorited": True})


@login_required
@require_POST
def save_as_dashboard(request):
    """
    Save current layout as a new dashboard.
    """
    user = request.user

    try:
        data = json.loads(request.body)
        name = data.get("name", "").strip()
        description = data.get("description", "").strip()
        widget_config = data.get("widgets", [])

        if not name:
            return JsonResponse({"success": False, "error": "Name is required"}, status=400)

        dashboard = SavedDashboard.objects.create(
            name=name,
            description=description,
            created_by=user,
            widget_config=widget_config,
            visibility=SavedDashboard.Visibility.PRIVATE,
        )

        return JsonResponse({
            "success": True,
            "dashboard_id": dashboard.id,
            "message": f'Dashboard "{name}" saved successfully!'
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)


def get_user_accessible_dashboards(user):
    """
    Get all dashboards a user can access for sidebar display.
    """
    user_roles = user.roles.all()

    dashboards = SavedDashboard.objects.filter(
        Q(created_by=user) |
        Q(visibility=SavedDashboard.Visibility.PUBLIC) |
        Q(visibility=SavedDashboard.Visibility.SHARED, shared_with_roles__in=user_roles)
    ).filter(
        is_active=True,
        show_in_sidebar=True
    ).distinct().order_by("-is_default", "name")[:10]  # Limit to 10 for sidebar

    return dashboards
