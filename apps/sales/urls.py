"""
ARDT FMS - Sales URLs
Version: 5.4 - Sprint 2

URL patterns for customer, rig, well, and warehouse management.
"""

from django.urls import path

from . import views

app_name = "sales"

urlpatterns = [
    # ==========================================================================
    # CUSTOMER URLS
    # ==========================================================================
    path("customers/", views.CustomerListView.as_view(), name="customer_list"),
    path("customers/create/", views.CustomerCreateView.as_view(), name="customer_create"),
    path("customers/<int:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("customers/<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="customer_update"),
    path("customers/export/", views.export_customers_csv, name="customer_export"),
    # Customer contacts
    path("customers/<int:customer_pk>/contacts/add/", views.add_contact, name="contact_add"),
    path("contacts/<int:pk>/edit/", views.edit_contact, name="contact_edit"),
    path("contacts/<int:pk>/delete/", views.delete_contact, name="contact_delete"),
    # ==========================================================================
    # RIG URLS
    # ==========================================================================
    path("rigs/", views.RigListView.as_view(), name="rig_list"),
    path("rigs/create/", views.RigCreateView.as_view(), name="rig_create"),
    path("rigs/<int:pk>/", views.RigDetailView.as_view(), name="rig_detail"),
    path("rigs/<int:pk>/edit/", views.RigUpdateView.as_view(), name="rig_update"),
    path("rigs/export/", views.export_rigs_csv, name="rig_export"),
    # ==========================================================================
    # WELL URLS
    # ==========================================================================
    path("wells/", views.WellListView.as_view(), name="well_list"),
    path("wells/create/", views.WellCreateView.as_view(), name="well_create"),
    path("wells/<int:pk>/", views.WellDetailView.as_view(), name="well_detail"),
    path("wells/<int:pk>/edit/", views.WellUpdateView.as_view(), name="well_update"),
    # ==========================================================================
    # WAREHOUSE URLS
    # ==========================================================================
    path("warehouses/", views.WarehouseListView.as_view(), name="warehouse_list"),
    path("warehouses/create/", views.WarehouseCreateView.as_view(), name="warehouse_create"),
    path("warehouses/<int:pk>/", views.WarehouseDetailView.as_view(), name="warehouse_detail"),
    path("warehouses/<int:pk>/edit/", views.WarehouseUpdateView.as_view(), name="warehouse_update"),
    # ==========================================================================
    # SALES ORDER URLS
    # ==========================================================================
    path("orders/", views.SalesOrderListView.as_view(), name="salesorder_list"),
    path("orders/create/", views.SalesOrderCreateView.as_view(), name="salesorder_create"),
    path("orders/<int:pk>/", views.SalesOrderDetailView.as_view(), name="salesorder_detail"),
    path("orders/<int:pk>/edit/", views.SalesOrderUpdateView.as_view(), name="salesorder_update"),
    path("orders/<int:pk>/delete/", views.SalesOrderDeleteView.as_view(), name="salesorder_delete"),
    # ==========================================================================
    # SERVICE SITE URLS
    # ==========================================================================
    path("sites/", views.ServiceSiteListView.as_view(), name="servicesite_list"),
    path("sites/create/", views.ServiceSiteCreateView.as_view(), name="servicesite_create"),
    path("sites/<int:pk>/", views.ServiceSiteDetailView.as_view(), name="servicesite_detail"),
    path("sites/<int:pk>/edit/", views.ServiceSiteUpdateView.as_view(), name="servicesite_update"),
    path("sites/<int:pk>/delete/", views.ServiceSiteDeleteView.as_view(), name="servicesite_delete"),
    # ==========================================================================
    # FIELD TECHNICIAN URLS
    # ==========================================================================
    path("technicians/", views.FieldTechnicianListView.as_view(), name="fieldtechnician_list"),
    path("technicians/create/", views.FieldTechnicianCreateView.as_view(), name="fieldtechnician_create"),
    path("technicians/<int:pk>/", views.FieldTechnicianDetailView.as_view(), name="fieldtechnician_detail"),
    path("technicians/<int:pk>/edit/", views.FieldTechnicianUpdateView.as_view(), name="fieldtechnician_update"),
    path("technicians/<int:pk>/delete/", views.FieldTechnicianDeleteView.as_view(), name="fieldtechnician_delete"),
    # ==========================================================================
    # FIELD SERVICE REQUEST URLS
    # ==========================================================================
    path("service-requests/", views.FieldServiceRequestListView.as_view(), name="fieldservicerequest_list"),
    path("service-requests/create/", views.FieldServiceRequestCreateView.as_view(), name="fieldservicerequest_create"),
    path("service-requests/<int:pk>/", views.FieldServiceRequestDetailView.as_view(), name="fieldservicerequest_detail"),
    path("service-requests/<int:pk>/edit/", views.FieldServiceRequestUpdateView.as_view(), name="fieldservicerequest_update"),
    path("service-requests/<int:pk>/delete/", views.FieldServiceRequestDeleteView.as_view(), name="fieldservicerequest_delete"),
    # ==========================================================================
    # SERVICE SCHEDULE URLS
    # ==========================================================================
    path("schedules/", views.ServiceScheduleListView.as_view(), name="serviceschedule_list"),
    path("schedules/create/", views.ServiceScheduleCreateView.as_view(), name="serviceschedule_create"),
    path("schedules/<int:pk>/", views.ServiceScheduleDetailView.as_view(), name="serviceschedule_detail"),
    path("schedules/<int:pk>/edit/", views.ServiceScheduleUpdateView.as_view(), name="serviceschedule_update"),
    path("schedules/<int:pk>/delete/", views.ServiceScheduleDeleteView.as_view(), name="serviceschedule_delete"),
    # ==========================================================================
    # SITE VISIT URLS
    # ==========================================================================
    path("visits/", views.SiteVisitListView.as_view(), name="sitevisit_list"),
    path("visits/create/", views.SiteVisitCreateView.as_view(), name="sitevisit_create"),
    path("visits/<int:pk>/", views.SiteVisitDetailView.as_view(), name="sitevisit_detail"),
    path("visits/<int:pk>/edit/", views.SiteVisitUpdateView.as_view(), name="sitevisit_update"),
    path("visits/<int:pk>/delete/", views.SiteVisitDeleteView.as_view(), name="sitevisit_delete"),
    # ==========================================================================
    # SERVICE REPORT URLS
    # ==========================================================================
    path("reports/", views.ServiceReportListView.as_view(), name="servicereport_list"),
    path("reports/create/", views.ServiceReportCreateView.as_view(), name="servicereport_create"),
    path("reports/<int:pk>/", views.ServiceReportDetailView.as_view(), name="servicereport_detail"),
    path("reports/<int:pk>/edit/", views.ServiceReportUpdateView.as_view(), name="servicereport_update"),
    path("reports/<int:pk>/delete/", views.ServiceReportDeleteView.as_view(), name="servicereport_delete"),
    # ==========================================================================
    # FIELD DRILL STRING RUN URLS
    # ==========================================================================
    path("drill-runs/", views.FieldDrillStringRunListView.as_view(), name="fielddrillstringrun_list"),
    path("drill-runs/create/", views.FieldDrillStringRunCreateView.as_view(), name="fielddrillstringrun_create"),
    path("drill-runs/<int:pk>/", views.FieldDrillStringRunDetailView.as_view(), name="fielddrillstringrun_detail"),
    path("drill-runs/<int:pk>/edit/", views.FieldDrillStringRunUpdateView.as_view(), name="fielddrillstringrun_update"),
    path("drill-runs/<int:pk>/delete/", views.FieldDrillStringRunDeleteView.as_view(), name="fielddrillstringrun_delete"),
    # ==========================================================================
    # FIELD RUN DATA URLS
    # ==========================================================================
    path("run-data/", views.FieldRunDataListView.as_view(), name="fieldrundata_list"),
    path("run-data/create/", views.FieldRunDataCreateView.as_view(), name="fieldrundata_create"),
    path("run-data/<int:pk>/", views.FieldRunDataDetailView.as_view(), name="fieldrundata_detail"),
    path("run-data/<int:pk>/edit/", views.FieldRunDataUpdateView.as_view(), name="fieldrundata_update"),
    path("run-data/<int:pk>/delete/", views.FieldRunDataDeleteView.as_view(), name="fieldrundata_delete"),
]
