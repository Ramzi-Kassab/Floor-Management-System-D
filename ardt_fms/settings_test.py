"""
ARDT FMS - Test Settings

Uses SQLite for testing when PostgreSQL is not available.
"""

from .settings import *  # noqa: F401, F403

# Override database to use SQLite for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_test.sqlite3',
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable debug for tests
DEBUG = False

# Faster tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
