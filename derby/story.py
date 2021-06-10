# -*- coding: utf-8 -*-

from .derby import Derby
import sqlite3
import asyncio


class Reading(Derby):

    def __init__(self, client):
        self.client = client
        self.con = sqlite3.connect("./data/master.mdb")

    def __del__(self):
        self.con.close()

    async def get_account_info(self):
        resp = await self.client.post("/load/index")
        return resp["data"]

    async def read_chara_story(self, episode_id):
        data = {}
        data["episode_id"] = episode_id
        await self.client.post("/character_story/first_clear", data)

    async def run(self):
        data = {}
        data["add_home_story_data_array"] = []
        data["add_short_episode_data_array"] = []
        data["add_home_poster_data_array"] = []
        data["add_tutorial_guide_data_array"] = []
        data["add_released_episode_data_array"] = []
        resp = await self.client.post("/read_info/index", data)
        read_stories = sorted(resp["data"]["released_episode_data_array"], key=lambda k:k["id"], reverse=True)

        info = await self.get_account_info()
        charas = info["chara_list"]
        cur = self.con.cursor()
        for chara in charas:
            stories = cur.execute("select id, story_id from chara_story_data where chara_id = %d and episode_index < 5" % chara["chara_id"]).fetchall()
            for story in stories:
                if story[1] in read_stories:
                    continue
                await self.uma_read_chara_story(story[0])
                await asyncio.sleep(0.5)
