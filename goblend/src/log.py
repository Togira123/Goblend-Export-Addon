# log.py
#
# Copyright (C) 2026-present Goblend contributers, see https://github.com/Togira123/Goblend-Export-Addon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>


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
