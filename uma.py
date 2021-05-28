# -*- coding: utf-8 -*-

import os
import sys
import json
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

    def training(self):
        INFO("Training uma")
        fp = open(self.path, "r")
        for line in fp.readlines():
            data = json.loads(line)
            derby = Derby(data)
            derby.uma_login()
            derby.uma_daily()
            info = derby.uma_info()
            INFO("fcoin %d" % info["fcoin"])
            INFO("sc: %s" % (str(info["support_card_list"])))
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

if __name__ == "__main__":
    # test
    SET_LOG_LEVEL(3)
    teio = Teio()
    #teio.breeding()
    #teio.training()
    #teio.gacha()
    teio.test()

