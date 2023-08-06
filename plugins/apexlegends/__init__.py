###
from functools import lru_cache
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Event, Message, PrivateMessageEvent, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import Arg, CommandArg, ArgPlainText, EventMessage
from nonebot.plugin import on_command
from nonebot.typing import T_State
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


global_config = get_driver().config

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = global_config.apex_key
DEFAULT_HEADERS = {
    "Authorization": API_KEY,
}
TIMEOUT = aiohttp.ClientTimeout(total=30, sock_connect=20, sock_read=20)
BASE_URL = "https://api.mozambiquehe.re/"

apex_list = on_command("apex_list", rule=lambda: True, aliases={"apex列表", "apex_list"})
apex_user = on_command("apex_user", rule=lambda: True, aliases={"apex用户","apex_user"})
apex_uid = on_command("apex_uid", rule=lambda: True, aliases={"apexuid","apex_uid"})
apex_stat = on_command("apex_stat", rule=lambda: True, aliases={"上分统计","apex_stat"})
apex_add = on_command("apex_add", rule=lambda: True, aliases={"apex添加","apex_add"})
apex_bind = on_command("apex_bind", rule=lambda: True, aliases={"apex绑定","apex_bind"})

@apex_uid.handle()
async def handle_uid_first(matcher: Matcher, arg: Message = CommandArg()):
    uid = arg.extract_plain_text()
    if uid:
        matcher.set_arg("uid", int(arg))


@apex_uid.got("uid", prompt="请提供用户uid")
async def handle_uid(matcher: Matcher, uid: str = ArgPlainText("uid")):
    async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
        url = BASE_URL + f"bridge"
        async with session.get(url, params={"uid":uid, "platform": "PC"}) as r:
            user = json.loads(await r.text())
            await matcher.finish(str(user)[:20])