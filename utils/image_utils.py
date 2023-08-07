from copy import copy
from functools import lru_cache
from io import BytesIO
import random
import string
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import numpy as np
from dataclasses import dataclass, astuple

import requests

FONTS_PATH = os.path.join(".", "assets", "fonts")
IMAGES_PATH = os.path.join(".", "assets", "images")
LEGEND_AVATARS_PATH = os.path.join(IMAGES_PATH, "legends")
RANK_LOGOS_PATH = os.path.join(IMAGES_PATH, "ranks")

# Colors (RGBA):
TRANSPARENT = (255, 255, 255, 0)
ZJU_BLUE = (0, 63, 136, 255)
ZJU_RED = (176, 31, 36, 255)
XLAB_BLUE_DEEP = (0, 113, 239, 255)
XLAB_BLUE_LIGHT = (20, 155, 255, 255)
XLAB_GREEN_DEEP = (67, 197, 172, 255)
XLAB_GREEN_LIGHT = (138, 212, 194, 255)
WHITE = (255, 255, 255, 255)
GRAY = (191, 191, 191, 255)
DEEP_GRAY = (63, 63, 63, 255)
BLACK = (0, 0, 0, 255)
RICE_WHITE = (254, 253, 248, 255)
SHALLOW_PURPLE = (248, 247, 251, 255)
SHALLOW_YELLOW = (250, 244, 224, 255)
SHALLOW_RED = (255, 235, 229, 255)

# Font paths:
# Zpix, 最像素, (https://github.com/SolidZORO/zpix-pixel-font)
ZPIX = os.path.join(FONTS_PATH, 'zpix.ttf')
# Matisse Pro EB, EVA Style, Japanese Only
MATISSE_EB = os.path.join(FONTS_PATH, 'Matisse-Pro-EB.otf')
# Source Han Serif Heavy, Callback of MatisseEB. Copyright:Adobe
SERIF_HEAVY = os.path.join(FONTS_PATH, 'SourceHanSerifSC-Heavy.otf')
# MS P Mincho
MS_PMINCHO = os.path.join(FONTS_PATH, 'MS-PMincho.ttf')
# Bank Sans EF CY Semi-Condensed Regular Oblique
BANK_SANS_EF_SCRO = os.path.join(FONTS_PATH, 'Bank-Sans-EF-SCRO.otf')
BANK_SANS_EF_SC_REGULAR = os.path.join(
    FONTS_PATH, 'Bank-Sans-EF-SC-Regular.otf')

@dataclass
class Pos:
    x: int | float = 0
    y: int | float = 0

def fetch_image(name: str, path_template: str, remote_template: str, type: str = "Unknown"):
    """If not found, try to fetch from the remote website."""
    local_image_path = path_template.format(name)
    if os.path.exists(local_image_path):
        return Image.open(local_image_path).convert('RGBA')
    try:
        image_url = remote_template.format(name)
        response = requests.get(image_url)
        image_avatar = Image.open(BytesIO(response.content))
        image_avatar.save(local_image_path)
    except Exception as e:
        print(f"WARN: error occured when fetching {type} of '{name}': ")
        print(e)
        return Image.new('RGBA', (0,0))
    
    return Image.open(local_image_path).convert('RGBA')

def get_legend_avatar(name: str):
    name = name.lower()
    local_image_tplt = os.path.join(LEGEND_AVATARS_PATH, "{}.png")
    image_url = "https://apexlegendsstatus.com/assets/legends-select/{}.png"
    return fetch_image(name, local_image_tplt, image_url, type = "legend avatar")

def get_rank_logo(name: str):
    name = name.lower()
    local_image_tplt = os.path.join(RANK_LOGOS_PATH, "{}.png")
    image_tplt = "https://api.mozambiquehe.re/assets/ranks/{}.png"
    
    return fetch_image(name, local_image_tplt, image_tplt, type = "rank logo")

    
def get_gradient_2d(start, stop, width, height, is_horizontal=True):
    """get gradient 2d grayscale image.
    Source: https://note.nkmk.me/en/python-numpy-generate-gradation-image/
    """
    if is_horizontal:
        return np.tile(np.linspace(start, stop, width), (height, 1))
    else:
        return np.tile(np.linspace(start, stop, height), (width, 1)).T


def get_gradient_3d(width, height, start_list, stop_list, is_horizontal_list):
    result = np.zeros((height, width, len(start_list)), dtype=np.uint8)

    for i, (start, stop, is_horizontal) in enumerate(zip(start_list, stop_list, is_horizontal_list)):
        result[:, :, i] = get_gradient_2d(
            start, stop, width, height, is_horizontal)

    return result


def draw_rounded_rectangle(image: Image.Image | ImageDraw.ImageDraw, pos: tuple[Pos, Pos] | tuple[float | int, float | int, float | int, float | int],
                           fill=TRANSPARENT, r: int | float = 0, border=False, border_color=TRANSPARENT,
                           border_width=1):
    """pos can be (x1,y1,x2,y2) or (Pos(x1,y1),Pos(x2,y2))"""
    draw = image if isinstance(
        image, ImageDraw.ImageDraw) else ImageDraw.Draw(image)

    if isinstance(pos[0], (float, int)):
        x1, y1, x2, y2 = pos
    else:
        x1, y1, x2, y2 = pos[0].x, pos[0].y, pos[1].x, pos[1].y

    assert isinstance(x1, (int, float))
    assert isinstance(y1, (int, float))
    assert isinstance(x2, (int, float))
    assert isinstance(y2, (int, float))

    draw.ellipse((x1, y1, x1+2*r, y1+2*r), fill=fill)
    draw.ellipse((x2-2*r, y1, x2, y1+2*r), fill=fill)
    draw.ellipse((x1, y2-2*r, x1+2*r, y2), fill=fill)
    draw.ellipse((x2-2*r, y2-2*r, x2, y2), fill=fill)
    draw.rectangle((x1+r, y1, x2-r, y2), fill=fill)
    draw.rectangle((x1, y1+r, x2, y2-r), fill=fill)
    if border:
        draw.arc((x1, y1, x1+2*r, y1+2*r), 180,
                 270, border_color, border_width)
        draw.arc((x2-2*r, y1, x2, y1+2*r), 270,
                 360, border_color, border_width)
        draw.arc((x1, y2-2*r, x1+2*r, y2), 90,
                 180, border_color, border_width)
        draw.arc((x2-2*r, y2-2*r, x2, y2), 0,
                 90, border_color, border_width)
        draw.line((x1, y1+r, x1, y2-r), border_color, border_width)
        draw.line((x2, y1+r, x2, y2-r), border_color, border_width)
        draw.line((x1+r, y1, x2-r, y1), border_color, border_width)
        draw.line((x1+r, y2, x2-r, y2), border_color, border_width)


@lru_cache
def sized_font(font=ZPIX, fontsize=24):
    return ImageFont.truetype(font, fontsize)


def text_with_pos_updated(draw: ImageDraw.ImageDraw, pos: Pos, text: str = "", font=ZPIX,
                          fontsize=12, color=(0, 0, 0),
                          is_right2left=False,
                          is_horaligned=False,
                          language="zh-Hans"):
    """NOTE: pos will be directly changed
    if aligned, then the pos provided is considered to be centralized, and will NOT updated
    """
    txtlen = draw.textlength(text, font=sized_font(
        font, fontsize), language=language)
    draw_pos = copy(pos)
    if is_right2left:
        draw_pos.x -= txtlen
    elif is_horaligned:
        draw_pos.x -= txtlen/2

    draw.text(astuple(draw_pos), text, color,
              font=sized_font(font, fontsize), language=language)

    # Correct the cursor bias introduced by painting
    if not is_horaligned:
        pos.x += txtlen if not is_right2left else -txtlen


def multiline_text_with_pos_updated(draw: ImageDraw.ImageDraw, pos: Pos, text="", font=ZPIX,
                                    fontsize=12, color=(0, 0, 0), width=300, line_gap=0, seg_gap=0, language="zh-Hans", is_right2left=False):
    # TODO: take kerning into consideration
    # TODO: avoid symbols appearing at the beginning of a line
    single_width = draw.textlength("ああ",
                                   font=sized_font(font, fontsize)) - draw.textlength("あ", font=sized_font(font, fontsize))
    max_per_line = max(int(width // single_width), 1)

    def splitn(s, n):
        for i in range(0, len(s), n):
            yield s[i:i+n]
    text = text.split("\n")
    text = [splitn(s, max_per_line) for s in text]
    # print(max_per_line, list(text))
    for segment in text:
        for line in segment:
            draw_pos = copy(pos)
            text_with_pos_updated(draw, draw_pos, line,
                                  font, fontsize, color, language=language, is_right2left=is_right2left)
            pos.y += fontsize + line_gap
        pos.y += seg_gap - line_gap


def image_fit(image: Image.Image, size: tuple[int, int], mode="cover", filling=TRANSPARENT):
    """Like the property 'object-fit' in CSS
    mode:fill|contain|cover|scale-down|none|initial|inherit
    """
    if mode == "cover":
        ratio = max(size[0]/image.width, size[1]/image.height)
        new_width, new_height = int(image.width*ratio), int(image.height*ratio)
        new_img = image.resize((new_width, new_height))
    elif mode == "contain":
        ratio = min(size[0]/image.width, size[1]/image.height)
        new_width, new_height = int(image.width*ratio), int(image.height*ratio)
        new_img = image.resize((new_width, new_height))
    else:
        raise ValueError(f"Invalid or unsupported mode {mode}.")

    center_width, center_height = size[0]/2, size[1]/2
    canva = Image.new('RGBA', (size[0], size[1]), filling)
    canva.paste(new_img, (
        int(center_width-new_img.width / 2),
        int(center_height-new_img.height/2)))

    return canva


def get_circle_mask(size: tuple[int, int], blur_radius: int = 0) -> Image.Image:
    bigsize = (size[0] * 3, size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(size, Image.LANCZOS)  # High quality
    return mask if not blur_radius else mask.filter(ImageFilter.GaussianBlur(blur_radius))

def random_str(length):
    """Generate random a string consists with a-zA-z0-9 with a given length"""
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))