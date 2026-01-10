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
    print("Setting up PDC Cutters category attributes...")

    # Get the existing PDC Cutters category
    pdc = InventoryCategory.objects.filter(code__in=['CUT-PDC', 'CT-PDC']).first()
    if not pdc:
        print("ERROR: PDC Cutters category not found!")
        print("Please create the category first via the UI or run:")
        print("  InventoryCategory.objects.create(code='CUT-PDC', name='PDC Cutters')")
        return

    print(f"  Found category: {pdc.code} - {pdc.name} (ID={pdc.pk})")

    # PDC Cutter attributes with correct field names for CategoryAttribute model
    # attribute_type choices: TEXT, NUMBER, BOOLEAN, DATE
    pdc_attributes = [
        {
            'code': 'item_number',
            'name': 'Item Number',
            'classification': 'IDEN',
            'attribute_type': 'TEXT',
            'is_required': False,
        },
        {
            'code': 'hdbs_code',
            'name': 'HDBS Code',
            'classification': 'IDEN',
            'attribute_type': 'TEXT',
            'is_required': True,
            'is_used_in_name': True,
        },
        {
            'code': 'cutter_size',
            'name': 'Cutter Size',
            'classification': 'PHYS',
            'attribute_type': 'TEXT',
            'is_required': True,
            'is_used_in_name': True,
            'options': ['8', '9', '11', '13', '13.44', '16', '19', '22'],
        },
        {
            'code': 'diameter',
            'name': 'Diameter',
            'classification': 'PHYS',
            'attribute_type': 'NUMBER',
            'is_required': False,
            'min_value': 5,
            'max_value': 30,
        },
        {
            'code': 'length',
            'name': 'Length',
            'classification': 'PHYS',
            'attribute_type': 'NUMBER',
            'is_required': False,
        },
        {
            'code': 'length_class',
            'name': 'Length Class',
            'classification': 'PHYS',
            'attribute_type': 'TEXT',
            'options': ['Short', 'Standard', 'Long', 'Extra Long'],
        },
        {
            'code': 'cutter_type',
            'name': 'Cutter Type',
            'classification': 'TECH',
            'attribute_type': 'TEXT',
            'is_required': True,
            'is_used_in_name': True,
            'options': ['CT', 'WC', 'PDC', 'TSP', 'IMP', 'NAT'],
        },
        {
            'code': 'additional_description',
            'name': 'Additional Description',
            'classification': 'GEN',
            'attribute_type': 'TEXT',
        },
        {
            'code': 'chamfer',
            'name': 'Chamfer',
            'classification': 'TECH',
            'attribute_type': 'TEXT',
            'is_used_in_name': True,
            'options': ['NA', 'U-45', 'U-60', 'U-70', '18C-45', '18C-60', '18C-70', 'DC-45', 'DC-60'],
        },
        {
            'code': 'cutter_shape',
            'name': 'Cutter Shape',
            'classification': 'TECH',
            'attribute_type': 'TEXT',
            'options': ['Flat', 'Dome', 'Conical', 'Chisel', 'Scribe', 'Axe'],
        },
        {
            'code': 'substrate_shape',
            'name': 'Substrate Shape',
            'classification': 'TECH',
            'attribute_type': 'TEXT',
            'options': ['Cylindrical', 'Stud', 'Cone', 'Custom'],
        },
        {
            'code': 'diamond_thickness',
            'name': 'Diamond Thickness',
            'classification': 'TECH',
            'attribute_type': 'NUMBER',
            'min_value': 0.5,
            'max_value': 5,
        },
        {
            'code': 'separator_type',
            'name': 'Separator Type',
            'classification': 'TECH',
            'attribute_type': 'TEXT',
            'options': ['None', 'Standard', 'Heavy Duty'],
        },
        {
            'code': 'family',
            'name': 'Family',
            'classification': 'IDEN',
            'attribute_type': 'TEXT',
            'is_used_in_name': True,
        },
        {
            'code': 'use',
            'name': 'Use',
            'classification': 'OPER',
            'attribute_type': 'TEXT',
            'options': ['Primary', 'Backup', 'Gauge', 'Cone', 'Shoulder', 'Nose'],
        },
        {
            'code': 'cutter_grade',
            'name': 'Cutter Grade',
            'classification': 'TECH',
            'attribute_type': 'TEXT',
            'is_used_in_name': True,
            'options': ['Premium', 'Standard', 'Economy', 'High Impact', 'High Abrasion', 'Thermal Stable'],
        },
        {
            'code': 'rotatability',
            'name': 'Rotatability',
            'classification': 'TECH',
            'attribute_type': 'TEXT',
            'options': ['Non-Rotating', 'Free Rotating', 'Controlled Rotating'],
        },
        {
            'code': 'dynamic',
            'name': 'Dynamic',
            'classification': 'TECH',
            'attribute_type': 'TEXT',
            'options': ['Static', 'Dynamic', 'Semi-Dynamic'],
        },
    ]

    print("\nConfiguring attributes:")
    display_order = 1

    for attr_config in pdc_attributes:
        code = attr_config['code']
        name = attr_config['name']
        classification = attr_config.get('classification', 'GEN')

        # Create or update the Attribute
        attr, attr_created = Attribute.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'classification': classification
            }
        )

        # Build CategoryAttribute fields
        ca_defaults = {
            'attribute_type': attr_config.get('attribute_type', 'TEXT'),
            'is_required': attr_config.get('is_required', False),
            'is_used_in_name': attr_config.get('is_used_in_name', False),
            'display_order': display_order,
        }

        # Add options if present
        if 'options' in attr_config:
            ca_defaults['options'] = attr_config['options']

        # Add min/max if present (convert to Decimal)
        if 'min_value' in attr_config:
            from decimal import Decimal
            ca_defaults['min_value'] = Decimal(str(attr_config['min_value']))
        if 'max_value' in attr_config:
            from decimal import Decimal
            ca_defaults['max_value'] = Decimal(str(attr_config['max_value']))

        # Create or update CategoryAttribute
        ca, ca_created = CategoryAttribute.objects.update_or_create(
            category=pdc,
            attribute=attr,
            defaults=ca_defaults
        )

        status = '+ Created' if ca_created else '= Updated'
        opts = f' [{len(ca.options)} options]' if ca.options else ''
        req = ' *REQUIRED' if ca.is_required else ''
        name_flag = ' [in name]' if ca.is_used_in_name else ''
        print(f"  {status}: {name}{req}{opts}{name_flag}")

        display_order += 1

    total = CategoryAttribute.objects.filter(category=pdc).count()
    print(f"\n✓ Done! {pdc.code} now has {total} configured attributes")
    print(f"  View at: /inventory/categories/{pdc.pk}/")

if __name__ == '__main__':
    setup_pdc_cutters()
