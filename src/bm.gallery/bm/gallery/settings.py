# Shared Django settings for 'bm.gallery' project.
import os.path

APP_ROOT = os.path.normpath(os.path.dirname(__file__))

SITE_ID = 1

USE_I18N = True

MEDIA_ROOT = '%s/static/' % APP_ROOT

MEDIA_URL = '/static/'

GALLERIES_URL = '/g/'

ADMIN_MEDIA_PREFIX = '/admin_static/'

FLOWPLAYER_CONFIG = {
    'default' :
    { 'clip' : { 'autoPlay':'false' },
      'plugins' : { 'controls' : { 'playlist': 'false' } }
      },
    }

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    'django.core.context_processors.request',
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    'django_notify.context_processors.notifications',
    "bm.gallery.context_processors.template_api",
    )

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_notify.middleware.NotificationsMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'bm.gallery.urls'

TEMPLATE_DIRS = (
    '%s/templates' % APP_ROOT,
)

LOGIN_URL = '/login'

AUTH_PROFILE_MODULE = 'gallery.Profile'

PAGINATION_BATCH_SIZE = 15

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'tagging',
    'imagekit',
    'flowplayer',
    'bm.gallery',
    'signedauth',
    'django_extensions',
    #'signedauth.explore',
    'south',
    'gunicorn',
)

try:
    from bm.gallery.local_settings import BUILDOUT_ROOT
except ImportError:
    BUILDOUT_ROOT = '/'.join(APP_ROOT.split('/')[:-4]) + '/'

GALLERIES_ROOT = '%smedia/' % BUILDOUT_ROOT
PRESS_GALLERY_URL = '%spress_gallery/' % GALLERIES_URL
PRESS_GALLERY_PATH = '%spress_gallery/' % GALLERIES_ROOT
FLOWPLAYER_URL = '/static/flowplayer/flowplayer-3.2.0.swf'
CACHE_BACKEND = 'file://%svar/tmp/django-cache' % BUILDOUT_ROOT

AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
    )

USE_LDAP = True

# Load the local settings
from bm.gallery.local_settings import *

