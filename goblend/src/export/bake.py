# bake.py
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


from typing import cast

import bpy
import os

from ..types.goblend_types import GoblendScene, UvMapOverride, UvMapOverrideValueKeys
from ..types.blender_types import BakePassTypeItems, ColorSpaceConvertDefaultItems
from ..log import log


def bake_alpha(
    mat: bpy.types.Material,
    img: bpy.types.Image,
    emission_color_link: bpy.types.NodeLink,
    alpha_input: bpy.types.NodeSocketFloat,
    emission: bpy.types.Node,
    scene: GoblendScene,
) -> None:
    rgb_pixels = list(cast(list[float], img.pixels))
    node_tree = cast(bpy.types.ShaderNodeTree, mat.node_tree)
    # make new link from alpha to emission strength
    node_tree.links.remove(emission_color_link)
    if alpha_input.is_linked:
        node_tree.links.new(
            cast(bpy.types.NodeSocket, cast(bpy.types.NodeLinks, alpha_input.links)[0].from_socket),
            emission.inputs["Strength"],
        )
    else:
        cast(bpy.types.NodeSocketFloat, emission.inputs["Strength"]).default_value = alpha_input.default_value
    # bake alpha values
    bpy.ops.object.bake(type="EMIT", save_mode="INTERNAL")
    alpha_pixels = list(cast(list[float], img.pixels))
    # combine into one image
    final_pixels: list[float] = []
    for i in range(0, len(rgb_pixels), 4):
        r = rgb_pixels[i]
        g = rgb_pixels[i + 1]
        b = rgb_pixels[i + 2]
        a = alpha_pixels[i]
        final_pixels.extend([r, g, b, a])
    img.pixels = final_pixels


def get_uv_index_from_name(uv_map_name: str, mesh: bpy.types.Mesh) -> int:
    c = 0
    for layer in mesh.uv_layers:
        if layer.name == uv_map_name:
            break
        c += 1
    return c


def check_uv_map_target(
    obj: bpy.types.Object, uv_map_override: UvMapOverride, key: UvMapOverrideValueKeys
) -> int | None:
    mesh = cast(bpy.types.Mesh, obj.data)
    old_active_ind_uv_map = mesh.uv_layers.active_index
    if not mesh.uv_layers.active_index or mesh.uv_layers.active_index < 0:
        mesh.uv_layers.active_index = 0
    if obj.name in uv_map_override:
        uv_map_name = uv_map_override[obj.name][key]
        idx = get_uv_index_from_name(uv_map_name, mesh)
        mesh.uv_layers.active_index = idx
    return old_active_ind_uv_map


def create_image_texture_node(
    node_tree: bpy.types.ShaderNodeTree,
    bsdf: bpy.types.Node,
    seen_mat: bool,
    extra_shader_nodes: list[tuple[bpy.types.Node, bpy.types.Nodes]],
    created_texture_nodes: dict[
        str, tuple[bpy.types.ShaderNodeTexImage, bpy.types.NodeSocket, bpy.types.NodeSocket, bpy.types.Node]
    ],
    main_socket: bpy.types.NodeSocket,
    socket_connected_to_main_socket: bpy.types.NodeSocket,
    type: str,
    key: str,
) -> tuple[bpy.types.ShaderNodeTexImage, bool]:
    node_name = "BakeTarget" + type + "ImageTextureNode"
    if not seen_mat and node_tree.nodes.get(node_name) is not None:
        raise Exception("A node named '" + node_name + "' already exists! Please rename it")
    img_texture_node = None
    if seen_mat:
        img_texture_node = cast(bpy.types.ShaderNodeTexImage, node_tree.nodes.get(node_name))
        return img_texture_node, False
    else:
        img_texture_node = cast(bpy.types.ShaderNodeTexImage, node_tree.nodes.new("ShaderNodeTexImage"))
        img_texture_node.name = node_name
        extra_shader_nodes.append((img_texture_node, node_tree.nodes))

        created_texture_nodes[key] = (
            img_texture_node,
            main_socket,
            socket_connected_to_main_socket,
            bsdf,
        )
        return img_texture_node, True


def bake_and_clean_up(
    obj: bpy.types.Object,
    mat: bpy.types.Material,
    scene: GoblendScene,
    img: bpy.types.Image,
    img_name: str,
    bsdf: bpy.types.Node,
    mat_output_node: bpy.types.ShaderNode | None,
    seen_mat: bool,
    seen_group: bool,
    bake_margins: dict[str, int],
    use_alpha: bool,
    emission_color_link: bpy.types.NodeLink | None,
    alpha_input: bpy.types.NodeSocketFloat | None,
    emission: bpy.types.Node | None,
    images_created: set[bpy.types.Image],
    old_active_ind_uv_map: int | None,
    bake_type: BakePassTypeItems,
) -> None:
    old_bake_margin = scene.render.bake.margin
    if mat.name in bake_margins:
        scene.render.bake.margin = bake_margins[mat.name]
    scene.render.bake.use_clear = not seen_mat and not seen_group
    scene.render.bake.use_selected_to_active = False
    log("Baking " + img_name + "... (this might take a while)")
    bpy.ops.object.bake(type=bake_type, save_mode="INTERNAL")
    if use_alpha:
        # we need to bake alpha separately and add it to the image
        if emission_color_link is not None and alpha_input is not None and emission is not None:
            bake_alpha(
                mat,
                img,
                emission_color_link,
                alpha_input,
                emission,
                scene,
            )
        else:
            log(
                "This should not happen, report on GitHub. Debug info: ecl="
                + str(emission_color_link)
                + ", ai="
                + str(alpha_input)
                + ", e="
                + str(emission),
                "WARNING",
            )

    log("Baked " + img_name)
    img.save()
    images_created.add(img)

    # remove emission node and restore links from before
    if emission is not None and mat_output_node is not None:
        cast(bpy.types.ShaderNodeTree, mat.node_tree).nodes.remove(emission)
        cast(bpy.types.ShaderNodeTree, mat.node_tree).links.new(bsdf.outputs[0], mat_output_node.inputs["Surface"])

    # restore old active index of uv map
    cast(bpy.types.Mesh, obj.data).uv_layers.active_index = old_active_ind_uv_map
    # restore bake margin
    scene.render.bake.margin = old_bake_margin


def get_or_create_image(
    mat: bpy.types.Material,
    name: str,
    seen_mat: bool,
    seen_group: bool,
    is_in_texture_group: bool,
    texture_group: str,
    texture_dim: dict[str, int],
    texture_overrides: dict[str, list[int]],
    use_alpha: bool,
    img_texture_node: bpy.types.ShaderNodeTexImage,
    color_space: str,
    export_path_tex: str,
) -> tuple[str, bpy.types.Image]:
    img_name = ""
    if is_in_texture_group:
        img_name = texture_group
    else:
        img_name = mat.name
    img_name = img_name + name
    img = None
    found = False
    if seen_mat or seen_group:
        img = bpy.data.images.get(img_name)
        found = img is not None
    if not found:
        tex_dim_x = texture_dim["x"]
        tex_dim_y = texture_dim["y"]
        if mat.name in texture_overrides:
            tex_dim_x = texture_overrides[mat.name][0]
            tex_dim_y = texture_overrides[mat.name][1]
        img = bpy.data.images.new(img_name, tex_dim_x, tex_dim_y, alpha=use_alpha)
        if use_alpha:
            img.alpha_mode = "STRAIGHT"
        else:
            img.alpha_mode = "NONE"
        if img.colorspace_settings:
            img.colorspace_settings.name = cast(ColorSpaceConvertDefaultItems, color_space)
        # create path if it doesn't exist yet
        os.makedirs(export_path_tex, exist_ok=True)
        img.filepath = export_path_tex + img_name + ".png"
    img_texture_node.image = img
    return img_name, cast(bpy.types.Image, img)


def make_emission_node(mat: bpy.types.Material, mat_output_node: bpy.types.ShaderNode) -> bpy.types.Node:
    node_tree = cast(bpy.types.ShaderNodeTree, mat.node_tree)
    emission = node_tree.nodes.new("ShaderNodeEmission")
    node_tree.links.new(emission.outputs["Emission"], mat_output_node.inputs["Surface"])
    return emission


def bake_base_color(
    obj: bpy.types.Object,
    mat: bpy.types.Material,
    scene: GoblendScene,
    bsdf: bpy.types.Node,
    mat_output_node: bpy.types.ShaderNode,
    bake_margins: dict[str, int],
    seen_mat: bool,
    alpha_input: bpy.types.NodeSocketFloat,
    export_path_tex: str,
    images_created: set[bpy.types.Image],
    link_array: list[list[str]],
    uv_map_override: UvMapOverride,
    extra_shader_nodes: list[tuple[bpy.types.Node, bpy.types.Nodes]],
    created_texture_nodes: dict[
        str, tuple[bpy.types.ShaderNodeTexImage, bpy.types.NodeSocket, bpy.types.NodeSocket, bpy.types.Node]
    ],
    seen_group: bool,
    is_in_texture_group: bool,
    texture_group: str,
    texture_dim: dict[str, int],
    texture_overrides: dict[str, list[int]],
    use_alpha_on_base_color: bool,
) -> None:
    base_color = cast(bpy.types.NodeSocketColor, bsdf.inputs.get("Base Color"))
    node_tree = cast(bpy.types.ShaderNodeTree, mat.node_tree)
    if not base_color.is_linked:
        # create a value node in case there is no connection
        rgb_node = node_tree.nodes.new("ShaderNodeRGB")
        extra_shader_nodes.append((rgb_node, node_tree.nodes))
        cast(bpy.types.NodeSocketColor, rgb_node.outputs[0]).default_value = base_color.default_value
        node_tree.links.new(rgb_node.outputs[0], base_color)
    socket_connected_to_base_color = cast(
        bpy.types.NodeSocket, cast(bpy.types.NodeLinks, base_color.links)[0].from_socket
    )
    # create image texture node
    img_texture_node, _ = create_image_texture_node(
        node_tree,
        bsdf,
        seen_mat,
        extra_shader_nodes,
        created_texture_nodes,
        base_color,
        socket_connected_to_base_color,
        "BaseColor",
        "Base Color",
    )

    if alpha_input.is_linked:
        socket_connected_to_alpha = cast(
            bpy.types.NodeSocket, cast(bpy.types.NodeLinks, alpha_input.links)[0].from_socket
        )
        created_texture_nodes["Alpha"] = (
            img_texture_node,
            alpha_input,
            socket_connected_to_alpha,
            bsdf,
        )

    # connect color to emission node to make sure only color is baked
    emission = make_emission_node(mat, mat_output_node)
    emission_color_link = node_tree.links.new(socket_connected_to_base_color, emission.inputs["Color"])

    # get or create the image
    img_name, img = get_or_create_image(
        mat,
        "BaseColor",
        seen_mat,
        seen_group,
        is_in_texture_group,
        texture_group,
        texture_dim,
        texture_overrides,
        use_alpha_on_base_color,
        img_texture_node,
        "sRGB",
        export_path_tex,
    )

    link_array.append(["Base Color", img_name + ".png", "all"])

    # check for other UV map targets
    old_active_ind_uv_map = check_uv_map_target(obj, uv_map_override, "Base Color")

    img_texture_node.select = True
    node_tree.nodes.active = img_texture_node

    # bake and save file
    bake_and_clean_up(
        obj,
        mat,
        scene,
        img,
        img_name,
        bsdf,
        mat_output_node,
        seen_mat,
        seen_group,
        bake_margins,
        use_alpha_on_base_color,
        emission_color_link,
        alpha_input,
        emission,
        images_created,
        old_active_ind_uv_map,
        "EMIT",
    )


def bake_metallic(
    obj: bpy.types.Object,
    mat: bpy.types.Material,
    scene: GoblendScene,
    bsdf: bpy.types.Node,
    mat_output_node: bpy.types.ShaderNode,
    bake_margins: dict[str, int],
    seen_mat: bool,
    export_path_tex: str,
    images_created: set[bpy.types.Image],
    link_array: list[list[str]],
    uv_map_override: UvMapOverride,
    extra_shader_nodes: list[tuple[bpy.types.Node, bpy.types.Nodes]],
    created_texture_nodes: dict[
        str, tuple[bpy.types.ShaderNodeTexImage, bpy.types.NodeSocket, bpy.types.NodeSocket, bpy.types.Node]
    ],
    seen_group: bool,
    is_in_texture_group: bool,
    texture_group: str,
    texture_dim: dict[str, int],
    texture_overrides: dict[str, list[int]],
    tex_node_to_separate_metallic_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node],
    tex_node_to_combine_metallic_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node],
    combine_color: bpy.types.Node,
    should_bake_roughness: bool,
) -> bpy.types.Node:
    metallic = cast(bpy.types.NodeSocketFloat, bsdf.inputs.get("Metallic"))
    emission = None
    value_node = None
    node_tree = cast(bpy.types.ShaderNodeTree, mat.node_tree)
    if not metallic.is_linked:
        # create a value node in case there is no connection
        value_node = node_tree.nodes.new("ShaderNodeValue")
        extra_shader_nodes.append((value_node, node_tree.nodes))
        cast(bpy.types.NodeSocketFloat, value_node.outputs[0]).default_value = metallic.default_value
        node_tree.links.new(value_node.outputs[0], metallic)
    socket_connected_to_metallic = cast(bpy.types.NodeSocket, cast(bpy.types.NodeLinks, metallic.links)[0].from_socket)
    # create image texture node
    img_texture_node, create_additional_nodes = create_image_texture_node(
        node_tree,
        bsdf,
        seen_mat,
        extra_shader_nodes,
        created_texture_nodes,
        metallic,
        socket_connected_to_metallic,
        "MetalRoughness",
        "Metallic",
    )
    if create_additional_nodes:
        # also create metallic separate and combine nodes
        separate_metallic_node = node_tree.nodes.new("ShaderNodeSeparateColor")
        combine_metallic_node = node_tree.nodes.new("ShaderNodeCombineColor")
        extra_shader_nodes.append((separate_metallic_node, node_tree.nodes))
        extra_shader_nodes.append((combine_metallic_node, node_tree.nodes))
        tex_node_to_separate_metallic_dict[img_texture_node] = separate_metallic_node
        tex_node_to_combine_metallic_dict[img_texture_node] = combine_metallic_node

    # connect color to combine color node (red channel)
    node_tree.links.new(socket_connected_to_metallic, combine_color.inputs[0])
    # for some reason all sockets need to be connected, otherwise the image is
    # misinterpreted by godot and compresses with the wrong compression, doubling the file size
    # green channel can easily be overwritten by roughness still, we just connect it below
    node_tree.links.new(socket_connected_to_metallic, combine_color.inputs[1])
    node_tree.links.new(socket_connected_to_metallic, combine_color.inputs[2])
    # connect combine color to emission node to make sure only color is baked
    emission = make_emission_node(mat, mat_output_node)
    node_tree.links.new(combine_color.outputs[0], emission.inputs["Color"])

    if (
        not should_bake_roughness
    ):  # if roughness isn't linked do all the baking, otherwise we'll do it in the roughness section below
        # get or create the image
        img_name, img = get_or_create_image(
            mat,
            "MetallicRoughness",
            seen_mat,
            seen_group,
            is_in_texture_group,
            texture_group,
            texture_dim,
            texture_overrides,
            False,
            img_texture_node,
            "Non-Color",
            export_path_tex,
        )

        link_array.append(["Metallic", img_name + ".png", "red"])

        # check for other UV map targets
        old_active_ind_uv_map = check_uv_map_target(obj, uv_map_override, "Metallic/Roughness")

        img_texture_node.select = True
        node_tree.nodes.active = img_texture_node

        # bake and save file
        bake_and_clean_up(
            obj,
            mat,
            scene,
            img,
            img_name,
            bsdf,
            mat_output_node,
            seen_mat,
            seen_group,
            bake_margins,
            False,
            None,
            None,
            emission,
            images_created,
            old_active_ind_uv_map,
            "EMIT",
        )
    return emission


def bake_roughness(
    obj: bpy.types.Object,
    mat: bpy.types.Material,
    scene: GoblendScene,
    bsdf: bpy.types.Node,
    mat_output_node: bpy.types.ShaderNode,
    bake_margins: dict[str, int],
    seen_mat: bool,
    export_path_tex: str,
    images_created: set[bpy.types.Image],
    link_array: list[list[str]],
    uv_map_override: UvMapOverride,
    extra_shader_nodes: list[tuple[bpy.types.Node, bpy.types.Nodes]],
    created_texture_nodes: dict[
        str, tuple[bpy.types.ShaderNodeTexImage, bpy.types.NodeSocket, bpy.types.NodeSocket, bpy.types.Node]
    ],
    seen_group: bool,
    is_in_texture_group: bool,
    texture_group: str,
    texture_dim: dict[str, int],
    texture_overrides: dict[str, list[int]],
    tex_node_to_separate_roughness_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node],
    tex_node_to_combine_roughness_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node],
    combine_color: bpy.types.Node,
    emission: bpy.types.Node | None,
    should_bake_metallic: bool,
) -> None:
    roughness = cast(bpy.types.NodeSocketFloat, bsdf.inputs.get("Roughness"))
    value_node = None
    node_tree = cast(bpy.types.ShaderNodeTree, mat.node_tree)
    if not roughness.is_linked:
        # create a value node in case there is no connection
        value_node = node_tree.nodes.new("ShaderNodeValue")
        extra_shader_nodes.append((value_node, node_tree.nodes))
        cast(bpy.types.NodeSocketFloat, value_node.outputs[0]).default_value = roughness.default_value
        node_tree.links.new(value_node.outputs[0], roughness)
    socket_connected_to_roughness = cast(
        bpy.types.NodeSocket, cast(bpy.types.NodeLinks, roughness.links)[0].from_socket
    )
    # create image texture node
    if (
        not seen_mat
        and not should_bake_metallic
        and node_tree.nodes.get("BakeTargetMetalRoughnessImageTextureNode") is not None
    ):
        raise Exception("A node named 'BakeTargetMetalRoughnessImageTextureNode' already exists! Please rename it")
    img_texture_node = None
    if seen_mat or should_bake_metallic:
        img_texture_node = cast(
            bpy.types.ShaderNodeTexImage, node_tree.nodes.get("BakeTargetMetalRoughnessImageTextureNode")
        )
        if not seen_mat:
            # also create metallic separate and combine nodes
            separate_roughness_node = node_tree.nodes.new("ShaderNodeSeparateColor")
            combine_roughness_node = node_tree.nodes.new("ShaderNodeCombineColor")
            extra_shader_nodes.append((separate_roughness_node, node_tree.nodes))
            extra_shader_nodes.append((combine_roughness_node, node_tree.nodes))
            tex_node_to_separate_roughness_dict[img_texture_node] = separate_roughness_node
            tex_node_to_combine_roughness_dict[img_texture_node] = combine_roughness_node

            created_texture_nodes["Roughness"] = (
                img_texture_node,
                roughness,
                socket_connected_to_roughness,
                bsdf,
            )
    else:
        img_texture_node = cast(bpy.types.ShaderNodeTexImage, node_tree.nodes.new("ShaderNodeTexImage"))
        img_texture_node.name = "BakeTargetMetalRoughnessImageTextureNode"
        extra_shader_nodes.append((img_texture_node, node_tree.nodes))
        # also create metallic separate and combine nodes
        separate_roughness_node = node_tree.nodes.new("ShaderNodeSeparateColor")
        combine_roughness_node = node_tree.nodes.new("ShaderNodeCombineColor")
        extra_shader_nodes.append((separate_roughness_node, node_tree.nodes))
        extra_shader_nodes.append((combine_roughness_node, node_tree.nodes))
        tex_node_to_separate_roughness_dict[img_texture_node] = separate_roughness_node
        tex_node_to_combine_roughness_dict[img_texture_node] = combine_roughness_node

        created_texture_nodes["Roughness"] = (
            img_texture_node,
            roughness,
            socket_connected_to_roughness,
            bsdf,
        )

    # connect color to combine color node (green channel)
    node_tree.links.new(socket_connected_to_roughness, combine_color.inputs[1])
    # for some reason all sockets need to be connected, otherwise the image is
    # misinterpreted by godot and compresses with the wrong compression, doubling the file size
    node_tree.links.new(socket_connected_to_roughness, combine_color.inputs[2])
    if not should_bake_metallic:
        # only connect to red channel if it wasn't connected by metallic
        node_tree.links.new(socket_connected_to_roughness, combine_color.inputs[0])
    # connect combine color to emission node to make sure only color is baked
    if not should_bake_metallic:  # otherwise we have already created an emission node
        emission = make_emission_node(mat, mat_output_node)
        node_tree.links.new(combine_color.outputs[0], emission.inputs["Color"])

    # get or create the image
    img_name, img = get_or_create_image(
        mat,
        "MetallicRoughness",
        seen_mat,
        seen_group,
        is_in_texture_group,
        texture_group,
        texture_dim,
        texture_overrides,
        False,
        img_texture_node,
        "Non-Color",
        export_path_tex,
    )

    link_array.append(["Roughness", img_name + ".png", "green"])
    if should_bake_metallic:
        link_array.append(["Metallic", img_name + ".png", "red"])

    # check for other UV map targets
    old_active_ind_uv_map = check_uv_map_target(obj, uv_map_override, "Metallic/Roughness")

    img_texture_node.select = True
    node_tree.nodes.active = img_texture_node

    # bake and save file
    bake_and_clean_up(
        obj,
        mat,
        scene,
        img,
        img_name,
        bsdf,
        mat_output_node,
        seen_mat,
        seen_group,
        bake_margins,
        False,
        None,
        None,
        emission,
        images_created,
        old_active_ind_uv_map,
        "EMIT",
    )


def bake_normal(
    obj: bpy.types.Object,
    mat: bpy.types.Material,
    scene: GoblendScene,
    bsdf: bpy.types.Node,
    bake_margins: dict[str, int],
    seen_mat: bool,
    export_path_tex: str,
    images_created: set[bpy.types.Image],
    link_array: list[list[str]],
    uv_map_override: UvMapOverride,
    extra_shader_nodes: list[tuple[bpy.types.Node, bpy.types.Nodes]],
    created_texture_nodes: dict[
        str, tuple[bpy.types.ShaderNodeTexImage, bpy.types.NodeSocket, bpy.types.NodeSocket, bpy.types.Node]
    ],
    seen_group: bool,
    is_in_texture_group: bool,
    texture_group: str,
    texture_dim: dict[str, int],
    texture_overrides: dict[str, list[int]],
    tex_node_to_normal_dict: dict[bpy.types.ShaderNodeTexImage, bpy.types.Node],
) -> None:
    normal = cast(bpy.types.NodeSocketVector, bsdf.inputs.get("Normal"))
    node_tree = cast(bpy.types.ShaderNodeTree, mat.node_tree)
    if not normal.is_linked:
        # create a value node in case there is no connection
        mapping_node = node_tree.nodes.new("ShaderNodeMapping")
        extra_shader_nodes.append((mapping_node, node_tree.nodes))
        cast(bpy.types.NodeSocketVector, mapping_node.outputs[0]).default_value = normal.default_value
        node_tree.links.new(mapping_node.outputs[0], normal)
    socket_connected_to_normal = cast(bpy.types.NodeSocket, cast(bpy.types.NodeLinks, normal.links)[0].from_socket)
    # create image texture node
    img_texture_node, create_normal_map = create_image_texture_node(
        node_tree,
        bsdf,
        seen_mat,
        extra_shader_nodes,
        created_texture_nodes,
        normal,
        socket_connected_to_normal,
        "Normal",
        "Normal",
    )
    if create_normal_map:
        # also create normal map
        normal_map = node_tree.nodes.new("ShaderNodeNormalMap")
        node_tree.links.new(
            cast(bpy.types.NodeOutputs, img_texture_node.outputs)["Color"],
            normal_map.inputs["Color"],
        )
        extra_shader_nodes.append((normal_map, node_tree.nodes))
        tex_node_to_normal_dict[img_texture_node] = normal_map

    # get or create the image
    img_name, img = get_or_create_image(
        mat,
        "Normal",
        seen_mat,
        seen_group,
        is_in_texture_group,
        texture_group,
        texture_dim,
        texture_overrides,
        False,
        img_texture_node,
        "Non-Color",
        export_path_tex,
    )

    link_array.append(["Normal", img_name + ".png", "all"])

    # check for other UV map targets
    old_active_ind_uv_map = check_uv_map_target(obj, uv_map_override, "Normal")

    img_texture_node.select = True
    node_tree.nodes.active = img_texture_node

    # bake and save file
    scene.render.bake.normal_space = "TANGENT"
    bake_and_clean_up(
        obj,
        mat,
        scene,
        img,
        img_name,
        bsdf,
        None,
        seen_mat,
        seen_group,
        bake_margins,
        False,
        None,
        None,
        None,
        images_created,
        old_active_ind_uv_map,
        "NORMAL",
    )
