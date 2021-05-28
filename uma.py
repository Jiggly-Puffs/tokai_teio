# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import pprint
from derby import Derby
from utils.logger import *


class Teio(object):

    def __init__(self):
        self.path = "data/derby.json"

    def breeding(self, name=None, sex=None):
        INFO("Breeding uma")
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
        INFO("Daily uma")
        fp = open(self.path, "r")
        for line in fp.readlines():
            data = json.loads(line)
            derby = Derby(data)
            derby.uma_login()
            derby.uma_daily()
            info = derby.uma_info()
            INFO("fcoin %d" % info["fcoin"])
            print()

    def gacha(self):
        derby = self.breeding()
        info = derby.uma_gacha_strategy_three()
        INFO("sc: %s" % (str(info["support_card_list"])))

    def test(self):
        data = json.loads(open(self.path, "r").readlines()[-1])
        derby = Derby(data)
        derby.uma_login()
        derby.uma_daily()
        derby.uma_support_card_limit_break_all()
        info = derby.uma_info()
        INFO("fcoin %d" % info["fcoin"])
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(info["support_card_list"])
        derby.uma_account_trans("abcABC123")

    def batch_breeding(self, num):
        SET_LOG_LEVEL(2)  # info
        for i in range(num):
            self.breeding()
            time.sleep(5)


if __name__ == "__main__":
    # test
    SET_LOG_LEVEL(3)
    teio = Teio()
    #teio.breeding()
    #teio.training()
    #teio.gacha()
    #teio.test()
    teio.batch_breeding(50)

