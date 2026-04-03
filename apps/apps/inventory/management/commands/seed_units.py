"""
Seed command for Units of Measure.
Creates standard units from the comprehensive CSV file with full conversion support.

Usage:
    python manage.py seed_units           # Add/update only
    python manage.py seed_units --replace # Replace all (delete units not in CSV)
"""
import csv
import os
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from apps.inventory.models import UnitOfMeasure


class Command(BaseCommand):
    help = "Seed units of measure from CSV file with conversion data"

    # Map CSV categories to model UnitType choices
    CATEGORY_MAP = {
        "Length": "LENGTH",
        "Weight/Mass": "WEIGHT",
        "Volume": "VOLUME",
        "Area": "AREA",
        "Pressure": "PRESSURE",
        "Temperature": "TEMPERATURE",
        "Rotational Speed": "ROTATIONAL_SPEED",
        "Torque": "TORQUE",
        "Power": "POWER",
        "Voltage": "VOLTAGE",
        "Current": "CURRENT",
        "Resistance": "RESISTANCE",
        "Frequency": "FREQUENCY",
        "Flow Rate": "FLOW_RATE",
        "Angle": "ANGLE",
        "Speed": "SPEED",
        "Hardness": "HARDNESS",
        "Stress/Strength": "STRESS",
        "Ratio/Percentage": "RATIO",
        "Concentration": "CONCENTRATION",
        "Density": "DENSITY",
        "Viscosity": "VISCOSITY",
        "Quantity": "QUANTITY",
        "Packaging": "PACKAGING",
        "Time": "TIME",
        "Thread Specification": "THREAD_SPEC",
        "Wire Specification": "WIRE_SPEC",
        "Surface Finish": "SURFACE_FINISH",
        "Abrasive Specification": "ABRASIVE_SPEC",
        "Particle Size": "PARTICLE_SIZE",
        "Chemical Property": "CHEMICAL",
        "Sound/Noise": "SOUND",
        "Illumination": "ILLUMINATION",
        "Luminous Flux": "LUMINOUS_FLUX",
        "Energy": "ENERGY",
        "Force": "FORCE",
    }

    # Packaging units (variable conversion per item)
    PACKAGING_UNITS = {
        "BOX", "BAG", "DRUM", "PALLET", "ROLL", "SPOOL", "REEL",
        "COIL", "BUNDLE", "SET"
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Replace mode: delete units not in CSV file',
        )

    def handle(self, *args, **options):
        replace_mode = options.get('replace', False)

        if replace_mode:
            self.stdout.write(self.style.WARNING("Running in REPLACE mode - units not in CSV will be deleted"))
        else:
            self.stdout.write("Seeding Units of Measure from CSV...")

        csv_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..', '..', '..',
            'docs', 'development', 'units_comprehensive.csv'
        )
        csv_path = os.path.normpath(csv_path)

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f"CSV file not found: {csv_path}"))
            return

        # Read all rows from CSV
        rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get('Unit Code', '').strip()
                if code:  # Skip empty rows
                    rows.append(row)

        csv_codes = {row['Unit Code'].strip() for row in rows}

        # PASS 1: Create/update all units (without base_unit references)
        self.stdout.write("\n--- Pass 1: Creating/updating units ---")
        created_count = 0
        updated_count = 0

        for row in rows:
            code = row.get('Unit Code', '').strip()
            name = row.get('Unit Name', '').strip()
            symbol = row.get('Unit Symbol', '').strip()
            category = row.get('Unit Category', '').strip()
            description = row.get('Description', '').strip()
            conversion_notes = row.get('Conversion Notes', '').strip()
            base_unit_code = row.get('Base Unit', '').strip()

            # Parse conversion factor
            conv_factor_str = row.get('Conversion Factor', '').strip()
            try:
                conversion_factor = Decimal(conv_factor_str) if conv_factor_str else Decimal('1')
            except InvalidOperation:
                conversion_factor = Decimal('1')

            # Map category to unit_type
            unit_type = self.CATEGORY_MAP.get(category, "OTHER")

            # Determine if SI base (no base_unit means it's a base unit)
            is_si_base = not base_unit_code and conversion_factor == Decimal('1')
            is_packaging = code in self.PACKAGING_UNITS

            # Build description
            full_description = description
            if conversion_notes:
                full_description = f"{description}. {conversion_notes}" if description else conversion_notes

            # Create or update the unit (without base_unit for now)
            unit, created = UnitOfMeasure.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "unit_type": unit_type,
                    "symbol": symbol,
                    "is_si_base": is_si_base,
                    "is_packaging": is_packaging,
                    "conversion_factor": conversion_factor,
                    "description": full_description,
                    "is_active": True,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f"  + {code} - {name} [{unit_type}]")
            else:
                updated_count += 1

        self.stdout.write(f"  Created: {created_count}, Updated: {updated_count}")

        # PASS 2: Set base_unit references
        self.stdout.write("\n--- Pass 2: Setting base unit references ---")
        ref_count = 0
        ref_errors = []

        for row in rows:
            code = row.get('Unit Code', '').strip()
            base_unit_code = row.get('Base Unit', '').strip()

            if not base_unit_code:
                continue  # No base unit to set

            try:
                unit = UnitOfMeasure.objects.get(code=code)
                base_unit = UnitOfMeasure.objects.filter(code=base_unit_code).first()

                if base_unit:
                    unit.base_unit = base_unit
                    unit.save(update_fields=['base_unit'])
                    ref_count += 1
                    self.stdout.write(f"  {code} -> {base_unit_code}")
                else:
                    ref_errors.append(f"{code} references unknown base unit: {base_unit_code}")
            except UnitOfMeasure.DoesNotExist:
                ref_errors.append(f"Unit not found: {code}")

        self.stdout.write(f"  Set {ref_count} base unit references")

        if ref_errors:
            self.stdout.write(self.style.WARNING("\n  Warnings:"))
            for err in ref_errors:
                self.stdout.write(self.style.WARNING(f"    - {err}"))

        # In replace mode, delete units not in CSV
        deleted_count = 0
        if replace_mode:
            units_to_delete = UnitOfMeasure.objects.exclude(code__in=csv_codes)
            deleted_count = units_to_delete.count()
            if deleted_count > 0:
                self.stdout.write(self.style.WARNING(f"\n--- Deleting {deleted_count} units not in CSV ---"))
                for unit in units_to_delete:
                    self.stdout.write(f"  - {unit.code} - {unit.name}")
                units_to_delete.delete()

        # Summary
        total = UnitOfMeasure.objects.count()
        with_base = UnitOfMeasure.objects.filter(base_unit__isnull=False).count()

        self.stdout.write(self.style.SUCCESS(f"""
=== Summary ===
Created: {created_count}
Updated: {updated_count}
Deleted: {deleted_count}
Total units: {total}
With conversions: {with_base}
"""))
