from functools import wraps
from typing import Iterator
from PIL import Image, ImageDraw, ImageFont
from zju_fetcher.chalaoshi_fetcher import Teacher
from zju_fetcher.school_fetcher import Exam, Course
import os
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

# Font paths:
# Zpix, 最像素, (https://github.com/SolidZORO/zpix-pixel-font)
ZPIX = os.path.join(FONTS_PATH, 'zpix.ttf')
# Matisse Pro EB, EVA Style, Japanese Only
MATISSE_EB = os.path.join(FONTS_PATH, 'Matisse-Pro-EB.otf')
# Source Han Serif Heavy, Callback of MatisseEB. Copyright:Adobe
SERIF_HEAVY = os.path.join(FONTS_PATH, 'SourceHanSerifSC-Heavy.otf')


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


def draw_rounded_rectangle(image, pos: tuple[Pos, Pos] | tuple[float, float, float, float], fill=TRANSPARENT, r=0, border=False, border_color=TRANSPARENT, border_width=1):
    if isinstance(image, ImageDraw.ImageDraw):
        draw = image
    else:
        draw = ImageDraw.Draw(image)
        
    if isinstance(pos[0], (float, int)):
        x1, y1, x2, y2 = pos
    else:
        x1, y1, x2, y2 = pos[0].x, pos[0].y, pos[1].x, pos[1].y

    assert isinstance(x1, (int,float))
    assert isinstance(y1, (int,float))
    assert isinstance(x2, (int,float))
    assert isinstance(y2, (int,float))
    
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


def text_with_pos_updated(draw: ImageDraw.ImageDraw, pos: Pos, text, font=ZPIX, fontsize=12, color=(0, 0, 0)):
    txtlen = draw.textlength(text, font=ImageFont.truetype(font, fontsize))
    draw.text(astuple(pos), text, color,
              font=ImageFont.truetype(font, fontsize))
    pos.x += txtlen


def get_exam_card(exam: Exam, days_left='几', bg_color=WHITE, width=2000,height=400):
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


@registered_as("exam")
def get_exam_image(arg_dicts: list[dict]):
    CARD_HEIGHT = 400
    CARD_WIDTH = 1600
    CARD_GAP = 30
    height = (CARD_HEIGHT + CARD_GAP) * len(arg_dicts) + 130
    width = CARD_WIDTH + 100
    background = Image.new('RGBA', (width, height), BLACK)
    draw = ImageDraw.Draw(background)
    pos = Pos(0, 0)
    draw.text(astuple(pos), "試験、襲来", WHITE,
              font=ImageFont.truetype(MATISSE_EB, 126))
    pos = Pos(50, 126)
    for id, exam in enumerate(arg_dicts):
        card = get_exam_card(**exam, bg_color=SHALLOW_PURPLE if id&1 else RICE_WHITE, width=CARD_WIDTH, height=CARD_HEIGHT)
        background.paste(card, astuple(pos), card)  # with transparency
        pos.y += CARD_HEIGHT + CARD_GAP
    return background


if __name__ == '__main__':
    image = Image.new('RGBA', (1920, 1080), (192, 192, 192, 255))
    exam = Exam(code='(2922-2923-1)-114514', name='大学物理（戊）Ⅱ', term='冬', time_final='2923年13月33日(88:00-0:88)', location_final=None,
                seat_final=None, time_mid='2922年13月36日(25:00-28:00)', location_mid='白银港西2B-114(录播.6)', seat_mid='19', remark='推迟进行的线下期末考试', is_retake=None, credits='3.0')
    exams = [{'exam':exam,'days_left':114} for _ in range(6)]
    image = get_exam_image(exams)
    image.save('./tmp.png')
