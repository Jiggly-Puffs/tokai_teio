# -*- coding: utf-8 -*-
import subprocess
import os
import uuid
import ssl
import json
import httpx
import base64
import random
import string
import struct
import codecs
import msgpack
import secrets
import asyncio
import tempfile
from hashlib import md5
from utils import RESPCODE

import logging
logger = logging.getLogger(__name__)


APP_VER = "1.5.6"
RES_VER = "10001900:TQN8+nghtqw5"
UMA_PUBKEY = "6b20e2ab6c311330f761d737ce3f3025750850665eea58b6372f8d2f57501eb30d05104d5f315e8b7d3628003474bfe4dd716d43"

USER_AGENT = "Mozilla/5.0 (Linux; Android 10; SM-A102U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36"

class UmaClientResponseErrorException(Exception):
    def __init__(self, status_code: int):
        super().__init__()
        self.status_code = status_code

class UmaClient(object):

    def __init__(self, data=None):
        self.tmp_dir = tempfile.TemporaryDirectory(prefix="UmaClient")
        if data:
            self.load(data)
            #self.omotenashi()
        else:
            self.init()  # generate a new account
        #self.omotenashi()

    def __del__(self):
        self.tmp_dir.cleanup()

    def load(self, data):
        self.app_viewer_id = data["app_viewer_id"]
        self.device_info = data["device_info"]
        self.firebase = data["firebase"]
        self.viewer_id = self.device_info["viewer_id"]
        self.auth_key = base64.b64decode(data["auth_key"])
        self.password = data.get("password", "")
        self.gen_session_id()

    def tojson(self) -> dict:
        data = {}
        data["app_viewer_id"] = self.app_viewer_id
        data["device_info"] = self.device_info
        data["firebase"] = self.firebase

        assert self.auth_key is not None
        data["auth_key"] = base64.b64encode(self.auth_key).decode("utf8")
        data["password"] = self.password
        return data

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

    def init(self):
        self.viewer_id = 0
        self.app_viewer_id = str(uuid.uuid4())
        logger.debug("app_viewer_id: %s" % self.app_viewer_id)
        self.gen_session_id()
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
            if data.get("auth_key"):
                self.auth_key = base64.b64decode(data["auth_key"])

    def parse_res_ver(self, resp):
        if resp.get("data"):
            data = resp["data"]
            if data.get("resource_version"):
                global RES_VER
                if data["resource_version"] != RES_VER:
                    RES_VER = data["resource_version"]
                    logger.warning("NEW RES-VER: %s" % RES_VER)

    async def signup(self, name=None, sex=None):

        await self.post("/tool/pre_signup")

        data = {}
        data["credential"] = ""
        data["error_code"] = 0
        data["error_message"] = ""
        resp = await self.post("/tool/signup", data)
        self.parse_signup_info(resp)

        resp = await self.post("/tool/start_session")
        self.parse_res_ver(resp)

        await self.post("/load/index")

        data = {}
        if name:
            data["name"] = name
        else:
            data["name"] = ''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(3, 10)))
        await self.post("/user/change_name", data)

        data = {}
        if sex:
            data["sex"] = sex
        else:
            data["sex"] = random.randint(1, 2)
        await self.post("/user/change_sex", data)

        await self.post("/tutorial/skip")

        await self.post("/load/index")

        await self.post("/payment/item_list")

        data = {}
        data["log_key"] = 3
        data["log_message"] = "Google Play In-app Billing API version is less than 3"
        await self.post("/payment/send_log", data)

    async def get_info(self):
        resp = await self.post("/load/index")
        data = resp["data"]
        info = {}
        info["fcoin"] = data["coin_info"]["fcoin"]
        info["card_list"] = data["card_list"]
        info["support_card_list"] = data["support_card_list"]
        logger.debug("FCOIN %d" % info["fcoin"])
        return info

    async def signin(self):
        resp = await self.post("/tool/start_session")
        self.parse_res_ver(resp)

        await self.post("/load/index")

        await self.post("/payment/item_list")

        data = {}
        data["log_key"] = 3
        data["log_message"] = "Google Play In-app Billing API version is less than 3"
        await self.post("/payment/send_log", data)

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
        subprocess.check_call(["./utils/proto", "0", self.tmp_dir.name])
        #os.system(f"./utils/proto 0 {self.tmp_dir.name}")
        try:
            return base64.b64encode(open(f"{self.tmp_dir.name}/req.enc", "rb").read())
        except Exception:
            os.system(f"cp -r {self.tmp_dir.name} ./")
            raise

    def decompress(self, data):
        open(f"{self.tmp_dir.name}/resp", "wb").write(base64.b64decode(data.strip()))
        subprocess.check_call(["./utils/proto", "1", self.tmp_dir.name])
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
            # FIXME: the exception should different from status_code error
            raise UmaClientResponseErrorException(resp["response_code"])

    async def post(self, url, data={}):
        await asyncio.sleep(0.1) # avoid double click
        UMA_URL = os.environ.get("API_ENDPOINT", "https://api-umamusume.cygames.jp/umamusume")
        url = UMA_URL + url
        headers = self.con_headers()
        data.update(self.device_info)
        logger.info("URL: %s" % url)
        logger.debug("Headers: %s" % str(headers))
        logger.debug("Req: %s" % data)
        req = self.con_req(data)

        r = None
        for _ in range(4):
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.post(url, content=req, headers=headers)
                    break
            except (httpx.ReadTimeout, httpx.ProxyError, ssl.SSLError, httpx.ConnectTimeout) as e:
                await asyncio.sleep(1)

        # Final Try
        if r is None:
            async with httpx.AsyncClient() as client:
                r = await client.post(url, content=req, headers=headers)


        if r.status_code != 200:
            logger.error("url: %s\n Error code: %d" % (url, r.status_code))
            # FIXME: the exception should different from response_code error
            raise UmaClientResponseErrorException(r.status_code)

        try:
            resp = msgpack.unpackb(self.decompress(r.text), raw=False)
        except msgpack.ExtraData as e:
            logger.warning("msgpack ExtraData")
            resp = e.args[0]

        self.update_session_id(resp)
        return resp

