"""
ARDT FMS - Sales Forms
Version: 5.4 - Sprint 2

Forms for customer, rig, well, and contact management.
"""

from django import forms
from django.core.exceptions import ValidationError

from .models import Customer, CustomerContact, Rig, Warehouse, Well

# Tailwind CSS classes for form widgets
TAILWIND_INPUT = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
TAILWIND_SELECT = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
TAILWIND_TEXTAREA = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
TAILWIND_CHECKBOX = "h-4 w-4 text-ardt-blue focus:ring-ardt-blue border-gray-300 rounded"


class CustomerForm(forms.ModelForm):
    """
    Customer creation and edit form.
    """

    class Meta:
        model = Customer
        fields = [
            # Identity
            "code",
            "name",
            "name_ar",
            "customer_type",
            # Contact
            "address",
            "city",
            "country",
            "phone",
            "email",
            "website",
            # Business
            "tax_id",
            "credit_limit",
            "payment_terms",
            # Status
            "is_active",
            "is_aramco",
            # Management
            "account_manager",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., CUST-001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Company Name"}),
            "name_ar": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "اسم الشركة", "dir": "rtl"}),
            "customer_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "address": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Full address"}),
            "city": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "City"}),
            "country": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Country"}),
            "phone": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "+966 XX XXX XXXX"}),
            "email": forms.EmailInput(attrs={"class": TAILWIND_INPUT, "placeholder": "contact@company.com"}),
            "website": forms.URLInput(attrs={"class": TAILWIND_INPUT, "placeholder": "https://www.company.com"}),
            "tax_id": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Tax ID / VAT Number"}),
            "credit_limit": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01", "placeholder": "0.00"}),
            "payment_terms": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., Net 30"}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "is_aramco": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "account_manager": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }

    def clean_code(self):
        """Ensure customer code is uppercase."""
        code = self.cleaned_data.get("code")
        if code:
            code = code.upper().strip()
            # Check uniqueness for new customers
            if not self.instance.pk:
                if Customer.objects.filter(code=code).exists():
                    raise ValidationError("A customer with this code already exists.")
        return code

    def clean_email(self):
        """Validate email format."""
        email = self.cleaned_data.get("email")
        if email:
            email = email.lower().strip()
        return email


class CustomerContactForm(forms.ModelForm):
    """
    Customer contact person form.
    """

    class Meta:
        model = CustomerContact
        fields = ["name", "title", "department", "email", "phone", "mobile", "is_primary", "is_active", "notes"]
        widgets = {
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Contact Name"}),
            "title": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Job Title"}),
            "department": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Department"}),
            "email": forms.EmailInput(attrs={"class": TAILWIND_INPUT, "placeholder": "contact@company.com"}),
            "phone": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Office Phone"}),
            "mobile": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Mobile Phone"}),
            "is_primary": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2, "placeholder": "Additional notes"}),
        }


class RigForm(forms.ModelForm):
    """
    Rig registration and edit form.
    """

    class Meta:
        model = Rig
        fields = ["code", "name", "customer", "contractor", "rig_type", "location", "latitude", "longitude", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., RIG-001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Rig Name"}),
            "customer": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "contractor": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "rig_type": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., Land Rig, Jack-Up"}),
            "location": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Current Location"}),
            "latitude": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0000001", "placeholder": "Latitude"}),
            "longitude": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0000001", "placeholder": "Longitude"}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter customer/contractor dropdowns to active customers only
        self.fields["customer"].queryset = Customer.objects.filter(is_active=True)
        self.fields["contractor"].queryset = Customer.objects.filter(
            is_active=True, customer_type=Customer.CustomerType.CONTRACTOR
        )

    def clean_code(self):
        """Ensure rig code is uppercase."""
        code = self.cleaned_data.get("code")
        if code:
            code = code.upper().strip()
            if not self.instance.pk:
                if Rig.objects.filter(code=code).exists():
                    raise ValidationError("A rig with this code already exists.")
        return code


class WellForm(forms.ModelForm):
    """
    Well registration and edit form.
    """

    class Meta:
        model = Well
        fields = ["code", "name", "customer", "rig", "field_name", "spud_date", "target_depth", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., WELL-001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Well Name"}),
            "customer": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "rig": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "field_name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Oil Field Name"}),
            "spud_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "target_depth": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Target Depth (ft)"}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = Customer.objects.filter(is_active=True)
        self.fields["rig"].queryset = Rig.objects.filter(is_active=True)

    def clean_code(self):
        """Ensure well code is uppercase."""
        code = self.cleaned_data.get("code")
        if code:
            code = code.upper().strip()
            if not self.instance.pk:
                if Well.objects.filter(code=code).exists():
                    raise ValidationError("A well with this code already exists.")
        return code


class WarehouseForm(forms.ModelForm):
    """
    Warehouse registration and edit form.
    """

    class Meta:
        model = Warehouse
        fields = [
            "code",
            "name",
            "warehouse_type",
            "customer",
            "address",
            "city",
            "contact_person",
            "contact_phone",
            "is_active",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., WH-001"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Warehouse Name"}),
            "warehouse_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "customer": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "address": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2, "placeholder": "Warehouse Address"}),
            "city": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "City"}),
            "contact_person": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Contact Person Name"}),
            "contact_phone": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Contact Phone"}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = Customer.objects.filter(is_active=True)
        self.fields["customer"].required = False


# =============================================================================
# SPRINT 3 FORMS - Field Service Models
# =============================================================================

from .models import (
    CustomerDocumentRequirement, SalesOrder, SalesOrderLine,
    ServiceSite, FieldTechnician, FieldServiceRequest, ServiceSchedule,
    SiteVisit, ServiceReport, FieldDrillStringRun, FieldRunData
)


class CustomerDocumentRequirementForm(forms.ModelForm):
    """Form for CustomerDocumentRequirement - Inline formset for Customer."""

    class Meta:
        model = CustomerDocumentRequirement
        fields = ['document_name', 'description', 'is_mandatory', 'notes']
        widgets = {
            'document_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'is_mandatory': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['description', 'notes']:
            self.fields[field].required = False


class SalesOrderForm(forms.ModelForm):
    """Form for SalesOrder with all key fields."""

    class Meta:
        model = SalesOrder
        fields = [
            'order_number', 'customer', 'order_date', 'expected_delivery_date',
            'status', 'priority', 'payment_terms', 'shipping_address',
            'billing_address', 'contact_person', 'special_instructions',
            'internal_notes', 'sales_rep', 'approved_by', 'approval_date'
        ]
        widgets = {
            'order_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'customer': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'order_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'priority': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'payment_terms': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'shipping_address': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'billing_address': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'contact_person': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'special_instructions': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'sales_rep': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'approved_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'approval_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['expected_delivery_date', 'priority', 'payment_terms', 'shipping_address',
                    'billing_address', 'contact_person', 'special_instructions', 'internal_notes',
                    'sales_rep', 'approved_by', 'approval_date']
        for field in optional:
            self.fields[field].required = False


class SalesOrderLineForm(forms.ModelForm):
    """Form for SalesOrderLine - Inline formset for SalesOrder."""

    class Meta:
        model = SalesOrderLine
        fields = ['line_number', 'drill_bit', 'quantity', 'unit_price',
                  'discount_percent', 'tax_rate', 'delivery_date', 'line_status',
                  'special_requirements', 'notes']
        widgets = {
            'line_number': forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'drill_bit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'quantity': forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'unit_price': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'discount_percent': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'delivery_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'line_status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'special_requirements': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['drill_bit', 'discount_percent', 'tax_rate', 'delivery_date',
                    'special_requirements', 'notes']
        for field in optional:
            self.fields[field].required = False


class ServiceSiteForm(forms.ModelForm):
    """Form for ServiceSite - Field service location management."""

    class Meta:
        model = ServiceSite
        fields = [
            'site_number', 'customer', 'site_name', 'site_type', 'status',
            'address', 'city', 'state_province', 'postal_code', 'country',
            'gps_latitude', 'gps_longitude', 'site_contact_name',
            'site_contact_phone', 'site_contact_email', 'rig_name',
            'rig_type', 'field_name', 'notes'
        ]
        widgets = {
            'site_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'customer': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'site_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'site_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'address': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'city': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'state_province': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'postal_code': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'country': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'gps_latitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.000001'}),
            'gps_longitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.000001'}),
            'site_contact_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'site_contact_phone': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'site_contact_email': forms.EmailInput(attrs={'class': TAILWIND_INPUT}),
            'rig_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'rig_type': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'field_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['address', 'city', 'state_province', 'postal_code', 'country',
                    'gps_latitude', 'gps_longitude', 'site_contact_name',
                    'site_contact_phone', 'site_contact_email', 'rig_name',
                    'rig_type', 'field_name', 'notes']
        for field in optional:
            self.fields[field].required = False


class FieldTechnicianForm(forms.ModelForm):
    """Form for FieldTechnician - Technician profile management."""

    class Meta:
        model = FieldTechnician
        fields = [
            'employee', 'tech_id', 'status', 'hire_date', 'primary_skills',
            'secondary_skills', 'certifications', 'license_number',
            'license_expiry', 'training_level', 'years_experience',
            'home_base_location', 'phone', 'emergency_contact_name',
            'emergency_contact_phone', 'availability_status', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'tech_id': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'hire_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'primary_skills': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'secondary_skills': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'certifications': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'license_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'license_expiry': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'training_level': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'years_experience': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'home_base_location': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'phone': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'emergency_contact_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'availability_status': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['employee', 'secondary_skills', 'certifications', 'license_number',
                    'license_expiry', 'years_experience', 'home_base_location',
                    'phone', 'emergency_contact_name', 'emergency_contact_phone',
                    'availability_status', 'notes']
        for field in optional:
            self.fields[field].required = False


class FieldServiceRequestForm(forms.ModelForm):
    """Form for FieldServiceRequest - Service request management."""

    class Meta:
        model = FieldServiceRequest
        fields = [
            'request_number', 'customer', 'service_site', 'request_type',
            'priority', 'status', 'requested_date', 'required_completion_date',
            'requested_by', 'service_description', 'equipment_required',
            'estimated_duration_hours', 'estimated_cost', 'assigned_technician',
            'customer_po_number', 'special_instructions', 'internal_notes'
        ]
        widgets = {
            'request_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'customer': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'request_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'priority': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'requested_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'required_completion_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'requested_by': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'service_description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 4}),
            'equipment_required': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'estimated_duration_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.5'}),
            'estimated_cost': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'assigned_technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'customer_po_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'special_instructions': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['service_site', 'required_completion_date', 'requested_by',
                    'equipment_required', 'estimated_duration_hours', 'estimated_cost',
                    'assigned_technician', 'customer_po_number', 'special_instructions',
                    'internal_notes']
        for field in optional:
            self.fields[field].required = False


class ServiceScheduleForm(forms.ModelForm):
    """Form for ServiceSchedule - Scheduling service visits."""

    class Meta:
        model = ServiceSchedule
        fields = [
            'schedule_number', 'service_request', 'technician', 'scheduled_date',
            'scheduled_start_time', 'scheduled_end_time', 'status', 'notes'
        ]
        widgets = {
            'schedule_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'service_request': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'scheduled_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'scheduled_start_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'scheduled_end_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['scheduled_start_time', 'scheduled_end_time', 'notes']
        for field in optional:
            self.fields[field].required = False


class SiteVisitForm(forms.ModelForm):
    """Form for SiteVisit - Recording site visits."""

    class Meta:
        model = SiteVisit
        fields = [
            'visit_number', 'service_request', 'schedule', 'technician',
            'visit_date', 'arrival_time', 'departure_time', 'status',
            'work_performed', 'issues_found', 'recommendations', 'notes'
        ]
        widgets = {
            'visit_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'service_request': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'schedule': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'visit_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'arrival_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'departure_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'work_performed': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 4}),
            'issues_found': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'recommendations': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['schedule', 'arrival_time', 'departure_time', 'issues_found',
                    'recommendations', 'notes']
        for field in optional:
            self.fields[field].required = False


class ServiceReportForm(forms.ModelForm):
    """Form for ServiceReport - Service report documentation."""

    class Meta:
        model = ServiceReport
        fields = [
            'report_number', 'site_visit', 'service_request', 'report_date',
            'status', 'summary', 'detailed_findings', 'actions_taken',
            'recommendations', 'follow_up_required', 'customer_signature', 'notes'
        ]
        widgets = {
            'report_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'site_visit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_request': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'report_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'summary': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'detailed_findings': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 5}),
            'actions_taken': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 4}),
            'recommendations': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'follow_up_required': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'customer_signature': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['site_visit', 'detailed_findings', 'actions_taken',
                    'recommendations', 'customer_signature', 'notes']
        for field in optional:
            self.fields[field].required = False


class FieldDrillStringRunForm(forms.ModelForm):
    """Form for FieldDrillStringRun - Recording drill string runs."""

    class Meta:
        model = FieldDrillStringRun
        fields = [
            'run_number', 'service_site', 'drill_bit', 'start_date',
            'end_date', 'status', 'depth_in', 'depth_out', 'footage_drilled',
            'hours_on_bit', 'notes'
        ]
        widgets = {
            'run_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'drill_bit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'start_date': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'depth_in': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'depth_out': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'footage_drilled': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'hours_on_bit': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['end_date', 'depth_out', 'footage_drilled', 'hours_on_bit', 'notes']
        for field in optional:
            self.fields[field].required = False


class FieldRunDataForm(forms.ModelForm):
    """Form for FieldRunData - Recording run performance data."""

    class Meta:
        model = FieldRunData
        fields = [
            'drill_string_run', 'recorded_at', 'depth', 'rop', 'wob',
            'rpm', 'torque', 'flow_rate', 'pressure', 'notes'
        ]
        widgets = {
            'drill_string_run': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'recorded_at': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'depth': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'rop': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'wob': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'rpm': forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'torque': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'flow_rate': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'pressure': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['rop', 'wob', 'rpm', 'torque', 'flow_rate', 'pressure', 'notes']
        for field in optional:
            self.fields[field].required = False
