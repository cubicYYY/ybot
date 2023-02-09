import random
from typing import Optional, Iterator, Callable
from nonebot import get_driver
from nonebot.params import EventPlainText
from nonebot.matcher import Matcher
from nonebot.plugin import on_command, on_message
from nonebot.adapters.onebot.v11 import Event, Message, GroupMessageEvent
import pickle
import os
import re
import jieba

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
DIAGRAM_SAVE = os.path.join(PLUGIN_DIR, 'diagram.cache')

EOS = "<eos>"
BOS = "<bos>"

global_config = get_driver().config
TRACKING_GROUPS = global_config.tracking_groups
print("tracking:"+str(TRACKING_GROUPS))

async def tracked_group_checker(event: Event) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    if str(event.group_id) not in TRACKING_GROUPS:
        return False
    return True

class Markov(object):
    def __init__(self):
        self.trans: dict[tuple, dict[str, int]] = {}
        self.gram = 2
        try:
            with open(DIAGRAM_SAVE, "rb") as f:
                self.trans = pickle.load(file=f)
        except:
            pass

    def increase(self, key: tuple, value: str):
        times = self.trans.setdefault(key, {}).setdefault(value, 0)
        self.trans[key][value] = times + 1

    def update(self, sentence: list):
        sentence = [*[BOS for _ in range(self.gram)], *list(sentence), EOS]
        for i in range(len(sentence) - self.gram):
            self.increase(
                tuple(sentence[i:i+self.gram]), sentence[i+self.gram])
    
    def cache_machine(self):
        with open(DIAGRAM_SAVE, "wb") as f:
            pickle.dump(self.trans, file=f)

    def random_choose_weighted(self, key: tuple):
        tot = sum(self.trans.setdefault(key, {}).values())
        weight = tuple(
            elem/tot for elem in self.trans.setdefault(key, {}).values())
        return random.choices(list(self.trans.setdefault(key, {}).keys()), weights=weight, k=1)[0]

    def gen(self, ctx=None):
        if not ctx:
            state = [BOS for _ in range(self.gram)]
        else:
            ctx = list(ctx)
            ctx = ctx[-self.gram:]
            state = tuple([*[BOS for _ in range(self.gram-len(ctx))], *ctx])
        output = []
        while True:
            gen = self.random_choose_weighted(tuple(state))
            if gen == BOS:
                pass
            elif gen == EOS:
                output += "。"
            else:
                output += gen
            state = [*state[1:], gen]
            if gen == EOS:
                break
        return "".join(output)


machine = Markov()

markov = on_command("歪诗", rule = tracked_group_checker, priority=1)
group_message = on_message(rule=tracked_group_checker, priority=2)



@markov.handle()
async def handle_markov(matcher: Matcher, event: Event):
    message = machine.gen()
    await matcher.send(message)
    matcher.stop_propagation()


@group_message.handle()
async def handle_group(matcher: Matcher, event: Event, plain=EventPlainText()):
    plain = re.sub(r"\[.*?\]", "", plain)  # remove CQ Code
    plain = re.sub(r"&#[0-9]{1,3};", "", plain)  # remove escaped symbols
    segments = plain.split("\n")
    for segment in segments:
        raw_sentences = re.split(r"\.|。|\?|!|？|！", segment, flags=re.UNICODE)
        for raw_sentence in raw_sentences:
            if raw_sentence == "" or raw_sentence == " ":
                continue
            token_list = jieba.lcut(raw_sentence)
            machine.update(token_list)
    machine.cache_machine()
