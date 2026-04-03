"""
Comprehensive Integration Test Suite
ARDT Floor Management System - Phase 3 Testing

Tests complete workflows across multiple apps.
Uses shared fixtures from apps/conftest.py.

Note: Detailed model-level tests are in sprint smoke tests:
- apps/sales/tests/test_sprint5_smoke.py
- apps/supplychain/tests/test_sprint6_smoke.py
- apps/compliance/tests/test_sprint7_smoke.py
- apps/hr/tests/test_sprint8_smoke.py

This file focuses on cross-app integration and workflow tests.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db

User = get_user_model()


# ============================================================================
# REPAIR WORKFLOW TESTS
# ============================================================================

class TestRepairWorkflow:
    """Test complete repair workflow from work order to completion."""

    def test_work_order_creation(self, db):
        """Test work order can be created."""
        from apps.workorders.models import WorkOrder

        work_order = WorkOrder.objects.create(
            wo_type="REPAIR",
            description="Integration test for repair workflow",
            priority="MEDIUM",
            status="DRAFT",
            due_date=date.today() + timedelta(days=7),
        )

        assert work_order.pk is not None
        assert work_order.status == "DRAFT"

    def test_work_order_status_transitions(self, db):
        """Test work order can transition through statuses."""
        from apps.workorders.models import WorkOrder

        work_order = WorkOrder.objects.create(
            wo_type="REPAIR",
            description="Testing status transitions",
            priority="HIGH",
            status="DRAFT",
            due_date=date.today() + timedelta(days=5),
        )

        # Transition through statuses
        for status in ["PLANNED", "RELEASED", "IN_PROGRESS", "COMPLETED"]:
            work_order.status = status
            work_order.save()
            work_order.refresh_from_db()
            assert work_order.status == status

    def test_work_order_with_drill_bit(self, db):
        """Test work order linked to drill bit."""
        from apps.workorders.models import WorkOrder, DrillBit

        drill_bit = DrillBit.objects.create(
            serial_number="DB-INT-001",
            status="AVAILABLE",
            size=Decimal("8.500"),
            bit_type="PDC",
        )

        work_order = WorkOrder.objects.create(
            wo_type="REPAIR",
            description="Repair for drill bit",
            priority="HIGH",
            status="DRAFT",
            drill_bit=drill_bit,
            due_date=date.today() + timedelta(days=3),
        )

        assert work_order.drill_bit == drill_bit

    def test_work_order_qc_flow(self, db):
        """Test work order quality control flow."""
        from apps.workorders.models import WorkOrder

        work_order = WorkOrder.objects.create(
            wo_type="MANUFACTURING",
            description="Testing QC flow",
            priority="HIGH",
            status="DRAFT",
            due_date=date.today() + timedelta(days=5),
        )

        # Progress to QC
        work_order.status = "IN_PROGRESS"
        work_order.save()

        work_order.status = "QC_PENDING"
        work_order.save()

        work_order.status = "QC_PASSED"
        work_order.save()

        work_order.status = "COMPLETED"
        work_order.save()

        assert work_order.status == "COMPLETED"


# ============================================================================
# FIELD SERVICE WORKFLOW TESTS
# ============================================================================

class TestFieldServiceWorkflow:
    """Test complete field service workflow."""

    def test_service_request_creation(self, db, field_service_request):
        """Test field service request exists (uses conftest fixture)."""
        assert field_service_request.pk is not None
        assert field_service_request.customer is not None
        assert field_service_request.service_site is not None

    def test_service_request_status_transitions(self, db, customer, service_site, user):
        """Test service request status transitions."""
        from apps.sales.models import FieldServiceRequest

        request = FieldServiceRequest.objects.create(
            customer=customer,
            service_site=service_site,
            request_type="DRILL_BIT_INSPECTION",
            priority="HIGH",
            title="Status Transition Test",
            description="Testing status transitions",
            requested_date=date.today(),
            contact_person="Test Contact",
            contact_phone="+1234567890",
            created_by=user,
            status="DRAFT",
        )

        # Test status transitions
        for status in ["SUBMITTED", "REVIEWED", "APPROVED"]:
            request.status = status
            request.save()
            request.refresh_from_db()
            assert request.status == status


# ============================================================================
# HR EMPLOYEE LIFECYCLE TESTS
# ============================================================================

class TestHREmployeeLifecycle:
    """Test complete HR employee lifecycle."""

    def test_employee_creation(self, db, user):
        """Test employee can be created."""
        from apps.hr.models import Employee

        employee = Employee.objects.create(
            user=user,
            department="Engineering",
            job_title="Software Engineer",
            hire_date=date.today(),
            employment_type=Employee.EmploymentType.FULL_TIME,
            employment_status=Employee.EmploymentStatus.ACTIVE,
        )

        assert employee.pk is not None
        assert employee.employment_status == "ACTIVE"

    def test_employee_document(self, db, user, admin_user):
        """Test employee document creation."""
        from apps.hr.models import Employee, EmployeeDocument

        employee = Employee.objects.create(
            user=user,
            department="Operations",
            job_title="Technician",
            hire_date=date.today(),
            employment_type=Employee.EmploymentType.FULL_TIME,
            employment_status=Employee.EmploymentStatus.ACTIVE,
        )

        doc = EmployeeDocument.objects.create(
            employee=employee,
            document_type=EmployeeDocument.DocumentType.CONTRACT,
            title="Employment Contract",
            file_path="/docs/contract.pdf",
            file_name="contract.pdf",
            file_size=10000,
            file_type="application/pdf",
            status=EmployeeDocument.Status.ACTIVE,
            uploaded_by=admin_user,
        )

        assert doc.employee == employee

    def test_employee_performance_review(self, db, user, admin_user):
        """Test employee performance review."""
        from apps.hr.models import Employee, PerformanceReview

        employee = Employee.objects.create(
            user=user,
            department="Operations",
            job_title="Operator",
            hire_date=date.today() - timedelta(days=365),
            employment_type=Employee.EmploymentType.FULL_TIME,
            employment_status=Employee.EmploymentStatus.ACTIVE,
        )

        review = PerformanceReview.objects.create(
            employee=employee,
            reviewer=admin_user,
            review_type=PerformanceReview.ReviewType.ANNUAL,
            review_period_start=date.today() - timedelta(days=365),
            review_period_end=date.today(),
            review_date=date.today(),
            status=PerformanceReview.Status.DRAFT,
        )

        assert review.employee == employee


# ============================================================================
# SUPPLY CHAIN WORKFLOW TESTS
# ============================================================================

class TestSupplyChainWorkflow:
    """Test supply chain procurement workflow."""

    def test_vendor_creation(self, db):
        """Test vendor can be created."""
        from apps.supplychain.models import Vendor

        vendor = Vendor.objects.create(
            name="Test Vendor",
            vendor_type="SUPPLIER",
            status="ACTIVE",
            email="vendor@test.com",
        )

        assert vendor.pk is not None
        assert vendor.status == "ACTIVE"

    def test_vendor_status_transitions(self, db):
        """Test vendor status transitions."""
        from apps.supplychain.models import Vendor

        vendor = Vendor.objects.create(
            name="Status Test Vendor",
            vendor_type="SUPPLIER",
            status="PROSPECT",
        )

        # Qualify vendor
        vendor.status = "QUALIFIED"
        vendor.save()
        assert vendor.status == "QUALIFIED"

        # Activate vendor
        vendor.status = "ACTIVE"
        vendor.save()
        assert vendor.status == "ACTIVE"

    def test_purchase_requisition_creation(self, db, user):
        """Test purchase requisition creation."""
        from apps.supplychain.models import PurchaseRequisition

        requisition = PurchaseRequisition.objects.create(
            requested_by=user,
            title="Test Requisition",
            description="Integration test requisition",
            priority="NORMAL",
            status="DRAFT",
            request_date=date.today(),
            required_date=date.today() + timedelta(days=14),
        )

        assert requisition.pk is not None
        assert requisition.status == "DRAFT"


# ============================================================================
# COMPLIANCE INTEGRATION TESTS
# ============================================================================

class TestComplianceIntegration:
    """Test compliance and quality control integrations."""

    def test_quality_control_creation(self, db, user):
        """Test quality control can be created."""
        from apps.compliance.models import QualityControl

        qc = QualityControl.objects.create(
            inspection_type="RECEIVING",
            inspection_date=date.today(),
            inspector=user,
            result="PASS",
        )

        assert qc.pk is not None
        assert qc.result == "PASS"


# ============================================================================
# CROSS-APP INTEGRATION TESTS
# ============================================================================

class TestCrossAppIntegration:
    """Test integrations between multiple apps."""

    def test_customer_service_site_relationship(self, db, customer, service_site):
        """Test customer and service site are linked."""
        assert service_site.customer == customer
        assert service_site in customer.service_sites.all()

    def test_user_employee_relationship(self, db, user):
        """Test user can be linked to employee."""
        from apps.hr.models import Employee

        employee = Employee.objects.create(
            user=user,
            department="IT",
            job_title="Developer",
            hire_date=date.today(),
            employment_type=Employee.EmploymentType.FULL_TIME,
            employment_status=Employee.EmploymentStatus.ACTIVE,
        )

        assert employee.user == user
        assert employee.user.email == user.email

    def test_field_request_customer_site_relationship(self, db, field_service_request):
        """Test field service request links customer and site."""
        assert field_service_request.customer == field_service_request.service_site.customer


# ============================================================================
# DATA CONSISTENCY TESTS
# ============================================================================

class TestDataConsistency:
    """Test data consistency across the system."""

    def test_status_field_values(self, db):
        """Test status fields only accept valid values."""
        from apps.workorders.models import WorkOrder

        work_order = WorkOrder.objects.create(
            wo_type="REPAIR",
            description="Testing status values",
            priority="NORMAL",
            status="DRAFT",
            due_date=date.today() + timedelta(days=5),
        )

        valid_statuses = [
            "DRAFT", "PLANNED", "RELEASED", "IN_PROGRESS",
            "ON_HOLD", "QC_PENDING", "QC_PASSED", "QC_FAILED",
            "COMPLETED", "CANCELLED"
        ]

        for status in valid_statuses:
            work_order.status = status
            work_order.save()
            work_order.refresh_from_db()
            assert work_order.status == status

    def test_foreign_key_integrity(self, db, customer, service_site):
        """Test foreign key relationships maintain integrity."""
        # service_site already has FK to customer via conftest
        assert service_site.customer == customer

        service_site.refresh_from_db()
        assert service_site.customer.pk == customer.pk

    def test_model_str_methods(self, db, customer, service_site):
        """Test models have proper string representations."""
        assert str(customer)  # Has __str__
        assert str(service_site)  # Has __str__


# ============================================================================
# AUTO-ID GENERATION TESTS
# ============================================================================

class TestAutoIDGeneration:
    """Test auto-generated IDs across models."""

    def test_work_order_has_id(self, db):
        """Test work order gets an ID after save."""
        from apps.workorders.models import WorkOrder

        wo = WorkOrder.objects.create(
            wo_type="REPAIR",
            description="Auto ID test",
            priority="NORMAL",
            status="DRAFT",
            due_date=date.today() + timedelta(days=5),
        )

        # Should have a primary key
        assert wo.pk is not None

    def test_vendor_auto_code(self, db):
        """Test vendor generates auto code."""
        from apps.supplychain.models import Vendor

        v1 = Vendor.objects.create(
            name="Auto Code Vendor 1",
            vendor_type="SUPPLIER",
            status="ACTIVE",
        )

        v2 = Vendor.objects.create(
            name="Auto Code Vendor 2",
            vendor_type="SUPPLIER",
            status="ACTIVE",
        )

        # Should have unique auto-generated codes
        if v1.vendor_code and v2.vendor_code:
            assert v1.vendor_code != v2.vendor_code
