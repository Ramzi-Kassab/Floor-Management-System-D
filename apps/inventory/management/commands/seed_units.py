"""
Seed command for Units of Measure.
Creates standard units from the comprehensive CSV file.
"""
import csv
import os
from django.core.management.base import BaseCommand
from apps.inventory.models import UnitOfMeasure


class Command(BaseCommand):
    help = "Seed units of measure from CSV file"

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

    # SI base units per category
    SI_BASE_UNITS = {
        "M", "KG", "L", "EA", "M2", "HR", "SEC", "K", "A", "V",
        "OHM", "HZ", "NEWTON", "JOULE", "W", "PA_S", "RAD", "LUX",
        "LUMEN", "DEG", "PERCENT", "G_CM3", "CP"
    }

    # Packaging units
    PACKAGING_UNITS = {
        "BOX", "BAG", "DRUM", "PALLET", "ROLL", "SPOOL", "REEL",
        "COIL", "BUNDLE", "SET", "PAIR", "DOZEN"
    }

    def handle(self, *args, **options):
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

        created_count = 0
        updated_count = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                code = row.get('Unit Code', '').strip()
                if not code:
                    continue  # Skip empty rows

                name = row.get('Unit Name', '').strip()
                symbol = row.get('Unit Symbol', '').strip()
                category = row.get('Unit Category', '').strip()
                description = row.get('Description', '').strip()
                conversion_notes = row.get('Conversion Notes', '').strip()

                # Map category to unit_type
                unit_type = self.CATEGORY_MAP.get(category, "OTHER")

                # Determine if SI base or packaging
                is_si_base = code in self.SI_BASE_UNITS
                is_packaging = code in self.PACKAGING_UNITS

                # Build description
                full_description = description
                if conversion_notes:
                    full_description = f"{description}. {conversion_notes}" if description else conversion_notes

                # Create or update the unit
                unit, created = UnitOfMeasure.objects.update_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "unit_type": unit_type,
                        "symbol": symbol,
                        "is_si_base": is_si_base,
                        "is_packaging": is_packaging,
                        "description": full_description,
                        "is_active": True,
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(f"  Created: {code} - {name} [{unit_type}]")
                else:
                    updated_count += 1
                    self.stdout.write(f"  Updated: {code} - {name} [{unit_type}]")

        total = UnitOfMeasure.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created: {created_count}, Updated: {updated_count}, Total: {total}"
        ))
