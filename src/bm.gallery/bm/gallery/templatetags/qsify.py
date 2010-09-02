from django import template
from urllib import urlencode
try:
    from urlparse import parse_qs
except ImportError:
    # python 2.5
    from cgi import parse_qs

register = template.Library()

@register.tag('qsify')
def qsify(parser, token):
    """Takes a URL, figures out which GET query parameters should be
    preserved to maintain the current result set, and returns the URL
    with the GET query string attached.

    The template tag usage is like so:

    {% qsify URL [STRIP-FILTERS] [PAGE] %}

    URL: a variable or harcoded value representing the URL that is being
    qs-ified

    STRIP-FILTERS: if 'true', any of the "extra" filters (owner, tag, or
    press_gallery) will be stripped from the returned query parameters

    PAGE: a variable or hard-coded integer value representing the value
    to be specified for the 'page' parameter
    """
    try:
        call_args = token.split_contents()
    except ValueError:
        msg = ("%r tag requires at least one argument"
               % token.contents.split()[0])
        raise template.TemplateSyntaxError, msg
    tag_name = call_args[0]
    node_params = (call_args[1],)
    if len(call_args) > 2:
        remove_extra_filters = call_args[2].lower() == 'true'
        node_params += (remove_extra_filters,)
    if len(call_args) == 4:
        node_params += (call_args[3],)
    if len(call_args) > 4:
        msg = ("%r tag accepts no more than three arguments"
               % tag_name)
        raise template.TemplateSyntaxError, msg
    return QSNode(*node_params)


class QSNode(template.Node):
    """Generate the QS-ified string"""
    def __init__(self, url, remove_extra_filters=False, page=None):
        self.url_raw = url
        self.url = template.Variable(url)
        self.remove_extra_filters = remove_extra_filters
        self.page_raw = page
        if page is None:
            self.page = None
        else:
            self.page = template.Variable(page)
        self.request = template.Variable('request')

    def render(self, context):
        # don't wrap the request resolution in a try:except, b/c
        # not having access to the 'request' IS an error
        request = self.request.resolve(context)
        query_string = request.META.get('QUERY_STRING', '')
        query_map = parse_qs(query_string)
        try:
            url = self.url.resolve(context)
        except template.VariableDoesNotExist:
            # no url var, assume we were given a hardcoded URL
            url = self.url_raw
        if self.page is None:
            query_map.pop('page', None)
        else:
            try:
                page = self.page.resolve(context)
            except template.VariableDoesNotExist:
                # no page number, assume hardcoded integer value
                page = int(self.page_raw)
            query_map['page'] = page
        if self.remove_extra_filters:
            for extra_filter in ('owner', 'tag', 'press_gallery'):
                if extra_filter in query_map:
                    del(query_map[extra_filter])
        new_query_string = urlencode(query_map, doseq=True)
        if new_query_string:
            delimiter = '&' if '?' in url else '?'
            return '%s%s%s' % (url, delimiter, new_query_string)
        return url
