"""
Seed command for Attributes - simple global list of attribute names.

Usage:
    python manage.py seed_attributes
"""

from django.core.management.base import BaseCommand
from apps.inventory.models import Attribute


class Command(BaseCommand):
    help = "Seed common attributes (just names, no type/unit/validation)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Attributes (global list)...\n")

        # Common attributes - just name and description
        # Code is auto-generated as ATT-001, ATT-002, etc.
        # Type, unit, validation are defined when connecting to category
        attributes = [
            # Physical dimensions
            ("Size", "Physical size (could be number or text depending on category)"),
            ("Diameter", "Diameter measurement"),
            ("Length", "Length measurement"),
            ("Width", "Width measurement"),
            ("Height", "Height measurement"),
            ("Thickness", "Thickness measurement"),
            ("Depth", "Depth measurement"),
            ("Weight", "Weight measurement"),
            ("Volume", "Volume measurement"),

            # Material properties
            ("Material", "Material type or composition"),
            ("Grade", "Quality grade or classification"),
            ("Hardness", "Hardness rating"),
            ("Density", "Material density"),
            ("Tensile Strength", "Tensile strength rating"),
            ("Finish", "Surface finish"),
            ("Coating", "Coating type"),

            # Appearance
            ("Color", "Color designation"),
            ("Pattern", "Pattern or design"),
            ("Style", "Style designation"),

            # Technical specifications
            ("Model", "Model number or designation"),
            ("Series", "Product series"),
            ("Version", "Version number"),
            ("Generation", "Product generation"),
            ("Capacity", "Capacity measurement"),
            ("Power", "Power rating"),
            ("Voltage", "Voltage rating"),
            ("Current", "Current rating"),
            ("Frequency", "Frequency rating"),
            ("Pressure", "Pressure rating"),
            ("Temperature", "Temperature rating"),
            ("Speed", "Speed rating (RPM, etc.)"),
            ("Torque", "Torque rating"),
            ("Flow Rate", "Flow rate measurement"),

            # Thread/connection specs
            ("Thread Type", "Thread type (API, NPT, etc.)"),
            ("Thread Size", "Thread size specification"),
            ("Connection Type", "Connection type"),
            ("Connection Size", "Connection size"),

            # Bit/cutter specific
            ("Body OD", "Body outer diameter"),
            ("Gauge", "Gauge measurement"),
            ("TFA", "Total Flow Area"),
            ("Blade Count", "Number of blades"),
            ("Cutter Count", "Number of cutters"),
            ("Nozzle Count", "Number of nozzles"),
            ("Nozzle Size", "Nozzle size"),
            ("Jet Count", "Number of jets"),
            ("Insert Type", "Type of insert"),
            ("Insert Count", "Number of inserts"),

            # Classification
            ("Category", "Category classification"),
            ("Type", "Type classification"),
            ("Class", "Class rating"),
            ("Rating", "General rating"),

            # Manufacturer info
            ("Manufacturer", "Manufacturer name"),
            ("Brand", "Brand name"),
            ("Country of Origin", "Manufacturing country"),

            # Certification/compliance
            ("Certification", "Certification type"),
            ("Standard", "Standard compliance"),
            ("API Spec", "API specification"),

            # Packaging
            ("Quantity per Pack", "Items per package"),
            ("Pack Size", "Package size"),
            ("Shelf Life", "Shelf life duration"),

            # Other common attributes
            ("Tolerance", "Tolerance specification"),
            ("Accuracy", "Accuracy rating"),
            ("Resolution", "Resolution specification"),
            ("Range", "Operating range"),
            ("Efficiency", "Efficiency rating"),
        ]

        created_count = 0
        for name, description in attributes:
            # Check if attribute with this name already exists
            attr, created = Attribute.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "is_active": True,
                }
            )
            if created:
                self.stdout.write(f"  Created: {attr.code} - {name}")
                created_count += 1
            else:
                self.stdout.write(f"  Exists: {attr.code} - {name}")

        self.stdout.write(self.style.SUCCESS(f"\nTotal attributes: {Attribute.objects.count()} (new: {created_count})"))
