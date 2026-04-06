# SyncLights.py
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

from ...config import abs_path, get_config
from ...log import log
from ...parse_scene import parse_scene


class SCENE_OT_SyncLights(bpy.types.Operator):
    bl_idname = "scene.sync_lights"
    bl_label = "Sync All Lights"
    bl_description = "For each light in the scene that has a respective node in the respective Godot scene, read the light settings for that node and save them here. On further export, lights in Godot will automatically be set with these values"

    def execute(self, context):
        scene = context.scene
        props = scene.panel_props
        paths = get_config()["defaults"]["paths"].copy()
        if props.same_hierarchy_target.lower() != "default":
            paths["same_hierarchy_target"] = abs_path(props.same_hierarchy_target)
        if props.scene_save_path.lower() != "default":
            paths["scene_save_path"] = abs_path(props.scene_save_path)

        blend_path = os.path.normcase(bpy.data.filepath)

        hierarchy_path_start = blend_path.index(paths["same_hierarchy_target"]) + len(paths["same_hierarchy_target"])
        # remove forward and backward slashes from the beginning of the path
        hierarchy_path = blend_path[hierarchy_path_start : len(blend_path) - len(os.path.basename(blend_path))].lstrip(
            "/\\"
        )

        scene_path = paths["scene_save_path"]

        if paths["scene_use_same_hierarchy"]:
            scene_path = abs_path(os.path.join(os.path.normcase(scene_path), hierarchy_path))

        blend_path = os.path.normcase(bpy.data.filepath)
        filename = os.path.basename(blend_path)
        scene_path = os.path.join(scene_path, os.path.splitext(filename)[0]) + ".tscn"

        try:
            data = parse_scene(scene_path)
            scene.light_panel_props.clear()
            nodes = data["nodes"]
            for obj in bpy.data.objects:
                if obj.type != "LIGHT":
                    continue
                validated_obj_name = obj.name
                for char in '.:@/"%':
                    validated_obj_name = validated_obj_name.replace(char, "_")
                if validated_obj_name in nodes:
                    node_props = nodes[validated_obj_name]["props"]
                    light_panel = scene.light_panel_props.add()
                    light_panel.light = obj
                    node_type = nodes[validated_obj_name]["meta"]["type"]["value"]
                    if node_type != "DirectionalLight3D" and node_type != "OmniLight3D" and node_type != "SpotLight3D":
                        continue
                    light_panel.type = node_type
                    if (
                        not "light_specular" in node_props
                        and nodes[validated_obj_name]["meta"]["type"] == "DirectionalLight3D"
                    ):
                        # has a different default value for DirecitonalLight3D's than OmniLight3D's or SpotLight3D's
                        node_props["light_specular"] = {"type": "number", "value": 1.0}
                    if "light_cull_mask" in node_props:
                        # only store the lower 20 bits, as the rest are managed by godot internally so we never want to change them
                        lower20bits = (1 << 20) - 1
                        node_props["light_cull_mask"]["value"] = node_props["light_cull_mask"]["value"] & lower20bits
                    for prop, value in node_props.items():
                        if hasattr(light_panel, prop):
                            match value["type"]:
                                case "str" | "number" | "bool":
                                    setattr(light_panel, prop, value["value"])
                                case "type_value":
                                    class_name = value["value"]["type"]
                                    match class_name:
                                        case "Color":
                                            setattr(
                                                light_panel,
                                                prop,
                                                [
                                                    value["value"]["args"][0]["value"],
                                                    value["value"]["args"][1]["value"],
                                                    value["value"]["args"][2]["value"],
                                                ],
                                            )
                                        case _:
                                            raise Exception("A type of class " + class_name + " is not supported")
                                case _:
                                    raise Exception("Type " + value["type"] + " is not supported")

        except Exception as e:
            log(repr(e), "ERROR")
            raise e
        return {"FINISHED"}
