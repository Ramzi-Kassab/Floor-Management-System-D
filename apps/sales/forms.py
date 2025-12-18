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
            'priority', 'status', 'title', 'description', 'customer_notes',
            'requested_date', 'requested_time_slot', 'estimated_duration_hours',
            'flexible_scheduling', 'assigned_technician'
        ]
        widgets = {
            'request_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'customer': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'request_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'priority': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'title': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 4}),
            'customer_notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'requested_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'requested_time_slot': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'estimated_duration_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'flexible_scheduling': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'assigned_technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['customer_notes', 'requested_time_slot', 'estimated_duration_hours',
                    'flexible_scheduling', 'assigned_technician']
        for field in optional:
            self.fields[field].required = False


class ServiceScheduleForm(forms.ModelForm):
    """Form for ServiceSchedule - Scheduling service visits."""

    class Meta:
        model = ServiceSchedule
        fields = [
            'schedule_number', 'service_request', 'technician', 'service_site',
            'scheduled_date', 'scheduled_start_time', 'scheduled_end_time',
            'estimated_duration_hours', 'status'
        ]
        widgets = {
            'schedule_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'service_request': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'scheduled_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'scheduled_start_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'scheduled_end_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'estimated_duration_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['estimated_duration_hours']
        for field in optional:
            self.fields[field].required = False


class SiteVisitForm(forms.ModelForm):
    """Form for SiteVisit - Recording site visits."""

    class Meta:
        model = SiteVisit
        fields = [
            'visit_number', 'service_request', 'schedule', 'technician', 'service_site',
            'visit_date', 'visit_type', 'check_in_time', 'check_out_time', 'status',
            'work_performed', 'issues_found', 'recommendations'
        ]
        widgets = {
            'visit_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'service_request': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'schedule': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'visit_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'visit_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'check_in_time': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'check_out_time': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'work_performed': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 4}),
            'issues_found': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'recommendations': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['schedule', 'check_in_time', 'check_out_time', 'work_performed',
                    'issues_found', 'recommendations']
        for field in optional:
            self.fields[field].required = False


class ServiceReportForm(forms.ModelForm):
    """Form for ServiceReport - Service report documentation."""

    class Meta:
        model = ServiceReport
        fields = [
            'report_number', 'site_visit', 'service_request', 'report_date',
            'report_title', 'status', 'executive_summary', 'work_performed_detail',
            'findings', 'issues_identified', 'corrective_actions', 'recommendations'
        ]
        widgets = {
            'report_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'site_visit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_request': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'report_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'report_title': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'executive_summary': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'work_performed_detail': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 5}),
            'findings': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 4}),
            'issues_identified': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'corrective_actions': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 4}),
            'recommendations': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['findings', 'issues_identified', 'corrective_actions',
                    'recommendations']
        for field in optional:
            self.fields[field].required = False


class FieldDrillStringRunForm(forms.ModelForm):
    """Form for FieldDrillStringRun - Recording drill string runs."""

    class Meta:
        model = FieldDrillStringRun
        fields = [
            'run_number', 'drill_bit', 'well', 'rig', 'service_site', 'service_request',
            'customer', 'field_technician', 'run_type', 'status', 'spud_time',
            'out_of_hole_time', 'depth_in', 'depth_out', 'footage_drilled',
            'total_rotating_hours', 'total_on_bottom_hours', 'operational_notes'
        ]
        widgets = {
            'run_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'drill_bit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'well': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'rig': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_request': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'customer': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'field_technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'run_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'spud_time': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'out_of_hole_time': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'depth_in': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'depth_out': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'footage_drilled': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'total_rotating_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'total_on_bottom_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'operational_notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['rig', 'service_site', 'service_request', 'field_technician',
                    'spud_time', 'out_of_hole_time', 'depth_in', 'depth_out',
                    'footage_drilled', 'total_rotating_hours', 'total_on_bottom_hours',
                    'operational_notes']
        for field in optional:
            self.fields[field].required = False


class FieldRunDataForm(forms.ModelForm):
    """Form for FieldRunData - Recording run performance data."""

    class Meta:
        model = FieldRunData
        fields = [
            'field_run', 'recorded_by', 'timestamp', 'bit_depth', 'rop', 'wob',
            'rpm', 'torque', 'flow_rate', 'standpipe_pressure', 'notes'
        ]
        widgets = {
            'field_run': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'recorded_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'timestamp': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'bit_depth': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'rop': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'wob': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'rpm': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'torque': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'flow_rate': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'standpipe_pressure': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['recorded_by', 'rop', 'wob', 'rpm', 'torque', 'flow_rate',
                    'standpipe_pressure', 'notes']
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
            'log_number', 'field_run', 'logged_by', 'interval_type',
            'start_time', 'end_time', 'start_depth', 'end_depth',
            'footage_drilled', 'rotating_hours', 'on_bottom_hours',
            'avg_rop', 'max_rop', 'avg_wob', 'avg_rpm', 'avg_torque',
            'avg_flow_rate', 'formation_name', 'connection_time_avg',
            'performance_rating', 'performance_notes', 'optimization_recommendations'
        ]
        widgets = {
            'log_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'field_run': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'logged_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'interval_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'start_time': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'start_depth': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'end_depth': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'footage_drilled': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'rotating_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'on_bottom_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'avg_rop': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'max_rop': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'avg_wob': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'avg_rpm': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'avg_torque': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'avg_flow_rate': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'formation_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'connection_time_avg': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'performance_rating': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'performance_notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'optimization_recommendations': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['logged_by', 'max_rop', 'avg_wob', 'avg_rpm', 'avg_torque',
                    'avg_flow_rate', 'formation_name', 'connection_time_avg',
                    'performance_notes', 'optimization_recommendations']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldInspectionForm(forms.ModelForm):
    """Form for FieldInspection - Recording equipment inspections."""

    class Meta:
        model = FieldInspection
        fields = [
            'inspection_number', 'drill_bit', 'field_run', 'site_visit', 'service_site',
            'inspection_type', 'inspection_date', 'inspection_time', 'inspector', 'status',
            'dull_grade', 'inner_rows', 'outer_rows', 'dull_characteristic',
            'bearing_seal', 'gauge', 'reason_pulled', 'overall_condition',
            'blade_condition', 'cutter_condition', 'body_condition', 'connection_condition',
            'recommendation', 'recommendation_notes', 'has_photos', 'findings'
        ]
        widgets = {
            'inspection_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'drill_bit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'field_run': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'site_visit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'inspection_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'inspection_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'inspection_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'inspector': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'dull_grade': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'inner_rows': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'outer_rows': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'dull_characteristic': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'bearing_seal': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'gauge': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'reason_pulled': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'overall_condition': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'blade_condition': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'cutter_condition': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'body_condition': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'connection_condition': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'recommendation': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'recommendation_notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'has_photos': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'findings': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['field_run', 'site_visit', 'service_site', 'inspection_time', 'inspector',
                    'dull_grade', 'inner_rows', 'outer_rows', 'dull_characteristic',
                    'bearing_seal', 'gauge', 'reason_pulled', 'blade_condition',
                    'cutter_condition', 'body_condition', 'connection_condition',
                    'recommendation_notes', 'findings']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class RunHoursForm(forms.ModelForm):
    """Form for RunHours - Tracking equipment run hours."""

    class Meta:
        model = RunHours
        fields = [
            'drill_bit', 'field_run', 'recorded_by', 'hour_type', 'hours',
            'record_date', 'start_time', 'end_time', 'entry_source',
            'depth_at_start', 'depth_at_end', 'notes'
        ]
        widgets = {
            'drill_bit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'field_run': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'recorded_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'hour_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'record_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'entry_source': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'depth_at_start': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'depth_at_end': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['field_run', 'recorded_by', 'start_time', 'end_time',
                    'depth_at_start', 'depth_at_end', 'notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldIncidentForm(forms.ModelForm):
    """Form for FieldIncident - Recording and tracking incidents."""

    class Meta:
        model = FieldIncident
        fields = [
            'incident_number', 'service_site', 'site_visit', 'field_run',
            'category', 'severity', 'status', 'incident_title',
            'incident_date', 'incident_time', 'reported_by', 'location_description',
            'description', 'immediate_actions', 'root_cause', 'contributing_factors',
            'corrective_actions', 'preventive_actions', 'lessons_learned',
            'injury_type', 'injury_description', 'property_damage', 'damage_description',
            'estimated_damage_cost', 'reported_to_client', 'reported_to_authority',
            'closed_date'
        ]
        widgets = {
            'incident_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'site_visit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'field_run': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'category': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'severity': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'incident_title': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'incident_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'incident_time': forms.TimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'time'}),
            'reported_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'location_description': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 5}),
            'immediate_actions': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'root_cause': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'contributing_factors': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'corrective_actions': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'preventive_actions': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'lessons_learned': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'injury_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'injury_description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'property_damage': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'damage_description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'estimated_damage_cost': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'reported_to_client': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'reported_to_authority': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'closed_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['service_site', 'site_visit', 'field_run', 'incident_time',
                    'reported_by', 'location_description', 'immediate_actions',
                    'root_cause', 'contributing_factors', 'corrective_actions',
                    'preventive_actions', 'lessons_learned', 'injury_description',
                    'damage_description', 'estimated_damage_cost', 'closed_date']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldDataEntryForm(forms.ModelForm):
    """Form for FieldDataEntry - Recording field data entries."""

    class Meta:
        model = FieldDataEntry
        fields = [
            'entry_number', 'site_visit', 'field_run', 'service_site', 'entered_by',
            'data_type', 'category', 'status', 'field_name', 'field_code',
            'description', 'value_text', 'value_numeric', 'value_boolean',
            'unit_of_measure', 'notes'
        ]
        widgets = {
            'entry_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'site_visit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'field_run': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'entered_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'data_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'category': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'field_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'field_code': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'value_text': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'value_numeric': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.0001'}),
            'value_boolean': forms.CheckboxInput(attrs={'class': TAILWIND_CHECKBOX}),
            'unit_of_measure': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['site_visit', 'field_run', 'service_site', 'entered_by',
                    'field_code', 'description', 'value_text', 'value_numeric',
                    'value_boolean', 'unit_of_measure', 'notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldPhotoForm(forms.ModelForm):
    """Form for FieldPhoto - Uploading and managing field photos."""

    class Meta:
        model = FieldPhoto
        fields = [
            'photo_number', 'site_visit', 'field_inspection', 'field_incident',
            'drill_bit', 'service_site', 'taken_by', 'category', 'status',
            'title', 'description', 'file_path', 'taken_at',
            'latitude', 'longitude', 'tags'
        ]
        widgets = {
            'photo_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'site_visit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'field_inspection': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'field_incident': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'drill_bit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'taken_by': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'category': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'title': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'file_path': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'taken_at': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'latitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.0000001'}),
            'longitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.0000001'}),
            'tags': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['site_visit', 'field_inspection', 'field_incident', 'drill_bit',
                    'service_site', 'taken_by', 'title', 'description', 'file_path',
                    'latitude', 'longitude', 'tags']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldDocumentForm(forms.ModelForm):
    """Form for FieldDocument - Uploading and managing field documents."""

    class Meta:
        model = FieldDocument
        fields = [
            'document_number', 'site_visit', 'service_request', 'service_report',
            'service_site', 'created_by_technician', 'document_type', 'status',
            'title', 'description', 'file_path', 'version', 'document_date'
        ]
        widgets = {
            'document_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'site_visit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_request': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_report': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'created_by_technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'document_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'title': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'file_path': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'version': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'document_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['site_visit', 'service_request', 'service_report', 'service_site',
                    'created_by_technician', 'description', 'file_path', 'version']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class GPSLocationForm(forms.ModelForm):
    """Form for GPSLocation - Recording GPS coordinates."""

    class Meta:
        model = GPSLocation
        fields = [
            'field_technician', 'site_visit', 'service_site', 'latitude', 'longitude',
            'altitude', 'accuracy', 'recorded_at', 'location_type', 'source_device',
            'address', 'notes'
        ]
        widgets = {
            'field_technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'site_visit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'latitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.0000001'}),
            'longitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.0000001'}),
            'altitude': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'accuracy': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'recorded_at': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'location_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'source_device': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'address': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['field_technician', 'site_visit', 'service_site', 'altitude',
                    'accuracy', 'address', 'notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldWorkOrderForm(forms.ModelForm):
    """Form for FieldWorkOrder - Managing field work orders."""

    class Meta:
        model = FieldWorkOrder
        fields = [
            'work_order_number', 'service_request', 'service_site', 'customer',
            'work_type', 'status', 'priority', 'assigned_technician', 'title',
            'description', 'scheduled_start', 'scheduled_end', 'actual_start',
            'actual_end', 'actual_hours', 'work_performed', 'completion_notes',
            'actual_labor_cost', 'actual_material_cost'
        ]
        widgets = {
            'work_order_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'service_request': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'customer': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'work_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'priority': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'assigned_technician': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'title': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'description': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 4}),
            'scheduled_start': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'scheduled_end': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'actual_start': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'actual_end': forms.DateTimeInput(attrs={'class': TAILWIND_INPUT, 'type': 'datetime-local'}),
            'actual_hours': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'work_performed': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 4}),
            'completion_notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 3}),
            'actual_labor_cost': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
            'actual_material_cost': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['service_request', 'assigned_technician', 'scheduled_start',
                    'scheduled_end', 'actual_start', 'actual_end', 'actual_hours',
                    'work_performed', 'completion_notes', 'actual_labor_cost',
                    'actual_material_cost']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False


class FieldAssetAssignmentForm(forms.ModelForm):
    """Form for FieldAssetAssignment - Assigning assets to field service."""

    class Meta:
        model = FieldAssetAssignment
        fields = [
            'assignment_number', 'drill_bit', 'work_order', 'site_visit', 'service_site',
            'assigned_to', 'asset_type', 'asset_name', 'asset_code', 'status',
            'checkout_date', 'expected_return_date', 'return_date',
            'checkout_condition', 'condition_on_return', 'checkout_notes', 'return_notes'
        ]
        widgets = {
            'assignment_number': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'drill_bit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'work_order': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'site_visit': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'service_site': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'assigned_to': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'asset_type': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'asset_name': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'asset_code': forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'status': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'checkout_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'expected_return_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'return_date': forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'checkout_condition': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'condition_on_return': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'checkout_notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
            'return_notes': forms.Textarea(attrs={'class': TAILWIND_TEXTAREA, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ['drill_bit', 'work_order', 'site_visit', 'service_site', 'assigned_to',
                    'asset_code', 'expected_return_date', 'return_date', 'checkout_condition',
                    'condition_on_return', 'checkout_notes', 'return_notes']
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False
