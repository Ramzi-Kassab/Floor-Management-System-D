"""
Tests for Inventory app models.
"""
import pytest
from decimal import Decimal
from datetime import date
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.inventory.models import (
    InventoryCategory, InventoryLocation, InventoryItem,
    InventoryStock, InventoryTransaction
)

User = get_user_model()


class TestInventoryCategoryModel:
    """Tests for InventoryCategory model."""

    def test_create_category(self, db):
        """Test creating an inventory category."""
        category = InventoryCategory.objects.create(
            code='PARTS',
            name='Spare Parts',
            description='Replacement parts',
            is_active=True
        )
        assert category.pk is not None
        assert category.code == 'PARTS'

    def test_category_str(self, inventory_category):
        """Test category string representation."""
        assert 'TOOLS' in str(inventory_category)
        assert 'Tools & Equipment' in str(inventory_category)

    def test_category_hierarchy(self, inventory_category, child_category):
        """Test category parent-child relationship."""
        assert child_category.parent == inventory_category
        assert child_category in inventory_category.children.all()

    def test_category_unique_code(self, db, inventory_category):
        """Test category code uniqueness."""
        with pytest.raises(Exception):
            InventoryCategory.objects.create(
                code='TOOLS',  # Duplicate
                name='Another Tools'
            )


class TestInventoryLocationModel:
    """Tests for InventoryLocation model."""

    def test_create_location(self, db, warehouse):
        """Test creating an inventory location."""
        location = InventoryLocation.objects.create(
            warehouse=warehouse,
            code='B-02-03',
            name='Aisle B Rack 2 Shelf 3',
            aisle='B',
            rack='02',
            shelf='03'
        )
        assert location.pk is not None
        assert location.code == 'B-02-03'

    def test_location_str(self, inventory_location, warehouse):
        """Test location string representation."""
        result = str(inventory_location)
        assert warehouse.code in result
        assert 'A-01-01' in result

    def test_location_unique_in_warehouse(self, db, warehouse, inventory_location):
        """Test location code unique within warehouse."""
        with pytest.raises(Exception):
            InventoryLocation.objects.create(
                warehouse=warehouse,
                code='A-01-01',  # Duplicate in same warehouse
                name='Duplicate'
            )


class TestInventoryItemModel:
    """Tests for InventoryItem model."""

    def test_create_item(self, db, test_user):
        """Test creating an inventory item."""
        item = InventoryItem.objects.create(
            code='TEST-ITEM',
            name='Test Item',
            item_type=InventoryItem.ItemType.CONSUMABLE,
            unit='EA',
            created_by=test_user
        )
        assert item.pk is not None
        assert item.code == 'TEST-ITEM'

    def test_item_str(self, inventory_item):
        """Test item string representation."""
        assert 'ITEM-001' in str(inventory_item)
        assert 'Test Drill Bit' in str(inventory_item)

    def test_item_type_choices(self, db, test_user):
        """Test item type choices."""
        for item_type, _ in InventoryItem.ItemType.choices:
            item = InventoryItem.objects.create(
                code=f'ITEM-{item_type}',
                name=f'Test {item_type}',
                item_type=item_type,
                unit='EA',
                created_by=test_user
            )
            assert item.item_type == item_type

    def test_item_total_stock_property(self, inventory_item, inventory_stock):
        """Test item total stock calculation."""
        total = inventory_item.total_stock
        assert total == Decimal('50.000')

    def test_item_with_no_stock(self, db, test_user):
        """Test item with no stock records."""
        item = InventoryItem.objects.create(
            code='NO-STOCK',
            name='No Stock Item',
            item_type=InventoryItem.ItemType.TOOL,
            unit='EA',
            created_by=test_user
        )
        assert item.total_stock == 0

    def test_item_unique_code(self, db, inventory_item, test_user):
        """Test item code uniqueness."""
        with pytest.raises(Exception):
            InventoryItem.objects.create(
                code='ITEM-001',  # Duplicate
                name='Another Item',
                item_type=InventoryItem.ItemType.TOOL,
                unit='EA',
                created_by=test_user
            )


class TestInventoryStockModel:
    """Tests for InventoryStock model."""

    def test_create_stock(self, db, inventory_item, inventory_location):
        """Test creating an inventory stock record."""
        stock = InventoryStock.objects.create(
            item=inventory_item,
            location=inventory_location,
            quantity_on_hand=Decimal('100.000'),
            quantity_reserved=Decimal('10.000')
        )
        assert stock.pk is not None
        assert stock.quantity_available == Decimal('90.000')

    def test_stock_str(self, inventory_stock):
        """Test stock string representation."""
        result = str(inventory_stock)
        assert 'ITEM-001' in result
        assert '50' in result

    def test_stock_available_calculation(self, db, inventory_item, inventory_location):
        """Test quantity available auto-calculation."""
        stock = InventoryStock.objects.create(
            item=inventory_item,
            location=inventory_location,
            quantity_on_hand=Decimal('75.000'),
            quantity_reserved=Decimal('25.000'),
            lot_number='LOT-TEST'
        )
        assert stock.quantity_available == Decimal('50.000')

    def test_stock_with_lot_number(self, inventory_stock):
        """Test stock with lot tracking."""
        assert inventory_stock.lot_number == 'LOT-2024-001'
        assert inventory_stock.expiry_date is not None

    def test_stock_update_available(self, inventory_stock):
        """Test updating stock recalculates available."""
        inventory_stock.quantity_reserved = Decimal('20.000')
        inventory_stock.save()
        inventory_stock.refresh_from_db()
        assert inventory_stock.quantity_available == Decimal('30.000')


class TestInventoryTransactionModel:
    """Tests for InventoryTransaction model."""

    def test_create_transaction(self, db, test_user, inventory_item, inventory_location):
        """Test creating an inventory transaction."""
        txn = InventoryTransaction.objects.create(
            transaction_number='TXN-TEST',
            transaction_type=InventoryTransaction.TransactionType.RECEIPT,
            transaction_date=timezone.now(),
            item=inventory_item,
            to_location=inventory_location,
            quantity=Decimal('25.000'),
            unit_cost=Decimal('10.00'),
            total_cost=Decimal('250.00'),
            performed_by=test_user
        )
        assert txn.pk is not None
        assert txn.transaction_number == 'TXN-TEST'

    def test_transaction_type_choices(self, db, test_user, inventory_item, inventory_location):
        """Test transaction type choices."""
        for i, (txn_type, _) in enumerate(InventoryTransaction.TransactionType.choices):
            txn = InventoryTransaction.objects.create(
                transaction_number=f'TXN-{i}',
                transaction_type=txn_type,
                transaction_date=timezone.now(),
                item=inventory_item,
                to_location=inventory_location,
                quantity=Decimal('10.000'),
                performed_by=test_user
            )
            assert txn.transaction_type == txn_type

    def test_transaction_unique_number(self, db, inventory_transaction, test_user, inventory_item, inventory_location):
        """Test transaction number uniqueness."""
        with pytest.raises(Exception):
            InventoryTransaction.objects.create(
                transaction_number='TXN-001',  # Duplicate
                transaction_type=InventoryTransaction.TransactionType.ISSUE,
                transaction_date=timezone.now(),
                item=inventory_item,
                to_location=inventory_location,
                quantity=Decimal('5.000'),
                performed_by=test_user
            )

    def test_transfer_transaction(self, db, test_user, inventory_item, inventory_location, warehouse):
        """Test transfer transaction with from and to locations."""
        to_location = InventoryLocation.objects.create(
            warehouse=warehouse,
            code='C-01-01',
            name='Destination'
        )
        txn = InventoryTransaction.objects.create(
            transaction_number='TXN-TRANSFER',
            transaction_type=InventoryTransaction.TransactionType.TRANSFER,
            transaction_date=timezone.now(),
            item=inventory_item,
            from_location=inventory_location,
            to_location=to_location,
            quantity=Decimal('10.000'),
            performed_by=test_user
        )
        assert txn.from_location == inventory_location
        assert txn.to_location == to_location
