from bm.gallery import feeds
from django.conf import settings
from django.conf.urls.defaults import handler404, include, patterns, url
from django.contrib import admin
import django.contrib.auth.views

admin.autodiscover()

urlpatterns = patterns(
    'bm.gallery.views',
    url(r'^$', 'index'),
    url(r'^upload$', 'upload'),
    url(r'^upload/file$', 'upload_ajax', name="gallery_upload_ajax"),
    url(r'^upload/batchname$', 'batchname_ajax', name="gallery_batchname_ajax"),
    url(r'^delete/(?P<mediatype>.*)/(?P<pictureid>\d+)$', 'delete_ajax', name="gallery_delete_ajax"),
    url(r'^batch/(?P<batchid>.*)/later/$', 'batch_later', name='gallery_batch_later'),
    url(r'^batch/(?P<batchid>.*)/delete/$', 'batch_delete', name='gallery_batch_delete'),
    url(r'^batch/(?P<batchid>.*)/edit/$', 'batch_edit', name='gallery_batch_edit'),
    url(r'^batch$', 'batch_list', name='gallery_batch_list'),
    url(r'^browse$', 'browse'),
    url(r'^register$', 'register'),
    )

urlpatterns += patterns(
    '',
    (r'^api/', include('bm.gallery.api'))
    )

galroot = getattr(settings, 'GALLERIES_ROOT', settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += patterns('django.views.static',
                            (r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:],
                             'serve',
                             {'document_root': settings.MEDIA_ROOT,
                              'show_indexes': True}),
                            (r'^%s(?P<path>.*)$' % settings.GALLERIES_URL[1:],
                             'serve',
                             {'document_root': settings.GALLERIES_ROOT,
                              'show_indexes': True}),
                            (r'^%s(?P<path>.*)$' % settings.PRESS_GALLERY_URL[1:],
                             'serve',
                             {'document_root': settings.PRESS_GALLERY_PATH,
                              'show_indexes': True}),
                            )
    urlpatterns += patterns('',
                            (r'^explore/', include('signedauth.explore.urls')))

urlpatterns += patterns('',
    (r'^feeds/tag/(?P<tag>.*)$', feeds.TagFeed()),
    (r'^feeds/category/(?P<category>.*)$', feeds.CategoryFeed()),
    (r'^feeds/featured$', feeds.FeaturedFeed()),
    )

urlpatterns += patterns(
    'bm.gallery.views',
    (r'^admin/', include(admin.site.urls)),
    (r'^contributors$', 'contributors'),
    (r'^press_gallery$', 'press_gallery'),
    (r'^full_size$', 'full_size'),
    (r'^profiles/(?P<username>.*)/edit$', 'profile_edit'),
    (r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
     'password_reset_confirm'),
    (r'^reset/done/$', django.contrib.auth.views.password_reset_complete,
     {'template_name': 'gallery/password_reset_complete.html'}),
    (r'^(?P<mediatype>.*)/by_id$', 'id_lookup'),
    (r'^(?P<mediatype>.*)/by_legacy_id$', 'legacy_lookup'),
    (r'^(?P<mediatype>.*)/(?P<username>.*)/(?P<slug>.*)/moderate$',
     'media_moderate'),
    (r'^(?P<mediatype>.*)/(?P<username>.*)/(?P<slug>.*)/submit$',
     'media_submit'),
    (r'^(?P<mediatype>.*)/(?P<username>.*)/(?P<slug>.*)/edit$', 'media_edit'),
    (r'^(?P<mediatype>.*)/(?P<username>.*)/(?P<slug>.*)/feature$',
     'media_feature'),
    (r'^(?P<mediatype>.*)/(?P<username>.*)/(?P<slug>.*)/full$', 'image_full'),
    (r'^(?P<mediatype>.*)/(?P<username>.*)/(?P<slug>.*)$', 'media_view'),
    (r'^login$', django.contrib.auth.views.login,
     {'template_name': 'gallery/login.html'}),
    (r'^logout$', django.contrib.auth.views.logout,
     {'template_name': 'gallery/logout.html'}),
    (r'^faq$', 'faq'),
    (r'^upgrade_ie$', 'upgrade_ie'),
    (r'^password_reset$', django.contrib.auth.views.password_reset,
     {'template_name': 'gallery/password_reset.html',
      'email_template_name': 'gallery/password_reset_email.html'}),
    (r'^password_reset/done$', django.contrib.auth.views.password_reset_done,
     {'template_name': 'gallery/password_reset_done.html'}),
    (r'^password-change', 'password_change',
     {'template_name': 'gallery/password_change.html'}),
    )

handler500 = 'bm.gallery.views.handler500'
