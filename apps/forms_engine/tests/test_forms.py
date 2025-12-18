"""
Forms Engine App - Form Tests
Comprehensive tests for all form classes.

Tests cover:
- Form field validation
- Required fields
- Invalid data handling
- Form initialization
"""

import pytest
from django.contrib.auth import get_user_model

from apps.forms_engine.forms import (
    FormTemplateForm, FormSectionForm, FormFieldForm, FieldTypeForm
)
from apps.forms_engine.models import (
    FormTemplate, FormSection, FieldType, FormField
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
        password='testpass123'
    )


@pytest.fixture
def form_template(db, user):
    """Create a test form template."""
    return FormTemplate.objects.create(
        code='FORM-001',
        name='Test Form',
        created_by=user
    )


@pytest.fixture
def form_section(db, form_template):
    """Create a test form section."""
    return FormSection.objects.create(
        template=form_template,
        name='Test Section',
        sequence=1
    )


@pytest.fixture
def field_type(db):
    """Create a text field type."""
    return FieldType.objects.create(
        code='TEXT',
        name='Text Field',
        html_input_type='text'
    )


# =============================================================================
# FORM TEMPLATE FORM TESTS
# =============================================================================

class TestFormTemplateForm:
    """Tests for FormTemplateForm."""

    def test_valid_form(self, db):
        """Test form with valid data."""
        data = {
            'code': 'TEST-001',
            'name': 'Test Form Template',
            'description': 'A test form',
            'status': 'DRAFT'
        }
        form = FormTemplateForm(data=data)
        assert form.is_valid()

    def test_required_fields(self, db):
        """Test that required fields are enforced."""
        data = {}
        form = FormTemplateForm(data=data)
        assert not form.is_valid()
        assert 'code' in form.errors
        assert 'name' in form.errors

    def test_code_only_required(self, db):
        """Test form with only code provided."""
        data = {'code': 'TEST-002'}
        form = FormTemplateForm(data=data)
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_status_choices(self, db):
        """Test invalid status choice."""
        data = {
            'code': 'TEST-003',
            'name': 'Test Form',
            'status': 'INVALID'
        }
        form = FormTemplateForm(data=data)
        assert not form.is_valid()
        assert 'status' in form.errors

    def test_optional_description(self, db):
        """Test form without description."""
        data = {
            'code': 'TEST-004',
            'name': 'Test Form',
            'status': 'DRAFT'
        }
        form = FormTemplateForm(data=data)
        assert form.is_valid()

    def test_duplicate_code_on_create(self, form_template):
        """Test duplicate code validation (handled at model level)."""
        data = {
            'code': form_template.code,  # Duplicate
            'name': 'Another Form',
            'status': 'DRAFT'
        }
        form = FormTemplateForm(data=data)
        # Form validates, but model will raise IntegrityError
        assert form.is_valid()


# =============================================================================
# FORM SECTION FORM TESTS
# =============================================================================

class TestFormSectionForm:
    """Tests for FormSectionForm."""

    def test_valid_form(self, db):
        """Test form with valid data."""
        data = {
            'name': 'Test Section',
            'description': 'Section description',
            'sequence': 1,
            'is_collapsible': False,
            'is_collapsed_default': False
        }
        form = FormSectionForm(data=data)
        assert form.is_valid()

    def test_required_name(self, db):
        """Test that name is required."""
        data = {
            'sequence': 1
        }
        form = FormSectionForm(data=data)
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_optional_fields(self, db):
        """Test form with only required fields."""
        data = {
            'name': 'Minimal Section'
        }
        form = FormSectionForm(data=data)
        assert form.is_valid()

    def test_collapsible_options(self, db):
        """Test collapsible section options."""
        data = {
            'name': 'Collapsible Section',
            'is_collapsible': True,
            'is_collapsed_default': True
        }
        form = FormSectionForm(data=data)
        assert form.is_valid()

    def test_negative_sequence(self, db):
        """Test negative sequence number."""
        data = {
            'name': 'Test Section',
            'sequence': -1
        }
        form = FormSectionForm(data=data)
        # Widget has min=0 but form should still validate
        assert form.is_valid()  # Will fail at widget level in browser


# =============================================================================
# FORM FIELD FORM TESTS
# =============================================================================

class TestFormFieldForm:
    """Tests for FormFieldForm."""

    def test_valid_form(self, field_type):
        """Test form with valid data."""
        data = {
            'field_type': field_type.pk,
            'name': 'test_field',
            'label': 'Test Field',
            'placeholder': 'Enter value',
            'help_text': 'Help text',
            'is_required': False,
            'sequence': 1,
            'width': 'full'
        }
        form = FormFieldForm(data=data)
        assert form.is_valid()

    def test_required_fields(self, db):
        """Test required field validation."""
        data = {}
        form = FormFieldForm(data=data)
        assert not form.is_valid()
        assert 'field_type' in form.errors
        assert 'name' in form.errors
        assert 'label' in form.errors

    def test_width_choices(self, field_type):
        """Test width field choices."""
        valid_widths = ['full', 'half', 'third', 'quarter']
        for width in valid_widths:
            data = {
                'field_type': field_type.pk,
                'name': f'field_{width}',
                'label': f'Field {width}',
                'width': width
            }
            form = FormFieldForm(data=data)
            assert form.is_valid(), f"Width '{width}' should be valid"

    def test_validation_fields(self, field_type):
        """Test validation field settings."""
        data = {
            'field_type': field_type.pk,
            'name': 'validated_field',
            'label': 'Validated Field',
            'is_required': True,
            'min_length': 5,
            'max_length': 100,
            'regex_pattern': '^[A-Z]+$',
            'validation_message': 'Custom error message',
            'width': 'full'
        }
        form = FormFieldForm(data=data)
        assert form.is_valid()

    def test_json_options_field(self, field_type):
        """Test JSON options field."""
        import json
        options = json.dumps([
            {'value': 'A', 'label': 'Option A'},
            {'value': 'B', 'label': 'Option B'}
        ])
        data = {
            'field_type': field_type.pk,
            'name': 'select_field',
            'label': 'Select Field',
            'options': options,
            'width': 'full'
        }
        form = FormFieldForm(data=data)
        assert form.is_valid()

    def test_conditional_display(self, field_type, form_section):
        """Test conditional display fields."""
        # Create a field to depend on
        parent_field = FormField.objects.create(
            section=form_section,
            field_type=field_type,
            name='parent_field',
            label='Parent Field'
        )

        data = {
            'field_type': field_type.pk,
            'name': 'child_field',
            'label': 'Child Field',
            'depends_on_field': parent_field.pk,
            'depends_on_value': 'yes',
            'width': 'full'
        }
        form = FormFieldForm(data=data)
        assert form.is_valid()


# =============================================================================
# FIELD TYPE FORM TESTS
# =============================================================================

class TestFieldTypeForm:
    """Tests for FieldTypeForm."""

    def test_valid_form(self, db):
        """Test form with valid data."""
        data = {
            'code': 'DATE',
            'name': 'Date Field',
            'html_input_type': 'date',
            'has_options': False,
            'has_validation': True,
            'icon': 'calendar'
        }
        form = FieldTypeForm(data=data)
        assert form.is_valid()

    def test_required_fields(self, db):
        """Test required field validation."""
        data = {}
        form = FieldTypeForm(data=data)
        assert not form.is_valid()
        assert 'code' in form.errors
        assert 'name' in form.errors

    def test_minimal_valid_form(self, db):
        """Test form with minimal required fields."""
        data = {
            'code': 'MINIMAL',
            'name': 'Minimal Type'
        }
        form = FieldTypeForm(data=data)
        assert form.is_valid()

    def test_has_options_flag(self, db):
        """Test field type with options."""
        data = {
            'code': 'RADIO',
            'name': 'Radio Buttons',
            'html_input_type': 'radio',
            'has_options': True,
            'has_validation': True
        }
        form = FieldTypeForm(data=data)
        assert form.is_valid()

    def test_icon_optional(self, db):
        """Test that icon is optional."""
        data = {
            'code': 'NOICON',
            'name': 'No Icon Type',
            'html_input_type': 'text'
        }
        form = FieldTypeForm(data=data)
        assert form.is_valid()


# =============================================================================
# FORM WIDGET TESTS
# =============================================================================

class TestFormWidgets:
    """Tests for form widget configurations."""

    def test_form_template_widgets(self, db):
        """Test FormTemplateForm widget attributes."""
        form = FormTemplateForm()
        # Check that widgets have proper CSS classes
        assert 'class' in form.fields['code'].widget.attrs
        assert 'rounded-lg' in form.fields['code'].widget.attrs['class']

    def test_form_section_widgets(self, db):
        """Test FormSectionForm widget attributes."""
        form = FormSectionForm()
        assert 'class' in form.fields['name'].widget.attrs
        assert 'min' in form.fields['sequence'].widget.attrs

    def test_form_field_widgets(self, db):
        """Test FormFieldForm widget attributes."""
        form = FormFieldForm()
        assert 'class' in form.fields['name'].widget.attrs
        assert 'rows' in form.fields['help_text'].widget.attrs

    def test_field_type_widgets(self, db):
        """Test FieldTypeForm widget attributes."""
        form = FieldTypeForm()
        assert 'class' in form.fields['code'].widget.attrs
        assert 'placeholder' in form.fields['code'].widget.attrs
