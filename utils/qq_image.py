from copy import copy
from functools import lru_cache, wraps
from itertools import chain
from typing import Iterator
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from zju_fetcher.chalaoshi_fetcher import Teacher
from zju_fetcher.school_fetcher import Exam, Course
import os
import numpy as np
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, astuple
# TODO: Night/Day mode switch (time-wise)
FONTS_PATH = "./assets/fonts"
IMAGES_PATH = "./assets/images"

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


@dataclass
class Pos:
    x: int | float = 0
    y: int | float = 0


handlers = {}  # global handler registry


def registered_as(name):
    def wrapper(func):
        global handlers
        handlers[name] = func

        @wraps(func)
        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapped
    return wrapper


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


def draw_rounded_rectangle(image, pos: tuple[Pos, Pos] | tuple[float | int, float | int, float | int, float | int],
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


def text_with_pos_updated(draw: ImageDraw.ImageDraw, pos: Pos, text="", font=ZPIX,
                          fontsize=12, color=(0, 0, 0), is_right2left=False, language="zh-Hans"):
    """NOTE: pos will be directly changed
    """
    txtlen = draw.textlength(text, font=sized_font(
        font, fontsize), language=language)
    draw_pos = copy(pos)
    if is_right2left:
        draw_pos.x -= txtlen
    draw.text(astuple(draw_pos), text, color,
              font=sized_font(font, fontsize), language=language)
    pos.x += txtlen if not is_right2left else -txtlen


def multiline_text_with_pos_updated(draw: ImageDraw.ImageDraw, pos: Pos, text="", font=ZPIX,
                                    fontsize=12, color=(0, 0, 0), width=300, line_gap=0, seg_gap=0, language="zh-Hans"):
    # TODO: take kerning into consideration
    # TODO: avoid symbols appearing at the beginning of a line
    single_width = draw.textlength("ああ",
                                   font=sized_font(font, fontsize)) - draw.textlength("あ", font=sized_font(font, fontsize))
    max_per_line = max(int(width / single_width), 1)

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
                                  font, fontsize, color, language=language)
            pos.y += fontsize + line_gap
        pos.y += seg_gap - line_gap


def get_exam_card(exam: Exam, days_left='几', bg_color=WHITE, width=2000, height=400):
    image = Image.new('RGBA', (width, height), TRANSPARENT)
    d = ImageDraw.Draw(image)
    draw_rounded_rectangle(d, (0, 0, width, height), bg_color, 20, False)

    pos = Pos(50, 50)

    text_with_pos_updated(d, pos, exam.name, ZPIX, 54)
    pos.y += 20
    text_with_pos_updated(d, pos, f"/{exam.credits}", ZPIX, 36, GRAY)
    pos.y -= 20
    pos.x += 10

    text_with_pos_updated(d, pos, f"({days_left}天后)", SERIF_HEAVY, 36, ZJU_RED)

    # New Line
    pos = Pos(70, 150)

    if exam.time_final:
        text_with_pos_updated(d, pos, f"【期末】{exam.time_final}", MATISSE_EB, 36)
        if exam.location_final:
            text_with_pos_updated(
                d, pos, f"@{exam.location_final}", SERIF_HEAVY, 36)
        if exam.seat_final:
            text_with_pos_updated(
                d, pos, f"[No.{exam.seat_final}]", SERIF_HEAVY, 36)
        pos.y += 60

    # New Line
    pos.x = 70
    if exam.time_mid:
        text_with_pos_updated(d, pos, f"【期中】{exam.time_mid}", MATISSE_EB, 36)
        if exam.location_mid:
            text_with_pos_updated(
                d, pos, f"@{exam.location_mid}", SERIF_HEAVY, 36)
        if exam.seat_mid:
            text_with_pos_updated(
                d, pos, f"[No.{exam.seat_mid}]", SERIF_HEAVY, 36)
        pos.y += 70

    pos.x = 50
    if exam.remark:
        text_with_pos_updated(
            d, pos, f"⚠{exam.remark}", SERIF_HEAVY, 36, ZJU_BLUE)
    return image


def image_fit(image: Image.Image, size: tuple[int, int], mode="cover", filling=TRANSPARENT):
    """Like the property 'object-fit' in CSS
    mode:fill|contain|cover|scale-down|none|initial|inherit
    """
    if mode == "cover":
        ratio = max(size[0]/image.width, size[1]/image.height)
        new_width, new_height = int(image.width*ratio), int(image.height*ratio)
        new_img = image.resize((new_width, new_height))
    elif mode == "cotain":
        ratio = min(size[0]/image.width, size[1]/image.height)
        new_width, new_height = int(image.width*ratio), int(image.height*ratio)
        new_img = image.resize((new_width, new_height))
    else:
        raise ValueError("Invalid or unsupported mode")

    center_width, center_height = size[0]/2, size[1]/2
    canva = Image.new('RGBA', (size[0], size[1]), filling)
    canva.paste(new_img, (
        int(center_width-new_img.width / 2),
        int(center_height-new_img.height/2)))

    return canva


@registered_as("exam")
def _get_exam_image(exams: list[dict], last_update: Optional[float] = None):
    CARD_HEIGHT = 400
    CARD_WIDTH = 1600
    CARD_GAP = 30
    height = (CARD_HEIGHT + CARD_GAP) * len(exams) + 130
    width = CARD_WIDTH + 100
    background = Image.new('RGBA', (width, height), BLACK)
    draw = ImageDraw.Draw(background)
    pos = Pos(0, 0)
    text_with_pos_updated(draw, pos, "試験、襲来", MATISSE_EB,
                          126, color=WHITE, language="ja")
    pos_tmp = copy(pos)
    text_with_pos_updated(draw, pos, "仅供参考：请以教务网为准！" + "/" * 20,
                          SERIF_HEAVY, 56, color=ZJU_RED)
    pos = pos_tmp
    pos.y += 60
    if last_update:
        text_with_pos_updated(draw, pos, f"数据更新于:{datetime.fromtimestamp(last_update)}", SERIF_HEAVY, 40, color=ZJU_RED)
    pos = Pos(50, 126)
    for id, exam in enumerate(exams):
        card = get_exam_card(**exam, bg_color=SHALLOW_PURPLE if id &
                             1 else RICE_WHITE, width=CARD_WIDTH, height=CARD_HEIGHT)
        background.paste(card, astuple(pos), card)  # with transparency
        pos.y += CARD_HEIGHT + CARD_GAP
    return background


@registered_as("hanakotoba")
def _get_hanakotoba_image(image: str, kotobas: list[str], name="", desc=""):
    WIDTH, HEIGHT = 1920, 1080
    IMG_W, IMG_H = 1080, 1080
    GRAD_W = 512
    PADDING = 50
    CARD_H = 100
    GAP = 15

    bk_ground = Image.new('RGBA', (WIDTH, HEIGHT), SHALLOW_YELLOW)
    flower = Image.open(image).convert('RGBA')
    # Left-side flower image with gradient
    flower = image_fit(flower, (IMG_W, IMG_H))

    grad_array = get_gradient_3d(
        GRAD_W, flower.height, (255, ), (0, ), (True, ))
    grad_array = np.concatenate((np.full(
        shape=[flower.height, flower.width-GRAD_W], dtype=np.uint8, fill_value=255), grad_array[:, :, 0]), axis=1)
    grad = Image.fromarray(grad_array, 'L')

    flower.putalpha(grad)
    flower = flower.filter(ImageFilter.GaussianBlur(radius=5))

    bk_ground.paste(flower, (0, 0), flower)

    draw = ImageDraw.Draw(bk_ground)
    pos = Pos(IMG_W - 30, IMG_H - 140)
    text_with_pos_updated(draw, pos, name, MS_PMINCHO, 108, WHITE, True)

    text_w, text_h = WIDTH - IMG_W - 2 * PADDING, HEIGHT - 2 * PADDING
    pos = Pos(IMG_W + PADDING, PADDING)
    for kotoba in kotobas:
        draw_rounded_rectangle(
            draw, (pos.x, pos.y, pos.x+text_w+PADDING, pos.y+CARD_H), SHALLOW_RED)
        txt_pos = copy(pos)
        txt_pos.y += 14
        text_with_pos_updated(
            draw, txt_pos, f"「{kotoba}」", MS_PMINCHO, 72, BLACK, language='ja')
        pos.y += CARD_H + GAP

    pos.y += 2*GAP
    multiline_text_with_pos_updated(draw, copy(
        pos), desc, MATISSE_EB, 30, BLACK, text_w, language='ja', line_gap=8, seg_gap=24)
    return bk_ground


if __name__ == '__main__':
    image = Image.new('RGBA', (1920, 1080), BLACK)
    exam = Exam(code='(2922-2923-1)-114514', name='大学物理（戊）Ⅱ', term='冬', time_final='2923年13月33日(88:00-0:88)', location_final=None,
                seat_final=None, time_mid='2922年13月36日(25:00-28:00)', location_mid='白银港西2B-114(录播.6)', seat_mid='19', remark='推迟进行的线下期末考试', is_retake=None, credits='3.0')
    exams = [{'exam': exam, 'days_left': 114} for _ in range(6)]
    image = _get_exam_image(exams)
#     image = _get_hanakotoba_image("/root/ybot/plugins/hanakotoba/images/hana_16.jpg", ['努力', '未来', 'A Beautiful Star'], "アイウエオ",
#                                   """誕生日1/21の花
# 別名：ヘデラ、セイヨウキヅタ
# 科名：ウコギ科
#   花言葉は、アイビーが他の樹木、岩、石垣などにしっかりつかまって成長することから。 とても丈夫な植物で、日向でも日陰でも育つ。日本の環境では適さない条件はほぼ無い程に育てることは容易。
#   ◎広がりすぎないように管理することが育てる上で重要なポイントです。アイビーの品種はなんと１０００種以上もあります。""")
    image.save('./tmp.png')
