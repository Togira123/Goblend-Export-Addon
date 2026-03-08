import bpy
import os
import json

from .utils import get_root_dir, reset_cache_enums

from . import log

# config file should be named goblend.json

# cache value
root_dir = None

prev_filepath = ""


def get_collision_groups(collision_config):
    groups = []
    if "groups" in collision_config:
        groups_config = collision_config["groups"]
        if not type(groups_config) is list:
            raise Exception("Invalid groups attribute")
        seen_names = set()
        for group in groups_config:
            if "display_name" in group and "godot_group_name" in group:
                if group["godot_group_name"] in seen_names:
                    raise Exception("Duplicate group name")
                if not (type(group["display_name"]) is str and type(group["godot_group_name"]) is str):
                    raise Exception("Incorrect type for 'display_name' or 'godot_group_name'")
                seen_names.add(group["godot_group_name"])
                obj = {"display_name": group["display_name"], "godot_group_name": group["godot_group_name"]}
                if "description" in group and type(group["description"]) is str:
                    obj["description"] = group["description"]
                else:
                    obj["description"] = ""
                groups.append(obj)
            else:
                raise Exception("Malformed collision group")
    return groups


def get_collision_layers(collision_config):
    layers = []
    if "layers" in collision_config:
        layers_config = collision_config["layers"]
        if not type(layers_config) is list:
            raise Exception("Invalid layers attribute")
        seen_bits = set()
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


def get_collision_config(config):
    if "collisions" in config:
        groups = get_collision_groups(config["collisions"])
        layers = get_collision_layers(config["collisions"])
        return (groups, layers)
    return ([], [])


def abs_path(path):
    if not path.endswith("/"):
        path = path + "/"
    if path.startswith("res://"):
        root_dir = get_root_dir()
        if not root_dir.endswith("/"):
            root_dir = root_dir + "/"
        return path.replace("res://", root_dir, 1)
    return path


def validate_hierarchy_props(paths_config, key, has_hierarchy):
    if not type(paths_config[key]) is bool:
        raise Exception("Incorrect type for '" + key + "', should be bool")
    if paths_config[key] and not has_hierarchy:
        raise Exception("'same_hierarchy_target' has to be set in order to use '" + key + "'")


def get_default_paths(config):
    paths = {}
    save_keys = [
        ["scene_save_path", "scene_use_same_hierarchy", "res://goblend/scenes/"],
        ["material_save_path", "material_use_same_hierarchy", "res://goblend/materials/"],
        ["texture_save_path", "texture_use_same_hierarchy", "res://goblend/textures/"],
        ["animation_library_save_path", "animation_library_use_same_hierarchy", "res://goblend/animation_libraries/"],
        ["animation_save_path", "animation_use_same_hierarchy", "res://goblend/animations/"],
        ["shader_save_path", "shader_use_same_hierarchy", "res://goblend/shaders/"],
    ]
    if "paths" in config:
        paths_config = config["paths"]
        has_hierarchy = False
        if "same_hierarchy_target" in paths_config:
            if type(paths_config["same_hierarchy_target"]) is str:
                has_hierarchy = True
                paths["same_hierarchy_target"] = abs_path(paths_config["same_hierarchy_target"])
            else:
                raise Exception("Incorrect type for 'same_hierarchy_target', should be string")

        for keys in save_keys:
            if keys[0] in paths_config:
                if type(paths_config[keys[0]]) is str:
                    paths[keys[0]] = abs_path(paths_config[keys[0]])
                else:
                    raise Exception("Incorrect type for 'scene_save_path', should be string")
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
    else:
        for keys in save_keys:
            paths[keys[0]] = abs_path(keys[2])
            paths[keys[1]] = False
        paths["same_hierarchy_target"] = abs_path("res://")
        paths["collision_shapes_save_path"] = abs_path("res://goblend/collision_shapes")
        paths["reuse_collision_shapes"] = True
    return paths


def get_collision_defaults(config):
    layers = []
    if "collision_layers" in config:
        if type(config["collision_layers"]) is list:
            for bit in config["collision_layers"]:
                if not type(bit) is int:
                    raise Exception("Incorrect type for element of 'collision_layers', should be int")
            layers = config["collision_layers"]
        else:
            raise Exception("Incorrect type for 'collision_layers', should be list")

    masks = []
    if "collision_masks" in config:
        if type(config["collision_masks"]) is list:
            for bit in config["collision_masks"]:
                if not type(bit) is int:
                    raise Exception("Incorrect type for element of 'collision_masks', should be int")
            masks = config["collision_masks"]
        else:
            raise Exception("Incorrect type for 'collision_masks', should be list")
    return (layers, masks)


def get_defaults(config):
    defaults = {}
    if "defaults" in config:
        defaults["paths"] = get_default_paths(config["defaults"])
        layers, masks = get_collision_defaults(config["defaults"])
        defaults["collision_layers"] = layers
        defaults["collision_masks"] = masks
    else:
        defaults["paths"] = get_default_paths({})  # will get default paths
        layers, masks = get_collision_defaults({})
        defaults["collision_layers"] = layers
        defaults["collision_masks"] = masks

    return defaults


def get_godot_scenes(config):
    scenes = []
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


config = {}


def read_config():
    global config
    root_dir = get_root_dir()
    config_file_name = "goblend.json"
    file = os.path.join(root_dir, config_file_name)
    if os.path.isfile(file):
        try:
            with open(file, "r") as f:
                content = json.load(f)
                groups, layers = get_collision_config(content)
                config["collisions"] = {}
                config["collisions"]["groups"] = groups
                config["collisions"]["layers"] = layers
                config["defaults"] = get_defaults(content)
                config["godot_scenes"] = get_godot_scenes(content)
                return

        except FileNotFoundError:
            log.log("No config found")
        except json.JSONDecodeError:
            log.log("Config contains invalid json", "ERROR")
        except Exception as e:
            log.log("Exception while reading config: " + repr(e), "ERROR")

    config["collisions"] = {}
    config["collisions"]["groups"] = []
    config["collisions"]["layers"] = []
    config["defaults"] = get_defaults({})
    config["godot_scenes"] = get_godot_scenes({})


@bpy.app.handlers.persistent
def get_config_at_startup(_file):
    get_config()


def get_config():
    global config
    global prev_filepath
    if not config or prev_filepath != bpy.data.filepath:
        prev_filepath = bpy.data.filepath
        read_config()
        # reset cached values
        reset_cache_enums()
        log.log("Config loaded:\n" + str(config))
    return config
