"""
WSGI config for ARDT FMS project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ardt_fms.settings')

application = get_wsgi_application()
