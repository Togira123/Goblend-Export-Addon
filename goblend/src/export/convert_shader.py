# convert_shader.py
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
import random
import string
from enum import Enum

from ..types.goblend_types import SettingsforGodotLimitUVEffectNormal
from ..log import log

from typing import TypedDict, cast

from collections.abc import Callable


class DataTypes(Enum):
    FLOAT = "float"
    INT = "int"
    VEC2 = "vec2"
    VEC3 = "vec3"
    VEC4 = "vec4"
    BSDF = "BSDF"
    SAMPLER2D = "sampler2D"


# converts a blender shader to a godot shader

fragment_code = ""
structs_code = ""
vertex_code = ""
globals_code = ""

added_structs: set[str] = set()


class VarInfo(TypedDict):
    name: str
    type: DataTypes


nodes_to_vars: dict[bpy.types.Node, dict[bpy.types.NodeSocket, VarInfo]] = dict()
special_var_props: dict[bpy.types.Node, dict[bpy.types.NodeSocket, dict[str, bool]]] = dict()

next_num = 0

is_constant = True
group_nodes_stack: list[bpy.types.Node] = []
visited: set[str] = set()

uniform_vars: set[tuple[str, str, str, str]] = set()


class SpecialVars(TypedDict, total=False):
    uv_flipped: dict[int, str]
    uv: dict[int, str]
    vertex_local: bool


special_vars: SpecialVars = {}

limit_normal_effect = None
# typing this without None because it gets assigned in convert_to_godot_shader
# which is the entry point
obj: bpy.types.Object = cast(bpy.types.Object, None)

uv_base_color_idx = 0
uv_roughness_metallic_idx = 0
uv_normal_idx = 0
is_right_after_bake = False

separator = ""


def add_line(line: str, const: bool, top: bool = False) -> None:
    global fragment_code
    if const:
        if top:
            fragment_code = "\tconst " + line + "\n" + fragment_code
        else:
            fragment_code += "\tconst " + line + "\n"
    else:
        if top:
            fragment_code = "\t" + line + "\n" + fragment_code
        else:
            fragment_code += "\t" + line + "\n"


# only call this after checking that the corresponding entry in special_vars does not exist yet
def add_uv_line(name: str, uv_index: int, flipped: bool) -> None:
    subtract_str = ""
    if flipped:
        subtract_str = "1.0 - "
    if uv_index == 0:
        add_line("vec2 " + name + " = vec2(UV.x, " + subtract_str + "UV.y);", True, True)
    elif uv_index == 1:
        add_line("vec2 " + name + " = vec2(UV2.x, " + subtract_str + "UV2.y);", True, True)
    else:
        custom_idx = str((uv_index // 2) - 1)
        custom = "CUSTOM" + custom_idx
        custom_var = "custom" + custom_idx
        add_global_line("varying vec4 " + custom_var + ";")
        add_vertex_line(custom_var + " = " + custom + ";")
        if uv_index % 2 == 0:
            add_line(
                "vec2 " + name + " = vec2(" + custom_var + ".x, " + subtract_str + custom_var + ".y);",
                False,
                True,
            )
        else:
            add_line(
                "vec2 " + name + " = vec2(" + custom_var + ".z, " + subtract_str + custom_var + ".w);",
                False,
                True,
            )
    if flipped:  # this one is needed when UV coords are used for something other than textures
        if "uv_flipped" not in special_vars:
            special_vars["uv_flipped"] = {}
        special_vars["uv_flipped"][uv_index] = name
    else:
        if "uv" not in special_vars:
            special_vars["uv"] = {}
        special_vars["uv"][uv_index] = name


def add_global_line(line: str) -> None:
    global globals_code
    globals_code += line + "\n"


def add_vertex_line(line: str) -> None:
    global vertex_code
    vertex_code += "\t" + line + "\n"


def add_struct(type: str, vars: dict[str, str]) -> None:
    match type:
        case "BSDF":
            if "BSDF" in added_structs:
                raise Exception("tried adding BSDF struct even though it already exists")
            added_structs.add("BSDF")
            struct = "struct BSDF {\n"
            for key in vars:
                struct += "\t" + vars[key] + " " + key + ";\n"
            struct += "};\n"
            global structs_code
            structs_code += struct


class UnsupportedSocket(Exception):
    def __init__(self, node: bpy.types.Node, socket_name: str) -> None:
        super().__init__("Connecting " + socket_name + " on " + node.bl_idname + " is not supported")


def input_to_data_type(input: bpy.types.NodeSocket) -> DataTypes:
    match input.type:
        case "INT":  # assuming "value" is "float"
            return DataTypes.INT
        case "VALUE":
            return DataTypes.FLOAT
        case "BOOLEAN":
            return DataTypes.INT
        case "VECTOR":
            match len(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)):
                case 2:
                    return DataTypes.VEC2
                case 3:
                    return DataTypes.VEC3
                case 4:
                    return DataTypes.VEC4
                case _:
                    raise Exception(
                        "Unsupported vector length of "
                        + str(len(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)))
                        + ", please report on GitHub"
                    )
        case "RGBA":
            return DataTypes.VEC3
        case _:
            raise Exception("Unsupported type: " + input.type)


# pass None as output to indicate a helper variable
def create_var(node: bpy.types.Node, output: bpy.types.NodeSocket | None, type: DataTypes) -> str:
    global next_num
    name = "v" + str(next_num)
    next_num += 1
    if output is None:
        return name
    if node not in nodes_to_vars:
        nodes_to_vars[node] = dict()

    nodes_to_vars[node][output] = {"name": name, "type": type}
    return name


def add_prop_to_var(node: bpy.types.Node, output: bpy.types.NodeSocket, key: str, val: bool) -> None:
    if node not in special_var_props:
        special_var_props[node] = dict()
    if output in special_var_props[node]:
        special_var_props[node][output][key] = val
    else:
        special_var_props[node][output] = dict([(key, val)])


def get_prop_from_var(node: bpy.types.Node, output: bpy.types.NodeSocket, key: str) -> bool:
    if node not in special_var_props or output not in special_var_props[node]:
        raise Exception("No special properties for node " + node.name)
    return special_var_props[node][output][key]


def get_prop_from_any_child_of_var(
    node: bpy.types.Node, output: bpy.types.NodeSocket, key: str
) -> tuple[bool | None, bool]:
    if node not in special_var_props or output not in special_var_props[node]:
        for inp in node.inputs:
            if inp.is_linked:
                link = cast(bpy.types.NodeLinks, inp.links)[0]
                socket = cast(bpy.types.NodeSocket, link.from_socket)
                parent = cast(bpy.types.Node, link.from_node)
                res = get_prop_from_any_child_of_var(parent, socket, key)
                if res[1]:
                    return res
        return (None, False)
    return (special_var_props[node][output][key], True)


def set_var(node: bpy.types.Node, output: bpy.types.NodeSocket, type: DataTypes, name: str) -> None:
    if node not in nodes_to_vars:
        nodes_to_vars[node] = dict()

    nodes_to_vars[node][output] = {"name": name, "type": type}


def set_var_as_uniform(
    name: str, type: str, linkTo: str, uniform_hint: str
) -> None:  # linkTo can for example be the name of the image for samplers
    uniform_vars.add((name, type, linkTo, uniform_hint))


def get_var(node: bpy.types.Node, input: bpy.types.NodeSocket) -> VarInfo:
    # find the output that connects to this input
    link = cast(bpy.types.NodeLinks, input.links)[0]
    output = cast(bpy.types.NodeSocket, link.from_socket)
    output_node = cast(bpy.types.Node, link.from_node)
    if output_node not in nodes_to_vars or output not in nodes_to_vars[output_node]:
        log(str(output_node))
        log(str(nodes_to_vars[output_node]))
        raise Exception(
            "Variable that is needed for node "
            + node.name
            + ", input "
            + input.name
            + " does not exist, please report on GitHub"
        )
    return nodes_to_vars[output_node][output]


def get_var_name(node: bpy.types.Node, input: bpy.types.NodeSocket) -> str:
    return get_var(node, input)["name"]


def get_var_data_type(node: bpy.types.Node, input: bpy.types.NodeSocket) -> DataTypes:
    return get_var(node, input)["type"]


def beautify_float(f: float) -> str:
    as_str = "%.6f" % f
    as_str = as_str.rstrip("0")
    if as_str.endswith("."):
        as_str = as_str + "0"
    return as_str


def get_constant(node: bpy.types.Node, input: bpy.types.NodeSocket) -> str:
    match input.type:
        case "INT":  # assuming "value" is "float"
            return str(cast(bpy.types.NodeSocketInt, input).default_value)
        case "VALUE":
            return beautify_float(cast(bpy.types.NodeSocketFloat, input).default_value)
        case "BOOLEAN":
            return "true" if cast(bpy.types.NodeSocketBool, input).default_value else "false"
        case "VECTOR":
            match len(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)):
                case 2:
                    return (
                        "vec2("
                        + beautify_float(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[0])
                        + ", "
                        + beautify_float(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[1])
                        + ")"
                    )
                case 3:
                    return (
                        "vec3("
                        + beautify_float(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[0])
                        + ", "
                        + beautify_float(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[1])
                        + ", "
                        + beautify_float(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[2])
                        + ")"
                    )
                case 4:
                    return (
                        "vec4("
                        + beautify_float(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[0])
                        + ", "
                        + beautify_float(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[1])
                        + ", "
                        + beautify_float(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[2])
                        + ", "
                        + beautify_float(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[3])
                        + ")"
                    )
                case _:
                    raise Exception(
                        "Unsupported vector length of "
                        + str(len(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)))
                        + ", please report on GitHub"
                    )
        case "RGBA":
            return (
                "vec3("
                + beautify_float(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[0])
                + ", "
                + beautify_float(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[1])
                + ", "
                + beautify_float(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[2])
                + ")"
            )
        case _:
            raise Exception("Unsupported constant value at " + node.name + " with socket " + input.name)


def get_data_type(node: bpy.types.Node, input: bpy.types.NodeSocket) -> DataTypes:
    match input.type:
        case "VALUE":
            return DataTypes.FLOAT
        case "INT":
            return DataTypes.INT
        case "VECTOR":
            match len(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)):
                case 2:
                    return DataTypes.VEC2
                case 3:
                    return DataTypes.VEC3
                case 4:
                    return DataTypes.VEC4
                case _:
                    raise Exception(
                        "Unsupported vector length of "
                        + str(len(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)))
                        + ", please report on GitHub"
                    )
        case "RGBA":
            return DataTypes.VEC3
        case _:
            raise Exception("Unsupported constant value at " + node.name + " with socket " + input.name)


def reset_is_constant() -> None:
    global is_constant
    is_constant = True


def get_casted_var_or_constant(node: bpy.types.Node, input: bpy.types.NodeSocket, needed_data_type: DataTypes) -> str:
    if input.is_linked:
        global is_constant
        is_constant = False
        var = get_var(node, input)
        return cast_var(var["type"], needed_data_type, var["name"])
    return cast_var(get_data_type(node, input), needed_data_type, get_constant(node, input))


def cast_var(actual: DataTypes, needed: DataTypes, var_name: str) -> str:
    match actual:
        case DataTypes.FLOAT:
            match needed:
                case DataTypes.FLOAT:
                    return var_name
                case DataTypes.INT:
                    return "int(" + var_name + ")"
                case DataTypes.VEC2:
                    return "vec2(" + var_name + ")"
                case DataTypes.VEC3:
                    return "vec3(" + var_name + ")"
                case DataTypes.VEC4:
                    return "vec4(" + var_name + ")"
        case DataTypes.INT:
            match needed:
                case DataTypes.FLOAT:
                    return "float(" + var_name + ")"
                case DataTypes.INT:
                    return var_name
                case DataTypes.VEC2:
                    return "vec2(" + var_name + ")"
                case DataTypes.VEC3:
                    return "vec3(" + var_name + ")"
                case DataTypes.VEC4:
                    return "vec4(" + var_name + ")"
        case DataTypes.VEC2:
            match needed:
                case DataTypes.FLOAT:
                    return "(" + var_name + ".x + " + var_name + ".y) / 2.0"
                case DataTypes.VEC2:
                    return var_name
                case DataTypes.VEC3:
                    return "vec3(" + var_name + ", 0)"
                case DataTypes.VEC4:
                    return "vec4(" + var_name + ", 0, 0)"
        case DataTypes.VEC3:
            match needed:
                case DataTypes.FLOAT:
                    return "(" + var_name + ".x + " + var_name + ".y + " + var_name + ".z) / 3.0"
                case DataTypes.VEC2:
                    return "(" + var_name + ".xy)"
                case DataTypes.VEC3:
                    return var_name
                case DataTypes.VEC4:
                    return "vec4(" + var_name + ", 0)"
        case DataTypes.VEC4:
            match needed:
                case DataTypes.FLOAT:
                    return "(" + var_name + ".x + " + var_name + ".y + " + var_name + ".z + " + var_name + ".w) / 4.0"
                case DataTypes.VEC2:
                    return "(" + var_name + ".xy)"
                case DataTypes.VEC3:
                    return "(" + var_name + ".xyz)"
                case DataTypes.VEC4:
                    return var_name
    raise Exception("Unsupported cast: Cannot cast from " + actual.name + " to " + needed.name)


def socket_is_zero(input: bpy.types.NodeSocket) -> bool:
    if input.is_linked:
        return False  # if socket is connected assume for simplicity that it's not 0
    match input.type:
        case "INT":
            return cast(bpy.types.NodeSocketInt, input).default_value == 0
        case "VALUE":
            return cast(bpy.types.NodeSocketFloat, input).default_value == 0.0
        case "BOOLEAN":
            return not cast(bpy.types.NodeSocketBool, input).default_value
        case "VECTOR":
            match len(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)):
                case 2:
                    return (
                        cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[0] == 0.0
                        and cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[1] == 0.0
                    )
                case 3:
                    return (
                        cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[0] == 0.0
                        and cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[1] == 0.0
                        and cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[2] == 0.0
                    )
                case 4:
                    return (
                        cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[0] == 0.0
                        and cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[1] == 0.0
                        and cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[2] == 0.0
                        and cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[3] == 0.0
                    )
                case _:
                    return False
        case _:
            return False


def socket_is_one(input: bpy.types.NodeSocket) -> bool:
    if input.is_linked:
        return False  # if socket is connected assume for simplicity that it's not 0
    match input.type:
        case "INT":
            return cast(bpy.types.NodeSocketInt, input).default_value == 1
        case "VALUE":
            return cast(bpy.types.NodeSocketFloat, input).default_value == 1.0
        case "BOOLEAN":
            return cast(bpy.types.NodeSocketBool, input).default_value
        case "VECTOR":
            match len(cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)):
                case 2:
                    return (
                        cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[0] == 1.0
                        and cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[1] == 1.0
                    )
                case 3:
                    return (
                        cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[0] == 1.0
                        and cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[1] == 1.0
                        and cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[2] == 1.0
                    )
                case 4:
                    return (
                        cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[0] == 1.0
                        and cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[1] == 1.0
                        and cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[2] == 1.0
                        and cast(list[float], cast(bpy.types.NodeSocketVector, input).default_value)[3] == 1.0
                    )
                case _:
                    return False
        case _:
            return False


def init_tex_coord(node: bpy.types.Node, uv_index: int) -> None:
    if cast(bpy.types.ShaderNodeTexCoord, node).from_instancer:
        raise Exception('Setting "From Instancer" on Texture Coordinate Node is not supported')
    if cast(bpy.types.ShaderNodeTexCoord, node).object is not None:
        raise Exception('Setting "Object" on Texture Coordinate Node is not supported')

    for output in node.outputs:
        if output.is_linked:
            match output.name:
                case "UV":
                    if "uv_flipped" in special_vars and uv_index in special_vars["uv_flipped"]:
                        uv_var = special_vars["uv_flipped"][uv_index]
                        set_var(node, output, DataTypes.VEC2, uv_var)
                    else:
                        var_name = create_var(node, output, DataTypes.VEC2)
                        add_uv_line(var_name, uv_index, True)
                        add_prop_to_var(node, output, "is_uv_value", True)
                case "Object":
                    if "vertex_local" not in special_vars:
                        add_global_line("varying vec3 vertex_local;")
                        add_vertex_line("vertex_local = VERTEX;")
                        special_vars["vertex_local"] = True
                    var_name = create_var(node, output, DataTypes.VEC3)
                    add_line(
                        "vec3 " + var_name + " = vec3(vertex_local.x, -vertex_local.z, vertex_local.y);",
                        False,
                    )
                case _:
                    raise UnsupportedSocket(node, output.name)


def init_math(node: bpy.types.Node) -> None:
    line = ""
    var_name = create_var(node, node.outputs[0], DataTypes.FLOAT)  # math nodes only have one output
    use_clamp = cast(bpy.types.ShaderNodeMath, node).use_clamp

    reset_is_constant()

    def line_two_in(
        node: bpy.types.Node,
        op: str,
        ind1: int = 0,
        ind2: int = 1,
        str1: str | None = None,
        str2: str | None = None,
        is_inline: bool = False,
    ) -> str:
        expr = (
            (
                ("(" + str1 + ")")
                if str1 is not None
                else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.FLOAT)
            )
            + " "
            + op
            + " "
            + (
                ("(" + str2 + ")")
                if str2 is not None
                else get_casted_var_or_constant(node, node.inputs[ind2], DataTypes.FLOAT)
            )
        )
        if is_inline:
            return expr
        if use_clamp:
            expr = "clamp(" + expr + ", 0.0, 1.0)"
        return "float " + var_name + " = " + expr

    def one_param_fn(
        node: bpy.types.Node, fn: str, ind1: int = 0, str1: str | None = None, is_inline: bool = False
    ) -> str:
        expr = (
            fn
            + "("
            + (str1 if str1 is not None else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.FLOAT))
            + ")"
        )
        if is_inline:
            return expr
        if use_clamp:
            expr = "clamp(" + expr + ", 0.0, 1.0)"
        return "float " + var_name + " = " + expr

    def two_param_fn(
        node: bpy.types.Node,
        fn: str,
        ind1: int = 0,
        ind2: int = 1,
        str1: str | None = None,
        str2: str | None = None,
        is_inline: bool = False,
    ) -> str:
        expr = (
            fn
            + "("
            + (str1 if str1 is not None else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.FLOAT))
            + ", "
            + (str2 if str2 is not None else get_casted_var_or_constant(node, node.inputs[ind2], DataTypes.FLOAT))
            + ")"
        )
        if is_inline:
            return expr
        if use_clamp:
            expr = "clamp(" + expr + ", 0.0, 1.0)"
        return "float " + var_name + " = " + expr

    def three_param_fn(
        node: bpy.types.Node,
        fn: str,
        ind1: int = 0,
        ind2: int = 1,
        ind3: int = 2,
        str1: str | None = None,
        str2: str | None = None,
        str3: str | None = None,
        is_inline: bool = False,
    ) -> str:
        expr = (
            fn
            + "("
            + (str1 if str1 is not None else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.FLOAT))
            + ", "
            + (str2 if str2 is not None else get_casted_var_or_constant(node, node.inputs[ind2], DataTypes.FLOAT))
            + ", "
            + (str3 if str3 is not None else get_casted_var_or_constant(node, node.inputs[ind3], DataTypes.FLOAT))
            + ")"
        )
        if is_inline:
            return expr
        if use_clamp:
            expr = "clamp(" + expr + ", 0.0, 1.0)"
        return "float " + var_name + " = " + expr

    def ternary(
        node: bpy.types.Node,
        ind1: int = 0,
        ind2: int = 1,
        ind3: int = 2,
        str1: str | None = None,
        str2: str | None = None,
        str3: str | None = None,
        is_inline: bool = False,
    ) -> str:
        expr = (
            (
                ("(" + str1 + ")")
                if str1 is not None
                else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.FLOAT)
            )
            + " ? "
            + (
                ("(" + str2 + ")")
                if str2 is not None
                else get_casted_var_or_constant(node, node.inputs[ind2], DataTypes.FLOAT)
            )
            + " : "
            + (
                ("(" + str3 + ")")
                if str3 is not None
                else get_casted_var_or_constant(node, node.inputs[ind3], DataTypes.FLOAT)
            )
        )
        if is_inline:
            return expr
        if use_clamp:
            expr = "clamp(" + expr + ", 0.0, 1.0)"
        return "float " + var_name + " = " + expr

    add_semicolon = True

    match cast(bpy.types.ShaderNodeMath, node).operation:
        case "ADD":
            line = line_two_in(node, "+")
        case "SUBTRACT":
            line = line_two_in(node, "-")
        case "MULTIPLY":
            line = line_two_in(node, "*")
        case "DIVIDE":
            line = line_two_in(node, "/")
        case "MULTIPLY_ADD":
            line = three_param_fn(node, "fma")
        case "POWER":
            line = two_param_fn(node, "pow")
        case "LOGARITHM":
            line = line_two_in(
                node,
                "/",
                -1,
                -1,
                one_param_fn(node, "log2", is_inline=True),
                one_param_fn(node, "log2", 1, is_inline=True),
            )
        case "SQRT":
            line = ternary(
                node,
                -1,
                -1,
                -1,
                line_two_in(node, "<=", 0, -1, None, "0.0", True),
                "0.0",
                one_param_fn(node, "sqrt", is_inline=True),
            )
        case "INVERSE_SQRT":
            line = ternary(
                node,
                -1,
                -1,
                -1,
                line_two_in(node, "<=", 0, -1, None, "0.0", True),
                "0.0",
                one_param_fn(node, "inversesqrt", is_inline=True),
            )
        case "ABSOLUTE":
            line = one_param_fn(node, "abs")
        case "EXPONENT":
            line = one_param_fn(node, "exp")
        case "MINIMUM":
            line = two_param_fn(node, "min")
        case "MAXIMUM":
            line = two_param_fn(node, "max")
        case "LESS_THAN":
            line = ternary(node, -1, -1, -1, line_two_in(node, "<", is_inline=True), "1.0", "0.0")
        case "GREATER_THAN":
            line = ternary(node, -1, -1, -1, line_two_in(node, ">", is_inline=True), "1.0", "0.0")
        case "SIGN":
            line = one_param_fn(node, "sign")

        # smooth min blender source code (https://projects.blender.org/blender/blender/src/commit/39dbd17e92f41925011ae9b427eae474e81c5f6e/intern/cycles/util/math_base.h#L450):
        # params are a, b, k
        # if (k != 0.0f) {
        #   const float h = fmaxf(k - fabsf(a - b), 0.0f) / k;
        #   return fminf(a, b) - h * h * h * k * (1.0f / 6.0f);
        # }
        # return fminf(a, b);

        # smooth_max is same as smooth_min but a, b and result negated
        case "SMOOTH_MIN" | "SMOOTH_MAX":
            add_semicolon = False
            tmp_var_name = create_var(node, None, DataTypes.FLOAT)
            a_minus_b = (
                get_casted_var_or_constant(node, node.inputs[0], DataTypes.FLOAT)
                + " - "
                + get_casted_var_or_constant(node, node.inputs[1], DataTypes.FLOAT)
            )
            a_negated = get_casted_var_or_constant(node, node.inputs[0], DataTypes.FLOAT)
            b_negated = get_casted_var_or_constant(node, node.inputs[1], DataTypes.FLOAT)
            if cast(bpy.types.ShaderNodeMath, node).operation == "SMOOTH_MAX":
                a_minus_b = "-(" + a_minus_b + ")"
                a_negated = "-(" + a_negated + ")"
                b_negated = "-(" + b_negated + ")"
            line = "float " + var_name + ";\n"
            line += "\tif (" + line_two_in(node, "!=", 2, -1, None, "0.0", True) + ") {\n"
            line += (
                "\t\tfloat "
                + tmp_var_name
                + " = "
                + line_two_in(
                    node,
                    "/",
                    -1,
                    2,
                    two_param_fn(
                        node,
                        "max",
                        -1,
                        -1,
                        line_two_in(
                            node,
                            "-",
                            2,
                            -1,
                            None,
                            one_param_fn(node, "abs", -1, a_minus_b, True),
                            True,
                        ),
                        "0.0",
                        True,
                    ),
                    None,
                    True,
                )
                + ";\n\t\t"
            )
            line += (
                var_name
                + " = "
                + line_two_in(
                    node,
                    "-",
                    -1,
                    -1,
                    two_param_fn(node, "min", -1, -1, a_negated, b_negated, True),
                    tmp_var_name
                    + " * "
                    + tmp_var_name
                    + " * "
                    + tmp_var_name
                    + " * "
                    + line_two_in(node, "*", 2, -1, None, "(1.0 / 6.0)", True),
                    True,
                )
                + ";\n\t} else {\n\t\t"
                + var_name
                + " = "
                + two_param_fn(node, "min", -1, -1, a_negated, b_negated, True)
                + ";\n\t}"
            )
        case "COMPARE":
            # blender source code: ((Value1 == Value2) || (abs(Value1 - Value2) <= max(Value3, 1e-5))) ? 1.0 : 0.0;
            line = ternary(
                node,
                -1,
                -1,
                -1,
                line_two_in(
                    node,
                    "||",
                    -1,
                    -1,
                    line_two_in(node, "==", is_inline=True),
                    line_two_in(
                        node,
                        "<=",
                        -1,
                        -1,
                        one_param_fn(node, "abs", -1, line_two_in(node, "-", is_inline=True), True),
                        two_param_fn(node, "max", 2, -1, None, "1e-5", True),
                        True,
                    ),
                    True,
                ),
                "1.0",
                "0.0",
            )
        case "ROUND":
            line = one_param_fn(node, "round")
        case "FLOOR":
            line = one_param_fn(node, "floor")
        case "CEIL":
            line = one_param_fn(node, "ceil")
        case "TRUNC":
            line = one_param_fn(node, "trunc")
        case "FRACT":
            line = one_param_fn(node, "fract")
        case "MODULO":
            line = ternary(
                node,
                -1,
                -1,
                -1,
                line_two_in(node, "!=", 1, -1, None, "0.0", True),
                line_two_in(
                    node,
                    "-",
                    0,
                    -1,
                    None,
                    line_two_in(
                        node,
                        "*",
                        -1,
                        1,
                        one_param_fn(node, "trunc", -1, line_two_in(node, "/", is_inline=True), True),
                        is_inline=True,
                    ),
                    True,
                ),
                "0.0",
            )
        case "FLOORED_MODULO":
            line = ternary(
                node,
                -1,
                -1,
                -1,
                line_two_in(node, "!=", 1, -1, None, "0.0", True),
                two_param_fn(node, "mod", is_inline=True),
                "0.0",
            )
        # blender source code:
        # float range = max - min;
        # return (range != 0.0) ? value - (range * floor((value - min) / range)) : min;
        case "WRAP":
            tmp_var_name = create_var(node, None, DataTypes.FLOAT)
            line = "float " + tmp_var_name + " = " + line_two_in(node, "-", 1, 2, is_inline=True) + ";\n\t"
            cond = line_two_in(node, "!=", -1, -1, tmp_var_name, "0.0", True)
            expr1 = line_two_in(
                node,
                "-",
                0,
                -1,
                None,
                line_two_in(
                    node,
                    "*",
                    -1,
                    -1,
                    tmp_var_name,
                    one_param_fn(
                        node,
                        "floor",
                        -1,
                        line_two_in(
                            node, "/", -1, -1, line_two_in(node, "-", 0, 2, is_inline=True), tmp_var_name, True
                        ),
                        True,
                    ),
                    True,
                ),
                True,
            )
            line += ternary(node, -1, -1, 2, cond, expr1)
        # blender source code: floor(safe_divide(a, b)) * b;
        case "SNAP":
            line = line_two_in(
                node,
                "*",
                -1,
                1,
                one_param_fn(
                    node,
                    "floor",
                    -1,
                    ternary(
                        node,
                        -1,
                        -1,
                        -1,
                        line_two_in(node, "!=", 1, -1, None, "0.0", True),
                        line_two_in(node, "/", is_inline=True),
                        "0.0",
                        is_inline=True,
                    ),
                    True,
                ),
            )
        # blender source code: (b != 0.0) ? abs(fract((a - b) / (b * 2.0)) * b * 2.0 - b) : 0.0;
        case "PINGPONG":
            line = ternary(
                node,
                -1,
                -1,
                -1,
                line_two_in(node, "!=", 1, -1, None, "0.0", True),
                one_param_fn(
                    node,
                    "abs",
                    -1,
                    line_two_in(
                        node,
                        "-",
                        -1,
                        1,
                        line_two_in(
                            node,
                            "*",
                            -1,
                            -1,
                            one_param_fn(
                                node,
                                "fract",
                                -1,
                                line_two_in(
                                    node,
                                    "/",
                                    -1,
                                    -1,
                                    line_two_in(node, "-", is_inline=True),
                                    line_two_in(node, "*", 1, -1, None, "2.0", True),
                                    True,
                                ),
                                True,
                            ),
                            line_two_in(node, "*", 1, -1, None, "2.0", True),
                            True,
                        ),
                        is_inline=True,
                    ),
                    True,
                ),
                "0.0",
            )
        case "SINE":
            line = one_param_fn(node, "sin")
        case "COSINE":
            line = one_param_fn(node, "cos")
        case "TANGENT":
            line = one_param_fn(node, "tan")
        case "ARCSINE":
            line = one_param_fn(node, "asin", -1, three_param_fn(node, "clamp", 0, -1, -1, None, "-1.0", "1.0", True))
        case "ARCCOSINE":
            line = one_param_fn(node, "acos", -1, three_param_fn(node, "clamp", 0, -1, -1, None, "-1.0", "1.0", True))
        case "ARCTANGENT":
            line = one_param_fn(node, "atan")
        case "ARCTAN2":
            line = two_param_fn(node, "atan")
        case "SINH":
            line = one_param_fn(node, "sinh")
        case "COSH":
            line = one_param_fn(node, "cosh")
        case "TANH":
            line = one_param_fn(node, "tanh")
        case "RADIANS":
            line = one_param_fn(node, "radians")
        case "DEGREES":
            line = one_param_fn(node, "degrees")
        case _:
            raise UnsupportedSocket(node, node.operation)

    add_line(line + (";" if add_semicolon else ""), is_constant)


def init_vector_math(node: bpy.types.Node) -> None:
    line = ""
    var_str = "vec3 "
    var_name = ""
    match cast(bpy.types.ShaderNodeVectorMath, node).operation:
        case "DOT_PRODUCT" | "DISTANCE" | "LENGTH":
            var_str = "float "
            var_name = create_var(node, node.outputs.get("Value"), DataTypes.FLOAT)
        case _:
            var_name = create_var(node, node.outputs.get("Vector"), DataTypes.VEC3)

    reset_is_constant()

    def line_two_in(
        node: bpy.types.Node,
        op: str,
        ind1: int = 0,
        ind2: int = 1,
        str1: str | None = None,
        str2: str | None = None,
        snd_arg_data_type: DataTypes = DataTypes.VEC3,
        is_inline: bool = False,
    ) -> str:
        expr = (
            (
                ("(" + str1 + ")")
                if str1 is not None
                else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.VEC3)
            )
            + " "
            + op
            + " "
            + (
                ("(" + str2 + ")")
                if str2 is not None
                else get_casted_var_or_constant(node, node.inputs[ind2], snd_arg_data_type)
            )
        )
        if is_inline:
            return expr
        return var_str + var_name + " = " + expr

    def one_param_fn(
        node: bpy.types.Node, fn: str, ind1: int = 0, str1: str | None = None, is_inline: bool = False
    ) -> str:
        expr = (
            fn
            + "("
            + (str1 if str1 is not None else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.VEC3))
            + ")"
        )
        if is_inline:
            return expr
        return var_str + var_name + " = " + expr

    def two_param_fn(
        node: bpy.types.Node,
        fn: str,
        ind1: int = 0,
        ind2: int = 1,
        str1: str | None = None,
        str2: str | None = None,
        is_inline: bool = False,
    ) -> str:
        expr = (
            fn
            + "("
            + (str1 if str1 is not None else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.VEC3))
            + ", "
            + (str2 if str2 is not None else get_casted_var_or_constant(node, node.inputs[ind2], DataTypes.VEC3))
            + ")"
        )
        if is_inline:
            return expr
        return var_str + var_name + " = " + expr

    def three_param_fn(
        node: bpy.types.Node,
        fn: str,
        ind1: int = 0,
        ind2: int = 1,
        ind3: int = 2,
        str1: str | None = None,
        str2: str | None = None,
        str3: str | None = None,
        third_arg_data_type: DataTypes = DataTypes.VEC3,
        is_inline: bool = False,
    ) -> str:
        expr = (
            fn
            + "("
            + (str1 if str1 is not None else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.VEC3))
            + ", "
            + (str2 if str2 is not None else get_casted_var_or_constant(node, node.inputs[ind2], DataTypes.VEC3))
            + ", "
            + (str3 if str3 is not None else get_casted_var_or_constant(node, node.inputs[ind3], third_arg_data_type))
            + ")"
        )
        if is_inline:
            return expr
        return var_str + var_name + " = " + expr

    def ternary(
        node: bpy.types.Node,
        ind1: int = 0,
        ind2: int = 1,
        ind3: int = 2,
        str1: str | None = None,
        str2: str | None = None,
        str3: str | None = None,
        ret_type: DataTypes = DataTypes.FLOAT,
        is_inline: bool = False,
    ) -> str:
        expr = (
            (
                ("(" + str1 + ")")
                if str1 is not None
                else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.FLOAT)
            )
            + " ? "
            + (
                ("(" + str2 + ")")
                if str2 is not None
                else get_casted_var_or_constant(node, node.inputs[ind2], ret_type)
            )
            + " : "
            + (
                ("(" + str3 + ")")
                if str3 is not None
                else get_casted_var_or_constant(node, node.inputs[ind3], ret_type)
            )
        )
        if is_inline:
            return expr
        if ret_type == DataTypes.FLOAT:
            return "float " + var_name + " = " + expr
        else:
            return "vec3 " + var_name + " = " + expr

    add_semicolon = True

    match cast(bpy.types.ShaderNodeVectorMath, node).operation:
        case "ADD":
            line = line_two_in(node, "+")
        case "SUBTRACT":
            line = line_two_in(node, "-")
        case "MULTIPLY":
            line = line_two_in(node, "*")
        case "DIVIDE":
            line = line_two_in(node, "/")
        case "MULTIPLY_ADD":
            line = three_param_fn(node, "fma")
        case "CROSS_PRODUCT":
            line = two_param_fn(node, "cross")
        case "PROJECT":
            tmp_var_name = create_var(node, None, DataTypes.FLOAT)
            line = "float " + tmp_var_name + " = " + two_param_fn(node, "dot", 1, 1, is_inline=True) + ";\n\t"
            line += ternary(
                node,
                -1,
                -1,
                -1,
                line_two_in(node, "!=", -1, -1, tmp_var_name, "0.0", is_inline=True),
                line_two_in(
                    node,
                    "*",
                    -1,
                    1,
                    line_two_in(
                        node, "/", -1, -1, two_param_fn(node, "dot", is_inline=True), tmp_var_name, is_inline=True
                    ),
                    is_inline=True,
                ),
                one_param_fn(node, "vec3", -1, "0.0", True),
                DataTypes.VEC3,
            )
        case "REFLECT":
            line = two_param_fn(node, "reflect", 0, -1, None, one_param_fn(node, "normalize", 1, is_inline=True))
        case "REFRACT":
            line = three_param_fn(
                node,
                "refract",
                0,
                -1,
                2,
                None,
                one_param_fn(node, "normalize", 1, is_inline=True),
                third_arg_data_type=DataTypes.FLOAT,
            )
        case "FACEFORWARD":
            line = three_param_fn(node, "faceforward")
        case "DOT_PRODUCT":
            line = two_param_fn(node, "dot")
        case "DISTANCE":
            line = two_param_fn(node, "distance")
        case "LENGTH":
            line = one_param_fn(node, "length")
        case "SCALE":
            line = line_two_in(node, "*", snd_arg_data_type=DataTypes.FLOAT)
        case "NORMALIZE":
            line = one_param_fn(node, "normalize")
        case "ABSOLUTE":
            line = one_param_fn(node, "abs")
        case "POWER":
            line = two_param_fn(node, "pow")
        case "SIGN":
            line = one_param_fn(node, "sign")
        case "MINIMUM":
            line = two_param_fn(node, "min")
        case "MAXIMUM":
            line = two_param_fn(node, "max")
        case "ROUND":
            line = one_param_fn(node, "round")
        case "FLOOR":
            line = one_param_fn(node, "floor")
        case "CEIL":
            line = one_param_fn(node, "ceil")
        case "FRACTION":
            line = one_param_fn(node, "fract")
        case "MODULO":
            # we have to separate into each coordinate because we have to check for divisions by 0
            x_coord_0 = get_casted_var_or_constant(node, node.inputs[0], DataTypes.VEC3) + ".x"
            y_coord_0 = get_casted_var_or_constant(node, node.inputs[0], DataTypes.VEC3) + ".y"
            z_coord_0 = get_casted_var_or_constant(node, node.inputs[0], DataTypes.VEC3) + ".z"
            x_coord_1 = get_casted_var_or_constant(node, node.inputs[1], DataTypes.VEC3) + ".x"
            y_coord_1 = get_casted_var_or_constant(node, node.inputs[1], DataTypes.VEC3) + ".y"
            z_coord_1 = get_casted_var_or_constant(node, node.inputs[1], DataTypes.VEC3) + ".z"

            def mod_one_coord(coord_0: str, coord_1: str) -> str:
                return ternary(
                    node,
                    -1,
                    -1,
                    -1,
                    line_two_in(node, "!=", -1, -1, coord_1, "0.0", is_inline=True),
                    line_two_in(
                        node,
                        "-",
                        -1,
                        -1,
                        coord_0,
                        line_two_in(
                            node,
                            "*",
                            -1,
                            -1,
                            one_param_fn(
                                node,
                                "trunc",
                                -1,
                                line_two_in(node, "/", -1, -1, coord_0, coord_1, is_inline=True),
                                True,
                            ),
                            coord_1,
                            is_inline=True,
                        ),
                        is_inline=True,
                    ),
                    "0.0",
                    is_inline=True,
                )

            line = three_param_fn(
                node,
                "vec3",
                -1,
                -1,
                -1,
                mod_one_coord(x_coord_0, x_coord_1),
                mod_one_coord(y_coord_0, y_coord_1),
                mod_one_coord(z_coord_0, z_coord_1),
            )
        case "WRAP":
            # we have to separate into each coordinate because we have to check for divisions by 0
            x_coord_0 = get_casted_var_or_constant(node, node.inputs[0], DataTypes.VEC3) + ".x"
            y_coord_0 = get_casted_var_or_constant(node, node.inputs[0], DataTypes.VEC3) + ".y"
            z_coord_0 = get_casted_var_or_constant(node, node.inputs[0], DataTypes.VEC3) + ".z"
            x_coord_1 = get_casted_var_or_constant(node, node.inputs[1], DataTypes.VEC3) + ".x"
            y_coord_1 = get_casted_var_or_constant(node, node.inputs[1], DataTypes.VEC3) + ".y"
            z_coord_1 = get_casted_var_or_constant(node, node.inputs[1], DataTypes.VEC3) + ".z"
            x_coord_2 = get_casted_var_or_constant(node, node.inputs[2], DataTypes.VEC3) + ".x"
            y_coord_2 = get_casted_var_or_constant(node, node.inputs[2], DataTypes.VEC3) + ".y"
            z_coord_2 = get_casted_var_or_constant(node, node.inputs[2], DataTypes.VEC3) + ".z"
            tmp_var_name_x = create_var(node, None, DataTypes.FLOAT)
            tmp_var_name_y = create_var(node, None, DataTypes.FLOAT)
            tmp_var_name_z = create_var(node, None, DataTypes.FLOAT)
            line = (
                "float "
                + tmp_var_name_x
                + " = "
                + line_two_in(node, "-", -1, -1, x_coord_1, x_coord_2, is_inline=True)
                + ";\n\t"
            )
            line += (
                "float "
                + tmp_var_name_y
                + " = "
                + line_two_in(node, "-", -1, -1, y_coord_1, y_coord_2, is_inline=True)
                + ";\n\t"
            )
            line += (
                "float "
                + tmp_var_name_z
                + " = "
                + line_two_in(node, "-", -1, -1, z_coord_1, z_coord_2, is_inline=True)
                + ";\n\t"
            )

            def wrap1(tmp_var_name: str, coord_0: str, coord_2: str) -> str:
                cond = line_two_in(node, "!=", -1, -1, tmp_var_name, "0.0", is_inline=True)
                expr1 = line_two_in(
                    node,
                    "-",
                    -1,
                    -1,
                    coord_0,
                    line_two_in(
                        node,
                        "*",
                        -1,
                        -1,
                        tmp_var_name,
                        one_param_fn(
                            node,
                            "floor",
                            -1,
                            line_two_in(
                                node,
                                "/",
                                -1,
                                -1,
                                line_two_in(node, "-", -1, -1, coord_0, coord_2, is_inline=True),
                                tmp_var_name,
                                is_inline=True,
                            ),
                            is_inline=True,
                        ),
                        is_inline=True,
                    ),
                    is_inline=True,
                )
                return ternary(node, -1, -1, -1, cond, expr1, coord_2, is_inline=True)

            line += three_param_fn(
                node,
                "vec3",
                -1,
                -1,
                -1,
                wrap1(tmp_var_name_x, x_coord_0, x_coord_2),
                wrap1(tmp_var_name_y, y_coord_0, y_coord_2),
                wrap1(tmp_var_name_z, z_coord_0, z_coord_2),
            )
        case "SNAP":
            x_coord_0 = get_casted_var_or_constant(node, node.inputs[0], DataTypes.VEC3) + ".x"
            y_coord_0 = get_casted_var_or_constant(node, node.inputs[0], DataTypes.VEC3) + ".y"
            z_coord_0 = get_casted_var_or_constant(node, node.inputs[0], DataTypes.VEC3) + ".z"
            x_coord_1 = get_casted_var_or_constant(node, node.inputs[1], DataTypes.VEC3) + ".x"
            y_coord_1 = get_casted_var_or_constant(node, node.inputs[1], DataTypes.VEC3) + ".y"
            z_coord_1 = get_casted_var_or_constant(node, node.inputs[1], DataTypes.VEC3) + ".z"

            def wrap2(coord_0: str, coord_1: str) -> str:
                return line_two_in(
                    node,
                    "*",
                    -1,
                    -1,
                    one_param_fn(
                        node,
                        "floor",
                        -1,
                        ternary(
                            node,
                            -1,
                            -1,
                            -1,
                            line_two_in(node, "!=", -1, -1, coord_1, "0.0", is_inline=True),
                            line_two_in(node, "/", -1, -1, coord_0, coord_1, is_inline=True),
                            "0.0",
                            is_inline=True,
                        ),
                        True,
                    ),
                    coord_1,
                    is_inline=True,
                )

            line = three_param_fn(
                node,
                "vec3",
                -1,
                -1,
                -1,
                wrap2(x_coord_0, x_coord_1),
                wrap2(y_coord_0, y_coord_1),
                wrap2(z_coord_0, z_coord_1),
            )
        case "SINE":
            line = one_param_fn(node, "sin")
        case "COSINE":
            line = one_param_fn(node, "cos")
        case "TANGENT":
            line = one_param_fn(node, "tan")
    add_line(line + (";" if add_semicolon else ""), is_constant)


def init_mapping(node: bpy.types.Node) -> None:
    if cast(bpy.types.ShaderNodeMapping, node).vector_type != "POINT":
        raise Exception("Only POINT type is supported on Mapping Node")

    var_name = create_var(node, node.outputs[0], DataTypes.VEC3)

    reset_is_constant()

    vec = get_casted_var_or_constant(node, cast(bpy.types.NodeSocket, node.inputs.get("Vector")), DataTypes.VEC3)
    expr = "vec3 " + var_name + " = " + vec

    scale = cast(bpy.types.NodeSocket, node.inputs.get("Scale"))
    if socket_is_one(scale):
        expr += ";"
    else:
        expr += (
            " * " + get_casted_var_or_constant(node, scale, DataTypes.VEC3) + ";"
        )  # vector-vector multiplication is component wise

    rot = cast(bpy.types.NodeSocketVector, node.inputs.get("Rotation"))
    loc = cast(bpy.types.NodeSocket, node.inputs.get("Location"))

    add_line(expr, is_constant and socket_is_zero(rot) and socket_is_zero(loc))

    if not socket_is_zero(rot):
        rot_var = ""
        if rot.is_linked:
            rot_var = get_var_name(node, rot)
        else:
            reset_is_constant()
            rot_var = create_var(
                node, rot, DataTypes.VEC3
            )  # it is fine to use an input here because we won't have to access that variable outside of here
            add_line(
                "vec3 " + rot_var + " = " + get_casted_var_or_constant(node, rot, DataTypes.VEC3) + ";",
                is_constant,
            )
        if rot.is_linked or cast(list[float], rot.default_value)[0] != 0.0:
            cx = create_var(node, None, DataTypes.VEC3)
            add_line("vec3 " + cx + " = cos(" + rot_var + ".x);", False)
            sx = create_var(node, None, DataTypes.VEC3)
            add_line("vec3 " + sx + " = sin(" + rot_var + ".x);", False)
            add_line(
                var_name + ".y = " + var_name + ".y * " + cx + " - " + var_name + ".z * " + sx + ";",
                False,
            )
            add_line(
                var_name + ".z = " + var_name + ".y * " + sx + " + " + var_name + ".z * " + cx + ";",
                False,
            )

        if rot.is_linked or cast(list[float], rot.default_value)[1] != 0.0:
            cy = create_var(node, None, DataTypes.VEC3)
            add_line("vec3 " + cy + " = cos(" + rot_var + ".y);", False)
            sy = create_var(node, None, DataTypes.VEC3)
            add_line("vec3 " + sy + " = sin(" + rot_var + ".y);", False)
            add_line(
                var_name + ".x = " + var_name + ".x * " + cy + " + " + var_name + ".z * " + sy + ";",
                False,
            )
            add_line(
                var_name + ".z = -" + var_name + ".x * " + sy + " + " + var_name + ".z * " + cy + ";",
                False,
            )

        if rot.is_linked or cast(list[float], rot.default_value)[2] != 0.0:
            cz = create_var(node, None, DataTypes.VEC3)
            add_line("vec3 " + cz + " = cos(" + rot_var + ".z);", False)
            sz = create_var(node, None, DataTypes.VEC3)
            add_line("vec3 " + sz + " = sin(" + rot_var + ".z);", False)
            add_line(
                var_name + ".x = " + var_name + ".x * " + cz + " - " + var_name + ".y * " + sz + ";",
                False,
            )
            add_line(
                var_name + ".y = " + var_name + ".x * " + sz + " + " + var_name + ".y * " + cz + ";",
                False,
            )

    if not socket_is_zero(loc):
        add_line(
            var_name + " = " + var_name + " + " + get_casted_var_or_constant(node, loc, DataTypes.VEC3) + ";",
            False,
        )


def init_combine_color(node: bpy.types.Node) -> None:
    reset_is_constant()
    r = get_casted_var_or_constant(node, node.inputs[0], DataTypes.FLOAT)
    g = get_casted_var_or_constant(node, node.inputs[1], DataTypes.FLOAT)
    b = get_casted_var_or_constant(node, node.inputs[2], DataTypes.FLOAT)
    color = create_var(node, node.outputs[0], DataTypes.VEC3)
    add_line("vec3 " + color + " = vec3(" + r + ", " + g + ", " + b + ");", is_constant)


def init_combine_xyz(node: bpy.types.Node) -> None:
    reset_is_constant()
    x = get_casted_var_or_constant(node, node.inputs[0], DataTypes.FLOAT)
    y = get_casted_var_or_constant(node, node.inputs[1], DataTypes.FLOAT)
    z = get_casted_var_or_constant(node, node.inputs[2], DataTypes.FLOAT)
    vector = create_var(node, node.outputs[0], DataTypes.VEC3)
    add_line("vec3 " + vector + " = vec3(" + x + ", " + y + ", " + z + ");", is_constant)


def init_separate_color(node: bpy.types.Node) -> None:
    vec = get_casted_var_or_constant(node, node.inputs[0], DataTypes.VEC3)
    if node.outputs[0].is_linked:
        varx = create_var(node, node.outputs[0], DataTypes.FLOAT)
        add_line("float " + varx + " = " + vec + ".r;", False)
    if node.outputs[1].is_linked:
        vary = create_var(node, node.outputs[1], DataTypes.FLOAT)
        add_line("float " + vary + " = " + vec + ".g;", False)
    if node.outputs[2].is_linked:
        varz = create_var(node, node.outputs[2], DataTypes.FLOAT)
        add_line("float " + varz + " = " + vec + ".b;", False)


def init_separate_xyz(node: bpy.types.Node) -> None:
    vec = get_casted_var_or_constant(node, node.inputs[0], DataTypes.VEC3)
    if node.outputs[0].is_linked:
        varx = create_var(node, node.outputs[0], DataTypes.FLOAT)
        add_line("float " + varx + " = " + vec + ".x;", False)
    if node.outputs[1].is_linked:
        vary = create_var(node, node.outputs[1], DataTypes.FLOAT)
        add_line("float " + vary + " = " + vec + ".y;", False)
    if node.outputs[2].is_linked:
        varz = create_var(node, node.outputs[2], DataTypes.FLOAT)
        add_line("float " + varz + " = " + vec + ".z;", False)


def init_tex_image(node: bpy.types.Node, uv_index: int, type: str) -> None:
    img = cast(bpy.types.ShaderNodeTexImage, node).image
    if img is None:
        raise Exception("No Image set in Texture Image Shader node " + node.name)
    if img.source != "FILE":
        raise Exception("Images have to be external files when used in Texture Image Shader node " + node.name)
    sampler = create_var(node, None, DataTypes.SAMPLER2D)
    abs_filepath = os.path.normcase(bpy.path.abspath(img.filepath))
    log("Reading TextureImage Node with filepath " + abs_filepath)
    # in general, these are the hints available: # https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/shading_language.html#uniform-hints
    if type == "BaseColor":
        # samplers using sRGB color data needs source_color hint: https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/shading_language.html#using-source-color
        set_var_as_uniform(sampler, DataTypes.SAMPLER2D.value, abs_filepath, ": source_color")
    elif type == "Roughness":
        set_var_as_uniform(sampler, DataTypes.SAMPLER2D.value, abs_filepath, ": hint_roughness_g")
    elif type == "Normal":
        set_var_as_uniform(sampler, DataTypes.SAMPLER2D.value, abs_filepath, ": hint_normal")
    else:
        set_var_as_uniform(sampler, DataTypes.SAMPLER2D.value, abs_filepath, "")
    vec = None
    if node.inputs[0].is_linked:
        vec = get_casted_var_or_constant(node, node.inputs[0], DataTypes.VEC2)
        # check whether this value comes from UV. If yes, we have to invert because
        # all values coming from UV are flipped, so we have to flip back now
        node_link = cast(bpy.types.NodeLinks, node.inputs[0].links)[0]
        res = get_prop_from_any_child_of_var(
            cast(bpy.types.Node, node_link.from_node), cast(bpy.types.NodeSocket, node_link.from_socket), "is_uv_value"
        )
        if res[1] and res[0]:
            vec = "vec2(" + vec + ".x, 1.0 - " + vec + ".y)"
    else:
        if "uv" in special_vars and uv_index in special_vars["uv"]:
            vec = special_vars["uv"][uv_index]
        else:
            vec = create_var(node, None, DataTypes.VEC2)
            # do not flip UV because we exclusively will use this value for an image
            add_uv_line(vec, uv_index, False)
    if node.outputs[0].is_linked:
        color = create_var(node, node.outputs[0], DataTypes.VEC3)
        add_line("vec3 " + color + " = texture(" + sampler + ", " + vec + ").rgb;", False)
        add_prop_to_var(node, node.outputs[0], "is_texture", True)
    if node.outputs[1].is_linked:
        alpha = create_var(node, node.outputs[1], DataTypes.FLOAT)
        add_line("float " + alpha + " = texture(" + sampler + ", " + vec + ").a;", False)


def init_normal_map(node: bpy.types.Node) -> None:
    if cast(bpy.types.ShaderNodeNormalMap, node).space != "TANGENT":
        raise Exception("Only Tangent space is supported for Normal Maps, check node " + node.name)
    strength = get_casted_var_or_constant(node, node.inputs[0], DataTypes.FLOAT)
    color = get_casted_var_or_constant(node, node.inputs[1], DataTypes.VEC3)
    if cast(bpy.types.ShaderNodeNormalMap, node).uv_map != "":
        raise Exception("Setting uv_map on Normal Map nodes is not supported: " + node.name)
    if float(strength) != 1.0:
        add_line("NORMAL_MAP_DEPTH = " + strength + ";", False)
    # pass the color variable along, no need to create a new one
    set_var(node, node.outputs[0], DataTypes.VEC3, color)


def init_uv_map(node: bpy.types.Node, uv_index: int) -> None:
    if cast(bpy.types.ShaderNodeUVMap, node).from_instancer:
        raise Exception("Using 'from_instancer' on a UV Map node is not supported: " + node.name)
    uv_map_name = cast(bpy.types.ShaderNodeUVMap, node).uv_map
    if uv_map_name != "":
        c = 0
        for layer in cast(bpy.types.Mesh, obj.data).uv_layers:
            if layer.name == uv_map_name:
                break
            c += 1
        uv_index = c
    if "uv_flipped" in special_vars and uv_index in special_vars["uv_flipped"]:
        uv_var = special_vars["uv_flipped"][uv_index]
        set_var(node, node.outputs[0], DataTypes.VEC2, uv_var)
    else:
        uv = create_var(node, node.outputs[0], DataTypes.VEC2)
        add_uv_line(uv, uv_index, True)
    add_prop_to_var(node, node.outputs[0], "is_uv_value", True)


def init_bsdf_principled(node: bpy.types.Node) -> None:
    base_color = cast(bpy.types.NodeSocket, node.inputs.get("Base Color"))
    metallic = cast(bpy.types.NodeSocket, node.inputs.get("Metallic"))
    roughness = cast(bpy.types.NodeSocket, node.inputs.get("Roughness"))
    alpha = cast(bpy.types.NodeSocket, node.inputs.get("Alpha"))
    normal = cast(bpy.types.NodeSocket, node.inputs.get("Normal"))
    emission_color = cast(bpy.types.NodeSocket, node.inputs.get("Emission Color"))
    emission_strength = cast(bpy.types.NodeSocket, node.inputs.get("Emission Strength"))
    # rest is ignored
    dict = {
        "ALBEDO": "vec3",
        "METALLIC": "float",
        "ROUGHNESS": "float",
        "ALPHA": "float",
        "NORMAL": "vec3",
        "EMISSION": "vec3",
    }
    if "BSDF" not in added_structs:
        add_struct("BSDF", dict)
    var_bsdf = create_var(node, node.outputs[0], DataTypes.BSDF)
    has_alpha = get_casted_var_or_constant(node, alpha, DataTypes.FLOAT) != "1.0"
    has_normal = normal.is_linked
    add_prop_to_var(node, node.outputs[0], "has_alpha", has_alpha)
    add_prop_to_var(node, node.outputs[0], "has_normal", has_normal)
    has_normal_map = False
    if normal.is_linked:
        link = cast(bpy.types.NodeLinks, normal.links)[0]
        res = get_prop_from_any_child_of_var(
            cast(bpy.types.Node, link.from_node), cast(bpy.types.NodeSocket, link.from_socket), "is_texture"
        )
        if res[1] and res[0]:
            has_normal_map = True
    add_prop_to_var(node, node.outputs[0], "has_normal_map", has_normal_map)
    reset_is_constant()
    line = (
        "BSDF "
        + var_bsdf
        + " = "
        + "BSDF("
        + get_casted_var_or_constant(node, base_color, DataTypes.VEC3)
        + ", "
        + get_casted_var_or_constant(node, metallic, DataTypes.FLOAT)
        + ", "
        + get_casted_var_or_constant(node, roughness, DataTypes.FLOAT)
        + ", "
        + get_casted_var_or_constant(node, alpha, DataTypes.FLOAT)
        + ", "
        + get_casted_var_or_constant(node, normal, DataTypes.VEC3)
        + ", "
        + get_casted_var_or_constant(node, emission_color, DataTypes.VEC3)
        + " * "
        + get_casted_var_or_constant(node, emission_strength, DataTypes.FLOAT)
        + ");"
    )
    add_line(line, is_constant)


def init_output_material(node: bpy.types.Node) -> None:
    if not cast(bpy.types.ShaderNodeOutputMaterial, node).is_active_output:
        return
    # make sure it is connected to a principled bsdf node
    surface = cast(bpy.types.NodeSocket, node.inputs.get("Surface"))
    if not surface.is_linked:
        raise Exception("Surface of Material Output is not linked to anything")

    connected_to = cast(bpy.types.Node, cast(bpy.types.NodeLinks, surface.links)[0].from_node)
    if connected_to.bl_idname != "ShaderNodeBsdfPrincipled":
        raise Exception("Material Output Surface must be connected to Principled BSDF node")

    bsdf = get_var_name(node, surface)
    add_line("ALBEDO = " + bsdf + ".ALBEDO;", False)
    add_line("METALLIC = " + bsdf + ".METALLIC;", False)
    add_line("ROUGHNESS = " + bsdf + ".ROUGHNESS;", False)
    has_alpha = get_prop_from_var(connected_to, connected_to.outputs[0], "has_alpha")
    if has_alpha:
        add_line("ALPHA = " + bsdf + ".ALPHA;", False)
    has_normal = get_prop_from_var(connected_to, connected_to.outputs[0], "has_normal")
    has_normal_map = get_prop_from_var(connected_to, connected_to.outputs[0], "has_normal_map")
    if has_normal:
        tab = ""
        if limit_normal_effect is not None:
            tab = "\t"
            # grab correct UV variable or create
            uv_var = None
            uv_ind = cast(int, cast(bpy.types.Mesh, obj.data).uv_layers.active_index)
            if is_right_after_bake:
                # we just baked the textures, so we should also take the UVs that we baked them with
                uv_ind = uv_normal_idx
            if "uv_flipped" in special_vars and uv_ind in special_vars["uv_flipped"]:
                uv_var = special_vars["uv_flipped"][uv_ind]
            else:
                uv_var = create_var(node, None, DataTypes.VEC2)
                add_uv_line(uv_var, cast(int, uv_ind), True)
                # no need to add prop for is_uv_value here like everywhere else since we only
                # use this value here and output material node has no outputs anyway
            # add normal limiting code
            add_line(
                "if ("
                + uv_var
                + ".x >= "
                + str(limit_normal_effect["min_x"])
                + " && "
                + uv_var
                + ".x <= "
                + str(limit_normal_effect["max_x"])
                + " && "
                + uv_var
                + ".y >= "
                + str(limit_normal_effect["min_y"])
                + " && "
                + uv_var
                + ".y <= "
                + str(limit_normal_effect["max_y"])
                + ") {",
                False,
            )
        if has_normal_map:
            add_line(tab + "NORMAL_MAP = " + bsdf + ".NORMAL;", False)
        else:
            add_line(tab + "NORMAL = " + bsdf + ".NORMAL;", False)
        if limit_normal_effect is not None:
            add_line("}", False)
    add_line("EMISSION = " + bsdf + ".EMISSION;", False)


def init_value(node: bpy.types.Node) -> None:
    add_line(
        "float "
        + create_var(node, node.outputs[0], DataTypes.FLOAT)
        + " = "
        + get_constant(node, node.outputs[0])
        + ";",
        True,
    )


def init_mix(node: bpy.types.Node) -> None:
    match cast(bpy.types.ShaderNodeMix, node).data_type:
        case "FLOAT":
            reset_is_constant()
            mix_var = create_var(node, node.outputs.get("Result"), DataTypes.FLOAT)
            a = get_casted_var_or_constant(node, cast(bpy.types.NodeSocket, node.inputs.get("A")), DataTypes.FLOAT)
            b = get_casted_var_or_constant(node, cast(bpy.types.NodeSocket, node.inputs.get("B")), DataTypes.FLOAT)
            fac = get_casted_var_or_constant(
                node, cast(bpy.types.NodeSocket, node.inputs.get("Factor")), DataTypes.FLOAT
            )
            if cast(bpy.types.ShaderNodeMix, node).clamp_factor:
                fac = "clamp(" + fac + ", 0.0, 1.0)"
            add_line(
                "float " + mix_var + " = mix(" + a + ", " + b + ", " + fac + ");",
                is_constant,
            )
        case "VECTOR":
            reset_is_constant()
            mix_var = create_var(node, node.outputs.get("Result"), DataTypes.VEC3)
            a = get_casted_var_or_constant(node, cast(bpy.types.NodeSocket, node.inputs.get("A")), DataTypes.VEC3)
            b = get_casted_var_or_constant(node, cast(bpy.types.NodeSocket, node.inputs.get("B")), DataTypes.VEC3)
            fac = ""
            if cast(bpy.types.ShaderNodeMix, node).factor_mode == "UNIFORM":
                fac = get_casted_var_or_constant(
                    node, cast(bpy.types.NodeSocket, node.inputs.get("Factor")), DataTypes.FLOAT
                )
            elif cast(bpy.types.ShaderNodeMix, node).factor_mode == "NON_UNIFORM":
                fac = get_casted_var_or_constant(
                    node, cast(bpy.types.NodeSocket, node.inputs.get("Factor")), DataTypes.VEC3
                )
            if cast(bpy.types.ShaderNodeMix, node).clamp_factor:
                fac = "clamp(" + fac + ", 0.0, 1.0)"
            add_line(
                "vec3 " + mix_var + " = mix(" + a + ", " + b + ", " + fac + ");",
                is_constant,
            )
        case "RGBA":
            reset_is_constant()
            # https://github.com/blender/blender/blob/main/intern/cycles/kernel/osl/shaders/node_color_blend.h
            mix_var = create_var(node, node.outputs.get("Result"), DataTypes.VEC3)
            a = get_casted_var_or_constant(node, cast(bpy.types.NodeSocket, node.inputs.get("A")), DataTypes.VEC3)
            b = get_casted_var_or_constant(node, cast(bpy.types.NodeSocket, node.inputs.get("B")), DataTypes.VEC3)
            fac = get_casted_var_or_constant(
                node, cast(bpy.types.NodeSocket, node.inputs.get("Factor")), DataTypes.FLOAT
            )
            if cast(bpy.types.ShaderNodeMix, node).clamp_factor:
                fac = "clamp(" + fac + ", 0.0, 1.0)"
            line = ""
            match cast(bpy.types.ShaderNodeMix, node).blend_type:
                case "MIX":
                    line = "mix(" + a + ", " + b + ", " + fac + ")"
                case "DARKEN":
                    line = "mix(" + a + ", " + "min(" + a + ", " + b + "), " + fac + ")"
                case "MULTIPLY":
                    line = "mix(" + a + ", " + a + " * " + b + ", " + fac + ")"
                # skip BURN for now
                case "LIGHTEN":
                    line = "mix(" + a + ", " + "max(" + a + ", " + b + "), " + fac + ")"
                case "SCREEN":
                    white = "vec3(1.0)"
                    inv = "vec3(1.0 - " + fac + ")"
                    line = (
                        white
                        + " - ("
                        + inv
                        + " + "
                        + fac
                        + " * ("
                        + white
                        + " - "
                        + b
                        + ")) * ("
                        + white
                        + " - "
                        + a
                        + ")"
                    )
                # skip DODGE for now
                case "ADD":
                    line = "mix(" + a + ", " + a + " + " + b + ", " + fac + ")"
                # skip OVERLAY for now
                # skip SOFT_LIGHT for now
                # skip LINEAR_LIGHT for now
                case "DIFFERENCE":
                    line = "mix(" + a + ", " + "abs(" + a + " - " + b + "), " + fac + ")"
                case "EXCLUSION":
                    line = (
                        "max(mix("
                        + a
                        + ", "
                        + a
                        + " + "
                        + b
                        + " - 2.0 * "
                        + a
                        + " * "
                        + b
                        + ", "
                        + fac
                        + "), "
                        + "0.0)"
                    )
                case "SUBTRACT":
                    line = "mix(" + a + ", " + a + " - " + b + ", " + fac + ")"
                # skip DIVIDE for now
                # skip HUE, SATURATION, COLOR and VALUE for now
                case _:
                    raise UnsupportedSocket(node, cast(bpy.types.ShaderNodeMix, node).blend_type)
            if cast(bpy.types.ShaderNodeMix, node).clamp_result:
                line = "clamp(" + line + ", 0.0, 1.0)"
            add_line("vec3 " + mix_var + " = " + line + ";", is_constant)


def init_rgb(node: bpy.types.Node) -> None:
    add_line(
        "vec3 " + create_var(node, node.outputs[0], DataTypes.VEC3) + " = " + get_constant(node, node.outputs[0]) + ";",
        True,
    )


def init_group(node: bpy.types.Node, type: str | None) -> None:
    group_nodes_stack.append(node)
    group_output = cast(
        bpy.types.Node,
        cast(bpy.types.ShaderNodeTree, cast(bpy.types.ShaderNodeGroup, node).node_tree).nodes.get("Group Output"),
    )
    if group_output.bl_idname != "NodeGroupOutput":
        raise Exception('A node is named "Group Output" but is not actually the group output')
    pre_node_names = ""
    for no in group_nodes_stack:
        pre_node_names += no.name + separator  # choose some separator that is unlikely to be used in node names
    dfs(group_output, pre_node_names, type)
    # -1 because one input is a NodeSocketVirtual input, which is used to create new outputs
    assert len(node.outputs) == len(group_output.inputs) - 1

    for i in range(len(node.outputs)):
        if group_output.inputs[i].is_linked:
            group_inp_var = get_var(group_output, group_output.inputs[i])
            set_var(node, node.outputs[i], group_inp_var["type"], group_inp_var["name"])
        else:
            dtype = input_to_data_type(node.outputs[i])
            var = create_var(node, node.outputs[i], dtype)
            add_line(
                dtype.value + " " + var + " = " + get_constant(group_output, group_output.inputs[i]) + ";",
                True,
            )


def init_group_input(node: bpy.types.Node) -> None:
    group_node = group_nodes_stack[len(group_nodes_stack) - 1]
    # -1 because one input is a NodeSocketVirtual input, which is used to create new outputs
    assert len(node.outputs) - 1 == len(group_node.inputs)
    for i in range(len(group_node.inputs)):
        if group_node.inputs[i].is_linked:
            group_inp_var = get_var(group_node, group_node.inputs[i])
            set_var(node, node.outputs[i], group_inp_var["type"], group_inp_var["name"])
        else:
            type = input_to_data_type(node.outputs[i])
            var = create_var(node, node.outputs[i], type)
            add_line(
                type.value + " " + var + " = " + get_constant(group_node, group_node.inputs[i]) + ";",
                True,
            )


def init_group_output(_node: bpy.types.Node) -> None:
    group_nodes_stack.pop()


class SupportedNodes(TypedDict):
    ShaderNodeTexCoord: Callable[[bpy.types.Node, int], None]
    ShaderNodeMath: Callable[[bpy.types.Node], None]

    ShaderNodeVectorMath: Callable[[bpy.types.Node], None]
    ShaderNodeMapping: Callable[[bpy.types.Node], None]
    ShaderNodeCombineColor: Callable[[bpy.types.Node], None]
    ShaderNodeCombineXYZ: Callable[[bpy.types.Node], None]
    ShaderNodeSeparateColor: Callable[[bpy.types.Node], None]
    ShaderNodeSeparateXYZ: Callable[[bpy.types.Node], None]
    ShaderNodeBsdfPrincipled: Callable[[bpy.types.Node], None]
    ShaderNodeOutputMaterial: Callable[[bpy.types.Node], None]
    ShaderNodeValue: Callable[[bpy.types.Node], None]
    ShaderNodeMix: Callable[[bpy.types.Node], None]
    ShaderNodeRGB: Callable[[bpy.types.Node], None]
    ShaderNodeTexImage: Callable[[bpy.types.Node, int, str], None]
    ShaderNodeNormalMap: Callable[[bpy.types.Node], None]
    ShaderNodeUVMap: Callable[[bpy.types.Node, int], None]
    ShaderNodeGroup: Callable[[bpy.types.Node, str], None]
    NodeGroupInput: Callable[[bpy.types.Node], None]
    NodeGroupOutput: Callable[[bpy.types.Node], None]


supported_nodes: SupportedNodes = {
    "ShaderNodeTexCoord": init_tex_coord,
    "ShaderNodeMath": init_math,
    "ShaderNodeVectorMath": init_vector_math,
    "ShaderNodeMapping": init_mapping,
    "ShaderNodeCombineColor": init_combine_color,
    "ShaderNodeCombineXYZ": init_combine_xyz,
    "ShaderNodeSeparateColor": init_separate_color,
    "ShaderNodeSeparateXYZ": init_separate_xyz,
    "ShaderNodeBsdfPrincipled": init_bsdf_principled,
    "ShaderNodeOutputMaterial": init_output_material,
    "ShaderNodeValue": init_value,
    "ShaderNodeMix": init_mix,
    "ShaderNodeRGB": init_rgb,
    "ShaderNodeTexImage": init_tex_image,
    "ShaderNodeNormalMap": init_normal_map,
    "ShaderNodeUVMap": init_uv_map,
    "ShaderNodeGroup": init_group,
    "NodeGroupInput": init_group_input,
    "NodeGroupOutput": init_group_output,
}

needs_uv = set(("ShaderNodeTexCoord", "ShaderNodeUVMap"))
needs_type = set(["ShaderNodeGroup"])
needs_uv_and_type = set(["ShaderNodeTexImage"])


def initialize_vars(node: bpy.types.Node, type: str | None) -> None:
    if node.bl_idname in supported_nodes:
        if node.bl_idname in needs_uv:
            if is_right_after_bake:
                # we just baked the textures, so we should also take the UVs that we baked them with
                if type == "BaseColor":
                    supported_nodes[node.bl_idname](node, cast(int, uv_base_color_idx))
                elif type == "Metallic" or type == "Roughness":
                    supported_nodes[node.bl_idname](node, cast(int, uv_roughness_metallic_idx))
                elif type == "Normal":
                    supported_nodes[node.bl_idname](node, cast(int, uv_normal_idx))
                else:
                    raise Exception("Unknown UV type encountered: " + str(type))
            else:
                # this is the material how it originally was, we take the UV from the object data
                supported_nodes[node.bl_idname](node, cast(int, cast(bpy.types.Mesh, obj.data).uv_layers.active_index))
        elif node.bl_idname in needs_uv_and_type:
            if is_right_after_bake:
                # we just baked the textures, so we should also take the UVs that we baked them with
                if type == "BaseColor":
                    supported_nodes[node.bl_idname](node, uv_base_color_idx, type)
                elif type == "Metallic" or type == "Roughness":
                    supported_nodes[node.bl_idname](node, uv_roughness_metallic_idx, type)
                elif type == "Normal":
                    supported_nodes[node.bl_idname](node, uv_normal_idx, type)
                else:
                    raise Exception("Unknown UV type encountered: " + str(type))
            else:
                # this is the material how it originally was, we take the UV from the object data
                supported_nodes[node.bl_idname](node, cast(bpy.types.Mesh, obj.data).uv_layers.active_index, type)
        elif node.bl_idname in needs_type:
            supported_nodes[node.bl_idname](node, type)
        else:
            supported_nodes[node.bl_idname](node)
    else:
        raise Exception(node.bl_idname + " not supported yet!")


def dfs(node: bpy.types.Node, path: str, type: str | None) -> None:
    if node.bl_idname not in supported_nodes:
        raise Exception("Node " + node.bl_idname + " is not supported")
    for input in node.inputs:
        if input.is_linked:
            for link in cast(bpy.types.NodeLinks, input.links):
                visited_name = path + separator + cast(bpy.types.Node, link.from_node).name
                if link.is_valid and not link.is_muted and visited_name not in visited:
                    visited.add(visited_name)
                    from_node = cast(bpy.types.Node, link.from_node)
                    if node.bl_idname == "ShaderNodeBsdfPrincipled" and type is None:
                        base_color = node.inputs.get("Base Color")
                        metallic = node.inputs.get("Metallic")
                        roughness = node.inputs.get("Roughness")
                        normal = node.inputs.get("Normal")
                        if input == base_color:
                            dfs(from_node, path, "BaseColor")
                        elif input == metallic:
                            dfs(from_node, path, "Metallic")
                        elif input == roughness:
                            dfs(from_node, path, "Roughness")
                        elif input == normal:
                            dfs(from_node, path, "Normal")
                        else:
                            dfs(from_node, path, type)
                    else:
                        dfs(from_node, path, type)

    initialize_vars(node, type)


def convert_to_godot_shader(
    object: bpy.types.Object,
    material_name: str,
    cull_mode: str,
    limit_normal: SettingsforGodotLimitUVEffectNormal | None,
    right_after_bake: bool,
    uv_base_color: int | None,
    uv_roughness_metallic: int | None,
    uv_normal: int | None,
) -> tuple[str, list[list[str]]]:
    global fragment_code
    global structs_code
    global vertex_code
    global globals_code
    global added_structs
    global nodes_to_vars
    global special_var_props
    global next_num
    global is_constant
    global group_nodes_stack
    global visited
    global uniform_vars
    global limit_normal_effect
    global obj
    global special_vars
    global uv_base_color_idx
    global uv_roughness_metallic_idx
    global uv_normal_idx
    global is_right_after_bake
    global separator
    fragment_code = ""
    structs_code = ""
    vertex_code = ""
    globals_code = ""
    added_structs = set()
    nodes_to_vars = dict()
    special_var_props = dict()
    next_num = 0
    is_constant = True
    group_nodes_stack = []
    visited = set()
    uniform_vars = set()

    limit_normal_effect = limit_normal
    obj = object
    special_vars = {}
    uv_base_color_idx = uv_base_color
    uv_roughness_metallic_idx = uv_roughness_metallic
    uv_normal_idx = uv_normal
    is_right_after_bake = right_after_bake

    mat = bpy.data.materials.get(material_name)
    if not mat or not mat.use_nodes:
        raise Exception("Material does not use nodes")

    mat_output_node = cast(bpy.types.ShaderNode | None, mat.node_tree.nodes.get("Material Output"))
    if not mat_output_node or mat_output_node.bl_idname != "ShaderNodeOutputMaterial":
        raise Exception('A node is named "Material Output" but is not actually the material output')

    uniforms: list[list[str]] = []

    separator = "".join(random.choices(string.punctuation, k=10))

    dfs(mat_output_node, "", None)
    code = "// Generated by Goblend export addon\n\n"
    code += "shader_type spatial;\nrender_mode blend_mix, depth_draw_opaque, "
    if cull_mode == "DISABLED":
        code += "cull_disabled, "
    elif cull_mode == "FRONT":
        code += "cull_front, "
    elif cull_mode == "BACK":
        code += "cull_back, "
    code += "diffuse_lambert, specular_schlick_ggx;\n\n"
    for uniform in uniform_vars:
        code += "uniform " + uniform[1] + " " + uniform[0] + uniform[3] + ";\n"
        uniforms.append([uniform[0], uniform[2]])  # name and linkTo

    code += structs_code + "\n"
    if globals_code:
        code += globals_code
    if vertex_code:
        code += "\nvoid vertex() {\n" + vertex_code + "}\n\n"
    code += "void fragment() {\n" + fragment_code + "}\n"
    return code, uniforms
