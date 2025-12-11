"""
ARDT FMS - Seed Departments Command
Creates real ARDT departments from company structure

Usage: python manage.py seed_departments
"""

from django.core.management.base import BaseCommand
from apps.organization.models import Department


class Command(BaseCommand):
    help = "Seed real ARDT departments from company structure"

    # Real ARDT Departments from MASTER_PLAN.md
    DEPARTMENTS = [
        {
            "code": "EXEC",
            "name": "Executive Management",
            "name_ar": "الإدارة التنفيذية",
            "location": "Head Office - Al Khobar",
        },
        {
            "code": "PROD",
            "name": "Production",
            "name_ar": "الإنتاج",
            "location": "Factory Floor",
        },
        {
            "code": "QC",
            "name": "Quality Control",
            "name_ar": "مراقبة الجودة",
            "location": "QC Lab",
        },
        {
            "code": "TECH",
            "name": "Technical/Engineering",
            "name_ar": "الهندسة والتقنية",
            "location": "Engineering Office",
        },
        {
            "code": "SALES",
            "name": "Sales & Commercial",
            "name_ar": "المبيعات والتجارة",
            "location": "Head Office - Al Khobar",
        },
        {
            "code": "LOG",
            "name": "Logistics & Warehouse",
            "name_ar": "اللوجستيات والمستودعات",
            "location": "Warehouse",
        },
        {
            "code": "HR",
            "name": "Human Resources",
            "name_ar": "الموارد البشرية",
            "location": "Head Office - Al Khobar",
        },
        {
            "code": "HSSE",
            "name": "Health, Safety, Security, Environment",
            "name_ar": "الصحة والسلامة والأمن والبيئة",
            "location": "HSSE Office",
        },
        {
            "code": "FIN",
            "name": "Finance & Accounting",
            "name_ar": "المالية والمحاسبة",
            "location": "Head Office - Al Khobar",
        },
        {
            "code": "FIELD",
            "name": "Field Operations",
            "name_ar": "العمليات الميدانية",
            "location": "Rig Sites",
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update of existing departments",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding ARDT Departments ===\n"))

        force = options.get("force", False)
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for dept_data in self.DEPARTMENTS:
            code = dept_data["code"]

            try:
                dept, created = Department.objects.get_or_create(
                    code=code,
                    defaults=dept_data,
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Created: {code} - {dept.name}")
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f"           {dept.name_ar}")
                    )
                elif force:
                    # Update existing department
                    for key, value in dept_data.items():
                        setattr(dept, key, value)
                    dept.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  ↻ Updated: {code} - {dept.name}")
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.NOTICE(f"  - Skipped (exists): {code}")
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error creating {code}: {str(e)}")
                )

        # Summary
        self.stdout.write("\n" + "-" * 40)
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.WARNING(f"  Updated: {updated_count}"))
        self.stdout.write(f"  Skipped: {skipped_count}")
        self.stdout.write("-" * 40)

        # Department list
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== ARDT Departments ===\n"))
        self.stdout.write("  Code   | Name                                    | Arabic")
        self.stdout.write("  " + "-" * 70)
        for dept_data in self.DEPARTMENTS:
            self.stdout.write(
                f"  {dept_data['code']:<6} | {dept_data['name']:<40} | {dept_data['name_ar']}"
            )

        self.stdout.write(self.style.SUCCESS("\n✓ Department seeding complete!\n"))
