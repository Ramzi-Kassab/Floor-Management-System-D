"""
ARDT FMS - Django Settings
Version: 5.4

This is the main Django settings file. It uses django-environ for
environment variable management.
"""

import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)

# Read .env file
environ.Env.read_env(BASE_DIR / '.env')

# =============================================================================
# CORE SETTINGS
# =============================================================================

# SECURITY: No default for SECRET_KEY - must be set in environment
SECRET_KEY = env('SECRET_KEY')

DEBUG = env('DEBUG')

ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'django_htmx',
    'widget_tweaks',
    'crispy_forms',
    'crispy_tailwind',
    'django_filters',
    'django_extensions',
]

# P1 Core Apps (22 apps including dashboard)
LOCAL_APPS = [
    # Organization & Auth
    'apps.organization',
    'apps.accounts',

    # Dashboard
    'apps.dashboard',

    # Procedure Engine
    'apps.procedures',
    'apps.forms_engine',
    'apps.execution',

    # Operations
    'apps.drss',
    'apps.sales',
    'apps.workorders',
    'apps.technology',

    # Quality & Inventory
    'apps.quality',
    'apps.inventory',
    'apps.compliance',

    # Support Systems
    'apps.scancodes',
    'apps.notifications',
    'apps.maintenance',
    'apps.documents',

    # Planning (NEW in v5.4)
    'apps.planning',

    # Reports & Analytics (NEW in v5.4)
    'apps.reports',

    # Common utilities
    'apps.common',

    # Future Phases (skeleton only)
    'apps.supplychain',
    'apps.dispatch',
    'apps.hr',
    'apps.hsse',
    'apps.erp_integration',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'ardt_fms.urls'

# =============================================================================
# TEMPLATES
# =============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ardt_fms.wsgi.application'

# =============================================================================
# DATABASE
# =============================================================================

# SECURITY: No default for DATABASE_URL - must be set in environment
DATABASES = {
    'default': env.db('DATABASE_URL')
}

# =============================================================================
# AUTHENTICATION
# =============================================================================

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'accounts:login'

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Riyadh'
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# =============================================================================
# MEDIA FILES
# =============================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# DEFAULT PRIMARY KEY FIELD TYPE
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# CRISPY FORMS
# =============================================================================

CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'

# =============================================================================
# DJANGO DEBUG TOOLBAR (Development Only)
# =============================================================================

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']

# =============================================================================
# LOGGING
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'ardt_fms.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Create logs directory
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# =============================================================================
# ARDT FMS CUSTOM SETTINGS
# =============================================================================

# Company Information
ARDT_COMPANY_NAME = 'ARDT'
ARDT_SYSTEM_NAME = 'Floor Management System'
ARDT_VERSION = '5.4'

# Pagination defaults
ARDT_DEFAULT_PAGE_SIZE = 25
ARDT_MAX_PAGE_SIZE = 100

# File upload limits
ARDT_MAX_UPLOAD_SIZE_MB = 10
ARDT_ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif']
ARDT_ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'application/msword', 
                                'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

# Work Order Settings
ARDT_WO_NUMBER_PREFIX = 'WO'
ARDT_WO_NUMBER_PADDING = 6  # WO-000001

# DRSS Settings
ARDT_DRSS_NUMBER_PREFIX = 'DRSS'
ARDT_DRSS_NUMBER_PADDING = 6

# Planning Settings
ARDT_DEFAULT_SPRINT_DURATION_WEEKS = 2
ARDT_DEFAULT_WIP_LIMIT = 3

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# SSL/HTTPS (Enable in production)
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS (Enable in production)
if not DEBUG:
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Cookie Security
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=not DEBUG)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=not DEBUG)
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Additional Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'
