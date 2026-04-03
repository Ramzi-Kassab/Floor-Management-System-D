"""
Compliance App - Pytest Configuration and Shared Fixtures
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def base_user(db):
    """Base user fixture for all tests."""
    return User.objects.create_user(
        username='base_user',
        email='base@example.com',
        password='basepass123',
        first_name='Base',
        last_name='User'
    )


@pytest.fixture
def staff_user(db):
    """Staff user fixture."""
    return User.objects.create_user(
        username='staff_user',
        email='staff@example.com',
        password='staffpass123',
        is_staff=True
    )


@pytest.fixture
def admin_user(db):
    """Admin/superuser fixture."""
    return User.objects.create_superuser(
        username='admin_user',
        email='admin@example.com',
        password='adminpass123'
    )


# Django settings for pytest
def pytest_configure():
    """Configure Django settings for tests."""
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
                'apps.compliance',
            ],
        )
