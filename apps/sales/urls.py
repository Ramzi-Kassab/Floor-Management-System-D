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
]
