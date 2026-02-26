import subprocess
import bpy
import os

from .convert_shader import convert_to_godot_shader

from .bake import bake_base_color, bake_metallic, bake_normal, bake_roughness, get_uv_index_from_name
from .setup import save_path_keys
from ..config import get_root_dir
from ..log import log

def material_prep_cmd_line_args(mat, cmd_line_args, settings_for_godot):
    cmd_line_args.append(mat.name)
    if mat.name in settings_for_godot["material_transparency_mode_overrides"]:
        cmd_line_args.append(settings_for_godot["material_transparency_mode_overrides"][mat.name]["mode"])
        if settings_for_godot["material_transparency_mode_overrides"][mat.name]["mode"] == "SCISSOR":
            cmd_line_args.append(str(settings_for_godot["material_transparency_mode_overrides"][mat.name]["scissor"]))
    else:
        cmd_line_args.append(settings_for_godot["transparency_mode"])
        if settings_for_godot["transparency_mode"] == "SCISSOR":
            cmd_line_args.append(str(settings_for_godot["scissor_value"]))
    if mat.name in settings_for_godot["material_cull_mode_overrides"]:
        cmd_line_args.append(settings_for_godot["material_cull_mode_overrides"][mat.name])
    else:
        cmd_line_args.append(settings_for_godot["cull_mode"])

def get_bsdf_and_mat_output_node_of_mat(mat):
    mat_output_node = mat.node_tree.nodes.get("Material Output")
    if mat_output_node.type != "OUTPUT_MATERIAL":
        raise Exception('A node is named "Material Output" but is not actually the material output')
    surface_input = mat_output_node.inputs.get("Surface")
    if not surface_input.is_linked:
        raise Exception('Surface input of "Material Output" node is not linked to anything!')
    link = surface_input.links[0]
    bsdf = link.from_node
    if bsdf.type != "BSDF_PRINCIPLED":
        raise Exception("Material Output is connected to non-bsdf node, currently not supported")
    return mat_output_node, bsdf

def prepare_material(obj, mat, poly_indices):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    # make sure polys are correct again
    for poly in obj.data.polygons:
        poly.material_index = poly_indices[poly.index]
    if not mat.use_nodes:
        log("Material not using nodes", "WARNING")
        return None
    return get_bsdf_and_mat_output_node_of_mat(mat) 

def handle_texture_group(mat, texture_groups, seen_texture_groups, cmd_line_args):
    is_in_texture_group = mat.name in texture_groups 
    texture_group = ""
    seen_group = False
    if is_in_texture_group:
        texture_group = texture_groups[mat.name]
        if texture_group in seen_texture_groups:
            seen_group = True
        else:
            seen_texture_groups.add(texture_group)

    if is_in_texture_group:
        cmd_line_args.append(texture_group)
    else:
        cmd_line_args.append("null")  # used to indicate that the object is in no uv group
    return is_in_texture_group, texture_group, seen_group

def should_bake_target(orig_value, orig_texture_group, texture_groups, input_name, is_equal):
    for mat_name, group_name in texture_groups.items():
        if group_name == orig_texture_group:
            # if this material has this input linked or has a different value we have to bake
            mat = bpy.data.materials.get(mat_name)
            _, bsdf = get_bsdf_and_mat_output_node_of_mat(mat)
            inp = bsdf.inputs.get(input_name)
            if inp.is_linked or not is_equal(inp.default_value, orig_value):
                return True
    # none of the other materials have linked that input and they all have the same default value
    # hence there is no need to bake this
    return False

def get_bake_targets(mat, bsdf, texture_groups, is_in_texture_group):
    base_color = bsdf.inputs.get("Base Color")
    bake_base_color = base_color.is_linked
    mat_group_name = None
    if is_in_texture_group:
        mat_group_name = texture_groups[mat.name]
    if not bake_base_color and is_in_texture_group:
        # check whether any material in the same texture group is linked or has a different value
        def is_equal(a, b):
            return a[0] == b[0] and a[1] == b[1] and a[2] == b[2] and a[3] == b[3]
        bake_base_color = should_bake_target(base_color.default_value, mat_group_name, texture_groups, "Base Color", is_equal)
    roughness = bsdf.inputs.get("Roughness")
    bake_roughness = roughness.is_linked
    if not bake_roughness and is_in_texture_group:
        def is_equal(a, b):
            return a == b
        bake_roughness = should_bake_target(roughness.default_value, mat_group_name, texture_groups, "Roughness", is_equal) 
    metallic = bsdf.inputs.get("Metallic")
    bake_metallic = metallic.is_linked
    if not bake_metallic and is_in_texture_group:
        def is_equal(a, b):
            return a == b
        bake_metallic = should_bake_target(metallic.default_value, mat_group_name, texture_groups, "Metallic", is_equal)
    normal = bsdf.inputs.get("Normal")
    bake_normal = normal.is_linked
    if not bake_normal and is_in_texture_group:
        def is_equal(a, b):
            return a[0] == b[0] and a[1] == b[1] and a[2] == b[2]
        bake_normal = should_bake_target(normal.default_value, mat_group_name, texture_groups, "Normal", is_equal)
    return bake_base_color, bake_roughness, bake_metallic, bake_normal
        

def save_mesh_and_modifiers(obj, old_meshes, orig_mod_per_obj):
    mesh_copy = obj.data.copy()
    old_meshes[obj] = obj.data
    obj.data = mesh_copy
    # store modifiers in here
    original_modifiers = []
    # first check for modifiers
    for m in obj.modifiers:
        # handle each modifier differently
        mod_data = {
            "name": m.name,
            "type": m.type,
            "props": {}
        }
        match m.type:
            case "NODES":  # geometry nodes
                ng = m.node_group
                mod_data["node_group"] = ng
                for i, item in enumerate(ng.interface.items_tree):
                    identifier = item.identifier
                    if identifier in m:
                        mod_data["props"][identifier] = m[identifier]
                original_modifiers.append(mod_data)
                # apply geometry nodes modifier
                bpy.ops.object.modifier_apply(modifier=m.name)

    orig_mod_per_obj[obj] = original_modifiers

def prepare_object(obj):
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

def connect_image_textures(objects, created_tex_nodes_per_mat_per_obj, tex_node_to_normal_dict, tex_node_to_separate_metallic_dict, tex_node_to_combine_metallic_dict, tex_node_to_separate_roughness_dict, tex_node_to_combine_roughness_dict):
    inputs = ["Base Color", "Metallic", "Roughness", "Normal"]
    for obj in objects:
        for slot in obj.material_slots:
            mat = slot.material
            for inp in inputs:
                if obj in created_tex_nodes_per_mat_per_obj and mat in created_tex_nodes_per_mat_per_obj[obj] and inp in created_tex_nodes_per_mat_per_obj[obj][mat]:
                    img_tex_node = created_tex_nodes_per_mat_per_obj[obj][mat][inp][0]
                    bsdf = created_tex_nodes_per_mat_per_obj[obj][mat][inp][3]
                    if inp == "Normal":
                        normal_map = tex_node_to_normal_dict[img_tex_node]
                        mat.node_tree.links.new(normal_map.outputs["Normal"], bsdf.inputs[inp])
                    elif inp == "Metallic":
                        # we have to create metallic and roughness info on all three rgb channels separately
                        # for metallic:
                        separate_metallic_node = tex_node_to_separate_metallic_dict[img_tex_node]
                        combine_metallic_node = tex_node_to_combine_metallic_dict[img_tex_node]
                        # first separate the color coming from the texture into r, g and b
                        mat.node_tree.links.new(img_tex_node.outputs["Color"], separate_metallic_node.inputs["Color"])
                        # then connect all inputs from combine with the r output from the separate node
                        mat.node_tree.links.new(separate_metallic_node.outputs[0], combine_metallic_node.inputs[0])
                        mat.node_tree.links.new(separate_metallic_node.outputs[0], combine_metallic_node.inputs[1])
                        mat.node_tree.links.new(separate_metallic_node.outputs[0], combine_metallic_node.inputs[2])
                        mat.node_tree.links.new(combine_metallic_node.outputs["Color"], bsdf.inputs["Metallic"])
                    elif inp == "Roughness":
                        # for roughness:
                        separate_roughness_node = tex_node_to_separate_roughness_dict[img_tex_node]
                        combine_roughness_node = tex_node_to_combine_roughness_dict[img_tex_node]
                        # first separate the color coming from the texture into r, g and b
                        mat.node_tree.links.new(img_tex_node.outputs["Color"], separate_roughness_node.inputs["Color"])
                        # then connect all inputs from combine with the g output from the separate node
                        mat.node_tree.links.new(separate_roughness_node.outputs[1], combine_roughness_node.inputs[0])
                        mat.node_tree.links.new(separate_roughness_node.outputs[1], combine_roughness_node.inputs[1])
                        mat.node_tree.links.new(separate_roughness_node.outputs[1], combine_roughness_node.inputs[2])
                        mat.node_tree.links.new(combine_roughness_node.outputs["Color"], bsdf.inputs["Roughness"])
                    else:
                        mat.node_tree.links.new(img_tex_node.outputs["Color"], bsdf.inputs[inp])
    return inputs

def first_clean_up(objects, extra_shader_nodes, inputs, created_tex_nodes_per_mat_per_obj, old_meshes, orig_mod_per_obj):
    # deselect afterwards
    bpy.ops.object.select_all(action="DESELECT")

    # make sure to remove the Image Texture node when done exporting
    for d in extra_shader_nodes:
        d[1].remove(d[0])

    # restore original node links
    for obj in objects:
        for slot in obj.material_slots:
            mat = slot.material
            for inp in inputs:
                if inp in created_tex_nodes_per_mat_per_obj[obj][mat]:
                    mat.node_tree.links.new(created_tex_nodes_per_mat_per_obj[obj][mat][inp][2], created_tex_nodes_per_mat_per_obj[obj][mat][inp][1])

    # reapply old meshes for every object
    for obj in objects:
        orig_name = obj.data.name
        obj.data = old_meshes[obj]
        obj.data.name = orig_name
        # set object as active
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        # reapply all modifiers
        for m in orig_mod_per_obj[obj]:
            bpy.ops.object.modifier_add(type=m["type"])
            mod = obj.modifiers[len(obj.modifiers) - 1]
            mod.name = m["name"]
            match m["type"]:
                case "BEVEL":
                    for prop in m["props"]:
                        setattr(mod, prop, m["props"][prop])
                case "NODES":
                    mod.node_group = m["node_group"]
                    for identifier, val in m["props"].items():
                        mod[identifier] = val

def last_clean_up(images_created, found_col_objects, collision_objects, export_path_glb, selected_objects):
    content = os.listdir(export_path_glb)
    for file in content:
        filepath = os.path.join(export_path_glb, file)
        if os.path.isfile(filepath):
            os.remove(filepath)
        else:
            log("Temporary directory contains other directories", "ERROR")
    
    try:
        os.rmdir(export_path_glb)
    except:
        log("Failed to remove temporary export directory", "ERROR")


    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    # clear cached image data blocks
    for img in images_created:
        bpy.data.images.remove(img)
    
    # remove extra cubes
    for obj in found_col_objects:
        bpy.data.objects.remove(obj)
    
    for obj in collision_objects:
        if obj.name.endswith("-convcolonly"):
            obj.name = obj.name[:-12] # remove the last 12 chars
    
    bpy.ops.object.select_all(action="DESELECT")

    for obj in selected_objects:
        obj.select_set(True)

def check_convert_to_shader(settings_for_godot, cmd_line_shader_data, already_converted_mats, objects):
    shader_count = 0
    for mat_name, obj in settings_for_godot["use_shader_mats"].items():
        if mat_name in already_converted_mats:
            continue
        # do not do anything with objects that aren't exported
        if not obj in objects:
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
                # if right_after_bake is false, the 3 uv indices don't matter so we can safely pass None for them
            code, uniforms = convert_to_godot_shader(obj, mat_name, cull_mode, limit_normal, False, None, None, None)
            shader_count += 1
            cmd_line_shader_data.append(mat_name)
            cmd_line_shader_data.append(code)
            cmd_line_shader_data.append(str(len(uniforms)))
            for uniform in uniforms:
                cmd_line_shader_data.append(uniform[0]) # var name
                cmd_line_shader_data.append(uniform[1]) # linkTo (image name or so, the value to set with set_shader_parameter in Godot)
        except Exception as e:
            log("Exception while trying to generate shader code: " + repr(e), "ERROR")
            raise e
    total_shader_count = int(cmd_line_shader_data[0]) + shader_count
    cmd_line_shader_data[0] = str(total_shader_count)

def check_early_convert_to_shader(uv_map_override, settings_for_godot, objects):
    cmd_line_shader_data = []
    shader_count = 0
    seen_mat_names = set()
    for obj_name in uv_map_override:
        obj = uv_map_override[obj_name]["obj"]
        # do not do anything with objects that aren't exported
        if not obj in objects:
            continue
        mat_slots = []
        for slot in obj.material_slots:
            if slot.material != None:
                mat_slots.append(slot)
        for slot in mat_slots:
            mat = slot.material
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
                code, uniforms = convert_to_godot_shader(
                    obj,
                    mat_name,
                    cull_mode,
                    limit_normal,
                    True,
                    get_uv_index_from_name(uv_map_override[obj_name]["Base Color"], obj),
                    get_uv_index_from_name(uv_map_override[obj_name]["Metallic/Roughness"], obj),
                    get_uv_index_from_name(uv_map_override[obj_name]["Normal"], obj),
                )
                shader_count += 1
                cmd_line_shader_data.append(mat_name)
                cmd_line_shader_data.append(code)
                cmd_line_shader_data.append(str(len(uniforms)))
                for uniform in uniforms:
                    cmd_line_shader_data.append(uniform[0]) # var name
                    cmd_line_shader_data.append(uniform[1]) # linkTo (image name or so, the value to set with set_shader_parameter in Godot)
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
            obj = settings_for_godot["limit_uv_effect_normal"][mat_name]["obj"]
            code, uniforms = convert_to_godot_shader(
                obj,
                mat_name,
                cull_mode,
                limit_normal,
                True,
                # if there were indices specified we would've handled the material in the previous loop
                obj.data.uv_layers.active_index,
                obj.data.uv_layers.active_index,
                obj.data.uv_layers.active_index
            )
            shader_count += 1
            cmd_line_shader_data.append(mat_name)
            cmd_line_shader_data.append(code)
            cmd_line_shader_data.append(str(len(uniforms)))
            for uniform in uniforms:
                cmd_line_shader_data.append(uniform[0]) # var name
                cmd_line_shader_data.append(uniform[1]) # linkTo (image name or so, the value to set with set_shader_parameter in Godot)
        except Exception as e:
            log("Exception while trying to generate shader code: " + repr(e), "ERROR")
            raise e
    return [str(shader_count)] + cmd_line_shader_data, seen_mat_names

def handle_materials(uv_map_override, objects, paths, texture_groups, settings_for_godot, bake_margins, texture_dim, texture_overrides):
    images_created = set()
    scene = bpy.context.scene
    seen_mats = set()
    seen_texture_groups = set()
    extra_shader_nodes = []
    old_meshes = {}
    orig_mod_per_obj = {}
    created_tex_nodes_per_mat_per_obj = {}
    tex_node_to_normal_dict = {}
    tex_node_to_separate_metallic_dict = {}
    tex_node_to_combine_metallic_dict = {}
    tex_node_to_separate_roughness_dict = {}
    tex_node_to_combine_roughness_dict = {}

    root_dir = get_root_dir()

    blend_path = os.path.normcase(bpy.data.filepath)
    filename = os.path.basename(blend_path)

    cmd_line_args_path = []
    for save_path in save_path_keys:
        cmd_line_args_path.append(os.path.normcase(paths[save_path]))

    cmd_line_args = []
    cmd_line_args.append("true" if scene.is_root_scene else "false")
    cmd_line_args.append(str(len(objects)))
    cmd_line_args.append(os.path.splitext(filename)[0])

    # use temp file for storing paths of child scenes
    # will be read in the gdscript script to figure out what scenes to link 
    tmp_file_path = os.path.normcase(os.path.join(root_dir, ".tmp.goblend"))
    with open(tmp_file_path, "a") as tmp_file:
        tmp_file.write(os.path.normcase(bpy.data.filepath) + "\n" + os.path.join(paths["scene_save_path"], os.path.splitext(filename)[0]) + "\n")

    for obj in objects:
        if not prepare_object(obj):
            continue

        # TODO: maybe all of this saving operators and saving meshes not needed if I can simply undo the whole export operator
        # save old mesh to after exporting
        save_mesh_and_modifiers(obj, old_meshes, orig_mod_per_obj)

        created_tex_nodes_per_mat = {}

        # for each material of the object create textures
        mat_slots = []
        for slot in obj.material_slots:
            if slot.material != None:
                mat_slots.append(slot)

        cmd_line_args.append(obj.name)
        cmd_line_args.append(str(len(mat_slots)))

        if obj.name in settings_for_godot["shadow_cast_mode"]:
            cmd_line_args.append(settings_for_godot["shadow_cast_mode"][obj.name])
        else:
            cmd_line_args.append("ON") # default value for casting shadows
        
        # store all materials in an array, remove them all from the object and always only have one material slot
        # because having multiple will result in all of them baking at the same time
        materials = []
        for slot in mat_slots:
            materials.append(slot.material)

        poly_indices = {}
        for poly in obj.data.polygons:
            poly_indices[poly.index] = poly.material_index
        
        for mat in materials:
            if mat.name in settings_for_godot["use_shader_mats"]:
                settings_for_godot["use_shader_mats"][mat.name] = obj
            if mat.name in settings_for_godot["limit_uv_effect_normal"]:
                settings_for_godot["limit_uv_effect_normal"][mat.name]["obj"] = obj
            material_output_and_bsdf = prepare_material(obj, mat, poly_indices)
            if not material_output_and_bsdf:
                continue
            mat_output_node, bsdf = material_output_and_bsdf
            material_prep_cmd_line_args(mat, cmd_line_args, settings_for_godot)
            is_in_texture_group, texture_group, seen_group = handle_texture_group(mat, texture_groups, seen_texture_groups, cmd_line_args)
            link_array = []
            seen_mat = False
            if mat.name in seen_mats:
                seen_mat = True
                log("Using the same material (" + mat.name + ") on more than one object, baking to the same image as before! If these objects have overlapping UV maps this is (potentially) bad")
            else:
                seen_mats.add(mat.name)

            # create a combine color node to split metallic and roughness into red and green channels respectively
            combine_color = mat.node_tree.nodes.new("ShaderNodeCombineColor")
            combine_color.inputs[2].default_value = 0.0
            combine_color.inputs[0].default_value = 0.0

            created_texture_nodes = {}

            alpha_input = bsdf.inputs.get("Alpha")
            use_alpha_on_base_color = alpha_input.is_linked or alpha_input.default_value != 1.0

            if not mat.name in settings_for_godot["use_shader_mats"]:
                log("Checking material '" + mat.name + "' on object '" + obj.name + "'")

                should_bake_base_color, should_bake_roughness, should_bake_metallic, should_bake_normal = get_bake_targets(mat, bsdf, texture_groups, is_in_texture_group)
                emission = None 
                # bake materials
                if should_bake_base_color:
                    bake_base_color(obj,
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
                                    use_alpha_on_base_color
                                    )
                if should_bake_metallic:
                    emission = bake_metallic(obj,
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
                                            should_bake_roughness
                                            )
                if should_bake_roughness:
                    bake_roughness(obj,
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
                                should_bake_metallic
                                )
                if should_bake_normal:
                    bake_normal(obj,
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
                                tex_node_to_normal_dict
                                )

                # transmission
                transmission = bsdf.inputs.get("Transmission Weight")
                # we only handle single float values here
                # to support textures later on, we'd need to bake the values
                # into the alpha channel of the base color
                if not transmission.is_linked and transmission.default_value > 0.0:
                    link_array.append(["Transmission", str(transmission.default_value), "all"])

            # remove combine color node
            mat.node_tree.nodes.remove(combine_color)

            cmd_line_args.append(str(len(link_array)))
            for li in link_array:
                cmd_line_args.append(li[0])
                cmd_line_args.append(li[1])
                cmd_line_args.append(li[2])
            created_tex_nodes_per_mat[mat] = created_texture_nodes
        created_tex_nodes_per_mat_per_obj[obj] = created_tex_nodes_per_mat

        # restore materials
        obj.data.materials.clear()
        for mat in materials:
            obj.data.materials.append(mat)
        for poly in obj.data.polygons:
            poly.material_index = poly_indices[poly.index]
        
    # all textures for all materials for all objects are created, connect the image textures to the inputs of the principled bsdf
    inputs = connect_image_textures(objects, created_tex_nodes_per_mat_per_obj, tex_node_to_normal_dict, tex_node_to_separate_metallic_dict, tex_node_to_combine_metallic_dict, tex_node_to_separate_roughness_dict, tex_node_to_combine_roughness_dict)

    # if either limiting normal effect with disabled use shader or separate UV maps are set, we have to convert to a shader here
    cmd_line_shader_data, converted_mat_names = check_early_convert_to_shader(uv_map_override, settings_for_godot, objects)

    return extra_shader_nodes, inputs, created_tex_nodes_per_mat_per_obj, old_meshes, orig_mod_per_obj, cmd_line_shader_data, converted_mat_names, cmd_line_args_path, cmd_line_args, images_created
