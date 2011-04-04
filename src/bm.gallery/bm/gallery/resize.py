from imagekit.lib import Image

def resize_image(img, h=0, w=0, crop=False, upscale=False):
    """Resize an image to h, w"""
    cur_width, cur_height = img.size
    if crop:
        crop_horz = 1
        crop_vert = 1
        if (w == 0 and h == 0) or (w is None and h is None):
            return img

        if w == 0:
            ratio = float(h)/cur_height
        elif h == 0:
            ratio = float(w)/cur_height
        else:
            ratio = max(float(w)/cur_width, float(h)/cur_height)

        resize_x, resize_y = ((cur_width * ratio), (cur_height * ratio))
        crop_x, crop_y = (abs(w - resize_x), abs(h - resize_y))
        x_diff, y_diff = (int(crop_x / 2), int(crop_y / 2))
        box_left, box_right = {
            0: (0, w),
            1: (int(x_diff), int(x_diff + w)),
            2: (int(crop_x), int(resize_x)),
        }[crop_horz]
        box_upper, box_lower = {
            0: (0, h),
            1: (int(y_diff), int(y_diff + h)),
            2: (int(crop_y), int(resize_y)),
        }[crop_vert]
        box = (box_left, box_upper, box_right, box_lower)
        img = img.resize((int(resize_x), int(resize_y)), Image.ANTIALIAS).crop(box)
    else:
        if (w is not None and not h is not None) and (w!= 0 and h != 0):
            ratio = min(float(w)/cur_width,
                        float(h)/cur_height)
        else:
            if w is None or w == 0:
                ratio = float(h)/cur_height
            else:
                ratio = float(w)/cur_width
        new_dimensions = (int(round(cur_width*ratio)),
                          int(round(cur_height*ratio)))
        if new_dimensions[0] > cur_width or \
           new_dimensions[1] > cur_height:
            if not upscale:
                return img
        img = img.resize(new_dimensions, Image.ANTIALIAS)
    return img

