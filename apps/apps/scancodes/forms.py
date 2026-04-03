"""
ARDT FMS - Scan Codes Forms
Version: 5.4

Form definitions for scan code management.
"""

from django import forms
from .models import ScanCode, ScanLog


class ScanCodeForm(forms.ModelForm):
    """Form for creating/editing scan codes."""

    class Meta:
        model = ScanCode
        fields = ['code', 'code_type', 'entity_type', 'entity_id', 'is_external',
                  'external_source', 'encoded_data', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter unique code'
            }),
            'code_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            }),
            'entity_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500'
            }),
            'entity_id': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Entity ID (optional)'
            }),
            'external_source': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g., ARAMCO, Supplier name'
            }),
            'encoded_data': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-sm focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': '{"key": "value"}'
            }),
        }


class ScanLogFilterForm(forms.Form):
    """Form for filtering scan logs."""

    purpose = forms.ChoiceField(
        choices=[('', 'All Purposes')] + list(ScanLog.Purpose.choices),
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
        })
    )
    is_valid = forms.ChoiceField(
        choices=[('', 'All Results'), ('true', 'Valid'), ('false', 'Invalid')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
        })
    )


class QuickScanForm(forms.Form):
    """Form for quick code scanning/lookup."""

    code = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Scan or enter code...',
            'autofocus': True
        })
    )
    purpose = forms.ChoiceField(
        choices=ScanLog.Purpose.choices,
        initial='IDENTIFY',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
        })
    )
