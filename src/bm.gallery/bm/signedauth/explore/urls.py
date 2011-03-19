from django.conf.urls.defaults import patterns, include, handler500, handler404, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

handler500 # Pyflakes
handler404

urlpatterns = patterns(
    '',
    url(r'^admin/(.*)', admin.site.root),
    url(r'^/', 'bm.signedauth.explore.views.explore'),
)

# if settings.DEBUG:
#     from staticfiles.urls import staticfiles_urlpatterns
#     urlpatterns += staticfiles_urlpatterns()
