# -*- coding: utf-8 -*-

import os
import sys
import base64
import random
import string
import struct
import codecs
import msgpack
import hashlib
import secrets
import requests

UMA_URL = "https://api-umamusume.cygames.jp/umamusume"
APP_VER = "1.3.2"
RES_VER = "10001310:TWMvHe0MQgo3"

BRANDS = ["Samsung", "Xiaomi", "Sony", "Sharp", "Toshiba", "Google", "Casio", "Fujitsu", "HP", "Lenovo", "LG", "Panasonic", "Kyocera", "DoCoMo"]
USER_AGENT = "Mozilla/5.0 (Linux; Android 10; SM-A102U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36"


class UmaProto(object):

    def __init__(self, cert_uuid):
        self.cert_uuid = cert_uuid
        self.viewer_id = 0

    def con_req(self, buf):
        data = codecs.decode("6b20e2ab6c311330f761d737ce3f3025750850665eea58b6372f8d2f57501eb34d0c4b6a47cc9d7a74f1735d6100e46aa037bd69", "hex")
        data += self.session_id
        data += self.cert_uuid
        data += secrets.token_bytes(32)
        if self.auth_key:
            data += self.auth_key
        data = struct.pack("<I", len(data)) + data
        data += msgpack.packb(buf)
        self.compress(data)

    def compress(self, data):
        with open("tmp/req", "wb") as f:
            f.write(data)
        os.system("./proto 0 tmp")
        with open("tmp/req.enc", "rb") as f:
            self.data = base64.b64encode(f.read())

    def decompress(self, data):
        data = base64.b64decode(data.strip())
        with open("tmp/resp", "wb") as f:
            f.write(data)
        os.system("./proto 1 tmp")
        with open("tmp/resp.dec", "rb") as f:
            self.resp = f.read()

    def update_headers(self):
        self.headers = {
            "SID": self.session_id.hex(),
            "APP-VER": APP_VER,
            "RES-VER": RES_VER,
            "Content-Type": "application/x-msgpack",
            "ViewerID": str(self.viewer_id),
            "User-agent": USER_AGENT,
        }
        print(self.headers)

    def post(self):
        print(self.data)
        r = requests.post(self.url, data=self.data, headers=self.headers)
        print(r.status_code)
        self.decompress(r.text)
        return msgpack.unpackb(self.resp)

    def run(self, url, session_id, data, viewer_id, auth_key=None):
        self.url = UMA_URL + url
        self.session_id = session_id
        self.viewer_id = viewer_id
        self.auth_key = auth_key
        print(data)
        self.con_req(data)
        self.update_headers()
        return self.post()


class UmaHohoho(object):

    def __init__(self, viewer_id=None, device_info=None):
        self.auth_key = None
        if device_info: # load account from db
            self.viewer_id = viewer_id
            self.device_info = device_info
            # load
            self.gen_session_id()
            self.pro = UmaProto(self.cert_uuid)
            self.uma_login()
        else:
            self.name = None
            self.sex = None
            self.pre_init()  # generate a new account
            self.pro = UmaProto(self.cert_uuid)
            self.uma_signup()

    def set_name_sex(self, name, sex):
        self.name = name
        self.sex = sex

    def gen_device_info(self):
        self.device_info = {
            "viewer_id": 0,
            "device": 2,
            #"device_id": self.device_id,
            "device_id": "652497c376f58028f04e6b959fd48e36",
            #"device_name": self.brand + " " + "".join(random.choice(string.ascii_uppercase) for i in range(random.randint(6, 8))),
            "device_name": "Xiaomi M2004J7AC",
            "graphics_device_name": "Mali-G57",
            "ip_address": "192.168."+str(random.randint(0, 254))+"."+str(random.randint(1, 254)),
            "platform_os_version": "Android OS 10 / API-29 (QP1A.190711.020/V12.0.7.0.QJHCNXM)",
            #"carrier": self.brand,
            "carrier": "Redmi",
            "keychain": 0,
            "locale": "JPN",
            "dmm_viewer_id": None,
            "dmm_onetime_token": None,
        }

    def gen_session_id(self):
        cert_uuid = self.cert_uuid.hex()
        cert_uuid = cert_uuid[:8] + "-" + cert_uuid[8:12] + "-" + cert_uuid[12:16] + "-" + cert_uuid[16:20] + "-" + cert_uuid[20:]
        md5 = hashlib.md5()
        md5.update((str(self.viewer_id) + cert_uuid + 'r!I@mt8e5i=').encode("utf8"))
        self.session_id = md5.digest()
        print(self.session_id.hex())

    def pre_init(self):
        self.viewer_id = 0
        self.cert_uuid = secrets.token_bytes(16)
        self.gen_session_id()
        self.device_id = codecs.encode(secrets.token_bytes(16), "hex").decode("utf8")
        self.brand = BRANDS[random.randint(0, len(BRANDS)-1)]
        if not self.name:
            self.name = ''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(3, 10)))
        if not self.sex:
            self.sex = random.randint(1, 2)
        self.gen_device_info()

    def update_resp(self, resp):
        print(resp)
        if resp.get("data_headers"):
            data_headers = resp["data_headers"]
            if data_headers.get("sid"):
                md5 = hashlib.md5()
                md5.update(data_headers.get("sid").encode("utf8") + b'r!I@mt8e5i=')
                self.session_id = md5.digest()
        if resp.get("data"):
            data = resp["data"]
            if data.get("viewer_id"):
                self.viewer_id = data["viewer_id"]
                self.device_info["viewer_id"] = self.viewer_id
                print(self.device_info)
            if data.get("auth_key"):
                self.auth_key = base64.b64decode(data["auth_key"])
            if data.get("resource_version"):
                RES_VER = data["resource_version"]
                print("NEW RES-VER:", RES_VER)


    def uma_signup(self):
        data = self.device_info
        resp = self.pro.run("/tool/pre_signup", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)
        return

        data = self.device_info
        data["credential"] = ""
        data["error_code"] = ""
        data["error_message"] = ""
        resp = self.pro.run("/tool/signup", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)

        data = self.device_info
        resp = self.pro.run("/tool/start_session", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)

        data = self.device_info
        resp = self.pro.run("/load/index", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)

        data = self.device_info
        data["name"] = self.name
        resp = self.pro.run("/user/change_name", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)

        data = self.device_info
        data["sex"] = self.sex
        resp = self.pro.run("/user/change_sex", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)

        data = self.device_info
        resp = self.pro.run("/tutorial/skip", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)

    def parse_mission(self, resp):
        data = resp["data"]
        m = []
        if data.get("mission_list"):
            missions = data.get("mission_list")
            for mis in missions:
                if mis["mission_status"] == 1:
                    m.append(mis["mission_id"])
        return m

    def uma_daily(self):

        data = self.device_info
        resp = self.pro.run("/load/index", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)

        data = self.device_info
        resp = self.pro.run("/payment/item_list", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)

        data = self.device_info
        data["log_key"] = 3
        data["log_message"] = "Google Play In-app Billing API version is less than 3"
        resp = self.pro.run("/payment/send_log", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)

        # get mission & receive mission_gift
        data = self.device_info
        resp = self.pro.run("/mission/index", self.session_id, data, self.viewer_id, self.auth_key)
        missions = self.parse_mission(resp)
        self.update_resp(resp)

        data = self.device_info
        data['mission_id_array'] = missions
        resp = self.pro.run("/mission/receive", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)

        # receive gifts
        data = self.device_info
        data["time_filter_type"] = 0
        data["category_filter_type"] = [0]
        data["offset"] = 0
        data["limit"] = 100
        data["is_asc"] = True
        resp = self.pro.run("/present/index", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)

        data = self.device_info
        data["time_filter_type"] = 0
        data["category_filter_type"] = [0]
        data["is_asc"] = True
        resp = self.pro.run("/present/receive_all", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)

        # next c_one/1621328531022.HEADERS

    def uma_login(self):
        data = self.device_info
        resp = self.pro.run("/tool/start_session", self.session_id, data, self.viewer_id, self.auth_key)
        self.update_resp(resp)

    def uma_gacha(self):
        pass


if __name__ == "__main__":
    # test
    uma = UmaHohoho()
