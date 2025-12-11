"""
ARDT FMS - Seed Positions Command
Creates real ARDT job positions from company structure

Usage: python manage.py seed_positions
"""

from django.core.management.base import BaseCommand
from apps.organization.models import Department, Position


class Command(BaseCommand):
    help = "Seed real ARDT positions from company structure"

    # Real ARDT Positions from MASTER_PLAN.md
    # Level: 1=Executive, 2=Manager, 3=Supervisor, 4=Staff
    POSITIONS = [
        # Executive Management
        {
            "code": "GM",
            "title": "General Manager",
            "title_ar": "المدير العام",
            "department_code": "EXEC",
            "level": 1,
            "description": "Overall company leadership and strategic direction",
        },
        # Production
        {
            "code": "PROD-MGR",
            "title": "Production Manager",
            "title_ar": "مدير الإنتاج",
            "department_code": "PROD",
            "level": 2,
            "description": "Manages all production operations",
        },
        {
            "code": "PROD-SUP",
            "title": "Production Supervisor",
            "title_ar": "مشرف الإنتاج",
            "department_code": "PROD",
            "level": 3,
            "description": "Supervises production floor operations",
        },
        {
            "code": "PROD-TECH",
            "title": "Production Technician",
            "title_ar": "فني الإنتاج",
            "department_code": "PROD",
            "level": 4,
            "description": "Operates production equipment and processes",
        },
        # Quality Control
        {
            "code": "QC-MGR",
            "title": "QC Manager",
            "title_ar": "مدير مراقبة الجودة",
            "department_code": "QC",
            "level": 2,
            "description": "Manages quality control department",
        },
        {
            "code": "QC-INSP",
            "title": "QC Inspector",
            "title_ar": "مفتش الجودة",
            "department_code": "QC",
            "level": 4,
            "description": "Performs quality inspections and tests",
        },
        # Technical/Engineering
        {
            "code": "TECH-ENG",
            "title": "Design Engineer",
            "title_ar": "مهندس التصميم",
            "department_code": "TECH",
            "level": 3,
            "description": "Designs drill bits and components",
        },
        # Sales
        {
            "code": "SALES-MGR",
            "title": "Sales Manager",
            "title_ar": "مدير المبيعات",
            "department_code": "SALES",
            "level": 2,
            "description": "Manages sales and customer relationships",
        },
        # Logistics
        {
            "code": "LOG-MGR",
            "title": "Logistics Manager",
            "title_ar": "مدير اللوجستيات",
            "department_code": "LOG",
            "level": 2,
            "description": "Manages warehouse and supply chain operations",
        },
        # Field Operations
        {
            "code": "FIELD-MGR",
            "title": "Field Manager",
            "title_ar": "مدير العمليات الميدانية",
            "department_code": "FIELD",
            "level": 2,
            "description": "Manages all field operations and rig site activities",
        },
        {
            "code": "FIELD-FOR",
            "title": "Field Foreman",
            "title_ar": "ملاحظ ميداني",
            "department_code": "FIELD",
            "level": 3,
            "description": "Supervises field crews at rig sites",
        },
        {
            "code": "FIELD-ENG",
            "title": "Field Engineer",
            "title_ar": "مهندس ميداني",
            "department_code": "FIELD",
            "level": 3,
            "description": "Provides technical support at rig sites",
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update of existing positions",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding ARDT Positions ===\n"))

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

            # Get department
            department = departments.get(dept_code)
            if not department:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ Department {dept_code} not found for position {code}")
                )
                error_count += 1
                pos_data["department_code"] = dept_code  # restore
                continue

            pos_data["department"] = department

            try:
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
                    # Update existing position
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

                # Restore department_code for reference
                pos_data["department_code"] = dept_code
                del pos_data["department"]

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error creating {code}: {str(e)}")
                )
                error_count += 1
                pos_data["department_code"] = dept_code
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

        # Position hierarchy
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Position Hierarchy ===\n"))
        self.stdout.write("  Level | Code        | Title                        | Department")
        self.stdout.write("  " + "-" * 75)

        level_names = {1: "Executive", 2: "Manager", 3: "Supervisor", 4: "Staff"}
        for pos in sorted(self.POSITIONS, key=lambda x: (x["level"], x["code"])):
            level = pos["level"]
            level_str = f"L{level}"
            self.stdout.write(
                f"  {level_str:<5} | {pos['code']:<11} | {pos['title']:<28} | {pos['department_code']}"
            )

        self.stdout.write(self.style.SUCCESS("\n✓ Position seeding complete!\n"))
