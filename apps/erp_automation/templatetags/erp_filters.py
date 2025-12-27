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
