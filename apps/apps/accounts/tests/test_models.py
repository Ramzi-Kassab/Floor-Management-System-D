"""
Tests for Accounts app models.
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


class TestUserModel:
    """Tests for custom User model."""

    def test_create_user(self, db):
        """Test creating a regular user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.pk is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_user_without_email(self, db):
        """Test creating a user without email."""
        user = User.objects.create_user(
            username='noemail',
            password='testpass123'
        )
        assert user.pk is not None
        assert user.email == ''

    def test_create_superuser(self, db):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        assert admin.pk is not None
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_user_str(self, db):
        """Test user string representation."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        assert str(user) == 'testuser'

    def test_user_employee_id(self, db):
        """Test user with employee ID."""
        user = User.objects.create_user(
            username='employee1',
            password='testpass123',
            employee_id='EMP-001'
        )
        assert user.employee_id == 'EMP-001'

    def test_user_phone_fields(self, db):
        """Test user phone fields."""
        user = User.objects.create_user(
            username='phoneuser',
            password='testpass123',
            phone='555-0100',
            phone_extension='123',
            mobile='555-0101'
        )
        assert user.phone == '555-0100'
        assert user.phone_extension == '123'
        assert user.mobile == '555-0101'

    def test_user_localization(self, db):
        """Test user localization settings."""
        user = User.objects.create_user(
            username='localeuser',
            password='testpass123',
            language='ar',
            timezone='Asia/Riyadh'
        )
        assert user.language == 'ar'
        assert user.timezone == 'Asia/Riyadh'

    def test_user_defaults(self, db):
        """Test user default values."""
        user = User.objects.create_user(
            username='defaultuser',
            password='testpass123'
        )
        assert user.language == 'en'
        assert user.timezone == 'Asia/Riyadh'

    def test_user_unique_username(self, db):
        """Test username uniqueness."""
        User.objects.create_user(
            username='unique',
            password='testpass123'
        )
        with pytest.raises(Exception):
            User.objects.create_user(
                username='unique',
                password='different'
            )

    def test_user_unique_employee_id(self, db):
        """Test employee_id uniqueness."""
        User.objects.create_user(
            username='user1',
            password='testpass123',
            employee_id='EMP-UNIQUE'
        )
        with pytest.raises(Exception):
            User.objects.create_user(
                username='user2',
                password='testpass123',
                employee_id='EMP-UNIQUE'
            )

    def test_create_user_without_username_fails(self, db):
        """Test creating user without username raises error."""
        with pytest.raises(ValueError):
            User.objects.create_user(
                username='',
                password='testpass123'
            )

    def test_superuser_must_be_staff(self, db):
        """Test superuser must have is_staff=True."""
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                username='badsuper',
                password='testpass123',
                is_staff=False
            )

    def test_superuser_must_be_superuser(self, db):
        """Test superuser must have is_superuser=True."""
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                username='badsuper',
                password='testpass123',
                is_superuser=False
            )
