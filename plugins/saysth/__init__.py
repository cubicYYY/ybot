from nonebot import get_driver
# from nonebot.rule import to_me
from nonebot.params import EventPlainText
from nonebot.plugin import on_command

from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

START_KEY_WORD = "说话！"
echo = on_command(START_KEY_WORD)


@echo.handle()
async def handle_echo(message: str = EventPlainText()):
    plain_text = message.lstrip(START_KEY_WORD)
    plain_text = plain_text.replace('是不是','就是')
    plain_text = plain_text.replace('_TMP_ME_CONSTANT_','')
    plain_text = plain_text.replace('我','_TMP_ME_CONSTANT_')
    plain_text = plain_text.replace('你','我')
    plain_text = plain_text.replace('_TMP_ME_CONSTANT_','你')
    plain_text += "!"
    await echo.send(message=plain_text)
