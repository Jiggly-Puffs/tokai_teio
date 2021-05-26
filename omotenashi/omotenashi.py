# -*- coding: utf-8 -*-

import uuid
import pytz
import json
import time
import random
import codecs
import base64
import secrets
import requests
from omotenash import checkin_pb2
from datetime import datetime, timezone


class Omotenashi(object):

    def __init__(self, app_viewer_id, app_ver, firebase={}):
        self.app_viewer_id = app_viewer_id
        self.app_ver = app_ver
        self.firebase = firebase

    def register(self):
        self.register_session()
        self.register_firebase()
        self.register_event()

    def update(self):
        self.register_session()
        self.refresh_token()
        self.register_event()

    def register_session(self):
        now = datetime.now(timezone.utc).astimezone(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')
        OMO_URL = requests.utils.requote_uri("https://omotenashi.cygames.jp/api/v1/Session?APP_ID=110&INSTALL_ID=AA0000000000&EVENT_DATE=%s&RETRY_COUNT=0&APP_VIEWER_ID=%s&SDK_VERSION=4.24.0" % (now, self.app_viewer_id))
        OMO_HEADERS = {
            "Install-id": "AA0000000000",
            "App-version": self.app_ver,
            "Os": "Android",
            "App-salt": "",
            "Environment-mode": "1",
            "Event-date": now,
            "Retry-count": "0",
            "App-viewer-id": self.app_viewer_id,
            "App-id": "110",
            "Sdk-version": "4.24.0",
            "User-agent": "Mozilla/5.0 (Linux; Android 10; SM-A102U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36",
        }
        OMO_DATA = {
            "ID": "e9ddb9e3dbe41bda26f02bd294927078",
        }
        print(OMO_URL)
        requests.post(OMO_URL, data=OMO_DATA, headers=OMO_HEADERS)


    def register_firebase(self):
        FIRE_URL = "https://firebaseinstallations.googleapis.com/v1/projects/gallop-28588356/installations"
        FIRE_HEADERS = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Content-Encoding": "gzip",
            "Cache-Control": "no-cache",
            "X-Android-Package": "jp.co.cygames.umamusume",
            "X-Android-Cert": "800CFF70A31C24B5C55E1448843EE25453AFD902",
            "x-goog-api-key": "AIzaSyBlOXUUCnIb5zssdk-_Sq0QNViUi_EE0io",
        }
        self.firebase["gmp_appid"] = "1:134325780869:android:" + codecs.encode(secrets.token_bytes(8), 'hex').decode("utf8")
        FIRE_DATA = {
            "fid": base64.b64encode(secrets.token_bytes(16)).strip(b"=").decode("utf8"),
            "appId": self.firebase["gmp_appid"],
            "authVersion": "FIS_v2",
            "sdkVersion": "a:16.3.3",
        }
        print(FIRE_URL)
        r = requests.post(FIRE_URL, data=json.dumps(FIRE_DATA), headers=FIRE_HEADERS)
        print(r.text)
        con = json.loads(r.text)
        print()

        self.firebase["fid"] = con["fid"]
        self.firebase["fire_url"] = "https://firebaseinstallations.googleapis.com/v1/projects" + con["name"]
        self.firebase["refresh_token"] = con["refreshToken"]
        self.firebase["auth_token"] = con["authToken"]["token"]

        self.checkin()
        self.get_token()

    def refresh_token(self):
        data = self.firebase["auth_token"].split('.')[1]
        exptime = json.loads(base64.b64decode(data+"="*(4-(len(data)%4))))["exp"]
        now = int(time.time())
        if now < exptime:
            return

        FIRE_URL = "https://firebaseinstallations.googleapis.com/v1/projects/gallop-28588356/installations" + "/" + self.firebase["fid"] + "/authTokens:generate"
        FIRE_HEADERS = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Content-Encoding": "gzip",
            "Cache-Control": "no-cache",
            "X-Android-Package": "jp.co.cygames.umamusume",
            "X-Android-Cert": "800CFF70A31C24B5C55E1448843EE25453AFD902",
            "x-goog-api-key": "AIzaSyBlOXUUCnIb5zssdk-_Sq0QNViUi_EE0io",
            "Authorization": "FIS_v2 " + self.firebase["refresh_token"]
        }
        FIRE_DATA = {
            "installation": {
                "sdkVersion": "a:16.3.3",
            },
        }
        print(FIRE_URL)
        r = requests.post(FIRE_URL, data=json.dumps(FIRE_DATA), headers=FIRE_HEADERS)
        print(r.text)
        con = json.loads(r.text)
        print()

        self.firebase["auth_token"] = con["token"]
        self.get_token()

    def checkin(self):
        cr = checkin_pb2.CheckinRequest()
        cr.imei = "".join(random.choice("0123456789") for _ in range(15))
        cr.androidId= 0
        cr.checkin.build.fingerprint = "google/razor/flo:5.0.1/LRX22C/1602158:user/release-keys"
        cr.checkin.build.hardware = "flo"
        cr.checkin.build.brand = "google"
        cr.checkin.build.radio = "FLO-04.04"
        cr.checkin.build.clientId = "android-google"
        cr.checkin.lastCheckinMs = 0

        #cr.desiredBuild
        cr.locale = "en"
        cr.loggingId = random.getrandbits(63)
        #cr.marketCheckin
        cr.macAddress.append("".join(random.choice("ABCDEF0123456789") for _ in range(12)))
        cr.meid = "".join(random.choice("0123456789") for _ in range(14))
        cr.accountCookie.append("")
        cr.timeZone = "GMT"
        cr.version = 3
        cr.otaCert.append("--no-output--") # 71Q6Rn2DDZl1zPDVaaeEHItd
        #cr.serial
        cr.esn = "".join(random.choice("ABCDEF0123456789") for _ in range(8))
        #cr.deviceConfiguration
        cr.macAddressType.append("wifi")
        cr.fragment = 0
        #cr.username
        cr.userSerialNumber = 0

        data = cr.SerializeToString()
        headers = {"Content-type": "application/x-protobuffer",
                   "Accept-Encoding": "gzip",
                   "User-Agent": "Android-Checkin/2.0 (vbox86p JLS36G); gzip"}

        r = requests.post("https://android.clients.google.com/checkin", headers=headers, data=data)

        if r.status_code == 200:
            cresp = checkin_pb2.CheckinResponse()
            cresp.ParseFromString(r.content)
            self.firebase["android_id"] = str(cresp.androidId)
            self.firebase["security_token"] = str(cresp.securityToken)
            self.firebase["version_info"] = cresp.versionInfo
        else:
            print(r.text)
            sys.exit(0)

    def get_token(self):
        FCM_URL = "https://android.clients.google.com/c2dm/register3"
        #FCM_URL = "https://fcmtoken.googleapis.com/register"
        FCM_HEADERS = {
            "Content-type": "application/x-www-form-urlencoded",
            "Authorization": "AidLogin " + self.firebase["android_id"] + ":" + self.firebase["security_token"],
            "gcm_ver": "211816037",
            "app": "jp.co.cygames.umamusume",
        }
        FCM_DATA = {
            "X-subtype": "134325780869",
            'X-scope': '*',
            "sender": "134325780869",
            "X-app": "jp.co.cygames.umamusume",
            "X-app_ver_name": "v1.3.2",
            "X-Goog-Firebase-Installations-Auth": self.firebase["auth_token"],
            "X-gmp_app_id": self.firebase["gmp_appid"],
            "X-appid": self.firebase["fid"],
            "device": self.firebase["android_id"],
            "info": self.firebase["version_info"],
            "plat": "0",
            "gcm_ver": "211816037",
            "cert": "800CFF70A31C24B5C55E1448843EE25453AFD902",
            "target_ver": 28,
            "app": "jp.co.cygames.umamusume",
            "app_ver": self.app_ver,
            'X-Firebase-Client': 'fire-abt/17.1.1+fire-installations/16.3.1+fire-android/+fire-analytics/17.4.2+fire-iid/20.2.0+fire-rc/17.0.0+fire-fcm/20.2.0+fire-cls/17.0.0+fire-cls-ndk/17.0.0+fire-core/19.3.0',
            'X-Firebase-Client-Log-Type': '1',
        }
        print(FCM_URL)
        r = requests.post(FCM_URL, data=FCM_DATA, headers=FCM_HEADERS)
        self.token = r.text.split("=")[1]
        print(self.token)
        print()
        if 'Error' in r.text:
            sys.exit(0)

    def unregister_firebase(self):
        FIRE_URL = "https://firebaseinstallations.googleapis.com/v1/projects/gallop-28588356/installations" + "/" + self.firebase["fid"]
        FIRE_HEADERS = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Content-Encoding": "gzip",
            "Cache-Control": "no-cache",
            "X-Android-Package": "jp.co.cygames.umamusume",
            "X-Android-Cert": "800CFF70A31C24B5C55E1448843EE25453AFD902",
            "x-goog-api-key": "AIzaSyBlOXUUCnIb5zssdk-_Sq0QNViUi_EE0io",
            "Authorization": "FIS_v2 " + self.firebase["refresh_token"]
        }
        print(FIRE_URL)
        r = requests.delete(FIRE_URL, headers=FIRE_HEADERS)
        print(r.text)
        print()

    def register_event(self):
        now = datetime.now(timezone.utc).astimezone(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')
        OMO_URL = requests.utils.requote_uri("https://omotenashi.cygames.jp/api/v1/MeasurementEvent?APP_ID=110&INSTALL_ID=AA0000000000&EVENT_DATE=%s&RETRY_COUNT=0&APP_VIEWER_ID=%s&SDK_VERSION=4.24.0&EVENT_ID=10002" % (now, self.app_viewer_id))
        OMO_HEADERS = {
            "Install-id": "AA0000000000",
            "App-version": self.app_ver,
            "Os": "Android",
            "App-salt": "",
            "Environment-mode": "1",
            "Event-date": now,
            "Retry-count": "0",
            "App-viewer-id": self.app_viewer_id,
            "App-id": "110",
            "Sdk-version": "4.24.0",
            "User-agent": "Mozilla/5.0 (Linux; Android 10; SM-A102U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36",
        }
        OMO_DATA = {
                "CURRENCY": "JPY",
                "ACTION": "PushDeviceTokenReceived",
                "ORDER_ID": "JP",
                "PRICE": "0.0",
                "QUANTITY": "0",
                "LABEL": "",
                "EVENT_ID": "10002",
                "ID": "e9ddb9e3dbe41bda26f02bd294927078",
                "SKU": "",
                "ITEM_NAME": self.token,
        }
        print(OMO_URL)
        requests.post(OMO_URL, data=OMO_DATA, headers=OMO_HEADERS)


if __name__ == "__main__":
    app_viewer_id = str(uuid.uuid4())
    omo = Omotenashi(app_viewer_id, "1.3.2")
    omo.register()
    omo.update()

