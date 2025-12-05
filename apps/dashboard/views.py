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
    Shows general overview and quick links.
    """
    context = {
        "page_title": "Dashboard",
        "user": request.user,
    }
    return render(request, "dashboard/main.html", context)


@login_required
def manager_dashboard(request):
    """
    Manager dashboard with KPIs and overview statistics.
    """
    from apps.workorders.models import DrillBit, WorkOrder

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # Work order statistics
    total_work_orders = WorkOrder.objects.count()
    active_work_orders = WorkOrder.objects.filter(status__in=["IN_PROGRESS", "PLANNED", "RELEASED"]).count()
    completed_this_week = WorkOrder.objects.filter(status="COMPLETED", actual_end__date__gte=week_ago).count()
    overdue_work_orders = WorkOrder.objects.filter(
        due_date__lt=today, status__in=["PLANNED", "IN_PROGRESS", "ON_HOLD"]
    ).count()

    # Drill bit statistics
    total_drill_bits = DrillBit.objects.count()
    in_stock_bits = DrillBit.objects.filter(status="IN_STOCK").count()
    in_production_bits = DrillBit.objects.filter(status="IN_PRODUCTION").count()

    # Status breakdown for chart
    status_breakdown = WorkOrder.objects.values("status").annotate(count=Count("id")).order_by("status")

    # Recent work orders
    recent_work_orders = WorkOrder.objects.select_related("customer", "assigned_to", "drill_bit").order_by("-created_at")[:10]

    context = {
        "page_title": "Manager Dashboard",
        "total_work_orders": total_work_orders,
        "active_work_orders": active_work_orders,
        "completed_this_week": completed_this_week,
        "overdue_work_orders": overdue_work_orders,
        "total_drill_bits": total_drill_bits,
        "in_stock_bits": in_stock_bits,
        "in_production_bits": in_production_bits,
        "status_breakdown": list(status_breakdown),
        "recent_work_orders": recent_work_orders,
    }
    return render(request, "dashboard/manager.html", context)


@login_required
def planner_dashboard(request):
    """
    Planner dashboard focused on scheduling and planning.
    Optimized to avoid N+1 queries.
    """
    from apps.workorders.models import WorkOrder

    today = timezone.now().date()
    week_end = today + timedelta(days=7)

    # Get all counts in a single query using aggregate
    status_counts = WorkOrder.objects.aggregate(
        pending=Count("id", filter=Q(status__in=["DRAFT", "PLANNED"])),
        in_progress=Count("id", filter=Q(status="IN_PROGRESS")),
        overdue=Count("id", filter=Q(due_date__lt=today, status__in=["PLANNED", "IN_PROGRESS", "ON_HOLD"])),
        due_this_week=Count("id", filter=Q(due_date__range=[today, week_end], status__in=["PLANNED", "IN_PROGRESS"])),
    )

    # Work order lists (separate queries for display)
    pending_work_orders = (
        WorkOrder.objects.filter(status__in=["DRAFT", "PLANNED"])
        .select_related("customer", "drill_bit")
        .order_by("due_date")[:20]
    )

    in_progress_work_orders = (
        WorkOrder.objects.filter(status="IN_PROGRESS").select_related("customer", "assigned_to").order_by("due_date")[:10]
    )

    overdue_work_orders = (
        WorkOrder.objects.filter(due_date__lt=today, status__in=["PLANNED", "IN_PROGRESS", "ON_HOLD"])
        .select_related("customer", "assigned_to")
        .order_by("due_date")[:10]
    )

    context = {
        "page_title": "Planner Dashboard",
        "pending_work_orders": pending_work_orders,
        "in_progress_work_orders": in_progress_work_orders,
        "overdue_work_orders": overdue_work_orders,
        "pending_count": status_counts["pending"],
        "in_progress_count": status_counts["in_progress"],
        "overdue_count": status_counts["overdue"],
        "due_this_week": status_counts["due_this_week"],
    }
    return render(request, "dashboard/planner.html", context)


@login_required
def technician_dashboard(request):
    """
    Technician dashboard showing assigned work orders.
    """
    from apps.workorders.models import WorkOrder

    user = request.user

    # My assigned work orders
    my_work_orders = (
        WorkOrder.objects.filter(assigned_to=user)
        .exclude(status__in=["COMPLETED", "CANCELLED"])
        .select_related("customer", "drill_bit")
        .order_by("-priority", "due_date")
    )

    # Completed today
    today = timezone.now().date()
    completed_today = WorkOrder.objects.filter(assigned_to=user, status="COMPLETED", actual_end__date=today).count()

    # In progress
    in_progress = WorkOrder.objects.filter(assigned_to=user, status="IN_PROGRESS").first()

    context = {
        "page_title": "My Dashboard",
        "my_work_orders": my_work_orders,
        "assigned_count": my_work_orders.count(),
        "completed_today": completed_today,
        "current_work_order": in_progress,
    }
    return render(request, "dashboard/technician.html", context)


@login_required
def qc_dashboard(request):
    """
    QC Inspector dashboard showing inspections and NCRs.
    """
    from apps.quality.models import NCR
    from apps.workorders.models import WorkOrder

    # Pending QC
    pending_qc = (
        WorkOrder.objects.filter(status="QC_PENDING")
        .select_related("customer", "assigned_to", "drill_bit")
        .order_by("due_date")
    )

    # Recent NCRs
    recent_ncrs = NCR.objects.select_related("work_order", "detected_by").order_by("-created_at")[:10]

    # Statistics
    open_ncrs = NCR.objects.filter(status__in=["OPEN", "INVESTIGATING", "PENDING_DISPOSITION", "IN_REWORK"]).count()

    context = {
        "page_title": "QC Dashboard",
        "pending_qc": pending_qc,
        "pending_qc_count": pending_qc.count(),
        "recent_ncrs": recent_ncrs,
        "open_ncrs": open_ncrs,
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

# Available widgets configuration
AVAILABLE_WIDGETS = {
    "work_orders_summary": {
        "name": "Work Orders Summary",
        "description": "Active, completed, and overdue work order counts",
        "icon": "clipboard-list",
        "default_size": "medium",
    },
    "drill_bits_status": {
        "name": "Drill Bits Status",
        "description": "Overview of drill bit inventory status",
        "icon": "tool",
        "default_size": "small",
    },
    "recent_work_orders": {
        "name": "Recent Work Orders",
        "description": "List of recently created work orders",
        "icon": "clock",
        "default_size": "large",
    },
    "maintenance_due": {
        "name": "Maintenance Due",
        "description": "Equipment due for maintenance",
        "icon": "wrench",
        "default_size": "medium",
    },
    "open_ncrs": {
        "name": "Open NCRs",
        "description": "Non-conformance reports requiring attention",
        "icon": "alert-triangle",
        "default_size": "medium",
    },
    "low_stock_alerts": {
        "name": "Low Stock Alerts",
        "description": "Inventory items below reorder point",
        "icon": "package",
        "default_size": "medium",
    },
    "pending_approvals": {
        "name": "Pending Approvals",
        "description": "Items awaiting your approval",
        "icon": "check-circle",
        "default_size": "small",
    },
    "quick_links": {
        "name": "Quick Links",
        "description": "Shortcuts to frequently used modules",
        "icon": "link",
        "default_size": "small",
    },
}

DEFAULT_WIDGET_LAYOUT = [
    {"id": "work_orders_summary", "size": "medium", "order": 1, "visible": True},
    {"id": "drill_bits_status", "size": "small", "order": 2, "visible": True},
    {"id": "recent_work_orders", "size": "large", "order": 3, "visible": True},
    {"id": "quick_links", "size": "small", "order": 4, "visible": True},
]


def get_user_widget_layout(user):
    """Get the widget layout for a user, or return default."""
    try:
        preferences = UserPreference.objects.get(user=user)
        widgets = preferences.dashboard_widgets
        if widgets and isinstance(widgets, list) and len(widgets) > 0:
            return widgets
    except UserPreference.DoesNotExist:
        pass
    return DEFAULT_WIDGET_LAYOUT


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
        from django.db.models import F as ModelF
        from apps.inventory.models import Stock

        try:
            return {
                "count": Stock.objects.filter(quantity_on_hand__lte=ModelF("reorder_point")).count()
            }
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
                {"name": "Work Orders", "url": "workorders:list", "icon": "clipboard-list"},
                {"name": "Inventory", "url": "inventory:item_list", "icon": "package"},
                {"name": "Quality", "url": "quality:ncr_list", "icon": "shield-check"},
                {"name": "Reports", "url": "reports:dashboard", "icon": "bar-chart"},
            ]
        }

    return {}


@login_required
def customize_dashboard(request):
    """
    Dashboard customization page - allows users to configure their widgets.
    """
    user = request.user

    # Get or create preferences
    preferences, created = UserPreference.objects.get_or_create(user=user)

    if request.method == "POST":
        # Parse the widget configuration from POST
        try:
            widget_config = json.loads(request.POST.get("widget_config", "[]"))
            preferences.dashboard_widgets = widget_config
            preferences.save()
            messages.success(request, "Dashboard layout saved successfully!")
            return redirect("dashboard:main")
        except json.JSONDecodeError:
            messages.error(request, "Invalid widget configuration.")

    # Get current layout
    current_layout = get_user_widget_layout(user)

    # Add widget metadata to current layout
    for widget in current_layout:
        widget_info = AVAILABLE_WIDGETS.get(widget["id"], {})
        widget["name"] = widget_info.get("name", widget["id"])
        widget["description"] = widget_info.get("description", "")
        widget["icon"] = widget_info.get("icon", "square")

    context = {
        "page_title": "Customize Dashboard",
        "available_widgets": AVAILABLE_WIDGETS,
        "current_layout": current_layout,
        "current_layout_json": json.dumps(current_layout),
    }
    return render(request, "dashboard/customize.html", context)


@login_required
@require_POST
def save_widget_order(request):
    """
    AJAX endpoint to save widget order.
    """
    user = request.user

    try:
        data = json.loads(request.body)
        widget_config = data.get("widgets", [])

        preferences, created = UserPreference.objects.get_or_create(user=user)
        preferences.dashboard_widgets = widget_config
        preferences.save()

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
def reset_dashboard(request):
    """
    Reset dashboard to default layout.
    """
    user = request.user

    preferences, created = UserPreference.objects.get_or_create(user=user)
    preferences.dashboard_widgets = DEFAULT_WIDGET_LAYOUT.copy()
    preferences.save()

    messages.success(request, "Dashboard reset to default layout.")
    return redirect("dashboard:main")
