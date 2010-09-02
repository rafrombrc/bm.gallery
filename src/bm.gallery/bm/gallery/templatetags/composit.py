from django import template
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
