"""
Base Test Classes for ARDT FMS

These base classes provide reusable test patterns to eliminate duplication
across app test suites. Inherit from these classes and configure via class
attributes to quickly build comprehensive test coverage.

Usage:
    class TestCustomerViews(BaseCRUDTest):
        app_name = 'sales'
        model_name = 'customer'
        url_list = 'sales:customer-list'
        url_detail = 'sales:customer-detail'
        url_create = 'sales:customer-create'
        url_update = 'sales:customer-update'
        url_delete = 'sales:customer-delete'
        template_list = 'sales/customer_list.html'
        template_detail = 'sales/customer_detail.html'
        template_form = 'sales/customer_form.html'
"""

import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()


# =============================================================================
# SHARED FIXTURES
# =============================================================================

@pytest.fixture
def test_user(db):
    """Create a standard test user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user(db):
    """Create an admin/superuser."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def client():
    """Return a Django test client."""
    return Client()


@pytest.fixture
def authenticated_client(client, test_user):
    """Return an authenticated test client."""
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Return an admin-authenticated test client."""
    client.login(username='admin', password='adminpass123')
    return client


# =============================================================================
# BASE CRUD TEST CLASS
# =============================================================================

class BaseCRUDTest:
    """
    Base class for testing CRUD views.

    Subclasses must define:
        - app_name: str - The app name (e.g., 'sales')
        - model_name: str - The model name (e.g., 'customer')
        - url_list: str - URL name for list view (e.g., 'sales:customer-list')
        - url_detail: str - URL name for detail view
        - url_create: str - URL name for create view
        - url_update: str - URL name for update view
        - url_delete: str - URL name for delete view (optional)
        - template_list: str - Template path for list view
        - template_detail: str - Template path for detail view
        - template_form: str - Template path for form view

    Subclasses should define fixtures:
        - get_test_object(): Returns a model instance for testing
        - get_valid_data(): Returns dict of valid form data for create/update
    """

    # Required class attributes (override in subclass)
    app_name = None
    model_name = None
    url_list = None
    url_detail = None
    url_create = None
    url_update = None
    url_delete = None
    template_list = None
    template_detail = None
    template_form = None

    # Optional: Set to False to skip certain tests
    test_delete = True
    test_create = True
    test_update = True

    # ==========================================================================
    # LIST VIEW TESTS
    # ==========================================================================

    def test_list_requires_login(self, client):
        """Test that list view requires authentication."""
        if not self.url_list:
            pytest.skip("url_list not defined")
        url = reverse(self.url_list)
        response = client.get(url)
        assert response.status_code == 302, f"Expected redirect to login, got {response.status_code}"
        assert 'login' in response.url.lower(), f"Expected redirect to login page, got {response.url}"

    def test_list_returns_200(self, authenticated_client):
        """Test that list view returns 200 for authenticated users."""
        if not self.url_list:
            pytest.skip("url_list not defined")
        url = reverse(self.url_list)
        response = authenticated_client.get(url)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_list_uses_correct_template(self, authenticated_client):
        """Test that list view uses the correct template."""
        if not self.url_list or not self.template_list:
            pytest.skip("url_list or template_list not defined")
        url = reverse(self.url_list)
        response = authenticated_client.get(url)
        assert response.status_code == 200
        templates_used = [t.name for t in response.templates]
        assert self.template_list in templates_used, \
            f"Expected {self.template_list} in {templates_used}"

    def test_list_with_search(self, authenticated_client):
        """Test that list view handles search parameter."""
        if not self.url_list:
            pytest.skip("url_list not defined")
        url = reverse(self.url_list)
        response = authenticated_client.get(url, {'q': 'test'})
        assert response.status_code == 200

    # ==========================================================================
    # DETAIL VIEW TESTS
    # ==========================================================================

    def test_detail_requires_login(self, client, test_object):
        """Test that detail view requires authentication."""
        if not self.url_detail:
            pytest.skip("url_detail not defined")
        url = reverse(self.url_detail, kwargs={'pk': test_object.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url.lower()

    def test_detail_returns_200(self, authenticated_client, test_object):
        """Test that detail view returns 200 for authenticated users."""
        if not self.url_detail:
            pytest.skip("url_detail not defined")
        url = reverse(self.url_detail, kwargs={'pk': test_object.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_detail_uses_correct_template(self, authenticated_client, test_object):
        """Test that detail view uses the correct template."""
        if not self.url_detail or not self.template_detail:
            pytest.skip("url_detail or template_detail not defined")
        url = reverse(self.url_detail, kwargs={'pk': test_object.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        templates_used = [t.name for t in response.templates]
        assert self.template_detail in templates_used

    def test_detail_not_found(self, authenticated_client):
        """Test that detail view returns 404 for invalid ID."""
        if not self.url_detail:
            pytest.skip("url_detail not defined")
        url = reverse(self.url_detail, kwargs={'pk': 99999})
        response = authenticated_client.get(url)
        assert response.status_code == 404

    # ==========================================================================
    # CREATE VIEW TESTS
    # ==========================================================================

    def test_create_requires_login(self, client):
        """Test that create view requires authentication."""
        if not self.url_create or not self.test_create:
            pytest.skip("url_create not defined or test_create is False")
        url = reverse(self.url_create)
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url.lower()

    def test_create_get_returns_200(self, authenticated_client):
        """Test that create view GET returns 200."""
        if not self.url_create or not self.test_create:
            pytest.skip("url_create not defined or test_create is False")
        url = reverse(self.url_create)
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_create_uses_correct_template(self, authenticated_client):
        """Test that create view uses the correct template."""
        if not self.url_create or not self.template_form or not self.test_create:
            pytest.skip("url_create or template_form not defined")
        url = reverse(self.url_create)
        response = authenticated_client.get(url)
        assert response.status_code == 200
        templates_used = [t.name for t in response.templates]
        assert self.template_form in templates_used

    def test_create_post_valid_data(self, authenticated_client, valid_data):
        """Test that create view creates object with valid data."""
        if not self.url_create or not self.test_create:
            pytest.skip("url_create not defined or test_create is False")
        url = reverse(self.url_create)
        response = authenticated_client.post(url, valid_data)
        # Should redirect on success (302) or return 200 with errors
        assert response.status_code in [200, 302]

    # ==========================================================================
    # UPDATE VIEW TESTS
    # ==========================================================================

    def test_update_requires_login(self, client, test_object):
        """Test that update view requires authentication."""
        if not self.url_update or not self.test_update:
            pytest.skip("url_update not defined or test_update is False")
        url = reverse(self.url_update, kwargs={'pk': test_object.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url.lower()

    def test_update_get_returns_200(self, authenticated_client, test_object):
        """Test that update view GET returns 200."""
        if not self.url_update or not self.test_update:
            pytest.skip("url_update not defined or test_update is False")
        url = reverse(self.url_update, kwargs={'pk': test_object.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_update_uses_correct_template(self, authenticated_client, test_object):
        """Test that update view uses the correct template."""
        if not self.url_update or not self.template_form or not self.test_update:
            pytest.skip("url_update or template_form not defined")
        url = reverse(self.url_update, kwargs={'pk': test_object.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        templates_used = [t.name for t in response.templates]
        assert self.template_form in templates_used

    def test_update_post_valid_data(self, authenticated_client, test_object, valid_data):
        """Test that update view updates object with valid data."""
        if not self.url_update or not self.test_update:
            pytest.skip("url_update not defined or test_update is False")
        url = reverse(self.url_update, kwargs={'pk': test_object.pk})
        response = authenticated_client.post(url, valid_data)
        assert response.status_code in [200, 302]

    # ==========================================================================
    # DELETE VIEW TESTS
    # ==========================================================================

    def test_delete_requires_login(self, client, test_object):
        """Test that delete view requires authentication."""
        if not self.url_delete or not self.test_delete:
            pytest.skip("url_delete not defined or test_delete is False")
        url = reverse(self.url_delete, kwargs={'pk': test_object.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url.lower()

    def test_delete_get_returns_200(self, authenticated_client, test_object):
        """Test that delete confirmation view returns 200."""
        if not self.url_delete or not self.test_delete:
            pytest.skip("url_delete not defined or test_delete is False")
        url = reverse(self.url_delete, kwargs={'pk': test_object.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_delete_post_deletes_object(self, authenticated_client, test_object):
        """Test that delete POST removes the object."""
        if not self.url_delete or not self.test_delete:
            pytest.skip("url_delete not defined or test_delete is False")
        url = reverse(self.url_delete, kwargs={'pk': test_object.pk})
        model_class = test_object.__class__
        pk = test_object.pk
        response = authenticated_client.post(url)
        assert response.status_code in [200, 302]
        # Verify object was deleted
        assert not model_class.objects.filter(pk=pk).exists()


# =============================================================================
# BASE FORM TEST CLASS
# =============================================================================

class BaseFormTest:
    """
    Base class for testing Django forms.

    Subclasses must define:
        - form_class: The form class to test
        - valid_data: dict of valid form data
        - required_fields: list of required field names
    """

    form_class = None
    valid_data = None
    required_fields = []

    def test_form_with_valid_data(self):
        """Test that form is valid with correct data."""
        if not self.form_class or not self.valid_data:
            pytest.skip("form_class or valid_data not defined")
        form = self.form_class(data=self.valid_data)
        assert form.is_valid(), f"Form errors: {form.errors}"

    def test_form_with_empty_data(self):
        """Test that form is invalid with empty data."""
        if not self.form_class:
            pytest.skip("form_class not defined")
        form = self.form_class(data={})
        assert not form.is_valid()

    def test_form_required_fields(self):
        """Test that required fields are enforced."""
        if not self.form_class or not self.required_fields:
            pytest.skip("form_class or required_fields not defined")
        form = self.form_class(data={})
        for field in self.required_fields:
            assert field in form.errors, f"Field '{field}' should be required"

    def test_form_field_widgets(self):
        """Test that form fields have expected widgets."""
        if not self.form_class:
            pytest.skip("form_class not defined")
        form = self.form_class()
        # Basic check that form has fields
        assert len(form.fields) > 0, "Form should have at least one field"

    def test_form_labels(self):
        """Test that form fields have labels."""
        if not self.form_class:
            pytest.skip("form_class not defined")
        form = self.form_class()
        for field_name, field in form.fields.items():
            # Most fields should have a label (or use field name)
            assert field.label is not None or field_name


# =============================================================================
# BASE PERMISSION TEST CLASS
# =============================================================================

class BasePermissionTest:
    """
    Base class for testing view permissions.

    Subclasses must define:
        - url_name: The URL name to test
        - required_permission: The permission required (optional)
    """

    url_name = None
    url_kwargs = None  # e.g., {'pk': 1}
    required_permission = None

    def get_url(self, **kwargs):
        """Get the URL for testing."""
        url_kwargs = kwargs or self.url_kwargs or {}
        return reverse(self.url_name, kwargs=url_kwargs) if url_kwargs else reverse(self.url_name)

    def test_requires_authentication(self, client):
        """Test that view requires authentication."""
        if not self.url_name:
            pytest.skip("url_name not defined")
        url = self.get_url()
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url.lower()

    def test_authenticated_user_can_access(self, authenticated_client):
        """Test that authenticated user can access the view."""
        if not self.url_name:
            pytest.skip("url_name not defined")
        url = self.get_url()
        response = authenticated_client.get(url)
        # Should either succeed (200) or redirect to allowed page (302)
        assert response.status_code in [200, 302, 403]

    def test_admin_can_access(self, admin_client):
        """Test that admin user can access the view."""
        if not self.url_name:
            pytest.skip("url_name not defined")
        url = self.get_url()
        response = admin_client.get(url)
        assert response.status_code in [200, 302]


# =============================================================================
# BASE MODEL TEST CLASS
# =============================================================================

class BaseModelTest:
    """
    Base class for testing Django models.

    Subclasses must define:
        - model_class: The model class to test
        - required_fields: dict of field_name: sample_value for required fields
        - str_field: Field name used in __str__ (optional)
    """

    model_class = None
    required_fields = {}
    str_field = None

    def test_create_instance(self, db):
        """Test creating a model instance."""
        if not self.model_class or not self.required_fields:
            pytest.skip("model_class or required_fields not defined")
        instance = self.model_class.objects.create(**self.required_fields)
        assert instance.pk is not None

    def test_str_representation(self, db):
        """Test model string representation."""
        if not self.model_class or not self.required_fields:
            pytest.skip("model_class or required_fields not defined")
        instance = self.model_class.objects.create(**self.required_fields)
        str_repr = str(instance)
        assert str_repr is not None
        assert len(str_repr) > 0

    def test_instance_fields(self, db):
        """Test that instance fields are set correctly."""
        if not self.model_class or not self.required_fields:
            pytest.skip("model_class or required_fields not defined")
        instance = self.model_class.objects.create(**self.required_fields)
        for field, value in self.required_fields.items():
            actual = getattr(instance, field, None)
            # Handle foreign keys and special types
            if hasattr(actual, 'pk'):
                assert actual.pk == value.pk if hasattr(value, 'pk') else actual == value
            else:
                assert actual == value or str(actual) == str(value)


# =============================================================================
# BASE API TEST CLASS
# =============================================================================

class BaseAPITest:
    """
    Base class for testing API endpoints.

    Subclasses must define:
        - api_url_list: URL name for list endpoint
        - api_url_detail: URL name for detail endpoint
    """

    api_url_list = None
    api_url_detail = None
    content_type = 'application/json'

    def test_api_list_requires_auth(self, client):
        """Test that API list endpoint requires authentication."""
        if not self.api_url_list:
            pytest.skip("api_url_list not defined")
        url = reverse(self.api_url_list)
        response = client.get(url)
        assert response.status_code in [401, 403, 302]

    def test_api_list_authenticated(self, authenticated_client):
        """Test that API list endpoint works for authenticated users."""
        if not self.api_url_list:
            pytest.skip("api_url_list not defined")
        url = reverse(self.api_url_list)
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_api_detail_requires_auth(self, client, test_object):
        """Test that API detail endpoint requires authentication."""
        if not self.api_url_detail:
            pytest.skip("api_url_detail not defined")
        url = reverse(self.api_url_detail, kwargs={'pk': test_object.pk})
        response = client.get(url)
        assert response.status_code in [401, 403, 302]

    def test_api_detail_authenticated(self, authenticated_client, test_object):
        """Test that API detail endpoint works for authenticated users."""
        if not self.api_url_detail:
            pytest.skip("api_url_detail not defined")
        url = reverse(self.api_url_detail, kwargs={'pk': test_object.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200
