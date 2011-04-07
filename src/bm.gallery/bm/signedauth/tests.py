from django.contrib.auth.models import User
from django.core import urlresolvers
from django.test import TestCase
from django.test.client import Client
from models import UserKey, WhitelistedIP
import logging
import urlparse

try:
    parse_qs = urlparse.parse_qs
except AttributeError:
    from cgi import parse_qs

log = logging.getLogger('test')

class UserKeyTest(TestCase):
    def testCreate(self):
        k = UserKey.objects.create(active=True)
        self.assert_(k.key is not None)
        self.assert_(k.timestamp is not None)

    def testSign(self):
        """Test round-trip sign, verify"""
        k = UserKey(active=True)
        k.save()
        sig = k.sign('testing testing testing', 'xxx')
        self.assertEqual(len(sig), 32)
        self.assert_(k.verify('testing testing testing', 'xxx', sig))

    def testSignBlank(self):
         """Test round-trip sign, verify"""
         k = UserKey(active=True)
         k.save()
         sig = k.sign('', 'yyy')
         self.assertEqual(len(sig), 32)
         self.assert_(k.verify('', 'yyy', sig))

    def testSignUrlAnonymous(self):
         """Test round-trip sign, verify"""
         k = UserKey(active=True, user=None)
         k.save()
         url = 'http://localhost/test/'
         signed = k.sign_url(url, 'zzz')
         parsed = urlparse.urlsplit(signed)
         qs = parse_qs(parsed.query)
         self.assert_('seed' in qs)
         self.assert_('user' not in qs)
         self.assert_('sig' in qs)
         self.assertEqual(qs['seed'][0], 'zzz')
         self.assert_(k.verify_url(signed)[0])

    def testSignUrlAnonymousQuery(self):
         """Test round-trip sign, verify with GET params"""
         k = UserKey(active=True, user=None)
         k.save()
         url = 'http://localhost/test/?arg=this&arg2=that'
         signed = k.sign_url(url, '123')
         parsed = urlparse.urlsplit(signed)
         qs = parse_qs(parsed.query)
         self.assert_('seed' in qs)
         self.assert_('user' not in qs)
         self.assert_('sig' in qs)
         self.assertEqual(qs['seed'][0], '123')
         self.assert_('arg' in qs)
         self.assert_('arg2' in qs)
         self.assert_(k.verify_url(signed)[0])

    def testAnonymousSeedReuse(self):
         """Test invalid reuse of seed"""
         k = UserKey(active=True, user=None)
         k.save()
         url = 'http://localhost/test/'
         signed = k.sign_url(url, 'reusemenot')
         self.assert_(k.verify_url(signed)[0])
         # seed shouldn't work twice
         self.assertFalse(k.verify_url(signed)[0])

    def testSignUrlUser(self):
         """Test signature roundtrip with a real user"""
         user = User.objects.create(username='joe', is_active=True)
         k = UserKey(active=True, user=user)
         url = 'http://localhost/test/'
         signed = k.sign_url(url, 'uuu')
         parsed = urlparse.urlsplit(signed)
         qs = parse_qs(parsed.query)
         self.assert_('seed' in qs)
         self.assert_('user' in qs)
         self.assertEqual(qs['user'][0], 'joe')
         self.assert_('sig' in qs)
         self.assertEqual(qs['seed'][0], 'uuu')
         self.assert_(k.verify_url(signed)[0])

    def testSignUrlBadUser(self):
         """Test signature roundtrip with a real user"""
         user = User.objects.create(username='joe', is_active=True)
         k = UserKey(active=True, user=user)
         url = 'http://localhost/test/'
         signed = k.sign_url(url, 'uuu')

         # bad username
         bad = signed.replace('joe', 'bob')
         self.assertFalse(k.verify_url(bad)[0])

         # bad seed
         bad = signed.replace('uuu','badseed')
         self.assertFalse(k.verify_url(bad)[0])

class UserKeyEchoHandlerTest(TestCase):
    fixtures = ["signedauth_auth.json",]

    def testAuthNoSig(self):
        """Test that a simple django-piston handler will not permit unsigned url calls."""
        client = Client()
        try:
            url = urlresolvers.reverse('userechohandler',
                                       kwargs={'emitter_format' : 'json'})
            response = client.get(url + '?echo=test')
            self.assertContains(response, "Authorization Required",
                                status_code=401)

        except urlresolvers.NoReverseMatch:
            log.warning("Could not test userauth echo handler - no echo handler found, perhaps you need to add 'bm.signedauth.explore.urls' to your urls?")

    def testGoodAuth(self):
        """Test that a simple django-piston handler will permit properly signed url calls."""
        client = Client()
        try:
            url = urlresolvers.reverse('userechohandler',
                                       kwargs={'emitter_format' : 'json'})
            url += '?echo=success'
            k = UserKey.objects.get(pk=2)
            signed = k.sign_url(url, '123')
            response = client.get(signed)

            self.assertContains(response, '"data_length": 7',
                                status_code=200)
            self.assertContains(response, '"echo": "success"',
                                status_code=200)

        except urlresolvers.NoReverseMatch:
            log.warning("Could not test userauth echo handler - no echo handler found, perhaps you need to add 'bm.signedauth.explore.urls' to your urls?")


class IPUserKeyEchoHandlerTest(TestCase):
    fixtures = ["signedauth_auth.json",]

    def testAuthNoSig(self):
        """Test that a simple django-piston handler will not permit unsigned url callswhen the IP is not whitelisted."""
        WhitelistedIP.objects.get(pk=1).delete()
        client = Client()
        try:
            url = urlresolvers.reverse('ipechohandler',
                                       kwargs={'emitter_format' : 'json'})
            response = client.get(url + '?echo=test')
            self.assertContains(response, "Authorization Required",
                                status_code=401)

        except urlresolvers.NoReverseMatch:
            log.warning("Could not test ipuserauth echo handler - no echo handler found, perhaps you need to add 'bm.signedauth.explore.urls' to your urls?")

    def testGoodAuth(self):
        """Test that a simple django-piston handler will permit properly signed url calls, even when the IP is not whitelisted."""
        client = Client()
        WhitelistedIP.objects.get(pk=1).delete()
        try:
            url = urlresolvers.reverse('ipechohandler',
                                       kwargs={'emitter_format' : 'json'})
            url += '?echo=success'
            k = UserKey.objects.get(pk=2)
            signed = k.sign_url(url, '123')
            response = client.get(signed)

            self.assertContains(response, '"data_length": 7',
                                status_code=200)
            self.assertContains(response, '"echo": "success"',
                                status_code=200)

        except urlresolvers.NoReverseMatch:
            log.warning("Could not test ipuserauth echo handler - no echo handler found, perhaps you need to add 'bm.signedauth.explore.urls' to your urls?")

    def testGoodIPNoSig(self):
        """Test that a simple django-piston handler will permit unsigned url calls from whitelisted IPs."""
        client = Client()
        try:
            url = urlresolvers.reverse('ipechohandler',
                                       kwargs={'emitter_format' : 'json'})
            url += '?echo=happy'
            response = client.get(url)

            self.assertContains(response, '"data_length": 5',
                                status_code=200)
            self.assertContains(response, '"echo": "happy"',
                                status_code=200)

        except urlresolvers.NoReverseMatch:
            log.warning("Could not test ipuserauth echo handler - no echo handler found, perhaps you need to add 'bm.signedauth.explore.urls' to your urls?")

class EchoHandlerTest(TestCase):
    fixtures = ["signedauth_auth.json",]


    def testEchoHandler(self):
        """Simple test to ensure that the echo handler
        is working when called without authentication"""
        client = Client()

        try:
            url = urlresolvers.reverse('echohandler',
                                       kwargs={'emitter_format' : 'json'})
            response = client.get(url + '?echo=test')
            self.assertContains(response, '"data_length": 4',
                                status_code=200)
            self.assertContains(response, '"echo": "test"',
                                status_code=200)

        except urlresolvers.NoReverseMatch:
            log.warning("Could not test echo handler - no echo handler found, perhaps you need to add 'bm.signedauth.explore.urls' to your urls?")

class WhitelistTest(TestCase):
    fixtures = ["signedauth_auth.json",]
    def testWhitelistByIP(self):
        self.assert_(WhitelistedIP.objects.ip_is_whitelisted('127.0.0.1'))


    def testWhitelistUser(self):

        user = WhitelistedIP.objects.whitelisted_user(ip='127.0.0.1')
        self.assert_(user)
        self.assertEquals(user.username, 'LocalUser')
