"""
Management command to fix variant codes and migrate to new variant cases.

Fixes:
1. Updates ItemVariants pointing to old/deprecated VariantCases
   to point to current canonical ones.
2. Regenerates variant codes using the new convention.

Deprecated → Current mapping:
  USED-RET  → NEW-RET   (Retrofit is NEW condition)
  NEW-ENO   → NEW-EO    (Renamed)
  USED-EO   → NEW-EO    (E&O is NEW condition)
  USED-GRD  → GRD-EO    (Renamed)
  USED-STD  → USED-RCL  (Renamed)
  CLI-USED  → CLI-RCL   (Renamed)
  NEW-CLI   → CLI-NEW   (Renamed — client-owned uses CLI- prefix)
  USED-CLI  → CLI-RCL   (Renamed — client-owned reclaim)
"""

from django.core.management.base import BaseCommand
from apps.inventory.models import ItemVariant, VariantCase


class Command(BaseCommand):
    help = "Fix variant codes and migrate to new variant cases"

    def handle(self, *args, **options):
        self.stdout.write("Fixing variant codes...")

        # Mapping of old/deprecated variant case codes to current canonical ones
        # NOTE: Must match seed_variant_cases.py and apps/inventory/constants.py
        case_mapping = {
            'USED-RET': 'NEW-RET',    # Retrofit is NEW condition
            'NEW-ENO': 'NEW-EO',      # Renamed (was typo in old code)
            'USED-EO': 'NEW-EO',      # E&O is NEW condition
            'USED-GRD': 'GRD-EO',     # Renamed to E&O Ground
            'USED-STD': 'USED-RCL',   # Renamed to Used Reclaimed
            'CLI-USED': 'CLI-RCL',    # Renamed to Client Reclaimed
            'NEW-CLI': 'CLI-NEW',      # Client-owned uses CLI- prefix
            'USED-CLI': 'CLI-RCL',     # Client reclaimed
        }

        # Get all variant cases
        old_cases = {vc.code: vc for vc in VariantCase.objects.filter(code__in=case_mapping.keys())}
        new_cases = {vc.code: vc for vc in VariantCase.objects.filter(code__in=case_mapping.values())}

        migrated_count = 0
        code_fixed_count = 0

        for variant in ItemVariant.objects.select_related('base_item', 'variant_case', 'customer'):
            needs_save = False

            # Check if variant case needs migration
            if variant.variant_case and variant.variant_case.code in case_mapping:
                new_case_code = case_mapping[variant.variant_case.code]
                if new_case_code in new_cases:
                    self.stdout.write(f"  Migrating {variant.code}: {variant.variant_case.code} -> {new_case_code}")
                    variant.variant_case = new_cases[new_case_code]
                    needs_save = True
                    migrated_count += 1

            # Regenerate variant code if needed
            if variant.variant_case:
                expected_code_parts = [variant.base_item.code, variant.variant_case.code]
                if variant.customer and hasattr(variant.customer, 'code') and variant.customer.code:
                    expected_code_parts.append(variant.customer.code[:6])
                expected_code = "-".join(expected_code_parts)

                if variant.code != expected_code:
                    self.stdout.write(f"  Fixing code: {variant.code} -> {expected_code}")
                    variant.code = expected_code
                    needs_save = True
                    code_fixed_count += 1

            if needs_save:
                variant.save()

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Migrated {migrated_count} variant cases, fixed {code_fixed_count} codes."
        ))
