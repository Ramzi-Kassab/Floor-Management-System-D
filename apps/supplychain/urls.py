"""
ARDT FMS - Supply Chain URLs
Version: 5.4
"""

from django.urls import path

from . import views

app_name = "supplychain"

urlpatterns = [
    # Suppliers
    path("suppliers/", views.SupplierListView.as_view(), name="supplier_list"),
    path("suppliers/create/", views.SupplierCreateView.as_view(), name="supplier_create"),
    path("suppliers/<int:pk>/", views.SupplierDetailView.as_view(), name="supplier_detail"),
    path("suppliers/<int:pk>/edit/", views.SupplierUpdateView.as_view(), name="supplier_update"),
    # Purchase Requisitions
    path("requisitions/", views.PRListView.as_view(), name="pr_list"),
    path("requisitions/create/", views.PRCreateView.as_view(), name="pr_create"),
    path("requisitions/<int:pk>/", views.PRDetailView.as_view(), name="pr_detail"),
    path("requisitions/<int:pk>/approve/", views.PRApproveView.as_view(), name="pr_approve"),
    path("requisitions/<int:pk>/add-line/", views.PRAddLineView.as_view(), name="pr_add_line"),
    # Purchase Orders
    path("orders/", views.POListView.as_view(), name="po_list"),
    path("orders/create/", views.POCreateView.as_view(), name="po_create"),
    path("orders/<int:pk>/", views.PODetailView.as_view(), name="po_detail"),
    path("orders/<int:pk>/edit/", views.POUpdateView.as_view(), name="po_update"),
    path("orders/<int:pk>/add-line/", views.POAddLineView.as_view(), name="po_add_line"),
    path("orders/<int:pk>/pdf/", views.POPDFView.as_view(), name="po_pdf"),
    path("orders/<int:pk>/email/", views.POEmailView.as_view(), name="po_email"),
    # Goods Receipts
    path("receipts/", views.GRNListView.as_view(), name="grn_list"),
    path("receipts/create/", views.GRNCreateView.as_view(), name="grn_create"),
    path("receipts/<int:pk>/", views.GRNDetailView.as_view(), name="grn_detail"),
    path("receipts/<int:pk>/add-line/", views.GRNAddLineView.as_view(), name="grn_add_line"),
    # CAPAs
    path("capa/", views.CAPAListView.as_view(), name="capa_list"),
    path("capa/create/", views.CAPACreateView.as_view(), name="capa_create"),
    path("capa/<int:pk>/", views.CAPADetailView.as_view(), name="capa_detail"),
    path("capa/<int:pk>/edit/", views.CAPAUpdateView.as_view(), name="capa_update"),
]
