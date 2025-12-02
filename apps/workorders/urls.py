"""
ARDT FMS - Work Orders URLs
Version: 5.4 - Sprint 1
"""

from django.urls import path
from . import views

app_name = 'workorders'

urlpatterns = [
    # List and CRUD
    path('', views.WorkOrderListView.as_view(), name='list'),
    path('create/', views.WorkOrderCreateView.as_view(), name='create'),
    path('<int:pk>/', views.WorkOrderDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.WorkOrderUpdateView.as_view(), name='update'),

    # Actions
    path('<int:pk>/start/', views.start_work_view, name='start'),
    path('<int:pk>/complete/', views.complete_work_view, name='complete'),
]
