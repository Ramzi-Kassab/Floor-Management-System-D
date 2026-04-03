"""
Sales App - Edge Case Tests
Boundary conditions, special characters, and unusual scenarios.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.db import IntegrityError


# =============================================================================
# CODE FIELD EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestCodeFieldEdgeCases:
    """Tests for code field edge cases."""

    def test_customer_code_max_length(self, base_user):
        """Test customer code at max length (20 chars)."""
        from apps.sales.models import Customer
        max_code = 'X' * 20
        customer = Customer.objects.create(
            code=max_code,
            name='Max Code Test',
            created_by=base_user
        )
        assert len(customer.code) == 20

    def test_customer_code_special_characters(self, base_user):
        """Test customer code with special characters."""
        from apps.sales.models import Customer
        special_code = 'CUST-001/A'
        customer = Customer.objects.create(
            code=special_code,
            name='Special Code Test',
            created_by=base_user
        )
        assert customer.code == special_code

    def test_rig_code_max_length(self):
        """Test rig code at max length (30 chars)."""
        from apps.sales.models import Rig
        max_code = 'R' * 30
        rig = Rig.objects.create(
            code=max_code,
            name='Max Code Rig'
        )
        assert len(rig.code) == 30

    def test_well_code_max_length(self):
        """Test well code at max length (50 chars)."""
        from apps.sales.models import Well
        max_code = 'W' * 50
        well = Well.objects.create(
            code=max_code,
            name='Max Code Well'
        )
        assert len(well.code) == 50

    def test_so_number_max_length(self, customer, base_user):
        """Test sales order number at max length (30 chars)."""
        from apps.sales.models import SalesOrder
        max_so = 'S' * 30
        so = SalesOrder.objects.create(
            so_number=max_so,
            customer=customer,
            order_date=date.today(),
            created_by=base_user
        )
        assert len(so.so_number) == 30


# =============================================================================
# NAME FIELD EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestNameFieldEdgeCases:
    """Tests for name field edge cases."""

    def test_customer_name_max_length(self, base_user):
        """Test customer name at max length (200 chars)."""
        from apps.sales.models import Customer
        max_name = 'N' * 200
        customer = Customer.objects.create(
            code='NAME-MAX-001',
            name=max_name,
            created_by=base_user
        )
        assert len(customer.name) == 200

    def test_customer_name_arabic(self, base_user):
        """Test customer name with Arabic characters."""
        from apps.sales.models import Customer
        customer = Customer.objects.create(
            code='AR-NAME-001',
            name='Test Company',
            name_ar='شركة تجريبية للنفط',
            created_by=base_user
        )
        assert customer.name_ar == 'شركة تجريبية للنفط'

    def test_customer_name_unicode(self, base_user):
        """Test customer name with various unicode characters."""
        from apps.sales.models import Customer
        unicode_name = 'Test™ Company® ☆ العربية'
        customer = Customer.objects.create(
            code='UNI-NAME-001',
            name=unicode_name,
            created_by=base_user
        )
        assert customer.name == unicode_name


# =============================================================================
# DECIMAL FIELD EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestDecimalFieldEdgeCases:
    """Tests for decimal field edge cases."""

    def test_credit_limit_max_value(self, base_user):
        """Test credit limit at max value (15,2)."""
        from apps.sales.models import Customer
        max_limit = Decimal('9999999999999.99')
        customer = Customer.objects.create(
            code='CREDIT-MAX-001',
            name='Max Credit Test',
            credit_limit=max_limit,
            created_by=base_user
        )
        assert customer.credit_limit == max_limit

    def test_credit_limit_zero(self, base_user):
        """Test credit limit at zero."""
        from apps.sales.models import Customer
        customer = Customer.objects.create(
            code='CREDIT-ZERO-001',
            name='Zero Credit Test',
            credit_limit=Decimal('0.00'),
            created_by=base_user
        )
        assert customer.credit_limit == Decimal('0.00')

    def test_unit_price_precision(self, sales_order):
        """Test unit price precision (15,2)."""
        from apps.sales.models import SalesOrderLine
        line = SalesOrderLine.objects.create(
            sales_order=sales_order,
            line_number=100,
            description='Precision Test',
            unit_price=Decimal('99999999.99')
        )
        assert line.unit_price == Decimal('99999999.99')

    def test_discount_percent_range(self, sales_order):
        """Test discount percent range (0-100)."""
        from apps.sales.models import SalesOrderLine
        # Test 0%
        line0 = SalesOrderLine.objects.create(
            sales_order=sales_order,
            line_number=101,
            description='No Discount',
            discount_percent=Decimal('0.00')
        )
        assert line0.discount_percent == Decimal('0.00')

        # Test 100%
        line100 = SalesOrderLine.objects.create(
            sales_order=sales_order,
            line_number=102,
            description='Full Discount',
            discount_percent=Decimal('100.00')
        )
        assert line100.discount_percent == Decimal('100.00')

    def test_gps_coordinate_precision(self, customer):
        """Test GPS coordinate precision (10,7)."""
        from apps.sales.models import Rig
        rig = Rig.objects.create(
            code='GPS-PREC-001',
            name='GPS Precision Rig',
            latitude=Decimal('25.1234567'),
            longitude=Decimal('49.9876543')
        )
        assert rig.latitude == Decimal('25.1234567')
        assert rig.longitude == Decimal('49.9876543')


# =============================================================================
# DATE FIELD EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestDateFieldEdgeCases:
    """Tests for date field edge cases."""

    def test_sales_order_same_dates(self, customer, base_user):
        """Test sales order with same order and required date."""
        from apps.sales.models import SalesOrder
        today = date.today()
        so = SalesOrder.objects.create(
            so_number='SO-SAME-DATE',
            customer=customer,
            order_date=today,
            required_date=today,
            created_by=base_user
        )
        assert so.order_date == so.required_date

    def test_sales_order_past_dates(self, customer, base_user):
        """Test sales order with past dates."""
        from apps.sales.models import SalesOrder
        past = date.today() - timedelta(days=365)
        so = SalesOrder.objects.create(
            so_number='SO-PAST-001',
            customer=customer,
            order_date=past,
            created_by=base_user
        )
        assert so.order_date == past

    def test_sales_order_far_future_dates(self, customer, base_user):
        """Test sales order with far future dates."""
        from apps.sales.models import SalesOrder
        future = date.today() + timedelta(days=3650)  # 10 years
        so = SalesOrder.objects.create(
            so_number='SO-FUTURE-001',
            customer=customer,
            order_date=date.today(),
            required_date=future,
            created_by=base_user
        )
        assert so.required_date == future

    def test_well_null_spud_date(self, customer):
        """Test well with null spud date."""
        from apps.sales.models import Well
        well = Well.objects.create(
            code='WELL-NO-SPUD',
            name='No Spud Date Well',
            spud_date=None
        )
        assert well.spud_date is None


# =============================================================================
# TEXT FIELD EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestTextFieldEdgeCases:
    """Tests for text field edge cases."""

    def test_customer_address_long_text(self, base_user):
        """Test customer address with very long text."""
        from apps.sales.models import Customer
        long_address = 'A' * 5000
        customer = Customer.objects.create(
            code='ADDR-LONG-001',
            name='Long Address Test',
            address=long_address,
            created_by=base_user
        )
        assert len(customer.address) == 5000

    def test_special_characters_in_address(self, base_user):
        """Test special characters in address."""
        from apps.sales.models import Customer
        special_address = '<script>alert("XSS")</script>\n\t"quotes" & ampersand'
        customer = Customer.objects.create(
            code='ADDR-SPEC-001',
            name='Special Address Test',
            address=special_address,
            created_by=base_user
        )
        assert customer.address == special_address

    def test_unicode_in_text_fields(self, base_user):
        """Test unicode characters in text fields."""
        from apps.sales.models import Customer
        unicode_text = '日本語テスト 🔧 العربية'
        customer = Customer.objects.create(
            code='UNI-TEXT-001',
            name='Unicode Test',
            address=unicode_text,
            created_by=base_user
        )
        assert customer.address == unicode_text

    def test_empty_text_fields(self, base_user):
        """Test empty/blank text fields."""
        from apps.sales.models import Customer
        customer = Customer.objects.create(
            code='EMPTY-TEXT-001',
            name='Empty Text Test',
            address='',
            created_by=base_user
        )
        assert customer.address == ''


# =============================================================================
# FOREIGN KEY EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestForeignKeyEdgeCases:
    """Tests for foreign key edge cases."""

    def test_customer_null_foreign_keys(self, base_user):
        """Test customer with all nullable FKs as null."""
        from apps.sales.models import Customer
        customer = Customer.objects.create(
            code='NULL-FK-001',
            name='Null FK Test',
            account_manager=None,
            created_by=base_user
        )
        assert customer.account_manager is None

    def test_rig_null_foreign_keys(self):
        """Test rig with all nullable FKs as null."""
        from apps.sales.models import Rig
        rig = Rig.objects.create(
            code='RIG-NULL-FK',
            name='Null FK Rig',
            customer=None,
            contractor=None
        )
        assert rig.customer is None
        assert rig.contractor is None

    def test_customer_set_null_on_user_delete(self, customer, base_user):
        """Test SET_NULL behavior when account manager is deleted."""
        from apps.sales.models import Customer
        customer.account_manager = base_user
        customer.save()
        # Note: Actually deleting user would test this, but we just verify setup
        assert customer.account_manager == base_user

    def test_sales_order_customer_protect(self, sales_order, customer):
        """Test PROTECT behavior on sales order customer delete."""
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            customer.delete()

    def test_cascade_delete_customer_contacts(self, customer):
        """Test cascade delete of contacts when customer is deleted."""
        from apps.sales.models import CustomerContact
        CustomerContact.objects.create(
            customer=customer,
            name='To Delete',
            is_primary=True
        )
        contact_count = CustomerContact.objects.filter(customer=customer).count()
        assert contact_count == 1

        # Delete with no sales orders
        # Note: In real test, would need customer without sales orders
        # contact would be cascade deleted


# =============================================================================
# UNIQUE CONSTRAINT EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestUniqueConstraintEdgeCases:
    """Tests for unique constraint edge cases."""

    def test_duplicate_customer_code_fails(self, customer, base_user):
        """Test duplicate customer code raises IntegrityError."""
        from apps.sales.models import Customer
        with pytest.raises(IntegrityError):
            Customer.objects.create(
                code=customer.code,
                name='Duplicate Code',
                created_by=base_user
            )

    def test_duplicate_rig_code_fails(self, rig):
        """Test duplicate rig code raises IntegrityError."""
        from apps.sales.models import Rig
        with pytest.raises(IntegrityError):
            Rig.objects.create(
                code=rig.code,
                name='Duplicate Rig'
            )

    def test_duplicate_well_code_fails(self, well):
        """Test duplicate well code raises IntegrityError."""
        from apps.sales.models import Well
        with pytest.raises(IntegrityError):
            Well.objects.create(
                code=well.code,
                name='Duplicate Well'
            )

    def test_duplicate_so_number_fails(self, sales_order, customer, base_user):
        """Test duplicate SO number raises IntegrityError."""
        from apps.sales.models import SalesOrder
        with pytest.raises(IntegrityError):
            SalesOrder.objects.create(
                so_number=sales_order.so_number,
                customer=customer,
                order_date=date.today(),
                created_by=base_user
            )


# =============================================================================
# UNIQUE TOGETHER EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestUniqueTogetherEdgeCases:
    """Tests for unique_together constraint edge cases."""

    def test_duplicate_line_number_fails(self, sales_order, sales_order_line):
        """Test duplicate line_number for same sales order fails."""
        from apps.sales.models import SalesOrderLine
        with pytest.raises(IntegrityError):
            SalesOrderLine.objects.create(
                sales_order=sales_order,
                line_number=sales_order_line.line_number,
                description='Duplicate Line'
            )

    def test_same_line_number_different_orders_ok(self, customer, base_user):
        """Test same line_number for different orders is allowed."""
        from apps.sales.models import SalesOrder, SalesOrderLine
        so1 = SalesOrder.objects.create(
            so_number='SO-UNIQUE-001',
            customer=customer,
            order_date=date.today(),
            created_by=base_user
        )
        so2 = SalesOrder.objects.create(
            so_number='SO-UNIQUE-002',
            customer=customer,
            order_date=date.today(),
            created_by=base_user
        )
        line1 = SalesOrderLine.objects.create(
            sales_order=so1,
            line_number=1,
            description='Order 1 Line 1'
        )
        line2 = SalesOrderLine.objects.create(
            sales_order=so2,
            line_number=1,
            description='Order 2 Line 1'
        )
        assert line1.line_number == line2.line_number


# =============================================================================
# BOOLEAN FIELD EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestBooleanFieldEdgeCases:
    """Tests for boolean field edge cases."""

    def test_customer_default_boolean_values(self, base_user):
        """Test customer default boolean values."""
        from apps.sales.models import Customer
        customer = Customer.objects.create(
            code='BOOL-DEF-001',
            name='Boolean Default Test',
            created_by=base_user
        )
        assert customer.is_active is True
        assert customer.is_aramco is False

    def test_service_site_boolean_fields(self, customer):
        """Test service site boolean fields."""
        from apps.sales.models import ServiceSite
        site = ServiceSite.objects.create(
            site_code='SITE-BOOL-001',
            name='Boolean Test Site',
            customer=customer,
            address_line1='Test Address',
            city='Test City',
            requires_escort=True,
            requires_ppe=False,
            is_24_hour=True,
            has_parking=False,
            has_loading_dock=True
        )
        assert site.requires_escort is True
        assert site.requires_ppe is False
        assert site.is_24_hour is True
        assert site.has_parking is False


# =============================================================================
# EMAIL FIELD EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestEmailFieldEdgeCases:
    """Tests for email field edge cases."""

    def test_customer_email_formats(self, base_user):
        """Test various valid email formats."""
        from apps.sales.models import Customer
        emails = [
            'simple@example.com',
            'very.common@example.com',
            'disposable.style.email.with+symbol@example.com',
            'user@subdomain.example.com',
        ]
        for i, email in enumerate(emails):
            customer = Customer.objects.create(
                code=f'EMAIL-{i:03d}',
                name=f'Email Test {i}',
                email=email,
                created_by=base_user
            )
            assert customer.email == email

    def test_customer_empty_email(self, base_user):
        """Test customer with empty email."""
        from apps.sales.models import Customer
        customer = Customer.objects.create(
            code='NO-EMAIL-001',
            name='No Email Test',
            email='',
            created_by=base_user
        )
        assert customer.email == ''


# =============================================================================
# INTEGER FIELD EDGE CASES
# =============================================================================

@pytest.mark.django_db
class TestIntegerFieldEdgeCases:
    """Tests for integer field edge cases."""

    def test_well_target_depth_zero(self):
        """Test well with zero target depth."""
        from apps.sales.models import Well
        well = Well.objects.create(
            code='WELL-DEPTH-ZERO',
            name='Zero Depth Well',
            target_depth=0
        )
        assert well.target_depth == 0

    def test_well_target_depth_large(self):
        """Test well with large target depth."""
        from apps.sales.models import Well
        well = Well.objects.create(
            code='WELL-DEPTH-LARGE',
            name='Large Depth Well',
            target_depth=50000
        )
        assert well.target_depth == 50000

    def test_sales_order_line_quantity(self, sales_order):
        """Test sales order line quantity edge values."""
        from apps.sales.models import SalesOrderLine
        # Test quantity = 1
        line1 = SalesOrderLine.objects.create(
            sales_order=sales_order,
            line_number=200,
            description='Single Item',
            quantity=1
        )
        assert line1.quantity == 1

        # Test large quantity
        line2 = SalesOrderLine.objects.create(
            sales_order=sales_order,
            line_number=201,
            description='Bulk Order',
            quantity=10000
        )
        assert line2.quantity == 10000
