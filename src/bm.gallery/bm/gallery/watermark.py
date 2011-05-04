from PIL import ImageDraw, ImageFont
from imagekit.processors import ImageProcessor
from imagekit.lib import Image
from django.conf import settings
import os
import logging

log = logging.getLogger(__name__)

EXTRA_COPY = "\xa9 All images are copyright in their respective year, by both the photographer and Burning Man. For publication or other use requests, contact the photographer at the email provided and press@burningman.com for written permission."

class Watermark(ImageProcessor):
    @classmethod
    def process(cls, image, fmt, obj=None):
        """Adds a watermark to an image."""
        newimage = add_watermark(image, footer=False, extended=True)
        return newimage, fmt

def add_watermark(image, footer=True, extended=True):
    if image.mode != 'RGBA':
            image = image.convert('RGBA')

    pink = (255, 94, 200)
    white = (255, 255, 255)

    im_width, im_height = image.size
    log.debug('size: %s', image.size)
    if im_height:
        fontsize = int(im_height/34)
    else:
        fontsize = int(im_width/34)

    if fontsize > 16:
        fontsize = 16

    log.debug('font size=%i', fontsize)
    ttf = os.path.join(settings.MEDIA_ROOT, 'fonts', 'Tahoma.ttf')
    font = ImageFont.truetype(ttf, fontsize)

    overlay = Image.new('RGBA', image.size, (0,0,0,0))
    if footer:
        im_width, im_height = image.size
        copyright = "Copyright \xa9 by the Artist and Burning Man"

        draw = ImageDraw.Draw(overlay)
        draw.rectangle((0, im_height - fontsize - 6, im_width, im_height),
                       fill=(0,0,0,90))
        draw.text((10, im_height - fontsize - 4), copyright, fill=(255,255,255,90), font=font)


    if extended:
        newimage = Image.new('RGB', (im_width, im_height + 200), white)
        textheight = draw_word_wrap(newimage, EXTRA_COPY, 10, 5, max_width=im_width-10, fill=pink, font=font, height_only=True)
        h = im_height + textheight + 5
        log.debug('new height: %s, textheight=%s', h, textheight)
        newimage = Image.new('RGB', (im_width, h), white)
    else:
        newimage = Image.new('RGB', (im_width, im_height))

    if extended:
        #draw2 = ImageDraw.Draw(newimage)
        draw_word_wrap(newimage, EXTRA_COPY, 10, im_height + 5, max_width=im_width-10, fill=pink, font=font)

        # draw2.text((10, h),
        #            "\xa9 All images are copyright in their respective year, by "
        #            "both the ",
        #            fill=pink,
        #            font=font)
        # h += fontsize + 3
        # draw2.text((10, h),
        #            "photographer and Burning Man. For publication or other use ",
        #            fill=pink,
        #            font=font)
        # h += fontsize + 3
        # draw2.text((10, h),
        #            "requests, contact the photographer at the email provided and ",
        #            fill=pink,
        #            font=font)
        # h += fontsize + 3
        # draw2.text((10, h),
        #            "press@burningman.com for written permission.",
        #            fill=pink,
        #            font=font)

    comp = Image.composite(overlay, image, overlay)
    newimage.paste(comp, (0,0))
    return newimage


def draw_word_wrap(img, text, xpos=0, ypos=0, max_width=130,
                   fill=(0,0,0), font=None, height_only=False):
    '''Draw the given ``text`` to the x and y position of the image, using
    the minimum length word-wrapping algorithm to restrict the text to
    a pixel width of ``max_width.``
    '''
    if font is None:
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(img)
    text_size_x, text_size_y = draw.textsize(text, font=font)
    remaining = max_width
    space_width, space_height = draw.textsize(' ', font=font)
    # use this list as a stack, push/popping each line
    output_text = []
    # split on whitespace...
    for word in text.split(None):
        word_width, word_height = draw.textsize(word, font=font)
        if word_width + space_width > remaining:
            output_text.append(word)
            remaining = max_width - word_width
        else:
            if not output_text:
                output_text.append(word)
            else:
                output = output_text.pop()
                output += ' %s' % word
                output_text.append(output)
            remaining = remaining - (word_width + space_width)
    for text in output_text:
        if not height_only:
            draw.text((xpos, ypos), text, font=font, fill=fill)

        ypos += text_size_y

    return ypos

