#import unittest
from django.contrib.auth.models import User
from django.test import TestCase
from models import UserKey, WhitelistedIP
import logging
import urlparse
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
         qs = urlparse.parse_qs(parsed.query)
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
         qs = urlparse.parse_qs(parsed.query)
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
         qs = urlparse.parse_qs(parsed.query)
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

class WhitelistTest(TestCase):
    fixtures = ["signedauth_auth.json",]
    def testWhitelistByIP(self):
        self.assert_(WhitelistedIP.objects.ip_is_whitelisted('127.0.0.1'))

