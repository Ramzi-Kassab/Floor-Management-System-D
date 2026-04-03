"""
Forms Engine App - Model Tests
Comprehensive tests for all 5 forms engine models.

Tests cover:
- Instance creation with required fields
- __str__ representation
- Field validation (max_length, choices, unique constraints)
- Foreign key relationships and cascades
- Custom methods and properties
- Edge cases (blank fields, invalid data)
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

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
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User'
    )


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
def active_form_template(db, user):
    """Create an active form template."""
    return FormTemplate.objects.create(
        code='FORM-002',
        name='Quality Check Form',
        description='Quality control checklist',
        version='1.0',
        status=FormTemplate.Status.ACTIVE,
        created_by=user
    )


@pytest.fixture
def field_type_text(db):
    """Create a TEXT field type."""
    return FieldType.objects.create(
        code='TEXT',
        name='Text Field',
        html_input_type='text',
        has_options=False,
        has_validation=True,
        icon='type'
    )


@pytest.fixture
def field_type_select(db):
    """Create a SELECT field type."""
    return FieldType.objects.create(
        code='SELECT',
        name='Dropdown',
        html_input_type='select',
        has_options=True,
        has_validation=True,
        icon='chevron-down'
    )


@pytest.fixture
def field_type_number(db):
    """Create a NUMBER field type."""
    return FieldType.objects.create(
        code='NUMBER',
        name='Number Field',
        html_input_type='number',
        has_options=False,
        has_validation=True,
        icon='hash'
    )


@pytest.fixture
def form_section(db, form_template):
    """Create a test form section."""
    return FormSection.objects.create(
        template=form_template,
        name='General Information',
        description='Basic details section',
        sequence=1,
        is_collapsible=False,
        is_collapsed_default=False
    )


@pytest.fixture
def form_field(db, form_section, field_type_text):
    """Create a test form field."""
    return FormField.objects.create(
        section=form_section,
        field_type=field_type_text,
        name='inspector_name',
        label='Inspector Name',
        placeholder='Enter inspector name',
        help_text='Full name of the inspector',
        is_required=True,
        sequence=1,
        width='half'
    )


# =============================================================================
# FORM TEMPLATE MODEL TESTS
# =============================================================================

class TestFormTemplateModel:
    """Tests for the FormTemplate model."""

    def test_create_form_template(self, db, user):
        """Test creating a form template with required fields."""
        template = FormTemplate.objects.create(
            code='TEST-001',
            name='Test Form',
            created_by=user
        )
        assert template.pk is not None
        assert template.code == 'TEST-001'
        assert template.name == 'Test Form'
        assert template.status == FormTemplate.Status.DRAFT
        assert template.is_active is True

    def test_form_template_str(self, form_template):
        """Test the __str__ method."""
        expected = 'FORM-001 - Safety Inspection Form'
        assert str(form_template) == expected

    def test_form_template_unique_code(self, form_template, user):
        """Test that code must be unique."""
        with pytest.raises(IntegrityError):
            FormTemplate.objects.create(
                code='FORM-001',  # Duplicate code
                name='Duplicate Form',
                created_by=user
            )

    def test_form_template_status_choices(self, db, user):
        """Test valid status choices."""
        for status_code, status_name in FormTemplate.Status.choices:
            template = FormTemplate.objects.create(
                code=f'STATUS-{status_code}',
                name=f'Status Test - {status_name}',
                status=status_code,
                created_by=user
            )
            assert template.status == status_code

    def test_form_template_field_count_property(self, form_template, form_section, field_type_text):
        """Test the field_count property."""
        assert form_template.field_count == 0

        # Add fields
        FormField.objects.create(
            section=form_section,
            field_type=field_type_text,
            name='field1',
            label='Field 1'
        )
        FormField.objects.create(
            section=form_section,
            field_type=field_type_text,
            name='field2',
            label='Field 2'
        )

        assert form_template.field_count == 2

    def test_form_template_timestamps(self, form_template):
        """Test auto-generated timestamps."""
        assert form_template.created_at is not None
        assert form_template.updated_at is not None

    def test_form_template_optional_description(self, db, user):
        """Test template with empty description."""
        template = FormTemplate.objects.create(
            code='NODESC-001',
            name='No Description Form',
            description='',
            created_by=user
        )
        assert template.description == ''


# =============================================================================
# FORM SECTION MODEL TESTS
# =============================================================================

class TestFormSectionModel:
    """Tests for the FormSection model."""

    def test_create_form_section(self, form_template):
        """Test creating a form section."""
        section = FormSection.objects.create(
            template=form_template,
            name='Test Section',
            sequence=0
        )
        assert section.pk is not None
        assert section.name == 'Test Section'
        assert section.template == form_template

    def test_form_section_str(self, form_section):
        """Test the __str__ method."""
        expected = 'FORM-001 - General Information'
        assert str(form_section) == expected

    def test_form_section_cascade_delete(self, form_template, form_section):
        """Test that deleting a template cascades to sections."""
        section_id = form_section.pk
        form_template.delete()

        assert not FormSection.objects.filter(pk=section_id).exists()

    def test_form_section_ordering(self, form_template):
        """Test section ordering by template and sequence."""
        section3 = FormSection.objects.create(
            template=form_template,
            name='Third Section',
            sequence=3
        )
        section1 = FormSection.objects.create(
            template=form_template,
            name='First Section',
            sequence=1
        )
        section2 = FormSection.objects.create(
            template=form_template,
            name='Second Section',
            sequence=2
        )

        sections = list(form_template.sections.all())
        assert sections[0].sequence == 1
        assert sections[1].sequence == 2
        assert sections[2].sequence == 3

    def test_form_section_collapsible_options(self, form_template):
        """Test collapsible section settings."""
        section = FormSection.objects.create(
            template=form_template,
            name='Collapsible Section',
            sequence=1,
            is_collapsible=True,
            is_collapsed_default=True
        )
        assert section.is_collapsible is True
        assert section.is_collapsed_default is True


# =============================================================================
# FIELD TYPE MODEL TESTS
# =============================================================================

class TestFieldTypeModel:
    """Tests for the FieldType model."""

    def test_create_field_type(self, db):
        """Test creating a field type."""
        field_type = FieldType.objects.create(
            code='DATE',
            name='Date Picker',
            html_input_type='date',
            has_options=False
        )
        assert field_type.pk is not None
        assert field_type.code == 'DATE'

    def test_field_type_str(self, field_type_text):
        """Test the __str__ method."""
        expected = 'TEXT - Text Field'
        assert str(field_type_text) == expected

    def test_field_type_unique_code(self, field_type_text):
        """Test that code must be unique."""
        with pytest.raises(IntegrityError):
            FieldType.objects.create(
                code='TEXT',  # Duplicate
                name='Another Text Field'
            )

    def test_field_type_with_options(self, field_type_select):
        """Test field type that has options."""
        assert field_type_select.has_options is True

    def test_field_type_without_options(self, field_type_text):
        """Test field type without options."""
        assert field_type_text.has_options is False


# =============================================================================
# FORM FIELD MODEL TESTS
# =============================================================================

class TestFormFieldModel:
    """Tests for the FormField model."""

    def test_create_form_field(self, form_section, field_type_text):
        """Test creating a form field."""
        field = FormField.objects.create(
            section=form_section,
            field_type=field_type_text,
            name='test_field',
            label='Test Field'
        )
        assert field.pk is not None
        assert field.name == 'test_field'
        assert field.label == 'Test Field'

    def test_form_field_str(self, form_field):
        """Test the __str__ method."""
        expected = 'FORM-001 - Inspector Name'
        assert str(form_field) == expected

    def test_form_field_cascade_delete(self, form_section, form_field):
        """Test that deleting a section cascades to fields."""
        field_id = form_field.pk
        form_section.delete()

        assert not FormField.objects.filter(pk=field_id).exists()

    def test_form_field_protect_field_type(self, form_field, field_type_text):
        """Test that field type is protected from deletion."""
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            field_type_text.delete()

    def test_form_field_validation_settings(self, form_section, field_type_text):
        """Test field validation settings."""
        from decimal import Decimal
        field = FormField.objects.create(
            section=form_section,
            field_type=field_type_text,
            name='validated_field',
            label='Validated Field',
            is_required=True,
            min_length=5,
            max_length=100,
            min_value=Decimal('0'),
            max_value=Decimal('1000'),
            regex_pattern='^[A-Z]+$',
            validation_message='Must be uppercase letters'
        )

        assert field.is_required is True
        assert field.min_length == 5
        assert field.max_length == 100
        assert field.min_value == Decimal('0')
        assert field.max_value == Decimal('1000')
        assert field.regex_pattern == '^[A-Z]+$'

    def test_form_field_json_options(self, form_section, field_type_select):
        """Test field with JSON options."""
        options = [
            {'value': 'A', 'label': 'Option A'},
            {'value': 'B', 'label': 'Option B'},
            {'value': 'C', 'label': 'Option C'}
        ]
        field = FormField.objects.create(
            section=form_section,
            field_type=field_type_select,
            name='choice_field',
            label='Choice Field',
            options=options
        )

        assert field.options == options
        assert len(field.options) == 3

    def test_form_field_width_choices(self, form_section, field_type_text):
        """Test different width options."""
        widths = ['full', 'half', 'third', 'quarter']
        for width in widths:
            field = FormField.objects.create(
                section=form_section,
                field_type=field_type_text,
                name=f'field_{width}',
                label=f'Field {width}',
                width=width
            )
            assert field.width == width

    def test_form_field_conditional_display(self, form_section, field_type_text, form_field):
        """Test conditional field dependency."""
        dependent_field = FormField.objects.create(
            section=form_section,
            field_type=field_type_text,
            name='dependent_field',
            label='Dependent Field',
            depends_on_field=form_field,
            depends_on_value='yes'
        )

        assert dependent_field.depends_on_field == form_field
        assert dependent_field.depends_on_value == 'yes'

    def test_form_field_readonly_hidden(self, form_section, field_type_text):
        """Test readonly and hidden flags."""
        field = FormField.objects.create(
            section=form_section,
            field_type=field_type_text,
            name='readonly_hidden',
            label='Readonly Hidden Field',
            is_readonly=True,
            is_hidden=True
        )

        assert field.is_readonly is True
        assert field.is_hidden is True


# =============================================================================
# FORM TEMPLATE VERSION MODEL TESTS
# =============================================================================

class TestFormTemplateVersionModel:
    """Tests for the FormTemplateVersion model."""

    def test_create_version(self, form_template, user):
        """Test creating a template version."""
        snapshot = {
            'code': form_template.code,
            'name': form_template.name,
            'sections': []
        }
        version = FormTemplateVersion.objects.create(
            template=form_template,
            version_number=1,
            snapshot=snapshot,
            change_summary='Initial version',
            changed_by=user
        )

        assert version.pk is not None
        assert version.version_number == 1
        assert version.snapshot == snapshot

    def test_version_str(self, form_template, user):
        """Test the __str__ method."""
        version = FormTemplateVersion.objects.create(
            template=form_template,
            version_number=2,
            snapshot={},
            changed_by=user
        )
        expected = 'FORM-001 v2'
        assert str(version) == expected

    def test_version_unique_together(self, form_template, user):
        """Test unique constraint on template + version_number."""
        FormTemplateVersion.objects.create(
            template=form_template,
            version_number=1,
            snapshot={},
            changed_by=user
        )

        with pytest.raises(IntegrityError):
            FormTemplateVersion.objects.create(
                template=form_template,
                version_number=1,  # Duplicate
                snapshot={},
                changed_by=user
            )

    def test_version_ordering(self, form_template, user):
        """Test version ordering (newest first)."""
        FormTemplateVersion.objects.create(
            template=form_template,
            version_number=1,
            snapshot={},
            changed_by=user
        )
        FormTemplateVersion.objects.create(
            template=form_template,
            version_number=2,
            snapshot={},
            changed_by=user
        )
        FormTemplateVersion.objects.create(
            template=form_template,
            version_number=3,
            snapshot={},
            changed_by=user
        )

        versions = list(form_template.versions.all())
        assert versions[0].version_number == 3
        assert versions[1].version_number == 2
        assert versions[2].version_number == 1

    def test_version_cascade_delete(self, form_template, user):
        """Test that deleting template cascades to versions."""
        version = FormTemplateVersion.objects.create(
            template=form_template,
            version_number=1,
            snapshot={},
            changed_by=user
        )
        version_id = version.pk
        form_template.delete()

        assert not FormTemplateVersion.objects.filter(pk=version_id).exists()


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestFormEngineEdgeCases:
    """Edge case tests for forms engine models."""

    def test_deeply_nested_structure(self, db, user, field_type_text):
        """Test template with many sections and fields."""
        template = FormTemplate.objects.create(
            code='LARGE-001',
            name='Large Form',
            created_by=user
        )

        # Create 10 sections with 5 fields each
        for i in range(10):
            section = FormSection.objects.create(
                template=template,
                name=f'Section {i}',
                sequence=i
            )
            for j in range(5):
                FormField.objects.create(
                    section=section,
                    field_type=field_type_text,
                    name=f'field_{i}_{j}',
                    label=f'Field {i}-{j}'
                )

        assert template.sections.count() == 10
        assert template.field_count == 50

    def test_special_characters_in_names(self, db, user):
        """Test handling of special characters."""
        template = FormTemplate.objects.create(
            code='SPECIAL-001',
            name='Form with "Quotes" & <Special> Characters',
            description="Description with\nnewlines\tand\ttabs",
            created_by=user
        )

        assert '"Quotes"' in template.name
        assert '&' in template.name

    def test_unicode_characters(self, db, user):
        """Test handling of unicode characters."""
        template = FormTemplate.objects.create(
            code='UNICODE-001',
            name='نموذج عربي',  # Arabic
            description='Japanese: フォーム, Chinese: 表单',
            created_by=user
        )

        assert template.name == 'نموذج عربي'

    def test_empty_form_template(self, form_template):
        """Test template with no sections or fields."""
        assert form_template.sections.count() == 0
        assert form_template.field_count == 0

    def test_null_optional_fields(self, form_section, field_type_text):
        """Test field with all optional values null."""
        field = FormField.objects.create(
            section=form_section,
            field_type=field_type_text,
            name='minimal_field',
            label='Minimal Field',
            placeholder='',
            help_text='',
            min_length=None,
            max_length=None,
            min_value=None,
            max_value=None,
            regex_pattern='',
            validation_message='',
            options=None,
            default_value='',
            depends_on_field=None,
            depends_on_value=''
        )

        assert field.pk is not None
        assert field.min_length is None
        assert field.options is None
