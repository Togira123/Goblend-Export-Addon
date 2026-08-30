# parse_scene.py
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


import os

from typing import TypedDict, cast


class TypeValue(TypedDict):
    type: str
    args: list["LastReadValue"]


class LastReadValue(TypedDict):
    type: str
    value: str | int | float | list["LastReadValue"] | dict[str, "LastReadValue"] | bool | TypeValue


class Node(TypedDict):
    meta: dict[str, LastReadValue]
    props: dict[str, LastReadValue]


class Scene(TypedDict):
    nodes: dict[str, Node]
    ext_resources: dict
    sub_resources: dict
    connections: dict
    gd_scene: dict


class State(TypedDict):
    last_read_string: str
    last_read_identifier: str
    last_read_kv_pairs: dict[str, LastReadValue]
    last_read_type_key: str
    last_read_key: str
    last_read_value: LastReadValue
    last_read_number: int | float
    last_read_type_value: bool | TypeValue
    last_read_arguments: list[LastReadValue]
    last_read_object: dict[str, LastReadValue]


def parse_float(scene: str, state: State, idx: int) -> int:
    f = ""
    seen_dot = False
    seen_e = 0
    if scene[idx] == "-":
        f = "-"
        idx += 1
    for i in range(idx, len(scene)):
        if scene[i].isnumeric():
            f += scene[i]
        elif scene[i] == "." and not seen_dot:
            seen_dot = True
            f += scene[i]
        elif scene[i] == "e" and seen_e == 0:
            seen_e = i
            f += scene[i]
        elif scene[i] == "-" and seen_e == i - 1:
            f += scene[i]
        else:
            state["last_read_number"] = float(f)
            return i
    state["last_read_number"] = float(f)
    return len(scene)


def parse_number(scene: str, state: State, idx: int) -> int:
    n = ""
    minus = 0
    if scene[idx] == "-":
        n = "-"
        minus = 1
    for i in range(idx + minus, len(scene)):
        if scene[i].isnumeric():
            n += scene[i]
            i += 1
        elif scene[i] == ".":
            i = parse_float(scene, state, idx)
            return i
        elif scene[i] == "e":
            i = parse_float(scene, state, idx)
            return i
        else:
            state["last_read_number"] = int(n)
            return i
    state["last_read_number"] = int(n)
    return len(scene)


def parse_string(scene: str, state: State, idx: int) -> int:
    s = ""
    for i in range(idx, len(scene)):
        if scene[i] == '"':
            state["last_read_string"] = s
            return i + 1
        s += scene[i]
    raise Exception("Non-terminated string")


def parse_arguments(scene: str, state: State, idx: int) -> int:
    i = idx
    scene_len = len(scene)
    args: list[LastReadValue] = []
    while i < scene_len:
        while i < scene_len and scene[i].isspace():
            i += 1
        i = parse_value(scene, state, i)
        arg = state["last_read_value"]
        args.append(arg)
        while i < scene_len and scene[i].isspace():
            i += 1
        if scene[i] != ",":
            state["last_read_arguments"] = args
            return i
        i += 1
    state["last_read_arguments"] = args
    return scene_len


def parse_type_value(scene: str, state: State, idx: int) -> int:
    i = parse_identifier(scene, state, idx)
    if state["last_read_identifier"] == "true" or state["last_read_identifier"] == "false":
        state["last_read_type_value"] = state["last_read_identifier"] == "true"
        return i
    else:
        identifier = state["last_read_identifier"]
        if scene[i] == "(":
            i = parse_arguments(scene, state, i + 1)
            if scene[i] == ")":
                state["last_read_type_value"] = {"type": identifier, "args": state["last_read_arguments"]}
                return i + 1
        raise Exception("Unexpected token when parsing type value: " + scene[i])


def parse_identifier(scene: str, state: State, idx: int) -> int:
    id = ""
    for i in range(idx, len(scene)):
        if scene[i].isalnum() or scene[i] == "_" or scene[i] == "/":
            id += scene[i]
        else:
            state["last_read_identifier"] = id
            return i
    state["last_read_identifier"] = id
    return len(scene)


def parse_key(scene: str, state: State, idx: int) -> int:
    if scene[idx] == '"':
        i = parse_string(scene, state, idx + 1)
        key = state["last_read_string"]
        state["last_read_key"] = key
        return i
    elif scene[idx].isalpha() or scene[idx] == "_" or scene[idx] == "/":
        i = parse_identifier(scene, state, idx)
        key = state["last_read_identifier"]
        state["last_read_key"] = key
        return i
    else:
        raise Exception("Unexpected token when parsing key: " + scene[idx])


def parse_value(scene: str, state: State, idx: int) -> int:
    if scene[idx] == '"':
        i = parse_string(scene, state, idx + 1)
        value = state["last_read_string"]
        state["last_read_value"] = {"type": "str", "value": value}
        return i
    elif scene[idx].isnumeric() or scene[idx] == "-":
        i = parse_number(scene, state, idx)
        value = state["last_read_number"]
        state["last_read_value"] = {"type": "number", "value": value}
        return i
    elif scene[idx].isalnum() or scene[idx] == "_":
        # parses either booleans or godot types (e.g. ExtResource)
        i = parse_type_value(scene, state, idx)
        type_value = state["last_read_type_value"]
        if isinstance(type_value, bool):
            state["last_read_value"] = {"type": "bool", "value": type_value}
        else:
            state["last_read_value"] = {"type": "type_value", "value": type_value}
        return i
    elif scene[idx] == "[":
        i = parse_arguments(scene, state, idx + 1)
        if scene[i] != "]":
            raise Exception("Unexpected token when parsing array: " + scene[i])
        array = state["last_read_arguments"]
        state["last_read_value"] = {"type": "array", "value": array}
        return i + 1
    elif scene[idx] == "{":
        i = parse_object(scene, state, idx + 1)
        if scene[i] != "}":
            raise Exception("Unexpected token when parsing array: " + scene[i])
        obj = state["last_read_object"]
        state["last_read_value"] = {"type": "object", "value": obj}
        return i + 1
    else:
        raise Exception("Unexpected token when parsing value: " + scene[idx])


def parse_object(scene: str, state: State, idx: int) -> int:
    obj = {}
    i = idx
    scene_len = len(scene)
    while i < scene_len:
        while i < scene_len and scene[i].isspace():
            i += 1
        if scene[i] != '"':
            state["last_read_object"] = obj
            return i
        i = parse_string(scene, state, i + 1)
        key = state["last_read_string"]
        while i < scene_len and scene[i].isspace():
            i += 1
        if scene[i] != ":":
            raise Exception("Unexpected token when parsing key value pairs: " + scene[i])
        i += 1
        while i < scene_len and scene[i].isspace():
            i += 1
        i = parse_value(scene, state, i)
        value = state["last_read_value"]
        obj[key] = value
        while i < scene_len and scene[i].isspace():
            i += 1
        if scene[i] != ",":
            state["last_read_object"] = obj
            return i
        i += 1

    state["last_read_object"] = obj
    return scene_len


def parse_kv_pairs(scene: str, state: State, idx: int) -> int:
    properties = {}
    i = idx
    scene_len = len(scene)
    while i < scene_len:
        while i < scene_len and scene[i].isspace():
            i += 1
        if i == scene_len:
            state["last_read_kv_pairs"] = properties
            return i
        if scene[i] != '"' and not scene[i].isalpha() and scene[i] != "_" and scene[i] != "/":
            state["last_read_kv_pairs"] = properties
            return i
        i = parse_key(scene, state, i)
        key = state["last_read_key"]
        while i < scene_len and scene[i].isspace():
            i += 1
        if scene[i] != "=":
            raise Exception("Unexpected token when parsing key value pairs: " + scene[i])
        i += 1
        while i < scene_len and scene[i].isspace():
            i += 1
        i = parse_value(scene, state, i)
        value = state["last_read_value"]
        properties[key] = value

    state["last_read_kv_pairs"] = properties
    return scene_len


def parse_gd_scene(scene: str, data: Scene, state: State, idx: int) -> int:
    i = parse_kv_pairs(scene, state, idx)
    if scene[i] != "]":
        raise Exception("Unexpected token when parsing gd_scene header: " + scene[i])
    i += 1
    meta = state["last_read_kv_pairs"]
    data["gd_scene"] = {"meta": meta}
    i = parse_kv_pairs(scene, state, i)
    data["gd_scene"]["props"] = state["last_read_kv_pairs"]
    return i


def parse_connection(scene: str, data: Scene, state: State, idx: int) -> int:
    i = parse_kv_pairs(scene, state, idx)
    if scene[i] != "]":
        raise Exception("Unexpected token when parsing connection header: " + scene[i])
    i += 1
    meta = state["last_read_kv_pairs"]
    if "signal" not in meta:
        raise Exception("Missing signal attribute in connection header")
    data["connections"][meta["signal"]["value"]] = {"meta": meta}
    i = parse_kv_pairs(scene, state, i)
    data["connections"][meta["meta"]["value"]]["props"] = state["last_read_kv_pairs"]
    return i


def parse_sub_resource(scene: str, data: Scene, state: State, idx: int) -> int:
    i = parse_kv_pairs(scene, state, idx)
    if scene[i] != "]":
        raise Exception("Unexpected token when parsing sub_resource header: " + scene[i])
    i += 1
    meta = state["last_read_kv_pairs"]
    if "id" not in meta:
        raise Exception("Missing id attribute in sub_resource header")
    data["sub_resources"][meta["id"]["value"]] = {"meta": meta}
    i = parse_kv_pairs(scene, state, i)
    data["sub_resources"][meta["id"]["value"]]["props"] = state["last_read_kv_pairs"]
    return i


def parse_ext_resource(scene: str, data: Scene, state: State, idx: int) -> int:
    i = parse_kv_pairs(scene, state, idx)
    if scene[i] != "]":
        raise Exception("Unexpected token when parsing ext_resource header: " + scene[i])
    i += 1
    meta = state["last_read_kv_pairs"]
    if "id" not in meta:
        raise Exception("Missing id attribute in ext_resource header")
    data["ext_resources"][meta["id"]["value"]] = {"meta": meta}
    i = parse_kv_pairs(scene, state, i)
    data["ext_resources"][meta["id"]["value"]]["props"] = state["last_read_kv_pairs"]
    return i


def parse_node(scene: str, data: Scene, state: State, idx: int) -> int:
    i = parse_kv_pairs(scene, state, idx)
    if scene[i] != "]":
        raise Exception("Unexpected token when parsing node header: " + scene[i])
    i += 1
    meta = state["last_read_kv_pairs"]
    if "name" not in meta:
        raise Exception("Missing name attribute in node header")
    val = meta["name"]["value"]
    if type(val) is not str:
        raise Exception("Node name should be string")
    i = parse_kv_pairs(scene, state, i)
    node_dict: Node = {"meta": meta, "props": state["last_read_kv_pairs"]}
    data["nodes"][val] = node_dict
    return i


def parse_resource(scene: str, data: Scene, state: State, idx: int) -> int:
    i = parse_identifier(scene, state, idx)
    def_type = state["last_read_identifier"]
    match def_type:
        case "node":
            new_idx = parse_node(scene, data, state, i + 1)
        case "ext_resource":
            new_idx = parse_ext_resource(scene, data, state, i + 1)
        case "sub_resource":
            new_idx = parse_sub_resource(scene, data, state, i + 1)
        case "connection":
            new_idx = parse_connection(scene, data, state, i + 1)
        case "gd_scene":
            new_idx = parse_gd_scene(scene, data, state, i + 1)
        case _:
            raise Exception("Unknown header type: " + def_type)
    return new_idx


def parse_scene(path: str) -> Scene:
    data: Scene = {"nodes": {}, "ext_resources": {}, "sub_resources": {}, "connections": {}, "gd_scene": {}}
    state: State = {
        "last_read_string": "",
        "last_read_identifier": "",
        "last_read_kv_pairs": {},
        "last_read_type_key": "",
        "last_read_key": "",
        "last_read_value": cast(
            LastReadValue, {}
        ),  # allow empty object here since we will not read if we have not written to it before
        "last_read_number": 0,
        "last_read_type_value": False,
        "last_read_arguments": [],
        "last_read_object": {},
    }
    if os.path.isfile(path):
        with open(path, "r") as file:
            scene = file.read()
            i = 0
            scene_len = len(scene)
            while i < scene_len:
                if scene[i] == "[":
                    i = parse_resource(scene, data, state, i + 1)
                else:
                    raise Exception("Unexpected token when parsing scene: " + scene[i])
    else:
        raise Exception("Scene file not found")
    return data
