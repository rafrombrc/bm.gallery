from bm.gallery import models
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from tagging import models as tagmodels

class TagFeed(Feed):
    def get_object(self, request, tag):
        return get_object_or_404(tagmodels.Tag, name=tag)
        
    def title(self, tag):
        return "Burning Man Media Gallery Keyword Feed: %s" % tag.name

    def link(self, tag):
        return '%s?tag=%s' % (reverse('bm.gallery.views.browse'),
                              tag.name)

    def description(self, tag):
        return "Media recently tagged with keyword %s" % tag.name

    def items(self, tag):
        approved = models.MediaBase.objects.filter(status='approved')
        tagged = tagmodels.TaggedItem.objects.get_by_model(approved,
                                                           tag)
        tagged = tagged.order_by('-id')[:30]
        return tagged
    
    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.notes


class CategoryFeed(Feed):
    def get_object(self, request, category):
        return get_object_or_404(models.Category, slug=category)

    def title(self, category):
        return "Burning Man Media Gallery Category Feed: %s" % category.title

    def link(self, category):
        return '%s?category=%s' % (reverse('bm.gallery.views.browse'),
                                   category.slug)        

    def description(self, category):
        return "Media recently specified with category %s" % category.title

    def items(self, category):
        items = models.MediaBase.objects.filter(categories=category,
                                                status='approved')
        items = items.order_by('-id')[:30]
        return items

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.notes


class FeaturedFeed(Feed):
    def get_object(self, request):
        return models.get_featured()

    def title(self, featured):
        return "Burning Man Media Gallery Featured Item Feed"

    def link(self, featured):
        return featured.get_absolute_url()

    def description(self, featured):
        return "Media recently selected as the featured item"

    def items(self, featured):
        items = models.FeaturedMedia.objects.order_by('-id')[:30]
        return [item.media for item in items]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.notes
        
