"""
Seed Special Technologies reference data.
"""

from django.core.management.base import BaseCommand

from apps.technology.models import SpecialTechnology


class Command(BaseCommand):
    help = "Seed Special Technologies reference data"

    def handle(self, *args, **options):
        technologies = [
            {"code": "CP", "name": "Cerebro Puck", "description": "Cerebro Puck technology for enhanced ROP feedback"},
            {"code": "CF", "name": "Cerebro Force", "description": "Cerebro Force technology for weight-on-bit monitoring"},
            {"code": "TP", "name": "Torpedo", "description": "Torpedo nozzle technology for improved hydraulics"},
            {"code": "DS", "name": "DualString", "description": "DualString cutter technology"},
            {"code": "AXIS", "name": "AXIS", "description": "AXIS stabilization technology"},
            {"code": "SST", "name": "SteerStar", "description": "SteerStar directional technology"},
            {"code": "TCD", "name": "TCD", "description": "Thermally Conductive Diamond technology"},
            {"code": "RGD", "name": "RGD", "description": "Rolling Gauge Device"},
            {"code": "VBS", "name": "VBS", "description": "Vibration Blocking System"},
            {"code": "FM", "name": "ForceMaster", "description": "ForceMaster cutter placement technology"},
        ]

        created = 0
        for tech_data in technologies:
            obj, was_created = SpecialTechnology.objects.update_or_create(
                code=tech_data["code"],
                defaults={
                    "name": tech_data["name"],
                    "description": tech_data["description"],
                    "is_active": True,
                },
            )
            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(f"SpecialTechnology: {created} created, {len(technologies) - created} already exist")
        )
