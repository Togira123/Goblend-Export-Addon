import bpy
import os
import subprocess

from .handle_materials import handle_materials, check_convert_to_shader
from .clean_up import first_clean_up, last_clean_up
from .setup import setup
from .animations import handle_animations
from ..config import get_root_dir
from ..log import log

def handle_collision_shapes(collision_objects):
    cmd_line_args_for_collisions = []
    obj_info = []
    for obj in collision_objects:
        if "boxshape" in obj.name.lower():
            # use a literal box shape in godot for performance reasons
            obj_info.append({
                "name": obj.name,
                "type": "box",
                "dimensions": [obj.dimensions[0], obj.dimensions[1], obj.dimensions[2]],
            })
        elif "cylshape" in obj.name.lower() or "cylindershape" in obj.name.lower():
            obj_info.append({
                "name": obj.name,
                "type": "cyl",
                "height": obj.dimensions[2],
                "radius": obj.dimensions[0] / 2.0 # could also pick y axis, the two should be the same
            })
        elif "sphereshape" in obj.name.lower():
            obj_info.append({
                "name": obj.name,
                "type": "sphere",
                "radius": obj.dimensions[2] / 2.0 # could pick any axis
            })
        else:
            # simply append -col to the name, this will make godot import it as a collision shape
            obj.name = obj.name + "-convcolonly"
    cmd_line_args_for_collisions.append(str(len(obj_info)))
    for info in obj_info:
        cmd_line_args_for_collisions.append(info["name"])
        cmd_line_args_for_collisions.append(info["type"])
        if info["type"] == "box":
            cmd_line_args_for_collisions.append(str(info["dimensions"][0]))
            cmd_line_args_for_collisions.append(str(info["dimensions"][1]))
            cmd_line_args_for_collisions.append(str(info["dimensions"][2]))
        elif info["type"] == "cyl":
            cmd_line_args_for_collisions.append(str(info["height"]))
            cmd_line_args_for_collisions.append(str(info["radius"]))
        elif info["type"] == "sphere":
            cmd_line_args_for_collisions.append(str(info["radius"]))
    return cmd_line_args_for_collisions

def prep_for_export(objects, found_col_objects, collision_objects, collision_collection, settings_for_godot, godot_scene_nodes):
    # select all objects since we only export selected
    for obj in objects:
        obj.select_set(True)
    
    # and also select objects that hold the collections for external libraries
    # because we will later replace them with the scene instance in godot
    for obj in found_col_objects:
        obj.select_set(True)
    
    # handle collision objects
    cmd_line_args_for_collisions = handle_collision_shapes(collision_objects)
    # also select them
    for obj in collision_objects:
        obj.select_set(True)
    
    # and select the godot_scene_nodes
    for obj in godot_scene_nodes:
        obj.select_set(True)
    
    # and create more command line args
    # first come the default collision settings
    cmd_line_args_collision_settings = [settings_for_godot["default_physics_type"]]
    cmd_line_args_collision_settings.append(str(len(settings_for_godot["default_collision_layers"])))
    for default_layer in settings_for_godot["default_collision_layers"]:
        cmd_line_args_collision_settings.append(default_layer)
    cmd_line_args_collision_settings.append(str(len(settings_for_godot["default_collision_masks"])))
    for default_mask in settings_for_godot["default_collision_masks"]:
        cmd_line_args_collision_settings.append(default_mask)
    cmd_line_args_collision_settings.append(str(len(settings_for_godot["default_groups"])))
    for default_group in settings_for_godot["default_groups"]:
        cmd_line_args_collision_settings.append(default_group)

    
    if collision_collection == None:
        cmd_line_args_collision_settings.append("0")
    else:
        all_children = collision_collection.children_recursive
        cmd_line_args_collision_settings.append(str(len(settings_for_godot["collisions"])))
        for sett in settings_for_godot["collisions"]:
            cmd_line_args_collision_settings.append(sett["collection"].name)
            cmd_line_args_collision_settings.append(sett["type"])
            if sett["layer_overrides"] == None:
                cmd_line_args_collision_settings.append("null")
            else:
                cmd_line_args_collision_settings.append(str(len(sett["layer_overrides"])))
                for layer in sett["layer_overrides"]:
                    cmd_line_args_collision_settings.append(layer)
            
            if sett["mask_overrides"] == None:
                cmd_line_args_collision_settings.append("null")
            else:
                cmd_line_args_collision_settings.append(str(len(sett["mask_overrides"])))
                for mask in sett["mask_overrides"]:
                    cmd_line_args_collision_settings.append(mask)

            if sett["group_overrides"] == None:
                cmd_line_args_collision_settings.append("null")
            else:
                cmd_line_args_collision_settings.append(str(len(sett["group_overrides"])))
                for group in sett["group_overrides"]:
                    cmd_line_args_collision_settings.append(group)

            # check whether the collection really is a collision collection
            if sett["collection"] == collision_collection or sett["collection"] in all_children:
                num_of_objs = len(sett["collection"].objects)
                cmd_line_args_collision_settings.append(str(num_of_objs))
                for obj in sett["collection"].objects:
                    cmd_line_args_collision_settings.append(obj.name)
            else:
                cmd_line_args_collision_settings.append("0")
    
    # finally also add lights
    for obj in bpy.data.objects:
        if obj.type == "LIGHT" and not obj.hide_render and obj.library == None:
            obj.hide_set(False)
            obj.select_set(True)
    
    return cmd_line_args_for_collisions, cmd_line_args_collision_settings

def get_light_cmd_line_args(settings_for_godot):
    cmd_line_args_light_settings = []
    cnt = 0
    for obj_name, settings in settings_for_godot["lights"].items():
        cnt += 1
        cmd_line_args_light_settings.append(obj_name)
        cnt2 = 0
        tmp_arr = []
        for key, value in settings.items():
            cnt2 += 1
            tmp_arr.append(key)
            if type(value) is str:
                tmp_arr.append("1")
                tmp_arr.append(value)
            else: # type is list
                tmp_arr.append(str(len(value)))
                for val in value:
                    tmp_arr.append(val)
        cmd_line_args_light_settings += [str(cnt2)] + tmp_arr
        
    return [str(cnt)] + cmd_line_args_light_settings

def export(godot_exec_path, texture_dim, uv_map_override, bake_margins, texture_groups, texture_overrides, settings_for_godot, paths):
    objects, found_col_objects, collision_objects, collision_collection, export_path_glb, cmd_line_args_scene_instances, godot_scene_nodes, selected_objects, hidden_layer_collections, hidden_objects = setup(texture_groups, settings_for_godot)
    extra_shader_nodes, inputs, created_tex_nodes_per_mat_per_obj, old_meshes, orig_mod_per_obj, cmd_line_shader_data, converted_mat_names, cmd_line_args_path, cmd_line_args, images_created = handle_materials(uv_map_override, objects, paths, texture_groups, settings_for_godot, bake_margins, texture_dim, texture_overrides)

    blend_path = os.path.normcase(bpy.data.filepath)
    filename = os.path.basename(blend_path)

    cmd_line_args_for_collisions, cmd_line_args_collision_settings = prep_for_export(objects, found_col_objects, collision_objects, collision_collection, settings_for_godot, godot_scene_nodes)

    # export
    bpy.ops.export_scene.gltf(
        filepath=export_path_glb + os.path.splitext(filename)[0] + ".glb",
        export_format="GLB",
        use_selection=True,
        export_lights=True,
        export_apply=True # apply remaining modifiers
    )

    first_clean_up(objects, extra_shader_nodes, inputs, created_tex_nodes_per_mat_per_obj, old_meshes, orig_mod_per_obj)

    # grab animations on materials, since they are not exported by default
    cmd_line_animation_data = handle_animations()
    tmp = []
    for anim in settings_for_godot["animations"]:
        tmp.append(anim)
        tmp.append("true" if settings_for_godot["animations"][anim]["autoplay"] else "false")
        tmp.append("true" if settings_for_godot["animations"][anim]["loop"] else "false")
    tmp = [str(len(tmp) // 3)] + tmp
    cmd_line_animation_data = tmp + cmd_line_animation_data

    check_convert_to_shader(settings_for_godot, cmd_line_shader_data, converted_mat_names, objects)

    cmd_line_args_light_settings = get_light_cmd_line_args(settings_for_godot)

    # import into godot
    root_dir = get_root_dir()

    # this will also run post_import.gd which creates a copy of the project in a temporary folder
    val = subprocess.run([godot_exec_path, "--path", root_dir, "--headless", "--import", "--", "true"]
                        + cmd_line_args_path
                        + cmd_line_args_collision_settings
                        + cmd_line_args_for_collisions
                        + cmd_line_args
                        + cmd_line_animation_data
                        + cmd_line_shader_data
                        + cmd_line_args_light_settings
                        + cmd_line_args_scene_instances
                        )
    if val.returncode != 0:
        log("Running the godot executable with import resulted in an error", "WARNING")

    last_clean_up(images_created, found_col_objects, collision_objects, export_path_glb, selected_objects, hidden_layer_collections, hidden_objects)
