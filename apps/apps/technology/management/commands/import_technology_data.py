"""
ARDT FMS - Import Technology Data Command
Imports Designs and BOMs from JSON backup file.

Usage:
    python manage.py import_technology_data backups/technology_data_20250102_120000.json
    python manage.py import_technology_data backups/tech_backup.json --force
"""

import json
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Import Designs and BOMs from JSON backup file"

    def add_arguments(self, parser):
        parser.add_argument(
            "input_file",
            type=str,
            help="Path to the JSON backup file"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing records (default: skip existing)"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without making changes"
        )

    def handle(self, *args, **options):
        from apps.technology.models import (
            Design, BOM, BOMLine, BitSize, UpperSectionType,
            ConnectionType, ConnectionSize, Connection, BreakerSlot,
            FormationType, Application, IADCCode, SpecialTechnology
        )
        from apps.inventory.models import InventoryItem

        input_path = Path(options["input_file"])
        force = options["force"]
        dry_run = options["dry_run"]

        if not input_path.exists():
            raise CommandError(f"File not found: {input_path}")

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Importing Technology Data ===\n"))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made\n"))

        # Load data
        with open(input_path) as f:
            data = json.load(f)

        self.stdout.write(f"   File exported at: {data.get('exported_at', 'Unknown')}")
        self.stdout.write(f"   Designs in file: {len(data.get('designs', []))}")
        self.stdout.write(f"   BOMs in file: {len(data.get('boms', []))}\n")

        # Cache for lookups
        size_cache = {s.code: s for s in BitSize.objects.all()}
        upper_section_cache = {u.code: u for u in UpperSectionType.objects.all()}
        connection_type_cache = {c.code: c for c in ConnectionType.objects.all()}
        connection_size_cache = {c.code: c for c in ConnectionSize.objects.all()}
        connection_cache = {c.mat_no: c for c in Connection.objects.all()}
        breaker_slot_cache = {b.mat_no: b for b in BreakerSlot.objects.all()}
        formation_cache = {f.code: f for f in FormationType.objects.all()}
        application_cache = {a.code: a for a in Application.objects.all()}
        iadc_cache = {i.code: i for i in IADCCode.objects.all()}
        special_tech_cache = {s.code: s for s in SpecialTechnology.objects.all()}
        inventory_cache = {}

        # Statistics
        stats = {
            "designs_created": 0,
            "designs_updated": 0,
            "designs_skipped": 0,
            "boms_created": 0,
            "boms_updated": 0,
            "boms_skipped": 0,
            "lines_created": 0,
        }

        with transaction.atomic():
            # Import Designs
            self.stdout.write("Importing Designs...")
            for design_data in data.get("designs", []):
                mat_no = design_data["mat_no"]
                existing = Design.objects.filter(mat_no=mat_no).first()

                if existing and not force:
                    stats["designs_skipped"] += 1
                    continue

                design_fields = {
                    "hdbs_type": design_data.get("hdbs_type", ""),
                    "smi_type": design_data.get("smi_type", ""),
                    "ref_mat_no": design_data.get("ref_mat_no", ""),
                    "ardt_item_no": design_data.get("ardt_item_no", ""),
                    "category": design_data.get("category", "FC"),
                    "series": design_data.get("series", ""),
                    "body_material": design_data.get("body_material", ""),
                    "no_of_blades": design_data.get("no_of_blades"),
                    "total_pockets_count": design_data.get("total_pockets_count"),
                    "pocket_rows_count": design_data.get("pocket_rows_count", 1),
                    "pocket_layout_number": design_data.get("pocket_layout_number", ""),
                    "cutter_size": design_data.get("cutter_size"),
                    "gage_length": Decimal(design_data["gage_length"]) if design_data.get("gage_length") else None,
                    "gage_relief": Decimal(design_data["gage_relief"]) if design_data.get("gage_relief") else None,
                    "erosion_sleeve": design_data.get("erosion_sleeve", False),
                    "nozzle_count": design_data.get("nozzle_count"),
                    "nozzle_bore_size": design_data.get("nozzle_bore_size", ""),
                    "nozzle_config": design_data.get("nozzle_config", ""),
                    "tfa": Decimal(design_data["tfa"]) if design_data.get("tfa") else None,
                    "port_count": design_data.get("port_count"),
                    "port_size": Decimal(design_data["port_size"]) if design_data.get("port_size") else None,
                    "connection_mat_no": design_data.get("connection_mat_no", ""),
                    "order_level": design_data.get("order_level", ""),
                    "status": design_data.get("status", "DRAFT"),
                    "revision": design_data.get("revision", ""),
                    "description": design_data.get("description", ""),
                    "notes": design_data.get("notes", ""),
                }

                # Resolve foreign keys
                if design_data.get("size_code"):
                    design_fields["size"] = size_cache.get(design_data["size_code"])
                if design_data.get("upper_section_type_code"):
                    design_fields["upper_section_type"] = upper_section_cache.get(design_data["upper_section_type_code"])
                if design_data.get("connection_type_ref_code"):
                    design_fields["connection_type_ref"] = connection_type_cache.get(design_data["connection_type_ref_code"])
                if design_data.get("connection_size_ref_code"):
                    design_fields["connection_size_ref"] = connection_size_cache.get(design_data["connection_size_ref_code"])
                if design_data.get("connection_ref_mat_no"):
                    design_fields["connection_ref"] = connection_cache.get(design_data["connection_ref_mat_no"])
                if design_data.get("breaker_slot_mat_no"):
                    design_fields["breaker_slot"] = breaker_slot_cache.get(design_data["breaker_slot_mat_no"])
                if design_data.get("formation_type_ref_code"):
                    design_fields["formation_type_ref"] = formation_cache.get(design_data["formation_type_ref_code"])
                if design_data.get("application_ref_code"):
                    design_fields["application_ref"] = application_cache.get(design_data["application_ref_code"])
                if design_data.get("iadc_code_ref_code"):
                    design_fields["iadc_code_ref"] = iadc_cache.get(design_data["iadc_code_ref_code"])

                if dry_run:
                    if existing:
                        stats["designs_updated"] += 1
                    else:
                        stats["designs_created"] += 1
                    continue

                if existing:
                    for key, value in design_fields.items():
                        setattr(existing, key, value)
                    existing.save()
                    design = existing
                    stats["designs_updated"] += 1
                else:
                    design = Design.objects.create(mat_no=mat_no, **design_fields)
                    stats["designs_created"] += 1

                # Handle M2M - Special Technologies
                if design_data.get("special_technology_codes"):
                    special_techs = [
                        special_tech_cache[code]
                        for code in design_data["special_technology_codes"]
                        if code in special_tech_cache
                    ]
                    design.special_technologies.set(special_techs)

            # Import BOMs
            self.stdout.write("Importing BOMs...")
            design_cache = {d.mat_no: d for d in Design.objects.all()}

            for bom_data in data.get("boms", []):
                code = bom_data["code"]
                design_mat_no = bom_data["design_mat_no"]

                design = design_cache.get(design_mat_no)
                if not design:
                    self.stdout.write(
                        self.style.WARNING(f"   Skipping BOM {code}: Design {design_mat_no} not found")
                    )
                    stats["boms_skipped"] += 1
                    continue

                existing = BOM.objects.filter(code=code).first()

                if existing and not force:
                    stats["boms_skipped"] += 1
                    continue

                bom_fields = {
                    "design": design,
                    "name": bom_data.get("name", ""),
                    "revision": bom_data.get("revision", "A"),
                    "status": bom_data.get("status", "DRAFT"),
                    "notes": bom_data.get("notes", ""),
                    "source_type": bom_data.get("source_type", "MANUAL"),
                    "source_mat_number": bom_data.get("source_mat_number", ""),
                    "source_sn_number": bom_data.get("source_sn_number", ""),
                    "source_revision_level": bom_data.get("source_revision_level", ""),
                    "source_software_version": bom_data.get("source_software_version", ""),
                }

                if bom_data.get("effective_date"):
                    bom_fields["effective_date"] = datetime.fromisoformat(bom_data["effective_date"]).date()

                if dry_run:
                    if existing:
                        stats["boms_updated"] += 1
                    else:
                        stats["boms_created"] += 1
                    stats["lines_created"] += len(bom_data.get("lines", []))
                    continue

                if existing:
                    for key, value in bom_fields.items():
                        setattr(existing, key, value)
                    existing.save()
                    bom = existing
                    # Clear existing lines before reimporting
                    bom.lines.all().delete()
                    stats["boms_updated"] += 1
                else:
                    bom = BOM.objects.create(code=code, **bom_fields)
                    stats["boms_created"] += 1

                # Import BOM Lines
                for line_data in bom_data.get("lines", []):
                    inventory_item = None
                    if line_data.get("inventory_item_code"):
                        if line_data["inventory_item_code"] not in inventory_cache:
                            inventory_cache[line_data["inventory_item_code"]] = InventoryItem.objects.filter(
                                code=line_data["inventory_item_code"]
                            ).first()
                        inventory_item = inventory_cache[line_data["inventory_item_code"]]

                    BOMLine.objects.create(
                        bom=bom,
                        line_number=line_data["line_number"],
                        inventory_item=inventory_item,
                        quantity=line_data.get("quantity", 1),
                        unit=line_data.get("unit", "EA"),
                        order_number=line_data.get("order_number", 1),
                        color_code=line_data.get("color_code", "#4A4A4A"),
                        cutter_size=line_data.get("cutter_size", ""),
                        cutter_chamfer=line_data.get("cutter_chamfer", ""),
                        cutter_type=line_data.get("cutter_type", ""),
                        hdbs_code=line_data.get("hdbs_code", ""),
                        family_number=line_data.get("family_number", ""),
                        unit_cost=Decimal(line_data.get("unit_cost", "0")),
                        position=line_data.get("position", ""),
                        is_optional=line_data.get("is_optional", False),
                        is_phantom=line_data.get("is_phantom", False),
                        notes=line_data.get("notes", ""),
                    )
                    stats["lines_created"] += 1

            if dry_run:
                # Rollback in dry run
                transaction.set_rollback(True)

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.MIGRATE_HEADING("  IMPORT SUMMARY"))
        self.stdout.write("=" * 50)
        self.stdout.write(f"  Designs created: {stats['designs_created']}")
        self.stdout.write(f"  Designs updated: {stats['designs_updated']}")
        self.stdout.write(f"  Designs skipped: {stats['designs_skipped']}")
        self.stdout.write(f"  BOMs created: {stats['boms_created']}")
        self.stdout.write(f"  BOMs updated: {stats['boms_updated']}")
        self.stdout.write(f"  BOMs skipped: {stats['boms_skipped']}")
        self.stdout.write(f"  BOM lines created: {stats['lines_created']}")
        self.stdout.write("=" * 50)

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN - No changes were made"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ Import completed successfully!\n"))
