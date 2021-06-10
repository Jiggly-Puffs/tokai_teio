# -*- coding: utf-8 -*-

from .derby import Derby


class TeamRace(Derby):

    def __init__(self, client):
        self.client = client

    def __del__(self):
        pass

    async def get_account_info(self):
        resp = await self.client.post("/load/index")
        return resp["data"]

    def gen_team_array(self, trained_chara, choosed_chara, distance):
        tr = None
        for t in trained_chara:
            if t["card_id"] in choosed_chara:
                continue
            tr = t
            break
        arr = []
        for i in range(3):
            member = {}
            member["distance_type"] = distance
            member["member_id"] = i + 1
            if i == 0:
                member["trained_chara_id"] = tr["trained_chara_id"]
                style = [tr["proper_running_style_nige"], tr["proper_running_style_oikomi"], tr["proper_running_style_sashi"], tr["proper_running_style_senko"]]
                member["running_style"] = style.index(max(style)) + 1
            else:
                member["trained_chara_id"] = 0
                member["running_style"] = 0
            arr.append(member)
        return tr, arr

    async def team_stadium_edit(self):
        info = await self.get_account_info()
        score = 0
        teams = []
        choosed_chara = []
        # dirt first
        trained_chara = sorted(info["trained_chara"], key=lambda k:(k["proper_ground_dirt"] // 6) * 10000 + k["rank_score"], reverse=True)
        tr, arr = self.gen_team_array(trained_chara, choosed_chara, 5)
        score += tr["rank_score"]
        teams.extend(arr)
        choosed_chara.append(tr["card_id"])

        trained_chara = sorted(trained_chara, key=lambda k:(k["proper_distance_short"] // 6) * 10000 + k["rank_score"], reverse=True)
        tr, arr = self.gen_team_array(trained_chara, choosed_chara, 1)
        score += tr["rank_score"]
        teams.extend(arr)
        choosed_chara.append(tr["card_id"])

        trained_chara = sorted(trained_chara, key=lambda k:(k["proper_distance_mile"] // 6) * 10000 + k["rank_score"], reverse=True)
        tr, arr = self.gen_team_array(trained_chara, choosed_chara, 2)
        score += tr["rank_score"]
        teams.extend(arr)
        choosed_chara.append(tr["card_id"])

        trained_chara = sorted(trained_chara, key=lambda k:(k["proper_distance_middle"] // 6) * 10000 + k["rank_score"], reverse=True)
        tr, arr = self.gen_team_array(trained_chara, choosed_chara, 3)
        score += tr["rank_score"]
        teams.extend(arr)
        choosed_chara.append(tr["card_id"])

        trained_chara = sorted(trained_chara, key=lambda k:(k["proper_distance_long"] // 6) * 10000 + k["rank_score"], reverse=True)
        tr, arr = self.gen_team_array(trained_chara, choosed_chara, 4)
        score += tr["rank_score"]
        teams.extend(arr)
        choosed_chara.append(tr["card_id"])

        data = {}
        data["team_data_array"] = teams
        data["team_evaluation_point"] = score
        await self.client.post("/team_stadium/team_edit", data)

    async def run(self, edit=False):
        await self.client.post("/team_stadium/index")

        # team edit
        if edit:
            await self.team_stadium_edit()

        resp = await self.client.post("/team_stadium/opponent_list")

        data = {}
        resp["data"]["opponent_info_array"][-1].pop(None)
        data["opponent_info"] = resp["data"]["opponent_info_array"][-1]
        await self.client.post("/team_stadium/decide_frame_order", data)

        data = {}
        data["item_id_array"] = []
        await self.client.post("/team_stadium/start", data)

        for i in range(5):
            data = {}
            data["round"] = i + 1
            await self.client.post("/team_stadium/replay_check", data)

        await self.client.post("/team_stadium/all_race_end")



