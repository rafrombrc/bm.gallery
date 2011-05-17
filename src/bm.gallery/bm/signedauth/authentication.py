from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpResponse
from models import UserKey, WhitelistedIP, WhitelistedDomain
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
        valid = sig.valid()

        log.debug('auth result: %s, %s', valid, sig.error)
        if valid:
            request.user = sig.user
        else:
            self.error = sig.error

        return self.error == ''

    def challenge(self):
        resp = HttpResponse("Authorization Required")
        resp.status_code = 401
        return resp

    def __repr__(self):
        return u'<UserAuthentication>'

class IPUserAuthentication(UserAuthentication):
    """
    Authenticates via IP WhiteListing if possible,
    followed by UserAuthentication.
    """
    def is_authenticated(self, request):
        log.debug('IPUserAuthentication start')

        user = WhitelistedIP.objects.whitelisted_user(request=request)
        if user is not None:
            log.debug('got whitelisted user from ip: %s', user)
        else:
            user = WhitelistedDomain.objects.whitelisted_user(request=request)
            if user is not None:
                log.debug('got whitelisted user from domain: %s', user)

        if user is not None:
            request.user = user
            return True

        return super(IPUserAuthentication, self).is_authenticated(request)

    def __repr__(self):
        return u'<IPUserAuthentication>'

# ----- helpers

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
            valid = 'valid'
        else:
            valid = 'not valid'
        return u"Signature for %(user)s [%(valid)s]" % {'user': self.user, 'valid' : valid}

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
                username = req.GET.get('user', None)
                if username:
                    log.debug('Got username from query: %s', username)
                    try:
                        user = User.objects.get(username=username)
                    except User.DoesNotExist:
                        log.debug('Could not retrieve username: %s', username)

                if user is None and hasattr(req, 'user') and req.user is not None:
                    log.debug('Got user from request')
                    user = req.user

            if user is None:
                log.debug('No user - returning AnonymousUser')
                user = AnonymousUser()
            self._user = user

            if req is not None and req.user is None:
                req.user = user

        return self._user

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
            self.error = 'No url to check'
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
                self.error = 'Signature invalid - no seed given'

            try:
                key = UserKey.objects.get(user = u)
                valid, msg = key.verify_url(url)
                if not valid:
                    self.error = msg

            except UserKey.DoesNotExist:
                self.error = "I can't find a key for that user"

            self._valid = self.error is None

        return self._valid
