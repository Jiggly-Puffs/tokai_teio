# -*- coding: utf-8 -*-

import os
import sys
import json
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
            derby.uma_info()


if __name__ == "__main__":
    # test
    teio = Teio()
    #teio.breeding()
    teio.training()

