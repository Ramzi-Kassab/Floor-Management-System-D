#!/usr/bin/env python
"""Setup PDC Cutters category with all attributes."""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ardt_fms.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.inventory.models import InventoryCategory, Attribute, CategoryAttribute

def setup_pdc_cutters():
    print("Setting up PDC Cutters category and attributes...")

    # Create parent category first
    cutters, created = InventoryCategory.objects.get_or_create(
        code='CUTTERS',
        defaults={
            'name': 'Cutters',
            'item_type': 'COMPONENT',
            'code_prefix': 'CUT'
        }
    )
    print(f"  Parent: CUTTERS {'(created)' if created else '(exists)'}")

    # Get or create PDC Cutters category (check both possible codes)
    pdc = InventoryCategory.objects.filter(code__in=['CUT-PDC', 'CT-PDC']).first()
    if not pdc:
        pdc = InventoryCategory.objects.create(
            code='CUT-PDC',
            name='PDC Cutters',
            parent=cutters,
            item_type='COMPONENT',
            code_prefix='PDC'
        )
        print(f"  Category: CUT-PDC (created)")
    else:
        print(f"  Category: {pdc.code} (exists, ID={pdc.pk})")

    # Full attribute configurations
    pdc_attributes = [
        {
            'code': 'item_number',
            'name': 'Item Number',
            'data_type': 'text',
            'classification': 'IDEN',
            'is_required': False,
            'show_in_list': True,
        },
        {
            'code': 'hdbs_code',
            'name': 'HDBS Code',
            'data_type': 'text',
            'classification': 'IDEN',
            'is_required': True,
            'show_in_list': True,
        },
        {
            'code': 'cutter_size',
            'name': 'Cutter Size',
            'data_type': 'select',
            'classification': 'PHYS',
            'is_required': True,
            'show_in_list': True,
            'unit': 'mm',
            'options': ['8', '9', '11', '13', '13.44', '16', '19', '22'],
        },
        {
            'code': 'diameter',
            'name': 'Diameter',
            'data_type': 'decimal',
            'classification': 'PHYS',
            'is_required': False,
            'unit': 'mm',
            'min_value': 5,
            'max_value': 30,
        },
        {
            'code': 'length',
            'name': 'Length',
            'data_type': 'decimal',
            'classification': 'PHYS',
            'is_required': False,
            'unit': 'mm',
        },
        {
            'code': 'length_class',
            'name': 'Length Class',
            'data_type': 'select',
            'classification': 'PHYS',
            'options': ['Short', 'Standard', 'Long', 'Extra Long'],
        },
        {
            'code': 'cutter_type',
            'name': 'Cutter Type',
            'data_type': 'select',
            'classification': 'TECH',
            'is_required': True,
            'show_in_list': True,
            'options': ['CT', 'WC', 'PDC', 'TSP', 'IMP', 'NAT'],
        },
        {
            'code': 'additional_description',
            'name': 'Additional Description',
            'data_type': 'text',
            'classification': 'GEN',
        },
        {
            'code': 'chamfer',
            'name': 'Chamfer',
            'data_type': 'select',
            'classification': 'TECH',
            'show_in_list': True,
            'options': ['NA', 'U-45', 'U-60', 'U-70', '18C-45', '18C-60', '18C-70', 'DC-45', 'DC-60'],
        },
        {
            'code': 'cutter_shape',
            'name': 'Cutter Shape',
            'data_type': 'select',
            'classification': 'TECH',
            'options': ['Flat', 'Dome', 'Conical', 'Chisel', 'Scribe', 'Axe'],
        },
        {
            'code': 'substrate_shape',
            'name': 'Substrate Shape',
            'data_type': 'select',
            'classification': 'TECH',
            'options': ['Cylindrical', 'Stud', 'Cone', 'Custom'],
        },
        {
            'code': 'diamond_thickness',
            'name': 'Diamond Thickness',
            'data_type': 'decimal',
            'classification': 'TECH',
            'unit': 'mm',
            'min_value': 0.5,
            'max_value': 5,
        },
        {
            'code': 'separator_type',
            'name': 'Separator Type',
            'data_type': 'select',
            'classification': 'TECH',
            'options': ['None', 'Standard', 'Heavy Duty'],
        },
        {
            'code': 'family',
            'name': 'Family',
            'data_type': 'text',
            'classification': 'IDEN',
            'show_in_list': True,
        },
        {
            'code': 'use',
            'name': 'Use',
            'data_type': 'select',
            'classification': 'OPER',
            'options': ['Primary', 'Backup', 'Gauge', 'Cone', 'Shoulder', 'Nose'],
        },
        {
            'code': 'cutter_grade',
            'name': 'Cutter Grade',
            'data_type': 'select',
            'classification': 'TECH',
            'show_in_list': True,
            'options': ['Premium', 'Standard', 'Economy', 'High Impact', 'High Abrasion', 'Thermal Stable'],
        },
        {
            'code': 'rotatability',
            'name': 'Rotatability',
            'data_type': 'select',
            'classification': 'TECH',
            'options': ['Non-Rotating', 'Free Rotating', 'Controlled Rotating'],
        },
        {
            'code': 'dynamic',
            'name': 'Dynamic',
            'data_type': 'select',
            'classification': 'TECH',
            'options': ['Static', 'Dynamic', 'Semi-Dynamic'],
        },
    ]

    print("\nConfiguring attributes:")
    for attr_config in pdc_attributes:
        code = attr_config.pop('code')
        name = attr_config.pop('name')
        data_type = attr_config.get('data_type', 'text')
        classification = attr_config.pop('classification', 'GEN')

        # Create or update attribute
        attr, attr_created = Attribute.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'data_type': data_type,
                'classification': classification
            }
        )

        # Prepare CategoryAttribute fields
        ca_fields = {
            'data_type': data_type,
            'is_required': attr_config.get('is_required', False),
            'show_in_list': attr_config.get('show_in_list', False),
            'unit': attr_config.get('unit', ''),
            'options': attr_config.get('options', []),
        }

        # Handle min/max if present
        if 'min_value' in attr_config:
            ca_fields['min_value'] = attr_config['min_value']
        if 'max_value' in attr_config:
            ca_fields['max_value'] = attr_config['max_value']

        # Update or create CategoryAttribute
        ca, ca_created = CategoryAttribute.objects.update_or_create(
            category=pdc,
            attribute=attr,
            defaults=ca_fields
        )

        status = '+ Created' if ca_created else '= Updated'
        opts = f' [{len(ca.options)} options]' if ca.options else ''
        unit = f' ({ca.unit})' if ca.unit else ''
        req = ' *REQUIRED' if ca.is_required else ''
        print(f"  {status}: {name}{req}{unit}{opts}")

    total = CategoryAttribute.objects.filter(category=pdc).count()
    print(f"\n✓ Done! CT-PDC now has {total} configured attributes")
    print(f"  View at: /inventory/categories/{pdc.pk}/")

if __name__ == '__main__':
    setup_pdc_cutters()
