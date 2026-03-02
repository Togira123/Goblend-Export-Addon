from .. import __package__ as base_package

import bpy
import datetime
import os

from .utils import get_root_dir

log_file = None


def init_log_file():
    global log_file
    if log_file:
        # old file was not closed for some reason
        log_file.close()
    root_dir = get_root_dir()
    if root_dir == "":
        return False
    file_path = os.path.join(root_dir, "goblend.log")
    try:
        log_file = open(file_path, "a")
        return True
    except:
        log_file = None
        return False


def close_log_file():
    global log_file
    if log_file:
        log_file.close()
        log_file = None


def log(message, type="INFO"):
    global log_file
    msg = type + ": " + str(message)
    now = datetime.datetime.now()
    msg = ("[%02d:%02d:%02d] (BLEND) " % (now.hour, now.minute, now.second)) + msg
    print(msg)
    addon_prefs = bpy.context.preferences.addons[base_package].preferences
    if addon_prefs.create_log_file:
        if init_log_file():
            log_file.write(msg + "\n")
            close_log_file()
