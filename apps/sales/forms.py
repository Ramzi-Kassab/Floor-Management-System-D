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
    SiteVisit, ServiceReport, FieldDrillStringRun, FieldRunData,
    FieldPerformanceLog, FieldInspection, RunHours,
    FieldIncident, FieldDataEntry, FieldPhoto, FieldDocument,
    GPSLocation, FieldWorkOrder, FieldAssetAssignment
)


class CustomerDocumentRequirementForm(forms.ModelForm):
    """Form for CustomerDocumentRequirement - Inline formset for Customer."""

    class Meta:
        model = CustomerDocumentRequirement
        fields = ['document_type', 'description', 'is_required']
        widgets = {
            'document_type': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'is_required': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False


class SalesOrderForm(forms.ModelForm):
    """Form for SalesOrder with all key fields."""

    class Meta:
        model = SalesOrder
        fields = [
            'so_number', 'customer', 'customer_po', 'rig', 'well',
            'delivery_warehouse', 'order_date', 'required_date', 'promised_date',
            'status', 'currency', 'notes', 'internal_notes'
        ]
        widgets = {
            'so_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'customer': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'customer_po': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'rig': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'well': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'delivery_warehouse': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'order_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'required_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'promised_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'currency': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['customer_po', 'rig', 'well', 'delivery_warehouse',
                    'required_date', 'promised_date', 'notes', 'internal_notes']
        for field in optional:
            self.fields[field].required = False


class SalesOrderLineForm(forms.ModelForm):
    """Form for SalesOrderLine - Inline formset for SalesOrder."""

    class Meta:
        model = SalesOrderLine
        fields = ['line_number', 'design', 'description', 'quantity', 'unit_price',
                  'discount_percent', 'status']
        widgets = {
            'line_number': forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'design': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'description': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'quantity': forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'unit_price': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'discount_percent': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['design', 'discount_percent']
        for field in optional:
            self.fields[field].required = False


class ServiceSiteForm(forms.ModelForm):
    """Form for ServiceSite - Field service location management."""

    class Meta:
        model = ServiceSite
        fields = [
            'site_code', 'name', 'customer', 'site_type', 'status',
            'description', 'address_line1', 'address_line2', 'city',
            'state_province', 'postal_code', 'country', 'latitude', 'longitude',
            'primary_contact_name', 'primary_contact_phone', 'primary_contact_email'
        ]
        widgets = {
            'site_code': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'customer': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'site_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'address_line1': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'address_line2': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'city': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'state_province': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'postal_code': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'country': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'latitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.0000001'}),
            'longitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.0000001'}),
            'primary_contact_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'primary_contact_phone': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'primary_contact_email': forms.EmailInput(attrs={'class': TAILWIND_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['description', 'address_line2', 'state_province', 'postal_code',
                    'latitude', 'longitude', 'primary_contact_name',
                    'primary_contact_phone', 'primary_contact_email']
        for field in optional:
            self.fields[field].required = False


class FieldTechnicianForm(forms.ModelForm):
    """Form for FieldTechnician - Technician profile management."""

    class Meta:
        model = FieldTechnician
        fields = [
            'employee_id', 'user', 'name', 'email', 'phone', 'mobile',
            'hire_date', 'employment_status', 'job_title', 'department',
            'skill_level', 'specializations', 'certifications',
            'home_base_location', 'emergency_contact_name', 'emergency_contact_phone'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'user': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'email': forms.EmailInput(attrs={'class': TAILWIND_INPUT}),
            'phone': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'mobile': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'hire_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'employment_status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'job_title': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'department': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'skill_level': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'specializations': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'certifications': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'home_base_location': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'emergency_contact_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['user', 'mobile', 'hire_date', 'job_title', 'department',
                    'specializations', 'certifications', 'home_base_location',
                    'emergency_contact_name', 'emergency_contact_phone']
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


# =============================================================================
# SPRINT 4A/4B FORMS - Field Operations & Asset Management
# =============================================================================

class FieldPerformanceLogForm(forms.ModelForm):
    """Form for FieldPerformanceLog - Recording drilling performance data."""

    class Meta:
        model = FieldPerformanceLog
        fields = [
            'drill_string_run', 'log_date', 'shift', 'technician',
            'drilling_hours', 'rotating_hours', 'circulating_hours',
            'reaming_hours', 'tripping_hours', 'connection_time',
            'footage_drilled', 'avg_rop', 'max_rop', 'avg_wob', 'max_wob',
            'avg_rpm', 'max_rpm', 'avg_torque', 'max_torque',
            'avg_flow_rate', 'avg_pressure', 'bit_grade', 'formation',
            'performance_rating', 'observations', 'recommendations', 'notes'
        ]
        widgets = {
            'drill_string_run': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'log_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'shift': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'drilling_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'rotating_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'circulating_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'reaming_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'tripping_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'connection_time': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'footage_drilled': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'avg_rop': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'max_rop': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'avg_wob': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'max_wob': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'avg_rpm': forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'max_rpm': forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'avg_torque': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'max_torque': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'avg_flow_rate': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'avg_pressure': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'bit_grade': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'formation': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'performance_rating': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'observations': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'recommendations': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['shift', 'technician', 'rotating_hours', 'circulating_hours',
                    'reaming_hours', 'tripping_hours', 'connection_time', 'max_rop',
                    'avg_wob', 'max_wob', 'avg_rpm', 'max_rpm', 'avg_torque', 'max_torque',
                    'avg_flow_rate', 'avg_pressure', 'bit_grade', 'formation',
                    'performance_rating', 'observations', 'recommendations', 'notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldInspectionForm(forms.ModelForm):
    """Form for FieldInspection - Recording equipment inspections."""

    class Meta:
        model = FieldInspection
        fields = [
            'inspection_number', 'drill_string_run', 'inspection_type',
            'inspection_date', 'inspector', 'status', 'equipment_type',
            'serial_number', 'condition_rating', 'wear_percentage',
            'thread_condition', 'body_condition', 'gauge_condition',
            'passed', 'failed_reason', 'corrective_action', 'next_inspection_due',
            'findings', 'recommendations', 'photos_attached', 'notes'
        ]
        widgets = {
            'inspection_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'drill_string_run': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'inspection_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'inspection_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'inspector': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'equipment_type': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'serial_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'condition_rating': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'wear_percentage': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'thread_condition': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'body_condition': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'gauge_condition': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'passed': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'failed_reason': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'corrective_action': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'next_inspection_due': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'findings': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'recommendations': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'photos_attached': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['drill_string_run', 'inspector', 'equipment_type', 'serial_number',
                    'wear_percentage', 'thread_condition', 'body_condition', 'gauge_condition',
                    'failed_reason', 'corrective_action', 'next_inspection_due',
                    'findings', 'recommendations', 'notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class RunHoursForm(forms.ModelForm):
    """Form for RunHours - Tracking equipment run hours."""

    class Meta:
        model = RunHours
        fields = [
            'drill_string_run', 'record_date', 'start_time', 'end_time',
            'total_hours', 'drilling_hours', 'rotating_hours', 'standby_hours',
            'maintenance_hours', 'technician', 'verified', 'verified_by',
            'notes'
        ]
        widgets = {
            'drill_string_run': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'record_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'total_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'drilling_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'rotating_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'standby_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'maintenance_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'verified': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'verified_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['start_time', 'end_time', 'drilling_hours', 'rotating_hours',
                    'standby_hours', 'maintenance_hours', 'technician',
                    'verified_by', 'notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldIncidentForm(forms.ModelForm):
    """Form for FieldIncident - Recording and tracking incidents."""

    class Meta:
        model = FieldIncident
        fields = [
            'incident_number', 'service_site', 'incident_type', 'severity',
            'status', 'priority', 'incident_date', 'reported_date',
            'reported_by', 'technician', 'location_description', 'description',
            'immediate_actions', 'root_cause', 'contributing_factors',
            'preventive_measures', 'corrective_actions', 'lessons_learned',
            'injuries', 'injury_details', 'property_damage', 'damage_description',
            'estimated_cost', 'actual_cost', 'downtime_hours',
            'customer_notified', 'authorities_notified', 'follow_up_required',
            'follow_up_actions', 'closed_date', 'notes'
        ]
        widgets = {
            'incident_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'incident_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'severity': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'priority': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'incident_date': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'reported_date': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'reported_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'location_description': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 5}),
            'immediate_actions': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'root_cause': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'contributing_factors': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'preventive_measures': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'corrective_actions': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'lessons_learned': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'injuries': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'injury_details': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'property_damage': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'damage_description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'estimated_cost': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'actual_cost': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'downtime_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.5'}),
            'customer_notified': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'authorities_notified': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'follow_up_required': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'follow_up_actions': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'closed_date': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['service_site', 'reported_by', 'technician', 'location_description',
                    'immediate_actions', 'root_cause', 'contributing_factors',
                    'preventive_measures', 'corrective_actions', 'lessons_learned',
                    'injury_details', 'damage_description', 'estimated_cost',
                    'actual_cost', 'downtime_hours', 'follow_up_actions',
                    'closed_date', 'notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldDataEntryForm(forms.ModelForm):
    """Form for FieldDataEntry - Recording field data entries."""

    class Meta:
        model = FieldDataEntry
        fields = [
            'entry_number', 'drill_string_run', 'entry_type', 'entry_date',
            'recorded_by', 'depth', 'value_1', 'value_2', 'value_3',
            'measurement_unit', 'quality_status', 'verified', 'verified_by',
            'notes'
        ]
        widgets = {
            'entry_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'drill_string_run': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'entry_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'entry_date': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'recorded_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'depth': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'value_1': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'value_2': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'value_3': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'measurement_unit': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'quality_status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'verified': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'verified_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['recorded_by', 'depth', 'value_2', 'value_3',
                    'measurement_unit', 'quality_status', 'verified_by', 'notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldPhotoForm(forms.ModelForm):
    """Form for FieldPhoto - Uploading and managing field photos."""

    class Meta:
        model = FieldPhoto
        fields = [
            'title', 'photo', 'photo_type', 'drill_string_run', 'service_site',
            'taken_date', 'taken_by', 'latitude', 'longitude', 'caption',
            'description', 'is_public', 'notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'photo': forms.FileInput(attrs={'class': TAILWIND_INPUT, 'accept': 'image/*'}),
            'photo_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'drill_string_run': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'taken_date': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'taken_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'latitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.000001'}),
            'caption': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'is_public': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['drill_string_run', 'service_site', 'taken_date', 'taken_by',
                    'latitude', 'longitude', 'caption', 'description', 'notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldDocumentForm(forms.ModelForm):
    """Form for FieldDocument - Uploading and managing field documents."""

    class Meta:
        model = FieldDocument
        fields = [
            'title', 'document', 'document_type', 'drill_string_run', 'service_site',
            'document_date', 'uploaded_by', 'version', 'status', 'expiry_date',
            'description', 'is_confidential', 'notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'document': forms.FileInput(attrs={'class': TAILWIND_INPUT}),
            'document_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'drill_string_run': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'document_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'uploaded_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'version': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'expiry_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'is_confidential': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['drill_string_run', 'service_site', 'uploaded_by', 'version',
                    'expiry_date', 'description', 'notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class GPSLocationForm(forms.ModelForm):
    """Form for GPSLocation - Recording GPS coordinates."""

    class Meta:
        model = GPSLocation
        fields = [
            'technician', 'service_site', 'latitude', 'longitude', 'altitude',
            'accuracy', 'recorded_at', 'source', 'address', 'notes'
        ]
        widgets = {
            'technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'latitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.000001'}),
            'altitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'accuracy': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'recorded_at': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'source': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'address': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['technician', 'service_site', 'altitude', 'accuracy',
                    'source', 'address', 'notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldWorkOrderForm(forms.ModelForm):
    """Form for FieldWorkOrder - Managing field work orders."""

    class Meta:
        model = FieldWorkOrder
        fields = [
            'work_order_number', 'service_request', 'service_site', 'work_order_type',
            'status', 'priority', 'assigned_technician', 'scheduled_date',
            'scheduled_start_time', 'scheduled_end_time', 'actual_start_time',
            'actual_end_time', 'description', 'work_performed', 'materials_used',
            'labor_hours', 'labor_cost', 'material_cost', 'total_cost',
            'customer_signature', 'completion_notes', 'notes'
        ]
        widgets = {
            'work_order_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'service_request': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'work_order_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'priority': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'assigned_technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'scheduled_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'scheduled_start_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'scheduled_end_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'actual_start_time': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'actual_end_time': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 4}),
            'work_performed': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 4}),
            'materials_used': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'labor_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.5'}),
            'labor_cost': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'material_cost': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'total_cost': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'customer_signature': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'completion_notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['service_request', 'service_site', 'assigned_technician',
                    'scheduled_start_time', 'scheduled_end_time', 'actual_start_time',
                    'actual_end_time', 'work_performed', 'materials_used',
                    'labor_hours', 'labor_cost', 'material_cost', 'total_cost',
                    'customer_signature', 'completion_notes', 'notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldAssetAssignmentForm(forms.ModelForm):
    """Form for FieldAssetAssignment - Assigning assets to field service."""

    class Meta:
        model = FieldAssetAssignment
        fields = [
            'assignment_number', 'drill_bit', 'service_site', 'technician',
            'assignment_type', 'status', 'assignment_date', 'expected_return_date',
            'actual_return_date', 'condition_at_assignment', 'condition_at_return',
            'assigned_by', 'returned_to', 'purpose', 'notes'
        ]
        widgets = {
            'assignment_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'drill_bit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'assignment_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'assignment_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'expected_return_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'actual_return_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'condition_at_assignment': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'condition_at_return': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'assigned_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'returned_to': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'purpose': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['drill_bit', 'service_site', 'technician', 'expected_return_date',
                    'actual_return_date', 'condition_at_return', 'assigned_by',
                    'returned_to', 'purpose', 'notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False
