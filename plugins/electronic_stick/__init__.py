# 电棍活字印刷
# 资源来自：https://github.com/DSP-8192/HuoZiYinShua
# TODO: 原声大碟替换常见短语
from time import sleep
from nonebot import get_driver
from nonebot.rule import to_me
from nonebot.params import EventPlainText, CommandArg, ArgPlainText
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.plugin import on_command
from nonebot.typing import T_State
import pypinyin
from pydub import AudioSegment
import os
import random
import string
import re

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

WORD_WAV_PATH = os.path.join(PLUGIN_DIR, "sources")
PHRASE_WAV_PATH = os.path.join(PLUGIN_DIR, "special_sources")
_TRANSFORM_MAP = {
    "a": "诶",
    "b": "比",
    "c": "西",
    "d": "底",
    "e": "一",
    "f": "爱抚",
    "g": "鸡",
    "h": "爱吃",
    "i": "爱",
    "j": "$zhei$",
    "k": "可",
    "l": "爱录",
    "m": "爱目",
    "n": "恩",
    "o": "偶",
    "p": "皮",
    "q": "$kiu$",
    "r": "啊",
    "s": "爱死",
    "t": "题",
    "u": "油",
    "v": "喂",
    "w": "打不溜",
    "x": "艾克斯",
    "y": "歪",
    "z": "贼",
    "0": "零",
    "1": "一",
    "2": "二",
    "3": "三",
    "4": "四",
    "5": "五",
    "6": "六",
    "7": "七",
    "8": "八",
    "9": "九",
    "米浴说的道理": "$miyu$",
    "啊米浴说的道理": "$miyu$",
    "大家好啊": "$djha$",
    "我是说的道理": "$wssddl$",
    "今天来点大家想看的东西": "$jtlaidian$",
    "今天来点儿大家想看的东西": "$jtlaidian$",
    "说的道理": "$sddl$",
    "波比是我爹": "$bobi$",
    "啊嘛波比是我爹": "$bobi$",
    "哇袄": "$waao$",
    "【欧西给】": "$oxga$", # TODO: avoid collision with number/alpha escaping
    "【欧西给一】": "$oxga$",
    "【欧西给一】": "$oxgb$",
    "【欧西给二】": "$oxgc$",
    "【欧西给三】": "$oxgd$",
    "AQ": "$AQ$",
    "AQ1": "$AQa$",
    "AQ2": "$AQb$",
    "再Q": "$zaiQ$",
    "走位": "$zouwei$",
    "诶乌兹": "$euz$",
    "欧内的手": "$onds$",
    "好汉": "$haohan$",
    "我是电棍": "$wsdg$",
    "【啊】": "$aa$",
    "【啊一】": "$aa$",
    "【啊二】": "$ab$",
    "韭菜盒子": "$jiucaihezi$",
    "癌症晚期": "$azwq$",
    "【鬼叫】": "$guijiaoa$",
    "【鬼叫一】": "$guijiaob$", #哇袄！！
    "【鬼叫二】": "$guijiaob$", #哇袄！！
    "【鬼叫三】": "$guijiaoc$", #哇袄！！#哇袄！！
    "【鬼叫四】": "$guijiaod$", #wu---ao
    "【鬼叫五】": "$guijiaoe$", #wu---ao
    "【鬼叫六】": "$guijiaof$", #wua
}
TRANSFORM_MAP_LIST = sorted(_TRANSFORM_MAP.items(), key=lambda item: len(item[0]))
TRANSFORM_MAP = {ele[0] : ele[1]  for ele in TRANSFORM_MAP_LIST}
# print(TRANSFORM_MAP)

def random_str(length):
    """Generate random a string consists with a-zA-z0-9 with a given length"""
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


diangun = on_command("大家好啊", rule=lambda: True, aliases={"diangun", "活字印刷"})


@diangun.handle()
async def handle_diangun(state: T_State, matcher: Matcher, arg: Message = CommandArg()):
    state["start_init"] = False
    if arg.extract_plain_text().strip(" ") != "":
        state["start_init"] = True
        matcher.set_arg("word", Message(arg))


@diangun.got("word", prompt="你要鬼叫什么？")
async def gen_diangun(state: T_State, matcher: Matcher, word: str = ArgPlainText("word")):
    word = word.lower()
    for k, v in TRANSFORM_MAP.items():
        word = word.replace(k, v)
    pinyins = pypinyin.lazy_pinyin(word)
    sound_data = AudioSegment.from_wav(
        f"{PHRASE_WAV_PATH}/djha.wav") if state["start_init"] else AudioSegment.empty()
    # print(word, pinyins)
    for pinyin in pinyins:
        pattern = r"\$(.*?)\$"
        matches = re.findall(pattern, pinyin)
        try:
            # print(matches)
            if matches:
                for special in matches:
                    sound_data += AudioSegment.from_wav(
                        f"{PHRASE_WAV_PATH}/{special}.wav")
            elif pinyin.islower() and pinyin.isalpha():
                sound_data += AudioSegment.from_wav(
                    f"{WORD_WAV_PATH}/{pinyin}.wav")
        except Exception as e:
            print(e)
            continue
    tmp_file_path = f"/tmp/tmp_{random_str(6)}.wav"
    sound_data.export(tmp_file_path, format="wav")
    with open(tmp_file_path, "rb") as f:
        await matcher.send(MessageSegment.record(file=f.read()))
    # await matcher.send(MessageSegment.record(file=f.read()))
    # FIXME: I don't know why cqhttp respond "file not exist" when using file path as a arg
    os.remove(tmp_file_path)
