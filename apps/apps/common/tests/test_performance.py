"""
Performance Test Suite
ARDT Floor Management System - Phase 3 Day 5

Tests performance characteristics:
- Query optimization (N+1 prevention)
- Bulk operations
- Complex queries
"""

import pytest
import time
from decimal import Decimal
from datetime import date, timedelta
from django.db import connection, reset_queries
from django.test.utils import override_settings
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db

User = get_user_model()


class TestQueryOptimization:
    """Test query optimization patterns."""

    def test_vendor_list_query_count(self, db):
        """Test Vendor list doesn't cause N+1 queries."""
        from apps.supplychain.models import Vendor

        # Create test data one at a time (for auto-ID)
        for i in range(5):
            Vendor.objects.create(
                name=f"Query Test Vendor {i}",
                vendor_type="SUPPLIER",
                status="ACTIVE",
            )

        reset_queries()

        with override_settings(DEBUG=True):
            vendors = list(Vendor.objects.all()[:5])
            for v in vendors:
                _ = v.name
                _ = v.status

            query_count = len(connection.queries)

        # Simple model should only need 1-2 queries
        assert query_count <= 3, f"Too many queries: {query_count}"

    def test_employee_list_query_count(self, db, admin_user):
        """Test Employee list with related user doesn't cause N+1."""
        from apps.hr.models import Employee

        # Create employees
        for i in range(3):
            user = User.objects.create_user(
                username=f"perf_emp_{i}",
                email=f"perf{i}@test.com",
                password="testpass123",
            )
            Employee.objects.create(
                user=user,
                department="Engineering",
                job_title="Engineer",
                hire_date=date.today(),
                employment_type=Employee.EmploymentType.FULL_TIME,
                employment_status=Employee.EmploymentStatus.ACTIVE,
            )

        reset_queries()

        with override_settings(DEBUG=True):
            employees = list(
                Employee.objects.select_related('user').all()[:5]
            )
            for e in employees:
                _ = e.user.username  # Access related user

            query_count = len(connection.queries)

        # With select_related, should be minimal queries
        assert query_count <= 3, f"Too many queries: {query_count}"


class TestSingleRecordOperations:
    """Test single record operation performance."""

    def test_single_vendor_create(self, db):
        """Test single vendor create is fast."""
        from apps.supplychain.models import Vendor

        start_time = time.time()
        for i in range(10):
            Vendor.objects.create(
                name=f"Single Vendor {i}",
                vendor_type="SUPPLIER",
                status="ACTIVE",
            )
        elapsed = time.time() - start_time

        # 10 creates should be fast
        assert elapsed < 2.0, f"Creates too slow: {elapsed:.2f}s"
        assert Vendor.objects.count() >= 10

    def test_employee_create_with_related(self, db, admin_user):
        """Test employee creation with user is efficient."""
        from apps.hr.models import Employee

        start_time = time.time()
        for i in range(5):
            user = User.objects.create_user(
                username=f"create_emp_{i}",
                email=f"create{i}@test.com",
                password="testpass123",
            )
            Employee.objects.create(
                user=user,
                department="Operations",
                job_title="Technician",
                hire_date=date.today(),
                employment_type=Employee.EmploymentType.FULL_TIME,
                employment_status=Employee.EmploymentStatus.ACTIVE,
            )
        elapsed = time.time() - start_time

        assert elapsed < 3.0, f"Creates too slow: {elapsed:.2f}s"


class TestComplexQueries:
    """Test complex query performance."""

    def test_filtered_vendors(self, db):
        """Test filtering vendors by multiple criteria."""
        from apps.supplychain.models import Vendor

        # Create test data
        for i in range(20):
            Vendor.objects.create(
                name=f"Filter Vendor {i}",
                vendor_type="SUPPLIER" if i % 2 == 0 else "MANUFACTURER",
                status="ACTIVE" if i % 3 == 0 else "INACTIVE",
            )

        start_time = time.time()

        # Complex filter
        results = list(
            Vendor.objects.filter(
                vendor_type="SUPPLIER",
                status="ACTIVE",
            ).order_by('name')[:10]
        )

        elapsed = time.time() - start_time

        # Should complete in under 500ms
        assert elapsed < 0.5, f"Complex query too slow: {elapsed:.3f}s"

    def test_aggregation_query(self, db):
        """Test aggregation queries are efficient."""
        from apps.supplychain.models import Vendor
        from django.db.models import Count

        # Create test data
        for i in range(15):
            Vendor.objects.create(
                name=f"Agg Vendor {i}",
                vendor_type="SUPPLIER" if i % 2 == 0 else "MANUFACTURER",
                status="ACTIVE",
            )

        start_time = time.time()

        # Aggregation query
        counts = Vendor.objects.values('vendor_type').annotate(count=Count('id'))
        list(counts)  # Execute query

        elapsed = time.time() - start_time

        assert elapsed < 0.5, f"Aggregation query too slow: {elapsed:.3f}s"


class TestDatabaseIndexing:
    """Test that indexes are being used."""

    def test_primary_key_lookup(self, db):
        """Test primary key lookups are fast."""
        from apps.supplychain.models import Vendor

        vendor = Vendor.objects.create(
            name="PK Lookup Vendor",
            vendor_type="SUPPLIER",
            status="ACTIVE",
        )

        start_time = time.time()
        for _ in range(100):
            Vendor.objects.get(pk=vendor.pk)
        elapsed = time.time() - start_time

        # 100 PK lookups should be very fast
        assert elapsed < 1.0, f"PK lookups too slow: {elapsed:.3f}s"

    def test_status_filter(self, db):
        """Test status field filtering is efficient."""
        from apps.supplychain.models import Vendor

        # Create test data
        for i in range(20):
            Vendor.objects.create(
                name=f"Status Filter Vendor {i}",
                vendor_type="SUPPLIER",
                status="ACTIVE" if i < 10 else "INACTIVE",
            )

        start_time = time.time()
        active_count = Vendor.objects.filter(status="ACTIVE").count()
        elapsed = time.time() - start_time

        assert active_count >= 10
        assert elapsed < 0.1, f"Status filter too slow: {elapsed:.3f}s"


class TestQueryCounting:
    """Test query counting for optimization verification."""

    def test_customer_site_prefetch(self, db):
        """Test customer with sites uses prefetch_related efficiently."""
        from apps.sales.models import Customer, ServiceSite

        # Create customer with sites
        customer = Customer.objects.create(
            code="PERF-CUST-001",
            name="Prefetch Test Customer",
            customer_type="OPERATOR",
            is_active=True,
        )

        for i in range(3):
            ServiceSite.objects.create(
                site_code=f"PERF-SITE-{i}",
                name=f"Prefetch Test Site {i}",
                customer=customer,
                site_type="RIG_SITE",
                address_line1="123 Test St",
                city="Test City",
                country="Saudi Arabia",
                is_active=True,
            )

        reset_queries()

        with override_settings(DEBUG=True):
            # With prefetch_related
            customers = list(
                Customer.objects.prefetch_related('service_sites').filter(
                    code="PERF-CUST-001"
                )
            )
            for c in customers:
                sites = list(c.service_sites.all())  # Should use cached data

            query_count = len(connection.queries)

        # Should be 2 queries: 1 for customers, 1 for sites
        assert query_count <= 3, f"Too many queries: {query_count}"
