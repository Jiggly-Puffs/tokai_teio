# -*- coding: utf-8 -*-

from .derby import Derby


class Gifts(Derby):

    def __init__(self, client):
        self.client = client

    def __del__(self):
        pass

    def parse_mission(self, resp):
        data = resp["data"]
        m = []
        if data.get("mission_list"):
            missions = data.get("mission_list")
            for mis in missions:
                if mis["mission_status"] == 1:
                    m.append(mis["mission_id"])
        return m

    async def run(self):
        # get mission & receive mission_gift
        resp = await self.client.post("/mission/index")
        missions = self.parse_mission(resp)

        if missions:
            data = {}
            data['mission_id_array'] = missions
            resp = await self.client.post("/mission/receive", data)

        # receive gifts
        data = {}
        data["time_filter_type"] = 0
        data["category_filter_type"] = [0]
        data["offset"] = 0
        data["limit"] = 100
        data["is_asc"] = True
        resp = await self.client.post("/present/index", data)

        data = {}
        data["time_filter_type"] = 0
        data["category_filter_type"] = [0]
        data["is_asc"] = True
        resp = await self.client.post("/present/receive_all", data)
