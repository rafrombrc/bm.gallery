from bm.signedauth.authentication import IPUserAuthentication
from django.conf.urls.defaults import patterns
from piston.resource import Resource
from handlers import MediaViewHandler

ipauth = IPUserAuthentication()
media_view = Resource(handler=MediaViewHandler, authentication=ipauth)

urlpatterns = patterns(
    '',
    (r'^(?P<mediatype>.*)/(?P<username>.*)/(?P<slug>.*)/image$', 'bm.gallery.handlers.media_view_image'),
    (r'^(?P<mediatype>.*)/(?P<username>.*)/(?P<slug>.*)/(?P<emitter_format>[-\w]+)$', media_view),
    )

