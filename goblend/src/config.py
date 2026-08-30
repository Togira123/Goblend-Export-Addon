# config.py
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
import json

from typing import Literal, TypedDict, cast

from .utils import get_root_dir, reset_cache_enums

from . import log

# config file should be named goblend.json

# cache value
root_dir = None

prev_filepath = ""


class CollisionGroup(TypedDict):
    display_name: str
    godot_group_name: str
    description: str


class Layer(TypedDict):
    bit: int
    display_name: str


class CollisionConfig(TypedDict):
    groups: list[CollisionGroup]
    layers: list[Layer]


class GodotScene(TypedDict):
    display_name: str
    name: str
    godot_scene_path: str


class VisualConfig(TypedDict, total=False):
    render_layers: list[Layer]


class NonTotalPaths(TypedDict, total=False):
    same_hierarchy_target: str
    scene_save_path: str
    scene_use_same_hierarchy: bool
    material_save_path: str
    material_use_same_hierarchy: bool
    texture_save_path: str
    texture_use_same_hierarchy: bool
    animation_library_save_path: str
    animation_library_use_same_hierarchy: bool
    animation_save_path: str
    animation_use_same_hierarchy: bool
    shader_save_path: str
    shader_use_same_hierarchy: bool
    mesh_save_path: str
    mesh_use_same_hierarchy: bool
    collision_shapes_save_path: str
    reuse_collision_shapes: bool
    save_material_separately: bool
    save_animation_library_separately: bool
    save_animation_separately: bool
    save_shader_separately: bool
    save_mesh_separately: bool


class Paths(TypedDict):
    same_hierarchy_target: str
    scene_save_path: str
    scene_use_same_hierarchy: bool
    material_save_path: str
    material_use_same_hierarchy: bool
    texture_save_path: str
    texture_use_same_hierarchy: bool
    animation_library_save_path: str
    animation_library_use_same_hierarchy: bool
    animation_save_path: str
    animation_use_same_hierarchy: bool
    shader_save_path: str
    shader_use_same_hierarchy: bool
    mesh_save_path: str
    mesh_use_same_hierarchy: bool
    collision_shapes_save_path: str
    reuse_collision_shapes: bool
    save_material_separately: bool
    save_animation_library_separately: bool
    save_animation_separately: bool
    save_shader_separately: bool
    save_mesh_separately: bool


PathKeysStringVal = Literal[
    "same_hierarchy_target",
    "scene_save_path",
    "material_save_path",
    "texture_save_path",
    "animation_library_save_path",
    "animation_save_path",
    "shader_save_path",
    "collision_shapes_save_path",
    "mesh_save_path",
]

PathKeysBoolVal = Literal[
    "scene_use_same_hierarchy",
    "material_use_same_hierarchy",
    "texture_use_same_hierarchy",
    "animation_library_use_same_hierarchy",
    "animation_use_same_hierarchy",
    "shader_use_same_hierarchy",
    "reuse_collision_shapes",
    "mesh_use_same_hierarchy",
    "save_material_separately",
    "save_animation_library_separately",
    "save_animation_separately",
    "save_shader_separately",
    "save_mesh_separately",
]

PathKeys = PathKeysStringVal | PathKeysBoolVal


class DefaultConfig(TypedDict):
    paths: Paths
    collision_layers: list[int]
    collision_masks: list[int]
    render_layers: list[int]


class NonTotalDefaultConfig(TypedDict, total=False):
    paths: NonTotalPaths
    collision_layers: list[int]
    collision_masks: list[int]
    render_layers: list[int]


class NonTotalConfig(TypedDict, total=False):
    collisions: CollisionConfig
    godot_scenes: list[GodotScene]
    visuals: VisualConfig
    defaults: NonTotalDefaultConfig


class Config(TypedDict):
    collisions: CollisionConfig
    godot_scenes: list[GodotScene]
    visuals: VisualConfig
    defaults: DefaultConfig


config: NonTotalConfig = {}


def get_collision_groups(collision_config: CollisionConfig) -> list[CollisionGroup]:
    groups: list[CollisionGroup] = []
    if "groups" in collision_config:
        groups_config = collision_config["groups"]
        if type(groups_config) is not list:
            raise Exception("Invalid groups attribute")
        seen_names: set[str] = set()
        for group in groups_config:
            if "display_name" in group and "godot_group_name" in group:
                if group["godot_group_name"] in seen_names:
                    raise Exception("Duplicate group name")
                if not (type(group["display_name"]) is str and type(group["godot_group_name"]) is str):
                    raise Exception("Incorrect type for 'display_name' or 'godot_group_name'")
                seen_names.add(group["godot_group_name"])
                obj: CollisionGroup = {
                    "display_name": group["display_name"],
                    "godot_group_name": group["godot_group_name"],
                    "description": "",
                }
                if "description" in group and type(group["description"]) is str:
                    obj["description"] = group["description"]
                groups.append(obj)
            else:
                raise Exception("Malformed collision group")
    return groups


def get_collision_layers(collision_config: CollisionConfig) -> list[Layer]:
    layers: list[Layer] = []
    if "layers" in collision_config:
        layers_config = collision_config["layers"]
        if type(layers_config) is not list:
            raise Exception("Invalid layers attribute")
        seen_bits: set[int] = set()
        for layer in layers_config:
            if "bit" in layer and "display_name" in layer:
                if layer["bit"] in seen_bits:
                    raise Exception("Duplicate bit used in layers")
                if not (type(layer["bit"]) is int and type(layer["display_name"]) is str):
                    raise Exception("Incorrect type for 'bit' or 'display_name'")
                layers.append({"bit": layer["bit"], "display_name": layer["display_name"]})
            else:
                raise Exception("Malformed collision layer")
    return layers


def get_collision_config(config: Config) -> tuple[list[CollisionGroup], list[Layer]]:
    if "collisions" in config:
        groups = get_collision_groups(config["collisions"])
        layers = get_collision_layers(config["collisions"])
        return (groups, layers)
    return ([], [])


def abs_path(path: str) -> str:
    if path.startswith("res://"):
        root_dir = os.path.join(os.path.normcase(get_root_dir()), "")
        path = path.replace("res://", root_dir, 1)
    path = os.path.join(os.path.normcase(path), "")
    return path


def validate_hierarchy_props(paths_config: Paths, key: PathKeysBoolVal, has_hierarchy: bool) -> None:
    if type(paths_config[key]) is not bool:
        raise Exception("Incorrect type for '" + key + "', should be bool")
    if paths_config[key] and not has_hierarchy:
        raise Exception("'same_hierarchy_target' has to be set in order to use '" + key + "'")


def get_default_paths(config: NonTotalDefaultConfig) -> NonTotalPaths:
    paths: NonTotalPaths = {}
    save_keys: list[tuple[PathKeysStringVal, PathKeysBoolVal, str]] = [
        ("scene_save_path", "scene_use_same_hierarchy", "res://goblend/scenes/"),
        ("material_save_path", "material_use_same_hierarchy", "res://goblend/materials/"),
        ("texture_save_path", "texture_use_same_hierarchy", "res://goblend/textures/"),
        ("animation_library_save_path", "animation_library_use_same_hierarchy", "res://goblend/animation_libraries/"),
        ("animation_save_path", "animation_use_same_hierarchy", "res://goblend/animations/"),
        ("shader_save_path", "shader_use_same_hierarchy", "res://goblend/shaders/"),
        ("mesh_save_path", "mesh_use_same_hierarchy", "res://goblend/meshes/"),
    ]
    whether_to_save_separately_keys: list[tuple[PathKeysBoolVal, bool]] = [
        ("save_material_separately", True),
        ("save_animation_library_separately", True),
        ("save_animation_separately", True),
        ("save_shader_separately", True),
        ("save_mesh_separately", False),
    ]

    if "paths" in config:
        paths_config = cast(Paths, config["paths"])
        has_hierarchy = False
        if "same_hierarchy_target" in paths_config:
            if type(paths_config["same_hierarchy_target"]) is str:
                has_hierarchy = True
                paths["same_hierarchy_target"] = abs_path(paths_config["same_hierarchy_target"])
            else:
                raise Exception("Incorrect type for 'same_hierarchy_target', should be string")

        for keys in save_keys:
            if keys[0] in paths_config:
                val = paths_config[keys[0]]
                if type(val) is str:
                    paths[keys[0]] = abs_path(val)
                else:
                    raise Exception("Incorrect type for '" + keys[0] + "', should be string")
            else:
                paths[keys[0]] = abs_path(keys[2])

            if keys[1] in paths_config:
                validate_hierarchy_props(paths_config, keys[1], has_hierarchy)
                paths[keys[1]] = paths_config[keys[1]]
            else:
                paths[keys[1]] = False

        # collision shapes do not have hierarchy setting because we want to be reusing them
        if "collision_shapes_save_path" in paths_config:
            if type(paths_config["collision_shapes_save_path"]) is str:
                paths["collision_shapes_save_path"] = abs_path(paths_config["collision_shapes_save_path"])
            else:
                raise Exception("Incorrect type for 'scene_save_path', should be string")
        else:
            paths["collision_shapes_save_path"] = abs_path("res://goblend/collision_shapes")
        if "reuse_collision_shapes" in paths_config:
            if type(paths_config["reuse_collision_shapes"]) is bool:
                paths["reuse_collision_shapes"] = paths_config["reuse_collision_shapes"]
            else:
                raise Exception("Incorrect type for 'reuse_collision_shapes', should be bool")

        for key_value in whether_to_save_separately_keys:
            if key_value[0] in paths_config:
                if type(paths_config[key_value[0]]) is bool:
                    paths[key_value[0]] = paths_config[key_value[0]]
                else:
                    raise Exception("Incorrect type for '" + key_value[0] + "', should be bool")
            else:
                paths[key_value[0]] = key_value[1]
    else:
        for keys in save_keys:
            paths[keys[0]] = abs_path(keys[2])
            paths[keys[1]] = False
        paths["same_hierarchy_target"] = abs_path("res://")
        paths["collision_shapes_save_path"] = abs_path("res://goblend/collision_shapes")
        paths["reuse_collision_shapes"] = True
        for key_value in whether_to_save_separately_keys:
            paths[key_value[0]] = key_value[1]
    return paths


def get_collision_defaults(config: NonTotalDefaultConfig) -> tuple[list[int], list[int], list[int]]:
    layers = [0]
    if "collision_layers" in config:
        if type(config["collision_layers"]) is list:
            for bit in config["collision_layers"]:
                if type(bit) is not int:
                    raise Exception("Incorrect type for element of 'collision_layers', should be int")
            layers = config["collision_layers"]
        else:
            raise Exception("Incorrect type for 'collision_layers', should be list")

    masks = [0]
    if "collision_masks" in config:
        if type(config["collision_masks"]) is list:
            for bit in config["collision_masks"]:
                if type(bit) is not int:
                    raise Exception("Incorrect type for element of 'collision_masks', should be int")
            masks = config["collision_masks"]
        else:
            raise Exception("Incorrect type for 'collision_masks', should be list")

    render_layers = [0]
    if "render_layers" in config:
        if type(config["render_layers"]) is list:
            for bit in config["render_layers"]:
                if type(bit) is not int:
                    raise Exception("Incorrect type for element of 'render_layers', should be int")
            render_layers = config["render_layers"]
        else:
            raise Exception("Incorrect type for 'render_layers', should be list")

    return (layers, masks, render_layers)


def get_defaults(config: NonTotalConfig) -> NonTotalDefaultConfig:
    defaults: NonTotalDefaultConfig = {}
    if "defaults" in config:
        defaults["paths"] = get_default_paths(config["defaults"])
        layers, masks, render_layers = get_collision_defaults(config["defaults"])
        defaults["collision_layers"] = layers
        defaults["collision_masks"] = masks
        defaults["render_layers"] = render_layers
    else:
        defaults["paths"] = get_default_paths({})  # will get default paths
        layers, masks, render_layers = get_collision_defaults({})
        defaults["collision_layers"] = layers
        defaults["collision_masks"] = masks
        defaults["render_layers"] = render_layers

    return defaults


def get_godot_scenes(config: NonTotalConfig) -> list[GodotScene]:
    scenes: list[GodotScene] = []
    if "godot_scenes" in config:
        conf_scenes = config["godot_scenes"]
        if type(conf_scenes) is list:
            for scene in conf_scenes:
                if type(scene) is dict and "display_name" in scene and "name" in scene and "godot_scene_path" in scene:
                    if (
                        type(scene["display_name"]) is str
                        and type(scene["name"]) is str
                        and type(scene["godot_scene_path"]) is str
                    ):
                        scenes.append(
                            {
                                "display_name": scene["display_name"],
                                "name": scene["name"],
                                "godot_scene_path": scene["godot_scene_path"],
                            }
                        )
                    else:
                        raise Exception(
                            "'display_name', 'name' and 'godot_scene_path' in 'godot_scenes' all have to be strings"
                        )
                else:
                    raise Exception(
                        "'godot_scenes' array element is missing at least one required key ('display_name', 'name' and 'godot_scene_path')"
                    )
        else:
            raise Exception("Incorrect type for 'godot_scenes', should be list")
    return scenes


def get_render_layers(visual_config: VisualConfig) -> list[Layer]:
    layers: list[Layer] = []
    if "render_layers" in visual_config:
        layers_config = visual_config["render_layers"]
        if type(layers_config) is not list:
            raise Exception("Invalid layers attribute")
        seen_bits: set[int] = set()
        for layer in layers_config:
            if "bit" in layer and "display_name" in layer:
                if layer["bit"] in seen_bits:
                    raise Exception("Duplicate bit used in layers")
                if not (type(layer["bit"]) is int and type(layer["display_name"]) is str):
                    raise Exception("Incorrect type for 'bit' or 'display_name'")
                layers.append({"bit": layer["bit"], "display_name": layer["display_name"]})
            else:
                raise Exception("Malformed render layer")
    return layers


def get_visual_settings(config: Config) -> VisualConfig:
    visuals: VisualConfig = {}
    layers = []
    if "visuals" in config:
        layers = get_render_layers(config["visuals"])
    visuals["render_layers"] = layers
    return visuals


def read_config() -> None:
    global config
    root_dir = get_root_dir()
    config_file_name = "goblend.json"
    file = os.path.join(root_dir, config_file_name)
    if os.path.isfile(file):
        try:
            with open(file, "r") as f:
                content = json.load(f)
                groups, layers = get_collision_config(content)
                config["collisions"] = {"groups": groups, "layers": layers}
                config["defaults"] = get_defaults(content)
                config["godot_scenes"] = get_godot_scenes(content)
                config["visuals"] = get_visual_settings(content)
                return

        except FileNotFoundError:
            log.log("No config found")
        except json.JSONDecodeError:
            log.log("Config contains invalid json", "ERROR")
        except Exception as e:
            log.log("Exception while reading config: " + repr(e), "ERROR")

    config["collisions"] = {"groups": [], "layers": []}
    config["defaults"] = get_defaults({})
    config["godot_scenes"] = get_godot_scenes({})
    config["visuals"] = {"render_layers": []}


@bpy.app.handlers.persistent
def get_config_at_startup(_file: str) -> None:
    get_config()


def get_config() -> Config:
    global config
    global prev_filepath
    if not config or prev_filepath != bpy.data.filepath:
        prev_filepath = bpy.data.filepath
        read_config()
        # reset cached values
        reset_cache_enums()
        log.log("Config loaded:\n" + str(config))
    return cast(Config, config)
