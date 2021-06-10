# -*- coding: utf-8 -*-

from .derby import Derby
import logging
logger = logging.getLogger(__name__)


class SupportCard(Derby):

    def __init__(self, client):
        self.client = client

    def __del__(self):
        pass

    async def get_account_info(self):
        resp = await self.client.post("/load/index")
        return resp["data"]

    async def uma_support_card_limit_break(self, support_card_id):
        logger.debug("Support card %d limit break" % support_card_id)
        data = {}
        data["support_card_id"] = support_card_id
        data["material_support_card_num"] = 1
        resp = await self.client.post("/support_card/limit_break", data)

    async def uma_support_card_limit_break_all(self):
        support_cards = (await self.get_account_info())["support_card_list"]
        for sc in support_cards:
            for i in range(sc["stock"]):
                if i + sc["limit_break_count"] >= 4:
                    logger.warning("support card %d: %d" % (sc["support_card_id"], sc["stock"]+sc["limit_break_count"]+1))
                    break
                await self.uma_support_card_limit_break(sc["support_card_id"])
                await asyncio.sleep(1) # otherwise will trigger 208 fault ( DOUBLE_CLICK_ERROR )

    async def run(self):
    	self.uma_support_card_limit_break_all()
    	# maybe do level up later