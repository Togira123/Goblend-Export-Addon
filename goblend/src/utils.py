# utils.py
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


import bpy
import os

root_dir = None

layers_enum_cache = []
group_list_enum_cache = []
godot_scene_panel_props_enum_cache = []


def reset_cache_enums():
    global layers_enum_cache
    global group_list_enum_cache
    global godot_scene_panel_props_enum_cache
    layers_enum_cache = []
    group_list_enum_cache = []
    godot_scene_panel_props_enum_cache = []


def get_root_dir():
    global root_dir
    if root_dir != None:
        return root_dir
    if bpy.data.filepath == "":
        return ""
    filepath = os.path.normcase(bpy.data.filepath)
    while True:
        head, _ = os.path.split(filepath)
        if head == filepath:
            # reached root
            break
        files = [f for f in os.listdir(head) if os.path.isfile(os.path.join(head, f))]
        for file in files:
            if file == "project.godot":
                root_dir = head
                break
        filepath = head
    if root_dir == None:
        # no godot project found
        raise Exception("No Godot project found")
    return root_dir
