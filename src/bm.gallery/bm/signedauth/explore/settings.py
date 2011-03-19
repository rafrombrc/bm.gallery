# simple explore project for signedauth
import os.path

DEBUG = True
DIRNAME = os.path.dirname(os.path.abspath(__file__))
_parent = lambda x: os.path.normpath(os.path.join(x, '..'))

APP_ROOT = _parent(_parent(DIRNAME))

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = os.path.join(APP_ROOT, 'explore.db')

SITE_ID = 1

USE_I18N = True

MEDIA_ROOT = '%s/static/' % APP_ROOT
MEDIA_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/admin_static/'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    'django.core.context_processors.request',
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    'django_notify.context_processors.notifications',
    #"bm.gallery.context_processors.template_api",
    )

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_notify.middleware.NotificationsMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'bm.signedauth.explore.urls'

TEMPLATE_DIRS = (
    '%s/templates' % DIRNAME,
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'bm.signedauth',
    'bm.signedauth.explore',
    'django_extensions',
    'piston',
)

CACHE_BACKEND = 'file://tmp/django-cache'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    )


from bm.signedauth import logs
import os

LOGFILE = "/tmp/signedauth.log"

_loglevels = {'root' : logs.DEBUG }
log = logs.getLogger('settings', level=_loglevels,
    format="%(asctime)s [%(process)d] %(levelname)s %(name)s: %(message)s",
    outfile=LOGFILE, rotation_count=10, rotation_max=4, streaming=True)
log.info("Signedauth Started")
