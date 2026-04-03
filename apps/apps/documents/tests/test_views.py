"""
Tests for Documents app views.
"""
import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from apps.common.tests.base import BaseCRUDTest

User = get_user_model()


@pytest.fixture
def test_user(db):
    """Create a test user."""
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
def document_category(db, test_user):
    """Create a test document category."""
    from apps.documents.models import DocumentCategory
    return DocumentCategory.objects.create(
        code='PROC',
        name='Procedures',
        description='Procedure documents',
        created_by=test_user
    )


@pytest.fixture
def document(db, test_user, document_category):
    """Create a test document."""
    from apps.documents.models import Document
    return Document.objects.create(
        document_number='DOC-001',
        title='Test Document',
        description='Test description',
        category=document_category,
        status='DRAFT',
        created_by=test_user
    )


class TestCategoryViews:
    """Tests for DocumentCategory views."""

    def test_category_list_requires_login(self, client):
        url = reverse('documents:category_list')
        response = client.get(url)
        assert response.status_code == 302

    def test_category_list_authenticated(self, authenticated_client, document_category):
        url = reverse('documents:category_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_category_detail(self, authenticated_client, document_category):
        url = reverse('documents:category_detail', kwargs={'pk': document_category.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_category_create_get(self, authenticated_client):
        url = reverse('documents:category_create')
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_category_update_get(self, authenticated_client, document_category):
        url = reverse('documents:category_update', kwargs={'pk': document_category.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestDocumentViews(BaseCRUDTest):
    """Tests for Document views."""

    app_name = 'documents'
    model_name = 'document'
    url_list = 'documents:document_list'
    url_detail = 'documents:document_detail'
    url_create = 'documents:document_create'
    url_update = 'documents:document_update'
    url_delete = None
    template_list = 'documents/document_list.html'
    template_detail = 'documents/document_detail.html'
    template_form = 'documents/document_form.html'
    test_delete = False

    @pytest.fixture
    def test_object(self, document):
        return document

    @pytest.fixture
    def valid_data(self, document_category):
        return {
            'document_number': 'DOC-NEW',
            'title': 'New Document',
            'description': 'New description',
            'category': document_category.pk,
            'status': 'DRAFT',
        }


class TestDocumentActions:
    """Tests for document action views."""

    def test_download_requires_login(self, client, document):
        url = reverse('documents:document_download', kwargs={'pk': document.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_preview_requires_login(self, client, document):
        url = reverse('documents:document_preview', kwargs={'pk': document.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_approve_requires_login(self, client, document):
        url = reverse('documents:document_approve', kwargs={'pk': document.pk})
        response = client.post(url)
        assert response.status_code == 302

    def test_archive_requires_login(self, client, document):
        url = reverse('documents:document_archive', kwargs={'pk': document.pk})
        response = client.post(url)
        assert response.status_code == 302
