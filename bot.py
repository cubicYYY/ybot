### simple bot for zjuer
#TODO: statistics in QQ group
#TODO: QQ group word cloud!
#TODO: bilibili liveroom tracking
#TODO: bilibili follow tracking
#TODO: recapture of drawbacked messages
import asyncio
import multiprocessing

import nonebot
import sqlite3
import time
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
    from plugins.apexlegends import init_track, fetch_current_rankscore, apexbind_infos,CUR_SEASON, CUR_SPLIT, PERIOD_KEY, DATABASE_FILE
    async def _track_apex_data(): #TODO: Refactor it into a separated module to handle apex updates
        print(":)")
        db = sqlite3.connect(DATABASE_FILE)
        cursor = db.cursor()
        last_score = {}
        
        # init for all accounts every season
        for struid in apexbind_infos["tracked"]:
            uid = int(struid)
            apexbind_infos["initialized"].setdefault(PERIOD_KEY,(lambda :[])())
            if uid not in apexbind_infos["initialized"][PERIOD_KEY]:
                await init_track(uid)
                time.sleep(30)
            
        while True:
            for struid in apexbind_infos["tracked"]:
                uid = int(struid)
                
                if uid not in last_score.keys():
                    cursor.execute("SELECT score FROM data WHERE uid=? AND season=? AND split=? ORDER BY timestamp DESC, id DESC", (uid, CUR_SEASON, CUR_SPLIT))
                    row = cursor.fetchone()
                    if row:
                        last_score[uid] = int(row[0])
                    
                score = await fetch_current_rankscore(uid)
                if uid not in last_score.keys() or score != last_score[uid]:
                    print(f"!update{uid}")
                    cursor.execute("INSERT INTO data (score,uid,season,split) VALUES (?,?,?,?)", 
                                    (score, uid, CUR_SEASON, CUR_SPLIT))
                    db.commit()
                    last_score[uid] = score
                time.sleep(1)
                
    def track_apex_data():
        asyncio.run(_track_apex_data())
    fetch_process = multiprocessing.Process(target=track_apex_data)
    fetch_process.daemon = True  # Set the process as daemon
    # Start the process
    fetch_process.start()
    nonebot.run()
