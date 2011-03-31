from bm.signedauth.authentication import UserAuthentication, IPUserAuthentication
from django.conf.urls.defaults import patterns, handler500, handler404, url
from django.contrib import admin
from handlers import EchoHandler
from piston.resource import Resource
admin.autodiscover()

handler500 # Pyflakes
handler404

userauth = UserAuthentication()
ipauth = IPUserAuthentication()

userecho = Resource(handler=EchoHandler, authentication=userauth)
ipecho = Resource(handler=EchoHandler, authentication=ipauth)
echo = Resource(handler=EchoHandler)

urlpatterns = patterns(
    '',
    url(r'^admin/(.*)', admin.site.root),
    url(r'^explore/$', 'bm.signedauth.explore.views.explore', name="exploreform"),
    url(r'^echo\.(?P<emitter_format>[-\w]+)/$',echo, name="echohandler"),
    url(r'^ipecho\.(?P<emitter_format>[-\w]+)/$',ipecho, name="ipechohandler"),
    url(r'^userecho\.(?P<emitter_format>[-\w]+)/$',userecho, name="userechohandler")

)

# if settings.DEBUG:
#     from staticfiles.urls import staticfiles_urlpatterns
#     urlpatterns += staticfiles_urlpatterns()
