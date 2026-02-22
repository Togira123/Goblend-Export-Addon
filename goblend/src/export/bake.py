import bpy
import os
from ..log import log



def bake_alpha(mat, img, emission_color_link, alpha_input, emission, scene):
    rgb_pixels = list(img.pixels)
    # make new link from alpha to emission strength
    mat.node_tree.links.remove(emission_color_link)
    if alpha_input.is_linked:
        mat.node_tree.links.new(alpha_input.links[0].from_socket, emission.inputs["Strength"])
    else:
        emission.inputs["Strength"].default_value = alpha_input.default_value
    # bake alpha values
    bpy.ops.object.bake(type="EMIT", save_mode="INTERNAL")
    alpha_pixels = list(img.pixels)
    # combine into one image
    final_pixels = []
    for i in range(0, len(rgb_pixels), 4):
        r = rgb_pixels[i]
        g = rgb_pixels[i + 1]
        b = rgb_pixels[i + 2]
        a = alpha_pixels[i]
        final_pixels.extend([r, g, b, a])
    # set pixels
    img.pixels = final_pixels

def get_uv_index_from_name(uv_map_name, obj):
    c = 0
    for layer in obj.data.uv_layers:
        if layer.name == uv_map_name:
            break
        c += 1
    return c

def check_uv_map_target(obj, mat, uv_map_override, key):
    old_active_ind_uv_map = obj.data.uv_layers.active_index
    if obj.name in uv_map_override and mat.name in uv_map_override[obj.name]:
        uv_map_name = uv_map_override[obj.name][mat.name][key]
        idx = get_uv_index_from_name(uv_map_name, obj)
        obj.data.uv_layers.active_index = idx
        return old_active_ind_uv_map
    return old_active_ind_uv_map

def create_image_texture_node(mat, bsdf, seen_mat, extra_shader_nodes, created_texture_nodes, main_socket, socket_connected_to_main_socket, type, key):
    node_name = "BakeTarget" + type + "ImageTextureNode"
    if not seen_mat and mat.node_tree.nodes.get(node_name) != None:
        raise Exception("A node named '" + node_name + "' already exists! Please rename it")
    img_texture_node = None
    if seen_mat:
        img_texture_node = mat.node_tree.nodes.get(node_name)
        return img_texture_node, False
    else:
        img_texture_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        img_texture_node.name = node_name
        extra_shader_nodes.append([img_texture_node, mat.node_tree.nodes])

        created_texture_nodes[key] = [img_texture_node, main_socket, socket_connected_to_main_socket, bsdf]
        return img_texture_node, True

def bake_and_clean_up(obj, mat, scene, img, img_name, bsdf, mat_output_node, seen_mat, seen_group, bake_margin, use_alpha, emission_color_link, alpha_input, emission, images_created, old_active_ind_uv_map, bake_type):
    scene.render.bake.margin = bake_margin
    scene.render.bake.use_clear = not seen_mat and not seen_group
    scene.render.bake.use_selected_to_active = False
    log("Baking " + img_name + "... (this might take a while)")
    bpy.ops.object.bake(type=bake_type, save_mode="INTERNAL")
    if use_alpha:
        # we need to bake alpha separately and add it to the image
        bake_alpha(mat, img, emission_color_link, alpha_input, emission, scene) 

    log("Baked " + img_name)
    img.save()
    images_created.add(img)

    # remove emission node and restore links from before
    if emission != None:
        mat.node_tree.nodes.remove(emission)
        mat.node_tree.links.new(bsdf.outputs[0], mat_output_node.inputs["Surface"])

    # restore old active index of uv map
    obj.data.uv_layers.active_index = old_active_ind_uv_map

def get_or_create_image(obj, mat, name, seen_mat, seen_group, is_in_uv_group, uv_group, texture_dim, texture_overrides, use_alpha, img_texture_node, color_space, export_path_tex):
    img_name = ""
    if is_in_uv_group:
        img_name = uv_group
    else:
        img_name = mat.name
    img_name = img_name + name
    img = None
    found = False
    if seen_mat or seen_group:
        img = bpy.data.images.get(img_name)
        found = img != None
    if not found:
        tex_dim_x = texture_dim["x"]
        tex_dim_y = texture_dim["y"]
        if obj.name in texture_overrides and mat.name in texture_overrides[obj.name]:
            tex_dim_x = texture_overrides[obj.name][mat.name][0]
            tex_dim_y = texture_overrides[obj.name][mat.name][1]
        img = bpy.data.images.new(img_name, tex_dim_x, tex_dim_y, alpha=use_alpha)
        if use_alpha:
            img.alpha_mode = "STRAIGHT"
        else:
            img.alpha_mode = "NONE"
        img.colorspace_settings.name = color_space
        # create path if it doesn't exist yet
        os.makedirs(export_path_tex, exist_ok=True)
        img.filepath = export_path_tex + img_name + ".png"
    img_texture_node.image = img
    return img_name, img

def make_emission_node(mat, mat_output_node):
    emission = mat.node_tree.nodes.new("ShaderNodeEmission")
    mat.node_tree.links.new(emission.outputs["Emission"], mat_output_node.inputs["Surface"])
    return emission

def bake_base_color(obj, mat, scene, bsdf, mat_output_node, bake_margin, seen_mat, alpha_input, export_path_tex, images_created, link_array, uv_map_override, extra_shader_nodes, created_texture_nodes, seen_group, is_in_uv_group, uv_group, texture_dim, texture_overrides, use_alpha_on_base_color):
    base_color = bsdf.inputs.get("Base Color")
    if base_color.is_linked:
        socket_connected_to_base_color = base_color.links[0].from_socket
        # create image texture node
        img_texture_node, _ = create_image_texture_node(mat, bsdf, seen_mat, extra_shader_nodes, created_texture_nodes, base_color, socket_connected_to_base_color, "BaseColor", "Base Color")

        # connect color to emission node to make sure only color is baked
        emission = make_emission_node(mat, mat_output_node)
        emission_color_link = mat.node_tree.links.new(socket_connected_to_base_color, emission.inputs["Color"])

        # get or create the image
        img_name, img = get_or_create_image(obj, mat, "BaseColor", seen_mat, seen_group, is_in_uv_group, uv_group, texture_dim, texture_overrides, use_alpha_on_base_color, img_texture_node, "sRGB", export_path_tex)

        link_array.append(["Base Color", img_name + ".png", "all"])

        # check for other UV map targets
        old_active_ind_uv_map = check_uv_map_target(obj, mat, uv_map_override, "Base Color")

        img_texture_node.select = True
        mat.node_tree.nodes.active = img_texture_node

        # bake and save file
        bake_and_clean_up(obj, mat, scene, img, img_name, bsdf, mat_output_node, seen_mat, seen_group, bake_margin, use_alpha_on_base_color, emission_color_link, alpha_input, emission, images_created, old_active_ind_uv_map, "EMIT")

def bake_metallic(obj, mat, scene, bsdf, mat_output_node, bake_margin, seen_mat, export_path_tex, images_created, link_array, uv_map_override, extra_shader_nodes, created_texture_nodes, seen_group, is_in_uv_group, uv_group, texture_dim, texture_overrides, tex_node_to_separate_metallic_dict, tex_node_to_combine_metallic_dict, combine_color):
    metallic = bsdf.inputs.get("Metallic")
    roughness = bsdf.inputs.get("Roughness")  # already get roughness here because we plan on baking them together
    emission = None
    if metallic.is_linked:
        socket_connected_to_metallic = metallic.links[0].from_socket
        # create image texture node
        img_texture_node, create_additional_nodes = create_image_texture_node(mat, bsdf, seen_mat, extra_shader_nodes, created_texture_nodes, metallic, socket_connected_to_metallic, "MetalRoughness", "Metallic")
        if create_additional_nodes:
            # also create metallic separate and combine nodes
            separate_metallic_node = mat.node_tree.nodes.new("ShaderNodeSeparateColor")
            combine_metallic_node = mat.node_tree.nodes.new("ShaderNodeCombineColor")
            extra_shader_nodes.append([separate_metallic_node, mat.node_tree.nodes])
            extra_shader_nodes.append([combine_metallic_node, mat.node_tree.nodes])
            tex_node_to_separate_metallic_dict[img_texture_node] = separate_metallic_node
            tex_node_to_combine_metallic_dict[img_texture_node] = combine_metallic_node

        # connect color to combine color node (red channel)
        mat.node_tree.links.new(socket_connected_to_metallic, combine_color.inputs[0])
        # for some reason all sockets need to be connected, otherwise the image is
        # misinterpreted by godot and compresses with the wrong compression, doubling the file size
        # green channel can easily be overwritten by roughness still, we just connect it below
        mat.node_tree.links.new(socket_connected_to_metallic, combine_color.inputs[1])
        mat.node_tree.links.new(socket_connected_to_metallic, combine_color.inputs[2])
        # connect combine color to emission node to make sure only color is baked
        emission = make_emission_node(mat, mat_output_node)
        mat.node_tree.links.new(combine_color.outputs[0], emission.inputs["Color"])

        if not roughness.is_linked:  # if roughness isn't linked do all the baking, otherwise we'll do it in the roughness section below
            # get or create the image
            img_name, img = get_or_create_image(obj, mat, "MetallicRoughness", seen_mat, seen_group, is_in_uv_group, uv_group, texture_dim, texture_overrides, False, img_texture_node, "Non-Color", export_path_tex)

            link_array.append(["Metallic", img_name + ".png", "red"])

            # check for other UV map targets
            old_active_ind_uv_map = check_uv_map_target(obj, mat, uv_map_override, "Metallic/Roughness")

            img_texture_node.select = True
            mat.node_tree.nodes.active = img_texture_node

            # bake and save file
            bake_and_clean_up(obj, mat, scene, img, img_name, bsdf, mat_output_node, seen_mat, seen_group, bake_margin, False, None, None, emission, images_created, old_active_ind_uv_map, "EMIT")
    return emission

def bake_roughness(obj, mat, scene, bsdf, mat_output_node, bake_margin, seen_mat, export_path_tex, images_created, link_array, uv_map_override, extra_shader_nodes, created_texture_nodes, seen_group, is_in_uv_group, uv_group, texture_dim, texture_overrides, tex_node_to_separate_roughness_dict, tex_node_to_combine_roughness_dict, combine_color, emission):
    metallic = bsdf.inputs.get("Metallic")
    roughness = bsdf.inputs.get("Roughness")
    if roughness.is_linked:
        socket_connected_to_roughness = roughness.links[0].from_socket
        # create image texture node
        if not seen_mat and not metallic.is_linked and mat.node_tree.nodes.get("BakeTargetMetalRoughnessImageTextureNode") != None:
            raise Exception("A node named 'BakeTargetMetalRoughnessImageTextureNode' already exists! Please rename it")
        img_texture_node = None
        if seen_mat or metallic.is_linked:
            img_texture_node = mat.node_tree.nodes.get("BakeTargetMetalRoughnessImageTextureNode")
            if not seen_mat:
                # also create metallic separate and combine nodes
                separate_roughness_node = mat.node_tree.nodes.new("ShaderNodeSeparateColor")
                combine_roughness_node = mat.node_tree.nodes.new("ShaderNodeCombineColor")
                extra_shader_nodes.append([separate_roughness_node, mat.node_tree.nodes])
                extra_shader_nodes.append([combine_roughness_node, mat.node_tree.nodes])
                tex_node_to_separate_roughness_dict[img_texture_node] = separate_roughness_node
                tex_node_to_combine_roughness_dict[img_texture_node] = combine_roughness_node

                created_texture_nodes["Roughness"] = [img_texture_node, roughness, socket_connected_to_roughness, bsdf]
        else:
            img_texture_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
            img_texture_node.name = "BakeTargetMetalRoughnessImageTextureNode"
            extra_shader_nodes.append([img_texture_node, mat.node_tree.nodes])
            # also create metallic separate and combine nodes
            separate_roughness_node = mat.node_tree.nodes.new("ShaderNodeSeparateColor")
            combine_roughness_node = mat.node_tree.nodes.new("ShaderNodeCombineColor")
            extra_shader_nodes.append([separate_roughness_node, mat.node_tree.nodes])
            extra_shader_nodes.append([combine_roughness_node, mat.node_tree.nodes])
            tex_node_to_separate_roughness_dict[img_texture_node] = separate_roughness_node
            tex_node_to_combine_roughness_dict[img_texture_node] = combine_roughness_node

            created_texture_nodes["Roughness"] = [img_texture_node, roughness, socket_connected_to_roughness, bsdf]

        # connect color to combine color node (green channel)
        mat.node_tree.links.new(socket_connected_to_roughness, combine_color.inputs[1])
        # for some reason all sockets need to be connected, otherwise the image is
        # misinterpreted by godot and compresses with the wrong compression, doubling the file size
        mat.node_tree.links.new(socket_connected_to_roughness, combine_color.inputs[2])
        if not metallic.is_linked:
            # only connect to red channel if it wasn't connected by metallic
            mat.node_tree.links.new(socket_connected_to_roughness, combine_color.inputs[0])
        # connect combine color to emission node to make sure only color is baked
        if not metallic.is_linked:  # otherwise we have already created an emission node
            emission = make_emission_node(mat, mat_output_node)
            mat.node_tree.links.new(combine_color.outputs[0], emission.inputs["Color"])

        # get or create the image
        img_name, img = get_or_create_image(obj, mat, "MetallicRoughness", seen_mat, seen_group, is_in_uv_group, uv_group, texture_dim, texture_overrides, False, img_texture_node, "Non-Color", export_path_tex)
        
        link_array.append(["Roughness", img_name + ".png", "green"])
        if metallic.is_linked:
            link_array.append(["Metallic", img_name + ".png", "red"])

        # check for other UV map targets
        old_active_ind_uv_map = check_uv_map_target(obj, mat, uv_map_override, "Metallic/Roughness")

        img_texture_node.select = True
        mat.node_tree.nodes.active = img_texture_node

        # bake and save file
        bake_and_clean_up(obj, mat, scene, img, img_name, bsdf, mat_output_node, seen_mat, seen_group, bake_margin, False, None, None, emission, images_created, old_active_ind_uv_map, "EMIT")
    
def bake_normal(obj, mat, scene, bsdf, bake_margin, seen_mat, export_path_tex, images_created, link_array, uv_map_override, extra_shader_nodes, created_texture_nodes, seen_group, is_in_uv_group, uv_group, texture_dim, texture_overrides, tex_node_to_normal_dict):
    normal = bsdf.inputs.get("Normal")
    if normal.is_linked:
        socket_connected_to_normal = normal.links[0].from_socket
        # create image texture node
        img_texture_node, create_normal_map = create_image_texture_node(mat, bsdf, seen_mat, extra_shader_nodes, created_texture_nodes, normal, socket_connected_to_normal, "Normal", "Normal")
        if create_normal_map:
            # also create normal map
            normal_map = mat.node_tree.nodes.new("ShaderNodeNormalMap")
            mat.node_tree.links.new(img_texture_node.outputs["Color"], normal_map.inputs["Color"])
            extra_shader_nodes.append([normal_map, mat.node_tree.nodes])
            tex_node_to_normal_dict[img_texture_node] = normal_map

        # get or create the image
        img_name, img = get_or_create_image(obj, mat, "Normal", seen_mat, seen_group, is_in_uv_group, uv_group, texture_dim, texture_overrides, False, img_texture_node, "Non-Color", export_path_tex)

        link_array.append(["Normal", img_name + ".png", "all"])

        # check for other UV map targets
        old_active_ind_uv_map = check_uv_map_target(obj, mat, uv_map_override, "Normal")

        img_texture_node.select = True
        mat.node_tree.nodes.active = img_texture_node

        # bake and save file
        scene.render.bake.normal_space = "TANGENT"
        bake_and_clean_up(obj, mat, scene, img, img_name, bsdf, None, seen_mat, seen_group, bake_margin, False, None, None, None, images_created, old_active_ind_uv_map, "NORMAL")
