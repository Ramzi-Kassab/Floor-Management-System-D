"""
Tests for Quality app views.
"""
import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

from apps.common.tests.base import BaseCRUDTest, BasePermissionTest
from apps.quality.models import Inspection, NCR

User = get_user_model()


class TestInspectionViews(BaseCRUDTest):
    """Tests for Inspection views."""

    app_name = 'quality'
    model_name = 'inspection'
    url_list = 'quality:inspection_list'
    url_detail = 'quality:inspection_detail'
    url_create = 'quality:inspection_create'
    url_update = 'quality:inspection_update'
    url_delete = None
    template_list = 'quality/inspection_list.html'
    template_detail = 'quality/inspection_detail.html'
    template_form = 'quality/inspection_form.html'
    test_delete = False

    @pytest.fixture
    def test_object(self, inspection):
        """Use inspection fixture as test object."""
        return inspection

    @pytest.fixture
    def valid_data(self, work_order):
        """Valid data for inspection creation."""
        from datetime import date
        return {
            'inspection_number': 'INSP-NEW',
            'inspection_type': Inspection.InspectionType.INCOMING,
            'work_order': work_order.pk,
            'scheduled_date': date.today(),
            'status': Inspection.Status.SCHEDULED,
        }

    def test_inspection_complete_requires_login(self, client, inspection):
        """Test inspection complete requires authentication."""
        url = reverse('quality:inspection_complete', kwargs={'pk': inspection.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_inspection_complete_get(self, authenticated_client, inspection):
        """Test inspection complete form."""
        url = reverse('quality:inspection_complete', kwargs={'pk': inspection.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestNCRViews(BaseCRUDTest):
    """Tests for NCR views."""

    app_name = 'quality'
    model_name = 'ncr'
    url_list = 'quality:ncr_list'
    url_detail = 'quality:ncr_detail'
    url_create = 'quality:ncr_create'
    url_update = 'quality:ncr_update'
    url_delete = None
    template_list = 'quality/ncr_list.html'
    template_detail = 'quality/ncr_detail.html'
    template_form = 'quality/ncr_form.html'
    test_delete = False

    @pytest.fixture
    def test_object(self, ncr):
        """Use NCR fixture as test object."""
        return ncr

    @pytest.fixture
    def valid_data(self, work_order, test_user):
        """Valid data for NCR creation."""
        from django.utils import timezone
        return {
            'ncr_number': 'NCR-NEW',
            'work_order': work_order.pk,
            'title': 'New NCR',
            'description': 'Test description',
            'severity': NCR.Severity.MINOR,
            'status': NCR.Status.OPEN,
            'detected_at': timezone.now(),
        }

    def test_ncr_disposition_requires_login(self, client, ncr):
        """Test NCR disposition requires authentication."""
        url = reverse('quality:ncr_disposition', kwargs={'pk': ncr.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_ncr_disposition_get(self, authenticated_client, ncr):
        """Test NCR disposition form."""
        url = reverse('quality:ncr_disposition', kwargs={'pk': ncr.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestNCRPhotoViews:
    """Tests for NCR Photo views."""

    def test_photo_upload_requires_login(self, client, ncr):
        """Test photo upload requires authentication."""
        url = reverse('quality:ncr_photo_upload', kwargs={'pk': ncr.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_photo_upload_get(self, authenticated_client, ncr):
        """Test photo upload form."""
        url = reverse('quality:ncr_photo_upload', kwargs={'pk': ncr.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestQualityPermissions(BasePermissionTest):
    """Test quality permissions."""

    url_name = 'quality:inspection_list'

    def test_inspection_list_requires_auth(self, client):
        """Test inspection list requires authentication."""
        url = reverse(self.url_name)
        response = client.get(url)
        assert response.status_code == 302
