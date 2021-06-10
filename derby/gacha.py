# -*- coding: utf-8 -*-

from .derby import Derby
import logging
import asyncio
logger = logging.getLogger(__name__)


class Gacha(Derby):

    def __init__(self, client):
        self.client = client

    def __del__(self):
        pass

    async def get_account_info(self):
        resp = await self.client.post("/load/index")
        return resp["data"]

    async def get_gacha_info(self):
        resp = await self.client.post("/gacha/index")
        return resp["data"]["gacha_info_list"]

    async def gacha_exec(self, gacha_id, num, fcoin):
        data = {}
        data["gacha_id"] = gacha_id
        data["draw_type"] = 1
        data["draw_num"] = num
        data["current_num"] = fcoin
        data["item_id"] = 0
        resp = await self.client.post("/gacha/exec", data)

    def gacha_find_pool(self, gachas, category):
        for gacha in gachas:
            # category: 0: uma pool / 1: support card pool
            if ((gacha["id"] // 10000) == 3) and ((gacha["id"] % 2) == category):
                return gacha["id"]
        return None

    async def gacha_pulls(self, pulls, well=1, times=None, category=1):
        coins = (pulls * 150) * well
        fcoin = (await self.get_account_info())["coin_info"]["fcoin"]
        coin_times = fcoin // coins
        if not times:
            times = coin_times
        if coin_times < times:
            logger.error("No enough fcoin: %d" % fcoin)
        logger.info("To Gacha %d (one: %d)" % (times, coins))
        gachas = await self.get_gacha_info()
        gacha_id = self.gacha_find_pool(gachas, category)
        if gacha_id:
            for i in range(times):
                for j in range(well):
                    await self.gacha_exec(gacha_id, pulls, fcoin)
                    fcoin -= (pulls * 150)
                    await asyncio.sleep(3) # otherwise will trigger 208 fault ( DOUBLE_CLICK_ERROR )

    async def run(self, mode, pulls=None):
        if mode == 1:
            # one well to support card gacha
            await self.gacha_pulls(10, 20)
        elif mode == 2:
            # 10 pulls to support card gacha
            await self.gacha_pulls(10)
        elif mode == 3:
            # first ten pull, later one pull
            await self.gacha_pulls(10)
            await self.gacha_pulls(1)
        elif mode == 4:
            # single pull
            await self.gacha_pulls(1)
        else:
            await self.gacha_pulls(pulls[0], pulls[1], pulls[2], pulls[3])
