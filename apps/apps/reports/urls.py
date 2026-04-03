"""
ARDT FMS - Reports URLs
Version: 5.4
"""

from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    # Dashboard
    path("", views.ReportsDashboardView.as_view(), name="dashboard"),
    # Work Orders
    path("work-orders/", views.WorkOrderReportView.as_view(), name="workorder_report"),
    # Inventory
    path("inventory/", views.InventoryReportView.as_view(), name="inventory_report"),
    path("inventory/low-stock/", views.LowStockAlertView.as_view(), name="low_stock_alert"),
    # Quality
    path("quality/", views.QualityReportView.as_view(), name="quality_report"),
    # Maintenance
    path("maintenance/", views.MaintenanceReportView.as_view(), name="maintenance_report"),
    path("equipment-health/", views.EquipmentHealthReportView.as_view(), name="equipment_health"),
    # Supply Chain
    path("supply-chain/", views.SupplyChainReportView.as_view(), name="supplychain_report"),
]
