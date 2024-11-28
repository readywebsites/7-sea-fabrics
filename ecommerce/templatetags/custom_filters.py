
from django import template

register = template.Library()

@register.filter
def comma_to_br(value):
    """
    Replace commas with commas followed by <br /> tags.
    """
    return value.replace(',', ',<br />')


@register.filter
def multiply(value, arg):
    try:
        return value * arg
    except (ValueError, TypeError):
        return ''
    

@register.filter
def currency_symbol(currency_code):
    if currency_code == 'CAD':
        return 'CA$'
    elif currency_code == 'EUR':
        return '€'
    else:
        return '$'


@register.filter(name='add_class')
def add_class(value, arg):
    css_classes = value.field.widget.attrs.get('class', '')
    if css_classes:
        css_classes += ' ' + arg
    else:
        css_classes = arg
    return value.as_widget(attrs={'class': css_classes})