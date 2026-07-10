from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Allow dict[key] access in templates: {{ my_dict|get_item:key }}"""
    return dictionary.get(key, [])


@register.filter
def subtract(value, arg):
    """Subtract arg from value: {{ value|subtract:arg }}"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value


@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter: {{ "a,b,c"|split:"," }}"""
    return value.split(delimiter)


@register.filter
def percentage(value, total):
    """Calculate percentage: {{ value|percentage:total }}"""
    try:
        if int(total) == 0:
            return 0
        return round(int(value) / int(total) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
