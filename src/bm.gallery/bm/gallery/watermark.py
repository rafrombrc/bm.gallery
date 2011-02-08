from PIL import ImageDraw
from imagekit.processors import ImageProcessor
from imagekit.lib import Image


class Watermark(ImageProcessor):
    @classmethod
    def process(cls, image, fmt, obj=None):
        """Adds a watermark to an image."""
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        im_width, im_height = image.size
        copyright = "Copyright \xa9 by the Artist and Burning Man"

        overlay = Image.new('RGBA', image.size, (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        draw.rectangle((0, im_height - 20, im_width, im_height),
                       fill=(0,0,0,90))
        draw.text((10, im_height - 15), copyright, fill=(255,255,255,90))
        newimage = Image.new('RGB', (im_width, im_height))

        comp = Image.composite(overlay, image, overlay)
        newimage.paste(comp, (0,0))
        return newimage, fmt
