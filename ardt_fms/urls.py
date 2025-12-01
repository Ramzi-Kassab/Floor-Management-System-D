"""
ARDT FMS - URL Configuration
Version: 5.4
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Dashboard (home)
    path('', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    
    # Authentication & User Management
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    
    # Organization
    path('organization/', include('apps.organization.urls', namespace='organization')),
    
    # Operations
    path('drss/', include('apps.drss.urls', namespace='drss')),
    path('sales/', include('apps.sales.urls', namespace='sales')),
    path('work-orders/', include('apps.workorders.urls', namespace='workorders')),
    
    # Technology / Engineering
    path('technology/', include('apps.technology.urls', namespace='technology')),
    
    # Procedure Engine
    path('procedures/', include('apps.procedures.urls', namespace='procedures')),
    path('forms/', include('apps.forms_engine.urls', namespace='forms_engine')),
    path('execution/', include('apps.execution.urls', namespace='execution')),
    
    # Quality
    path('quality/', include('apps.quality.urls', namespace='quality')),
    
    # Inventory
    path('inventory/', include('apps.inventory.urls', namespace='inventory')),
    
    # Support Systems
    path('scan/', include('apps.scancodes.urls', namespace='scancodes')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('maintenance/', include('apps.maintenance.urls', namespace='maintenance')),
    path('documents/', include('apps.documents.urls', namespace='documents')),
    
    # Planning Module (NEW in v5.4)
    path('planning/', include('apps.planning.urls', namespace='planning')),
    
    # Future Phase Apps (P2+)
    path('supply-chain/', include('apps.supplychain.urls', namespace='supplychain')),
    path('dispatch/', include('apps.dispatch.urls', namespace='dispatch')),
    path('hr/', include('apps.hr.urls', namespace='hr')),
    path('hsse/', include('apps.hsse.urls', namespace='hsse')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

# Custom error handlers
handler400 = 'ardt_fms.views.bad_request'
handler403 = 'ardt_fms.views.permission_denied'
handler404 = 'ardt_fms.views.page_not_found'
handler500 = 'ardt_fms.views.server_error'
