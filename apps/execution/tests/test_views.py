"""
Tests for Execution app views.
"""
import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

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
def work_order(db, test_user):
    """Create a test work order."""
    from apps.workorders.models import WorkOrder
    return WorkOrder.objects.create(
        work_order_number='WO-EXEC-001',
        title='Test Work Order',
        description='Test description',
        status='IN_PROGRESS',
        created_by=test_user
    )


@pytest.fixture
def procedure(db, test_user):
    """Create a test procedure."""
    from apps.procedures.models import Procedure
    return Procedure.objects.create(
        code='PROC-EXEC-001',
        name='Test Procedure',
        description='Test description',
        version='1.0',
        status='ACTIVE',
        created_by=test_user
    )


@pytest.fixture
def procedure_execution(db, test_user, work_order, procedure):
    """Create a test procedure execution."""
    from apps.execution.models import ProcedureExecution
    return ProcedureExecution.objects.create(
        work_order=work_order,
        procedure=procedure,
        status='IN_PROGRESS',
        executed_by=test_user
    )


class TestExecutionListView:
    """Tests for execution list view."""

    def test_list_requires_login(self, client):
        url = reverse('execution:list')
        response = client.get(url)
        assert response.status_code == 302

    def test_list_authenticated(self, authenticated_client):
        url = reverse('execution:list')
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestExecutionDetailView:
    """Tests for execution detail view."""

    def test_detail_requires_login(self, client, procedure_execution):
        url = reverse('execution:detail', kwargs={'pk': procedure_execution.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_detail_authenticated(self, authenticated_client, procedure_execution):
        url = reverse('execution:detail', kwargs={'pk': procedure_execution.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200


class TestExecutionStartView:
    """Tests for starting execution."""

    def test_start_requires_login(self, client, work_order, procedure):
        url = reverse('execution:start', kwargs={
            'wo_pk': work_order.pk,
            'procedure_pk': procedure.pk
        })
        response = client.get(url)
        assert response.status_code == 302

    def test_start_authenticated(self, authenticated_client, work_order, procedure):
        url = reverse('execution:start', kwargs={
            'wo_pk': work_order.pk,
            'procedure_pk': procedure.pk
        })
        response = authenticated_client.get(url)
        assert response.status_code in [200, 302]


class TestExecutionControlViews:
    """Tests for execution control views (pause/resume)."""

    def test_pause_requires_login(self, client, procedure_execution):
        url = reverse('execution:pause', kwargs={'pk': procedure_execution.pk})
        response = client.post(url)
        assert response.status_code == 302

    def test_resume_requires_login(self, client, procedure_execution):
        url = reverse('execution:resume', kwargs={'pk': procedure_execution.pk})
        response = client.post(url)
        assert response.status_code == 302

    def test_pause_authenticated(self, authenticated_client, procedure_execution):
        url = reverse('execution:pause', kwargs={'pk': procedure_execution.pk})
        response = authenticated_client.post(url)
        assert response.status_code in [200, 302]
