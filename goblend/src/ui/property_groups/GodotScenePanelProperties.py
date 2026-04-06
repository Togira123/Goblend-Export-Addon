# GodotScenePanelProperties.py
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

from ... import config as conf
from ... import utils


def is_godot_scene(self, obj):
    scene = bpy.context.scene
    for item in scene.godot_scene_panel_props:
        if obj == item.obj:
            return False
    godot_scenes = bpy.data.collections.get("GodotScenes")
    if not godot_scenes:
        return False
    return obj.name in godot_scenes.objects


def scenes(_self, _context):
    if len(utils.godot_scene_panel_props_enum_cache) == 0:
        config = conf.get_config()
        for scene in config["godot_scenes"]:
            utils.godot_scene_panel_props_enum_cache.append(
                (scene["name"], scene["display_name"], "Godot Scene at: " + scene["godot_scene_path"])
            )

    return utils.godot_scene_panel_props_enum_cache


class GodotScenePanelProperties(bpy.types.PropertyGroup):
    open: bpy.props.BoolProperty(default=True)
    obj: bpy.props.PointerProperty(
        name="Target Object",
        description="The object to be replaced with the scene.",
        type=bpy.types.Object,
        poll=is_godot_scene,
    )
    scene: bpy.props.EnumProperty(
        name="Scene",
        description="The Godot Scene to place at the object's position. Use the config file to register more scenes.",
        items=scenes,
    )
