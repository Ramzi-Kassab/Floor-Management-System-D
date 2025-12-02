"""
ARDT FMS - Dashboard Views
Version: 5.4 - Sprint 1

Role-based dashboard views with KPIs and statistics.
"""

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone


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
