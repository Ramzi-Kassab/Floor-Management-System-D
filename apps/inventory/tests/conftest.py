"""
Inventory App Test Fixtures
"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.inventory.models import (
    InventoryCategory, InventoryLocation, InventoryItem,
    InventoryStock, InventoryTransaction
)

User = get_user_model()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )


@pytest.fixture
def inventory_category(db):
    """Create a test inventory category."""
    return InventoryCategory.objects.create(
        code='TOOLS',
        name='Tools & Equipment',
        description='Hand and power tools',
        is_active=True
    )


@pytest.fixture
def child_category(db, inventory_category):
    """Create a child category."""
    return InventoryCategory.objects.create(
        code='HAND-TOOLS',
        name='Hand Tools',
        parent=inventory_category,
        is_active=True
    )


@pytest.fixture
def warehouse(db):
    """Create a test warehouse."""
    from apps.sales.models import Warehouse
    return Warehouse.objects.create(
        code='WH001',
        name='Main Warehouse',
        is_active=True
    )


@pytest.fixture
def inventory_location(db, warehouse):
    """Create a test inventory location."""
    return InventoryLocation.objects.create(
        warehouse=warehouse,
        code='A-01-01',
        name='Aisle A Rack 1 Shelf 1',
        aisle='A',
        rack='01',
        shelf='01',
        bin='',
        is_active=True
    )


@pytest.fixture
def inventory_item(db, test_user, inventory_category):
    """Create a test inventory item."""
    return InventoryItem.objects.create(
        code='ITEM-001',
        name='Test Drill Bit',
        description='8mm carbide drill bit',
        item_type=InventoryItem.ItemType.TOOL,
        category=inventory_category,
        unit='EA',
        standard_cost=Decimal('25.00'),
        last_cost=Decimal('24.50'),
        currency='SAR',
        min_stock=Decimal('10'),
        max_stock=Decimal('100'),
        reorder_point=Decimal('15'),
        reorder_quantity=Decimal('50'),
        lead_time_days=7,
        is_active=True,
        is_serialized=False,
        is_lot_controlled=True,
        created_by=test_user
    )


@pytest.fixture
def inventory_stock(db, inventory_item, inventory_location):
    """Create a test inventory stock record."""
    return InventoryStock.objects.create(
        item=inventory_item,
        location=inventory_location,
        quantity_on_hand=Decimal('50.000'),
        quantity_reserved=Decimal('5.000'),
        lot_number='LOT-2024-001',
        expiry_date=date.today().replace(year=date.today().year + 1)
    )


@pytest.fixture
def inventory_transaction(db, test_user, inventory_item, inventory_location):
    """Create a test inventory transaction."""
    return InventoryTransaction.objects.create(
        transaction_number='TXN-001',
        transaction_type=InventoryTransaction.TransactionType.RECEIPT,
        transaction_date=timezone.now(),
        item=inventory_item,
        from_location=None,
        to_location=inventory_location,
        quantity=Decimal('50.000'),
        unit='EA',
        unit_cost=Decimal('24.50'),
        total_cost=Decimal('1225.00'),
        link_type=InventoryTransaction.LinkType.PURCHASE_ORDER,
        reference_number='PO-001',
        notes='Initial stock receipt',
        created_by=test_user
    )


# Fixtures for base class tests
@pytest.fixture
def test_object(inventory_item):
    """Default test object for base class tests."""
    return inventory_item


@pytest.fixture
def valid_data(inventory_category):
    """Valid data for item creation."""
    return {
        'code': 'ITEM-NEW',
        'name': 'New Item',
        'description': 'Test item',
        'item_type': InventoryItem.ItemType.TOOL,
        'category': inventory_category.pk if inventory_category else None,
        'unit': 'EA',
        'standard_cost': '10.00',
        'min_stock': '5',
        'is_active': True,
    }
