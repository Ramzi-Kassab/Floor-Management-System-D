"""
Tests for Procedures app views.
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
def procedure(db, test_user):
    """Create a test procedure."""
    from apps.procedures.models import Procedure
    return Procedure.objects.create(
        code='PROC-001',
        name='Test Procedure',
        description='Test description',
        version='1.0',
        status='ACTIVE',
        created_by=test_user
    )


@pytest.fixture
def procedure_step(db, test_user, procedure):
    """Create a test procedure step."""
    from apps.procedures.models import ProcedureStep
    return ProcedureStep.objects.create(
        procedure=procedure,
        step_number=1,
        title='Step 1',
        instruction='Do something',
        is_mandatory=True,
        created_by=test_user
    )


class TestProcedureViews(BaseCRUDTest):
    """Tests for Procedure views."""

    app_name = 'procedures'
    model_name = 'procedure'
    url_list = 'procedures:procedure_list'
    url_detail = 'procedures:procedure_detail'
    url_create = 'procedures:procedure_create'
    url_update = 'procedures:procedure_update'
    url_delete = None
    template_list = 'procedures/procedure_list.html'
    template_detail = 'procedures/procedure_detail.html'
    template_form = 'procedures/procedure_form.html'
    test_delete = False

    @pytest.fixture
    def test_object(self, procedure):
        return procedure

    @pytest.fixture
    def valid_data(self):
        return {
            'code': 'PROC-NEW',
            'name': 'New Procedure',
            'description': 'New description',
            'version': '1.0',
            'status': 'DRAFT',
        }


class TestProcedureStepViews:
    """Tests for ProcedureStep views."""

    def test_step_create_requires_login(self, client, procedure):
        url = reverse('procedures:step_create', kwargs={'pk': procedure.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_step_create_get(self, authenticated_client, procedure):
        url = reverse('procedures:step_create', kwargs={'pk': procedure.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_step_update_get(self, authenticated_client, procedure, procedure_step):
        url = reverse('procedures:step_update', kwargs={
            'pk': procedure.pk,
            'step_pk': procedure_step.pk
        })
        response = authenticated_client.get(url)
        assert response.status_code == 200

    def test_step_delete_requires_login(self, client, procedure, procedure_step):
        url = reverse('procedures:step_delete', kwargs={
            'pk': procedure.pk,
            'step_pk': procedure_step.pk
        })
        response = client.post(url)
        assert response.status_code == 302
