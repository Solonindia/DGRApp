from django import template
from report.models import ChecklistHistory

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def dict_get(d, key):
    return d.get(key, '')

@register.filter
def to(value, arg):
    try:
        return range(value, int(arg) + 1)
    except:
        return []

@register.filter
def get_image(obj, suffix):
    field_name = f"image{suffix}"
    return getattr(obj, field_name).url if getattr(obj, field_name) else None

@register.filter
def attr(obj, attr_name):
    return getattr(obj, attr_name, None)

@register.filter
def dict_count(histories, report_type):
    return histories.filter(checklist__report_type=report_type).count()