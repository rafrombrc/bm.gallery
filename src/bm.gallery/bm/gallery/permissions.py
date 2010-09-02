"""
Initial code to handle non-Model based permission definition from
http://djangosnippets.org/snippets/334/
"""
from bm.gallery import models
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import signals


def register_custom_permissions(permissions, sender, callbacks=None):
    """
    Registers any number of custom permissions that are not related to any
    certain model (i.e. "global/app level").
    
    You must pass the models module of your app as the sender parameter. If
    you use "None" instead, the permissions will be duplicated for each
    application in your project.
    
    Permissions is a tuple:    
       (
           # codename, name
           ("can_drive", "Can drive"),
           ("can_drink", "Can drink alcohol"),
       )
       
    Examples:        
        from myapp.mysite import models as app
        register_custom_permissions(('my_perm', 'My Permission'), app)
        register_custom_permissions(('my_perm', 'My Permission'),
                                    sys.modules[__name__])  # in models.py
        register_custom_permissions(('my_perm', 'My Permission'))
    """
    if callbacks is None:
        callbacks = []

    def mk_permissions(permissions, app, verbosity):
        # retrieve actual appname string from module instance
        appname = app.__name__.lower().split('.')[-2]
        # create a content type for the app
        ct, created = ContentType.objects.get_or_create(model='', app_label=appname,
                                                        defaults={'name': appname})
        if created and verbosity >= 2: print "Adding custom content type '%s'" % ct
        # create permissions
        perm_objs = []
        for codename, name in permissions:
            p, created = Permission.objects.get_or_create(codename=codename,
                            content_type__pk=ct.id,
                            defaults={'name': name, 'content_type': ct})            
            if created and verbosity >= 2:
                print "Adding custom permission '%s'" % p
            perm_objs.append(p)
        return perm_objs

    def permreg(**kwargs):
        app = kwargs.get('app')
        verbosity = kwargs.get('verbosity')
        result = mk_permissions(permissions, app, verbosity)
        for callback in callbacks:
            # do something w/ the permissions that have just been
            # created
            for perm_obj in result:
                callback(perm_obj)

    signals.post_syncdb.connect(permreg, sender=sender, weak=False)

msg = ("XXX!!!NOTE!!!XXX: DJANGO GROUP '%s' DOES NOT EXIST.  THIS MEANS DJANGO "
       "GROUPS HAVEN'T YET BEEN INITIALIZED FROM LDAP.  THIS INITIALIZATION "
       "WILL HAPPEN WHEN THIS 'syncdb' OPERATION FINISHES.  YOU WILL NEED TO "
       "RUN 'django syncdb' _AGAIN_ WHEN THIS RUN COMPLETES TO FINALIZE THE "
       "SETUP.")
msg_printed = False

def grant_to_group(permission, groupname):
    try:
        group = Group.objects.get(name=groupname)
    except Group.DoesNotExist:
        # LDAP group not yet initialized
        global msg_printed
        if not msg_printed:
            print msg % groupname
            msg_printed = True
        return
    group.permissions.add(permission)
    group.save()

def grant_to_galleries(permission):
    return grant_to_group(permission, 'galleries')

def grant_to_reviewers(permission):
    return grant_to_group(permission, 'galleries_reviewer')

def grant_to_press(permission):
    return grant_to_group(permission, 'galleries_press')

register_custom_permissions([('can_upload', 'Can Upload')],
                            models, [grant_to_galleries])
register_custom_permissions([('can_review', 'Can Review')],
                            models, [grant_to_reviewers])
register_custom_permissions([('can_admin_users', 'Can Admin Users')],
                            models, [grant_to_reviewers])
register_custom_permissions([('can_see_fullsize', 'Can see full-size media')],
                            models, [grant_to_reviewers])
register_custom_permissions([('can_see_press_gallery', 'Can see press gallery')],
                            models, [grant_to_press, grant_to_reviewers])

def grant_edit_permissions(**kwargs):
    """Grant edit permission on all of the exposed model types to our
    reviewers."""
    try:
        reviewers = Group.objects.get(name='galleries_reviewer')
    except Group.DoesNotExist:
        # LDAP group not yet initialized
        global msg_printed
        if not msg_printed:
            print msg % 'galleries_reviewer'
            msg_printed = True
        return
    for modeldata in models.mediatype_map.values():
        slug = modeldata['klass'].__name__.lower()
        perm_codename = 'change_%s' % slug
        permission = Permission.objects.get(codename=perm_codename)
        reviewers.permissions.add(permission)
    reviewers.save()

signals.post_syncdb.connect(grant_edit_permissions, sender=models)
