from django import template
from django.template.defaultfilters import stringfilter
from django.utils import dateparse
import urllib.parse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import pytz

register = template.Library()


@register.filter
@stringfilter
def truncateString(value):
    # If the string is longer than 2000 characters, truncate it and add "..."
    if len(value) > 2000:
        return value[:2000] + "..."
    return value


@register.filter
@stringfilter
def stringToDate(value):
    # Parse the datetime string to a datetime object
    dt = parse_datetime(value)
    if dt is not None:
        edmonton_tz = pytz.timezone('America/Edmonton')
        # Check if the datetime object is naive (has no timezone information)
        if timezone.is_naive(dt):
            # Make the datetime object timezone-aware by assuming it is in UTC
            dt = timezone.make_aware(dt, timezone=timezone.utc)
        # Convert to 'America/Edmonton' timezone
        dt = dt.astimezone(edmonton_tz)
        return dt.strftime("%I:%M %p, %B %d, %Y")
    return ''


@register.filter
@stringfilter
def getId(value):
    """
    Get the id from an "id" field as described in the project specs. 
    Example id: "http://127.0.0.1:5454/authors/1d698d25ff008f7538453c120f581471"
    """
    return value.split('/')[-1]


@register.filter
@stringfilter
def urlEncode(value):
    return urllib.parse.quote_plus(value)


@register.filter
@stringfilter
def getImageURLFromPost(post):
    """Get the link of the image from the post."""
    if post.image:
        return post.id + '/image'

    return ''


@register.filter(name='split_uuid')
def split_uuid(value):
    """Splits a URL and returns the UUID part."""
    try:
        return value.strip('/').split('/')[-1]
    except AttributeError:
        # In case the value is not a string, return it as is
        return value
