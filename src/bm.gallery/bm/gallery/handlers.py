from bm.gallery.views import media_view
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseNotFound, HttpResponseBadRequest, HttpResponse
from piston.handler import BaseHandler
from piston.utils import rc
from bm.signedauth.authentication import IPUserAuthentication
from bm.gallery.models import Photo
import imghdr
import logging
log = logging.getLogger(__name__)

class MediaViewHandler(BaseHandler):
    """Django Piston handler which serializes a media resource into the requested return format"""
    allowed_methods = ('GET',)

    def read(self, request, mediatype=None, username=None, slug=None):
        log.debug('MediaViewHandler read: %s, %s, %s', mediatype, username, slug)
        try:
            resource = media_view(request, mediatype, username, slug, piston=True)
            log.debug('got resource: %s', resource)

        except Http404:
            log.debug('404')
            return rc.NOT_FOUND

        except PermissionDenied:
            log.debug('Denied')
            return rc.FORBIDDEN

        rtype = type(resource)
        if rtype is HttpResponseNotFound:
            log.debug('Not Found')
            return rc.NOT_FOUND

        if rtype is HttpResponseBadRequest:
            log.debug('Bad request')
            return rc.BAD_REQUEST

        log.debug('returning resource')
        return resource


def media_view_image(request, mediatype, username, slug):
    """A view which returns the raw image"""
    auth = IPUserAuthentication()
    if not auth.is_authenticated(request):
        return auth.challenge()
    resource = media_view(request, mediatype, username, slug, piston=True)
    if not resource:
        raise Http404()

    if type(resource) is not Photo:
        raise Http404('Not a photo')

    options = _parse_media_args(request)

    if options['h'] == 0 and options['w'] == 0 and options['footer'] and options['extended']:
        do_resize = False
    else:
        do_resize = options['footer'] or options['extended']

    if do_resize:
        img, fn = resource.resized(**options)
    else:
        log.debug('returning base display file')
        fn = resource.display.file.name

    log.debug('media file: %s', fn)
    data = open(fn,'r').read()

    imgtype = imghdr.what(resource.image.file.name, data)
    return HttpResponse(data, mimetype='image/%s' % imgtype)


def _parse_media_args(request):
    options = {}

    # now check for sizing & watermark options
    h = request.GET.get('h',0)
    w = request.GET.get('w',0)

    if h:
        try:
            h = int(h)
        except ValueError:
            h = None

    if w:
        try:
            w = int(w)
        except ValueError:
            w = None

    options['h'] = h
    options['w'] = w

    watermark=request.GET.get('watermark','')
    watermark = watermark.lower()
    if watermark == 'both':
        footer = True
        extended = True
    elif watermark == 'footer' or watermark == 'foot':
        footer = True
        extended=False
    elif watermark == 'extended':
        footer = False
        extended = True
    else:
        footer = False
        extended = False

    options['footer'] = footer
    options['extended'] = extended

    crop = request.GET.get('crop','f')
    crop = crop.lower() in ('1','y','t','true','yes')

    options['crop'] = crop

    upscale = request.GET.get('upscale','f')
    upscale = upscale.lower() in ('1','y','t','true','yes')

    options['upscale'] = upscale

    return options
