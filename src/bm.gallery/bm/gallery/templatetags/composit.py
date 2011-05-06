from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter

register = template.Library()

def split_email_address(email):
    """Returns name, domain, and tld parts of an address; might raise
    ValueError if it has an invalid email address."""
    name, host = email.split('@')
    host = host.split('.')
    if len(host) == 1:
        domain = host
        tld = ''
    else:
        domain = '.'.join(host[:-1])
        tld = host[-1]
    return name, domain, tld

@register.filter
@stringfilter
def composit_url(email):
    if not email:
        return ''
    try:
        name, domain, tld = split_email_address(email)
    except ValueError:
        return ''
    url = ('http://www.burningman.com/scripts/composit/mailform.php'
           '?d=%s&n=%s' % (domain, name))
    if tld:
        url = '%s&tld=%s' % (url, tld)
    return url

@register.filter
@stringfilter
def composit_onclick(email):
    if not email:
        return ''
    try:
        name, domain, tld = split_email_address(email)
    except ValueError:
        return ''
    js = "composIt('%s', '%s', '%s');return false;" % (name, domain, tld)
    return js

@register.filter
def truncatesmart(value, limit=80):
    """
    Truncates a string after a given number of chars keeping whole words.

    Usage:
        {{ string|truncatesmart }}
        {{ string|truncatesmart:50 }}
    """

    try:
        limit = int(limit)
    # invalid literal for int()
    except ValueError:
        # Fail silently.
        return value

    # Make sure it's unicode
    value = unicode(value)

    # Return the string itself if length is smaller or equal to the limit
    if len(value) <= limit:
        return value

    # Cut the string
    value = value[:limit]

    # Break into words and remove the last
    words = value.split(' ')[:-1]

    # Join the words and return
    return mark_safe(' '.join(words) + '&hellip;')
