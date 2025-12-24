#!/usr/bin/env python
"""
System Health Check Script for Floor Management System
Run this periodically or after major changes/migrations.

Usage:
    python scripts/health_check.py
    ./hc  (short alias)
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
CYAN = '\033[96m'
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

def run_interactive(cmd):
    """Run command with live output."""
    return subprocess.run(cmd, shell=True).returncode

def ask_yes_no(question, default='y'):
    """Ask a yes/no question and return True for yes."""
    suffix = "[Y/n]" if default.lower() == 'y' else "[y/N]"
    try:
        answer = input(f"  {CYAN}?{RESET} {question} {suffix}: ").strip().lower()
        if not answer:
            answer = default.lower()
        return answer in ('y', 'yes')
    except (EOFError, KeyboardInterrupt):
        print()
        return False

def print_header(title):
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}  {title}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

def print_status(check_name, passed, details=""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"  {status}  {check_name}")
    if details and not passed:
        print(f"         {YELLOW}{details}{RESET}")

def git_pull():
    """Pull latest changes from remote."""
    print_header("Git Pull")

    # Check if we're in a git repo
    code, out, err = run_command("git rev-parse --is-inside-work-tree 2>&1")
    if code != 0:
        print(f"  {YELLOW}Not a git repository, skipping pull{RESET}")
        return True

    # Get current branch
    code, branch, err = run_command("git rev-parse --abbrev-ref HEAD")
    branch = branch.strip()

    # Check for uncommitted changes
    code, status, err = run_command("git status --porcelain")
    if status.strip():
        print(f"  {YELLOW}⚠ Uncommitted changes detected{RESET}")
        if ask_yes_no("Stash changes before pulling?", 'n'):
            run_command("git stash")
            print(f"  {GREEN}✓{RESET} Changes stashed")

    # Pull
    print(f"  Pulling from origin/{branch}...")
    code = run_interactive(f"git pull origin {branch}")

    if code == 0:
        print(f"  {GREEN}✓{RESET} Pull successful")
        return True
    else:
        print(f"  {RED}✗{RESET} Pull failed")
        return False

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

        # Offer to run migrations
        print()
        if ask_yes_no("Apply pending migrations now?"):
            print()
            code = run_interactive("python manage.py migrate")
            if code == 0:
                print(f"\n  {GREEN}✓ Migrations applied successfully{RESET}")
                return True
            else:
                print(f"\n  {RED}✗ Migration failed{RESET}")
                return False
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

        # Offer to create migrations
        print()
        if ask_yes_no("Create new migrations now?"):
            print()
            code = run_interactive("python manage.py makemigrations")
            if code == 0:
                print(f"\n  {GREEN}✓ Migrations created{RESET}")
                # Offer to apply them
                if ask_yes_no("Apply the new migrations now?"):
                    run_interactive("python manage.py migrate")
                return True
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


def check_seed_data():
    """Check if seed data needs to be applied."""
    import csv
    print_header("Seed Data Status")

    # ==========================================================================
    # SEED DATA DEFINITIONS
    # Each entry defines: name, model path, expected minimum, seed command
    # For CSV-based seeds, include csv_path and code_column
    # ==========================================================================

    # CSV-based seeds (compare against CSV file)
    csv_seed_checks = [
        {
            'name': 'Units of Measure',
            'csv_path': 'docs/development/units_comprehensive.csv',
            'code_column': 'Unit Code',
            'count_cmd': "from apps.inventory.models import UnitOfMeasure; print(UnitOfMeasure.objects.count())",
            'seed_cmd': 'python manage.py seed_units',
        },
        {
            'name': 'Attributes',
            'csv_path': 'docs/development/attributes_comprehensive.csv',
            'code_column': 'Attribute Code',
            'count_cmd': "from apps.inventory.models import Attribute; print(Attribute.objects.count())",
            'seed_cmd': 'python manage.py seed_attributes',
        },
    ]

    # Model-based seeds (check model has minimum expected records)
    # Format: (name, model_import, expected_min, seed_command, category)
    model_seed_checks = [
        # Organization/Core seeds
        ('Departments', 'from apps.organization.models import Department; print(Department.objects.count())', 10, 'seed_departments', 'Organization'),
        ('Positions', 'from apps.organization.models import Position; print(Position.objects.count())', 50, 'seed_positions', 'Organization'),

        # Sales seeds
        ('Customers', 'from apps.sales.models import Customer; print(Customer.objects.count())', 5, 'seed_customers', 'Sales'),
        ('Rigs', 'from apps.sales.models import Rig; print(Rig.objects.count())', 5, 'seed_rigs', 'Sales'),
        ('Wells', 'from apps.sales.models import Well; print(Well.objects.count())', 20, 'seed_wells', 'Sales'),

        # Inventory master data seeds
        ('Condition Types', 'from apps.inventory.models import ConditionType; print(ConditionType.objects.count())', 8, 'seed_condition_types', 'Inventory'),
        ('Quality Statuses', 'from apps.inventory.models import QualityStatus; print(QualityStatus.objects.count())', 7, 'seed_quality_statuses', 'Inventory'),
        ('Location Types', 'from apps.inventory.models import LocationType; print(LocationType.objects.count())', 10, 'seed_location_types', 'Inventory'),
        ('Ownership Types', 'from apps.inventory.models import OwnershipType; print(OwnershipType.objects.count())', 3, 'seed_ownership_types', 'Inventory'),
        ('Adjustment Reasons', 'from apps.inventory.models import AdjustmentReason; print(AdjustmentReason.objects.count())', 5, 'seed_adjustment_reasons', 'Inventory'),
        ('Parties', 'from apps.inventory.models import Party; print(Party.objects.count())', 1, 'seed_parties', 'Inventory'),

        # Technology seeds
        ('Applications', 'from apps.technology.models import Application; print(Application.objects.count())', 15, 'seed_applications', 'Technology'),
        ('Connection Types', 'from apps.technology.models import ConnectionType; print(ConnectionType.objects.count())', 5, 'seed_connection_types', 'Technology'),
        ('Connection Sizes', 'from apps.technology.models import ConnectionSize; print(ConnectionSize.objects.count())', 5, 'seed_connection_sizes', 'Technology'),
        ('Formation Types', 'from apps.technology.models import FormationType; print(FormationType.objects.count())', 5, 'seed_formation_types', 'Technology'),
        ('IADC Codes', 'from apps.technology.models import IADCCode; print(IADCCode.objects.count())', 10, 'seed_iadc_codes', 'Technology'),
        ('Pocket Shapes', 'from apps.technology.models import PocketShape; print(PocketShape.objects.count())', 3, 'seed_pocket_shapes', 'Technology'),
        ('Pocket Sizes', 'from apps.technology.models import PocketSize; print(PocketSize.objects.count())', 5, 'seed_pocket_sizes', 'Technology'),
        ('Upper Section Types', 'from apps.technology.models import UpperSectionType; print(UpperSectionType.objects.count())', 3, 'seed_upper_section_types', 'Technology'),
        ('Special Technologies', 'from apps.technology.models import SpecialTechnology; print(SpecialTechnology.objects.count())', 3, 'seed_special_technologies', 'Technology'),
        ('Breaker Slots', 'from apps.technology.models import BreakerSlot; print(BreakerSlot.objects.count())', 3, 'seed_breaker_slots', 'Technology'),

        # Bit technology seeds (in technology app, managed by workorders commands)
        ('Bit Sizes', 'from apps.technology.models import BitSize; print(BitSize.objects.count())', 10, 'seed_bit_sizes', 'Technology'),
        ('Bit Types', 'from apps.technology.models import BitType; print(BitType.objects.count())', 5, 'seed_bit_types', 'Technology'),

        # Procurement/Supply Chain seeds (test data for PR→PO→GRN workflow)
        ('Vendors', 'from apps.supplychain.models import Vendor; print(Vendor.objects.count())', 1, 'seed_procurement_workflow', 'Procurement'),
        ('Purchase Requisitions', 'from apps.supplychain.models import PurchaseRequisition; print(PurchaseRequisition.objects.count())', 1, 'seed_procurement_workflow', 'Procurement'),
        ('Purchase Orders', 'from apps.supplychain.models import PurchaseOrder; print(PurchaseOrder.objects.count())', 1, 'seed_procurement_workflow', 'Procurement'),
        ('GRNs', 'from apps.inventory.models import GoodsReceiptNote; print(GoodsReceiptNote.objects.count())', 1, 'seed_procurement_workflow', 'Procurement'),
    ]

    all_passed = True
    seeds_to_run = []
    current_category = None

    # ==========================================================================
    # Check CSV-based seeds
    # ==========================================================================
    print(f"  {CYAN}── CSV-Based Seeds ──{RESET}")

    for seed in csv_seed_checks:
        csv_path = PROJECT_ROOT / seed['csv_path']

        # Check if CSV exists
        if not csv_path.exists():
            print(f"  {YELLOW}⚠{RESET} {seed['name']}: CSV not found, skipping")
            continue

        # Count unique codes in CSV (handles duplicates correctly)
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                codes = set()
                for row in reader:
                    code = row.get(seed['code_column'], '').strip()
                    if code:
                        codes.add(code)
                csv_count = len(codes)
        except Exception as e:
            print(f"  {RED}✗{RESET} {seed['name']}: Error reading CSV - {e}")
            all_passed = False
            continue

        # Get current database count
        code, out, err = run_command(f'python -c "import django; django.setup(); {seed["count_cmd"]}"')
        try:
            db_count = int(out.strip())
        except ValueError:
            print(f"  {RED}✗{RESET} {seed['name']}: Error getting DB count")
            all_passed = False
            continue

        # Compare counts
        if db_count >= csv_count:
            print(f"  {GREEN}✓{RESET} {seed['name']}: {db_count} records (CSV: {csv_count})")
        else:
            missing = csv_count - db_count
            print(f"  {YELLOW}⚠{RESET} {seed['name']}: {db_count}/{csv_count} ({missing} missing)")
            seeds_to_run.append({'name': seed['name'], 'seed_cmd': seed['seed_cmd']})
            all_passed = False

    # ==========================================================================
    # Check model-based seeds
    # ==========================================================================
    print(f"\n  {CYAN}── Model-Based Seeds ──{RESET}")

    for name, count_cmd, expected_min, seed_cmd, category in model_seed_checks:
        # Print category header if changed
        if category != current_category:
            current_category = category
            print(f"  {BOLD}{category}:{RESET}")

        # Get current database count
        code, out, err = run_command(f'python -c "import django; django.setup(); {count_cmd}" 2>&1')

        try:
            db_count = int(out.strip())
        except ValueError:
            # Model might not exist or import error
            if "ModuleNotFoundError" in (out + err) or "ImportError" in (out + err):
                print(f"    {YELLOW}○{RESET} {name}: Model not found (skip)")
            else:
                print(f"    {YELLOW}○{RESET} {name}: Unable to check")
            continue

        # Compare counts
        if db_count >= expected_min:
            print(f"    {GREEN}✓{RESET} {name}: {db_count} records (min: {expected_min})")
        elif db_count == 0:
            print(f"    {RED}✗{RESET} {name}: Empty (needs {expected_min}+)")
            seeds_to_run.append({'name': name, 'seed_cmd': f'python manage.py {seed_cmd}'})
            all_passed = False
        else:
            print(f"    {YELLOW}⚠{RESET} {name}: {db_count} records (expected {expected_min}+)")
            seeds_to_run.append({'name': name, 'seed_cmd': f'python manage.py {seed_cmd}'})
            all_passed = False

    # ==========================================================================
    # Offer to run missing seeds
    # ==========================================================================
    if seeds_to_run:
        print()
        if ask_yes_no(f"Apply {len(seeds_to_run)} pending seed(s) now?"):
            print()
            for seed in seeds_to_run:
                cmd = seed['seed_cmd'] if seed['seed_cmd'].startswith('python') else f"python manage.py {seed['seed_cmd']}"
                print(f"  Running: {cmd}")
                code = run_interactive(cmd)
                if code == 0:
                    print(f"  {GREEN}✓{RESET} {seed['name']} seeded successfully\n")
                else:
                    print(f"  {RED}✗{RESET} {seed['name']} seed failed\n")
            return True  # Consider passed after running
        return False

    return all_passed

def offer_run_server():
    """Offer to run the development server."""
    print()
    if ask_yes_no("Start the development server?", 'n'):
        print(f"\n  {CYAN}Starting server on http://127.0.0.1:8000/{RESET}")
        print(f"  {YELLOW}Press Ctrl+C to stop{RESET}\n")
        try:
            run_interactive("python manage.py runserver")
        except KeyboardInterrupt:
            print(f"\n  {YELLOW}Server stopped{RESET}")

def main():
    print(f"\n{BOLD}{'#'*60}{RESET}")
    print(f"{BOLD}#  Floor Management System - Health Check{RESET}")
    print(f"{BOLD}{'#'*60}{RESET}")

    results = []

    # Git pull first
    git_pull()

    results.append(("Database", check_database()))
    results.append(("Migrations Applied", check_migrations()))
    results.append(("Pending Changes", check_pending_migrations()))
    results.append(("Seed Data", check_seed_data()))
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

    # Offer to run server
    offer_run_server()

    print()
    return 0 if passed == total else 1

if __name__ == '__main__':
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ardt_fms.settings')
    import django
    django.setup()

    sys.exit(main())
