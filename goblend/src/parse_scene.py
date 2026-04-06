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


def parse_float(scene, state, idx):
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


def parse_number(scene, state, idx):
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


def parse_string(scene, state, idx):
    s = ""
    for i in range(idx, len(scene)):
        if scene[i] == '"':
            state["last_read_string"] = s
            return i + 1
        s += scene[i]
    raise Exception("Non-terminated string")


def parse_arguments(scene, state, idx):
    i = idx
    scene_len = len(scene)
    args = []
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


def parse_type_value(scene, state, idx):
    i = parse_identifier(scene, state, idx)
    if state["last_read_identifier"] == "true" or state["last_read_identifier"] == "false":
        state["last_read_type_value"] = True if state["last_read_identifier"] == "true" else False
        return i
    else:
        identifier = state["last_read_identifier"]
        if scene[i] == "(":
            i = parse_arguments(scene, state, i + 1)
            if scene[i] == ")":
                state["last_read_type_value"] = {"type": identifier, "args": state["last_read_arguments"]}
                return i + 1
        raise Exception("Unexpected token when parsing type value: " + scene[i])


def parse_identifier(scene, state, idx):
    id = ""
    for i in range(idx, len(scene)):
        if scene[i].isalnum() or scene[i] == "_" or scene[i] == "/":
            id += scene[i]
        else:
            state["last_read_identifier"] = id
            return i
    state["last_read_identifier"] = id
    return len(scene)


def parse_key(scene, state, idx):
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


def parse_value(scene, state, idx):
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
        i = parse_type_value(scene, state, idx)
        type_value = state["last_read_type_value"]
        if type_value == True or type_value == False:
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


def parse_object(scene, state, idx):
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


def parse_kv_pairs(scene, state, idx):
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


def parse_gd_scene(scene, data, state, idx):
    i = parse_kv_pairs(scene, state, idx)
    if scene[i] != "]":
        raise Exception("Unexpected token when parsing gd_scene header: " + scene[i])
    i += 1
    meta = state["last_read_kv_pairs"]
    data["gd_scene"] = {"meta": meta}
    i = parse_kv_pairs(scene, state, i)
    data["gd_scene"]["props"] = state["last_read_kv_pairs"]
    return i


def parse_connection(scene, data, state, idx):
    i = parse_kv_pairs(scene, state, idx)
    if scene[i] != "]":
        raise Exception("Unexpected token when parsing connection header: " + scene[i])
    i += 1
    meta = state["last_read_kv_pairs"]
    if not "signal" in meta:
        raise Exception("Missing signal attribute in connection header")
    data["connections"][meta["signal"]["value"]] = {"meta": meta}
    i = parse_kv_pairs(scene, state, i)
    data["connections"][meta["meta"]["value"]]["props"] = state["last_read_kv_pairs"]
    return i


def parse_sub_resource(scene, data, state, idx):
    i = parse_kv_pairs(scene, state, idx)
    if scene[i] != "]":
        raise Exception("Unexpected token when parsing sub_resource header: " + scene[i])
    i += 1
    meta = state["last_read_kv_pairs"]
    if not "id" in meta:
        raise Exception("Missing id attribute in sub_resource header")
    data["sub_resources"][meta["id"]["value"]] = {"meta": meta}
    i = parse_kv_pairs(scene, state, i)
    data["sub_resources"][meta["id"]["value"]]["props"] = state["last_read_kv_pairs"]
    return i


def parse_ext_resource(scene, data, state, idx):
    i = parse_kv_pairs(scene, state, idx)
    if scene[i] != "]":
        raise Exception("Unexpected token when parsing ext_resource header: " + scene[i])
    i += 1
    meta = state["last_read_kv_pairs"]
    if not "id" in meta:
        raise Exception("Missing id attribute in ext_resource header")
    data["ext_resources"][meta["id"]["value"]] = {"meta": meta}
    i = parse_kv_pairs(scene, state, i)
    data["ext_resources"][meta["id"]["value"]]["props"] = state["last_read_kv_pairs"]
    return i


def parse_node(scene, data, state, idx):
    i = parse_kv_pairs(scene, state, idx)
    if scene[i] != "]":
        raise Exception("Unexpected token when parsing node header: " + scene[i])
    i += 1
    meta = state["last_read_kv_pairs"]
    if not "name" in meta:
        raise Exception("Missing name attribute in node header")
    data["nodes"][meta["name"]["value"]] = {"meta": meta}
    i = parse_kv_pairs(scene, state, i)
    data["nodes"][meta["name"]["value"]]["props"] = state["last_read_kv_pairs"]
    return i


def parse_resource(scene, data, state, idx):
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


def parse_scene(path):
    data = {"nodes": {}, "ext_resources": {}, "sub_resources": {}, "connections": {}, "gd_scene": {}}
    state = {
        "last_read_string": "",
        "last_read_identifier": "",
        "last_read_kv_pairs": {},
        "last_read_type_key": "",
        "last_read_key": "",
        "last_read_value": "",
        "last_read_number": 0,
        "last_read_type_value": None,
        "last_read_arguments": [],
        "last_read_array": [],
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
