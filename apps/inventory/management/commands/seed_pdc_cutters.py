"""
Seed PDC Cutters category with all its attributes.

This links attributes to the PDC Cutters (CUT-PDC) category with proper
configuration: required flags, dropdown options, min/max values, number types, etc.

Usage:
    python manage.py seed_pdc_cutters
"""
from django.core.management.base import BaseCommand
from apps.inventory.models import InventoryCategory, Attribute, CategoryAttribute


class Command(BaseCommand):
    help = "Seed PDC Cutters category attributes"

    # PDC Cutters attribute definitions with enhanced configuration
    # Format: {
    #   'code': attribute code,
    #   'type': TEXT/NUMBER/BOOLEAN/DATE,
    #   'required': bool,
    #   'in_name': bool,
    #   'order': int,
    #   'options': list or None,
    #   'min': number or None,
    #   'max': number or None,
    #   'number_type': INTEGER/DECIMAL (for NUMBER type),
    #   'allow_negative': bool (for NUMBER type),
    #   'decimal_places': int (for DECIMAL type),
    #   'placeholder': str,
    #   'help_text': str,
    # }
    PDC_ATTRIBUTES = [
        {
            'code': 'item_number',
            'type': 'TEXT',
            'required': False,
            'in_name': False,
            'order': 1,
            'placeholder': 'e.g., PDC-001',
            'help_text': 'Internal item tracking number',
        },
        {
            'code': 'hdbs_code',
            'type': 'TEXT',
            'required': True,
            'in_name': True,
            'order': 2,
            'placeholder': 'e.g., HDBS-12345',
            'help_text': 'HDBS system code for cutter identification',
        },
        {
            'code': 'cutter_size',
            'type': 'TEXT',
            'required': True,
            'in_name': True,
            'order': 3,
            'options': ['8', '9', '11', '13', '13.44', '16', '19', '22'],
            'help_text': 'Standard cutter size in mm',
        },
        {
            'code': 'diameter',
            'type': 'NUMBER',
            'required': False,
            'in_name': False,
            'order': 4,
            'min': 5,
            'max': 30,
            'number_type': 'DECIMAL',
            'allow_negative': False,
            'decimal_places': 2,
            'placeholder': '5.00 - 30.00',
            'help_text': 'Cutter diameter in mm',
        },
        {
            'code': 'length',
            'type': 'NUMBER',
            'required': False,
            'in_name': False,
            'order': 5,
            'number_type': 'DECIMAL',
            'allow_negative': False,
            'decimal_places': 2,
            'placeholder': 'Length in mm',
            'help_text': 'Overall cutter length',
        },
        {
            'code': 'length_class',
            'type': 'TEXT',
            'required': False,
            'in_name': False,
            'order': 6,
            'options': ['Short', 'Standard', 'Long', 'Extra Long'],
            'help_text': 'Length classification category',
        },
        {
            'code': 'cutter_type',
            'type': 'TEXT',
            'required': True,
            'in_name': True,
            'order': 7,
            'options': ['CT', 'WC', 'PDC', 'TSP', 'IMP', 'NAT'],
            'help_text': 'CT=Carbide, WC=Tungsten Carbide, PDC=Polycrystalline Diamond, TSP=Thermally Stable, IMP=Impregnated, NAT=Natural',
        },
        {
            'code': 'additional_description',
            'type': 'TEXT',
            'required': False,
            'in_name': False,
            'order': 8,
            'is_multiline': True,
            'placeholder': 'Additional notes or specifications',
            'help_text': 'Free-text description for special characteristics',
        },
        {
            'code': 'chamfer',
            'type': 'TEXT',
            'required': False,
            'in_name': True,
            'order': 9,
            'options': ['NA', 'U-45', 'U-60', 'U-70', 'C-45', 'C-60', 'D-45', 'D-60', 'Custom'],
            'help_text': 'Chamfer type: U=Uniform, C=Compound, D=Double. Number is angle in degrees.',
        },
        {
            'code': 'cutter_shape',
            'type': 'TEXT',
            'required': False,
            'in_name': False,
            'order': 10,
            'options': ['Flat', 'Dome', 'Conical', 'Ridged', 'Scribe', 'Custom'],
            'help_text': 'Top surface geometry of the cutter',
        },
        {
            'code': 'substrate_shape',
            'type': 'TEXT',
            'required': False,
            'in_name': False,
            'order': 11,
            'options': ['Cylindrical', 'Stud', 'Cone', 'Custom'],
            'help_text': 'Shape of the tungsten carbide substrate',
        },
        {
            'code': 'diamond_thickness',
            'type': 'NUMBER',
            'required': False,
            'in_name': False,
            'order': 12,
            'min': 0.5,
            'max': 5,
            'number_type': 'DECIMAL',
            'allow_negative': False,
            'decimal_places': 2,
            'placeholder': '0.5 - 5.0',
            'help_text': 'Diamond layer thickness in mm',
        },
        {
            'code': 'separator_type',
            'type': 'TEXT',
            'required': False,
            'in_name': False,
            'order': 13,
            'options': ['None', 'Standard', 'Heavy Duty'],
            'help_text': 'Type of separator used for cutter installation',
        },
        {
            'code': 'family',
            'type': 'TEXT',
            'required': False,
            'in_name': True,
            'order': 14,
            'placeholder': 'e.g., Premium Series',
            'help_text': 'Product family or series name',
        },
        {
            'code': 'use',
            'type': 'TEXT',
            'required': False,
            'in_name': False,
            'order': 15,
            'options': ['Primary', 'Backup', 'Gauge', 'Shoulder', 'Nose', 'Cone'],
            'help_text': 'Intended cutter position on the bit',
        },
        {
            'code': 'cutter_grade',
            'type': 'TEXT',
            'required': False,
            'in_name': True,
            'order': 16,
            'options': ['Premium', 'Standard', 'Economy', 'High Impact', 'Abrasion Resistant', 'Thermal Stable'],
            'help_text': 'Quality/performance grade classification',
        },
        {
            'code': 'rotatability',
            'type': 'TEXT',
            'required': False,
            'in_name': False,
            'order': 17,
            'options': ['Non-Rotating', 'Free', 'Controlled'],
            'help_text': 'Cutter rotation capability in pocket',
        },
        {
            'code': 'dynamic',
            'type': 'TEXT',
            'required': False,
            'in_name': False,
            'order': 18,
            'options': ['Static', 'Dynamic', 'Semi-Dynamic'],
            'help_text': 'Dynamic behavior classification',
        },
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

        for attr_def in self.PDC_ATTRIBUTES:
            # Find the attribute
            attr = Attribute.objects.filter(code=attr_def['code']).first()
            if not attr:
                self.stdout.write(self.style.WARNING(f"  ⚠ Attribute not found: {attr_def['code']}"))
                skipped_count += 1
                continue

            # Build the defaults dict
            defaults = {
                'attribute_type': attr_def['type'],
                'is_required': attr_def.get('required', False),
                'is_used_in_name': attr_def.get('in_name', False),
                'display_order': attr_def.get('order', 0),
                'options': attr_def.get('options', []),
                'min_value': attr_def.get('min'),
                'max_value': attr_def.get('max'),
                # New fields
                'number_type': attr_def.get('number_type', 'DECIMAL'),
                'allow_negative': attr_def.get('allow_negative', True),
                'decimal_places': attr_def.get('decimal_places', 2),
                'is_multiline': attr_def.get('is_multiline', False),
                'placeholder': attr_def.get('placeholder', ''),
                'field_help_text': attr_def.get('help_text', ''),
            }

            # Create or update CategoryAttribute
            ca, created = CategoryAttribute.objects.update_or_create(
                category=pdc,
                attribute=attr,
                defaults=defaults
            )

            flags = []
            if attr_def.get('required'):
                flags.append('REQUIRED')
            if attr_def.get('in_name'):
                flags.append('in name')
            if attr_def.get('options'):
                flags.append(f'{len(attr_def["options"])} options')
            if attr_def['type'] == 'NUMBER':
                flags.append(attr_def.get('number_type', 'DECIMAL').lower())

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
