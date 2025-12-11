"""
ARDT FMS - Seed Departments Command
Creates real ARDT departments from QAS-105 company structure

Usage: python manage.py seed_departments
"""

from django.core.management.base import BaseCommand
from apps.organization.models import Department


class Command(BaseCommand):
    help = "Seed real ARDT departments from QAS-105 company structure"

    # Real ARDT Departments from MASTER_PLAN v3.0 / QAS-105
    DEPARTMENTS = [
        {
            "code": "EXEC",
            "name": "Executive Management",
            "name_ar": "الإدارة التنفيذية",
            "location": "Head Office - Dammam",
        },
        {
            "code": "TECH",
            "name": "Technology",
            "name_ar": "التقنية",
            "location": "Engineering Office",
        },
        {
            "code": "SALES",
            "name": "Sales",
            "name_ar": "المبيعات",
            "location": "Head Office - Dammam",
        },
        {
            "code": "OPS",
            "name": "Operations",
            "name_ar": "العمليات",
            "location": "Factory Floor",
        },
        {
            "code": "QC",
            "name": "Quality",
            "name_ar": "الجودة",
            "location": "QC Lab",
        },
        {
            "code": "PROC",
            "name": "Procurement & Logistics",
            "name_ar": "المشتريات واللوجستيات",
            "location": "Warehouse",
        },
        {
            "code": "FIN",
            "name": "Finance",
            "name_ar": "المالية",
            "location": "Head Office - Dammam",
        },
        {
            "code": "HR",
            "name": "HR & Administration",
            "name_ar": "الموارد البشرية والإدارة",
            "location": "Head Office - Dammam",
        },
        {
            "code": "IT",
            "name": "Information Technology",
            "name_ar": "تقنية المعلومات",
            "location": "IT Office",
        },
        {
            "code": "HSSE",
            "name": "Health, Safety, Security, Environment",
            "name_ar": "الصحة والسلامة والأمن والبيئة",
            "location": "HSSE Office",
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update of existing departments",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding ARDT Departments (QAS-105) ===\n"))

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
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== ARDT Departments (10 Total) ===\n"))
        self.stdout.write("  Code   | Name                                    | Arabic")
        self.stdout.write("  " + "-" * 70)
        for dept_data in self.DEPARTMENTS:
            self.stdout.write(
                f"  {dept_data['code']:<6} | {dept_data['name']:<40} | {dept_data['name_ar']}"
            )

        self.stdout.write(self.style.SUCCESS("\n✓ Department seeding complete!\n"))
