"""
ARDT FMS - Technology Filters
Using django-filter for standardized filtering.
"""

import django_filters
from django import forms
from django.db.models import Q
from .models import BOM, Design, BitSize


class BOMFilter(django_filters.FilterSet):
    """
    Filter for BOM list view.
    Provides filtering by design attributes, size, status, and materials availability.
    """

    # Text search across multiple fields
    search = django_filters.CharFilter(
        method='filter_search',
        label='Search',
        widget=forms.TextInput(attrs={
            'class': 'px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm w-full',
            'placeholder': 'Search BOMs...'
        })
    )

    # Design level filter
    design__order_level = django_filters.ChoiceFilter(
        choices=Design.OrderLevel.choices,
        label='Level',
        empty_label='All Levels',
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm'
        })
    )

    # Size filter
    design__size = django_filters.ModelChoiceFilter(
        queryset=BitSize.objects.filter(is_active=True),
        label='Size',
        empty_label='All Sizes',
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm'
        })
    )

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=BOM.Status.choices,
        label='Status',
        empty_label='All Status',
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm'
        })
    )

    class Meta:
        model = BOM
        fields = ['status', 'design__order_level', 'design__size']

    def filter_search(self, queryset, name, value):
        """Search across BOM code, name, and design fields."""
        if value:
            return queryset.filter(
                Q(code__icontains=value) |
                Q(name__icontains=value) |
                Q(design__mat_no__icontains=value) |
                Q(design__hdbs_type__hdbs_name__icontains=value) |
                Q(design__smi_types__smi_name__icontains=value)
            ).distinct()
        return queryset


class DesignFilter(django_filters.FilterSet):
    """
    Filter for Design selection in BOM builder.
    """

    search = django_filters.CharFilter(
        method='filter_search',
        label='Search',
        widget=forms.TextInput(attrs={
            'class': 'px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm w-full',
            'placeholder': 'Search designs...'
        })
    )

    order_level = django_filters.ChoiceFilter(
        choices=Design.OrderLevel.choices,
        label='Level',
        empty_label='All Levels',
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm'
        })
    )

    size = django_filters.ModelChoiceFilter(
        queryset=BitSize.objects.filter(is_active=True),
        label='Size',
        empty_label='All Sizes',
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm'
        })
    )

    status = django_filters.ChoiceFilter(
        choices=Design.Status.choices,
        label='Status',
        empty_label='All Status',
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm'
        })
    )

    class Meta:
        model = Design
        fields = ['order_level', 'size', 'status']

    def filter_search(self, queryset, name, value):
        """Search across design fields."""
        if value:
            return queryset.filter(
                Q(mat_no__icontains=value) |
                Q(hdbs_type__hdbs_name__icontains=value) |
                Q(smi_types__smi_name__icontains=value)
            ).distinct()
        return queryset
