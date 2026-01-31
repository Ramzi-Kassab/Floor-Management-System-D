"""
ARDT FMS - Sync HDBS Types from Existing Designs

Scans all Design records that have an hdbs_type text value and ensures:
1. A matching HDBSType record exists (created if missing)
2. The design's size is linked to the HDBSType.sizes M2M
3. A DesignHDBS junction record exists linking Design -> HDBSType

Usage:
    python manage.py sync_hdbs_from_designs          # Dry run (preview)
    python manage.py sync_hdbs_from_designs --confirm # Execute changes
"""

from django.core.management.base import BaseCommand
from apps.technology.models import Design, HDBSType, DesignHDBS


class Command(BaseCommand):
    help = "Create missing HDBSType records from Design.hdbs_type text values and link sizes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Actually execute changes (default is dry run)",
        )

    def handle(self, *args, **options):
        confirm = options.get("confirm", False)
        mode = "EXECUTE" if confirm else "DRY RUN"
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n=== Sync HDBS Types from Designs ({mode}) ===\n"
        ))

        # Get all designs with a non-empty hdbs_type
        designs = Design.objects.filter(
            hdbs_type__isnull=False
        ).exclude(hdbs_type='').select_related('size')

        self.stdout.write(f"Found {designs.count()} designs with HDBS type values\n")

        # Collect unique hdbs_type -> set of sizes
        hdbs_map = {}  # hdbs_name -> { 'sizes': set of BitSize, 'designs': list of Design }
        for d in designs:
            name = d.hdbs_type.strip()
            if not name:
                continue
            if name not in hdbs_map:
                hdbs_map[name] = {'sizes': set(), 'designs': []}
            if d.size:
                hdbs_map[name]['sizes'].add(d.size)
            hdbs_map[name]['designs'].append(d)

        self.stdout.write(f"Found {len(hdbs_map)} unique HDBS type names\n")

        # Check which already exist
        existing = {h.hdbs_name: h for h in HDBSType.objects.all()}
        existing_junctions = set(
            DesignHDBS.objects.filter(is_current=True).values_list('design_id', 'hdbs_type_id')
        )

        hdbs_created = 0
        sizes_linked = 0
        junctions_created = 0
        already_ok = 0

        for hdbs_name, data in sorted(hdbs_map.items()):
            sizes = data['sizes']
            design_list = data['designs']

            if hdbs_name in existing:
                hdbs_obj = existing[hdbs_name]
                # Check if we need to add sizes
                current_sizes = set(hdbs_obj.sizes.all())
                missing_sizes = sizes - current_sizes
                if missing_sizes:
                    for sz in missing_sizes:
                        self.stdout.write(
                            self.style.WARNING(f"  ~ Link size {sz.size_display} to {hdbs_name}")
                        )
                        if confirm:
                            hdbs_obj.sizes.add(sz)
                        sizes_linked += 1
                else:
                    already_ok += 1
            else:
                # Create new HDBSType
                self.stdout.write(
                    self.style.SUCCESS(f"  + Create HDBSType: {hdbs_name} "
                                       f"(sizes: {', '.join(s.size_display for s in sizes) or 'none'}, "
                                       f"{len(design_list)} design(s))")
                )
                if confirm:
                    hdbs_obj = HDBSType.objects.create(
                        hdbs_name=hdbs_name,
                        description=f"Auto-created from design import",
                        is_active=True,
                    )
                    for sz in sizes:
                        hdbs_obj.sizes.add(sz)
                    existing[hdbs_name] = hdbs_obj
                hdbs_created += 1
                sizes_linked += len(sizes)

            # Create DesignHDBS junction records
            if confirm:
                hdbs_obj = existing.get(hdbs_name)
            for design in design_list:
                if confirm and hdbs_obj:
                    key = (design.pk, hdbs_obj.pk)
                    if key not in existing_junctions:
                        DesignHDBS.objects.get_or_create(
                            design=design,
                            hdbs_type=hdbs_obj,
                            defaults={'is_current': True},
                        )
                        junctions_created += 1
                        existing_junctions.add(key)
                elif not confirm:
                    # In dry run, just count
                    junctions_created += 1

        # Summary
        self.stdout.write("\n" + "-" * 50)
        self.stdout.write(self.style.SUCCESS(f"  HDBSType records to create:  {hdbs_created}"))
        self.stdout.write(self.style.WARNING(f"  Size links to add:           {sizes_linked}"))
        self.stdout.write(f"  DesignHDBS junctions to add: {junctions_created}")
        self.stdout.write(f"  Already complete:            {already_ok}")
        self.stdout.write("-" * 50)

        if not confirm:
            self.stdout.write(self.style.NOTICE(
                "\nThis was a DRY RUN. Run with --confirm to execute.\n"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "\nSync complete!\n"
            ))
