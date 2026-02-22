import bpy
import os
from ..log import log

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
                case "NODES":
                    mod.node_group = m["node_group"]
                    for identifier, val in m["props"].items():
                        mod[identifier] = val

def last_clean_up(images_created, found_col_objects, collision_objects, export_path_glb, selected_objects, hidden_layer_collections, hidden_objects):
    
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

    for coll in hidden_layer_collections:
        coll.hide_viewport = True
    
    for obj in hidden_objects:
        obj.hide_set(True)

