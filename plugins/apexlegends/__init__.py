###
import asyncio
from functools import lru_cache, wraps
from typing import Any
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Event, Message, PrivateMessageEvent, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import Arg, CommandArg, ArgPlainText, EventMessage
from nonebot.plugin import on_command
from nonebot.typing import T_State
from cachetools import TTLCache

import base64
import os
import re
import json
import pytz
import string
import random
from datetime import datetime, timezone, timedelta
from math import ceil
from utils import qq_image
from nonebot import get_driver
import aiohttp
import time
import sqlite3

from utils.image_utils import random_str

global_config = get_driver().config

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
BINDED_USER_FILE = os.path.join(PLUGIN_DIR, 'users.json')
API_KEY = global_config.apex_key
CUR_SEASON = global_config.season
CUR_SPLIT = global_config.split
IMAGE_TMP_PATH = "/tmp"

qq2uid:dict[str, Any] = {
    "initialized":[]
}
try:
    with open(BINDED_USER_FILE, "r") as f:
        qq2uid = json.loads(f.read())
except FileNotFoundError:
    pass
except:
    print("WARNING: Could not recover account JSON file.")
    pass

# Database to Store Rank Records
DATABASE_FILE = os.path.join(PLUGIN_DIR, 'data.sqlite')
INIT_SQL = """CREATE TABLE IF NOT EXISTS data 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                timestamp BIGINT DEFAULT (strftime('%s', 'now')), 
                score INTEGER,
                uid BIGINT NOT NULL,
                season INTEGER,
                split INTEGER);
            CREATE INDEX IF NOT EXISTS timeidx ON data(timestamp);
            CREATE INDEX IF NOT EXISTS seasonidx ON data(season);
            CREATE INDEX IF NOT EXISTS scoreidx ON data(score);
            """

db = sqlite3.connect(DATABASE_FILE)
dbcursor = db.cursor()
dbcursor.executescript(INIT_SQL)

DEFAULT_HEADERS = {
    "Authorization": API_KEY,
}
TIMEOUT = aiohttp.ClientTimeout(total=30, sock_connect=20, sock_read=20)
API_BASE_URL = "https://api.mozambiquehe.re/"
MATCH_HISTORY_URL = "https://apexlegendsstatus.com/core/gameHistory"
MOST_LEGENDS_URL = "https://apexlegendsstatus.com/core/chart_data.php"

def lru_cache_with_expire(maxsize=128, expire_seconds=300):
    cache = TTLCache(maxsize=maxsize, ttl=expire_seconds)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = (args, frozenset(kwargs.items()))

            # Check if the result is already in the cache
            if key in cache.keys():
                result, timestamp = cache[key]
                current_time = time.time()

                # Check if the cached entry has expired
                if current_time - timestamp <= expire_seconds:
                    return result

            # Call the function and cache the result with the current timestamp
            result = await func(*args, **kwargs)
            cache[key] = (result, time.time())
            return result

        return wrapper

    return decorator

def extract_rank_scores(html: str):
    pattern = r'([0-9,]+) LP '
    for match in re.finditer(pattern, html):
        yield int(match.group(1).replace(",",""))

@lru_cache_with_expire(maxsize=128, expire_seconds=90)
async def fetch_status(uid: int):
    async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
        url = API_BASE_URL + 'bridge'
        async with session.get(url, params={"uid": uid,
                                            "platform": "PC"}) as r:
            return await r.json()
        
@lru_cache_with_expire(maxsize=128, expire_seconds=120)
async def fetch_rank_scores(uid: int, season: int, split: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(MATCH_HISTORY_URL, params={"split": f"s{season}_s{split}",
                                            "uid": uid}) as r:
            html = await r.text()
            # print(html[:200])
            scores = list(extract_rank_scores(html))
            scores.reverse()
            return scores
            
        
@lru_cache_with_expire(maxsize=128, expire_seconds=300)
async def fetch_legend_played(uid: int, season: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(MOST_LEGENDS_URL, params={"period": f"season{season}",
                                            "p": "legend_gameplayed", # replace with `total_timeplayed` to query time played
                                            "AUID": uid}) as r:
            obj = await r.json()
            res = {}
            for legend in obj[1:]:
                non_zero_values = list(filter(lambda x: x != 0, legend["data"]))
                res[legend["name"]] = 0 if not non_zero_values else non_zero_values[0]
            return sorted(res.items(), key=lambda x: x[1], reverse=True)
            
apex_list = on_command("apex_list", rule=lambda: True,
                       aliases={"apex列表", "apex_list"})
apex_user = on_command("apex_user", rule=lambda: True,
                       aliases={"apex用户", "apex_user"})
apex_uid = on_command("apex_uid", rule=lambda: True,
                      aliases={"apexuid", "apex_uid"})
apex_stat = on_command("apex_stat", rule=lambda: True,
                       aliases={"apex名片", "apexme"})
apex_add = on_command("apex_add", rule=lambda: True,
                      aliases={"apex添加", "apex追踪", "apex_add"})
apex_bind = on_command("apex_bind", rule=lambda: True,
                       aliases={"apex绑定", "apex_bind"})

def dump_qq2uid():
    with open(BINDED_USER_FILE, "w") as f:
        f.write(json.dumps(qq2uid))

async def init_trace(matcher, uid):
    async with aiohttp.ClientSession() as session:
        await matcher.send(f"UID:{uid}\n请等待初始化……")
        scores = await fetch_rank_scores(int(uid), int(CUR_SEASON), int(CUR_SPLIT))
        for score in scores:
            dbcursor.execute("INSERT INTO data (timestamp,score,uid,season,split) VALUES (?,?,?,?,?)", 
                             (0, score, int(uid), CUR_SEASON, CUR_SPLIT))
            # print((0, score, int(uid)))
        db.commit()
        qq2uid["initialized"].append(uid) 
        dump_qq2uid()
        await matcher.finish(f"初始化完毕，导入了{len(scores)}条排位分数记录。")
        
@apex_bind.handle()
async def handle_bind_first(matcher: Matcher, arg: Message = CommandArg()):
    uid = arg.extract_plain_text()
    if uid:
        matcher.set_arg("uid", Message(uid))


@apex_bind.got("uid", prompt="请提供你的uid")
async def handle_bind(matcher: Matcher, event: Event, struid: str = ArgPlainText("uid")):
    uid = int(struid)
    if uid in qq2uid.values():
        await matcher.finish(f"UID:{uid}已经被绑定。绑定者可以使用 apex解绑 命令解除绑定。")
        return
    
    qq = event.get_user_id()
    if uid in qq2uid["initialized"]:
        await matcher.finish(f"绑定成功。")
        
    await init_trace(matcher, uid)
        
        


@apex_stat.handle()
async def handle_stat_first(matcher: Matcher, event: Event, arg: Message = CommandArg()):
    uid = arg.extract_plain_text()
    try:
        int(uid)
        matcher.set_arg("uid", Message(str(uid)))
    except ValueError: # Default: self
        qq = event.get_user_id()
        if qq not in qq2uid.keys():
            await matcher.finish(f"该QQ未绑定uid. 请使用 apex绑定 命令进行绑定。")
        print(f"Corresponding uid:{qq2uid[qq]}")
        matcher.set_arg("uid", Message(str(qq2uid[qq])))


@apex_stat.got("uid", prompt="我uid呢？")
async def handle_stat(matcher: Matcher, struid: str = ArgPlainText("uid")):
    uid = int(struid)
    legend_stat = list(map(lambda x:x[0], await fetch_legend_played(uid, CUR_SEASON)))
    top3 = legend_stat[:3]
    info = await fetch_status(uid)
    dbcursor.execute("SELECT score FROM data WHERE season=? AND split=? AND uid=?", (CUR_SEASON, CUR_SPLIT, uid))
    result = dbcursor.fetchall()
    scores = list(map(lambda x:x[0], result))
    image = qq_image.handlers['apex'](info, top3, scores)
    image_path = f"{IMAGE_TMP_PATH}/tmp_{random_str(6)}.png"
    try:
        image.save(image_path) #TODO: using a context manager to delete tmp file
        await matcher.send(MessageSegment.image("file://" + image_path))
    finally:
        os.remove(image_path)

@apex_add.handle()
async def handle_add_first(matcher: Matcher, arg: Message = CommandArg()):
    uid = arg.extract_plain_text()
    if uid:
        matcher.set_arg("uid", Message(uid))


@apex_add.got("uid", prompt="请提供你的uid")
async def handle_add(matcher: Matcher, event: Event, struid: str = ArgPlainText("uid")):
    uid = int(struid)
    if uid in qq2uid["initialized"]:
        await matcher.finish(f"已经在追踪列表中。")
        
    await init_trace(matcher, uid)
    
        
if __name__ == "__main__":
    pass