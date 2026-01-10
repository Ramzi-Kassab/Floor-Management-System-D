"""
Seed PDC Cutters category with all its attributes.

This links attributes to the PDC Cutters (CUT-PDC) category with proper
configuration: required flags, dropdown options, min/max values, etc.

Usage:
    python manage.py seed_pdc_cutters
"""
from django.core.management.base import BaseCommand
from apps.inventory.models import InventoryCategory, Attribute, CategoryAttribute


class Command(BaseCommand):
    help = "Seed PDC Cutters category attributes"

    # PDC Cutters attribute definitions
    PDC_ATTRIBUTES = [
        # (code, attribute_type, is_required, is_used_in_name, display_order, options, min_val, max_val)
        ('item_number', 'TEXT', False, False, 1, None, None, None),
        ('hdbs_code', 'TEXT', True, True, 2, None, None, None),
        ('cutter_size', 'TEXT', True, True, 3, ['8', '9', '11', '13', '13.44', '16', '19', '22'], None, None),
        ('diameter', 'NUMBER', False, False, 4, None, 5, 30),
        ('length', 'NUMBER', False, False, 5, None, None, None),
        ('length_class', 'TEXT', False, False, 6, ['Short', 'Standard', 'Long', 'Extra Long'], None, None),
        ('cutter_type', 'TEXT', True, True, 7, ['CT', 'WC', 'PDC', 'TSP', 'IMP', 'NAT'], None, None),
        ('additional_description', 'TEXT', False, False, 8, None, None, None),
        ('chamfer', 'TEXT', False, True, 9, ['NA', 'U-45', 'U-60', 'U-70', 'C-45', 'C-60', 'D-45', 'D-60', 'Custom'], None, None),
        ('cutter_shape', 'TEXT', False, False, 10, ['Flat', 'Dome', 'Conical', 'Ridged', 'Scribe', 'Custom'], None, None),
        ('substrate_shape', 'TEXT', False, False, 11, ['Cylindrical', 'Stud', 'Cone', 'Custom'], None, None),
        ('diamond_thickness', 'NUMBER', False, False, 12, None, 0.5, 5),
        ('separator_type', 'TEXT', False, False, 13, ['None', 'Standard', 'Heavy Duty'], None, None),
        ('family', 'TEXT', False, True, 14, None, None, None),
        ('use', 'TEXT', False, False, 15, ['Primary', 'Backup', 'Gauge', 'Shoulder', 'Nose', 'Cone'], None, None),
        ('cutter_grade', 'TEXT', False, True, 16, ['Premium', 'Standard', 'Economy', 'High Impact', 'Abrasion Resistant', 'Thermal Stable'], None, None),
        ('rotatability', 'TEXT', False, False, 17, ['Non-Rotating', 'Free', 'Controlled'], None, None),
        ('dynamic', 'TEXT', False, False, 18, ['Static', 'Dynamic', 'Semi-Dynamic'], None, None),
    ]

    def handle(self, *args, **options):
        self.stdout.write("Seeding PDC Cutters category attributes...\n")

        # Find PDC Cutters category
        pdc = InventoryCategory.objects.filter(code__in=['CUT-PDC', 'CT-PDC']).first()
        if not pdc:
            self.stdout.write(self.style.ERROR("PDC Cutters category not found (CUT-PDC or CT-PDC)"))
            return

        self.stdout.write(f"  Found category: {pdc.code} - {pdc.name} (ID={pdc.id})\n")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for attr_code, attr_type, required, in_name, order, options, min_val, max_val in self.PDC_ATTRIBUTES:
            # Find the attribute
            attr = Attribute.objects.filter(code=attr_code).first()
            if not attr:
                self.stdout.write(self.style.WARNING(f"  ⚠ Attribute not found: {attr_code}"))
                skipped_count += 1
                continue

            # Create or update CategoryAttribute
            ca, created = CategoryAttribute.objects.update_or_create(
                category=pdc,
                attribute=attr,
                defaults={
                    'attribute_type': attr_type,
                    'is_required': required,
                    'is_used_in_name': in_name,
                    'display_order': order,
                    'options': options or [],
                    'min_value': min_val,
                    'max_value': max_val,
                }
            )

            flags = []
            if required:
                flags.append('REQUIRED')
            if in_name:
                flags.append('in name')
            if options:
                flags.append(f'{len(options)} options')

            flag_str = f" [{', '.join(flags)}]" if flags else ""

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  + Created: {attr.name}{flag_str}"))
            else:
                updated_count += 1
                self.stdout.write(f"  = Updated: {attr.name}{flag_str}")

        # Summary
        total = pdc.category_attributes.count()
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS(
            f"Done! Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}"
        ))
        self.stdout.write(self.style.SUCCESS(f"PDC Cutters now has {total} configured attributes"))
        self.stdout.write(f"View at: /inventory/categories/{pdc.id}/")
