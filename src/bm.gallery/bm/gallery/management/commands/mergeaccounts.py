import os

from optparse import make_option

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from django.conf import settings

from bm.gallery.models import Photo, Artifact, Profile
from bm.gallery.ldap_util import get_user_dn, ldap_delete


class Command(BaseCommand):
    args = '<canonical_user> <obsolete_user> [--readonly]'
    help = ('Merges all Gallery pictures from obsolete_user into '
            'canonical_user (both files and metadata).\n'
            'Pass usernames into each parameter.\nThe '
            'default behavior is to commit the actions. Pass --readonly to '
            'see what actions this command will take, without actually doing '
            'them.\nWARNING: Without --readonly, this command will delete the '
            'obsolete user from Django and LDAP. Use with caution.\n\n')

    option_list = BaseCommand.option_list + (
        make_option('--readonly',
            action='store_true',
            dest='readonly',
            default=False,
            help='Shows output but doesn\'t commit actions.'),
        )

    def handle(self, *args, **options):
        self.readonly = options.get('readonly', False)

        if self.readonly:
            self.stdout.write('Output is sample only, '
                              'changes NOT committed.\n')

        if len(args) != 2:
            self.stdout.write('Error: Please provide two usernames.\n\n' \
              'Usage: ' + Command.args + '\n' + Command.help)
            return

        canonical_username = args[0]
        obsolete_username = args[1]

        self.stdout.write('Canonical: ' + canonical_username + '\n')
        self.stdout.write('Obsolete: ' + obsolete_username + '\n')

        # Get accounts from usernames
        canonical_user = None
        obsolete_user = None

        try:
            canonical_user = User.objects.get(username=canonical_username)
        except User.DoesNotExist:
            self.stdout.write('\nError: Canonical user %s does not exist.\n' %
                              canonical_username)
            return

        try:
            obsolete_user = User.objects.get(username=obsolete_username)
        except User.DoesNotExist:
            self.stdout.write('\nError: Obsolete user %s does not exist.\n'
                              % obsolete_username)
            return

        self.one_account_to_rule_its_doppelgangers(canonical_user,
                                                   obsolete_user)

    # Takes a canonical account, and a list of other accounts, and moves the
    # pictures to the new one.
    def one_account_to_rule_its_doppelgangers(self, canonical_user,
                                              obsolete_user):
        # For each photo owned by this user, change its owner to the canonical
        # user.
        photos = Photo.objects.filter(owner=obsolete_user)
        artifacts = Artifact.objects.filter(owner=obsolete_user)
        self.stdout.write('Found %s photos and %s artifacts for %s.\n'
                          % (len(photos), len(artifacts),
                             str(obsolete_user)))

        self.stdout.write('Merging images for account "%s" into account "%s".'
                          '\n' % (str(obsolete_user), str(canonical_user)))

        # Migrate each image individually.
        images = list(photos) + list(artifacts)  # cvrt from QuerySet to object
        for image in images:
            self.change_image_owner(canonical_user, image)

        # Delete the obsolete account, both the Gallery profile and the Django
        # user.

        if not self.readonly:
            obsolete_profile = Profile.objects.get(user=obsolete_user)
            obsolete_profile.delete()
            obsolete_user.delete()

            # Delete the ldap account for the obsolete user.
            if settings.USE_LDAP:
                self.delete_ldap_user(obsolete_user)
        self.stdout.write('Done.\n')

    def delete_ldap_user(self, obsolete_user):
        dn = get_user_dn(obsolete_user.username)
        ldap_delete(dn)

    def change_image_owner(self, newuser, image):
        # Separate the relative directory and the filename itself:
        # subpath oldfilename
        subpath, old_filename = os.path.split(image.image.path)
        # e.g. '/var/www/bm.gallery/media/photos/andrei_rublev',
        # 'andrei_rublev.1234.jpg'

        # Remove the author's dir from the base dir used to store images of the
        # current type.
        images_base, old_owner_dir = os.path.split(subpath)
        # e.g. '/var/www/bm.gallery/media/photos', 'andrei_rublev'

        # Create new filename extension (based on new user and id)
        basename, extension = os.path.splitext(old_filename)
        new_filename = '%s.%d%s' % (newuser.username, image.id, extension)

        # basepath   newuser newfilename
        # Move the file to its new home, e.g.
        '/var/www/bm.gallery/media/photos/andrei/andrei.1234.jpg'
        new_file_path = (images_base + '/' + newuser.username
                         + '/' + new_filename)

        # Change image metadata in Django
        image.image.upload_to = subpath + new_filename
        image.owner = newuser

        if isinstance(image, Photo) and image.in_press_gallery:
            self.change_image_in_press_gallery(old_filename, new_filename)

        self.stdout.write('%s -> %s\n' % (image.image.path, new_file_path))

        # We're done prep, now commit the actual moves.
        if not self.readonly:
            image.save()
            # Note: os.renames will create intermediate dirs if they don't
            # exist.
            os.renames(image.image.path, new_file_path)

    def change_image_in_press_gallery(self, old_filename, new_filename):
        old_path = settings.PRESS_GALLERY_PATH + old_filename
        new_path = settings.PRESS_GALLERY_PATH + new_filename

        self.stdout.write('Found a press image.\n')
        self.stdout.write('%s -> %s' % (old_path, new_path))

        if not self.readonly:
            os.renames(old_path, new_path)
