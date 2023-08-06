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

from image_utils import * # Oh, forgive me

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

def get_foreground(info: dict, desc:str, legends: list|None = None, scores: list = None, width=1920, height=1080):
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
    
    ### Part: Progression Graph
    # Graph Title
    TITLE_POS = Pos(640, 270)
    cursor = copy(TITLE_POS)
    text_with_pos_updated(d, cursor, "Rank Progression", font = BANK_SANS_EF_SC_REGULAR, fontsize = TINY_SIZE, color=BLACK)
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
    cursor = Pos(width - STD_GAP, STD_GAP)
    multiline_text_with_pos_updated(d, cursor, desc, width = 500, font = SERIF_HEAVY, fontsize = TINY_SIZE, color=BLACK, is_right2left=True)
    
    ### Part: WaterMark
    cursor = Pos(width - STD_GAP, height - STD_GAP - 2 * MIN_SIZE)
    multiline_text_with_pos_updated(d, cursor, f"Generated by Cubic YYY\n{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}", width = 1000, 
                                    font = BANK_SANS_EF_SC_REGULAR, fontsize = MIN_SIZE, color=(191,191,191,127), is_right2left=True)

    
    ### Part: progress
    # Gen plot
    if not scores:
        scores = [rank_score]
    
    if scores[-1]!=rank_score:
        scores.append(rank_score)

    return image


@registered_as("apex")
def _get_apex_image(uid: int, info_dict: dict):

    def get_apex_card(background_url: str | tuple = "", width: int = 1920, height: int = 1080):
        pass


if __name__ == '__main__': 
    rank_scores = [85, 900, 4920, 11095, 10008, 20008, 24091, 30094, 97, 99]  
    test_info = {"global":{"name":"REXUEGOUDANER","uid":"1008633771133","avatar":"https://secure.download.dm.origin.com/production/avatar/prod/userAvatar/32806649/416x416.PNG","platform":"PC","level":19,"toNextLevelPercent":12,"internalUpdateCount":75155,"bans":{"isActive":False,"remainingSeconds":0,"last_banReason":"COMPETITIVE_DODGE_COOLDOWN"},"rank":{"rankScore":336593,"rankName":"Apex Predator","rankDiv":0,"ladderPosPlatform":575,"rankImg":"https://api.mozambiquehe.re/assets/ranks/apexpredator1.png","rankedSeason":"br_ranked","ALStopPercent":0.01,"ALStopInt":533,"ALStopPercentGlobal":0.01,"ALStopIntGlobal":567,"ALSFlag":False},"arena":{"rankScore":0,"rankName":"Unranked","rankDiv":0,"ladderPosPlatform":-1,"rankImg":"https://api.mozambiquehe.re/assets/ranks/unranked4.png","rankedSeason":"arenas17_split_0","ALStopPercent":"No game this split","ALStopInt":"No game this split","ALStopPercentGlobal":"No game this split","ALStopIntGlobal":"No game this split","ALSFlag":True},"battlepass":{"level":-1,"history":{"season1":-1,"season2":0,"season3":-1,"season4":-1,"season5":-1,"season6":-1,"season7":-1,"season8":-1,"season9":-1,"season10":-1,"season11":-1,"season12":-1,"season13":-1,"season14":-1,"season15":-1,"season16":-1,"season17":-1}},"internalParsingVersion":2,"badges":[{"name":"null","value":0},{"name":"You're Tiering Me Apart: Ranked Season 8","value":14},{"name":"You're Tiering Me Apart: Ranked Season 6","value":14},{"name":"You're Tiering Me Apart: Ranked Season 4","value":15},{"name":"You're Tiering Me Apart: Ranked Season 3","value":12361},{"name":"You're Tiering Me Apart: Ranked Season 16","value":0},{"name":"You're Tiering Me Apart: Ranked Season 13","value":14},{"name":"You're Tiering Me Apart: Ranked Season 11","value":14},{"name":"ALGS Participant","value":0}],"levelPrestige":3},"realtime":{"lobbyState":"open","isOnline":1,"isInGame":0,"canJoin":0,"partyFull":1,"selectedLegend":"Revenant","currentState":"inMatch","currentStateSinceTimestamp":1691228681,"currentStateSecsAgo":39,"currentStateAsText":"In match (00:39)"},"legends":{"selected":{"LegendName":"Revenant","data":[{"name":"BR Kills","value":206,"key":"kills","global":False}],"gameInfo":{"skin":"Limelight","skinRarity":"Common","frame":"Slice and Dice","frameRarity":"Legendary","pose":"Simulacrum","poseRarity":"Common","intro":"None","introRarity":"None","badges":[{"name":"null","value":0,"category":"Account Badges"},{"name":"null","value":0,"category":"Account Badges"},{"name":"null","value":0,"category":"Account Badges"},{"name":"null","value":0,"category":"Account Badges"}]},"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/revenant.png","banner":"https://api.mozambiquehe.re/assets/banners/revenant.jpg"}},"all":{"Global":{"data":[{"name":"R-99 SMG Kills","value":8391,"key":"mastery_r99_kills","rank":{"rankPos":472,"topPercent":15.25},"rankPlatformSpecific":{"rankPos":73,"topPercent":6.33}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/global.png","banner":"https://api.mozambiquehe.re/assets/banners/global.jpg"}},"Revenant":{"data":[{"name":"BR Kills","value":206,"key":"kills","rank":{"rankPos":550185,"topPercent":23.11},"rankPlatformSpecific":{"rankPos":142444,"topPercent":21.13}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/revenant.png","banner":"https://api.mozambiquehe.re/assets/banners/revenant.jpg"}},"Crypto":{"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/crypto.png","banner":"https://api.mozambiquehe.re/assets/banners/crypto.jpg"}},"Horizon":{"data":[{"name":"BR Kills","value":5595,"key":"specialEvent_kills","rank":{"rankPos":20389,"topPercent":1.08},"rankPlatformSpecific":{"rankPos":7022,"topPercent":0.74}},{"name":"BR Damage","value":1838733,"key":"specialEvent_damage","rank":{"rankPos":19298,"topPercent":1.03},"rankPlatformSpecific":{"rankPos":6664,"topPercent":0.71}},{"name":"BR Wins","value":352,"key":"specialEvent_wins","rank":{"rankPos":9954,"topPercent":0.79},"rankPlatformSpecific":{"rankPos":3399,"topPercent":0.51}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/horizon.png","banner":"https://api.mozambiquehe.re/assets/banners/horizon.jpg"}},"Gibraltar":{"data":[{"name":"BR Season 3 Wins","value":3,"key":"wins_season_3","rank":{"rankPos":10352,"topPercent":12.49},"rankPlatformSpecific":{"rankPos":2787,"topPercent":20.8}},{"name":"BR Season 6 Wins","value":2,"key":"wins_season_6","rank":{"rankPos":6928,"topPercent":25.36},"rankPlatformSpecific":{"rankPos":2421,"topPercent":56.21}},{"name":"BR Season 8 wins","value":5,"key":"wins_season_8","rank":{"rankPos":17864,"topPercent":12.17},"rankPlatformSpecific":{"rankPos":4670,"topPercent":16.76}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/gibraltar.png","banner":"https://api.mozambiquehe.re/assets/banners/gibraltar.jpg"}},"Wattson":{"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/wattson.png","banner":"https://api.mozambiquehe.re/assets/banners/wattson.jpg"}},"Fuse":{"data":[{"name":"BR Kills","value":24,"key":"kills","rank":{"rankPos":1733242,"topPercent":72.74},"rankPlatformSpecific":{"rankPos":791685,"topPercent":79.84}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/fuse.png","banner":"https://api.mozambiquehe.re/assets/banners/fuse.jpg"}},"Bangalore":{"data":[{"name":"Double time: Distance","value":114911,"key":"double_time_distance","rank":{"rankPos":43468,"topPercent":9.58},"rankPlatformSpecific":{"rankPos":17611,"topPercent":8.28}},{"name":"Smoke grenade: Enemies hit","value":862,"key":"smoke_grenade_enemies_hit","rank":{"rankPos":4926,"topPercent":2.12},"rankPlatformSpecific":{"rankPos":2197,"topPercent":1.83}},{"name":"Rolling thunder: Damage","value":86998,"key":"creeping_barrage_damage","rank":{"rankPos":18751,"topPercent":4.94},"rankPlatformSpecific":{"rankPos":6866,"topPercent":3.67}},{"name":"BR Season 5 Wins","value":1,"key":"wins_season_5","rank":{"rankPos":57372,"topPercent":49.66},"rankPlatformSpecific":{"rankPos":12264,"topPercent":50.88}},{"name":"BR Season 7 kills","value":0,"key":"kills_season_7","rank":{"rankPos":52782,"topPercent":95.5},"rankPlatformSpecific":{"rankPos":17803,"topPercent":96.3}},{"name":"BR Season 7 wins","value":0,"key":"wins_season_7","rank":{"rankPos":100961,"topPercent":76.67},"rankPlatformSpecific":{"rankPos":30522,"topPercent":73.53}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/bangalore.png","banner":"https://api.mozambiquehe.re/assets/banners/bangalore.jpg"}},"Wraith":{"data":[{"name":"BR Kills","value":18708,"key":"kills","rank":{"rankPos":12898,"topPercent":0.22},"rankPlatformSpecific":{"rankPos":4343,"topPercent":0.18}},{"name":"BR Headshots","value":29125,"key":"headshots","rank":{"rankPos":5061,"topPercent":1.37},"rankPlatformSpecific":{"rankPos":1630,"topPercent":1.4}},{"name":"BR Damage","value":5880644,"key":"damage","rank":{"rankPos":8491,"topPercent":0.42},"rankPlatformSpecific":{"rankPos":3062,"topPercent":0.24}},{"name":"BR Kills","value":19005,"key":"specialEvent_kills","rank":{"rankPos":9233,"topPercent":0.42},"rankPlatformSpecific":{"rankPos":2645,"topPercent":0.26}},{"name":"BR Damage","value":5973126,"key":"specialEvent_damage","rank":{"rankPos":7671,"topPercent":0.37},"rankPlatformSpecific":{"rankPos":2172,"topPercent":0.22}},{"name":"BR Wins","value":856,"key":"specialEvent_wins","rank":{"rankPos":9004,"topPercent":0.67},"rankPlatformSpecific":{"rankPos":2622,"topPercent":0.43}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/wraith.png","banner":"https://api.mozambiquehe.re/assets/banners/wraith.jpg"}},"Octane":{"data":[{"name":"Stim distance traveled","value":952113,"key":"distance_on_stim","rank":{"rankPos":40766,"topPercent":3.09},"rankPlatformSpecific":{"rankPos":8140,"topPercent":1.81}},{"name":"Jump pad allies launched","value":4849,"key":"squadmates_use_jumppad","rank":{"rankPos":3794,"topPercent":0.89},"rankPlatformSpecific":{"rankPos":1211,"topPercent":0.79}},{"name":"Passive health regenerated","value":354586,"key":"passive_health_regen","rank":{"rankPos":15739,"topPercent":2.01},"rankPlatformSpecific":{"rankPos":5345,"topPercent":1.97}}],"gameInfo":{"badges":[{"name":"NOT_IMPLEMENTED_YET_1519787133","value":0},{"name":"Octane's Wrath","value":5},{"name":"Octane's Wake","value":0}]},"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/octane.png","banner":"https://api.mozambiquehe.re/assets/banners/octane.jpg"}},"Bloodhound":{"data":[{"name":"BR Headshots","value":1153,"key":"headshots","rank":{"rankPos":61984,"topPercent":20.61},"rankPlatformSpecific":{"rankPos":"NOT_CALCULATED_YET","topPercent":"NOT_CALCULATED_YET"}},{"name":"BR Wins","value":185,"key":"specialEvent_wins","rank":{"rankPos":22096,"topPercent":2.87},"rankPlatformSpecific":{"rankPos":5457,"topPercent":1.64}},{"name":"BR Kills","value":2616,"key":"specialEvent_kills","rank":{"rankPos":66639,"topPercent":3.23},"rankPlatformSpecific":{"rankPos":18223,"topPercent":2.02}},{"name":"BR Damage","value":944148,"key":"specialEvent_damage","rank":{"rankPos":36683,"topPercent":4.17},"rankPlatformSpecific":{"rankPos":8867,"topPercent":2.6}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/bloodhound.png","banner":"https://api.mozambiquehe.re/assets/banners/bloodhound.jpg"}},"Caustic":{"data":[{"name":"BR Season 3 Wins","value":1,"key":"wins_season_3","rank":{"rankPos":23426,"topPercent":47.53},"rankPlatformSpecific":{"rankPos":5579,"topPercent":55.52}},{"name":"BR Season 4 Wins","value":2,"key":"wins_season_4","rank":{"rankPos":31568,"topPercent":45.33},"rankPlatformSpecific":{"rankPos":7390,"topPercent":55.1}},{"name":"BR Season 9 wins","value":0,"key":"wins_season_9","rank":{"rankPos":49308,"topPercent":82.42},"rankPlatformSpecific":{"rankPos":9011,"topPercent":81.48}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/caustic.png","banner":"https://api.mozambiquehe.re/assets/banners/caustic.jpg"}},"Lifeline":{"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/lifeline.png","banner":"https://api.mozambiquehe.re/assets/banners/lifeline.jpg"}},"Pathfinder":{"data":[{"name":"BR Headshots","value":11527,"key":"headshots","rank":{"rankPos":11590,"topPercent":4.93},"rankPlatformSpecific":{"rankPos":"NOT_CALCULATED_YET","topPercent":"NOT_CALCULATED_YET"}},{"name":"Grapple: Travel distance","value":1255066,"key":"grapple_travel_distance","rank":{"rankPos":22764,"topPercent":1.92},"rankPlatformSpecific":{"rankPos":"NOT_CALCULATED_YET","topPercent":"NOT_CALCULATED_YET"}},{"name":"BR Season 3 Wins","value":19,"key":"wins_season_3","rank":{"rankPos":8670,"topPercent":8.35},"rankPlatformSpecific":{"rankPos":3111,"topPercent":12.24}},{"name":"Grand Soiree kills","value":18578,"key":"grandsoiree_kills","rank":{"rankPos":2245,"topPercent":1.19},"rankPlatformSpecific":{"rankPos":508,"topPercent":1.4}},{"name":"Grand Soiree wins","value":292,"key":"grandsoiree_wins","rank":{"rankPos":14449,"topPercent":7.8},"rankPlatformSpecific":{"rankPos":"NOT_CALCULATED_YET","topPercent":"NOT_CALCULATED_YET"}},{"name":"BR Kills","value":18578,"key":"specialEvent_kills","rank":{"rankPos":4565,"topPercent":0.2},"rankPlatformSpecific":{"rankPos":991,"topPercent":0.08}},{"name":"BR Damage","value":5909156,"key":"specialEvent_damage","rank":{"rankPos":3638,"topPercent":0.17},"rankPlatformSpecific":{"rankPos":810,"topPercent":0.07}},{"name":"BR Wins","value":905,"key":"specialEvent_wins","rank":{"rankPos":4433,"topPercent":0.28},"rankPlatformSpecific":{"rankPos":1114,"topPercent":0.14}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/pathfinder.png","banner":"https://api.mozambiquehe.re/assets/banners/pathfinder.jpg"}},"Loba":{"data":[{"name":"BR Kills","value":647,"key":"kills","rank":{"rankPos":275855,"topPercent":8.84},"rankPlatformSpecific":{"rankPos":113068,"topPercent":9.4}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/loba.png","banner":"https://api.mozambiquehe.re/assets/banners/loba.jpg"}},"Mirage":{"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/mirage.png","banner":"https://api.mozambiquehe.re/assets/banners/mirage.jpg"}},"Rampart":{"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/rampart.png","banner":"https://api.mozambiquehe.re/assets/banners/rampart.jpg"}},"Valkyrie":{"data":[{"name":"VTOL Jets: Distance travelled","value":191739,"key":"vtol_distance_travelled","rank":{"rankPos":9823,"topPercent":3.31},"rankPlatformSpecific":{"rankPos":3382,"topPercent":3.07}},{"name":"Missile Swarm: Enemies hit","value":1701,"key":"missile_swarm_enemies_hit","rank":{"rankPos":13987,"topPercent":2.59},"rankPlatformSpecific":{"rankPos":4142,"topPercent":1.37}},{"name":"Skyward dive: Alies repositioned","value":1258,"key":"skyward_dive_allies_repositioned","rank":{"rankPos":1862,"topPercent":1.45},"rankPlatformSpecific":{"rankPos":662,"topPercent":1.2}},{"name":"BR Wins","value":2,"key":"specialEvent_wins","rank":{"rankPos":"NOT_CALCULATED_YET","topPercent":"NOT_CALCULATED_YET"},"rankPlatformSpecific":{"rankPos":"NOT_CALCULATED_YET","topPercent":"NOT_CALCULATED_YET"}},{"name":"BR Season 9 wins","value":2,"key":"wins_season_9","rank":{"rankPos":55247,"topPercent":55.65},"rankPlatformSpecific":{"rankPos":"NOT_CALCULATED_YET","topPercent":"NOT_CALCULATED_YET"}},{"name":"BR Season 10 wins","value":0,"key":"wins_season_10","rank":{"rankPos":62321,"topPercent":87.49},"rankPlatformSpecific":{"rankPos":"NOT_CALCULATED_YET","topPercent":"NOT_CALCULATED_YET"}}],"gameInfo":{"badges":[{"name":"Valkyrie's Wrath","value":5}]},"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/valkyrie.png","banner":"https://api.mozambiquehe.re/assets/banners/valkyrie.jpg"}},"Seer":{"data":[{"name":"BR Kills","value":445,"key":"kills","rank":{"rankPos":4794,"topPercent":0.17},"rankPlatformSpecific":{"rankPos":1611,"topPercent":0.13}},{"name":"Focus of Attention: Enemies Hit","value":4344,"key":"tactical_focus_of_attention_hits","rank":{"rankPos":4930,"topPercent":0.99},"rankPlatformSpecific":{"rankPos":1849,"topPercent":0.59}},{"name":"BR Kills","value":2647,"key":"specialEvent_kills","rank":{"rankPos":3843,"topPercent":0.34},"rankPlatformSpecific":{"rankPos":1207,"topPercent":0.22}},{"name":"BR Damage","value":797286,"key":"specialEvent_damage","rank":{"rankPos":5918,"topPercent":0.51},"rankPlatformSpecific":{"rankPos":2093,"topPercent":0.36}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/seer.png","banner":"https://api.mozambiquehe.re/assets/banners/seer.jpg"}},"Ash":{"data":[{"name":"BR Kills","value":175,"key":"kills","rank":{"rankPos":634350,"topPercent":22.23},"rankPlatformSpecific":{"rankPos":"NOT_CALCULATED_YET","topPercent":"NOT_CALCULATED_YET"}},{"name":"BR Damage","value":131943,"key":"specialEvent_damage","rank":{"rankPos":186375,"topPercent":19.59},"rankPlatformSpecific":{"rankPos":116496,"topPercent":19.59}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/ash.png","banner":"https://api.mozambiquehe.re/assets/banners/ash.jpg"}},"Mad Maggie":{"data":[{"name":"BR Kills","value":763,"key":"kills","rank":{"rankPos":32554,"topPercent":1.58},"rankPlatformSpecific":{"rankPos":19560,"topPercent":2.17}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/mad maggie.png","banner":"https://api.mozambiquehe.re/assets/banners/mad maggie.jpg"}},"Newcastle":{"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/newcastle.png","banner":"https://api.mozambiquehe.re/assets/banners/newcastle.jpg"}},"Vantage":{"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/vantage.png","banner":"https://api.mozambiquehe.re/assets/banners/vantage.jpg"}},"Catalyst":{"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/catalyst.png","banner":"https://api.mozambiquehe.re/assets/banners/catalyst.jpg"}},"Ballistic":{"data":[{"name":"BR Season 17 wins","value":20,"key":"wins_season_17","rank":{"rankPos":9205,"topPercent":5.42},"rankPlatformSpecific":{"rankPos":5056,"topPercent":3.89}},{"name":"BR Season 17 kills","value":238,"key":"kills_season_17","rank":{"rankPos":21552,"topPercent":11.83},"rankPlatformSpecific":{"rankPos":12490,"topPercent":9.02}}],"ImgAssets":{"icon":"https://api.mozambiquehe.re/assets/icons/ballistic.png","banner":"https://api.mozambiquehe.re/assets/banners/ballistic.jpg"}}}},"mozambiquehere_internal":{"isNewToDB":False,"clusterSrv":"fr-1"},"total":{"mastery_r99_kills":{"name":"R-99 SMG Kills","value":8391},"kills":{"name":"BR Kills","value":20968},"specialEvent_kills":{"name":"BR Kills","value":48441},"specialEvent_damage":{"name":"BR Damage","value":15594392},"specialEvent_wins":{"name":"BR Wins","value":2300},"wins_season_3":{"name":"BR Season 3 Wins","value":23},"wins_season_6":{"name":"BR Season 6 Wins","value":2},"wins_season_8":{"name":"BR Season 8 wins","value":5},"double_time_distance":{"name":"Double time: Distance","value":114911},"smoke_grenade_enemies_hit":{"name":"Smoke grenade: Enemies hit","value":862},"creeping_barrage_damage":{"name":"Rolling thunder: Damage","value":86998},"wins_season_5":{"name":"BR Season 5 Wins","value":1},"kills_season_7":{"name":"BR Season 7 kills","value":0},"wins_season_7":{"name":"BR Season 7 wins","value":0},"headshots":{"name":"BR Headshots","value":41805},"damage":{"name":"BR Damage","value":5880644},"distance_on_stim":{"name":"Stim distance traveled","value":952113},"squadmates_use_jumppad":{"name":"Jump pad allies launched","value":4849},"passive_health_regen":{"name":"Passive health regenerated","value":354586},"wins_season_4":{"name":"BR Season 4 Wins","value":2},"wins_season_9":{"name":"BR Season 9 wins","value":2},"grapple_travel_distance":{"name":"Grapple: Travel distance","value":1255066},"grandsoiree_kills":{"name":"Grand Soiree kills","value":18578},"grandsoiree_wins":{"name":"Grand Soiree wins","value":292},"vtol_distance_travelled":{"name":"VTOL Jets: Distance travelled","value":191739},"missile_swarm_enemies_hit":{"name":"Missile Swarm: Enemies hit","value":1701},"skyward_dive_allies_repositioned":{"name":"Skyward dive: Alies repositioned","value":1258},"wins_season_10":{"name":"BR Season 10 wins","value":0},"tactical_focus_of_attention_hits":{"name":"Focus of Attention: Enemies Hit","value":4344},"wins_season_17":{"name":"BR Season 17 wins","value":20},"kills_season_17":{"name":"BR Season 17 kills","value":238},"kd":{"value":"-1","name":"KD"}},"processingTime":0.2688868045806885}
    image = Image.new('RGBA', (1920, 1080), WHITE)
    image_fore = get_foreground(test_info, "我阐释你的梦\n変わったあああああああああああああああ", ['pathfinder', 'seer', 'bangalore'], scores=rank_scores)
    if image_fore:
        image.paste(image_fore, None, image_fore)
        image.save('./tmp.png')
