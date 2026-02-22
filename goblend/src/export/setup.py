import bpy
import os
import subprocess

from ...src.config import get_root_dir

from ...src.log import log

save_path_keys = [
    "scene_save_path",
    "material_save_path", 
    "texture_save_path",
    "animation_library_save_path",
    "animation_save_path",
    "shader_save_path",
    "collision_shapes_save_path"
]

save_path_uses_filename = [
    False,
    True,
    True,
    True,
    True,
    True,
    False
]

save_path_hierarchy_keys = [
    "scene_use_same_hierarchy",
    "material_use_same_hierarchy",
    "texture_use_same_hierarchy",
    "animation_library_use_same_hierarchy",
    "animation_use_same_hierarchy",
    "shader_use_same_hierarchy",
    "reuse_collision_shapes"
]

def find_objs_and_cols(root, found_col_objects, seen_libs, cmd_line_args_scene_instances):
    collision_collection = None
    if root.name == "Collisions":
        collision_collection = root
    for child in root.children:
        coll = find_objs_and_cols(child, found_col_objects, seen_libs, cmd_line_args_scene_instances)
        if coll != None:
            collision_collection = coll
    for obj in root.objects:
        if obj.instance_type == "COLLECTION" and obj.instance_collection and not obj.hide_render:
            col = obj.instance_collection
            if col.library != None:
                blender_binary_path = bpy.app.binary_path

                library_blend_file = os.path.normpath(os.path.abspath(bpy.path.abspath(col.library.filepath)))
                
                bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.mesh.primitive_cube_add(
                    location=obj.location,
                    rotation=obj.rotation_euler
                )
                
                cube = bpy.context.active_object
                cube.name = obj.name + "__tmp_name"
                cube.scale = obj.scale # add scale after creating because otherwise it directly applies it
                
                found_col_objects.append(cube)
                
                if not col.library.filepath in seen_libs:
                    log("Found Library: " + col.library.name)
                    seen_libs.add(col.library.filepath)
                    subprocess.run([blender_binary_path, "-b", "--addons", "goblend", library_blend_file, "--python-expr", "import bpy; bpy.context.scene.is_root_scene = False; bpy.ops.scene.export_to_godot()"])
                
                cmd_line_args_scene_instances.append(library_blend_file)
                cmd_line_args_scene_instances.append(cube.name)
    return collision_collection

def get_objects_to_export(uv_group_assignments, uv_groups):
    objects = []
    hidden_objects = set()
    for obj in bpy.data.objects:
        # only export object if it's a mesh, not hidden from rendering and not from a library
        if obj.type == "MESH" and not obj.hide_render and obj.library == None and not obj.name.endswith("__tmp_name"):
            if obj.hide_get():
                hidden_objects.add(obj)
            obj.hide_set(False) # make every object that we take into consideration visible
            objects.append(obj)
        else:
            continue

        if obj.name in uv_group_assignments and len(obj.material_slots) > 1:
            raise Exception("Objects that have a uv group cannot have more than 1 material (could be added though probably if really needed)")
        for slot in obj.material_slots:
            for grp in uv_groups:
                if slot.material.name == grp:
                    raise Exception("There is a material named" + slot.material.name + " which conflicts with a uv_group name")
    return objects, hidden_objects

def get_collision_objects(collision_collection, objects):
    collision_objects = set()
    if collision_collection != None:
        def remove_collision_from_render(col):
            to_remove = set()
            for obj in col.objects:
                if obj in objects:
                    to_remove.add(obj)
            for obj in to_remove:
                objects.remove(obj)
                collision_objects.add(obj)
                    
        remove_collision_from_render(collision_collection)
        for col in collision_collection.children_recursive:
            remove_collision_from_render(col)
    return collision_objects

def remove_godot_scene_objects(objects):
    godot_scenes = bpy.data.collections.get("GodotScenes")
    godot_scene_nodes = set()
    if not godot_scenes:
        return godot_scene_nodes
    to_remove = set()
    for obj in godot_scenes.objects:
        if obj in objects:
            to_remove.add(obj)
        log("Found Object to be replaced with Godot Scene: " + obj.name)
        godot_scene_nodes.add(obj)
    for obj in to_remove:
        objects.remove(obj)
    
    return godot_scene_nodes

def setup(uv_group_assignments, settings_for_godot):
    log("Running export for: " + os.path.normcase(bpy.data.filepath))

    selected_objects = bpy.context.selected_objects.copy()

    root_dir = get_root_dir()

    seen_libs = set()
    
    # scene path, scene name
    cmd_line_args_scene_instances = []
    found_col_objects = []

    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection
    
    collision_collection = find_objs_and_cols(bpy.context.scene.collection, found_col_objects, seen_libs, cmd_line_args_scene_instances)

    cmd_line_args_scene_instances.insert(0, str(len(found_col_objects)))

    # also append info about godot scenes
    cmd_line_godot_scenes = []
    for obj_name in settings_for_godot["godot_scenes"]:
        cmd_line_godot_scenes.append(obj_name)
        cmd_line_godot_scenes.append(settings_for_godot["godot_scenes"][obj_name])
    cmd_line_godot_scenes.insert(0, str(len(cmd_line_godot_scenes) // 2))
    cmd_line_args_scene_instances = cmd_line_args_scene_instances + cmd_line_godot_scenes

    # make all LayerCollections visible
    # we need this to later make all objects visible and then to export the visible objects
    hidden_layer_collections = set()

    def loop_layer_collections(layer_coll):
        if layer_coll.hide_viewport:
            hidden_layer_collections.add(layer_coll)
        layer_coll.hide_viewport = False
        for c in layer_coll.children:
            loop_layer_collections(c)
    
    loop_layer_collections(bpy.context.view_layer.layer_collection) # this is the root collection

    uv_groups = set()

    for val in uv_group_assignments.values():
        if not val in uv_groups:
            log("INFO: Found uv_group " + val)
            uv_groups.add(val)
    
    objects, hidden_objects = get_objects_to_export(uv_group_assignments, uv_groups)

    collision_objects = get_collision_objects(collision_collection, objects)

    godot_scene_nodes = remove_godot_scene_objects(objects)

    log("Collision Objects:\n" + str(collision_objects))

    scene = bpy.context.scene

    if scene.render.engine != "CYCLES":
        log("Render Engine is not set to cycles, baking won't work. Changing to Cycles", "WARNING")
        scene.render.engine = "CYCLES"
    if scene.render.image_settings.file_format != "PNG":
        log("Setting image settings: file_format to PNG, was: " + scene.render.image_settings.file_format)
        scene.render.image_settings.file_format = "PNG"
    if scene.render.image_settings.compression != 100:
        log("Setting image settings: compression to 100, was: " + str(scene.render.image_settings.compression))
        scene.render.image_settings.compression = 100
    if scene.render.image_settings.color_mode != "RGB":
        log("Setting image settings: color_mode to RGB, was: " + scene.render.image_settings.color_mode)
        scene.render.image_settings.color_mode = "RGB"
    if scene.render.image_settings.color_depth != "8":
        log("Setting image settings: color_depth to 8, was: " + scene.render.image_settings.color_depth)
        scene.render.image_settings.color_depth = "8"

    # create it again every time because it is deleted by the gdscript script
    export_path_glb = os.path.join(root_dir, "tmp_goblend_export/")
    os.makedirs(export_path_glb, exist_ok=True)
    log("Setup done")

    return objects, found_col_objects, collision_objects, collision_collection, export_path_glb, cmd_line_args_scene_instances, godot_scene_nodes, selected_objects, hidden_layer_collections, hidden_objects


