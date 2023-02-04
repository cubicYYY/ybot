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
import pypinyin
from pydub import AudioSegment
import os
import random
import string
import base64

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

WORD_WAV_PATH = os.path.join(PLUGIN_DIR, "sources")
PHRASE_WAV_PATH = os.path.join(PLUGIN_DIR, "ysddSources")
TRANSFORM_MAP = {
    "a": "诶",
    "b": "比",
    "c": "西",
    "d": "底",
    "e": "一",
    "f": "爱抚",
    "g": "鸡",
    "h": "爱吃",
    "i": "爱",
    "j": "贼",  # TODO: zhei.wav not zei.wav
    "k": "可",
    "l": "爱录",
    "m": "爱目",
    "n": "恩",
    "o": "偶",
    "p": "皮",
    "q": "揪",  # TODO: kiu.wav not jiu.wav
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
}


def random_str(length):
    """Generate random a string consists with a-zA-z0-9 with a given length"""
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


diangun = on_command("大家好啊", rule=lambda: True, aliases={"diangun", "活字印刷"})


@diangun.handle()
async def handle_diangun(matcher: Matcher, arg: Message = CommandArg()):
    if arg.extract_plain_text().strip(" ") != "":
        matcher.set_arg("word", Message(arg))


@diangun.got("word", prompt="你要鬼叫什么？")
async def gen_diangun(matcher: Matcher, word: str = ArgPlainText("word")):
    word = word.lower()
    for k, v in TRANSFORM_MAP.items():
        word = word.replace(k, v)
    pinyins = pypinyin.lazy_pinyin(word)
    sound_data = AudioSegment.from_wav(f"{PHRASE_WAV_PATH}/djha.wav")
    for pinyin in filter(lambda x: x.islower() and x.isalpha(), pinyins):
        try:
            sound_data += AudioSegment.from_wav(
                f"{WORD_WAV_PATH}/{pinyin}.wav")
        except:
            pass
    tmp_file_path = f"/tmp/tmp_{random_str(6)}.wav"
    sound_data.export(tmp_file_path, format="wav")
    with open(tmp_file_path, "rb") as f:
        await matcher.send(MessageSegment.record(file=f.read()))
    # await matcher.send(MessageSegment.record(file=f.read()))
    # FIXME: I don't know why cqhttp respond "file not exist" when using file path as a arg
    os.remove(tmp_file_path)
