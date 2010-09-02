from __future__ import absolute_import
from datetime import datetime
from django.conf import settings
from django.contrib.auth import models as authmodels
from django.core.files.storage import FileSystemStorage
from django.core.validators import email_re
from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _
from imagekit.models import ImageModel
from imagekit.specs import Accessor
from tagging import models as tagmodels
import os
import shutil

def get_media_path(instance, filename=''):
    return os.path.join(instance.mediadir, instance.owner.username, filename)

def get_scaled_media_path(instance, filename=''):
    return os.path.join('scaled', get_media_path(instance, filename))

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

    def get_child_instance(self):
        """Returns an instance of the appropriate model subclass for
        this instance."""
        child = self
        for attr in self.child_attrpath.split('.'):
            child = getattr(child, attr, child)
        return child

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

class Photo(ImageBase):
    """Burning Man Photo Gallery photo object"""
    mediadir = 'photos'
    legacy_id = models.PositiveIntegerField(editable=False, null=True,
                                            db_index=True)
    in_press_gallery = models.BooleanField(default=False, db_index=True)
    
    def __unicode__(self):
        return "Photo: %s/%s" % (self.owner.username, self.slug)


class Artifact(ImageBase):
    """Burning Man Playa Artifact Gallery artifact object"""
    mediadir = 'artifacts'
    legacy_id = models.PositiveIntegerField(editable=False, null=True,
                                            db_index=True)

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

    def __unicode__(self):
        return "Video: %s/%s" % (self.owner.username, self.slug)

    def get_display_url(self):
        return self.filefield.url

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
