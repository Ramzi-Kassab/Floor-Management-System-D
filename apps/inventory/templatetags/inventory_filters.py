"""
Custom template filters for inventory app.
"""
from django import template
from decimal import Decimal

register = template.Library()


def _format_decimal(value):
    """Format a Decimal without scientific notation and remove trailing zeros."""
    if value is None:
        return ''
    if isinstance(value, Decimal):
        # Convert to string with fixed notation (no scientific)
        # Then strip trailing zeros and unnecessary decimal point
        str_val = format(value, 'f')
        if '.' in str_val:
            str_val = str_val.rstrip('0').rstrip('.')
        return str_val
    return str(value)


@register.filter
def format_number(value, number_type='DECIMAL'):
    """
    Format a number based on number_type.
    If INTEGER, display without decimals.
    If DECIMAL, display with appropriate precision.

    Usage: {{ attr.min_value|format_number:attr.number_type }}
    """
    if value is None:
        return ''

    try:
        if number_type == 'INTEGER':
            # Convert to int for display
            return int(float(value))
        else:
            # For decimal, remove trailing zeros without scientific notation
            return _format_decimal(value)
    except (ValueError, TypeError):
        return value


@register.filter
def format_range(attr):
    """
    Format min/max range for a CategoryAttribute.
    Returns formatted string like "[8-19]" or "[8.5-19.5]"

    Usage: {{ attr|format_range }}
    """
    if attr.min_value is None and attr.max_value is None:
        return ''

    number_type = getattr(attr, 'number_type', 'DECIMAL')

    def fmt(val):
        if val is None:
            return ''
        if number_type == 'INTEGER':
            return str(int(float(val)))
        # For decimal, remove trailing zeros without scientific notation
        return _format_decimal(val)

    min_str = fmt(attr.min_value)
    max_str = fmt(attr.max_value)

    return f"[{min_str}-{max_str}]"
