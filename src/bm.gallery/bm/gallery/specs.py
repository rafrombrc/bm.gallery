from bm.gallery.watermark import Watermark
from django.conf import settings
from imagekit.specs import ImageSpec
from imagekit import processors

# first we define our thumbnail resize processor
class ResizeThumb(processors.Resize):
    width = 96
    height = 128
    crop = True

# now we define a display size resize processor
class ResizeDisplay(processors.Resize):
    width = 400
    height = 400

# now lets create an adjustment processor to enhance the image at small sizes
class EnhanceThumb(processors.Adjustment):
    contrast = 1.2
    sharpness = 1.1

# now we can define our thumbnail spec
class Thumbnail(ImageSpec):
    access_as = 'thumbnail_image'
    pre_cache = True
    processors = [ResizeThumb, EnhanceThumb]

# watermark processor
class DisplayWatermark(Watermark):
    image_path = '%swatermark.png' % settings.MEDIA_ROOT
    offset = '0x0'
    looks_best = '357x350'

# and our display spec
class Display(ImageSpec):
    increment_count = True
    processors = [ResizeDisplay, DisplayWatermark]

# full size spec
class Full(ImageSpec):
    access_as = 'full_image'
    pre_cache = True
    # this spec doesn't need any processors, b/c it's attached to a
    # special accessor which manually copies the image file

