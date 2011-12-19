from __future__ import absolute_import
from bm.gallery.resize import resize_image
from bm.gallery.watermark import add_watermark
from datetime import datetime
from django.conf import settings
from django.contrib.auth import models as authmodels
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.validators import email_re
from django.db import models, connection
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import UUIDField
from hachoir_core.stream.input import InputIOStream
from imagekit.lib import Image
from imagekit.models import ImageModel
from imagekit.specs import Accessor
from tagging import models as tagmodels
import hachoir_metadata
import hachoir_parser
import logging
import os
import shutil
import tarfile
import tempfile
import zipfile

log = logging.getLogger('gallery.models')

def get_media_path(instance, filename=''):
    return os.path.join(instance.mediadir, instance.owner.username, filename)

def get_scaled_media_path(instance, filename='', suffix=''):
    if filename and filename.startswith('/'):
        path, filename = os.path.split(filename)
        path = path.split('/')
        if path[-1] == instance.owner.username:
            path = path[:-1]
        if path[-1] == instance.mediadir:
            path = path[:-1]
        path = '/'.join(path)
    else:
        path = ''

    if suffix and filename:
        parts = os.path.splitext(filename)
        parts = [parts[0], suffix, parts[1]]
        filename = ''.join(parts)

    return os.path.join(path, 'scaled', get_media_path(instance, filename))

statuses = (('approved', _('Approved')),
            ('submitted', _('Submitted')),
            ('rejected', _('Declined')),
            ('uploaded', _('Uploaded')),
            )

galroot = getattr(settings, 'GALLERIES_ROOT', settings.MEDIA_ROOT)
mediastorage = FileSystemStorage(location=galroot,
                                 base_url=settings.GALLERIES_URL)


class Category(models.Model):
    slug = models.CharField(_('slug'), max_length=15)
    title = models.CharField(_('title'), max_length=25)

    def __unicode__(self):
        return self.title

class Profile(models.Model):
    """Gallery-specific profile data."""
    user = models.ForeignKey(authmodels.User, editable=False, null=False,
                             unique=True)
    url = models.URLField(null=True, max_length=300, blank=True)

    def __unicode__(self):
        return "Profile: %s" % (self.user.username)

    def has_valid_email(self):
        return bool(email_re.match(self.user.email))

def add_profile_callback(sender, **kwargs):
    if sender == authmodels.User and kwargs.get('created'):
        profile = Profile(user=kwargs['instance'])
        profile.save()
signals.post_save.connect(add_profile_callback)


class MediaBase(models.Model):
    """Abstract base class for all media content models.  Note that this
    is not an Abstract Base Class in the most strict Django model sense
    (see http://tinyurl.com/84capd#abstract-base-classes); we want to
    support queries w/ this model class so that we can do cross-media-type
    queries w/o having to use joins.  However there should never be a
    true instance of this class, there should always be a child class
    associated w/ each instance.  The relative dotted path to this child
    class is stored in the 'child_attrpath' attribute when an instance is
    created, and the instance of this child class is reachable via the
    'get_child_instance' method."""
    title = models.CharField(_('title'), max_length=300)
    slug = models.SlugField(_('slug'), max_length=100, editable=False)
    caption = models.CharField(_('caption'), max_length=500, null=True)
    owner = models.ForeignKey(authmodels.User, null=True, editable=False)
    date_added = models.DateTimeField(_('date added'),
                                      default=datetime.now, editable=False)
    categories = models.ManyToManyField(Category)
    year = models.PositiveIntegerField(null=True)
    view_count = models.PositiveIntegerField(editable=False, default=0)
    status = models.CharField(_('status'), max_length=15, choices=statuses,
                              default='uploaded', editable=False)
    child_attrpath = models.CharField(_('child_attrpath'), max_length=50,
                                      editable=False)
    height = models.PositiveIntegerField(editable=False)
    width = models.PositiveIntegerField(editable=False)
    date_submitted = models.DateTimeField(_('date_submitted'), editable=False,
                                          null=True)
    date_approved = models.DateTimeField(_('date_approved'), editable=False,
                                         null=True)
    moderator = models.ForeignKey(authmodels.User, editable=False, null=True,
                                  related_name='mediabase_moderator_set')
    notes = models.TextField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super(MediaBase, self).__init__(*args, **kwargs)
        if self.__class__ is MediaBase:
            # XXX shouldn't happen, actually
            return
        child_attrpath = MediaBase.class_climber(self.__class__)
        if child_attrpath:
            self.child_attrpath = child_attrpath

    @classmethod
    def class_climber(cls, inst_cls):
        if cls in inst_cls.__bases__:
            return inst_cls.__name__.lower()
        else:
            for base in inst_cls.__bases__:
                attrpath = cls.class_climber(base)
                if attrpath:
                    return '%s.%s' % (attrpath, inst_cls.__name__.lower())

    def delete(self, *args, **kwargs):
        cursor = connection.cursor()
        cursor.execute('delete from gallery_searchable_text where mediabase_ptr_id=%i' % self.id)
        self.delete_file()
        super(MediaBase, self).delete()

    def get_child_instance(self):
        """Returns an instance of the appropriate model subclass for
        this instance."""
        child = self
        for attr in self.child_attrpath.split('.'):
            child = getattr(child, attr, child)
        return child

    def get_fname(self):
        return self.image.file.name

    @property
    def mediadir(self):
        """Makes explicit the contract that subclasses must provide
        a mediadir value."""
        raise NotImplementedError

    def get_absolute_url(self):
        """Retrieve 'mediadir' value from the child class instance.
        Subclasses must provide a 'mediadir' value somewhere in the
        inheritance chain or this will raise a NotImplementedError."""
        child = self.get_child_instance()
        return '/%s/%s/%s' % (child.mediadir, self.owner.username, self.slug)

    @property
    def thumbnail_image(self):
        """Makes explicit the contract that subclasses must provide
        a thumbnail_image value."""
        raise NotImplementedError

    def get_thumbnail_image(self):
        """Retrieve 'thumbnail_image' value from the child class
        instance.  Subclasses must provide this value somewhere in the
        inheritance chain or this will raise a NotImplementedError."""
        # bit of a hack; use a threadlocal to keep track of whether or
        # not we're recursing
        child = self.get_child_instance()
        return child.thumbnail_image

    def is_featured(self):
        """Returns True if this is the current 'featured' item, False
        otherwise."""
        featured = get_featured()
        if (featured is not None and
            featured.get_child_instance() == self):
            return True
        return False

    def _set_tags(self, tags):
        tagmodels.Tag.objects.update_tags(self, tags)
    def _get_tags(self):
        return tagmodels.Tag.objects.get_for_object(self)
    tags = property(_get_tags, _set_tags)

class FullImageAccessor(Accessor):
    """Custom accessor object that will only generate a scaled image
    if a flag is set on the image object."""
    def _create(self):
        if (not self._obj.full_image_available) or self._exists():
            return
        frompath = self._obj.image.path
        topath = self._obj._storage.path(self.name)
        shutil.copy(frompath, topath)

class ImageBase(ImageModel, MediaBase):
    """Base class for the BM Gallery image types"""
    image = models.ImageField(_('image'), upload_to=get_media_path,
                              storage=mediastorage, null=True)
    date_taken = models.DateTimeField(_('date taken'), null=True,
                                      blank=True, editable=False)
    full_image_available = models.BooleanField(default=False)
    textheight = models.PositiveIntegerField(editable=False)

    class IKOptions:
        spec_module = 'bm.gallery.specs'
        cache_dir = 'scaled'
        image_field = 'image'
        save_count_as = 'view_count'

    def __init__(self, *args, **kwargs):
        """Imagekit uses a metaclass to decorate the ImageModel
        instances with accessor objects.  The first time you try to
        retrieve a scaled image by referencing one of these accessor
        attributes, the accessor triggers the image processors to
        generate the processed image.

        Unfortunately, Imagekit doesn't support conditional
        processors; if you define an image spec, it will always be
        created.  To get around this we create our own custom accessor
        type which will only trigger the image processors if a flag is
        set, and we assign it in the constructor so that it overrides
        the default one provided by the metaclass during object
        instantiation."""
        full_image_accessor = FullImageAccessor(self, self.full_image.spec)
        self.full_image = full_image_accessor
        return super(ImageBase, self).__init__(*args, **kwargs)

    def delete_file(self):
        try:
            thumb = self.thumbnail_image
            if thumb and os.path.exists(thumb.file.name):
                fn = thumb.file.name
                log.debug('deleting: %s', fn)
                os.unlink(fn)
        except IOError:
            pass

        if os.path.exists(self.image.path):
            log.debug('deleting: %s', self.image.path)
            os.unlink(self.image.path)

class Photo(ImageBase):
    """Burning Man Photo Gallery photo object"""
    mediadir = 'photos'
    legacy_id = models.PositiveIntegerField(editable=False, null=True,
                                            db_index=True)
    in_press_gallery = models.BooleanField(default=False, db_index=True)
    batch = models.ForeignKey('Batch', related_name='photos', null=True)

    def __unicode__(self):
        return "Photo: %s/%s" % (self.owner.username, self.slug)

    @classmethod
    def mediatype(klass):
        return 'photo'

    @property
    def image_data(self):
        """Get raw image data"""
        return self.image.read()

    def resized(self, h=0, w=0, footer=True, extended=True, crop=False, upscale=False):
        """Get the image, resized and optionally watermarked"""
        fn = self.image.file.name
        suffix = ['_']
        if not w:
            suffix.append('0')
        else:
            suffix.append(str(w))
        suffix.append('x')
        if not h:
            suffix.append('0')
        else:
            suffix.append(str(h))

        if footer or extended:
            suffix.append('-')
            if footer:
                suffix.append('w')
            if extended:
                suffix.append('e')

        suffix = ''.join(suffix)
        fn = get_scaled_media_path(self, filename=fn, suffix=suffix)
        if os.path.exists(fn):
            img = Image.open(fn)
            log.debug('returning cached image: %s', fn)
        else:
            img = Image.open(self.image.file.name)
            cw, ch = img.size
            if h == 0 and w == 0:
                h = ch
                w = cw

            if h != ch or w != cw:
                img = resize_image(img, h, w, crop=crop, upscale=upscale)

            if footer or extended:
                img = add_watermark(img, footer=footer, extended=extended)

            img.save(fn)
            log.debug('Created and cached new image: %s', fn)

        return img, fn

class Artifact(ImageBase):
    """Burning Man Playa Artifact Gallery artifact object"""
    mediadir = 'artifacts'
    legacy_id = models.PositiveIntegerField(editable=False, null=True,
                                            db_index=True)
    batch = models.ForeignKey('Batch', related_name='artifacts', null=True)

    @classmethod
    def mediatype(klass):
        return 'artifact'

    def __unicode__(self):
        return "Artifact: %s/%s" % (self.owner.username, self.slug)


class Video(MediaBase):
    """Burning Man Video Gallery object"""
    filefield = models.FileField(_('filefield'), upload_to=get_media_path,
                                  storage=mediastorage)
    flvfile = models.FileField(_('flvfile'), null=True, blank=True,
                               upload_to=get_scaled_media_path,
                               storage=mediastorage)
    thumbnail = models.ImageField(blank=True, null=True,
                                  upload_to=get_scaled_media_path,
                                  storage=mediastorage)
    flvheight = models.PositiveIntegerField(editable=False, null=True)
    flvwidth = models.PositiveIntegerField(editable=False, null=True)
    # flag for whether or not video needs to be encoded
    encode = models.BooleanField(default=False)
    mediadir = 'videos'
    batch = models.ForeignKey('Batch', related_name='videos', null=True)

    @classmethod
    def mediatype(klass):
        return 'video'

    def __unicode__(self):
        return "Video: %s/%s" % (self.owner.username, self.slug)

    def delete_file(self):
        if os.path.exists(self.image.path):
            log.debug('deleting: %s', self.image.path)
            os.unlink(self.filefield.path)

        thumb = self.thumbnail_image
        if thumb and os.path.exists(thumb.file.name):
            fn = thumb.file.name
            log.debug('deleting: %s', fn)
            os.unlink(fn)

    def get_display_url(self):
        return self.filefield.url

    def get_fname(self):
        return self.filefield.file.name

    @property
    def thumbnail_image(self):
        return (self.thumbnail or None)


mediatype_map = dict(
    photo=dict(klass=Photo, title=_('Photo')),
    artifact=dict(klass=Artifact, title=_('Artifact')),
    video=dict(klass=Video, title=_('Video')),
    )

class FeaturedMedia(models.Model):
    media = models.ForeignKey(MediaBase, editable=False, null=False,
                              related_name='media')
    timestamp = models.DateTimeField(auto_now_add=True)

def get_featured():
    try:
        featured = FeaturedMedia.objects.all().order_by('-id')[0]
    except IndexError:
        return
    return featured.media

def get_pending_contributors():
    pending_contributors = authmodels.User.objects
    pending_contributors = pending_contributors.exclude(groups__name='galleries')
    return pending_contributors.order_by('id')

class Batch(models.Model):
    uuid = UUIDField(primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(authmodels.User)
    date_added = models.DateTimeField(_('date added'),
                                      default=datetime.now, editable=False)
    submitted = models.BooleanField('Submitted', default=False)

    def autoname(self):
        return "%s %s" % (self.date_added.strftime('%m-%d-%y %H:%M'), self.user.username)

    def delete(self, *args, **kwargs):
        for f in self.photos.all():
            f.delete()

        for f in self.videos.all():
            f.delete()

        super(Batch, self).delete(*args, **kwargs)

    def extract_archives(self):
        """Extracts all archives and delete the ArchiveFile objects"""
        for archive in self.archives.all():
            log.debug('extracting: %s', archive)
            archive.extract()
            archive.delete()

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.autoname()

        super(Batch, self).save(*args, **kwargs)

    def __unicode__(self):
        name = self.name
        if not name:
            name = self.autoname()
        return u"Batch: %s for %s" % (name, self.user.username)


class ArchiveFile(models.Model):
    owner = models.ForeignKey(authmodels.User)
    date_added = models.DateTimeField(_('date added'),
                                      default=datetime.now, editable=False)
    filefield = models.FileField(_('filefield'), upload_to=get_media_path,
                                 storage=mediastorage)
    batch = models.ForeignKey('Batch', related_name='archives', null=True)
    mediadir = 'archives'

    def __unicode__(self):
        return u"Archive: %s" % self.filefield.path

    def delete(self, *args, **kwargs):
        log.info('deleting %s', self.filefield.path)
        os.unlink(self.filefield.path)
        super(ArchiveFile, self).delete(*args, **kwargs)

    def extract(self):

        f, ext = self.filefield.path.rsplit('.',1)
        ext = ext.lower()
        files = []
        tdir = tempfile.mkdtemp()
        legal = ('gif','jpg','jpeg','png')
        if self.owner.has_perm('gallery.can_review'):
            legal += ('avi','mpg','mpeg','m1v','mp2','mpa','mpe','mpv2','asf','mov','qt', 'flv')

        tname = str(tdir)
        members = []
        membernames = []

        if ext == 'zip':
            log.debug('zipfile')
            log.debug('zipfile: %s', self.filefield.path)
            z = zipfile.ZipFile(self.filefield.path, 'r')
            for member in z.infolist():
                log.debug('checking: %s', member.filename)
                f, ext = member.filename.rsplit('.',1)
                ext = ext.lower()
                if ext in legal and not f.startswith('/'):
                    log.debug('adding: %s', member.filename)
                    members.append(member)
                    membernames.append(os.path.join(tname, member.filename))
                else:
                    log.debug('%s.%s not in %s', f, ext, legal)

            z.extractall(tname, members)

        if ext in ('tar','tar.gz','tgz','tbz','tar.bz'):
            log.debug('tarfile: %s', self.filefield.path)
            t = tarfile.open(self.filefield.path)
            for member in t.getmembers():
                f, ext = member.name.rsplit('.',1)
                ext = ext.lower()
                if ext in legal and not f.startswith('/'):
                    members.append(member)
                    membernames.append(os.path.join(tname, member.name))
                else:
                    log.debug('%s.%s not in %s', f, ext, legal)

            t.extractall(tname, members)

        log.debug('extracted: %s', membernames)

        for fn in membernames:
            infile = open(fn,'r')
            files.append(media_from_file(infile, self.batch, self.owner, True))
            infile.close()

        return files

def media_from_file(infile, batch, user, manual=False):
    """Creates an instance of correct Media class from an open file"""
    stream = InputIOStream(infile)
    parser = hachoir_parser.guessParser(stream)
    metadata = hachoir_metadata.extractMetadata(parser)
    model_class = klass_from_metadata(metadata, infile.name)

    if not model_class:
        # TODO: need to test different errors
        log.warn('no media found for: %s', infile.name)
        return None

    else:
        mediatype = model_class.mediatype()
        cursor = connection.cursor()
        cursor.execute("SELECT nextval ('gallery_mediabase_id_seq')")
        slugid = cursor.fetchone()[0]

        slug = '%s.%d' % (user.username, slugid)
        args = {'owner': user,
                'slug': slug,
                'status': 'infile',
                'textheight' : 50,
                'batch': batch}

        if not manual:
            if hasattr(model_class, 'IKOptions'):
                # we're some type of image object
                args['image'] = infile
            else:
                args['filefield'] = infile

        for dimension in ('width', 'height'):
            dimvalue = metadata.get(dimension, False)
            if dimvalue:
                args[dimension] = dimvalue
        if mediatype == 'video' and not infile.name.endswith('flv'):
            args['encode'] = True

        if metadata.has('creation_date'):
            year = metadata.get('creation_date', None)
            if year:
                year = year.year
                args['year'] = year

        instance = model_class(**args)
        if manual:
            fn = os.path.basename(infile.name)
            fileobj = File(infile)
            log.debug('manual creation of %s: %s', mediatype, fn)
            if hasattr(model_class, 'IKOptions'):
                # we're some type of image object
                instance.image.save(fn, fileobj)
            else:
                instance.filefield.save(fn, fileobj)

        instance.save()
        log.debug('Saved %s: %s' % (mediatype, instance.get_fname()))
        return instance


def klass_from_metadata(metadata, fname):
    """Returns the correct Media Class from the metadata"""
    mime = metadata.get('mime_type', None)
    if not mime:
        log.warn('Could not extract metadata for %s', fname)
        return None
    filetype = mime.split('/')[0]
    if not filetype:
        log.warn('Could not extract determine MIME type for %s', fname)
        return None

    if filetype == 'image':
        return Photo
    elif filetype == 'video':
        return Video
    else:
        return Artifact
