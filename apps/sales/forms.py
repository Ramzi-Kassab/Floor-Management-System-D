"""
ARDT FMS - Sales Forms
Version: 5.4 - Sprint 2

Forms for customer, rig, well, and contact management.
"""

from django import forms
from django.core.exceptions import ValidationError

from .models import Customer, CustomerContact, Rig, Well, Warehouse


# Tailwind CSS classes for form widgets
TAILWIND_INPUT = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white'
TAILWIND_SELECT = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white'
TAILWIND_TEXTAREA = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white'
TAILWIND_CHECKBOX = 'h-4 w-4 text-ardt-blue focus:ring-ardt-blue border-gray-300 rounded'


class CustomerForm(forms.ModelForm):
    """
    Customer creation and edit form.
    """

    class Meta:
        model = Customer
        fields = [
            # Identity
            'code', 'name', 'name_ar', 'customer_type',
            # Contact
            'address', 'city', 'country', 'phone', 'email', 'website',
            # Business
            'tax_id', 'credit_limit', 'payment_terms',
            # Status
            'is_active', 'is_aramco',
            # Management
            'account_manager'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'e.g., CUST-001'
            }),
            'name': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Company Name'
            }),
            'name_ar': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'اسم الشركة',
                'dir': 'rtl'
            }),
            'customer_type': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'address': forms.Textarea(attrs={
                'class': TAILWIND_TEXTAREA,
                'rows': 3,
                'placeholder': 'Full address'
            }),
            'city': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'City'
            }),
            'country': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Country'
            }),
            'phone': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': '+966 XX XXX XXXX'
            }),
            'email': forms.EmailInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'contact@company.com'
            }),
            'website': forms.URLInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'https://www.company.com'
            }),
            'tax_id': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Tax ID / VAT Number'
            }),
            'credit_limit': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT,
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'payment_terms': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'e.g., Net 30'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': TAILWIND_CHECKBOX
            }),
            'is_aramco': forms.CheckboxInput(attrs={
                'class': TAILWIND_CHECKBOX
            }),
            'account_manager': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
        }

    def clean_code(self):
        """Ensure customer code is uppercase."""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
            # Check uniqueness for new customers
            if not self.instance.pk:
                if Customer.objects.filter(code=code).exists():
                    raise ValidationError('A customer with this code already exists.')
        return code

    def clean_email(self):
        """Validate email format."""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email


class CustomerContactForm(forms.ModelForm):
    """
    Customer contact person form.
    """

    class Meta:
        model = CustomerContact
        fields = [
            'name', 'title', 'department',
            'email', 'phone', 'mobile',
            'is_primary', 'is_active', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Contact Name'
            }),
            'title': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Job Title'
            }),
            'department': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Department'
            }),
            'email': forms.EmailInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'contact@company.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Office Phone'
            }),
            'mobile': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Mobile Phone'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': TAILWIND_CHECKBOX
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': TAILWIND_CHECKBOX
            }),
            'notes': forms.Textarea(attrs={
                'class': TAILWIND_TEXTAREA,
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }


class RigForm(forms.ModelForm):
    """
    Rig registration and edit form.
    """

    class Meta:
        model = Rig
        fields = [
            'code', 'name', 'customer', 'contractor',
            'rig_type', 'location', 'latitude', 'longitude',
            'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'e.g., RIG-001'
            }),
            'name': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Rig Name'
            }),
            'customer': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'contractor': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'rig_type': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'e.g., Land Rig, Jack-Up'
            }),
            'location': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Current Location'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT,
                'step': '0.0000001',
                'placeholder': 'Latitude'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT,
                'step': '0.0000001',
                'placeholder': 'Longitude'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': TAILWIND_CHECKBOX
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter customer/contractor dropdowns to active customers only
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)
        self.fields['contractor'].queryset = Customer.objects.filter(
            is_active=True,
            customer_type=Customer.CustomerType.CONTRACTOR
        )

    def clean_code(self):
        """Ensure rig code is uppercase."""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
            if not self.instance.pk:
                if Rig.objects.filter(code=code).exists():
                    raise ValidationError('A rig with this code already exists.')
        return code


class WellForm(forms.ModelForm):
    """
    Well registration and edit form.
    """

    class Meta:
        model = Well
        fields = [
            'code', 'name', 'customer', 'rig',
            'field_name', 'spud_date', 'target_depth',
            'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'e.g., WELL-001'
            }),
            'name': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Well Name'
            }),
            'customer': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'rig': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'field_name': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Oil Field Name'
            }),
            'spud_date': forms.DateInput(attrs={
                'class': TAILWIND_INPUT,
                'type': 'date'
            }),
            'target_depth': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Target Depth (ft)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': TAILWIND_CHECKBOX
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)
        self.fields['rig'].queryset = Rig.objects.filter(is_active=True)

    def clean_code(self):
        """Ensure well code is uppercase."""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
            if not self.instance.pk:
                if Well.objects.filter(code=code).exists():
                    raise ValidationError('A well with this code already exists.')
        return code


class WarehouseForm(forms.ModelForm):
    """
    Warehouse registration and edit form.
    """

    class Meta:
        model = Warehouse
        fields = [
            'code', 'name', 'warehouse_type', 'customer',
            'address', 'city', 'contact_person', 'contact_phone',
            'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'e.g., WH-001'
            }),
            'name': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Warehouse Name'
            }),
            'warehouse_type': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'customer': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'address': forms.Textarea(attrs={
                'class': TAILWIND_TEXTAREA,
                'rows': 2,
                'placeholder': 'Warehouse Address'
            }),
            'city': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'City'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Contact Person Name'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Contact Phone'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': TAILWIND_CHECKBOX
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)
        self.fields['customer'].required = False
