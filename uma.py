# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import pprint
from derby import Derby
import logging
logger = logging.getLogger(__name__)


class ShutdownHandler(logging.StreamHandler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            sys.exit(1)


class Teio(object):

    def __init__(self):
        self.path = "data/derby.json"

    def breeding(self, name=None, sex=None):
        derby = Derby()
        derby.uma_signup()
        if name or sex:
            derby.set_name_sex(name, sex)
        derby.uma_daily()
        self.save(derby.tojson())
        return derby

    def save(self, data):
        open(self.path, "a+").write(data+"\n")

    def daily(self):
        logger.info("Daily uma")
        num = 1
        with open(self.path, "r") as fp:
            for line in fp.readlines():
                logger.info("Uma %d" % num)
                data = json.loads(line)
                derby = Derby(data)
                derby.uma_login()
                derby.uma_daily()
                info = derby.uma_info()
                logger.info("fcoin %d" % info["fcoin"])
                num += 1

    def test_gacha(self):
        derby = self.breeding()
        info = derby.uma_gacha_strategy_three()
        logger.info("sc: %s" % (str(info["support_card_list"])))

    def test(self):
        data = json.loads(open(self.path, "r").readlines()[-1])
        derby = Derby(data)
        derby.uma_login()
        derby.uma_daily()
        derby.uma_support_card_limit_break_all()
        info = derby.uma_info()
        logger.info("fcoin %d" % info["fcoin"])
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(info["support_card_list"])
        derby.uma_account_trans("abcABC123")

    def batch_breeding(self, num):
        for i in range(num):
            logger.info("Breeding uma %d" % (i+1))
            self.breeding()
            time.sleep(3)

    def gacha(self):
        num = 1
        with open(self.path, "r") as fp:
            for line in fp.readlines():
                logger.info("Uma %d" % num)
                data = json.loads(line)
                derby = Derby(data)
                derby.uma_login()
                derby.uma_daily()
                info = derby.uma_gacha_strategy_three()
                sr = 0
                ssr = 0
                for sc in info["support_card_list"]:
                    if sc["support_card_id"] > 20000:
                        if sc["support_card_id"] > 30000:
                            ssr += sc["limit_break_count"] + sc["stock"]
                        else:
                            sr += sc["limit_break_count"] + sc["stock"]
                logger.info("SSR: %d, SR: %d" % (ssr, sr))
                if ssr >= 6:
                    for sc in info["support_card_list"]:
                        if sc["support_card_id"] > 30000:
                            logger.info("%s" % str(sc))
                num += 1
                if num > 50:
                    break



if __name__ == "__main__":
    # test
    import coloredlogs
    coloredlogs.install(logging.INFO)
    logging.getLogger().addHandler(ShutdownHandler())

    import dotenv
    dotenv.load_dotenv() # install .env into os.env

    teio = Teio()
    #teio.training()
    teio.gacha()
    #teio.test()
    #teio.batch_breeding(50)
    #teio.daily()

