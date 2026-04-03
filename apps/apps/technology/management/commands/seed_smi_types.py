"""
ARDT FMS - Seed SMI Types Command
Creates sample SMI (client-facing) types linked to HDBS types.

Usage: python manage.py seed_smi_types

Note: Run seed_hdbs_types first to create the HDBS types.
"""

from django.core.management.base import BaseCommand
from apps.technology.models import BitSize, HDBSType, SMIType


class Command(BaseCommand):
    help = "Seed SMI Types (client-facing naming linked to HDBS)"

    # SMI types follow pattern: hdbs_name variations per size
    # Format: (hdbs_name, smi_name, size_display, description)
    SMI_TYPES = [
        # GT65RHS variants
        ("GT65RHS", "GT65RHS-85", "8 1/2\"", "GT65RHS for 8.5\" hole sections"),
        ("GT65RHS", "GT65RHS-122", "12 1/4\"", "GT65RHS for 12.25\" hole sections"),
        ("GT65RHS", "GT65RHS-175", "17 1/2\"", "GT65RHS for 17.5\" surface sections"),
        # FM2565 variants
        ("FM2565", "FM2565A", "6\"", "Fast-drill 6\" variant A"),
        ("FM2565", "FM2565B", "8 1/2\"", "Fast-drill 8.5\" variant B"),
        ("FM2565", "FM2565C", "12 1/4\"", "Fast-drill 12.25\" variant C"),
        # HM3575 variants
        ("HM3575", "HM3575-A", "6\"", "Hard formation 6\" standard"),
        ("HM3575", "HM3575-B", "8 1/2\"", "Hard formation 8.5\" standard"),
        ("HM3575", "HM3575-C", "12 1/4\"", "Hard formation 12.25\" standard"),
        ("HM3575", "HM3575-D", "17 1/2\"", "Hard formation 17.5\" surface"),
        # FX3665 variants
        ("FX3665", "FX3665X", "8 1/2\"", "Extended durability 8.5\""),
        ("FX3665", "FX3665Y", "12 1/4\"", "Extended durability 12.25\""),
        # GS4575 variants
        ("GS4575", "GS4575-S1", "6\"", "Shale 6\" type 1"),
        ("GS4575", "GS4575-S2", "8 1/2\"", "Shale 8.5\" type 2"),
        ("GS4575", "GS4575-S3", "12 1/4\"", "Shale 12.25\" type 3"),
        ("GS4575", "GS4575-S4", "17 1/2\"", "Shale 17.5\" type 4"),
        # HS5575 variants
        ("HS5575", "HS5575-FAST", "8 1/2\"", "High-speed 8.5\" fast drill"),
        ("HS5575", "HS5575-XFAST", "12 1/4\"", "High-speed 12.25\" extra fast"),
        # MS6585 variants
        ("MS6585", "MS6585-INT", "8 1/2\"", "Interbedded 8.5\" standard"),
        ("MS6585", "MS6585-INT2", "12 1/4\"", "Interbedded 12.25\" enhanced"),
        ("MS6585", "MS6585-INT3", "17 1/2\"", "Interbedded 17.5\" surface"),
        # XS7595 variants
        ("XS7595", "XS7595-HD", "6\"", "Extra-strength 6\" heavy duty"),
        ("XS7595", "XS7595-XHD", "8 1/2\"", "Extra-strength 8.5\" extra heavy"),
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update of existing SMI types",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding SMI Types ===\n"))

        force = options.get("force", False)
        created_count = 0
        updated_count = 0
        skipped_count = 0
        errors = 0

        # Build lookup maps
        hdbs_map = {h.hdbs_name: h for h in HDBSType.objects.all()}
        size_map = {s.size_display: s for s in BitSize.objects.all()}

        if not hdbs_map:
            self.stdout.write(
                self.style.ERROR("No HDBS Types found. Run seed_hdbs_types first!")
            )
            return

        for hdbs_name, smi_name, size_display, description in self.SMI_TYPES:
            try:
                hdbs = hdbs_map.get(hdbs_name)
                size = size_map.get(size_display)

                if not hdbs:
                    self.stdout.write(
                        self.style.WARNING(f"  ! HDBS '{hdbs_name}' not found, skipping {smi_name}")
                    )
                    errors += 1
                    continue

                if not size:
                    self.stdout.write(
                        self.style.WARNING(f"  ! Size '{size_display}' not found, skipping {smi_name}")
                    )
                    errors += 1
                    continue

                smi, created = SMIType.objects.get_or_create(
                    smi_name=smi_name,
                    hdbs_type=hdbs,
                    size=size,
                    defaults={"description": description},
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  + Created: {smi_name} ({hdbs_name}, {size_display})")
                    )
                elif force:
                    smi.description = description
                    smi.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  ~ Updated: {smi_name}")
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.NOTICE(f"  - Skipped (exists): {smi_name}")
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  x Error creating {smi_name}: {str(e)}")
                )
                errors += 1

        # Summary
        self.stdout.write("\n" + "-" * 50)
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.WARNING(f"  Updated: {updated_count}"))
        self.stdout.write(f"  Skipped: {skipped_count}")
        if errors:
            self.stdout.write(self.style.ERROR(f"  Errors: {errors}"))
        self.stdout.write("-" * 50)

        self.stdout.write(self.style.SUCCESS("\nSMI Types seeding complete!\n"))
