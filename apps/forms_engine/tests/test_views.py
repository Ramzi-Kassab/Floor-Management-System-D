"""
Forms Engine App - View Tests
Comprehensive tests for all forms engine views.

Tests cover:
- List, detail, create, update, delete views
- Authentication requirements
- Template rendering
- Form validation
- Redirect behavior
- Context data
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.forms_engine.models import (
    FormTemplate, FormSection, FieldType, FormField, FormTemplateVersion
)

User = get_user_model()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def authenticated_client(client, user):
    """Return an authenticated client."""
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def form_template(db, user):
    """Create a test form template."""
    return FormTemplate.objects.create(
        code='FORM-001',
        name='Safety Inspection Form',
        description='Standard safety inspection form',
        version='1.0',
        status=FormTemplate.Status.DRAFT,
        created_by=user
    )


@pytest.fixture
def active_template(db, user):
    """Create an active form template."""
    return FormTemplate.objects.create(
        code='FORM-002',
        name='Active Form',
        status=FormTemplate.Status.ACTIVE,
        created_by=user
    )


@pytest.fixture
def field_type(db):
    """Create a TEXT field type."""
    return FieldType.objects.create(
        code='TEXT',
        name='Text Field',
        html_input_type='text'
    )


@pytest.fixture
def form_section(db, form_template):
    """Create a form section."""
    return FormSection.objects.create(
        template=form_template,
        name='General Information',
        sequence=1
    )


@pytest.fixture
def form_field(db, form_section, field_type):
    """Create a form field."""
    return FormField.objects.create(
        section=form_section,
        field_type=field_type,
        name='test_field',
        label='Test Field'
    )


# =============================================================================
# FORM TEMPLATE LIST VIEW TESTS
# =============================================================================

class TestFormTemplateListView:
    """Tests for FormTemplateListView."""

    def test_list_view_requires_login(self, client):
        """Test that list view requires authentication."""
        response = client.get(reverse('forms_engine:template-list'))
        assert response.status_code == 302
        assert 'login' in response.url

    def test_list_view_authenticated(self, authenticated_client):
        """Test list view for authenticated user."""
        response = authenticated_client.get(reverse('forms_engine:template-list'))
        assert response.status_code == 200
        assert 'templates' in response.context

    def test_list_view_template(self, authenticated_client):
        """Test correct template is used."""
        response = authenticated_client.get(reverse('forms_engine:template-list'))
        assert 'forms_engine/template_list.html' in [t.name for t in response.templates]

    def test_list_view_with_templates(self, authenticated_client, form_template):
        """Test list view shows templates."""
        response = authenticated_client.get(reverse('forms_engine:template-list'))
        assert form_template.name in str(response.content)

    def test_list_view_status_filter(self, authenticated_client, form_template, active_template):
        """Test filtering by status."""
        response = authenticated_client.get(
            reverse('forms_engine:template-list'),
            {'status': 'ACTIVE'}
        )
        content = str(response.content)
        assert active_template.name in content

    def test_list_view_search(self, authenticated_client, form_template):
        """Test search functionality."""
        response = authenticated_client.get(
            reverse('forms_engine:template-list'),
            {'q': 'Safety'}
        )
        content = str(response.content)
        assert form_template.name in content

    def test_list_view_context_data(self, authenticated_client):
        """Test context data includes expected keys."""
        response = authenticated_client.get(reverse('forms_engine:template-list'))
        assert 'page_title' in response.context
        assert 'status_choices' in response.context


# =============================================================================
# FORM TEMPLATE DETAIL VIEW TESTS
# =============================================================================

class TestFormTemplateDetailView:
    """Tests for FormTemplateDetailView."""

    def test_detail_view_requires_login(self, client, form_template):
        """Test detail view requires authentication."""
        response = client.get(
            reverse('forms_engine:template-detail', kwargs={'pk': form_template.pk})
        )
        assert response.status_code == 302

    def test_detail_view_authenticated(self, authenticated_client, form_template):
        """Test detail view for authenticated user."""
        response = authenticated_client.get(
            reverse('forms_engine:template-detail', kwargs={'pk': form_template.pk})
        )
        assert response.status_code == 200

    def test_detail_view_shows_template_data(self, authenticated_client, form_template):
        """Test that template data is displayed."""
        response = authenticated_client.get(
            reverse('forms_engine:template-detail', kwargs={'pk': form_template.pk})
        )
        content = str(response.content)
        assert form_template.code in content
        assert form_template.name in content

    def test_detail_view_404_for_nonexistent(self, authenticated_client):
        """Test 404 for non-existent template."""
        response = authenticated_client.get(
            reverse('forms_engine:template-detail', kwargs={'pk': 99999})
        )
        assert response.status_code == 404


# =============================================================================
# FORM TEMPLATE CREATE VIEW TESTS
# =============================================================================

class TestFormTemplateCreateView:
    """Tests for FormTemplateCreateView."""

    def test_create_view_requires_login(self, client):
        """Test create view requires authentication."""
        response = client.get(reverse('forms_engine:template-create'))
        assert response.status_code == 302

    def test_create_view_get(self, authenticated_client):
        """Test create view GET request."""
        response = authenticated_client.get(reverse('forms_engine:template-create'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_create_view_post_valid(self, authenticated_client):
        """Test creating a template via POST."""
        data = {
            'code': 'NEW-001',
            'name': 'New Test Form',
            'description': 'Test description',
            'status': 'DRAFT'
        }
        response = authenticated_client.post(
            reverse('forms_engine:template-create'),
            data
        )
        assert response.status_code == 302  # Redirect on success

        template = FormTemplate.objects.get(code='NEW-001')
        assert template.name == 'New Test Form'

    def test_create_view_post_invalid(self, authenticated_client):
        """Test validation errors on invalid POST."""
        data = {
            'code': '',  # Required field missing
            'name': 'Test Form'
        }
        response = authenticated_client.post(
            reverse('forms_engine:template-create'),
            data
        )
        assert response.status_code == 200  # Form re-rendered
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_create_view_sets_created_by(self, authenticated_client, user):
        """Test that created_by is set to current user."""
        data = {
            'code': 'CREATOR-001',
            'name': 'Creator Test',
            'status': 'DRAFT'
        }
        authenticated_client.post(reverse('forms_engine:template-create'), data)

        template = FormTemplate.objects.get(code='CREATOR-001')
        assert template.created_by == user


# =============================================================================
# FORM TEMPLATE UPDATE VIEW TESTS
# =============================================================================

class TestFormTemplateUpdateView:
    """Tests for FormTemplateUpdateView."""

    def test_update_view_requires_login(self, client, form_template):
        """Test update view requires authentication."""
        response = client.get(
            reverse('forms_engine:template-update', kwargs={'pk': form_template.pk})
        )
        assert response.status_code == 302

    def test_update_view_get(self, authenticated_client, form_template):
        """Test update view GET request."""
        response = authenticated_client.get(
            reverse('forms_engine:template-update', kwargs={'pk': form_template.pk})
        )
        assert response.status_code == 200
        assert response.context['form'].instance == form_template

    def test_update_view_post(self, authenticated_client, form_template):
        """Test updating a template via POST."""
        data = {
            'code': form_template.code,
            'name': 'Updated Form Name',
            'description': 'Updated description',
            'status': 'ACTIVE'
        }
        response = authenticated_client.post(
            reverse('forms_engine:template-update', kwargs={'pk': form_template.pk}),
            data
        )
        assert response.status_code == 302

        form_template.refresh_from_db()
        assert form_template.name == 'Updated Form Name'
        assert form_template.status == 'ACTIVE'


# =============================================================================
# FORM TEMPLATE DELETE VIEW TESTS
# =============================================================================

class TestFormTemplateDeleteView:
    """Tests for FormTemplateDeleteView."""

    def test_delete_view_requires_login(self, client, form_template):
        """Test delete view requires authentication."""
        response = client.get(
            reverse('forms_engine:template-delete', kwargs={'pk': form_template.pk})
        )
        assert response.status_code == 302

    def test_delete_view_get_confirmation(self, authenticated_client, form_template):
        """Test delete confirmation page."""
        response = authenticated_client.get(
            reverse('forms_engine:template-delete', kwargs={'pk': form_template.pk})
        )
        assert response.status_code == 200
        assert form_template.name in str(response.content)

    def test_delete_view_post(self, authenticated_client, form_template):
        """Test deleting a template via POST."""
        template_id = form_template.pk
        response = authenticated_client.post(
            reverse('forms_engine:template-delete', kwargs={'pk': form_template.pk})
        )
        assert response.status_code == 302

        assert not FormTemplate.objects.filter(pk=template_id).exists()


# =============================================================================
# FORM BUILDER VIEW TESTS
# =============================================================================

class TestFormTemplateBuilderView:
    """Tests for FormTemplateBuilderView."""

    def test_builder_view_requires_login(self, client, form_template):
        """Test builder view requires authentication."""
        response = client.get(
            reverse('forms_engine:template-builder', kwargs={'pk': form_template.pk})
        )
        assert response.status_code == 302

    def test_builder_view_authenticated(self, authenticated_client, form_template):
        """Test builder view for authenticated user."""
        response = authenticated_client.get(
            reverse('forms_engine:template-builder', kwargs={'pk': form_template.pk})
        )
        assert response.status_code == 200

    def test_builder_view_context(self, authenticated_client, form_template, field_type):
        """Test builder view context includes field types."""
        response = authenticated_client.get(
            reverse('forms_engine:template-builder', kwargs={'pk': form_template.pk})
        )
        assert 'field_types' in response.context
        assert 'section_form' in response.context
        assert 'field_form' in response.context


# =============================================================================
# FORM SECTION VIEW TESTS
# =============================================================================

class TestFormSectionViews:
    """Tests for FormSection views."""

    def test_section_create_view(self, authenticated_client, form_template):
        """Test creating a section."""
        data = {
            'name': 'New Section',
            'description': 'Section description',
            'sequence': 1,
            'is_collapsible': False,
            'is_collapsed_default': False
        }
        response = authenticated_client.post(
            reverse('forms_engine:section-create', kwargs={'template_pk': form_template.pk}),
            data
        )
        assert response.status_code == 302

        assert FormSection.objects.filter(
            template=form_template,
            name='New Section'
        ).exists()

    def test_section_update_view(self, authenticated_client, form_section):
        """Test updating a section."""
        data = {
            'name': 'Updated Section Name',
            'description': 'Updated description',
            'sequence': 1,
            'is_collapsible': True,
            'is_collapsed_default': False
        }
        response = authenticated_client.post(
            reverse('forms_engine:section-update', kwargs={'pk': form_section.pk}),
            data
        )
        assert response.status_code == 302

        form_section.refresh_from_db()
        assert form_section.name == 'Updated Section Name'

    def test_section_delete_view(self, authenticated_client, form_section):
        """Test deleting a section."""
        section_id = form_section.pk
        response = authenticated_client.post(
            reverse('forms_engine:section-delete', kwargs={'pk': form_section.pk})
        )
        assert response.status_code == 302

        assert not FormSection.objects.filter(pk=section_id).exists()


# =============================================================================
# FORM FIELD VIEW TESTS
# =============================================================================

class TestFormFieldViews:
    """Tests for FormField views."""

    def test_field_create_view(self, authenticated_client, form_section, field_type):
        """Test creating a field."""
        data = {
            'field_type': field_type.pk,
            'name': 'new_field',
            'label': 'New Field',
            'placeholder': 'Enter value',
            'help_text': 'Help text',
            'is_required': False,
            'sequence': 1,
            'width': 'full'
        }
        response = authenticated_client.post(
            reverse('forms_engine:field-create', kwargs={'section_pk': form_section.pk}),
            data
        )
        assert response.status_code == 302

        assert FormField.objects.filter(
            section=form_section,
            name='new_field'
        ).exists()

    def test_field_update_view(self, authenticated_client, form_field, field_type):
        """Test updating a field."""
        data = {
            'field_type': field_type.pk,
            'name': 'updated_field',
            'label': 'Updated Field',
            'placeholder': '',
            'help_text': '',
            'is_required': True,
            'sequence': 1,
            'width': 'half'
        }
        response = authenticated_client.post(
            reverse('forms_engine:field-update', kwargs={'pk': form_field.pk}),
            data
        )
        assert response.status_code == 302

        form_field.refresh_from_db()
        assert form_field.label == 'Updated Field'
        assert form_field.is_required is True

    def test_field_delete_view(self, authenticated_client, form_field):
        """Test deleting a field."""
        field_id = form_field.pk
        response = authenticated_client.post(
            reverse('forms_engine:field-delete', kwargs={'pk': form_field.pk})
        )
        assert response.status_code == 302

        assert not FormField.objects.filter(pk=field_id).exists()


# =============================================================================
# FIELD TYPE VIEW TESTS
# =============================================================================

class TestFieldTypeViews:
    """Tests for FieldType views."""

    def test_fieldtype_list_view(self, authenticated_client, field_type):
        """Test field type list view."""
        response = authenticated_client.get(reverse('forms_engine:fieldtype-list'))
        assert response.status_code == 200
        assert field_type.name in str(response.content)

    def test_fieldtype_create_view(self, authenticated_client):
        """Test creating a field type."""
        data = {
            'code': 'DATE',
            'name': 'Date Picker',
            'html_input_type': 'date',
            'has_options': False,
            'has_validation': True,
            'icon': 'calendar'
        }
        response = authenticated_client.post(
            reverse('forms_engine:fieldtype-create'),
            data
        )
        assert response.status_code == 302

        assert FieldType.objects.filter(code='DATE').exists()

    def test_fieldtype_update_view(self, authenticated_client, field_type):
        """Test updating a field type."""
        data = {
            'code': field_type.code,
            'name': 'Updated Text Field',
            'html_input_type': 'text',
            'has_options': False,
            'has_validation': True,
            'icon': 'type'
        }
        response = authenticated_client.post(
            reverse('forms_engine:fieldtype-update', kwargs={'pk': field_type.pk}),
            data
        )
        assert response.status_code == 302

        field_type.refresh_from_db()
        assert field_type.name == 'Updated Text Field'


# =============================================================================
# PREVIEW VIEW TESTS
# =============================================================================

class TestFormPreviewView:
    """Tests for FormPreviewView."""

    def test_preview_view_requires_login(self, client, form_template):
        """Test preview view requires authentication."""
        response = client.get(
            reverse('forms_engine:template-preview', kwargs={'pk': form_template.pk})
        )
        assert response.status_code == 302

    def test_preview_view_authenticated(self, authenticated_client, form_template):
        """Test preview view for authenticated user."""
        response = authenticated_client.get(
            reverse('forms_engine:template-preview', kwargs={'pk': form_template.pk})
        )
        assert response.status_code == 200

    def test_preview_view_shows_form(self, authenticated_client, form_template, form_section, form_field):
        """Test that preview displays form structure."""
        response = authenticated_client.get(
            reverse('forms_engine:template-preview', kwargs={'pk': form_template.pk})
        )
        content = str(response.content)
        assert form_template.name in content


# =============================================================================
# TEMPLATE ACTION VIEW TESTS
# =============================================================================

class TestTemplateActionViews:
    """Tests for template action views (duplicate, activate, deactivate)."""

    def test_duplicate_template(self, authenticated_client, form_template):
        """Test duplicating a template."""
        response = authenticated_client.post(
            reverse('forms_engine:template-duplicate', kwargs={'pk': form_template.pk})
        )
        assert response.status_code == 302

        duplicate = FormTemplate.objects.get(code=f'{form_template.code}-COPY')
        assert 'Copy' in duplicate.name
        assert duplicate.status == 'DRAFT'

    def test_activate_template(self, authenticated_client, form_template):
        """Test activating a template."""
        assert form_template.status == 'DRAFT'

        response = authenticated_client.post(
            reverse('forms_engine:template-activate', kwargs={'pk': form_template.pk})
        )
        assert response.status_code == 302

        form_template.refresh_from_db()
        assert form_template.status == 'ACTIVE'

    def test_deactivate_template(self, authenticated_client, active_template):
        """Test deactivating a template."""
        assert active_template.status == 'ACTIVE'

        response = authenticated_client.post(
            reverse('forms_engine:template-deactivate', kwargs={'pk': active_template.pk})
        )
        assert response.status_code == 302

        active_template.refresh_from_db()
        assert active_template.status == 'DRAFT'


# =============================================================================
# HTMX ENDPOINT TESTS
# =============================================================================

class TestHTMXEndpoints:
    """Tests for HTMX/API endpoints."""

    def test_reorder_sections(self, authenticated_client, form_template):
        """Test reordering sections."""
        section1 = FormSection.objects.create(
            template=form_template,
            name='Section 1',
            sequence=0
        )
        section2 = FormSection.objects.create(
            template=form_template,
            name='Section 2',
            sequence=1
        )

        response = authenticated_client.post(
            reverse('forms_engine:reorder-sections', kwargs={'pk': form_template.pk}),
            {'section_ids[]': [section2.pk, section1.pk]}
        )
        assert response.status_code == 200
        assert response.json()['success'] is True

    def test_reorder_fields(self, authenticated_client, form_section, field_type):
        """Test reordering fields."""
        field1 = FormField.objects.create(
            section=form_section,
            field_type=field_type,
            name='field1',
            label='Field 1',
            sequence=0
        )
        field2 = FormField.objects.create(
            section=form_section,
            field_type=field_type,
            name='field2',
            label='Field 2',
            sequence=1
        )

        response = authenticated_client.post(
            reverse('forms_engine:reorder-fields', kwargs={'pk': form_section.pk}),
            {'field_ids[]': [field2.pk, field1.pk]}
        )
        assert response.status_code == 200
        assert response.json()['success'] is True
