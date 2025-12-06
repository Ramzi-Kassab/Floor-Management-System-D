"""
ARDT FMS - Load Demo Data Command
Phase 5: Test Data & Demo

Creates comprehensive demo data for all sprint models:
- Sprint 4: Work Orders, Drill Bits
- Sprint 5: Customers, Sites, Field Service
- Sprint 6: Vendors, Purchase Orders
- Sprint 7: Quality Control, NCRs
- Sprint 8: Employees, Leave, Training

Usage:
    python manage.py load_demo_data
    python manage.py load_demo_data --clear
    python manage.py load_demo_data --module=sales
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Load comprehensive demo data for all modules"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing demo data before loading",
        )
        parser.add_argument(
            "--module",
            type=str,
            choices=["sales", "supplychain", "compliance", "hr", "workorders", "all"],
            default="all",
            help="Load data for specific module only",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(self.style.NOTICE("ARDT FMS - Demo Data Loader"))
        self.stdout.write(self.style.NOTICE("=" * 60))

        if options["clear"]:
            self.clear_demo_data()

        # Always create base users first
        self.create_demo_users()

        module = options["module"]

        if module in ["all", "workorders"]:
            self.create_workorders_data()

        if module in ["all", "sales"]:
            self.create_sales_data()

        if module in ["all", "supplychain"]:
            self.create_supplychain_data()

        if module in ["all", "compliance"]:
            self.create_compliance_data()

        if module in ["all", "hr"]:
            self.create_hr_data()

        self.print_summary()
        self.stdout.write(self.style.SUCCESS("\nDemo data loaded successfully!"))

    def clear_demo_data(self):
        """Clear existing demo data."""
        self.stdout.write(self.style.WARNING("\nClearing existing demo data..."))

        # Clear in reverse dependency order
        try:
            from apps.hr.models import LeaveRequest, Employee
            LeaveRequest.objects.filter(employee__user__username__startswith="demo_").delete()
            Employee.objects.filter(user__username__startswith="demo_").delete()
        except Exception:
            pass

        try:
            from apps.compliance.models import QualityControl, NonConformanceReport
            QualityControl.objects.filter(qc_number__startswith="QC-DEMO").delete()
            NonConformanceReport.objects.filter(ncr_number__startswith="NCR-DEMO").delete()
        except Exception:
            pass

        try:
            from apps.supplychain.models import PurchaseOrder, Vendor
            PurchaseOrder.objects.filter(po_number__startswith="PO-DEMO").delete()
            Vendor.objects.filter(vendor_code__startswith="VND-DEMO").delete()
        except Exception:
            pass

        try:
            from apps.sales.models import FieldServiceRequest, ServiceSite, Customer
            FieldServiceRequest.objects.filter(request_number__startswith="FSR-DEMO").delete()
            ServiceSite.objects.filter(site_code__startswith="SITE-DEMO").delete()
            Customer.objects.filter(code__startswith="DEMO").delete()
        except Exception:
            pass

        try:
            from apps.workorders.models import WorkOrder, DrillBit
            WorkOrder.objects.filter(wo_number__startswith="WO-DEMO").delete()
            DrillBit.objects.filter(serial_number__startswith="DEMO-").delete()
        except Exception:
            pass

        # Delete demo users
        User.objects.filter(username__startswith="demo_").delete()

        self.stdout.write(self.style.SUCCESS("Demo data cleared."))

    def create_demo_users(self):
        """Create demo users."""
        self.stdout.write("\nCreating demo users...")

        demo_users = [
            ("demo_admin", "Admin", "User", "admin@demo.ardt.com", True),
            ("demo_manager", "Sarah", "Johnson", "sarah.j@demo.ardt.com", False),
            ("demo_technician", "Mike", "Chen", "mike.c@demo.ardt.com", False),
            ("demo_qc", "Emma", "Wilson", "emma.w@demo.ardt.com", False),
            ("demo_planner", "James", "Brown", "james.b@demo.ardt.com", False),
            ("demo_hr", "Lisa", "Davis", "lisa.d@demo.ardt.com", False),
            ("demo_procurement", "David", "Miller", "david.m@demo.ardt.com", False),
            ("demo_field", "Alex", "Taylor", "alex.t@demo.ardt.com", False),
        ]

        for username, first, last, email, is_staff in demo_users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": email,
                    "is_staff": is_staff,
                    "is_active": True,
                }
            )
            if created:
                user.set_password("demo123")
                user.save()
                self.stdout.write(f"  Created: {username}")

    def create_workorders_data(self):
        """Create work orders and drill bits demo data."""
        self.stdout.write("\nCreating Work Orders module data...")

        from apps.workorders.models import DrillBit, WorkOrder

        # Create drill bits
        bit_configs = [
            ("DEMO-PDC-001", "PDC", Decimal("8.500"), "M323"),
            ("DEMO-PDC-002", "PDC", Decimal("12.250"), "M423"),
            ("DEMO-TCI-001", "TCI", Decimal("9.875"), "S323"),
            ("DEMO-TCI-002", "TCI", Decimal("17.500"), "S423"),
            ("DEMO-HYBRID-001", "HYBRID", Decimal("8.500"), "M222"),
        ]

        for serial, bit_type, size, iadc in bit_configs:
            DrillBit.objects.get_or_create(
                serial_number=serial,
                defaults={
                    "bit_type": bit_type,
                    "size": size,
                    "iadc_code": iadc,
                    "status": "AVAILABLE",
                    "total_hours": Decimal(str(random.randint(50, 300))),
                    "total_footage": random.randint(1000, 8000),
                }
            )

        # Create work orders
        technician = User.objects.filter(username="demo_technician").first()
        drill_bits = list(DrillBit.objects.filter(serial_number__startswith="DEMO-"))
        today = date.today()

        wo_configs = [
            ("WO-DEMO-001", "REPAIR", "DRAFT", "HIGH", "PDC bit repair - blade damage"),
            ("WO-DEMO-002", "REWORK", "PLANNED", "MEDIUM", "TCI bit rework - bearing replacement"),
            ("WO-DEMO-003", "NEW", "IN_PROGRESS", "NORMAL", "New 8.5 PDC bit manufacturing"),
            ("WO-DEMO-004", "REPAIR", "QC_PENDING", "HIGH", "Emergency repair - field return"),
            ("WO-DEMO-005", "RETROFIT", "COMPLETED", "LOW", "Retrofit with new cutter design"),
        ]

        for wo_num, wo_type, status, priority, desc in wo_configs:
            wo, created = WorkOrder.objects.get_or_create(
                wo_number=wo_num,
                defaults={
                    "wo_type": wo_type,
                    "status": status,
                    "priority": priority,
                    "description": desc,
                    "drill_bit": random.choice(drill_bits) if drill_bits else None,
                    "assigned_to": technician,
                    "due_date": today + timedelta(days=random.randint(3, 14)),
                    "planned_start": today,
                    "planned_end": today + timedelta(days=random.randint(3, 10)),
                }
            )

        self.stdout.write(f"  Drill bits: {DrillBit.objects.filter(serial_number__startswith='DEMO-').count()}")
        self.stdout.write(f"  Work orders: {WorkOrder.objects.filter(wo_number__startswith='WO-DEMO').count()}")

    def create_sales_data(self):
        """Create sales and field service demo data."""
        self.stdout.write("\nCreating Sales module data...")

        from apps.sales.models import Customer, ServiceSite, FieldServiceRequest

        user = User.objects.filter(username="demo_field").first() or User.objects.first()

        # Create customers
        customer_configs = [
            ("DEMO-ARAMCO", "Saudi Aramco", "OPERATOR", "+966-13-872-0000"),
            ("DEMO-ADNOC", "ADNOC Drilling", "OPERATOR", "+971-2-602-0000"),
            ("DEMO-PDO", "Petroleum Dev Oman", "OPERATOR", "+968-24-67-0000"),
            ("DEMO-SCHLUM", "Schlumberger", "CONTRACTOR", "+1-713-513-2000"),
            ("DEMO-HALLI", "Halliburton", "CONTRACTOR", "+1-281-871-2699"),
        ]

        customers = []
        for code, name, ctype, phone in customer_configs:
            customer, created = Customer.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "customer_type": ctype,
                    "phone": phone,
                    "is_active": True,
                }
            )
            customers.append(customer)

        # Create service sites
        site_configs = [
            ("SITE-DEMO-001", "Ghawar Field Rig 5", "RIG_SITE", "Dhahran", "Saudi Arabia"),
            ("SITE-DEMO-002", "Shaybah Remote Site", "RIG_SITE", "Shaybah", "Saudi Arabia"),
            ("SITE-DEMO-003", "ADNOC Service Center", "SERVICE_CENTER", "Abu Dhabi", "UAE"),
            ("SITE-DEMO-004", "PDO Main Base", "WAREHOUSE", "Muscat", "Oman"),
            ("SITE-DEMO-005", "Aramco HQ Workshop", "SERVICE_CENTER", "Dhahran", "Saudi Arabia"),
        ]

        sites = []
        for site_code, name, stype, city, country in site_configs:
            site, created = ServiceSite.objects.get_or_create(
                site_code=site_code,
                defaults={
                    "name": name,
                    "site_type": stype,
                    "customer": random.choice(customers),
                    "address_line1": f"Industrial Area {random.randint(1, 10)}",
                    "city": city,
                    "country": country,
                    "is_active": True,
                }
            )
            sites.append(site)

        # Create field service requests
        today = date.today()
        fsr_configs = [
            ("FSR-DEMO-001", "DRILL_BIT_INSPECTION", "HIGH", "Urgent bit inspection required"),
            ("FSR-DEMO-002", "ON_SITE_REPAIR", "MEDIUM", "On-site blade repair needed"),
            ("FSR-DEMO-003", "EQUIPMENT_DELIVERY", "NORMAL", "New bit delivery and setup"),
            ("FSR-DEMO-004", "TECHNICAL_SUPPORT", "LOW", "Technical consultation"),
            ("FSR-DEMO-005", "TRAINING", "NORMAL", "Operator training session"),
        ]

        for req_num, rtype, priority, title in fsr_configs:
            site = random.choice(sites)
            FieldServiceRequest.objects.get_or_create(
                request_number=req_num,
                defaults={
                    "customer": site.customer,
                    "service_site": site,
                    "request_type": rtype,
                    "priority": priority,
                    "title": title,
                    "description": f"Demo request: {title}",
                    "requested_date": today + timedelta(days=random.randint(1, 14)),
                    "contact_person": "Field Contact",
                    "contact_phone": "+966-50-000-0000",
                    "created_by": user,
                    "status": random.choice(["DRAFT", "SUBMITTED", "APPROVED"]),
                }
            )

        self.stdout.write(f"  Customers: {Customer.objects.filter(code__startswith='DEMO').count()}")
        self.stdout.write(f"  Service sites: {ServiceSite.objects.filter(site_code__startswith='SITE-DEMO').count()}")
        self.stdout.write(f"  Service requests: {FieldServiceRequest.objects.filter(request_number__startswith='FSR-DEMO').count()}")

    def create_supplychain_data(self):
        """Create supply chain demo data."""
        self.stdout.write("\nCreating Supply Chain module data...")

        from apps.supplychain.models import Vendor, PurchaseOrder

        user = User.objects.filter(username="demo_procurement").first() or User.objects.first()

        # Create vendors
        vendor_configs = [
            ("VND-DEMO-001", "PDC Cutters Inc", "MANUFACTURER", "USA"),
            ("VND-DEMO-002", "Bearing Solutions Ltd", "SUPPLIER", "Germany"),
            ("VND-DEMO-003", "Steel Materials Corp", "SUPPLIER", "China"),
            ("VND-DEMO-004", "Precision Tools ME", "SUPPLIER", "UAE"),
            ("VND-DEMO-005", "Advanced Carbide Co", "MANUFACTURER", "USA"),
        ]

        vendors = []
        for code, name, vtype, country in vendor_configs:
            vendor, created = Vendor.objects.get_or_create(
                vendor_code=code,
                defaults={
                    "name": name,
                    "vendor_type": vtype,
                    "status": "ACTIVE",
                    "country": country,
                    "payment_terms": "NET30",
                    "credit_limit": Decimal(str(random.randint(50000, 500000))),
                }
            )
            vendors.append(vendor)

        # Create purchase orders
        today = date.today()
        po_configs = [
            ("PO-DEMO-001", "PDC cutters order", Decimal("45000.00")),
            ("PO-DEMO-002", "Bearing assemblies", Decimal("12500.00")),
            ("PO-DEMO-003", "Steel blanks", Decimal("28000.00")),
            ("PO-DEMO-004", "Tool accessories", Decimal("5600.00")),
            ("PO-DEMO-005", "Carbide inserts", Decimal("67000.00")),
        ]

        for po_num, desc, amount in po_configs:
            PurchaseOrder.objects.get_or_create(
                po_number=po_num,
                defaults={
                    "vendor": random.choice(vendors),
                    "description": desc,
                    "status": random.choice(["DRAFT", "SUBMITTED", "APPROVED", "ORDERED"]),
                    "order_date": today - timedelta(days=random.randint(0, 30)),
                    "expected_date": today + timedelta(days=random.randint(7, 45)),
                    "total_amount": amount,
                    "currency": "USD",
                    "created_by": user,
                }
            )

        self.stdout.write(f"  Vendors: {Vendor.objects.filter(vendor_code__startswith='VND-DEMO').count()}")
        self.stdout.write(f"  Purchase orders: {PurchaseOrder.objects.filter(po_number__startswith='PO-DEMO').count()}")

    def create_compliance_data(self):
        """Create compliance and quality demo data."""
        self.stdout.write("\nCreating Compliance module data...")

        from apps.compliance.models import QualityControl, NonConformanceReport

        inspector = User.objects.filter(username="demo_qc").first() or User.objects.first()
        today = date.today()

        # Create quality control records
        qc_configs = [
            ("QC-DEMO-001", "RECEIVING", "PASS", "Incoming material inspection"),
            ("QC-DEMO-002", "IN_PROCESS", "PASS", "Mid-production check"),
            ("QC-DEMO-003", "FINAL", "PASS", "Final product inspection"),
            ("QC-DEMO-004", "RECEIVING", "FAIL", "Material defect found"),
            ("QC-DEMO-005", "FINAL", "CONDITIONAL", "Minor deviation accepted"),
        ]

        for qc_num, itype, result, notes in qc_configs:
            QualityControl.objects.get_or_create(
                qc_number=qc_num,
                defaults={
                    "inspection_type": itype,
                    "inspection_date": today - timedelta(days=random.randint(0, 30)),
                    "inspector": inspector,
                    "result": result,
                    "notes": notes,
                }
            )

        # Create NCRs
        ncr_configs = [
            ("NCR-DEMO-001", "MATERIAL", "OPEN", "HIGH", "Out-of-spec steel received"),
            ("NCR-DEMO-002", "PROCESS", "UNDER_REVIEW", "MEDIUM", "Procedure deviation"),
            ("NCR-DEMO-003", "PRODUCT", "CLOSED", "LOW", "Minor cosmetic defect"),
        ]

        for ncr_num, ntype, status, severity, desc in ncr_configs:
            NonConformanceReport.objects.get_or_create(
                ncr_number=ncr_num,
                defaults={
                    "ncr_type": ntype,
                    "status": status,
                    "severity": severity,
                    "description": desc,
                    "detected_date": today - timedelta(days=random.randint(0, 30)),
                    "detected_by": inspector,
                    "reported_by": inspector,
                }
            )

        self.stdout.write(f"  QC records: {QualityControl.objects.filter(qc_number__startswith='QC-DEMO').count()}")
        self.stdout.write(f"  NCRs: {NonConformanceReport.objects.filter(ncr_number__startswith='NCR-DEMO').count()}")

    def create_hr_data(self):
        """Create HR workforce demo data."""
        self.stdout.write("\nCreating HR module data...")

        from apps.hr.models import Employee, LeaveRequest, Training

        today = date.today()

        # Create employees from demo users
        employee_configs = [
            ("demo_manager", "Operations", "Operations Manager", "FULL_TIME"),
            ("demo_technician", "Workshop", "Senior Technician", "FULL_TIME"),
            ("demo_qc", "Quality", "QC Inspector", "FULL_TIME"),
            ("demo_planner", "Planning", "Production Planner", "FULL_TIME"),
            ("demo_hr", "Human Resources", "HR Coordinator", "FULL_TIME"),
            ("demo_procurement", "Supply Chain", "Procurement Officer", "FULL_TIME"),
            ("demo_field", "Field Service", "Field Engineer", "FULL_TIME"),
        ]

        employees = []
        for username, dept, title, emp_type in employee_configs:
            user = User.objects.filter(username=username).first()
            if user:
                emp, created = Employee.objects.get_or_create(
                    user=user,
                    defaults={
                        "department": dept,
                        "job_title": title,
                        "hire_date": today - timedelta(days=random.randint(180, 1000)),
                        "employment_type": emp_type,
                        "employment_status": "ACTIVE",
                    }
                )
                employees.append(emp)

        # Create leave requests
        if employees:
            leave_types = ["ANNUAL", "SICK", "PERSONAL"]
            for i in range(5):
                emp = random.choice(employees)
                start = today + timedelta(days=random.randint(5, 60))
                days = random.randint(1, 5)
                LeaveRequest.objects.get_or_create(
                    employee=emp,
                    start_date=start,
                    defaults={
                        "leave_type": random.choice(leave_types),
                        "end_date": start + timedelta(days=days),
                        "total_days": days,
                        "reason": "Demo leave request",
                        "status": random.choice(["DRAFT", "SUBMITTED", "APPROVED"]),
                    }
                )

        # Create training records
        training_configs = [
            ("Safety Orientation", "SAFETY", 8),
            ("PDC Bit Repair Training", "TECHNICAL", 24),
            ("QC Procedures", "QUALITY", 16),
            ("Leadership Skills", "SOFT_SKILLS", 8),
        ]

        for title, ttype, hours in training_configs:
            Training.objects.get_or_create(
                title=title,
                defaults={
                    "training_type": ttype,
                    "description": f"Demo training: {title}",
                    "duration_hours": hours,
                    "is_mandatory": ttype == "SAFETY",
                    "status": "ACTIVE",
                }
            )

        self.stdout.write(f"  Employees: {Employee.objects.filter(user__username__startswith='demo_').count()}")
        self.stdout.write(f"  Leave requests: {LeaveRequest.objects.count()}")
        self.stdout.write(f"  Training programs: {Training.objects.count()}")

    def print_summary(self):
        """Print summary of created demo data."""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("DEMO DATA SUMMARY")
        self.stdout.write("=" * 60)

        self.stdout.write("\nDemo User Credentials (password: demo123):")
        self.stdout.write("  - demo_admin (Administrator)")
        self.stdout.write("  - demo_manager (Operations Manager)")
        self.stdout.write("  - demo_technician (Technician)")
        self.stdout.write("  - demo_qc (QC Inspector)")
        self.stdout.write("  - demo_planner (Planner)")
        self.stdout.write("  - demo_hr (HR)")
        self.stdout.write("  - demo_procurement (Procurement)")
        self.stdout.write("  - demo_field (Field Engineer)")

        self.stdout.write("\nDemo Data Prefixes:")
        self.stdout.write("  - Drill bits: DEMO-*")
        self.stdout.write("  - Work orders: WO-DEMO-*")
        self.stdout.write("  - Customers: DEMO-*")
        self.stdout.write("  - Sites: SITE-DEMO-*")
        self.stdout.write("  - Vendors: VND-DEMO-*")
        self.stdout.write("  - POs: PO-DEMO-*")
        self.stdout.write("  - QC: QC-DEMO-*")
        self.stdout.write("  - NCR: NCR-DEMO-*")
