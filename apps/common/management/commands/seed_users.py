"""
ARDT FMS - Seed Users Command
Creates all 27 real ARDT employees from QAS-105 contact list

Usage: python manage.py seed_users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.organization.models import Department, Position

User = get_user_model()


class Command(BaseCommand):
    help = "Seed all 27 real ARDT employees from QAS-105"

    # Password for all users (except admin)
    DEFAULT_PASSWORD = "Ardt@2025"

    # All 27 Real ARDT Employees from MASTER_PLAN v3.0
    USERS = [
        # ============ EXECUTIVE ============
        {
            "username": "g.escobar",
            "first_name": "Gustavo",
            "last_name": "Escobar",
            "email": "gustavofredy.escobar@halliburton.com",
            "mobile": "506-517-855",
            "position_code": "GM",
            "department_code": "EXEC",
            "is_staff": True,
        },

        # ============ TECHNOLOGY ============
        {
            "username": "s.jamal",
            "first_name": "Saad",
            "last_name": "Jamal",
            "email": "saad.jamal@halliburton.com",
            "mobile": "500-611-270",
            "phone_extension": "132",
            "position_code": "TM",
            "department_code": "TECH",
            "is_staff": True,
        },

        # ============ SALES ============
        {
            "username": "o.abdelbaset",
            "first_name": "Omar",
            "last_name": "Abdel Baset",
            "email": "omar.abdelbaset@halliburton.com",
            "mobile": "537-070-233",
            "position_code": "SM",
            "department_code": "SALES",
            "is_staff": True,
        },
        {
            "username": "a.elsafi",
            "first_name": "Ahmed Emad",
            "last_name": "Elsafi",
            "email": "ahmed.elsafi@halliburton.com",
            "mobile": "550-103-145",
            "position_code": "SAL",
            "department_code": "SALES",
        },
        {
            "username": "j.kunjur",
            "first_name": "Jainuddin",
            "last_name": "Kunjur",
            "email": "zainukunjur@ardtco.com",
            "mobile": "538-250-722",
            "position_code": "FOS",
            "department_code": "SALES",
        },

        # ============ OPERATIONS ============
        {
            "username": "a.buobaid",
            "first_name": "Abdulaziz",
            "last_name": "Al Buobaid",
            "email": "azizbuobaid@ardtco.com",
            "mobile": "543-331-108",
            "position_code": "OPM",
            "department_code": "OPS",
            "is_staff": True,
        },
        {
            "username": "r.shetty",
            "first_name": "Ranjith",
            "last_name": "Shetty",
            "email": "ranjith@ardtco.com",
            "mobile": "532-461-019",
            "position_code": "MFS",
            "department_code": "OPS",
        },
        {
            "username": "r.kassab",
            "first_name": "Ramzi",
            "last_name": "Kassab",
            "email": "ramzi@ardtco.com",
            "mobile": "570-646-911",
            "phone_extension": "109",
            "position_code": "RPS",
            "department_code": "OPS",
        },
        {
            "username": "r.alwasmi",
            "first_name": "Radi",
            "last_name": "Al Wasmi",
            "email": "radi@ardtco.com",
            "mobile": "505-511-385",
            "position_code": "RPT",
            "department_code": "OPS",
        },
        {
            "username": "h.alsaba",
            "first_name": "Habib Salah",
            "last_name": "Al Saba",
            "email": "habeebs1399@gmail.com",
            "mobile": "540-742-881",
            "position_code": "RPT",
            "department_code": "OPS",
        },
        {
            "username": "h.almuhnna",
            "first_name": "Habib Tahar",
            "last_name": "Al Muhnna",
            "email": "hbhb-2010@hotmail.com",
            "mobile": "501-520-531",
            "position_code": "RPT",
            "department_code": "OPS",
        },

        # ============ QUALITY ============
        {
            "username": "a.chisti",
            "first_name": "Ahmed Faizan",
            "last_name": "Chisti",
            "email": "chisti@ardtco.com",
            "mobile": "538-071-220",
            "position_code": "QM",
            "department_code": "QC",
            "is_staff": True,
        },
        {
            "username": "j.lohar",
            "first_name": "Javed Umer",
            "last_name": "Lohar",
            "email": "javedlohar@ardtco.com",
            "mobile": "531-019-157",
            "position_code": "QAC",
            "department_code": "QC",
        },
        {
            "username": "a.khan",
            "first_name": "Adil",
            "last_name": "Khan",
            "email": "adil.khan@ardtco.com",
            "mobile": "531-156-753",
            "position_code": "FNI",
            "department_code": "QC",
        },
        {
            "username": "a.alhammad",
            "first_name": "Ali",
            "last_name": "Al Hammad",
            "email": "ali.alhammad@ardtco.com",
            "mobile": "550-868-041",
            "position_code": "QCI",
            "department_code": "QC",
        },

        # ============ PROCUREMENT & LOGISTICS ============
        {
            "username": "m.asad",
            "first_name": "Muhammad",
            "last_name": "Asad",
            "email": "muhammad.mukhtar@ardtco.com",
            "mobile": "508-921-463",
            "position_code": "PLM",
            "department_code": "PROC",
            "is_staff": True,
        },
        {
            "username": "f.alhammad",
            "first_name": "Fathima",
            "last_name": "Alhammad",
            "email": "fatimah@ardtco.com",
            "mobile": "556-536-664",
            "position_code": "PRS",
            "department_code": "PROC",
        },
        {
            "username": "r.badaam",
            "first_name": "Riyadh",
            "last_name": "Badaam",
            "email": "riyadh.badaam@ardtco.com",
            "mobile": "545-182-942",
            "position_code": "PRC",
            "department_code": "PROC",
        },
        {
            "username": "p.peer",
            "first_name": "Peerla Imam",
            "last_name": "Peer",
            "email": "peerla.peer@ardtco.com",
            "mobile": "557-468-588",
            "position_code": "LGC",
            "department_code": "PROC",
        },
        {
            "username": "j.alghafly",
            "first_name": "Jehad",
            "last_name": "Alghafly",
            "email": "jehad@ardtco.com",
            "mobile": "533-418-111",
            "position_code": "LGC",
            "department_code": "PROC",
        },
        {
            "username": "a.vangali",
            "first_name": "Ajad",
            "last_name": "Vangali",
            "email": "azad658@gmail.com",
            "mobile": "531-017-322",
            "position_code": "DSP",
            "department_code": "PROC",
        },
        {
            "username": "a.mirza",
            "first_name": "Anas",
            "last_name": "Mirza",
            "email": "storekeeper@ardtco.com",
            "mobile": "540-729-874",
            "position_code": "STK",
            "department_code": "PROC",
        },
        {
            "username": "l.aljubran",
            "first_name": "Layla",
            "last_name": "Al Jubran",
            "email": "layla@ardtco.com",
            "mobile": "533-622-120",
            "position_code": "AOC",
            "department_code": "PROC",
        },

        # ============ FINANCE ============
        {
            "username": "w.khan",
            "first_name": "Waseem M.",
            "last_name": "Khan",
            "email": "wkhan@ardtco.com",
            "mobile": "581-691-218",
            "position_code": "FC",
            "department_code": "FIN",
            "is_staff": True,
        },

        # ============ IT ============
        {
            "username": "m.irshad",
            "first_name": "Mohammad",
            "last_name": "Irshad",
            "email": "irshad@ardtco.com",
            "mobile": "547-222-795",
            "position_code": "ITM",
            "department_code": "IT",
            "is_staff": True,
        },

        # ============ HR & ADMINISTRATION ============
        {
            "username": "b.setmoni",
            "first_name": "Bahebak Ya",
            "last_name": "Setmoni",
            "email": "Bahebak.Ya.Setmoni@elkayf.com",
            "mobile": "555-000-001",
            "position_code": "HRM",
            "department_code": "HR",
            "is_staff": True,
        },

        # ============ HSSE ============
        {
            "username": "m.lamouni",
            "first_name": "Mahma Elnas",
            "last_name": "Lamouni",
            "email": "Mahma.Elnas.Lamouni@elkayf.com",
            "mobile": "555-000-002",
            "position_code": "HSM",
            "department_code": "HSSE",
            "is_staff": True,
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update of existing users (resets password)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding ARDT Employees (27 Total) ===\n"))

        force = options.get("force", False)
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        # Cache departments and positions
        departments = {d.code: d for d in Department.objects.all()}
        positions = {p.code: p for p in Position.objects.all()}

        for idx, user_data in enumerate(self.USERS, 1):
            username = user_data["username"]
            dept_code = user_data.pop("department_code", None)
            pos_code = user_data.pop("position_code", None)

            try:
                # Get department and position
                department = departments.get(dept_code) if dept_code else None
                position = positions.get(pos_code) if pos_code else None

                if dept_code and not department:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ Department {dept_code} not found for {username}")
                    )
                if pos_code and not position:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ Position {pos_code} not found for {username}")
                    )

                # Add FK relationships
                user_data["department"] = department
                user_data["position"] = position
                user_data["employee_id"] = f"ARDT-{idx:03d}"
                user_data["timezone"] = "Asia/Riyadh"
                user_data["language"] = "en"

                # Set defaults
                user_data.setdefault("is_staff", False)
                user_data.setdefault("is_superuser", False)
                user_data.setdefault("phone_extension", "")

                user, created = User.objects.get_or_create(
                    username=username,
                    defaults=user_data,
                )

                if created:
                    user.set_password(self.DEFAULT_PASSWORD)
                    user.save()
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Created: {username} - {user.get_full_name()} ({pos_code or 'No Position'})")
                    )
                elif force:
                    for key, value in user_data.items():
                        setattr(user, key, value)
                    user.set_password(self.DEFAULT_PASSWORD)
                    user.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  ↻ Updated: {username} - {user.get_full_name()}")
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.NOTICE(f"  - Skipped (exists): {username}")
                    )

                # Restore for reference
                user_data["department_code"] = dept_code
                user_data["position_code"] = pos_code
                if "department" in user_data:
                    del user_data["department"]
                if "position" in user_data:
                    del user_data["position"]

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error creating {username}: {str(e)}")
                )
                error_count += 1
                user_data["department_code"] = dept_code
                user_data["position_code"] = pos_code

        # Summary
        self.stdout.write("\n" + "-" * 50)
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.WARNING(f"  Updated: {updated_count}"))
        self.stdout.write(f"  Skipped: {skipped_count}")
        if error_count:
            self.stdout.write(self.style.ERROR(f"  Errors: {error_count}"))
        self.stdout.write("-" * 50)

        # User count by department
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Employees by Department ===\n"))
        dept_counts = {}
        for user in self.USERS:
            dept = user.get("department_code", "Unknown")
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        for dept, count in sorted(dept_counts.items()):
            self.stdout.write(f"  {dept:<8}: {count} employees")

        # Login info
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Login Credentials ===\n"))
        self.stdout.write(f"  Password for ALL users: {self.DEFAULT_PASSWORD}")
        self.stdout.write("\n  Sample logins:")
        self.stdout.write("    - r.kassab (Ramzi Kassab - Repair Supervisor)")
        self.stdout.write("    - g.escobar (Gustavo Escobar - General Manager)")
        self.stdout.write("    - m.irshad (Mohammad Irshad - IT & ERP Manager)")

        self.stdout.write(f"\n  Total: {len(self.USERS)} employees")
        self.stdout.write(self.style.SUCCESS("\n✓ User seeding complete!\n"))
