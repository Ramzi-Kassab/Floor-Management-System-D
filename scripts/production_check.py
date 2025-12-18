#!/usr/bin/env python
"""
ARDT FMS - Production Readiness Check
Phase 6: Deployment Preparation

Validates the system is ready for production deployment.

Usage:
    python scripts/production_check.py
"""

import os
import sys
from pathlib import Path

# Add project to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ardt_fms.settings")


def check_environment():
    """Check environment configuration."""
    print("\n[1/7] Checking Environment Configuration...")

    issues = []

    # Check DEBUG setting
    debug = os.environ.get("DEBUG", "True")
    if debug.lower() == "true":
        issues.append("WARNING: DEBUG=True (should be False in production)")
    else:
        print("  DEBUG is disabled")

    # Check SECRET_KEY
    secret_key = os.environ.get("SECRET_KEY", "")
    if "change-in-production" in secret_key or len(secret_key) < 40:
        issues.append("WARNING: SECRET_KEY appears to be default or too short")
    else:
        print("  SECRET_KEY is properly set")

    # Check ALLOWED_HOSTS
    allowed_hosts = os.environ.get("ALLOWED_HOSTS", "")
    if not allowed_hosts or allowed_hosts == "localhost,127.0.0.1":
        issues.append("WARNING: ALLOWED_HOSTS may need production domains")
    else:
        print("  ALLOWED_HOSTS configured")

    return issues


def check_database():
    """Check database configuration."""
    print("\n[2/7] Checking Database Configuration...")

    issues = []

    try:
        import django
        django.setup()

        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("  Database connection successful")

        # Check for pending migrations
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command("showmigrations", "--list", stdout=out)
        output = out.getvalue()
        if "[ ]" in output:
            issues.append("WARNING: Pending migrations found")
        else:
            print("  All migrations applied")

    except Exception as e:
        issues.append(f"ERROR: Database check failed: {e}")

    return issues


def check_static_files():
    """Check static files configuration."""
    print("\n[3/7] Checking Static Files...")

    issues = []

    try:
        import django
        django.setup()

        from django.conf import settings

        static_root = getattr(settings, "STATIC_ROOT", None)
        if not static_root:
            issues.append("WARNING: STATIC_ROOT not configured")
        else:
            if Path(static_root).exists():
                file_count = sum(1 for _ in Path(static_root).rglob("*") if _.is_file())
                print(f"  STATIC_ROOT exists with {file_count} files")
            else:
                issues.append("WARNING: STATIC_ROOT directory does not exist (run collectstatic)")

    except Exception as e:
        issues.append(f"ERROR: Static files check failed: {e}")

    return issues


def check_security():
    """Check security settings."""
    print("\n[4/7] Checking Security Settings...")

    issues = []

    try:
        import django
        django.setup()

        from django.conf import settings

        security_settings = [
            ("SECURE_SSL_REDIRECT", True),
            ("SESSION_COOKIE_SECURE", True),
            ("CSRF_COOKIE_SECURE", True),
            ("SECURE_BROWSER_XSS_FILTER", True),
            ("SECURE_CONTENT_TYPE_NOSNIFF", True),
        ]

        for setting, expected in security_settings:
            value = getattr(settings, setting, False)
            if value != expected:
                issues.append(f"WARNING: {setting} is {value} (should be {expected} in production)")
            else:
                print(f"  {setting}: OK")

    except Exception as e:
        issues.append(f"ERROR: Security check failed: {e}")

    return issues


def check_apps():
    """Check installed apps."""
    print("\n[5/7] Checking Installed Apps...")

    issues = []

    try:
        import django
        django.setup()

        from django.apps import apps

        app_count = len(apps.get_app_configs())
        print(f"  {app_count} apps installed")

        # Check for debug toolbar in production
        if "debug_toolbar" in [a.name for a in apps.get_app_configs()]:
            debug = os.environ.get("DEBUG", "True")
            if debug.lower() != "true":
                issues.append("WARNING: debug_toolbar is installed but DEBUG is False")

    except Exception as e:
        issues.append(f"ERROR: Apps check failed: {e}")

    return issues


def check_models():
    """Check models are properly registered."""
    print("\n[6/7] Checking Models...")

    issues = []

    try:
        import django
        django.setup()

        from django.apps import apps

        model_count = len(apps.get_models())
        print(f"  {model_count} models registered")

        # Check admin registration
        from django.contrib import admin
        registered = len(admin.site._registry)
        print(f"  {registered} models in admin")

    except Exception as e:
        issues.append(f"ERROR: Model check failed: {e}")

    return issues


def check_files():
    """Check required files exist."""
    print("\n[7/7] Checking Required Files...")

    issues = []

    required_files = [
        "manage.py",
        "requirements.txt",
        "ardt_fms/settings.py",
        "ardt_fms/urls.py",
        "ardt_fms/wsgi.py",
    ]

    for file_path in required_files:
        full_path = BASE_DIR / file_path
        if full_path.exists():
            print(f"  {file_path}: OK")
        else:
            issues.append(f"ERROR: Required file missing: {file_path}")

    # Check deployment files
    deployment_files = [
        ("Dockerfile", "Docker deployment"),
        ("docker-compose.yml", "Docker Compose"),
        (".env.example", "Environment template"),
    ]

    for file_path, description in deployment_files:
        full_path = BASE_DIR / file_path
        if full_path.exists():
            print(f"  {file_path}: OK ({description})")
        else:
            issues.append(f"WARNING: {file_path} not found ({description})")

    return issues


def main():
    """Run all production checks."""
    print("=" * 60)
    print("ARDT FMS - Production Readiness Check")
    print("=" * 60)

    all_issues = []

    all_issues.extend(check_environment())
    all_issues.extend(check_database())
    all_issues.extend(check_static_files())
    all_issues.extend(check_security())
    all_issues.extend(check_apps())
    all_issues.extend(check_models())
    all_issues.extend(check_files())

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    warnings = [i for i in all_issues if i.startswith("WARNING")]
    errors = [i for i in all_issues if i.startswith("ERROR")]

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")

    if not all_issues:
        print("\nAll checks passed! System is ready for production.")
        return 0
    elif errors:
        print(f"\nSystem has {len(errors)} error(s) that must be fixed before deployment.")
        return 1
    else:
        print(f"\nSystem has {len(warnings)} warning(s) to review before deployment.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
