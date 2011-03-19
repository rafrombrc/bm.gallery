from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from models import UserKey
import logging

log = logging.getLogger(__name__)

class UserAuthentication(object):
    """
    Authenticates via RequestSignature methods
    """
    def __init__(self):
        self.error = ''

    def is_authenticated(self, request):
        log.debug('UserAuthentication start')
        self.error = ''
        sig = None
        sig = Signature(request)

        log.debug('auth result: %s, %s', sig.valid, sig.message)
        if sig.valid:
            request.user = sig.user
        else:
            self.error = sig.error

        return self.error == ''

    def challenge(self):
        resp = HttpResponse("Authorization Required: %s" % self.error)
        resp.status_code = 401
        return resp

    def __repr__(self):
        return u'<UserAuthentication>'

class Signature(object):
    """A signature, generated from a Request."""

    def __init__(self, request):
        self.request = request
        self.error = None
        self._valid  = None
        self._user = None
        self._seed = None
        self._query = None
        self._last_url = None

    def __unicode__(self):
        if self.valid:
            valid = _('valid')
        else:
            valid = _('not valid')
        return _(u"Signature for %(user)s [%(valid)s]") % {'user': self.user, 'valid' : valid}

    @property
    def query(self):
        """Lazy load the query, retreiving from the request if necessary"""
        if self._query is None:
            pass
        return self._query

    @property
    def seed(self):
        """Lazy load the seed, building from the request if necessary"""
        if self._seed is None and self.request is not None:
            self._seed = self.request.GET.get('seed', None)

        return self._seed

    @property
    def user(self):
        """Lazy load the user, retreiving from the request if necessary"""
        if self._user is None:
            req = self.request
            user = None
            if req is not None:
                if hasattr(req, 'user') and req.user is not None:
                    log.debug('Got user from request')
                    user = req.user
                else:
                    log.debug('Getting user from query')
                    username = req.GET.get('user', None)
                    if username:
                        try:
                            user = User.objects.get(username=username)
                        except User.DoesNotExist:
                            log.debug('Could not retrieve username: %s', username)

            if user is None:
                log.debug('No user - returning AnonymousUser')
                user = AnonymousUser()
            self._user = user
        return self._user

    @property
    def valid(self, url=None):
        """Return the "valid" status of the Signature, caching result.

        Kwargs:
            url: the full url string, including query parameters.

        Returns:
            Boolean result

        Note that any error message will be in the 'error' property of this object.
        """
        if url is None and self.request is not None:
            url = self.request.get_full_path()

        else:
            self.error = _('No url to check')
            self._valid = False
            return False

        log.debug('checking validity for %s', url)

        if self._valid is None or self._last_url != url:
            self._last_url = url

            if self.user.is_anonymous():
                u = None
            else:
                u = self.user

            seed = self.seed
            if seed is None:
                self.error = _('Signature invalid - no seed given')

            try:
                key = UserKey.objects.get(user = u)
                valid, msg = key.verify_url(url)
                if not valid:
                    self.error = msg

            except UserKey.DoesNotExist:
                self.error = _("I can't find a key for that user")

            self._valid = self.error is None

        return self._valid
