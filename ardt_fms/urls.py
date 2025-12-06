"""
ARDT FMS - URL Configuration
Version: 5.4
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connection


def health_check(request):
    """Health check endpoint for container orchestration."""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    status = {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "5.4.0",
    }

    status_code = 200 if status["status"] == "healthy" else 503
    return JsonResponse(status, status=status_code)


urlpatterns = [
    # Health check (for container orchestration)
    path('health/', health_check, name='health_check'),

    # Admin
    path('admin/', admin.site.urls),
    
    # Dashboard (home)
    path('', include('apps.dashboard.urls', namespace='dashboard')),
    
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
    # INCOMPLETE: forms_engine has models but no views/templates - see docs/SKELETON_APPS_ROOT_CAUSE_ANALYSIS.md
    # path('forms/', include('apps.forms_engine.urls', namespace='forms_engine')),
    path('execution/', include('apps.execution.urls', namespace='execution')),
    
    # Quality
    path('quality/', include('apps.quality.urls', namespace='quality')),
    
    # Inventory
    path('inventory/', include('apps.inventory.urls', namespace='inventory')),
    
    # Support Systems
    # INCOMPLETE: scancodes has partial implementation - see docs/SKELETON_APPS_ROOT_CAUSE_ANALYSIS.md
    # path('scan/', include('apps.scancodes.urls', namespace='scancodes')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('maintenance/', include('apps.maintenance.urls', namespace='maintenance')),
    path('documents/', include('apps.documents.urls', namespace='documents')),
    
    # Planning Module (NEW in v5.4)
    path('planning/', include('apps.planning.urls', namespace='planning')),

    # Reports & Analytics (NEW in v5.4)
    path('reports/', include('apps.reports.urls', namespace='reports')),

    # Supply Chain (Complete)
    path('supply-chain/', include('apps.supplychain.urls', namespace='supplychain')),

    # ==========================================
    # INCOMPLETE APPS - Removed Until Sprint 9
    # ==========================================
    # These apps have models but no views/templates.
    # Accessible via Django admin only.
    # Will be completed in Sprint 9 post-launch.
    #
    # Sprint 8 (Incomplete - Models Only):
    # path('hr/', include('apps.hr.urls', namespace='hr')),
    # path('dispatch/', include('apps.dispatch.urls', namespace='dispatch')),
    # path('hsse/', include('apps.hsse.urls', namespace='hsse')),
    #
    # See: docs/SKELETON_APPS_ROOT_CAUSE_ANALYSIS.md for details
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
