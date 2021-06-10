# -*- coding: utf-8 -*-

from .derby import Derby
from hashlib import md5


class Account(Derby):

    def __init__(self, client):
        self.client = client

    def __del__(self):
        pass

    async def account_trans(self, password):
        self.password = password
        data = {}
        data["password"] = md5((password+"r!I@mt8e5i=").encode("utf8")).hexdigest()
        await self.client.post("/account/publish_transition_code", data)

    async def run(self, password):
    	self.account_trans(password)
    	logger.info("update account %s password: %s" % (client.viewer_id, password))