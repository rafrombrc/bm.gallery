import ldap
from django.conf import settings
from bm.gallery.utils import encode_modlist_strings

def get_ldap_connection():
    ldapper = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
    ldapper.simple_bind_s(who=settings.AUTH_LDAP_BIND_DN,
                           cred=settings.AUTH_LDAP_BIND_PASSWORD)
    return ldapper

def get_user_dn(username):
    return 'uid=%s,ou=galleries,dc=burningman,dc=com' % username


def ldap_add(dn, modlist_map):
    ldapper = get_ldap_connection()
    encode_modlist_strings(modlist_map)
    modlist = ldap.modlist.addModlist(modlist_map)
    ldapper.add_s(dn, modlist)
    ldapper.unbind_s()
