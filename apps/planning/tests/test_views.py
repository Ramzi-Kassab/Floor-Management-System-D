"""
Tests for Planning app views using base test classes.
"""
import pytest
from datetime import date, timedelta
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from apps.common.tests.base import BaseCRUDTest, BasePermissionTest
from apps.planning.models import Sprint, PlanningBoard, PlanningItem, WikiSpace, WikiPage

User = get_user_model()


# =============================================================================
# SPRINT VIEWS
# =============================================================================

class TestSprintViews(BaseCRUDTest):
    """Tests for Sprint views using base CRUD test class."""

    app_name = 'planning'
    model_name = 'sprint'
    url_list = 'planning:sprint_list'
    url_detail = 'planning:sprint_detail'
    url_create = 'planning:sprint_create'
    url_update = 'planning:sprint_update'
    url_delete = 'planning:sprint_delete'
    template_list = 'planning/sprint_list.html'
    template_detail = 'planning/sprint_detail.html'
    template_form = 'planning/sprint_form.html'

    @pytest.fixture
    def test_object(self, sprint):
        """Use sprint fixture as test object."""
        return sprint

    @pytest.fixture
    def valid_data(self, test_user):
        """Valid data for sprint creation."""
        return {
            'name': 'New Sprint',
            'code': 'SPRINT-NEW',
            'goal': 'Complete features',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=14),
            'status': Sprint.Status.PLANNING,
            'capacity_points': 40,
        }

    def test_sprint_list_filter_by_status(self, authenticated_client, sprint):
        """Test sprint list filtering by status."""
        url = reverse(self.url_list)
        response = authenticated_client.get(url, {'status': 'ACTIVE'})
        assert response.status_code == 200


# =============================================================================
# BOARD VIEWS
# =============================================================================

class TestBoardViews(BaseCRUDTest):
    """Tests for PlanningBoard views."""

    app_name = 'planning'
    model_name = 'board'
    url_list = 'planning:board_list'
    url_detail = 'planning:board_detail'
    url_create = 'planning:board_create'
    url_update = 'planning:board_update'
    url_delete = 'planning:board_delete'
    template_list = 'planning/board_list.html'
    template_detail = 'planning/board_detail.html'
    template_form = 'planning/board_form.html'

    @pytest.fixture
    def test_object(self, planning_board):
        """Use planning board fixture as test object."""
        return planning_board

    @pytest.fixture
    def valid_data(self):
        """Valid data for board creation."""
        return {
            'name': 'New Board',
            'code': 'NEW-BOARD',
            'description': 'Test description',
            'is_active': True,
            'default_wip_limit': 5,
        }


# =============================================================================
# ITEM VIEWS
# =============================================================================

class TestItemViews(BaseCRUDTest):
    """Tests for PlanningItem views."""

    app_name = 'planning'
    model_name = 'item'
    url_list = 'planning:item_list'
    url_detail = 'planning:item_detail'
    url_create = 'planning:item_create'
    url_update = 'planning:item_update'
    url_delete = 'planning:item_delete'
    template_list = 'planning/item_list.html'
    template_detail = 'planning/item_detail.html'
    template_form = 'planning/item_form.html'

    @pytest.fixture
    def test_object(self, planning_item):
        """Use planning item fixture as test object."""
        return planning_item

    @pytest.fixture
    def valid_data(self):
        """Valid data for item creation."""
        return {
            'code': 'ARDT-NEW',
            'title': 'New Task',
            'description': 'Task description',
            'item_type': PlanningItem.ItemType.TASK,
            'priority': PlanningItem.Priority.MEDIUM,
        }


# =============================================================================
# LABEL VIEWS
# =============================================================================

class TestLabelViews:
    """Tests for PlanningLabel views."""

    def test_label_list_requires_login(self, client):
        """Test label list requires authentication."""
        url = reverse('planning:label_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_label_list_authenticated(self, authenticated_client, planning_label):
        """Test label list for authenticated users."""
        url = reverse('planning:label_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_label_create_get(self, authenticated_client):
        """Test label create form."""
        url = reverse('planning:label_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_label_update_get(self, authenticated_client, planning_label):
        """Test label update form."""
        url = reverse('planning:label_update', kwargs={'pk': planning_label.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# COLUMN VIEWS
# =============================================================================

class TestColumnViews:
    """Tests for PlanningColumn views."""

    def test_column_create_requires_login(self, client):
        """Test column create requires authentication."""
        url = reverse('planning:column_create')
        response = client.get(url)
        assert response.status_code == 302

    def test_column_create_get(self, authenticated_client):
        """Test column create form."""
        url = reverse('planning:column_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_column_update_get(self, authenticated_client, planning_column):
        """Test column update form."""
        url = reverse('planning:column_update', kwargs={'pk': planning_column.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


# =============================================================================
# WIKI SPACE VIEWS
# =============================================================================

class TestWikiSpaceViews(BaseCRUDTest):
    """Tests for WikiSpace views."""

    app_name = 'planning'
    model_name = 'wiki_space'
    url_list = 'planning:wiki_list'
    url_detail = 'planning:wiki_space_detail'
    url_create = 'planning:wiki_space_create'
    url_update = 'planning:wiki_space_update'
    url_delete = 'planning:wiki_space_delete'
    template_list = 'planning/wiki_list.html'
    template_detail = 'planning/wiki_space_detail.html'
    template_form = 'planning/wiki_space_form.html'

    @pytest.fixture
    def test_object(self, wiki_space):
        """Use wiki space fixture as test object."""
        return wiki_space

    @pytest.fixture
    def valid_data(self):
        """Valid data for wiki space creation."""
        return {
            'code': 'WIKI-NEW',
            'name': 'New Wiki Space',
            'description': 'Test wiki space',
            'is_public': True,
        }


# =============================================================================
# WIKI PAGE VIEWS
# =============================================================================

class TestWikiPageViews:
    """Tests for WikiPage views."""

    def test_wiki_page_detail_requires_login(self, client, wiki_page):
        """Test wiki page detail requires authentication."""
        url = reverse('planning:wiki_page_detail', kwargs={'pk': wiki_page.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_wiki_page_detail_authenticated(self, authenticated_client, wiki_page):
        """Test wiki page detail for authenticated users."""
        url = reverse('planning:wiki_page_detail', kwargs={'pk': wiki_page.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_wiki_page_create_get(self, authenticated_client):
        """Test wiki page create form."""
        url = reverse('planning:wiki_page_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_wiki_page_update_get(self, authenticated_client, wiki_page):
        """Test wiki page update form."""
        url = reverse('planning:wiki_page_update', kwargs={'pk': wiki_page.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_wiki_page_not_found(self, authenticated_client):
        """Test wiki page 404."""
        url = reverse('planning:wiki_page_detail', kwargs={'pk': 99999})
        response = authenticated_client.get(url)
        assert response.status_code == 404


# =============================================================================
# PERMISSION TESTS
# =============================================================================

class TestSprintPermissions(BasePermissionTest):
    """Test sprint permissions."""

    url_name = 'planning:sprint_list'

    def test_sprint_list_requires_auth(self, client):
        """Test sprint list requires authentication."""
        url = reverse(self.url_name)
        response = client.get(url)
        assert response.status_code == 302


class TestBoardPermissions(BasePermissionTest):
    """Test board permissions."""

    url_name = 'planning:board_list'

    def test_board_list_requires_auth(self, client):
        """Test board list requires authentication."""
        url = reverse(self.url_name)
        response = client.get(url)
        assert response.status_code == 302


class TestItemPermissions(BasePermissionTest):
    """Test item permissions."""

    url_name = 'planning:item_list'

    def test_item_list_requires_auth(self, client):
        """Test item list requires authentication."""
        url = reverse(self.url_name)
        response = client.get(url)
        assert response.status_code == 302
