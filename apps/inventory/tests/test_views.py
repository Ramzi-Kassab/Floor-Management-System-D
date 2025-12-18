"""
Tests for Inventory app views.
"""
import pytest
from decimal import Decimal
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from apps.common.tests.base import BaseCRUDTest, BasePermissionTest
from apps.inventory.models import InventoryCategory, InventoryItem, InventoryStock

User = get_user_model()


# =============================================================================
# CATEGORY VIEWS
# =============================================================================

class TestCategoryViews:
    """Tests for InventoryCategory views."""

    def test_category_list_requires_login(self, client):
        """Test category list requires authentication."""
        url = reverse('inventory:category_list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url.lower()

    def test_category_list_authenticated(self, authenticated_client, inventory_category):
        """Test category list for authenticated users."""
        url = reverse('inventory:category_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_category_create_get(self, authenticated_client):
        """Test category create form."""
        url = reverse('inventory:category_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_category_update_get(self, authenticated_client, inventory_category):
        """Test category update form."""
        url = reverse('inventory:category_update', kwargs={'pk': inventory_category.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# LOCATION VIEWS
# =============================================================================

class TestLocationViews:
    """Tests for InventoryLocation views."""

    def test_location_list_requires_login(self, client):
        """Test location list requires authentication."""
        url = reverse('inventory:location_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_location_list_authenticated(self, authenticated_client, inventory_location):
        """Test location list for authenticated users."""
        url = reverse('inventory:location_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_location_create_get(self, authenticated_client):
        """Test location create form."""
        url = reverse('inventory:location_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_location_update_get(self, authenticated_client, inventory_location):
        """Test location update form."""
        url = reverse('inventory:location_update', kwargs={'pk': inventory_location.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# ITEM VIEWS
# =============================================================================

class TestItemViews(BaseCRUDTest):
    """Tests for InventoryItem views."""

    app_name = 'inventory'
    model_name = 'item'
    url_list = 'inventory:item_list'
    url_detail = 'inventory:item_detail'
    url_create = 'inventory:item_create'
    url_update = 'inventory:item_update'
    url_delete = None  # No delete view
    template_list = 'inventory/item_list.html'
    template_detail = 'inventory/item_detail.html'
    template_form = 'inventory/item_form.html'
    test_delete = False

    @pytest.fixture
    def test_object(self, inventory_item):
        """Use inventory item fixture as test object."""
        return inventory_item

    @pytest.fixture
    def valid_data(self, inventory_category):
        """Valid data for item creation."""
        return {
            'code': 'ITEM-NEW',
            'name': 'New Item',
            'description': 'Test item',
            'item_type': InventoryItem.ItemType.TOOL,
            'unit': 'EA',
            'standard_cost': '10.00',
            'min_stock': '5',
            'is_active': True,
        }

    def test_item_list_search(self, authenticated_client, inventory_item):
        """Test item list search functionality."""
        url = reverse(self.url_list)
        response = authenticated_client.get(url, {'q': 'Drill'})
        assert response.status_code == 200


# =============================================================================
# TRANSACTION VIEWS
# =============================================================================

class TestTransactionViews:
    """Tests for InventoryTransaction views."""

    def test_transaction_list_requires_login(self, client):
        """Test transaction list requires authentication."""
        url = reverse('inventory:transaction_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_transaction_list_authenticated(self, authenticated_client, inventory_transaction):
        """Test transaction list for authenticated users."""
        url = reverse('inventory:transaction_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_transaction_detail(self, authenticated_client, inventory_transaction):
        """Test transaction detail view."""
        url = reverse('inventory:transaction_detail', kwargs={'pk': inventory_transaction.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_transaction_create_get(self, authenticated_client):
        """Test transaction create form."""
        url = reverse('inventory:transaction_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# STOCK VIEWS
# =============================================================================

class TestStockViews:
    """Tests for InventoryStock views."""

    def test_stock_list_requires_login(self, client):
        """Test stock list requires authentication."""
        url = reverse('inventory:stock_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_stock_list_authenticated(self, authenticated_client, inventory_stock):
        """Test stock list for authenticated users."""
        url = reverse('inventory:stock_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_stock_adjust_requires_login(self, client, inventory_stock):
        """Test stock adjust requires authentication."""
        url = reverse('inventory:stock_adjust', kwargs={'pk': inventory_stock.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_stock_adjust_get(self, authenticated_client, inventory_stock):
        """Test stock adjust form."""
        url = reverse('inventory:stock_adjust', kwargs={'pk': inventory_stock.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# PERMISSION TESTS
# =============================================================================

class TestInventoryPermissions(BasePermissionTest):
    """Test inventory permissions."""

    url_name = 'inventory:item_list'

    def test_item_list_requires_auth(self, client):
        """Test item list requires authentication."""
        url = reverse(self.url_name)
        response = client.get(url)
        assert response.status_code == 302
