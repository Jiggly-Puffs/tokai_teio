# -*- coding: utf-8 -*-

import os
import uuid
import json
import time
import httpx
import base64
import random
import string
import struct
import codecs
import sqlite3
import msgpack
import secrets
import asyncio
import tempfile
from hashlib import md5
from utils.constant import RESPCODE

import logging
logger = logging.getLogger(__name__)


UMA_URL = "https://api-umamusume.cygames.jp/umamusume"
APP_VER = "1.4.0"
RES_VER = "10001520:TdKTHfQLd73S"
UMA_PUBKEY = "6b20e2ab6c311330f761d737ce3f3025750850665eea58b6372f8d2f57501eb348ee86c2de2699100d32f9e07dbfccb9a8fe658b"

USER_AGENT = "Mozilla/5.0 (Linux; Android 10; SM-A102U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36"


class UmaProto(object):

    def __init__(self, cert_uuid, session_id, viewer_id=0, auth_key=None):
        self.cert_uuid = cert_uuid
        self.session_id = session_id
        self.viewer_id = viewer_id
        self.auth_key = auth_key
        self.tmp_dir = tempfile.TemporaryDirectory(prefix="UmaProto")
        print(self.tmp_dir.name)

    def __del__(self):
        self.tmp_dir.cleanup()

    def set_viewer_id(self, viewer_id):
        self.viewer_id = viewer_id

    def set_auth_key(self, auth_key):
        self.auth_key = auth_key

    def con_req(self, req):
        data = codecs.decode(UMA_PUBKEY, "hex")
        data += self.session_id
        data += self.cert_uuid
        data += secrets.token_bytes(32)
        if self.auth_key:
            data += self.auth_key
        data = struct.pack("<I", len(data)) + data
        data += msgpack.packb(req)
        return self.compress(data)

    def compress(self, data):
        open(f"{self.tmp_dir.name}/req", "wb").write(data)
        os.system(f"./utils/proto 0 {self.tmp_dir.name}")
        return base64.b64encode(open(f"{self.tmp_dir.name}/req.enc", "rb").read())

    def decompress(self, data):
        open(f"{self.tmp_dir.name}/resp", "wb").write(base64.b64decode(data.strip()))
        os.system(f"./utils/proto 1 {self.tmp_dir.name}")
        return open(f"{self.tmp_dir.name}/resp.dec", "rb").read()

    def con_headers(self):
        headers = {
            "SID": self.session_id.hex(),
            "APP-VER": APP_VER,
            "RES-VER": RES_VER,
            "Content-Type": "application/x-msgpack",
            "ViewerID": str(self.viewer_id),
            "User-agent": USER_AGENT,
        }
        return headers

    def update_session_id(self, resp):
        logger.debug("RESP: %s" % str(resp))
        if resp.get("data_headers"):
            data_headers = resp["data_headers"]
            if data_headers.get("sid"):
                self.session_id = md5(data_headers.get("sid").encode("utf8") + b'r!I@mt8e5i=').digest()
        # update session_id first if we want to continue after error
        if resp["response_code"] != 1:
            logger.error("ERROR RESPONSE_CODE %s: %s!!!" % (resp["response_code"], RESPCODE(resp["response_code"]).name))

    async def post(self, url, data):
        time.sleep(0.1) # avoid double click
        url = UMA_URL + url
        logger.info("URL: %s" % url)
        headers = self.con_headers()
        logger.debug("Headers: %s" % str(headers))
        logger.debug("Req: %s" % data)
        req = self.con_req(data)
        while True:
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.post(url, content=req, headers=headers)
                break
            except Exception as e:
                logger.warning(str(e))
                await asyncio.sleep(1)
        if r.status_code != 200:
            logger.error("url: %s\n Error code: %d" % (url, r.status_code))
        try:
            resp = msgpack.unpackb(self.decompress(r.text), raw=False)
        except msgpack.ExtraData as e:
            logger.warn("msgpack ExtraData")
            resp = e.args[0] # ExtraData(ret, unpacker._get_extradata())
        self.update_session_id(resp)
        return resp


class Derby(object):

    def __init__(self, data=None):
        if data:
            self.load(data)
        else:
            self.uma_init()  # generate a new account

        self.proto = UmaProto(self.cert_uuid, self.session_id, self.viewer_id, self.auth_key)
        #self.omotenashi()

    def load(self, data):
        self.app_viewer_id = data["app_viewer_id"]
        self.device_info = data["device_info"]
        self.firebase = data["firebase"]
        self.viewer_id = self.device_info["viewer_id"]
        self.auth_key = base64.b64decode(data["auth_key"])
        self.password = data.get("password", "")
        self.gen_session_id()

    def tojson(self):
        data = {}
        data["app_viewer_id"] = self.app_viewer_id
        data["device_info"] = self.device_info
        data["firebase"] = self.firebase

        assert self.auth_key is not None
        data["auth_key"] = base64.b64encode(self.auth_key).decode("utf8")
        data["password"] = self.password
        return json.dumps(data)

    def set_name_sex(self, name, sex):
        if name:
            self.name = name
        if sex:
            self.sex = sex

    def gen_device_info(self):
        BRANDS = ["Samsung", "Xiaomi", "Sony", "Sharp", "Toshiba", "Google", "Casio", "Fujitsu", "HP", "Lenovo", "LG", "Panasonic", "Kyocera", "DoCoMo"]
        brand = BRANDS[random.randint(0, len(BRANDS)-1)]
        device_id = codecs.encode(secrets.token_bytes(16), "hex").decode("utf8")
        self.device_info = {
            "viewer_id": 0,
            "device": 2,
            "device_id": device_id,
            "device_name": brand + " " + "".join(random.choice(string.ascii_uppercase) for i in range(random.randint(6, 8))),
            "graphics_device_name": "Mali-G57",
            "ip_address": "192.168." + str(random.randint(0, 254)) + "." + str(random.randint(1, 254)),
            "platform_os_version": "Android OS 10 / API-29 (QP1A.190711.020/V12.0.7.0.QJHCNXM)",
            "carrier": brand,
            "keychain": 0,
            "locale": "JPN",
            "dmm_viewer_id": None,
            "dmm_onetime_token": None,
        }

    def gen_session_id(self):
        self.cert_uuid = codecs.decode(self.app_viewer_id.replace("-", ""), "hex")
        self.session_id = md5((str(self.viewer_id) + self.app_viewer_id + 'r!I@mt8e5i=').encode("utf8")).digest()

    def uma_init(self):
        self.viewer_id = 0
        self.app_viewer_id = str(uuid.uuid4())
        logger.debug("app_viewer_id: %s" % self.app_viewer_id)
        self.gen_session_id()
        self.name = ''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(3, 10)))
        self.sex = random.randint(1, 2)
        self.gen_device_info()
        self.firebase = {}
        self.auth_key = None
        self.password = ""

    def omotenashi(self):
        from omotenashi.omotenashi import Omotenashi
        omo = Omotenashi(self.app_viewer_id, APP_VER)
        if self.firebase:
            omo.update()
        else:
            omo.register()

    def parse_signup_info(self, resp):
        if resp.get("data"):
            data = resp["data"]
            if data.get("viewer_id"):
                if data["viewer_id"] != self.viewer_id:
                    self.viewer_id = data["viewer_id"]
                    self.device_info["viewer_id"] = self.viewer_id
                    self.proto.set_viewer_id(self.viewer_id)
            if data.get("auth_key"):
                self.auth_key = base64.b64decode(data["auth_key"])
                self.proto.set_auth_key(self.auth_key)

    def parse_res_ver(self, resp):
        if resp.get("data"):
            data = resp["data"]
            if data.get("resource_version"):
                global RES_VER
                if data["resource_version"] != RES_VER:
                    RES_VER = data["resource_version"]
                    logger.warning("NEW RES-VER: %s" % RES_VER)

    def parse_gacha(self, resp):
        return resp["data"]["gacha_info_list"]

    @staticmethod
    def parse_info(resp):
        data = resp["data"]
        info = {}
        info["fcoin"] = data["coin_info"]["fcoin"]
        info["card_list"] = data["card_list"]
        info["support_card_list"] = data["support_card_list"]
        #logger.info("FCOIN %d" % info["fcoin"])
        return info

    @staticmethod
    def parse_mission(resp):
        data = resp["data"]
        m = []
        if data.get("mission_list"):
            missions = data.get("mission_list")
            for mis in missions:
                if mis["mission_status"] == 1:
                    m.append(mis["mission_id"])
        return m

    async def uma_signup(self):
        data = self.device_info.copy()
        resp = await self.proto.post("/tool/pre_signup", data)

        data = self.device_info.copy()
        data["credential"] = ""
        data["error_code"] = 0
        data["error_message"] = ""
        resp = await self.proto.post("/tool/signup", data)
        self.parse_signup_info(resp)

        data = self.device_info.copy()
        resp = await self.proto.post("/tool/start_session", data)
        self.parse_res_ver(resp)

        data = self.device_info.copy()
        resp = await self.proto.post("/load/index", data)

        data = self.device_info.copy()
        data["name"] = self.name
        resp = await self.proto.post("/user/change_name", data)

        data = self.device_info.copy()
        data["sex"] = self.sex
        resp = await self.proto.post("/user/change_sex", data)

        data = self.device_info.copy()
        resp = await self.proto.post("/tutorial/skip", data)

    async def uma_daily(self):

        data = self.device_info.copy()
        resp = await self.proto.post("/load/index", data)

        data = self.device_info.copy()
        resp = await self.proto.post("/payment/item_list", data)

        data = self.device_info.copy()
        data["log_key"] = 3
        data["log_message"] = "Google Play In-app Billing API version is less than 3"
        resp = await self.proto.post("/payment/send_log", data)

        await self.uma_receive_gifts()

    async def uma_receive_gifts(self):
        # get mission & receive mission_gift
        data = self.device_info.copy()
        resp = await self.proto.post("/mission/index", data)
        missions = self.parse_mission(resp)

        if missions:
            data = self.device_info.copy()
            data['mission_id_array'] = missions
            resp = await self.proto.post("/mission/receive", data)

        # receive gifts
        data = self.device_info.copy()
        data["time_filter_type"] = 0
        data["category_filter_type"] = [0]
        data["offset"] = 0
        data["limit"] = 100
        data["is_asc"] = True
        resp = await self.proto.post("/present/index", data)

        data = self.device_info.copy()
        data["time_filter_type"] = 0
        data["category_filter_type"] = [0]
        data["is_asc"] = True
        resp = await self.proto.post("/present/receive_all", data)

    async def uma_info(self):
        data = self.device_info.copy()
        resp = await self.proto.post("/load/index", data)
        return self.parse_info(resp)

    async def uma_raw_info(self):
        data = self.device_info.copy()
        resp = await self.proto.post("/load/index", data)
        return resp["data"]

    async def uma_login(self):
        data = self.device_info.copy()
        resp = await self.proto.post("/tool/start_session", data)
        self.parse_res_ver(resp)

    ### Card #################################################################################

    async def uma_support_card_limit_break(self, support_card_id):
        logger.debug("Support card %d limit break" % support_card_id)
        data = self.device_info.copy()
        data["support_card_id"] = support_card_id
        data["material_support_card_num"] = 1
        resp = await self.proto.post("/support_card/limit_break", data)

    async def uma_support_card_limit_break_all(self):
        support_cards = (await self.uma_info())["support_card_list"]
        for sc in support_cards:
            for i in range(sc["stock"]):
                if i + sc["limit_break_count"] >= 4:
                    logging.warn("support card %d: %d" % (sc["support_card_id"], sc["stock"]+sc["limit_break_count"]+1))
                    break
                await self.uma_support_card_limit_break(sc["support_card_id"])
                await asyncio.sleep(1) # otherwise will trigger 208 fault ( DOUBLE_CLICK_ERROR )

    ### Gacha ################################################################################

    async def uma_gacha_info(self):
        data = self.device_info.copy()
        resp = await self.proto.post("/gacha/index", data)
        return self.parse_gacha(resp)

    async def uma_gacha_exec(self, gacha_id, num, fcoin):
        data = self.device_info.copy()
        data["gacha_id"] = gacha_id
        data["draw_type"] = 1
        data["draw_num"] = num
        data["current_num"] = fcoin
        data["item_id"] = 0
        resp = await self.proto.post("/gacha/exec", data)

    @staticmethod
    def gacha_find_sc_pool(gachas):
        for gacha in gachas:
            if ((gacha["id"] // 10000) == 3) and ((gacha["id"] % 2) == 1):
                return gacha["id"]
        return None

    async def gacha_sc_pulls(self, pulls, well=1, times=None):
        coins = (pulls * 150) * well
        fcoin = (await self.uma_info())["fcoin"]
        if not times:
            times = fcoin // coins
        logger.info("To Gacha %d (one: %d)" % (times, coins))
        gachas = await self.uma_gacha_info()
        gacha_id = self.gacha_find_sc_pool(gachas)
        if gacha_id:
            for i in range(times):
                for j in range(well):
                    await self.uma_gacha_exec(gacha_id, pulls, fcoin)
                    fcoin -= (pulls * 150)
                    await asyncio.sleep(3) # otherwise will trigger 208 fault ( DOUBLE_CLICK_ERROR )

    async def uma_gacha_strategy_one(self):
        # one well to support card gacha
        await self.gacha_sc_pulls(10, 20)

    async def uma_gacha_strategy_two(self):
        # 10 pulls to support card gacha
        await self.gacha_sc_pulls(10)

    async def uma_gacha_strategy_three(self):
        # first ten pull, later one pull
        await self.gacha_sc_pulls(10)
        await self.gacha_sc_pulls(1)

    async def uma_gacha_strategy_four(self):
        # single pull
        await self.gacha_sc_pulls(1)

    async def uma_gacha_strategy(self, mode, limit_break=False):
        if mode == 1:
            self.uma_gacha_strategy_one()
        elif mode == 2:
            self.uma_gacha_strategy_two()
        elif mode == 3:
            self.uma_gacha_strategy_three()
        else:
            self.uma_gacha_strategy_four()

        if limit_break:
            await self.uma_support_card_limit_break_all()
        return await self.uma_info()

    ### Account ##############################################################################

    async def uma_account_trans(self, password):
        self.password = password
        data = self.device_info.copy()
        data["password"] = md5((password+"r!I@mt8e5i=").encode("utf8")).hexdigest()
        resp = await self.proto.post("/account/publish_transition_code", data)

    ### Single mode ##########################################################################

    def choose_training_uma(self, info):
        # choose least fan
        chara_list = sorted(info["chara_list"], key=lambda k: k["fan"])
        chara = chara_list[0]["chara_id"]
        for card in info["card_list"]:
            if card["card_id"] // 100 == chara:
                return card["card_id"]

    def choose_sc_cards(self, info, chara_id):
        sc_list = sorted(info["support_card_list"], key=lambda k:k["limit_break_count"]+(k["support_card_id"] // 10000), reverse=True)
        con = sqlite3.connect("./data/master.mdb")
        cur = con.cursor()
        sc_card_ids = []
        sc_chara_ids = []
        for sc in sc_list:
            cid = cur.execute("select chara_id from support_card_data where id= %s" % sc["support_card_id"]).fetchone()[0]
            if cid == (chara_id // 100):
                continue
            if cid in sc_chara_ids:
                continue
            sc_card_ids.append(sc["support_card_id"])
            sc_chara_ids.append(cid)
            if len(sc_card_ids) == 5:
                con.close()
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

    async def uma_choose_rental(self, chara_id, sc_chara_ids):
        data = self.device_info.copy()
        resp = await self.proto.post("/single_mode/rental_info", data)
        FRIEND_CARDS = [30016, 30028, 30021]
        sc_cards = resp["data"]["friend_support_card_data"]["support_card_data_array"]
        sc_cards = sorted(sc_cards, key=lambda k:k["limit_break_count"]+(k["support_card_id"] // 10000), reverse=True)
        con = sqlite3.connect("./data/master.mdb")
        cur = con.cursor()
        for sc in sc_cards:
            cid = cur.execute("select chara_id from support_card_data where id= %s" % sc["support_card_id"]).fetchone()[0]
            if cid == (chara_id // 100):
                continue
            if cid in sc_chara_ids:
                continue
            if sc["support_card_id"] in FRIEND_CARDS and sc["limit_break_count"] > 2:
                con.close()
                return {"viewer_id": sc["viewer_id"], "support_card_id": sc["support_card_id"]}
        for sc in sc_cards:
            cid = cur.execute("select chara_id from support_card_data where id= %s" % sc["support_card_id"]).fetchone()[0]
            if cid == (chara_id // 100):
                continue
            if cid in sc_chara_ids:
                continue
            con.close()
            return {"viewer_id": sc["viewer_id"], "support_card_id": sc["support_card_id"]}

    async def single_mode_prepare(self, chara_id, sc_list, succ):
        info = await self.uma_raw_info()
        if not chara_id:
            chara_id = self.choose_training_uma(info)
        if not sc_list:
            support_card_ids, sc_chara_ids = self.choose_sc_cards(info, chara_id)
        if not succ:
            succ = self.choose_succs(info, chara_id)

        logger.warn("card_id %d" % chara_id)
        logger.warn("sc: %s" % str(support_card_ids))

        money = 0
        for item in info["item_list"]:
            if item["item_id"] == 59:
                money = item["number"]
                break
        friend_info = await self.uma_choose_rental(chara_id, sc_chara_ids)

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


        data = self.device_info.copy()
        data["start_chara"] = start_chara
        data["tp_info"] = info["tp_info"]
        data["current_money"] = money
        resp = await self.proto.post("/single_mode/start", data)

        # support card deck array
        data = self.device_info.copy()
        data["support_card_deck_array"] = []
        deck= {}
        deck["deck_id"] = 1
        deck["support_card_id_array"] = support_card_ids
        for i in range(2, 11):
            deck = {}
            deck["deck_id"] = i
            deck["support_card_id_array"] = [0, 0, 0, 0, 0]
            data["support_card_deck_array"].append(deck)
        await self.proto.post("/support_card_deck/change_party", data)

        # short_cut
        data = self.device_info.copy()
        data["short_cut_state"] = 1
        data["current_turn"] = 1
        resp = await self.proto.post("/single_mode/change_short_cut", data)

        return resp["data"]

    def single_mode_check_route(self, info):
        chara_id = info["chara_info"]["card_id"] // 100
        con = sqlite3.connect("./data/master.mdb")
        cur = con.cursor()
        races = cur.execute("select turn, condition_id from single_mode_route_race where race_set_id= %s" % chara_id).fetchall()
        routes = []
        for r in races:
            print(r)
            route = {}
            route["program_id"] = r[1]
            route["turn"] = r[0]
            if r[1] > 10000:
                route["fans"] = 0
            else:
                route["fans"] = cur.execute("select need_fan_count from single_mode_program where id = %s" % r[1]).fetchone()[0]
            logger.warn(str(route))
            routes.append(route)
        con.close()
        return sorted(routes, key=lambda k:k["turn"])

    async def uma_check_event(self, event, turn):
        data = self.device_info.copy()
        data["event_id"] = event["event_id"]
        data["chara_id"] = event["chara_id"]
        # FIXME: always choose first option
        data["choice_number"] = 0
        data["current_turn"] = turn
        resp = await self.proto.post("/single_mode/check_event", data)
        return resp["data"]

    async def uma_minigame(self, turn):
        # FIXME: add more result value to gain rest & skills
        data = self.device_info.copy()
        data["result"] = {}
        data["result"]["result_state"] = 2
        data["result"]["result_value"] = 2
        data["result"]["result_detail_array"] = [{"get_id": 0, "chara_id": 1002, "dress_id": 2, "motion": "Catch11", "face": "WaraiD"}]
        data["current_turn"] = turn
        resp = await self.proto.post("/single_mode/minigame_end", data)
        return resp["data"]

    async def single_mode_check_event(self, data):
        while data.get("unchecked_event_array"):
            event = data["unchecked_event_array"][0]
            data = await self.uma_check_event(event, data["chara_info"]["turn"])
            # minigame
            if event["event_id"] == 6002:
                data = await self.uma_minigame(data["chara_info"]["turn"])
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

        data = self.device_info.copy()
        data["command_type"] = mycmd["command_type"]
        data["command_id"] = mycmd["command_id"]
        data["command_group_id"] = mycmd.get("command_group_id", 0)
        data["select_id"] = 0
        data["current_turn"] = turn
        data["current_vital"] = chara_info["vital"]
        resp = await self.proto.post("/single_mode/exec_command", data)
        return resp["data"]

    async def uma_run_race(self, program_id, turn):
        data = self.device_info.copy()
        data["program_id"] = program_id
        data["current_turn"] = turn
        resp = await self.proto.post("/single_mode/race_entry", data)

        data = await self.single_mode_check_event(resp["data"])

        data = self.device_info.copy()
        data["is_short"] = 1
        data["current_turn"] = turn
        resp = await self.proto.post("/single_mode/race_start", data)

        data = self.device_info.copy()
        data["current_turn"] = turn
        resp = await self.proto.post("/single_mode/race_end", data)

        if resp["data"]["add_music"]:
            # FIXME: obtain live
            # /live/live_start
            pass

        data = self.device_info.copy()
        data["current_turn"] = turn
        resp = await self.proto.post("/single_mode/race_out", data)

        data = await self.single_mode_check_event(resp["data"])
        return data

    def choose_race(self, info, need_run, race_property):
        chara_info = info["chara_info"]
        races = info["race_condition_array"]
        chara_id = info["chara_info"]["card_id"] // 100
        con = sqlite3.connect("./data/master.mdb")
        cur = con.cursor()
        choose_race_id = None
        run_races = []
        for race in races:
            programs = cur.execute("select race_instance_id, need_fan_count from single_mode_program where id = %s" % race["program_id"]).fetchone()
            if chara_info["fans"] < programs[1]:
                continue
            race_id = cur.execute("select race_id from race_instance where id = %s" % programs[0]).fetchone()[0]
            race_grade = cur.execute("select grade, course_set from race where id = %s" % race_id).fetchone()
            course_set = cur.execute("select distance, ground from race_course_set where id = %s" % race_grade[1]).fetchone()

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

        con.close()
        if need_run and not choose_race_id:
            # choose first race
            choose_race_id = races[0]["program_id"]
        return choose_race_id

    async def uma_gain_skill(self, info, turn):
        skill_point = info["chara_info"]["skill_point"]
        skill_tips = info["chara_info"]["skill_tips_array"]
        if not skill_tips:
            return
        got_skills = []
        for sk in info["chara_info"]["skill_array"]:
            got_skills.append(sk["skill_id"])
        con = sqlite3.connect("./data/master.mdb")
        cur = con.cursor()
        gain_skills = []
        # FIXME: random choose skill
        count = 0
        while True:
            skill_tip = skill_tips[random.randint(0, len(skill_tips)-1)]
            sk_info = cur.execute("select id, rarity from skill_data where group_id = %d" % skill_tip["group_id"]).fetchall()
            sk_info.reverse()
            logger.warn(str(skill_tip))
            logger.warn(str(sk_info))
            logger.warn(str(got_skills))
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
        con.close()
        if gain_skills:
            data = self.device_info.copy()
            data["gain_skill_info_array"] = gain_skills
            data["current_turn"] = turn
            await self.proto.post("/single_mode/gain_skills", data)

    async def single_mode_finish(self, info):
        turn = info["chara_info"]["turn"]
        await self.uma_gain_skill(info, turn)

        data = self.device_info.copy()
        data["is_force_delete"] = False
        data["current_turn"] = turn
        resp = await self.proto.post("/single_mode/finish", data)
        info = resp["data"]

        friend_viewer_id = 0
        for sc in info["chara_info"]["support_card_array"]:
            if sc["owner_viewer_id"] != 0:
                friend_viewer_id = sc["owner_viewer_id"]
                break

        # change nick name
        data = self.device_info.copy()
        data["trained_chara_id"] = info["directory_card_array"][0]["trained_chara"]["trained_chara_id"]
        data["nickname_id"] = info["chara_info"]["nickname_id_array"][0]
        resp = await self.proto.post("/trained_chara/change_nickname", data)

        '''
        # FIXME: ignore friend search now
        data = self.device_info.copy()
        data["friend_viewer_id"] = friend_viewer_id
        resp = await self.proto.post("/friend/search", data)
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

    async def uma_training(self, chara_id=None, sc_list=[], succ=[]):
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
                        await self.uma_gain_skill(data, turn)
                    data = await self.uma_run_race(routes[route_num]["program_id"], turn)
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
                    logger.warn("race_id %s" % race_id)
                    data = await self.uma_run_race(race_id, turn)
                else:
                    data = await self.single_mode_exec_cmd(data)
            # failed
            if data["chara_info"]["state"] == 2:
                break
        # finish
        await self.single_mode_finish(data)

    ### Team Stadium #########################################################################

    def gen_team_array(self, trained_chara, choosed, distance):
        tr = None
        for t in trained_chara:
            if t["trained_chara_id"] in choosed:
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
        info = await self.uma_raw_info()
        score = 0
        teams = []
        choosed = []
        # dirt first
        trained_chara = sorted(info["trained_chara"], key=lambda k:(k["proper_ground_dirt"] // 6) * 10000 + k["rank_score"], reverse=True)
        tr, arr = self.gen_team_array(trained_chara, choosed, 5)
        score += tr["rank_score"]
        teams.extend(arr)
        choosed.append(tr["trained_chara_id"])

        trained_chara = sorted(trained_chara, key=lambda k:(k["proper_distance_short"] // 6) * 10000 + k["rank_score"], reverse=True)
        tr, arr = self.gen_team_array(trained_chara, choosed, 1)
        score += tr["rank_score"]
        teams.extend(arr)
        choosed.append(tr["trained_chara_id"])

        trained_chara = sorted(trained_chara, key=lambda k:(k["proper_distance_mile"] // 6) * 10000 + k["rank_score"], reverse=True)
        tr, arr = self.gen_team_array(trained_chara, choosed, 2)
        score += tr["rank_score"]
        teams.extend(arr)
        choosed.append(tr["trained_chara_id"])

        trained_chara = sorted(trained_chara, key=lambda k:(k["proper_distance_middle"] // 6) * 10000 + k["rank_score"], reverse=True)
        tr, arr = self.gen_team_array(trained_chara, choosed, 3)
        score += tr["rank_score"]
        teams.extend(arr)
        choosed.append(tr["trained_chara_id"])

        trained_chara = sorted(trained_chara, key=lambda k:(k["proper_distance_long"] // 6) * 10000 + k["rank_score"], reverse=True)
        tr, arr = self.gen_team_array(trained_chara, choosed, 4)
        score += tr["rank_score"]
        teams.extend(arr)
        choosed.append(tr["trained_chara_id"])

        data = self.device_info.copy()
        data["team_data_array"] = teams
        data["team_evaluation_point"] = score
        await self.proto.post("/team_stadium/team_edit", data)

    async def uma_team_stadium(self, edit=False):
        data = self.device_info.copy()
        await self.proto.post("/team_stadium/index", data)

        # team edit
        if edit:
            await self.team_stadium_edit()

        data = self.device_info.copy()
        resp = await self.proto.post("/team_stadium/opponent_list", data)

        data = self.device_info.copy()
        resp["data"]["opponent_info_array"][-1].pop(None)
        data["opponent_info"] = resp["data"]["opponent_info_array"][-1]
        await self.proto.post("/team_stadium/decide_frame_order", data)

        data = self.device_info.copy()
        data["item_id_array"] = []
        await self.proto.post("/team_stadium/start", data)

        for i in range(5):
            data = self.device_info.copy()
            data["round"] = i + 1
            await self.proto.post("/team_stadium/replay_check", data)

        data = self.device_info.copy()
        await self.proto.post("/team_stadium/all_race_end", data)

    ### Story ################################################################################

    async def uma_chara_story(self, episode_id):
        data = self.device_info.copy()
        data["episode_id"] = episode_id
        resp = await self.proto.post("/character_story/first_clear", data)

