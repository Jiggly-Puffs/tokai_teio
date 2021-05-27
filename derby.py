# -*- coding: utf-8 -*-

import os
import sys
import uuid
import json
import base64
import random
import string
import struct
import codecs
import msgpack
import secrets
import requests
from hashlib import md5

from utils.logger import *


UMA_URL = "https://api-umamusume.cygames.jp/umamusume"
APP_VER = "1.4.0"
RES_VER = "10001420:TSVRrfC372gH"
UMA_PUBKEY = "6b20e2ab6c311330f761d737ce3f3025750850665eea58b6372f8d2f57501eb348ee86c2de2699100d32f9e07dbfccb9a8fe658b"

USER_AGENT = "Mozilla/5.0 (Linux; Android 10; SM-A102U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36"


class UmaProto(object):

    def __init__(self, cert_uuid, viewer_id=0, auth_key=None):
        self.cert_uuid = cert_uuid
        self.viewer_id = viewer_id
        self.auth_key = auth_key

    def set_viewer_id(self, viewer_id):
        self.viewer_id = viewer_id

    def set_auth_key(self, auth_key):
        self.auth_key = auth_key

    def con_req(self, req, session_id):
        data = codecs.decode(UMA_PUBKEY, "hex")
        data += session_id
        data += self.cert_uuid
        data += secrets.token_bytes(32)
        if self.auth_key:
            data += self.auth_key
        data = struct.pack("<I", len(data)) + data
        data += msgpack.packb(req)
        return self.compress(data)

    def compress(self, data):
        open("tmp/req", "wb").write(data)
        os.system("./utils/proto 0 tmp")
        return base64.b64encode(open("tmp/req.enc", "rb").read())

    def decompress(self, data):
        open("tmp/resp", "wb").write(base64.b64decode(data.strip()))
        os.system("./utils/proto 1 tmp")
        return open("tmp/resp.dec", "rb").read()

    def con_headers(self, session_id):
        headers = {
            "SID": session_id.hex(),
            "APP-VER": APP_VER,
            "RES-VER": RES_VER,
            "Content-Type": "application/x-msgpack",
            "ViewerID": str(self.viewer_id),
            "User-agent": USER_AGENT,
        }
        return headers

    def run(self, url, session_id, data):
        url = UMA_URL + url
        INFO("URL: %s" % url)
        headers = self.con_headers(session_id)
        DEBUG("Headers: %s" % str(headers))
        DEBUG("Req: %s" % data)
        req = self.con_req(data, session_id)
        r = requests.post(url, data=req, headers=headers)
        if r.status_code != 200:
            ERROR("url: %s\n Error code: %d" % (url, r.status_code))
        resp = msgpack.unpackb(self.decompress(r.text))
        return resp


class Derby(object):

    def __init__(self, data=None):
        if data:
            self.load(data)
        else:
            self.uma_init()  # generate a new account

        self.proto = UmaProto(self.cert_uuid, self.viewer_id, self.auth_key)
        #self.omotenashi()

    def load(self, data):
        self.app_viewer_id = data["app_viewer_id"]
        self.device_info = data["device_info"]
        self.firebase = data["firebase"]
        self.viewer_id = self.device_info["viewer_id"]
        self.auth_key = base64.b64decode(data["auth_key"])
        self.gen_session_id()

    def tojson(self):
        data = {}
        data["app_viewer_id"] = self.app_viewer_id
        data["device_info"] = self.device_info
        data["firebase"] = self.firebase
        data["auth_key"] = base64.b64encode(self.auth_key).decode("utf8")
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
        DEBUG("app_viewer_id: %s" % self.app_viewer_id)
        self.gen_session_id()
        self.name = ''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(3, 10)))
        self.sex = random.randint(1, 2)
        self.gen_device_info()
        self.firebase = {}
        self.auth_key = None

    def omotenashi(self):
        from omotenashi.omotenashi import Omotenashi
        omo = Omotenashi(self.app_viewer_id, APP_VER)
        if self.firebase:
            omo.update()
        else:
            omo.register()

    def update_resp(self, resp):
        DEBUG("RESP: %s" % str(resp))
        if resp["response_code"] != 1:
            ERROR("ERROR RESPONSE_CODE %s!!!" % resp["response_code"])
        if resp.get("data_headers"):
            data_headers = resp["data_headers"]
            if data_headers.get("sid"):
                self.session_id = md5(data_headers.get("sid").encode("utf8") + b'r!I@mt8e5i=').digest()
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
            if data.get("resource_version"):
                global RES_VER
                if data["resource_version"] != RES_VER:
                    RES_VER = data["resource_version"]
                    INFO("NEW RES-VER: %s" % RES_VER)

    def parse_fcoin(self, resp):
        data = resp["data"]
        self.fcoin = data["coin_info"]["fcoin"]
        INFO("FCOIN %d" % self.fcoin)

    def parse_mission(self, resp):
        data = resp["data"]
        m = []
        if data.get("mission_list"):
            missions = data.get("mission_list")
            for mis in missions:
                if mis["mission_status"] == 1:
                    m.append(mis["mission_id"])
        return m

    def uma_signup(self):
        data = self.device_info.copy()
        resp = self.proto.run("/tool/pre_signup", self.session_id, data)
        self.update_resp(resp)

        data = self.device_info.copy()
        data["credential"] = ""
        data["error_code"] = 0
        data["error_message"] = ""
        resp = self.proto.run("/tool/signup", self.session_id, data)
        self.update_resp(resp)

        data = self.device_info.copy()
        resp = self.proto.run("/tool/start_session", self.session_id, data)
        self.update_resp(resp)

        data = self.device_info.copy()
        resp = self.proto.run("/load/index", self.session_id, data)
        self.update_resp(resp)

        data = self.device_info.copy()
        data["name"] = self.name
        resp = self.proto.run("/user/change_name", self.session_id, data)
        self.update_resp(resp)

        data = self.device_info.copy()
        data["sex"] = self.sex
        resp = self.proto.run("/user/change_sex", self.session_id, data)
        self.update_resp(resp)

        data = self.device_info.copy()
        resp = self.proto.run("/tutorial/skip", self.session_id, data)
        self.update_resp(resp)

    def uma_daily(self):

        data = self.device_info.copy()
        resp = self.proto.run("/load/index", self.session_id, data)
        self.update_resp(resp)

        data = self.device_info.copy()
        resp = self.proto.run("/payment/item_list", self.session_id, data)
        self.update_resp(resp)

        data = self.device_info.copy()
        data["log_key"] = 3
        data["log_message"] = "Google Play In-app Billing API version is less than 3"
        resp = self.proto.run("/payment/send_log", self.session_id, data)
        self.update_resp(resp)

        self.uma_receive_gifts()

    def uma_receive_gifts(self):
        # get mission & receive mission_gift
        data = self.device_info.copy()
        resp = self.proto.run("/mission/index", self.session_id, data)
        self.update_resp(resp)
        missions = self.parse_mission(resp)

        if missions:
            data = self.device_info.copy()
            data['mission_id_array'] = missions
            resp = self.proto.run("/mission/receive", self.session_id, data)
            self.update_resp(resp)

        # receive gifts
        data = self.device_info.copy()
        data["time_filter_type"] = 0
        data["category_filter_type"] = [0]
        data["offset"] = 0
        data["limit"] = 100
        data["is_asc"] = True
        resp = self.proto.run("/present/index", self.session_id, data)
        self.update_resp(resp)

        data = self.device_info.copy()
        data["time_filter_type"] = 0
        data["category_filter_type"] = [0]
        data["is_asc"] = True
        resp = self.proto.run("/present/receive_all", self.session_id, data)
        self.update_resp(resp)

    def check_fcoin(self):
        data = self.device_info.copy()
        resp = self.proto.run("/load/index", self.session_id, data)
        self.update_resp(resp)
        self.parse_fcoin(resp)

    def uma_login(self):
        data = self.device_info.copy()
        resp = self.proto.run("/tool/start_session", self.session_id, data)
        self.update_resp(resp)

    def uma_view_card(self):
        pass

    def uma_view_support_card(self):
        pass

    def uma_support_card_limit_break(self):
        pass

    def uma_gacha(self):
        pass
