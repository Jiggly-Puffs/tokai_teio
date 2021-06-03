# -*- coding: utf-8 -*-

import asyncio
import json
import time
import pprint
from derby import Derby
import logging
logger = logging.getLogger(__name__)


class UmaException(Exception):
    pass

class ShutdownHandler(logging.StreamHandler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            raise UmaException("Uma Error")


class Teio(object):

    def __init__(self):
        self.path = "data/derby.json"

    async def breeding(self, name=None, sex=None) -> Derby:
        derby = Derby()
        await derby.uma_signup()
        if name or sex:
            derby.set_name_sex(name, sex)
        await derby.uma_daily()
        self.save(derby.tojson())
        print(await derby.uma_info())
        return derby

    def save(self, data):
        open(self.path, "a+").write(data+"\n")

    async def daily(self):
        logger.info("Daily uma")
        num = 1
        with open(self.path, "r") as fp:
            for line in fp.readlines():
                logger.info("Uma %d" % num)
                data = json.loads(line)
                derby = Derby(data)
                await derby.uma_login()
                await derby.uma_daily()
                info = await derby.uma_info()

                logger.info("fcoin %d" % info["fcoin"])
                num += 1

    async def test_gacha(self):
        derby = await self.breeding()
        info = await derby.uma_gacha_strategy_three()
        logger.info("sc: %s" % (str(info["support_card_list"])))

    async def test(self):
        data = json.loads(open(self.path, "r").readlines()[-1])
        derby = Derby(data)
        await derby.uma_login()
        await derby.uma_daily()
        await derby.uma_support_card_limit_break_all()
        info = await derby.uma_info()
        logger.info("fcoin %d" % info["fcoin"])
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(info["support_card_list"])
        await derby.uma_account_trans("abcABC123")

    async def batch_breeding(self, num):
        for i in range(num):
            logger.info("Breeding uma %d" % (i+1))
            await self.breeding()
            await asyncio.sleep(3)

    async def gacha_login(self):
        num = 1
        with open(self.path, "r") as fp:
            for line in fp.readlines():
                logger.info("Uma %d" % num)
                data = json.loads(line)
                derby = Derby(data)
                await derby.uma_login()
                #derby.uma_daily()
                info = derby.uma_gacha_strategy(3)
                self.parse_gacha_info(info)
                num += 1
                if num > 50:
                    break

    def parse_gacha_info(self, info):
        sr = 0
        ssr = 0
        for sc in info["support_card_list"]:
            if sc["support_card_id"] > 20000:
                if sc["support_card_id"] > 30000:
                    ssr += sc["limit_break_count"] + sc["stock"] + 1
                else:
                    sr += sc["limit_break_count"] + sc["stock"] + 1
        logger.info("SSR: %d, SR: %d" % (ssr, sr))
        if ssr >= 6:
            for sc in info["support_card_list"]:
                if sc["support_card_id"] > 30000:
                    logger.info("%s" % str(sc))

    async def gacha_signup(self, num):
        for i in range(num):
            logger.info("Breeding uma %d" % (i+1))
            derby = await self.breeding()
            info = await derby.uma_gacha_strategy(4)
            self.parse_gacha_info(info)

async def job():
    teio = Teio()
    #teio.training()
    #teio.gacha_login()
    #teio.gacha_signup(10)
    #teio.test()
    for i in range(10):
        await teio.batch_breeding(500)
    #teio.daily()

    
async def main():
    jobs = []
    for i in range(20):
        jobs.append(job())
    await asyncio.gather(*jobs)
        

if __name__ == "__main__":
    # test
    import coloredlogs
    coloredlogs.install(logging.INFO)
    logging.getLogger().addHandler(ShutdownHandler())

    import dotenv
    dotenv.load_dotenv() # install .env into os.env

    asyncio.run(main())

