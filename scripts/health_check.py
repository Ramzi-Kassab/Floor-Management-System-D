#!/usr/bin/env python
"""
System Health Check Script for Floor Management System
Run this periodically or after major changes/migrations.

Usage:
    python scripts/health_check.py

Or via manage.py:
    python manage.py runscript health_check  (requires django-extensions)
"""
import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def run_command(cmd, capture=True):
    """Run a shell command and return output."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=capture,
        text=True
    )
    return result.returncode, result.stdout, result.stderr

def print_header(title):
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}  {title}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

def print_status(check_name, passed, details=""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"  {status}  {check_name}")
    if details and not passed:
        print(f"         {YELLOW}{details}{RESET}")

def check_migrations():
    """Check all migrations are applied."""
    print_header("Migration Status")

    # Check for unapplied migrations
    code, out, err = run_command("python manage.py showmigrations --plan | grep '\\[ \\]'")
    unapplied = out.strip().split('\n') if out.strip() else []
    unapplied = [m for m in unapplied if m]  # Filter empty

    if unapplied:
        print_status("All migrations applied", False, f"{len(unapplied)} unapplied")
        for m in unapplied[:5]:  # Show first 5
            print(f"         - {m.strip()}")
        if len(unapplied) > 5:
            print(f"         ... and {len(unapplied)-5} more")
        return False
    else:
        print_status("All migrations applied", True)
        return True

def check_pending_migrations():
    """Check for model changes that need migrations."""
    print_header("Pending Model Changes")

    code, out, err = run_command("python manage.py makemigrations --check --dry-run 2>&1")

    if code == 0 and "No changes detected" in out:
        print_status("No pending migrations", True)
        return True
    else:
        print_status("No pending migrations", False, "Models have unmigrated changes")
        if out:
            for line in out.strip().split('\n')[:10]:
                print(f"         {line}")
        return False

def check_system():
    """Run Django system check."""
    print_header("Django System Check")

    code, out, err = run_command("python manage.py check 2>&1")

    if code == 0:
        print_status("System check passed", True)
        return True
    else:
        print_status("System check passed", False)
        output = out + err
        for line in output.strip().split('\n')[:10]:
            print(f"         {line}")
        return False

def check_model_locations():
    """Verify key models are in correct apps."""
    print_header("Model Location Verification")

    expected_locations = {
        'BitSize': 'apps/technology/models.py',
        'BitType': 'apps/technology/models.py',
        'Design': 'apps/technology/models.py',
        'InventoryItem': 'apps/inventory/models.py',
        'WorkOrder': 'apps/workorders/models.py',
        'DrillBit': 'apps/workorders/models.py',
    }

    all_passed = True
    for model, expected_file in expected_locations.items():
        code, out, err = run_command(f"grep -rn '^class {model}' apps/*/models.py")

        if out.strip():
            actual_file = out.strip().split(':')[0]
            if actual_file == expected_file:
                print_status(f"{model} in {expected_file}", True)
            else:
                print_status(f"{model} in {expected_file}", False, f"Found in {actual_file}")
                all_passed = False
        else:
            print_status(f"{model} exists", False, "Model not found")
            all_passed = False

    return all_passed

def check_migration_conflicts():
    """Check for migration conflicts (multiple leaf nodes)."""
    print_header("Migration Conflict Check")

    code, out, err = run_command("python manage.py showmigrations 2>&1")

    if "Conflicting migrations" in (out + err):
        print_status("No migration conflicts", False, "Conflicting migrations detected")
        return False
    else:
        print_status("No migration conflicts", True)
        return True

def check_urls():
    """Verify URL configuration."""
    print_header("URL Configuration")

    code, out, err = run_command("python manage.py show_urls 2>&1 | head -5")

    # show_urls requires django-extensions, fallback to basic check
    if code != 0:
        code, out, err = run_command("python -c \"from ardt_fms.urls import urlpatterns; print(f'{len(urlpatterns)} URL patterns loaded')\"")

    if code == 0:
        print_status("URL configuration valid", True)
        return True
    else:
        print_status("URL configuration valid", False, out + err)
        return False

def check_database():
    """Quick database connectivity check."""
    print_header("Database Connection")

    code, out, err = run_command("python manage.py dbshell -- -c 'SELECT 1;' 2>&1")

    # For SQLite, just check if we can query
    code2, out2, err2 = run_command("python -c \"import django; django.setup(); from django.db import connection; connection.ensure_connection(); print('Connected')\" 2>&1")

    if "Connected" in out2:
        print_status("Database connection", True)
        return True
    else:
        print_status("Database connection", False, out2 + err2)
        return False

def count_apps():
    """Count and list Django apps."""
    print_header("Application Summary")

    code, out, err = run_command("ls -d apps/*/ | wc -l")
    app_count = out.strip()

    code, apps_out, err = run_command("ls -d apps/*/")
    apps = [a.replace('apps/', '').replace('/', '') for a in apps_out.strip().split('\n')]

    print(f"  Total apps: {BOLD}{app_count}{RESET}")
    print(f"  Apps: {', '.join(apps[:10])}")
    if len(apps) > 10:
        print(f"        ... and {len(apps)-10} more")

    return True

def main():
    print(f"\n{BOLD}{'#'*60}{RESET}")
    print(f"{BOLD}#  Floor Management System - Health Check{RESET}")
    print(f"{BOLD}{'#'*60}{RESET}")

    results = []

    results.append(("Database", check_database()))
    results.append(("Migrations Applied", check_migrations()))
    results.append(("Pending Changes", check_pending_migrations()))
    results.append(("System Check", check_system()))
    results.append(("Model Locations", check_model_locations()))
    results.append(("Migration Conflicts", check_migration_conflicts()))
    results.append(("URL Config", check_urls()))
    count_apps()

    # Summary
    print_header("Summary")
    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
        print(f"  {status} {name}")

    print()
    if passed == total:
        print(f"  {GREEN}{BOLD}All {total} checks passed!{RESET}")
    else:
        print(f"  {YELLOW}{passed}/{total} checks passed{RESET}")
        print(f"  {RED}{total-passed} issue(s) need attention{RESET}")

    print()
    return 0 if passed == total else 1

if __name__ == '__main__':
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ardt_fms.settings')
    import django
    django.setup()

    sys.exit(main())
