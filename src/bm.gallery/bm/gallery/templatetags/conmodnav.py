from bm.gallery import models
from django import template
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

register = template.Library()

@register.inclusion_tag('gallery/con_mod_nav.html', takes_context=True)
def con_mod_nav(context, media_ob=None):
    request = context['request']
    user = request.user
    if not user.has_perm('gallery.can_upload'):
        # if you can't upload, you shouldn't get any of this nav
        return dict()

    current_path = request.get_full_path()
    nav_items = []

    browse_url = reverse('bm.gallery.views.browse')
    if len(models.MediaBase.objects.filter(status='uploaded',
                                           owner=user)):
        my_unsubmitted = dict(
            title=_('My Unsubmitted'),
            url = reverse('gallery_batch_list'))
        nav_items.append(my_unsubmitted)

    if len(models.MediaBase.objects.filter(status='approved',
                                           owner=user)):
        my_approved = dict(
            title=_('My Approved'),
            url='%s?status=approved&owner=%s' % (browse_url, user.username))
        nav_items.append(my_approved)

    if media_ob is not None:
        if (user.has_perm('gallery.can_review') or
            (media_ob.status == 'uploaded' and user == media_ob.owner)):
            # we can edit
            view_kwargs = dict(mediatype=media_ob.mediadir,
                               username=media_ob.owner.username,
                               slug=media_ob.slug)
            url = reverse('bm.gallery.views.media_edit', kwargs=view_kwargs)
            edit = dict(title=_('Edit'), url=url)
            if url == current_path:
                edit['current'] = True
            nav_items.append(edit)

    if user.has_perm('gallery.can_review'):
        url = '%s?status=submitted' % reverse('bm.gallery.views.browse')
        pending = dict(title=_('Pending'), url=url)
        nav_items.append(pending)

    upload = dict(title=_('Upload'), url=reverse('bm.gallery.views.upload'))
    if upload['url'] == current_path:
        upload['current'] = True
    nav_items.append(upload)

    return dict(nav_items=nav_items)
