# -*- coding: utf-8 -*-

import asyncio
import os
import httpx
import uuid
import json
import base64
import random
import string
import struct
import codecs
import msgpack
import secrets
import tempfile
from hashlib import md5
from utils.resp import RESPCODE

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
        if resp["response_code"] != 1:
            logger.error("ERROR RESPONSE_CODE %s: %s!!!" % (resp["response_code"], RESPCODE(resp["response_code"]).name))
        if resp.get("data_headers"):
            data_headers = resp["data_headers"]
            if data_headers.get("sid"):
                self.session_id = md5(data_headers.get("sid").encode("utf8") + b'r!I@mt8e5i=').digest()

    async def post(self, url, data):
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
        resp = msgpack.unpackb(self.decompress(r.text))
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

    async def uma_support_card_limit_break(self, support_card_id):
        logger.debug("Support card %d limit break" % support_card_id)
        data = self.device_info.copy()
        data["support_card_id"] = support_card_id
        data["material_support_card_num"] = 1
        resp = await self.proto.post("/support_card/limit_break", data)

    async def uma_chara_story(self, episode_id):
        data = self.device_info.copy()
        data["episode_id"] = episode_id
        resp = await self.proto.post("/character_story/first_clear", data)

    async def uma_support_card_limit_break_all(self):
        support_cards = (await self.uma_info())["support_card_list"]
        for sc in support_cards:
            for i in range(sc["stock"]):
                if i + sc["limit_break_count"] >= 4:
                    logging.warn("support card %d: %d" % (sc["support_card_id"], sc["stock"]+sc["limit_break_count"]+1))
                    break
                await self.uma_support_card_limit_break(sc["support_card_id"])
                await asyncio.sleep(1) # otherwise will trigger 208 fault ( DOUBLE_CLICK_ERROR )

    @staticmethod
    async def gacha_find_sc_pool(gachas):
        for gacha in gachas:
            if ((gacha["id"] // 10000) == 3) and ((gacha["id"] % 2) == 1):
                return gacha["id"]
        return None

    async def gacha_sc_pulls(self, pulls, well=1):
        coins = (pulls * 150) * well
        fcoin = (await self.uma_info())["fcoin"]
        times = fcoin // coins
        logger.info("To Gacha %d (one: %d)" % (times, coins))
        gachas = self.uma_gacha_info()
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
        # FIXME: no idea how
        await self.gacha_sc_pulls(10)

    async def uma_gacha_strategy_three(self):
        # first ten pull, later one pull
        await self.gacha_sc_pulls(10)
        await self.gacha_sc_pulls(1)

    async def uma_gacha_strategy_four(self):
        # single pull
        await self.gacha_sc_pulls(1)

    def uma_gacha_strategy(self, mode, limit_break=False):
        if mode == 1:
            self.uma_gacha_strategy_one()
        elif mode == 2:
            self.uma_gacha_strategy_two()
        elif mode == 3:
            self.uma_gacha_strategy_three()
        else:
            self.uma_gacha_strategy_four()

        if limit_break:
            self.uma_support_card_limit_break_all()
        return await self.uma_info()

    async def uma_account_trans(self, password):
        self.password = password
        data = self.device_info.copy()
        data["password"] = md5((password+"r!I@mt8e5i=").encode("utf8")).hexdigest()
        resp = await self.proto.post("/account/publish_transition_code", data)
