"""
Seed command for Units of Measure.
Creates standard units with conversion factors.
"""
from django.core.management.base import BaseCommand
from apps.inventory.models import UnitOfMeasure


class Command(BaseCommand):
    help = "Seed standard units of measure with conversions"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Units of Measure...")

        # Define units by type
        units_data = [
            # QUANTITY (Count) - base unit: EA (Each)
            {"code": "EA", "name": "Each", "unit_type": "QUANTITY", "symbol": "ea", "is_base": True},
            {"code": "PC", "name": "Piece", "unit_type": "QUANTITY", "symbol": "pc", "base": "EA", "factor": 1},
            {"code": "SET", "name": "Set", "unit_type": "QUANTITY", "symbol": "set", "base": "EA", "factor": 1},
            {"code": "PK", "name": "Pack", "unit_type": "QUANTITY", "symbol": "pk", "base": "EA", "factor": 1, "description": "Varies by item - pieces per pack"},
            {"code": "BOX", "name": "Box", "unit_type": "QUANTITY", "symbol": "box", "base": "EA", "factor": 1, "description": "Varies by item - pieces per box"},
            {"code": "CTN", "name": "Carton", "unit_type": "QUANTITY", "symbol": "ctn", "base": "EA", "factor": 1, "description": "Varies by item - pieces per carton"},
            {"code": "PAL", "name": "Pallet", "unit_type": "QUANTITY", "symbol": "pallet", "base": "EA", "factor": 1, "description": "Varies by item - pieces per pallet"},
            {"code": "DZ", "name": "Dozen", "unit_type": "QUANTITY", "symbol": "dz", "base": "EA", "factor": 12},
            {"code": "GR", "name": "Gross", "unit_type": "QUANTITY", "symbol": "gross", "base": "EA", "factor": 144},

            # LENGTH - base unit: M (Meter)
            {"code": "M", "name": "Meter", "unit_type": "LENGTH", "symbol": "m", "is_base": True},
            {"code": "CM", "name": "Centimeter", "unit_type": "LENGTH", "symbol": "cm", "base": "M", "factor": 0.01},
            {"code": "MM", "name": "Millimeter", "unit_type": "LENGTH", "symbol": "mm", "base": "M", "factor": 0.001},
            {"code": "KM", "name": "Kilometer", "unit_type": "LENGTH", "symbol": "km", "base": "M", "factor": 1000},
            {"code": "IN", "name": "Inch", "unit_type": "LENGTH", "symbol": "in", "base": "M", "factor": 0.0254},
            {"code": "FT", "name": "Foot", "unit_type": "LENGTH", "symbol": "ft", "base": "M", "factor": 0.3048},
            {"code": "YD", "name": "Yard", "unit_type": "LENGTH", "symbol": "yd", "base": "M", "factor": 0.9144},
            {"code": "ROL", "name": "Roll", "unit_type": "LENGTH", "symbol": "roll", "base": "M", "factor": 1, "description": "Varies by item - meters per roll"},

            # WEIGHT - base unit: KG (Kilogram)
            {"code": "KG", "name": "Kilogram", "unit_type": "WEIGHT", "symbol": "kg", "is_base": True},
            {"code": "G", "name": "Gram", "unit_type": "WEIGHT", "symbol": "g", "base": "KG", "factor": 0.001},
            {"code": "MG", "name": "Milligram", "unit_type": "WEIGHT", "symbol": "mg", "base": "KG", "factor": 0.000001},
            {"code": "MT", "name": "Metric Ton", "unit_type": "WEIGHT", "symbol": "t", "base": "KG", "factor": 1000},
            {"code": "LB", "name": "Pound", "unit_type": "WEIGHT", "symbol": "lb", "base": "KG", "factor": 0.453592},
            {"code": "OZ", "name": "Ounce", "unit_type": "WEIGHT", "symbol": "oz", "base": "KG", "factor": 0.0283495},

            # VOLUME - base unit: L (Liter)
            {"code": "L", "name": "Liter", "unit_type": "VOLUME", "symbol": "L", "is_base": True},
            {"code": "ML", "name": "Milliliter", "unit_type": "VOLUME", "symbol": "mL", "base": "L", "factor": 0.001},
            {"code": "M3", "name": "Cubic Meter", "unit_type": "VOLUME", "symbol": "m³", "base": "L", "factor": 1000},
            {"code": "GAL", "name": "Gallon (US)", "unit_type": "VOLUME", "symbol": "gal", "base": "L", "factor": 3.78541},
            {"code": "QT", "name": "Quart (US)", "unit_type": "VOLUME", "symbol": "qt", "base": "L", "factor": 0.946353},
            {"code": "PT", "name": "Pint (US)", "unit_type": "VOLUME", "symbol": "pt", "base": "L", "factor": 0.473176},
            {"code": "BBL", "name": "Barrel (Oil)", "unit_type": "VOLUME", "symbol": "bbl", "base": "L", "factor": 158.987},
            {"code": "CF", "name": "Cubic Foot", "unit_type": "VOLUME", "symbol": "ft³", "base": "L", "factor": 28.3168},

            # AREA - base unit: M2 (Square Meter)
            {"code": "M2", "name": "Square Meter", "unit_type": "AREA", "symbol": "m²", "is_base": True},
            {"code": "CM2", "name": "Square Centimeter", "unit_type": "AREA", "symbol": "cm²", "base": "M2", "factor": 0.0001},
            {"code": "SF", "name": "Square Foot", "unit_type": "AREA", "symbol": "ft²", "base": "M2", "factor": 0.092903},
            {"code": "SY", "name": "Square Yard", "unit_type": "AREA", "symbol": "yd²", "base": "M2", "factor": 0.836127},

            # TIME - base unit: HR (Hour)
            {"code": "HR", "name": "Hour", "unit_type": "TIME", "symbol": "hr", "is_base": True},
            {"code": "MIN", "name": "Minute", "unit_type": "TIME", "symbol": "min", "base": "HR", "factor": 0.0166667},
            {"code": "DAY", "name": "Day", "unit_type": "TIME", "symbol": "day", "base": "HR", "factor": 24},
            {"code": "WK", "name": "Week", "unit_type": "TIME", "symbol": "wk", "base": "HR", "factor": 168},
            {"code": "MO", "name": "Month", "unit_type": "TIME", "symbol": "mo", "base": "HR", "factor": 720},

            # OTHER
            {"code": "JOB", "name": "Job", "unit_type": "OTHER", "symbol": "job", "is_base": True},
            {"code": "LOT", "name": "Lot", "unit_type": "OTHER", "symbol": "lot", "is_base": True},
            {"code": "SVC", "name": "Service", "unit_type": "OTHER", "symbol": "svc", "is_base": True},
        ]

        # First pass: create base units
        base_units = {}
        for unit_data in units_data:
            if unit_data.get("is_base"):
                unit, created = UnitOfMeasure.objects.update_or_create(
                    code=unit_data["code"],
                    defaults={
                        "name": unit_data["name"],
                        "unit_type": unit_data["unit_type"],
                        "symbol": unit_data.get("symbol", ""),
                        "conversion_factor": 1,
                        "description": unit_data.get("description", ""),
                        "is_active": True,
                    }
                )
                base_units[unit_data["code"]] = unit
                status = "Created" if created else "Updated"
                self.stdout.write(f"  {status}: {unit.code} - {unit.name} (BASE)")

        # Second pass: create derived units with conversions
        for unit_data in units_data:
            if not unit_data.get("is_base") and "base" in unit_data:
                base_unit = base_units.get(unit_data["base"])
                unit, created = UnitOfMeasure.objects.update_or_create(
                    code=unit_data["code"],
                    defaults={
                        "name": unit_data["name"],
                        "unit_type": unit_data["unit_type"],
                        "symbol": unit_data.get("symbol", ""),
                        "base_unit": base_unit,
                        "conversion_factor": unit_data.get("factor", 1),
                        "description": unit_data.get("description", ""),
                        "is_active": True,
                    }
                )
                status = "Created" if created else "Updated"
                self.stdout.write(f"  {status}: {unit.code} - {unit.name} (converts to {base_unit.code})")

        total = UnitOfMeasure.objects.count()
        self.stdout.write(self.style.SUCCESS(f"\nTotal units: {total}"))
