import bpy

from ...config import get_config
from ..lists.GroupList import GroupListItem

from .enum_items import physics_objects

def is_godot_scene(self, obj):
    scene = bpy.context.scene
    for item in scene.godot_scene_panel_props:
        if obj == item.obj:
            return False
    godot_scenes = bpy.data.collections.get("GodotScenes")
    if not godot_scenes:
        return False
    return obj.name in godot_scenes.objects
    
enum = []

def scenes(_self, _context):
    global enum
    if len(enum) == 0:
        config = get_config()
        for scene in config["godot_scenes"]:
            enum.append((scene["name"], scene["display_name"], "Godot Scene at: " + scene["godot_scene_path"]))
    
    return enum

class GodotScenePanelProperties(bpy.types.PropertyGroup):
    open: bpy.props.BoolProperty(default=True)
    obj: bpy.props.PointerProperty(
        name="Target Object",
        description="The object to be replaced with the scene.",
        type=bpy.types.Object,
        poll=is_godot_scene
    )
    scene: bpy.props.EnumProperty(
        name="Scene",
        description="The Godot Scene to place at the object's position. Use the config file to register more scenes.",
        items=scenes
    )
