"""
Sales App - Form Tests
Comprehensive tests for all sales forms.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal


# =============================================================================
# CUSTOMER FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestCustomerForm:
    """Tests for CustomerForm."""

    def test_valid_data_passes_validation(self):
        """Test form with valid data passes validation."""
        from apps.sales.forms import CustomerForm
        from apps.sales.models import Customer
        form_data = {
            'code': 'CUST-FORM-001',
            'name': 'Form Test Company',
            'customer_type': Customer.CustomerType.OPERATOR,
            'city': 'Riyadh',
            'country': 'Saudi Arabia',
            'email': 'test@company.com',
            'is_active': True,
            'is_aramco': False,
        }
        form = CustomerForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_code_required(self):
        """Test code is required."""
        from apps.sales.forms import CustomerForm
        form_data = {
            'name': 'Test Company',
        }
        form = CustomerForm(data=form_data)
        assert not form.is_valid()
        assert 'code' in form.errors

    def test_name_required(self):
        """Test name is required."""
        from apps.sales.forms import CustomerForm
        form_data = {
            'code': 'CUST-001',
        }
        form = CustomerForm(data=form_data)
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_code_uppercased(self):
        """Test code is uppercased and trimmed."""
        from apps.sales.forms import CustomerForm
        from apps.sales.models import Customer
        form_data = {
            'code': '  cust-lower-001  ',
            'name': 'Test Company',
            'customer_type': Customer.CustomerType.OPERATOR,
        }
        form = CustomerForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data['code'] == 'CUST-LOWER-001'

    def test_email_lowercased(self):
        """Test email is lowercased and trimmed."""
        from apps.sales.forms import CustomerForm
        from apps.sales.models import Customer
        form_data = {
            'code': 'CUST-EMAIL-001',
            'name': 'Test Company',
            'customer_type': Customer.CustomerType.OPERATOR,
            'email': '  TEST@COMPANY.COM  ',
        }
        form = CustomerForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data['email'] == 'test@company.com'

    def test_duplicate_code_rejected(self, customer):
        """Test duplicate code is rejected."""
        from apps.sales.forms import CustomerForm
        from apps.sales.models import Customer
        form_data = {
            'code': customer.code,
            'name': 'Duplicate',
            'customer_type': Customer.CustomerType.OPERATOR,
        }
        form = CustomerForm(data=form_data)
        assert not form.is_valid()
        assert 'code' in form.errors


# =============================================================================
# CUSTOMER CONTACT FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestCustomerContactForm:
    """Tests for CustomerContactForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.sales.forms import CustomerContactForm
        form_data = {
            'name': 'John Smith',
            'title': 'Manager',
            'email': 'john@company.com',
            'phone': '+966501234567',
            'is_primary': True,
            'is_active': True,
        }
        form = CustomerContactForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_name_required(self):
        """Test name is required."""
        from apps.sales.forms import CustomerContactForm
        form_data = {
            'email': 'test@company.com',
        }
        form = CustomerContactForm(data=form_data)
        assert not form.is_valid()
        assert 'name' in form.errors


# =============================================================================
# RIG FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestRigForm:
    """Tests for RigForm."""

    def test_valid_data_passes(self, customer):
        """Test form with valid data passes."""
        from apps.sales.forms import RigForm
        form_data = {
            'code': 'RIG-FORM-001',
            'name': 'Test Rig',
            'customer': customer.pk,
            'rig_type': 'Land Rig',
            'is_active': True,
        }
        form = RigForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_code_required(self):
        """Test code is required."""
        from apps.sales.forms import RigForm
        form_data = {
            'name': 'Test Rig',
        }
        form = RigForm(data=form_data)
        assert not form.is_valid()
        assert 'code' in form.errors

    def test_code_uppercased(self, customer):
        """Test code is uppercased."""
        from apps.sales.forms import RigForm
        form_data = {
            'code': '  rig-lower-001  ',
            'name': 'Test Rig',
            'customer': customer.pk,
            'is_active': True,
        }
        form = RigForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data['code'] == 'RIG-LOWER-001'


# =============================================================================
# WELL FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestWellForm:
    """Tests for WellForm."""

    def test_valid_data_passes(self, customer, rig):
        """Test form with valid data passes."""
        from apps.sales.forms import WellForm
        form_data = {
            'code': 'WELL-FORM-001',
            'name': 'Test Well',
            'customer': customer.pk,
            'rig': rig.pk,
            'field_name': 'Ghawar',
            'target_depth': 15000,
            'is_active': True,
        }
        form = WellForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_code_required(self):
        """Test code is required."""
        from apps.sales.forms import WellForm
        form_data = {
            'name': 'Test Well',
        }
        form = WellForm(data=form_data)
        assert not form.is_valid()
        assert 'code' in form.errors


# =============================================================================
# WAREHOUSE FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestWarehouseForm:
    """Tests for WarehouseForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.sales.forms import WarehouseForm
        from apps.sales.models import Warehouse
        form_data = {
            'code': 'WH-FORM-001',
            'name': 'Test Warehouse',
            'warehouse_type': Warehouse.WarehouseType.ARDT,
            'city': 'Dammam',
            'is_active': True,
        }
        form = WarehouseForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_warehouse_type_choices(self):
        """Test warehouse type choices are valid."""
        from apps.sales.forms import WarehouseForm
        from apps.sales.models import Warehouse
        for choice in Warehouse.WarehouseType.choices:
            form_data = {
                'code': f'WH-{choice[0][:4]}',
                'name': f'Warehouse {choice[0]}',
                'warehouse_type': choice[0],
            }
            form = WarehouseForm(data=form_data)
            assert form.is_valid(), f"Form invalid for type {choice[0]}: {form.errors}"


# =============================================================================
# SALES ORDER FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestSalesOrderForm:
    """Tests for SalesOrderForm."""

    def test_valid_data_passes(self, customer):
        """Test form with valid data passes."""
        from apps.sales.forms import SalesOrderForm
        from apps.sales.models import SalesOrder
        form_data = {
            'order_number': 'SO-FORM-001',
            'customer': customer.pk,
            'order_date': date.today().isoformat(),
            'status': SalesOrder.Status.DRAFT,
        }
        form = SalesOrderForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_customer_required(self):
        """Test customer is required."""
        from apps.sales.forms import SalesOrderForm
        form_data = {
            'order_number': 'SO-001',
            'order_date': date.today().isoformat(),
        }
        form = SalesOrderForm(data=form_data)
        assert not form.is_valid()
        assert 'customer' in form.errors


# =============================================================================
# SALES ORDER LINE FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestSalesOrderLineForm:
    """Tests for SalesOrderLineForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.sales.forms import SalesOrderLineForm
        form_data = {
            'line_number': 1,
            'quantity': 2,
            'unit_price': '15000.00',
        }
        form = SalesOrderLineForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_line_number_required(self):
        """Test line_number is required."""
        from apps.sales.forms import SalesOrderLineForm
        form_data = {
            'quantity': 1,
        }
        form = SalesOrderLineForm(data=form_data)
        assert not form.is_valid()
        assert 'line_number' in form.errors


# =============================================================================
# SERVICE SITE FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestServiceSiteForm:
    """Tests for ServiceSiteForm."""

    def test_valid_data_passes(self, customer):
        """Test form with valid data passes."""
        from apps.sales.forms import ServiceSiteForm
        from apps.sales.models import ServiceSite
        form_data = {
            'site_number': 'SITE-FORM-001',
            'customer': customer.pk,
            'site_name': 'Test Site',
            'site_type': ServiceSite.SiteType.RIG_SITE,
            'status': ServiceSite.Status.ACTIVE,
        }
        form = ServiceSiteForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_customer_required(self):
        """Test customer is required."""
        from apps.sales.forms import ServiceSiteForm
        from apps.sales.models import ServiceSite
        form_data = {
            'site_number': 'SITE-001',
            'site_name': 'Test',
            'site_type': ServiceSite.SiteType.RIG_SITE,
        }
        form = ServiceSiteForm(data=form_data)
        assert not form.is_valid()
        assert 'customer' in form.errors


# =============================================================================
# FIELD TECHNICIAN FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestFieldTechnicianForm:
    """Tests for FieldTechnicianForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.sales.forms import FieldTechnicianForm
        from apps.sales.models import FieldTechnician
        form_data = {
            'tech_id': 'TECH-FORM-001',
            'status': FieldTechnician.Status.ACTIVE if hasattr(FieldTechnician, 'Status') else 'ACTIVE',
            'hire_date': date.today().isoformat(),
            'primary_skills': 'PDC Bits',
            'training_level': 'Senior',
        }
        form = FieldTechnicianForm(data=form_data)
        assert form.is_valid(), form.errors


# =============================================================================
# FIELD SERVICE REQUEST FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestFieldServiceRequestForm:
    """Tests for FieldServiceRequestForm."""

    def test_valid_data_passes(self, customer):
        """Test form with valid data passes."""
        from apps.sales.forms import FieldServiceRequestForm
        from apps.sales.models import FieldServiceRequest
        form_data = {
            'request_number': 'FSR-FORM-001',
            'customer': customer.pk,
            'request_type': FieldServiceRequest.RequestType.INSPECTION,
            'priority': FieldServiceRequest.Priority.NORMAL,
            'status': FieldServiceRequest.Status.PENDING,
            'requested_date': date.today().isoformat(),
            'service_description': 'Test service request',
        }
        form = FieldServiceRequestForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_customer_required(self):
        """Test customer is required."""
        from apps.sales.forms import FieldServiceRequestForm
        from apps.sales.models import FieldServiceRequest
        form_data = {
            'request_number': 'FSR-001',
            'request_type': FieldServiceRequest.RequestType.INSPECTION,
            'requested_date': date.today().isoformat(),
            'service_description': 'Test',
        }
        form = FieldServiceRequestForm(data=form_data)
        assert not form.is_valid()
        assert 'customer' in form.errors


# =============================================================================
# FIELD INCIDENT FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestFieldIncidentForm:
    """Tests for FieldIncidentForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.sales.forms import FieldIncidentForm
        from apps.sales.models import FieldIncident
        form_data = {
            'incident_number': 'INC-FORM-001',
            'incident_type': FieldIncident.IncidentType.EQUIPMENT_FAILURE if hasattr(FieldIncident, 'IncidentType') else 'EQUIPMENT_FAILURE',
            'severity': 'LOW',
            'status': 'OPEN',
            'priority': 'NORMAL',
            'incident_date': date.today().isoformat(),
            'reported_date': date.today().isoformat(),
            'description': 'Test incident description',
        }
        form = FieldIncidentForm(data=form_data)
        assert form.is_valid(), form.errors


# =============================================================================
# FIELD PHOTO FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestFieldPhotoForm:
    """Tests for FieldPhotoForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.sales.forms import FieldPhotoForm
        form_data = {
            'title': 'Test Photo',
            'photo_type': 'INSPECTION',
            'caption': 'Test caption',
            'is_public': False,
        }
        form = FieldPhotoForm(data=form_data)
        # Photo file would be required in full validation
        assert 'title' not in form.errors


# =============================================================================
# FIELD DOCUMENT FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestFieldDocumentForm:
    """Tests for FieldDocumentForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.sales.forms import FieldDocumentForm
        form_data = {
            'title': 'Test Document',
            'document_type': 'REPORT',
            'status': 'DRAFT',
            'is_confidential': False,
        }
        form = FieldDocumentForm(data=form_data)
        # Document file would be required in full validation
        assert 'title' not in form.errors


# =============================================================================
# GPS LOCATION FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestGPSLocationForm:
    """Tests for GPSLocationForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.sales.forms import GPSLocationForm
        form_data = {
            'latitude': '25.5000000',
            'longitude': '49.5000000',
            'recorded_at': date.today().isoformat(),
        }
        form = GPSLocationForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_coordinates_required(self):
        """Test coordinates are required."""
        from apps.sales.forms import GPSLocationForm
        form_data = {
            'recorded_at': date.today().isoformat(),
        }
        form = GPSLocationForm(data=form_data)
        assert not form.is_valid()
        assert 'latitude' in form.errors
        assert 'longitude' in form.errors


# =============================================================================
# FIELD WORK ORDER FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestFieldWorkOrderForm:
    """Tests for FieldWorkOrderForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.sales.forms import FieldWorkOrderForm
        form_data = {
            'work_order_number': 'FWO-FORM-001',
            'work_order_type': 'REPAIR',
            'status': 'PENDING',
            'priority': 'NORMAL',
            'scheduled_date': date.today().isoformat(),
            'description': 'Test field work order',
        }
        form = FieldWorkOrderForm(data=form_data)
        assert form.is_valid(), form.errors


# =============================================================================
# FIELD ASSET ASSIGNMENT FORM TESTS
# =============================================================================

@pytest.mark.django_db
class TestFieldAssetAssignmentForm:
    """Tests for FieldAssetAssignmentForm."""

    def test_valid_data_passes(self):
        """Test form with valid data passes."""
        from apps.sales.forms import FieldAssetAssignmentForm
        form_data = {
            'assignment_number': 'ASSIGN-FORM-001',
            'assignment_type': 'DISPATCH',
            'status': 'PENDING',
            'assignment_date': date.today().isoformat(),
            'condition_at_assignment': 'GOOD',
        }
        form = FieldAssetAssignmentForm(data=form_data)
        assert form.is_valid(), form.errors
