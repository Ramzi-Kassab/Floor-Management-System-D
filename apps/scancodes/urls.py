"""
ARDT FMS - Scan Codes URLs
Version: 5.4

URL patterns for scan code management.
"""

from django.urls import path
from . import views

app_name = "scancodes"

urlpatterns = [
    # Scan Code Management
    path('', views.ScanCodeListView.as_view(), name='scancode-list'),
    path('<int:pk>/', views.ScanCodeDetailView.as_view(), name='scancode-detail'),
    path('register/', views.ScanCodeCreateView.as_view(), name='scancode-create'),
    path('<int:pk>/edit/', views.ScanCodeUpdateView.as_view(), name='scancode-update'),
    path('<int:pk>/delete/', views.ScanCodeDeleteView.as_view(), name='scancode-delete'),

    # Scan Logs
    path('logs/', views.ScanLogListView.as_view(), name='scanlog-list'),
    path('logs/<int:pk>/', views.ScanLogDetailView.as_view(), name='scanlog-detail'),

    # Scanner Interface
    path('scanner/', views.ScannerView.as_view(), name='scanner'),
    path('verify/', views.VerifyScanView.as_view(), name='verify-scan'),
    path('generate/', views.GenerateCodeView.as_view(), name='generate-code'),
]
