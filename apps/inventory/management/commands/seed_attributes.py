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

        # Common attributes - just code and name
        # Type, unit, validation are defined when connecting to category
        attributes = [
            # Physical dimensions
            ("size", "Size", "Physical size (could be number or text depending on category)"),
            ("diameter", "Diameter", "Diameter measurement"),
            ("length", "Length", "Length measurement"),
            ("width", "Width", "Width measurement"),
            ("height", "Height", "Height measurement"),
            ("thickness", "Thickness", "Thickness measurement"),
            ("depth", "Depth", "Depth measurement"),
            ("weight", "Weight", "Weight measurement"),
            ("volume", "Volume", "Volume measurement"),

            # Material properties
            ("material", "Material", "Material type or composition"),
            ("grade", "Grade", "Quality grade or classification"),
            ("hardness", "Hardness", "Hardness rating"),
            ("density", "Density", "Material density"),
            ("tensile_strength", "Tensile Strength", "Tensile strength rating"),
            ("finish", "Finish", "Surface finish"),
            ("coating", "Coating", "Coating type"),

            # Appearance
            ("color", "Color", "Color designation"),
            ("pattern", "Pattern", "Pattern or design"),
            ("style", "Style", "Style designation"),

            # Technical specifications
            ("model", "Model", "Model number or designation"),
            ("series", "Series", "Product series"),
            ("version", "Version", "Version number"),
            ("generation", "Generation", "Product generation"),
            ("capacity", "Capacity", "Capacity measurement"),
            ("power", "Power", "Power rating"),
            ("voltage", "Voltage", "Voltage rating"),
            ("current", "Current", "Current rating"),
            ("frequency", "Frequency", "Frequency rating"),
            ("pressure", "Pressure", "Pressure rating"),
            ("temperature", "Temperature", "Temperature rating"),
            ("speed", "Speed", "Speed rating (RPM, etc.)"),
            ("torque", "Torque", "Torque rating"),
            ("flow_rate", "Flow Rate", "Flow rate measurement"),

            # Thread/connection specs
            ("thread_type", "Thread Type", "Thread type (API, NPT, etc.)"),
            ("thread_size", "Thread Size", "Thread size specification"),
            ("connection_type", "Connection Type", "Connection type"),
            ("connection_size", "Connection Size", "Connection size"),

            # Bit/cutter specific
            ("body_od", "Body OD", "Body outer diameter"),
            ("gauge", "Gauge", "Gauge measurement"),
            ("tfa", "TFA", "Total Flow Area"),
            ("blade_count", "Blade Count", "Number of blades"),
            ("cutter_count", "Cutter Count", "Number of cutters"),
            ("nozzle_count", "Nozzle Count", "Number of nozzles"),
            ("nozzle_size", "Nozzle Size", "Nozzle size"),
            ("jet_count", "Jet Count", "Number of jets"),
            ("insert_type", "Insert Type", "Type of insert"),
            ("insert_count", "Insert Count", "Number of inserts"),

            # Classification
            ("category", "Category", "Category classification"),
            ("type", "Type", "Type classification"),
            ("class", "Class", "Class rating"),
            ("rating", "Rating", "General rating"),

            # Manufacturer info
            ("manufacturer", "Manufacturer", "Manufacturer name"),
            ("brand", "Brand", "Brand name"),
            ("country_of_origin", "Country of Origin", "Manufacturing country"),

            # Certification/compliance
            ("certification", "Certification", "Certification type"),
            ("standard", "Standard", "Standard compliance"),
            ("api_spec", "API Spec", "API specification"),

            # Packaging
            ("quantity_per_pack", "Quantity per Pack", "Items per package"),
            ("pack_size", "Pack Size", "Package size"),
            ("shelf_life", "Shelf Life", "Shelf life duration"),

            # Other common attributes
            ("tolerance", "Tolerance", "Tolerance specification"),
            ("accuracy", "Accuracy", "Accuracy rating"),
            ("resolution", "Resolution", "Resolution specification"),
            ("range", "Range", "Operating range"),
            ("efficiency", "Efficiency", "Efficiency rating"),
        ]

        created_count = 0
        for code, name, description in attributes:
            attr, created = Attribute.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": description,
                    "is_active": True,
                }
            )
            if created:
                self.stdout.write(f"  Created: {name}")
                created_count += 1
            else:
                self.stdout.write(f"  Exists: {name}")

        self.stdout.write(self.style.SUCCESS(f"\nTotal attributes: {Attribute.objects.count()} (new: {created_count})"))
