from bm.gallery import models
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.paginator import InvalidPage


class BetterPaginator(Paginator):
    """
    Stolen from http://www.davidcramer.net/code/466/pagination-in-django.html

    An enhanced version of the QuerySetPaginator.

    >>> my_objects = BetterPaginator(queryset, 25)
    >>> page = 1
    >>> context = {
    >>>     'my_objects': my_objects.get_context(page),
    >>> }
    """
    def get_context(self, page, range_gap=3):
        try:
            page = int(page)
        except (ValueError, TypeError), exc:
            raise InvalidPage, exc
        paginator = self.page(page)
        if page > range_gap:
            start = page-range_gap
        else:
            start = 1
        if page < self.num_pages-range_gap:
            end = page+range_gap+1
        else:
            end = self.num_pages+1
        context = {
            'firstlink': start != 1,
            'firstellipses': start > 2,
            'lastellipses': end < self.num_pages,
            'lastlink': end != self.num_pages + 1,
            'page_range': range(start, end),
            'objects': paginator.object_list,
            'num_pages': self.num_pages,
            'page': page,
            'has_pages': self.num_pages > 1,
            'has_previous': paginator.has_previous(),
            'has_next': paginator.has_next(),
            'previous_page': paginator.previous_page_number(),
            'next_page': paginator.next_page_number(),
            'is_first': page == 1,
            'is_last': page == self.num_pages,
        }
        return context


def encode_modlist_strings(modlist_map):
    """Encodes any modlist_map unicode values into utf-8 strings."""
    for key, value in modlist_map.items():
        if type(value) is unicode:
            modlist_map[key] = value.encode('utf-8')

def media_klass_from_request(request):
    mediatype = request.GET.get('mediatype')
    default = models.MediaBase
    if mediatype:
        klass = models.mediatype_map.get(mediatype,
                                         {'klass': default})['klass']
    else:
        klass = default
    return klass

def filter_args_from_request(request):
    """Massages the query values in the request's values as a tuple
    and a dictionary suitable to be used as the positional and keyword
    arguments for a query set's 'filter' method.

    NOTE: The only search keys we look for are 'keywords', 'year',
    'category', and 'owner'.  'status' is another field that will
    commonly be used, but the ability to see media that is not in an
    'approved' status is only for people with heightened privileges.
    This utility method knows nothing about context or security
    policy, so we just let the 'status' portion of the query be the
    responsibility of the calling code."""
    filter_args = tuple()
    filter_kwargs = dict()
    year = request.GET.get('year')
    if year:
        filter_kwargs['year'] = int(year)
    category = request.GET.get('category')
    if category:
        cat_object = models.Category.objects.filter(slug=category)
        if len(cat_object):
            cat_object = cat_object[0]
        filter_kwargs['categories'] = cat_object.id
    owner = request.GET.get('owner')
    if owner:
        filter_kwargs['owner__username'] = owner
    return filter_args, filter_kwargs

def year_choices():
    year_choices = cache.get('year_choices')
    if year_choices is None:
        year_choices = models.MediaBase.objects.values_list('year').distinct()
        year_choices = year_choices.order_by('year').reverse()
        year_choices = [str(y[0]) for y in year_choices if y[0]]
        cache.set('year_choices', year_choices, 86400) # 1 day
    return year_choices

def category_choices():
    category_choices = cache.get('category_choices')
    if category_choices is None:
        category_choices = models.Category.objects.all()
        category_choices = [(cat.slug, cat.title)
                            for cat in category_choices]
        cache.set('category_choices', category_choices, 86400) # 1 day
    return category_choices

def apply_searchable_text_filter(queryset, search_string):
    """Expects a query set representing a set of MediaBase objects,
    returning a query set representing the original results filtered
    by a full text search of the provided search string."""
    return queryset.extra(
        tables=['gallery_searchable_text'],
        where=['gallery_searchable_text.tsv @@ plainto_tsquery(%s) and '
               'gallery_mediabase.id = '
               'gallery_searchable_text.mediabase_ptr_id'],
        params=[search_string])
