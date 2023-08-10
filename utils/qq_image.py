from copy import copy
from math import ceil
import matplotlib.pyplot as plt
from functools import lru_cache, wraps
from io import BytesIO
import io
import re
import time
from PIL import Image, ImageDraw
import requests
from zju_fetcher.chalaoshi_fetcher import Teacher
from zju_fetcher.school_fetcher import Exam, Course
import os
import numpy as np
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, astuple
from colour import Color
# TODO: Night/Day mode switch (time-wise)

from .image_utils import * # Oh, forgive me

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

# Image Generators 
@registered_as("exam")
def _get_exam_image(exams: list[dict], last_update: Optional[float] = None):

    def get_exam_card(exam: Exam, days_left='?', bg_color=WHITE, width=2000, height=400) -> Image.Image:
        image = Image.new('RGBA', (width, height), TRANSPARENT)
        d = ImageDraw.Draw(image)
        draw_rounded_rectangle(d, (0, 0, width, height), bg_color, 20, False)

        pos = Pos(50, 50)

        text_with_pos_updated(d, pos, exam.name if exam.name else "", ZPIX, 54)
        pos.y += 20
        text_with_pos_updated(d, pos, f"/{exam.credits}", ZPIX, 36, GRAY)
        pos.y -= 20
        pos.x += 10

        text_with_pos_updated(
            d, pos, f"({days_left}天后)", SERIF_HEAVY, 36, ZJU_RED)

        # New Line
        pos = Pos(70, 150)

        if exam.time_final:
            text_with_pos_updated(
                d, pos, f"【期末】{exam.time_final}", MATISSE_EB, 36)
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
            text_with_pos_updated(
                d, pos, f"【期中】{exam.time_mid}", MATISSE_EB, 36)
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
        text_with_pos_updated(
            draw, pos, f"数据更新于:{datetime.fromtimestamp(last_update)}", SERIF_HEAVY, 40, color=ZJU_RED)
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
    grad = Image.fromarray(grad_array, mode='L')

    flower.putalpha(grad)
    # flower = flower.filter(ImageFilter.GaussianBlur(radius=5))

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

# TODO: move these APEX_*  constants to a seperated config file
APEX_RANKS = ["Rookie", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Master", "Apex Predator"]
APEX_LEGENDS = ["Bangalore","Bloodhound","Lifeline","Caustic","Gibraltar","Mirage","Pathfinder","Wraith","Octane","Wattson","Crypto","Revenant","Loba","Rampart","Horizon","Fuse","Valkyrie","Seer","Ash","Mad Maggie","Newcastle","Vantage","Catalyst","Ballistic"]
APEX_DIVSCORE = [0, 4000, 8000, 12000, 16000, 20000, 24000]
APEX_COLORS = ["#484852", "#CD7F32", "#C0C0C0",
               "#FFD700", "#B1F4FA", "#358DE6", "#9F35E6", "#E31B39"]

def plot_progress(rank_scores, height_to_width_ratio):
    """Example:  
    rank_scores = [85, 900, 4920, 11095, 10008, 20008, 24091, 30094, 97, 99]  
    height_to_width_ratio = 0.5  
    output_filename = "custom_plot.png"  
    """
    # Determine plot y-axis range
    MAX_Y = max(36000, ceil(max(rank_scores)/1000) * 1000)
    MIN_Y = 0
    
    total_games = list(range(1, len(rank_scores) + 1))
    
    # Calculate the figure width based on the desired height-to-width ratio
    fig_width = 10
    fig_height = fig_width * height_to_width_ratio

    # Create a figure and axes with the custom size
    fig, ax1 = plt.subplots(figsize=(fig_width, fig_height), linewidth=2)

    # Plot the line chart with circle markers
    ax1.plot(total_games, rank_scores, marker='o',
             linestyle='-', color='#1090FF', linewidth=2)

    ## Set background colors on the y-axis with gradient
    # < Master
    for i in range(len(APEX_DIVSCORE) - 1):
        ax1.axhspan(APEX_DIVSCORE[i], APEX_DIVSCORE[i+1],
                    facecolor=APEX_COLORS[i], alpha=0.3)

    # Master and Predators
    red = Color(APEX_COLORS[-2])
    colors = list(red.range_to(Color(APEX_COLORS[-1]), 100))
    HEIGHT = MAX_Y - APEX_DIVSCORE[-1]
    for i, color in enumerate(colors):
        ax1.axhspan(APEX_DIVSCORE[-1] + i*(HEIGHT/100), APEX_DIVSCORE[-1] +
                    (i+1)*(HEIGHT/100), facecolor=color.get_rgb(), alpha=0.3)

    ax1.set_ylim(MIN_Y, MAX_Y)
    ax1.yaxis.set_ticks_position('right')
    ax1.xaxis.set_ticks_position('bottom')
    ax1.set_xlabel('Ranked Played')
    ax1.set_ylabel('Rank Score')
    
    # Set transparent background
    fig.patch.set_alpha(0.0)

    # Set thicker frame borders with the same width
    ax1.spines['top'].set_linewidth(2)
    ax1.spines['bottom'].set_linewidth(2)
    ax1.spines['left'].set_linewidth(2)
    ax1.spines['right'].set_linewidth(2)

    # Set ticks towards the inside
    ax1.tick_params(axis='y', direction='in')
    ax1.tick_params(axis='x', direction='in')

    # Save the plot as a temporary image file
    # plt.savefig(output_filename, transparent=True)
    def fig2img(fig):
        """Convert a Matplotlib figure to a PIL Image and return it"""
        buf = io.BytesIO()
        fig.savefig(buf)
        buf.seek(0)
        img = Image.open(buf)
        return img
    
    img = fig2img(fig)
    
    return img

def get_foreground(info: dict, desc:str, legends: list|None = None, scores: list|None = None, width=1920, height=1080):
    """Generate foreground(info layer) of the card.
    `info` format is determined by this API: https://apexlegendsapi.com/#query-by-uid
    """
    if (not info) or (not info.get("global")) or (info.get("Error")):  # Invalid info object structure
        return None
    
    MAX_SIZE = 108
    HUGE_SIZE = 72
    MID_SIZE = 56
    TINY_SIZE = 48
    MIN_SIZE = 36
    
    STD_GAP = 20

    image = Image.new('RGBA', (width, height), TRANSPARENT)
    d = ImageDraw.Draw(image)

    
    ### Part: Rank Infos
    RANK_IMG_POS = Pos(80, 320)
    RANK_IMG_SIZE = (500, 470)
    rank = info["global"]["rank"]
    rank_name: str = rank["rankName"]
    rank_score: int = int(rank["rankScore"])
    rank_stop_percent: float = rank["ALStopPercent"]
    cursor = copy(RANK_IMG_POS)
    
    # Draw rank logo
    rank_logo_name = re.search(r"\/([^\/]+)\.png$", rank["rankImg"]).group(1)
    rank_img = get_rank_logo(rank_logo_name)
    rank_img = image_fit(rank_img.convert("RGBA"), RANK_IMG_SIZE, "contain")
    image.paste(rank_img, astuple(RANK_IMG_POS), rank_img)
    
    # Moved to bottom mid point of the logo
    cursor.y += RANK_IMG_SIZE[1]  
    cursor.x += RANK_IMG_SIZE[0]/2
    BOTTOM_CENTER_CURSOR = copy(cursor)
    
    # Rank Name
    text_with_pos_updated(d, cursor, rank_name, font = BANK_SANS_EF_SCRO, fontsize = HUGE_SIZE, is_horaligned=True, color = BLACK)
    # LP
    cursor.y += HUGE_SIZE + STD_GAP
    text_with_pos_updated(d, cursor, f"{rank_score} LP", font = BANK_SANS_EF_SC_REGULAR, fontsize = MID_SIZE, is_horaligned=True, color = BLACK)
    is_master_or_pred = lambda rank_name: rank_name == APEX_RANKS[-1] or rank_name == APEX_RANKS[-2]
    # Top Stop Percent
    # if not is_master_or_pred(rank_name):
    cursor.y += MID_SIZE + STD_GAP
    text_with_pos_updated(d, cursor, f"Top {rank_stop_percent}%", font = BANK_SANS_EF_SC_REGULAR, fontsize = MIN_SIZE, is_horaligned=True, color=ZJU_BLUE)
    cursor.y += MIN_SIZE
    text_with_pos_updated(d, cursor, f"(At the moment of the last game)", font = BANK_SANS_EF_SC_REGULAR, fontsize = MIN_SIZE, is_horaligned=True, color=GRAY)
    # Top Stop Integer (ranking), only for masters and predators
    if is_master_or_pred(rank_name):
        stop_cursor = copy(BOTTOM_CENTER_CURSOR)
        stop_cursor.y -= 85
        rank_pos = rank.get("ladderPosPlatform")
        if rank_pos and int(rank_pos) != -1:
            text_with_pos_updated(d, stop_cursor, f"#{rank_pos}", font = BANK_SANS_EF_SC_REGULAR, fontsize = MIN_SIZE, is_horaligned=True, color=WHITE)

    def sec2str_suffix(secs: int|None):
        """Optional suffix for state duration description"""
        if secs is None:
            return ""
        return f" - ({secs//60:02d}m:{secs%60:02d}s)"
        
    def status_text_and_color(is_online: bool, current_state: str, state_duration: None|int = None) -> tuple[str,tuple[int,int,int,int]]:
        # current state: inLobby, inMatch, offline
        # Regularization
        is_online = bool(is_online)
        current_state = str(current_state)
        
        if not is_online or "offline" in current_state.lower():
            return ("Offline",(0xb3, 0x38, 0x34, 255))
        if "match" in current_state.lower():
            return (f"In Match{sec2str_suffix(state_duration)}",(0xe5, 0x88, 0x26, 255))
        if "lobby" in current_state.lower():
            return (f"In Lobby{sec2str_suffix(state_duration)}",(0x4d, 0x86, 0x10, 255))
        return ("???",BLACK)
    
    ### Part: Player Info
    # Status/Realtime Info
    realtime = info["realtime"]
    cursor = Pos(100, 50)
    text, color = status_text_and_color(realtime.get("isOnline"), realtime.get("currentState"), realtime.get("currentStateSecsAgo"))
    text_with_pos_updated(d, cursor, text, font = SERIF_HEAVY, fontsize = MID_SIZE, color=color)
    
    # Name and Level
    player_name = info["global"]["name"]
    player_level = int(info["global"]["level"]) + 500 * int(info["global"]["levelPrestige"]) # 1 prestige = 500 levels
    cursor = Pos(100, 50 + MID_SIZE + STD_GAP)
    text_with_pos_updated(d, cursor, player_name, font = SERIF_HEAVY, fontsize = HUGE_SIZE, color=BLACK)
    cursor.x += STD_GAP
    BAR_CURSOR = copy(cursor) # reserve for progress bar
    text_with_pos_updated(d, cursor, f"Lv. {player_level}", font = BANK_SANS_EF_SCRO, fontsize = HUGE_SIZE, color=ZJU_BLUE)
    
    # Level Progress Bar
    cursor = BAR_CURSOR
    cursor.y += 3.5 * STD_GAP
    LEVEL_BAR_W = 300
    LEVEL_BAR_H = 20
    progress_percent = info["global"]["toNextLevelPercent"]
    draw_rounded_rectangle(d, (cursor, Pos(cursor.x+LEVEL_BAR_W, cursor.y+LEVEL_BAR_H)), DEEP_GRAY)
    draw_rounded_rectangle(d, (cursor, Pos(cursor.x+LEVEL_BAR_W * (progress_percent / 100), cursor.y+LEVEL_BAR_H)), XLAB_GREEN_DEEP)
    
    ### Part: Progress Graph
    # Patch
    if not scores:
        scores = [rank_score]
    
    if scores[-1]!=rank_score:
        scores.append(rank_score)
    # Graph Title
    TITLE_POS = Pos(640, 270)
    cursor = copy(TITLE_POS)
    text_with_pos_updated(d, cursor, "Rank Progress", font = BANK_SANS_EF_SC_REGULAR, fontsize = TINY_SIZE, color=BLACK)
    cursor = Pos(500, 250)
    PROGRESS_W = 1450
    PROGRESS_H = 650
    progress = plot_progress(scores, PROGRESS_H/PROGRESS_W).convert("RGBA")
    progress = image_fit(progress, (PROGRESS_W, PROGRESS_H), mode = "cover")
    image.paste(progress, astuple(cursor) + (cursor.x + PROGRESS_W, cursor.y + PROGRESS_H), mask=progress)
    # draw_rounded_rectangle(d, (cursor, Pos(cursor.x+PROGRESS_W, cursor.y+PROGRESS_H)), 
    #                        fill = TRANSPARENT, 
    #                        r=0, 
    #                        border=True,
    #                        border_width=5,
    #                        border_color=BLACK
    #                     )
    
    ### Part: Most Played Legends
    # Prompt "Most Played Legends"
    cursor = Pos(670, 900)
    LEGENDS_CURSOR = copy(cursor)
    cursor.y += 2 * STD_GAP
    multiline_text_with_pos_updated(d, cursor, "Season\nMost-Played\nLengeds", font = BANK_SANS_EF_SC_REGULAR, fontsize = MIN_SIZE, color=BLACK)
    # Legend Avatar & Times Played
    def draw_legend_compose(pos: Pos, radius: int, raw_avatar: Image.Image, frame_color = GRAY):
        """`pos` = Upper Left Position"""
        cutted_avatar = image_fit(raw_avatar, (radius * 2,radius * 2), mode="cover")
        mask = get_circle_mask(cutted_avatar.size)
        # Avatar Frame
        FRAME_SIZE = (2*radius, 2*radius)
        bigsize = (FRAME_SIZE[0] * 3, FRAME_SIZE[1] * 3)
        frame = Image.new('RGBA', bigsize, TRANSPARENT)
        ImageDraw.Draw(frame).ellipse((0, 0) + bigsize, fill=TRANSPARENT, outline = frame_color, width = 10)
        frame = frame.resize(FRAME_SIZE, Image.LANCZOS)  # High quality
        image.paste(cutted_avatar, astuple(pos), mask)
        # frame.save("./frame.png")
        image.paste(frame, astuple(pos), frame)
    
    cursor = copy(LEGENDS_CURSOR)
    cursor.x += 70
    
    if not legends:
        legends = []
        
    for legend in legends:
        cursor.x += 180
        draw_legend_compose(cursor, 80, get_legend_avatar(legend), frame_color=ZJU_BLUE)
    
    ### Part: Descriptive Infos (Upper Right)
    cursor = Pos(width - 2 * STD_GAP, STD_GAP)
    multiline_text_with_pos_updated(d, cursor, desc, width = 500, font = SERIF_HEAVY, fontsize = TINY_SIZE, color=BLACK, is_right2left=True)
    
    ### Part: WaterMark
    cursor = Pos(width - STD_GAP, height - STD_GAP - 2 * MIN_SIZE)
    multiline_text_with_pos_updated(d, cursor, f"Generated by Cubic YYY\n{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}", width = 1000, 
                                    font = BANK_SANS_EF_SC_REGULAR, fontsize = MIN_SIZE, color=(191,191,191,127), is_right2left=True)

    return image


@registered_as("apex")
def _get_apex_image(info_dict: dict, legends: list, scores: list):
    image = Image.new('RGBA', (1920, 1080), WHITE)
    image_fore = get_foreground(info_dict, "", legends=legends, scores=scores)
    if image_fore:
        image.paste(image_fore, None, image_fore)
        
    return image

