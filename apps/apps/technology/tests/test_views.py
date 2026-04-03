"""
Tests for Technology app views.
"""
import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from apps.common.tests.base import BaseCRUDTest

User = get_user_model()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def authenticated_client(client, test_user):
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def design(db, test_user):
    """Create a test design."""
    from apps.technology.models import Design
    return Design.objects.create(
        design_number='DES-001',
        name='Test Design',
        description='Test description',
        status='DRAFT',
        created_by=test_user
    )


@pytest.fixture
def bom(db, test_user):
    """Create a test BOM."""
    from apps.technology.models import BOM
    return BOM.objects.create(
        bom_number='BOM-001',
        name='Test BOM',
        description='Test description',
        status='DRAFT',
        created_by=test_user
    )


class TestDesignViews(BaseCRUDTest):
    """Tests for Design views."""

    app_name = 'technology'
    model_name = 'design'
    url_list = 'technology:design_list'
    url_detail = 'technology:design_detail'
    url_create = 'technology:design_create'
    url_update = 'technology:design_update'
    url_delete = None
    template_list = 'technology/design_list.html'
    template_detail = 'technology/design_detail.html'
    template_form = 'technology/design_form.html'
    test_delete = False

    @pytest.fixture
    def test_object(self, design):
        return design

    @pytest.fixture
    def valid_data(self):
        return {
            'design_number': 'DES-NEW',
            'name': 'New Design',
            'description': 'New description',
            'status': 'DRAFT',
        }


class TestCutterLayoutViews:
    """Tests for CutterLayout views."""

    def test_cutter_create_requires_login(self, client, design):
        url = reverse('technology:cutter_create', kwargs={'design_pk': design.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_cutter_create_authenticated(self, authenticated_client, design):
        url = reverse('technology:cutter_create', kwargs={'design_pk': design.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestBOMViews(BaseCRUDTest):
    """Tests for BOM views."""

    app_name = 'technology'
    model_name = 'bom'
    url_list = 'technology:bom_list'
    url_detail = 'technology:bom_detail'
    url_create = 'technology:bom_create'
    url_update = 'technology:bom_update'
    url_delete = None
    template_list = 'technology/bom_list.html'
    template_detail = 'technology/bom_detail.html'
    template_form = 'technology/bom_form.html'
    test_delete = False

    @pytest.fixture
    def test_object(self, bom):
        return bom

    @pytest.fixture
    def valid_data(self):
        return {
            'bom_number': 'BOM-NEW',
            'name': 'New BOM',
            'description': 'New description',
            'status': 'DRAFT',
        }


class TestBOMLineViews:
    """Tests for BOMLine views."""

    def test_bom_line_create_requires_login(self, client, bom):
        url = reverse('technology:bom_line_create', kwargs={'pk': bom.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_bom_line_create_authenticated(self, authenticated_client, bom):
        url = reverse('technology:bom_line_create', kwargs={'pk': bom.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200
