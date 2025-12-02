"""
ARDT FMS - DRSS Forms
Version: 5.4 - Sprint 2

Forms for DRSS request management.
"""

from django import forms
from django.forms import inlineformset_factory

from .models import DRSSRequest, DRSSRequestLine
from apps.sales.models import Customer, Rig, Well


# Tailwind CSS classes
TAILWIND_INPUT = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white'
TAILWIND_SELECT = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white'
TAILWIND_TEXTAREA = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white'


class DRSSRequestForm(forms.ModelForm):
    """
    DRSS Request creation and edit form.
    """

    class Meta:
        model = DRSSRequest
        fields = [
            'drss_number', 'external_reference',
            'customer', 'rig', 'well',
            'requested_date', 'required_date', 'priority',
            'status',
            'customer_notes', 'internal_notes'
        ]
        widgets = {
            'drss_number': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'DRSS Number from ARAMCO'
            }),
            'external_reference': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Additional reference (optional)'
            }),
            'customer': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'rig': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'well': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'requested_date': forms.DateInput(attrs={
                'class': TAILWIND_INPUT,
                'type': 'date'
            }),
            'required_date': forms.DateInput(attrs={
                'class': TAILWIND_INPUT,
                'type': 'date'
            }),
            'priority': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'status': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'customer_notes': forms.Textarea(attrs={
                'class': TAILWIND_TEXTAREA,
                'rows': 3,
                'placeholder': 'Notes from customer/ARAMCO'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': TAILWIND_TEXTAREA,
                'rows': 3,
                'placeholder': 'Internal notes (not visible to customer)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to ARAMCO customers only
        self.fields['customer'].queryset = Customer.objects.filter(
            is_active=True, is_aramco=True
        ).order_by('name')
        self.fields['rig'].queryset = Rig.objects.filter(is_active=True).order_by('code')
        self.fields['well'].queryset = Well.objects.filter(is_active=True).order_by('code')
        self.fields['rig'].required = False
        self.fields['well'].required = False

    def clean(self):
        cleaned_data = super().clean()
        requested_date = cleaned_data.get('requested_date')
        required_date = cleaned_data.get('required_date')

        if requested_date and required_date:
            if required_date < requested_date:
                raise forms.ValidationError(
                    'Required date cannot be before requested date.'
                )

        return cleaned_data


class DRSSRequestLineForm(forms.ModelForm):
    """
    DRSS Request Line form for individual bit requests.
    """

    class Meta:
        model = DRSSRequestLine
        fields = [
            'line_number', 'bit_type', 'bit_size', 'design_code', 'quantity',
            'iadc_code', 'formation', 'depth_from', 'depth_to',
            'status', 'fulfillment_option', 'fulfillment_notes'
        ]
        widgets = {
            'line_number': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT,
                'min': 1
            }),
            'bit_type': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'FC / RC'
            }),
            'bit_size': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT,
                'step': '0.001',
                'placeholder': 'Size (inches)'
            }),
            'design_code': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Design code'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT,
                'min': 1
            }),
            'iadc_code': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'IADC code'
            }),
            'formation': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Formation type'
            }),
            'depth_from': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'From (ft)'
            }),
            'depth_to': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'To (ft)'
            }),
            'status': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'fulfillment_option': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'fulfillment_notes': forms.Textarea(attrs={
                'class': TAILWIND_TEXTAREA,
                'rows': 2,
                'placeholder': 'Fulfillment notes'
            }),
        }


# Inline formset for managing lines within a request
DRSSRequestLineFormSet = inlineformset_factory(
    DRSSRequest,
    DRSSRequestLine,
    form=DRSSRequestLineForm,
    extra=1,
    can_delete=True
)


class DRSSEvaluationForm(forms.ModelForm):
    """
    Form for evaluating/updating a DRSS request line.
    """

    class Meta:
        model = DRSSRequestLine
        fields = [
            'status', 'fulfillment_option', 'fulfillment_notes',
            'source_bit', 'work_order'
        ]
        widgets = {
            'status': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'fulfillment_option': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'fulfillment_notes': forms.Textarea(attrs={
                'class': TAILWIND_TEXTAREA,
                'rows': 3
            }),
            'source_bit': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
            'work_order': forms.Select(attrs={
                'class': TAILWIND_SELECT
            }),
        }
