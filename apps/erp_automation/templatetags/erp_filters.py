from decimal import Decimal, InvalidOperation
from fractions import Fraction

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key."""
    if dictionary is None:
        return None
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return getattr(dictionary, key, '')


def format_size_fraction(value):
    """Convert a decimal size to clean fraction format.

    Examples:
        12.000 → "12"
        6.125  → "6 1/8"
        8.500  → "8 1/2"
        3.750  → "3 3/4"
        0.875  → "7/8"
        6.0625 → "6 1/16"
        None   → ""
        ""     → ""
    """
    if value is None or value == '':
        return ''

    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return str(value)

    # Split into whole and fractional parts
    whole = int(dec)
    frac_part = dec - whole

    # If no fractional part, return whole number only
    if frac_part == 0:
        return str(whole) if whole != 0 else '0'

    # Convert fractional part to a Fraction and limit denominator
    # Common drill bit fractions go up to 1/32
    frac = Fraction(frac_part).limit_denominator(32)

    if frac.numerator == 0:
        return str(whole) if whole != 0 else '0'

    if whole == 0:
        return f"{frac.numerator}/{frac.denominator}"
    else:
        return f"{whole} {frac.numerator}/{frac.denominator}"


@register.filter(name='size_fraction')
def size_fraction_filter(value):
    """Django template filter: {{ size_inches|size_fraction }}"""
    return format_size_fraction(value)
