"""
ARDT FMS - Seed Positions Command
Creates all 54 real ARDT positions from QAS-105 Rev R

Usage: python manage.py seed_positions
"""

from django.core.management.base import BaseCommand
from apps.organization.models import Department, Position


class Command(BaseCommand):
    help = "Seed all 54 real ARDT positions from QAS-105"

    # All 54 positions from QAS-105 Rev R organized by department
    # Level: 1=Executive, 2=Manager, 3=Supervisor/Coordinator, 4=Specialist, 5=Technician/Staff, 6=General
    POSITIONS = [
        # ============ EXECUTIVE ============
        {"code": "GM", "title": "General Manager", "department_code": "EXEC", "level": 1, "reports_to": "Board of Directors"},

        # ============ TECHNOLOGY ============
        {"code": "TM", "title": "Technology Manager", "department_code": "TECH", "level": 2, "reports_to": "GM"},
        {"code": "ADE", "title": "Application Design Engineer", "department_code": "TECH", "level": 4, "reports_to": "TM"},
        {"code": "AE", "title": "Application Engineer", "department_code": "TECH", "level": 4, "reports_to": "TM"},

        # ============ SALES ============
        {"code": "SM", "title": "Sales Manager", "department_code": "SALES", "level": 2, "reports_to": "GM"},
        {"code": "SAL", "title": "Sales Account Lead", "department_code": "SALES", "level": 3, "reports_to": "SM"},
        {"code": "SAR", "title": "Sales Accounts Rep", "department_code": "SALES", "level": 4, "reports_to": "SM"},
        {"code": "FOC", "title": "Field Operation Coordinator", "department_code": "SALES", "level": 3, "reports_to": "SM"},
        {"code": "FOS", "title": "Field Operation Specialist", "department_code": "SALES", "level": 4, "reports_to": "FOC"},
        {"code": "DBO", "title": "Database Operator", "department_code": "SALES", "level": 4, "reports_to": "SM"},

        # ============ OPERATIONS ============
        {"code": "OPM", "title": "Operations Manager", "department_code": "OPS", "level": 2, "reports_to": "GM"},
        {"code": "MFS", "title": "Manufacturing Supervisor", "department_code": "OPS", "level": 3, "reports_to": "OPM"},
        {"code": "WLD", "title": "Welder", "department_code": "OPS", "level": 5, "reports_to": "MFS"},
        {"code": "MCH", "title": "Machinist", "department_code": "OPS", "level": 5, "reports_to": "MFS"},
        {"code": "FLT", "title": "Floor Technician", "department_code": "OPS", "level": 5, "reports_to": "MFS"},
        {"code": "CRP", "title": "Carpenter", "department_code": "OPS", "level": 5, "reports_to": "MFS"},
        {"code": "MNT", "title": "Maintenance Man", "department_code": "OPS", "level": 5, "reports_to": "MFS"},
        {"code": "RPS", "title": "Repair Supervisor", "department_code": "OPS", "level": 3, "reports_to": "OPM"},
        {"code": "RPC", "title": "Repair Coordinator", "department_code": "OPS", "level": 4, "reports_to": "RPS"},
        {"code": "RPT", "title": "Repair Technician", "department_code": "OPS", "level": 5, "reports_to": "RPS"},

        # ============ QUALITY ============
        {"code": "QM", "title": "Quality Manager", "department_code": "QC", "level": 2, "reports_to": "GM"},
        {"code": "QCC", "title": "Quality Control Coordinator", "department_code": "QC", "level": 3, "reports_to": "QM"},
        {"code": "FNI", "title": "Final Inspector", "department_code": "QC", "level": 4, "reports_to": "QCC"},
        {"code": "QCI", "title": "QC Inspector", "department_code": "QC", "level": 4, "reports_to": "QCC"},
        {"code": "QAC", "title": "Quality Assurance Coordinator", "department_code": "QC", "level": 3, "reports_to": "QM"},
        {"code": "DOC", "title": "Document Controller", "department_code": "QC", "level": 4, "reports_to": "QAC"},

        # ============ PROCUREMENT & LOGISTICS ============
        {"code": "PLM", "title": "Procurement & Logistics Manager", "department_code": "PROC", "level": 2, "reports_to": "GM"},
        {"code": "APL", "title": "Assistant Procurement & Logistics Manager", "department_code": "PROC", "level": 3, "reports_to": "PLM"},
        {"code": "LGC", "title": "Logistics Coordinator", "department_code": "PROC", "level": 4, "reports_to": "PLM"},
        {"code": "DSP", "title": "Dispatch Inspector", "department_code": "PROC", "level": 4, "reports_to": "PLM"},
        {"code": "DRV", "title": "Driver", "department_code": "PROC", "level": 5, "reports_to": "PLM"},
        {"code": "OPC", "title": "Operations Coordinator", "department_code": "PROC", "level": 4, "reports_to": "PLM"},
        {"code": "AOC", "title": "Assistant Operations Coordinator", "department_code": "PROC", "level": 4, "reports_to": "PLM"},
        {"code": "STK", "title": "Storekeeper", "department_code": "PROC", "level": 5, "reports_to": "PLM"},
        {"code": "PRS", "title": "Procurement Supervisor", "department_code": "PROC", "level": 3, "reports_to": "PLM"},
        {"code": "PRC", "title": "Procurement Specialist", "department_code": "PROC", "level": 4, "reports_to": "PRS"},

        # ============ FINANCE ============
        {"code": "FC", "title": "Finance Controller", "department_code": "FIN", "level": 2, "reports_to": "GM"},
        {"code": "CAC", "title": "Chief Accountant", "department_code": "FIN", "level": 3, "reports_to": "FC"},
        {"code": "SAC", "title": "Senior Accountant", "department_code": "FIN", "level": 4, "reports_to": "FC"},
        {"code": "ACC", "title": "Accountant", "department_code": "FIN", "level": 4, "reports_to": "SAC"},
        {"code": "ACK", "title": "Accounts Clerk", "department_code": "FIN", "level": 5, "reports_to": "ACC"},

        # ============ HR & ADMINISTRATION ============
        {"code": "HRM", "title": "HR & Administration Manager", "department_code": "HR", "level": 2, "reports_to": "GM"},
        {"code": "HRS", "title": "HR Supervisor", "department_code": "HR", "level": 3, "reports_to": "HRM"},
        {"code": "HRC", "title": "HR Coordinator", "department_code": "HR", "level": 4, "reports_to": "HRS"},
        {"code": "ADS", "title": "Admin Supervisor", "department_code": "HR", "level": 3, "reports_to": "HRM"},
        {"code": "ADC", "title": "Admin Coordinator", "department_code": "HR", "level": 4, "reports_to": "ADS"},

        # ============ IT ============
        {"code": "ITM", "title": "IT & ERP Manager", "department_code": "IT", "level": 2, "reports_to": "GM"},
        {"code": "ITC", "title": "IT Control Engineer", "department_code": "IT", "level": 4, "reports_to": "ITM"},
        {"code": "PRE", "title": "Production Encoder", "department_code": "IT", "level": 4, "reports_to": "ITM"},

        # ============ HSSE ============
        {"code": "HSM", "title": "HSSE Manager", "department_code": "HSSE", "level": 2, "reports_to": "GM"},
        {"code": "HSS", "title": "HSE Supervisor", "department_code": "HSSE", "level": 3, "reports_to": "HSM"},

        # ============ GENERAL/SUPPORT ============
        {"code": "GWK", "title": "General Worker", "department_code": "OPS", "level": 6, "reports_to": "Supervisors"},
        {"code": "GRD", "title": "Guard", "department_code": "HSSE", "level": 6, "reports_to": "HSS"},
        {"code": "OFB", "title": "Office Boy", "department_code": "HR", "level": 6, "reports_to": "ADS"},
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update of existing positions",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding ARDT Positions (QAS-105 - 54 Total) ===\n"))

        force = options.get("force", False)
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        # Cache departments
        departments = {d.code: d for d in Department.objects.all()}

        for pos_data in self.POSITIONS:
            code = pos_data["code"]
            dept_code = pos_data.pop("department_code")
            reports_to = pos_data.pop("reports_to", "")

            try:
                # Get department
                department = departments.get(dept_code)
                if not department:
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ Department not found: {dept_code} for position {code}")
                    )
                    error_count += 1
                    pos_data["department_code"] = dept_code
                    pos_data["reports_to"] = reports_to
                    continue

                # Add description with reports_to info
                pos_data["description"] = f"Reports to: {reports_to}"
                pos_data["department"] = department

                position, created = Position.objects.get_or_create(
                    code=code,
                    defaults=pos_data,
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Created: {code} - {position.title} ({dept_code})")
                    )
                elif force:
                    for key, value in pos_data.items():
                        setattr(position, key, value)
                    position.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  ↻ Updated: {code} - {position.title}")
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.NOTICE(f"  - Skipped (exists): {code}")
                    )

                # Restore for reference
                pos_data["department_code"] = dept_code
                pos_data["reports_to"] = reports_to
                if "department" in pos_data:
                    del pos_data["department"]

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error creating {code}: {str(e)}")
                )
                error_count += 1
                pos_data["department_code"] = dept_code
                pos_data["reports_to"] = reports_to
                if "department" in pos_data:
                    del pos_data["department"]

        # Summary
        self.stdout.write("\n" + "-" * 50)
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.WARNING(f"  Updated: {updated_count}"))
        self.stdout.write(f"  Skipped: {skipped_count}")
        if error_count:
            self.stdout.write(self.style.ERROR(f"  Errors: {error_count}"))
        self.stdout.write("-" * 50)

        # Position count by department
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Positions by Department ===\n"))
        dept_counts = {}
        for pos in self.POSITIONS:
            dept = pos.get("department_code", "Unknown")
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        for dept, count in sorted(dept_counts.items()):
            self.stdout.write(f"  {dept:<8}: {count} positions")

        self.stdout.write(f"\n  Total: {len(self.POSITIONS)} positions")
        self.stdout.write(self.style.SUCCESS("\n✓ Position seeding complete!\n"))
