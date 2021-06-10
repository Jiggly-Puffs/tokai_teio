# -*- coding: utf-8 -*-

from .derby import Derby
import sqlite3
import logging
logger = logging.getLogger(__name__)


class Training(Derby):

    def __init__(self, client):
        self.client = client
        self.con = sqlite3.connect("./data/master.mdb")

    def __del__(self):
        self.con.close()

    async def get_account_info(self):
        resp = await self.client.post("/load/index")
        return resp["data"]

    def choose_training_uma(self, info):
        # choose least fan
        chara_list = sorted(info["chara_list"], key=lambda k: k["fan"])
        chara = chara_list[0]["chara_id"]
        for card in info["card_list"]:
            if card["card_id"] // 100 == chara:
                return card["card_id"]

    def choose_sc_cards(self, info, chara_id):
        sc_list = sorted(info["support_card_list"], key=lambda k:k["limit_break_count"]+(k["support_card_id"] // 10000), reverse=True)
        cur = self.con.cursor()
        sc_card_ids = []
        sc_chara_ids = []
        for sc in sc_list:
            cid = cur.execute("select chara_id from support_card_data where id= %d" % sc["support_card_id"]).fetchone()[0]
            if cid == (chara_id // 100):
                continue
            if cid in sc_chara_ids:
                continue
            sc_card_ids.append(sc["support_card_id"])
            sc_chara_ids.append(cid)
            if len(sc_card_ids) == 5:
                return sc_card_ids, sc_chara_ids

    def choose_succs(self, info, chara_id):
        trained = sorted(info["trained_chara"], key=lambda k: k["rank_score"], reverse=True)
        succs = []
        for tr in trained:
            if tr["card_id"] == chara_id:
                continue
            succs.append(tr["trained_chara_id"])
            if len(succs) == 2:
                return succs
        return succs

    async def choose_rental(self, chara_id, sc_chara_ids):
        resp = await self.client.post("/single_mode/rental_info")
        FRIEND_CARDS = [30016, 30028, 30021]
        sc_cards = resp["data"]["friend_support_card_data"]["support_card_data_array"]
        sc_cards = sorted(sc_cards, key=lambda k:k["limit_break_count"]+(k["support_card_id"] // 10000), reverse=True)
        cur = self.con.cursor()
        for sc in sc_cards:
            cid = cur.execute("select chara_id from support_card_data where id= %d" % sc["support_card_id"]).fetchone()[0]
            if cid == (chara_id // 100):
                continue
            if cid in sc_chara_ids:
                continue
            if sc["support_card_id"] in FRIEND_CARDS and sc["limit_break_count"] > 2:
                return {"viewer_id": sc["viewer_id"], "support_card_id": sc["support_card_id"]}
        for sc in sc_cards:
            cid = cur.execute("select chara_id from support_card_data where id= %d" % sc["support_card_id"]).fetchone()[0]
            if cid == (chara_id // 100):
                continue
            if cid in sc_chara_ids:
                continue
            return {"viewer_id": sc["viewer_id"], "support_card_id": sc["support_card_id"]}

    async def single_mode_prepare(self, chara_id, sc_list, succ):
        info = await self.get_account_info()
        if not chara_id:
            chara_id = self.choose_training_uma(info)
        if not sc_list:
            support_card_ids, sc_chara_ids = self.choose_sc_cards(info, chara_id)
        if not succ:
            succ = self.choose_succs(info, chara_id)

        logger.debug("card_id %d" % chara_id)
        logger.debug("sc: %s" % str(support_card_ids))

        money = 0
        for item in info["item_list"]:
            if item["item_id"] == 59:
                money = item["number"]
                break
        friend_info = await self.choose_rental(chara_id, sc_chara_ids)

        start_chara = {}
        start_chara["card_id"] = chara_id
        start_chara["support_card_ids"] = support_card_ids
        start_chara["friend_support_card_info"] = friend_info
        start_chara["succession_trained_chara_id_1"] = succ[0]
        start_chara["succession_trained_chara_id_2"] = succ[1]
        start_chara["rental_succession_trained_chara"] = {"viewer_id": 0, "trained_chara_id": 0, "is_circle_member": False}
        start_chara["scenario_id"] = 1
        start_chara["selected_difficulty_info"] = {"difficulty_id": 0, "difficulty": 0}
        start_chara["select_deck_id"] = 1


        data = {}
        data["start_chara"] = start_chara
        data["tp_info"] = info["tp_info"]
        data["current_money"] = money
        resp = await self.client.post("/single_mode/start", data)

        # support card deck array
        data = {}
        data["support_card_deck_array"] = []
        deck= {}
        deck["deck_id"] = 1
        deck["support_card_id_array"] = support_card_ids
        for i in range(2, 11):
            deck = {}
            deck["deck_id"] = i
            deck["support_card_id_array"] = [0, 0, 0, 0, 0]
            data["support_card_deck_array"].append(deck)
        await self.client.post("/support_card_deck/change_party", data)

        # short_cut
        data = {}
        data["short_cut_state"] = 1
        data["current_turn"] = 1
        resp = await self.client.post("/single_mode/change_short_cut", data)

        return resp["data"]

    def single_mode_check_route(self, info):
        chara_id = info["chara_info"]["card_id"] // 100
        cur = self.con.cursor()
        races = cur.execute("select turn, condition_id from single_mode_route_race where race_set_id= %d" % chara_id).fetchall()
        routes = []
        for r in races:
            print(r)
            route = {}
            route["program_id"] = r[1]
            route["turn"] = r[0]
            if r[1] > 10000:
                route["fans"] = 0
            else:
                route["fans"] = cur.execute("select need_fan_count from single_mode_program where id = %d" % r[1]).fetchone()[0]
            routes.append(route)
        return sorted(routes, key=lambda k:k["turn"])

    async def check_event(self, event, turn):
        data = {}
        data["event_id"] = event["event_id"]
        data["chara_id"] = event["chara_id"]
        # FIXME: always choose first option
        data["choice_number"] = 0
        data["current_turn"] = turn
        resp = await self.client.post("/single_mode/check_event", data)
        return resp["data"]

    async def do_minigame(self, turn):
        # FIXME: add more result value to gain rest & skills
        data = {}
        data["result"] = {}
        data["result"]["result_state"] = 2
        data["result"]["result_value"] = 2
        data["result"]["result_detail_array"] = [{"get_id": 0, "chara_id": 1002, "dress_id": 2, "motion": "Catch11", "face": "WaraiD"}]
        data["current_turn"] = turn
        resp = await self.client.post("/single_mode/minigame_end", data)
        return resp["data"]

    async def single_mode_check_event(self, data):
        while data.get("unchecked_event_array"):
            event = data["unchecked_event_array"][0]
            data = await self.check_event(event, data["chara_info"]["turn"])
            # minigame
            if event["event_id"] == 6002:
                data = await self.do_minigame(data["chara_info"]["turn"])
        return data

    async def single_mode_exec_cmd(self, info):
        chara_info = info["chara_info"]
        cmds = sorted(info["home_info"]["command_info_array"], key=lambda k:k["command_id"], reverse=True)
        turn = chara_info["turn"]
        mycmd = {}
        for cmd in cmds:
            if cmd["is_enable"] == 0:
                continue
            # health romm
            if cmd["command_id"] == 801:
                mycmd = cmd
                break
            # rest room
            if chara_info["vital"] < 28 and cmd["command_id"] == 701:
                mycmd = cmd
                break
            # go out
            if chara_info["motivation"] < 3 and cmd["command_id"] == 301:
                mycmd["command_type"] = 3
                mycmd["command_id"] = 0
                mycmd["command_group_id"] = 301
                break
            # sea rest room
            if chara_info["vital"] < 28 and cmd["command_id"] == 304:
                mycmd["command_type"] = 3
                mycmd["command_id"] = 0
                mycmd["command_group_id"] = 304
                break

        if not mycmd:
            cmds = sorted(cmds, key=lambda k:k["training_partner_array"], reverse=True)
            # FIXME: more AI mode to choose cmd wisely
            speed = chara_info["speed"]
            stamina = chara_info["stamina"]
            power = chara_info["power"]
            is_speed = is_stamina = is_power = False
            min_val = min(speed, stamina, power)
            if min_val == speed and (speed + turn * 6 < stamina + power):
                is_speed = True
            if min_val == stamina and (stamina + turn * 6 < speed + power):
                is_stamina = True
            if min_val == power and (power + turn * 6 < stamina + speed):
                is_power = True
            for cmd in cmds:
                if cmd["is_enable"] == 0:
                    continue
                if (cmd["command_id"] // 100 != 1) and (cmd["command_id"] // 100 != 6):
                    continue
                if not is_speed and not is_stamina and not is_power:
                    if cmd["training_partner_array"] < 4 and (cmd["command_id"] % 100 == 3):
                        continue
                    mycmd = cmd
                    break
                if is_speed and (cmd["command_id"] % 100 == 1):
                    mycmd = cmd
                    break
                if is_stamina and (cmd["command_id"] % 100 == 5):
                    mycmd = cmd
                    break
                if is_power and (cmd["command_id"] % 100 == 2):
                    mycmd = cmd
                    break

        if not mycmd: # maybe disable
            cmds = sorted(cmds, key=lambda k:k["is_enable"], reverse=True)
            for cmd in cmds:
                if cmd["is_enable"] == 0:
                    continue
                if (cmd["command_id"] // 100 == 3) or (cmd["command_id"] // 100 == 4):
                    continue
                mycmd = cmd
                break

        if not mycmd:
            logger.error("cannot find cmd: %s" % str(cmds))

        data = {}
        data["command_type"] = mycmd["command_type"]
        data["command_id"] = mycmd["command_id"]
        data["command_group_id"] = mycmd.get("command_group_id", 0)
        data["select_id"] = 0
        data["current_turn"] = turn
        data["current_vital"] = chara_info["vital"]
        resp = await self.client.post("/single_mode/exec_command", data)
        return resp["data"]

    async def single_mode_run_race(self, program_id, turn):
        data = {}
        data["program_id"] = program_id
        data["current_turn"] = turn
        resp = await self.client.post("/single_mode/race_entry", data)

        data = await self.single_mode_check_event(resp["data"])

        data = {}
        data["is_short"] = 1
        data["current_turn"] = turn
        resp = await self.client.post("/single_mode/race_start", data)

        data = {}
        data["current_turn"] = turn
        resp = await self.client.post("/single_mode/race_end", data)

        if resp["data"]["add_music"]:
            # FIXME: obtain live
            # /live/live_start
            pass

        data = {}
        data["current_turn"] = turn
        resp = await self.client.post("/single_mode/race_out", data)

        data = await self.single_mode_check_event(resp["data"])
        return data

    def choose_race(self, info, need_run, race_property):
        chara_info = info["chara_info"]
        races = info["race_condition_array"]
        chara_id = info["chara_info"]["card_id"] // 100
        cur = self.con.cursor()
        choose_race_id = None
        run_races = []
        for race in races:
            programs = cur.execute("select race_instance_id, need_fan_count from single_mode_program where id = %d" % race["program_id"]).fetchone()
            if chara_info["fans"] < programs[1]:
                continue
            race_id = cur.execute("select race_id from race_instance where id = %d" % programs[0]).fetchone()[0]
            race_grade = cur.execute("select grade, course_set from race where id = %d" % race_id).fetchone()
            course_set = cur.execute("select distance, ground from race_course_set where id = %d" % race_grade[1]).fetchone()

            if course_set[1] == 1 and not race_property.get("turf", False): # turf
                continue
            if course_set[1] == 2 and not race_property.get("dirt", False): # dirt
                continue
            if course_set[0] >= 2400 and not race_property.get("long", False):
                continue
            if 1800 < course_set[0] <= 2400 and not race_property.get("middle", False):
                continue
            if 1400 < course_set[0] <= 1800 and not race_property.get("mile", False):
                continue
            if course_set[0] <= 1400 and not race_property.get("short", False):
                continue
            r = {}
            r["grade"] = race_grade[0]
            r["program_id"] = race["program_id"]
            run_races.append(r)

        if run_races:
            choose_race_id = sorted(run_races, key=lambda k:k["grade"])[0]["program_id"]

        if need_run and not choose_race_id:
            # choose first race
            choose_race_id = races[0]["program_id"]
        return choose_race_id

    async def single_mode_gain_skill(self, info, turn):
        skill_point = info["chara_info"]["skill_point"]
        skill_tips = info["chara_info"]["skill_tips_array"]
        if not skill_tips:
            return
        got_skills = []
        for sk in info["chara_info"]["skill_array"]:
            got_skills.append(sk["skill_id"])
        cur = self.con.cursor()
        gain_skills = []
        # FIXME: random choose skill
        count = 0
        while True:
            skill_tip = skill_tips[random.randint(0, len(skill_tips)-1)]
            sk_info = cur.execute("select id, rarity from skill_data where group_id = %d" % skill_tip["group_id"]).fetchall()
            sk_info.reverse()
            logger.debug(str(sk_info))
            if not sk_info or len(sk_info) > 2:
                count += 1
                if count > (len(skill_tips) // 3):
                    break
                continue
            for sk in sk_info:
                if sk[1] > skill_tip["rarity"]:
                    continue
                if sk[0] in got_skills:
                    continue
                point = cur.execute("select need_skill_point from single_mode_skill_need_point where id = %d" % sk[0]).fetchone()[0]
                if point and point <= skill_point:
                    skill = {}
                    skill["skill_id"] = sk[0]
                    skill["level"] = skill_tip["level"]
                    gain_skills.append(skill)
                    skill_point -= point
                    if skill_point < 50:
                        break
            count += 1
            if count > (len(skill_tips) // 3):
                break
        if gain_skills:
            data = {}
            data["gain_skill_info_array"] = gain_skills
            data["current_turn"] = turn
            await self.client.post("/single_mode/gain_skills", data)

    async def single_mode_finish(self, info):
        turn = info["chara_info"]["turn"]
        await self.single_mode_gain_skill(info, turn)

        data = {}
        data["is_force_delete"] = False
        data["current_turn"] = turn
        resp = await self.client.post("/single_mode/finish", data)
        info = resp["data"]

        friend_viewer_id = 0
        for sc in info["chara_info"]["support_card_array"]:
            if sc["owner_viewer_id"] != 0:
                friend_viewer_id = sc["owner_viewer_id"]
                break

        # change nick name
        data = {}
        data["trained_chara_id"] = info["directory_card_array"][0]["trained_chara"]["trained_chara_id"]
        data["nickname_id"] = info["chara_info"]["nickname_id_array"][0]
        resp = await self.client.post("/trained_chara/change_nickname", data)

        '''
        # FIXME: ignore friend search now
        data = {}
        data["friend_viewer_id"] = friend_viewer_id
        resp = await self.client.post("/friend/search", data)
        '''

    def detect_race_property(self, info):
        # distance, ground
        race_property = {}
        chara_info = info["chara_info"]
        if chara_info["proper_distance_long"] >= 7:
            race_property["long"] = True
        if chara_info["proper_distance_middle"] >= 7:
            race_property["middle"] = True
        if chara_info["proper_distance_mile"] >= 7:
            race_property["mile"] = True
        if chara_info["proper_distance_short"] >= 7:
            race_property["short"] = True
        if chara_info["proper_ground_dirt"] >= 6:
            race_property["dirt"] = True
        if chara_info["proper_ground_turf"] >= 6:
            race_property["turf"] = True
        return race_property

    async def run(self, chara_id=None, sc_list=[], succ=[]):
        data = await self.single_mode_prepare(chara_id, sc_list, succ)
        routes = self.single_mode_check_route(data)
        race_property = self.detect_race_property(data)
        route_num = 0
        while True:
            data = await self.single_mode_check_event(data)
            turn = data["chara_info"]["turn"]
            if routes[route_num]["turn"] == turn:
                # obtain skill
                if routes[route_num]["program_id"]:
                    # race target, not fan target
                    if turn > 20:
                        await self.single_mode_gain_skill(data, turn)
                    data = await self.single_mode_run_race(routes[route_num]["program_id"], turn)
                route_num += 1
            else:
                fans = data["chara_info"]["fans"]
                race_id = None
                if fans < routes[route_num]["fans"]:
                    need_fans = routes[route_num]["fans"] - fans
                    if ((need_fans+1000) // 1000) >= (routes[route_num]["turn"] - turn):
                        need_run = ((turn+1) == routes[route_num]["turn"])
                        race_id = self.choose_race(data, need_run, race_property)
                if race_id:
                    logger.debug("choose race_id %s" % race_id)
                    data = await self.single_mode_run_race(race_id, turn)
                else:
                    data = await self.single_mode_exec_cmd(data)
            # failed
            if data["chara_info"]["state"] == 2:
                break
        # finish
        await self.single_mode_finish(data)

