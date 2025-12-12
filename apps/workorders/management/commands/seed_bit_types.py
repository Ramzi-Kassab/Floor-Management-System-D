"""
ARDT FMS - Seed Bit Types
Phase 2: Products & Drill Bit Tracking

Creates product models/types used by ARDT (GT, HD, MM, FX series, etc.)
"""

from django.core.management.base import BaseCommand

from apps.workorders.models import BitType


class Command(BaseCommand):
    help = "Seed bit types (product models) for ARDT drill bit tracking"

    def handle(self, *args, **options):
        # Bit types organized by series
        bit_types = [
            # GT Series
            {"code": "GT53", "name": "GT53", "series": "GT"},
            {"code": "GT64DH", "name": "GT64DH", "series": "GT"},
            {"code": "GT65DH", "name": "GT65DH", "series": "GT"},
            {"code": "GT65RHS", "name": "GT65RHS", "series": "GT"},
            {"code": "GT65RHS-1", "name": "GT65RHS-1", "series": "GT"},
            {"code": "GT76H", "name": "GT76H", "series": "GT"},
            {"code": "GTD54H", "name": "GTD54H", "series": "GT"},
            {"code": "GTD55H", "name": "GTD55H", "series": "GT"},
            {"code": "GTi54H", "name": "GTi54H", "series": "GT"},
            {"code": "GTi64H", "name": "GTi64H", "series": "GT"},
            {"code": "GTi65H", "name": "GTi65H", "series": "GT"},
            {"code": "GTi76H", "name": "GTi76H", "series": "GT"},

            # HD Series
            {"code": "HD54", "name": "HD54", "series": "HD"},
            {"code": "HD54-2", "name": "HD54-2", "series": "HD"},
            {"code": "HD54-3", "name": "HD54-3", "series": "HD"},
            {"code": "HD54F", "name": "HD54F", "series": "HD"},
            {"code": "HD54O", "name": "HD54O", "series": "HD"},
            {"code": "HD54X", "name": "HD54X", "series": "HD"},
            {"code": "HD64", "name": "HD64", "series": "HD"},
            {"code": "HD64KHF", "name": "HD64KHF", "series": "HD"},
            {"code": "HD64KHO", "name": "HD64KHO", "series": "HD"},

            # MM Series
            {"code": "MM64", "name": "MM64", "series": "MM"},
            {"code": "MMD54H", "name": "MMD54H", "series": "MM"},
            {"code": "MMD63", "name": "MMD63", "series": "MM"},
            {"code": "MMD64", "name": "MMD64", "series": "MM"},
            {"code": "MMD64H", "name": "MMD64H", "series": "MM"},
            {"code": "MMD65H", "name": "MMD65H", "series": "MM"},
            {"code": "MMD76H", "name": "MMD76H", "series": "MM"},
            {"code": "MME63", "name": "MME63", "series": "MM"},
            {"code": "MMG64H", "name": "MMG64H", "series": "MM"},

            # FX Series
            {"code": "FX53", "name": "FX53", "series": "FX"},
            {"code": "FXD63", "name": "FXD63", "series": "FX"},
            {"code": "FXD65", "name": "FXD65", "series": "FX"},

            # FM Series
            {"code": "FM3651Z", "name": "FM3651Z", "series": "FM"},
            {"code": "FMD44", "name": "FMD44", "series": "FM"},

            # HXi Series
            {"code": "HXi54s", "name": "HXi54s", "series": "HXi"},
            {"code": "HXi65Dks", "name": "HXi65Dks", "series": "HXi"},

            # CS Series
            {"code": "CS54Os", "name": "CS54Os", "series": "CS"},
            {"code": "CS55RKOs", "name": "CS55RKOs", "series": "CS"},

            # SF Series
            {"code": "SF53", "name": "SF53", "series": "SF"},
            {"code": "SFD66CH", "name": "SFD66CH", "series": "SF"},
        ]

        created_count = 0
        updated_count = 0

        for type_data in bit_types:
            obj, created = BitType.objects.update_or_create(
                code=type_data["code"],
                defaults={
                    "name": type_data["name"],
                    "series": type_data["series"],
                    "is_active": True,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Bit Types: {created_count} created, {updated_count} updated. Total: {BitType.objects.count()}"
            )
        )
