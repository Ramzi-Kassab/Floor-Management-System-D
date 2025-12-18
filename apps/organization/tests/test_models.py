"""
Organization App - Model Tests
Comprehensive tests for Department, Position, Theme, SystemSetting, NumberSequence models.

Tests cover:
- Instance creation with required fields
- __str__ representation
- Field validation (max_length, choices, unique constraints)
- Foreign key relationships
- Custom methods and properties
- Edge cases
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.organization.models import (
    Department, Position, Theme, SystemSetting, NumberSequence
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
def manager(db):
    """Create a manager user."""
    return User.objects.create_user(
        username='manager',
        email='manager@example.com',
        password='mgrpass123',
        first_name='Department',
        last_name='Manager'
    )


@pytest.fixture
def department(db, manager):
    """Create a test department."""
    return Department.objects.create(
        code='MFG',
        name='Manufacturing',
        name_ar='التصنيع',
        manager=manager,
        location='Building A'
    )


@pytest.fixture
def child_department(db, department):
    """Create a child department."""
    return Department.objects.create(
        code='MFG-QC',
        name='Quality Control',
        parent=department,
        location='Building A - Floor 2'
    )


@pytest.fixture
def position(db, department):
    """Create a test position."""
    return Position.objects.create(
        code='QC-INSP',
        title='QC Inspector',
        title_ar='مفتش الجودة',
        department=department,
        level=2,
        description='Quality control inspector role'
    )


@pytest.fixture
def theme(db):
    """Create a test theme."""
    return Theme.objects.create(
        code='DARK',
        name='Dark Theme',
        primary_color='#1e40af',
        secondary_color='#64748b',
        sidebar_color='#0f172a',
        is_dark=True
    )


@pytest.fixture
def system_setting(db, user):
    """Create a test system setting."""
    return SystemSetting.objects.create(
        key='company_name',
        value='ARDT',
        value_type=SystemSetting.SettingType.STRING,
        description='Company name',
        category='general',
        updated_by=user
    )


@pytest.fixture
def number_sequence(db):
    """Create a test number sequence."""
    return NumberSequence.objects.create(
        code='WO',
        name='Work Order Sequence',
        prefix='WO-',
        suffix='',
        padding=6,
        current_value=100,
        increment_by=1
    )


# =============================================================================
# DEPARTMENT MODEL TESTS
# =============================================================================

class TestDepartmentModel:
    """Tests for the Department model."""

    def test_create_department(self, db):
        """Test creating a department."""
        dept = Department.objects.create(
            code='TEST',
            name='Test Department'
        )
        assert dept.pk is not None
        assert dept.is_active is True

    def test_department_str(self, department):
        """Test the __str__ method."""
        expected = 'MFG - Manufacturing'
        assert str(department) == expected

    def test_department_unique_code(self, department):
        """Test that code must be unique."""
        with pytest.raises(IntegrityError):
            Department.objects.create(
                code='MFG',  # Duplicate
                name='Another Manufacturing'
            )

    def test_department_arabic_name(self, department):
        """Test Arabic name field."""
        assert department.name_ar == 'التصنيع'

    def test_department_hierarchy(self, department, child_department):
        """Test parent-child relationship."""
        assert child_department.parent == department
        assert child_department in department.children.all()

    def test_department_full_path(self, department, child_department):
        """Test full_path property."""
        assert child_department.full_path == 'Manufacturing > Quality Control'

    def test_department_full_path_no_parent(self, department):
        """Test full_path for root department."""
        assert department.full_path == 'Manufacturing'

    def test_department_manager(self, department, manager):
        """Test department manager assignment."""
        assert department.manager == manager

    def test_department_null_manager(self, db):
        """Test department without manager."""
        dept = Department.objects.create(
            code='NO-MGR',
            name='No Manager Department',
            manager=None
        )
        assert dept.manager is None

    def test_department_timestamps(self, department):
        """Test auto-generated timestamps."""
        assert department.created_at is not None
        assert department.updated_at is not None


# =============================================================================
# POSITION MODEL TESTS
# =============================================================================

class TestPositionModel:
    """Tests for the Position model."""

    def test_create_position(self, db):
        """Test creating a position."""
        position = Position.objects.create(
            code='TEST-POS',
            title='Test Position',
            level=1
        )
        assert position.pk is not None
        assert position.is_active is True

    def test_position_str(self, position):
        """Test the __str__ method."""
        assert str(position) == 'QC Inspector'

    def test_position_unique_code(self, position):
        """Test that code must be unique."""
        with pytest.raises(IntegrityError):
            Position.objects.create(
                code='QC-INSP',  # Duplicate
                title='Another QC Inspector'
            )

    def test_position_arabic_title(self, position):
        """Test Arabic title field."""
        assert position.title_ar == 'مفتش الجودة'

    def test_position_department_relationship(self, position, department):
        """Test position-department relationship."""
        assert position.department == department
        assert position in department.positions.all()

    def test_position_level(self, position):
        """Test position level."""
        assert position.level == 2

    def test_position_null_department(self, db):
        """Test position without department."""
        position = Position.objects.create(
            code='EXEC-001',
            title='Executive',
            department=None,
            level=5
        )
        assert position.department is None


# =============================================================================
# THEME MODEL TESTS
# =============================================================================

class TestThemeModel:
    """Tests for the Theme model."""

    def test_create_theme(self, db):
        """Test creating a theme."""
        theme = Theme.objects.create(
            code='LIGHT',
            name='Light Theme',
            is_dark=False
        )
        assert theme.pk is not None
        assert theme.is_active is True

    def test_theme_str(self, theme):
        """Test the __str__ method."""
        assert str(theme) == 'Dark Theme'

    def test_theme_unique_code(self, theme):
        """Test that code must be unique."""
        with pytest.raises(IntegrityError):
            Theme.objects.create(
                code='DARK',  # Duplicate
                name='Another Dark Theme'
            )

    def test_theme_colors(self, theme):
        """Test theme color fields."""
        assert theme.primary_color == '#1e40af'
        assert theme.secondary_color == '#64748b'
        assert theme.sidebar_color == '#0f172a'

    def test_theme_is_dark(self, theme):
        """Test dark mode flag."""
        assert theme.is_dark is True

    def test_theme_default_flag(self, db):
        """Test default theme flag."""
        theme = Theme.objects.create(
            code='DEFAULT',
            name='Default Theme',
            is_default=True
        )
        assert theme.is_default is True


# =============================================================================
# SYSTEM SETTING MODEL TESTS
# =============================================================================

class TestSystemSettingModel:
    """Tests for the SystemSetting model."""

    def test_create_setting(self, db):
        """Test creating a system setting."""
        setting = SystemSetting.objects.create(
            key='test_key',
            value='test_value'
        )
        assert setting.pk is not None

    def test_setting_str(self, system_setting):
        """Test the __str__ method."""
        assert str(system_setting) == 'company_name: ARDT'

    def test_setting_unique_key(self, system_setting):
        """Test that key must be unique."""
        with pytest.raises(IntegrityError):
            SystemSetting.objects.create(
                key='company_name',  # Duplicate
                value='Different Company'
            )

    def test_setting_get_value_string(self, db):
        """Test get_value for STRING type."""
        setting = SystemSetting.objects.create(
            key='str_setting',
            value='hello',
            value_type=SystemSetting.SettingType.STRING
        )
        assert setting.get_value() == 'hello'

    def test_setting_get_value_integer(self, db):
        """Test get_value for INTEGER type."""
        setting = SystemSetting.objects.create(
            key='int_setting',
            value='42',
            value_type=SystemSetting.SettingType.INTEGER
        )
        assert setting.get_value() == 42

    def test_setting_get_value_boolean_true(self, db):
        """Test get_value for BOOLEAN type (true)."""
        setting = SystemSetting.objects.create(
            key='bool_true',
            value='true',
            value_type=SystemSetting.SettingType.BOOLEAN
        )
        assert setting.get_value() is True

    def test_setting_get_value_boolean_false(self, db):
        """Test get_value for BOOLEAN type (false)."""
        setting = SystemSetting.objects.create(
            key='bool_false',
            value='false',
            value_type=SystemSetting.SettingType.BOOLEAN
        )
        assert setting.get_value() is False

    def test_setting_get_value_json(self, db):
        """Test get_value for JSON type."""
        import json
        json_data = {'key1': 'value1', 'key2': 123}
        setting = SystemSetting.objects.create(
            key='json_setting',
            value=json.dumps(json_data),
            value_type=SystemSetting.SettingType.JSON
        )
        result = setting.get_value()
        assert result['key1'] == 'value1'
        assert result['key2'] == 123

    def test_setting_category(self, db):
        """Test setting category."""
        setting = SystemSetting.objects.create(
            key='email_host',
            value='smtp.example.com',
            category='email'
        )
        assert setting.category == 'email'

    def test_setting_editable_flag(self, db):
        """Test is_editable flag."""
        setting = SystemSetting.objects.create(
            key='readonly_key',
            value='readonly_value',
            is_editable=False
        )
        assert setting.is_editable is False


# =============================================================================
# NUMBER SEQUENCE MODEL TESTS
# =============================================================================

class TestNumberSequenceModel:
    """Tests for the NumberSequence model."""

    def test_create_sequence(self, db):
        """Test creating a number sequence."""
        seq = NumberSequence.objects.create(
            code='TEST-SEQ',
            name='Test Sequence'
        )
        assert seq.pk is not None
        assert seq.current_value == 0

    def test_sequence_str(self, number_sequence):
        """Test the __str__ method."""
        expected = 'WO: WO-000100'
        assert str(number_sequence) == expected

    def test_sequence_unique_code(self, number_sequence):
        """Test that code must be unique."""
        with pytest.raises(IntegrityError):
            NumberSequence.objects.create(
                code='WO',  # Duplicate
                name='Another WO Sequence'
            )

    def test_get_formatted_number(self, number_sequence):
        """Test get_formatted_number method."""
        assert number_sequence.get_formatted_number() == 'WO-000100'

    def test_get_next_number(self, number_sequence):
        """Test get_next_number method."""
        initial_value = number_sequence.current_value
        next_num = number_sequence.get_next_number()

        assert number_sequence.current_value == initial_value + 1
        assert next_num == 'WO-000101'

    def test_sequence_padding(self, db):
        """Test different padding values."""
        seq = NumberSequence.objects.create(
            code='PAD-TEST',
            name='Padding Test',
            prefix='NUM-',
            padding=3,
            current_value=5
        )
        assert seq.get_formatted_number() == 'NUM-005'

    def test_sequence_with_suffix(self, db):
        """Test sequence with suffix."""
        seq = NumberSequence.objects.create(
            code='SUF-TEST',
            name='Suffix Test',
            prefix='PRE-',
            suffix='-2024',
            padding=4,
            current_value=1
        )
        assert seq.get_formatted_number() == 'PRE-0001-2024'

    def test_sequence_increment_by(self, db):
        """Test custom increment value."""
        seq = NumberSequence.objects.create(
            code='INC-TEST',
            name='Increment Test',
            prefix='',
            padding=3,
            current_value=0,
            increment_by=10
        )
        seq.get_next_number()
        assert seq.current_value == 10

    def test_sequence_reset_period(self, db):
        """Test reset period field."""
        seq = NumberSequence.objects.create(
            code='YEARLY-TEST',
            name='Yearly Reset Test',
            reset_period='YEARLY'
        )
        assert seq.reset_period == 'YEARLY'


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestOrganizationEdgeCases:
    """Edge case tests for organization models."""

    def test_deep_department_hierarchy(self, department):
        """Test deeply nested department hierarchy."""
        current = department
        for i in range(5):
            child = Department.objects.create(
                code=f'DEEP-{i}',
                name=f'Deep Level {i}',
                parent=current
            )
            current = child

        # Check full path of deepest
        assert 'Manufacturing' in current.full_path
        assert 'Deep Level 4' in current.full_path

    def test_many_positions_per_department(self, department):
        """Test department with many positions."""
        for i in range(10):
            Position.objects.create(
                code=f'POS-{i:03d}',
                title=f'Position {i}',
                department=department,
                level=i % 5 + 1
            )

        assert department.positions.count() == 10

    def test_sequence_large_numbers(self, db):
        """Test sequence with large numbers."""
        seq = NumberSequence.objects.create(
            code='LARGE-SEQ',
            name='Large Sequence',
            prefix='LG-',
            padding=10,
            current_value=999999999
        )
        assert seq.get_formatted_number() == 'LG-0999999999'

    def test_setting_long_value(self, db):
        """Test setting with long value."""
        long_value = 'X' * 10000
        setting = SystemSetting.objects.create(
            key='long_setting',
            value=long_value,
            value_type=SystemSetting.SettingType.TEXT
        )
        assert len(setting.value) == 10000

    def test_special_characters_in_names(self, db):
        """Test special characters in department/position names."""
        dept = Department.objects.create(
            code='SPECIAL',
            name='R&D Department (Alpha/Beta)',
            location='Floor 1 - Section A/B'
        )
        assert '&' in dept.name
        assert '/' in dept.location
