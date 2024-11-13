from django import template
import commonmark

register = template.Library()

@register.filter(name='markdown')
def markdown_format(text):
    return commonmark.commonmark(text)
