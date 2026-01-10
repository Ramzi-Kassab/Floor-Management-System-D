"""
Custom template filters for inventory app.
"""
from django import template
from decimal import Decimal

register = template.Library()


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
            # For decimal, remove trailing zeros
            if isinstance(value, Decimal):
                # Normalize to remove trailing zeros
                normalized = value.normalize()
                return str(normalized)
            return value
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
        # For decimal, remove trailing zeros
        if isinstance(val, Decimal):
            return str(val.normalize())
        return str(val)

    min_str = fmt(attr.min_value)
    max_str = fmt(attr.max_value)

    return f"[{min_str}-{max_str}]"
