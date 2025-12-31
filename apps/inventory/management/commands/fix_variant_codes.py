"""
Management command to fix variant codes and migrate to new variant cases.

Fixes:
1. Updates ItemVariants pointing to old VariantCases (USED-RET, USED-EO, etc.)
   to point to new ones (NEW-RET, NEW-ENO, etc.)
2. Regenerates variant codes using the new convention
"""

from django.core.management.base import BaseCommand
from apps.inventory.models import ItemVariant, VariantCase


class Command(BaseCommand):
    help = "Fix variant codes and migrate to new variant cases"

    def handle(self, *args, **options):
        self.stdout.write("Fixing variant codes...")

        # Mapping of old variant case codes to new ones
        case_mapping = {
            'USED-RET': 'NEW-RET',    # Retrofit is NEW condition
            'USED-EO': 'NEW-ENO',     # E&O is NEW condition
            'USED-RCL': 'USED-STD',   # Standard Reclaim
            'CLI-RCL': 'CLI-USED',    # Client Used
        }

        # Get all variant cases
        old_cases = {vc.code: vc for vc in VariantCase.objects.filter(code__in=case_mapping.keys())}
        new_cases = {vc.code: vc for vc in VariantCase.objects.filter(code__in=case_mapping.values())}

        migrated_count = 0
        code_fixed_count = 0

        for variant in ItemVariant.objects.select_related('base_item', 'variant_case', 'customer'):
            needs_save = False
            old_code = variant.code

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
