from django import template
from django.conf import settings

register = template.Library()

@register.inclusion_tag('gallery/pagination_widget.html', takes_context=True)
def pagination_widget(context):
    paginator = context['paginator']
    batch_size = settings.PAGINATION_BATCH_SIZE
    total_count = context['total_count']
    if paginator['next_page'] == paginator['num_pages']:
        modulo = total_count % batch_size
        next_batch_size = modulo and modulo or batch_size
    else:
        next_batch_size = batch_size
    return {
        'request': context['request'],
        'query_string': context['query_string'],
        'paginator': paginator,
        'page_results': context['page_results'],
        'total_count': total_count,
        'prev_batch_size': batch_size,
        'next_batch_size': next_batch_size,
        'MEDIA_URL': settings.MEDIA_URL,
    }
