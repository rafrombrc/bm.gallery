from bm.gallery.views import media_view
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseNotFound, HttpResponseBadRequest, HttpResponse
from piston.handler import BaseHandler
from piston.utils import rc
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
    resource = media_view(request, mediatype, username, slug, piston=True)
    if not resource:
        raise Http404()

    data = resource.display.file.read()
    imgtype = imghdr.what(resource.display.file.name, data)
    return HttpResponse(data, mimetype='image/%s' % imgtype)

