from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
import base64
import datetime, time
import hashlib
import logging
import os
import types
import urllib
import urlparse

try:
    parse_qs = urlparse.parse_qs
except AttributeError:
    from cgi import parse_qs

log = logging.getLogger(__name__)

class UserSeed(models.Model):
    """Stores a single "Seed" linked to a User.

    These UserSeeds are automatically removed after expiration by the django command "signedauth_expire",
    which should be set up in a daily cron job.
    """

    user = models.ForeignKey(User, null = True, db_index=True)
    seed = models.CharField(_('Seed'), max_length=44, blank=True, null=False, db_index=True)
    timestamp = models.DateTimeField(_('Time Stamp'), auto_now_add=True)


class UserKey(models.Model):
    """A key associated to a user."""

    label = models.CharField(_('Label'), blank=False, null=False, max_length=10, help_text='Enter anything here to create the key')
    key = models.CharField(_('Key'), blank=False, null=False, max_length=44)
    timestamp = models.DateTimeField(_('Time Stamp'), auto_now_add=True)
    active = models.BooleanField(default=False)
    user = models.ForeignKey(User, null=True)

    def __unicode__(self):
        return "Userkey for %s=%s" % (self.user.username, self.key)

    def save(self, *args, **kwargs):
        """Create the random key and save the object."""

        if not self.key:
            self.key = base64.encodestring(os.urandom(32))[:-1]

        super(UserKey, self).save(*args, **kwargs)

    def sign(self, work, seed):
        """Sign a string with the given seed.

        Args:
            work: The string to sign
            seed: The seed to use as part of the signature


        Returns:
            The hexdigest of the signature string

        """
        log.debug('Signing: "%s" with seed "%s"', work, seed)
        processor = hashlib.md5(work)
        processor.update(seed)
        processor.update(self.key)
        sig = processor.hexdigest()
        return sig.lower()

    def sign_url(self, url, seed=None):
        """Sign an url.

        Args:
            url: An url to sign.  It can have query parameters which will be preserved.
                 If there is no "seed" provided as a keyword arg, it will look in the
                 query params for it before finally simply giving up and using the
                 current timestamp as the seed.

        Kwargs:
            seed: An explicit seed string to use for signing.

        Returns:
            The same url, with its signature added to the querystring.
        """
        origurl = url
        parsed = urlparse.urlsplit(url)
        qs = parse_qs(parsed.query)

        if not seed:
            # first look at query
            if 'seed' in qs:
                seed = qs
                del qs['seed']
            else:
                timestamp = datetime.datetime.now()
                timestamp = time.mktime(timestamp.timetuple())
                seed = str(int(timestamp))
                log.debug('sign_url: no seed, using timestamp %s', seed)

        if self.user:
            if 'user' in qs:
                username = qs['user']
                if type(username) is types.ListType:
                    username = username[0]
                if username != self.user.username:
                    qs['user'] = self.user.username
            else:
                qs['user'] = self.user.username
        else:
            if 'user' in qs:
                del qs['user']

        query = urllib.urlencode(qs, True)
        url = urlparse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))

        sig = self.sign(url, seed)
        last = "seed=%s&sig=%s" % (urllib.quote_plus(seed), urllib.quote_plus(sig))
        if query:
            query = "%s&%s" % (query, last)
        else:
            query = last

        url = urlparse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))
        log.debug('Signed %s = %s', origurl, url)
        return url

    def verify(self, work, seed, sig):
        """Validate that the signature for 'work' is 'sig'

        Args:
            work: the string to verify
            seed: the seed to use
            sig: the signature to validate

        Returns:
            Boolean result
        """
        goodsig = self.sign(work, seed)
        if goodsig != sig:
            log.debug('Signature mismatch: %s != %s', sig, goodsig)
            return False
        return True


    def verify_url(self, url):
        """Validate a signed url using this key.

        Args:
            url: the signed url

        Returns:
            A two-member tuple: (Boolean status of validation, Message string)
        """

        if not self.active:
            return (False, _('UserKey not active'))

        origurl = url
        parsed = urlparse.urlsplit(url)
        qs = parse_qs(parsed.query)

        user = None

        if not 'seed' in qs:
            log.debug('No seed in: %s', origurl)
            return (False, _('No seed in url'))

        if self.user:
            if not 'user' in qs:
                log.debug('No user in: %s', origurl)
                return (False, _('No user in url'))
            user = qs['user']
            if type(user) is types.ListType:
                user = user[0]
            if user != self.user.username:
                log.debug('Username mismatch: %s != %s', user, self.user.username)
                return (False, _('Wrong user'))
            if not self.user.is_active:
                log.debug('User not active: %s', user)
                return (False, _('User not active'))

        elif 'user' in qs:
            log.debug('No user should be sent for an anonymous query: %s', url)
            return(False, _('No user should be sent for an anonymous query'))

        if not 'sig' in qs:
            log.debug('No sig in: %s', origurl)
            return (False, _('URL is not signed'))

        seed = qs.pop('seed')
        if type(seed) is types.ListType:
            seed = seed[0]

        seedobj, created = UserSeed.objects.get_or_create(user=self.user, seed=seed)
        if not created:
            log.debug('Disallowing seed reuse: %s', seed)
            return (False, _('Signature invalid - seed has been used'))

        sig = qs.pop('sig')
        if type(sig) is types.ListType:
            sig = sig[0]
        sig.lower()

        query = urllib.urlencode(qs, True)
        url = urlparse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))
        if not self.verify(url, seed, sig):
            return (False, _('Signature does not validate'))

        return (True,'OK')

class WhitelistedIPManager(models.Manager):
    def request_is_whitelisted(self, request):
        """Tests whether the request's IP is whitelisted.

        Args:
            request: A django Request object

        Returns:
            Boolean
        """

        ip = request.META.get('REMOTE_ADDR', None)
        return self.ip_is_whitelisted(ip)

    def whitelisted_user(self, request = None, ip = None):
        """Returns the whitelisted user, else None"""
        if not ip and request is not None:
            ip = request.META.get('REMOTE_ADDR', None)

        if ip is not None and ip:
            white = self.filter(ip=ip)
            if white.count() > 0:
                return white[0].user
        return None

    def ip_is_whitelisted(self, ip):
        """Tests whether the request's IP is whitelisted.

        Args:
            IP: a string representing the IP to be tested

        Returns:
            Boolean
        """
        return ip is not None and ip and self.filter(ip = ip).count() > 0

class WhitelistedIP(models.Model):
    """A single IP Address that doesn't have to explicitly
    provide signatures to be authenticated as the attached user."""

    label = models.CharField(_("Label"), max_length=30)
    ip = models.IPAddressField(_("Ip Address"), db_index=True)
    user = models.ForeignKey(User)

    objects = WhitelistedIPManager()

    def __unicode__(self):
        return u"%s: %s = %s" % (self.label, self.ip, self.user.username)
