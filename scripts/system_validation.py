#!/usr/bin/env python
"""
Comprehensive System Validation Script
ARDT Floor Management System - Finalization Phase 1

Checks for common issues across all models:
- Django system check
- Migration status
- Import validation
- Model validation (all apps)
- Admin registrations
- Auto-ID generation
"""

import os
import sys

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ardt_fms.settings')

import django
django.setup()

from django.apps import apps
from django.db import models
from django.core.management import call_command
from io import StringIO
import inspect


class SystemValidator:
    """Comprehensive system validation for ARDT FMS"""

    def __init__(self):
        self.issues = []
        self.warnings = []
        self.stats = {
            'total_models': 0,
            'total_fields': 0,
            'missing_help_text': 0,
            'missing_related_name': 0,
            'missing_str': 0,
            'missing_meta': 0,
            'missing_docstring': 0,
        }
        # Apps to validate (all 21+ apps)
        self.apps_to_check = [
            'core', 'accounts', 'dashboards', 'workorders', 'drillbits',
            'sales', 'drss', 'documents', 'warehouses',
            'quality', 'technology', 'procedures', 'notifications',
            'inventory', 'maintenance', 'planning', 'supplychain',
            'fieldservice', 'fieldoperations', 'fielddatacapture',
            'compliance', 'hr'
        ]

    def validate_all(self):
        """Run all validations"""
        print("=" * 80)
        print("ARDT FMS - COMPREHENSIVE SYSTEM VALIDATION")
        print("=" * 80)
        print()

        self.check_django_system()
        self.check_migrations()
        self.check_imports()
        self.validate_models()
        self.check_admin_registrations()
        self.check_auto_ids()

        self.print_report()

        return len(self.issues) == 0

    def check_django_system(self):
        """Run Django's system check"""
        print("1. Running Django System Check...")

        out = StringIO()
        err = StringIO()
        try:
            call_command('check', stdout=out, stderr=err)
            output = out.getvalue()
            if 'System check identified no issues' in output or not output.strip():
                print("   [OK] Django system check passed")
            else:
                print(f"   [WARN] {output}")
        except Exception as e:
            self.issues.append(f"Django system check failed: {e}")
            print(f"   [FAIL] Django system check failed: {e}")

    def check_migrations(self):
        """Check migration status"""
        print("\n2. Checking Migrations...")

        out = StringIO()
        try:
            call_command('showmigrations', '--plan', stdout=out)
            output = out.getvalue()
            unapplied = [line for line in output.split('\n') if line.strip().startswith('[ ]')]

            if unapplied:
                self.warnings.append(f"{len(unapplied)} unapplied migrations")
                print(f"   [WARN] {len(unapplied)} unapplied migrations")
                for migration in unapplied[:5]:
                    print(f"      - {migration.strip()}")
                if len(unapplied) > 5:
                    print(f"      ... and {len(unapplied) - 5} more")
            else:
                print("   [OK] All migrations applied")
        except Exception as e:
            self.warnings.append(f"Migration check warning: {e}")
            print(f"   [WARN] Could not check migrations: {e}")

    def check_imports(self):
        """Check all app imports work"""
        print("\n3. Checking Imports...")

        successful = 0
        failed = 0

        for app_name in self.apps_to_check:
            try:
                __import__(f'apps.{app_name}.models')
                successful += 1
            except ImportError:
                # App might not exist, which is OK
                pass
            except Exception as e:
                failed += 1
                self.issues.append(f"Import error in apps.{app_name}.models: {e}")
                print(f"   [FAIL] apps.{app_name}.models: {e}")

        print(f"   [OK] {successful} apps imported successfully")
        if failed > 0:
            print(f"   [FAIL] {failed} apps failed to import")

    def validate_models(self):
        """Validate all models"""
        print("\n4. Validating Models...")

        for app_config in apps.get_app_configs():
            if not app_config.name.startswith('apps.'):
                continue

            app_models = app_config.get_models()
            for model in app_models:
                self.stats['total_models'] += 1
                self._validate_model(model)

        print(f"   [OK] Validated {self.stats['total_models']} models")
        print(f"   [INFO] Total fields: {self.stats['total_fields']}")

        if self.stats['missing_str'] > 0:
            print(f"   [WARN] {self.stats['missing_str']} models missing __str__")
        if self.stats['missing_docstring'] > 0:
            print(f"   [WARN] {self.stats['missing_docstring']} models missing docstrings")
        if self.stats['missing_help_text'] > 0:
            print(f"   [INFO] {self.stats['missing_help_text']} fields missing help_text")
        if self.stats['missing_related_name'] > 0:
            print(f"   [WARN] {self.stats['missing_related_name']} ForeignKeys missing related_name")

    def _validate_model(self, model):
        """Validate a single model"""
        model_name = f"{model._meta.app_label}.{model.__name__}"

        # Check __str__ method
        if not hasattr(model, '__str__') or model.__str__ is models.Model.__str__:
            self.stats['missing_str'] += 1
            self.warnings.append(f"{model_name} missing __str__ method")

        # Check docstring
        if not model.__doc__ or model.__doc__.strip() == '':
            self.stats['missing_docstring'] += 1

        # Check fields
        for field in model._meta.get_fields():
            if hasattr(field, 'column'):  # Concrete field
                self.stats['total_fields'] += 1

                # Check help_text
                if hasattr(field, 'help_text') and not field.help_text:
                    self.stats['missing_help_text'] += 1

                # Check related_name for ForeignKey/OneToOneField
                if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                    if not field.remote_field.related_name:
                        self.stats['missing_related_name'] += 1
                        self.warnings.append(f"{model_name}.{field.name} missing related_name")

    def check_admin_registrations(self):
        """Check admin registrations"""
        print("\n5. Checking Admin Registrations...")

        from django.contrib.admin.sites import site

        registered_count = 0
        unregistered = []

        for app_config in apps.get_app_configs():
            if not app_config.name.startswith('apps.'):
                continue

            for model in app_config.get_models():
                if model in site._registry:
                    registered_count += 1
                else:
                    unregistered.append(f"{model._meta.app_label}.{model.__name__}")

        print(f"   [OK] {registered_count} models registered in admin")

        if unregistered:
            print(f"   [WARN] {len(unregistered)} models not registered:")
            for model_name in unregistered[:10]:
                print(f"      - {model_name}")
            if len(unregistered) > 10:
                print(f"      ... and {len(unregistered) - 10} more")

    def check_auto_ids(self):
        """Check auto-ID implementations"""
        print("\n6. Checking Auto-ID Implementations...")

        auto_id_models = []

        for app_config in apps.get_app_configs():
            if not app_config.name.startswith('apps.'):
                continue

            for model in app_config.get_models():
                # Check if model has auto-ID generation method
                if hasattr(model, '_generate_') or any(
                    method.startswith('_generate_') for method in dir(model)
                ):
                    auto_id_models.append(f"{model._meta.app_label}.{model.__name__}")

        if auto_id_models:
            print(f"   [OK] {len(auto_id_models)} models with auto-ID generation")
        else:
            print("   [INFO] No auto-ID generation methods detected")

    def print_report(self):
        """Print final validation report"""
        print("\n" + "=" * 80)
        print("VALIDATION REPORT")
        print("=" * 80)

        print(f"\nStatistics:")
        print(f"  - Total Models: {self.stats['total_models']}")
        print(f"  - Total Fields: {self.stats['total_fields']}")
        print(f"  - Missing __str__: {self.stats['missing_str']}")
        print(f"  - Missing docstrings: {self.stats['missing_docstring']}")
        print(f"  - Missing help_text: {self.stats['missing_help_text']}")
        print(f"  - Missing related_name: {self.stats['missing_related_name']}")

        if self.issues:
            print(f"\n[CRITICAL ISSUES] ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  - {issue}")

        if self.warnings:
            print(f"\n[WARNINGS] ({len(self.warnings)}):")
            for warning in self.warnings[:20]:
                print(f"  - {warning}")
            if len(self.warnings) > 20:
                print(f"  ... and {len(self.warnings) - 20} more")

        print("\n" + "=" * 80)
        if len(self.issues) == 0:
            print("RESULT: VALIDATION PASSED!")
            print("No critical issues found.")
        else:
            print(f"RESULT: VALIDATION FAILED!")
            print(f"{len(self.issues)} critical issues must be fixed.")
        print("=" * 80)


def main():
    validator = SystemValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
