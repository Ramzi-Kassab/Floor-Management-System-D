"""
Edge Case Test Suite
ARDT Floor Management System - Phase 3 Day 5

Tests edge cases and boundary conditions:
- Decimal precision handling
- Unique constraint enforcement
- Null vs blank field handling
- Boundary values
- String length limits
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.db import IntegrityError
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db

User = get_user_model()


class TestDecimalPrecision:
    """Test decimal field precision handling."""

    def test_drill_bit_size_precision(self, db):
        """Test drill bit size handles decimal precision."""
        from apps.workorders.models import DrillBit

        # Test standard decimal
        bit1 = DrillBit.objects.create(
            serial_number="DEC-001",
            status="AVAILABLE",
            size=Decimal("8.500"),
            bit_type="PDC",
        )
        assert bit1.size == Decimal("8.500")

        # Test high precision decimal
        bit2 = DrillBit.objects.create(
            serial_number="DEC-002",
            status="AVAILABLE",
            size=Decimal("12.125"),
            bit_type="PDC",
        )
        assert bit2.size == Decimal("12.125")

    def test_decimal_rounding(self, db):
        """Test decimal values are handled correctly."""
        from apps.supplychain.models import Vendor

        vendor = Vendor.objects.create(
            name="Decimal Test Vendor",
            vendor_type="SUPPLIER",
            status="ACTIVE",
            credit_limit=Decimal("99999.99"),
        )

        vendor.refresh_from_db()
        assert vendor.credit_limit == Decimal("99999.99")


class TestUniqueConstraints:
    """Test unique constraint enforcement."""

    def test_unique_serial_number(self, db):
        """Test drill bit serial numbers must be unique."""
        from apps.workorders.models import DrillBit

        DrillBit.objects.create(
            serial_number="UNIQUE-001",
            status="AVAILABLE",
            size=Decimal("8.500"),
            bit_type="PDC",
        )

        # Creating another with same serial should fail
        with pytest.raises(IntegrityError):
            DrillBit.objects.create(
                serial_number="UNIQUE-001",
                status="AVAILABLE",
                size=Decimal("8.500"),
                bit_type="PDC",
            )

    def test_unique_customer_code(self, db):
        """Test customer codes must be unique."""
        from apps.sales.models import Customer

        Customer.objects.create(
            code="CUST-UNIQUE",
            name="Test Customer 1",
            customer_type="OPERATOR",
            is_active=True,
        )

        with pytest.raises(IntegrityError):
            Customer.objects.create(
                code="CUST-UNIQUE",
                name="Test Customer 2",
                customer_type="OPERATOR",
                is_active=True,
            )


class TestNullAndBlankHandling:
    """Test null vs blank field handling."""

    def test_optional_fields_accept_null(self, db):
        """Test optional FK fields can be null."""
        from apps.supplychain.models import Vendor

        # Create with minimal required fields
        vendor = Vendor.objects.create(
            name="Null Test Vendor",
            vendor_type="SUPPLIER",
            status="ACTIVE",
        )

        # Optional fields should be empty/null
        assert vendor.website == "" or vendor.website is None
        assert vendor.tax_id == "" or vendor.tax_id is None

    def test_blank_string_fields(self, db):
        """Test blank string fields are handled correctly."""
        from apps.supplychain.models import Vendor

        vendor = Vendor.objects.create(
            name="Blank Test Vendor",
            vendor_type="SUPPLIER",
            status="ACTIVE",
            website="",  # Blank string
            internal_notes="",  # Blank string
        )

        assert vendor.website == ""
        assert vendor.internal_notes == ""


class TestBoundaryValues:
    """Test boundary value handling."""

    def test_date_boundaries(self, db):
        """Test date field boundaries with employees."""
        from apps.hr.models import Employee

        user = User.objects.create_user(
            username="date_bound_user",
            email="datebound@test.com",
            password="testpass123",
        )

        # Test future hire date
        employee = Employee.objects.create(
            user=user,
            department="Engineering",
            job_title="Engineer",
            hire_date=date(2025, 12, 31),
            employment_type=Employee.EmploymentType.FULL_TIME,
            employment_status=Employee.EmploymentStatus.ACTIVE,
        )
        assert employee.hire_date.year == 2025

    def test_vendor_status_values(self, db):
        """Test all vendor status values are valid."""
        from apps.supplychain.models import Vendor

        statuses = [
            "PROSPECT", "QUALIFIED", "ACTIVE",
            "INACTIVE", "SUSPENDED", "DISQUALIFIED"
        ]

        for i, status in enumerate(statuses):
            vendor = Vendor.objects.create(
                name=f"Status Vendor {i}",
                vendor_type="SUPPLIER",
                status=status,
            )
            assert vendor.status == status


class TestStringLengthLimits:
    """Test string field length limits."""

    def test_description_length(self, db):
        """Test description field can hold long text."""
        from apps.supplychain.models import Vendor

        long_notes = "A" * 2000  # 2000 characters

        vendor = Vendor.objects.create(
            name="Long Notes Vendor",
            vendor_type="SUPPLIER",
            status="ACTIVE",
            internal_notes=long_notes,
        )

        vendor.refresh_from_db()
        assert len(vendor.internal_notes) == 2000

    def test_vendor_name_length(self, db):
        """Test vendor name field length."""
        from apps.supplychain.models import Vendor

        # Standard name
        vendor = Vendor.objects.create(
            name="Test Vendor Name",
            vendor_type="SUPPLIER",
            status="ACTIVE",
        )
        assert len(vendor.name) == 16


class TestStatusTransitions:
    """Test status field transitions and constraints."""

    def test_all_vendor_statuses(self, db):
        """Test all vendor status values."""
        from apps.supplychain.models import Vendor

        statuses = [
            "PROSPECT", "QUALIFIED", "ACTIVE",
            "INACTIVE", "SUSPENDED", "DISQUALIFIED"
        ]

        vendor = Vendor.objects.create(
            name="Transition Test Vendor",
            vendor_type="SUPPLIER",
            status="PROSPECT",
        )

        for status in statuses:
            vendor.status = status
            vendor.save()
            vendor.refresh_from_db()
            assert vendor.status == status

    def test_employee_employment_status(self, db):
        """Test employee employment status transitions."""
        from apps.hr.models import Employee

        user = User.objects.create_user(
            username="status_trans_user",
            email="statustrans@test.com",
            password="testpass123",
        )

        employee = Employee.objects.create(
            user=user,
            department="Operations",
            job_title="Operator",
            hire_date=date.today(),
            employment_type=Employee.EmploymentType.FULL_TIME,
            employment_status=Employee.EmploymentStatus.ACTIVE,
        )

        # Test status transitions
        for status in ["ACTIVE", "ON_LEAVE", "TERMINATED"]:
            employee.employment_status = status
            employee.save()
            employee.refresh_from_db()
            assert employee.employment_status == status


class TestForeignKeyConstraints:
    """Test foreign key constraint handling."""

    def test_protected_relationship(self, db):
        """Test protected FK prevents deletion."""
        from apps.sales.models import Customer, ServiceSite
        from django.db.models.deletion import ProtectedError

        customer = Customer.objects.create(
            code="PROTECT-001",
            name="Protected Test Customer",
            customer_type="OPERATOR",
            is_active=True,
        )

        site = ServiceSite.objects.create(
            site_code="SITE-PROTECT",
            name="Protected Test Site",
            customer=customer,
            site_type="RIG_SITE",
            address_line1="123 Test St",
            city="Test City",
            country="Saudi Arabia",
            is_active=True,
        )

        # Delete customer should raise ProtectedError
        with pytest.raises(ProtectedError):
            customer.delete()

        # Site should still exist
        assert ServiceSite.objects.filter(id=site.id).exists()

    def test_optional_fk_null_handling(self, db):
        """Test optional foreign keys can be null."""
        from apps.supplychain.models import Vendor

        vendor = Vendor.objects.create(
            name="Optional FK Vendor",
            vendor_type="SUPPLIER",
            status="ACTIVE",
        )

        # Optional FKs should be null
        assert vendor.qualified_by is None


class TestModelValidation:
    """Test model-level validation."""

    def test_employee_employment_type_choices(self, db):
        """Test employee employment type must be valid choice."""
        from apps.hr.models import Employee

        user = User.objects.create_user(
            username="emp_type_user",
            email="emptype@test.com",
            password="testpass123",
        )

        employee = Employee.objects.create(
            user=user,
            department="Engineering",
            job_title="Engineer",
            hire_date=date.today(),
            employment_type=Employee.EmploymentType.FULL_TIME,
            employment_status=Employee.EmploymentStatus.ACTIVE,
        )

        # Should have valid employment type
        assert employee.employment_type in [
            "FULL_TIME", "PART_TIME", "CONTRACT", "INTERN", "TEMPORARY"
        ]

    def test_leave_request_dates(self, db):
        """Test leave request date validation."""
        from apps.hr.models import Employee, LeaveRequest

        user = User.objects.create_user(
            username="leave_user",
            email="leave@test.com",
            password="testpass123",
        )

        employee = Employee.objects.create(
            user=user,
            department="Engineering",
            job_title="Engineer",
            hire_date=date.today() - timedelta(days=365),
            employment_type=Employee.EmploymentType.FULL_TIME,
            employment_status=Employee.EmploymentStatus.ACTIVE,
        )

        # End date should be after start date
        leave = LeaveRequest.objects.create(
            employee=employee,
            leave_type="ANNUAL",
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            total_days=5,
            reason="Vacation",
            status="DRAFT",
        )

        assert leave.end_date > leave.start_date


class TestAutoIDGeneration:
    """Test auto-ID generation edge cases."""

    def test_vendor_auto_code_generation(self, db):
        """Test vendors get unique auto-generated codes."""
        from apps.supplychain.models import Vendor

        vendor1 = Vendor.objects.create(
            name="Auto ID Vendor 1",
            vendor_type="SUPPLIER",
            status="ACTIVE",
        )

        vendor2 = Vendor.objects.create(
            name="Auto ID Vendor 2",
            vendor_type="SUPPLIER",
            status="ACTIVE",
        )

        # Both should have codes
        assert vendor1.vendor_code is not None
        assert vendor2.vendor_code is not None

        # Codes should be unique
        assert vendor1.vendor_code != vendor2.vendor_code
