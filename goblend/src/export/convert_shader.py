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
from ..log import log

# converts a blender shader to a godot shader

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

special_vars = {}

limit_normal_effect = None
obj = None

uv_base_color_idx = 0
uv_roughness_metallic_idx = 0
uv_normal_idx = 0
is_right_after_bake = False

separator = ""


def add_line(str, const, top=False):
    global fragment_code
    if const:
        if top:
            fragment_code = "\tconst " + str + "\n" + fragment_code
        else:
            fragment_code += "\tconst " + str + "\n"
    else:
        if top:
            fragment_code = "\t" + str + "\n" + fragment_code
        else:
            fragment_code += "\t" + str + "\n"


# only call this after checking that the corresponding entry in special_vars does not exist yet
def add_uv_line(name, uv_index, flipped):
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
        if not "uv_flipped" in special_vars:
            special_vars["uv_flipped"] = {}
        special_vars["uv_flipped"][uv_index] = name
    else:
        if not "uv" in special_vars:
            special_vars["uv"] = {}
        special_vars["uv"][uv_index] = name


def add_global_line(str):
    global globals_code
    globals_code += str + "\n"


def add_vertex_line(str):
    global vertex_code
    vertex_code += "\t" + str + "\n"


def add_struct(type, vars):
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
    def __init__(self, node, socket_name):
        super().__init__("Connecting " + socket_name + " on " + node.bl_idname + " is not supported")


class DataTypes(Enum):
    FLOAT = "float"
    INT = "int"
    VEC2 = "vec2"
    VEC3 = "vec3"
    VEC4 = "vec4"
    BSDF = "BSDF"
    SAMPLER2D = "sampler2D"


def input_to_data_type(input):
    match input.type:
        case "INT":  # assuming "value" is "float"
            return DataTypes.INT
        case "VALUE":
            return DataTypes.FLOAT
        case "BOOLEAN":
            return DataTypes.INT
        case "VECTOR":
            match len(input.default_value):
                case 2:
                    return DataTypes.VEC2
                case 3:
                    return DataTypes.VEC3
                case 4:
                    return DataTypes.VEC4
        case "RGBA":
            return DataTypes.VEC3
        case _:
            raise Exception("Unsupported type: " + type)


# pass None as output to indicate a helper variable
def create_var(node, output, type):
    global next_num
    name = "v" + str(next_num)
    next_num += 1
    if output == None:
        return name
    if not node in nodes_to_vars:
        nodes_to_vars[node] = dict()

    nodes_to_vars[node][output] = {"name": name, "type": type}
    return name


def add_prop_to_var(node, output, key, val):
    if not node in special_var_props:
        special_var_props[node] = dict()
    if output in special_var_props[node]:
        special_var_props[node][output][key] = val
    else:
        special_var_props[node][output] = dict([(key, val)])


def get_prop_from_var(node, output, key):
    if not node in special_var_props or not output in special_var_props[node]:
        raise Exception("No special properties for node " + node.name)
    return special_var_props[node][output][key]


def get_prop_from_any_child_of_var(node, output, key):
    if not node in special_var_props or not output in special_var_props[node]:
        for inp in node.inputs:
            if inp.is_linked:
                socket = inp.links[0].from_socket
                parent = inp.links[0].from_node
                res = get_prop_from_any_child_of_var(parent, socket, key)
                if res[1]:
                    return res
        return (None, False)
    return (special_var_props[node][output][key], True)


def set_var(node, output, type, name):
    if not node in nodes_to_vars:
        nodes_to_vars[node] = dict()

    nodes_to_vars[node][output] = {"name": name, "type": type}


def set_var_as_uniform(
    name, type, linkTo, uniform_hint
):  # linkTo can for example be the name of the image for samplers
    uniform_vars.add((name, type, linkTo, uniform_hint))


def get_var(node, input):
    # find the output that connects to this input
    link = input.links[0]
    output = link.from_socket
    output_node = link.from_node
    if not output_node in nodes_to_vars or not output in nodes_to_vars[output_node]:
        log(output_node)
        log(nodes_to_vars[output_node])
        raise Exception("Variable that is needed for node " + node.name + ", input " + input.name + " does not exist")
    return nodes_to_vars[output_node][output]


def get_var_name(node, input):
    return get_var(node, input)["name"]


def get_var_data_type(node, input):
    return get_var(node, input)["type"]


def beautify_float(f):
    as_str = "%.6f" % f
    as_str = as_str.rstrip("0")
    if as_str.endswith("."):
        as_str = as_str + "0"
    return as_str


def get_constant(node, input):
    match input.type:
        case "INT":  # assuming "value" is "float"
            return str(input.default_value)
        case "VALUE":
            return beautify_float(input.default_value)
        case "BOOLEAN":
            return "true" if input.default_value else "false"
        case "VECTOR":
            match len(input.default_value):
                case 2:
                    return (
                        "vec2("
                        + beautify_float(input.default_value[0])
                        + ", "
                        + beautify_float(input.default_value[1])
                        + ")"
                    )
                case 3:
                    return (
                        "vec3("
                        + beautify_float(input.default_value[0])
                        + ", "
                        + beautify_float(input.default_value[1])
                        + ", "
                        + beautify_float(input.default_value[2])
                        + ")"
                    )
                case 4:
                    return (
                        "vec4("
                        + beautify_float(input.default_value[0])
                        + ", "
                        + beautify_float(input.default_value[1])
                        + ", "
                        + beautify_float(input.default_value[2])
                        + ", "
                        + beautify_float(input.default_value[3])
                        + ")"
                    )
        case "RGBA":
            return (
                "vec3("
                + beautify_float(input.default_value[0])
                + ", "
                + beautify_float(input.default_value[1])
                + ", "
                + beautify_float(input.default_value[2])
                + ")"
            )
        case _:
            raise Exception("Unsupported constant value at " + node.name + " with socket " + input.name)


def get_data_type(node, input):
    match input.type:
        case "VALUE":
            return DataTypes.FLOAT
        case "INT":
            return DataTypes.INT
        case "VECTOR":
            match len(input.default_value):
                case 2:
                    return DataTypes.VEC2
                case 3:
                    return DataTypes.VEC3
                case 4:
                    return DataTypes.VEC4
        case "RGBA":
            return DataTypes.VEC3
        case _:
            raise Exception("Unsupported constant value at " + node.name + " with socket " + input.name)


def reset_is_constant():
    global is_constant
    is_constant = True


def get_casted_var_or_constant(node, input, needed_data_type):
    if input.is_linked:
        global is_constant
        is_constant = False
        var = get_var(node, input)
        return cast(var["type"], needed_data_type, var["name"])
    return cast(get_data_type(node, input), needed_data_type, get_constant(node, input))


def cast(actual, needed, str):
    match actual:
        case DataTypes.FLOAT:
            match needed:
                case DataTypes.FLOAT:
                    return str
                case DataTypes.INT:
                    return "int(" + str + ")"
                case DataTypes.VEC2:
                    return "vec2(" + str + ")"
                case DataTypes.VEC3:
                    return "vec3(" + str + ")"
                case DataTypes.VEC4:
                    return "vec4(" + str + ")"
        case DataTypes.INT:
            match needed:
                case DataTypes.FLOAT:
                    return "float(" + str + ")"
                case DataTypes.INT:
                    return str
                case DataTypes.VEC2:
                    return "vec2(" + str + ")"
                case DataTypes.VEC3:
                    return "vec3(" + str + ")"
                case DataTypes.VEC4:
                    return "vec4(" + str + ")"
        case DataTypes.VEC2:
            match needed:
                case DataTypes.FLOAT:
                    return "(" + str + ".x + " + str + ".y) / 2.0"
                case DataTypes.VEC2:
                    return str
                case DataTypes.VEC3:
                    return "vec3(" + str + ", 0)"
                case DataTypes.VEC4:
                    return "vec4(" + str + ", 0, 0)"
        case DataTypes.VEC3:
            match needed:
                case DataTypes.FLOAT:
                    return "(" + str + ".x + " + str + ".y + " + str + ".z) / 3.0"
                case DataTypes.VEC2:
                    return "(" + str + ".xy)"
                case DataTypes.VEC3:
                    return str
                case DataTypes.VEC4:
                    return "vec4(" + str + ", 0)"
        case DataTypes.VEC4:
            match needed:
                case DataTypes.FLOAT:
                    return "(" + str + ".x + " + str + ".y + " + str + ".z + " + str + ".w) / 4.0"
                case DataTypes.VEC2:
                    return "(" + str + ".xy)"
                case DataTypes.VEC3:
                    return "(" + str + ".xyz)"
                case DataTypes.VEC4:
                    return str
    raise Exception("Unsupported cast: Cannot cast from " + actual.name + " to " + needed.name)


def socket_is_zero(input):
    if input.is_linked:
        return False  # if socket is connected assume for simplicity that it's not 0
    match input.type:
        case "INT":
            return input.default_value == 0
        case "VALUE":
            return input.default_value == 0.0
        case "BOOLEAN":
            return input.default_value == False
        case "VECTOR":
            match len(input.default_value):
                case 2:
                    return input.default_value[0] == 0.0 and input.default_value[1] == 0.0
                case 3:
                    return (
                        input.default_value[0] == 0.0
                        and input.default_value[1] == 0.0
                        and input.default_value[2] == 0.0
                    )
                case 4:
                    return (
                        input.default_value[0] == 0.0
                        and input.default_value[1] == 0.0
                        and input.default_value[2] == 0.0
                        and input.default_value[3] == 0.0
                    )
                case _:
                    return False
        case _:
            return False


def socket_is_one(input):
    if input.is_linked:
        return False  # if socket is connected assume for simplicity that it's not 0
    match input.type:
        case "INT":
            return input.default_value == 1
        case "VALUE":
            return input.default_value == 1.0
        case "BOOLEAN":
            return input.default_value == True
        case "VECTOR":
            match len(input.default_value):
                case 2:
                    return input.default_value[0] == 1.0 and input.default_value[1] == 1.0
                case 3:
                    return (
                        input.default_value[0] == 1.0
                        and input.default_value[1] == 1.0
                        and input.default_value[2] == 1.0
                    )
                case 4:
                    return (
                        input.default_value[0] == 1.0
                        and input.default_value[1] == 1.0
                        and input.default_value[2] == 1.0
                        and input.default_value[3] == 1.0
                    )
                case _:
                    return False
        case _:
            return False


def init_tex_coord(node, uv_index):
    if node.from_instancer:
        raise Exception('Setting "From Instancer" on Texture Coordinate Node is not supported')
    if node.object != None:
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
                    if not "vertex_local" in special_vars:
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


def init_math(node):
    line = ""
    var_name = create_var(node, node.outputs[0], DataTypes.FLOAT)  # math nodes only have one output
    use_clamp = node.use_clamp

    reset_is_constant()

    def line_two_in(node, op, ind1=0, ind2=1, str1=None, str2=None, is_inline=False):
        expr = (
            (
                ("(" + str1 + ")")
                if str1 != None
                else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.FLOAT)
            )
            + " "
            + op
            + " "
            + (
                ("(" + str2 + ")")
                if str2 != None
                else get_casted_var_or_constant(node, node.inputs[ind2], DataTypes.FLOAT)
            )
        )
        if is_inline:
            return expr
        if use_clamp:
            expr = "clamp(" + expr + ", 0.0, 1.0)"
        return "float " + var_name + " = " + expr

    def one_param_fn(node, fn, ind1=0, str1=None, is_inline=False):
        expr = (
            fn
            + "("
            + (str1 if str1 != None else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.FLOAT))
            + ")"
        )
        if is_inline:
            return expr
        if use_clamp:
            expr = "clamp(" + expr + ", 0.0, 1.0)"
        return "float " + var_name + " = " + expr

    def two_param_fn(node, fn, ind1=0, ind2=1, str1=None, str2=None, is_inline=False):
        expr = (
            fn
            + "("
            + (str1 if str1 != None else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.FLOAT))
            + ", "
            + (str2 if str2 != None else get_casted_var_or_constant(node, node.inputs[ind2], DataTypes.FLOAT))
            + ")"
        )
        if is_inline:
            return expr
        if use_clamp:
            expr = "clamp(" + expr + ", 0.0, 1.0)"
        return "float " + var_name + " = " + expr

    def three_param_fn(node, fn, ind1=0, ind2=1, ind3=2, str1=None, str2=None, str3=None, is_inline=False):
        expr = (
            fn
            + "("
            + (str1 if str1 != None else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.FLOAT))
            + ", "
            + (str2 if str2 != None else get_casted_var_or_constant(node, node.inputs[ind2], DataTypes.FLOAT))
            + ", "
            + (str3 if str3 != None else get_casted_var_or_constant(node, node.inputs[ind3], DataTypes.FLOAT))
            + ")"
        )
        if is_inline:
            return expr
        if use_clamp:
            expr = "clamp(" + expr + ", 0.0, 1.0)"
        return "float " + var_name + " = " + expr

    def ternary(node, ind1=0, ind2=1, ind3=2, str1=None, str2=None, str3=None, is_inline=False):
        expr = (
            (
                ("(" + str1 + ")")
                if str1 != None
                else get_casted_var_or_constant(node, node.inputs[ind1], DataTypes.FLOAT)
            )
            + " ? "
            + (
                ("(" + str2 + ")")
                if str2 != None
                else get_casted_var_or_constant(node, node.inputs[ind2], DataTypes.FLOAT)
            )
            + " : "
            + (
                ("(" + str3 + ")")
                if str3 != None
                else get_casted_var_or_constant(node, node.inputs[ind3], DataTypes.FLOAT)
            )
        )
        if is_inline:
            return expr
        if use_clamp:
            expr = "clamp(" + expr + ", 0.0, 1.0)"
        return "float " + var_name + " = " + expr

    add_semicolon = True

    match node.operation:
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
                None,
                None,
                one_param_fn(node, "log2", is_inline=True),
                one_param_fn(node, "log2", 1, is_inline=True),
            )
        case "SQRT":
            line = one_param_fn(node, "sqrt")
        case "INVERSE_SQRT":
            line = one_param_fn(node, "inversesqrt")
        case "ABSOLUTE":
            line = one_param_fn(node, "abs")
        case "EXPONENT":
            line = one_param_fn(node, "exp")
        case "MINIMUM":
            line = two_param_fn(node, "min")
        case "MAXIMUM":
            line = two_param_fn(node, "max")
        case "LESS_THAN":
            line = ternary(node, None, None, None, line_two_in(node, "<", is_inline=True), "1.0", "0.0")
        case "GREATER_THAN":
            line = ternary(node, None, None, None, line_two_in(node, ">", is_inline=True), "1.0", "0.0")
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
            if node.operation == "SMOOTH_MAX":
                a_minus_b = "-(" + a_minus_b + ")"
                a_negated = "-(" + a_negated + ")"
                b_negated = "-(" + b_negated + ")"
            line = "float " + var_name + ";\n"
            line += "\tif (" + line_two_in(node, "!=", 2, None, None, "0.0", True) + ") {\n"
            line += (
                "\t\tfloat "
                + tmp_var_name
                + " = "
                + line_two_in(
                    node,
                    "/",
                    None,
                    2,
                    two_param_fn(
                        node,
                        "max",
                        None,
                        None,
                        line_two_in(
                            node,
                            "-",
                            2,
                            None,
                            None,
                            one_param_fn(node, "abs", None, a_minus_b, True),
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
                    None,
                    None,
                    two_param_fn(node, "min", None, None, a_negated, b_negated, True),
                    tmp_var_name
                    + " * "
                    + tmp_var_name
                    + " * "
                    + tmp_var_name
                    + " * "
                    + line_two_in(node, "*", 2, None, None, "(1.0 / 6.0)", True),
                    True,
                )
                + ";\n\t} else {\n\t\t"
                + var_name
                + " = "
                + two_param_fn(node, "min", None, None, a_negated, b_negated, True)
                + ";\n\t}"
            )
        case "COMPARE":
            # blender source code: ((Value1 == Value2) || (abs(Value1 - Value2) <= max(Value3, 1e-5))) ? 1.0 : 0.0;
            line = ternary(
                node,
                None,
                None,
                None,
                line_two_in(
                    node,
                    "||",
                    None,
                    None,
                    "(" + line_two_in(node, "==", is_inline=True) + ")",
                    line_two_in(
                        node,
                        "<=",
                        None,
                        None,
                        one_param_fn(node, "abs", None, line_two_in(node, "-", is_inline=True), True),
                        two_param_fn(node, "max", 2, None, None, "1e-5", True),
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
            line = two_param_fn(node, "trunc(mod") + ")"
        case "FLOORED_MODULO":
            line = two_param_fn(node, "floor(mod") + ")"
        # blender source code:
        # float range = max - min;
        # return (range != 0.0) ? value - (range * floor((value - min) / range)) : min;
        case "WRAP":
            tmp_var_name = create_var(node, None, DataTypes.FLOAT)
            line = "float " + tmp_var_name + " = " + line_two_in(node, "-", 1, 2, is_inline=True) + ";\n\t"
            cond = line_two_in(node, "!=", None, None, tmp_var_name, "0.0", True)
            expr1 = line_two_in(
                node,
                "-",
                0,
                None,
                None,
                line_two_in(
                    node,
                    "*",
                    None,
                    None,
                    tmp_var_name,
                    one_param_fn(
                        node,
                        "floor",
                        None,
                        line_two_in(
                            node, "/", None, None, line_two_in(node, "-", 0, 2, is_inline=True), tmp_var_name, True
                        ),
                        True,
                    ),
                    True,
                ),
                True,
            )
            expr2 = get_casted_var_or_constant(node, node.inputs[2], DataTypes.FLOAT)
            line += ternary(node, None, None, None, cond, expr1, expr2)
        # blender source code: floor(safe_divide(a, b)) * b;
        case "SNAP":
            line = line_two_in(
                node,
                "*",
                None,
                1,
                one_param_fn(
                    node,
                    "floor",
                    None,
                    ternary(
                        node,
                        None,
                        None,
                        None,
                        line_two_in(node, "!=", 1, None, None, "0.0", True),
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
                None,
                None,
                None,
                line_two_in(node, "!=", 1, None, None, "0.0", True),
                one_param_fn(
                    node,
                    "abs",
                    None,
                    line_two_in(
                        node,
                        "-",
                        None,
                        1,
                        line_two_in(
                            node,
                            "*",
                            None,
                            None,
                            one_param_fn(
                                node,
                                "fract",
                                None,
                                line_two_in(
                                    node,
                                    "/",
                                    None,
                                    None,
                                    line_two_in(node, "-", is_inline=True),
                                    line_two_in(node, "*", 1, None, None, "2.0", True),
                                    True,
                                ),
                                True,
                            ),
                            line_two_in(node, "*", 1, None, None, "2.0", True),
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
            line = one_param_fn(node, "asin")
        case "ARCCOSINE":
            line = one_param_fn(node, "acos")
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


def init_mapping(node):
    if node.vector_type != "POINT":
        raise Exception("Only POINT type is support on Mapping Node")

    var_name = create_var(node, node.outputs[0], DataTypes.VEC3)

    reset_is_constant()

    vec = get_casted_var_or_constant(node, node.inputs.get("Vector"), DataTypes.VEC3)
    expr = "vec3 " + var_name + " = " + vec

    scale = node.inputs.get("Scale")
    if socket_is_one(scale):
        expr += ";"
    else:
        expr += (
            " * " + get_casted_var_or_constant(node, scale, DataTypes.VEC3) + ";"
        )  # vector-vector multiplication is component wise

    rot = node.inputs.get("Rotation")
    loc = node.inputs.get("Location")

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
        if rot.is_linked or rot.default_value[0] != 0.0:
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

        if rot.is_linked or rot.default_value[1] != 0.0:
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

        if rot.is_linked or rot.default_value[2] != 0.0:
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


def init_combine_color(node):
    reset_is_constant()
    r = get_casted_var_or_constant(node, node.inputs[0], DataTypes.FLOAT)
    g = get_casted_var_or_constant(node, node.inputs[1], DataTypes.FLOAT)
    b = get_casted_var_or_constant(node, node.inputs[2], DataTypes.FLOAT)
    color = create_var(node, node.outputs[0], DataTypes.VEC3)
    add_line("vec3 " + color + " = vec3(" + r + ", " + g + ", " + b + ");", is_constant)


def init_combine_xyz(node):
    reset_is_constant()
    x = get_casted_var_or_constant(node, node.inputs[0], DataTypes.FLOAT)
    y = get_casted_var_or_constant(node, node.inputs[1], DataTypes.FLOAT)
    z = get_casted_var_or_constant(node, node.inputs[2], DataTypes.FLOAT)
    vector = create_var(node, node.outputs[0], DataTypes.VEC3)
    add_line("vec3 " + vector + " = vec3(" + x + ", " + y + ", " + z + ");", is_constant)


def init_separate_color(node):
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


def init_separate_xyz(node):
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


def init_tex_image(node, uv_index, type):
    if node.image is None:
        raise Exception("No Image set in Texture Image Shader node " + node.name)
    if node.image.source != "FILE":
        raise Exception("Images have to be external files when used in Texture Image Shader node " + node.name)
    sampler = create_var(node, None, DataTypes.SAMPLER2D)
    abs_filepath = os.path.normcase(bpy.path.abspath(node.image.filepath))
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
        res = get_prop_from_any_child_of_var(
            node.inputs[0].links[0].from_node, node.inputs[0].links[0].from_socket, "is_uv_value"
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


def init_normal_map(node):
    if node.space != "TANGENT":
        raise Exception("Only Tangent space is supported for Normal Maps, check node " + node.name)
    strength = get_casted_var_or_constant(node, node.inputs[0], DataTypes.FLOAT)
    color = get_casted_var_or_constant(node, node.inputs[1], DataTypes.VEC3)
    if node.uv_map != "":
        raise Exception("Setting uv_map on Normal Map nodes is not supported: " + node.name)
    if float(strength) != 1.0:
        add_line("NORMAL_MAP_DEPTH = " + strength + ";", False)
    # pass the color variable along, no need to create a new one
    set_var(node, node.outputs[0], DataTypes.VEC3, color)


def init_uv_map(node, uv_index):
    if node.from_instancer:
        raise Exception("Using 'from_instancer' on a UV Map node is not supported: " + node.name)
    uv_map_name = node.uv_map
    if uv_map_name != "":
        c = 0
        for layer in obj.data.uv_layers:
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


def init_bsdf_principled(node):
    base_color = node.inputs.get("Base Color")
    metallic = node.inputs.get("Metallic")
    roughness = node.inputs.get("Roughness")
    alpha = node.inputs.get("Alpha")
    normal = node.inputs.get("Normal")
    emission_color = node.inputs.get("Emission Color")
    emission_strength = node.inputs.get("Emission Strength")
    # rest is ignored
    dict = {
        "ALBEDO": "vec3",
        "METALLIC": "float",
        "ROUGHNESS": "float",
        "ALPHA": "float",
        "NORMAL": "vec3",
        "EMISSION": "vec3",
    }
    if not "BSDF" in added_structs:
        add_struct("BSDF", dict)
    var_bsdf = create_var(node, node.outputs[0], DataTypes.BSDF)
    has_alpha = get_casted_var_or_constant(node, alpha, DataTypes.FLOAT) != "1.0"
    has_normal = normal.is_linked
    add_prop_to_var(node, node.outputs[0], "has_alpha", has_alpha)
    add_prop_to_var(node, node.outputs[0], "has_normal", has_normal)
    has_normal_map = False
    if normal.is_linked:
        res = get_prop_from_any_child_of_var(normal.links[0].from_node, normal.links[0].from_socket, "is_texture")
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


def init_output_material(node):
    if not node.is_active_output:
        return
    # make sure it is connected to a principled bsdf node
    surface = node.inputs.get("Surface")
    if not surface.is_linked:
        raise Exception("Surface of Material Output is not linked to anything")

    connected_to = surface.links[0].from_node
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
        if limit_normal_effect != None:
            tab = "\t"
            # grab correct UV variable or create
            uv_var = None
            uv_ind = obj.data.uv_layers.active_index
            if is_right_after_bake:
                # we just baked the textures, so we should also take the UVs that we baked them with
                uv_ind = uv_normal_idx
            if "uv_flipped" in special_vars and uv_ind in special_vars["uv_flipped"]:
                uv_var = special_vars["uv_flipped"][uv_ind]
            else:
                uv_var = create_var(node, None, DataTypes.VEC2)
                add_uv_line(uv_var, uv_ind, True)
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
        if limit_normal_effect != None:
            add_line("}", False)
    add_line("EMISSION = " + bsdf + ".EMISSION;", False)


def init_value(node):
    add_line(
        "float "
        + create_var(node, node.outputs[0], DataTypes.FLOAT)
        + " = "
        + get_constant(node, node.outputs[0])
        + ";",
        True,
    )


def init_mix(node):
    match node.data_type:
        case "FLOAT":
            reset_is_constant()
            mix_var = create_var(node, node.outputs.get("Result"), DataTypes.FLOAT)
            a = get_casted_var_or_constant(node, node.inputs.get("A"), DataTypes.FLOAT)
            b = get_casted_var_or_constant(node, node.inputs.get("B"), DataTypes.FLOAT)
            fac = get_casted_var_or_constant(node, node.inputs.get("Factor"), DataTypes.FLOAT)
            if node.clamp_factor:
                fac = "clamp(" + fac + ", 0.0, 1.0)"
            add_line(
                "float " + mix_var + " = mix(" + a + ", " + b + ", " + fac + ");",
                is_constant,
            )
        case "VECTOR":
            reset_is_constant()
            mix_var = create_var(node, node.outputs.get("Result"), DataTypes.VEC3)
            a = get_casted_var_or_constant(node, node.inputs.get("A"), DataTypes.VEC3)
            b = get_casted_var_or_constant(node, node.inputs.get("B"), DataTypes.VEC3)
            fac = None
            if node.factor_mode == "UNIFORM":
                fac = get_casted_var_or_constant(node, node.inputs.get("Factor"), DataTypes.FLOAT)
            elif node.factor_mode == "NON_UNIFORM":
                fac = get_casted_var_or_constant(node, node.inputs.get("Factor"), DataTypes.VEC3)
            if node.clamp_factor:
                fac = "clamp(" + fac + ", 0.0, 1.0)"
            add_line(
                "vec3 " + mix_var + " = mix(" + a + ", " + b + ", " + fac + ");",
                is_constant,
            )
        case "RGBA":
            reset_is_constant()
            # https://github.com/blender/blender/blob/main/intern/cycles/kernel/osl/shaders/node_color_blend.h
            mix_var = create_var(node, node.outputs.get("Result"), DataTypes.VEC3)
            a = get_casted_var_or_constant(node, node.inputs.get("A"), DataTypes.VEC3)
            b = get_casted_var_or_constant(node, node.inputs.get("B"), DataTypes.VEC3)
            fac = get_casted_var_or_constant(node, node.inputs.get("Factor"), DataTypes.FLOAT)
            if node.clamp_factor:
                fac = "clamp(" + fac + ", 0.0, 1.0)"
            line = ""
            match node.blend_type:
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
                    raise UnsupportedSocket(node, node.blend_type)
            if node.clamp_result:
                line = "clamp(" + line + ", 0.0, 1.0)"
            add_line("vec3 " + mix_var + " = " + line + ";", is_constant)


def init_rgb(node):
    add_line(
        "vec3 " + create_var(node, node.outputs[0], DataTypes.VEC3) + " = " + get_constant(node, node.outputs[0]) + ";",
        True,
    )


def init_group(node, type):
    group_nodes_stack.append(node)
    group_output = node.node_tree.nodes.get("Group Output")
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
            type = input_to_data_type(node.outputs[i])
            var = create_var(node, node.outputs[i], type)
            add_line(
                type.value + " " + var + " = " + get_constant(group_output, group_output.inputs[i]) + ";",
                True,
            )


def init_group_input(node):
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


def init_group_output(_node):
    group_nodes_stack.pop()


supported_nodes = {
    "ShaderNodeTexCoord": init_tex_coord,
    "ShaderNodeMath": init_math,
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


def initialize_vars(node, type):
    if node.bl_idname in supported_nodes:
        if node.bl_idname in needs_uv:
            if is_right_after_bake:
                # we just baked the textures, so we should also take the UVs that we baked them with
                if type == "BaseColor":
                    supported_nodes[node.bl_idname](node, uv_base_color_idx)
                elif type == "Metallic" or type == "Roughness":
                    supported_nodes[node.bl_idname](node, uv_roughness_metallic_idx)
                elif type == "Normal":
                    supported_nodes[node.bl_idname](node, uv_normal_idx)
                else:
                    raise Exception("Unknown UV type encountered: " + type)
            else:
                # this is the material how it originally was, we take the UV from the object data
                supported_nodes[node.bl_idname](node, obj.data.uv_layers.active_index)
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
                    raise Exception("Unknown UV type encountered: " + type)
            else:
                # this is the material how it originally was, we take the UV from the object data
                supported_nodes[node.bl_idname](node, obj.data.uv_layers.active_index, type)
        elif node.bl_idname in needs_type:
            supported_nodes[node.bl_idname](node, type)
        else:
            supported_nodes[node.bl_idname](node)
    else:
        raise Exception(node.bl_idname + " not supported yet!")


def dfs(node, path, type):
    if not node.bl_idname in supported_nodes:
        raise Exception("Node " + node.bl_idname + " is not supported")
    for input in node.inputs:
        if input.is_linked:
            for link in input.links:
                visited_name = path + separator + link.from_node.name
                if link.is_valid and not link.is_muted and not visited_name in visited:
                    visited.add(visited_name)
                    if node.bl_idname == "ShaderNodeBsdfPrincipled" and type == None:
                        base_color = node.inputs.get("Base Color")
                        metallic = node.inputs.get("Metallic")
                        roughness = node.inputs.get("Roughness")
                        normal = node.inputs.get("Normal")
                        if input == base_color:
                            dfs(link.from_node, path, "BaseColor")
                        elif input == metallic:
                            dfs(link.from_node, path, "Metallic")
                        elif input == roughness:
                            dfs(link.from_node, path, "Roughness")
                        elif input == normal:
                            dfs(link.from_node, path, "Normal")
                        else:
                            dfs(link.from_node, path, type)
                    else:
                        dfs(link.from_node, path, type)

    initialize_vars(node, type)


def convert_to_godot_shader(
    object,
    material_name,
    cull_mode,
    limit_normal,
    right_after_bake,
    uv_base_color,
    uv_roughness_metallic,
    uv_normal,
):
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
    if not mat.use_nodes:
        raise Exception("Material does not use nodes")

    mat_output_node = mat.node_tree.nodes.get("Material Output")
    if mat_output_node.bl_idname != "ShaderNodeOutputMaterial":
        raise Exception('A node is named "Material Output" but is not actually the material output')

    uniforms = []

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
