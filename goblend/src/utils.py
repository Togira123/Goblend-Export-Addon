import bpy
import os

root_dir = None

layers_enum_cache = []
group_list_enum_cache = []
godot_scene_panel_props_enum_cache = []


def reset_cache_enums():
    global layers_enum_cache
    global group_list_enum_cache
    global godot_scene_panel_props_enum_cache
    layers_enum_cache = []
    group_list_enum_cache = []
    godot_scene_panel_props_enum_cache = []


def get_root_dir():
    global root_dir
    if root_dir != None:
        return root_dir
    if bpy.data.filepath == "":
        return ""
    filepath = os.path.normcase(bpy.data.filepath)
    while True:
        head, _ = os.path.split(filepath)
        if head == filepath:
            # reached root
            break
        files = [f for f in os.listdir(head) if os.path.isfile(os.path.join(head, f))]
        for file in files:
            if file == "project.godot":
                root_dir = head
                break
        filepath = head
    if root_dir == None:
        # no godot project found
        raise Exception("No Godot project found")
    return root_dir
