from __future__ import absolute_import
from bm.gallery import models
from bm.gallery.forms import mediatype_forms, PasswordChangeForm, UserForm, ProfileForm, RegForm, PhotoFormNoFile, ArtifactFormNoFile, VideoFormNoFile
from bm.gallery.ldap_util import get_ldap_connection, get_user_dn, ldap_add
from bm.gallery.media import image_types, mediatype_deplural
from bm.gallery.utils import BetterPaginator, apply_searchable_text_filter, filter_args_from_request, media_klass_from_request
from django.conf import settings
from django.contrib.auth import authenticate, login, models as authmodels
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.models import modelformset_factory
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed,  HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.http import base36_to_int
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from tagging import models as tagmodels
import ldap.modlist
import logging
import os
import random
import shutil
import string

try:
    from urlparse import parse_qs
except ImportError:
    # python2.5
    from cgi import parse_qs
from urllib import urlencode

log = logging.getLogger(__name__)

extra_filter_args = ['b', 'mediatype', 'text']

status_map = {'Decline': 'declined',
              'Approve': 'approved',
              'Submit': 'submitted',
              'Retract': 'uploaded',
              }

if settings.USE_LDAP:
    for option in settings.AUTH_LDAP_GLOBAL_OPTIONS.items():
        ldap.set_option(*option)

def batch_delete(request, batchid):
    if not request.user.has_perm('gallery.can_upload'):
        raise PermissionDenied

    try:
        batch = models.Batch.objects.get(uuid=batchid)
    except models.Batch.DoesNotExist:
        log.warn('No such batch: %s', batchid)
        raise PermissionDenied

    if batch.user != request.user:
        log.warn('User %s cannot edit batch %s', request.user, batch)
        raise PermissionDenied

    site = Site.objects.get_current()

    if not request.GET.get('confirmed', False):
        ctx = RequestContext(request, {
                'site' : site,
                'batch' : batch,
                'confirm' : True
                })

        return render_to_response('gallery/batch_delete.html', ctx)

    else:
        request.notifications.add('Deleted batch "%s"' % batch.name)
        batch.delete()
        return HttpResponseRedirect(reverse('gallery_batch_list'))

def batch_later(request, batchid):
    log.debug('later view')
    if not request.user.has_perm('gallery.can_upload'):
        raise PermissionDenied

    try:
        batch = models.Batch.objects.get(uuid=batchid)
    except models.Batch.DoesNotExist:
        log.warn('No such batch: %s', batchid)
        raise PermissionDenied

    if batch.user != request.user:
        log.warn('User %s cannot edit batch %s', request.user, batch)
        raise PermissionDenied

    site = Site.objects.get_current()

    ctx = RequestContext(request, {
            'site' : site,
            'batch' : batch,
            })
    return render_to_response('gallery/batch_later.html', ctx)

def batch_list(request):
    batches = models.Batch.objects.filter(user = request.user, submitted=False)
    ctx = RequestContext(request, {
            'batches' : batches,
            })
    return render_to_response('gallery/batch_list.html', ctx)


def batch_edit(request, batchid):
    log.debug('batch edit view')
    if not request.user.has_perm('gallery.can_upload'):
        raise PermissionDenied

    try:
        batch = models.Batch.objects.get(uuid=batchid)
    except models.Batch.DoesNotExist:
        log.warn('No such batch: %s', batchid)
        raise PermissionDenied

    if batch.user != request.user:
        log.warn('User %s cannot edit batch %s', request.user, batch)
        raise PermissionDenied

    batch.extract_archives()

    video = batch.user.has_perm('gallery.can_review')
    photoforms = None
    photovalid = True
    videoforms = None
    videovalid = True
    artifactforms = None
    artifactvalid = True

    editing = request.method == "POST"

    if batch.photos.count():
        factory = modelformset_factory(models.Photo,
                                       form=PhotoFormNoFile,
                                       max_num = batch.photos.count(),
                                       can_delete = True,
                                       extra=0)
        if editing:
            photoforms = factory(request.POST, queryset=batch.photos.all(), prefix='photos')
            photovalid = photoforms.is_valid()
        else:
            photoforms = factory(queryset=batch.photos.all(), prefix='photos')

    if batch.artifacts.count():
        factory = modelformset_factory(models.Artifact,
                                       form=ArtifactFormNoFile,
                                       max_num = batch.artifacts.count(),
                                       can_delete = True,
                                       extra=0)

        if editing:
            artifactforms = factory(request.POST, queryset=batch.artifacts.all(), prefix='artifacts')
            artifactvalid = artifactforms.is_valid()
        else:
            artifactforms = factory(queryset=batch.artifacts.all(), prefix='artifacts')

    if video and batch.videos.count():
        factory = modelformset_factory(models.Video,
                                       form=VideoFormNoFile,
                                       max_num = batch.videos.count(),
                                       can_delete = True,
                                       extra=0)
        if editing:
            videoforms = factory(request.POST, queryset=batch.videos.all(), prefix='videos')
            videovalid = videoforms.is_valid()
        else:
            videoforms = factory(queryset=batch.videos.all(), prefix='videos')

    if editing and photovalid and videovalid and artifactvalid:
        if photoforms:
            photoforms.save()
        if videoforms:
            videoforms.save()
        if artifactforms:
            artifactforms.save()

        if request.POST.get('save_submit', False):
            log.debug('submitting')
            batch.submit_all();
            request.notifications.add('Submitted batch "%s" to moderators' % batch.name)
            url = reverse('gallery_batch_list')
        else:
            request.notifications.add('Successfully saved batch "%s"' % batch.name)
            log.debug('POST: %s' % request.POST.keys())
            url = reverse('gallery_batch_edit', args=(batch.uuid,))

        return HttpResponseRedirect(url)

    ctx = RequestContext(request, {
            'batch' : batch,
            'photoforms' : photoforms,
            'artifactforms' : artifactforms,
            'videoforms' : videoforms,
            })
    return render_to_response('gallery/batch_edit.html', ctx)

def contributors(request):
    letter = request.GET.get('letter', 'a')
    if len(letter) > 1:
        letter = letter[0]
    if not letter.isalpha():
        letter = '#'
        q = (Q(last_name__iregex=r'^[a-z]') |
             (Q(last_name='') & Q(first_name__iregex=r'^[a-z]')))
        contribs = authmodels.User.objects.exclude(q)
    else:
        letter = letter.upper()
        q = (Q(last_name__istartswith=letter) |
             (Q(last_name='') & Q(first_name__istartswith=letter)))
        contribs = authmodels.User.objects.filter(q)
    # only include contributors that have uploaded content we can see
    contribs = contribs.exclude(mediabase__isnull=True)
    if not request.user.has_perm('gallery.can_review'):
        # this is expensive, is there a way to do it w/ a single
        # query?
        excludes = []
        for contrib in contribs:
            if not len(models.MediaBase.objects.filter(owner=contrib,
                                                       status='approved')):
                excludes.append(contrib.pk)
        contribs = contribs.exclude(pk__in=excludes)
    contribs = contribs.order_by('last_name')
    num_contribs = len(contribs)
    split_length = num_contribs - (num_contribs / 2)
    contrib_lists = (contribs[:split_length], contribs[split_length:])
    template_map = dict(contrib_lists=contrib_lists,
                        letters=string.ascii_uppercase,
                        chosen_letter=letter,
                        )
    context = RequestContext(request, template_map)
    return render_to_response('gallery/contributors.html',
                              context_instance=context)


def browse(request):
    """Render the browse page.  This page supports a wide variety of
    query parameters, some of which are restricted to those w/ certain
    permissions."""
    klass = media_klass_from_request(request)
    filter_args, filter_kwargs = filter_args_from_request(request)
    press_gallery = request.GET.get('press_gallery', '')
    press_gallery = press_gallery.lower() == 'true'
    if press_gallery:
        if not request.user.has_perm('gallery.can_see_press_gallery'):
            raise PermissionDenied
        # for now we only allow photos in the press gallery, not
        # artifacts or any other types.  it's okay if the search query
        # doesn't specify a type, or if it specifies the photo type,
        # but we disallow other types of searches.  it's a little ugly
        # to be doing explicit type checking, but expedience demands
        # it :P
        if klass is models.MediaBase:
            klass = models.Photo
        if klass is not models.Photo:
            return handler400(request)
        filter_kwargs['in_press_gallery'] = True
    status = request.GET.get('status')
    if not status:
        filter_kwargs['status'] = 'approved'
    elif status != 'approved':
        if not request.user.has_perm('gallery.can_review'):
            # only reviewers can arbitrarily query based on status;
            # non-reviewers are restricted to seeing their own
            # submissions if they search on a status other than
            # 'approved'
            filter_kwargs['owner'] = request.user
        filter_kwargs['status'] = status
    else:
        filter_kwargs['status'] = status
    full_results = klass.objects.filter(*filter_args, **filter_kwargs)
    # reverse the order so most recent is first
    full_results = full_results.order_by('id').reverse()
    tag = request.GET.get('tag')
    if tag:
        full_results = tagmodels.TaggedItem.objects.get_by_model(full_results,
                                                                 tag)
    text = request.GET.get('text')
    if text:
        full_results = apply_searchable_text_filter(full_results, text)
    paginator = BetterPaginator(full_results, settings.PAGINATION_BATCH_SIZE)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        page_results = paginator.page(page)
    except (InvalidPage, EmptyPage):
        page_results = paginator.page(paginator.num_pages)
    query_string = request.META.get('QUERY_STRING')
    # remove 'page' from query string so it doesn't get used in the template
    query_map = parse_qs(query_string)
    query_map.pop('page', None)
    query_string = urlencode(query_map, doseq=True)
    for extra_filter in ('owner', 'tag', 'press_gallery'):
        if extra_filter in query_map:
            del(query_map[extra_filter])
    qs_no_extra_filters = urlencode(query_map, doseq=True)
    no_extra_filters_url = reverse('bm.gallery.views.browse')
    if qs_no_extra_filters:
        no_extra_filters_url = '%s?%s' % (no_extra_filters_url,
                                          qs_no_extra_filters)
    template_map = {'page_results': page_results,
                    'total_count': full_results.count(),
                    'query_string': query_string,
                    'no_extra_filters_url': no_extra_filters_url,
                    'paginator': paginator.get_context(page),
                    'page': page}
    owner_username = request.GET.get('owner')
    if owner_username:
        template_map['owner'] = authmodels.User.objects.get(username=owner_username)
    if tag:
        template_map['tag'] = tag
    if press_gallery:
        template_map['press_gallery'] = True
    context = RequestContext(request, template_map)
    return render_to_response('gallery/browse.html', context)


def faq(request):
    context = RequestContext(request)
    return render_to_response('gallery/faq.html', context_instance=context)


def full_size(request):
    allowed_methods = ['POST']
    if request.method not in allowed_methods:
        return HttpResponseNotAllowed(allowed_methods)
    image_id = request.POST['id']
    klass = models.MediaBase
    mediabase = get_object_or_404(klass, id=image_id)
    image = mediabase.get_child_instance()
    button = request.POST.get('full_size', '').lower()
    if button == 'make':
        image.full_image_available = True
        image.save()
        request.notifications.add(_('Full size image now available'))
    if button == 'remove':
        # manually delete the scaled image
        filepath = image.full_image.file.name
        if os.path.exists(filepath):
            os.remove(filepath)
        image.full_image_available = False
        image.save()
        request.notifications.add(_('Full size image no longer available'))
    return HttpResponseRedirect(image.get_absolute_url())


def handler400(request):
    response = HttpResponseBadRequest()
    context = RequestContext(request)
    response.content = render_to_string('400.html', context_instance=context)
    return response


def handler500(request):
    context = RequestContext(request)
    return render_to_response('500.html', context_instance=context)


def _id_lookup(request, mediatype, fieldname):
    mediatype_plural = mediatype
    mediatype = mediatype_deplural.get(mediatype_plural)
    klass = models.mediatype_map.get(mediatype, {}).get('klass')
    if not klass:
        return HttpResponseNotFound()
    id_ = request.GET.get('id')
    if not id_:
        from bm.gallery.views import handler400
        return handler400(request)
    resource = get_object_or_404(klass, **{fieldname: id_})
    username = resource.owner.username
    if request.GET.get('full_image', '').lower() == 'true':
        extension = resource.image.file.name.split('.')[-1]
        url = '/g/scaled/%s/%s/%s_full_image.%s' % (mediatype_plural,
                                                    username,
                                                    resource.slug,
                                                    extension)
    else:
        url = reverse('bm.gallery.views.media_view',
                      kwargs=dict(mediatype=mediatype_plural,
                                  username=username,
                                  slug=resource.slug))
    if request.GET.get('geturl', '').lower() == 'true':
        return HttpResponse(url)
    return HttpResponseRedirect(url)

def id_lookup(request, mediatype):
    return _id_lookup(request, mediatype, 'id')

def image_full(request, mediatype, username, slug):
    if not request.user.has_perm('gallery.can_see_fullsize'):
        raise PermissionDenied
    user = get_object_or_404(authmodels.User, username=username)
    mediatype_plural = mediatype
    mediatype = mediatype_deplural.get(mediatype_plural)
    klass = models.mediatype_map.get(mediatype, {}).get('klass')
    if not klass:
        return HttpResponseNotFound()
    resource = klass.objects.get(owner=user, slug=slug)
    query_string = request.META.get('QUERY_STRING')
    template_map = dict(image=resource,
                        query_string=query_string)
    context = RequestContext(request, template_map)
    return render_to_response('gallery/image_full_size.html',
                              context_instance=context)

def index(request):
    featured = models.get_featured()
    photo_count = cache.get('photo_count')
    if photo_count is None:
        photo_count = models.Photo.objects.filter(status='approved').count()
        cache.set('photo_count', photo_count, 3000)
    num_pages = photo_count / settings.PAGINATION_BATCH_SIZE
    try:
        random_page = random.randrange(1, num_pages)
    except ValueError:
        # might happen if there aren't yet enough photos in the
        # gallery
        random_page = False
    template_map = dict(featured=featured,
                        random_page=random_page)
    context = RequestContext(request, template_map)
    return render_to_response('gallery/index.html',
                              context_instance=context)

def legacy_lookup(request, mediatype):
    return _id_lookup(request, mediatype, 'legacy_id')


# If Django supported object permissions, we might be able to
# wrap this entire view with a permission check. Django does
# not, however, so we just do a login_required check on the
# function and do more finely grained permission checks in the
# view code itself.
@login_required
def media_edit(request, mediatype, username, slug):
    """Generic media edit view.  Handles some existence and permission
    checks that apply to all media types, then delegates to a more type
    specific implementation."""
    # verify the object exists and fetch it, if so
    user = get_object_or_404(authmodels.User, username=username)
    mediatype = mediatype_deplural.get(mediatype)
    klass = models.mediatype_map.get(mediatype, {}).get('klass')
    if not klass:
        return HttpResponseNotFound()
    resource = get_object_or_404(klass, owner=user, slug=slug)
    # permission check
    edit_perm = 'gallery.change_%s' % klass.__name__.lower()
    if not request.user.has_perm(edit_perm):
        # not a special privs account, have to check for ownership and
        # status
        if (request.user != resource.owner
            or resource.status not in ('uploaded', 'submitted')):
            # nope.  REJECTED!
            raise PermissionDenied

    template_map = dict(image=resource)
    try:
        resource.clean_fields(exclude=['caption'])
    except ValidationError:
        pass
    else:
        template_map['can_cancel'] = True
    batch_length = request.REQUEST.get('batch_length')
    ids = request.REQUEST.get('ids', [])
    if batch_length:
        # we're in a batch upload process
        template_map['batch_length'] = batch_length
        if ids:
            ids = [int(i) for i in ids.split(',')]
        if resource.id in ids:
            ids.remove(resource.id)
        if ids:
            template_map['ids'] = ','.join([str(i) for i in ids])
        template_map['num_remaining'] = len(ids) + 1

    form_klass = mediatype_forms.get(mediatype)
    if request.method == 'POST':
        if 'cancel' in request.POST:
            request.notifications.add(_('Edit canceled.'))
            return HttpResponseRedirect(resource.get_absolute_url())
        form = form_klass(request.POST, request.FILES, instance=resource)
        try:
            form.save()
        except ValueError:
            request.notifications.add(_('Save failed.'))
            # falls through to the template rendering
        else:
            request.notifications.add(_('%s edited.' % resource.title))
            if ids:
                next_resource = None
                for id_ in ids:
                    try:
                        next_resource = klass.objects.get(id=id_)
                    except klass.DoesNotExist:
                        continue
                    break
                if next_resource is not None:
                    url = '%s/edit' % next_resource.get_absolute_url()
                    url = '%s?batch_length=%s&ids=%s' % (url,
                                                         batch_length,
                                                         template_map['ids'])
                return HttpResponseRedirect(url)
            elif batch_length:
                # last one in the series, redirect to unsubmitted view
                url = reverse('bm.gallery.views.browse')
                url = '%s?status=uploaded&owner=%s' % (url,
                                                       request.user.username)
                return HttpResponseRedirect(url)
            return HttpResponseRedirect(resource.get_absolute_url())
    else:
        form = form_klass(instance=resource)
    template_map['form'] = form
    context = RequestContext(request, template_map)
    return render_to_response('gallery/image_edit.html',
                              context_instance=context)


@login_required
def media_feature(request, mediatype, username, slug):
    if not request.user.has_perm('gallery.can_review'):
        raise PermissionDenied
    user = get_object_or_404(authmodels.User, username=username)
    mediatype_plural = mediatype
    mediatype = mediatype_deplural.get(mediatype_plural)
    klass = models.mediatype_map.get(mediatype, {}).get('klass')
    if not klass:
        return HttpResponseNotFound()
    resource = get_object_or_404(klass, owner=user, slug=slug)
    if request.method == 'POST':
        if request.POST.get('feature'):
            featured = models.FeaturedMedia(media=resource)
            featured.save()
            request.notifications.add(_('Item featured.'))
    return HttpResponseRedirect(reverse('bm.gallery.views.media_view',
                                        kwargs=dict(mediatype=mediatype_plural,
                                                    username=username,
                                                    slug=slug)))


@login_required
def media_moderate(request, mediatype, username, slug):
    if not request.user.has_perm('gallery.can_review'):
        raise PermissionDenied
    user = get_object_or_404(authmodels.User, username=username)
    mediatype_plural = mediatype
    mediatype = mediatype_deplural.get(mediatype_plural)
    klass = models.mediatype_map.get(mediatype, {}).get('klass')
    if not klass:
        return HttpResponseNotFound()
    resource = get_object_or_404(klass, owner=user, slug=slug)
    if request.method == 'POST':
        new_status = request.POST.get('new_status')
        if new_status:
            new_status = status_map.get(new_status)
            if new_status:
                resource.status = new_status
                resource.save()
                request.notifications.add(_('Resource %s.' % new_status))
    return HttpResponseRedirect(reverse('bm.gallery.views.media_view',
                                        kwargs=dict(mediatype=mediatype_plural,
                                                    username=username,
                                                    slug=slug)))


@login_required
def media_submit(request, mediatype, username, slug):
    user = get_object_or_404(authmodels.User, username=username)
    if not request.user == user:
        raise PermissionDenied
    mediatype_plural = mediatype
    mediatype = mediatype_deplural.get(mediatype_plural)
    klass = models.mediatype_map.get(mediatype, {}).get('klass')
    if not klass:
        return HttpResponseNotFound()
    resource = get_object_or_404(klass, owner=user, slug=slug)
    if request.method == 'POST':
        new_status = request.POST.get('new_status')
        if new_status:
            new_status = status_map.get(new_status)
            if new_status:
                resource.status = new_status
                resource.save()
    return HttpResponseRedirect(reverse('bm.gallery.views.media_view',
                                        kwargs=dict(mediatype=mediatype_plural,
                                                    username=username,
                                                    slug=slug)))


def media_view(request, mediatype, username, slug, piston=False):
    log.debug('media_view: %s, %s, %s, %s', mediatype, username, slug, piston)
    user = get_object_or_404(authmodels.User, username=username)
    mediatype_plural = mediatype
    mediatype = mediatype_deplural.get(mediatype_plural)
    klass = models.mediatype_map.get(mediatype, {}).get('klass')
    if not klass:
        return HttpResponseNotFound()
    filter_args, filter_kwargs = filter_args_from_request(request)
    resource = get_object_or_404(klass, owner=user, slug=slug)
    show_set_context = True # default to showing a search context
    status = request.GET.get('status')
    # The code below is the meat of the security policy, deciding
    # whether or not a user can view a particular piece of media.
    # It's fairly straightforward, I think.  Still, edit with care,
    # lest you end up exposing pages that aren't supposed to be
    # exposed.
    log.debug('checking perm for %s', request.user)
    can_review = request.user.has_perm('gallery.can_review')
    log.debug('checked perm: %s', can_review)
    if not status:
        # if there aren't any other search parameters, don't use a
        # search context
        if (not any([arg in request.GET for arg in extra_filter_args])
            and not filter_args and not filter_kwargs):
            show_set_context = False
        # status isn't specified as a search parameter, default to
        # only showing approved items, which everyone can see
        if resource.status == 'approved':
            filter_kwargs['status'] = 'approved'
        elif (not can_review and
              getattr(resource, 'full_image_available', False)):
            # it's not approved, but the full size image is explicitly
            # made available so we're allowed to see it; restrict the
            # query to only this object
            filter_kwargs['id'] = resource.id
        else:
            # object isn't in approved state, no status was specified
            # in the search parameters, user must either be the owner
            # or have review privs
            if (request.user != user and not can_review):
                raise PermissionDenied
            if not can_review:
                # we're a non-privileged user looking at one of our
                # own images, enforce a query that is limited to
                # resources we own
                filter_kwargs['owner'] = user
    elif not request.user.has_perm('gallery.can_upload'):
        # status is specified as a search parameter but user isn't a
        # contributor; not allowed
        raise PermissionDenied
    else:
        # status is specified as search arg; user is a contributor so
        # we allow it
        filter_kwargs['status'] = status
        # however, if the user doesn't have review privs, she'll be
        # limited to seeing her own images
        if not can_review:
            filter_kwargs['owner'] = user

    # now we create a query set which represents the search context
    # within which the item exists (i.e. the full set of queried
    # objects of which the one we are viewing is a single element)
    if 'mediatype' in request.GET:
        # mediatype is specified, has to be the current type
        if request.GET['mediatype'] != mediatype:
            return handler400(request)
        query_klass = klass
    else:
        # mediatype isn't specified, search all content
        query_klass = models.MediaBase
    resource_qs = query_klass.objects.filter(*filter_args, **filter_kwargs)
    tag = request.GET.get('tag')
    if tag:
        resource_qs = tagmodels.TaggedItem.objects.get_by_model(resource_qs,
                                                                tag)
    text = request.GET.get('text')
    if text:
        resource_qs = apply_searchable_text_filter(resource_qs, text)
    try:
        # verify that resource we're looking at is IN the query set
        resource_qs.get(owner=user, slug=slug)
    except query_klass.DoesNotExist:
        # if not, something is weird so we don't allow it
        raise PermissionDenied
    except query_klass.MultipleObjectsReturned:
        # possible edge case where we're searching over all media
        # types, and two objects of different types have same owner
        # and slug; check to see if the object is in the result set
        if resource not in [r.get_child_instance() for r in
                            resource_qs.filter(owner=user, slug=slug)]:
            raise PermissionDenied

    # for piston calls, we just want the resource, no template rendering needed.
    if piston:
        log.debug('returning piston resource: %s', resource)
        return resource

    # we will reverse, but not yet
    resource_qs = resource_qs.order_by('id')

    # generate prev and next link URLs
    query_string = request.META.get('QUERY_STRING')
    template_map = dict(resource=resource,
                        query_string=query_string,
                        show_set_context=show_set_context,
                        mediatype_plural=mediatype_plural)
    if show_set_context:
        # since we go in reverse order, prev is newer
        prev = resource_qs.filter(id__gt=resource.id)
        if prev.count():
            prevurl = prev[0].get_absolute_url()
        else:
            prevurl = None
        # next is older (i.e. lower id)
        next = resource_qs.filter(id__lt=resource.id).reverse()
        if next.count():
            nexturl = next[0].get_absolute_url()
        else:
            nexturl = None
        # now reverse the entire set to calculate pages
        resource_qs = resource_qs.reverse()
        # <index> out of <count> items
        index = prev.count() + 1
        count = resource_qs.count()
        browse_page = index / settings.PAGINATION_BATCH_SIZE
        if index % settings.PAGINATION_BATCH_SIZE:
            browse_page += 1
        template_map.update(dict(prevurl=prevurl,
                                 nexturl=nexturl,
                                 count=count,
                                 index=index,
                                 browse_page=browse_page))

    if request.user.has_perm('gallery.can_review'):
        if resource.status in ['submitted', 'rejected']:
            template_map['can_approve'] = True
        if resource.status in ['submitted', 'approved']:
            template_map['can_reject'] = True
    if request.user == user:
        if resource.status == 'uploaded':
            template_map['can_submit'] = True
        if resource.status == 'submitted':
            template_map['can_retract'] = True
    if mediatype in image_types:
        template = 'gallery/image.html'
        template_map['display_height'] = (resource.display.height -
                                          resource.textheight)
        if (request.user.has_perm('gallery.can_see_press_gallery') and
            getattr(resource, 'in_press_gallery', False)):
            filename = os.path.split(resource.image.name)[-1]
            url = '%s%s' % (settings.PRESS_GALLERY_URL, filename)
            template_map['press_gallery_image_url'] = url
    elif mediatype == 'video':
        template = 'gallery/video.html'
    context = RequestContext(request, template_map)
    return render_to_response(template, context_instance=context)


@csrf_protect
@login_required
def password_change(request, template_name='gallery/password_change.html',
                    post_change_redirect=None,
                    password_change_form=PasswordChangeForm):
    if post_change_redirect is None:
        post_change_redirect = reverse('bm.gallery.views.index')
    if request.method == 'POST':
        if 'save' not in request.POST:
            request.notifications.add(_('Password change canceled.'))
            return HttpResponseRedirect(post_change_redirect)
        form = password_change_form(user=request.user, data=request.POST)
        if form.is_valid():
            # we can't use form.save b/c that will update the p/w on the
            # model object, we need to  do it in LDAP
            if settings.USE_LDAP:
                ldapper = get_ldap_connection()
                dn = get_user_dn(request.user.username)
                old_password = request.POST.get('old_password')
                new_password = request.POST.get('new_password1')
                # we've already validated the old_password is correct, so
                # this shouldn't fail for password mismatch
                ldapper.passwd_s(dn, old_password, new_password)
                ldapper.unbind_s()
                request.notifications.add(_('Password change successful.'))
            else:
                form.save()
            return HttpResponseRedirect(post_change_redirect)
    else:
        form = password_change_form(user=request.user)
    context = RequestContext(request, {'form': form})
    return render_to_response(template_name, context_instance=context)


# Doesn't need csrf_protect since no-one can guess the URL
def password_reset_confirm(request, uidb36=None, token=None,
                           template_name='gallery/password_reset_confirm.html',
                           token_generator=default_token_generator,
                           set_password_form=SetPasswordForm,
                           post_reset_redirect=None):
    """
    View that checks the hash in a password reset link and presents a
    form for entering a new password.
    """
    assert uidb36 is not None and token is not None # checked by URLconf
    if post_reset_redirect is None:
        post_reset_redirect = reverse('django.contrib.auth.views.password_reset_complete')
    try:
        uid_int = base36_to_int(uidb36)
    except ValueError:
        raise HttpResponseNotFound

    user = get_object_or_404(authmodels.User, id=uid_int)
    context_instance = RequestContext(request)

    if token_generator.check_token(user, token):
        context_instance['validlink'] = True
        if request.method == 'POST':
            form = set_password_form(user, request.POST)
            if form.is_valid():
                # we can't use form.save b/c that will update the p/w on the
                # model object, we need to  do it in LDAP
                if settings.USE_LDAP:
                    ldapper = get_ldap_connection()
                    dn = get_user_dn(user.username)
                    new_password = request.POST.get('new_password1')
                    ldapper.passwd_s(dn, None, new_password)
                    ldapper.unbind_s()
                    request.notifications.add(_('Password change successful.'))
                else:
                    form.save()
                return HttpResponseRedirect(post_reset_redirect)
        else:
            form = set_password_form(None)
    else:
        context_instance['validlink'] = False
        form = None
    context_instance['form'] = form
    return render_to_response(template_name, context_instance=context_instance)


def press_gallery(request):
    """If POST, either add to or remove from press gallery.  If GET,
    redirect to the browse page w/ a properly formed press gallery
    query."""
    press_gallery_path = settings.PRESS_GALLERY_PATH
    if request.method == 'POST':
        if not request.user.has_perm('gallery.can_review'):
            raise PermissionDenied
        photo = models.Photo.objects.get(id=request.POST.get('id'))
        if photo is None:
            return handler400(request)
        if not os.path.exists(press_gallery_path):
            os.makedirs(press_gallery_path)
        action = request.POST.get('press_gallery', '').lower()
        filename = os.path.split(photo.image.name)[-1]
        press_photo_path = '%s%s' % (press_gallery_path, filename)
        if action == 'remove':
            if os.path.exists(press_photo_path):
                os.remove(press_photo_path)
            photo.in_press_gallery = False
            photo.save()
            request.notifications.add(_('Image removed from press gallery.'))
        elif action == 'add':
            shutil.copy(photo.image.file.name, press_photo_path)
            photo.in_press_gallery = True
            photo.save()
            request.notifications.add(_('Image added to press gallery.'))
        return HttpResponseRedirect(photo.get_absolute_url())
    # Redirect to a browse page query
    if not request.user.has_perm('gallery.can_see_press_gallery'):
        raise PermissionDenied
    url =  '%s?press_gallery=true' % reverse('bm.gallery.views.browse')
    return HttpResponseRedirect(url)


@csrf_protect
@login_required
def profile_edit(request, username):
    # a bit of hackage so we can make the email field required w/o
    # having to actually change the default user model :(
    if request.user.username == username:
        user = request.user
    else:
        if not request.user.has_perm('gallery.can_admin_users'):
            raise PermissionDenied
        user = get_object_or_404(authmodels.User, username=username)
    profile = user.get_profile()
    emailerror = ''
    if request.method == 'POST':
        if 'save' not in request.POST:
            request.notifications.add(_('Edit canceled'))
            return HttpResponseRedirect('/')
        if not request.POST.get('email'):
            # email is required, but not at the model level, so we fake it
            emailerror = _(u'This field is required.')
        userform = UserForm(request.POST, instance=user)
        profileform = ProfileForm(request.POST, instance=profile)
        try:
            if emailerror:
                # more fake-age
                raise ValueError
            userform.save()
            profileform.save()
        except ValueError:
            request.notifications.add(_('Save failed.'))
            # falls through to the template rendering
        else:
            request.notifications.add(_('Profile edited.'))
            return HttpResponseRedirect('/')
    else: # not a POST
        userform = UserForm(instance=user)
        profileform = ProfileForm(instance=profile)
    template_map = dict(forms=(userform, profileform),
                        emailerror=emailerror,
                        password_link=True)
    context = RequestContext(request, template_map)
    return render_to_response('gallery/profile_edit.html',
                              context_instance=context)


def register(request):
    if not request.user.is_anonymous():
        return HttpResponseRedirect(reverse('bm.gallery.views.index'))
    emailerror = ''
    if request.method == 'POST':
        if 'save' not in request.POST:
            request.notifications.add(_('Registration canceled.'))
            return HttpResponseRedirect(reverse('bm.gallery.views.index'))
        if not request.POST.get('email'):
            emailerror = _(u'This field is required.')
        regform = RegForm(request.POST)
        profileform = ProfileForm(request.POST)
        if regform.is_valid() and profileform.is_valid() and not emailerror:
            if settings.USE_LDAP:
                # first create the LDAP entry
                regdata = regform.cleaned_data
                profiledata = profileform.cleaned_data
                username = regdata['username']
                password = regdata['password']
                dn = get_user_dn(username)
                modlist_map = {
                    'givenName': regdata['first_name'],
                    'sn': regdata['last_name'],
                    'mail': regdata['email'],
                    'objectclass': ['inetOrgPerson', 'shadowAccount'],
                    'uid': username,
                    'cn': ' '.join([regdata['first_name'], regdata['last_name']]),
                    'labeledURI': profiledata['url'],
                    'userPassword': password,
                    }
                ldap_add(dn, modlist_map)

                # now add user to the 'galleries' group
                groupname = 'galleries'
                ldapper = get_ldap_connection()
                groupdn = 'cn=%s,ou=groups,dc=burningman,dc=com' % groupname
                groupdict = ldapper.search_s(groupdn, ldap.SCOPE_BASE)[0][1]
                contribs = set(groupdict['uniqueMember'])
                if isinstance(dn, unicode):
                    dn = dn.encode('utf-8')
                contribs.add(dn)
                new_groupdict = groupdict.copy()
                new_groupdict['uniqueMember'] = list(contribs)
                modlist = ldap.modlist.modifyModlist(groupdict, new_groupdict)
                ldapper.modify_s(groupdn, modlist)

            # user now exists in LDAP, first authentication triggers
            # creation of Django user and profile model objects
            authed_user = authenticate(username=username,
                                       password=password)
            profile = authed_user.get_profile()
            profile.url = profiledata['url']
            profile.save()
            login(request, authed_user)
            request.notifications.add(_('Account created.'))
            return HttpResponseRedirect('/')
        else: # failed validation
            request.notifications.add(_('Registration failed.'))
            # falls through to template rendering
    else: # not a POST
        regform = RegForm()
        profileform = ProfileForm()
    template_map = dict(forms=(regform, profileform),
                        emailerror=emailerror,
                        register=True,)
    context = RequestContext(request, template_map)
    return render_to_response('gallery/profile_edit.html',
                              context_instance=context)


def upgrade_ie(request):
    context = RequestContext(request)
    return render_to_response('gallery/upgrade_ie.html',
                              context_instance=context)



@login_required
def upload(request):
    """View that displays the upload form and processes upload form
    submissions."""
    # Django's 'permission_required' decorator redirects to the login
    # form even if the user is already logged in.  That sucks, so we
    # don't use it, and we do the permission check in the code
    # instead.
    log.debug('upload view')
    if not request.user.has_perm('gallery.can_upload'):
        raise PermissionDenied

    videoPerm = request.user.has_perm('gallery.can_review')

    batch = models.Batch.objects.create(user = request.user)
    ctx = RequestContext(request, {
            'videoPermission' : videoPerm,
            'batch' : batch
            })

    return render_to_response('gallery/upload.html', ctx)

@login_required
def batchname_ajax(request):
    """View that accepts ajax upload requests, returning a JSON response"""
    log.debug('batchname ajax view')
    if not request.user.has_perm('gallery.can_upload'):
        return None

    if request.method != "POST":
        return JSONResponse(False, {}, response_mimetype(request))

    log.debug("Batch: %s" % request.POST['batch'])
    batchid = request.POST.get('batch', None)
    if not batchid:
        log.warn('no Batch')
        raise PermissionDenied
    try:
        batch = models.Batch.objects.get(uuid=batchid)
    except models.Batch.DoesNotExist:
        log.warn('No such batch: %s', batchid)
        raise PermissionDenied

    if batch.user != request.user:
        log.warn('User %s cannot edit batch %s', request.user, batch)
        raise PermissionDenied

    batchname = request.POST.get('batchname', None)

    if batchname:
        batch.name = batchname
        log.debug('updating batch %s to name: %s', batch, batchname)
        batch.save()

    return JSONResponse(batchname, {}, response_mimetype(request))

@login_required
def upload_ajax(request):
    """View that accepts ajax upload requests, returning a JSON response"""
    log.debug('upload ajax view')
    if not request.user.has_perm('gallery.can_upload'):
        return None

    #videoPerm =  request.user.has_perm('gallery.can_review')

    if request.method != "POST":
        return JSONResponse(False, {}, response_mimetype(request))

    log.debug("Batch: %s" % request.POST['batch'])
    batchid = request.POST.get('batch', None)
    if not batchid:
        log.warn('no Batch')
        raise PermissionDenied
    try:
        batch = models.Batch.objects.get(uuid=batchid)
    except models.Batch.DoesNotExist:
        log.warn('No such batch: %s', batchid)
        raise PermissionDenied

    if batch.user != request.user:
        log.warn('User %s cannot edit batch %s', request.user, batch)
        raise PermissionDenied

    batchname = request.POST.get('batchname', None)

    if batchname:
        batch.name = batchname
        log.debug('updating batch %s to name: %s', batch, batchname)
        batch.save()

    uploaded = request.FILES.get('file')
    f, ext = uploaded.name.rsplit('.',1)
    ext = ext.lower()
    if ext in ('zip','tar','tar.gz','tgz','tbz','tar.bz'):
        log.debug('saving ArchiveFile')
        instance = models.ArchiveFile.objects.create(
                owner = request.user,
                filefield = uploaded,
                batch = batch)

        data = [{'name': uploaded.name,
                 'url': '',
                 'thumbnail_url': '',
                 'delete_url': reverse('gallery_delete_ajax', args=['archive', instance.id]),
                 'delete_type': "DELETE",
                 'batchid' : batch.uuid,
                 'batchname' : batch.name}]
    else:
        instance = models.media_from_file(uploaded, batch, request.user)

        if instance is None:
            data = [{'error' : 'Could not read file: %s, perhaps it is corrupt' % uploaded.name}]
        else:
            data = [{'name': uploaded.name,
                     'url': instance.image.url,
                     'thumbnail_url': instance.thumbnail_image.url,
                     'delete_url': reverse('gallery_delete_ajax', args=[instance.mediatype(), instance.id]),
                     'delete_type': "DELETE",
                     'batchid' : batch.uuid,
                     'batchname' : batch.name}]

    response = JSONResponse(data, {}, response_mimetype(request))
    response['Content-Disposition'] = 'inline; filename=files.json'
    return response

@login_required
def delete_ajax(request, mediatype, pictureid):
    if not (mediatype in ('image','photo','video')):
        log.error('Bad mediatype: %s', mediatype)
        raise PermissionDenied

    if not request.user.has_perm('gallery.can_upload'):
        raise PermissionDenied

    media_class = models.mediatype_map[mediatype]['klass']

    try:
        obj = media_class.objects.get(pk=pictureid)
    except media_class.DoesNotExist:
        log.debug('Media object #%i not found', pictureid)
        return JSONResponse(False, {}, response_mimetype(request))

    if not obj.owner == request.user:
        log.warn("User %s cannot delete %s because he or she doesn't own it", request.user, obj)
        raise PermissionDenied

    log.info('Deleted %s at user request', obj)
    obj.delete()
    return JSONResponse(True, {}, response_mimetype(request))

def response_mimetype(request):
    if "application/json" in request.META['HTTP_ACCEPT']:
        return "application/json"
    else:
        return "text/plain"

class JSONResponse(HttpResponse):
    """JSON response class."""
    def __init__(self,obj='',json_opts={},mimetype="application/json",*args,**kwargs):
        content = simplejson.dumps(obj,**json_opts)
        super(JSONResponse,self).__init__(content,mimetype,*args,**kwargs)

