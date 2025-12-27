"""
ARDT FMS - Seed HDBS Types Command
Creates sample HDBS (Halliburton Drill Bit System) types.

Usage: python manage.py seed_hdbs_types
"""

from django.core.management.base import BaseCommand
from apps.technology.models import BitSize, HDBSType


class Command(BaseCommand):
    help = "Seed HDBS Types (internal Halliburton naming)"

    # Sample HDBS types with size compatibility
    HDBS_TYPES = [
        {
            "hdbs_name": "GT65RHS",
            "description": "General purpose PDC for medium formations",
            "sizes": ["8 1/2\"", "12 1/4\"", "17 1/2\""],
        },
        {
            "hdbs_name": "FM2565",
            "description": "Fast drilling in soft formations",
            "sizes": ["6\"", "8 1/2\"", "12 1/4\""],
        },
        {
            "hdbs_name": "HM3575",
            "description": "Hard formation medium-speed",
            "sizes": ["6\"", "8 1/2\"", "12 1/4\"", "17 1/2\""],
        },
        {
            "hdbs_name": "FX3665",
            "description": "Extended durability for abrasive formations",
            "sizes": ["8 1/2\"", "12 1/4\""],
        },
        {
            "hdbs_name": "GS4575",
            "description": "General shale drilling",
            "sizes": ["6\"", "8 1/2\"", "12 1/4\"", "17 1/2\""],
        },
        {
            "hdbs_name": "HS5575",
            "description": "High-speed soft formation",
            "sizes": ["8 1/2\"", "12 1/4\""],
        },
        {
            "hdbs_name": "MS6585",
            "description": "Medium-speed for interbedded formations",
            "sizes": ["8 1/2\"", "12 1/4\"", "17 1/2\""],
        },
        {
            "hdbs_name": "XS7595",
            "description": "Extra-strength hard formation",
            "sizes": ["6\"", "8 1/2\""],
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update of existing HDBS types",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding HDBS Types ===\n"))

        force = options.get("force", False)
        created_count = 0
        updated_count = 0
        skipped_count = 0

        # Get all available sizes for lookup
        size_map = {s.size_display: s for s in BitSize.objects.all()}
        available_sizes = list(size_map.keys())
        self.stdout.write(f"Available sizes: {available_sizes}\n")

        for hdbs_data in self.HDBS_TYPES:
            name = hdbs_data["hdbs_name"]

            try:
                hdbs, created = HDBSType.objects.get_or_create(
                    hdbs_name=name,
                    defaults={"description": hdbs_data["description"]},
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  + Created: {name}")
                    )
                elif force:
                    hdbs.description = hdbs_data["description"]
                    hdbs.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  ~ Updated: {name}")
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.NOTICE(f"  - Skipped (exists): {name}")
                    )

                # Assign sizes
                for size_display in hdbs_data["sizes"]:
                    if size_display in size_map:
                        hdbs.sizes.add(size_map[size_display])
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"    Size not found: {size_display}")
                        )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  x Error creating {name}: {str(e)}")
                )

        # Summary
        self.stdout.write("\n" + "-" * 50)
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.WARNING(f"  Updated: {updated_count}"))
        self.stdout.write(f"  Skipped: {skipped_count}")
        self.stdout.write("-" * 50)

        self.stdout.write(self.style.SUCCESS("\nHDBS Types seeding complete!\n"))
