### simple bot for zjuer
#TODO: statistics in QQ group
#TODO: QQ group word cloud!
#TODO: divination
#TODO: bilibili liveroom tracking
#TODO: bilibili follow tracking
#TODO: recapture of drawbacked messages
# TODO: QQ/username/password binding
# TODO: infos in the form of images
# TODO: Teacher rankings with candidate list
import nonebot
#from nonebot.adapters.telegram import Adapter as TELEGRAMAdapter
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter

#from nonebot.adapters.console import Adapter as CONSOLEAdapter

# from nonebot.adapters.spigot import Adapter as SPIGOTAdapter



nonebot.init()

driver = nonebot.get_driver()
#driver.register_adapter(TELEGRAMAdapter)

driver.register_adapter(ONEBOT_V11Adapter)

#driver.register_adapter(CONSOLEAdapter)

# driver.register_adapter(SPIGOTAdapter)

# nonebot.load_builtin_plugins('echo')
nonebot.load_plugins('./plugins')

nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":
    nonebot.run()
