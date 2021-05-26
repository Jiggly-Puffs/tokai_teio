# -*- coding: utf-8 -*-
import sys
from termcolor import colored

LOG_LEVEL = 3
FILELOG = False
LOGFILE = ""

def LOG(level, color, formatStr, *arg):
    if arg:
        if FILELOG:
            with open(LOGFILE, 'a+') as f:
                f.write((formatStr + '\n') % arg)
        if LOG_LEVEL >= level:
            print(colored((formatStr) % arg, color))
    else:
        if FILELOG:
            with open(LOGFILE, 'a+') as f:
                f.write(formatStr + '\n')
        if LOG_LEVEL >= level:
            print(colored(formatStr, color))


def INFO(formatStr, *arg):
    LOG(2, "green", "[INFO] "+formatStr, *arg)


def WARN(formatStr, *arg):
    LOG(1, "yellow", "[WARN] "+formatStr, *arg)


def ERROR(formatStr, *arg):
    LOG(0, "red", "[ERROR] "+formatStr, *arg)
    sys.exit(0)
    '''
    if config.FILELOG:
        with open(config.ERRLOG, 'a+') as f:
            if arg:
                f.write((formatStr + '\n') % arg)
            else:
                f.write(formatStr + '\n')
    '''

def DEBUG(formatStr, *arg):
    LOG(3, "blue", "[DEBUG] "+formatStr, *arg)


def TRACE(formatStr, *arg):
    LOG(4, "grey", "[TRACE] "+formatStr, *arg)
