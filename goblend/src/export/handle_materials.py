# handle_materials.py
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


from typing import TypeVar, cast

from collections.abc import Callable

import bpy
import os

from ..config import Paths
from ..types.blender_types import NodesModifierProperties

from ..types.goblend_types import GoblendScene, SettingsForGodot, UvMapOverride, ModifierData

from .convert_shader import convert_to_godot_shader

from .bake import bake_base_color, bake_metallic, bake_normal, bake_roughness, get_uv_index_from_name
from .setup import save_path_keys
from ..log import log


def material_prep_gltf_data(mat: bpy.types.Material, settings_for_godot: SettingsForGodot) -> None:
    gltf_extension_materials = cast(GoblendScene, bpy.context.scene).panel_props.gltf_extension.materials
    material = gltf_extension_materials.add()
    material.name = mat.name
    if mat.name in settings_for_godot["material_transparency_mode_overrides"]:
        material.transparency_mode = settings_for_godot["material_transparency_mode_overrides"][mat.name]["mode"]
        if settings_for_godot["material_transparency_mode_overrides"][mat.name]["mode"] == "SCISSOR":
            material.transparency_alpha_scissor_threshold = settings_for_godot["material_transparency_mode_overrides"][
                mat.name
            ]["scissor"]
    else:
        material.transparency_mode = settings_for_godot["transparency_mode"]
        if settings_for_godot["transparency_mode"] == "SCISSOR":
            material.transparency_alpha_scissor_threshold = settings_for_godot["scissor_value"]
    if mat.name in settings_for_godot["material_cull_mode_overrides"]:
        material.cull_mode = settings_for_godot["material_cull_mode_overrides"][mat.name]
    else:
        material.cull_mode = settings_for_godot["cull_mode"]


def get_bsdf_and_mat_output_node_of_mat(mat: bpy.types.Material) -> tuple[bpy.types.ShaderNode, bpy.types.Node]:
    node_tree = cast(bpy.types.ShaderNodeTree, mat.node_tree)
    mat_output_node = cast(bpy.types.ShaderNode | None, node_tree.nodes.get("Material Output"))
    if not mat_output_node:
        raise Exception('Material "' + mat.name + '" has no "Material Output" shader node')
    if mat_output_node.type != "OUTPUT_MATERIAL":
        raise Exception('A node is named "Material Output" but is not actually the material output')
    surface_input = cast(bpy.types.NodeSocket, mat_output_node.inputs.get("Surface"))
    if not surface_input.is_linked:
        raise Exception('Surface input of "Material Output" node is not linked to anything!')
    link = cast(bpy.types.NodeLinks, surface_input.links)[0]
    bsdf = link.from_node
    if not bsdf or bsdf.type != "BSDF_PRINCIPLED":
        raise Exception("Material Output is connected to non-bsdf node, currently not supported")
    return mat_output_node, bsdf


def prepare_material(
    mesh: bpy.types.Mesh, mat: bpy.types.Material, poly_indices: dict[int, int]
) -> tuple[bpy.types.ShaderNode, bpy.types.Node] | None:
    mesh.materials.clear()
    mesh.materials.append(mat)
    # make sure polys are correct again
    for poly in mesh.polygons:
        poly.material_index = poly_indices[poly.index]
    if not mat.use_nodes:
        log("Material not using nodes", "WARNING")
        return None
    return get_bsdf_and_mat_output_node_of_mat(mat)


def handle_texture_group(
    mat: bpy.types.Material, texture_groups: dict[str, str], seen_texture_groups: set[str]
) -> tuple[bool, str, bool]:
    is_in_texture_group = mat.name in texture_groups
    texture_group = ""
    seen_group = False
    if is_in_texture_group:
        texture_group = texture_groups[mat.name]
        if texture_group in seen_texture_groups:
            seen_group = True
        else:
            seen_texture_groups.add(texture_group)

    return is_in_texture_group, texture_group, seen_group


T = TypeVar("T", bound=list[float] | float)


def should_bake_target(
    orig_value: T,
    orig_texture_group: str | None,
    texture_groups: dict[str, str],
    input_name: str,
    is_equal: Callable[[T, T], bool],
) -> bool:
    for mat_name, group_name in texture_groups.items():
        if group_name == orig_texture_group:
            # if this material has this input linked or has a different value we have to bake
            mat = cast(bpy.types.Material, bpy.data.materials.get(mat_name))
            _, bsdf = get_bsdf_and_mat_output_node_of_mat(mat)
            inp = cast(
                bpy.types.NodeSocketFloat | bpy.types.NodeSocketColor | bpy.types.NodeSocketVector,
                bsdf.inputs.get(input_name),
            )
            if inp.is_linked or not is_equal(cast(T, inp.default_value), orig_value):
                return True
    # none of the other materials have linked that input and they all have the same default value
    # hence there is no need to bake this
    return False


def get_bake_targets(
    mat: bpy.types.Material, bsdf: bpy.types.Node, texture_groups: dict[str, str], is_in_texture_group: bool
) -> tuple[bool, bool, bool, bool]:
    base_color = cast(bpy.types.NodeSocketColor, bsdf.inputs.get("Base Color"))
    alpha = cast(bpy.types.NodeSocketFloat, bsdf.inputs.get("Alpha"))
    bake_base_color = base_color.is_linked or alpha.is_linked
    mat_group_name = None
    if is_in_texture_group:
        mat_group_name = texture_groups[mat.name]

    def is_equal_base_color(a: list[float], b: list[float]) -> bool:
        return a[0] == b[0] and a[1] == b[1] and a[2] == b[2] and a[3] == b[3]

    def is_equal_float(a: float, b: float) -> bool:
        return a == b

    def is_equal_vector(a: list[float], b: list[float]) -> bool:
        return a[0] == b[0] and a[1] == b[1] and a[2] == b[2]

    if not bake_base_color and is_in_texture_group:
        # check whether any material in the same texture group is linked or has a different value
        bake_base_color = should_bake_target(
            cast(list[float], base_color.default_value),
            mat_group_name,
            texture_groups,
            "Base Color",
            is_equal_base_color,
        ) or should_bake_target(alpha.default_value, mat_group_name, texture_groups, "Alpha", is_equal_float)
    roughness = cast(bpy.types.NodeSocketFloat, bsdf.inputs.get("Roughness"))
    bake_roughness = roughness.is_linked
    if not bake_roughness and is_in_texture_group:

        bake_roughness = should_bake_target(
            roughness.default_value, mat_group_name, texture_groups, "Roughness", is_equal_float
        )
    metallic = cast(bpy.types.NodeSocketFloat, bsdf.inputs.get("Metallic"))
    bake_metallic = metallic.is_linked
    if not bake_metallic and is_in_texture_group:

        bake_metallic = should_bake_target(
            metallic.default_value, mat_group_name, texture_groups, "Metallic", is_equal_float
        )
    normal = cast(bpy.types.NodeSocketVector, bsdf.inputs.get("Normal"))
    bake_normal = normal.is_linked
    if not bake_normal and is_in_texture_group:

        bake_normal = should_bake_target(
            cast(list[float], normal.default_value), mat_group_name, texture_groups, "Normal", is_equal_vector
        )
    return bake_base_color, bake_roughness, bake_metallic, bake_normal


def save_mesh_and_modifiers(
    obj: bpy.types.Object,
    old_meshes: dict[bpy.types.Object, bpy.types.Mesh],
    orig_mod_per_obj: dict[bpy.types.Object, list[ModifierData]],
) -> None:
    mesh_copy = cast(bpy.types.Mesh, obj.data).copy()
    old_meshes[obj] = cast(bpy.types.Mesh, obj.data)
    obj.data = mesh_copy
    # store modifiers in here
    original_modifiers: list[ModifierData] = []
    # first check for modifiers
    for m in obj.modifiers:
        # handle each modifier differently
        mod_data: ModifierData = {"name": m.name, "type": m.type, "props": {}}
        match m.type:
            case "NODES":  # geometry nodes
                nodes_mod = cast(bpy.types.NodesModifier, m)
                ng = cast(bpy.types.NodesModifier, m).node_group
                if not ng or not ng.interface:
                    continue
                mod_data["node_group"] = ng
                for item in ng.interface.items_tree:
                    if type(item) is not bpy.types.NodeTreeInterfaceSocket:
                        continue
                    identifier = item.identifier
                    # geometry nodes modifier api changed in 5.2, see here: https://developer.blender.org/docs/release_notes/5.2/python_api/
                    if bpy.app.version >= (5, 2, 0):
                        if nodes_mod.properties:
                            properties = cast(NodesModifierProperties, nodes_mod.properties)
                            if hasattr(properties.inputs, identifier) and hasattr(
                                getattr(properties.inputs, identifier), "value"
                            ):
                                mod_data["props"][identifier] = getattr(properties.inputs, identifier).value
                            elif hasattr(properties.outputs, identifier) and hasattr(
                                getattr(properties.outputs, identifier), "value"
                            ):
                                mod_data["props"][identifier] = getattr(properties.outputs, identifier).value
                    else:
                        # old way of accessing modifier properties
                        if identifier in m:
                            mod_data["props"][identifier] = m[identifier]
                original_modifiers.append(mod_data)
                # apply geometry nodes modifier
                bpy.ops.object.modifier_apply(modifier=m.name)

    orig_mod_per_obj[obj] = original_modifiers


def prepare_object(obj: bpy.types.Object) -> bool:
    if obj.type != "MESH":
        return False
    bpy.context.view_layer.objects.active = obj
    # put object in object mode
    if obj.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    # Select and make active
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    return True


def connect_image_textures(
    objects: list[bpy.types.Object],
    created_tex_nodes_per_mat_per_obj: dict[
        bpy.types.Object,
        dict[
            bpy.types.Material,
            dict[str, tuple[bpy.types.ShaderNodeTexImage, bpy.types.NodeSocket, bpy.types.NodeSocket, bpy.types.Node]],
        ],
    ],
    tex_node_to_normal_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node],
    tex_node_to_separate_metallic_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node],
    tex_node_to_combine_metallic_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node],
    tex_node_to_separate_roughness_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node],
    tex_node_to_combine_roughness_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node],
) -> list[str]:
    inputs = ["Base Color", "Metallic", "Roughness", "Normal", "Alpha"]
    for obj in objects:
        for slot in obj.material_slots:
            mat = slot.material
            for inp in inputs:
                if (
                    obj in created_tex_nodes_per_mat_per_obj
                    and mat in created_tex_nodes_per_mat_per_obj[obj]
                    and inp in created_tex_nodes_per_mat_per_obj[obj][mat]
                ):
                    img_tex_node = created_tex_nodes_per_mat_per_obj[obj][mat][inp][0]
                    bsdf = created_tex_nodes_per_mat_per_obj[obj][mat][inp][3]
                    node_tree = cast(bpy.types.ShaderNodeTree, mat.node_tree)
                    if inp == "Normal":
                        normal_map = tex_node_to_normal_dict[img_tex_node]
                        node_tree.links.new(normal_map.outputs["Normal"], bsdf.inputs[inp])
                    elif inp == "Metallic":
                        # we have to create metallic and roughness info on all three rgb channels separately
                        # for metallic:
                        separate_metallic_node = tex_node_to_separate_metallic_dict[img_tex_node]
                        combine_metallic_node = tex_node_to_combine_metallic_dict[img_tex_node]
                        # first separate the color coming from the texture into r, g and b
                        node_tree.links.new(
                            cast(bpy.types.NodeOutputs, img_tex_node.outputs)["Color"],
                            separate_metallic_node.inputs["Color"],
                        )
                        # then connect all inputs from combine with the r output from the separate node
                        node_tree.links.new(separate_metallic_node.outputs[0], combine_metallic_node.inputs[0])
                        node_tree.links.new(separate_metallic_node.outputs[0], combine_metallic_node.inputs[1])
                        node_tree.links.new(separate_metallic_node.outputs[0], combine_metallic_node.inputs[2])
                        node_tree.links.new(combine_metallic_node.outputs["Color"], bsdf.inputs["Metallic"])
                    elif inp == "Roughness":
                        # for roughness:
                        separate_roughness_node = tex_node_to_separate_roughness_dict[img_tex_node]
                        combine_roughness_node = tex_node_to_combine_roughness_dict[img_tex_node]
                        # first separate the color coming from the texture into r, g and b
                        node_tree.links.new(
                            cast(bpy.types.NodeOutputs, img_tex_node.outputs)["Color"],
                            separate_roughness_node.inputs["Color"],
                        )
                        # then connect all inputs from combine with the g output from the separate node
                        node_tree.links.new(separate_roughness_node.outputs[1], combine_roughness_node.inputs[0])
                        node_tree.links.new(separate_roughness_node.outputs[1], combine_roughness_node.inputs[1])
                        node_tree.links.new(separate_roughness_node.outputs[1], combine_roughness_node.inputs[2])
                        node_tree.links.new(combine_roughness_node.outputs["Color"], bsdf.inputs["Roughness"])
                    elif inp == "Base Color":
                        node_tree.links.new(
                            cast(bpy.types.NodeOutputs, img_tex_node.outputs)["Color"], bsdf.inputs[inp]
                        )
                    else:  # inp == "Alpha"
                        node_tree.links.new(
                            cast(bpy.types.NodeOutputs, img_tex_node.outputs)["Alpha"], bsdf.inputs[inp]
                        )

    return inputs


def check_convert_to_shader(
    settings_for_godot: SettingsForGodot, already_converted_mats: set[str], objects: list[bpy.types.Object]
) -> None:
    for mat_name, obj in settings_for_godot["use_shader_mats"].items():
        if mat_name in already_converted_mats:
            continue
        # do not do anything with objects that aren't exported
        if obj not in objects:
            continue
        cull_mode = ""
        if mat_name in settings_for_godot["material_cull_mode_overrides"]:
            cull_mode = settings_for_godot["material_cull_mode_overrides"][mat_name]
        else:
            cull_mode = settings_for_godot["cull_mode"]
        try:
            limit_normal = None
            if mat_name in settings_for_godot["limit_uv_effect_normal"]:
                limit_normal = settings_for_godot["limit_uv_effect_normal"][mat_name]
                # if right_after_bake is false, the 3 uv indices don't matter so we can safely pass None for them
            code, uniforms = convert_to_godot_shader(obj, mat_name, cull_mode, limit_normal, False, None, None, None)
            material = bpy.context.scene.panel_props.gltf_extension.materials.add()
            material.name = mat_name
            material.shader_code = code
            for uniform in uniforms:
                shader_uniform = material.shader_uniforms.add()
                shader_uniform.var_name = uniform[0]
                shader_uniform.uniform_data = uniform[1]
        except Exception as e:
            log("Exception while trying to generate shader code: " + repr(e), "ERROR")
            raise e


def check_early_convert_to_shader(
    uv_map_override: UvMapOverride, settings_for_godot: SettingsForGodot, objects: list[bpy.types.Object]
) -> set[str]:
    seen_mat_names: set[str] = set()
    for obj_name in uv_map_override:
        obj = uv_map_override[obj_name]["obj"]
        # do not do anything with objects that aren't exported
        if obj not in objects:
            continue
        mat_slots: list[bpy.types.MaterialSlot] = []
        for slot in obj.material_slots:
            if slot.material is not None:
                mat_slots.append(slot)
        for slot in mat_slots:
            mat = cast(bpy.types.Material, slot.material)
            mat_name = mat.name
            if mat_name in seen_mat_names or mat_name in settings_for_godot["use_shader_mats"]:
                continue
            seen_mat_names.add(mat_name)
            cull_mode = ""
            if mat_name in settings_for_godot["material_cull_mode_overrides"]:
                cull_mode = settings_for_godot["material_cull_mode_overrides"][mat_name]
            else:
                cull_mode = settings_for_godot["cull_mode"]
            try:
                limit_normal = None
                if mat_name in settings_for_godot["limit_uv_effect_normal"]:
                    limit_normal = settings_for_godot["limit_uv_effect_normal"][mat_name]
                mesh = cast(bpy.types.Mesh, obj.data)
                code, uniforms = convert_to_godot_shader(
                    obj,
                    mat_name,
                    cull_mode,
                    limit_normal,
                    True,
                    get_uv_index_from_name(uv_map_override[obj_name]["Base Color"], mesh),
                    get_uv_index_from_name(uv_map_override[obj_name]["Metallic/Roughness"], mesh),
                    get_uv_index_from_name(uv_map_override[obj_name]["Normal"], mesh),
                )
                material = bpy.context.scene.panel_props.gltf_extension.materials.add()
                material.name = mat_name
                material.shader_code = code
                for uniform in uniforms:
                    shader_uniform = material.shader_uniforms.add()
                    shader_uniform.var_name = uniform[0]
                    shader_uniform.uniform_data = uniform[1]
            except Exception as e:
                log("Exception while trying to generate shader code: " + repr(e), "ERROR")
                raise e
    for mat_name in settings_for_godot["limit_uv_effect_normal"]:
        # if use shader is on we convert the shader later to convert the original shader
        # and not the one with the baked textures
        if mat_name in seen_mat_names or mat_name in settings_for_godot["use_shader_mats"]:
            continue
        seen_mat_names.add(mat_name)
        cull_mode = ""
        if mat_name in settings_for_godot["material_cull_mode_overrides"]:
            cull_mode = settings_for_godot["material_cull_mode_overrides"][mat_name]
        else:
            cull_mode = settings_for_godot["cull_mode"]
        try:
            limit_normal = settings_for_godot["limit_uv_effect_normal"][mat_name]
            obj = cast(bpy.types.Object, settings_for_godot["limit_uv_effect_normal"][mat_name]["obj"])
            mesh = cast(bpy.types.Mesh, obj.data)
            code, uniforms = convert_to_godot_shader(
                obj,
                mat_name,
                cull_mode,
                limit_normal,
                True,
                # if there were indices specified we would've handled the material in the previous loop
                cast(int, mesh.uv_layers.active_index),
                cast(int, mesh.uv_layers.active_index),
                cast(int, mesh.uv_layers.active_index),
            )
            material = bpy.context.scene.panel_props.gltf_extension.materials.add()
            material.name = mat_name
            material.shader_code = code
            for uniform in uniforms:
                shader_uniform = material.shader_uniforms.add()
                shader_uniform.var_name = uniform[0]
                shader_uniform.uniform_data = uniform[1]
        except Exception as e:
            log("Exception while trying to generate shader code: " + repr(e), "ERROR")
            raise e
    return seen_mat_names


def handle_materials(
    uv_map_override: UvMapOverride,
    objects: list[bpy.types.Object],
    paths: Paths,
    texture_groups: dict[str, str],
    settings_for_godot: SettingsForGodot,
    bake_margins: dict[str, int],
    texture_dim: dict[str, int],
    texture_overrides: dict[str, list[int]],
) -> tuple[
    list[tuple[bpy.types.Node, bpy.types.Nodes]],
    list[str],
    dict[
        bpy.types.Object,
        dict[
            bpy.types.Material,
            dict[str, tuple[bpy.types.ShaderNodeTexImage, bpy.types.NodeSocket, bpy.types.NodeSocket, bpy.types.Node]],
        ],
    ],
    dict[bpy.types.Object, bpy.types.Mesh],
    dict[bpy.types.Object, list[ModifierData]],
    set[str],
    set[bpy.types.Image],
]:
    images_created: set[bpy.types.Image] = set()
    scene = cast(GoblendScene, bpy.context.scene)
    seen_mats: set[str] = set()
    seen_texture_groups: set[str] = set()
    extra_shader_nodes: list[tuple[bpy.types.Node, bpy.types.Nodes]] = []
    old_meshes: dict[bpy.types.Object, bpy.types.Mesh] = {}
    orig_mod_per_obj: dict[bpy.types.Object, list[ModifierData]] = {}
    created_tex_nodes_per_mat_per_obj: dict[
        bpy.types.Object,
        dict[
            bpy.types.Material,
            dict[str, tuple[bpy.types.ShaderNodeTexImage, bpy.types.NodeSocket, bpy.types.NodeSocket, bpy.types.Node]],
        ],
    ] = {}
    tex_node_to_normal_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node] = {}
    tex_node_to_separate_metallic_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node] = {}
    tex_node_to_combine_metallic_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node] = {}
    tex_node_to_separate_roughness_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node] = {}
    tex_node_to_combine_roughness_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node] = {}

    for save_path in save_path_keys:
        setattr(scene.panel_props.gltf_extension.save_paths, save_path, os.path.normcase(paths[save_path]))

    for obj in objects:
        if not prepare_object(obj):
            continue

        # TODO: maybe all of this saving operators and saving meshes not needed if I can simply undo the whole export operator
        # save old mesh to after exporting
        save_mesh_and_modifiers(obj, old_meshes, orig_mod_per_obj)

        created_tex_nodes_per_mat: dict[
            bpy.types.Material,
            dict[str, tuple[bpy.types.ShaderNodeTexImage, bpy.types.NodeSocket, bpy.types.NodeSocket, bpy.types.Node]],
        ] = {}

        # for each material of the object create textures
        mat_slots: list[bpy.types.MaterialSlot] = []
        # store all materials in an array, remove them all from the object and always only have one material slot
        # because having multiple will result in all of them baking at the same time
        materials: list[bpy.types.Material] = []
        for slot in obj.material_slots:
            if slot.material is not None:
                mat_slots.append(slot)
                materials.append(slot.material)

        poly_indices: dict[int, int] = {}
        for poly in cast(bpy.types.Mesh, obj.data).polygons:
            poly_indices[poly.index] = poly.material_index

        for mat in materials:
            if mat.name in settings_for_godot["use_shader_mats"]:
                settings_for_godot["use_shader_mats"][mat.name] = obj
            if mat.name in settings_for_godot["limit_uv_effect_normal"]:
                settings_for_godot["limit_uv_effect_normal"][mat.name]["obj"] = obj
            material_output_and_bsdf = prepare_material(cast(bpy.types.Mesh, obj.data), mat, poly_indices)
            if not material_output_and_bsdf:
                continue
            mat_output_node, bsdf = material_output_and_bsdf
            material_prep_gltf_data(mat, settings_for_godot)
            is_in_texture_group, texture_group, seen_group = handle_texture_group(
                mat, texture_groups, seen_texture_groups
            )
            link_array: list[list[str]] = []
            seen_mat = False
            if mat.name in seen_mats:
                seen_mat = True
                log(
                    "Using the same material ("
                    + mat.name
                    + ") on more than one object, baking to the same image as before! If these objects have overlapping UV maps this is (potentially) bad"
                )
            else:
                seen_mats.add(mat.name)

            # create a combine color node to split metallic and roughness into red and green channels respectively
            combine_color = cast(bpy.types.ShaderNodeTree, mat.node_tree).nodes.new("ShaderNodeCombineColor")
            cast(bpy.types.NodeSocketFloat, combine_color.inputs[2]).default_value = 0.0
            cast(bpy.types.NodeSocketFloat, combine_color.inputs[0]).default_value = 0.0

            created_texture_nodes: dict[
                str, tuple[bpy.types.ShaderNodeTexImage, bpy.types.NodeSocket, bpy.types.NodeSocket, bpy.types.Node]
            ] = {}

            alpha_input = cast(bpy.types.NodeSocketFloat, bsdf.inputs.get("Alpha"))
            use_alpha_on_base_color = alpha_input.is_linked or alpha_input.default_value != 1.0

            if mat.name not in settings_for_godot["use_shader_mats"]:
                log("Checking material '" + mat.name + "' on object '" + obj.name + "'")

                should_bake_base_color, should_bake_roughness, should_bake_metallic, should_bake_normal = (
                    get_bake_targets(mat, bsdf, texture_groups, is_in_texture_group)
                )
                emission = None
                # bake materials
                if should_bake_base_color:
                    bake_base_color(
                        obj,
                        mat,
                        scene,
                        bsdf,
                        mat_output_node,
                        bake_margins,
                        seen_mat,
                        alpha_input,
                        paths["texture_save_path"],
                        images_created,
                        link_array,
                        uv_map_override,
                        extra_shader_nodes,
                        created_texture_nodes,
                        seen_group,
                        is_in_texture_group,
                        texture_group,
                        texture_dim,
                        texture_overrides,
                        use_alpha_on_base_color,
                    )
                if should_bake_metallic:
                    emission = bake_metallic(
                        obj,
                        mat,
                        scene,
                        bsdf,
                        mat_output_node,
                        bake_margins,
                        seen_mat,
                        paths["texture_save_path"],
                        images_created,
                        link_array,
                        uv_map_override,
                        extra_shader_nodes,
                        created_texture_nodes,
                        seen_group,
                        is_in_texture_group,
                        texture_group,
                        texture_dim,
                        texture_overrides,
                        tex_node_to_separate_metallic_dict,
                        tex_node_to_combine_metallic_dict,
                        combine_color,
                        should_bake_roughness,
                    )
                if should_bake_roughness:
                    bake_roughness(
                        obj,
                        mat,
                        scene,
                        bsdf,
                        mat_output_node,
                        bake_margins,
                        seen_mat,
                        paths["texture_save_path"],
                        images_created,
                        link_array,
                        uv_map_override,
                        extra_shader_nodes,
                        created_texture_nodes,
                        seen_group,
                        is_in_texture_group,
                        texture_group,
                        texture_dim,
                        texture_overrides,
                        tex_node_to_separate_roughness_dict,
                        tex_node_to_combine_roughness_dict,
                        combine_color,
                        emission,
                        should_bake_metallic,
                    )
                if should_bake_normal:
                    bake_normal(
                        obj,
                        mat,
                        scene,
                        bsdf,
                        bake_margins,
                        seen_mat,
                        paths["texture_save_path"],
                        images_created,
                        link_array,
                        uv_map_override,
                        extra_shader_nodes,
                        created_texture_nodes,
                        seen_group,
                        is_in_texture_group,
                        texture_group,
                        texture_dim,
                        texture_overrides,
                        tex_node_to_normal_dict,
                    )

                # transmission
                transmission = cast(bpy.types.NodeSocketFloat, bsdf.inputs.get("Transmission Weight"))
                # we only handle single float values here
                # to support textures later on, we'd need to bake the values
                # into the alpha channel of the base color
                if not transmission.is_linked and transmission.default_value > 0.0:
                    link_array.append(["Transmission", str(transmission.default_value), "all"])

            # remove combine color node
            cast(bpy.types.ShaderNodeTree, mat.node_tree).nodes.remove(combine_color)
            created_tex_nodes_per_mat[mat] = created_texture_nodes
        created_tex_nodes_per_mat_per_obj[obj] = created_tex_nodes_per_mat

        # restore materials
        mesh = cast(bpy.types.Mesh, obj.data)
        mesh.materials.clear()
        for mat in materials:
            mesh.materials.append(mat)
        for poly in mesh.polygons:
            poly.material_index = poly_indices[poly.index]

    # all textures for all materials for all objects are created, connect the image textures to the inputs of the principled bsdf
    inputs = connect_image_textures(
        objects,
        created_tex_nodes_per_mat_per_obj,
        tex_node_to_normal_dict,
        tex_node_to_separate_metallic_dict,
        tex_node_to_combine_metallic_dict,
        tex_node_to_separate_roughness_dict,
        tex_node_to_combine_roughness_dict,
    )

    # if either limiting normal effect with disabled use shader or separate UV maps are set, we have to convert to a shader here
    converted_mat_names = check_early_convert_to_shader(uv_map_override, settings_for_godot, objects)

    return (
        extra_shader_nodes,
        inputs,
        created_tex_nodes_per_mat_per_obj,
        old_meshes,
        orig_mod_per_obj,
        converted_mat_names,
        images_created,
    )
