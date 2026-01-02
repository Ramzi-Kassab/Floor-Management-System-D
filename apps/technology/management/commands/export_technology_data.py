"""
ARDT FMS - Export Technology Data Command
Exports Designs and BOMs to JSON file for backup/restore.

Usage:
    python manage.py export_technology_data
    python manage.py export_technology_data --output backups/tech_backup.json
"""

import json
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder


class Command(BaseCommand):
    help = "Export Designs and BOMs to JSON file for backup"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            "-o",
            type=str,
            default=None,
            help="Output file path (default: backups/technology_data_YYYYMMDD_HHMMSS.json)"
        )

    def handle(self, *args, **options):
        from apps.technology.models import Design, BOM, BOMLine

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Exporting Technology Data ===\n"))

        # Prepare output path
        if options["output"]:
            output_path = Path(options["output"])
        else:
            # Use data/ folder which is NOT in .gitignore (persists across container rebuilds)
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = data_dir / f"technology_data_{timestamp}.json"
            # Also create a "latest" symlink for easy import
            latest_path = data_dir / "technology_data_latest.json"

        # Collect data
        data = {
            "exported_at": datetime.now().isoformat(),
            "designs": [],
            "boms": [],
        }

        # Export Designs
        designs = Design.objects.select_related(
            "size", "upper_section_type", "connection_type_ref",
            "connection_size_ref", "connection_ref", "breaker_slot",
            "formation_type_ref", "application_ref", "iadc_code_ref"
        ).prefetch_related("special_technologies")

        for design in designs:
            design_data = {
                "mat_no": design.mat_no,
                "hdbs_type": design.hdbs_type,
                "smi_type": design.smi_type,
                "ref_mat_no": design.ref_mat_no,
                "ardt_item_no": design.ardt_item_no,
                "category": design.category,
                "size_code": design.size.code if design.size else None,
                "series": design.series,
                "body_material": design.body_material,
                "no_of_blades": design.no_of_blades,
                "total_pockets_count": design.total_pockets_count,
                "pocket_rows_count": design.pocket_rows_count,
                "pocket_layout_number": design.pocket_layout_number,
                "cutter_size": design.cutter_size,
                "gage_length": str(design.gage_length) if design.gage_length else None,
                "gage_relief": str(design.gage_relief) if design.gage_relief else None,
                "erosion_sleeve": design.erosion_sleeve,
                "nozzle_count": design.nozzle_count,
                "nozzle_bore_size": design.nozzle_bore_size,
                "nozzle_config": design.nozzle_config,
                "tfa": str(design.tfa) if design.tfa else None,
                "port_count": design.port_count,
                "port_size": str(design.port_size) if design.port_size else None,
                "connection_mat_no": design.connection_mat_no,
                "upper_section_type_code": design.upper_section_type.code if design.upper_section_type else None,
                "connection_type_ref_code": design.connection_type_ref.code if design.connection_type_ref else None,
                "connection_size_ref_code": design.connection_size_ref.code if design.connection_size_ref else None,
                "connection_ref_mat_no": design.connection_ref.mat_no if design.connection_ref else None,
                "breaker_slot_mat_no": design.breaker_slot.mat_no if design.breaker_slot else None,
                "formation_type_ref_code": design.formation_type_ref.code if design.formation_type_ref else None,
                "application_ref_code": design.application_ref.code if design.application_ref else None,
                "iadc_code_ref_code": design.iadc_code_ref.code if design.iadc_code_ref else None,
                "special_technology_codes": [st.code for st in design.special_technologies.all()],
                "order_level": design.order_level,
                "status": design.status,
                "revision": design.revision,
                "description": design.description,
                "notes": design.notes,
            }
            data["designs"].append(design_data)

        self.stdout.write(f"   - Exported {len(data['designs'])} designs")

        # Export BOMs and BOMLines
        boms = BOM.objects.select_related("design").prefetch_related("lines__inventory_item")

        for bom in boms:
            bom_data = {
                "design_mat_no": bom.design.mat_no,
                "code": bom.code,
                "name": bom.name,
                "revision": bom.revision,
                "status": bom.status,
                "effective_date": bom.effective_date.isoformat() if bom.effective_date else None,
                "notes": bom.notes,
                "source_type": bom.source_type,
                "source_mat_number": bom.source_mat_number,
                "source_sn_number": bom.source_sn_number,
                "source_revision_level": bom.source_revision_level,
                "source_software_version": bom.source_software_version,
                "lines": [],
            }

            for line in bom.lines.all():
                line_data = {
                    "line_number": line.line_number,
                    "inventory_item_code": line.inventory_item.code if line.inventory_item else None,
                    "quantity": line.quantity,
                    "unit": line.unit,
                    "order_number": line.order_number,
                    "color_code": line.color_code,
                    "cutter_size": line.cutter_size,
                    "cutter_chamfer": line.cutter_chamfer,
                    "cutter_type": line.cutter_type,
                    "hdbs_code": line.hdbs_code,
                    "family_number": line.family_number,
                    "unit_cost": str(line.unit_cost),
                    "position": line.position,
                    "is_optional": line.is_optional,
                    "is_phantom": line.is_phantom,
                    "notes": line.notes,
                }
                bom_data["lines"].append(line_data)

            data["boms"].append(bom_data)

        self.stdout.write(f"   - Exported {len(data['boms'])} BOMs")
        total_lines = sum(len(bom["lines"]) for bom in data["boms"])
        self.stdout.write(f"   - Exported {total_lines} BOM lines")

        # Write to file
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, cls=DjangoJSONEncoder)

        # Also write to "latest" file for easy auto-import
        if not options["output"]:
            import shutil
            shutil.copy(output_path, latest_path)
            self.stdout.write(f"   - Also saved to: {latest_path}")

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Data exported to: {output_path}\n")
        )
        self.stdout.write(
            self.style.WARNING(
                "NOTE: File attachments (PDFs, drawings) are NOT exported.\n"
                "      Only database records are backed up.\n"
            )
        )
        self.stdout.write(
            self.style.NOTICE(
                "TIP: To restore after container rebuild, run:\n"
                "     python manage.py import_technology_data data/technology_data_latest.json\n"
            )
        )
